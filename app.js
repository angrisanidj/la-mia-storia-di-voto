'use strict';
// ===== Configurazione =====
// Testo in fondo all'immagine: metti qui l'indirizzo della pagina pubblicata.
const PIEDE_IMMAGINE = '';
const OGGI = new Date();
const OGGI_ISO = OGGI.toISOString().slice(0, 10);

const MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'];
const REGIONI = { '01': 'Piemonte', '02': "Valle d'Aosta", '03': 'Lombardia', '04': 'Trentino-Alto Adige', '05': 'Veneto', '06': 'Friuli-Venezia Giulia', '07': 'Liguria', '08': 'Emilia-Romagna', '09': 'Toscana', '10': 'Umbria', '11': 'Marche', '12': 'Lazio', '13': 'Abruzzo', '14': 'Molise', '15': 'Campania', '16': 'Puglia', '17': 'Basilicata', '18': 'Calabria', '19': 'Sicilia', '20': 'Sardegna' };

// Simboli disegnabili (inseriti come emoji nel testo, ridisegnati in vettoriale nell'immagine)
const SEGNI = [
  { e: '🔴', c: '#E0322B', n: 'rosso' }, { e: '🟠', c: '#F28B1E', n: 'arancione' }, { e: '🟡', c: '#F6C62C', n: 'giallo' },
  { e: '🟢', c: '#3BA55C', n: 'verde' }, { e: '🔵', c: '#2D6FDB', n: 'blu' }, { e: '🟣', c: '#8E44C4', n: 'viola' },
  { e: '🟤', c: '#8A5A3B', n: 'marrone' }, { e: '⚫', c: '#1E1E1E', n: 'nero' }, { e: '⚪', c: '#FFFFFF', n: 'bianco' },
  { e: '✅', c: '#3BA55C', n: 'sì', tipo: 'si' }, { e: '❌', c: '#E0322B', n: 'no', tipo: 'no' },
];
const SEGNO_DA_EMOJI = Object.fromEntries(SEGNI.map(s => [s.e, s]));

// ===== Comuni =====
const ESTERO = { id: 'EE', nome: 'Estero', sig: '', reg: null, cod: 'EE', att: 1, alias: [] };
const COMUNI = COMUNI_TXT.split('\n').map(r => {
  const [nome, sig, reg, cod, att, alias] = r.split('|');
  return { nome, sig, reg, cod, att: att === '1', alias: alias ? alias.split(';') : [] };
});
COMUNI.forEach(c => { c.k = norm(c.nome); c.ka = c.alias.map(norm); });
ESTERO.k = 'estero'; ESTERO.ka = ['aire', 'fuori italia']; COMUNI.push(ESTERO);

function norm(s) {
  return s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[’'`\-\/.]/g, ' ').replace(/\s+/g, ' ').trim();
}
function cercaComuni(q) {
  const k = norm(q);
  if (!k) return [];
  const pref = [], cont = [], al = [];
  for (const c of COMUNI) {
    if (c.k.startsWith(k)) pref.push(c);
    else if (c.k.includes(k)) cont.push(c);
    else if (c.ka.some(a => a.startsWith(k))) al.push(c);
  }
  const ord = (a, b) => (b.att - a.att) || a.nome.localeCompare(b.nome, 'it');
  return [...pref.sort(ord), ...cont.sort(ord), ...al.sort(ord)].slice(0, 10);
}

// ===== Date =====
const ym = iso => { const [y, m] = iso.split('-').map(Number); return y * 12 + (m - 1); };
function dataLunga(d, d2) {
  const [y, m, g] = d.split('-').map(Number);
  if (d2) {
    const [y2, m2, g2] = d2.split('-').map(Number);
    if (m2 === m) return `${g}-${g2} ${MESI[m - 1]} ${y}`;
    return `${g} ${MESI[m - 1]} - ${g2} ${MESI[m2 - 1]} ${y}`;
  }
  return `${g} ${MESI[m - 1]} ${y}`;
}
function dataBreve(d) { const [y, m, g] = d.split('-'); return `${g}/${m}/${y}`; }
function sommaAnni(iso, n) { const [y, m, g] = iso.split('-'); return `${+y + n}-${m}-${g}`; }

// ===== Stato (solo in memoria) =====
let seq = 0;
const stato = {
  nascita: { y: null, m: null },
  residenze: [{ id: ++seq, comune: null, y: null, m: null }],
  extra: [], // {id, tipo:'com'|'bal'|'altro', resId, nome, d}
  risposte: {}, // key -> {testo, st: 'ok'|'non'|'escl'}
};

// Residenza attiva in una data (ISO). Restituisce {res, trasloco}
function residenzaIn(iso) {
  const v = ym(iso);
  const rs = residenzeOrdinate();
  let att = null, trasloco = false;
  for (let i = 0; i < rs.length; i++) {
    const r = rs[i];
    const ini = i === 0 ? -Infinity : r.y * 12 + (r.m - 1);
    if (v >= ini) { att = r; trasloco = v === ini; }
  }
  return { res: att, trasloco };
}
function residenzeOrdinate() {
  const [prima, ...altre] = stato.residenze;
  return [prima, ...altre.filter(r => r.y && r.m).sort((a, b) => (a.y * 12 + a.m) - (b.y * 12 + b.m))].filter(r => r && r.comune);
}
function regioneDi(comune, iso) {
  if (!comune || !comune.reg) return null;
  const c = CAMBI_REGIONE[comune.cod];
  if (c) return iso < c[0] ? c[1] : c[2];
  return comune.reg;
}

// Maggiore età: confronto per mese; nel mese del compleanno dipende dal giorno.
function eta(iso, anni) {
  const { y, m } = stato.nascita;
  const comp = (y + anni) * 12 + (m - 1);
  const v = ym(iso);
  return v > comp ? 'si' : v === comp ? 'forse' : 'no';
}

// ===== Calcolo dell'elenco =====
function calcola() {
  const out = [];
  const { y, m } = stato.nascita;
  if (!y || !m || !stato.residenze[0].comune) return out;
  const push = (o) => {
    if (o.d > OGGI_ISO) return;
    const e18 = eta(o.d, 18);
    if (e18 === 'no') return;
    o.note = o.note || [];
    if (e18 === 'forse') o.note.push(`Hai compiuto 18 anni in quel mese: potevi votare solo se il compleanno cadeva entro il ${dataLunga(o.d)}${o.d2 ? ', primo giorno di voto' : ''}.`);
    out.push(o);
  };

  for (const e of NAZIONALI) {
    const note = [];
    const { res, trasloco } = residenzaIn(e.d);
    if (res && res.comune === ESTERO) note.push('Eri residente all’estero.');
    if (e.t === 'pol' && e.d < '2022-01-01') {
      const e25 = eta(e.d, 25);
      if (e25 === 'no') note.push('Solo Camera: per il Senato servivano 25 anni.');
      if (e25 === 'forse') note.push('Per il Senato servivano 25 anni: dipende dal giorno di nascita.');
    }
    const descr = e.t === 'ref' ? e.l + (e.q > 1 ? ` (${e.q} quesiti)` : '') : e.t === 'pol' ? 'Camera e Senato' : 'Parlamento europeo';
    push({ key: `N:${e.d}:${e.t}`, d: e.d, d2: e.d2, tipo: e.t, qk: e.d, etichetta: e.s, descr, q: e.q, note });
  }

  // Regionali
  const giaRegionali = new Set();
  const aggiungiRegionali = (d, d2, cb) => {
    const { res, trasloco } = residenzaIn(d);
    if (!res || res.comune === ESTERO) return;
    const reg = regioneDi(res.comune, d);
    if (!reg) return;
    cb(reg, res, trasloco);
  };
  for (const [reg, date] of Object.entries(REGIONALI)) {
    for (const s of date) {
      const [d, d2] = s.split('|');
      aggiungiRegionali(d, d2, (r, res, trasloco) => {
        if (r !== reg) return;
        const note = [];
        if (trasloco) note.push('Ti sei trasferito in quel mese: verifica dove eri iscritto.');
        const nome = reg === '04' ? 'Trentino-Alto Adige' : REGIONI[reg];
        push({ key: `R:${reg}:${d}`, d, d2, tipo: 'reg', reg, sig: res.comune.sig, etichetta: `Regionali ${nome}`, descr: reg === '02' ? 'Consiglio regionale' : 'Presidente e consiglio regionale', note });
      });
    }
  }
  for (const [reg, date] of Object.entries(SECONDI_TURNI_REGIONALI)) {
    for (const d of date) {
      aggiungiRegionali(d, null, (r, res, trasloco) => {
        if (r !== reg) return;
        push({ key: `R2:${reg}:${d}`, d, tipo: 'reg', reg, sig: res.comune.sig, etichetta: `Regionali ${REGIONI[reg]}, secondo turno`, descr: 'Secondo voto per presidenza e parte del consiglio', note: trasloco ? ['Ti sei trasferito in quel mese: verifica dove eri iscritto.'] : [] });
      });
    }
  }
  for (const turno of PROVINCIALI_TAA) for (const prov of ['TN', 'BZ']) {
    const d = turno[prov];
    aggiungiRegionali(d, null, (r, res, trasloco) => {
      if (r !== '04' || res.comune.sig !== prov) return;
      const bz = prov === 'BZ';
      const note = [];
      if (trasloco) note.push('Ti sei trasferito in quel mese: verifica dove eri iscritto.');
      let escl = false;
      const anniRes = d >= '2026-06-23' ? 2 : 4;
      if (bz && !residenteDa(d, anniRes, '04')) { note.push(`Per il consiglio provinciale di Bolzano servivano ${anniRes} anni di residenza in regione: dai comuni indicati non risultano.`); escl = true; }
      push({ key: `P:${res.comune.sig}:${d}`, d, tipo: 'reg', reg: '04', sig: res.comune.sig, etichetta: bz ? 'Provinciali Bolzano' : 'Provinciali Trento', descr: bz ? 'Consiglio provinciale di Bolzano' : 'Presidente e consiglio provinciale di Trento', note, esclDefault: escl });
    });
  }
  for (const e of REFERENDUM_REGIONALI) {
    aggiungiRegionali(e.d, e.d2, (r) => {
      if (r !== e.r) return;
      push({ key: `RR:${e.r}:${e.d}`, d: e.d, d2: e.d2, tipo: 'ref', qk: `R${e.r}-${e.d}`, etichetta: e.s, descr: e.l, note: [] });
    });
  }

  // Aggiunte a mano
  for (const x of stato.extra) {
    if (!x.d) continue;
    const res = stato.residenze.find(r => r.id === x.resId);
    const nomeC = res && res.comune ? res.comune.nome : '';
    const etichetta = x.tipo === 'com' ? `Comunali ${nomeC}` : x.tipo === 'bal' ? `Ballottaggio comunali ${nomeC}` : x.nome || 'Altra elezione';
    const note = [];
    if (res) { const att = residenzaIn(x.d).res; if (att && att.id !== res.id) note.push(`In quella data risultavi residente a ${att.comune.nome}.`); }
    const o = { key: `X:${x.id}`, d: x.d, d2: x.d2, tipo: x.tipo, etichetta, descr: '', note, extraId: x.id,
      reg: res && res.comune ? regioneDi(res.comune, x.d) : null, sig: res && res.comune ? res.comune.sig : null };
    if (eta(x.d, 18) === 'no') { o.note.push('A quella data non avevi ancora 18 anni.'); o.esclDefault = true; out.push(o); }
    else push(o);
  }

  out.sort((a, b) => a.d.localeCompare(b.d) || ordineTipo(a.tipo) - ordineTipo(b.tipo));
  return out;
}
const ordineTipo = t => ({ pol: 0, eur: 1, reg: 2, ref: 3, com: 4, bal: 5, altro: 6 }[t] ?? 9);

// Residenza continuativa nella regione per n anni prima della data
function residenteDa(iso, anni, reg) {
  const inizio = sommaAnni(iso, -anni);
  const rs = residenzeOrdinate();
  if (!rs.length) return false;
  // nascita come inizio della prima residenza
  for (let v = ym(inizio); v <= ym(iso); v++) {
    const y = Math.floor(v / 12), m = v % 12 + 1;
    if (y * 12 + m - 1 < stato.nascita.y * 12 + stato.nascita.m - 1) return false;
    const r = residenzaIn(`${y}-${String(m).padStart(2, '0')}-15`).res;
    if (!r || regioneDi(r.comune, `${y}-${String(m).padStart(2, '0')}-15`) !== reg) return false;
  }
  return true;
}

// ===== Interfaccia =====
const $ = s => document.querySelector(s);
const el = (tag, attrs = {}, ...figli) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') n.className = v;
    else if (k.startsWith('on')) n.addEventListener(k.slice(2), v);
    else if (v === true) n.setAttribute(k, '');
    else if (v !== false && v != null) n.setAttribute(k, v);
  }
  for (const f of figli.flat()) if (f != null) n.append(f);
  return n;
};

