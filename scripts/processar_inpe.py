"""Junção espacial da grade INPE (GTI) com os polígonos municipais -> GTI por município.

Sem geopandas: usa shapely + STRtree (índice espacial) direto.
 1. Lê os pontos da grade (LON, LAT, ANNUAL) do CSV do INPE.
 2. Lê os polígonos municipais simplificados (data/interim/mun_simpl.geojson).
 3. Ponto-em-polígono vetorizado -> média de GTI por município (Wh -> kWh/m².dia).
 4. Fallback: municípios sem ponto interno recebem o ponto da grade mais próximo do centroide.
Saída: data/interim/gti_por_municipio.json  ({code: gti_kwh}).
"""
from __future__ import annotations

import csv
import io
import json
import zipfile
from pathlib import Path

import numpy as np
from shapely import STRtree, points
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / "data" / "raw" / "inpe_gti.zip"
GEO = ROOT / "data" / "interim" / "mun_simpl.geojson"
OUT = ROOT / "data" / "interim" / "gti_por_municipio.json"


def _carregar_pontos() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    nome = next(n for n in zipfile.ZipFile(ZIP).namelist() if n.lower().endswith(".csv"))
    lon, lat, anual = [], [], []
    with zipfile.ZipFile(ZIP).open(nome) as f:
        leitor = csv.reader(io.TextIOWrapper(f, encoding="latin-1"), delimiter=";")
        next(leitor)  # header
        for r in leitor:
            lon.append(float(r[2])); lat.append(float(r[3])); anual.append(float(r[4]))
    return np.array(lon), np.array(lat), np.array(anual)


def processar() -> dict:
    lon, lat, anual = _carregar_pontos()
    print(f"INPE: {len(lon):,} pontos da grade carregados.")

    geo = json.loads(GEO.read_text(encoding="utf-8"))
    feats = [f for f in geo["features"] if f.get("geometry")]  # ignora geometria nula
    pulados = len(geo["features"]) - len(feats)
    if pulados:
        print(f"  aviso: {pulados} município(s) sem geometria — ficarão sem GTI.")
    codes = [f["properties"]["code"] for f in feats]
    polos = [shape(f["geometry"]) for f in feats]
    tree = STRtree(polos)

    pts = points(lon, lat)
    # Pares (idx_ponto, idx_poligono) onde o ponto cai dentro do polígono.
    idx_pt, idx_pol = tree.query(pts, predicate="intersects")

    soma = np.zeros(len(polos)); cont = np.zeros(len(polos))
    np.add.at(soma, idx_pol, anual[idx_pt])
    np.add.at(cont, idx_pol, 1)

    # Fallback: municípios sem nenhum ponto interno -> ponto mais próximo do centroide.
    falt = np.where(cont == 0)[0]
    if len(falt):
        tree_pts = STRtree(pts)
        for i in falt:
            if polos[i].is_empty:
                continue
            j = tree_pts.nearest(polos[i].representative_point())
            soma[i] = anual[j]; cont[i] = 1
    print(f"  municípios por polígono: {int((cont > 0).sum()):,} | fallback centroide: {len(falt):,}")

    gti = {codes[i]: round(soma[i] / cont[i] / 1000.0, 3) for i in range(len(polos)) if cont[i] > 0}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(gti, ensure_ascii=False), encoding="utf-8")
    vals = np.array(list(gti.values()))
    print(f"OK: GTI de {len(gti):,} municípios ({vals.min():.2f}–{vals.max():.2f} kWh/m².dia). "
          f"Salvo em {OUT.relative_to(ROOT)}")
    return gti


if __name__ == "__main__":
    processar()
