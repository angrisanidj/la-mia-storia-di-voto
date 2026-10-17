'use strict';
// ===== Il sismografo del voto =====
// Ogni voto si colloca sull'asse sinistra-destra secondo lo schieramento della lista o del
// candidato scelto (le aree dei dati: coalizioni come da fonti ufficiali e Wikipedia).
// Liste civiche, referendum, schede bianche e astensioni restano fuori dall'asse.
// Tutto si calcola nel browser a partire dalle risposte in memoria.

const NAZIONALI_TIPI = new Set(['pol', 'eur', 'sup']);
// peso dei voti nazionali nel baricentro (il resto va a regionali e comunali); 1 = solo nazionali
let pesoNazionale = 0.7;
const ASSE = { sinistra: -2, centrosinistra: -1, centro: 0, centrodestra: 1, destra: 2 };
const CORSIE = [
  { k: 'sinistra', n: ['Sinistra'], c: '#B3121B' },
  { k: 'centrosinistra', n: ['Centro-', 'sinistra'], c: '#E0574F' },
  { k: 'centro', n: ['Centro'], c: '#8C93A0' },
  { k: 'centrodestra', n: ['Centro-', 'destra'], c: '#5B8FE6' },
  { k: 'destra', n: ['Destra'], c: '#1F4FA8' },
];
const BLU = '#2D6FDB', CARTA = '#F5F8F6', GRIGLIA = '#E3ECE6';
const AMPIEZZA = 0.96; // radianti: inclinazione massima del pendolo (circa 55°)
const PASSO_ANG = 2 * (AMPIEZZA + 0.08) / 5; // ampiezza di una delle cinque aree sul quadrante

// --- Posizione di un voto ---
const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
function areaDi(p) {
  if (!p) return null;
  if (typeof p.a === 'string') return p.a;      // partiti nazionali
  if (typeof p.area === 'string') return p.area; // partiti locali, liste civiche, coalizioni locali
  return null;
}
// Lo schieramento di un candidato: quello indicato nei dati o, se manca, l'area che pesa di più tra le sue liste
function areaCandidato(c) {
  if (!c) return null;
  if (c.area) return c.area;
  const peso = {};
  for (const l of c.liste || []) { const a = l.partito && areaDi(l.partito); if (a) peso[a] = (peso[a] || 0) + (l.p || 1); }
  // sostenuto da partiti di entrambi i poli, ciascuno con almeno un quarto dei voti dei poli: candidato trasversale, al centro
  const sx = (peso.sinistra || 0) + (peso.centrosinistra || 0), dx = (peso.destra || 0) + (peso.centrodestra || 0);
  if (sx && dx && Math.min(sx, dx) >= 0.25 * (sx + dx)) return 'centro';
  // in coalizione con partiti dei due poli (es. M5S con il PD) conta lo schieramento del polo
  const top = Object.entries(peso).sort((x, y) => (y[0] in ASSE) - (x[0] in ASSE) || y[1] - x[1])[0];
  return top ? top[0] : null;
}
function piuVotato(liste, campo = 'p') {
  let m = null;
  for (const l of liste) if (l[campo] != null && (!m || l[campo] > m[campo])) m = l;
  return m;
}
// Liste del Ministero o dei dati nazionali per un'elezione politica o europea
function listeNazionali(o) {
  const PN = typeof PARTITI_NAZIONALI !== 'undefined' ? PARTITI_NAZIONALI : {};
  const anno = o.d.slice(0, 4);
  return o.ramo === 'S' ? (PN[`sen-${anno}`] || PN[`pol-${anno}`]) : PN[`${o.tipo}-${anno}`];
}
function trovaLista(testo, liste) {
  const n = ' ' + norm(testo) + ' ';
  return liste.slice().sort((a, b) => (b.n || '').length - (a.n || '').length).find(l =>
    (l.n && n.includes(' ' + norm(l.n) + ' ')) ||
    (l.b && l.b.length >= 2 && new RegExp(`(^|[^\\p{L}])${esc(l.b)}(?![\\p{L}])`, 'u').test(testo)));
}
const AREA_COALIZIONE = { CDX: 'centrodestra', CSX: 'centrosinistra', 'CSX e M5S': 'centrosinistra', M5S: 'altro' };

// Dal testo scritto a mano, quando la voce non è stata scelta dai menu
function posizioneDaTesto(o, t) {
  if (o.tipo === 'pol' || o.tipo === 'eur') {
    const dati = listeNazionali(o);
    if (!dati) return null;
    const l = trovaLista(t, dati.liste);
    if (!l) return null;
    const m = piuVotato(dati.liste);
    return { area: l.a, col: m ? l === m : null, piccolo: (l.p || 0) < 4 };
  }
  for (const c of COALIZIONI_LOCALI) if (t === c.b || t.startsWith(c.b + ' ')) return { area: AREA_COALIZIONE[c.b] || null, civica: c.b === 'Civico', col: null };
  for (const c of CIVICHE) if (t.startsWith(c.b)) return { area: c.area || null, civica: true, col: null };
  const reali = candidatiReali(o);
  if (reali) {
    const n = ' ' + norm(t) + ' ';
    const cand = reali.filter(c => c.nome).find(c => n.includes(' ' + norm(c.nome) + ' '));
    const vinc = o.tipo === 'bal' ? null : piuVotato(reali.filter(c => c.nome), 'pct');
    if (cand) return { area: areaCandidato(cand), civica: !areaCandidato(cand), col: vinc ? cand === vinc : null };
    const tutte = reali.flatMap(c => c.liste.map(l => ({ ...l, c })));
    const l = trovaLista(t, tutte.map(x => ({ n: x.n, b: x.partito && x.partito.pieno ? x.partito.b : null, x })));
    if (l) return { area: (l.x.partito && areaDi(l.x.partito)) || areaCandidato(l.x.c), civica: !l.x.partito, col: null };
  }
  if (o.reg) {
    const { naz, loc } = partitiDelPeriodo(o.d, o.reg, o.sig, o.tipo);
    const l = trovaLista(t, [...naz, ...loc]);
    if (l) return { area: areaDi(l), col: null };
  }
  return null;
}

