import math
import time

import numpy as np
from PIL import Image, ImageTk


class ReactiveOrb:
    """A small procedural liquid orb rendered directly into a Tk canvas."""

    def __init__(self, canvas, size=112, fps=45):
        self.canvas = canvas
        self.size = size
        self.frame_ms = round(1000 / fps)
        self.target_level = 0.0
        self.level = 0.0
        self.phase = 0.0
        self.mode = "listening"
        self.running = False
        self._after_id = None
        self._last_time = time.perf_counter()
        self._photo = None

        axis = np.linspace(-1.08, 1.08, size, dtype=np.float32)
        self.x, self.y = np.meshgrid(axis, axis)
        self.radius = np.sqrt(self.x * self.x + self.y * self.y)
        # A soft one-pixel antialiased boundary around the sphere.
        self.alpha = np.clip((1.0 - self.radius) * size * 0.9, 0.0, 1.0)
        self.image_item = canvas.create_image(size // 2, size // 2, anchor="center")
        self._render_frame()

    def set_volume(self, rms):
        # Suppress room noise, then use a soft logarithmic curve so ordinary
        # speech remains lively without violent jumps on loud sounds.
        normalized = max(0.0, (float(rms) - 65.0) / 2400.0)
        self.target_level = min(1.0, math.sqrt(normalized))

    def set_mode(self, mode):
        self.mode = mode
        if mode == "processing":
            self.target_level = 0.32

    def start(self):
        if self.running:
            return
        self.running = True
        self._last_time = time.perf_counter()
        self._animate()

    def stop(self):
        self.running = False
        self.target_level = 0.0
        if self._after_id:
            try:
                self.canvas.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _animate(self):
        if not self.running:
            return
        now = time.perf_counter()
        dt = min(now - self._last_time, 0.08)
        self._last_time = now

        smoothing = 1.0 - math.exp(-dt * (20.0 if self.target_level > self.level else 7.5))
        self.level += (self.target_level - self.level) * smoothing
        speed = 1.2 if self.mode == "processing" else 0.42 + self.level * 3.4
        self.phase = (self.phase + dt * speed) % (math.pi * 20)
        self._render_frame()
        self._after_id = self.canvas.after(self.frame_ms, self._animate)

    def _render_frame(self):
        x, y, phase, level = self.x, self.y, self.phase, self.level
        energy = 0.08 + level * 0.92

        # Several slowly moving fields create the impression of one viscous
        # substance folding through another rather than a repeating waveform.
        displacement = 0.055 + 0.22 * level
        warp_x = x + displacement * np.sin(2.4 * y - phase * 1.55)
        warp_y = y + displacement * 1.15 * np.sin(2.0 * x + phase * 1.2)
        voice_push = level * 0.30 * math.sin(phase * 2.35)
        fold = np.sin(2.7 * warp_x - 1.9 * warp_y + phase * (1.35 + level))
        fold += (0.48 + 0.30 * level) * np.sin(3.6 * warp_y + 1.3 * warp_x - phase * 1.1)
        fold = (np.tanh(fold * 1.15) + 1.0) * 0.5

        tide = warp_x + 0.42 * warp_y - 0.28 + 0.16 * fold + voice_push
        tide += 0.13 * math.sin(phase * 0.74)
        cyan = (np.tanh(tide * 2.7) + 1.0) * 0.5
        cyan *= 0.68 + 0.32 * fold
        blue = np.exp(-((warp_x + 0.22 * math.cos(phase)) ** 2 * 1.45 + (warp_y + 0.02) ** 2 * 1.05))
        violet = np.exp(-((warp_x + 0.30) ** 2 * 2.0 + (warp_y + 0.67 + 0.12 * math.sin(phase * 0.5)) ** 2 * 3.2))

        if self.mode == "processing":
            cyan *= 0.82
            violet *= 1.35

        # Deep navy base with separate violet, electric-blue, and cyan regions.
        blue_mix = np.clip((1.0 - cyan * 0.58) * blue * (0.68 + 0.32 * fold), 0.0, 1.0)
        violet_mix = violet * (1.0 - cyan * 0.72)
        brightness = 0.86 + 0.22 * level
        red = (2 + 4 * cyan + 6 * blue_mix + 58 * violet_mix) * brightness
        green = (4 + 188 * cyan + 34 * blue_mix + 2 * violet_mix) * brightness
        blue_channel = (31 + 172 * cyan + 214 * blue_mix + 132 * violet_mix) * brightness

        # Spherical depth: dark lower rim, cobalt edge light, and restrained
        # glass highlight at the upper-left.
        rim = np.clip((self.radius - 0.79) / 0.21, 0.0, 1.0)
        shade = np.clip(1.04 - 0.48 * rim + 0.08 * (-x - y), 0.48, 1.08)
        edge_blue = np.exp(-((self.radius - 0.91) / 0.055) ** 2)
        highlight = np.exp(-((x + 0.36) ** 2 * 7.0 + (y + 0.48) ** 2 * 10.0))

        red = red * shade + 4 * edge_blue + 13 * highlight
        green = green * shade + 18 * edge_blue + 22 * highlight
        blue_channel = blue_channel * shade + 48 * edge_blue + 38 * highlight

        rgba = np.empty((self.size, self.size, 4), dtype=np.uint8)
        rgba[..., 0] = np.clip(red, 0, 255).astype(np.uint8)
        rgba[..., 1] = np.clip(green, 0, 255).astype(np.uint8)
        rgba[..., 2] = np.clip(blue_channel, 0, 255).astype(np.uint8)
        rgba[..., 3] = (self.alpha * 255).astype(np.uint8)

        self.last_image = Image.fromarray(rgba, "RGBA")
        self._photo = ImageTk.PhotoImage(self.last_image)
        self.canvas.itemconfigure(self.image_item, image=self._photo)
