"""Jury packaging checks, exercised only in a complete jury bundle."""
import json
import tempfile
import unittest
from pathlib import Path

from src.ml_data import ROOT
from judge import fingerprint, verify_bundle


class JuryBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / "jury_bundle_manifest.json").exists():
            raise unittest.SkipTest("Jury bundle manifest is not present in this checkout")

    def test_text_hash_is_cross_platform(self):
        with tempfile.TemporaryDirectory() as directory:
            lf, crlf = Path(directory) / "lf.txt", Path(directory) / "crlf.txt"
            lf.write_bytes(b"a\nb\n")
            crlf.write_bytes(b"a\r\nb\r\n")
            self.assertEqual(fingerprint(lf, "text_lf"), fingerprint(crlf, "text_lf"))
            self.assertNotEqual(fingerprint(lf), fingerprint(crlf))

    def test_bundle_complete_and_checksummed(self):
        manifest = verify_bundle()
        included = {row["path"] for row in manifest["files"]}
        self.assertIn("data/final/training_dataset.parquet", included)
        self.assertIn("predictions/validation_predictions.parquet", included)
        self.assertTrue(any(path.endswith(".joblib") for path in included))
        self.assertFalse(any("data/cache/" in path or ".deps/" in path for path in included))

    def test_original_model_training_source_fingerprint_is_retained(self):
        registry = json.loads((ROOT / "models/model_registry.json").read_text(encoding="utf-8"))
        manifest = json.loads((ROOT / "experiments" / registry["run_id"] / "run_manifest.json").read_text(encoding="utf-8"))
        for filename, expected in manifest["inputs"].items():
            path = ROOT / filename
            mode = "text_lf" if path.suffix in {".py", ".json"} else "binary"
            self.assertEqual(fingerprint(path, mode), expected, filename)


if __name__ == "__main__":
    unittest.main()
