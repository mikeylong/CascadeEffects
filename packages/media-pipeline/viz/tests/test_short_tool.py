from __future__ import annotations

import json
import subprocess
import shutil
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from unittest import mock

from PIL import Image


ROOT = Path("/Users/mike/CascadeEffects/packages/media-pipeline/viz")
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from short_tool import (  # noqa: E402
    PIPELINE_MANIFEST_SUFFIX,
    HOUSE_CRT_FINAL_CONTRACT_ID,
    HOUSE_CRT_FINAL_INTENSITY,
    HOUSE_CRT_FINAL_LEGACY_CALIBRATION_RECIPE_ID,
    HOUSE_CRT_FINAL_PROFILE_ID,
    HOUSE_CRT_FINAL_SCANLINE_BAND_PIXELS,
    HOUSE_CRT_FINAL_SCANLINE_DELTA_Y,
    HOUSE_CRT_FINAL_SCANLINE_PERIOD_PIXELS,
    HOUSE_CRT_FINAL_SCANLINE_POLICY_ID,
    HOUSE_CRT_FINAL_SCANLINE_STRENGTH_VARIANT_ID,
    HOUSE_CRT_FINAL_TEXTURE_RENDERER_SOURCE,
    HOUSE_CRT_FINAL_TONE_POLICY,
    HOUSE_CRT_STATIC_DURATION_SECONDS,
    HOUSE_CRT_STATIC_PROFILE_ID,
    ShortBuilder,
    fallback_caption_segments_from_transcript,
    parse_caption_timing_file,
    split_caption_segments_for_style,
    CAPTION_STYLE_PRESETS,
    caption_style_with_placement,
    compute_motif_outro_mix_timing,
    duration_to_frames,
    file_sha256,
    find_motif_caption_span,
    ffprobe_video_info,
    parse_args,
)


