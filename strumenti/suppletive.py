"""Elezioni suppletive della Camera dei deputati e del Senato dal 1994 a oggi (strumenti/suppletive.json).

Le suppletive si tengono quando si libera un seggio eletto in un collegio uninominale: con la legge Mattarella
(collegi del 1993, d.lgs. 535/1993 per il Senato e 536/1993 per la Camera, usati nelle legislature XII, XIII e
XIV, 1994-2006) e con la legge Rosato (collegi del 2017, d.lgs. 189/2017, nella XVIII legislatura; collegi del
2020, d.lgs. 177/2020, dalla XIX dopo il taglio dei parlamentari). Dal 2006 al 2018 (legislature XV, XVI e
XVII, legge Calderoli) non ce ne furono: il sistema era proporzionale e i seggi vacanti andavano al primo dei non
eletti della lista; restavano uninominali solo la Valle d'Aosta e i collegi senatoriali del Trentino-Alto Adige,
dove però nessun seggio si liberò (le tabelle «Modifiche intervenute» delle pagine «Deputati/Senatori della XV,
XVI e XVII legislatura» non registrano suppletive).

L'elenco delle suppletive è fissato a mano qui sotto (SUPPLETIVE) ed è stato ricostruito da it.wikipedia.org:
«Elezioni politiche suppletive in Italia» (tabella riassuntiva), le pagine «Elezioni politiche suppletive in Italia
del AAAA» e, per controllo, le tabelle «Modifiche intervenute» delle pagine «Deputati della ... legislatura» e
«Senatori della ... legislatura» (XII, XIII, XIV, XVIII, XIX), che per ogni subentro in un collegio uninominale
indicano la suppletiva. Le suppletive non ancora votate (per esempio Abruzzo - 01, Chieti, 15-16 novembre 2026)
restano fuori finché non c'è il risultato: per aggiungerle basta una voce in SUPPLETIVE.

Per ogni suppletiva lo script legge dalla pagina dell'anno, nella sezione del collegio:
  - candidati e voti dal riquadro {{Elezione uninominale}} o dalla tabella (2005): la percentuale è calcolata sui
    voti validi ai candidati, come fa il Modulo:Risultati; il partito è il testo della lista come sulla pagina;
  - affluenza = votanti / elettori del riquadro (quando la pagina li riporta);
  - l'elenco dei comuni del collegio dalla frase «Il collegio è formato da ...».
Lo stesso elenco si legge anche dalla sezione «Territorio» della pagina del collegio («Collegio elettorale di ...»
per il 1993, «Collegio uninominale ...» per il 2017 e il 2020; per i collegi del Senato che esistevano già prima
del 1993 la sezione «Dal 1993 al 2005»): i due elenchi devono coincidere, salvo le differenze spiegate in
'sostituisci' (comuni nati da fusioni dopo il decreto o rinominati). Se non coincidono lo script si ferma.
Per alcune suppletive 'verifica' indica una fonte indipendente (Quaderni dell'Osservatorio elettorale, l'Unità,
giornali) che conferma data e risultato. Data, vincitore e numero dei candidati di ogni suppletiva sono stati controllati anche con la tabella riassuntiva
e con le date di subentro delle tabelle «Modifiche intervenute»; dove le pagine si contraddicono (data nel testo
diversa da quella del riquadro) vale la data confermata dal subentro, ed è detto in 'note'.

I comuni sono quelli esistenti il giorno del voto, con il codice catastale di dati/comuni.js (nome, sigla, regione,
codice, attivo, nomi precedenti): si cercano per nome, nomi precedenti compresi, nelle regioni del collegio;
'sostituisci' converte i nomi della pagina in quelli in vigore alla data (per esempio Porto Viro, nato nel 1995 da
Contarina e Donada, o Ville di Fiemme, nato nel 2020 da Carano, Daiano e Varena). "parziale": true se il comune era
diviso tra più collegi (le grandi città): votava solo una parte dei suoi elettori, indicata in 'zona' quando la
pagina dice quali quartieri. L'area del candidato (sinistra, centrosinistra, centro, centrodestra, destra, altro)
segue lo schieramento con cui si presentava in quella suppletiva, con gli stessi criteri di dati/partiti.js
(per esempio la Lega Nord fuori dai poli nel 1996-2000 e il M5S da solo sono 'altro'); null se incerta.

Si lancia a mano (servono solo la libreria standard e l'accesso a it.wikipedia.org):
    python strumenti/suppletive.py [CARTELLA]
CARTELLA tiene le pagine scaricate in wikitext (index.php?title=...&action=raw), una per file con _ al posto degli
spazi; quelle che mancano vengono scaricate con una pausa di almeno un secondo tra una richiesta e l'altra.
"""
import os, re, sys, json, time, tempfile, unicodedata, urllib.request, urllib.parse

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIKI = 'https://it.wikipedia.org/wiki/'
UA = 'la-mia-storia-di-voto (github.com/angrisanidj/la-mia-storia-di-voto)'
PAUSA = 1.5
ANNO = 'Elezioni politiche suppletive in Italia del '

# Regioni ISTAT: 03 Lombardia, 05 Veneto, 06 Friuli-Venezia Giulia, 07 Liguria, 08 Emilia-Romagna, 09 Toscana,
# 10 Umbria, 11 Marche, 12 Lazio, 15 Campania, 16 Puglia, 17 Basilicata, 18 Calabria, 20 Sardegna, 04 Trentino-AA.
CSX, CDX, SX, DX, CEN, ALT = 'centrosinistra', 'centrodestra', 'sinistra', 'destra', 'centro', 'altro'

