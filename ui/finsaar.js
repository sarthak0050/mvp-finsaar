// FinSaar app front end (Streamlit custom component v2). UI state lives in window.__fsUI;
// data (numbers, chat, eval) comes from Python on every rerun; actions go back as trigger values.
export default function (component) {
  const { data, setTriggerValue, parentElement } = component;
  window.__fsD = data;
  window.__fsTrig = setTriggerValue;

  // fonts must be registered on the document (not the shadow root)
  if (!document.getElementById('fs-fonts')) {
    const l = document.createElement('link');
    l.id = 'fs-fonts'; l.rel = 'stylesheet';
    l.href = 'https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap';
    document.head.appendChild(l);
  }

  const S = window.__fsUI || (window.__fsUI = {
    tab: 'dashboard', view: null, sheet: null, why: false, contHidden: false, search: '', filter: 'all',
    watch: loadWatch(), pending: null, evalOpen: {}, txAll: false, actAll: false, menu: false, toast: '',
    evalRunning: null, lastRun: null, input: '',
  });
  if (S.pending && data.done_nonce === S.pending.nonce) S.pending = null;
  if (S.evalRunning && data.eval_done_nonce === S.evalRunning) S.evalRunning = null;

  let root = parentElement.querySelector('#fs-root');
  if (!root) { root = document.createElement('div'); root.id = 'fs-root'; parentElement.appendChild(root); }
  window.__fsRoot = root;
  draw();
  if (!window.__fsKeys) {
    window.__fsKeys = true;
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && window.__fsUI.sheet) { window.__fsUI.sheet = null; draw(); }
    });
  }
}

/* ---------------- helpers ---------------- */
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const nl = (s) => esc(s).replace(/\n/g, '<br>');
function loadWatch() { try { return JSON.parse(localStorage.getItem('fs-watch') || '["smallcap"]'); } catch (e) { return ['smallcap']; } }
function saveWatch(w) { try { localStorage.setItem('fs-watch', JSON.stringify(w)); } catch (e) { /* storage blocked */ } }
function toTop() {
  // Streamlit scrolls its own container, not the window
  try { window.scrollTo(0, 0); } catch (e) { /* ignore */ }
  for (const sel of ['[data-testid="stMain"]', '[data-testid="stAppViewContainer"]', 'section.main', '.main']) {
    const el = document.querySelector(sel); if (el) el.scrollTop = 0;
  }
  if (document.scrollingElement) document.scrollingElement.scrollTop = 0;
}
const nonce = () => Date.now() + '-' + Math.random().toString(36).slice(2, 7);
const I = {
  search: '<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/></svg>',
  spin: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="7.5" stroke-dasharray="2.2 2.6"/></svg>',
  explore: '<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/></svg>',
  dashboard: '<svg viewBox="0 0 24 24"><rect x="4" y="5" width="16" height="14" rx="2"/><path d="M4 10h16M9 14h6"/></svg>',
  sips: '<svg viewBox="0 0 24 24"><rect x="4" y="5" width="16" height="15" rx="2"/><path d="M8 3v4M16 3v4M4 10h16M8 14h1M11.5 14h1M15 14h1M8 17h1M11.5 17h1"/></svg>',
  watchlist: '<svg viewBox="0 0 24 24"><path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/></svg>',
  quality: '<svg viewBox="0 0 24 24"><path d="M12 3l7 3v6c0 4.2-3 7.5-7 9-4-1.5-7-4.8-7-9V6z"/><path d="M9 12l2 2 4-4"/></svg>',
  eye: '<svg viewBox="0 0 24 24"><path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/></svg>',
  eyeoff: '<svg viewBox="0 0 24 24"><path d="M3 3l18 18M10.6 6.1A9.6 9.6 0 0 1 12 6c6 0 9.5 6 9.5 6a17 17 0 0 1-2.7 3.4M6.6 7.1C3.9 8.9 2.5 12 2.5 12S6 18.5 12 18.5c1.6 0 3-.4 4.2-1M9.9 9.9a3 3 0 0 0 4.2 4.2"/></svg>',
  spark: '<svg viewBox="0 0 24 24"><path d="M12 3.5l1.9 5.2 5.2 1.9-5.2 1.9L12 17.7l-1.9-5.2-5.2-1.9 5.2-1.9z"/><path d="M18.5 3.5l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z"/></svg>',
  info: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg>',
  book: '<svg viewBox="0 0 24 24"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5zM4 20.5A2.5 2.5 0 0 0 6.5 23H20v-5"/></svg>',
  send: '<svg viewBox="0 0 24 24"><path d="M21 3L10 14M21 3l-7 18-4-7-7-4z"/></svg>',
  okc: '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M8.5 12.2l2.4 2.4 4.6-4.8"/></svg>',
  badc: '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M9 9l6 6M15 9l-6 6"/></svg>',
  refresh: '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 11a8 8 0 1 0-2.3 5.7M20 4v7h-7"/></svg>',
};
const LOGO = '<svg class="logo" viewBox="0 0 40 40"><defs><linearGradient id="fsg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2d7d55"/><stop offset="1" stop-color="#14432c"/></linearGradient></defs><circle cx="20" cy="20" r="19" fill="url(#fsg)"/><path d="M7 27c4-6 7-9 10-9s5 4 8 4 5-3 8-6v13H7z" fill="#bfe3cc"/><path d="M7 30c4-3 7-4 10-4s6 2 9 2 5-1 7-3v8H7z" fill="#ffffff" opacity=".9"/></svg>';

