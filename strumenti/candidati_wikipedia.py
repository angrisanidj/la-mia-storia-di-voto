"""Estrae da it.wikipedia.org i candidati sindaco delle comunali di Valle d'Aosta, Trentino-Alto Adige,
Friuli-Venezia Giulia e Sicilia dal 1993 (strumenti/candidati-wikipedia.json), che l'Archivio storico
del Ministero non ha (queste regioni gestiscono da sé le elezioni locali).

Si lancia a mano, con la cartella delle pagine scaricate in wikitext (index.php?title=...&action=raw):
    python strumenti/candidati_wikipedia.py CARTELLA
con dentro aAAAA.txt («Elezioni amministrative in Italia del AAAA»), reg/Regione_AAAA.txt
(«Elezioni comunali in Sicilia del AAAA», Friuli-Venezia_Giulia, Trentino-Alto_Adige, Valle_dAosta)
ed eventualmente ded/*.txt (pagine dedicate, «Elezioni comunali a Palermo del 2012», con _ al posto degli spazi).

Per ogni riquadro {{Elezioni}} di un comune legge la tabella che segue ({{Elezione amministrativa}},
{{Elezione candidati}}, {{Elezione individuale}} o una wikitable): candidati con la percentuale del primo
turno e liste collegate con la loro percentuale, calcolate come fa il Modulo:Risultati (voti del candidato
sul totale dei voti ai candidati, voti di lista sul totale dei voti di lista). Area del candidato: prima la
coalizione del riquadro, poi l'area della tabella, poi il partito del riquadro.
Scarta i riquadri senza data, con una data incoerente con la pagina o la sezione (salvo che dati/comunali.js
abbia la stessa tornata entro un giorno: elezioni anticipate fuori turno), i comuni non riconosciuti e le date
che non trovano in dati/comunali.js una tornata dello stesso comune entro 45 giorni: la chiave è codice
catastale-data del primo turno come in dati/comunali.js. Controlla i voti della tabella con quelli del
riquadro: un refuso su un candidato si corregge se col voto del riquadro i totali tornano; se i totali
restano diversi di oltre lo 0,6% (o un candidato di oltre un punto) l'elezione si scarta; una lista senza
voti fa togliere le liste. La stessa elezione in due pagine: si tiene la più completa, a parità la regionale.
Le elezioni già presenti in dati/candidati/RR.js (Archivio del Ministero) restano: strumenti/comunali.py
aggiunge da qui solo quelle che mancano.
"""
import os, re, sys, json, glob, datetime as dt, unicodedata
from collections import Counter, defaultdict

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIKI = 'https://it.wikipedia.org/wiki/'
MESI = ['gennaio','febbraio','marzo','aprile','maggio','giugno','luglio','agosto','settembre','ottobre','novembre','dicembre']
_M = '|'.join(MESI)
REGIONI = {'Valle_dAosta': '02', 'Trentino-Alto_Adige': '04', 'Friuli-Venezia_Giulia': '06', 'Sicilia': '19'}
NOMI_REG = {'02': ("Valle d'Aosta", 'Valle d’Aosta'), '04': ('Trentino-Alto Adige', 'Trentino'), '06': ('Friuli-Venezia Giulia', 'Friuli Venezia Giulia'), '19': ('Sicilia',)}
SCARTO_TOTALE = 0.006  # differenza ammessa tra il totale dei voti della tabella e quello implicito nel riquadro
TOLLERANZA = 45  # giorni tra la data di Wikipedia e la tornata di dati/comunali.js


def norm(s):
    s = unicodedata.normalize('NFD', s.lower()); s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()


def date_box(anno, s):
    """«7, 21 maggio» -> [7 maggio, 21 maggio]; «2-3, 16-17 aprile»: conta il primo giorno di ogni turno."""
    gg = []
    for p in re.split(r',\s*|\s+e\s+(?=\d)', re.sub(r'\d{4}', '', s)):
        m = re.match(r'\s*(\d{1,2})', p.replace('º', '').replace('°', ''))
        if m: gg.append([int(m.group(1)), next((MESI.index(w) + 1 for w in re.findall(r'[a-z]+', p.lower()) if w in MESI), None)])
    mese = None
    for g in reversed(gg):
        if g[1]: mese = g[1]
        else: g[1] = mese
    out = []
    for d, m in gg:
        try:
            if m: out.append(dt.date(anno, m, d))
        except ValueError:
            pass
    return out


