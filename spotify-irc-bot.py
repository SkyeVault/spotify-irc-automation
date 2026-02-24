import os
import re
import ssl

import irc.client
import irc.connection
import spotipy
from spotipy.oauth2 import SpotifyOAuth


def getenv_required(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise SystemExit(f"Missing required environment variable: {key}")
    return val


IRC_SERVER = os.getenv("IRC_SERVER", "irc.example.org")
IRC_PORT = int(os.getenv("IRC_PORT", "6697"))
IRC_NICK = os.getenv("IRC_NICK", "yourname-bot")
IRC_CHANNEL = os.getenv("IRC_CHANNEL", "#music")

SPOTIFY_DEVICE_NAME = os.getenv("SPOTIFY_DEVICE_NAME", "spotatui")
SPOTIFY_SCOPE = os.getenv(
    "SPOTIFY_SCOPE",
    "user-modify-playback-state user-read-playback-state playlist-read-private",
)

SPOTIPY_CACHE_PATH = os.getenv("SPOTIPY_CACHE_PATH", ".spotify_cache")


def normalize_playlist_ref(s: str) -> str:
    s = s.strip()
    if s.startswith("spotify:playlist:"):
        return s
    m = re.search(r"open\.spotify\.com/playlist/([A-Za-z0-9]+)", s)
    if m:
        return f"spotify:playlist:{m.group(1)}"
    if re.fullmatch(r"[A-Za-z0-9]{22}", s):
        return f"spotify:playlist:{s}"
    return s  # treat as name search


def resolve_playlist_uri(sp: spotipy.Spotify, ref: str) -> tuple[str, str]:
    if ref.startswith("spotify:playlist:"):
        pl_id = ref.split(":")[-1]
        pl = sp.playlist(pl_id, fields="name,uri")
        return pl["uri"], pl["name"]

    results = sp.search(q=ref, type="playlist", limit=5)
    items = results.get("playlists", {}).get("items", [])
    if not items:
        raise RuntimeError(f"No playlist found for: {ref}")
    pl = items[0]
    return pl["uri"], pl["name"]


def pick_device(sp: spotipy.Spotify) -> dict | None:
    devices = sp.devices().get("devices", [])
    if not devices:
        return None

    # exact name match first
    for d in devices:
        if d.get("name", "").lower() == SPOTIFY_DEVICE_NAME.lower():
            return d

    # else active device
    for d in devices:
        if d.get("is_active"):
            return d

    return devices[0]


def main():
    # Ensure required Spotify OAuth env vars exist (fail fast)
    getenv_required("SPOTIPY_CLIENT_ID")
    getenv_required("SPOTIPY_CLIENT_SECRET")
    getenv_required("SPOTIPY_REDIRECT_URI")

    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope=SPOTIFY_SCOPE,
            cache_path=SPOTIPY_CACHE_PATH,
        )
    )

    reactor = irc.client.Reactor()

    # TLS with SNI (server_hostname) to avoid: "check_hostname requires server_hostname"
    ssl_ctx = ssl.create_default_context()

    def tls_wrap(sock):
        return ssl_ctx.wrap_socket(sock, server_hostname=IRC_SERVER)

    c = reactor.server().connect(
        IRC_SERVER,
        IRC_PORT,
        IRC_NICK,
        connect_factory=irc.connection.Factory(wrapper=tls_wrap),
    )

    def on_welcome(conn, event):
        conn.join(IRC_CHANNEL)
        conn.privmsg(IRC_CHANNEL, "spotiBot online. Usage: !pl <playlist name|id|url|uri> | !devices")

    def on_pubmsg(conn, event):
        msg = event.arguments[0].strip()

        if msg == "!devices":
            try:
                ds = sp.devices().get("devices", [])
                if not ds:
                    conn.privmsg(IRC_CHANNEL, "No Spotify Connect devices found.")
                    return
                parts = []
                for d in ds:
                    name = d.get("name", "?")
                    dtype = d.get("type", "?")
                    active = "active" if d.get("is_active") else "idle"
                    parts.append(f"{name} ({dtype}, {active})")
                conn.privmsg(IRC_CHANNEL, "Devices: " + " | ".join(parts))
            except Exception as e:
                conn.privmsg(IRC_CHANNEL, f"Error: {type(e).__name__}: {e}")
            return

        if not msg.startswith("!pl"):
            return

        arg = msg[3:].strip()
        if not arg:
            conn.privmsg(IRC_CHANNEL, "Usage: !pl <playlist name|id|url|uri>")
            return

        try:
            playlist_ref = normalize_playlist_ref(arg)
            playlist_uri, playlist_name = resolve_playlist_uri(sp, playlist_ref)

            device = pick_device(sp)
            if device is None:
                conn.privmsg(
                    IRC_CHANNEL,
                    "No Spotify Connect device found. Start a player (e.g., spotatui) and try again.",
                )
                return

            # Make the device active first (helps reliability)
            sp.transfer_playback(device_id=device["id"], force_play=True)
            sp.start_playback(device_id=device["id"], context_uri=playlist_uri)

            conn.privmsg(IRC_CHANNEL, f"Playing '{playlist_name}' on {device['name']}")
        except Exception as e:
            conn.privmsg(IRC_CHANNEL, f"Error: {type(e).__name__}: {e}")

    c.add_global_handler("welcome", on_welcome)
    c.add_global_handler("pubmsg", on_pubmsg)

    reactor.process_forever()


if __name__ == "__main__":
    main()
