import argparse
import os
import sys
import threading
import traceback

import keyboard
from dotenv import load_dotenv

from config import SettingsStore, application_dir
from storage import Storage


load_dotenv(application_dir() / ".env")

from audio_manager import AudioManager
from llm_processor import TextProcessor
from startup import set_launch_at_login
from transcriber import Transcriber
from typer import Typer
from ui import AppUI
from tray_icon import TrayIcon


class ModifierReleaseHotkey:
    """Detect a Ctrl+Windows chord and fire exactly once when it is released."""

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
            return
        if event.event_type == keyboard.KEY_DOWN:
            self.pressed.add(group)
            if self.pressed == {"ctrl", "windows"}:
                self.armed = True
            return
        if event.event_type == keyboard.KEY_UP:
            should_fire = self.armed and group in self.pressed
            self.pressed.discard(group)
            if should_fire:
                self.armed = False
                self.callback()


class AltWispApp:
    def __init__(self):
        self.settings_store = SettingsStore()
        self.settings = self.settings_store.load()
        self.storage = Storage()
        self.storage.prune_history(self.settings.auto_delete_hours)
        self.audio = AudioManager(max_seconds=self.settings.max_recording_seconds)
        self.transcriber = None
        self.processor = None
        self.typer = Typer()
        self.ui = None
        self.tray = None
        self.is_recording = False
        self.last_text = ""
        self.processing_lock = threading.Lock()
        self.state_lock = threading.RLock()
        self.primary_hotkey = None
        self._configure_pipeline()

    def _configure_pipeline(self):
        self.transcriber = Transcriber(
            backend=self.settings.transcription_backend,
            local_model=self.settings.local_model,
            language=self.settings.language,
        )
        self.processor = TextProcessor(self.storage, self.settings.polish_enabled, self.settings.style)
        self.audio.max_seconds = self.settings.max_recording_seconds

    def attach_ui(self, ui):
        self.ui = ui
        self.audio.on_volume_change = ui.update_waveform_from_volume
        self.audio.on_max_duration = lambda: ui.enqueue(self.stop_recording)

    def attach_tray(self, tray):
        self.tray = tray

    def toggle_recording(self):
        with self.state_lock:
            if self.processing_lock.locked():
                self._status("Finishing the previous dictation…")
                return
            if self.is_recording:
                self.stop_recording()
            else:
                self.start_recording()

    def start_recording(self):
        try:
            self.audio.start_recording()
        except Exception as exc:
            self.is_recording = False
            self._status("Microphone unavailable")
            self.ui.hide_recording()
            self.ui.show_error("Microphone unavailable", f"ALTWISP could not start recording.\n\n{exc}")
            return
        self.is_recording = True
        self._status("Listening…")
        self.ui.set_overlay_status("Listening…")
        self.ui.show_recording()

    def stop_recording(self):
        with self.state_lock:
            if not self.is_recording and not self.audio.recording:
                return
            self.is_recording = False
            self.ui.set_overlay_status("Processing…")
            try:
                audio_file, duration = self.audio.stop_recording()
            except Exception as exc:
                self.ui.hide_recording()
                self._report_error("Could not save recording", exc)
                return
            if not audio_file:
                self.ui.hide_recording()
                self._status("No speech captured")
                return
            threading.Thread(target=self.process_audio, args=(audio_file, duration), daemon=True).start()

    def cancel_recording(self):
        with self.state_lock:
            if not self.is_recording:
                return
            self.is_recording = False
            try:
                audio_file, _ = self.audio.stop_recording()
                if audio_file:
                    os.remove(audio_file)
            except OSError:
                pass
            finally:
                self.ui.hide_recording()
                self._status("Dictation cancelled")

    def process_audio(self, audio_file, duration):
        with self.processing_lock:
            try:
                self._status("Transcribing…")
                raw_text = self.transcriber.transcribe(audio_file)
                if not raw_text:
                    self._status("No speech recognized")
                    return
                self._status("Polishing…")
                final_text = self.processor.process_text(raw_text)
                if not final_text:
                    self._status("No text produced")
                    return
                self.last_text = final_text
                if self.settings.save_history:
                    self.storage.add_history(raw_text, final_text, duration)
                self.typer.inject_text(final_text)
                self._status(f"Pasted {len(final_text.split())} words")
                self.ui.enqueue(self.ui.refresh)
            except Exception as exc:
                self._report_error("Dictation failed", exc)
            finally:
                try:
                    os.remove(audio_file)
                except OSError:
                    pass
                self.ui.hide_recording()

    def paste_last(self):
        if self.last_text:
            try:
                self.typer.inject_text(self.last_text)
                self._status("Pasted last dictation")
            except Exception as exc:
                self._report_error("Paste failed", exc)
        else:
            history = self.storage.recent_history(1)
            if history:
                self.last_text = history[0]["final_text"]
                self.paste_last()
            else:
                self._status("No previous dictation")

    def save_settings(self, values):
        old_autostart = self.settings.launch_at_login
        self.settings.transcription_backend = values["backend"]
        self.settings.local_model = values["model"]
        self.settings.language = values["language"].strip() or "auto"
        self.settings.style = values["style"]
        self.settings.polish_enabled = bool(values["polish"])
        self.settings.save_history = bool(values["history"])
        self.settings.auto_delete_hours = values["retention"]
        self.settings.launch_at_login = bool(values["autostart"])
        if old_autostart != self.settings.launch_at_login:
            set_launch_at_login(self.settings.launch_at_login)
        self.settings_store.save(self.settings)
        self.storage.prune_history(self.settings.auto_delete_hours)
        self._configure_pipeline()

    def register_hotkeys(self):
        # Keyboard hooks run on their own thread. Only enqueue work here; audio
        # state and Tk widgets are controlled from the main application thread.
        self.primary_hotkey = ModifierReleaseHotkey(lambda: self.ui.enqueue(self.toggle_recording))
        keyboard.hook(self.primary_hotkey.handle, suppress=False)
        keyboard.add_hotkey(
            self.settings.paste_last_hotkey,
            lambda: self.ui.enqueue(self.paste_last),
            trigger_on_release=True,
        )
        keyboard.add_hotkey(
            "ctrl+alt+d",
            lambda: self.ui.enqueue(self.ui.show_dashboard),
            trigger_on_release=True,
        )
        keyboard.add_hotkey("esc", lambda: self.ui.enqueue(self.cancel_recording), trigger_on_release=True)

    def quit(self):
        try:
            keyboard.unhook_all()
            self.audio.close()
            if self.tray:
                self.tray.stop()
        finally:
            self.ui.enqueue(self.ui.root.destroy)

    def _status(self, message):
        print(message)
        if self.ui:
            self.ui.set_status(message)
        if self.tray:
            self.tray.set_status(message)

    def _report_error(self, title, exc):
        traceback.print_exc()
        self._status(title)
        if self.ui:
            self.ui.show_error(title, str(exc))


def parse_args():
    parser = argparse.ArgumentParser(description="ALTWISP voice dictation")
    parser.add_argument("--background", action="store_true", help="Start with the dashboard hidden")
    return parser.parse_args()


def main():
    args = parse_args()
    app = AltWispApp()
    callbacks = {
        "toggle": app.toggle_recording,
        "quit": app.quit,
        "save_settings": app.save_settings,
    }
    ui = AppUI(app.storage, app.settings, callbacks)
    app.attach_ui(ui)
    tray = TrayIcon(app)
    app.attach_tray(tray)
    try:
        app.register_hotkeys()
    except Exception as exc:
        ui.show_error("Hotkey registration failed", str(exc))
    tray.start()
    ui.run(background=args.background)


if __name__ == "__main__":
    main()
