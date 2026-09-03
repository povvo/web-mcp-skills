#!/usr/bin/env python3
"""Run the WebMCP skill's deterministic, package-local verification suites.

This command proves the compiler and its local fixtures. It deliberately does
not claim native browser discovery, ChatGPT Site tools behavior, WPT
conformance, model selection quality, deployment, or a live MCP transport.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Iterable


SCHEMA_VERSION = "webmcp-self-test.v1"
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
REPOSITORY_ROOT = SKILL_ROOT.parents[1]
VALIDATION_ROOT = SKILL_ROOT / "validation"
NODE_TEST_ROOT = VALIDATION_ROOT / "node"
TYPECHECK_ROOT = VALIDATION_ROOT / "typecheck"

CORE_NODE_TESTS = (
    "lifecycle.test.mjs",
    "product-create.test.mjs",
    "proposals.test.mjs",
    "runtime.test.mjs",
    "serialization.test.mjs",
)

STATUS_ORDER = {
    "PASS": 0,
    "NOT_RUN": 1,
    "UNSUPPORTED": 2,
    "BLOCKED": 3,
    "FAIL": 4,
}


class SelfTestInputError(ValueError):
    """Raised for invalid self-test inputs."""


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _display_command(command: Iterable[str]) -> str:
    rendered: list[str] = []
    for value in command:
        item = str(value)
        rendered.append(json.dumps(item) if any(character.isspace() for character in item) else item)
    return " ".join(rendered)


def _tail(value: str, limit: int = 4000) -> str:
    if len(value) <= limit:
        return value
    return "...<truncated>\n" + value[-limit:]


def _aggregate(checks: Iterable[dict[str, Any]]) -> str:
    statuses = [str(check.get("status", "FAIL")) for check in checks]
    if not statuses:
        return "NOT_RUN"
    return max(statuses, key=lambda status: STATUS_ORDER.get(status, STATUS_ORDER["FAIL"]))


def _static_check(
    check_id: str,
    status: str,
    summary: str,
    *,
    evidence: list[dict[str, str]] | None = None,
    reason: str | None = None,
    next_step: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": check_id,
        "status": status,
        "summary": summary,
        "evidence": evidence or [],
    }
    if reason:
        result["reason"] = reason
    if next_step:
        result["nextStep"] = next_step
    return result


def _run_check(
    check_id: str,
    summary: str,
    command: list[str],
    *,
    cwd: Path,
    timeout_seconds: int,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
            env=env,
        )
    except FileNotFoundError as exc:
        return _static_check(
            check_id,
            "BLOCKED",
            summary,
            reason=f"Required executable was not found: {exc.filename or command[0]}",
            next_step=f"Install {command[0]} and rerun the self-test.",
        )
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "") + (exc.stderr or "")
        return {
            "id": check_id,
            "status": "FAIL",
            "summary": summary,
            "command": command,
            "commandText": _display_command(command),
            "cwd": str(cwd),
            "durationMs": round((time.perf_counter() - started) * 1000),
            "reason": f"Command exceeded the {timeout_seconds}-second test budget.",
            "evidence": [
                {"kind": "output-sha256", "value": _sha256_text(output)},
            ],
            "outputTail": _tail(output),
        }

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    combined = stdout + stderr
    return {
        "id": check_id,
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "summary": summary,
        "command": command,
        "commandText": _display_command(command),
        "cwd": str(cwd),
        "exitCode": completed.returncode,
        "durationMs": round((time.perf_counter() - started) * 1000),
        "evidence": [
            {"kind": "stdout-sha256", "value": _sha256_text(stdout)},
            {"kind": "stderr-sha256", "value": _sha256_text(stderr)},
        ],
        "outputTail": _tail(combined),
    }


def _node_version(node: str | None) -> str | None:
    if node is None:
        return None
    completed = subprocess.run(
        [node, "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def _dependency_check() -> dict[str, Any]:
    try:
        version = importlib.metadata.version("jsonschema")
    except importlib.metadata.PackageNotFoundError:
        return _static_check(
            "python.dependencies",
            "BLOCKED",
            "Pinned Python contract dependency is installed.",
            reason="jsonschema is not installed in the current Python environment.",
            next_step=f'Run "{sys.executable}" -m pip install -r "{SKILL_ROOT / "requirements.txt"}".',
        )
    return _static_check(
        "python.dependencies",
        "PASS",
        "Pinned Python contract dependency is installed.",
        evidence=[{"kind": "package", "value": f"jsonschema=={version}"}],
    )


def _portability_check() -> dict[str, Any]:
    dependency_directory = "node" + "_modules"
    nested_archive_suffixes = {".skill", ".zip"}
    mirror_key = "local" + "Mirror"
    external_path_token = "docs" + "/"
    text_suffixes = {
        ".css",
        ".html",
        ".js",
        ".json",
        ".md",
        ".mjs",
        ".py",
        ".sh",
        ".toml",
        ".ts",
        ".tsx",
        ".txt",
        ".yaml",
        ".yml",
    }
    findings = [
        f"installed dependency tree: {path.relative_to(SKILL_ROOT)}"
        for path in SKILL_ROOT.rglob(dependency_directory)
        if path.is_dir()
    ]
    findings.extend(
        f"nested release archive: {path.relative_to(SKILL_ROOT)}"
        for path in SKILL_ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in nested_archive_suffixes
    )
    inspected = 0
    for path in sorted(SKILL_ROOT.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in text_suffixes:
            continue
        inspected += 1
        text = path.read_text(encoding="utf-8")
        if mirror_key in text:
            findings.append(f"workspace mirror field: {path.relative_to(SKILL_ROOT)}")
        for line_number, line in enumerate(text.splitlines(), start=1):
            without_urls = re.sub(r"https?://[^\s\"'`<>]+", "", line)
            if external_path_token in without_urls.lower():
                findings.append(
                    "external documentation path: "
                    f"{path.relative_to(SKILL_ROOT)}:{line_number}"
                )

    if findings:
        return _static_check(
            "package.portability",
            "FAIL",
            "Portable Skill source has no installed tree, nested release archive, or workspace documentation binding.",
            reason="; ".join(findings[:20]),
            next_step="Remove every reported artifact or path binding before packaging.",
        )
    return _static_check(
        "package.portability",
        "PASS",
        "Portable Skill source has no installed tree, nested release archive, or workspace documentation binding.",
        evidence=[{"kind": "note", "value": f"inspected {inspected} packaged text files"}],
    )


def _typecheck_dependency_check(
    node: str | None,
    npm: str | None,
    workspace: Path,
    *,
    timeout_seconds: int,
) -> dict[str, Any]:
    source_files = tuple(
        TYPECHECK_ROOT / name
        for name in ("package.json", "package-lock.json", "tsconfig.base.json")
    )
    missing = [str(path) for path in source_files if not path.is_file()]
    install_command = [
        npm or "npm",
        "ci",
        "--ignore-scripts",
        "--include=dev",
        "--no-audit",
        "--no-fund",
    ]
    if node is None:
        return _static_check(
            "typecheck.dependencies",
            "BLOCKED",
            "Locked official-types toolchain is installed in a disposable workspace.",
            reason="Node.js is not installed or is not on PATH.",
            next_step="Install Node.js 24 or newer, then rerun the full self-test.",
        )
    if npm is None:
        return _static_check(
            "typecheck.dependencies",
            "BLOCKED",
            "Locked official-types toolchain is installed in a disposable workspace.",
            reason="npm is not installed or is not on PATH.",
            next_step="Install npm, then rerun the full self-test.",
        )
    if missing:
        return _static_check(
            "typecheck.dependencies",
            "FAIL",
            "Locked official-types toolchain is installed in a disposable workspace.",
            reason="The clean package is missing locked typecheck source: " + ", ".join(missing),
            next_step="Restore the package manifest, lockfile, and TypeScript configuration.",
        )
    workspace.mkdir(parents=True, exist_ok=True)
    for source in source_files:
        shutil.copy2(source, workspace / source.name)

    result = _run_check(
        "typecheck.dependencies",
        "Locked official-types toolchain is installed in a disposable workspace.",
        install_command,
        cwd=workspace,
        timeout_seconds=timeout_seconds,
    )
    tsc = workspace / "node_modules" / "typescript" / "bin" / "tsc"
    if result["status"] == "PASS" and not tsc.is_file():
        result["status"] = "FAIL"
        result["reason"] = "npm completed without creating the pinned TypeScript executable."
    result["evidence"].extend(
        {"kind": "file-sha256", "value": f"{source.name}:{_sha256_file(source)}"}
        for source in source_files
    )
    result["workspacePolicy"] = "temporary-outside-skill-source"
    return result


def run_self_test(profile: str, *, timeout_seconds: int = 300) -> dict[str, Any]:
    if profile not in {"core", "full"}:
        raise SelfTestInputError("profile must be core or full")
    if timeout_seconds < 1:
        raise SelfTestInputError("timeout_seconds must be at least 1")

    node = shutil.which("node")
    npm = shutil.which("npm")
    checks: list[dict[str, Any]] = []
    checks.append(_portability_check())
    checks.append(_dependency_check())

    if checks[-1]["status"] == "PASS":
        checks.append(
            _run_check(
                "python.contract-and-compiler",
                "Python schema, contract, product, DUAL, proposal, and evidence suites pass.",
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    str(VALIDATION_ROOT / "python"),
                    "-p",
                    "test_*.py",
                    "-v",
                ],
                cwd=REPOSITORY_ROOT,
                timeout_seconds=timeout_seconds,
            )
        )
    else:
        checks.append(
            _static_check(
                "python.contract-and-compiler",
                "NOT_RUN",
                "Python schema, contract, product, DUAL, proposal, and evidence suites pass.",
                reason="The required Python dependency preflight did not pass.",
            )
        )

    if node is None:
        checks.append(
            _static_check(
                "node.runtime-and-fixtures",
                "BLOCKED",
                "Node runtime, lifecycle, serialization, product, and proposal suites pass.",
                reason="Node.js is not installed or is not on PATH.",
                next_step="Install Node.js 24 or newer and rerun the self-test.",
            )
        )
    else:
        node_files = [str(NODE_TEST_ROOT / filename) for filename in CORE_NODE_TESTS]
        checks.append(
            _run_check(
                "node.runtime-and-fixtures",
                "Node runtime, lifecycle, serialization, product, and proposal suites pass.",
                [node, "--test", *node_files],
                cwd=REPOSITORY_ROOT,
                timeout_seconds=timeout_seconds,
            )
        )

    if profile == "full":
        with tempfile.TemporaryDirectory(prefix="webmcp-typecheck-") as temporary:
            typecheck_workspace = Path(temporary).resolve()
            typecheck_dependencies = _typecheck_dependency_check(
                node,
                npm,
                typecheck_workspace,
                timeout_seconds=timeout_seconds,
            )
            checks.append(typecheck_dependencies)
            if typecheck_dependencies["status"] == "PASS" and node is not None:
                test_environment = os.environ.copy()
                test_environment["WEBMCP_TYPECHECK_ROOT"] = str(typecheck_workspace)
                test_environment["WEBMCP_TEST_PYTHON"] = sys.executable
                checks.append(
                    _run_check(
                        "typecheck.framework-matrix",
                        "All TypeScript and framework targets compile against pinned official types.",
                        [node, "--test", str(NODE_TEST_ROOT / "typecheck.test.mjs")],
                        cwd=REPOSITORY_ROOT,
                        timeout_seconds=timeout_seconds,
                        env=test_environment,
                    )
                )
            else:
                checks.append(
                    _static_check(
                        "typecheck.framework-matrix",
                        "NOT_RUN",
                        "All TypeScript and framework targets compile against pinned official types.",
                        reason="The isolated typecheck dependency installation did not pass.",
                    )
                )

    status = _aggregate(checks)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "profile": profile,
        "status": status,
        "skillRoot": str(SKILL_ROOT),
        "environment": {
            "python": sys.version.split()[0],
            "pythonExecutable": sys.executable,
            "node": _node_version(node),
            "nodeExecutable": node,
            "platform": sys.platform,
        },
        "scope": {
            "proved": [
                "contract validation",
                "portable source boundary",
                "CREATE and EXTEND compiler behavior",
                "WebMCP adapter lifecycle and JSON serialization",
                "DUAL shared-operation parity through dependency-injected adapters",
                "proposal mocks with non-conformance labels",
                "candidate-bound verification logic",
            ] + (["official-types framework compilation"] if profile == "full" else []),
            "notClaimed": [
                "WPT conformance",
                "native browser discovery or invocation",
                "native ChatGPT Site tools behavior",
                "model tool-selection quality",
                "live MCP SDK transport",
                "deployment or challenge submission",
            ],
        },
        "counts": {
            state: sum(1 for check in checks if check["status"] == state)
            for state in STATUS_ORDER
        },
        "checks": checks,
    }


def _render_text(report: dict[str, Any]) -> str:
    lines = [f"{report['status']}: WebMCP {report['profile']} self-test"]
    for check in report["checks"]:
        lines.append(f"- {check['status']} {check['id']}: {check['summary']}")
        if check.get("reason"):
            lines.append(f"  reason: {check['reason']}")
        if check.get("nextStep"):
            lines.append(f"  next: {check['nextStep']}")
    lines.append("- NOT CLAIMED: " + ", ".join(report["scope"]["notClaimed"]))
    return "\n".join(lines)


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="webmcp-self-test",
        description="Run deterministic package-local WebMCP skill verification.",
    )
    parser.add_argument("--profile", choices=("core", "full"), default="core")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument("--output", help="optional path for the complete JSON report")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = run_self_test(args.profile, timeout_seconds=args.timeout_seconds)
    except SelfTestInputError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 64
    if args.output:
        _write_report(Path(args.output), report)
    if args.format == "json":
        # Keep machine output safe on Windows consoles that still default to a
        # legacy code page; evidence tails can contain Unicode test markers.
        print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
    else:
        print(_render_text(report))
    return {
        "PASS": 0,
        "FAIL": 1,
        "BLOCKED": 2,
        "UNSUPPORTED": 3,
        "NOT_RUN": 4,
    }[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
