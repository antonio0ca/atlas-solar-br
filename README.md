# ☀️ Atlas de Potencial Solar do Brasil — potencial vs. aproveitamento

> Onde o Brasil tem mais sol — e quão pouco desse potencial está sendo aproveitado?

Projeto de **análise de dados geoespacial** que cruza duas camadas para revelar
**oportunidades desperdiçadas** de energia solar no Brasil:

1. **Recurso** — irradiação solar disponível (quanto sol cada lugar recebe).
2. **Uso real** — capacidade fotovoltaica efetivamente instalada por município.

O contraste entre as duas é a narrativa central: **regiões com muito sol e pouca
instalação são "desertos de aproveitamento"** — alto potencial, baixo uso.

> 🗺️ **Vitrine interativa (React + deck.gl):** mapa dark navegável com modos
> _Recurso_ / _Uso_ / _Oportunidade_, visão 3D e realce dos desertos.
> Código em [`web/`](web/). _(link da demo na Vercel — em breve)_

---

## 🧭 A pergunta de negócio

A intuição comum é que o Nordeste, com o maior recurso solar do país, lidera a
geração fotovoltaica. Mas a adoção de solar distribuída é puxada por **renda,
tarifa de energia e acesso a crédito** — não pelo recurso. O resultado é um
**descasamento entre onde o sol é mais forte e onde os painéis são instalados**.

Este projeto quantifica e mapeia esse descasamento.

---

## 🗺️ Fontes de dados (públicas)

