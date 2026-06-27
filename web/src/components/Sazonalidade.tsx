// Sparkline da irradiação mês a mês (GTI mensal) do município selecionado.
// Mostra a estabilidade do recurso ao longo do ano (NE estável vs Sul variável).
interface Props {
  meses: number[] | null | undefined;
}

const ROTULOS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"];
const W = 300;
const H = 66;
const PAD = 8;

export function Sazonalidade({ meses }: Props) {
  if (!meses || meses.length !== 12) {
    return <p className="saz-vazio">Selecione um município (busca ou clique no mapa) para ver a sazonalidade do recurso.</p>;
  }

  const min = Math.min(...meses);
  const max = Math.max(...meses);
  const span = max - min || 1;
  const amplitude = max - min;

  const pts = meses.map((v, i) => {
    const x = PAD + (i / 11) * (W - 2 * PAD);
    const y = H - PAD - ((v - min) / span) * (H - 2 * PAD - 12);
    return [x, y] as const;
  });
  const linha = pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(" ");
  const area = `${linha} L${pts[11][0].toFixed(1)} ${H - PAD} L${pts[0][0].toFixed(1)} ${H - PAD} Z`;

  return (
    <div className="sazonal">
      <div className="saz-head">
        <span className="eyebrow">Sazonalidade do recurso (GTI mensal)</span>
        <span className="saz-amp">
          amplitude <b>{amplitude.toFixed(2)}</b> kWh
        </span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="saz-svg" preserveAspectRatio="none" role="img"
        aria-label="Irradiação mensal">
        <path d={area} className="saz-area" />
        <path d={linha} className="saz-linha" />
        {pts.map((p, i) => (
          <circle key={i} cx={p[0]} cy={p[1]} r={1.8} className="saz-pt" />
        ))}
      </svg>
      <div className="saz-meses">
        {ROTULOS.map((r, i) => (
          <span key={i}>{r}</span>
        ))}
      </div>
    </div>
  );
}
