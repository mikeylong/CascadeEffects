from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import os
import re
import subprocess
import tempfile
import threading
import unittest
from datetime import datetime, timezone
from pathlib import Path
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request
from unittest import mock

from orchestration.assembly import assemble_episode_cut, derive_act_spine, transition_for_boundary
from orchestration.contact_sheet import _fit_contain, build_contact_sheet_pages, render_contact_sheet_pdf
from orchestration.cli import (
    build_bootstrap_manifest,
    build_context,
    build_production_report,
    command_bootstrap,
    command_assemble,
    command_finalize_scene,
    command_promote_audio,
    command_process_research_sources,
    command_promote_scene,
    command_promote_motion,
    command_review_action,
    command_review_inbox,
    command_review_server,
    command_render_packaging,
    command_render_scene,
    command_render_motion,
    command_set_scene_archetype,
    derive_episode_state,
    load_episode_manifest,
    render_brief,
)
from orchestration.adapters import EpisodesRepo
from orchestration.io import Context, materialize_episode_manifest, write_episode_manifest
from orchestration.motion import validate_motion_duration
from orchestration.research_sources import load_source_inventory, write_source_inventory
from orchestration.review_brand import (
    CONSUMED_TOKEN_PATHS,
    load_signal_brand_theme,
    signal_style_system_path,
    signal_style_system_schema_path,
)
from orchestration.review import (
    build_review_inbox,
    build_review_message_detail,
    load_review_history,
    message_id_for,
    perform_review_action,
)
from orchestration.review_server import build_review_server, render_markdown_html, render_review_page
from orchestration.shorts_audio import (
    run_shorts_audio_audit,
    sha256_path,
    sync_shorts_audio_lane,
    write_historical_proof_annotations,
)
from orchestration.source_control import install_source_media_pre_commit_hooks, run_source_control_media_audit
from orchestration.stills import _opening_scene_render_overrides, render_scene_still


ROOT = Path("/Users/mike/Agents_CascadeEffects")
EPISODES_ROOT = Path("/Users/mike/Episodes_CascadeEffects")
TEST_ELEVENLABS_MODEL = "test_model_v2_hq"


def _lookup_token_path(node: dict[str, object], path: tuple[str, ...]) -> object:
    current: object = node
    for part in path:
        if not isinstance(current, dict):
            raise KeyError(".".join(path))
        current = current[part]
    return current


ALLOWED_FONT_SIZE_LITERALS = frozenset({"11px", "12px", "14px"})


def _font_size_literals(rendered: str) -> set[str]:
    pattern = re.compile(r"(?m)^\s*(?:--(?:font|type)[^:]*|font(?:-size)?)\s*:\s*([^;]+);")
    literals: set[str] = set()
    for value in pattern.findall(rendered):
        literals.update(re.findall(r"\d+(?:\.\d+)?(?:px|rem)", value))
    return literals


def _css_block(rendered: str, selector: str) -> str:
    anchor = f"{selector} {{"
    start = rendered.find(anchor)
    if start == -1:
        raise AssertionError(f"Missing CSS block for {selector}")
    start += len(anchor)
    end = rendered.find("\n    }", start)
    if end == -1:
        raise AssertionError(f"Unterminated CSS block for {selector}")
    return rendered[start:end]