# Una voce per suppletiva. sez = (ramo nella pagina dell'anno, titolo della sezione del collegio);
# coll = pagina del collegio; parziali = {comune: zona}; aree = {cognome: area}; sostituisci = {nome sulla pagina:
# [nomi alla data del voto]}; prov = sigle di province intere comprese nel collegio (comuni attivi oggi, controllati).
SUPPLETIVE = [
    # ---------------- XII legislatura (1994-1996), collegi del 1993 ----------------
    dict(d='1994-09-11', ramo='S', leg='XII', collegio='Toscana - 6 (Pistoia)', sez=('Senato', 'Collegio Toscana - 6'),
         coll='Collegio elettorale di Pistoia (Senato della Repubblica)', reg=['09'],
         soppressi=['Abetone', 'Cutigliano', 'Piteglio', 'San Marcello Pistoiese'],
         aree={'Gallo': CSX, 'Panati': CDX}),
    dict(d='1995-04-09', ramo='C', leg='XII', collegio='Veneto 1 - 14 (Padova - Selvazzano Dentro)', sez=('Camera', 'Collegio Veneto 1 - 14'),
         coll='Collegio elettorale di Padova - Selvazzano Dentro (Camera dei deputati)', reg=['05'], parziali={'Padova': None},
         aree={'Saonara': CSX, 'Negri': CDX},
         note='Saonara era sostenuto da Lega Nord, PPI, PDS e dagli altri partiti progressisti (lista «Federalismo e Democrazia»).'),
    dict(d='1995-05-14', ramo='C', leg='XII', collegio='Emilia-Romagna - 8 (Ravenna - Lugo)', sez=('Camera', 'Collegio Emilia-Romagna - 8'),
         coll='Collegio elettorale di Ravenna - Lugo', reg=['08'], parziali={'Ravenna': None},
         aree={'Signorino': CSX, 'Brini': CEN}),
    dict(d='1995-05-14', ramo='S', leg='XII', collegio='Calabria - 3 (Cosenza)', sez=('Senato', 'Collegio Calabria - 3'),
         coll='Collegio elettorale di Cosenza (Senato della Repubblica)', reg=['18'], sostituisci={'Maligo': ['Malito']},
         soppressi=['Casole Bruzio', 'Pedace', 'Serra Pedace', 'Spezzano Piccolo', 'Trenta'],
         aree={'Veltri': CSX, 'Zupo': CDX, 'Petramala': CEN}),
    dict(d='1995-10-22', ramo='C', leg='XII', collegio='Campania 1 - 2 (Napoli - Vomero)', sez=('Camera', 'Collegio Campania 1 - 2'),
         coll='Collegio elettorale di Napoli - Vomero', reg=['15'], parziali={'Napoli': 'Chiaia, Posillipo, Vomero'},
         aree={'Siniscalchi': CSX, 'de Tilla': CDX, 'Pannella': ALT, 'Vitale': DX, 'Visconti': ALT, 'Vestuto': ALT}),
    dict(d='1996-01-14', ramo='C', leg='XII', collegio='Puglia - 4 (Foggia centro)', sez=('Camera', 'Collegio Puglia - 4'),
         coll='Collegio elettorale di Foggia centro', reg=['16'],
         parziali={'Foggia': 'Cattedrale, Centrale, Ferrovia, Puglia, Mazzini, CEP, Incoronata'},
         aree={'Pepe': CDX, 'Cavaliere': CSX}),
    # ---------------- XIII legislatura (1996-2001) ----------------
    dict(d='1996-10-27', ramo='S', leg='XIII', collegio='Emilia-Romagna - 3 (Ravenna)', sez=('Senato', 'Collegio Emilia-Romagna - 3'),
         coll='Collegio elettorale di Ravenna (Senato della Repubblica)', reg=['08'],
         soppressi=['Massa Fiscaglia', 'Migliarino', 'Migliaro', 'Tresigallo'],
         aree={'Preda': CSX, "D'Amico": CDX}),
    dict(d='1997-06-01', ramo='C', leg='XIII', collegio='Lombardia 2 - 3 (Tradate)', sez=('Camera', 'Collegio Lombardia 2 - 3'),
         coll='Collegio elettorale di Tradate (Camera dei deputati)', reg=['03'],
         aree={'Galli': ALT, 'Luini': CSX, 'Valmori': CDX, 'Piacentini': None, 'Biotti': DX},
         note='Lega Nord fuori dai poli; Piacentini (Socialisti Italiani e Partito Socialista) senza area certa.'),
    dict(d='1997-11-09', ramo='S', leg='XIII', collegio='Toscana - 3 (Sesto Fiorentino)', sez=('Senato', 'Collegio Toscana - 3'),
         coll='Collegio elettorale di Sesto Fiorentino (Senato della Repubblica)', reg=['09'],
         soppressi=['Castelfranco di Sopra', 'Pian di Scò', 'San Piero a Sieve', 'Scarperia'],
         aree={'Di Pietro': CSX, 'Ferrara': CDX, 'Curzi': SX, 'Checacci': ALT},
         verifica='https://archivio.unita.news/assets/main/1997/11/10/page_005.pdf',
         note='L\'Unità del 10 novembre 1997 scrive «Checcacci». La tabella riassuntiva di Wikipedia numera il collegio 4: è il 3 (Collegi elettorali del Senato della Repubblica del 1993).'),
    dict(d='1997-12-14', ramo='S', leg='XIII', collegio='Friuli-Venezia Giulia - 2 (Gorizia)', sez=('Senato', 'Collegio Friuli-Venezia Giulia - 2'),
         coll='Collegio elettorale di Gorizia (Senato della Repubblica)', reg=['06'],
         soppressi=['Campolongo al Torre', 'Fiumicello', 'Tapogliano', 'Villa Vicentina'],
         aree={'Volcic': CSX, 'Mulitsch': CDX}),
    dict(d='1998-06-21', ramo='C', leg='XIII', collegio='Lombardia 1 - 6 (Milano 6)', sez=('Camera', 'Collegio Lombardia 1 - 6'),
         coll='Collegio elettorale di Milano 6', reg=['03'], parziali={'Milano': None},
         aree={'Pecorella': CDX, 'Mattioni': CSX, 'Bernardelli': ALT, 'Pannella': ALT, 'Ghezzi': SX, 'Schultze': ALT, 'Cartolari': DX}),
    dict(d='1999-05-09', ramo='C', leg='XIII', collegio='Puglia - 20 (Bari - Libertà - Marconi)', sez=('Camera', 'Collegio Puglia - 20'),
         coll='Collegio elettorale di Bari - Libertà - Marconi', reg=['16'],
         parziali={'Bari': 'Libertà, Marconi, Murat, Picone, Poggiofranco, San Nicola'},
         aree={'Tatarella': CDX, 'Tedesco': CSX, 'Diomede': ALT}),
    dict(d='1999-05-09', ramo='S', leg='XIII', collegio='Veneto - 4 (Treviso)', sez=('Senato', 'Collegio Veneto - 4'),
         coll='Collegio elettorale di Treviso (Senato della Repubblica)', reg=['05'],
         scarta_anno='La pagina delle suppletive del 1999 riporta i 20 comuni del collegio del 1948-1993; vale l\'elenco del 1993 della '
                     'pagina del collegio (16 comuni, con Altivole e Mogliano Veneto), confermato dalle pagine dei collegi vicini del 1993: '
                     'Carbonera, Roncade, Silea e Villorba erano nel collegio di Conegliano, Ponzano Veneto e Povegliano in quello di Vittorio Veneto.',
         aree={'Stiffoni': ALT, 'Pasqualetti': CDX, 'Casotto': CSX, 'Contin': ALT, 'Dogà': ALT}),
    dict(d='1999-05-09', ramo='S', leg='XIII', collegio='Emilia-Romagna - 1 (Forlì)', sez=('Senato', 'Collegio Emilia-Romagna - 1'),
         coll='Collegio elettorale di Forlì (Senato della Repubblica)', reg=['08'],
         aree={'Manzella': CSX, 'Ridolfi': CDX, 'Monti': ALT}),
    dict(d='1999-06-27', ramo='C', leg='XIII', collegio='Lombardia 2 - 24 (Brescia - Flero)', sez=('Camera', 'Collegio Lombardia 2 - 24'),
         coll='Collegio elettorale di Brescia - Flero', reg=['03'], parziali={'Brescia': None},
         aree={'Rebecchi': CSX, 'Bontempi': CDX, 'Orizio': ALT, 'Manzoni': ALT}),
    dict(d='1999-06-27', ramo='C', leg='XIII', collegio='Puglia - 7 (Lecce)', sez=('Camera', 'Collegio Puglia - 7'),
         coll='Collegio elettorale di Lecce (Camera dei deputati)', reg=['16'],
         aree={'Casilli': CSX, 'Siciliano': CDX}),
    dict(d='1999-06-27', ramo='S', leg='XIII', collegio='Puglia - 7 (Lecce)', sez=('Senato', 'Collegio Puglia - 7'),
         coll='Collegio elettorale di Lecce (Senato della Repubblica)', reg=['16'],
         aree={'Maritati': CSX, 'Camilli': CDX},
         note='Il riquadro della pagina indica il 9 maggio 1999, ma Lisi morì il 20 aprile e il testo dice 27 giugno; '
              'il subentro di Maritati è del 30 giugno 1999 (Senatori della XIII legislatura).'),
    dict(d='1999-11-28', ramo='C', leg='XIII', collegio='Emilia-Romagna - 12 (Bologna - Mazzini)', sez=('Camera', 'Collegio Emilia Romagna - 12'),
         coll='Collegio elettorale di Bologna - Mazzini', reg=['08'], parziali={'Bologna': 'Galvani, Murri, San Vitale, Mazzini'},
         verifica='https://oaj.fupress.net/index.php/qoe/article/download/12787/10643',
         aree={'Parisi': CSX, 'Tura': CDX, 'Loreti': SX, 'Banasiak': ALT, 'Busin': ALT},
         note='La pagina dà date diverse (16 settembre nel testo, 27 giugno nel riquadro): Prodi si dimise il 16 settembre 1999, '
              'la tabella riassuntiva indica il 28 novembre e il subentro di Parisi è del 2 dicembre 1999 (Deputati della XIII legislatura).'),
    dict(d='1999-11-28', ramo='C', leg='XIII', collegio='Toscana - 8 (Bagno a Ripoli)', sez=('Camera', 'Collegio Toscana - 8'),
         coll='Collegio elettorale di Bagno a Ripoli (Camera dei deputati)', reg=['09'],
         soppressi=["Barberino Val d'Elsa", 'Figline Valdarno', "Incisa in Val d'Arno", 'Tavarnelle Val di Pesa'],
         verifica='https://oaj.fupress.net/index.php/qoe/article/download/12787/10643',
         aree={'Ventura': CSX, 'Bosi': CDX, 'Barbagli': SX, 'Vennarini': ALT}),
    dict(d='1999-11-28', ramo='C', leg='XIII', collegio='Umbria - 6 (Terni)', sez=('Camera', 'Collegio Umbria - 6'),
         coll='Collegio elettorale di Terni (Camera dei deputati)', reg=['10'],
         verifica='https://oaj.fupress.net/index.php/qoe/article/download/12787/10643',
         aree={'Micheli': CSX, 'Melasecche Germini': CDX, 'Botondi': SX},
         note='La pagina indica il 27 giugno 1999, ma Raffaelli si dimise il 10 settembre 1999: la tabella riassuntiva indica il 28 novembre '
              'e il subentro di Micheli è del 2 dicembre 1999 (Deputati della XIII legislatura).'),
    dict(d='1999-11-28', ramo='C', leg='XIII', collegio='Basilicata - 5 (Lauria)', sez=('Camera', 'Collegio Basilicata - 5'),
         coll='Collegio elettorale di Lauria (Camera dei deputati)', reg=['17'],
         verifica='https://oaj.fupress.net/index.php/qoe/article/download/12787/10643',
         aree={'Luongo': CSX, 'Sisinni': CDX}),
    dict(d='1999-11-28', ramo='S', leg='XIII', collegio='Marche - 6 (Pesaro)', sez=('Senato', 'Collegio Marche - 6'),
         coll='Collegio elettorale di Pesaro (Senato della Repubblica)', reg=['11', '08'],
         soppressi=['Auditore', 'Colbordolo', 'Monteciccardo', "Sant'Angelo in Lizzola", 'Sassocorvaro'],
         verifica='https://oaj.fupress.net/index.php/qoe/article/download/12787/10643',
         aree={'Mascioni': CSX, 'Cicoli': CDX, 'Cecchini': SX}),
    dict(d='2000-06-18', ramo='C', leg='XIII', collegio='Sardegna - 6 (Tortolì)', sez=('Camera', 'Collegio Sardegna - 6'),
         coll='Collegio elettorale di Tortolì (Camera dei deputati)', reg=['20'],
         aree={'Loddo': CSX, 'Liori': CDX, 'Marras': SX, 'Carta': ALT}),
    # ---------------- XIV legislatura (2001-2006) ----------------
    dict(d='2002-10-27', ramo='S', leg='XIV', collegio='Toscana - 10 (Pisa)', sez=('Senato', 'Collegio Toscana - 10'),
         coll='Collegio elettorale di Pisa (Senato della Repubblica)', reg=['09'],
         verifica='https://oaj.fupress.net/index.php/qoe/article/download/12753/10583/36472',
         aree={'Modica': CSX, 'Cognetti': CDX, 'Piddiu': SX}),
    dict(d='2003-06-22', ramo='S', leg='XIV', collegio='Lazio - 21 (Marino)', sez=('Senato', 'Collegio Lazio - 21'),
         coll='Collegio elettorale di Marino (Senato della Repubblica)', reg=['12'],
         aree={'Zanda': CSX}, note='Candidato unico.'),
    dict(d='2003-10-26', ramo='C', leg='XIV', collegio='Friuli-Venezia Giulia - 2 (Trieste - Muggia)', sez=('Camera', 'Collegio Friuli-Venezia Giulia - 2'),
         coll='Collegio elettorale di Trieste - Muggia', reg=['06'], parziali={'Trieste': None},
         aree={'Rosato': CSX, 'Codarin': CDX, 'Sponza': ALT}),
    dict(d='2004-10-24', d2='2004-10-25', ramo='C', leg='XIV', collegio='Lombardia 1 - 3 (Milano 3)', sez=('Camera', 'Collegio Lombardia 1 - 3'),
         coll='Collegio elettorale di Milano 3 (Camera dei deputati)', reg=['03'], parziali={'Milano': None},
         aree={'Zaccaria': CSX, 'Bresciani': CDX, 'Pagliuzzi': ALT, 'Traversa': DX, 'Garatti': ALT, 'Ferrario': ALT,
               'Belardi': ALT, 'Staiti di Cuddia': DX}),
    dict(d='2004-10-24', d2='2004-10-25', ramo='C', leg='XIV', collegio='Liguria - 10 (Genova - Nervi)', sez=('Camera', 'Collegio Liguria - 10'),
         coll='Collegio elettorale di Genova - Nervi', reg=['07'], parziali={'Genova': None},
         aree={'Zara': CSX, 'Suriani': CDX, 'Castellaneta': None, 'Brignola': ALT, 'Riccobaldi': DX, 'Loda': ALT},
         note='Castellaneta (Liguria Nuova, lista civica di area di centrodestra) era in alternativa al candidato della Casa delle Libertà: area non assegnata.'),
    dict(d='2004-10-24', d2='2004-10-25', ramo='C', leg='XIV', collegio='Emilia-Romagna - 30 (Fidenza)', sez=('Camera', 'Collegio Emilia-Romagna - 30'),
         coll='Collegio elettorale di Fidenza (Camera dei deputati)', reg=['08'],
         soppressi=['Mezzani', 'Polesine Parmense', 'Sissa', 'Sorbolo', 'Trecasali'],
         aree={'Tedeschi': CSX, 'Villani': CDX}),
    dict(d='2004-10-24', d2='2004-10-25', ramo='C', leg='XIV', collegio='Toscana - 4 (Scandicci)', sez=('Camera', 'Collegio Toscana - 4'),
         coll='Collegio elettorale di Scandicci (Camera dei deputati)', reg=['09'],
         aree={'Giacomelli': CSX, 'Calderisi': CDX}),
    dict(d='2004-10-24', d2='2004-10-25', ramo='C', leg='XIV', collegio='Toscana - 6 (Firenze - Pontassieve)', sez=('Camera', 'Collegio Toscana - 6'),
         coll='Collegio elettorale di Firenze - Pontassieve', reg=['09'],
         soppressi=['San Piero a Sieve', 'Scarperia'], parziali={'Firenze': None},
         aree={'Galante': CSX, 'Gnaga': CDX}),
    dict(d='2004-10-24', d2='2004-10-25', ramo='C', leg='XIV', collegio='Campania 1 - 1 (Napoli - Ischia)', sez=('Camera', 'Collegio Campania 1 - 1'),
         coll='Collegio elettorale di Napoli - Ischia', reg=['15'],
         parziali={'Napoli': 'San Ferdinando, San Giuseppe, Montecalvario, Mercato, Pendino, Porto'},
         aree={"D'Antoni": CSX, 'Laboccetta': CDX, 'Venia': DX, 'Savio': SX, 'Salvatore': None, 'Isernia': DX},
         senza_affluenza='La pagina riporta 37.778 votanti, lo stesso numero del collegio Firenze - Pontassieve: probabile errore di copia, affluenza omessa.',
         note='Salvatore (Nuovo PSI, in alternativa al candidato della Casa delle Libertà) senza area certa.'),
    dict(d='2004-10-24', d2='2004-10-25', ramo='C', leg='XIV', collegio='Puglia - 11 (Casarano)', sez=('Camera', 'Collegio Puglia - 11'),
         coll='Collegio elettorale di Casarano (Camera dei deputati)', reg=['16'],
         aree={'Ria': CSX, 'Barba': CDX}),
    dict(d='2005-01-23', d2='2005-01-24', ramo='S', leg='XIV', collegio='Veneto - 8 (Rovigo)', sez=('Senato', 'Collegio Veneto - 8'),
         coll='Collegio elettorale di Rovigo (Senato della Repubblica)', reg=['05'],
         sostituisci_coll={'Contarina': ['Porto Viro'], 'Donada': ['Porto Viro']},
         aree={'Donadi': CSX, 'Romeo': CDX, 'Osti': None, 'Previati': DX},
         note='Contarina e Donada, nel collegio secondo il decreto del 1993, dal 1995 formano il comune di Porto Viro. '
              'Osti (UDEUR, in alternativa al candidato dell\'Ulivo) senza area certa.'),
    dict(d='2005-01-23', d2='2005-01-24', ramo='S', leg='XIV', collegio='Puglia - 2 (Bari - Bitonto)', sez=('Senato', 'Collegio Puglia - 2'),
         coll='Collegio elettorale di Bari - Bitonto', reg=['16'],
         parziali={'Bari': 'Palese, Santo Spirito, San Paolo, Stanic, Carbonara, Ceglie, Loseto'},
         aree={'Latorre': CSX, 'Degennaro': CDX, 'Monaco': DX, 'Zuccaro': None},
         note='Zuccaro (UDEUR, in alternativa al candidato dell\'Ulivo) senza area certa.'),
    dict(d='2005-06-26', d2='2005-06-27', ramo='C', leg='XIV', collegio='Lazio 1 - 11 (Roma - Don Bosco)', sez=('Camera', 'Collegio Lazio 1 - 11'),
         coll='Collegio elettorale di Roma - Don Bosco', reg=['12'], parziali={'Roma': 'Appio Claudio, Don Bosco, Capannelle'},
         aree={'Meta': CSX, 'Tilia': CDX}),
    dict(d='2005-06-26', d2='2005-06-27', ramo='C', leg='XIV', collegio='Calabria - 9 (Isola di Capo Rizzuto)', sez=('Camera', 'Collegio Calabria - 9'),
         coll='Collegio elettorale di Isola di Capo Rizzuto (Camera dei deputati)', reg=['18'],
         aree={'Oliverio': CSX, 'Zavettieri': None, 'Calzone': CDX, 'Scalise': DX},
         note='Zavettieri (Nuovo PSI, in alternativa al candidato della Casa delle Libertà) senza area certa.'),
    # ---------------- XVIII legislatura (2018-2022), collegi del 2017 ----------------
    dict(d='2019-01-20', ramo='C', leg='XVIII', collegio='Sardegna - 01 (Cagliari)', sez=('Camera', 'Collegio Sardegna 01'),
         coll='Collegio uninominale Sardegna - 01 (Camera dei deputati 2017)', reg=['20'],
         aree={'Frailis': CSX, 'Caschili': ALT, 'Noli': CDX, 'Balletto': DX}),
    dict(d='2019-05-26', ramo='C', leg='XVIII', collegio='Trentino-Alto Adige - 04 (Trento)', sez=('Camera', 'Collegio Trentino-Alto Adige 04'),
         coll='Collegio uninominale Trentino-Alto Adige - 04 (Camera dei deputati 2017)', reg=['04'],
         soppressi=['Castelfondo', 'Fondo', 'Malosco', 'Brez', "Cagno'", 'Cloz', "Revo'", 'Romallo', 'Nave San Rocco', 'Zambana'],
         sostituisci_coll={'Borgo d\'Anaunia': ['Castelfondo', 'Fondo', 'Malosco'],
                           'Novella': ['Brez', 'Cagnò', 'Cloz', 'Revò', 'Romallo']},
         aree={'Loss': CDX, 'Merlo': CSX, 'Leoni': ALT},
         note='La pagina del collegio usa i comuni di oggi: Borgo d\'Anaunia e Novella sono nati il 1º gennaio 2020, '
              'il giorno del voto c\'erano Castelfondo, Fondo e Malosco e Brez, Cagnò, Cloz, Revò e Romallo '
              '(Nave San Rocco e Zambana, uniti nel 2020 in Terre d\'Adige, sono già indicati con i nomi di allora).'),
    dict(d='2019-05-26', ramo='C', leg='XVIII', collegio='Trentino-Alto Adige - 06 (Pergine Valsugana)', sez=('Camera', 'Collegio Trentino-Alto Adige 06'),
         coll='Collegio uninominale Trentino-Alto Adige - 06 (Camera dei deputati)', reg=['04'],
         soppressi=['Carano', 'Daiano', 'Varena'],
         sostituisci_coll={'Ville di Fiemme': ['Carano', 'Daiano', 'Varena']},
         aree={'Sutto': CDX, 'Donei': CSX, 'Rizzi': ALT},
         note='La pagina del collegio usa i comuni di oggi: Ville di Fiemme è nato il 1º gennaio 2020, il giorno del voto c\'erano Carano, Daiano e Varena.'),
    dict(d='2020-02-23', ramo='S', leg='XVIII', collegio='Campania - 07 (Napoli - San Carlo all\'Arena)', sez=('Senato', 'Collegio Campania - 07'),
         coll='Collegio uninominale Campania - 07 (2017)', reg=['15'],
         parziali={'Napoli': 'Arenella, Barra, Miano, Piscinola, Poggioreale, Ponticelli, San Carlo all\'Arena, San Giovanni a Teduccio, '
                             'San Pietro a Patierno, Scampia, Secondigliano, Vicaria, Vomero, Zona Industriale'},
         verifica='https://tg24.sky.it/politica/2020/02/24/elezioni-suppletive-napoli-sandro-ruotolo',
         aree={'Ruotolo': CSX, 'Guangi': CDX, 'Napolitano': ALT, 'Aragno': SX, 'Guarino': ALT}),
    dict(d='2020-03-01', ramo='C', leg='XVIII', collegio='Lazio 1 - 01 (Roma - Trionfale)', sez=('Camera', 'Collegio Lazio 1 - 01'),
         coll='Collegio uninominale Lazio 1 - 01 (2017)', reg=['12'],
         parziali={'Roma': 'rioni del centro storico, Esquilino, Ludovisi, Sallustiano, Castro Pretorio, Celio, San Saba, Testaccio, '
                           'Trastevere, Borgo, Prati; quartieri Trionfale, Flaminio, Della Vittoria'},
         verifica='https://www.open.online/2020/03/02/roma-elezioni-suppletive-per-la-camera-vince-gualtieri-con-il-62-per-cento-dei-consensi/',
         aree={'Gualtieri': CSX, 'Leo': CDX, 'Rendina': ALT, 'Rizzo': SX, 'Canitano': SX, 'Adinolfi': ALT, 'Lo Muzio Lezza': ALT}),
    dict(d='2020-03-08', ramo='S', leg='XVIII', collegio='Umbria - 02 (Terni)', sez=('Senato', 'Collegio Umbria - 02'),
         coll='Collegio uninominale Umbria - 02 (Senato della Repubblica)', reg=['10'],
         aree={'Alessandrini': CDX, 'Mascio': CSX, 'Alcidi': ALT, 'Gargani': ALT}),
    dict(d='2020-09-20', d2='2020-09-21', ramo='S', leg='XVIII', collegio='Sardegna - 03 (Sassari)', sez=('Senato', 'Collegio Sardegna - 03'),
         coll='Collegio uninominale Sardegna - 03 (Senato della Repubblica)', reg=['20'], prov=['SS'],
         aree={'Doria': CDX, 'Corda': CSX, 'Marras': CEN, 'Salis': None},
         note='«Tutta la provincia di Sassari» è quella del 2016-2025 (92 comuni, con l\'ex provincia di Olbia-Tempio), come in dati/comuni.js. '
              'Corda era sostenuto da M5S e PD; Salis (PSI, da solo) senza area certa.'),
    dict(d='2020-09-20', d2='2020-09-21', ramo='S', leg='XVIII', collegio='Veneto - 09 (Villafranca di Verona)', sez=('Senato', 'Collegio Veneto - 09'),
         coll='Collegio uninominale Veneto - 09', reg=['05'],
         aree={'De Carlo': CDX, 'Melotti': CSX, 'Sterzi': ALT}),
    dict(d='2021-10-03', d2='2021-10-04', ramo='C', leg='XVIII', collegio='Toscana - 12 (Siena)', sez=('Camera', 'Collegio Toscana - 12'),
         coll='Collegio uninominale Toscana - 12', reg=['09'],
         aree={'Letta': CSX, 'Marrocchesi Marzi': CDX, 'Rizzo': SX, 'Golini': SX, 'Aurigi': ALT, 'Rappuoli': ALT, 'Agostini': ALT}),
    dict(d='2021-10-03', d2='2021-10-04', ramo='C', leg='XVIII', collegio='Lazio 1 - 11 (Roma - Primavalle)', sez=('Camera', 'Collegio Lazio 1 - 11'),
         coll='Collegio uninominale Lazio 1 - 11', reg=['12'],
         parziali={'Roma': 'Gianicolense, Aurelio, Casalotti, Trionfale (suburbio), Primavalle, La Pisana'},
         aree={'Casu': CSX, 'Calzetta': CDX, 'Ballanti': SX, 'Palamara': ALT, 'Bocci': ALT, 'Cocco': ALT}),
    dict(d='2022-01-16', ramo='C', leg='XVIII', collegio='Lazio 1 - 01 (Roma - Trionfale)', sez=('Camera', 'Collegio Lazio 1 - 01'),
         coll='Collegio uninominale Lazio 1 - 01 (2017)', reg=['12'],
         parziali={'Roma': 'rioni del centro storico, Esquilino, Ludovisi, Sallustiano, Castro Pretorio, Celio, San Saba, Testaccio, '
                           'Trastevere, Borgo, Prati; quartieri Trionfale, Flaminio, Della Vittoria'},
         aree={"D'Elia": CSX, 'Matone': CDX, 'Casini': CEN, 'Gamberini': SX, 'Vanni': ALT}),
    # ---------------- XIX legislatura (dal 2022), collegi del 2020 ----------------
    dict(d='2023-10-22', d2='2023-10-23', ramo='S', leg='XIX', collegio='Lombardia - 06 (Monza)', sez=('Senato', 'Collegio Lombardia - 06'),
         coll='Collegio uninominale Lombardia - 06 (2020)', reg=['03'], prov=['MB'],
         aree={'Galliani': CDX, 'Cappato': CSX, 'De Luca': ALT, 'Capelli': SX, 'Di Modugno': SX, 'Giovanardi': ALT, 'Musso': ALT, 'Brenna': ALT}),
    dict(d='2026-03-22', d2='2026-03-23', ramo='C', leg='XIX', collegio='Veneto 2 - 01 (Rovigo)', sez=('Camera', 'Collegio Veneto 2 - 01'),
         coll='Collegio uninominale Veneto 2 - 01 (2020)', reg=['05'], prov=['RO'], anno_senza_elenco=True,
         sostituisci_coll={'Carceri': ["Santa Caterina d'Este"], "Vighizzolo d'Este": ["Santa Caterina d'Este"]},
         note='Carceri e Vighizzolo d\'Este, nel collegio secondo il decreto del 2020, dal 22 gennaio 2024 formano il comune di Santa Caterina d\'Este.',
         verifica='https://pagellapolitica.it/articoli/elezioni-suppletive-veneto-vittoria-centrodestra',
         aree={'Di Rubba': CDX, 'Bovolenta': CSX, 'Padoan': ALT}),
    dict(d='2026-03-22', d2='2026-03-23', ramo='C', leg='XIX', collegio='Veneto 2 - 02 (Selvazzano Dentro)', sez=('Camera', 'Collegio Veneto 2 - 02'),
         coll='Collegio uninominale Veneto 2 - 02 (2020)', reg=['05'],
         verifica='https://pagellapolitica.it/articoli/elezioni-suppletive-veneto-vittoria-centrodestra',
         aree={'Centenaro': CDX, 'Stivanello': CSX, 'Adinolfi': ALT, 'Paccagnella': ALT}),
    dict(d='2026-09-27', d2='2026-09-28', ramo='C', leg='XIX', collegio='Calabria - 05 (Reggio Calabria)', sez=('Camera', 'Collegio Calabria - 05'),
         coll='Collegio uninominale Calabria - 05 (2020)', reg=['18'],
         aree={'Roscioli': CDX, 'Benedetto': CSX, 'Giannetta': DX, 'Toscano': ALT}),
]

