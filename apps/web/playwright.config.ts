import { defineConfig } from "@playwright/test";

const liveBaseURL = process.env.VEYTAC_TEST_BASE_URL;

export default defineConfig({
  testDir: "./e2e",
  use: { baseURL: liveBaseURL ?? "http://localhost:5173", ignoreHTTPSErrors: !!liveBaseURL },
  webServer: liveBaseURL ? undefined : {
    command: "npm run dev",
    port: 5173,
    reuseExistingServer: true,
  },
});
