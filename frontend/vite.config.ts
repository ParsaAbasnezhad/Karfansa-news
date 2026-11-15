import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  return {
    plugins: [react()],
    resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
    server: {
      host: true,
      port: 5173,
      // File-watching inside Docker bind mounts needs polling on some hosts.
      watch: env.CHOKIDAR_USEPOLLING === "true" ? { usePolling: true } : undefined,
      proxy: {
        "/api": {
          target: env.VITE_PROXY_TARGET ?? "http://localhost:8000",
          changeOrigin: true,
        },
      },
    },
    test: {
      environment: "node",
      include: ["src/**/*.test.ts"],
    },
  };
});
