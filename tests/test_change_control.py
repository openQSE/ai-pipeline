from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ai_pipeline.cli import main  # noqa: E402
from ai_pipeline.gates import GateEngine  # noqa: E402
from ai_pipeline.models import (  # noqa: E402
    GATE_DESIGN,
    GATE_DOCUMENTATION,
    GATE_HUMAN_DESIGN_ACCEPTANCE,
    GATE_IMPLEMENTATION,
    GATE_REQUIREMENTS,
    GATE_VALIDATION_TESTING,
    STAGE_COMPLETE,
    STAGE_DESIGN,
)
from ai_pipeline.state_store import StateStore  # noqa: E402


class ChangeControlTests(unittest.TestCase):
    def run_cli(self, args: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(args)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_classified_change_request_still_blocks_transitions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = StateStore(root)
            manifest = store.init_run(run_id="run-1")
            open_code, _open_stdout, open_stderr = self.run_cli(
                [
                    "--root",
                    str(root),
                    "change",
                    "open",
                    "--baseline",
                    "design",
                    "--reason",
                    "Validation found design drift.",
                ]
            )
            classify_code, classify_stdout, classify_stderr = self.run_cli(
                [
                    "--root",
                    str(root),
                    "change",
                    "classify",
                    "CR-0001",
                    "--baseline",
                    "requirements",
                ]
            )

            result = GateEngine(root).stage_order("requirements", manifest)
            requests = store.read_change_requests()

            self.assertEqual(open_code, 0, open_stderr)
            self.assertEqual(classify_code, 0, classify_stderr)
            self.assertIn("baseline: requirements", classify_stdout)
            self.assertFalse(result.passed)
            self.assertEqual(requests[0]["status"], "classified")
            self.assertEqual(requests[0]["baseline"], "requirements")

    def test_reopen_invalidates_downstream_gates_and_resumes_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = StateStore(root)
            manifest = store.init_run(run_id="run-1")
            for gate in [
                GATE_REQUIREMENTS,
                GATE_DESIGN,
                GATE_HUMAN_DESIGN_ACCEPTANCE,
                GATE_IMPLEMENTATION,
                GATE_VALIDATION_TESTING,
                GATE_DOCUMENTATION,
            ]:
                manifest.complete_gate(gate)
            manifest.set_active_stage(STAGE_COMPLETE)
            store.save_manifest(manifest)
            self.assertEqual(
                self.run_cli(
                    [
                        "--root",
                        str(root),
                        "change",
                        "open",
                        "--baseline",
                        "design",
                        "--reason",
                        "The design must be corrected.",
                    ]
                )[0],
                0,
            )

            code, stdout, stderr = self.run_cli(
                ["--root", str(root), "change", "reopen", "CR-0001"]
            )
            manifest = store.load_current_manifest()
            requests = store.read_change_requests()
            order = GateEngine(root).stage_order(STAGE_DESIGN, manifest)

            self.assertEqual(code, 0, stderr)
            self.assertIn("active stage: design", stdout)
            self.assertEqual(manifest.active_stage, STAGE_DESIGN)
            self.assertTrue(manifest.has_gate(GATE_REQUIREMENTS))
            self.assertFalse(manifest.has_gate(GATE_DESIGN))
            self.assertFalse(manifest.has_gate(GATE_IMPLEMENTATION))
            self.assertEqual(requests[0]["status"], "reopened")
            self.assertTrue(order.passed)


if __name__ == "__main__":
    unittest.main()