function votoReferendum(o, r) {
  const dati = typeof QUESITI !== 'undefined' ? QUESITI[o.qk] : null;
  const qs = dati && dati.quesiti ? dati.quesiti : [];
  const t = r.testo || '';
  const si = /(^|[^\p{L}])S[ÌIì](?!\p{L})/iu.test(t), no = /(^|[^\p{L}])NO(?!\p{L})/iu.test(t);
  let risp;
  if (qs.length > 1 && r.q && r.q.some(Boolean)) risp = r.q;
  else if (si !== no) risp = qs.length ? qs.map(() => (si ? 'si' : 'no')) : [si ? 'si' : 'no'];
  else return { k: /bianca|nulla/i.test(t) ? 'bianca' : t.trim() ? 'ref' : 'ignoto', esito: null, col: null };
  const date = risp.filter(Boolean);
  const nSi = date.filter(v => v === 'si').length;
  const esito = !date.length ? null : nSi === date.length ? 'si' : nSi === 0 ? 'no' : 'misto';
  let col = null;
  if (qs.length && qs.every(q => typeof q.si === 'number')) {
    let con = 0, tot = 0;
    risp.forEach((v, i) => { if (v && qs[i]) { tot++; if ((qs[i].si > 50) === (v === 'si')) con++; } });
    col = tot ? (con * 2 > tot ? true : con * 2 < tot ? false : null) : null;
  }
  return { k: 'ref', esito, col };
}

// { k: 'voto'|'altro'|'civico'|'ignoto'|'ref'|'bianca'|'non', x, area, col, piccolo, civica }
function posizioneVoto(o) {
  const st = statoDi(o);
  if (st === 'escl') return null;
  if (st === 'non') return { k: 'non', col: null };
  const r = risposta(o.key), t = (r.testo || '').trim();
  if (o.tipo === 'ref') return votoReferendum(o, r);
  if (!t) return { k: 'ignoto', col: null };
  if (/^Scheda (bianca|nulla)/i.test(t)) return { k: 'bianca', col: null };
  let p = r.pos && r.testoPos === r.testo ? r.pos : posizioneDaTesto(o, t);
  if (!p && r.pos) p = r.pos;
  if (!p) return { k: 'ignoto', col: null };
  if (p.k === 'bianca') return { k: 'bianca', col: null };
  const x = p.area in ASSE ? ASSE[p.area] : null;
  const k = x != null ? 'voto' : p.area ? 'altro' : p.civica ? 'civico' : 'ignoto';
  return { k, x, area: p.area || null, col: p.col ?? null, piccolo: !!p.piccolo, civica: !!p.civica };
}

// Come ha votato la maggioranza: posizione della lista o del candidato più votato (al primo turno)
function posizioneVincitore(o) {
  let area = null;
  if (o.tipo === 'pol' || o.tipo === 'eur') {
    const dati = listeNazionali(o), m = dati && piuVotato(dati.liste);
    area = m ? m.a : null;
  } else if (o.tipo === 'reg' || o.tipo === 'com' || o.tipo === 'sup') {
    const reali = candidatiReali(o);
    if (reali) {
      const conNome = reali.filter(c => c.nome);
      if (conNome.length) area = areaCandidato(piuVotato(conNome, 'pct'));
      else { const l = piuVotato(reali.flatMap(c => c.liste)); area = l && l.partito ? areaDi(l.partito) : null; }
    }
  }
  if (!area) return null;
  return area in ASSE ? ASSE[area] : area === 'altro' ? 0 : null;
}