| Camada | Fonte | O que fornece |
|---|---|---|
| **Irradiação** | [Atlas Brasileiro de Energia Solar — 2ª ed. (2017)](https://labren.ccst.inpe.br/atlas_2017.html) — LABREN/CCST/INPE | Grade de ~72.272 pontos (0,1° ≈ 10 km) com médias anuais/mensais de GHI, Difusa, DNI, **Plano Inclinado (GTI)** e PAR, em Wh/m².dia |
| **Uso real** | [Geração Distribuída — Dados Abertos ANEEL](https://dadosabertos.aneel.gov.br/dataset/relacao-de-empreendimentos-de-geracao-distribuida) | Empreendimentos fotovoltaicos por município + potência instalada (kW) |
| **Limites** | [Malhas Territoriais — IBGE](https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais.html) (via `geobr`) | Polígonos de municípios e estados + código IBGE |
| **População** | [API de Agregados — IBGE](https://servicodados.ibge.gov.br/api/docs/agregados) | População estimada por município (para o per capita) |

> 📌 **Por que GTI (plano inclinado)?** É a irradiação no plano do módulo fotovoltaico —
> o que o painel realmente capta. GHI (horizontal) subestima o recurso útil. Como
> tenho domínio de fotovoltaica (GHI/POA/plano inclinado, PR), a análise prioriza GTI.

### ⚠️ Licença dos dados — leia antes de usar

A base do **INPE/LABREN não pode ser redistribuída** (uso não comercial + citação
obrigatória da fonte). Por isso:

- **Os dados brutos NÃO são versionados** neste repositório (ver [`.gitignore`](.gitignore)).
- O código **baixa e processa** localmente; nada de dado original entra no git.
- Cite sempre: **LABREN/CCST/INPE — Brasil. Atlas Brasileiro de Energia Solar, 2ª ed., 2017.**

O código está sob licença MIT; os dados seguem as licenças de cada fonte ([`LICENSE`](LICENSE)).

---

## 🧱 Estrutura do repositório

```
atlas-solar-br/
├── data/                 # dados baixados (gitignored — não versionado)
│   ├── raw/              # zips e CSVs originais
│   ├── interim/          # descompactados / intermediários
│   └── processed/        # tabela final município × recurso × uso
├── notebooks/
│   └── 01_ingestao.ipynb # ingestão + casamento IBGE × ANEEL × INPE (passo a passo)
├── src/                  # motor de dados (Python)
│   ├── config.py         # caminhos, URLs e nomes de colunas das fontes
│   ├── download.py       # download + descompactação
│   ├── ingest_inpe.py    # grade de irradiação -> pontos
│   ├── ingest_aneel.py   # potência FV instalada por município
│   ├── ingest_ibge.py    # malhas e população
│   └── aggregate.py      # junção espacial + cruzamento + índice de oportunidade
├── scripts/
│   └── montar_dados_web.py  # gera o GeoJSON que a vitrine consome
├── web/                  # vitrine (React + Vite + TS + MapLibre + deck.gl)
│   ├── src/components/   # MapaAtlas (mapa) · Painel (controles/legenda)
│   ├── src/lib/atlas.ts  # tipos, métricas e escalas de cor
│   └── public/data/      # atlas_uf.geojson (servido ao mapa)
├── docs/PLANEJAMENTO.md  # planejamento completo (milestones, riscos, DoD)
├── outputs/              # mapas e figuras geradas (gitignored)
├── README.md · requirements.txt · .gitignore · LICENSE
```

---

## ⚙️ Como rodar

```bash
# 1. Ambiente
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Notebook de ingestão (baixa os dados e monta a tabela cruzada)
jupyter lab notebooks/01_ingestao.ipynb
```

> O primeiro download da ANEEL tem ~122 MB; o do INPE, alguns MB por variável.
> As funções fazem cache em `data/` e pulam o que já existe.

### Vitrine (frontend React)

```bash
cd web
npm install
npm run dev        # http://localhost:5173

# Regerar o GeoJSON que o mapa consome (a partir da raiz do projeto):
python scripts/montar_dados_web.py --demo
```

> Hoje a vitrine roda com **dados de demonstração** por UF (claramente sinalizado
> na interface). Ao concluir o pipeline (M1/M2), o mesmo frontend passa a consumir
> o GeoJSON **municipal real** — sem mudar o código do mapa. Deploy: Vercel (preset Vite, raiz `web/`).

---

## 🔬 Método — o desafio do casamento IBGE × ANEEL × INPE

O coração técnico do projeto é **casar três fontes que não compartilham a mesma
chave geográfica**:

- **INPE** dá pontos de uma **grade de 10 km** (lon/lat), sem código de município.
- **ANEEL** dá empreendimentos com **código IBGE do município** (`CodMunicipioIbge`).
- **IBGE** dá os **polígonos** com `code_muni`.

Estratégia adotada (documentada no notebook):

1. **INPE → IBGE por geometria.** Junção espacial *ponto-em-polígono*: cada ponto da
   grade recebe o município que o contém → **média de GTI por município**.
   Municípios pequenos sem ponto interno usam *fallback* pelo ponto mais próximo do centroide.
2. **ANEEL → IBGE por código.** `CodMunicipioIbge` ≡ `code_muni`. Junção tabular direta,
   **sem casar por nome** (acentuação/grafia divergem entre as bases — armadilha clássica).
3. **Agregação do uso.** Filtra `SigTipoGeracao == 'UFV'` (fotovoltaica) e soma
   `MdaPotenciaInstaladakW` por município.
4. **Per capita.** Potência ÷ população (IBGE) → W/hab, comparável entre municípios.

> Municípios sem instalação FV recebem potência **0** (ausência real de uso), não
> dado faltante — é justamente o que queremos enxergar.

---

## 📊 Achados (em construção)

> _Esta seção será preenchida com 3–4 achados + mapas após a EDA e o cruzamento._

1. **Mapa do recurso** — coroplético de GTI por estado/município (onde o sol é mais forte).
2. **Sazonalidade** — variação mensal de GTI por região (a estabilidade do Nordeste).
3. **Mapa do uso** — potência FV per capita (onde os painéis estão de fato).
4. **Desertos de aproveitamento** — o cruzamento: muito recurso × pouco uso.

---

## 🗂️ Roadmap

- [x] **Scaffold + ingestão** — baixar as 3 fontes e casá-las por código IBGE.
- [x] **Vitrine React** — mapa interativo (deck.gl + MapLibre) rodando com dados demo por UF.
- [ ] **EDA + mapas de recurso** — coroplético de irradiação, sazonalidade, ranking.
- [ ] **Cruzamento (o insight)** — GTI × potência per capita; índice de oportunidade.
- [ ] **Dados reais na vitrine** — trocar o GeoJSON demo pelo municipal do pipeline.
- [ ] **Storytelling** — pergunta → método → achados → conclusão, com mapas.
- [ ] **Deploy** — publicar a vitrine na Vercel e linkar no topo do README.

---

## 👤 Autor

**Antonio Carvalho** — estudante de ADS (FATEC) e desenvolvedor com atuação em
**monitoramento de usinas fotovoltaicas**. A interpretação dos dados parte de
domínio real de fotovoltaica (GHI/POA/plano inclinado, Performance Ratio).

## 📚 Créditos das fontes

- **LABREN/CCST/INPE — Brasil.** *Atlas Brasileiro de Energia Solar*, 2ª ed., 2017.
- **ANEEL** — Portal de Dados Abertos (Geração Distribuída).
- **IBGE** — Malhas Territoriais e Agregados (população).
