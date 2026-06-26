"""Ingestão das malhas territoriais do IBGE (via geobr) e da população.

O geobr entrega GeoDataFrames já com 'code_muni' (código IBGE de 7 dígitos) e
'name_muni' — exatamente a chave para casar com a ANEEL sem depender de nomes.
"""
from __future__ import annotations

import geopandas as gpd
import pandas as pd
import requests

from . import config


def carregar_municipios() -> gpd.GeoDataFrame:
    """Polígonos municipais do Brasil (EPSG:4326). Colunas-chave: code_muni, name_muni, abbrev_state."""
    import geobr

    gdf = geobr.read_municipality(code_muni="all", year=config.IBGE_ANO_MALHA)
    gdf = gdf.to_crs("EPSG:4326")
    gdf["code_muni"] = pd.to_numeric(gdf["code_muni"], errors="coerce").astype("Int64")
    print(f"IBGE: {len(gdf):,} municípios (malha {config.IBGE_ANO_MALHA}).")
    return gdf


def carregar_estados() -> gpd.GeoDataFrame:
    """Polígonos estaduais (úteis para coropléticos por UF e bordas)."""
    import geobr

    gdf = geobr.read_state(code_state="all", year=config.IBGE_ANO_MALHA)
    return gdf.to_crs("EPSG:4326")


def carregar_populacao() -> pd.DataFrame:
    """População estimada por município, via API de agregados do IBGE.

    Retorna DataFrame com code_muni (Int64) e populacao (int). Necessária para
    o indicador de potência instalada per capita. Se a API mudar, ajuste a URL
    em config.IBGE_POP_API / IBGE_POP_ANO.
    """
    url = config.IBGE_POP_API.format(ano=config.IBGE_POP_ANO)
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    dados = r.json()

    registros = []
    for serie in dados[0]["resultados"][0]["series"]:
        code = serie["localidade"]["id"]
        valor = list(serie["serie"].values())[0]
        if valor not in (None, "...", "-"):
            registros.append((int(code), int(valor)))

    df = pd.DataFrame(registros, columns=["code_muni", "populacao"])
    df["code_muni"] = df["code_muni"].astype("Int64")
    print(f"IBGE população: {len(df):,} municípios ({config.IBGE_POP_ANO}).")
    return df
