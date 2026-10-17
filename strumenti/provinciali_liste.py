"""Candidati presidente (tutti, con la percentuale al primo turno) e liste collegate di 39 elezioni provinciali
dirette per cui il sito aveva solo i primi due candidati dal riquadro {{Elezioni}} di Wikipedia
(strumenti/provinciali-liste.json). Sono le provinciali 1993-1996 (regioni ordinarie, Sicilia, Friuli-Venezia
Giulia) e quelle di Sicilia e Friuli-Venezia Giulia fino al 2011.

Si lancia a mano:
    python strumenti/provinciali_liste.py ELENCO CARTELLA
ELENCO è il JSON delle elezioni da cercare (lista di {"chiave": "SIGLA-AAAA-MM-GG", "provincia", "ballottaggio",
"candidati": [[nome, %, area], ...]}: i due candidati del riquadro, che servono da controllo). CARTELLA contiene:
- wiki/pAAAA.txt: «Elezioni provinciali in Italia del AAAA» in wikitext (index.php?title=...&action=raw);
- fvg/a_<data>_ELZ_PROV_<id>.json: Archivio storico delle elezioni della Regione Friuli Venezia Giulia
  (elezionistorico.regione.fvg.it/distribuzione/json-storico/; elenco in elezioni_archiviate.json, province
  in a_<data>_ELZ_PROV.json: 1 Gorizia, 2 Pordenone, 3 Trieste, 4 Udine). Ogni file ha un elemento per comune e
  uno per l'intera provincia (idStrutturaInteressata = id della provincia): si usa quello. Copre le provinciali
  dal 1999 al 2013;
- sicilia2008/RIP_<n>.html: «Report Ripartizione Seggi» del sito elettorale della Regione Siciliana
  (www.elezioni.regione.sicilia.it/provinciali2008/REPORT_RIRARTIZIONE_SEGGI_PRIMO_TURNO_PROV_<n>.html, n = 1..8
  da Agrigento a Trapani in ordine alfabetico), dalle copie della Wayback Machine (scrutinio completo).
I siti della Regione e la Wayback Machine si scaricano con il workflow «Sonda» (la shell raggiunge solo Wikipedia).

Fonti, in ordine di preferenza:
1. Friuli-Venezia Giulia 2004-2011: l'archivio della Regione. Candidati e liste con i voti ufficiali; i nomi dei
   candidati («COGNOME NOME» nell'archivio) e delle liste (nel 2004 sigle come «DEMOCR_LIBER») si prendono da
   Wikipedia quando i voti coincidono, altrimenti si tengono quelli dell'archivio.
2. Sicilia 2008: il sito della Regione Siciliana, allo stesso modo.
3. Altrimenti it.wikipedia.org: {{Elezione amministrativa}} (candidati e liste con i voti), {{Elezione
   candidati}} o la tabella «Elezione del Presidente» (Sicilia 1994: solo candidati, perché le liste si
   collegavano tra loro e non ai candidati presidente; voto su due schede).
Percentuali: candidati sui voti validi ai candidati, liste sul totale dei voti validi di lista (come il
Modulo:Risultati di Wikipedia), entrambe del primo turno. Area: prima la coalizione (parametro aN della tabella,
coalizione del riquadro), poi il partito del riquadro, poi le liste collegate (come strumenti/candidati_wikipedia.py).
Controlli: percentuali dei candidati che sommano 100 (±0,5), primi due candidati uguali al riquadro entro 0,3 punti
(con la fonte ufficiale una differenza si segnala e vale la fonte ufficiale), liste che sommano 100, voti di
candidati e liste di Wikipedia confrontati con quelli ufficiali (le differenze si segnalano; valgono i voti ufficiali).
Un'elezione che non passa i controlli, o con un candidato senza nome, si scarta.
"""
import os, re, sys, json, html, unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from candidati_wikipedia import template, da_amministrativa, da_candidati, testo, voti, area_di, area_parte, pulisci_cella, numero, campi_box  # noqa: E402

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIKI = 'https://it.wikipedia.org/wiki/Elezioni_provinciali_in_Italia_del_'
SICILIA = 'http://www.elezioni.regione.sicilia.it/provinciali2008/REPORT_RIRARTIZIONE_SEGGI_PRIMO_TURNO_PROV_%d.html'
WAYBACK = 'https://web.archive.org/web/20080701000000/'
# chiave -> (data del file dell'archivio, id della provincia). Le provinciali friulane del 2006 si tennero il
# 9-10 aprile (archivio della Regione; introduzione della pagina di Wikipedia): la data 28 maggio dei riquadri è sbagliata.
FILE_FVG = {'PN-2004-06-12': ('2004-06-12', 2), 'GO-2006-05-28': ('2006-04-09', 1), 'TS-2006-05-28': ('2006-04-09', 3),
            'UD-2006-05-28': ('2006-04-09', 4), 'UD-2008-04-13': ('2008-04-13', 4), 'PN-2009-06-06': ('2009-06-06', 2),
            'GO-2011-05-15': ('2011-05-15', 1), 'TS-2011-05-15': ('2011-05-15', 3)}