/* ---------------- actions ---------------- */
function act(name, arg) {
  const S = window.__fsUI, D = window.__fsD, trig = window.__fsTrig;
  switch (name) {
    case 'nav': S.tab = arg; S.view = null; S.sheet = null; S.menu = false; draw(); toTop(); return;
    case 'fund': S.view = { id: arg, from: S.tab }; S.sheet = null; draw(); toTop(); return;
    case 'back': S.view = null; draw(); toTop(); return;
    case 'metric': S.sheet = { type: 'metric', key: arg }; break;
    case 'fundmetric': S.sheet = { type: 'fundmetric', key: arg }; break;
    case 'understand': S.sheet = { type: 'understand' }; break;
    case 'why': S.why = !S.why; break;
    case 'chat': S.sheet = { type: 'chat' }; break;
    case 'close': S.sheet = null; break;
    case 'ask': S.sheet = { type: 'chat' }; send(arg); return;
    case 'followup': S.sheet = { type: 'chat' }; S.input = arg || ''; break;
    case 'newchat': trig('event', { type: 'newchat', nonce: nonce() }); break;
    case 'lang': D.lang = arg; trig('event', { type: 'lang', value: arg, nonce: nonce() }); break;
    case 'scenario': D.scenario = arg; S.why = false; trig('event', { type: 'scenario', value: arg, nonce: nonce() }); break;
    case 'watch': { const i = S.watch.indexOf(arg); if (i >= 0) S.watch.splice(i, 1); else S.watch.push(arg); saveWatch(S.watch); break; }
    case 'filter': S.filter = arg; break;
    case 'cont-x': S.contHidden = true; break;
    case 'txall': S.txAll = !S.txAll; break;
    case 'actall': S.actAll = !S.actAll; break;
    case 'menu': S.menu = !S.menu; break;
    case 'reset': S.menu = false; S.contHidden = false; S.why = false; trig('event', { type: 'reset', nonce: nonce() }); break;
    case 'toast': toast(arg); return;
    case 'eval-toggle': S.evalOpen[arg] = !S.evalOpen[arg]; break;
    case 'run-eval': {
      let code = '';
      if (D.eval && D.eval.passcode_required) { code = window.prompt('Passcode to run the golden set') || ''; if (!code) return; }
      const n = nonce(); S.evalRunning = n; trig('event', { type: 'runeval', passcode: code, nonce: n }); break;
    }
    case 'run-pick': S.lastRun = arg; break;
    case 'top-search': S.tab = 'explore'; S.view = null; S.sheet = null; draw(); const el = window.__fsRoot.querySelector('#fs-search'); if (el) el.focus(); return;
    case 'send': { const el = window.__fsRoot.querySelector('#fs-input'); send(el ? el.value : ''); return; }
  }
  draw();
}
function send(q) {
  const S = window.__fsUI;
  q = (q || '').trim();
  if (!q || S.pending) { draw(); return; }
  S.input = '';
  S.pending = { q, nonce: nonce() };
  draw();
  window.__fsTrig('ask', { q, nonce: S.pending.nonce });
}
function toast(msg) {
  const S = window.__fsUI; S.toast = msg; draw();
  clearTimeout(window.__fsToastT); window.__fsToastT = setTimeout(() => { S.toast = ''; draw(); }, 2200);
}

