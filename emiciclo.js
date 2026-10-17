// L'emiciclo della mia storia di voto: l'immagine principale. Ogni voto è un seggio: l'angolo è il tempo (da sinistra
// il primo voto, a destra oggi), l'anello è il tipo di elezione (dal centro: politiche, europee, regionali, provinciali,
// comunali; fuori i referendum), il colore è quello del voto. Al centro, come i seggi di un parlamento, le volte al voto.
// Camera e Senato votati in modo diverso: un seggio diviso a metà. Ballottaggio: un anello bianco dentro il seggio.
// Astensione: seggio tratteggiato. Referendum: segno di spunta verde (Sì) o croce rossa (No).
function disegnaEmicicloVoto(cv, formato) {
  const F = FORMATI[formato];
  const W = F.W, H = F.H || 1350;
  const [alto, basso] = F.sicuro || [0, 0];
  const ctx = cv.getContext('2d');
  cv.width = W; cv.height = H;
  ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, W, H);
  const m = 84, larg = W - 2 * m;

  // ---- dati
  const ANELLI = [['pol', 'Politiche'], ['eur', 'Europee'], ['reg', 'Regionali'], ['prov', 'Provinciali'], ['com', 'Comunali'], ['ref', 'Referendum']];
  const tipoDi = o => o.prov ? 'prov' : o.tipo === 'bal' ? 'com' : o.tipo === 'ref' ? 'ref' : o.tipo;
  const reSegni = new RegExp(`(${SEGNI.map(x => x.e).join('|')})️?`, 'gu');
  const seggi = [];
  for (const o of elenco) {
    const st = statoDi(o);
    if (st === 'escl') continue;
    const r = risposta(o.key);
    const testo = (r.testo || '').replace(reSegni, '').replace(/\s+/g, ' ').trim();
    const p = seggi[seggi.length - 1];
    // Camera e Senato con lo stesso voto: un seggio solo
    if (o.ramo === 'S' && p && p.gruppo === o.gruppo) {
      if (!(p.testo === testo && p.non === (st === 'non'))) p.senato = { non: st === 'non', vuoto: st !== 'non' && !testo, testo, col: coloreVoto(o) };
      continue;
    }
    seggi.push({ o, d: o.d, k: tipoDi(o), bal: o.tipo === 'bal', non: st === 'non', vuoto: st !== 'non' && !testo, testo, col: coloreVoto(o), gruppo: o.gruppo,
      si: /^s[iì](\s|$)/i.test(testo) ? 1 : 0, no: /^no(\s|$)/i.test(testo) ? 1 : 0 });
  }
  const anelli = ANELLI.filter(([k]) => seggi.some(s => s.k === k));
  if (!seggi.length) {
    nastroEMarchio(ctx, W, m, alto + 96, 1);
    ctx.font = `400 28px ${TXT}`; ctx.fillStyle = C.grigio;
    ctx.fillText('Inserisci anno di nascita e comune per vedere qui il tuo emiciclo.', m, alto + 260);
    disegnaPiede(ctx, m, H - basso - 78, W, m);
    return;
  }
  const giorno = d => Date.parse(d + 'T12:00:00Z') / 864e5;
  const anno0 = +seggi.reduce((a, s) => s.d < a ? s.d : a, '9999').slice(0, 4);
  const anno1 = Math.max(+seggi.reduce((a, s) => s.d > a ? s.d : a, '0').slice(0, 4), anno0 + 4);
  const t0 = giorno(`${anno0}-01-01`), t1 = giorno(`${anno1}-12-31`);

  // ---- impaginazione per formato
  const orizz = !!F.orizzontale;
  const titolo = $('#titolo').value.trim();
  const firma = $('#firma').value.trim();
  let cx, cy, R, yLeg, xLeg, wLeg;
  if (orizz) {
    R = 380; cx = 64 + R; cy = H - 175;
    xLeg = cx + R + 90; wLeg = W - m - xLeg; yLeg = titolo ? 300 : Math.max(230, cy - R / 2 - 140);
  } else {
    const q = formato === 'quadrata';
    R = q ? 380 : 500;
    cx = W / 2;
    // altezza della legenda: una riga ogni due gruppi di colore, più la riga dei referendum
    const nGruppi = new Set(seggi.flatMap(s => s.senato ? [s, s.senato] : [s]).filter(s => s.k !== 'ref' && !s.non && !s.vuoto && s.col && !s.col.vuoto).map(s => s.col.c)).size;
    const st = formato === 'storia';
    const hLeg = Math.ceil(Math.min(nGruppi, q ? 8 : 12) / 2) * (q ? 42 : st ? 70 : 58) + 70;
    const inizio = alto + (q ? 112 : 140) + (titolo ? 64 : 0), fine = H - basso - 160;
    const extra = Math.max(0, fine - inizio - (R + 50) - hLeg - 40);
    cy = inizio + extra * 0.25 + R + 50;
    xLeg = m; wLeg = larg; yLeg = cy + 40 + extra * 0.35 + (q ? 24 : 40);
  }
  nastroEMarchio(ctx, W, m, alto + 96, 1);
  if (titolo && !orizz) { ctx.font = `700 54px ${TIT}`; ctx.fillStyle = C.ink; ctx.fillText(titolo, m, alto + 196); }
  if (firma) { ctx.font = `600 26px ${TXT}`; ctx.fillStyle = C.grigio; ctx.textAlign = 'right'; ctx.fillText(firma, W - m, alto + 106); ctx.textAlign = 'left'; }

  // geometria degli anelli
  const r0 = R * 0.34, rN = R * 0.97;
  const passoR = (rN - r0) / anelli.length;
  const rAnello = i => r0 + passoR * (i + 0.5);
  const fendL = 0.5, fendR = 0.04;           // spicchio a sinistra per i nomi degli anelli
  const ang = t => Math.PI - fendL - (t - t0) / (t1 - t0) * (Math.PI - fendL - fendR);
  const xy = (r, a) => [cx + r * Math.cos(a), cy - r * Math.sin(a)];

  // guide: anelli sottili e linee radiali degli anni tondi
  ctx.lineCap = 'round';
  // anelli alternati appena velati, come le file di un'aula
  anelli.forEach((_, i) => {
    if (i % 2) return;
    ctx.beginPath(); ctx.arc(cx, cy, rAnello(i) + passoR / 2, Math.PI, 2 * Math.PI); ctx.arc(cx, cy, rAnello(i) - passoR / 2, 2 * Math.PI, Math.PI, true); ctx.closePath();
    ctx.fillStyle = '#F6F7F9'; ctx.fill();
  });
  anelli.forEach((_, i) => {
    ctx.beginPath(); ctx.arc(cx, cy, rAnello(i), Math.PI + 0.02, 2 * Math.PI - 0.01);
    ctx.strokeStyle = '#E9ECF0'; ctx.lineWidth = 1.2; ctx.stroke();
  });
  const anniTacca = [];
  for (let a = Math.ceil(anno0 / 5) * 5; a <= anno1; a += 5) anniTacca.push(a);
  if (!anniTacca.includes(anno0) && (anniTacca[0] - anno0) >= 3) anniTacca.unshift(anno0);
  ctx.font = `600 ${orizz ? 19 : 20}px ${TXT}`;
  for (const a of anniTacca) {
    const an = ang(giorno(`${a}-01-01`));
    const [x1, y1] = xy(r0 - 6, an), [x2, y2] = xy(rN + 10, an);
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.strokeStyle = '#F1F2F5'; ctx.lineWidth = 1.2; ctx.stroke();
    const [xt, yt] = xy(rN + 30, an);
    ctx.save(); ctx.translate(xt, yt); ctx.rotate(Math.PI / 2 - an);
    ctx.fillStyle = '#8A93A1'; ctx.textAlign = 'center'; ctx.fillText(String(a), 0, 6); ctx.restore();
  }

  // nomi degli anelli, scritti lungo l'anello nello spicchio di sinistra
  anelli.forEach(([k, nome], i) => {
    const r = rAnello(i);
    ctx.font = `600 ${Math.min(17, passoR * 0.42)}px ${TXT}`;
    ctx.fillStyle = '#7A8494';
    let a = Math.PI - 0.03;
    for (const ch of nome) {
      const da = ctx.measureText(ch).width / r;
      const am = a - da / 2;
      const [x, y] = xy(r, am);
      ctx.save(); ctx.translate(x, y); ctx.rotate(Math.atan2(Math.cos(am), Math.sin(am)));
      ctx.textAlign = 'center'; ctx.fillText(ch, 0, 5); ctx.restore();
      a -= da + 0.003;
    }
  });

  // ---- seggi: posizione nel tempo, poi si separano quelli troppo vicini lungo l'anello
  const luce = hex => { const n = parseInt(hex.slice(1), 16); return (0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255; };
  let rs = Math.min(passoR * 0.43, 30);
  anelli.forEach(([k], i) => {
    const r = rAnello(i), n = seggi.filter(s => s.k === k).length;
    const lungo = (ang(t0) - ang(t1)) * r;
    while (n * rs * 2.15 > lungo && rs > 6) rs *= 0.96;
  });
  anelli.forEach(([k], i) => {
    const r = rAnello(i);
    const qui = seggi.filter(s => s.k === k).sort((a, b) => a.d.localeCompare(b.d));
    const uMin = (Math.PI - ang(t0)) * r, uMax = (Math.PI - ang(t1)) * r;   // lunghezza d'arco disponibile
    const gap = rs * 2.15;
    const u = qui.map(s => (Math.PI - ang(giorno(s.d))) * r);
    for (let it = 0; it < 200; it++) {
      let mosso = false;
      for (let j = 1; j < u.length; j++) {
        const dd = u[j] - u[j - 1];
        if (dd < gap - 0.01) { const sp = (gap - dd) / 2; u[j - 1] -= sp; u[j] += sp; mosso = true; }
      }
      for (let j = 0; j < u.length; j++) u[j] = Math.min(uMax - rs, Math.max(uMin + rs, u[j]));
      if (!mosso) break;
    }
    qui.forEach((s, j) => { s.a = Math.PI - u[j] / r; s.r = r; s.rs = rs; });
  });
  for (const s of seggi) {
    if (s.a == null) continue;
    const [x, y] = xy(s.r, s.a), rs = s.rs;
    ctx.save();
    if (s.k === 'ref') {
      const c = s.non ? '#9AA2AF' : s.si && !s.no ? C.verde : s.no && !s.si ? C.rosso : s.vuoto ? '#D5D9E0' : C.ink;
      ctx.beginPath(); ctx.arc(x, y, rs - 1.5, 0, 2 * Math.PI); ctx.fillStyle = '#fff'; ctx.fill();
      ctx.lineWidth = 3; ctx.strokeStyle = c; if (s.non) ctx.setLineDash([4, 3.5]); ctx.stroke(); ctx.setLineDash([]);
      if (!s.non && !s.vuoto) {
        ctx.lineWidth = Math.max(2.4, rs * 0.16); ctx.strokeStyle = c; ctx.beginPath();
        if (s.no && !s.si) { const q = rs * 0.36; ctx.moveTo(x - q, y - q); ctx.lineTo(x + q, y + q); ctx.moveTo(x + q, y - q); ctx.lineTo(x - q, y + q); }
        else { ctx.moveTo(x - rs * 0.42, y + rs * 0.02); ctx.lineTo(x - rs * 0.1, y + rs * 0.34); ctx.lineTo(x + rs * 0.45, y - rs * 0.3); }
        ctx.stroke();
      }
    } else if (s.senato) {
      // Camera a sinistra, Senato a destra
      const meta = (v, a0, a1) => {
        ctx.beginPath(); ctx.moveTo(x, y); ctx.arc(x, y, rs - (v.non ? 1.5 : 0), a0, a1); ctx.closePath();
        if (v.non || v.vuoto || !v.col || v.col.vuoto) { ctx.fillStyle = '#fff'; ctx.fill(); ctx.setLineDash(v.non ? [4, 3.5] : []); ctx.lineWidth = 2; ctx.strokeStyle = '#9AA2AF'; ctx.stroke(); ctx.setLineDash([]); }
        else { ctx.fillStyle = v.col.c; ctx.fill(); if (v.col.c.toUpperCase() === '#FFFFFF') { ctx.lineWidth = 2; ctx.strokeStyle = '#9AA2AF'; ctx.stroke(); } }
      };
      meta(s, Math.PI / 2, Math.PI * 1.5); meta(s.senato, -Math.PI / 2, Math.PI / 2);
      ctx.beginPath(); ctx.moveTo(x, y - rs); ctx.lineTo(x, y + rs); ctx.lineWidth = 2; ctx.strokeStyle = '#fff'; ctx.stroke();
    } else if (s.non) {
      ctx.beginPath(); ctx.arc(x, y, rs - 1.5, 0, 2 * Math.PI); ctx.setLineDash([4, 3.5]); ctx.lineWidth = 2.2; ctx.strokeStyle = '#9AA2AF'; ctx.stroke(); ctx.setLineDash([]);
    } else if (s.vuoto || !s.col || s.col.vuoto) {
      ctx.beginPath(); ctx.arc(x, y, rs * 0.42, 0, 2 * Math.PI); ctx.fillStyle = '#E6E9EE'; ctx.fill();
    } else {
      const c = s.col.c, bianco = c.toUpperCase() === '#FFFFFF';
      ctx.beginPath(); ctx.arc(x, y, rs, 0, 2 * Math.PI); ctx.fillStyle = c; ctx.fill();
      if (bianco) { ctx.lineWidth = 2; ctx.strokeStyle = '#9AA2AF'; ctx.stroke(); }
      if (s.bal) { ctx.beginPath(); ctx.arc(x, y, rs * 0.52, 0, 2 * Math.PI); ctx.lineWidth = Math.max(2, rs * 0.13); ctx.strokeStyle = bianco ? '#9AA2AF' : '#fff'; ctx.stroke(); }
      else if ((s.k === 'pol' || s.k === 'eur') && rs >= 17) {
        // la sigla dentro il seggio, se ci sta
        const sig = s.testo.replace(/\s*\(.*\)$/, '').split(/[\s-]/)[0];
        for (const fs of [rs * 0.62, rs * 0.52, rs * 0.44]) {
          ctx.font = `700 ${fs}px ${TXT}`;
          if (ctx.measureText(sig).width <= rs * 1.62) {
            ctx.fillStyle = !bianco && luce(c) < 0.6 ? '#fff' : C.ink; ctx.textAlign = 'center';
            ctx.fillText(sig, x, y + fs * 0.35); break;
          }
        }
      }
    }
    ctx.restore();
  }

  // ---- centro: le volte al voto, come i seggi di un parlamento
  const votate = perConsultazione(righeImmagine());
  const nVoti = votate.filter(x => !x.non).length, nNon = votate.filter(x => x.non).length;
  ctx.textAlign = 'center';
  ctx.font = `700 ${r0 * 0.78}px ${TIT}`; ctx.fillStyle = C.ink;
  ctx.fillText(String(nVoti), cx, cy - r0 * 0.12);
  ctx.font = `600 ${Math.max(18, r0 * 0.15)}px ${TXT}`; ctx.fillStyle = C.grigio;
  ctx.fillText(nVoti === 1 ? 'volta al voto' : 'volte al voto', cx, cy + r0 * 0.06);
  ctx.textAlign = 'left';
  if (!orizz) { ctx.fillStyle = C.filo; ctx.fillRect(cx - rN - 10, cy + r0 * 0.16, 2 * rN + 20, 2); }

  // ---- legenda: la storia per colori
  const gruppi = new Map();
  const corto = s => s.testo.replace(/\s*\(.*\)$/, '').replace(/^Lista\s+/i, '');
  const tutti = seggi.flatMap(s => s.senato ? [s, { ...s.senato, k: s.k }] : [s]);
  for (const s of tutti) {
    if (s.k === 'ref' || s.non || s.vuoto || !s.col || s.col.vuoto) continue;
    const g = gruppi.get(s.col.c) || { c: s.col.c, n: 0, naz: [], loc: [] };
    g.n++;
    const nome = corto(s);
    const dove = s.k === 'pol' || s.k === 'eur' ? g.naz : g.loc;
    if (nome && !g.naz.includes(nome) && !g.loc.includes(nome)) dove.push(nome);
    gruppi.set(s.col.c, g);
  }
  const lista = [...gruppi.values()].sort((a, b) => b.n - a.n);
  const ref = seggi.filter(s => s.k === 'ref' && !s.non && !s.vuoto);
  const colonne = orizz ? 1 : 2, gapC = 40, wc = (wLeg - (colonne - 1) * gapC) / colonne;
  const hRiga = orizz ? 50 : (formato === 'quadrata' ? 42 : formato === 'storia' ? 70 : 58);
  const yFine = H - basso - 150;
  const maxRighe = Math.max(1, Math.floor((yFine - yLeg - (orizz ? 0 : 10)) / hRiga) - 1);
  const voci = lista.slice(0, maxRighe * colonne - 1);
  let yl = yLeg + (orizz ? 0 : 18);
  if (orizz && titolo) {
    ctx.font = `700 46px ${TIT}`; ctx.fillStyle = C.ink;
    ctx.fillText(titolo, xLeg, 210);
  }
  voci.forEach((g, i) => {
    const col = i % colonne, riga = Math.floor(i / colonne);
    const x = xLeg + col * (wc + gapC), y = yl + riga * hRiga;
    ctx.beginPath(); ctx.arc(x + 15, y - 9, 15, 0, 2 * Math.PI); ctx.fillStyle = g.c; ctx.fill();
    if (g.c.toUpperCase() === '#FFFFFF') { ctx.strokeStyle = '#9AA2AF'; ctx.lineWidth = 2; ctx.stroke(); }
    ctx.font = `700 ${formato === 'quadrata' ? 26 : formato === 'storia' ? 34 : 30}px ${TIT}`; ctx.fillStyle = C.ink; ctx.textAlign = 'right';
    ctx.fillText(String(g.n), x + wc, y);
    const wN = ctx.measureText(String(g.n)).width;
    ctx.textAlign = 'left';
    const AREE = { '#E0322B': 'candidati di centrosinistra', '#2D6FDB': 'candidati di centrodestra', '#1E1E1E': 'candidati di destra',
      '#8E44C4': 'liste civiche e di centro', '#8A5A3B': 'liste autonomiste', '#FFFFFF': 'schede bianche' };
    // con i colori dei gruppi europei, il nome del gruppo e poi i partiti votati
    const ue = typeof tavolozza !== 'undefined' && tavolozza === 'ue' && typeof GRUPPI_UE !== 'undefined'
      ? Object.values(GRUPPI_UE).find(x => x.c.toUpperCase() === g.c.toUpperCase()) : null;
    const nomi = ue ? [g.naz.length ? `${ue.n}: ${[...g.naz].reverse().join(', ')}` : ue.n]
      : g.naz.length ? [...g.naz].reverse() : [AREE[g.c.toUpperCase()] || 'liste e candidati locali'];
    ctx.font = `600 ${formato === 'quadrata' ? 22 : formato === 'storia' ? 28 : 25}px ${TXT}`; ctx.fillStyle = C.ink;
    let t = '', maxW = wc - 44 - wN - 16;
    for (const n of nomi) {
      const p = t ? t + ', ' + n : n;
      if (ctx.measureText(p).width > maxW) {
        if (!t) { t = n; while (t.length > 1 && ctx.measureText(t + '…').width > maxW) t = t.slice(0, -1); t = t.trimEnd().replace(/[,(]$/, '') + '…'; }
        else t += '…';
        break;
      }
      t = p;
    }
    ctx.fillText(t, x + 44, y);
  });
  // ultima riga: referendum e astensioni
  const iUlt = voci.length;
  const yU = yl + Math.ceil((iUlt + (iUlt % colonne ? 1 : 0)) / colonne) * hRiga + (orizz ? 6 : 8);
  ctx.font = `600 22px ${TXT}`; ctx.fillStyle = C.grigio;
  const pezzi = [];
  if (ref.length) pezzi.push(`${ref.filter(s => s.si && !s.no).length} Sì e ${ref.filter(s => s.no && !s.si).length} No ai referendum`);
  pezzi.push(nNon ? `${nNon} ${nNon === 1 ? 'volta' : 'volte'} non ho votato` : 'mai un\'astensione');
  ctx.fillText(pezzi.join('     '), xLeg, Math.min(yU, yFine - 8));

  disegnaPiede(ctx, m, H - basso - 78, W, m);
}
