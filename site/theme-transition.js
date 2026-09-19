(function () {
  const themes = ['default', 'orb', 'signal'];
  const classNames = ['orb-theme', 'signal-theme'];
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const body = document.body;

  function currentTheme() {
    if (body.classList.contains('signal-theme')) return 'signal';
    if (body.classList.contains('orb-theme')) return 'orb';
    return 'default';
  }

  function setTheme(theme) {
    body.classList.add('theme-changing');
    window.setTimeout(() => {
      body.classList.remove(...classNames);
      if (theme === 'orb') body.classList.add('orb-theme');
      if (theme === 'signal') body.classList.add('signal-theme');
      history.replaceState(null, '', theme === 'default' ? location.pathname : `?theme=${theme}`);
      window.ScrollTrigger?.refresh();
      window.setTimeout(() => body.classList.remove('theme-changing'), 80);
    }, reducedMotion.matches ? 0 : 420);
  }

  function advanceTheme() {
    const next = themes[(themes.indexOf(currentTheme()) + 1) % themes.length];
    setTheme(next);
  }

  // The automatic cycle is intentionally slow enough to read the page, and is
  // disabled for visitors who ask the browser to minimize motion.
  if (!reducedMotion.matches) window.setInterval(advanceTheme, 14000);
})();
