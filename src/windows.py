"""Typed Windows calls; keep native handles pointer-sized on 64-bit Python."""
import ctypes
import sys
from ctypes import wintypes


class SingleInstance:
    def __init__(self):
        self.handle = None
        self.acquired = True
        if sys.platform == "win32":
            self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            self.kernel.CreateMutexW.argtypes = (ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR)
            self.kernel.CreateMutexW.restype = wintypes.HANDLE
            self.kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
            self.handle = self.kernel.CreateMutexW(None, False, "Local\\ALTWISP.DesktopAgent")
            if not self.handle:
                raise ctypes.WinError(ctypes.get_last_error())
            self.acquired = ctypes.get_last_error() != 183

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def foreground_window():
    if sys.platform != "win32":
        return None
    user32 = ctypes.WinDLL("user32")
    user32.GetForegroundWindow.restype = wintypes.HWND
    return user32.GetForegroundWindow()


class OverlayWindow:
    def __init__(self, widget):
        self.widget = widget
        self.handle = None
        if sys.platform == "win32":
            api = self.api = ctypes.WinDLL("user32", use_last_error=True)
            api.GetAncestor.argtypes = (wintypes.HWND, wintypes.UINT)
            api.GetAncestor.restype = wintypes.HWND
            api.GetWindowLongW.argtypes = (wintypes.HWND, ctypes.c_int)
            api.SetWindowLongW.argtypes = (wintypes.HWND, ctypes.c_int, wintypes.LONG)
            api.ShowWindow.argtypes = (wintypes.HWND, ctypes.c_int)
            api.SetWindowPos.argtypes = (wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT)
            native_id = widget.winId() if hasattr(widget, "winId") else widget.winfo_id()
            self.handle = api.GetAncestor(native_id, 2)
            style = api.GetWindowLongW(self.handle, -20)
            api.SetWindowLongW(self.handle, -20, style | 0x08000080)

    def show(self):
        if self.handle:
            self.api.ShowWindow(self.handle, 4)
            self.api.SetWindowPos(self.handle, -1, 0, 0, 0, 0, 0x0013)
        else:
            self.widget.deiconify()

    def hide(self):
        if self.handle:
            self.api.ShowWindow(self.handle, 0)
        else:
            self.widget.withdraw()
