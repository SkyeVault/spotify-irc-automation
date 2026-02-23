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
