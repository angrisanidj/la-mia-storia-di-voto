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
    const { res } = residenzaIn(e.d);
    const estero = res && res.comune === ESTERO;
    const reg = res && !estero ? regioneDi(res.comune, e.d) : null;
    if (estero) {
      if (e.t === 'pol' && e.d >= '2006-01-01') note.push('Da residente all’estero votavi per corrispondenza le liste della circoscrizione Estero.');
      else if (e.t === 'pol' || e.t === 'eur') note.push('Eri residente all’estero: per votare dovevi rientrare in Italia, salvo il voto per corrispondenza dove previsto.');
      else note.push('Eri residente all’estero: votavi per corrispondenza.');
    }
    if (e.t !== 'pol') {
      const descr = e.t === 'ref' ? e.l + (e.q > 1 ? ` (${e.q} quesiti)` : '') : 'Parlamento europeo';
      push({ key: `N:${e.d}:${e.t}`, d: e.d, d2: e.d2, tipo: e.t, qk: e.d, etichetta: e.s, descr, q: e.q, note });
      continue;
    }
    // Politiche: Camera e Senato sono due schede, e il voto può essere diverso
    const gruppo = `pol-${e.d}`;
    const vda = reg === '02' ? ['In Valle d’Aosta si vota un candidato nel collegio uninominale della regione.'] : [];
    const noteC = [...note, ...vda];
    const e25 = e.d < '2022-01-01' ? eta(e.d, 25) : 'si';
    if (e25 === 'no') noteC.push('Per il Senato servivano 25 anni: non potevi ancora votarlo.');
    push({ key: `N:${e.d}:pol`, d: e.d, d2: e.d2, tipo: 'pol', ramo: 'C', gruppo, estero, reg, etichetta: 'Politiche (Camera)', descr: 'Camera dei deputati', note: noteC });
    if (e25 !== 'no') {
      const noteS = [...note, ...vda];
      if (reg === '04' && e.d >= '2006-01-01' && e.d < '2018-01-01') noteS.push('In Trentino-Alto Adige al Senato si votava un candidato nel collegio uninominale.');
      if (e25 === 'forse') noteS.push(`Per il Senato servivano 25 anni: potevi votarlo solo se li avevi compiuti entro il ${dataLunga(e.d)}.`);
      push({ key: `N:${e.d}:polS`, d: e.d, d2: e.d2, tipo: 'pol', ramo: 'S', gruppo, estero, reg, etichetta: 'Politiche (Senato)', descr: 'Senato della Repubblica', note: noteS });
    }
  }

  // Suppletive: si votava solo nel collegio rimasto senza deputato o senatore
  for (const [d, d2, ramo, collegio, comuni, candidati] of (typeof SUPPLETIVE !== 'undefined' ? SUPPLETIVE : [])) {
    const { res, trasloco } = residenzaIn(d);
    if (!res || !res.comune || res.comune === ESTERO) continue;
    const voce = comuni.find(c => c.slice(0, 4) === res.comune.cod);
    if (!voce) continue;
    const senato = ramo === 'S';
    const e25 = senato && d < '2022-01-01' ? eta(d, 25) : 'si';
    if (e25 === 'no') continue;
    const note = [];
    if (trasloco) note.push('Ti sei trasferito in quel mese: verifica dove eri iscritto.');
    if (e25 === 'forse') note.push(`Per il Senato servivano 25 anni: potevi votare solo se li avevi compiuti entro il ${dataLunga(d)}.`);
    const zona = voce.includes('*') ? voce.slice(5) : null;
    if (voce.includes('*')) note.push(`Il collegio comprendeva solo una parte di ${res.comune.nome}${zona ? ` (${zona})` : ''}: se abitavi lì, segna come hai votato.`);
    push({ key: `S:${ramo}:${d}:${res.comune.cod}`, d, d2, tipo: 'sup', ramo, supp: { collegio, candidati }, reg: regioneDi(res.comune, d), sig: res.comune.sig,
      etichetta: `Suppletive ${senato ? 'Senato' : 'Camera'}`, descr: `Collegio ${collegio}`, note, esclDefault: voce.includes('*') });
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
    aggiungiRegionali(e.d, e.d2, (r, res, trasloco) => {
      if (r !== e.r || (e.p && res.comune.sig !== e.p)) return;
      const note = trasloco ? ['Ti sei trasferito in quel mese: verifica dove eri iscritto.'] : [];
      let escl = false;
      // a Bolzano per i referendum provinciali vale la residenza in regione chiesta per il consiglio provinciale
      if (e.p === 'BZ' && !residenteDa(e.d, 4, '04')) { note.push('Per i referendum provinciali di Bolzano servivano 4 anni di residenza in regione: dai comuni indicati non risultano.'); escl = true; }
      push({ key: `RR:${e.r}${e.p || ''}:${e.d}`, d: e.d, d2: e.d2, tipo: 'ref', qk: `R${e.r}${e.p || ''}-${e.d}`, etichetta: e.s, descr: e.l, note, esclDefault: escl });
    });
  }

  // Comunali dall'Archivio storico delle elezioni (dati/comunali.js), per ogni comune in cui hai vissuto
  const visti = new Set();
  for (const r of residenzeOrdinate()) {
    if (!r.comune || r.comune === ESTERO || visti.has(r.comune.cod)) continue;
    visti.add(r.comune.cod);
    caricaCandidatiComunali(r.comune.reg);
    for (const c of comunaliDi(r.comune.cod)) {
      for (const [d, d2, tipo] of [[c.d, c.d2, 'com'], ...(c.b ? [[c.b, c.b2, 'bal']] : [])]) {
        const att = residenzaIn(d);
        if (!att.res || att.res.comune.cod !== r.comune.cod) continue;
        const note = att.trasloco ? ['Ti sei trasferito in quel mese: verifica dove eri iscritto.'] : [];
        push({ key: `C:${r.comune.cod}:${d}`, d, d2, tipo, reg: regioneDi(r.comune, d), sig: r.comune.sig, cod: r.comune.cod, primo: c.d,
          etichetta: tipo === 'com' ? `Comunali ${r.comune.nome}` : `Ballottaggio comunali ${r.comune.nome}`,
          descr: tipo === 'com' ? 'Sindaco e consiglio comunale' : 'Secondo turno per il sindaco', note });
      }
    }
  }

  // Provinciali dirette 1993-2011 (Trento e Bolzano sono sopra)
  const vistiP = new Set();
  for (const r of residenzeOrdinate()) {
    if (!r.comune || r.comune === ESTERO) continue;
    for (const e of provincialiDi(r.comune)) {
      if (vistiP.has(e.key)) continue;
      const att = residenzaIn(e.d);
      if (!att.res || att.res.comune.cod !== r.comune.cod) continue;
      vistiP.add(e.key);
      const note = att.trasloco ? ['Ti sei trasferito in quel mese: verifica dove eri iscritto.'] : [];
      const reg = regioneDi(r.comune, e.d);
      push({ key: `PR:${e.key}`, d: e.d, tipo: 'com', prov: e.key, reg, sig: e.sig, etichetta: `Provinciali ${e.n}`, descr: 'Presidente e consiglio provinciale', note });
      if (e.b) push({ key: `PRB:${e.key}`, d: piuGiorni(e.d, 14), tipo: 'bal', prov: e.key, reg, sig: e.sig, etichetta: `Ballottaggio provinciali ${e.n}`, descr: 'Secondo turno per il presidente della provincia', note: [] });
    }
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
      reg: res && res.comune ? regioneDi(res.comune, x.d) : null, sig: res && res.comune ? res.comune.sig : null,
      cod: res && res.comune ? res.comune.cod : null, primo: x.primo || x.d };
    if (eta(x.d, 18) === 'no') { o.note.push('A quella data non avevi ancora 18 anni.'); o.esclDefault = true; out.push(o); }
    else push(o);
  }

  out.sort((a, b) => a.d.localeCompare(b.d) || ordineTipo(a.tipo) - ordineTipo(b.tipo) || (a.ramo === 'S') - (b.ramo === 'S'));
  return out;
}
const ordineTipo = t => ({ pol: 0, sup: 0.5, eur: 1, reg: 2, ref: 3, com: 4, bal: 5, altro: 6 }[t] ?? 9);

