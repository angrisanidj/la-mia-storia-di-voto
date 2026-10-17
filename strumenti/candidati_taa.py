"""Candidati sindaco delle comunali del Trentino-Alto Adige che né l'Archivio del Ministero né it.wikipedia.org
hanno (strumenti/candidati-taa.json), dalle fonti ufficiali della Regione e della Provincia di Bolzano.

Si lancia a mano, con la cartella dei file già scaricati (dal workflow «Sonda» o dalla Wayback Machine):
    python strumenti/candidati_taa.py CARTELLA
Ogni elezione ha in FONTI il tipo di fonte, i file e l'indirizzo da citare:
  - «pdf»: il prospetto dei risultati della Regione (www.regione.taa.it/elezioni/dati/CCCGGMMAAAA.pdf, oggi non più
    in linea: copie della Wayback Machine), letto con «pdftotext -layout». Nella tabella del primo turno ogni lista
    senza candidato appartiene al candidato della riga sopra (le liste di un gruppo sono in ordine di numero: se
    l'ordine si rompe, la lista va al candidato con cui compare al secondo turno, altrimenti si toglie);
  - «g2000», «g2005», «g2010», «g2015» («g2010graf»: la pagina dei grafici, solo percentuali): le pagine dei risultati della Regione sul sito della Provincia di Bolzano
    (www.provinz.bz.it/vote/gem2000, .../gem2005, static.provinz.bz.it/vote/gem2010, .../gem2015: copie della
    Wayback Machine; il sito vivo non si legge, il suo robots.txt esclude /vote/), pagina dei candidati sindaco e,
    se c'è, pagina dei voti di lista (i dati sono quelli provvisori della notte dello spoglio);
  - «civis»: gli open data della Regione su data.civis.bz.it (file CSV su datahub.civis.bz.it: voti ai sindaci,
    voti di lista e collegamenti lista-candidato, per sezione o riassunti per comune);
  - «ectn», «ectn-nc»: il sito dei risultati del Trentino (www.elezionicomunali.tn.it, 2015.elezionicomunali.tn.it,
    www.2020.elezionicomunali.tn.it: copie della Wayback Machine), pagine «Coalizioni» (candidati) e «Liste»; «-nc»
    quando i nomi sono già scritti «NOME COGNOME» (2009-2010).
Percentuali ricalcolate dai voti: candidati sul totale dei voti validi ai candidati, liste sul totale dei voti
validi alle liste (comprese le liste senza candidato); al secondo turno restano le percentuali del primo.
Nei comuni altoatesini fino a 13.000/15.000 abitanti una lista può avere più candidati sindaco (a Lana tutti i
candidati consiglieri): ci sono tutti, e ognuno porta le liste del suo gruppo; strumenti/comunali.py tiene poi
solo chi supera il 2%. Nomi in forma «Nome Cognome» (NOMI corregge le divisioni che la regola sbaglia).
Area: null (la ricava l'app dalle liste).
"""
import csv, html, json, os, re, subprocess, sys, unicodedata
from collections import Counter, defaultdict

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WB = 'https://web.archive.org/web/'
DH = 'https://datahub.civis.bz.it/region-of-trentino-alto-adige-suedtirol/'

COMUNI = {'A332': 'Appiano sulla strada del vino', 'A372': 'Arco', 'B160': 'Bressanone', 'B220': 'Brunico',
          'E421': 'Laives', 'E434': 'Lana', 'F132': 'Merano', 'F728': 'Mori', 'G452': 'Pergine Valsugana',
          'H330': 'Riva del Garda', 'H612': 'Rovereto'}
# nome del comune negli open data della Regione
COMUNI_CIVIS = {'A332': 'APPIANO S.S.D.V.', 'B160': 'BRESSANONE', 'B220': 'BRUNICO', 'E421': 'LAIVES', 'E434': 'LANA', 'F132': 'MERANO'}

R = 'http://www.regione.taa.it:80/elezioni/dati/'
P00 = 'http://www.provincia.bz.it:80/vote/gem2000/'
P05 = 'http://www.provinz.bz.it:80/vote/gem2005/'
S10 = 'https://static.provinz.bz.it/vote/gem2010/'
S15 = 'https://static.provinz.bz.it/vote/gem2015/'
T10 = 'http://www.elezionicomunali.tn.it:80/000053_Com/'
T15 = 'http://2015.elezionicomunali.tn.it/Risultati/'
T20 = 'http://www.2020.elezionicomunali.tn.it/Risultati/'

