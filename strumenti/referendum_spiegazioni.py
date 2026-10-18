"""Genera strumenti/referendum-spiegazioni.json: per ogni referendum (nazionale,
regionale o provinciale) dell'elenco di storia-di-voto/research/quesiti.json, una
spiegazione breve (cosa si votava, cosa comportava il Sì) e le posizioni dei
principali partiti/schieramenti del momento, con le fonti.

Come sono stati raccolti i dati (ottobre 2026)
---------------------------------------------
1. Wikitesto delle voci it.wikipedia «Referendum abrogativi in Italia del AAAA»,
   «Referendum costituzionale in Italia del AAAA» e delle voci dei singoli
   referendum regionali/provinciali, scaricato con action=raw (User-Agent
   descrittivo, pause di 4 s); lette le sezioni «Quesiti» e «Posizioni».
2. Seconda fonte per i referendum più noti (WebSearch/WebFetch): Quaderni
   dell'Osservatorio elettorale (QOE, tabelle tratte dal Corriere della Sera),
   l'Unità (archivio), Il Post, Fanpage, Sky TG24, AGCOM, Wanted in Rome,
   openDemocracy. Dove le fonti divergono lo si dice in "nota_posizioni".
3. Le posizioni sono riportate solo per i partiti principali del momento
   (indicativamente sopra il 2-3% o promotori), con il nome di allora.

Per le giornate con più quesiti e schieramenti diversi quesito per quesito,
le posizioni sono scritte come tabella partito -> codici per quesito
(S = Sì, N = No, A = astensione/non voto, L = libertà di voto, - = non nota).
Lo script ne ricava "posizioni_quesiti" (dettaglio) e "posizioni"
(indicazione prevalente: il partito compare solo se ha dato la stessa
indicazione in più della metà dei quesiti su cui è nota; gli altri sono citati
nella nota). Per 1993 e 1995 "posizioni" riporta invece lo schieramento sul
quesito più conteso (Senato nel 1993, tv nel 1995), come detto nella nota.

Controlli: numero di righe "quesiti" uguale al numero di quesiti di
quesiti.json, chiavi identiche, lunghezze indicative dei testi.

Uso:  python3 strumenti/referendum_spiegazioni.py [percorso/quesiti.json]
"""
import json
import os
import sys
from collections import Counter

QUI = os.path.dirname(os.path.abspath(__file__))
QUESITI = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    QUI, '..', '..', 'storia-di-voto', 'research', 'quesiti.json')
USCITA = os.path.join(QUI, 'referendum-spiegazioni.json')

W = 'https://it.wikipedia.org/wiki/'
CHIAVE = {'S': 'si', 'N': 'no', 'A': 'astensione', 'L': 'liberta'}


def tabella(righe, n, guida=None):
    """righe: lista di (partito, codici[, suffissi]) -> (posizioni_quesiti, posizioni, misti).

    posizioni = indicazione prevalente: un partito vi compare se ha dato la stessa
    indicazione in più della metà dei quesiti su cui la sua posizione è nota (e se
    è nota per almeno metà dei quesiti); altrimenti finisce in "misti".
    Con guida=i, posizioni = schieramento sul quesito i (0-based), il più conteso.
    """
    pq = [{} for _ in range(n)]
    prev = {}
    misti = []
    for riga in righe:
        nome, codici = riga[0], riga[1].split()
        suff = riga[2] if len(riga) > 2 else {}
        assert len(codici) == n, (nome, codici)
        for i, c in enumerate(codici):
            if c == '-':
                continue
            pq[i].setdefault(CHIAVE[c], []).append(nome + suff.get(c, ''))
        noti = [c for c in codici if c != '-']
        c, k = Counter(noti).most_common(1)[0]
        if k * 2 > len(noti) and len(noti) * 2 >= n:
            prev.setdefault(CHIAVE[c], []).append(nome + suff.get(c, ''))
        else:
            misti.append(nome)
    ordine = ['si', 'no', 'astensione', 'liberta']
    pq = [{k: d[k] for k in ordine if k in d} for d in pq]
    prev = {k: prev[k] for k in ordine if k in prev}
    if guida is not None:
        prev, misti = pq[guida], []
    return pq, prev, misti


def nota(testo, misti):
    if misti:
        testo += ' Indicazioni diverse a seconda del quesito: ' + ', '.join(misti) + '.'
    return testo


D = {}

# ---------------------------------------------------------------- NAZIONALI

pq, prev, _ = tabella([
    ('Lista Pannella-Riformatori', 'S S S S S S S S'),
    ('Democrazia Cristiana', 'S N S S S S N S'),
    ('Partito Democratico della Sinistra', 'S S S S S S S S'),
    ('Partito Socialista Italiano', 'S S S S - S - -'),
    ('Rifondazione Comunista', 'N S L L N N - N'),
    ('Lega Nord', 'L L S S S S S S'),
    ('Movimento Sociale Italiano', 'S N S S S N N N'),
    ('Partito Repubblicano Italiano', 'L L S S S S S S'),
    ('Partito Liberale Italiano', 'N S S S S S N -'),
    ('Partito Socialista Democratico Italiano', 'S N S S S S N S'),
    ('Federazione dei Verdi', 'S S S S - - - -'),
    ('La Rete', '- - - - - N - -'),
], 8, guida=5)
D['1993-04-18'] = {
    'cosa': "Otto referendum abrogativi promossi soprattutto da radicali, dal comitato di Mario Segni e da alcune regioni, "
            "in piena Tangentopoli. Il Sì cancellava, tra l'altro, il finanziamento pubblico dei partiti, tre ministeri "
            "e il sistema proporzionale per il Senato, aprendo al maggioritario. Vinse il Sì in tutti e otto.",
    'quesiti': [
        "Sì: toglieva alle USL i controlli ambientali (poi affidati alle agenzie regionali per l'ambiente)",
        "Sì: niente più sanzioni penali per la detenzione di droga per uso personale né «dose media giornaliera»",
        "Sì: aboliva il finanziamento pubblico dei partiti",
        "Sì: toglieva al governo le nomine ai vertici di casse di risparmio e monti di pietà",
        "Sì: sopprimeva il ministero delle Partecipazioni statali",
        "Sì: Senato eletto con il maggioritario nei collegi uninominali invece che con il proporzionale",
        "Sì: sopprimeva il ministero dell'Agricoltura e delle foreste",
        "Sì: sopprimeva il ministero del Turismo e dello spettacolo",
    ],
    'posizioni': prev,
    'posizioni_quesiti': pq,
    'nota_posizioni': "In «posizioni» lo schieramento sul quesito del Senato, il più conteso: l'Unità chiamava MSI, Rete e "
                      "Rifondazione «i tre partiti del No», Wikipedia vi aggiunge i Verdi. Le posizioni sugli altri quesiti "
                      "vengono dalla sola Wikipedia, che le segnala come da verificare.",
    'fonti': [W + 'Referendum_abrogativi_in_Italia_del_1993',
              'https://archivio.unita.news/assets/main/1993/04/11/page_006.pdf'],
}

