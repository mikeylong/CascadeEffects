import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_living_cover_script_locked_captions import (
    CaptionAlignmentError,
    build_script_locked_caption_package,
    iter_vtt_srt_cues,
    validate_caption_manifest_gate,
    validate_living_cover_manifest_gate,
)


def write_whisperx(path: Path, words: list[str], seconds_per_word: float = 0.2) -> None:
    word_segments = []
    cursor = 0.0
    for word in words:
        word_segments.append({"word": word, "start": cursor, "end": cursor + seconds_per_word})
        cursor += seconds_per_word
    path.write_text(json.dumps({"word_segments": word_segments}), encoding="utf-8")


def write_script(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def base_living_cover_manifest() -> dict:
    return {
        "caption_context": {
            "caption_text_source": {"path": "locked_script.txt", "sha256": "script-hash"},
            "caption_timing_source": {"path": "timing.vtt", "sha256": "timing-hash"},
            "caption_text_matches_script_read": "pass",
            "caption_alignment_coverage_read": "pass_0.991",
            "caption_asr_text_not_used_read": "pass",
        },
        "end_screen_context": {
            "end_screen_background_motion_policy": "continuous_ambient_background_under_static_youtube_targets",
            "end_screen_hold_read": "pass_static_youtube_target_geometry_background_expected_to_move",
            "youtube_target_geometry_static_read": "pass",
            "end_screen_title_policy_read": "pass_titleless_or_approved_episode_policy",
            "caption_suppression_read": "pass",
            "rail_fade_read": "pass",
            "continuous_ambient_end_screen_preservation_read": "pass_safe_window_frames_differ",
        },
        "rough_assembly_reads": {
            "caption_known_regression_fixture_read": "pass_too_weak_not_two_weeks",
            "stale_cross_episode_label_read": "pass",
        },
        "rail_behavior": {
            "active_panel_hierarchy": [
                "specific episode chapter label",
                "viewer-facing active beat title",
                "short episode-specific summary",
            ],
            "sections": [
                {"chapter": "Launch-Night Standard", "title": "The foam strike becomes the test"},
                {"chapter": "Reversal and Flight", "title": "The review process turns evidence away"},
            ],
        },
        "may_create_full_runtime_mp4_render": False,
        "may_advance_to_video_render": False,
        "may_advance_to_final_assembly": False,
        "may_advance_to_publish_readiness": False,
        "may_youtube_action": False,
    }


def final_render_manifest(*, disposition: str = "defer") -> dict:
    return {
        "gate": "final_assembly_gate",
        "human_disposition": disposition,
        "source_html_proof": {
            "packet_path": "rough_proof_packet",
            "manifest_path": "rough_assembly_manifest.json",
            "player_path": "player.html",
            "player_sha256": "player-hash",
        },
        "audio_source": {
            "path": "approved_mix.wav",
            "sha256": "audio-hash",
            "encode_policy": "encoded_to_aac_for_mp4_container",
        },
        "caption_package": {
            "visible_rail_captions_burned_in": True,
            "youtube_sidecar_vtt": {"path": "captions.vtt", "sha256": "caption-hash"},
        },
        "output": {
            "path": "episode_final_review_1080p24.mp4",
            "sha256": "mp4-hash",
            "duration_seconds": 1245.553,
        },
        "render_strategy": {
            "width": 1920,
            "height": 1080,
            "fps": 24,
            "audio_stream_copy_justification": "source WAV encoded to AAC for MP4 container",
        },
        "qa_reads": {
            "mp4_created_read": "pass",
            "video_stream_read": "pass_h264_present",
            "audio_stream_read": "pass_aac_audio_present",
            "audio_source_encode_read": "pass_aac_encoded_from_approved_wav_source",
            "duration_read": "pass",
            "dimensions_read": "pass",
            "fps_read": "pass",
            "full_decode_read": "pass",
            "caption_sidecar_read": "pass",
            "visible_rail_captions_burned_in_read": "pass",
            "downstream_gate_read": "pass_publish_and_youtube_flags_false",
            "current_kept_proof_render_source_read": "pass_rendered_from_current_kept_html_proof",
        },
    }


class ScriptLockedCaptionTests(unittest.TestCase):
    def build_package(
        self,
        script_text: str,
        asr_words: list[str],
        *,
        min_alignment_coverage: float = 0.985,
        max_unmatched_script_span: int = 8,
    ) -> tuple[dict, str, str]:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            script_path = tmp_path / "locked_script.txt"
            timing_path = tmp_path / "timing.whisperx.json"
            output_dir = tmp_path / "out"
            write_script(script_path, script_text)
            write_whisperx(timing_path, asr_words)
            qa = build_script_locked_caption_package(
                script_path=script_path,
                timing_path=timing_path,
                output_dir=output_dir,
                basename="episode",
                voice_offset_seconds=1.0,
                outro_cutoff_seconds=999.0,
                story_cutoff_seconds=None,
                max_chars_per_cue=54,
                max_words_per_cue=8,
                min_alignment_coverage=min_alignment_coverage,
                max_unmatched_script_span=max_unmatched_script_span,
            )
            story_vtt = (output_dir / "episode.script_locked_rail_safe.vtt").read_text(encoding="utf-8")
            offset_vtt = (
                output_dir / "episode.script_locked_rail_safe.offset_intro_1s000.vtt"
            ).read_text(encoding="utf-8")
            return qa, story_vtt, offset_vtt

    def test_homophone_uses_script_text_not_asr_text(self) -> None:
        prefix = " ".join(f"anchor{i}" for i in range(80))
        suffix = " ".join(f"tail{i}" for i in range(80))
        script_text = f"{prefix} final decision too weak to stop the machine {suffix}"
        asr_words = (
            prefix.split()
            + "final decision two weeks to stop the machine".split()
            + suffix.split()
        )

        qa, story_vtt, _ = self.build_package(script_text, asr_words)

        self.assertEqual(qa["reads"]["caption_text_matches_script_read"], "pass")
        self.assertIn("too weak", story_vtt)
        self.assertNotIn("two weeks", story_vtt)

    def test_performance_tags_are_removed_but_words_remain(self) -> None:
        qa, story_vtt, _ = self.build_package(
            "[calm]\nHello, world. [deliberate]\nKeep going.",
            "Hello world Keep going".split(),
            min_alignment_coverage=1.0,
        )

        self.assertEqual(qa["reads"]["caption_text_matches_script_read"], "pass")
        self.assertIn("Hello, world.", story_vtt)
        self.assertIn("Keep going.", story_vtt)
        self.assertNotIn("[calm]", story_vtt)
        self.assertNotIn("[deliberate]", story_vtt)

    def test_speaker_prefixes_in_asr_never_appear_in_output(self) -> None:
        qa, story_vtt, _ = self.build_package(
            "Warning signs stayed visible.",
            ["SPEAKER_00:", "Warning", "signs", "stayed", "visible"],
            min_alignment_coverage=1.0,
        )

        self.assertEqual(qa["reads"]["caption_asr_text_not_used_read"], "pass")
        self.assertNotIn("SPEAKER_00", story_vtt)
        self.assertIn("Warning signs stayed visible.", story_vtt)

    def test_large_script_audio_drift_fails_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            script_path = tmp_path / "locked_script.txt"
            timing_path = tmp_path / "timing.whisperx.json"
            write_script(script_path, " ".join(f"script{i}" for i in range(40)))
            write_whisperx(timing_path, [f"audio{i}" for i in range(40)])

            with self.assertRaises(CaptionAlignmentError):
                build_script_locked_caption_package(
                    script_path=script_path,
                    timing_path=timing_path,
                    output_dir=tmp_path / "out",
                    basename="episode",
                    voice_offset_seconds=0.0,
                    outro_cutoff_seconds=None,
                    story_cutoff_seconds=None,
                    max_chars_per_cue=54,
                    max_words_per_cue=8,
                    min_alignment_coverage=0.985,
                    max_unmatched_script_span=8,
                )

    def test_vtt_cues_ascend_and_respect_outro_cutoff(self) -> None:
        words = "one two three four five six seven eight nine ten".split()
        qa, _, offset_vtt = self.build_package(
            " ".join(words),
            words,
            min_alignment_coverage=1.0,
        )

        cues = list(iter_vtt_srt_cues(Path(write_temp_text(offset_vtt))))
        self.assertEqual(qa["reads"]["caption_no_caption_after_outro_start_read"], "pass")
        previous_end = -1.0
        for start, end, _ in cues:
            self.assertGreaterEqual(start, previous_end)
            self.assertGreater(end, start)
            self.assertLessEqual(end, 999.0)
            previous_end = end

    def test_manifest_blocks_advancement_when_caption_validation_is_missing_or_failing(self) -> None:
        failing_manifest = {
            "caption_context": {
                "caption_text_source": {"path": "locked_script.txt", "sha256": "abc"},
                "caption_timing_source": {"path": "timing.vtt", "sha256": "def"},
                "caption_text_matches_script_read": "fail",
                "caption_alignment_coverage_read": "pass",
                "caption_asr_text_not_used_read": "pass",
            },
            "may_advance_to_final_assembly": True,
            "may_advance_to_publish_readiness": True,
        }

        failing_report = validate_caption_manifest_gate(failing_manifest)
        self.assertEqual(failing_report["status"], "fail")
        self.assertIn("may_advance_to_final_assembly", failing_report["illegal_advancement_flags"])

        passing_manifest = {
            "caption_context": {
                "caption_text_source": {"path": "locked_script.txt", "sha256": "abc"},
                "caption_timing_source": {"path": "timing.vtt", "sha256": "def"},
                "caption_text_matches_script_read": "pass",
                "caption_alignment_coverage_read": "pass_0.991",
                "caption_asr_text_not_used_read": "pass",
            },
            "may_advance_to_final_assembly": True,
        }
        self.assertEqual(validate_caption_manifest_gate(passing_manifest)["status"], "pass")

    def test_living_cover_gate_accepts_static_youtube_geometry_with_continuous_ambient_motion(self) -> None:
        manifest = base_living_cover_manifest()

        report = validate_living_cover_manifest_gate(manifest)

        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["end_screen_gate_passes"])

    def test_living_cover_gate_rejects_old_whole_frame_end_screen_hold_semantics(self) -> None:
        manifest = base_living_cover_manifest()
        manifest["end_screen_context"]["end_screen_hold_read"] = "pass_final_safe_window_static_layout"

        report = validate_living_cover_manifest_gate(manifest)

        self.assertEqual(report["status"], "fail")
        self.assertEqual(
            report["failing_reads"]["end_screen_hold_read"],
            "pass_final_safe_window_static_layout",
        )

    def test_living_cover_gate_blocks_stale_cross_episode_rail_labels(self) -> None:
        manifest = base_living_cover_manifest()
        manifest["rail_behavior"]["sections"][0]["title"] = "Therac-25 bridge"

        report = validate_living_cover_manifest_gate(manifest)

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["stale_rail_label_violations"][0]["label"], "Therac-25 bridge")

    def test_final_render_contract_requires_current_kept_source_proof_and_sidecars(self) -> None:
        manifest = base_living_cover_manifest()
        manifest["mp4_render_created"] = True
        render_manifest = final_render_manifest()

        self.assertEqual(
            validate_living_cover_manifest_gate(manifest, render_manifest=render_manifest)["status"],
            "pass",
        )

        broken_render_manifest = final_render_manifest(disposition="keep")
        del broken_render_manifest["source_html_proof"]["player_sha256"]
        manifest["may_advance_to_publish_readiness"] = True

        report = validate_living_cover_manifest_gate(manifest, render_manifest=broken_render_manifest)

        self.assertEqual(report["status"], "fail")
        self.assertIn(
            "final_render_manifest.source_html_proof.packet_path/player_path/player_sha256/manifest_path",
            report["missing_fields"],
        )
        self.assertIn("may_advance_to_publish_readiness", report["illegal_advancement_flags"])

    def test_youtube_action_requires_publish_readiness_package_and_explicit_approval(self) -> None:
        manifest = base_living_cover_manifest()
        manifest["mp4_render_created"] = True
        manifest["may_youtube_action"] = True
        render_manifest = final_render_manifest(disposition="keep")

        report = validate_living_cover_manifest_gate(manifest, render_manifest=render_manifest)

        self.assertEqual(report["status"], "fail")
        self.assertIn(
            "may_youtube_action_without_explicit_publish_approval",
            report["illegal_advancement_flags"],
        )
        self.assertIn(
            "may_youtube_action_without_publish_readiness_package",
            report["illegal_advancement_flags"],
        )

    def test_challenger_script_locked_fixture_when_sources_are_available(self) -> None:
        script_path = Path(
            "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/audio/"
            "recording_20260511T204835Z_hybrid_attention_rewrite/scripts/"
            "challenger_longform_hybrid_attention_rewrite_20260511T204835Z.txt"
        )
        timing_path = Path(
            "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/audio/"
            "recording_20260511T204835Z_hybrid_attention_rewrite/transcripts/"
            "recording_20260511T204835Z_hybrid_attention_rewrite.diarized.corrected.vtt"
        )
        if not script_path.exists() or not timing_path.exists():
            self.skipTest("Challenger local caption sources are not available.")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            qa = build_script_locked_caption_package(
                script_path=script_path,
                timing_path=timing_path,
                output_dir=tmp_path,
                basename="challenger",
                voice_offset_seconds=9.601451,
                outro_cutoff_seconds=1214.763537,
                story_cutoff_seconds=1205.162086,
                max_chars_per_cue=54,
                max_words_per_cue=8,
                min_alignment_coverage=0.985,
                max_unmatched_script_span=8,
            )
            offset_vtt = tmp_path / "challenger.script_locked_rail_safe.offset_intro_9s601.vtt"
            text = offset_vtt.read_text(encoding="utf-8")

        self.assertEqual(qa["reads"]["caption_text_matches_script_read"], "pass")
        self.assertEqual(qa["reads"]["caption_asr_text_not_used_read"], "pass")
        self.assertGreaterEqual(qa["alignment"]["alignment_coverage"], 0.985)
        self.assertIn("then arrive at the final decision too weak", text)
        self.assertNotIn("then arrive at the final decision two weeks", text)


def write_temp_text(text: str) -> str:
    handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".vtt", delete=False)
    with handle:
        handle.write(text)
    return handle.name


if __name__ == "__main__":
    unittest.main()
