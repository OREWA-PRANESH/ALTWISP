import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "native"))
from audio_manager import AudioManager


class FakeStream:
    def __init__(self, **kwargs):
        self.options = kwargs

    def start(self):
        pass

    def stop(self):
        pass

    def close(self):
        pass


class AudioManagerTests(unittest.TestCase):
    def test_selected_device_is_used_for_capture(self):
        with patch("audio_manager.sd.InputStream", side_effect=FakeStream) as create:
            audio = AudioManager(input_device=3)
            audio.start_recording()
            self.assertEqual(create.call_args.kwargs["device"], 3)
            audio.close()

    def test_silent_capture_has_no_wav_or_speech_level(self):
        with patch("audio_manager.sd.InputStream", side_effect=FakeStream):
            audio = AudioManager()
            audio.start_recording()
            audio._audio_callback(np.zeros((320, 1), dtype=np.int16), 320, None, None)
            path, _ = audio.stop_recording()
            self.assertIsNone(path)
            self.assertEqual(audio.peak_rms, 0)

    def test_capture_tracks_real_input_level(self):
        with patch("audio_manager.sd.InputStream", side_effect=FakeStream):
            audio = AudioManager()
            audio.start_recording()
            audio._audio_callback(np.full((320, 1), 500, dtype=np.int16), 320, None, None)
            path, _ = audio.stop_recording()
            self.assertGreaterEqual(audio.peak_rms, 500)
            self.assertTrue(Path(path).exists())
            Path(path).unlink()


if __name__ == "__main__":
    unittest.main()
