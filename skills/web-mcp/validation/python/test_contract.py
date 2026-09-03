from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import webmcp_contract as contract  # noqa: E402


EXAMPLES = SKILL_ROOT / "assets" / "examples"
FIXTURES = SKILL_ROOT / "validation" / "fixtures" / "contracts"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def set_path(document: object, path: tuple[object, ...], value: object) -> None:
    current = document
    for part in path[:-1]:
        current = current[part]  # type: ignore[index]
    current[path[-1]] = value  # type: ignore[index]


class ContractSchemaTests(unittest.TestCase):
    def test_all_bundled_schemas_are_valid_draft_2020_12(self) -> None:
        for name in contract.CONTRACTS:
            with self.subTest(contract=name):
                schema = contract.load_schema(name)
                self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_all_examples_validate(self) -> None:
        examples = (
            ("toolset.example.json", "toolset"),
            ("product.create-challenge.example.json", "product"),
            ("product.extend-dual.example.json", "product"),
            ("evidence.example.json", "evidence"),
            ("release.challenge.example.json", "release"),
        )
        for filename, kind in examples:
            with self.subTest(filename=filename):
                report = contract.validate_contract(read_json(EXAMPLES / filename), kind)
                self.assertEqual(report["status"], "PASS", report["findings"])
                self.assertEqual(report["structuralStatus"], "PASS")
                self.assertEqual(report["semanticStatus"], "PASS")

    def test_toolset_schema_and_runtime_structural_phase_have_parity(self) -> None:
        source = read_json(EXAMPLES / "toolset.example.json")
        mutations = (
            ("app name length", ("app", "name"), "x" * 121, "$/app/name"),
            ("app description length", ("app", "description"), "x" * 501, "$/app/description"),
            ("title length", ("tools", 0, "title"), "x" * 161, "$/tools/0/title"),
            ("handler length", ("tools", 0, "handler"), "h" + "x" * 160, "$/tools/0/handler"),
            ("owner length", ("tools", 0, "registration", "owner"), "x" * 301, "$/tools/0/registration/owner"),
            ("reversible type", ("tools", 0, "semantics", "reversible"), "yes", "$/tools/0/semantics/reversible"),
            ("failureModes type", ("tools", 0, "semantics", "failureModes"), "failed", "$/tools/0/semantics/failureModes"),
            ("input schema empty", ("tools", 0, "inputSchema"), {}, "$/tools/0/inputSchema"),
            ("app name whitespace", ("app", "name"), "   ", "$/app/name"),
            ("description whitespace", ("tools", 0, "description"), "   ", "$/tools/0/description"),
            ("visible effect whitespace", ("tools", 0, "semantics", "visibleEffect"), "   ", "$/tools/0/semantics/visibleEffect"),
            ("evidence whitespace", ("tools", 0, "semantics", "successEvidence", 0), "   ", "$/tools/0/semantics/successEvidence/0"),
            ("precondition whitespace", ("tools", 0, "semantics", "preconditions", 0), "   ", "$/tools/0/semantics/preconditions/0"),
        )
        for label, path, value, expected_path in mutations:
            with self.subTest(case=label):
                mutated = deepcopy(source)
                set_path(mutated, path, value)
                direct = [item.to_dict() for item in contract.structural_findings(mutated, "toolset")]
                report = contract.validate_contract(mutated, "toolset")
                reported_structure = [
                    item for item in report["findings"] if item["phase"] == "structural"
                ]
                key = lambda item: (item["path"], item["code"], item["message"])
                self.assertEqual(sorted(direct, key=key), sorted(reported_structure, key=key))
                self.assertEqual(report["structuralStatus"], "FAIL")
                self.assertEqual(report["semanticStatus"], "NOT_RUN")
                self.assertTrue(
                    any(item["path"].startswith(expected_path) for item in report["findings"]),
                    report["findings"],
                )

    def test_sensitive_purpose_is_structurally_nonblank(self) -> None:
        source = read_json(EXAMPLES / "toolset.example.json")
        source["tools"][0]["semantics"]["sensitiveInputs"] = [
            {"name": "seriesId", "purpose": "   "}
        ]
        report = contract.validate_contract(source, "toolset")
        self.assertEqual(report["structuralStatus"], "FAIL")
        self.assertTrue(
            any(item["path"].endswith("/purpose") for item in report["findings"]),
            report["findings"],
        )

    def test_non_document_registration_requires_named_owner(self) -> None:
        source = read_json(EXAMPLES / "toolset.example.json")
        del source["tools"][0]["registration"]["owner"]
        report = contract.validate_contract(source, "toolset")
        self.assertEqual(report["structuralStatus"], "FAIL")
        self.assertTrue(
            any(
                item["path"].startswith("$/tools/0/registration")
                and item["code"] == "schema.required"
                for item in report["findings"]
            ),
            report["findings"],
        )

        source["tools"][0]["registration"]["lifetime"] = "document"
        document_report = contract.validate_contract(source, "toolset")
        self.assertEqual(document_report["structuralStatus"], "PASS")

    def test_report_is_deterministic(self) -> None:
        document = read_json(FIXTURES / "toolset.semantic-invalid.json")
        first = contract.validate_contract(document, "toolset")
        second = contract.validate_contract(document, "toolset")
        self.assertEqual(first, second)