function opzioniMesi(sel, vuoto) {
  sel.append(el('option', { value: '' }, vuoto));
  MESI.forEach((m, i) => sel.append(el('option', { value: i + 1 }, m[0].toUpperCase() + m.slice(1))));
}
function opzioniAnni(sel, da, a, vuoto, desc = true) {
  sel.append(el('option', { value: '' }, vuoto));
  for (let y = desc ? a : da; desc ? y >= da : y <= a; desc ? y-- : y++) sel.append(el('option', { value: y }, String(y)));
}

function initNascita() {
  opzioniMesi($('#nascita-mese'), 'Scegli…');
  opzioniAnni($('#nascita-anno'), 1910, OGGI.getFullYear() - 17, 'Scegli…');
  $('#nascita-mese').addEventListener('change', e => { stato.nascita.m = +e.target.value || null; aggiorna(); });
  $('#nascita-anno').addEventListener('change', e => { stato.nascita.y = +e.target.value || null; aggiorna(); });
}

function disegnaResidenze() {
  const box = $('#residenze');
  box.replaceChildren();
  stato.residenze.forEach((r, i) => {
    const riga = el('div', { class: 'residenza' });
    riga.append(campoComune(r, i));
    if (i === 0) {
      riga.append(el('div', { class: 'dal-nascita' }, 'dalla nascita'));
    } else {
      const sm = el('select', { class: 'campo', 'aria-label': 'Mese del trasferimento' });
      opzioniMesi(sm, 'Mese');
      sm.value = r.m || '';
      sm.addEventListener('change', () => { r.m = +sm.value || null; aggiorna(); });
      const sy = el('select', { class: 'campo', 'aria-label': 'Anno del trasferimento' });
      opzioniAnni(sy, 1910, OGGI.getFullYear(), 'Anno');
      sy.value = r.y || '';
      sy.addEventListener('change', () => { r.y = +sy.value || null; aggiorna(); });
      riga.append(el('div', {}, el('span', { class: 'etichetta', 'aria-hidden': 'true' }, 'Dal mese'), sm), el('div', {}, el('span', { class: 'etichetta', 'aria-hidden': 'true' }, 'dell’anno'), sy));
      riga.append(el('button', { class: 'x', type: 'button', 'aria-label': 'Rimuovi questo comune', onclick: () => {
        stato.residenze.splice(i, 1);
        stato.extra = stato.extra.filter(x => x.resId !== r.id);
        disegnaResidenze(); aggiorna();
      } }, '×'));
    }
    box.append(riga);
  });
  disegnaPulsantiAggiunta();
}

function campoComune(r, i) {
  const wrap = el('div', { class: 'ac' });
  const id = `comune-${r.id}`;
  const lab = el('label', { class: 'etichetta', for: id }, i === 0 ? (stato.residenze.length > 1 ? 'Il primo comune di residenza' : 'Comune di residenza') : 'Poi ti sei trasferito a');
  const inp = el('input', { id, class: 'campo', autocomplete: 'off', spellcheck: 'false', placeholder: 'Scrivi il nome del comune', role: 'combobox', 'aria-expanded': 'false', 'aria-autocomplete': 'list', 'aria-controls': id + '-lista' });
  if (r.comune) inp.value = etichettaComune(r.comune);
  const ul = el('ul', { id: id + '-lista', role: 'listbox', hidden: true });
  let risultati = [], att = -1;
  const chiudi = () => { ul.hidden = true; inp.setAttribute('aria-expanded', 'false'); };
  const scegli = c => { r.comune = c; inp.value = etichettaComune(c); chiudi(); disegnaPulsantiAggiunta(); aggiorna(); };
  const mostra = () => {
    ul.replaceChildren();
    risultati.forEach((c, j) => {
      const li = el('li', { role: 'option', id: `${id}-o${j}`, 'aria-selected': j === att ? 'true' : 'false' },
        el('span', {}, c.nome), el('small', {}, c === ESTERO ? 'fuori dall’Italia' : `${c.sig}${c.att ? '' : ' · ex comune'}`));
      li.addEventListener('mousedown', ev => { ev.preventDefault(); scegli(c); });
      ul.append(li);
    });
    ul.hidden = !risultati.length;
    inp.setAttribute('aria-expanded', String(!ul.hidden));
    if (att >= 0) inp.setAttribute('aria-activedescendant', `${id}-o${att}`); else inp.removeAttribute('aria-activedescendant');
  };
  inp.addEventListener('input', () => {
    if (r.comune) { r.comune = null; aggiorna(); }
    risultati = cercaComuni(inp.value); att = risultati.length ? 0 : -1; mostra();
  });
  inp.addEventListener('keydown', ev => {
    if (ul.hidden) return;
    if (ev.key === 'ArrowDown') { att = Math.min(att + 1, risultati.length - 1); mostra(); ev.preventDefault(); }
    else if (ev.key === 'ArrowUp') { att = Math.max(att - 1, 0); mostra(); ev.preventDefault(); }
    else if (ev.key === 'Enter' && att >= 0) { scegli(risultati[att]); ev.preventDefault(); }
    else if (ev.key === 'Escape') chiudi();
  });
  inp.addEventListener('blur', chiudi);
  wrap.append(lab, inp, ul);
  return wrap;
}
const etichettaComune = c => c === ESTERO ? 'Estero' : `${c.nome} (${c.sig})`;

