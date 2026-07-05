from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ai_pipeline.adapters.base import AgentInvocation  # noqa: E402
from ai_pipeline.config import parse_pipeline_config  # noqa: E402
from ai_pipeline.runtime import runtime_for_role  # noqa: E402


class RuntimeConfigTests(unittest.TestCase):
    def test_parse_runtime_config_selects_role_runtime(self) -> None:
        config = parse_pipeline_config(
            """
            [runtime]
            default = "manual"

            [runtimes.manual-review]
            adapter = "manual"
            command = "manual"
            env = ["PATH", "TOKEN"]
            response_file = "response.md"

            [roles]
            design_review = "manual-review"
            """
        )

        runtime = config.runtime_for_role("design_review")

        self.assertEqual(runtime.adapter, "manual")
        self.assertEqual(runtime.env, ["PATH", "TOKEN"])
        self.assertEqual(runtime.options["response_file"], "response.md")

    def test_manual_runtime_reads_configured_response_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "response.md").write_text("accepted\n", encoding="utf-8")
            (root / "agent-pipeline.toml").write_text(
                """
                [runtime]
                default = "manual"

                [runtimes.manual]
                adapter = "manual"
                command = "manual"
                response_file = "response.md"
                """,
                encoding="utf-8",
            )

            runtime = runtime_for_role("design_review", root)
            result = runtime.invoke(
                AgentInvocation(role="design_review", prompt="review"),
            )

        self.assertTrue(result.ok)
        self.assertEqual(result.final_message, "accepted\n")


if __name__ == "__main__":
    unittest.main()