NOTE_DATA = {k: 'Primo turno il 9-10 aprile 2006 (archivio della Regione FVG), non il 28 maggio' for k in ('GO-2006-05-28', 'TS-2006-05-28', 'UD-2006-05-28')}
SICILIA_2008 = {'AG': 1, 'CL': 2, 'CT': 3, 'EN': 4, 'ME': 5, 'PA': 6, 'SR': 7, 'TP': 8}
# nomi dell'archivio friulano senza corrispondenza su Wikipedia (Pordenone 2009 non c'è)
NOMI = {'CIRIANI ALESSANDRO': 'Alessandro Ciriani', 'ZANIN GIORGIO': 'Giorgio Zanin', 'SAM ALDO': 'Aldo Sam', 'SARTOR GIANNI': 'Gianni Sartor'}


def norm(s):
    s = unicodedata.normalize('NFD', s.lower()); s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()


def pct(v, tot):
    return round(v / tot * 100, 2) if tot else None


def sezione_wiki(cartella, chiave, provincia):
    """Testo della sezione della provincia (dal riquadro {{Elezioni}} al titolo successivo) e url della fonte."""
    anno = chiave[3:7]
    f = os.path.join(cartella, 'wiki', 'p%s.txt' % anno)
    if not os.path.exists(f): return None, None
    t = open(f, encoding='utf-8').read()
    nome = {'Massa e Carrara': 'Massa'}.get(provincia, provincia)
    m = re.search(r'\|\s*provincia\s*=\s*\[?\[?' + re.escape(nome) + r'[^\n]*', t)
    if not m: return None, None
    nxt = re.search(r'\n==', t[m.start():])
    titolo = (re.findall(r'^=+\s*(Provincia d[^=]*?)\s*=+\s*$', t[:m.start()], re.M) or [''])[-1]
    return t[m.start():m.start() + (nxt.start() if nxt else len(t))], WIKI + anno + ('#' + titolo.replace(' ', '_') if titolo else '')