# chiave (codice catastale-data del primo turno come in dati/comunali.js) -> fonte
FONTI = {
    # Alto Adige
    'A332-2000-05-14': ('g2000', ['A332-2000-05-14.htm'], WB + '20041029070852/' + P00 + 'BZ/comm/comm354.htm'),
    'A332-2010-05-16': ('g2010', ['A332-2010-05-16_sindaci.htm', 'A332-2010-05-16_liste.htm'], WB + '2010/' + S10 + '8423/mayor_ld_vg.htm'),
    'A332-2020-09-20': ('civis', '2020', DH + 'elezioni-comunali-2020/VOTISINDACI.CSV'),
    'A332-2025-05-04': ('civis', '2025', DH + 'elezioni-comunali-2025/VOTISINDACI-SUM.CSV'),
    'B160-2000-05-14': ('g2000', ['B160-2000-05-14.htm'], WB + '20041029070916/' + P00 + 'BZ/comm/comm361.htm'),
    'B160-2005-05-08': ('g2005', ['B160-2005-05-08_sindaci.htm', 'B160-2005-05-08_liste.htm'], WB + '20150127180733/' + P05 + '010/mayor_ld_s0_p0_c0.htm'),
    'B160-2010-05-16': ('g2010', ['B160-2010-05-16_sindaci.htm', 'B160-2010-05-16_liste.htm'], WB + '2010/' + S10 + '8429/mayor_ld_vg.htm'),
    'B160-2015-05-10': ('g2015', ['B160-2015-05-10_sindaci.htm'], WB + '2015/' + S15 + '17511/mayor_li_vg.htm'),
    'B160-2020-09-20': ('civis', '2020', DH + 'elezioni-comunali-2020/VOTISINDACI.CSV'),
    'B220-2000-05-14': ('g2000', ['B220-2000-05-14.htm'], WB + '20041029070920/' + P00 + 'BZ/comm/comm363.htm'),
    'B220-2005-05-08': ('g2005', ['B220-2005-05-08_sindaci.htm'], WB + '20130227014600/' + P05 + '012/mayor_ld_s0_p0_c0.htm'),
    'B220-2010-05-16': ('g2010', ['B220-2010-05-16_sindaci.htm', 'B220-2010-05-16_liste.htm'], WB + '2010/' + S10 + '8434/mayor_ld_vg.htm'),
    'B220-2020-09-20': ('civis', '2020', DH + 'elezioni-comunali-2020/VOTISINDACI.CSV'),
    'E421-1999-05-16': ('pdf', ['E421-1999-05-16.pdf'], WB + '20150319034304/' + R + '39016051999.pdf'),
    'E421-2005-05-29': ('pdf', ['E421-2005-05-29.pdf'], WB + '20150405145525/' + R + '39008052005.pdf'),
    'E421-2010-05-16': ('pdf', ['E421-2010-05-16.pdf'], WB + '20141006085904/http://www.regione.taa.it/elezioni/dati/39016052010.pdf'),
    'E421-2020-09-20': ('civis', '2020', DH + 'elezioni-comunali-2020/VOTISINDACI.CSV'),
    'E421-2024-05-26': ('civis', '2024', DH + 'elezioni-comunali-2024/2024-05_06_extra/VOTISINDACI-SUM.CSV'),
    'E434-2000-05-14': ('g2000', ['E434-2000-05-14.htm'], WB + '20041029071105/' + P00 + 'BZ/comm/comm391.htm'),
    'E434-2010-05-16': ('g2010', ['E434-2010-05-16_sindaci.htm', 'E434-2010-05-16_liste.htm'], WB + '2010/' + S10 + '8460/mayor_ld_vg.htm'),
    'E434-2020-09-20': ('civis', '2020', DH + 'elezioni-comunali-2020/VOTISINDACI.CSV'),
    'E434-2024-05-26': ('civis', '2024', DH + 'elezioni-comunali-2024/2024-05_06_extra/VOTISINDACI-SUM.CSV'),
    'F132-2000-05-14': ('g2000', ['F132-2000-05-14.htm'], WB + '20041029071245/' + P00 + 'BZ/comm/comm402.htm'),
    'F132-2005-05-08': ('pdf', ['F132-2005-05-08.pdf'], WB + '20100601110938/' + R + '40208052005.pdf'),
    'F132-2010-05-16': ('g2010graf', ['F132-2010-05-16_grafici.htm'], WB + '2010/' + S10 + '8470/graph_ld_vg.htm'),
    'F132-2015-05-10': ('pdf', ['F132-2015-05-10.pdf'], WB + '20190921182231/http://www.regione.taa.it/elezioni/dati/40210052015.pdf'),
    'F132-2020-09-20': ('civis', '2020', DH + 'elezioni-comunali-2020/VOTISINDACI.CSV'),
    'F132-2021-10-10': ('civis', '2021', DH + 'elezioni-comunali-2021/VOTISINDACI-SUM.CSV'),
    # Trentino
    'A372-2005-05-08': ('pdf', ['A372-2005-05-08.pdf'], WB + '20100601210817/' + R + '00608052005.pdf'),
    'F728-2000-05-14': ('g2000', ['F728-2000-05-14.htm'], WB + '20041029223045/http://www.provinz.bz.it:80/vote/gem2000/TN/comm/comm121.htm'),
    'F728-2004-05-09': ('pdf', ['F728-2004-05-09.pdf'], WB + '20100601211958/' + R + '12109052004.pdf'),
    'G452-2000-05-14': ('g2000', ['G452-2000-05-14.htm'], WB + '20041029223145/http://www.provinz.bz.it:80/vote/gem2000/TN/comm/comm137.htm'),
    'H330-2003-05-18': ('pdf', ['H330-2003-05-18.pdf'], WB + '20030731004135/http://www.regione.trentino-a-adige.it:80/giunta/elezioni_it/comunali_2003/dati/Riva.pdf'),
    'A372-2010-05-16': ('ectn-nc', ['A372-2010-05-16_coalizioni.htm', 'A372-2010-05-16_liste.htm'], WB + '20100519151328/' + T10 + 'Coalizioni/000020.html'),
    'A372-2020-09-20': ('ectn', ['A372-2020-09-20_coalizioni.htm', 'A372-2020-09-20_liste.htm'], WB + '20200924031752/' + T20 + 'Coalizioni/000020.html'),
    'F728-2010-05-16': ('ectn-nc', ['F728-2010-05-16_coalizioni.htm', 'F728-2010-05-16_liste.htm'], WB + '20100520062844/' + T10.replace('www.', 'www3.') + 'Coalizioni/000134.html'),
    'F728-2015-05-10': ('ectn', ['F728-2015-05-10_coalizioni.htm', 'F728-2015-05-10_liste.htm'], WB + '20240805000912/' + T15 + 'Coalizioni/000134.html'),
    'F728-2020-09-20': ('ectn', ['F728-2020-09-20_coalizioni.htm', 'F728-2020-09-20_liste.htm'], WB + '20200924024820/' + T20 + 'Coalizioni/000134.html'),
    'G452-2009-05-03': ('ectn-nc', ['G452-2009-05-03_coalizioni.htm', 'G452-2009-05-03_liste.htm'], WB + '20090508071116/http://www.elezionicomunali.tn.it:80/000025_Com/Coalizioni/000150.html'),
    'G452-2015-05-10': ('ectn', ['G452-2015-05-10_coalizioni.htm', 'G452-2015-05-10_liste.htm'], WB + '20240815160617/' + T15 + 'Coalizioni/000150.html'),
    'G452-2020-09-20': ('ectn', ['G452-2020-09-20_coalizioni.htm', 'G452-2020-09-20_liste.htm'], WB + '20200924032628/' + T20 + 'Coalizioni/000150.html'),
    'H330-2010-05-16': ('ectn-nc', ['H330-2010-05-16_coalizioni.htm', 'H330-2010-05-16_liste.htm'], WB + '20100521163847/' + T10.replace('www.', 'www3.') + 'Coalizioni/000164.html'),
    'H330-2015-05-10': ('ectn', ['H330-2015-05-10_coalizioni.htm', 'H330-2015-05-10_liste.htm'], WB + '20240814111711/' + T15 + 'Coalizioni/000164.html'),
    'H330-2020-09-20': ('ectn', ['H330-2020-09-20_coalizioni.htm', 'H330-2020-09-20_liste.htm'], WB + '20200924035243/' + T20 + 'Coalizioni/000164.html'),
    'H612-2010-05-16': ('ectn-nc', ['H612-2010-05-16_coalizioni.htm', 'H612-2010-05-16_liste.htm'], WB + '20100520024430/' + T10 + 'Coalizioni/000172.html'),
    'H612-2015-05-10': ('ectn', ['H612-2015-05-10_coalizioni.htm', 'H612-2015-05-10_liste.htm'], WB + '20240812034534/' + T15 + 'Coalizioni/000172.html'),
    'H612-2020-09-20': ('ectn', ['H612-2020-09-20_coalizioni.htm', 'H612-2020-09-20_liste.htm'], WB + '20200924031943/' + T20 + 'Coalizioni/000172.html'),
    'H612-2005-05-08': ('pdf', ['H612-2005-05-08.pdf'], WB + '20100601110806/' + R + '16008052005.pdf'),
}

