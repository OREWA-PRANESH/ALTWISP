const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('altwisp', {
  command: (name, payload = {}) => ipcRenderer.invoke('agent-command', { name, payload }),
  onEvent: (callback) => ipcRenderer.on('agent-event', (_, event) => callback(event)),
  window: (action) => ipcRenderer.send('window-action', action),
  platform: process.platform,
});
