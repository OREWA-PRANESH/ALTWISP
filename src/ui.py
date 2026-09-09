"""Complete PySide6 dashboard for ALTWISP."""
import os, queue
from datetime import datetime
from pathlib import Path
_qt=Path(__file__).resolve().parent.parent/'venv'/'Lib'/'site-packages'/'PySide6'; _dll=[]
for _d in (_qt,_qt.parent/'shiboken6'):
    if _d.exists() and hasattr(os,'add_dll_directory'): _dll.append(os.add_dll_directory(str(_d)))
from PySide6.QtCore import Qt,QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication,QCheckBox,QComboBox,QFileDialog,QFrame,QGridLayout,QHBoxLayout,QHeaderView,QLabel,QLineEdit,QMainWindow,QMessageBox,QPushButton,QScrollArea,QStackedWidget,QTableWidget,QTableWidgetItem,QTextEdit,QVBoxLayout,QWidget
from qt_orb import OrbOverlay

BG='#F4F6FA'; INK='#142033'; MUTED='#6C788A'; BLUE='#4C6FFF'; NAVY='#111C2B'; BORDER='#E2E7F0'

def label(text,size=12,color=INK,weight=QFont.Weight.Normal):
    w=QLabel(text); w.setFont(QFont('Segoe UI',size,weight)); w.setStyleSheet(f'color:{color};background:transparent'); return w
def btn(text,kind='secondary'):
    b=QPushButton(text); b.setCursor(Qt.CursorShape.PointingHandCursor); b.setProperty('kind',kind); return b
def card():
    c=QFrame(); c.setObjectName('card'); return c
def field():
    x=QLineEdit(); x.setMinimumHeight(42); return x

STYLE='''QMainWindow,QWidget#app{background:#F4F6FA;font-family:"Segoe UI"} QFrame#side{background:#111C2B} QFrame#card{background:white;border:1px solid #E2E7F0;border-radius:14px} QLabel{color:#142033} QPushButton{border:0;border-radius:9px;padding:11px 15px;font:600 12px "Segoe UI"} QPushButton[kind="primary"]{background:#4C6FFF;color:white} QPushButton[kind="primary"]:hover{background:#3E5AE2} QPushButton[kind="secondary"]{background:#EEF1F7;color:#142033} QPushButton[kind="secondary"]:hover{background:#E3E8F2} QPushButton[kind="nav"]{background:transparent;color:#AAB7C7;text-align:left;padding:13px 15px} QPushButton[kind="nav"]:hover{background:#1B2A3D;color:white} QPushButton[kind="nav"][active="true"]{background:#263853;color:white} QLineEdit,QTextEdit,QComboBox{background:white;border:1px solid #DCE2EC;border-radius:9px;padding:9px;color:#142033;selection-background-color:#4C6FFF} QLineEdit:focus,QTextEdit:focus,QComboBox:focus{border:1px solid #4C6FFF} QTableWidget{background:white;border:0;gridline-color:#EDF0F5;color:#142033;selection-background-color:#E8EDFF;selection-color:#142033} QHeaderView::section{background:#F7F8FB;color:#6C788A;border:0;border-bottom:1px solid #E2E7F0;padding:10px;font-weight:600} QScrollArea{border:0;background:transparent} QCheckBox{spacing:9px;color:#142033}'''