# Divisioni nome/cognome che la regola non indovina: forma della fonte (cognome nome) -> «Nome Cognome»
NOMI = {
    'Staffler Gunter Paul': 'Gunter Paul Staffler',
    'Schwienbacher Susanna Renate Marlene': 'Susanna Renate Marlene Schwienbacher',
    'Schwienbacher - Felder Magdalena': 'Magdalena Schwienbacher-Felder',
    'Gasser - Abler Maria Luigia': 'Maria Luigia Gasser-Abler',
    'von MARSONER EGON KARL MARIA': 'Egon Karl Maria von Marsoner',
}

PARTICELLE = {'de', 'di', 'da', 'dal', 'dalla', 'dalle', 'del', 'della', 'dello', 'dei', 'degli', 'von', 'van', 'lo', 'la', 'le', 'dall', "dell'", "d'"}


def norm(s):
    s = unicodedata.normalize('NFD', s.lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()


def maiuscole(s):
    """«PÜRGSTALLER ALBERT» -> «Pürgstaller Albert», con apostrofi e trattini."""
    def parola(w):
        if not w: return w
        return '-'.join("'".join(p[:1].upper() + p[1:].lower() for p in x.split("'")) for x in w.split('-'))
    return ' '.join(parola(w) for w in s.split())


NOMI_PROPRI = set()


def carica_nomi_propri():
    """I nomi di battesimo noti: dai candidati di candidati-wikipedia.json (forma «Nome Cognome») e da un elenco fisso."""
    base = ('albert alberto alessandro alexander alfred alois andrea andreas angelika anna antonio armin arnold barbara benedetto '
            'bernhard bruno carlo carmelo christian christine christoph claudia claudio cristina daniela dario david diego '
            'dietmar elena elisabeth emil enzo erich ernst eugenio fabio fabrizio felix florian francesco franco frank franz '
            'gabriele georg gerhard gianni giorgio giovanni giulia giuseppe gottfried gunther günther hans harald heinrich '
            'helmut herbert hermann hubert ingo irene johann johanna josef jürgen karl katharina klaus konrad kurt laura '
            'leonardo liliana lorenzo luca luigi manfred marco maria mario markus martin mauro maximilian michael michele '
            'monika nerio oskar othmar paolo paul peter philipp pietro raimondo reinhard reinhold renate renato renzo '
            'richard rita roberto roland rudolf ruggero sandro sergio sigmar simone sonja stefan stefano sven thomas ulrike '
            'valentina vanda verena viliam walter werner wilfried wolfgang loris leonardo pier giorgio gloria rocco enzo '
            'birgitta birgit eva mario gianlorenzo dario massimo pius hans gottfried luca sergio cristiana remo norbert '
            'regina helene helga erika edeltraud gertraud gertrud theresia romana christine hartmann heinz').split()
    NOMI_PROPRI.update(base)
    try:
        with open(os.path.join(RADICE, 'strumenti', 'candidati-wikipedia.json'), encoding='utf-8') as f:
            for v in json.load(f)['elezioni'].values():
                for c in v['c']:
                    if c[0] and ' ' in c[0]:
                        NOMI_PROPRI.add(norm(c[0].split()[0]))
    except OSError:
        pass


def nome_cognome(grezzo):
    """«COGNOME NOME [ALTRI NOMI] (detto)» -> «Nome Cognome»: il nome comincia dalla prima parola, dopo il
    cognome, che è un nome di battesimo noto; se nessuna lo è, è l'ultima parola."""
    s = re.sub(r'\s*\([^)]*\)', '', grezzo).strip()
    s = re.sub(r'\s+', ' ', s)
    if s in NOMI: return NOMI[s]
    t = maiuscole(s) if s.isupper() or any(w.isupper() and len(w) > 2 for w in s.split()) else s
    if t in NOMI: return NOMI[t]
    w = t.split()
    if len(w) == 1: return t
    i = 1
    while i < len(w) - 1 and norm(w[i - 1]) in PARTICELLE:
        i += 1  # «De Martin», «von Wohlgemuth»: la particella va col cognome
    k = next((j for j in range(i, len(w)) if norm(w[j]) in NOMI_PROPRI), len(w) - 1)
    cognome = [x.lower() if norm(x) in PARTICELLE and x.lower() in ('von', 'van') else x for x in w[:k]]
    return ' '.join(w[k:] + cognome)


def pct(v, tot):
    return round(100 * v / tot, 2) if tot else None


# --- lettori -------------------------------------------------------------------------------------------------------

def testo_html(b):
    try: t = b.decode('utf-8')
    except UnicodeDecodeError: t = b.decode('latin-1')
    t = re.sub(r'<(script|style).*?</\1>', '', t, flags=re.S | re.I)
    return t


def celle(riga):
    out = []
    for c in re.findall(r'<td[^>]*>(.*?)</td>', riga, re.S | re.I):
        out.append(c)
    return out


def pulito(c):
    c = re.sub(r'<br\s*/?>', '\n', c, flags=re.I)
    c = re.sub(r'<[^>]+>', ' ', c)
    return html.unescape(c).replace('\xa0', ' ')


def numero(s):
    s = s.strip().replace('.', '')
    return int(s) if re.fullmatch(r'\d+', s) else None


def leggi_g2000(cartella, files):
    """Pagina di un comune del sito 2000: tabella dei candidati sindaco (nome, liste collegate separate da virgole,
    voti, %) e tabella dei voti di lista."""
    t = testo_html(open(os.path.join(cartella, files[0]), 'rb').read())
    cand, liste = [], {}
    for riga in re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.S | re.I):
        cc = celle(riga)
        if len(cc) < 4: continue
        if '<strong>' in cc[1].lower() and 'lists/' not in cc[1]:
            m = re.search(r'<strong>(.*?)</strong>(.*)', cc[1], re.S | re.I)
            if not m: continue
            nome = re.sub(r'\s+', ' ', pulito(m.group(1))).strip()
            ll = re.sub(r'\s+', ' ', pulito(m.group(2))).strip()
            v = numero(pulito(cc[2]))
            if v is None or not nome: continue
            cand.append({'nome': nome, 'voti': v, 'liste_txt': ll})
        elif 'lists/' in cc[1]:
            n = re.sub(r'\s+', ' ', pulito(cc[1])).strip()
            n = re.sub(r'\s*\((Compreso|Lista di riferimento)[^)]*\)', '', n).strip()
            v = numero(pulito(cc[2]))
            if v is not None: liste[n] = v
    # liste collegate: i nomi della tabella delle liste che compaiono nel testo del candidato
    nomi_l = sorted(liste, key=len, reverse=True)
    for c in cand:
        resto, trovate = ', ' + c['liste_txt'] + ',', []
        for n in nomi_l:
            if ', ' + n + ',' in resto:
                trovate.append(n); resto = resto.replace(', ' + n + ',', ',', 1)
        if resto.strip(', '):
            raise ValueError(f"liste non riconosciute: {resto!r} in {files[0]}")
        c['liste'] = sorted(trovate, key=lambda n: -liste[n])
    return cand, liste


