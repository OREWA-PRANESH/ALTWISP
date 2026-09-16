import os


class Transcriber:
    def __init__(self, backend="groq", local_model="small", language="auto"):
        self.backend = backend
        self.local_model = local_model
        self.language = language
        self._client = None
        self._local = None

    def _groq_client(self):
        if self._client is None:
            from cloud import create_client
            self._client = create_client()
        return self._client

    def _local_model_instance(self):
        if self._local is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise RuntimeError("Local mode requires: pip install faster-whisper") from exc
            self._local = WhisperModel(self.local_model, device="cpu", compute_type="int8")
        return self._local

    def transcribe(self, audio_file_path):
        if not audio_file_path or not os.path.exists(audio_file_path):
            return ""
        if os.path.getsize(audio_file_path) <= 44:
            return ""
        if self.backend == "local":
            segments, _ = self._local_model_instance().transcribe(
                audio_file_path,
                language=None if self.language == "auto" else self.language,
                vad_filter=True,
            )
            return " ".join(segment.text.strip() for segment in segments).strip()
        if self.backend != "groq":
            raise ValueError(f"Unsupported transcription backend: {self.backend}")
        with open(audio_file_path, "rb") as audio:
            result = self._groq_client().audio.transcriptions.create(
                file=(os.path.basename(audio_file_path), audio.read()),
                model="whisper-large-v3-turbo",
                response_format="text",
                language=None if self.language == "auto" else self.language,
            )
        if isinstance(result, bytes):
            result = result.decode("utf-8", errors="replace")
        return str(result or "").strip()
