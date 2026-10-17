"""Referendum regionali e delle province autonome dal 1992 (strumenti/referendum-regionali.json).

Raccolti a mano: per ogni referendum ci sono i voti assoluti (Sì, No, votanti, elettori) presi dalla
fonte indicata in «fonte», e lo script ne ricava le percentuali (Sì sui voti validi = Sì + No, affluenza
= votanti / elettori), arrotondate a due decimali. Dove la fonte non dà i numeri assoluti si usa la
percentuale che riporta (campi «si_pct» e «affluenza_pct»).

Sono inclusi solo i referendum in cui votava l'intera regione o l'intera provincia autonoma di Trento
o di Bolzano. Restano fuori, e sono elencati in ESCLUSI con il motivo: i referendum comunali, di
fusione di comuni o territoriali (passaggio di comuni ad altra regione o provincia), quelli su una
parte sola della regione, quelli provinciali fuori dalle province autonome, quelli indetti e poi
annullati e quelli prima del 1992.

Fonti: voci di it.wikipedia.org (scaricate in wikitext con index.php?title=...&action=raw; i numeri
vengono dalle tabelle dei risultati, che a loro volta citano i siti ufficiali di regioni e province),
pagine dei risultati della Regione Valle d'Aosta (regione.vda.it) per il 2007 e il 2012, sentenza
della Corte costituzionale n. 149 del 2009 per il referendum sulla legge statutaria sarda del 2007.

quorum: True raggiunto, False non raggiunto, None se la legge non lo prevedeva (referendum
confermativi, consultivo lombardo del 2017). Se l'affluenza cambia da quesito a quesito, quella del
referendum è la più alta e ogni quesito ha la sua.

Uso: python3 strumenti/referendum_regionali.py
"""
import json, os

def pct(a, b):
    return round(100 * a / b, 2)

W = 'https://it.wikipedia.org/wiki/'
VDA07 = 'https://www.regione.vda.it/amministrazione/elezioni/referendum2007/Default_i.asp?p=1&f=0&Tipo=R&L=I&idele='

