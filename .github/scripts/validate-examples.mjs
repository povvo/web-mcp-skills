#!/usr/bin/env node

import {spawnSync} from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {fileURLToPath} from "node:url";

const repository = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const toolkit = path.join(repository, "skills", "web-mcp", "scripts", "webmcp_toolkit.py");
const examples = ["shared-board", "release-rail", "evidence-desk"];
const python = process.env.WEB_MCP_PYTHON ?? (process.platform === "win32" ? "python" : "python3");
const errors = [];
const receipts = [];

function run(args) {
  const result = spawnSync(python, ["-B", toolkit, ...args], {cwd: repository, encoding: "utf8", maxBuffer: 16 * 1024 * 1024, env: {...process.env, PYTHONDONTWRITEBYTECODE: "1"}});
  if (result.error) throw result.error;
  if (result.status !== 0) throw new Error(`${python} ${args.join(" ")} exited ${result.status}\n${result.stderr || result.stdout}`);
  return JSON.parse(result.stdout);
}

for (const name of examples) {
  const application = path.join(repository, "examples", name);
  const product = path.join(application, "product.json");
  const checkedAdapter = path.join(application, "webmcp-tools.js");
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), `web-mcp-${name}-`));
  try {
    const plan = run(["product-plan", product, "--target", "vanilla-js"]);
    if (plan.status !== "PASS") errors.push(`${name}: product plan returned ${plan.status}`);
    if (plan.validation?.summary?.bundleErrors || plan.validation?.summary?.bundleWarnings) errors.push(`${name}: product bundle contains findings`);
    if (plan.handlerReadiness?.status !== "PASS") errors.push(`${name}: handler readiness returned ${plan.handlerReadiness?.status ?? "UNKNOWN"}`);

    const compile = run(["compile-product", product, "--target", "vanilla-js", "--output-dir", temporary, "--write", "--force"]);
    if (compile.status !== "PASS") errors.push(`${name}: compile returned ${compile.status}`);
    const regenerated = path.join(temporary, "webmcp-tools.js");
    if (!fs.existsSync(regenerated)) errors.push(`${name}: clean compilation did not emit webmcp-tools.js`);
    else if (!fs.existsSync(checkedAdapter) || !fs.readFileSync(regenerated).equals(fs.readFileSync(checkedAdapter))) errors.push(`${name}: checked-in adapter differs from clean generation`);

    const html = fs.readFileSync(path.join(application, "index.html"), "utf8");
    const ui = fs.readFileSync(path.join(application, "src", "ui.mjs"), "utf8");
    if (!html.includes("../_shared/web-mcp-design.css")) errors.push(`${name}: shared design stylesheet is not linked`);
    if (!ui.includes('from "../webmcp-tools.js"')) errors.push(`${name}: UI does not import the generated adapter`);
    receipts.push({name, tools: compile.capabilities.map((item) => item.webmcpTool), adapterSha256: compile.artifacts.find((item) => item.path.endsWith("webmcp-tools.js"))?.sha256});
  } catch (error) {
    errors.push(`${name}: ${error.message}`);
  } finally {
    fs.rmSync(temporary, {recursive: true, force: true});
  }
}

const css = fs.readFileSync(path.join(repository, "examples", "_shared", "web-mcp-design.css"), "utf8");
for (const forbidden of ["linear-gradient", "radial-gradient", "box-shadow:"]) {
  if (css.includes(forbidden)) errors.push(`design stylesheet contains forbidden treatment: ${forbidden}`);
}
for (const font of ["JetBrainsMono-Regular.woff2", "JetBrainsMono-SemiBold.woff2", "JetBrainsMono-ExtraBold.woff2", "OFL.txt"]) {
  if (!fs.existsSync(path.join(repository, "examples", "_shared", "fonts", font))) errors.push(`missing self-hosted font asset: ${font}`);
}

if (errors.length) {
  console.error(JSON.stringify({status: "FAIL", errors, receipts}, null, 2));
  process.exit(1);
}

console.log(JSON.stringify({status: "PASS", examples: receipts}, null, 2));