def da_wiki(sez):
    """Candidati da Wikipedia: [[nome, voti|None, %, [[lista, voti|None, %], ...], etichetta area], ...]"""
    r = template(sez, 'Elezione amministrativa', 0, len(sez))
    if r and any(re.fullmatch(r'c\d+l\d+', k) for k in r[0]):
        par = r[0]
        cand, manc = da_amministrativa(par)
        if manc: return None, 'voti mancanti su Wikipedia: %s' % manc
        out = []
        for i, c in zip(sorted(int(k[1:]) for k in par if re.fullmatch(r'c\d+', k) and par[k].strip()), cand):
            liste, j = [], 1
            while ('c%dl%d' % (i, j)) in par:
                liste.append([testo(par['c%dl%d' % (i, j)]), voti(par.get('c%dv%d' % (i, j)))]); j += 1
            out.append([c[0], c[4], c[1], [[n, v, lp[1]] for (n, v), lp in zip(liste, c[2])], par.get('a%d' % i, ''), par.get('el%d' % i, '')])
        return out, None
    r = template(sez, 'Elezione candidati', 0, len(sez))
    if r:
        par = r[0]
        cand, manc = da_candidati(par)
        if manc: return None, 'voti mancanti su Wikipedia: %s' % manc
        idx = sorted(int(k[1:]) for k in par if re.fullmatch(r'c\d+', k) and par[k].strip())
        return [[c[0], c[4], c[1], [], par.get('a%d' % i, '') or par.get('p%d' % i, ''), ''] for i, c in zip(idx, cand)], None
    # Sicilia 1994: tabella «Elezione del Presidente» con nome – (sostegno) | %-I | %-II
    i = sez.find('Elezione del Presidente')
    if i >= 0 and sez.find('{|', i) >= 0:
        j = sez.find('{|', i); corpo = sez[j:sez.find('\n|}', j)]
        out = []
        for riga in corpo.split('\n|-')[1:]:
            celle = [c for c in (pulisci_cella(c) for c in re.split(r'\n\||\|\|', '\n' + riga.strip('\n'))[1:]) if c]
            if not celle or re.search(r'Totale', celle[0]) or celle[0].startswith('!'): continue
            m = re.match(r'(.*?)\s*(?:–\s*)?\((.*)\)\s*$', testo(celle[0]).replace('–', '– '))
            nome, sost = (m.group(1).strip(' –'), m.group(2)) if m else (testo(celle[0]), '')
            out.append([re.sub(r'\s+', ' ', nome), None, numero(celle[1]) if len(celle) > 1 else None, [], sost, ''])
        if out and all(c[2] is not None for c in out): return out, None
    return None, 'nessuna tabella dei candidati su Wikipedia'


def da_fvg(cartella, data, pid):
    f = os.path.join(cartella, 'fvg', 'a_%s_ELZ_PROV_%d.json' % (data, pid))
    tot = [x for x in json.load(open(f, encoding='utf-8')) if x['idStrutturaInteressata'] == pid][0]
    return [[p['nominativoElettorale'], p['votiValidi'], None, [[l['nomeLista'], l['votiValidi'], None] for l in p['liste']]] for p in tot['premierEletti']]


def da_sicilia(cartella, n):
    t = open(os.path.join(cartella, 'sicilia2008', 'RIP_%d.html' % n), encoding='latin-1').read()
    s = re.sub(r'<script.*?</script>|<style.*?</style>', '', t, flags=re.S)
    s = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s)))
    sez = re.findall(r'relativi a n\. (\d+) su n\. (\d+) sezioni', s)
    if not sez or any(a != b for a, b in sez): raise ValueError('scrutinio incompleto')
    out = []
    for b in re.findall(r'N° \d+ (?:Candidato Presidente|Presidente Eletto) (.+?) VOTI ([\d.]+) % [\d,]+ % Lista/e Collegata/e Candidati Voti % Seggi (.*?) Totale ', s):
        liste = re.findall(r'\s*(.+?) \d+ ([\d.]+) [\d,]+ % \d+(?= |$)', b[2])
        out.append([b[0], int(b[1].replace('.', '')), None, [[l[0], int(l[1].replace('.', '')), None] for l in liste]])
    return out


def nome_candidato(uff, voti_uff, wiki):
    """Nome «Nome Cognome»: quello di Wikipedia con gli stessi voti, o con il cognome uguale."""
    for w in wiki or []:
        if w[1] == voti_uff: return w[0]
    parole = set(norm(uff).split())
    for w in wiki or []:
        if norm(w[0]).split()[-1] in parole: return w[0]
    if uff in NOMI: return NOMI[uff]
    p = uff.title().split()
    return ' '.join(p[1:] + p[:1]) if len(p) == 2 else None


