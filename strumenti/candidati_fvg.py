"""Candidati sindaco di dieci comunali del Friuli-Venezia Giulia che it.wikipedia.org non ha (o ha con dati
incoerenti), dalle fonti ufficiali della Regione (strumenti/candidati-fvg.json, stesso schema di
strumenti/candidati-wikipedia.json).

Fonti, tutte della Regione autonoma Friuli Venezia Giulia (Servizio elettorale):
- Archivio storico delle elezioni (elezionistorico.regione.fvg.it): per ogni comune un file
  distribuzione/json-storico/a_AAAA-MM-GG_ELZ_COM_<ISTAT>.json con i candidati sindaco, i voti, la percentuale
  e le liste collegate. Copre le comunali dal 1998 al 2017. Nota: la tornata del 9-10 aprile 2006 ha lì la data
  2006-04-10; per il 1999 i nomi sono «COGNOME NOME» e i nomi delle liste sono tagliati a 20 caratteri.
- Portale dei risultati (elezioni.regione.fvg.it): per le comunali dal 2021 i file
  distribuzione/json/AAAA-MM-GG_ELZ_COM_<id>_{voti_sindaco,voti_liste,liste,sindaci_AMMESSA}.json;
  il collegamento lista -> candidato passa per id_aggregazione (sindaci_AMMESSA) = id_agg_premier (liste).
- Portale open data (dati.friuliveneziagiulia.it, Socrata): i dataset «Elezioni comunali AAAA - Voti Sindaco/Liste»
  (voti per comune). Servono da controllo: i voti di candidati e liste devono coincidere con quelli dell'archivio o
  del portale, altrimenti l'elezione si scarta.

Si lancia a mano:
    python strumenti/candidati_fvg.py --scarica CARTELLA   # scarica i file (pausa di 1,5 s tra le richieste)
    python strumenti/candidati_fvg.py CARTELLA             # legge CARTELLA/{storico,portale,socrata}/ e scrive il JSON

Percentuali: per i candidati quella dell'archivio storico (sui voti validi ai candidati) o, dal portale, voti del
candidato sul totale dei voti ai candidati; per le liste voti di lista sul totale dei voti di lista.
Area: 'centrodestra' se tra le liste c'è un partito del centrodestra nazionale (Forza Italia, PdL, Fratelli d'Italia,
Alleanza Nazionale), 'centrosinistra' se c'è il PD (o i DS); altrimenti null, e l'app la ricava dalle liste.
Controlli: somma delle percentuali dei candidati vicina a 100, vincitore uguale al sindaco eletto noto
(tuttitalia.it, it.wikipedia.org), voti uguali a quelli degli open data quando ci sono.
Le elezioni già presenti in dati/candidati/06.js restano: strumenti/comunali.py aggiunge solo quelle che mancano.
"""
import os, re, sys, json, time, unicodedata, urllib.request

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = 'la-mia-storia-di-voto (github.com/angrisanidj/la-mia-storia-di-voto)'
STORICO = 'https://elezionistorico.regione.fvg.it/distribuzione/json-storico/'
PORTALE = 'https://elezioni.regione.fvg.it/distribuzione/json/'
PAGINA_PORTALE = 'https://elezioni.regione.fvg.it/consultazioni/ELZ_COM/'
SOCRATA = 'https://www.dati.friuliveneziagiulia.it/resource/'