/* ---------------- render ---------------- */
function draw() {
  const S = window.__fsUI, D = window.__fsD, root = window.__fsRoot;
  const body = root.querySelector('.chat-body');
  const keepBottom = body ? (body.scrollHeight - body.scrollTop - body.clientHeight < 40) : true;
  const typed = root.querySelector('#fs-input'); if (typed) S.input = typed.value;
  root.innerHTML = `<div class="app">${topbar()}${nav()}<main class="main">${S.view ? fundPage() : tabPage()}</main></div>${sheet()}${S.toast ? `<div class="toast">${esc(S.toast)}</div>` : ''}`;
  root.onclick = (e) => {
    const t = e.target.closest('[data-a]');
    if (!t) { if (S.menu && !e.target.closest('.menu')) { S.menu = false; draw(); } return; }
    if (t.classList.contains('overlay') && e.target !== t) return;   // clicks inside the sheet don't close it
    e.preventDefault();
    act(t.dataset.a, t.dataset.v);
  };
  const s = root.querySelector('#fs-search');
  if (s) s.oninput = () => { S.search = s.value; const list = root.querySelector('#fund-list'); if (list) list.innerHTML = fundList(); };
  const inp = root.querySelector('#fs-input');
  if (inp) { inp.value = S.input || ''; inp.onkeydown = (e) => { if (e.key === 'Enter') { e.preventDefault(); send(inp.value); } }; }
  const nb = root.querySelector('.chat-body');
  if (nb && (keepBottom || S.pending)) nb.scrollTop = nb.scrollHeight;
}

function topbar() {
  return `<header class="topbar"><div class="brand">${LOGO}<span>FinSaar</span></div>
    <div class="top-icons"><button class="iconbtn" data-a="top-search" aria-label="Search">${I.search}</button>
    <span class="iconbtn" aria-hidden="true">${I.spin}</span><span class="avatar">SS</span></div></header>`;
}
function nav() {
  const S = window.__fsUI;
  const tabs = [['explore', 'Explore'], ['dashboard', 'Dashboard'], ['sips', 'SIPs'], ['watchlist', 'Watchlist'], ['quality', 'Quality']];
  return `<nav class="nav">${tabs.map(([k, l]) => `<button class="${S.tab === k && !S.view ? 'on' : (S.view && S.view.from === k ? 'on' : '')}" data-a="nav" data-v="${k}">${I[k]}<span>${l}</span></button>`).join('')}</nav>`;
}
function tabPage() {
  const S = window.__fsUI;
  return ({ explore, dashboard, sips, watchlist, quality }[S.tab] || dashboard)();
}
const fundById = (id) => (window.__fsD.funds || []).find((f) => f.id === id);
const tile = (f) => `<span class="tile" style="background:${esc(f.color)}">${esc(f.letter)}</span>`;
const q = (l) => `${esc(l)}<span class="qmark">?</span>`;

/* ----- Explore ----- */
function explore() {
  const S = window.__fsUI;
  const chips = [['all', 'All funds'], ['equity', 'Equity'], ['lower', 'Lower risk']]
    .map(([k, l]) => `<button class="chip ${S.filter === k ? 'on' : ''}" data-a="filter" data-v="${k}">${l}</button>`).join('');
  return `<div class="page"><div class="row"><div class="cap">Explore</div><button class="iconbtn" data-a="top-search" aria-label="Search">${I.search}</button></div>
    <div class="h1">Browse sample funds</div><div class="lede">Learn what each fund type does. FinSaar doesn't recommend funds.</div>
    <label class="search">${I.search}<input id="fs-search" placeholder="Search funds or categories" value="${esc(S.search)}" autocomplete="off"></label>
    <div class="chips">${chips}</div><div id="fund-list">${fundList()}</div>
    <div class="foot-note">Sample fund data for this prototype. Past returns don't indicate future returns.</div></div>`;
}
function fundList() {
  const S = window.__fsUI, D = window.__fsD;
  const term = S.search.trim().toLowerCase();
  const list = (D.funds || []).filter((f) => (S.filter === 'all' || (S.filter === 'equity' ? f.type === 'equity' : f.lower))
    && (!term || (f.name + ' ' + f.cat).toLowerCase().includes(term)));
  if (!list.length) return '<div class="empty">No sample funds match that search.</div>';
  return list.map((f) => fundCard(f)).join('');
}
function fundCard(f) {
  const S = window.__fsUI, on = S.watch.includes(f.id);
  return `<div class="card fund" data-a="fund" data-v="${f.id}" role="button" tabindex="0"><div class="top">${tile(f)}
    <span class="eye ${on ? 'on' : ''}" data-a="watch" data-v="${f.id}" role="button" aria-label="${on ? 'Remove from' : 'Add to'} watchlist">${on ? I.eye : I.eyeoff}</span></div>
    <div class="name">${esc(f.name)}</div><div class="cat">${esc(f.cat)}</div>
    <div class="stats"><div><div class="l">NAV</div><div class="v">${esc(f.nav)}</div></div>
    <div><div class="l">1Y return</div><div class="v pos">${esc(f.r1y)}</div></div><span class="chev">›</span></div></div>`;
}

