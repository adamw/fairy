#!/usr/bin/env python3
"""One-time Spotify OAuth2 authentication.

Run this on a machine with a browser (your laptop, not the Pi).
It will open a browser window for you to log in and authorize the app,
then save the token to .spotify_cache.

Steps before running:
  1. Create an app at https://developer.spotify.com/dashboard
  2. Set redirect URI to http://127.0.0.1:8888/callback
  3. Fill in SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in config.py

After running, copy .spotify_cache to the Pi:
  scp .spotify_cache fairy@fairy.local:~/fairy/.spotify_cache
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
user = sp.current_user()
print(f"Authenticated as: {user['display_name']} ({user['id']})")
print(f"Token cached to: {config.SPOTIFY_CACHE_PATH}")
print(f"\nCopy to Pi:  scp {config.SPOTIFY_CACHE_PATH} fairy@fairy.local:~/fairy/.spotify_cache")
