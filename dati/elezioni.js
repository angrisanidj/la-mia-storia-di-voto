// Calendario delle consultazioni 1992-2026.
// d = primo (o unico) giorno di voto, d2 = secondo giorno (se presente).
// Per le politiche fino al 2018 il Senato richiedeva 25 anni (L. cost. 1/2021: 18 anni dal 2022).

const NAZIONALI = [
  // Politiche
  { t: 'pol', d: '1992-04-05', d2: '1992-04-06', s: 'Politiche' },
  { t: 'pol', d: '1994-03-27', d2: '1994-03-28', s: 'Politiche' },
  { t: 'pol', d: '1996-04-21', s: 'Politiche' },
  { t: 'pol', d: '2001-05-13', s: 'Politiche' },
  { t: 'pol', d: '2006-04-09', d2: '2006-04-10', s: 'Politiche' },
  { t: 'pol', d: '2008-04-13', d2: '2008-04-14', s: 'Politiche' },
  { t: 'pol', d: '2013-02-24', d2: '2013-02-25', s: 'Politiche' },
  { t: 'pol', d: '2018-03-04', s: 'Politiche' },
  { t: 'pol', d: '2022-09-25', s: 'Politiche' },
  // Europee
  { t: 'eur', d: '1994-06-12', s: 'Europee' },
  { t: 'eur', d: '1999-06-13', s: 'Europee' },
  { t: 'eur', d: '2004-06-12', d2: '2004-06-13', s: 'Europee' },
  { t: 'eur', d: '2009-06-06', d2: '2009-06-07', s: 'Europee' },
  { t: 'eur', d: '2014-05-25', s: 'Europee' },
  { t: 'eur', d: '2019-05-26', s: 'Europee' },
  { t: 'eur', d: '2024-06-08', d2: '2024-06-09', s: 'Europee' },
  // Referendum nazionali (q = numero di quesiti)
  { t: 'ref', d: '1993-04-18', d2: '1993-04-19', q: 8, s: 'Referendum elettorale e finanziamento partiti', l: 'Legge elettorale del Senato, finanziamento pubblico ai partiti, ministeri, droghe e altri' },
  { t: 'ref', d: '1995-06-11', q: 12, s: 'Referendum TV, sindacati e commercio', l: 'Concessioni televisive, rappresentanza sindacale, orari dei negozi, RAI e altri' },
  { t: 'ref', d: '1997-06-15', q: 7, s: 'Referendum abrogativi 1997', l: 'Privatizzazioni, obiezione di coscienza, caccia, carriere dei magistrati, ordine dei giornalisti e altri' },
  { t: 'ref', d: '1999-04-18', q: 1, s: 'Referendum elettorale', l: 'Abolizione della quota proporzionale alla Camera' },
  { t: 'ref', d: '2000-05-21', q: 7, s: 'Referendum abrogativi 2000', l: 'Quota proporzionale, rimborsi elettorali, CSM, licenziamenti, trattenute sindacali e altri' },
  { t: 'ref', d: '2001-10-07', q: 1, c: 1, s: 'Referendum costituzionale Titolo V', l: 'Riforma del Titolo V della Costituzione' },
  { t: 'ref', d: '2003-06-15', d2: '2003-06-16', q: 2, s: 'Referendum articolo 18 ed elettrodotti', l: 'Estensione dell’articolo 18 e servitù degli elettrodotti' },
  { t: 'ref', d: '2005-06-12', d2: '2005-06-13', q: 4, s: 'Referendum procreazione assistita', l: 'Legge 40 sulla procreazione medicalmente assistita' },
  { t: 'ref', d: '2006-06-25', d2: '2006-06-26', q: 1, c: 1, s: 'Referendum costituzionale', l: 'Riforma della Parte II della Costituzione (“devolution”)' },
  { t: 'ref', d: '2009-06-21', d2: '2009-06-22', q: 3, s: 'Referendum elettorale', l: 'Premio di maggioranza alla lista e candidature multiple' },
  { t: 'ref', d: '2011-06-12', d2: '2011-06-13', q: 4, s: 'Referendum acqua, nucleare e legittimo impedimento', l: 'Servizi idrici (2 quesiti), nucleare, legittimo impedimento' },
  { t: 'ref', d: '2016-04-17', q: 1, s: 'Referendum trivellazioni', l: 'Durata delle concessioni per le trivellazioni in mare' },
  { t: 'ref', d: '2016-12-04', q: 1, c: 1, s: 'Referendum costituzionale', l: 'Riforma Renzi-Boschi' },
  { t: 'ref', d: '2020-09-20', d2: '2020-09-21', q: 1, c: 1, s: 'Referendum costituzionale', l: 'Riduzione del numero dei parlamentari' },
  { t: 'ref', d: '2022-06-12', q: 5, s: 'Referendum giustizia', l: 'Legge Severino, misure cautelari, separazione delle funzioni, CSM, consigli giudiziari' },
  { t: 'ref', d: '2025-06-08', d2: '2025-06-09', q: 5, s: 'Referendum lavoro e cittadinanza', l: 'Licenziamenti, contratti a termine, appalti, cittadinanza' },
  { t: 'ref', d: '2026-03-22', d2: '2026-03-23', q: 1, c: 1, s: 'Referendum costituzionale giustizia', l: 'Separazione delle carriere dei magistrati' },
];

