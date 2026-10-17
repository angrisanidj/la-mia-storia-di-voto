# La mia storia di voto

Pagina statica che, a partire da mese e anno di nascita e dai comuni di residenza, elenca le elezioni e i referendum italiani a cui una persona poteva votare dal 1992 a oggi, permette di indicare come ha votato e genera un'immagine PNG da condividere.

## Privacy

Tutto avviene nel browser. La pagina non usa cookie né `localStorage`, non invia dati e, tramite Content-Security-Policy, può caricare solo i propri file statici. Chiudendo la scheda non resta nulla.

## Struttura

| File | Contenuto |
|---|---|
| `index.html` | Pagina e stili (stesso sistema visivo di «Il tuo emiciclo») |
| `stile/font.css` | Bodoni Moda e Titillium Web incorporati, senza richieste esterne |
| `condivisione.png`, `condivisione-quadrata.png` | Anteprime per i link condivisi |
| `social/` | Immagini per promuovere il link: X 1600×900, Instagram post 1080×1350, storie 1080×1920 |
| `app.js` | Logica: calcolo delle elezioni, interfaccia, disegno del PNG |
| `tavolozza.js` | Tavolozza alternativa «Gruppi europei»: colori dei gruppi del Parlamento europeo per partiti, candidati e liste civiche |
| `sismografo.js` | Il sismografo del voto: posizione dei voti, profilo, pendolo animato e immagine |
| `dati/elezioni.js` | Calendario: politiche, europee, referendum nazionali, regionali per regione, provinciali di Trento e Bolzano, referendum regionali, comuni che hanno cambiato regione, turni ordinari delle comunali |
| `dati/comuni.js` | Comuni italiani attivi e soppressi (fonte ISTAT), con regione e nomi precedenti |
| `dati/partiti.js` | Liste sopra l'1% a politiche ed europee, coalizioni, partiti locali, colori proposti |
| `dati/provinciali.js` | Provinciali dirette 2004-2011 dall'Archivio storico del Ministero (candidati, liste, ballottaggi; comuni delle province sarde), generato da `strumenti/provinciali.py` |
| `dati/provinciali-wiki.js` | Provinciali dirette 1993-2003 e di Sicilia e Friuli-Venezia Giulia, da it.wikipedia.org |
| `dati/referendum.js` | Quesiti dei referendum e percentuale dei Sì di ciascuno |
| `fonti/` | Dati di partenza in JSON, con l'indicazione delle fonti |

I dati grezzi con le fonti (URL per ogni elezione) sono in `fonti/`: i file in `dati/` ne sono la versione compatta.

Per aggiungere una nuova consultazione basta modificare il file in `dati/` corrispondente: una riga in `dati/elezioni.js` e, se servono, le liste in `dati/partiti.js` o i quesiti in `dati/referendum.js`.

## Regole applicate

- Età: 18 anni compiuti entro il primo giorno di voto (art. 33 DPR 223/1967). Con il solo mese di nascita, se il compleanno cade nel mese del voto la voce è segnalata.
- Camera e Senato sono voci separate. Per il Senato fino alle politiche 2018 servivano 25 anni (L. cost. 1/2021).
- Bolzano: per il consiglio provinciale servivano 4 anni di residenza in regione (2 dal 23/06/2026).
- Comuni passati di regione: Valmarecchia (2009), Sappada (2017), Montecopiolo e Sassofeltrio (2021).
- Provinciali: si votavano direttamente dal 1993 al 2011 (dal 2014 le province sono enti di secondo livello). La provincia è quella di allora: Monza e Brianza, Fermo e Barletta-Andria-Trani dal 2009, prima Milano, Ascoli Piceno, Bari o Foggia; Biella, Verbano-Cusio-Ossola, Lecco, Lodi, Rimini, Prato, Crotone e Vibo Valentia dal 1995; le province sarde dal 2005 secondo l'archivio, prima le quattro di allora (Cagliari, Sassari, Nuoro, Oristano), con i 26 comuni che nel 2005 lasciarono la provincia di Nuoro. Le provinciali sarde del 1995 e del 2000 (23 aprile 1995 e 16 aprile 2000, con le comunali) non hanno la data nelle pagine di Wikipedia: è indicata in `strumenti/provinciali_wikipedia.py` con le fonti.

L'immagine personale si esporta in cinque formati (lista completa, Instagram post, storie, X, quadrata), in PNG o JPG; nei formati a misura fissa la lista si impagina da sola su più colonne e a corpo ridotto.

## Il sismografo del voto

