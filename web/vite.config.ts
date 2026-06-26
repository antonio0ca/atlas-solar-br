import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// SPA estática — deploy direto na Vercel (preset Vite).
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
});