// Elezioni regionali per codice ISTAT di regione.
// Per il Trentino-Alto Adige dal 2003 si votano i due consigli provinciali (vedi PROVINCIALI_TAA).
const REGIONALI = {
  '01': ['1995-04-23', '2000-04-16', '2005-04-03|2005-04-04', '2010-03-28|2010-03-29', '2014-05-25', '2019-05-26', '2024-06-08|2024-06-09'],
  '02': ['1993-05-30', '1998-05-31', '2003-06-08', '2008-05-25', '2013-05-26', '2018-05-20', '2020-09-20|2020-09-21', '2025-09-28'],
  '03': ['1995-04-23', '2000-04-16', '2005-04-03|2005-04-04', '2010-03-28|2010-03-29', '2013-02-24|2013-02-25', '2018-03-04', '2023-02-12|2023-02-13'],
  '04': ['1993-11-21', '1998-11-22'],
  '05': ['1995-04-23', '2000-04-16', '2005-04-03|2005-04-04', '2010-03-28|2010-03-29', '2015-05-31', '2020-09-20|2020-09-21', '2025-11-23|2025-11-24'],
  '06': ['1993-06-06', '1998-06-14', '2003-06-08|2003-06-09', '2008-04-13|2008-04-14', '2013-04-21|2013-04-22', '2018-04-29', '2023-04-02|2023-04-03'],
  '07': ['1995-04-23', '2000-04-16', '2005-04-03|2005-04-04', '2010-03-28|2010-03-29', '2015-05-31', '2020-09-20|2020-09-21', '2024-10-27|2024-10-28'],
  '08': ['1995-04-23', '2000-04-16', '2005-04-03|2005-04-04', '2010-03-28|2010-03-29', '2014-11-23', '2020-01-26', '2024-11-17|2024-11-18'],
  '09': ['1995-04-23', '2000-04-16', '2005-04-03|2005-04-04', '2010-03-28|2010-03-29', '2015-05-31', '2020-09-20|2020-09-21', '2025-10-12|2025-10-13'],
  '10': ['1995-04-23', '2000-04-16', '2005-04-03|2005-04-04', '2010-03-28|2010-03-29', '2015-05-31', '2019-10-27', '2024-11-17|2024-11-18'],
  '11': ['1995-04-23', '2000-04-16', '2005-04-03|2005-04-04', '2010-03-28|2010-03-29', '2015-05-31', '2020-09-20|2020-09-21', '2025-09-28|2025-09-29'],
  '12': ['1995-04-23', '2000-04-16', '2005-04-03|2005-04-04', '2010-03-28|2010-03-29', '2013-02-24|2013-02-25', '2018-03-04', '2023-02-12|2023-02-13'],
  '13': ['1995-04-23', '2000-04-16', '2005-04-03|2005-04-04', '2008-12-14|2008-12-15', '2014-05-25', '2019-02-10', '2024-03-10'],
  '14': ['1995-04-23', '2000-04-16', '2001-11-11', '2006-11-05|2006-11-06', '2011-10-16|2011-10-17', '2013-02-24|2013-02-25', '2018-04-22', '2023-06-25|2023-06-26'],
  '15': ['1995-04-23', '2000-04-16', '2005-04-03|2005-04-04', '2010-03-28|2010-03-29', '2015-05-31', '2020-09-20|2020-09-21', '2025-11-23|2025-11-24'],
  '16': ['1995-04-23', '2000-04-16', '2005-04-03|2005-04-04', '2010-03-28|2010-03-29', '2015-05-31', '2020-09-20|2020-09-21', '2025-11-23|2025-11-24'],
  '17': ['1995-04-23', '2000-04-16', '2005-04-17|2005-04-18', '2010-03-28|2010-03-29', '2013-11-17|2013-11-18', '2019-03-24', '2024-04-21|2024-04-22'],
  '18': ['1995-04-23', '2000-04-16', '2005-04-03|2005-04-04', '2010-03-28|2010-03-29', '2014-11-23', '2020-01-26', '2021-10-03|2021-10-04', '2025-10-05|2025-10-06'],
  '19': ['1996-06-16', '2001-06-24', '2006-05-28', '2008-04-13|2008-04-14', '2012-10-28', '2017-11-05', '2022-09-25'],
  '20': ['1994-06-12', '1999-06-13', '2004-06-12|2004-06-13', '2009-02-15|2009-02-16', '2014-02-16', '2019-02-24', '2024-02-25'],
};