pq, prev, misti = tabella([
    ('Partito Democratico della Sinistra', 'N S S L S N N N N S S S'),
    ('Forza Italia', 'S S S S S N S S N N N N'),
    ('Alleanza Nazionale', 'S S S S N N S S N N N N'),
    ('Lega Nord', 'S S S S S N L N N S S S'),
    ('Partito Popolare Italiano (Bianco)', 'N N N S S N N N N S S S'),
    ('Popolari di Buttiglione', 'N N N N N N N N N N N N'),
    ('Rifondazione Comunista', 'S S S S N N L N N S S S'),
    ('Centro Cristiano Democratico', 'L L L S N N L S N N N N'),
    ('Patto dei Democratici', 'N N N S S L N N N S S S'),
    ('Federazione dei Verdi', 'S S S S N N N N N S S S'),
    ('Lista Pannella-Riformatori', 'S S S S S S S S S N N N'),
], 12, guida=9)
D['1995-06-11'] = {
    'cosa': "Dodici referendum abrogativi: sindacati e lavoro pubblico, soggiorno cautelare dei mafiosi, Rai, commercio, "
            "legge elettorale dei comuni e, i più seguiti, tre quesiti sulla tv privata che avrebbero ridotto le reti e la "
            "pubblicità di un singolo operatore (Fininvest). Sui tre quesiti tv prevalse il No.",
    'quesiti': [
        "Sì: rappresentanze sindacali aziendali aperte a tutti i sindacati, non solo alle confederazioni maggiori",
        "Sì: rappresentanze aperte anche ai sindacati firmatari di contratti applicati in azienda (versione ridotta)",
        "Sì: cancellava le regole sulla rappresentatività sindacale nei contratti del pubblico impiego",
        "Sì: aboliva il soggiorno cautelare fuori residenza per gli imputati di mafia",
        "Sì: toglieva l'obbligo che la Rai fosse interamente pubblica, aprendo alla privatizzazione",
        "Sì: aboliva l'autorizzazione amministrativa (licenza) per aprire un'attività commerciale",
        "Sì: aboliva la trattenuta automatica dei contributi sindacali in busta paga",
        "Sì: sindaco eletto a turno unico, senza ballottaggio, anche nei comuni sopra i 15.000 abitanti",
        "Sì: liberalizzava gli orari dei negozi",
        "Sì: un solo soggetto non avrebbe potuto possedere più di una rete tv nazionale",
        "Sì: vietava le interruzioni pubblicitarie durante i film in tv",
        "Sì: una concessionaria non avrebbe potuto raccogliere pubblicità per più di due reti nazionali",
    ],
    'posizioni': prev,
    'posizioni_quesiti': pq,
    'nota_posizioni': "In «posizioni» lo schieramento sui tre quesiti tv, i più seguiti, promossi da ARCI, ACLI e Legambiente. "
                      "Sugli altri le alleanze cambiavano quesito per quesito: quelli sindacali venivano dai Cobas, gli altri "
                      "da radicali e Lega.",
    'fonti': [W + 'Referendum_abrogativi_in_Italia_del_1995',
              'https://www.ilgiornale.it/news/politica/quei-quesiti-che-volevano-seppellire-reti-cav-trionf-libert-2492814.html'],
}

D['1997-06-15'] = {
    'cosa': "Sette referendum abrogativi, sei promossi dai Club Pannella-Riformatori e uno da sette consigli regionali: "
            "golden share, obiezione di coscienza, caccia, magistrati, Ordine dei giornalisti, ministero agricolo. "
            "Vinse ovunque il Sì, ma con il 30% di affluenza mancò il quorum.",
    'quesiti': [
        "Sì: aboliva i poteri speciali del Tesoro nelle aziende privatizzate (golden share)",
        "Sì: toglieva i limiti per essere ammessi al servizio civile al posto di quello militare",
        "Sì: i cacciatori non avrebbero più potuto entrare liberamente nei fondi privati",
        "Sì: aboliva l'attuale sistema di progressione in carriera dei magistrati",
        "Sì: aboliva l'Ordine dei giornalisti",
        "Sì: vietava ai magistrati gli incarichi fuori dall'attività giudiziaria",
        "Sì: sopprimeva il ministero delle Risorse agricole, alimentari e forestali",
    ],
    'posizioni': {'si': ['Club Pannella-Riformatori (promotori dei quesiti 1-6)']},
    'nota_posizioni': "Il quesito sul ministero agricolo fu chiesto da sette consigli regionali. Secondo Wikipedia i radicali "
                      "rimasero isolati nella campagna; nelle fonti consultate non si trovano indicazioni di voto ufficiali "
                      "degli altri partiti.",
    'fonti': [W + 'Referendum_abrogativi_in_Italia_del_1997',
              'https://www.regione.toscana.it/documents/10180/452241/Elezioni%20in%20Italia_q38/98505082-8afc-4268-ae85-e6ffea569c30'],
}

D['1999-04-18'] = {
    'cosa': "Referendum abrogativo sulla legge elettorale della Camera (Mattarellum): il Sì aboliva il voto di lista per la "
            "quota proporzionale (25% dei seggi), che sarebbe andata ai migliori non eletti nei collegi, rendendo il "
            "sistema quasi solo maggioritario. Sì al 91,5%, ma quorum mancato di poco (49,6%).",
    'posizioni': {
        'si': ['Patto Segni', 'Lista Bonino (radicali)', 'I Democratici', 'Democratici di Sinistra', 'Alleanza Nazionale',
               'Centro Cristiano Democratico'],
        'no': ['Rifondazione Comunista', 'Partito dei Comunisti Italiani'],
        'astensione': ['Partito Popolare Italiano', 'Lega Nord'],
        'liberta': ['Forza Italia'],
    },
    'nota_posizioni': "Comitato promotore trasversale (Segni, Occhetto, Fini, radicali). Secondo i Quaderni dell'Osservatorio "
                      "elettorale erano contrari anche SDI, Verdi e UDR, mentre Forza Italia e buona parte dei DS si impegnarono poco.",
    'fonti': [W + 'Referendum_abrogativo_in_Italia_del_1999',
              'https://oaj.fupress.net/index.php/qoe/article/download/13789/11232/43765'],
}

