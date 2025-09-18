// Universal Ripple Effect
// Applies to .btn, a, button, .card, and any element with [data-ripple]
// Lightweight, no dependencies. Respects reduced motion preference.
(function(){
  const PREFERS_REDUCED = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if(PREFERS_REDUCED) return; // Respect users opting out of animations.

  const SELECTOR = '.btn, a, button, .card, [data-ripple]';
  const RIPPLE_CLASS = 'ripple-effect-wave';
  const ACTIVE_ATTR = 'data-rippling';

  const styleId = 'global-ripple-style';
  if(!document.getElementById(styleId)){
    const st = document.createElement('style');
    st.id = styleId;
    st.textContent = `
      .${RIPPLE_CLASS} { position:absolute; border-radius:50%; pointer-events:none; transform:scale(0); opacity:0.35; background:currentColor; mix-blend-mode:overlay; animation:ripple-enter .6s ease-out forwards; }
      @keyframes ripple-enter { to { transform:scale(1); opacity:0; } }
      [data-ripple-container]{ position:relative; overflow:hidden; }
    `;
    document.head.appendChild(st);
  }

  function ensureContainer(el){
    if(!el.hasAttribute('data-ripple-container')){
      // Avoid breaking existing stacking contexts: only set position if static.
      const cs = window.getComputedStyle(el);
      if(cs.position === 'static') el.style.position = 'relative';
      // If element might visually clip, keep overflow hidden (cards/buttons fine); anchors usually fine.
      el.setAttribute('data-ripple-container','');
      if(!/(card|btn)/.test(el.className)){
        // Only hide overflow if not already styled; anchors with underline unaffected.
        if(cs.overflow === 'visible') el.style.overflow = 'hidden';
      }
    }
  }

  function createRipple(e, target){
    ensureContainer(target);
    const rect = target.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height) * 1.2; // cover fully
    const wave = document.createElement('span');
    wave.className = RIPPLE_CLASS;
    const x = (e.clientX !== undefined ? e.clientX : (rect.left + rect.width/2)) - rect.left - size/2;
    const y = (e.clientY !== undefined ? e.clientY : (rect.top + rect.height/2)) - rect.top - size/2;
    wave.style.width = wave.style.height = size + 'px';
    wave.style.left = x + 'px';
    wave.style.top = y + 'px';
    target.appendChild(wave);
    wave.addEventListener('animationend', ()=> wave.remove());
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

  document.addEventListener('pointerdown', (e)=>{
    if(e.button !== 0) return; // only main button
    const el = findInteractive(e.target);
    if(!el) return;
    createRipple(e, el);
  }, { passive:true });

  // Keyboard accessibility: trigger on Enter/Space for focused interactive elements
  document.addEventListener('keydown', (e)=>{
    if(e.key !== 'Enter' && e.key !== ' ') return;
    const active = document.activeElement;
    if(!eligible(active)) return;
    createRipple({ clientX: undefined, clientY: undefined }, active);
  });
})();
