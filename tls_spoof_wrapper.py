#!/usr/bin/env python3

import os
import random
import requests
from flask import Flask, request, Response, jsonify
from dotenv import load_dotenv

load_dotenv()

TLS_SPOOF_PROXY_HOST = os.getenv("TLS_SPOOF_PROXY_HOST")
TLS_SPOOF_PROXY = f"https://{TLS_SPOOF_PROXY_HOST}/handle"
PROXY_LIST = os.getenv("OUTBOUND_PROXY_LIST", "").split(",")
LISTEN_PORT = int(os.getenv("TLS_SPOOF_WRAPPER_PORT", "8888"))

app = Flask(__name__)

CHROME_USER_AGENT = os.getenv("CHROME_USER_AGENT", "Mozilla/5.0")
CHROME_JA3 = os.getenv("CHROME_JA3", "")

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"response": "pong"}), 200

@app.route('/', defaults={'path': ''}, methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
@app.route('/<path:path>', methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
def proxy(path):
    try:
        method = request.method
        target_url = request.headers.get("X-Target-URL")
        if not target_url:
            return jsonify({"error": "X-Target-URL header missing"}), 400

        outgoing_proxy = random.choice(PROXY_LIST) if PROXY_LIST and PROXY_LIST[0] else None

        payload = {
            "Url": target_url,
            "Method": method,
            "Headers": dict(request.headers),
            "UserAgent": CHROME_USER_AGENT,
            "Ja3": CHROME_JA3,
            "Timeout": 20,
            "DisableRedirect": False,
            "InsecureSkipVerify": False,
            "Cookies": [],
        }

        if method in ["POST", "PUT", "PATCH"]:
            try:
                payload["Payload"] = request.get_data(as_text=True)
            except Exception:
                payload["Payload"] = ""

        if outgoing_proxy:
            payload["Proxy"] = outgoing_proxy

        resp = requests.post(TLS_SPOOF_PROXY, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("success"):
            return jsonify({"error": "TLS proxy error", "details": data.get("error")}), 502

        proxy_payload = data.get("payload", {})
        status_code = proxy_payload.get("status", 200)
        response_text = proxy_payload.get("text", "")
        response_headers = proxy_payload.get("headers", {})

        return Response(response=response_text, status=status_code, headers=response_headers)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=LISTEN_PORT)
