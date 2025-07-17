#!/usr/bin/env python3
import os
import json
import random
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, urlunparse
from dotenv import load_dotenv

load_dotenv()

TLS_SPOOF_PROXY = f"https://{os.getenv('TLS_SPOOF_PROXY_HOST')}/handle"
CHROME_USER_AGENT = os.getenv("CHROME_USER_AGENT", "Mozilla/5.0")
CHROME_JA3 = os.getenv("CHROME_JA3", "")
PROXY_LIST = os.getenv("OUTBOUND_PROXY_LIST", "").split(",")
LISTEN_PORT = int(os.getenv("TLS_SPOOF_WRAPPER_PORT", "8888"))

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self): self.forward_request()
    def do_POST(self): self.forward_request()
    def do_PUT(self): self.forward_request()
    def do_DELETE(self): self.forward_request()
    def do_HEAD(self): self.forward_request()
    def do_OPTIONS(self): self.forward_request()
    def do_PATCH(self): self.forward_request()

    def forward_request(self):
        try:
            # Parse and rewrite target URL to HTTPS
            parsed = urlparse(self.path)

            if not parsed.scheme:
                host = self.headers.get("Host")
                if not host:
                    self.send_error(400, "Missing Host header")
                    return
                target_url = f"https://{host}{self.path}"
            else:
                parsed = parsed._replace(scheme="https")
                target_url = urlunparse(parsed)

            # Body handling
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""

            outgoing_proxy = random.choice(PROXY_LIST) if PROXY_LIST and PROXY_LIST[0] else None

            spoof_request = {
                "Url": target_url,
                "Method": self.command,
                "Headers": dict(self.headers),
                "UserAgent": CHROME_USER_AGENT,
                "Ja3": CHROME_JA3,
                "Timeout": 20,
                "DisableRedirect": False,
                "InsecureSkipVerify": False,
                "Cookies": [],
                "Body": body,
            }

            if outgoing_proxy:
                spoof_request["Proxy"] = outgoing_proxy

            # Send to tls_spoof_proxy
            resp = requests.post(TLS_SPOOF_PROXY, json=spoof_request, timeout=30)
            data = resp.json()

            if not data.get("success"):
                self.send_error(502, f"TLS spoof proxy error: {data.get('error')}")
                return

            payload = data.get("payload", {})
            self.send_response(payload.get("status", 200))

            for k, v in payload.get("headers", {}).items():
                try:
                    self.send_header(k, v)
                except Exception:
                    pass
            self.end_headers()
            self.wfile.write(payload.get("text", "").encode("utf-8"))

        except Exception as e:
            self.send_error(500, f"Proxy wrapper error: {str(e)}")

def run():
    server_address = ("0.0.0.0", LISTEN_PORT)
    httpd = HTTPServer(server_address, ProxyHandler)
    print(f"[*] TLS spoofing wrapper proxy running on port {LISTEN_PORT}")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
