#!/usr/bin/env python3
"""Generate explicitly non-conformant WebMCP proposal scaffolds.

The declarative-form and Service Worker surfaces represented here are useful
for research and local prototyping, but are not the current document WebMCP
API. Every generated artifact is accompanied by a status sidecar so a mock or
proposal cannot be mistaken for browser-conformance evidence.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import html
import json
from pathlib import Path
import re
from typing import Any, Sequence


GENERATOR_VERSION = "1.0.0"
SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = SKILL_ROOT / "assets" / "templates"
NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")

PROPOSAL_CATALOG: dict[str, dict[str, Any]] = {
    "declarative": {
        "id": "declarative-webmcp",
        "maturity": "PROPOSAL",
        "specificationSupport": "INCOMPLETE",
        "chatgptSiteToolsSupport": "UNSUPPORTED",
        "documentApiConformance": "NOT_CLAIMED",
        "browserConformance": "NOT_RUN",
        "testEvidence": "MOCK_ONLY",
        "eventName": "toolcanceled",
        "eventTarget": "UNRESOLVED",
        "sourceEvidence": [
            "https://github.com/webmachinelearning/webmcp/blob/main/declarative-api-explainer.md",
            "https://webmachinelearning.github.io/webmcp/",
            "https://help.openai.com/en/articles/20001423-using-site-tools-in-the-chatgpt-desktop-app",
        ],
        "openQuestions": [
            "form-to-JSON-Schema synthesis",
            "cross-document response handling",
            "event targets and imperative-event coverage",
            "getTools and executeTool integration",
        ],
    },
    "service-worker": {
        "id": "service-worker-webmcp",
        "maturity": "PROPOSAL",
        "specificationSupport": "UNSUPPORTED",
        "chatgptSiteToolsSupport": "UNSUPPORTED",
        "documentApiConformance": "NOT_CLAIMED",
        "browserConformance": "NOT_RUN",
        "testEvidence": "MOCK_ONLY",
        "runtimeSurface": "DEPENDENCY_INJECTED_PROPOSAL_MOCK",
        "sourceEvidence": [
            "https://github.com/webmachinelearning/webmcp/blob/main/docs/service-workers.md",
            "https://webmachinelearning.github.io/webmcp/",
            "https://help.openai.com/en/articles/20001423-using-site-tools-in-the-chatgpt-desktop-app",
        ],
        "openQuestions": [
            "provider discovery and JIT installation",
            "session identity",
            "page-versus-worker routing",
            "worker restart and durable state",
            "multi-origin data boundaries",
        ],
    },
}

TEMPLATES = {
    "declarative": TEMPLATE_ROOT / "declarative-webmcp.proposal.html",
    "service-worker": TEMPLATE_ROOT / "service-worker-webmcp.proposal.mjs",
}

ARTIFACT_NAMES = {
    "declarative": "declarative-webmcp.proposal.html",
    "service-worker": "service-worker-webmcp.proposal.mjs",
}


class ProposalError(ValueError):
    """Raised for unsafe or incomplete proposal-generation inputs."""


def proposal_status(kind: str | None = None) -> dict[str, Any]:
    """Return a detached, deterministic proposal-status document."""

    if kind is None:
        return {
            "generatorVersion": GENERATOR_VERSION,
            "profiles": deepcopy(PROPOSAL_CATALOG),
        }
    if kind not in PROPOSAL_CATALOG:
        raise ProposalError(f"unknown proposal kind: {kind}")
    return {
        "generatorVersion": GENERATOR_VERSION,
        "profile": deepcopy(PROPOSAL_CATALOG[kind]),
    }


def validate_inputs(tool_name: str, description: str) -> None:
    if not NAME_PATTERN.fullmatch(tool_name):
        raise ProposalError(
            "tool name must be 1-128 ASCII alphanumeric, underscore, hyphen, or dot characters"
        )
    if not description.strip():
        raise ProposalError("description must not be empty")
    if len(description) > 1000:
        raise ProposalError("description must be at most 1000 characters")


def _replace_all(source: str, replacements: dict[str, str]) -> str:
    rendered = source
    for token, value in replacements.items():
        rendered = rendered.replace(token, value)
    leftovers = sorted(set(re.findall(r"__[A-Z][A-Z0-9_]+__", rendered)))
    if leftovers:
        raise ProposalError(f"unresolved template tokens: {', '.join(leftovers)}")
    return rendered


def render_proposal(
    kind: str,
    *,
    tool_name: str,
    description: str,
    auto_submit: bool = False,
) -> str:
    """Render one proposal artifact without writing it."""

    if kind not in TEMPLATES:
        raise ProposalError(f"unknown proposal kind: {kind}")
    if auto_submit and kind != "declarative":
        raise ProposalError("--auto-submit applies only to the declarative proposal")
    validate_inputs(tool_name, description)

    template_path = TEMPLATES[kind]
    if not template_path.is_file():
        raise ProposalError(f"proposal template is missing: {template_path}")
    source = template_path.read_text(encoding="utf-8")
    form_id = "webmcp-proposal-" + re.sub(r"[._]", "-", tool_name.lower())
    return _replace_all(
        source,
        {
            "__TOOL_NAME_HTML__": html.escape(tool_name, quote=True),
            "__DESCRIPTION_HTML__": html.escape(description, quote=True),
            "__FORM_ID_HTML__": html.escape(form_id, quote=True),
            "__TOOL_NAME_JSON__": json.dumps(tool_name, ensure_ascii=False),
            "__DESCRIPTION_JSON__": json.dumps(description, ensure_ascii=False),
            "__AUTOSUBMIT_ATTRIBUTE__": "\n  toolautosubmit" if auto_submit else "",
        },
    )


def generate_proposal(
    kind: str,
    *,
    output_dir: Path,
    tool_name: str,
    description: str,
    auto_submit: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """Write a proposal artifact and its inseparable status sidecar."""

    rendered = render_proposal(
        kind,
        tool_name=tool_name,
        description=description,
        auto_submit=auto_submit,
    )
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if not output_dir.is_dir():
        raise ProposalError(f"output is not a directory: {output_dir}")

    artifact_path = output_dir / ARTIFACT_NAMES[kind]
    status_path = output_dir / f"{ARTIFACT_NAMES[kind]}.status.json"
    existing = [path for path in (artifact_path, status_path) if path.exists()]
    if existing and not force:
        names = ", ".join(path.name for path in existing)
        raise ProposalError(f"refusing to overwrite existing output: {names}; pass --force")

    status = proposal_status(kind)
    status.update(
        {
            "artifact": artifact_path.name,
            "toolName": tool_name,
            "autoSubmit": auto_submit if kind == "declarative" else None,
            "verification": {
                "templateRendered": "PASS",
                "mockTests": "NOT_RUN",
                "nativeDiscovery": "NOT_RUN",
                "nativeInvocation": "NOT_RUN",
            },
        }
    )
    artifact_path.write_text(rendered, encoding="utf-8", newline="\n")
    status_path.write_text(
        json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return {
        "operation": "generate-proposal",
        "status": "PASS",
        "artifact": str(artifact_path),
        "statusMetadata": str(status_path),
        "profile": deepcopy(PROPOSAL_CATALOG[kind]),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect or generate explicitly non-conformant declarative and "
            "Service Worker WebMCP proposal artifacts."
        )
    )
    parser.add_argument("--version", action="version", version=GENERATOR_VERSION)
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status", help="print proposal maturity metadata")
    status_parser.add_argument("--kind", choices=tuple(PROPOSAL_CATALOG))

    generate_parser = subparsers.add_parser(
        "generate", help="render a proposal template and status sidecar"
    )
    generate_parser.add_argument("kind", choices=tuple(PROPOSAL_CATALOG))
    generate_parser.add_argument("--output-dir", type=Path, required=True)
    generate_parser.add_argument("--tool-name", required=True)
    generate_parser.add_argument("--description", required=True)
    generate_parser.add_argument(
        "--auto-submit",
        action="store_true",
        help="add the experimental toolautosubmit attribute to a declarative form",
    )
    generate_parser.add_argument(
        "--force", action="store_true", help="overwrite only this generator's named outputs"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "status":
            result = proposal_status(args.kind)
        else:
            result = generate_proposal(
                args.kind,
                output_dir=args.output_dir,
                tool_name=args.tool_name,
                description=args.description,
                auto_submit=args.auto_submit,
                force=args.force,
            )
    except (OSError, ProposalError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
