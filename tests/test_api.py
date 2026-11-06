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

    def call(self, body, method="POST", authorization="Bearer test-token", path="/api"):
        handler = api.handler.__new__(api.handler)
        handler.path = path
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

    def test_read_only_google_model_probe_success(self):
        metadata = b'{"name":"models/gemini-3.6-flash"}'
        env = {
            "OPENAI_API_KEY": "test-google-key",
            "OPENAI_MODEL": "gemini-3.6-flash",
            "OPENAI_BASE_URL": "https://generativelanguage.googleapis.com/v1beta/openai",
        }
        with patch.dict(os.environ, env), patch.object(api, "urlopen", return_value=io.BytesIO(metadata)) as provider:
            status, payload = self.call(b"", "GET", path="/api?provider_check=1")
        self.assertEqual(status, 200)
        self.assertTrue(payload["model_available"])
        self.assertEqual(payload["provider_http_status"], 200)
        provider.assert_called_once()
        request = provider.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(request.full_url, "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash")
        self.assertNotIn("test-google-key", json.dumps(payload))

    def test_google_probe_rejects_wrong_access_token(self):
        env = {
            "OPENAI_API_KEY": "test-google-key",
            "OPENAI_MODEL": "gemini-3.6-flash",
            "OPENAI_BASE_URL": "https://generativelanguage.googleapis.com/v1beta/openai",
        }
        with patch.dict(os.environ, env), patch.object(api, "urlopen") as provider:
            status, _ = self.call(b"", "GET", authorization="Bearer wrong", path="/api?provider_check=1")
        self.assertEqual(status, 401)
        provider.assert_not_called()

    def test_google_probe_error_hides_provider_message(self):
        env = {
            "OPENAI_API_KEY": "test-google-key",
            "OPENAI_MODEL": "gemini-3.6-flash",
            "OPENAI_BASE_URL": "https://generativelanguage.googleapis.com/v1beta/openai",
        }
        body = io.BytesIO(b'{"error":{"message":"secret provider message"}}')
        with patch.dict(os.environ, env), patch.object(api, "urlopen", side_effect=HTTPError("https://example.com",400,"bad",{},body)):
            status, payload = self.call(b"", "GET", path="/api?provider_check=1")
        self.assertEqual(status, 200)
        self.assertEqual(payload["provider_http_status"], 400)
        self.assertNotIn("secret", json.dumps(payload))

    def test_json_root_must_be_object(self):
        for value in ([], 12, True, None, "hello"):
            with self.subTest(value=value):
                status, payload = self.call(json.dumps(value).encode())
                self.assertEqual(status, 400)
                self.assertEqual(payload["error"], "Expected a JSON object")

    def test_invalid_agent_rejected(self):
        status, payload = self.call(b'{"agent":"unknown","prompt":"Hello"}')
        self.assertEqual(status, 400)

    def test_invalid_agent_types_return_400_not_500(self):
        for agent in ([], {}, 123, None, True):
            with self.subTest(agent=agent):
                status, payload = self.call(json.dumps({"agent": agent, "prompt": "Hello"}).encode())
                self.assertEqual(status, 400)
                self.assertEqual(payload["error"], "Invalid agent or prompt")

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

    def test_provider_errors_wrapped_in_arrays_are_classified(self):
        for message, expected in (
            ("API key not valid. Please pass a valid API key.", "invalid_api_key"),
            ("Request contains an invalid argument.", "invalid_request")
        ):
            payload=json.dumps([{"error":{"code":400,"message":message,"status":"INVALID_ARGUMENT"}}]).encode()
            err=HTTPError("https://example.com",400,"private",None,io.BytesIO(payload))
            with patch.dict(os.environ, {"OPENAI_API_KEY":"key"}), patch.object(api,"urlopen",side_effect=err):
                status,result=self.call(b'{"agent":"content","prompt":"test"}')
            self.assertEqual(status,502)
            self.assertEqual(result["provider_issue"],expected)
            self.assertNotIn(message,json.dumps(result))

    def test_provider_error_classification_never_reveals_key_or_error_message(self):
        private = [
            ('API key not valid. Please pass a valid API key.', 'invalid_api_key'),
            ('Request contains an invalid argument.', 'invalid_request'),
            ('Unknown name "store": Cannot find field.', 'unsupported_parameter'),
            ('Quota exceeded for this API key.', 'quota_or_rate_limit'),
        ]
        for message, expected in private:
            payload = json.dumps({"error":{"code":400,"message":message}}).encode()
            err = HTTPError("https://example.com",400,"Private upstream error",None,io.BytesIO(payload))
            with self.subTest(expected=expected), patch.dict(os.environ, {"OPENAI_API_KEY":"private-key-123"}):
                with patch.object(api, "urlopen",side_effect=err):
                    status,result=self.call(b'{"agent":"content","prompt":"test"}')
            self.assertEqual(status,502)
            self.assertEqual(result["provider_issue"],expected)
            self.assertEqual(result["provider_status"],400)
            self.assertNotIn(message,json.dumps(result))
            self.assertNotIn("private-key-123",json.dumps(result))

    def test_http_provider_errors_expose_only_safe_numeric_status(self):
        for code in (400, 401, 403, 404, 429, 500):
            with self.subTest(code=code), patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
                with patch.object(api, "urlopen", side_effect=HTTPError("https://example.com", code, "provider private diagnostics", None, None)):
                    status, payload = self.call(b'{"agent":"content","prompt":"Hello"}')
            self.assertEqual(status, 502)
            self.assertEqual(payload["provider_status"], code)
            self.assertEqual(payload["error"], "Model provider rejected request")
            self.assertNotIn("private", json.dumps(payload))
            self.assertNotIn("test-key", json.dumps(payload))

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

    def test_native_gemini_success_and_payload(self):
        reply = b'{"candidates":[{"content":{"parts":[{"text":"NEXUS_OK"}]}}]}'
        cfg = {
            "AI_PROVIDER": "gemini", "OPENAI_API_KEY": "test-google-key",
            "OPENAI_MODEL": "gemini-3.6-flash", "OPENAI_MAX_TOKENS": "4000",
        }
        with patch.dict(os.environ, cfg), patch.object(api, "urlopen", return_value=io.BytesIO(reply)) as gateway:
            status, result = self.call(b'{"agent":"content","prompt":"Hello"}')
        self.assertEqual(status, 200)
        self.assertEqual(result["answer"], "NEXUS_OK")
        req = gateway.call_args.args[0]
        self.assertEqual(req.full_url, "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent")
        body = json.loads(req.data)
        self.assertEqual(body["generationConfig"]["maxOutputTokens"], 4000)
        self.assertEqual(body["contents"][0]["parts"][0]["text"], "Hello")
        self.assertIn("X-goog-api-key", req.headers)
        self.assertNotIn("Authorization", req.headers)

    def test_native_gemini_rejects_bad_model_before_network(self):
        for model in ("../private", "something?inject=true", "", "model name"):
            with self.subTest(model=model):
                with patch.dict(os.environ, {"AI_PROVIDER":"gemini","OPENAI_API_KEY":"test-key","OPENAI_MODEL":model}), patch.object(api, "urlopen") as gateway:
                    status, _ = self.call(b'{"agent":"content","prompt":"Hello"}')
                self.assertEqual(status, 503)
                gateway.assert_not_called()

    def test_unknown_provider_fails_closed(self):
        with patch.dict(os.environ, {"AI_PROVIDER":"unknown","OPENAI_API_KEY":"test-key"}), patch.object(api, "urlopen") as gateway:
            status, _ = self.call(b'{"agent":"content","prompt":"Hello"}')
        self.assertEqual(status, 503)
        gateway.assert_not_called()

    def test_gemini_compatible_endpoint_and_max_tokens(self):
        reply = b'{"choices":[{"message":{"content":"Gemini mocked"}}]}'
        config = {
            "OPENAI_API_KEY": "test-key",
            "OPENAI_BASE_URL": "https://generativelanguage.googleapis.com/v1beta/openai",
            "OPENAI_MODEL": "gemini-3.6-flash",
            "OPENAI_MAX_TOKENS": "4000",
        }
        with patch.dict(os.environ, config), patch.object(api, "urlopen", return_value=io.BytesIO(reply)) as provider:
            status, payload = self.call(b'{"agent":"content","prompt":"Hello"}')
        self.assertEqual(status, 200)
        self.assertEqual(payload["answer"], "Gemini mocked")
        req = provider.call_args.args[0]
        self.assertEqual(req.full_url, "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions")
        body = json.loads(req.data)
        self.assertEqual(body["max_tokens"], 4000)
        self.assertEqual(body["model"], "gemini-3.6-flash")

    def test_invalid_provider_urls_rejected_without_network_calls(self):
        for url in ("http://example.com/v1", "https://localhost/v1", "https://127.0.0.1/v1", "https://example.com/v1?x=y", "ftp://example.com/v1"):
            with self.subTest(url=url):
                with patch.dict(os.environ, {"OPENAI_API_KEY":"test-key", "OPENAI_BASE_URL":url}), patch.object(api, "urlopen") as provider:
                    status, payload = self.call(b'{"agent":"content","prompt":"Hello"}')
                self.assertEqual(status, 503)
                provider.assert_not_called()

    def test_invalid_output_limits_rejected_without_network_calls(self):
        for value in ("63", "8193", "abc", "-1"):
            with self.subTest(value=value):
                with patch.dict(os.environ, {"OPENAI_API_KEY":"test-key", "OPENAI_MAX_TOKENS":value}), patch.object(api, "urlopen") as provider:
                    status, payload = self.call(b'{"agent":"content","prompt":"Hello"}')
                self.assertEqual(status, 503)
                provider.assert_not_called()

    def test_default_provider_and_output_limit(self):
        reply = b'{"choices":[{"message":{"content":"OpenAI mocked"}}]}'
        with patch.dict(os.environ, {"OPENAI_API_KEY":"test-key", "OPENAI_BASE_URL":"", "OPENAI_MAX_TOKENS":""}), patch.object(api, "urlopen", return_value=io.BytesIO(reply)) as provider:
            status, _ = self.call(b'{"agent":"content","prompt":"Hello"}')
        self.assertEqual(status, 200)
        req = provider.call_args.args[0]
        self.assertEqual(req.full_url, "https://api.openai.com/v1/chat/completions")
        self.assertEqual(json.loads(req.data)["max_tokens"], 1200)

if __name__ == "__main__":
    unittest.main()
