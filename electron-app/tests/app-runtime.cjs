// Smoke the real Electron main process, preload and Python worker in a disposable profile.
const { app, BrowserWindow } = require('electron');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const assert = require('node:assert/strict');
const childProcess = require('node:child_process');
let nativeWorker;
childProcess.spawn = (...args) => {
  const child = spawn(...args);
  if (args[1]?.some(value => value.endsWith('agent.py'))) nativeWorker = child;
  return child;
};
const output = fs.mkdtempSync(path.join(os.tmpdir(), 'altwisp-app-'));
app.setPath('userData', path.join(output, 'electron'));
process.env.LOCALAPPDATA = path.join(output, 'profile');
process.argv.push('--background');
require('../electron/main.js');

function python(code, args = []) {
  return new Promise((resolve, reject) => {
    const child = spawn(path.join(__dirname, '../.venv-worker/Scripts/python.exe'), ['-c', code, ...args], { windowsHide: true, cwd: path.join(__dirname, '..'), env: process.env });
    let stdout = '', stderr = '';
    child.stdout.on('data', data => stdout += data);
    child.stderr.on('data', data => stderr += data);
    child.on('error', reject);
    child.on('exit', code => code === 0 ? resolve(stdout.trim()) : reject(new Error(stderr)));
  });
}

app.whenReady().then(async () => {
  await new Promise(resolve => setTimeout(resolve, 1500));
  const dashboard = BrowserWindow.getAllWindows().find(win => win.getTitle() === 'ALTWISP');
  assert.ok(dashboard);
  const run = code => dashboard.webContents.executeJavaScript(code);
  const command = (name, payload = {}) => run(`window.altwisp.command(${JSON.stringify(name)},${JSON.stringify(payload)})`);
  const snapshot = await command('snapshot');
  assert.equal(snapshot.state, 'idle');
  assert.equal(snapshot.stats.dictations, 0);
  await command('upsertDictionary', { spoken: 'audit phrase', replacement: 'AUDIT' });
  await command('upsertSnippet', { trigger: 'audit end', expansion: 'Synthetic ending.' });
  const saved = await command('saveSettings', { style: 'formal' });
  assert.equal(saved.settings.style, 'formal');
  assert.equal(saved.dictionary.length, 1);
  assert.equal(saved.snippets.length, 1);
  assert.ok(nativeWorker);
  const previousWorker = nativeWorker;
  previousWorker.kill();
  await new Promise(resolve => previousWorker.once('exit', resolve));
  await new Promise(resolve => setTimeout(resolve, 200));
  assert.equal(await run(`document.querySelector('#status b').textContent`), 'Unavailable');
  await new Promise(resolve => setTimeout(resolve, 1600));
  assert.notEqual(nativeWorker, previousWorker);
  const recovered = await command('snapshot');
  assert.equal(recovered.settings.style, 'formal');
  assert.equal(recovered.dictionary.length, 1);
  assert.equal(recovered.state, 'idle');
  dashboard.showInactive();
  await new Promise(resolve => setTimeout(resolve, 500));
  fs.writeFileSync(path.join(output, 'dashboard.png'), (await dashboard.webContents.capturePage()).toPNG());
  const target = new BrowserWindow({ width: 500, height: 200, show: false });
  await target.loadURL('data:text/html,<textarea id="target" autofocus style="width:90%;height:100px" aria-label="Synthetic paste target"></textarea>');
  target.show(); app.focus({ steal: true }); target.focus();
  await target.webContents.executeJavaScript('document.querySelector("textarea").focus()');
  await new Promise(resolve => setTimeout(resolve, 400));
  const handle = target.getNativeWindowHandle();
  const hwnd = handle.length === 8 ? handle.readBigUInt64LE().toString() : String(handle.readUInt32LE());
  const foreground = await python("import sys;sys.path.insert(0,'native');from windows import foreground_window;print(foreground_window())");
  console.log('PASTE_TARGET', JSON.stringify({ hwnd, foreground }));
  const pasted = await python("import sys;sys.path.insert(0,'native');from typer import Typer;import pyperclip;original=pyperclip.paste();result=Typer.inject_text('ALTWISP synthetic paste check.',int(sys.argv[1]));print(result,pyperclip.paste()==original)", [hwnd]);
  const nativePasteAvailable = foreground === hwnd;
  if (nativePasteAvailable) {
    assert.equal(pasted, 'True True', 'Paste failed or clipboard was not restored');
    assert.equal(await target.webContents.executeJavaScript('document.querySelector("textarea").value'), 'ALTWISP synthetic paste check.');
  } else {
    assert.equal(pasted, 'False True');
    assert.equal(await target.webContents.executeJavaScript('document.querySelector("textarea").value'), '');
    console.log('SKIP: Windows refused foreground activation of the synthetic target; successful native paste requires an interactive check');
  }
  // The same transcript must not be inserted after the recorded target loses focus.
  dashboard.show(); dashboard.focus();
  await new Promise(resolve => setTimeout(resolve, 300));
  assert.equal(await python("import sys;sys.path.insert(0,'native');from typer import Typer;print(Typer.inject_text('Must not paste',int(sys.argv[1])))", [hwnd]), 'False');
  target.destroy();
  console.log('PASS: real app startup, IPC, isolated storage, settings, dictionary/snippets, worker crash/restart, persisted settings and changed-target paste protection');
  console.log('APP_AUDIT', JSON.stringify({ output, processes: app.getAppMetrics().map(({ type, cpu, memory }) => ({ type, cpuPercent: cpu.percentCPUUsage, workingSetKB: memory.workingSetSize })) }));
  app.isQuitting = true; app.quit();
}).catch(error => { console.error(error); app.isQuitting = true; if(nativeWorker)nativeWorker.once('exit',()=>app.exit(1));app.quit();if(!nativeWorker)app.exit(1); });