pq, prev, misti = tabella([
    ('Democratici di Sinistra', 'N S L N L N L'),
    ('Forza Italia', 'A A A A A A A', {'A': ' (o libertà di voto)'}),
    ('Alleanza Nazionale', 'S S L L L L L'),
    ('Lega Nord', 'A A A A A A A'),
    ('Partito Popolare Italiano', 'N N N N N N N', {'N': ' (o astensione)'}),
    ('Rifondazione Comunista', 'A A A A A A A'),
    ('Lista Bonino', 'S S S S S S S'),
    ('I Democratici', 'S S S N S N S'),
    ('Centro Cristiano Democratico', 'L L L L L L L'),
    ('Cristiani Democratici Uniti', 'A A A A A A A'),
    ('Partito dei Comunisti Italiani', 'N N N N S N N'),
    ('Socialisti Democratici Italiani', 'A A A A A A A'),
    ('Federazione dei Verdi', 'S L S N S N S'),
], 7)
D['2000-05-21'] = {
    'cosa': "Sette referendum abrogativi promossi dai radicali (Lista Bonino): rimborsi elettorali, quota proporzionale della "
            "Camera, CSM e carriere dei magistrati, art. 18 dello Statuto dei lavoratori, trattenute sindacali. "
            "Con il 32% di affluenza mancò il quorum; sull'art. 18 prevalse il No.",
    'quesiti': [
        "Sì: aboliva i rimborsi delle spese elettorali ai partiti",
        "Sì: aboliva il voto di lista per la quota proporzionale della Camera (seggi ai migliori non eletti nei collegi)",
        "Sì: membri togati del CSM eletti senza liste, con candidature individuali",
        "Sì: separava le carriere di giudici e pubblici ministeri",
        "Sì: vietava ai magistrati gli incarichi fuori dall'attività giudiziaria",
        "Sì: aboliva il reintegro nel posto di lavoro per i licenziamenti senza giusta causa (art. 18)",
        "Sì: aboliva le trattenute sindacali tramite gli enti previdenziali (su pensioni e indennità)",
    ],
    'posizioni': prev,
    'posizioni_quesiti': pq,
    'nota_posizioni': nota("Fonte principale la tabella del Corriere della Sera ripresa dai Quaderni dell'Osservatorio "
                           "elettorale; Wikipedia diverge su alcuni partiti minori (per esempio lo SDI).", misti),
    'fonti': [W + 'Referendum_abrogativi_in_Italia_del_2000',
              'https://oaj.fupress.net/index.php/qoe/article/download/12792/10648'],
}

D['2001-10-07'] = {
    'cosa': "Primo referendum costituzionale confermativo della Repubblica, sulla riforma del Titolo V approvata a "
            "maggioranza dal centrosinistra a fine legislatura. Il Sì confermava più poteri a regioni ed enti locali "
            "(legislazione concorrente, autonomia finanziaria). Vinse il Sì con il 64%; non c'era quorum.",
    'posizioni': {
        'si': ["L'Ulivo (DS, Margherita e alleati)"],
        'no': ['Rifondazione Comunista'],
        'astensione': ['Lega Nord'],
        'liberta': ['Casa delle Libertà (divisa; governo Berlusconi ufficialmente neutrale)'],
    },
    'nota_posizioni': "Il centrodestra, contrario alla riforma in Parlamento, si divise: Bossi e Gasparri invitarono a non votare, "
                      "quasi tutti i presidenti di regione di centrodestra si espressero per il Sì.",
    'fonti': [W + 'Referendum_costituzionale_in_Italia_del_2001',
              'https://archivio.unita.news/assets/main/2001/09/25/page_011.pdf'],
}

D['2003-06-15'] = {
    'cosa': "Due referendum abrogativi promossi da Rifondazione Comunista e sinistra sindacale: il Sì estendeva la tutela "
            "dell'art. 18 (reintegro dopo un licenziamento illegittimo) alle aziende sotto i 16 dipendenti e aboliva "
            "l'obbligo di far passare gli elettrodotti sui terreni privati. Quorum mancato (25,7%).",
    'quesiti': [
        "Sì: reintegro dopo un licenziamento illegittimo anche nelle aziende con meno di 16 dipendenti",
        "Sì: aboliva la servitù coattiva di elettrodotto, l'obbligo per i privati di far passare le linee elettriche",
    ],
    'posizioni': {
        'si': ['Rifondazione Comunista', 'Federazione dei Verdi', 'Partito dei Comunisti Italiani', 'Italia dei Valori'],
        'no': ['Radicali Italiani'],
        'astensione': ['Democratici di Sinistra', 'Democrazia è Libertà - La Margherita', 'Socialisti Democratici Italiani',
                       'Popolari-UDEUR'],
    },
    'nota_posizioni': "Per Forza Italia, AN, Lega Nord e UDC Wikipedia indica il No, mentre Il Post e l'Unità riportano che il "
                      "governo di centrodestra invitò all'astensione: le fonti divergono. Nei DS il Correntone votò contro la "
                      "linea dell'astensione.",
    'fonti': [W + 'Referendum_abrogativi_in_Italia_del_2003',
              'https://archivio.unita.news/assets/main/2003/06/12/page_008.pdf',
              'https://www.ilpost.it/2025/05/13/referendum-astensione-la-russa-tajani-cgil-astensionismo/'],
}

D['2005-06-12'] = {
    'cosa': "Quattro referendum abrogativi sulla legge 40/2004 sulla procreazione medicalmente assistita. Il Sì cancellava "
            "parti della legge: limiti alla ricerca sugli embrioni, limiti di accesso alle tecniche, norma sui diritti del "
            "concepito e divieto di fecondazione eterologa. Quorum mancato (25,6%), la legge restò com'era.",
    'quesiti': [
        "Sì: consentiva la ricerca clinica e sperimentale sugli embrioni, allora vietata",
        "Sì: toglieva limiti all'accesso (tra cui il tetto di tre embrioni e l'obbligo di impiantarli tutti)",
        "Sì: cancellava la norma che tutelava i diritti del concepito alla pari degli altri soggetti",
        "Sì: cancellava il divieto di fecondazione eterologa (con gameti di un donatore esterno alla coppia)",
    ],
    'posizioni': {
        'si': ['Democratici di Sinistra', 'Rifondazione Comunista', 'Partito dei Comunisti Italiani', 'Federazione dei Verdi',
               'Italia dei Valori', 'Radicali Italiani'],
        'astensione': ['Unione di Centro', 'Lega Nord', 'Popolari-UDEUR'],
        'liberta': ['Forza Italia', 'Alleanza Nazionale', 'Democrazia è Libertà - La Margherita'],
    },
    'nota_posizioni': "La CEI del cardinale Ruini fece campagna per l'astensione. Centrodestra diviso: Berlusconi non prese "
                      "posizione, Fini (AN) votò tre Sì e un No; Casini e Pera sostennero l'astensione. Nel centrosinistra Rutelli "
                      "(Margherita) scelse l'astensione.",
    'fonti': [W + 'Referendum_abrogativi_in_Italia_del_2005',
              'https://www.wantedinrome.com/news/political-fallout-from-fertility-referendum.html',
              'https://www.opendemocracy.net/en/religion-2626jsp/',
              'https://www.ilpost.it/2026/05/21/camillo-ruini-morto/'],
}

