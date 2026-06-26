"""Configuração central do projeto: caminhos, URLs das fontes e constantes de domínio.

Tudo que é "endpoint" ou "nome de coluna de fonte externa" mora aqui, para que os
demais módulos não precisem conhecer detalhes das fontes. URLs verificadas em jun/2026.
"""
from __future__ import annotations

from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Caminhos do projeto
# ─────────────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "data"
RAW = DATA / "raw"            # downloads originais (zips, csv brutos)
INTERIM = DATA / "interim"    # intermediários (csv descompactado, parquet)
PROCESSED = DATA / "processed"  # tabela final município × recurso × uso
OUTPUTS = ROOT / "outputs"
FIGURAS = OUTPUTS / "figuras"
MAPAS = OUTPUTS / "mapas"

for _p in (RAW, INTERIM, PROCESSED, FIGURAS, MAPAS):
    _p.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# INPE / LABREN — Atlas Brasileiro de Energia Solar (2ª ed., 2017)
# CSVs por variável, em ZIP. Separador ';', decimal '.'.
# Grade completa: ~72.272 pontos a 0,1° x 0,1° (~10 km).
# Priorizamos TILTED (plano inclinado / GTI), que é o que o painel realmente capta.
# Fonte: https://labren.ccst.inpe.br/atlas_2017.html
# ─────────────────────────────────────────────────────────────────────────────
LABREN_BASE = "https://labren.ccst.inpe.br/projetos/atlas_2017"

# Grade completa do Brasil (use estes para a agregação por polígono).
LABREN_CSV = {
    "gti": f"{LABREN_BASE}/TILTED_LATITUDE_(csv).zip",     # plano inclinado (prioritário)
    "ghi": f"{LABREN_BASE}/GLOBAL_HORIZONTAL_(csv).zip",   # global horizontal
    "dni": f"{LABREN_BASE}/DIRECT_NORMAL_(csv).zip",       # direta normal
    "dif": f"{LABREN_BASE}/DIFFUSE_(csv).zip",             # difusa
    "par": f"{LABREN_BASE}/PAR_(csv).zip",                 # radiação fotossint. ativa
}

# Versão "sedes municipais" — 1 valor por sede de município (atalho, menos rigoroso
# que a média por polígono, mas útil para validação rápida).
LABREN_CSV_SEDES = {
    "gti": f"{LABREN_BASE}/TILTED_LATITUDE_sedes-munic_(csv).zip",
    "ghi": f"{LABREN_BASE}/GLOBAL_HORIZONTAL_sedes-munic_(csv).zip",
}

# Colunas da grade INPE. Confirme o cabeçalho real após o 1º download
# (ver inspecionar_cabecalho em ingest_inpe). Esperado: lon, lat, anual + 12 meses.
INPE_COL_LON = "LON"
INPE_COL_LAT = "LAT"
INPE_COL_ANUAL = "ANNUAL"
INPE_COLS_MESES = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                   "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
# Unidade da fonte: Wh/m².dia. Dividir por 1000 -> kWh/m².dia (mais legível).

# ─────────────────────────────────────────────────────────────────────────────
# ANEEL — Relação de Empreendimentos de Geração Distribuída (MMGD)
# Recurso atual: ZIP (~122 MB) com 1 CSV. Separador ';', decimal ','.
# Dicionário de dados v2.3 (17-11-2025).
# Fonte: https://dadosabertos.aneel.gov.br/dataset/relacao-de-empreendimentos-de-geracao-distribuida
# ─────────────────────────────────────────────────────────────────────────────
ANEEL_GD_ZIP = (
    "https://dadosabertos.aneel.gov.br/dataset/"
    "5e0fafd2-21b9-4d5b-b622-40438d40aba2/resource/"
    "b1bd71e7-d0ad-4214-9053-cbd58e9564a7/download/"
    "empreendimento-geracao-distribuida.zip"
)

# Colunas relevantes (nomes exatos do dicionário v2.3).
ANEEL_COL_COD_MUN = "CodMunicipioIbge"       # chave de junção com o IBGE
ANEEL_COL_UF = "SigUF"
ANEEL_COL_MUN = "NomMunicipio"
ANEEL_COL_TIPO_GERACAO = "SigTipoGeracao"    # 'UFV' = solar fotovoltaica
ANEEL_COL_FONTE = "DscFonteGeracao"          # 'Radiação solar'
ANEEL_COL_POTENCIA = "MdaPotenciaInstaladakW"  # atenção: 'k' minúsculo
ANEEL_COL_LAT = "NumCoordNEmpreendimento"
ANEEL_COL_LON = "NumCoordEEmpreendimento"

ANEEL_PV_FLAG = "UFV"  # Central Geradora Solar Fotovoltaica

# ─────────────────────────────────────────────────────────────────────────────
# IBGE — malhas territoriais (via geobr) e população (via API de agregados)
# ─────────────────────────────────────────────────────────────────────────────
IBGE_ANO_MALHA = 2022  # ano da malha municipal a usar no geobr

# API de agregados do IBGE — população estimada por município.
# Tabela 6579 = "População residente estimada". Confirme o período disponível.
IBGE_POP_API = (
    "https://servicodados.ibge.gov.br/api/v3/agregados/6579/"
    "periodos/{ano}/variaveis/9324?localidades=N6[all]"
)
IBGE_POP_ANO = 2021
