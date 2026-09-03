#!/usr/bin/env python3
# Builder-first repository analysis and framework adapter generation for WebMCP.

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable

BUILDER_VERSION = "3.0.0"

SUPPORTED_TARGETS = (
    "auto",
    "vanilla-js",
    "typescript",
    "react",
    "next",
    "vue",
    "svelte",
    "angular",
)

SOURCE_EXTENSIONS = {
    ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts",
    ".html", ".htm", ".vue", ".svelte", ".astro",
}
TEXT_EXTENSIONS = SOURCE_EXTENSIONS | {
    ".json", ".md", ".yaml", ".yml", ".toml", ".css", ".scss",
}
SKIP_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode", ".next", ".nuxt",
    ".svelte-kit", ".angular", ".cache", ".turbo", ".vercel",
    "node_modules", "bower_components", "vendor", "dist", "build",
    "coverage", "out", "target", "__pycache__",
}
LOCKFILES = {
    "package-lock.json": "npm",
    "npm-shrinkwrap.json": "npm",
    "pnpm-lock.yaml": "pnpm",
    "yarn.lock": "yarn",
    "bun.lock": "bun",
    "bun.lockb": "bun",
}
FRAMEWORK_PACKAGES = {
    "next": "next",
    "react": "react",
    "vue": "vue",
    "svelte": "svelte",
    "angular": "@angular/core",
}
FRAMEWORK_CONFIGS = {
    "next": ("next.config.js", "next.config.mjs", "next.config.ts"),
    "vue": ("vite.config.js", "vite.config.ts", "nuxt.config.ts", "nuxt.config.js"),
    "svelte": ("svelte.config.js", "svelte.config.ts"),
    "angular": ("angular.json",),
}
ARCHITECTURE_NAMES = {
    "package.json", "tsconfig.json", "jsconfig.json", "vite.config.js",
    "vite.config.ts", "next.config.js", "next.config.mjs", "next.config.ts",
    "svelte.config.js", "svelte.config.ts", "angular.json", "nuxt.config.ts",
    "nuxt.config.js", "astro.config.mjs", "astro.config.ts",
}
CURRENT_PATTERNS = {
    "document.modelContext": re.compile(r"\bdocument\s*\.\s*modelContext\b"),
    "registerTool": re.compile(r"\bregisterTool\s*\("),
    "getTools": re.compile(r"\bgetTools\s*\("),
    "executeTool": re.compile(r"\bexecuteTool\s*\("),
    "toolchange": re.compile(r"\b(?:on)?toolchange\b"),
    "exposedTo": re.compile(r"\bexposedTo\b"),
    "fromOrigins": re.compile(r"\bfromOrigins\b"),
}
LEGACY_PATTERNS = {
    "navigator.modelContext": re.compile(r"\bnavigator\s*\.\s*modelContext\b"),
    "provideContext": re.compile(r"\bprovideContext\s*\("),
    "registerTools": re.compile(r"\bregisterTools\s*\("),
    "unregisterTool": re.compile(r"\bunregisterTool\s*\("),
}
DECLARATIVE_PATTERNS = {
    "toolname": re.compile(r"\btoolname\s*=", re.I),
    "tooldescription": re.compile(r"\btooldescription\s*=", re.I),
    "toolparamdescription": re.compile(r"\btoolparamdescription\s*=", re.I),
    "toolautosubmit": re.compile(r"\btoolautosubmit\b", re.I),
    "agentInvoked": re.compile(r"\bagentInvoked\b"),
    "respondWith": re.compile(r"\brespondWith\s*\("),
    "toolactivated": re.compile(r"\btoolactivated\b"),
    "toolcancel": re.compile(r"\btoolcancel\b"),
    "tool-form-active": re.compile(r":tool-form-active\b"),
    "tool-submit-active": re.compile(r":tool-submit-active\b"),
}
EXPORTED_FUNCTION_PATTERNS = (
    re.compile(r"\bexport\s+(?:default\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\("),
    re.compile(r"\bexport\s+(?:default\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*="),
    re.compile(r"\bmodule\.exports\.([A-Za-z_$][\w$]*)\s*="),
    re.compile(r"\bexports\.([A-Za-z_$][\w$]*)\s*="),
)
LOCAL_FUNCTION_PATTERNS = (
    re.compile(r"(?m)^\s*(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\("),
    re.compile(r"(?m)^\s*(?:const|let)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>"),
)
FORM_RE = re.compile(r"<form\b", re.I)
ROUTE_RE = re.compile(r"(?:^|/)(?:app|pages|routes?|views?)/|(?:page|route|layout)\.(?:[cm]?[jt]sx?|vue|svelte)$", re.I)
COMPONENT_RE = re.compile(r"(?:^|/)(?:components?|features?)/|(?:component|view)\.(?:[cm]?[jt]sx?|vue|svelte)$", re.I)
EXECUTE_STRING_RE = re.compile(r"\bexecuteTool\s*\([^,\n]+,\s*(?:JSON\.stringify\s*\(|[`'\"])")
EXECUTE_OBJECT_RE = re.compile(r"\bexecuteTool\s*\([^,\n]+,\s*(?:\{|[A-Za-z_$][\w$]*\s*(?:,|\)))")