D['2006-06-25'] = {
    'cosa': "Referendum costituzionale confermativo sulla riforma della Seconda parte della Costituzione approvata dalla "
            "Casa delle Libertà: premier più forte, Senato federale, meno parlamentari, più competenze esclusive alle "
            "regioni (devolution su sanità, scuola, polizia locale). Prevalse il No (61,3%).",
    'posizioni': {
        'si': ['Forza Italia', 'Alleanza Nazionale', 'Lega Nord', 'Unione di Centro'],
        'no': ['Democratici di Sinistra', 'Democrazia è Libertà - La Margherita', 'Rifondazione Comunista',
               'Partito dei Comunisti Italiani', 'Federazione dei Verdi', 'Italia dei Valori', 'Popolari-UDEUR'],
    },
    'nota_posizioni': "Il Sì era sostenuto dal centrodestra che aveva approvato la riforma, il No dai partiti dell'Unione, "
                      "da poco al governo con Prodi.",
    'fonti': [W + 'Referendum_costituzionale_in_Italia_del_2006'],
}

D['2009-06-21'] = {
    'cosa': "Tre referendum abrogativi sulla legge elettorale del 2005 (Porcellum), promossi dal comitato Guzzetta-Segni. "
            "Il Sì dava il premio di maggioranza alla lista più votata invece che alla coalizione, alla Camera e al "
            "Senato, e vietava le candidature multiple. Quorum mancato (23,5%).",
    'quesiti': [
        "Sì: alla Camera il premio di maggioranza andava alla lista più votata, non più alla coalizione",
        "Sì: al Senato i premi regionali andavano alla lista più votata, non più alla coalizione",
        "Sì: vietava di candidarsi in più circoscrizioni contemporaneamente",
    ],
    'posizioni': {
        'si': ['Partito Democratico'],
        'no': ['Italia dei Valori', 'Radicali Italiani'],
        'astensione': ['Lega Nord', 'Unione di Centro', 'Rifondazione Comunista'],
        'liberta': ['Il Popolo della Libertà'],
    },
    'nota_posizioni': "I partiti minori, penalizzati dal premio alla lista, si opposero; Sinistra e Libertà oscillò tra No e "
                      "non voto. Nel PdL Fini annunciò il Sì, ma il partito non fece campagna per non urtare la Lega.",
    'fonti': [W + 'Referendum_abrogativi_in_Italia_del_2009'],
}

pq, prev, misti = tabella([
    ('Partito Democratico', 'S S S S'),
    ('Il Popolo della Libertà', 'A A A A'),
    ('Lega Nord', 'L L L L'),
    ('Italia dei Valori', 'S S S S'),
    ('Unione di Centro', 'N N L -'),
    ('Futuro e Libertà per l\'Italia', 'L L L L'),
    ('Sinistra Ecologia Libertà', 'S S S S'),
    ('Federazione della Sinistra', 'S S S S'),
    ('Movimento 5 Stelle', 'S S S S'),
], 4)
D['2011-06-12'] = {
    'cosa': "Quattro referendum abrogativi: due sull'acqua (promossi dai movimenti per l'acqua pubblica), uno sul ritorno "
            "al nucleare e uno sul legittimo impedimento (promossi dall'IdV). Il Sì cancellava le norme in vigore. "
            "Primo quorum raggiunto dal 1995 (54,8%): vinse il Sì con oltre il 94%.",
    'quesiti': [
        "Sì: cancellava le norme che obbligavano ad affidare i servizi pubblici locali (come l'acqua) con gara o a privati",
        "Sì: toglieva dalla tariffa dell'acqua la «remunerazione del capitale investito»",
        "Sì: cancellava le norme per costruire nuove centrali nucleari in Italia",
        "Sì: aboliva il legittimo impedimento di premier e ministri a comparire alle udienze",
    ],
    'posizioni': prev,
    'posizioni_quesiti': pq,
    'nota_posizioni': nota("Il PdL invitò a non votare e Berlusconi annunciò che non sarebbe andato alle urne. Sul quarto "
                           "quesito l'UDC è indicata per il Sì da Wikipedia e per la libertà di voto dai Quaderni "
                           "dell'Osservatorio elettorale.", misti),
    'fonti': [W + 'Referendum_abrogativi_in_Italia_del_2011',
              'https://oaj.fupress.net/index.php/qoe/article/download/9786/8753',
              'https://www.ilpost.it/2025/05/13/referendum-astensione-la-russa-tajani-cgil-astensionismo/'],
}

D['2016-04-17'] = {
    'cosa': "Referendum abrogativo chiesto da nove consigli regionali, detto «sulle trivelle». Il Sì faceva scadere alla fine "
            "della concessione le estrazioni di gas e petrolio già attive entro 12 miglia dalla costa, invece di farle "
            "durare fino all'esaurimento del giacimento. Quorum mancato (31,2%).",
    'posizioni': {
        'si': ['Movimento 5 Stelle', 'Lega Nord', "Fratelli d'Italia", 'Sinistra Italiana - SEL'],
        'astensione': ['Partito Democratico'],
    },
    'nota_posizioni': "Il governo Renzi invitò all'astensione, ma la minoranza PD e alcuni presidenti di regione PD che avevano "
                      "promosso il voto (come Emiliano) sostennero il Sì. Forza Italia e NCD non diedero un'indicazione "
                      "ufficiale (in NCD prevaleva l'astensione).",
    'fonti': [W + 'Referendum_abrogativo_in_Italia_del_2016',
              'https://www.ilpost.it/2016/04/11/referendum-trivellazioni-voto-partiti/'],
}

D['2016-12-04'] = {
    'cosa': "Referendum costituzionale confermativo sulla riforma Renzi-Boschi: fine del bicameralismo paritario, Senato "
            "ridotto a 100 membri scelti tra consiglieri regionali e sindaci, abolizione del CNEL, revisione dei poteri "
            "delle regioni. Prevalse il No (59,1%) e Renzi si dimise.",
    'posizioni': {
        'si': ['Partito Democratico', 'Nuovo Centrodestra', 'ALA (Verdini)', 'Scelta Civica'],
        'no': ['Movimento 5 Stelle', 'Forza Italia', 'Lega Nord', "Fratelli d'Italia", 'Sinistra Italiana - SEL'],
    },
    'nota_posizioni': "La minoranza del PD (Bersani, D'Alema) fece campagna per il No; l'UDC scelse il No mentre Casini "
                      "sostenne il Sì. Per il Sì CISL e Confindustria, per il No CGIL e ANPI.",
    'fonti': [W + 'Referendum_costituzionale_in_Italia_del_2016',
              'https://www.agcom.it/sites/default/files/migration/documento_generico/Documento%20generico%2025-10-2016.pdf',
              'https://www.dire.it/18-07-2016/65881-strappo-delludc-centristi-verso-no-al-referendum/'],
}

