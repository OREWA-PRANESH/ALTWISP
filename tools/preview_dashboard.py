"""Safe visual preview with isolated sample data; no audio, keys or network."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from config import Settings
from storage import Storage
from ui import AppUI

with tempfile.TemporaryDirectory() as directory:
    storage = Storage(Path(directory) / "preview.db")
    storage.add_history("", "Could we move the design review to Thursday? I'd like to share the updated prototype with the team first.", 12)
    storage.upsert_dictionary("alt wisp", "ALTWISP")
    storage.upsert_snippet("my sign off", "Thanks,\nHave a lovely day.")
    ui = AppUI(storage, Settings(), {"quit": lambda: ui.destroy(), "save_settings": lambda _: None})
    ui.root.setWindowTitle("ALTWISP — design preview")
    ui.run()
