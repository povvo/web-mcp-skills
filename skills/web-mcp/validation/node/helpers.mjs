import { spawnSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

export const skillRoot = fileURLToPath(new URL("../../", import.meta.url));
const toolkit = fileURLToPath(new URL("../../scripts/webmcp_toolkit.py", import.meta.url));
const manifest = fileURLToPath(new URL("../../assets/examples/toolset.example.json", import.meta.url));
const shimPath = fileURLToPath(new URL("../../assets/testing/model-context-shim.mjs", import.meta.url));

export async function generateModule(target = "vanilla-js") {
  const python = process.env.WEBMCP_TEST_PYTHON || "python";
  const result = spawnSync(
    python,
    ["-B", toolkit, "generate", manifest, "--target", target],
    { encoding: "utf8" },
  );
  if (result.status !== 0) {
    throw new Error(`generator failed (${result.status}): ${result.stderr || result.stdout}`);
  }
  const url = `data:text/javascript;base64,${Buffer.from(result.stdout).toString("base64")}`;
  return import(url);
}

export async function installShim(config = {}) {
  const { installModelContextShim } = await import(pathToFileURL(shimPath).href);
  const host = {};
  const installed = installModelContextShim(host, config);
  const previousDocument = globalThis.document;
  globalThis.document = host.document;
  return {
    ...installed,
    restore() {
      installed.uninstall();
      if (previousDocument === undefined) delete globalThis.document;
      else globalThis.document = previousDocument;
    },
  };
}

export function validHandlers(overrides = {}) {
  return {
    inspectDashboardSeries: async (input) => ({
      dashboardId: "dashboard-1",
      seriesId: input.seriesId ?? "series-1",
      pointCount: 2,
      sourceIds: ["fixture"],
    }),
    setDashboardDateRange: async (input) => ({
      dashboardId: "dashboard-1",
      startDate: input.startDate ?? "2026-01-01",
      endDate: input.endDate ?? "2026-01-31",
      chartRevision: 2,
    }),
    ...overrides,
  };
}

