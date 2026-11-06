import json
import os
import hmac
import http.client
from http.server import BaseHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
import ipaddress

AGENTS = {
    "content": "You are ContentBot, an expert Arabic and English content writer.",
    "code": "You are CodeBot, a careful software engineer. Produce working code and tests.",
    "marketing": "You are MarketBot, a practical digital marketing strategist.",
    "image": "You are ImageBot, a creative image prompt specialist. Produce detailed image prompts, not image files.",
    "data": "You are DataBot, a rigorous data analyst. Never invent figures.",
}

MAX_PROVIDER_BYTES = 1_000_000

DEFAULT_PROVIDER_BASE = "https://api.openai.com/v1"

def provider_endpoint():
    """Validate configured HTTPS base before using a server-side provider."""
    base = os.getenv("OPENAI_BASE_URL", "").strip() or DEFAULT_PROVIDER_BASE
    try:
        parsed = urlsplit(base)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            return None
        if parsed.query or parsed.fragment:
            return None
        host = parsed.hostname.lower()
        if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
            return None
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            if not ip.is_global:
                return None
        return base.rstrip("/") + "/chat/completions"
    except ValueError:
        return None

def output_limit():
    raw = os.getenv("OPENAI_MAX_TOKENS", "").strip() or "1200"
    try:
        value = int(raw)
    except ValueError:
        return None
    return value if 64 <= value <= 8192 else None

class handler(BaseHTTPRequestHandler):
    def respond(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.respond(200, {})

    def do_GET(self):
        self.respond(200, {
            "project": "NexusAI",
            "api": "online",
            "agents": list(AGENTS),
            "inference_configured": bool(os.getenv("OPENAI_API_KEY")),
            "access_configured": bool(os.getenv("NEXUSAI_ACCESS_TOKEN")),
            "runtime": "Python standard-library HTTP handler",
            "usage": "POST /api with JSON: agent=content|code|marketing|image|data, prompt=text"
        })

    def do_POST(self):
        try:
            expected_token = os.getenv("NEXUSAI_ACCESS_TOKEN", "")
            if not expected_token or not expected_token.isascii():
                return self.respond(503, {"error": "Service access not configured"})
            auth = self.headers.get("Authorization", "")
            if not isinstance(auth, str) or not auth.isascii() or not auth.startswith("Bearer "):
                return self.respond(401, {"error": "Unauthorized"})
            supplied_token = auth[7:]
            if not supplied_token or not hmac.compare_digest(supplied_token, expected_token):
                return self.respond(401, {"error": "Unauthorized"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except (TypeError, ValueError):
                return self.respond(400, {"error": "Invalid Content-Length"})
            if length < 1 or length > 32768:
                return self.respond(413, {"error": "Request must be 1-32768 bytes"})
            try:
                body = json.loads(self.rfile.read(length))
            except (ValueError, RecursionError):
                return self.respond(400, {"error": "Invalid JSON request body"})
            if not isinstance(body, dict):
                return self.respond(400, {"error": "Expected a JSON object"})
            agent = body.get("agent", "")
            prompt = body.get("prompt", "")
            if not isinstance(agent, str) or agent not in AGENTS or not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 12000:
                return self.respond(400, {"error": "Invalid agent or prompt"})
            key = os.getenv("OPENAI_API_KEY")
            if not key:
                return self.respond(503, {"error": "Inference not configured: OPENAI_API_KEY is missing"})
            endpoint = provider_endpoint()
            max_tokens = output_limit()
            if not endpoint or max_tokens is None:
                return self.respond(503, {"error": "Model provider configuration invalid"})
            payload = json.dumps({
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "messages": [{"role": "system", "content": AGENTS[agent]},
                             {"role": "user", "content": prompt}],
                "max_tokens": max_tokens
            }).encode("utf-8")
            request = Request(endpoint,
                              data=payload,
                              headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
                              method="POST")
            # Everything that can go wrong talking to / parsing the provider is a
            # bad gateway (502) with a generic message; no provider detail is leaked.
            try:
                with urlopen(request, timeout=25) as response:
                    raw = response.read(MAX_PROVIDER_BYTES + 1)
                if len(raw) > MAX_PROVIDER_BYTES:
                    raise ValueError("provider response too large")
                result = json.loads(raw)
                answer = result["choices"][0]["message"]["content"]
            except HTTPError as upstream:
                # Whitelist a coarse error category, never relay the upstream body
                # or any credentials. Authentication is checked above.
                code = upstream.code if isinstance(upstream.code, int) and 400 <= upstream.code <= 599 else 502
                category = "UNCLASSIFIED"
                try:
                    body = upstream.read(8192)
                    detail = json.loads(body)
                    error = detail.get("error", {}) if isinstance(detail, dict) else {}
                    if isinstance(error, dict):
                        info = error.get("details", [])
                        reasons = [d.get("reason", "") for d in info if isinstance(d, dict)] if isinstance(info, list) else []
                        message = str(error.get("message", "")).lower()
                        status = str(error.get("status", ""))
                        if "API_KEY_INVALID" in reasons or "api key not valid" in message:
                            category = "API_KEY_INVALID"
                        elif "FAILED_PRECONDITION" == status or "free tier is not available" in message:
                            category = "FAILED_PRECONDITION"
                        elif "API_KEY_SERVICE_BLOCKED" in reasons:
                            category = "API_KEY_SERVICE_BLOCKED"
                        elif "not found" in message and "model" in message:
                            category = "MODEL_NOT_FOUND"
                        elif "unknown name" in message or "cannot find field" in message:
                            category = "UNSUPPORTED_PARAMETER"
                        elif status in {"INVALID_ARGUMENT", "PERMISSION_DENIED", "RESOURCE_EXHAUSTED", "UNAUTHENTICATED", "NOT_FOUND"}:
                            category = status
                except (OSError, ValueError, TypeError, AttributeError):
                    pass
                return self.respond(502, {"error": "Model provider rejected request",
                                          "provider_status": code, "provider_reason": category})
            except (OSError, http.client.HTTPException, ValueError, RecursionError,
                    KeyError, IndexError, TypeError, AttributeError):
                return self.respond(502, {"error": "Invalid model provider response"})
            if not isinstance(answer, str) or not answer.strip():
                return self.respond(502, {"error": "Invalid model provider response"})
            self.respond(200, {"agent": agent, "answer": answer})
        except Exception:
            # Never let an unexpected error escape with a stack trace or detail.
            self.respond(500, {"error": "Internal error"})
