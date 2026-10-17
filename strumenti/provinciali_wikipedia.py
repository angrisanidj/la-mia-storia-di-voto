"""Estrae da it.wikipedia.org le provinciali dirette 1993-2011 (fonti/provinciali_wikipedia.json).
Si lancia a mano nella cartella con le pagine «Elezioni provinciali in Italia del AAAA» scaricate in
wikitext (pAAAA.txt, da index.php?title=...&action=raw). Scarta i riquadri senza data o con una data
incoerente con la pagina; il sito usa da qui gli anni prima del 2004 e Sicilia e Friuli-Venezia Giulia.
"""
import os, re, json, glob, datetime as dt, unicodedata
MESI = ['gennaio','febbraio','marzo','aprile','maggio','giugno','luglio','agosto','settembre','ottobre','novembre','dicembre']
def norm(s):
    s = unicodedata.normalize('NFD', s.upper()); s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', re.sub(r"[’'`\-/.,()]", ' ', s)).strip()
PROV = {norm(v): k for k, v in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'province.json'))).items()}
PROV.update({'FORLI': 'FC', 'FORLI CESENA': 'FC', 'PESARO E URBINO': 'PU', 'PESARO URBINO': 'PU', 'VERBANO CUSIO OSSOLA': 'VB', 'MASSA CARRARA': 'MS', 'MASSA E CARRARA': 'MS',
             'REGGIO EMILIA': 'RE', "REGGIO NELL EMILIA": 'RE', 'REGGIO CALABRIA': 'RC', 'CARBONIA IGLESIAS': 'CI', 'OGLIASTRA': 'OG', 'OLBIA TEMPIO': 'OT',
             'MEDIO CAMPIDANO': 'VS', 'MONZA E DELLA BRIANZA': 'MB', 'MONZA E BRIANZA': 'MB', 'BARLETTA ANDRIA TRANI': 'BT', 'L AQUILA': 'AQ', 'AQUILA': 'AQ'})
def date_box(anno, s):
    gg = []
    for p in re.split(r',\s*|\s+e\s+(?=\d)', re.sub(r'\d{4}', '', s)):
        m = re.match(r'\s*(\d{1,2})', p.replace('º', '').replace('°', ''))
        if m: gg.append([int(m.group(1)), next((MESI.index(w) + 1 for w in re.findall(r'[a-z]+', p) if w in MESI), None)])
    mese = None
    for g in reversed(gg):
        if g[1]: mese = g[1]
        else: g[1] = mese
    return [dt.date(anno, m, d) for d, m in gg if m]
def pulisci(cella):
    c = cella
    while re.search(r'\{\{[^{}]*\}\}', c): c = re.sub(r'\{\{[^{}]*\}\}', '', c)
    c = re.sub(r'^\s*(?:[a-z]+\s*=\s*"?[^|"]*"?\s*)+\|', '', c)
    return c.strip()
def testo_link(s):
    return re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r'\1', s).replace("'''", '').strip()
def numero(s):
    s = s.replace("'''", '').strip()
    return float(s.replace('.', '').replace(',', '.')) if re.fullmatch(r'[\d.]+(,\d+)?', s) else None
def tabella(t, da):
    i = t.find('{|', da)
    if i < 0: return []
    j = t.find('\n|}', i)
    corpo = t[i:j]
    cand = []
    for riga in corpo.split('\n|-')[1:]:
        celle = [pulisci(c) for c in re.split(r'\n\||\|\|', '\n' + riga.strip('\n'))[1:]]
        celle = [c for c in celle if c != '']
        k = 0
        while k < len(celle):
            c = celle[k]
            if "'''" in c and numero(c) is None and not c.startswith('!'):
                nome = testo_link(c)
                nums = [numero(x) for x in celle[k + 1:k + 3]]
                cand.append([nome, nums[1] if len(nums) > 1 else None, []]); k += 3; continue
            if numero(c) is None and cand and not re.search(r"Seggio|Totale|colspan|''", c, re.I) and (('[[' in c) or re.search(r'[A-Za-z]{3}', c)):
                nums = [numero(x) for x in celle[k + 1:k + 3]]
                if len(nums) > 1 and nums[1] is not None:
                    cand[-1][2].append([testo_link(c).replace(' (A)', ''), nums[1]]); k += 3; continue
            k += 1
    return cand
AREA = [(r'Centro-sinistra|Ulivo|Progressisti|Unione', 'centrosinistra'), (r'Centro-destra|Polo|Casa delle Libert|Popolo della Libert', 'centrodestra'),
        (r'Rifondazione|Comunisti', 'sinistra'), (r'Alleanza Nazionale|Movimento Sociale|Fiamma|La Destra', 'destra'), (r'Lega Nord', 'altro')]
out = []; scartati = []
for f in sorted(glob.glob('p*.txt')):
    anno = int(f[1:5])
    if anno < 1993 or anno > 2011: continue
    t = open(f).read()
    pr = re.search(r"'''elezioni provinciali in[^']*'''([^\n]*)", t, re.I)
    intro = re.sub(r'<ref.*?(</ref>|/>)', '', pr.group(1)) if pr else ''
    # senza frase d'introduzione: la data dei risultati ufficiali citati (es. .../provinciali/20000416/...), fuori da Sardegna e Sicilia
    ufficiale = re.search(r'provinciali/(\d{4})(\d{2})(\d{2})/', t)
    date_intro = [dt.date(anno, MESI.index(m) + 1, int(g)) for g, m in re.findall(r"(\d{1,2})[°º]?(?:\s*(?:e|-)\s*\d{1,2})?\s+(" + '|'.join(MESI) + r")", intro)]
    for m in re.finditer(r"\{\{Elezioni\s*\n(.*?)\n\}\}", t, re.S):
        campi = dict((k.strip(), v.strip()) for k, v in re.findall(r"^\|\s*([^=|]+?)\s*=(.*)$", m.group(1), re.M))
        nome = testo_link(campi.get('provincia', ''))
        if not nome: continue
        sig = PROV.get(norm(re.sub(r'^Provincia (di |del |della |dell\')', '', nome)))
        ds = date_box(anno, campi.get('data', ''))
        if not ds and sig and date_intro:
            # riquadro senza data: quella dell'introduzione (per Sardegna e Sicilia quella indicata per la regione)
            regione = 'Sardegna' if sig in ('CA','NU','OR','SS','CI','VS','OG','OT') else 'Sicilia' if sig in ('AG','CL','CT','EN','ME','PA','RG','SR','TP') else None
            pezzo = intro.split(regione, 1)[1] if regione and regione in intro else intro.split('Sardegna')[0].split('Sicilia')[0]
            dd = [dt.date(anno, MESI.index(mm) + 1, int(g)) for g, mm in re.findall(r"(\d{1,2})[°º]?(?:\s*(?:e|-)\s*\d{1,2})?\s+(" + '|'.join(MESI) + r")", pezzo)]
            ds = dd[:1]
        if not ds and sig and not date_intro and ufficiale and sig not in ('CA','NU','OR','SS','CI','VS','OG','OT','AG','CL','CT','EN','ME','PA','RG','SR','TP'):
            ds = [dt.date(int(ufficiale.group(1)), int(ufficiale.group(2)), int(ufficiale.group(3)))]
        if not sig or not ds: scartati.append((anno, nome, campi.get('data'))); continue
        sezione = (re.findall(r'^==([^=].*?)==\s*$', t[:m.start()], re.M) or [''])[-1]
        conferma = f"{ds[0].day} {MESI[ds[0].month - 1]}" in sezione  # la sezione della pagina riporta la stessa data
        if date_intro and not conferma and not any(abs((ds[0] - d).days) <= 3 for d in date_intro): scartati.append((anno, nome, campi.get('data'), 'incoerente')); continue
        bal = any(k.lower().startswith(('votibal', '%bal')) and re.search(r'\d', v) for k, v in campi.items())
        aree = {}
        for i in range(1, 12):
            c = testo_link(campi.get(f'candidato{i}', ''))
            if not c: break
            coal = campi.get(f'coalizione{i}', '') + ' ' + campi.get(f'partito{i}', '')
            aree[c] = next((a for rx, a in AREA if re.search(rx, coal)), None)
        cand = tabella(t, m.end())
        for c in cand: c.append(aree.get(c[0]))
        if not cand:
            cand = [[testo_link(campi[f'candidato{i}']), numero(campi.get(f'%{i}', '') or ''), [], aree.get(testo_link(campi[f'candidato{i}']))] for i in range(1, 12) if campi.get(f'candidato{i}')]
        out.append({'chiave': f'{sig}-{ds[0].isoformat()}', 'n': nome, 'b': 1 if bal else 0, 'c': cand, 'fonte': f'https://it.wikipedia.org/wiki/Elezioni_provinciali_in_Italia_del_{anno}'})
print(len(out), 'elezioni;', len(scartati), 'scartate:', scartati[:15])
json.dump(out, open('provinciali-wiki.json', 'w'), ensure_ascii=False)
from collections import Counter
print(Counter(o['chiave'][-10:-6] for o in out))
for o in out[:1] + [x for x in out if x['chiave'].startswith('MI-')]: print(o['chiave'], o['b'], json.dumps(o['c'][:3], ensure_ascii=False)[:400])