class ContractSemanticTests(unittest.TestCase):
    def test_valid_minimal_toolset_passes(self) -> None:
        report = contract.validate_file(FIXTURES / "toolset.valid-minimal.json", "toolset")
        self.assertEqual(report["status"], "PASS", report["findings"])

    def test_toolset_semantic_failures_are_not_schema_drift(self) -> None:
        report = contract.validate_file(FIXTURES / "toolset.semantic-invalid.json", "toolset")
        codes = {item["code"] for item in report["findings"]}
        self.assertEqual(report["structuralStatus"], "PASS")
        self.assertEqual(report["semanticStatus"], "FAIL")
        self.assertTrue(
            {
                "annotations.read_only_mismatch",
                "input_schema.required_unknown",
                "origin.not_origin_only",
            }.issubset(codes),
            codes,
        )

    def test_invalid_nested_input_schema_fails_semantically(self) -> None:
        report = contract.validate_file(
            FIXTURES / "toolset.input-schema-invalid.json", "toolset"
        )
        self.assertEqual(report["structuralStatus"], "PASS")
        self.assertEqual(report["semanticStatus"], "FAIL")
        self.assertIn("input_schema.invalid", {item["code"] for item in report["findings"]})

    def test_product_cross_field_rules(self) -> None:
        report = contract.validate_file(FIXTURES / "product.semantic-invalid.json", "product")
        codes = {item["code"] for item in report["findings"]}
        self.assertEqual(report["structuralStatus"], "PASS")
        self.assertTrue(
            {
                "product.document_disabled",
                "product.challenge_document_required",
                "product.challenge_host_required",
                "product.service_worker_session_unresolved",
            }.issubset(codes),
            codes,
        )

    def test_evidence_counts_status_receipts_and_reasons(self) -> None:
        report = contract.validate_file(FIXTURES / "evidence.semantic-invalid.json", "evidence")
        codes = {item["code"] for item in report["findings"]}
        self.assertEqual(report["structuralStatus"], "PASS")
        self.assertTrue(
            {
                "evidence.pass_without_receipt",
                "evidence.pass_nonzero_exit",
                "evidence.reason_required",
                "evidence.time_order",
                "evidence.count_mismatch",
                "evidence.status_mismatch",
            }.issubset(codes),
            codes,
        )

    def test_release_duplicate_claims_targets_and_unbacked_pass(self) -> None:
        report = contract.validate_file(FIXTURES / "release.semantic-invalid.json", "release")
        codes = {item["code"] for item in report["findings"]}
        self.assertEqual(report["structuralStatus"], "PASS")
        self.assertTrue(
            {
                "release.duplicate_claim",
                "release.duplicate_target",
                "release.pass_without_gate",
            }.issubset(codes),
            codes,
        )


class ContractBundleTests(unittest.TestCase):
    def test_complete_examples_bind_to_exact_candidate_and_evidence(self) -> None:
        product = read_json(EXAMPLES / "product.create-challenge.example.json")
        toolset = read_json(EXAMPLES / "toolset.example.json")
        evidence = read_json(EXAMPLES / "evidence.example.json")
        release = read_json(EXAMPLES / "release.challenge.example.json")
        report = contract.validate_bundle(product, toolset, evidence, release)
        self.assertEqual(report["status"], "PASS", report)
        self.assertEqual(report["bundleFindings"], [])

    def test_service_worker_selection_must_exist_and_be_background_safe(self) -> None:
        product = read_json(EXAMPLES / "product.create-challenge.example.json")
        toolset = read_json(EXAMPLES / "toolset.example.json")
        product["profiles"]["serviceWorkerProposal"] = {
            "enabled": True,
            "toolNames": ["missing_tool", "set_dashboard_date_range"],
            "stateModel": "stateless",
            "sessionStrategy": "not-required",
            "scope": "/",
            "workerPath": "./service-worker.js",
        }
        findings = contract.bundle_findings(product, toolset)
        codes = {item.code for item in findings}
        self.assertIn("bundle.service_worker_tool_unknown", codes)
        self.assertIn("bundle.service_worker_page_state_tool", codes)

    def test_claims_cannot_use_unknown_or_nonpassing_gates(self) -> None:
        product = read_json(EXAMPLES / "product.create-challenge.example.json")
        toolset = read_json(EXAMPLES / "toolset.example.json")
        evidence = read_json(EXAMPLES / "evidence.example.json")
        release = read_json(EXAMPLES / "release.challenge.example.json")
        release["claims"][0]["evidenceGateIds"] = [
            "service-worker.proposal",
            "missing-gate",
        ]
        findings = contract.bundle_findings(product, toolset, evidence, release)
        codes = {item.code for item in findings}
        self.assertIn("bundle.claim_gate_not_passed", codes)
        self.assertIn("bundle.claim_gate_unknown", codes)

    def test_candidate_hashes_are_bound_to_product_and_toolset(self) -> None:
        product = read_json(EXAMPLES / "product.create-challenge.example.json")
        toolset = read_json(EXAMPLES / "toolset.example.json")
        evidence = read_json(EXAMPLES / "evidence.example.json")
        release = read_json(EXAMPLES / "release.challenge.example.json")
        evidence["candidate"]["productSha256"] = "0" * 64
        evidence["candidate"]["toolsetSha256"] = "1" * 64
        findings = contract.bundle_findings(product, toolset, evidence, release)
        codes = {item.code for item in findings}
        self.assertIn("bundle.product_hash_mismatch", codes)
        self.assertIn("bundle.toolset_hash_mismatch", codes)


if __name__ == "__main__":
    unittest.main()
