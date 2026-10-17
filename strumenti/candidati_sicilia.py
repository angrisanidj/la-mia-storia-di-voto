"""Candidati sindaco delle comunali siciliane che mancano a dati/candidati/19.js (strumenti/candidati-sicilia.json),
presi soprattutto dal sito elettorale della Regione Siciliana (www.elezioni.regione.sicilia.it, Servizio elettorale
dell'Assessorato delle Autonomie locali), letto attraverso le copie della Wayback Machine di archive.org: il sito
non risponde dall'estero (né da qui né da GitHub Actions), ma l'Internet Archive ne conserva molte pagine.

Il sito c'è dal 2008: comunaliAAAA/primoTurno/PR/ReportRisultatiPRnnn.html (e la radice del sito, che mostra
l'ultima tornata) con, per ogni comune, i candidati sindaco con voti e percentuale e le liste collegate con voti e
percentuale sui voti validi alle liste; nnn è il numero del comune nell'elenco alfabetico regionale. Valgono anche
ReportCandidatiListe (stessi dati senza intestazione), ReportSeggi (solo le liste sopra lo sbarramento: la loro
percentuale si ricalcola sul totale dei voti di lista, liste sbarrate comprese), ReportCandidati (solo i candidati) e
le versioni in PDF. Si tengono solo le pagine del primo turno (FLAGBALLOTTAGGIO falso, niente «Turno di ballottaggio»),
a scrutinio completo, con comune, provincia e data uguali a quelli dell'elezione cercata; la percentuale del candidato
è calcolata sui voti validi ai candidati e deve tornare con quella della pagina; i voti dei candidati devono sommare
ai voti validi per il sindaco dell'intestazione.

Per gli anni precedenti al 2008 il sito non ha nulla. Si aggiungono, segnalati come dubbi:
  - tre elezioni (Bronte e Caltagirone 1993, Scicli 2012) scartate da strumenti/candidati_wikipedia.py solo perché il
    riquadro {{Elezioni}} di Wikipedia ha la data di un'altra tornata (CORREZIONI_DATA): si rileggono con la data
    della sezione della pagina;
  - Belpasso, Corleone e Floridia 1993 e Grammichele 1994, che Wikipedia ha con una tabella sbagliata (i voti non
    tornano col riquadro; per Belpasso anche la data del riquadro è sbagliata): si prendono dall'Archivio elettorale
    di Roberto Brocchini (archivioelettorale.it, fonte citata da Wikipedia, che dichiara come fonti il Ministero
    dell'Interno e la stampa), copia della Wayback Machine, se il totale torna col riquadro di Wikipedia;
    Cinisi 1993 (giugno) solo da lì, senza riscontro.

Si lancia a mano:
    python strumenti/candidati_sicilia.py urls PAGINE ELENCO.json
stampa gli indirizzi della Wayback Machine da scaricare (col workflow «Sonda»), a partire dagli elenchi CDX salvati in
PAGINE (cdx_report.json, cdx_pdf.json: https://web.archive.org/cdx/search/cdx?url=elezioni.regione.sicilia.it/*
&output=json&fl=timestamp,original,statuscode,digest&collapse=digest&filter=statuscode:200&filter=original:.*Report.*html.*
e lo stesso con pdf) e dalle pagine provinciali in PAGINE/prov (per i numeri dei comuni);
    python strumenti/candidati_sicilia.py PAGINE WIKI ELENCO.json
scrive strumenti/candidati-sicilia.json leggendo le pagine scaricate (PAGINE/indice.json: indirizzo -> file),
la cartella WIKI di strumenti/candidati_wikipedia.py (reg/Sicilia_AAAA.txt) e l'elenco delle elezioni da cercare
(ELENCO.json: [{"cod", "comune", "sigla", "reg", "data", "ballottaggio"}, ...], data del primo turno come in
dati/comunali.js). Nomi da «COGNOME NOME» a «Nome Cognome»; area lasciata a null (l'app la ricava dalle liste).
"""
import os, re, sys, json, html, glob, tempfile, subprocess, unicodedata, collections, datetime as dt

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, 'strumenti'))
WAYBACK = 'https://web.archive.org/web/'
MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre']
TIPI = {'Risultati': 0, 'CandidatiListe': 1, 'Seggi': 2, 'Candidati': 3}  # preferenza tra i report

