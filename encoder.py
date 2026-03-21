"""Rotary encoder driver using GPIO (rpi-lgpio).

Breakout Garden header wiring:
    CLK → SDA (GPIO 2)
    DT  → SCL (GPIO 3)
    SW  → INT (GPIO 4)
"""

import logging
import time
import RPi.GPIO as GPIO
import config

log = logging.getLogger("fairy.encoder")

ENCODER_DEBOUNCE_MS = 30


class Encoder:
    def __init__(self, on_turn=None, on_press=None):
        """
        Args:
            on_turn: callback(direction) where direction is +1 or -1
            on_press: callback() called on button press
        """
        self._on_turn = on_turn
        self._on_press = on_press
        self._last_event_time = 0

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(config.PIN_CLK, GPIO.IN)
        GPIO.setup(config.PIN_DT, GPIO.IN)
        GPIO.setup(config.PIN_SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        GPIO.add_event_detect(
            config.PIN_CLK, GPIO.FALLING, callback=self._encoder_cb
        )
        GPIO.add_event_detect(
            config.PIN_SW, GPIO.FALLING, callback=self._button_cb,
            bouncetime=300
        )

    def _encoder_cb(self, channel):
        clk = GPIO.input(config.PIN_CLK)
        dt = GPIO.input(config.PIN_DT)

        if clk != 0:
            log.debug("Encoder IGNORED (not falling): clk=%d dt=%d", clk, dt)
            return

        now = time.monotonic() * 1000
        elapsed = now - self._last_event_time
        if elapsed < ENCODER_DEBOUNCE_MS:
            log.debug("Encoder FILTERED (bounce): clk=%d dt=%d elapsed=%.1fms", clk, dt, elapsed)
            return
        self._last_event_time = now

        direction = 1 if dt else -1
        log.debug("Encoder ACCEPTED: clk=%d dt=%d elapsed=%.1fms direction=%d", clk, dt, elapsed, direction)
        if self._on_turn:
            self._on_turn(direction)

    def _button_cb(self, channel):
        log.debug("Button press detected")
        if self._on_press:
            self._on_press()

    def cleanup(self):
        GPIO.cleanup()
