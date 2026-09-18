const fs = require('node:fs');
const path = require('node:path');

// ALTWISP currently ships an English UI. Chromium's other locale packs add
// about 45 MB to every Windows install without affecting app functionality.
exports.default = async function afterPack(context) {
  if (context.electronPlatformName !== 'win32') return;
  const locales = path.join(context.appOutDir, 'locales');
  if (!fs.existsSync(locales)) return;
  for (const file of fs.readdirSync(locales)) {
    if (file !== 'en-US.pak') fs.rmSync(path.join(locales, file), { force: true });
  }
};
