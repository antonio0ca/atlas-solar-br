#!/usr/bin/env bash
# Baixa a malha municipal do Brasil e a simplifica para uso web (deck.gl).
# Fonte: tbrugz/geodata-br (derivado do IBGE). Mantém só code (IBGE 7 díg.) e nome.
# Saída: data/interim/mun_simpl.geojson (gitignored; insumo do montar_dados_web.py).
set -euo pipefail
cd "$(dirname "$0")/.."

RAW=data/raw/mun_raw.json
OUT=data/interim/mun_simpl.geojson
URL="https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-100-mun.json"

[ -f "$RAW" ] || curl -sSL -o "$RAW" "$URL"

# -simplify: reduz vértices (Visvalingam). keep-shapes evita sumir municípios pequenos.
# precision: arredonda coords (~100 m), encolhe o arquivo. Renomeia id->code, name->nome.
npx --yes mapshaper "$RAW" \
  -simplify 6% keep-shapes \
  -each 'code=id, nome=name' \
  -filter-fields code,nome \
  -o format=geojson precision=0.001 "$OUT"

echo "OK -> $OUT ($(du -h "$OUT" | cut -f1))"
