import { useMemo } from "react";
import { type AtlasFC, type Modo, MODOS, rgbCss, CORES_CLASSE } from "../lib/atlas";

interface Props {
  dados: AtlasFC;
  modo: Modo;
  setModo: (m: Modo) => void;
  tresD: boolean;
  setTresD: (v: boolean) => void;
  selecionado: string | null;
  onSelecionar: (code: string | null) => void;
}

export function Painel({ dados, modo, setModo, tresD, setTresD, selecionado, onSelecionar }: Props) {
  const cfg = MODOS.find((m) => m.id === modo)!;
  const feats = dados.features.map((f) => f.properties);

  // Estatísticas nacionais (demo ou reais — sempre derivadas dos dados carregados).
  const stats = useMemo(() => {
    const potTotal = feats.reduce((s, p) => s + p.pot_instalada_mw, 0);
    const gtiMax = feats.reduce((a, p) => (p.gti_anual > a.gti_anual ? p : a), feats[0]);
    return { potTotal, gtiMax };
  }, [feats]);

  // Top desertos de aproveitamento (alto recurso, baixo uso).
  const desertos = useMemo(
    () =>
      feats
        .filter((p) => p.classe_oportunidade === "deserto de aproveitamento")
        .sort((a, b) => b.score_oportunidade - a.score_oportunidade)
        .slice(0, 6),
    [feats]
  );

  return (
    <aside className="painel">
      <header className="painel-head">
        <div className="logo">☀️</div>
        <div>
          <h1>Atlas de Potencial Solar do Brasil</h1>
          <p className="sub">Recurso disponível × aproveitamento real</p>
        </div>
      </header>

      <p className="pergunta">
        Onde o Brasil tem <strong>mais sol</strong> — e quão pouco esse potencial está
        sendo <strong>aproveitado</strong>?
      </p>

      {/* Seletor de modo */}
      <div className="modos">
        {MODOS.map((m) => (
          <button
            key={m.id}
            className={m.id === modo ? "modo ativo" : "modo"}
            onClick={() => setModo(m.id)}
          >
            {m.titulo}
          </button>
        ))}
      </div>
      <p className="modo-desc">{cfg.descricao}</p>

      {/* Legenda */}
      <div className="legenda">
        {cfg.legenda.map((l, i) => (
          <div key={i} className="legenda-item">
            <span className="swatch" style={{ background: rgbCss(l.cor) }} />
            <span>{l.rotulo}</span>
          </div>
        ))}
        {cfg.unidade && <span className="unidade">unidade: {cfg.unidade}</span>}
      </div>

      <label className="toggle">
        <input type="checkbox" checked={tresD} onChange={(e) => setTresD(e.target.checked)} />
        <span>Visão 3D — altura = uso per capita</span>
      </label>

      {/* Achado / narrativa */}
      <div className="achado">
        <span className="achado-tag">o insight</span>
        <p>
          O sol mais forte está no <strong>Nordeste e Centro-Oeste</strong>, mas a maior
          parte da capacidade instalada está no <strong>Sul e Sudeste</strong>. O
          descasamento entre os dois cria os <strong>desertos de aproveitamento</strong>.
        </p>
      </div>

      {/* Ranking de desertos */}
      {desertos.length > 0 && (
        <div className="ranking">
          <h2>
            <span
              className="dot"
              style={{ background: rgbCss(CORES_CLASSE["deserto de aproveitamento"]) }}
            />
            Desertos de aproveitamento
          </h2>
          <ul>
            {desertos.map((p) => (
              <li
                key={p.code}
                className={selecionado === p.code ? "sel" : ""}
                onMouseEnter={() => onSelecionar(p.code)}
              >
                <span className="r-nome">{p.name}</span>
                <span className="r-val">{p.gti_anual.toFixed(2)} kWh · {p.w_per_capita.toFixed(0)} W/hab</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="stats">
        <div>
          <span className="stat-num">{(stats.potTotal / 1000).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}</span>
          <span className="stat-lbl">GW FV instalados</span>
        </div>
        <div>
          <span className="stat-num">{stats.gtiMax.uf}</span>
          <span className="stat-lbl">maior recurso ({stats.gtiMax.gti_anual.toFixed(2)})</span>
        </div>
      </div>

      <footer className="painel-foot">
        {dados.meta?.fonte?.startsWith("DEMO") && (
          <span className="badge-demo">⚠ dados de demonstração</span>
        )}
        <p>
          Fontes: <strong>LABREN/CCST/INPE</strong> (irradiação) · <strong>ANEEL</strong>{" "}
          (geração distribuída) · <strong>IBGE</strong> (malhas/população).
        </p>
        <a href="https://github.com/antonio0ca/atlas-solar-br" target="_blank" rel="noreferrer">
          ↗ código no GitHub
        </a>
      </footer>
    </aside>
  );
}