# (codice catastale, comune, data della chiave come in dati/comunali.js, fonte, parametri, sindaco eletto noto)
# socrata: (dataset voti sindaco, dataset voti liste) per il controllo; ordine: come l'archivio scrive i nomi
ELEZIONI = [
    ('D670', 'Fontanafredda', '1999-06-13', 'storico', {'data': '1999-06-13', 'istat': '93022', 'ordine': 'cn'}, 'Saldan'),
    ('F795', 'Muggia', '2006-04-09', 'storico', {'data': '2006-04-10', 'istat': '32003', 'ordine': 'nc'}, 'Nesladek'),
    ('F795', 'Muggia', '2011-05-15', 'storico', {'data': '2011-05-15', 'istat': '32003', 'socrata': ('r289-szst', 'xytw-trq6')}, 'Nesladek'),
    ('A516', 'Aviano', '2012-05-06', 'storico', {'data': '2012-05-06', 'istat': '93004', 'socrata': ('an7u-i3jx', '3wid-8egx')}, 'Del Cont-Bernard'),
    ('F795', 'Muggia', '2016-06-05', 'storico', {'data': '2016-06-05', 'istat': '32003', 'socrata': ('xb7f-igun', 'b8d3-cprs')}, 'Marzi'),
    ('D670', 'Fontanafredda', '2017-06-11', 'storico', {'data': '2017-06-11', 'istat': '93022', 'socrata': ('8n3n-8ibc', '8byq-mgfp')}, 'Pegolo'),
    ('F795', 'Muggia', '2021-10-03', 'portale', {'id': 136, 'pagina': 'muggia', 'socrata': ('t8jr-umke', '2k5f-mrbi')}, 'Polidori'),
    ('D670', 'Fontanafredda', '2022-06-12', 'portale', {'id': 96, 'pagina': 'fontanafredda', 'socrata': ('3y4x-iyy9', 'cmzk-c39j')}, 'Pegolo'),
    ('L065', 'Tavagnacco', '2023-04-02', 'portale', {'id': 217, 'pagina': 'tavagnacco', 'socrata': ('9zey-sikm', 'q2ma-2dh6')}, 'Cucci'),
    ('C758', 'Cividale del Friuli', '2026-05-24', 'portale', {'id': 69, 'pagina': 'cividale_del_friuli', 'socrata': ('ivm2-pa4q', '82uh-ws4v')}, 'Vuga'),
]
FILE_PORTALE = ('voti_sindaco', 'voti_liste', 'liste', 'sindaci_AMMESSA')
# sigle dell'archivio 2006 sciolte nel nome del partito, perché l'app riconosca il simbolo
SIGLE = {'F.I.': 'Forza Italia', 'L.N.': 'Lega Nord', 'A.N.': 'Alleanza Nazionale', 'P.R.C.': 'Partito della Rifondazione Comunista'}
CDX = re.compile(r"forza italia|popolo della libert|\bpdl\b|fratelli d.italia|alleanza nazionale", re.I)
CSX = re.compile(r"partito democratico|\bpd\b|democratici di sinistra", re.I)
TAGLIO_1999 = 20  # nell'archivio del 1999 i nomi di lista sono tagliati a 20 caratteri


def norm(s):
    s = unicodedata.normalize('NFD', s.lower()); s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()


def ripara(s):
    """Testo UTF-8 letto come Latin-1 nell'archivio («LibertÃ\xa0» -> «Libertà»)."""
    if re.search('[ÃÄÅ]', s):
        try:
            return s.encode('latin-1').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return s


def titolo(s):
    """«DEL CONT-BERNARD» -> «Del Cont-Bernard»."""
    return ''.join(w.capitalize() for w in re.split(r"(\s+|-|')", s.strip().lower()))


def lista(s, anno):
    s = ripara(s).strip()
    tagliata = anno == '1999' and len(s) == TAGLIO_1999
    s = re.sub(r'\s+', ' ', s)
    s = SIGLE.get(s, s)
    return s + '…' if tagliata else s


def area(liste):
    nomi = ' | '.join(n for n, _ in liste)
    if CDX.search(nomi): return 'centrodestra'
    if CSX.search(nomi): return 'centrosinistra'
    return None


def leggi(cartella, *parti):
    with open(os.path.join(cartella, *parti), encoding='utf-8') as f:
        return json.load(f)


def da_storico(cartella, cod, comune, chiave, p):
    """Archivio storico: candidati con percentuale e liste collegate."""
    d = leggi(cartella, 'storico', f"a_{p['data']}_ELZ_COM_{p['istat']}.json")
    if norm(d['nomeStrutturaInteressata']) != norm(comune): raise ValueError(f"comune diverso: {d['nomeStrutturaInteressata']}")
    out = []
    for c in d['premierEletti']:
        nome = c['nominativoElettorale'].split()
        if p.get('ordine') == 'cn': nome = nome[-1:] + nome[:-1]
        tot = sum(l['votiValidi'] for x in d['premierEletti'] for l in x['liste'])
        liste = [(lista(l['nomeLista'], chiave[:4]), int(l['votiValidi'])) for l in c['liste']]
        out.append({'nome': titolo(' '.join(nome)), 'cognome_src': c['nominativoElettorale'], 'voti': int(c['votiValidi']),
                    'pct': round(c['votiValidiPerc'], 2), 'liste': liste, 'tot_liste': tot})
    return out, STORICO + f"a_{p['data']}_ELZ_COM_{p['istat']}.json"


