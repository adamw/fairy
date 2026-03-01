"""Display driver for the Pimoroni Display HAT Mini."""

from displayhatmini import DisplayHATMini
from PIL import Image, ImageDraw, ImageFont

WIDTH = DisplayHATMini.WIDTH   # 320
HEIGHT = DisplayHATMini.HEIGHT  # 240

# Reserve space at bottom for playlist name
TEXT_AREA_HEIGHT = 40
IMAGE_HEIGHT = HEIGHT - TEXT_AREA_HEIGHT

try:
    _font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22
    )
except OSError:
    _font = ImageFont.load_default()


class Display:
    def __init__(self):
        self._buffer = Image.new("RGB", (WIDTH, HEIGHT))
        self._draw = ImageDraw.Draw(self._buffer)
        self._display = DisplayHATMini(self._buffer, backlight_pwm=True)
        self._backlight_on = False

    def set_backlight(self, on):
        self._backlight_on = on
        self._display.set_backlight(1.0 if on else 0.0)

    @property
    def backlight_on(self):
        return self._backlight_on

    def show_playlist(self, image_path, name, is_playing=False):
        """Show a playlist cover image with name below."""
        self._draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(0, 0, 0))

        # Draw cover image
        if image_path:
            try:
                img = Image.open(image_path)
                img = img.resize((WIDTH, IMAGE_HEIGHT), Image.LANCZOS)
                self._buffer.paste(img, (0, 0))
            except Exception:
                self._draw.rectangle(
                    (0, 0, WIDTH, IMAGE_HEIGHT), fill=(40, 40, 40)
                )

        # Draw name bar
        if is_playing:
            bar_color = (0, 100, 0)
            text_color = (255, 255, 255)
        else:
            bar_color = (0, 0, 0)
            text_color = (180, 180, 180)

        self._draw.rectangle(
            (0, IMAGE_HEIGHT, WIDTH, HEIGHT), fill=bar_color
        )

        # Draw playlist name
        self._draw.text(
            (8, IMAGE_HEIGHT + TEXT_AREA_HEIGHT // 2),
            name,
            font=_font, fill=text_color, anchor="lm"
        )

        self._display.display()

    def set_led(self, r, g, b):
        self._display.set_led(r, g, b)

    @property
    def hat(self):
        """Access the underlying DisplayHATMini for button callbacks."""
        return self._display
