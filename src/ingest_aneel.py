"""Ingestão da relação de empreendimentos de Geração Distribuída da ANEEL.

O CSV é grande (~milhões de linhas). Lemos em chunks, filtramos apenas
fotovoltaica (SigTipoGeracao == 'UFV') e agregamos potência por município
(CodMunicipioIbge), que é a chave de junção com o IBGE.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import config


def _achar_csv() -> Path:
    pasta = config.INTERIM / "aneel_gd"
    csvs = sorted(pasta.glob("*.csv"))
    if not csvs:
        raise FileNotFoundError(
            f"Nenhum CSV em {pasta}. Rode download.baixar_aneel() antes."
        )
    # Pega o maior arquivo (a relação principal), caso haja CSVs auxiliares.
    return max(csvs, key=lambda p: p.stat().st_size)


def agregar_por_municipio(*, chunksize: int = 200_000) -> pd.DataFrame:
    """Lê o CSV da ANEEL em chunks e devolve potência FV instalada por município.

    Retorna DataFrame com: code_muni (Int64, 7 díg.), uf, n_empreendimentos,
    pot_instalada_kw, pot_instalada_mw.
    """
    csv_path = _achar_csv()
    usecols = [
        config.ANEEL_COL_COD_MUN,
        config.ANEEL_COL_UF,
        config.ANEEL_COL_TIPO_GERACAO,
        config.ANEEL_COL_POTENCIA,
    ]

    acumulado: list[pd.DataFrame] = []
    total_linhas = 0
    leitor = pd.read_csv(
        csv_path,
        sep=";",
        decimal=",",          # ANEEL usa vírgula decimal
        usecols=usecols,
        dtype={config.ANEEL_COL_COD_MUN: "string", config.ANEEL_COL_UF: "string"},
        chunksize=chunksize,
        encoding="latin-1",   # portais gov.br costumam ser latin-1/cp1252
        on_bad_lines="skip",
    )
    for chunk in leitor:
        total_linhas += len(chunk)
        # Mantém só fotovoltaica (UFV).
        fv = chunk[chunk[config.ANEEL_COL_TIPO_GERACAO] == config.ANEEL_PV_FLAG].copy()
        if fv.empty:
            continue
        fv["pot_kw"] = pd.to_numeric(fv[config.ANEEL_COL_POTENCIA], errors="coerce")
        g = fv.groupby(
            [config.ANEEL_COL_COD_MUN, config.ANEEL_COL_UF], dropna=True
        ).agg(n_empreendimentos=("pot_kw", "size"),
              pot_instalada_kw=("pot_kw", "sum")).reset_index()
        acumulado.append(g)

    if not acumulado:
        raise RuntimeError("Nenhum empreendimento fotovoltaico encontrado — confira os filtros.")

    # Reagrupa os parciais dos chunks.
    df = (pd.concat(acumulado, ignore_index=True)
          .groupby([config.ANEEL_COL_COD_MUN, config.ANEEL_COL_UF], as_index=False)
          .agg(n_empreendimentos=("n_empreendimentos", "sum"),
               pot_instalada_kw=("pot_instalada_kw", "sum")))

    df = df.rename(columns={
        config.ANEEL_COL_COD_MUN: "code_muni",
        config.ANEEL_COL_UF: "uf",
    })
    # Código IBGE como inteiro de 7 dígitos (chave de junção).
    df["code_muni"] = pd.to_numeric(df["code_muni"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["code_muni"])
    df["pot_instalada_mw"] = df["pot_instalada_kw"] / 1000.0

    print(f"ANEEL: {total_linhas:,} linhas lidas -> "
          f"{len(df):,} municípios com FV, "
          f"{df['pot_instalada_mw'].sum():,.0f} MW instalados.")
    return df
