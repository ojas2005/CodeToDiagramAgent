import subprocess
import tempfile
import unittest
from pathlib import Path

from code_to_diagram.models import DiagramError
from code_to_diagram.source import read_revision, read_worktree


class SourceTests(unittest.TestCase):
    def test_skips_secrets_dependencies_and_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "app.py").write_text("print('ok')\n")
            (root / ".env").write_text("TOKEN=secret\n")
            (root / "node_modules").mkdir()
            (root / "node_modules" / "lib.js").write_text("secret")
            (root / "linked.py").symlink_to(root / "app.py")
            snapshot = read_worktree(root)
            self.assertEqual(set(snapshot.files), {"app.py"})

    def test_revision_uses_committed_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "app.py").write_text("old = 1\n")
            subprocess.run(["git", "-C", str(root), "add", "app.py"], check=True)
            subprocess.run(["git", "-C", str(root), "-c", "user.name=Test", "-c",
                            "user.email=test@example.com", "commit", "-qm", "initial"], check=True)
            (root / "app.py").write_text("new = 2\n")
            self.assertEqual(read_revision(root, "HEAD").files["app.py"], "old = 1\n")
            self.assertEqual(read_worktree(root).files["app.py"], "new = 2\n")
            with self.assertRaises(DiagramError):
                read_revision(root, "--bad")


if __name__ == "__main__":
    unittest.main()
