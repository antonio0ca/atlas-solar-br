import { useMemo, useState } from "react";
import { type AtlasFC } from "../lib/atlas";

interface Props {
  dados: AtlasFC;
  onIr: (code: string) => void;
}

// Remove acentos para busca tolerante ("sao paulo" acha "São Paulo").
const norm = (s: string) =>
  s.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();

export function Busca({ dados, onIr }: Props) {
  const [q, setQ] = useState("");
  const [aberto, setAberto] = useState(false);

  const matches = useMemo(() => {
    const s = norm(q.trim());
    if (s.length < 2) return [];
    return dados.features
      .map((f) => f.properties)
      .filter((p) => norm(`${p.name} ${p.uf}`).includes(s))
      .slice(0, 8);
  }, [q, dados]);

  const escolher = (code: string, nome: string) => {
    onIr(code);
    setQ(nome);
    setAberto(false);
  };

  return (
    <div className="busca">
      <input
        type="search"
        placeholder="Buscar município ou UF…"
        value={q}
        onChange={(e) => {
          setQ(e.target.value);
          setAberto(true);
        }}
        onFocus={() => setAberto(true)}
        onBlur={() => setTimeout(() => setAberto(false), 150)}
        aria-label="Buscar município ou estado"
      />
      {aberto && matches.length > 0 && (
        <ul className="busca-lista">
          {matches.map((p) => (
            <li key={p.code} onMouseDown={() => escolher(p.code, p.name)}>
              <span className="b-nome">{p.name}</span>
              <span className="b-uf">{p.uf}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
