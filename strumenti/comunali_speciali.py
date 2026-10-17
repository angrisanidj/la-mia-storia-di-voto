"""Aggiunge a dati/comunali.js le comunali di Sicilia, Friuli-Venezia Giulia,
Valle d'Aosta e Trentino-Alto Adige, che non sono nell'Archivio storico del
Ministero dell'Interno perché queste regioni gestiscono da sé le elezioni locali.

Fonte: le pagine «storico elezioni comunali» di tuttitalia.it, una per comune
(date dal 1993 e indicazione del ballottaggio). Lettura lenta e una sola volta
al mese, con pausa tra le richieste.

Gira dopo strumenti/comunali.py nello stesso flusso di GitHub Actions.
"""
import datetime as dt
import json
import os
import re
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import unicodedata

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITO = "https://www.tuttitalia.it"
REGIONI = {"sicilia": "19", "friuli-venezia-giulia": "06", "valle-d-aosta": "02", "trentino-alto-adige": "04"}
PAUSA = float(os.environ.get("PAUSA_TT", "1.0"))
LIMITE_MINUTI = float(os.environ.get("LIMITE_MINUTI", "95"))
INIZIO = time.time()
LAVORATORI = int(os.environ.get("LAVORATORI", "1"))
ATTESA_ERRORE = float(os.environ.get("ATTESA_ERRORE", "180"))
OGNI_MINUTI = float(os.environ.get("SALVA_OGNI_MINUTI", "15"))
STATO = os.path.join(RADICE, "strumenti", "comunali-speciali-stato.json")
MESI = {m: i + 1 for i, m in enumerate(["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
                                        "agosto", "settembre", "ottobre", "novembre", "dicembre"])}
_M = "|".join(MESI)
# «6 giugno 1993», «13 e 14 aprile 2008», «1° giugno 2015», «31 maggio e 1° giugno 2015» (conta il primo giorno)
DATA_RE = re.compile(r"(\d{1,2})[^\d\s]{0,3}(?:\s*(?:e|-)\s*\d{1,2}[^\d\s]{0,3})?\s+(" + _M + r")(?:\s*(?:e|-)\s*\d{1,2}[^\d\s]{0,3}\s+(?:" + _M + r"))?\s+(\d{4})", re.I)
VERSIONE = 2  # con la versione 2 si rileggono le pagine con anni mancanti, lette con la vecchia lettura delle date


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def sessione():
    s = requests.Session()
    s.headers["User-Agent"] = "la-mia-storia-di-voto (github.com/angrisanidj/la-mia-storia-di-voto)"
    s.mount("https://", HTTPAdapter(max_retries=Retry(total=1, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504], respect_retry_after_header=False)))
    return s


def testo(html):
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<h2[^>]*>", "\n@@SEZIONE@@ ", html, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", html)
    t = re.sub(r"&nbsp;|&#160;", " ", t)
    t = re.sub(r"&#39;|&rsquo;", "'", t)
    return re.sub(r"[ \t]+", " ", t)


def elezioni_comune(html):
    """[(data_iso, ballottaggio_iso o None)] dalle sezioni «Elezioni Comunali AAAA»."""
    out = []
    for sez in testo(html).split("@@SEZIONE@@")[1:]:
        if not re.match(r"\s*Elezioni Comunali \d{4}", sez):
            continue
        anno = int(re.match(r"\s*Elezioni Comunali (\d{4})", sez).group(1))
        if anno < 1993:
            continue
        date = [dt.date(int(y), MESI[m.lower()], int(g)) for g, m, y in DATA_RE.findall(sez[:1500])]
        date = [d for d in date if d.year == anno]
        if not date:
            continue
        primo = min(date)
        ball = None
        if re.search(r"ballottaggio", sez[:2500], re.I):
            dopo = [d for d in date if d > primo]
            ball = (dopo[0] if dopo else primo + dt.timedelta(days=14)).isoformat()
        out.append((primo.isoformat(), ball))
    return sorted(set(out))


def carica_comuni():
    righe = open(os.path.join(RADICE, "dati", "comuni.js"), encoding="utf-8").read().split("`")[1].split("\n")
    indice = {}
    for r in righe:
        nome, sig, reg, cod, att, alias = r.split("|")
        for n in [nome] + [a for a in alias.split(";") if a]:
            indice.setdefault((reg, norm(n)), []).append((cod, att == "1"))
    return indice


def buchi(el):
    """Una tornata saltata (più di 5 anni e mezzo tra due elezioni), nessuna prima del 2000 o nessuna dal 2019."""
    ds = sorted(dt.date.fromisoformat(d) for d, _ in el)
    if not ds:
        return True
    salti = [(b - a).days / 365 for a, b in zip(ds, ds[1:])]
    return (salti and max(salti) > 5.7) or ds[0].year > 1999 or ds[-1].year < 2019


def salva_stato(stato):
    with open(STATO, "w", encoding="utf-8") as f:
        json.dump(stato, f, ensure_ascii=False, separators=(",", ":"))


