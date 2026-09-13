import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "native"))
from hotkey import CtrlWindowsChord, WindowsHotkeyConnection


def event(name, event_type, scan_code):
    return SimpleNamespace(name=name, event_type=event_type, scan_code=scan_code)


class ChordTests(unittest.TestCase):
    def setUp(self):
        self.calls = 0
        self.chord = CtrlWindowsChord(lambda: setattr(self, "calls", self.calls + 1))

    def send(self, *events):
        for item in events:
            self.chord.handle(item)

    def test_fires_once_only_after_both_keys_are_released(self):
        self.send(event("left ctrl", "down", 29), event("left windows", "down", 91))
        self.assertEqual(self.calls, 0)
        self.send(event("left ctrl", "up", 29))
        self.assertEqual(self.calls, 0)
        self.send(event("left windows", "up", 91))
        self.assertEqual(self.calls, 1)

    def test_accepts_right_side_keys_and_reverse_order(self):
        self.send(event("right windows", "down", 92), event("right ctrl", "down", 285),
                  event("right windows", "up", 92), event("right ctrl", "up", 285))
        self.assertEqual(self.calls, 1)

    def test_key_repeat_does_not_retrigger(self):
        self.send(event("ctrl", "down", 29), event("windows", "down", 91),
                  event("windows", "down", 91), event("windows", "up", 91),
                  event("ctrl", "up", 29))
        self.assertEqual(self.calls, 1)

    def test_another_key_cancels_the_chord(self):
        self.send(event("ctrl", "down", 29), event("windows", "down", 91),
                  event("a", "down", 30), event("windows", "up", 91),
                  event("ctrl", "up", 29))
        self.assertEqual(self.calls, 0)


class FakeKeyboard:
    def __init__(self):
        self.callback = None
        self.unhooked = None

    def hook(self, callback, suppress=False):
        self.callback = callback
        self.suppress = suppress
        return "hook-1"

    def unhook(self, handle):
        self.unhooked = handle


class ConnectionTests(unittest.TestCase):
    def test_connection_has_one_owned_hook_and_releases_it(self):
        backend = FakeKeyboard()
        connection = WindowsHotkeyConnection(backend, lambda: None)
        self.assertTrue(connection.start())
        connection.start()
        self.assertEqual(connection.handle, "hook-1")
        self.assertFalse(backend.suppress)
        connection.close()
        self.assertEqual(backend.unhooked, "hook-1")
        self.assertFalse(connection.active)


if __name__ == "__main__":
    unittest.main()