# Numeri del sito per i comuni che non compaiono nelle pagine provinciali scaricate: l'elenco è alfabetico su tutta
# la regione, il numero si ricava dai vicini (Melilli 191, Messina 194 -> Menfi 192). Servono solo a cercare le pagine,
# che si accettano comunque solo se dicono «Comune di <nome> (<provincia>)».
NUMERI_DEDOTTI = {('AG', 'menfi'): 192, ('AG', 'ravanusa'): 274, ('CL', 'riesi'): 280, ('CT', 'ramacca'): 272,
                  ('EN', 'barrafranca'): 31, ('EN', 'leonforte'): 166, ('EN', 'troina'): 367, ('ME', 'capo d orlando'): 74,
                  ('ME', 'patti'): 247, ('ME', 'sant agata di militello'): 325, ('PA', 'casteldaccia'): 84, ('SR', 'noto'): 231,
                  ('TP', 'castellammare del golfo'): 85, ('TP', 'erice'): 118, ('TP', 'paceco'): 235, ('TP', 'partanna'): 244,
                  ('TP', 'valderice'): 371}

# Riquadri di Wikipedia con la data di un'altra tornata: (anno della pagina, comune) -> data giusta (quella della sezione
# «Elezioni del novembre 1993» e dell'introduzione; per Scicli il ballottaggio del 20-21 maggio 2012 è confermato dal
# sito della Regione, comunali2012/RG/ReportSeggiRG339.html).
CORREZIONI_DATA = {('1993', 'Bronte'): '21 novembre, 5 dicembre',
                   ('1993', 'Caltagirone'): '21 novembre, 5 dicembre', ('2012', 'Scicli'): '6-7, 20-21 maggio'}

# Archivio elettorale (archivioelettorale.it), pagine conservate dalla Wayback Machine: chiave -> (indirizzo, voti validi
# ai candidati implicati dal riquadro di Wikipedia, che devono tornare).
ARCHIVIO_ELETTORALE = {
    'D009-1993-11-21': ('https://web.archive.org/web/20230816095410id_/http://www.archivioelettorale.it/joomla/index.php?option=com_content&view=article&id=5654:comunali-corleone-pa-1993&catid=36:elezioni-comunali&Itemid=58', 7321),
    'E133-1994-06-12': ('https://web.archive.org/web/20230821090806id_/http://www.archivioelettorale.it/joomla/index.php?option=com_content&view=article&id=5661:comunali-grammichele-ct-1994&catid=36:elezioni-comunali&Itemid=58', 8571),
    'A766-1993-11-21': ('https://web.archive.org/web/20230812100109id_/http://www.archivioelettorale.it/joomla/index.php?option=com_content&view=article&id=5631:comunali-belpasso-ct-1993&catid=36:elezioni-comunali&Itemid=58', 10608),
    'D636-1993-11-21': ('https://web.archive.org/web/20230814103313id_/http://www.archivioelettorale.it/joomla/index.php?option=com_content&view=article&id=5656:comunali-floridia-sr-1993&catid=36:elezioni-comunali&Itemid=58', 12399),
    # Cinisi 1993: Wikipedia non ha il riquadro, nessun riscontro possibile
    'C708-1993-06-06': ('https://web.archive.org/web/20230810230702id_/http://www.archivioelettorale.it/joomla/index.php?option=com_content&view=article&id=5636:comunali-cinisi-pa-1993&catid=36:elezioni-comunali&Itemid=58', None),
}

PARTICELLE = {'DI', 'DE', 'DEL', 'DELLA', 'DELLE', 'DELLO', 'DEI', 'DEGLI', 'LO', 'LA', 'LI', 'LE', 'DA', 'DAL', 'DALLA', 'DALL', 'D',
              'SAN', 'SANTA', 'SANTO', 'MC', 'MAC', 'DU', 'DO'}