D['2020-09-20'] = {
    'cosa': "Referendum costituzionale confermativo sulla riduzione dei parlamentari voluta dal M5S: il Sì confermava il "
            "taglio dei deputati da 630 a 400 e dei senatori elettivi da 315 a 200. Si votò con le regionali, dopo il "
            "rinvio per la pandemia. Vinse il Sì con il 70%.",
    'posizioni': {
        'si': ['Movimento 5 Stelle', 'Partito Democratico', 'Lega', "Fratelli d'Italia"],
        'no': ['Azione', '+Europa', 'Sinistra Italiana'],
        'liberta': ['Forza Italia', 'Italia Viva', 'Articolo Uno'],
    },
    'nota_posizioni': "Nel PD (Prodi, Veltroni) e nella Lega (Giorgetti) diversi esponenti votarono No; in Forza Italia "
                      "Berlusconi criticò la riforma. Il referendum fu chiesto da 71 senatori.",
    'fonti': [W + 'Referendum_costituzionale_in_Italia_del_2020',
              'https://www.fanpage.it/politica/referendum-2020-chi-vota-si-e-chi-no-le-posizioni-dei-partiti-sul-taglio-dei-parlamentari/'],
}

pq, prev, misti = tabella([
    ('Lega', 'S S S S S'),
    ('Forza Italia', 'S S S S S'),
    ("Fratelli d'Italia", 'N N S S S'),
    ('Partito Democratico', 'N N N N N', {'N': ' (con libertà di voto)'}),
    ('Movimento 5 Stelle', 'N N N N N'),
    ('Italia Viva', 'S S S S S'),
    ('Azione', 'S S S S S'),
    ('+Europa', 'S S S S S'),
    ('Sinistra Italiana', 'N N N N N'),
    ('Articolo Uno', 'L L L L L'),
], 5)
D['2022-06-12'] = {
    'cosa': "Cinque referendum abrogativi sulla giustizia chiesti da nove consigli regionali di centrodestra, su iniziativa "
            "di Lega e Partito Radicale: legge Severino, custodia cautelare, funzioni dei magistrati, consigli giudiziari, "
            "elezione del CSM. Affluenza minima storica (20,9%), quorum mancato.",
    'quesiti': [
        "Sì: aboliva la legge Severino (incandidabilità e decadenza automatica dopo una condanna)",
        "Sì: limitava la custodia cautelare motivata dal rischio che l'indagato ripeta il reato",
        "Sì: il magistrato sceglieva una volta per tutte se fare il giudice o il pubblico ministero",
        "Sì: avvocati e professori dei consigli giudiziari potevano votare sulle valutazioni dei magistrati",
        "Sì: abolito l'obbligo di raccogliere firme per candidarsi al CSM",
    ],
    'posizioni': prev,
    'posizioni_quesiti': pq,
    'nota_posizioni': nota("Fratelli d'Italia indicò il Sì solo su tre quesiti (No su Severino e custodia cautelare). "
                           "Il PD era ufficialmente per il No ma lasciò libertà di voto.", misti),
    'fonti': [W + 'Referendum_abrogativi_in_Italia_del_2022',
              'https://tg24.sky.it/politica/2022/06/03/referendum-12-giugno-partiti'],
}

pq, prev, misti = tabella([
    ("Fratelli d'Italia", 'A A A A A'),
    ('Partito Democratico', 'S S S S S'),
    ('Lega', 'A A A A A'),
    ('Movimento 5 Stelle', 'S S S S L'),
    ('Forza Italia', 'A A A A A'),
    ('Alleanza Verdi e Sinistra', 'S S S S S'),
    ('Italia Viva', 'N N N L S'),
    ('Azione', 'N N N N S'),
    ('Noi Moderati', 'N N N N N'),
    ('+Europa', 'N N N S S'),
], 5)
D['2025-06-08'] = {
    'cosa': "Cinque referendum abrogativi: quattro sul lavoro promossi dalla CGIL (licenziamenti, contratti a termine, "
            "sicurezza negli appalti) e uno sulla cittadinanza promosso da +Europa e altri. Il Sì cancellava le norme "
            "in vigore. Affluenza del 30%, quorum mancato.",
    'quesiti': [
        "Sì: aboliva il contratto a tutele crescenti del Jobs Act, tornando al reintegro per i licenziamenti illegittimi",
        "Sì: toglieva il tetto all'indennizzo per i licenziamenti illegittimi nelle imprese sotto i 16 dipendenti",
        "Sì: obbligo di una causale anche per i contratti a termine sotto i 12 mesi",
        "Sì: il committente rispondeva insieme all'appaltatore degli infortuni sul lavoro negli appalti",
        "Sì: dimezzava da 10 a 5 anni la residenza legale richiesta agli stranieri per chiedere la cittadinanza",
    ],
    'posizioni': prev,
    'posizioni_quesiti': pq,
    'nota_posizioni': nota("I partiti di governo invitarono all'astensione; Meloni andò al seggio senza ritirare le "
                           "schede. Nel PD l'area riformista si dichiarò a favore solo degli ultimi due quesiti; sulla "
                           "cittadinanza il M5S lasciò libertà di voto (Conte annunciò il Sì). Italia Viva, Azione e "
                           "+Europa (tra i promotori) indicarono il Sì sulla cittadinanza.", misti),
    'fonti': [W + 'Referendum_abrogativi_in_Italia_del_2025',
              'https://tg24.sky.it/politica/2025/05/06/referendum-giugno-2025-posizioni-partiti'],
}

D['2026-03-22'] = {
    'cosa': "Referendum costituzionale confermativo sulla riforma della giustizia del governo Meloni (riforma Nordio): "
            "separazione delle carriere di giudici e pubblici ministeri, due CSM con membri estratti a sorte e un'Alta "
            "Corte disciplinare. Non c'era quorum; prevalse il No (53,2%).",
    'posizioni': {
        'si': ["Fratelli d'Italia", 'Lega', 'Forza Italia', 'Noi Moderati', 'Azione', '+Europa'],
        'no': ['Partito Democratico', 'Movimento 5 Stelle', 'Alleanza Verdi e Sinistra'],
        'liberta': ['Italia Viva'],
    },
    'nota_posizioni': "Nel PD alcuni esponenti (come Pina Picierno) votarono Sì; l'Associazione nazionale magistrati fece "
                      "campagna per il No. La SVP lasciò libertà di voto, con la maggior parte del partito per il Sì.",
    'fonti': [W + 'Referendum_costituzionale_in_Italia_del_2026',
              'https://www.fanpage.it/politica/chi-vota-si-e-chi-vota-no-al-referendum-sulla-giustizia-2026-la-posizione-dei-partiti-sul-quesito/',
              'https://tg24.sky.it/politica/approfondimenti/referendum-giustizia-2026-quando-si-vota'],
}

