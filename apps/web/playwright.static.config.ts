import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  use: { baseURL: "http://localhost:5173" },
  webServer: {
    command: "python -m http.server 5173 --directory static-build",
    port: 5173,
    reuseExistingServer: true,
  },
});