function controllaResidenze() {
  const box = $('#avvisi-res');
  box.replaceChildren();
  const msg = [];
  const altre = stato.residenze.slice(1);
  if (altre.some(r => r.comune && (!r.y || !r.m))) msg.push('Indica mese e anno del trasferimento per ogni comune successivo.');
  if (stato.nascita.y && altre.some(r => r.y && r.m && r.y * 12 + r.m < stato.nascita.y * 12 + stato.nascita.m)) msg.push('Un trasferimento risulta precedente alla nascita.');
  const date = altre.filter(r => r.y && r.m).map(r => r.y * 12 + r.m);
  if (new Set(date).size !== date.length) msg.push('Due trasferimenti hanno lo stesso mese.');
  msg.forEach(m => box.append(el('p', { class: 'avviso' }, m)));
}

// ===== Elenco =====
let elenco = [];
function risposta(k) { return stato.risposte[k] || (stato.risposte[k] = { testo: '', st: null }); }
function statoDi(o) { const r = risposta(o.key); return r.st || (o.esclDefault ? 'escl' : 'ok'); }

// Colore del pallino di una voce: il primo simbolo scritto nella risposta
function coloreVoto(o) {
  const st = statoDi(o), r = risposta(o.key);
  if (st === 'escl') return null;
  if (st === 'non') return { c: '#fff', b: '#9AA2AF', vuoto: true };
  const m = r.testo.match(new RegExp(SEGNI.map(x => x.e).join('|'), 'u'));
  if (m) { const sg = SEGNO_DA_EMOJI[m[0]]; return { c: sg.c, b: sg.c === '#FFFFFF' ? '#9AA2AF' : sg.c }; }
  return r.testo.trim() ? { c: '#5A6372', b: '#5A6372' } : { c: '#fff', b: '#C3C8D2', vuoto: true };
}
function applicaColore(nodo, o) {
  const k = coloreVoto(o);
  nodo.style.setProperty('--c', k ? k.c : '#fff');
  nodo.style.setProperty('--b', k ? k.b : '#E1E4E9');
}

function disegnaElenco() {
  const box = $('#elenco');
  const scroll = window.scrollY;
  box.replaceChildren();
  const pronto = stato.nascita.y && stato.nascita.m && stato.residenze[0].comune;
  $('#box-agg').hidden = !pronto;
  if (!elenco.length) {
    box.append(el('div', { class: 'vuoto' }, pronto
      ? 'Dal 1992 a oggi non risulta nessuna consultazione in cui avessi già 18 anni.'
      : 'Inserisci data di nascita e comune per vedere l’elenco.'));
    return;
  }
  const attive = elenco.filter(o => statoDi(o) !== 'escl').length;
  box.append(el('p', { class: 'conto' }, el('b', {}, String(attive)), attive === 1 ? 'consultazione nella tua storia' : 'consultazioni nella tua storia'));
  const perAnno = new Map();
  for (const o of elenco) { const a = o.d.slice(0, 4); if (!perAnno.has(a)) perAnno.set(a, []); perAnno.get(a).push(o); }
  for (const [anno, voci] of perAnno) {
    const contenitore = el('div', { class: 'voci' });
    box.append(el('section', { class: 'annata', 'aria-label': anno }, el('h3', { class: 'anno' }, anno), contenitore));
    for (const o of voci) contenitore.append(voceElenco(o, anno));
  }
  window.scrollTo(0, scroll);
}

function voceElenco(o, anno) {
  const st = statoDi(o);
  const r = risposta(o.key);
  const pallino = el('span', { class: 'pallino-voto', 'aria-hidden': 'true' });
  applicaColore(pallino, o);
  const inp = el('input', { class: 'campo', value: r.testo, placeholder: segnaposto(o), 'aria-label': `Come hai votato: ${o.etichetta} ${anno}`, maxlength: 140 });
  inp.addEventListener('input', () => { r.testo = inp.value; applicaColore(pallino, o); programmaAnteprima(); });
  const inserisci = (t) => {
    const s = inp.selectionStart ?? inp.value.length, f = inp.selectionEnd ?? s;
    const pre = inp.value.slice(0, s), dopo = inp.value.slice(f);
    const sp = pre && !/\s$/.test(pre) ? ' ' : '';
    inp.value = pre + sp + t + dopo; r.testo = inp.value;
    const pos = (pre + sp + t).length; inp.focus(); inp.setSelectionRange(pos, pos);
    applicaColore(pallino, o); programmaAnteprima();
  };
  const segni = el('div', { class: 'segni', role: 'group', 'aria-label': 'Aggiungi un simbolo colorato' },
    SEGNI.map(s => el('button', { class: 'segno', type: 'button', title: s.n, 'aria-label': `Aggiungi simbolo ${s.n}`, onclick: () => inserisci(s.e) }, iconaSegno(s))));
  const nome = `st-${o.key}`;
  const opzione = (val, txt) => el('label', {}, el('input', { type: 'radio', name: nome, value: val, checked: st === val, onchange: () => { r.st = val; aggiorna(false); } }), el('span', {}, txt));
  const stato_ = el('div', { class: 'stato', role: 'radiogroup', 'aria-label': 'Cosa hai fatto' },
    opzione('ok', 'Ho votato'), opzione('non', 'Non ho votato'), opzione('escl', 'Togli'));
  const elimina = o.extraId ? el('button', { class: 'bottone testuale elimina', type: 'button', onclick: () => { stato.extra = stato.extra.filter(x => x.id !== o.extraId); aggiorna(); } }, 'Elimina') : null;
  return el('article', { class: 'el' + (st === 'escl' ? ' escl' : '') },
    pallino,
    el('h3', {}, o.etichetta),
    el('p', { class: 'data' }, dataLunga(o.d, o.d2) + (o.descr ? ' · ' + o.descr : '')),
    o.note.map(t => el('p', { class: 'nota' }, t)),
    st === 'ok' ? el('div', { class: 'voto' }, controlliScelta(o, r, inp, () => applicaColore(pallino, o)), el('div', { class: 'riga-testo' }, el('div', {}, el('span', { class: 'sulla-card', 'aria-hidden': 'true' }, 'Sulla tua immagine'), inp), segni)) : null,
    el('div', {}, stato_, elimina));
}

// ===== Scelte guidate: liste, coalizioni, quesiti =====
const COALIZIONI_LOCALI = [
  { b: 'CDX', n: 'Centrodestra', e: '🔵' },
  { b: 'CSX', n: 'Centrosinistra', e: '🔴' },
  { b: 'M5S', n: 'Movimento 5 Stelle', e: '🟡', da: '2009-10-04' },
  { b: 'Civico', n: 'Candidato civico', e: '🟣' },
];
const CIVICHE = [
  { b: 'Lista civica di centrodestra', n: 'Lista civica di centrodestra', e: '🔵', civica: true },
  { b: 'Lista civica di centrosinistra', n: 'Lista civica di centrosinistra', e: '🔴', civica: true },
  { b: 'Lista civica', n: 'Lista civica (altra)', e: '🟣', civica: true },
];
const SCHEDE = [{ v: '__bianca', t: 'Scheda bianca ⚪', l: 'Scheda bianca' }, { v: '__nulla', t: 'Scheda nulla', l: 'Scheda nulla' }];
const emojiDi = p => p.e || (typeof COLORE_PARTITO !== 'undefined' && COLORE_PARTITO[p.b]) || (typeof COLORE_AREA !== 'undefined' && COLORE_AREA[p.a]) || '⚪';

// Ultima consultazione nazionale (politiche o europee) svolta entro la data
function ultimaNazionale(iso) {
  if (typeof PARTITI_NAZIONALI === 'undefined') return null;
  const cand = NAZIONALI.filter(e => (e.t === 'pol' || e.t === 'eur') && e.d <= iso);
  if (!cand.length) return null;
  const e = cand.sort((x, y) => x.d.localeCompare(y.d))[cand.length - 1];
  return PARTITI_NAZIONALI[`${e.t}-${e.d.slice(0, 4)}`];
}
// Partiti del periodo per regionali e comunali: le liste dell'ultima consultazione nazionale + partiti locali attivi
function partitiDelPeriodo(iso, reg, sig, tipo) {
  const anno = +iso.slice(0, 4);
  const fonte = ultimaNazionale(iso);
  const naz = fonte ? fonte.liste.slice() : [];
  const loc = (typeof PARTITI_REGIONALI === 'undefined' ? [] : PARTITI_REGIONALI).filter(p => {
    const [r, prov] = p.reg.split('-');
    // le liste personali dei candidati presidenti valgono solo alle regionali
    return r === reg && (!prov || prov === sig) && p.da <= anno && anno <= p.a && !(p.pers && tipo !== 'reg');
  });
  return { naz, loc };
}

