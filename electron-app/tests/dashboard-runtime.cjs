const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('node:path');
const fs = require('node:fs');
const os = require('node:os');
const assert = require('node:assert/strict');

const output = fs.mkdtempSync(path.join(os.tmpdir(), 'altwisp-dashboard-'));
app.setPath('userData', path.join(output, 'profile'));
const snapshot = {
  settings: { transcription_backend: 'groq', local_model: 'small', language: 'auto', style: 'neutral', polish_enabled: true, save_history: true, launch_at_login: false, input_device: null },
  stats: { words: 12, dictations: 1, seconds: 6 }, state: 'idle', pendingRecording: false,
  history: [{ id: 1, created_at: '2026-09-30T09:00:00Z', final_text: 'Synthetic audit transcript. ' + 'longword'.repeat(80) }],
  dictionary: [], snippets: []
};
let micDelay = 0, snapshotDelay = 0, failSave = false, snapshotRequests = 0;
ipcMain.handle('agent-command', async (_, { name, payload }) => {
  if (name === 'snapshot') { snapshotRequests++; await new Promise(resolve => setTimeout(resolve, snapshotDelay)); return snapshot; }
  if (name === 'checkForUpdates') return { available: true, latest: '2.0.6', current: '2.0.5' };
  if (name === 'openReleases') return;
  if (name === 'listMicrophones') { await new Promise(resolve => setTimeout(resolve, micDelay)); return { default: 0, devices: [{ id: 0, name: 'Audit microphone', hostapi: 'Fixture' }] }; }
  if (name === 'saveSettings') { if (failSave) throw new Error('Audit save failure'); Object.assign(snapshot.settings, payload); return snapshot; }
  if (name === 'testMicrophone') return { device: 'Audit microphone', level: .5 };
  if (name === 'upsertDictionary') snapshot.dictionary.push({ id: 1, ...payload });
  if (name === 'upsertSnippet') snapshot.snippets.push({ id: 1, ...payload });
  if (name === 'deleteEntry') snapshot[payload.table] = snapshot[payload.table].filter(x => x.id !== payload.id);
  if (name === 'clearHistory') snapshot.history = [];
  return snapshot;
});