# ----------------------------------------------------- REGIONALI/PROVINCIALI

D['R06-2002-09-29'] = {
    'cosa': "Referendum confermativo sulla legge elettorale e di forma di governo approvata nel 2002: proporzionale con "
            "premio e soglia del 4%, presidente «indicato» dagli elettori ma eletto dal Consiglio. Vinse il No (73%): "
            "la legge non entrò in vigore e dal 2003 il presidente fu eletto direttamente.",
    'posizioni': {
        'si': ['Casa delle Libertà (centrodestra)', 'Rifondazione Comunista'],
        'no': ["L'Ulivo (centrosinistra)"],
    },
    'nota_posizioni': "La legge era stata votata in Consiglio regionale dal centrodestra e da Rifondazione Comunista.",
    'fonti': [W + 'Referendum_confermativo_in_Friuli-Venezia_Giulia_del_2002',
              'https://oaj.fupress.net/index.php/qoe/article/download/12747/10577/36458'],
}

D['R05-2002-10-06'] = {
    'cosa': "Referendum abrogativo regionale sulla legge veneta del 2001 sul buono-scuola (giunta Galan), un contributo "
            "alle famiglie con rette o spese di iscrizione oltre 300.000 lire, andato soprattutto agli alunni delle "
            "scuole paritarie. Il Sì aboliva la legge. Quorum mancato (21%).",
    'posizioni': {
        'si': ['Rifondazione Comunista', 'Comunisti Italiani', 'Verdi', 'Socialisti Democratici Italiani'],
        'no': ['La Margherita'],
    },
    'nota_posizioni': "I partiti di sinistra promossero il voto con CGIL, Cobas e associazioni della scuola pubblica; il "
                      "centrodestra non si pronunciò e Galan lo definì inutile; la Chiesa e i movimenti cattolici invitarono "
                      "all'astensione.",
    'fonti': [W + 'Referendum_abrogativo_in_Veneto_del_2002'],
}

D['R04TN-2007-09-30'] = {
    'cosa': "Referendum abrogativo provinciale, promosso dalla UIL scuola, su parti della riforma della scuola trentina del "
            "2006 (legge provinciale 5/2006): il Sì cancellava le norme sul finanziamento alle scuole paritarie e sulla "
            "composizione degli organi collegiali. Quorum mancato (18,9%).",
    'posizioni': {
        'si': ['Rifondazione Comunista', 'Leali al Trentino', 'Socialisti Democratici Italiani'],
        'no': ['PATT'],
        'astensione': ['Civica Margherita', 'Forza Italia', 'Unione di Centro', 'Lega Nord', 'Alleanza Nazionale', 'UDEUR'],
        'liberta': ['Democratici di Sinistra', 'Federazione dei Verdi'],
    },
    'fonti': [W + 'Referendum_abrogativo_nella_provincia_autonoma_di_Trento_del_2007'],
}

D['R20-2007-10-21'] = {
    'cosa': "Referendum confermativo sulla legge statutaria della Sardegna, proposta dalla giunta Soru e approvata dal "
            "Consiglio nel marzo 2007: regole su referendum, poteri di giunta, consiglio e presidente, conflitto di "
            "interessi, incompatibilità. Il Sì la confermava. Affluenza del 15,7%.",
    'posizioni': {
        'no': ['Centrodestra (opposizione in Consiglio regionale)'],
    },
    'nota_posizioni': "Il referendum fu chiesto da 19 consiglieri dell'opposizione di centrodestra, contraria alla legge. "
                      "Mancato il quorum di un terzo, la Corte costituzionale (sent. 149/2009) annullò poi la promulgazione.",
    'fonti': ['https://giurcost.org/decisioni/2009/0149s-09.html',
              'https://regione.emilia-romagna.it/idf/numeri/2009/1_2009/97-seddone-venturino.pdf/@@download/file',
              'https://www.forumcostituzionale.it/wordpress/images/stories/pdf/documenti_forum/paper/0113_sias.pdf'],
}

D['R02-2007-11-18'] = {
    'cosa': "Cinque referendum propositivi su proposte di legge di iniziativa popolare: preferenza unica, elezione diretta "
            "della giunta, alleanze dichiarate prima del voto, parità di genere nelle liste, nuovo ospedale unico. "
            "Il Sì le approvava. Affluenza 27,6%, sotto il quorum del 45%.",
    'quesiti': [
        "Sì: una sola preferenza invece di tre nell'elezione del Consiglio regionale",
        "Sì: elezione diretta della Giunta regionale da parte dei cittadini",
        "Sì: obbligo di dichiarare le alleanze politiche prima del voto",
        "Sì: regole per l'equilibrio tra donne e uomini nelle liste per il Consiglio",
        "Sì: un nuovo presidio ospedaliero unico per la regione",
    ],
    'posizioni': {
        'astensione': ["Maggioranza regionale guidata dall'Union Valdôtaine"],
    },
    'nota_posizioni': "I comitati promotori erano formati in prevalenza da militanti di partiti d'opposizione; alla scelta "
                      "astensionista della maggioranza si unirono anche forze formalmente d'opposizione.",
    'fonti': ['https://www.regione.vda.it/amministrazione/elezioni/Referendum2007/default_i.asp',
              'https://www.astrid-online.it/static/upload/protected/R_Lo/R_Louvin-referendum-propositivo-18_12_07.pdf'],
}

pq, prev, misti = tabella([
    ('Südtiroler Volkspartei', 'N N N N L'),
    ('Die Freiheitlichen', 'S S N S S'),
    ('Il Popolo della Libertà', 'S N N N N'),
    ('Partito Democratico', 'N N N S L'),
    ('Verdi-Grüne-Vërc', 'N N A S S'),
    ('Süd-Tiroler Freiheit', 'L L L S S'),
    ('Union für Südtirol', 'S S S S S'),
    ('Lega Nord', 'S L L L L'),
], 5)
D['R04BZ-2009-10-25'] = {
    'cosa': "Cinque referendum propositivi su leggi di iniziativa popolare: tre dell'Union für Südtirol (casa, seconde "
            "case, democrazia diretta), uno dell'Iniziativa per più democrazia e uno degli ambientalisti sull'aeroporto. "
            "Il Sì le approvava. Quorum del 40% mancato in tutti.",
    'quesiti': [
        "Sì: precedenza ai residenti di lungo periodo nell'edilizia abitativa agevolata",
        "Sì: limiti più stretti alle residenze per il tempo libero (seconde case) nella legge urbanistica",
        "Sì: nuova legge su referendum e iniziativa popolare, nella versione dell'Union für Südtirol",
        "Sì: nuova legge sulla democrazia diretta, nella versione dell'Iniziativa per più democrazia",
        "Sì: riduzione del traffico aereo e stop ai finanziamenti pubblici all'aeroporto di Bolzano",
    ],
    'posizioni': prev,
    'posizioni_quesiti': pq,
    'nota_posizioni': nota("La SVP, partito di maggioranza, era contraria ai primi quattro e lasciò libertà sul quinto, "
                           "promosso dalla Federazione ambientalisti Alto Adige.", misti),
    'fonti': [W + 'Referendum_propositivi_nella_provincia_autonoma_di_Bolzano_del_2009'],
}

