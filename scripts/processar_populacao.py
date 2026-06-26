"""População por município via API de Agregados do IBGE -> data/interim/populacao.json.

Tabela 6579 (população residente estimada), variável 9324, todos os municípios (N6).
Necessária para o indicador de potência instalada per capita.
"""
from __future__ import annotations

import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "interim" / "populacao.json"
ANO = 2021
URL = f"https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/{ANO}/variaveis/9324?localidades=N6[all]"


def processar() -> dict:
    r = requests.get(URL, timeout=120)
    r.raise_for_status()
    series = r.json()[0]["resultados"][0]["series"]

    pop = {}
    for s in series:
        code = s["localidade"]["id"]
        valor = next(iter(s["serie"].values()))
        if valor not in (None, "...", "-", ""):
            pop[code] = int(valor)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(pop, ensure_ascii=False), encoding="utf-8")
    print(f"OK: população de {len(pop):,} municípios ({ANO}). Salvo em {OUT.relative_to(ROOT)}")
    return pop


if __name__ == "__main__":
    processar()
