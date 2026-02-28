#!/usr/bin/env python3
"""Test script for Display HAT Mini buttons. Prints button presses to console."""

import time
from displayhatmini import DisplayHATMini
from PIL import Image, ImageDraw, ImageFont

width = DisplayHATMini.WIDTH
height = DisplayHATMini.HEIGHT

buffer = Image.new("RGB", (width, height))
draw = ImageDraw.Draw(buffer)
display = DisplayHATMini(buffer, backlight_pwm=True)
display.set_backlight(1.0)

try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
except OSError:
    font = ImageFont.load_default()
    small_font = font

BUTTON_NAMES = {
    DisplayHATMini.BUTTON_A: "A",
    DisplayHATMini.BUTTON_B: "B",
    DisplayHATMini.BUTTON_X: "X",
    DisplayHATMini.BUTTON_Y: "Y",
}

last_pressed = "---"


def button_callback(pin):
    global last_pressed
    if not display.read_button(pin):
        return
    name = BUTTON_NAMES.get(pin, str(pin))
    last_pressed = name
    print(f"Button {name} pressed")


display.on_button_pressed(button_callback)

print("Press HAT buttons A, B, X, Y. Ctrl+C to exit.")

try:
    while True:
        draw.rectangle((0, 0, width, height), fill=(0, 0, 0))
        draw.text((width // 2, 40), "Button Test", font=font, fill=(255, 255, 255), anchor="mt")
        draw.text((width // 2, 100), f"Last: {last_pressed}", font=font, fill=(0, 255, 0), anchor="mt")
        draw.text((width // 2, 200), "Press A, B, X or Y", font=small_font, fill=(128, 128, 128), anchor="mt")
        display.display()
        time.sleep(1.0 / 15)
except KeyboardInterrupt:
    display.set_backlight(0)
    print("\nDone.")
