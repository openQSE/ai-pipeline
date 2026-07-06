from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from electroboy.planning import planned_phases  # noqa: E402


class PlanTests(unittest.TestCase):
    def test_planned_phases_parse_clean_heading_and_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_file(
                root / "docs" / "implementation-plan.md",
                "# Plan\n\n"
                "## Phase 1. First Work\n\n"
                "Requirements: REQ-1\n"
                "Paths: src/electroboy\n"
                "Paths: tests\n",
            )

            phases = planned_phases(root)

        self.assertEqual(phases[0].heading, "Phase 1. First Work")
        self.assertEqual(phases[0].paths, ["src/electroboy", "tests"])


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
