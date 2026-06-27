// Tipos, métricas e escalas de cor do Atlas.
// O frontend é agnóstico ao nível geográfico (uf/mun): lê as mesmas propriedades.

export type RGB = [number, number, number];

export interface AtlasProps {
  code: string;
  name: string;
  uf: string;
  regiao?: string; // macrorregião do IBGE
  level: "uf" | "mun";
  gti_anual: number; // recurso: kWh/m².dia (plano inclinado)
  gti_meses?: number[] | null; // 12 médias mensais de GTI (sazonalidade)
  pot_instalada_mw: number; // uso: potência FV instalada
  n_empreendimentos?: number; // adoção: nº de usinas de GD
  densidade_adocao?: number | null; // adoção: empreendimentos por mil hab
  populacao?: number | null;
  w_per_capita: number; // uso: W/hab
  score_oportunidade: number; // percentil(recurso) - percentil(uso), -1..1
  classe_oportunidade: string;
}

export type AtlasFeature = GeoJSON.Feature<GeoJSON.Geometry, AtlasProps>;
export type AtlasFC = GeoJSON.FeatureCollection<GeoJSON.Geometry, AtlasProps> & {
  meta?: { fonte?: string; nivel?: string };
};

export type Modo = "recurso" | "uso" | "oportunidade" | "adocao";

// ── Interpolação linear em uma rampa de cores ───────────────────────────────
function lerp(a: number, b: number, t: number): number {
  return Math.round(a + (b - a) * t);
}
function rampa(stops: RGB[], t: number): RGB {
  const x = Math.max(0, Math.min(1, t)) * (stops.length - 1);
  const i = Math.floor(x);
  const f = x - i;
  if (i >= stops.length - 1) return stops[stops.length - 1];
  const a = stops[i];
  const b = stops[i + 1];
  return [lerp(a[0], b[0], f), lerp(a[1], b[1], f), lerp(a[2], b[2], f)];
}

// Paleta alinhada à identidade do Visualizador (teal/âmbar/índigo/verde).
// Rampa "sol" (recurso): creme -> âmbar -> terracota (YlOrRd quente).
const RAMPA_SOL: RGB[] = [
  [255, 230, 168],
  [251, 195, 77],
  [245, 158, 11],
  [224, 112, 26],
  [181, 71, 27],
];
// Rampa "uso" (teal sequencial, ancorada no acento #0D9488).
const RAMPA_USO: RGB[] = [
  [214, 240, 234],
  [134, 208, 190],
  [47, 182, 154],
  [13, 148, 136],
  [11, 110, 102],
];
// Rampa "adoção" (índigo sequencial) — densidade de empreendimentos.
const RAMPA_ADOCAO: RGB[] = [
  [231, 230, 250],
  [179, 178, 240],
  [129, 130, 232],
  [99, 102, 241],
  [67, 56, 170],
];

// Cores categóricas do modo oportunidade (a narrativa) — palette do Visualizador.
export const CORES_CLASSE: Record<string, RGB> = {
  "deserto de aproveitamento": [245, 158, 11], // âmbar (compare): muito sol, pouco uso
  "recurso e uso altos": [16, 185, 129], // verde (sorted)
  "uso acima do recurso": [99, 102, 241], // índigo (pivot)
  intermediário: [120, 113, 108], // stone
  "sem dado": [168, 162, 158],
};

// Domínios das rampas (calibrados aos dados reais; p5–p95 do GTI municipal).
const DOM_RECURSO: [number, number] = [4.4, 6.0];
// Uso: log10(W/hab), distribuição muito assimétrica (mediana ~250, cauda até ~9700).
const DOM_USO_LOG: [number, number] = [1.3, 3.48]; // ~20 a ~3000 W/hab
// Adoção: log10(empreendimentos por mil hab).
const DOM_ADOCAO_LOG: [number, number] = [0, 1.9]; // ~0 a ~80 por mil hab

function norm(v: number, [lo, hi]: [number, number]): number {
  return (v - lo) / (hi - lo);
}

export function corDaFeature(p: AtlasProps, modo: Modo): RGB {
  if (modo === "recurso") {
    if (p.gti_anual == null) return CORES_CLASSE["sem dado"];
    return rampa(RAMPA_SOL, norm(p.gti_anual, DOM_RECURSO));
  }
  if (modo === "uso") {
    if (p.w_per_capita == null) return CORES_CLASSE["sem dado"];
    return rampa(RAMPA_USO, norm(Math.log10(p.w_per_capita + 1), DOM_USO_LOG));
  }
  if (modo === "adocao") {
    if (p.densidade_adocao == null) return CORES_CLASSE["sem dado"];
    return rampa(RAMPA_ADOCAO, norm(Math.log10(p.densidade_adocao + 1), DOM_ADOCAO_LOG));
  }
  return CORES_CLASSE[p.classe_oportunidade] ?? CORES_CLASSE["sem dado"];
}

// Configuração de cada modo (rótulos, unidade, legenda).
export interface ConfigModo {
  id: Modo;
  titulo: string;
  descricao: string;
  unidade: string;
  campo: keyof AtlasProps;
  legenda: { cor: RGB; rotulo: string }[];
}

