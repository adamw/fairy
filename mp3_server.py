"""Local HTTP server for cached MP3 files.

Downloads remote MP3s to disk and serves them to the Chromecast over LAN,
avoiding issues with expiring signed URLs (e.g. Dropbox).
Supports Range requests for seeking and large-file streaming.
"""

import hashlib
import http.server
import logging
import os
import socket
import tempfile
import threading
import urllib.request

import config

log = logging.getLogger("fairy.mp3_server")

PORT = 8080
SERVE_DIR = os.path.join(config.CACHE_DIR, "mp3")

_server = None
_lan_ip = None


def _get_lan_ip():
    global _lan_ip
    if _lan_ip is None:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            _lan_ip = s.getsockname()[0]
    return _lan_ip


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        self._serve(head_only=True)

    def do_GET(self):
        self._serve(head_only=False)

    def _serve(self, head_only):
        name = self.path.lstrip("/")
        if "/" in name or ".." in name:
            self.send_error(403)
            return
        path = os.path.join(SERVE_DIR, name)
        if not os.path.isfile(path):
            self.send_error(404)
            return

        size = os.path.getsize(path)
        start, end = 0, size - 1
        range_header = self.headers.get("Range")

        if range_header and range_header.startswith("bytes="):
            spec = range_header[6:]
            parts = spec.split("-", 1)
            if parts[0]:
                start = int(parts[0])
            if parts[1]:
                end = int(parts[1])
            end = min(end, size - 1)
            length = end - start + 1
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        else:
            length = size
            self.send_response(200)

        self.send_header("Content-Type", "audio/mpeg")
        self.send_header("Content-Length", length)
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()

        if head_only:
            return

        with open(path, "rb") as f:
            f.seek(start)
            remaining = length
            while remaining > 0:
                chunk = f.read(min(remaining, 65536))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)

    def log_message(self, fmt, *args):
        log.debug(fmt, *args)


def start():
    """Start the file server in a daemon thread. Idempotent."""
    global _server
    if _server is not None:
        return
    os.makedirs(SERVE_DIR, exist_ok=True)
    _server = http.server.HTTPServer(("0.0.0.0", PORT), _Handler)
    threading.Thread(target=_server.serve_forever, daemon=True).start()
    log.info("MP3 server listening on port %d", PORT)


def ensure_cached(url):
    """Download url to local cache if not already present. Return local HTTP URL."""
    os.makedirs(SERVE_DIR, exist_ok=True)
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
    filename = f"{url_hash}.mp3"
    filepath = os.path.join(SERVE_DIR, filename)

    if not os.path.exists(filepath):
        log.info("Downloading %s", url)
        fd, tmp = tempfile.mkstemp(dir=SERVE_DIR, suffix=".tmp")
        os.close(fd)
        try:
            urllib.request.urlretrieve(url, tmp)
            os.rename(tmp, filepath)
        except BaseException:
            os.unlink(tmp)
            raise
        log.info("Cached %s (%d MB)", filename, os.path.getsize(filepath) // (1024 * 1024))
    else:
        log.debug("Already cached: %s", filename)

    return f"http://{_get_lan_ip()}:{PORT}/{filename}"
