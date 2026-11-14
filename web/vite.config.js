import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// base "./" — одна и та же сборка работает и на сервере (/), и в Electron (app://)
export default defineConfig({
  base: "./",
  plugins: [react()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
    chunkSizeWarningLimit: 6000,
  },
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8080",
      "/deck-assets": "http://127.0.0.1:8080",
    },
  },
});