# Ultima legislatura con i collegi del 1993; dal 2018 la legge Rosato.
SISTEMA = {'XII': 'Mattarellum', 'XIII': 'Mattarellum', 'XIV': 'Mattarellum', 'XVIII': 'Rosatellum', 'XIX': 'Rosatellum'}


# ===== Scaricamento =====
def scarica(titolo, cartella):
    """Wikitext di una pagina di it.wikipedia.org, dalla cartella o scaricato; segue i rinvii."""
    for _ in range(4):
        f = os.path.join(cartella, titolo.replace(' ', '_').replace('/', '_') + '.txt')
        if not os.path.exists(f) or os.path.getsize(f) == 0:
            u = 'https://it.wikipedia.org/w/index.php?' + urllib.parse.urlencode({'title': titolo, 'action': 'raw'})
            for tentativo in range(5):
                try:
                    testo = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': UA}), timeout=60).read().decode()
                    break
                except urllib.error.HTTPError as e:
                    if e.code != 429 or tentativo == 4: raise
                    time.sleep(20 * (tentativo + 1))
            with open(f, 'w', encoding='utf-8') as o: o.write(testo)
            time.sleep(PAUSA)
        testo = open(f, encoding='utf-8').read()
        m = re.match(r'#(?:REDIRECT|RINVIA)\s*\[\[([^\]|#]+)', testo, re.I)
        if not m: return testo
        titolo = m.group(1).strip()
    raise RuntimeError('troppi rinvii: ' + titolo)


