const { app, BrowserWindow, ipcMain, Tray, Menu, nativeImage, screen, shell } = require('electron');
const { spawn } = require('node:child_process');
const path = require('node:path');
const fs = require('node:fs');
const readline = require('node:readline');
const { positionOverlay: applyOverlayBounds } = require('./overlay-geometry');

let dashboard, overlay, tray, worker;
let overlayReady = false;
let latestAgentState = { value: 'idle', message: 'Ready when you are' };
let workerRestartAttempts = 0;
let workerRestartTimer;
let nextRequest = 1;
const pending = new Map();
const LOGIN_ARGS = ['--background'];

function page(name) { return path.join(__dirname, '..', 'renderer', name); }
function positionOverlay() {
  if (!overlay || overlay.isDestroyed()) return;
  applyOverlayBounds(overlay, screen.getPrimaryDisplay());
}
function syncOverlay() {
  if (!overlayReady || !overlay || overlay.isDestroyed()) return;
  positionOverlay();
  if (latestAgentState.value === 'starting' || latestAgentState.value === 'listening') overlay.showInactive();
  else overlay.hide();
}
function createWindows() {
  dashboard = new BrowserWindow({
    width: 1180, height: 800, minWidth: 980, minHeight: 680, show: false,
    backgroundColor: '#f5f7fb', titleBarStyle: 'hidden',
    webPreferences: { preload: path.join(__dirname, 'preload.js'), contextIsolation: true, nodeIntegration: false }
  });
  dashboard.loadFile(page('index.html'));
  dashboard.on('close', e => { if (!app.isQuitting) { e.preventDefault(); dashboard.hide(); } });

  overlay = new BrowserWindow({
    width: 58, height: 58, frame: false, transparent: true, backgroundColor: '#00000000',
    thickFrame: false, roundedCorners: false, resizable: false,
    show: false, skipTaskbar: true, focusable: false, alwaysOnTop: true,
    hasShadow: false, webPreferences: { preload: path.join(__dirname, 'preload.js'), contextIsolation: true }
  });
  overlay.setAlwaysOnTop(true, 'screen-saver');
  overlay.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
  overlay.setBackgroundColor('#00000000');
  overlay.setIgnoreMouseEvents(true);
  overlay.setTitle('ALTWISP Recorder');
  positionOverlay();
  // A hidden transparent window may never emit ready-to-show during sign-in startup.
  // The page load is the readiness signal; replay the latest worker state so an
  // activation that happened during startup also starts the orb animation.
  overlay.webContents.on('did-start-loading', () => { overlayReady = false; });
  overlay.webContents.on('did-finish-load', () => {
    overlayReady = true;
    syncOverlay();
    overlay.webContents.send('agent-event', { type: 'state', ...latestAgentState });
  });
  overlay.webContents.on('did-fail-load', (_, code, description, url, isMainFrame) => {
    if (isMainFrame) console.error(`Recorder overlay failed to load (${code}): ${description} ${url}`);
  });
  overlay.on('closed', () => { overlayReady = false; overlay = null; });
  if (!process.argv.includes('--background')) dashboard.once('ready-to-show', () => dashboard.show());
  overlay.loadFile(page('overlay.html'));
}

