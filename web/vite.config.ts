import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// SPA estática. O caminho base vem por env: '/' no dev e na Vercel; no GitHub
// Pages o workflow passa BASE_PATH=/atlas-solar-br/ (site servido em subdiretório).
export default defineConfig({
  base: process.env.BASE_PATH || "/",
  plugins: [react()],
  server: { port: 5173 },
});