/* ----- Dashboard ----- */
function dashboard() {
  const S = window.__fsUI, D = window.__fsD, s = D.s;
  const cont = (!S.contHidden && D.last_q) ? `<div class="card cont"><span class="spark">${I.spark}</span>
      <button style="flex:1" data-a="chat"><div class="t">Continue where you left off</div><div class="s">Last time: “${esc(D.last_q)}”</div></button>
      <button class="chev" data-a="chat" aria-label="Continue">›</button><button class="x" data-a="cont-x" aria-label="Dismiss">✕</button></div>` : '';
  const seg = `<div class="seg"><button class="${D.scenario === 'regular' ? 'on' : ''}" data-a="scenario" data-v="regular">Regular day</button><button class="${D.scenario === 'dip' ? 'on' : ''}" data-a="scenario" data-v="dip">Dip day</button></div>`;
  const menu = S.menu ? `<div class="menu"><button data-a="reset">Reset demo</button></div>` : '';
  return `<div class="page"><div class="row"><div><div class="cap">Your money, made clear</div><div class="lede" style="margin-top:6px">Here’s what your SIPs are doing today.</div></div>
      <button class="iconbtn" data-a="menu" aria-label="More">⋮</button></div>${menu}${cont}
    <div class="row" style="margin-top:20px"><div class="cap">Prototype scenario</div>${seg}</div>
    <div class="sec"><h3 style="font-weight:500">Portfolio snapshot</h3><span class="aside">As of today</span></div>
    <div class="card snap"><div class="row" style="align-items:flex-start"><div><button class="lbl" data-a="metric" data-v="value">${q('Current value')}</button>
      <div class="big">${esc(s.value)}</div></div><button class="oned ${s.one_tone}" data-a="metric" data-v="oneday">1D returns ${esc(s.one_day)}</button></div>
      <div class="dash"></div><div class="trio">
      <button data-a="metric" data-v="invested"><div class="l"><span>Invested</span><span class="qmark">?</span></div><div class="v">${esc(s.invested)}</div></button>
      <button data-a="metric" data-v="returns"><div class="l"><span>Total returns</span><span class="qmark">?</span></div><div class="v ${s.ret_tone}">${esc(s.ret_abs)}<br>(${esc(s.ret_pct)})</div></button>
      <button data-a="metric" data-v="xirr"><div class="l"><span>XIRR (Active)</span><span class="qmark">?</span></div><div class="v ${s.xirr_tone}">${esc(s.xirr)}</div></button></div></div>
    <div class="info-line">${I.info}<span>FinSaar explains your SIP here when NAV moves 1% or more in a day, or today's value is under the amount invested.</span></div>
    ${D.trigger ? dipCard() : ''}
    <div class="sec"><h3 style="font-weight:500">Your holdings <span class="mono" style="color:var(--green2);font-size:.82rem;margin-left:4px">1</span></h3><span class="link-btn">Current ›</span></div>
    <button class="holding" data-a="fund" data-v="${D.held_id}">${tile(fundById(D.held_id))}<div><div class="n">${esc(s.fund_short)}</div><div class="c">SIP · ${esc(s.n)} instalments</div></div>
      <div class="vals"><div class="v ${s.ret_tone}">${esc(s.value)}</div><div class="i">(${esc(s.invested)})</div></div><span class="chev">›</span></button>
    <button class="import" data-a="toast" data-v="Importing investments isn't part of this prototype">＋ Import or add investments</button>
    <button class="card askcard" data-a="chat"><span class="spark">${I.spark}</span><div style="flex:1"><div class="t">Have a question about your numbers?</div><div class="s">Ask FinSaar in English or Hinglish.</div></div><span class="chev">›</span></button>
    <div class="foot-note">FinSaar explains your numbers. It is not investment advice and never predicts returns.</div></div>`;
}
function dipCard() {
  const S = window.__fsUI, D = window.__fsD;
  return `<div class="card fs-card"><span class="fs-tag">FinSaar</span><h4>A quick look at your SIP today</h4><p>${esc(D.dip_line)}</p>
    ${S.why ? `<div class="why-text">${esc(D.why_text)}</div>` : ''}
    <div class="acts"><button class="why" data-a="why">Why am I seeing this? ${S.why ? '⌃' : '⌄'}</button><button class="btn-out" data-a="understand">Understand this ↗</button></div></div>`;
}