// --- Dati e profilo ---
function nomeArea(b) {
  if (b == null) return '—';
  return b <= -1.5 ? 'Sinistra' : b <= -0.5 ? 'Centrosinistra' : b < 0.5 ? 'Centro' : b < 1.5 ? 'Centrodestra' : 'Destra';
}
function datiSismografo() {
  const righe = [];
  for (const o of elenco) {
    const p = posizioneVoto(o);
    if (!p) continue;
    const prec = righe[righe.length - 1];
    // Camera e Senato con lo stesso voto: una riga sola
    if (o.ramo === 'S' && prec && prec.gruppo === o.gruppo && prec.k === p.k && prec.x === p.x && risposta(o.key).testo === prec.testo) continue;
    righe.push({ ...p, colore: coloreVoto(o), gruppo: o.gruppo || o.key, anno: o.d.slice(0, 4), tipo: o.tipo, testo: risposta(o.key).testo, xi: posizioneVincitore(o) });
  }
  const pos = righe.filter(r => r.x != null);
  // baricentro: media dei voti nazionali (politiche, europee) e di quelli locali, pesate per gruppo
  const media = l => l.length ? l.reduce((a, r) => a + r.x, 0) / l.length : null;
  const naz = pos.filter(r => NAZIONALI_TIPI.has(r.tipo)), loc = pos.filter(r => !NAZIONALI_TIPI.has(r.tipo));
  const mN = media(naz), mL = media(loc);
  const bar = pesoNazionale >= 1 ? mN : mN != null && mL != null ? pesoNazionale * mN + (1 - pesoNazionale) * mL : (mN ?? mL);
  let passi = 0, cambi = 0, segno = 0, prec = null, ultimoLato = null, traversata = null;
  for (const r of pos) {
    if (prec != null) passi += Math.abs(r.x - prec);
    const s = Math.sign(r.x);
    if (s && segno && s !== segno) { cambi++; traversata = { anno: r.anno, da: ultimoLato.area, a: r.area }; }
    if (s) { segno = s; ultimoLato = r; }
    prec = r.x;
  }
  const oscillazione = pos.length > 1 ? passi / (pos.length - 1) : 0;
  const vento = righe.filter(r => r.col != null), conVento = vento.filter(r => r.col).length;
  const D = { righe, pos, naz, loc, bar, cambi, traversata, oscillazione, vento: { con: conVento, tot: vento.length } };
  D.profilo = profilo(D);
  return D;
}
function profilo(D) {
  const { righe, pos, bar, cambi, vento, traversata } = D;
  const voti = righe.filter(r => ['voto', 'altro', 'civico', 'ref'].includes(r.k));
  if (voti.length < 3) return null;
  const quota = vento.tot ? vento.con / vento.tot : null;
  const lati = pos.map(r => Math.sign(r.x));
  const latoTop = [-1, 0, 1].map(s => [s, lati.filter(x => x === s).length]).sort((a, b) => b[1] - a[1])[0];
  const fuori = righe.filter(r => r.k === 'altro' || (r.k === 'voto' && (r.piccolo || r.area === 'sinistra' || r.area === 'destra')));
  const locali = righe.filter(r => (r.tipo === 'com' || r.tipo === 'bal') && ['voto', 'altro', 'civico'].includes(r.k));
  const civiche = locali.filter(r => r.civica).length;
  const refs = righe.filter(r => r.tipo === 'ref'), refVotati = refs.filter(r => r.k === 'ref');
  const volte = n => n === 1 ? 'una volta' : `${n} volte`;
  if (cambi >= 2) return { nome: 'Il Pendolo', descr: `Hai attraversato il centro ${volte(cambi)}: il tuo voto si sposta con le stagioni della politica.` };
  if (cambi === 1 && pos.length >= 4) {
    const nome = { sinistra: 'la sinistra', centrosinistra: 'il centrosinistra', centrodestra: 'il centrodestra', destra: 'la destra' };
    return { nome: 'La Traversata', descr: `Hai cambiato campo una volta sola: nel ${traversata.anno}, dal${nome[traversata.da].startsWith('la') ? 'la ' + nome[traversata.da].slice(3) : ' ' + nome[traversata.da].slice(3)} ${traversata.a === 'destra' || traversata.a === 'sinistra' ? 'alla' : 'al'} ${nome[traversata.a].replace(/^(il|la) /, '')}.` };
  }
  if (vento.tot >= 5 && quota <= 0.3) return { nome: 'Il Bastian contrario', descr: `Solo ${vento.con} ${vento.con === 1 ? 'voto' : 'voti'} su ${vento.tot} come la maggioranza: vai controcorrente.` };
  if (pos.length >= 4 && cambi === 0 && latoTop[1] / pos.length >= 0.85) {
    const conta = {};
    pos.forEach(r => { conta[r.area] = (conta[r.area] || 0) + 1; });
    const area = Object.entries(conta).sort((x, y) => y[1] - x[1])[0][0];
    const verso = { sinistra: 'la sinistra', centrosinistra: 'il centrosinistra', centro: 'il centro', centrodestra: 'il centrodestra', destra: 'la destra' }[area];
    return { nome: 'La Bussola', descr: `Dal ${pos[0].anno} il tuo ago punta verso ${verso}, elezione dopo elezione.` };
  }
  if (vento.tot >= 5 && quota >= 0.7) return { nome: 'Il Barometro', descr: `${vento.con} volte su ${vento.tot} hai votato come la maggioranza: l’Italia vota spesso come te.` };
  if (fuori.length >= 3 && fuori.length / voti.length >= 0.4) return { nome: 'Il Battitore libero', descr: `${fuori.length} voti su ${voti.length} a liste fuori dai grandi schieramenti o sotto il 4%.` };
  if (civiche >= 3 && civiche / locali.length >= 0.5) return { nome: 'Il Campanile', descr: `Alle comunali scegli il territorio: ${civiche} voti a liste civiche.` };
  if (refs.length >= 3 && refVotati.length === refs.length) return { nome: 'Il Quorum', descr: `Non hai saltato un referendum: ${refs.length} su ${refs.length}.` };
  if (bar != null && Math.abs(bar) < 0.5 && pos.length >= 3) return { nome: 'L’Ago della bilancia', descr: 'Il tuo baricentro sta in mezzo: né di qua né di là, ma sempre al seggio.' };
  return { nome: 'Il Viandante', descr: 'Ogni consultazione fa storia a sé: il tuo voto non segue una sola strada.' };
}
function metriche(D) {
  const o = D.oscillazione;
  return [
    { l: 'Baricentro', v: nomeArea(D.bar), s: D.bar == null ? (D.pos.length ? 'nessun voto nazionale sull’asse' : 'nessun voto sull’asse') : pesoNazionale >= 1 ? `${D.naz.length} ${D.naz.length === 1 ? 'voto nazionale' : 'voti nazionali'}` : D.naz.length && D.loc.length ? `nazionali ${Math.round(pesoNazionale * 100)}%, locali ${Math.round((1 - pesoNazionale) * 100)}%` : `media di ${D.pos.length} ${D.pos.length === 1 ? 'voto' : 'voti'}` },
    { l: 'Oscillazione', v: D.pos.length < 2 ? '—' : o < 0.15 ? 'Piatta' : o < 0.5 ? 'Lieve' : o < 1 ? 'Moderata' : 'Forte',
      s: D.cambi ? `${D.cambi} ${D.cambi === 1 ? 'cambio' : 'cambi'} di campo` : 'mai cambiato campo' },
    { l: 'Col vento', v: D.vento.tot ? `${D.vento.con} su ${D.vento.tot}` : '—', s: 'voti come la maggioranza' },
  ];
}
const angoloDi = b => (b == null ? 0 : Math.max(-2, Math.min(2, b))) * PASSO_ANG;

// --- Disegno ---
function mescola(a, b, t) {
  const h = s => [1, 3, 5].map(i => parseInt(s.slice(i, i + 2), 16));
  const [x, y] = [h(a), h(b)];
  return '#' + x.map((v, i) => Math.round(v + (y[i] - v) * t).toString(16).padStart(2, '0')).join('');
}
function colorePendolo(th) {
  const t = th / AMPIEZZA;
  return t < 0 ? mescola('#5A6372', C.rosso, Math.min(1, -t * 1.3)) : mescola('#5A6372', BLU, Math.min(1, t * 1.3));
}

// Il pendolo: perno in alto, quadrante ad arco sotto con le cinque aree
function disegnaPendolo(ctx, cx, cy, L, th, s, etichetta) {
  const rArco = L * 1.06, a0 = Math.PI / 2 + AMPIEZZA + 0.08, a1 = Math.PI / 2 - AMPIEZZA - 0.08;
  // quadrante: cinque archi colorati
  const passo = (a0 - a1) / 5;
  ctx.lineCap = 'butt';
  CORSIE.forEach((c, i) => {
    ctx.beginPath(); ctx.arc(cx, cy, rArco, a0 - i * passo - 0.012, a0 - (i + 1) * passo + 0.012, true);
    ctx.strokeStyle = c.c; ctx.lineWidth = 9 * s; ctx.stroke();
  });
  // tacche
  ctx.strokeStyle = C.contorno; ctx.lineWidth = 1.5 * s;
  for (let i = 0; i <= 10; i++) {
    const a = a0 - i * (a0 - a1) / 10, r1 = rArco - 9 * s, r2 = rArco - (i % 5 === 0 ? 22 : 15) * s;
    ctx.beginPath(); ctx.moveTo(cx + r1 * Math.cos(a), cy + r1 * Math.sin(a)); ctx.lineTo(cx + r2 * Math.cos(a), cy + r2 * Math.sin(a)); ctx.stroke();
  }
  ctx.font = `600 ${17 * s}px ${TXT}`; ctx.fillStyle = C.grigio; ctx.textBaseline = 'top';
  ctx.textAlign = 'right'; ctx.fillText('Sinistra', cx + (rArco + 14 * s) * Math.cos(a0) + 8 * s, cy + rArco * Math.sin(a0) + 12 * s);
  ctx.textAlign = 'left'; ctx.fillText('Destra', cx + (rArco + 14 * s) * Math.cos(a1) - 8 * s, cy + rArco * Math.sin(a1) + 12 * s);
  ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
  // asta e peso
  const bx = cx + L * Math.sin(th), by = cy + L * Math.cos(th);
  const col = colorePendolo(th);
  ctx.strokeStyle = C.ink; ctx.lineWidth = 3.5 * s; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(bx, by); ctx.stroke();
  tondo(ctx, bx, by, 25 * s, '#fff');
  tondo(ctx, bx, by, 21 * s, col);
  tondo(ctx, bx - 6 * s, by - 6 * s, 6 * s, 'rgba(255,255,255,.35)');
  // perno
  ctx.fillStyle = C.ink; rr(ctx, cx - 30 * s, cy - 12 * s, 60 * s, 8 * s, 4 * s); ctx.fill();
  tondo(ctx, cx, cy, 8 * s, '#fff', C.ink, 3.5 * s);
  if (etichetta) {
    ctx.textAlign = 'center';
    ctx.font = `700 ${34 * s}px ${TIT}`; ctx.fillStyle = C.ink;
    ctx.fillText(etichetta, cx, cy + rArco + 64 * s);
    ctx.textAlign = 'left';
  }
}

