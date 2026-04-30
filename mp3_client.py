"""Chromecast playback for MP3 files served over HTTP.

The speaker (Bose 500 with Chromecast built-in) fetches the URL directly —
the Pi doesn't proxy the audio.
"""

import logging

import pychromecast

import config
import playlist_source

log = logging.getLogger("fairy.mp3")

DISCOVERY_TIMEOUT_S = 10

_cast = None
_browser = None


def _get_cast():
    """Discover the configured Chromecast (lazy, cached) and return the device."""
    global _cast, _browser
    if _cast is not None and _cast.socket_client.is_connected:
        return _cast

    known_hosts = [config.CHROMECAST_HOST] if config.CHROMECAST_HOST else None
    log.info(
        "Discovering Chromecast: %s%s",
        config.CHROMECAST_NAME,
        f" (known host: {config.CHROMECAST_HOST})" if known_hosts else "",
    )
    casts, browser = pychromecast.get_listed_chromecasts(
        friendly_names=[config.CHROMECAST_NAME],
        discovery_timeout=DISCOVERY_TIMEOUT_S,
        known_hosts=known_hosts,
    )
    if not casts:
        if browser is not None:
            browser.stop_discovery()
        raise RuntimeError(
            f"Chromecast '{config.CHROMECAST_NAME}' not found on the network"
        )
    cast = casts[0]
    cast.wait(timeout=DISCOVERY_TIMEOUT_S)
    log.info("Connected to Chromecast: %s", cast.name)

    # Release any previous browser before replacing it.
    if _browser is not None:
        _browser.stop_discovery()
    _cast = cast
    _browser = browser
    return _cast


def connect():
    """Attempt Chromecast discovery up front. Safe to call if unconfigured;
    failures are logged but not raised — playback will retry lazily."""
    if not config.CHROMECAST_NAME:
        log.info("CHROMECAST_NAME not set; skipping Chromecast discovery")
        return
    try:
        _get_cast()
    except Exception as e:
        log.warning("Chromecast discovery failed at startup: %s", e)


def play(entry):
    """Play an mp3 entry (format: 'mp3|URL|Title') on the Chromecast."""
    url, title = playlist_source.parse_mp3(entry)
    log.debug("Starting MP3 playback: %s (%s)", title, url)
    cast = _get_cast()
    mc = cast.media_controller
    mc.play_media(url, "audio/mpeg", title=title)
    mc.block_until_active(timeout=DISCOVERY_TIMEOUT_S)
