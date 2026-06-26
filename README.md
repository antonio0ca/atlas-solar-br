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
```

A vitrine consome `web/public/data/atlas_municipios.geojson` (5.563 municípios,
**dados reais**). Para regerá-lo a partir das fontes (rodar na raiz do projeto):

```bash
pip install shapely numpy requests          # sem geopandas — junção via shapely
bash   scripts/construir_geometria.sh        # malha municipal simplificada (~2 MB)
python scripts/processar_aneel.py            # potência FV por município (ANEEL ~122 MB)
python scripts/processar_inpe.py             # GTI por município (junção espacial INPE)
python scripts/processar_populacao.py        # população (API IBGE)
python scripts/montar_dados_web.py --real     # monta atlas_municipios.geojson
```

> O frontend é **agnóstico ao nível**: se `atlas_municipios.geojson` não existir,
> ele cai para `atlas_uf.geojson` (demo por UF, sinalizado na interface).
> Deploy: Vercel (preset Vite, raiz `web/`).

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

## 📊 Achados (primeira leitura — dados reais)

Números do pipeline atual (INPE GTI + ANEEL GD + IBGE, jun/2026):

1. **Recurso (GTI).** A irradiação no plano inclinado varia de **3,9 a 6,1 kWh/m²·dia**.
   O topo está no **semiárido (PB, PI, BA, MG-norte)** com ~6,0; o vale, no
   **Sul/litoral e Amazônia** (3,9–4,5), por nebulosidade.
2. **Uso real.** ~**49,7 GW** de FV distribuída instalada, **concentrada em S/SE/CO**
   (MG, SP, RS, PR, SC) — puxada por renda e tarifa, não por irradiação.
3. **Desertos de aproveitamento.** **671 municípios** combinam recurso no terço
   superior e uso no terço inferior. Os extremos (ex.: **São José de Caiana/PB**,
   **Morro Cabeça no Tempo/PI**, **Cônego Marinho/MG**) têm GTI ~6,0 e **30–50 W/hab**.
4. **O contraste capital × interior.** Mesmo capitais ensolaradas têm baixo per capita
   por causa da população (ex.: **São Paulo** com GTI 4,6 e só **19 W/hab**).

> ⚠️ Leitura preliminar a partir dos agregados. A EDA aprofundada (sazonalidade por
> região, controle por renda) está no roadmap (M1/M2).

---

## 🗂️ Roadmap

- [x] **Scaffold + ingestão** — baixar as 3 fontes e casá-las por código IBGE.
- [x] **Vitrine React** — mapa interativo (deck.gl + MapLibre).
- [x] **Dados reais na vitrine** — 5.563 municípios (INPE GTI + ANEEL + IBGE), via shapely.
- [ ] **EDA + mapas de recurso** — sazonalidade por região, ranking, controle por renda.
- [ ] **Cruzamento aprofundado** — correlação recurso/uso × renda (hipótese H4).
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
