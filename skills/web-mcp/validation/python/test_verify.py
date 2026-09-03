from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import webmcp_contract as contract  # noqa: E402
import webmcp_verify as verify  # noqa: E402


EXAMPLES = SKILL_ROOT / "assets" / "examples"
RELEASE_ASSETS = SKILL_ROOT / "assets" / "release"
EVAL_ASSETS = SKILL_ROOT / "assets" / "examples"
LEDGER = SKILL_ROOT / "assets" / "sources" / "official-materials.json"
REPOSITORY_ROOT = SKILL_ROOT.parents[1]
AS_OF = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)
REVISION = "0123456789abcdef0123456789abcdef01234567"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def development_product() -> dict:
    product = read_json(EXAMPLES / "product.create-challenge.example.json")
    product["release"] = "development"
    return product


def candidate_receipts(product: dict, toolset: dict, receipts: list[dict]) -> dict:
    return {
        "schemaVersion": "webmcp-verification-receipts.v1",
        "candidate": {
            "productSha256": contract.sha256_json(product),
            "toolsetSha256": contract.sha256_json(toolset),
        },
        "receipts": receipts,
    }


def pass_receipt(gate_id: str) -> dict:
    return {
        "gateId": gate_id,
        "status": "PASS",
        "command": f"python -m tests {gate_id}",
        "exitCode": 0,
        "evidence": [{"kind": "log", "value": f"evidence/{gate_id}.json"}],
        "environment": {},
    }


def run_report(product: dict, toolset: dict, receipts: dict | None = None, **kwargs: object) -> dict:
    return verify.verification_report(
        product,
        toolset,
        receipts=receipts,
        ledger=read_json(LEDGER),
        repository_root=REPOSITORY_ROOT,
        as_of=AS_OF,
        repository_revision=REVISION,
        dirty=False,
        **kwargs,
    )


class StatusAndPlanningTests(unittest.TestCase):
    def test_status_precedence_is_explicit(self) -> None:
        base = {"required": True}
        self.assertEqual(
            verify.aggregate_status(
                [{**base, "status": "UNSUPPORTED"}, {**base, "status": "NOT_RUN"}],
                required_only=True,
            ),
            "NOT_RUN",
        )
        self.assertEqual(
            verify.aggregate_status(
                [{**base, "status": "BLOCKED"}, {**base, "status": "FAIL"}],
                required_only=True,
            ),
            "FAIL",
        )

    def test_challenge_plan_separates_wpt_browser_agent_and_native_hosts(self) -> None:
        plan = verify.gate_plan(read_json(EXAMPLES / "product.create-challenge.example.json"))
        by_id = {item["id"]: item for item in plan}
        self.assertEqual(by_id["wpt.webmcp"]["evidenceClass"], "wpt")
        self.assertEqual(by_id["browser.discovery"]["evidenceClass"], "browser")
        self.assertEqual(by_id["agent.selection"]["evidenceClass"], "agent")
        self.assertEqual(by_id["native.chrome"]["host"], "chromium-webmcp")
        self.assertEqual(by_id["native.chatgpt"]["host"], "chatgpt-site-tools")
        self.assertNotEqual(by_id["native.chrome"]["id"], by_id["native.chatgpt"]["id"])

    def test_dual_surface_requires_real_composition_even_in_development(self) -> None:
        product = read_json(EXAMPLES / "product.extend-dual.example.json")
        product["release"] = "development"
        toolset = read_json(EXAMPLES / "toolset.example.json")
        receipts = candidate_receipts(
            product,
            toolset,
            [pass_receipt("deterministic.lifecycle"), pass_receipt("deterministic.serialization")],
        )
        report = run_report(product, toolset, receipts)
        gates = {item["id"]: item for item in report["gates"]}
        self.assertEqual(gates["dual.composition"]["status"], "NOT_RUN")
        self.assertTrue(gates["dual.composition"]["required"])
        self.assertEqual(report["status"], "NOT_RUN")