Ogni voto scelto dai menu (o scritto a mano con un partito riconoscibile) va su un asse a cinque posizioni, sinistra, centrosinistra, centro, centrodestra, destra, secondo l'area con cui la lista o il candidato si presentava in quell'elezione (`a` in `dati/partiti.js`). Un candidato senza area nei dati prende quella delle sue liste, con i partiti dei due poli che prevalgono su quelli fuori (il M5S in coalizione con il PD conta come centrosinistra); se è sostenuto da partiti di entrambi i poli, ciascuno con almeno un quarto dei loro voti, va al centro. Un candidato con sole liste civiche è civico: viola nell'elenco e fuori dall'asse nel sismografo. I partiti fuori dai poli (area `altro`) sono cerchi vuoti al centro e non entrano nella media; referendum, liste civiche senza schieramento, schede bianche e astensioni stanno nella colonna «Fuori dall'asse».

- **Baricentro**: la media dei voti sull'asse, pesata per gruppo: di base il 70% alla media dei voti nazionali (politiche ed europee) e il 30% a quella dei voti locali (regionali, comunali, ballottaggi); si può scegliere 60-40, metà e metà o solo nazionali. Se un gruppo è vuoto conta l'altro.
- **Oscillazione**: lo spostamento medio da un voto al successivo; i cambi di campo sono i passaggi da un lato all'altro del centro.
- **Col vento**: le volte in cui si è scelta la lista o il candidato più votato (al primo turno), o nei referendum la risposta con più voti, anche senza quorum. I ballottaggi non contano.
- **Profilo**: Il Pendolo (almeno due cambi di campo), La Traversata (un solo cambio di campo, su almeno 4 voti), Il Bastian contrario (col vento al massimo il 30% su almeno 5 voti), La Bussola (sempre dallo stesso lato, almeno 4 voti), Il Barometro (col vento almeno il 70%), Il Battitore libero (almeno il 40% dei voti fuori dai poli o a liste sotto il 4%), Il Campanile (almeno metà delle comunali a liste civiche), Il Quorum (nessun referendum saltato), L'Ago della bilancia (baricentro al centro), Il Viandante (negli altri casi). Si applica il primo che corrisponde, in quest'ordine.

Il sismografo si scarica anche come video: la stessa animazione della pagina registrata dalla tela con MediaRecorder, nel browser, in MP4. Il tasto «Video» compare solo nei browser che registrano in MP4 (Chrome, Edge, Safari), il formato che Instagram e X accettano.

## Comunali e candidati

- `dati/comunali.js`: date delle comunali di ogni comune dal 1993, con i ballottaggi. Fonte: Archivio storico delle elezioni del Ministero dell'Interno; per Sicilia, Friuli-Venezia Giulia, Valle d'Aosta e Trentino-Alto Adige, che gestiscono da sé le elezioni locali, tuttitalia.it, completato per i capoluoghi e i comuni maggiori con i riquadri di it.wikipedia.org (`strumenti/ballottaggi-wikipedia.json`), perché tuttitalia.it non indica i ballottaggi delle elezioni più vecchie.
- `dati/candidati/RR.js`: candidati sindaco e liste nei comuni sopra i 15.000 abitanti, un file per regione caricato solo quando serve.
  Per Sicilia, Friuli-Venezia Giulia, Valle d'Aosta e Trentino-Alto Adige, dopo gli anni coperti dall'archivio: riquadri di it.wikipedia.org e, dove mancano, fonti ufficiali regionali (archivio elettorale e open data del Friuli-Venezia Giulia, risultati della Regione Trentino-Alto Adige, della Provincia di Bolzano e di elezionicomunali.tn.it, sito elettorale della Regione Siciliana), anche tramite le copie della Wayback Machine (`strumenti/candidati-*.json`). Le date sbagliate nelle fonti sono corrette, con la fonte ufficiale, in `strumenti/comunali-correzioni.json`.
- `dati/regionali-candidati.js` e `dati/regionali-speciali.js`: candidati presidente e liste delle regionali.
- Si aggiornano da soli ogni mese con GitHub Actions (`.github/workflows/`), con gli script in `strumenti/`.

Suppletive, provinciali e referendum locali si aggiungono a mano.

## Pubblicazione

Caricare il contenuto della cartella nel repository `angrisanidj/la-mia-storia-di-voto` e attivare GitHub Pages sul branch principale. Le anteprime dei link puntano a `angrisanidj.github.io/la-mia-storia-di-voto/`: con un nome diverso vanno aggiornati i meta `og:` in `index.html`. Sulla card l'indirizzo è letto dalla pagina stessa; `PIEDE_IMMAGINE` in `app.js` serve solo a forzarlo.
