"""Exercise source or packaged worker IPC using a disposable local profile."""
import argparse
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--packaged', action='store_true')
    parser.add_argument('--microphone', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='altwisp-protocol-') as temporary:
        env = dict(os.environ, LOCALAPPDATA=temporary)
        command = [str(root / 'native/dist/altwisp-worker.exe')] if args.packaged else [sys.executable, str(root / 'native/agent.py')]
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, cwd=root)
        replies = queue.Queue()
        def read():
            for line in process.stdout:
                try: replies.put(json.loads(line))
                except ValueError: replies.put({'invalid_stdout': True})
        threading.Thread(target=read, daemon=True).start()
        request = 0
        def send(name, payload=None, expect_error=False):
            nonlocal request
            request += 1
            process.stdin.write(json.dumps({'id': request, 'name': name, 'payload': payload or {}}) + '\n')
            process.stdin.flush()
            while True:
                response = replies.get(timeout=15)
                assert not response.get('invalid_stdout'), 'Worker stdout must contain JSON only'
                if response.get('replyTo') == request:
                    assert response['ok'] != expect_error, response.get('error')
                    return response.get('data')
        try:
            assert send('snapshot')['state'] == 'idle'
            devices = send('listMicrophones')
            if args.microphone:
                reading = send('testMicrophone')
                assert reading['rms'] >= 0
            send('upsertDictionary', {'spoken': 'audit phrase', 'replacement': 'AUDIT'})
            send('upsertSnippet', {'trigger': 'audit end', 'expansion': 'Synthetic ending.'})
            snapshot = send('saveSettings', {'style': 'formal'})
            assert snapshot['settings']['style'] == 'formal'
            assert len(snapshot['dictionary']) == len(snapshot['snippets']) == 1
            send('saveSettings', {'save_history': 'invalid'}, expect_error=True)
            assert send('snapshot')['settings']['save_history'] is True
            send('deleteEntry', {'table': 'dictionary', 'id': snapshot['dictionary'][0]['id']})
            send('clearHistory')
            for malformed in ('{bad-json}', '[]'):
                process.stdin.write(malformed + '\n'); process.stdin.flush()
                assert send('snapshot')['state'] == 'idle'
            saved = json.loads((Path(temporary) / 'ALTWISP/settings.json').read_text())
            assert saved['style'] == 'formal'
            print(json.dumps({'worker': 'packaged' if args.packaged else 'source', 'protocol': 'passed', 'input_devices': len(devices['devices']), 'microphone_test': 'passed' if args.microphone else 'not requested'}))
        finally:
            try:
                process.stdin.write('{"name":"quit"}\n'); process.stdin.flush()
                process.communicate(timeout=8)
            except Exception:
                process.kill(); process.communicate(); raise
        assert process.returncode == 0, 'Worker failed to quit cleanly'


if __name__ == '__main__':
    main()