// Curva morbida che passa per tutti i punti: tangenti verticali, così non va mai oltre un voto
function tracciaCurva(ctx, pt) {
  ctx.moveTo(pt[0].x, pt[0].y);
  for (let i = 0; i < pt.length - 1; i++) {
    const p1 = pt[i], p2 = pt[i + 1], dy = (p2.y - p1.y) * 0.55;
    ctx.bezierCurveTo(p1.x, p1.y + dy, p2.x, p2.y - dy, p2.x, p2.y);
  }
}

// Il tracciato: anni a sinistra, cinque corsie, una colonna "Fuori dall'asse" a destra.
// prog: quota di righe già tracciate (0-1), per l'animazione della pagina.
function disegnaTracciato(ctx, a, D, s, prog = 1) {
  const righe = D.righe;
  const legenda = vociLegenda(righe);
  if (legenda.length) a = { ...a, h: a.h - 46 * s };
  const annoW = 78 * s, fuoriW = Math.max(96 * s, a.w * 0.13), testaH = 66 * s;
  const x0 = a.x + annoW, x1 = a.x + a.w - fuoriW, corsiaW = (x1 - x0) / 5;
  const xc = i => x0 + corsiaW * (i + 0.5), xAsse = v => xc(v + 2);
  const y0 = a.y + testaH, h = a.h - testaH;
  const N = Math.max(righe.length, 1), passo = Math.min(h / N, 58 * s);
  const yR = i => y0 + passo * (i + 0.5);
  const yFine = y0 + passo * N;
  // carta millimetrata
  ctx.fillStyle = CARTA; rr(ctx, x0, y0 - 8 * s, x1 - x0, yFine - y0 + 16 * s, 10 * s); ctx.fill();
  ctx.save(); rr(ctx, x0, y0 - 8 * s, x1 - x0, yFine - y0 + 16 * s, 10 * s); ctx.clip();
  ctx.strokeStyle = GRIGLIA; ctx.lineWidth = 1;
  const maglia = corsiaW / 4;
  for (let x = x0 + maglia; x < x1; x += maglia) { ctx.beginPath(); ctx.moveTo(x, y0 - 8 * s); ctx.lineTo(x, yFine + 8 * s); ctx.stroke(); }
  for (let y = y0 - 8 * s + maglia; y < yFine + 8 * s; y += maglia) { ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(x1, y); ctx.stroke(); }
  ctx.strokeStyle = '#CFDDD4'; ctx.lineWidth = 1.5;
  for (let i = 1; i < 5; i++) { const x = x0 + i * corsiaW; ctx.beginPath(); ctx.moveTo(x, y0 - 8 * s); ctx.lineTo(x, yFine + 8 * s); ctx.stroke(); }
  ctx.restore();
  // asse centrale
  ctx.save(); ctx.setLineDash([6 * s, 6 * s]); ctx.strokeStyle = '#9AA2AF'; ctx.lineWidth = 1.5 * s;
  ctx.beginPath(); ctx.moveTo(xAsse(0), y0 - 8 * s); ctx.lineTo(xAsse(0), yFine + 8 * s); ctx.stroke(); ctx.restore();
  // intestazioni delle corsie
  ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
  CORSIE.forEach((c, i) => {
    ctx.fillStyle = c.c; rr(ctx, xc(i) - corsiaW * 0.3, a.y + testaH - 22 * s, corsiaW * 0.6, 5 * s, 2.5 * s); ctx.fill();
    ctx.font = `600 ${(corsiaW < 120 * s ? 16 : 18) * s}px ${TXT}`; ctx.fillStyle = C.ink;
    const lin = corsiaW < 150 * s ? c.n : [c.n.join('')];
    lin.forEach((t, j) => ctx.fillText(t, xc(i), a.y + testaH - 34 * s - (lin.length - 1 - j) * 20 * s));
  });
  ctx.font = `600 ${16 * s}px ${TXT}`; ctx.fillStyle = C.grigio;
  ctx.fillText('Fuori', x1 + fuoriW / 2, a.y + testaH - 54 * s);
  ctx.fillText('dall’asse', x1 + fuoriW / 2, a.y + testaH - 34 * s);
  ctx.fillStyle = C.filo; rr(ctx, x1 + fuoriW * 0.2, a.y + testaH - 22 * s, fuoriW * 0.6, 5 * s, 2.5 * s); ctx.fill();
  ctx.textAlign = 'left';
  if (!righe.length) {
    ctx.font = `400 ${24 * s}px ${TXT}`; ctx.fillStyle = C.grigio; ctx.textAlign = 'center';
    ctx.fillText('Segna come hai votato per vedere il tracciato.', (x0 + x1) / 2, y0 + 40 * s); ctx.textAlign = 'left';
    return;
  }
  const visibili = Math.max(0, Math.min(righe.length, prog * righe.length));
  const yTaglio = y0 + passo * visibili;
  // anni
  let ultimoY = -Infinity, annoPrec = null;
  righe.forEach((r, i) => {
    if (r.anno === annoPrec) return;
    annoPrec = r.anno;
    const y = yR(i);
    if (y - ultimoY < 30 * s || i >= Math.ceil(visibili)) return;
    ultimoY = y;
    ctx.font = `700 ${24 * s}px ${TIT}`; ctx.fillStyle = C.verdeScuro; ctx.fillText(r.anno, a.x, y + 8 * s);
  });
  // tracciato: campitura verso l'asse, rossa a sinistra e blu a destra, poi la linea
  const pt = righe.map((r, i) => r.x != null ? { x: xAsse(r.x), y: yR(i) } : null).filter(Boolean);
  ctx.save();
  ctx.beginPath(); ctx.rect(a.x, y0 - 10 * s, a.w, yTaglio - y0 + 10 * s); ctx.clip();
  if (pt.length > 1) {
    const area = new Path2D();
    area.moveTo(xAsse(0), pt[0].y); area.lineTo(pt[0].x, pt[0].y);
    const tmp = { moveTo: () => {}, bezierCurveTo: (...v) => area.bezierCurveTo(...v) };
    tracciaCurva(tmp, pt);
    area.lineTo(xAsse(0), pt[pt.length - 1].y); area.closePath();
    for (const [lato, col] of [[-1, 'rgba(205,33,42,.16)'], [1, 'rgba(45,111,219,.16)']]) {
      ctx.save(); ctx.beginPath();
      if (lato < 0) ctx.rect(x0, y0 - 10 * s, xAsse(0) - x0, yFine - y0 + 20 * s); else ctx.rect(xAsse(0), y0 - 10 * s, x1 - xAsse(0), yFine - y0 + 20 * s);
      ctx.clip(); ctx.fillStyle = col; ctx.fill(area); ctx.restore();
    }
  }
  // la maggioranza: una traccia tratteggiata sotto la tua
  const pi = righe.map((r, i) => r.xi != null ? { x: xAsse(r.xi), y: yR(i) } : null).filter(Boolean);
  if (pi.length > 1) {
    ctx.save(); ctx.setLineDash([1, 7 * s]); ctx.lineCap = 'round';
    ctx.beginPath(); tracciaCurva(ctx, pi); ctx.strokeStyle = '#6B7383'; ctx.lineWidth = 3.2 * s; ctx.stroke(); ctx.restore();
  }
  if (pt.length > 1) {
    ctx.beginPath(); tracciaCurva(ctx, pt);
    ctx.strokeStyle = C.ink; ctx.lineWidth = 3 * s; ctx.lineJoin = 'round'; ctx.lineCap = 'round'; ctx.stroke();
  }
  // punti
  const rP = Math.max(6 * s, Math.min(passo * 0.3, 12 * s));
  const xF = x1 + fuoriW / 2;
  righe.forEach((r, i) => {
    const y = yR(i), k = r.colore || { c: '#fff', b: C.contorno };
    if (r.k === 'voto') { tondo(ctx, xAsse(r.x), y, rP + 3.5 * s, '#fff'); tondo(ctx, xAsse(r.x), y, rP, k.c, k.c === '#FFFFFF' ? '#9AA2AF' : null, 2.5 * s); }
    else if (r.k === 'altro') { tondo(ctx, xAsse(0), y, rP + 3 * s, '#fff'); tondo(ctx, xAsse(0), y, rP - 1.5 * s, '#fff', k.c === '#FFFFFF' || k.vuoto ? '#9AA2AF' : k.c, 3.5 * s); }
    else if (r.k === 'ref') {
      if (r.esito === 'si' || r.esito === 'no') disegnaSegno(ctx, SEGNI.find(x => x.tipo === r.esito), xF, y, rP * 0.95);
      else { ctx.fillStyle = '#9AA2AF'; rr(ctx, xF - rP * 0.9, y - rP * 0.9, rP * 1.8, rP * 1.8, rP * 0.4); ctx.fill(); }
    }
    else if (r.k === 'civico') tondo(ctx, xF, y, rP, coloreCivico());
    else if (r.k === 'non') tondo(ctx, xF, y, rP * 0.85, '#fff', '#9AA2AF', 2.5 * s);
    else if (r.k === 'bianca') tondo(ctx, xF, y, rP * 0.85, '#fff', C.ink, 1.5 * s);
    else tondo(ctx, xF, y, rP * 0.55, k.vuoto ? '#C3C8D2' : k.c);
  });
  ctx.restore();
  // il salto più grande, annotato come in un grafico di giornale
  const salto = saltoMaggiore(righe);
  if (salto && passo >= 16 * s && yR(salto.j) <= yTaglio + 1) { // solo se c'è spazio per scriverlo
    const A = { x: xAsse(righe[salto.i].x), y: yR(salto.i) }, B = { x: xAsse(righe[salto.j].x), y: yR(salto.j) };
    const testo = righe[salto.i].anno === righe[salto.j].anno ? `Il salto più grande, nel ${righe[salto.j].anno}` : `Il salto più grande, ${righe[salto.i].anno}–${righe[salto.j].anno}`;
    ctx.font = `600 ${17 * s}px ${TXT}`;
    const tw = ctx.measureText(testo).width, verso = B.x < xAsse(0) ? 1 : -1;
    const xt = B.x + verso * (rP + 22 * s), yt = B.y;
    const bx = verso > 0 ? xt - 6 * s : xt - tw - 6 * s;
    ctx.fillStyle = 'rgba(255,255,255,.92)'; rr(ctx, bx, yt - 15 * s, tw + 12 * s, 30 * s, 8 * s); ctx.fill();
    ctx.strokeStyle = C.ink; ctx.lineWidth = 1.5 * s; ctx.beginPath(); ctx.moveTo(B.x + verso * (rP + 4 * s), yt); ctx.lineTo(xt - verso * 4 * s, yt); ctx.stroke();
    ctx.fillStyle = C.ink; ctx.textBaseline = 'middle'; ctx.textAlign = verso > 0 ? 'left' : 'right'; ctx.fillText(testo, xt, yt + 1);
    ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
    void A;
  }
  if (legenda.length) disegnaLegenda(ctx, legenda, x0, yFine + 46 * s, a.x + a.w - x0, s);
  // il pennino: dove sta scrivendo il tracciato
  if (prog < 1 && pt.length) {
    const ult = [...pt].reverse().find(p => p.y <= yTaglio) || pt[0];
    ctx.fillStyle = C.ink; ctx.fillRect(x0, yTaglio - 0.75 * s, x1 - x0, 1.5 * s);
    tondo(ctx, ult.x, Math.min(ult.y, yTaglio), 5 * s, C.ink);
  }
}

