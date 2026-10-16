"""Costruisce dati/comunali.js: per ogni comune, le date delle elezioni comunali
(e dei ballottaggi) dal 1993 a oggi, lette dall'Archivio storico delle elezioni del
Ministero dell'Interno (elezionistorico.interno.gov.it).

Gira su GitHub Actions (.github/workflows/comunali.yml). Usa le funzioni di
navigazione del pacchetto tallyho (MIT, github.com/jack89-ML/tallyho).

Uscite:
  dati/comunali.js                      COMUNALI_DATE (elenco date) e COMUNALI
                                        (codice catastale -> indici delle date,
                                        con ballottaggio segnato come negativo)
  strumenti/comunali-non-trovati.txt    nomi dell'archivio non abbinati a un comune
"""
import datetime as dt
import json
import os
import re
import sys
import time
import unicodedata

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from tallyho.costanti import BASE, UA
from tallyho.navigazione import leggi_onchange, leggi_select, scendi_livello

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAL = dt.date(1993, 1, 1)
PAUSA = float(os.environ.get("PAUSA", "0.15"))
LIMITE_MINUTI = float(os.environ.get("LIMITE_MINUTI", "320"))
SOLO_PROVA = os.environ.get("SOLO_PROVA") == "1"
INIZIO = time.time()

REGIONI = {
    "PIEMONTE": "01", "VALLE D AOSTA": "02", "VALLE D AOSTA VALLEE D AOSTE": "02", "LOMBARDIA": "03",
    "TRENTINO ALTO ADIGE": "04", "TRENTINO ALTO ADIGE SUDTIROL": "04", "VENETO": "05",
    "FRIULI VENEZIA GIULIA": "06", "LIGURIA": "07", "EMILIA ROMAGNA": "08", "TOSCANA": "09",
    "UMBRIA": "10", "MARCHE": "11", "LAZIO": "12", "ABRUZZO": "13", "ABRUZZI": "13", "MOLISE": "14",
    "CAMPANIA": "15", "PUGLIA": "16", "BASILICATA": "17", "CALABRIA": "18", "SICILIA": "19", "SARDEGNA": "20",
}


