'use strict';
// ===== Tavolozza «europea»: i colori dei gruppi del Parlamento europeo =====
// Un'alternativa ai colori dei partiti: decide i pallini della card, i simboli nell'immagine e i punti del sismografo.
// Il testo (e quello copiato per WhatsApp) tiene le emoji, che hanno solo nove colori.
const GRUPPI_UE = {
  ppe: { c: '#3399FF', n: 'Popolari (PPE)' },
  ecr: { c: '#0B3D91', n: 'Conservatori (ECR)' },
  dr: { c: '#1E1E1E', n: 'Destra radicale' },
  renew: { c: '#F2B705', n: 'Centristi liberali (Renew)' },
  sd: { c: '#E02027', n: 'Socialisti (S&D)' },
  verdi: { c: '#3BA55C', n: 'Verdi' },
  sx: { c: '#8B1A1A', n: 'Sinistra radicale' },
  ni: { c: '#9AA2AF', n: 'Non iscritti' },
  civ: { c: '#D6198A', n: 'Liste civiche' },
  civsx: { c: '#F48FB1', n: 'Civiche di centrosinistra' },
  civdx: { c: '#8EC5F0', n: 'Civiche di centrodestra' },
  aut: { c: '#8A5A3B', n: 'Autonomisti' },
};
// Sigle dei dati (dati/partiti.js) -> gruppo; le altre seguono l'area
const GRUPPO_DI = {
  DC: 'ppe', PPI: 'ppe', 'CCD-CDU': 'ppe', CCD: 'ppe', CDU: 'ppe', UDC: 'ppe', UdC: 'ppe', 'NCD-UDC': 'ppe', 'NcI-UDC': 'ppe', DE: 'ppe', UDEUR: 'ppe',
  FI: 'ppe', PdL: 'ppe', 'FI-NM': 'ppe', SVP: 'ppe',
  'Polo delle Libertà': 'ppe', 'Polo del Buon Governo': 'ppe', 'Polo per le Libertà': 'ppe', 'Casa delle Libertà': 'ppe', CdL: 'ppe', Centrodestra: 'ppe', "Patto per l'Italia": 'ppe',
  AN: 'ecr', 'AN-Segni': 'ecr', FdI: 'ecr',
  'Lega Nord': 'dr', Lega: 'dr', 'LN-MpA': 'dr', 'MSI-DN': 'dr', 'Fiamma Tricolore': 'dr', 'La Destra': 'dr', AS: 'dr',
  PRI: 'renew', PLI: 'renew', 'Patto Segni': 'renew', AD: 'renew', RI: 'renew', 'DL Margherita': 'renew', Democratici: 'renew', IdV: 'renew',
  'Lista Pannella': 'renew', 'Pannella-Sgarbi': 'renew', 'Lista Bonino': 'renew', 'Lista Bonino-Pannella': 'renew', SC: 'renew', FFD: 'renew',
  '+Europa': 'renew', 'A-IV': 'renew', Azione: 'renew', SUE: 'renew', 'Con Monti per l\'Italia': 'renew', 'Con Monti': 'renew', 'Team K': 'renew',
  PDS: 'sd', DS: 'sd', PD: 'sd', PSI: 'sd', PSDI: 'sd', SDI: 'sd', 'PSI-AD': 'sd', Ulivo: 'sd', RnP: 'sd',
  Progressisti: 'sd', "L'Ulivo": 'sd', "L'Unione": 'sd', Centrosinistra: 'sd', 'Italia. Bene Comune': 'sd', "Insieme con l'Unione": 'sd',
  Verdi: 'verdi', Girasole: 'verdi', EV: 'verdi', AVS: 'verdi', 'La Rete': 'verdi',
  PRC: 'sx', PdCI: 'sx', 'PRC-PdCI': 'sx', SA: 'sx', SL: 'sx', SEL: 'sx', RC: 'sx', LeU: 'sx', PaP: 'sx', UP: 'sx', 'Lista Tsipras': 'sx', 'La Sinistra': 'sx',
  M5S: 'ni', Italexit: 'ni', ISP: 'ni', PTD: 'ni', Libertà: 'ni', Pensionati: 'ni',
  MpA: 'aut', "L'Autonomia": 'aut',
};
const GRUPPO_AREA = { sinistra: 'sx', centrosinistra: 'sd', centro: 'renew', centrodestra: 'ppe', destra: 'dr', altro: 'ni', autonomista: 'aut' };
const POLI_SX = ['sinistra', 'centrosinistra'], POLI_DX = ['centrodestra', 'destra'];
let tavolozza = 'partiti';

function gruppoPartito(p) {
  if (!p) return null;
  if (p.civica) return p.area && POLI_SX.includes(p.area) ? 'civsx' : p.area && POLI_DX.includes(p.area) ? 'civdx' : 'civ';
  if (p.b && GRUPPO_DI[p.b]) return GRUPPO_DI[p.b];
  if (p.b === 'Lista della circoscrizione Estero') return 'ni';
  const a = typeof p.a === 'string' ? p.a : p.area;
  return GRUPPO_AREA[a] || null;
}
// Il colore di un candidato: il partito più votato della sua coalizione (prima quelli dei poli), civico se non ne ha
function gruppoCandidato(c) {
  if (!c) return null;
  const area = typeof areaCandidato === 'function' ? areaCandidato(c) : c.area;
  const conPartito = (c.liste || []).filter(l => l.partito);
  if (!conPartito.length) return c.area ? GRUPPO_AREA[c.area] : 'civ';
  // trasversale (sostenuto da entrambi i poli): centro
  const sx = conPartito.some(l => POLI_SX.includes(areaDi(l.partito))), dx = conPartito.some(l => POLI_DX.includes(areaDi(l.partito)));
  if (sx && dx && area === 'centro') return 'renew';
  const ordinati = conPartito.slice().sort((x, y) => ((y.p || 0) - (x.p || 0)));
  const delPolo = ordinati.find(l => areaDi(l.partito) === area) || ordinati[0];
  return gruppoPartito(delPolo.partito);
}
// Una lista nel contesto del suo candidato: le civiche prendono il colore civico del candidato
function gruppoLista(l, c) {
  if (l.partito) return gruppoPartito(l.partito);
  const a = typeof areaCandidato === 'function' ? areaCandidato(c) : null;
  return POLI_SX.includes(a) ? 'civsx' : POLI_DX.includes(a) ? 'civdx' : 'civ';
}
const GRUPPO_COALIZIONE_LOCALE = { CDX: 'ppe', CSX: 'sd', 'CSX e M5S': 'sd', M5S: 'ni', Civico: 'civ' };
const coloreGruppo = g => (g && GRUPPI_UE[g] ? GRUPPI_UE[g].c : null);
const coloreCivico = () => (tavolozza === 'ue' ? GRUPPI_UE.civ.c : '#8E44C4');
