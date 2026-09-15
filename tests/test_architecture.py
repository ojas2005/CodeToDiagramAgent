import unittest
from pathlib import Path

from code_to_diagram.extract import build_architecture
from code_to_diagram.render import render_mermaid
from code_to_diagram.source import read_worktree


FIXTURE = Path(__file__).resolve().parents[1] / "examples" / "auth_stack"


class ArchitectureTests(unittest.TestCase):
    def setUp(self):
        self.architecture = build_architecture(read_worktree(FIXTURE))

    def test_five_diagrams_cover_the_fixture(self):
        diagrams = self.architecture.diagrams
        self.assertEqual(set(diagrams), {"components", "api", "er", "auth", "dependencies"})
        self.assertIn("file:backend/app/auth.py", diagrams["components"].nodes)
        self.assertIn("route:POST:/login", diagrams["api"].nodes)
        self.assertTrue(any(edge.kind == "calls" for edge in diagrams["api"].edges.values()))
        self.assertIn("table:users", diagrams["er"].nodes)
        self.assertTrue(any(edge.kind == "foreign key" for edge in diagrams["er"].edges.values()))
        self.assertIn("service:redis", diagrams["dependencies"].nodes)
        self.assertIn("sequenceDiagram", render_mermaid(diagrams["auth"]))

    def test_every_detected_relationship_has_source_evidence(self):
        for diagram in self.architecture.diagrams.values():
            for edge in diagram.edges.values():
                self.assertTrue(edge.evidence, (diagram.kind, edge.key))
                for ref in edge.evidence:
                    self.assertIn(ref.path, read_worktree(FIXTURE).files)
                    self.assertGreater(ref.line, 0)

    def test_er_renderer_displays_fields(self):
        rendered = render_mermaid(self.architecture.diagrams["er"])
        self.assertIn("sessions }o--|| users", rendered)
        self.assertIn("user_id", rendered)


if __name__ == "__main__":
    unittest.main()
