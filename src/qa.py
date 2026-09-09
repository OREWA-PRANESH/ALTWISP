"""Opt-in UI latency check with simulated audio. Never captures or pastes."""
import json
import queue
import tempfile
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from config import Settings
from controller import DictationController
from storage import Storage
from ui import AppUI


def run(report_path):
    from main import ModifierReleaseHotkey
    with tempfile.TemporaryDirectory() as directory:
        with patch("controller.SettingsStore") as config, patch("controller.Storage", return_value=Storage(Path(directory) / "qa.db")):
            config.return_value.load.return_value = Settings()
            app = DictationController()
        app.audio = Mock(recording=False)
        app.audio.start_recording.side_effect = lambda: time.sleep(.08)
        app.audio.stop_recording.side_effect = lambda: (time.sleep(.04) or (None, .1))
        app.typer = Mock()
        app.typer.foreground_window.return_value = 111
        ui = AppUI(app.storage, app.settings, {"quit": lambda: None, "last_text": lambda: ""})
        app.attach_ui(ui)
        hook = ModifierReleaseHotkey(lambda: ui.enqueue(app.toggle_recording))
        latencies = {"show": [], "hide": []}
        sent = [0.0]
        events = queue.Queue()
        original_show, original_hide = ui.native_overlay.show_orb, ui.native_overlay.hide_orb

        def show():
            original_show()
            latencies["show"].append((time.perf_counter() - sent[0]) * 1000)
            events.put("shown")

        def hide():
            original_hide()
            latencies["hide"].append((time.perf_counter() - sent[0]) * 1000)
            events.put("hidden")

        ui.native_overlay.show_orb, ui.native_overlay.hide_orb = show, hide

        def chord():
            sent[0] = time.perf_counter()
            for name, kind in (("ctrl", "down"), ("windows", "down"), ("windows", "up"), ("ctrl", "up")):
                hook.handle(SimpleNamespace(name=name, event_type=kind))

        outcome = {}
        def exercise():
            try:
                for _ in range(20):
                    chord()
                    assert events.get(timeout=2) == "shown"
                    # Release again while the 80ms fake microphone init is pending.
                    chord()
                    assert events.get(timeout=2) == "hidden"
                    deadline = time.perf_counter() + 3
                    while app.state != "idle" and time.perf_counter() < deadline:
                        time.sleep(.005)
                    assert app.state == "idle"
                for key, values in latencies.items():
                    values.sort()
                    outcome[key + "_p95_ms"] = round(values[int(.95 * (len(values) - 1))], 2)
                outcome["cycles"] = 20
                outcome["orb_size"] = ui.orb.size
                outcome["passed"] = max(outcome["show_p95_ms"], outcome["hide_p95_ms"]) < 100
            except Exception as exc:
                outcome.update(passed=False, error=repr(exc))
            finally:
                ui.enqueue(ui.destroy)

        threading.Thread(target=exercise, daemon=True).start()
        ui.run(background=True)
        app.closed = True
        app.worker.shutdown(wait=True)
        Path(report_path).write_text(json.dumps(outcome, indent=2), encoding="utf-8")
        return outcome