# Per ogni quesito: breve, si, no (voti) oppure si_pct; votanti/elettori se diversi da quelli del referendum.
REFERENDUM = [
    dict(r='05', d='2002-10-06', s='Referendum buono-scuola', l='Referendum abrogativo regionale sul buono-scuola in Veneto',
         tipo='abrogativo', quorum=False, affluenza_pct=21.15,
         quesiti=[dict(breve='Abrogazione della legge regionale sul buono-scuola (L.R. 1/2001)', si=749214, no=52041)],
         fonte=W + 'Referendum_abrogativo_in_Veneto_del_2002',
         nota='Affluenza e voti dalla voce di Wikipedia (che cita ECN); non trovati sul sito della Regione.'),
    dict(r='06', d='2002-09-29', s='Referendum legge elettorale', l='Referendum confermativo sulla legge statutaria del Friuli-Venezia Giulia (forma di governo ed elezione del consiglio)',
         tipo='confermativo', quorum=None, affluenza_pct=23.06,
         quesiti=[dict(breve='Legge statutaria su forma di governo, elezione del consiglio regionale e referendum', si=65931, no=178766)],
         fonte=W + 'Referendum_confermativo_in_Friuli-Venezia_Giulia_del_2002',
         nota='Wikipedia indica «quorum non raggiunto», ma lo Statuto (art. 12) non prevede quorum per il referendum confermativo: '
              'la legge non fu promulgata perché vinse il No. Affluenza 23,06% come nella voce; votanti/iscritti della stessa voce darebbero 22,84%.'),
    dict(r='04', p='TN', d='2007-09-30', s='Referendum provinciale scuola', l='Referendum provinciale abrogativo sul finanziamento delle scuole paritarie in Trentino',
         tipo='abrogativo', quorum=False, votanti=76621, elettori=405239,
         quesiti=[dict(breve='Pianificazione del sistema scolastico e finanziamento delle istituzioni paritarie', si=70594, no=5177)],
         fonte=W + 'Referendum_abrogativo_nella_provincia_autonoma_di_Trento_del_2007'),
    dict(r='20', d='2007-10-21', s='Referendum legge statutaria', l='Referendum confermativo sulla legge statutaria della Sardegna',
         tipo='confermativo', quorum=False, affluenza_pct=15.7,
         quesiti=[dict(breve='Legge statutaria della Regione autonoma della Sardegna (approvata il 7 marzo 2007)', si=72606, no=153053)],
         fonte='https://giurcost.org/decisioni/2009/0149s-09.html',
         nota='Voti e affluenza riportati nella sentenza della Corte costituzionale n. 149/2009 (votanti 228.440). Quorum di un terzo degli elettori: '
              'la Corte d\'appello dichiarò il referendum non valido (30 giugno 2008); la Corte costituzionale annullò poi la promulgazione della legge.'),
    dict(r='02', d='2007-11-18', s='Referendum propositivi', l='Referendum propositivi regionali in Valle d\'Aosta (legge elettorale e ospedale, 5 quesiti)',
         tipo='propositivo', quorum=False, elettori=103765,
         quesiti=[dict(breve='Preferenza unica', si=24843, no=2278, votanti=28652, fonte=VDA07 + '085&noref=1'),
                  dict(breve='Elezione diretta della Giunta regionale', si=24685, no=2417, votanti=28553, fonte=VDA07 + '086&noref=2'),
                  dict(breve='Dichiarazione preventiva delle alleanze politiche', si=25402, no=1720, votanti=28639, fonte=VDA07 + '087&noref=3'),
                  dict(breve='Equilibrio della rappresentanza tra i generi', si=21373, no=5072, votanti=28429, fonte=VDA07 + '088&noref=4'),
                  dict(breve='Nuovo e unico presidio ospedaliero', si=16891, no=9684, votanti=28179, fonte=VDA07 + '089&noref=5')],
         fonte='https://www.regione.vda.it/amministrazione/elezioni/Referendum2007/default_i.asp',
         nota='Risultati del sito della Regione (indicati come ufficiosi). Quorum del 45% degli elettori.'),
    dict(r='04', p='BZ', d='2009-10-25', s='Referendum provinciali', l='Referendum provinciali propositivi in Alto Adige (5 quesiti)',
         tipo='propositivo', quorum=False, elettori=390398,
         quesiti=[dict(breve='Edilizia abitativa agevolata: precedenza alla popolazione locale', si=115560, no=24351, votanti=148051),
                  dict(breve='Residenze di tempo libero (legge urbanistica)', si=111414, no=26281, votanti=147886),
                  dict(breve='Democrazia diretta: referendum e iniziativa popolare (Union für Südtirol)', si=96616, no=38086, votanti=147696),
                  dict(breve='Democrazia diretta (Iniziativa per più democrazia)', si=114884, no=23260, votanti=148815),
                  dict(breve='Riduzione del traffico aereo (aeroporto di Bolzano)', si=113674, no=26739, votanti=149262)],
         fonte=W + 'Referendum_propositivi_nella_provincia_autonoma_di_Bolzano_del_2009',
         nota='Quorum del 40% degli elettori.'),
    dict(r='20', d='2011-05-15', d2='2011-05-16', s='Referendum nucleare (regionale)', l='Referendum consultivo sul nucleare in Sardegna',
         tipo='consultivo', quorum=True, votanti=887347, elettori=1479485,
         quesiti=[dict(breve='Contrarietà a centrali nucleari e depositi di scorie in Sardegna', si=848691, no=25026)],
         fonte=W + 'Referendum_consultivo_in_Sardegna_del_2011',
         nota='La Regione dichiarò il 97,13% di Sì; dai voti (848.691 Sì, 25.026 No) viene 97,14%.'),
    dict(r='04', p='TN', d='2012-04-29', s='Referendum provinciale Comunità di valle', l='Referendum provinciale abrogativo sulle Comunità di valle in Trentino',
         tipo='abrogativo', quorum=False, votanti=113157, elettori=413315,
         quesiti=[dict(breve='Abrogazione delle Comunità di valle', si=104531, no=7191)],
         fonte=W + 'Referendum_abrogativo_nella_provincia_autonoma_di_Trento_del_2012'),
    dict(r='20', d='2012-05-06', s='Referendum regionali', l='Referendum regionali sardi su province ed enti (10 quesiti)',
         tipo='abrogativo e consultivo', quorum=True, votanti=525651, elettori=1480366,
         quesiti=[dict(breve='Abrogazione del riassetto generale delle province (L.R. 4/1997)', tipo='abrogativo', si=503560, no=15876),
                  dict(breve='Abrogazione degli adempimenti per le nuove province (L.R. 10/2002)', tipo='abrogativo', si=507268, no=12431),
                  dict(breve='Abrogazione della delibera sulle nuove circoscrizioni provinciali', tipo='abrogativo', si=507278, no=11853),
                  dict(breve='Abrogazione delle province di Carbonia-Iglesias, Medio Campidano, Ogliastra, Olbia-Tempio', tipo='abrogativo', si=504680, no=16300),
                  dict(breve='Abolizione delle province storiche', tipo='consultivo', si=341956, no=176261),
                  dict(breve='Assemblea costituente per un nuovo Statuto', tipo='consultivo', si=487060, no=28803),
                  dict(breve='Elezione diretta del presidente con primarie', tipo='consultivo', si=501397, no=16267),
                  dict(breve='Abrogazione delle indennità dei consiglieri regionali (art. 1 L.R. 2/1966)', tipo='abrogativo', si=499328, no=14511),
                  dict(breve='Abolizione dei consigli di amministrazione di enti e agenzie regionali', tipo='consultivo', si=503879, no=15244),
                  dict(breve='Riduzione a 50 dei consiglieri regionali', tipo='consultivo', si=512321, no=8992)],
         fonte=W + 'Referendum_in_Sardegna_del_2012',
         nota='Affluenza definitiva sul totale degli iscritti; i votanti dei singoli quesiti vanno da 525.292 a 525.558. Quorum di un terzo degli elettori.'),
    dict(r='02', d='2012-11-18', s='Referendum rifiuti', l='Referendum propositivo regionale sul trattamento a caldo dei rifiuti (pirogassificatore) in Valle d\'Aosta',
         tipo='propositivo', quorum=True, votanti=50919, elettori=104064,
         quesiti=[dict(breve='Proposta di legge popolare sulla gestione dei rifiuti (no al trattamento a caldo)', si=47143, no=3000)],
         fonte='https://www.regione.vda.it/amministrazione/elezioni/referendum2012/Default_i.asp?ele=108&p=1&f=0&Tipo=VR&L=I',
         nota='Affluenza: https://www.regione.vda.it/amministrazione/elezioni/referendum2012/Default_i.asp?ele=108&p=1&f=0&Tipo=D&L=I&giorno=3&ora=15 . Quorum del 45%.'),
    dict(r='04', p='BZ', d='2014-02-09', s='Referendum provinciale partecipazione', l='Referendum provinciale confermativo sulla legge per la partecipazione civica in Alto Adige',
         tipo='confermativo', quorum=None, votanti=106305, elettori=401979,
         quesiti=[dict(breve='Legge provinciale sulla partecipazione civica in Alto Adige', si=36372, no=68463)],
         fonte=W + 'Referendum_confermativo_nella_provincia_autonoma_di_Bolzano_del_2014'),
    dict(r='04', p='BZ', d='2016-06-12', s='Referendum provinciale aeroporto', l='Referendum provinciale consultivo sull\'aeroporto di Bolzano',
         tipo='consultivo', quorum=True, votanti=191422, elettori=410148,
         quesiti=[dict(breve='Disegno di legge 60/15 «Norme sull\'aeroporto di Bolzano»', si=55633, no=134409)],
         fonte=W + 'Referendum_consultivo_nella_provincia_autonoma_di_Bolzano_del_2016',
         nota='Quorum del 40% degli elettori.'),
    dict(r='03', d='2017-10-22', s='Referendum autonomia', l='Referendum consultivo sull’autonomia della Lombardia',
         tipo='consultivo', quorum=None, votanti=3017707, elettori=7897056,
         quesiti=[dict(breve='Autonomia differenziata (art. 116 Cost.)', si=2875438, no=119051)],
         fonte=W + 'Referendum_consultivo_in_Lombardia_del_2017'),
    dict(r='05', d='2017-10-22', s='Referendum autonomia', l='Referendum consultivo sull’autonomia del Veneto',
         tipo='consultivo', quorum=True, affluenza_pct=57.2,
         quesiti=[dict(breve='Ulteriori forme di autonomia per il Veneto', si=2273985, no=43938)],
         fonte=W + 'Referendum_consultivo_in_Veneto_del_2017',
         nota='Affluenza ufficiale 57,2%; la tabella della voce (2.328.947 votanti su 4.019.628 elettori) darebbe 57,94%.'),
    dict(r='04', p='TN', d='2021-09-26', s='Referendum provinciale biodistretto', l='Referendum provinciale propositivo sul distretto biologico in Trentino',
         tipo='propositivo', quorum=False, votanti=68125, elettori=437113,
         quesiti=[dict(breve='Qualificazione come distretto biologico del territorio agricolo trentino', si=65642, no=2061)],
         fonte=W + 'Referendum_propositivo_nella_provincia_autonoma_di_Trento_del_2021',
         nota='Quorum del 40% degli elettori.'),
    dict(r='04', p='BZ', d='2022-05-29', s='Referendum provinciale democrazia diretta', l='Referendum provinciale confermativo sulla riforma della democrazia diretta in Alto Adige',
         tipo='confermativo', quorum=None, votanti=94680, elettori=426980,
         quesiti=[dict(breve='Modifiche alle leggi su democrazia diretta e Consiglio dei Comuni', si=22387, no=70843)],
         fonte=W + 'Referendum_confermativo_nella_provincia_autonoma_di_Bolzano_del_2022'),
    dict(r='02', d='2025-08-10', s='Referendum legge elettorale', l='Referendum confermativo sulla legge elettorale della Valle d\'Aosta (tre preferenze)',
         tipo='confermativo', quorum=None, votanti=16853, elettori=105054,
         quesiti=[dict(breve='Reintroduzione delle tre preferenze e rappresentanza di genere', si=8655, no=7944)],
         fonte=W + 'Referendum_confermativo_in_Valle_d%27Aosta_del_2025'),
]

