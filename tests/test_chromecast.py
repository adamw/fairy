#!/usr/bin/env python3
"""Discover Chromecast-built-in devices on the LAN.

Lists friendly names so you can fill in CHROMECAST_NAME in config.py.
If an MP3 URL is passed as argv[1], attempts to play it on the configured
Chromecast as a round-trip test.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time
import pychromecast
import config

known_hosts = [config.CHROMECAST_HOST] if getattr(config, "CHROMECAST_HOST", "") else None

print("=== Chromecast discovery ===")
if known_hosts:
    print(f"  Using known host: {known_hosts[0]}")
casts, browser = pychromecast.get_chromecasts(timeout=10, known_hosts=known_hosts)

if not casts:
    print("  No Chromecast devices found on the LAN.")
    browser.stop_discovery()
    raise SystemExit(1)

for c in casts:
    print(f"  {c.cast_info.friendly_name}  ({c.cast_info.model_name})")

if len(sys.argv) < 2:
    browser.stop_discovery()
    print("\nPass an MP3 URL as the first argument to test playback.")
    raise SystemExit(0)

url = sys.argv[1]
if not config.CHROMECAST_NAME:
    print("\nSet CHROMECAST_NAME in config.py first.")
    browser.stop_discovery()
    raise SystemExit(1)

match = next(
    (c for c in casts if c.cast_info.friendly_name == config.CHROMECAST_NAME),
    None,
)
if match is None:
    print(f"\n'{config.CHROMECAST_NAME}' not among discovered devices.")
    browser.stop_discovery()
    raise SystemExit(1)

print(f"\n=== Playing on {match.cast_info.friendly_name} ===")
print(f"  URL: {url}")
match.wait(timeout=10)
mc = match.media_controller
mc.play_media(url, "audio/mpeg", title="test")
mc.block_until_active(timeout=10)
print("  Status:", mc.status.player_state)
time.sleep(5)
print("  Status after 5s:", mc.status.player_state)

browser.stop_discovery()
print("\nChromecast test PASS")