# nomi propri che i candidati di Wikipedia non bastano a riconoscere
NOMI_IN_PIU = set("""PIERA SABRINA ROSY MARILENA ROSALBA NICOLO FILIBERTO PANCRAZIO EDWARD EDDY OTELLO LILLO CETTINA MARA MILENA GIUSY
CATENO CALOGERO NUNZIO NUNZIA CONCETTA CARMELINA GIUSEPPA VITA ALBA AGATINO AGATA ORAZIO ALFIO SANTO SANTA CORRADO PLACIDO
BIAGIO GASPARE LIBORIO ONOFRIO GANDOLFO CALOGERA ROSARIA CROCIFISSA BARTOLO BARTOLOMEO IGNAZIO EZIO TURI TURE SALVO NINO NINA
PIPPO PEPPINO NELLO NUCCIO GIANNI MIMMO TOTO ENZO LELLO TANINO TANO FILIPPO ROCCO ROSOLINO VENERANDO GIACINTO
MARIAGRAZIA MARIA GRAZIA ESTER LUCIA LUCIANA ROSSANA ROSANNA SONIA SIMONA DANIELA PAOLA ANNA ANNAMARIA LETIZIA VALENTINA
FRANCESCA GIOVANNA ANTONELLA ANTONINA SERAFINA SEBASTIANA FILIPPA BENEDETTA VINCENZA CARMELA ROSA ROSETTA TERESA ELENA
CLAUDIA LAURA MONICA PATRIZIA CRISTINA BARBARA SILVIA ALESSANDRA ALESSIA MARCELLA MARINELLA MARIELLA MIRELLA ORNELLA
DAMIANO ANGELO GIAMBATTISTA GIOVAN BATTISTA PARIDE FLORIDIANO FLAVIO EMANUELE UMBERTO ALFONSO TOMMASO GIROLAMO GERLANDO""".split())


def norm(s):
    s = unicodedata.normalize('NFD', s.lower()); s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()


def numero(s):
    s = (s or '').replace('.', '').replace('%', '').replace(',', '.').strip()
    return float(s) if re.fullmatch(r'\d+(\.\d+)?', s) else None


def decodifica(b):
    try:
        return b.decode('utf-8')
    except UnicodeDecodeError:
        return b.decode('latin-1')


# ---------------------------------------------------------------- pagine del sito della Regione

def celle(t):
    """Il testo della pagina diviso nelle celle delle tabelle (e negli a capo)."""
    t = re.sub(r'<script.*?</script>|<style.*?</style>|<select.*?</select>|<!--.*?-->', '', t, flags=re.S | re.I)
    out = []
    for c in re.split(r'<(?:td|th|/td|/th|tr|/tr|br|p|div|/div|h\d|/h\d|font)\b[^>]*>', t, flags=re.I):
        c = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', c))).strip()
        if c:
            out.append(c.replace('NÂ°', 'N°'))
    return out


def data_titolo(s):
    """«15-16 giugno 2008», «31 Maggio - 01 Giugno 2015» -> data del primo giorno."""
    m = re.match(r'\s*(\d{1,2})(?:\s*-\s*\d{1,2})?\s+(\w+)\s+(?:-\s*\d{1,2}\s+\w+\s+)?(\d{4})', s)
    if m and m.group(2).lower() in MESI:
        return '%s-%02d-%02d' % (m.group(3), MESI.index(m.group(2).lower()) + 1, int(m.group(1)))
    return None