ESCLUSI = [
    ('Emilia-Romagna, 1990 (abrogativi)', 'prima del 1992', W + 'Referendum_abrogativi_in_Emilia-Romagna_del_1990'),
    ('Piemonte, caccia (previsto il 3 giugno 2012)', 'non si è tenuto: la Regione abrogò la legge un mese prima', W + 'Referendum_piemontese_sulla_caccia'),
    ('Friuli-Venezia Giulia, 21 marzo 2004 (Provincia dell\'Alto Friuli)', 'solo una parte della regione', 'https://autonomielocali.regione.fvg.it/aall/export/sites/default/AALL/Elezioni/risultati/referendum/index.html'),
    ('Friuli-Venezia Giulia, 2007-2017 (fusioni di comuni)', 'referendum di fusione', 'https://autonomielocali.regione.fvg.it/aall/export/sites/default/AALL/Elezioni/risultati/referendum/index.html'),
    ('Valle d\'Aosta, Courmayeur 1° giugno 2014', 'comunale', 'https://www.regione.vda.it/amministrazione/Elezioni/Consultazioni_referendarie/Referendum_regionali/Archivio/default_i.aspx'),
    ('Provincia di Belluno, 22 ottobre 2017 (autonomia provinciale)', 'provinciale fuori dalle province autonome', W + 'Referendum_consultivo_in_provincia_di_Belluno_del_2017'),
    ('Verbano-Cusio-Ossola, 21 ottobre 2018 (passaggio alla Lombardia)', 'territoriale e provinciale', W + 'Referendum_consultivo_nella_provincia_del_Verbano-Cusio-Ossola_del_2018'),
    ('Trento, terzo mandato del presidente (richiesto nel 2025)', 'non indetto', 'https://www.ladige.it/cronaca/il-centrosinistra-al-referendum-contro-il-terzo-mandato-del-presidente-provinciale-axus2ltw'),
]

