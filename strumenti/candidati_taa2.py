"""Candidati sindaco di sei comunali del Trentino-Alto Adige rimaste senza dati dopo strumenti/candidati_taa.py
(strumenti/candidati-taa2.json, stesso schema di candidati-wikipedia.json; candidati-taa.json non si tocca).

Si lancia a mano, senza argomenti (i dati sono trascritti qui sotto, con la fonte di ogni numero):
    python strumenti/candidati_taa2.py

Elezioni cercate (codice catastale-data del primo turno come in dati/comunali.js):
  G452-2013-05-26 Pergine Valsugana (turno straordinario, ballottaggio il 9 giugno), B220-2014-05-04 Brunico
  (turno straordinario), A332-2015-05-10 Appiano sulla strada del vino, E421-2015-05-10 Laives (ballottaggio il
  24 maggio), E434-2015-05-10 Lana, H612-2024-05-26 Rovereto (turno straordinario, ballottaggio il 9 giugno).

Trovata solo Rovereto 2024, da due quotidiani che riportano gli stessi risultati definitivi:
  - candidati: voti da l'Adige del 27 maggio 2024 (stesse percentuali in il Dolomiti dello stesso giorno);
  - liste: percentuali (un decimale) da il Dolomiti del 10 giugno 2024 (somma 99,9);
  - nomi dei candidati e delle liste come nell'elenco ufficiale del Comune («Elezioni trasparenti»,
    www3.comune.rovereto.tn.it/elezioni-trasparenti, copia della Wayback Machine del 3 giugno 2024);
  - collegamenti lista-candidato da l'Adige, coerenti con tuttitalia.it (coalizione della sindaca eletta).
Vincitrice Giulia Robol al ballottaggio (tuttitalia.it e it.wikipedia.org, voce Rovereto).

Fonti provate senza esito (ottobre 2026):
  - prospetti PDF della Regione (www.regione.taa.it/elezioni/dati/CCCGGMMAAAA.pdf, codici 137 Pergine, 363 Brunico,
    354 Appiano, 390 Laives, 391 Lana): nessuna copia nella Wayback Machine per queste date; oggi rispondono 410;
  - sito dei risultati 2015 della Provincia di Bolzano (static.provinz.bz.it/vote/gem2015, codici 17504 Eppan,
    17540 Leifers): robots.txt esclude /vote/ e la Wayback Machine ha solo Bolzano, Bressanone e una pagina
    riassuntiva con i soli eletti; nessuna cartella per il turno straordinario del 2014;
  - www.elezionicomunali.bz.it (robots.txt permette tutto): applicazione con le sole comunali 2025, senza archivio;
  - open data della Regione (datahub.civis.bz.it): nessun file per il 2013-2015 (404); per il 2024 solo Laives,
    Lana e San Martino in Passiria;
  - elezioni.provincia.tn.it: archivio con provinciali, referendum ed europee, non le comunali;
  - risultati del Trentino (elezionicomunali.tn.it e sottodomini): nessuna copia del 2013 (solo una pagina del
    2010) e nessun sottodominio per il 2024 (esistono solo 2015, 2020, 2025, extraturno.2025 e .2026);
    www.extraturno.2024.elezionicomunali.tn.it e www.2024.elezionicomunali.tn.it non esistono;
  - siti dei Comuni (copie della Wayback Machine filtrate su elezioni/Wahlen): solo pagine dal 2024 in poi;
  - Regione (www.regione.taa.it/Documenti/Elezioni-Comunali): elenco caricato da /opendata/api, escluso da robots.txt;
  - stampa: per Pergine 2013 solo i nomi dei sette candidati e quattro percentuali di lista; per Laives 2015 solo
    i primi due candidati (il Post); per Appiano, Lana 2015 e Brunico 2014 nessun risultato completo.
Area: null (la ricava l'app dalle liste).
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from candidati_taa import date_comunali  # noqa: E402

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ADIGE_2024 = 'https://www.ladige.it/cronaca/elezioni-comunali-i-risultati-definitivi-ecco-i-sindaci-eletti-ed-i-voti-di-tutti-i-candidati-fmmcqb61'
DOLOMITI_2024 = ('https://www.ildolomiti.it/politica/2024/giulia-robol-e-la-prima-sindaca-di-rovereto-entrano-in-7-del-'
                 'partito-democratico-nessun-eletto-per-forza-italia-ecco-il-consiglio-comunale')
TRASPARENTI_2024 = ('https://web.archive.org/web/20240603165952/https://www3.comune.rovereto.tn.it/elezioni-trasparenti/'
                    'electo/extra/elenchi_trasparenza/0/L')

# chiave -> comune, sindaco eletto (per il controllo), candidati [nome, voti, [[lista, %], ...]], fonti
ELEZIONI = {
    'H612-2024-05-26': {
        'comune': 'Rovereto', 'eletto': 'Giulia Robol',
        'c': [
            ['Giulia Robol', 6450, [['Partito Democratico del Trentino', 19.3], ['Campobase', 9.2],
                                    ['Alleanza Verdi e Sinistra', 4.9], ['Rovereto Libera', 3.3],
                                    ["Civici per l'Autonomia", 3.1]]],
            ['Gianpiero Lui', 4813, [['Noi Rovereto Lui Sindaco', 15.0], ['Lega Trentino per Salvini Premier', 5.8],
                                     ['Partito Autonomista Trentino Tirolese', 4.6], ['Rovereto al Centro', 3.8],
                                     ['Forza Italia', 1.6]]],
            ['Michele Dorigotti', 2285, [['Officina Comune Rovereto', 15.3]]],
            ['Paolo Piccinni', 1631, [["Fratelli d'Italia", 10.6]]],
            ['Milo Marsili', 521, [['Democrazia Sovrana Popolare', 3.4]]],
        ],
        'fonte': ADIGE_2024, 'fonte_liste': DOLOMITI_2024, 'fonte_nomi': TRASPARENTI_2024,
    },
}

NON_TROVATE = {
    'G452-2013-05-26': 'Pergine Valsugana: sito dei risultati del Trentino 2013 e PDF della Regione non archiviati; stampa incompleta',
    'B220-2014-05-04': 'Brunico: pagine della Provincia di Bolzano e PDF della Regione non archiviati; nessun open data',
    'A332-2015-05-10': 'Appiano: pagina gem2015 (17504) non archiviata e /vote/ escluso da robots.txt; PDF della Regione non archiviato',
    'E421-2015-05-10': 'Laives: pagina gem2015 (17540) non archiviata; PDF della Regione non archiviato; stampa: solo i primi due',
    'E434-2015-05-10': 'Lana: pagina gem2015 non archiviata; PDF della Regione non archiviato',
}


def main():
    tornate = date_comunali()
    out, note = {}, []
    for chiave, e in ELEZIONI.items():
        if chiave[5:] not in tornate.get(chiave[:4], ()):
            raise ValueError(f'{chiave}: data non in dati/comunali.js')
        tot = sum(v for _, v, _ in e['c'])
        voci = [[n, round(100 * v / tot, 2), ll, None] for n, v, ll in sorted(e['c'], key=lambda c: -c[1])]
        if voci[0][0] != e['eletto']:
            note.append(f'{chiave}: il primo al primo turno ({voci[0][0]}) non è l\'eletto ({e["eletto"]})')
        s_l = sum(p for v in voci for _, p in v[2])
        if abs(s_l - 100) > 0.5:
            note.append(f'{chiave}: somma delle liste {s_l:.1f}')
        voce = {'comune': e['comune'], 'reg': '04', 'c': voci, 'fonte': e['fonte']}
        for k in ('fonte_liste', 'fonte_nomi'):
            if k in e: voce[k] = e[k]
        out[chiave] = voce
    return out, note


if __name__ == '__main__':
    trovate, note = main()
    uscita = {
        'descrizione': "Candidati sindaco (percentuale al primo turno) e liste collegate (percentuale sul totale dei voti di lista) "
                       "di comunali del Trentino-Alto Adige che mancano all'Archivio del Ministero, a it.wikipedia.org e a "
                       "strumenti/candidati-taa.json. Rovereto 2024: voti dei candidati da l'Adige (\"fonte\"), percentuali di "
                       "lista da il Dolomiti (\"fonte_liste\"), nomi ufficiali dall'elenco del Comune (\"fonte_nomi\"). Chiave: "
                       "codice catastale-data del primo turno come in dati/comunali.js. Voce: [nome, %, [[lista, %], ...], area]. "
                       "Generato da strumenti/candidati_taa2.py.",
        'elezioni': dict(sorted(trovate.items(), key=lambda kv: (kv[1]['comune'], kv[0]))),
    }
    righe = [f' {json.dumps(k)}: {json.dumps(v, ensure_ascii=False, separators=(",", ":"))}' for k, v in uscita['elezioni'].items()]
    with open(os.path.join(RADICE, 'strumenti', 'candidati-taa2.json'), 'w', encoding='utf-8') as f:
        f.write('{\n "descrizione": ' + json.dumps(uscita['descrizione'], ensure_ascii=False) + ',\n "elezioni": {\n' + ',\n'.join(righe) + '\n }\n}\n')
    print(len(trovate), 'elezioni trovate,', len(NON_TROVATE), 'non trovate')
    for k, m in NON_TROVATE.items(): print('  -', k, m)
    print('--- note'); [print(' ', n) for n in note]
