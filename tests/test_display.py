#!/usr/bin/env python3
"""Test script for Display HAT Mini. Cycles through solid colors then shows text."""

import time
from displayhatmini import DisplayHATMini
from PIL import Image, ImageDraw, ImageFont

width = DisplayHATMini.WIDTH
height = DisplayHATMini.HEIGHT

buffer = Image.new("RGB", (width, height))
draw = ImageDraw.Draw(buffer)
display = DisplayHATMini(buffer, backlight_pwm=True)
display.set_backlight(1.0)

colors = [
    ("Red", (255, 0, 0)),
    ("Green", (0, 255, 0)),
    ("Blue", (0, 0, 255)),
    ("White", (255, 255, 255)),
]

for name, color in colors:
    draw.rectangle((0, 0, width, height), fill=color)
    display.display()
    print(f"Showing {name}")
    time.sleep(1)

# Show text on black background
draw.rectangle((0, 0, width, height), fill=(0, 0, 0))

try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
except OSError:
    font = ImageFont.load_default()

text = "Hello!"
bbox = draw.textbbox((0, 0), text, font=font)
text_w = bbox[2] - bbox[0]
text_h = bbox[3] - bbox[1]
x = (width - text_w) // 2
y = (height - text_h) // 2
draw.text((x, y), text, font=font, fill=(255, 255, 0))
display.display()
print("Showing 'Hello!' text")
print("Display test PASS — press Ctrl+C to exit")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    display.set_backlight(0)
    print("\nDone.")