// Sardegna: con la legge elettorale dell'epoca si tornava al voto in tutta la regione due settimane dopo.
const SECONDI_TURNI_REGIONALI = { '20': ['1994-06-26', '1999-06-27'] };

// Trentino-Alto Adige dal 2003: consiglio provinciale di Trento (TN) o di Bolzano (BZ).
// Stessa data, tranne il 2008 (Bolzano 26 ottobre, Trento 9 novembre).
// A Bolzano servivano 4 anni di residenza in regione; 2 anni dal 23/06/2026 (L. cost. 2/2026).
const PROVINCIALI_TAA = [
  { TN: '2003-10-26', BZ: '2003-10-26' },
  { TN: '2008-11-09', BZ: '2008-10-26' },
  { TN: '2013-10-27', BZ: '2013-10-27' },
  { TN: '2018-10-21', BZ: '2018-10-21' },
  { TN: '2023-10-22', BZ: '2023-10-22' },
];

// Referendum regionali (solo i principali, a livello di intera regione).
const REFERENDUM_REGIONALI = [
  { r: '03', d: '2017-10-22', s: 'Referendum autonomia', l: 'Referendum consultivo sull’autonomia della Lombardia' },
  { r: '05', d: '2017-10-22', s: 'Referendum autonomia', l: 'Referendum consultivo sull’autonomia del Veneto' },
  { r: '20', d: '2011-05-15', d2: '2011-05-16', s: 'Referendum nucleare (regionale)', l: 'Referendum consultivo sul nucleare in Sardegna' },
  { r: '20', d: '2012-05-06', s: 'Referendum regionali', l: 'Referendum regionali sardi su province ed enti (10 quesiti)' },
];

// Comuni passati da una regione all'altra: codice catastale -> [data di passaggio, regione prima, regione dopo]
const CAMBI_REGIONE = {
  I421: ['2017-12-16', '05', '06'], // Sappada: Veneto -> Friuli-Venezia Giulia (L. 182/2017)
  C080: ['2009-08-15', '11', '08'], // Casteldelci
  E838: ['2009-08-15', '11', '08'], // Maiolo
  F137: ['2009-08-15', '11', '08'], // Novafeltria
  G433: ['2009-08-15', '11', '08'], // Pennabilli
  H949: ['2009-08-15', '11', '08'], // San Leo
  I201: ['2009-08-15', '11', '08'], // Sant'Agata Feltria
  L034: ['2009-08-15', '11', '08'], // Talamello
  F478: ['2021-06-17', '11', '08'], // Montecopiolo
  I460: ['2021-06-17', '11', '08'], // Sassofeltrio
};

