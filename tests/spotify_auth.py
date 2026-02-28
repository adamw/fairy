#!/usr/bin/env python3
"""One-time Spotify OAuth2 authentication.

Run this on a machine with a browser (your laptop, not the Pi).
It will open a browser window for you to log in and authorize the app,
then save the token to .spotify_cache in the current directory.

Steps before running:
  1. Create an app at https://developer.spotify.com/dashboard
  2. Set redirect URI to http://127.0.0.1:8888/callback
  3. Set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET env vars, or
     edit them below.

After running, copy .spotify_cache to the Pi:
  scp .spotify_cache fairy@fairy.local:~/fairy/.spotify_cache
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

CACHE_PATH = ".spotify_cache"

client_id = os.environ.get("SPOTIPY_CLIENT_ID", "")
client_secret = os.environ.get("SPOTIPY_CLIENT_SECRET", "")
redirect_uri = os.environ.get("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

if not client_id or not client_secret:
    print("Set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables.")
    print("Example:")
    print("  export SPOTIPY_CLIENT_ID='your_client_id'")
    print("  export SPOTIPY_CLIENT_SECRET='your_client_secret'")
    raise SystemExit(1)

auth_manager = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=SCOPES,
    cache_path=CACHE_PATH,
)

sp = spotipy.Spotify(auth_manager=auth_manager)
user = sp.current_user()
print(f"Authenticated as: {user['display_name']} ({user['id']})")
print(f"Token cached to: {CACHE_PATH}")
print(f"\nCopy to Pi:  scp {CACHE_PATH} fairy@fairy.local:~/fairy/{CACHE_PATH}")
