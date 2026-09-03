from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import webmcp_dual as dual  # noqa: E402


FIXTURE = SKILL_ROOT / "validation" / "fixtures" / "dual-shared-board"
CONTRACT = FIXTURE / "dual-contract.json"


def read_contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


class DualContractTests(unittest.TestCase):
    def test_fixture_contract_has_surface_and_shared_handler_parity(self) -> None:
        report = dual.validate_file(CONTRACT)
        self.assertEqual(report["status"], "PASS", report["findings"])
        self.assertEqual(
            report["summary"],
            {
                "operations": 4,
                "webmcpTools": 3,
                "mcpTools": 3,
                "sharedOperations": 2,
                "errors": 0,
                "warnings": 0,
            },
        )
        shared = [item for item in report["mappings"] if item["parity"] == "shared-handler"]
        self.assertEqual([item["handler"] for item in shared], ["inspectBoard", "addBoardItem"])
        self.assertTrue(all(item["webmcpTool"] != item["mcpTool"] for item in shared))

    def test_validator_rejects_cross_surface_tool_name_collision(self) -> None:
        contract = read_contract()
        contract["operations"][0]["surfaces"]["mcp"]["toolName"] = "inspect_visible_board"
        report = dual.validate_dual_contract(contract)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("surface.tool_name_collision", {item["code"] for item in report["findings"]})

    def test_validator_requires_a_shared_canonical_operation(self) -> None:
        contract = deepcopy(read_contract())
        for operation in contract["operations"]:
            if "webmcp" in operation["surfaces"] and "mcp" in operation["surfaces"]:
                del operation["surfaces"]["mcp"]
        report = dual.validate_dual_contract(contract)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("dual.shared_operation_missing", {item["code"] for item in report["findings"]})

    def test_report_is_deterministic(self) -> None:
        document = read_contract()
        self.assertEqual(dual.validate_dual_contract(document), dual.validate_dual_contract(document))


class DualExecutableFixtureTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is required for the dual fixture")
    def test_both_adapters_execute_against_one_state_and_operation_set(self) -> None:
        result = subprocess.run(
            ["node", str(FIXTURE / "run.mjs")],
            cwd=SKILL_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["sharedOperations"], ["board.inspect", "board.add_item"])
        self.assertEqual(report["finalRevision"], 2)
        self.assertEqual(report["auditSurfaces"], ["webmcp", "mcp"])
        self.assertEqual(report["pageClosedMcpInvocation"], "PASS")


if __name__ == "__main__":
    unittest.main()
