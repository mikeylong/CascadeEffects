from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path("/Users/mike/Viz_CascadeEffects")
SCRIPT = ROOT / "scripts" / "validate_motion_contact_sheet_contract.py"


def base_candidate(**overrides: object) -> dict[str, object]:
    candidate: dict[str, object] = {
        "beat_id": "beat_01_denial_initial",
        "source_still_path": "/tmp/stills/beat_01.png",
        "source_still_variant_role": "primary",
        "motion_pipeline": "distilled",
        "model_repo": "mlx-community/LTX-2-distilled-bf16",
        "seed": 73101,
        "prompt_variant_id": "canonical_a",
        "prompt_text": "locked treatment-room motion, no text",
        "raw_clip_path": "/tmp/raw/beat_01.mp4",
        "normalized_clip_path": "/tmp/normalized/beat_01.mp4",
        "disposition": "diagnostic only",
        "selected_for_motion_proof": False,
    }
    candidate.update(overrides)
    return candidate


class MotionContactSheetContractTests(unittest.TestCase):
    def run_validator(self, path: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(path)],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_valid_json_allows_distilled_and_apple_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "motion_contact_sheet.json"
            path.write_text(
                json.dumps(
                    {
                        "motion_candidates": [
                            base_candidate(),
                            base_candidate(
                                beat_id="beat_05_reports_denial",
                                motion_pipeline="apple-ltx23-q8-one-stage",
                                model_repo="dgrauet/ltx-2.3-mlx-q8",
                                text_encoder_repo="mlx-community/gemma-3-12b-it-4bit",
                                prompt_variant_id="stability_b_human_tableau",
                            ),
                        ]
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            result = self.run_validator(path)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("OK", result.stdout)

    def test_apple_json_candidate_requires_text_encoder_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "motion_contact_sheet.json"
            path.write_text(
                json.dumps(
                    {
                        "motion_candidates": [
                            base_candidate(
                                motion_pipeline="apple-ltx23-q8-one-stage",
                                model_repo="dgrauet/ltx-2.3-mlx-q8",
                            )
                        ]
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            result = self.run_validator(path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("text_encoder_repo", result.stderr)

    def test_valid_markdown_with_contract_fields_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "motion_contact_sheet.md"
            path.write_text(
                "\n".join(
                    [
                        "- `beat_id`: `beat_05_reports_denial`",
                        "- `source_still_path`: `/tmp/beat_05.png`",
                        "- `source_still_variant_role`: `primary`",
                        "- `motion_pipeline`: `apple-ltx23-q8-one-stage`",
                        "- `model_repo`: `dgrauet/ltx-2.3-mlx-q8`",
                        "- `text_encoder_repo`: `mlx-community/gemma-3-12b-it-4bit`",
                        "- `seed`: `73502`",
                        "- `prompt_variant_id`: `stability_b_human_tableau`",
                        "- `prompt_text`: `operator remains fixed at the console`",
                        "- `raw_clip_path`: `/tmp/raw.mp4`",
                        "- `normalized_clip_path`: `/tmp/normalized.mp4`",
                        "- `disposition`: `diagnostic only`",
                        "- `selected_for_motion_proof`: `false`",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = self.run_validator(path)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_markdown_missing_normalized_clip_path_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "motion_contact_sheet.md"
            path.write_text(
                "\n".join(
                    [
                        "- `beat_id`: `beat_01_denial_initial`",
                        "- `source_still_path`: `/tmp/beat_01.png`",
                        "- `source_still_variant_role`: `primary`",
                        "- `motion_pipeline`: `distilled`",
                        "- `model_repo`: `mlx-community/LTX-2-distilled-bf16`",
                        "- `seed`: `73101`",
                        "- `prompt_variant_id`: `canonical_a`",
                        "- `prompt_text`: `locked treatment-room motion`",
                        "- `raw_clip_path`: `/tmp/raw.mp4`",
                        "- `disposition`: `diagnostic only`",
                        "- `selected_for_motion_proof`: `false`",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = self.run_validator(path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("normalized_clip_path", result.stderr)


if __name__ == "__main__":
    unittest.main()
