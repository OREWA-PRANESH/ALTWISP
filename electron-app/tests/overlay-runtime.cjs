const { app, BrowserWindow, screen } = require('electron');
const path = require('node:path');
const assert = require('node:assert/strict');
const appDirArg = process.argv.find(arg => arg.startsWith('--app-dir='));
const appDir = appDirArg ? appDirArg.slice('--app-dir='.length) : path.join(__dirname, '..');
const { positionOverlay } = require(path.join(appDir, 'electron/overlay-geometry'));

app.whenReady().then(async () => {
  const display = screen.getPrimaryDisplay();
  console.log('DISPLAY', JSON.stringify(display));
  const win = new BrowserWindow({ width: 58, height: 58, frame: false,
    transparent: true, thickFrame: false, roundedCorners: false,
    resizable: false, show: false, skipTaskbar: true, focusable: false,
    alwaysOnTop: true, hasShadow: false,
    webPreferences: { preload: path.join(appDir, 'electron/preload.js'), contextIsolation: true } });
  await win.loadFile(path.join(appDir, 'renderer/overlay.html'));
  const samples = [];
  let firstOrb;
  for (let i = 0; i < 100; i++) {
    positionOverlay(win, display);
    win.showInactive();
    win.webContents.send('agent-event', { type: 'state', value: 'starting' });
    win.webContents.send('agent-event', { type: 'state', value: 'listening' });
    win.webContents.send('agent-event', { type: 'volume', value: i % 2 });
    await new Promise(resolve => setTimeout(resolve, 30));
    samples.push(win.getBounds());
    assert.deepEqual(samples[i], samples[0], `Geometry changed at activation ${i + 1}`);
    assert.ok(samples[i].y + samples[i].height <= display.workArea.y + display.workArea.height - 10);
    const orb = await win.webContents.executeJavaScript(`(() => {
      const rect = document.querySelector('.orb').getBoundingClientRect();
      return { width: rect.width, height: rect.height, zoom: window.devicePixelRatio };
    })()`);
    firstOrb ||= orb;
    assert.deepEqual(orb, firstOrb, `Rendered orb changed at activation ${i + 1}`);
    win.webContents.send('agent-event', { type: 'state', value: 'processing' });
    win.hide();
    win.webContents.send('agent-event', { type: 'state', value: 'idle' });
  }
  console.log('PASS: 100 activations, stable bounds', JSON.stringify(samples[0]), 'rendered orb', JSON.stringify(firstOrb));
  win.destroy();
  app.quit();
}).catch(error => { console.error(error); app.exit(1); });