D['R20-2011-05-15'] = {
    'cosa': "Referendum consultivo regionale promosso da Sardigna Natzione Indipendentzia, abbinato alle comunali: votare "
            "Sì significava dirsi contrari a centrali nucleari e a depositi di scorie radioattive in Sardegna. Precedette "
            "di un mese il referendum nazionale. Quorum raggiunto, Sì al 97%.",
    'posizioni': {
        'si': ['Sardigna Natzione Indipendentzia (promotore)', 'Partito Democratico', 'Italia dei Valori'],
    },
    'nota_posizioni': "La giunta di centrodestra di Ugo Cappellacci volle l'abbinamento con le amministrative e commentò "
                      "positivamente l'affluenza; nelle fonti consultate non risultano partiti schierati per il No.",
    'fonti': [W + 'Referendum_consultivo_in_Sardegna_del_2011',
              'https://www.greenme.it/news/approfondimenti/referendum-nucleare-sardegna/'],
}

D['R04TN-2012-04-29'] = {
    'cosa': "Referendum abrogativo provinciale promosso da un comitato guidato dalla Lega Nord: il Sì aboliva le 14 Comunità "
            "di valle, enti intermedi tra provincia e comuni istituiti dalla riforma del 2006 al posto dei comprensori. "
            "Quorum mancato (27,4%).",
    'posizioni': {
        'si': ['Lega Nord', 'Il Popolo della Libertà', 'Civica per Divina Presidente'],
        'no': ['Federazione dei Verdi'],
        'astensione': ['Unione per il Trentino', 'PATT'],
        'liberta': ['Italia dei Valori', 'Unione di Centro'],
    },
    'nota_posizioni': "Il Partito Democratico del Trentino oscillò tra No e astensione.",
    'fonti': [W + 'Referendum_abrogativo_nella_provincia_autonoma_di_Trento_del_2012'],
}

D['R20-2012-05-06'] = {
    'cosa': "Dieci referendum regionali, cinque abrogativi e cinque consultivi, detti «anticasta», promossi dal Movimento "
            "referendario sardo: abolizione delle province, indennità e numero dei consiglieri, statuto, elezione del "
            "presidente. Quorum di un terzo raggiunto (35,5%), vinse il Sì su tutti.",
    'quesiti': [
        "Sì (abrogativo): cancellava la legge regionale 4/1997 sul riassetto delle province",
        "Sì (abrogativo): cancellava la legge 10/2002 sugli adempimenti per le nuove province",
        "Sì (abrogativo): cancellava la delibera del 1999 che disegnava le nuove circoscrizioni provinciali",
        "Sì (abrogativo): aboliva le province di Carbonia-Iglesias, Medio Campidano, Ogliastra e Olbia-Tempio",
        "Sì (consultivo): favorevoli ad abolire anche le province storiche di Cagliari, Sassari, Nuoro e Oristano",
        "Sì (consultivo): favorevoli a un'assemblea costituente eletta per riscrivere lo Statuto sardo",
        "Sì (consultivo): favorevoli all'elezione diretta del presidente della Regione scelto con primarie",
        "Sì (abrogativo): cancellava la norma sulle indennità dei consiglieri regionali",
        "Sì (consultivo): favorevoli ad abolire i consigli di amministrazione di enti e agenzie regionali",
        "Sì (consultivo): favorevoli a ridurre a 50 i consiglieri regionali",
    ],
    'posizioni': {
        'si': ['Movimento referendario sardo (promotore)', 'Riformatori Sardi', 'Italia dei Valori'],
    },
    'nota_posizioni': "La maggior parte dei partiti non prese posizione ufficiale; si dissero favorevoli il presidente Ugo "
                      "Cappellacci (PdL) e Arturo Parisi (PD). L'Unione delle province sarde fece ricorso contro il voto.",
    'fonti': [W + 'Referendum_in_Sardegna_del_2012',
              'https://www.ilpost.it/2012/05/03/i-referendum-in-sardegna/',
              'https://www.linkiesta.it/2012/05/referendum-anticasta-in-sardegna-quorum-superato/'],
}

D['R02-2012-11-18'] = {
    'cosa': "Referendum propositivo su una legge di iniziativa popolare dell'associazione Valle Virtuosa: il Sì escludeva "
            "il trattamento a caldo dei rifiuti, fermando il pirogassificatore di Brissogne previsto dalla Regione. "
            "Quorum del 45% raggiunto (48,9%), Sì al 94%.",
    'posizioni': {
        'si': ['Valle Virtuosa (promotore)', 'Movimento 5 Stelle'],
    },
    'nota_posizioni': "La giunta regionale guidata da Augusto Rollandin (Union Valdôtaine) aveva avviato l'impianto e il "
                      "presidente criticò il referendum; nelle fonti consultate non ci sono indicazioni di voto ufficiali "
                      "degli altri partiti.",
    'fonti': ['https://www.regione.vda.it/amministrazione/elezioni/referendum2012/Default_i.asp?ele=108&p=1&f=0&Tipo=VR&L=I',
              'https://pagellapolitica.it/fact-checking/abbiamo-un-referendum-in-val-daosta-propositivo-senza-quorum-che-e-passato-per-togliere-un-inceneritore-che-viene-invalidato-0245',
              'https://www.montagna.tv/44602/la-valle-daosta-dice-no-allinceneritore/amp/'],
}

D['R04BZ-2014-02-09'] = {
    'cosa': "Referendum confermativo sulla legge provinciale sulla partecipazione civica, approvata nel 2013 con i soli voti "
            "della SVP: nuove regole per richiesta e iniziativa popolare e referendum, con esclusione di alcune materie. "
            "Il Sì la confermava. Vinse il No (65%); non c'era quorum.",
    'posizioni': {
        'si': ['Südtiroler Volkspartei'],
        'no': ['Die Freiheitlichen', 'Verdi-Grüne-Vërc', 'Süd-Tiroler Freiheit', 'Partito Democratico', 'Movimento 5 Stelle',
               'BürgerUnion', "L'Alto Adige nel cuore", 'Team Autonomie'],
    },
    'fonti': [W + 'Referendum_confermativo_nella_provincia_autonoma_di_Bolzano_del_2014'],
}