def costruisci():
    out = []
    for x in REFERENDUM:
        e = {k: x[k] for k in ('r', 'p', 'd', 'd2', 's', 'l', 'tipo', 'quorum') if k in x}
        qs, aff = [], []
        for q in x['quesiti']:
            o = {'breve': q['breve']}
            if 'tipo' in q: o['tipo'] = q['tipo']
            o['si'] = q['si_pct'] if 'si_pct' in q else pct(q['si'], q['si'] + q['no'])
            if 'votanti' in q:
                o['affluenza'] = pct(q['votanti'], q.get('elettori', x['elettori'])); aff.append(o['affluenza'])
            if 'fonte' in q: o['fonte'] = q['fonte']
            qs.append(o)
        if 'affluenza_pct' in x: e['affluenza'] = x['affluenza_pct']
        elif 'votanti' in x: e['affluenza'] = pct(x['votanti'], x['elettori'])
        else: e['affluenza'] = max(aff)
        if len(set(aff)) <= 1:
            for o in qs: o.pop('affluenza', None)
        e['quesiti'] = qs
        e['fonte'] = x['fonte']
        if 'nota' in x: e['nota'] = x['nota']
        out.append(e)
    out.sort(key=lambda e: (e['d'], e['r'], e.get('p', '')))
    return {
        'descrizione': 'Referendum regionali e delle province autonome di Trento e Bolzano dal 1992 in cui votava l\'intera regione o provincia. '
                       'si = % di Sì sui voti validi; affluenza = % di votanti sugli elettori; quorum: true raggiunto, false non raggiunto, null non previsto. '
                       'Generato da strumenti/referendum_regionali.py.',
        'referendum': out,
        'esclusi': [{'referendum': a, 'motivo': b, 'fonte': c} for a, b, c in ESCLUSI],
    }

if __name__ == '__main__':
    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'referendum-regionali.json')
    with open(dest, 'w', encoding='utf-8') as f:
        json.dump(costruisci(), f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(dest)
