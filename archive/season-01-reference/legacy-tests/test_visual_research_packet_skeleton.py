from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path("/Users/mike/Agents_CascadeEffects")
SCRIPT_PATH = (
    ROOT
    / "references"
    / "skills"
    / "youtube_shorts_production_v1"
    / "scripts"
    / "visual_research_packet_skeleton.py"
)

spec = importlib.util.spec_from_file_location("visual_research_packet_skeleton", SCRIPT_PATH)
assert spec is not None
packet_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(packet_module)


class VisualResearchPacketSkeletonTests(unittest.TestCase):
    def test_generate_packet_uses_leaf_beats_and_timed_transcript(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-visual-research-packet-") as temp_dir:
            root = Path(temp_dir)
            narration_map = root / "narration_map.md"
            transcript = root / "caption_source.txt"
            narration_map.write_text(
                "\n".join(
                    [
                        "# Narration Map",
                        "",
                        "### `beat_01`",
                        "",
                        "- `spoken_cue_range`: `00:00:00.000-00:00:10.000`",
                        "- `visual_segments`: `beat_01a`, `beat_01b`",
                        "",
                        "#### `beat_01a`",
                        "",
                        "- `cue_range`: `00:00:00.000-00:00:04.000`",
                        "- `target_duration_seconds`: `4.000`",
                        "- `primary_subject`: `engineer at a launch tower terminal`",
                        "- `anomaly_carrier`: `warning posture inside the launch structure`",
                        "- `still_strategy`: `use a tower-side warning frame`",
                        "",
                        "#### `beat_01b`",
                        "",
                        "- `cue_range`: `00:00:04.000-00:00:10.000`",
                        "- `target_duration_seconds`: `6.000`",
                        "- `primary_subject`: `cold Challenger launch site`",
                        "- `anomaly_carrier`: `fixed shuttle in cold haze`",
                        "",
                        "### `beat_02`",
                        "",
                        "- `cue_range`: `00:00:10.000-00:00:16.000`",
                        "- `target_duration_seconds`: `6.000`",
                        "- `primary_subject`: `field-joint O-ring close-up`",
                        "- `anomaly_carrier`: `localized dark seam`",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            transcript.write_text(
                "\n".join(
                    [
                        "[00:00:00.000-00:00:02.000] SPEAKER_00: The first warning appears.",
                        "[00:00:04.100-00:00:09.000] SPEAKER_00: The shuttle remains fixed in cold haze.",
                        "[00:00:10.500-00:00:15.000] SPEAKER_00: The booster O-rings had shown erosion before.",
                    ]
                ),
                encoding="utf-8",
            )

            packet = packet_module.generate_packet(
                episode_id="challenger",
                short_id="challenger_short_test",
                narration_map_path=narration_map,
                caption_source_path=transcript,
                short_script_path="/tmp/script.txt",
                workflow_scope_manifest_path="/tmp/workflow_scope_manifest.md",
                dp_research_brief_path="/tmp/dp_research_brief.md",
                archival_footage_review_path="/tmp/archival_footage_review.md",
                dp_shot_packet_path="/tmp/shot_plan_v2.md",
                episode_constraint_ledger_path="/tmp/episode_constraint_ledger.md",
                exact_dp_imports=["/tmp/import_a.md"],
                audio_package_sha256="audio-sha",
            )

        self.assertIn("# Visual Research Packet - challenger_short_test", packet)
        self.assertIn("### `beat_01a`", packet)
        self.assertIn("### `beat_01b`", packet)
        self.assertIn("### `beat_02`", packet)
        self.assertNotIn("### `beat_01`\n", packet)
        self.assertIn("The first warning appears.", packet)
        self.assertIn("The booster O-rings had shown erosion before.", packet)
        self.assertIn("use a tower-side warning frame", packet)
        self.assertIn(
            "/Users/mike/Viz_CascadeEffects/references/style_packages/source_preserving_documentary_v1/SKILL.md",
            packet,
        )
        self.assertIn("- `narration_map_path`:", packet)
        self.assertIn("- `archival_footage_review_path`: `/tmp/archival_footage_review.md`", packet)
        self.assertIn("- `visual_beatmap_path`: `pending until DP derives after visual research`", packet)
        self.assertIn("- `artifact_selection_thesis`: `engaging and visually stimulating`", packet)
        self.assertIn("- `workflow_scope_manifest_path`: `/tmp/workflow_scope_manifest.md`", packet)
        self.assertIn("- `exact_dp_imports_used`: `/tmp/import_a.md`", packet)
        self.assertIn("- Keep archival source breadth narrow: `1-3` primary videos plus at most `2` backups.", packet)
        self.assertIn("- `candidate_artifact_total`: `0`", packet)
        self.assertIn("- `composition_mode`: `single_subject`", packet)
        self.assertIn("- `lead_artifact_id`: `TODO`", packet)
        self.assertIn("- `supporting_artifact_ids`: `TODO or none`", packet)
        self.assertIn("- `optional_accent_artifact_ids`: `TODO or none`", packet)
        self.assertIn("- `preferred_clip_ids`: `TODO or none if archival motion is not in scope for this beat`", packet)
        self.assertIn("- `footage_family_id`: `TODO or not_in_scope`", packet)
        self.assertIn("- `archive_reference_mode`: `reference_only`", packet)
        self.assertIn("- `texture_influence`: `none`", packet)
        self.assertIn("- `source_anchor_id`: `TODO`", packet)
        self.assertIn("- `carrier_mode`: `generated`", packet)
        self.assertIn("- `nonliteral_exception_approved`: `false`", packet)
        self.assertIn("- `object_cluster_rule`: `TODO if coverage_class is object_cluster; otherwise none`", packet)
        self.assertIn("#### Candidate Clips", packet)
        self.assertIn("- `source_anchor_map_complete`: `false`", packet)
        self.assertIn("- `artifact_rankings_complete`: `false`", packet)
        self.assertIn("- `may_enter_stills_contact_sheet`: `false`", packet)

    def test_parse_beat_plan_rejects_missing_leaf_beats(self) -> None:
        nodes = packet_module.parse_beat_plan("# Plan\n\n### `beat_01`\n\n- `notes`: `no leaves`\n")
        with self.assertRaisesRegex(Exception, "leaf beats"):
            packet_module.leaf_beats(nodes)


if __name__ == "__main__":
    unittest.main()
