from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import io
import json
import os
import tempfile
import unittest
from unittest import mock
from pathlib import Path
from urllib import error as urllib_error

from orchestration.adapters import (
    BuzzsproutPublishResult,
    YouTubeDeleteResult,
    YouTubePublishResult,
    YouTubePublisher,
    YouTubeTitleUpdateResult,
    YouTubeVideoStatus,
)
from orchestration.cli import (
    build_context,
    command_publish,
    command_publish_check,
    command_publish_package_delete,
    command_publish_package_status,
    command_publish_package_update_title,
    command_publish_package_upload,
    command_publish_prepare,
    command_publish_status,
)
from orchestration.domain import derive_episode_state, render_brief
from orchestration.io import Context, load_episode_manifest, materialize_episode_manifest, write_episode_manifest
from orchestration.publish import (
    PublishValidationError,
    build_buzzsprout_publisher_from_env,
    build_publish_bundle,
    build_publish_status,
    build_youtube_package_publisher,
    build_youtube_shorts_publish_payload,
    build_youtube_publisher_from_env,
    load_publish_state,
    prepare_publish,
    publish_package_delete,
    publish_package_status,
    publish_package_update_title,
    publish_package_upload,
    publish_episode,
    validate_publish_package_manifest,
    validate_publish_bundle,
)


ROOT = Path("/Users/mike/Agents_CascadeEffects")


