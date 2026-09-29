const flow = document.querySelector('.flow-diagram');
document.querySelector('.replay-flow')?.addEventListener('click', () => {
  document.body.classList.add('motion-requested');
  flow.classList.remove('replaying');
  void flow.offsetWidth;
  flow.classList.add('replaying');
});
flow.querySelectorAll('.flow-stage')[2].addEventListener('animationend', event => {
  if (event.animationName === 'stage-replay') flow.classList.remove('replaying');
});

if (window.gsap && window.ScrollTrigger && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  gsap.registerPlugin(ScrollTrigger);

  const glow = document.querySelector('.cursor-glow');
  if (window.matchMedia('(pointer: fine)').matches && glow) {
    const moveX = gsap.quickTo(glow, 'x', { duration: .5, ease: 'power3.out' });
    const moveY = gsap.quickTo(glow, 'y', { duration: .5, ease: 'power3.out' });
    window.addEventListener('pointermove', event => {
      moveX(event.clientX);
      moveY(event.clientY);
    }, { passive: true });
  } else if (glow) {
    glow.hidden = true;
  }

  gsap.from('.how-hero-copy > *', { y: 32, opacity: 0, duration: 1, ease: 'power4.out', stagger: .12 });
  gsap.from('.flow-diagram > .flow-stage, .flow-diagram > b', { y: 36, opacity: 0, duration: .9, ease: 'power3.out', stagger: .1, delay: .2 });

  gsap.utils.toArray('.how-heading').forEach(heading => {
    gsap.from(heading.children, {
      y: 36, opacity: 0, duration: .9, ease: 'power4.out', stagger: .1,
      scrollTrigger: { trigger: heading, start: 'top 82%', once: true }
    });
  });

  gsap.utils.toArray('.step-list article, .mode-card, .privacy-note, .tool-grid article, .start-panel').forEach(item => {
    gsap.from(item, {
      y: 45, opacity: 0, duration: .9, ease: 'power3.out',
      scrollTrigger: { trigger: item, start: 'top 88%', once: true }
    });
  });
}