def leggi_html(b):
    t = decodifica(b)
    r = {'ballottaggio': False, 'data': None, 'comune': None, 'prov': None, 'cand': [], 'intest': None, 'sbarrate': False}
    if re.search(r'name="FLAGBALLOTTAGGIO" value="true"', t) or re.search(r'Turno di [Bb]allottaggio del', t):
        r['ballottaggio'] = True
    m = re.search(r'Elezioni (?:Comunali|Amministrative) del ([^<]+?)\s*<', t)
    if m: r['data'] = data_titolo(m.group(1))
    m = re.search(r'Comune di ([^<]+?) \(([A-Z]{2})\)', t)
    if m: r['comune'], r['prov'] = html.unescape(m.group(1)).strip(), m.group(2)
    sez = re.findall(r'relativi a n\. (\d+) su n\. (\d+) sezioni', t)
    r['completo'] = bool(re.search(r'scrutinio completo', t)) and all(a == b for a, b in sez)
    c = celle(t)
    if 'di cui bianche' in c:
        i = c.index('di cui bianche')
        vals = []
        for x in c[i + 1:i + 8]:
            if numero(x) is None: break
            vals.append(numero(x))
        r['sbarrate'] = 'Liste sbarrate' in c[i - 4:i]
        # votanti, %, voti validi sindaco, voti validi consiglio, [liste sbarrate], non valide, bianche
        r['intest'] = {'sindaco': vals[2], 'consiglio': vals[3] + (vals[4] if r['sbarrate'] else 0)} if len(vals) >= 6 else None
    i, cur = 0, None
    while i < len(c):
        if c[i] == 'VOTI' and i + 3 < len(c) and c[i + 2] == '%' and numero(c[i + 1]) is not None:
            k = i - 2
            while k > max(0, i - 8) and c[k] != 'N°': k -= 1
            ruolo = ' '.join(c[k + 2:i - 1])
            if 'Sindaco' not in ruolo: raise ValueError('candidato senza ruolo: %r' % c[k:i + 1])
            cur = {'nome': c[i - 1], 'eletto': 'Eletto' in ruolo, 'voti': numero(c[i + 1]), 'pct': numero(c[i + 3]), 'liste': []}
            r['cand'].append(cur); i += 4; continue
        if c[i] == 'Lista/e Collegata/e' and cur is not None:
            j = i + 1
            while c[j] in ('Candidati', 'Voti', '%', '%*', 'Seggi'): j += 1
            seggi = 'Seggi' in c[i:j]
            while j < len(c) and c[j] not in ('Totale', 'N°') and not re.match(r'Nessuna lista|Trattasi|I report', c[j]):
                if re.fullmatch(r'\d+', c[j]) and j + 4 < len(c) and numero(c[j + 3]) is not None:
                    cur['liste'].append([c[j + 1], numero(c[j + 3]), numero(c[j + 4])])
                    j += 6 if seggi else 5
                elif c[j] in ('Sindaco', 'Candidato', 'Candidato Sindaco', 'Sindaco Eletto') or c[j].startswith('*'):
                    break
                elif c[j].startswith('ALTRE LISTE'):
                    # liste non collegate ai candidati elencati: restano fuori (contano solo nel totale dei voti di lista)
                    cur = None; break
                else:
                    raise ValueError('riga di lista inattesa: %r' % c[j:j + 6])
            i = j; continue
        i += 1
    return r


def leggi_pdf(b):
    with tempfile.NamedTemporaryFile(suffix='.pdf') as f:
        f.write(b); f.flush()
        t = subprocess.run(['pdftotext', '-layout', f.name, '-'], capture_output=True, check=True).stdout.decode('utf-8', 'replace')
    r = {'ballottaggio': bool(re.search(r'Turno di Ballottaggio', t, re.I)), 'data': None, 'comune': None, 'prov': None,
         'cand': [], 'intest': None, 'sbarrate': False, 'completo': 'scrutinio completo' in t}
    m = re.search(r'Elezioni (?:Comunali|Amministrative) del ([^\n]+)', t)
    if m: r['data'] = data_titolo(m.group(1))
    m = re.search(r'COMUNE DI (.+?) \(([A-Z]{2})\)', t)
    if m: r['comune'], r['prov'] = m.group(1).strip().title(), m.group(2)
    m = re.search(r'di cui bianche\s*\n\s*\n?\s*([\d.\s,]+)\n', t)
    if m:
        v = [numero(x) for x in m.group(1).split()]
        if len(v) >= 8 and 'sbarrate' not in t:
            r['intest'] = {'sindaco': v[5], 'consiglio': v[6]}
    cur = None
    for riga in t.split('\n'):
        m = re.match(r'\s*N°\s+\d+\s+(Candidato Sindaco|Sindaco Eletto)\s+(.+?)\s{2,}VOTI\s+([\d.]+)\s+%\s+([\d,]+)', riga)
        if m:
            cur = {'nome': m.group(2).strip(), 'eletto': 'Eletto' in m.group(1), 'voti': numero(m.group(3)), 'pct': numero(m.group(4)), 'liste': []}
            r['cand'].append(cur); continue
        m = re.match(r'\s*(\d+)\s{3,}(.+?)\s{3,}(\d+)\s+([\d.]+)\s+([\d,]+)\s*$', riga)
        if m and cur is not None:
            cur['liste'].append([m.group(2).strip(), numero(m.group(4)), numero(m.group(5))])
    return r