function seleziona(etichetta, gruppi, valore, onchange) {
  const sel = el('select', { class: 'campo', 'aria-label': etichetta });
  sel.append(el('option', { value: '' }, etichetta + '…'));
  for (const [nomeGr, voci] of gruppi) {
    if (!voci.length) continue;
    const g = nomeGr ? el('optgroup', { label: nomeGr }) : sel;
    voci.forEach(v => g.append(el('option', { value: v.v }, v.l)));
    if (nomeGr) sel.append(g);
  }
  sel.value = valore || '';
  sel.addEventListener('change', () => onchange(sel.value));
  return sel;
}
const vocePartito = (p, pref = '') => ({ v: pref + p.b, l: p.b && p.n && p.b !== p.n ? `${p.b} – ${p.n}` : (p.n || p.b), p });

function controlliScelta(o, r, inp, dopo = () => {}) {
  const box = el('div', { class: 'scelte' });
  r.sel = r.sel || {};
  const imposta = t => { inp.value = t; r.testo = t; r.st = 'ok'; dopo(); programmaAnteprima(); };
  const anno = o.d.slice(0, 4);

  if (o.tipo === 'pol' || o.tipo === 'eur') {
    const dati = typeof PARTITI_NAZIONALI !== 'undefined' ? PARTITI_NAZIONALI[`${o.tipo}-${anno}`] : null;
    if (!dati) return box;
    const liste = dati.liste.map(p => vocePartito(p));
    const coal = (o.tipo === 'pol' && ['1994', '1996', '2001'].includes(anno) && dati.coalizioni) ? dati.coalizioni.map(c => ({ v: c.n, l: c.n, p: { b: c.n, n: c.n, a: c.a } })) : null;
    const tutte = [...liste, ...(coal || [])];
    const componi = () => {
      const { lista, coalizione } = r.sel;
      if (lista && lista.startsWith('__')) return imposta(SCHEDE.find(s => s.v === lista).t);
      const pl = liste.find(v => v.v === lista), pc = coal && coal.find(v => v.v === coalizione);
      const parti = [];
      if (pc) parti.push(`${pc.p.n} ${emojiDi(pc.p)}`);
      if (pl) parti.push(`${pc ? 'Lista ' : ''}${pl.p.b} ${emojiDi(pl.p)}`);
      if (lista === '__altro') parti.push('Altra lista');
      imposta(parti.join(' '));
    };
    if (coal) box.append(seleziona('Coalizione (scheda uninominale)', [[null, coal]], r.sel.coalizione, v => { r.sel.coalizione = v; componi(); }));
    box.append(seleziona(coal ? 'Lista (scheda proporzionale)' : 'Lista votata', [['Liste sopra l’1%', liste], ['Altro', [{ v: '__altro', l: 'Un’altra lista' }, ...SCHEDE]]], r.sel.lista, v => { r.sel.lista = v; componi(); }));
    void tutte;
    return box;
  }

  if (o.tipo === 'reg' || o.tipo === 'com' || o.tipo === 'bal') {
    const senzaPresidente = o.reg === '02' || (o.reg === '04' && (o.sig === 'BZ' || o.d < '2003-01-01'));
    const coalizioni = COALIZIONI_LOCALI.filter(c => !c.da || c.da <= o.d).map(c => ({ v: c.b, l: c.n, p: c }));
    const { naz, loc } = o.reg ? partitiDelPeriodo(o.d, o.reg, o.sig, o.tipo) : { naz: [], loc: [] };
    const vn = naz.map(p => vocePartito(p)), vl = loc.map(p => vocePartito(p)), vc = CIVICHE.map(p => ({ v: p.b, l: p.n, p }));
    const tutte = [...vn, ...vl, ...vc];
    const componi = () => {
      const { coalizione, lista } = r.sel;
      if ([coalizione, lista].some(v => v && v.startsWith('__'))) return imposta(SCHEDE.find(s => s.v === coalizione || s.v === lista).t);
      const pc = coalizioni.find(v => v.v === coalizione), pl = tutte.find(v => v.v === lista);
      const parti = [];
      if (pc) parti.push(`${pc.p.b} ${pc.p.e}`);
      if (pl) parti.push(pl.p.civica || /^lista /i.test(pl.p.b) ? `${pl.p.b} ${emojiDi(pl.p)}` : `Lista ${pl.p.b} ${emojiDi(pl.p)}`);
      imposta(parti.join(' '));
    };
    const nomeCand = o.tipo === 'reg' ? (o.reg === '04' ? 'Candidato presidente della provincia' : 'Candidato presidente') : 'Candidato sindaco';
    if (!senzaPresidente) box.append(seleziona(nomeCand, [[null, coalizioni], ['Altro', o.tipo === 'bal' ? SCHEDE : []]], r.sel.coalizione, v => { r.sel.coalizione = v; componi(); }));
    if (o.tipo !== 'bal') box.append(seleziona('Lista', [['Partiti nazionali', vn], [o.tipo === 'reg' ? 'Partiti locali e liste dei candidati' : 'Partiti locali', vl], ['Liste civiche', vc], ['Altro', SCHEDE]], r.sel.lista, v => { r.sel.lista = v; componi(); }));
    return box;
  }

  if (o.tipo === 'ref') {
    box.className = 'scelte-ref';
    const dati = typeof QUESITI !== 'undefined' ? QUESITI[o.qk] : null;
    const quesiti = dati && dati.quesiti && dati.quesiti.length > 1 ? dati.quesiti : null;
    if (!quesiti) {
      [['SÌ ✅', 'Sì'], ['NO ❌', 'No'], ['Scheda bianca ⚪', 'Scheda bianca']].forEach(([t, l]) =>
        box.append(el('button', { class: 'tondino ' + (l === 'Sì' ? 'si' : l === 'No' ? 'no' : 'nulla'), type: 'button', 'aria-pressed': String(r.testo === t), onclick: () => { imposta(t); disegnaElenco(); } }, l)));
      return box;
    }
    r.q = r.q || quesiti.map(() => '');
    const componi = () => {
      const tot = quesiti.length, si = [], no = [];
      quesiti.forEach((q, i) => { if (r.q[i] === 'si') si.push(q.breve); if (r.q[i] === 'no') no.push(q.breve); });
      const parti = [];
      const descr = (lista, verbo, em) => {
        if (lista.length === tot) return `${verbo} a tutti i ${tot} quesiti ${em}`;
        if (lista.length <= 2) return `${verbo} a ${lista.map(x => '«' + x + '»').join(' e ')} ${em}`;
        return `${verbo} a ${lista.length} quesiti su ${tot} ${em}`;
      };
      // prima il gruppo più numeroso, descritto per numero; poi l'altro, per nome se breve
      const gruppi = [[si, 'SÌ', '✅'], [no, 'NO', '❌']].filter(g => g[0].length).sort((a, b) => b[0].length - a[0].length);
      gruppi.forEach(([l, v, e]) => parti.push(descr(l, v, e)));
      imposta(parti.join(' '));
    };
    const tutti = v => { r.q = quesiti.map(() => v); componi(); disegnaElenco(); };
    box.append(el('div', { class: 'rapidi' },
      el('button', { class: 'tondino si', type: 'button', 'aria-pressed': String(r.q.every(v => v === 'si')), onclick: () => tutti('si') }, 'Sì a tutti'),
      el('button', { class: 'tondino no', type: 'button', 'aria-pressed': String(r.q.every(v => v === 'no')), onclick: () => tutti('no') }, 'No a tutti')));
    const tab = el('div', { class: 'quesiti' });
    quesiti.forEach((q, i) => {
      const gruppo = el('div', { class: 'quesito' }, el('span', {}, `${i + 1}. ${q.breve}`));
      const sw = el('div', { class: 'sino', role: 'group', 'aria-label': `Quesito ${i + 1}` });
      [['si', 'Sì', 'si'], ['no', 'No', 'no'], ['', '–', 'nulla']].forEach(([v, l, c]) => sw.append(el('button', { type: 'button', class: 'tondino ' + c, 'aria-label': v ? `${l} al quesito ${i + 1}` : `Nessuna risposta al quesito ${i + 1}`, 'aria-pressed': String(r.q[i] === v), onclick: () => { r.q[i] = v; componi(); disegnaElenco(); } }, l)));
      gruppo.append(sw);
      tab.append(gruppo);
    });
    box.append(tab);
    return box;
  }
  return box;
}

function segnaposto(o) {
  if (o.tipo === 'ref') return o.q > 1 ? 'Es. SÌ a 4 quesiti su 5 ✅' : 'Es. NO ❌';
  if (o.tipo === 'reg') return 'Es. centrodestra 🔵, lista Forza Italia 🔵';
  if (o.tipo === 'com' || o.tipo === 'bal') return 'Es. lista civica 🟣';
  return 'Es. il partito che hai votato 🔵';
}
function iconaSegno(s) {
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg'); svg.setAttribute('viewBox', '0 0 20 20'); svg.setAttribute('aria-hidden', 'true');
  const add = (t, a) => { const n = document.createElementNS(ns, t); for (const k in a) n.setAttribute(k, a[k]); svg.append(n); };
  if (s.tipo === 'si') { add('rect', { x: 1, y: 1, width: 18, height: 18, rx: 4, fill: s.c }); add('path', { d: 'M5 10.5l3.2 3.2L15 6.8', fill: 'none', stroke: '#fff', 'stroke-width': 2.6, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }); }
  else if (s.tipo === 'no') add('path', { d: 'M4 4l12 12M16 4L4 16', stroke: s.c, 'stroke-width': 3.6, 'stroke-linecap': 'round' });
  else add('circle', { cx: 10, cy: 10, r: 8.5, fill: s.c, stroke: s.c === '#FFFFFF' ? '#9AA0A6' : 'none', 'stroke-width': 1 });
  return svg;
}