def date_testo(anno, s):
    return [dt.date(anno, MESI.index(m.lower()) + 1, int(g)) for g, m in re.findall(r"(\d{1,2})[°º]?(?:\s*(?:e|-)\s*(?:il\s+)?\d{1,2})?\s+(" + _M + r")", s, re.I)
            if 1 <= int(g) <= 31 and not (int(g) > 30 and m.lower() in ('aprile', 'giugno', 'settembre', 'novembre'))]


def abbr(s):
    """{{abbr|sigla|significato}} -> sigla (la sigla può contenere link con «|»)."""
    while True:
        m = re.search(r'\{\{\s*[Aa]bbr\s*\|', s)
        if not m: return s
        j, liv, parti, cur = m.end(), 1, [], ''
        while j < len(s) and liv:
            c2 = s[j:j + 2]
            if c2 in ('{{', '[['): liv += 1; cur += c2; j += 2; continue
            if c2 in ('}}', ']]'):
                liv -= 1
                if liv == 0: j += 2; break
                cur += c2; j += 2; continue
            if s[j] == '|' and liv == 1: parti.append(cur); cur = ''; j += 1; continue
            cur += s[j]; j += 1
        parti.append(cur)
        s = s[:m.start()] + parti[0] + s[j:]


def senza_template(s):
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
    s = re.sub(r'<ref[^>/]*/>', '', s); s = re.sub(r'<ref[^>]*>.*?</ref>', '', s, flags=re.S)
    s = abbr(s)
    while re.search(r'\{\{[^{}]*\}\}', s): s = re.sub(r'\{\{[^{}]*\}\}', '', s)
    return s


def testo(s):
    """Testo visibile di una cella o di un parametro: link, grassetti, note e template tolti."""
    s = senza_template(s or '')
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r'\1', s)
    s = re.sub(r"\[https?://\S+\s*([^\]]*)\]", r'\1', s)
    s = re.sub(r'<br\s*/?>', ' ', s); s = re.sub(r'</?[a-z]+[^>]*>', '', s)
    s = s.replace("'''", '').replace("''", '').replace('&nbsp;', ' ').replace('{', '').replace('}', '')
    s = re.sub(r'\s*\((?:A|B|C|D|E|F|1|2|3|\*)\)\s*$', '', s)  # lettere degli apparentamenti
    return re.sub(r'\s+', ' ', s).strip(' -–')


def voti(s):
    s = re.sub(r'[\s ]', '', senza_template(s or '').replace("'''", ''))
    if re.fullmatch(r'\d{1,3}(\.\d{3})+', s): s = s.replace('.', '')
    return int(s) if re.fullmatch(r'\d+', s) else None


def numero(s):
    s = senza_template(s or '').replace("'''", '').strip()
    if re.fullmatch(r'\d{1,2}\.\d{1,2}', s): return float(s)  # percentuale scritta col punto
    return float(s.replace('.', '').replace(',', '.')) if re.fullmatch(r'[\d.]+(,\d+)?', s) else None


def campi_box(body):
    return dict((k.strip(), v.strip()) for k, v in re.findall(r"^\|\s*([^=|]+?)\s*=(.*)$", body, re.M))


def template(t, nome, da, a):
    """Il primo {{nome ...}} tra da e a: (parametri con nome, parametri posizionali) o None."""
    i = t.find('{{' + nome, da)
    if i < 0 or i >= a: return None
    j, liv = i, 0
    while j < len(t):
        if t.startswith('{{', j): liv += 1; j += 2; continue
        if t.startswith('}}', j):
            liv -= 1; j += 2
            if liv == 0: break
            continue
        j += 1
    corpo = t[i + 2 + len(nome):j - 2]
    parti, liv, cur, k = [], 0, '', 0
    while k < len(corpo):
        c2 = corpo[k:k + 2]
        if c2 in ('{{', '[['): liv += 1; cur += c2; k += 2; continue
        if c2 in ('}}', ']]'): liv -= 1; cur += c2; k += 2; continue
        if corpo[k] == '|' and liv == 0: parti.append(cur); cur = ''; k += 1; continue
        cur += corpo[k]; k += 1
    parti.append(cur)
    nominati, posiz = {}, []
    for p in parti[1:]:
        m = re.match(r'\s*([A-Za-z%][\w%]*)\s*=(.*)$', p, re.S)
        if m: nominati[m.group(1)] = m.group(2).strip()
        else: posiz.append(p.strip())
    return nominati, posiz


