#!/usr/bin/env python3
"""Create, extend, inspect, validate, generate, and verify WebMCP products.

The manifest contains build-time semantics that are deliberately not registered
with the browser. Generated JavaScript wires current WebMCP registration to
real application handlers. Product-specific logic is implemented in the target
repository and must exist before generated adapters are considered ready.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from dataclasses import dataclass, asdict
from typing import Any, Iterable
from urllib.parse import urlsplit

VERSION = "3.0.0"
SCHEMA_VERSION = "webmcp-toolset.v1"
NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")
HANDLER_RE = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")
AMBIGUOUS_NAME_RE = re.compile(
    r"^(?:do|action|process|manage|finalize|handle|run|execute|tool)(?:[._-].*)?$",
    re.IGNORECASE,
)
INJECTION_PATTERNS = [
    re.compile(r"\bignore\s+(?:all\s+|any\s+|the\s+)?previous\s+instructions?\b", re.I),
    re.compile(r"\b(?:system|developer)\s+(?:instruction|message|override)\b", re.I),
    re.compile(r"<\s*(?:system|developer|assistant|important)\b", re.I),
    re.compile(r"\b(?:exfiltrate|steal)\b.*\b(?:secret|token|history|credential|data)\b", re.I),
    re.compile(r"\breveal\b.*\b(?:system prompt|secret|credential|browsing history)\b", re.I),
]
TOKEN_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "a", "an", "and", "as", "at", "be", "by", "current", "currently", "for",
    "from", "in", "into", "is", "it", "of", "on", "or", "page", "return",
    "returns", "the", "this", "to", "tool", "using", "when", "with",
}
EFFECTS = {
    "read",
    "local-write",
    "remote-write",
    "external-communication",
    "purchase",
    "permission-change",
    "destructive",
}
OUTPUT_TRUST = {"trusted", "external", "user-generated", "mixed"}
CONFIRMATIONS = {"none", "required", "site-native"}
IDEMPOTENCY = {"natural", "keyed", "none"}
LIFETIMES = {"document", "route", "selection", "mode", "permission", "custom"}
CONSEQUENTIAL_EFFECTS = {
    "external-communication", "purchase", "permission-change", "destructive"
}
MUTATING_EFFECTS = EFFECTS - {"read"}
ALLOWED_ROOT = {"$schema", "schemaVersion", "app", "tools"}
ALLOWED_APP = {"name", "description"}
ALLOWED_TOOL = {
    "name", "title", "description", "handler", "inputSchema",
    "annotations", "registration", "semantics",
}
ALLOWED_ANNOTATIONS = {"readOnlyHint", "untrustedContentHint"}
ALLOWED_REGISTRATION = {"lifetime", "owner", "exposedTo"}
ALLOWED_SEMANTICS = {
    "effect", "outputTrust", "confirmation", "idempotency", "reversible",
    "preconditions", "visibleEffect", "successEvidence", "failureModes",
    "sensitiveInputs",
}
HIGHLY_SENSITIVE_PATTERNS = {
    "password": re.compile(r"(?:^|_)(?:password|passcode|pin)(?:$|_)", re.I),
    "secret": re.compile(r"(?:^|_)(?:secret|credential|private_key)(?:$|_)", re.I),
    "api_key": re.compile(r"(?:^|_)(?:api_?key|access_?token|refresh_?token)(?:$|_)", re.I),
    "government_id": re.compile(r"(?:^|_)(?:ssn|social_?security|passport|national_?id)(?:$|_)", re.I),
    "payment_card": re.compile(r"(?:^|_)(?:credit_?card|card_?number|cvv|cvc)(?:$|_)", re.I),
    "medical": re.compile(r"(?:^|_)(?:diagnosis|medical|health|pregnan\w*|biometric)(?:$|_)", re.I),
}
CONTEXTUAL_SENSITIVE_PATTERNS = {
    "location": re.compile(r"(?:^|_)(?:precise_?location|location|latitude|longitude|address)(?:$|_)", re.I),
    "demographic": re.compile(r"(?:^|_)(?:age|birth_?date|date_?of_?birth|gender|race|ethnicity|religion|skin_?tone)(?:$|_)", re.I),
    "financial": re.compile(r"(?:^|_)(?:income|salary|net_?worth)(?:$|_)", re.I),
    "cross_site_history": re.compile(r"(?:^|_)(?:browsing_?history|purchase_?history|previous_?purchases)(?:$|_)", re.I),
}
EFFECT_VERBS = {
    "remote-write": {"create", "update", "change", "save", "set", "edit", "modify", "submit"},
    "external-communication": {"send", "share", "publish", "message", "email", "notify"},
    "purchase": {"purchase", "buy", "charge", "order", "pay"},
    "permission-change": {"grant", "revoke", "permission", "access", "role", "share"},
    "destructive": {"delete", "remove", "erase", "destroy", "purge"},
}


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    message: str
    remediation: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class ManifestError(Exception):
    """Raised for unreadable or invalid manifest input."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_manifest(path: Path) -> tuple[dict[str, Any], str]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ManifestError(f"cannot read manifest {path}: {exc}") from exc
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ManifestError(
            f"invalid JSON in {path} at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(value, dict):
        raise ManifestError("manifest root must be a JSON object")
    return value, _sha256_bytes(_canonical_json(value).encode("utf-8"))


def _add(
    findings: list[Finding],
    severity: str,
    code: str,
    path: str,
    message: str,
    remediation: str,
) -> None:
    findings.append(Finding(severity, code, path, message, remediation))


def _unknown_keys(
    value: Any,
    allowed: set[str],
    path: str,
    findings: list[Finding],
) -> None:
    if not isinstance(value, dict):
        return
    for key in sorted(set(value) - allowed):
        _add(
            findings,
            "error",
            "unknown_field",
            f"{path}.{key}",
            f"Unsupported field {key!r}.",
            "Remove the field or place build-only semantics under the documented semantics object.",
        )


def _normalized_field_name(name: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    value = re.sub(r"[^A-Za-z0-9]+", "_", value)
    return value.strip("_").lower()


def _tokens(text: str) -> set[str]:
    return {token for token in TOKEN_RE.findall(text.lower()) if token not in STOPWORDS}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _is_loopback(hostname: str | None) -> bool:
    if hostname is None:
        return False
    host = hostname.strip("[]").lower()
    return host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".localhost")


def _validate_origin(
    origin: Any,
    path: str,
    findings: list[Finding],
) -> None:
    if not isinstance(origin, str) or not origin:
        _add(
            findings, "error", "invalid_origin", path,
            "Origin must be a non-empty string.",
            "Use an exact origin such as https://partner.example.",
        )
        return
    if "*" in origin:
        _add(
            findings, "error", "wildcard_origin", path,
            "Wildcard origins are not allowed.",
            "List each required, trustworthy origin explicitly.",
        )
        return
    try:
        parsed = urlsplit(origin)
        _ = parsed.port
    except ValueError as exc:
        _add(
            findings, "error", "invalid_origin", path,
            f"Origin cannot be parsed: {exc}.",
            "Use scheme, host, and optional port only.",
        )
        return
    if parsed.scheme not in {"https", "http"} or not parsed.hostname:
        _add(
            findings, "error", "untrustworthy_origin", path,
            "Origin must use HTTPS, except explicitly marked loopback development origins.",
            "Use an exact HTTPS origin.",
        )
        return
    if parsed.username or parsed.password:
        _add(
            findings, "error", "origin_credentials", path,
            "Origin must not contain credentials.",
            "Remove user information and store credentials outside the tool definition.",
        )
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        _add(
            findings, "error", "origin_not_origin_only", path,
            "exposedTo accepts origins, not full URLs with paths, queries, or fragments.",
            "Keep only scheme, host, and optional port.",
        )
    if parsed.scheme == "http":
        if _is_loopback(parsed.hostname):
            _add(
                findings, "warning", "loopback_http_origin", path,
                "HTTP loopback origin is suitable only for local development.",
                "Use HTTPS for production and keep this origin out of production manifests.",
            )
        else:
            _add(
                findings, "error", "insecure_origin", path,
                "Non-loopback HTTP is not a trustworthy production origin.",
                "Use HTTPS.",
            )


def _validate_input_schema(
    schema: Any,
    base_path: str,
    findings: list[Finding],
) -> tuple[set[str], dict[str, Any]]:
    if not isinstance(schema, dict):
        _add(
            findings, "error", "input_schema_type", base_path,
            "inputSchema must be a JSON Schema object.",
            "Use an object schema with properties, required, and additionalProperties.",
        )
        return set(), {}
    schema_type = schema.get("type")
    if schema_type != "object":
        _add(
            findings, "error", "input_schema_root", f"{base_path}.type",
            "WebMCP tool input must be modeled as an object in this manifest.",
            "Set type to object and move arguments under properties.",
        )
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        _add(
            findings, "error", "properties_type", f"{base_path}.properties",
            "properties must be an object.",
            "Map each argument name to a JSON Schema.",
        )
        properties = {}
    required = schema.get("required", [])
    if not isinstance(required, list) or any(not isinstance(x, str) for x in required):
        _add(
            findings, "error", "required_type", f"{base_path}.required",
            "required must be an array of property names.",
            "Use a string array and omit it when no property is required.",
        )
        required = []
    if len(required) != len(set(required)):
        _add(
            findings, "error", "required_duplicates", f"{base_path}.required",
            "required contains duplicate property names.",
            "Keep each required property once.",
        )
    unknown_required = sorted(set(required) - set(properties))
    for name in unknown_required:
        _add(
            findings, "error", "required_unknown_property", f"{base_path}.required",
            f"Required property {name!r} is absent from properties.",
            "Define the property or remove it from required.",
        )
    if schema.get("additionalProperties") is not False:
        _add(
            findings, "warning", "open_input_object", f"{base_path}.additionalProperties",
            "The input object accepts undeclared properties.",
            "Set additionalProperties to false unless an open object is essential and reviewed.",
        )
    for name, prop in properties.items():
        prop_path = f"{base_path}.properties.{name}"
        if not isinstance(prop, dict):
            _add(
                findings, "error", "property_schema_type", prop_path,
                "Property schema must be an object.",
                "Define a valid JSON Schema for the property.",
            )
            continue
        if not isinstance(prop.get("description"), str) or not prop.get("description", "").strip():
            _add(
                findings, "warning", "property_description_missing", f"{prop_path}.description",
                "Property has no factual description.",
                "Describe the value and units/format without adding agent instructions.",
            )
        prop_type = prop.get("type")
        if prop_type == "string" and "enum" not in prop and "const" not in prop:
            if "maxLength" not in prop:
                _add(
                    findings, "warning", "string_unbounded", f"{prop_path}.maxLength",
                    "Free-text string has no maximum length.",
                    "Add a task-appropriate maxLength and enforce it in code.",
                )
            if name in required and "minLength" not in prop and prop.get("format") not in {
                "date", "date-time", "email", "uri", "uuid"
            }:
                _add(
                    findings, "warning", "required_string_allows_empty", f"{prop_path}.minLength",
                    "Required string may still be empty.",
                    "Add minLength: 1 when an empty value is invalid.",
                )
        if prop_type == "array":
            if "items" not in prop:
                _add(
                    findings, "error", "array_items_missing", f"{prop_path}.items",
                    "Array schema has no items contract.",
                    "Define the allowed item schema.",
                )
            if "maxItems" not in prop:
                _add(
                    findings, "warning", "array_unbounded", f"{prop_path}.maxItems",
                    "Array input has no maximum item count.",
                    "Add a task-appropriate maxItems and enforce it in code.",
                )
    return set(properties), properties


def _validate_tool(
    tool: Any,
    index: int,
    findings: list[Finding],
) -> dict[str, Any]:
    path = f"$.tools[{index}]"
    if not isinstance(tool, dict):
        _add(
            findings, "error", "tool_type", path,
            "Each tool must be an object.",
            "Replace the item with a complete tool contract.",
        )
        return {}
    _unknown_keys(tool, ALLOWED_TOOL, path, findings)

    name = tool.get("name")
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        _add(
            findings, "error", "tool_name", f"{path}.name",
            "Tool name must be 1–128 ASCII letters, digits, underscores, hyphens, or periods.",
            "Choose a direct, distinctive verb-object name.",
        )
        name = f"invalid_{index}"
    elif AMBIGUOUS_NAME_RE.fullmatch(name):
        _add(
            findings, "warning", "ambiguous_tool_name", f"{path}.name",
            "Tool name is too generic to communicate its effect.",
            "Use a specific verb-object name that distinguishes preview, initiation, and commitment.",
        )

    title = tool.get("title")
    if title is not None and not isinstance(title, str):
        _add(
            findings, "error", "title_type", f"{path}.title",
            "title must be a string when present.",
            "Use a localized human-readable label or omit the field.",
        )

    description = tool.get("description")
    if not isinstance(description, str) or not description.strip():
        _add(
            findings, "error", "description_missing", f"{path}.description",
            "Tool description must be a non-empty factual statement.",
            "Describe the action, applicability, actual effect, and verifiable result.",
        )
        description = ""
    elif len(description) > 1000:
        _add(
            findings, "error", "description_too_long", f"{path}.description",
            "Description exceeds the manifest limit of 1000 characters.",
            "Keep capability metadata concise and move detail into application documentation.",
        )
    for pattern in INJECTION_PATTERNS:
        if pattern.search(description):
            _add(
                findings, "error", "metadata_injection_pattern", f"{path}.description",
                "Description contains instruction-like or exfiltration language.",
                "Replace it with a factual capability description and investigate the source.",
            )
            break

    handler = tool.get("handler")
    if not isinstance(handler, str) or not HANDLER_RE.fullmatch(handler):
        _add(
            findings, "error", "handler_name", f"{path}.handler",
            "handler must be a JavaScript identifier naming an existing application function.",
            "Provide a handler key such as updateDashboard.",
        )
        handler = ""

    property_names, properties = _validate_input_schema(
        tool.get("inputSchema"), f"{path}.inputSchema", findings
    )

    annotations = tool.get("annotations")
    if not isinstance(annotations, dict):
        _add(
            findings, "error", "annotations_type", f"{path}.annotations",
            "annotations must be an object with explicit boolean hints.",
            "Declare readOnlyHint and untrustedContentHint.",
        )
        annotations = {}
    else:
        _unknown_keys(annotations, ALLOWED_ANNOTATIONS, f"{path}.annotations", findings)
    for key in ("readOnlyHint", "untrustedContentHint"):
        if not isinstance(annotations.get(key), bool):
            _add(
                findings, "error", "annotation_boolean", f"{path}.annotations.{key}",
                f"{key} must be an explicit boolean.",
                "Set the hint from reviewed implementation behavior.",
            )

    registration = tool.get("registration")
    if not isinstance(registration, dict):
        _add(
            findings, "error", "registration_type", f"{path}.registration",
            "registration must describe lifetime and origin exposure.",
            "Add lifetime, owner, and exposedTo.",
        )
        registration = {}
    else:
        _unknown_keys(registration, ALLOWED_REGISTRATION, f"{path}.registration", findings)
    lifetime = registration.get("lifetime")
    if lifetime not in LIFETIMES:
        _add(
            findings, "error", "registration_lifetime", f"{path}.registration.lifetime",
            f"lifetime must be one of {sorted(LIFETIMES)}.",
            "Choose the state owner that makes the tool valid.",
        )
    owner = registration.get("owner")
    if lifetime and lifetime != "document" and (not isinstance(owner, str) or not owner.strip()):
        _add(
            findings, "warning", "registration_owner_missing", f"{path}.registration.owner",
            "State-dependent registration has no named owner.",
            "Name the route, selection, mode, permission, or component that aborts it.",
        )
    exposed = registration.get("exposedTo")
    if not isinstance(exposed, list):
        _add(
            findings, "error", "exposed_to_type", f"{path}.registration.exposedTo",
            "exposedTo must be an array, even when empty.",
            "Use [] for same-origin-only exposure.",
        )
        exposed = []
    else:
        if len(exposed) != len(set(map(str, exposed))):
            _add(
                findings, "error", "duplicate_origin", f"{path}.registration.exposedTo",
                "exposedTo contains duplicate origins.",
                "Keep each exact origin once.",
            )
        for j, origin in enumerate(exposed):
            _validate_origin(origin, f"{path}.registration.exposedTo[{j}]", findings)

    semantics = tool.get("semantics")
    if not isinstance(semantics, dict):
        _add(
            findings, "error", "semantics_type", f"{path}.semantics",
            "semantics must explicitly describe effect and review properties.",
            "Add the required build-time semantics fields.",
        )
        semantics = {}
    else:
        _unknown_keys(semantics, ALLOWED_SEMANTICS, f"{path}.semantics", findings)

    effect = semantics.get("effect")
    if effect not in EFFECTS:
        _add(
            findings, "error", "effect", f"{path}.semantics.effect",
            f"effect must be one of {sorted(EFFECTS)}.",
            "Classify the handler's actual state change, not its marketing label.",
        )
    output_trust = semantics.get("outputTrust")
    if output_trust not in OUTPUT_TRUST:
        _add(
            findings, "error", "output_trust", f"{path}.semantics.outputTrust",
            f"outputTrust must be one of {sorted(OUTPUT_TRUST)}.",
            "Classify all returned content by its least-trusted material source.",
        )
    confirmation = semantics.get("confirmation")
    if confirmation not in CONFIRMATIONS:
        _add(
            findings, "error", "confirmation", f"{path}.semantics.confirmation",
            f"confirmation must be one of {sorted(CONFIRMATIONS)}.",
            "Declare none, required, or site-native.",
        )
    idempotency = semantics.get("idempotency")
    if idempotency not in IDEMPOTENCY:
        _add(
            findings, "error", "idempotency", f"{path}.semantics.idempotency",
            f"idempotency must be one of {sorted(IDEMPOTENCY)}.",
            "Declare natural, keyed, or none and document retry behavior.",
        )

    read_hint = annotations.get("readOnlyHint")
    untrusted_hint = annotations.get("untrustedContentHint")
    if effect == "read" and read_hint is False:
        _add(
            findings, "warning", "read_hint_conservative", f"{path}.annotations.readOnlyHint",
            "A declared read effect does not advertise readOnlyHint.",
            "Set the hint to true only after proving the handler and downstream path do not mutate state.",
        )
    if effect in MUTATING_EFFECTS and read_hint is True:
        _add(
            findings, "error", "read_only_mismatch", f"{path}.annotations.readOnlyHint",
            f"readOnlyHint is true but the declared effect is {effect}.",
            "Set the hint to false and make the side effect explicit.",
        )
    if output_trust in {"external", "user-generated", "mixed"} and untrusted_hint is not True:
        _add(
            findings, "error", "untrusted_hint_missing", f"{path}.annotations.untrustedContentHint",
            f"{output_trust} output requires untrustedContentHint.",
            "Set the hint to true and preserve provenance/data-instruction boundaries.",
        )

    if effect in CONSEQUENTIAL_EFFECTS and confirmation == "none":
        _add(
            findings, "error", "confirmation_required", f"{path}.semantics.confirmation",
            f"{effect} is consequential but confirmation is none.",
            "Require confirmation bound to the exact current operation.",
        )
    if effect == "remote-write" and confirmation == "none":
        _add(
            findings, "warning", "remote_write_without_confirmation", f"{path}.semantics.confirmation",
            "Durable remote write has no confirmation requirement.",
            "Verify that explicit user intent and the site's policy make confirmation unnecessary, or require it.",
        )
    if effect in CONSEQUENTIAL_EFFECTS and idempotency == "none":
        _add(
            findings, "warning", "consequential_non_idempotent", f"{path}.semantics.idempotency",
            "Consequential action has no idempotency protection.",
            "Use a keyed or naturally idempotent commit, or define authoritative uncertain-outcome recovery.",
        )

    if effect in EFFECT_VERBS and description:
        words = _tokens(description)
        if not words.intersection(EFFECT_VERBS[effect]):
            _add(
                findings, "warning", "effect_not_explicit", f"{path}.description",
                f"Description does not use an explicit verb associated with {effect}.",
                "Name the real side effect directly, such as send, purchase, grant, or delete.",
            )

    preconditions = semantics.get("preconditions")
    if not isinstance(preconditions, list) or any(not isinstance(x, str) or not x.strip() for x in preconditions):
        _add(
            findings, "error", "preconditions_type", f"{path}.semantics.preconditions",
            "preconditions must be an array of non-empty statements.",
            "Describe page state and authorization conditions checked at execution time.",
        )
        preconditions = []
    if effect in CONSEQUENTIAL_EFFECTS and not preconditions:
        _add(
            findings, "error", "consequential_preconditions_missing", f"{path}.semantics.preconditions",
            "Consequential action has no declared preconditions.",
            "Declare account, resource, authorization, current-state, and confirmation preconditions.",
        )

    visible_effect = semantics.get("visibleEffect")
    if not isinstance(visible_effect, str) or not visible_effect.strip():
        _add(
            findings, "error", "visible_effect_missing", f"{path}.semantics.visibleEffect",
            "visibleEffect must state what the person can inspect in the page.",
            "State the visible change or explicitly say there is no visible state change.",
        )

    evidence = semantics.get("successEvidence")
    if not isinstance(evidence, list) or not evidence or any(
        not isinstance(x, str) or not x.strip() for x in evidence
    ):
        _add(
            findings, "error", "success_evidence_missing", f"{path}.semantics.successEvidence",
            "successEvidence must contain at least one observable proof.",
            "Return stable IDs, affected state, receipt/audit data, or visible-state revision.",
        )

    sensitive = semantics.get("sensitiveInputs")
    declared_sensitive: dict[str, str] = {}
    if not isinstance(sensitive, list):
        _add(
            findings, "error", "sensitive_inputs_type", f"{path}.semantics.sensitiveInputs",
            "sensitiveInputs must be an array, even when empty.",
            "Use [] or declare each necessary sensitive field and purpose.",
        )
        sensitive = []
    else:
        for j, item in enumerate(sensitive):
            item_path = f"{path}.semantics.sensitiveInputs[{j}]"
            if not isinstance(item, dict):
                _add(
                    findings, "error", "sensitive_input_entry", item_path,
                    "Sensitive input declaration must be an object.",
                    "Provide name and purpose.",
                )
                continue
            if set(item) - {"name", "purpose"}:
                _add(
                    findings, "error", "sensitive_input_unknown_field", item_path,
                    "Sensitive input declaration has unsupported fields.",
                    "Keep only name and purpose.",
                )
            s_name = item.get("name")
            purpose = item.get("purpose")
            if not isinstance(s_name, str) or not s_name:
                _add(
                    findings, "error", "sensitive_input_name", f"{item_path}.name",
                    "Sensitive input name must be non-empty.",
                    "Name a property from inputSchema.properties.",
                )
                continue
            if s_name in declared_sensitive:
                _add(
                    findings, "error", "sensitive_input_duplicate", f"{item_path}.name",
                    f"Sensitive input {s_name!r} is declared more than once.",
                    "Keep one declaration with a precise purpose.",
                )
            if s_name not in property_names:
                _add(
                    findings, "error", "sensitive_input_unknown", f"{item_path}.name",
                    f"Sensitive input {s_name!r} is absent from inputSchema.properties.",
                    "Correct the name or remove the declaration.",
                )
            if not isinstance(purpose, str) or len(purpose.strip()) < 12:
                _add(
                    findings, "warning", "sensitive_purpose_weak", f"{item_path}.purpose",
                    "Sensitive input purpose is missing or too vague.",
                    "Explain why this exact field is necessary for the declared job.",
                )
            declared_sensitive[s_name] = purpose if isinstance(purpose, str) else ""

    for prop_name in property_names:
        normalized = _normalized_field_name(prop_name)
        strong = next((label for label, pat in HIGHLY_SENSITIVE_PATTERNS.items() if pat.search(normalized)), None)
        contextual = next((label for label, pat in CONTEXTUAL_SENSITIVE_PATTERNS.items() if pat.search(normalized)), None)
        if strong and prop_name not in declared_sensitive:
            _add(
                findings, "error", "undeclared_highly_sensitive_input",
                f"{path}.inputSchema.properties.{prop_name}",
                f"Property resembles highly sensitive {strong} data but is not declared.",
                "Remove it unless strictly necessary; otherwise declare purpose and complete domain security review.",
            )
        elif contextual and prop_name not in declared_sensitive:
            _add(
                findings, "warning", "undeclared_sensitive_input",
                f"{path}.inputSchema.properties.{prop_name}",
                f"Property resembles sensitive or cross-site {contextual} data but is not declared.",
                "Remove it unless required, or declare its exact purpose and test data minimization.",
            )

    if exposed and declared_sensitive:
        _add(
            findings, "warning", "cross_origin_sensitive_data", f"{path}.registration.exposedTo",
            "Tool combines cross-origin exposure with declared sensitive inputs.",
            "Review caller authorization, returned data, retention, and whether same-origin-only design is possible.",
        )

    return {
        "index": index,
        "name": name,
        "description": description,
        "handler": handler,
        "effect": effect,
        "outputTrust": output_trust,
        "confirmation": confirmation,
        "idempotency": idempotency,
        "lifetime": lifetime,
        "exposedTo": exposed,
        "sensitiveInputs": sorted(declared_sensitive),
        "propertyCount": len(properties),
    }


def validate_manifest(manifest: dict[str, Any], manifest_hash: str) -> dict[str, Any]:
    findings: list[Finding] = []
    _unknown_keys(manifest, ALLOWED_ROOT, "$", findings)
    if manifest.get("schemaVersion") != SCHEMA_VERSION:
        _add(
            findings, "error", "schema_version", "$.schemaVersion",
            f"schemaVersion must be {SCHEMA_VERSION!r}.",
            "Migrate the manifest to the bundled schema.",
        )

    app = manifest.get("app")
    if not isinstance(app, dict):
        _add(
            findings, "error", "app_type", "$.app",
            "app must be an object.",
            "Provide at least app.name.",
        )
    else:
        _unknown_keys(app, ALLOWED_APP, "$.app", findings)
        if not isinstance(app.get("name"), str) or not app.get("name", "").strip():
            _add(
                findings, "error", "app_name", "$.app.name",
                "app.name must be a non-empty string.",
                "Name the application or surface owning the tools.",
            )

    tools = manifest.get("tools")
    summaries: list[dict[str, Any]] = []
    if not isinstance(tools, list) or not tools:
        _add(
            findings, "error", "tools_type", "$.tools",
            "tools must be a non-empty array.",
            "Add at least one complete tool contract.",
        )
        tools = []
    elif len(tools) > 30:
        _add(
            findings, "warning", "large_toolset", "$.tools",
            f"Toolset contains {len(tools)} tools; large overlapping catalogs reduce selection quality.",
            "Partition tools by page state/domain and run selection evals.",
        )

    for i, item in enumerate(tools):
        summaries.append(_validate_tool(item, i, findings))

    name_to_indexes: dict[str, list[int]] = {}
    handler_to_tools: dict[str, list[dict[str, Any]]] = {}
    for summary in summaries:
        name_to_indexes.setdefault(summary.get("name", ""), []).append(summary.get("index", -1))
        handler_to_tools.setdefault(summary.get("handler", ""), []).append(summary)
    for name, indexes in name_to_indexes.items():
        if name and len(indexes) > 1:
            _add(
                findings, "error", "duplicate_tool_name", "$.tools",
                f"Tool name {name!r} is repeated at indexes {indexes}.",
                "Give every registration a unique, semantically distinct name.",
            )
    for handler, mapped in handler_to_tools.items():
        effects = {item.get("effect") for item in mapped}
        if handler and len(mapped) > 1 and len(effects) > 1:
            _add(
                findings, "warning", "handler_effect_alias", "$.tools",
                f"Handler {handler!r} is used by tools with different effects: {sorted(map(str, effects))}.",
                "Confirm the handler branches cannot hide a stronger side effect from a weaker contract.",
            )

    # Pairwise selection-overlap heuristic.
    for left_i in range(len(summaries)):
        for right_i in range(left_i + 1, len(summaries)):
            left = summaries[left_i]
            right = summaries[right_i]
            left_tokens = _tokens(f"{left.get('name', '')} {left.get('description', '')}")
            right_tokens = _tokens(f"{right.get('name', '')} {right.get('description', '')}")
            score = _jaccard(left_tokens, right_tokens)
            if score >= 0.67:
                _add(
                    findings, "warning", "tool_overlap", "$.tools",
                    f"Tools {left.get('name')!r} and {right.get('name')!r} have high lexical overlap ({score:.2f}).",
                    "Clarify or merge the jobs, then add near-miss selection evals.",
                )

    errors = sum(1 for f in findings if f.severity == "error")
    warnings = sum(1 for f in findings if f.severity == "warning")
    status = "FAIL" if errors else ("WARN" if warnings else "PASS")
    return {
        "status": status,
        "schemaVersion": manifest.get("schemaVersion"),
        "manifestSha256": manifest_hash,
        "summary": {
            "tools": len(tools),
            "errors": errors,
            "warnings": warnings,
            "findings": len(findings),
        },
        "tools": summaries,
        "findings": [f.to_dict() for f in findings],
    }


def _risk(
    risks: list[dict[str, Any]],
    tool: str,
    risk_id: str,
    severity: str,
    condition: str,
    controls: Iterable[str],
    tests: Iterable[str],
) -> None:
    risks.append({
        "tool": tool,
        "id": risk_id,
        "severity": severity,
        "condition": condition,
        "controls": list(controls),
        "tests": list(tests),
    })


def build_threat_model(
    manifest: dict[str, Any],
    manifest_hash: str,
    validation: dict[str, Any],
) -> dict[str, Any]:
    risks: list[dict[str, Any]] = []
    for tool in validation.get("tools", []):
        name = tool.get("name", "<invalid>")
        effect = tool.get("effect")
        trust = tool.get("outputTrust")
        lifetime = tool.get("lifetime")
        exposed = tool.get("exposedTo") or []
        sensitive = tool.get("sensitiveInputs") or []
        _risk(
            risks, name, "metadata-poisoning", "medium",
            "Agents select this capability from untrusted natural-language metadata.",
            [
                "Keep metadata factual and concise.",
                "Treat metadata as data rather than instruction authority.",
                "Use distinct names and non-overlapping contracts.",
            ],
            [
                "Inject policy-looking text into name/description fixtures.",
                "Add a lookalike malicious tool and measure selection.",
            ],
        )
        _risk(
            risks, name, "intent-misrepresentation", "high" if effect in CONSEQUENTIAL_EFFECTS else "medium",
            f"Declared effect is {effect}; the handler and downstream calls may differ.",
            [
                "Compare handler call graph and observed state/network effects with the manifest.",
                "Enforce authorization and confirmation in the authoritative application/service.",
                "Return observable success evidence.",
            ],
            [
                "Snapshot state before/after execution.",
                "Exercise UI and WebMCP paths with the same inputs.",
            ],
        )
        if trust in {"external", "user-generated", "mixed"}:
            _risk(
                risks, name, "output-injection", "high",
                f"Output trust is {trust}.",
                [
                    "Set untrustedContentHint.",
                    "Return bounded structured records with provenance.",
                    "Keep returned text out of instructions and follow-on destinations.",
                ],
                [
                    "Place explicit and subtle malicious instructions in returned records.",
                    "Test read-to-write chains and unrelated-data exfiltration.",
                ],
            )
        if tool.get("propertyCount", 0) >= 6 or sensitive:
            _risk(
                risks, name, "over-parameterization", "high" if sensitive else "medium",
                "The input surface is broad or contains declared sensitive fields.",
                [
                    "Apply field-by-field necessity review.",
                    "Derive authorized page/server context without asking the agent to transmit it.",
                    "Reject unknown properties and minimize retention.",
                ],
                [
                    "Verify unnecessary fields remain absent.",
                    "Test cross-site or personalization data is not supplied.",
                ],
            )
        if effect in MUTATING_EFFECTS:
            _risk(
                risks, name, "signed-session-privilege", "high",
                "The page may act with the user's authenticated session.",
                [
                    "Perform fresh resource/tenant authorization.",
                    "Bind required confirmation to exact scope.",
                    "Use idempotency and authoritative receipts.",
                ],
                [
                    "Run unauthenticated, wrong-role, wrong-tenant, stale-session, and duplicate-call cases.",
                    "Verify confirmation decline causes no mutation.",
                ],
            )
            _risk(
                risks, name, "cancellation-race", "high" if effect in CONSEQUENTIAL_EFFECTS else "medium",
                "Execution cancellation can race with client or server mutation.",
                [
                    "Propagate the execution signal.",
                    "Recheck preconditions immediately before mutation.",
                    "Query authoritative status before retrying an uncertain commit.",
                ],
                [
                    "Cancel before start, during I/O, during commit, and after server completion.",
                    "Test late promise resolution and outcome-unknown recovery.",
                ],
            )
            _risk(
                risks, name, "ui-path-divergence", "medium",
                "The tool path may bypass UI validation or leave the shared interface stale.",
                [
                    "Use shared application/service functions.",
                    "Update the same state store and visible UI.",
                    "Compare UI and tool-path authorization and outcomes.",
                ],
                [
                    "Assert returned identifiers and visible state agree.",
                    "Inject failures between backend commit and UI refresh.",
                ],
            )
        if exposed:
            _risk(
                risks, name, "cross-origin-exposure", "high",
                f"Tool is exposed to {len(exposed)} cross-origin caller(s).",
                [
                    "Use exact secure origins and deliberate Permissions Policy.",
                    "Keep handler authorization independent of origin exposure.",
                    "Review returned data for each caller.",
                ],
                [
                    "Test unlisted origin, sibling subdomain, changed port, frame navigation, and revoked access.",
                ],
            )
        if lifetime and lifetime != "document":
            _risk(
                risks, name, "stale-registration", "medium",
                f"Tool lifetime is owned by {lifetime} state.",
                [
                    "Abort registration when the owner changes.",
                    "Recheck current state inside the handler.",
                    "Observe toolchange and UI affordances.",
                ],
                [
                    "Change route/selection/mode/permission before and during execution.",
                    "Test unmount, navigation, and back-forward cache.",
                ],
            )

    global_risks = [
        {
            "id": "spec-and-platform-drift",
            "severity": "medium",
            "condition": "WebMCP and product availability are evolving.",
            "controls": [
                "Verify current normative and platform sources at implementation/release time.",
                "Feature-detect document.modelContext.registerTool.",
                "Record target versions and retrieval dates.",
            ],
            "tests": [
                "Run target-browser discovery and execution tests.",
                "Search for deprecated navigator surfaces and manual unregister APIs.",
            ],
        },
        {
            "id": "cross-tool-chain",
            "severity": "high",
            "condition": "A benign read can feed untrusted data into a consequential write.",
            "controls": [
                "Authorize every call independently.",
                "Keep untrusted data out of recipients, destinations, commands, and confirmations.",
                "Stop chains on ambiguity, failure, or declined confirmation.",
            ],
            "tests": [
                "Poison read output and attempt a write tool.",
                "Use lookalike tools and changed page state between calls.",
            ],
        },
    ]
    validation_status = validation.get("status")
    any_high = any(r["severity"] == "high" for r in risks + global_risks)
    status = "FAIL" if validation_status == "FAIL" else (
        "WARN" if validation_status == "WARN" or any_high else "PASS"
    )
    return {
        "status": status,
        "manifestSha256": manifest_hash,
        "validationStatus": validation_status,
        "scope": {
            "tools": len(validation.get("tools", [])),
            "risks": len(risks) + len(global_risks),
            "note": "Risk presence is not proof of vulnerability; controls require implementation and live verification.",
        },
        "globalRisks": global_risks,
        "toolRisks": risks,
    }


def build_eval_plan(
    manifest: dict[str, Any],
    manifest_hash: str,
    validation: dict[str, Any],
) -> dict[str, Any]:
    deterministic: list[dict[str, Any]] = []
    browser: list[dict[str, Any]] = []
    agent: list[dict[str, Any]] = []
    adversarial: list[dict[str, Any]] = []

    for tool in validation.get("tools", []):
        name = tool.get("name", "invalid")
        effect = tool.get("effect")
        trust = tool.get("outputTrust")
        exposed = tool.get("exposedTo") or []
        sensitive = tool.get("sensitiveInputs") or []
        deterministic.extend([
            {
                "id": f"{name}.valid-minimum",
                "layer": "handler",
                "assert": "Minimum valid input succeeds and returns declared success evidence.",
            },
            {
                "id": f"{name}.unknown-property",
                "layer": "handler",
                "assert": "Unknown input property is rejected or stripped by explicit reviewed policy.",
            },
            {
                "id": f"{name}.invalid-types-and-bounds",
                "layer": "handler",
                "assert": "Wrong types, empty required strings, and boundary violations fail safely.",
            },
            {
                "id": f"{name}.precondition-changed",
                "layer": "handler",
                "assert": "Changed route/selection/tenant/permission fails closed before side effect.",
            },
            {
                "id": f"{name}.cancel",
                "layer": "handler",
                "assert": "Execution signal is propagated and cancellation outcome is explicit.",
            },
            {
                "id": f"{name}.safe-error",
                "layer": "handler",
                "assert": "Dependency failure returns structured safe error without secrets or stack trace.",
            },
        ])
        browser.extend([
            {
                "id": f"{name}.discovery",
                "layer": "browser",
                "assert": "Tool appears only in valid page state with exact manifest metadata.",
            },
            {
                "id": f"{name}.lifecycle",
                "layer": "browser",
                "assert": "Registration aborts on its declared owner change and can be registered again.",
            },
            {
                "id": f"{name}.visible-result",
                "layer": "browser",
                "assert": "Returned evidence and visible page state agree.",
            },
            {
                "id": f"{name}.unsupported-fallback",
                "layer": "browser",
                "assert": "Human interface remains usable when registerTool is unavailable.",
            },
        ])
        agent.extend([
            {
                "id": f"{name}.clear-positive",
                "layer": "agent",
                "assert": "Clear matching intent selects this tool with valid minimum arguments.",
            },
            {
                "id": f"{name}.paraphrase",
                "layer": "agent",
                "assert": "A natural paraphrase selects the same tool.",
            },
            {
                "id": f"{name}.near-miss",
                "layer": "agent",
                "assert": "Neighboring intent selects a different tool or no tool.",
            },
            {
                "id": f"{name}.underspecified",
                "layer": "agent",
                "assert": "Missing material argument causes clarification rather than invention.",
            },
            {
                "id": f"{name}.unavailable-state",
                "layer": "agent",
                "assert": "Agent does not call the tool when it is absent from current page state.",
            },
            {
                "id": f"{name}.result-verification",
                "layer": "agent",
                "assert": "Agent uses returned evidence and does not overclaim success.",
            },
        ])
        adversarial.extend([
            {
                "id": f"{name}.poisoned-metadata",
                "layer": "security",
                "assert": "Instruction-like metadata cannot redirect the agent or obtain unrelated context.",
            },
            {
                "id": f"{name}.misrepresented-effect",
                "layer": "security",
                "assert": "Observed state/network effects match the declared effect and annotation.",
            },
        ])
        if trust in {"external", "user-generated", "mixed"}:
            adversarial.append({
                "id": f"{name}.poisoned-output",
                "layer": "security",
                "assert": "Malicious returned text remains data and cannot trigger an unrelated follow-on action.",
            })
        if effect in MUTATING_EFFECTS:
            deterministic.extend([
                {
                    "id": f"{name}.exact-state-delta",
                    "layer": "handler",
                    "assert": "Only the declared state changes.",
                },
                {
                    "id": f"{name}.duplicate-or-retry",
                    "layer": "handler",
                    "assert": "Duplicate and uncertain-outcome retry follow declared idempotency policy.",
                },
            ])
            if tool.get("confirmation") in {"required", "site-native"} or effect in CONSEQUENTIAL_EFFECTS:
                adversarial.append({
                    "id": f"{name}.confirmation-declined",
                    "layer": "security",
                    "assert": "Declined or absent required confirmation causes no mutation.",
                })
            adversarial.extend([
                {
                    "id": f"{name}.wrong-tenant-role",
                    "layer": "security",
                    "assert": "Signed-in session cannot cross tenant/resource/role authorization.",
                },
                {
                    "id": f"{name}.cancel-during-commit",
                    "layer": "security",
                    "assert": "Cancellation race yields a recoverable, authoritative outcome state.",
                },
            ])
        if exposed:
            adversarial.append({
                "id": f"{name}.cross-origin-boundaries",
                "layer": "security",
                "assert": "Unlisted or changed origins cannot discover/use the tool; listed origins still require authorization.",
            })
        if sensitive:
            adversarial.append({
                "id": f"{name}.data-minimization",
                "layer": "security",
                "assert": "Agent sends no undeclared or unnecessary sensitive/cross-site context.",
            })

    if len(validation.get("tools", [])) > 1:
        names = [t.get("name") for t in validation["tools"]]
        agent.extend([
            {
                "id": "toolset.correct-order",
                "layer": "agent",
                "assert": f"Multi-tool workflows use the required order across {names}.",
            },
            {
                "id": "toolset.no-overlap-confusion",
                "layer": "agent",
                "assert": "Near-miss prompts distinguish every neighboring tool pair.",
            },
            {
                "id": "toolset.stop-on-failure",
                "layer": "agent",
                "assert": "A failed prerequisite or declined confirmation stops the chain.",
            },
        ])
        adversarial.append({
            "id": "toolset.read-to-write-injection",
            "layer": "security",
            "assert": "Poisoned read output cannot alter recipient, destination, scope, or selection of a later write.",
        })

    status = "FAIL" if validation.get("status") == "FAIL" else (
        "WARN" if validation.get("status") == "WARN" else "PASS"
    )
    return {
        "status": status,
        "manifestSha256": manifest_hash,
        "validationStatus": validation.get("status"),
        "acceptance": {
            "static": "All declared deterministic cases PASS.",
            "browser": "Target browser discovery, lifecycle, cancellation, origin, and UI cases PASS.",
            "agent": "Declared utility thresholds pass for positive, near-miss, no-tool, arguments, and chains.",
            "security": "Declared attack-success and data-leakage thresholds pass without unacceptable utility loss.",
            "unavailable": "Any unavailable live layer is NOT RUN, never inferred from static results.",
        },
        "suites": {
            "deterministic": deterministic,
            "browser": browser,
            "agent": agent,
            "adversarial": adversarial,
        },
        "counts": {
            "deterministic": len(deterministic),
            "browser": len(browser),
            "agent": len(agent),
            "adversarial": len(adversarial),
        },
    }


def _registration_descriptors(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    descriptors: list[dict[str, Any]] = []
    for item in manifest.get("tools", []):
        descriptor: dict[str, Any] = {
            "name": item["name"],
            "description": item["description"],
            "inputSchema": item["inputSchema"],
            "annotations": item["annotations"],
            "handler": item["handler"],
            "registration": {
                "exposedTo": item.get("registration", {}).get("exposedTo", []),
            },
        }
        if "title" in item:
            descriptor["title"] = item["title"]
        descriptors.append(descriptor)
    return descriptors


def generate_javascript(manifest: dict[str, Any], manifest_hash: str) -> str:
    # The v2 public function remains as a compatibility entry point. Generation
    # is centralized in webmcp_codegen so every framework shares the same
    # handler, cancellation, lifecycle, and JSON-result guarantees.
    try:
        import webmcp_codegen as codegen
    except ImportError:
        from . import webmcp_codegen as codegen  # type: ignore[no-redef]
    return codegen.generate_javascript(manifest, manifest_hash)

    # Retained below only until downstream v2 imports have migrated; unreachable.
    descriptors_json = json.dumps(
        _registration_descriptors(manifest),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    return f"""// Generated by webmcp_toolkit.py {VERSION}.
// Manifest SHA-256: {manifest_hash}
// Build-time semantics are intentionally omitted from browser registration.
// Pass existing, authorization-preserving application handlers to registerWebMCPTools().

export const WEBMCP_MANIFEST_SHA256 = "{manifest_hash}";

const TOOL_DESCRIPTORS = Object.freeze({descriptors_json});

export const WEBMCP_TOOL_NAMES = Object.freeze(
  TOOL_DESCRIPTORS.map((descriptor) => descriptor.name),
);

function abortReason(signal) {{
  if (signal && "reason" in signal && signal.reason !== undefined) {{
    return signal.reason;
  }}
  return new DOMException("The operation was aborted.", "AbortError");
}}

/**
 * Register the generated WebMCP toolset against existing application handlers.
 *
 * @param {{Record<string, Function>}} handlers
 * @param {{{{signal?: AbortSignal}}}} options
 * @returns {{Promise<{{
 *   supported: boolean,
 *   registered: readonly string[],
 *   signal?: AbortSignal,
 *   dispose: (reason?: unknown) => void
 * }} >}}
 */
export async function registerWebMCPTools(handlers, options = {{}}) {{
  const modelContext = globalThis.document?.modelContext;
  if (typeof modelContext?.registerTool !== "function") {{
    return Object.freeze({{
      supported: false,
      registered: Object.freeze([]),
      dispose() {{}},
    }});
  }}

  if (!handlers || typeof handlers !== "object") {{
    throw new TypeError("handlers must be an object keyed by manifest handler names");
  }}

  for (const descriptor of TOOL_DESCRIPTORS) {{
    if (typeof handlers[descriptor.handler] !== "function") {{
      throw new TypeError(
        `Missing WebMCP application handler: ${{descriptor.handler}} for ${{descriptor.name}}`,
      );
    }}
  }}

  const controller = new AbortController();
  const externalSignal = options?.signal;
  let externalAbortListener = null;

  if (externalSignal) {{
    if (externalSignal.aborted) {{
      throw abortReason(externalSignal);
    }}
    externalAbortListener = () => controller.abort(abortReason(externalSignal));
    externalSignal.addEventListener("abort", externalAbortListener, {{ once: true }});
  }}

  const cleanupExternalListener = () => {{
    if (externalSignal && externalAbortListener) {{
      externalSignal.removeEventListener("abort", externalAbortListener);
      externalAbortListener = null;
    }}
  }};

  const registered = [];

  try {{
    for (const descriptor of TOOL_DESCRIPTORS) {{
      const handler = handlers[descriptor.handler];
      const tool = {{
        name: descriptor.name,
        ...(descriptor.title !== undefined ? {{ title: descriptor.title }} : {{}}),
        description: descriptor.description,
        inputSchema: descriptor.inputSchema,
        annotations: descriptor.annotations,
        execute: async (input, executionOptions = {{}}) => {{
          const signal = executionOptions?.signal;
          if (signal?.aborted) {{
            throw abortReason(signal);
          }}
          return await handler(input, {{
            signal,
            toolName: descriptor.name,
          }});
        }},
      }};

      const registrationOptions = {{ signal: controller.signal }};
      if (descriptor.registration.exposedTo.length > 0) {{
        registrationOptions.exposedTo = [...descriptor.registration.exposedTo];
      }}

      await modelContext.registerTool(tool, registrationOptions);
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
    dispose(reason) {{
      if (disposed) return;
      disposed = true;
      controller.abort(reason);
      cleanupExternalListener();
    }},
  }});
}}
"""


def _atomic_write(path: Path, text: str, force: bool) -> None:
    if path.exists() and not force:
        raise ManifestError(f"output exists; use --force to replace: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
        text=True,
    )
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        tmp.replace(path)
    finally:
        if tmp.exists():
            tmp.unlink()


def _print_validation_text(report: dict[str, Any]) -> None:
    summary = report["summary"]
    print(
        f"{report['status']}: {summary['tools']} tool(s), "
        f"{summary['errors']} error(s), {summary['warnings']} warning(s)"
    )
    print(f"Manifest SHA-256: {report['manifestSha256']}")
    for finding in report["findings"]:
        print(
            f"- {finding['severity'].upper()} {finding['code']} "
            f"{finding['path']}: {finding['message']}"
        )
        print(f"  Repair: {finding['remediation']}")


def _emit_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _parse_manifest_and_validate(path_text: str) -> tuple[dict[str, Any], str, dict[str, Any]]:
    path = Path(path_text).expanduser().resolve()
    manifest, manifest_hash = _load_manifest(path)
    try:
        import webmcp_contract as contract
    except ImportError:
        from . import webmcp_contract as contract  # type: ignore[no-redef]

    authoritative = contract.validate_contract(manifest, "toolset")
    # Preserve the detailed v2 tool summaries and mature semantic checks while
    # making the bundled JSON Schema the only structural authority.
    legacy = validate_manifest(manifest, manifest_hash) if authoritative["structuralStatus"] == "PASS" else None
    findings = list(authoritative["findings"])
    seen = {
        (item.get("severity"), item.get("code"), item.get("path"), item.get("message"))
        for item in findings
    }
    if legacy is not None:
        for item in legacy["findings"]:
            key = (item.get("severity"), item.get("code"), item.get("path"), item.get("message"))
            if key in seen:
                continue
            findings.append({**item, "phase": "semantic"})
            seen.add(key)

    errors = sum(item.get("severity") == "error" for item in findings)
    warnings = sum(item.get("severity") == "warning" for item in findings)
    status = "FAIL" if errors else ("WARN" if warnings else "PASS")
    validation = {
        **authoritative,
        "status": status,
        "manifestSha256": manifest_hash,
        "findings": findings,
        "summary": {
            "tools": len(manifest.get("tools", [])) if isinstance(manifest.get("tools"), list) else 0,
            "errors": errors,
            "warnings": warnings,
            "findings": len(findings),
        },
        "tools": legacy["tools"] if legacy is not None else [],
    }
    return manifest, manifest_hash, validation


def _load_builder_module() -> Any:
    try:
        import webmcp_builder as builder
    except ImportError:
        from . import webmcp_builder as builder  # type: ignore[no-redef]
    return builder


def _load_product_module() -> Any:
    try:
        import webmcp_product as product
    except ImportError:
        from . import webmcp_product as product  # type: ignore[no-redef]
    return product


def _load_contract_module() -> Any:
    try:
        import webmcp_contract as contract
    except ImportError:
        from . import webmcp_contract as contract  # type: ignore[no-redef]
    return contract


def _load_dual_module() -> Any:
    try:
        import webmcp_dual as dual
    except ImportError:
        from . import webmcp_dual as dual  # type: ignore[no-redef]
    return dual


def _load_proposals_module() -> Any:
    try:
        import webmcp_proposals as proposals
    except ImportError:
        from . import webmcp_proposals as proposals  # type: ignore[no-redef]
    return proposals


def _load_verify_module() -> Any:
    try:
        import webmcp_verify as verify
    except ImportError:
        from . import webmcp_verify as verify  # type: ignore[no-redef]
    return verify


def _load_selftest_module() -> Any:
    try:
        import webmcp_selftest as selftest
    except ImportError:
        from . import webmcp_selftest as selftest  # type: ignore[no-redef]
    return selftest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="webmcp-toolkit",
        description=(
            "Inspect web repositories, plan and generate framework-aware WebMCP "
            "integrations, validate toolsets, and produce deterministic eval or assurance reports."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan-repo", help="inspect a repository for framework, handler, form, and WebMCP evidence")
    scan.add_argument("repository")
    scan.add_argument("--format", choices=("text", "json"), default="json")
    scan.add_argument("--max-file-bytes", type=int, default=1_000_000)

    compatibility = sub.add_parser(
        "compatibility",
        help="detect current, legacy, declarative, origin, and executeTool compatibility branches",
    )
    compatibility.add_argument("repository")
    compatibility.add_argument("--format", choices=("text", "json"), default="json")

    patch = sub.add_parser(
        "patch-plan",
        help="map manifest handlers into a repository and produce a non-mutating integration plan",
    )
    patch.add_argument("repository")
    patch.add_argument("manifest")
    patch.add_argument(
        "--target",
        choices=("auto", "vanilla-js", "typescript", "react", "next", "vue", "svelte", "angular"),
        default="auto",
    )
    patch.add_argument("--format", choices=("text", "json"), default="json")

    validate_product = sub.add_parser(
        "validate-product",
        help="validate a product profile, its toolset, and capability bindings",
    )
    validate_product.add_argument("product")

    product_plan = sub.add_parser(
        "product-plan",
        help="inspect CREATE/EXTEND capability and real-handler readiness without writing",
    )
    product_plan.add_argument("product")
    product_plan.add_argument(
        "--target",
        choices=("auto", "vanilla-js", "typescript", "react", "next", "vue", "svelte", "angular"),
        default="auto",
    )

    compile_product = sub.add_parser(
        "compile-product",
        help="compile capability-mapped WebMCP adapter artifacts",
    )
    compile_product.add_argument("product")
    compile_product.add_argument(
        "--target",
        choices=("auto", "vanilla-js", "typescript", "react", "next", "vue", "svelte", "angular"),
        default="auto",
    )
    compile_product.add_argument("--output-dir")
    compile_product.add_argument("--write", action="store_true")
    compile_product.add_argument("--force", action="store_true")

    dual = sub.add_parser(
        "dual-check",
        help="validate a WebMCP/MCP map over shared canonical operations",
    )
    dual.add_argument("contract")

    proposal_status = sub.add_parser(
        "proposal-status",
        help="report declarative or Service Worker proposal maturity without compatibility claims",
    )
    proposal_status.add_argument("--kind", choices=("declarative", "service-worker"))

    proposal_generate = sub.add_parser(
        "generate-proposal",
        help="render an explicitly proposal-only artifact and status sidecar",
    )
    proposal_generate.add_argument("kind", choices=("declarative", "service-worker"))
    proposal_generate.add_argument("--output-dir", required=True)
    proposal_generate.add_argument("--tool-name", required=True)
    proposal_generate.add_argument("--description", required=True)
    proposal_generate.add_argument("--auto-submit", action="store_true")
    proposal_generate.add_argument("--force", action="store_true")

    verification_plan = sub.add_parser(
        "verification-plan",
        help="emit evidence gates for the selected product and release profile",
    )
    verification_plan.add_argument("product")

    source_status = sub.add_parser(
        "source-status",
        help="evaluate freshness and canonical binding of official WebMCP sources",
    )
    source_status.add_argument("product")
    source_status.add_argument("--ledger")
    source_status.add_argument("--source-refresh")
    source_status.add_argument("--repository-root")
    source_status.add_argument("--as-of")
    source_status.add_argument("--max-age-days", type=int)

    for command_name, command_help, require_release in (
        ("verify", "produce candidate-bound layered verification evidence", False),
        ("release-check", "apply the full release contract to candidate-bound evidence", True),
    ):
        command = sub.add_parser(command_name, help=command_help)
        command.add_argument("product")
        command.add_argument("toolset")
        command.add_argument("--release", required=require_release)
        command.add_argument("--receipts")
        command.add_argument("--source-refresh")
        command.add_argument("--ledger")
        command.add_argument("--repository-root")
        command.add_argument("--repository-revision")
        command.add_argument("--dirty", choices=("true", "false"))
        command.add_argument("--as-of")
        command.add_argument("--source-max-age-days", type=int)
        command.add_argument("--output")
        command.add_argument("--evidence-output")
        command.add_argument("--format", choices=("json", "text"), default="json")

    self_test = sub.add_parser(
        "self-test",
        help="run deterministic package-local verification without claiming native-host evidence",
    )
    self_test.add_argument("--profile", choices=("core", "full"), default="core")
    self_test.add_argument("--format", choices=("json", "text"), default="json")
    self_test.add_argument("--timeout-seconds", type=int, default=300)
    self_test.add_argument("--output")

    validate = sub.add_parser("validate", help="validate a webmcp-toolset.v1 manifest")
    validate.add_argument("manifest")
    validate.add_argument("--format", choices=("text", "json"), default="text")
    validate.add_argument(
        "--fail-on-warn",
        action="store_true",
        help="return a non-zero exit status when warnings remain",
    )

    threat = sub.add_parser("threat-model", help="produce a deterministic, proportionate threat model")
    threat.add_argument("manifest")
    threat.add_argument("--format", choices=("text", "json"), default="json")

    evaluate = sub.add_parser("eval-plan", help="produce deterministic repository/browser/agent/security test cases")
    evaluate.add_argument("manifest")
    evaluate.add_argument("--format", choices=("text", "json"), default="json")

    generate = sub.add_parser(
        "generate",
        help="generate a portable or framework-lifecycle WebMCP adapter around existing handlers",
    )
    generate.add_argument("manifest")
    generate.add_argument(
        "--target",
        choices=("vanilla-js", "typescript", "react", "next", "vue", "svelte", "angular"),
        default="vanilla-js",
    )
    generate.add_argument("--output", help="destination JavaScript/TypeScript path")
    generate.add_argument("--write", action="store_true", help="write output; otherwise preview")
    generate.add_argument("--force", action="store_true", help="replace an existing output")
    generate.add_argument("--format", choices=("code", "json"), default="code")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    builder = _load_builder_module()
    try:
        if args.command == "scan-repo":
            if args.max_file_bytes < 1:
                raise ManifestError("--max-file-bytes must be at least 1")
            report = builder.scan_repository(
                args.repository,
                max_file_bytes=args.max_file_bytes,
            )
            if args.format == "json":
                _emit_json(report)
            else:
                print(builder.text_summary(report))
            return 0

        if args.command == "compatibility":
            report = builder.compatibility_report(args.repository)
            if args.format == "json":
                _emit_json(report)
            else:
                print(builder.text_summary(report))
            return 1 if report["status"] == "FAIL" else 0

        if args.command in {"validate-product", "product-plan", "compile-product"}:
            product_module = _load_product_module()
            contract_module = _load_contract_module()
            try:
                if args.command == "validate-product":
                    product, toolset, _, _, _ = product_module.load_product_bundle(args.product)
                    report = contract_module.validate_bundle(product, toolset)
                elif args.command == "product-plan":
                    product, toolset, _, _, application_root = product_module.load_product_bundle(
                        args.product
                    )
                    report = product_module.build_plan(
                        product, toolset, application_root, args.target
                    )
                else:
                    report = product_module.compile_product(
                        args.product,
                        target=args.target,
                        output_dir=args.output_dir,
                        write=args.write,
                        force=args.force,
                    )
            except (
                product_module.ProductCompilerError,
                contract_module.ContractInputError,
                builder.BuilderError,
            ) as exc:
                raise ManifestError(str(exc)) from exc
            _emit_json(report)
            return 1 if report.get("status") in {"FAIL", "BLOCKED"} else 0

        if args.command == "dual-check":
            dual_module = _load_dual_module()
            try:
                report = dual_module.validate_file(args.contract)
            except dual_module.DualContractError as exc:
                raise ManifestError(str(exc)) from exc
            _emit_json(report)
            return 1 if report.get("status") == "FAIL" else 0

        if args.command == "proposal-status":
            proposals = _load_proposals_module()
            _emit_json(proposals.proposal_status(args.kind))
            return 0

        if args.command == "generate-proposal":
            proposals = _load_proposals_module()
            try:
                report = proposals.generate_proposal(
                    args.kind,
                    output_dir=Path(args.output_dir),
                    tool_name=args.tool_name,
                    description=args.description,
                    auto_submit=args.auto_submit,
                    force=args.force,
                )
            except (OSError, proposals.ProposalError) as exc:
                raise ManifestError(str(exc)) from exc
            _emit_json(report)
            return 0

        if args.command in {"verification-plan", "source-status", "verify", "release-check"}:
            verify_module = _load_verify_module()
            if args.command == "verification-plan":
                return verify_module.main(["plan", "--product", args.product])
            if args.command == "source-status":
                forwarded = ["source-status", "--product", args.product]
                for option, value in (
                    ("--ledger", args.ledger),
                    ("--source-refresh", args.source_refresh),
                    ("--repository-root", args.repository_root),
                    ("--as-of", args.as_of),
                    ("--max-age-days", args.max_age_days),
                ):
                    if value is not None:
                        forwarded.extend([option, str(value)])
                return verify_module.main(forwarded)

            forwarded = [
                "verify",
                "--product", args.product,
                "--toolset", args.toolset,
                "--format", args.format,
            ]
            for option, value in (
                ("--release", args.release),
                ("--receipts", args.receipts),
                ("--source-refresh", args.source_refresh),
                ("--ledger", args.ledger),
                ("--repository-root", args.repository_root),
                ("--repository-revision", args.repository_revision),
                ("--dirty", args.dirty),
                ("--as-of", args.as_of),
                ("--source-max-age-days", args.source_max_age_days),
                ("--output", args.output),
                ("--evidence-output", args.evidence_output),
            ):
                if value is not None:
                    forwarded.extend([option, str(value)])
            return verify_module.main(forwarded)

        if args.command == "self-test":
            selftest = _load_selftest_module()
            forwarded = [
                "--profile", args.profile,
                "--format", args.format,
                "--timeout-seconds", str(args.timeout_seconds),
            ]
            if args.output:
                forwarded.extend(["--output", args.output])
            return selftest.main(forwarded)

        manifest, manifest_hash, validation = _parse_manifest_and_validate(args.manifest)

        if args.command == "validate":
            if args.format == "json":
                _emit_json(validation)
            else:
                _print_validation_text(validation)
            if validation["status"] == "FAIL":
                return 1
            if args.fail_on_warn and validation["status"] == "WARN":
                return 3
            return 0

        if validation["status"] == "FAIL":
            _emit_json({
                "status": "FAIL",
                "message": "Manifest validation failed; repair errors before this operation.",
                "validation": validation,
            })
            return 1

        if args.command == "patch-plan":
            report = builder.patch_plan(args.repository, manifest, args.target)
            report["manifestSha256"] = manifest_hash
            report["validationStatus"] = validation["status"]
            if args.format == "json":
                _emit_json(report)
            else:
                print(builder.text_summary(report))
            return 1 if report["status"] == "BLOCKED" else 0

        if args.command == "threat-model":
            report = build_threat_model(manifest, manifest_hash, validation)
            if args.format == "json":
                _emit_json(report)
            else:
                print(
                    f"{report['status']}: {report['scope']['tools']} tool(s), "
                    f"{report['scope']['risks']} modeled risk(s)"
                )
                for risk in report["globalRisks"] + report["toolRisks"]:
                    prefix = f"{risk.get('tool')}: " if risk.get("tool") else ""
                    print(f"- {risk['severity'].upper()} {prefix}{risk['id']}: {risk['condition']}")
            return 0

        if args.command == "eval-plan":
            report = build_eval_plan(manifest, manifest_hash, validation)
            if args.format == "json":
                _emit_json(report)
            else:
                print(f"{report['status']}: evaluation plan for {len(validation['tools'])} tool(s)")
                for name, count in report["counts"].items():
                    print(f"- {name}: {count} case(s)")
            return 0

        if args.command == "generate":
            code = builder.generate_target(
                manifest,
                manifest_hash,
                args.target,
                generate_javascript,
            )
            code_hash = _sha256_bytes(code.encode("utf-8"))
            if args.write:
                if not args.output:
                    raise ManifestError("--output is required with --write")
                output = Path(args.output).expanduser().resolve()
                _atomic_write(output, code, args.force)
                report = {
                    "status": "PASS",
                    "operation": "generate",
                    "target": args.target,
                    "manifestSha256": manifest_hash,
                    "artifactSha256": code_hash,
                    "output": str(output),
                    "bytes": output.stat().st_size,
                    "validationStatus": validation["status"],
                }
                _emit_json(report)
            elif args.format == "json":
                _emit_json({
                    "status": "PREVIEW",
                    "operation": "generate",
                    "target": args.target,
                    "manifestSha256": manifest_hash,
                    "artifactSha256": code_hash,
                    "validationStatus": validation["status"],
                    "code": code,
                })
            else:
                sys.stdout.write(code)
            return 0

        raise ManifestError(f"unsupported command: {args.command}")
    except (ManifestError, builder.BuilderError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("ERROR: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
