from __future__ import annotations

from pathlib import Path
import sys
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import webmcp_selftest as selftest  # noqa: E402


class SelfTestContractTests(unittest.TestCase):
    def test_status_precedence_is_fail_then_blocked_then_not_run(self) -> None:
        self.assertEqual(selftest._aggregate([{"status": "PASS"}]), "PASS")
        self.assertEqual(
            selftest._aggregate([{"status": "PASS"}, {"status": "NOT_RUN"}]),
            "NOT_RUN",
        )
        self.assertEqual(
            selftest._aggregate([{"status": "NOT_RUN"}, {"status": "BLOCKED"}]),
            "BLOCKED",
        )
        self.assertEqual(
            selftest._aggregate([{"status": "BLOCKED"}, {"status": "FAIL"}]),
            "FAIL",
        )

    def test_invalid_profile_and_timeout_are_rejected_before_execution(self) -> None:
        with self.assertRaises(selftest.SelfTestInputError):
            selftest.run_self_test("browser")
        with self.assertRaises(selftest.SelfTestInputError):
            selftest.run_self_test("core", timeout_seconds=0)

    def test_core_suite_includes_product_and_proposal_journeys(self) -> None:
        self.assertIn("product-create.test.mjs", selftest.CORE_NODE_TESTS)
        self.assertIn("proposals.test.mjs", selftest.CORE_NODE_TESTS)
        self.assertNotIn("typecheck.test.mjs", selftest.CORE_NODE_TESTS)


if __name__ == "__main__":
    unittest.main()
