#!/usr/bin/env python3
"""Fairy tale playlist picker — main entry point."""

import logging
import queue
import random
import time

import config
import cache
import playlist_source
import spotify_client
from encoder import Encoder
from display import Display

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("fairy")


class App:
    def __init__(self):
        log.info("Initializing...")
        log.debug("Creating Spotify client")
        self.sp = spotify_client.create_client()
        log.debug("Spotify client ready")

        log.debug("Initializing display")
        self.display = Display()
        log.debug("Display ready")

        self._current_uris = playlist_source.load_uris(config.GIST_RAW_URL)
        log.debug("Loading playlists (%d URIs)", len(self._current_uris))
        self.playlists = cache.load_playlists(self.sp, self._current_uris)
        self._last_gist_fetch = time.time()

        if not self.playlists:
            raise RuntimeError("No playlists loaded. Check your gist.")

        self.selected_index = None
        self.playing_index = None
        self.asleep = True
        self._last_interaction = 0
        self._last_turn = 0
        self._events = queue.Queue()

        # Start with screen off
        self.display.set_backlight(False)

        log.debug("Initializing encoder (CLK=%d, DT=%d, SW=%d)",
                   config.PIN_CLK, config.PIN_DT, config.PIN_SW)
        self.encoder = Encoder(
            on_turn=lambda d: self._events.put(("turn", d)),
            on_press=lambda: self._events.put(("press",)),
        )
        log.debug("Encoder ready")

    def _ensure_selection(self):
        """Pick a random playlist if none selected yet."""
        if self.selected_index is None:
            self.selected_index = random.randint(0, len(self.playlists) - 1)
            log.info("Random selection: %s", self.playlists[self.selected_index]["name"])

    def _wake(self):
        """Wake from sleep."""
        log.info("Waking up")
        self.asleep = False
        self.playing_index = None
        self._reset_timer()

    def _reset_timer(self):
        self._last_interaction = time.time()

    def _refresh_display(self):
        """Show the currently selected playlist."""
        p = self.playlists[self.selected_index]
        is_playing = self.selected_index == self.playing_index
        self.display.show_playlist(p["image_path"], p["name"], is_playing)

    def _handle_turn(self, direction):
        if self.asleep:
            self._wake()
            self._ensure_selection()
            self._refresh_display()
            self.display.set_backlight(True)
            return
        self.selected_index = (
            (self.selected_index + direction) % len(self.playlists)
        )
        self._reset_timer()
        p = self.playlists[self.selected_index]
        log.info("Selected: %s", p["name"])
        self._refresh_display()

    def _handle_press(self):
        if self.asleep:
            self._wake()
            self._ensure_selection()
            self._refresh_display()
            self.display.set_backlight(True)
            return
        self._reset_timer()

        p = self.playlists[self.selected_index]
        log.info("Playing: %s (%s)", p["name"], p["uri"])
        self.playing_index = self.selected_index
        self._refresh_display()
        try:
            spotify_client.play(self.sp, p["uri"])
        except Exception as e:
            log.error("Playback failed: %s", e)
            self.playing_index = None
            self.display.show_error("Playback failed")

    def _process_events(self):
        net_turn = 0
        pressed = False
        while True:
            try:
                event = self._events.get_nowait()
            except queue.Empty:
                break
            if event[0] == "turn":
                net_turn += event[1]
            elif event[0] == "press":
                pressed = True
        was_asleep = self.asleep
        now = time.time()
        did_turn = False
        if net_turn != 0:
            if now - self._last_turn >= 0.2:
                self._last_turn = now
                self._handle_turn(1 if net_turn > 0 else -1)
                did_turn = True
            else:
                log.debug("Turn debounced (net=%+d)", net_turn)
        if pressed and not did_turn and not was_asleep:
            self._handle_press()

    def _check_idle(self):
        if not self.asleep and self._last_interaction > 0:
            elapsed = time.time() - self._last_interaction
            if elapsed >= config.IDLE_TIMEOUT_S:
                log.info("Idle timeout, going to sleep")
                self.asleep = True
                self.display.set_backlight(False)

    def _check_gist_refresh(self):
        if time.time() - self._last_gist_fetch < config.GIST_REFRESH_S:
            return
        self._last_gist_fetch = time.time()
        try:
            new_uris = playlist_source.load_uris(config.GIST_RAW_URL)
        except Exception as e:
            log.warning("Gist refresh failed: %s", e)
            return
        if new_uris == self._current_uris:
            log.debug("Gist unchanged")
            return
        log.info("Gist changed, reloading playlists")
        playing_uri = (
            self.playlists[self.playing_index]["uri"]
            if self.playing_index is not None
            else None
        )
        self._current_uris = new_uris
        self.playlists = cache.load_playlists(self.sp, new_uris)
        # preserve playing_index if the playing URI is still present
        self.playing_index = None
        if playing_uri:
            for i, p in enumerate(self.playlists):
                if p["uri"] == playing_uri:
                    self.playing_index = i
                    break
        # pick a new selection and refresh display if awake
        self.selected_index = self.playing_index
        self._ensure_selection()
        if not self.asleep:
            self._refresh_display()

    def run(self):
        log.info("Ready. %d items loaded. Waiting for input...", len(self.playlists))
        try:
            while True:
                self._process_events()
                self._check_idle()
                self._check_gist_refresh()
                spotify_client.refresh_token_if_needed(self.sp)
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            self.display.set_backlight(False)
            self.encoder.cleanup()
            log.info("Stopped.")


if __name__ == "__main__":
    import sys
    if "--debug" in sys.argv:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("PIL").setLevel(logging.WARNING)
    app = App()
    app.run()