def righe_th(t):
    """Le righe <tr> con l'intestazione <th scope="row">: (testo prima del <br>, voci <li>, celle <td>)."""
    out = []
    for riga in re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.S | re.I):
        m = re.search(r'<th[^>]*scope="row"[^>]*>(.*?)</th>', riga, re.S | re.I)
        if not m: continue
        th = m.group(1)
        testa = re.sub(r'\s+', ' ', pulito(re.split(r'<br\s*/?>|<span|<ul', th, flags=re.I)[0])).strip()
        li = [re.sub(r'\s+', ' ', pulito(x)).strip() for x in re.findall(r'<li[^>]*>(.*?)</li>', th, re.S | re.I)]
        td = [re.sub(r'\s+', ' ', pulito(x)).strip() for x in re.findall(r'<td[^>]*>(.*?)</td>', riga[m.end():], re.S | re.I)]
        out.append((testa, li, td))
    return out


def leggi_g2005(cartella, files):
    """Sito 2005: righe «N. Cognome Nome» con le liste collegate in elenco, voti e %; voti di lista dall'altra pagina."""
    t = testo_html(open(os.path.join(cartella, files[0]), 'rb').read())
    liste = {}
    if len(files) > 1:
        for testa, li, td in righe_th(testo_html(open(os.path.join(cartella, files[1]), 'rb').read())):
            v = numero(td[0]) if td else None
            if v is not None: liste[re.sub(r'^\d+\.\s*', '', testa)] = v
    cand = []
    for testa, li, td in righe_th(t):
        v = numero(td[0]) if td else None
        if v is None or not re.match(r'\d+\.', testa): continue
        nome = re.sub(r'^\d+\.\s*', '', testa)
        nome = re.sub(r'\s+(Bürgermeister|Gemeinderat|Sindaco|Consigliere)$', '', nome)  # eletto come
        cand.append({'nome': nome, 'voti': v, 'liste': li})
    return cand, controlla_liste(cand, liste, files[0])


