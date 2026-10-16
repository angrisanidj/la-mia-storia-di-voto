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
| `dati/elezioni.js` | Calendario: politiche, europee, referendum nazionali, regionali per regione, provinciali di Trento e Bolzano, referendum regionali, comuni che hanno cambiato regione, turni ordinari delle comunali |
| `dati/comuni.js` | Comuni italiani attivi e soppressi (fonte ISTAT), con regione e nomi precedenti |
| `dati/partiti.js` | Liste sopra l'1% a politiche ed europee, coalizioni, partiti locali, colori proposti |
| `dati/referendum.js` | Quesiti dei referendum con più domande |
| `fonti/` | Dati di partenza in JSON, con l'indicazione delle fonti |

I dati grezzi con le fonti (URL per ogni elezione) sono in `fonti/`: i file in `dati/` ne sono la versione compatta.

Per aggiungere una nuova consultazione basta modificare il file in `dati/` corrispondente: una riga in `dati/elezioni.js` e, se servono, le liste in `dati/partiti.js` o i quesiti in `dati/referendum.js`.

## Regole applicate

- Età: 18 anni compiuti entro il primo giorno di voto (art. 33 DPR 223/1967). Con il solo mese di nascita, se il compleanno cade nel mese del voto la voce è segnalata.
- Senato: fino alle politiche 2018 servivano 25 anni (L. cost. 1/2021).
- Bolzano: per il consiglio provinciale servivano 4 anni di residenza in regione (2 dal 23/06/2026).
- Comuni passati di regione: Valmarecchia (2009), Sappada (2017), Montecopiolo e Sassofeltrio (2021).

L'immagine personale si esporta in cinque formati (lista completa, Instagram post, storie, X, quadrata), in PNG o JPG; nei formati a misura fissa la lista si impagina da sola su più colonne e a corpo ridotto.

Comunali, ballottaggi, suppletive, provinciali e referendum locali si aggiungono a mano: le date dei turni ordinari sono precompilate.

## Pubblicazione

Caricare il contenuto della cartella nel repository `angrisanidj/la-mia-storia-di-voto` e attivare GitHub Pages sul branch principale. Le anteprime dei link puntano a `angrisanidj.github.io/la-mia-storia-di-voto/`: con un nome diverso vanno aggiornati i meta `og:` in `index.html`. Sulla card l'indirizzo è letto dalla pagina stessa; `PIEDE_IMMAGINE` in `app.js` serve solo a forzarlo.
