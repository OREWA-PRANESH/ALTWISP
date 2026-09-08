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
            from groq import Groq
            key = os.environ.get("GROQ_API_KEY")
            if not key:
                raise RuntimeError("GROQ_API_KEY is missing. Add it in Settings or switch to Local Whisper.")
            self._client = Groq(api_key=key)
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
        if self.backend == "local":
            segments, _ = self._local_model_instance().transcribe(
                audio_file_path,
                language=None if self.language == "auto" else self.language,
                vad_filter=True,
            )
            return " ".join(segment.text.strip() for segment in segments).strip()
        with open(audio_file_path, "rb") as audio:
            result = self._groq_client().audio.transcriptions.create(
                file=(os.path.basename(audio_file_path), audio.read()),
                model="whisper-large-v3-turbo",
                response_format="text",
                language=None if self.language == "auto" else self.language,
            )
        return result.strip()