// ===== Comunali e altre =====
let formAperto = null;
function disegnaPulsantiAggiunta() {
  const box = $('#pulsanti-agg');
  box.replaceChildren();
  const visti = new Set();
  for (const r of stato.residenze) {
    if (!r.comune || r.comune === ESTERO || visti.has(r.comune.cod)) continue;
    visti.add(r.comune.cod);
    box.append(el('button', { class: 'bottone secondario piccolo', type: 'button', onclick: () => apriForm({ tipo: 'com', resId: r.id }) }, `Comunali a ${r.comune.nome}`));
  }
  box.append(el('button', { class: 'bottone secondario piccolo', type: 'button', onclick: () => apriForm({ tipo: 'altro' }) }, 'Altra elezione'));
  disegnaForm();
}
function apriForm(f) { formAperto = f; disegnaForm(); const p = $('#form-agg input, #form-agg select'); if (p) p.focus(); }
function disegnaForm() {
  const box = $('#form-agg');
  box.replaceChildren();
  if (!formAperto) return;
  const f = formAperto;
  const form = el('form', { class: 'form-agg' });
  const res = stato.residenze.find(r => r.id === f.resId);
  const annoMin = stato.nascita.y ? Math.max(1992, stato.nascita.y + 18) : 1992;
  let nomeInp = null;
  if (f.tipo === 'altro') {
    nomeInp = el('input', { class: 'campo', id: 'agg-nome', required: true, maxlength: 60, placeholder: 'Es. Suppletive Senato', list: 'tipi-altro' });
    form.append(el('div', {}, el('label', { class: 'etichetta', for: 'agg-nome' }, 'Nome'), nomeInp,
      el('datalist', { id: 'tipi-altro' }, ['Suppletive Camera', 'Suppletive Senato', 'Provinciali', 'Municipio', 'Referendum comunale', 'Primarie'].map(t => el('option', { value: t })))));
  }
  const d1 = el('input', { type: 'date', class: 'campo', id: 'agg-d1', required: true, min: `${annoMin}-01-01`, max: OGGI_ISO });
  form.append(el('div', {}, el('label', { class: 'etichetta', for: 'agg-d1' }, f.tipo === 'com' ? `Data delle comunali a ${res.comune.nome}` : 'Data del voto'), d1));
  let chk = null, d2 = null;
  if (f.tipo === 'com') {
    const turni = TURNI_COMUNALI.filter(t => t.d >= `${annoMin}-01-01` && t.d <= OGGI_ISO).reverse();
    const sa = el('select', { class: 'campo', id: 'agg-turno' });
    sa.append(el('option', { value: '' }, 'Scegli il turno…'));
    turni.forEach((t, i) => sa.append(el('option', { value: i }, `${MESI[+t.d.slice(5, 7) - 1]} ${t.d.slice(0, 4)}`)));
    sa.append(el('option', { value: 'x' }, 'Altra data (turno straordinario o regione a statuto speciale)'));
    sa.addEventListener('change', () => {
      const t = turni[sa.value];
      f.turno = t || null;
      if (t) { d1.value = t.d; d2.value = t.b; }
    });
    d1.addEventListener('input', () => { f.turno = null; });
    form.prepend(el('div', {}, el('label', { class: 'etichetta', for: 'agg-turno' }, 'Turno ordinario (riempie le date)'), sa));
    d2 = el('input', { type: 'date', class: 'campo', id: 'agg-d2', min: `${annoMin}-01-01`, max: OGGI_ISO, disabled: true });
    chk = el('input', { type: 'checkbox', id: 'agg-bal', onchange: () => { d2.disabled = !chk.checked; d2.required = chk.checked; } });
    form.append(el('label', { class: 'chk', for: 'agg-bal' }, chk, 'C’è stato il ballottaggio'), el('div', {}, el('label', { class: 'etichetta', for: 'agg-d2' }, 'Data del ballottaggio'), d2));
  }
  form.append(el('div', { class: 'azioni' }, el('button', { class: 'bottone', type: 'submit' }, 'Aggiungi all’elenco'), el('button', { class: 'bottone testuale', type: 'button', onclick: () => { formAperto = null; disegnaForm(); } }, 'Annulla')));
  form.addEventListener('submit', ev => {
    ev.preventDefault();
    if (f.tipo === 'com') {
      const t = f.turno && f.turno.d === d1.value ? f.turno : null;
      stato.extra.push({ id: ++seq, tipo: 'com', resId: f.resId, d: d1.value, d2: t ? t.d2 : null });
      if (chk.checked && d2.value) stato.extra.push({ id: ++seq, tipo: 'bal', resId: f.resId, d: d2.value, d2: t && t.b === d2.value ? t.b2 : null });
    } else {
      stato.extra.push({ id: ++seq, tipo: 'altro', nome: nomeInp.value.trim(), d: d1.value });
    }
    formAperto = null; disegnaForm(); aggiorna();
    annuncia('Elezione aggiunta all’elenco.');
  });
  box.append(form);
}

// ===== Emiciclo: un pallino per ogni consultazione =====
// Disposizione a file concentriche, come nei grafici dei seggi; ordine da sinistra a destra.
function postiEmiciclo(N, R) {
  if (!N) return { posti: [], raggio: 0 };
  const file = N <= 9 ? 1 : N <= 26 ? 2 : N <= 50 ? 3 : 4;
  const passo = R * (file > 2 ? 0.17 : 0.2);
  const raggi = Array.from({ length: file }, (_, j) => R - (file - 1 - j) * passo);
  const somma = raggi.reduce((a, b) => a + b, 0);
  const n = raggi.map(r => Math.max(1, Math.round(N * r / somma)));
  n[file - 1] += N - n.reduce((a, b) => a + b, 0);
  const posti = [];
  let raggio = R * 0.11;
  raggi.forEach((r, j) => {
    if (n[j] > 1) raggio = Math.min(raggio, (Math.PI * r / (n[j] - 1)) / 2.5);
    for (let k = 0; k < n[j]; k++) {
      const th = n[j] === 1 ? Math.PI / 2 : Math.PI - k * Math.PI / (n[j] - 1);
      posti.push({ x: r * Math.cos(th), y: -r * Math.sin(th), th, r });
    }
  });
  raggio = Math.min(raggio, passo / 2.25);
  posti.sort((p, q) => (q.th - p.th) || (p.r - q.r));
  return { posti, raggio };
}

function disegnaCalendario() {
  const box = $('#calendario');
  if (!box) return;
  const naz = NAZIONALI.filter(e => e.d <= OGGI_ISO).sort((a, b) => a.d.localeCompare(b.d));
  const R = 250, { posti, raggio } = postiEmiciclo(naz.length, R);
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', `${-R - 20} ${-R - 20} ${2 * R + 40} ${R + 76}`);
  svg.setAttribute('aria-hidden', 'true');
  posti.forEach((p, i) => {
    const c = document.createElementNS(ns, 'circle');
    c.setAttribute('cx', p.x.toFixed(1)); c.setAttribute('cy', p.y.toFixed(1)); c.setAttribute('r', raggio.toFixed(1));
    c.setAttribute('class', naz[i].t);
    c.style.setProperty('--i', i);
    const t = document.createElementNS(ns, 'title'); t.textContent = `${naz[i].s}, ${dataLunga(naz[i].d, naz[i].d2)}`; c.append(t);
    svg.append(c);
  });
  const num = document.createElementNS(ns, 'text');
  num.setAttribute('class', 'grande'); num.setAttribute('x', 0); num.setAttribute('y', -4); num.setAttribute('text-anchor', 'middle');
  num.textContent = String(naz.length);
  const sotto = document.createElementNS(ns, 'text');
  sotto.setAttribute('class', 'grande-sotto'); sotto.setAttribute('x', 0); sotto.setAttribute('y', 46); sotto.setAttribute('text-anchor', 'middle');
  sotto.textContent = `consultazioni nazionali dal 1992 a oggi`;
  svg.append(num, sotto);
  box.replaceChildren(svg);
}

// ===== Immagine =====
const W = 1080;
const TIT = '"Bodoni Moda", "Bodoni 72", Didot, Georgia, serif';
const TXT = '"Titillium Web", "Segoe UI", system-ui, sans-serif';
const C = { ink: '#161B26', grigio: '#5A6372', filo: '#E1E4E9', velo: '#F3F4F6', contorno: '#C3C8D2', verde: '#008C45', verdeScuro: '#00753A', rosso: '#CD212A' };