// Turni ordinari delle amministrative nelle regioni a statuto ordinario:
// primo turno (d) e ballottaggio (b). Fino al 1998 c'erano due turni l'anno (L. 120/1999).
// Servono solo a precompilare le comunali aggiunte a mano: le regioni a statuto speciale
// e i turni straordinari hanno date proprie, che l'utente può correggere.
// 1996: date dei ballottaggi ricavate (primo turno + 14 giorni), non confermate da fonte diretta.
const TURNI_COMUNALI = [
  { d: '1993-06-06', b: '1993-06-20' }, { d: '1993-11-21', b: '1993-12-05' },
  { d: '1994-06-12', b: '1994-06-26' }, { d: '1994-11-20', b: '1994-12-04' },
  { d: '1995-04-23', b: '1995-05-07' }, { d: '1995-11-19', b: '1995-12-03' },
  { d: '1996-06-09', b: '1996-06-23' }, { d: '1996-11-17', b: '1996-12-01' },
  { d: '1997-04-27', b: '1997-05-11' }, { d: '1997-11-16', b: '1997-11-30' },
  { d: '1998-05-24', b: '1998-06-07' }, { d: '1998-11-29', b: '1998-12-13' },
  { d: '1999-06-13', b: '1999-06-27' },
  { d: '2000-04-16', b: '2000-04-30' },
  { d: '2001-05-13', b: '2001-05-27' },
  { d: '2002-05-26', d2: '2002-05-27', b: '2002-06-09', b2: '2002-06-10' },
  { d: '2003-05-25', d2: '2003-05-26', b: '2003-06-08', b2: '2003-06-09' },
  { d: '2004-06-12', d2: '2004-06-13', b: '2004-06-26', b2: '2004-06-27' },
  { d: '2005-04-03', d2: '2005-04-04', b: '2005-04-17', b2: '2005-04-18' },
  { d: '2006-05-28', d2: '2006-05-29', b: '2006-06-11', b2: '2006-06-12' },
  { d: '2007-05-27', d2: '2007-05-28', b: '2007-06-10', b2: '2007-06-11' },
  { d: '2008-04-13', d2: '2008-04-14', b: '2008-04-27', b2: '2008-04-28' },
  { d: '2009-06-06', d2: '2009-06-07', b: '2009-06-21', b2: '2009-06-22' },
  { d: '2010-03-28', d2: '2010-03-29', b: '2010-04-11', b2: '2010-04-12' },
  { d: '2011-05-15', d2: '2011-05-16', b: '2011-05-29', b2: '2011-05-30' },
  { d: '2012-05-06', d2: '2012-05-07', b: '2012-05-20', b2: '2012-05-21' },
  { d: '2013-05-26', d2: '2013-05-27', b: '2013-06-09', b2: '2013-06-10' },
  { d: '2014-05-25', b: '2014-06-08' },
  { d: '2015-05-31', b: '2015-06-14' },
  { d: '2016-06-05', b: '2016-06-19' },
  { d: '2017-06-11', b: '2017-06-25' },
  { d: '2018-06-10', b: '2018-06-24' },
  { d: '2019-05-26', b: '2019-06-09' },
  { d: '2020-09-20', d2: '2020-09-21', b: '2020-10-04', b2: '2020-10-05' },
  { d: '2021-10-03', d2: '2021-10-04', b: '2021-10-17', b2: '2021-10-18' },
  { d: '2022-06-12', b: '2022-06-26' },
  { d: '2023-05-14', d2: '2023-05-15', b: '2023-05-28', b2: '2023-05-29' },
  { d: '2024-06-08', d2: '2024-06-09', b: '2024-06-23', b2: '2024-06-24' },
  { d: '2025-05-25', d2: '2025-05-26', b: '2025-06-08', b2: '2025-06-09' },
  { d: '2026-05-24', d2: '2026-05-25', b: '2026-06-07', b2: '2026-06-08' },
];
