from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import webmcp_contract as contract  # noqa: E402
import webmcp_product as product_compiler  # noqa: E402


CREATE_FIXTURE = SKILL_ROOT / "validation" / "fixtures" / "create-shared-board" / "product.json"
DUAL_FIXTURE = SKILL_ROOT / "validation" / "fixtures" / "dual-shared-board" / "product.json"
EXAMPLE = SKILL_ROOT / "assets" / "examples" / "product.create-challenge.example.json"


class ProductCompilerTests(unittest.TestCase):
    def test_create_fixture_is_a_complete_capability_mapped_product(self) -> None:
        product, toolset, _, _, root = product_compiler.load_product_bundle(CREATE_FIXTURE)
        validation = contract.validate_bundle(product, toolset)
        self.assertEqual(validation["status"], "PASS", validation)
        plan = product_compiler.build_plan(product, toolset, root, "vanilla-js")
        self.assertEqual(plan["status"], "PASS", plan)
        self.assertEqual(plan["mode"], "CREATE")
        self.assertEqual(
            [item["operation"] for item in plan["capabilities"]],
            ["inspect-board", "add-board-item"],
        )
        self.assertTrue(all(item["resolved"] for item in plan["handlerReadiness"]["handlerMappings"]))

    def test_example_without_application_handlers_is_truthfully_blocked(self) -> None:
        product, toolset, _, _, root = product_compiler.load_product_bundle(EXAMPLE)
        plan = product_compiler.build_plan(product, toolset, root, "vanilla-js")
        self.assertEqual(plan["status"], "BLOCKED")
        self.assertEqual(
            {item["code"] for item in plan["handlerReadiness"]["blockers"]},
            {"HANDLER_NOT_FOUND"},
        )

    def test_extend_dual_allows_page_only_capability_and_shared_mcp_operations(self) -> None:
        product, toolset, _, _, root = product_compiler.load_product_bundle(DUAL_FIXTURE)
        validation = contract.validate_bundle(product, toolset)
        self.assertEqual(validation["status"], "WARN", validation)
        plan = product_compiler.build_plan(product, toolset, root, "vanilla-js")
        self.assertEqual(plan["mode"], "EXTEND")
        self.assertEqual(plan["surface"], "DUAL")
        self.assertEqual(plan["status"], "WARN")
        mappings = {item["operation"]: item for item in plan["capabilities"]}
        self.assertEqual(mappings["board.inspect"]["mcpTool"], "inspect_board_record")
        self.assertIsNone(mappings["board.select_visible_item"]["mcpTool"])

    def test_compile_is_deterministic_and_keeps_host_evidence_not_run(self) -> None:
        product, toolset, _, _, root = product_compiler.load_product_bundle(CREATE_FIXTURE)
        plan = product_compiler.build_plan(product, toolset, root, "vanilla-js")
        first = product_compiler.compile_artifacts(product, toolset, plan, "vanilla-js")
        second = product_compiler.compile_artifacts(product, toolset, plan, "vanilla-js")
        self.assertEqual(first, second)
        self.assertIn("registerWebMCPTools", first["webmcp-tools.js"])
        receipt = json.loads(first["webmcp-compile-receipt.json"])
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(receipt["nativeHostEvidence"], "NOT_RUN")

    def test_write_refuses_accidental_replacement(self) -> None:
        product, toolset, _, _, root = product_compiler.load_product_bundle(CREATE_FIXTURE)
        plan = product_compiler.build_plan(product, toolset, root, "vanilla-js")
        artifacts = product_compiler.compile_artifacts(product, toolset, plan, "vanilla-js")
        with tempfile.TemporaryDirectory() as temporary:
            receipts = product_compiler.write_artifacts(artifacts, temporary)
            self.assertEqual(len(receipts), 4)
            with self.assertRaises(product_compiler.ProductCompilerError):
                product_compiler.write_artifacts(artifacts, temporary)

    def test_bundle_rejects_handler_effect_and_revision_contract_drift(self) -> None:
        product, toolset, _, _, _ = product_compiler.load_product_bundle(CREATE_FIXTURE)
        changed = deepcopy(product)
        changed["capabilities"][0]["operation"]["handler"] = "missingHandler"
        changed["capabilities"][1]["operation"]["effect"] = "remote-write"
        changed["capabilities"][1]["concurrency"]["expectedRevisionField"] = "missingRevision"
        findings = contract.bundle_findings(changed, toolset)
        codes = {item.code for item in findings}
        self.assertTrue(
            {
                "bundle.capability_handler_mismatch",
                "bundle.capability_effect_mismatch",
                "bundle.revision_input_missing",
            }.issubset(codes),
            codes,
        )


if __name__ == "__main__":
    unittest.main()
