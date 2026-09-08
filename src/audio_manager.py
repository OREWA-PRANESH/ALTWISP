import os
import tempfile
import threading
import time

import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write


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
        self._lock = threading.Lock()

    def start_recording(self):
        with self._lock:
            if self.recording:
                return True
            self.audio_data = []
            try:
                self.stream = sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="int16", callback=self._audio_callback)
                self.stream.start()
                self.recording = True
                self.started_at = time.monotonic()
                return True
            except Exception:
                self._close_stream()
                self.recording = False
                raise

    def _audio_callback(self, indata, frames, callback_time, status):
        del frames, callback_time
        if status:
            print(f"Audio status: {status}")
        if not self.recording:
            return
        self.audio_data.append(indata.copy())
        if self.on_volume_change:
            rms = float(np.sqrt(np.mean(indata.astype(np.float32) ** 2)))
            self.on_volume_change(rms)
        if self.started_at and time.monotonic() - self.started_at >= self.max_seconds:
            self.recording = False
            if self.on_max_duration:
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
            self._close_stream()
            duration = time.monotonic() - self.started_at if self.started_at else 0
            self.started_at = None
            if not self.audio_data:
                return None, duration
            audio = np.concatenate(self.audio_data, axis=0)
            self.audio_data = []
        file_descriptor, path = tempfile.mkstemp(prefix="altwisp_", suffix=".wav")
        os.close(file_descriptor)
        try:
            write(path, self.sample_rate, audio)
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
            self._close_stream()
            self.audio_data = []