class Dashboard(QMainWindow):
    def __init__(self,ui):
        super().__init__(); self.ui=ui; self.setWindowTitle('ALTWISP · Your voice, in flow'); self.resize(1120,780); self.setMinimumSize(940,680); self.setStyleSheet(STYLE)
        root=QWidget(); root.setObjectName('app'); self.setCentralWidget(root); outer=QHBoxLayout(root); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)
        self.side=QFrame(); self.side.setObjectName('side'); self.side.setFixedWidth(220); sl=QVBoxLayout(self.side); sl.setContentsMargins(18,28,18,20); sl.setSpacing(5)
        brand=label('◉  ALTWISP',18,'#F7FAFF',QFont.Weight.Bold); sl.addWidget(brand); sl.addWidget(label('Voice that keeps up.',10,'#8495AA')); sl.addSpacing(28); self.nav={}
        for name,icon in [('Home','⌂'),('History','≡'),('Dictionary','Aa'),('Snippets','↗'),('Settings','⚙')]:
            b=btn(f'{icon}   {name}','nav'); b.clicked.connect(lambda checked=False,n=name:self.open_page(n)); sl.addWidget(b); self.nav[name]=b
        sl.addStretch(); sl.addWidget(label('Ctrl + Windows',10,'#8292A7',QFont.Weight.Bold)); sl.addWidget(label('Start · stop dictation',9,'#66778C')); sl.addSpacing(16); quitb=btn('Quit ALTWISP','nav'); quitb.clicked.connect(ui.callbacks.get('quit',lambda:None)); sl.addWidget(quitb); outer.addWidget(self.side)
        body=QWidget(); body_l=QVBoxLayout(body); body_l.setContentsMargins(34,27,34,22); body_l.setSpacing(14); top=QHBoxLayout(); self.breadcrumb=label('Workspace  /  Home',10,MUTED); top.addWidget(self.breadcrumb); top.addStretch(); self.status=label('●  Ready when you are',10,'#277A61',QFont.Weight.DemiBold); self.status.setStyleSheet('color:#277A61;background:#E7F5EF;border-radius:8px;padding:8px 12px'); top.addWidget(self.status); body_l.addLayout(top)
        self.error=QFrame(); self.error.setObjectName('error'); self.error.setStyleSheet('QFrame#error{background:#FFF1E8;border:1px solid #FFD5BB;border-radius:10px}'); er=QHBoxLayout(self.error); self.error_text=label('',10,'#884515'); er.addWidget(self.error_text,1); retry=btn('Retry','secondary'); retry.clicked.connect(ui.callbacks.get('retry',lambda:None)); er.addWidget(retry); discard=btn('Discard','secondary'); discard.clicked.connect(ui.callbacks.get('discard',lambda:None)); er.addWidget(discard); close=btn('×','secondary'); close.clicked.connect(self.error.hide); er.addWidget(close); self.error.hide(); body_l.addWidget(self.error)
        self.stack=QStackedWidget(); body_l.addWidget(self.stack,1); outer.addWidget(body,1); self.pages={}; self.builders={'Home':self.home,'History':self.history,'Dictionary':lambda:self.entries('dictionary'),'Snippets':lambda:self.entries('snippets'),'Settings':self.settings_page}; self.open_page('Home')
    def closeEvent(self,event): event.ignore(); self.hide()
    def open_page(self,name):
        if name not in self.pages: self.pages[name]=self.builders[name](); self.stack.addWidget(self.pages[name])
        self.stack.setCurrentWidget(self.pages[name]); self.ui.current_page=name; self.breadcrumb.setText(f'Workspace  /  {name}')
        for n,b in self.nav.items(): b.setProperty('active','true' if n==name else 'false'); b.style().unpolish(b); b.style().polish(b)
        if hasattr(self.ui,'root'): self.ui.refresh()
    def page_shell(self,title,subtitle):
        w=QWidget(); l=QVBoxLayout(w); l.setContentsMargins(0,0,0,0); l.setSpacing(14); l.addWidget(label(title,26,INK,QFont.Weight.Bold)); l.addWidget(label(subtitle,11,MUTED)); return w,l
    def home(self):
        w,l=self.page_shell('Less typing. More you.','A calm command center for every thought you speak.'); hero=card(); h=QHBoxLayout(hero); h.setContentsMargins(26,22,24,22); left=QVBoxLayout(); left.addWidget(label('YOUR VOICE · ANY TEXT BOX',9,'#526AA0',QFont.Weight.Bold)); left.addWidget(label('Say it. Let it flow.',22,'#243B78',QFont.Weight.Bold)); left.addWidget(label('Select a text box and release  Ctrl + Windows\nRepeat the same gesture to finish.',11,'#60729B')); h.addLayout(left,1); from qt_orb import ReactiveOrb; self.hero_orb=ReactiveOrb(82); h.addWidget(self.hero_orb); l.addWidget(hero)
        metrics=QHBoxLayout(); self.metric_values={};
        for key,title in [('words','WORDS DICTATED'),('dictations','RECORDINGS'),('wpm','WORDS / MIN')]:
            c=card(); x=QVBoxLayout(c); x.setContentsMargins(20,16,20,16); x.addWidget(label(title,9,MUTED,QFont.Weight.DemiBold)); v=label('—',22,INK,QFont.Weight.Bold); x.addWidget(v); self.metric_values[key]=v; metrics.addWidget(c)
        l.addLayout(metrics); latest=card(); ll=QVBoxLayout(latest); head=QHBoxLayout(); head.addWidget(label('Your latest words',12,INK,QFont.Weight.DemiBold)); head.addStretch(); copy=btn('Copy text','secondary'); copy.clicked.connect(self.copy_latest); head.addWidget(copy); ll.addLayout(head); self.latest=QTextEdit(); self.latest.setMinimumHeight(145); ll.addWidget(self.latest); l.addWidget(latest,1); return w
    def history(self):
        w,l=self.page_shell('History','Everything you dictated, kept useful and easy to find.'); bar=QHBoxLayout(); bar.addStretch(); export=btn('Export JSON','secondary'); export.clicked.connect(self.export_history); bar.addWidget(export); clear=btn('Clear history','secondary'); clear.clicked.connect(self.clear_history); bar.addWidget(clear); l.addLayout(bar); self.history_table=QTableWidget(0,3); self.history_table.setHorizontalHeaderLabels(['WHEN','TRANSCRIPT','WORDS']); self.history_table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.Stretch); self.history_table.verticalHeader().hide(); self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows); self.history_table.setAlternatingRowColors(True); l.addWidget(self.history_table,1); return w
    def entries(self,table):
        title='Dictionary' if table=='dictionary' else 'Snippets'; sub='Teach ALTWISP names, terms and replacements.' if table=='dictionary' else 'Expand short spoken triggers into complete reusable text.'; w,l=self.page_shell(title,sub); form=card(); fl=QGridLayout(form); fl.setContentsMargins(18,16,18,16); a=field(); b=QTextEdit(); b.setFixedHeight(74); fl.addWidget(label('Spoken phrase' if table=='dictionary' else 'Trigger',9,MUTED),0,0); fl.addWidget(label('Replacement' if table=='dictionary' else 'Expansion',9,MUTED),0,1); fl.addWidget(a,1,0); fl.addWidget(b,1,1); save=btn('Save','primary'); fl.addWidget(save,1,2); l.addWidget(form); tree=QTableWidget(0,3); tree.setHorizontalHeaderLabels(['PHRASE','RESULT','']); tree.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.Stretch); l.addWidget(tree,1); self.entry_controls[table]=(a,b,tree); save.clicked.connect(lambda:self.save_entry(table)); return w
    @property
    def entry_controls(self):
        if not hasattr(self,'_entry_controls'): self._entry_controls={}
        return self._entry_controls
    def settings_page(self):
        w,l=self.page_shell('Settings','Tune how ALTWISP listens, writes and lives on this computer.')
        engine=card(); g=QGridLayout(engine); g.setContentsMargins(22,18,22,20); g.setHorizontalSpacing(24); g.setVerticalSpacing(12)
        g.addWidget(label('Transcription',13,INK,QFont.Weight.DemiBold),0,0,1,2)
        self.backend=QComboBox(); self.backend.addItems(['groq','local']); self.backend.setCurrentText(self.ui.settings.transcription_backend)
        self.model=QComboBox(); self.model.addItems(['tiny','base','small','medium','large-v3']); self.model.setCurrentText(self.ui.settings.local_model)
        self.language=field(); self.language.setText(self.ui.settings.language)
        self.tone=QComboBox(); self.tone.addItems(['neutral','casual','formal','concise']); self.tone.setCurrentText(self.ui.settings.style)
        for row,(name,widget) in enumerate([('Engine',self.backend),('Local model',self.model),('Language',self.language),('Writing style',self.tone)],1):
            widget.setFixedHeight(42)
            g.addWidget(label(name,10,MUTED),row,0); g.addWidget(widget,row,1)
        engine.setFixedHeight(288)
        l.addWidget(engine)
        privacy=card(); pv=QVBoxLayout(privacy); pv.setContentsMargins(22,18,22,20); pv.setSpacing(12); pv.addWidget(label('Privacy & startup',13,INK,QFont.Weight.DemiBold))
        self.polish=QCheckBox('Polish transcription with AI'); self.polish.setChecked(self.ui.settings.polish_enabled)
        self.keep=QCheckBox('Save transcription history'); self.keep.setChecked(self.ui.settings.save_history)
        self.autostart=QCheckBox('Launch ALTWISP when I sign in'); self.autostart.setChecked(self.ui.settings.launch_at_login)
        pv.addWidget(self.polish); pv.addWidget(self.keep); pv.addWidget(self.autostart); privacy.setFixedHeight(164); l.addWidget(privacy)
        actions=QHBoxLayout(); actions.addWidget(label('Local mode keeps audio on this computer.',10,MUTED)); actions.addStretch(); save=btn('Save settings','primary'); save.clicked.connect(self.save_settings); actions.addWidget(save); l.addLayout(actions); l.addStretch(); return w
    def copy_latest(self): QApplication.clipboard().setText(self.latest.toPlainText()); self.status.setText('✓  Copied to clipboard')
    def export_history(self):
        path,_=QFileDialog.getSaveFileName(self,'Export history','altwisp-history.json','JSON (*.json)');
        if path:self.ui.storage.export_json(path)
    def clear_history(self):
        if QMessageBox.question(self,'Clear history','Permanently remove all saved transcripts?')==QMessageBox.StandardButton.Yes:self.ui.storage.delete_history(); self.ui.refresh()
    def save_entry(self,table):
        a,b,tree=self.entry_controls[table]; first=a.text().strip(); second=b.toPlainText().strip()
        if not first or not second:return
        (self.ui.storage.upsert_dictionary if table=='dictionary' else self.ui.storage.upsert_snippet)(first,second); a.clear(); b.clear(); self.ui.refresh()
    def delete_entry(self,table,entry_id): self.ui.storage.delete_entry(table,entry_id); self.ui.refresh()
    def save_settings(self):
        try:
            self.ui.callbacks['save_settings']({'backend':self.backend.currentText(),'model':self.model.currentText(),'language':self.language.text(),'style':self.tone.currentText(),'polish':self.polish.isChecked(),'history':self.keep.isChecked(),'retention':0,'autostart':self.autostart.isChecked()}); self.status.setText('✓  Settings saved')
        except Exception as exc:self.ui.show_error('Settings not saved',str(exc))