def unisci(uff, wiki, note):
    """Dati ufficiali con i nomi di Wikipedia (candidati e liste con gli stessi voti)."""
    out = []
    for c in uff:
        nome = nome_candidato(c[0], c[1], wiki)
        if not nome: note.append('nome non risolto: ' + c[0]); return None
        w = next((x for x in wiki or [] if x[0] == nome), None)
        if w and w[1] is not None and w[1] != c[1]: note.append('voti di %s: Wikipedia %s, fonte ufficiale %s' % (nome, w[1], c[1]))
        # liste: il nome di Wikipedia con gli stessi voti (a parità di voti, quello con una parola in comune);
        # se restano una lista ufficiale e una di Wikipedia senza corrispondenza, si accoppiano (refuso nei voti)
        wliste = list(w[3]) if w else []
        nomi = [None] * len(c[3])
        for n, l in enumerate(c[3]):
            wl = [x for x in wliste if x[1] == l[1]]
            if len(wl) > 1: wl = [x for x in wl if set(norm(x[0]).split()) & {t for t in norm(l[0]).split() if len(t) > 3}]
            if len(wl) == 1: nomi[n] = wl[0][0]; wliste.remove(wl[0])
        resto = [n for n in range(len(c[3])) if nomi[n] is None]
        if len(resto) == 1 and len(wliste) == 1:
            n = resto[0]
            note.append('lista %s: voti ufficiali %s, Wikipedia %s (%s)' % (c[3][n][0], c[3][n][1], wliste[0][1], wliste[0][0]))
            nomi[n] = wliste[0][0]; wliste = []
        elif w and (resto or wliste):
            note.append('liste di %s senza corrispondenza su Wikipedia: %s' % (nome, [c[3][n][0] for n in resto]))
        liste = [[nomi[n] or l[0], l[1]] for n, l in enumerate(c[3])]
        out.append([nome, c[1], None, [[n, v, None] for n, v in liste], w[4] if w else '', w[5] if w else ''])
    return out


def percentuali(cand):
    tot_c = sum(c[1] for c in cand) if all(c[1] is not None for c in cand) else None
    tot_l = sum(l[1] for c in cand for l in c[3])
    for c in cand:
        if tot_c: c[2] = pct(c[1], tot_c)
        for l in c[3]: l[2] = pct(l[1], tot_l)
    return cand


def area(c, box, anno):
    """Prima la coalizione (tabella, riquadro), poi il partito del riquadro, poi le liste."""
    i = next((n for n in range(1, 12) if box.get('candidato%d' % n) and norm(testo(box['candidato%d' % n])) == norm(c[0])), None)
    # «Rifondazione Cristiana» (Veritas) non è Rifondazione Comunista
    liste = [re.sub(r'Rifondazione (?=Cristiana)', '', l[0]) for l in c[3]]
    prove = [c[4]] + ([box.get('coalizione%d' % i, ''), box.get('partito%d' % i, '')] if i else []) + [' - '.join(liste)]
    for p in prove:
        p = re.sub(r'^Polo$', 'Polo delle Libertà', testo(p) if '[[' not in (p or '') else p)
        a = area_di(p, anno)
        if a: return a
    # nomi con «e» che area_di spezzerebbe («Futuro e Libertà»): lista per lista, se l'area è una sola
    aree = {area_parte(l, anno) for l in liste} - {None}
    return aree.pop() if len(aree) == 1 else None


