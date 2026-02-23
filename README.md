# Spotify IRC Bot (Playback Control)

An IRC bot that listens for commands and controls Spotify playback on a Spotify Connect device (e.g., `spotatui`).

This bot does not stream audio itself. It instructs Spotify to start playback on the target device.

## Features

- `!pl <playlist name|id|url|uri>`: play a playlist on a Spotify Connect device
- `!devices`: list available Spotify Connect devices

## Requirements

- Spotify Premium account (required for Spotify Connect playback control)
- Python 3.10+
- A running Spotify Connect device (Spotify app, or `spotatui`)

## Setup

### 1) Create a Spotify Developer App

1. Create an app in the Spotify Developer Dashboard.
2. Add a Redirect URI (recommended):
   - `http://127.0.0.1:8888/callback`
3. Save settings.

### 2) Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
3) Configure environment variables

Copy the example file and edit it:

cp .env.example .env

Export variables (one simple way):

set -a
source .env
set +a

Important:

Never commit .env

Never commit .spotify_cache

4) Run
python spotify_irc_bot.py

The first run opens a browser to complete Spotify OAuth.

Usage (in IRC)

!devices

!pl discover weekly

!pl spotify:playlist:<id>

!pl https://open.spotify.com/playlist/<id>

Notes

If the bot can’t find your device, start your player (Spotify app / spotatui) and play something once, then retry.

If you change scopes, delete the cache and re-auth:

rm -f .spotify_cache
Security

Use environment variables for secrets.

Do not run the bot as root.

Consider adding a command allowlist / admin-only controls if running in public channels.

License

MIT


---

## `LICENSE` (MIT)
If you want MIT, use the standard MIT license text with your name/year.

---

## Before you publish (quick safety checklist)
- Replace `IRC_SERVER`/`IRC_CHANNEL` in your `.env` locally, not in code.
- Ensure `.spotify_cache` is ignored and not tracked:
  ```bash
  git status --ignored

If you accidentally committed secrets:

rotate Spotify client secret in the dashboard
