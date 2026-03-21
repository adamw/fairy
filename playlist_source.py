"""Fetch playlist URIs from a GitHub Gist and cache locally."""

import logging
import os
import urllib.request

import config

log = logging.getLogger("fairy.playlist_source")

CACHE_FILE = os.path.join(config.CACHE_DIR, "playlists.txt")


def _is_valid_uri(uri):
    parts = uri.split(":")
    return len(parts) == 3 and parts[0] == "spotify"


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
        if not _is_valid_uri(line):
            log.warning("Skipping invalid URI: %s", line)
            continue
        uris.append(line)
    log.info("Fetched %d URIs", len(uris))
    return uris


def _save_cache(uris):
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        f.write("\n".join(uris) + "\n")
    log.debug("Saved %d URIs to %s", len(uris), CACHE_FILE)


def _load_cache():
    with open(CACHE_FILE, "r") as f:
        uris = [u for l in f if (u := _strip_comment(l)) and _is_valid_uri(u)]
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