def main(elenco, cartella):
    trovate, scarti, avvisi = {}, [], []
    for e in json.load(open(elenco, encoding='utf-8')):
        k, prov = e['chiave'], e['provincia']
        anno = int(k[3:7]); note = []
        sez, url_wiki = sezione_wiki(cartella, k, prov)
        wiki, err = da_wiki(sez) if sez else (None, 'provincia assente dalla pagina di Wikipedia')
        box = campi_box(sez[:sez.find('\n}}')]) if sez else {}
        fonte = url_wiki
        if k in FILE_FVG:
            data, pid = FILE_FVG[k]
            cand = unisci(da_fvg(cartella, data, pid), wiki, note)
            fonte = 'https://elezionistorico.regione.fvg.it/consultazioni/provincerubrica/%s/ELZ_PROV' % data
        elif anno == 2008 and k[:2] in SICILIA_2008:
            cand = unisci(da_sicilia(cartella, SICILIA_2008[k[:2]]), wiki, note)
            fonte = WAYBACK + SICILIA % SICILIA_2008[k[:2]]
        else:
            cand = wiki
            if cand is None: scarti.append((k, prov, err)); continue
        if cand is None: scarti.append((k, prov, '; '.join(note))); continue
        if any(not re.search(r'[A-Za-z]', c[0]) for c in cand):
            scarti.append((k, prov, 'candidato senza nome su Wikipedia: ' + str([[c[0], c[3][0][0] if c[3] else ''] for c in cand if not re.search(r'[A-Za-z]', c[0])])))
            continue
        cand = percentuali(cand)
        somma = sum(c[2] for c in cand)
        somma_l = sum(l[2] for c in cand for l in c[3])
        if abs(somma - 100) > 0.5: scarti.append((k, prov, 'candidati sommano %.2f' % somma)); continue
        if any(c[3] for c in cand) and abs(somma_l - 100) > 0.5: scarti.append((k, prov, 'liste sommano %.2f' % somma_l)); continue
        ufficiale = fonte != url_wiki
        for nome, p, _ in e['candidati']:
            c = next((c for c in cand if norm(c[0]) == norm(nome) or norm(c[0]).split()[-1] == norm(nome).split()[-1]), None)
            if c is None: note.append('%s del riquadro non trovato' % nome); continue
            if abs(c[2] - p) > 0.3: note.append('%s: riquadro %.2f, %s %.2f' % (nome, p, 'fonte ufficiale' if ufficiale else 'tabella', c[2]))
        if not ufficiale and any('riquadro' in n for n in note): scarti.append((k, prov, '; '.join(note))); continue
        voce = {'provincia': prov,
                'c': [[c[0], c[2], [[l[0], l[2]] for l in c[3]], area(c, box, anno)] for c in sorted(cand, key=lambda c: -c[2])],
                'fonte': fonte}
        if k in NOTE_DATA: voce['nota'] = NOTE_DATA[k]
        if not any(c[3] for c in cand): note.append('solo candidati, senza liste')
        trovate[k] = voce
        if note: avvisi.append((k, prov, '; '.join(note)))
    uscita = {'descrizione': 'Candidati presidente (percentuale al primo turno sui voti validi ai candidati), liste collegate (percentuale sul '
                             'totale dei voti validi di lista) e area politica di provinciali dirette 1993-2011 che nel sito avevano solo i primi due '
                             'candidati. Fonti: Archivio storico delle elezioni della Regione Friuli Venezia Giulia (elezionistorico.regione.fvg.it, '
                             'file json-storico) per il Friuli-Venezia Giulia dal 2004; sito elettorale della Regione Siciliana '
                             '(www.elezioni.regione.sicilia.it/provinciali2008, copie della Wayback Machine) per la Sicilia 2008; it.wikipedia.org '
                             '(«Elezioni provinciali in Italia del AAAA», tabelle {{Elezione amministrativa}}, {{Elezione candidati}} e «Elezione del '
                             'Presidente») per le altre. Sicilia 1994: solo candidati (le liste non erano collegate ai candidati presidente). '
                             'Chiave: sigla della provincia-data del primo turno come nel sito. Voce: [nome, %, [[lista, %], ...], area]. '
                             'Generato da strumenti/provinciali_liste.py.',
              'elezioni': dict(sorted(trovate.items(), key=lambda kv: (kv[0][3:], kv[0][:2])))}
    with open(os.path.join(RADICE, 'strumenti', 'provinciali-liste.json'), 'w', encoding='utf-8') as f:
        righe = [' %s: %s' % (json.dumps(k), json.dumps(v, ensure_ascii=False, separators=(',', ':'))) for k, v in uscita['elezioni'].items()]
        f.write('{\n "descrizione": ' + json.dumps(uscita['descrizione'], ensure_ascii=False) + ',\n "elezioni": {\n' + ',\n'.join(righe) + '\n }\n}\n')
    print(len(trovate), 'elezioni;', len(scarti), 'scartate')
    print('--- scarti'); [print(' ', *s, sep=' | ') for s in scarti]
    print('--- note'); [print(' ', *a, sep=' | ') for a in avvisi]


if __name__ == '__main__':
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
