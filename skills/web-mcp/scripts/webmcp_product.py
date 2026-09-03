#!/usr/bin/env python3
"""Compile an explicit WebMCP product profile into verified adapter artifacts.

The compiler binds product capabilities to a validated toolset and produces
deterministic browser adapters. It never fabricates domain operations: handler
readiness is inspected in the application repository and remains BLOCKED until
every tool maps to one exact callable operation candidate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping

try:
    import webmcp_builder as builder
    import webmcp_codegen as codegen
    import webmcp_contract as contract
except ImportError:  # pragma: no cover - package-style import fallback.
    from . import webmcp_builder as builder  # type: ignore[no-redef]
    from . import webmcp_codegen as codegen  # type: ignore[no-redef]
    from . import webmcp_contract as contract  # type: ignore[no-redef]


VERSION = "3.0.0"
TARGET_FILENAMES = {
    "vanilla-js": "webmcp-tools.js",
    "typescript": "registerWebMCPTools.ts",
    "react": "useWebMCPTools.tsx",
    "next": "useWebMCPTools.tsx",
    "vue": "useWebMCPTools.ts",
    "svelte": "useWebMCPTools.ts",
    "angular": "webmcp-tools.service.ts",
}


class ProductCompilerError(RuntimeError):
    """Raised when product compilation cannot proceed safely."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ProductCompilerError(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ProductCompilerError(
            f"invalid JSON in {path} at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(value, dict):
        raise ProductCompilerError(f"JSON root must be an object: {path}")
    return value


def load_product_bundle(
    product_path: str | Path,
) -> tuple[dict[str, Any], dict[str, Any], Path, Path, Path]:
    """Load product and referenced toolset with paths resolved from the profile."""

    resolved_product = Path(product_path).expanduser().resolve()
    product = _load_object(resolved_product)
    toolset_ref = product.get("toolset")
    app_ref = product.get("applicationRoot")
    if not isinstance(toolset_ref, str) or not toolset_ref.strip():
        raise ProductCompilerError("product.toolset must be a non-empty relative or absolute path")
    if not isinstance(app_ref, str) or not app_ref.strip():
        raise ProductCompilerError("product.applicationRoot must be a non-empty path")
    toolset_path = (resolved_product.parent / toolset_ref).resolve()
    application_root = (resolved_product.parent / app_ref).resolve()
    toolset = _load_object(toolset_path)
    return product, toolset, resolved_product, toolset_path, application_root


