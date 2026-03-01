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

DEBOUNCE_MS = 5


class Encoder:
    def __init__(self, on_turn=None, on_press=None):
        """
        Args:
            on_turn: callback(direction) where direction is +1 or -1
            on_press: callback() called on button press
        """
        self._on_turn = on_turn
        self._on_press = on_press
        self._last_clk = None
        self._last_event_time = 0

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(config.PIN_CLK, GPIO.IN)
        GPIO.setup(config.PIN_DT, GPIO.IN)
        GPIO.setup(config.PIN_SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self._last_clk = GPIO.input(config.PIN_CLK)

        GPIO.add_event_detect(
            config.PIN_CLK, GPIO.FALLING, callback=self._encoder_cb
        )
        GPIO.add_event_detect(
            config.PIN_SW, GPIO.FALLING, callback=self._button_cb,
            bouncetime=200
        )

    def _encoder_cb(self, channel):
        now = time.time() * 1000
        if now - self._last_event_time < DEBOUNCE_MS:
            return
        self._last_event_time = now

        clk = GPIO.input(config.PIN_CLK)
        dt = GPIO.input(config.PIN_DT)

        if clk != self._last_clk:
            direction = 1 if dt != clk else -1
            self._last_clk = clk
            if self._on_turn:
                self._on_turn(direction)

    def _button_cb(self, channel):
        time.sleep(0.05)
        if GPIO.input(config.PIN_SW) == 0:
            log.debug("Button press confirmed")
            if self._on_press:
                self._on_press()
        else:
            log.debug("Button press rejected (bounce)")

    def cleanup(self):
        GPIO.cleanup()