// Il passaggio più ampio tra due voti consecutivi sull'asse (almeno due aree); a parità, il più recente
function saltoMaggiore(righe) {
  let meglio = null, prec = -1;
  righe.forEach((r, i) => {
    if (r.x == null) return;
    if (prec >= 0) { const d = Math.abs(r.x - righe[prec].x); if (d >= 2 && (!meglio || d >= meglio.d)) meglio = { i: prec, j: i, d }; }
    prec = i;
  });
  return meglio;
}
// Legenda dei simboli fuori dall'asse, solo quelli presenti
function vociLegenda(righe) {
  const ci = k => righe.some(r => r.k === k);
  const out = [];
  if (righe.filter(r => r.xi != null).length > 1) out.push(['italia', 'la maggioranza']);
  if (ci('altro')) out.push(['altro', 'fuori dai poli']);
  if (righe.some(r => r.k === 'ref' && r.esito === 'si')) out.push(['si', 'Sì']);
  if (righe.some(r => r.k === 'ref' && r.esito === 'no')) out.push(['no', 'No']);
  if (righe.some(r => r.k === 'ref' && r.esito === 'misto')) out.push(['misto', 'Sì e No']);
  if (ci('civico')) out.push(['civico', 'lista civica']);
  if (ci('bianca')) out.push(['bianca', 'bianca o nulla']);
  if (ci('non')) out.push(['non', 'non ho votato']);
  if (ci('ignoto')) out.push(['ignoto', 'senza partito']);
  return out;
}
function disegnaLegenda(ctx, voci, x, y, w, s) {
  let fs = 17 * s;
  const misura = () => { ctx.font = `400 ${fs}px ${TXT}`; return voci.reduce((t, v) => t + 26 * s + ctx.measureText(v[1]).width + 22 * s + (v[0] === 'italia' ? 10 * s : 0), 0); };
  while (misura() > w && fs > 12 * s) fs -= 1 * s;
  let xx = x; const r = 7 * s;
  ctx.textBaseline = 'middle'; ctx.fillStyle = C.grigio;
  for (const [k, t] of voci) {
    const cx = xx + r;
    if (k === 'italia') { ctx.save(); ctx.setLineDash([1, 7 * s]); ctx.lineCap = 'round'; ctx.strokeStyle = '#6B7383'; ctx.lineWidth = 3.2 * s; ctx.beginPath(); ctx.moveTo(xx, y); ctx.lineTo(xx + 2 * r + 10 * s, y); ctx.stroke(); ctx.restore(); xx += 10 * s; }
    else if (k === 'altro') tondo(ctx, cx, y, r - 1, '#fff', '#9AA2AF', 3 * s);
    else if (k === 'si' || k === 'no') disegnaSegno(ctx, SEGNI.find(z => z.tipo === k), cx, y, r);
    else if (k === 'misto') { ctx.fillStyle = '#9AA2AF'; rr(ctx, cx - r, y - r, 2 * r, 2 * r, r * 0.4); ctx.fill(); }
    else if (k === 'civico') tondo(ctx, cx, y, r, coloreCivico());
    else if (k === 'bianca') tondo(ctx, cx, y, r * 0.9, '#fff', C.ink, 1.5 * s);
    else if (k === 'non') tondo(ctx, cx, y, r * 0.9, '#fff', '#9AA2AF', 2.5 * s);
    else tondo(ctx, cx, y, r * 0.6, '#C3C8D2');
    ctx.font = `400 ${fs}px ${TXT}`; ctx.fillStyle = C.grigio;
    ctx.fillText(t, xx + 2 * r + 8 * s, y + 1);
    xx += 26 * s + ctx.measureText(t).width + 22 * s;
  }
  ctx.textBaseline = 'alphabetic';
}