# ===== Wikitext =====
def togli_template(s, nomi):
    """Toglie i template {{nome...}} (anche annidati) il cui nome è in nomi."""
    out, i = [], 0
    pat = re.compile(r'\{\{\s*(' + '|'.join(nomi) + r')\b', re.I)
    while True:
        m = pat.search(s, i)
        if not m: out.append(s[i:]); return ''.join(out)
        out.append(s[i:m.start()])
        j, prof = m.start(), 0
        while j < len(s):
            if s.startswith('{{', j): prof += 1; j += 2
            elif s.startswith('}}', j):
                prof -= 1; j += 2
                if prof == 0: break
            else: j += 1
        i = j


def pulisci(s):
    s = re.sub(r'<ref[^>]*/>', '', s)
    s = re.sub(r'<ref[^>]*>.*?</ref>', '', s, flags=re.S)
    s = togli_template(s, [r'#tag:ref', 'efn', 'Efn'])
    s = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', s)
    s = re.sub(r"'''?|<br\s*/?>|<small>.*?</small>|&#32;|<nowiki/>", ' ', s)
    s = s.replace('&nbsp;', ' ')
    return re.sub(r'\s+', ' ', s).strip(' -')


def parametri(template):
    """Parametri di un template come dizionario (separa sui | di primo livello)."""
    corpo, parti, prof, cur, i = template[2:-2], [], 0, '', 0
    while i < len(corpo):
        c2 = corpo[i:i + 2]
        if c2 in ('{{', '[['): prof += 1; cur += c2; i += 2; continue
        if c2 in ('}}', ']]'): prof -= 1; cur += c2; i += 2; continue
        if corpo[i] == '|' and prof == 0: parti.append(cur); cur = ''; i += 1; continue
        cur += corpo[i]; i += 1
    parti.append(cur)
    out = {}
    for p in parti[1:]:
        if '=' in p:
            k, v = p.split('=', 1); out[k.strip()] = v.strip()
    return out


