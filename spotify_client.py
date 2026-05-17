"""Spotify Web API client wrapper."""

import logging
import time

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import config

log = logging.getLogger("fairy.spotify")

# Force-refresh token every 45 minutes regardless of local clock.
# Spotipy's auto-refresh relies on comparing expires_at to time.time(),
# which fails silently when the system clock is wrong (no RTC on Pi Zero).
TOKEN_REFRESH_INTERVAL_S = 45 * 60
_last_token_refresh = 0


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


def refresh_token_if_needed(sp):
    """Force-refresh the token periodically, independent of the system clock.

    This protects against clock skew on the Pi Zero (no hardware RTC),
    where spotipy's built-in refresh thinks the token is still valid
    but Spotify's servers reject it as expired.

    Tolerates transient network failures: logs and backs off for a minute
    instead of crashing the service.
    """
    global _last_token_refresh
    now = time.monotonic()
    if now - _last_token_refresh < TOKEN_REFRESH_INTERVAL_S:
        return
    try:
        _force_token_refresh(sp)
    except Exception as e:
        log.warning("Token refresh failed, will retry in ~1min: %s", e)
        _last_token_refresh = now - TOKEN_REFRESH_INTERVAL_S + 60


def _force_token_refresh(sp):
    """Unconditionally refresh the Spotify access token."""
    global _last_token_refresh
    auth = sp.auth_manager
    token_info = auth.cache_handler.get_cached_token()
    if token_info and "refresh_token" in token_info:
        log.info("Forcing token refresh")
        auth.refresh_access_token(token_info["refresh_token"])
        _last_token_refresh = time.monotonic()


def _do_play(sp, uri):
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
    sp.repeat("off", device_id=config.SPOTIFY_DEVICE_ID)


def play(sp, uri):
    """Start playback on the configured device.

    Handles playlists, albums, and individual tracks.
    Sets repeat to off so playback stops after the last track.
    Retries once with a forced token refresh on 401.
    """
    log.debug("Starting playback: %s on device %s", uri, config.SPOTIFY_DEVICE_ID)
    try:
        _do_play(sp, uri)
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 401:
            log.warning("Got 401, forcing token refresh and retrying")
            _force_token_refresh(sp)
            _do_play(sp, uri)
        else:
            raise
