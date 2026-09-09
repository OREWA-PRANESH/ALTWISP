"""Visual-only orb preview; does not capture audio or register hotkeys."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from PySide6.QtWidgets import QApplication
from qt_orb import OrbOverlay
app=QApplication([])
orb=OrbOverlay(64)
orb.show_orb()
orb.orb.set_volume(1000)
app.exec()