def pct(v, tot):
    return round(v / tot * 100, 2) if v is not None and tot else None


def indici(par):
    """Numeri dei candidati c1, c2, ... nell'ordine; anche con buchi o fuori ordine (c1, c2, c4, c3)."""
    return sorted(int(k[1:]) for k in par if re.fullmatch(r'c\d+', k) and par[k].strip())


def da_amministrativa(par):
    """{{Elezione amministrativa}}: [[nome, %, [[lista, %], ...], area tabella], ...]"""
    cand = []
    for i in indici(par):
        liste, j = [], 1
        while ('c%dl%d' % (i, j)) in par:
            liste.append([testo(par['c%dl%d' % (i, j)]), voti(par.get('c%dv%d' % (i, j)))]); j += 1
        cand.append([testo(par['c%d' % i]), voti(par.get('v%d' % i)), liste, testo(par.get('a%d' % i, ''))])
    idem = par.get('sistema', '').strip() == 'idem'
    if idem:  # comuni minori: i voti del candidato sono quelli della sua lista
        for c in cand: c[1] = c[2][0][1] if c[2] else c[1]
    tot_c = sum(c[1] or 0 for c in cand)
    tot_l = sum(l[1] or 0 for c in cand for l in c[2])
    mancano = [c[0] for c in cand if c[1] is None]
    if any(l[1] is None for c in cand for l in c[2]):
        # una lista senza voti falsa le percentuali di tutte le altre: si tengono solo i candidati
        mancano_l = [l[0] for c in cand for l in c[2] if l[1] is None]
        return [[c[0], pct(c[1], tot_c), [], c[3], c[1]] for c in cand], mancano + ['liste: ' + ', '.join(mancano_l)]
    return [[c[0], pct(c[1], tot_c), [[l[0], pct(l[1], tot_l)] for l in c[2]], c[3], c[1]] for c in cand], mancano


def da_candidati(par):
    """{{Elezione candidati}}: candidati senza liste collegate (Sicilia 1993-1994, voto separato)."""
    cand = [[testo(par['c%d' % i]), voti(par.get('v%d' % i)), [], testo(par.get('a%d' % i, ''))] for i in indici(par)]
    tot = sum(c[1] or 0 for c in cand)
    return [[c[0], pct(c[1], tot), [], c[3], c[1]] for c in cand], [c[0] for c in cand if c[1] is None]


def da_individuale(posiz):
    """{{Elezione individuale}}: terne posizionali nome | sostegno | voti."""
    cand = [[testo(posiz[k]), voti(posiz[k + 2]), [], ''] for k in range(0, len(posiz) - 2, 3)]
    tot = sum(c[1] or 0 for c in cand)
    return [[c[0], pct(c[1], tot), [], c[3], c[1]] for c in cand], [c[0] for c in cand if c[1] is None]


def pulisci_cella(cella):
    c = cella
    while re.search(r'\{\{[^{}]*\}\}', c): c = re.sub(r'\{\{[^{}]*\}\}', '', c)
    c = re.sub(r'^\s*(?:[a-z]+\s*=\s*"?[^|"]*"?\s*)+\|', '', c)
    return c.strip()


def da_wikitable(t, da):
    """Tabella wikitable con i candidati in grassetto e le liste sotto (come tabella() di provinciali_wikipedia.py)."""
    i = t.find('{|', da)
    if i < 0: return []
    corpo = t[i:t.find('\n|}', i)]
    cand = []
    for riga in corpo.split('\n|-')[1:]:
        celle = [c for c in (pulisci_cella(c) for c in re.split(r'\n\||\|\|', '\n' + riga.strip('\n'))[1:]) if c != '']
        k = 0
        while k < len(celle):
            c = celle[k]
            if "'''" in c and numero(c) is None and not c.startswith('!'):
                nums = [numero(x) for x in celle[k + 1:k + 3]]
                cand.append([testo(c), nums[1] if len(nums) > 1 else None, [], '', None]); k += 3; continue
            if numero(c) is None and cand and not re.search(r"Seggio|Totale|colspan|''", c, re.I) and (('[[' in c) or re.search(r'[A-Za-z]{3}', c)):
                nums = [numero(x) for x in celle[k + 1:k + 3]]
                if len(nums) > 1 and nums[1] is not None:
                    cand[-1][2].append([testo(c), nums[1]]); k += 3; continue
            k += 1
    return cand


