"""Posizioni dei partiti italiani nel quadrante politico, per il «Quadrante del mio voto».

Fonte: Chapel Hill Expert Survey, trend file 1999-2024 (Jolly et al. 2022; Bakker et al. 2025),
https://www.chesdata.eu - variabili lrecon (economia: 0 sinistra, 10 destra) e galtan
(valori: 0 progressisti/libertari, 10 conservatori/autoritari).

Per ogni lista delle politiche, delle europee e del Senato (dati/partiti.js) si prende il
partito CHES corrispondente nell'ondata più vicina all'anno del voto. Le liste unitarie
(L'Ulivo, AVS, i Poli del Senato...) hanno la media dei partiti che le formavano.
È una «stima» (s=1) quando la lista non è nella rilevazione e si usa il partito erede o
predecessore, la media di una coalizione o un valore assegnato a mano; prima del 1999
CHES non misura galtan, quindi tutto il 1992-1996 viene dall'ondata 1999.

Uso: python3 strumenti/posizioni/posizioni.py strumenti/posizioni/ches-italia.csv strumenti/posizioni/posizioni-liste.json > dati/posizioni.js
(ches-italia.csv: le righe italiane del trend file 1999-2024_CHES_dataset_meansV2.csv)
"""
import csv, json, sys

trend = [r for r in csv.DictReader(open(sys.argv[1], encoding='latin-1')) if r['country'] == '8']
liste = json.load(open(sys.argv[2]))

# stesso partito sotto sigle diverse nelle ondate
ALIAS = {'LEGA': ['LN', 'Lega'], 'FDI': ['FdI', 'FDI'], 'M5S': ['M5S', 'MS5'], 'PEU': ['RI2019', '+E'],
         'SDI': ['PSDI', 'SDI'], 'VERDI': ['FdV', 'VERDI', 'EV'], 'UDC': ['UDC'], 'RC': ['RC']}
MISURE = {}
for r in trend:
    p = r['party']
    if r['year'] == '2019' and p == 'RI':  # nel 2019 «RI» è +Europa (Radicali Italiani)
        p = 'RI2019'
    if r['lrecon'] in ('', '.') or r['galtan'] in ('', '.'):
        continue
    MISURE.setdefault(p, []).append((int(r['year']), float(r['lrecon']), float(r['galtan'])))


def misura(codice, anno):
    cod = ALIAS.get(codice, [codice])
    cand = [m for c in cod for m in MISURE.get(c, [])]
    if not cand:
        raise SystemExit(f'manca {codice}')
    return min(cand, key=lambda m: (abs(m[0] - anno), -m[0]))