/* ----- Fund details ----- */
function fundPage() {
  const S = window.__fsUI, D = window.__fsD, f = fundById(S.view.id);
  if (!f) { S.view = null; return tabPage(); }
  const on = S.watch.includes(f.id);
  const head = `<div class="subbar"><button class="back" data-a="back" aria-label="Back">‹</button><div class="t">Fund details</div><span class="more">⋮</span></div>
    <div class="page"><div class="ftag">${esc(f.cat.replace(' · ', ' · '))}</div><div class="fhead">${tile(f)}<div class="h1">${esc(f.name)}</div>
    <span class="eye ${on ? 'on' : ''}" data-a="watch" data-v="${f.id}" role="button" aria-label="${on ? 'Remove from' : 'Add to'} watchlist">${on ? I.eye : I.eyeoff}</span></div>`;
  if (!f.held) {
    return `${head}<div class="sec"><h3 style="font-weight:500">About this fund</h3><span class="aside">Sample fund data</span></div>
      <div class="card"><div class="grid2">
        <button data-a="fundmetric" data-v="nav"><div class="l">${q('Current NAV')}</div><div class="v">${esc(f.nav)}</div></button>
        <button data-a="fundmetric" data-v="risk"><div class="l">${q('Risk level')}</div><div class="v">${esc(f.risk)}</div></button>
        <button data-a="fundmetric" data-v="r1y"><div class="l">${q('1Y return (past)')}</div><div class="v pos">${esc(f.r1y)}</div></button></div></div>
      <div class="info-line">${I.info}<span>You don't hold this fund. Past returns don't indicate future returns.</span></div>
      <div class="foot-note">FinSaar explains your numbers. It is not investment advice and never predicts returns.</div></div>`;
  }
  const s = D.s, tx = D.tx || [], shown = S.txAll ? tx : tx.slice(0, 1);
  return `${head}<button class="card askbanner" data-a="chat"><span class="spark">${I.spark}</span><div style="flex:1"><div style="font-weight:700">Ask FinSaar</div><div class="small">About this SIP</div></div><span class="chev">›</span></button>
    <div class="info-line">${I.info}<span>FinSaar explains your SIP here when NAV moves 1% or more in a day, or today's value is under the amount invested.</span></div>
    ${D.trigger ? dipCard() : ''}
    <div class="sec"><h3 style="font-weight:500">Your investment</h3><span class="aside">Based on your data</span></div>
    <div class="card"><div class="grid2">
      <button data-a="metric" data-v="returns"><div class="l">${q('Total returns')}</div><div class="v ${s.ret_tone}">${esc(s.ret_abs)} (${esc(s.ret_pct)})</div></button>
      <button data-a="metric" data-v="xirr"><div class="l">${q('XIRR')}</div><div class="v ${s.xirr_tone}">${esc(s.xirr)}</div></button>
      <button data-a="metric" data-v="units"><div class="l">${q('Units')}</div><div class="v">${esc(s.units)}</div></button>
      <button data-a="metric" data-v="avgnav"><div class="l">${q('Average NAV')}</div><div class="v">${esc(s.avg_nav)}</div></button>
      <button data-a="metric" data-v="nav"><div class="l">${q('Current NAV')}</div><div class="v">${esc(s.nav)}</div></button>
      <button data-a="metric" data-v="value"><div class="l">${q('Current value')}</div><div class="v">${esc(s.value)}</div></button></div></div>
    <div class="card sipline" style="margin-top:14px"><div><div class="small">Your SIP</div><div class="big">${esc(s.monthly)} monthly</div><div class="s">Next instalment · ${esc(s.next_short)}</div></div>
      <button class="link-btn" style="color:var(--green2);font-weight:700" data-a="nav" data-v="sips">View SIP ›</button></div>
    <div class="sec"><h3 style="font-weight:500">Transactions</h3><button class="link-btn" data-a="txall">${S.txAll ? 'Show less' : 'View all'} ›</button></div>
    <div>${shown.map((t) => `<div class="tx"><div>${esc(t.short)} · ${esc(t.amount)} instalment<div class="sub">${esc(t.units)} units at NAV ${esc(t.nav)}</div></div><span class="done">Completed</span></div>`).join('')}</div>
    <div class="foot-note">FinSaar explains your numbers. It is not investment advice and never predicts returns.</div></div>`;
}

