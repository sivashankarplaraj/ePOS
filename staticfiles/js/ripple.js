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
      :root { --ripple-duration: 600ms; --ripple-opacity: 0.35; --ripple-color-light: rgba(255,255,255,0.55); --ripple-color-dark: rgba(0,0,0,0.35); }
      .${RIPPLE_CLASS} { position:absolute; border-radius:50%; pointer-events:none; transform:scale(0); opacity:var(--ripple-opacity,0.35); background:var(--_ripple-color,currentColor); mix-blend-mode:overlay; animation:ripple-enter var(--ripple-duration,600ms) ease-out forwards; will-change: transform, opacity; }
      [data-ripple-container]{ position:relative; overflow:hidden; }
      @media (prefers-reduced-motion: reduce){ .${RIPPLE_CLASS} { animation:none; opacity:0; } }
      @keyframes ripple-enter { to { transform:scale(1); opacity:0; } }
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

  function luminance(rgb){
    const toLin = v => {
      v /= 255; return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4);
    };
    return 0.2126*toLin(rgb[0]) + 0.7152*toLin(rgb[1]) + 0.0722*toLin(rgb[2]);
  }

  function parseRGB(str){
    const m = /rgba?\(([^)]+)\)/.exec(str || '');
    if(!m) return null;
    const parts = m[1].split(',').map(s=>parseFloat(s));
    return parts.length>=3 ? parts : null;
  }

  function pickRippleColor(target){
    // Attribute overrides
    const explicit = target.getAttribute('data-ripple-color');
    if(explicit) return explicit;
    const cs = getComputedStyle(target);
    // Attempt background-color first; fall back to parent if transparent
    let bg = cs.backgroundColor;
    if(!bg || bg === 'transparent' || bg.startsWith('rgba(0, 0, 0, 0')){
      let p = target.parentElement; let safety=4;
      while(p && safety--){
        const pcbg = getComputedStyle(p).backgroundColor;
        if(pcbg && !pcbg.startsWith('rgba(0, 0, 0, 0')) { bg = pcbg; break; }
        p = p.parentElement;
      }
    }
    const rgb = parseRGB(bg) || [255,255,255];
    const lum = luminance(rgb);
    // If background is light, use dark ripple; if dark use light ripple.
    if(lum > 0.6) return 'var(--ripple-color-dark, rgba(0,0,0,0.35))';
    if(lum < 0.25) return 'var(--ripple-color-light, rgba(255,255,255,0.55))';
    // Mid-tone: blend both via currentColor overlay fallback.
    return 'color-mix(in srgb, var(--ripple-color-light, rgba(255,255,255,0.55)) 55%, var(--ripple-color-dark, rgba(0,0,0,0.45)))';
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
    // Determine effective contrast color
    const color = pickRippleColor(target);
    wave.style.setProperty('--_ripple-color', color);
    // If element has data-ripple-opacity override
    const op = target.getAttribute('data-ripple-opacity');
    if(op) wave.style.opacity = op;
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
