from __future__ import annotations

import copy
import json
import re
import tempfile
import threading
import unittest
from pathlib import Path
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

from inbox_app.agents_bridge import (
    AGENTS_ROOT,
    Context,
    build_context,
    load_episode_manifest,
    resolve_agents_root,
    write_episode_manifest,
)
from inbox_app.cli import build_parser
from inbox_app.review import build_review_inbox, build_review_message_detail, perform_review_action
from inbox_app.review_brand import (
    CONSUMED_TOKEN_PATHS,
    load_signal_brand_theme,
    signal_style_system_path,
    signal_style_system_schema_path,
)
from inbox_app.review_server import build_review_server, render_markdown_html, render_review_page


def _lookup_token_path(node: dict[str, object], path: tuple[str, ...]) -> object:
    current: object = node
    for part in path:
        if not isinstance(current, dict):
            raise KeyError(".".join(path))
        current = current[part]
    return current


ALLOWED_FONT_SIZE_LITERALS = frozenset({"11px", "12px", "14px"})
TEST_ELEVENLABS_MODEL = "test_model_v2_hq"


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


class InboxAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = build_context()

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

    def _write_manifest_copy(self, temp_root: Path, episode_id: str, manifest: dict[str, object] | None = None) -> Path:
        manifest_path = temp_root / "episodes" / f"{episode_id}.toml"
        if manifest is None:
            manifest_path.write_text((AGENTS_ROOT / "episodes" / f"{episode_id}.toml").read_text(encoding="utf-8"), encoding="utf-8")
        else:
            write_episode_manifest(manifest_path, manifest)
        return manifest_path

    def _write_artifact(self, path: Path, *, content: str = "artifact", manifest_payload: dict[str, object] | None = None) -> tuple[str, str]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        manifest_path = Path(f"{path}.json")
        payload = manifest_payload or {"output_path": str(path), "final_outputs": [str(path)]}
        manifest_path.write_text(json.dumps(payload), encoding="utf-8")
        return str(path), str(manifest_path)

    def _write_audio_package_metadata(
        self,
        pipeline_dir: Path,
        *,
        packaged_path: Path,
        transcript_path: Path,
        provider: str = "elevenlabs",
        voice: str = "voice_test_123",
        model: str = TEST_ELEVENLABS_MODEL,
        source_manifest_path: Path | None = None,
    ) -> Path:
        pipeline_dir.mkdir(parents=True, exist_ok=True)
        source_manifest = source_manifest_path or (pipeline_dir / "effective_final_jobs.elevenlabs.jsonl")
        source_manifest.write_text("{}\n", encoding="utf-8")
        metadata_path = pipeline_dir / "audio_package.json"
        metadata_path.write_text(
            json.dumps(
                {
                    "provider": provider,
                    "voice": voice,
                    "model": model,
                    "effective_manifest_path": str(source_manifest),
                    "packaged_path": str(packaged_path),
                    "packaged_sha256": "packaged-sha",
                    "packaged_at": "2026-03-30T18:00:00Z",
                    "transcript_path": str(transcript_path),
                    "transcript_sha256": "transcript-sha",
                    "qa_completed_at": "2026-03-30T18:05:00Z",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return metadata_path

    def _scene_item(self, manifest: dict[str, object], item_id: str) -> dict[str, object]:
        return next(item for item in manifest["scene_stills"]["items"] if item["id"] == item_id)

    def _audio_ready_manifest(self, temp_root: Path) -> dict[str, object]:
        manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
        pipeline_dir = temp_root / "audio" / "pipeline"
        pipeline_dir.mkdir(parents=True, exist_ok=True)
        master_path = temp_root / "final" / "episode.wav"
        master_path.parent.mkdir(parents=True, exist_ok=True)
        master_path.write_text("audio", encoding="utf-8")
        transcript_path = temp_root / "audio" / "transcript.txt"
        transcript_path.parent.mkdir(parents=True, exist_ok=True)
        transcript_path.write_text("transcript", encoding="utf-8")
        manifest["audio"]["pipeline_dir"] = str(pipeline_dir)
        manifest["audio"]["master_path"] = str(master_path)
        manifest["audio"]["transcript_path"] = str(transcript_path)
        manifest["audio"]["status"] = "review"
        manifest["audio"]["review"] = {
            "status": "pending",
            "reviewer": "",
            "reviewed_at": "",
            "notes": "",
        }
        manifest["visual_research"]["status"] = "done"
        manifest["visual_research"]["approval"]["status"] = "approved"
        return manifest

    def test_resolve_agents_root_matches_configured_checkout(self) -> None:
        self.assertEqual(resolve_agents_root(), AGENTS_ROOT)

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

    def test_load_signal_brand_theme_includes_dark_palette(self) -> None:
        theme = load_signal_brand_theme(self.context)
        self.assertEqual(theme.warning, "")
        self.assertEqual(theme.source_path, str(signal_style_system_path(self.context)))
        self.assertEqual(theme.css_variables["--paper"], "#FFFFFF")
        self.assertEqual(theme.css_variables["--text-primary"], "#0B1320")
        self.assertEqual(theme.css_variables["--type-heading-size"], "14px")
        self.assertEqual(theme.css_variables["--type-body-size"], "12px")
        self.assertEqual(theme.css_variables["--type-overline-size"], "11px")
        self.assertEqual(theme.css_variables["--font-display"], "14px")
        self.assertEqual(theme.css_variables["--font-body"], "12px")
        self.assertEqual(theme.css_variables["--font-caption"], "11px")
        self.assertEqual(theme.css_variables["--font-ui-weight"], "400")
        self.assertEqual(theme.css_variables["--font-section-weight"], "700")
        self.assertEqual(theme.dark_css_variables["--paper"], "#20314B")
        self.assertEqual(theme.dark_css_variables["--text-primary"], "#FFFFFF")
        self.assertEqual(theme.dark_css_variables["--type-heading-size"], "14px")
        self.assertEqual(theme.dark_css_variables["--type-body-size"], "12px")
        self.assertEqual(theme.dark_css_variables["--type-overline-size"], "11px")
        self.assertEqual(theme.dark_css_variables["--line"], "rgba(255, 255, 255, 0.12)")
        self.assertEqual(theme.dark_css_variables["--ink"], "#0B1320")

    def test_review_page_renders_token_driven_css_variables(self) -> None:
        theme = load_signal_brand_theme(self.context)
        page = render_review_page(title="Review Inbox", theme=theme)
        app_shell_css = _css_block(page, ".app-shell")
        theme_warning_css = _css_block(page, ".theme-warning")
        workspace_css = _css_block(page, ".workspace")
        control_trigger_css = _css_block(page, ".control-trigger")
        rail_select_css = _css_block(page, ".rail-select")
        self.assertIn("--paper: #FFFFFF;", page)
        self.assertIn("--text-primary: #0B1320;", page)
        self.assertIn("--signal: #B7FF4A;", page)
        self.assertIn("--type-heading-size: 14px;", page)
        self.assertIn("--type-body-size: 12px;", page)
        self.assertIn("--type-overline-size: 11px;", page)
        self.assertIn("<title>Cascade Effects / Review Desk</title>", page)
        self.assertNotIn('class="masthead"', page)
        self.assertNotIn(".masthead {", page)
        self.assertNotIn("/review/episodes/", page)
        self.assertNotIn('<a class="nav-link" href="/review">Inbox</a>', page)
        self.assertNotIn(".nav-link {", page)
        self.assertIn('class="menu-trigger control-trigger"', page)
        self.assertIn('data-rail-root', page)
        self.assertIn('data-detail-root', page)
        self.assertIn('const PHASE_GATE_ORDER = [', page)
        self.assertIn('const STATUS_FILTER_OPTIONS = [', page)
        self.assertIn('const PENDING_FILTER_STATUSES = new Set(["pending", "unapproved"]);', page)
        self.assertIn('const APPROVED_FILTER_STATUSES = new Set(["approved", "approved_for_motion"]);', page)
        self.assertIn('let currentEpisodeFilter = "all";', page)
        self.assertIn('let currentStatusFilter = "all";', page)
        self.assertIn("function decisionStatus(message)", page)
        self.assertIn("function laneLabel(message)", page)
        self.assertIn("function freshnessLabel(message)", page)
        self.assertIn("function packageSyncLabel(message)", page)
        self.assertIn("function chipMarkup(label, status)", page)
        self.assertIn("function captureRailScrollState()", page)
        self.assertIn("function selectedEpisodeIdFromUrl()", page)
        self.assertIn("function selectedStatusFilterFromUrl()", page)
        self.assertIn('const TIMESTAMP_FORMATTER = typeof Intl !== "undefined" && typeof Intl.DateTimeFormat === "function"', page)
        self.assertIn('hourCycle: "h23"', page)
        self.assertIn("const DEV_RELOAD_ENABLED = false;", page)
        self.assertIn("function syncViewState(messageId, episodeId, statusFilter, push)", page)
        self.assertIn("function filterMessages(inbox, episodeId, statusFilter)", page)
        self.assertIn("function groupMessagesByGate(messages)", page)
        self.assertIn("function resolveRailSelection(inbox, requestedMessageId, episodeId, statusFilter)", page)
        self.assertIn("function renderRail(inbox, selectedMessageId, episodeId, statusFilter, preserveScroll)", page)
        self.assertIn("function assetUrl(path, version = \"\")", page)
        self.assertIn('if (preview.preview_type === "audio") {', page)
        self.assertIn('<div class="preview-audio"><audio controls preload="metadata" src="${assetUrl(preview.preview_path, version)}" aria-label="${escapeHtml(label)}"></audio></div>', page)
        self.assertIn("const railState = preserveScroll ? captureRailScrollState() : null;", page)
        self.assertIn("window.requestAnimationFrame(() => restoreRailScrollState(railState));", page)
        self.assertIn("@media (prefers-color-scheme: dark)", page)
        self.assertIn("color-scheme: light;", page)
        self.assertIn("color-scheme: dark;", page)
        self.assertIn("color: var(--text-primary);", page)
        self.assertIn("overflow-x: auto;", page)
        self.assertIn("overflow-y: hidden;", page)
        self.assertIn("width: max(1081px, 100vw);", page)
        self.assertNotIn("margin: 0 auto;", app_shell_css)
        self.assertNotIn("padding: calc(var(--space-card) * 0.42) 0 calc(var(--space-card) * 0.54);", app_shell_css)
        self.assertIn("border-bottom: 1px solid var(--alert);", theme_warning_css)
        self.assertNotIn("border-radius: var(--radius-md);", theme_warning_css)
        self.assertNotIn("box-shadow: var(--shadow-panel);", theme_warning_css)
        self.assertNotIn("border: 1px solid var(--line);", workspace_css)
        self.assertNotIn("border-radius: calc(var(--radius-lg) + 8px);", workspace_css)
        self.assertNotIn("box-shadow: var(--shadow-panel);", workspace_css)
        self.assertIn("@media (min-width: 1081px) and (max-width: 1180px)", page)
        self.assertNotIn("@media (max-width: 1080px)", page)
        self.assertNotIn("@media (max-width: 760px)", page)
        self.assertIn(".review-shell {", page)
        self.assertIn("--history-rail-collapsed-width: 40px;", page)
        self.assertIn("--history-rail-expanded-width: 320px;", page)
        self.assertIn("grid-template-columns:", page)
        self.assertIn(".review-shell.is-history-expanded {", page)
        self.assertIn(".detail-main {", page)
        self.assertIn(".history-rail {", page)
        self.assertIn(".control-trigger {", page)
        self.assertIn(".control-trigger::after {", page)
        self.assertIn(".rail-select-shell {", page)
        self.assertIn(".history-rail-collapsed-toggle {", page)
        self.assertIn(".history-rail-expanded {", page)
        self.assertIn(".history-rail-header {", page)
        self.assertIn(".history-rail-body {", page)
        self.assertIn(".detail-summary-bar {", page)
        self.assertIn(".summary-pill {", page)
        self.assertIn(".disclosure-block {", page)
        self.assertIn(".disclosure-summary {", page)
        self.assertIn(".preview-stage .preview-audio {", page)
        self.assertIn(".preview-stage .preview-audio audio {", page)
        self.assertIn(".history-meta-grid {", page)
        self.assertIn(".history-title-block {", page)
        self.assertIn("border-left: 1px solid var(--line);", page)
        self.assertIn("writing-mode: vertical-rl;", page)
        self.assertIn('pointer-events: none;', page)
        self.assertIn("function renderDetail(detail)", page)
        self.assertIn("function renderHistory(detail)", page)
        self.assertIn("function syncHistoryRailState()", page)
        self.assertIn("function toggleHistoryRail(forceExpanded)", page)
        self.assertIn("function railMessageMarkup(message, selectedMessageId)", page)
        self.assertIn("function railMarkup(inbox, selectedMessageId, episodeId, statusFilter)", page)
        self.assertIn("const visibleMessages = filterMessages(inbox, episodeId, statusFilter);", page)
        self.assertIn('data-episode-filter', page)
        self.assertIn('data-status-filter="${escapeHtml(option.key)}"', page)
        self.assertIn('data-gate-group="${escapeHtml(group.gateType)}"', page)
        self.assertIn("railRoot.innerHTML = railMarkup(inbox, selectedMessageId, episodeId, statusFilter);", page)
        self.assertIn('No messages match current filters', page)
        self.assertIn('const previousMessageId = currentDetail && currentDetail.message ? currentDetail.message.message_id : "";', page)
        self.assertIn("detailRoot.innerHTML = detailMarkup(detail, previousMessageId);", page)
        self.assertIn("historyRoot.innerHTML = historyRailMarkup(detail);", page)
        self.assertIn("function setSelectedMessageClasses(messageId)", page)
        self.assertIn("setSelectedMessageClasses(activeMessageId);", page)
        self.assertIn('url.searchParams.set("episode", resolvedEpisodeId);', page)
        self.assertIn('url.searchParams.set("status", resolvedStatusFilter);', page)
        self.assertIn('return "other";', page)
        self.assertIn("const visualResearchTabState = {};", page)
        self.assertIn("function reviewContextMarkup(message)", page)
        self.assertIn("function disclosureSectionMarkup(title, body, extraClass)", page)
        self.assertIn("function historyRailMarkup(detail)", page)
        self.assertIn('class="menu-trigger control-trigger"', page)
        self.assertIn('class="control-trigger rail-select-shell"', page)
        self.assertIn('class="detail-main"', page)
        self.assertIn('class="history-rail"', page)
        self.assertIn('data-history-root', page)
        self.assertIn('data-history-toggle', page)
        self.assertIn('class="history-rail-collapsed-toggle"', page)
        self.assertIn('class="history-rail-header"', page)
        self.assertIn('class="history-title-block"', page)
        self.assertIn("box-shadow: var(--shadow-panel);", control_trigger_css)
        self.assertIn("border-radius: var(--radius-pill);", control_trigger_css)
        self.assertIn('content: "▾";', _css_block(page, ".control-trigger::after"))
        self.assertIn("appearance: none;", rail_select_css)
        self.assertNotIn("border: 1px solid var(--line);", rail_select_css)
        self.assertNotIn("border-radius: 14px;", rail_select_css)
        self.assertNotIn("background: var(--paper);", rail_select_css)
        self.assertIn('class="summary-pill"', page)
        self.assertIn('class="disclosure-block"', page)
        self.assertIn('class="history-meta-grid"', page)
        self.assertIn('metaField("Workflow", laneLabel(message) || "-")', page)
        self.assertIn('metaField("Decision", decisionLabel(message) || "-")', page)
        self.assertIn('metaField("Audio Freshness", freshnessLabel(message))', page)
        self.assertIn('disclosureSectionMarkup("Details", detailMetadata, "detail-disclosure")', page)
        self.assertIn('disclosureSectionMarkup("Review Context", reviewContext, "review-context-disclosure")', page)
        self.assertIn('disclosureSectionMarkup("Episode Guardrails", episodeGuardrailsMarkup(message), "guardrails-disclosure")', page)
        self.assertIn('const HISTORY_RAIL_PANEL_ID = "history-rail-panel";', page)
        self.assertIn('historyRoot.querySelectorAll("[data-history-toggle]")', page)
        self.assertIn('const historyToggle = event.target.closest("button[data-history-toggle]");', page)
        self.assertIn('role="tablist"', page)
        self.assertIn('aria-label="Visual research files"', page)
        self.assertIn("function resolveVisualResearchPreview(message, previousMessageId)", page)
        self.assertIn("function visualResearchPreviewMarkup(message, previousMessageId)", page)
        self.assertIn('data-doc-label="${escapeHtml(doc.label)}"', page)
        self.assertIn('app.addEventListener("click", async (event) => {', page)
        self.assertIn('const docTab = event.target.closest("button.doc-tab[data-doc-label][data-message-id]");', page)
        self.assertIn('app.addEventListener("keydown", (event) => {', page)
        self.assertIn("const blockedActions = message.blocked_actions || {};", page)
        self.assertIn("const blockedReason = message.blocked_reason", page)
        self.assertIn('aria-disabled="true"', page)
        self.assertIn('title="${escapeHtml(blockedActions.approve)}"', page)
        self.assertIn(".detail-note {", page)
        self.assertIn("max-height: min(78vh, 720px);", page)
        self.assertIn(".menu-panel > * {", page)
        self.assertIn(".menu-form-fields > * {", page)
        self.assertIn(".menu-links a {", page)
        self.assertIn("overflow-wrap: anywhere;", page)
        self.assertNotIn(".menu-panel input.tag-option-control {", page)
        self.assertNotIn(".tag-option-body {", page)
        self.assertNotIn(".tag-option-control:checked + .tag-option-body {", page)
        self.assertNotIn('class="tag-option-control"', page)
        self.assertNotIn('class="tag-option-label"', page)
        self.assertNotIn("Reject Tags", page)
        self.assertNotIn("Review Tags", page)
        self.assertNotIn("Latest Reject Tags", page)
        self.assertIn('<div class="detail-note">${escapeHtml(message.blocked_reason)}</div>', page)
        self.assertNotIn('${message.review_notes ? `<div class="history-notes">${escapeHtml(message.review_notes)}</div>` : ""}', page)
        self.assertIn("if (form.dataset.itemId) {", page)
        self.assertIn("payload.item_id = form.dataset.itemId;", page)
        self.assertIn('if (actionButton.getAttribute("aria-disabled") === "true") {', page)
        self.assertIn('const statusFilterButton = event.target.closest("button[data-status-filter]");', page)
        self.assertIn('await applyRailFilters(currentEpisodeFilter, statusFilterButton.dataset.statusFilter, true);', page)
        self.assertIn('const episodeSelect = event.target.closest("select[data-episode-filter]");', page)
        self.assertIn('await applyRailFilters(episodeSelect.value, currentStatusFilter, true);', page)
        self.assertIn("async function checkForServerRestart()", page)
        self.assertIn('const state = await fetchJson("/api/review/dev-state", { cache: "no-store" });', page)
        self.assertIn("await syncInboxView(preferredMessageId, selectedEpisodeIdFromUrl(), selectedStatusFilterFromUrl(), pushHistory, true);", page)
        self.assertIn('actions.unreject ? \'<button class="action unreject" type="button">Undo Reject</button>\' : ""', page)
        self.assertIn('actions.unapprove ? \'<button class="action unapprove" type="button">Unapprove</button>\' : ""', page)
        self.assertIn('actionButton.classList.contains("unapprove")', page)
        self.assertIn(': "unreject";', page)
        self.assertIn("Decision", page)
        self.assertIn("Workflow", page)
        self.assertNotIn("localStorage", page)
        self.assertNotIn('searchParams.set("theme"', page)
        self.assertNotIn('searchParams.get("theme"', page)
        self.assertNotIn("function attachHandlers()", page)
        self.assertNotIn("function renderApp(", page)

    def test_review_page_typography_uses_only_allowed_type_scale(self) -> None:
        page = render_review_page(title="Review Inbox", theme=load_signal_brand_theme(self.context))
        self.assertEqual(_font_size_literals(page), ALLOWED_FONT_SIZE_LITERALS)
        phase_label_css = _css_block(page, ".phase-label")
        self.assertIn("background: var(--paper-strong);", phase_label_css)
        self.assertIn("border-bottom: 1px solid var(--line);", phase_label_css)
        self.assertIn(".phase-group + .phase-group .phase-label {", page)
        self.assertNotIn(".phase-label::after {", page)
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

    def test_markdown_preview_typography_uses_only_allowed_type_scale(self) -> None:
        page = render_markdown_html("# Review notes", title="Review Notes", theme=load_signal_brand_theme(self.context))
        self.assertEqual(_font_size_literals(page), ALLOWED_FONT_SIZE_LITERALS)
        self.assertIn("text-transform: uppercase;", _css_block(page, ".theme-warning strong"))

    def test_markdown_preview_renders_token_driven_theme_modes(self) -> None:
        theme = load_signal_brand_theme(self.context)
        page = render_markdown_html("# Review notes", title="Review Notes", theme=theme)
        self.assertIn("@media (prefers-color-scheme: dark)", page)
        self.assertIn("color-scheme: light;", page)
        self.assertIn("color-scheme: dark;", page)
        self.assertIn("color: var(--text-primary, #18191c);", page)
        self.assertNotIn("localStorage", page)

    def test_review_page_enables_dev_reload_probe_when_requested(self) -> None:
        page = render_review_page(
            title="Review Inbox",
            theme=load_signal_brand_theme(self.context),
            dev_reload_enabled=True,
            server_instance_id="dev-123",
        )
        self.assertIn('const DEV_RELOAD_ENABLED = true;', page)
        self.assertIn('let currentServerInstanceId = "dev-123";', page)
        self.assertIn("window.setInterval(checkForServerRestart, 1000);", page)

    def test_review_action_parser_accepts_unapprove(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["review-action", "challenger", "visual_research", "--decision", "unapprove"])
        self.assertEqual(args.decision, "unapprove")

    def test_review_action_parser_accepts_unreject(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["review-action", "challenger", "visual_research", "--decision", "unreject"])
        self.assertEqual(args.decision, "unreject")

    def test_review_action_parser_accepts_repeated_tags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "review-action",
                "challenger",
                "visual_research",
                "--decision",
                "reject",
                "--tag",
                "missing_contact_sheet",
                "--tag",
                "too_abstract",
            ]
        )
        self.assertEqual(args.tag, ["missing_contact_sheet", "too_abstract"])

    def test_review_server_parser_accepts_reload(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["review-server", "--reload"])
        self.assertTrue(args.reload)

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

    def test_visual_research_message_detail_preserves_fixed_doc_tabs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "review"
            manifest["visual_research"]["approval"]["status"] = "pending"
            manifest["visual_research"]["sources_path"] = ""
            self._write_manifest_copy(temp_root, "challenger", manifest)
            detail = build_review_message_detail(context, "challenger:visual_research:visual_research")
            docs = detail["message"]["docs"]
            self.assertEqual(
                [doc["label"] for doc in docs],
                ["Contact sheet", "Source inventory", "Act breakdown", "Reference notes", "Sources", "Assembly notes"],
            )
            self.assertEqual(docs[4]["path"], "")
            self.assertEqual(detail["message"]["preview_path"], docs[0]["path"])
            self.assertEqual(detail["message"]["lane_status"], "review")
            self.assertEqual(detail["message"]["lane_label"], "Awaiting review")
            self.assertEqual(detail["message"]["decision_status"], "pending")
            self.assertEqual(detail["message"]["decision_label"], "Pending")

    def test_visual_research_message_detail_prefers_contact_sheet_preview(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "review"
            manifest["visual_research"]["approval"]["status"] = "pending"
            contact_sheet = temp_root / "proofs" / "challenger-contact-sheet.pdf"
            contact_sheet.parent.mkdir(parents=True, exist_ok=True)
            contact_sheet.write_text("pdf", encoding="utf-8")
            manifest["visual_research"]["contact_sheet_path"] = str(contact_sheet)
            manifest["visual_research"]["act_breakdown_path"] = str(temp_root / "proofs" / "act_breakdown.md")
            Path(manifest["visual_research"]["act_breakdown_path"]).write_text("# Act breakdown", encoding="utf-8")
            self._write_manifest_copy(temp_root, "challenger", manifest)
            detail = build_review_message_detail(context, "challenger:visual_research:visual_research")
            self.assertEqual(detail["message"]["preview_path"], str(contact_sheet))
            self.assertEqual(detail["message"]["preview_type"], "pdf")

    def test_scene_still_detail_exposes_blocked_approve_reason_when_visual_research_is_not_done(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "review"
            manifest["visual_research"]["approval"]["status"] = "rejected"
            proof_path, proof_manifest_path = self._write_artifact(temp_root / "proofs" / "scene-proof.png")
            scene_item = self._scene_item(manifest, "launch_commit_console")
            scene_item["latest_render_path"] = proof_path
            scene_item["latest_render_manifest_path"] = proof_manifest_path
            scene_item["selected_asset"] = ""
            scene_item["review_status"] = "pending"
            self._write_manifest_copy(temp_root, "challenger", manifest)
            detail = build_review_message_detail(context, f"challenger:scene_still:{scene_item['id']}")
            self.assertEqual(detail["message"]["actions"], {"approve": False, "reject": True, "unapprove": False, "unreject": False})
            self.assertEqual(detail["message"]["lane_status"], "review")
            self.assertEqual(detail["message"]["lane_label"], "Awaiting review")
            self.assertEqual(detail["message"]["decision_status"], "pending")
            self.assertEqual(detail["message"]["decision_label"], "Pending")
            self.assertEqual(
                detail["message"]["blocked_actions"],
                {"approve": "blocked until visual research is approved"},
            )

    def test_packaging_still_detail_exposes_blocked_approve_reason_when_visual_research_is_not_done(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "review"
            manifest["visual_research"]["approval"]["status"] = "rejected"
            proof_path, proof_manifest_path = self._write_artifact(temp_root / "proofs" / "packaging-proof.png")
            packaging_item = manifest["packaging_stills"]["items"][0]
            packaging_item["latest_render_path"] = proof_path
            packaging_item["latest_render_manifest_path"] = proof_manifest_path
            packaging_item["selected_asset"] = ""
            packaging_item["review_status"] = "pending"
            self._write_manifest_copy(temp_root, "challenger", manifest)
            detail = build_review_message_detail(context, f"challenger:packaging_still:{packaging_item['id']}")
            self.assertEqual(detail["message"]["actions"], {"approve": False, "reject": True, "unapprove": False, "unreject": False})
            self.assertEqual(detail["message"]["lane_status"], "review")
            self.assertEqual(detail["message"]["lane_label"], "Awaiting review")
            self.assertEqual(detail["message"]["decision_status"], "pending")
            self.assertEqual(detail["message"]["decision_label"], "Pending")
            self.assertEqual(
                detail["message"]["blocked_actions"],
                {"approve": "blocked until visual research is approved"},
            )

    def test_review_inbox_reads_real_agents_messages(self) -> None:
        inbox = build_review_inbox(self.context)
        self.assertGreaterEqual(inbox["total_items"], 1)
        self.assertTrue(inbox["default_message_id"])
        detail = build_review_message_detail(self.context, inbox["default_message_id"])
        self.assertEqual(detail["message_id"], inbox["default_message_id"])

    def test_review_server_serves_inbox_and_restricts_asset_paths(self) -> None:
        server = build_review_server(self.context, host="127.0.0.1", port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            with urllib_request.urlopen(f"{base_url}/api/review/inbox", timeout=5) as response:
                inbox = json.loads(response.read().decode("utf-8"))
            self.assertGreaterEqual(inbox["total_items"], 1)
            with urllib_request.urlopen(
                f"{base_url}/api/review/messages/{urllib_parse.quote(inbox['default_message_id'], safe='')}",
                timeout=5,
            ) as response:
                detail = json.loads(response.read().decode("utf-8"))
            self.assertIn("message", detail)
            asset_path = signal_style_system_path(self.context)
            with urllib_request.urlopen(
                f"{base_url}/api/review/assets?path={urllib_parse.quote(str(asset_path), safe='')}",
                timeout=5,
            ) as response:
                served = response.read().decode("utf-8")
            self.assertIn('"semantic"', served)
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

    def test_review_server_reports_dev_state_when_reload_enabled(self) -> None:
        server = build_review_server(
            self.context,
            host="127.0.0.1",
            port=0,
            dev_reload_enabled=True,
            server_instance_id="dev-123",
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            with urllib_request.urlopen(f"{base_url}/api/review/dev-state", timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
            self.assertEqual(payload["server_instance_id"], "dev-123")
            self.assertTrue(payload["dev_reload_enabled"])
        finally:
            server.shutdown()
            thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
            server.server_close()

    def test_review_server_allows_visual_research_action_without_item_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "done"
            manifest["visual_research"]["approval"]["status"] = "approved"
            self._write_manifest_copy(temp_root, "challenger", manifest)
            server = build_review_server(context, host="127.0.0.1", port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base_url = f"http://127.0.0.1:{server.server_address[1]}"
                request = urllib_request.Request(
                    f"{base_url}/api/review/actions",
                    data=json.dumps(
                        {
                            "episode_id": "challenger",
                            "gate_type": "visual_research",
                            "item_id": None,
                            "decision": "unapprove",
                            "reviewer": "mike",
                            "notes": "restart research",
                        }
                    ).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib_request.urlopen(request, timeout=5) as response:
                    result = json.loads(response.read().decode("utf-8"))
                updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
                self.assertEqual(result["decision"], "unapprove")
                self.assertEqual(updated["visual_research"]["status"], "review")
                self.assertEqual(updated["visual_research"]["approval"]["status"], "pending")
            finally:
                server.shutdown()
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())
                server.server_close()

    def test_review_server_allows_visual_research_unreject_without_item_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "review"
            manifest["visual_research"]["approval"]["status"] = "rejected"
            manifest["visual_research"]["approval"]["reviewer"] = "mike"
            manifest["visual_research"]["approval"]["reviewed_at"] = "2026-03-29T10:00:00Z"
            manifest["visual_research"]["approval"]["notes"] = "Needs revision."
            self._write_manifest_copy(temp_root, "challenger", manifest)
            server = build_review_server(context, host="127.0.0.1", port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base_url = f"http://127.0.0.1:{server.server_address[1]}"
                request = urllib_request.Request(
                    f"{base_url}/api/review/actions",
                    data=json.dumps(
                        {
                            "episode_id": "challenger",
                            "gate_type": "visual_research",
                            "item_id": None,
                            "decision": "unreject",
                            "reviewer": "mike",
                            "notes": "",
                        }
                    ).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib_request.urlopen(request, timeout=5) as response:
                    result = json.loads(response.read().decode("utf-8"))
                updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
                self.assertEqual(result["decision"], "unreject")
                self.assertEqual(updated["visual_research"]["status"], "review")
                self.assertEqual(updated["visual_research"]["approval"]["status"], "pending")
                self.assertEqual(updated["visual_research"]["approval"]["reviewer"], "")
                self.assertEqual(updated["visual_research"]["approval"]["notes"], "")
            finally:
                server.shutdown()
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())
                server.server_close()

    def test_review_server_allows_visual_research_reject_without_tags(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "review"
            manifest["visual_research"]["approval"]["status"] = "pending"
            self._write_manifest_copy(temp_root, "challenger", manifest)
            server = build_review_server(context, host="127.0.0.1", port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base_url = f"http://127.0.0.1:{server.server_address[1]}"
                request = urllib_request.Request(
                    f"{base_url}/api/review/actions",
                    data=json.dumps(
                        {
                            "episode_id": "challenger",
                            "gate_type": "visual_research",
                            "item_id": None,
                            "decision": "reject",
                            "reviewer": "mike",
                            "notes": "Need the contact sheet.",
                        }
                    ).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib_request.urlopen(request, timeout=5) as response:
                    result = json.loads(response.read().decode("utf-8"))
                updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
                self.assertEqual(result["decision"], "reject")
                self.assertEqual(result["tags"], [])
                self.assertEqual(updated["visual_research"]["status"], "review")
                self.assertEqual(updated["visual_research"]["approval"]["status"], "rejected")
                self.assertEqual(updated["visual_research"]["approval"]["tags"], [])
            finally:
                server.shutdown()
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())
                server.server_close()

    def test_review_action_writes_back_into_agents_state_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "review"
            manifest["visual_research"]["approval"]["status"] = "pending"
            self._write_manifest_copy(temp_root, "challenger", manifest)
            result = perform_review_action(
                context,
                episode_id="challenger",
                gate_type="visual_research",
                decision="approve",
                reviewer="reviewer_1",
                notes="Coverage is complete.",
            )
            updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
            self.assertEqual(updated["visual_research"]["approval"]["status"], "approved")
            self.assertTrue(str(result["log_path"]).startswith(str(temp_root / "state" / "reviews")))

    def test_reject_requires_notes_but_not_tags(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "review"
            manifest["visual_research"]["approval"]["status"] = "pending"
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
            self.assertEqual(str(exc.exception), "Reject notes are required.")

            result = perform_review_action(
                context,
                episode_id="challenger",
                gate_type="visual_research",
                decision="reject",
                reviewer="reviewer_1",
                notes="Need the contact sheet.",
            )

            updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
            self.assertEqual(updated["visual_research"]["approval"]["status"], "rejected")
            self.assertEqual(updated["visual_research"]["approval"]["tags"], [])
            self.assertEqual(result["tags"], [])

    def test_audio_thread_appears_with_transcript_and_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = self._audio_ready_manifest(temp_root)
            self._write_manifest_copy(temp_root, "challenger", manifest)
            detail = build_review_message_detail(context, "challenger:audio:audio")
            self.assertEqual(detail["message"]["gate_type"], "audio")
            self.assertEqual(detail["message"]["label"], "Final audio")
            self.assertEqual(detail["message"]["status"], "pending")
            self.assertEqual(detail["message"]["lane_status"], "review")
            self.assertEqual(detail["message"]["lane_label"], "Awaiting review")
            self.assertEqual(detail["message"]["decision_status"], "pending")
            self.assertEqual(detail["message"]["decision_label"], "Pending")
            self.assertEqual(detail["message"]["freshness_status"], "current")
            self.assertEqual(detail["message"]["freshness_label"], "Current")
            self.assertEqual(detail["message"]["package_sync_status"], "unknown")
            self.assertEqual(detail["message"]["package_sync_label"], "Unknown")
            self.assertTrue(detail["message"]["unread"])
            self.assertEqual(detail["message"]["actions"], {"approve": True, "reject": True, "unapprove": False, "unreject": False})
            self.assertEqual(detail["message"]["preview_type"], "audio")
            self.assertEqual(detail["message"]["proof_path"], manifest["audio"]["master_path"])
            self.assertEqual(detail["message"]["docs"][0]["label"], "QA transcript")
            self.assertEqual(detail["message"]["docs"][0]["path"], manifest["audio"]["transcript_path"])

    def test_audio_thread_surfaces_package_sync_and_provider_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = self._audio_ready_manifest(temp_root)
            pipeline_dir = Path(str(manifest["audio"]["pipeline_dir"]))
            self._write_audio_package_metadata(
                pipeline_dir,
                packaged_path=Path(str(manifest["audio"]["master_path"])),
                transcript_path=Path(str(manifest["audio"]["transcript_path"])),
            )
            self._write_manifest_copy(temp_root, "challenger", manifest)

            detail = build_review_message_detail(context, "challenger:audio:audio")

            self.assertEqual(detail["message"]["package_sync_status"], "current")
            self.assertEqual(detail["message"]["package_sync_label"], "Current")
            self.assertEqual(detail["message"]["audio_provider"], "elevenlabs")
            self.assertEqual(detail["message"]["audio_voice"], "voice_test_123")
            self.assertEqual(detail["message"]["audio_model"], TEST_ELEVENLABS_MODEL)
            self.assertTrue(detail["message"]["audio_source_manifest_path"].endswith("effective_final_jobs.elevenlabs.jsonl"))
            self.assertTrue(detail["message"]["audio_package_metadata_path"].endswith("audio_package.json"))

    def test_audio_reject_requires_notes_but_not_tags(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = self._audio_ready_manifest(temp_root)
            self._write_manifest_copy(temp_root, "challenger", manifest)
            with self.assertRaises(SystemExit) as exc:
                perform_review_action(
                    context,
                    episode_id="challenger",
                    gate_type="audio",
                    item_id="audio",
                    decision="reject",
                    reviewer="reviewer_1",
                    notes="",
                )
            self.assertEqual(str(exc.exception), "Reject notes are required.")

            result = perform_review_action(
                context,
                episode_id="challenger",
                gate_type="audio",
                item_id="audio",
                decision="reject",
                reviewer="reviewer_1",
                notes="Needs pickup fixes.",
            )
            updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
            self.assertEqual(updated["audio"]["status"], "review")
            self.assertEqual(updated["audio"]["review"]["status"], "rejected")
            self.assertEqual(updated["audio"]["review"]["notes"], "Needs pickup fixes.")
            self.assertEqual(result["tags"], [])

    def test_approve_audio_marks_lane_done_and_exposes_unapprove(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = self._audio_ready_manifest(temp_root)
            self._write_manifest_copy(temp_root, "challenger", manifest)
            perform_review_action(
                context,
                episode_id="challenger",
                gate_type="audio",
                item_id="audio",
                decision="approve",
                reviewer="reviewer_1",
                notes="Approved final narration.",
            )
            updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
            self.assertEqual(updated["audio"]["status"], "done")
            self.assertEqual(updated["audio"]["review"]["status"], "approved")
            self.assertEqual(updated["audio"]["review"]["reviewer"], "reviewer_1")
            detail = build_review_message_detail(context, "challenger:audio:audio")
            self.assertEqual(detail["message"]["lane_status"], "done")
            self.assertEqual(detail["message"]["lane_label"], "Done")
            self.assertEqual(detail["message"]["decision_status"], "approved")
            self.assertEqual(detail["message"]["decision_label"], "Approved")
            self.assertEqual(detail["message"]["actions"], {"approve": False, "reject": False, "unapprove": True, "unreject": False})

    def test_audio_thread_blocks_approval_when_stale(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = self._audio_ready_manifest(temp_root)
            manifest["visual_research"]["approval"]["reviewed_at"] = "2100-01-01T00:00:00Z"
            self._write_manifest_copy(temp_root, "challenger", manifest)
            detail = build_review_message_detail(context, "challenger:audio:audio")
            self.assertEqual(detail["message"]["status"], "pending")
            self.assertEqual(detail["message"]["lane_status"], "review")
            self.assertEqual(detail["message"]["decision_status"], "pending")
            self.assertEqual(detail["message"]["freshness_status"], "stale")
            self.assertEqual(detail["message"]["freshness_label"], "Stale")
            self.assertEqual(detail["message"]["actions"], {"approve": False, "reject": False, "unapprove": False, "unreject": False})
            self.assertIn("predates the latest fact-check or approved visual research", detail["message"]["blocked_reason"])

    def test_audio_thread_blocks_review_when_package_needs_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = self._audio_ready_manifest(temp_root)
            pipeline_dir = Path(str(manifest["audio"]["pipeline_dir"]))
            promoted_transcript = pipeline_dir / "Ep99_Test.diarized.txt"
            promoted_transcript.write_text("new transcript", encoding="utf-8")
            self._write_audio_package_metadata(
                pipeline_dir,
                packaged_path=Path(str(manifest["audio"]["master_path"])),
                transcript_path=promoted_transcript,
            )
            self._write_manifest_copy(temp_root, "challenger", manifest)

            detail = build_review_message_detail(context, "challenger:audio:audio")

            self.assertEqual(detail["message"]["package_sync_status"], "out_of_sync")
            self.assertEqual(detail["message"]["package_sync_label"], "Needs promotion")
            self.assertEqual(detail["message"]["actions"], {"approve": False, "reject": False, "unapprove": False, "unreject": False})
            self.assertIn("promoted", detail["message"]["blocked_reason"])

    def test_unapprove_audio_reopens_downstream_and_clears_release_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = self._audio_ready_manifest(temp_root)
            manifest["audio"]["status"] = "done"
            manifest["audio"]["review"] = {
                "status": "approved",
                "reviewer": "reviewer_1",
                "reviewed_at": "2026-03-30T16:00:00Z",
                "notes": "Approved.",
            }
            manifest["assembly"]["status"] = "done"
            manifest["assembly"]["master_video_path"] = str(temp_root / "final" / "episode.mp4")
            manifest["assembly"]["completed_at"] = "2026-03-30T16:05:00Z"
            manifest["web"]["status"] = "done"
            manifest["web"]["entry_id"] = "challenger"
            manifest["release"]["status"] = "done"
            manifest["release"]["scheduled_for"] = "2026-03-31T09:00:00Z"
            manifest["release"]["published_at"] = "2026-03-31T16:00:00Z"
            manifest["analytics"]["status"] = "done"
            self._write_manifest_copy(temp_root, "challenger", manifest)
            perform_review_action(
                context,
                episode_id="challenger",
                gate_type="audio",
                item_id="audio",
                decision="unapprove",
                reviewer="reviewer_undo",
                notes="Reopen audio review.",
            )
            updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
            self.assertEqual(updated["audio"]["status"], "review")
            self.assertEqual(updated["audio"]["review"]["status"], "pending")
            self.assertEqual(updated["assembly"]["status"], "todo")
            self.assertEqual(updated["assembly"]["master_video_path"], "")
            self.assertEqual(updated["assembly"]["completed_at"], "")
            self.assertEqual(updated["web"]["status"], "todo")
            self.assertEqual(updated["web"]["entry_id"], "challenger")
            self.assertEqual(updated["release"]["status"], "todo")
            self.assertEqual(updated["release"]["scheduled_for"], "")
            self.assertEqual(updated["release"]["published_at"], "")
            self.assertEqual(updated["analytics"]["status"], "todo")

    def test_reject_persists_tags_and_detail_backfills_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "review"
            manifest["visual_research"]["approval"]["status"] = "pending"
            self._write_manifest_copy(temp_root, "challenger", manifest)

            result = perform_review_action(
                context,
                episode_id="challenger",
                gate_type="visual_research",
                decision="reject",
                reviewer="reviewer_1",
                notes="Need the contact sheet.",
                tags=["missing_contact_sheet"],
            )

            updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
            self.assertEqual(updated["visual_research"]["approval"]["tags"], ["missing_contact_sheet"])
            log_entries = (temp_root / "state" / "reviews" / "challenger.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(log_entries), 1)
            self.assertEqual(json.loads(log_entries[0])["tags"], ["missing_contact_sheet"])
            self.assertEqual(result["tags"], ["missing_contact_sheet"])

            detail = build_review_message_detail(context, "challenger:visual_research:visual_research")
            self.assertEqual(detail["message"]["review_tags"], ["missing_contact_sheet"])
            self.assertEqual(detail["message"]["history"][0]["tags"], ["missing_contact_sheet"])
            self.assertEqual(
                [option["tag"] for option in detail["message"]["reject_tag_options"]],
                ["missing_contact_sheet", "too_abstract", "source_text_unresolved"],
            )

    def test_unreject_clears_current_tags_but_preserves_history_tags(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "review"
            manifest["visual_research"]["approval"]["status"] = "pending"
            self._write_manifest_copy(temp_root, "challenger", manifest)

            perform_review_action(
                context,
                episode_id="challenger",
                gate_type="visual_research",
                decision="reject",
                reviewer="reviewer_1",
                notes="Need the contact sheet.",
                tags=["missing_contact_sheet"],
            )
            perform_review_action(
                context,
                episode_id="challenger",
                gate_type="visual_research",
                decision="unreject",
                reviewer="reviewer_1",
                notes="Re-open review.",
            )

            updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
            self.assertEqual(updated["visual_research"]["approval"]["tags"], [])

            detail = build_review_message_detail(context, "challenger:visual_research:visual_research")
            self.assertEqual(detail["message"]["review_tags"], [])
            reject_event = next(item for item in detail["message"]["history"] if item["decision"] == "reject")
            self.assertEqual(reject_event["tags"], ["missing_contact_sheet"])

    def test_rejected_visual_research_exposes_unreject_action(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "review"
            manifest["visual_research"]["approval"]["status"] = "rejected"
            manifest["visual_research"]["approval"]["reviewer"] = "mike"
            manifest["visual_research"]["approval"]["reviewed_at"] = "2026-03-29T10:00:00Z"
            manifest["visual_research"]["approval"]["notes"] = "Needs revision."
            self._write_manifest_copy(temp_root, "challenger", manifest)
            detail = build_review_message_detail(context, "challenger:visual_research:visual_research")
            self.assertEqual(detail["message"]["actions"], {"approve": True, "reject": True, "unapprove": False, "unreject": True})

    def test_rejected_scene_still_exposes_unreject_action(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "done"
            manifest["visual_research"]["approval"]["status"] = "approved"
            proof_path, proof_manifest_path = self._write_artifact(temp_root / "proofs" / "scene-proof.png")
            scene_item = self._scene_item(manifest, "launch_commit_console")
            scene_item["latest_render_path"] = proof_path
            scene_item["latest_render_manifest_path"] = proof_manifest_path
            scene_item["selected_asset"] = ""
            scene_item["review_status"] = "rejected"
            self._write_manifest_copy(temp_root, "challenger", manifest)
            detail = build_review_message_detail(context, f"challenger:scene_still:{scene_item['id']}")
            self.assertEqual(detail["message"]["actions"], {"approve": True, "reject": True, "unapprove": False, "unreject": True})

    def test_rejected_packaging_still_exposes_unreject_action(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "done"
            manifest["visual_research"]["approval"]["status"] = "approved"
            proof_path, proof_manifest_path = self._write_artifact(temp_root / "proofs" / "packaging-proof.png")
            packaging_item = manifest["packaging_stills"]["items"][0]
            packaging_item["latest_render_path"] = proof_path
            packaging_item["latest_render_manifest_path"] = proof_manifest_path
            packaging_item["selected_asset"] = ""
            packaging_item["review_status"] = "rejected"
            self._write_manifest_copy(temp_root, "challenger", manifest)
            detail = build_review_message_detail(context, f"challenger:packaging_still:{packaging_item['id']}")
            self.assertEqual(detail["message"]["actions"], {"approve": True, "reject": True, "unapprove": False, "unreject": True})

    def test_rejected_motion_source_exposes_unreject_action(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "done"
            manifest["visual_research"]["approval"]["status"] = "approved"
            selected_asset, _selected_manifest = self._write_artifact(temp_root / "proofs" / "scene-selected.png")
            scene_item = self._scene_item(manifest, "launch_commit_console")
            scene_item["selected_asset"] = selected_asset
            scene_item["review_status"] = "approved"
            scene_item["motion_review_status"] = "rejected"
            self._write_manifest_copy(temp_root, "challenger", manifest)
            detail = build_review_message_detail(context, "challenger:motion_source:launch_commit_console")
            self.assertEqual(detail["message"]["actions"], {"approve": True, "reject": True, "unapprove": False, "unreject": True})

    def test_blocked_motion_source_detail_uses_scene_proof_and_reason(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "done"
            manifest["visual_research"]["approval"]["status"] = "approved"
            proof_path, proof_manifest_path = self._write_artifact(temp_root / "proofs" / "scene-proof.png")
            scene_item = self._scene_item(manifest, "launch_commit_console")
            scene_item["selected_asset"] = ""
            scene_item["latest_render_path"] = proof_path
            scene_item["latest_render_manifest_path"] = proof_manifest_path
            scene_item["review_status"] = "rejected"
            scene_item["motion_review_status"] = "pending"
            self._write_manifest_copy(temp_root, "challenger", manifest)
            inbox = build_review_inbox(context)
            self.assertNotIn(
                "challenger:motion_source:launch_commit_console",
                {item["message_id"] for item in inbox["messages"]},
            )
            detail = build_review_message_detail(context, "challenger:motion_source:launch_commit_console")
            self.assertEqual(detail["message"]["status"], "pending")
            self.assertEqual(detail["message"]["lane_status"], "review")
            self.assertEqual(detail["message"]["decision_status"], "pending")
            self.assertEqual(detail["message"]["actions"], {"approve": False, "reject": False, "unapprove": False, "unreject": False})
            self.assertEqual(
                detail["message"]["blocked_reason"],
                "Blocked until the scene still review is approved.",
            )
            self.assertEqual(detail["message"]["preview_path"], proof_path)
            self.assertEqual(detail["message"]["proof_path"], proof_path)

    def test_blocked_motion_source_falls_back_to_history_proof(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "done"
            manifest["visual_research"]["approval"]["status"] = "approved"
            scene_item = self._scene_item(manifest, "launch_commit_console")
            scene_item["selected_asset"] = ""
            scene_item["latest_render_path"] = ""
            scene_item["latest_render_manifest_path"] = ""
            scene_item["review_status"] = "pending"
            scene_item["motion_review_status"] = "pending"
            self._write_manifest_copy(temp_root, "challenger", manifest)
            history_proof_path, _history_manifest_path = self._write_artifact(temp_root / "proofs" / "scene-history.png")
            review_dir = temp_root / "state" / "reviews"
            review_dir.mkdir(parents=True, exist_ok=True)
            (review_dir / "challenger.jsonl").write_text(
                json.dumps(
                    {
                        "timestamp": "2026-03-30T00:00:00Z",
                        "reviewer": "reviewer_history",
                        "episode_id": "challenger",
                        "lane": "scene_stills",
                        "gate_type": "motion_source",
                        "item_id": "launch_commit_console",
                        "decision": "reject",
                        "notes": "Previous motion-source pass.",
                        "proof_path": history_proof_path,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            detail = build_review_message_detail(context, "challenger:motion_source:launch_commit_console")
            self.assertEqual(detail["message"]["status"], "pending")
            self.assertEqual(detail["message"]["decision_status"], "pending")
            self.assertEqual(detail["message"]["preview_path"], history_proof_path)
            self.assertEqual(detail["message"]["proof_path"], history_proof_path)

    def test_approved_motion_source_still_appears_in_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "done"
            manifest["visual_research"]["approval"]["status"] = "approved"
            selected_asset, _selected_manifest = self._write_artifact(temp_root / "proofs" / "scene-selected.png")
            scene_item = self._scene_item(manifest, "launch_commit_console")
            scene_item["selected_asset"] = selected_asset
            scene_item["review_status"] = "approved"
            scene_item["motion_review_status"] = "pending"
            self._write_manifest_copy(temp_root, "challenger", manifest)
            inbox = build_review_inbox(context)
            message = next(item for item in inbox["messages"] if item["message_id"] == "challenger:motion_source:launch_commit_console")
            self.assertEqual(message["status"], "pending")
            self.assertEqual(message["lane_status"], "review")
            self.assertEqual(message["decision_status"], "pending")

    def test_rejected_motion_asset_exposes_unreject_action(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "done"
            manifest["visual_research"]["approval"]["status"] = "approved"
            selected_asset, _selected_manifest = self._write_artifact(temp_root / "proofs" / "scene-selected.png")
            motion_proof_path = temp_root / "proofs" / "motion-proof.mp4"
            motion_proof, motion_proof_manifest = self._write_artifact(
                motion_proof_path,
                manifest_payload={"output_path": str(motion_proof_path)},
            )
            scene_item = self._scene_item(manifest, "launch_commit_console")
            scene_item["selected_asset"] = selected_asset
            scene_item["review_status"] = "approved"
            scene_item["motion_review_status"] = "approved_for_motion"
            motion_item = manifest["motion_assets"]["items"][0]
            motion_item["status"] = "todo"
            motion_item["review_outcome"] = "rejected"
            motion_item["latest_render_path"] = motion_proof
            motion_item["latest_render_manifest_path"] = motion_proof_manifest
            self._write_manifest_copy(temp_root, "challenger", manifest)
            detail = build_review_message_detail(context, "challenger:motion_asset:launch_commit_dolly")
            self.assertEqual(detail["message"]["actions"], {"approve": False, "reject": False, "unapprove": False, "unreject": True})

    def test_approved_scene_still_exposes_unapprove_action(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "done"
            manifest["visual_research"]["approval"]["status"] = "approved"
            selected_asset, _selected_manifest = self._write_artifact(temp_root / "proofs" / "hero_still.png")
            scene_item = self._scene_item(manifest, "launch_commit_console")
            scene_item["selected_asset"] = selected_asset
            scene_item["latest_render_path"] = ""
            scene_item["latest_render_manifest_path"] = ""
            scene_item["review_status"] = "approved"
            self._write_manifest_copy(temp_root, "challenger", manifest)
            detail = build_review_message_detail(context, "challenger:scene_still:launch_commit_console")
            self.assertEqual(detail["message"]["actions"], {"approve": False, "reject": False, "unapprove": True, "unreject": False})

    def test_approve_scene_still_captures_approved_proof_and_unlocks_motion_from_proof(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "done"
            manifest["visual_research"]["approval"]["status"] = "approved"
            proof_path, proof_manifest_path = self._write_artifact(temp_root / "proofs" / "scene-proof.png")
            stale_selected_asset, _stale_selected_manifest = self._write_artifact(temp_root / "proofs" / "scene-final.png")
            scene_item = self._scene_item(manifest, "launch_commit_console")
            scene_item["reference_dir"] = str(temp_root / "references" / "launch_commit_console")
            scene_item["latest_render_path"] = proof_path
            scene_item["latest_render_manifest_path"] = proof_manifest_path
            scene_item["selected_asset"] = stale_selected_asset
            self._write_manifest_copy(temp_root, "challenger", manifest)
            result = perform_review_action(
                context,
                episode_id="challenger",
                gate_type="scene_still",
                item_id="launch_commit_console",
                decision="approve",
                reviewer="reviewer_scene",
                notes="Approve the refined proof.",
            )
            updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
            scene_item = self._scene_item(updated, "launch_commit_console")
            approved_proof_path = Path(scene_item["reference_dir"]) / "selects" / "review_approved.png"
            self.assertEqual(scene_item["review_status"], "approved")
            self.assertEqual(scene_item["approved_proof_path"], str(approved_proof_path))
            self.assertEqual(scene_item["approved_proof_manifest_path"], f"{approved_proof_path}.json")
            self.assertTrue(approved_proof_path.exists())
            self.assertTrue(Path(f"{approved_proof_path}.json").exists())
            self.assertEqual(scene_item["latest_render_path"], proof_path)
            self.assertEqual(scene_item["latest_render_manifest_path"], proof_manifest_path)
            self.assertEqual(scene_item["selected_asset"], "")
            self.assertEqual(result["decision"], "approve")
            detail = build_review_message_detail(context, "challenger:scene_still:launch_commit_console")
            self.assertEqual(detail["message"]["decision_status"], "approved")
            self.assertEqual(detail["message"]["lane_status"], "in_progress")
            self.assertEqual(detail["message"]["preview_path"], str(approved_proof_path))
            self.assertEqual(detail["message"]["proof_path"], str(approved_proof_path))
            motion_source_detail = build_review_message_detail(context, "challenger:motion_source:launch_commit_console")
            self.assertEqual(motion_source_detail["message"]["actions"], {"approve": True, "reject": True, "unapprove": False, "unreject": False})
            self.assertEqual(motion_source_detail["message"]["preview_path"], str(approved_proof_path))

    def test_approve_packaging_still_captures_approved_proof_and_keeps_lane_in_progress(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "done"
            manifest["visual_research"]["approval"]["status"] = "approved"
            proof_path, proof_manifest_path = self._write_artifact(temp_root / "proofs" / "packaging-proof.png")
            stale_selected_asset, _stale_selected_manifest = self._write_artifact(temp_root / "proofs" / "packaging-final.png")
            packaging_item = manifest["packaging_stills"]["items"][0]
            packaging_item["reference_dir"] = str(temp_root / "references" / packaging_item["id"])
            packaging_item["latest_render_path"] = proof_path
            packaging_item["latest_render_manifest_path"] = proof_manifest_path
            packaging_item["selected_asset"] = stale_selected_asset
            self._write_manifest_copy(temp_root, "challenger", manifest)
            result = perform_review_action(
                context,
                episode_id="challenger",
                gate_type="packaging_still",
                item_id=str(packaging_item["id"]),
                decision="approve",
                reviewer="reviewer_packaging",
                notes="Approve the refined packaging proof.",
            )
            updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
            packaging_item = updated["packaging_stills"]["items"][0]
            approved_proof_path = Path(packaging_item["reference_dir"]) / "selects" / "review_approved.png"
            self.assertEqual(packaging_item["review_status"], "approved")
            self.assertEqual(packaging_item["approved_proof_path"], str(approved_proof_path))
            self.assertEqual(packaging_item["approved_proof_manifest_path"], f"{approved_proof_path}.json")
            self.assertTrue(approved_proof_path.exists())
            self.assertTrue(Path(f"{approved_proof_path}.json").exists())
            self.assertEqual(packaging_item["latest_render_path"], proof_path)
            self.assertEqual(packaging_item["latest_render_manifest_path"], proof_manifest_path)
            self.assertEqual(packaging_item["selected_asset"], "")
            self.assertEqual(result["decision"], "approve")
            detail = build_review_message_detail(context, f"challenger:packaging_still:{packaging_item['id']}")
            self.assertEqual(detail["message"]["decision_status"], "approved")
            self.assertEqual(detail["message"]["lane_status"], "in_progress")
            self.assertEqual(detail["message"]["preview_path"], str(approved_proof_path))
            self.assertEqual(detail["message"]["proof_path"], str(approved_proof_path))

    def test_unapprove_scene_still_restores_proof_and_reopens_motion_asset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "done"
            manifest["visual_research"]["approval"]["status"] = "approved"
            selected_asset, _selected_manifest = self._write_artifact(temp_root / "proofs" / "scene-selected.png")
            motion_proof_path = temp_root / "proofs" / "motion-proof.mp4"
            motion_proof, motion_proof_manifest = self._write_artifact(
                motion_proof_path,
                manifest_payload={"output_path": str(motion_proof_path)},
            )
            scene_item = self._scene_item(manifest, "launch_commit_console")
            scene_item["selected_asset"] = selected_asset
            scene_item["latest_render_path"] = ""
            scene_item["latest_render_manifest_path"] = ""
            scene_item["review_status"] = "approved"
            scene_item["motion_review_status"] = "approved_for_motion"
            scene_item["reviewer"] = "reviewer_scene"
            scene_item["reviewed_at"] = "2026-03-29T10:00:00Z"
            scene_item["review_notes"] = "Approved still."
            scene_item["motion_reviewer"] = "reviewer_motion"
            scene_item["motion_reviewed_at"] = "2026-03-29T10:05:00Z"
            scene_item["motion_review_notes"] = "Ready for motion."
            motion_item = manifest["motion_assets"]["items"][0]
            motion_item["status"] = "done"
            motion_item["review_outcome"] = "approved"
            motion_item["latest_render_path"] = motion_proof
            motion_item["latest_render_manifest_path"] = motion_proof_manifest
            motion_item["reviewer"] = "reviewer_motion"
            motion_item["reviewed_at"] = "2026-03-29T10:06:00Z"
            motion_item["review_notes"] = "Approved motion."
            self._write_manifest_copy(temp_root, "challenger", manifest)
            result = perform_review_action(
                context,
                episode_id="challenger",
                gate_type="scene_still",
                item_id="launch_commit_console",
                decision="unapprove",
                reviewer="reviewer_1",
                notes="Reopen still review.",
            )
            updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
            scene_item = self._scene_item(updated, "launch_commit_console")
            motion_item = updated["motion_assets"]["items"][0]
            self.assertEqual(scene_item["review_status"], "pending")
            self.assertEqual(scene_item["latest_render_path"], selected_asset)
            self.assertEqual(scene_item["latest_render_manifest_path"], f"{selected_asset}.json")
            self.assertEqual(scene_item["selected_asset"], "")
            self.assertEqual(scene_item["motion_review_status"], "pending")
            self.assertEqual(scene_item["reviewer"], "")
            self.assertEqual(scene_item["motion_reviewer"], "")
            self.assertEqual(motion_item["status"], "review")
            self.assertEqual(motion_item["review_outcome"], "")
            self.assertEqual(result["decision"], "unapprove")
            detail = build_review_message_detail(context, "challenger:scene_still:launch_commit_console")
            self.assertEqual(detail["message"]["actions"], {"approve": True, "reject": True, "unapprove": False, "unreject": False})

    def test_unapprove_motion_source_reopens_dependent_motion_asset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "done"
            manifest["visual_research"]["approval"]["status"] = "approved"
            selected_asset, _selected_manifest = self._write_artifact(temp_root / "proofs" / "scene-selected.png")
            motion_proof_path = temp_root / "proofs" / "motion-proof.mp4"
            motion_proof, motion_proof_manifest = self._write_artifact(
                motion_proof_path,
                manifest_payload={"output_path": str(motion_proof_path)},
            )
            scene_item = self._scene_item(manifest, "launch_commit_console")
            scene_item["selected_asset"] = selected_asset
            scene_item["review_status"] = "approved"
            scene_item["motion_review_status"] = "approved_for_motion"
            motion_item = manifest["motion_assets"]["items"][0]
            motion_item["status"] = "done"
            motion_item["review_outcome"] = "approved"
            motion_item["latest_render_path"] = motion_proof
            motion_item["latest_render_manifest_path"] = motion_proof_manifest
            self._write_manifest_copy(temp_root, "challenger", manifest)
            perform_review_action(
                context,
                episode_id="challenger",
                gate_type="motion_source",
                item_id="launch_commit_console",
                decision="unapprove",
                reviewer="reviewer_2",
                notes="Need to revisit motion handoff.",
            )
            updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
            self.assertEqual(self._scene_item(updated, "launch_commit_console")["motion_review_status"], "pending")
            self.assertEqual(updated["motion_assets"]["items"][0]["status"], "review")
            self.assertEqual(updated["motion_assets"]["items"][0]["review_outcome"], "")

    def test_unapprove_packaging_still_restores_proof(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "done"
            manifest["visual_research"]["approval"]["status"] = "approved"
            selected_asset, _selected_manifest = self._write_artifact(temp_root / "proofs" / "packaging-selected.png")
            packaging_item = manifest["packaging_stills"]["items"][0]
            packaging_item["selected_asset"] = selected_asset
            packaging_item["latest_render_path"] = ""
            packaging_item["latest_render_manifest_path"] = ""
            packaging_item["review_status"] = "approved"
            self._write_manifest_copy(temp_root, "challenger", manifest)
            perform_review_action(
                context,
                episode_id="challenger",
                gate_type="packaging_still",
                item_id="launch_thumbnail",
                decision="unapprove",
                reviewer="reviewer_3",
                notes="Reopen packaging review.",
            )
            updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
            packaging_item = updated["packaging_stills"]["items"][0]
            self.assertEqual(packaging_item["review_status"], "pending")
            self.assertEqual(packaging_item["latest_render_path"], selected_asset)
            self.assertEqual(packaging_item["selected_asset"], "")

    def test_unreject_visual_research_reopens_pending_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "review"
            manifest["visual_research"]["approval"]["status"] = "rejected"
            manifest["visual_research"]["approval"]["reviewer"] = "mike"
            manifest["visual_research"]["approval"]["reviewed_at"] = "2026-03-29T09:00:00Z"
            manifest["visual_research"]["approval"]["notes"] = "Needs revision."
            self._write_manifest_copy(temp_root, "challenger", manifest)
            result = perform_review_action(
                context,
                episode_id="challenger",
                gate_type="visual_research",
                decision="unreject",
                reviewer="reviewer_undo",
                notes="",
            )
            updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
            approval = updated["visual_research"]["approval"]
            self.assertEqual(updated["visual_research"]["status"], "review")
            self.assertEqual(approval["status"], "pending")
            self.assertEqual(approval["reviewer"], "")
            self.assertEqual(approval["reviewed_at"], "")
            self.assertEqual(approval["notes"], "")
            self.assertEqual(result["decision"], "unreject")

    def test_unreject_scene_still_reopens_pending_without_cascade(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "done"
            manifest["visual_research"]["approval"]["status"] = "approved"
            proof_path, proof_manifest_path = self._write_artifact(temp_root / "proofs" / "scene-proof.png")
            scene_item = self._scene_item(manifest, "launch_commit_console")
            scene_item["latest_render_path"] = proof_path
            scene_item["latest_render_manifest_path"] = proof_manifest_path
            scene_item["selected_asset"] = ""
            scene_item["review_status"] = "rejected"
            scene_item["motion_review_status"] = "pending"
            scene_item["reviewer"] = "mike"
            scene_item["reviewed_at"] = "2026-03-29T09:10:00Z"
            scene_item["review_notes"] = "Reject."
            self._write_manifest_copy(temp_root, "challenger", manifest)
            result = perform_review_action(
                context,
                episode_id="challenger",
                gate_type="scene_still",
                item_id="launch_commit_console",
                decision="unreject",
                reviewer="reviewer_undo",
                notes="",
            )
            updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
            scene_item = self._scene_item(updated, "launch_commit_console")
            self.assertEqual(scene_item["review_status"], "pending")
            self.assertEqual(scene_item["latest_render_path"], proof_path)
            self.assertEqual(scene_item["latest_render_manifest_path"], proof_manifest_path)
            self.assertEqual(scene_item["motion_review_status"], "pending")
            self.assertEqual(scene_item["reviewer"], "")
            self.assertEqual(scene_item["review_notes"], "")
            self.assertEqual(result["decision"], "unreject")

    def test_unreject_motion_source_reopens_pending_without_resetting_motion_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "done"
            manifest["visual_research"]["approval"]["status"] = "approved"
            selected_asset, _selected_manifest = self._write_artifact(temp_root / "proofs" / "scene-selected.png")
            motion_proof_path = temp_root / "proofs" / "motion-proof.mp4"
            motion_proof, motion_proof_manifest = self._write_artifact(
                motion_proof_path,
                manifest_payload={"output_path": str(motion_proof_path)},
            )
            scene_item = self._scene_item(manifest, "launch_commit_console")
            scene_item["selected_asset"] = selected_asset
            scene_item["review_status"] = "approved"
            scene_item["motion_review_status"] = "rejected"
            scene_item["motion_reviewer"] = "mike"
            scene_item["motion_reviewed_at"] = "2026-03-29T09:20:00Z"
            scene_item["motion_review_notes"] = "Too risky."
            motion_item = manifest["motion_assets"]["items"][0]
            motion_item["status"] = "done"
            motion_item["review_outcome"] = "approved"
            motion_item["latest_render_path"] = motion_proof
            motion_item["latest_render_manifest_path"] = motion_proof_manifest
            self._write_manifest_copy(temp_root, "challenger", manifest)
            perform_review_action(
                context,
                episode_id="challenger",
                gate_type="motion_source",
                item_id="launch_commit_console",
                decision="unreject",
                reviewer="reviewer_undo",
                notes="",
            )
            updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
            scene_item = self._scene_item(updated, "launch_commit_console")
            motion_item = updated["motion_assets"]["items"][0]
            self.assertEqual(scene_item["motion_review_status"], "pending")
            self.assertEqual(scene_item["selected_asset"], selected_asset)
            self.assertEqual(scene_item["motion_reviewer"], "")
            self.assertEqual(motion_item["status"], "done")
            self.assertEqual(motion_item["review_outcome"], "approved")

    def test_unreject_packaging_still_reopens_pending_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "done"
            manifest["visual_research"]["approval"]["status"] = "approved"
            proof_path, proof_manifest_path = self._write_artifact(temp_root / "proofs" / "packaging-proof.png")
            packaging_item = manifest["packaging_stills"]["items"][0]
            packaging_item["latest_render_path"] = proof_path
            packaging_item["latest_render_manifest_path"] = proof_manifest_path
            packaging_item["selected_asset"] = ""
            packaging_item["review_status"] = "rejected"
            packaging_item["reviewer"] = "mike"
            packaging_item["reviewed_at"] = "2026-03-29T09:30:00Z"
            packaging_item["review_notes"] = "Reject."
            self._write_manifest_copy(temp_root, "challenger", manifest)
            perform_review_action(
                context,
                episode_id="challenger",
                gate_type="packaging_still",
                item_id="launch_thumbnail",
                decision="unreject",
                reviewer="reviewer_undo",
                notes="",
            )
            updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
            packaging_item = updated["packaging_stills"]["items"][0]
            self.assertEqual(packaging_item["review_status"], "pending")
            self.assertEqual(packaging_item["latest_render_path"], proof_path)
            self.assertEqual(packaging_item["latest_render_manifest_path"], proof_manifest_path)
            self.assertEqual(packaging_item["reviewer"], "")
            self.assertEqual(packaging_item["review_notes"], "")

    def test_unapprove_motion_asset_reopens_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "done"
            manifest["visual_research"]["approval"]["status"] = "approved"
            selected_asset, _selected_manifest = self._write_artifact(temp_root / "proofs" / "scene-selected.png")
            motion_proof_path = temp_root / "proofs" / "motion-proof.mp4"
            motion_proof, motion_proof_manifest = self._write_artifact(
                motion_proof_path,
                manifest_payload={"output_path": str(motion_proof_path)},
            )
            scene_item = self._scene_item(manifest, "launch_commit_console")
            scene_item["selected_asset"] = selected_asset
            scene_item["review_status"] = "approved"
            scene_item["motion_review_status"] = "approved_for_motion"
            motion_item = manifest["motion_assets"]["items"][0]
            motion_item["status"] = "done"
            motion_item["review_outcome"] = "approved"
            motion_item["latest_render_path"] = motion_proof
            motion_item["latest_render_manifest_path"] = motion_proof_manifest
            self._write_manifest_copy(temp_root, "challenger", manifest)
            perform_review_action(
                context,
                episode_id="challenger",
                gate_type="motion_asset",
                item_id="launch_commit_dolly",
                decision="unapprove",
                reviewer="reviewer_4",
                notes="Reopen motion review.",
            )
            updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
            motion_item = updated["motion_assets"]["items"][0]
            self.assertEqual(motion_item["status"], "review")
            self.assertEqual(motion_item["review_outcome"], "")
            detail = build_review_message_detail(context, "challenger:motion_asset:launch_commit_dolly")
            self.assertEqual(detail["message"]["actions"], {"approve": True, "reject": True, "unapprove": False, "unreject": False})

    def test_unreject_motion_asset_reopens_review_and_preserves_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "done"
            manifest["visual_research"]["approval"]["status"] = "approved"
            selected_asset, _selected_manifest = self._write_artifact(temp_root / "proofs" / "scene-selected.png")
            motion_output = temp_root / "selects" / "hero_video.mp4"
            motion_output.parent.mkdir(parents=True, exist_ok=True)
            motion_output.write_text("video", encoding="utf-8")
            motion_proof_path = temp_root / "proofs" / "motion-proof.mp4"
            motion_proof, motion_proof_manifest = self._write_artifact(
                motion_proof_path,
                manifest_payload={"output_path": str(motion_proof_path)},
            )
            scene_item = self._scene_item(manifest, "launch_commit_console")
            scene_item["selected_asset"] = selected_asset
            scene_item["review_status"] = "approved"
            scene_item["motion_review_status"] = "approved_for_motion"
            motion_item = manifest["motion_assets"]["items"][0]
            motion_item["status"] = "todo"
            motion_item["review_outcome"] = "rejected"
            motion_item["output_path"] = str(motion_output)
            motion_item["latest_render_path"] = motion_proof
            motion_item["latest_render_manifest_path"] = motion_proof_manifest
            motion_item["reviewer"] = "mike"
            motion_item["reviewed_at"] = "2026-03-29T09:40:00Z"
            motion_item["review_notes"] = "Reject."
            self._write_manifest_copy(temp_root, "challenger", manifest)
            result = perform_review_action(
                context,
                episode_id="challenger",
                gate_type="motion_asset",
                item_id="launch_commit_dolly",
                decision="unreject",
                reviewer="reviewer_undo",
                notes="",
            )
            updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
            motion_item = updated["motion_assets"]["items"][0]
            self.assertEqual(motion_item["status"], "review")
            self.assertEqual(motion_item["review_outcome"], "")
            self.assertEqual(motion_item["latest_render_path"], motion_proof)
            self.assertEqual(motion_item["latest_render_manifest_path"], motion_proof_manifest)
            self.assertEqual(motion_item["output_path"], str(motion_output))
            self.assertEqual(motion_item["reviewer"], "")
            self.assertEqual(result["decision"], "unreject")
            detail = build_review_message_detail(context, "challenger:motion_asset:launch_commit_dolly")
            self.assertEqual(detail["message"]["actions"], {"approve": True, "reject": True, "unapprove": False, "unreject": False})

    def test_unapprove_visual_research_cascades_downstream_resets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "done"
            manifest["visual_research"]["approval"]["status"] = "approved"
            manifest["visual_research"]["approval"]["reviewer"] = "vr_reviewer"
            manifest["visual_research"]["approval"]["reviewed_at"] = "2026-03-29T09:00:00Z"
            manifest["visual_research"]["approval"]["notes"] = "Approved."
            scene_selected, _scene_selected_manifest = self._write_artifact(temp_root / "proofs" / "scene-selected.png")
            packaging_selected, _packaging_selected_manifest = self._write_artifact(temp_root / "proofs" / "packaging-selected.png")
            motion_proof_path = temp_root / "proofs" / "motion-proof.mp4"
            motion_proof, motion_proof_manifest = self._write_artifact(
                motion_proof_path,
                manifest_payload={"output_path": str(motion_proof_path)},
            )
            scene_item = self._scene_item(manifest, "launch_commit_console")
            scene_item["selected_asset"] = scene_selected
            scene_item["latest_render_path"] = ""
            scene_item["latest_render_manifest_path"] = ""
            scene_item["review_status"] = "approved"
            scene_item["motion_review_status"] = "approved_for_motion"
            packaging_item = manifest["packaging_stills"]["items"][0]
            packaging_item["selected_asset"] = packaging_selected
            packaging_item["latest_render_path"] = ""
            packaging_item["latest_render_manifest_path"] = ""
            packaging_item["review_status"] = "approved"
            motion_item = manifest["motion_assets"]["items"][0]
            motion_item["status"] = "done"
            motion_item["review_outcome"] = "approved"
            motion_item["latest_render_path"] = motion_proof
            motion_item["latest_render_manifest_path"] = motion_proof_manifest
            self._write_manifest_copy(temp_root, "challenger", manifest)
            result = perform_review_action(
                context,
                episode_id="challenger",
                gate_type="visual_research",
                decision="unapprove",
                reviewer="reviewer_5",
                notes="Need another pass through coverage.",
            )
            updated = load_episode_manifest(temp_root / "episodes/challenger.toml")
            self.assertEqual(updated["visual_research"]["status"], "review")
            self.assertEqual(updated["visual_research"]["approval"]["status"], "pending")
            self.assertEqual(updated["visual_research"]["approval"]["reviewer"], "")
            self.assertEqual(self._scene_item(updated, "launch_commit_console")["review_status"], "pending")
            self.assertEqual(self._scene_item(updated, "launch_commit_console")["selected_asset"], "")
            self.assertEqual(self._scene_item(updated, "launch_commit_console")["motion_review_status"], "pending")
            self.assertEqual(updated["packaging_stills"]["items"][0]["review_status"], "pending")
            self.assertEqual(updated["motion_assets"]["items"][0]["status"], "review")
            self.assertEqual(updated["motion_assets"]["items"][0]["review_outcome"], "")
            self.assertEqual(result["state"]["lanes"]["visual_research"]["status"], "review")

    def test_approve_visual_research_requires_contact_sheet(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "review"
            manifest["visual_research"]["approval"]["status"] = "pending"
            manifest["visual_research"]["contact_sheet_path"] = str(temp_root / "visual_research" / "missing-contact-sheet.pdf")
            self._write_manifest_copy(temp_root, "challenger", manifest)
            with self.assertRaises(SystemExit) as exc:
                perform_review_action(
                    context,
                    episode_id="challenger",
                    gate_type="visual_research",
                    decision="approve",
                    reviewer="reviewer_1",
                    notes="Coverage is complete.",
                )
            self.assertIn("six visual research deliverables", str(exc.exception))

    def test_visual_research_detail_blocks_approve_when_source_inventory_is_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "review"
            manifest["visual_research"]["approval"]["status"] = "pending"
            inventory_path = temp_root / "source_inventory.json"
            raw_asset = temp_root / "source.png"
            raw_asset.write_text("image", encoding="utf-8")
            inventory_path.write_text(
                json.dumps(
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
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            manifest["visual_research"]["source_inventory_path"] = str(inventory_path)
            self._write_manifest_copy(temp_root, "challenger", manifest)

            detail = build_review_message_detail(context, "challenger:visual_research:visual_research")
            self.assertFalse(detail["message"]["actions"]["approve"])
            self.assertIn("act1_console_01", detail["message"]["blocked_actions"]["approve"])
            self.assertEqual(detail["message"]["source_inventory"]["unresolved_source_ids"], ["act1_console_01"])

    def test_approve_visual_research_requires_resolved_source_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "review"
            manifest["visual_research"]["approval"]["status"] = "pending"
            inventory_path = temp_root / "source_inventory.json"
            raw_asset = temp_root / "source.png"
            raw_asset.write_text("image", encoding="utf-8")
            inventory_path.write_text(
                json.dumps(
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
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            manifest["visual_research"]["source_inventory_path"] = str(inventory_path)
            self._write_manifest_copy(temp_root, "challenger", manifest)

            with self.assertRaises(SystemExit) as exc:
                perform_review_action(
                    context,
                    episode_id="challenger",
                    gate_type="visual_research",
                    decision="approve",
                    reviewer="reviewer_1",
                    notes="Coverage is complete.",
                )
            self.assertIn("text-clear or cleaned", str(exc.exception))

    def test_unreject_scene_history_displays_pending_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "done"
            manifest["visual_research"]["approval"]["status"] = "approved"
            proof_path, proof_manifest_path = self._write_artifact(temp_root / "proofs" / "scene-proof.png")
            scene_item = self._scene_item(manifest, "launch_commit_console")
            scene_item["latest_render_path"] = proof_path
            scene_item["latest_render_manifest_path"] = proof_manifest_path
            scene_item["review_status"] = "rejected"
            self._write_manifest_copy(temp_root, "challenger", manifest)
            perform_review_action(
                context,
                episode_id="challenger",
                gate_type="scene_still",
                item_id="launch_commit_console",
                decision="unreject",
                reviewer="reviewer_undo",
                notes="",
            )
            detail = build_review_message_detail(context, "challenger:scene_still:launch_commit_console")
            self.assertEqual(detail["message"]["history"][0]["decision"], "unreject")
            self.assertEqual(detail["message"]["history"][0]["status"], "pending")

    def test_unreject_motion_asset_history_displays_review_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            context = self._build_temp_context(temp_root)
            manifest = load_episode_manifest(AGENTS_ROOT / "episodes/challenger.toml")
            manifest["visual_research"]["status"] = "done"
            manifest["visual_research"]["approval"]["status"] = "approved"
            selected_asset, _selected_manifest = self._write_artifact(temp_root / "proofs" / "scene-selected.png")
            motion_proof_path = temp_root / "proofs" / "motion-proof.mp4"
            motion_proof, motion_proof_manifest = self._write_artifact(
                motion_proof_path,
                manifest_payload={"output_path": str(motion_proof_path)},
            )
            scene_item = self._scene_item(manifest, "launch_commit_console")
            scene_item["selected_asset"] = selected_asset
            scene_item["review_status"] = "approved"
            scene_item["motion_review_status"] = "approved_for_motion"
            motion_item = manifest["motion_assets"]["items"][0]
            motion_item["status"] = "todo"
            motion_item["review_outcome"] = "rejected"
            motion_item["latest_render_path"] = motion_proof
            motion_item["latest_render_manifest_path"] = motion_proof_manifest
            self._write_manifest_copy(temp_root, "challenger", manifest)
            perform_review_action(
                context,
                episode_id="challenger",
                gate_type="motion_asset",
                item_id="launch_commit_dolly",
                decision="unreject",
                reviewer="reviewer_undo",
                notes="",
            )
            detail = build_review_message_detail(context, "challenger:motion_asset:launch_commit_dolly")
            self.assertEqual(detail["message"]["history"][0]["decision"], "unreject")
            self.assertEqual(detail["message"]["history"][0]["status"], "review")


if __name__ == "__main__":
    unittest.main()
