"""Fetch playlist URIs from a GitHub Gist and cache locally.

Supported gist line formats:
    spotify:album:xxx                      - spotify URI
    https://open.spotify.com/album/xxx     - spotify share URL
    mp3|https://server.com/track.mp3|Title - MP3 file on a web server
"""

import logging
import os
import urllib.parse
import urllib.request

import config

log = logging.getLogger("fairy.playlist_source")

CACHE_FILE = os.path.join(config.CACHE_DIR, "playlists.txt")


def _is_valid_spotify_uri(uri):
    parts = uri.split(":")
    return len(parts) == 3 and parts[0] == "spotify"


def _is_valid_mp3_entry(entry):
    parts = entry.split("|", 2)
    if len(parts) != 3 or parts[0] != "mp3":
        return False
    url, title = parts[1], parts[2]
    return url.startswith(("http://", "https://")) and bool(title.strip())


def _is_valid_entry(entry):
    return _is_valid_spotify_uri(entry) or _is_valid_mp3_entry(entry)


def parse_mp3(entry):
    """Return (url, title) from an 'mp3|url|title' entry."""
    _, url, title = entry.split("|", 2)
    return url, title.strip()


def _normalize(value):
    """Convert a Spotify share URL to a canonical spotify:type:id URI.

    Other forms (spotify: URIs, mp3| entries) pass through unchanged.
    """
    if value.startswith("https://open.spotify.com/"):
        parsed = urllib.parse.urlparse(value)
        parts = parsed.path.strip("/").split("/")
        if len(parts) == 2:
            return f"spotify:{parts[0]}:{parts[1]}"
        log.warning("Cannot parse Spotify URL path: %s", parsed.path)
    return value


def _strip_comment(line):
    """Strip inline '# ...' comments and surrounding whitespace."""
    idx = line.find("#")
    return line[:idx].strip() if idx >= 0 else line.strip()


def fetch_entries(url):
    """Download gist and parse one entry per line (skip blank/comment/invalid lines)."""
    log.info("Fetching playlist entries from %s", url)
    data = urllib.request.urlopen(url, timeout=15).read().decode("utf-8")
    entries = []
    for line in data.splitlines():
        line = _strip_comment(line)
        if not line:
            continue
        entry = _normalize(line)
        if not _is_valid_entry(entry):
            log.warning("Skipping invalid entry: %s", line)
            continue
        entries.append(entry)
    log.info("Fetched %d entries", len(entries))
    return entries


def _save_cache(entries):
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        f.write("\n".join(entries) + "\n")
    log.debug("Saved %d entries to %s", len(entries), CACHE_FILE)


def _load_cache():
    with open(CACHE_FILE, "r") as f:
        entries = [
            e for l in f
            if (s := _strip_comment(l))
            and _is_valid_entry(e := _normalize(s))
        ]
    log.info("Loaded %d entries from cache %s", len(entries), CACHE_FILE)
    return entries


def load_entries(url):
    """Fetch entries from gist; on failure fall back to local cache."""
    try:
        entries = fetch_entries(url)
        _save_cache(entries)
        return entries
    except Exception as e:
        log.warning("Failed to fetch gist: %s — trying local cache", e)
        try:
            return _load_cache()
        except Exception:
            raise RuntimeError(
                f"Cannot load playlist entries: gist fetch failed ({e}) "
                f"and no local cache at {CACHE_FILE}"
            )