/* ----- SIPs ----- */
function sips() {
  const S = window.__fsUI, D = window.__fsD, s = D.s, tx = D.tx || [], shown = S.actAll ? tx : tx.slice(0, 2);
  return `<div class="page"><div class="cap">SIPs</div><div class="h1">Small steps, monthly</div><div class="lede">A simple view of your investing rhythm.</div>
    <div class="sipcard"><div><div class="l">Monthly SIP</div><div class="big">${esc(s.monthly)}</div></div><div class="r"><div class="l">Next instalment</div><div class="v">${esc(s.next_short)}</div></div></div>
    <div class="stats3"><div><div class="l">Instalments</div><div class="v">${esc(s.n)}</div></div><div><div class="l">Started</div><div class="v">${esc(s.started)}</div></div><div><div class="l">Cadence</div><div class="v">Monthly</div></div></div>
    <div class="sec"><h3 style="font-weight:500">Recent activity</h3><button class="link-btn" data-a="actall">${S.actAll ? 'Show less' : 'View all'} ›</button></div>
    <div class="timeline">${shown.map((t, i) => `<div class="tl"><span class="dot"></span><div><div class="t">${esc(t.short)} · Instalment paid</div><div class="s">${esc(t.amount)} · bought ${esc(t.units)} units${i === 0 ? ` · ${esc(s.units)} units held in total` : ''}</div></div><span class="done">Completed</span></div>`).join('')}</div>
    <button class="card askcard" data-a="chat"><span class="spark">${I.spark}</span><div style="flex:1"><div class="t">Want to understand your SIP?</div><div class="s">Ask FinSaar about any number.</div></div><span class="chev">›</span></button>
    <div class="foot-note">FinSaar explains your numbers. It is not investment advice and never predicts returns.</div></div>`;
}

/* ----- Watchlist ----- */
function watchlist() {
  const S = window.__fsUI, D = window.__fsD;
  const list = (D.funds || []).filter((f) => S.watch.includes(f.id));
  return `<div class="page"><div class="cap">Watchlist</div><div class="h1">Funds you’re watching</div><div class="lede">Tap the eye on any fund in Explore to add it here.</div>
    ${list.length ? list.map((f) => fundCard(f)).join('') : '<div class="empty">Your watchlist is empty.</div>'}
    <div class="foot-note">Sample fund data for this prototype. Past returns don't indicate future returns.</div></div>`;
}