def norm(s):
    s = unicodedata.normalize("NFD", s.upper())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[’'`\-/.,()]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def sessione():
    s = requests.Session()
    s.headers["User-Agent"] = UA
    r = Retry(total=6, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
    s.mount("https://", HTTPAdapter(max_retries=r))
    orig = s.get

    def get(url, **kw):
        time.sleep(PAUSA)
        kw.setdefault("timeout", 60)
        return orig(url, **kw)
    s.get = get
    return s


def carica_comuni():
    testo = open(os.path.join(RADICE, "dati", "comuni.js"), encoding="utf-8").read()
    righe = testo.split("`")[1].split("\n")
    indice = {}  # (regione, nome normalizzato) -> [(codice, sigla)]
    for r in righe:
        nome, sig, reg, cod, att, alias = r.split("|")
        for n in [nome] + [a for a in alias.split(";") if a]:
            indice.setdefault((reg, norm(n)), []).append((cod, sig))
    return indice


def main():
    S = sessione()
    indice = carica_comuni()
    prov = {norm(v): k for k, v in json.load(open(os.path.join(RADICE, "strumenti", "province.json"))).items()}
    grandi = set(json.load(open(os.path.join(RADICE, "strumenti", "sopra9000.json"))))

    h = S.get(f"{BASE}?tpel=G").text
    date = []
    for _, t in leggi_select(h, "sel_date"):
        m = re.match(r"(\d{2})/(\d{2})/(\d{4})", t.strip())
        if m:
            d = dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            if d >= DAL:
                date.append((d, t.strip()))
    date.sort()
    print(f"[i] {len(date)} date di comunali dal {DAL}", flush=True)
    if SOLO_PROVA:
        date = [x for x in date if x[0].year == 2016][:1]

    voti = {}          # codice -> {data_iso: ballottaggio?}
    non_trovati = set()
    for i, (d, testo_data) in enumerate(date):
        if (time.time() - INIZIO) / 60 > LIMITE_MINUTI:
            print("[!] tempo esaurito: interrompo, i dati restano parziali", flush=True)
            break
        iso = d.isoformat()
        h = S.get(f"{BASE}?tpel=G&dtel={testo_data}").text
        aree = leggi_select(h, "sel_aree")
        if not aree:
            continue
        pp, pv = leggi_onchange(h, "sel_aree")
        area = next((a for a in aree if a[1].strip().upper() == "ITALIA"), aree[0])
        h = scendi_livello(S, pp or f"index.php?tpel=G&dtel={testo_data}&es0=S", "tpa", area[0])
        regioni = leggi_select(h, "sel_sezione2")
        pp2, pv2 = leggi_onchange(h, "sel_sezione2")
        n_data = 0
        for rv, rt in regioni:
            reg = REGIONI.get(norm(rt))
            if not reg:
                print(f"[?] regione non riconosciuta: {rt}", flush=True)
                continue
            h3 = scendi_livello(S, pp2, pv2, rv)
            liv3 = leggi_select(h3, "sel_sezione3")
            pp3, pv3 = leggi_onchange(h3, "sel_sezione3")
            # il livello 3 sono province se i nomi corrispondono a province note
            sono_province = liv3 and sum(norm(t) in prov for _, t in liv3) >= max(1, len(liv3) // 2)
            gruppi = []
            if sono_province:
                for pvv, pt in liv3:
                    h4 = scendi_livello(S, pp3, pv3, pvv)
                    comuni = leggi_select(h4, "sel_sezione4")
                    pp4, pv4 = leggi_onchange(h4, "sel_sezione4")
                    gruppi.append((prov.get(norm(pt)), comuni, pp4, pv4))
            else:
                gruppi.append((None, liv3, pp3, pv3))
            for sigla, comuni, ppc, pvc in gruppi:
                for cv, ct in comuni:
                    cand = indice.get((reg, norm(ct)), [])
                    if len(cand) > 1 and sigla:
                        cand = [c for c in cand if c[1] == sigla] or cand
                    if not cand:
                        non_trovati.add(f"{iso}\t{rt}\t{sigla or ''}\t{ct}")
                        continue
                    cod = cand[0][0]
                    ball = False
                    if cod in grandi and ppc:
                        try:
                            pagina = scendi_livello(S, ppc, pvc, cv)
                            ball = bool(re.search(r"II\s*turno", pagina, re.I))
                        except Exception as e:  # una pagina mancante non ferma tutto
                            print(f"[!] {iso} {ct}: {e}", flush=True)
                    voti.setdefault(cod, {})[iso] = ball
                    n_data += 1
        print(f"[{i + 1}/{len(date)}] {iso}: {n_data} comuni", flush=True)

    scrivi(voti, non_trovati)


def scrivi(voti, non_trovati):
    tutte = sorted({d for v in voti.values() for d in v})
    pos = {d: i for i, d in enumerate(tutte)}
    righe = []
    for cod in sorted(voti):
        idx = [(-(pos[d] + 1) if b else pos[d] + 1) for d, b in sorted(voti[cod].items())]
        righe.append(f"{cod}:{','.join(map(str, idx))}")
    aggiornato = dt.date.today().isoformat()
    js = ("// Elezioni comunali per comune, dall'Archivio storico delle elezioni (Ministero dell'Interno).\n"
          "// Generato da strumenti/comunali.py: non modificare a mano.\n"
          "// COMUNALI: codice catastale -> indici (base 1) in COMUNALI_DATE; negativo = con ballottaggio.\n"
          f"const COMUNALI_AGGIORNATE = '{aggiornato}';\n"
          f"const COMUNALI_DATE = {json.dumps(tutte)};\n"
          f"const COMUNALI_TXT = `{chr(10).join(righe)}`;\n")
    with open(os.path.join(RADICE, "dati", "comunali.js"), "w", encoding="utf-8") as f:
        f.write(js)
    with open(os.path.join(RADICE, "strumenti", "comunali-non-trovati.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(non_trovati)) + "\n")
    print(f"[ok] {len(voti)} comuni, {len(tutte)} date, {len(non_trovati)} nomi non abbinati", flush=True)


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as e:
        print(f"[x] archivio non raggiungibile: {e}", file=sys.stderr)
        sys.exit(1)