// ===== Provinciali =====
// Archivio del Ministero (2004-2011, con i comuni di ogni provincia) e Wikipedia (1993-2003, Sicilia e Friuli-Venezia Giulia).
let PROV = null;
function indiceProvinciali() {
  if (PROV) return PROV;
  PROV = { el: new Map(), comuni: new Map(), sigla: new Map() };
  const aggiungi = (v, mappata) => {
    const [key, n, b, c] = v, i = key.indexOf('-'), sig = key.slice(0, i), d = key.slice(i + 1);
    if (['TN', 'BZ', 'AO'].includes(sig)) return;
    // «Monza E Della Brianza» -> «Monza e della Brianza»
    const nome = n.replace(/ (E|Della|Dell'|Di|Del|Delle|Nell')(?= )/g, x => x.toLowerCase());
    PROV.el.set(key, { key, sig, d, n: nome, b: !!b, c, mappata });
  };
  if (typeof PROVINCIALI_WIKI !== 'undefined') PROVINCIALI_WIKI.forEach(v => aggiungi(v, false));
  if (typeof PROVINCIALI !== 'undefined') {
    PROVINCIALI.forEach(v => aggiungi(v, true));
    for (const riga of PROVINCIALI_COMUNI.split('\n')) {
      const [cod, idx] = riga.split(':');
      if (cod) PROV.comuni.set(cod, new Set(idx.split(',').map(i => PROVINCIALI[+i][0])));
    }
  }
  for (const e of PROV.el.values()) { if (!PROV.sigla.has(e.sig)) PROV.sigla.set(e.sig, []); PROV.sigla.get(e.sig).push(e); }
  return PROV;
}
// La provincia di un comune a una data: le province nate dopo tornano alla provincia di prima
const PROVINCE_MADRI_1992 = { BI: 'VC', VB: 'NO', LC: 'CO', LO: 'MI', RN: 'FC', PO: 'FI', KR: 'CZ', VV: 'CZ' };
// Sardegna prima del 2005: quattro province. Le nuove (Olbia-Tempio, Ogliastra, Carbonia-Iglesias, Medio Campidano,
// poi Sud Sardegna) erano parti di Sassari, Nuoro e Cagliari; in più 26 comuni lasciarono la provincia di Nuoro
// (Budoni e San Teodoro, i 10 della Planargia, di Laconi e Genoni, i 14 del Sarcidano e della Barbagia di Seulo).
const EX_NUORO = new Set(['B248', 'I329', 'B068', 'D640', 'E400', 'E825', 'F261', 'H661', 'L006', 'L172', 'F698', 'D968', 'D431',
  'D982', 'E336', 'F981', 'F982', 'F986', 'G122', 'I668', 'L992', 'D430', 'D443', 'H659', 'I707', 'I706']);
const sardaPrima2005 = c => EX_NUORO.has(c.cod) ? 'NU' : ({ SS: 'SS', OT: 'SS', NU: 'NU', OG: 'NU', OR: 'OR' })[c.sig] || 'CA';
function provinciaStorica(c, iso) {
  let s = c.sig;
  if (c.reg === '20' && iso < '2005-05-01') return sardaPrima2005(c);
  const cambio = CAMBI_REGIONE[c.cod];
  if (cambio && iso < cambio[0] && cambio[1] === '11') s = 'PU'; // Valmarecchia, Montecopiolo e Sassofeltrio
  if (iso < '2009-06-01') {
    if (s === 'MB') s = 'MI';
    if (s === 'FM') s = 'AP';
    if (s === 'BT') s = ['E946', 'H839', 'B915'].includes(c.cod) ? 'FG' : 'BA';
  }
  if (iso < '1995-04-01' && PROVINCE_MADRI_1992[s]) s = PROVINCE_MADRI_1992[s];
  return s;
}
function provincialiDi(c) {
  const P = indiceProvinciali(), out = new Map();
  const mappate = P.comuni.get(c.cod);
  if (mappate) for (const k of mappate) { const e = P.el.get(k); if (e) out.set(k, e); }
  // senza l'elenco dei comuni (Wikipedia, o comune non abbinato): la provincia del comune a quella data
  for (const lista of P.sigla.values()) for (const e of lista) {
    if (out.has(e.key) || (e.mappata && mappate)) continue;
    if (provinciaStorica(c, e.d) === e.sig) out.set(e.key, e);
  }
  return [...out.values()];
}