class ShortToolTests(unittest.TestCase):
    def make_builder(self, models_root: Path) -> ShortBuilder:
        return ShortBuilder(
            repo_root=ROOT,
            models_root=models_root,
            comfy_workflows_dir=ROOT / "workflows" / "generated",
            comfy_output_dir=ROOT / "renders",
            references_root=ROOT / "references",
        )

    def make_final_export_fixture(self, temp_root: Path) -> tuple[ShortBuilder, Path, Path, Path]:
        builder = self.make_builder(temp_root / "models")
        build_dir = temp_root / "build"
        build_dir.mkdir(parents=True, exist_ok=True)
        proof_path = build_dir / "proof.mp4"
        audio_path = build_dir / "audio.wav"
        transcript_path = build_dir / "transcript.txt"
        review_note_path = build_dir / "motion_review.md"
        effective_jobs_path = build_dir / "effective_final_jobs.elevenlabs.jsonl"
        audio_package_path = build_dir / "audio_package.json"
        proof_manifest_path = build_dir / "20260101T000000Z__proof.json"
        proof_path.write_text("proof", encoding="utf-8")
        audio_path.write_text("audio", encoding="utf-8")
        transcript_path.write_text(
            "The system made the wrong behavior feel normal. Then the warning became background noise.",
            encoding="utf-8",
        )
        effective_jobs_path.write_text(
            json.dumps(
                {
                    "elevenlabs_model_id": "eleven_multilingual_v2",
                    "elevenlabs_voice_settings": {"speed": 0.95},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        audio_package_payload = {
            "provider": "elevenlabs",
            "voice": "dPrTCMw2R7HQlznlgwCO",
            "model": "eleven_multilingual_v2",
            "effective_manifest_path": str(effective_jobs_path),
            "packaged_path": str(audio_path),
            "packaged_sha256": file_sha256(audio_path),
            "packaged_at": "2026-01-01T00:00:00Z",
            "transcript_path": str(transcript_path),
            "transcript_sha256": file_sha256(transcript_path),
            "qa_completed_at": "2026-01-01T00:01:00Z",
        }
        audio_package_path.write_text(json.dumps(audio_package_payload, indent=2) + "\n", encoding="utf-8")
        review_note_path.write_text("# Motion Proof Review\n\nDisposition: keep\n", encoding="utf-8")
        proof_manifest_path.write_text(
            json.dumps(
                {
                    "short_id": "caption_export_short",
                    "episode_id": "caption_export",
                    "title": "Caption Export Short",
                    "proof_path": str(proof_path),
                    "audio_path": str(audio_path),
                    "transcript_path": str(transcript_path),
                    "short_audio_package_path": str(audio_package_path),
                    "expected_voice_profile_id": "youtube_shorts_mike_challenger_match_v1",
                    "audio_package_sha256": file_sha256(audio_package_path),
                    "packaged_audio_sha256": file_sha256(audio_path),
                    "audio_disposition": "keep",
                    "caption_source_path": str(transcript_path),
                    "caption_text_source_path": str(transcript_path),
                    "caption_timing_source_path": str(transcript_path),
                    "caption_text_matches_script_read": "pass",
                    "caption_alignment_coverage_read": "pass",
                    "transcript_sha256": file_sha256(transcript_path),
                    "fps": 24,
                    "disposition": "keep",
                    "reel_class": "keeper short",
                    "beats": [
                        {
                            "id": "beat_01",
                            "cue_start_seconds": 0.0,
                            "cue_end_seconds": 2.0,
                            "motion_disposition": "keep",
                        },
                        {
                            "id": "beat_02",
                            "cue_start_seconds": 2.0,
                            "cue_end_seconds": 4.0,
                            "motion_disposition": "keep",
                        },
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return builder, proof_manifest_path, review_note_path, transcript_path

    def house_crt_final_gate_payload(self, proof_manifest_path: Path, motion_bed_path: Path) -> dict[str, object]:
        return {
            "source_proof_manifest_path": str(proof_manifest_path),
            "house_crt_contract_id": HOUSE_CRT_FINAL_CONTRACT_ID,
            "house_crt_contract_read": {
                "house_crt_contract_id": HOUSE_CRT_FINAL_CONTRACT_ID,
            },
            "house_crt_texture_read": {
                "house_crt_contract_id": HOUSE_CRT_FINAL_CONTRACT_ID,
                "profile_id": HOUSE_CRT_FINAL_PROFILE_ID,
                "intensity": HOUSE_CRT_FINAL_INTENSITY,
                "texture_tone_policy": HOUSE_CRT_FINAL_TONE_POLICY,
                "calibration_recipe_id": HOUSE_CRT_FINAL_LEGACY_CALIBRATION_RECIPE_ID,
                "legacy_calibration_recipe_id": HOUSE_CRT_FINAL_LEGACY_CALIBRATION_RECIPE_ID,
                "texture_renderer_source": HOUSE_CRT_FINAL_TEXTURE_RENDERER_SOURCE,
                "scanline_policy_id": HOUSE_CRT_FINAL_SCANLINE_POLICY_ID,
                "scanline_strength_variant_id": HOUSE_CRT_FINAL_SCANLINE_STRENGTH_VARIANT_ID,
                "scanline_delta_y": HOUSE_CRT_FINAL_SCANLINE_DELTA_Y,
                "scanline_period_pixels": HOUSE_CRT_FINAL_SCANLINE_PERIOD_PIXELS,
                "scanline_band_pixels": HOUSE_CRT_FINAL_SCANLINE_BAND_PIXELS,
            },
            "luma_chroma_metrics_read": {
                "overall_read": "pass",
                "max_abs_luma_yavg_delta": 1.4,
            },
            "source_lineage_read": {
                "clean_source_confirmed": True,
                "selected_source_mode": "single_clean_no_caption_visual_source",
                "selected_source_rejections": [],
                "selected_segment_source_paths": ["/tmp/source_clean.mp4"],
            },
            "randomized_static_transition_read": {
                "read": "superseded_label_use_signal_interruption_read",
            },
            "visual_layer_order_read": {
                "visual_layer_sequence": [
                    "approved_no_caption_motion_or_proof_source",
                    "historical_signal_conservative_clean_normalization",
                    "luma_neutral_visible_scanline_house_crt_texture",
                    "challenger_style_signal_interruption_at_eligible_outgoing_cut_tails",
                    "final_duration_tail_visual_handling",
                    "caption_burn_last_visual_layer",
                    "audio_mux_stream_only_after_caption_burn",
                ],
                "motion_source_contains_captions": False,
                "texture_applied_before_captions": True,
                "signal_interruption_applied_before_captions": True,
                "caption_burn_is_last_visual_operation": True,
                "post_caption_visual_effects_applied": False,
            },
            "signal_interruption_read": {
                "house_crt_contract_id": HOUSE_CRT_FINAL_CONTRACT_ID,
                "profile_id": HOUSE_CRT_STATIC_PROFILE_ID,
                "duration_seconds": HOUSE_CRT_STATIC_DURATION_SECONDS,
                "timing_policy": "replace_outgoing_segment_tail_preserve_total_duration",
                "render_policy": "mutate_outgoing_footage_tail_no_full_frame_static_cards",
                "full_frame_static_replacement_used": False,
                "eligible_cut_count": 2,
                "applied_cut_count": 2,
            },
            "outputs": {
                "motion_full_duration_no_audio_path": str(motion_bed_path),
            },
        }

    def make_short_manifest_audio_self_contained(
        self,
        builder: ShortBuilder,
        payload: dict[str, object],
        temp_root: Path,
    ) -> None:
        temp_root.mkdir(parents=True, exist_ok=True)
        audio_path = temp_root / "audio.wav"
        transcript_path = temp_root / "transcript.txt"
        package_path = temp_root / "audio_package.json"
        duration_seconds = sum(
            float(beat.get("target_duration_seconds") or 0.0)
            if beat.get("target_duration_seconds") is not None
            else float(beat.get("cue_end_seconds", 0.0)) - float(beat.get("cue_start_seconds", 0.0))
            for beat in payload.get("beats", [])
            if isinstance(beat, dict)
        )
        frame_rate = 44100
        frame_count = max(1, int(round(max(duration_seconds, 1.0) * frame_rate)))
        with wave.open(str(audio_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(frame_rate)
            wav_file.writeframes(b"\x00\x00" * frame_count)
        transcript_path.write_text("Unit transcript for manifest validation.", encoding="utf-8")
        expected_profile_id = str(payload["expected_voice_profile_id"])
        profile = builder.load_short_voice_profiles()[expected_profile_id]
        package_payload = {
            "provider": profile["provider"],
            "voice": profile["voice"],
            "model": profile["model"],
            "packaged_path": str(audio_path),
            "packaged_sha256": file_sha256(audio_path),
            "transcript_path": str(transcript_path),
            "transcript_sha256": file_sha256(transcript_path),
            "disposition": "keep",
        }
        package_path.write_text(json.dumps(package_payload, indent=2) + "\n", encoding="utf-8")
        payload["audio_path"] = str(audio_path)
        payload["short_audio_package_path"] = str(package_path)
        payload["audio_package_sha256"] = file_sha256(package_path)
        payload["packaged_audio_sha256"] = file_sha256(audio_path)
        payload["caption_source_path"] = str(transcript_path)
        payload["transcript_path"] = str(transcript_path)
        payload["transcript_sha256"] = file_sha256(transcript_path)
        payload["audio_disposition"] = "keep"

    def make_historical_signal_video(
        self,
        temp_root: Path,
        name: str,
        *,
        audio: bool = False,
        size: str = "90x160",
        duration: float = 1.0,
    ) -> Path:
        output_path = temp_root / name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if audio:
            command = [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                f"testsrc2=size={size}:rate=24:duration={duration}",
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency=440:sample_rate=48000:duration={duration}",
                "-shortest",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-movflags",
                "+faststart",
                str(output_path),
            ]
        else:
            command = [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                f"testsrc2=size={size}:rate=24:duration={duration}",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                "-an",
                str(output_path),
            ]
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        if completed.returncode != 0:
            self.fail(completed.stderr.strip() or completed.stdout.strip() or "ffmpeg fixture generation failed")
        return output_path.resolve()

    def write_historical_signal_motion_manifest(
        self,
        temp_root: Path,
        source_path: Path,
        *,
        row_key: str = "items",
        profile_id: str | None = "era_1980s_broadcast_crt_v1",
        texture_influence: str = "house_crt",
        disposition: str = "keep",
        extra_row: dict[str, object] | None = None,
    ) -> Path:
        row: dict[str, object] = {
            "row_id": "edl_01",
            "order": 1,
            "shot_id": "shot_01",
            "texture_influence": texture_influence,
            "disposition": disposition,
            "normalized_no_audio_path": str(source_path),
            "hygiene_read": "pass",
            "strict_clean_read": "pass",
            "source_clean_read": "pass",
            "temporal_coherence_read": "pass",
            "physical_plausibility_read": "pass",
            "source_motion_alignment_read": "pass",
            "historical_context_year_or_range": "1980-1989",
            "source_media_era": "analog_broadcast_video",
        }
        if profile_id is not None:
            row["historical_signal_profile_id"] = profile_id
        if extra_row:
            row.update(extra_row)
        manifest_path = temp_root / "motion_manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "episode_id": "fixture_episode",
                    "short_id": "fixture_short",
                    row_key: [row],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return manifest_path.resolve()

    def test_duration_to_frames_rounds_manifest_durations(self) -> None:
        self.assertEqual(duration_to_frames(9.493, 24), 228)
        self.assertEqual(duration_to_frames(3.585, 24), 86)

    def test_parse_args_accepts_export_midjourney(self) -> None:
        argv = [
            "short_tool.py",
            "--repo-root",
            "/tmp/repo",
            "--models-root",
            "/tmp/models",
            "--comfy-workflows-dir",
            "/tmp/workflows",
            "--comfy-output-dir",
            "/tmp/output",
            "--references-root",
            "/tmp/references",
            "export-midjourney",
            "challenger_short_minimal_surreal_v1",
        ]
        with mock.patch.object(sys, "argv", argv):
            args = parse_args()
        self.assertEqual(args.command, "export-midjourney")
        self.assertEqual(args.short_id, "challenger_short_minimal_surreal_v1")

    def test_parse_args_accepts_build_delivery_mode(self) -> None:
        argv = [
            "short_tool.py",
            "--repo-root",
            "/tmp/repo",
            "--models-root",
            "/tmp/models",
            "--comfy-workflows-dir",
            "/tmp/workflows",
            "--comfy-output-dir",
            "/tmp/output",
            "--references-root",
            "/tmp/references",
            "build",
            "challenger_short_minimal_surreal_v1",
            "--delivery-mode",
            "advisory",
            "--quality-profile",
            "fast",
        ]
        with mock.patch.object(sys, "argv", argv):
            args = parse_args()
        self.assertEqual(args.command, "build")
        self.assertEqual(args.delivery_mode, "advisory")
        self.assertEqual(args.quality_profile, "fast")

    def test_parse_args_accepts_build_clip_mode(self) -> None:
        argv = [
            "short_tool.py",
            "--repo-root",
            "/tmp/repo",
            "--models-root",
            "/tmp/models",
            "--comfy-workflows-dir",
            "/tmp/workflows",
            "--comfy-output-dir",
            "/tmp/output",
            "--references-root",
            "/tmp/references",
            "build",
            "challenger_short_minimal_surreal_v3_trimmed",
            "--clip-mode",
            "still_holds",
        ]
        with mock.patch.object(sys, "argv", argv):
            args = parse_args()
        self.assertEqual(args.command, "build")
        self.assertEqual(args.clip_mode, "still_holds")

    def test_parse_args_accepts_final_export_gate_flags(self) -> None:
        argv = [
            "short_tool.py",
            "--repo-root",
            "/tmp/repo",
            "--models-root",
            "/tmp/models",
            "--comfy-workflows-dir",
            "/tmp/workflows",
            "--comfy-output-dir",
            "/tmp/output",
            "--references-root",
            "/tmp/references",
            "final-export",
            "/tmp/build/20260101T000000Z__proof.json",
            "--proof-review-note",
            "/tmp/review.md",
            "--proof-disposition",
            "keep",
            "--reel-class",
            "keeper-short",
            "--all-motion-clips-keep",
            "--no-diagnostic-placeholders",
            "--caption-style",
            "documentary_lower_third_v1",
            "--caption-placement",
            "lower-left",
            "--caption-timing",
            "/tmp/captions.srt",
            "--output-tag",
            "keeper_v1",
            "--source-motion-tail-path",
            "/tmp/tail.mp4",
            "--source-motion-tail-source-clip-id",
            "TAC02-SC02-color-collapse-0325-0349",
            "--source-motion-tail-source-path",
            "/tmp/source.mp4",
            "--source-motion-tail-span-in",
            "5.222",
            "--source-motion-tail-span-out",
            "8.722",
            "--house-crt-static-manifest",
            "/tmp/house_crt_static_manifest.json",
        ]
        with mock.patch.object(sys, "argv", argv):
            args = parse_args()
        self.assertEqual(args.command, "final-export")
        self.assertEqual(args.proof_disposition, "keep")
        self.assertEqual(args.reel_class, "keeper-short")
        self.assertTrue(args.all_motion_clips_keep)
        self.assertTrue(args.no_diagnostic_placeholders)
        self.assertEqual(args.caption_style, "documentary_lower_third_v1")
        self.assertEqual(args.caption_placement, "lower-left")
        self.assertEqual(args.music_policy, "canonical_default")
        self.assertEqual(args.music_track_id, "paper_architecture_theme_v1")
        self.assertEqual(args.source_motion_tail_path, "/tmp/tail.mp4")
        self.assertEqual(args.source_motion_tail_source_clip_id, "TAC02-SC02-color-collapse-0325-0349")
        self.assertEqual(args.source_motion_tail_source_path, "/tmp/source.mp4")
        self.assertAlmostEqual(args.source_motion_tail_span_in, 5.222)
        self.assertAlmostEqual(args.source_motion_tail_span_out, 8.722)
        self.assertAlmostEqual(args.source_motion_tail_residual_hold_max, 0.15)
        self.assertEqual(args.house_crt_static_manifest, "/tmp/house_crt_static_manifest.json")
        self.assertEqual(args.house_crt_static_waiver_reason, "")
        alias_argv = [
            item if item != "--house-crt-static-manifest" else "--house-crt-final-gate-manifest"
            for item in argv
        ]
        with mock.patch.object(sys, "argv", alias_argv):
            alias_args = parse_args()
        self.assertEqual(alias_args.house_crt_static_manifest, "/tmp/house_crt_static_manifest.json")

    def test_parse_args_accepts_music_policy_overrides(self) -> None:
        argv = [
            "short_tool.py",
            "--repo-root",
            "/tmp/repo",
            "--models-root",
            "/tmp/models",
            "--comfy-workflows-dir",
            "/tmp/workflows",
            "--comfy-output-dir",
            "/tmp/output",
            "--references-root",
            "/tmp/references",
            "final-export",
            "/tmp/build/20260101T000000Z__proof.json",
            "--proof-review-note",
            "/tmp/review.md",
            "--proof-disposition",
            "keep",
            "--reel-class",
            "keeper-short",
            "--all-motion-clips-keep",
            "--no-diagnostic-placeholders",
            "--music-policy",
            "waived",
            "--music-waiver-reason",
            "approved silent treatment",
            "--music-rights-check-status",
            "not_applicable",
        ]
        with mock.patch.object(sys, "argv", argv):
            args = parse_args()
        self.assertEqual(args.music_policy, "waived")
        self.assertEqual(args.music_waiver_reason, "approved silent treatment")
        self.assertEqual(args.music_rights_check_status, "not_applicable")

    def test_parse_args_accepts_historical_signal_texture(self) -> None:
        argv = [
            "short_tool.py",
            "--repo-root",
            "/tmp/repo",
            "--models-root",
            "/tmp/models",
            "--comfy-workflows-dir",
            "/tmp/workflows",
            "--comfy-output-dir",
            "/tmp/output",
            "--references-root",
            "/tmp/references",
            "historical-signal-texture",
            "/tmp/motion_manifest.json",
            "--pass-id",
            "pass_01_texture_review",
            "--review-note-output",
            "/tmp/production/historical_signal_texture_review.md",
            "--output-root",
            "/tmp/texture_packages",
            "--profile",
            "era_1980s_broadcast_crt_v1",
            "--strength",
            "visible_but_premium",
        ]
        with mock.patch.object(sys, "argv", argv):
            args = parse_args()
        self.assertEqual(args.command, "historical-signal-texture")
        self.assertEqual(args.motion_manifest_path, "/tmp/motion_manifest.json")
        self.assertEqual(args.pass_id, "pass_01_texture_review")
        self.assertEqual(args.review_note_output, "/tmp/production/historical_signal_texture_review.md")
        self.assertEqual(args.output_root, "/tmp/texture_packages")
        self.assertEqual(args.profile, "era_1980s_broadcast_crt_v1")
        self.assertEqual(args.strength, "visible_but_premium")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe required")
    def test_historical_signal_texture_writes_pending_review_package(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-hist-signal-") as temp_dir:
            root = Path(temp_dir)
            builder = self.make_builder(root / "models")
            source_clip = self.make_historical_signal_video(root, "source_no_audio.mp4")
            motion_manifest_path = self.write_historical_signal_motion_manifest(root, source_clip)
            output_manifest_path = builder.historical_signal_texture(
                motion_manifest_path,
                pass_id="pass_01_texture_review",
                review_note_output=root / "production" / "historical_signal_texture_review.md",
                output_root=root / "texture_packages",
            )

            json_tool = subprocess.run(
                [sys.executable, "-m", "json.tool", str(output_manifest_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(json_tool.returncode, 0, json_tool.stderr)
            payload = json.loads(output_manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["stage"], "historical_signal_texture")
            self.assertEqual(payload["disposition"], "tighten")
            self.assertEqual(payload["historical_signal_texture_read"], "pending_human_review")
            self.assertEqual(payload["texture_visibility_read"], "pending_human_review")
            self.assertEqual(payload["texture_readability_read"], "pending_human_review")
            self.assertEqual(payload["machine_checks_read"], "pass")
            self.assertFalse(payload["may_start_motion_video_proof"])
            self.assertFalse(payload["may_start_video_final"])
            self.assertEqual(payload["candidate_count"], 1)
            self.assertTrue(Path(payload["review_note_path"]).exists())
            self.assertTrue(Path(payload["review_sheet_path"]).exists())
            self.assertIn("proof assembly and final export intentionally not performed", " ".join(payload["blockers"]))

            item = payload["items"][0]
            self.assertEqual(item["historical_signal_profile_id"], "era_1980s_broadcast_crt_v1")
            self.assertEqual(item["signal_texture_strength"], "visible_but_premium")
            self.assertEqual(item["texture_influence"], "house_crt")
            self.assertEqual(item["texture_application_scope"], "house_crt_story_clips")
            self.assertEqual(item["house_crt_texture_read"], "pending_human_review")
            self.assertEqual(item["randomized_static_transition_read"], "not_applicable")
            self.assertEqual(item["disposition"], "tighten")
            self.assertEqual(item["historical_signal_texture_read"], "pending_human_review")
            self.assertEqual(item["youtube_survival_read"], "pending_human_review")
            self.assertEqual(item["texture_readability_read"], "pending_human_review")
            self.assertEqual(item["machine_checks_read"], "pass")
            source_info = ffprobe_video_info(source_clip)
            for path_key in (
                "conservative_clean_path",
                "texture_applied_path",
                "youtube_survival_proxy_path",
            ):
                output_path = Path(item[path_key])
                self.assertTrue(output_path.exists(), path_key)
                output_info = ffprobe_video_info(output_path)
                self.assertEqual((output_info["width"], output_info["height"]), (90, 160))
                self.assertEqual(output_info["audio_stream_count"], 0)
                self.assertLess(abs(output_info["duration_seconds"] - source_info["duration_seconds"]), 0.25)
            for variant in ("baseline", "texture_applied", "youtube_proxy"):
                for frame_path in item["frame_audit_paths"][variant].values():
                    self.assertTrue(Path(frame_path).exists())

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe required")
    def test_historical_signal_texture_rejects_inactive_period_profile_override(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-hist-signal-1940s-") as temp_dir:
            root = Path(temp_dir)
            builder = self.make_builder(root / "models")
            source_clip = self.make_historical_signal_video(root, "source_no_audio.mp4")
            motion_manifest_path = self.write_historical_signal_motion_manifest(
                root,
                source_clip,
                row_key="rows",
                profile_id=None,
                extra_row={
                    "historical_context_year_or_range": "1940-1949",
                    "source_media_era": "analog_archival_film",
                },
            )
            with self.assertRaisesRegex(Exception, "unsupported historical signal profile"):
                builder.historical_signal_texture(
                    motion_manifest_path,
                    pass_id="pass_02_1940s_texture_review",
                    review_note_output=root / "production" / "historical_signal_texture_review.md",
                    output_root=root / "texture_packages",
                    profile="era_1940s_archival_film_v1",
                    strength="low",
                )

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe required")
    def test_historical_signal_texture_accepts_proof_level_visual_noaudio_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-hist-signal-proof-") as temp_dir:
            root = Path(temp_dir)
            builder = self.make_builder(root / "models")
            source_clip = self.make_historical_signal_video(root, "proof_visual_noaudio.mp4")
            proof_manifest_path = root / "proof_manifest.json"
            proof_manifest_path.write_text(
                json.dumps(
                    {
                        "episode_id": "hyatt-regency",
                        "short_id": "hyatt_short_scoped_v1",
                        "proof_id": "pass_11_scene_led_no_freeze_44s",
                        "disposition": "keep",
                        "reel_class": "keeper short",
                        "visual_noaudio_path": str(source_clip),
                        "historical_signal_profile_id": "era_1980s_broadcast_crt_v1",
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            output_manifest_path = builder.historical_signal_texture(
                proof_manifest_path,
                pass_id="pass_12_challenger_match",
                review_note_output=root / "production" / "historical_signal_texture_review.md",
                output_root=root / "texture_packages",
                strength="visible_but_premium",
            )

            payload = json.loads(output_manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["candidate_count"], 1)
            item = payload["items"][0]
            self.assertEqual(item["row_id"], "pass_11_scene_led_no_freeze_44s")
            self.assertEqual(item["source_motion_clip_path"], str(source_clip))
            self.assertEqual(item["historical_signal_profile_id"], "era_1980s_broadcast_crt_v1")
            self.assertEqual(item["signal_texture_strength"], "visible_but_premium")
            self.assertTrue(Path(item["texture_applied_path"]).exists())
            self.assertTrue(Path(item["youtube_survival_proxy_path"]).exists())

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe required")
    def test_historical_signal_texture_accepts_shot_vertical_clip_rows(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-hist-signal-shots-") as temp_dir:
            root = Path(temp_dir)
            builder = self.make_builder(root / "models")
            source_clip = self.make_historical_signal_video(root, "shot_vertical.mp4")
            proof_manifest_path = root / "proof_manifest.json"
            proof_manifest_path.write_text(
                json.dumps(
                    {
                        "episode_id": "hyatt-regency",
                        "short_id": "hyatt_short_scoped_v1",
                        "proof_id": "pass_11_scene_led_no_freeze_44s",
                        "disposition": "keep",
                        "historical_signal_profile_id": "era_1980s_broadcast_crt_v1",
                        "shots": [
                            {
                                "shot_id": "hyatt_p11_001_event_sign_hook",
                                "vertical_clip_path": str(source_clip),
                            }
                        ],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            output_manifest_path = builder.historical_signal_texture(
                proof_manifest_path,
                pass_id="pass_12_challenger_match_shots",
                review_note_output=root / "production" / "historical_signal_texture_review.md",
                output_root=root / "texture_packages",
                strength="visible_but_premium",
            )

            payload = json.loads(output_manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["candidate_count"], 1)
            item = payload["items"][0]
            self.assertEqual(item["row_id"], "hyatt_p11_001_event_sign_hook")
            self.assertEqual(item["source_motion_clip_path"], str(source_clip))
            self.assertEqual(item["texture_influence"], "house_crt")
            self.assertEqual(item["signal_texture_strength"], "visible_but_premium")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe required")
    def test_historical_signal_texture_rejects_invalid_inputs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-hist-signal-reject-") as temp_dir:
            root = Path(temp_dir)
            builder = self.make_builder(root / "models")
            source_clip = self.make_historical_signal_video(root, "source_no_audio.mp4")

            unsupported_manifest = self.write_historical_signal_motion_manifest(
                root,
                source_clip,
                profile_id="era_2090s_fake_profile_v1",
            )
            with self.assertRaisesRegex(Exception, "unsupported historical signal profile"):
                builder.historical_signal_texture(
                    unsupported_manifest,
                    pass_id="pass_bad_profile",
                    review_note_output=root / "review_bad_profile.md",
                    output_root=root / "bad_profile_out",
                )

            conflict_manifest = self.write_historical_signal_motion_manifest(root, source_clip)
            with self.assertRaisesRegex(Exception, "conflicts with --profile"):
                builder.historical_signal_texture(
                    conflict_manifest,
                    pass_id="pass_conflict",
                    review_note_output=root / "review_conflict.md",
                    output_root=root / "conflict_out",
                    profile="era_1940s_archival_film_v1",
                )

            no_eligible_manifest = self.write_historical_signal_motion_manifest(
                root,
                source_clip,
                texture_influence="none",
            )
            with self.assertRaisesRegex(Exception, "no keep rows with texture_influence house_crt"):
                builder.historical_signal_texture(
                    no_eligible_manifest,
                    pass_id="pass_no_eligible",
                    review_note_output=root / "review_no_eligible.md",
                    output_root=root / "no_eligible_out",
                )

            unsupported_strength_manifest = self.write_historical_signal_motion_manifest(
                root,
                source_clip,
                extra_row={"signal_texture_strength": "unmistakable_review_visible"},
            )
            with self.assertRaisesRegex(Exception, "unsupported signal texture strength"):
                builder.historical_signal_texture(
                    unsupported_strength_manifest,
                    pass_id="pass_bad_strength",
                    review_note_output=root / "review_bad_strength.md",
                    output_root=root / "bad_strength_out",
                )

            square_clip = self.make_historical_signal_video(root, "square_no_audio.mp4", size="160x160")
            square_manifest = self.write_historical_signal_motion_manifest(root, square_clip)
            with self.assertRaisesRegex(Exception, "portrait 9:16"):
                builder.historical_signal_texture(
                    square_manifest,
                    pass_id="pass_square",
                    review_note_output=root / "review_square.md",
                    output_root=root / "square_out",
                )

            audio_clip = self.make_historical_signal_video(root, "source_with_audio.mp4", audio=True)
            audio_manifest = self.write_historical_signal_motion_manifest(root, audio_clip)
            with self.assertRaisesRegex(Exception, "must be no-audio"):
                builder.historical_signal_texture(
                    audio_manifest,
                    pass_id="pass_audio",
                    review_note_output=root / "review_audio.md",
                    output_root=root / "audio_out",
                )

            missing_source_manifest = self.write_historical_signal_motion_manifest(root, source_clip)
            missing_payload = json.loads(missing_source_manifest.read_text(encoding="utf-8"))
            for key in (
                "visual_noaudio_path",
                "normalized_no_audio_path",
                "normalized_clip_path",
                "vertical_clip_path",
                "source_motion_clip_path",
                "source_clip_path",
                "source_path",
                "output_path",
                "motion_clip_path",
                "clean_motion_path",
            ):
                missing_payload["items"][0].pop(key, None)
            missing_source_manifest.write_text(json.dumps(missing_payload, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(Exception, "has no source clip path"):
                builder.historical_signal_texture(
                    missing_source_manifest,
                    pass_id="pass_missing_source",
                    review_note_output=root / "review_missing_source.md",
                    output_root=root / "missing_source_out",
                )

            failed_hygiene_manifest = self.write_historical_signal_motion_manifest(
                root,
                source_clip,
                extra_row={"hygiene_read": "fail"},
            )
            with self.assertRaisesRegex(Exception, "cannot enter historical_signal_texture because hygiene_read"):
                builder.historical_signal_texture(
                    failed_hygiene_manifest,
                    pass_id="pass_failed_hygiene",
                    review_note_output=root / "review_failed_hygiene.md",
                    output_root=root / "failed_hygiene_out",
                )

            with self.assertRaisesRegex(Exception, "motion_manifest_path must be an absolute path"):
                builder.historical_signal_texture(
                    Path("relative_manifest.json"),
                    pass_id="pass_relative_manifest",
                    review_note_output=root / "review_relative_manifest.md",
                    output_root=root / "relative_manifest_out",
                )
            with self.assertRaisesRegex(Exception, "--review-note-output must be an absolute path"):
                builder.historical_signal_texture(
                    conflict_manifest,
                    pass_id="pass_relative_review",
                    review_note_output=Path("relative_review.md"),
                    output_root=root / "relative_review_out",
                )
            with mock.patch("short_tool.HISTORICAL_SIGNAL_TEXTURE_REGISTRY_PATH", root / "missing_registry.json"):
                with self.assertRaisesRegex(Exception, "registry is missing"):
                    builder.load_historical_signal_profiles()

    def test_parse_caption_timing_file_reads_srt_segments(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-caption-srt-") as temp_dir:
            timing_path = Path(temp_dir) / "captions.srt"
            timing_path.write_text(
                "\n".join(
                    [
                        "1",
                        "00:00:00,000 --> 00:00:01,400",
                        "A warning light stayed quiet.",
                        "",
                        "2",
                        "00:00:01,400 --> 00:00:03,000",
                        "Then the system made the wrong failure normal.",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            segments = parse_caption_timing_file(timing_path)
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0]["start_seconds"], 0.0)
        self.assertEqual(segments[0]["end_seconds"], 1.4)
        self.assertEqual(segments[1]["text"], "Then the system made the wrong failure normal.")

    def test_caption_style_segmentation_strips_speaker_and_splits_long_srt_cues(self) -> None:
        segments = [
            {
                "segment_id": "caption_001",
                "start_seconds": 0.0,
                "end_seconds": 8.0,
                "text": (
                    "SPEAKER_00: A simple design change turned an approved structure into a death trap, "
                    "and no one caught it because everyone assumed someone else had checked."
                ),
            }
        ]
        refined = split_caption_segments_for_style(
            segments,
            CAPTION_STYLE_PRESETS["documentary_lower_third_v1"],
        )
        self.assertGreater(len(refined), 1)
        self.assertNotIn("SPEAKER_00", " ".join(segment["text"] for segment in refined))
        self.assertLessEqual(max(len(segment["text"]) for segment in refined), 56)
        self.assertEqual(refined[0]["start_seconds"], 0.0)
        self.assertEqual(refined[-1]["end_seconds"], 8.0)

    def test_caption_style_with_placement_applies_lower_left_override(self) -> None:
        style = caption_style_with_placement("documentary_lower_third_v1", "lower-left")
        self.assertEqual(style["alignment"], 1)
        self.assertEqual(style["placement"], "mobile-safe lower-left third")
        self.assertEqual(style["max_line_chars"], 22)

    def test_caption_style_with_placement_supports_early_1980s_broadcast_cg(self) -> None:
        style = caption_style_with_placement("early_1980s_broadcast_cg_v1", "lower-left")
        self.assertEqual(style["font_name"], "Andale Mono")
        self.assertEqual(style["alignment"], 1)
        self.assertEqual(style["max_line_chars"], 20)
        self.assertEqual(style["period_reference"], "early-1980s broadcast character generator, not late-1980s desktop UI")

    def test_caption_style_with_placement_supports_1940s_newsreel_lower_left(self) -> None:
        style = caption_style_with_placement("era_1940s_newsreel_ivory_v1", "lower-left")
        self.assertEqual(style["font_name"], "Futura Condensed ExtraBold")
        self.assertEqual(style["font_color"], "&H00C8E8F2")
        self.assertEqual(style["alignment"], 1)
        self.assertEqual(style["placement"], "mobile-safe lower-left third")

    def test_caption_style_with_placement_supports_contemporary_aviation_news(self) -> None:
        style = caption_style_with_placement("contemporary_aviation_news_v1", "lower-left")
        self.assertEqual(style["font_name"], "Helvetica Neue")
        self.assertEqual(style["font_color"], "&H00F8F1E8")
        self.assertEqual(style["alignment"], 1)
        self.assertEqual(style["max_line_chars"], 22)
        self.assertIn("2010s aviation/news", style["period_reference"])

    def test_load_music_track_context_verifies_registered_hashes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-music-registry-") as temp_dir:
            root = Path(temp_dir)
            builder = self.make_builder(root / "models")
            loop_path = root / "loop.wav"
            outro_path = root / "outro.m4a"
            loop_path.write_bytes(b"loop")
            outro_path.write_bytes(b"outro")
            loop_sha256 = file_sha256(loop_path)
            outro_sha256 = file_sha256(outro_path)
            registry_path = root / "music_track_registry.json"
            registry_path.write_text(
                json.dumps(
                    {
                        "default_active_shorts_music_track_id": "paper_architecture_theme_v1",
                        "tracks": {
                            "paper_architecture_theme_v1": {
                                "name": "Paper Architecture",
                                "body_loop": {
                                    "path": str(loop_path),
                                    "sha256": loop_sha256,
                                    "default_volume_linear": 0.2,
                                },
                                "outro": {
                                    "path": str(outro_path),
                                    "sha256": outro_sha256,
                                    "default_initial_volume_linear": 0.1,
                                },
                                "mix_profile": {},
                            }
                        },
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            context = builder.load_music_track_context(
                music_policy="canonical_default",
                music_track_registry=registry_path,
                music_track_id="paper_architecture_theme_v1",
                music_waiver_reason="",
                music_rights_check_status="pending_youtube_upload_check",
            )
        self.assertTrue(context["motif_outro_mix_used"])
        self.assertEqual(context["music_track_id"], "paper_architecture_theme_v1")
        self.assertEqual(context["body_loop_sha256"], loop_sha256)
        self.assertEqual(context["outro_sha256"], outro_sha256)

    def test_motif_outro_mix_timing_extends_hold_to_complete_outro(self) -> None:
        timing = compute_motif_outro_mix_timing(
            source_duration=58.746009,
            motif_start=55.524,
            motif_end=58.746,
            outro_asset_duration=6.971542,
            mix_profile={
                "final_frame_hold_seconds_min": 0.5,
                "final_frame_hold_seconds_max": 0.75,
                "outro_pre_motif_lead_seconds": 0.25,
                "outro_completion_policy": "extend_final_to_complete_outro",
                "max_extended_final_frame_hold_seconds": 4.0,
            },
        )
        self.assertEqual(timing["outro_completion_read"], "pass")
        self.assertAlmostEqual(timing["outro_start_seconds"], 55.274, places=3)
        self.assertAlmostEqual(timing["outro_duration_used_seconds"], 6.971542, places=5)
        self.assertAlmostEqual(timing["outro_cutoff_seconds"], 0.0, places=3)
        self.assertAlmostEqual(timing["final_frame_hold_seconds"], 3.499533, places=3)

    def test_waived_music_policy_requires_reason(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-music-waiver-") as temp_dir:
            root = Path(temp_dir)
            builder = self.make_builder(root / "models")
            registry_path = root / "music_track_registry.json"
            registry_path.write_text(json.dumps({"tracks": {}}, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(Exception, "music-waiver-reason"):
                builder.load_music_track_context(
                    music_policy="waived",
                    music_track_registry=registry_path,
                    music_track_id="",
                    music_waiver_reason="",
                    music_rights_check_status="not_applicable",
                )

    def test_find_motif_caption_span_matches_closing_motif(self) -> None:
        span = find_motif_caption_span(
            [
                {"segment_id": "caption_001", "start_seconds": 0.0, "end_seconds": 2.0, "text": "The bridge moved."},
                {
                    "segment_id": "caption_002",
                    "start_seconds": 55.0,
                    "end_seconds": 58.7,
                    "text": "Small causes, massive consequences.",
                },
            ],
            {"motif_text": "Small causes, massive consequences."},
        )
        self.assertEqual(span["segment_id"], "caption_002")
        self.assertEqual(span["source"], "caption_exact_match")

    def test_fallback_caption_segments_use_proof_beats(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-caption-fallback-") as temp_dir:
            transcript_path = Path(temp_dir) / "transcript.txt"
            transcript_path.write_text(
                "The first phrase lands here. The second phrase explains the mechanism. "
                "The third phrase closes the short.",
                encoding="utf-8",
            )
            proof_manifest = {
                "beats": [
                    {"cue_start_seconds": 0.0, "cue_end_seconds": 2.0},
                    {"cue_start_seconds": 2.0, "cue_end_seconds": 6.0},
                ]
            }
            segments = fallback_caption_segments_from_transcript(
                transcript_path,
                proof_manifest,
                proof_duration_seconds=6.0,
            )
        self.assertGreaterEqual(len(segments), 3)
        self.assertEqual(segments[0]["start_seconds"], 0.0)
        self.assertLessEqual(segments[-1]["end_seconds"], 6.0)
        self.assertIn("mechanism", " ".join(segment["text"] for segment in segments))

    def test_final_export_writes_caption_manifests_and_final_paths(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-final-export-") as temp_dir:
            builder, proof_manifest_path, review_note_path, _transcript_path = self.make_final_export_fixture(
                Path(temp_dir)
            )

            def fake_apply_caption_overlay(
                proof_path: Path,
                *,
                caption_ass_path: Path,
                output_path: Path,
            ) -> Path:
                self.assertTrue(proof_path.exists())
                self.assertTrue(caption_ass_path.exists())
                output_path.write_text("captioned final", encoding="utf-8")
                return output_path.resolve()

            builder.apply_caption_overlay = mock.Mock(side_effect=fake_apply_caption_overlay)  # type: ignore[method-assign]
            with mock.patch("short_tool.ffprobe_dimensions", autospec=True, return_value=(1080, 1920)), mock.patch(
                "short_tool.ffprobe_duration",
                autospec=True,
                return_value=4.0,
            ):
                final_manifest_path = builder.final_export_existing_build(
                    proof_manifest_path,
                    proof_review_note=review_note_path,
                    proof_disposition="keep",
                    reel_class="keeper-short",
                    all_motion_clips_keep=True,
                    no_diagnostic_placeholders=True,
                    caption_style="documentary_lower_third_v1",
                    caption_placement="lower-left",
                    output_tag="keeper_v1",
                    music_policy="waived",
                    music_waiver_reason="unit fixture uses caption-only fake media",
                    music_rights_check_status="not_applicable",
                    house_crt_static_waiver_reason="unit fixture does not render the final-gate motion rebuild",
                )

            final_manifest = json.loads(final_manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(final_manifest["stage"], "video final")
            self.assertEqual(final_manifest["caption_style_preset"], "documentary_lower_third_v1")
            self.assertEqual(final_manifest["caption_placement"], "lower-left")
            self.assertEqual(final_manifest["expected_voice_profile_id"], "youtube_shorts_mike_challenger_match_v1")
            self.assertEqual(final_manifest["audio_disposition"], "keep")
            self.assertEqual(final_manifest["music_policy"], "waived")
            self.assertFalse(final_manifest["motif_outro_mix_used"])
            self.assertEqual(final_manifest["motif_music_bed_read"], "waived")
            self.assertEqual(final_manifest["house_crt_static_status"], "waived")
            self.assertEqual(
                final_manifest["house_crt_static_waiver_reason"],
                "unit fixture does not render the final-gate motion rebuild",
            )
            self.assertTrue(Path(final_manifest["short_audio_package_path"]).exists())
            self.assertEqual(final_manifest["audio_provenance"]["model"], "eleven_multilingual_v2")
            self.assertTrue(Path(final_manifest["caption_timing_path"]).exists())
            self.assertTrue(Path(final_manifest["caption_srt_path"]).exists())
            self.assertTrue(Path(final_manifest["caption_ass_path"]).exists())
            self.assertTrue(Path(final_manifest["caption_overlay_manifest_path"]).exists())
            self.assertTrue(Path(final_manifest["captioned_final_path"]).exists())
            self.assertEqual(final_manifest["gate_assertions"]["proof_disposition"], "keep")
            overlay_manifest = json.loads(Path(final_manifest["caption_overlay_manifest_path"]).read_text(encoding="utf-8"))
            self.assertEqual(overlay_manifest["style_defaults"]["placement"], "mobile-safe lower-left third")

    def test_final_export_uses_validated_house_crt_static_motion_bed_before_captions(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-final-house-crt-static-") as temp_dir:
            root = Path(temp_dir)
            builder, proof_manifest_path, review_note_path, _transcript_path = self.make_final_export_fixture(root)
            motion_bed_path = root / "house_crt_static_no_audio.mp4"
            motion_bed_path.write_text("motion bed", encoding="utf-8")
            house_manifest_path = root / "house_crt_static_manifest.json"
            house_manifest_path.write_text(
                json.dumps(
                    {
                        "source_proof_manifest_path": str(proof_manifest_path),
                        "house_crt_contract_id": HOUSE_CRT_FINAL_CONTRACT_ID,
                        "house_crt_contract_read": {
                            "house_crt_contract_id": HOUSE_CRT_FINAL_CONTRACT_ID,
                        },
                        "house_crt_texture_read": {
                            "house_crt_contract_id": HOUSE_CRT_FINAL_CONTRACT_ID,
                            "profile_id": HOUSE_CRT_FINAL_PROFILE_ID,
                            "intensity": HOUSE_CRT_FINAL_INTENSITY,
                            "texture_tone_policy": HOUSE_CRT_FINAL_TONE_POLICY,
                            "calibration_recipe_id": HOUSE_CRT_FINAL_LEGACY_CALIBRATION_RECIPE_ID,
                            "legacy_calibration_recipe_id": HOUSE_CRT_FINAL_LEGACY_CALIBRATION_RECIPE_ID,
                            "texture_renderer_source": HOUSE_CRT_FINAL_TEXTURE_RENDERER_SOURCE,
                            "scanline_policy_id": HOUSE_CRT_FINAL_SCANLINE_POLICY_ID,
                            "scanline_strength_variant_id": HOUSE_CRT_FINAL_SCANLINE_STRENGTH_VARIANT_ID,
                            "scanline_delta_y": HOUSE_CRT_FINAL_SCANLINE_DELTA_Y,
                            "scanline_period_pixels": HOUSE_CRT_FINAL_SCANLINE_PERIOD_PIXELS,
                            "scanline_band_pixels": HOUSE_CRT_FINAL_SCANLINE_BAND_PIXELS,
                        },
                        "luma_chroma_metrics_read": {
                            "overall_read": "pass",
                            "max_abs_luma_yavg_delta": 1.4,
                        },
                        "source_lineage_read": {
                            "clean_source_confirmed": True,
                            "selected_source_mode": "single_clean_no_caption_visual_source",
                            "selected_source_rejections": [],
                            "selected_segment_source_paths": ["/tmp/source_clean.mp4"],
                        },
                        "randomized_static_transition_read": {
                            "read": "superseded_label_use_signal_interruption_read",
                        },
                        "visual_layer_order_read": {
                            "visual_layer_sequence": [
                                "approved_no_caption_motion_or_proof_source",
                                "historical_signal_conservative_clean_normalization",
                                "luma_neutral_house_crt_texture",
                                "challenger_style_signal_interruption_at_eligible_outgoing_cut_tails",
                                "final_duration_tail_visual_handling",
                                "caption_burn_last_visual_layer",
                                "audio_mux_stream_only_after_caption_burn",
                            ],
                            "motion_source_contains_captions": False,
                            "texture_applied_before_captions": True,
                            "signal_interruption_applied_before_captions": True,
                            "caption_burn_is_last_visual_operation": True,
                            "post_caption_visual_effects_applied": False,
                        },
                        "signal_interruption_read": {
                            "house_crt_contract_id": HOUSE_CRT_FINAL_CONTRACT_ID,
                            "profile_id": HOUSE_CRT_STATIC_PROFILE_ID,
                            "duration_seconds": HOUSE_CRT_STATIC_DURATION_SECONDS,
                            "timing_policy": "replace_outgoing_segment_tail_preserve_total_duration",
                            "render_policy": "mutate_outgoing_footage_tail_no_full_frame_static_cards",
                            "full_frame_static_replacement_used": False,
                            "eligible_cut_count": 2,
                            "applied_cut_count": 2,
                        },
                        "outputs": {
                            "motion_full_duration_no_audio_path": str(motion_bed_path),
                        },
                    }
                ),
                encoding="utf-8",
            )

            def fake_apply_caption_overlay(
                proof_path: Path,
                *,
                caption_ass_path: Path,
                output_path: Path,
            ) -> Path:
                self.assertEqual(proof_path, motion_bed_path.resolve())
                self.assertTrue(caption_ass_path.exists())
                output_path.write_text("captioned final", encoding="utf-8")
                return output_path.resolve()

            builder.apply_caption_overlay = mock.Mock(side_effect=fake_apply_caption_overlay)  # type: ignore[method-assign]
            with mock.patch("short_tool.ffprobe_video_info", autospec=True) as probe_info, mock.patch(
                "short_tool.ffprobe_dimensions",
                autospec=True,
                return_value=(1080, 1920),
            ), mock.patch(
                "short_tool.ffprobe_duration",
                autospec=True,
                return_value=4.0,
            ):
                probe_info.return_value = {
                    "width": 1080,
                    "height": 1920,
                    "duration_seconds": 4.0,
                    "fps": 30.0,
                    "audio_stream_count": 0,
                }
                final_manifest_path = builder.final_export_existing_build(
                    proof_manifest_path,
                    proof_review_note=review_note_path,
                    proof_disposition="keep",
                    reel_class="keeper-short",
                    all_motion_clips_keep=True,
                    no_diagnostic_placeholders=True,
                    caption_style="documentary_lower_third_v1",
                    output_tag="keeper_house_crt",
                    music_policy="waived",
                    music_waiver_reason="unit fixture uses caption-only fake media",
                    music_rights_check_status="not_applicable",
                    house_crt_static_manifest=house_manifest_path,
                )

            final_manifest = json.loads(final_manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(final_manifest["final_picture_source_path"], str(motion_bed_path.resolve()))
            self.assertEqual(final_manifest["house_crt_static_status"], "applied")
            self.assertEqual(
                final_manifest["house_crt_static_context"]["house_crt_contract_id"],
                HOUSE_CRT_FINAL_CONTRACT_ID,
            )
            self.assertEqual(
                final_manifest["house_crt_static_context"]["scanline_strength_variant_id"],
                HOUSE_CRT_FINAL_SCANLINE_STRENGTH_VARIANT_ID,
            )
            self.assertEqual(
                final_manifest["house_crt_static_context"]["scanline_delta_y"],
                HOUSE_CRT_FINAL_SCANLINE_DELTA_Y,
            )
            self.assertEqual(
                final_manifest["house_crt_static_context"]["caption_layer_order_read"],
                "captions_applied_after_house_crt_signal_interruption_motion_rebuild",
            )
            self.assertTrue(
                final_manifest["house_crt_static_context"]["visual_layer_order_read"][
                    "caption_burn_is_last_visual_operation"
                ]
            )
            self.assertTrue(final_manifest["gate_assertions"]["house_crt_static_final_gate_checked"])

    def test_final_export_rejects_old_luma_neutral_only_house_crt_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-final-old-house-crt-reject-") as temp_dir:
            root = Path(temp_dir)
            builder, proof_manifest_path, _review_note_path, _transcript_path = self.make_final_export_fixture(root)
            motion_bed_path = root / "house_crt_static_no_audio.mp4"
            motion_bed_path.write_text("motion bed", encoding="utf-8")
            payload = self.house_crt_final_gate_payload(proof_manifest_path, motion_bed_path)
            house_read = payload["house_crt_texture_read"]
            assert isinstance(house_read, dict)
            house_read["texture_tone_policy"] = "luma_neutral_chroma_v1"
            house_read["calibration_recipe_id"] = "premium_broadcast_crt_luma_neutral_chroma_v1"
            house_read["legacy_calibration_recipe_id"] = "premium_broadcast_crt_luma_neutral_chroma_v1"
            house_read["texture_renderer_source"] = "house_crt_static_final_pass.luma_neutral_chroma_filter_graph"
            manifest_path = root / "old_luma_neutral_manifest.json"
            manifest_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(Exception, "texture_tone_policy must be"):
                builder.final_export_house_crt_static_context(proof_manifest_path, manifest_path)

    def test_final_export_rejects_missing_selected_scanline_fields(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-final-missing-scanline-reject-") as temp_dir:
            root = Path(temp_dir)
            builder, proof_manifest_path, _review_note_path, _transcript_path = self.make_final_export_fixture(root)
            motion_bed_path = root / "house_crt_static_no_audio.mp4"
            motion_bed_path.write_text("motion bed", encoding="utf-8")
            payload = self.house_crt_final_gate_payload(proof_manifest_path, motion_bed_path)
            house_read = payload["house_crt_texture_read"]
            assert isinstance(house_read, dict)
            for key in (
                "scanline_policy_id",
                "scanline_strength_variant_id",
                "scanline_delta_y",
                "scanline_period_pixels",
                "scanline_band_pixels",
            ):
                house_read.pop(key)
            manifest_path = root / "missing_scanline_manifest.json"
            manifest_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(Exception, "scanline_policy_id must be"):
                builder.final_export_house_crt_static_context(proof_manifest_path, manifest_path)

    def test_final_export_rejects_calibration_only_visible_scanline_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-final-calibration-only-reject-") as temp_dir:
            root = Path(temp_dir)
            builder, proof_manifest_path, _review_note_path, _transcript_path = self.make_final_export_fixture(root)
            motion_bed_path = root / "house_crt_static_no_audio.mp4"
            motion_bed_path.write_text("motion bed", encoding="utf-8")
            payload = self.house_crt_final_gate_payload(proof_manifest_path, motion_bed_path)
            payload["pass_id"] = "house_crt_visible_scanline_high_visibility_ladder_pass_07c"
            payload["calibration_only"] = True
            manifest_path = root / "calibration_only_manifest.json"
            manifest_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(Exception, "calibration-only house CRT manifests cannot be used"):
                builder.final_export_house_crt_static_context(proof_manifest_path, manifest_path)

    def test_final_export_rejects_missing_clean_source_lineage_read(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-final-house-crt-lineage-reject-") as temp_dir:
            root = Path(temp_dir)
            builder, proof_manifest_path, _review_note_path, _transcript_path = self.make_final_export_fixture(root)
            motion_bed_path = root / "house_crt_static_no_audio.mp4"
            motion_bed_path.write_text("motion bed", encoding="utf-8")
            manifest_path = root / "missing_lineage_manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "source_proof_manifest_path": str(proof_manifest_path),
                        "house_crt_contract_id": HOUSE_CRT_FINAL_CONTRACT_ID,
                        "house_crt_texture_read": {
                            "house_crt_contract_id": HOUSE_CRT_FINAL_CONTRACT_ID,
                            "profile_id": HOUSE_CRT_FINAL_PROFILE_ID,
                            "intensity": HOUSE_CRT_FINAL_INTENSITY,
                            "texture_tone_policy": HOUSE_CRT_FINAL_TONE_POLICY,
                            "calibration_recipe_id": HOUSE_CRT_FINAL_LEGACY_CALIBRATION_RECIPE_ID,
                            "legacy_calibration_recipe_id": HOUSE_CRT_FINAL_LEGACY_CALIBRATION_RECIPE_ID,
                            "texture_renderer_source": HOUSE_CRT_FINAL_TEXTURE_RENDERER_SOURCE,
                            "scanline_policy_id": HOUSE_CRT_FINAL_SCANLINE_POLICY_ID,
                            "scanline_strength_variant_id": HOUSE_CRT_FINAL_SCANLINE_STRENGTH_VARIANT_ID,
                            "scanline_delta_y": HOUSE_CRT_FINAL_SCANLINE_DELTA_Y,
                            "scanline_period_pixels": HOUSE_CRT_FINAL_SCANLINE_PERIOD_PIXELS,
                            "scanline_band_pixels": HOUSE_CRT_FINAL_SCANLINE_BAND_PIXELS,
                        },
                        "luma_chroma_metrics_read": {"overall_read": "pass"},
                        "visual_layer_order_read": {
                            "visual_layer_sequence": [
                                "approved_no_caption_motion_or_proof_source",
                                "caption_burn_last_visual_layer",
                            ],
                            "motion_source_contains_captions": False,
                            "texture_applied_before_captions": True,
                            "signal_interruption_applied_before_captions": True,
                            "caption_burn_is_last_visual_operation": True,
                            "post_caption_visual_effects_applied": False,
                        },
                        "signal_interruption_read": {
                            "profile_id": HOUSE_CRT_STATIC_PROFILE_ID,
                            "duration_seconds": HOUSE_CRT_STATIC_DURATION_SECONDS,
                            "timing_policy": "replace_outgoing_segment_tail_preserve_total_duration",
                            "full_frame_static_replacement_used": False,
                            "eligible_cut_count": 1,
                            "applied_cut_count": 1,
                        },
                        "outputs": {"motion_full_duration_no_audio_path": str(motion_bed_path)},
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(Exception, "source_lineage_read object is required"):
                builder.final_export_house_crt_static_context(proof_manifest_path, manifest_path)

    def test_final_export_rejects_generic_full_frame_static_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-final-house-crt-static-reject-") as temp_dir:
            root = Path(temp_dir)
            builder, proof_manifest_path, _review_note_path, _transcript_path = self.make_final_export_fixture(root)
            motion_bed_path = root / "house_crt_static_no_audio.mp4"
            motion_bed_path.write_text("motion bed", encoding="utf-8")
            legacy_manifest_path = root / "legacy_house_crt_static_manifest.json"
            legacy_manifest_path.write_text(
                json.dumps(
                    {
                        "source_proof_manifest_path": str(proof_manifest_path),
                        "house_crt_contract_id": HOUSE_CRT_FINAL_CONTRACT_ID,
                        "house_crt_texture_read": {
                            "house_crt_contract_id": HOUSE_CRT_FINAL_CONTRACT_ID,
                            "profile_id": HOUSE_CRT_FINAL_PROFILE_ID,
                            "intensity": HOUSE_CRT_FINAL_INTENSITY,
                            "texture_tone_policy": HOUSE_CRT_FINAL_TONE_POLICY,
                            "calibration_recipe_id": HOUSE_CRT_FINAL_LEGACY_CALIBRATION_RECIPE_ID,
                            "legacy_calibration_recipe_id": HOUSE_CRT_FINAL_LEGACY_CALIBRATION_RECIPE_ID,
                            "texture_renderer_source": HOUSE_CRT_FINAL_TEXTURE_RENDERER_SOURCE,
                            "scanline_policy_id": HOUSE_CRT_FINAL_SCANLINE_POLICY_ID,
                            "scanline_strength_variant_id": HOUSE_CRT_FINAL_SCANLINE_STRENGTH_VARIANT_ID,
                            "scanline_delta_y": HOUSE_CRT_FINAL_SCANLINE_DELTA_Y,
                            "scanline_period_pixels": HOUSE_CRT_FINAL_SCANLINE_PERIOD_PIXELS,
                            "scanline_band_pixels": HOUSE_CRT_FINAL_SCANLINE_BAND_PIXELS,
                        },
                        "luma_chroma_metrics_read": {
                            "overall_read": "pass",
                        },
                        "source_lineage_read": {
                            "clean_source_confirmed": True,
                            "selected_source_mode": "single_clean_no_caption_visual_source",
                            "selected_source_rejections": [],
                            "selected_segment_source_paths": ["/tmp/source_clean.mp4"],
                        },
                        "visual_layer_order_read": {
                            "visual_layer_sequence": [
                                "approved_no_caption_motion_or_proof_source",
                                "caption_burn_last_visual_layer",
                            ],
                            "motion_source_contains_captions": False,
                            "texture_applied_before_captions": True,
                            "signal_interruption_applied_before_captions": True,
                            "caption_burn_is_last_visual_operation": True,
                            "post_caption_visual_effects_applied": False,
                        },
                        "randomized_static_transition_read": {
                            "profile_id": HOUSE_CRT_STATIC_PROFILE_ID,
                            "duration_seconds": HOUSE_CRT_STATIC_DURATION_SECONDS,
                            "timing_policy": "replace_outgoing_segment_tail_preserve_total_duration",
                            "full_frame_static_replacement_used": True,
                            "eligible_cut_count": 1,
                            "applied_cut_count": 1,
                        },
                        "outputs": {
                            "motion_full_duration_no_audio_path": str(motion_bed_path),
                        },
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(Exception, "signal_interruption_read object is required"):
                builder.final_export_house_crt_static_context(
                    proof_manifest_path,
                    legacy_manifest_path,
                )

    def test_final_export_rejects_missing_house_crt_contract_id(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-final-house-crt-contract-reject-") as temp_dir:
            root = Path(temp_dir)
            builder, proof_manifest_path, _review_note_path, _transcript_path = self.make_final_export_fixture(root)
            manifest_path = root / "missing_contract_manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "source_proof_manifest_path": str(proof_manifest_path),
                        "house_crt_texture_read": {
                            "profile_id": HOUSE_CRT_FINAL_PROFILE_ID,
                            "intensity": HOUSE_CRT_FINAL_INTENSITY,
                        },
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(Exception, "house_crt_contract_id must be"):
                builder.final_export_house_crt_static_context(proof_manifest_path, manifest_path)

    def test_final_export_rejects_caption_not_last_visual_layer(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-final-caption-last-reject-") as temp_dir:
            root = Path(temp_dir)
            builder, proof_manifest_path, _review_note_path, _transcript_path = self.make_final_export_fixture(root)
            motion_bed_path = root / "house_crt_static_no_audio.mp4"
            motion_bed_path.write_text("motion bed", encoding="utf-8")
            manifest_path = root / "bad_layer_order_manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "source_proof_manifest_path": str(proof_manifest_path),
                        "house_crt_contract_id": HOUSE_CRT_FINAL_CONTRACT_ID,
                        "house_crt_texture_read": {
                            "house_crt_contract_id": HOUSE_CRT_FINAL_CONTRACT_ID,
                            "profile_id": HOUSE_CRT_FINAL_PROFILE_ID,
                            "intensity": HOUSE_CRT_FINAL_INTENSITY,
                            "texture_tone_policy": HOUSE_CRT_FINAL_TONE_POLICY,
                            "calibration_recipe_id": HOUSE_CRT_FINAL_LEGACY_CALIBRATION_RECIPE_ID,
                            "legacy_calibration_recipe_id": HOUSE_CRT_FINAL_LEGACY_CALIBRATION_RECIPE_ID,
                            "texture_renderer_source": HOUSE_CRT_FINAL_TEXTURE_RENDERER_SOURCE,
                            "scanline_policy_id": HOUSE_CRT_FINAL_SCANLINE_POLICY_ID,
                            "scanline_strength_variant_id": HOUSE_CRT_FINAL_SCANLINE_STRENGTH_VARIANT_ID,
                            "scanline_delta_y": HOUSE_CRT_FINAL_SCANLINE_DELTA_Y,
                            "scanline_period_pixels": HOUSE_CRT_FINAL_SCANLINE_PERIOD_PIXELS,
                            "scanline_band_pixels": HOUSE_CRT_FINAL_SCANLINE_BAND_PIXELS,
                        },
                        "luma_chroma_metrics_read": {"overall_read": "pass"},
                        "source_lineage_read": {
                            "clean_source_confirmed": True,
                            "selected_source_mode": "single_clean_no_caption_visual_source",
                            "selected_source_rejections": [],
                            "selected_segment_source_paths": ["/tmp/source_clean.mp4"],
                        },
                        "visual_layer_order_read": {
                            "visual_layer_sequence": [
                                "approved_no_caption_motion_or_proof_source",
                                "caption_burn_last_visual_layer",
                                "luma_neutral_house_crt_texture",
                            ],
                            "motion_source_contains_captions": False,
                            "texture_applied_before_captions": False,
                            "signal_interruption_applied_before_captions": True,
                            "caption_burn_is_last_visual_operation": False,
                            "post_caption_visual_effects_applied": True,
                        },
                        "signal_interruption_read": {
                            "profile_id": HOUSE_CRT_STATIC_PROFILE_ID,
                            "duration_seconds": HOUSE_CRT_STATIC_DURATION_SECONDS,
                            "timing_policy": "replace_outgoing_segment_tail_preserve_total_duration",
                            "full_frame_static_replacement_used": False,
                        },
                        "outputs": {"motion_full_duration_no_audio_path": str(motion_bed_path)},
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(Exception, "captions must be the last visual operation"):
                builder.final_export_house_crt_static_context(proof_manifest_path, manifest_path)

    def test_final_export_rejects_old_era_specific_texture_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-final-era-texture-reject-") as temp_dir:
            root = Path(temp_dir)
            builder, proof_manifest_path, _review_note_path, _transcript_path = self.make_final_export_fixture(root)
            manifest_path = root / "old_era_texture_manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "source_proof_manifest_path": str(proof_manifest_path),
                        "house_crt_contract_id": HOUSE_CRT_FINAL_CONTRACT_ID,
                        "house_crt_texture_read": {
                            "house_crt_contract_id": HOUSE_CRT_FINAL_CONTRACT_ID,
                            "profile_id": "era_1940s_archival_film_v1",
                            "intensity": HOUSE_CRT_FINAL_INTENSITY,
                            "texture_tone_policy": HOUSE_CRT_FINAL_TONE_POLICY,
                            "calibration_recipe_id": HOUSE_CRT_FINAL_LEGACY_CALIBRATION_RECIPE_ID,
                            "legacy_calibration_recipe_id": HOUSE_CRT_FINAL_LEGACY_CALIBRATION_RECIPE_ID,
                            "texture_renderer_source": HOUSE_CRT_FINAL_TEXTURE_RENDERER_SOURCE,
                            "scanline_policy_id": HOUSE_CRT_FINAL_SCANLINE_POLICY_ID,
                            "scanline_strength_variant_id": HOUSE_CRT_FINAL_SCANLINE_STRENGTH_VARIANT_ID,
                            "scanline_delta_y": HOUSE_CRT_FINAL_SCANLINE_DELTA_Y,
                            "scanline_period_pixels": HOUSE_CRT_FINAL_SCANLINE_PERIOD_PIXELS,
                            "scanline_band_pixels": HOUSE_CRT_FINAL_SCANLINE_BAND_PIXELS,
                        },
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(Exception, "house CRT profile must be"):
                builder.final_export_house_crt_static_context(proof_manifest_path, manifest_path)

    def test_final_export_rejects_failed_gate_inputs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-final-export-reject-") as temp_dir:
            builder, proof_manifest_path, review_note_path, _transcript_path = self.make_final_export_fixture(
                Path(temp_dir)
            )
            with self.assertRaisesRegex(Exception, "requires --proof-disposition keep"):
                builder.final_export_existing_build(
                    proof_manifest_path,
                    proof_review_note=review_note_path,
                    proof_disposition="tighten",
                    reel_class="keeper-short",
                    all_motion_clips_keep=True,
                    no_diagnostic_placeholders=True,
                )
            with self.assertRaisesRegex(Exception, "requires --reel-class keeper-short"):
                builder.final_export_existing_build(
                    proof_manifest_path,
                    proof_review_note=review_note_path,
                    proof_disposition="keep",
                    reel_class="mixed-review-short",
                    all_motion_clips_keep=True,
                    no_diagnostic_placeholders=True,
                )
            with self.assertRaisesRegex(Exception, "requires --all-motion-clips-keep"):
                builder.final_export_existing_build(
                    proof_manifest_path,
                    proof_review_note=review_note_path,
                    proof_disposition="keep",
                    reel_class="keeper-short",
                    all_motion_clips_keep=False,
                    no_diagnostic_placeholders=True,
                )
            with self.assertRaisesRegex(Exception, "requires --house-crt-static-manifest"):
                builder.final_export_existing_build(
                    proof_manifest_path,
                    proof_review_note=review_note_path,
                    proof_disposition="keep",
                    reel_class="keeper-short",
                    all_motion_clips_keep=True,
                    no_diagnostic_placeholders=True,
                )
            review_note_path.unlink()
            with self.assertRaisesRegex(Exception, "--proof-review-note"):
                builder.final_export_existing_build(
                    proof_manifest_path,
                    proof_review_note=review_note_path,
                    proof_disposition="keep",
                    reel_class="keeper-short",
                    all_motion_clips_keep=True,
                    no_diagnostic_placeholders=True,
                    house_crt_static_waiver_reason="unit fixture bypasses final-gate motion rebuild",
                )

    def test_audio_provenance_rejects_same_voice_wrong_model(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-audio-provenance-wrong-model-") as temp_dir:
            builder, proof_manifest_path, _review_note_path, _transcript_path = self.make_final_export_fixture(
                Path(temp_dir)
            )
            payload = json.loads(proof_manifest_path.read_text(encoding="utf-8"))
            package_path = Path(payload["short_audio_package_path"])
            package_payload = json.loads(package_path.read_text(encoding="utf-8"))
            package_payload["model"] = "eleven_v3"
            package_path.write_text(json.dumps(package_payload, indent=2) + "\n", encoding="utf-8")
            payload["audio_package_sha256"] = file_sha256(package_path)
            proof_manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(Exception, "model .* does not match profile"):
                builder.validate_audio_provenance(
                    proof_manifest_path,
                    payload,
                    require_final_export_eligible=True,
                )

    def test_final_export_rejects_missing_audio_provenance(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-final-export-missing-provenance-") as temp_dir:
            builder, proof_manifest_path, review_note_path, _transcript_path = self.make_final_export_fixture(
                Path(temp_dir)
            )
            payload = json.loads(proof_manifest_path.read_text(encoding="utf-8"))
            payload.pop("short_audio_package_path")
            proof_manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(Exception, "short_audio_package_path"):
                builder.final_export_existing_build(
                    proof_manifest_path,
                    proof_review_note=review_note_path,
                    proof_disposition="keep",
                    reel_class="keeper-short",
                    all_motion_clips_keep=True,
                    no_diagnostic_placeholders=True,
                    house_crt_static_waiver_reason="unit fixture bypasses final-gate motion rebuild",
                )

    def test_final_export_rejects_non_portrait_proof(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-final-export-landscape-") as temp_dir:
            builder, proof_manifest_path, review_note_path, _transcript_path = self.make_final_export_fixture(
                Path(temp_dir)
            )
            with mock.patch("short_tool.ffprobe_dimensions", autospec=True, return_value=(1920, 1080)):
                with self.assertRaisesRegex(Exception, "portrait 9:16"):
                    builder.final_export_existing_build(
                        proof_manifest_path,
                        proof_review_note=review_note_path,
                        proof_disposition="keep",
                        reel_class="keeper-short",
                        all_motion_clips_keep=True,
                        no_diagnostic_placeholders=True,
                        music_policy="waived",
                        music_waiver_reason="unit fixture uses fake media",
                        house_crt_static_waiver_reason="unit fixture bypasses final-gate motion rebuild",
                    )

    def test_apply_caption_overlay_uses_ass_subtitles_filter(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-caption-overlay-") as temp_dir:
            builder = self.make_builder(Path(temp_dir) / "models")
            proof_path = Path(temp_dir) / "proof.mp4"
            ass_path = Path(temp_dir) / "captions.ass"
            output_path = Path(temp_dir) / "final.mp4"
            proof_path.write_text("proof", encoding="utf-8")
            ass_path.write_text("[Script Info]\n", encoding="utf-8")
            commands: list[list[str]] = []

            def fake_run(command: list[str], *, label: str) -> subprocess.CompletedProcess[str]:
                del label
                commands.append(command)
                output_path.write_text("final", encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, "", "")

            builder.run_command = mock.Mock(side_effect=fake_run)  # type: ignore[method-assign]
            with mock.patch("short_tool.ffprobe_dimensions", autospec=True, return_value=(1080, 1920)):
                result = builder.apply_caption_overlay(
                    proof_path,
                    caption_ass_path=ass_path,
                    output_path=output_path,
                )
            self.assertEqual(result, output_path.resolve())
            filter_arg = commands[0][commands[0].index("-vf") + 1]
            self.assertIn("subtitles=filename=", filter_arg)
            self.assertIn(str(ass_path), filter_arg)

    def test_validate_short_manifest_resolves_packaging_frame_and_frames(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-short-models-") as models_root:
            builder = self.make_builder(Path(models_root))
            manifest_path = ROOT / "references/episodes/challenger/shorts/challenger_short_minimal_surreal_v1.json"
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.make_short_manifest_audio_self_contained(builder, payload, Path(models_root))
            payload = builder.validate_short_manifest(
                manifest_path,
                payload,
            )
        self.assertEqual(payload["packaging_frame_id"], "shorts_cover_plate/challenger_thesis_cover")
        self.assertEqual(payload["beats"][0]["preset_id"], "shorts_scene_plate/challenger_warning_cold")
        self.assertEqual(payload["beats"][0]["frames"], 223)
        self.assertEqual(len(payload["beats"]), 7)

    def test_validate_short_manifest_resolves_packaging_frame_still_override_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-short-models-") as models_root, tempfile.TemporaryDirectory(
            prefix="ce-short-packaging-override-"
        ) as temp_dir:
            builder = self.make_builder(Path(models_root))
            temp_root = Path(temp_dir)
            manifest_path = ROOT / "references/episodes/challenger/shorts/challenger_short_minimal_surreal_v1.json"
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.make_short_manifest_audio_self_contained(builder, payload, temp_root)
            packaging_override = temp_root / "cover.png"
            Image.new("RGB", (90, 160), color=(0, 0, 0)).save(packaging_override)
            payload["packaging_frame_still_override_path"] = str(packaging_override)

            validated = builder.validate_short_manifest(Path("/tmp/challenger_short_minimal_surreal_v1.json"), payload)

            self.assertEqual(validated["packaging_frame_still_override_path"], packaging_override.resolve())

    def test_validate_short_manifest_rejects_negative_cue_start(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-short-models-") as models_root:
            builder = self.make_builder(Path(models_root))
            manifest_path = ROOT / "references/episodes/challenger/shorts/challenger_short_minimal_surreal_v1.json"
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.make_short_manifest_audio_self_contained(builder, payload, Path(models_root))
            payload["short_id"] = "challenger_short_minimal_surreal_v1"
            payload["beats"][1]["cue_start_seconds"] = -1.0
            with self.assertRaisesRegex(Exception, "cue_start_seconds must be >= 0"):
                builder.validate_short_manifest(Path("/tmp/challenger_short_minimal_surreal_v1.json"), payload)

    def test_validate_short_manifest_resolves_beat_override_paths(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-short-models-") as models_root, tempfile.TemporaryDirectory(
            prefix="ce-short-overrides-"
        ) as temp_dir:
            builder = self.make_builder(Path(models_root))
            temp_root = Path(temp_dir)
            manifest_path = ROOT / "references/episodes/challenger/shorts/challenger_short_minimal_surreal_v1.json"
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.make_short_manifest_audio_self_contained(builder, payload, temp_root)
            for beat in payload["beats"]:
                beat.pop("still_override_path", None)
                beat.pop("raw_clip_override_path", None)
            still_override = temp_root / "still.png"
            raw_override = temp_root / "clip.mp4"
            Image.new("RGB", (90, 160), color=(0, 0, 0)).save(still_override)
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "color=c=black:s=90x160:d=1",
                    "-pix_fmt",
                    "yuv420p",
                    str(raw_override),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload["beats"][0]["still_override_path"] = str(still_override)
            payload["beats"][1]["raw_clip_override_path"] = str(raw_override)

            validated = builder.validate_short_manifest(Path("/tmp/challenger_short_minimal_surreal_v1.json"), payload)

            self.assertEqual(validated["beats"][0]["still_override_path"], still_override.resolve())
            self.assertIsNone(validated["beats"][0]["raw_clip_override_path"])
            self.assertEqual(validated["beats"][1]["raw_clip_override_path"], raw_override.resolve())

    def test_validate_short_manifest_allows_dual_beat_overrides(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-short-models-") as models_root, tempfile.TemporaryDirectory(
            prefix="ce-short-overrides-"
        ) as temp_dir:
            builder = self.make_builder(Path(models_root))
            temp_root = Path(temp_dir)
            manifest_path = ROOT / "references/episodes/challenger/shorts/challenger_short_minimal_surreal_v1.json"
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.make_short_manifest_audio_self_contained(builder, payload, temp_root)
            for beat in payload["beats"]:
                beat.pop("still_override_path", None)
                beat.pop("raw_clip_override_path", None)
            still_override = temp_root / "still.png"
            raw_override = temp_root / "clip.mp4"
            Image.new("RGB", (90, 160), color=(0, 0, 0)).save(still_override)
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "color=c=black:s=90x160:d=1",
                    "-pix_fmt",
                    "yuv420p",
                    str(raw_override),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload["beats"][0]["still_override_path"] = str(still_override)
            payload["beats"][0]["raw_clip_override_path"] = str(raw_override)

            validated = builder.validate_short_manifest(Path("/tmp/challenger_short_minimal_surreal_v1.json"), payload)

            self.assertEqual(validated["beats"][0]["still_override_path"], still_override.resolve())
            self.assertEqual(validated["beats"][0]["raw_clip_override_path"], raw_override.resolve())

    def test_latest_pipeline_manifest_prefers_successful_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-short-models-") as models_root, tempfile.TemporaryDirectory(
            prefix="ce-short-runs-"
        ) as generated_root:
            builder = self.make_builder(Path(models_root))
            builder.compiler.generated_dir = Path(generated_root)
            run_dir = builder.compiler.generated_dir / "runs" / "shorts_scene_plate" / "challenger_warning_cold"
            run_dir.mkdir(parents=True, exist_ok=True)
            success_output = builder.compiler.generated_dir / "still.png"
            success_output.write_text("still", encoding="utf-8")
            failed_manifest = run_dir / f"20260101T000000Z{PIPELINE_MANIFEST_SUFFIX}"
            success_manifest = run_dir / f"20260101T000100Z{PIPELINE_MANIFEST_SUFFIX}"
            failed_manifest.write_text(
                json.dumps({"status": "failed", "final_outputs": [str(success_output)]}),
                encoding="utf-8",
            )
            success_manifest.write_text(
                json.dumps({"status": "success", "final_outputs": [str(success_output)]}),
                encoding="utf-8",
            )
            self.assertEqual(
                builder.latest_pipeline_manifest("shorts_scene_plate", "challenger_warning_cold"),
                success_manifest,
            )

    def test_latest_pipeline_manifest_accepts_advisory_status_when_requested(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-short-models-") as models_root, tempfile.TemporaryDirectory(
            prefix="ce-short-runs-"
        ) as generated_root:
            builder = self.make_builder(Path(models_root))
            builder.compiler.generated_dir = Path(generated_root)
            run_dir = builder.compiler.generated_dir / "runs" / "shorts_scene_plate" / "challenger_warning_cold"
            run_dir.mkdir(parents=True, exist_ok=True)
            advisory_output = builder.compiler.generated_dir / "still.png"
            advisory_output.write_text("still", encoding="utf-8")
            advisory_manifest = run_dir / f"20260101T000100Z{PIPELINE_MANIFEST_SUFFIX}"
            advisory_manifest.write_text(
                json.dumps({"status": "advisory_success", "final_outputs": [str(advisory_output)]}),
                encoding="utf-8",
            )
            self.assertEqual(
                builder.latest_pipeline_manifest(
                    "shorts_scene_plate",
                    "challenger_warning_cold",
                    accepted_statuses={"success", "advisory_success"},
                ),
                advisory_manifest,
            )

    def test_render_motion_clip_recovers_external_raw_clip_and_writes_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-short-models-") as models_root, tempfile.TemporaryDirectory(
            prefix="ce-short-motion-recovery-"
        ) as temp_dir:
            builder = self.make_builder(Path(models_root))
            temp_root = Path(temp_dir)
            builder.shorts_generated_root = temp_root / "generated" / "shorts"
            output_path = (
                builder.shorts_generated_root
                / "challenger_short_minimal_surreal_v1"
                / "20260406T081838Z"
                / "clips"
                / "raw"
                / "beat_01__raw.mp4"
            )
            external_clip = (
                temp_root
                / "mlx-video"
                / "workflows"
                / "generated"
                / "shorts"
                / "challenger_short_minimal_surreal_v1"
                / "20260406T081838Z"
                / "motion_proofs"
                / "raw"
                / "beat_01__raw.mp4"
            )
            external_clip.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "color=c=black:s=90x160:d=1",
                    "-pix_fmt",
                    "yuv420p",
                    str(external_clip),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            staged_path = temp_root / "staged.png"
            Image.new("RGB", (90, 160), color=(0, 0, 0)).save(staged_path)
            builder.run_command = mock.Mock(  # type: ignore[method-assign]
                return_value=subprocess.CompletedProcess(args=["handoff-i2v"], returncode=0, stdout="", stderr="")
            )
            builder.load_paths_config = mock.Mock(  # type: ignore[method-assign]
                return_value={"CE_MLX_VIDEO_DIR": str(temp_root / "mlx-video")}
            )

            with mock.patch("short_tool.ffprobe_duration", return_value=9.285):
                raw_clip_path, manifest_path = builder.render_motion_clip(
                    staged_path,
                    motion_prompt="stillness_breathe",
                    frames=223,
                    motion_pipeline="distilled",
                    output_path=output_path,
                )

            self.assertEqual(raw_clip_path, output_path.resolve())
            self.assertTrue(raw_clip_path.exists())
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["recovered_from_path"], str(external_clip.resolve()))
            self.assertEqual(payload["pipeline"], "distilled")
            self.assertEqual(payload["frames"], 223)

    def test_import_raw_clip_override_copies_clip_and_writes_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-short-models-") as models_root, tempfile.TemporaryDirectory(
            prefix="ce-short-raw-override-"
        ) as temp_dir:
            builder = self.make_builder(Path(models_root))
            temp_root = Path(temp_dir)
            source_clip = temp_root / "source.mp4"
            output_path = temp_root / "generated" / "beat_05__raw.mp4"
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "color=c=black:s=90x160:d=1",
                    "-pix_fmt",
                    "yuv420p",
                    str(source_clip),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            with mock.patch("short_tool.ffprobe_duration", return_value=10.912):
                raw_clip_path, manifest_path = builder.import_raw_clip_override(
                    source_clip,
                    motion_prompt="stillness_breathe",
                    frames=262,
                    motion_pipeline="distilled",
                    output_path=output_path,
                )

            self.assertEqual(raw_clip_path, output_path.resolve())
            self.assertTrue(raw_clip_path.exists())
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["output_path"], str(output_path.resolve()))
            self.assertEqual(payload["frames"], 262)
            self.assertEqual(payload["pipeline"], "distilled")

    def test_preflight_headless_runtime_fails_when_main_path_missing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-short-models-") as models_root:
            builder = self.make_builder(Path(models_root))
            builder.load_headless_config = mock.Mock(  # type: ignore[method-assign]
                return_value={
                    "CE_COMFY_MAIN_PY": "/tmp/does-not-exist-main.py",
                    "CE_COMFY_PYTHON": sys.executable,
                    "CE_COMFY_CLIP_VISION_MODEL": "clip_vision_g.safetensors",
                    "CE_COMFY_HEADLESS_HOST": "127.0.0.1",
                    "CE_COMFY_HEADLESS_PORT": "8188",
                }
            )
            with self.assertRaisesRegex(Exception, "CE_COMFY_MAIN_PY"):
                builder.preflight_headless_runtime()

    def test_preflight_headless_runtime_fails_when_clip_vision_model_missing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-short-models-") as models_root, tempfile.TemporaryDirectory(
            prefix="ce-short-headless-"
        ) as temp_dir:
            builder = self.make_builder(Path(models_root))
            main_path = Path(temp_dir) / "main.py"
            python_path = Path(temp_dir) / "python"
            main_path.write_text("print('stub')\n", encoding="utf-8")
            python_path.write_text("stub\n", encoding="utf-8")
            builder.load_headless_config = mock.Mock(  # type: ignore[method-assign]
                return_value={
                    "CE_COMFY_MAIN_PY": str(main_path),
                    "CE_COMFY_PYTHON": str(python_path),
                    "CE_COMFY_CLIP_VISION_MODEL": "clip_vision_g.safetensors",
                    "CE_COMFY_HEADLESS_HOST": "127.0.0.1",
                    "CE_COMFY_HEADLESS_PORT": "8188",
                }
            )
            with self.assertRaisesRegex(Exception, "CE_COMFY_CLIP_VISION_MODEL"):
                builder.preflight_headless_runtime()

    def test_preflight_headless_runtime_fails_when_system_stats_unreachable(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-short-models-") as models_root, tempfile.TemporaryDirectory(
            prefix="ce-short-headless-"
        ) as temp_dir:
            builder = self.make_builder(Path(models_root))
            main_path = Path(temp_dir) / "main.py"
            python_path = Path(temp_dir) / "python"
            clip_vision_dir = Path(models_root) / "clip_vision"
            main_path.write_text("print('stub')\n", encoding="utf-8")
            python_path.write_text("stub\n", encoding="utf-8")
            clip_vision_dir.mkdir(parents=True, exist_ok=True)
            (clip_vision_dir / "clip_vision_g.safetensors").write_text("stub\n", encoding="utf-8")
            builder.load_headless_config = mock.Mock(  # type: ignore[method-assign]
                return_value={
                    "CE_COMFY_MAIN_PY": str(main_path),
                    "CE_COMFY_PYTHON": str(python_path),
                    "CE_COMFY_CLIP_VISION_MODEL": "clip_vision_g.safetensors",
                    "CE_COMFY_HEADLESS_HOST": "127.0.0.1",
                    "CE_COMFY_HEADLESS_PORT": "8188",
                }
            )
            builder.run_command = mock.Mock()  # type: ignore[method-assign]
            builder.fetch_headless_system_stats = mock.Mock(  # type: ignore[method-assign]
                side_effect=Exception("boom")
            )
            with self.assertRaisesRegex(Exception, "boom"):
                builder.preflight_headless_runtime()

    @mock.patch("short_tool.ensure_command", autospec=True)
    def test_build_writes_manifest_structure(self, ensure_command_mock: mock.Mock) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-short-models-") as models_root, tempfile.TemporaryDirectory(
            prefix="ce-short-build-"
        ) as temp_dir:
            builder = self.make_builder(Path(models_root))
            temp_root = Path(temp_dir)
            manifest_stub = temp_root / "manifest.json"
            audio_path = temp_root / "audio.wav"
            transcript_path = temp_root / "transcript.txt"
            still_path = temp_root / "still.png"
            stage_manifest = temp_root / "stage.json"
            raw_clip_manifest = temp_root / "raw.mp4.json"
            packaging_manifest = temp_root / "packaging.run.json"
            proof_path = temp_root / "proof.mp4"
            picture_path = temp_root / "picture.mp4"
            normalized_clip = temp_root / "normalized.mp4"
            raw_clip = temp_root / "raw.mp4"
            for path in (
                audio_path,
                transcript_path,
                still_path,
                stage_manifest,
                raw_clip_manifest,
                packaging_manifest,
                proof_path,
                picture_path,
                normalized_clip,
                raw_clip,
                manifest_stub,
            ):
                path.write_text("stub", encoding="utf-8")

            builder.shorts_generated_root = temp_root / "generated"
            manifest_stub.write_text("{}", encoding="utf-8")
            builder.resolve_short_manifest_path = mock.Mock(return_value=manifest_stub)  # type: ignore[method-assign]
            builder.validate_short_manifest = mock.Mock(  # type: ignore[method-assign]
                return_value={
                    "short_id": "challenger_short_minimal_surreal_v1",
                    "title": "Challenger Short Minimal Surreal v1",
                    "episode_id": "challenger",
                    "audio_path": audio_path,
                    "audio_duration_seconds": 55.541667,
                    "transcript_path": transcript_path,
                    "fps": 24,
                    "packaging_frame_id": "shorts_cover_plate/challenger_thesis_cover",
                    "packaging_family": "shorts_cover_plate",
                    "packaging_preset": "challenger_thesis_cover",
                    "beats": [
                        {
                            "id": "beat_01",
                            "family": "shorts_scene_plate",
                            "preset": "challenger_warning_cold",
                            "preset_id": "shorts_scene_plate/challenger_warning_cold",
                            "cue_start_seconds": 0.031,
                            "cue_end_seconds": 8.503,
                            "target_duration_seconds": 9.285,
                            "motion_prompt": "stillness_breathe",
                            "motion_pipeline": "distilled",
                            "frames": 223,
                        }
                    ],
                }
            )
            builder.preflight_headless_runtime = mock.Mock(  # type: ignore[method-assign]
                return_value={
                    "server_url": "http://127.0.0.1:8188",
                    "comfy_main_py": "/tmp/comfy/main.py",
                    "comfy_python": "/tmp/comfy/python",
                }
            )
            builder.ensure_pipeline_output = mock.Mock(  # type: ignore[method-assign]
                side_effect=[
                    (packaging_manifest, {"status": "advisory_success", "delivery_advisory_used": True}, still_path),
                    (
                        temp_root / "still_pipeline.run.json",
                        {"status": "advisory_success", "delivery_advisory_used": True},
                        still_path,
                    ),
                ]
            )
            builder.stage_still = mock.Mock(return_value=(temp_root / "staged.png", stage_manifest))  # type: ignore[method-assign]
            builder.render_motion_clip = mock.Mock(return_value=(raw_clip, raw_clip_manifest))  # type: ignore[method-assign]
            builder.normalize_clip = mock.Mock(return_value=normalized_clip)  # type: ignore[method-assign]
            builder.concat_picture_segments = mock.Mock(return_value=picture_path)  # type: ignore[method-assign]
            builder.mux_proof = mock.Mock(return_value=proof_path)  # type: ignore[method-assign]
            builder.render_beat_sheet = mock.Mock(return_value=temp_root / "beat_sheet.png")  # type: ignore[method-assign]

            manifest_path = builder.build(
                "challenger_short_minimal_surreal_v1",
                delivery_mode="advisory",
                quality_profile="fast",
            )
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["delivery_mode"], "advisory")
            self.assertEqual(payload["render_quality_profile"], "fast")
            self.assertEqual(payload["headless_comfy"]["server_url"], "http://127.0.0.1:8188")
            self.assertEqual(payload["packaging_frame_id"], "shorts_cover_plate/challenger_thesis_cover")
            self.assertTrue(payload["packaging_frame_delivery_advisory_used"])
            self.assertEqual(payload["packaging_frame_path"], str(still_path))
            self.assertTrue(payload["beats"][0]["still_delivery_advisory_used"])
            self.assertEqual(payload["beats"][0]["normalized_clip_path"], str(normalized_clip))
            self.assertEqual(payload["proof_path"], str(proof_path))
            self.assertEqual(payload["picture_master_path"], str(picture_path))

    @mock.patch("short_tool.ensure_command", autospec=True)
    def test_build_still_holds_skips_motion_rendering(self, ensure_command_mock: mock.Mock) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-short-models-") as models_root, tempfile.TemporaryDirectory(
            prefix="ce-short-build-"
        ) as temp_dir:
            builder = self.make_builder(Path(models_root))
            temp_root = Path(temp_dir)
            manifest_stub = temp_root / "manifest.json"
            audio_path = temp_root / "audio.wav"
            transcript_path = temp_root / "transcript.txt"
            still_path = temp_root / "still.png"
            packaging_manifest = temp_root / "packaging.run.json"
            proof_path = temp_root / "proof.mp4"
            picture_path = temp_root / "picture.mp4"
            normalized_clip = temp_root / "normalized.mp4"
            raw_clip = temp_root / "raw.mp4"
            raw_clip_manifest = temp_root / "raw.mp4.json"
            for path in (
                audio_path,
                transcript_path,
                packaging_manifest,
                proof_path,
                picture_path,
                normalized_clip,
                raw_clip,
                raw_clip_manifest,
            ):
                path.write_text("stub", encoding="utf-8")
            manifest_stub.write_text("{}", encoding="utf-8")
            Image.new("RGB", (90, 160), color=(0, 0, 0)).save(still_path)

            builder.shorts_generated_root = temp_root / "generated"
            builder.resolve_short_manifest_path = mock.Mock(return_value=manifest_stub)  # type: ignore[method-assign]
            builder.validate_short_manifest = mock.Mock(  # type: ignore[method-assign]
                return_value={
                    "short_id": "challenger_short_minimal_surreal_v3_trimmed",
                    "title": "Challenger Short Minimal Surreal v3 Trimmed",
                    "episode_id": "challenger",
                    "audio_path": audio_path,
                    "audio_duration_seconds": 57.306848,
                    "transcript_path": transcript_path,
                    "fps": 24,
                    "packaging_frame_id": "shorts_cover_plate/challenger_thesis_cover",
                    "packaging_family": "shorts_cover_plate",
                    "packaging_preset": "challenger_thesis_cover",
                    "packaging_frame_still_override_path": None,
                    "beats": [
                        {
                            "id": "beat_01",
                            "family": "shorts_scene_plate",
                            "preset": "challenger_boisjoly_warning",
                            "preset_id": "shorts_scene_plate/challenger_boisjoly_warning",
                            "cue_start_seconds": 0.031,
                            "cue_end_seconds": 11.185,
                            "target_duration_seconds": 12.188,
                            "motion_prompt": "stillness_breathe",
                            "motion_pipeline": "distilled",
                            "frames": 293,
                            "still_override_path": still_path,
                            "raw_clip_override_path": None,
                        }
                    ],
                }
            )
            builder.preflight_headless_runtime = mock.Mock(  # type: ignore[method-assign]
                return_value={"server_url": "http://127.0.0.1:8188"}
            )
            builder.ensure_pipeline_output = mock.Mock(  # type: ignore[method-assign]
                return_value=(packaging_manifest, {"status": "success", "delivery_advisory_used": False}, still_path)
            )
            builder.render_still_hold_clip = mock.Mock(return_value=(raw_clip, raw_clip_manifest))  # type: ignore[method-assign]
            builder.stage_still = mock.Mock(side_effect=AssertionError("stage_still should not run"))  # type: ignore[method-assign]
            builder.render_motion_clip = mock.Mock(side_effect=AssertionError("render_motion_clip should not run"))  # type: ignore[method-assign]
            builder.normalize_clip = mock.Mock(return_value=normalized_clip)  # type: ignore[method-assign]
            builder.concat_picture_segments = mock.Mock(return_value=picture_path)  # type: ignore[method-assign]
            builder.mux_proof = mock.Mock(return_value=proof_path)  # type: ignore[method-assign]
            builder.render_beat_sheet = mock.Mock(return_value=temp_root / "beat_sheet.png")  # type: ignore[method-assign]

            manifest_path = builder.build(
                "challenger_short_minimal_surreal_v3_trimmed",
                delivery_mode="strict",
                quality_profile="standard",
                clip_mode="still_holds",
            )
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["clip_mode"], "still_holds")
            self.assertEqual(payload["beats"][0]["raw_clip_source_mode"], "still_hold")
            self.assertEqual(payload["beats"][0]["still_override_path"], str(still_path))
            builder.render_still_hold_clip.assert_called_once()
            builder.stage_still.assert_not_called()
            builder.render_motion_clip.assert_not_called()

    @mock.patch("short_tool.ensure_command", autospec=True)
    def test_build_still_holds_prefers_still_source_with_raw_clip_override(self, ensure_command_mock: mock.Mock) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-short-models-") as models_root, tempfile.TemporaryDirectory(
            prefix="ce-short-build-"
        ) as temp_dir:
            builder = self.make_builder(Path(models_root))
            temp_root = Path(temp_dir)
            manifest_stub = temp_root / "manifest.json"
            audio_path = temp_root / "audio.wav"
            transcript_path = temp_root / "transcript.txt"
            still_path = temp_root / "still.png"
            raw_override = temp_root / "override.mp4"
            packaging_manifest = temp_root / "packaging.run.json"
            proof_path = temp_root / "proof.mp4"
            picture_path = temp_root / "picture.mp4"
            normalized_clip = temp_root / "normalized.mp4"
            raw_clip = temp_root / "raw.mp4"
            raw_clip_manifest = temp_root / "raw.mp4.json"
            for path in (
                audio_path,
                transcript_path,
                packaging_manifest,
                proof_path,
                picture_path,
                normalized_clip,
                raw_clip,
                raw_clip_manifest,
            ):
                path.write_text("stub", encoding="utf-8")
            manifest_stub.write_text("{}", encoding="utf-8")
            Image.new("RGB", (90, 160), color=(0, 0, 0)).save(still_path)
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "color=c=black:s=90x160:d=1",
                    "-pix_fmt",
                    "yuv420p",
                    str(raw_override),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            builder.shorts_generated_root = temp_root / "generated"
            builder.resolve_short_manifest_path = mock.Mock(return_value=manifest_stub)  # type: ignore[method-assign]
            builder.validate_short_manifest = mock.Mock(  # type: ignore[method-assign]
                return_value={
                    "short_id": "challenger_short_minimal_surreal_v3_trimmed",
                    "title": "Challenger Short Minimal Surreal v3 Trimmed",
                    "episode_id": "challenger",
                    "audio_path": audio_path,
                    "audio_duration_seconds": 57.306848,
                    "transcript_path": transcript_path,
                    "fps": 24,
                    "packaging_frame_id": "shorts_cover_plate/challenger_thesis_cover",
                    "packaging_family": "shorts_cover_plate",
                    "packaging_preset": "challenger_thesis_cover",
                    "packaging_frame_still_override_path": None,
                    "beats": [
                        {
                            "id": "beat_01",
                            "family": "shorts_scene_plate",
                            "preset": "challenger_boisjoly_warning",
                            "preset_id": "shorts_scene_plate/challenger_boisjoly_warning",
                            "cue_start_seconds": 0.031,
                            "cue_end_seconds": 11.185,
                            "target_duration_seconds": 12.188,
                            "motion_prompt": "stillness_breathe",
                            "motion_pipeline": "distilled",
                            "frames": 293,
                            "still_override_path": still_path,
                            "raw_clip_override_path": raw_override,
                        }
                    ],
                }
            )
            builder.preflight_headless_runtime = mock.Mock(  # type: ignore[method-assign]
                return_value={"server_url": "http://127.0.0.1:8188"}
            )
            builder.ensure_pipeline_output = mock.Mock(  # type: ignore[method-assign]
                return_value=(packaging_manifest, {"status": "success", "delivery_advisory_used": False}, still_path)
            )
            builder.render_still_hold_clip = mock.Mock(return_value=(raw_clip, raw_clip_manifest))  # type: ignore[method-assign]
            builder.stage_still = mock.Mock(side_effect=AssertionError("stage_still should not run"))  # type: ignore[method-assign]
            builder.render_motion_clip = mock.Mock(side_effect=AssertionError("render_motion_clip should not run"))  # type: ignore[method-assign]
            builder.import_raw_clip_override = mock.Mock(side_effect=AssertionError("raw override should not run in still_holds"))  # type: ignore[method-assign]
            builder.normalize_clip = mock.Mock(return_value=normalized_clip)  # type: ignore[method-assign]
            builder.concat_picture_segments = mock.Mock(return_value=picture_path)  # type: ignore[method-assign]
            builder.mux_proof = mock.Mock(return_value=proof_path)  # type: ignore[method-assign]
            builder.render_beat_sheet = mock.Mock(return_value=temp_root / "beat_sheet.png")  # type: ignore[method-assign]

            manifest_path = builder.build(
                "challenger_short_minimal_surreal_v3_trimmed",
                clip_mode="still_holds",
            )

            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["beats"][0]["raw_clip_source_mode"], "still_hold")
            self.assertEqual(payload["beats"][0]["raw_clip_override_path"], str(raw_override))
            builder.render_still_hold_clip.assert_called_once()
            builder.import_raw_clip_override.assert_not_called()

    @mock.patch("short_tool.ensure_command", autospec=True)
    def test_build_uses_packaging_frame_still_override_without_pipeline(self, ensure_command_mock: mock.Mock) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-short-models-") as models_root, tempfile.TemporaryDirectory(
            prefix="ce-short-build-packaging-override-"
        ) as temp_dir:
            builder = self.make_builder(Path(models_root))
            temp_root = Path(temp_dir)
            manifest_stub = temp_root / "manifest.json"
            audio_path = temp_root / "audio.wav"
            transcript_path = temp_root / "transcript.txt"
            cover_path = temp_root / "cover.png"
            still_path = temp_root / "still.png"
            proof_path = temp_root / "proof.mp4"
            picture_path = temp_root / "picture.mp4"
            normalized_clip = temp_root / "normalized.mp4"
            raw_clip = temp_root / "raw.mp4"
            raw_clip_manifest = temp_root / "raw.mp4.json"
            for path in (
                audio_path,
                transcript_path,
                proof_path,
                picture_path,
                normalized_clip,
                raw_clip,
                raw_clip_manifest,
            ):
                path.write_text("stub", encoding="utf-8")
            manifest_stub.write_text("{}", encoding="utf-8")
            Image.new("RGB", (90, 160), color=(0, 0, 0)).save(cover_path)
            Image.new("RGB", (90, 160), color=(0, 0, 0)).save(still_path)

            builder.shorts_generated_root = temp_root / "generated"
            builder.resolve_short_manifest_path = mock.Mock(return_value=manifest_stub)  # type: ignore[method-assign]
            builder.validate_short_manifest = mock.Mock(  # type: ignore[method-assign]
                return_value={
                    "short_id": "challenger_short_minimal_surreal_v3_trimmed",
                    "title": "Challenger Short Minimal Surreal v3 Trimmed",
                    "episode_id": "challenger",
                    "audio_path": audio_path,
                    "audio_duration_seconds": 57.306848,
                    "transcript_path": transcript_path,
                    "fps": 24,
                    "packaging_frame_id": "shorts_cover_plate/challenger_thesis_cover",
                    "packaging_family": "shorts_cover_plate",
                    "packaging_preset": "challenger_thesis_cover",
                    "packaging_frame_still_override_path": cover_path,
                    "beats": [
                        {
                            "id": "beat_01",
                            "family": "shorts_scene_plate",
                            "preset": "challenger_boisjoly_warning",
                            "preset_id": "shorts_scene_plate/challenger_boisjoly_warning",
                            "cue_start_seconds": 0.031,
                            "cue_end_seconds": 11.185,
                            "target_duration_seconds": 12.188,
                            "motion_prompt": "stillness_breathe",
                            "motion_pipeline": "distilled",
                            "frames": 293,
                            "still_override_path": still_path,
                            "raw_clip_override_path": None,
                        }
                    ],
                }
            )
            builder.preflight_headless_runtime = mock.Mock(  # type: ignore[method-assign]
                return_value={"server_url": "http://127.0.0.1:8188"}
            )
            builder.ensure_pipeline_output = mock.Mock(side_effect=AssertionError("packaging pipeline should not run"))  # type: ignore[method-assign]
            builder.stage_still = mock.Mock(return_value=(temp_root / "staged.png", temp_root / "stage.run.json"))  # type: ignore[method-assign]
            builder.render_motion_clip = mock.Mock(return_value=(raw_clip, raw_clip_manifest))  # type: ignore[method-assign]
            builder.normalize_clip = mock.Mock(return_value=normalized_clip)  # type: ignore[method-assign]
            builder.concat_picture_segments = mock.Mock(return_value=picture_path)  # type: ignore[method-assign]
            builder.mux_proof = mock.Mock(return_value=proof_path)  # type: ignore[method-assign]
            builder.render_beat_sheet = mock.Mock(return_value=temp_root / "beat_sheet.png")  # type: ignore[method-assign]

            manifest_path = builder.build(
                "challenger_short_minimal_surreal_v3_trimmed",
                delivery_mode="strict",
                quality_profile="standard",
                clip_mode="animated",
            )
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["packaging_frame_status"], "override")
            self.assertEqual(payload["packaging_frame_still_override_path"], str(cover_path))
            self.assertEqual(payload["packaging_frame_path"], str(cover_path.resolve()))
            builder.ensure_pipeline_output.assert_not_called()

    def make_midjourney_export_builder(self, repo_root: Path, episode_root: Path) -> tuple[ShortBuilder, dict[str, object]]:
        (repo_root / "workflows" / "style_profiles").mkdir(parents=True, exist_ok=True)
        (repo_root / "workflows" / "specs" / "shorts_scene_plate").mkdir(parents=True, exist_ok=True)
        (repo_root / "workflows" / "specs" / "shorts_cover_plate").mkdir(parents=True, exist_ok=True)
        (repo_root / "references" / "episodes" / "challenger" / "shorts").mkdir(parents=True, exist_ok=True)
        (repo_root / "workflows" / "generated").mkdir(parents=True, exist_ok=True)
        (repo_root / "renders").mkdir(parents=True, exist_ok=True)
        (repo_root / "models").mkdir(parents=True, exist_ok=True)

        style_profile_source = ROOT / "workflows" / "style_profiles" / "minimal_surreal_editorial.json"
        shutil.copy2(style_profile_source, repo_root / "workflows" / "style_profiles" / style_profile_source.name)

        short_manifest_path = ROOT / "references" / "episodes" / "challenger" / "shorts" / "challenger_short_minimal_surreal_v1.json"
        short_manifest = json.loads(short_manifest_path.read_text(encoding="utf-8"))
        audio_path = episode_root / "Ep1_Challenger" / "shorts" / "challenger_short_v1" / "final" / "challenger_short_v1.wav"
        transcript_path = episode_root / "Ep1_Challenger" / "shorts" / "challenger_short_v1" / "final" / "challenger_short_v1.diarized.txt"
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        transcript_path.parent.mkdir(parents=True, exist_ok=True)
        audio_path.write_text("stub", encoding="utf-8")
        transcript_path.write_text("stub", encoding="utf-8")
        short_manifest["audio_path"] = str(audio_path)
        short_manifest["transcript_path"] = str(transcript_path)
        (repo_root / "references" / "episodes" / "challenger" / "shorts" / short_manifest_path.name).write_text(
            json.dumps(short_manifest, indent=2),
            encoding="utf-8",
        )

        cover_preset = short_manifest["packaging_frame_id"].split("/", 1)[1]
        scene_presets = [beat["preset_id"].split("/", 1)[1] for beat in short_manifest["beats"]]
        for preset in [cover_preset, *scene_presets]:
            family = "shorts_cover_plate" if preset == cover_preset else "shorts_scene_plate"
            for stage in ("draft_txt2img", "refine_img2img", "final_upscale"):
                source_spec = ROOT / "workflows" / "specs" / family / f"{preset}__{stage}.json"
                shutil.copy2(source_spec, repo_root / "workflows" / "specs" / family / source_spec.name)

        inventory_source = Path("/Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/visual_research/source_inventory.json")
        inventory_payload = json.loads(inventory_source.read_text(encoding="utf-8"))
        selected_source_ids = {
            "opening_02",
            "act1_05",
            "act2_01",
            "act2_02",
            "act2_03",
            "act2_04",
            "act2_05",
            "act2_06",
            "act2_08",
            "act3_01",
            "act3_02",
            "act3_03",
            "act3_04",
            "act3_06",
            "act3_07",
            "act3_08",
            "act4_01",
            "act4_02",
            "act4_03",
            "act4_04",
            "act4_06",
            "act4_07",
        }
        visual_research_dir = episode_root / "Ep1_Challenger" / "visual_research"
        research_assets_dir = visual_research_dir / "research_assets"
        research_assets_dir.mkdir(parents=True, exist_ok=True)
        subset = []
        for item in inventory_payload["sources"]:
            source_id = item["source_id"]
            if source_id not in selected_source_ids:
                continue
            copied = dict(item)
            suffix = Path(str(item["raw_asset_path"])).suffix or ".jpg"
            asset_path = research_assets_dir / f"{source_id}{suffix}"
            asset_path.write_text(f"stub-{source_id}\n", encoding="utf-8")
            copied["raw_asset_path"] = str(asset_path)
            subset.append(copied)
        visual_research_dir.mkdir(parents=True, exist_ok=True)
        (visual_research_dir / "source_inventory.json").write_text(
            json.dumps({"schema_version": "1.0", "sources": subset}, indent=2),
            encoding="utf-8",
        )
        (visual_research_dir / "sources.md").write_text("# Challenger Source Package\n", encoding="utf-8")

        builder = ShortBuilder(
            repo_root=repo_root,
            models_root=repo_root / "models",
            comfy_workflows_dir=repo_root / "workflows" / "generated",
            comfy_output_dir=repo_root / "renders",
            references_root=repo_root / "references",
        )
        validated_payload: dict[str, object] = {
            "short_id": "challenger_short_minimal_surreal_v1",
            "episode_id": "challenger",
            "title": "Challenger Short Minimal Surreal v1",
            "audio_path": audio_path,
            "audio_duration_seconds": 55.541667,
            "transcript_path": transcript_path,
            "fps": 24,
            "packaging_frame_id": "shorts_cover_plate/challenger_thesis_cover",
            "packaging_family": "shorts_cover_plate",
            "packaging_preset": "challenger_thesis_cover",
            "beats": [],
        }
        for beat in short_manifest["beats"]:
            family, preset = beat["preset_id"].split("/", 1)
            validated_payload["beats"].append(  # type: ignore[union-attr]
                {
                    "id": beat["id"],
                    "family": family,
                    "preset": preset,
                    "preset_id": beat["preset_id"],
                    "cue_start_seconds": beat["cue_start_seconds"],
                    "cue_end_seconds": beat["cue_end_seconds"],
                    "target_duration_seconds": beat["target_duration_seconds"],
                    "motion_prompt": beat["motion_prompt"],
                    "motion_pipeline": beat["motion_pipeline"],
                    "frames": duration_to_frames(float(beat["target_duration_seconds"]), 24),
                }
            )
        return builder, validated_payload

    @mock.patch("short_tool.ffprobe_duration", autospec=True, return_value=55.541667)
    def test_export_midjourney_writes_package_with_provenance(self, ffprobe_duration_mock: mock.Mock) -> None:
        del ffprobe_duration_mock
        with tempfile.TemporaryDirectory(prefix="ce-midjourney-repo-") as repo_root_str, tempfile.TemporaryDirectory(
            prefix="ce-midjourney-episode-"
        ) as episode_root_str:
            builder, validated_payload = self.make_midjourney_export_builder(Path(repo_root_str), Path(episode_root_str))
            builder.validate_short_manifest = mock.Mock(return_value=validated_payload)  # type: ignore[method-assign]
            package_manifest_path = builder.export_midjourney("challenger_short_minimal_surreal_v1")

            package_root = package_manifest_path.parent
            payload = json.loads(package_manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["surface_type"], "short_beats")
            self.assertEqual(payload["reference_mode"], "manual_upload_local_files_with_provenance")
            self.assertEqual(payload["midjourney_defaults"]["parameter_suffix"], "--v 7 --ar 9:16 --raw --s 75")
            self.assertEqual(payload["cover"]["preset_id"], "shorts_cover_plate/challenger_thesis_cover")
            self.assertEqual(len(payload["cover"]["reference_files"]), 4)
            self.assertEqual(len(payload["shots"]), 7)
            self.assertEqual(payload["shots"][0]["shot_id"], "beat_01")
            self.assertEqual(
                [item["source_id"] for item in payload["shots"][0]["reference_provenance"]],
                ["act3_06", "act3_07", "act3_08"],
            )
            self.assertTrue((package_root / payload["cover"]["reference_files"][0]).exists())
            self.assertTrue((package_root / payload["shots"][0]["reference_files"][0]).exists())
            prompt_doc = package_root / payload["shots"][0]["prompt_doc_path"]
            prompt_text = prompt_doc.read_text(encoding="utf-8")
            self.assertIn("Midjourney reference upload order:", prompt_text)
            self.assertIn("Curated --no terms:", prompt_text)
            self.assertIn("Stillness, soft diffuse light, quiet suspended atmosphere.", prompt_text)
            self.assertNotIn("minimal surreal editorial composition", prompt_text)
            shot_list_path = package_root / payload["shot_list_path"]
            self.assertTrue(shot_list_path.exists())
            shot_list_text = shot_list_path.read_text(encoding="utf-8")
            self.assertIn("## Cover", shot_list_text)
            self.assertIn("### beat_07", shot_list_text)

    @mock.patch("short_tool.ffprobe_duration", autospec=True, return_value=55.541667)
    def test_export_midjourney_fails_when_reference_asset_is_missing(self, ffprobe_duration_mock: mock.Mock) -> None:
        del ffprobe_duration_mock
        with tempfile.TemporaryDirectory(prefix="ce-midjourney-repo-") as repo_root_str, tempfile.TemporaryDirectory(
            prefix="ce-midjourney-episode-"
        ) as episode_root_str:
            episode_root = Path(episode_root_str)
            builder, validated_payload = self.make_midjourney_export_builder(Path(repo_root_str), episode_root)
            builder.validate_short_manifest = mock.Mock(return_value=validated_payload)  # type: ignore[method-assign]
            missing_path = (
                episode_root / "Ep1_Challenger" / "visual_research" / "research_assets" / "act3_06.jpg"
            )
            missing_path.unlink()
            with self.assertRaisesRegex(Exception, "act3_06.raw_asset_path"):
                builder.export_midjourney("challenger_short_minimal_surreal_v1")


if __name__ == "__main__":
    unittest.main()