def sezione(testo, ramo, titolo):
    """Testo della sezione titolo (=== ... ===) dentro la sezione di livello 2 del ramo (Camera/Senato)."""
    norm_t = lambda x: re.sub(r'\s+', ' ', x.replace('-', ' - ')).strip().lower()
    livello2 = re.split(r'\n==\s*([^=\n]+?)\s*==\s*\n', '\n' + testo)
    for k in range(1, len(livello2), 2):
        if not livello2[k].lower().startswith(ramo.lower()): continue
        corpo = livello2[k + 1]
        parti = re.split(r'\n===\s*([^=\n]+?)\s*===\s*\n', '\n' + corpo)
        for j in range(1, len(parti), 2):
            if norm_t(parti[j]) == norm_t(titolo): return parti[j + 1]
    raise KeyError(f'sezione non trovata: {ramo} / {titolo}')


def numero(s):
    s = pulisci(s).replace('.', '').replace(' ', '')
    return int(s) if s.isdigit() else None


def candidati(sez):
    """[(nome, voti, lista)] dal riquadro {{Elezione uninominale}} o dalla tabella; elettori e votanti."""
    m = re.search(r'\{\{\s*elezione uninominale', sez, re.I)
    if m:
        j, prof = m.start(), 0
        while True:
            if sez.startswith('{{', j): prof += 1; j += 2
            elif sez.startswith('}}', j):
                prof -= 1; j += 2
                if prof == 0: break
            else: j += 1
        p = parametri(sez[m.start():j])
        out = []
        for n in range(1, 30):
            if f'cand{n}' not in p: continue
            out.append((pulisci(p[f'cand{n}']), numero(p.get(f'voti{n}', '')), pulisci(p.get(f'part{n}', ''))))
        return out, numero(p.get('elettori', '')), numero(p.get('votanti', ''))
    # Tabella: |'''[[Nome]]'''<br/>... / ! colore / |[[Lista]] / |voti / |%
    out = []
    for riga in re.split(r'\n\|-', sez):
        celle = [c.strip() for c in re.split(r'\n[|!]', '\n' + riga) if c.strip()]
        celle = [c for c in celle if not c.startswith('style=') and not c.startswith('{|')]
        if len(celle) >= 4 and re.search(r'\d', celle[-2]) and 'Totale' not in riga and 'Candidato' not in riga:
            nome = pulisci(re.sub(r'<small>.*?</small>', '', celle[0]))
            voti = numero(re.sub(r'^.*\|', '', celle[-2]))
            out.append((nome, voti, pulisci(celle[-3])))
    return out, None, None


