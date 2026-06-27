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


# ─────────────────────────────────────────────────────────────────────────────
# Modo REAL — nível municipal, a partir dos insumos processados.
# ─────────────────────────────────────────────────────────────────────────────
INTERIM = ROOT / "data" / "interim"
RAW_UF_GEO = ROOT / "data" / "raw" / "brazil-states.geojson"
OUT_MUN = ROOT / "web" / "public" / "data" / "atlas_municipios.geojson"


def _mapa_uf_por_codigo() -> dict[str, str]:
    """Código IBGE do estado (2 díg.) -> sigla da UF, a partir da malha estadual."""
    geo = json.loads(RAW_UF_GEO.read_text(encoding="utf-8"))
    return {str(f["properties"]["codigo_ibg"]): f["properties"]["sigla"] for f in geo["features"]}


# Macrorregião do IBGE por sigla de UF.
REGIAO_POR_UF = {
    **{uf: "Norte" for uf in ["AC", "AP", "AM", "PA", "RO", "RR", "TO"]},
    **{uf: "Nordeste" for uf in ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"]},
    **{uf: "Centro-Oeste" for uf in ["DF", "GO", "MT", "MS"]},
    **{uf: "Sudeste" for uf in ["ES", "MG", "RJ", "SP"]},
    **{uf: "Sul" for uf in ["PR", "RS", "SC"]},
}


def _percentil_array(valores):
    import numpy as np
    a = np.asarray(valores, dtype=float)
    ordem = a.argsort()
    rank = np.empty_like(ordem, dtype=float)
    rank[ordem] = (np.arange(len(a)) + 1) / len(a)
    return rank


def montar_real() -> None:
    import numpy as np

    geo = json.loads((INTERIM / "mun_simpl.geojson").read_text(encoding="utf-8"))
    gti = json.loads((INTERIM / "gti_por_municipio.json").read_text(encoding="utf-8"))
    aneel = json.loads((INTERIM / "aneel_por_municipio.json").read_text(encoding="utf-8"))
    pop = json.loads((INTERIM / "populacao.json").read_text(encoding="utf-8"))
    uf_por_cod = _mapa_uf_por_codigo()

    # Monta linhas com valores; calcula W/hab e densidade de adoção onde houver população.
    linhas = []
    for f in geo["features"]:
        if not f.get("geometry"):
            continue
        code = str(f["properties"]["code"])
        info = aneel.get(code, {})
        pot_kw = info.get("pot_kw", 0.0)
        n_emp = info.get("n", 0)
        habit = pop.get(code)
        wpc = (pot_kw * 1000.0) / habit if habit else None        # W/hab
        dens = (n_emp / habit * 1000.0) if habit else None         # empreend. por mil hab
        uf = info.get("uf") or uf_por_cod.get(code[:2], "")
        linhas.append({
            "f": f, "code": code,
            "name": f["properties"]["nome"], "uf": uf,
            "regiao": REGIAO_POR_UF.get(uf, ""),
            "gti": gti.get(code),
            "pot_mw": pot_kw / 1000.0, "n_emp": n_emp,
            "wpc": wpc, "dens": dens, "pop": habit,
        })

    # Percentis nacionais (só entre municípios com recurso e uso definidos).
    validos = [r for r in linhas if r["gti"] is not None and r["wpc"] is not None]
    pr = dict(zip([r["code"] for r in validos], _percentil_array([r["gti"]["anual"] for r in validos])))
    pu = dict(zip([r["code"] for r in validos], _percentil_array([r["wpc"] for r in validos])))

    feats = []
    for r in linhas:
        p_rec = pr.get(r["code"])
        p_uso = pu.get(r["code"])
        tem = p_rec is not None and p_uso is not None
        score = round(float(p_rec - p_uso), 3) if tem else None
        g = r["gti"]
        feats.append({
            "type": "Feature",
            "properties": {
                "code": r["code"], "name": r["name"], "uf": r["uf"], "regiao": r["regiao"],
                "level": "mun",
                "gti_anual": round(g["anual"], 2) if g else None,
                "gti_meses": [round(m, 2) for m in g["meses"]] if g else None,
                "pot_instalada_mw": round(r["pot_mw"], 2),
                "n_empreendimentos": r["n_emp"],
                "densidade_adocao": round(r["dens"], 2) if r["dens"] is not None else None,
                "populacao": r["pop"],
                "w_per_capita": round(r["wpc"], 1) if r["wpc"] is not None else None,
                "score_oportunidade": score,
                "classe_oportunidade": _classe(p_rec or 0, p_uso or 0, tem),
            },
            "geometry": r["f"]["geometry"],
        })

    out = {"type": "FeatureCollection", "meta": {
        "fonte": "LABREN/CCST/INPE (GTI), ANEEL (GD fotovoltaica), IBGE (malha/população)",
        "nivel": "mun"}, "features": feats}
    OUT_MUN.parent.mkdir(parents=True, exist_ok=True)
    OUT_MUN.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")

    mb = OUT_MUN.stat().st_size / 1e6
    desertos = sum(1 for f in feats if f["properties"]["classe_oportunidade"] == "deserto de aproveitamento")
    pot_total = sum(f["properties"]["pot_instalada_mw"] for f in feats) / 1000
    print(f"OK: {OUT_MUN.relative_to(ROOT)} ({len(feats):,} municípios, {mb:.1f} MB)")
    print(f"   {pot_total:,.1f} GW FV · {desertos:,} desertos de aproveitamento")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="gera atlas_uf.geojson (valores demo)")
    ap.add_argument("--real", action="store_true", help="gera atlas_municipios.geojson (dados reais)")
    args = ap.parse_args()
    if args.real:
        montar_real()
    else:
        montar_demo()
