#!/usr/bin/env python3
"""Test script for rotary encoder connected to Breakout Garden header.

Wiring:
    CLK → SDA  (GPIO 2)
    DT  → SCL  (GPIO 3)
    SW  → INT  (GPIO 4)
    +   → 3V3
    GND → GND
"""

import time
import RPi.GPIO as GPIO

PIN_CLK = 2
PIN_DT = 3
PIN_SW = 4

counter = 0
last_clk_state = None
last_event_time = 0
DEBOUNCE_MS = 5


def encoder_callback(channel):
    global counter, last_clk_state, last_event_time

    now = time.time() * 1000
    if now - last_event_time < DEBOUNCE_MS:
        return
    last_event_time = now

    clk_state = GPIO.input(PIN_CLK)
    dt_state = GPIO.input(PIN_DT)

    if clk_state != last_clk_state:
        if dt_state != clk_state:
            counter += 1
            print(f"→ CW   counter={counter}")
        else:
            counter -= 1
            print(f"← CCW  counter={counter}")
    last_clk_state = clk_state


def button_callback(channel):
    time.sleep(0.02)  # debounce
    if GPIO.input(PIN_SW) == 0:
        print(f"● PRESSED  counter={counter}")


GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_CLK, GPIO.IN)  # GPIO 2/3 have fixed 1.8kΩ pull-ups
GPIO.setup(PIN_DT, GPIO.IN)
GPIO.setup(PIN_SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # GPIO 4 needs software pull-up

last_clk_state = GPIO.input(PIN_CLK)

GPIO.add_event_detect(PIN_CLK, GPIO.BOTH, callback=encoder_callback)
GPIO.add_event_detect(PIN_SW, GPIO.FALLING, callback=button_callback, bouncetime=200)

print(f"Encoder test — turn the knob and press the button. Ctrl+C to exit.")
print(f"Pins: CLK=GPIO{PIN_CLK}, DT=GPIO{PIN_DT}, SW=GPIO{PIN_SW}")

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nDone.")
finally:
    GPIO.cleanup()
