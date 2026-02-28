"""Fetch and cache playlist metadata and cover images from Spotify."""

import json
import os
import urllib.request

from PIL import Image
from io import BytesIO

import config

METADATA_FILE = os.path.join(config.CACHE_DIR, "metadata.json")
IMG_WIDTH = 320
IMG_HEIGHT = 240


def _playlist_id(uri):
    """Extract playlist ID from a Spotify URI."""
    return uri.split(":")[-1]


def _image_path(playlist_id):
    return os.path.join(config.CACHE_DIR, f"{playlist_id}.png")


def _load_cached_metadata():
    """Load cached metadata if it exists."""
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r") as f:
            return json.load(f)
    return {}


def _save_metadata(metadata):
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2)


def _download_image(url, dest_path):
    """Download an image, resize to display dimensions, save as PNG."""
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    data = urllib.request.urlopen(url, timeout=15).read()
    img = Image.open(BytesIO(data))
    img = img.resize((IMG_WIDTH, IMG_HEIGHT), Image.LANCZOS)
    img.save(dest_path, "PNG")


def load_playlists(sp):
    """Load playlist metadata, fetching from API and caching as needed.

    Args:
        sp: authenticated spotipy.Spotify instance

    Returns:
        list of dicts: [{"uri", "id", "name", "image_path"}, ...]
    """
    cached = _load_cached_metadata()
    playlists = []
    updated = False

    for uri in config.PLAYLISTS:
        pid = _playlist_id(uri)
        img_path = _image_path(pid)

        if pid in cached and os.path.exists(img_path):
            playlists.append({
                "uri": uri,
                "id": pid,
                "name": cached[pid]["name"],
                "image_path": img_path,
            })
            continue

        # Fetch from API
        try:
            data = sp.playlist(pid, fields="name,images")
            name = data["name"]
            images = data.get("images", [])
            image_url = images[0]["url"] if images else None

            if image_url:
                _download_image(image_url, img_path)

            cached[pid] = {"name": name, "image_url": image_url or ""}
            updated = True

            playlists.append({
                "uri": uri,
                "id": pid,
                "name": name,
                "image_path": img_path if image_url else None,
            })
        except Exception as e:
            print(f"Warning: failed to fetch playlist {uri}: {e}")
            # Use whatever we have cached, or skip
            if pid in cached:
                playlists.append({
                    "uri": uri,
                    "id": pid,
                    "name": cached[pid]["name"],
                    "image_path": img_path if os.path.exists(img_path) else None,
                })

    if updated:
        _save_metadata(cached)

    return playlists
