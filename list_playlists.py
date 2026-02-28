#!/usr/bin/env python3
"""List all Spotify playlists for the current user.

Use this to find playlist URIs to add to config.py.
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import config

auth_manager = SpotifyOAuth(
    client_id=config.SPOTIFY_CLIENT_ID,
    client_secret=config.SPOTIFY_CLIENT_SECRET,
    redirect_uri=config.SPOTIFY_REDIRECT_URI,
    scope="playlist-read-private playlist-read-collaborative",
    cache_path=config.SPOTIFY_CACHE_PATH,
)

sp = spotipy.Spotify(auth_manager=auth_manager)

offset = 0
index = 0
while True:
    results = sp.current_user_playlists(limit=50, offset=offset)
    items = results["items"]
    if not items:
        break
    for p in items:
        index += 1
        tracks = p.get("tracks", {}).get("total", "?")
        print(f"{index:3d}. {p['name']}")
        print(f"     URI: {p['uri']}")
        print(f"     Tracks: {tracks}")
        print()
    offset += 50
    if not results.get("next"):
        break

print(f"Total: {index} playlists")