class OrchestrationTests(unittest.TestCase):
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

    def _clone_context_with_web_root(self, web_root: Path) -> Context:
        channel = copy.deepcopy(self.context.channel)
        channel["paths"] = copy.deepcopy(channel["paths"])
        channel["paths"]["web_root"] = str(web_root)
        return Context(
            root=self.context.root,
            channel=channel,
            web_entry_ids=self.context.web_entry_ids,
            asset_archetypes=self.context.asset_archetypes,
            episodes_repo=self.context.episodes_repo,
            audio_repo=self.context.audio_repo,
            viz_repo=self.context.viz_repo,
            web_repo=self.context.web_repo,
        )

    def _build_temp_bootstrap_context(self, temp_root: Path, episodes_root: Path, web_root: Path) -> Context:
        agents_root = temp_root / "agents"
        (agents_root / "episodes").mkdir(parents=True, exist_ok=True)
        (agents_root / "state").mkdir(parents=True, exist_ok=True)
        helper = agents_root / "bin" / "ce-orchestrate"
        helper.parent.mkdir(parents=True, exist_ok=True)
        helper.write_text("#!/bin/sh\n", encoding="utf-8")
        channel = copy.deepcopy(self.context.channel)
        channel["paths"] = copy.deepcopy(channel["paths"])
        channel["paths"]["agents_root"] = str(agents_root)
        channel["paths"]["episodes_root"] = str(episodes_root)
        channel["paths"]["orchestrate_helper"] = str(helper)
        channel["paths"]["web_root"] = str(web_root)
        return Context(
            root=agents_root,
            channel=channel,
            web_entry_ids=self.context.web_entry_ids,
            asset_archetypes=self.context.asset_archetypes,
            episodes_repo=EpisodesRepo(episodes_root),
            audio_repo=self.context.audio_repo,
            viz_repo=self.context.viz_repo,
            web_repo=self.context.web_repo,
        )

    def _write_temp_episode_dir(self, episodes_root: Path) -> Path:
        episode_dir = episodes_root / "Ep99_Test-Episode"
        episode_dir.mkdir(parents=True, exist_ok=True)
        (episode_dir / "Ep99_Test-Episode.txt").write_text("Test episode script.\n", encoding="utf-8")
        return episode_dir

    def _write_manifest_copy(self, temp_root: Path, episode_id: str, manifest: dict[str, object] | None = None) -> Path:
        manifest_path = temp_root / "episodes" / f"{episode_id}.toml"
        if manifest is None:
            manifest_path.write_text((ROOT / "episodes" / f"{episode_id}.toml").read_text(encoding="utf-8"), encoding="utf-8")
        else:
            write_episode_manifest(manifest_path, manifest)
        return manifest_path

    def _write_audio_package_metadata(
        self,
        pipeline_dir: Path,
        *,
        packaged_path: Path,
        transcript_path: Path | None = None,
        provider: str = "elevenlabs",
        voice: str = "voice_test_123",
        model: str = TEST_ELEVENLABS_MODEL,
        source_manifest_path: Path | None = None,
    ) -> Path:
        pipeline_dir.mkdir(parents=True, exist_ok=True)
        metadata_path = pipeline_dir / "audio_package.json"
        transcript = transcript_path or packaged_path.with_suffix(".diarized.txt")
        if not transcript.exists():
            transcript.write_text("transcript", encoding="utf-8")
        source_manifest = source_manifest_path or (pipeline_dir / "effective_final_jobs.elevenlabs.jsonl")
        if not source_manifest.exists():
            source_manifest.write_text("{}\n", encoding="utf-8")
        payload = {
            "provider": provider,
            "voice": voice,
            "model": model,
            "effective_manifest_path": str(source_manifest),
            "packaged_path": str(packaged_path),
            "packaged_sha256": "packaged-sha",
            "packaged_at": "2026-03-30T18:00:00Z",
            "transcript_path": str(transcript),
            "transcript_sha256": "transcript-sha",
            "qa_completed_at": "2026-03-30T18:05:00Z",
        }
        metadata_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return metadata_path

    def _prepare_visual_research_fixture(self, manifest: dict[str, object], temp_root: Path) -> dict[str, object]:
        visual_research = manifest["visual_research"]
        fixture_root = temp_root / "visual_research"
        asset_root = fixture_root / "research_assets"
        fixture_root.mkdir(parents=True, exist_ok=True)
        asset_root.mkdir(parents=True, exist_ok=True)

        for field, filename in (
            ("contact_sheet_path", "contact_sheet.pdf"),
            ("act_breakdown_path", "act_breakdown.md"),
            ("reference_notes_path", "reference_notes.md"),
            ("sources_path", "sources.md"),
            ("assembly_notes_path", "assembly_notes.md"),
        ):
            path = fixture_root / filename
            path.write_text(f"{field}\n", encoding="utf-8")
            visual_research[field] = str(path)

        script_path = Path(str(manifest.get("script", {}).get("path", ""))).expanduser()
        if script_path.exists():
            visual_research["script_sha256"] = sha256_path(script_path)

        sources: list[dict[str, object]] = []
        opening_sequence = visual_research.get("opening_sequence", {})
        slots = list(opening_sequence.get("slots", [])) if isinstance(opening_sequence, dict) else []

        def add_source(slot: dict[str, object], suffix: str = "primary") -> None:
            slot_id = str(slot.get("slot_id", "")).strip()
            role = str(slot.get("role", "")).strip()
            label = str(slot.get("display_label", "")).strip() or slot_id
            if not slot_id:
                return
            source_id = f"opening_{slot_id}_{suffix}"
            raw_asset_path = asset_root / f"{source_id}.png"
            board_asset_path = asset_root / f"{source_id}_board.png"
            raw_asset_path.write_text(source_id, encoding="utf-8")
            board_asset_path.write_text(f"{source_id} board", encoding="utf-8")
            sources.append(
                {
                    "source_id": source_id,
                    "coverage_id": "opening",
                    "opening_slot_id": slot_id,
                    "candidate_label": label,
                    "candidate_role": "opening_subject" if role == "subject_object" else "opening_supporting",
                    "source_url": f"https://example.test/{source_id}.png",
                    "source_origin": "web_fresh",
                    "raw_asset_path": str(raw_asset_path),
                    "board_asset_path": str(board_asset_path),
                    "approved_for_generation": True,
                    "text_status": "clear",
                    "downstream_asset_path": str(raw_asset_path),
                    "notes": "Isolated test fixture asset.",
                }
            )

        for slot in slots:
            if isinstance(slot, dict):
                add_source(slot)
        for slot in slots:
            if isinstance(slot, dict) and str(slot.get("role", "")).strip() == "subject_object":
                add_source(slot, "secondary")
                break

        for act in visual_research.get("acts", []):
            if not isinstance(act, dict):
                continue
            act_id = str(act.get("id", "")).strip()
            if not act_id:
                continue
            for index in range(1, 9):
                source_id = f"{act_id}_reference_{index:02d}"
                raw_asset_path = asset_root / f"{source_id}.png"
                board_asset_path = asset_root / f"{source_id}_board.png"
                raw_asset_path.write_text(source_id, encoding="utf-8")
                board_asset_path.write_text(f"{source_id} board", encoding="utf-8")
                sources.append(
                    {
                        "source_id": source_id,
                        "act_id": act_id,
                        "coverage_id": act_id,
                        "candidate_label": f"{act_id} reference {index:02d}",
                        "candidate_role": "act_reference",
                        "source_url": f"https://example.test/{source_id}.png",
                        "source_origin": "web_fresh",
                        "raw_asset_path": str(raw_asset_path),
                        "board_asset_path": str(board_asset_path),
                        "approved_for_generation": True,
                        "text_status": "clear",
                        "downstream_asset_path": str(raw_asset_path),
                        "notes": "Isolated test fixture asset.",
                    }
                )

        inventory_path = fixture_root / "source_inventory.json"
        write_source_inventory(inventory_path, {"schema_version": 2, "sources": sources})
        visual_research["source_inventory_path"] = str(inventory_path)
        return manifest

    def _build_short_audio_audit_context(self, temp_root: Path, *, package_model: str = "eleven_multilingual_v2") -> Context:
        agents_root = temp_root / "agents"
        audio_root = temp_root / "audio"
        viz_root = temp_root / "viz"
        episodes_root = temp_root / "episodes"
        for path in (agents_root, audio_root, viz_root, episodes_root):
            path.mkdir(parents=True, exist_ok=True)
        channel = copy.deepcopy(self.context.channel)
        channel["paths"] = copy.deepcopy(channel["paths"])
        channel["paths"]["agents_root"] = str(agents_root)
        channel["paths"]["audio_root"] = str(audio_root)
        channel["paths"]["viz_root"] = str(viz_root)
        channel["paths"]["episodes_root"] = str(episodes_root)

        profiles_path = audio_root / "references" / "voice_profiles" / "youtube_shorts_voice_profiles.json"
        profiles_path.parent.mkdir(parents=True, exist_ok=True)
        profiles_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "profiles": {
                        "youtube_shorts_mike_challenger_match_v1": {
                            "provider": "elevenlabs",
                            "voice": "dPrTCMw2R7HQlznlgwCO",
                            "model": "eleven_multilingual_v2",
                            "final_export_eligible": True,
                            "allowed_lane_types": ["active_short"],
                            "render_settings": {"speed": 0.95},
                        }
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        package_dir = audio_root / "tmp" / "ep1_short"
        package_dir.mkdir(parents=True, exist_ok=True)
        audio_path = episodes_root / "Ep1_Challenger" / "shorts" / "challenger_short_v1" / "final" / "challenger_short_v1.wav"
        transcript_path = package_dir / "transcripts_mastered" / "challenger_short_v1.diarized.txt"
        effective_path = package_dir / "effective_final_jobs.elevenlabs.jsonl"
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        transcript_path.parent.mkdir(parents=True, exist_ok=True)
        audio_path.write_text("audio", encoding="utf-8")
        transcript_path.write_text("transcript", encoding="utf-8")
        effective_path.write_text(
            json.dumps({"elevenlabs_model_id": package_model, "elevenlabs_voice_settings": {"speed": 0.95}}) + "\n",
            encoding="utf-8",
        )
        package_path = package_dir / "audio_package.json"
        package_path.write_text(
            json.dumps(
                {
                    "provider": "elevenlabs",
                    "voice": "dPrTCMw2R7HQlznlgwCO",
                    "model": package_model,
                    "effective_manifest_path": str(effective_path),
                    "packaged_path": str(audio_path),
                    "packaged_sha256": sha256_path(audio_path),
                    "transcript_path": str(transcript_path),
                    "transcript_sha256": sha256_path(transcript_path),
                    "qa_completed_at": "2026-01-01T00:00:00Z",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        short_manifest_path = viz_root / "references" / "episodes" / "challenger" / "shorts" / "challenger_short_minimal_surreal_v1.json"
        registry_path = agents_root / "references" / "shorts" / "audio_lane_registry.json"
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "voice_profiles_path": str(profiles_path),
                    "lanes": [
                        {
                            "episode_id": "challenger",
                            "lane_id": "challenger_short_v1",
                            "lane_type": "active_short",
                            "status": "active",
                            "short_id": "challenger_short_minimal_surreal_v1",
                            "short_audio_package_path": str(package_path),
                            "expected_voice_profile_id": "youtube_shorts_mike_challenger_match_v1",
                            "audio_disposition": "keep",
                            "final_export_eligible": True,
                            "audio_package_sha256": sha256_path(package_path),
                            "packaged_audio_sha256": sha256_path(audio_path),
                            "transcript_sha256": sha256_path(transcript_path),
                            "active_manifest_paths": [str(short_manifest_path)],
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        short_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        short_manifest_path.write_text(
            json.dumps(
                {
                    "short_id": "challenger_short_minimal_surreal_v1",
                    "episode_id": "challenger",
                    "audio_path": str(audio_path),
                    "transcript_path": str(transcript_path),
                    "short_audio_package_path": str(package_path),
                    "expected_voice_profile_id": "youtube_shorts_mike_challenger_match_v1",
                    "audio_package_sha256": sha256_path(package_path),
                    "packaged_audio_sha256": sha256_path(audio_path),
                    "audio_disposition": "keep",
                    "caption_source_path": str(transcript_path),
                    "transcript_sha256": sha256_path(transcript_path),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return Context(
            root=agents_root,
            channel=channel,
            web_entry_ids=self.context.web_entry_ids,
            asset_archetypes=self.context.asset_archetypes,
            episodes_repo=self.context.episodes_repo,
            audio_repo=self.context.audio_repo,
            viz_repo=self.context.viz_repo,
            web_repo=self.context.web_repo,
        )

    def test_shorts_audio_audit_accepts_valid_active_lane(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-shorts-audio-audit-") as temp_dir:
            context = self._build_short_audio_audit_context(Path(temp_dir))
            report = run_shorts_audio_audit(context)
        self.assertTrue(report["ok"])
        self.assertEqual(report["error_count"], 0)

    def test_shorts_music_track_registry_defines_paper_architecture_default(self) -> None:
        registry_path = ROOT / "references" / "shorts" / "music_track_registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))

        self.assertEqual(registry["schema_version"], "1.0")
        self.assertEqual(registry["default_active_shorts_music_track_id"], "paper_architecture_theme_v1")
        self.assertEqual(registry["rules"]["active_shorts_default_music_policy"], "canonical_default")
        self.assertEqual(registry["rules"]["music_stage"], "video final")
        self.assertTrue(registry["rules"]["apply_after_voice_and_caption_timing_locked"])

        track = registry["tracks"]["paper_architecture_theme_v1"]
        self.assertEqual(track["status"], "active_default")
        self.assertEqual(track["name"], "Paper Architecture")
        self.assertEqual(track["usage"], "canonical_default_for_active_youtube_shorts")
        self.assertEqual(track["mix_profile"]["outro_completion_policy"], "extend_final_to_complete_outro")
        self.assertGreaterEqual(track["mix_profile"]["max_extended_final_frame_hold_seconds"], 4.0)

        for asset_key in ("body_loop", "outro"):
            asset = track[asset_key]
            asset_path = Path(asset["path"])
            self.assertTrue(asset_path.exists(), f"Missing {asset_key}: {asset_path}")
            self.assertEqual(sha256_path(asset_path), asset["sha256"])

        rights = track["rights_and_claims"]
        self.assertTrue(rights["rights_check_required_before_public_release"])
        self.assertEqual(rights["claim_handling"], "warning_not_hard_failure")

    def test_shorts_music_policy_fields_are_present_in_templates(self) -> None:
        required_fields = (
            "music_track_registry_path",
            "music_track_id",
            "music_policy",
            "music_waiver_reason",
            "music_rights_check_status",
            "body_loop_sha256",
            "outro_sha256",
        )
        template_paths = [
            ROOT / "references" / "skills" / "youtube_shorts_final_export_v1" / "templates" / "final_export_request_template.md",
            ROOT / "references" / "skills" / "youtube_shorts_final_export_v1" / "templates" / "final_export_review_template.md",
            ROOT / "references" / "skills" / "youtube_shorts_production_v1" / "templates" / "short_video_stage_review_template.md",
            ROOT / "references" / "skills" / "youtube_shorts_production_v1" / "templates" / "short_production_pilot_template.md",
        ]

        for template_path in template_paths:
            template = template_path.read_text(encoding="utf-8")
            for field in required_fields:
                self.assertIn(f"`{field}`", template, f"{field} missing from {template_path}")

    def test_shorts_music_default_policy_is_codified_in_skill_docs(self) -> None:
        doc_paths = [
            ROOT / "references" / "skills" / "youtube_shorts_production_v1" / "SKILL.md",
            ROOT / "references" / "skills" / "youtube_shorts_production_v1" / "references" / "stage_gate_policy.md",
            ROOT / "references" / "skills" / "youtube_shorts_production_v1" / "references" / "caption_and_final_export_policy.md",
            ROOT / "references" / "skills" / "youtube_shorts_final_export_v1" / "SKILL.md",
        ]

        for doc_path in doc_paths:
            doc = doc_path.read_text(encoding="utf-8")
            self.assertIn("paper_architecture_theme_v1", doc, f"default track missing from {doc_path}")
            self.assertIn("music_policy", doc, f"music policy missing from {doc_path}")

    def _build_source_control_media_audit_context(self, temp_root: Path) -> Context:
        agents_root = temp_root / "agents"
        audio_root = temp_root / "audio"
        viz_root = temp_root / "viz"
        episodes_root = temp_root / "episodes"
        for path in (agents_root, audio_root, viz_root, episodes_root):
            path.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "-C", str(path), "init", "--quiet"], check=True)
        channel = copy.deepcopy(self.context.channel)
        channel["paths"] = copy.deepcopy(channel["paths"])
        channel["paths"]["agents_root"] = str(agents_root)
        channel["paths"]["audio_root"] = str(audio_root)
        channel["paths"]["viz_root"] = str(viz_root)
        channel["paths"]["episodes_root"] = str(episodes_root)
        return Context(
            root=agents_root,
            channel=channel,
            web_entry_ids=self.context.web_entry_ids,
            asset_archetypes=self.context.asset_archetypes,
            episodes_repo=self.context.episodes_repo,
            audio_repo=self.context.audio_repo,
            viz_repo=self.context.viz_repo,
            web_repo=self.context.web_repo,
        )

    def test_source_control_media_audit_accepts_contract_files(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-source-media-audit-ok-") as temp_dir:
            context = self._build_source_control_media_audit_context(Path(temp_dir))
            readme = Path(context.channel["paths"]["viz_root"]) / "README.md"
            readme.write_text("contract\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(readme.parent), "add", "README.md"], check=True)

            report = run_source_control_media_audit(context)

        self.assertTrue(report["ok"])
        self.assertEqual(report["error_count"], 0)

    def test_source_control_media_audit_rejects_tracked_media(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-source-media-audit-media-") as temp_dir:
            context = self._build_source_control_media_audit_context(Path(temp_dir))
            media = Path(context.channel["paths"]["viz_root"]) / "reference.png"
            media.write_bytes(b"png")
            subprocess.run(["git", "-C", str(media.parent), "add", "reference.png"], check=True)

            report = run_source_control_media_audit(context)

        self.assertFalse(report["ok"])
        self.assertEqual(report["error_count"], 1)
        self.assertEqual(report["errors"][0]["code"], "tracked_banned_media_or_model_asset")

    def test_source_control_media_audit_rejects_tracked_media_sidecar(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-source-media-audit-sidecar-") as temp_dir:
            context = self._build_source_control_media_audit_context(Path(temp_dir))
            sidecar = Path(context.channel["paths"]["viz_root"]) / "review_approved.png.json"
            sidecar.write_text('{"final_outputs": []}\n', encoding="utf-8")
            subprocess.run(["git", "-C", str(sidecar.parent), "add", sidecar.name], check=True)

            report = run_source_control_media_audit(context)

        self.assertFalse(report["ok"])
        self.assertEqual(report["error_count"], 1)
        self.assertEqual(report["errors"][0]["code"], "tracked_generated_media_sidecar")

    def test_source_media_hook_installer_writes_pre_commit_hooks(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-source-media-hooks-") as temp_dir:
            context = self._build_source_control_media_audit_context(Path(temp_dir))

            result = install_source_media_pre_commit_hooks(context)

            self.assertEqual(result["installed_count"], 4)
            for repo in result["repositories"]:
                hook_path = Path(str(repo["hook_path"]))
                self.assertTrue(hook_path.exists())
                self.assertTrue(os.access(hook_path, os.X_OK))
                self.assertIn("source-media-audit", hook_path.read_text(encoding="utf-8"))

    def test_source_media_hook_installer_preserves_existing_pre_commit_hook(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-source-media-hooks-chain-") as temp_dir:
            context = self._build_source_control_media_audit_context(Path(temp_dir))
            agents_root = Path(context.channel["paths"]["agents_root"])
            hook_path = agents_root / ".git" / "hooks" / "pre-commit"
            hook_path.write_text("#!/bin/sh\necho previous\n", encoding="utf-8")
            hook_path.chmod(0o755)

            result = install_source_media_pre_commit_hooks(context)

            agents_result = next(repo for repo in result["repositories"] if repo["name"] == "agents")
            previous_hook_path = Path(str(agents_result["previous_hook_path"]))
            self.assertTrue(agents_result["previous_hook_preserved"])
            self.assertTrue(previous_hook_path.exists())
            self.assertEqual(previous_hook_path.read_text(encoding="utf-8"), "#!/bin/sh\necho previous\n")
            self.assertIn(str(previous_hook_path), hook_path.read_text(encoding="utf-8"))

    def test_shorts_audio_audit_rejects_same_voice_wrong_model(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-shorts-audio-audit-wrong-model-") as temp_dir:
            context = self._build_short_audio_audit_context(Path(temp_dir), package_model="eleven_v3")
            report = run_shorts_audio_audit(context)
        self.assertFalse(report["ok"])
        self.assertTrue(any(issue["code"] == "model_mismatch" for issue in report["errors"]))

    def test_sync_shorts_audio_lane_updates_registry_and_active_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-shorts-audio-sync-") as temp_dir:
            context = self._build_short_audio_audit_context(Path(temp_dir))
            registry_path = context.root / "references" / "shorts" / "audio_lane_registry.json"
            package_path = (
                Path(context.channel["paths"]["audio_root"])
                / "tmp"
                / "ep1_short"
                / "audio_package.json"
            )
            package_payload = json.loads(package_path.read_text(encoding="utf-8"))
            package_payload["voice_profile_id"] = "youtube_shorts_mike_challenger_match_v1"
            package_payload["voice_profile_settings"] = {"speed": 0.95}
            package_payload["render_settings"] = {
                "provider": "elevenlabs",
                "voice": "dPrTCMw2R7HQlznlgwCO",
                "model": "eleven_multilingual_v2",
                "speed": 0.95,
            }
            package_path.write_text(json.dumps(package_payload, indent=2) + "\n", encoding="utf-8")

            result = sync_shorts_audio_lane(context, "challenger_short_v1")
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            lane = registry["lanes"][0]
            short_manifest_path = Path(lane["active_manifest_paths"][0])
            short_manifest = json.loads(short_manifest_path.read_text(encoding="utf-8"))
            package_sha = sha256_path(package_path)

            self.assertEqual(result["updated_manifest_count"], 1)
            self.assertEqual(lane["audio_package_sha256"], package_sha)
            self.assertEqual(lane["expected_voice_profile_id"], "youtube_shorts_mike_challenger_match_v1")
            self.assertEqual(short_manifest["audio_package_sha256"], package_sha)
            self.assertEqual(Path(short_manifest["caption_source_path"]).resolve(), Path(package_payload["transcript_path"]).resolve())

            report = run_shorts_audio_audit(context)
        self.assertTrue(report["ok"])

    def test_historical_proof_annotations_suppress_old_provenance_warnings(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-shorts-audio-annotations-") as temp_dir:
            context = self._build_short_audio_audit_context(Path(temp_dir))
            short_manifest = json.loads(
                (
                    Path(context.channel["paths"]["viz_root"])
                    / "references"
                    / "episodes"
                    / "challenger"
                    / "shorts"
                    / "challenger_short_minimal_surreal_v1.json"
                ).read_text(encoding="utf-8")
            )
            proof_dir = (
                Path(context.channel["paths"]["viz_root"])
                / "workflows"
                / "generated"
                / "shorts"
                / "challenger_short_minimal_surreal_v1"
                / "20260101T000000Z"
            )
            proof_dir.mkdir(parents=True, exist_ok=True)
            proof_path = proof_dir / "20260101T000000Z__proof.json"
            proof_path.write_text(
                json.dumps(
                    {
                        "short_id": "challenger_short_minimal_surreal_v1",
                        "episode_id": "challenger",
                        "audio_path": short_manifest["audio_path"],
                        "transcript_path": short_manifest["transcript_path"],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            unannotated = run_shorts_audio_audit(context, use_historical_annotations=False)
            self.assertEqual(unannotated["warning_count"], 1)

            annotation_result = write_historical_proof_annotations(context)
            self.assertEqual(annotation_result["annotation_count"], 1)
            self.assertEqual(annotation_result["unresolved_count"], 0)
            annotated = run_shorts_audio_audit(context)

        self.assertEqual(annotated["warning_count"], 0)
        self.assertEqual(annotated["historical_suppressed_warning_count"], 1)

    def _build_ready_for_assembly_manifest(self, temp_root: Path | None = None) -> dict[str, object]:
        temp_root = temp_root or Path(tempfile.mkdtemp(prefix="ce-test-ready-for-assembly-"))
        temp_root.mkdir(parents=True, exist_ok=True)
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        manifest["visual_research"]["status"] = "done"
        manifest["visual_research"]["approval"]["status"] = "approved"
        manifest["visual_research"]["approval"]["reviewer"] = "test"
        manifest["visual_research"]["approval"]["reviewed_at"] = "2026-03-29T00:00:00Z"
        manifest["visual_research"]["approval"]["notes"] = ""
        audio_pipeline_dir = temp_root / "audio_pipeline"
        audio_pipeline_dir.mkdir(parents=True, exist_ok=True)
        audio_master = temp_root / "episode.wav"
        audio_master.write_text("audio", encoding="utf-8")
        audio_transcript = temp_root / "episode.txt"
        audio_transcript.write_text(
            (
                "[00:00:00.000–00:00:02.000] SPEAKER_00: By January 1986, every piece of evidence already existed.\n"
                "[00:00:02.001–00:00:05.103] SPEAKER_00: And it starts with a promise.\n"
                "[00:00:05.104–00:00:08.500] SPEAKER_00: The space shuttle was supposed to change what space travel meant.\n"
            ),
            encoding="utf-8",
        )
        manifest["audio"]["pipeline_dir"] = str(audio_pipeline_dir)
        manifest["audio"]["master_path"] = str(audio_master)
        manifest["audio"]["transcript_path"] = str(audio_transcript)
        manifest["audio"]["review"] = {
            "status": "approved",
            "reviewer": "test",
            "reviewed_at": "2026-03-29T00:05:00Z",
            "notes": "",
            "freshness_override": "waived",
        }
        manifest["audio"]["status"] = "done"
        self._prepare_visual_research_fixture(manifest, temp_root)
        manifest = materialize_episode_manifest(self.context, manifest)
        for item in manifest["scene_stills"]["items"]:
            if not item.get("required", True):
                continue
            approved_path = temp_root / f"{item['id']}.png"
            approved_manifest = temp_root / f"{item['id']}.run.json"
            approved_path.write_text(item["id"], encoding="utf-8")
            approved_manifest.write_text("{}", encoding="utf-8")
            item["output_path"] = str(approved_path)
            item["latest_render_path"] = str(approved_path)
            item["latest_render_manifest_path"] = str(approved_manifest)
            item["selected_asset"] = str(approved_path)
            item["review_status"] = "approved"
            item["reviewer"] = "test"
            item["reviewed_at"] = "2026-03-29T00:10:00Z"
            item["review_notes"] = ""
            if str(item["id"]) in {"opening_culture_cluster", "launch_commit_console"}:
                item["motion_review_status"] = "approved_for_motion"
                item["motion_reviewer"] = "test"
                item["motion_reviewed_at"] = "2026-03-29T00:10:00Z"
                item["motion_review_notes"] = "Approved for the opening focus beat: Challenger takes focus and commits to liftoff."
        manifest["scene_stills"]["status"] = "done"
        for item in manifest["packaging_stills"]["items"]:
            approved_path = temp_root / f"{item['id']}.png"
            approved_manifest = temp_root / f"{item['id']}.run.json"
            approved_path.write_text(item["id"], encoding="utf-8")
            approved_manifest.write_text("{}", encoding="utf-8")
            item["output_path"] = str(approved_path)
            item["latest_render_path"] = str(approved_path)
            item["latest_render_manifest_path"] = str(approved_manifest)
            item["selected_asset"] = str(approved_path)
            item["review_status"] = "approved"
            item["reviewer"] = "test"
            item["reviewed_at"] = "2026-03-29T00:15:00Z"
            item["review_notes"] = ""
        manifest["packaging_stills"]["status"] = "done"
        for motion_item in manifest["motion_assets"]["items"]:
            motion_item["behavior"] = motion_item.get("behavior") or "Other period objects clear from frame as Challenger takes focus and blasts off."
            motion_item["status"] = "done"
            motion_item["review_outcome"] = "approved"
            motion_item["reviewer"] = "mike"
            motion_item["reviewed_at"] = motion_item.get("reviewed_at") or "2026-03-29T23:39:50Z"
            motion_item["review_notes"] = ""
            motion_output = temp_root / f"{motion_item['id']}.mp4"
            motion_output.write_text("motion", encoding="utf-8")
            motion_item["latest_render_path"] = str(motion_output)
            motion_item["output_path"] = str(motion_output)
        manifest["motion_assets"]["status"] = "done"
        manifest["_manifest_path"] = str(temp_root / "challenger.toml")
        return manifest

    def _write_ready_for_assembly_manifest(self, temp_root: Path) -> tuple[Path, dict[str, object]]:
        manifest = self._build_ready_for_assembly_manifest(temp_root)
        manifest_path = temp_root / "challenger.toml"
        write_episode_manifest(manifest_path, manifest)
        return manifest_path, load_episode_manifest(manifest_path)

    def _write_svg_fixture(self, path: Path, *, top_color: str = "#cc0000", bottom_color: str = "#0033cc") -> Path:
        path.write_text(
            (
                '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="80">'
                f'<rect width="40" height="40" fill="{top_color}"/>'
                f'<rect y="40" width="40" height="40" fill="{bottom_color}"/>'
                "</svg>"
            ),
            encoding="utf-8",
        )
        return path

    def test_machine_assemblable_episode_is_ready_for_assembly(self) -> None:
        manifest = self._build_ready_for_assembly_manifest()
        state = derive_episode_state(manifest, self.context)
        self.assertEqual(state["errors"], [])
        self.assertEqual(state["board_category"], "ready_for_assembly")
        self.assertEqual(state["next_action"]["lane"], "assembly")

    def test_materialized_manifest_backfills_reject_tags_and_guardrails(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        manifest["visual_research"]["status"] = "review"
        manifest["visual_research"]["approval"] = {
            "status": "rejected",
            "reviewer": "mike",
            "reviewed_at": "2026-03-30T00:22:42Z",
            "notes": "I can't approve this until i see a contact sheet",
        }
        scene_item = next(item for item in manifest["scene_stills"]["items"] if item["id"] == "routine_console_wide")
        scene_item["review_status"] = "rejected"
        scene_item["review_notes"] = (
            "Readable text and numeric artifacts remain in frame (NASA, 45, paperwork/UI fragments), "
            "and the image drifts into collage-board signage instead of a clean mission-control wide."
        )
        packaging_item = next(item for item in manifest["packaging_stills"]["items"] if item["id"] == "launch_thumbnail")
        packaging_item["review_status"] = "rejected"
        packaging_item["review_notes"] = "too much typography with gibberish - not a recognizable object"
        packaging_item["review_tags"] = []

        materialized = materialize_episode_manifest(self.context, manifest)

        self.assertEqual(materialized["visual_research"]["approval"]["tags"], ["missing_contact_sheet"])
        scene_after = next(item for item in materialized["scene_stills"]["items"] if item["id"] == "routine_console_wide")
        self.assertEqual(scene_after["review_tags"], ["text_artifacts"])
        packaging_after = next(item for item in materialized["packaging_stills"]["items"] if item["id"] == "launch_thumbnail")
        self.assertEqual(packaging_after["review_tags"], ["unrecognizable_anchor", "text_artifacts"])
        self.assertIn("missing_contact_sheet", materialized["visual_research"]["guardrails"]["latest_reject_tags"])
        self.assertIn("text_artifacts", materialized["visual_research"]["guardrails"]["latest_reject_tags"])

        state = derive_episode_state(materialized, self.context)
        self.assertIn("missing_contact_sheet", state["lanes"]["visual_research"]["guardrails"]["machine_enforced_reject_tags"])
        self.assertIn("Space Shuttle Challenger", state["lanes"]["visual_research"]["guardrails"]["signal_object"])

    def test_validate_motion_duration_rejects_short_motion_manifest(self) -> None:
        with self.assertRaises(SystemExit) as exc:
            validate_motion_duration(
                Path("/tmp/console_alarm_push.mp4"),
                {"duration_seconds": 0.375},
                min_duration_seconds=5.0,
                motion_item_id="console_alarm_push",
            )
        self.assertIn("too short", str(exc.exception))

    def test_challenger_is_blocked_without_full_act_coverage(self) -> None:
        manifest = self._build_ready_for_assembly_manifest()
        manifest["visual_research"]["acts"][0]["planned_scene_ids"] = []
        state = derive_episode_state(manifest, self.context)
        self.assertEqual(state["board_category"], "in_production")
        self.assertEqual(state["next_action"]["lane"], "assembly")
        self.assertTrue(any("every act" in issue["message"] for issue in state["errors"]))

    def test_assembly_done_requires_master_video_path(self) -> None:
        manifest = self._build_ready_for_assembly_manifest()
        manifest["assembly"]["status"] = "done"
        manifest["assembly"]["master_video_path"] = ""
        state = derive_episode_state(manifest, self.context)
        self.assertTrue(any("master_video_path" in issue["message"] for issue in state["errors"]))

    def test_derive_act_spine_respects_motion_then_scene_order(self) -> None:
        manifest = self._build_ready_for_assembly_manifest()
        manifest["visual_research"]["acts"][2]["planned_motion_ids"] = ["launch_commit_dolly"]
        manifest["visual_research"]["acts"][2]["planned_scene_ids"] = ["launch_commit_console", "launch_commit_console"]
        plan = derive_act_spine(self.context, manifest)
        act3 = next(act for act in plan.acts if act.act_id == "act3")
        self.assertEqual([source.asset_id for source in act3.sources], ["launch_commit_dolly", "launch_commit_console", "launch_commit_console"])
        self.assertEqual(act3.sources[0].kind, "motion")

    def test_transition_override_only_applies_to_declared_boundary(self) -> None:
        manifest = self._build_ready_for_assembly_manifest()
        manifest["assembly"]["transitions"] = [
            {
                "from_act": "act1",
                "to_act": "act2",
                "video": "xfade",
                "audio": "acrossfade",
                "duration_seconds": 0.75,
            }
        ]
        declared = transition_for_boundary(manifest, "act1", "act2")
        defaulted = transition_for_boundary(manifest, "act2", "act3")
        self.assertEqual(declared.video, "xfade")
        self.assertEqual(declared.audio, "acrossfade")
        self.assertEqual(declared.duration_seconds, 0.75)
        self.assertEqual(defaulted.video, "cut")
        self.assertEqual(defaulted.audio, "cut")

    def test_write_episode_manifest_round_trips_assembly_compositions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest_path = temp_root / "challenger.toml"
            manifest = self._build_ready_for_assembly_manifest(temp_root)
            manifest["assembly"]["compositions"] = [
                {
                    "act_id": "act3",
                    "base_asset_id": "launch_commit_console",
                    "overlays": [
                        {
                            "motion_asset_id": "launch_commit_dolly",
                            "start_seconds": 0.5,
                            "duration_seconds": 2.5,
                            "x": 1440.0,
                            "y": 320.0,
                            "scale": 0.75,
                            "opacity": 0.8,
                            "blend_mode": "normal",
                        }
                    ],
                }
            ]
            write_episode_manifest(manifest_path, manifest)

            updated = materialize_episode_manifest(self.context, load_episode_manifest(manifest_path))

            self.assertEqual(
                updated["assembly"]["compositions"],
                [
                    {
                        "act_id": "act3",
                        "base_asset_id": "launch_commit_console",
                        "overlays": [
                            {
                                "motion_asset_id": "launch_commit_dolly",
                                "start_seconds": 0.5,
                                "duration_seconds": 2.5,
                                "x": 1440.0,
                                "y": 320.0,
                                "scale": 0.75,
                                "opacity": 0.8,
                                "blend_mode": "normal",
                                "hold_last_frame": False,
                            }
                        ],
                    }
                ],
            )

    def test_assemble_episode_cut_composes_base_clip_with_overlay_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest = self._build_ready_for_assembly_manifest(temp_root)
            manifest["assembly"]["compositions"] = [
                {
                    "act_id": "act3",
                    "base_asset_id": "launch_commit_console",
                    "overlays": [
                        {
                            "motion_asset_id": "launch_commit_dolly",
                            "start_seconds": 0.5,
                            "duration_seconds": 2.0,
                            "scale": 0.9,
                            "opacity": 0.7,
                            "blend_mode": "normal",
                        }
                    ],
                }
            ]
            manifest = materialize_episode_manifest(self.context, manifest)
            recorded_commands: list[list[str]] = []

            def fake_run(args: list[str]) -> str:
                recorded_commands.append(args)
                output_path = Path(args[-1])
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text("video", encoding="utf-8")
                return ""

            with (
                mock.patch("orchestration.assembly._run_checked_command", side_effect=fake_run),
                mock.patch("orchestration.assembly.probe_media_duration_seconds", return_value=5.0),
            ):
                output_path = assemble_episode_cut(self.context, manifest)

            self.assertTrue(output_path.exists())
            filter_command = next(args for args in recorded_commands if "-filter_complex" in args and "overlay=" in args[args.index("-filter_complex") + 1])
            filter_text = filter_command[filter_command.index("-filter_complex") + 1]
            self.assertIn("enable='between(t,0.500,2.500)'", filter_text)
            self.assertIn("[1:v]setpts=PTS+0.500000/TB[ov1pts]", filter_text)
            self.assertIn("colorchannelmixer=aa=0.700000", filter_text)
            self.assertIn("overlay=x=(main_w-overlay_w)/2:y=(main_h-overlay_h)/2", filter_text)
            mux_command = recorded_commands[-1]
            self.assertEqual(mux_command[mux_command.index("-map") + 1], "0:v:0")
            self.assertIn("[a]", mux_command)

    def test_assemble_episode_cut_uses_declared_overlay_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest = self._build_ready_for_assembly_manifest(temp_root)
            extra_overlay = next(item for item in manifest["motion_assets"]["items"] if item["id"] == "opening_subject_pull_in")
            extra_path = temp_root / "opening_subject_pull_in.mov"
            extra_path.write_text("video", encoding="utf-8")
            extra_overlay["output_path"] = str(extra_path)
            manifest["assembly"]["compositions"] = [
                {
                    "act_id": "act3",
                    "base_asset_id": "launch_commit_console",
                    "overlays": [
                        {
                            "motion_asset_id": "opening_subject_pull_in",
                            "start_seconds": 0.25,
                            "duration_seconds": 1.5,
                            "x": 80.0,
                            "y": 90.0,
                            "scale": 0.5,
                            "opacity": 1.0,
                            "blend_mode": "normal",
                        },
                        {
                            "motion_asset_id": "launch_commit_dolly",
                            "start_seconds": 1.0,
                            "duration_seconds": 2.0,
                            "x": 900.0,
                            "y": 120.0,
                            "scale": 0.75,
                            "opacity": 1.0,
                            "blend_mode": "normal",
                        },
                    ],
                }
            ]
            manifest = materialize_episode_manifest(self.context, manifest)
            recorded_commands: list[list[str]] = []

            def fake_run(args: list[str]) -> str:
                recorded_commands.append(args)
                output_path = Path(args[-1])
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text("video", encoding="utf-8")
                return ""

            with (
                mock.patch("orchestration.assembly._run_checked_command", side_effect=fake_run),
                mock.patch("orchestration.assembly.probe_media_duration_seconds", return_value=5.0),
            ):
                assemble_episode_cut(self.context, manifest)

            filter_command = next(args for args in recorded_commands if "-filter_complex" in args and "overlay=" in args[args.index("-filter_complex") + 1])
            filter_text = filter_command[filter_command.index("-filter_complex") + 1]
            self.assertLess(filter_text.index("between(t,0.250,1.750)"), filter_text.index("between(t,1.000,3.000)"))

    def test_assembly_overlay_requires_existing_output(self) -> None:
        manifest = self._build_ready_for_assembly_manifest()
        next(item for item in manifest["motion_assets"]["items"] if item["id"] == "launch_commit_dolly")["output_path"] = "/tmp/missing-overlay.mov"
        manifest["assembly"]["compositions"] = [
            {
                "act_id": "act3",
                "base_asset_id": "launch_commit_console",
                "overlays": [
                    {
                        "motion_asset_id": "launch_commit_dolly",
                        "start_seconds": 0.0,
                        "duration_seconds": 1.0,
                        "blend_mode": "normal",
                    }
                ],
            }
        ]

        with self.assertRaises(SystemExit) as exc:
            derive_act_spine(self.context, materialize_episode_manifest(self.context, manifest))

        self.assertIn("missing its output file", str(exc.exception))

    def test_assembly_overlay_rejects_unsupported_blend_mode(self) -> None:
        manifest = self._build_ready_for_assembly_manifest()
        manifest["assembly"]["compositions"] = [
            {
                "act_id": "act3",
                "base_asset_id": "launch_commit_console",
                "overlays": [
                    {
                        "motion_asset_id": "launch_commit_dolly",
                        "start_seconds": 0.0,
                        "duration_seconds": 1.0,
                        "blend_mode": "screen",
                    }
                ],
            }
        ]

        with self.assertRaises(SystemExit) as exc:
            derive_act_spine(self.context, materialize_episode_manifest(self.context, manifest))

        self.assertIn("unsupported blend_mode", str(exc.exception))

    def test_assembly_overlay_timing_must_fit_inside_base_shot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest = self._build_ready_for_assembly_manifest(temp_root)
            manifest["assembly"]["compositions"] = [
                {
                    "act_id": "act3",
                    "base_asset_id": "launch_commit_console",
                    "overlays": [
                        {
                            "motion_asset_id": "launch_commit_dolly",
                            "start_seconds": 99.0,
                            "duration_seconds": 1.0,
                            "blend_mode": "normal",
                        }
                    ],
                }
            ]
            manifest = materialize_episode_manifest(self.context, manifest)

            def fake_run(args: list[str]) -> str:
                output_path = Path(args[-1])
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text("video", encoding="utf-8")
                return ""

            with (
                mock.patch("orchestration.assembly._run_checked_command", side_effect=fake_run),
                mock.patch("orchestration.assembly.probe_media_duration_seconds", return_value=5.0),
                self.assertRaises(SystemExit) as exc,
            ):
                assemble_episode_cut(self.context, manifest)

            self.assertIn("exceeds the shot duration", str(exc.exception))

    def test_optional_scene_still_can_remain_incomplete(self) -> None:
        manifest = self._build_ready_for_assembly_manifest()
        state = derive_episode_state(manifest, self.context)
        self.assertTrue(any(not item.get("required", True) for item in manifest["scene_stills"]["items"]))
        self.assertEqual(state["errors"], [])

    def test_audio_is_next_when_visual_package_is_ready(self) -> None:
        manifest = self._build_ready_for_assembly_manifest()
        manifest["audio"]["status"] = "todo"
        manifest["audio"]["review"]["status"] = "pending"
        manifest["audio"]["transcript_path"] = ""
        state = derive_episode_state(manifest, self.context)
        self.assertEqual(state["errors"], [])
        self.assertEqual(state["board_category"], "in_production")
        self.assertEqual(state["next_action"]["lane"], "audio")

    def test_done_audio_without_research_anchor_is_marked_provisional(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            episode_dir = temp_root / "episodes_repo" / "Ep1_Challenger"
            visual_research_dir = episode_dir / "visual_research"
            visual_research_dir.mkdir(parents=True, exist_ok=True)
            script_path = episode_dir / "Ep1_Challenger.txt"
            script_path.write_text("test script", encoding="utf-8")
            context = Context(
                root=context.root,
                channel=context.channel,
                web_entry_ids=context.web_entry_ids,
                asset_archetypes=context.asset_archetypes,
                episodes_repo=self.context.episodes_repo.__class__(episode_dir.parent),
                audio_repo=context.audio_repo,
                viz_repo=context.viz_repo,
                web_repo=context.web_repo,
            )
            manifest = self._build_ready_for_assembly_manifest(temp_root)
            manifest["script"]["path"] = str(script_path)
            manifest["visual_research"]["approval"]["status"] = "pending"
            manifest["visual_research"]["approval"]["reviewed_at"] = ""
            state = derive_episode_state(manifest, context)
        self.assertEqual(state["lanes"]["audio"]["freshness"], "provisional")
        self.assertTrue(any("treat it as provisional" in issue["message"] for issue in state["pending"]))

    def test_audio_stale_after_research_approval_blocks_on_audio(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = self._build_ready_for_assembly_manifest(Path(temp_dir))
            manifest["audio"]["review"]["freshness_override"] = ""
            manifest["visual_research"]["approval"]["reviewed_at"] = "2100-01-01T00:00:00Z"
            state = derive_episode_state(manifest, self.context)
        self.assertEqual(state["lanes"]["audio"]["freshness"], "stale")
        self.assertEqual(state["next_action"]["lane"], "audio")
        self.assertTrue(any("predates the latest fact-check or approved visual research" in issue["message"] for issue in state["errors"]))

    def test_audio_freshness_waiver_keeps_approved_audio_current(self) -> None:
        manifest = self._build_ready_for_assembly_manifest()
        manifest["visual_research"]["approval"]["reviewed_at"] = "2100-01-01T00:00:00Z"
        state = derive_episode_state(manifest, self.context)
        self.assertEqual(state["lanes"]["audio"]["freshness"], "current")
        self.assertTrue(state["lanes"]["audio"]["freshness_override_applied"])
        self.assertNotEqual(state["next_action"]["lane"], "audio")

    def test_audio_freshness_waiver_is_ignored_without_approved_review(self) -> None:
        manifest = self._build_ready_for_assembly_manifest()
        manifest["audio"]["review"]["status"] = "pending"
        manifest["audio"]["status"] = "review"
        manifest["visual_research"]["approval"]["reviewed_at"] = "2100-01-01T00:00:00Z"
        state = derive_episode_state(manifest, self.context)
        self.assertEqual(state["lanes"]["audio"]["freshness"], "stale")
        self.assertFalse(state["lanes"]["audio"]["freshness_override_applied"])

    def test_motion_requires_motion_approved_still(self) -> None:
        manifest = self._build_ready_for_assembly_manifest()
        broken = copy.deepcopy(manifest)
        next(item for item in broken["scene_stills"]["items"] if item["id"] == "launch_commit_console")["motion_review_status"] = "pending"
        broken["motion_assets"]["status"] = "review"
        broken["motion_assets"]["items"][0]["status"] = "review"
        state = derive_episode_state(broken, self.context)
        self.assertTrue(any("not approved for motion" in issue["message"] for issue in state["errors"]))

    def test_motion_active_accepts_approved_proof_without_selected_asset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest = self._build_ready_for_assembly_manifest(temp_root)
            source_still = next(item for item in manifest["scene_stills"]["items"] if item["id"] == "launch_commit_console")
            approved_proof = temp_root / "review_approved.png"
            approved_proof.write_text("proof", encoding="utf-8")
            approved_proof_manifest = Path(f"{approved_proof}.json")
            approved_proof_manifest.write_text("{}", encoding="utf-8")
            source_still["approved_proof_path"] = str(approved_proof)
            source_still["approved_proof_manifest_path"] = str(approved_proof_manifest)
            source_still["selected_asset"] = ""
            manifest["scene_stills"]["status"] = "in_progress"

            state = derive_episode_state(manifest, self.context)

            self.assertFalse(
                any("launch_commit_console" in issue["message"] and "not approved for motion" in issue["message"] for issue in state["errors"])
            )
            self.assertFalse(
                any("Motion assets require at least one still approved for motion." in issue["message"] for issue in state["errors"])
            )

    def test_motion_item_behavior_is_required_once_visual_research_is_active(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        broken = copy.deepcopy(manifest)
        next(item for item in broken["motion_assets"]["items"] if item["id"] == "launch_commit_dolly")["behavior"] = ""
        state = derive_episode_state(broken, self.context)
        self.assertTrue(any("missing `behavior`" in issue["message"] for issue in state["errors"]))

    def test_workbench_motion_requires_existing_project(self) -> None:
        manifest = self._build_ready_for_assembly_manifest()
        broken = copy.deepcopy(manifest)
        motion_item = next(item for item in broken["motion_assets"]["items"] if item["id"] == "launch_commit_dolly")
        motion_item["authoring_mode"] = "particle_workbench"
        motion_item["workbench_project_path"] = "/tmp/missing-workbench-project.json"

        state = derive_episode_state(broken, self.context)

        self.assertTrue(any("workbench project is missing" in issue["message"].lower() for issue in state["errors"]))

    def test_scene_motion_approval_requires_behavior_notes(self) -> None:
        manifest = self._build_ready_for_assembly_manifest()
        broken = copy.deepcopy(manifest)
        next(item for item in broken["scene_stills"]["items"] if item["id"] == "launch_commit_console")["motion_review_notes"] = ""
        state = derive_episode_state(broken, self.context)
        self.assertTrue(any("missing motion_review_notes describing the approved behavior" in issue["message"] for issue in state["errors"]))

    def test_bootstrapped_hyatt_points_to_visual_research_without_errors(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/hyatt-regency.toml")
        state = derive_episode_state(manifest, self.context)
        self.assertEqual(state["errors"], [])
        self.assertEqual(state["board_category"], "in_production")
        self.assertEqual(state["next_action"]["lane"], "visual_research")
        self.assertEqual(state["lanes"]["scene_stills"]["unresolved_archetype_count"], 1)

    def test_downstream_pending_is_gated_until_lane_is_eligible(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/hyatt-regency.toml")
        manifest["visual_research"]["status"] = "todo"
        state = derive_episode_state(manifest, self.context)
        self.assertEqual([item["lane"] for item in state["pending"]], ["audio"])
        self.assertIn("treat it as provisional", state["pending"][0]["message"])

    def test_audio_and_motion_can_remain_pending_together(self) -> None:
        manifest = self._build_ready_for_assembly_manifest()
        manifest["audio"]["status"] = "todo"
        manifest["audio"]["review"]["status"] = "pending"
        manifest["audio"]["transcript_path"] = "/tmp/missing-audio-transcript.txt"
        manifest["motion_assets"]["status"] = "todo"
        manifest["motion_assets"]["items"][0]["status"] = "todo"
        manifest["motion_assets"]["items"][0]["output_path"] = "/tmp/missing-assembly-motion.mp4"
        state = derive_episode_state(manifest, self.context)
        pending_messages = [issue["message"] for issue in state["pending"]]
        self.assertTrue(any("audio" in message.lower() for message in pending_messages))
        self.assertTrue(any("motion item" in message.lower() for message in pending_messages))
        self.assertFalse(any("scene still" in message.lower() for message in pending_messages))

    def test_piltdown_web_entry_is_allowed_while_web_lane_is_todo(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/piltdown-man.toml")
        state = derive_episode_state(manifest, self.context)
        self.assertEqual(state["errors"], [])
        self.assertEqual(state["next_action"]["lane"], "visual_research")

    def test_report_surfaces_unresolved_scene_archetypes_and_packaging_demand(self) -> None:
        report = build_production_report(self.context)
        unresolved_episode_ids = {item["episode_id"] for item in report["unresolved_scene_archetypes"]}
        self.assertTrue({"737-max", "hyatt-regency", "tacoma-narrows", "piltdown-man"}.issubset(unresolved_episode_ids))
        self.assertIn("thumbnail", report["packaging_demand"])
        self.assertIn("shorts_cover", report["packaging_demand"])
        self.assertGreaterEqual(report["packaging_stills_coverage"]["required_pending_render_count"], 1)
        self.assertGreaterEqual(report["motion_demand"]["required_pending_count"], 1)
        self.assertIn("hyatt-regency", report["motion_blocked_on_source_still_approval"]["episodes"])
        self.assertIsInstance(report["motion_ready_episodes"], list)
        self.assertIn("cycle_time_summary", report)
        self.assertIn("throughput_summary", report)
        self.assertIn("slate_forecast", report)
        self.assertEqual(report["cycle_time_summary"]["p50_cycle_days"]["status"], "insufficient_sample")
        self.assertEqual(report["slate_forecast"]["target_episode_count"], 186)

    def test_report_motion_blockage_accepts_approved_proof_without_selected_asset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = self._build_ready_for_assembly_manifest(temp_root)
            source_still = next(item for item in manifest["scene_stills"]["items"] if item["id"] == "launch_commit_console")
            approved_proof = temp_root / "review_approved.png"
            approved_proof.write_text("proof", encoding="utf-8")
            approved_proof_manifest = Path(f"{approved_proof}.json")
            approved_proof_manifest.write_text("{}", encoding="utf-8")
            source_still["approved_proof_path"] = str(approved_proof)
            source_still["approved_proof_manifest_path"] = str(approved_proof_manifest)
            source_still["selected_asset"] = ""
            manifest["motion_assets"]["status"] = "todo"
            manifest["motion_assets"]["items"][0]["status"] = "todo"
            manifest["motion_assets"]["items"][0]["latest_render_path"] = ""
            manifest["motion_assets"]["items"][0]["latest_render_manifest_path"] = ""
            self._write_manifest_copy(temp_root, "challenger", manifest)

            report = build_production_report(context)

            self.assertEqual(report["motion_blocked_on_source_still_approval"]["required_pending_count"], 0)
            self.assertEqual(report["motion_blocked_on_source_still_approval"]["episodes"], [])
            self.assertIn("challenger", report["motion_ready_episodes"])

    def test_legacy_manifest_backfills_bootstrapped_at_from_manifest_mtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(ROOT / "episodes/hyatt-regency.toml")
            manifest.pop("tracking", None)
            manifest_path = temp_root / "episodes" / "hyatt-regency.toml"
            write_episode_manifest(manifest_path, manifest)
            expected_bootstrap = "2026-02-01T12:00:00Z"
            timestamp = datetime(2026, 2, 1, 12, 0, tzinfo=timezone.utc).timestamp()
            os.utime(manifest_path, (timestamp, timestamp))
            state = derive_episode_state(load_episode_manifest(manifest_path), context)
            milestone = state["cycle_time"]["milestones"]["bootstrapped_at"]
            self.assertEqual(milestone["timestamp"], expected_bootstrap)
            self.assertEqual(milestone["source"], "manifest_mtime")
            self.assertEqual(milestone["confidence"], "backfilled")

    def test_report_calculates_cycle_and_throughput_from_posted_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            fixtures = [
                ("challenger", "2026-03-01T00:00:00Z", "2026-03-05T00:00:00Z"),
                ("hyatt-regency", "2026-03-07T00:00:00Z", "2026-03-12T00:00:00Z"),
                ("semmelweis", "2026-03-13T00:00:00Z", "2026-03-19T00:00:00Z"),
                ("tacoma-narrows", "2026-03-19T00:00:00Z", "2026-03-26T00:00:00Z"),
                ("therac-25", "2026-03-25T00:00:00Z", "2026-04-02T00:00:00Z"),
            ]
            for episode_id, bootstrapped_at, published_at in fixtures:
                manifest = load_episode_manifest(ROOT / "episodes" / f"{episode_id}.toml")
                manifest.setdefault("tracking", {})["bootstrapped_at"] = bootstrapped_at
                manifest["release"]["status"] = "done"
                manifest["release"]["published_at"] = published_at
                self._write_manifest_copy(temp_root, episode_id, manifest)
            report = build_production_report(context)
            self.assertEqual(report["cycle_time_summary"]["completed_sample_count"], 5)
            self.assertEqual(report["cycle_time_summary"]["p50_cycle_days"]["status"], "ok")
            self.assertEqual(report["cycle_time_summary"]["p50_cycle_days"]["value"], 6.0)
            self.assertEqual(report["cycle_time_summary"]["p90_cycle_days"]["status"], "ok")
            self.assertEqual(report["cycle_time_summary"]["p90_cycle_days"]["value"], 8.0)
            self.assertEqual(report["throughput_summary"]["episodes_per_week"]["status"], "ok")
            self.assertEqual(report["throughput_summary"]["episodes_per_week"]["value"], 1.0)
            self.assertEqual(report["throughput_summary"]["median_days_between_posts"]["value"], 7.0)
            self.assertEqual(report["slate_forecast"]["status"], "forecasted")
            self.assertEqual(report["slate_forecast"]["posted_count"], 5)
            self.assertEqual(report["slate_forecast"]["remaining_count"], 181)

    def test_load_signal_brand_theme_uses_canonical_web_tokens(self) -> None:
        theme = load_signal_brand_theme(self.context)
        self.assertEqual(theme.warning, "")
        self.assertEqual(theme.source_path, str(signal_style_system_path(self.context)))
        self.assertEqual(theme.css_variables["--paper"], "#0B1023")
        self.assertEqual(theme.css_variables["--text-primary"], "#0B1023")
        self.assertEqual(theme.css_variables["--signal"], "#78DCE8")
        self.assertEqual(theme.css_variables["--alert"], "#FF6F61")
        self.assertEqual(theme.css_variables["--type-heading-size"], "14px")
        self.assertEqual(theme.css_variables["--type-body-size"], "12px")
        self.assertEqual(theme.css_variables["--type-overline-size"], "11px")
        self.assertEqual(theme.css_variables["--font-display"], "14px")
        self.assertEqual(theme.css_variables["--font-body"], "12px")
        self.assertEqual(theme.css_variables["--font-caption"], "11px")
        self.assertEqual(theme.dark_css_variables["--paper"], "#11172F")
        self.assertEqual(theme.dark_css_variables["--text-primary"], "#FFF8E8")
        self.assertEqual(theme.dark_css_variables["--type-heading-size"], "14px")
        self.assertEqual(theme.dark_css_variables["--type-body-size"], "12px")
        self.assertEqual(theme.dark_css_variables["--type-overline-size"], "11px")
        self.assertEqual(theme.dark_css_variables["--line"], "rgba(255, 255, 255, 0.12)")
        self.assertIn('"Inter"', theme.css_variables["--font-display-family"])
        self.assertEqual(theme.css_variables["--dur-base"], "220ms")

    def test_review_brand_consumed_tokens_exist_in_canonical_and_schema_files(self) -> None:
        canonical = json.loads(signal_style_system_path(self.context).read_text(encoding="utf-8"))
        schema = json.loads(signal_style_system_schema_path(self.context).read_text(encoding="utf-8"))
        schema_properties = schema.get("properties", {})
        schema_required = set(schema.get("required", []))
        for token_path in CONSUMED_TOKEN_PATHS:
            with self.subTest(token_path=".".join(token_path)):
                self.assertIsNotNone(_lookup_token_path(canonical, token_path))
                self.assertIn(token_path[0], schema_properties)
                self.assertIn(token_path[0], schema_required)

    def test_review_page_renders_token_driven_css_variables(self) -> None:
        theme = load_signal_brand_theme(self.context)
        page = render_review_page(title="Review Inbox", theme=theme)
        self.assertIn("--paper: #0B1023;", page)
        self.assertIn("--text-primary: #0B1023;", page)
        self.assertIn("--signal: #78DCE8;", page)
        self.assertIn("--type-heading-size: 14px;", page)
        self.assertIn("--type-body-size: 12px;", page)
        self.assertIn("--type-overline-size: 11px;", page)
        self.assertIn('--font-display-family: "Inter"', page)
        self.assertIn('"Arial Black"', page)
        self.assertIn('"Helvetica Neue"', page)
        self.assertNotIn("--signal: #E24B4A;", page)
        self.assertNotIn("Pending approvals generated from live manifests.", page)
        self.assertNotIn("Local only / manifest-backed state", page)
        self.assertNotIn("Approve promotes the recorded proof.", page)
        self.assertNotIn(">Review Inbox<", page)
        self.assertNotIn("<h1>", page)
        self.assertNotIn("/review/episodes/", page)
        self.assertIn("Cascade Effects / Review Desk", page)
        self.assertNotIn('<a class="nav-link" href="/review">Inbox</a>', page)
        self.assertIn("menu-trigger", page)
        self.assertIn("@media (prefers-color-scheme: dark)", page)
        self.assertIn("color-scheme: light;", page)
        self.assertIn("color-scheme: dark;", page)
        self.assertIn("color: var(--text-primary);", page)
        self.assertNotIn("localStorage", page)
        self.assertNotIn('searchParams.set("theme"', page)

    def test_review_page_typography_uses_only_allowed_type_scale(self) -> None:
        page = render_review_page(title="Review Inbox", theme=load_signal_brand_theme(self.context))
        self.assertEqual(_font_size_literals(page), ALLOWED_FONT_SIZE_LITERALS)
        for selector in (
            ".eyebrow",
            ".phase-label",
            ".summary-pill-label",
            ".meta-label",
            ".menu-panel label",
            ".menu-section-label",
            ".theme-warning strong",
        ):
            self.assertIn("text-transform: uppercase;", _css_block(page, selector))
        for selector in (".rail-filter", ".chip", ".disclosure-summary", ".menu-trigger"):
            self.assertNotIn("text-transform: uppercase;", _css_block(page, selector))

    def test_markdown_preview_renders_token_driven_theme_modes(self) -> None:
        theme = load_signal_brand_theme(self.context)
        page = render_markdown_html("# Review notes", title="Review Notes", theme=theme)
        self.assertIn("@media (prefers-color-scheme: dark)", page)
        self.assertIn("color-scheme: light;", page)
        self.assertIn("color-scheme: dark;", page)
        self.assertIn("color: var(--text-primary, #18191c);", page)
        self.assertNotIn("localStorage", page)

    def test_markdown_preview_typography_uses_only_allowed_type_scale(self) -> None:
        page = render_markdown_html("# Review notes", title="Review Notes", theme=load_signal_brand_theme(self.context))
        self.assertEqual(_font_size_literals(page), ALLOWED_FONT_SIZE_LITERALS)
        self.assertIn("text-transform: uppercase;", _css_block(page, ".theme-warning strong"))

    def test_visual_research_fails_when_act_has_fewer_scenes_than_beats(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        broken = copy.deepcopy(manifest)
        broken["visual_research"]["acts"][2]["beat_count"] = 3
        state = derive_episode_state(broken, self.context)
        self.assertTrue(any("beat_count=3" in issue["message"] for issue in state["errors"]))

    def test_visual_research_fails_when_long_act_lacks_motion_plan_or_exception(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        broken = copy.deepcopy(manifest)
        broken["visual_research"]["acts"][0]["estimated_seconds"] = 301
        broken["visual_research"]["acts"][0]["required_motion_sequences"] = 3
        broken["visual_research"]["acts"][0]["exception_reason"] = ""
        state = derive_episode_state(broken, self.context)
        self.assertTrue(any("needs 3 planned motion sequences" in issue["message"] for issue in state["errors"]))

    def test_visual_research_fails_when_opening_sequence_is_incomplete(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        broken = copy.deepcopy(manifest)
        broken["visual_research"]["opening_sequence"]["subject_action"] = ""
        state = derive_episode_state(broken, self.context)
        self.assertTrue(any("opening_sequence is missing `subject_action`" in issue["message"] for issue in state["errors"]))

    def test_visual_research_fails_when_opening_sequence_references_invalid_planned_assets(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        broken = copy.deepcopy(manifest)
        broken["visual_research"]["opening_sequence"]["planned_scene_id"] = "unknown_scene"
        broken["visual_research"]["opening_sequence"]["planned_motion_id"] = "unknown_motion"
        state = derive_episode_state(broken, self.context)
        error_messages = [issue["message"] for issue in state["errors"]]
        self.assertTrue(any("planned_scene_id `unknown_scene`" in message for message in error_messages))
        self.assertTrue(any("planned_motion_id `unknown_motion`" in message for message in error_messages))

    def test_visual_research_fails_when_review_is_pending_or_rejected(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        with tempfile.TemporaryDirectory() as temp_dir:
            self._prepare_visual_research_fixture(manifest, Path(temp_dir))
            for approval_status in ("pending", "rejected"):
                with self.subTest(approval_status=approval_status):
                    broken = copy.deepcopy(manifest)
                    broken["visual_research"]["status"] = "review"
                    broken["visual_research"]["approval"]["reviewed_at"] = ""
                    broken["visual_research"]["approval"]["notes"] = ""
                    broken["visual_research"]["approval"]["reviewer"] = ""
                    broken["visual_research"]["approval"]["status"] = approval_status
                    state = derive_episode_state(broken, self.context)
                    self.assertTrue(any(f"approval is `{approval_status}`" in issue["message"] for issue in state["errors"]))

    def test_visual_research_fails_when_script_fingerprint_changes(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        broken = copy.deepcopy(manifest)
        broken["visual_research"]["script_sha256"] = "stale"
        state = derive_episode_state(broken, self.context)
        self.assertEqual(state["lanes"]["visual_research"]["status"], "review")
        self.assertTrue(any("Locked script changed" in issue["message"] for issue in state["errors"]))

    def test_visual_research_fails_when_contact_sheet_is_missing(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        broken = copy.deepcopy(manifest)
        broken["visual_research"]["contact_sheet_path"] = "/tmp/missing-challenger-contact-sheet.pdf"
        state = derive_episode_state(broken, self.context)
        self.assertEqual(state["lanes"]["visual_research"]["status"], "review")
        self.assertFalse(state["lanes"]["visual_research"]["docs_complete"])
        self.assertTrue(any("contact_sheet_path" in issue["message"] for issue in state["errors"]))

    def test_visual_research_fails_when_source_inventory_is_missing(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        broken = copy.deepcopy(manifest)
        broken["visual_research"]["source_inventory_path"] = "/tmp/missing-source-inventory.json"
        state = derive_episode_state(broken, self.context)
        self.assertEqual(state["lanes"]["visual_research"]["status"], "review")
        self.assertFalse(state["lanes"]["visual_research"]["docs_complete"])
        self.assertTrue(any("source_inventory_path" in issue["message"] for issue in state["errors"]))

    def test_visual_research_fails_when_approved_sources_are_unresolved(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            inventory_path = temp_root / "source_inventory.json"
            raw_asset = temp_root / "source.png"
            raw_asset.write_text("image", encoding="utf-8")
            write_source_inventory(
                inventory_path,
                {
                    "schema_version": 1,
                    "sources": [
                        {
                            "source_id": "act1_console_01",
                            "act_id": "act1",
                            "raw_asset_path": str(raw_asset),
                            "board_asset_path": "",
                            "approved_for_generation": True,
                            "text_status": "needs_cleanup",
                            "text_detection_manifest_path": "",
                            "cleanup_manifest_path": "",
                            "cleaned_asset_path": "",
                            "downstream_asset_path": "",
                            "notes": "",
                        }
                    ],
                },
            )
            manifest["visual_research"]["source_inventory_path"] = str(inventory_path)
            state = derive_episode_state(manifest, self.context)
        self.assertFalse(state["lanes"]["visual_research"]["source_inventory_complete"])
        self.assertIn("act1_console_01", state["lanes"]["visual_research"]["guardrails"]["unresolved_source_ids"])
        self.assertTrue(any("text cleanup" in issue["message"] for issue in state["errors"]))

    def test_source_inventory_round_trips_source_provenance_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            inventory_path = temp_root / "source_inventory.json"
            raw_asset = self._write_svg_fixture(temp_root / "candidate.svg")
            write_source_inventory(
                inventory_path,
                {
                    "schema_version": 2,
                    "sources": [
                        {
                            "source_id": "opening_01",
                            "act_id": "act1",
                            "coverage_id": "opening",
                            "opening_slot_id": "space_shuttle_challenger",
                            "candidate_label": "Launch stack",
                            "candidate_role": "opening_subject",
                            "source_url": "https://example.com/source.jpg",
                            "source_origin": "web_fresh",
                            "raw_asset_path": str(raw_asset),
                            "board_asset_path": "",
                            "approved_for_generation": False,
                            "text_status": "clear",
                            "text_detection_manifest_path": "",
                            "cleanup_manifest_path": "",
                            "cleaned_asset_path": "",
                            "downstream_asset_path": "",
                            "notes": "",
                        }
                    ],
                },
            )
            loaded = load_source_inventory(inventory_path)
        source = loaded["sources"][0]
        self.assertEqual(source["source_url"], "https://example.com/source.jpg")
        self.assertEqual(source["source_origin"], "web_fresh")
        self.assertEqual(source["raw_asset_path"], str(raw_asset))
        self.assertEqual(source["opening_slot_id"], "space_shuttle_challenger")

    def test_visual_research_fails_fresh_web_only_when_source_url_is_missing(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            raw_asset = self._write_svg_fixture(temp_root / "candidate.svg")
            inventory_path = temp_root / "source_inventory.json"
            write_source_inventory(
                inventory_path,
                {
                    "schema_version": 2,
                    "sources": [
                        {
                            "source_id": "opening_01",
                            "act_id": "act3",
                            "coverage_id": "opening",
                            "candidate_label": "Launch stack",
                            "candidate_role": "opening_subject",
                            "source_url": "",
                            "source_origin": "web_fresh",
                            "raw_asset_path": str(raw_asset),
                            "board_asset_path": "",
                            "approved_for_generation": False,
                            "text_status": "clear",
                            "text_detection_manifest_path": "",
                            "cleanup_manifest_path": "",
                            "cleaned_asset_path": "",
                            "downstream_asset_path": "",
                            "notes": "",
                        }
                    ],
                },
            )
            manifest["visual_research"]["source_inventory_path"] = str(inventory_path)
            manifest["visual_research"]["source_origin_policy"] = "fresh_web_only"
            state = derive_episode_state(manifest, self.context)
        self.assertFalse(state["lanes"]["visual_research"]["source_policy_complete"])
        self.assertTrue(any("missing source_url" in issue["message"] for issue in state["errors"]))

    def test_visual_research_fails_fresh_web_only_when_raw_asset_is_missing(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            inventory_path = temp_root / "source_inventory.json"
            write_source_inventory(
                inventory_path,
                {
                    "schema_version": 2,
                    "sources": [
                        {
                            "source_id": "opening_01",
                            "act_id": "act3",
                            "coverage_id": "opening",
                            "candidate_label": "Launch stack",
                            "candidate_role": "opening_subject",
                            "source_url": "https://example.com/source.jpg",
                            "source_origin": "web_fresh",
                            "raw_asset_path": str(temp_root / "missing.svg"),
                            "board_asset_path": "",
                            "approved_for_generation": False,
                            "text_status": "clear",
                            "text_detection_manifest_path": "",
                            "cleanup_manifest_path": "",
                            "cleaned_asset_path": "",
                            "downstream_asset_path": "",
                            "notes": "",
                        }
                    ],
                },
            )
            manifest["visual_research"]["source_inventory_path"] = str(inventory_path)
            manifest["visual_research"]["source_origin_policy"] = "fresh_web_only"
            state = derive_episode_state(manifest, self.context)
        self.assertFalse(state["lanes"]["visual_research"]["source_policy_complete"])
        self.assertTrue(any("missing local raw_asset_path downloads" in issue["message"] for issue in state["errors"]))

    def test_visual_research_fails_fresh_web_only_when_generated_select_is_reused(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            generated_select = temp_root / "references" / "episodes" / "challenger" / "launch_stack_exterior" / "selects" / "legacy.svg"
            generated_select.parent.mkdir(parents=True, exist_ok=True)
            self._write_svg_fixture(generated_select)
            inventory_path = temp_root / "source_inventory.json"
            write_source_inventory(
                inventory_path,
                {
                    "schema_version": 2,
                    "sources": [
                        {
                            "source_id": "opening_01",
                            "act_id": "act3",
                            "coverage_id": "opening",
                            "candidate_label": "Launch stack",
                            "candidate_role": "opening_subject",
                            "source_url": "https://example.com/source.jpg",
                            "source_origin": "web_fresh",
                            "raw_asset_path": str(generated_select),
                            "board_asset_path": "",
                            "approved_for_generation": False,
                            "text_status": "clear",
                            "text_detection_manifest_path": "",
                            "cleanup_manifest_path": "",
                            "cleaned_asset_path": "",
                            "downstream_asset_path": "",
                            "notes": "",
                        }
                    ],
                },
            )
            manifest["visual_research"]["source_inventory_path"] = str(inventory_path)
            manifest["visual_research"]["source_origin_policy"] = "fresh_web_only"
            state = derive_episode_state(manifest, self.context)
        self.assertFalse(state["lanes"]["visual_research"]["source_policy_complete"])
        self.assertTrue(any("cannot reuse prior generated selects" in issue["message"] for issue in state["errors"]))

    def test_visual_research_fails_fresh_web_only_when_display_assets_duplicate(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            shared_asset = self._write_svg_fixture(temp_root / "shared.svg")
            inventory_path = temp_root / "source_inventory.json"
            write_source_inventory(
                inventory_path,
                {
                    "schema_version": 2,
                    "sources": [
                        {
                            "source_id": "opening_01",
                            "act_id": "act3",
                            "coverage_id": "opening",
                            "candidate_label": "Launch stack A",
                            "candidate_role": "opening_subject",
                            "source_url": "https://example.com/source-a.jpg",
                            "source_origin": "web_fresh",
                            "raw_asset_path": str(shared_asset),
                            "board_asset_path": "",
                            "approved_for_generation": False,
                            "text_status": "clear",
                            "text_detection_manifest_path": "",
                            "cleanup_manifest_path": "",
                            "cleaned_asset_path": "",
                            "downstream_asset_path": "",
                            "notes": "",
                        },
                        {
                            "source_id": "opening_02",
                            "act_id": "act3",
                            "coverage_id": "opening",
                            "candidate_label": "Launch stack B",
                            "candidate_role": "opening_subject",
                            "source_url": "https://example.com/source-b.jpg",
                            "source_origin": "web_fresh",
                            "raw_asset_path": str(shared_asset),
                            "board_asset_path": "",
                            "approved_for_generation": False,
                            "text_status": "clear",
                            "text_detection_manifest_path": "",
                            "cleanup_manifest_path": "",
                            "cleaned_asset_path": "",
                            "downstream_asset_path": "",
                            "notes": "",
                        },
                    ],
                },
            )
            manifest["visual_research"]["source_inventory_path"] = str(inventory_path)
            manifest["visual_research"]["source_origin_policy"] = "fresh_web_only"
            state = derive_episode_state(manifest, self.context)
        self.assertFalse(state["lanes"]["visual_research"]["source_policy_complete"])
        self.assertTrue(any("must use unique displayed images" in issue["message"] for issue in state["errors"]))

    def test_visual_research_fails_when_opening_candidate_lacks_opening_slot_id(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            raw_asset = self._write_svg_fixture(temp_root / "candidate.svg")
            inventory_path = temp_root / "source_inventory.json"
            write_source_inventory(
                inventory_path,
                {
                    "schema_version": 2,
                    "sources": [
                        {
                            "source_id": "opening_01",
                            "act_id": "act3",
                            "coverage_id": "opening",
                            "opening_slot_id": "",
                            "candidate_label": "Launch stack",
                            "candidate_role": "opening_subject",
                            "source_url": "https://example.com/source.jpg",
                            "source_origin": "web_fresh",
                            "raw_asset_path": str(raw_asset),
                            "board_asset_path": "",
                            "approved_for_generation": False,
                            "text_status": "clear",
                            "text_detection_manifest_path": "",
                            "cleanup_manifest_path": "",
                            "cleaned_asset_path": "",
                            "downstream_asset_path": "",
                            "notes": "",
                        }
                    ],
                },
            )
            manifest["visual_research"]["source_inventory_path"] = str(inventory_path)
            state = derive_episode_state(manifest, self.context)
        self.assertFalse(state["lanes"]["visual_research"]["opening_slot_assignment_complete"])
        self.assertTrue(any("missing opening_slot_id assignments" in issue["message"] for issue in state["errors"]))

    def test_visual_research_fails_when_named_opening_slot_has_no_candidates(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            inventory_path = temp_root / "source_inventory.json"
            slots = [
                ("space_shuttle_challenger", "opening_subject"),
                ("vhs_cassette", "opening_supporting"),
                ("boombox_radio", "opening_supporting"),
                ("high_top_sneaker", "opening_supporting"),
                ("aluminum_soda_can", "opening_supporting"),
                ("beige_home_computer_crt", "opening_supporting"),
            ]
            sources = []
            for index, (slot_id, role) in enumerate(slots, start=1):
                asset = self._write_svg_fixture(temp_root / f"{slot_id}.svg")
                sources.append(
                    {
                        "source_id": f"opening_{index:02d}",
                        "act_id": "act3",
                        "coverage_id": "opening",
                        "opening_slot_id": slot_id,
                        "candidate_label": slot_id,
                        "candidate_role": role,
                        "source_url": f"https://example.com/{slot_id}.jpg",
                        "source_origin": "web_fresh",
                        "raw_asset_path": str(asset),
                        "board_asset_path": "",
                        "approved_for_generation": False,
                        "text_status": "clear",
                        "text_detection_manifest_path": "",
                        "cleanup_manifest_path": "",
                        "cleaned_asset_path": "",
                        "downstream_asset_path": "",
                        "notes": "",
                    }
                )
            write_source_inventory(inventory_path, {"schema_version": 2, "sources": sources})
            manifest["visual_research"]["source_inventory_path"] = str(inventory_path)
            state = derive_episode_state(manifest, self.context)
        self.assertTrue(any("missing: Cube puzzle" in issue["message"] for issue in state["errors"]))

    def test_visual_research_fails_when_subject_opening_slot_has_too_few_candidates(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            inventory_path = temp_root / "source_inventory.json"
            source_specs = [
                ("opening_01", "space_shuttle_challenger", "opening_subject"),
                ("opening_02", "vhs_cassette", "opening_supporting"),
                ("opening_03", "boombox_radio", "opening_supporting"),
                ("opening_04", "high_top_sneaker", "opening_supporting"),
                ("opening_05", "aluminum_soda_can", "opening_supporting"),
                ("opening_06", "cube_puzzle", "opening_supporting"),
                ("opening_07", "beige_home_computer_crt", "opening_supporting"),
            ]
            sources = []
            for source_id, slot_id, role in source_specs:
                asset = self._write_svg_fixture(temp_root / f"{source_id}.svg")
                sources.append(
                    {
                        "source_id": source_id,
                        "act_id": "act3",
                        "coverage_id": "opening",
                        "opening_slot_id": slot_id,
                        "candidate_label": source_id,
                        "candidate_role": role,
                        "source_url": f"https://example.com/{source_id}.jpg",
                        "source_origin": "web_fresh",
                        "raw_asset_path": str(asset),
                        "board_asset_path": "",
                        "approved_for_generation": False,
                        "text_status": "clear",
                        "text_detection_manifest_path": "",
                        "cleanup_manifest_path": "",
                        "cleaned_asset_path": "",
                        "downstream_asset_path": "",
                        "notes": "",
                    }
                )
            write_source_inventory(inventory_path, {"schema_version": 2, "sources": sources})
            manifest["visual_research"]["source_inventory_path"] = str(inventory_path)
            state = derive_episode_state(manifest, self.context)
        self.assertTrue(any("opening subject slot `Space Shuttle Challenger` needs at least 2 candidates" in issue["message"] for issue in state["errors"]))

    def test_generic_era_cluster_fails_when_supporting_slot_count_is_too_small(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        broken = copy.deepcopy(manifest)
        broken["visual_research"]["opening_sequence"]["object_strategy"] = "generic_era_cluster"
        broken["visual_research"]["opening_sequence"]["supporting_objects"] = [
            "VHS cassette",
            "Cassette boombox radio",
            "White leather high-top sneaker",
        ]
        broken["visual_research"]["opening_sequence"]["slots"] = [
            {
                "slot_id": "vhs_cassette",
                "display_label": "VHS cassette",
                "role": "supporting_object",
                "object_scope": "generic_mass_market",
                "renderability": "common_iconic",
                "visual_descriptor": "generic black VHS cassette",
            },
            {
                "slot_id": "boombox_radio",
                "display_label": "Cassette boombox radio",
                "role": "supporting_object",
                "object_scope": "generic_mass_market",
                "renderability": "common_iconic",
                "visual_descriptor": "generic silver or black cassette boombox",
            },
            {
                "slot_id": "high_top_sneaker",
                "display_label": "White leather high-top sneaker",
                "role": "supporting_object",
                "object_scope": "generic_mass_market",
                "renderability": "common_iconic",
                "visual_descriptor": "generic white leather high-top sneaker",
            },
            {
                "slot_id": "space_shuttle_challenger",
                "display_label": "Space Shuttle Challenger",
                "role": "subject_object",
                "object_scope": "episode_specific",
                "renderability": "common_iconic",
                "visual_descriptor": "space shuttle stack on pad",
            },
        ]
        state = derive_episode_state(broken, self.context)
        self.assertTrue(any("at least 4 generic_mass_market supporting_object slots" in issue["message"] for issue in state["errors"]))

    def test_generic_era_cluster_fails_when_subject_slot_is_not_last(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        broken = copy.deepcopy(manifest)
        slots = copy.deepcopy(broken["visual_research"]["opening_sequence"]["slots"])
        broken["visual_research"]["opening_sequence"]["slots"] = [slots[-1], *slots[:-1]]
        state = derive_episode_state(broken, self.context)
        self.assertTrue(any("subject_object slot must be the final opening slot" in issue["message"] for issue in state["errors"]))

    def test_generic_era_cluster_fails_when_context_imagery_occupies_generic_slot(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            inventory_path = temp_root / "source_inventory.json"
            source_specs = [
                ("opening_01", "vhs_cassette", "Mission control room wide", "opening_supporting"),
                ("opening_02", "boombox_radio", "Cassette boombox radio", "opening_supporting"),
                ("opening_03", "high_top_sneaker", "White high-top sneaker", "opening_supporting"),
                ("opening_04", "aluminum_soda_can", "Red soda can", "opening_supporting"),
                ("opening_05", "cube_puzzle", "Cube puzzle", "opening_supporting"),
                ("opening_06", "beige_home_computer_crt", "Beige home computer CRT", "opening_supporting"),
                ("opening_07", "space_shuttle_challenger", "Launch stack A", "opening_subject"),
                ("opening_08", "space_shuttle_challenger", "Launch stack B", "opening_subject"),
            ]
            sources = []
            for source_id, slot_id, label, role in source_specs:
                asset = self._write_svg_fixture(temp_root / f"{source_id}.svg")
                sources.append(
                    {
                        "source_id": source_id,
                        "act_id": "act3",
                        "coverage_id": "opening",
                        "opening_slot_id": slot_id,
                        "candidate_label": label,
                        "candidate_role": role,
                        "source_url": f"https://example.com/{source_id}.jpg",
                        "source_origin": "web_fresh",
                        "raw_asset_path": str(asset),
                        "board_asset_path": "",
                        "approved_for_generation": False,
                        "text_status": "clear",
                        "text_detection_manifest_path": "",
                        "cleanup_manifest_path": "",
                        "cleaned_asset_path": "",
                        "downstream_asset_path": "",
                        "notes": "",
                    }
                )
            write_source_inventory(inventory_path, {"schema_version": 2, "sources": sources})
            manifest["visual_research"]["source_inventory_path"] = str(inventory_path)
            state = derive_episode_state(manifest, self.context)
        self.assertTrue(any("isolated mass-market object references" in issue["message"] for issue in state["errors"]))

    def test_build_contact_sheet_pages_groups_opening_candidates_by_slot_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            cassette = self._write_svg_fixture(temp_root / "cassette.svg")
            boombox = self._write_svg_fixture(temp_root / "boombox.svg")
            shuttle = self._write_svg_fixture(temp_root / "shuttle.svg")
            pages = build_contact_sheet_pages(
                {
                    "id": "challenger",
                    "title": "Challenger",
                    "visual_research": {
                        "opening_sequence": {
                            "object_strategy": "generic_era_cluster",
                            "time_period_label": "January 1986",
                            "slots": [
                                {
                                    "slot_id": "vhs_cassette",
                                    "display_label": "VHS cassette",
                                    "role": "supporting_object",
                                    "object_scope": "generic_mass_market",
                                    "renderability": "common_iconic",
                                    "visual_descriptor": "generic black VHS cassette",
                                },
                                {
                                    "slot_id": "boombox_radio",
                                    "display_label": "Cassette boombox radio",
                                    "role": "supporting_object",
                                    "object_scope": "generic_mass_market",
                                    "renderability": "common_iconic",
                                    "visual_descriptor": "generic silver or black cassette boombox",
                                },
                                {
                                    "slot_id": "space_shuttle_challenger",
                                    "display_label": "Space Shuttle Challenger",
                                    "role": "subject_object",
                                    "object_scope": "episode_specific",
                                    "renderability": "common_iconic",
                                    "visual_descriptor": "space shuttle stack on pad",
                                },
                            ],
                        },
                        "acts": [],
                        "_source_inventory": {
                            "sources": [
                                {
                                    "source_id": "opening_01",
                                    "coverage_id": "opening",
                                    "opening_slot_id": "space_shuttle_challenger",
                                    "candidate_label": "Launch stack",
                                    "candidate_role": "opening_subject",
                                    "raw_asset_path": str(shuttle),
                                },
                                {
                                    "source_id": "opening_02",
                                    "coverage_id": "opening",
                                    "opening_slot_id": "vhs_cassette",
                                    "candidate_label": "VHS cassette",
                                    "candidate_role": "opening_supporting",
                                    "raw_asset_path": str(cassette),
                                },
                                {
                                    "source_id": "opening_03",
                                    "coverage_id": "opening",
                                    "opening_slot_id": "boombox_radio",
                                    "candidate_label": "Cassette boombox radio",
                                    "candidate_role": "opening_supporting",
                                    "raw_asset_path": str(boombox),
                                },
                            ]
                        },
                    },
                }
            )
        self.assertEqual(pages[0].subtitle, "January 1986 / generic era culture cluster")
        self.assertEqual([section.heading for section in pages[0].sections], ["VHS cassette", "Cassette boombox radio", "Space Shuttle Challenger"])
        self.assertEqual([candidate.candidate_label for candidate in pages[0].sections[0].candidates], ["VHS cassette"])
        self.assertEqual([candidate.candidate_label for candidate in pages[0].sections[2].candidates], ["Launch stack"])

    def test_render_contact_sheet_pdf_fails_when_opening_candidate_slot_assignment_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            asset = self._write_svg_fixture(temp_root / "candidate.svg")
            manifest = {
                "id": "challenger",
                "title": "Challenger",
                "visual_research": {
                    "opening_sequence": {
                        "time_period_label": "January 1986",
                        "slots": [
                            {"slot_id": "space_shuttle_challenger", "display_label": "Space Shuttle Challenger", "role": "subject_object"},
                        ],
                    },
                    "acts": [],
                    "_source_inventory": {
                        "sources": [
                            {
                                "source_id": "opening_01",
                                "coverage_id": "opening",
                                "opening_slot_id": "",
                                "candidate_label": "Missing assignment",
                                "candidate_role": "opening_subject",
                                "raw_asset_path": str(asset),
                            }
                        ]
                    },
                },
            }
            with self.assertRaises(SystemExit) as exc:
                render_contact_sheet_pdf(manifest, temp_root / "contact_sheet.pdf")
        self.assertIn("must map to explicit opening slots", str(exc.exception))

    def test_contact_sheet_fit_uses_contain_geometry(self) -> None:
        draw_x, draw_y, draw_width, draw_height = _fit_contain(
            source_width=40,
            source_height=80,
            box_x=10.0,
            box_y=20.0,
            box_width=100.0,
            box_height=100.0,
        )
        self.assertEqual(draw_width, 50.0)
        self.assertEqual(draw_height, 100.0)
        self.assertEqual(draw_x, 35.0)
        self.assertEqual(draw_y, 20.0)

    def test_render_contact_sheet_pdf_generates_plain_white_page(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            sources = []
            for index in range(1, 9):
                asset = self._write_svg_fixture(temp_root / f"opening_{index}.svg")
                sources.append(
                    {
                        "source_id": f"opening_{index:02d}",
                        "coverage_id": "opening",
                        "candidate_label": f"Candidate {index}",
                        "candidate_role": "opening_subject" if index <= 2 else "opening_supporting",
                        "raw_asset_path": str(asset),
                    }
                )
            manifest = {
                "id": "challenger",
                "title": "Challenger",
                "visual_research": {
                    "opening_sequence": {"time_period_label": "January 1986"},
                    "acts": [],
                    "_source_inventory": {"sources": sources},
                },
            }
            output_path = temp_root / "contact_sheet.pdf"
            render_contact_sheet_pdf(manifest, output_path)
            self.assertTrue(output_path.exists())
            self.assertIn(b"0 g", output_path.read_bytes())
            subprocess.run(
                ["pdftoppm", "-png", str(output_path), str(temp_root / "page")],
                check=True,
                capture_output=True,
                text=True,
            )
            corner_rgb = subprocess.run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-i",
                    str(temp_root / "page-1.png"),
                    "-vf",
                    "crop=1:1:0:0,format=rgb24",
                    "-f",
                    "rawvideo",
                    "-",
                ],
                check=True,
                capture_output=True,
            ).stdout
        self.assertEqual(corner_rgb, bytes([255, 255, 255]))

    def test_render_contact_sheet_pdf_fails_when_candidate_image_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest = {
                "id": "challenger",
                "title": "Challenger",
                "visual_research": {
                    "opening_sequence": {"time_period_label": "January 1986"},
                    "acts": [],
                    "_source_inventory": {
                        "sources": [
                            {
                                "source_id": "opening_01",
                                "coverage_id": "opening",
                                "candidate_label": "Missing candidate",
                                "candidate_role": "opening_subject",
                                "raw_asset_path": str(temp_root / "missing.svg"),
                            }
                        ]
                    },
                },
            }
            with self.assertRaises(SystemExit) as exc:
                render_contact_sheet_pdf(manifest, temp_root / "contact_sheet.pdf")
        self.assertIn("missing a usable image", str(exc.exception))

    def test_visual_research_fails_when_fact_check_is_missing(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            episode_dir = temp_root / "episodes_repo" / "Ep1_Challenger"
            visual_research_dir = episode_dir / "visual_research"
            visual_research_dir.mkdir(parents=True, exist_ok=True)
            script_path = episode_dir / "Ep1_Challenger.txt"
            script_path.write_text("test script", encoding="utf-8")
            for name in ("contact_sheet.pdf", "source_inventory.json", "act_breakdown.md", "reference_notes.md", "sources.md", "assembly_notes.md"):
                (visual_research_dir / name).write_text(name, encoding="utf-8")
            context = Context(
                root=context.root,
                channel=context.channel,
                web_entry_ids=context.web_entry_ids,
                asset_archetypes=context.asset_archetypes,
                episodes_repo=self.context.episodes_repo.__class__(episode_dir.parent),
                audio_repo=context.audio_repo,
                viz_repo=context.viz_repo,
                web_repo=context.web_repo,
            )
            broken = copy.deepcopy(manifest)
            broken["script"]["path"] = str(script_path)
            broken["visual_research"]["status"] = "review"
            broken["visual_research"]["contact_sheet_path"] = str(visual_research_dir / "contact_sheet.pdf")
            broken["visual_research"]["source_inventory_path"] = str(visual_research_dir / "source_inventory.json")
            broken["visual_research"]["act_breakdown_path"] = str(visual_research_dir / "act_breakdown.md")
            broken["visual_research"]["reference_notes_path"] = str(visual_research_dir / "reference_notes.md")
            broken["visual_research"]["sources_path"] = str(visual_research_dir / "sources.md")
            broken["visual_research"]["assembly_notes_path"] = str(visual_research_dir / "assembly_notes.md")
            state = derive_episode_state(broken, context)
        self.assertEqual(state["lanes"]["visual_research"]["status"], "review")
        self.assertFalse(state["lanes"]["visual_research"]["docs_complete"])
        self.assertTrue(any("fact_check_path" in issue["message"] for issue in state["errors"]))

    def test_next_action_stays_on_visual_research_until_approval_is_complete(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        broken = copy.deepcopy(manifest)
        broken["visual_research"]["status"] = "review"
        broken["visual_research"]["approval"]["status"] = "pending"
        state = derive_episode_state(broken, self.context)
        self.assertEqual(state["next_action"]["lane"], "visual_research")

    def test_approved_visual_research_seeds_scene_and_motion_items(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/hyatt-regency.toml")
        seeded = copy.deepcopy(manifest)
        seeded["visual_research"]["status"] = "review"
        seeded["visual_research"]["approval"] = {
            "status": "approved",
            "reviewer": "human_editor",
            "reviewed_at": "2026-03-28T00:00:00Z",
            "notes": "Approved for seeding.",
        }
        seeded["visual_research"]["acts"] = [
            {
                "id": "act1",
                "title": "Signal discovery",
                "estimated_seconds": 180,
                "beat_count": 2,
                "visual_thesis": "Show the warning signal becoming legible.",
                "dominant_signal": "fracture line and suspended structure.",
                "reference_board_path": "/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/visual_research/boards/act1",
                "required_motion_sequences": 2,
                "planned_scene_ids": ["signal_frame", "atrium_close"],
                "planned_motion_ids": ["signal_frame_drift"],
                "exception_reason": "Second motion sequence deferred until more approved stills exist.",
            }
        ]
        seeded["scene_stills"]["items"] = []
        seeded["motion_assets"]["items"] = []
        materialized = materialize_episode_manifest(self.context, seeded)
        scene_ids = [item["id"] for item in materialized["scene_stills"]["items"]]
        motion_ids = [item["id"] for item in materialized["motion_assets"]["items"]]
        self.assertEqual(scene_ids[:2], ["signal_frame", "atrium_close"])
        self.assertEqual(motion_ids, ["signal_frame_drift"])
        self.assertEqual(materialized["motion_assets"]["items"][0]["source_still_id"], "signal_frame")
        self.assertEqual(materialized["motion_assets"]["items"][0]["behavior"], "")
        self.assertEqual(materialized["motion_assets"]["items"][0]["authoring_mode"], "legacy_i2v")
        self.assertTrue(materialized["motion_assets"]["items"][0]["workbench_project_path"].endswith("/signal_frame_drift/workbench/project.json"))

    def test_bootstrap_uses_episode_owned_packaging_paths(self) -> None:
        manifest = build_bootstrap_manifest(
            self.context,
            EPISODES_ROOT / "Ep3_Hyatt-Regency",
            scene_archetype_id=None,
            pillar="design-failures",
        )
        self.assertEqual(manifest["scene_stills"]["items"][0]["reference_dir"], "")
        self.assertEqual(manifest["scene_stills"]["items"][0]["output_path"], "")
        thumbnail = manifest["packaging_stills"]["items"][0]
        self.assertEqual(
            thumbnail["reference_dir"],
            "/Users/mike/Viz_CascadeEffects/references/episodes/hyatt-regency/primary_thumbnail",
        )
        self.assertEqual(
            thumbnail["output_path"],
            "/Users/mike/Viz_CascadeEffects/references/episodes/hyatt-regency/primary_thumbnail/selects/hero_plate.png",
        )
        self.assertEqual(manifest["visual_research"]["opening_sequence"]["planned_motion_id"], "")

    def test_bootstrap_creates_local_inception_review_packet_and_stable_remote_url(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            episodes_root = temp_root / "Episodes"
            self._write_temp_episode_dir(episodes_root)
            context = self._build_temp_bootstrap_context(temp_root, episodes_root, temp_root / "Web")
            args = argparse.Namespace(
                episode="test-episode",
                all=False,
                scene_archetype=None,
                pillar=None,
                skip_remote_review=True,
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = command_bootstrap(context, args)

            self.assertEqual(exit_code, 0)
            packet_root = (
                episodes_root
                / "Ep99_Test-Episode"
                / "production"
                / "long_form_video_v1"
                / "youtube"
                / "publish_readiness"
                / "test-episode"
            )
            manifest_path = packet_root / "publish_readiness_manifest.json"
            review_html_path = packet_root / "review.html"
            self.assertTrue(manifest_path.exists())
            self.assertTrue(review_html_path.exists())
            review_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(review_manifest["review_id"], "test-episode")
            self.assertEqual(review_manifest["lifecycle_stage"], "inception")
            self.assertEqual(
                review_manifest["remote_review"]["remote_review_url"],
                "https://cascadeeffects.tv/reviews/publish-readiness/test-episode",
            )
            self.assertFalse(review_manifest["locks"]["may_youtube_action"])
            self.assertIn("Review Video Not Attached", review_html_path.read_text(encoding="utf-8"))
            self.assertIn("remote inception review publish skipped", output.getvalue())

    def test_bootstrap_publishes_inception_review_manifest_when_not_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            episodes_root = temp_root / "Episodes"
            self._write_temp_episode_dir(episodes_root)
            context = self._build_temp_bootstrap_context(temp_root, episodes_root, temp_root / "Web")
            args = argparse.Namespace(
                episode="test-episode",
                all=False,
                scene_archetype=None,
                pillar=None,
                skip_remote_review=False,
            )
            completed = subprocess.CompletedProcess(
                args=["npm"],
                returncode=0,
                stdout=json.dumps(
                    {
                        "ok": True,
                        "remoteReviewUrl": "https://cascadeeffects.tv/reviews/publish-readiness/test-episode",
                        "manifestBlobUrl": "https://blob.example/reviews/publish-readiness/test-episode/manifest.json",
                    }
                ),
                stderr="",
            )
            with mock.patch.dict(os.environ, {"BLOB_READ_WRITE_TOKEN": "blob-test-token"}), mock.patch(
                "orchestration.inception_review.subprocess.run",
                return_value=completed,
            ) as run:
                with contextlib.redirect_stdout(io.StringIO()):
                    exit_code = command_bootstrap(context, args)

            self.assertEqual(exit_code, 0)
            command = run.call_args.args[0]
            self.assertIn("--mode", command)
            self.assertIn("inception", command)
            self.assertIn("--review-id", command)
            self.assertIn("test-episode", command)

    def test_challenger_motion_item_declares_archetype(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        motion_item = next(item for item in manifest["motion_assets"]["items"] if item["id"] == "launch_commit_dolly")
        self.assertEqual(motion_item["archetype_id"], "challenger_slow_dolly")
        self.assertEqual(motion_item["width"], 640)
        self.assertEqual(motion_item["height"], 384)

    def test_viz_adapter_exposes_motion_certification(self) -> None:
        certification = self.context.viz_repo.find_motion_certification("challenger", "launch_commit_dolly")
        self.assertIsNotNone(certification)
        assert certification is not None
        self.assertEqual(certification.pipeline, "distilled")
        self.assertTrue(certification.expected_typography_metadata)

    def test_bootstrap_imports_web_metadata_for_semmelweis(self) -> None:
        manifest = build_bootstrap_manifest(
            self.context,
            EPISODES_ROOT / "Ep4_Semmelweis",
            scene_archetype_id=None,
            pillar="design-failures",
        )
        self.assertEqual(manifest["pillar"], "one-decision")
        self.assertEqual(manifest["label"], "One Decision · Launch Episode 04")
        self.assertIn("Hospital mortality ledgers", manifest["summary"])
        self.assertEqual(
            manifest["audio"]["pipeline_dir"],
            "/Users/mike/Audio_CascadeEffects/tmp/ep4_semmelweis_production",
        )
        self.assertEqual(
            manifest["audio"]["master_path"],
            "/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/final/Ep4_Semmelweis.wav",
        )
        self.assertEqual(manifest["audio"]["review"]["status"], "pending")

    def test_web_launch_entries_follow_canonical_first_eight_order(self) -> None:
        entries = self.context.web_repo.launch_entries()
        self.assertEqual(
            list(entries)[:8],
            [
                "challenger",
                "therac-25",
                "hyatt-regency",
                "semmelweis",
                "tacoma-narrows",
                "piltdown-man",
                "737-max",
                "titanic",
            ],
        )
        self.assertEqual(entries["737-max"].label, "Design Failures · Launch Episode 07")
        self.assertEqual(entries["titanic"].label, "Mystery That Has Receipts · Launch Episode 08")

    def test_materialized_manifest_backfills_audio_review_and_writes_audio_review_block(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/hyatt-regency.toml")
        materialized = materialize_episode_manifest(self.context, manifest)
        self.assertEqual(
            materialized["audio"]["review"],
            {
                "status": "pending",
                "reviewer": "",
                "reviewed_at": "",
                "notes": "",
                "freshness_override": "",
            },
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "hyatt-regency.toml"
            write_episode_manifest(manifest_path, materialized)
            rendered = manifest_path.read_text(encoding="utf-8")
        self.assertIn("[audio.review]", rendered)
        self.assertIn('reviewer = ""', rendered)

    def test_bootstrap_imports_web_metadata_for_piltdown(self) -> None:
        manifest = build_bootstrap_manifest(
            self.context,
            EPISODES_ROOT / "Ep6_Piltdown-Man",
            scene_archetype_id=None,
            pillar="design-failures",
        )
        self.assertEqual(manifest["pillar"], "receipts")
        self.assertEqual(manifest["label"], "Receipts · Launch Episode 06")
        self.assertIn("flattering fossil story", manifest["summary"])
        self.assertEqual(manifest["web"]["entry_id"], "piltdown-man")
        self.assertIn("Launch entry exists", manifest["web"]["notes"])

    def test_audio_brief_uses_delegated_audio_flow_and_episode_package_contract(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/therac-25.toml")
        brief = render_brief(self.context, manifest, "audio")
        self.assertIn("validate -> cost -> render -> guard -> merge -> qa -> promote-audio", brief)
        self.assertIn("/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/final/Ep2_Therac-25.wav", brief)
        self.assertIn("Audio package metadata:", brief)
        self.assertIn("promoted into the episode manifest", brief)
        self.assertIn("Human review status: pending", brief)
        self.assertIn("A human reviewer has approved the final audio package.", brief)

    def test_workflow_docs_describe_audio_review_gate_and_status_glossary(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        diagram = (ROOT / "episode-workflow-swimlane.mmd").read_text(encoding="utf-8")
        self.assertIn(
            "audio` reaches `done` only when the final master WAV exists, the QA transcript exists, and a human reviewer approves the package",
            readme,
        )
        self.assertIn("## Workflow Glossary", readme)
        self.assertIn("Workflow phase:", readme)
        self.assertIn("Review decision:", readme)
        self.assertIn("Audio freshness:", readme)
        self.assertIn("promote-audio", readme)
        self.assertIn("March 30, 2026 Challenger", readme)
        self.assertIn('ReviewDesk["single /review inbox<br/>visual research / audio / scene / packaging / motion"]', diagram)
        self.assertIn('AudioGate{"audio approval approved<br/>and freshness current?"}', diagram)
        self.assertIn("PromoteAudio[\"ce-orchestrate promote-audio\"]", diagram)
        self.assertIn("FinalAudio --> PromoteAudio", diagram)
        self.assertIn("Transcript --> PromoteAudio", diagram)
        self.assertIn("PromoteAudio --> ReviewDesk", diagram)
        self.assertIn("AudioGate -->|approved| AssemblyReady", diagram)

    def test_audio_ready_for_review_resolves_to_review_and_next_action_is_approve(self) -> None:
        manifest = self._build_ready_for_assembly_manifest()
        manifest["audio"]["review"]["status"] = "pending"
        manifest["audio"]["status"] = "todo"
        state = derive_episode_state(manifest, self.context)
        self.assertEqual(state["lanes"]["audio"]["status"], "review")
        self.assertEqual(state["lanes"]["audio"]["review_status"], "pending")
        self.assertEqual(state["lanes"]["audio"]["package_sync_status"], "unknown")
        self.assertTrue(state["lanes"]["audio"]["review_actionable"])
        self.assertEqual(state["next_action"]["lane"], "audio")
        self.assertEqual(state["next_action"]["reason"], "Approve the final audio package.")

    def test_out_of_sync_audio_package_blocks_review_and_changes_next_action(self) -> None:
        manifest = self._build_ready_for_assembly_manifest()
        manifest["audio"]["review"]["status"] = "pending"
        manifest["audio"]["status"] = "review"
        pipeline_dir = Path(str(manifest["audio"]["pipeline_dir"]))
        new_transcript = pipeline_dir / "Ep99_Test.diarized.txt"
        new_transcript.write_text("new transcript", encoding="utf-8")
        self._write_audio_package_metadata(
            pipeline_dir,
            packaged_path=Path(str(manifest["audio"]["master_path"])),
            transcript_path=new_transcript,
        )

        state = derive_episode_state(manifest, self.context)

        self.assertEqual(state["lanes"]["audio"]["package_sync_status"], "out_of_sync")
        self.assertFalse(state["lanes"]["audio"]["review_actionable"])
        self.assertIn("promoted", state["lanes"]["audio"]["review_blocked_reason"])
        self.assertEqual(state["next_action"]["lane"], "audio")
        self.assertEqual(
            state["next_action"]["reason"],
            "Promote the latest packaged audio and QA transcript before continuing review.",
        )

    def test_promote_audio_updates_manifest_and_reopens_downstream_when_package_changed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = self._build_ready_for_assembly_manifest(temp_root)
            old_master = temp_root / "legacy" / "episode.wav"
            old_master.parent.mkdir(parents=True, exist_ok=True)
            old_master.write_text("old audio", encoding="utf-8")
            old_transcript = temp_root / "legacy" / "episode.diarized.txt"
            old_transcript.write_text("old transcript", encoding="utf-8")
            manifest["audio"]["master_path"] = str(old_master)
            manifest["audio"]["transcript_path"] = str(old_transcript)
            manifest["audio"]["status"] = "done"
            manifest["audio"]["review"] = {
                "status": "approved",
                "reviewer": "reviewer_1",
                "reviewed_at": "2026-03-30T18:00:00Z",
                "notes": "Approved.",
            }
            manifest["assembly"]["status"] = "done"
            manifest["assembly"]["master_video_path"] = str(temp_root / "final" / "episode.mp4")
            manifest["assembly"]["completed_at"] = "2026-03-30T18:10:00Z"
            manifest["web"]["status"] = "done"
            manifest["release"]["status"] = "done"
            manifest["release"]["scheduled_for"] = "2026-03-31T09:00:00Z"
            manifest["release"]["published_at"] = "2026-03-31T16:00:00Z"
            manifest["analytics"]["status"] = "done"
            pipeline_dir = Path(str(manifest["audio"]["pipeline_dir"]))
            packaged_path = temp_root / "packaged" / "episode.wav"
            packaged_path.parent.mkdir(parents=True, exist_ok=True)
            packaged_path.write_text("new audio", encoding="utf-8")
            transcript_path = temp_root / "packaged" / "episode.diarized.txt"
            transcript_path.write_text("new transcript", encoding="utf-8")
            self._write_audio_package_metadata(pipeline_dir, packaged_path=packaged_path, transcript_path=transcript_path)
            self._write_manifest_copy(temp_root, "challenger", manifest)

            args = type("Args", (), {"episode_id": "challenger"})()
            exit_code = command_promote_audio(context, args)

            self.assertEqual(exit_code, 0)
            updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
            self.assertEqual(updated["audio"]["master_path"], str(packaged_path))
            self.assertEqual(updated["audio"]["transcript_path"], str(transcript_path))
            self.assertEqual(updated["audio"]["status"], "review")
            self.assertEqual(updated["audio"]["review"]["status"], "pending")
            self.assertEqual(updated["assembly"]["status"], "todo")
            self.assertEqual(updated["assembly"]["master_video_path"], "")
            self.assertEqual(updated["release"]["status"], "todo")
            self.assertEqual(updated["release"]["scheduled_for"], "")
            self.assertEqual(updated["release"]["published_at"], "")
            self.assertEqual(updated["analytics"]["status"], "todo")

    def test_visual_research_brief_calls_out_opening_sequence_contract(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        brief = render_brief(self.context, manifest, "visual_research")
        self.assertIn("Fact-check target: /Users/mike/Episodes_CascadeEffects/Ep1_Challenger/fact_check.md", brief)
        self.assertIn("Contact sheet target: /Users/mike/Episodes_CascadeEffects/Ep1_Challenger/visual_research/contact_sheet.pdf", brief)
        self.assertIn("Opening object strategy: generic_era_cluster", brief)
        self.assertIn("Opening period label: January 1986", brief)
        self.assertIn("Opening subject object: Space Shuttle Challenger", brief)
        self.assertIn("Opening act/scene/motion: act1 / opening_culture_cluster / opening_subject_pull_in", brief)
        self.assertIn("Opening cue text: And it starts with a promise.", brief)
        self.assertIn("vhs_cassette:VHS cassette (supporting_object) scope=generic_mass_market renderability=common_iconic descriptor=generic black VHS cassette", brief)
        self.assertIn("boombox_radio:Cassette boombox radio (supporting_object) scope=generic_mass_market renderability=common_iconic descriptor=generic silver or black cassette boombox", brief)

    def test_challenger_opening_slot_contract_is_fully_populated(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        state = derive_episode_state(manifest, self.context)
        opening_slots = manifest["visual_research"]["opening_sequence"]["slots"]
        self.assertEqual(
            [slot["slot_id"] for slot in opening_slots],
            [
                "vhs_cassette",
                "boombox_radio",
                "high_top_sneaker",
                "aluminum_soda_can",
                "cube_puzzle",
                "beige_home_computer_crt",
                "space_shuttle_challenger",
            ],
        )
        self.assertEqual(manifest["visual_research"]["opening_sequence"]["object_strategy"], "generic_era_cluster")
        self.assertTrue(state["lanes"]["visual_research"]["opening_slot_contract_enabled"])
        self.assertTrue(state["lanes"]["visual_research"]["opening_slot_assignment_complete"])
        self.assertEqual(state["lanes"]["visual_research"]["guardrails"]["missing_opening_slot_ids"], [])
        self.assertEqual(state["lanes"]["visual_research"]["guardrails"]["opening_slot_candidate_totals"]["space_shuttle_challenger"], 2)
        self.assertEqual(state["lanes"]["visual_research"]["guardrails"]["opening_candidate_total"], 8)
        self.assertEqual(state["lanes"]["visual_research"]["guardrails"]["act_candidate_totals"]["act1"], 8)

    def test_challenger_opening_render_payload_uses_ordered_slot_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
            self._prepare_visual_research_fixture(manifest, temp_root)
            overrides = _opening_scene_render_overrides(manifest, "opening_culture_cluster")
            payload = overrides["opening_payload"]
            self.assertEqual(payload["subject_slot_id"], "space_shuttle_challenger")
            self.assertEqual(
                [slot["slot_id"] for slot in payload["slots"]],
                [
                    "vhs_cassette",
                    "boombox_radio",
                    "high_top_sneaker",
                    "aluminum_soda_can",
                    "cube_puzzle",
                    "beige_home_computer_crt",
                    "space_shuttle_challenger",
                ],
            )
            self.assertTrue(
                all(
                    str(slot["asset_path"]).startswith(str(temp_root / "visual_research" / "research_assets"))
                    and Path(str(slot["asset_path"])).exists()
                    for slot in payload["slots"]
                )
            )
            self.assertIn("central dominant subject isolated for the pull-in", overrides["opening_anchor_fragment"])
            self.assertIn("VHS cassette", overrides["opening_required_reads"])

    def test_render_scene_fails_fast_after_scene_still_workflow_retirement(self) -> None:
        manifest = self._build_ready_for_assembly_manifest()
        opening_item = next(item for item in manifest["scene_stills"]["items"] if item["id"] == "opening_culture_cluster")
        opening_item["review_status"] = "pending"
        opening_item["selected_asset"] = ""
        with self.assertRaises(SystemExit) as exc:
            render_scene_still(self.context, manifest, "routine_console_wide")
        self.assertIn("scene_still workflow family is retired", str(exc.exception))

    def test_render_scene_retirement_does_not_call_viz_renderer(self) -> None:
        manifest = self._build_ready_for_assembly_manifest()
        manifest["visual_research"]["opening_sequence"]["block_downstream_until_approved"] = False
        opening_item = next(item for item in manifest["scene_stills"]["items"] if item["id"] == "opening_culture_cluster")
        opening_item["review_status"] = "pending"
        opening_item["selected_asset"] = ""
        with mock.patch(
            "orchestration.stills._render_viz_manifest",
            return_value=(Path("/tmp/routine_console_wide.png"), Path("/tmp/routine_console_wide.run.json")),
        ) as render_mock:
            with self.assertRaises(SystemExit) as exc:
                render_scene_still(self.context, manifest, "routine_console_wide")
        self.assertIn("short-specific still lanes", str(exc.exception))
        render_mock.assert_not_called()

    def test_scene_brief_includes_opening_tableau_review_checklist(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
        brief = render_brief(self.context, manifest, "scene_stills")
        self.assertIn("Opening tableau review checklist:", brief)
        self.assertIn("visible read: VHS cassette (supporting_object)", brief)
        self.assertIn("visible read: Space Shuttle Challenger (subject_object)", brief)
        self.assertIn("Challenger must be the largest and most central read.", brief)

    def test_web_brief_distinguishes_archive_entry_from_homepage_visibility(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/hyatt-regency.toml")
        brief = render_brief(self.context, manifest, "web")
        self.assertIn("Launch archive entry exists: yes", brief)
        self.assertIn("Homepage visible now: no", brief)

    def test_motion_brief_includes_behavior_and_opening_target(self) -> None:
        manifest = self._build_ready_for_assembly_manifest()
        source_still = next(item for item in manifest["scene_stills"]["items"] if item["id"] == "launch_commit_console")
        source_still["approved_proof_path"] = ""
        source_still["approved_proof_manifest_path"] = ""
        brief = render_brief(self.context, manifest, "motion_assets")
        self.assertIn("Opening sequence motion target: opening_subject_pull_in", brief)
        self.assertIn("behavior=Other period objects clear from frame as Challenger takes focus and blasts off.", brief)
        self.assertIn("source=launch_commit_console", brief)
        self.assertNotIn("No stills are approved for motion yet.", brief)

    def test_motion_brief_includes_approved_proof_backed_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest = self._build_ready_for_assembly_manifest(temp_root)
            source_still = next(item for item in manifest["scene_stills"]["items"] if item["id"] == "launch_commit_console")
            approved_proof = temp_root / "review_approved.png"
            approved_proof.write_text("proof", encoding="utf-8")
            approved_proof_manifest = Path(f"{approved_proof}.json")
            approved_proof_manifest.write_text("{}", encoding="utf-8")
            source_still["approved_proof_path"] = str(approved_proof)
            source_still["approved_proof_manifest_path"] = str(approved_proof_manifest)
            source_still["selected_asset"] = ""

            brief = render_brief(self.context, manifest, "motion_assets")

            self.assertIn("Opening sequence motion target: opening_subject_pull_in", brief)
            self.assertIn("source=launch_commit_console", brief)
            self.assertIn("behavior=Other period objects clear from frame as Challenger takes focus and blasts off.", brief)
            self.assertNotIn("No stills are approved for motion yet.", brief)

    def test_motion_brief_includes_workbench_mode_and_project_path(self) -> None:
        manifest = self._build_ready_for_assembly_manifest()
        motion_item = next(item for item in manifest["motion_assets"]["items"] if item["id"] == "launch_commit_dolly")
        motion_item["authoring_mode"] = "particle_workbench"
        motion_item["workbench_project_path"] = "/Users/mike/Viz_CascadeEffects/references/episodes/challenger/launch_commit_dolly/workbench/project.json"

        brief = render_brief(self.context, manifest, "motion_assets")

        self.assertIn("mode=particle_workbench", brief)
        self.assertIn("project=/Users/mike/Viz_CascadeEffects/references/episodes/challenger/launch_commit_dolly/workbench/project.json", brief)

    def test_motion_brief_includes_compositing_prompt_guidance_for_overlay_fx(self) -> None:
        manifest = self._build_ready_for_assembly_manifest()
        motion_item = next(item for item in manifest["motion_assets"]["items"] if item["id"] == "launch_commit_dolly")
        motion_item["authoring_mode"] = "particle_workbench"
        motion_item["output_path"] = motion_item["output_path"].replace(".mp4", ".mov")
        Path(motion_item["output_path"]).write_text("overlay", encoding="utf-8")
        manifest["assembly"]["compositions"] = [
            {
                "act_id": "act3",
                "base_asset_id": "launch_commit_console",
                "overlays": [
                    {
                        "motion_asset_id": "launch_commit_dolly",
                        "start_seconds": 0.5,
                        "duration_seconds": 2.0,
                        "blend_mode": "normal",
                    }
                ],
            }
        ]

        brief = render_brief(self.context, materialize_episode_manifest(self.context, manifest), "motion_assets")

        self.assertIn("role=overlay_fx", brief)
        self.assertIn("Compositing-first prompt contract:", brief)
        self.assertIn("Render only the plume or event element as an isolated overlay", brief)

    def test_set_scene_archetype_populates_episode_owned_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest_path = temp_root / "hyatt-regency.toml"
            manifest_path.write_text((ROOT / "episodes/hyatt-regency.toml").read_text(encoding="utf-8"), encoding="utf-8")
            manifest = load_episode_manifest(manifest_path)
            with mock.patch("orchestration.cli.resolve_target_manifests", return_value=[manifest]):
                with mock.patch("sys.stdout", new=io.StringIO()):
                    exit_code = command_set_scene_archetype(
                        self.context,
                        type(
                            "Args",
                            (),
                            {
                                "episode_id": "hyatt-regency",
                                "scene_item_id": "primary_scene_hero",
                                "archetype_id": "challenger_mission_control",
                            },
                        )(),
                    )
            self.assertEqual(exit_code, 0)
            updated = load_episode_manifest(manifest_path)
            scene_item = next(item for item in updated["scene_stills"]["items"] if item["id"] == "primary_scene_hero")
            motion_item = updated["motion_assets"]["items"][0]
            self.assertEqual(scene_item["archetype_status"], "resolved")
            self.assertEqual(scene_item["preset"], "challenger_mission_control")
            self.assertEqual(
                scene_item["output_path"],
                "/Users/mike/Viz_CascadeEffects/references/episodes/hyatt-regency/primary_scene_hero/selects/hero_still.png",
            )
            self.assertEqual(
                motion_item["output_path"],
                "/Users/mike/Viz_CascadeEffects/references/episodes/hyatt-regency/primary_scene_hero/selects/hero_video.mp4",
            )

    def test_render_scene_fails_when_archetype_is_unresolved(self) -> None:
        manifest = load_episode_manifest(ROOT / "episodes/hyatt-regency.toml")
        with mock.patch("orchestration.cli.resolve_target_manifests", return_value=[manifest]):
            with self.assertRaises(SystemExit) as exc:
                command_render_scene(
                    self.context,
                    type("Args", (), {"episode_id": "hyatt-regency", "scene_item_id": "primary_scene_hero"})(),
                )
        self.assertIn("scene_still workflow family is retired", str(exc.exception))

    def test_render_packaging_updates_latest_render_without_scene_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest_path = temp_root / "hyatt-regency.toml"
            manifest_path.write_text((ROOT / "episodes/hyatt-regency.toml").read_text(encoding="utf-8"), encoding="utf-8")
            manifest = load_episode_manifest(manifest_path)
            proof_image = temp_root / "thumbnail.png"
            proof_image.write_text("image", encoding="utf-8")
            pipeline_manifest = temp_root / "pipeline.run.json"
            pipeline_manifest.write_text(
                json.dumps(
                    {
                        "final_outputs": [str(proof_image)],
                        "stage_validations": {
                            "visual_qc": {
                                "status": "ok",
                                "audit_manifest": str(temp_root / "visual_qc.run.json"),
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            (temp_root / "visual_qc.run.json").write_text("{}", encoding="utf-8")
            with (
                mock.patch("orchestration.cli.resolve_target_manifests", return_value=[manifest]),
                mock.patch(
                    "orchestration.stills.run_checked_command",
                    return_value=f"INFO  pipeline manifest -> {pipeline_manifest}",
                ),
            ):
                with mock.patch("sys.stdout", new=io.StringIO()):
                    exit_code = command_render_packaging(
                        self.context,
                        type("Args", (), {"episode_id": "hyatt-regency", "item_id": "primary_thumbnail"})(),
                    )
            self.assertEqual(exit_code, 0)
            updated = load_episode_manifest(manifest_path)
            packaging_item = updated["packaging_stills"]["items"][0]
            self.assertEqual(packaging_item["latest_render_path"], str(proof_image))
            self.assertEqual(packaging_item["latest_render_manifest_path"], str(pipeline_manifest))
            self.assertEqual(updated["packaging_stills"]["status"], "review")

    def test_render_scene_clears_approved_proof_and_reopens_motion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest_path = temp_root / "challenger.toml"
            manifest = self._build_ready_for_assembly_manifest(temp_root)
            scene_item = next(item for item in manifest["scene_stills"]["items"] if item["id"] == "launch_commit_console")
            approved_proof = temp_root / "approved-proof.png"
            approved_proof.write_text("proof", encoding="utf-8")
            Path(f"{approved_proof}.json").write_text("{}", encoding="utf-8")
            scene_item["approved_proof_path"] = str(approved_proof)
            scene_item["approved_proof_manifest_path"] = f"{approved_proof}.json"
            scene_item["selected_asset"] = str(temp_root / "selected.png")
            Path(scene_item["selected_asset"]).write_text("selected", encoding="utf-8")
            Path(f"{scene_item['selected_asset']}.json").write_text("{}", encoding="utf-8")
            scene_item["review_status"] = "approved"
            scene_item["motion_review_status"] = "approved_for_motion"
            next(item for item in manifest["motion_assets"]["items"] if item["id"] == "launch_commit_dolly")["status"] = "done"
            original_latest_render_path = scene_item["latest_render_path"]
            original_latest_render_manifest_path = scene_item["latest_render_manifest_path"]
            write_episode_manifest(manifest_path, manifest)
            manifest = load_episode_manifest(manifest_path)
            proof_image = temp_root / "review-proof.png"
            proof_image.write_text("image", encoding="utf-8")
            pipeline_manifest = temp_root / "review-proof.run.json"
            pipeline_manifest.write_text(
                json.dumps(
                    {
                        "final_outputs": [str(proof_image)],
                        "stage_validations": {
                            "visual_qc": {
                                "status": "ok",
                                "audit_manifest": str(temp_root / "visual_qc.run.json"),
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            (temp_root / "visual_qc.run.json").write_text("{}", encoding="utf-8")
            with (
                mock.patch("orchestration.cli.resolve_target_manifests", return_value=[manifest]),
                mock.patch(
                    "orchestration.stills.run_checked_command",
                    return_value=f"INFO  pipeline manifest -> {pipeline_manifest}",
                ) as run_mock,
            ):
                with mock.patch("sys.stdout", new=io.StringIO()):
                    with self.assertRaises(SystemExit) as exc:
                        command_render_scene(
                            self.context,
                            type("Args", (), {"episode_id": "challenger", "scene_item_id": "launch_commit_console"})(),
                        )
            self.assertIn("scene_still workflow family is retired", str(exc.exception))
            run_mock.assert_not_called()
            updated = load_episode_manifest(manifest_path)
            scene_item = next(item for item in updated["scene_stills"]["items"] if item["id"] == "launch_commit_console")
            motion_item = next(item for item in updated["motion_assets"]["items"] if item["id"] == "launch_commit_dolly")
            self.assertEqual(scene_item["latest_render_path"], original_latest_render_path)
            self.assertEqual(scene_item["latest_render_manifest_path"], original_latest_render_manifest_path)
            self.assertEqual(scene_item["approved_proof_path"], str(approved_proof))
            self.assertEqual(scene_item["approved_proof_manifest_path"], f"{approved_proof}.json")
            self.assertEqual(scene_item["selected_asset"], str(temp_root / "selected.png"))
            self.assertEqual(scene_item["review_status"], "approved")
            self.assertEqual(scene_item["motion_review_status"], "approved_for_motion")
            self.assertEqual(motion_item["status"], "done")

    def test_finalize_scene_promotes_finalized_asset_without_overwriting_review_proof(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest_path = temp_root / "challenger.toml"
            manifest = self._build_ready_for_assembly_manifest(temp_root)
            scene_item = next(item for item in manifest["scene_stills"]["items"] if item["id"] == "launch_commit_console")
            approved_proof = temp_root / "review_approved.png"
            approved_proof.write_text("proof", encoding="utf-8")
            Path(f"{approved_proof}.json").write_text("{}", encoding="utf-8")
            scene_item["approved_proof_path"] = str(approved_proof)
            scene_item["approved_proof_manifest_path"] = f"{approved_proof}.json"
            scene_item["selected_asset"] = ""
            scene_item["latest_render_path"] = str(temp_root / "latest-proof.png")
            scene_item["latest_render_manifest_path"] = str(temp_root / "latest-proof.run.json")
            scene_item["review_status"] = "approved"
            scene_item["output_path"] = str(temp_root / "canonical" / "hero_still.png")
            write_episode_manifest(manifest_path, manifest)
            manifest = load_episode_manifest(manifest_path)
            final_image = temp_root / "finalized.png"
            final_image.write_text("final", encoding="utf-8")
            finalize_manifest = temp_root / "finalize-still.run.json"
            finalize_manifest.write_text(
                json.dumps(
                    {
                        "final_outputs": [str(final_image)],
                        "stage_validations": {
                            "visual_qc": {
                                "status": "ok",
                                "audit_manifest": str(temp_root / "visual_qc.run.json"),
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            (temp_root / "visual_qc.run.json").write_text("{}", encoding="utf-8")
            with (
                mock.patch("orchestration.cli.resolve_target_manifests", return_value=[manifest]),
                mock.patch(
                    "orchestration.stills.run_checked_command",
                    return_value=f"INFO  pipeline manifest -> {finalize_manifest}",
                ) as run_mock,
            ):
                with mock.patch("sys.stdout", new=io.StringIO()):
                    with self.assertRaises(SystemExit) as exc:
                        command_finalize_scene(
                            self.context,
                            type("Args", (), {"episode_id": "challenger", "scene_item_id": "launch_commit_console"})(),
                        )
            self.assertIn("scene_still workflow family is retired", str(exc.exception))
            run_mock.assert_not_called()
            updated = load_episode_manifest(manifest_path)
            scene_item = next(item for item in updated["scene_stills"]["items"] if item["id"] == "launch_commit_console")
            self.assertEqual(scene_item["approved_proof_path"], str(approved_proof))
            self.assertEqual(scene_item["latest_render_path"], str(temp_root / "latest-proof.png"))
            self.assertEqual(scene_item["selected_asset"], "")

    def test_promote_scene_copies_asset_and_manifest_to_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest_path = temp_root / "therac-25.toml"
            manifest = load_episode_manifest(ROOT / "episodes/therac-25.toml")
            manifest["scene_stills"]["items"][0]["output_path"] = str(temp_root / "canonical" / "hero_still.png")
            manifest["scene_stills"]["items"][0]["latest_render_path"] = str(temp_root / "review.png")
            manifest["scene_stills"]["items"][0]["latest_render_manifest_path"] = str(temp_root / "pipeline.run.json")
            manifest["scene_stills"]["items"][0]["review_status"] = "pending"
            from orchestration.io import write_episode_manifest

            write_episode_manifest(manifest_path, manifest)
            manifest = load_episode_manifest(manifest_path)
            proof_asset = Path(manifest["scene_stills"]["items"][0]["latest_render_path"])
            proof_asset.write_text("image", encoding="utf-8")
            proof_manifest = Path(manifest["scene_stills"]["items"][0]["latest_render_manifest_path"])
            proof_manifest.write_text(
                json.dumps(
                    {
                        "final_outputs": [str(proof_asset)],
                        "stage_validations": {
                            "visual_qc": {
                                "status": "ok",
                                "audit_manifest": str(temp_root / "visual_qc.run.json"),
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            (temp_root / "visual_qc.run.json").write_text("{}", encoding="utf-8")
            with mock.patch("orchestration.cli.resolve_target_manifests", return_value=[manifest]):
                with mock.patch("sys.stdout", new=io.StringIO()):
                    exit_code = command_promote_scene(
                        self.context,
                        type(
                            "Args",
                            (),
                            {
                                "episode_id": "therac-25",
                                "scene_item_id": "console_alarm_hero",
                                "asset": str(proof_asset),
                            },
                        )(),
                    )
            self.assertEqual(exit_code, 0)
            updated = load_episode_manifest(manifest_path)
            scene_item = updated["scene_stills"]["items"][0]
            self.assertEqual(scene_item["review_status"], "approved")
            self.assertTrue(Path(scene_item["selected_asset"]).exists())
            self.assertTrue(Path(f"{scene_item['selected_asset']}.json").exists())

    def test_promote_scene_rejects_missing_visual_qc(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest_path = temp_root / "therac-25.toml"
            manifest = load_episode_manifest(ROOT / "episodes/therac-25.toml")
            manifest["scene_stills"]["items"][0]["output_path"] = str(temp_root / "canonical" / "hero_still.png")
            manifest["scene_stills"]["items"][0]["latest_render_path"] = str(temp_root / "review.png")
            manifest["scene_stills"]["items"][0]["latest_render_manifest_path"] = str(temp_root / "pipeline.run.json")
            from orchestration.io import write_episode_manifest

            write_episode_manifest(manifest_path, manifest)
            manifest = load_episode_manifest(manifest_path)
            proof_asset = Path(manifest["scene_stills"]["items"][0]["latest_render_path"])
            proof_asset.write_text("image", encoding="utf-8")
            proof_manifest = Path(manifest["scene_stills"]["items"][0]["latest_render_manifest_path"])
            proof_manifest.write_text(json.dumps({"final_outputs": [str(proof_asset)]}), encoding="utf-8")
            with mock.patch("orchestration.cli.resolve_target_manifests", return_value=[manifest]):
                with self.assertRaises(SystemExit) as exc:
                    command_promote_scene(
                        self.context,
                        type(
                            "Args",
                            (),
                            {
                                "episode_id": "therac-25",
                                "scene_item_id": "console_alarm_hero",
                                "asset": str(proof_asset),
                            },
                        )(),
                    )
            self.assertIn("stage_validations", str(exc.exception))

    def test_render_motion_uses_mocked_handoff_flow_and_updates_manifest_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest_path, manifest = self._write_ready_for_assembly_manifest(temp_root)
            manifest["motion_assets"]["status"] = "todo"
            next(item for item in manifest["motion_assets"]["items"] if item["id"] == "launch_commit_dolly")["status"] = "todo"
            write_episode_manifest(manifest_path, manifest)
            manifest = load_episode_manifest(manifest_path)
            proof_video = temp_root / "proof.mp4"
            proof_video.write_text("video", encoding="utf-8")
            video_manifest = temp_root / "proof.mp4.json"
            video_manifest.write_text(json.dumps({"output_path": str(proof_video), "duration_seconds": 5.5}), encoding="utf-8")
            with (
                mock.patch("orchestration.cli.resolve_target_manifests", return_value=[manifest]),
                mock.patch("orchestration.motion.run_checked_command") as run_checked_command,
                mock.patch("orchestration.motion.preflight_motion_source_asset", return_value=(temp_root / "preflight.png", {"status": "cleaned"})),
            ):
                run_checked_command.side_effect = [
                    f"INFO  Staged asset: {temp_root / 'staged.png'}",
                    f"INFO  Handoff video manifest: {video_manifest}",
                ]
                with mock.patch("sys.stdout", new=io.StringIO()):
                    exit_code = command_render_motion(
                        self.context,
                        type("Args", (), {"episode_id": "challenger", "motion_item_id": "launch_commit_dolly"})(),
                    )
            self.assertEqual(exit_code, 0)
            stage_args = run_checked_command.call_args_list[0].args[0]
            self.assertEqual(stage_args[2], str(temp_root / "preflight.png"))
            prompt_value = stage_args[stage_args.index("--prompt") + 1]
            self.assertIn(
                next(item for item in manifest["motion_assets"]["items"] if item["id"] == "launch_commit_dolly")["behavior"],
                prompt_value,
            )
            updated = load_episode_manifest(manifest_path)
            motion_item = next(item for item in updated["motion_assets"]["items"] if item["id"] == "launch_commit_dolly")
            self.assertEqual(motion_item["status"], "review")
            self.assertEqual(motion_item["latest_render_path"], str(proof_video))
            self.assertEqual(motion_item["latest_render_manifest_path"], str(video_manifest))

    def test_render_motion_with_ready_helper_never_writes_back_to_tracked_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            tracked_manifest_path = ROOT / "episodes/challenger.toml"
            tracked_before = tracked_manifest_path.read_text(encoding="utf-8")
            manifest = self._build_ready_for_assembly_manifest(temp_root)
            self.assertEqual(Path(str(manifest["_manifest_path"])), temp_root / "challenger.toml")
            self.assertNotEqual(Path(str(manifest["_manifest_path"])), tracked_manifest_path)
            manifest["motion_assets"]["status"] = "todo"
            next(item for item in manifest["motion_assets"]["items"] if item["id"] == "launch_commit_dolly")["status"] = "todo"
            proof_video = temp_root / "proof.mp4"
            proof_video.write_text("video", encoding="utf-8")
            video_manifest = temp_root / "proof.mp4.json"
            video_manifest.write_text(json.dumps({"output_path": str(proof_video), "duration_seconds": 5.5}), encoding="utf-8")

            with (
                mock.patch("orchestration.cli.resolve_target_manifests", return_value=[manifest]),
                mock.patch("orchestration.motion.run_checked_command") as run_checked_command,
                mock.patch("orchestration.motion.preflight_motion_source_asset", return_value=(temp_root / "preflight.png", {"status": "cleaned"})),
            ):
                run_checked_command.side_effect = [
                    f"INFO  Staged asset: {temp_root / 'staged.png'}",
                    f"INFO  Handoff video manifest: {video_manifest}",
                ]
                with mock.patch("sys.stdout", new=io.StringIO()):
                    exit_code = command_render_motion(
                        self.context,
                        type("Args", (), {"episode_id": "challenger", "motion_item_id": "launch_commit_dolly"})(),
                    )

            self.assertEqual(exit_code, 0)
            self.assertEqual(tracked_manifest_path.read_text(encoding="utf-8"), tracked_before)
            persisted = load_episode_manifest(temp_root / "challenger.toml")
            motion_item = next(item for item in persisted["motion_assets"]["items"] if item["id"] == "launch_commit_dolly")
            self.assertEqual(motion_item["status"], "review")
            self.assertEqual(motion_item["latest_render_path"], str(proof_video))
            self.assertEqual(motion_item["latest_render_manifest_path"], str(video_manifest))

    def test_render_motion_dispatches_to_workbench_export_for_workbench_items(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest_path, manifest = self._write_ready_for_assembly_manifest(temp_root)
            motion_item = next(item for item in manifest["motion_assets"]["items"] if item["id"] == "launch_commit_dolly")
            motion_item["authoring_mode"] = "particle_workbench"
            motion_item["workbench_project_path"] = str(temp_root / "workbench" / "project.json")
            Path(motion_item["workbench_project_path"]).parent.mkdir(parents=True, exist_ok=True)
            Path(motion_item["workbench_project_path"]).write_text("{}", encoding="utf-8")
            write_episode_manifest(manifest_path, manifest)
            manifest = load_episode_manifest(manifest_path)
            proof_video = temp_root / "proof.mp4"
            proof_video.write_text("video", encoding="utf-8")
            video_manifest = temp_root / "proof.mp4.json"
            video_manifest.write_text(
                json.dumps(
                    {
                        "output_path": str(proof_video),
                        "manifest_path": str(video_manifest),
                        "duration_seconds": 5.0,
                    }
                ),
                encoding="utf-8",
            )
            with (
                mock.patch("orchestration.cli.resolve_target_manifests", return_value=[manifest]),
                mock.patch("orchestration.motion.run_checked_command", return_value=video_manifest.read_text(encoding="utf-8")) as run_checked_command,
            ):
                with mock.patch("sys.stdout", new=io.StringIO()):
                    exit_code = command_render_motion(
                        self.context,
                        type("Args", (), {"episode_id": "challenger", "motion_item_id": "launch_commit_dolly"})(),
                    )

            self.assertEqual(exit_code, 0)
            workbench_args = run_checked_command.call_args.args[0]
            self.assertEqual(workbench_args[1:3], ["workbench", "export-shot"])
            self.assertIn("--project", workbench_args)
            self.assertIn(str(temp_root / "workbench" / "project.json"), workbench_args)
            updated = load_episode_manifest(manifest_path)
            updated_item = next(item for item in updated["motion_assets"]["items"] if item["id"] == "launch_commit_dolly")
            self.assertEqual(updated_item["latest_render_path"], str(proof_video))
            self.assertEqual(updated_item["latest_render_manifest_path"], str(video_manifest))
            self.assertEqual(updated_item["status"], "review")

    def test_render_motion_adds_alpha_for_workbench_overlay_items(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest_path, manifest = self._write_ready_for_assembly_manifest(temp_root)
            motion_item = next(item for item in manifest["motion_assets"]["items"] if item["id"] == "launch_commit_dolly")
            motion_item["authoring_mode"] = "particle_workbench"
            motion_item["workbench_project_path"] = str(temp_root / "workbench" / "project.json")
            Path(motion_item["workbench_project_path"]).parent.mkdir(parents=True, exist_ok=True)
            Path(motion_item["workbench_project_path"]).write_text("{}", encoding="utf-8")
            manifest["assembly"]["compositions"] = [
                {
                    "act_id": "act3",
                    "base_asset_id": "launch_commit_console",
                    "overlays": [
                        {
                            "motion_asset_id": "launch_commit_dolly",
                            "start_seconds": 0.25,
                            "duration_seconds": 1.5,
                            "blend_mode": "normal",
                        }
                    ],
                }
            ]
            write_episode_manifest(manifest_path, manifest)
            manifest = load_episode_manifest(manifest_path)
            proof_video = temp_root / "proof.mov"
            proof_video.write_text("video", encoding="utf-8")
            video_manifest = temp_root / "proof.mov.json"
            video_manifest.write_text(
                json.dumps(
                    {
                        "output_path": str(proof_video),
                        "manifest_path": str(video_manifest),
                        "duration_seconds": 5.0,
                    }
                ),
                encoding="utf-8",
            )
            with (
                mock.patch("orchestration.cli.resolve_target_manifests", return_value=[manifest]),
                mock.patch("orchestration.motion.run_checked_command", return_value=video_manifest.read_text(encoding="utf-8")) as run_checked_command,
            ):
                with mock.patch("sys.stdout", new=io.StringIO()):
                    exit_code = command_render_motion(
                        self.context,
                        type("Args", (), {"episode_id": "challenger", "motion_item_id": "launch_commit_dolly"})(),
                    )

            self.assertEqual(exit_code, 0)
            workbench_args = run_checked_command.call_args.args[0]
            self.assertIn("--alpha", workbench_args)
            updated = load_episode_manifest(manifest_path)
            updated_item = next(item for item in updated["motion_assets"]["items"] if item["id"] == "launch_commit_dolly")
            self.assertTrue(updated_item["output_path"].endswith(".mov"))

    def test_render_motion_prefers_approved_proof_over_selected_asset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest_path, manifest = self._write_ready_for_assembly_manifest(temp_root)
            scene_item = next(item for item in manifest["scene_stills"]["items"] if item["id"] == "launch_commit_console")
            approved_proof = temp_root / "review_approved.png"
            selected_asset = temp_root / "selected.png"
            approved_proof.write_text("proof", encoding="utf-8")
            selected_asset.write_text("selected", encoding="utf-8")
            scene_item["approved_proof_path"] = str(approved_proof)
            scene_item["approved_proof_manifest_path"] = str(temp_root / "review_approved.png.json")
            Path(scene_item["approved_proof_manifest_path"]).write_text("{}", encoding="utf-8")
            scene_item["selected_asset"] = str(selected_asset)
            write_episode_manifest(manifest_path, manifest)
            manifest = load_episode_manifest(manifest_path)
            proof_video = temp_root / "proof.mp4"
            proof_video.write_text("video", encoding="utf-8")
            video_manifest = temp_root / "proof.mp4.json"
            video_manifest.write_text(json.dumps({"output_path": str(proof_video), "duration_seconds": 5.5}), encoding="utf-8")
            with (
                mock.patch("orchestration.cli.resolve_target_manifests", return_value=[manifest]),
                mock.patch("orchestration.motion.run_checked_command") as run_checked_command,
                mock.patch("orchestration.motion.preflight_motion_source_asset", return_value=(temp_root / "preflight.png", {"status": "ok"})) as preflight,
            ):
                run_checked_command.side_effect = [
                    f"INFO  Staged asset: {temp_root / 'staged.png'}",
                    f"INFO  Handoff video manifest: {video_manifest}",
                ]
                with mock.patch("sys.stdout", new=io.StringIO()):
                    exit_code = command_render_motion(
                        self.context,
                        type("Args", (), {"episode_id": "challenger", "motion_item_id": "launch_commit_dolly"})(),
                    )
            self.assertEqual(exit_code, 0)
            self.assertEqual(preflight.call_args.kwargs["selected_asset_path"], approved_proof)

    def test_process_research_sources_updates_inventory_and_returns_nonzero_when_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest_path = temp_root / "challenger.toml"
            manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
            inventory_path = temp_root / "source_inventory.json"
            raw_clear = temp_root / "clear.png"
            raw_blocked = temp_root / "blocked.png"
            raw_clear.write_text("clear", encoding="utf-8")
            raw_blocked.write_text("blocked", encoding="utf-8")
            write_source_inventory(
                inventory_path,
                {
                    "schema_version": 1,
                    "sources": [
                        {
                            "source_id": "source_clear",
                            "act_id": "act1",
                            "raw_asset_path": str(raw_clear),
                            "board_asset_path": "",
                            "approved_for_generation": True,
                            "text_status": "needs_cleanup",
                            "text_detection_manifest_path": "",
                            "cleanup_manifest_path": "",
                            "cleaned_asset_path": "",
                            "downstream_asset_path": "",
                            "notes": "",
                        },
                        {
                            "source_id": "source_blocked",
                            "act_id": "act1",
                            "raw_asset_path": str(raw_blocked),
                            "board_asset_path": "",
                            "approved_for_generation": True,
                            "text_status": "needs_cleanup",
                            "text_detection_manifest_path": "",
                            "cleanup_manifest_path": "",
                            "cleaned_asset_path": "",
                            "downstream_asset_path": "",
                            "notes": "",
                        },
                    ],
                },
            )
            manifest["visual_research"]["source_inventory_path"] = str(inventory_path)
            write_episode_manifest(manifest_path, manifest)
            manifest = load_episode_manifest(manifest_path)

            def fake_process(_context: Context, *, artifact_path: Path, output_path: Path, debug_dir: Path, policy_path: Path | None) -> dict[str, object]:
                self.assertIsNotNone(policy_path)
                if artifact_path == raw_clear:
                    return {
                        "status": "clear",
                        "text_detection_manifest_path": str(debug_dir / "clear-audit.json"),
                        "cleanup_manifest_path": "",
                        "output_artifact": "",
                        "blocked_reason": "",
                    }
                return {
                    "status": "blocked",
                    "text_detection_manifest_path": str(debug_dir / "blocked-audit.json"),
                    "cleanup_manifest_path": str(debug_dir / "cleanup.json"),
                    "output_artifact": str(output_path),
                    "blocked_reason": "Residual readable text remains after cleanup.",
                }

            with (
                mock.patch("orchestration.cli.resolve_target_manifests", return_value=[manifest]),
                mock.patch("orchestration.research_sources.process_source_artifact_with_viz", side_effect=fake_process),
                mock.patch("sys.stdout", new=io.StringIO()),
            ):
                exit_code = command_process_research_sources(
                    self.context,
                    type("Args", (), {"episode_id": "challenger"})(),
                )

            self.assertEqual(exit_code, 1)
            updated_inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
            source_clear = next(item for item in updated_inventory["sources"] if item["source_id"] == "source_clear")
            source_blocked = next(item for item in updated_inventory["sources"] if item["source_id"] == "source_blocked")
            self.assertEqual(source_clear["text_status"], "clear")
            self.assertEqual(source_clear["downstream_asset_path"], str(raw_clear))
            self.assertEqual(source_blocked["text_status"], "blocked")
            self.assertEqual(source_blocked["downstream_asset_path"], "")

    def test_write_episode_manifest_round_trips_multiline_review_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest_path = temp_root / "challenger.toml"
            manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
            multiline_notes = 'There is a floating "45" overlay.\n\nAlso, one head is blurred.'
            manifest["motion_assets"]["items"][0]["review_notes"] = multiline_notes
            write_episode_manifest(manifest_path, manifest)
            updated = load_episode_manifest(manifest_path)
            self.assertEqual(updated["motion_assets"]["items"][0]["review_notes"], multiline_notes)

    def test_write_episode_manifest_round_trips_opening_sequence_and_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest_path = temp_root / "challenger.toml"
            manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["opening_sequence"]["object_strategy"] = "generic_era_cluster"
            manifest["visual_research"]["opening_sequence"]["supporting_objects"] = ["VHS cassette", "Cassette boombox radio"]
            manifest["visual_research"]["opening_sequence"]["block_downstream_until_approved"] = False
            manifest["visual_research"]["opening_sequence"]["slots"] = [
                {
                    "slot_id": "vhs_cassette",
                    "display_label": "VHS cassette",
                    "role": "supporting_object",
                    "object_scope": "generic_mass_market",
                    "renderability": "common_iconic",
                    "visual_descriptor": "generic black VHS cassette",
                },
                {
                    "slot_id": "boombox_radio",
                    "display_label": "Cassette boombox radio",
                    "role": "supporting_object",
                    "object_scope": "generic_mass_market",
                    "renderability": "common_iconic",
                    "visual_descriptor": "generic silver or black cassette boombox",
                },
                {
                    "slot_id": "challenger",
                    "display_label": "Challenger",
                    "role": "subject_object",
                    "object_scope": "episode_specific",
                    "renderability": "common_iconic",
                    "visual_descriptor": "space shuttle stack on pad",
                },
            ]
            manifest["motion_assets"]["items"][0]["behavior"] = "Challenger takes focus and blasts off."
            write_episode_manifest(manifest_path, manifest)
            updated = load_episode_manifest(manifest_path)
            self.assertEqual(updated["visual_research"]["opening_sequence"]["object_strategy"], "generic_era_cluster")
            self.assertEqual(updated["visual_research"]["opening_sequence"]["supporting_objects"], ["VHS cassette", "Cassette boombox radio"])
            self.assertFalse(updated["visual_research"]["opening_sequence"]["block_downstream_until_approved"])
            self.assertEqual(
                updated["visual_research"]["opening_sequence"]["slots"],
                [
                    {
                        "slot_id": "vhs_cassette",
                        "display_label": "VHS cassette",
                        "role": "supporting_object",
                        "object_scope": "generic_mass_market",
                        "renderability": "common_iconic",
                        "visual_descriptor": "generic black VHS cassette",
                    },
                    {
                        "slot_id": "boombox_radio",
                        "display_label": "Cassette boombox radio",
                        "role": "supporting_object",
                        "object_scope": "generic_mass_market",
                        "renderability": "common_iconic",
                        "visual_descriptor": "generic silver or black cassette boombox",
                    },
                    {
                        "slot_id": "challenger",
                        "display_label": "Challenger",
                        "role": "subject_object",
                        "object_scope": "episode_specific",
                        "renderability": "common_iconic",
                        "visual_descriptor": "space shuttle stack on pad",
                    },
                ],
            )
            self.assertEqual(updated["motion_assets"]["items"][0]["behavior"], "Challenger takes focus and blasts off.")

    def test_promote_motion_uses_temp_manifest_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest_path = temp_root / "challenger.toml"
            manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
            manifest["motion_assets"]["items"][0]["output_path"] = str(temp_root / "canonical" / "hero_video.mp4")
            manifest["motion_assets"]["items"][0]["status"] = "review"
            from orchestration.io import write_episode_manifest

            write_episode_manifest(manifest_path, manifest)
            manifest = load_episode_manifest(manifest_path)
            proof_video = temp_root / "review.mp4"
            proof_video.write_text("video", encoding="utf-8")
            proof_manifest = temp_root / "review.mp4.json"
            proof_manifest.write_text(json.dumps({"output_path": "review", "duration_seconds": 5.5}), encoding="utf-8")
            with mock.patch("orchestration.cli.resolve_target_manifests", return_value=[manifest]):
                with mock.patch("sys.stdout", new=io.StringIO()):
                    exit_code = command_promote_motion(
                        self.context,
                        type(
                            "Args",
                            (),
                            {"episode_id": "challenger", "motion_item_id": "launch_commit_dolly", "video": str(proof_video)},
                        )(),
                    )
            self.assertEqual(exit_code, 0)
            updated = load_episode_manifest(manifest_path)
            motion_item = next(item for item in updated["motion_assets"]["items"] if item["id"] == "launch_commit_dolly")
            self.assertEqual(motion_item["status"], "done")
            self.assertTrue(Path(motion_item["output_path"]).exists())
            self.assertTrue(Path(f"{motion_item['output_path']}.json").exists())

    def test_command_assemble_updates_manifest_on_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest_path, manifest = self._write_ready_for_assembly_manifest(temp_root)
            output_path = temp_root / "final" / "challenger.mp4"

            def fake_assemble(_context: Context, _manifest: dict[str, object]) -> Path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text("video", encoding="utf-8")
                return output_path

            with (
                mock.patch("orchestration.cli.resolve_target_manifests", return_value=[manifest]),
                mock.patch("orchestration.cli.assemble_episode_cut", side_effect=fake_assemble),
            ):
                with mock.patch("sys.stdout", new=io.StringIO()):
                    exit_code = command_assemble(self.context, type("Args", (), {"episode_id": "challenger"})())
            self.assertEqual(exit_code, 0)
            updated = load_episode_manifest(manifest_path)
            self.assertEqual(updated["assembly"]["status"], "done")
            self.assertEqual(updated["assembly"]["owner"], "agent")
            self.assertEqual(updated["assembly"]["renderer"], "ffmpeg")
            self.assertEqual(updated["assembly"]["strategy"], "act_spine")
            self.assertEqual(updated["assembly"]["master_video_path"], str(output_path))
            self.assertTrue(updated["assembly"]["completed_at"])

    def test_command_assemble_fails_without_full_coverage_and_preserves_master_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest_path, manifest = self._write_ready_for_assembly_manifest(temp_root)
            manifest["visual_research"]["acts"][0]["planned_scene_ids"] = []
            write_episode_manifest(manifest_path, manifest)
            manifest = load_episode_manifest(manifest_path)
            with (
                mock.patch("orchestration.cli.resolve_target_manifests", return_value=[manifest]),
                mock.patch("orchestration.cli.assemble_episode_cut") as assemble_episode_cut,
            ):
                with self.assertRaises(SystemExit) as exc:
                    command_assemble(self.context, type("Args", (), {"episode_id": "challenger"})())
            self.assertIn("every act", str(exc.exception))
            assemble_episode_cut.assert_not_called()
            updated = load_episode_manifest(manifest_path)
            self.assertEqual(updated["assembly"]["master_video_path"], "")

    def test_review_inbox_returns_persistent_messages_and_message_detail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(ROOT / "episodes/hyatt-regency.toml")
            proof_root = temp_root / "proofs"
            proof_root.mkdir(parents=True, exist_ok=True)
            scene_selected = proof_root / "scene-approved.png"
            scene_selected.write_text("approved", encoding="utf-8")
            packaging_selected = proof_root / "thumb-approved.png"
            packaging_selected.write_text("thumb", encoding="utf-8")
            motion_proof = proof_root / "motion-proof.mp4"
            motion_proof.write_text("motion", encoding="utf-8")
            manifest["visual_research"]["status"] = "review"
            manifest["visual_research"]["approval"] = {
                "status": "pending",
                "reviewer": "",
                "reviewed_at": "",
                "notes": "",
            }
            manifest["scene_stills"]["items"][0]["selected_asset"] = str(scene_selected)
            manifest["scene_stills"]["items"][0]["review_status"] = "approved"
            manifest["scene_stills"]["items"][0]["reviewer"] = "editor_scene"
            manifest["scene_stills"]["items"][0]["reviewed_at"] = "2026-03-28T09:00:00Z"
            manifest["scene_stills"]["items"][0]["motion_review_status"] = "approved_for_motion"
            manifest["scene_stills"]["items"][0]["motion_reviewer"] = "editor_motion"
            manifest["scene_stills"]["items"][0]["motion_reviewed_at"] = "2026-03-28T10:00:00Z"
            manifest["scene_stills"]["items"][0]["motion_review_notes"] = "Approved opening focus beat."
            manifest["packaging_stills"]["items"][0]["selected_asset"] = str(packaging_selected)
            manifest["packaging_stills"]["items"][0]["review_status"] = "approved"
            manifest["packaging_stills"]["items"][0]["reviewer"] = "editor_packaging"
            manifest["packaging_stills"]["items"][0]["reviewed_at"] = "2026-03-28T11:00:00Z"
            manifest["motion_assets"]["items"][0]["latest_render_path"] = str(motion_proof)
            manifest["motion_assets"]["items"][0]["behavior"] = "Approved opening focus beat."
            manifest["motion_assets"]["items"][0]["status"] = "done"
            manifest["motion_assets"]["items"][0]["review_outcome"] = "approved"
            manifest["motion_assets"]["items"][0]["reviewer"] = "editor_video"
            manifest["motion_assets"]["items"][0]["reviewed_at"] = "2026-03-28T12:00:00Z"
            self._write_manifest_copy(temp_root, "hyatt-regency", manifest)
            inbox = build_review_inbox(context)
            self.assertEqual(inbox["episode_count"], 1)
            self.assertEqual(inbox["total_items"], 6)
            self.assertEqual(inbox["unread_count"], 1)
            self.assertEqual(inbox["default_message_id"], message_id_for("hyatt-regency", "visual_research", "visual_research"))
            self.assertEqual(inbox["gate_counts"]["visual_research"], 1)
            self.assertEqual(inbox["gate_counts"]["audio"], 1)
            self.assertEqual(inbox["gate_counts"]["motion_source"], 1)
            self.assertEqual(inbox["gate_counts"]["scene_still"], 1)
            self.assertEqual(inbox["gate_counts"]["packaging_still"], 1)
            self.assertEqual(inbox["gate_counts"]["motion_asset"], 1)
            detail = build_review_message_detail(context, inbox["default_message_id"])
            self.assertEqual(detail["message"]["message_id"], inbox["default_message_id"])
            self.assertEqual(detail["message"]["status"], "pending")
            self.assertTrue(detail["message"]["unread"])
            closed_scene = next(item for item in inbox["messages"] if item["gate_type"] == "scene_still")
            self.assertFalse(closed_scene["unread"])
            self.assertEqual(closed_scene["status"], "approved")

    def test_review_inbox_reopens_message_as_unread_when_new_proof_arrives(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(ROOT / "episodes/therac-25.toml")
            proof_root = temp_root / "proofs"
            proof_root.mkdir(parents=True, exist_ok=True)
            proof_image = proof_root / "scene.png"
            proof_image.write_text("image", encoding="utf-8")
            manifest["scene_stills"]["items"][0]["latest_render_path"] = str(proof_image)
            manifest["scene_stills"]["items"][0]["latest_render_manifest_path"] = str(proof_root / "scene.png.json")
            Path(manifest["scene_stills"]["items"][0]["latest_render_manifest_path"]).write_text(
                json.dumps({"final_outputs": [str(proof_image)]}),
                encoding="utf-8",
            )
            manifest["scene_stills"]["items"][0]["review_status"] = "pending"
            manifest["scene_stills"]["items"][0]["selected_asset"] = str(proof_root / "older-approved.png")
            Path(manifest["scene_stills"]["items"][0]["selected_asset"]).write_text("approved", encoding="utf-8")
            manifest["scene_stills"]["items"][0]["reviewer"] = ""
            manifest["scene_stills"]["items"][0]["reviewed_at"] = ""
            self._write_manifest_copy(temp_root, "therac-25", manifest)
            review_dir = temp_root / "state" / "reviews"
            review_dir.mkdir(parents=True, exist_ok=True)
            (review_dir / "therac-25.jsonl").write_text(
                json.dumps(
                    {
                        "timestamp": "2026-03-28T08:00:00Z",
                        "reviewer": "editor_one",
                        "episode_id": "therac-25",
                        "lane": "scene_stills",
                        "gate_type": "scene_still",
                        "item_id": "console_alarm_hero",
                        "decision": "approve",
                        "notes": "Approved.",
                        "before": {"id": "console_alarm_hero"},
                        "after": {"id": "console_alarm_hero", "purpose": "Console alarm hero"},
                        "proof_path": str(proof_image),
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            inbox = build_review_inbox(context)
            scene_message = next(item for item in inbox["messages"] if item["gate_type"] == "scene_still")
            self.assertTrue(scene_message["unread"])
            self.assertEqual(scene_message["status"], "pending")

    def test_load_review_history_returns_newest_first_normalized_events(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            review_dir = temp_root / "state" / "reviews"
            review_dir.mkdir(parents=True, exist_ok=True)
            proof_path = temp_root / "proofs" / "scene.png"
            proof_path.parent.mkdir(parents=True, exist_ok=True)
            proof_path.write_text("image", encoding="utf-8")
            history_path = review_dir / "challenger.jsonl"
            history_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "timestamp": "2026-03-28T10:00:00Z",
                                "reviewer": "editor_one",
                                "episode_id": "challenger",
                                "lane": "scene_stills",
                                "gate_type": "scene_still",
                                "item_id": "launch_commit_console",
                                "decision": "approve",
                                "notes": "Approved.",
                                "before": {"id": "launch_commit_console"},
                                "after": {"id": "launch_commit_console", "purpose": "Launch commit console"},
                                "proof_path": str(proof_path),
                            }
                        ),
                        json.dumps(
                            {
                                "timestamp": "2026-03-28T12:00:00Z",
                                "reviewer": "editor_two",
                                "episode_id": "challenger",
                                "lane": "motion_assets",
                                "gate_type": "motion_asset",
                                "item_id": "launch_commit_dolly",
                                "decision": "reject",
                                "notes": "Move is too fast.",
                                "before": {"id": "launch_commit_dolly"},
                                "after": {"id": "launch_commit_dolly", "purpose": "Launch commit dolly"},
                                "proof_path": "",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            history = load_review_history(context, "challenger")
            self.assertEqual([item["decision"] for item in history], ["reject", "approve"])
            self.assertEqual(history[0]["status"], "rejected")
            self.assertEqual(history[0]["gate_label"], "Motion asset")
            self.assertEqual(history[0]["item_label"], "Launch commit dolly")
            self.assertEqual(history[1]["status"], "approved")
            self.assertEqual(history[1]["proof_path"], str(proof_path))
            self.assertTrue(history[1]["proof_exists"])

    def test_review_message_detail_includes_history_for_closed_thread(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(ROOT / "episodes/hyatt-regency.toml")
            proof_root = temp_root / "proofs"
            proof_root.mkdir(parents=True, exist_ok=True)
            approved = proof_root / "thumb.png"
            approved.write_text("thumb", encoding="utf-8")
            manifest["packaging_stills"]["items"][0]["selected_asset"] = str(approved)
            manifest["packaging_stills"]["items"][0]["review_status"] = "approved"
            manifest["packaging_stills"]["items"][0]["reviewer"] = "editor_three"
            manifest["packaging_stills"]["items"][0]["reviewed_at"] = "2026-03-28T14:00:00Z"
            self._write_manifest_copy(temp_root, "hyatt-regency", manifest)
            review_dir = temp_root / "state" / "reviews"
            review_dir.mkdir(parents=True, exist_ok=True)
            (review_dir / "hyatt-regency.jsonl").write_text(
                json.dumps(
                    {
                        "timestamp": "2026-03-28T14:00:00Z",
                        "reviewer": "editor_three",
                        "episode_id": "hyatt-regency",
                        "lane": "packaging_stills",
                        "gate_type": "packaging_still",
                        "item_id": "primary_thumbnail",
                        "decision": "approve",
                        "notes": "Approved for archive.",
                        "before": {"id": "primary_thumbnail"},
                        "after": {"id": "primary_thumbnail", "purpose": "Primary thumbnail"},
                        "proof_path": "",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            detail = build_review_message_detail(context, message_id_for("hyatt-regency", "packaging_still", "primary_thumbnail"))
            self.assertEqual(detail["message"]["history_count"], 1)
            self.assertEqual(detail["message"]["history"][0]["decision"], "approve")
            self.assertEqual(detail["message"]["history"][0]["item_label"], "Primary thumbnail")
            self.assertEqual(detail["message"]["status"], "approved")

    def test_review_action_approves_visual_research_and_logs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "review"
            manifest["visual_research"]["approval"]["status"] = "pending"
            self._prepare_visual_research_fixture(manifest, temp_root)
            self._write_manifest_copy(temp_root, "challenger", manifest)
            result = perform_review_action(
                context,
                episode_id="challenger",
                gate_type="visual_research",
                decision="approve",
                reviewer="reviewer_1",
                notes="Coverage is complete.",
            )
            self.assertEqual(result["state"]["lanes"]["visual_research"]["status"], "done")
            updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
            self.assertEqual(updated["visual_research"]["approval"]["status"], "approved")
            self.assertEqual(updated["visual_research"]["approval"]["reviewer"], "reviewer_1")
            review_log = Path(result["log_path"]).read_text(encoding="utf-8")
            self.assertIn('"gate_type": "visual_research"', review_log)
            self.assertIn('"decision": "approve"', review_log)

    def test_review_action_reject_requires_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "review"
            self._write_manifest_copy(temp_root, "challenger", manifest)
            with self.assertRaises(SystemExit) as exc:
                perform_review_action(
                    context,
                    episode_id="challenger",
                    gate_type="visual_research",
                    decision="reject",
                    reviewer="reviewer_1",
                    notes="",
                )
            self.assertIn("Reject notes are required", str(exc.exception))

    def test_review_action_rejects_scene_still_and_preserves_proof(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(ROOT / "episodes/therac-25.toml")
            proof_root = temp_root / "proofs"
            proof_root.mkdir(parents=True, exist_ok=True)
            proof_image = proof_root / "scene.png"
            proof_image.write_text("image", encoding="utf-8")
            proof_manifest = proof_root / "scene.png.json"
            proof_manifest.write_text(json.dumps({"final_outputs": [str(proof_image)]}), encoding="utf-8")
            manifest["scene_stills"]["items"][0]["latest_render_path"] = str(proof_image)
            manifest["scene_stills"]["items"][0]["latest_render_manifest_path"] = str(proof_manifest)
            manifest["scene_stills"]["items"][0]["review_status"] = "pending"
            self._write_manifest_copy(temp_root, "therac-25", manifest)
            result = perform_review_action(
                context,
                episode_id="therac-25",
                gate_type="scene_still",
                item_id="console_alarm_hero",
                decision="reject",
                reviewer="reviewer_2",
                notes="Needs a cleaner focal hierarchy.",
                tags=["overscaled_ripped_paper"],
            )
            updated = load_episode_manifest(temp_root / "episodes/therac-25.toml")
            scene_item = updated["scene_stills"]["items"][0]
            self.assertEqual(scene_item["review_status"], "rejected")
            self.assertEqual(scene_item["reviewer"], "reviewer_2")
            self.assertEqual(scene_item["latest_render_path"], str(proof_image))
            review_log = Path(result["log_path"]).read_text(encoding="utf-8")
            self.assertIn('"decision": "reject"', review_log)
            self.assertIn('"gate_type": "scene_still"', review_log)

    def test_review_action_motion_source_requires_approved_still(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
            scene_item = next(item for item in manifest["scene_stills"]["items"] if item["id"] == "launch_commit_console")
            scene_item["review_status"] = "pending"
            scene_item["selected_asset"] = ""
            self._write_manifest_copy(temp_root, "challenger", manifest)
            with self.assertRaises(SystemExit) as exc:
                perform_review_action(
                    context,
                    episode_id="challenger",
                    gate_type="motion_source",
                    item_id="launch_commit_console",
                    decision="approve",
                    reviewer="reviewer_3",
                    notes="Ready for motion.",
                )
            self.assertIn("must be approved with an approved proof", str(exc.exception))

    def test_review_action_rejects_motion_asset_back_to_todo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
            proof_root = temp_root / "proofs"
            proof_root.mkdir(parents=True, exist_ok=True)
            proof_video = proof_root / "motion.mp4"
            proof_video.write_text("video", encoding="utf-8")
            proof_manifest = proof_root / "motion.mp4.json"
            proof_manifest.write_text(json.dumps({"output_path": str(proof_video)}), encoding="utf-8")
            motion_item = next(item for item in manifest["motion_assets"]["items"] if item["id"] == "launch_commit_dolly")
            motion_item["status"] = "review"
            motion_item["latest_render_path"] = str(proof_video)
            motion_item["latest_render_manifest_path"] = str(proof_manifest)
            self._write_manifest_copy(temp_root, "challenger", manifest)
            result = perform_review_action(
                context,
                episode_id="challenger",
                gate_type="motion_asset",
                item_id="launch_commit_dolly",
                decision="reject",
                reviewer="reviewer_4",
                notes="Camera move is too aggressive.",
                tags=["motion_too_short"],
            )
            updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
            motion_item = next(item for item in updated["motion_assets"]["items"] if item["id"] == "launch_commit_dolly")
            self.assertEqual(motion_item["status"], "todo")
            self.assertEqual(motion_item["review_outcome"], "rejected")
            self.assertEqual(motion_item["reviewer"], "reviewer_4")
            self.assertEqual(result["state"]["lanes"]["motion_assets"]["status"], "todo")

    def test_review_server_serves_inbox_and_restricts_asset_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(ROOT / "episodes/therac-25.toml")
            proof_root = temp_root / "proofs"
            proof_root.mkdir(parents=True, exist_ok=True)
            proof_video = proof_root / "motion.mp4"
            proof_video.write_text("video", encoding="utf-8")
            proof_manifest = proof_root / "motion.mp4.json"
            proof_manifest.write_text(json.dumps({"output_path": str(proof_video)}), encoding="utf-8")
            manifest["motion_assets"]["items"][0]["status"] = "review"
            manifest["motion_assets"]["items"][0]["latest_render_path"] = str(proof_video)
            manifest["motion_assets"]["items"][0]["latest_render_manifest_path"] = str(proof_manifest)
            self._write_manifest_copy(temp_root, "therac-25", manifest)
            server = build_review_server(context, host="127.0.0.1", port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base_url = f"http://127.0.0.1:{server.server_address[1]}"
                with urllib_request.urlopen(f"{base_url}/api/review/inbox", timeout=5) as response:
                    inbox = json.loads(response.read().decode("utf-8"))
                self.assertGreaterEqual(inbox["total_items"], 1)
                self.assertTrue(
                    any(
                        item["message_id"] == message_id_for("therac-25", "motion_asset", "console_alarm_push")
                        for item in inbox["messages"]
                    )
                )
                with urllib_request.urlopen(
                    f"{base_url}/api/review/assets?path={urllib_parse.quote(str(proof_video), safe='')}",
                    timeout=5,
                ) as response:
                    served = response.read().decode("utf-8")
                self.assertEqual(served, "video")
                with tempfile.NamedTemporaryFile(delete=False) as handle:
                    outside = Path(handle.name)
                try:
                    outside.write_text("outside", encoding="utf-8")
                    with self.assertRaises(urllib_error.HTTPError) as exc:
                        response = urllib_request.urlopen(
                            f"{base_url}/api/review/assets?path={urllib_parse.quote(str(outside), safe='')}",
                            timeout=5,
                        )
                        response.close()
                    self.assertEqual(exc.exception.code, 403)
                    exc.exception.close()
                finally:
                    outside.unlink(missing_ok=True)
            finally:
                server.shutdown()
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())
                server.server_close()

    def test_review_page_renders_single_inbox_surface(self) -> None:
        theme = load_signal_brand_theme(self.context)
        page = render_review_page(title="Review Inbox", theme=theme)
        self.assertNotIn("/review/episodes/", page)
        self.assertNotIn("Episode detail", page)
        self.assertNotIn("Across ", page)
        self.assertNotIn("side-panel", page)
        self.assertNotIn("actionForm(message)", page)
        self.assertIn("menu-trigger", page)
        self.assertIn("data-action-menu", page)
        self.assertIn("closeActionMenus()", page)
        self.assertIn(".rail-list {\n      overflow: auto;", page)
        self.assertIn(".message-pane {\n      padding: 18px", page)
        self.assertIn("overflow: auto;", page)
        self.assertIn("position: sticky;", page)
        self.assertEqual(page.count('message.unread ? "Unread" : "Read"'), 1)
        self.assertIn('searchParams.set("message"', page)

    def test_command_review_inbox_delegates_to_inbox_cli(self) -> None:
        with mock.patch("orchestration.cli._run_inbox_cli", return_value=0) as delegated:
            exit_code = command_review_inbox(self.context, type("Args", (), {"json": True})())
        delegated.assert_called_once_with(["review-inbox", "--json"])
        self.assertEqual(exit_code, 0)

    def test_command_review_action_delegates_to_inbox_cli(self) -> None:
        args = type(
            "Args",
            (),
            {
                "episode_id": "challenger",
                "gate_type": "scene_still",
                "item_id": "launch_commit_console",
                "decision": "reject",
                "reviewer": "editor",
                "notes": "Needs another pass.",
                "tag": [],
            },
        )()
        with mock.patch("orchestration.cli._run_inbox_cli", return_value=0) as delegated:
            exit_code = command_review_action(self.context, args)
        delegated.assert_called_once_with(
            [
                "review-action",
                "challenger",
                "scene_still",
                "launch_commit_console",
                "--decision",
                "reject",
                "--reviewer",
                "editor",
                "--notes",
                "Needs another pass.",
            ]
        )
        self.assertEqual(exit_code, 0)

    def test_command_review_server_delegates_to_inbox_cli(self) -> None:
        args = type("Args", (), {"host": "127.0.0.1", "port": 9001})()
        with mock.patch("orchestration.cli._run_inbox_cli", return_value=0) as delegated:
            exit_code = command_review_server(self.context, args)
        delegated.assert_called_once_with(["review-server", "--host", "127.0.0.1", "--port", "9001"])
        self.assertEqual(exit_code, 0)

    def test_review_server_message_detail_api_and_episode_redirect(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(ROOT / "episodes/challenger.toml")
            self._write_manifest_copy(temp_root, "challenger", manifest)
            review_dir = temp_root / "state" / "reviews"
            review_dir.mkdir(parents=True, exist_ok=True)
            (review_dir / "challenger.jsonl").write_text(
                json.dumps(
                    {
                        "timestamp": "2026-03-28T15:00:00Z",
                        "reviewer": "editor_four",
                        "episode_id": "challenger",
                        "lane": "motion_assets",
                        "gate_type": "motion_asset",
                        "item_id": "launch_commit_dolly",
                        "decision": "reject",
                        "notes": "Ease in more gently.",
                        "before": {"id": "launch_commit_dolly"},
                        "after": {"id": "launch_commit_dolly", "purpose": "Launch commit dolly"},
                        "proof_path": "",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            server = build_review_server(context, host="127.0.0.1", port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base_url = f"http://127.0.0.1:{server.server_address[1]}"
                with urllib_request.urlopen(f"{base_url}/api/review/inbox", timeout=5) as response:
                    inbox = json.loads(response.read().decode("utf-8"))
                self.assertIn("messages", inbox)
                self.assertIn("default_message_id", inbox)
                with urllib_request.urlopen(
                    f"{base_url}/api/review/messages/{urllib_parse.quote(message_id_for('challenger', 'motion_asset', 'launch_commit_dolly'), safe='')}",
                    timeout=5,
                ) as response:
                    detail = json.loads(response.read().decode("utf-8"))
                self.assertIn("message", detail)
                self.assertEqual(detail["message"]["history"][0]["decision"], "reject")
                with urllib_request.urlopen(f"{base_url}/review/episodes/challenger", timeout=5) as response:
                    self.assertTrue(response.geturl().endswith("/review"))
            finally:
                server.shutdown()
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())
                server.server_close()

    def test_review_server_uses_fallback_theme_when_brand_tokens_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._clone_context_with_web_root(temp_root / "missing-web")
            server = build_review_server(context, host="127.0.0.1", port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base_url = f"http://127.0.0.1:{server.server_address[1]}"
                with urllib_request.urlopen(f"{base_url}/review", timeout=5) as response:
                    page = response.read().decode("utf-8")
                self.assertIn("Brand fallback active.", page)
                self.assertIn("Unable to load signal style-system tokens", page)
                self.assertIn("@media (prefers-color-scheme: dark)", page)
                self.assertIn("color-scheme: dark;", page)
            finally:
                server.shutdown()
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())
                server.server_close()


if __name__ == "__main__":
    unittest.main()
