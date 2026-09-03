import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, extname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const scanRoots = ["README.md", "docs", "examples", "skills"];
const immutableSnapshotRoot = normalize(join(repositoryRoot, "docs", "official", "snapshots"));
const markdownLink = /!?\[[^\]]*\]\(([^)]+)\)/g;
const externalScheme = /^[a-z][a-z0-9+.-]*:/i;
const failures = [];
let inspectedFiles = 0;
let inspectedLinks = 0;

function collectMarkdown(path) {
  if (!existsSync(path)) return [];
  const stats = statSync(path);
  if (stats.isFile()) return extname(path).toLowerCase() === ".md" ? [path] : [];
  return readdirSync(path, { withFileTypes: true }).flatMap((entry) => {
    const child = join(path, entry.name);
    if (normalize(child).startsWith(immutableSnapshotRoot)) return [];
    return entry.isDirectory() ? collectMarkdown(child) : collectMarkdown(child);
  });
}

function cleanTarget(rawTarget) {
  const target = rawTarget.trim();
  if (target.startsWith("<")) {
    const closing = target.indexOf(">");
    return closing === -1 ? target : target.slice(1, closing);
  }
  return target.split(/\s+["']/u, 1)[0];
}

for (const root of scanRoots) {
  for (const file of collectMarkdown(join(repositoryRoot, root))) {
    inspectedFiles += 1;
    const content = readFileSync(file, "utf8");
    for (const match of content.matchAll(markdownLink)) {
      const target = cleanTarget(match[1]);
      if (!target || target.startsWith("#") || externalScheme.test(target)) continue;
      inspectedLinks += 1;
      const pathPart = target.split("#", 1)[0];
      let decoded;
      try {
        decoded = decodeURIComponent(pathPart);
      } catch {
        failures.push(`${file}: invalid URL encoding in ${target}`);
        continue;
      }
      const resolved = resolve(dirname(file), decoded);
      if (!existsSync(resolved)) failures.push(`${file}: missing ${target}`);
    }
  }
}

if (failures.length > 0) {
  console.error("Documentation link validation failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exitCode = 1;
} else {
  console.log(
    `Documentation links PASS (${inspectedFiles} authored Markdown files, ${inspectedLinks} local targets; official snapshots preserved verbatim).`,
  );
}
