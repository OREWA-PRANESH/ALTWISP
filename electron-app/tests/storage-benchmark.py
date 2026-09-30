"""Compare bounded dashboard reads against a Git revision using synthetic data."""
import argparse
import importlib.util
import json
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / 'electron-app/native'))
from storage import Storage


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline-ref', default='bd0112a')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='altwisp-benchmark-') as temporary:
        folder = Path(temporary)
        legacy = folder / 'baseline_storage.py'
        legacy.write_bytes(subprocess.check_output(['git', 'show', f'{args.baseline_ref}:electron-app/native/storage.py'], cwd=root))
        spec = importlib.util.spec_from_file_location('baseline_storage', legacy)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        baseline = module.Storage(folder / 'synthetic.db')
        with baseline._connect() as database:
            database.executemany('INSERT INTO history(created_at,raw_text,final_text,duration_seconds,app_name) VALUES(?,?,?,?,?)', [('2026-09-30', 'synthetic', 'Synthetic audit words ' * 12, 6, 'audit')] * 5000)
        optimized = Storage(folder / 'synthetic.db')
        def snapshot(store):
            return (store.stats(), store.recent_history(80), store.list_entries('dictionary'), store.list_entries('snippets'))
        def measure(store):
            snapshot(store)
            samples = []
            for _ in range(40):
                start = time.perf_counter()
                snapshot(store)
                samples.append((time.perf_counter() - start) * 1000)
            return round(statistics.median(samples), 4)
        print(json.dumps({'rows': 5000, 'samples': 40, 'baseline_ref': args.baseline_ref, 'baseline_median_ms': measure(baseline), 'optimized_warm_median_ms': measure(optimized)}))


if __name__ == '__main__':
    main()