class HonestReceiptTests(unittest.TestCase):
    def test_missing_execution_is_not_run_not_pass_or_blocked(self) -> None:
        product = development_product()
        toolset = read_json(EXAMPLES / "toolset.example.json")
        report = run_report(product, toolset)
        gates = {item["id"]: item for item in report["gates"]}
        self.assertEqual(gates["deterministic.lifecycle"]["status"], "NOT_RUN")
        self.assertEqual(report["status"], "NOT_RUN")

    def test_development_can_pass_with_candidate_bound_deterministic_receipts(self) -> None:
        product = development_product()
        toolset = read_json(EXAMPLES / "toolset.example.json")
        receipts = candidate_receipts(
            product,
            toolset,
            [pass_receipt("deterministic.lifecycle"), pass_receipt("deterministic.serialization")],
        )
        report = run_report(product, toolset, receipts)
        self.assertEqual(report["status"], "PASS", report["decision"])
        self.assertTrue(report["decision"]["releaseReady"])
        self.assertEqual(report["classes"]["source"]["status"], "NOT_RUN")
        self.assertEqual(report["classes"]["source"]["requiredStatus"], "PASS")
        self.assertEqual(report["evidenceContract"]["status"], "PASS")

    def test_candidate_hash_mismatch_rejects_all_external_receipts(self) -> None:
        product = development_product()
        toolset = read_json(EXAMPLES / "toolset.example.json")
        receipts = candidate_receipts(
            product,
            toolset,
            [pass_receipt("deterministic.lifecycle"), pass_receipt("deterministic.serialization")],
        )
        receipts["candidate"]["toolsetSha256"] = "0" * 64
        report = run_report(product, toolset, receipts)
        gates = {item["id"]: item for item in report["gates"]}
        self.assertEqual(gates["receipt.binding"]["status"], "FAIL")
        self.assertEqual(gates["deterministic.lifecycle"]["status"], "NOT_RUN")
        self.assertEqual(report["status"], "FAIL")

    def test_external_receipt_cannot_override_an_automated_gate(self) -> None:
        product = development_product()
        toolset = read_json(EXAMPLES / "toolset.example.json")
        receipts = candidate_receipts(
            product,
            toolset,
            [pass_receipt("contract")],
        )
        report = run_report(product, toolset, receipts)
        gates = {item["id"]: item for item in report["gates"]}
        self.assertEqual(gates["contract"]["status"], "PASS")
        self.assertEqual(gates["receipt.binding"]["status"], "FAIL")
        self.assertIn("cannot override automated gate", gates["receipt.binding"]["reason"])

    def test_blocked_requires_an_attempt_and_evidence(self) -> None:
        spec = {
            "id": "native.chrome",
            "evidenceClass": "host-native",
            "host": "chromium-webmcp",
            "required": True,
        }
        invalid = verify._receipt_result(  # noqa: SLF001 - focused contract test
            spec,
            {
                "gateId": "native.chrome",
                "status": "BLOCKED",
                "reason": "Native host unavailable.",
                "evidence": [],
            },
        )
        self.assertEqual(invalid["status"], "FAIL")
        valid = verify._receipt_result(  # noqa: SLF001
            spec,
            {
                "gateId": "native.chrome",
                "status": "BLOCKED",
                "reason": "Native host manifest is absent.",
                "attemptedAt": "2026-08-28T11:00:00Z",
                "evidence": [{"kind": "log", "value": "evidence/chrome-diagnostic.json"}],
            },
        )
        self.assertEqual(valid["status"], "BLOCKED")

    def test_unsupported_requires_official_url_evidence(self) -> None:
        spec = {
            "id": "service-worker.proposal",
            "evidenceClass": "browser",
            "required": False,
        }
        invalid = verify._receipt_result(  # noqa: SLF001
            spec,
            {
                "gateId": "service-worker.proposal",
                "status": "UNSUPPORTED",
                "reason": "No target implementation.",
                "evidence": [{"kind": "note", "value": "No implementation was observed."}],
            },
        )
        self.assertEqual(invalid["status"], "FAIL")
        valid = verify._receipt_result(  # noqa: SLF001
            spec,
            {
                "gateId": "service-worker.proposal",
                "status": "UNSUPPORTED",
                "reason": "The selected host does not implement the proposal.",
                "evidence": [
                    {
                        "kind": "url",
                        "value": "https://learn.chatgpt.com/docs/webmcp"
                    }
                ],
            },
        )
        self.assertEqual(valid["status"], "UNSUPPORTED")


