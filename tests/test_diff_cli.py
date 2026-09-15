import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path

from code_to_diagram.cli import main
from code_to_diagram.diff import compare, update_changed_diagrams
from code_to_diagram.extract import build_architecture
from code_to_diagram.source import read_revision


class DiffCliTests(unittest.TestCase):
    def commit(self, root, message):
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "-c", "user.name=Test", "-c",
                        "user.email=test@example.com", "commit", "-qm", message], check=True)
        return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()

    def test_diff_updates_only_changed_diagrams(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "routes.py").write_text('from fastapi import FastAPI\napp = FastAPI()\n@app.get("/health")\ndef health(): pass\n')
            base = self.commit(root, "health")
            (root / "routes.py").write_text((root / "routes.py").read_text() +
                                          '@app.post("/login")\ndef login(): pass\n')
            head = self.commit(root, "login")
            before = build_architecture(read_revision(root, base))
            after = build_architecture(read_revision(root, head))
            changes = compare(before, after)
            self.assertTrue(changes["api"].changed)
            self.assertTrue(changes["auth"].changed)
            self.assertFalse(changes["er"].changed)
            out = root / "diagrams"
            self.assertEqual(set(update_changed_diagrams(after, changes, out, root)), {"api", "auth"})
            self.assertFalse((out / "er.mmd").exists())
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["diff", "--repo", str(root), "--base", base,
                                       "--head", head, "--out", str(out)]), 0)
            self.assertIn("Added nodes", (out / "CHANGES.md").read_text())


if __name__ == "__main__":
    unittest.main()