class StubYouTubePublisher:
    def __init__(self, *, result: YouTubePublishResult | None = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.publish_calls: list[dict[str, object]] = []

    def validate_credentials(self) -> dict[str, str]:
        return {"channel_id": "test-channel", "validated_at": "2026-03-30T00:00:00Z"}

    def publish_video(self, payload: dict[str, object]) -> YouTubePublishResult:
        self.publish_calls.append(payload)
        if self.error is not None:
            raise self.error
        assert self.result is not None
        return self.result


class StubPackageYouTubePublisher:
    def __init__(self, *, video_id: str = "yt-package-123", channel_id: str = "test-channel", status_channel_id: str | None = None) -> None:
        self.video_id = video_id
        self.channel_id = channel_id
        self.status_channel_id = status_channel_id or channel_id
        self.publish_calls: list[dict[str, object]] = []
        self.title_update_calls: list[tuple[str, str]] = []
        self.delete_calls: list[str] = []
        self.deleted_ids: set[str] = set()
        self.titles: dict[str, str] = {video_id: "Title"}

    def get_authenticated_channel(self) -> dict[str, object]:
        return {
            "channel_id": self.channel_id,
            "title": "Cascade Effects Test Channel",
            "custom_url": "@cascadeeffectstest",
            "raw_response": {},
        }

    def publish_video(self, payload: dict[str, object]) -> YouTubePublishResult:
        self.publish_calls.append(payload)
        self.titles[self.video_id] = str(payload.get("title", "Title")).strip() or "Title"
        return YouTubePublishResult(
            video_id=self.video_id,
            video_url=f"https://www.youtube.com/watch?v={self.video_id}",
            scheduled_for="",
            published_at="2026-04-29T00:00:00Z",
            raw_response={"id": self.video_id},
            thumbnail_status="failed_nonfatal",
            thumbnail_error="thumbnail permission not enabled",
        )

    def get_video_status(self, video_id: str) -> YouTubeVideoStatus:
        exists = video_id not in self.deleted_ids
        return YouTubeVideoStatus(
            video_id=video_id,
            exists=exists,
            video_url=f"https://www.youtube.com/watch?v={video_id}",
            channel_id=self.status_channel_id if exists else "",
            channel_title="Cascade Effects Test Channel" if exists else "",
            title=self.titles.get(video_id, "Title") if exists else "",
            privacy_status="unlisted" if exists else "",
            upload_status="processed" if exists else "",
            processing_status="succeeded" if exists else "",
            published_at="2026-04-29T00:00:00Z" if exists else "",
            raw_response={"items": [{"id": video_id, "status": {"embeddable": True}}]} if exists else {"items": []},
            embeddable=exists,
        )

    def update_video_title(self, video_id: str, title: str) -> YouTubeTitleUpdateResult:
        old_title = self.titles.get(video_id, "Title")
        new_title = str(title).strip()
        self.title_update_calls.append((video_id, new_title))
        self.titles[video_id] = new_title
        return YouTubeTitleUpdateResult(
            video_id=video_id,
            video_url=f"https://www.youtube.com/watch?v={video_id}",
            old_title=old_title,
            new_title=new_title,
            raw_response={"id": video_id, "snippet": {"title": new_title}},
            updated_at="2026-04-29T00:02:00Z",
        )

    def delete_video(self, video_id: str) -> YouTubeDeleteResult:
        self.delete_calls.append(video_id)
        self.deleted_ids.add(video_id)
        return YouTubeDeleteResult(
            video_id=video_id,
            deleted_at="2026-04-29T00:01:00Z",
            raw_response={},
        )


class FakeHTTPResponse:
    def __init__(self, payload: dict[str, object] | None = None, *, headers: dict[str, str] | None = None) -> None:
        self._body = json.dumps(payload or {}).encode("utf-8") if payload is not None else b""
        self.headers = headers or {}

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "FakeHTTPResponse":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None


class StubBuzzsproutPublisher:
    def __init__(self, *, result: BuzzsproutPublishResult | None = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.publish_calls: list[dict[str, object]] = []

    def validate_credentials(self) -> dict[str, str]:
        return {"podcast_id": "12345", "validated_at": "2026-03-30T00:00:00Z"}

    def publish_episode(self, payload: dict[str, object]) -> BuzzsproutPublishResult:
        self.publish_calls.append(payload)
        if self.error is not None:
            raise self.error
        assert self.result is not None
        return self.result


class PublishAutomationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = build_context(ROOT)

    def _build_temp_context(self, temp_root: Path) -> Context:
        (temp_root / "episodes").mkdir(parents=True, exist_ok=True)
        (temp_root / "state").mkdir(parents=True, exist_ok=True)
        (temp_root / "bin").mkdir(parents=True, exist_ok=True)
        helper = temp_root / "bin" / "ce-orchestrate"
        helper.write_text("#!/bin/sh\n", encoding="utf-8")
        channel = copy.deepcopy(self.context.channel)
        channel["paths"] = copy.deepcopy(channel["paths"])
        channel["paths"]["agents_root"] = str(temp_root)
        channel["paths"]["orchestrate_helper"] = str(helper)
        return Context(
            root=temp_root,
            channel=channel,
            web_entry_ids=self.context.web_entry_ids,
            asset_archetypes=self.context.asset_archetypes,
            episodes_repo=self.context.episodes_repo,
            audio_repo=self.context.audio_repo,
            viz_repo=self.context.viz_repo,
            web_repo=self.context.web_repo,
        )

    def _write_audio_package_metadata(
        self,
        pipeline_dir: Path,
        *,
        packaged_path: Path,
        transcript_path: Path,
    ) -> None:
        pipeline_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "provider": "elevenlabs",
            "voice": "voice_test_123",
            "model": "test_model_v2_hq",
            "effective_manifest_path": str(pipeline_dir / "effective_final_jobs.elevenlabs.jsonl"),
            "packaged_path": str(packaged_path),
            "packaged_sha256": "packaged-sha",
            "packaged_at": "2026-03-30T18:00:00Z",
            "transcript_path": str(transcript_path),
            "transcript_sha256": "transcript-sha",
            "qa_completed_at": "2026-03-30T18:05:00Z",
        }
        (pipeline_dir / "effective_final_jobs.elevenlabs.jsonl").write_text("{}\n", encoding="utf-8")
        (pipeline_dir / "audio_package.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def _sha256_file(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _write_valid_publish_package(self, temp_root: Path) -> Path:
        package_dir = temp_root / "publish"
        package_dir.mkdir(parents=True, exist_ok=True)
        video_path = package_dir / "short.mp4"
        title_path = package_dir / "title.txt"
        description_path = package_dir / "description.txt"
        tags_path = package_dir / "tags.txt"
        srt_path = package_dir / "captions.srt"
        cover_path = package_dir / "cover.png"
        metadata_path = package_dir / "metadata.md"
        checklist_path = package_dir / "checklist.md"
        review_path = package_dir / "final_review.md"
        source_manifest_path = package_dir / "final_export.json"
        locked_script_path = package_dir / "locked_script.txt"
        timing_source_path = package_dir / "voice_timing.diarized.srt"
        for path, text in (
            (video_path, "video"),
            (title_path, "Title"),
            (description_path, "Description"),
            (tags_path, "tag one, tag two"),
            (srt_path, "1\n00:00:00,000 --> 00:00:01,000\nCaption\n"),
            (cover_path, "cover"),
            (metadata_path, "# Metadata\n"),
            (checklist_path, "# Checklist\n"),
            (review_path, "# Review\n"),
            (source_manifest_path, "{}\n"),
            (locked_script_path, "Caption\n"),
            (timing_source_path, "1\n00:00:00,000 --> 00:00:01,000\nCaption\n"),
        ):
            path.write_text(text, encoding="utf-8")
        manifest_path = package_dir / "youtube_upload_manifest.json"
        payload = {
            "target": "youtube_shorts",
            "publication_readiness": "ready_for_upload_with_rights_check",
            "source_final": {
                "path": str(video_path),
                "sha256": self._sha256_file(video_path),
                "final_export_manifest_path": str(source_manifest_path),
                "review_path": str(review_path),
                "disposition": "keep",
                "reel_class": "keeper short",
                "may_publish": True,
                "caption_model": "script_locked_canonical_text_timing_from_asr_v1",
                "caption_text_source_policy": "script_locked_canonical_text_only",
                "caption_timing_source_policy": "asr_whisperx_timing_only",
                "caption_text_source_path": str(locked_script_path),
                "caption_timing_source_path": str(timing_source_path),
                "caption_text_matches_script_read": "pass",
                "caption_asr_text_not_used_read": "pass",
                "caption_alignment_coverage_read": "pass",
                "burned_in_and_sidecar_same_script_locked_source_read": "pass",
            },
            "upload_assets": {
                "video_path": str(video_path),
                "video_sha256": self._sha256_file(video_path),
                "caption_srt_path": str(srt_path),
                "caption_srt_sha256": self._sha256_file(srt_path),
                "suggested_cover_frame_path": str(cover_path),
                "suggested_cover_frame_sha256": self._sha256_file(cover_path),
                "metadata_path": str(metadata_path),
                "title_path": str(title_path),
                "title_sha256": self._sha256_file(title_path),
                "description_path": str(description_path),
                "description_sha256": self._sha256_file(description_path),
                "tags_path": str(tags_path),
                "tags_sha256": self._sha256_file(tags_path),
                "upload_checklist_path": str(checklist_path),
            },
            "technical_read": {"container": "mp4"},
            "youtube_metadata": {
                "title": "Title",
                "description_path": str(description_path),
                "tags": ["tag one", "tag two"],
                "privacy": "public",
            },
            "final_music_context": {
                "music_policy": "canonical_default",
                "music_track_id": "paper_architecture_theme_v1",
                "music_rights_check_status": "pending_youtube_upload_check",
            },
            "rights_and_claims": {
                "claim_risk": "check_upload_processing_before_public_release",
                "music_bed_used": True,
                "music_track_id": "paper_architecture_theme_v1",
                "music_policy": "canonical_default",
                "music_rights_check_status": "pending_youtube_upload_check",
            },
            "caption_context": {
                "caption_model": "script_locked_canonical_text_timing_from_asr_v1",
                "caption_text_source_policy": "script_locked_canonical_text_only",
                "caption_timing_source_policy": "asr_whisperx_timing_only",
                "caption_source_path": str(locked_script_path),
                "caption_text_source_path": str(locked_script_path),
                "caption_timing_source_path": str(timing_source_path),
                "caption_text_matches_script_read": "pass",
                "caption_asr_text_not_used_read": "pass",
                "caption_alignment_coverage_read": "pass",
                "burned_in_and_sidecar_same_script_locked_source_read": "pass",
            },
        }
        manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return manifest_path

    def _valid_probe(self) -> dict[str, object]:
        return {
            "video_codec": "h264",
            "audio_codec": "aac",
            "width": 576,
            "height": 1024,
            "duration_seconds": 62.041667,
            "frame_rate": "24/1",
            "audio_sample_rate_hz": 44100,
            "audio_channels": 1,
        }

    def _build_publish_ready_manifest(self, temp_root: Path) -> tuple[Context, dict[str, object]]:
        context = self._build_temp_context(temp_root)
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        manifest = copy.deepcopy(manifest)
        manifest["_manifest_path"] = str(temp_root / "episodes" / "challenger.toml")
        manifest["visual_research"]["status"] = "done"
        manifest["visual_research"]["approval"]["status"] = "approved"
        manifest["visual_research"]["approval"]["reviewer"] = "test"
        manifest["visual_research"]["approval"]["reviewed_at"] = "2026-03-29T00:00:00Z"
        manifest["visual_research"]["approval"]["notes"] = ""

        assets_root = temp_root / "artifacts"
        assets_root.mkdir(parents=True, exist_ok=True)
        audio_pipeline_dir = temp_root / "audio_pipeline"
        audio_master = assets_root / "episode.wav"
        audio_master.write_text("audio", encoding="utf-8")
        audio_transcript = assets_root / "episode.diarized.txt"
        audio_transcript.write_text("transcript", encoding="utf-8")
        self._write_audio_package_metadata(audio_pipeline_dir, packaged_path=audio_master, transcript_path=audio_transcript)

        manifest["audio"]["pipeline_dir"] = str(audio_pipeline_dir)
        manifest["audio"]["master_path"] = str(audio_master)
        manifest["audio"]["transcript_path"] = str(audio_transcript)
        manifest["audio"]["review"] = {
            "status": "approved",
            "reviewer": "test",
            "reviewed_at": "2026-03-29T00:05:00Z",
            "notes": "",
        }
        manifest["audio"]["status"] = "done"

        motion_source_ids = {
            str(item.get("source_still_id", "")).strip()
            for item in manifest["motion_assets"]["items"]
            if str(item.get("source_still_id", "")).strip()
        }
        for item in manifest["scene_stills"]["items"]:
            if not item.get("required", True):
                continue
            approved_path = assets_root / f"{item['id']}.png"
            approved_path.write_text(str(item["id"]), encoding="utf-8")
            item["output_path"] = str(approved_path)
            item["selected_asset"] = str(approved_path)
            item["review_status"] = "approved"
            item["reviewer"] = "test"
            item["reviewed_at"] = "2026-03-29T00:10:00Z"
            item["review_notes"] = ""
            if str(item["id"]) in motion_source_ids:
                item["motion_review_status"] = "approved_for_motion"
                item["motion_reviewer"] = "test"
                item["motion_reviewed_at"] = "2026-03-29T00:10:00Z"
                item["motion_review_notes"] = "Approved for motion."
        manifest["scene_stills"]["status"] = "done"

        for item in manifest["packaging_stills"]["items"]:
            approved_path = assets_root / f"{item['id']}.png"
            approved_path.write_text(str(item["id"]), encoding="utf-8")
            item["output_path"] = str(approved_path)
            item["selected_asset"] = str(approved_path)
            item["review_status"] = "approved"
            item["reviewer"] = "test"
            item["reviewed_at"] = "2026-03-29T00:15:00Z"
            item["review_notes"] = ""
        manifest["packaging_stills"]["status"] = "done"

        for item in manifest["motion_assets"]["items"]:
            item["behavior"] = str(item.get("behavior", "")).strip() or "Approved motion behavior."
            item["status"] = "done"
            item["review_outcome"] = "approved"
            item["reviewer"] = "test"
            item["reviewed_at"] = "2026-03-29T00:20:00Z"
            item["review_notes"] = ""
            motion_output = assets_root / f"{item['id']}.mp4"
            motion_output.write_text("motion", encoding="utf-8")
            item["latest_render_path"] = str(motion_output)
            item["output_path"] = str(motion_output)
        manifest["motion_assets"]["status"] = "done"

        assembly_output = assets_root / "episode.mp4"
        assembly_output.write_text("video", encoding="utf-8")
        manifest["assembly"]["status"] = "done"
        manifest["assembly"]["master_video_path"] = str(assembly_output)
        manifest["assembly"]["completed_at"] = "2026-03-29T00:30:00Z"

        manifest["web"]["status"] = "done"

        notes_path = temp_root / "publish_notes.md"
        notes_path.write_text(
            "# Challenger\n\n## Summary\nRelease copy.\n\n## Description\nPublic episode description.\n",
            encoding="utf-8",
        )
        manifest.setdefault("release", {})
        manifest["release"]["notes_path"] = str(notes_path)
        manifest["release"]["scheduled_for"] = ""
        manifest["release"]["published_at"] = ""
        manifest["release"]["status"] = "todo"
        manifest["release"].setdefault("youtube", {})
        manifest["release"].setdefault("podcast", {})
        manifest["release"]["youtube"]["description_path"] = str(notes_path)
        manifest["release"]["podcast"]["description_path"] = str(notes_path)
        manifest["release"]["podcast"]["audio_path"] = str(audio_master)
        manifest = materialize_episode_manifest(context, manifest)

        manifest_path = temp_root / "episodes" / "challenger.toml"
        write_episode_manifest(manifest_path, manifest)
        return context, load_episode_manifest(manifest_path)

    def test_build_publish_bundle_inherits_schedule_and_release_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context, manifest = self._build_publish_ready_manifest(temp_root)
            manifest["release"]["scheduled_for"] = "2026-04-02T16:00:00Z"
            bundle = build_publish_bundle(context, manifest)
            self.assertEqual(bundle["targets"]["youtube"]["scheduled_for"], "2026-04-02T16:00:00Z")
            self.assertEqual(bundle["targets"]["podcast"]["scheduled_for"], "2026-04-02T16:00:00Z")
            self.assertTrue(bundle["publish_notes_exists"])
            self.assertTrue(bundle["targets"]["youtube"]["thumbnail_item_id"])
            self.assertEqual(bundle["targets"]["podcast"]["audio_path"], manifest["audio"]["master_path"])

    def test_validate_publish_bundle_catches_missing_notes_and_release_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context, ready_manifest = self._build_publish_ready_manifest(temp_root)
            cases = [
                (
                    "missing_notes",
                    lambda payload: payload["release"].update({"notes_path": str(temp_root / "missing-notes.md")}),
                    "Release publish notes are missing",
                ),
                (
                    "thumbnail_not_approved",
                    lambda payload: payload["packaging_stills"]["items"][0].update({"review_status": "pending"}),
                    "YouTube publish requires an approved thumbnail asset.",
                ),
                (
                    "web_not_done",
                    lambda payload: payload["web"].update({"status": "todo"}),
                    "YouTube publish requires the web lane to be done.",
                ),
                (
                    "audio_stale",
                    lambda payload: (
                        payload["audio"]["review"].update({"freshness_override": ""}),
                        os.utime(payload["audio"]["master_path"], (0, 0)),
                        os.utime(payload["audio"]["transcript_path"], (0, 0)),
                    ),
                    "Podcast publish requires the approved audio package to be current.",
                ),
            ]
            for _name, mutate, expected in cases:
                with self.subTest(case=_name):
                    manifest = copy.deepcopy(ready_manifest)
                    mutate(manifest)
                    validation = validate_publish_bundle(context, manifest)
                    self.assertTrue(any(expected in issue for issue in validation["issues"]))

    def test_missing_publish_credentials_fail_fast(self) -> None:
        with self.assertRaises(PublishValidationError):
            build_youtube_publisher_from_env({})
        with self.assertRaises(PublishValidationError):
            build_buzzsprout_publisher_from_env({})

    def test_youtube_package_publisher_loads_local_oauth_config_without_repo_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            (config_dir / "oauth_client_secret.json").write_text(
                json.dumps({"installed": {"client_id": "local-client", "client_secret": "local-secret"}}),
                encoding="utf-8",
            )
            (config_dir / "access_token.json").write_text(
                json.dumps({"refresh_token": "local-refresh"}),
                encoding="utf-8",
            )
            (config_dir / "channel_id.txt").write_text("local-channel\n", encoding="utf-8")
            publisher = build_youtube_package_publisher(env={}, config_dir=config_dir)
        self.assertEqual(publisher.client_id, "local-client")
        self.assertEqual(publisher.refresh_token, "local-refresh")
        self.assertEqual(publisher.channel_id, "local-channel")

    def test_publish_package_check_accepts_valid_youtube_shorts_manifest_without_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = self._write_valid_publish_package(Path(temp_dir))
            with mock.patch("orchestration.publish._probe_video", return_value=self._valid_probe()):
                result = validate_publish_package_manifest(manifest_path)
            self.assertTrue(result["ok"])
            self.assertEqual(result["issues"], [])
            self.assertIn("check_upload_processing_before_public_release", result["warnings"])

    def test_publish_package_check_rejects_raw_asr_caption_word_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = self._write_valid_publish_package(Path(temp_dir))
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            raw_asr = manifest_path.parent / "episode.diarized.txt"
            raw_asr.write_text("misheard caption text\n", encoding="utf-8")
            payload["caption_context"]["caption_source_path"] = str(raw_asr)
            payload["caption_context"]["caption_text_source_path"] = str(raw_asr)
            manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            with mock.patch("orchestration.publish._probe_video", return_value=self._valid_probe()):
                result = validate_publish_package_manifest(manifest_path)
            self.assertFalse(result["ok"])
            self.assertTrue(any("ASR/WhisperX/diarized" in issue for issue in result["issues"]))

    def test_publish_package_check_rejects_missing_script_locked_caption_reads(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = self._write_valid_publish_package(Path(temp_dir))
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            payload["caption_context"].pop("caption_text_matches_script_read")
            payload["source_final"].pop("caption_text_matches_script_read")
            manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            with mock.patch("orchestration.publish._probe_video", return_value=self._valid_probe()):
                result = validate_publish_package_manifest(manifest_path)
            self.assertFalse(result["ok"])
            self.assertTrue(any("caption_text_matches_script_read" in issue for issue in result["issues"]))

    def test_publish_package_check_rejects_unwaived_silent_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = self._write_valid_publish_package(Path(temp_dir))
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            payload.pop("final_music_context")
            payload["rights_and_claims"] = {
                "claim_risk": "check_upload_processing_before_public_release",
                "music_bed_used": False,
            }
            manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            with mock.patch("orchestration.publish._probe_video", return_value=self._valid_probe()):
                result = validate_publish_package_manifest(manifest_path)
            self.assertFalse(result["ok"])
            self.assertTrue(any("music_policy: waived" in issue for issue in result["issues"]))
            self.assertTrue(any("music_waiver_reason" in issue for issue in result["issues"]))

    def test_publish_package_check_accepts_explicit_music_waiver(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = self._write_valid_publish_package(Path(temp_dir))
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            payload["final_music_context"] = {
                "music_policy": "waived",
                "music_waiver_reason": "approved silence for source-only memorial cut",
                "music_rights_check_status": "not_applicable",
            }
            payload["rights_and_claims"] = {
                "claim_risk": "check_upload_processing_before_public_release",
                "music_bed_used": False,
                "music_policy": "waived",
                "music_waiver_reason": "approved silence for source-only memorial cut",
            }
            manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            with mock.patch("orchestration.publish._probe_video", return_value=self._valid_probe()):
                result = validate_publish_package_manifest(manifest_path)
            self.assertTrue(result["ok"])
            self.assertEqual(result["issues"], [])

    def test_publish_package_check_accepts_legacy_music_complete_metadata_with_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = self._write_valid_publish_package(Path(temp_dir))
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            payload.pop("final_music_context")
            payload["rights_and_claims"] = {
                "claim_risk": "check_upload_processing_before_public_release",
                "music_bed_used": True,
            }
            manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            with mock.patch("orchestration.publish._probe_video", return_value=self._valid_probe()):
                result = validate_publish_package_manifest(manifest_path)
            self.assertTrue(result["ok"])
            self.assertTrue(any("missing `music_track_id`" in warning for warning in result["warnings"]))

    def test_publish_package_check_catches_missing_asset_hash_mismatch_and_invalid_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = self._write_valid_publish_package(Path(temp_dir))
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            Path(payload["upload_assets"]["caption_srt_path"]).unlink()
            payload["upload_assets"]["video_sha256"] = "not-the-real-sha"
            payload["target"] = "youtube"
            manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            with mock.patch("orchestration.publish._probe_video", return_value=self._valid_probe()):
                result = validate_publish_package_manifest(manifest_path)
            self.assertFalse(result["ok"])
            self.assertTrue(any("Unsupported publish package target" in issue for issue in result["issues"]))
            self.assertTrue(any("caption_srt_path" in issue and "does not exist" in issue for issue in result["issues"]))
            self.assertTrue(any("video_sha256" in issue and "mismatch" in issue for issue in result["issues"]))

    def test_publish_package_check_rejects_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "broken.json"
            manifest_path.write_text("{", encoding="utf-8")
            result = validate_publish_package_manifest(manifest_path)
            self.assertFalse(result["ok"])
            self.assertTrue(any("JSON is invalid" in issue for issue in result["issues"]))

    def test_publish_package_check_rejects_non_vertical_or_too_long_video(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = self._write_valid_publish_package(Path(temp_dir))
            probe = {**self._valid_probe(), "width": 1920, "height": 1080, "duration_seconds": 181.0}
            with mock.patch("orchestration.publish._probe_video", return_value=probe):
                result = validate_publish_package_manifest(manifest_path)
            self.assertFalse(result["ok"])
            self.assertTrue(any("must be vertical" in issue for issue in result["issues"]))
            self.assertTrue(any("duration must be at most" in issue for issue in result["issues"]))

    def test_build_youtube_shorts_publish_payload_uses_unlisted_review_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = self._write_valid_publish_package(Path(temp_dir))
            payload = build_youtube_shorts_publish_payload(manifest_path, privacy="unlisted")
            self.assertEqual(payload["privacy"], "unlisted")
            self.assertEqual(payload["category_id"], "27")
            self.assertFalse(payload["notify_subscribers"])
            self.assertTrue(payload["ignore_thumbnail_errors"])
            self.assertFalse(payload["self_declared_made_for_kids"])
            self.assertEqual(payload["tags"], ["tag one", "tag two"])
            self.assertTrue(str(payload["caption_srt_path"]).endswith("captions.srt"))

    def test_build_youtube_shorts_publish_payload_rejects_channel_title_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = self._write_valid_publish_package(Path(temp_dir))
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            payload["youtube_metadata"]["title"] = "Title | Cascade Effects"
            manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(PublishValidationError, "must not append"):
                build_youtube_shorts_publish_payload(manifest_path, privacy="unlisted")

    def test_publish_package_upload_writes_review_receipt_without_env_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = self._write_valid_publish_package(Path(temp_dir))
            publisher = StubPackageYouTubePublisher()
            with mock.patch("orchestration.publish._probe_video", return_value=self._valid_probe()):
                result = publish_package_upload(manifest_path, publisher=publisher)
            receipt_path = Path(result["receipt_path"])
            self.assertTrue(receipt_path.exists())
            self.assertTrue(receipt_path.name.startswith("youtube_review_upload_receipt_"))
            self.assertEqual(result["privacy"], "unlisted")
            self.assertEqual(result["video_id"], "yt-package-123")
            self.assertEqual(result["thumbnail_status"], "failed_nonfatal")
            self.assertEqual(publisher.publish_calls[0]["privacy"], "unlisted")
            self.assertTrue(publisher.publish_calls[0].get("embeddable", True))
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["receipt_type"], "youtube_review_upload")
            self.assertEqual(receipt["privacy"], "unlisted")
            self.assertEqual(receipt["youtube"]["video_id"], "yt-package-123")
            self.assertTrue(receipt["youtube"]["status"]["embeddable"])
            self.assertEqual(receipt["public_release"], "manual_youtube_studio_only")
            self.assertFalse(receipt["captions_uploaded"])
            self.assertIn("check_upload_processing_before_public_release", receipt["validation"]["warnings"])

    def test_publish_package_upload_rejects_non_unlisted_privacy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = self._write_valid_publish_package(Path(temp_dir))
            with mock.patch("orchestration.publish._probe_video", return_value=self._valid_probe()):
                for privacy in ("private", "public"):
                    with self.subTest(privacy=privacy):
                        with self.assertRaisesRegex(PublishValidationError, "--privacy unlisted"):
                            publish_package_upload(
                                manifest_path,
                                privacy=privacy,
                                publisher=StubPackageYouTubePublisher(),
                            )

    def test_publish_package_status_reads_upload_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = self._write_valid_publish_package(Path(temp_dir))
            publisher = StubPackageYouTubePublisher()
            with mock.patch("orchestration.publish._probe_video", return_value=self._valid_probe()):
                upload = publish_package_upload(manifest_path, publisher=publisher)
            status = publish_package_status(upload["receipt_path"], publisher=publisher)
            self.assertTrue(status["ok"])
            self.assertTrue(status["status"]["exists"])
            self.assertEqual(status["video_id"], "yt-package-123")
            self.assertEqual(status["status"]["privacy_status"], "unlisted")

    def test_publish_package_update_title_preserves_status_and_writes_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            receipt_path = Path(temp_dir) / "youtube_review_upload_receipt_20260429T000000Z.json"
            receipt_path.write_text(
                json.dumps(
                    {
                        "receipt_type": "youtube_review_upload",
                        "privacy": "unlisted",
                        "youtube": {"video_id": "yt-package-123"},
                    }
                ),
                encoding="utf-8",
            )
            publisher = StubPackageYouTubePublisher()
            result = publish_package_update_title(receipt_path, title="New Title", publisher=publisher)
            self.assertTrue(result["ok"])
            self.assertEqual(result["old_title"], "Title")
            self.assertEqual(result["new_title"], "New Title")
            self.assertEqual(result["privacy_status"], "unlisted")
            self.assertTrue(result["privacy_preserved"])
            self.assertEqual(publisher.title_update_calls, [("yt-package-123", "New Title")])
            update_receipt = json.loads(Path(result["receipt_path"]).read_text(encoding="utf-8"))
            self.assertEqual(update_receipt["receipt_type"], "youtube_title_update")
            self.assertEqual(update_receipt["verification"]["before"]["privacy_status"], "unlisted")
            self.assertEqual(update_receipt["verification"]["after"]["title"], "New Title")

    def test_publish_package_update_title_rejects_empty_title(self) -> None:
        with self.assertRaisesRegex(PublishValidationError, "non-empty title"):
            publish_package_update_title("yt-package-123", title="", publisher=StubPackageYouTubePublisher())

    def test_publish_package_update_title_rejects_channel_title_suffix(self) -> None:
        with self.assertRaisesRegex(PublishValidationError, "must not append"):
            publish_package_update_title(
                "yt-package-123",
                title="New Title | Cascade Effects",
                publisher=StubPackageYouTubePublisher(),
            )

    def test_publish_package_update_title_refuses_wrong_channel_video(self) -> None:
        publisher = StubPackageYouTubePublisher(channel_id="expected-channel", status_channel_id="other-channel")
        with self.assertRaisesRegex(PublishValidationError, "belongs to channel"):
            publish_package_update_title("yt-package-123", title="New Title", publisher=publisher)
        self.assertEqual(publisher.title_update_calls, [])

    def test_publish_package_status_reads_legacy_private_upload_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            receipt_path = Path(temp_dir) / "youtube_private_upload_receipt_20260429T000000Z.json"
            receipt_path.write_text(
                json.dumps(
                    {
                        "receipt_type": "youtube_private_upload",
                        "privacy": "private",
                        "youtube": {"video_id": "yt-package-123"},
                    }
                ),
                encoding="utf-8",
            )
            status = publish_package_status(receipt_path, publisher=StubPackageYouTubePublisher())
            self.assertTrue(status["ok"])
            self.assertEqual(status["video_id"], "yt-package-123")

    def test_publish_package_delete_reads_legacy_private_upload_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            receipt_path = Path(temp_dir) / "youtube_private_upload_receipt_20260429T000000Z.json"
            receipt_path.write_text(
                json.dumps(
                    {
                        "receipt_type": "youtube_private_upload",
                        "privacy": "private",
                        "youtube": {"video_id": "yt-package-123"},
                    }
                ),
                encoding="utf-8",
            )
            publisher = StubPackageYouTubePublisher()
            delete = publish_package_delete(receipt_path, confirm_video_id="yt-package-123", publisher=publisher)
            self.assertTrue(delete["deleted"])
            self.assertEqual(publisher.delete_calls, ["yt-package-123"])
            delete_receipt = json.loads(Path(delete["receipt_path"]).read_text(encoding="utf-8"))
            self.assertEqual(delete_receipt["source_receipt_path"], str(receipt_path))

    def test_publish_package_delete_requires_confirmation_and_writes_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = self._write_valid_publish_package(Path(temp_dir))
            publisher = StubPackageYouTubePublisher()
            with mock.patch("orchestration.publish._probe_video", return_value=self._valid_probe()):
                upload = publish_package_upload(manifest_path, publisher=publisher)
            with self.assertRaises(PublishValidationError):
                publish_package_delete(upload["receipt_path"], confirm_video_id="wrong-id", publisher=publisher)
            delete = publish_package_delete(upload["receipt_path"], confirm_video_id="yt-package-123", publisher=publisher)
            self.assertTrue(delete["deleted"])
            self.assertEqual(publisher.delete_calls, ["yt-package-123"])
            receipt_path = Path(delete["receipt_path"])
            self.assertTrue(receipt_path.exists())
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["confirmation_text"], "yt-package-123")
            self.assertFalse(receipt["verification"]["exists_after_delete"])

    def test_publish_package_cli_upload_status_delete_emit_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            context = self._build_temp_context(Path(temp_dir))
            upload_payload = {"ok": True, "receipt_path": "/tmp/receipt.json", "video_id": "yt-package-123"}
            status_payload = {"ok": True, "video_id": "yt-package-123", "status": {"exists": True}}
            update_title_payload = {"ok": True, "video_id": "yt-package-123", "new_title": "New Title"}
            delete_payload = {"ok": True, "video_id": "yt-package-123", "deleted": True}
            cases = [
                (
                    command_publish_package_upload,
                    argparse.Namespace(manifest_path="/tmp/manifest.json", privacy="unlisted"),
                    "orchestration.cli.publish_package_upload",
                    upload_payload,
                    "receipt_path",
                ),
                (
                    command_publish_package_status,
                    argparse.Namespace(receipt_or_video_id="/tmp/receipt.json"),
                    "orchestration.cli.publish_package_status",
                    status_payload,
                    "status",
                ),
                (
                    command_publish_package_update_title,
                    argparse.Namespace(receipt_or_video_id="/tmp/receipt.json", title="New Title"),
                    "orchestration.cli.publish_package_update_title",
                    update_title_payload,
                    "new_title",
                ),
                (
                    command_publish_package_delete,
                    argparse.Namespace(receipt_or_video_id="/tmp/receipt.json", confirm_video_id="yt-package-123"),
                    "orchestration.cli.publish_package_delete",
                    delete_payload,
                    "deleted",
                ),
            ]
            for command, args, patch_target, payload, expected_key in cases:
                with self.subTest(command=command.__name__):
                    buffer = io.StringIO()
                    with mock.patch(patch_target, return_value=payload):
                        with contextlib.redirect_stdout(buffer):
                            exit_code = command(context, args)
                    self.assertEqual(exit_code, 0)
                    result = json.loads(buffer.getvalue())
                    self.assertTrue(result["ok"])
                    self.assertIn(expected_key, result)

    def test_youtube_adapter_channel_status_and_delete_requests(self) -> None:
        requests: list[object] = []

        def opener(request: object) -> FakeHTTPResponse:
            requests.append(request)
            url = str(getattr(request, "full_url"))
            method = request.get_method()
            if "oauth2.googleapis.com/token" in url:
                return FakeHTTPResponse({"access_token": "access-token"})
            if "youtube/v3/channels" in url:
                return FakeHTTPResponse({"items": [{"id": "test-channel", "snippet": {"title": "Cascade Effects"}}]})
            if "youtube/v3/videos" in url and method == "GET":
                return FakeHTTPResponse(
                    {
                        "items": [
                            {
                                "id": "abc123",
                                "snippet": {
                                    "title": "Title",
                                    "channelId": "test-channel",
                                    "channelTitle": "Cascade Effects",
                                    "publishedAt": "2026-04-29T00:00:00Z",
                                },
                                "status": {"privacyStatus": "unlisted", "uploadStatus": "processed", "embeddable": True},
                                "processingDetails": {"processingStatus": "succeeded"},
                            }
                        ]
                    }
                )
            if "youtube/v3/videos" in url and method == "DELETE":
                return FakeHTTPResponse({})
            raise AssertionError(f"unexpected request: {method} {url}")

        publisher = YouTubePublisher(
            client_id="client",
            client_secret="secret",
            refresh_token="refresh",
            channel_id="test-channel",
            opener=opener,
        )
        channel = publisher.get_authenticated_channel()
        status = publisher.get_video_status("abc123")
        deleted = publisher.delete_video("abc123")
        self.assertEqual(channel["channel_id"], "test-channel")
        self.assertEqual(status.privacy_status, "unlisted")
        self.assertEqual(status.processing_status, "succeeded")
        self.assertTrue(status.embeddable)
        self.assertEqual(deleted.video_id, "abc123")
        request_urls = [str(getattr(request, "full_url")) for request in requests]
        self.assertTrue(any("mine=true" in url for url in request_urls))
        self.assertTrue(any("id=abc123" in url and "youtube/v3/videos" in url for url in request_urls))

    def test_youtube_adapter_update_title_preserves_mutable_snippet_fields(self) -> None:
        requests: list[object] = []

        def opener(request: object) -> FakeHTTPResponse:
            requests.append(request)
            url = str(getattr(request, "full_url"))
            method = request.get_method()
            if "oauth2.googleapis.com/token" in url:
                return FakeHTTPResponse({"access_token": "access-token"})
            if "youtube/v3/videos" in url and method == "GET":
                return FakeHTTPResponse(
                    {
                        "items": [
                            {
                                "id": "abc123",
                                "snippet": {
                                    "title": "Old Title",
                                    "description": "Description",
                                    "tags": ["tag one", "tag two"],
                                    "categoryId": "27",
                                    "defaultLanguage": "en",
                                    "defaultAudioLanguage": "en",
                                    "channelId": "test-channel",
                                    "channelTitle": "Cascade Effects",
                                },
                            }
                        ]
                    }
                )
            if "youtube/v3/videos" in url and method == "PUT":
                payload = json.loads(request.data.decode("utf-8"))
                self.assertEqual(payload["id"], "abc123")
                self.assertNotIn("status", payload)
                self.assertEqual(
                    payload["snippet"],
                    {
                        "title": "New Title",
                        "description": "Description",
                        "categoryId": "27",
                        "tags": ["tag one", "tag two"],
                        "defaultLanguage": "en",
                        "defaultAudioLanguage": "en",
                    },
                )
                return FakeHTTPResponse({"id": "abc123", "snippet": payload["snippet"]})
            raise AssertionError(f"unexpected request: {method} {url}")

        publisher = YouTubePublisher(
            client_id="client",
            client_secret="secret",
            refresh_token="refresh",
            channel_id="test-channel",
            opener=opener,
        )
        result = publisher.update_video_title("abc123", "New Title")
        self.assertEqual(result.old_title, "Old Title")
        self.assertEqual(result.new_title, "New Title")
        put_request = next(request for request in requests if request.get_method() == "PUT")
        self.assertIn("part=snippet", str(getattr(put_request, "full_url")))

    def test_youtube_adapter_thumbnail_failure_is_nonfatal_when_requested(self) -> None:
        requests: list[object] = []

        def opener(request: object) -> FakeHTTPResponse:
            requests.append(request)
            url = str(getattr(request, "full_url"))
            method = request.get_method()
            if "oauth2.googleapis.com/token" in url:
                return FakeHTTPResponse({"access_token": "access-token"})
            if "upload/youtube/v3/videos" in url and method == "POST":
                return FakeHTTPResponse({}, headers={"Location": "https://upload.example/session"})
            if url == "https://upload.example/session" and method == "PUT":
                return FakeHTTPResponse({"id": "abc123", "snippet": {"publishedAt": "2026-04-29T00:00:00Z"}})
            if "thumbnails/set" in url:
                raise urllib_error.HTTPError(url, 403, "Forbidden", hdrs={}, fp=io.BytesIO(b"thumbnail denied"))
            raise AssertionError(f"unexpected request: {method} {url}")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            video_path = temp_root / "short.mp4"
            thumbnail_path = temp_root / "cover.png"
            video_path.write_bytes(b"video")
            thumbnail_path.write_bytes(b"cover")
            publisher = YouTubePublisher(
                client_id="client",
                client_secret="secret",
                refresh_token="refresh",
                channel_id="test-channel",
                opener=opener,
            )
            result = publisher.publish_video(
                {
                    "video_path": str(video_path),
                    "thumbnail_path": str(thumbnail_path),
                    "title": "Title",
                    "description_text": "Description",
                    "tags": ["tag"],
                    "privacy": "unlisted",
                    "category_id": "27",
                    "self_declared_made_for_kids": False,
                    "notify_subscribers": False,
                    "ignore_thumbnail_errors": True,
                }
            )
        self.assertEqual(result.video_id, "abc123")
        self.assertEqual(result.thumbnail_status, "failed_nonfatal")
        metadata_request = requests[1]
        metadata = json.loads(metadata_request.data.decode("utf-8"))
        self.assertEqual(metadata["status"]["privacyStatus"], "unlisted")
        self.assertTrue(metadata["status"]["embeddable"])
        self.assertEqual(metadata["snippet"]["categoryId"], "27")
        self.assertIn("notifySubscribers=false", str(getattr(metadata_request, "full_url")))

    def test_publish_skill_and_templates_cover_unlisted_review_workflow(self) -> None:
        paths = [
            ROOT / "references/skills/youtube_shorts_publish_v1/SKILL.md",
            ROOT / "references/skills/youtube_shorts_production_v1/SKILL.md",
            ROOT / "references/skills/youtube_shorts_final_export_v1/SKILL.md",
            ROOT / "references/skills/youtube_shorts_final_export_v1/templates/final_export_review_template.md",
            ROOT / "references/skills/youtube_shorts_production_v1/templates/short_production_pilot_template.md",
        ]
        for path in paths:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertIn("publish-package-upload", text)
                self.assertIn("unlisted", text)
                self.assertIn("public release", text.lower())
        publish_skill = (ROOT / "references/skills/youtube_shorts_publish_v1/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("altered-content disclosure", publish_skill)
        self.assertIn("burned-in captions", publish_skill)
        self.assertIn("publish-package-delete", publish_skill)

    def test_legacy_publish_cli_commands_are_deprecated(self) -> None:
        commands = [
            ("publish-check", command_publish_check, argparse.Namespace(command="publish-check", episode_id="challenger")),
            ("publish-prepare", command_publish_prepare, argparse.Namespace(command="publish-prepare", episode_id="challenger")),
            ("publish", command_publish, argparse.Namespace(command="publish", episode_id="challenger", target="all", dry_run=True)),
            ("publish-status", command_publish_status, argparse.Namespace(command="publish-status", episode_id="challenger")),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            context = self._build_temp_context(Path(temp_dir))
            for name, command, args in commands:
                with self.subTest(command=name):
                    buffer = io.StringIO()
                    with contextlib.redirect_stdout(buffer):
                        exit_code = command(context, args)
                    payload = json.loads(buffer.getvalue())
                    self.assertEqual(exit_code, 1)
                    self.assertTrue(payload["deprecated"])
                    self.assertEqual(payload["replacement"], "publish-package-check <manifest_path>")

    def test_prepare_publish_writes_state_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context, manifest = self._build_publish_ready_manifest(temp_root)
            manifest["release"]["scheduled_for"] = "2026-04-03T12:00:00Z"
            prepared = prepare_publish(context, manifest)
            state_path = Path(prepared["state_path"])
            self.assertTrue(state_path.exists())
            publish_state = load_publish_state(context, "challenger")
            self.assertEqual(publish_state["release_scheduled_for"], "2026-04-03T12:00:00Z")
            self.assertIn("idempotency_key", publish_state["targets"]["youtube"])
            self.assertIn("idempotency_key", publish_state["targets"]["podcast"])

    def test_publish_episode_persists_partial_success_and_retry_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context, manifest = self._build_publish_ready_manifest(temp_root)
            youtube_first = StubYouTubePublisher(
                result=YouTubePublishResult(
                    video_id="yt-123",
                    video_url="https://www.youtube.com/watch?v=yt-123",
                    scheduled_for="",
                    published_at="2026-03-30T10:00:00Z",
                    raw_response={},
                )
            )
            podcast_first = StubBuzzsproutPublisher(error=RuntimeError("podcast upload failed"))

            first = publish_episode(
                context,
                manifest,
                youtube_publisher=youtube_first,
                buzzsprout_publisher=podcast_first,
            )
            self.assertEqual(first["results"]["youtube"]["status"], "published")
            self.assertEqual(first["results"]["podcast"]["status"], "failed")

            manifest_after_first = load_episode_manifest(Path(str(manifest["_manifest_path"])))
            materialized_first = materialize_episode_manifest(context, manifest_after_first)
            self.assertEqual(materialized_first["release"]["status"], "in_progress")
            self.assertEqual(materialized_first["release"]["published_at"], "")
            self.assertEqual(materialized_first["release"]["youtube"]["video_id"], "yt-123")
            self.assertEqual(materialized_first["release"]["podcast"]["status"], "failed")

            publish_state = load_publish_state(context, "challenger")
            self.assertEqual(publish_state["targets"]["youtube"]["video_id"], "yt-123")
            self.assertEqual(publish_state["targets"]["podcast"]["status"], "failed")

            youtube_retry = StubYouTubePublisher(
                result=YouTubePublishResult(
                    video_id="should-not-run",
                    video_url="https://www.youtube.com/watch?v=should-not-run",
                    scheduled_for="",
                    published_at="2026-03-30T10:05:00Z",
                    raw_response={},
                )
            )
            podcast_retry = StubBuzzsproutPublisher(
                result=BuzzsproutPublishResult(
                    external_id="bs-456",
                    episode_url="https://www.buzzsprout.com/12345/bs-456",
                    scheduled_for="",
                    published_at="2026-03-30T10:06:00Z",
                    raw_response={},
                )
            )
            second = publish_episode(
                context,
                manifest_after_first,
                youtube_publisher=youtube_retry,
                buzzsprout_publisher=podcast_retry,
            )
            self.assertTrue(second["results"]["youtube"]["skipped"])
            self.assertEqual(second["results"]["podcast"]["status"], "published")
            self.assertEqual(len(youtube_retry.publish_calls), 0)
            self.assertEqual(len(podcast_retry.publish_calls), 1)

            manifest_after_second = materialize_episode_manifest(
                context,
                load_episode_manifest(Path(str(manifest_after_first["_manifest_path"]))),
            )
            self.assertEqual(manifest_after_second["release"]["status"], "done")
            self.assertEqual(manifest_after_second["release"]["youtube"]["video_id"], "yt-123")
            self.assertEqual(manifest_after_second["release"]["podcast"]["external_id"], "bs-456")
            self.assertEqual(manifest_after_second["release"]["published_at"], "2026-03-30T10:06:00Z")

    def test_build_publish_status_reflects_manifest_and_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context, manifest = self._build_publish_ready_manifest(temp_root)
            prepare_publish(context, manifest)
            status = build_publish_status(context, manifest)
            self.assertEqual(status["episode_id"], "challenger")
            self.assertTrue(status["publish_state_exists"])
            self.assertIn("youtube", status["release"])
            self.assertIn("podcast", status["release"])
            self.assertIn("targets", status["publish_state"])

    def test_release_target_substate_preserves_release_classification_and_brief(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context, manifest = self._build_publish_ready_manifest(temp_root)

            scheduled_manifest = copy.deepcopy(manifest)
            scheduled_manifest["release"]["status"] = "done"
            scheduled_manifest["release"]["scheduled_for"] = "2026-04-04T12:00:00Z"
            scheduled_manifest["release"]["youtube"] = {
                **scheduled_manifest["release"].get("youtube", {}),
                "status": "scheduled",
                "scheduled_for": "2026-04-04T12:00:00Z",
                "video_id": "yt-scheduled",
            }
            scheduled_manifest["release"]["podcast"] = {
                **scheduled_manifest["release"].get("podcast", {}),
                "status": "scheduled",
                "scheduled_for": "2026-04-04T12:00:00Z",
                "external_id": "bs-scheduled",
            }
            scheduled_state = derive_episode_state(scheduled_manifest, context)
            self.assertEqual(scheduled_state["board_category"], "scheduled")

            published_manifest = copy.deepcopy(manifest)
            published_manifest["release"]["status"] = "done"
            published_manifest["release"]["published_at"] = "2026-04-04T13:00:00Z"
            published_manifest["release"]["youtube"] = {
                **published_manifest["release"].get("youtube", {}),
                "status": "published",
                "published_at": "2026-04-04T13:00:00Z",
                "video_id": "yt-published",
            }
            published_manifest["release"]["podcast"] = {
                **published_manifest["release"].get("podcast", {}),
                "status": "published",
                "published_at": "2026-04-04T13:00:00Z",
                "external_id": "bs-published",
            }
            published_state = derive_episode_state(published_manifest, context)
            self.assertEqual(published_state["board_category"], "published")

            brief = render_brief(context, manifest, "release")
            self.assertIn("publish-package-check", brief)
            self.assertIn("YouTube status", brief)
