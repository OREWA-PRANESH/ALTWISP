from PIL import Image, ImageDraw
import pystray


def _create_icon_image():
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((4, 4, 60, 60), radius=15, fill="#111a2b", outline="#6ee7d2", width=3)
    heights = (12, 24, 38, 50, 38, 24, 12)
    for index, height in enumerate(heights):
        x = 14 + index * 6
        draw.rounded_rectangle((x, 32 - height // 2, x + 3, 32 + height // 2), radius=2, fill="#6ee7d2")
    return image


class TrayIcon:
    def __init__(self, app):
        self.app = app
        self.icon = pystray.Icon(
            "ALTWISP",
            _create_icon_image(),
            "ALTWISP — Ready",
            menu=pystray.Menu(
                pystray.MenuItem("Open dashboard", self._open_dashboard, default=True),
                pystray.MenuItem("Start / stop dictation", self._toggle),
                pystray.MenuItem("Paste last dictation", self._paste_last),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit ALTWISP", self._quit),
            ),
        )

    def start(self):
        self.icon.run_detached()

    def stop(self):
        self.icon.stop()

    def notify(self, title, message):
        try:
            self.icon.notify(message, title)
        except Exception:
            pass

    def set_status(self, status):
        try:
            self.icon.title = f"ALTWISP — {status}"[:127]
        except Exception:
            pass

    def _open_dashboard(self, icon, item):
        del icon, item
        self.app.ui.enqueue(self.app.ui.show_dashboard)

    def _toggle(self, icon, item):
        del icon, item
        self.app.ui.enqueue(self.app.toggle_recording)

    def _paste_last(self, icon, item):
        del icon, item
        self.app.ui.enqueue(self.app.paste_last)

    def _quit(self, icon, item):
        del icon, item
        self.app.ui.enqueue(self.app.quit)