def collegamenti(frase):
    """Collegamenti [[...]] di una frase con l'indicazione 'parte del comune di' davanti. Restano fuori i quartieri:
    i collegamenti tra parentesi e quelli dopo «comune di [[Città]]:»."""
    link = re.findall(r'\[\[[^\]]*\]\]', frase)
    t = re.sub(r'\[\[[^\]]*\]\]', lambda m: f'\x00{link.index(m.group(0))}\x00', frase)
    t = re.sub(r'\([^()]*\x00[^()]*\)', ' ', t)
    t = re.sub(r'(comune di \x00\d+\x00)\s*:.*', r'\1', t, flags=re.S)
    t = re.sub(r'\x00(\d+)\x00', lambda m: link[int(m.group(1))], t)
    out = []
    for m in re.finditer(r'\[\[([^\]|]+)(?:\|([^\]]*))?\]\]', t):
        prima = t[max(0, m.start() - 30):m.start()].lower()
        out.append((m.group(1).strip(), (m.group(2) or m.group(1)).strip(), 'parte' in prima))
    return out


def frase_comuni_anno(sez):
    m = re.search(r'Il collegio (?:elettorale )?(?:è formato|comprendeva)(.*?)(?:\n|$)', sez)
    return m.group(1) if m else ''


def frase_comuni_collegio(testo):
    """La frase del territorio dalla pagina del collegio (per i collegi del Senato anteriori al 1993, «Dal 1993 al 2005»)."""
    i = -1
    for t in ('Dal 1993 al 2005', '1993-2005 =='):
        i = testo.find(t)
        if i >= 0: break
    m = re.search(r'==\s*Territorio\s*==(.*?)\n=', testo[max(i, 0):], re.S)
    s = re.sub(r'<ref[^>]*/>|<ref[^>]*>.*?</ref>', '', m.group(1), flags=re.S) if m else ''
    return s.strip()