def tipo_url(u):
    m = re.search(r'Report(Risultati|CandidatiListe|Candidati|Seggi)[A-Z]{2}\d+\.(html|pdf)$', u)
    return (TIPI[m.group(1)], m.group(2) == 'pdf', m.group(1)) if m else None


def fonte_wayback(u):
    return u.replace('id_/', '/', 1)


def da_regione(x, pagine, idx, nc):
    """La migliore pagina del primo turno per l'elezione x: (voce, note) o (None, motivi)."""
    prove, motivi = [], []
    for u, f in idx.items():
        tp = tipo_url(u)
        if not tp or 'elezioni.regione.sicilia.it' not in u: continue
        r = pagine.get(u)
        if r is None:
            try:
                b = open(os.path.join(cartella_pagine, f), 'rb').read()
                r = leggi_pdf(b) if tp[1] else leggi_html(b)
            except Exception as e:
                r = {'errore': str(e)}
            pagine[u] = r
        if 'errore' in r: continue
        if norm(r.get('comune') or '') != norm(x['comune']) or r.get('prov') != x['sigla']: continue
        if r['data'] != x['data']: continue
        if r['ballottaggio']: motivi.append('solo la pagina del ballottaggio'); continue
        if not r['completo']: motivi.append('scrutinio incompleto'); continue
        if not r['cand']: continue
        prove.append((tp[0], tp[1], -int(re.search(r'/web/(\d+)', u).group(1)), u, r, tp[2]))
    for _, _, _, u, r, tipo in sorted(prove):
        tot = sum(c['voti'] for c in r['cand'])
        note = []
        if r['intest'] and abs(r['intest']['sindaco'] - tot) > 0.5:
            motivi.append(f"voti dei candidati {tot:.0f} diversi dai voti validi dell'intestazione {r['intest']['sindaco']:.0f}"); continue
        out = []
        sbagliate = False
        for c in r['cand']:
            p = round(c['voti'] * 100 / tot, 2)
            if c['pct'] is not None and abs(p - c['pct']) > 0.02: sbagliate = True
            liste = []
            for nome, voti, pl in c['liste']:
                if tipo == 'Seggi':
                    # percentuali sulle sole liste sopra lo sbarramento: si ricalcolano su tutti i voti di lista
                    if not r['intest']: liste = []; break
                    pl = round(voti * 100 / r['intest']['consiglio'], 2)
                elif r['intest'] and abs(voti * 100 / r['intest']['consiglio'] - pl) > 0.02:
                    note.append(f'percentuale della lista {nome} diversa dal ricalcolo');
                liste.append([nome, pl])
            nome, dubbio = converti_nome(c['nome'], nc)
            if dubbio: note.append(f"nome «{c['nome']}» -> «{nome}» da verificare")
            out.append([nome, p, liste, None, c['eletto']])
        if sbagliate:
            motivi.append('percentuali della pagina diverse dal ricalcolo'); continue
        out.sort(key=lambda c: -c[1])
        eletti = [c for c in out if c[4]]
        if eletti and eletti[0] is not out[0] and not x['ballottaggio']:
            motivi.append('il sindaco eletto non è il primo e non risulta ballottaggio'); continue
        if tipo == 'Seggi' and any(len(c[2]) for c in out): note.append('liste solo sopra lo sbarramento (ReportSeggi)')
        if tipo == 'Candidati': note.append('solo candidati, senza liste (ReportCandidati)')
        return {'comune': x['comune'], 'reg': x['reg'], 'c': [c[:4] for c in out], 'fonte': fonte_wayback(u)}, note
    return None, motivi or ['nessuna pagina conservata dalla Wayback Machine']


