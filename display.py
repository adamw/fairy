"""Display driver for the Pimoroni Display HAT Mini."""

import logging

from displayhatmini import DisplayHATMini
from PIL import Image, ImageDraw, ImageFont, ImageOps

log = logging.getLogger("fairy.display")

WIDTH = DisplayHATMini.WIDTH   # 320
HEIGHT = DisplayHATMini.HEIGHT  # 240

# Reserve space at bottom for playlist name
TEXT_AREA_HEIGHT = 40
IMAGE_HEIGHT = HEIGHT - TEXT_AREA_HEIGHT

try:
    _font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22
    )
    _font_small = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16
    )
    _font_large = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32
    )
except OSError:
    _font = ImageFont.load_default()
    _font_small = _font
    _font_large = _font


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
        """Show a playlist cover image with name below, or a text-only view
        if image_path is None (e.g. MP3 entries)."""
        self._draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(0, 0, 0))

        if image_path is None:
            self._draw_text_only(name, is_playing)
            self._display.display()
            return

        try:
            img = Image.open(image_path)
            if img.size != (WIDTH, IMAGE_HEIGHT):
                img = ImageOps.fit(img, (WIDTH, IMAGE_HEIGHT), Image.LANCZOS)
            self._buffer.paste(img, (0, 0))
        except Exception:
            log.warning("Failed to load image: %s", image_path)
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

        # Draw playlist name — single line at 22px, or two lines at 16px
        max_width = WIDTH - 16  # 8px padding each side
        if self._draw.textlength(name, font=_font) <= max_width:
            self._draw.text(
                (8, IMAGE_HEIGHT + TEXT_AREA_HEIGHT // 2),
                name,
                font=_font, fill=text_color, anchor="lm"
            )
        else:
            lines = self._wrap_text(name, _font_small, max_width, max_lines=2)
            y = IMAGE_HEIGHT + (TEXT_AREA_HEIGHT - len(lines) * 20) // 2
            for line in lines:
                self._draw.text((8, y), line, font=_font_small, fill=text_color)
                y += 20

        self._display.display()

    def _draw_text_only(self, name, is_playing):
        """Centered title across the whole screen; used when there's no cover image."""
        bg_color = (0, 60, 0) if is_playing else (30, 30, 30)
        text_color = (255, 255, 255) if is_playing else (220, 220, 220)
        self._draw.rectangle((0, 0, WIDTH, HEIGHT), fill=bg_color)

        max_width = WIDTH - 16
        # Try large font on one line; else large on up to 3 lines; else medium on up to 4.
        if self._draw.textlength(name, font=_font_large) <= max_width:
            lines, font, line_h = [name], _font_large, 36
        else:
            lines = self._wrap_text(name, _font_large, max_width, max_lines=3)
            if len(lines) <= 3:
                font, line_h = _font_large, 36
            else:
                lines = self._wrap_text(name, _font, max_width, max_lines=4)
                font, line_h = _font, 26

        total_h = len(lines) * line_h
        y = (HEIGHT - total_h) // 2
        for line in lines:
            self._draw.text(
                (WIDTH // 2, y + line_h // 2),
                line, font=font, fill=text_color, anchor="mm",
            )
            y += line_h

    def _wrap_text(self, text, font, max_width, max_lines=2):
        """Word-wrap text into lines that fit max_width, truncating with ellipsis."""
        words = text.split()
        lines = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            if self._draw.textlength(test, font=font) <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
                if len(lines) == max_lines:
                    break
        if current and len(lines) < max_lines:
            lines.append(current)
        # Truncate last line if needed
        if lines:
            last = lines[-1]
            if self._draw.textlength(last, font=font) > max_width:
                while len(last) > 1 and self._draw.textlength(last + "…", font=font) > max_width:
                    last = last[:-1]
                lines[-1] = last.rstrip() + "…"
        return lines

    def show_error(self, message):
        """Show an error message on a red background."""
        self._draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(100, 0, 0))
        self._draw.text(
            (WIDTH // 2, HEIGHT // 2),
            message,
            font=_font, fill=(255, 255, 255), anchor="mm"
        )
        self._display.display()

    def set_led(self, r, g, b):
        self._display.set_led(r, g, b)

    @property
    def hat(self):
        """Access the underlying DisplayHATMini for button callbacks."""
        return self._display
