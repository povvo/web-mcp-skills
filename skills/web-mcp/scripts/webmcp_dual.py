#!/usr/bin/env python3
"""Validate a DUAL WebMCP/MCP operation map.

The map has one canonical operation and handler per job. Surface entries may
use different tool names and descriptions, but they cannot point at different
handlers. Runtime adapter tests remain responsible for proving that the named
handler exists and is the same function object on both surfaces.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


SCHEMA_VERSION = "webmcp-dual.v1"
OPERATION_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
HANDLER_RE = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")
TOOL_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")
EFFECTS = {
    "read",
    "local-write",
    "remote-write",
    "external-communication",
    "purchase",
    "permission-change",
    "destructive",
}
ROOT_FIELDS = {"schemaVersion", "application", "operations"}
APPLICATION_FIELDS = {"name"}
OPERATION_FIELDS = {
    "operationId",
    "handler",
    "effect",
    "inputSchema",
    "annotations",
    "surfaces",
}
SURFACE_FIELDS = {"toolName", "title", "description", "scope"}
SURFACES = {"webmcp": "page", "mcp": "service"}


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class DualContractError(Exception):
    """Raised when a contract file cannot be loaded."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _add(
    findings: list[Finding],
    severity: str,
    code: str,
    path: str,
    message: str,
) -> None:
    findings.append(Finding(severity, code, path, message))


def _unknown_fields(
    value: Any,
    allowed: set[str],
    path: str,
    findings: list[Finding],
) -> None:
    if not isinstance(value, dict):
        return
    for name in sorted(set(value) - allowed):
        _add(findings, "error", "unknown_field", f"{path}.{name}", "Unsupported field.")


def _nonblank_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_input_schema(
    schema: Any,
    path: str,
    findings: list[Finding],
) -> None:
    if not isinstance(schema, dict):
        _add(findings, "error", "input_schema.type", path, "inputSchema must be an object.")
        return
    if schema.get("type") != "object":
        _add(
            findings,
            "error",
            "input_schema.root",
            f"{path}.type",
            "A dual operation must have one object-root input contract shared by both adapters.",
        )
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        _add(
            findings,
            "error",
            "input_schema.properties",
            f"{path}.properties",
            "properties must be an object, including for an argument-free operation.",
        )
        properties = {}
    required = schema.get("required", [])
    if not isinstance(required, list) or any(not isinstance(item, str) for item in required):
        _add(
            findings,
            "error",
            "input_schema.required",
            f"{path}.required",
            "required must be an array of property names.",
        )
    else:
        for name in sorted(set(required) - set(properties)):
            _add(
                findings,
                "error",
                "input_schema.required_unknown",
                f"{path}.required",
                f"Required property {name!r} is not declared.",
            )
    if schema.get("additionalProperties") is not False:
        _add(
            findings,
            "error",
            "input_schema.open",
            f"{path}.additionalProperties",
            "Set additionalProperties to false so both surfaces receive the same bounded input.",
        )


