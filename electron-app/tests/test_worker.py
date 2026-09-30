import sys
import io
import tempfile
import threading
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch
from contextlib import redirect_stdout

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'native'))
from agent import Agent
from config import Settings, SettingsStore, validate_settings
from llm_processor import TextProcessor
from storage import Storage
from transcriber import Transcriber
from typer import Typer


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.storage = Storage(Path(self.temp.name) / 'test.db')

    def test_cached_snapshots_are_copies_and_invalidate_on_mutation(self):
        self.storage.add_history('raw', 'one  two\nthree', 2)
        self.assertEqual(self.storage.stats()['words'], 3)
        with patch('storage.sqlite3.connect', side_effect=AssertionError('Warm reads must not reopen SQLite')):
            self.storage.stats()['words'] = 999
            self.assertEqual(self.storage.stats()['words'], 3)
        self.storage.recent_history()[0]['final_text'] = 'changed'
        self.assertEqual(self.storage.recent_history()[0]['final_text'], 'one  two\nthree')
        self.storage.delete_history()
        self.assertEqual(self.storage.stats()['dictations'], 0)
        self.assertEqual(self.storage.recent_history(), [])

    def test_dictionary_and_snippet_updates_invalidate_compiled_rules(self):
        processor = TextProcessor(self.storage, polish_enabled=False)
        self.storage.upsert_dictionary('alt wisp', 'ALTWISP')
        self.storage.upsert_snippet('sign off', 'Thanks, alt wisp')
        self.assertEqual(processor.process_text('sign off'), 'Thanks, ALTWISP')
        patterns = processor._patterns
        self.assertEqual(processor.process_text('ALT WISP'), 'ALTWISP')
        self.assertIs(processor._patterns, patterns)
        self.storage.upsert_dictionary('alt wisp', 'New name')
        self.assertEqual(processor.process_text('sign off'), 'Thanks, New name')
        self.storage.delete_entry('snippets', self.storage.list_entries('snippets')[0]['id'])
        self.assertEqual(processor.process_text('sign off'), 'sign off')

    def test_concurrent_reads_and_writes_do_not_leave_stale_cache(self):
        errors = []
        def read():
            try:
                for _ in range(25): self.storage.stats()
            except Exception as error: errors.append(error)
        thread = threading.Thread(target=read)
        thread.start()
        for _ in range(10): self.storage.add_history('one', 'one', 1)
        thread.join()
        self.assertEqual(errors, [])
        self.assertEqual(self.storage.stats()['dictations'], 10)


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.storage = Storage(root / 'test.db')
        self.settings = SettingsStore(root / 'settings.json')
        with patch('agent.SettingsStore', return_value=self.settings), patch('agent.Storage', return_value=self.storage), patch('agent.AudioManager'), patch('agent.Typer'):
            self.agent = Agent()
        self.agent.audio.input_device = None
        self.agent.emit = Mock()
        self.addCleanup(self.agent.close)

    def test_unrelated_settings_preserve_transcriber_and_polish_client(self):
        transcriber, processor = self.agent.transcriber, self.agent.processor
        client = object()
        processor._client = client
        self.agent.command('saveSettings', {'style': 'formal', 'max_recording_seconds': 45})
        self.assertIs(self.agent.transcriber, transcriber)
        self.assertIs(self.agent.processor, processor)
        self.assertIs(processor._client, client)
        self.assertEqual(processor.style, 'formal')
        self.assertEqual(self.agent.audio.max_seconds, 45)
        self.agent.command('saveSettings', {'local_model': 'tiny'})
        self.assertIs(self.agent.transcriber, transcriber, 'An unused local model choice should not recreate the cloud client')

    def test_settings_cannot_change_during_recording_or_accept_invalid_values(self):
        self.agent.state = 'processing'
        with self.assertRaises(RuntimeError): self.agent.command('saveSettings', {'input_device': 1})
        self.agent.state = 'idle'
        for payload in ({'input_device': True}, {'transcription_backend': 'invalid'}, {'save_history': 'false'}, {'max_recording_seconds': 0}):
            with self.assertRaises(ValueError): self.agent.command('saveSettings', payload)
        self.assertFalse(self.settings.path.exists())

    def test_microphone_test_excludes_hotkey_recording_and_recovers_after_failure(self):
        def wait():
            self.assertEqual(self.agent.state, 'testing')
            self.assertFalse(self.agent.start())
        with patch('sounddevice.query_devices', return_value={'name': 'Fixture'}), patch('sounddevice.rec', return_value=np.ones((100, 1))), patch('sounddevice.wait', side_effect=wait):
            self.agent.command('testMicrophone', {})
        self.assertEqual(self.agent.state, 'idle')
        with patch('sounddevice.query_devices', side_effect=RuntimeError('No input')):
            with self.assertRaises(RuntimeError): self.agent.command('testMicrophone', {})
        self.assertEqual(self.agent.state, 'idle')

    def test_failed_paste_preserves_result_without_retranscribing_or_duplicate_history(self):
        path = Path(self.temp.name) / 'audio.wav'
        path.write_bytes(b'fixture')
        self.agent.audio.stop_recording.return_value = (str(path), 2)
        self.agent.audio.peak_rms = 100
        self.agent.transcriber = Mock()
        self.agent.transcriber.transcribe.return_value = 'Synthetic dictation'
        self.agent.processor = Mock()
        self.agent.processor.process_text.return_value = 'Synthetic dictation.'
        self.agent.typer.inject_text.side_effect = RuntimeError('Clipboard locked')
        self.agent._finish()
        result = next(call.kwargs for call in self.agent.emit.call_args_list if call.kwargs.get('type') == 'result')
        self.assertFalse(result['pasted'])
        self.assertEqual(result['text'], 'Synthetic dictation.')
        self.assertEqual(self.storage.stats()['dictations'], 1)
        self.assertIsNone(self.agent.pending)
        self.assertFalse(path.exists())

    def test_retry_rejects_busy_and_missing_recording(self):
        self.agent.state = 'listening'
        with self.assertRaises(RuntimeError): self.agent.command('retry', {})
        self.agent.state = 'idle'
        with self.assertRaises(RuntimeError): self.agent.command('retry', {})

    def test_shutdown_during_transcription_does_not_paste_or_retain_audio(self):
        path = Path(self.temp.name) / 'audio.wav'
        path.write_bytes(b'fixture')
        self.agent.audio.stop_recording.return_value = (str(path), 2)
        self.agent.audio.peak_rms = 100
        self.agent.transcriber = Mock()
        def transcribe(_):
            self.agent.close()
            return 'Synthetic words'
        self.agent.transcriber.transcribe.side_effect = transcribe
        self.agent._finish()
        self.agent.typer.inject_text.assert_not_called()
        self.assertEqual(self.storage.stats()['dictations'], 0)
        self.assertFalse(path.exists())

    def test_invalid_saved_settings_fall_back_to_valid_defaults(self):
        self.settings.path.write_text('{"input_device": true}', encoding='utf-8')
        self.assertEqual(self.settings.load(), Settings())
        with self.assertRaises(ValueError): validate_settings(replace(Settings(), local_model='bad'))

    def test_cloud_polish_uses_supported_model_without_reasoning_in_transcript(self):
        processor = TextProcessor(self.storage)
        client = Mock()
        client.chat.completions.create.return_value.choices = [Mock(message=Mock(content='Synthetic text.'))]
        processor._client = client
        self.assertEqual(processor.process_text('synthetic text'), 'Synthetic text.')
        request = client.chat.completions.create.call_args.kwargs
        self.assertEqual(request['model'], 'openai/gpt-oss-120b')
        self.assertEqual(request['reasoning_effort'], 'low')
        self.assertFalse(request['include_reasoning'])
        self.assertIn('<raw_speech>', request['messages'][1]['content'])

    def test_polish_failure_preserves_text_without_polluting_worker_stdout(self):
        processor = TextProcessor(self.storage)
        processor._client = Mock()
        processor._client.chat.completions.create.side_effect = RuntimeError('fixture error')
        output = io.StringIO()
        with redirect_stdout(output), self.assertLogs(level='WARNING'):
            self.assertEqual(processor.process_text('Synthetic words'), 'Synthetic words')
        self.assertEqual(output.getvalue(), '')

    def test_local_model_is_reused_and_language_auto_maps_to_none(self):
        path = Path(self.temp.name) / 'fixture.wav'
        path.write_bytes(b'x' * 100)
        transcriber = Transcriber('local', 'tiny')
        transcriber._local = Mock()
        transcriber._local.transcribe.return_value = ([Mock(text=' Synthetic text ')], None)
        self.assertEqual(transcriber.transcribe(str(path)), 'Synthetic text')
        self.assertIsNone(transcriber._local.transcribe.call_args.kwargs['language'])
        self.assertTrue(transcriber._local.transcribe.call_args.kwargs['vad_filter'])
        transcriber.language = 'en'
        transcriber.transcribe(str(path))
        self.assertEqual(transcriber._local.transcribe.call_args.kwargs['language'], 'en')

    def test_native_paste_restores_clipboard_and_rechecks_target(self):
        with patch('typer.foreground_window', return_value=42), patch('typer.pyperclip.paste', side_effect=['original', 'Synthetic text']), patch('typer.pyperclip.copy') as copy, patch('typer.pyautogui.hotkey') as hotkey, patch('typer.time.sleep'):
            self.assertTrue(Typer.inject_text('Synthetic text', 42))
            self.assertEqual([call.args[0] for call in copy.call_args_list], ['Synthetic text', 'original'])
            hotkey.assert_called_once_with('ctrl', 'v')
        with patch('typer.foreground_window', side_effect=[42, 43]), patch('typer.pyperclip.paste', side_effect=['original', 'Synthetic text']), patch('typer.pyperclip.copy') as copy, patch('typer.pyautogui.hotkey') as hotkey, patch('typer.time.sleep'):
            self.assertFalse(Typer.inject_text('Synthetic text', 42))
            hotkey.assert_not_called()
            self.assertEqual(copy.call_args.args[0], 'original')


if __name__ == '__main__':
    unittest.main()
