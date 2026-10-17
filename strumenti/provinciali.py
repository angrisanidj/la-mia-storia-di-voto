"""Costruisce dati/provinciali.js: le elezioni provinciali dirette (presidente e
consiglio) dal 1993 al 2011, lette dall'Archivio storico delle elezioni del
Ministero dell'Interno, con i candidati presidente, le liste e i ballottaggi, e
per ogni comune le elezioni provinciali a cui ha partecipato (così valgono anche i
confini di allora: Monza e Brianza dal 2009, le province sarde dal 2005...).

Dal 2014 (legge 56/2014) le province sono enti di secondo livello: i cittadini
non votano più. Trento e Bolzano restano a parte (dati/elezioni.js).

Gira su GitHub Actions (.github/workflows/provinciali.yml), con le funzioni di
navigazione di tallyho (MIT, github.com/jack89-ML/tallyho).
"""
import datetime as dt
import json
import os
import re
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comunali import REGIONI, RADICE, carica_comuni, compatta, norm, sessione  # noqa: E402
from tallyho.costanti import BASE  # noqa: E402
from tallyho.navigazione import leggi_onchange, leggi_select, scendi_livello  # noqa: E402
from tallyho.parsing import estrai_tabelle, parse_candidati, parse_candidati_regionali  # noqa: E402

SOLO_PROVA = os.environ.get("SOLO_PROVA") == "1"
DAL, AL = dt.date(1993, 1, 1), dt.date(2013, 12, 31)
# province soppresse o rinominate che non sono più in province.json
PROVINCE_STORICHE = {"CARBONIA IGLESIAS": "CI", "OGLIASTRA": "OG", "OLBIA TEMPIO": "OT", "MEDIO CAMPIDANO": "VS",
                     "FORLI": "FC", "PESARO URBINO": "PU", "PESARO E URBINO": "PU", "VERBANO CUSIO OSSOLA": "VB",
                     "MASSA CARRARA": "MS", "REGGIO EMILIA": "RE", "REGGIO NELL EMILIA": "RE", "REGGIO CALABRIA": "RC",
                     "MONZA E DELLA BRIANZA": "MB", "MONZA BRIANZA": "MB", "BARLETTA ANDRIA TRANI": "BT", "BOLZANO BOZEN": "BZ"}


def selects(h):
    return re.findall(r'<select[^>]*(?:id|name)="([^"]+)"', h)