function workerCommand(name, payload = {}) {
  return new Promise((resolve, reject) => {
    if (!worker?.stdin.writable) return reject(new Error('Native worker is unavailable'));
    const id = nextRequest++;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error('Worker did not respond')); }, 6000);
    pending.set(id, { resolve, reject, timer });
    worker.stdin.write(JSON.stringify({ id, name, payload }) + '\n');
  });
}
function broadcast(event) {
  if (event.type === 'state') latestAgentState = { value: event.value, message: event.message || '' };
  dashboard?.webContents.send('agent-event', event);
  if (event.type === 'state') syncOverlay();
  if (overlayReady) overlay?.webContents.send('agent-event', event);
}
function startWorker() {
  const sourcePython = [
    path.join(__dirname, '..', '.venv-worker', 'Scripts', 'python.exe')
  ].find(fs.existsSync);
  const executable = app.isPackaged ? path.join(process.resourcesPath, 'native', 'altwisp-worker.exe') : sourcePython;
  if (!executable) {
    broadcast({ type: 'error', title: 'Background worker unavailable', message: 'Run npm run build:worker once to prepare the native hotkey and microphone worker.' });
    return;
  }
  const args = app.isPackaged ? [] : [path.join(__dirname, '..', 'native', 'agent.py')];
  const workerCwd = app.isPackaged ? process.resourcesPath : path.join(__dirname, '..');
  worker = spawn(executable, args, { cwd: workerCwd, windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'] });
  const currentWorker = worker;
  worker.on('error', error => {
    console.error('Native worker failed to start:', error);
    broadcast({ type: 'error', title: 'Background worker unavailable', message: error.message });
  });
  readline.createInterface({ input: worker.stdout }).on('line', line => {
    try {
      const msg = JSON.parse(line);
      if (msg.type === 'hotkey' && msg.value === 'ready') workerRestartAttempts = 0;
      if (msg.replyTo && pending.has(msg.replyTo)) { const p = pending.get(msg.replyTo); clearTimeout(p.timer); pending.delete(msg.replyTo); msg.ok ? p.resolve(msg.data) : p.reject(new Error(msg.error)); }
      else broadcast(msg);
    } catch { /* diagnostics remain on stderr */ }
  });
  worker.stderr.on('data', data => console.error(String(data).trim()));
  worker.on('exit', code => {
    if (worker !== currentWorker) return;
    worker = null;
    for (const [id, request] of pending) { clearTimeout(request.timer); request.reject(new Error('Background worker stopped')); pending.delete(id); }
    if (app.isQuitting) return;
    if (workerRestartAttempts < 5) {
      workerRestartAttempts += 1;
      workerRestartTimer = setTimeout(() => { workerRestartTimer = undefined; startWorker(); }, Math.min(1000 * workerRestartAttempts, 5000));
      broadcast({ type: 'error', title: 'Background worker restarted', message: `Worker stopped (exit ${code}); retrying automatically.` });
    } else {
      broadcast({ type: 'error', title: 'Background worker stopped', message: `Exit code ${code}. Restart ALTWISP to try again.` });
    }
  });
}
function createTray() {
  const iconPath = app.isPackaged
    ? path.join(process.resourcesPath, 'assets', 'tray.png')
    : path.join(__dirname, '..', 'assets', 'tray.png');
  tray = new Tray(nativeImage.createFromPath(iconPath).resize({width: 20, height: 20}));
  tray.setToolTip('ALTWISP — Ready');
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: 'Open dashboard', click: () => { dashboard.show(); dashboard.focus(); } },
    { label: 'Start / stop dictation', click: () => workerCommand('toggle').catch(() => {}) },
    { type: 'separator' }, { label: 'Quit ALTWISP', click: () => { app.isQuitting = true; app.quit(); } }
  ]));
  tray.on('click', () => { dashboard.show(); dashboard.focus(); });
  tray.on('double-click', () => { dashboard.show(); dashboard.focus(); });
}

if (!app.requestSingleInstanceLock()) app.quit();
else app.whenReady().then(() => {
  createWindows();
  screen.on('display-metrics-changed', positionOverlay);
  screen.on('display-added', positionOverlay);
  screen.on('display-removed', positionOverlay);
  startWorker();
  createTray();
});
app.on('second-instance', () => { dashboard?.show(); dashboard?.focus(); });
app.on('before-quit', () => { app.isQuitting = true; if (workerRestartTimer) clearTimeout(workerRestartTimer); try { worker?.stdin.write(JSON.stringify({name:'quit'})+'\n'); } catch {} });
app.on('window-all-closed', () => {});
ipcMain.handle('agent-command', async (_, {name,payload}) => {
  if (name === 'openReleases') return shell.openExternal('https://github.com/OREWA-PRANESH/ALTWISP/releases/latest');
  if (name === 'checkForUpdates') {
    const response = await fetch('https://api.github.com/repos/OREWA-PRANESH/ALTWISP/releases/latest', {
      headers: { 'Accept': 'application/vnd.github+json', 'User-Agent': 'ALTWISP' },
      signal: AbortSignal.timeout(8000)
    });
    if (!response.ok) throw new Error(response.status === 404 ? 'Release information is private. Open the release page with an authorized GitHub account.' : `GitHub returned HTTP ${response.status}`);
    const release = await response.json();
    const latest = String(release.tag_name || '').replace(/^v/, '');
    if (!/^\d+\.\d+\.\d+$/.test(latest)) throw new Error('The latest release has no valid version tag');
    const current = app.getVersion();
    const toParts = version => version.split('.').map(Number);
    const a = toParts(latest), b = toParts(current);
    return { latest, current, available: a.some((part, index) => part > b[index] && a.slice(0, index).every((earlier, i) => earlier === b[i])) };
  }
  const data = await workerCommand(name,payload);
  if (name === 'saveSettings') {
    app.setLoginItemSettings({ openAtLogin: !!payload.launch_at_login, args: LOGIN_ARGS });
  }
  return data;
});
ipcMain.on('window-action', (_, action) => { if(action==='minimize') dashboard.minimize(); if(action==='maximize') dashboard.isMaximized() ? dashboard.unmaximize() : dashboard.maximize(); if(action==='close') dashboard.hide(); if(action==='quit'){app.isQuitting=true;app.quit();} });