# ---------------------------------------------------------------- nomi

def maiuscole(w):
    """«D'ANGELO» -> «D'Angelo», «NICOLO'» -> «Nicolò»."""
    w = re.sub(r"([AEIOUaeiou])'$", lambda m: {'A': 'à', 'E': 'è', 'I': 'ì', 'O': 'ò', 'U': 'ù'}[m.group(1).upper()], w)
    return ''.join(p if p in ("'", '-') else p[:1].upper() + p[1:].lower() for p in re.split(r"(['\-])", w))


def carica_nomi():
    """Nomi propri e cognomi riconosciuti, dai candidati di strumenti/candidati-wikipedia.json («Nome Cognome»)."""
    d = json.load(open(os.path.join(RADICE, 'strumenti', 'candidati-wikipedia.json'), encoding='utf-8'))['elezioni']
    primo, ultimo = collections.Counter(), collections.Counter()
    for v in d.values():
        for c in v['c']:
            t = c[0].upper().split()
            if len(t) >= 2: primo[t[0]] += 1; ultimo[t[-1]] += 1
    nomi = {n for n, k in primo.items() if k > ultimo.get(n, 0)} | NOMI_IN_PIU
    return nomi, {n for n, k in ultimo.items() if k >= primo.get(n, 0)} - nomi


def converti_nome(s, nc):
    """«NICOTRA RAFFAELE GIUSEPPE» -> «Raffaele Giuseppe Nicotra»; «OLIVERI SEBASTIANO detto NELLO» -> «Nello Oliveri»
    (il nome con cui è conosciuto). Cognome: la prima parola (con le particelle Di, Lo, De...) più le seguenti che non sono nomi propri noti,
    se dopo ne viene uno («TOSCANO PECORELLA DANIELA» -> «Daniela Toscano Pecorella»). Restituisce (nome, dubbio)."""
    nomi, cognomi = nc
    s = re.sub(r'\s+', ' ', s.strip()); detto = ''; femm = False
    m = re.match(r'(.*?)\s+(detto|detta)\s+(.*)$', s, re.I)
    if m: s, femm, detto = m.group(1), m.group(2).lower() == 'detta', m.group(3)
    t = s.split(' ')
    if len(t) == 1: return maiuscole(t[0]), True
    U = lambda w: w.upper().rstrip("'")
    i = 0
    while i < len(t) - 1 and U(t[i]) in PARTICELLE: i += 1
    i += 1
    dubbio = False
    while i < len(t) - 1 and U(t[i]) not in nomi and any(U(w) in nomi for w in t[i + 1:]):
        if U(t[i]) not in cognomi: dubbio = True
        i += 1
    if not all(U(w) in nomi for w in t[i:]): dubbio = True
    out = ' '.join(maiuscole(w) for w in t[i:] + t[:i])
    if detto:
        # il nome con cui la persona è conosciuta, come su Wikipedia: «OLIVERI SEBASTIANO detto NELLO» -> «Nello Oliveri»
        d = [w for w in detto.split(' - ')[0].split() if w.upper() not in [y.upper() for y in t[:i]]] or detto.split()
        out = ' '.join(maiuscole(w) for w in d + t[:i])
    return out, dubbio


# ---------------------------------------------------------------- Wikipedia (date dei riquadri corrette) e Archivio elettorale

def da_wikipedia(wiki, elenco):
    """Rilegge con strumenti/candidati_wikipedia.py le pagine regionali con le date dei riquadri corrette."""
    import candidati_wikipedia as cw
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, 'reg'))
        for anno in sorted({a for a, _ in CORREZIONI_DATA}):
            t = open(os.path.join(wiki, 'reg', f'Sicilia_{anno}.txt'), encoding='utf-8').read()
            for (a, comune), data in CORREZIONI_DATA.items():
                if a != anno: continue
                t, n = re.subn(r'(\|comune\s*=\s*' + re.escape(comune) + r'\s*\n(?:\|.*\n)*?\|data\s*=\s*)[^\n]*', lambda m: m.group(1) + data, t, count=1)
                if n != 1: raise SystemExit(f'riquadro di {comune} {anno} non trovato')
            open(os.path.join(tmp, 'reg', f'Sicilia_{anno}.txt'), 'w', encoding='utf-8').write(t)
        trovate, scarti, dubbi = cw.main(tmp)
    voluti = {(a, c) for a, c in CORREZIONI_DATA}
    out = {}
    for k, v in trovate.items():
        if (k[5:9], v['comune']) in voluti and k in elenco:
            note = [f"data del riquadro di Wikipedia corretta in «{CORREZIONI_DATA[(k[5:9], v['comune'])]}»"] + [d for kk, d in dubbi if kk == k]
            out[k] = (v, note)
    return out