class ClassSpecificReceiptTests(unittest.TestCase):
    def test_agent_pass_enforces_model_runs_threshold_and_stop_conditions(self) -> None:
        spec = {"id": "agent.selection", "evidenceClass": "agent", "required": True}
        receipt = {
            "gateId": "agent.selection",
            "status": "PASS",
            "evidence": [{"kind": "log", "value": "evidence/agent.json"}],
            "environment": {
                "model": "provider:model-id",
                "backend": "vercel",
                "runs": 5,
                "passedRuns": 3,
                "threshold": 0.8,
                "stopViolations": 0,
            },
        }
        self.assertEqual(verify._receipt_result(spec, receipt)["status"], "FAIL")  # noqa: SLF001
        receipt["environment"]["passedRuns"] = 4
        self.assertEqual(verify._receipt_result(spec, receipt)["status"], "PASS")  # noqa: SLF001
        receipt["environment"]["stopViolations"] = 1
        self.assertEqual(verify._receipt_result(spec, receipt)["status"], "FAIL")  # noqa: SLF001

    def test_wpt_pass_requires_revision_browser_command_and_raw_report(self) -> None:
        spec = {"id": "wpt.webmcp", "evidenceClass": "wpt", "required": True}
        receipt = {
            "gateId": "wpt.webmcp",
            "status": "PASS",
            "evidence": [{"kind": "log", "value": "evidence/wpt.json"}],
            "environment": {
                "browserVersion": "Chrome Canary 142.0.0.0",
                "wptRevision": "abc123",
                "command": "./wpt run chrome webmcp/",
            },
        }
        self.assertEqual(verify._receipt_result(spec, receipt)["status"], "PASS")  # noqa: SLF001
        del receipt["environment"]["wptRevision"]
        self.assertEqual(verify._receipt_result(spec, receipt)["status"], "FAIL")  # noqa: SLF001

    def test_chatgpt_native_pass_cannot_omit_model_or_native_capture(self) -> None:
        spec = {
            "id": "native.chatgpt",
            "evidenceClass": "host-native",
            "host": "chatgpt-site-tools",
            "required": True,
        }
        receipt = {
            "gateId": "native.chatgpt",
            "status": "PASS",
            "evidence": [{"kind": "screenshot", "value": "evidence/site-tools.png"}],
            "environment": {
                "host": "chatgpt-site-tools",
                "hostVersion": "Codex desktop 2026-08-28",
            },
        }
        self.assertEqual(verify._receipt_result(spec, receipt)["status"], "FAIL")  # noqa: SLF001
        receipt["environment"]["model"] = "gpt-5.6-sol"
        self.assertEqual(verify._receipt_result(spec, receipt)["status"], "PASS")  # noqa: SLF001

    def test_dual_pass_names_distinct_tool_surfaces(self) -> None:
        spec = {"id": "dual.composition", "evidenceClass": "dual", "required": True}
        receipt = {
            "gateId": "dual.composition",
            "status": "PASS",
            "evidence": [{"kind": "receipt", "value": "evidence/combined-trace.json"}],
            "environment": {
                "webmcpTool": "set_dashboard_date_range",
                "mcpTool": "persist_dashboard_snapshot",
                "host": "chatgpt",
            },
        }
        self.assertEqual(verify._receipt_result(spec, receipt)["status"], "PASS")  # noqa: SLF001
        receipt["environment"]["mcpTool"] = "set_dashboard_date_range"
        self.assertEqual(verify._receipt_result(spec, receipt)["status"], "FAIL")  # noqa: SLF001

    def test_challenge_pass_requires_complete_public_assets_and_youtube_video_audio(self) -> None:
        environment = {
            "liveUrl": "https://analytics.example.com/",
            "liveUrlPublic": True,
            "sourceRepository": "https://github.com/example/acme-analytics",
            "sourceRepositoryPublic": True,
            "repositoryContents": {
                "sourceCode": True,
                "assets": True,
                "runInstructions": True,
                "openSourceLicense": True,
            },
            "demoUrl": "https://www.youtube.com/watch?v=example",
            "demoPublic": True,
            "demoDurationSeconds": 179,
            "audioPresent": True,
        }
        spec = {
            "id": "challenge.public-assets",
            "evidenceClass": "challenge",
            "required": True,
            "expectedChallenge": deepcopy(environment),
        }
        receipt = {
            "gateId": "challenge.public-assets",
            "status": "PASS",
            "environment": environment,
            "evidence": [
                {"kind": "url", "value": environment["liveUrl"]},
                {"kind": "url", "value": environment["sourceRepository"]},
                {"kind": "url", "value": environment["demoUrl"]},
            ],
        }
        self.assertEqual(verify._receipt_result(spec, receipt)["status"], "PASS")  # noqa: SLF001

        invalid_cases = {
            "exactly three minutes": ("demoDurationSeconds", 180),
            "silent video": ("audioPresent", False),
            "private demo": ("demoPublic", False),
            "non-YouTube demo": ("demoUrl", "https://vimeo.com/example"),
        }
        for label, (field, value) in invalid_cases.items():
            with self.subTest(case=label):
                invalid = deepcopy(receipt)
                invalid["environment"][field] = value
                if field == "demoUrl":
                    invalid["evidence"][2]["value"] = value
                self.assertEqual(verify._receipt_result(spec, invalid)["status"], "FAIL")  # noqa: SLF001

        missing_asset = deepcopy(receipt)
        missing_asset["environment"]["repositoryContents"]["assets"] = False
        self.assertEqual(verify._receipt_result(spec, missing_asset)["status"], "FAIL")  # noqa: SLF001

        unrelated_candidate = deepcopy(receipt)
        unrelated_candidate["environment"]["liveUrl"] = "https://other.example.com/"
        unrelated_candidate["evidence"][0]["value"] = "https://other.example.com/"
        self.assertEqual(
            verify._receipt_result(spec, unrelated_candidate)["status"],  # noqa: SLF001
            "FAIL",
        )


