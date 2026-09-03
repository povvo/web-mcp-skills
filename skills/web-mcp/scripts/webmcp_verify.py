#!/usr/bin/env python3
"""Evidence-driven WebMCP verification and release gating.

This module deliberately separates deterministic checks from WPT, browser,
agent, and host-native evidence.  External behavior is never inferred from a
local shim or from the presence of a configuration file: a candidate-bound
receipt is required before an external gate can pass.
"""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import parse_qs, urlparse


SCRIPT_ROOT = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_ROOT.parent
REPOSITORY_ROOT = SKILL_ROOT.parents[1]
DEFAULT_LEDGER = SKILL_ROOT / "assets" / "sources" / "official-materials.json"

if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

import webmcp_contract as contract  # noqa: E402


STATUSES = ("PASS", "FAIL", "BLOCKED", "UNSUPPORTED", "NOT_RUN")
EVIDENCE_CLASSES = (
    "deterministic",
    "source",
    "wpt",
    "browser",
    "agent",
    "host-native",
    "dual",
    "deployment",
    "package",
    "challenge",
    "release",
)
STATUS_EXIT_CODES = {
    "PASS": 0,
    "FAIL": 1,
    "BLOCKED": 2,
    "UNSUPPORTED": 3,
    "NOT_RUN": 4,
}
STATUS_PRECEDENCE = ("FAIL", "BLOCKED", "NOT_RUN", "UNSUPPORTED", "PASS")