def main():
    S = sessione()
    indice = carica_comuni()
    prov = {norm(v): k for k, v in json.load(open(os.path.join(RADICE, "strumenti", "province.json"))).items()}
    prov.update(PROVINCE_STORICHE)
    h = S.get(f"{BASE}?tpel=P").text
    date = []
    for _, t in leggi_select(h, "sel_date"):
        m = re.match(r"(\d{2})/(\d{2})/(\d{4})", t.strip())
        if m:
            d = dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            if DAL <= d <= AL:
                date.append((d, t.strip()))
    date.sort()
    print(f"::notice title=date::{len(date)} date di provinciali: {[d.isoformat() for d, _ in date]}", flush=True)
    if SOLO_PROVA:
        date = [x for x in date if x[0].year == 2004][:1] or date[:1]

    elezioni = {}      # "SIGLA-data" -> {"n": nome, "b": ballottaggio, "c": candidati}
    comuni_di = {}     # codice comune -> [chiavi]
    non_trovati = set()
    for d, testo in date:
        iso = d.isoformat()
        try:
            h = S.get(f"{BASE}?tpel=P&dtel={testo}").text
            aree = leggi_select(h, "sel_aree")
            if not aree:
                print(f"::warning title=area::{iso}: nessuna area; select: {selects(h)}", flush=True)
                continue
            pp, pv = leggi_onchange(h, "sel_aree")
            area = next((a for a in aree if a[1].strip().upper() == "ITALIA"), aree[0])
            h2 = scendi_livello(S, pp or f"index.php?tpel=P&dtel={testo}&es0=S", "tpa", area[0])
            pp2, pv2 = leggi_onchange(h2, "sel_sezione2")
            n = 0
            for rv, rt in leggi_select(h2, "sel_sezione2"):
                reg = REGIONI.get(norm(rt))
                h3 = scendi_livello(S, pp2, pv2, rv)
                pp3, pv3 = leggi_onchange(h3, "sel_sezione3")
                province = leggi_select(h3, "sel_sezione3")
                if SOLO_PROVA:
                    print(f"::notice title=prova:: {iso} {rt}: select {selects(h3)}; province {[p[1] for p in province][:12]}", flush=True)
                for pvv, pt in province:
                    sig = prov.get(norm(pt)) or norm(pt)
                    if sig == norm(pt):
                        print(f"::warning title=sigla::provincia senza sigla: {pt}", flush=True)
                    h4 = scendi_livello(S, pp3, pv3, pvv)
                    cand = parse_candidati(estrai_tabelle(h4)) or parse_candidati_regionali(h4)
                    ball = bool(re.search(r"II\s*turno", h4, re.I))
                    chiave = f"{sig}-{iso}"
                    elezioni[chiave] = {"n": pt.strip().title(), "b": 1 if ball else 0, "c": compatta(cand) if cand else []}
                    comuni = leggi_select(h4, "sel_sezione4")
                    if SOLO_PROVA and n < 2:
                        print(f"::notice title=prova:: {pt}: select {selects(h4)}; {len(comuni)} comuni; ballottaggio {ball}; candidati {json.dumps(elezioni[chiave]['c'][:3], ensure_ascii=False)[:600]}", flush=True)
                    for _, ct in comuni:
                        c = indice.get((reg, norm(ct)), [])
                        if len(c) > 1:
                            c = [x for x in c if x[1] == sig] or c
                        if not c:
                            tutti = [x for (r, nn), v in indice.items() if nn == norm(ct) for x in v]
                            c = [x for x in tutti if x[1] == sig] or (tutti if len(tutti) == 1 else [])
                        if not c:
                            non_trovati.add(f"{iso}\t{pt}\t{ct}")
                            continue
                        comuni_di.setdefault(c[0][0], []).append(chiave)
                    n += 1
            print(f"::notice title={iso}::{n} province", flush=True)
        except requests.RequestException as e:
            print(f"[!] {iso}: {e}", flush=True)
    scrivi(elezioni, comuni_di, non_trovati)


def scrivi(elezioni, comuni_di, non_trovati):
    chiavi = sorted(elezioni, key=lambda k: (k.split("-", 1)[1], k))
    pos = {k: i for i, k in enumerate(chiavi)}
    righe = [f"{cod}:{','.join(str(pos[k]) for k in sorted(set(ks), key=lambda k: pos[k]))}" for cod, ks in sorted(comuni_di.items())]
    voci = [[k, elezioni[k]["n"], elezioni[k]["b"], elezioni[k]["c"]] for k in chiavi]
    js = ("// Elezioni provinciali dirette 1993-2011, dall'Archivio storico delle elezioni (Ministero dell'Interno).\n"
          "// Generato da strumenti/provinciali.py: non modificare a mano.\n"
          "// PROVINCIALI: [chiave sigla-data, provincia, ballottaggio, candidati [[nome, %, [[lista, %]]]]].\n"
          "// PROVINCIALI_COMUNI: codice catastale -> indici in PROVINCIALI (i confini di allora).\n"
          f"const PROVINCIALI_AGGIORNATE = '{dt.date.today().isoformat()}';\n"
          f"const PROVINCIALI = {json.dumps(voci, ensure_ascii=False, separators=(',', ':'))};\n"
          f"const PROVINCIALI_COMUNI = `{chr(10).join(righe)}`;\n")
    with open(os.path.join(RADICE, "dati", "provinciali.js"), "w", encoding="utf-8") as f:
        f.write(js)
    with open(os.path.join(RADICE, "strumenti", "provinciali-non-trovati.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(non_trovati)) + "\n")
    print(f"::notice title=fine::{len(elezioni)} elezioni provinciali, {len(comuni_di)} comuni, {len(non_trovati)} nomi non abbinati", flush=True)


if __name__ == "__main__":
    main()
