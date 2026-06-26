"""Ingestão da grade de irradiação do INPE/LABREN.

A grade é um conjunto de ~72.272 pontos (0,1°) com médias anuais e mensais.
Carregamos como GeoDataFrame de pontos para, depois, fazer a junção espacial
com os polígonos municipais do IBGE (ver aggregate.py).
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

from . import config


def inspecionar_cabecalho(csv_path: Path, n: int = 3) -> pd.DataFrame:
    """Lê só as primeiras linhas para conferir nomes de colunas e separador.

    Use isto na PRIMEIRA execução: os nomes em config.INPE_* são o esperado,
    mas confirme contra o arquivo real antes de confiar.
    """
    df = pd.read_csv(csv_path, sep=";", decimal=".", nrows=n)
    print("Colunas encontradas:", list(df.columns))
    return df


def _achar_csv(variavel: str) -> Path:
    """Localiza o .csv extraído da variável (o zip pode conter 1 csv com nome longo)."""
    pasta = config.INTERIM / f"inpe_{variavel}"
    csvs = sorted(pasta.glob("*.csv"))
    if not csvs:
        raise FileNotFoundError(
            f"Nenhum CSV em {pasta}. Rode download.baixar_inpe('{variavel}') antes."
        )
    return csvs[0]


def carregar_grade(variavel: str = "gti") -> gpd.GeoDataFrame:
    """Carrega a grade INPE de uma variável como GeoDataFrame de pontos (EPSG:4326).

    Converte irradiação de Wh/m².dia -> kWh/m².dia. Renomeia colunas para um
    padrão estável: lon, lat, <var>_anual, <var>_jan..<var>_dez.
    """
    csv_path = _achar_csv(variavel)
    df = pd.read_csv(csv_path, sep=";", decimal=".")

    # Normaliza nomes (a fonte usa MAIÚSCULAS; toleramos variações).
    cols = {c.upper(): c for c in df.columns}
    lon = cols.get(config.INPE_COL_LON, config.INPE_COL_LON)
    lat = cols.get(config.INPE_COL_LAT, config.INPE_COL_LAT)
    anual = cols.get(config.INPE_COL_ANUAL, config.INPE_COL_ANUAL)

    out = pd.DataFrame({
        "lon": df[lon].astype(float),
        "lat": df[lat].astype(float),
        f"{variavel}_anual": df[anual].astype(float) / 1000.0,  # Wh -> kWh
    })
    for mes_src, mes_dst in zip(config.INPE_COLS_MESES, range(1, 13)):
        col = cols.get(mes_src)
        if col is not None:
            out[f"{variavel}_m{mes_dst:02d}"] = df[col].astype(float) / 1000.0

    gdf = gpd.GeoDataFrame(
        out,
        geometry=gpd.points_from_xy(out["lon"], out["lat"]),
        crs="EPSG:4326",
    )
    print(f"INPE/{variavel}: {len(gdf):,} pontos carregados "
          f"({gdf[f'{variavel}_anual'].min():.2f}–{gdf[f'{variavel}_anual'].max():.2f} kWh/m².dia)")
    return gdf
