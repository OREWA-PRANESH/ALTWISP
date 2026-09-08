import time

import pyautogui
import pyperclip


class Typer:
    @staticmethod
    def inject_text(text):
        if not text:
            return False
        original = None
        try:
            original = pyperclip.paste()
            pyperclip.copy(text)
            time.sleep(0.12)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.25)
            return True
        finally:
            if original is not None:
                try:
                    pyperclip.copy(original)
                except Exception as exc:
                    print(f"Could not restore clipboard: {exc}")