class VerificationInputError(ValueError):
    """Raised when a verification input cannot be interpreted honestly."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _read_json(path: str | Path) -> dict[str, Any]:
    resolved = Path(path).expanduser().resolve()
    try:
        value = json.loads(resolved.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise VerificationInputError(f"JSON input does not exist: {resolved}") from exc
    except json.JSONDecodeError as exc:
        raise VerificationInputError(
            f"Invalid JSON in {resolved}: line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(value, dict):
        raise VerificationInputError(f"JSON input must be an object: {resolved}")
    return value


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _parse_datetime(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise VerificationInputError(f"{label} must be a non-empty ISO-8601 date or date-time.")
    normalized = value.strip()
    if len(normalized) == 10:
        try:
            parsed_date = date.fromisoformat(normalized)
        except ValueError as exc:
            raise VerificationInputError(f"{label} is not a valid ISO date: {value!r}") from exc
        return datetime(
            parsed_date.year, parsed_date.month, parsed_date.day, tzinfo=timezone.utc
        )
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as exc:
        raise VerificationInputError(f"{label} is not a valid ISO date-time: {value!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _is_https_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def _is_youtube_video_url(value: object) -> bool:
    """Return whether value identifies a video on an official YouTube host."""

    if not _is_https_url(value):
        return False
    parsed = urlparse(str(value))
    host = (parsed.hostname or "").lower()
    if host == "youtu.be":
        return bool(parsed.path.strip("/"))
    if host not in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        return False
    if parsed.path == "/watch":
        return bool(parse_qs(parsed.query).get("v", [""])[0].strip())
    return parsed.path.startswith(("/shorts/", "/live/")) and bool(
        parsed.path.split("/", 2)[-1].strip("/")
    )


def aggregate_status(results: Iterable[Mapping[str, Any]], *, required_only: bool) -> str:
    selected = [
        item
        for item in results
        if not required_only or item.get("required") is True
    ]
    if not selected:
        return "PASS"
    statuses = {item.get("status") for item in selected}
    for status in STATUS_PRECEDENCE:
        if status in statuses:
            return status
    return "FAIL"


def _counts(results: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    counted = Counter(str(item.get("status")) for item in results)
    return {status: counted.get(status, 0) for status in STATUSES}


def _git_identity(repository_root: Path) -> tuple[str, bool]:
    def run(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=repository_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )

    try:
        revision_result = run("rev-parse", "HEAD")
        revision = revision_result.stdout.strip() if revision_result.returncode == 0 else "uncommitted"
        dirty_result = run("status", "--porcelain")
        dirty = dirty_result.returncode != 0 or bool(dirty_result.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        return "git-unavailable", True
    return revision or "uncommitted", dirty


def _candidate(
    product: Mapping[str, Any],
    toolset: Mapping[str, Any],
    *,
    generated_at: datetime,
    repository_root: Path,
    repository_revision: str | None = None,
    dirty: bool | None = None,
) -> dict[str, Any]:
    observed_revision, observed_dirty = _git_identity(repository_root)
    return {
        "productSha256": contract.sha256_json(product),
        "toolsetSha256": contract.sha256_json(toolset),
        "repositoryRevision": repository_revision or observed_revision,
        "dirty": observed_dirty if dirty is None else dirty,
        "generatedAt": _iso(generated_at),
    }


def _profile_targets(product: Mapping[str, Any]) -> list[str]:
    targets = [str(item) for item in product.get("targets", []) if isinstance(item, str)]
    if product.get("surface") == "dual" and "mcp" not in targets:
        targets.append("mcp")
    profiles = product.get("profiles", {})
    worker = profiles.get("serviceWorkerProposal", {}) if isinstance(profiles, dict) else {}
    if isinstance(worker, dict) and worker.get("enabled") is True:
        targets.append("service-worker-proposal")
    return list(dict.fromkeys(targets))


def _source_ids_for(product: Mapping[str, Any]) -> list[str]:
    selected = {
        "webmcp-draft-spec",
        "webmcp-explainer",
        "webmcp-security-questionnaire",
        "webmcp-implementation-status",
    }
    targets = set(_profile_targets(product))
    release = product.get("release")
    profiles = product.get("profiles", {})
    if "chatgpt-site-tools" in targets:
        selected.add("openai-site-tools")
    if targets.intersection({"webmcp-document", "chromium-webmcp"}):
        selected.update({"webmcp-wpt", "webmcp-types"})
    if "chromium-webmcp" in targets:
        selected.add("chrome-webmcp-evals")
    if product.get("surface") == "dual":
        selected.add("mcp-architecture")
    if isinstance(profiles, dict):
        declarative = profiles.get("declarativeProposal", {})
        if isinstance(declarative, dict) and declarative.get("enabled") is True:
            selected.add("webmcp-declarative-explainer")
        worker = profiles.get("serviceWorkerProposal", {})
        if isinstance(worker, dict) and worker.get("enabled") is True:
            selected.add("webmcp-service-worker-explainer")
    if release == "challenge":
        selected.update(
            {
                "openai-webmcp-challenge",
                "openai-webmcp-challenge-rules",
                "openai-webmcp-showcase",
            }
        )
    return sorted(selected)


def _source_freshness_days(release: object) -> int:
    if release == "challenge":
        return 1
    if release == "production":
        return 7
    return 30


def _normalize_evidence(value: object) -> tuple[list[dict[str, Any]], list[str]]:
    findings: list[str] = []
    normalized: list[dict[str, Any]] = []
    if not isinstance(value, list):
        return [], ["evidence must be an array"]
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            findings.append(f"evidence[{index}] must be an object")
            continue
        kind = item.get("kind")
        evidence_value = item.get("value")
        if kind not in {"file", "command", "url", "screenshot", "log", "receipt", "note"}:
            findings.append(f"evidence[{index}].kind is invalid")
            continue
        if not isinstance(evidence_value, str) or not evidence_value.strip():
            findings.append(f"evidence[{index}].value must be non-empty")
            continue
        entry: dict[str, Any] = {"kind": kind, "value": evidence_value}
        sha = item.get("sha256")
        if sha is not None:
            if not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
                findings.append(f"evidence[{index}].sha256 is not a lowercase SHA-256")
            else:
                entry["sha256"] = sha
        normalized.append(entry)
    return normalized, findings


def evaluate_source_status(
    product: Mapping[str, Any],
    *,
    ledger: Mapping[str, Any],
    repository_root: Path,
    as_of: datetime,
    refresh: Mapping[str, Any] | None = None,
    max_age_days: int | None = None,
) -> dict[str, Any]:
    """Evaluate source availability/freshness without fabricating a live refresh."""

    release = product.get("release")
    freshness_days = max_age_days if max_age_days is not None else _source_freshness_days(release)
    requested = set(_source_ids_for(product))
    ledger_sources = {
        item.get("id"): item
        for item in ledger.get("sources", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    refresh_items: dict[str, Mapping[str, Any]] = {}
    refresh_errors: list[str] = []
    if refresh is not None:
        if refresh.get("schemaVersion") != "webmcp-source-refresh.v1":
            refresh_errors.append("source refresh schemaVersion must be webmcp-source-refresh.v1")
        items = refresh.get("sources")
        if not isinstance(items, list):
            refresh_errors.append("source refresh sources must be an array")
        else:
            for index, item in enumerate(items):
                if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                    refresh_errors.append(f"source refresh sources[{index}] has no valid id")
                    continue
                source_id = str(item["id"])
                if source_id in refresh_items:
                    refresh_errors.append(f"duplicate source refresh receipt: {source_id}")
                refresh_items[source_id] = item

    results: list[dict[str, Any]] = []
    for source_id in sorted(requested):
        source = ledger_sources.get(source_id)
        if source is None:
            results.append(
                {
                    "id": source_id,
                    "status": "FAIL",
                    "reason": "The required source is absent from official-materials.json.",
                    "evidence": [],
                }
            )
            continue
        canonical_url = source.get("canonicalUrl")
        result: dict[str, Any] = {
            "id": source_id,
            "title": source.get("title"),
            "canonicalUrl": canonical_url,
            "authority": source.get("authority"),
            "maturity": source.get("maturity"),
            "ledgerVerifiedAt": ledger.get("verifiedAt"),
            "liveRefreshRequired": source.get("liveRefreshRequired") is True,
            "evidence": [],
        }
        receipt = refresh_items.get(source_id)
        if receipt is None:
            if source.get("liveRefreshRequired") is True:
                result.update(
                    status="NOT_RUN",
                    reason=(
                        "No candidate-time refresh receipt was supplied for this mutable official source; "
                        "the ledger snapshot is not a current-support claim."
                    ),
                )
            else:
                result.update(
                    status="PASS",
                    evidence=[{"kind": "url", "value": str(canonical_url)}],
                )
            results.append(result)
            continue

        status = receipt.get("status")
        reason = receipt.get("reason")
        evidence, evidence_findings = _normalize_evidence(receipt.get("evidence", []))
        receipt_errors: list[str] = list(evidence_findings)
        if status not in STATUSES:
            receipt_errors.append(f"invalid status {status!r}")
        if receipt.get("canonicalUrl") != canonical_url:
            receipt_errors.append("canonicalUrl does not match official-materials.json")
        checked_at: datetime | None = None
        try:
            checked_at = _parse_datetime(receipt.get("checkedAt"), f"source {source_id} checkedAt")
        except VerificationInputError as exc:
            receipt_errors.append(str(exc))
        if status == "PASS":
            if not evidence:
                receipt_errors.append("PASS source receipt has no evidence")
            if not any(item["kind"] == "url" and item["value"] == canonical_url for item in evidence):
                receipt_errors.append("PASS source receipt must cite the exact canonical URL")
            if checked_at is not None:
                age_days = (as_of - checked_at).total_seconds() / 86400
                if age_days < -1 / 24:
                    receipt_errors.append("checkedAt is in the future")
                elif age_days > freshness_days:
                    result.update(
                        status="NOT_RUN",
                        checkedAt=_iso(checked_at),
                        reason=(
                            f"The source receipt is {age_days:.1f} days old; this {release} profile "
                            f"requires a refresh no older than {freshness_days} day(s)."
                        ),
                        evidence=evidence,
                    )
                    results.append(result)
                    continue
        elif status in {"FAIL", "BLOCKED", "UNSUPPORTED", "NOT_RUN"}:
            if not isinstance(reason, str) or not reason.strip():
                receipt_errors.append(f"{status} source receipt requires a reason")
            if status in {"FAIL", "BLOCKED", "UNSUPPORTED"} and not evidence:
                receipt_errors.append(f"{status} source receipt requires observed evidence")
        if receipt_errors:
            result.update(
                status="FAIL",
                reason="Invalid source refresh receipt: " + "; ".join(receipt_errors),
                evidence=evidence,
            )
        else:
            result["status"] = status
            result["checkedAt"] = _iso(checked_at) if checked_at is not None else None
            result["evidence"] = evidence
            if isinstance(reason, str) and reason.strip():
                result["reason"] = reason.strip()
        results.append(result)

    if refresh_errors:
        results.insert(
            0,
            {
                "id": "source-refresh-document",
                "status": "FAIL",
                "reason": "; ".join(refresh_errors),
                "evidence": [],
            },
        )
    source_status = aggregate_status(
        ({**item, "required": True} for item in results), required_only=True
    )
    return {
        "schemaVersion": "webmcp-source-status.v1",
        "asOf": _iso(as_of),
        "release": release,
        "freshnessDays": freshness_days,
        "status": source_status,
        "counts": _counts(results),
        "sources": results,
    }


def gate_plan(product: Mapping[str, Any]) -> list[dict[str, Any]]:
    release = product.get("release")
    production_bar = release in {"production", "challenge"}
    targets = set(_profile_targets(product))
    document_or_chromium = bool(targets.intersection({"webmcp-document", "chromium-webmcp"}))
    specs: list[dict[str, Any]] = [
        {
            "id": "contract",
            "evidenceClass": "deterministic",
            "required": True,
            "automated": True,
            "instruction": "Validate product, toolset, and supplied release contracts.",
        },
        {
            "id": "deterministic.lifecycle",
            "evidenceClass": "deterministic",
            "required": True,
            "automated": False,
            "instruction": "Run handler preflight, registration rollback, cancellation, route, navigation, and BFCache tests.",
        },
        {
            "id": "deterministic.serialization",
            "evidenceClass": "deterministic",
            "required": True,
            "automated": False,
            "instruction": "Prove callback results serialize and invalid values fail before a false success is reported.",
        },
        {
            "id": "source.official",
            "evidenceClass": "source",
            "required": production_bar,
            "automated": True,
            "instruction": "Refresh every mutable official source relevant to the selected profile.",
        },
    ]
    if document_or_chromium:
        specs.extend(
            [
                {
                    "id": "wpt.webmcp",
                    "evidenceClass": "wpt",
                    "required": production_bar,
                    "automated": False,
                    "instruction": "Run the pinned upstream WebMCP WPT corpus in the claimed browser build.",
                },
                {
                    "id": "browser.discovery",
                    "evidenceClass": "browser",
                    "required": production_bar,
                    "automated": False,
                    "instruction": "Record browser-native tool discovery, schema, invocation, lifecycle, and status output.",
                },
                {
                    "id": "browser.shared-state",
                    "evidenceClass": "browser",
                    "required": production_bar,
                    "automated": False,
                    "instruction": "Prove normal UI and WebMCP operations update the same visible/durable application state.",
                },
            ]
        )
    specs.extend(
        [
            {
                "id": "agent.selection",
                "evidenceClass": "agent",
                "required": production_bar,
                "automated": False,
                "minimumRuns": 5,
                "minimumThreshold": 0.8,
                "instruction": "Run repeated positive, distractor, insufficient-information, and no-tool selection cases.",
            },
            {
                "id": "agent.multistep",
                "evidenceClass": "agent",
                "required": production_bar,
                "automated": False,
                "minimumRuns": 5,
                "minimumThreshold": 0.8,
                "instruction": "Run ordered/unordered journeys where results and dynamic tool state feed later steps.",
            },
            {
                "id": "agent.failure-recovery",
                "evidenceClass": "agent",
                "required": production_bar,
                "automated": False,
                "minimumRuns": 5,
                "minimumThreshold": 0.8,
                "instruction": "Inject retryable, terminal, cancellation, stale-state, and uncertain-write failures.",
            },
        ]
    )
    if "chromium-webmcp" in targets:
        specs.append(
            {
                "id": "native.chrome",
                "evidenceClass": "host-native",
                "host": "chromium-webmcp",
                "required": production_bar,
                "automated": False,
                "instruction": "Capture headed Chrome DevTools WebMCP discovery and invocation receipts.",
            }
        )
    if "chatgpt-site-tools" in targets:
        specs.append(
            {
                "id": "native.chatgpt",
                "evidenceClass": "host-native",
                "host": "chatgpt-site-tools",
                "required": production_bar,
                "automated": False,
                "instruction": "Capture native ChatGPT Site Tools availability, invocation, source, and visible-effect receipts.",
            }
        )
    if product.get("surface") == "dual":
        specs.append(
            {
                "id": "dual.composition",
                "evidenceClass": "dual",
                "required": True,
                "automated": False,
                "instruction": "Run one candidate-bound host journey using independent WebMCP and MCP tools over the same domain contract.",
            }
        )
    profiles = product.get("profiles", {})
    worker = profiles.get("serviceWorkerProposal", {}) if isinstance(profiles, dict) else {}
    worker_enabled = isinstance(worker, dict) and worker.get("enabled") is True
    specs.append(
        {
            "id": "service-worker.proposal",
            "evidenceClass": "browser",
            "required": worker_enabled,
            "automated": False,
            "instruction": (
                "Name the implementing target and execute background routing and UI-handoff tests, "
                "or attach official evidence for UNSUPPORTED."
            ),
        }
    )
    if production_bar:
        specs.extend(
            [
                {
                    "id": "deployment.live",
                    "evidenceClass": "deployment",
                    "required": True,
                    "automated": False,
                    "instruction": "Verify the exact deployed candidate, normal UI, authentication path, and WebMCP surface.",
                },
                {
                    "id": "package.clean-install",
                    "evidenceClass": "package",
                    "required": True,
                    "automated": False,
                    "instruction": "Extract the release artifact into a clean directory and run install, build, and tests.",
                },
                {
                    "id": "release.local-materials",
                    "evidenceClass": "release",
                    "required": True,
                    "automated": True,
                    "instruction": "Validate release metadata and required local license/run files.",
                },
                {
                    "id": "release.claim-bindings",
                    "evidenceClass": "release",
                    "required": True,
                    "automated": True,
                    "instruction": "Require every public claim and compatibility statement to cite passing evidence gates.",
                },
            ]
        )
    if release == "challenge":
        specs.append(
            {
                "id": "challenge.public-assets",
                "evidenceClass": "challenge",
                "required": True,
                "automated": False,
                "instruction": (
                    "Verify the public live app; the public repository with source code, assets, "
                    "run instructions, and open-source license; and a public YouTube demo video "
                    "with audio that is strictly under three minutes."
                ),
            }
        )
    return specs


def _receipt_binding(
    receipts: Mapping[str, Any] | None,
    candidate: Mapping[str, Any],
    known_gate_ids: set[str],
    automated_gate_ids: set[str],
) -> tuple[dict[str, Mapping[str, Any]], dict[str, Any] | None]:
    if receipts is None:
        return {}, None
    errors: list[str] = []
    if receipts.get("schemaVersion") != "webmcp-verification-receipts.v1":
        errors.append("schemaVersion must be webmcp-verification-receipts.v1")
    receipt_candidate = receipts.get("candidate")
    if not isinstance(receipt_candidate, dict):
        errors.append("candidate binding is required")
    else:
        for field in ("productSha256", "toolsetSha256"):
            if receipt_candidate.get(field) != candidate.get(field):
                errors.append(f"candidate {field} does not identify this verification candidate")
    mapped: dict[str, Mapping[str, Any]] = {}
    items = receipts.get("receipts")
    if not isinstance(items, list):
        errors.append("receipts must be an array")
    else:
        for index, item in enumerate(items):
            if not isinstance(item, dict) or not isinstance(item.get("gateId"), str):
                errors.append(f"receipts[{index}] has no valid gateId")
                continue
            gate_id = str(item["gateId"])
            if gate_id not in known_gate_ids:
                errors.append(f"receipt references unknown gate {gate_id!r}")
            elif gate_id in automated_gate_ids:
                errors.append(f"receipt cannot override automated gate {gate_id!r}")
            if gate_id in mapped:
                errors.append(f"duplicate receipt for gate {gate_id!r}")
            mapped[gate_id] = item
    if errors:
        return {}, {
            "id": "receipt.binding",
            "evidenceClass": "deterministic",
            "status": "FAIL",
            "required": True,
            "automated": True,
            "reason": "; ".join(errors),
            "evidence": [{"kind": "note", "value": "External receipts were rejected before use."}],
            "details": {"findings": errors},
        }
    return mapped, {
        "id": "receipt.binding",
        "evidenceClass": "deterministic",
        "status": "PASS",
        "required": True,
        "automated": True,
        "evidence": [{"kind": "note", "value": "External receipts match the product and toolset hashes."}],
        "details": {"receiptCount": len(mapped)},
    }


def _receipt_result(spec: Mapping[str, Any], receipt: Mapping[str, Any]) -> dict[str, Any]:
    status = receipt.get("status")
    reason = receipt.get("reason")
    evidence, errors = _normalize_evidence(receipt.get("evidence", []))
    environment = receipt.get("environment")
    if status not in STATUSES:
        errors.append(f"invalid status {status!r}")
    if not isinstance(environment, dict):
        environment = {}
    if status == "PASS" and not evidence:
        errors.append("PASS requires at least one evidence item")
    if status in {"FAIL", "BLOCKED", "UNSUPPORTED", "NOT_RUN"} and not (
        isinstance(reason, str) and reason.strip()
    ):
        errors.append(f"{status} requires a reason")
    if status in {"FAIL", "BLOCKED", "UNSUPPORTED"} and not evidence:
        errors.append(f"{status} requires observed evidence")
    if status == "BLOCKED" and not isinstance(receipt.get("attemptedAt"), str):
        errors.append("BLOCKED requires attemptedAt")
    if status == "UNSUPPORTED" and not any(item["kind"] == "url" for item in evidence):
        errors.append("UNSUPPORTED requires an official URL evidence item")
    if status == "PASS" and isinstance(receipt.get("exitCode"), int) and receipt["exitCode"] != 0:
        errors.append("PASS cannot have a non-zero exitCode")

    evidence_class = spec.get("evidenceClass")
    if status == "PASS" and evidence_class == "deterministic":
        if not isinstance(receipt.get("command"), str) or not receipt["command"].strip():
            errors.append("deterministic PASS requires the executed command")
        if receipt.get("exitCode") != 0:
            errors.append("deterministic PASS requires exitCode=0")
        if not any(item["kind"] in {"log", "receipt", "file"} for item in evidence):
            errors.append("deterministic PASS requires a log, receipt, or file")
    elif status == "PASS" and evidence_class == "wpt":
        for field in ("browserVersion", "wptRevision", "command"):
            if not isinstance(environment.get(field), str) or not environment[field].strip():
                errors.append(f"WPT PASS requires environment.{field}")
        if not any(item["kind"] in {"log", "receipt", "file"} for item in evidence):
            errors.append("WPT PASS requires a log, receipt, or file")
    elif status == "PASS" and evidence_class == "browser":
        for field in ("browserVersion", "featureState"):
            if not isinstance(environment.get(field), str) or not environment[field].strip():
                errors.append(f"browser PASS requires environment.{field}")
        if not any(item["kind"] in {"screenshot", "log", "receipt"} for item in evidence):
            errors.append("browser PASS requires a screenshot, log, or receipt")
    elif status == "PASS" and evidence_class == "agent":
        for field in ("model", "backend"):
            if not isinstance(environment.get(field), str) or not environment[field].strip():
                errors.append(f"agent PASS requires environment.{field}")
        runs = environment.get("runs")
        passed = environment.get("passedRuns")
        threshold = environment.get("threshold")
        if not isinstance(runs, int) or isinstance(runs, bool) or runs < 1:
            errors.append("agent PASS requires positive integer environment.runs")
        elif runs < int(spec.get("minimumRuns", 1)):
            errors.append(f"agent PASS requires at least {spec.get('minimumRuns')} runs")
        if not isinstance(passed, int) or isinstance(passed, bool) or passed < 0:
            errors.append("agent PASS requires non-negative integer environment.passedRuns")
        if not isinstance(threshold, (int, float)) or isinstance(threshold, bool) or not 0 <= threshold <= 1:
            errors.append("agent PASS requires environment.threshold between 0 and 1")
        elif threshold < float(spec.get("minimumThreshold", 0)):
            errors.append(
                f"agent PASS threshold is below the gate minimum {spec.get('minimumThreshold')}"
            )
        if isinstance(runs, int) and runs > 0 and isinstance(passed, int) and isinstance(threshold, (int, float)):
            if passed > runs:
                errors.append("agent passedRuns cannot exceed runs")
            elif passed / runs < threshold:
                errors.append("agent observed pass rate is below threshold")
        if environment.get("stopViolations", 0) != 0:
            errors.append("agent PASS requires zero stopViolations")
        if not any(item["kind"] in {"log", "receipt"} for item in evidence):
            errors.append("agent PASS requires a trajectory log or receipt")
    elif status == "PASS" and evidence_class == "host-native":
        expected_host = spec.get("host")
        if environment.get("host") != expected_host:
            errors.append(f"host-native PASS requires environment.host={expected_host!r}")
        if not isinstance(environment.get("hostVersion"), str) or not environment["hostVersion"].strip():
            errors.append("host-native PASS requires environment.hostVersion")
        if expected_host == "chatgpt-site-tools" and (
            not isinstance(environment.get("model"), str) or not environment["model"].strip()
        ):
            errors.append("ChatGPT host-native PASS requires the exact model")
        if not any(item["kind"] in {"screenshot", "receipt"} for item in evidence):
            errors.append("host-native PASS requires a screenshot or native receipt")
    elif status == "PASS" and evidence_class == "package":
        artifact_sha = environment.get("artifactSha256")
        if not isinstance(artifact_sha, str) or len(artifact_sha) != 64:
            errors.append("package PASS requires environment.artifactSha256")
        if not any(item["kind"] in {"receipt", "log"} for item in evidence):
            errors.append("package PASS requires clean-extraction receipt or log")
    elif status == "PASS" and evidence_class == "deployment":
        if not _is_https_url(environment.get("url")):
            errors.append("deployment PASS requires an HTTPS environment.url")
    elif status == "PASS" and evidence_class == "challenge":
        for field in ("liveUrl", "sourceRepository"):
            if not _is_https_url(environment.get(field)):
                errors.append(f"challenge PASS requires HTTPS environment.{field}")
        if not _is_youtube_video_url(environment.get("demoUrl")):
            errors.append("challenge PASS requires environment.demoUrl to identify a public YouTube video")
        for field in ("liveUrlPublic", "sourceRepositoryPublic", "demoPublic"):
            if environment.get(field) is not True:
                errors.append(f"challenge PASS requires environment.{field}=true")
        repository_contents = environment.get("repositoryContents")
        required_contents = (
            "sourceCode",
            "assets",
            "runInstructions",
            "openSourceLicense",
        )
        if not isinstance(repository_contents, dict):
            errors.append("challenge PASS requires environment.repositoryContents")
        else:
            for field in required_contents:
                if repository_contents.get(field) is not True:
                    errors.append(
                        f"challenge PASS requires environment.repositoryContents.{field}=true"
                    )
        duration = environment.get("demoDurationSeconds")
        if not isinstance(duration, int) or isinstance(duration, bool) or not 1 <= duration < 180:
            errors.append("challenge PASS requires demoDurationSeconds between 1 and 179")
        if environment.get("audioPresent") is not True:
            errors.append(
                "challenge PASS requires audioPresent=true for the demo video; "
                "audioPresent is not a separate asset"
            )
        evidence_urls = {
            item["value"] for item in evidence if item.get("kind") == "url"
        }
        for field in ("liveUrl", "sourceRepository", "demoUrl"):
            value = environment.get(field)
            if isinstance(value, str) and value not in evidence_urls:
                errors.append(
                    f"challenge PASS requires an exact URL evidence item for environment.{field}"
                )
        expected = spec.get("expectedChallenge")
        if isinstance(expected, dict):
            for field in (
                "liveUrl",
                "sourceRepository",
                "liveUrlPublic",
                "sourceRepositoryPublic",
                "repositoryContents",
                "demoUrl",
                "demoPublic",
                "demoDurationSeconds",
                "audioPresent",
            ):
                if field in expected and environment.get(field) != expected[field]:
                    errors.append(
                        f"challenge PASS environment.{field} does not match the release manifest"
                    )
    elif status == "PASS" and evidence_class == "dual":
        for field in ("webmcpTool", "mcpTool", "host"):
            if not isinstance(environment.get(field), str) or not environment[field].strip():
                errors.append(f"dual PASS requires environment.{field}")
        if environment.get("webmcpTool") == environment.get("mcpTool"):
            errors.append("dual PASS must identify distinct WebMCP and MCP tools")
        if not any(item["kind"] in {"receipt", "log"} for item in evidence):
            errors.append("dual PASS requires a combined host trace")

    base = {
        "id": spec["id"],
        "evidenceClass": evidence_class,
        "required": spec.get("required") is True,
        "automated": False,
        "evidence": evidence,
        "details": {"environment": environment},
    }
    for field in ("command", "workingDirectory", "startedAt", "endedAt", "durationMs", "exitCode"):
        if field in receipt:
            base[field] = receipt[field]
    if errors:
        base.update(
            status="FAIL",
            reason="Invalid external receipt: " + "; ".join(errors),
        )
        base["details"]["receiptFindings"] = errors
        return base
    base["status"] = status
    if isinstance(reason, str) and reason.strip():
        base["reason"] = reason.strip()
    return base


def _not_run(spec: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": spec["id"],
        "evidenceClass": spec["evidenceClass"],
        "status": "NOT_RUN",
        "required": spec.get("required") is True,
        "automated": False,
        "reason": "No candidate-bound execution receipt was supplied for this gate.",
        "evidence": [],
        "details": {"instruction": spec.get("instruction")},
    }


def _contract_gate(
    product: Mapping[str, Any],
    toolset: Mapping[str, Any],
    release: Mapping[str, Any] | None,
) -> dict[str, Any]:
    reports = {
        "product": contract.validate_contract(product, "product"),
        "toolset": contract.validate_contract(toolset, "toolset"),
    }
    if release is not None:
        reports["release"] = contract.validate_contract(release, "release")
    failures = [name for name, report in reports.items() if report.get("status") == "FAIL"]
    result: dict[str, Any] = {
        "id": "contract",
        "evidenceClass": "deterministic",
        "status": "FAIL" if failures else "PASS",
        "required": True,
        "automated": True,
        "evidence": [
            {
                "kind": "command",
                "value": "internal:webmcp_contract.validate_contract(product, toolset, release)",
            }
        ],
        "details": {"reports": reports},
    }
    if failures:
        result["reason"] = "Contract validation failed for: " + ", ".join(failures)
    return result


def _release_local_materials_gate(
    release: Mapping[str, Any] | None,
    *,
    release_path: Path | None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": "release.local-materials",
        "evidenceClass": "release",
        "required": True,
        "automated": True,
        "evidence": [],
        "details": {},
    }
    if release is None or release_path is None:
        result.update(status="FAIL", reason="Production and challenge verification require a release manifest.")
        return result
    application = release.get("application", {})
    base = release_path.resolve().parent
    checked: list[dict[str, Any]] = []
    missing: list[str] = []
    for field in ("license", "runInstructions"):
        value = application.get(field) if isinstance(application, dict) else None
        if not isinstance(value, str):
            missing.append(field)
            continue
        path = (base / value).resolve()
        exists = path.is_file()
        item = {"field": field, "path": str(path), "exists": exists}
        if exists:
            item["sha256"] = _sha256_file(path)
            result["evidence"].append(
                {"kind": "file", "value": str(path), "sha256": item["sha256"]}
            )
        else:
            missing.append(str(path))
        checked.append(item)
    result["details"] = {"checked": checked}
    if missing:
        result.update(status="FAIL", reason="Required local release material is missing: " + ", ".join(missing))
    else:
        result["status"] = "PASS"
    return result


def _claim_bindings_gate(
    release: Mapping[str, Any] | None,
    results: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    gate_map = {item.get("id"): item for item in results}
    outcome: dict[str, Any] = {
        "id": "release.claim-bindings",
        "evidenceClass": "release",
        "required": True,
        "automated": True,
        "evidence": [{"kind": "note", "value": "Public claims were resolved against candidate gate IDs."}],
        "details": {"claims": [], "compatibility": []},
    }
    if release is None:
        outcome.update(status="FAIL", reason="No release manifest was supplied for claim binding.")
        return outcome
    claim_results: list[Mapping[str, Any]] = []
    compatibility_findings: list[dict[str, Any]] = []
    unknown: list[str] = []
    for claim in release.get("claims", []):
        if not isinstance(claim, dict):
            continue
        statuses: list[str] = []
        for gate_id in claim.get("evidenceGateIds", []):
            gate = gate_map.get(gate_id)
            if gate is None:
                unknown.append(str(gate_id))
                statuses.append("UNKNOWN")
            else:
                statuses.append(str(gate.get("status")))
                claim_results.append(gate)
        outcome["details"]["claims"].append({"id": claim.get("id"), "gateStatuses": statuses})
    for item in release.get("compatibility", []):
        if not isinstance(item, dict):
            continue
        statuses: list[str] = []
        compatibility_results: list[Mapping[str, Any]] = []
        for gate_id in item.get("evidenceGateIds", []):
            gate = gate_map.get(gate_id)
            if gate is None:
                unknown.append(str(gate_id))
                statuses.append("UNKNOWN")
            else:
                statuses.append(str(gate.get("status")))
                compatibility_results.append(gate)
        observed = aggregate_status(
            ({**gate, "required": True} for gate in compatibility_results),
            required_only=True,
        ) if compatibility_results else "NOT_RUN"
        declared = item.get("status")
        if observed != declared:
            compatibility_findings.append(
                {
                    "target": item.get("target"),
                    "declared": declared,
                    "observed": observed,
                }
            )
        outcome["details"]["compatibility"].append(
            {
                "target": item.get("target"),
                "declared": declared,
                "observed": observed,
                "gateStatuses": statuses,
            }
        )
    if unknown:
        outcome.update(status="FAIL", reason="Release references unknown gates: " + ", ".join(sorted(set(unknown))))
        return outcome
    claim_status = aggregate_status(
        ({**item, "required": True} for item in claim_results), required_only=True
    )
    mismatch_statuses = [item["observed"] for item in compatibility_findings]
    if compatibility_findings:
        mismatch_status = next(
            (status for status in STATUS_PRECEDENCE if status in mismatch_statuses),
            "FAIL",
        )
        # A completed but contradictory compatibility receipt is a contract
        # failure; an unavailable receipt retains its honest unavailable state.
        if mismatch_status in {"PASS", "UNSUPPORTED"}:
            mismatch_status = "FAIL"
    else:
        mismatch_status = "PASS"
    status = next(
        (candidate for candidate in STATUS_PRECEDENCE if candidate in {claim_status, mismatch_status}),
        "FAIL",
    )
    outcome["status"] = status
    if status != "PASS":
        if compatibility_findings:
            outcome["reason"] = (
                f"One or more compatibility statements lack matching {status} evidence: "
                + ", ".join(
                    f"{item['target']} declared {item['declared']} observed {item['observed']}"
                    for item in compatibility_findings
                )
            )
        else:
            outcome["reason"] = f"One or more public claims depend on {status} evidence."
    return outcome


def _source_gate(source_status: Mapping[str, Any], required: bool) -> dict[str, Any]:
    evidence: list[dict[str, Any]] = []
    for item in source_status.get("sources", []):
        if not isinstance(item, dict):
            continue
        evidence.extend(deepcopy(item.get("evidence", [])))
    if not evidence:
        evidence = [
            {
                "kind": "note",
                "value": "official-materials.json was evaluated; no candidate-time refresh receipt was supplied.",
            }
        ]
    result: dict[str, Any] = {
        "id": "source.official",
        "evidenceClass": "source",
        "status": source_status.get("status"),
        "required": required,
        "automated": True,
        "evidence": evidence,
        "details": deepcopy(source_status),
    }
    if result["status"] != "PASS":
        failing = [
            f"{item.get('id')}={item.get('status')}"
            for item in source_status.get("sources", [])
            if isinstance(item, dict) and item.get("status") != "PASS"
        ]
        result["reason"] = "Official source status is incomplete: " + ", ".join(failing)
    return result


def _to_evidence_gate(result: Mapping[str, Any]) -> dict[str, Any]:
    allowed = {
        "id",
        "status",
        "required",
        "command",
        "workingDirectory",
        "startedAt",
        "endedAt",
        "durationMs",
        "exitCode",
        "stdoutSha256",
        "stderrSha256",
        "reason",
        "evidence",
    }
    return {key: deepcopy(value) for key, value in result.items() if key in allowed}


def verification_report(
    product: Mapping[str, Any],
    toolset: Mapping[str, Any],
    *,
    release: Mapping[str, Any] | None = None,
    release_path: Path | None = None,
    receipts: Mapping[str, Any] | None = None,
    ledger: Mapping[str, Any] | None = None,
    source_refresh: Mapping[str, Any] | None = None,
    repository_root: Path = REPOSITORY_ROOT,
    as_of: datetime | None = None,
    repository_revision: str | None = None,
    dirty: bool | None = None,
    source_max_age_days: int | None = None,
) -> dict[str, Any]:
    as_of = as_of or datetime.now(timezone.utc)
    ledger = ledger or _read_json(DEFAULT_LEDGER)
    candidate = _candidate(
        product,
        toolset,
        generated_at=as_of,
        repository_root=repository_root,
        repository_revision=repository_revision,
        dirty=dirty,
    )
    specs = gate_plan(product)
    known_ids = {str(item["id"]) for item in specs}
    automated_ids = {str(item["id"]) for item in specs if item.get("automated") is True}
    receipt_map, binding_gate = _receipt_binding(
        receipts,
        candidate,
        known_ids,
        automated_ids,
    )
    results: list[dict[str, Any]] = []
    contract_gate = _contract_gate(product, toolset, release)
    source_status = evaluate_source_status(
        product,
        ledger=ledger,
        repository_root=repository_root,
        as_of=as_of,
        refresh=source_refresh,
        max_age_days=source_max_age_days,
    )

    for spec in specs:
        gate_id = spec["id"]
        if gate_id == "contract":
            results.append(contract_gate)
        elif gate_id == "source.official":
            results.append(_source_gate(source_status, spec.get("required") is True))
        elif gate_id == "release.local-materials":
            results.append(_release_local_materials_gate(release, release_path=release_path))
        elif gate_id == "release.claim-bindings":
            continue
        elif gate_id in receipt_map:
            receipt_spec: Mapping[str, Any] = spec
            if gate_id == "challenge.public-assets" and isinstance(release, dict):
                application = release.get("application", {})
                challenge = release.get("challenge", {})
                expected_challenge: dict[str, Any] = {}
                if isinstance(application, dict):
                    for field in ("liveUrl", "sourceRepository"):
                        if field in application:
                            expected_challenge[field] = application[field]
                if isinstance(challenge, dict):
                    for field in (
                        "liveUrlPublic",
                        "sourceRepositoryPublic",
                        "repositoryContents",
                        "demoUrl",
                        "demoPublic",
                        "demoDurationSeconds",
                        "audioPresent",
                    ):
                        if field in challenge:
                            expected_challenge[field] = challenge[field]
                receipt_spec = {**spec, "expectedChallenge": expected_challenge}
            results.append(_receipt_result(receipt_spec, receipt_map[gate_id]))
        else:
            results.append(_not_run(spec))
    if binding_gate is not None:
        results.append(binding_gate)
    if any(spec["id"] == "release.claim-bindings" for spec in specs):
        results.append(_claim_bindings_gate(release, results))

    results.sort(key=lambda item: str(item["id"]))
    evidence_gates = [_to_evidence_gate(item) for item in results]
    evidence_status = aggregate_status(evidence_gates, required_only=True)
    evidence = {
        "$schema": "../schemas/evidence.schema.json",
        "schemaVersion": "webmcp-evidence.v1",
        "candidate": candidate,
        "profile": {
            "release": product.get("release"),
            "targets": _profile_targets(product),
        },
        "gates": evidence_gates,
        "summary": {
            "status": evidence_status,
            "counts": _counts(evidence_gates),
        },
    }
    evidence_validation = contract.validate_contract(evidence, "evidence")
    if evidence_validation.get("status") == "FAIL":
        results.append(
            {
                "id": "evidence.contract",
                "evidenceClass": "deterministic",
                "status": "FAIL",
                "required": True,
                "automated": True,
                "reason": "Generated evidence failed its own contract.",
                "evidence": [{"kind": "note", "value": "Internal evidence contract validation failed."}],
                "details": evidence_validation,
            }
        )
    overall_status = aggregate_status(results, required_only=True)
    classes: dict[str, dict[str, Any]] = {}
    for evidence_class in EVIDENCE_CLASSES:
        class_results = [item for item in results if item.get("evidenceClass") == evidence_class]
        if not class_results:
            continue
        classes[evidence_class] = {
            "status": aggregate_status(class_results, required_only=False),
            "requiredStatus": aggregate_status(class_results, required_only=True),
            "counts": _counts(class_results),
            "gateIds": [item["id"] for item in class_results],
        }
    return {
        "schemaVersion": "webmcp-verification-report.v1",
        "status": overall_status,
        "candidate": candidate,
        "profile": deepcopy(evidence["profile"]),
        "classes": classes,
        "gates": results,
        "sourceStatus": source_status,
        "evidence": evidence,
        "evidenceContract": evidence_validation,
        "decision": {
            "releaseReady": overall_status == "PASS",
            "status": overall_status,
            "exitCode": STATUS_EXIT_CODES[overall_status],
            "blockingGateIds": [
                item["id"]
                for item in results
                if item.get("required") is True and item.get("status") != "PASS"
            ],
        },
    }


def _format_text(report: Mapping[str, Any]) -> str:
    lines = [f"{report.get('status')}  WebMCP verification"]
    for gate in report.get("gates", []):
        required = "required" if gate.get("required") else "optional"
        lines.append(
            f"{gate.get('status', 'FAIL'):11} {gate.get('id')} "
            f"[{gate.get('evidenceClass')}; {required}]"
        )
        if gate.get("reason"):
            lines.append(f"             {gate['reason']}")
    lines.append("Release ready: " + ("yes" if report.get("decision", {}).get("releaseReady") else "no"))
    return "\n".join(lines)


def _write_json(path: str | None, value: Mapping[str, Any]) -> None:
    if path is None:
        return
    destination = Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan and verify WebMCP release evidence without conflating execution layers."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan", help="Emit the evidence gate plan for a product profile.")
    plan.add_argument("--product", required=True)

    source = subparsers.add_parser("source-status", help="Evaluate official source refresh status.")
    source.add_argument("--product", required=True)
    source.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    source.add_argument("--source-refresh")
    source.add_argument("--repository-root", default=str(REPOSITORY_ROOT))
    source.add_argument("--as-of")
    source.add_argument("--max-age-days", type=int)

    verify = subparsers.add_parser("verify", help="Produce a release decision and evidence document.")
    verify.add_argument("--product", required=True)
    verify.add_argument("--toolset", required=True)
    verify.add_argument("--release")
    verify.add_argument("--receipts")
    verify.add_argument("--source-refresh")
    verify.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    verify.add_argument("--repository-root", default=str(REPOSITORY_ROOT))
    verify.add_argument("--repository-revision")
    verify.add_argument("--dirty", choices=("true", "false"))
    verify.add_argument("--as-of")
    verify.add_argument("--source-max-age-days", type=int)
    verify.add_argument("--output", help="Write the full verification report as JSON.")
    verify.add_argument("--evidence-output", help="Write the schema-compatible evidence document as JSON.")
    verify.add_argument("--format", choices=("json", "text"), default="json")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        product = _read_json(args.product)
        if args.command == "plan":
            output = {
                "schemaVersion": "webmcp-verification-plan.v1",
                "release": product.get("release"),
                "targets": _profile_targets(product),
                "statuses": list(STATUSES),
                "evidenceClasses": list(EVIDENCE_CLASSES),
                "gates": gate_plan(product),
            }
            print(json.dumps(output, indent=2, ensure_ascii=False))
            return 0

        as_of = _parse_datetime(args.as_of, "--as-of") if args.as_of else datetime.now(timezone.utc)
        ledger = _read_json(args.ledger)
        source_refresh = _read_json(args.source_refresh) if args.source_refresh else None
        repository_root = Path(args.repository_root).expanduser().resolve()
        if args.command == "source-status":
            output = evaluate_source_status(
                product,
                ledger=ledger,
                repository_root=repository_root,
                as_of=as_of,
                refresh=source_refresh,
                max_age_days=args.max_age_days,
            )
            print(json.dumps(output, indent=2, ensure_ascii=False))
            return STATUS_EXIT_CODES[output["status"]]

        toolset = _read_json(args.toolset)
        release = _read_json(args.release) if args.release else None
        receipts = _read_json(args.receipts) if args.receipts else None
        dirty = None if args.dirty is None else args.dirty == "true"
        report = verification_report(
            product,
            toolset,
            release=release,
            release_path=Path(args.release).expanduser().resolve() if args.release else None,
            receipts=receipts,
            ledger=ledger,
            source_refresh=source_refresh,
            repository_root=repository_root,
            as_of=as_of,
            repository_revision=args.repository_revision,
            dirty=dirty,
            source_max_age_days=args.source_max_age_days,
        )
        _write_json(args.output, report)
        _write_json(args.evidence_output, report["evidence"])
        if args.format == "text":
            print(_format_text(report))
        else:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        return STATUS_EXIT_CODES[report["status"]]
    except (VerificationInputError, contract.ContractDependencyError, contract.ContractInputError) as exc:
        error = {
            "schemaVersion": "webmcp-verification-error.v1",
            "status": "FAIL",
            "error": type(exc).__name__,
            "message": str(exc),
        }
        print(json.dumps(error, indent=2, ensure_ascii=False))
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
