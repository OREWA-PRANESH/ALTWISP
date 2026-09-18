const ORB_SIZE_PIXELS = 58;
const TASKBAR_MARGIN = 12;

function overlayBounds(display) {
  const area = display.workArea;
  const size = Math.max(24, Math.round(ORB_SIZE_PIXELS / (display.scaleFactor || 1)));
  return {
    x: Math.round(area.x + (area.width - size) / 2),
    y: Math.round(area.y + area.height - size - TASKBAR_MARGIN),
    width: size,
    height: size,
  };
}

function positionOverlay(window, display) {
  // setPosition preserves a rounded native size on Windows. At fractional DPI,
  // repeated DIP/native conversions enlarge it. Always supply all four bounds.
  window.setBounds(overlayBounds(display), false);
}

module.exports = { overlayBounds, positionOverlay };
