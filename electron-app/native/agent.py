"""Headless Windows dictation worker for the Electron shell."""
import json, logging, os, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from pathlib import Path
import keyboard
from dotenv import load_dotenv
from audio_manager import AudioManager
from cloud import describe_error
from config import SettingsStore, app_data_dir, application_dir
from llm_processor import TextProcessor
from storage import Storage
from transcriber import Transcriber
from typer import Typer
from hotkey import WindowsHotkeyConnection

_env_files = [app_data_dir() / '.env']
if getattr(sys, 'frozen', False):
    _env_files.append(application_dir() / '.env')
else:
    _env_files.extend([
        Path(__file__).resolve().parents[1] / '.env',
        Path(__file__).resolve().parents[2] / '.env',
    ])
# AppData is the canonical user location; development project files remain
# supported for local testing without ever being bundled into a release.
for _env_file in _env_files:
    load_dotenv(_env_file)
logging.basicConfig(stream=sys.stderr,level=logging.WARNING)

class Agent:
    def __init__(self):
        self.lock=threading.RLock(); self.settings_store=SettingsStore(); self.settings=self.settings_store.load(); self.storage=Storage(); self.audio=AudioManager(max_seconds=self.settings.max_recording_seconds); self.typer=Typer(); self.state='idle'; self.target=None; self.pending=None; self.closed=False; self.worker=ThreadPoolExecutor(max_workers=1,thread_name_prefix='dictation'); self.configure(); self.audio.on_volume_change=self.volume; self.audio.on_max_duration=self.stop
    def emit(self,**message):
        with self.lock: sys.stdout.write(json.dumps(message,ensure_ascii=True)+'\n'); sys.stdout.flush()
    def configure(self):
        self.transcriber=Transcriber(self.settings.transcription_backend,self.settings.local_model,self.settings.language); self.processor=TextProcessor(self.storage,self.settings.polish_enabled and self.settings.transcription_backend=='groq',self.settings.style)
    def volume(self,value): self.emit(type='volume',value=min(1,max(0,(float(value)-45)/2200)))
    def set_state(self,value,message=''):
        with self.lock:
            if self.closed:return
            self.state=value
        self.emit(type='state',value=value,message=message)
    def toggle(self):
        with self.lock:
            state=self.state
        if state in {'starting','listening'}: self.stop()
        elif state=='idle': self.start()
    def start(self):
        with self.lock:
            if self.closed or self.state!='idle':return False
            try:self.target=self.typer.foreground_window()
            except Exception as exc:
                self.emit(type='error',title='Could not identify target window',message=describe_error(exc)); return False
            self.state='starting'
        self.emit(type='state',value='starting',message='Opening microphone…'); self.worker.submit(self._start); return True
    def _start(self):
        try:
            self.audio.start_recording()
            if self.state=='starting':self.set_state('listening','Listening')
            else:self.audio.recording=False
        except Exception as exc:self.audio.recording=False;self.set_state('idle','Microphone unavailable');self.emit(type='error',title='Microphone unavailable',message=describe_error(exc))
    def stop(self):
        with self.lock:
            if self.closed or self.state not in {'starting','listening'}:return False
            self.audio.recording=False; self.state='processing'
        self.emit(type='state',value='processing',message='Transcribing…'); self.worker.submit(self._finish); return True
    def _finish(self):
        path=None
        try:
            path,duration=self.audio.stop_recording()
            if not path:self.set_state('idle','No audio captured');return
            raw=self.transcriber.transcribe(path)
            if not raw:self.set_state('idle','No speech recognized');return
            text=self.processor.process_text(raw) or raw
            if self.settings.save_history:self.storage.add_history(raw,text,duration)
            pasted=self.typer.inject_text(text,target_window=self.target)
            self.emit(type='result',text=text,pasted=bool(pasted)); self.set_state('idle','Text inserted' if pasted else 'Text ready in dashboard')
        except Exception as exc:
            self.pending=(path,duration if 'duration' in locals() else 0) if path else None; self.set_state('idle','Dictation failed'); self.emit(type='error',title='Dictation failed',message=describe_error(exc),retry=bool(path))
        finally:
            if path and (not self.pending or self.pending[0]!=path):
                try:os.remove(path)
                except OSError:pass
    def snapshot(self):
        return {'settings':asdict(self.settings),'stats':self.storage.stats(),'history':self.storage.recent_history(80),'dictionary':self.storage.list_entries('dictionary'),'snippets':self.storage.list_entries('snippets')}
    def command(self,name,payload):
        if name=='toggle':self.toggle();return {'state':self.state}
        if name=='snapshot':return self.snapshot()
        if name=='saveSettings':
            allowed={k:v for k,v in payload.items() if hasattr(self.settings,k)}; self.settings=replace(self.settings,**allowed); self.settings_store.save(self.settings); self.configure(); return self.snapshot()
        if name=='upsertDictionary':self.storage.upsert_dictionary(payload['spoken'],payload['replacement']);return self.snapshot()
        if name=='upsertSnippet':self.storage.upsert_snippet(payload['trigger'],payload['expansion']);return self.snapshot()
        if name=='deleteEntry':self.storage.delete_entry(payload['table'],int(payload['id']));return self.snapshot()
        if name=='clearHistory':self.storage.delete_history();return self.snapshot()
        if name=='retry' and self.pending:
            path,duration=self.pending;self.pending=None;self.set_state('processing','Retrying…');self.worker.submit(self._retry,path,duration);return {'state':self.state}
        return {'state':self.state}
    def _retry(self,path,duration):
        try:
            raw=self.transcriber.transcribe(path)
            if not raw:
                self.set_state('idle','No speech recognized')
                try:os.remove(path)
                except OSError:pass
                return
            text=self.processor.process_text(raw) or raw
            if self.settings.save_history:self.storage.add_history(raw,text,duration)
            self.emit(type='result',text=text,pasted=False);self.set_state('idle','Text ready in dashboard')
        except Exception as exc:self.pending=(path,duration);self.set_state('idle','Retry failed');self.emit(type='error',title='Retry failed',message=describe_error(exc),retry=True);return
        try:os.remove(path)
        except OSError:pass
    def close(self):
        with self.lock:
            if self.closed:return
            self.closed=True; self.state='closed'
        self.audio.recording=False;self.audio.close();self.worker.shutdown(wait=False)

agent=Agent()
hotkey=WindowsHotkeyConnection(keyboard,agent.toggle)
try:
    hotkey.start()
    agent.emit(type='hotkey',value='ready',message='Ctrl + Windows connected')
    agent.emit(type='state',value='idle',message='Ready when you are')
except Exception as exc:
    agent.emit(type='hotkey',value='error',message=describe_error(exc))
    agent.emit(type='state',value='idle',message='Hotkey unavailable; use the tray control')
for line in sys.stdin:
    try:
        msg=json.loads(line); name=msg.get('name','');
        if name=='quit':break
        data=agent.command(name,msg.get('payload') or {}); agent.emit(replyTo=msg.get('id'),ok=True,data=data)
    except Exception as exc:agent.emit(replyTo=msg.get('id') if 'msg' in locals() else None,ok=False,error=describe_error(exc))
hotkey.close()
agent.close()
