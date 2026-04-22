"""Fetch and cache playlist/album metadata and cover images.

Spotify entries: metadata and cover come from the Web API.
MP3 entries: title comes from the gist line; cover is extracted from the
file's ID3 tag via a partial HTTP read (no full download).
"""

import hashlib
import json
import logging
import os
import urllib.request

from PIL import Image, ImageOps
from io import BytesIO

import config
import playlist_source

log = logging.getLogger("fairy.cache")

METADATA_FILE = os.path.join(config.CACHE_DIR, "metadata.json")
IMG_WIDTH = 320
IMG_HEIGHT = 200  # display height minus text area

# Hard cap on how much of an MP3 we'll read just to extract the cover art.
MP3_COVER_MAX_BYTES = 4 * 1024 * 1024


def _parse_spotify_uri(uri):
    """Extract type and ID from a Spotify URI.

    e.g. 'spotify:playlist:xxx' → ('playlist', 'xxx')
         'spotify:album:yyy'    → ('album', 'yyy')
    """
    parts = uri.split(":")
    return parts[1], parts[2]


def _mp3_id(url):
    """Short, filesystem-safe cache key for an MP3 URL."""
    return "mp3_" + hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def _image_path(item_id):
    return os.path.join(config.CACHE_DIR, f"{item_id}.png")


def _load_cached_metadata():
    """Load cached metadata if it exists."""
    if os.path.exists(METADATA_FILE):
        log.debug("Loading metadata cache from %s", METADATA_FILE)
        with open(METADATA_FILE, "r") as f:
            data = json.load(f)
        log.debug("Metadata cache has %d entries", len(data))
        return data
    log.debug("No metadata cache found at %s", METADATA_FILE)
    return {}


def _save_metadata(metadata):
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2)


def _save_image(data, dest_path):
    """Resize image bytes to display dimensions and save as PNG."""
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    img = Image.open(BytesIO(data))
    img = ImageOps.fit(img, (IMG_WIDTH, IMG_HEIGHT), Image.LANCZOS)
    img.save(dest_path, "PNG")
    log.debug("Saved image to %s", dest_path)


def _download_image(url, dest_path):
    """Download an image from a URL and save it resized as PNG."""
    log.debug("Downloading %s", url)
    data = urllib.request.urlopen(url, timeout=15).read()
    log.debug("Downloaded %d bytes", len(data))
    _save_image(data, dest_path)


def _fetch_mp3_cover(url):
    """Fetch only the ID3v2 tag from an MP3 URL and return the embedded cover bytes.

    Returns None if the file has no ID3v2 tag or no embedded cover.
    Reads a single HTTP response incrementally — no Range requests required,
    capped at MP3_COVER_MAX_BYTES.
    """
    log.debug("Reading ID3 tag from %s", url)
    with urllib.request.urlopen(url, timeout=15) as resp:
        head = resp.read(10)
        if len(head) < 10 or head[:3] != b"ID3":
            log.debug("No ID3v2 tag on %s", url)
            return None
        # Synchsafe 32-bit size: each byte's MSB is 0, 7 effective bits each.
        s = head[6:10]
        tag_size = (s[0] << 21) | (s[1] << 14) | (s[2] << 7) | s[3]
        total = 10 + tag_size
        if total > MP3_COVER_MAX_BYTES:
            log.warning(
                "ID3 tag on %s is %d bytes (> %d cap); skipping cover",
                url, total, MP3_COVER_MAX_BYTES,
            )
            return None
        body = resp.read(tag_size)

    from mutagen.id3 import ID3, ID3NoHeaderError
    try:
        tag = ID3(BytesIO(head + body))
    except ID3NoHeaderError:
        return None
    apics = tag.getall("APIC")
    if not apics:
        log.debug("No APIC frame in ID3 tag of %s", url)
        return None
    # Prefer APIC type 3 (front cover) if present, else first.
    front = next((a for a in apics if getattr(a, "type", None) == 3), apics[0])
    return front.data