class SourceAndReleaseTests(unittest.TestCase):
    def test_source_ledger_has_no_workspace_mirror_bindings(self) -> None:
        product = development_product()
        ledger = read_json(LEDGER)
        mirror_key = "local" + "Mirror"
        self.assertIn("portabilityPolicy", ledger)
        self.assertTrue(all(mirror_key not in source for source in ledger["sources"]))

        status = verify.evaluate_source_status(
            product,
            ledger=ledger,
            repository_root=REPOSITORY_ROOT,
            as_of=AS_OF,
        )
        self.assertEqual(status["status"], "NOT_RUN")
        self.assertTrue(
            all(
                mirror_key not in field
                for source in status["sources"]
                for field in source
            )
        )

    def test_portable_skill_has_no_installed_tree_or_external_documentation_path(self) -> None:
        dependency_directory = "node" + "_modules"
        dependency_trees = sorted(
            str(path.relative_to(SKILL_ROOT))
            for path in SKILL_ROOT.rglob(dependency_directory)
            if path.is_dir()
        )
        self.assertEqual(dependency_trees, [])

        nested_archives = sorted(
            str(path.relative_to(SKILL_ROOT))
            for path in SKILL_ROOT.rglob("*")
            if path.is_file() and path.suffix.lower() in {".skill", ".zip"}
        )
        self.assertEqual(nested_archives, [])

        external_path_token = "docs" + "/"
        mirror_key = "local" + "Mirror"
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
        offenders: list[str] = []
        for path in sorted(SKILL_ROOT.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in text_suffixes:
                continue
            text = path.read_text(encoding="utf-8")
            if mirror_key in text:
                offenders.append(f"{path.relative_to(SKILL_ROOT)}: workspace mirror field")
            for line_number, line in enumerate(text.splitlines(), start=1):
                without_urls = re.sub(r"https?://[^\s\"'`<>]+", "", line)
                if external_path_token in without_urls.lower():
                    offenders.append(
                        f"{path.relative_to(SKILL_ROOT)}:{line_number}: external documentation path"
                    )
        self.assertEqual(offenders, [])

    def test_source_status_requires_candidate_time_refresh_for_mutable_sources(self) -> None:
        product = development_product()
        ledger = read_json(LEDGER)
        status = verify.evaluate_source_status(
            product,
            ledger=ledger,
            repository_root=REPOSITORY_ROOT,
            as_of=AS_OF,
        )
        self.assertEqual(status["status"], "NOT_RUN")
        self.assertTrue(all(item["status"] == "NOT_RUN" for item in status["sources"]))

    def test_fresh_exact_canonical_source_receipt_passes_that_source(self) -> None:
        product = development_product()
        ledger = read_json(LEDGER)
        draft = next(item for item in ledger["sources"] if item["id"] == "webmcp-draft-spec")
        refresh = {
            "schemaVersion": "webmcp-source-refresh.v1",
            "sources": [
                {
                    "id": draft["id"],
                    "canonicalUrl": draft["canonicalUrl"],
                    "status": "PASS",
                    "checkedAt": "2026-08-28T11:00:00Z",
                    "evidence": [{"kind": "url", "value": draft["canonicalUrl"]}],
                }
            ],
        }
        status = verify.evaluate_source_status(
            product,
            ledger=ledger,
            repository_root=REPOSITORY_ROOT,
            as_of=AS_OF,
            refresh=refresh,
        )
        by_id = {item["id"]: item for item in status["sources"]}
        self.assertEqual(by_id["webmcp-draft-spec"]["status"], "PASS")
        self.assertEqual(status["status"], "NOT_RUN")

    def test_source_canonical_url_mismatch_is_fail(self) -> None:
        product = development_product()
        ledger = read_json(LEDGER)
        refresh = {
            "schemaVersion": "webmcp-source-refresh.v1",
            "sources": [
                {
                    "id": "webmcp-draft-spec",
                    "canonicalUrl": "https://example.invalid/not-official",
                    "status": "PASS",
                    "checkedAt": "2026-08-28T11:00:00Z",
                    "evidence": [{"kind": "url", "value": "https://example.invalid/not-official"}],
                }
            ],
        }
        status = verify.evaluate_source_status(
            product,
            ledger=ledger,
            repository_root=REPOSITORY_ROOT,
            as_of=AS_OF,
            refresh=refresh,
        )
        by_id = {item["id"]: item for item in status["sources"]}
        self.assertEqual(by_id["webmcp-draft-spec"]["status"], "FAIL")
        self.assertEqual(status["status"], "FAIL")

    def test_local_release_materials_are_checked_on_disk(self) -> None:
        release = read_json(EXAMPLES / "release.challenge.example.json")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "LICENSE").write_text("Example license\n", encoding="utf-8")
            (root / "README.md").write_text("# Run\n", encoding="utf-8")
            release_path = root / "release.json"
            result = verify._release_local_materials_gate(  # noqa: SLF001
                release,
                release_path=release_path,
            )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(result["evidence"]), 2)

    def test_explicit_unsupported_compatibility_is_valid_when_evidence_matches(self) -> None:
        release = {
            "claims": [],
            "compatibility": [
                {
                    "target": "service-worker-proposal",
                    "status": "UNSUPPORTED",
                    "evidenceGateIds": ["service-worker.proposal"],
                }
            ],
        }
        matching = verify._claim_bindings_gate(  # noqa: SLF001
            release,
            [
                {
                    "id": "service-worker.proposal",
                    "status": "UNSUPPORTED",
                    "required": False,
                }
            ],
        )
        self.assertEqual(matching["status"], "PASS")
        missing = verify._claim_bindings_gate(  # noqa: SLF001
            release,
            [
                {
                    "id": "service-worker.proposal",
                    "status": "NOT_RUN",
                    "required": False,
                }
            ],
        )
        self.assertEqual(missing["status"], "NOT_RUN")


