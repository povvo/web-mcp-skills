from __future__ import annotations

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

import webmcp_proposals as proposals  # noqa: E402


class ProposalStatusTests(unittest.TestCase):
    def test_source_evidence_is_portable_official_https(self) -> None:
        for profile in proposals.proposal_status()["profiles"].values():
            self.assertTrue(profile["sourceEvidence"])
            self.assertTrue(
                all(source.startswith("https://") for source in profile["sourceEvidence"]),
                profile,
            )

    def test_every_profile_denies_current_conformance_claims(self) -> None:
        status = proposals.proposal_status()
        self.assertEqual(status["generatorVersion"], proposals.GENERATOR_VERSION)
        self.assertEqual(set(status["profiles"]), {"declarative", "service-worker"})
        for profile in status["profiles"].values():
            with self.subTest(profile=profile["id"]):
                self.assertEqual(profile["maturity"], "PROPOSAL")
                self.assertEqual(profile["chatgptSiteToolsSupport"], "UNSUPPORTED")
                self.assertEqual(profile["documentApiConformance"], "NOT_CLAIMED")
                self.assertEqual(profile["browserConformance"], "NOT_RUN")
                self.assertEqual(profile["testEvidence"], "MOCK_ONLY")

    def test_service_worker_profile_is_dependency_injected(self) -> None:
        rendered = proposals.render_proposal(
            "service-worker",
            tool_name="queue_background_item",
            description="Queue one item through a proposal-only background adapter.",
        )
        self.assertIn("DEPENDENCY_INJECTED_PROPOSAL_MOCK", rendered)
        self.assertNotIn("self.agent", rendered)
        self.assertNotIn("provideContext", rendered)
        self.assertNotIn("document.modelContext", rendered)


class ProposalGenerationTests(unittest.TestCase):
    def test_declarative_generation_uses_official_cancellation_spelling(self) -> None:
        rendered = proposals.render_proposal(
            "declarative",
            tool_name="search_catalog",
            description="Search the visible catalog using the existing form path.",
        )
        self.assertIn('addEventListener("toolcanceled"', rendered)
        self.assertIsNone(re.search(r'addEventListener\("toolcancel"\s*,', rendered))
        self.assertNotIn("__TOOL_NAME_", rendered)
        self.assertNotIn("toolautosubmit>", rendered)

    def test_auto_submit_is_explicit_and_declarative_only(self) -> None:
        rendered = proposals.render_proposal(
            "declarative",
            tool_name="preview_selection",
            description="Preview the selected records.",
            auto_submit=True,
        )
        self.assertIn("\n  toolautosubmit>", rendered)
        with self.assertRaisesRegex(proposals.ProposalError, "applies only"):
            proposals.render_proposal(
                "service-worker",
                tool_name="preview_selection",
                description="Preview the selected records.",
                auto_submit=True,
            )

    def test_generation_writes_inseparable_status_metadata_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory(prefix="webmcp-proposals-") as temporary:
            output = Path(temporary)
            result = proposals.generate_proposal(
                "service-worker",
                output_dir=output,
                tool_name="queue_record",
                description="Queue one record through a proposal mock.",
            )
            artifact = Path(result["artifact"])
            sidecar = Path(result["statusMetadata"])
            self.assertTrue(artifact.is_file())
            self.assertTrue(sidecar.is_file())
            metadata = json.loads(sidecar.read_text(encoding="utf-8"))
            self.assertEqual(metadata["profile"]["maturity"], "PROPOSAL")
            self.assertEqual(metadata["profile"]["specificationSupport"], "UNSUPPORTED")
            self.assertEqual(metadata["verification"]["templateRendered"], "PASS")
            self.assertEqual(metadata["verification"]["mockTests"], "NOT_RUN")
            self.assertEqual(metadata["verification"]["nativeInvocation"], "NOT_RUN")
            with self.assertRaisesRegex(proposals.ProposalError, "refusing to overwrite"):
                proposals.generate_proposal(
                    "service-worker",
                    output_dir=output,
                    tool_name="queue_record",
                    description="Queue one record through a proposal mock.",
                )

    def test_generation_rejects_nonportable_tool_names(self) -> None:
        with self.assertRaisesRegex(proposals.ProposalError, "tool name"):
            proposals.render_proposal(
                "declarative",
                tool_name="Search flights",
                description="Invalid because the machine name contains a space.",
            )


if __name__ == "__main__":
    unittest.main()