# Area di un'etichetta (coalizione o area del riquadro, area della tabella, partito), letta sul titolo della voce
# collegata (così «PDS» è il Partito Democratico della Sinistra). Prima le coalizioni, poi i partiti; «Unione di
# Centro» e «Unione Democratica per la Repubblica» non sono l'Unione di centrosinistra. Liste civiche senza
# indicazione, indipendenti, trasversali e autonomisti (MPA, PATT, SVP, Union Valdôtaine) restano senza area.
AREA_COALIZIONI = [
    (r"civic[ah]e? (?:di )?centrosinistra|indipendente di centrosinistra", 'centrosinistra'),
    (r"civic[ah]e? (?:di )?centrodestra|indipendente di centrodestra", 'centrodestra'),
    (r"civic[ah]e? (?:di )?centro$", 'centro'),
    (r"civic[ah]e? (?:di )?destra$", 'destra'),
    (r"civic[ah]e? (?:di )?sinistra$", 'sinistra'),
    (r"nuovo polo per l.italia|terzo polo", 'centro'),
    (r"centrosinistra|\bulivo\b|^l.unione$|^unione$|progressisti", 'centrosinistra'),
    (r"centrodestra|polo (?:per|delle) libert|polo del buon governo|casa delle libert", 'centrodestra'),
    (r"^centrismo|^centro$|pentapartito", 'centro'),
    (r"^(?:estrema )?sinistra(?: \(politica\))?$", 'sinistra'),
    (r"^(?:estrema )?destra(?: \(politica\))?$", 'destra'),
]
AREA_PARTITI = [
    (r"rifondazione|comunist|federazione della sinistra|potere al popolo|sinistra ecologia|^prc$|^pdci$", 'sinistra'),
    (r"alleanza nazionale|movimento sociale|fiamma|^la destra|forza nuova|alternativa sociale|fratelli d.italia|fronte nazionale|fascismo|^an$|^msi|^fdi$", 'destra'),
    (r"forza italia|popolo della libert|lega per salvini|^lega$|centro cristiano democratico|cristiani democratici uniti|nuovo psi|nuova sicilia|grande sud|forza del sud|biancofiore|diventer. bellissima|^fi$|^ccd$|^cdu$|^pdl$|^ncd$|nuovo centrodestra", 'centrodestra'),
    (r"partito democratico|democratici di sinistra|margherita|italia dei valori|federazione dei verdi|^verdi$|la rete|socialisti democratici italiani|^socialisti italiani$|^i democratici|rinnovamento italiano|udeur|italia in comune|megafono|sicilia futura|\+europa|partito socialista italiano \(2007\)|^pds$|^ds$|^pd$|^idv$|^sdi$", 'centrosinistra'),
    (r"unione di centro|alleanza di centro|^azione|italia viva|futuro e libert|alleanza per l.italia|cantiere popolare|democrazia europea|patto segni|patto per l.italia|^udc$|democratici cristiani e di centro|^area popolare", 'centro'),
    (r"movimento 5 stelle|^m5s$", 'altro'),
]


def area_parte(p, anno):
    p = p.lower().strip()
    if not p or re.fullmatch(r"nessun[ao]|liste? civic[ah]e?|indipendente.*|trasversal.*|altri", p): return None
    for rx, a in AREA_COALIZIONI:
        if re.search(rx, p): return a
    # «Liga Veneta» e «Lega Lombarda» nelle pagine di Friuli e Sicilia servono solo a dare un colore (indipendentisti, liste locali)
    if re.search(r"^liga veneta|^lega lombarda", p): return None
    if re.search(r"^lega nord", p): return 'altro' if anno < 2000 else 'centrodestra'
    if re.search(r"^democrazia cristiana$|^dc$", p): return 'centro' if anno < 1995 else None
    if re.search(r"^partito popolare italiano|^ppi$", p): return 'centro' if anno < 1995 else 'centrosinistra'
    if re.search(r"partito repubblicano|partito liberale|partito socialista democratico|^pri$|^pli$|^psdi$", p): return 'centro' if anno < 1995 else None
    return next((a for rx, a in AREA_PARTITI if re.search(rx, p)), None)