export const MODOS: ConfigModo[] = [
  {
    id: "recurso",
    titulo: "Recurso",
    descricao: "Irradiação no plano inclinado (GTI): quanto sol cada lugar recebe.",
    unidade: "kWh/m²·dia",
    campo: "gti_anual",
    legenda: [
      { cor: rampa(RAMPA_SOL, 1), rotulo: "Mais sol (≈6,0)" },
      { cor: rampa(RAMPA_SOL, 0.66), rotulo: "" },
      { cor: rampa(RAMPA_SOL, 0.33), rotulo: "" },
      { cor: rampa(RAMPA_SOL, 0), rotulo: "Menos sol (≈4,4)" },
    ],
  },
  {
    id: "uso",
    titulo: "Uso real",
    descricao: "Potência fotovoltaica instalada por habitante (geração distribuída).",
    unidade: "W/hab",
    campo: "w_per_capita",
    legenda: [
      { cor: rampa(RAMPA_USO, 1), rotulo: "Mais instalação" },
      { cor: rampa(RAMPA_USO, 0.5), rotulo: "" },
      { cor: rampa(RAMPA_USO, 0), rotulo: "Pouca instalação" },
    ],
  },
  {
    id: "oportunidade",
    titulo: "Oportunidade",
    descricao: "Cruzamento recurso vs uso. Destaque: muito sol e pouca instalação.",
    unidade: "",
    campo: "score_oportunidade",
    legenda: [
      { cor: CORES_CLASSE["deserto de aproveitamento"], rotulo: "Deserto de aproveitamento" },
      { cor: CORES_CLASSE["recurso e uso altos"], rotulo: "Recurso e uso altos" },
      { cor: CORES_CLASSE["uso acima do recurso"], rotulo: "Uso acima do recurso" },
      { cor: CORES_CLASSE["intermediário"], rotulo: "Intermediário" },
    ],
  },
  {
    id: "adocao",
    titulo: "Adoção",
    descricao: "Densidade de usinas: empreendimentos de GD por mil habitantes.",
    unidade: "usinas/mil hab",
    campo: "densidade_adocao",
    legenda: [
      { cor: rampa(RAMPA_ADOCAO, 1), rotulo: "Muita adoção" },
      { cor: rampa(RAMPA_ADOCAO, 0.5), rotulo: "" },
      { cor: rampa(RAMPA_ADOCAO, 0), rotulo: "Pouca adoção" },
    ],
  },
];

export const rgbCss = (c: RGB, a = 1) => `rgba(${c[0]}, ${c[1]}, ${c[2]}, ${a})`;

// Centro do bounding box de uma geometria (para "voar" o mapa até o município).
export function centroideBbox(geom: GeoJSON.Geometry): { lng: number; lat: number } | null {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  const visitar = (coords: any) => {
    if (typeof coords[0] === "number") {
      minX = Math.min(minX, coords[0]); maxX = Math.max(maxX, coords[0]);
      minY = Math.min(minY, coords[1]); maxY = Math.max(maxY, coords[1]);
    } else {
      for (const c of coords) visitar(c);
    }
  };
  if (!("coordinates" in geom)) return null;
  visitar((geom as any).coordinates);
  if (!isFinite(minX)) return null;
  return { lng: (minX + maxX) / 2, lat: (minY + maxY) / 2 };
}

// ── Insights agregados ──────────────────────────────────────────────────────
const mediana = (arr: number[]): number => {
  if (!arr.length) return 0;
  const s = [...arr].sort((a, b) => a - b);
  return s[Math.floor(s.length / 2)];
};

export interface Gap {
  gw: number; // capacidade FV (GW) que faltaria nos desertos para alcançar a mediana
  nDesertos: number;
  medianaWpc: number; // mediana nacional de W/hab
}

// Quanto de FV faltaria instalar para os desertos chegarem à mediana nacional de W/hab.
export function calcularGap(feats: AtlasProps[]): Gap {
  const wpcs = feats.filter((p) => p.w_per_capita != null).map((p) => p.w_per_capita);
  const medianaWpc = mediana(wpcs);
  let kw = 0;
  let n = 0;
  for (const p of feats) {
    if (p.classe_oportunidade !== "deserto de aproveitamento") continue;
    if (!p.populacao || p.w_per_capita == null) continue;
    const faltaW = (medianaWpc - p.w_per_capita) * p.populacao; // W
    if (faltaW > 0) {
      kw += faltaW / 1000;
      n++;
    }
  }
  return { gw: kw / 1e6, nDesertos: n, medianaWpc };
}

export interface ResumoRegiao {
  regiao: string;
  nMunicipios: number;
  gtiMedio: number;
  wpcMediano: number;
  potGW: number;
  nDesertos: number;
}

const ORDEM_REGIAO = ["Nordeste", "Centro-Oeste", "Sudeste", "Sul", "Norte"];

export function agregarPorRegiao(feats: AtlasProps[]): ResumoRegiao[] {
  const grupos: Record<string, AtlasProps[]> = {};
  for (const p of feats) {
    if (!p.regiao) continue;
    (grupos[p.regiao] ||= []).push(p);
  }
  return Object.entries(grupos)
    .map(([regiao, ps]) => ({
      regiao,
      nMunicipios: ps.length,
      gtiMedio: ps.reduce((s, p) => s + (p.gti_anual || 0), 0) / ps.length,
      wpcMediano: mediana(ps.filter((p) => p.w_per_capita != null).map((p) => p.w_per_capita)),
      potGW: ps.reduce((s, p) => s + p.pot_instalada_mw, 0) / 1000,
      nDesertos: ps.filter((p) => p.classe_oportunidade === "deserto de aproveitamento").length,
    }))
    .sort((a, b) => ORDEM_REGIAO.indexOf(a.regiao) - ORDEM_REGIAO.indexOf(b.regiao));
}
