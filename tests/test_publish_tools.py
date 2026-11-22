"""Smoke tests for the release/publication tooling."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PublishToolTest(unittest.TestCase):
    def test_zenodo_dry_run(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "zenodo" / "publish.py"), "--dry-run"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("dry run only", proc.stdout)
        self.assertIn("archive:", proc.stdout)

    def test_github_script_syntax(self):
        proc = subprocess.run(
            ["bash", "-n", str(ROOT / "scripts" / "publish_github.sh")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_hygiene_tool_runs(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "check_repo_hygiene.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("failures: 0", proc.stdout)

    def test_dockerfile_uses_dependency_free_demo(self):
        text = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("quickstart/run_demo.sh", text)
        self.assertNotIn("pip install", text)


if __name__ == "__main__":
    unittest.main()