def da_archivio_elettorale(chiave, x, idx, nc):
    u, totale_wiki = ARCHIVIO_ELETTORALE[chiave]
    if u not in idx: return None, ['pagina non scaricata']
    t = decodifica(open(os.path.join(cartella_pagine, idx[u]), 'rb').read())
    c = celle(t)
    if norm(x['comune']) not in norm(' '.join(c[:400])): return None, ['comune diverso']
    i = c.index('Candidati Sindaco')
    assert c[i + 1:i + 3] == ['voti validi', 'voti validi in %'], c[i:i + 4]
    cand, j = [], i + 3
    while c[j] != '_Totale':
        cand.append((c[j], numero(c[j + 1]), numero(c[j + 2]))); j += 3
    tot = sum(v for _, v, _ in cand)
    if numero(c[j + 1]) != tot or (totale_wiki and abs(tot - totale_wiki) > 0.002 * tot):
        return None, [f'totale {tot:.0f} diverso dal riquadro di Wikipedia ({totale_wiki})']
    out = []
    for nome, v, p in cand:
        pc = round(v * 100 / tot, 2)
        if abs(pc - p) > 0.02: return None, ['percentuali diverse dal ricalcolo']
        out.append([converti_nome(nome, nc)[0], pc, [], None])
    out.sort(key=lambda c: -c[1])
    riscontro = 'totale uguale al riquadro di Wikipedia' if totale_wiki else 'nessun riscontro con altre fonti'
    return {'comune': x['comune'], 'reg': x['reg'], 'c': out, 'fonte': fonte_wayback(u)}, \
        [f"Archivio elettorale di Roberto Brocchini (fonte non istituzionale: Ministero dell'Interno e stampa), {riscontro}; "
         "senza liste (nel 1993-94 sindaco e consiglio si votavano su schede separate)"]


# ---------------------------------------------------------------- indirizzi da scaricare

def indirizzi(pagine_dir, elenco):
    numeri = dict(NUMERI_DEDOTTI)
    for f in glob.glob(os.path.join(pagine_dir, 'prov', '*.html')):
        for p, n, c in re.findall(r'<option value="Report\w+?([A-Z]{2})(\d+)\.html">([^<]+)', decodifica(open(f, 'rb').read())):
            numeri[(p, norm(html.unescape(c)))] = int(n)
    righe = []
    for f in ('cdx_report.json', 'cdx_pdf.json'):
        righe += json.load(open(os.path.join(pagine_dir, f)))[1:]
    catture = collections.defaultdict(list)
    for t, u, s, g in righe:
        m = re.search(r'sicilia\.it(?::80)?/(.*?)([A-Z]{2})/(PrimoTurno)?Report(Risultati|CandidatiListe|Candidati|Seggi)([A-Z]{2})(\d+)\.(html|pdf)$', u)
        if m: catture[(m.group(2), int(m.group(6)))].append((t, u, m.group(1), m.group(4), bool(m.group(3)), m.group(7)))
    out = []
    for x in elenco.values():
        if x['data'] < '2008': continue
        k = (x['sigla'], numeri.get((x['sigla'], norm(x['comune']))))
        d0 = x['data'].replace('-', '')
        lim = (dt.date.fromisoformat(x['data']) + dt.timedelta(days=330)).strftime('%Y%m%d')
        cc = []
        for t, u, cart, tipo, pt, ext in catture.get(k, []):
            m = re.match(r'comunali(\d{4})/', cart)
            if m:
                if m.group(1) != x['data'][:4]: continue
                pri = 0 if 'primoTurno' in cart or pt else 1
            else:  # radice del sito: l'ultima tornata, catturata dopo il voto e prima della tornata successiva
                if not d0 < t[:8] <= lim: continue
                pri = 2 if 'primoTurno' in cart or pt else 3
            cc.append((ext == 'pdf', TIPI[tipo], pri, -int(t), WAYBACK + t + 'id_/' + u))
        out += [c[-1] for c in sorted(cc)]
    return out


