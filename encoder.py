"""Rotary encoder driver using GPIO (rpi-lgpio).

Breakout Garden header wiring:
    CLK → SDA (GPIO 2)
    DT  → SCL (GPIO 3)
    SW  → INT (GPIO 4)
"""

import logging
import RPi.GPIO as GPIO
import config

log = logging.getLogger("fairy.encoder")


class Encoder:
    """Driver for the Iduino SE055 (EC11-type, 30 detent / 15 pulse) encoder.

    The SE055 is a half-cycle encoder: detent positions alternate between
    (CLK=1, DT=1) and (CLK=0, DT=0).  Each detent produces one edge on CLK
    (alternating falling and rising), so we listen on GPIO.BOTH.

    Bounce is filtered by state tracking: multiple callbacks from the same
    edge all read the same pin state, and only the first one through sees a
    state change.  The GIL serialises callback execution, making this safe.

    If you have a 20-detent/20-pulse (full-cycle) encoder instead, change
    GPIO.BOTH to GPIO.FALLING to avoid double-counting.
    """

    def __init__(self, on_turn=None, on_press=None):
        """
        Args:
            on_turn: callback(direction) where direction is +1 or -1
            on_press: callback() called on button press
        """
        self._on_turn = on_turn
        self._on_press = on_press

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(config.PIN_CLK, GPIO.IN)
        GPIO.setup(config.PIN_DT, GPIO.IN)
        GPIO.setup(config.PIN_SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self._last_clk = GPIO.input(config.PIN_CLK)

        GPIO.add_event_detect(
            config.PIN_CLK, GPIO.BOTH, callback=self._encoder_cb
        )
        GPIO.add_event_detect(
            config.PIN_SW, GPIO.FALLING, callback=self._button_cb,
            bouncetime=300
        )

    def _encoder_cb(self, channel):
        clk = GPIO.input(config.PIN_CLK)
        if clk == self._last_clk:
            return  # bounce — pin state hasn't actually changed
        self._last_clk = clk

        dt = GPIO.input(config.PIN_DT)
        # CW: falling→dt=1, rising→dt=0 (clk≠dt). CCW: the opposite (clk==dt).
        direction = 1 if clk != dt else -1
        log.debug("Encoder: clk=%d dt=%d direction=%d", clk, dt, direction)
        if self._on_turn:
            self._on_turn(direction)

    def _button_cb(self, channel):
        log.debug("Button press detected")
        if self._on_press:
            self._on_press()

    def cleanup(self):
        GPIO.cleanup()
