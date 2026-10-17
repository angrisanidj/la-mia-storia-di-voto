'use strict';
// ===== Le immagini principali: la tessera elettorale, il quadrante del voto, le croci sulla scheda =====
// Tutto si disegna nel browser, a partire dalle risposte in memoria. Usa le funzioni comuni di app.js
// (FORMATI, elenco, statoDi, risposta, coloreVoto, nastroEMarchio, disegnaPiede) e di sismografo.js (trovaLista).

const IMG = (() => {
  const reSegni = new RegExp(`(${SEGNI.map(x => x.e).join('|')})️?`, 'gu');
  const pulisci = t => (t || '').replace(reSegni, '').replace(/\s+/g, ' ').trim();
  const luce = hex => { const n = parseInt((hex || '#888888').slice(1), 16); return (0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255; };
  const MESI_B = ['GEN', 'FEB', 'MAR', 'APR', 'MAG', 'GIU', 'LUG', 'AGO', 'SET', 'OTT', 'NOV', 'DIC'];
  const siDi = t => /^s[iì](\s|$)/i.test(t), noDi = t => /^no(\s|$)/i.test(t);
  const siglaNaz = t => t.replace(/\s*\(.*\)$/, '').split(/[\s-]/)[0].slice(0, 5);
  // generatore pseudo-casuale stabile: la stessa immagine a ogni disegno
  let seme = 7;
  const caso = () => { seme = (seme * 16807) % 2147483647; return (seme - 1) / 2147483646; };

  function tela(cv, formato) {
    const F = FORMATI[formato] || FORMATI.post;
    const W = F.W, H = F.H || 1350;
    cv.width = W; cv.height = H;
    const ctx = cv.getContext('2d');
    ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, W, H);
    const [alto, basso] = F.sicuro || [0, 0];
    return { F, W, H, ctx, alto, basso, m: 84, oriz: !!F.orizzontale };
  }
  // testata comune: nastro, marchio, titolo (quello scelto o quello di serie) e una riga sotto
  function testata(ctx, W, m, alto, titoloDiSerie, sotto, maxW) {
    nastroEMarchio(ctx, W, m, alto + 96, 1);
    const titolo = $('#titolo').value.trim() || titoloDiSerie;
    let c = 58;
    ctx.font = `700 ${c}px ${TIT}`;
    while (c > 36 && ctx.measureText(titolo).width > maxW) { c -= 2; ctx.font = `700 ${c}px ${TIT}`; }
    ctx.fillStyle = C.ink; ctx.fillText(titolo, m, alto + 200);
    if (sotto) {
      let s = 25; ctx.font = `400 ${s}px ${TXT}`;
      while (s > 17 && ctx.measureText(sotto).width > maxW) { s -= 1; ctx.font = `400 ${s}px ${TXT}`; }
      ctx.fillStyle = C.grigio; ctx.fillText(sotto, m, alto + 244);
    }
  }

  // voti in ordine: Camera e Senato uguali una volta sola
  function voti() {
    const out = [];
    for (const o of elenco) {
      const st = statoDi(o);
      if (st === 'escl') continue;
      const testo = pulisci(risposta(o.key).testo);
      const p = out[out.length - 1];
      if (o.ramo === 'S' && p && p.o.gruppo === o.gruppo && p.testo === testo && p.non === (st === 'non')) continue;
      const k = o.prov ? 'prov' : o.tipo;
      const col = coloreVoto(o);
      const si = siDi(testo), no = noDi(testo);
      let sig = '';
      if (k === 'ref') sig = si ? 'SÌ' : no ? 'NO' : '';
      else if (k === 'pol' || k === 'eur') sig = siglaNaz(testo);
      else sig = { reg: 'R', prov: 'P', com: 'C', bal: 'B' }[k] || '';
      out.push({ o, d: o.d, k, non: st === 'non', vuoto: st !== 'non' && !testo, testo, c: col && !col.vuoto ? col.c : null, si, no, sig });
    }
    return out;
  }
  const etichettaTipo = v => ({ pol: v.o.ramo === 'S' ? 'Senato' : 'Camera', eur: 'Europee', reg: 'Regionali', prov: 'Provinciali', com: 'Comunali', bal: 'Ballottaggio', ref: 'Referendum' }[v.k] || '');

  // =========================================================== LA TESSERA ELETTORALE
  // Un timbro per ogni giorno al seggio, 18 caselle per tessera come quella vera.
  function tessera(cv, formato) {
    const { W, H, ctx, alto, basso, m, oriz } = tela(cv, formato);
    seme = 7;
    const INK = '#3E3A8C', CARTA = '#F4F1E6', BORDO = '#D9D3BE', TRATTO = '#B9B096';
    const giorni = new Map();
    for (const o of elenco) {
      const st = statoDi(o);
      if (st === 'escl') continue;
      const testo = pulisci(risposta(o.key).testo);
      const g = giorni.get(o.d) || { d: o.d, voci: [] };
      g.voci.push({ o, st, testo, col: coloreVoto(o) });
      giorni.set(o.d, g);
    }
    const lista = [...giorni.values()].sort((a, b) => a.d.localeCompare(b.d));
    for (const g of lista) {
      const ok = g.voci.filter(v => v.st === 'ok' && v.testo);
      g.stato = ok.length ? 'timbro' : g.voci.some(v => v.st === 'non') ? 'non' : 'vuoto';
      const visti = new Set();
      g.bollini = ok.filter(v => { const k = (v.o.gruppo || v.o.key) + '|' + v.testo; if (visti.has(k)) return false; visti.add(k); return true; });
    }
    const timbri = lista.filter(g => g.stato === 'timbro').length;
    const non = lista.filter(g => g.stato === 'non').length;
    const nT = Math.max(1, Math.ceil(lista.length / 18));
    const anni = lista.length ? +lista[lista.length - 1].d.slice(0, 4) - +lista[0].d.slice(0, 4) + 1 : 0;
    const sotto = lista.length
      ? `${timbri} ${timbri === 1 ? 'timbro' : 'timbri'} in ${anni} ${anni === 1 ? 'anno' : 'anni'}, ${nT} ${nT === 1 ? 'tessera' : 'tessere'}${non ? `, ${non} ${non === 1 ? 'casella vuota' : 'caselle vuote'}` : ''}`
      : 'Segna dove hai votato: per ogni giorno al seggio, un timbro';
    testata(ctx, W, m, alto, 'La mia tessera elettorale', sotto, W - 2 * m);

    // disposizione: tessere orizzontali (6×3) o verticali (3×6), in una o più colonne; si sceglie
    // quella che dà le caselle più grandi con una proporzione vicina a quella dei timbri
    const y0 = alto + 290, yFine = H - basso - 150, larg = W - 2 * m, alt = yFine - y0;
    const gap = 22, hTit = 34, pad = 14;
    let best = null;
    for (const [cB, rB] of [[6, 3], [3, 6]]) for (let colT = 1; colT <= nT; colT++) {
      const rigT = Math.ceil(nT / colT);
      const wT = (larg - gap * (colT - 1)) / colT, hT = (alt - gap * (rigT - 1)) / rigT;
      const wBox = (wT - 2 * pad) / cB, hBox = (hT - hTit - pad) / rB;
      const voto = Math.min(wBox / 2.1, hBox);
      if (!best || voto > best.voto) best = { cB, rB, colT, rigT, wT, hT, wBox, hBox, voto };
    }
    let { cB, rB, colT, wT, hT, wBox, hBox, rigT } = best;
    // caselle non troppo alte: il resto si lascia come margine, centrato
    if (hBox > wBox * 0.62) { hBox = wBox * 0.62; hT = hTit + pad + hBox * rB; }
    const totH = rigT * hT + (rigT - 1) * gap, yIn = y0 + Math.max(0, (alt - totH) / 2);
    const sk = Math.min(1.25, Math.max(0.7, hBox / 78));
    const sigla = v => {
      if (v.o.tipo === 'ref') return siDi(v.testo) ? 'SÌ' : noDi(v.testo) ? 'NO' : 'REF';
      if (v.o.tipo === 'pol' || v.o.tipo === 'eur') return siglaNaz(v.testo);
      return v.o.prov ? 'P' : v.o.tipo === 'bal' ? 'B' : v.o.tipo === 'reg' ? 'R' : v.o.tipo === 'com' ? 'C' : '·';
    };
    for (let t = 0; t < nT; t++) {
      const xT = m + (t % colT) * (wT + gap), yT = yIn + Math.floor(t / colT) * (hT + gap);
      const parte = lista.slice(t * 18, t * 18 + 18);
      ctx.save(); ctx.shadowColor = 'rgba(60,50,20,0.10)'; ctx.shadowBlur = 10; ctx.shadowOffsetY = 3;
      ctx.beginPath(); ctx.roundRect(xT, yT, wT, hT, 10); ctx.fillStyle = CARTA; ctx.fill(); ctx.restore();
      ctx.strokeStyle = BORDO; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.roundRect(xT, yT, wT, hT, 10); ctx.stroke();
      const a0 = parte.length ? parte[0].d.slice(0, 4) : '', a1 = parte.length ? parte[parte.length - 1].d.slice(0, 4) : '';
      ctx.font = `700 15px ${TXT}`; ctx.fillStyle = '#8A7F5E'; ctx.textAlign = 'left';
      ctx.fillText(`TESSERA N. ${t + 1}`, xT + pad, yT + 24);
      ctx.textAlign = 'right'; ctx.font = `600 15px ${TXT}`;
      ctx.fillText(a0 === a1 ? a0 : `${a0} – ${a1}`, xT + wT - pad, yT + 24); ctx.textAlign = 'left';
      for (let i = 0; i < 18; i++) {
        const c = i % cB, r = Math.floor(i / cB);
        const x = xT + pad + c * wBox, y = yT + hTit + r * hBox;
        ctx.strokeStyle = TRATTO; ctx.lineWidth = 1; ctx.strokeRect(x + 0.5, y + 0.5, wBox, hBox);
        ctx.font = `600 ${Math.round(11 * sk)}px ${TXT}`; ctx.fillStyle = '#A99F80'; ctx.fillText(String(t * 18 + i + 1), x + 6, y + 6 + 10 * sk);
        const g = parte[i];
        if (!g) continue;
        const cx = x + wBox / 2 + 3, cy = y + hBox / 2 + 4;
        const dt = new Date(g.d + 'T12:00:00Z'), dataT = `${dt.getUTCDate()} ${MESI_B[dt.getUTCMonth()]} ${dt.getUTCFullYear()}`;
        if (g.stato !== 'timbro') {
          // casella senza timbro: solo la data, sbiadita
          ctx.font = `600 ${Math.round(13 * sk)}px ${TXT}`; ctx.fillStyle = g.stato === 'non' ? '#B8AE90' : '#D2CBB3'; ctx.textAlign = 'center';
          ctx.fillText(dataT, cx, cy + 4); ctx.textAlign = 'left';
          continue;
        }
        const ang = (caso() - 0.5) * 0.26, dx = (caso() - 0.5) * 6, dy = (caso() - 0.5) * 3;
        const sw = wBox * 0.80, sh = hBox * 0.70;
        ctx.save(); ctx.translate(cx + dx, cy + dy); ctx.rotate(ang);
        ctx.globalAlpha = 0.82 + caso() * 0.12;
        ctx.strokeStyle = INK; ctx.lineWidth = 2.6 * sk;
        ctx.beginPath(); ctx.roundRect(-sw / 2, -sh / 2, sw, sh, 9 * sk); ctx.stroke();
        ctx.lineWidth = 1.1; ctx.beginPath(); ctx.roundRect(-sw / 2 + 4 * sk, -sh / 2 + 4 * sk, sw - 8 * sk, sh - 8 * sk, 6 * sk); ctx.stroke();
        ctx.fillStyle = INK; ctx.textAlign = 'center';
        const fsS = Math.min(8.5 * sk, sh * 0.12, sw / 13);
        ctx.font = `700 ${fsS}px ${TXT}`; ctx.fillText('SEZIONE ELETTORALE', 0, -sh / 2 + 4 * sk + fsS + 3);
        let fsD = Math.min(17 * sk, sh * 0.23); ctx.font = `700 ${fsD}px ${TIT}`;
        while (ctx.measureText(dataT).width > sw - 14 && fsD > 8) { fsD -= 1; ctx.font = `700 ${fsD}px ${TIT}`; }
        ctx.fillText(dataT, 0, -sh * 0.04);
        const bs = g.bollini.slice(0, 4);
        const rB2 = Math.min(sh * 0.2, (sw - 14) / (bs.length * 2.3));
        const totW = bs.length * rB2 * 2 + (bs.length - 1) * rB2 * 0.35;
        ctx.globalAlpha = 1;
        bs.forEach((v, j) => {
          const bx = -totW / 2 + rB2 + j * rB2 * 2.35, by = sh * 0.22;
          const col = v.o.tipo === 'ref' ? (siDi(v.testo) ? C.verde : noDi(v.testo) ? C.rosso : C.grigio) : (v.col && !v.col.vuoto ? v.col.c : C.grigio);
          ctx.beginPath(); ctx.arc(bx, by, rB2, 0, 2 * Math.PI); ctx.fillStyle = col; ctx.fill();
          if (col.toUpperCase() === '#FFFFFF') { ctx.strokeStyle = '#9AA2AF'; ctx.lineWidth = 1.5; ctx.stroke(); }
          const sg = sigla(v);
          for (const fs of [rB2 * 0.82, rB2 * 0.68, rB2 * 0.56]) {
            ctx.font = `700 ${fs}px ${TXT}`;
            if (ctx.measureText(sg).width <= rB2 * 1.75) { ctx.fillStyle = luce(col) < 0.6 ? '#fff' : C.ink; ctx.fillText(sg, bx, by + fs * 0.36); break; }
          }
        });
        // grana dell'inchiostro
        ctx.globalAlpha = 0.55; ctx.fillStyle = CARTA;
        for (let k = 0; k < 22; k++) { const px = (caso() - 0.5) * sw, py = (caso() - 0.5) * sh; ctx.fillRect(px, py, 1 + caso() * 2.2, 1 + caso() * 1.6); }
        ctx.restore();
      }
    }
    disegnaPiede(ctx, m, H - basso - 78, W, m);
  }

  // =========================================================== LE CROCI SULLA SCHEDA
  function croci(cv, formato) {
    const { W, H, ctx, alto, basso, m } = tela(cv, formato);
    seme = 11;
    const V = voti();
    const votati = V.filter(v => !v.non && !v.vuoto).length;
    testata(ctx, W, m, alto, 'Le mie croci', V.length ? `${votati} ${votati === 1 ? 'croce' : 'croci'} a matita, dal ${V[0].d.slice(0, 4)} a oggi` : 'Segna come hai votato: una croce per ogni scheda', W - 2 * m);
    const x0 = m - 10, y0 = alto + 290, w = W - 2 * x0, h = H - basso - 160 - y0;
    ctx.save(); ctx.shadowColor = 'rgba(0,0,0,0.12)'; ctx.shadowBlur = 16; ctx.shadowOffsetY = 4;
    ctx.fillStyle = '#FBFAF6'; ctx.fillRect(x0, y0, w, h); ctx.restore();
    ctx.fillStyle = 'rgba(0,0,0,0.018)'; ctx.fillRect(x0, y0, w, h / 2); // la piega
    ctx.strokeStyle = '#D8D4C8'; ctx.lineWidth = 1.2; ctx.strokeRect(x0 + 10, y0 + 10, w - 20, h - 20);
    const n = Math.max(V.length, 1);
    // colonne: quelle che danno le celle più grandi (una cella è un po' più alta che larga)
    let col = 1, bestV = 0;
    for (let c = 1; c <= n; c++) { const r = Math.ceil(n / c), cw = (w - 40) / c, ch = (h - 40) / r; const v = Math.min(cw, ch / 1.15); if (v > bestV) { bestV = v; col = c; } }
    const righe = Math.ceil(n / col);
    const cw = (w - 40) / col, ch = Math.min((h - 40) / righe, cw * 1.6);
    const yIn = y0 + 20 + ((h - 40) - ch * righe) / 2;
    const R = Math.min(cw * 0.32, ch * 0.28);
    V.forEach((v, i) => {
      const cx = x0 + 20 + (i % col) * cw + cw / 2, cy = yIn + Math.floor(i / col) * ch + ch * 0.53;
      ctx.textAlign = 'center'; ctx.fillStyle = '#5E5A50'; ctx.font = `700 ${Math.min(17, ch * 0.13)}px ${TIT}`;
      ctx.fillText(v.d.slice(0, 4), cx, cy - R - ch * 0.08);
      const et = etichettaTipo(v) + ((v.k === 'pol' || v.k === 'eur') && v.sig ? ' · ' + v.sig : '');
      let fe = Math.min(13, ch * 0.105); ctx.font = `600 ${fe}px ${TXT}`;
      while (fe > 8 && ctx.measureText(et).width > cw - 6) { fe -= 0.5; ctx.font = `600 ${fe}px ${TXT}`; }
      ctx.fillStyle = '#8B8678'; ctx.fillText(et, cx, cy + R + fe + ch * 0.06);
      const spento = v.non || v.vuoto;
      ctx.globalAlpha = spento ? 0.28 : 1;
      if (v.k === 'ref') {
        const q = R * 0.78;
        [['SÌ', -q * 0.62], ['NO', q * 0.62]].forEach(([t, dx]) => {
          ctx.strokeStyle = '#3A3A3A'; ctx.lineWidth = 2; ctx.strokeRect(cx + dx - q / 2, cy - q / 2, q, q);
          ctx.fillStyle = '#3A3A3A'; ctx.font = `700 ${q * 0.42}px ${TXT}`; ctx.fillText(t, cx + dx, cy + q * 0.16);
        });
      } else {
        const c = v.c || '#C9CDD4';
        ctx.beginPath(); ctx.arc(cx, cy, R, 0, 2 * Math.PI); ctx.fillStyle = c; ctx.fill();
        ctx.lineWidth = 1.5; ctx.strokeStyle = c.toUpperCase() === '#FFFFFF' ? '#9AA2AF' : 'rgba(0,0,0,0.25)'; ctx.stroke();
        ctx.beginPath(); ctx.arc(cx, cy, R * 0.78, 0, 2 * Math.PI); ctx.strokeStyle = 'rgba(255,255,255,0.55)'; ctx.lineWidth = 2; ctx.stroke();
        if (v.k !== 'pol' && v.k !== 'eur' && v.sig) { ctx.font = `700 ${R * 0.62}px ${TIT}`; ctx.fillStyle = luce(c) < 0.6 ? 'rgba(255,255,255,0.35)' : 'rgba(22,27,38,0.3)'; ctx.fillText(v.sig, cx, cy + R * 0.22); }
      }
      ctx.globalAlpha = 1;
      if (spento || (v.k === 'ref' && v.si === v.no)) { ctx.textAlign = 'left'; return; }
      // la croce a matita copiativa: tratti sovrapposti e un po' storti
      let tx = cx, ty = cy, s = R * 0.92;
      if (v.k === 'ref') { tx = cx + (v.no ? R * 0.48 : -R * 0.48); s = R * 0.40; }
      ctx.lineCap = 'round';
      for (const [a, b] of [[[-1, -1], [1, 1]], [[1, -1], [-1, 1]]]) {
        for (let p = 0; p < 3; p++) {
          const j = () => (caso() - 0.5) * s * 0.12;
          ctx.beginPath(); ctx.moveTo(tx + a[0] * s + j(), ty + a[1] * s + j());
          ctx.quadraticCurveTo(tx + j() * 2, ty + j() * 2, tx + b[0] * s + j(), ty + b[1] * s + j());
          ctx.strokeStyle = `rgba(52,48,70,${0.45 + caso() * 0.25})`; ctx.lineWidth = Math.max(1, R / 28) * (1.1 + caso() * 1.3); ctx.stroke();
        }
      }
      ctx.lineCap = 'butt'; ctx.textAlign = 'left';
    });
    ctx.textAlign = 'left';
    disegnaPiede(ctx, m, H - basso - 78, W, m);
  }

  // =========================================================== IL QUADRANTE DEL VOTO
  // Ogni voto nel punto del quadrante politico del partito scelto. Orizzontale: economia (CHES lrecon);
  // verticale: valori (CHES galtan, conservatori in alto). Posizioni in dati/posizioni.js.
  const PN = () => (typeof PARTITI_NAZIONALI !== 'undefined' ? PARTITI_NAZIONALI : {});
  function datiNazionali(o) {
    const anno = o.d.slice(0, 4);
    if (o.tipo === 'pol' || o.tipo === 'eur') {
      const k = o.ramo === 'S' ? (PN()[`sen-${anno}`] ? `sen-${anno}` : `pol-${anno}`) : `${o.tipo}-${anno}`;
      return PN()[k] ? { k, liste: PN()[k].liste } : null;
    }
    // voti locali: le liste delle ultime politiche
    const pol = Object.keys(PN()).filter(k => k.startsWith('pol-')).sort();
    const k = pol.filter(k => k.slice(4) <= anno).pop() || pol[0];
    return k ? { k, liste: PN()[k].liste } : null;
  }
  function votiQuadrante() {
    const out = [], fuori = { civici: 0 };
    const POS = typeof POSIZIONI_PARTITI !== 'undefined' ? POSIZIONI_PARTITI : {};
    for (const o of elenco) {
      if (statoDi(o) !== 'ok' || o.tipo === 'ref') continue;
      const t = pulisci(risposta(o.key).testo);
      if (!t || /^Scheda (bianca|nulla)/i.test(t)) continue;
      const dn = datiNazionali(o);
      const l = dn && trovaLista(t, dn.liste);
      const p = l && POS[`${dn.k}|${l.b}`];
      if (!p) { fuori.civici++; continue; }
      const prec = out[out.length - 1];
      if (o.ramo === 'S' && prec && prec.o.gruppo === o.gruppo && prec.b === l.b) continue;
      const col = coloreVoto(o);
      out.push({ o, d: o.d, b: l.b, x: p[0], y: p[1], stima: !!p[2], naz: o.tipo === 'pol' || o.tipo === 'eur', c: col && !col.vuoto ? col.c : '#5A6372' });
    }
    return { voti: out, fuori };
  }
  const descrX = x => x < 3.5 ? 'economia di sinistra' : x < 4.5 ? 'economia di centrosinistra' : x <= 5.5 ? 'economia di centro' : x <= 6.5 ? 'economia di centrodestra' : 'economia di destra';
  const descrY = y => y < 3.5 ? 'valori progressisti' : y < 4.5 ? 'valori piuttosto progressisti' : y <= 5.5 ? 'valori moderati' : y <= 6.5 ? 'valori piuttosto conservatori' : 'valori conservatori';

  function quadrante(cv, formato) {
    const { W, H, ctx, alto, basso, m, oriz } = tela(cv, formato);
    const { voti, fuori } = votiQuadrante();
    const media = (l, k) => l.length ? l.reduce((a, v) => a + v[k], 0) / l.length : null;
    const N = voti.filter(v => v.naz), L = voti.filter(v => !v.naz);
    const pesa = k => { const a = media(N, k), b = media(L, k); return a != null && b != null ? 0.7 * a + 0.3 * b : (a ?? b); };
    const bx = pesa('x'), by = pesa('y');
    const sotto = bx == null ? 'Segna per chi hai votato: ogni partito ha il suo posto' : `Il mio baricentro: ${descrX(bx)}, ${descrY(by)}`;

    let S, X0, Y0;
    if (oriz) { S = H - 140; X0 = W - 60 - S; Y0 = 70; }
    else { const top = alto + 300, bot = H - basso - 245; S = Math.min(W - 2 * m - 40, bot - top); X0 = (W - S) / 2; Y0 = top + (bot - top - S) / 2; }
    testata(ctx, W, m, alto, 'Il quadrante del mio voto', oriz ? '' : sotto, oriz ? X0 - 80 - m : W - 2 * m);
    const px = x => X0 + x / 10 * S, py = y => Y0 + (1 - y / 10) * S;
    const sc = S / 830; // scala dei caratteri dentro il quadrato

    ctx.save(); ctx.beginPath(); ctx.roundRect(X0, Y0, S, S, 18); ctx.clip();
    for (const [c, fx, fy] of [['#FBF4EC', 0, 0], ['#EEF3FB', 0.5, 0], ['#FCEFEF', 0, 0.5], ['#EEF7F1', 0.5, 0.5]]) { ctx.fillStyle = c; ctx.fillRect(X0 + fx * S, Y0 + fy * S, S / 2, S / 2); }
    ctx.strokeStyle = 'rgba(22,27,38,0.05)'; ctx.lineWidth = 1;
    for (let i = 1; i < 10; i++) { if (i === 5) continue; ctx.beginPath(); ctx.moveTo(px(i), Y0); ctx.lineTo(px(i), Y0 + S); ctx.moveTo(X0, py(i)); ctx.lineTo(X0 + S, py(i)); ctx.stroke(); }
    ctx.strokeStyle = 'rgba(22,27,38,0.22)'; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(px(5), Y0); ctx.lineTo(px(5), Y0 + S); ctx.moveTo(X0, py(5)); ctx.lineTo(X0 + S, py(5)); ctx.stroke();
    const fA = Math.max(13, 17 * sc);
    ctx.font = `600 italic ${fA}px ${TXT}`; ctx.fillStyle = 'rgba(22,27,38,0.30)';
    ctx.textAlign = 'left'; ctx.fillText('Sinistra conservatrice', X0 + 18, Y0 + 14 + fA); ctx.fillText('Sinistra progressista', X0 + 18, Y0 + S - 18);
    ctx.textAlign = 'right'; ctx.fillText('Destra conservatrice', X0 + S - 18, Y0 + 14 + fA); ctx.fillText('Destra liberale', X0 + S - 18, Y0 + S - 18);
    ctx.restore();
    const wAng = 12 * fA;
    const occupati = [[X0, Y0, wAng, fA + 28], [X0 + S - wAng, Y0, wAng, fA + 28], [X0, Y0 + S - fA - 26, wAng, fA + 26], [X0 + S - wAng, Y0 + S - fA - 26, wAng, fA + 26]];
    const libero = (x, y, w, h) => !occupati.some(r => x < r[0] + r[2] && x + w > r[0] && y < r[1] + r[3] && y + h > r[1]);
    ctx.font = `700 16px ${TXT}`; ctx.fillStyle = '#8A93A1'; ctx.textAlign = 'center';
    ctx.fillText('CONSERVATORI', px(5), Y0 - 12); ctx.fillText('PROGRESSISTI', px(5), Y0 + S + 26);
    ctx.save(); ctx.translate(X0 - 14, py(5)); ctx.rotate(-Math.PI / 2); ctx.fillText('ECONOMIA DI SINISTRA', 0, 0); ctx.restore();
    ctx.save(); ctx.translate(X0 + S + 14, py(5)); ctx.rotate(Math.PI / 2); ctx.fillText('ECONOMIA DI DESTRA', 0, 0); ctx.restore();

    const RIF = typeof POSIZIONI_RIFERIMENTO !== 'undefined' ? POSIZIONI_RIFERIMENTO : {};
    for (const [, [x, y]] of Object.entries(RIF)) {
      ctx.save(); ctx.translate(px(x), py(y)); ctx.rotate(Math.PI / 4); ctx.strokeStyle = 'rgba(22,27,38,0.28)'; ctx.lineWidth = 1.5; ctx.strokeRect(-4, -4, 8, 8); ctx.restore();
    }
    // i voti, raggruppati per partito (posizione media)
    const gruppi = new Map();
    voti.forEach(v => { const g = gruppi.get(v.b) || { b: v.b, c: v.c, voti: [], stima: true }; g.voti.push(v); g.stima = g.stima && v.stima; g.c = v.c; gruppi.set(v.b, g); });
    const G = [...gruppi.values()];
    for (const g of G) { g.x = media(g.voti, 'x'); g.y = media(g.voti, 'y'); g.ax = px(g.x); g.ay = py(g.y); g.X = g.ax; g.Y = g.ay; g.r = (10 + Math.sqrt(g.voti.length) * 7) * Math.max(0.75, sc); }
    // le bolle si scostano quel tanto che basta per non coprirsi e non coprire il baricentro
    const corpi = G.slice();
    if (bx != null) corpi.push({ X: px(bx), Y: py(by), r: 30, fisso: true });
    for (let it = 0; it < 300; it++) {
      for (let i = 0; i < corpi.length; i++) for (let j = i + 1; j < corpi.length; j++) {
        const a = corpi[i], b = corpi[j];
        let dx = b.X - a.X, dy = b.Y - a.Y, d = Math.hypot(dx, dy);
        const min = a.r + b.r + 6;
        if (d >= min) continue;
        if (d < 0.01) { dx = 1; dy = 0.3; d = 1.04; }
        const sp = (min - d) / 2, ux = dx / d, uy = dy / d;
        if (a.fisso) { b.X += ux * sp * 2; b.Y += uy * sp * 2; }
        else if (b.fisso) { a.X -= ux * sp * 2; a.Y -= uy * sp * 2; }
        else { a.X -= ux * sp; a.Y -= uy * sp; b.X += ux * sp; b.Y += uy * sp; }
      }
      for (const c of corpi) if (!c.fisso) { c.X += (c.ax - c.X) * 0.02; c.Y += (c.ay - c.Y) * 0.02; c.X = Math.max(X0 + c.r, Math.min(X0 + S - c.r, c.X)); c.Y = Math.max(Y0 + c.r, Math.min(Y0 + S - c.r, c.Y)); }
    }
    // il percorso nel tempo, dal più vecchio (chiaro) al più recente (scuro)
    let ultimo = null;
    for (let i = 1; i < voti.length; i++) {
      const ga = gruppi.get(voti[i - 1].b), gb = gruppi.get(voti[i].b);
      if (ga === gb) continue;
      const f = i / voti.length;
      const mx = (ga.X + gb.X) / 2 - (gb.Y - ga.Y) * 0.18, my = (ga.Y + gb.Y) / 2 + (gb.X - ga.X) * 0.18;
      ctx.beginPath(); ctx.moveTo(ga.X, ga.Y); ctx.quadraticCurveTo(mx, my, gb.X, gb.Y);
      ctx.strokeStyle = `rgba(22,27,38,${0.06 + f * 0.22})`; ctx.lineWidth = 1.2 + f * 1.6; ctx.stroke();
      ultimo = [mx, my, gb];
    }
    G.sort((a, b) => b.voti.length - a.voti.length);
    for (const g of G) {
      const { X, Y, r } = g;
      if (Math.hypot(X - g.ax, Y - g.ay) > r * 0.6) {
        ctx.beginPath(); ctx.moveTo(g.ax, g.ay); ctx.lineTo(X, Y); ctx.strokeStyle = 'rgba(22,27,38,0.25)'; ctx.lineWidth = 1; ctx.stroke();
        ctx.beginPath(); ctx.arc(g.ax, g.ay, 2.5, 0, 2 * Math.PI); ctx.fillStyle = 'rgba(22,27,38,0.45)'; ctx.fill();
      }
      ctx.save(); ctx.shadowColor = 'rgba(0,0,0,0.16)'; ctx.shadowBlur = 8; ctx.shadowOffsetY = 2;
      ctx.beginPath(); ctx.arc(X, Y, r, 0, 2 * Math.PI); ctx.fillStyle = g.c; ctx.fill(); ctx.restore();
      ctx.lineWidth = 3; ctx.strokeStyle = '#fff'; if (g.stima) ctx.setLineDash([5, 4]); ctx.stroke(); ctx.setLineDash([]);
      if (g.c.toUpperCase() === '#FFFFFF') { ctx.strokeStyle = '#9AA2AF'; ctx.lineWidth = 1.5; ctx.stroke(); }
      if (g.voti.length > 1) { const fs = Math.min(r, 26); ctx.font = `700 ${fs}px ${TXT}`; ctx.fillStyle = luce(g.c) < 0.6 ? '#fff' : C.ink; ctx.textAlign = 'center'; ctx.fillText(String(g.voti.length), X, Y + fs * 0.36); }
      occupati.push([X - r, Y - r, 2 * r, 2 * r]);
    }
    if (ultimo) {
      const [mx, my, gb] = ultimo, a = Math.atan2(gb.Y - my, gb.X - mx);
      const tx = gb.X - Math.cos(a) * (gb.r + 3), ty = gb.Y - Math.sin(a) * (gb.r + 3);
      ctx.beginPath(); ctx.moveTo(tx, ty); ctx.lineTo(tx - Math.cos(a - 0.45) * 14, ty - Math.sin(a - 0.45) * 14); ctx.lineTo(tx - Math.cos(a + 0.45) * 14, ty - Math.sin(a + 0.45) * 14); ctx.closePath();
      ctx.fillStyle = 'rgba(22,27,38,0.55)'; ctx.fill();
    }
    if (bx != null) occupati.push([px(bx) - 30, py(by) - 44, 100, 74]);
    // etichette: sigla e anni, nel posto libero più vicino alla sua bolla e più lontano dalle altre
    const f1 = Math.max(15, 19 * sc), f2 = Math.max(12, 15 * sc);
    for (const g of G) {
      const { X, Y, r } = g;
      const anni = [...new Set(g.voti.map(v => v.d.slice(2, 4)))];
      const t1 = g.b, t2 = anni.length > 3 ? `’${anni[0]}–’${anni[anni.length - 1]}` : anni.map(a => '’' + a).join(' ');
      ctx.font = `700 ${f1}px ${TXT}`; const w1 = ctx.measureText(t1).width;
      ctx.font = `500 ${f2}px ${TXT}`; const w2 = ctx.measureText(t2).width;
      const w = Math.max(w1, w2) + 6, h = f1 + f2 + 6;
      const prove = [];
      for (const dist of [6, 34, 70]) for (const a of [0, Math.PI, -Math.PI / 2, Math.PI / 2, -Math.PI / 4, Math.PI / 4, -3 * Math.PI / 4, 3 * Math.PI / 4]) {
        const cx = X + Math.cos(a) * (r + dist), cy = Y + Math.sin(a) * (r + dist);
        prove.push([Math.cos(a) > 0.3 ? cx : Math.cos(a) < -0.3 ? cx - w : cx - w / 2, Math.sin(a) > 0.3 ? cy : Math.sin(a) < -0.3 ? cy - h : cy - h / 2, dist]);
      }
      const altri = G.filter(o => o !== g);
      let ok = null, meglio = -1e9;
      for (const pr of prove) {
        const [x, y, dist] = pr;
        if (!(x > X0 && x + w < X0 + S && y > Y0 && y + h < Y0 + S && libero(x, y, w, h))) continue;
        const cx = x + w / 2, cy = y + h / 2;
        const dOwn = Math.hypot(cx - X, cy - Y) - r;
        const dAlt = Math.min(1e4, ...altri.map(o => Math.hypot(cx - o.X, cy - o.Y) - o.r));
        const punti = Math.min(dAlt, 90) - dOwn * 0.9 - dist * 0.3;
        if (punti > meglio) { meglio = punti; ok = pr; }
      }
      ok = ok || prove[0];
      const [lx, ly] = ok; occupati.push([lx, ly, w, h]);
      if (ok[2] > 6) { const qx = Math.max(lx, Math.min(X, lx + w)), qy = Math.max(ly, Math.min(Y, ly + h)), a = Math.atan2(qy - Y, qx - X); ctx.beginPath(); ctx.moveTo(X + Math.cos(a) * r, Y + Math.sin(a) * r); ctx.lineTo(qx, qy); ctx.strokeStyle = 'rgba(22,27,38,0.3)'; ctx.lineWidth = 1; ctx.stroke(); }
      ctx.textAlign = 'left';
      ctx.font = `700 ${f1}px ${TXT}`; ctx.fillStyle = C.ink; ctx.fillText(t1, lx + 3, ly + f1 - 2);
      ctx.font = `500 ${f2}px ${TXT}`; ctx.fillStyle = C.grigio; ctx.fillText(t2, lx + 3, ly + f1 + f2 + 1);
    }
    ctx.font = `600 14px ${TXT}`; ctx.fillStyle = 'rgba(22,27,38,0.38)'; ctx.textAlign = 'left';
    for (const [n, [x, y]] of Object.entries(RIF)) {
      const X = px(x), Y = py(y), w = ctx.measureText(n).width + 4;
      const ok = [[X + 9, Y - 8], [X - 9 - w, Y - 8], [X - w / 2, Y - 24], [X - w / 2, Y + 8]].find(([a, b]) => libero(a, b, w, 16) && a > X0 && a + w < X0 + S);
      if (!ok) continue;
      occupati.push([ok[0], ok[1], w, 16]); ctx.fillText(n, ok[0] + 2, ok[1] + 12);
    }
    if (bx != null) {
      const X = px(bx), Y = py(by);
      ctx.beginPath(); ctx.arc(X, Y, 22, 0, 2 * Math.PI); ctx.strokeStyle = C.ink; ctx.lineWidth = 3; ctx.stroke();
      ctx.beginPath(); ctx.arc(X, Y, 5, 0, 2 * Math.PI); ctx.fillStyle = C.ink; ctx.fill();
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { ctx.beginPath(); ctx.moveTo(X + dx * 26, Y + dy * 26); ctx.lineTo(X + dx * 36, Y + dy * 36); ctx.stroke(); }
      ctx.font = `800 17px ${TXT}`; const w = ctx.measureText('IO').width + 18;
      const lx = X + 30 + w < X0 + S ? X + 30 : X - 30 - w;
      ctx.beginPath(); ctx.roundRect(lx, Y - 40, w, 26, 13); ctx.fillStyle = C.ink; ctx.fill();
      ctx.fillStyle = '#fff'; ctx.textAlign = 'center'; ctx.fillText('IO', lx + w / 2, Y - 21);
    }
    ctx.textAlign = 'left';
    // note
    const nota = [`${voti.length} ${voti.length === 1 ? 'voto' : 'voti'} nel quadrante`];
    if (fuori.civici) nota.push(`${fuori.civici} a liste civiche o candidati, fuori dal quadrante`);
    ctx.fillStyle = '#8A93A1';
    if (oriz) {
      ctx.font = `400 25px ${TXT}`; ctx.fillStyle = C.grigio;
      (bx == null ? [sotto] : ['Il mio baricentro:', `${descrX(bx)},`, descrY(by)]).forEach((r, i) => ctx.fillText(r, m, alto + 250 + i * 34));
      ctx.font = `500 18px ${TXT}`; ctx.fillStyle = '#8A93A1';
      nota.forEach((r, i) => ctx.fillText(r, m, alto + 390 + i * 26));
      ['Posizioni dei partiti:', 'Chapel Hill Expert Survey 1999–2024', '◇ i partiti nel 2024', 'bordo tratteggiato = stima'].forEach((r, i) => ctx.fillText(r, m, alto + 470 + i * 24));
    } else {
      ctx.font = `500 16px ${TXT}`; ctx.textAlign = 'center';
      ctx.fillText(nota.join(' · '), W / 2, Y0 + S + 58);
      ctx.fillText('Posizioni: Chapel Hill Expert Survey 1999–2024 · ◇ i partiti nel 2024 · bordo tratteggiato = stima', W / 2, Y0 + S + 82);
      ctx.textAlign = 'left';
    }
    disegnaPiede(ctx, m, H - basso - 78, oriz ? X0 - 50 + m : W, m);
  }

  return { tessera, croci, quadrante, votiQuadrante };
})();
