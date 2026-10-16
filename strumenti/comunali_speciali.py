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
import time
import unicodedata

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITO = "https://www.tuttitalia.it"
REGIONI = {"sicilia": "19", "friuli-venezia-giulia": "06", "valle-d-aosta": "02", "trentino-alto-adige": "04"}
PAUSA = float(os.environ.get("PAUSA_TT", "1.0"))
MESI = {m: i + 1 for i, m in enumerate(["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
                                        "agosto", "settembre", "ottobre", "novembre", "dicembre"])}
DATA_RE = re.compile(r"(\d{1,2})(?:\s*(?:e|-)\s*\d{1,2})?\s+(" + "|".join(MESI) + r")\s+(\d{4})", re.I)


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def sessione():
    s = requests.Session()
    s.headers["User-Agent"] = "la-mia-storia-di-voto (github.com/angrisanidj/la-mia-storia-di-voto)"
    s.mount("https://", HTTPAdapter(max_retries=Retry(total=5, backoff_factor=3, status_forcelist=[429, 500, 502, 503, 504])))
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


def main():
    S = sessione()
    indice = carica_comuni()
    trovati, non_trovati = {}, []
    for slug_reg, reg in REGIONI.items():
        h = S.get(f"{SITO}/{slug_reg}/storico-elezioni-comunali/", timeout=60).text
        province = sorted(set(re.findall(rf'href="(?:{SITO})?(/{slug_reg}/provincia-[^"/]+/storico-elezioni-comunali/)"', h)))
        # la Valle d'Aosta non ha province: i comuni sono già nella pagina regionale
        pagine = province or [f"/{slug_reg}/storico-elezioni-comunali/"]
        comuni = set()
        for pp in pagine:
            time.sleep(PAUSA)
            hp = S.get(SITO + pp, timeout=60).text
            comuni |= set(re.findall(rf'href="(?:{SITO})?(/{slug_reg}/\d+-[^"/]+/storico-elezioni-comunali/)"', hp))
        print(f"[{slug_reg}] {len(province)} province, {len(comuni)} comuni", flush=True)
        for url in sorted(comuni):
            time.sleep(PAUSA)
            nome = re.match(rf"/{slug_reg}/\d+-([^/]+)/", url).group(1).replace("-", " ")
            cand = indice.get((reg, norm(nome)), [])
            if not cand:
                non_trovati.append(f"{reg}\t{url}")
                continue
            cod = sorted(cand, key=lambda c: not c[1])[0][0]
            try:
                el = elezioni_comune(S.get(SITO + url, timeout=60).text)
            except requests.RequestException as e:
                print(f"[!] {url}: {e}", flush=True)
                continue
            if el:
                trovati[cod] = el
    unisci(trovati)
    with open(os.path.join(RADICE, "strumenti", "comunali-speciali-non-trovati.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(non_trovati) + "\n")
    print(f"[ok] {len(trovati)} comuni delle regioni a statuto speciale, {len(non_trovati)} non abbinati", flush=True)


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
    for cod, el in trovati.items():
        for d, ball in el:
            voti.setdefault(cod, {})[d] = bool(ball) or voti.get(cod, {}).get(d, False)
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
