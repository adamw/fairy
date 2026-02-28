"""Spotify Web API client wrapper."""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import config


def create_client():
    """Create an authenticated Spotify client."""
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
    return spotipy.Spotify(auth_manager=auth_manager)


def play_playlist(sp, uri):
    """Start playback of a playlist on the configured device.

    Sets repeat to off so playback stops after the last track.
    """
    try:
        sp.start_playback(
            device_id=config.SPOTIFY_DEVICE_ID,
            context_uri=uri,
        )
        sp.repeat("off", device_id=config.SPOTIFY_DEVICE_ID)
    except spotipy.exceptions.SpotifyException as e:
        print(f"Spotify error: {e}")
    except Exception as e:
        print(f"Playback error: {e}")