def validate_dual_contract(document: Any) -> dict[str, Any]:
    findings: list[Finding] = []
    mappings: list[dict[str, Any]] = []
    if not isinstance(document, dict):
        _add(findings, "error", "root.type", "$", "Contract root must be an object.")
        document = {}
    _unknown_fields(document, ROOT_FIELDS, "$", findings)
    if document.get("schemaVersion") != SCHEMA_VERSION:
        _add(
            findings,
            "error",
            "schema_version",
            "$.schemaVersion",
            f"schemaVersion must be {SCHEMA_VERSION!r}.",
        )

    application = document.get("application")
    if not isinstance(application, dict):
        _add(findings, "error", "application.type", "$.application", "application must be an object.")
    else:
        _unknown_fields(application, APPLICATION_FIELDS, "$.application", findings)
        if not _nonblank_string(application.get("name")):
            _add(
                findings,
                "error",
                "application.name",
                "$.application.name",
                "application.name must be non-blank.",
            )

    operations = document.get("operations")
    if not isinstance(operations, list) or not operations:
        _add(
            findings,
            "error",
            "operations.type",
            "$.operations",
            "operations must be a non-empty array.",
        )
        operations = []

    operation_ids: dict[str, int] = {}
    handlers: dict[str, int] = {}
    tool_names: dict[str, dict[str, int]] = {surface: {} for surface in SURFACES}
    all_tool_names: dict[str, tuple[str, int]] = {}
    surface_counts = {"webmcp": 0, "mcp": 0, "shared": 0}

    for index, operation in enumerate(operations):
        path = f"$.operations[{index}]"
        if not isinstance(operation, dict):
            _add(findings, "error", "operation.type", path, "Operation must be an object.")
            continue
        _unknown_fields(operation, OPERATION_FIELDS, path, findings)

        operation_id = operation.get("operationId")
        if not isinstance(operation_id, str) or not OPERATION_ID_RE.fullmatch(operation_id):
            _add(
                findings,
                "error",
                "operation.id",
                f"{path}.operationId",
                "operationId must be a stable lowercase dotted, dashed, or underscored identifier.",
            )
            operation_id = f"invalid-{index}"
        elif operation_id in operation_ids:
            _add(
                findings,
                "error",
                "operation.id_duplicate",
                f"{path}.operationId",
                f"operationId is already used at index {operation_ids[operation_id]}.",
            )
        else:
            operation_ids[operation_id] = index

        handler = operation.get("handler")
        if not isinstance(handler, str) or not HANDLER_RE.fullmatch(handler):
            _add(
                findings,
                "error",
                "operation.handler",
                f"{path}.handler",
                "handler must be one JavaScript identifier shared by every mapped surface.",
            )
            handler = ""
        elif handler in handlers:
            _add(
                findings,
                "error",
                "operation.handler_duplicate",
                f"{path}.handler",
                f"Handler is already assigned to the operation at index {handlers[handler]}.",
            )
        else:
            handlers[handler] = index

        if operation.get("effect") not in EFFECTS:
            _add(
                findings,
                "error",
                "operation.effect",
                f"{path}.effect",
                f"effect must be one of {sorted(EFFECTS)}.",
            )
        _validate_input_schema(operation.get("inputSchema"), f"{path}.inputSchema", findings)

        annotations = operation.get("annotations")
        if not isinstance(annotations, dict):
            _add(
                findings,
                "error",
                "operation.annotations",
                f"{path}.annotations",
                "annotations must be an object.",
            )
        else:
            if set(annotations) != {"readOnlyHint", "untrustedContentHint"}:
                _add(
                    findings,
                    "error",
                    "operation.annotations_fields",
                    f"{path}.annotations",
                    "Declare exactly readOnlyHint and untrustedContentHint.",
                )
            for name in ("readOnlyHint", "untrustedContentHint"):
                if not isinstance(annotations.get(name), bool):
                    _add(
                        findings,
                        "error",
                        "operation.annotation_boolean",
                        f"{path}.annotations.{name}",
                        "Annotation must be boolean.",
                    )

        surfaces = operation.get("surfaces")
        mapped: dict[str, str | None] = {"webmcp": None, "mcp": None}
        if not isinstance(surfaces, dict) or not surfaces:
            _add(
                findings,
                "error",
                "operation.surfaces",
                f"{path}.surfaces",
                "Map the operation to WebMCP, MCP, or both.",
            )
            surfaces = {}
        else:
            for unknown in sorted(set(surfaces) - set(SURFACES)):
                _add(
                    findings,
                    "error",
                    "surface.unknown",
                    f"{path}.surfaces.{unknown}",
                    "Surface must be webmcp or mcp.",
                )

        for surface, expected_scope in SURFACES.items():
            surface_spec = surfaces.get(surface)
            if surface_spec is None:
                continue
            surface_counts[surface] += 1
            surface_path = f"{path}.surfaces.{surface}"
            if not isinstance(surface_spec, dict):
                _add(findings, "error", "surface.type", surface_path, "Surface mapping must be an object.")
                continue
            _unknown_fields(surface_spec, SURFACE_FIELDS, surface_path, findings)
            tool_name = surface_spec.get("toolName")
            if not isinstance(tool_name, str) or not TOOL_NAME_RE.fullmatch(tool_name):
                _add(
                    findings,
                    "error",
                    "surface.tool_name",
                    f"{surface_path}.toolName",
                    "toolName must be a valid 1-128 character tool identifier.",
                )
            else:
                mapped[surface] = tool_name
                if tool_name in tool_names[surface]:
                    _add(
                        findings,
                        "error",
                        "surface.tool_name_duplicate",
                        f"{surface_path}.toolName",
                        f"Tool name is already used on {surface} at index {tool_names[surface][tool_name]}.",
                    )
                else:
                    tool_names[surface][tool_name] = index
                if tool_name in all_tool_names:
                    previous_surface, previous_index = all_tool_names[tool_name]
                    _add(
                        findings,
                        "error",
                        "surface.tool_name_collision",
                        f"{surface_path}.toolName",
                        f"Tool name collides with {previous_surface} operation index {previous_index}; use surface-distinct names.",
                    )
                else:
                    all_tool_names[tool_name] = (surface, index)
            for name in ("title", "description"):
                if not _nonblank_string(surface_spec.get(name)):
                    _add(
                        findings,
                        "error",
                        f"surface.{name}",
                        f"{surface_path}.{name}",
                        f"{name} must be non-blank.",
                    )
            if surface_spec.get("scope") != expected_scope:
                _add(
                    findings,
                    "error",
                    "surface.scope",
                    f"{surface_path}.scope",
                    f"{surface} scope must be {expected_scope!r}.",
                )

        if mapped["webmcp"] and mapped["mcp"]:
            surface_counts["shared"] += 1
        mappings.append(
            {
                "operationId": operation_id,
                "handler": handler,
                "webmcpTool": mapped["webmcp"],
                "mcpTool": mapped["mcp"],
                "parity": "shared-handler" if mapped["webmcp"] and mapped["mcp"] else "surface-only",
            }
        )

    if surface_counts["webmcp"] == 0:
        _add(findings, "error", "dual.webmcp_missing", "$.operations", "At least one WebMCP mapping is required.")
    if surface_counts["mcp"] == 0:
        _add(findings, "error", "dual.mcp_missing", "$.operations", "At least one MCP mapping is required.")
    if surface_counts["shared"] == 0:
        _add(
            findings,
            "error",
            "dual.shared_operation_missing",
            "$.operations",
            "At least one operation must prove both adapters share one canonical handler.",
        )

    errors = sum(item.severity == "error" for item in findings)
    warnings = sum(item.severity == "warning" for item in findings)
    status = "FAIL" if errors else ("WARN" if warnings else "PASS")
    digest = hashlib.sha256(canonical_json(document).encode("utf-8")).hexdigest()
    return {
        "status": status,
        "schemaVersion": document.get("schemaVersion"),
        "contractSha256": digest,
        "summary": {
            "operations": len(operations),
            "webmcpTools": surface_counts["webmcp"],
            "mcpTools": surface_counts["mcp"],
            "sharedOperations": surface_counts["shared"],
            "errors": errors,
            "warnings": warnings,
        },
        "mappings": mappings,
        "findings": [item.to_dict() for item in findings],
    }


def validate_file(path: str | Path) -> dict[str, Any]:
    resolved = Path(path).expanduser().resolve()
    try:
        document = json.loads(resolved.read_text(encoding="utf-8"))
    except OSError as exc:
        raise DualContractError(f"cannot read contract {resolved}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise DualContractError(
            f"invalid JSON in {resolved} at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    return validate_dual_contract(document)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="webmcp-dual",
        description="Validate a DUAL WebMCP/MCP map with one canonical handler per operation.",
    )
    parser.add_argument("contract")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = validate_file(args.contract)
    except DualContractError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        summary = report["summary"]
        print(
            f"{report['status']}: {summary['operations']} operation(s), "
            f"{summary['webmcpTools']} WebMCP tool(s), {summary['mcpTools']} MCP tool(s), "
            f"{summary['sharedOperations']} shared operation(s)"
        )
        for finding in report["findings"]:
            print(f"- {finding['severity'].upper()} {finding['code']} {finding['path']}: {finding['message']}")
    return 1 if report["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