function disegnaMetriche(ctx, x, y, w, D, s, colonna = false) {
  const m = metriche(D), gap = 22 * s;
  const tw = colonna ? w : (w - 2 * gap) / 3;
  m.forEach((t, i) => {
    const tx = colonna ? x : x + i * (tw + gap), ty = colonna ? y + i * 112 * s : y;
    ctx.fillStyle = C.verde; ctx.fillRect(tx, ty, 34 * s, 4 * s);
    ctx.font = `600 ${19 * s}px ${TXT}`; ctx.fillStyle = C.grigio; ctx.fillText(t.l, tx, ty + 32 * s);
    let fs = 38 * s; ctx.font = `700 ${fs}px ${TIT}`;
    while (ctx.measureText(t.v).width > tw && fs > 22 * s) { fs -= 2 * s; ctx.font = `700 ${fs}px ${TIT}`; }
    ctx.fillStyle = C.ink; ctx.fillText(t.v, tx, ty + 74 * s);
    ctx.font = `400 ${18 * s}px ${TXT}`; ctx.fillStyle = C.grigio;
    const sub = righeTesto(ctx, t.s, tw)[0];
    ctx.fillText(sub, tx, ty + 100 * s);
  });
  return colonna ? 3 * 112 * s : 108 * s;
}

// Titolo del profilo con la descrizione; restituisce la y di fine
function disegnaProfilo(ctx, x, y, w, D, s, firma, soloMisura = false) {
  const scrivi = soloMisura ? () => {} : (t, a, b) => ctx.fillText(t, a, b);
  ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
  ctx.font = `600 ${24 * s}px ${TXT}`; ctx.fillStyle = C.verdeScuro;
  scrivi('Il mio sismografo del voto', x, y);
  const P = D.profilo || { nome: 'Il pendolo è fermo', descr: 'Segna come hai votato in almeno tre consultazioni per metterlo in moto.' };
  let fs = 72 * s; ctx.font = `700 ${fs}px ${TIT}`;
  while (ctx.measureText(P.nome).width > w && fs > 40 * s) { fs -= 4 * s; ctx.font = `700 ${fs}px ${TIT}`; }
  ctx.fillStyle = C.ink; scrivi(P.nome, x, y + fs * 1.08);
  let yy = y + fs * 1.08 + 46 * s;
  ctx.font = `400 ${27 * s}px ${TXT}`; ctx.fillStyle = '#2C3340';
  righeTesto(ctx, P.descr, w).slice(0, 3).forEach(l => { scrivi(l, x, yy); yy += 37 * s; });
  if (firma) { yy += 6 * s; ctx.font = `600 ${26 * s}px ${TXT}`; ctx.fillStyle = C.grigio; scrivi(firma, x, yy); yy += 34 * s; }
  return yy - 30 * s;
}