/* ----- Quality ----- */
function quality() {
  const S = window.__fsUI, D = window.__fsD, E = D.eval || {};
  const runs = E.runs || [];
  const cur = runs.find((r) => r.id === S.lastRun) || runs[0];
  const golden = E.golden || [];
  const rowsById = {}; (cur ? cur.rows : []).forEach((r) => { rowsById[r.id] = r; });
  const latest = cur ? `<div class="runcard"><div class="l">${cur === runs[0] ? 'Latest run' : esc(cur.label)}</div><div class="big">${cur.passed} of ${cur.total} passed</div><div class="m">${esc(cur.model)} · ${esc(cur.at)}</div></div>`
    : `<div class="runcard"><div class="l">Latest run</div><div class="big">No runs yet</div><div class="m">Run the golden set to score the gate.</div></div>`;
  const runBtn = `<button class="btn-out runbtn" data-a="run-eval" ${S.evalRunning ? 'disabled' : ''}>${S.evalRunning ? 'Running the golden set… (about 2 min)' : '▶ Run golden set now'}</button>`;
  const gold = golden.map((g) => {
    const r = rowsById[g.id], ok = r ? r.passed : null, open = S.evalOpen[g.id];
    const icon = ok === false ? `<span class="okc bad">${I.badc}</span>` : `<span class="okc ${ok ? 'ok' : ''}" style="${ok === null ? 'stroke:var(--muted)' : ''}">${I.okc}</span>`;
    const ck = (name, pass) => `<span class="ck ${pass === false ? 'bad' : ''}">${name}</span>`;
    const bodyHtml = open ? `<div class="body"><div class="meta">${esc(g.profile)} · ${esc(g.source)} · expected ${esc(g.expected)}</div>
      ${r ? `<div class="ans">${nl(r.answer)}</div><div class="cks">${ck('gate', r.gate)}${ck('must include', r.include)}${ck('must not include', r.exclude)}${ck('path', r.path)}</div>${r.reasons ? `<div class="why-reasons">${esc(r.reasons)}</div>` : ''}`
        : '<div class="ans">Not run yet.</div>'}</div>` : '';
    return `<div class="card gold"><button class="head" data-a="eval-toggle" data-v="${g.id}">${icon}<span class="id">${esc(g.id)}</span><span class="q">${esc(g.question)}</span><span class="chev">${open ? '⌃' : '⌄'}</span></button>${bodyHtml}</div>`;
  }).join('');
  const past = runs.length ? `<div class="sec"><h3 style="font-weight:500">Past runs</h3></div><div class="runs">${runs.map((r) => `<button class="runchip ${cur && r.id === cur.id ? 'on' : ''}" data-a="run-pick" data-v="${r.id}"><span>${esc(r.label)}</span><b>${r.passed}/${r.total}</b></button>`).join('')}</div>` : '';
  return `<div class="page"><div class="row"><div class="cap">Answer quality</div><span class="iconbtn" style="color:var(--green2)">${I.quality}</span></div>
    <div class="h1">How FinSaar checks itself</div><div class="lede">Every answer passes a quality gate before you see it. This page scores that gate against a golden set.</div>
    <div class="card gate-list" style="margin-top:16px"><b>The gate blocks any answer that:</b><ul>${(E.gate_rules || []).map((x) => `<li>${esc(x)}</li>`).join('')}</ul>
      <div class="small" style="margin-top:8px">Blocked answers are retried once, then replaced with a safe reply that states your plain numbers and points to AMFI or SEBI.</div></div>
    ${latest}${runBtn}<div class="sec"><h3 style="font-weight:500">Golden set</h3><span class="aside">${golden.length} questions</span></div>${gold}${past}
    <div class="card ai-place"><b>Where AI earns its place</b>${esc(E.ai_place || '')}</div>
    <div class="foot-note">FinSaar explains your numbers. It is not investment advice and never predicts returns.</div></div>`;
}

