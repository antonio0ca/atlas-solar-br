"""Monta o GeoJSON que o frontend consome (web/public/data/atlas_uf.geojson).

Junta a geometria (malha do IBGE) com os valores de recurso (GTI) e uso (potência FV).

Dois modos:
  --demo  : usa valores plausíveis embutidos (para desenvolver o frontend já com o
            mapa "vivo" antes de rodar o pipeline completo). É o padrão atual.
  (futuro): ler data/processed/atlas_municipios.parquet e gerar atlas_municipios.geojson
            no nível municipal. A estrutura de propriedades é a mesma — o frontend
            é agnóstico ao nível (uf/mun).

Uso:  python scripts/montar_dados_web.py --demo
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_UF = ROOT / "data" / "raw" / "brazil-states.geojson"
OUT_UF = ROOT / "web" / "public" / "data" / "atlas_uf.geojson"

# ── Valores DEMO por UF (plausíveis, p/ desenvolver o frontend) ──────────────
# gti: irradiação no plano inclinado, kWh/m².dia (ordem de grandeza real).
# pot_mw: potência FV de geração distribuída instalada, MW (ranking real-ish).
# pop: população (milhões) para o per capita.
DEMO = {
    # NE — muito sol
    "BA": (5.80, 1900, 14.9), "CE": (5.90, 1100, 9.2), "PE": (5.80, 900, 9.7),
    "PI": (5.95, 400, 3.3), "RN": (5.90, 500, 3.6), "PB": (5.85, 500, 4.1),
    "SE": (5.70, 300, 2.3), "AL": (5.70, 350, 3.4), "MA": (5.55, 600, 7.1),
    # SE
    "MG": (5.60, 5200, 21.4), "SP": (5.30, 4800, 46.6), "RJ": (5.20, 1300, 17.5),
    "ES": (5.30, 700, 4.1),
    # S — menos sol, muito uso
    "PR": (5.10, 2600, 11.6), "SC": (4.90, 2100, 7.3), "RS": (5.20, 3500, 11.5),
    # CO
    "GO": (5.60, 1700, 7.2), "MT": (5.55, 1600, 3.6), "MS": (5.40, 1200, 2.8),
    "DF": (5.60, 450, 3.1),
    # N
    "TO": (5.60, 350, 1.6), "PA": (5.00, 700, 8.7), "AP": (4.90, 70, 0.9),
    "RR": (5.10, 90, 0.6), "AM": (4.80, 250, 4.3), "AC": (4.90, 90, 0.9),
    "RO": (5.10, 350, 1.8),
}


def _percentis(valores: list[float]) -> dict[float, float]:
    """Mapa valor -> percentil (rank/N), para comparar recurso e uso em escala 0–1."""
    ordenado = sorted(valores)
    n = len(ordenado)
    return {v: (i + 1) / n for i, v in enumerate(ordenado)}


def _classe(pct_rec: float, pct_uso: float, tem_dado: bool) -> str:
    if not tem_dado:
        return "sem dado"
    alto_rec, baixo_uso, alto_uso = pct_rec >= 0.66, pct_uso <= 0.33, pct_uso >= 0.66
    if alto_rec and baixo_uso:
        return "deserto de aproveitamento"
    if alto_rec and alto_uso:
        return "recurso e uso altos"
    if not alto_rec and alto_uso:
        return "uso acima do recurso"
    return "intermediário"


def montar_demo() -> None:
    geo = json.loads(RAW_UF.read_text(encoding="utf-8"))

    # Calcula W/hab e percentis nacionais.
    wpc = {uf: (pot * 1e6) / (pop * 1e6) for uf, (gti, pot, pop) in DEMO.items()}  # W/hab
    pr = _percentis([g for g, _, _ in DEMO.values()])
    pu = _percentis(list(wpc.values()))

    feats = []
    for f in geo["features"]:
        sigla = f["properties"]["sigla"]
        if sigla not in DEMO:
            continue
        gti, pot, pop = DEMO[sigla]
        props = {
            "code": str(f["properties"]["codigo_ibg"]),
            "name": f["properties"]["name"],
            "uf": sigla,
            "level": "uf",
            "gti_anual": round(gti, 2),
            "pot_instalada_mw": round(pot, 1),
            "w_per_capita": round(wpc[sigla], 1),
            "score_oportunidade": round(pr[gti] - pu[wpc[sigla]], 3),
            "classe_oportunidade": _classe(pr[gti], pu[wpc[sigla]], True),
        }
        feats.append({"type": "Feature", "properties": props, "geometry": f["geometry"]})

    out = {"type": "FeatureCollection", "meta": {
        "fonte": "DEMO — valores ilustrativos. Substituir pelo pipeline (INPE/ANEEL/IBGE).",
        "nivel": "uf"}, "features": feats}

    OUT_UF.parent.mkdir(parents=True, exist_ok=True)
    OUT_UF.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    kb = OUT_UF.stat().st_size / 1024
    desertos = [f["properties"]["uf"] for f in feats
                if f["properties"]["classe_oportunidade"] == "deserto de aproveitamento"]
    print(f"OK: {OUT_UF.relative_to(ROOT)} ({len(feats)} UFs, {kb:.0f} KB)")
    print("Desertos de aproveitamento (demo):", ", ".join(sorted(desertos)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="gera atlas_uf.geojson com valores demo")
    args = ap.parse_args()
    # Por ora só o modo demo está implementado; o modo municipal entra no M1/M2.
    montar_demo()