// L'immagine da scaricare, nei formati a misura fissa (la lista completa diventa il post)
function disegnaSismografo(cv, formato, D = datiSismografo(), th = null, prog = 1) {
  const chiave = formato === 'lista' ? 'post' : formato;
  const F = FORMATI[chiave];
  const ctx = cv.getContext('2d');
  const W = F.W, H = F.H;
  cv.width = W; cv.height = H;
  ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, W, H);
  const firma = $('#firma') ? $('#firma').value.trim() : '';
  const angolo = th == null ? angoloDi(D.bar) : th;
  if (F.orizzontale) {
    const m = 72, colSx = 500;
    nastroEMarchio(ctx, W, m, 92);
    const fineP = disegnaProfilo(ctx, m, 176, colSx, D, 0.86, firma);
    const L = 150, cy = Math.max(fineP + 40, H - 150 - 62 - L * 1.06 - 80);
    disegnaPendolo(ctx, m + colSx / 2, cy, L, angolo, 0.95, nomeArea(D.bar));
    ctx.fillStyle = C.filo; ctx.fillRect(m + colSx + 40, 70, 2, H - 210);
    const ax = m + colSx + 80, aw = W - m - ax;
    const yMet = H - 52 - 62 - 28 - 108 * 0.86;
    disegnaMetriche(ctx, ax, yMet, aw, D, 0.86);
    disegnaTracciato(ctx, { x: ax, y: 60, w: aw, h: yMet - 44 - 60 }, D, 0.86, prog);
    disegnaPiede(ctx, m, H - 52, W, m);
    return;
  }
  const [alto, basso] = F.sicuro || [0, 0];
  const hs = chiave === 'quadrata' ? 0.8 : 1;
  const m = 84, larg = W - 2 * m;
  const yM = alto + 106 * hs;
  nastroEMarchio(ctx, W, m, yM, hs);
  const L = 132 * hs, dialW = 2 * L * 1.06 * Math.sin(AMPIEZZA + 0.08) + 40 * hs;
  const fineP = disegnaProfilo(ctx, m, alto + 182 * hs, larg - dialW - 36 * hs, D, hs, firma);
  const cy = alto + 172 * hs;
  disegnaPendolo(ctx, W - m - dialW / 2, cy, L, angolo, hs, nomeArea(D.bar));
  const fineTesta = Math.max(fineP, cy + L * 1.06 + 76 * hs) + 34 * hs;
  ctx.fillStyle = C.filo; ctx.fillRect(m, fineTesta, larg, 2);
  const yPiede = H - basso - 78;
  const hMet = 108 * hs;
  const yMet = yPiede - 62 * hs - 44 * hs - hMet;
  disegnaMetriche(ctx, m, yMet, larg, D, hs);
  disegnaTracciato(ctx, { x: m, y: fineTesta + 22 * hs, w: larg, h: yMet - 40 * hs - (fineTesta + 22 * hs) }, D, hs, prog);
  disegnaPiede(ctx, m, yPiede, W, m, hs);
}

// ===== Pagina: pannello animato =====
let sismoD = null, sismoAnim = null, sismoInVista = false, sismoDaAnimare = true;
const MENO_MOTO = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
function disegnaPannello(th, prog) {
  const cv = $('#sismo');
  if (!cv || !sismoD) return;
  const D = sismoD, ctx = cv.getContext('2d');
  const largo = !cv.clientWidth || cv.clientWidth > 640;
  const W = largo ? 1080 : 540, s = 1;
  const N = Math.max(D.righe.length, 6);
  const L = 128 * s, dialW = 2 * L * 1.06 * Math.sin(AMPIEZZA + 0.08) + 150 * s;
  const passo = largo ? Math.min(46, Math.max(30, 900 / N)) : Math.min(40, Math.max(28, 700 / N));
  const hT = 66 * s + N * passo + 20 * s + (vociLegenda(D.righe).length ? 46 * s : 0);
  const wP = largo ? W - dialW - 30 : W;
  const fineP = disegnaProfilo(ctx, 0, 40 * s, wP, D, s, '', true);
  const yT = largo ? Math.max(fineP, 34 + L * 1.06 + 80) + 40 : fineP + 50 * s + L * 1.06 + 120 * s;
  const H = Math.round(yT + hT + 30 * s + (largo ? 120 : 336) * s);
  if (cv.width !== W || cv.height !== H) { cv.width = W; cv.height = H; }
  ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, W, H);
  disegnaProfilo(ctx, 0, 40 * s, wP, D, s);
  if (largo) disegnaPendolo(ctx, W - dialW / 2, 34, L, th, s, nomeArea(D.bar));
  else disegnaPendolo(ctx, W / 2, fineP + 50 * s, L, th, s, nomeArea(D.bar));
  disegnaTracciato(ctx, { x: 0, y: yT, w: W, h: hT }, D, s, prog);
  disegnaMetriche(ctx, 0, yT + hT + 30 * s, W, D, s, !largo);
}
// Il moto: il tracciato si scrive dall'alto, il pendolo insegue l'ultimo voto e poi si assesta sul baricentro.
// Restituisce una funzione che, dato il tempo trascorso, dà angolo, avanzamento e se è tutto fermo.
function creaMoto(D) {
  const fine = angoloDi(D.bar), N = D.righe.length;
  const durata = Math.min(4.2, Math.max(1.6, N * 0.11));
  let th = -AMPIEZZA, v = 0, tPrec = 0;
  return t => {
    const dt = Math.min(0.033, Math.max(0, t - tPrec)); tPrec = t;
    const prog = Math.min(1, t / durata);
    let bersaglio = fine;
    if (prog < 1) {
      const prec = D.righe.slice(0, Math.floor(prog * N) + 1).reverse().find(r => r.x != null);
      bersaglio = prec ? angoloDi(prec.x) : 0;
    }
    v += (-38 * (th - bersaglio) - 2.6 * v) * dt; th += v * dt;
    const fermo = prog >= 1 && Math.abs(th - fine) < 0.002 && Math.abs(v) < 0.004;
    return { th: fermo ? fine : th, prog, fermo };
  };
}
function animaPannello() {
  if (!sismoD) return;
  cancelAnimationFrame(sismoAnim);
  if (MENO_MOTO || !sismoD.righe.length) { disegnaPannello(angoloDi(sismoD.bar), 1); return; }
  const moto = creaMoto(sismoD);
  let t0 = null;
  const passo = now => {
    if (t0 == null) t0 = now;
    const m = moto((now - t0) / 1000);
    disegnaPannello(m.th, m.prog);
    if (!m.fermo) sismoAnim = requestAnimationFrame(passo);
  };
  sismoAnim = requestAnimationFrame(passo);
}

