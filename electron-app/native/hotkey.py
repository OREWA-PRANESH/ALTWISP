"""One small, testable connection between Windows key events and dictation."""


def _modifier(name):
    value = (name or "").lower().strip()
    if "ctrl" in value or "control" in value:
        return "ctrl"
    if "windows" in value or value in {"win", "left win", "right win"}:
        return "windows"
    return None


class CtrlWindowsChord:
    """Fire once after Ctrl+Windows has been pressed and fully released."""

    def __init__(self, callback):
        self.callback = callback
        self.pressed = set()
        self.armed = False

    def handle(self, event):
        modifier = _modifier(getattr(event, "name", ""))
        event_type = getattr(event, "event_type", "")
        if not modifier:
            if event_type == "down":
                self.armed = False
            return

        identity = (modifier, getattr(event, "scan_code", None))
        if event_type == "down":
            self.pressed.add(identity)
            if {item[0] for item in self.pressed} == {"ctrl", "windows"}:
                self.armed = True
            return

        if event_type == "up":
            self.pressed.discard(identity)
            if self.armed and not self.pressed:
                self.armed = False
                self.callback()


class WindowsHotkeyConnection:
    """Own the sole keyboard hook used by the worker."""

    def __init__(self, keyboard_backend, callback):
        self.backend = keyboard_backend
        self.chord = CtrlWindowsChord(callback)
        self.handle = None

    @property
    def active(self):
        return self.handle is not None

    def start(self):
        if not self.active:
            self.handle = self.backend.hook(self.chord.handle, suppress=False)
        return self.active

    def close(self):
        if self.active:
            self.backend.unhook(self.handle)
            self.handle = None
