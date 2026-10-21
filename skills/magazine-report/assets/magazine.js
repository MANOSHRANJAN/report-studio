/* Slot system: set aspect ratios, show labelled placeholders for missing images,
   flag pages whose content overflows. render.py reads the flags via --dump-dom. */
(function () {
  const slots = [...document.querySelectorAll('figure.slot')];
  const ready = slots.map(fig => new Promise(done => {
    const frame = fig.querySelector('.frame'), img = fig.querySelector('img');
    const r = fig.dataset.ratio;
    if (img && fig.dataset.fit) img.style.objectFit = fig.dataset.fit;  // data-fit="contain" for posters/graphics
    if (r && frame && !frame.style.height && !fig.classList.contains('fill')) frame.style.aspectRatio = r;
    if (fig.classList.contains('fill')) { fig.style.position = 'absolute'; frame.style.height = '100%'; }
    const ph = document.createElement('div');
    ph.className = 'ph';
    ph.innerHTML = `<b>${fig.dataset.slot}</b><span>ratio ${r || 'free'}</span><span>${fig.dataset.hint || ''}</span>` +
                   `<span>→ images/${fig.dataset.slot}.jpg</span>`;
    frame && frame.appendChild(ph);
    const mark = ok => { fig.classList.toggle('empty', !ok); fig.dataset.filled = ok ? 'yes' : 'no'; done(); };
    if (!img) return mark(false);
    if (img.complete) return mark(img.naturalWidth > 0);
    img.addEventListener('load', () => mark(true));
    img.addEventListener('error', () => mark(false));
  }));
  Promise.all(ready).then(() => (document.fonts ? document.fonts.ready : null)).then(() => {
    document.querySelectorAll('.cover').forEach(c => {
      const s = c.querySelector('figure.slot'); if (s && s.classList.contains('empty')) c.classList.add('empty-hero');
    });
    document.querySelectorAll('.page').forEach((p, i) => {
      p.dataset.index = i + 1;
      const over = p.scrollHeight - p.clientHeight > 2 || [...p.querySelectorAll('.body,.cols-2,.cols-3')]
        .some(el => el.scrollWidth - el.clientWidth > 2);
      p.dataset.overflow = over ? 'yes' : 'no';
    });
    const m = location.hash.match(/page=(\d+)/);
    if (m) { document.body.classList.add('solo'); const p = document.querySelectorAll('.page')[m[1] - 1]; p && p.classList.add('show'); }
    document.body.dataset.ready = 'yes';
  });
})();
