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
    input_device: int | None = None
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


def validate_settings(settings: Settings) -> Settings:
    for name, choices in {"transcription_backend": {"groq", "local"}, "local_model": {"tiny", "base", "small", "medium", "large-v3"}, "style": {"neutral", "casual", "formal", "concise"}}.items():
        if getattr(settings, name) not in choices:
            raise ValueError(f"Invalid {name.replace('_', ' ')}")
    if not isinstance(settings.language, str) or not settings.language or len(settings.language) > 16:
        raise ValueError("Choose a valid language")
    for name in ("polish_enabled", "save_history", "launch_at_login"):
        if type(getattr(settings, name)) is not bool:
            raise ValueError(f"Invalid {name.replace('_', ' ')}")
    for name, minimum, maximum in (("auto_delete_hours", 0, 87600), ("max_recording_seconds", 1, 3600)):
        value = getattr(settings, name)
        if type(value) is not int or not minimum <= value <= maximum:
            raise ValueError(f"Invalid {name.replace('_', ' ')}")
    if settings.input_device is not None and (type(settings.input_device) is not int or settings.input_device < 0):
        raise ValueError("Choose a valid microphone")
    return settings


class SettingsStore:
    def __init__(self, path: Path | None = None):
        self.path = path or app_data_dir() / "settings.json"

    def load(self) -> Settings:
        if not self.path.exists():
            return Settings()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            allowed = {field.name for field in fields(Settings)}
            return validate_settings(Settings(**{k: v for k, v in data.items() if k in allowed}))
        except (OSError, ValueError, TypeError):
            return Settings()

    def save(self, settings: Settings) -> None:
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
        temp.replace(self.path)
