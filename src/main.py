import argparse
import logging
from logging.handlers import RotatingFileHandler

import keyboard
from dotenv import load_dotenv
from config import SettingsStore, app_data_dir, application_dir
from controller import DictationController
from ui import AppUI
from tray_icon import TrayIcon

load_dotenv(application_dir() / ".env")


class ModifierReleaseHotkey:
    """One toggle after BOTH chord keys are released; ignores repeats."""
    def __init__(self, callback):
        self.callback = callback
        self.pressed = set()
        self.armed = False

    @staticmethod
    def _group(name):
        name = (name or "").lower()
        if "ctrl" in name or "control" in name:
            return "ctrl"
        if "windows" in name or name in {"win", "left win", "right win"}:
            return "windows"
        return None

    def handle(self, event):
        group = self._group(event.name)
        if not group:
            if event.event_type == keyboard.KEY_DOWN:
                self.armed = False
            return
        identity = (group, getattr(event, "scan_code", event.name))
        if event.event_type == keyboard.KEY_DOWN:
            self.pressed.add(identity)
            if {key[0] for key in self.pressed} == {"ctrl", "windows"}:
                self.armed = True
        elif event.event_type == keyboard.KEY_UP:
            self.pressed.discard(identity)
            if self.armed and not self.pressed:
                self.armed = False
                self.callback()


class AltWispApp(DictationController):
    def register_hotkeys(self):
        self.primary_hotkey = ModifierReleaseHotkey(lambda: self.ui.enqueue(self.toggle_recording))
        keyboard.hook(self.primary_hotkey.handle, suppress=False)
        keyboard.add_hotkey(self.settings.paste_last_hotkey, lambda: self.ui.enqueue(self.paste_last), trigger_on_release=True)
        keyboard.add_hotkey("ctrl+alt+d", lambda: self.ui.enqueue(self.ui.show_dashboard), trigger_on_release=True)
        keyboard.add_hotkey("esc", lambda: self.ui.enqueue(self.cancel_recording), trigger_on_release=True)


def main():
    parser = argparse.ArgumentParser(description="ALTWISP voice dictation")
    parser.add_argument("--background", action="store_true")
    parser.add_argument("--self-test", metavar="REPORT", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.self_test:
        from qa import run
        run(args.self_test)
        return
    handler = RotatingFileHandler(app_data_dir() / "diagnostics.log", maxBytes=500_000, backupCount=2, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.basicConfig(level=logging.WARNING, handlers=[handler])
    # Prevent duplicate hooks and duplicate pastes from multiple launches.
    from windows import SingleInstance
    instance = SingleInstance()
    if not instance.acquired:
        return
    app = AltWispApp()
    ui = AppUI(app.storage, app.settings, {
        "toggle": app.toggle_recording, "quit": app.quit, "save_settings": app.save_settings,
        "retry": app.retry, "discard": app.discard_failed,
        "last_text": lambda: app.last_text,
    })
    app.attach_ui(ui)
    tray = TrayIcon(app)
    app.attach_tray(tray)
    try:
        app.register_hotkeys()
        tray.start()
        ui.run(background=args.background)
    finally:
        if not app.closed:
            app.quit()
        instance.close()


if __name__ == "__main__":
    main()
