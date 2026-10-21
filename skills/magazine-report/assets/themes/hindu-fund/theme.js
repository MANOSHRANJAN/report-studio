/* Hindu Fund theme helpers — icons + data-driven charts. Load BEFORE magazine.js.
 *
 *  Icons:  <i class="ico" data-i="users"></i>        (stroke icons, Lucide-style, ISC licence)
 *  Charts: <div class="chart" data-chart="donut" data-unit="inr"
 *               data-values='[["Gharwapsi",995000],["Legal Fund",500000]]'></div>
 *          data-chart = donut | pie ; data-unit = inr | count ; data-legend = "below" | "none"
 *          optional data-center="₹38.8L" (donut centre label) and data-colors='["#..",...]'
 */
(function () {
  const P = {
    users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    rupee: '<path d="M6 3h12"/><path d="M6 8h12"/><path d="m6 13 8.5 8"/><path d="M6 13h3"/><path d="M9 13c6.667 0 6.667-10 0-10"/>',
    heart: '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>',
    file: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/>',
    trend: '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>',
    chart: '<path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>',
    megaphone: '<path d="m3 11 18-5v12L3 14v-3z"/><path d="M11.6 16.8a3 3 0 1 1-5.8-1.6"/>',
    bell: '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>',
    scale: '<path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>',
    book: '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
    calendar: '<rect width="18" height="18" x="3" y="4" rx="2"/><path d="M16 2v4"/><path d="M8 2v4"/><path d="M3 10h18"/>',
    temple: '<path d="M3 22h18"/><path d="M6 18v-7"/><path d="M10 18v-7"/><path d="M14 18v-7"/><path d="M18 18v-7"/><path d="M12 2 20 7H4z"/><path d="M4 11h16"/><path d="M4 18h16"/>',
    sprout: '<path d="M7 20h10"/><path d="M10 20c5.5-2.5.8-6.4 3-10"/><path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4 0 5.5.8z"/><path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z"/>',
    search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    hands: '<path d="M11 20 7 16V9a2 2 0 0 1 4 0v11z"/><path d="m13 20 4-4V9a2 2 0 0 0-4 0v11z"/><path d="M7 16 4 13"/><path d="m17 16 3-3"/>',
    camera: '<path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/>',
    whatsapp: '<path d="M3 21l1.65-3.8a9 9 0 1 1 3.4 2.9L3 21"/><path d="M9 10a.5.5 0 0 0 1 0V9a.5.5 0 0 0-1 0v1a5 5 0 0 0 5 5h1a.5.5 0 0 0 0-1h-1a.5.5 0 0 0 0 1"/>',
    youtube: '<path d="M2.5 17a24.12 24.12 0 0 1 0-10 2 2 0 0 1 1.4-1.4 49.56 49.56 0 0 1 16.2 0A2 2 0 0 1 21.5 7a24.12 24.12 0 0 1 0 10 2 2 0 0 1-1.4 1.4 49.55 49.55 0 0 1-16.2 0A2 2 0 0 1 2.5 17"/><path d="m10 15 5-3-5-3z"/>',
    instagram: '<rect width="20" height="20" x="2" y="2" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" x2="17.51" y1="6.5" y2="6.5"/>',
    facebook: '<path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>',
    linkedin: '<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/><rect width="4" height="12" x="2" y="9"/><circle cx="4" cy="4" r="2"/>',
    play: '<polygon points="6 3 20 12 6 21 6 3"/>',
  };
  const X_FILL = '<path fill="currentColor" stroke="none" d="M18.9 1.15h3.68l-8.04 9.19L24 22.85h-7.4l-5.8-7.58-6.64 7.58H.47l8.6-9.83L0 1.15h7.6l5.24 6.93zm-1.3 19.5h2.04L6.49 3.24H4.3z"/>';
  const BRAND = { youtube: "#FF0000", instagram: "#C13584", facebook: "#1877F2", linkedin: "#0A66C2", whatsapp: "#25D366" };

  document.querySelectorAll("i.ico[data-i]").forEach(el => {
    const k = el.dataset.i;
    const inner = k === "x" ? X_FILL : P[k];
    if (!inner) return;
    const color = el.hasAttribute("data-brand") && BRAND[k] ? ` style="color:${BRAND[k]}"` : "";
    el.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"${color}>${inner}</svg>`;
  });

  /* Indian number formatting: 3884500 -> 38,84,500 */
  const inr = n => {
    const s = Math.round(n).toString(), last3 = s.slice(-3), rest = s.slice(0, -3);
    return (rest ? rest.replace(/\B(?=(\d{2})+(?!\d))/g, ",") + "," : "") + last3;
  };
  window.HF = { inr };

  const PALETTE = ["#2E5E86", "#D9822B", "#3F8A4F", "#B8322A", "#7D5BA6", "#B59A45", "#C76FA8", "#6E6458", "#3F7E86", "#8E5A2B"];

  document.querySelectorAll(".chart[data-chart]").forEach(el => {
    let vals;
    try { vals = JSON.parse(el.dataset.values || "[]"); } catch (e) { el.textContent = "chart data error"; return; }
    const colors = el.dataset.colors ? JSON.parse(el.dataset.colors) : PALETTE;
    const total = vals.reduce((a, v) => a + v[1], 0) || 1;
    const donut = el.dataset.chart === "donut";
    const R = 100, r = donut ? 58 : 0, cx = 110, cy = 110;
    let a0 = -Math.PI / 2, paths = "";
    vals.forEach((v, i) => {
      const a1 = a0 + (v[1] / total) * Math.PI * 2, large = a1 - a0 > Math.PI ? 1 : 0;
      const p = (rad, ang) => [cx + rad * Math.cos(ang), cy + rad * Math.sin(ang)];
      const [x0, y0] = p(R, a0), [x1, y1] = p(R, a1);
      let d;
      if (vals.length === 1) d = `M${cx - R},${cy}a${R},${R} 0 1,0 ${2 * R},0a${R},${R} 0 1,0 ${-2 * R},0`;
      else if (donut) {
        const [x2, y2] = p(r, a1), [x3, y3] = p(r, a0);
        d = `M${x0},${y0}A${R},${R} 0 ${large} 1 ${x1},${y1}L${x2},${y2}A${r},${r} 0 ${large} 0 ${x3},${y3}Z`;
      } else d = `M${cx},${cy}L${x0},${y0}A${R},${R} 0 ${large} 1 ${x1},${y1}Z`;
      paths += `<path d="${d}" fill="${colors[i % colors.length]}" stroke="#fff" stroke-width="1.2"/>`;
      if (!donut && v[1] / total > 0.06) {  // % labels inside pie slices
        const [lx, ly] = p(R * 0.62, (a0 + a1) / 2);
        paths += `<text x="${lx}" y="${ly}" text-anchor="middle" dominant-baseline="middle" fill="#fff" style="font:700 11px var(--label)">${(v[1] / total * 100).toFixed(1)}%</text>`;
      }
      a0 = a1;
    });
    if (donut && el.dataset.center) {
      paths += `<text x="${cx}" y="${cy - 4}" text-anchor="middle" style="font:700 20px var(--display);fill:var(--ink)">${el.dataset.center}</text>`;
      if (el.dataset.centerLabel) paths += `<text x="${cx}" y="${cy + 14}" text-anchor="middle" style="font:500 7.5px var(--label);letter-spacing:.15em;fill:var(--muted)">${el.dataset.centerLabel}</text>`;
    }
    const size = el.dataset.size || "62mm";
    let html = `<svg viewBox="0 0 220 220" style="width:${size};height:${size};margin:0 auto">${paths}</svg>`;
    if (el.dataset.legend !== "none") {
      const fmt = v => el.dataset.unit === "inr" ? "₹" + inr(v) : el.dataset.unit === "pct" ? v + "%" : inr(v);
      html += `<div class="legend">${vals.map((v, i) =>
        `<div><i style="background:${colors[i % colors.length]}"></i><span>${v[0]}</span><b>${v[2] || fmt(v[1])}</b></div>`).join("")}</div>`;
    }
    el.innerHTML = html;
  });
})();