def capability_matrix(
    product: Mapping[str, Any], toolset: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Return the canonical human/UI/operation/adapter mapping."""

    tools = {
        item.get("name"): item
        for item in toolset.get("tools", [])
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    matrix: list[dict[str, Any]] = []
    for item in product.get("capabilities", []):
        if not isinstance(item, dict):
            continue
        webmcp = item.get("webmcpTool", {})
        operation = item.get("operation", {})
        ui = item.get("ui", {})
        state = item.get("state", {})
        result = item.get("resultContract", {})
        mcp = item.get("mcpTool")
        name = webmcp.get("name") if isinstance(webmcp, dict) else None
        tool = tools.get(name, {})
        matrix.append({
            "capability": item.get("id"),
            "userJourney": item.get("userJourney"),
            "humanEntrypoint": ui.get("humanEntrypoint") if isinstance(ui, dict) else None,
            "operation": operation.get("id") if isinstance(operation, dict) else None,
            "handler": operation.get("handler") if isinstance(operation, dict) else None,
            "operationModule": operation.get("module") if isinstance(operation, dict) else None,
            "operationSource": operation.get("source") if isinstance(operation, dict) else None,
            "effect": operation.get("effect") if isinstance(operation, dict) else None,
            "webmcpTool": name,
            "mcpTool": mcp.get("name") if isinstance(mcp, dict) else None,
            "stateReads": state.get("reads", []) if isinstance(state, dict) else [],
            "stateWrites": state.get("writes", []) if isinstance(state, dict) else [],
            "visibleEffect": ui.get("visibleEffect") if isinstance(ui, dict) else None,
            "resultSummary": result.get("summary") if isinstance(result, dict) else None,
            "resultIdentifiers": result.get("identifiers", []) if isinstance(result, dict) else [],
            "inputSchema": tool.get("inputSchema") if isinstance(tool, dict) else None,
        })
    return matrix


def _release_gates(product: Mapping[str, Any]) -> list[dict[str, Any]]:
    release = product.get("release")
    surface = product.get("surface")
    targets = set(product.get("targets", [])) if isinstance(product.get("targets"), list) else set()
    gates: list[dict[str, Any]] = [
        {"id": "contract", "class": "deterministic", "required": True},
        {"id": "operations", "class": "application", "required": True},
        {"id": "adapter-runtime", "class": "deterministic", "required": True},
        {"id": "normal-ui", "class": "application", "required": True},
        {"id": "shared-state", "class": "browser", "required": release != "development"},
    ]
    if surface == "dual":
        gates.append({"id": "dual-adapter-parity", "class": "integration", "required": True})
    if "chromium-webmcp" in targets:
        gates.append({"id": "native-chromium", "class": "host-native", "required": release != "development"})
    if "chatgpt-site-tools" in targets:
        gates.append({"id": "native-chatgpt-site-tools", "class": "host-native", "required": release != "development"})
    if release in {"production", "challenge"}:
        gates.append({"id": "clean-package", "class": "release", "required": True})
    if release == "challenge":
        gates.extend([
            {"id": "live-url", "class": "deployment", "required": True},
            {"id": "public-source-and-license", "class": "release", "required": True},
            {"id": "demo-video", "class": "release", "required": True},
        ])
    return gates


def build_plan(
    product: Mapping[str, Any],
    toolset: Mapping[str, Any],
    application_root: str | Path | None,
    target: str = "auto",
) -> dict[str, Any]:
    """Validate contracts and, when possible, inspect real handler readiness."""

    validation = contract.validate_bundle(product, toolset)
    selected_target = target
    handler_check: dict[str, Any]
    if validation["status"] == "FAIL":
        handler_check = {
            "status": "NOT_RUN",
            "reason": "Product/toolset contract validation failed.",
        }
    elif application_root is None:
        handler_check = {
            "status": "NOT_RUN",
            "reason": "No application repository was supplied for handler discovery.",
        }
    else:
        root = Path(application_root).expanduser().resolve()
        if not root.is_dir():
            handler_check = {
                "status": "BLOCKED",
                "reason": f"Application root does not exist or is not a directory: {root}",
            }
        else:
            patch = builder.patch_plan(root, dict(toolset), target)
            selected_target = patch.get("target", patch.get("selectedTarget", target))
            patch_status = patch.get("status")
            expected_modules = {
                item.get("operation", {}).get("handler"): str(
                    item.get("operation", {}).get("module", "")
                ).replace("\\", "/").removeprefix("./")
                for item in product.get("capabilities", [])
                if isinstance(item, dict) and isinstance(item.get("operation"), dict)
            }
            module_blockers: list[dict[str, Any]] = []
            for mapping in patch.get("handlerMappings", []):
                if not isinstance(mapping, dict):
                    continue
                handler = mapping.get("handler")
                expected_module = expected_modules.get(handler)
                matches = mapping.get("matches", [])
                if not expected_module or not isinstance(matches, list) or len(matches) != 1:
                    continue
                actual_module = str(matches[0].get("path", "")).replace("\\", "/")
                if actual_module != expected_module:
                    mapping["resolved"] = False
                    module_blockers.append({
                        "code": "HANDLER_MODULE_MISMATCH",
                        "handler": handler,
                        "expectedModule": expected_module,
                        "actualModule": actual_module,
                        "message": "The exact handler name resolves in a different module than the product capability contract.",
                    })
            if module_blockers:
                patch_status = "BLOCKED"
            handler_check = {
                "status": "PASS" if patch_status == "READY" else patch_status,
                "repository": str(root),
                "repositorySha256": patch.get("repositorySha256"),
                "target": patch.get("target", patch.get("selectedTarget")),
                "handlerMappings": patch.get("handlerMappings", []),
                "blockers": [*patch.get("blockers", []), *module_blockers],
                "warnings": patch.get("warnings", []),
            }

    if validation["status"] == "FAIL":
        status = "FAIL"
    elif handler_check["status"] == "BLOCKED":
        status = "BLOCKED"
    elif validation["status"] == "WARN" or handler_check["status"] == "WARN":
        status = "WARN"
    elif handler_check["status"] == "NOT_RUN":
        status = "NOT_RUN"
    else:
        status = "PASS"

    profiles = product.get("profiles", {})
    declarative = profiles.get("declarativeProposal", {}) if isinstance(profiles, dict) else {}
    worker = profiles.get("serviceWorkerProposal", {}) if isinstance(profiles, dict) else {}
    return {
        "status": status,
        "operation": "product-plan",
        "compilerVersion": VERSION,
        "mode": str(product.get("mode", "")).upper(),
        "surface": str(product.get("surface", "")).upper(),
        "targets": product.get("targets", []),
        "release": str(product.get("release", "")).upper(),
        "frameworkTarget": selected_target,
        "experimentalProfiles": {
            "declarative": bool(isinstance(declarative, dict) and declarative.get("enabled")),
            "serviceWorker": bool(isinstance(worker, dict) and worker.get("enabled")),
        },
        "productSha256": contract.sha256_json(product),
        "toolsetSha256": contract.sha256_json(toolset),
        "validation": validation,
        "handlerReadiness": handler_check,
        "capabilities": capability_matrix(product, toolset),
        "requiredEvidenceGates": _release_gates(product),
        "maturity": {
            "documentWebMCP": "IMPLEMENTATION_TARGET",
            "declarative": "PROPOSAL" if isinstance(declarative, dict) and declarative.get("enabled") else "DISABLED",
            "serviceWorker": "PROPOSAL" if isinstance(worker, dict) and worker.get("enabled") else "DISABLED",
            "nativeHostEvidence": "NOT_RUN",
        },
    }


def compile_artifacts(
    product: Mapping[str, Any],
    toolset: Mapping[str, Any],
    plan: Mapping[str, Any],
    target: str,
) -> dict[str, str]:
    """Compile deterministic artifacts in memory after contract validation."""

    validation = plan.get("validation", {})
    if not isinstance(validation, dict) or validation.get("status") == "FAIL":
        raise ProductCompilerError("cannot compile artifacts from a failing product bundle")
    if target == "auto":
        inferred = plan.get("frameworkTarget")
        target = inferred if isinstance(inferred, str) and inferred in codegen.SUPPORTED_TARGETS else "vanilla-js"
    if target not in codegen.SUPPORTED_TARGETS:
        raise ProductCompilerError(
            f"unsupported target {target!r}; choose one of {', '.join(codegen.SUPPORTED_TARGETS)}"
        )
    toolset_hash = contract.sha256_json(toolset)
    adapter = codegen.generate_target(dict(toolset), toolset_hash, target)
    capability_document = {
        "schemaVersion": "webmcp-capability-map.v1",
        "productSha256": contract.sha256_json(product),
        "toolsetSha256": toolset_hash,
        "canonicalStateOwner": product.get("product", {}).get("state", {}).get("canonicalOwner"),
        "capabilities": capability_matrix(product, toolset),
    }
    compile_receipt = {
        "schemaVersion": "webmcp-compile-receipt.v1",
        "compilerVersion": VERSION,
        "status": plan.get("status"),
        "target": target,
        "productSha256": contract.sha256_json(product),
        "toolsetSha256": toolset_hash,
        "handlerReadiness": plan.get("handlerReadiness"),
        "nativeHostEvidence": "NOT_RUN",
        "artifacts": {
            "adapter": TARGET_FILENAMES[target],
            "capabilityMap": "webmcp-capabilities.json",
            "plan": "webmcp-build-plan.json",
        },
    }
    return {
        TARGET_FILENAMES[target]: adapter,
        "webmcp-capabilities.json": json.dumps(capability_document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        "webmcp-build-plan.json": json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        "webmcp-compile-receipt.json": json.dumps(compile_receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    }


def write_artifacts(
    artifacts: Mapping[str, str], output_dir: str | Path, force: bool = False
) -> list[dict[str, Any]]:
    """Atomically write compiled artifacts, refusing accidental replacement."""

    root = Path(output_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    destinations = [root / name for name in artifacts]
    existing = [path for path in destinations if path.exists()]
    if existing and not force:
        raise ProductCompilerError(
            "refusing to replace existing artifact(s): " + ", ".join(str(path) for path in existing)
        )
    receipts: list[dict[str, Any]] = []
    for name, content in artifacts.items():
        destination = root / name
        temporary = destination.with_name(destination.name + ".tmp-webmcp")
        temporary.write_text(content, encoding="utf-8", newline="\n")
        temporary.replace(destination)
        receipts.append({
            "path": str(destination),
            "bytes": destination.stat().st_size,
            "sha256": _sha256_text(content),
        })
    return receipts


def compile_product(
    product_path: str | Path,
    target: str = "auto",
    output_dir: str | Path | None = None,
    write: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    product, toolset, resolved_product, toolset_path, application_root = load_product_bundle(product_path)
    plan = build_plan(product, toolset, application_root, target)
    report: dict[str, Any] = {
        **plan,
        "operation": "compile-product",
        "productPath": str(resolved_product),
        "toolsetPath": str(toolset_path),
        "applicationRoot": str(application_root),
    }
    if plan["status"] == "FAIL":
        report["artifacts"] = []
        return report
    artifacts = compile_artifacts(product, toolset, plan, target)
    report["artifactPreview"] = [
        {"name": name, "bytes": len(content.encode("utf-8")), "sha256": _sha256_text(content)}
        for name, content in artifacts.items()
    ]
    if write:
        if output_dir is None:
            raise ProductCompilerError("--output-dir is required with --write")
        report["artifacts"] = write_artifacts(artifacts, output_dir, force)
        report["written"] = True
    else:
        report["artifacts"] = []
        report["written"] = False
    return report


def _emit(value: Mapping[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="webmcp-product",
        description="Validate, plan, and compile capability-mapped WebMCP products.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="validate product, toolset, and capability bindings")
    validate.add_argument("product")
    plan = sub.add_parser("plan", help="inspect capability and real-handler readiness without writing")
    plan.add_argument("product")
    plan.add_argument("--target", choices=("auto", *codegen.SUPPORTED_TARGETS), default="auto")
    compile_command = sub.add_parser("compile", help="compile deterministic WebMCP adapter artifacts")
    compile_command.add_argument("product")
    compile_command.add_argument("--target", choices=("auto", *codegen.SUPPORTED_TARGETS), default="auto")
    compile_command.add_argument("--output-dir")
    compile_command.add_argument("--write", action="store_true")
    compile_command.add_argument("--force", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        product, toolset, _, _, application_root = load_product_bundle(args.product)
        if args.command == "validate":
            report = contract.validate_bundle(product, toolset)
        elif args.command == "plan":
            report = build_plan(product, toolset, application_root, args.target)
        elif args.command == "compile":
            report = compile_product(
                args.product,
                target=args.target,
                output_dir=args.output_dir,
                write=args.write,
                force=args.force,
            )
        else:  # pragma: no cover
            raise ProductCompilerError(f"unsupported command: {args.command}")
        _emit(report)
        return 1 if report.get("status") in {"FAIL", "BLOCKED"} else 0
    except (ProductCompilerError, contract.ContractInputError, builder.BuilderError, codegen.CodegenError) as exc:
        _emit({"status": "FAIL", "error": str(exc)})
        return 2
    except KeyboardInterrupt:
        print("ERROR: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