def controlla_liste(cand, liste, nomefile):
    """Le liste dei candidati devono essere nella tabella delle liste (se c'è); in ordine di voti."""
    if not liste:
        for c in cand: c['liste'] = []  # senza voti di lista: candidati senza liste
        return {}
    for c in cand:
        for l in c['liste']:
            if l not in liste: raise ValueError(f'lista {l!r} non nella tabella delle liste in {nomefile}')
        c['liste'] = sorted(c['liste'], key=lambda n: -liste[n])
    return liste


def leggi_g2010(cartella, files):
    """Sito 2010: righe «COGNOME NOME» con le liste collegate in elenco, eletto come, voti, %; voti di lista dalla
    prima tabella dell'altra pagina (la seconda è il 2005)."""
    t = testo_html(open(os.path.join(cartella, files[0]), 'rb').read())
    liste = {}
    if len(files) > 1:
        tl = testo_html(open(os.path.join(cartella, files[1]), 'rb').read())
        tab = re.findall(r'<tbody>(.*?)</tbody>', tl, re.S | re.I)
        for riga in re.findall(r'<tr[^>]*>(.*?)</tr>', tab[0] if tab else '', re.S | re.I):
            n = re.search(r'class="list-name"[^>]*>\s*<strong>(.*?)</strong>', riga, re.S | re.I)
            v = re.search(r'class="list-votes"[^>]*>(.*?)</td>', riga, re.S | re.I)
            if n and v: liste[re.sub(r'\s+', ' ', pulito(n.group(1))).strip()] = numero(pulito(v.group(1)))
    cand = []
    for testa, li, td in righe_th(t):
        v = next((numero(x) for x in td if numero(x) is not None), None)  # «eletto come» c'è solo nei comuni piccoli
        if v is None or not li: continue  # le righe senza liste sono i dati sul voto (schede valide...)
        cand.append({'nome': testa, 'voti': v, 'liste': li})
    return cand, controlla_liste(cand, liste, files[0])


def leggi_g2015(cartella, files):
    """Sito 2015: righe «COGNOME NOME» con i simboli delle liste collegate (titolo dell'immagine), voti in grassetto.
    La pagina dei voti di lista non c'è: candidati senza liste."""
    t = testo_html(open(os.path.join(cartella, files[0]), 'rb').read())
    cand = []
    for riga in re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.S | re.I):
        m = re.search(r'<th[^>]*scope="row"[^>]*>(.*?)</th>', riga, re.S | re.I)
        v = re.search(r'class="votes_now"[^>]*>\s*<strong>([\d.]+)</strong>', riga)
        if not m or not v: continue
        nome = re.sub(r'\s+', ' ', pulito(re.split(r'<br', m.group(1))[0])).strip()
        cand.append({'nome': nome, 'voti': numero(v.group(1)),
                     'liste': [html.unescape(x) for x in re.findall(r'title="([^"]+)"', m.group(1))]})
    return cand, controlla_liste(cand, {}, files[0])


def leggi_g2010_grafici(cartella, files):
    """Sito 2010, pagina dei grafici (quando quella dei candidati non è nella Wayback Machine): solo le percentuali
    dei candidati, con un decimale."""
    t = testo_html(open(os.path.join(cartella, files[0]), 'rb').read())
    tab = re.findall(r'<tbody>(.*?)</tbody>', t, re.S | re.I)
    cand = []
    for testa, li, td in righe_th(tab[0]):
        p = re.match(r'(\d+),(\d)%', td[0]) if td else None
        if p: cand.append({'nome': testa, 'pct': float(p.group(1) + '.' + p.group(2)), 'liste': []})
    return cand, {}