def da_portale(cartella, cod, comune, chiave, p):
    """Portale dei risultati: voti dei candidati, voti delle liste e collegamento lista -> candidato."""
    f = lambda n: leggi(cartella, 'portale', f"{chiave}_ELZ_COM_{p['id']}_{n}.json")
    voti, vl, liste, ammessi = (f(n) for n in FILE_PORTALE)
    agg = {a['id']: a for a in ammessi}
    voti_lista = {x['id_candidatura']: x['voti_validi'] for x in vl}
    if len(voti_lista) != len(liste): raise ValueError('liste e voti di lista non corrispondono')
    tot_c = sum(v['voti_validi'] for v in voti); tot_l = sum(voti_lista.values())
    out = []
    for v in voti:
        a = agg[v['id_candidato']]
        ll = [(lista(l['nome'], chiave[:4]), voti_lista[l['id']]) for l in liste if l['id_agg_premier'] == a['id_aggregazione']]
        out.append({'nome': titolo(f"{a['nome']} {a['cognome']}"), 'cognome_src': a['cognome'], 'voti': v['voti_validi'],
                    'pct': round(100 * v['voti_validi'] / tot_c, 2), 'liste': ll, 'tot_liste': tot_l})
    if sum(len(c['liste']) for c in out) != len(liste): raise ValueError('liste non collegate a nessun candidato')
    return out, PAGINA_PORTALE + f"{chiave}/{p['pagina']}"


def controllo_socrata(cartella, comune, cand, ids):
    """Voti dei candidati (per cognome) e delle liste (per nome) uguali a quelli degli open data della Regione."""
    vs, vl = (leggi(cartella, 'socrata', f'{i}.json') for i in ids)
    del_comune = lambda r: norm(r.get('comune') or r.get('nome_comune') or '') == norm(comune)
    vs = [r for r in vs if del_comune(r) and r.get('turno', 'Primo Turno') == 'Primo Turno']
    vl = [r for r in vl if del_comune(r) and r.get('turno', 'Primo Turno') == 'Primo Turno']
    s_cand = {}
    for r in vs:
        cg = r.get('cognome_candidato_sindaco') or r.get('cognome_candidato') or r.get('cognome')
        nm = r.get('nome_candidato_sindaco') or r.get('nome_candidato') or r.get('nome')
        s_cand[norm(cg)] = (int(r.get('voti_candidato') or r['voti']), titolo(f'{nm} {cg}'))
    s_liste = sorted(int(r.get('voti_lista') or r['voti']) for r in vl)
    errori = []
    for c in cand:
        k = next((k for k in s_cand if k and k in norm(c['cognome_src'])), None)
        if k is None or s_cand[k][0] != c['voti']: errori.append(f"candidato {c['nome']}: {c['voti']} contro {s_cand.get(k)}")
        elif s_cand[k][1] != c['nome']: c['nome'] = s_cand[k][1]  # «Nome Cognome» dagli open data (cognomi composti)
    if len(s_cand) != len(cand): errori.append(f'{len(cand)} candidati contro {len(s_cand)} negli open data')
    if sorted(v for c in cand for _, v in c['liste']) != s_liste: errori.append('voti di lista diversi dagli open data')
    return errori


