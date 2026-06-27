import { type ResumoRegiao } from "../lib/atlas";

// Agregados por macrorregião: evidencia o descasamento (NE muito sol, pouco uso).
interface Props {
  resumo: ResumoRegiao[];
}

export function RankingRegiao({ resumo }: Props) {
  if (!resumo.length) return null;
  return (
    <section className="reg">
      <span className="eyebrow">Recurso x uso por região</span>
      <table>
        <thead>
          <tr>
            <th>Região</th>
            <th className="num">GTI</th>
            <th className="num">W/hab</th>
            <th className="num">Desertos</th>
          </tr>
        </thead>
        <tbody>
          {resumo.map((r) => (
            <tr key={r.regiao}>
              <td>{r.regiao}</td>
              <td className="num">{r.gtiMedio.toFixed(2)}</td>
              <td className="num">{r.wpcMediano.toFixed(0)}</td>
              <td className="num">{r.nDesertos.toLocaleString("pt-BR")}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="reg-nota">
        GTI médio e W/hab mediano por município. O Nordeste lidera o recurso e concentra os desertos.
      </p>
    </section>
  );
}
