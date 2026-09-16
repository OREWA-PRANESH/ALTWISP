import os
import tempfile
import threading
import time
import wave

import numpy as np
import sounddevice as sd


class AudioManager:
    def __init__(self, sample_rate=16000, max_seconds=300):
        self.sample_rate = sample_rate
        self.max_seconds = max_seconds
        self.recording = False
        self.audio_data = []
        self.stream = None
        self.on_volume_change = None
        self.on_max_duration = None
        self.started_at = None
        self._max_duration_notified = False
        self._lock = threading.Lock()

    def start_recording(self):
        with self._lock:
            if self.recording:
                return True
            self.audio_data = []
            self._max_duration_notified = False
            try:
                self.stream = sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="int16", blocksize=320, callback=self._audio_callback)
                self.recording = True
                self.started_at = time.monotonic()
                stream = self.stream
            except Exception:
                self.recording = False
                self._close_stream()
                raise
        try:
            stream.start()
            return True
        except Exception:
            with self._lock:
                self.recording = False
                self.started_at = None
                self.stream = None
            try:
                stream.close()
            except Exception:
                pass
            raise

    def _audio_callback(self, indata, frames, callback_time, status):
        del frames, callback_time
        if status:
            print(f"Audio status: {status}")
        with self._lock:
            if not self.recording:
                return
            self.audio_data.append(indata.copy())
            callback = self.on_volume_change
            reached_max = bool(self.started_at and time.monotonic() - self.started_at >= self.max_seconds and not self._max_duration_notified)
            if reached_max:
                self._max_duration_notified = True
                self.recording = False
            started_at = self.started_at
        if callback:
            rms = float(np.sqrt(np.mean(indata.astype(np.float32) ** 2)))
            callback(rms)
        if reached_max and self.on_max_duration:
            self.on_max_duration()

    def _close_stream(self):
        stream, self.stream = self.stream, None
        if stream:
            try:
                stream.stop()
            finally:
                stream.close()

    def stop_recording(self):
        with self._lock:
            self.recording = False
            duration = time.monotonic() - self.started_at if self.started_at else 0
            self.started_at = None
            stream, self.stream = self.stream, None
            chunks = self.audio_data
            self.audio_data = []
        if stream:
            try:
                stream.stop()
            finally:
                stream.close()
        if not chunks:
            return None, duration
        audio = np.concatenate(chunks, axis=0)
        file_descriptor, path = tempfile.mkstemp(prefix="altwisp_", suffix=".wav")
        os.close(file_descriptor)
        try:
            with wave.open(path, "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(self.sample_rate)
                wav.writeframes(audio.astype('<i2', copy=False).tobytes())
            return path, duration
        except Exception:
            try:
                os.remove(path)
            except OSError:
                pass
            raise

    def close(self):
        with self._lock:
            self.recording = False
            stream, self.stream = self.stream, None
            self.started_at = None
            self.audio_data = []
        if stream:
            try:
                stream.stop()
            finally:
                stream.close()
