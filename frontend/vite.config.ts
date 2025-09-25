import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

declare const process: { env: Record<string, string | undefined> };

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: "0.0.0.0",
    proxy: {
      "/api": {
  target: process.env.VITE_PROXY_TARGET ?? "http://localhost:8080",
        changeOrigin: true,
        secure: false
      }
    }
  },
  preview: {
    port: 4173,
    host: "0.0.0.0"
  }
});
