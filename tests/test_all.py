#!/usr/bin/env python3
"""Combined hardware diagnostic — shows results on the display.

Tests: display, WiFi, encoder rotation, encoder button, HAT buttons.
"""

import subprocess
import time
import urllib.request
import urllib.error

import RPi.GPIO as GPIO
from displayhatmini import DisplayHATMini
from PIL import Image, ImageDraw, ImageFont

# --- Config ---
PIN_CLK = 2
PIN_DT = 3
PIN_SW = 4

# --- Display init ---
width = DisplayHATMini.WIDTH
height = DisplayHATMini.HEIGHT
buffer = Image.new("RGB", (width, height))
draw = ImageDraw.Draw(buffer)
display = DisplayHATMini(buffer, backlight_pwm=True)
display.set_backlight(1.0)

try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
except OSError:
    font = ImageFont.load_default()
    small = font

# --- State ---
results = {
    "Display": "PASS",  # if you see anything, it works
    "WiFi": "...",
    "Encoder": "...",
    "Enc. Btn": "...",
    "HAT Btn": "...",
}
encoder_counter = 0
encoder_last_clk = None
encoder_tested = False
enc_btn_tested = False
hat_btn_tested = False
done = False

GREEN = (0, 200, 0)
RED = (200, 0, 0)
YELLOW = (200, 200, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
BLACK = (0, 0, 0)


def color_for(status):
    if status == "PASS":
        return GREEN
    if status == "FAIL":
        return RED
    return YELLOW


def render():
    draw.rectangle((0, 0, width, height), fill=BLACK)
    draw.text((width // 2, 8), "Hardware Test", font=font, fill=WHITE, anchor="mt")
    y = 45
    for label, status in results.items():
        draw.text((10, y), label, font=small, fill=GRAY)
        draw.text((width - 10, y), status, font=small, fill=color_for(status), anchor="rt")
        y += 28
    if not done:
        draw.text((width // 2, height - 20), "Turn knob / press buttons", font=small, fill=GRAY, anchor="mb")
    else:
        passed = sum(1 for s in results.values() if s == "PASS")
        total = len(results)
        msg = f"{passed}/{total} passed"
        draw.text((width // 2, height - 20), msg, font=font, fill=GREEN if passed == total else YELLOW, anchor="mb")
    display.display()


# --- WiFi test ---
def test_wifi():
    try:
        result = subprocess.run(["iwgetid", "-r"], capture_output=True, text=True, timeout=5)
        if not result.stdout.strip():
            return "FAIL"
        req = urllib.request.urlopen("https://httpbin.org/status/200", timeout=5)
        return "PASS" if req.getcode() == 200 else "FAIL"
    except Exception:
        return "FAIL"


# --- Encoder callbacks ---
def encoder_callback(channel):
    global encoder_counter, encoder_last_clk, encoder_tested
    clk = GPIO.input(PIN_CLK)
    dt = GPIO.input(PIN_DT)
    if clk != encoder_last_clk:
        if dt != clk:
            encoder_counter += 1
        else:
            encoder_counter -= 1
        encoder_last_clk = clk
        if abs(encoder_counter) >= 3:
            encoder_tested = True
            results["Encoder"] = "PASS"


def enc_button_callback(channel):
    global enc_btn_tested
    time.sleep(0.02)
    if GPIO.input(PIN_SW) == 0:
        enc_btn_tested = True
        results["Enc. Btn"] = "PASS"


def hat_button_callback(pin):
    global hat_btn_tested
    if not display.read_button(pin):
        return
    hat_btn_tested = True
    results["HAT Btn"] = "PASS"


# --- Setup GPIO ---
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_CLK, GPIO.IN)
GPIO.setup(PIN_DT, GPIO.IN)
GPIO.setup(PIN_SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)
encoder_last_clk = GPIO.input(PIN_CLK)

GPIO.add_event_detect(PIN_CLK, GPIO.BOTH, callback=encoder_callback)
GPIO.add_event_detect(PIN_SW, GPIO.FALLING, callback=enc_button_callback, bouncetime=200)
display.on_button_pressed(hat_button_callback)

# --- Main ---
print("Running hardware tests. Check the display.")

render()

# WiFi test (blocking, takes a moment)
results["WiFi"] = test_wifi()
render()

# Wait for encoder + button interactions
timeout = 30
start = time.time()
try:
    while time.time() - start < timeout:
        if encoder_tested and enc_btn_tested and hat_btn_tested:
            break
        render()
        time.sleep(1.0 / 10)
except KeyboardInterrupt:
    pass

if not encoder_tested:
    results["Encoder"] = "FAIL"
if not enc_btn_tested:
    results["Enc. Btn"] = "FAIL"
if not hat_btn_tested:
    results["HAT Btn"] = "FAIL"

done = True
render()

passed = sum(1 for s in results.values() if s == "PASS")
total = len(results)
print(f"\nResults: {passed}/{total} passed")
for label, status in results.items():
    print(f"  {label}: {status}")

print("\nPress Ctrl+C to exit.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    display.set_backlight(0)
    GPIO.cleanup()
    print("Done.")