D['R04BZ-2016-06-12'] = {
    'cosa': "Referendum consultivo voluto dal Consiglio provinciale sul disegno di legge della giunta per l'aeroporto di "
            "Bolzano, che fissava obiettivi di sviluppo e un tetto ai finanziamenti pubblici. Il Sì era a favore della "
            "legge. Vinse il No (70,7%): la Provincia uscì dalla società dello scalo.",
    'posizioni': {
        'si': ['Südtiroler Volkspartei', 'Partito Democratico', 'Team Autonomie', "L'Alto Adige nel cuore", 'Lega Nord'],
        'no': ['Die Freiheitlichen', 'Verdi-Grüne-Vërc', 'Süd-Tiroler Freiheit', 'Movimento 5 Stelle', 'BürgerUnion'],
    },
    'fonti': [W + 'Referendum_consultivo_nella_provincia_autonoma_di_Bolzano_del_2016'],
}

D['R03-2017-10-22'] = {
    'cosa': "Referendum consultivo voluto dalla giunta Maroni (Lega) e dal Consiglio regionale: il Sì chiedeva alla Regione "
            "di trattare con lo Stato maggiore autonomia e risorse, come previsto dall'art. 116 della Costituzione. "
            "Senza quorum; affluenza 38%, Sì al 96%.",
    'posizioni': {
        'si': ['Lega Nord', 'Forza Italia', "Fratelli d'Italia", 'Movimento 5 Stelle', 'Lombardia Popolare',
               'Lista Maroni Presidente'],
        'astensione': ['Articolo 1 - MDP', 'Sinistra Italiana', 'Rifondazione Comunista'],
    },
    'nota_posizioni': "Il PD lombardo e la lista Patto Civico contestarono l'utilità e i costi del referendum, senza "
                      "un'indicazione netta tra Sì e astensione.",
    'fonti': [W + 'Referendum_consultivo_in_Lombardia_del_2017'],
}

D['R05-2017-10-22'] = {
    'cosa': "Referendum consultivo voluto dalla giunta Zaia (Lega) e dal Consiglio regionale: il Sì chiedeva che al Veneto "
            "fossero attribuite «ulteriori forme e condizioni particolari di autonomia», da negoziare con lo Stato. "
            "Quorum raggiunto (57,2%), Sì al 98%.",
    'posizioni': {
        'si': ['Liga Veneta - Lega Nord', 'Lista Zaia Presidente', 'Partito Democratico', 'Forza Italia', "Fratelli d'Italia",
               'Movimento 5 Stelle'],
        'no': ['Rifondazione Comunista'],
        'astensione': ['Articolo 1 - MDP', 'Sinistra Italiana'],
    },
    'nota_posizioni': "Tutti i gruppi del Consiglio regionale indicarono il Sì, tranne parte del gruppo misto "
                      "(astensione); il dibattito riguardò soprattutto utilità e costi della consultazione.",
    'fonti': [W + 'Referendum_consultivo_in_Veneto_del_2017'],
}

D['R04TN-2021-09-26'] = {
    'cosa': "Referendum propositivo provinciale chiesto da un comitato di cittadini con quasi 13.000 firme: il Sì impegnava "
            "la Provincia a fare di tutto il territorio agricolo trentino un distretto biologico, promuovendo l'agricoltura "
            "biologica. Quorum del 40% mancato (15,6%).",
    'posizioni': {
        'si': ['Futura', 'Movimento 5 Stelle', 'Onda Civica', 'Europa Verde'],
        'liberta': ['Lega', 'Partito Democratico', 'PATT', "Fratelli d'Italia", 'Forza Italia'],
    },
    'fonti': [W + 'Referendum_propositivo_nella_provincia_autonoma_di_Trento_del_2021'],
}

D['R04BZ-2022-05-29'] = {
    'cosa': "Referendum confermativo sulla legge della maggioranza SVP-Lega-Forza Italia (2021) che modificava le norme "
            "provinciali su democrazia diretta e Consiglio dei Comuni, tra cui l'abolizione dello stesso referendum "
            "confermativo. Il Sì la confermava. Vinse il No (76%).",
    'posizioni': {
        'si': ['Südtiroler Volkspartei', 'Lega', 'Forza Italia'],
        'no': ['Team K', 'Verdi-Grüne-Vërc', 'Die Freiheitlichen', 'Süd-Tiroler Freiheit', 'Partito Democratico',
               'Movimento 5 Stelle', "Fratelli d'Italia"],
    },
    'fonti': [W + 'Referendum_confermativo_nella_provincia_autonoma_di_Bolzano_del_2022'],
}

D['R02-2025-08-10'] = {
    'cosa': "Referendum confermativo sulla riforma elettorale regionale approvata dalla sola maggioranza nel febbraio 2025: "
            "reintroduceva fino a tre preferenze con regole per la rappresentanza di genere. Lo chiesero sette consiglieri "
            "della Lega. Vinse il Sì (52,1%); non c'era quorum.",
    'posizioni': {
        'si': ['Union Valdôtaine', 'Partito Democratico', "Valle d'Aosta Aperta"],
        'no': ['Alleanza Verdi e Sinistra - Rete Civica'],
        'liberta': ['Forza Italia', 'Rassemblement Valdôtain'],
    },
    'nota_posizioni': "La Lega, che aveva chiesto il referendum, è indicata tra libertà di voto e No.",
    'fonti': [W + "Referendum_confermativo_in_Valle_d%27Aosta_del_2025"],
}


def main():
    q = json.load(open(QUESITI, encoding='utf-8'))
    assert set(q) == set(D), ('chiavi diverse', set(q) ^ set(D))
    problemi = []
    out = {}
    for k in q:  # stesso ordine di quesiti.json
        d = D[k]
        n = len(q[k]['quesiti'])
        if n > 1:
            assert len(d.get('quesiti', [])) == n, (k, 'righe quesiti', len(d.get('quesiti', [])), n)
        else:
            assert 'quesiti' not in d, (k, 'quesito singolo con campo quesiti')
        if 'posizioni_quesiti' in d:
            assert len(d['posizioni_quesiti']) == n, (k, 'posizioni_quesiti')
        if not 200 <= len(d['cosa']) <= 360:
            problemi.append(f"{k}: cosa {len(d['cosa'])} caratteri")
        for i, r in enumerate(d.get('quesiti', []), 1):
            if len(r) > 120:
                problemi.append(f'{k}: quesito {i} {len(r)} caratteri')
        if len(d.get('nota_posizioni', '')) > 360:
            problemi.append(f"{k}: nota {len(d['nota_posizioni'])} caratteri")
        e = {'cosa': d['cosa']}
        for campo in ('quesiti', 'posizioni', 'posizioni_quesiti', 'nota_posizioni', 'fonti'):
            if campo in d:
                e[campo] = d[campo]
        out[k] = e
    with open(USCITA, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(f'{len(out)} chiavi scritte in {USCITA}')
    for p in problemi:
        print('  avviso:', p)


if __name__ == '__main__':
    main()
