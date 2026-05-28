import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "scripts" / "validate_video_visual_style.py"


class VideoVisualStyleValidatorTest(unittest.TestCase):
    def run_validator(self, body, *extra_args):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "artifact.md"
            artifact.write_text(body, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), *extra_args, str(artifact)],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            payload = json.loads(result.stdout)
            return result.returncode, payload

    def test_active_paper_architecture_source_art_fails(self):
        code, payload = self.run_validator(
            """
            candidate_status: ready_for_generation
            visual_profile: cascade-paper-architectures-ink-lit-v1
            Prompt: A 1920x1080 ink-lit Paper Architecture scene with a folded-paper aircraft.
            """,
        )
        self.assertNotEqual(code, 0)
        self.assertFalse(payload["ok"])
        self.assertIn("Paper Architecture visual style", payload["results"][0]["errors"][0])

    def test_invalidated_paper_architecture_artifact_passes_as_blocked_record(self):
        code, payload = self.run_validator(
            """
            status: rejected_wrong_longform_style_paper_architecture
            paper_architecture_resemblance_read: reject
            The prior folded-paper aircraft candidate is preserved only as a blocked record.
            """,
        )
        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])

    def test_superseded_keep_record_passes_as_blocked_record(self):
        code, payload = self.run_validator(
            """
            disposition: keep_superseded_wrong_longform_style_paper_architecture
            visual_profile: cascade-paper-architectures-ink-lit-v1
            long_form_source_art_lane_read: reject_paper_architecture_not_allowed_for_long_form_backplate
            paper_architecture_resemblance_read: reject
            """,
            "--require-style-reads",
        )
        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])

    def test_source_preserving_video_lane_with_reads_passes_required_read_preflight(self):
        code, payload = self.run_validator(
            """
            video_visual_style_scope_read: pass_video_asset_source_preserving
            paper_architecture_visual_style_read: pass_no_paper_architecture_visual_style
            Source-art prompt: ink-lit photoreal unbranded 737 MAX aircraft in a restrained hangar scene.
            """,
            "--require-style-reads",
        )
        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])

    def test_missing_required_reads_fail_when_requested(self):
        code, payload = self.run_validator(
            "Source-art prompt: ink-lit photoreal public-scene carrier.",
            "--require-style-reads",
        )
        self.assertNotEqual(code, 0)
        self.assertIn("missing required style reads", payload["results"][0]["errors"][0])

    def test_shorts_paper_architecture_candidate_fails(self):
        code, payload = self.run_validator(
            """
            workflow: youtube_shorts_production_v1
            stage: stills_keyframe_contact_sheet
            candidate_status: review_ready
            prompt: Human-Scale Paper System with foam-core terrain and folded-paper machinery.
            """,
        )
        self.assertNotEqual(code, 0)
        self.assertFalse(payload["ok"])


if __name__ == "__main__":
    unittest.main()