def leggi_ectn(cartella, files):
    """Sito dei risultati del Trentino (www.elezionicomunali.tn.it, poi 2015./www.2020.elezionicomunali.tn.it):
    pagina «Coalizioni» (candidati sindaco, voti, simboli delle liste collegate) e pagina «Liste» (voti di lista);
    le liste di un candidato si riconoscono dal numero del simbolo (sim_NNNN)."""
    tc = testo_html(open(os.path.join(cartella, files[0]), 'rb').read())
    tl = testo_html(open(os.path.join(cartella, files[1]), 'rb').read())
    m = re.search(r'precedent', tl, re.I)
    if m and 'sim_' in tl[:m.start()]:
        tl = tl[:m.start()]  # dopo c'è la tabella delle elezioni precedenti
    liste, nomi_sim = {}, {}
    for riga in re.findall(r'<tr[^>]*>(.*?)</tr>', tl, re.S | re.I):
        m = re.search(r'sim_(\d+)\.', riga)
        td = re.findall(r'<td[^>]*>(.*?)</td>', riga, re.S | re.I)
        if not m or len(td) < 2: continue
        i = next((k for k, x in enumerate(td) if '<strong>' in x), None)  # 2015-2020: nome in grassetto
        tdc = re.findall(r'<td([^>]*)>', riga, re.I)
        if i is None: i = next((k for k, x in enumerate(tdc) if 'class="nome"' in x), None)  # 2009
        if i is None: i = next(k for k, x in enumerate(td) if 'sim_' in x)  # 2010: nome dopo il simbolo
        n = re.search(r'<strong>(.*?)</strong>', td[i], re.S)
        n = n.group(1) if n else re.split(r'<br|<a ', td[i])[0]
        n = re.sub(r'\s+', ' ', pulito(n)).strip()
        alt = re.search(r'sim_\d+\.gif"\s+alt="([^"]+)"', riga)
        if 'class="nome"' in ''.join(tdc) and alt: n = html.unescape(alt.group(1)).strip()  # 2009: il nome intero è nel simbolo
        v = next((numero(pulito(x)) for x in td[i + 1:] if numero(pulito(x)) is not None), None)
        if v is None or not n: continue
        liste[n] = v; nomi_sim[m.group(1)] = n
    cand = []
    blocchi = re.findall(r'<tr[^>]*>(.*?)</tr>', tc, re.S | re.I)
    if 'contenutocandidati' in tc:  # 2009: un blocco <div> per candidato
        blocchi = [re.sub(r'<strong>(.*?)</strong>', r'<td>\1</td>', b).replace('<b>', 'Voti: <strong>').replace('</b>', '</strong>')
                   for b in tc.split('class="contenutocandidati"')[1:]]
    for riga in blocchi:
        v = re.search(r'Voti:\s*<strong>([\d.]+)</strong>|class="votes_now"[^>]*>\s*<strong>([\d.]+)</strong>', riga)
        if not v: continue
        th = re.search(r'<th[^>]*scope="row"[^>]*>(.*?)<br', riga, re.S | re.I)
        nome = th.group(1) if th else re.search(r'<td[^>]*>(.*?)</td>', riga, re.S).group(1)
        sims = re.findall(r'sim_(\d+)\.', riga)
        for x in sims:
            if x not in nomi_sim: raise ValueError(f'simbolo {x} senza lista in {files[1]}')
        cand.append({'nome': re.sub(r'\s+', ' ', pulito(nome)).strip(), 'voti': numero(v.group(1) or v.group(2)),
                     'liste': sorted({nomi_sim[x] for x in sims}, key=lambda n: -liste[n])})
    return cand, liste


# --- prospetti PDF della Regione ------------------------------------------------------------------------------------
NUM = re.compile(r'^\d{1,3}(?:\.\d{3})*$|^\d+$')
PCT = re.compile(r'^\d{1,3},\d{2}$')


def testo_pdf(percorso):
    return subprocess.run(['pdftotext', '-layout', percorso, '-'], capture_output=True, text=True, check=True).stdout


def coda_numeri(riga):
    """Separa la parte di testo dai numeri finali (voti, percentuali, seggi, «-»)."""
    tok = list(re.finditer(r'\S+', riga))
    i = len(tok)
    while i > 0 and (NUM.match(tok[i - 1].group()) or PCT.match(tok[i - 1].group()) or tok[i - 1].group() == '-'):
        i -= 1
    while i < len(tok) and tok[i].group() == '-':  # un trattino in testa è della descrizione
        i += 1
    fine_testo = tok[i - 1].end() if i > 0 else 0
    return riga[:fine_testo], [t.group() for t in tok[i:]]


def tabella_primo_turno(t):
    righe = t.split('\n')
    # inizio: la riga d'intestazione con «Descrizione del contrassegno»; fine: «Partecipano al ballottaggio», «Collegamento», «Eletto», riga vuota doppia
    i0 = next(i for i, r in enumerate(righe) if 'Descrizione del contrassegno' in r)
    intest = righe[i0]
    m = re.search(r'Candidat[oi] sindaco', intest)
    col_cand = m.start()
    out, i = [], i0 + 1
    while i < len(righe):
        r = righe[i]
        if re.match(r'\s*(\* Collegamento|Partecipano|Eletto|II\.|II°)', r) or 'TURNO' in r:
            break
        i += 1
        if not r.strip() or re.match(r'\s*(lista|Liste|Voti|dati|anzahl|candi-)', r.strip()) or 'Kandidaten' in r or 'Bürgermeisters' in r or re.match(r'^\s*(Liste Nr|lista candi)', r):
            continue
        m = re.match(r'\s*(\d+)\s+(\d+)\s+(\*\(\d+\)\s*)?', r)
        testo, num = coda_numeri(r)
        if m and len(num) >= 2:
            pcts = [x for x in num if PCT.match(x)]
            gruppo = m.group(3).strip() if m.group(3) else None
            corpo = testo[m.end():] if len(testo) > m.end() else ''
            # descrizione e candidato separati dalla colonna del candidato
            off = m.end()
            desc = testo[off:col_cand].strip() if len(testo) > off else ''
            cand = testo[col_cand:].strip() if len(testo) > col_cand else ''
            if desc and not cand:
                # la descrizione può sforare nella colonna del candidato: separa con due spazi
                parti = re.split(r'\s{2,}', corpo.strip())
                desc = parti[0]; cand = ' '.join(parti[1:])
            elif desc and testo[col_cand - 1:col_cand] not in (' ', ''):
                parti = re.split(r'\s{2,}', corpo.strip())
                desc = parti[0]; cand = ' '.join(parti[1:])
            voce = {'n': int(m.group(1)), 'desc': desc, 'cand': cand, 'gruppo': gruppo}
            if len(pcts) >= 2:
                voce['vc'] = int(num[0].replace('.', '')); voce['vl'] = int(num[2].replace('.', ''))
            else:
                voce['vc'] = None; voce['vl'] = int(num[0].replace('.', ''))
            out.append(voce)
        elif out:
            # riga di continuazione: descrizione o nome del candidato che va a capo
            sx = r[:col_cand].strip(); dx = r[col_cand:].strip()
            if sx: out[-1]['desc'] += ' ' + sx
            if dx: out[-1]['cand'] += ' ' + dx
    return out