def _fetch_metadata(sp, uri_type, item_id):
    """Fetch name and image URL from Spotify API."""
    log.debug("Fetching metadata: type=%s, id=%s", uri_type, item_id)
    if uri_type == "track":
        data = sp.track(item_id)
        name = data["name"]
        # Track images come from the album
        images = data.get("album", {}).get("images", [])
    elif uri_type == "album":
        data = sp.album(item_id)
        name = data["name"]
        images = data.get("images", [])
    else:
        data = sp.playlist(item_id, fields="name,images")
        name = data["name"]
        images = data.get("images", [])
    image_url = images[0]["url"] if images else None
    return name, image_url


def _load_spotify_entry(sp, uri, cached):
    """Return (entry_dict, fetched?) for a spotify URI, fetching/caching as needed."""
    uri_type, item_id = _parse_spotify_uri(uri)
    img_path = _image_path(item_id)

    if item_id in cached and os.path.exists(img_path):
        log.debug("Cache hit for %s: %s", item_id, cached[item_id]["name"])
        return {
            "uri": uri,
            "name": cached[item_id]["name"],
            "image_path": img_path,
        }, False

    try:
        log.info("Fetching from API: %s %s", uri_type, item_id)
        name, image_url = _fetch_metadata(sp, uri_type, item_id)
        log.debug("Got metadata: name=%s, image_url=%s", name, image_url)
        if image_url:
            log.info("Downloading image for: %s", name)
            _download_image(image_url, img_path)
        cached[item_id] = {"name": name, "image_url": image_url or ""}
        return {
            "uri": uri,
            "name": name,
            "image_path": img_path if image_url else None,
        }, True
    except Exception as e:
        log.warning("Failed to fetch %s: %s", uri, e)
        if item_id in cached:
            return {
                "uri": uri,
                "name": cached[item_id]["name"],
                "image_path": img_path if os.path.exists(img_path) else None,
            }, False
        return None, False


def _load_mp3_entry(entry, cached):
    """Return (entry_dict, fetched?) for an mp3 gist line.

    Title comes from the gist line; cover art is extracted from the MP3's
    ID3 tag on first encounter, then cached on disk.
    """
    url, title = playlist_source.parse_mp3(entry)
    item_id = _mp3_id(url)
    img_path = _image_path(item_id)

    cache_entry = cached.get(item_id)
    # URL changes for the same title would invalidate the cached cover.
    if cache_entry and cache_entry.get("image_url") == url:
        image_path = img_path if os.path.exists(img_path) else None
        return {"uri": entry, "name": title, "image_path": image_path}, False

    image_path = None
    try:
        image_bytes = _fetch_mp3_cover(url)
    except Exception as e:
        log.warning("Failed to read cover from %s: %s", url, e)
        image_bytes = None

    if image_bytes:
        try:
            _save_image(image_bytes, img_path)
            image_path = img_path
            log.info("Cached embedded cover for: %s", title)
        except Exception as e:
            log.warning("Failed to save cover for %s: %s", url, e)

    cached[item_id] = {"name": title, "image_url": url if image_path else ""}
    return {"uri": entry, "name": title, "image_path": image_path}, True


def load_playlists(sp, entries):
    """Load metadata for each entry, fetching/caching images as needed.

    Returns a list of dicts: [{"uri", "name", "image_path"}, ...]
    """
    cached = _load_cached_metadata()
    playlists = []
    updated = False

    for entry in entries:
        if entry.startswith("mp3|"):
            result, fetched = _load_mp3_entry(entry, cached)
        else:
            result, fetched = _load_spotify_entry(sp, entry, cached)
        if result:
            playlists.append(result)
        updated = updated or fetched

    # Prune orphaned cache entries.
    active_ids = set()
    for e in entries:
        if e.startswith("mp3|"):
            url, _ = playlist_source.parse_mp3(e)
            active_ids.add(_mp3_id(url))
        else:
            active_ids.add(_parse_spotify_uri(e)[1])
    orphaned = [k for k in cached if k not in active_ids]
    for item_id in orphaned:
        log.info("Removing orphaned cache entry: %s", item_id)
        del cached[item_id]
        updated = True
        img = _image_path(item_id)
        if os.path.exists(img):
            os.remove(img)

    if updated:
        log.debug("Saving updated metadata cache")
        _save_metadata(cached)

    log.info("Loaded %d items", len(playlists))
    return playlists