def area_di(etichetta, anno):
    """Area politica di un'etichetta di Wikipedia. Per più sigle unite da «-» o «+»: l'area comune; un partito di
    centro (o fuori dai poli) insieme a un polo resta del polo; con partiti di entrambi i poli nessuna area."""
    e = re.sub(r"\[\[([^|\]]*)(?:\|[^\]]*)?\]\]", r"\1", senza_template(etichetta or ''))
    e = testo(e).replace('’', "'")
    e = re.sub(r'\s*\((?:politica|partito politico|Italia|\d{4})\)', '', e)
    e = re.sub(r'centro[- ]?(sinistra|destra)', lambda m: 'centro' + m.group(1).lower(), e, flags=re.I)
    if not e: return None
    aree = {area_parte(p, anno) for p in re.split(r'\s+-\s+|-(?=[A-Z#])|\s*\+\s*|\s+e\s+(?=[A-Z])', e)} - {None}
    poli = aree - {'centro', 'altro'}
    if not aree: return None
    if len(aree) == 1: return aree.pop()
    # con un partito di centro, la destra e la sinistra diventano centrodestra e centrosinistra
    if poli <= {'sinistra', 'centrosinistra'} and poli: return 'centrosinistra' if len(poli) > 1 or 'centro' in aree else poli.pop()
    if poli <= {'destra', 'centrodestra'} and poli: return 'centrodestra' if len(poli) > 1 or 'centro' in aree else poli.pop()
    return None


def carica_comuni():
    righe = open(os.path.join(RADICE, 'dati', 'comuni.js'), encoding='utf-8').read().split('`')[1].split('\n')
    idx = defaultdict(list)
    for r in righe:
        n, sig, reg, c, att, al = r.split('|')
        if reg not in NOMI_REG: continue
        for x in [n] + [a for a in al.split(';') if a]:
            idx[(reg, norm(x))].append((c, att == '1'))
            for parte in re.split(r'[/]|\s-\s', x):  # nomi bilingui: «Bolzano/Bozen» anche come «Bolzano»
                if parte.strip() and parte.strip() != x: idx[(reg, norm(parte))].append((c, att == '1'))
    return idx


def carica_comunali():
    js = open(os.path.join(RADICE, 'dati', 'comunali.js'), encoding='utf-8').read()
    D = json.loads(re.search(r'const COMUNALI_DATE = (\[.*?\]);', js, re.S).group(1))
    out = {}
    for r in re.search(r'const COMUNALI_TXT = `(.*?)`;', js, re.S).group(1).split('\n'):
        if ':' in r:
            c, v = r.split(':'); out[c] = [D[abs(int(i)) - 1] for i in v.split(',')]
    return out


def intro(t, parola):
    pr = re.search(r"'''" + parola + r"[^']*'''([^\n]*)", t, re.I)
    return senza_template(pr.group(1)) if pr else ''


def frasi_regione(t, reg):
    """Date dette nel capo della pagina nazionale per la regione («In Sicilia le elezioni si sono tenute il 25 novembre»)."""
    capo = senza_template(t.split('\n==', 1)[0])
    return [f for f in re.split(r'(?<=[a-z\]\)])\.\s+', capo) if any(n in f for n in NOMI_REG[reg])]


def riquadri(cartella):
    """Ogni riquadro {{Elezioni}} di un comune delle quattro regioni, con la tabella che lo segue."""
    pagine = []
    for f in sorted(glob.glob(os.path.join(cartella, 'reg', '*.txt'))):
        base = os.path.basename(f)[:-4]; nome_reg, anno = base.rsplit('_', 1)
        titolo = f"Elezioni comunali in {nome_reg.replace('_', ' ').replace('dAosta', 'd%27Aosta')} del {anno}"
        pagine.append(('reg', f, int(anno), REGIONI[nome_reg], titolo))
    for f in sorted(glob.glob(os.path.join(cartella, 'a[12]*.txt'))):
        anno = int(os.path.basename(f)[1:5])
        pagine.append(('naz', f, anno, None, f'Elezioni amministrative in Italia del {anno}'))
    for f in sorted(glob.glob(os.path.join(cartella, 'ded', '*.txt'))):
        titolo = os.path.basename(f)[:-4].replace('_', ' ')
        pagine.append(('ded', f, int(re.search(r'(\d{4})$', titolo).group(1)), None, titolo))
    for tipo, f, anno, reg_pag, titolo in pagine:
        t = open(f, encoding='utf-8').read()
        if tipo == 'reg':
            ref_intro = date_testo(anno, intro(t, 'elezioni comunali'))
        elif tipo == 'ded':
            ref_intro = date_testo(anno, intro(t, 'elezioni comunali'))
        box = list(re.finditer(r"\{\{Elezioni\s*\n(.*?)\n\}\}", t, re.S))
        intest = [(m.start(), len(m.group(1)), m.group(2).strip()) for m in re.finditer(r"^(={2,5})\s*([^=]+?)\s*\1\s*$", t, re.M)]
        for n, m in enumerate(box):
            campi = campi_box(m.group(1))
            if 'comune' not in campi: continue
            prima = [h for h in intest if h[0] < m.start()]
            sez2 = next((h[2] for h in reversed(prima) if h[1] == 2), '')
            reg = reg_pag
            if tipo == 'naz':
                sez3 = next((h for h in reversed(prima) if h[1] <= 3), None)
                if not sez3 or sez3[1] != 3: continue
                reg = next((r for r, nomi in NOMI_REG.items() if any(sez3[2].startswith(x) for x in nomi)), None)
                if not reg: continue
                ref_intro = date_testo(anno, ' '.join(frasi_regione(t, reg)))
            fine = box[n + 1].start() if n + 1 < len(box) else len(t)
            yield dict(tipo=tipo, titolo=titolo, anno=anno, reg=reg, campi=campi, t=t, da=m.end(), a=fine,
                       sez2=sez2, ref_intro=ref_intro, sezione=(prima[-1][2] if prima else ''))