// ===== Video: la stessa animazione registrata dalla tela, tutto nel browser =====
const FORMATO_VIDEO = (() => {
  if (typeof MediaRecorder === 'undefined' || !HTMLCanvasElement.prototype.captureStream) return null;
  // prima H.264 (va bene per Instagram e X), poi quello che il browser sa fare
  for (const [mime, ext] of [['video/mp4;codecs=avc1.640028', 'mp4'], ['video/mp4;codecs=avc1.4d0028', 'mp4'], ['video/mp4;codecs=avc1', 'mp4'], ['video/mp4', 'mp4'], ['video/webm;codecs=vp9', 'webm'], ['video/webm', 'webm']])
    if (MediaRecorder.isTypeSupported(mime)) return { mime, ext };
  return null;
})();
let registrando = false;
function registraVideo(formato) {
  return new Promise((risolvi, rifiuta) => {
    const D = datiSismografo();
    const cv = document.createElement('canvas');
    disegnaSismografo(cv, formato, D, -AMPIEZZA, 0);
    const flusso = cv.captureStream(30);
    const rec = new MediaRecorder(flusso, { mimeType: FORMATO_VIDEO.mime, videoBitsPerSecond: 8e6 });
    const pezzi = [];
    rec.ondataavailable = e => { if (e.data && e.data.size) pezzi.push(e.data); };
    rec.onstop = () => risolvi(new Blob(pezzi, { type: FORMATO_VIDEO.mime.split(';')[0] }));
    rec.onerror = e => rifiuta(e.error || e);
    const moto = creaMoto(D);
    const attesa = 0.6, coda = 2.6; // un attimo fermo all'inizio, poi l'immagine finale resta qualche secondo
    let t0 = null, fermoDa = null;
    rec.start(250);
    const passo = now => {
      if (t0 == null) t0 = now;
      const t = (now - t0) / 1000;
      const m = t < attesa ? { th: -AMPIEZZA, prog: 0, fermo: false } : moto(t - attesa);
      disegnaSismografo(cv, formato, D, m.th, m.prog);
      const tr = flusso.getVideoTracks()[0];
      if (tr && tr.requestFrame) tr.requestFrame();
      if (m.fermo && fermoDa == null) fermoDa = t;
      if ((fermoDa != null && t - fermoDa > coda) || t > 20) { rec.stop(); return; }
      requestAnimationFrame(passo);
    };
    requestAnimationFrame(passo);
  });
}
async function scaricaVideo() {
  if (registrando || !FORMATO_VIDEO) return;
  registrando = true;
  const btn = $('#scarica-video');
  btn.disabled = true; btn.classList.add('in-corso');
  annuncia('Sto registrando il video: tieni aperta questa pagina per qualche secondo.');
  try {
    await fontPronti;
    const formato = formatoScelto === 'lista' ? 'post' : formatoScelto;
    const blob = await registraVideo(formato);
    const nome = `il-mio-sismografo-del-voto-${FORMATI[formato].file}.${FORMATO_VIDEO.ext}`;
    const file = typeof File !== 'undefined' ? new File([blob], nome, { type: blob.type }) : null;
    if (MENU_CONDIVISIONE && file && navigator.canShare && navigator.canShare({ files: [file] })) {
      try { await navigator.share({ files: [file] }); annuncia(''); return; } catch (e) { if (e && e.name === 'AbortError') { annuncia(''); return; } }
    }
    const url = URL.createObjectURL(blob);
    const a = el('a', { href: url, download: nome }); document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
    annuncia(`Video scaricato: ${FORMATI[formato].nome}, ${FORMATO_VIDEO.ext.toUpperCase()}.`);
  } catch (e) {
    annuncia('Video non creato: questo browser non riesce a registrare la tela. Scarica l’immagine.');
  } finally {
    registrando = false; btn.disabled = false; btn.classList.remove('in-corso');
  }
}
let sismoTimer = null, sismoFirma = '';
function aggiornaSismografo() {
  clearTimeout(sismoTimer);
  sismoTimer = setTimeout(() => fontPronti.then(() => {
    const D = datiSismografo();
    const firma = JSON.stringify([pesoNazionale, D.righe.map(r => [r.k, r.x, r.esito, r.colore && r.colore.c])]);
    const cambiato = firma !== sismoFirma;
    sismoFirma = firma; sismoD = D;
    const box = $('#s-sismografo');
    if (box) box.hidden = !elenco.length;
    const testo = $('#sismo-testo');
    if (testo) testo.textContent = D.profilo ? `${D.profilo.nome}. ${D.profilo.descr} ${metriche(D).map(m => `${m.l}: ${m.v}`).join('. ')}.` : 'Il pendolo è fermo: segna come hai votato in almeno tre consultazioni.';
    if (cambiato) sismoDaAnimare = true;
    if (sismoDaAnimare && sismoInVista) { sismoDaAnimare = false; animaPannello(); } else disegnaPannello(angoloDi(D.bar), 1);
  }), 260);
}
function testoSismografo() {
  const D = datiSismografo();
  const P = D.profilo;
  return ['Il mio sismografo del voto 🇮🇹', '', P ? `${P.nome}: ${P.descr}` : 'Il pendolo è fermo.', ...metriche(D).map(m => `${m.l}: ${m.v} (${m.s})`), '', 'Scopri il tuo: ' + indirizzoLink()].join('\n');
}
(function avviaSismografo() {
  const cv = $('#sismo');
  if (!cv) return;
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(voci => {
      sismoInVista = voci.some(v => v.isIntersecting);
      if (sismoInVista && sismoDaAnimare && sismoD) { sismoDaAnimare = false; animaPannello(); }
    }, { threshold: 0.2 }).observe(cv);
  } else sismoInVista = true;
  let larghezza = cv.clientWidth;
  window.addEventListener('resize', () => { if (Math.abs(cv.clientWidth - larghezza) > 40) { larghezza = cv.clientWidth; disegnaPannello(angoloDi(sismoD ? sismoD.bar : 0), 1); } });
  $('#sismo-replay').addEventListener('click', animaPannello);
  document.querySelectorAll('input[name=peso]').forEach(r => r.addEventListener('change', () => { pesoNazionale = +r.value; programmaAnteprima(); }));
  const bv = $('#scarica-video');
  // il video è un di più: solo dove il browser registra in MP4, il formato che Instagram e X accettano
  if (bv && FORMATO_VIDEO && FORMATO_VIDEO.ext === 'mp4') {
    bv.addEventListener('click', scaricaVideo);
    const mostra = () => { bv.hidden = contenuto !== 'sismografo'; };
    document.querySelectorAll('input[name=contenuto]').forEach(r => r.addEventListener('change', mostra));
    mostra();
  }
  $('#sismo-usa').addEventListener('click', () => {
    const r = document.querySelector('input[name=contenuto][value=sismografo]');
    r.checked = true; r.dispatchEvent(new Event('change'));
    $('#s-immagine').scrollIntoView({ behavior: MENO_MOTO ? 'auto' : 'smooth' });
  });
  aggiornaSismografo();
})();