app.whenReady().then(async () => {
  const win = new BrowserWindow({ width: 980, height: 680, useContentSize: true, show: false,
    webPreferences: { preload: path.join(__dirname, '../electron/preload.js'), contextIsolation: true } });
  const run = code => win.webContents.executeJavaScript(code);
  const settle = () => run('new Promise(resolve => setTimeout(resolve, 450))');
  const page = async name => { await run(`document.querySelector('[data-page="${name}"]').click()`); await settle(); };
  const capture = async name => { fs.writeFileSync(path.join(output, name + '.png'), (await win.webContents.capturePage()).toPNG()); };
  await win.loadFile(path.join(__dirname, '../renderer/index.html'));
  win.showInactive();await settle();
  await run(`window.auditErrors=[]; window.addEventListener('unhandledrejection',e=>auditErrors.push(String(e.reason))); window.addEventListener('error',e=>auditErrors.push(e.message));`);
  await capture('home');
  const heroOverlap = await run(`(() => {const range=document.createRange();range.selectNodeContents(document.querySelector('.hero h2'));const text=range.getBoundingClientRect(),orb=document.querySelector('.mini-orb').getBoundingClientRect();return text.right>orb.left&&text.top<orb.bottom&&text.bottom>orb.top})()`);
  await page('settings'); await capture('settings');
  await run(`document.querySelector('[name="style"]').value='formal'`);
  win.webContents.send('agent-event', { type: 'result', text: 'New synthetic dictation', pasted: false });
  await settle();
  const preservedStyle = await run(`document.querySelector('[name="style"]').value`);
  await page('home');
  win.webContents.send('agent-event', { type: 'state', value: 'listening' });
  win.webContents.send('agent-event', { type: 'volume', value: .8 });
  await settle();
  win.webContents.send('agent-event', { type: 'state', value: 'idle' }); await settle();
  const idleMeter = await run(`document.querySelector('.mic-meter').getAttribute('aria-valuenow')`);
  micDelay = 1000; await page('settings'); await page('home'); await settle();
  await page('history'); await capture('history');
  const overflow = await run(`document.querySelector('main').scrollWidth>document.querySelector('main').clientWidth`);
  const errors = await run('auditErrors');
  console.log('AUDIT', JSON.stringify({ output, heroOverlap, preservedStyle, idleMeter, overflow, errors, snapshotRequests }));
  if (!process.env.ALTWISP_AUDIT_BASELINE) {
    assert.equal(heroOverlap, false, 'Home copy overlaps the orb at minimum width');
    assert.equal(preservedStyle, 'formal', 'Background dictation erased an unsaved settings edit');
    assert.equal(idleMeter, '0', 'Microphone meter remains active after recording stops');
    assert.equal(overflow, false, 'Long history transcript overflows the workspace');
    assert.deepEqual(errors, [], 'Delayed microphone replies cause renderer errors after navigation');
    snapshotDelay = 150;
    const requestsBeforeBurst = snapshotRequests;
    for (let i = 0; i < 12; i++) win.webContents.send('agent-event', { type: 'result', text: 'Burst fixture', pasted: true });
    await settle();
    assert.ok(snapshotRequests - requestsBeforeBurst <= 2, 'Snapshot requests were not coalesced');
    snapshotDelay = 0;
    win.hide();await settle();
    const requestsBeforeHidden = snapshotRequests;
    win.webContents.send('agent-event', { type: 'result', text: 'Hidden fixture', pasted: true });await settle();
    assert.equal(snapshotRequests, requestsBeforeHidden, 'Hidden dashboard should defer database snapshots');
    win.showInactive();await settle();
    assert.ok(snapshotRequests > requestsBeforeHidden, 'Visible dashboard should refresh deferred data');
    await run(`document.querySelector('#historySearch').value='missing';document.querySelector('#historySearch').dispatchEvent(new Event('input'))`);
    assert.equal(await run(`document.querySelector('.table tbody tr').hidden`), true);
    win.webContents.send('agent-event', { type: 'result', text: 'Search stays intact', pasted: true }); await settle();
    assert.equal(await run(`document.querySelector('#historySearch').value`), 'missing');
    await page('dictionary');
    await run(`document.querySelector('[name="first"]').value='alt wisp';document.querySelector('[name="second"]').value='ALTWISP'`);
    win.webContents.send('agent-event', { type: 'result', text: 'Draft stays intact', pasted: true }); await settle();
    assert.equal(await run(`document.querySelector('[name="first"]').value`), 'alt wisp');
    await run(`document.querySelector('#entryForm').requestSubmit()`); await settle();
    assert.equal(snapshot.dictionary[0].replacement, 'ALTWISP');
    await run(`document.querySelector('[data-delete]').click()`); await settle();
    assert.equal(snapshot.dictionary.length, 0);
    await page('snippets');
    await run(`document.querySelector('[name="first"]').value='sign off';document.querySelector('[name="second"]').value='Synthetic ending.';document.querySelector('#entryForm').requestSubmit()`); await settle();
    assert.equal(snapshot.snippets[0].expansion, 'Synthetic ending.');
    await run(`document.querySelector('[data-delete]').click()`);await settle();
    assert.equal(snapshot.snippets.length, 0);
    await page('settings');
    await run(`document.querySelector('#checkUpdates').click()`);await settle();
    assert.match(await run(`document.querySelector('#updateResult').textContent`), /2\.0\.6/);
    await run(`document.querySelector('#testMicrophone').click()`);await settle();
    assert.match(await run(`document.querySelector('#micTestResult').textContent`), /Sound detected/);
    await run(`document.querySelector('#inputDevice').value='0';document.querySelector('#saveMicrophone').click()`);await settle();
    assert.equal(snapshot.settings.input_device, 0);
    assert.equal(await run(`Array.from(document.querySelectorAll('.field label')).every(label=>!!label.control)`), true);
    await run(`document.querySelector('[name="style"]').value='formal';document.querySelector('#settingsForm').requestSubmit()`); await settle();
    assert.equal(snapshot.settings.style, 'formal', 'The style control conflicts with HTMLFormElement.style');
    await run(`document.querySelector('[name="transcription_backend"]').value='local';document.querySelector('[name="transcription_backend"]').dispatchEvent(new Event('change',{bubbles:true}))`);
    assert.equal(await run(`document.querySelector('[name="local_model"]').disabled`), false);
    assert.equal(await run(`document.querySelector('[name="polish_enabled"]').disabled`), true);
    win.webContents.send('agent-event', { type: 'state', value: 'processing' }); await settle();
    assert.equal(await run(`document.querySelector('#settingsForm button').disabled`), true);
    win.webContents.send('agent-event', { type: 'state', value: 'idle' }); await settle();
    assert.equal(await run(`document.querySelector('#settingsForm button').disabled`), false);
    await page('settings'); failSave = true;
    await run(`document.querySelector('#settingsForm').requestSubmit()`); await settle();
    assert.match(await run(`document.querySelector('#toast').textContent`), /failed|could not/i);
    assert.deepEqual(await run('auditErrors'), [], 'Settings failure was not caught');
    assert.equal(await run(`document.querySelector('#settingsForm button').disabled`), false);
    await page('home');await run(`document.querySelector('#latest').value='Edited text';document.querySelector('#latest').dispatchEvent(new Event('input'))`);
    await page('history');await page('home');
    assert.equal(await run(`document.querySelector('#latest').value`), 'Edited text');
    await run(`Object.defineProperty(navigator,'clipboard',{value:{writeText:async()=>{throw new Error('Clipboard unavailable')}}});document.querySelector('[data-action="copy"]').click();void 0`);await settle();
    assert.match(await run(`document.querySelector('#toast').textContent`), /Clipboard unavailable/);
    await run(`window.confirm=()=>true;void 0`);await page('history');await run(`document.querySelector('[data-action="clearHistory"]').click()`);await settle();
    assert.equal(snapshot.history.length, 0);
    await run(`document.querySelector('#toast button').click()`);
    win.setSize(1180,800);await page('home');await capture('home-normal');
    assert.equal(await run(`document.querySelector('main').scrollWidth>document.querySelector('main').clientWidth`), false);
    assert.deepEqual(await run('auditErrors'), []);
    console.log('PASS: all dashboard pages, CRUD, search, engine controls, draft preservation, busy/error recovery, async replies and minimum/normal layouts');
  }
  win.destroy(); app.quit();
}).catch(error => { console.error(error); app.exit(1); });
