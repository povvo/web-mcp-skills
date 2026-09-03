#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";

const args = process.argv.slice(2);
const jsonMode = args.includes("--json");
const inputs = args.filter((arg) => arg !== "--json");

if (inputs.length === 0) {
  console.error(
    "Usage: node validate-skill.mjs [--json] <skill-directory-or-catalog> [...]",
  );
  process.exit(2);
}

const ignoredDirectories = new Set([
  ".git",
  ".svn",
  "node_modules",
  ".venv",
  "venv",
  "__pycache__",
  ".pytest_cache",
  ".mypy_cache",
  ".ruff_cache",
  "dist",
  "build",
]);

const disposableNames = new Set([".DS_Store", "Thumbs.db", "desktop.ini"]);
const riskyNames = [
  /^\.env(?:\.|$)/i,
  /^id_(?:rsa|dsa|ecdsa|ed25519)(?:\.pub)?$/i,
  /credentials?/i,
  /secrets?/i,
  /\.p(?:12|fx)$/i,
  /\.key$/i,
];

const secretPatterns = [
  ["private key", /-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----/],
  ["GitHub token", /\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b/],
  ["GitHub fine-grained token", /\bgithub_pat_[A-Za-z0-9_]{40,}\b/],
  ["AWS access key", /\bAKIA[0-9A-Z]{16}\b/],
  ["Slack token", /\bxox[baprs]-[A-Za-z0-9-]{20,}\b/],
];

function unique(values) {
  return [...new Set(values)];
}

function isInside(root, candidate) {
  const relative = path.relative(root, candidate);
  return (
    relative === "" ||
    (!relative.startsWith(`..${path.sep}`) && relative !== "..")
  );
}

function walk(directory, state, root) {
  let entries;
  try {
    entries = fs.readdirSync(directory, { withFileTypes: true });
  } catch (error) {
    state.errors.push(`Cannot read ${directory}: ${error.message}`);
    return;
  }

  for (const entry of entries) {
    const fullPath = path.join(directory, entry.name);
    const relativePath = path
      .relative(root, fullPath)
      .split(path.sep)
      .join("/");

    if (entry.isSymbolicLink()) {
      let resolved;
      try {
        resolved = fs.realpathSync(fullPath);
      } catch (error) {
        state.errors.push(
          `Broken symbolic link: ${relativePath} (${error.message})`,
        );
        continue;
      }
      if (!isInside(root, resolved)) {
        state.errors.push(
          `Symbolic link escapes the skill directory: ${relativePath}`,
        );
      } else {
        state.warnings.push(
          `Symbolic link may not be portable across installers: ${relativePath}`,
        );
      }
      continue;
    }

    if (entry.isDirectory()) {
      if (ignoredDirectories.has(entry.name)) {
        state.warnings.push(
          `Excluded development directory is present and should not be published: ${relativePath}/`,
        );
        continue;
      }
      walk(fullPath, state, root);
      continue;
    }

    if (!entry.isFile()) continue;

    let stats;
    try {
      stats = fs.statSync(fullPath);
    } catch (error) {
      state.errors.push(`Cannot stat ${relativePath}: ${error.message}`);
      continue;
    }

    state.files.push({ fullPath, relativePath, size: stats.size });
    state.totalBytes += stats.size;

    if (disposableNames.has(entry.name)) {
      state.warnings.push(
        `Disposable operating-system file should be removed: ${relativePath}`,
      );
    }
    if (riskyNames.some((pattern) => pattern.test(entry.name))) {
      state.errors.push(
        `Potential credential or private-key file must be reviewed and removed: ${relativePath}`,
      );
    }
    if (stats.size > 2 * 1024 * 1024) {
      state.warnings.push(
        `File exceeds 2 MiB and may be omitted from skills.sh packs: ${relativePath} (${stats.size} bytes)`,
      );
    }
    if (stats.size > 10 * 1024 * 1024) {
      state.warnings.push(
        `File exceeds the default 10 MiB direct-download limit: ${relativePath} (${stats.size} bytes)`,
      );
    }
  }
}

