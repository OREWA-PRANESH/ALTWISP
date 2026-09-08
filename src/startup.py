import sys

from config import APP_NAME, application_dir


def command_for_current_app():
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --background'
    packaged = application_dir() / "ALTWISP.exe"
    if packaged.exists():
        return f'"{packaged}" --background'
    pythonw = application_dir() / "venv" / "Scripts" / "pythonw.exe"
    executable = pythonw if pythonw.exists() else sys.executable
    main = application_dir() / "src" / "main.py"
    return f'"{executable}" "{main}" --background'


def set_launch_at_login(enabled):
    if sys.platform != "win32":
        raise RuntimeError("Launch at login is currently supported only on Windows.")
    import winreg

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command_for_current_app())
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