function indirizzoPagina() {
  if (PIEDE_IMMAGINE) return PIEDE_IMMAGINE;
  if (/^https?:$/.test(location.protocol)) return (location.host + location.pathname).replace(/\/(index\.html)?$/, '');
  return 'angrisanidj.github.io/la-mia-storia-di-voto';
}

function righeImmagine() {
  const vuote = $('#opt-vuote').checked, non = $('#opt-non').checked, dataPiena = $('#opt-date').checked;
  const out = [];
  let n = 0;
  for (const o of elenco) {
    const st = statoDi(o);
    if (st === 'escl') continue;
    const r = risposta(o.key);
    const testo = st === 'non' ? 'Non ho votato' : r.testo.trim();
    if (st === 'non' && !non) continue;
    if (st === 'ok' && !testo && !vuote) continue;
    n++;
    out.push({ n, anno: o.d.slice(0, 4), quando: dataPiena ? dataBreve(o.d) : o.d.slice(0, 4), giorno: dataLunga(o.d, o.d2).replace(/ \d{4}$/, ''), etichetta: o.etichetta, testo, non: st === 'non', colore: coloreVoto(o) });
  }
  return out;
}

// Spezza un testo in token: parole e simboli noti
function tokenizza(s) {
  const out = [];
  const re = new RegExp(`(${SEGNI.map(x => x.e).join('|')})️?`, 'gu');
  let ult = 0, m;
  while ((m = re.exec(s))) {
    if (m.index > ult) out.push(...parole(s.slice(ult, m.index)));
    out.push({ segno: SEGNO_DA_EMOJI[m[1]] });
    ult = re.lastIndex;
  }
  if (ult < s.length) out.push(...parole(s.slice(ult)));
  return out;
}
function parole(s) { return s.split(/(\s+)/).filter(Boolean).map(t => ({ t })); }

// Impagina una sequenza di token entro una larghezza; restituisce le linee
function impagina(ctx, toks, larg, fs) {
  const linee = [[]]; let x = 0;
  for (const t of toks) {
    ctx.font = t.f;
    const w = t.segno ? fs * 1.12 : ctx.measureText(t.t).width;
    if (t.t && /^\s+$/.test(t.t)) { if (x === 0) continue; linee[linee.length - 1].push({ ...t, w }); x += w; continue; }
    if (x + w > larg && x > 0) {
      const ult = linee[linee.length - 1];
      while (ult.length && ult[ult.length - 1].t && /^\s+$/.test(ult[ult.length - 1].t)) ult.pop();
      linee.push([]); x = 0;
    }
    linee[linee.length - 1].push({ ...t, w }); x += w;
  }
  return linee;
}
function scriviLinea(ctx, linea, x, y, fs) {
  for (const t of linea) {
    if (t.segno) disegnaSegno(ctx, t.segno, x + fs * 0.56, y - fs * 0.34, fs * 0.46);
    else { ctx.font = t.f; ctx.fillStyle = t.c; ctx.fillText(t.t, x, y); }
    x += t.w;
  }
}
function tondo(ctx, cx, cy, r, colore, bordo, spessore = 2) {
  ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.fillStyle = colore; ctx.fill();
  if (bordo) { ctx.lineWidth = spessore; ctx.strokeStyle = bordo; ctx.stroke(); }
}

function titoloAutomatico(righe) {
  const tot = righe.length, voti = righe.filter(r => !r.non).length;
  if (!tot) return 'La mia storia di voto';
  if (voti === tot) return voti === 1 ? 'Ho votato una volta' : `Ho votato ${voti} volte`;
  return `Ho votato ${voti} ${voti === 1 ? 'volta' : 'volte'} su ${tot}`;
}

// Formati dell'immagine personale. sicuro = margini in alto e in basso coperti dall'interfaccia delle storie.
const FORMATI = {
  lista: { W: 1080, H: 0, nome: 'Lista completa', file: 'lista' },
  post: { W: 1080, H: 1350, nome: 'Instagram post', file: 'instagram-post' },
  storia: { W: 1080, H: 1920, nome: 'Storie', file: 'storia', sicuro: [190, 250] },
  x: { W: 1600, H: 900, nome: 'X', file: 'x', orizzontale: true },
  quadrata: { W: 1080, H: 1080, nome: 'Quadrata', file: 'quadrata' },
};
let formatoScelto = 'lista';

// Misura ogni voce dell'elenco a una data scala, piena (etichetta sopra, voto sotto) o compatta (una riga sola)
function misuraVoci(ctx, righe, s, larg, compatta, dataPiena) {
  const fsE = 25 * s, fsV = 31 * s;
  return righe.map(r => {
    const et = (dataPiena ? r.giorno + ' · ' : '') + r.etichetta;
    const fE = `600 ${fsE}px ${TXT}`, fV = r.non ? `400 ${fsV}px ${TXT}` : `700 ${fsV}px ${TXT}`;
    const tokV = r.testo ? tokenizza(r.testo).map(t => ({ ...t, f: fV, c: r.non ? C.grigio : C.ink })) : [];
    if (compatta) {
      const fC = `600 ${fsV * 0.86}px ${TXT}`;
      const toks = [...parole(et + (r.testo ? ':' : '')).map(t => ({ ...t, f: fC, c: C.grigio })), ...(r.testo ? [{ t: ' ', f: fC, c: C.grigio }] : []),
        ...tokV.map(t => ({ ...t, f: t.f.replace(`${fsV}px`, `${fsV * 0.9}px`) }))];
      const l = impagina(ctx, toks, larg, fsV * 0.9);
      return { r, righeV: l, lhV: 37 * s, fsV: fsV * 0.9, righeE: [], lhE: 0, h: l.length * 37 * s + 16 * s, attacco: 25 * s };
    }
    const lE = impagina(ctx, parole(et).map(t => ({ ...t, f: fE, c: C.grigio })), larg, fsE);
    const lV = tokV.length ? impagina(ctx, tokV, larg, fsV) : [];
    return { r, righeE: lE, lhE: 32 * s, fsE, righeV: lV, lhV: 41 * s, fsV, h: lE.length * 32 * s + (lV.length ? 6 * s : 0) + lV.length * 41 * s + 28 * s, attacco: 27 * s };
  });
}

// Distribuisce le voci in colonne dentro un'area; restituisce le colonne e quante voci sono rimaste fuori
function inColonne(voci, area, s, colonne) {
  const gapCol = 44 * s, colW = (area.w - (colonne - 1) * gapCol) / colonne;
  const out = Array.from({ length: colonne }, () => []);
  let c = 0, y = 0, annoPrec = null, messe = 0;
  for (const v of voci) {
    const nuovoAnno = v.r.anno !== annoPrec;
    const salto = nuovoAnno && y > 0 ? 18 * s : 0;
    if (y + salto + v.h > area.h + 0.5) {
      c++; y = 0; annoPrec = null;
      if (c >= colonne) break;
    }
    const inizio = y === 0;
    const sep = !inizio && v.r.anno !== annoPrec;
    y += sep ? 18 * s : 0;
    out[c].push({ ...v, y, mostraAnno: inizio || v.r.anno !== annoPrec, sep });
    y += v.h; annoPrec = v.r.anno; messe++;
  }
  return { colonne: out, colW, gapCol, messe };
}

function scegliImpaginazione(ctx, righe, area, dataPiena, maxColonne) {
  let meglio = null;
  for (const compatta of [false, true]) {
    for (const s of [1, 0.92, 0.84, 0.76, 0.68, 0.6, 0.54, 0.48]) {
      for (let col = 1; col <= maxColonne; col++) {
        const colW = (area.w - (col - 1) * 44 * s) / col;
        if (colW < 330 * s || colW < 270) continue;
        const voci = misuraVoci(ctx, righe, s, colW - 168 * s, compatta, dataPiena);
        const disp = inColonne(voci, area, s, col);
        if (disp.messe === righe.length) {
          const voto = s - (compatta ? 0.16 : 0) - (col - 1) * 0.04;
          if (!meglio || voto > meglio.voto) meglio = { ...disp, s, compatta, voto, resto: 0 };
        }
      }
    }
  }
  if (meglio) return meglio;
  // non entra tutto: la versione più fitta, con l'indicazione di quante voci mancano
  const s = 0.48;
  let col = Math.max(1, maxColonne);
  while (col > 1 && (area.w - (col - 1) * 44 * s) / col < 270) col--;
  const colW = (area.w - (col - 1) * 44 * s) / col;
  const voci = misuraVoci(ctx, righe, s, colW - 168 * s, true, dataPiena);
  const disp = inColonne(voci, { ...area, h: area.h - 44 * s }, s, col);
  return { ...disp, s, compatta: true, resto: righe.length - disp.messe };
}