def main(cartella):
    trovate, scarti, note = {}, [], []
    for cod, comune, chiave, fonte, p, eletto in ELEZIONI:
        k = f'{cod}-{chiave}'
        try:
            cand, url = (da_storico if fonte == 'storico' else da_portale)(cartella, cod, comune, chiave, p)
        except (OSError, KeyError, ValueError) as e:
            scarti.append((k, comune, f'fonte non leggibile: {e}')); continue
        errori = controllo_socrata(cartella, comune, cand, p['socrata']) if p.get('socrata') else []
        if errori:
            scarti.append((k, comune, '; '.join(errori))); continue
        cand.sort(key=lambda c: -c['voti'])
        somma = round(sum(c['pct'] for c in cand), 2)
        if abs(somma - 100) > 1:
            scarti.append((k, comune, f'percentuali dei candidati: somma {somma}')); continue
        if abs(somma - 100) > 0.05: note.append((k, comune, f'somma delle percentuali dei candidati {somma}'))
        if norm(eletto) not in norm(cand[0]['nome']):
            scarti.append((k, comune, f"vince {cand[0]['nome']}, eletto noto {eletto}")); continue
        voce = []
        for c in cand:
            liste = [[n, round(100 * v / c['tot_liste'], 2)] for n, v in sorted(c['liste'], key=lambda x: -x[1])]
            voce.append([c['nome'], c['pct'], liste, area(liste)])
        trovate[k] = {'comune': comune, 'reg': '06', 'c': voce, 'fonte': url}
    return trovate, scarti, note


def scarica(cartella):
    """Scarica i file delle fonti in CARTELLA/{storico,portale,socrata}/ (crawl-delay 1 s degli open data)."""
    lavori = []
    for cod, comune, chiave, fonte, p, _ in ELEZIONI:
        if fonte == 'storico':
            n = f"a_{p['data']}_ELZ_COM_{p['istat']}.json"; lavori.append((STORICO + n, ('storico', n)))
        else:
            for f in FILE_PORTALE:
                n = f"{chiave}_ELZ_COM_{p['id']}_{f}.json"; lavori.append((PORTALE + n, ('portale', n)))
        for i in p.get('socrata', ()):
            lavori.append((SOCRATA + f'{i}.json?$limit=50000', ('socrata', f'{i}.json')))
    fatti = set()
    for url, (sotto, nome) in lavori:
        if url in fatti: continue
        fatti.add(url)
        os.makedirs(os.path.join(cartella, sotto), exist_ok=True)
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=60) as r, open(os.path.join(cartella, sotto, nome), 'wb') as f:
            f.write(r.read())
        print('[ok]', url, flush=True)
        time.sleep(1.5)


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--scarica':
        scarica(sys.argv[2]); sys.exit()
    cartella = sys.argv[1] if len(sys.argv) > 1 else '.'
    trovate, scarti, note = main(cartella)
    uscita = {
        'descrizione': "Candidati sindaco (percentuale al primo turno), liste collegate (percentuale sul totale dei voti di lista) e area politica "
                       "di comunali del Friuli-Venezia Giulia assenti da it.wikipedia.org, dalle fonti della Regione autonoma Friuli Venezia Giulia: "
                       "Archivio storico delle elezioni (elezionistorico.regione.fvg.it, file json-storico) fino al 2017, portale dei risultati "
                       "(elezioni.regione.fvg.it) dal 2021, con i voti controllati sugli open data regionali (dati.friuliveneziagiulia.it). "
                       "Chiave: codice catastale-data del primo turno come in dati/comunali.js. Voce: [nome, %, [[lista, %], ...], area]. "
                       "Generato da strumenti/candidati_fvg.py.",
        'elezioni': dict(sorted(trovate.items(), key=lambda kv: (kv[1]['comune'], kv[0]))),
    }
    # un'elezione per riga, così i cambiamenti si leggono nelle differenze di git
    righe = [f' {json.dumps(k)}: {json.dumps(v, ensure_ascii=False, separators=(",", ":"))}' for k, v in uscita['elezioni'].items()]
    with open(os.path.join(RADICE, 'strumenti', 'candidati-fvg.json'), 'w', encoding='utf-8') as f:
        f.write('{\n "descrizione": ' + json.dumps(uscita['descrizione'], ensure_ascii=False) + ',\n "elezioni": {\n' + ',\n'.join(righe) + '\n }\n}\n')
    print(len(trovate), 'elezioni su', len(ELEZIONI), ';', len(scarti), 'scartate;', len(note), 'note')
    print('--- scarti'); [print(' ', *s, sep=' | ') for s in scarti]
    print('--- note'); [print(' ', *n, sep=' | ') for n in note]
