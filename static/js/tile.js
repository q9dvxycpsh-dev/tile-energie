/* TILE ÉNERGIE — interactions (vanilla JS, aucune dépendance) */
(function () {
  'use strict';
  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => Array.from(c.querySelectorAll(s));
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Mobile drawer ---------- */
  function initDrawer() {
    const drawer = $('#drawer'); if (!drawer) return;
    const open = () => drawer.classList.add('is-open');
    const close = () => drawer.classList.remove('is-open');
    $('#burger') && $('#burger').addEventListener('click', open);
    $$('[data-drawer-close]', drawer).forEach(el => el.addEventListener('click', close));
    document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });
  }

  /* ---------- Scroll reveal ---------- */
  function initReveal() {
    const items = $$('[data-reveal]');
    if (reduce || !('IntersectionObserver' in window)) { items.forEach(i => i.classList.add('in')); return; }
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
    items.forEach(i => io.observe(i));
  }

  /* ---------- Animated counters ---------- */
  function animateCount(el) {
    const target = parseFloat(el.dataset.count);
    const dec = (el.dataset.count.indexOf('.') > -1) ? 1 : 0;
    const dur = 1400, t0 = performance.now();
    const suffix = el.dataset.suffix || '';
    const prefix = el.dataset.prefix || '';
    function frame(t) {
      const p = Math.min((t - t0) / dur, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      const val = (target * eased).toFixed(dec);
      el.textContent = prefix + Number(val).toLocaleString('fr-FR') + suffix;
      if (p < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }
  function initCounters() {
    const nums = $$('[data-count]');
    if (reduce || !('IntersectionObserver' in window)) {
      nums.forEach(n => { n.textContent = (n.dataset.prefix || '') + Number(n.dataset.count).toLocaleString('fr-FR') + (n.dataset.suffix || ''); });
      return;
    }
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => { if (e.isIntersecting) { animateCount(e.target); io.unobserve(e.target); } });
    }, { threshold: 0.5 });
    nums.forEach(n => io.observe(n));
  }

  /* ---------- Hero crossfade ---------- */
  function initHero() {
    const hero = $('[data-hero]'); if (!hero) return;
    const slides = $$('.hero__slide', hero);
    const dots = $$('.hero__dot', hero);
    if (slides.length < 2) return;
    let i = 0, timer;
    const go = (n) => {
      slides[i].classList.remove('is-active'); dots[i] && dots[i].classList.remove('is-active');
      i = (n + slides.length) % slides.length;
      slides[i].classList.add('is-active'); dots[i] && dots[i].classList.add('is-active');
      // restart ken burns
      const img = slides[i].querySelector('img');
      if (img && !reduce) { img.style.animation = 'none'; void img.offsetWidth; img.style.animation = ''; }
    };
    const play = () => { if (reduce) return; timer = setInterval(() => go(i + 1), 5200); };
    const stop = () => clearInterval(timer);
    dots.forEach((d, n) => d.addEventListener('click', () => { stop(); go(n); play(); }));
    play();
    hero.addEventListener('mouseenter', stop);
    hero.addEventListener('mouseleave', play);
  }

  /* ---------- Horizontal slider (galerie qui défile) ---------- */
  function initSliders() {
    $$('[data-slider]').forEach(root => {
      const track = $('.slider__track', root);
      const slides = $$('.slide', track);
      const prev = $('[data-slider-prev]', root);
      const next = $('[data-slider-next]', root);
      const dotsWrap = $('[data-slider-dots]', root);
      if (!track || !slides.length) return;
      let index = 0;
      const perView = () => {
        const w = window.innerWidth;
        if (w <= 540) return 1; if (w <= 880) return 2; return 3;
      };
      let dots = [];
      function buildDots() {
        if (!dotsWrap) return;
        const pages = Math.max(1, slides.length - perView() + 1);
        dotsWrap.innerHTML = '';
        dots = [];
        for (let p = 0; p < pages; p++) {
          const b = document.createElement('button');
          b.className = 'slider__dot'; b.type = 'button';
          b.setAttribute('aria-label', 'Aller à la diapositive ' + (p + 1));
          b.addEventListener('click', () => { index = p; update(); });
          dotsWrap.appendChild(b); dots.push(b);
        }
      }
      function maxIndex() { return Math.max(0, slides.length - perView()); }
      function update() {
        index = Math.min(index, maxIndex());
        const slideW = slides[0].getBoundingClientRect().width;
        const gap = parseFloat(getComputedStyle(track).gap) || 22;
        track.style.transform = `translateX(${-(index * (slideW + gap))}px)`;
        if (prev) prev.disabled = index === 0;
        if (next) next.disabled = index >= maxIndex();
        dots.forEach((d, n) => d.classList.toggle('is-active', n === index));
      }
      prev && prev.addEventListener('click', () => { index--; update(); });
      next && next.addEventListener('click', () => { index++; update(); });
      // drag / swipe
      let startX = 0, dragging = false;
      track.addEventListener('pointerdown', e => { dragging = true; startX = e.clientX; track.style.transition = 'none'; });
      window.addEventListener('pointerup', e => {
        if (!dragging) return; dragging = false; track.style.transition = '';
        const dx = e.clientX - startX;
        if (Math.abs(dx) > 50) { index += dx < 0 ? 1 : -1; }
        update();
      });
      buildDots(); update();
      let rt; window.addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(() => { buildDots(); update(); }, 150); });
    });
  }

  /* ---------- FAQ accordion ---------- */
  function initFaq() {
    $$('.faq__item').forEach(item => {
      const q = $('.faq__q', item), a = $('.faq__a', item);
      if (!q || !a) return;
      q.addEventListener('click', () => {
        const open = item.classList.contains('is-open');
        $$('.faq__item.is-open').forEach(o => { o.classList.remove('is-open'); $('.faq__a', o).style.maxHeight = null; });
        if (!open) { item.classList.add('is-open'); a.style.maxHeight = a.scrollHeight + 'px'; }
      });
    });
  }

  /* ---------- Flash messages ---------- */
  function initFlash() {
    $$('.flash').forEach(f => {
      const close = $('.flash__close', f);
      const dismiss = () => { f.style.opacity = '0'; f.style.transform = 'translateX(20px)'; setTimeout(() => f.remove(), 250); };
      close && close.addEventListener('click', dismiss);
      setTimeout(dismiss, 6000);
    });
  }

  /* ---------- Active nav / sidebar link (longest-prefix match per group) ---------- */
  function initActiveNav() {
    const path = location.pathname;
    [['.nav__link'], ['.drawer__link'], ['.side__link']].forEach(([sel]) => {
      let best = null, bestLen = -1;
      $$(sel).forEach(l => {
        const href = l.getAttribute('href');
        if (!href) return;
        if (href === '/') { if (path === '/' && bestLen < 1) { best = l; bestLen = 1; } return; }
        if (path === href || path.startsWith(href)) {
          if (href.length > bestLen) { best = l; bestLen = href.length; }
        }
      });
      if (best) best.classList.add('is-active');
    });
  }

  /* ---------- Chatbot (réponses à choisir, contenu servi par Django) ---------- */
  function initChatbot() {
    const root = $('#chatbot'); if (!root) return;
    const toggle = $('.chatbot__toggle', root);
    const body = $('#chat-body');
    const chips = $('#chat-chips');
    let tree = null, loaded = false;

    toggle.addEventListener('click', () => {
      root.classList.toggle('is-open');
      if (root.classList.contains('is-open') && !loaded) loadTree();
    });

    function loadTree() {
      loaded = true;
      const url = root.dataset.url;
      fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(r => r.json())
        .then(data => { tree = data.tree; render('start'); })
        .catch(() => { addBot("Le service est momentanément indisponible. Écrivez-nous via la page Contact."); });
    }

    function addMsg(text, who) {
      const d = document.createElement('div');
      d.className = 'msg msg--' + who; d.innerHTML = text;
      body.appendChild(d); body.scrollTop = body.scrollHeight;
      return d;
    }
    const addBot = (t) => addMsg(t, 'bot');

    function typing() {
      const d = document.createElement('div');
      d.className = 'msg msg--bot'; d.innerHTML = '<span class="typing"><i></i><i></i><i></i></span>';
      body.appendChild(d); body.scrollTop = body.scrollHeight; return d;
    }

    function render(nodeId) {
      const node = tree[nodeId]; if (!node) return;
      chips.innerHTML = '';
      const t = typing();
      setTimeout(() => {
        t.remove(); addBot(node.bot);
        (node.options || []).forEach(opt => {
          const c = document.createElement('button');
          c.className = 'chip'; c.type = 'button'; c.textContent = opt.label;
          c.addEventListener('click', () => {
            addMsg(opt.label, 'user');
            if (opt.url) { setTimeout(() => addBot('Je vous y emmène…'), 250); setTimeout(() => location.assign(opt.url), 700); return; }
            render(opt.go || 'start');
          });
          chips.appendChild(c);
        });
      }, reduce ? 50 : 550);
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    initDrawer(); initReveal(); initCounters(); initHero(); initSliders();
    initFaq(); initFlash(); initActiveNav(); initChatbot();
  });
})();

// Bouton retour en haut
document.addEventListener('DOMContentLoaded', () => {
  const backToTopBtn = document.getElementById('backToTop');

  if (backToTopBtn) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 400) {
        backToTopBtn.classList.add('visible');
      } else {
        backToTopBtn.classList.remove('visible');
      }
    });

    backToTopBtn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }
});