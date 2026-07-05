from __future__ import annotations

import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ai_pipeline.cli import main  # noqa: E402


class ProjectEnvironmentTests(unittest.TestCase):
    def run_cli(self, args: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(args)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_new_creates_project_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"

            code, stdout, stderr = self.run_cli(
                ["new", str(root), "--run-id", "run-1"]
            )

            self.assertEqual(code, 0, stderr)
            self.assertIn("active stage: requirements", stdout)
            self.assertTrue((root / ".git").exists())
            self.assertTrue((root / "bin" / "activate").exists())
            self.assertTrue((root / "bin" / "ai-pipeline").exists())
            self.assertTrue((root / "bin" / "electroboy").exists())
            self.assertTrue(
                (
                    root
                    / ".agent-pipeline"
                    / "local"
                    / "runtime"
                    / "src"
                    / "ai_pipeline"
                ).exists()
            )
            self.assertTrue((root / ".agent-pipeline" / "project.toml").exists())
            self.assertTrue(
                (root / ".agent-pipeline" / "shared" / "current-run").exists()
            )
            self.assertTrue((root / "docs" / "requirements.md").exists())
            self.assertIn(
                ".agent-pipeline/local/",
                (root / ".gitignore").read_text(encoding="utf-8"),
            )

    def test_generated_wrapper_runs_without_pythonpath(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            self.assertEqual(self.run_cli(["new", str(root)])[0], 0)
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)

            completed = subprocess.run(
                [str(root / "bin" / "ai-pipeline"), "--help"],
                cwd=root,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            wrapper = (root / "bin" / "ai-pipeline").read_text(encoding="utf-8")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("usage: ai-pipeline", completed.stdout)
        self.assertNotIn(str(ROOT), wrapper)

    def test_new_reuses_existing_git_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            project = repo / "nested"
            repo.mkdir()
            subprocess.run(
                ["git", "-C", str(repo), "init"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            code, stdout, stderr = self.run_cli(
                ["new", str(project), "--run-id", "run-1"]
            )

            self.assertEqual(code, 0, stderr)
            self.assertIn("active stage: requirements", stdout)
            self.assertFalse((project / ".git").exists())
            self.assertTrue((repo / ".git").exists())

    def test_deactivate_records_activity_when_run_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(
                self.run_cli(["--root", str(root), "init", "--run-id", "run-1"])[0],
                0,
            )

            code, stdout, stderr = self.run_cli(["--root", str(root), "deactivate"])

            self.assertEqual(code, 0, stderr)
            self.assertIn("pipeline project deactivated", stdout)


if __name__ == "__main__":
    unittest.main()
