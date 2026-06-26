import { useEffect, useMemo, useState } from "react";
import Map, { useControl, NavigationControl } from "react-map-gl/maplibre";
import { MapboxOverlay, type MapboxOverlayProps } from "@deck.gl/mapbox";
import { GeoJsonLayer } from "@deck.gl/layers";
import "maplibre-gl/dist/maplibre-gl.css";

import { type AtlasFC, type AtlasFeature, type AtlasProps, type Modo, corDaFeature } from "../lib/atlas";

// Basemaps CARTO gratuitos (sem token), acompanhando o tema da identidade.
const BASEMAP = {
  light: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
  dark: "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
};

// Busca o JSON do estilo uma vez por tema e cacheia. Passar o OBJETO completo
// (em vez da URL) evita que o react-map-gl faça diff contra um estilo ainda
// vazio durante o carregamento — origem dos erros de validação do maplibre.
const _cacheEstilo: Record<string, any> = {};
async function carregarEstilo(tema: "light" | "dark"): Promise<any> {
  if (!_cacheEstilo[tema]) {
    _cacheEstilo[tema] = await fetch(BASEMAP[tema]).then((r) => r.json());
  }
  return _cacheEstilo[tema];
}

const VISAO_INICIAL = {
  longitude: -54,
  latitude: -14,
  zoom: 3.4,
  pitch: 0,
  bearing: 0,
};

// Ponte deck.gl <-> maplibre: adiciona o overlay como um "control" do mapa.
function DeckOverlay(props: MapboxOverlayProps) {
  const overlay = useControl<MapboxOverlay>(() => new MapboxOverlay(props));
  overlay.setProps(props);
  return null;
}

interface Props {
  dados: AtlasFC;
  modo: Modo;
  tresD: boolean;
  tema: "light" | "dark";
  selecionado: string | null;
  onSelecionar: (code: string | null) => void;
}

export function MapaAtlas({ dados, modo, tresD, tema, selecionado, onSelecionar }: Props) {
  const [hover, setHover] = useState<{ x: number; y: number; p: AtlasProps } | null>(null);
  const [estilo, setEstilo] = useState<any>(null);
  const corLinha: [number, number, number] = tema === "light" ? [120, 113, 108] : [40, 42, 50];

  useEffect(() => {
    let vivo = true;
    carregarEstilo(tema).then((s) => vivo && setEstilo(s));
    return () => {
      vivo = false;
    };
  }, [tema]);

  const layer = useMemo(
    () =>
      new GeoJsonLayer<AtlasProps>({
        id: `atlas-${modo}-${tresD ? "3d" : "2d"}`,
        data: dados as unknown as AtlasFeature[],
        pickable: true,
        stroked: true,
        filled: true,
        extruded: tresD,
        wireframe: false,
        getFillColor: (f: AtlasFeature) => {
          const c = corDaFeature(f.properties, modo);
          const sel = selecionado === f.properties.code;
          return [c[0], c[1], c[2], sel ? 255 : 205];
        },
        getLineColor: (f: AtlasFeature) =>
          selecionado === f.properties.code ? [13, 148, 136, 255] : [...corLinha, 150],
        getLineWidth: (f: AtlasFeature) => (selecionado === f.properties.code ? 2.2 : 0.5),
        lineWidthUnits: "pixels",
        // Em 3D, a altura representa o uso (potência per capita) — colunas mais altas = mais instalação.
        getElevation: (f: AtlasFeature) => f.properties.w_per_capita * 120,
        elevationScale: tresD ? 1 : 0,
        onHover: (info) => {
          if (info.object) {
            setHover({ x: info.x, y: info.y, p: (info.object as AtlasFeature).properties });
          } else {
            setHover(null);
          }
        },
        onClick: (info) =>
          onSelecionar(info.object ? (info.object as AtlasFeature).properties.code : null),
        updateTriggers: {
          getFillColor: [modo, selecionado],
          getLineColor: [selecionado, tema],
          getLineWidth: [selecionado],
        },
        transitions: { getFillColor: 250, getElevation: 400 },
      }),
    [dados, modo, tresD, tema, corLinha, selecionado, onSelecionar]
  );

  return (
    <div className="mapa-wrap">
      {estilo && (
      <Map
        key={tema}
        initialViewState={{ ...VISAO_INICIAL, pitch: tresD ? 45 : 0 }}
        mapStyle={estilo}
        attributionControl={false}
      >
        <DeckOverlay layers={[layer]} interleaved />
        <NavigationControl position="bottom-right" showCompass={false} />
      </Map>
      )}

      {hover && (
        <div className="tooltip" style={{ left: hover.x + 14, top: hover.y + 14 }}>
          <strong>{hover.p.name}</strong>
          <span className="tt-uf">{hover.p.uf}</span>
          <dl>
            <div>
              <dt>Recurso (GTI)</dt>
              <dd>{hover.p.gti_anual != null ? `${hover.p.gti_anual.toFixed(2)} kWh/m²·dia` : "—"}</dd>
            </div>
            <div>
              <dt>Uso (per capita)</dt>
              <dd>{hover.p.w_per_capita != null ? `${hover.p.w_per_capita.toFixed(0)} W/hab` : "—"}</dd>
            </div>
            <div>
              <dt>Potência instalada</dt>
              <dd>{hover.p.pot_instalada_mw.toLocaleString("pt-BR")} MW</dd>
            </div>
          </dl>
          <span className="tt-classe">{hover.p.classe_oportunidade}</span>
        </div>
      )}
    </div>
  );
}