function disegnaEmicicloCard(ctx, cx, cy, R, righe, s) {
  const { posti, raggio } = postiEmiciclo(righe.length, R);
  if (posti.length) {
    posti.forEach((p, i) => {
      const k = righe[i].colore || { c: '#fff', b: C.contorno };
      tondo(ctx, cx + p.x, cy + p.y, raggio, k.c, k.vuoto || k.c === '#FFFFFF' ? (k.b || C.contorno) : null, 2 * s);
    });
  } else {
    postiEmiciclo(24, R).posti.forEach(p => tondo(ctx, cx + p.x, cy + p.y, R * 0.045, '#fff', C.contorno, 1.6));
  }
  ctx.textAlign = 'center'; ctx.fillStyle = C.ink; ctx.font = `700 ${(righe.length > 99 ? 54 : 68) * s}px ${TIT}`;
  ctx.fillText(String(righe.length), cx, cy - 4 * s);
  ctx.fillStyle = C.grigio; ctx.font = `400 ${21 * s}px ${TXT}`;
  ctx.fillText(righe.length === 1 ? 'consultazione' : 'consultazioni', cx, cy + 30 * s);
  ctx.textAlign = 'left';
}

function disegnaLista(ctx, imp, area) {
  const s = imp.s;
  imp.colonne.forEach((col, c) => {
    if (!col.length) return;
    const x = area.x + c * (imp.colW + imp.gapCol);
    const xLinea = x + 136 * s, xTesto = x + 168 * s, dx = x + imp.colW;
    const yP = v => area.y + v.y + (imp.compatta ? 14 * s : 19 * s);
    if (col.length > 1) { const y1 = yP(col[0]), y2 = yP(col[col.length - 1]); rr(ctx, xLinea - 2.5 * s, y1, 5 * s, y2 - y1, 2.5 * s); ctx.fillStyle = C.verde; ctx.fill(); }
    col.forEach(v => {
      const y = area.y + v.y;
      if (v.sep) { ctx.fillStyle = C.filo; ctx.fillRect(xTesto, y - 22 * s + (imp.compatta ? 6 * s : 0), dx - xTesto, 1.5); }
      if (v.mostraAnno) { ctx.font = `700 ${(imp.compatta ? 34 : 40) * s}px ${TIT}`; ctx.fillStyle = C.verdeScuro; ctx.fillText(v.r.anno, x, y + (imp.compatta ? 26 : 29) * s); }
      const k = v.r.colore || { c: '#fff', b: C.contorno };
      const r0 = imp.compatta ? 10 * s : 12 * s;
      tondo(ctx, xLinea, yP(v), r0 + 4 * s, '#fff');
      tondo(ctx, xLinea, yP(v), r0, k.c, k.vuoto || k.c === '#FFFFFF' ? k.b : null, 2.5 * s);
      let yy = y + v.attacco;
      v.righeE.forEach(l => { scriviLinea(ctx, l, xTesto, yy, v.fsE); yy += v.lhE; });
      if (v.righeE.length && v.righeV.length) yy += 6 * s;
      v.righeV.forEach(l => { scriviLinea(ctx, l, xTesto, yy, v.fsV); yy += v.lhV; });
    });
  });
  if (imp.resto) {
    ctx.font = `600 ${26 * s * 1.3}px ${TXT}`; ctx.fillStyle = C.grigio;
    ctx.fillText(`… e altre ${imp.resto} ${imp.resto === 1 ? 'consultazione' : 'consultazioni'}`, area.x + 168 * s, area.y + area.h - 6);
  }
}

function disegnaPiede(ctx, x, y, W, m, s = 1) {
  ctx.fillStyle = C.filo; ctx.fillRect(m, y - 62 * s, W - 2 * m, 2);
  ctx.font = `700 ${27 * s}px ${TXT}`;
  const testoP = 'Crea la tua', wP = ctx.measureText(testoP).width + 64 * s;
  rr(ctx, x, y - 30 * s, wP, 60 * s, 30 * s); ctx.fillStyle = C.verdeScuro; ctx.fill();
  ctx.fillStyle = '#fff'; ctx.textBaseline = 'middle'; ctx.fillText(testoP, x + 32 * s, y);
  ctx.font = `600 ${27 * s}px ${TXT}`; ctx.fillStyle = C.ink;
  ctx.fillText(indirizzoPagina(), x + wP + 28 * s, y);
  ctx.textBaseline = 'alphabetic';
}
function nastroEMarchio(ctx, W, m, yM, s = 1) {
  ctx.fillStyle = C.verde; ctx.fillRect(0, 0, W / 3, 16);
  ctx.fillStyle = C.rosso; ctx.fillRect(W * 2 / 3, 0, W / 3, 16);
  ctx.fillStyle = C.filo; ctx.fillRect(0, 16, W, 2);
  ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left';
  tondo(ctx, m + 9 * s, yM - 11 * s, 9 * s, C.verde); tondo(ctx, m + 33 * s, yM - 11 * s, 8 * s, '#fff', C.contorno); tondo(ctx, m + 57 * s, yM - 11 * s, 9 * s, C.rosso);
  ctx.fillStyle = C.ink; ctx.font = `700 ${34 * s}px ${TIT}`; ctx.fillText('La mia storia di voto', m + 82 * s, yM);
}

let ultimoResto = 0;
function disegna(cv, righe, formato = formatoScelto) {
  ultimoResto = 0;
  const F = FORMATI[formato] || FORMATI.lista;
  const ctx = cv.getContext('2d');
  const W = F.W;
  const titolo = $('#titolo').value.trim() || titoloAutomatico(righe);
  const firma = $('#firma').value.trim();
  const dataPiena = $('#opt-date').checked;
  cv.width = W; cv.height = F.H || 1350;

  if (F.orizzontale) {
    // X: testata a sinistra, elenco a destra
    const H = F.H, m = 72, colSx = righe.length > 24 ? 430 : 540;
    ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, W, H);
    nastroEMarchio(ctx, W, m, 92);
    let corpo = 64, linee;
    for (const c of [66, 60, 54, 48, 42]) { corpo = c; ctx.font = `700 ${c}px ${TIT}`; linee = righeBilanciate(ctx, titolo, colSx); if (linee.length <= 2) break; }
    if (linee.length > 2) linee = righeTesto(ctx, titolo, colSx);
    ctx.fillStyle = C.ink; ctx.font = `700 ${corpo}px ${TIT}`;
    linee.forEach((l, i) => ctx.fillText(l, m, 190 + corpo * 0.6 + i * corpo * 1.1));
    let yF = 190 + corpo * 0.6 + (linee.length - 1) * corpo * 1.1;
    if (firma) { ctx.font = `600 28px ${TXT}`; ctx.fillStyle = C.grigio; ctx.fillText(firma, m, yF + 50); }
    disegnaEmicicloCard(ctx, m + colSx / 2, H - 205, colSx > 500 ? 165 : 145, righe, colSx > 500 ? 1.05 : 0.95);
    ctx.fillStyle = C.filo; ctx.fillRect(m + colSx + 40, 70, 2, H - 210);
    const area = { x: m + colSx + 80, y: 74, w: W - m - (m + colSx + 80), h: H - 74 - 150 };
    const imp = righe.length ? scegliImpaginazione(ctx, righe, area, dataPiena, 3) : null;
    if (imp) ultimoResto = imp.resto;
    if (imp) disegnaLista(ctx, imp, area);
    else { ctx.font = `400 26px ${TXT}`; ctx.fillStyle = C.grigio; ctx.fillText('Segna come hai votato per vedere qui la tua storia.', area.x, area.y + 40); }
    disegnaPiede(ctx, m, H - 52, W, m);
    return;
  }

  // Formati verticali e quadrato
  const m = 84, larg = W - 2 * m;
  const [alto, basso] = F.sicuro || [0, 0];
  const hs = formato === 'quadrata' ? 0.84 : 1;
  const R = 136 * hs, emiW = 2 * R + 20;
  const colTit = larg - emiW - 36;
  let corpo = 74, lineeTit;
  for (const c of [76, 68, 60, 54, 48].map(v => v * hs)) {
    corpo = c; ctx.font = `700 ${c}px ${TIT}`;
    lineeTit = righeBilanciate(ctx, titolo, colTit);
    if (lineeTit.length <= 2) break;
  }
  const yM = alto + 106 * hs;
  const yTit0 = alto + 196 * hs;
  let yTesta = yTit0 + corpo * 0.92 + (lineeTit.length - 1) * corpo * 1.1;
  if (firma) yTesta += 52 * hs;
  const fineTesta = Math.max(yTesta, alto + 168 * hs + R + 40 * hs) + 44 * hs;
  const piede = 150;
  const area = { x: m, y: fineTesta + 26 * hs, w: larg, h: 0 };
  let imp = null, H = F.H;
  if (!F.H) {
    // lista completa: altezza libera, una colonna a grandezza piena
    const voci = misuraVoci(ctx, righe, 1, larg - 168, false, dataPiena);
    const tot = voci.reduce((a, v, i) => a + v.h + (i && v.r.anno !== voci[i - 1].r.anno ? 18 : 0), 0);
    area.h = tot;
    imp = righe.length ? { ...inColonne(voci, { ...area, h: tot + 1 }, 1, 1), s: 1, compatta: false, resto: 0 } : null;
    H = Math.max(1350, Math.ceil(area.y + (righe.length ? tot : 90) + piede));
  } else {
    area.h = H - basso - piede - area.y;
    imp = righe.length ? scegliImpaginazione(ctx, righe, area, dataPiena, 3) : null;
    if (imp) ultimoResto = imp.resto;
  }
  cv.width = W; cv.height = H;
  ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, W, H);
  nastroEMarchio(ctx, W, m, yM, hs);
  ctx.font = `700 ${corpo}px ${TIT}`; ctx.fillStyle = C.ink;
  lineeTit.forEach((l, i) => ctx.fillText(l, m, yTit0 + corpo * 0.92 + i * corpo * 1.1));
  if (firma) { ctx.font = `600 ${30 * hs}px ${TXT}`; ctx.fillStyle = C.grigio; ctx.fillText(firma, m, yTesta - 4 * hs); }
  disegnaEmicicloCard(ctx, W - m - R - 10, alto + 168 * hs + R, R, righe, hs);
  ctx.fillStyle = C.filo; ctx.fillRect(m, fineTesta - 22 * hs, larg, 2);
  if (imp) disegnaLista(ctx, imp, area);
  else { ctx.font = `400 28px ${TXT}`; ctx.fillStyle = C.grigio; ctx.fillText('Segna come hai votato per vedere qui la tua storia.', m, area.y + 30); }
  disegnaPiede(ctx, m, H - basso - 78, W, m);
}
// Su due righe sceglie il punto di a capo che rende le righe più simili (niente parola orfana)
function righeBilanciate(ctx, testo, larghezza) {
  const base = righeTesto(ctx, testo, larghezza);
  if (base.length !== 2) return base;
  const p = testo.split(' ');
  let meglio = base, peggio = Infinity;
  for (let i = 1; i < p.length; i++) {
    const a = p.slice(0, i).join(' '), b = p.slice(i).join(' ');
    const wa = ctx.measureText(a).width, wb = ctx.measureText(b).width;
    if (wa > larghezza || wb > larghezza) continue;
    const mx = Math.max(wa, wb);
    if (mx < peggio) { peggio = mx; meglio = [a, b]; }
  }
  return meglio;
}
function righeTesto(ctx, testo, larghezza) {
  const out = []; let riga = '';
  testo.split(' ').forEach(p => {
    const prova = riga ? riga + ' ' + p : p;
    if (ctx.measureText(prova).width > larghezza && riga) { out.push(riga); riga = p; } else riga = prova;
  });
  if (riga) out.push(riga);
  return out;
}
function disegnaSegno(ctx, s, cx, cy, r) {
  ctx.save();
  if (s.tipo === 'si') {
    const l = r * 1.9; rr(ctx, cx - l / 2, cy - l / 2, l, l, l * 0.22); ctx.fillStyle = C.verde; ctx.fill();
    ctx.strokeStyle = '#fff'; ctx.lineWidth = r * 0.3; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.beginPath(); ctx.moveTo(cx - r * 0.5, cy + r * 0.05); ctx.lineTo(cx - r * 0.13, cy + r * 0.42); ctx.lineTo(cx + r * 0.55, cy - r * 0.35); ctx.stroke();
  } else if (s.tipo === 'no') {
    ctx.strokeStyle = C.rosso; ctx.lineWidth = r * 0.42; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(cx - r * 0.68, cy - r * 0.68); ctx.lineTo(cx + r * 0.68, cy + r * 0.68); ctx.moveTo(cx + r * 0.68, cy - r * 0.68); ctx.lineTo(cx - r * 0.68, cy + r * 0.68); ctx.stroke();
  } else {
    tondo(ctx, cx, cy, r * 0.9, s.c, s.c === '#FFFFFF' ? '#9AA2AF' : null, 2);
  }
  ctx.restore();
}
function rr(ctx, x, y, w, h, r) { ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }

