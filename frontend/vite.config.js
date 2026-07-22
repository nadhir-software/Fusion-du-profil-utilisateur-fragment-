import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Le proxy évite les problèmes CORS en dev : les appels vers /api et /health
// sont redirigés vers l'API FastAPI (uvicorn) sur le port 8000.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/health": "http://localhost:8000",
    },
  },
});
