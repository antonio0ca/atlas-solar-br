# 📋 Planejamento — Atlas de Potencial Solar do Brasil

Documento de planejamento de ponta a ponta. Define **objetivo, hipóteses, fases,
entregáveis, cronograma, riscos e critérios de pronto**. É o mapa do projeto;
o [README](../README.md) é a vitrine.

---

## 1. Objetivo

Construir uma análise geoespacial de portfólio que responda, com dados públicos:

> **Onde o Brasil tem mais sol e quão pouco esse potencial está sendo aproveitado?**

O produto final é um **mapa-narrativa** que cruza **recurso** (irradiação GTI) com
**uso real** (potência fotovoltaica instalada), revelando os **"desertos de
aproveitamento"** — municípios com muito sol e pouca instalação.

### Público-alvo do entregável
Recrutadores técnicos e pares de dados/energia. O projeto precisa demonstrar:
domínio geoespacial (junção espacial, agregação por polígono), rigor de ingestão
(casar três bases com chaves diferentes) e **leitura de domínio** de fotovoltaica.

---

## 2. Pergunta de negócio e hipóteses

| # | Hipótese | Como testar | Resultado esperado |
|---|---|---|---|
| H1 | O recurso solar (GTI) é mais alto e mais **estável** no semiárido/Nordeste e Centro-Oeste. | Coroplético de GTI anual + desvio sazonal mensal por região. | Confirma; Nordeste com menor variação mensal. |
| H2 | A potência FV instalada **não acompanha** o recurso — concentra-se em SE/S (renda, tarifa). | Mapa de potência per capita (W/hab) por município. | Concentração em MG, SP, RS, SC, PR. |
| H3 | Existe **descasamento** mensurável: alto recurso + baixo uso. | Índice de oportunidade (percentil recurso − percentil uso). | Cluster de "desertos" no interior do NE/N. |
| H4 | O descasamento se associa a **renda/porte**, não ao recurso. | (Stretch) cruzar com PIB per capita ou porte do município. | Correlação fraca recurso↔uso; forte renda↔uso. |

> **Leitura de domínio:** a adoção de solar distribuída é puxada por **payback**
> (tarifa local, renda, crédito), não por irradiação. O recurso é condição
> necessária, não suficiente. O projeto quantifica esse gap.

---

## 3. Fases e entregáveis (milestones)

### ✅ M0 — Scaffold + Ingestão  *(concluído)*
Estrutura do repo, módulos `src/`, notebook `01_ingestao.ipynb`, casamento
IBGE×ANEEL×INPE, tabela `processed/atlas_municipios.parquet`.
- **Entregável:** pipeline reprodutível de ingestão.

### 🔜 M1 — EDA + mapas de recurso
Explorar a grade INPE e mapear o recurso.
- Coroplético de **GTI anual** por município e por UF.
- **Sazonalidade**: GTI mensal médio por macrorregião (5 linhas) + amplitude (máx−mín).
- **Ranking** dos top/bottom municípios por GTI.
- Validação: faixa de GTI plausível (≈ 4,5–6,5 kWh/m².dia), sem buracos na malha.
- **Entregável:** notebook `02_eda_recurso.ipynb` + 2–3 figuras em `outputs/`.

### 🔜 M2 — Cruzamento (o insight)
Mapear o uso e cruzar com o recurso.
- Coroplético de **potência FV per capita** (W/hab).
- **Mapa dos desertos de aproveitamento** (classe `deserto de aproveitamento`).
- Scatter **GTI × W/hab** com municípios destacados.
- Tabela dos **top-20 desertos** (alto recurso, baixo uso) com leitura.
- **Entregável:** notebook `03_cruzamento.ipynb` + mapa interativo Folium em `outputs/mapas/`.

### 🔜 M3 — Storytelling
Transformar análise em narrativa.
- Escrever no README os **3–4 achados** com figuras embutidas.
- Pergunta → método → achados → conclusão → limitações.
- Revisar créditos/licença das fontes.
- **Entregável:** README final com imagens.

### 🟡 M4 — App Streamlit  *(opcional / stretch)*
- App navegável: seletor de UF, camadas recurso/uso, tabela de desertos.
- Deploy no **Streamlit Community Cloud** (dados gerados on-the-fly ou parquet leve).
- **Entregável:** `app.py` + link público.

---

## 4. Cronograma estimado

Projeto pessoal, ritmo de portfólio (noites/fins de semana). Estimativa em esforço, não datas fixas.

| Fase | Esforço | Dependências |
|---|---|---|
| M0 Ingestão | ✅ feito | — |
| M1 EDA recurso | ~1 sessão | M0 |
| M2 Cruzamento | ~1–2 sessões | M1 |
| M3 Storytelling | ~1 sessão | M2 |
| M4 Streamlit | ~1–2 sessões | M3 |

---

## 5. Riscos técnicos e mitigação

| Risco | Impacto | Mitigação |
|---|---|---|
| Nomes de coluna do INPE diferentes do esperado | Quebra a ingestão | `inspecionar_cabecalho()` na 1ª célula; nomes centralizados em `config.py`. |
| Grade de 10 km não cobre municípios pequenos | GTI faltante | Fallback por centroide (`sjoin_nearest`) → cobertura 100%. |
| API de população do IBGE muda período/endpoint | `per capita` faltante | Período parametrizado em `config.IBGE_POP_ANO`; degradar para mapa absoluto se falhar. |
| CSV ANEEL grande (~122 MB) estoura memória | Falha de leitura | Leitura em chunks + `usecols` + filtro UFV cedo. |
| Encoding/decimal das fontes gov.br | Valores corrompidos | `latin-1` + decimal `,` na ANEEL; `;`/`.` no INPE — já tratados. |
| Código IBGE com dígitos divergentes (6 vs 7) | Junção falha | Normalização para `Int64` de 7 dígitos nos dois lados. |

---

## 6. Critérios de pronto (Definition of Done)

- [ ] Pipeline roda do zero (`pip install` → notebook 01) sem edição manual.
- [ ] Nenhum dado bruto versionado (verificar `git ls-files`).
- [ ] Cobertura de GTI ≈ 100% dos municípios.
- [ ] README conta a história com 3–4 mapas/figuras e cita as fontes.
- [ ] Índice de oportunidade gera lista de desertos coerente com o domínio.
- [ ] (M4) App publicado com link no README.

---

## 7. Stack

Python · GeoPandas · geobr · Pandas · Folium/Plotly · Matplotlib · Streamlit (opcional).
Comentários, docs e strings de usuário em **português**; nomes de código em inglês.

## 8. Fontes (resumo — detalhes no README)

- **INPE/LABREN** — Atlas Brasileiro de Energia Solar 2ª ed. (GTI, grade 0,1°). *Não redistribuível.*
- **ANEEL** — Geração Distribuída (potência FV por município). Dados abertos.
- **IBGE** — malhas (`geobr`) + população (API de agregados). Dados abertos.
