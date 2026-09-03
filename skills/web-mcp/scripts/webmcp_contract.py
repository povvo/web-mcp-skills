#!/usr/bin/env python3
"""Authoritative structural and semantic contracts for the WebMCP skill.

Structural validation is owned by the bundled Draft 2020-12 schemas. Semantic
validation adds cross-field rules that JSON Schema cannot express cleanly. The
module is intentionally independent from the CLI and generators so callers can
adopt it without creating an import cycle.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlsplit

try:
    from jsonschema import Draft202012Validator, FormatChecker
    from jsonschema.exceptions import SchemaError
except ImportError as exc:  # pragma: no cover - exercised in dependency-free hosts.
    Draft202012Validator = None  # type: ignore[assignment,misc]
    FormatChecker = None  # type: ignore[assignment,misc]
    SchemaError = Exception  # type: ignore[assignment,misc]
    _JSONSCHEMA_IMPORT_ERROR: ImportError | None = exc
else:
    _JSONSCHEMA_IMPORT_ERROR = None


SCHEMA_DIR = Path(__file__).resolve().parent.parent / "assets" / "schemas"
CONTRACTS: dict[str, tuple[str, str]] = {
    "toolset": ("toolset.schema.json", "webmcp-toolset.v1"),
    "product": ("product.schema.json", "webmcp-product.v1"),
    "evidence": ("evidence.schema.json", "webmcp-evidence.v1"),
    "release": ("release.schema.json", "webmcp-release.v1"),
}

CONSEQUENTIAL_EFFECTS = {
    "external-communication",
    "purchase",
    "permission-change",
    "destructive",
}
MUTATING_EFFECTS = {
    "local-write",
    "remote-write",
    *CONSEQUENTIAL_EFFECTS,
}
UNTRUSTED_OUTPUT = {"external", "user-generated", "mixed"}
INJECTION_PATTERNS = (
    re.compile(r"\bignore\s+(?:all\s+|any\s+|the\s+)?previous\s+instructions?\b", re.I),
    re.compile(r"\b(?:system|developer)\s+(?:instruction|message|override)\b", re.I),
    re.compile(r"<\s*(?:system|developer|assistant|important)\b", re.I),
    re.compile(r"\breveal\b.*\b(?:system prompt|secret|credential|browsing history)\b", re.I),
)
HIGHLY_SENSITIVE_PATTERNS = {
    "password": re.compile(r"(?:^|_)(?:password|passcode|pin)(?:$|_)", re.I),
    "secret": re.compile(r"(?:^|_)(?:secret|credential|private_key)(?:$|_)", re.I),
    "api_key": re.compile(r"(?:^|_)(?:api_?key|access_?token|refresh_?token)(?:$|_)", re.I),
    "government_id": re.compile(r"(?:^|_)(?:ssn|social_?security|passport|national_?id)(?:$|_)", re.I),
    "payment_card": re.compile(r"(?:^|_)(?:credit_?card|card_?number|cvv|cvc)(?:$|_)", re.I),
}
CONTEXTUAL_SENSITIVE_PATTERNS = {
    "location": re.compile(r"(?:^|_)(?:precise_?location|location|latitude|longitude|address)(?:$|_)", re.I),
    "demographic": re.compile(r"(?:^|_)(?:age|birth_?date|date_?of_?birth|gender|race|ethnicity|religion)(?:$|_)", re.I),
    "financial": re.compile(r"(?:^|_)(?:income|salary|net_?worth)(?:$|_)", re.I),
    "cross_site_history": re.compile(r"(?:^|_)(?:browsing_?history|purchase_?history|previous_?purchases)(?:$|_)", re.I),
}


class ContractDependencyError(RuntimeError):
    """Raised when the pinned structural-validation dependency is unavailable."""


class ContractInputError(ValueError):
    """Raised when a requested contract or input document cannot be loaded."""


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    message: str
    remediation: str
    phase: str = "semantic"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def canonical_json(value: Any) -> str:
    """Return the canonical JSON representation used for candidate identity."""

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load_json(path: str | Path) -> dict[str, Any]:
    resolved = Path(path).expanduser().resolve()
    try:
        value = json.loads(resolved.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ContractInputError(f"cannot read JSON document {resolved}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ContractInputError(
            f"invalid JSON in {resolved} at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(value, dict):
        raise ContractInputError(f"contract document root must be an object: {resolved}")
    return value


def _require_jsonschema() -> None:
    if _JSONSCHEMA_IMPORT_ERROR is not None:
        raise ContractDependencyError(
            "webmcp_contract requires jsonschema==4.26.0; install "
            "skills/web-mcp/requirements.txt in the active Python environment"
        ) from _JSONSCHEMA_IMPORT_ERROR


@lru_cache(maxsize=None)
def load_schema(contract: str) -> dict[str, Any]:
    _require_jsonschema()
    if contract not in CONTRACTS:
        raise ContractInputError(
            f"unknown contract {contract!r}; choose one of {', '.join(sorted(CONTRACTS))}"
        )
    filename, _ = CONTRACTS[contract]
    schema = load_json(SCHEMA_DIR / filename)
    try:
        Draft202012Validator.check_schema(schema)  # type: ignore[union-attr]
    except SchemaError as exc:
        raise ContractInputError(f"bundled {contract} schema is invalid: {exc.message}") from exc
    return schema


def _escape_pointer_token(value: object) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


def json_pointer(parts: Iterable[object]) -> str:
    tokens = [_escape_pointer_token(part) for part in parts]
    return "$" if not tokens else "$/" + "/".join(tokens)


def _finding(
    findings: list[Finding],
    severity: str,
    code: str,
    path: str,
    message: str,
    remediation: str,
    phase: str = "semantic",
) -> None:
    findings.append(Finding(severity, code, path, message, remediation, phase))


def _schema_remediation(validator_name: str) -> str:
    return {
        "required": "Add the required field using the bundled example as the contract shape.",
        "additionalProperties": "Remove unsupported fields or move build metadata into a documented field.",
        "type": "Use the value type declared by the bundled schema.",
        "const": "Use the exact schema or profile version required by the bundled contract.",
        "enum": "Choose one of the values declared by the bundled schema.",
        "pattern": "Use a non-empty value that matches the declared identifier or text grammar.",
        "format": "Use a standards-conforming value for the declared format.",
        "maxLength": "Shorten the value to the declared maximum length.",
        "minLength": "Provide a non-empty value.",
        "minItems": "Add the minimum required entries.",
        "uniqueItems": "Remove duplicate entries.",
        "minimum": "Use a value at or above the declared minimum.",
        "maximum": "Use a value at or below the declared maximum.",
        "not": "Remove the field that is incompatible with the selected profile.",
    }.get(validator_name, "Make the document satisfy the bundled authoritative schema.")


def structural_findings(document: Mapping[str, Any], contract: str) -> list[Finding]:
    """Validate a document against exactly one bundled structural schema."""

    schema = load_schema(contract)
    validator = Draft202012Validator(  # type: ignore[misc,operator]
        schema,
        format_checker=FormatChecker(),  # type: ignore[operator]
    )
    findings: list[Finding] = []
    errors = sorted(
        validator.iter_errors(document),
        key=lambda item: (list(map(str, item.absolute_path)), item.validator, item.message),
    )
    for error in errors:
        validator_name = str(error.validator or "contract")
        _finding(
            findings,
            "error",
            f"schema.{validator_name}",
            json_pointer(error.absolute_path),
            error.message,
            _schema_remediation(validator_name),
            "structural",
        )
    return findings


def _normalized_field_name(name: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()


def _is_loopback(hostname: str | None) -> bool:
    if hostname is None:
        return False
    host = hostname.strip("[]").lower()
    return host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".localhost")


def _validate_exact_origin(origin: str, path: str, findings: list[Finding]) -> None:
    if "*" in origin:
        _finding(
            findings, "error", "origin.wildcard", path,
            "Wildcard origins are not allowed.",
            "List each trusted exact origin separately.",
        )
        return
    try:
        parsed = urlsplit(origin)
        _ = parsed.port
    except ValueError as exc:
        _finding(
            findings, "error", "origin.invalid", path,
            f"Origin cannot be parsed: {exc}.",
            "Use scheme, host, and optional port only.",
        )
        return
    if parsed.scheme not in {"https", "http"} or not parsed.hostname:
        _finding(
            findings, "error", "origin.invalid", path,
            "Origin must contain an HTTP(S) scheme and host.",
            "Use an exact HTTPS origin such as https://partner.example.",
        )
        return
    if parsed.username or parsed.password:
        _finding(
            findings, "error", "origin.credentials", path,
            "Origin must not contain user information.",
            "Remove credentials from the origin.",
        )
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        _finding(
            findings, "error", "origin.not_origin_only", path,
            "exposedTo accepts origins, not URLs with paths, queries, or fragments.",
            "Keep only scheme, host, and optional port.",
        )
    if parsed.scheme == "http":
        if _is_loopback(parsed.hostname):
            _finding(
                findings, "warning", "origin.loopback_http", path,
                "HTTP loopback is suitable only for local development.",
                "Use HTTPS in production manifests.",
            )
        else:
            _finding(
                findings, "error", "origin.insecure", path,
                "Non-loopback HTTP is not a trustworthy production origin.",
                "Use HTTPS.",
            )


def _validate_input_schema(
    schema: Mapping[str, Any],
    tool_path: str,
    findings: list[Finding],
) -> None:
    try:
        Draft202012Validator.check_schema(schema)  # type: ignore[union-attr]
    except SchemaError as exc:
        _finding(
            findings, "error", "input_schema.invalid", f"{tool_path}/inputSchema",
            f"inputSchema is not a valid Draft 2020-12 schema: {exc.message}",
            "Repair the JSON Schema before generating or registering the tool.",
        )
        return

    properties = schema.get("properties", {})
    required = schema.get("required", [])
    if isinstance(properties, dict) and isinstance(required, list):
        for name in sorted(set(required) - set(properties)):
            _finding(
                findings, "error", "input_schema.required_unknown",
                f"{tool_path}/inputSchema/required",
                f"Required property {name!r} is absent from properties.",
                "Define the property or remove it from required.",
            )
        for name, prop in sorted(properties.items()):
            if not isinstance(prop, dict):
                continue
            prop_path = f"{tool_path}/inputSchema/properties/{_escape_pointer_token(name)}"
            description = prop.get("description")
            if not isinstance(description, str) or not description.strip():
                _finding(
                    findings, "warning", "input_schema.description_missing", prop_path,
                    "Input property has no factual description.",
                    "Describe the value, units, and format without adding agent instructions.",
                )
            if prop.get("type") == "string" and "enum" not in prop and "const" not in prop:
                if "maxLength" not in prop:
                    _finding(
                        findings, "warning", "input_schema.string_unbounded", prop_path,
                        "Free-text string has no maximum length.",
                        "Add a task-appropriate maxLength and enforce it in the handler.",
                    )
            if prop.get("type") == "array":
                if "items" not in prop:
                    _finding(
                        findings, "error", "input_schema.array_items_missing", prop_path,
                        "Array input has no items contract.",
                        "Define the allowed item schema.",
                    )
                if "maxItems" not in prop:
                    _finding(
                        findings, "warning", "input_schema.array_unbounded", prop_path,
                        "Array input has no maximum item count.",
                        "Add a task-appropriate maxItems and enforce it in the handler.",
                    )


def _toolset_semantics(document: Mapping[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    tools = document.get("tools", [])
    if not isinstance(tools, list):
        return findings

    if len(tools) > 30:
        _finding(
            findings, "warning", "toolset.large", "$/tools",
            f"Toolset contains {len(tools)} tools.",
            "Partition by page state or domain and run selection evaluations.",
        )

    names: dict[str, list[int]] = {}
    handlers: dict[str, list[tuple[int, str]]] = {}
    for index, tool in enumerate(tools):
        if not isinstance(tool, dict):
            continue
        path = f"$/tools/{index}"
        name = tool.get("name")
        handler = tool.get("handler")
        semantics = tool.get("semantics", {})
        annotations = tool.get("annotations", {})
        registration = tool.get("registration", {})
        input_schema = tool.get("inputSchema", {})
        if isinstance(name, str):
            names.setdefault(name, []).append(index)
        effect = semantics.get("effect") if isinstance(semantics, dict) else None
        if isinstance(handler, str):
            handlers.setdefault(handler, []).append((index, str(effect)))

        description = tool.get("description", "")
        if isinstance(description, str) and any(p.search(description) for p in INJECTION_PATTERNS):
            _finding(
                findings, "error", "metadata.instruction_like", f"{path}/description",
                "Tool description contains instruction-like or exfiltration language.",
                "Replace it with a factual capability description and review its source.",
            )

        if isinstance(input_schema, dict):
            _validate_input_schema(input_schema, path, findings)

        read_hint = annotations.get("readOnlyHint") if isinstance(annotations, dict) else None
        untrusted_hint = annotations.get("untrustedContentHint") if isinstance(annotations, dict) else None
        output_trust = semantics.get("outputTrust") if isinstance(semantics, dict) else None
        confirmation = semantics.get("confirmation") if isinstance(semantics, dict) else None
        idempotency = semantics.get("idempotency") if isinstance(semantics, dict) else None
        preconditions = semantics.get("preconditions") if isinstance(semantics, dict) else None

        if effect == "read" and read_hint is False:
            _finding(
                findings, "warning", "annotations.read_only_conservative",
                f"{path}/annotations/readOnlyHint",
                "A declared read effect does not advertise readOnlyHint.",
                "Set it true only after proving the complete handler path is read-only.",
            )
        if effect in MUTATING_EFFECTS and read_hint is True:
            _finding(
                findings, "error", "annotations.read_only_mismatch",
                f"{path}/annotations/readOnlyHint",
                f"readOnlyHint is true but the declared effect is {effect}.",
                "Set the hint false and describe the mutation explicitly.",
            )
        if output_trust in UNTRUSTED_OUTPUT and untrusted_hint is not True:
            _finding(
                findings, "error", "annotations.untrusted_missing",
                f"{path}/annotations/untrustedContentHint",
                f"{output_trust} output requires untrustedContentHint.",
                "Set the hint true and preserve provenance/data-instruction boundaries.",
            )
        if effect in CONSEQUENTIAL_EFFECTS and confirmation == "none":
            _finding(
                findings, "error", "semantics.confirmation_required",
                f"{path}/semantics/confirmation",
                f"{effect} is consequential but confirmation is none.",
                "Require confirmation bound to the exact current operation.",
            )
        if effect == "remote-write" and confirmation == "none":
            _finding(
                findings, "warning", "semantics.remote_write_unconfirmed",
                f"{path}/semantics/confirmation",
                "Durable remote write has no declared confirmation requirement.",
                "Verify explicit intent is sufficient or require site-native confirmation.",
            )
        if effect in CONSEQUENTIAL_EFFECTS and idempotency == "none":
            _finding(
                findings, "warning", "semantics.consequential_non_idempotent",
                f"{path}/semantics/idempotency",
                "Consequential action has no idempotency protection.",
                "Use natural/keyed idempotency or define uncertain-outcome recovery.",
            )
        if effect in CONSEQUENTIAL_EFFECTS and not preconditions:
            _finding(
                findings, "error", "semantics.preconditions_missing",
                f"{path}/semantics/preconditions",
                "Consequential action has no declared preconditions.",
                "Declare authorization, current-state, and confirmation preconditions.",
            )

        if isinstance(registration, dict):
            lifetime = registration.get("lifetime")
            owner = registration.get("owner")
            if lifetime != "document" and (not isinstance(owner, str) or not owner.strip()):
                _finding(
                    findings, "warning", "registration.owner_missing",
                    f"{path}/registration/owner",
                    "State-dependent registration has no named owner.",
                    "Name the route, selection, mode, permission, or component that aborts it.",
                )
            exposed = registration.get("exposedTo", [])
            if isinstance(exposed, list):
                for origin_index, origin in enumerate(exposed):
                    if isinstance(origin, str):
                        _validate_exact_origin(
                            origin,
                            f"{path}/registration/exposedTo/{origin_index}",
                            findings,
                        )

        properties = input_schema.get("properties", {}) if isinstance(input_schema, dict) else {}
        property_names = set(properties) if isinstance(properties, dict) else set()
        sensitive = semantics.get("sensitiveInputs", []) if isinstance(semantics, dict) else []
        declared: dict[str, int] = {}
        if isinstance(sensitive, list):
            for sensitive_index, item in enumerate(sensitive):
                if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                    continue
                sensitive_name = item["name"]
                sensitive_path = f"{path}/semantics/sensitiveInputs/{sensitive_index}/name"
                if sensitive_name in declared:
                    _finding(
                        findings, "error", "sensitive.duplicate", sensitive_path,
                        f"Sensitive input {sensitive_name!r} is declared more than once.",
                        "Keep one declaration with a precise purpose.",
                    )
                if sensitive_name not in property_names:
                    _finding(
                        findings, "error", "sensitive.unknown", sensitive_path,
                        f"Sensitive input {sensitive_name!r} is absent from inputSchema.properties.",
                        "Correct the field name or remove the declaration.",
                    )
                declared[sensitive_name] = sensitive_index

        for property_name in sorted(property_names):
            normalized = _normalized_field_name(str(property_name))
            strong = next(
                (label for label, pattern in HIGHLY_SENSITIVE_PATTERNS.items() if pattern.search(normalized)),
                None,
            )
            contextual = next(
                (label for label, pattern in CONTEXTUAL_SENSITIVE_PATTERNS.items() if pattern.search(normalized)),
                None,
            )
            property_path = f"{path}/inputSchema/properties/{_escape_pointer_token(property_name)}"
            if strong and property_name not in declared:
                _finding(
                    findings, "error", "sensitive.highly_sensitive_undeclared", property_path,
                    f"Property resembles highly sensitive {strong} data but is not declared.",
                    "Remove it unless essential; otherwise declare its exact purpose.",
                )
            elif contextual and property_name not in declared:
                _finding(
                    findings, "warning", "sensitive.contextual_undeclared", property_path,
                    f"Property resembles sensitive {contextual} data but is not declared.",
                    "Remove it unless required, or declare its exact purpose.",
                )

    for name, indexes in sorted(names.items()):
        if len(indexes) > 1:
            _finding(
                findings, "error", "tool.duplicate_name", "$/tools",
                f"Tool name {name!r} is repeated at indexes {indexes}.",
                "Give every registration a unique, semantically distinct name.",
            )
    for handler, mapped in sorted(handlers.items()):
        effects = {effect for _, effect in mapped}
        if len(mapped) > 1 and len(effects) > 1:
            _finding(
                findings, "warning", "tool.handler_effect_alias", "$/tools",
                f"Handler {handler!r} is used by tools with different effects: {sorted(effects)}.",
                "Prove the handler cannot hide a stronger effect behind a weaker contract.",
            )
    return findings


def _product_semantics(document: Mapping[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    targets = set(document.get("targets", [])) if isinstance(document.get("targets"), list) else set()
    profiles = document.get("profiles", {})
    document_profile = profiles.get("document", {}) if isinstance(profiles, dict) else {}
    document_enabled = document_profile.get("enabled") is True if isinstance(document_profile, dict) else False
    if targets.intersection({"webmcp-document", "chatgpt-site-tools", "chromium-webmcp"}) and not document_enabled:
        _finding(
            findings, "error", "product.document_disabled", "$/profiles/document/enabled",
            "A document WebMCP target is selected while the document profile is disabled.",
            "Enable the document profile or remove the document-based target.",
        )
    if document.get("release") == "challenge":
        if not document_enabled:
            _finding(
                findings, "error", "product.challenge_document_required", "$/profiles/document/enabled",
                "Challenge release requires genuine document WebMCP.",
                "Enable the document profile and implement registerTool integration.",
            )
        if not targets.intersection({"chatgpt-site-tools", "chromium-webmcp"}):
            _finding(
                findings, "error", "product.challenge_host_required", "$/targets",
                "Challenge release has no supported live browser target.",
                "Add chatgpt-site-tools or chromium-webmcp.",
            )

    declarative = profiles.get("declarativeProposal", {}) if isinstance(profiles, dict) else {}
    if isinstance(declarative, dict) and declarative.get("enabled") is True and "chatgpt-site-tools" in targets:
        _finding(
            findings, "warning", "product.declarative_not_site_tools",
            "$/profiles/declarativeProposal/enabled",
            "The declarative proposal is not evidence for the current ChatGPT Site Tools profile.",
            "Keep top-level imperative document tools as the Site Tools implementation.",
        )

    worker = profiles.get("serviceWorkerProposal", {}) if isinstance(profiles, dict) else {}
    if isinstance(worker, dict) and worker.get("enabled") is True:
        state_model = worker.get("stateModel")
        session_strategy = worker.get("sessionStrategy")
        if state_model == "session-required" and session_strategy == "unresolved":
            _finding(
                findings, "error", "product.service_worker_session_unresolved",
                "$/profiles/serviceWorkerProposal/sessionStrategy",
                "Session-dependent Service Worker tools have no implementable session strategy.",
                "Define an application/host session strategy or keep the proposal disabled.",
            )
        if state_model != "session-required" and session_strategy == "host-session-id":
            _finding(
                findings, "warning", "product.service_worker_session_unused",
                "$/profiles/serviceWorkerProposal/sessionStrategy",
                "A host session ID is selected for a toolset that does not declare session-required state.",
                "Use not-required/application-defined or change the state model.",
            )

    surface = document.get("surface")
    capabilities = document.get("capabilities", [])
    capability_ids: dict[str, int] = {}
    operation_ids: dict[str, int] = {}
    webmcp_names: dict[str, int] = {}
    mcp_names: dict[str, int] = {}
    declared_operations: set[str] = set()
    product = document.get("product", {})
    if isinstance(product, dict):
        workflow = product.get("humanWorkflow", {})
        if isinstance(workflow, dict) and isinstance(workflow.get("operations"), list):
            declared_operations = {
                item for item in workflow["operations"] if isinstance(item, str)
            }

    if isinstance(capabilities, list):
        for index, capability in enumerate(capabilities):
            if not isinstance(capability, dict):
                continue
            path = f"$/capabilities/{index}"
            capability_id = capability.get("id")
            operation = capability.get("operation", {})
            webmcp = capability.get("webmcpTool", {})
            mcp = capability.get("mcpTool")
            state = capability.get("state", {})
            concurrency = capability.get("concurrency", {})

            if isinstance(capability_id, str):
                if capability_id in capability_ids:
                    _finding(
                        findings, "error", "product.capability_duplicate", f"{path}/id",
                        f"Capability {capability_id!r} is already declared at index {capability_ids[capability_id]}.",
                        "Give every user capability one stable identifier.",
                    )
                capability_ids[capability_id] = index

            if isinstance(operation, dict):
                operation_id = operation.get("id")
                effect = operation.get("effect")
                if isinstance(operation_id, str):
                    if operation_id in operation_ids:
                        _finding(
                            findings, "error", "product.operation_duplicate", f"{path}/operation/id",
                            f"Operation {operation_id!r} is already bound at index {operation_ids[operation_id]}.",
                            "Map each canonical operation once and let adapters call that mapping.",
                        )
                    operation_ids[operation_id] = index
                    if declared_operations and operation_id not in declared_operations:
                        _finding(
                            findings, "error", "product.operation_not_human_workflow",
                            f"{path}/operation/id",
                            f"Operation {operation_id!r} is not listed in product.humanWorkflow.operations.",
                            "Add the human operation to the workflow or remove the orphan adapter capability.",
                        )
                writes = state.get("writes", []) if isinstance(state, dict) else []
                if effect == "read" and isinstance(writes, list) and writes:
                    _finding(
                        findings, "error", "product.read_operation_writes", f"{path}/state/writes",
                        "A read operation declares canonical state writes.",
                        "Correct the effect or remove the state writes.",
                    )

            if isinstance(webmcp, dict) and isinstance(webmcp.get("name"), str):
                name = webmcp["name"]
                if name in webmcp_names:
                    _finding(
                        findings, "error", "product.webmcp_tool_duplicate", f"{path}/webmcpTool/name",
                        f"WebMCP tool {name!r} is already mapped at index {webmcp_names[name]}.",
                        "Map each registered tool to exactly one capability.",
                    )
                webmcp_names[name] = index

            if surface != "dual" and isinstance(mcp, dict):
                _finding(
                    findings, "error", "product.webmcp_only_has_mcp_mapping", f"{path}/mcpTool",
                    "A WebMCP-only product declares an MCP adapter mapping.",
                    "Select the dual surface or remove the MCP mapping.",
                )
            if isinstance(mcp, dict) and isinstance(mcp.get("name"), str):
                name = mcp["name"]
                if name in mcp_names:
                    _finding(
                        findings, "error", "product.mcp_tool_duplicate", f"{path}/mcpTool/name",
                        f"MCP tool {name!r} is already mapped at index {mcp_names[name]}.",
                        "Map each MCP tool name to one canonical capability.",
                    )
                mcp_names[name] = index

    missing_operations = declared_operations.difference(operation_ids)
    for operation_id in sorted(missing_operations):
        _finding(
            findings, "error", "product.human_operation_unmapped",
            "$/product/humanWorkflow/operations",
            f"Human operation {operation_id!r} has no WebMCP capability mapping.",
            "Add a capability that maps the human operation to a real handler and WebMCP tool.",
        )
    if surface == "dual" and not mcp_names:
        _finding(
            findings, "error", "product.dual_shared_operation_required", "$/capabilities",
            "Dual surface product has no capability mapped to both WebMCP and MCP.",
            "Map at least one independently useful canonical operation to an MCP adapter.",
        )
    return findings


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _expected_evidence_status(gates: Sequence[Mapping[str, Any]]) -> str:
    required = [gate for gate in gates if gate.get("required") is True]
    statuses = {gate.get("status") for gate in required}
    if "FAIL" in statuses:
        return "FAIL"
    if "BLOCKED" in statuses:
        return "BLOCKED"
    if "NOT_RUN" in statuses:
        return "NOT_RUN"
    if "UNSUPPORTED" in statuses:
        return "UNSUPPORTED"
    return "PASS"


def _evidence_semantics(document: Mapping[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    gates = document.get("gates", [])
    if not isinstance(gates, list):
        return findings
    gate_ids: dict[str, int] = {}
    actual_counts = {
        status: 0
        for status in ("PASS", "FAIL", "BLOCKED", "UNSUPPORTED", "NOT_RUN")
    }
    valid_gates: list[Mapping[str, Any]] = []
    for index, gate in enumerate(gates):
        if not isinstance(gate, dict):
            continue
        valid_gates.append(gate)
        path = f"$/gates/{index}"
        gate_id = gate.get("id")
        status = gate.get("status")
        evidence = gate.get("evidence")
        reason = gate.get("reason")
        if isinstance(gate_id, str):
            if gate_id in gate_ids:
                _finding(
                    findings, "error", "evidence.duplicate_gate", f"{path}/id",
                    f"Gate ID {gate_id!r} is already used at index {gate_ids[gate_id]}.",
                    "Use one stable, unique ID per executed gate.",
                )
            gate_ids[gate_id] = index
        if status in actual_counts:
            actual_counts[str(status)] += 1
        if status == "PASS" and not evidence:
            _finding(
                findings, "error", "evidence.pass_without_receipt", f"{path}/evidence",
                "A passing gate has no evidence item.",
                "Attach a command, file, log, screenshot, or host receipt.",
            )
        if status in {"FAIL", "BLOCKED", "UNSUPPORTED", "NOT_RUN"} and not (
            isinstance(reason, str) and reason.strip()
        ):
            _finding(
                findings, "error", "evidence.reason_required", f"{path}/reason",
                f"{status} gate has no reason.",
                "Record the observed failure or exact unavailable prerequisite.",
            )
        if status == "PASS" and isinstance(gate.get("exitCode"), int) and gate["exitCode"] != 0:
            _finding(
                findings, "error", "evidence.pass_nonzero_exit", f"{path}/exitCode",
                "A passing gate records a non-zero exit code.",
                "Correct the status or attach the successful command execution.",
            )
        started = _parse_datetime(gate.get("startedAt"))
        ended = _parse_datetime(gate.get("endedAt"))
        if started is not None and ended is not None and ended < started:
            _finding(
                findings, "error", "evidence.time_order", f"{path}/endedAt",
                "Gate endedAt precedes startedAt.",
                "Record the actual ordered timestamps.",
            )

    summary = document.get("summary", {})
    if isinstance(summary, dict):
        counts = summary.get("counts", {})
        if isinstance(counts, dict) and counts != actual_counts:
            _finding(
                findings, "error", "evidence.count_mismatch", "$/summary/counts",
                f"Summary counts {counts} do not match gates {actual_counts}.",
                "Recompute counts directly from the gate records.",
            )
        expected_status = _expected_evidence_status(valid_gates)
        if summary.get("status") != expected_status:
            _finding(
                findings, "error", "evidence.status_mismatch", "$/summary/status",
                f"Summary status must be {expected_status} for the required gate results.",
                "Aggregate required gates using FAIL, BLOCKED, NOT_RUN, UNSUPPORTED, then PASS precedence.",
            )
    return findings


def _release_semantics(document: Mapping[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    claims = document.get("claims", [])
    claim_ids: dict[str, int] = {}
    if isinstance(claims, list):
        for index, claim in enumerate(claims):
            if not isinstance(claim, dict) or not isinstance(claim.get("id"), str):
                continue
            claim_id = claim["id"]
            if claim_id in claim_ids:
                _finding(
                    findings, "error", "release.duplicate_claim", f"$/claims/{index}/id",
                    f"Claim ID {claim_id!r} is already used at index {claim_ids[claim_id]}.",
                    "Use a unique stable ID for every release claim.",
                )
            claim_ids[claim_id] = index

    compatibility = document.get("compatibility", [])
    targets: dict[str, int] = {}
    if isinstance(compatibility, list):
        for index, item in enumerate(compatibility):
            if not isinstance(item, dict) or not isinstance(item.get("target"), str):
                continue
            target = item["target"]
            if target in targets:
                _finding(
                    findings, "error", "release.duplicate_target",
                    f"$/compatibility/{index}/target",
                    f"Compatibility target {target!r} is already declared at index {targets[target]}.",
                    "Keep one evidence-backed compatibility result per target.",
                )
            targets[target] = index
            if item.get("status") == "PASS" and not item.get("evidenceGateIds"):
                _finding(
                    findings, "error", "release.pass_without_gate",
                    f"$/compatibility/{index}/evidenceGateIds",
                    "Passing compatibility claim has no evidence gate.",
                    "Reference the native or deterministic gate that established support.",
                )
    return findings


SEMANTIC_VALIDATORS = {
    "toolset": _toolset_semantics,
    "product": _product_semantics,
    "evidence": _evidence_semantics,
    "release": _release_semantics,
}


def _sort_findings(findings: Iterable[Finding]) -> list[Finding]:
    severity_order = {"error": 0, "warning": 1}
    phase_order = {"structural": 0, "semantic": 1, "bundle": 2}
    return sorted(
        findings,
        key=lambda item: (
            severity_order.get(item.severity, 9),
            phase_order.get(item.phase, 9),
            item.path,
            item.code,
            item.message,
        ),
    )


def _status(findings: Sequence[Finding]) -> str:
    if any(item.severity == "error" for item in findings):
        return "FAIL"
    if any(item.severity == "warning" for item in findings):
        return "WARN"
    return "PASS"


def validate_contract(document: Mapping[str, Any], contract: str) -> dict[str, Any]:
    """Validate one in-memory contract document and return stable JSON data."""

    if contract not in CONTRACTS:
        raise ContractInputError(
            f"unknown contract {contract!r}; choose one of {', '.join(sorted(CONTRACTS))}"
        )
    structure = structural_findings(document, contract)
    semantics: list[Finding] = []
    if not structure:
        semantics = SEMANTIC_VALIDATORS[contract](document)
    findings = _sort_findings([*structure, *semantics])
    errors = sum(item.severity == "error" for item in findings)
    warnings = sum(item.severity == "warning" for item in findings)
    schema = load_schema(contract)
    return {
        "status": _status(findings),
        "contract": contract,
        "schemaVersion": document.get("schemaVersion"),
        "schemaId": schema.get("$id"),
        "schemaSha256": sha256_json(schema),
        "documentSha256": sha256_json(document),
        "structuralStatus": "FAIL" if structure else "PASS",
        "semanticStatus": "NOT_RUN" if structure else _status(semantics),
        "summary": {
            "errors": errors,
            "warnings": warnings,
            "findings": len(findings),
        },
        "findings": [item.to_dict() for item in findings],
    }


def validate_file(path: str | Path, contract: str) -> dict[str, Any]:
    report = validate_contract(load_json(path), contract)
    report["source"] = str(Path(path).expanduser().resolve())
    return report


def bundle_findings(
    product: Mapping[str, Any],
    toolset: Mapping[str, Any],
    evidence: Mapping[str, Any] | None = None,
    release: Mapping[str, Any] | None = None,
) -> list[Finding]:
    """Check references that cross otherwise independent contract documents."""

    findings: list[Finding] = []
    tool_by_name = {
        tool.get("name"): tool
        for tool in toolset.get("tools", [])
        if isinstance(tool, dict) and isinstance(tool.get("name"), str)
    }
    mapped_tool_names: set[str] = set()
    capabilities = product.get("capabilities", [])
    if isinstance(capabilities, list):
        for index, capability in enumerate(capabilities):
            if not isinstance(capability, dict):
                continue
            operation = capability.get("operation", {})
            webmcp = capability.get("webmcpTool", {})
            ui = capability.get("ui", {})
            if not isinstance(operation, dict) or not isinstance(webmcp, dict):
                continue
            name = webmcp.get("name")
            path = f"$/product/capabilities/{index}/webmcpTool/name"
            if not isinstance(name, str):
                continue
            mapped_tool_names.add(name)
            tool = tool_by_name.get(name)
            if tool is None:
                _finding(
                    findings, "error", "bundle.capability_tool_unknown", path,
                    f"Capability selects unknown WebMCP tool {name!r}.",
                    "Select a tool name present in the referenced toolset.", "bundle",
                )
                continue
            if operation.get("handler") != tool.get("handler"):
                _finding(
                    findings, "error", "bundle.capability_handler_mismatch",
                    f"$/product/capabilities/{index}/operation/handler",
                    f"Capability handler {operation.get('handler')!r} does not match toolset handler {tool.get('handler')!r}.",
                    "Bind WebMCP and product capability to the same canonical operation handler.", "bundle",
                )
            semantics = tool.get("semantics", {})
            if isinstance(semantics, dict) and operation.get("effect") != semantics.get("effect"):
                _finding(
                    findings, "error", "bundle.capability_effect_mismatch",
                    f"$/product/capabilities/{index}/operation/effect",
                    f"Capability effect {operation.get('effect')!r} does not match toolset effect {semantics.get('effect')!r}.",
                    "Use one accurate effect classification across product and toolset contracts.", "bundle",
                )
            if isinstance(semantics, dict) and isinstance(ui, dict):
                declared_effect = str(ui.get("visibleEffect", "")).strip().rstrip(".")
                tool_effect = str(semantics.get("visibleEffect", "")).strip().rstrip(".")
                if declared_effect and tool_effect and declared_effect != tool_effect:
                    _finding(
                        findings, "warning", "bundle.visible_effect_diverges",
                        f"$/product/capabilities/{index}/ui/visibleEffect",
                        "Product and toolset describe the visible effect differently.",
                        "Use one precise visible-effect statement or prove why the descriptions differ.", "bundle",
                    )
            concurrency = capability.get("concurrency", {})
            if isinstance(concurrency, dict) and concurrency.get("strategy") == "revision":
                expected = concurrency.get("expectedRevisionField")
                input_schema = tool.get("inputSchema", {}) if isinstance(tool, dict) else {}
                properties = input_schema.get("properties", {}) if isinstance(input_schema, dict) else {}
                if isinstance(expected, str) and (
                    not isinstance(properties, dict) or expected not in properties
                ):
                    _finding(
                        findings, "error", "bundle.revision_input_missing",
                        f"$/product/capabilities/{index}/concurrency/expectedRevisionField",
                        f"Revision strategy expects input field {expected!r}, but the tool schema does not declare it.",
                        "Add the expected revision to the tool input schema or select the actual concurrency strategy.",
                        "bundle",
                    )

    for name in sorted(set(tool_by_name).difference(mapped_tool_names)):
        _finding(
            findings, "error", "bundle.tool_unmapped", "$/toolset/tools",
            f"Toolset tool {name!r} is not mapped to a product capability.",
            "Add a capability binding the human workflow, operation, state, UI, and tool.", "bundle",
        )
    profiles = product.get("profiles", {})
    worker = profiles.get("serviceWorkerProposal", {}) if isinstance(profiles, dict) else {}
    if isinstance(worker, dict) and worker.get("enabled") is True:
        for index, name in enumerate(worker.get("toolNames", [])):
            path = f"$/product/profiles/serviceWorkerProposal/toolNames/{index}"
            if name not in tool_by_name:
                _finding(
                    findings, "error", "bundle.service_worker_tool_unknown", path,
                    f"Service Worker proposal selects unknown tool {name!r}.",
                    "Select a name from the referenced toolset.", "bundle",
                )
                continue
            registration = tool_by_name[name].get("registration", {})
            lifetime = registration.get("lifetime") if isinstance(registration, dict) else None
            if lifetime != "document":
                _finding(
                    findings, "error", "bundle.service_worker_page_state_tool", path,
                    f"Tool {name!r} has {lifetime!r} page-state lifetime and is not background-safe.",
                    "Create a background-safe operation contract or remove it from the proposal profile.",
                    "bundle",
                )

    if release is not None and evidence is not None:
        gates = {
            gate.get("id"): gate
            for gate in evidence.get("gates", [])
            if isinstance(gate, dict) and isinstance(gate.get("id"), str)
        }
        for claim_index, claim in enumerate(release.get("claims", [])):
            if not isinstance(claim, dict):
                continue
            for gate_index, gate_id in enumerate(claim.get("evidenceGateIds", [])):
                path = f"$/release/claims/{claim_index}/evidenceGateIds/{gate_index}"
                gate = gates.get(gate_id)
                if gate is None:
                    _finding(
                        findings, "error", "bundle.claim_gate_unknown", path,
                        f"Claim references unknown evidence gate {gate_id!r}.",
                        "Reference an ID present in the evidence report.", "bundle",
                    )
                elif gate.get("status") != "PASS":
                    _finding(
                        findings, "error", "bundle.claim_gate_not_passed", path,
                        f"Claim relies on gate {gate_id!r} with status {gate.get('status')!r}.",
                        "Limit the claim or produce passing executed evidence.", "bundle",
                    )
        for target_index, item in enumerate(release.get("compatibility", [])):
            if not isinstance(item, dict):
                continue
            declared_status = item.get("status")
            referenced = [gates.get(gate_id) for gate_id in item.get("evidenceGateIds", [])]
            if any(gate is None for gate in referenced):
                _finding(
                    findings, "error", "bundle.compatibility_gate_unknown",
                    f"$/release/compatibility/{target_index}/evidenceGateIds",
                    "Compatibility statement references an unknown evidence gate.",
                    "Reference only IDs present in the evidence report.", "bundle",
                )
            elif declared_status == "PASS" and any(
                gate.get("status") != "PASS" for gate in referenced if gate is not None
            ):
                _finding(
                    findings, "error", "bundle.compatibility_not_passed",
                    f"$/release/compatibility/{target_index}/status",
                    "Passing compatibility statement includes a non-passing gate.",
                    "Correct the status or produce passing native evidence.", "bundle",
                )

        candidate = evidence.get("candidate", {})
        if isinstance(candidate, dict):
            if candidate.get("productSha256") != sha256_json(product):
                _finding(
                    findings, "error", "bundle.product_hash_mismatch", "$/evidence/candidate/productSha256",
                    "Evidence product hash does not identify the supplied product profile.",
                    "Regenerate evidence for the exact product profile.", "bundle",
                )
            if candidate.get("toolsetSha256") != sha256_json(toolset):
                _finding(
                    findings, "error", "bundle.toolset_hash_mismatch", "$/evidence/candidate/toolsetSha256",
                    "Evidence toolset hash does not identify the supplied toolset.",
                    "Regenerate evidence for the exact toolset.", "bundle",
                )
    return _sort_findings(findings)


def validate_bundle(
    product: Mapping[str, Any],
    toolset: Mapping[str, Any],
    evidence: Mapping[str, Any] | None = None,
    release: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate all supplied documents, then their cross-document bindings."""

    reports = {
        "product": validate_contract(product, "product"),
        "toolset": validate_contract(toolset, "toolset"),
    }
    if evidence is not None:
        reports["evidence"] = validate_contract(evidence, "evidence")
    if release is not None:
        reports["release"] = validate_contract(release, "release")

    can_check_bundle = all(report["status"] != "FAIL" for report in reports.values())
    cross = bundle_findings(product, toolset, evidence, release) if can_check_bundle else []
    status = "FAIL" if any(report["status"] == "FAIL" for report in reports.values()) else _status(cross)
    if status == "PASS" and any(report["status"] == "WARN" for report in reports.values()):
        status = "WARN"
    return {
        "status": status,
        "reports": reports,
        "bundleFindings": [item.to_dict() for item in cross],
        "summary": {
            "documents": len(reports),
            "bundleErrors": sum(item.severity == "error" for item in cross),
            "bundleWarnings": sum(item.severity == "warning" for item in cross),
        },
    }


__all__ = [
    "CONTRACTS",
    "ContractDependencyError",
    "ContractInputError",
    "Finding",
    "bundle_findings",
    "canonical_json",
    "json_pointer",
    "load_json",
    "load_schema",
    "sha256_json",
    "structural_findings",
    "validate_bundle",
    "validate_contract",
    "validate_file",
]
