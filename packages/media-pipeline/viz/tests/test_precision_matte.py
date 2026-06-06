from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ModuleNotFoundError:  # pragma: no cover - environment-specific skip
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]


ROOT = Path("/Users/mike/CascadeEffects")
SCRIPTS_DIR = ROOT / "packages/media-pipeline/viz/scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

if Image is not None:
    from precision_matte import (  # noqa: E402
        DEFAULT_CHOKE_PX,
        DEFAULT_FEATHER_PX,
        FALLBACK_CHOKE_PX,
        apply_precision_matte,
        has_intermediate_alpha,
        write_edge_proof,
        write_precision_matte_receipt,
    )


@unittest.skipIf(Image is None, "Pillow is required for precision matte tests.")
class PrecisionMatteTests(unittest.TestCase):
    def _write_binary_mask(self, path: Path) -> None:
        mask = Image.new("L", (120, 80), 0)
        draw = ImageDraw.Draw(mask)
        draw.rectangle((24, 12, 92, 70), fill=255)
        mask.save(path)

    def test_precision_matte_adds_intermediate_alpha(self) -> None:
        mask = Image.new("L", (120, 80), 0)
        draw = ImageDraw.Draw(mask)
        draw.rectangle((24, 12, 92, 70), fill=255)
        repaired = apply_precision_matte(mask)
        self.assertTrue(has_intermediate_alpha(repaired))

    def test_validator_rejects_binary_repaired_mask(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            raw_path = root / "raw.png"
            repaired_path = root / "repaired.png"
            proof_path = root / "proof.png"
            receipt_path = root / "receipt.json"
            self._write_binary_mask(raw_path)
            self._write_binary_mask(repaired_path)
            write_edge_proof(Image.open(raw_path), Image.open(repaired_path), proof_path)
            write_precision_matte_receipt(
                receipt_path=receipt_path,
                raw_mask_path=raw_path,
                repaired_mask_path=repaired_path,
                before_after_edge_proof_path=proof_path,
                choke_px=DEFAULT_CHOKE_PX,
                feather_px=DEFAULT_FEATHER_PX,
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "packages/production-tools/scripts/validate_precision_matte_contract.py"),
                    "--receipt",
                    str(receipt_path),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("binary-only", result.stdout)

    def test_fallback_choke_requires_reason(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            raw_path = root / "raw.png"
            repaired_path = root / "repaired.png"
            proof_path = root / "proof.png"
            receipt_path = root / "receipt.json"
            self._write_binary_mask(raw_path)
            repaired = apply_precision_matte(Image.open(raw_path), choke_px=FALLBACK_CHOKE_PX)
            repaired.save(repaired_path)
            write_edge_proof(Image.open(raw_path), repaired, proof_path)
            write_precision_matte_receipt(
                receipt_path=receipt_path,
                raw_mask_path=raw_path,
                repaired_mask_path=repaired_path,
                before_after_edge_proof_path=proof_path,
                choke_px=FALLBACK_CHOKE_PX,
                feather_px=DEFAULT_FEATHER_PX,
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "packages/production-tools/scripts/validate_precision_matte_contract.py"),
                    "--receipt",
                    str(receipt_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("thin-detail reason", result.stderr)

    def test_valid_precision_matte_receipt_passes_cli(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            raw_path = root / "raw.png"
            repaired_path = root / "repaired.png"
            proof_path = root / "proof.png"
            receipt_path = root / "receipt.json"
            self._write_binary_mask(raw_path)
            repaired = apply_precision_matte(Image.open(raw_path))
            repaired.save(repaired_path)
            write_edge_proof(Image.open(raw_path), repaired, proof_path)
            write_precision_matte_receipt(
                receipt_path=receipt_path,
                raw_mask_path=raw_path,
                repaired_mask_path=repaired_path,
                before_after_edge_proof_path=proof_path,
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "packages/production-tools/scripts/validate_precision_matte_contract.py"),
                    "--receipt",
                    str(receipt_path),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