def leggi_tabella(r):
    t, da, a = r['t'], r['da'], r['a']
    for nome, f in (('Elezione amministrativa', 'amm'), ('Elezione candidati', 'cand'), ('Elezione individuale', 'ind')):
        x = template(t, nome, da, a)
        if x:
            par, posiz = x
            if f == 'amm': return da_amministrativa(par) + (nome,)
            if f == 'cand': return da_candidati(par) + (nome,)
            return da_individuale(posiz) + (nome,)
    i = t.find('{|', da)
    if 0 <= i < a:
        return da_wikitable(t, da), [], 'wikitable'
    return [], [], None


def main(cartella):
    comuni = carica_comuni(); comunali = carica_comunali()
    trovate, scarti, dubbi = {}, [], []
    for r in riquadri(cartella):
        campi, anno, reg = r['campi'], r['anno'], r['reg']
        nome = re.sub(r'\s*\(.*?\)', '', testo(campi.get('comune', ''))).strip()
        fonte = WIKI + r['titolo'].replace(' ', '_') + ('#' + nome.replace(' ', '_') if r['tipo'] != 'ded' else '')
        etich = f"{anno} {nome} ({r['titolo']})"
        ds = date_box(anno, campi.get('data', ''))
        anni = re.findall(r'\d{4}', campi.get('data', ''))
        if not ds: scarti.append((etich, 'riquadro senza data')); continue
        if anni and any(int(x) != anno for x in anni): scarti.append((etich, f"anno della data diverso dalla pagina: {campi.get('data')}")); continue
        cands = comuni.get((reg, norm(nome)), [])
        if not cands: scarti.append((etich, 'comune non riconosciuto in dati/comuni.js')); continue
        cod = sorted(cands, key=lambda c: not c[1])[0][0]
        nostri = sorted(comunali.get(cod, []), key=lambda d: abs((dt.date.fromisoformat(d) - ds[0]).days))
        vicina = nostri[0] if nostri else None
        gg = abs((dt.date.fromisoformat(vicina) - ds[0]).days) if vicina else None
        # coerenza con la pagina: le date dell'introduzione (per la pagina nazionale, quelle dette per la regione)
        # o il mese della sezione («Elezioni del giugno 1993»). Conferma la data una sezione con lo stesso giorno
        # o la stessa tornata (entro un giorno) in dati/comunali.js, che viene da altre fonti: così restano le
        # elezioni anticipate fuori dal turno della pagina (Messina e Bolzano, novembre 2005).
        conferma = f"{ds[0].day} {MESI[ds[0].month - 1]}" in r['sez2'] or (gg is not None and gg <= 1)
        # (nelle pagine nazionali le sezioni raggruppano i turni delle regioni ordinarie: conta solo l'introduzione)
        mesi_sez = [MESI.index(w) + 1 for w in re.findall(r'[a-z]+', r['sez2'].lower()) if w in MESI] if r['tipo'] == 'reg' else []
        if not conferma and mesi_sez and ds[0].month not in mesi_sez:
            scarti.append((etich, f"data {campi.get('data')} incoerente con la sezione «{r['sez2']}»")); continue
        if not conferma and not mesi_sez and r['ref_intro'] and not any(abs((ds[0] - d).days) <= 3 for d in r['ref_intro']):
            scarti.append((etich, f"data {campi.get('data')} incoerente con l'introduzione ({', '.join(d.isoformat() for d in r['ref_intro'])})")); continue
        if vicina is None or gg > TOLLERANZA:
            scarti.append((etich, f"nessuna tornata di dati/comunali.js entro {TOLLERANZA} giorni dal {ds[0].isoformat()} ({cod})")); continue
        data = vicina
        scarto_gg = (dt.date.fromisoformat(data) - ds[0]).days
        cand, mancano, formato = leggi_tabella(r)
        if any(not m.startswith('liste: ') for m in mancano):
            scarti.append((etich, 'candidati senza voti nella tabella: ' + ', '.join(mancano))); continue
        cand = [c for c in cand if c[0] and not re.match(r'\s*totale\b', c[0], re.I)]
        for c in cand: c[2] = [l for l in c[2] if l[0] and not re.match(r'\s*totale\b', l[0], re.I)]
        # dal riquadro: percentuale e voti (controllo) e coalizione/partito per l'area
        nel_box = {}
        for i in range(1, 16):
            cb = testo(campi.get(f'candidato{i}', ''))
            if cb: nel_box[norm(cb)] = (numero(campi.get(f'%{i}', '')), campi.get(f'coalizione{i}', ''), campi.get(f'partito{i}', ''), cb, voti(campi.get(f'voti{i}', '')))
        def dal_box(n):
            k = norm(n)
            if k in nel_box: return nel_box[k]
            # stesso cognome e nome abbreviato («Salvo» per «Salvatore Domenico Antonio»)
            if not k: return None
            simili = [v for kk, v in nel_box.items() if kk.split()[-1] == k.split()[-1] and kk.split()[0][:3] == k.split()[0][:3]
                      and not any(norm(c[0]) == kk for c in cand)]
            return simili[0] if len(simili) == 1 else None
        nota = []
        if not cand:
            # nessuna tabella: i candidati del riquadro, senza liste
            cand = [[v[3], v[0], [], '', v[4]] for v in nel_box.values()]
            formato = 'solo riquadro'
            nota.append(f'solo i {len(cand)} candidati del riquadro, senza liste')
        elif formato != 'wikitable':
            # controllo dei voti: il totale dei voti ai candidati della tabella deve tornare con quello implicito nel
            # riquadro (voti / percentuale, uguale per i candidati del riquadro). Se non torna e sostituendo i voti
            # diversi con quelli del riquadro il totale torna, la tabella ha un refuso e si corregge; altrimenti si scarta.
            stime = [v[4] * 100 / v[0] for v in nel_box.values() if v[0] and v[4]]
            t_box = sum(stime) / len(stime) if stime and max(stime) / min(stime) - 1 <= 0.003 else None
            t_tab = sum(c[4] or 0 for c in cand)
            if t_box and t_tab and abs(t_tab - t_box) / t_box > 0.0005:
                diversi = [(c, dal_box(c[0])) for c in cand]
                diversi = [(c, b) for c, b in diversi if b and b[4] is not None and b[4] != c[4]]
                t_corr = t_tab + sum(b[4] - (c[4] or 0) for c, b in diversi)
                if diversi and abs(t_corr - t_box) / t_box <= 0.002:
                    for c, b in diversi:
                        nota.append(f"voti di {c[0]} corretti col riquadro: {c[4]} -> {b[4]}"); c[4] = b[4]
                elif abs(t_tab - t_box) / t_box <= SCARTO_TOTALE:
                    nota.append(f"totale dei voti della tabella {t_tab}, dal riquadro {round(t_box)} ({(t_tab - t_box) / t_box * 100:+.2f}%)")
                else:
                    scarti.append((etich, f"voti della tabella incoerenti col riquadro (totale {t_tab} contro {round(t_box)} dal riquadro)")); continue
            tot = sum(c[4] or 0 for c in cand)
            for c in cand: c[1] = pct(c[4], tot)
        out, diff = [], []
        for c in cand:
            b = dal_box(c[0])
            # percentuale diversa dal riquadro: conta solo se anche i voti sono diversi (altrimenti è un refuso del riquadro)
            if b and b[0] is not None and c[1] is not None and abs(b[0] - c[1]) > 0.05 and not (b[4] is not None and b[4] == c[4]):
                diff.append(f"{c[0]} tabella {c[1]}% ({c[4]} voti) / riquadro {b[0]}% ({b[4]} voti)")
            area = None
            for et in ([b[1]] if b else []) + [c[3]] + ([b[2]] if b else []):
                area = area_di(et, anno) if et else None
                if area: break
            out.append([c[0], c[1], [[l[0], l[1]] for l in c[2]], area])
        out.sort(key=lambda c: -(c[1] or 0))
        if any(abs(float(x.split('tabella ')[1].split('%')[0]) - float(x.split('riquadro ')[1].split('%')[0])) > 1 for x in diff):
            scarti.append((etich, 'percentuali della tabella diverse di oltre un punto dal riquadro, con voti diversi: ' + '; '.join(diff[:2]))); continue
        if not out or all(c[1] is None for c in out): scarti.append((etich, 'nessun candidato con percentuale')); continue
        voce = {'comune': nome, 'reg': reg, 'c': out, 'fonte': fonte}
        if mancano: nota.append('liste tolte, voti mancanti nella tabella per ' + mancano[0][7:])
        if diff: nota.append('percentuali diverse dal riquadro: ' + '; '.join(diff[:3]))
        if scarto_gg: nota.append(f'data Wikipedia {ds[0].isoformat()}, in dati/comunali.js {data} ({scarto_gg:+d} giorni)')
        chiave = f'{cod}-{data}'
        if chiave in trovate:
            vecchia = trovate[chiave]
            # stessa elezione in due pagine: si tiene la tabella più completa, a parità la pagina regionale o dedicata
            peso = lambda v: (sum(len(c[2]) for c in v['c']) > 0, len(v['c']), not v.get('_dubbi'), v['_tipo'] != 'naz')
            nuova = dict(voce, _tipo=r['tipo'], _dubbi=nota)
            top = lambda v: [(c[0], c[1]) for c in v['c'][:2]]
            if top(vecchia) != top(nuova): dubbi.append((chiave, f"due pagine con dati diversi: {top(vecchia)} / {top(nuova)}"))
            if peso(nuova) > peso(vecchia): trovate[chiave] = nuova
            continue
        trovate[chiave] = dict(voce, _tipo=r['tipo'], _dubbi=nota)
    for k, v in trovate.items():
        for n in v.pop('_dubbi'): dubbi.append((k, n))
        v.pop('_tipo')
    return trovate, scarti, dubbi