class AppUI:
    def __init__(self,storage,settings,callbacks):
        self.storage,self.settings,self.callbacks=storage,settings,callbacks; self.alive=True; self.current_page='Home'; self.queue=queue.SimpleQueue(); self.app=QApplication.instance() or QApplication([]); self.app.setQuitOnLastWindowClosed(False); self.root=Dashboard(self); self.overlay=OrbOverlay(64); self.native_overlay=self.overlay; self.orb=self.overlay.orb; self.pump=QTimer(); self.pump.timeout.connect(self._drain); self.pump.start(8); self.refresh()
    def enqueue(self,callback,*args): self.queue.put((callback,args))
    def _drain(self):
        for _ in range(32):
            try: callback,args=self.queue.get_nowait()
            except queue.Empty:return
            try:callback(*args)
            except Exception as exc:self.show_error('Interface error',str(exc))
    def run(self,background=False):
        if not background:self.show_dashboard()
        self.app.exec()
    def show_dashboard(self):self.root.show(); self.root.raise_(); self.root.activateWindow(); self.refresh()
    def hide_dashboard(self):self.root.hide()
    def show_recording(self):self.overlay.show_orb()
    def hide_recording(self):self.overlay.hide_orb()
    def update_waveform_from_volume(self,volume):self.orb.set_volume(volume)
    def set_overlay_status(self,text):pass
    def set_status(self,message,error=False):self.root.status.setText(('!  ' if error else '●  ')+message)
    def show_error(self,title,message):self.root.error_text.setText(f'{title}\n{message}'); self.root.error.show()
    def refresh_if_visible(self):
        if self.root.isVisible():self.refresh()
    def refresh(self):
        name=self.current_page
        if name=='Home' and hasattr(self.root,'metric_values'):
            s=self.storage.stats(); self.root.metric_values['words'].setText(f"{s['words']:,}"); self.root.metric_values['dictations'].setText(f"{s['dictations']:,}"); self.root.metric_values['wpm'].setText(str(round(s['words']*60/s['seconds'])) if s['seconds'] else '—'); rows=self.storage.recent_history(1); text=self.callbacks.get('last_text',lambda:'')() or (rows[0]['final_text'] if rows else ''); self.root.latest.setPlainText(text or 'Your next thought starts here.')
        elif name=='History' and hasattr(self.root,'history_table'):
            rows=self.storage.recent_history(); t=self.root.history_table; t.setRowCount(len(rows))
            for r,row in enumerate(rows):
                stamp=datetime.fromisoformat(row['created_at']).astimezone().strftime('%d %b · %H:%M'); vals=(stamp,row['final_text'],str(len(row['final_text'].split())))
                for c,value in enumerate(vals):
                    item=QTableWidgetItem(value); item.setForeground(Qt.GlobalColor.black); t.setItem(r,c,item)
        elif name.lower() in self.root.entry_controls:
            table=name.lower(); tree=self.root.entry_controls[table][2]; rows=self.storage.list_entries(table); tree.setRowCount(len(rows))
            for r,row in enumerate(rows):
                vals=(row['spoken'],row['replacement']) if table=='dictionary' else (row['trigger'],row['expansion'])
                tree.setItem(r,0,QTableWidgetItem(vals[0])); tree.setItem(r,1,QTableWidgetItem(vals[1])); delete=btn('Delete','secondary'); delete.clicked.connect(lambda checked=False,t=table,i=row['id']:self.root.delete_entry(t,i)); tree.setCellWidget(r,2,delete)
    def destroy(self):
        if not self.alive:return
        self.alive=False; self.pump.stop(); self.overlay.hide_orb(); self.root.close(); self.app.quit()