// Comunali di un comune: date dall'archivio; il ballottaggio è la seconda domenica dopo il primo turno
// (salvo le eccezioni con fonte in strumenti/comunali-correzioni.json)
const BALLOTTAGGI_FUORI_REGOLA = { 'E421-2005-05-08': '2005-05-29' }; // Laives 2005: tre settimane dopo
let COMUNALI_MAPPA = null;
function comunaliDi(cod) {
  if (typeof COMUNALI_TXT === 'undefined' || typeof COMUNALI_DATE === 'undefined') return [];
  if (!COMUNALI_MAPPA) {
    COMUNALI_MAPPA = new Map();
    for (const riga of COMUNALI_TXT.split('\n')) { const [c, v] = riga.split(':'); if (c && v) COMUNALI_MAPPA.set(c, v); }
  }
  const v = COMUNALI_MAPPA.get(cod);
  if (!v) return [];
  return v.split(',').map(Number).map(i => {
    const d = COMUNALI_DATE[Math.abs(i) - 1];
    const t = TURNI_COMUNALI.find(x => x.d === d);
    const out = { d, d2: t ? t.d2 : null };
    if (i < 0) { out.b = BALLOTTAGGI_FUORI_REGOLA[`${cod}-${d}`] || (t ? t.b : piuGiorni(d, 14)); out.b2 = t && t.b === out.b ? t.b2 : null; }
    return out;
  });
}
function piuGiorni(iso, n) { const x = new Date(iso + 'T12:00:00Z'); x.setUTCDate(x.getUTCDate() + n); return x.toISOString().slice(0, 10); }
const haComunali = () => typeof COMUNALI_TXT !== 'undefined';

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
  $('#nascita-anno').addEventListener('change', e => { stato.nascita.y = +e.target.value || null; aggiornaAnniTrasferimenti(); aggiorna(); });
}

// Anni proposti per un trasferimento: non prima dei 18 anni, né prima del trasferimento precedente
function primoAnnoTrasferimento(i) {
  let da = stato.nascita.y ? stato.nascita.y + 18 : 1910;
  for (let j = 1; j < i; j++) if (stato.residenze[j] && stato.residenze[j].y) da = Math.max(da, stato.residenze[j].y);
  return Math.min(da, OGGI.getFullYear());
}
function anniTrasferimento(sy, i) {
  const r = stato.residenze[i];
  sy.replaceChildren();
  // un anno già scelto resta tra le voci anche se ora cade prima del limite
  const da = Math.min(primoAnnoTrasferimento(i), r && r.y ? r.y : Infinity);
  opzioniAnni(sy, da, OGGI.getFullYear(), 'Anno');
  sy.value = r && r.y ? r.y : '';
}
function aggiornaAnniTrasferimenti() {
  document.querySelectorAll('#residenze select.anno-trasf').forEach(sy => anniTrasferimento(sy, +sy.dataset.i));
}

