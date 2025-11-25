// Universal Touch Invert Effect
// Applies to .btn, a, button, .card, and any element with [data-ripple]
// On touch/pointer-down, inverts colours briefly for visual feedback.
// Lightweight, no dependencies. Respects reduced motion preference.
(function(){
  const SELECTOR = '.btn, a, button, .card, [data-ripple]';
  const INVERT_CLASS = 'touch-invert-active';
  const DURATION_MS = 300; // how long to keep the invert effect

  const styleId = 'global-touch-invert-style';
  if(!document.getElementById(styleId)){
    const st = document.createElement('style');
    st.id = styleId;
    st.textContent = `
      .${INVERT_CLASS} {
        filter: invert(1);
        transition: filter 0.05s ease-out;
      }
      @media (prefers-reduced-motion: reduce){
        .${INVERT_CLASS} { filter: none; }
      }
    `;
    document.head.appendChild(st);
  }

  function eligible(el){
    if(!el) return false;
    if(el.closest('[disabled]')) return false;
    return el.matches(SELECTOR);
  }

  function findInteractive(start){
    if(!start) return null;
    if(eligible(start)) return start;
    return start.closest(SELECTOR);
  }

  function applyInvert(el){
    if(!el || el.classList.contains(INVERT_CLASS)) return;
    el.classList.add(INVERT_CLASS);
    setTimeout(()=> el.classList.remove(INVERT_CLASS), DURATION_MS);
  }

  // Pointer (mouse / touch) interaction
  document.addEventListener('pointerdown', (e)=>{
    if(e.button !== 0) return; // only main button
    const el = findInteractive(e.target);
    if(!el) return;
    applyInvert(el);
  }, { passive: true });

  // Keyboard accessibility: trigger on Enter/Space for focused interactive elements
  document.addEventListener('keydown', (e)=>{
    if(e.key !== 'Enter' && e.key !== ' ') return;
    const active = document.activeElement;
    if(!eligible(active)) return;
    applyInvert(active);
  });
})();
