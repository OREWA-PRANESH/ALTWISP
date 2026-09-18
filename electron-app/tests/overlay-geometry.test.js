const test = require('node:test');
const assert = require('node:assert/strict');
const { overlayBounds, positionOverlay } = require('../electron/overlay-geometry');

test('orb stays physically compact and above taskbar on fractional DPI and offset monitors', () => {
  for (const scaleFactor of [1, 1.25, 1.3, 1.5, 1.75, 2]) {
    for (const workArea of [
      { x: 0, y: 0, width: 1477, height: 794 },
      { x: -1920, y: -200, width: 1920, height: 1040 },
      { x: 40, y: 40, width: 1400, height: 750 },
    ]) {
      const display = { scaleFactor, workArea };
      const bounds = overlayBounds(display);
      assert.ok(Math.abs(bounds.width * scaleFactor - 58) <= 1);
      assert.equal(bounds.width, bounds.height);
      assert.equal(bounds.y + bounds.height, workArea.y + workArea.height - 12);
      assert.ok(Math.abs(bounds.x + bounds.width / 2 - (workArea.x + workArea.width / 2)) <= 0.5);
      const writes = [];
      const window = { setBounds: bounds => writes.push(bounds) };
      for (let i = 0; i < 100; i++) positionOverlay(window, display);
      for (const write of writes) assert.deepEqual(write, bounds);
    }
  }
});
