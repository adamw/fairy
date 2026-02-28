#!/usr/bin/env python3
"""Test script for WiFi / network connectivity."""

import subprocess
import urllib.request
import urllib.error


def check_wifi_interface():
    """Check if connected to a WiFi network."""
    try:
        result = subprocess.run(
            ["iwgetid", "-r"], capture_output=True, text=True, timeout=5
        )
        ssid = result.stdout.strip()
        if ssid:
            print(f"WiFi SSID: {ssid}  — PASS")
            return True
        else:
            print("WiFi: not connected  — FAIL")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"WiFi check error: {e}  — FAIL")
        return False


def check_ping():
    """Ping an external host."""
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "3", "8.8.8.8"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            print("Ping 8.8.8.8: reachable  — PASS")
            return True
        else:
            print("Ping 8.8.8.8: unreachable  — FAIL")
            return False
    except subprocess.TimeoutExpired:
        print("Ping 8.8.8.8: timeout  — FAIL")
        return False


def check_https():
    """Make an HTTPS request."""
    try:
        req = urllib.request.urlopen("https://httpbin.org/status/200", timeout=5)
        code = req.getcode()
        if code == 200:
            print(f"HTTPS request: {code}  — PASS")
            return True
        else:
            print(f"HTTPS request: {code}  — FAIL")
            return False
    except (urllib.error.URLError, OSError) as e:
        print(f"HTTPS request: {e}  — FAIL")
        return False


if __name__ == "__main__":
    print("Network connectivity test\n")
    results = [
        check_wifi_interface(),
        check_ping(),
        check_https(),
    ]
    passed = sum(results)
    total = len(results)
    print(f"\nResult: {passed}/{total} checks passed")
