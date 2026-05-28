import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path("/Users/mike/CascadeEffects/packages/media-pipeline/audio")
PROSODY_GUARD_PATH = REPO_ROOT / "scripts" / "prosody_guard.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ProsodyGuardUnitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module("prosody_guard_test", PROSODY_GUARD_PATH)

    def test_split_sentences_keeps_decimal_values_inside_one_sentence(self):
        sentences = self.mod.split_sentences("A memo says 0.053 inches. The joint is not sealing as designed.")

        self.assertEqual(len(sentences), 2)
        self.assertEqual(sentences[0].text, "A memo says 0.053 inches.")
        self.assertEqual(sentences[1].text, "The joint is not sealing as designed.")


if __name__ == "__main__":
    unittest.main()
