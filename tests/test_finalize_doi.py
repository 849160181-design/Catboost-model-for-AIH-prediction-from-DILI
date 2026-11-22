"""Tests for the DOI finalisation tool (public files + optional private manuscript)."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "finalize_doi.py"
PLACEHOLDER = "10.5281/zenodo.XXXXXXX"
REAL_DOI = "10.5281/zenodo.1234567"


class FinalizeDoiTest(unittest.TestCase):
    def run_script(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_public_dry_run(self):
        proc = self.run_script("--doi", REAL_DOI, "--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Public repository locations updated", proc.stdout)
        self.assertIn("not provided", proc.stdout)

    def test_private_manuscript_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "manuscript"
            folder.mkdir()
            for name in ("data_sharing_statement.md", "methods_reproducibility.md", "references.md"):
                (folder / name).write_text(f"DOI: {PLACEHOLDER}\n", encoding="utf-8")
            proc = self.run_script(
                "--doi", REAL_DOI, "--dry-run", "--manuscript-dir", str(folder)
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("Private manuscript locations verified", proc.stdout)

    def test_placeholder_is_rejected(self):
        proc = self.run_script("--doi", PLACEHOLDER, "--dry-run")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("placeholder", (proc.stdout + proc.stderr).lower())


if __name__ == "__main__":
    unittest.main()