if __name__ == '__main__':
    cartella = sys.argv[1] if len(sys.argv) > 1 else '.'
    trovate, scarti, dubbi = main(cartella)
    uscita = {
        'descrizione': "Candidati sindaco (percentuale al primo turno), liste collegate (percentuale sul totale dei voti di lista) e area politica "
                       "delle comunali di Valle d'Aosta, Trentino-Alto Adige, Friuli-Venezia Giulia e Sicilia dal 1993, dai riquadri {{Elezioni}} "
                       "e dalle tabelle dei risultati di it.wikipedia.org. Chiave: codice catastale-data del primo turno come in dati/comunali.js. "
                       "Voce: [nome, %, [[lista, %], ...], area]. Generato da strumenti/candidati_wikipedia.py; strumenti/comunali.py le aggiunge "
                       "a dati/candidati/RR.js se l'Archivio del Ministero non le ha.",
        'elezioni': dict(sorted(trovate.items(), key=lambda kv: (kv[1]['reg'], kv[1]['comune'], kv[0]))),
    }
    # un'elezione per riga, così i cambiamenti si leggono nelle differenze di git
    righe = [f' {json.dumps(k)}: {json.dumps(v, ensure_ascii=False, separators=(",", ":"))}' for k, v in uscita['elezioni'].items()]
    with open(os.path.join(RADICE, 'strumenti', 'candidati-wikipedia.json'), 'w', encoding='utf-8') as f:
        f.write('{\n "descrizione": ' + json.dumps(uscita['descrizione'], ensure_ascii=False) + ',\n "elezioni": {\n' + ',\n'.join(righe) + '\n }\n}\n')
    print(len(trovate), 'elezioni;', len(scarti), 'scartate;', len(dubbi), 'note')
    print(Counter((v['reg'], k[5:9]) for k, v in trovate.items()))
    print('--- scarti'); [print(' ', *s, sep=' | ') for s in scarti]
    print('--- note'); [print(' ', *d, sep=' | ') for d in dubbi]
