import { existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const certDir = join(dirname(fileURLToPath(import.meta.url)), ".certs");

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  server: {
    port: 5173,
    ...(mode === "lan" ? {
      https: (() => {
        const key = join(certDir, "lan-server.key");
        const cert = join(certDir, "lan-server.crt");
        if (!existsSync(key) || !existsSync(cert)) {
          throw new Error("LAN certificate missing. Run npm run cert:lan first.");
        }
        return { key: readFileSync(key), cert: readFileSync(cert) };
      })(),
    } : {}),
    proxy: {
      "/api": { target: "http://127.0.0.1:8000", ws: true },
    },
  },
}));