class BuilderError(Exception):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _safe_relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _iter_files(root: Path, max_file_bytes: int) -> tuple[list[Path], list[dict[str, Any]]]:
    files: list[Path] = []
    skipped: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda p: p.as_posix()):
        try:
            rel_parts = path.relative_to(root).parts
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in rel_parts[:-1]):
            continue
        if path.is_symlink():
            skipped.append({"path": _safe_relative(path, root), "reason": "symlink"})
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS and path.name not in ARCHITECTURE_NAMES:
            continue
        size = path.stat().st_size
        if size > max_file_bytes:
            skipped.append({
                "path": _safe_relative(path, root),
                "reason": "oversize",
                "bytes": size,
                "limit": max_file_bytes,
            })
            continue
        files.append(path)
    return files, skipped


def _read_text(path: Path) -> str | None:
    try:
        raw = path.read_bytes()
        if b"\x00" in raw:
            return None
        return raw.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _package_metadata(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    package_path = root / "package.json"
    findings: list[dict[str, Any]] = []
    if not package_path.exists():
        return {}, findings
    try:
        value = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        findings.append({
            "severity": "warning",
            "code": "PACKAGE_JSON_UNREADABLE",
            "path": "package.json",
            "message": str(exc),
        })
        return {}, findings
    if not isinstance(value, dict):
        findings.append({
            "severity": "warning",
            "code": "PACKAGE_JSON_NOT_OBJECT",
            "path": "package.json",
            "message": "package.json is not a JSON object.",
        })
        return {}, findings
    return value, findings


def _frameworks(root: Path, package: dict[str, Any]) -> list[str]:
    deps: dict[str, Any] = {}
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        value = package.get(key, {})
        if isinstance(value, dict):
            deps.update(value)
    found: set[str] = set()
    for framework, package_name in FRAMEWORK_PACKAGES.items():
        if package_name in deps:
            found.add(framework)
    for framework, names in FRAMEWORK_CONFIGS.items():
        if any((root / name).exists() for name in names):
            found.add(framework)
    if "next" in found:
        found.add("react")
    if not found:
        found.add("vanilla")
    order = {"next": 0, "react": 1, "vue": 2, "svelte": 3, "angular": 4, "vanilla": 9}
    return sorted(found, key=lambda item: (order.get(item, 8), item))


def _language_counts(files: Iterable[Path]) -> dict[str, int]:
    mapping = {
        ".ts": "TypeScript", ".tsx": "TypeScript/JSX", ".mts": "TypeScript",
        ".cts": "TypeScript", ".js": "JavaScript", ".jsx": "JavaScript/JSX",
        ".mjs": "JavaScript", ".cjs": "JavaScript", ".html": "HTML",
        ".htm": "HTML", ".vue": "Vue SFC", ".svelte": "Svelte",
        ".astro": "Astro",
    }
    counts: dict[str, int] = {}
    for path in files:
        language = mapping.get(path.suffix.lower())
        if language:
            counts[language] = counts.get(language, 0) + 1
    return dict(sorted(counts.items()))


def _occurrences(
    patterns: dict[str, re.Pattern[str]],
    text: str,
    rel: str,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    lines = text.splitlines()
    for symbol, pattern in patterns.items():
        for match in pattern.finditer(text):
            line = _line_number(text, match.start())
            excerpt = lines[line - 1].strip()[:240] if lines else ""
            out.append({
                "symbol": symbol,
                "path": rel,
                "line": line,
                "excerpt": excerpt,
            })
    return out


def _handler_candidates(text: str, rel: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, int, str]] = set()
    for visibility, patterns in (
        ("exported", EXPORTED_FUNCTION_PATTERNS),
        ("local", LOCAL_FUNCTION_PATTERNS),
    ):
        for pattern in patterns:
            for match in pattern.finditer(text):
                name = match.group(1)
                line = _line_number(text, match.start())
                key = (name, line, visibility)
                if key in seen:
                    continue
                seen.add(key)
                out.append({
                    "name": name,
                    "visibility": visibility,
                    "path": rel,
                    "line": line,
                })
    return sorted(out, key=lambda item: (item["name"], item["path"], item["line"], item["visibility"]))


def scan_repository(path: str | Path, max_file_bytes: int = 1_000_000) -> dict[str, Any]:
    root = Path(path).expanduser().resolve()
    if not root.exists():
        raise BuilderError(f"repository path does not exist: {root}")
    if not root.is_dir():
        raise BuilderError(f"repository path is not a directory: {root}")

    package, package_findings = _package_metadata(root)
    files, skipped = _iter_files(root, max_file_bytes)
    current: list[dict[str, Any]] = []
    legacy: list[dict[str, Any]] = []
    declarative: list[dict[str, Any]] = []
    handlers: list[dict[str, Any]] = []
    forms: list[dict[str, Any]] = []
    routes: list[dict[str, Any]] = []
    components: list[dict[str, Any]] = []
    architecture: list[str] = []
    digester = hashlib.sha256()
    scanned_files = 0
    scanned_bytes = 0
    unreadable: list[dict[str, Any]] = []

    for file_path in files:
        rel = _safe_relative(file_path, root)
        text = _read_text(file_path)
        if text is None:
            unreadable.append({"path": rel, "reason": "not UTF-8 text"})
            continue
        scanned_files += 1
        encoded = text.encode("utf-8")
        scanned_bytes += len(encoded)
        digester.update(rel.encode("utf-8"))
        digester.update(b"\0")
        digester.update(hashlib.sha256(encoded).digest())
        if file_path.name in ARCHITECTURE_NAMES:
            architecture.append(rel)
        if file_path.suffix.lower() in SOURCE_EXTENSIONS:
            current.extend(_occurrences(CURRENT_PATTERNS, text, rel))
            legacy.extend(_occurrences(LEGACY_PATTERNS, text, rel))
            declarative.extend(_occurrences(DECLARATIVE_PATTERNS, text, rel))
            handlers.extend(_handler_candidates(text, rel))
            for match in FORM_RE.finditer(text):
                snippet = text[match.start():match.start()+800]
                forms.append({
                    "path": rel,
                    "line": _line_number(text, match.start()),
                    "hasToolName": bool(re.search(r"<form\b[^>]*\btoolname\s*=", snippet, re.I | re.S)),
                })
            if ROUTE_RE.search(rel):
                routes.append({"path": rel})
            if COMPONENT_RE.search(rel):
                components.append({"path": rel})

    managers = sorted({
        manager for filename, manager in LOCKFILES.items() if (root / filename).exists()
    })
    frameworks = _frameworks(root, package)
    unique_handlers: dict[tuple[str, str, int], dict[str, Any]] = {}
    for item in handlers:
        key = (item["name"], item["path"], item["line"])
        existing = unique_handlers.get(key)
        if existing is None or (existing["visibility"] == "local" and item["visibility"] == "exported"):
            unique_handlers[key] = item

    findings = package_findings
    findings.extend({
        "severity": "info",
        "code": "SKIPPED_FILE",
        "path": item["path"],
        "message": item["reason"],
    } for item in skipped)
    findings.extend({
        "severity": "warning",
        "code": "UNREADABLE_TEXT",
        "path": item["path"],
        "message": item["reason"],
    } for item in unreadable)

    return {
        "status": "PASS" if scanned_files else "WARN",
        "operation": "scan-repo",
        "root": str(root),
        "repositorySha256": digester.hexdigest(),
        "frameworks": frameworks,
        "packageManagers": managers,
        "languages": _language_counts(files),
        "architectureFiles": sorted(set(architecture)),
        "sourceSummary": {
            "scannedFiles": scanned_files,
            "scannedBytes": scanned_bytes,
            "skippedFiles": len(skipped),
            "unreadableFiles": len(unreadable),
        },
        "webmcp": {
            "current": sorted(current, key=lambda item: (item["path"], item["line"], item["symbol"])),
            "legacy": sorted(legacy, key=lambda item: (item["path"], item["line"], item["symbol"])),
            "declarative": sorted(declarative, key=lambda item: (item["path"], item["line"], item["symbol"])),
        },
        "handlerCandidates": sorted(
            unique_handlers.values(),
            key=lambda item: (item["name"], item["path"], item["line"]),
        ),
        "forms": sorted(forms, key=lambda item: (item["path"], item["line"])),
        "routes": sorted(routes, key=lambda item: item["path"]),
        "components": sorted(components, key=lambda item: item["path"]),
        "findings": findings,
        "limitations": [
            "Static scanning does not prove runtime reachability, authorization, UI parity, or browser support.",
            "Candidate handlers are lexical matches; inspect call paths before patching.",
            "Generated plans never infer business logic or import paths.",
        ],
    }


def _compat_finding(
    severity: str,
    code: str,
    message: str,
    evidence: list[dict[str, Any]] | None = None,
    remediation: str | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "severity": severity,
        "code": code,
        "message": message,
    }
    if evidence:
        out["evidence"] = evidence
    if remediation:
        out["remediation"] = remediation
    return out


def compatibility_report(path: str | Path) -> dict[str, Any]:
    scan = scan_repository(path)
    current = scan["webmcp"]["current"]
    legacy = scan["webmcp"]["legacy"]
    declarative = scan["webmcp"]["declarative"]
    findings: list[dict[str, Any]] = []

    document_context = [item for item in current if item["symbol"] == "document.modelContext"]
    register = [item for item in current if item["symbol"] == "registerTool"]
    execute = [item for item in current if item["symbol"] == "executeTool"]
    legacy_context = [item for item in legacy if item["symbol"] == "navigator.modelContext"]
    legacy_provide = [item for item in legacy if item["symbol"] in {"provideContext", "registerTools", "unregisterTool"}]

    if document_context and register:
        findings.append(_compat_finding(
            "info",
            "CURRENT_IMPERATIVE_API",
            "Current imperative WebMCP registration symbols were found.",
            (document_context + register)[:12],
        ))
    elif register and not document_context:
        findings.append(_compat_finding(
            "warning",
            "REGISTER_WITHOUT_DOCUMENT_CONTEXT",
            "registerTool() was found without a lexical document.modelContext reference.",
            register[:12],
            "Verify that registration uses the current Document.modelContext API or an intentional wrapper.",
        ))
    elif not current and not declarative and not legacy:
        findings.append(_compat_finding(
            "info",
            "NO_WEBMCP_INTEGRATION",
            "No current, legacy, or declarative WebMCP symbols were found.",
        ))

    if legacy_context or legacy_provide:
        findings.append(_compat_finding(
            "error",
            "LEGACY_API_SURFACE",
            "Legacy or experimental WebMCP symbols were found.",
            (legacy_context + legacy_provide)[:20],
            "Migrate to document.modelContext.registerTool() and lifecycle-bound AbortSignal unregistration.",
        ))

    if declarative:
        findings.append(_compat_finding(
            "warning",
            "DECLARATIVE_BROWSER_BRANCH",
            "Declarative WebMCP markup or events were found.",
            declarative[:20],
            "Treat declarative support as a browser-specific compatibility branch and retain ordinary form behavior.",
        ))

    if execute:
        string_calls: list[dict[str, Any]] = []
        object_calls: list[dict[str, Any]] = []
        ambiguous_calls: list[dict[str, Any]] = []
        root = Path(scan["root"])
        by_file: dict[str, str] = {}
        for item in execute:
            if item["path"] not in by_file:
                by_file[item["path"]] = _read_text(root / item["path"]) or ""
            lines = by_file[item["path"]].splitlines()
            line = lines[item["line"] - 1] if item["line"] <= len(lines) else item["excerpt"]
            evidence = {**item, "excerpt": line.strip()[:240]}
            if EXECUTE_STRING_RE.search(line):
                string_calls.append(evidence)
            elif EXECUTE_OBJECT_RE.search(line):
                object_calls.append(evidence)
            else:
                ambiguous_calls.append(evidence)
        if string_calls:
            findings.append(_compat_finding(
                "warning",
                "EXECUTE_TOOL_STRING_BRANCH",
                "executeTool() calls appear to pass JSON text, matching some browser documentation but not the current object-input draft interface.",
                string_calls,
                "Isolate this behind a tested adapter rather than spreading the string convention through application code.",
            ))
        if object_calls:
            findings.append(_compat_finding(
                "info",
                "EXECUTE_TOOL_OBJECT_BRANCH",
                "executeTool() calls appear to pass an object, matching the current draft WebIDL interface.",
                object_calls,
            ))
        if string_calls and object_calls:
            findings.append(_compat_finding(
                "error",
                "MIXED_EXECUTE_TOOL_INPUT_CONVENTIONS",
                "Both JSON-string and object executeTool() input conventions are present.",
                (string_calls + object_calls)[:20],
                "Choose one compatibility adapter per tested runtime and keep call sites consistent.",
            ))
        if ambiguous_calls:
            findings.append(_compat_finding(
                "warning",
                "EXECUTE_TOOL_INPUT_UNRESOLVED",
                "Some executeTool() call argument styles could not be classified statically.",
                ambiguous_calls,
                "Inspect the adapter or runtime feature test before changing these call sites.",
            ))

    cross_origin = [
        item for item in current
        if item["symbol"] in {"exposedTo", "fromOrigins"}
    ]
    if cross_origin:
        findings.append(_compat_finding(
            "warning",
            "CROSS_ORIGIN_TOOLS_PRESENT",
            "Cross-origin discovery or exposure options were found.",
            cross_origin[:20],
            "Verify trustworthy exact origins, the tools Permissions Policy, iframe topology, and target-browser behavior.",
        ))

    severities = [item["severity"] for item in findings]
    status = "FAIL" if "error" in severities else ("WARN" if "warning" in severities else "PASS")
    return {
        "status": status,
        "operation": "compatibility",
        "root": scan["root"],
        "repositorySha256": scan["repositorySha256"],
        "findings": findings,
        "compatibilityBranches": {
            "portableImperative": "document.modelContext with object-shaped tool input and lifecycle/execution AbortSignals",
            "browserDeclarative": "form attributes, agentInvoked/respondWith, tool events, and tool pseudo-classes; test in the target browser",
            "executeToolInput": "The current draft and some browser guidance differ; use a tested local adapter.",
            "productAvailability": "Live-verify model, workspace, application-version, rollout, and current-page availability.",
        },
        "scanSummary": {
            "frameworks": scan["frameworks"],
            "currentOccurrences": len(current),
            "legacyOccurrences": len(legacy),
            "declarativeOccurrences": len(declarative),
        },
    }


def infer_target(scan: dict[str, Any]) -> str:
    frameworks = set(scan.get("frameworks", []))
    languages = set(scan.get("languages", {}))
    if "next" in frameworks:
        return "next"
    if "react" in frameworks:
        return "react"
    if "vue" in frameworks:
        return "vue"
    if "svelte" in frameworks:
        return "svelte"
    if "angular" in frameworks:
        return "angular"
    if any(name.startswith("TypeScript") for name in languages):
        return "typescript"
    return "vanilla-js"


def output_path_for_target(target: str) -> str:
    return {
        "vanilla-js": "src/webmcp/webmcp-tools.js",
        "typescript": "src/webmcp/registerWebMCPTools.ts",
        "react": "src/webmcp/useWebMCPTools.tsx",
        "next": "src/webmcp/useWebMCPTools.tsx",
        "vue": "src/composables/useWebMCPTools.ts",
        "svelte": "src/lib/webmcp/useWebMCPTools.ts",
        "angular": "src/app/webmcp-tools.service.ts",
    }[target]


def patch_plan(
    repository: str | Path,
    manifest: dict[str, Any],
    target: str = "auto",
) -> dict[str, Any]:
    scan = scan_repository(repository)
    if target not in SUPPORTED_TARGETS:
        raise BuilderError(f"unsupported target: {target}")
    selected = infer_target(scan) if target == "auto" else target
    handler_candidates = scan.get("handlerCandidates", [])
    by_name: dict[str, list[dict[str, Any]]] = {}
    for item in handler_candidates:
        by_name.setdefault(item["name"], []).append(item)

    mappings: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    for tool in manifest.get("tools", []):
        handler = tool.get("handler", "")
        matches = by_name.get(handler, [])
        exported = [item for item in matches if item["visibility"] == "exported"]
        selected_matches = exported or matches
        mapping = {
            "tool": tool.get("name"),
            "handler": handler,
            "matches": selected_matches,
            "resolved": len(selected_matches) == 1,
        }
        mappings.append(mapping)
        if not selected_matches:
            blockers.append({
                "code": "HANDLER_NOT_FOUND",
                "tool": tool.get("name"),
                "handler": handler,
                "message": "No lexical handler candidate with this exact name was found.",
            })
        elif len(selected_matches) > 1:
            warnings.append({
                "code": "HANDLER_AMBIGUOUS",
                "tool": tool.get("name"),
                "handler": handler,
                "message": "Multiple exact-name candidates were found; choose the intended application action.",
                "matches": selected_matches,
            })
        elif selected_matches[0]["visibility"] != "exported":
            warnings.append({
                "code": "HANDLER_NOT_EXPORTED",
                "tool": tool.get("name"),
                "handler": handler,
                "message": "The candidate is local; export it or build the adapter in the owning module.",
                "match": selected_matches[0],
            })

    detected = infer_target(scan)
    if target != "auto" and selected != detected:
        warnings.append({
            "code": "TARGET_DIFFERS_FROM_REPOSITORY",
            "message": f"Requested target {selected!r} differs from inferred target {detected!r}.",
        })
    if scan["webmcp"]["legacy"]:
        warnings.append({
            "code": "LEGACY_WEBMCP_PRESENT",
            "message": "Legacy WebMCP symbols should be migrated or isolated before adding a second registration path.",
            "evidence": scan["webmcp"]["legacy"][:12],
        })

    owner_candidates = []
    for item in scan["routes"] + scan["components"]:
        if item not in owner_candidates:
            owner_candidates.append(item)
    status = "BLOCKED" if blockers else ("WARN" if warnings else "READY")
    steps = [
        "Confirm each exact handler match reaches the same validation, authorization, and state transition used by the human interface.",
        f"Generate the {selected} adapter and place it at {output_path_for_target(selected)} or an equivalent project-local path.",
        "Bind registration to the narrowest route, component, selection, mode, or permission lifetime declared by the manifest.",
        "Pass the invocation AbortSignal into cancellable I/O and re-check volatile page state immediately before commit.",
        "Update the visible interface from the same application state changed by the tool, then return compact success evidence.",
        "Run deterministic manifest, shim, syntax/type, and repository tests before target-browser discovery and agent-selection tests.",
    ]
    return {
        "status": status,
        "operation": "patch-plan",
        "repository": scan["root"],
        "repositorySha256": scan["repositorySha256"],
        "target": selected,
        "inferredTarget": detected,
        "suggestedOutput": output_path_for_target(selected),
        "handlerMappings": mappings,
        "ownerCandidates": owner_candidates[:30],
        "forms": scan["forms"][:30],
        "blockers": blockers,
        "warnings": warnings,
        "steps": steps,
        "nonActions": [
            "No repository file was modified.",
            "No import path, authorization rule, or business handler was invented.",
            "Static matches are evidence for review, not proof of behavioral equivalence.",
        ],
    }


def _descriptors(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for tool in manifest.get("tools", []):
        item: dict[str, Any] = {
            "name": tool["name"],
            "description": tool["description"],
            "inputSchema": tool["inputSchema"],
            "annotations": tool["annotations"],
            "handler": tool["handler"],
            "registration": {
                "exposedTo": tool.get("registration", {}).get("exposedTo", []),
            },
        }
        if "title" in tool:
            item["title"] = tool["title"]
        out.append(item)
    return out


def _descriptor_json(manifest: dict[str, Any]) -> str:
    return json.dumps(_descriptors(manifest), ensure_ascii=False, indent=2, sort_keys=True)


def _ts_runtime(manifest: dict[str, Any], manifest_hash: str) -> str:
    descriptors = _descriptor_json(manifest)
    return f'''// Generated by webmcp-toolkit {BUILDER_VERSION}.
// Manifest SHA-256: {manifest_hash}
// Wire only existing application handlers. This file does not replace app authorization or validation.

export const WEBMCP_MANIFEST_SHA256 = "{manifest_hash}";
const TOOL_DESCRIPTORS = {descriptors} as const;

type ToolExecutionContext = {{
  signal?: AbortSignal;
  toolName: string;
}};

export type WebMCPHandler = (
  input: Record<string, unknown>,
  context: ToolExecutionContext,
) => unknown | Promise<unknown>;

export type WebMCPHandlers = Record<string, WebMCPHandler>;

type RegisterOptions = {{
  signal?: AbortSignal;
}};

type ModelContextLike = {{
  registerTool(
    tool: {{
      name: string;
      title?: string;
      description: string;
      inputSchema?: object;
      annotations?: {{ readOnlyHint?: boolean; untrustedContentHint?: boolean }};
      execute(
        input: Record<string, unknown>,
        options: {{ signal: AbortSignal }},
      ): Promise<unknown>;
    }},
    options?: {{ signal?: AbortSignal; exposedTo?: string[] }},
  ): Promise<void>;
}};

export type WebMCPRegistration = Readonly<{{
  supported: boolean;
  registered: readonly string[];
  signal?: AbortSignal;
  dispose(reason?: unknown): void;
}}>;

function abortReason(signal: AbortSignal): unknown {{
  return signal.reason ?? new DOMException("The operation was aborted.", "AbortError");
}}

function getModelContext(): ModelContextLike | undefined {{
  if (typeof document === "undefined") return undefined;
  return (document as Document & {{ modelContext?: ModelContextLike }}).modelContext;
}}

export async function registerWebMCPTools(
  handlers: WebMCPHandlers,
  options: RegisterOptions = {{}},
): Promise<WebMCPRegistration> {{
  const modelContext = getModelContext();
  if (typeof modelContext?.registerTool !== "function") {{
    return Object.freeze({{
      supported: false,
      registered: Object.freeze([]),
      dispose() {{}},
    }});
  }}

  for (const descriptor of TOOL_DESCRIPTORS) {{
    if (typeof handlers[descriptor.handler] !== "function") {{
      throw new TypeError(
        `Missing WebMCP application handler: ${{descriptor.handler}} for ${{descriptor.name}}`,
      );
    }}
  }}

  const controller = new AbortController();
  const externalSignal = options.signal;
  let externalAbortListener: (() => void) | undefined;
  if (externalSignal) {{
    if (externalSignal.aborted) throw abortReason(externalSignal);
    externalAbortListener = () => controller.abort(abortReason(externalSignal));
    externalSignal.addEventListener("abort", externalAbortListener, {{ once: true }});
  }}

  const cleanupExternalListener = () => {{
    if (externalSignal && externalAbortListener) {{
      externalSignal.removeEventListener("abort", externalAbortListener);
      externalAbortListener = undefined;
    }}
  }};

  const registered: string[] = [];
  try {{
    for (const descriptor of TOOL_DESCRIPTORS) {{
      const handler = handlers[descriptor.handler];
      const registrationOptions: {{ signal: AbortSignal; exposedTo?: string[] }} = {{
        signal: controller.signal,
      }};
      if (descriptor.registration.exposedTo.length > 0) {{
        registrationOptions.exposedTo = [...descriptor.registration.exposedTo];
      }}
      await modelContext.registerTool(
        {{
          name: descriptor.name,
          ...("title" in descriptor ? {{ title: descriptor.title }} : {{}}),
          description: descriptor.description,
          inputSchema: descriptor.inputSchema,
          annotations: descriptor.annotations,
          execute: async (input, executionOptions) => {{
            if (executionOptions.signal.aborted) {{
              throw abortReason(executionOptions.signal);
            }}
            return await handler(input, {{
              signal: executionOptions.signal,
              toolName: descriptor.name,
            }});
          }},
        }},
        registrationOptions,
      );
      registered.push(descriptor.name);
    }}
  }} catch (error) {{
    controller.abort(error);
    cleanupExternalListener();
    throw error;
  }}

  let disposed = false;
  return Object.freeze({{
    supported: true,
    registered: Object.freeze([...registered]),
    signal: controller.signal,
    dispose(reason?: unknown) {{
      if (disposed) return;
      disposed = true;
      controller.abort(reason);
      cleanupExternalListener();
    }},
  }});
}}
'''


def _react_adapter(manifest: dict[str, Any], manifest_hash: str, next_client: bool) -> str:
    runtime = _ts_runtime(manifest, manifest_hash)
    prefix = '"use client";\n\n' if next_client else ""
    names = json.dumps([tool["handler"] for tool in manifest.get("tools", [])], ensure_ascii=False)
    hook = f'''
import {{ useEffect, useRef, useState }} from "react";

export type WebMCPHookState = Readonly<{{
  status: "idle" | "registering" | "ready" | "unsupported" | "error";
  registered: readonly string[];
  error?: unknown;
}}>;

const WEBMCP_HANDLER_NAMES = {names} as const;

export function useWebMCPTools(
  handlers: WebMCPHandlers,
  enabled = true,
): WebMCPHookState {{
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers;
  const [state, setState] = useState<WebMCPHookState>({{
    status: "idle",
    registered: Object.freeze([]),
  }});

  useEffect(() => {{
    if (!enabled) {{
      setState({{ status: "idle", registered: Object.freeze([]) }});
      return;
    }}

    let active = true;
    const lifecycle = new AbortController();
    const stableHandlers = Object.fromEntries(
      WEBMCP_HANDLER_NAMES.map((name) => [
        name,
        (input: Record<string, unknown>, context: ToolExecutionContext) =>
          handlersRef.current[name](input, context),
      ]),
    ) as WebMCPHandlers;

    setState({{ status: "registering", registered: Object.freeze([]) }});
    void registerWebMCPTools(stableHandlers, {{ signal: lifecycle.signal }})
      .then((registration) => {{
        if (!active) {{
          registration.dispose();
          return;
        }}
        setState({{
          status: registration.supported ? "ready" : "unsupported",
          registered: registration.registered,
        }});
      }})
      .catch((error: unknown) => {{
        if (active && !lifecycle.signal.aborted) {{
          setState({{ status: "error", registered: Object.freeze([]), error }});
        }}
      }});

    return () => {{
      active = false;
      lifecycle.abort();
    }};
  }}, [enabled]);

  return state;
}}
'''
    return prefix + runtime + hook


def _vue_adapter(manifest: dict[str, Any], manifest_hash: str) -> str:
    runtime = _ts_runtime(manifest, manifest_hash)
    names = json.dumps([tool["handler"] for tool in manifest.get("tools", [])], ensure_ascii=False)
    return runtime + f'''
import {{ onBeforeUnmount, onMounted, shallowRef }} from "vue";

export type WebMCPVueState = Readonly<{{
  status: "idle" | "registering" | "ready" | "unsupported" | "error";
  registered: readonly string[];
  error?: unknown;
}}>;

const WEBMCP_HANDLER_NAMES = {names} as const;

export function useWebMCPTools(
  getHandlers: () => WebMCPHandlers,
  enabled = true,
) {{
  const state = shallowRef<WebMCPVueState>({{
    status: "idle",
    registered: Object.freeze([]),
  }});
  let lifecycle: AbortController | undefined;

  onMounted(async () => {{
    if (!enabled) return;
    lifecycle = new AbortController();
    const stableHandlers = Object.fromEntries(
      WEBMCP_HANDLER_NAMES.map((name) => [
        name,
        (input: Record<string, unknown>, context: ToolExecutionContext) =>
          getHandlers()[name](input, context),
      ]),
    ) as WebMCPHandlers;
    state.value = {{ status: "registering", registered: Object.freeze([]) }};
    try {{
      const registration = await registerWebMCPTools(stableHandlers, {{
        signal: lifecycle.signal,
      }});
      if (!lifecycle.signal.aborted) {{
        state.value = {{
          status: registration.supported ? "ready" : "unsupported",
          registered: registration.registered,
        }};
      }}
    }} catch (error: unknown) {{
      if (!lifecycle.signal.aborted) {{
        state.value = {{ status: "error", registered: Object.freeze([]), error }};
      }}
    }}
  }});

  onBeforeUnmount(() => lifecycle?.abort());
  return {{ state, stop: () => lifecycle?.abort() }};
}}
'''


def _svelte_adapter(manifest: dict[str, Any], manifest_hash: str) -> str:
    runtime = _ts_runtime(manifest, manifest_hash)
    names = json.dumps([tool["handler"] for tool in manifest.get("tools", [])], ensure_ascii=False)
    return runtime + f'''
import {{ onMount }} from "svelte";

export type WebMCPSvelteState = Readonly<{{
  status: "idle" | "registering" | "ready" | "unsupported" | "error";
  registered: readonly string[];
  error?: unknown;
}}>;

const WEBMCP_HANDLER_NAMES = {names} as const;

export function useWebMCPTools(
  getHandlers: () => WebMCPHandlers,
  onState: (state: WebMCPSvelteState) => void = () => {{}},
  enabled = true,
): void {{
  onMount(() => {{
    if (!enabled) return;
    const lifecycle = new AbortController();
    const stableHandlers = Object.fromEntries(
      WEBMCP_HANDLER_NAMES.map((name) => [
        name,
        (input: Record<string, unknown>, context: ToolExecutionContext) =>
          getHandlers()[name](input, context),
      ]),
    ) as WebMCPHandlers;

    onState({{ status: "registering", registered: Object.freeze([]) }});
    void registerWebMCPTools(stableHandlers, {{ signal: lifecycle.signal }})
      .then((registration) => {{
        if (!lifecycle.signal.aborted) {{
          onState({{
            status: registration.supported ? "ready" : "unsupported",
            registered: registration.registered,
          }});
        }}
      }})
      .catch((error: unknown) => {{
        if (!lifecycle.signal.aborted) {{
          onState({{ status: "error", registered: Object.freeze([]), error }});
        }}
      }});

    return () => lifecycle.abort();
  }});
}}
'''


def _angular_adapter(manifest: dict[str, Any], manifest_hash: str) -> str:
    runtime = _ts_runtime(manifest, manifest_hash)
    return runtime + '''
import { Injectable, OnDestroy } from "@angular/core";

@Injectable({ providedIn: "root" })
export class WebMCPToolsService implements OnDestroy {
  private lifecycle?: AbortController;
  private registration?: WebMCPRegistration;

  async start(handlers: WebMCPHandlers): Promise<WebMCPRegistration> {
    this.stop();
    this.lifecycle = new AbortController();
    this.registration = await registerWebMCPTools(handlers, {
      signal: this.lifecycle.signal,
    });
    return this.registration;
  }

  stop(reason?: unknown): void {
    this.registration?.dispose(reason);
    this.registration = undefined;
    this.lifecycle?.abort(reason);
    this.lifecycle = undefined;
  }

  ngOnDestroy(): void {
    this.stop();
  }
}
'''


def generate_target(
    manifest: dict[str, Any],
    manifest_hash: str,
    target: str,
    javascript_generator: Any,
) -> str:
    del javascript_generator  # Kept in the public signature for v2 caller compatibility.
    if target not in SUPPORTED_TARGETS or target == "auto":
        raise BuilderError(f"generation target must be one of: {', '.join(SUPPORTED_TARGETS[1:])}")
    try:
        import webmcp_codegen as codegen
    except ImportError:
        from . import webmcp_codegen as codegen  # type: ignore[no-redef]
    try:
        return codegen.generate_target(manifest, manifest_hash, target)
    except codegen.CodegenError as exc:
        raise BuilderError(str(exc)) from exc


def text_summary(report: dict[str, Any]) -> str:
    operation = report.get("operation")
    if operation == "scan-repo":
        lines = [
            f"{report['status']}: scanned {report['sourceSummary']['scannedFiles']} file(s)",
            f"Frameworks: {', '.join(report['frameworks']) or 'none'}",
            f"Handlers: {len(report['handlerCandidates'])}",
            f"Forms: {len(report['forms'])}",
            "WebMCP: "
            f"{len(report['webmcp']['current'])} current, "
            f"{len(report['webmcp']['legacy'])} legacy, "
            f"{len(report['webmcp']['declarative'])} declarative occurrence(s)",
        ]
        return "\n".join(lines)
    if operation == "compatibility":
        lines = [f"{report['status']}: {len(report['findings'])} compatibility finding(s)"]
        lines.extend(
            f"- {item['severity'].upper()} {item['code']}: {item['message']}"
            for item in report["findings"]
        )
        return "\n".join(lines)
    if operation == "patch-plan":
        lines = [
            f"{report['status']}: target {report['target']}",
            f"Suggested output: {report['suggestedOutput']}",
            f"Handler mappings: {sum(1 for item in report['handlerMappings'] if item['resolved'])}/{len(report['handlerMappings'])} uniquely resolved",
            f"Blockers: {len(report['blockers'])}; warnings: {len(report['warnings'])}",
        ]
        lines.extend(f"- {step}" for step in report["steps"])
        return "\n".join(lines)
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
