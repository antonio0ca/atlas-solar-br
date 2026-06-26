import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";

// Sem StrictMode: o duplo mount/unmount de dev causa corrida no setStyle do
// maplibre (react-map-gl re-aplica o estilo antes de carregar) -> erros no console.
createRoot(document.getElementById("root")!).render(<App />);
