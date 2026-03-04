# Authentication Setup

## 1. Create a TickTick OAuth App

1. Go to [developer.ticktick.com/docs](https://developer.ticktick.com/docs)
2. Click **"Manage Apps"** in the top right and log in with your TickTick account
3. Click **"+ App Name"** to create a new app (only the name is required)
4. Copy your **Client ID** and **Client Secret**
5. Set the **OAuth Redirect URL** to `http://127.0.0.1:8000/callback`

## 2. Save Credentials

Create the config file at `~/.config/tt/.env`:

```
TICKTICK_CLIENT_ID=your_client_id
TICKTICK_CLIENT_SECRET=your_client_secret
```

## 3. Run the OAuth Flow

```bash
uv run python -m tt auth
```

This opens your browser, asks you to authorize the app, then saves the access and refresh tokens to `~/.config/tt/.env`.

## Notes

- Tokens persist across reboots — no need to re-auth unless the token expires
- To check if your token is still valid: `uv run python -m tt auth --status`
- The tool is run via `uv run python -m tt <command>` — no global installation needed
