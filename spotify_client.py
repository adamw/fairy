"""Spotify Web API client wrapper."""

import logging

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import config

log = logging.getLogger("fairy.spotify")


def create_client():
    """Create an authenticated Spotify client."""
    log.debug("Authenticating with client_id=%s...", config.SPOTIFY_CLIENT_ID[:8])
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
    client = spotipy.Spotify(auth_manager=auth_manager)
    log.debug("Spotify client authenticated")
    return client


def play(sp, uri):
    """Start playback on the configured device.

    Handles playlists, albums, and individual tracks.
    Sets repeat to off so playback stops after the last track.
    """
    try:
        log.debug("Starting playback: %s on device %s", uri, config.SPOTIFY_DEVICE_ID)
        if uri.startswith("spotify:track:"):
            sp.start_playback(
                device_id=config.SPOTIFY_DEVICE_ID,
                uris=[uri],
            )
        else:
            sp.start_playback(
                device_id=config.SPOTIFY_DEVICE_ID,
                context_uri=uri,
            )
        log.debug("Setting repeat off")
        sp.repeat("off", device_id=config.SPOTIFY_DEVICE_ID)
    except spotipy.exceptions.SpotifyException as e:
        log.error("Spotify error: %s", e)
    except Exception as e:
        log.error("Playback error: %s", e)
