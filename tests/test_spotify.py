#!/usr/bin/env python3
"""Test Spotify API access from the Pi.

Verifies: authentication, token refresh, device listing, playlist listing.
Run on the Pi after copying .spotify_cache from your desktop.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import config

if not config.SPOTIFY_CLIENT_ID or not config.SPOTIFY_CLIENT_SECRET:
    print("Fill in SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in config.py first.")
    raise SystemExit(1)

auth_manager = SpotifyOAuth(
    client_id=config.SPOTIFY_CLIENT_ID,
    client_secret=config.SPOTIFY_CLIENT_SECRET,
    redirect_uri=config.SPOTIFY_REDIRECT_URI,
    scope=" ".join([
        "user-read-playback-state",
        "user-modify-playback-state",
        "playlist-read-private",
        "playlist-read-collaborative",
    ]),
    cache_path=config.SPOTIFY_CACHE_PATH,
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
    tracks = p.get("tracks", {})
    track_count = tracks.get("total", "?")
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