function parseScalar(value, lines, fieldIndex) {
  const raw = value.trim();
  if (/^[>|][+-]?[0-9]*$/.test(raw)) {
    const chunks = [];
    for (let index = fieldIndex + 1; index < lines.length; index += 1) {
      const line = lines[index];
      if (line.trim() === "") {
        chunks.push("");
        continue;
      }
      const indentation = line.match(/^\s*/)[0].length;
      if (indentation === 0) break;
      chunks.push(line.slice(Math.min(indentation, 2)));
    }
    return raw.startsWith(">")
      ? chunks.join(" ").replace(/\s+/g, " ").trim()
      : chunks.join("\n").trim();
  }

  if (raw.startsWith('"') && raw.endsWith('"')) {
    try {
      return JSON.parse(raw);
    } catch {
      return raw.slice(1, -1);
    }
  }
  if (raw.startsWith("'") && raw.endsWith("'")) {
    return raw.slice(1, -1).replace(/''/g, "'");
  }
  return raw.replace(/\s+#.*$/, "").trim();
}

function readTopLevelField(lines, key, errors) {
  const matcher = new RegExp(`^${key}\\s*:(.*)$`);
  const matches = [];
  for (let index = 0; index < lines.length; index += 1) {
    const match = lines[index].match(matcher);
    if (match) matches.push({ value: match[1], index });
  }
  if (matches.length > 1)
    errors.push(`Frontmatter contains duplicate top-level '${key}' fields`);
  if (matches.length === 0) return undefined;
  return parseScalar(matches[0].value, lines, matches[0].index);
}

function validateLocalReference(target, root, sourceFile, state) {
  let cleaned = target.trim().replace(/^<|>$/g, "");
  if (cleaned.includes("{{") || cleaned.includes("}}")) return;
  if (!cleaned || cleaned.startsWith("#") || cleaned.startsWith("/")) return;
  if (/^[a-z][a-z0-9+.-]*:/i.test(cleaned)) return;
  cleaned = cleaned.split("#", 1)[0].split("?", 1)[0];
  try {
    cleaned = decodeURIComponent(cleaned);
  } catch {
    state.warnings.push(
      `Reference contains invalid URL escaping in ${sourceFile}: ${target}`,
    );
  }
  const resolved = path.resolve(root, cleaned);
  if (!isInside(root, resolved)) {
    state.errors.push(
      `Reference escapes the skill directory in ${sourceFile}: ${target}`,
    );
  } else if (!fs.existsSync(resolved)) {
    state.errors.push(`Missing local reference in ${sourceFile}: ${target}`);
  }
}

function scanMarkdownReferences(file, root, state) {
  let content;
  try {
    content = fs.readFileSync(file.fullPath, "utf8");
  } catch (error) {
    state.errors.push(
      `Cannot read Markdown file ${file.relativePath}: ${error.message}`,
    );
    return;
  }

  const markdownLinks = /!?\[[^\]]*\]\(([^)]+)\)/g;
  for (const match of content.matchAll(markdownLinks)) {
    const target = match[1].trim().replace(/\s+["'][^"']*["']$/, "");
    validateLocalReference(target, root, file.relativePath, state);
  }

  const codePaths =
    /`((?:\.\/)?(?:references|scripts|assets|agents)\/[^`\r\n]+)`/g;
  for (const match of content.matchAll(codePaths)) {
    const target = match[1].replace(/[.,;:]$/, "");
    if (!/[<>{}*]/.test(target))
      validateLocalReference(target, root, file.relativePath, state);
  }
}

function scanSecrets(file, state) {
  if (file.size === 0 || file.size > 25 * 1024 * 1024) return;
  let buffer;
  try {
    buffer = fs.readFileSync(file.fullPath);
  } catch (error) {
    state.errors.push(`Cannot inspect ${file.relativePath}: ${error.message}`);
    return;
  }
  const sample = buffer.subarray(0, Math.min(buffer.length, 8192));
  if (sample.includes(0)) return;
  const content = buffer.toString("utf8");
  for (const [label, pattern] of secretPatterns) {
    if (pattern.test(content))
      state.errors.push(`Possible ${label} found in ${file.relativePath}`);
  }
}

function validateSkill(skillDirectory) {
  const root = path.resolve(skillDirectory);
  const result = {
    path: root,
    name: null,
    errors: [],
    warnings: [],
    files: 0,
    totalBytes: 0,
  };

  const skillFile = path.join(root, "SKILL.md");
  if (!fs.existsSync(skillFile) || !fs.statSync(skillFile).isFile()) {
    result.errors.push("SKILL.md is missing");
    return result;
  }

  let content;
  try {
    content = fs.readFileSync(skillFile, "utf8").replace(/^\uFEFF/, "");
  } catch (error) {
    result.errors.push(`Cannot read SKILL.md as UTF-8: ${error.message}`);
    return result;
  }

  const lines = content.split(/\r?\n/);
  if (lines[0] !== "---") {
    result.errors.push(
      "SKILL.md must begin with a standalone --- YAML delimiter",
    );
    return result;
  }
  const closingIndex = lines.findIndex(
    (line, index) => index > 0 && line === "---",
  );
  if (closingIndex < 0) {
    result.errors.push(
      "SKILL.md frontmatter is missing its closing --- delimiter",
    );
    return result;
  }

  const frontmatterLines = lines.slice(1, closingIndex);
  const name = readTopLevelField(frontmatterLines, "name", result.errors);
  const description = readTopLevelField(
    frontmatterLines,
    "description",
    result.errors,
  );
  const compatibility = readTopLevelField(
    frontmatterLines,
    "compatibility",
    result.errors,
  );
  result.name = name ?? null;

  if (!name) {
    result.errors.push("Frontmatter requires a non-empty top-level name");
  } else {
    if (name.length > 64)
      result.errors.push("name must contain at most 64 characters");
    if (!/^(?!.*--)[a-z0-9]+(?:-[a-z0-9]+)*$/.test(name)) {
      result.errors.push(
        "name must use lowercase letters, numbers, and single hyphens without leading or trailing hyphens",
      );
    }
    if (path.basename(root) !== name) {
      result.errors.push(
        `name '${name}' must match parent directory '${path.basename(root)}'`,
      );
    }
  }

  if (!description) {
    result.errors.push(
      "Frontmatter requires a non-empty top-level description",
    );
  } else if (description.length > 1024) {
    result.errors.push("description must contain at most 1024 characters");
  } else if (!/\b(use|when|for)\b/i.test(description)) {
    result.warnings.push(
      "description should state when the skill applies, not only what it does",
    );
  }

  if (compatibility && compatibility.length > 500) {
    result.errors.push("compatibility must contain at most 500 characters");
  }

  if (
    !lines
      .slice(closingIndex + 1)
      .join("\n")
      .trim()
  ) {
    result.errors.push(
      "SKILL.md requires an instruction body after frontmatter",
    );
  }
  if (lines.length > 500)
    result.warnings.push(
      `SKILL.md has ${lines.length} lines; the specification recommends fewer than 500`,
    );
  if (content.length > 20000)
    result.warnings.push(
      `SKILL.md is ${content.length} characters; consider progressive disclosure through references`,
    );

  const state = {
    errors: result.errors,
    warnings: result.warnings,
    files: [],
    totalBytes: 0,
  };
  walk(root, state, root);
  result.files = state.files.length;
  result.totalBytes = state.totalBytes;

  for (const file of state.files.filter((candidate) =>
    candidate.relativePath.startsWith("references/"),
  )) {
    if (!content.includes(file.relativePath)) {
      result.warnings.push(
        `Reference file is not routed from SKILL.md: ${file.relativePath}`,
      );
    }
  }

  if (result.files > 1000)
    result.warnings.push(
      `Skill contains ${result.files} files; archive installs default to 1000 files`,
    );
  if (result.totalBytes > 25 * 1024 * 1024)
    result.warnings.push(
      `Skill expands to ${result.totalBytes} bytes; direct archive installs default to 25 MiB extracted content`,
    );

  for (const file of state.files) {
    scanSecrets(file, state);
    if (file.relativePath.toLowerCase().endsWith(".md"))
      scanMarkdownReferences(file, root, state);
  }

  result.errors = unique(result.errors);
  result.warnings = unique(result.warnings);
  return result;
}

function discoverSkills(input) {
  const resolved = path.resolve(input);
  if (!fs.existsSync(resolved))
    throw new Error(`Path does not exist: ${resolved}`);
  if (!fs.statSync(resolved).isDirectory())
    throw new Error(`Path is not a directory: ${resolved}`);
  if (fs.existsSync(path.join(resolved, "SKILL.md"))) return [resolved];

  const found = [];
  const visit = (directory) => {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      if (!entry.isDirectory() || ignoredDirectories.has(entry.name)) continue;
      const child = path.join(directory, entry.name);
      if (fs.existsSync(path.join(child, "SKILL.md"))) {
        found.push(child);
      } else {
        visit(child);
      }
    }
  };
  visit(resolved);
  return found;
}

const results = [];
const inputErrors = [];
for (const input of inputs) {
  try {
    const skills = discoverSkills(input);
    if (skills.length === 0)
      inputErrors.push(`No SKILL.md found under ${path.resolve(input)}`);
    for (const skill of skills) results.push(validateSkill(skill));
  } catch (error) {
    inputErrors.push(error.message);
  }
}

const failed =
  inputErrors.length > 0 || results.some((result) => result.errors.length > 0);

if (jsonMode) {
  console.log(JSON.stringify({ ok: !failed, inputErrors, results }, null, 2));
} else {
  for (const error of inputErrors) console.error(`ERROR ${error}`);
  for (const result of results) {
    const status = result.errors.length === 0 ? "PASS" : "FAIL";
    console.log(
      `${status} ${result.path}${result.name ? ` (${result.name})` : ""}`,
    );
    for (const error of result.errors) console.error(`  ERROR ${error}`);
    for (const warning of result.warnings) console.warn(`  WARN  ${warning}`);
    console.log(`  INFO  ${result.files} files, ${result.totalBytes} bytes`);
  }
  console.log(
    failed
      ? "Validation failed."
      : `Validation passed for ${results.length} skill(s).`,
  );
}

process.exit(failed ? 1 : 0);
