import { useMemo } from "react";
import { type AtlasFC, type Modo, MODOS, rgbCss, CORES_CLASSE } from "../lib/atlas";

interface Props {
  dados: AtlasFC;
  modo: Modo;
  setModo: (m: Modo) => void;
  tresD: boolean;
  setTresD: (v: boolean) => void;
  tema: "light" | "dark";
  setTema: (t: "light" | "dark") => void;
  selecionado: string | null;
  onSelecionar: (code: string | null) => void;
}

export function Painel({ dados, modo, setModo, tresD, setTresD, tema, setTema, selecionado, onSelecionar }: Props) {
  const cfg = MODOS.find((m) => m.id === modo)!;
  const feats = dados.features.map((f) => f.properties);

  const stats = useMemo(() => {
    const potTotal = feats.reduce((s, p) => s + p.pot_instalada_mw, 0);
    const comGti = feats.filter((p) => p.gti_anual != null);
    const gtiMax = comGti.reduce((a, p) => (p.gti_anual! > a.gti_anual! ? p : a), comGti[0]);
    const nDesertos = feats.filter((p) => p.classe_oportunidade === "deserto de aproveitamento").length;
    return { potTotal, gtiMax, nDesertos };
  }, [feats]);

  const desertos = useMemo(
    () =>
      feats
        .filter((p) => p.classe_oportunidade === "deserto de aproveitamento")
        .sort((a, b) => (b.score_oportunidade ?? 0) - (a.score_oportunidade ?? 0))
        .slice(0, 6),
    [feats]
  );

  return (
    <aside className="painel">
      {/* Masthead editorial */}
      <header className="masthead">
        <div className="masthead-text">
          <span className="eyebrow">Energia Solar &middot; Brasil</span>
          <h1>
            Atlas de Potencial <em>Solar</em>
          </h1>
          <p className="lede">
            Onde o Brasil tem mais sol — e quão pouco esse potencial está sendo aproveitado.
          </p>
        </div>
        <button
          className="ghost-btn"
          onClick={() => setTema(tema === "light" ? "dark" : "light")}
          title="Alternar tema claro/escuro"
          aria-label="Alternar tema claro/escuro"
        >
          Tema
        </button>
      </header>

      {/* Seletor de modo */}
      <div className="seg" role="tablist" aria-label="Camada do mapa">
        {MODOS.map((m) => (
          <button
            key={m.id}
            role="tab"
            aria-selected={m.id === modo}
            className={m.id === modo ? "seg-btn ativo" : "seg-btn"}
            onClick={() => setModo(m.id)}
          >
            {m.titulo}
          </button>
        ))}
      </div>

      {/* Descrição do modo — serifa em itálico (editorial) */}
      <p className="note-desc">{cfg.descricao}</p>

      {/* Legenda */}
      <div className="legenda">
        {cfg.legenda.map((l, i) => (
          <span key={i} className="legenda-item">
            <span className="swatch" style={{ background: rgbCss(l.cor) }} />
            {l.rotulo}
          </span>
        ))}
      </div>
      {cfg.unidade && <span className="unidade">unidade · {cfg.unidade}</span>}

      <label className="toggle">
        <input type="checkbox" checked={tresD} onChange={(e) => setTresD(e.target.checked)} />
        <span>Visão 3D — altura representa o uso per capita</span>
      </label>

      {/* Achado — pull-quote editorial */}
      <blockquote className="achado">
        <span className="eyebrow accent">O insight</span>
        <p>
          O sol mais forte está no <em>Nordeste e Centro-Oeste</em>, mas a capacidade
          instalada se concentra no <em>Sul e Sudeste</em>. Esse descasamento cria os
          desertos de aproveitamento.
        </p>
      </blockquote>

      {/* Ranking — tabela no estilo do histórico */}
      {desertos.length > 0 && (
        <section className="ranking">
          <span className="eyebrow">
            <span className="dot" style={{ background: rgbCss(CORES_CLASSE["deserto de aproveitamento"]) }} />
            Desertos de aproveitamento
          </span>
          <table>
            <thead>
              <tr>
                <th>Município</th>
                <th className="num">GTI</th>
                <th className="num">W/hab</th>
              </tr>
            </thead>
            <tbody>
              {desertos.map((p) => (
                <tr
                  key={p.code}
                  className={selecionado === p.code ? "sel" : ""}
                  onMouseEnter={() => onSelecionar(p.code)}
                >
                  <td>
                    {p.name} <span className="uf">{p.uf}</span>
                  </td>
                  <td className="num">{p.gti_anual?.toFixed(2)}</td>
                  <td className="num">{p.w_per_capita?.toFixed(0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {/* Estatísticas */}
      <div className="stats">
        <div className="stat">
          <span className="stat-label">FV instalada</span>
          <span className="stat-value">
            {(stats.potTotal / 1000).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}
            <small> GW</small>
          </span>
        </div>
        <div className="stat">
          <span className="stat-label">Desertos</span>
          <span className="stat-value">{stats.nDesertos.toLocaleString("pt-BR")}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Maior GTI</span>
          <span className="stat-value">
            {stats.gtiMax?.gti_anual?.toFixed(2)}
            <small> {stats.gtiMax?.uf}</small>
          </span>
        </div>
      </div>

      <footer className="painel-foot">
        {dados.meta?.fonte?.startsWith("DEMO") && (
          <span className="badge-demo">dados de demonstração</span>
        )}
        <p>
          Fontes: <b>LABREN/CCST/INPE</b> (irradiação) · <b>ANEEL</b> (geração distribuída) ·{" "}
          <b>IBGE</b> (malhas/população).
        </p>
        <a href="https://github.com/antonio0ca/atlas-solar-br" target="_blank" rel="noreferrer">
          Código no GitHub →
        </a>
      </footer>
    </aside>
  );
}
