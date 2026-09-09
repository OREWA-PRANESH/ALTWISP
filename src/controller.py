"""UI-owned recording state; one serial worker owns audio and network work."""
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

from audio_manager import AudioManager
from cloud import describe_error
from config import SettingsStore
from llm_processor import TextProcessor
from startup import set_launch_at_login
from storage import Storage
from transcriber import Transcriber
from typer import Typer

log = logging.getLogger(__name__)


class DictationController:
    def __init__(self):
        self.settings_store = SettingsStore()
        self.settings = self.settings_store.load()
        self.storage = Storage()
        self.storage.prune_history(self.settings.auto_delete_hours)
        self.audio = AudioManager(max_seconds=self.settings.max_recording_seconds)
        self.typer = Typer()
        self.ui = self.tray = None
        self.state = "idle"
        self.last_text = ""
        self.last_error = ""
        self.pending_audio = None
        self._pending_lock = threading.Lock()
        self.closed = False
        self.target_window = None
        self.worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="dictation")
        self._configure_pipeline()

    @property
    def is_recording(self):
        return self.state in {"starting", "recording"}

    def _configure_pipeline(self):
        self.transcriber = Transcriber(self.settings.transcription_backend, self.settings.local_model, self.settings.language)
        # Local means no cloud traffic, including optional polishing.
        self.processor = TextProcessor(self.storage, self.settings.polish_enabled and self.settings.transcription_backend == "groq", self.settings.style)
        self.audio.max_seconds = self.settings.max_recording_seconds

    def attach_ui(self, ui):
        self.ui = ui
        self.audio.on_volume_change = ui.update_waveform_from_volume
        self.audio.on_max_duration = lambda: self._post(self.stop_recording)

    def attach_tray(self, tray):
        self.tray = tray

    def _post(self, callback, *args):
        if not self.closed:
            self.ui.enqueue(callback, *args)

    def _status(self, message):
        log.info("state=%s status=%s", self.state, message)
        self.ui.set_status(message)
        if self.tray:
            self.tray.set_status(message)

    def toggle_recording(self):
        if self.closed:
            return
        if self.is_recording:
            self.stop_recording()
        elif self.state == "idle":
            self.start_recording()
        else:
            self._status("Finishing your words…")

    def start_recording(self):
        if self.closed or self.state != "idle":
            return
        self.target_window = self.typer.foreground_window()
        self.state = "starting"
        self.ui.show_recording()  # Paint before touching the audio device.
        self._status("Opening microphone…")
        self.worker.submit(self._start_capture)

    def _start_capture(self):
        try:
            self.audio.start_recording()
            if self.state != "starting" or self.closed:
                self.audio.recording = False
            self._post(self._capture_ready)
        except Exception as exc:
            log.exception("Microphone initialization failed")
            self._post(self._capture_failed, exc)

    def _capture_ready(self):
        if self.state == "starting":
            self.state = "recording"
            self._status("Listening")

    def _capture_failed(self, exc):
        self.ui.hide_recording()
        if self.state == "starting":
            self.state = "idle"
        self._error("Microphone unavailable", exc)

    def stop_recording(self):
        if not self.is_recording or self.closed:
            return
        self.state = "processing"  # Reserve the session before queuing work.
        self.audio.recording = False
        self.ui.hide_recording()  # No network, device close or file I/O first.
        self._status("Transcribing…")
        self.worker.submit(self._finish_capture, False)

    def cancel_recording(self):
        if not self.is_recording or self.closed:
            return
        self.state = "processing"
        self.audio.recording = False
        self.ui.hide_recording()
        self._status("Cancelled")
        self.worker.submit(self._finish_capture, True)

    @staticmethod
    def _remove(path):
        if path:
            try:
                os.remove(path)
            except OSError:
                log.warning("Temporary recording cleanup failed")

    def _finish_capture(self, cancelled):
        try:
            path, duration = self.audio.stop_recording()
            if cancelled or self.closed:
                self._remove(path)
                self._post(self._complete, "Cancelled")
            elif path:
                self._transcribe(path, duration, self.target_window)
            else:
                self._post(self._complete, "No audio captured")
        except Exception as exc:
            log.exception("Recording finalization failed")
            self._post(self._failed, exc)

    def _transcribe(self, path, duration, target):
        retain = False
        try:
            raw = self.transcriber.transcribe(path)
            if self.closed:
                return
            if not raw:
                self._post(self._complete, "No speech recognized")
                return
            text = self.processor.process_text(raw) or raw
            if self.closed:
                return
            self.last_text = text
            if self.settings.save_history:
                try:
                    self.storage.add_history(raw, text, duration)
                except Exception:
                    log.exception("History write failed; dictation remains available")
            # A retry from the dashboard recovers text without pasting into a
            # settings field. A changed target is also recovered, never stolen.
            pasted = False
            if target and not self.closed:
                try:
                    pasted = self.typer.inject_text(text, target_window=target)
                except Exception:
                    log.exception("Paste failed; result available in dashboard")
            self._post(self._complete, "Text inserted" if pasted else "Text ready — copy it from Home")
        except Exception as exc:
            log.warning("Transcription failed: %s; cause=%s", type(exc).__name__, type(exc.__cause__).__name__)
            with self._pending_lock:
                if not self.closed:
                    if self.pending_audio:
                        self._remove(self.pending_audio[0])
                    self.pending_audio = (path, duration)
                    retain = True
            if retain:
                self._post(self._failed, exc)
        finally:
            if not retain:
                self._remove(path)

    def _complete(self, message):
        self.state = "idle"
        self._status(message)
        self.ui.refresh_if_visible()

    def _error(self, title, exc):
        self.last_error = describe_error(exc)
        self._status(title)
        self.ui.show_error(title, self.last_error)
        if self.tray:
            self.tray.notify(title, self.last_error)

    def _failed(self, exc):
        self.state = "idle"
        self._error("Dictation failed", exc)

    def retry(self):
        if self.state != "idle" or not self.pending_audio:
            return
        path, duration = self.pending_audio
        self.pending_audio = None
        self.state = "processing"
        self._status("Retrying saved recording…")
        self.worker.submit(self._transcribe, path, duration, None)

    def discard_failed(self):
        if self.pending_audio:
            self._remove(self.pending_audio[0])
            self.pending_audio = None
        self._status("Failed recording discarded")

    def paste_last(self):
        if self.state != "idle":
            return
        if not self.last_text:
            rows = self.storage.recent_history(1)
            self.last_text = rows[0]["final_text"] if rows else ""
        if self.last_text:
            target = self.typer.foreground_window()
            self.state = "processing"
            self.worker.submit(self._paste_last_worker, target)

    def _paste_last_worker(self, target):
        try:
            ok = self.typer.inject_text(self.last_text, target_window=target)
            self._post(self._complete, "Text inserted" if ok else "Text ready — copy it from Home")
        except Exception as exc:
            self._post(self._failed, exc)

    def save_settings(self, values):
        if self.state != "idle":
            raise RuntimeError("Finish the current dictation before changing settings.")
        settings = replace(self.settings, transcription_backend=values["backend"], local_model=values["model"],
            language=values["language"].strip() or "auto", style=values["style"], polish_enabled=bool(values["polish"]),
            save_history=bool(values["history"]), auto_delete_hours=int(values["retention"]), launch_at_login=bool(values["autostart"]))
        if settings.transcription_backend not in {"local", "groq"}:
            raise ValueError("Choose Local or Groq.")
        if settings.launch_at_login != self.settings.launch_at_login:
            set_launch_at_login(settings.launch_at_login)
        self.settings_store.save(settings)
        for client in (self.transcriber._client, self.processor._client):
            if client:
                client.close()
        self.settings = settings
        self.storage.prune_history(settings.auto_delete_hours)
        self._configure_pipeline()

    def quit(self):
        import keyboard
        with self._pending_lock:
            self.closed = True
            if self.pending_audio:
                self._remove(self.pending_audio[0])
                self.pending_audio = None
        keyboard.unhook_all()
        self.audio.recording = False
        self.worker.submit(self.audio.close)
        self.worker.shutdown(wait=False)
        if self.tray:
            self.tray.stop()
        self.ui.destroy()
