"""Fetch and cache playlist/album metadata and cover images from Spotify."""

import json
import logging
import os
import urllib.request

from PIL import Image
from io import BytesIO

import config

log = logging.getLogger("fairy.cache")

METADATA_FILE = os.path.join(config.CACHE_DIR, "metadata.json")
IMG_WIDTH = 320
IMG_HEIGHT = 240


def _parse_uri(uri):
    """Extract type and ID from a Spotify URI.

    e.g. 'spotify:playlist:xxx' → ('playlist', 'xxx')
         'spotify:album:yyy'    → ('album', 'yyy')
    """
    parts = uri.split(":")
    return parts[1], parts[2]


def _image_path(playlist_id):
    return os.path.join(config.CACHE_DIR, f"{playlist_id}.png")


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


def _download_image(url, dest_path):
    """Download an image, resize to display dimensions, save as PNG."""
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    log.debug("Downloading %s", url)
    data = urllib.request.urlopen(url, timeout=15).read()
    log.debug("Downloaded %d bytes, resizing to %dx%d", len(data), IMG_WIDTH, IMG_HEIGHT)
    img = Image.open(BytesIO(data))
    img = img.resize((IMG_WIDTH, IMG_HEIGHT), Image.LANCZOS)
    img.save(dest_path, "PNG")
    log.debug("Saved image to %s", dest_path)


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


def load_playlists(sp):
    """Load playlist/album metadata, fetching from API and caching as needed.

    Args:
        sp: authenticated spotipy.Spotify instance

    Returns:
        list of dicts: [{"uri", "id", "name", "image_path"}, ...]
    """
    cached = _load_cached_metadata()
    playlists = []
    updated = False

    for uri in config.PLAYLISTS:
        uri_type, item_id = _parse_uri(uri)
        img_path = _image_path(item_id)

        if item_id in cached and os.path.exists(img_path):
            log.debug("Cache hit for %s: %s (image: %s)", item_id, cached[item_id]["name"], img_path)
            playlists.append({
                "uri": uri,
                "id": item_id,
                "name": cached[item_id]["name"],
                "image_path": img_path,
            })
            continue

        # Fetch from API
        try:
            log.info("Fetching from API: %s %s", uri_type, item_id)
            name, image_url = _fetch_metadata(sp, uri_type, item_id)
            log.debug("Got metadata: name=%s, image_url=%s", name, image_url)

            if image_url:
                log.info("Downloading image for: %s", name)
                _download_image(image_url, img_path)

            cached[item_id] = {"name": name, "image_url": image_url or ""}
            updated = True

            playlists.append({
                "uri": uri,
                "id": item_id,
                "name": name,
                "image_path": img_path if image_url else None,
            })
        except Exception as e:
            log.warning("Failed to fetch %s: %s", uri, e)
            if item_id in cached:
                playlists.append({
                    "uri": uri,
                    "id": item_id,
                    "name": cached[item_id]["name"],
                    "image_path": img_path if os.path.exists(img_path) else None,
                })

    if updated:
        log.debug("Saving updated metadata cache")
        _save_metadata(cached)

    log.info("Loaded %d items", len(playlists))
    return playlists
