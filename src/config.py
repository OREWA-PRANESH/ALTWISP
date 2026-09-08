import json
import os
import sys
from dataclasses import asdict, dataclass, fields
from pathlib import Path


APP_NAME = "ALTWISP"


def app_data_dir() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    path = base / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def application_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


@dataclass
class Settings:
    hotkey: str = "ctrl+windows"
    paste_last_hotkey: str = "shift+alt+z"
    transcription_backend: str = "groq"
    local_model: str = "small"
    language: str = "auto"
    polish_enabled: bool = True
    style: str = "neutral"
    save_history: bool = True
    auto_delete_hours: int = 0
    max_recording_seconds: int = 300
    launch_at_login: bool = False


class SettingsStore:
    def __init__(self, path: Path | None = None):
        self.path = path or app_data_dir() / "settings.json"

    def load(self) -> Settings:
        if not self.path.exists():
            return Settings()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            allowed = {field.name for field in fields(Settings)}
            return Settings(**{k: v for k, v in data.items() if k in allowed})
        except (OSError, ValueError, TypeError):
            return Settings()

    def save(self, settings: Settings) -> None:
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
        temp.replace(self.path)
