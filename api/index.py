import json
import os
import hmac
from http.server import BaseHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

AGENTS = {
    "content": "You are ContentBot, an expert Arabic and English content writer.",
    "code": "You are CodeBot, a careful software engineer. Produce working code and tests.",
    "marketing": "You are MarketBot, a practical digital marketing strategist.",
    "image": "You are ImageBot, a creative image prompt specialist. Produce detailed image prompts, not image files.",
    "data": "You are DataBot, a rigorous data analyst. Never invent figures.",
}

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
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 32768:
                return self.respond(413, {"error": "Request must be 1-32768 bytes"})
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                return self.respond(400, {"error": "Expected a JSON object"})
            agent = body.get("agent", "")
            prompt = body.get("prompt", "")
            if agent not in AGENTS or not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 12000:
                return self.respond(400, {"error": "Invalid agent or prompt"})
            key = os.getenv("OPENAI_API_KEY")
            if not key:
                return self.respond(503, {"error": "Inference not configured: OPENAI_API_KEY is missing"})
            payload = json.dumps({
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "messages": [{"role": "system", "content": AGENTS[agent]},
                             {"role": "user", "content": prompt}],
                "max_tokens": 1200
            }).encode("utf-8")
            request = Request("https://api.openai.com/v1/chat/completions",
                              data=payload,
                              headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
                              method="POST")
            with urlopen(request, timeout=25) as response:
                result = json.load(response)
            try:
                answer = result["choices"][0]["message"]["content"]
            except (IndexError, KeyError, TypeError):
                return self.respond(502, {"error": "Invalid model provider response"})
            if not isinstance(answer, str) or not answer.strip():
                return self.respond(502, {"error": "Invalid model provider response"})
            self.respond(200, {"agent": agent, "answer": answer})
        except (HTTPError, URLError, TimeoutError) as exc:
            self.respond(502, {"error": "Model provider request failed"})
        except (ValueError, KeyError, TypeError):
            self.respond(400, {"error": "Invalid request or provider response"})