# lista -> (partiti CHES, stima?) oppure [x, y] a mano (stima)
REGOLE = {
    'DC': (['PPI', 'CCD'], 1), 'PDS': (['PDS'], 0), 'PSI': (['SDI'], 1), 'Lega Nord': (['LEGA'], 0),
    'PRC': (['RC'], 0), 'MSI-DN': (['AN'], 1), 'PRI': (['PRI'], 0), 'PLI': [7.0, 5.0], 'Verdi': (['VERDI'], 0),
    'PSDI': (['SDI'], 0), 'La Rete': (['DEM'], 1), 'Lista Pannella': (['LB'], 1), 'FI': (['FI'], 0), 'AN': (['AN'], 0),
    'PPI': (['PPI'], 0), 'Patto Segni': (['SEG'], 0), 'AD': (['DEM'], 1), 'CCD-CDU': (['CCD', 'CDU'], 1),
    'RI': (['RI'], 0), 'Pannella-Sgarbi': (['LB'], 1), 'DS': (['DS'], 0), 'DL Margherita': (['DL'], 0), 'IdV': (['IdV'], 0),
    'DE': (['UDEUR'], 1), 'Lista Bonino': (['LB', 'RAD'], 0), 'Girasole': (['VERDI', 'SDI'], 1), 'PdCI': (['PdCI'], 0),
    'Ulivo': (['DS', 'DL'], 1), 'UDC': (['UDC'], 0), 'LN-MpA': (['LEGA'], 1), 'RnP': (['RAD', 'SDI'], 1), 'UDEUR': (['UDEUR'], 0),
    'PdL': (['PDL'], 0), 'PD': (['PD'], 0), 'UdC': (['UDC'], 0), 'SA': (['RC', 'PdCI', 'VERDI', 'SD'], 1),
    'La Destra': (['MS'], 1), 'MpA': (['MpA'], 0), 'M5S': (['M5S'], 0), 'SC': (['SC'], 0), 'SEL': (['SEL'], 0),
    'RC': (['IdV', 'RC'], 1), 'FdI': (['FDI'], 0), 'FFD': [8.0, 4.0], 'Lega': (['LEGA'], 0), 'LeU': (['SI'], 1),
    '+Europa': (['PEU'], 0), 'NcI-UDC': (['UDC', 'NCD'], 1), 'PaP': (['RC'], 1), 'A-IV': (['A'], 0), 'AVS': (['VERDI', 'SI'], 1),
    'Italexit': [5.5, 8.0], 'UP': (['RC'], 1), 'ISP': [4.0, 8.5], 'PSI-AD': (['SDI', 'DEM'], 1), 'AN-Segni': (['AN', 'SEG'], 1),
    'Democratici': (['DEM'], 0), 'CCD': (['CCD'], 0), 'SDI': (['SDI'], 0), 'CDU': (['CDU'], 0), 'Fiamma Tricolore': (['MS'], 0),
    'SUE': (['SDI', 'RAD'], 1), 'AS': (['MS'], 1), 'Pensionati': [4.0, 6.0], 'PRC-PdCI': (['RC', 'PdCI'], 1), 'SL': (['SL', 'SD'], 1),
    'Lista Bonino-Pannella': (['RAD'], 0), "L'Autonomia": (['MpA'], 1), 'NCD-UDC': (['NCD', 'UDC'], 1), 'Lista Tsipras': (['SEL', 'RC'], 1),
    'EV': (['VERDI'], 0), 'La Sinistra': (['SI'], 1), 'FI-NM': (['FI'], 0), 'Azione': (['A'], 0), 'PTD': [2.0, 4.0], 'Libertà': [5.5, 8.0],
    'Progressisti': (['PDS', 'RC', 'VERDI'], 1), 'Polo delle Libertà': (['FI', 'LEGA', 'CCD'], 1), "Patto per l'Italia": (['PPI', 'SEG'], 1),
    'Polo del Buon Governo': (['FI', 'AN', 'CCD'], 1), 'Polo per le Libertà': (['FI', 'AN', 'CCD'], 1), 'CdL': (['FI', 'AN', 'LEGA', 'CCD'], 1),
    'Insieme con l\'Unione': (['VERDI', 'PdCI'], 1), 'Con Monti': (['SC'], 0),
}
# per la sigla «SUE» del 2024 (Stati Uniti d'Europa: IV, +Europa, PSI...)
SPECIALI = {('eur-2024', 'SUE'): (['PEU', 'SDI'], 1), ('eur-2024', 'PD'): (['PD'], 0)}

out = {}
for k, sigle in liste.items():
    anno = int(k[-4:])
    for b in sigle:
        reg = SPECIALI.get((k, b), REGOLE.get(b))
        if reg is None:
            print('// senza posizione:', k, b, file=sys.stderr)
            continue
        if isinstance(reg, list):
            out[f'{k}|{b}'] = [reg[0], reg[1], 1]
            continue
        codici, stima = reg
        ms = [misura(c, anno) for c in codici]
        x = sum(m[1] for m in ms) / len(ms); y = sum(m[2] for m in ms) / len(ms)
        # misura presa da un'altra legislatura (più di 4 anni di distanza): stima
        if any(abs(m[0] - anno) > 4 for m in ms):
            stima = 1
        out[f'{k}|{b}'] = [round(x, 2), round(y, 2), stima]

# punti di riferimento: i partiti principali nell'ultima rilevazione
RIF = {'PD': 'PD', 'FdI': 'FDI', 'Lega': 'LEGA', 'FI': 'FI', 'M5S': 'M5S', 'AVS': None, 'Azione': 'A', '+Europa': 'PEU'}
rif = {}
for n, c in RIF.items():
    if c is None:
        a, b = misura('VERDI', 2024), misura('SI', 2024); rif[n] = [round((a[1] + b[1]) / 2, 2), round((a[2] + b[2]) / 2, 2)]
    else:
        m = misura(c, 2024); rif[n] = [round(m[1], 2), round(m[2], 2)]

print('// Generato da build/posizioni.py: posizioni dei partiti dal Chapel Hill Expert Survey 1999-2024')
print('// (lrecon, galtan; 0-10). Terzo valore: 1 = stima. Non modificare a mano.')
print('const POSIZIONI_PARTITI = ' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';')
print('const POSIZIONI_RIFERIMENTO = ' + json.dumps(rif, ensure_ascii=False, separators=(',', ':')) + ';')