LOCALE = threading.local()


def leggi(url):
    """(url, elezioni o None, secondi, errore) per una pagina di comune."""
    if not hasattr(LOCALE, "s"):
        LOCALE.s = sessione()
    time.sleep(PAUSA)
    t = time.time()
    try:
        r = LOCALE.s.get(SITO + url, timeout=(10, 20))
        if r.status_code != 200:
            return url, None, time.time() - t, f"HTTP {r.status_code}"
        return url, elezioni_comune(r.text), time.time() - t, None
    except requests.RequestException as e:
        return url, None, time.time() - t, type(e).__name__


# nomi che tuttitalia.it scrive diversamente dall'ISTAT
NOMI_TUTTITALIA = {"tripi abakainon": "tripi", "lampedusa linosa": "lampedusa e linosa", "erto casso": "erto e casso",
                   "san dorligo della valle dolina": "san dorligo della valle", "montagna sulla strada del vino": "montagna",
                   "salorno sulla strada del vino": "salorno"}


def applica(stato, indice):
    """Abbina le pagine lette ai codici dei comuni e le unisce alle date del Ministero."""
    trovati, non_trovati = {}, []
    for slug_reg, urls in stato["pagine"].items():
        reg = REGIONI[slug_reg]
        for url in urls:
            if url not in stato["fatti"]:
                continue
            nome = re.match(rf"/{slug_reg}/\d+-([^/]+)/", url).group(1).replace("-", " ")
            cand = indice.get((reg, NOMI_TUTTITALIA.get(nome, norm(nome))), [])
            if not cand:
                non_trovati.append(f"{reg}\t{url}")
                continue
            el = [tuple(x) for x in stato["fatti"][url]]
            if el:
                trovati[sorted(cand, key=lambda c: not c[1])[0][0]] = el
    unisci(trovati)
    with open(os.path.join(RADICE, "strumenti", "comunali-speciali-non-trovati.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(non_trovati) + "\n")
    return trovati, non_trovati


def pubblica(stato, indice, messaggio):
    """Su GitHub Actions salva subito il lavoro fatto, così non si perde e si vede l'avanzamento."""
    salva_stato(stato)
    if not os.environ.get("GITHUB_ACTIONS"):
        return
    applica(stato, indice)
    file = ["dati/comunali.js", "strumenti/comunali-speciali-non-trovati.txt", "strumenti/comunali-speciali-stato.json"]
    git = lambda *a: subprocess.run(["git", "-c", "user.name=github-actions[bot]",
                                     "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com", *a],
                                    cwd=RADICE, capture_output=True, text=True)
    git("add", *file)
    if git("diff", "--cached", "--quiet").returncode == 0:
        return
    git("commit", "-m", messaggio)
    for _ in range(3):
        if git("pull", "--rebase", "origin", "main").returncode == 0 and git("push").returncode == 0:
            return
        time.sleep(5)
    print("[!] salvataggio intermedio non riuscito", flush=True)


def main():
    """Lavora a rate: salva lo stato man mano e riparte da dove si era fermato."""
    S = sessione()
    indice = carica_comuni()
    stato = json.load(open(STATO, encoding="utf-8")) if os.path.exists(STATO) else {"pagine": {}, "fatti": {}, "versione": VERSIONE}
    if stato.get("versione", 1) < VERSIONE:
        da_rileggere = [u for u, el in stato["fatti"].items() if buchi(el)]
        for u in da_rileggere:
            del stato["fatti"][u]
        stato["versione"] = VERSIONE
        print(f"[i] {len(da_rileggere)} pagine da rileggere con la nuova lettura delle date", flush=True)
    # 1) elenco delle pagine dei comuni, regione per regione (una volta sola)
    for slug_reg, reg in REGIONI.items():
        if slug_reg in stato["pagine"]:
            continue
        h = S.get(f"{SITO}/{slug_reg}/storico-elezioni-comunali/", timeout=30).text
        province = sorted(set(re.findall(rf'href="(?:{SITO})?(/{slug_reg}/provincia-[^"/]+/storico-elezioni-comunali/)"', h)))
        pagine = province or [f"/{slug_reg}/storico-elezioni-comunali/"]
        comuni = set()
        for pp in pagine:
            time.sleep(PAUSA)
            hp = S.get(SITO + pp, timeout=30).text
            comuni |= set(re.findall(rf'href="(?:{SITO})?(/{slug_reg}/\d+-[^"/]+/storico-elezioni-comunali/)"', hp))
        stato["pagine"][slug_reg] = sorted(comuni)
        salva_stato(stato)
        print(f"[{slug_reg}] {len(province)} province, {len(comuni)} comuni", flush=True)
    # 2) le pagine dei comuni non ancora lette, qualche richiesta alla volta
    da_fare = [url for urls in stato["pagine"].values() for url in urls if url not in stato["fatti"]]
    print(f"[i] {len(da_fare)} comuni da leggere", flush=True)
    esiti, tempi, ultimo = {}, [], time.time()
    with ThreadPoolExecutor(LAVORATORI) as pool:
        attesi = {}
        coda = iter(da_fare)
        def avvia():
            if (time.time() - INIZIO) / 60 > LIMITE_MINUTI:
                return
            u = next(coda, None)
            if u:
                attesi[pool.submit(leggi, u)] = u
        for _ in range(LAVORATORI):
            avvia()
        while attesi:
            fut = next(as_completed(attesi))
            del attesi[fut]
            url, el, sec, err = fut.result()
            esiti[err or "ok"] = esiti.get(err or "ok", 0) + 1
            if err:
                time.sleep(ATTESA_ERRORE)  # il sito limita le richieste: dopo un rifiuto si aspetta di più
            if err is None:
                stato["fatti"][url] = el
                tempi.append(sec)
            avvia()
            if (time.time() - ultimo) / 60 > OGNI_MINUTI:
                ultimo = time.time()
                print(f"[{len(stato['fatti'])} letti] {esiti}", flush=True)
                pubblica(stato, indice, f"Comunali delle regioni a statuto speciale: {len(stato['fatti'])} comuni letti")
    salva_stato(stato)
    # 3) abbinamento ai codici dei comuni e unione con le date del Ministero
    trovati, non_trovati = applica(stato, indice)
    mancano = sum(1 for urls in stato["pagine"].values() for u in urls if u not in stato["fatti"])
    medio = sum(tempi) / len(tempi) if tempi else 0
    riepilogo = f"{len(trovati)} comuni con date, {len(non_trovati)} non abbinati, {mancano} ancora da leggere; esiti {esiti}; tempo medio {medio:.1f}s"
    print(f"[ok] {riepilogo}", flush=True)
    print(f"::notice title=Comunali speciali::{riepilogo}", flush=True)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"mancano={mancano}\n")


def unisci(trovati):
    """Riscrive dati/comunali.js aggiungendo le date trovate (le date del Ministero restano)."""
    p = os.path.join(RADICE, "dati", "comunali.js")
    js = open(p, encoding="utf-8").read()
    date = json.loads(re.search(r"const COMUNALI_DATE = (\[.*?\]);", js, re.S).group(1))
    righe = re.search(r"const COMUNALI_TXT = `(.*?)`;", js, re.S).group(1).split("\n")
    voti = {}
    for r in righe:
        if ":" not in r:
            continue
        cod, v = r.split(":")
        voti[cod] = {date[abs(int(i)) - 1]: int(i) < 0 for i in v.split(",")}
    def aggiungi(cod, d, ball, scarto=3, sostituisci=False):
        # una data a pochi giorni da una già presente è la stessa tornata (le fonti indicano a volte il secondo giorno di voto)
        v = voti.setdefault(cod, {})
        g = dt.date.fromisoformat(d)
        vicina = min((x for x in v if abs((dt.date.fromisoformat(x) - g).days) <= scarto), key=lambda x: abs((dt.date.fromisoformat(x) - g).days), default=None)
        if vicina and sostituisci and vicina != d:
            # la pagina del comune su tuttitalia.it vale più di un giorno sbagliato preso in passato dai riquadri di Wikipedia
            v[d] = v.pop(vicina) or bool(ball)
        elif vicina: v[vicina] = v[vicina] or bool(ball)
        else: v[d] = bool(ball)
    for cod, el in trovati.items():
        for d, ball in el:
            aggiungi(cod, d, ball, sostituisci=True)
    # comuni maggiori: tornate e ballottaggi da Wikipedia, dove tuttitalia.it non li riporta.
    # Entro 45 giorni da una data già nota è la stessa tornata (Wikipedia a volte sbaglia il giorno): si aggiunge solo il ballottaggio.
    wiki = os.path.join(RADICE, "strumenti", "ballottaggi-wikipedia.json")
    if os.path.exists(wiki):
        for t in json.load(open(wiki, encoding="utf-8"))["tornate"]:
            aggiungi(t["cod"], t["primo"], t["ballottaggio"], scarto=45)
    tutte = sorted({d for v in voti.values() for d in v})
    pos = {d: i for i, d in enumerate(tutte)}
    nuove = [f"{cod}:{','.join(str(-(pos[d] + 1) if b else pos[d] + 1) for d, b in sorted(v.items()))}" for cod, v in sorted(voti.items())]
    js = re.sub(r"const COMUNALI_DATE = \[.*?\];", lambda m: "const COMUNALI_DATE = " + json.dumps(tutte) + ";", js, flags=re.S)
    js = re.sub(r"const COMUNALI_TXT = `.*?`;", lambda m: "const COMUNALI_TXT = `" + "\n".join(nuove) + "`;", js, flags=re.S)
    if "tuttitalia" not in js:
        js = js.replace("// Generato da", "// Sicilia, Friuli-Venezia Giulia, Valle d'Aosta e Trentino-Alto Adige: tuttitalia.it.\n// Generato da", 1)
    open(p, "w", encoding="utf-8").write(js)


if __name__ == "__main__":
    main()