const fontPronti = document.fonts && document.fonts.load
  ? Promise.all([`700 40px "Bodoni Moda"`, `400 24px "Titillium Web"`, `600 24px "Titillium Web"`, `700 24px "Titillium Web"`].map(f => document.fonts.load(f))).catch(() => {})
  : Promise.resolve();
let timer = null;
function programmaAnteprima() {
  clearTimeout(timer);
  timer = setTimeout(() => fontPronti.then(() => {
    disegna($('#tela'), righeImmagine());
    const n = $('#nota-formato');
    if (n) {
      n.hidden = !ultimoResto;
      n.textContent = ultimoResto ? `In questo formato ${ultimoResto === 1 ? 'resta fuori una consultazione' : `restano fuori ${ultimoResto} consultazioni`}: per averle tutte scegli «Lista completa» o «Storie».` : '';
    }
  }), 120);
}

const URL_SITO = 'https://angrisanidj.github.io/la-mia-storia-di-voto/';
function indirizzoLink() { return /^https?:$/.test(location.protocol) ? location.origin + location.pathname.replace(/index\.html$/, '') : URL_SITO; }
function testoSemplice() {
  const righe = righeImmagine();
  const t = $('#titolo').value.trim() || titoloAutomatico(righe);
  return [t + ' 🇮🇹', '', ...righe.map(r => `${r.n}- ${r.quando}/${r.etichetta}${r.testo ? ': ' + r.testo : ''}`), '', 'Ricostruisci la tua: ' + indirizzoLink()].join('\n');
}
function annuncia(t) { $('#annuncio').textContent = t; }
function copia(t, fatto) {
  const riserva = () => {
    const ta = el('textarea', { class: 'solo-lettori' }); ta.value = t; document.body.append(ta); ta.select();
    let ok = false; try { ok = document.execCommand('copy'); } catch (e) { /* niente */ }
    ta.remove();
    annuncia(ok ? fatto : 'Copia non riuscita: il browser ha bloccato l’accesso agli appunti.');
  };
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(() => annuncia(fatto), riserva);
  else riserva();
}
// sui telefoni si apre il menu di condivisione del sistema; altrove il link va negli appunti
const MENU_CONDIVISIONE = !!navigator.share && !!window.matchMedia && window.matchMedia('(pointer: coarse)').matches;
function condividiLink() {
  const url = indirizzoLink(), fatto = 'Link copiato negli appunti.';
  if (!MENU_CONDIVISIONE) { copia(url, fatto); return; }
  navigator.share({ title: 'La mia storia di voto', text: 'Dal 1992 a oggi, quante volte ti hanno chiamato alle urne? Ricostruisci la tua storia di voto.', url })
    .then(() => annuncia(''), e => { if (!e || e.name !== 'AbortError') copia(url, fatto); });
}
function nomeFile(ext) { return `la-mia-storia-di-voto-${FORMATI[formatoScelto].file}.${ext}`; }
async function generaBlob(tipo = 'image/png') {
  await fontPronti;
  const cv = document.createElement('canvas'); disegna(cv, righeImmagine(), formatoScelto);
  return new Promise(res => cv.toBlob(res, tipo, 0.92));
}
async function scarica(jpg) {
  const blob = await generaBlob(jpg ? 'image/jpeg' : 'image/png');
  if (!blob) { annuncia('Immagine non creata: riprova.'); return; }
  const url = URL.createObjectURL(blob);
  const a = el('a', { href: url, download: nomeFile(jpg ? 'jpg' : 'png') }); document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
  annuncia(`Immagine scaricata: ${FORMATI[formatoScelto].nome}, ${jpg ? 'JPG' : 'PNG'}.`);
}

// ===== Avvio =====
function aggiorna(ricalcola = true) {
  if (ricalcola) elenco = calcola();
  controllaResidenze();
  disegnaElenco();
  programmaAnteprima();
}
function init() {
  initNascita();
  disegnaResidenze();
  disegnaCalendario();
  $('#agg-res').addEventListener('click', () => { stato.residenze.push({ id: ++seq, comune: null, y: null, m: null }); disegnaResidenze(); const ins = document.querySelectorAll('#residenze input'); ins[ins.length - 1].focus(); });
  ['#titolo', '#firma'].forEach(s => $(s).addEventListener('input', programmaAnteprima));
  ['#opt-vuote', '#opt-non', '#opt-date'].forEach(s => $(s).addEventListener('change', programmaAnteprima));
  document.querySelectorAll('input[name=formato]').forEach(r => r.addEventListener('change', () => { formatoScelto = r.value; programmaAnteprima(); }));
  $('#scarica').addEventListener('click', () => scarica(false));
  $('#scarica-jpg').addEventListener('click', () => scarica(true));
  $('#copia-link').addEventListener('click', condividiLink);
  if (MENU_CONDIVISIONE) $('#copia-link').textContent = 'Condividi il link';
  $('#copia').addEventListener('click', () => copia(testoSemplice(), 'Risultato copiato negli appunti.'));
  try {
    if (navigator.canShare && navigator.canShare({ files: [new File([new Blob()], 'x.png', { type: 'image/png' })] })) {
      $('#condividi').hidden = false;
      $('#condividi').addEventListener('click', async () => {
        const blob = await generaBlob();
        try { await navigator.share({ files: [new File([blob], nomeFile('png'), { type: 'image/png' })] }); annuncia(''); } catch (e) { /* annullato */ }
      });
    }
  } catch (e) { /* condivisione di file non disponibile */ }
  aggiorna();
}
init();
