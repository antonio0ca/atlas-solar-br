import { useEffect, useState } from "react";
import { MapaAtlas } from "./components/MapaAtlas";
import { Painel } from "./components/Painel";
import { type AtlasFC, type Modo } from "./lib/atlas";

type Tema = "light" | "dark";

export default function App() {
  const [dados, setDados] = useState<AtlasFC | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [modo, setModo] = useState<Modo>("recurso");
  const [tresD, setTresD] = useState(false);
  const [selecionado, setSelecionado] = useState<string | null>(null);
  const [tema, setTema] = useState<Tema>("light");

  useEffect(() => {
    document.documentElement.dataset.theme = tema;
  }, [tema]);

  useEffect(() => {
    // Carrega o nível municipal se existir; senão cai para o estadual (demo).
    const tentar = async (url: string) => {
      const r = await fetch(url);
      if (!r.ok) throw new Error(url);
      return (await r.json()) as AtlasFC;
    };
    tentar(`${import.meta.env.BASE_URL}data/atlas_municipios.geojson`)
      .catch(() => tentar(`${import.meta.env.BASE_URL}data/atlas_uf.geojson`))
      .then(setDados)
      .catch(() => setErro("Não foi possível carregar os dados do atlas."));
  }, []);

  if (erro) return <div className="estado">{erro}</div>;
  if (!dados) return <div className="estado">Carregando o atlas…</div>;

  return (
    <div className="app">
      <MapaAtlas
        dados={dados}
        modo={modo}
        tresD={tresD}
        tema={tema}
        selecionado={selecionado}
        onSelecionar={setSelecionado}
      />
      <Painel
        dados={dados}
        modo={modo}
        setModo={setModo}
        tresD={tresD}
        setTresD={setTresD}
        tema={tema}
        setTema={setTema}
        selecionado={selecionado}
        onSelecionar={setSelecionado}
      />
    </div>
  );
}