# ===== Comuni =====
def chiave(s):
    s = unicodedata.normalize('NFD', s.lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()


def carica_comuni():
    testo = open(os.path.join(RADICE, 'dati', 'comuni.js'), encoding='utf-8').read()
    righe = re.search(r'COMUNI_TXT = `(.*?)`', testo, re.S).group(1).split('\n')
    comuni = []
    for r in righe:
        nome, sig, reg, cod, att, alias = r.split('|')
        comuni.append(dict(nome=nome, sig=sig, reg=reg, cod=cod, att=att == '1', alias=[a for a in alias.split(';') if a]))
    indice = {}
    for c in comuni:
        for n in [c['nome']] + c['alias']:
            indice.setdefault(chiave(n), []).append(c)
    return comuni, indice


NON_COMUNI = re.compile(r'^(provincia|citt[aà] metropolitana|circoscrizione|collegio|regione|quartiere|rione|suburbio|zona)\b', re.I)


def risolvi(nome, regioni, indice):
    """Il comune di dati/comuni.js con questo nome (o nome precedente) nelle regioni del collegio; None se non è un comune."""
    base = re.sub(r'\s*\([^)]*\)\s*$', '', nome).strip()
    cand = list({c['cod']: c for c in indice.get(chiave(base), []) if c['reg'] in regioni}.values())
    if len(cand) > 1:  # stesso nome come nome attuale e come nome precedente: vale il nome attuale
        esatti = [c for c in cand if chiave(c['nome']) == chiave(base)]
        if len(esatti) == 1: cand = esatti
    if len(cand) > 1:  # un comune attivo e uno soppresso con lo stesso nome: vale quello attivo
        attivi = [c for c in cand if c['att']]
        if len(attivi) == 1: cand = attivi
    if len(cand) > 1: raise ValueError(f'nome ambiguo: {nome} {[c["cod"] for c in cand]}')
    return cand[0] if cand else None


def elenco(frase, e, indice, sost, quartieri):
    """{codice: (nome, parziale)} dai collegamenti della frase; i collegamenti che non sono comuni vanno in quartieri."""
    out = {}
    for dest, testo, parte in collegamenti(frase):
        if NON_COMUNI.match(dest): continue
        nomi = sost.get(testo) or sost.get(dest) or [dest]
        for n in nomi:
            c = risolvi(n, e['reg'], indice)
            if c is None and n == dest: c = risolvi(testo, e['reg'], indice)
            if c is None: quartieri.add(testo); continue
            if not c['att'] and chiave(c['nome']) not in {chiave(x) for x in e.get('soppressi', [])}:
                raise ValueError(f'{e["d"]} {e["collegio"]}: {n} è un comune soppresso non previsto in soppressi')
            out[c['cod']] = (c['nome'], parte or c['nome'] in e.get('parziali', {}))
    return out


def main():
    cartella = sys.argv[1] if len(sys.argv) > 1 else os.path.join(tempfile.gettempdir(), 'suppletive-wikipedia')
    os.makedirs(cartella, exist_ok=True)
    comuni, indice = carica_comuni()
    per_cod = {c['cod']: c for c in comuni}
    uscita, problemi = [], []
    contatori = {}
    for e in SUPPLETIVE:
        anno = e['d'][:4]
        pagina = ANNO + anno
        testo = scarica(pagina, cartella)
        sez = sezione(testo, e['sez'][0], e['sez'][1])
        # --- candidati ---
        cands, elettori, votanti = candidati(sez)
        cands = [c for c in cands if c[1] is not None]
        tot = sum(c[1] for c in cands)
        cands.sort(key=lambda c: -c[1])
        lista = []
        for nome, voti, part in cands:
            area = next((a for k, a in e['aree'].items() if nome.endswith(k)), 'MANCA')
            if area == 'MANCA': problemi.append(f'{e["d"]} {e["collegio"]}: area mancante per {nome}')
            lista.append([nome, round(100 * voti / tot, 2), part, area])
        if len(lista) != len(e['aree']):
            problemi.append(f'{e["d"]} {e["collegio"]}: {len(lista)} candidati, {len(e["aree"])} aree')
        # --- comuni: pagina dell'anno e pagina del collegio ---
        quartieri = set()
        sost = e.get('sostituisci', {})
        da_anno = elenco(frase_comuni_anno(sez), e, indice, sost, quartieri)
        frase_coll = frase_comuni_collegio(scarica(e['coll'], cartella))
        da_coll = elenco(frase_coll, e, indice, {**sost, **e.get('sostituisci_coll', {})}, quartieri)
        for sig in e.get('prov', []):
            for c in comuni:
                if c['sig'] == sig and c['att']:
                    da_coll[c['cod']] = (c['nome'], False)
                    if re.search(r'provincia', frase_comuni_anno(sez), re.I): da_anno[c['cod']] = (c['nome'], False)
        if e.get('anno_senza_elenco'): da_anno = {}
        if da_anno and set(da_anno) != set(da_coll) and not e.get('scarta_anno'):
            solo_a = sorted(da_anno[k][0] for k in set(da_anno) - set(da_coll))
            solo_c = sorted(da_coll[k][0] for k in set(da_coll) - set(da_anno))
            if solo_a or solo_c:
                problemi.append(f'{e["d"]} {e["collegio"]}: elenchi diversi; solo pagina anno {solo_a}; solo pagina collegio {solo_c}')
        com = da_coll or da_anno
        for nome in e.get('parziali', {}):
            c = risolvi(nome, e['reg'], indice)
            if c['cod'] not in com: problemi.append(f'{e["d"]} {e["collegio"]}: comune parziale {nome} non nell\'elenco')
            com[c['cod']] = (c['nome'], True)
        voce = {'d': e['d']}
        if e.get('d2'): voce['d2'] = e['d2']
        voce.update({'ramo': e['ramo'], 'legislatura': e['leg'], 'collegio': e['collegio'], 'sistema': SISTEMA[e['leg']]})
        voce['comuni'] = []
        for cod, (nome, parz) in sorted(com.items(), key=lambda x: chiave(x[1][0])):
            v = {'cod': cod, 'nome': nome, 'parziale': parz}
            if parz and e.get('parziali', {}).get(nome): v['zona'] = e['parziali'][nome]
            voce['comuni'].append(v)
        voce['candidati'] = lista
        voce['affluenza'] = round(100 * votanti / elettori, 2) if elettori and votanti and not e.get('senza_affluenza') else None
        anc = 'Collegio_' + e['sez'][1].replace('Collegio ', '').strip().replace(' ', '_')
        voce['fonte'] = WIKI + urllib.parse.quote(pagina.replace(' ', '_')) + '#' + urllib.parse.quote(anc)
        voce['fonte_comuni'] = WIKI + urllib.parse.quote(e['coll'].replace(' ', '_'))
        if e.get('verifica'): voce['verifica'] = e['verifica']  # controllo indipendente di data e risultato
        note = [x for x in (e.get('note'), e.get('scarta_anno'), e.get('senza_affluenza')) if x]
        if note: voce['note'] = ' '.join(note)
        uscita.append(voce)
        contatori[(e['leg'], e['ramo'])] = contatori.get((e['leg'], e['ramo']), 0) + 1
        print(f'{e["d"]} {e["ramo"]} {e["collegio"]}: {len(voce["comuni"])} comuni '
              f'({sum(1 for c in voce["comuni"] if c["parziale"])} parziali), {len(lista)} candidati, '
              f'vince {lista[0][0]} {lista[0][1]}%, affluenza {voce["affluenza"]}'
              + (f'; non comuni: {sorted(quartieri)}' if quartieri else ''))
    # Le voci della seconda sezione con lo stesso titolo nella stessa pagina hanno l'ancora con _2
    viste = {}
    for v in uscita:
        viste[v['fonte']] = viste.get(v['fonte'], 0) + 1
        if viste[v['fonte']] > 1: v['fonte'] += f'_{viste[v["fonte"]]}'
    for v in uscita:
        for c in v['comuni']:
            if c['cod'] not in per_cod: problemi.append(f'codice inesistente {c["cod"]}')
    uscita.sort(key=lambda v: (v['d'], v['ramo'], v['collegio']))
    if problemi:
        print('\nPROBLEMI:'); [print(' -', p) for p in problemi]
        sys.exit(1)
    dati = {
        'descrizione': 'Elezioni suppletive della Camera dei deputati (ramo C) e del Senato (ramo S) dal 1994 a oggi, '
                       'generato da strumenti/suppletive.py. Fonti: it.wikipedia.org, «Elezioni politiche suppletive in Italia» '
                       'e «Elezioni politiche suppletive in Italia del AAAA» (data, candidati, voti, elettori e votanti; fonte), '
                       'pagine dei collegi (comuni secondo i d.lgs. 535 e 536 del 1993, 189 del 2017 e 177 del 2020; fonte_comuni), '
                       '«Deputati/Senatori della ... legislatura» (controllo delle date con i subentri). Percentuali sui voti validi '
                       'ai candidati; affluenza = votanti/elettori. Comuni con il codice catastale di dati/comuni.js, come erano il '
                       'giorno del voto; parziale = comune diviso tra più collegi (vota solo la zona indicata). Area del candidato '
                       'secondo lo schieramento in quella suppletiva, null se incerta. Dal 2006 al 2017 non ci furono suppletive '
                       '(legge Calderoli, proporzionale). Escluse le suppletive non ancora votate.',
        'suppletive': uscita,
    }
    with open(os.path.join(RADICE, 'strumenti', 'suppletive.json'), 'w', encoding='utf-8') as o:
        json.dump(dati, o, ensure_ascii=False, indent=1)
    print(f'\n{len(uscita)} suppletive scritte in strumenti/suppletive.json')
    for (l, r), n in sorted(contatori.items(), key=lambda x: (list(SISTEMA).index(x[0][0]), x[0][1])): print(f'  {l} {r}: {n}')


if __name__ == '__main__':
    main()
