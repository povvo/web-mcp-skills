import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const packagedTypecheckRoot = fileURLToPath(new URL("../typecheck/", import.meta.url));
const typecheckRoot = resolve(process.env.WEBMCP_TYPECHECK_ROOT || packagedTypecheckRoot);
const generatedRoot = join(typecheckRoot, ".generated");
const toolkit = fileURLToPath(new URL("../../scripts/webmcp_toolkit.py", import.meta.url));
const manifest = fileURLToPath(new URL("../../assets/examples/toolset.example.json", import.meta.url));
const tsc = join(typecheckRoot, "node_modules", "typescript", "bin", "tsc");
const python = process.env.WEBMCP_TEST_PYTHON || "python";

const extensions = {
  typescript: "ts",
  react: "tsx",
  next: "tsx",
  vue: "ts",
  svelte: "ts",
  angular: "ts",
};

test("all generated TypeScript/framework adapters compile against official types", async (t) => {
  mkdirSync(generatedRoot, { recursive: true });
  try {
    for (const [target, extension] of Object.entries(extensions)) {
      await t.test(target, () => {
        rmSync(generatedRoot, { recursive: true, force: true });
        mkdirSync(generatedRoot, { recursive: true });
        const generated = spawnSync(
          python,
          ["-B", toolkit, "generate", manifest, "--target", target],
          { encoding: "utf8" },
        );
        assert.equal(generated.status, 0, generated.stderr || generated.stdout);
        assert.match(generated.stdout, /<reference types="webmcp-types"/);
        assert.doesNotMatch(generated.stdout, /interface Document\s*\{/);
        assert.doesNotMatch(generated.stdout, /from ["']webmcp-types["']/);

        const source = join(generatedRoot, `${target}.${extension}`);
        writeFileSync(source, generated.stdout, "utf8");
        const compiled = spawnSync(
          process.execPath,
          [
            tsc,
            "--project",
            join(typecheckRoot, "tsconfig.base.json"),
            "--pretty",
            "false",
            "--incremental",
            "false",
          ],
          { encoding: "utf8", cwd: typecheckRoot },
        );
        assert.equal(compiled.status, 0, compiled.stdout || compiled.stderr);
      });
    }
  } finally {
    rmSync(generatedRoot, { recursive: true, force: true });
  }
});
