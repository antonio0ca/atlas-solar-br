"""Processa o CSV real da ANEEL (Geração Distribuída) -> potência FV por município.

Streaming com a stdlib (csv), sem pandas: o arquivo tem milhões de linhas.
Filtra fotovoltaica (SigTipoGeracao == 'UFV') e soma MdaPotenciaInstaladaKW por
CodMunicipioIbge. Saída: data/interim/aneel_por_municipio.json.
"""
from __future__ import annotations

import csv
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / "data" / "raw" / "aneel_gd.zip"
OUT = ROOT / "data" / "interim" / "aneel_por_municipio.json"

# Aumenta o limite de campo do csv (alguns campos longos).
csv.field_size_limit(min(sys.maxsize, 2**31 - 1))


def _idx(header: list[str], nome: str) -> int:
    """Índice da coluna pelo nome (case-insensitive, ignora aspas/espacos)."""
    alvo = nome.strip().strip('"').lower()
    for i, c in enumerate(header):
        if c.strip().strip('"').lower() == alvo:
            return i
    raise KeyError(f"coluna '{nome}' não encontrada no header: {header}")


def processar() -> dict:
    nome_csv = next(n for n in zipfile.ZipFile(ZIP).namelist() if n.lower().endswith(".csv"))
    agg: dict[str, dict] = {}
    total = fv = 0

    with zipfile.ZipFile(ZIP).open(nome_csv) as bin_f:
        txt = (linha.decode("latin-1") for linha in bin_f)
        leitor = csv.reader(txt, delimiter=";", quotechar='"')
        header = next(leitor)
        i_cod = _idx(header, "CodMunicipioIbge")
        i_uf = _idx(header, "SigUF")
        i_mun = _idx(header, "NomMunicipio")
        i_tipo = _idx(header, "SigTipoGeracao")
        i_pot = _idx(header, "MdaPotenciaInstaladaKW")

        for row in leitor:
            total += 1
            if len(row) <= i_pot or row[i_tipo].strip() != "UFV":
                continue
            cod = row[i_cod].strip()
            if not cod or not cod.isdigit():
                continue
            try:
                pot = float(row[i_pot].strip().replace(".", "").replace(",", "."))
            except ValueError:
                continue
            fv += 1
            d = agg.setdefault(cod, {"uf": row[i_uf].strip(), "nome": row[i_mun].strip(),
                                     "pot_kw": 0.0, "n": 0})
            d["pot_kw"] += pot
            d["n"] += 1
            if total % 1_000_000 == 0:
                print(f"  ... {total:,} linhas, {fv:,} FV", flush=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(agg, ensure_ascii=False), encoding="utf-8")
    pot_total_mw = sum(d["pot_kw"] for d in agg.values()) / 1000
    print(f"OK: {total:,} linhas -> {len(agg):,} municípios com FV, "
          f"{pot_total_mw:,.0f} MW. Salvo em {OUT.relative_to(ROOT)}")
    return agg


if __name__ == "__main__":
    processar()