function disegnaResidenze() {
  const box = $('#residenze');
  box.replaceChildren();
  stato.residenze.forEach((r, i) => {
    const riga = el('div', { class: 'residenza' });
    riga.append(campoComune(r, i));
    if (i === 0) {
      riga.append(el('div', { class: 'dal-nascita' }, 'da quando eri maggiorenne'));
    } else {
      const sm = el('select', { class: 'campo', 'aria-label': 'Mese del trasferimento' });
      opzioniMesi(sm, 'Mese');
      sm.value = r.m || '';
      sm.addEventListener('change', () => { r.m = +sm.value || null; aggiorna(); });
      const sy = el('select', { class: 'campo anno-trasf', 'aria-label': 'Anno del trasferimento' });
      sy.dataset.i = i;
      anniTrasferimento(sy, i);
      sy.addEventListener('change', () => { r.y = +sy.value || null; aggiornaAnniTrasferimenti(); aggiorna(); });
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
  const ue = coloriUE(r);
  if (ue && ue[0]) return { c: ue[0], b: ue[0] };
  const m = r.testo.match(new RegExp(SEGNI.map(x => x.e).join('|'), 'u'));
  if (m) { const sg = SEGNO_DA_EMOJI[m[0]]; return { c: sg.c, b: sg.c === '#FFFFFF' ? '#9AA2AF' : sg.c }; }
  return r.testo.trim() ? { c: '#5A6372', b: '#5A6372' } : { c: '#fff', b: '#C3C8D2', vuoto: true };
}
// I colori europei dei simboli di una risposta, se il testo è ancora quello scelto dai menu
function coloriUE(r) {
  if (tavolozza !== 'ue' || !r.eu || !r.eu.some(Boolean) || r.testo !== r.testoPos) return null;
  return r.eu;
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
  const attive = new Set(elenco.filter(o => statoDi(o) !== 'escl').map(o => o.gruppo || o.key)).size;
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
// Usate solo quando l'archivio non ha i candidati di quell'elezione (comuni piccoli, dati mancanti)
const COALIZIONI_LOCALI = [
  { b: 'CDX', n: 'Candidato di centrodestra', e: '🔵' },
  { b: 'CSX', n: 'Candidato di centrosinistra', e: '🔴' },
  { b: 'CSX e M5S', n: 'Candidato di centrosinistra e M5S insieme', e: '🔴', da: '2019-01-01' },
  { b: 'M5S', n: 'Candidato del M5S', e: '🟡', da: '2009-10-04' },
  { b: 'Civico', n: 'Candidato civico', e: '🟣' },
];

// ===== Candidati reali (archivio del Ministero e regioni a statuto speciale) =====
const PARTICELLE = new Set(['di', 'del', 'della', 'dei', 'degli', 'delle', 'de', 'da', 'dal', 'e', 'per', 'con', 'in', 'il', 'la', 'le', 'lo', 'gli', 'a', 'al', 'alla', 'nel', 'nella', 'sul', 'sulla']);
// «Sala Giuseppe detto Beppe» -> «Sala Beppe»; «Brichetto Arnaboldi Letizia Maria detta Letizia Moratti» -> «Letizia Moratti».
// Senza «detto» resta l'ordine dell'archivio (cognome nome): rigirarlo spezzerebbe i cognomi composti.
const PARTICELLE_COGNOME = new Set(['de', 'di', 'da', 'del', 'della', 'dalla', 'dal', 'dei', 'degli', 'delle', 'lo', 'la', 'li', 'le', 'd', 'dell', 'mac', 'van', 'von']);
function nomeConosciuto(t) {
  const m = (t || '').match(/^(.*?)\s*\(?\s*\bdett[oa]\s+([^()]+?)\s*\)?\s*$/i);
  if (!m) return t;
  const alias = m[2].trim(), parole = m[1].trim().split(/\s+/);
  const pa = alias.split(/\s+/);
  if (pa.length >= 2) {
    // «Letizia Moratti» -> «Moratti Letizia», come gli altri nomi dell'archivio (con la particella: «Nando Dalla Chiesa» -> «Dalla Chiesa Nando»)
    if (pa.some(p => norm(p) === 'in')) return alias;
    const j = pa.length >= 3 && PARTICELLE_COGNOME.has(norm(pa[pa.length - 2])) ? pa.length - 2 : pa.length - 1;
    return [...pa.slice(j), ...pa.slice(0, j)].join(' ');
  }
  // cognome da sposata: «Bossi in Moratti» -> Moratti
  const k = parole.findIndex((p, i) => i > 0 && norm(p) === 'in');
  const inizio = k > 0 && k < parole.length - 1 ? k + 1 : 0;
  const cognome = [parole[inizio]];
  for (let i = inizio + 1; i < parole.length - 1 && PARTICELLE_COGNOME.has(norm(parole[i - 1])); i++) cognome.push(parole[i]);
  // il «detto» è una variante del cognome: nome + variante
  const na = norm(alias), nc = norm(cognome.join(' '));
  if (na[0] === nc[0] && na.slice(-4) === nc.slice(-4) && parole[inizio + cognome.length]) return `${alias} ${parole[inizio + cognome.length]}`;
  // stesso ordine dell'archivio (cognome prima), così nei menu i nomi restano coerenti
  return `${cognome.join(' ')} ${alias}`;
}
function titoloNome(t) {
  if (!t || t !== t.toUpperCase()) return t || '';
  return t.toLowerCase().split(/(\s+|-|')/).map((w, i) => (/^\s+$|^-$|^'$/.test(w) || (i > 0 && PARTICELLE.has(w))) ? w : w.charAt(0).toUpperCase() + w.slice(1)).join('')
    .replace(/\b(Pd|Pdl|M5s|Udc|Fdi|Psi|Pci|Pri|Pli|Psdi|Ds|Idv|Sel|Avs|Ppi|Ccd|Cdu|Udeur|Svp|Patt|Mpa|Nsi|Npsi|Ppe|Pse|Psd|Prc|Pdci)\b/g, m => m.toUpperCase());
}
let INDICE_PARTITI = null;
function partitoDaLista(nome) {
  if (!INDICE_PARTITI) {
    INDICE_PARTITI = [];
    const PN = typeof PARTITI_NAZIONALI !== 'undefined' ? PARTITI_NAZIONALI : {};
    for (const el of Object.values(PN)) for (const l of el.liste) {
      INDICE_PARTITI.push([norm(l.n), l]);
      if (l.b && l.b.length > 2) INDICE_PARTITI.push([norm(l.b), l]);
    }
    INDICE_PARTITI.sort((a, b) => b[0].length - a[0].length);
  }
  // abbreviazioni frequenti nell'archivio del Ministero
  const sigla = b => { for (const el of Object.values(typeof PARTITI_NAZIONALI !== 'undefined' ? PARTITI_NAZIONALI : {})) { const l = el.liste.find(x => x.b === b); if (l) return l; } return null; };
  if (/^part\.?\s*democr/i.test(nome) && sigla('PD')) return { ...sigla('PD'), pieno: true };
  if (/^lega\s+(lombarda|veneta|nord|piemont|emilia|toscana|friuli|liguria|trentina)/i.test(nome) && sigla('Lega Nord')) return sigla('Lega Nord');
  if (/^dem(ocratici)?\.?\s*(di\s*)?sin(istra)?\b/i.test(nome) && sigla('DS')) return { ...sigla('DS'), pieno: true };
  if (/\bcen[\s.-]*sin\b|\bcentro[\s-]?sinistra\b/i.test(nome)) return { b: 'Centrosinistra', n: 'Centrosinistra', a: 'centrosinistra' };
  if (/\bcen[\s.-]*des\b|\bcentro[\s-]?destra\b/i.test(nome)) return { b: 'Centrodestra', n: 'Centrodestra', a: 'centrodestra' };
  const k = norm(nome);
  for (const [n, l] of INDICE_PARTITI) if (k === n || (n.length >= 3 && k.startsWith(n + ' '))) return { ...l, pieno: true };
  for (const el of Object.values(typeof PARTITI_NAZIONALI !== 'undefined' ? PARTITI_NAZIONALI : {})) for (const l of el.liste) if (l.b && l.b.length === 2 && k === norm(l.b)) return { ...l, pieno: true };
  for (const [n, l] of INDICE_PARTITI) if (n.length > 8 && k.includes(n)) return l;
  return null;
}
function candidatiReali(o) {
  let grezzi = null;
  if (o.tipo === 'reg') {
    const chiave = o.reg === '04' ? `04-${o.sig === 'BZ' ? 'BZ' : 'TN'}-${o.d}` : `${o.reg}-${o.d}`;
    if (typeof REGIONALI_CANDIDATI !== 'undefined') grezzi = REGIONALI_CANDIDATI[chiave];
    if (!grezzi && typeof REGIONALI_SPECIALI !== 'undefined') grezzi = REGIONALI_SPECIALI[chiave];
  } else if (o.prov) {
    const e = indiceProvinciali().el.get(o.prov);
    grezzi = e ? e.c : null;
  } else if (o.supp) {
    grezzi = o.supp.candidati.map(([nome, pct, partito, area]) => [nome, pct, partito ? [[partito, null]] : [], area]);
  } else if ((o.tipo === 'com' || o.tipo === 'bal') && o.cod && window.CANDIDATI_COMUNALI) {
    grezzi = window.CANDIDATI_COMUNALI[`${o.cod}-${o.primo || o.d}`];
  }
  // la riga dei totali di una tabella non è un candidato
  grezzi = (grezzi || []).filter(([nome]) => !/^\s*totale\b/i.test(nome || ''));
  if (!grezzi.length) return null;
  // nell'archivio alcuni apostrofi arrivano come «?» o carattere sostitutivo
  const pulisci = t => (t || '').replace(/(\p{L})[?\uFFFD\u0092](\p{L})/gu, "$1'$2");
  let out = grezzi.map(([nome, pct, liste, area]) => ({ nome: nome ? titoloNome(nomeConosciuto(pulisci(nome)).replace(/(\p{L})\.(?=\p{L})/gu, '$1. ')).replace(/(^|\s)(de|di|da|del|della|dalla|dal|lo|la|li)(?=\s\p{Lu})/gu, (x, sp, p) => sp + p[0].toUpperCase() + p.slice(1)) : null, pct, area,
    // nell'archivio la somma delle liste compare come riga «Totale coalizione»: non è una lista
    liste: (liste || []).filter(([n]) => !/^\s*totale\b/i.test(n || '')).map(([n, p]) => ({ n: titoloNome(pulisci(n)), p, partito: partitoDaLista(pulisci(n)) })) }));
  if (o.tipo === 'bal') out = out.filter(c => c.nome).sort((a, b) => (b.pct || 0) - (a.pct || 0)).slice(0, 2);
  return out;
}
function emojiCandidato(c) {
  // il colore dello schieramento del candidato (con le liste dei poli che prevalgono sui partiti fuori dai poli)
  const area = c.area || (typeof areaCandidato === 'function' ? areaCandidato(c) : null);
  if (area && (c.area || ['sinistra', 'centrosinistra', 'centro', 'centrodestra', 'destra'].includes(area)) && typeof COLORE_AREA !== 'undefined' && COLORE_AREA[area]) return COLORE_AREA[area];
  const prima = [...c.liste].sort((a, b) => (b.p || 0) - (a.p || 0)).find(l => l.partito);
  // senza nessun partito riconoscibile è un candidato civico: viola, come le liste civiche
  return prima ? emojiDi(prima.partito) : '🟣';
}
const breveLista = l => l.partito && l.partito.b && l.partito.pieno ? l.partito.b : (l.n.length > 44 ? l.n.slice(0, 42) + '…' : l.n);
const emojiLista = (l, c) => l.partito ? emojiDi(l.partito) : emojiCandidato(c);

// I candidati sindaco sono divisi per regione: il file si carica solo quando serve
const regioniCaricate = new Set();
function caricaCandidatiComunali(reg) {
  if (!reg || regioniCaricate.has(reg)) return;
  regioniCaricate.add(reg);
  const sc = document.createElement('script');
  sc.src = `dati/candidati/${reg}.js`;
  sc.onload = () => aggiorna(false);
  sc.onerror = () => { /* nessun file per questa regione */ };
  document.head.append(sc);
}
const CIVICHE = [
  { b: 'Lista civica di centrodestra', n: 'Lista civica di centrodestra', e: '🔵', civica: true, area: 'centrodestra' },
  { b: 'Lista civica di centrosinistra', n: 'Lista civica di centrosinistra', e: '🔴', civica: true, area: 'centrosinistra' },
  { b: 'Lista civica', n: 'Lista civica (altra)', e: '🟣', civica: true },
];
const SCHEDE = [{ v: '__bianca', t: 'Scheda bianca ⚪', l: 'Scheda bianca' }, { v: '__nulla', t: 'Scheda nulla', l: 'Scheda nulla' }];
// colore di un partito: il suo, altrimenti quello della sua area (per i partiti locali l'area è in «area», «a» è l'anno di fine)
const emojiDi = p => p.e || (typeof COLORE_PARTITO !== 'undefined' && COLORE_PARTITO[p.b]) || (typeof COLORE_AREA !== 'undefined' && COLORE_AREA[typeof p.a === 'string' ? p.a : p.area]) || '🟣';

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
  // pos: lo schieramento del voto scelto dai menu, per il sismografo
  const imposta = (t, pos = null, eu = null) => { inp.value = t; r.testo = t; r.st = 'ok'; r.pos = pos; r.testoPos = t; r.eu = eu ? eu.map(coloreGruppo) : null; dopo(); programmaAnteprima(); };
  const scheda = v => SCHEDE.find(x => x.v === v);
  const anno = o.d.slice(0, 4);

  if (o.tipo === 'pol' || o.tipo === 'eur') {
    const PN = typeof PARTITI_NAZIONALI !== 'undefined' ? PARTITI_NAZIONALI : {};
    const senato = o.ramo === 'S';
    const dati = senato ? (PN[`sen-${anno}`] || PN[`pol-${anno}`]) : PN[`${o.tipo}-${anno}`];
    if (!dati) return box;
    const uninominale = senato && dati.uninominale;
    const liste = dati.liste.map(p => vocePartito(p));
    if (o.estero && o.tipo === 'pol' && o.d >= '2006-01-01') liste.unshift({ v: 'Estero', l: 'Una lista della circoscrizione Estero', p: { b: 'Lista della circoscrizione Estero', n: 'Lista della circoscrizione Estero', e: '🟤' } });
    const coal = (!senato && o.tipo === 'pol' && ['1994', '1996', '2001'].includes(anno) && dati.coalizioni) ? dati.coalizioni.map(c => ({ v: c.n, l: c.n, p: { b: c.n, n: c.n, a: c.a } })) : null;
    const tutte = [...liste, ...(coal || [])];
    const componi = () => {
      const { lista, coalizione } = r.sel;
      if (scheda(lista)) return imposta(scheda(lista).t, { k: 'bianca' });
      const pl = liste.find(v => v.v === lista), pc = coal && coal.find(v => v.v === coalizione);
      const primo = piuVotato(dati.liste);
      const parti = [];
      if (pc) parti.push(`${pc.p.n} ${emojiDi(pc.p)}`);
      if (pl) parti.push(`${pc ? 'Lista ' : ''}${pl.p.b} ${emojiDi(pl.p)}`);
      if (lista === '__altro') parti.push(uninominale ? 'Altro candidato' : 'Altra lista');
      const pos = pl ? (pl.v === 'Estero' ? { area: 'altro', col: null } : { area: pl.p.a, col: primo ? pl.p === primo : null, piccolo: (pl.p.p || 0) < 4 })
        : lista === '__altro' ? { area: null, col: false, piccolo: true } : pc ? { area: pc.p.a, col: null } : null;
      imposta(parti.join(' '), pos, [...(pc ? [gruppoPartito(pc.p)] : []), ...(pl ? [gruppoPartito(pl.p)] : [])]);
    };
    if (coal) box.append(seleziona('Coalizione (scheda uninominale)', [[null, coal]], r.sel.coalizione, v => { r.sel.coalizione = v; componi(); }));
    box.append(seleziona(uninominale ? 'Candidato (coalizione)' : coal ? 'Lista (scheda proporzionale)' : 'Lista votata', [[uninominale ? 'Coalizioni e gruppi sopra l’1%' : 'Liste sopra l’1%', liste], ['Altro', [{ v: '__altro', l: uninominale ? 'Un altro candidato' : 'Un’altra lista' }, ...SCHEDE]]], r.sel.lista, v => { r.sel.lista = v; componi(); }));
    void tutte;
    return box;
  }

  const reali = (o.tipo === 'reg' || o.tipo === 'com' || o.tipo === 'bal' || o.tipo === 'sup') ? candidatiReali(o) : null;
  if (reali) {
    const conNome = reali.filter(c => c.nome);
    const vc = conNome.map((c, i) => ({ v: 'c' + i, l: `${c.nome}${c.liste.length ? ' — ' + c.liste.slice(0, 2).map(breveLista).join(', ') : ''}`, c }));
    const gruppiListe = reali.map((c, i) => [c.nome ? `Con ${c.nome}` : 'Liste', c.liste.map((l, j) => ({ v: `l${i}-${j}`, l: `${breveLista(l)}${l.p != null ? ` (${String(l.p).replace('.', ',')}%)` : ''}`, lst: l, c }))]);
    const tutteListe = gruppiListe.flatMap(g => g[1]);
    const componi = () => {
      const { coalizione, lista } = r.sel;
      const sc = scheda(coalizione) || scheda(lista);
      if (sc) return imposta(sc.t, { k: 'bianca' });
      const pc = vc.find(v => v.v === coalizione), pl = tutteListe.find(v => v.v === lista);
      const parti = [];
      if (pc) parti.push(o.supp && pc.c.liste[0] ? `${pc.c.nome} (${pc.c.liste[0].n}) ${emojiCandidato(pc.c)}` : `${pc.c.nome} ${emojiCandidato(pc.c)}`);
      if (pl) parti.push(`${/^lista /i.test(breveLista(pl.lst)) ? '' : 'Lista '}${breveLista(pl.lst)} ${emojiLista(pl.lst, pl.c)}`);
      // lo schieramento è quello del candidato; senza candidati (liste e basta) quello della lista
      const cand = pc ? pc.c : pl && pl.c.nome ? pl.c : null;
      const vinc = o.tipo === 'bal' ? null : conNome.length ? piuVotato(conNome, 'pct') : null;
      let pos = null;
      if (cand) { const a = areaCandidato(cand); pos = { area: a, civica: !a, col: vinc ? cand === vinc : null }; }
      else if (pl) {
        const a = pl.lst.partito ? areaDi(pl.lst.partito) : null;
        const top = piuVotato(tutteListe.map(x => x.lst));
        pos = { area: a, civica: !pl.lst.partito, col: !conNome.length && top ? pl.lst === top : null };
      }
      imposta(parti.join(' '), pos, [...(pc ? [gruppoCandidato(pc.c)] : []), ...(pl ? [gruppoLista(pl.lst, pl.c)] : [])]);
    };
    const nomeCand = o.supp ? 'Candidato nel collegio' : o.prov ? 'Candidato presidente della provincia' : o.tipo === 'reg' ? (o.reg === '04' ? 'Candidato presidente della provincia' : 'Candidato presidente') : 'Candidato sindaco';
    if (vc.length) box.append(seleziona(nomeCand, [[null, vc], ['Altro', SCHEDE]], r.sel.coalizione, v => {
      r.sel.coalizione = v;
      // la lista scelta resta anche se è di un altro candidato: è il voto disgiunto
      componi(); disegnaElenco();
    }));
    if (o.tipo !== 'bal' && o.tipo !== 'sup' && tutteListe.length) {
      const scelto = vc.find(x => x.v === r.sel.coalizione);
      const gruppi = scelto ? [...gruppiListe.filter(g => g[1][0] && g[1][0].c === scelto.c), ...gruppiListe.filter(g => !g[1][0] || g[1][0].c !== scelto.c)] : gruppiListe;
      box.append(seleziona('Lista', [...gruppi, ['Altro', SCHEDE]], r.sel.lista, v => { r.sel.lista = v; componi(); }));
    }
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
      const sc = scheda(coalizione) || scheda(lista);
      if (sc) return imposta(sc.t, { k: 'bianca' });
      const pc = coalizioni.find(v => v.v === coalizione), pl = tutte.find(v => v.v === lista);
      const parti = [];
      if (pc) parti.push(`${pc.p.b} ${pc.p.e}`);
      if (pl) parti.push(pl.p.civica || /^lista /i.test(pl.p.b) ? `${pl.p.b} ${emojiDi(pl.p)}` : `Lista ${pl.p.b} ${emojiDi(pl.p)}`);
      const aC = pc ? AREA_COALIZIONE[pc.p.b] || null : null, aL = pl ? areaDi(pl.p) : null;
      const pos = pc || pl ? { area: aC || aL, civica: (pc && pc.p.b === 'Civico') || (!pc && pl && !!pl.p.civica), col: null } : null;
      imposta(parti.join(' '), pos, [...(pc ? [GRUPPO_COALIZIONE_LOCALE[pc.p.b] || null] : []), ...(pl ? [gruppoPartito(pl.p)] : [])]);
    };
    const nomeCand = o.prov ? 'Candidato presidente della provincia' : o.tipo === 'reg' ? (o.reg === '04' ? 'Candidato presidente della provincia' : 'Candidato presidente') : 'Candidato sindaco';
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
    box.append(el('button', { class: 'bottone secondario piccolo', type: 'button', onclick: () => apriForm({ tipo: 'com', resId: r.id }) }, `Altre comunali a ${r.comune.nome}`));
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
      if (chk.checked && d2.value) stato.extra.push({ id: ++seq, tipo: 'bal', resId: f.resId, d: d2.value, d2: t && t.b === d2.value ? t.b2 : null, primo: d1.value });
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

// Illustrazione d'apertura: la scheda tricolore, votata, che entra nella busta.
// La stessa grafica serve per la pagina (SVG animato) e per le immagini promozionali (disegnata su canvas).
function svgSchedaBusta(animata) {
  const verde = '#008C45', rosso = '#CD212A', ink = '#161B26', filo = '#E1E4E9', contorno = '#C3C8D2';
  const caselle = [];
  [[168, 112], [312, 112], [168, 210], [312, 210], [168, 308], [312, 308]].forEach(([x, y], i) => {
    caselle.push(`<rect x="${x}" y="${y}" width="120" height="84" rx="6" fill="#fff" stroke="${filo}" stroke-width="2"/>`);
    caselle.push(`<circle cx="${x + 60}" cy="${y + 42}" r="25" fill="${['#E7EAEE', '#DDE1E6', '#E4E7EB', '#DADFE5', '#E7EAEE', '#DDE1E6'][i]}"/>`);
    caselle.push(`<rect x="${x + 44}" y="${y + 38}" width="32" height="8" rx="4" fill="#fff" opacity=".85"/>`);
  });
  const croce = `<g class="croce" stroke="${ink}" stroke-width="8" stroke-linecap="round" fill="none">
      <path pathLength="1" d="M326 128 L418 182"/><path pathLength="1" d="M418 128 L326 182"/></g>`;
  const scheda = `<g class="scheda"><g transform="rotate(-3 300 260)">
      <rect x="150" y="34" width="300" height="420" rx="8" fill="#fff" stroke="${contorno}" stroke-width="2.5"/>
      <rect x="151.5" y="35.5" width="99" height="20" fill="${verde}"/><rect x="250.5" y="35.5" width="99" height="20" fill="#fff"/><rect x="349.5" y="35.5" width="99" height="20" fill="${rosso}"/>
      <rect x="150" y="34" width="300" height="420" rx="8" fill="none" stroke="${contorno}" stroke-width="2.5"/>
      <rect x="168" y="72" width="150" height="9" rx="4.5" fill="#C9CED6"/><rect x="168" y="89" width="96" height="7" rx="3.5" fill="#DDE1E6"/>
      ${caselle.join('')}${croce}</g></g>`;
  const corpo = `
    <polygon points="64,300 300,186 536,300" fill="#EEF0EC" stroke="${contorno}" stroke-width="2.5" stroke-linejoin="round"/>
    <rect x="64" y="300" width="472" height="232" rx="6" fill="#F4F5F1" stroke="${contorno}" stroke-width="2.5"/>
    ${scheda}
    <path d="M64 300 L300 432 L536 300 L536 526 Q536 532 530 532 L70 532 Q64 532 64 526 Z" fill="#fff" stroke="${contorno}" stroke-width="2.5" stroke-linejoin="round"/>
    <path d="M64 532 L250 400 M536 532 L350 400" stroke="${filo}" stroke-width="2.5" fill="none"/>
    <rect x="64" y="514" width="157.3" height="18" fill="${verde}"/><rect x="221.3" y="514" width="157.3" height="18" fill="#fff"/><rect x="378.6" y="514" width="157.4" height="18" fill="${rosso}"/>
    <path d="M64 514 L64 526 Q64 532 70 532 L530 532 Q536 532 536 526 L536 514" fill="none" stroke="${contorno}" stroke-width="2.5"/>`;
  const stile = animata ? `<style>
    @media (prefers-reduced-motion: no-preference) {
      .scheda { animation: entra 2.5s ease-in-out .1s both; }
      .croce path { stroke-dasharray: 1; stroke-dashoffset: 1; animation: segna .32s ease-out forwards; }
      .croce path:first-child { animation-delay: .55s; } .croce path:last-child { animation-delay: .9s; }
      @keyframes entra { 0% { transform: translateY(-80px); opacity: 0; } 14% { transform: translateY(-80px); opacity: 1; } 56% { transform: translateY(-80px); } 100% { transform: none; opacity: 1; } }
      @keyframes segna { to { stroke-dashoffset: 0; } }
    }</style>` : '';
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="40 20 520 530" role="img" aria-label="Una scheda elettorale tricolore, votata, che entra in una busta">${stile}${corpo}</svg>`;
}
function disegnaCalendario() {
  const box = $('#calendario');
  if (box) box.innerHTML = svgSchedaBusta(true);
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
    // Camera e Senato con lo stesso voto diventano una riga sola
    const prec = out[out.length - 1];
    if (o.ramo === 'S' && prec && prec.gruppo === o.gruppo && prec.testo === testo && prec.non === (st === 'non')) {
      prec.etichetta = 'Politiche (Camera e Senato)';
      continue;
    }
    n++;
    out.push({ n, gruppo: o.gruppo || o.key, anno: o.d.slice(0, 4), quando: dataPiena ? dataBreve(o.d) : o.d.slice(0, 4), giorno: dataLunga(o.d, o.d2).replace(/ \d{4}$/, ''), etichetta: o.etichetta, testo, non: st === 'non', colore: coloreVoto(o), eu: st === 'ok' ? coloriUE(r) : null });
  }
  return out;
}
// Una consultazione per giornata di voto: Camera e Senato contano insieme
function perConsultazione(righe) {
  const visti = new Map();
  for (const r of righe) {
    const g = visti.get(r.gruppo);
    if (!g) visti.set(r.gruppo, { colore: r.colore, non: r.non });
    else if (!r.non) g.non = false;
  }
  return [...visti.values()];
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
  const cons = perConsultazione(righe);
  const tot = cons.length, voti = cons.filter(r => !r.non).length;
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
let formatoScelto = 'post';

// Misura ogni voce dell'elenco a una data scala, piena (etichetta sopra, voto sotto) o compatta (una riga sola)
function misuraVoci(ctx, righe, s, larg, compatta, dataPiena) {
  const fsE = 25 * s, fsV = 31 * s;
  return righe.map(r => {
    const et = (dataPiena ? r.giorno + ' · ' : '') + r.etichetta;
    const fE = `600 ${fsE}px ${TXT}`, fV = r.non ? `400 ${fsV}px ${TXT}` : `700 ${fsV}px ${TXT}`;
    let nSim = 0;
    // con la tavolozza europea i tondi colorati prendono, in ordine, i colori dei gruppi
    const tokV = r.testo ? tokenizza(r.testo).map(t => {
      if (t.segno && !t.segno.tipo && t.segno.c !== '#FFFFFF' && r.eu) { const c = r.eu[nSim++]; if (c) t = { segno: { ...t.segno, c } }; }
      return { ...t, f: fV, c: r.non ? C.grigio : C.ink };
    }) : [];
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

// Nei formati a misura fissa, se non entra tutto, di base si parte dalle più recenti: restano fuori le più vecchie
let ultimoRecenti = false;
function impaginaFissa(ctx, righe, area, dataPiena, maxColonne) {
  const imp = scegliImpaginazione(ctx, righe, area, dataPiena, maxColonne);
  ultimoRecenti = false;
  if (!imp.resto || !$('#opt-recenti').checked) return imp;
  ultimoRecenti = true;
  return { ...scegliImpaginazione(ctx, [...righe].reverse(), area, dataPiena, maxColonne), recenti: true };
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

// In alto a destra nella card: la scheda tricolore nella busta, con il numero di consultazioni sotto
let IMG_SCHEDA = null;
const schedaPronta = new Promise(res => {
  const img = new Image();
  img.onload = () => { IMG_SCHEDA = img; res(); };
  img.onerror = () => res();
  img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgSchedaBusta(false));
});
function disegnaEmicicloCard(ctx, cx, cy, R, tutte, s) {
  const n = perConsultazione(tutte).length;
  const lato = R * 1.42;
  if (IMG_SCHEDA) ctx.drawImage(IMG_SCHEDA, cx - lato / 2, cy - R * 1.12, lato, lato * 530 / 520);
  const yT = cy - R * 1.12 + lato * 530 / 520 + 40 * s;
  ctx.textBaseline = 'alphabetic';
  ctx.font = `700 ${40 * s}px ${TIT}`; const wN = ctx.measureText(String(n)).width;
  ctx.font = `400 ${22 * s}px ${TXT}`; const et = n === 1 ? ' consultazione' : ' consultazioni'; const wE = ctx.measureText(et).width;
  const x0 = cx - (wN + wE) / 2;
  ctx.textAlign = 'left';
  ctx.fillStyle = C.ink; ctx.font = `700 ${40 * s}px ${TIT}`; ctx.fillText(String(n), x0, yT);
  ctx.fillStyle = C.grigio; ctx.font = `400 ${22 * s}px ${TXT}`; ctx.fillText(et, x0 + wN, yT);
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
    ctx.fillText(`… e altre ${imp.resto} ${imp.resto === 1 ? 'consultazione' : 'consultazioni'}${imp.recenti ? (imp.resto === 1 ? ' precedente' : ' precedenti') : ''}`, area.x + 168 * s, area.y + area.h - 6);
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
let contenuto = 'tessera';
function disegna(cv, righe, formato = formatoScelto) {
  ultimoResto = 0;
  if (contenuto === 'sismografo') return disegnaSismografo(cv, formato);
  const f = formato === 'lista' ? 'post' : formato;
  if (contenuto === 'tessera') return IMG.tessera(cv, f);
  if (contenuto === 'quadrante') return IMG.quadrante(cv, f);
  if (contenuto === 'croci') return IMG.croci(cv, f);
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
    const imp = righe.length ? impaginaFissa(ctx, righe, area, dataPiena, 3) : null;
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
  const fineTesta = Math.max(yTesta, alto + 168 * hs + R + 96 * hs) + 44 * hs; // sotto l'urna e il suo conteggio
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
    imp = righe.length ? impaginaFissa(ctx, righe, area, dataPiena, 3) : null;
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
  if (typeof aggiornaSismografo === 'function') aggiornaSismografo();
  timer = setTimeout(() => Promise.all([fontPronti, schedaPronta]).then(() => {
    disegna($('#tela'), righeImmagine());
    const n = $('#nota-formato');
    if (n) {
      n.hidden = !ultimoResto;
      n.textContent = ultimoResto ? `In questo formato ${ultimoResto === 1 ? `resta fuori la consultazione più ${ultimoRecenti ? 'vecchia' : 'recente'}` : `restano fuori le ${ultimoResto} più ${ultimoRecenti ? 'vecchie' : 'recenti'}`}: per averle tutte scegli «Lista completa» o «Storie».` : '';
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
  navigator.share({ title: 'La mia storia di voto', text: 'Dal 1992 a oggi, quante volte hai votato? Ricostruisci la tua storia di voto.', url })
    .then(() => annuncia(''), e => { if (!e || e.name !== 'AbortError') copia(url, fatto); });
}
function nomeFile(ext) {
  if (contenuto === 'sismografo') return `il-mio-sismografo-del-voto-${FORMATI[formatoScelto === 'lista' ? 'post' : formatoScelto].file}.${ext}`;
  const nomi = { tessera: 'la-mia-tessera-elettorale', quadrante: 'il-quadrante-del-mio-voto', croci: 'le-mie-croci' };
  if (nomi[contenuto]) return `${nomi[contenuto]}-${FORMATI[formatoScelto === 'lista' ? 'post' : formatoScelto].file}.${ext}`;
  return `la-mia-storia-di-voto-${FORMATI[formatoScelto].file}.${ext}`;
}
async function generaBlob(tipo = 'image/png') {
  await fontPronti; await schedaPronta;
  const cv = document.createElement('canvas'); disegna(cv, righeImmagine(), formatoScelto);
  return new Promise(res => cv.toBlob(res, tipo, 0.92));
}
async function scarica(jpg) {
  const blob = await generaBlob(jpg ? 'image/jpeg' : 'image/png');
  if (!blob) { annuncia('Immagine non creata: riprova.'); return; }
  const url = URL.createObjectURL(blob);
  const a = el('a', { href: url, download: nomeFile(jpg ? 'jpg' : 'png') }); document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
  annuncia(`Immagine scaricata: ${FORMATI[contenuto !== 'lista' && formatoScelto === 'lista' ? 'post' : formatoScelto].nome}, ${jpg ? 'JPG' : 'PNG'}.`);
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
  ['#opt-vuote', '#opt-non', '#opt-date', '#opt-recenti'].forEach(s => $(s).addEventListener('change', programmaAnteprima));
  document.querySelectorAll('input[name=formato]').forEach(r => r.addEventListener('change', () => { formatoScelto = r.value; programmaAnteprima(); }));
  $('#scarica').addEventListener('click', () => scarica(false));
  $('#scarica-jpg').addEventListener('click', () => scarica(true));
  $('#copia-link').addEventListener('click', condividiLink);
  if (MENU_CONDIVISIONE) $('#copia-link').textContent = 'Condividi il link';
  $('#copia').addEventListener('click', () => copia(contenuto === 'sismografo' ? testoSismografo() : testoSemplice(), 'Risultato copiato negli appunti.'));
  // tavolozza: colori dei partiti o dei gruppi del Parlamento europeo
  const leg = $('#legenda-ue');
  leg.append(...Object.values(GRUPPI_UE).map(g => el('li', {}, el('i', { style: `--c:${g.c}` }), g.n)));
  document.querySelectorAll('input[name=tavolozza]').forEach(r => r.addEventListener('change', () => {
    tavolozza = r.value; leg.hidden = tavolozza !== 'ue'; aggiorna(false);
  }));
  // cosa va nell'immagine: la tessera (di base), il quadrante, le croci, la lista dei voti o il sismografo. Solo la lista ha il formato a lunghezza libera.
  const sceltaContenuto = () => {
    const lista = document.querySelector('input[name=formato][value=lista]');
    const soloLista = contenuto === 'lista';
    lista.disabled = !soloLista;
    lista.closest('label').hidden = !soloLista;
    if (!soloLista && formatoScelto === 'lista') { const p = document.querySelector('input[name=formato][value=post]'); p.checked = true; formatoScelto = 'post'; }
    document.querySelectorAll('.solo-lista').forEach(n => { n.hidden = !soloLista; });
    document.querySelectorAll('.con-titolo').forEach(n => { n.hidden = contenuto === 'sismografo'; });
  };
  document.querySelectorAll('input[name=contenuto]').forEach(r => r.addEventListener('change', () => { contenuto = r.value; sceltaContenuto(); programmaAnteprima(); }));
  sceltaContenuto();
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

// «Metodo, fonti e limiti»: si apre anche dal link nel piede o con #metodo nell'indirizzo
(() => {
  const d = document.getElementById('metodo');
  if (!d) return;
  const apri = () => { if (location.hash === '#metodo' || location.hash === '#s-metodo') { d.open = true; d.scrollIntoView({ block: 'start' }); } };
  window.addEventListener('hashchange', apri);
  const l = document.getElementById('apri-metodo');
  if (l) l.addEventListener('click', () => { d.open = true; });
  apri();
})();
