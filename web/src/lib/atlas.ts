// Tipos, métricas e escalas de cor do Atlas.
// O frontend é agnóstico ao nível geográfico (uf/mun): lê as mesmas propriedades.

export type RGB = [number, number, number];

export interface AtlasProps {
  code: string;
  name: string;
  uf: string;
  level: "uf" | "mun";
  gti_anual: number; // recurso — kWh/m².dia (plano inclinado)
  pot_instalada_mw: number; // uso — potência FV instalada
  w_per_capita: number; // uso — W/hab
  score_oportunidade: number; // percentil(recurso) - percentil(uso), -1..1
  classe_oportunidade: string;
}

export type AtlasFeature = GeoJSON.Feature<GeoJSON.Geometry, AtlasProps>;
export type AtlasFC = GeoJSON.FeatureCollection<GeoJSON.Geometry, AtlasProps> & {
  meta?: { fonte?: string; nivel?: string };
};

export type Modo = "recurso" | "uso" | "oportunidade";

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

// Rampa "sol" (recurso): roxo profundo -> laranja -> amarelo quente.
const RAMPA_SOL: RGB[] = [
  [38, 24, 74],
  [122, 40, 80],
  [214, 96, 41],
  [245, 169, 41],
  [255, 226, 120],
];
// Rampa "uso" (ciano -> verde -> branco-azulado).
const RAMPA_USO: RGB[] = [
  [12, 34, 56],
  [16, 92, 120],
  [29, 161, 152],
  [120, 220, 180],
  [224, 255, 236],
];

// Cores categóricas do modo oportunidade (a narrativa).
export const CORES_CLASSE: Record<string, RGB> = {
  "deserto de aproveitamento": [244, 63, 94], // realce: muito sol, pouco uso
  "recurso e uso altos": [250, 204, 21],
  "uso acima do recurso": [56, 189, 248],
  intermediário: [71, 85, 105],
  "sem dado": [40, 44, 56],
};

// Domínios das rampas (calibrados aos dados reais; p5–p95 do GTI municipal).
const DOM_RECURSO: [number, number] = [4.4, 6.0];
// Uso: log10(W/hab) — distribuição muito assimétrica (mediana ~250, cauda até ~9700).
const DOM_USO_LOG: [number, number] = [1.3, 3.48]; // ~20 a ~3000 W/hab

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
    descricao: "Irradiação no plano inclinado (GTI) — quanto sol cada lugar recebe.",
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
    descricao: "Cruzamento recurso × uso. Destaque: muito sol e pouca instalação.",
    unidade: "",
    campo: "score_oportunidade",
    legenda: [
      { cor: CORES_CLASSE["deserto de aproveitamento"], rotulo: "Deserto de aproveitamento" },
      { cor: CORES_CLASSE["recurso e uso altos"], rotulo: "Recurso e uso altos" },
      { cor: CORES_CLASSE["uso acima do recurso"], rotulo: "Uso acima do recurso" },
      { cor: CORES_CLASSE["intermediário"], rotulo: "Intermediário" },
    ],
  },
];

export const rgbCss = (c: RGB, a = 1) => `rgba(${c[0]}, ${c[1]}, ${c[2]}, ${a})`;