def secondo_turno(t):
    """Liste per candidato al secondo turno: {numero lista: candidato o None se non collegata}."""
    righe = t.split('\n')
    idx = [i for i, r in enumerate(righe) if 'Descrizione del contrassegno' in r or 'Liste collegate ai candidati' in r]
    if len(idx) < 2:
        return {}
    out, cur, i = {}, None, idx[1] + 1
    iniziato = False
    bz = 'Liste collegate ai candidati' in righe[idx[1]]
    while i < len(righe):
        r = righe[i]; i += 1
        if re.match(r'\s*(Eletto|Gewählter|N\. Progr|Lfd)', r):
            break
        m2 = re.match(r'\s*(\d+)\s+', r)
        if not m2:
            continue
        testo, num = coda_numeri(r)
        if len(num) < 2 and not (bz and not num):
            if iniziato: break
            continue
        iniziato = True
        parti = re.split(r'\s{2,}', testo.strip())
        parti = [x for x in parti if not re.fullmatch(r'\d+', x)]
        if len(parti) >= 2:
            c = parti[-1]
            if 'non collegata' in c:
                out[int(m2.group(1))] = None; continue
            cur = c
        out[int(m2.group(1))] = cur
    return out


def leggi_pdf(cartella, files, note):
    t = testo_pdf(os.path.join(cartella, files[0]))
    righe = tabella_primo_turno(t)
    sec = secondo_turno(t)
    cand, liste, cur = [], {}, None
    nomi_ball = {norm(c) for c in sec.values() if c}
    for r in righe:
        desc = re.sub(r'\s+', ' ', r['desc']).strip()
        liste[desc] = r['vl']
        if r['vc'] is not None:
            cur = {'nome': re.sub(r'\s+', ' ', r['cand']).strip(), 'voti': r['vc'], 'liste': [desc], 'n': [r['n']]}
            cand.append(cur)
        else:
            if cur is None: continue
            if r['n'] < cur['n'][-1]:
                # ordine rotto: la lista non segue il gruppo della riga sopra; al secondo turno con chi è?
                dove = sec.get(r['n'])
                altro = next((c for c in cand if dove and norm(c['nome']) == norm(dove)), None)
                if altro is not None and norm(cur['nome']) in nomi_ball and altro is not cur:
                    altro['liste'].append(desc); altro['n'].append(r['n'])
                    note.append(f"lista «{desc}» fuori ordine: assegnata a {altro['nome']} (secondo turno)")
                else:
                    note.append(f"lista «{desc}» fuori ordine e senza riscontro: tolta dai candidati")
                continue
            cur['liste'].append(desc); cur['n'].append(r['n'])
    for c in cand:
        c['liste'] = sorted(c['liste'], key=lambda n: -liste[n])
        c.pop('n')
    return cand, liste


def csv_righe(cartella, nome):
    with open(os.path.join(cartella, nome), encoding='utf-8-sig') as f:
        return list(csv.DictReader(f, delimiter=';'))


_CSV = {}


def leggi_civis(cartella, anno, cod):
    """Open data della Regione: voti ai sindaci, voti di lista e voti di lista con il candidato collegato (per sezione o già sommati)."""
    suf = '' if anno == '2020' else '-SUM'
    if anno not in _CSV:
        _CSV[anno] = (csv_righe(cartella, f'{anno}_VOTISINDACI{suf}.csv'), csv_righe(cartella, f'{anno}_VOTILISTE{suf}.csv'),
                      csv_righe(cartella, f'{anno}_VOTILISTESINDACI{suf}.csv'))
    vs, vl, vls = _CSV[anno]
    com = COMUNI_CIVIS[cod]
    voti_c, voti_l = Counter(), Counter()
    for x in vs:
        if x['DESCRIZIONEISTAT_I'].strip() == com and 'Primo' in x['DESCRIZIONE']:
            voti_c[x['NOMINATIVO'].strip()] += int(x['VOTI_SINDACO'])
    for x in vl:
        if x['DESCRIZIONEISTAT_I'].strip() == com and 'Primo' in x['DESCRIZIONE']:
            voti_l[x['DESCRIZIONELISTA'].strip()] += int(x['VOTILISTA'])
    gruppo = defaultdict(set)  # candidato -> liste collegate (nei comuni piccoli una lista può non avere candidato)
    for x in vls:
        if x['DESCRIZIONEISTAT_I'].strip() == com and 'Primo' in x['DESCRIZIONE'] and (x['NOMINATIVO'] or '').strip():
            gruppo[x['NOMINATIVO'].strip()].add(x['DESCRIZIONELISTA'].strip())
    cand = []
    for n, v in voti_c.items():
        ll = gruppo.get(n)
        if ll is None:
            raise ValueError(f'{com} {anno}: candidato {n} senza liste collegate')
        cand.append({'nome': n, 'voti': v, 'liste': sorted(set(ll), key=lambda l: -voti_l[l])})
    for c in cand:
        for l in c['liste']:
            if l not in voti_l:
                raise ValueError(f'{com} {anno}: lista {l!r} senza voti')
    return cand, dict(voti_l)


