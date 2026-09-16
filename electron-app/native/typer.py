import time

import pyautogui
import pyperclip
from windows import foreground_window


class Typer:
    foreground_window = staticmethod(foreground_window)

    @staticmethod
    def inject_text(text, target_window=None):
        if not text or target_window is None:
            return False
        if target_window and foreground_window() != target_window:
            return False
        original = None
        try:
            original = pyperclip.paste()
            pyperclip.copy(text)
            time.sleep(0.03)
            if target_window and foreground_window() != target_window:
                return False
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.25)
            return True
        finally:
            if original is not None:
                try:
                    if pyperclip.paste() == text:
                        pyperclip.copy(original)
                except Exception as exc:
                    print(f"Could not restore clipboard: {exc}")
