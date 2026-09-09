import queue
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent / "src"))
from config import Settings, SettingsStore
from controller import DictationController
from main import ModifierReleaseHotkey
from storage import Storage
from llm_processor import TextProcessor


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Storage(Path(self.temp.name) / "test.db")
        with patch("controller.SettingsStore") as settings, patch("controller.Storage", return_value=self.store):
            settings.return_value.load.return_value = Settings()
            self.app = DictationController()
        self.ui = Mock()
        self.calls = queue.Queue()
        self.ui.enqueue.side_effect = lambda callback, *args: self.calls.put((callback, args))
        self.app.attach_ui(self.ui)
        self.app.audio = Mock(recording=False)
        self.app.typer = Mock()
        self.app.typer.foreground_window.return_value = 123
        self.app.transcriber = Mock()
        self.app.processor = Mock()

    def drain(self):
        self.app.worker.submit(lambda: None).result(timeout=3)
        while not self.calls.empty():
            callback, args = self.calls.get_nowait()
            callback(*args)

    def tearDown(self):
        self.app.closed = True
        self.app.worker.shutdown(wait=True)
        self.temp.cleanup()

    def recording(self):
        path = Path(self.temp.name) / "recording.wav"
        path.write_bytes(b"synthetic recording")
        return str(path)

    def test_show_and_hide_do_not_wait_for_slow_microphone(self):
        gate = threading.Event()
        self.app.audio.start_recording.side_effect = lambda: gate.wait(2)
        self.app.audio.stop_recording.return_value = (None, 0)
        try:
            start = time.perf_counter()
            self.app.toggle_recording()
            self.assertLess(time.perf_counter() - start, 0.1)
            self.ui.show_recording.assert_called_once()
            self.app.toggle_recording()  # Stop while driver initialization is pending.
            self.ui.hide_recording.assert_called_once()
            self.assertEqual(self.app.state, "processing")
        finally:
            gate.set()
        self.drain()
        self.assertEqual(self.app.state, "idle")
        self.assertFalse(self.app.audio.recording)

    def test_processing_blocks_second_session_until_complete(self):
        self.app.state = "processing"
        self.app.toggle_recording()
        self.app.audio.start_recording.assert_not_called()

    def test_microphone_failure_returns_idle_and_hides_orb(self):
        self.app.audio.start_recording.side_effect = RuntimeError("No microphone")
        self.app.start_recording()
        self.drain()
        self.assertEqual(self.app.state, "idle")
        self.ui.hide_recording.assert_called()
        self.ui.show_error.assert_called()

    def test_connection_failure_retains_audio_for_explicit_retry(self):
        path = self.recording()
        self.app.transcriber.transcribe.side_effect = RuntimeError("Offline")
        self.app._transcribe(path, 2, 123)
        self.drain()
        self.assertTrue(Path(path).exists())
        self.assertEqual(self.app.pending_audio[0], path)
        self.app.transcriber.transcribe.side_effect = None
        self.app.transcriber.transcribe.return_value = "Hello"
        self.app.processor.process_text.return_value = "Hello."
        self.app.retry()
        self.drain()
        self.assertFalse(Path(path).exists())
        self.assertEqual(self.app.last_text, "Hello.")
        self.app.typer.inject_text.assert_not_called()

    def test_cancel_removes_audio_without_transcription(self):
        path = self.recording()
        self.app.audio.stop_recording.return_value = (path, 1)
        self.app.state = "recording"
        self.app.cancel_recording()
        self.drain()
        self.assertFalse(Path(path).exists())
        self.app.transcriber.transcribe.assert_not_called()

    def test_shutdown_during_transcription_does_not_paste(self):
        path = self.recording()
        def finish(_):
            self.app.closed = True
            return "Hello"
        self.app.transcriber.transcribe.side_effect = finish
        self.app._transcribe(path, 1, 123)
        self.assertFalse(Path(path).exists())
        self.app.typer.inject_text.assert_not_called()

    def test_local_mode_never_initializes_cloud_polisher(self):
        self.app.settings.transcription_backend = "local"
        self.app._configure_pipeline()
        with patch.object(self.app.processor, "_groq_client") as client:
            self.assertEqual(self.app.processor.process_text("Hello there"), "Hello there")
            client.assert_not_called()

    def test_disabled_polishing_avoids_client_setup(self):
        processor = TextProcessor(self.store, polish_enabled=False)
        with patch.object(processor, "_groq_client") as client:
            self.assertEqual(processor.process_text("Hello there"), "Hello there")
            client.assert_not_called()

    def test_hotkey_waits_for_both_releases_and_ignores_repeat(self):
        callback = Mock()
        hotkey = ModifierReleaseHotkey(callback)
        def event(name, kind):
            hotkey.handle(SimpleNamespace(name=name, event_type=kind))
        for _ in range(2):
            event("left ctrl", "down")
            event("left windows", "down")
            event("left windows", "down")
            event("left windows", "up")
            self.assertEqual(callback.call_count, _)
            event("left ctrl", "up")
        self.assertEqual(callback.call_count, 2)

    def test_other_key_cancels_chord(self):
        callback = Mock()
        hotkey = ModifierReleaseHotkey(callback)
        for name, kind in (("ctrl", "down"), ("windows", "down"), ("d", "down"), ("ctrl", "up"), ("windows", "up")):
            hotkey.handle(SimpleNamespace(name=name, event_type=kind))
        callback.assert_not_called()


if __name__ == "__main__":
    unittest.main()