# --- costruzione -----------------------------------------------------------------------------------------------------

def costruisci(chiave, fonte, cartella):
    tipo, files, url = fonte
    note = []
    if tipo == 'g2000': cand, liste = leggi_g2000(cartella, files)
    elif tipo == 'g2005': cand, liste = leggi_g2005(cartella, files)
    elif tipo == 'g2010': cand, liste = leggi_g2010(cartella, files)
    elif tipo == 'pdf': cand, liste = leggi_pdf(cartella, files, note)
    elif tipo == 'civis': cand, liste = leggi_civis(cartella, files, chiave[:4])
    elif tipo == 'g2015': cand, liste = leggi_g2015(cartella, files)
    elif tipo == 'g2010graf': cand, liste = leggi_g2010_grafici(cartella, files)
    elif tipo in ('ectn', 'ectn-nc'): cand, liste = leggi_ectn(cartella, files)
    else: raise ValueError(tipo)
    for c in cand:
        if 'voti' not in c: c['voti'] = c['pct']  # solo percentuali (pagina dei grafici)
    tot_c = 100 if tipo == 'g2010graf' else sum(c['voti'] for c in cand)
    tot_l = sum(liste.values())
    cand.sort(key=lambda c: -c['voti'])
    voci = []
    for c in cand:
        ll = [[re.sub(r'\s+', ' ', l), pct(liste[l], tot_l)] for l in c['liste'] if l in liste and liste[l] is not None]
        nome = maiuscole(c['nome']) if tipo == 'ectn-nc' else nome_cognome(c['nome'])
        voci.append([nome, c['voti'] if tipo == 'g2010graf' else pct(c['voti'], tot_c), ll, None])
    return {'comune': COMUNI[chiave[:4]], 'reg': '04', 'c': voci, 'fonte': url}, note, cand


def date_comunali():
    """Le tornate di dati/comunali.js: codice catastale -> insieme delle date (per controllare le chiavi)."""
    t = open(os.path.join(RADICE, 'dati', 'comunali.js'), encoding='utf-8').read()
    date = json.loads(re.search(r'COMUNALI_DATE = (\[.*?\]);', t, re.S).group(1))
    out = {}
    for cod, idx in re.findall(r'\b([A-Z]\d{3}):(-?\d+(?:,-?\d+)*)', t):
        out[cod] = {date[abs(int(i)) - 1] for i in idx.split(',')}
    return out


def main(cartella):
    carica_nomi_propri()
    trovate, note = {}, []
    tornate = date_comunali()
    for chiave, fonte in FONTI.items():
        if chiave[5:] not in tornate.get(chiave[:4], ()):
            raise ValueError(f'{chiave}: data non in dati/comunali.js')
        voce, n, cand = costruisci(chiave, fonte, cartella)
        s = sum(c[1] for c in voce['c'])
        if abs(s - 100) > 0.1:
            n.append(f'somma delle percentuali {s:.2f}')
        trovate[chiave] = voce
        for x in n: note.append((chiave, x))
    return trovate, note


if __name__ == '__main__':
    cartella = sys.argv[1] if len(sys.argv) > 1 else '.'
    trovate, note = main(cartella)
    uscita = {
        'descrizione': "Candidati sindaco (percentuale al primo turno) e liste collegate (percentuale sul totale dei voti di lista) delle comunali "
                       "del Trentino-Alto Adige che mancano all'Archivio del Ministero e a it.wikipedia.org, dalle fonti della Regione: "
                       "prospetti dei risultati (www.regione.taa.it/elezioni/dati), pagine dei risultati sul sito della Provincia di Bolzano "
                       "(provinz.bz.it/vote), sito dei risultati del Trentino (elezionicomunali.tn.it) e open data (data.civis.bz.it), "
                       "anche da copie della Wayback Machine. Chiave: codice catastale-data "
                       "del primo turno come in dati/comunali.js. Voce: [nome, %, [[lista, %], ...], area]. Generato da strumenti/candidati_taa.py.",
        'elezioni': dict(sorted(trovate.items(), key=lambda kv: (kv[1]['comune'], kv[0]))),
    }
    righe = [f' {json.dumps(k)}: {json.dumps(v, ensure_ascii=False, separators=(",", ":"))}' for k, v in uscita['elezioni'].items()]
    with open(os.path.join(RADICE, 'strumenti', 'candidati-taa.json'), 'w', encoding='utf-8') as f:
        f.write('{\n "descrizione": ' + json.dumps(uscita['descrizione'], ensure_ascii=False) + ',\n "elezioni": {\n' + ',\n'.join(righe) + '\n }\n}\n')
    print(len(trovate), 'elezioni')
    print('--- note'); [print(' ', *d, sep=' | ') for d in note]
