#!/usr/bin/env python3

import requests
import argparse
import os
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()

TLS_SPOOF_PROXY_HOST = os.getenv("TLS_SPOOF_PROXY_HOST")
TLS_SPOOF_PROXY_URL = f"https://{TLS_SPOOF_PROXY_HOST}/handle"
TARGET_URL = os.getenv("TEST_TARGET_URL")
CHROME_USER_AGENT = os.getenv("CHROME_USER_AGENT")
CHROME_JA3 = os.getenv("CHROME_JA3")

# --- Argument parsing ---
parser = argparse.ArgumentParser(description="Send request to TLS spoofing proxy or directly")
parser.add_argument("--proxy", help="Proxy URL in format http://IP:PORT or http://USER:PASS@IP:PORT", default=None)
parser.add_argument("--clean", action="store_true", help="Only print the response body (payload.text)")
parser.add_argument("--direct", action="store_true", help="Send request directly to TARGET_URL (bypass TLS_SPOOF_PROXY)")
args = parser.parse_args()

# --- Request payload ---
payload = {
    "Url": TARGET_URL,
    "Method": "GET",
    "Headers": {
        "Accept": "*/*"
    },
    "UserAgent": CHROME_USER_AGENT,
    "Ja3": CHROME_JA3,
    "Timeout": 20,
    "DisableRedirect": False,
    "InsecureSkipVerify": False,
    "Cookies": []
}

# Add proxy if passed
if args.proxy:
    payload["Proxy"] = args.proxy

# --- Send request ---
try:
    if args.direct:
        if args.clean == False:
            print("[*] Sending direct request to TARGET_URL...")
        headers = {
            "User-Agent": CHROME_USER_AGENT,
            "Accept": "*/*"
        }
        proxies = {"http": args.proxy, "https": args.proxy} if args.proxy else None
        response = requests.get(TARGET_URL, headers=headers, proxies=proxies, timeout=30)
        response.raise_for_status()

        if args.clean:
            print(response.text)
        else:
            print("[+] Response status:", response.status_code)
            print("[+] Response body:\n", response.text)
    else:
        if args.clean == False:
            print("[*] Sending request via TLS proxy...")
        payload = {
            "Url": TARGET_URL,
            "Method": "GET",
            "Headers": {
                "Accept": "*/*"
            },
            "UserAgent": CHROME_USER_AGENT,
            "Ja3": CHROME_JA3,
            "Timeout": 20,
            "DisableRedirect": False,
            "InsecureSkipVerify": False,
            "Cookies": []
        }

        if args.proxy:
            payload["Proxy"] = args.proxy

        response = requests.post(TLS_SPOOF_PROXY_URL, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("success"):
            if args.clean:
                print(data["payload"]["text"])
            else:
                print("[+] Response status:", data["payload"]["status"])
                print("[+] Response body:\n", data["payload"]["text"])
        else:
            print("[-] TLS-Proxy error:", data.get("error"))
            print("[*] Full response:", data)

except requests.RequestException as e:
    print("[-] Request failed:", e)