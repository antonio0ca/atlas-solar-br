"""Agregação espacial e cruzamento recurso × uso — o núcleo analítico do projeto.

Etapas:
 1. Junção espacial: cada ponto da grade INPE recebe o município (polígono IBGE)
    que o contém -> média de GTI por município.
 2. Junção tabular por code_muni: GTI (recurso) + potência FV ANEEL (uso) + população.
 3. Indicadores derivados, incluindo o "índice de aproveitamento" que sustenta a
    narrativa dos 'desertos de aproveitamento' (muito sol, pouca instalação).
"""
from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd


def media_gti_por_municipio(
    pontos_inpe: gpd.GeoDataFrame,
    municipios: gpd.GeoDataFrame,
    *,
    coluna_valor: str = "gti_anual",
) -> pd.DataFrame:
    """Junção espacial ponto-em-polígono -> média da variável por município.

    Pontos sem polígono (ex.: litoral/grade fora da malha) são descartados.
    Municípios pequenos podem não conter nenhum ponto da grade de 10 km — esses
    ficam sem GTI por esta via (tratados depois com fallback de centroide).
    """
    pontos = pontos_inpe.to_crs(municipios.crs)
    juncao = gpd.sjoin(
        pontos, municipios[["code_muni", "name_muni", "geometry"]],
        how="inner", predicate="within",
    )
    agg = (juncao.groupby(["code_muni", "name_muni"], as_index=False)
           .agg(gti_anual=(coluna_valor, "mean"),
                n_pontos_grade=(coluna_valor, "size")))
    print(f"GTI agregada: {len(agg):,} municípios com >=1 ponto da grade.")
    return agg


def gti_por_centroide(
    pontos_inpe: gpd.GeoDataFrame,
    municipios: gpd.GeoDataFrame,
    municipios_faltantes: pd.Series,
    *,
    coluna_valor: str = "gti_anual",
) -> pd.DataFrame:
    """Fallback: para municípios sem ponto interno, usa o ponto da grade mais
    próximo do centroide (junção espacial 'nearest'). Garante cobertura de 100%.
    """
    faltantes = municipios[municipios["code_muni"].isin(municipios_faltantes)].copy()
    if faltantes.empty:
        return pd.DataFrame(columns=["code_muni", "name_muni", "gti_anual", "n_pontos_grade"])
    faltantes["geometry"] = faltantes.geometry.representative_point()
    nn = gpd.sjoin_nearest(
        faltantes[["code_muni", "name_muni", "geometry"]].to_crs(pontos_inpe.crs),
        pontos_inpe[[coluna_valor, "geometry"]],
        how="left",
    )
    out = (nn.groupby(["code_muni", "name_muni"], as_index=False)
           .agg(gti_anual=(coluna_valor, "mean")))
    out["n_pontos_grade"] = 0  # marca que veio de fallback
    print(f"GTI por centroide (fallback): {len(out):,} municípios.")
    return out


def cruzar(
    gti_mun: pd.DataFrame,
    aneel_mun: pd.DataFrame,
    populacao: pd.DataFrame,
    municipios: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Une recurso (GTI) × uso (potência FV) × população na malha municipal.

    Municípios sem nenhuma instalação FV recebem potência = 0 (não é dado faltante:
    é ausência real de aproveitamento — exatamente o que queremos enxergar).
    """
    base = municipios[["code_muni", "name_muni", "abbrev_state", "geometry"]].copy()

    df = (base
          .merge(gti_mun[["code_muni", "gti_anual", "n_pontos_grade"]], on="code_muni", how="left")
          .merge(aneel_mun[["code_muni", "n_empreendimentos", "pot_instalada_kw", "pot_instalada_mw"]],
                 on="code_muni", how="left")
          .merge(populacao, on="code_muni", how="left"))

    # Ausência de instalação = 0 (e não NaN).
    for c in ["n_empreendimentos", "pot_instalada_kw", "pot_instalada_mw"]:
        df[c] = df[c].fillna(0)

    # Indicadores de uso.
    df["pot_kw_per_capita"] = np.where(
        df["populacao"].gt(0), df["pot_instalada_kw"] / df["populacao"], np.nan
    )
    df["w_per_capita"] = df["pot_kw_per_capita"] * 1000.0  # W/hab, escala mais legível

    return gpd.GeoDataFrame(df, geometry="geometry", crs=municipios.crs)


def indice_aproveitamento(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Cria o índice que define 'deserto de aproveitamento'.

    Ideia: percentis nacionais de recurso (GTI) e de uso (W/hab). Um município com
    recurso alto (percentil GTI elevado) e uso baixo (percentil W/hab baixo) é uma
    OPORTUNIDADE DESPERDIÇADA. Definimos um score = pct_recurso - pct_uso:
      score alto  -> muito sol, pouca instalação (deserto de aproveitamento)
      score baixo -> aproveitamento proporcional (ou acima) ao recurso
    Percentis tornam recurso e uso comparáveis apesar de unidades e escalas distintas.
    """
    g = gdf.copy()
    g["pct_recurso"] = g["gti_anual"].rank(pct=True)
    g["pct_uso"] = g["w_per_capita"].rank(pct=True)
    g["score_oportunidade"] = g["pct_recurso"] - g["pct_uso"]

    # Classificação categórica para o mapa-narrativa.
    def _classe(row):
        if pd.isna(row["gti_anual"]):
            return "sem dado"
        alto_rec = row["pct_recurso"] >= 0.66
        baixo_uso = row["pct_uso"] <= 0.33
        alto_uso = row["pct_uso"] >= 0.66
        if alto_rec and baixo_uso:
            return "deserto de aproveitamento"
        if alto_rec and alto_uso:
            return "recurso e uso altos"
        if not alto_rec and alto_uso:
            return "uso acima do recurso"
        return "intermediário"

    g["classe_oportunidade"] = g.apply(_classe, axis=1)
    return g
