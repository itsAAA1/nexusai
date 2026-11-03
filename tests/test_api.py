"""Offline, no-paid-API tests for the deployed Python request handler."""
import http.client
import io
import json
import os
import unittest
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
from unittest.mock import patch
from urllib.error import HTTPError

spec = spec_from_file_location("nexus_api", Path(__file__).resolve().parents[1] / "api" / "index.py")
api = module_from_spec(spec)
spec.loader.exec_module(api)

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"NEXUSAI_ACCESS_TOKEN": "test-token"})
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def call(self, body, method="POST", authorization="Bearer test-token"):
        handler = api.handler.__new__(api.handler)
        handler.headers = {"Content-Length": str(len(body))}
        if authorization is not None:
            handler.headers["Authorization"] = authorization
        handler.rfile = io.BytesIO(body)
        sent = []
        handler.respond = lambda status, payload: sent.append((status, payload))
        (handler.do_POST if method == "POST" else handler.do_GET)()
        self.assertEqual(len(sent), 1)
        return sent[0]

    def test_get_status_without_key(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            status, payload = self.call(b"", "GET")
        self.assertEqual(status, 200)
        self.assertFalse(payload["inference_configured"])
        self.assertEqual(len(payload["agents"]), 5)

    def test_json_root_must_be_object(self):
        for value in ([], 12, True, None, "hello"):
            with self.subTest(value=value):
                status, payload = self.call(json.dumps(value).encode())
                self.assertEqual(status, 400)
                self.assertEqual(payload["error"], "Expected a JSON object")

    def test_invalid_agent_rejected(self):
        status, payload = self.call(b'{"agent":"unknown","prompt":"Hello"}')
        self.assertEqual(status, 400)

    def test_missing_key_never_calls_provider(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}), patch.object(api, "urlopen") as provider:
            status, payload = self.call(b'{"agent":"content","prompt":"Hello"}')
        self.assertEqual(status, 503)
        provider.assert_not_called()

    def test_unconfigured_access_fails_closed(self):
        with patch.dict(os.environ, {"NEXUSAI_ACCESS_TOKEN": ""}), patch.object(api, "urlopen") as provider:
            status, payload = self.call(b'{"agent":"content","prompt":"Hello"}')
        self.assertEqual(status, 503)
        provider.assert_not_called()

    def test_invalid_authorization_never_calls_provider(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}), patch.object(api, "urlopen") as provider:
            for authorization in (None, "", "Bearer wrong", "Basic abc", "Bearer badé"):
                status, payload = self.call(b'{"agent":"content","prompt":"Hello"}', authorization=authorization)
                self.assertEqual(status, 401)
            provider.assert_not_called()

    def test_bad_provider_responses_are_502(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            for content in (b'{}', b'{"choices":[]}', b'{"choices":[{"message":{"content":""}}]}', b'{"choices":[{"message":{"content":null}}]}'):
                with patch.object(api, "urlopen", return_value=io.BytesIO(content)):
                    status, payload = self.call(b'{"agent":"content","prompt":"Hello"}')
                self.assertEqual(status, 502)
                self.assertNotIn("detail", payload)

    def test_provider_success_mocked(self):
        content = b'{"choices":[{"message":{"content":"Mock result"}}]}'
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch.object(api, "urlopen", return_value=io.BytesIO(content)) as provider:
                status, payload = self.call(b'{"agent":"content","prompt":"Hello"}')
        self.assertEqual(status, 200)
        self.assertEqual(payload["answer"], "Mock result")
        provider.assert_called_once()

    def test_upstream_error_does_not_leak_provider_details(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch.object(api, "urlopen", side_effect=HTTPError("https://example.com", 500, "provider private diagnostics", None, None)):
                status, payload = self.call(b'{"agent":"content","prompt":"Hello"}')
        self.assertEqual(status, 502)
        self.assertNotIn("detail", payload)
        self.assertNotIn("private", json.dumps(payload))

    def test_malformed_provider_bodies_are_safe_502(self):
        bodies = (b"", b"<html>502 Bad Gateway</html>", b'{"choices":[', b"\xff\xfe\x00",
                  b"[1,2]", b'"x"', b"null", b'{"choices":["x"]}', b'{"choices":[{"message":"x"}]}',
                  b'{"choices":[{"message":{"content":42}}]}', b'{"choices":[{"message":{"content":"   "}}]}',
                  b"[" * 5000)
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            for content in bodies:
                with self.subTest(content=content[:30]):
                    with patch.object(api, "urlopen", return_value=io.BytesIO(content)):
                        status, payload = self.call(b'{"agent":"content","prompt":"Hello"}')
                    self.assertEqual(status, 502)
                    self.assertEqual(payload, {"error": "Invalid model provider response"})

    def test_oversized_provider_body_is_502(self):
        huge = b'{"choices":[{"message":{"content":"' + b"a" * (api.MAX_PROVIDER_BYTES + 10) + b'"}}]}'
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch.object(api, "urlopen", return_value=io.BytesIO(huge)):
                status, payload = self.call(b'{"agent":"content","prompt":"Hello"}')
        self.assertEqual(status, 502)

    def test_transport_failures_are_502_without_details(self):
        errors = (ConnectionResetError("secret-host"), http.client.IncompleteRead(b"x"),
                  http.client.RemoteDisconnected("secret-host"), TimeoutError("slow"), OSError("secret-host"))
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            for exc in errors:
                with self.subTest(exc=type(exc).__name__):
                    with patch.object(api, "urlopen", side_effect=exc):
                        status, payload = self.call(b'{"agent":"content","prompt":"Hello"}')
                    self.assertEqual(status, 502)
                    self.assertNotIn("secret", json.dumps(payload))

    def test_invalid_client_json_is_400_and_never_calls_provider(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}), patch.object(api, "urlopen") as provider:
            for body in (b"{", b"\xff\xfe", b"not json"):
                status, payload = self.call(body)
                self.assertEqual(status, 400)
            provider.assert_not_called()

    def test_unexpected_internal_error_is_generic_500(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch.object(api, "urlopen", side_effect=RuntimeError("sk-LEAK-DETAIL")):
                status, payload = self.call(b'{"agent":"content","prompt":"Hello"}')
        self.assertEqual(status, 500)
        self.assertNotIn("LEAK", json.dumps(payload))

    def test_responses_never_contain_configured_secrets(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-SECRET-KEY", "NEXUSAI_ACCESS_TOKEN": "tok-SECRET"}):
            status, payload = self.call(b"", "GET")
        text = json.dumps(payload)
        self.assertNotIn("SECRET", text)

if __name__ == "__main__":
    unittest.main()
