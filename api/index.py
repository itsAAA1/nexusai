from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        payload = {
            "project": "NexusAI",
            "status": "online",
            "agent_stack": {
                "langgraph": "source_verified_not_deployed",
                "browser_use": "source_verified_not_deployed",
                "crewai": "source_verified_not_deployed",
                "dify": "source_verified_not_deployed"
            }
        }
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
