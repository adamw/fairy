#!/usr/bin/env python3
"""Test Spotify API access from the Pi.

Verifies: authentication, token refresh, device listing, playlist listing.
Run on the Pi after copying .spotify_cache from your desktop.

Requires env vars SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET,
or edit them below.
"""

import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

SCOPES = " ".join([
    "user-read-playback-state",
    "user-modify-playback-state",
    "playlist-read-private",
    "playlist-read-collaborative",
])

CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", ".spotify_cache")

client_id = os.environ.get("SPOTIPY_CLIENT_ID", "")
client_secret = os.environ.get("SPOTIPY_CLIENT_SECRET", "")
redirect_uri = os.environ.get("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

if not client_id or not client_secret:
    print("Set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables.")
    raise SystemExit(1)

auth_manager = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=SCOPES,
    cache_path=CACHE_PATH,
)

sp = spotipy.Spotify(auth_manager=auth_manager)

# 1. Check auth
print("=== Authentication ===")
user = sp.current_user()
print(f"User: {user['display_name']} ({user['id']})")

# 2. List devices
print("\n=== Devices ===")
devices = sp.devices()
if devices["devices"]:
    for d in devices["devices"]:
        active = " (active)" if d["is_active"] else ""
        print(f"  {d['name']} — {d['type']}, id={d['id']}{active}")
else:
    print("  No devices found. Make sure a Spotify player is open/active.")

# 3. List playlists
print("\n=== Playlists (first 20) ===")
playlists = sp.current_user_playlists(limit=20)
for i, p in enumerate(playlists["items"]):
    track_count = p["tracks"]["total"]
    print(f"  {i+1:2d}. {p['name']} ({track_count} tracks) — uri={p['uri']}")

# 4. Current playback
print("\n=== Current Playback ===")
playback = sp.current_playback()
if playback and playback.get("item"):
    track = playback["item"]
    artist = track["artists"][0]["name"] if track["artists"] else "?"
    print(f"  Now playing: {artist} — {track['name']}")
    print(f"  Device: {playback['device']['name']}")
else:
    print("  Nothing playing.")

print("\nSpotify test PASS")
