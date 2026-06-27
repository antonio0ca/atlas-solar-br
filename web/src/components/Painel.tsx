import { useMemo } from "react";
import {
  type AtlasFC,
  type Modo,
  MODOS,
  rgbCss,
  CORES_CLASSE,
  calcularGap,
  agregarPorRegiao,
} from "../lib/atlas";
import { Busca } from "./Busca";
import { Sazonalidade } from "./Sazonalidade";
import { RankingRegiao } from "./RankingRegiao";

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
  onIrPara: (code: string) => void;
}

export function Painel({
  dados, modo, setModo, tresD, setTresD, tema, setTema, selecionado, onSelecionar, onIrPara,
}: Props) {
  const cfg = MODOS.find((m) => m.id === modo)!;
  const feats = useMemo(() => dados.features.map((f) => f.properties), [dados]);

  const stats = useMemo(() => {
    const potTotal = feats.reduce((s, p) => s + p.pot_instalada_mw, 0);
    const comGti = feats.filter((p) => p.gti_anual != null);
    const gtiMax = comGti.reduce((a, p) => (p.gti_anual! > a.gti_anual! ? p : a), comGti[0]);
    const nDesertos = feats.filter((p) => p.classe_oportunidade === "deserto de aproveitamento").length;
    return { potTotal, gtiMax, nDesertos };
  }, [feats]);

  const gap = useMemo(() => calcularGap(feats), [feats]);
  const regioes = useMemo(() => agregarPorRegiao(feats), [feats]);
  const sel = useMemo(() => feats.find((p) => p.code === selecionado) ?? null, [feats, selecionado]);

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
      <header className="masthead">
        <div className="masthead-text">
          <span className="eyebrow">Energia Solar &middot; Brasil</span>
          <h1>
            Atlas de Potencial <em>Solar</em>
          </h1>
          <p className="lede">
            Onde o Brasil tem mais sol, e quão pouco esse potencial está sendo aproveitado.
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

      <Busca dados={dados} onIr={onIrPara} />

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
      <p className="note-desc">{cfg.descricao}</p>

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
        <span>Visão 3D: altura representa o uso per capita</span>
      </label>

      {/* Detalhe do município selecionado + sazonalidade */}
      {sel && (
        <section className="detalhe">
          <div className="det-head">
            <h2>
              {sel.name} <span className="uf">{sel.uf}</span>
            </h2>
            <button className="ghost-btn small" onClick={() => onSelecionar(null)}>
              Limpar
            </button>
          </div>
          <div className="det-grid">
            <div><span className="det-l">GTI</span><span className="det-v">{sel.gti_anual?.toFixed(2) ?? "—"}</span></div>
            <div><span className="det-l">W/hab</span><span className="det-v">{sel.w_per_capita?.toFixed(0) ?? "—"}</span></div>
            <div><span className="det-l">Usinas/mil hab</span><span className="det-v">{sel.densidade_adocao?.toFixed(1) ?? "—"}</span></div>
            <div><span className="det-l">Região</span><span className="det-v det-reg">{sel.regiao || "—"}</span></div>
          </div>
          <Sazonalidade meses={sel.gti_meses} />
        </section>
      )}

      {/* Achado */}
      <blockquote className="achado">
        <span className="eyebrow accent">O insight</span>
        <p>
          O sol mais forte está no <em>Nordeste e Centro-Oeste</em>, mas a capacidade
          instalada se concentra no <em>Sul e Sudeste</em>. Esse descasamento cria os
          desertos de aproveitamento.
        </p>
      </blockquote>

      {/* Gap de aproveitamento */}
      <div className="gap">
        <span className="eyebrow accent">Gap de aproveitamento</span>
        <p>
          Se os <b>{gap.nDesertos.toLocaleString("pt-BR")}</b> desertos chegassem à mediana
          nacional de uso (<b>{gap.medianaWpc.toFixed(0)} W/hab</b>), seriam{" "}
          <b className="gap-num">+{gap.gw.toFixed(1)} GW</b> de solar instalada.
        </p>
      </div>

      {/* Ranking de desertos */}
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
                  onClick={() => onIrPara(p.code)}
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

      <RankingRegiao resumo={regioes} />

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
          Fontes: <b>LABREN/CCST/INPE</b> (irradiação), <b>ANEEL</b> (geração distribuída),{" "}
          <b>IBGE</b> (malhas/população).
        </p>
        <a href="https://github.com/antonio0ca/atlas-solar-br" target="_blank" rel="noreferrer">
          Código no GitHub →
        </a>
      </footer>
    </aside>
  );
}