class AssetContractTests(unittest.TestCase):
    def test_new_json_schemas_and_templates_are_valid(self) -> None:
        try:
            from jsonschema import Draft202012Validator
        except ImportError as exc:  # pragma: no cover - requirements pin jsonschema
            self.fail(f"jsonschema dependency unavailable: {exc}")
        for schema_name, template_name in (
            ("source-refresh.schema.json", "source-refresh.template.json"),
            ("verification-receipts.schema.json", "verification-receipts.template.json"),
        ):
            with self.subTest(schema=schema_name):
                schema = read_json(RELEASE_ASSETS / schema_name)
                Draft202012Validator.check_schema(schema)
                errors = sorted(
                    Draft202012Validator(schema).iter_errors(read_json(RELEASE_ASSETS / template_name)),
                    key=lambda item: list(item.absolute_path),
                )
                self.assertEqual(errors, [])

    def test_challenge_release_contract_matches_public_submission_requirements(self) -> None:
        release = read_json(EXAMPLES / "release.challenge.example.json")
        self.assertEqual(contract.validate_contract(release, "release")["status"], "PASS")

        exactly_three_minutes = deepcopy(release)
        exactly_three_minutes["challenge"]["demoDurationSeconds"] = 180
        self.assertEqual(
            contract.validate_contract(exactly_three_minutes, "release")["status"],
            "FAIL",
        )

        non_youtube = deepcopy(release)
        non_youtube["challenge"]["demoUrl"] = "https://vimeo.com/example"
        self.assertEqual(contract.validate_contract(non_youtube, "release")["status"], "FAIL")

        missing_repository_assets = deepcopy(release)
        missing_repository_assets["challenge"]["repositoryContents"]["assets"] = False
        self.assertEqual(
            contract.validate_contract(missing_repository_assets, "release")["status"],
            "FAIL",
        )

    def test_challenge_receipt_schema_models_audio_as_video_property(self) -> None:
        try:
            from jsonschema import Draft202012Validator
        except ImportError as exc:  # pragma: no cover - requirements pin jsonschema
            self.fail(f"jsonschema dependency unavailable: {exc}")
        environment = {
            "liveUrl": "https://analytics.example.com/",
            "liveUrlPublic": True,
            "sourceRepository": "https://github.com/example/acme-analytics",
            "sourceRepositoryPublic": True,
            "repositoryContents": {
                "sourceCode": True,
                "assets": True,
                "runInstructions": True,
                "openSourceLicense": True,
            },
            "demoUrl": "https://youtu.be/example",
            "demoPublic": True,
            "demoDurationSeconds": 179,
            "audioPresent": True,
        }
        receipt_document = {
            "schemaVersion": "webmcp-verification-receipts.v1",
            "candidate": {
                "productSha256": "0" * 64,
                "toolsetSha256": "1" * 64,
            },
            "receipts": [
                {
                    "gateId": "challenge.public-assets",
                    "status": "PASS",
                    "environment": environment,
                    "evidence": [
                        {"kind": "url", "value": environment["liveUrl"]},
                        {"kind": "url", "value": environment["sourceRepository"]},
                        {"kind": "url", "value": environment["demoUrl"]},
                    ],
                }
            ],
        }
        schema = read_json(RELEASE_ASSETS / "verification-receipts.schema.json")
        validator = Draft202012Validator(schema)
        self.assertEqual(list(validator.iter_errors(receipt_document)), [])

        silent_video = deepcopy(receipt_document)
        silent_video["receipts"][0]["environment"]["audioPresent"] = False
        self.assertTrue(list(validator.iter_errors(silent_video)))

        policy = read_json(RELEASE_ASSETS / "verification-policy.json")
        challenge_policy = policy["challengePublicAssets"]
        self.assertEqual(challenge_policy["demoDurationSecondsExclusiveMaximum"], 180)
        self.assertEqual(challenge_policy["demoAudioField"], "audioPresent")
        self.assertFalse(challenge_policy["demoAudioIsSeparateAsset"])

    def test_generated_report_validates_against_its_machine_contract(self) -> None:
        try:
            from jsonschema import Draft202012Validator
        except ImportError as exc:  # pragma: no cover - requirements pin jsonschema
            self.fail(f"jsonschema dependency unavailable: {exc}")
        product = development_product()
        toolset = read_json(EXAMPLES / "toolset.example.json")
        receipts = candidate_receipts(
            product,
            toolset,
            [pass_receipt("deterministic.lifecycle"), pass_receipt("deterministic.serialization")],
        )
        report = run_report(product, toolset, receipts)
        schema = read_json(RELEASE_ASSETS / "verification-report.schema.json")
        Draft202012Validator.check_schema(schema)
        errors = sorted(
            Draft202012Validator(schema).iter_errors(report),
            key=lambda item: list(item.absolute_path),
        )
        self.assertEqual(errors, [])

    def test_webmcp_evals_asset_contains_direct_no_tool_and_multistep_cases(self) -> None:
        evals = json.loads((EVAL_ASSETS / "webmcp-evals.example.json").read_text(encoding="utf-8"))
        self.assertTrue(any(item["expectedCall"] is None for item in evals))
        self.assertTrue(
            any(
                isinstance(node, dict) and "ordered" in node
                for item in evals
                if isinstance(item["expectedCall"], list)
                for node in item["expectedCall"]
            )
        )


if __name__ == "__main__":
    unittest.main()
