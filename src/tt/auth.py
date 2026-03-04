import base64
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import requests

from tt.config import get_client_credentials, save_tokens

AUTHORIZE_URL = "https://ticktick.com/oauth/authorize"
TOKEN_URL = "https://ticktick.com/oauth/token"
REDIRECT_URI = "http://127.0.0.1:8000/callback"
SCOPES = "tasks:read tasks:write"
TIMEOUT = 300  # 5 minutes


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    auth_code: str | None = None
    state: str | None = None
    error: str | None = None

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        params = parse_qs(parsed.query)

        if "error" in params:
            OAuthCallbackHandler.error = params["error"][0]
            self._respond("Authorization failed. You can close this tab.")
            return

        OAuthCallbackHandler.auth_code = params.get("code", [None])[0]
        OAuthCallbackHandler.state = params.get("state", [None])[0]
        self._respond("Authorization successful! You can close this tab.")

    def _respond(self, message: str):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        body = f"<html><body><p>{message}</p></body></html>"
        self.wfile.write(body.encode())

    def log_message(self, format, *args):
        pass  # suppress request logs


def _exchange_code(code: str, client_id: str, client_secret: str) -> dict:
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    resp = requests.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        },
    )
    resp.raise_for_status()
    return resp.json()


def refresh_access_token(refresh_token: str, client_id: str, client_secret: str) -> dict:
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    resp = requests.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
    )
    resp.raise_for_status()
    return resp.json()


def run_oauth_flow() -> None:
    client_id, client_secret = get_client_credentials()
    csrf_state = secrets.token_urlsafe(32)

    # Reset handler state
    OAuthCallbackHandler.auth_code = None
    OAuthCallbackHandler.state = None
    OAuthCallbackHandler.error = None

    server = HTTPServer(("127.0.0.1", 8000), OAuthCallbackHandler)
    server.timeout = TIMEOUT

    auth_url = (
        f"{AUTHORIZE_URL}"
        f"?client_id={client_id}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={SCOPES}"
        f"&state={csrf_state}"
    )

    print("Opening browser for authorization...")
    print(f"If the browser doesn't open, visit:\n{auth_url}")
    webbrowser.open(auth_url)

    # Wait for callback
    server_thread = threading.Thread(target=server.handle_request)
    server_thread.start()
    server_thread.join(timeout=TIMEOUT)
    server.server_close()

    if OAuthCallbackHandler.error:
        raise RuntimeError(f"Authorization failed: {OAuthCallbackHandler.error}")

    if not OAuthCallbackHandler.auth_code:
        raise RuntimeError("Authorization timed out (5 min). Try again.")

    if OAuthCallbackHandler.state != csrf_state:
        raise RuntimeError("CSRF state mismatch. Possible attack — aborting.")

    # Exchange code for tokens
    token_data = _exchange_code(OAuthCallbackHandler.auth_code, client_id, client_secret)
    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token", "")

    save_tokens(access_token, refresh_token)
    print("Authenticated successfully! Tokens saved.")