/* ---------------- sheets ---------------- */
function sheet() {
  const S = window.__fsUI, D = window.__fsD;
  if (!S.sheet) return '';
  let inner = '';
  if (S.sheet.type === 'metric' || S.sheet.type === 'fundmetric') {
    const src = S.sheet.type === 'metric' ? (D.metrics || {}) : (D.fund_metrics || {});
    const m = src[S.sheet.key]; if (!m) return '';
    const sub = S.sheet.type === 'fundmetric' ? (fundById(S.view && S.view.id) || {}) : null;
    const text = sub ? m.text.replace('{nav}', sub.nav || '').replace('{risk}', sub.risk || '').replace('{r1y}', sub.r1y || '') : m.text;
    inner = `<div class="sheet" role="dialog" aria-modal="true" aria-label="${esc(m.title)}"><div class="grab"></div><button class="sheet-x" data-a="close" aria-label="Close">✕</button>
      <div class="cap">FinSaar explains</div><h2>${esc(m.title)}</h2><p class="t">${esc(text)}</p>
      <div class="based">${I.book}<div><b>Based on</b><span>${esc(m.based)}</span></div></div>
      <button class="btn-dark" data-a="followup" data-v="${esc(m.ask || '')}">✦ Ask a follow-up</button></div>`;
  } else if (S.sheet.type === 'understand') {
    const u = D.understand || { items: [], chips: [] };
    inner = `<div class="sheet" role="dialog" aria-modal="true" aria-label="Understand today's value"><div class="grab"></div><button class="sheet-x" data-a="close" aria-label="Close">✕</button>
      <div class="cap">Understand today's value</div><h2>What changed, and what didn't</h2>
      <div class="steps">${u.items.map((it, i) => `<div class="st"><span class="n">${i + 1}</span><div><b>${esc(it[0])}</b><div>${esc(it[1])}</div></div></div>`).join('')}</div>
      <div class="based" style="margin-top:14px">${I.book}<div><b>Based on</b><span>Your SIP data · learn more at <a href="${esc(D.links.amfi)}" target="_blank" rel="noopener">AMFI</a> and <a href="${esc(D.links.sebi)}" target="_blank" rel="noopener">SEBI investor site</a></span></div></div>
      <div class="qchips">${u.chips.map((c) => `<button class="qchip" data-a="ask" data-v="${esc(c)}">${esc(c)}</button>`).join('')}</div>
      <div class="small">Educational only. Not investment advice.</div></div>`;
  } else if (S.sheet.type === 'chat') {
    inner = chatSheet();
  }
  return `<div class="overlay" data-a="close">${inner}</div>`;
}
function chatSheet() {
  const S = window.__fsUI, D = window.__fsD;
  const msgs = (D.messages || []).map(msgHtml).join('');
  const pend = S.pending ? `<div class="msg-user">${esc(S.pending.q)}</div><div class="msg-bot loading">${I.spark}<div>Checking your answer against your data<span class="dots"></span></div></div>` : '';
  const greet = D.lang === 'Hinglish'
    ? 'Namaste. Main aapke SIP ke numbers ko simple shabdon mein samjha sakta hoon. Kya samajhna chahenge?'
    : 'Hi. I can explain your SIP numbers in simple words. What would you like to understand?';
  const chips = (!D.messages || !D.messages.length) && !S.pending
    ? `<div class="qchips">${(D.chips || []).map((c) => `<button class="qchip" data-a="ask" data-v="${esc(c)}">${esc(c)}</button>`).join('')}</div>` : '';
  return `<div class="sheet chat" role="dialog" aria-modal="true" aria-label="FinSaar chat"><div class="head"><div class="grab"></div>
      <div class="hrow"><div><div class="cap">FinSaar</div><h2>Let’s make this simple</h2></div>
      <div><button class="newchat" data-a="newchat">${I.refresh} New chat</button><button class="sheet-x" style="float:none" data-a="close" aria-label="Close">✕</button></div></div>
      <div class="langseg"><button class="${D.lang === 'English' ? 'on' : ''}" data-a="lang" data-v="English">English</button><button class="${D.lang === 'Hinglish' ? 'on' : ''}" data-a="lang" data-v="Hinglish">Hinglish</button></div>
      <div class="note">FinSaar replies only in the language you pick here.</div></div>
    <div class="chat-body"><div class="msg-bot">${I.spark}<div>${esc(greet)}</div></div>${chips}${msgs}${pend}</div>
    <div class="composer"><input id="fs-input" placeholder="Ask a follow-up" maxlength="300" autocomplete="off"><button class="send" data-a="send" aria-label="Send" ${S.pending ? 'disabled' : ''}>${I.send}</button></div>
    <div class="disc">Educational only. FinSaar doesn't give investment advice or predictions.</div></div>`;
}
function msgHtml(m) {
  const D = window.__fsD;
  if (m.role === 'user') return `<div class="msg-user">${esc(m.text)}</div>`;
  const nums = m.numbers && m.numbers.length ? `<table class="nums">${m.numbers.map((r) => `<tr><td>${esc(r[0])}</td><td>${esc(r[1])}</td></tr>`).join('')}</table>` : '';
  let foot = '';
  if (m.footer === 'decline') foot = `<div class="msg-foot ok">Not investment advice · <a href="${esc(D.links.sebi)}" target="_blank" rel="noopener">SEBI</a> / <a href="${esc(D.links.amfi)}" target="_blank" rel="noopener">AMFI investor education</a></div>`;
  else if (m.footer === 'data') foot = '<div class="msg-foot ok">Your SIP data</div>';
  else foot = `<div class="msg-foot warn">⚠ ${esc(m.note || 'Showing your plain numbers')}</div>`;
  const outside = m.footer === 'decline' ? '<div class="outside">ⓘ Outside what I can help with</div>' : '';
  return `<div class="msg-bot">${I.spark}<div>${outside}${nl(m.text)}${nums}${foot}</div></div>`;
}
