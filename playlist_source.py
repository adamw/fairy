"""Fetch playlist URIs from a GitHub Gist and cache locally."""

import logging
import os
import urllib.parse
import urllib.request

import config

log = logging.getLogger("fairy.playlist_source")

CACHE_FILE = os.path.join(config.CACHE_DIR, "playlists.txt")


def _is_valid_uri(uri):
    parts = uri.split(":")
    return len(parts) == 3 and parts[0] == "spotify"


def _normalize_uri(value):
    """Convert a Spotify share URL or URI to a canonical spotify:type:id URI.

    Accepts:
        spotify:album:xxx
        https://open.spotify.com/album/xxx?si=...
    Returns the spotify:type:id form, or the input unchanged if not a URL.
    """
    if value.startswith("https://open.spotify.com/"):
        parsed = urllib.parse.urlparse(value)
        # path like /album/xxx or /track/xxx
        parts = parsed.path.strip("/").split("/")
        if len(parts) == 2:
            return f"spotify:{parts[0]}:{parts[1]}"
        log.warning("Cannot parse Spotify URL path: %s", parsed.path)
    return value


def _strip_comment(line):
    """Strip inline '# ...' comments and surrounding whitespace."""
    idx = line.find("#")
    return line[:idx].strip() if idx >= 0 else line.strip()


def fetch_uris(url):
    """Download gist and parse one URI per line (skip blank/comment/invalid lines)."""
    log.info("Fetching playlist URIs from %s", url)
    data = urllib.request.urlopen(url, timeout=15).read().decode("utf-8")
    uris = []
    for line in data.splitlines():
        line = _strip_comment(line)
        if not line:
            continue
        uri = _normalize_uri(line)
        if not _is_valid_uri(uri):
            log.warning("Skipping invalid URI: %s", line)
            continue
        uris.append(uri)
    log.info("Fetched %d URIs", len(uris))
    return uris


def _save_cache(uris):
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        f.write("\n".join(uris) + "\n")
    log.debug("Saved %d URIs to %s", len(uris), CACHE_FILE)


def _load_cache():
    with open(CACHE_FILE, "r") as f:
        uris = [
            u for l in f
            if (s := _strip_comment(l))
            and _is_valid_uri(u := _normalize_uri(s))
        ]
    log.info("Loaded %d URIs from cache %s", len(uris), CACHE_FILE)
    return uris


def load_uris(url):
    """Fetch URIs from gist; on failure fall back to local cache."""
    try:
        uris = fetch_uris(url)
        _save_cache(uris)
        return uris
    except Exception as e:
        log.warning("Failed to fetch gist: %s — trying local cache", e)
        try:
            return _load_cache()
        except Exception:
            raise RuntimeError(
                f"Cannot load playlist URIs: gist fetch failed ({e}) "
                f"and no local cache at {CACHE_FILE}"
            )