# ---------------------------------------------------------------- main

if __name__ == '__main__':
    if sys.argv[1] == 'urls':
        cartella_pagine = sys.argv[2]
        elenco = {f"{x['cod']}-{x['data']}": x for x in json.load(open(sys.argv[3], encoding='utf-8'))}
        print('\n'.join(indirizzi(cartella_pagine, elenco)))
        sys.exit()
    cartella_pagine, wiki, f_elenco = sys.argv[1:4]
    elenco = {f"{x['cod']}-{x['data']}": x for x in json.load(open(f_elenco, encoding='utf-8')) if x['reg'] == '19'}
    idx = json.load(open(os.path.join(cartella_pagine, 'indice.json')))
    nc = carica_nomi()
    trovate, note, mancate, pagine = {}, [], [], {}
    wikip = da_wikipedia(wiki, elenco)
    for k, x in sorted(elenco.items(), key=lambda kv: (kv[1]['comune'], kv[0])):
        v, n = da_regione(x, pagine, idx, nc)
        if v is None and k in wikip: v, n = wikip[k]
        elif v is None and k in ARCHIVIO_ELETTORALE:
            v2, n2 = da_archivio_elettorale(k, x, idx, nc)
            if v2: v, n = v2, n2
            else: n = n + n2
        if v is None and x['data'] < '2008':
            n = ['prima del 2008: niente sito della Regione, e Wikipedia non ha i risultati (o li ha scartati candidati_wikipedia.py)']
        if v is None:
            mancate.append((k, x['comune'], '; '.join(dict.fromkeys(n)))); continue
        trovate[k] = v
        for d in dict.fromkeys(n): note.append((k, x['comune'], d))
        s = sum(c[1] for c in v['c'] if c[1] is not None)
        if abs(s - 100) > 0.1: note.append((k, x['comune'], f'percentuali dei candidati sommano {s:.2f}'))
    uscita = {
        'descrizione': "Candidati sindaco (percentuale al primo turno sui voti validi ai candidati), liste collegate (percentuale sul "
                       "totale dei voti validi di lista) delle comunali siciliane che mancano all'Archivio del Ministero e a "
                       "strumenti/candidati-wikipedia.json: dal sito elettorale della Regione Siciliana (www.elezioni.regione.sicilia.it, "
                       "copie della Wayback Machine di archive.org, dal 2008), da it.wikipedia.org (tre riquadri con la data "
                       "corretta) e dall'Archivio elettorale di Roberto Brocchini (Belpasso, Cinisi, Corleone e Floridia 1993, Grammichele 1994). Chiave: codice "
                       "catastale-data del primo turno come in dati/comunali.js. Voce: [nome, %, [[lista, %], ...], area]. "
                       "Generato da strumenti/candidati_sicilia.py.",
        'elezioni': dict(sorted(trovate.items(), key=lambda kv: (kv[1]['comune'], kv[0]))),
    }
    righe = [f' {json.dumps(k)}: {json.dumps(v, ensure_ascii=False, separators=(",", ":"))}' for k, v in uscita['elezioni'].items()]
    with open(os.path.join(RADICE, 'strumenti', 'candidati-sicilia.json'), 'w', encoding='utf-8') as f:
        f.write('{\n "descrizione": ' + json.dumps(uscita['descrizione'], ensure_ascii=False) + ',\n "elezioni": {\n' + ',\n'.join(righe) + '\n }\n}\n')
    print(len(trovate), 'elezioni trovate su', len(elenco))
    print(collections.Counter(k[5:9] for k in trovate))
    print('--- note'); [print(' ', *n, sep=' | ') for n in note]
    print('--- non trovate'); [print(' ', *m, sep=' | ') for m in mancate]
