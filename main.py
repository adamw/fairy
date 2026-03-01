#!/usr/bin/env python3
"""Fairy tale playlist picker — main entry point."""

import logging
import random
import time

import config
import cache
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

        log.debug("Loading playlists from config (%d URIs)", len(config.PLAYLISTS))
        self.playlists = cache.load_playlists(self.sp)

        if not self.playlists:
            raise RuntimeError("No playlists configured. Edit config.py.")

        self.selected_index = None
        self.playing_index = None
        self.asleep = True
        self._last_interaction = 0

        # Start with screen off
        self.display.set_backlight(False)

        log.debug("Initializing encoder (CLK=%d, DT=%d, SW=%d)",
                   config.PIN_CLK, config.PIN_DT, config.PIN_SW)
        self.encoder = Encoder(
            on_turn=self._on_turn,
            on_press=self._on_press,
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
        self.display.set_backlight(True)
        self._reset_timer()

    def _reset_timer(self):
        self._last_interaction = time.time()

    def _refresh_display(self):
        """Show the currently selected playlist."""
        p = self.playlists[self.selected_index]
        is_playing = self.selected_index == self.playing_index
        self.display.show_playlist(p["image_path"], p["name"], is_playing)

    def _on_turn(self, direction):
        if self.asleep:
            self._wake()
            self._ensure_selection()
            self._refresh_display()
            return
        self.selected_index = (
            (self.selected_index + direction) % len(self.playlists)
        )
        self._reset_timer()
        p = self.playlists[self.selected_index]
        log.info("Selected: %s", p["name"])
        self._refresh_display()

    def _on_press(self):
        if self.asleep:
            self._wake()
            self._ensure_selection()
            self._refresh_display()
            return
        self._reset_timer()

        p = self.playlists[self.selected_index]
        log.info("Playing: %s (%s)", p["name"], p["uri"])
        spotify_client.play(self.sp, p["uri"])
        self.playing_index = self.selected_index
        self.display.set_led(0, 0.1, 0)  # green = playing
        self._refresh_display()

    def _check_idle(self):
        if not self.asleep and self._last_interaction > 0:
            elapsed = time.time() - self._last_interaction
            if elapsed >= config.IDLE_TIMEOUT_S:
                log.info("Idle timeout, going to sleep")
                self.asleep = True
                self.display.set_backlight(False)
                self.display.set_led(0, 0, 0)

    def run(self):
        log.info("Ready. %d items loaded. Waiting for input...", len(self.playlists))
        try:
            while True:
                self._check_idle()
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            self.display.set_backlight(False)
            self.display.set_led(0, 0, 0)
            self.encoder.cleanup()
            log.info("Stopped.")


if __name__ == "__main__":
    import sys
    if "--debug" in sys.argv:
        logging.getLogger().setLevel(logging.DEBUG)
    app = App()
    app.run()
