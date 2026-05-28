#!/usr/bin/env node
import fs from "node:fs";
import crypto from "node:crypto";
import path from "node:path";
import {
  endScreenPaletteContractFailures,
  endScreenPaletteContractForManifest,
  endScreenPalettePlayerFailures,
} from "./living_cover_end_screen_palette_contract.mjs";

const EPISODES_ROOT = "/Users/mike/Episodes_CascadeEffects";
const REVIEW_SERVER_BASE_URL = "http://127.0.0.1:8766";
const REVIEW_INDEX_PATH = "/Users/mike/Episodes_CascadeEffects/first-eight-rolling-caption-rail-review.html";
const HYATT_BLIP_REPAIRED_VOICE_MASTER_PATH =
  "/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/audio_repairs/live_load_long_i_blip_repair_20260519T184526Z/masters/Ep3-Hyatt-Regency.live_load_long_i_blip_repaired_voice_master.wav";
const HYATT_SUPERSEDED_DEFECTIVE_VOICE_MASTER_PATH =
  "/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/audio_repairs/live_load_long_i_repair_20260517T204138Z/masters/Ep3-Hyatt-Regency.live_load_long_i_voice_master.wav";

const REQUIRED_ROOT = {
  rail_preset_id: "fixed_16x9_right_rail_v1",
  rail_content_model_id: "rolling_caption_anchor_v1",
  caption_display_model: "rolling_rail_caption_window_v1",
  caption_window_role: "middle_two_thirds_right_rail",
  caption_blur_scope: "none",
  caption_window_treatment_model: "transparent_caption_mask_only_v1",
  caption_highlight_source: "living_cover_cue_map_key_phrases",
  caption_palette_source: "sampled_episode_backplate",
  caption_display_chunking: "script_locked_chunk_split_v1",
  review_chrome_policy: "hidden_in_render_mode",
  review_control_model: "single_foreground_review_transport_v1",
  review_transport_scrub_model: "foreground_transport_scrub_lock_v1",
  legacy_review_chrome_suppression_model: "predecessor_review_chrome_hidden_in_review_mode_v1",
  highlight_render_policy: "reviewed_cue_map_spans_only",
  caption_motion_model: "constant_speed_audio_time_aligned_scroll_v2",
  caption_timeline_layout_model: "audio_time_positioned_stack_v1",
  caption_sync_target: "pre_vo_reading_lead_active_band_v1",
  caption_reading_lead_seconds: 0.65,
  intro_trim_model: "first_eight_intro_trim_6s_v1",
  caption_intro_visibility_gate_model: "first_vo_intro_hold_fade_v1",
  caption_constant_speed_scope: "per_episode_constant_px_per_second",
  caption_playback_clock_model: "media_time_smoothed_raf_clock_v3",
  caption_stack_render_model: "compositor_linear_transform_driver_v1",
  caption_scroll_smoothness_model: "compositor_linear_transform_driver_v1",
  caption_runtime_coverage_model: "full_vo_runtime_visible_caption_coverage_v1",
  caption_end_screen_handoff_model: "review_approved_end_screen_entry_v1",
  caption_density_resolution_model: "merge_dense_chunks_no_speed_ramp_v1",
  caption_display_line_wrap_model: "pixel_budgeted_deterministic_line_wrap_v1",
  caption_line_opacity_model: "viewport_distance_smoothstep_v1",
  highlight_phrase_scope: "exact_authored_span_only",
  caption_highlight_model_id: "lesson_takeaway_highlight_v1",
  highlight_semantic_role: "story_lesson_takeaway",
  highlight_density_model: "memorable_takeaway_cadence_v1",
  highlight_color_model: "source_sampled_backplate_contrast_takeaway_accent_v3",
  highlight_visual_timing_model: "active_band_presence_aligned_v1",
  caption_layout_collision_guard: "fixed_line_box_visual_gap_guard_v1",
  proof_integration_model: "predecessor_html_rolling_rail_injection_v1",
};
const CAPTION_MOTION_MODEL = "constant_speed_audio_time_aligned_scroll_v2";
const CAPTION_TIMELINE_LAYOUT_MODEL = "audio_time_positioned_stack_v1";
const CAPTION_SYNC_TARGET = "pre_vo_reading_lead_active_band_v1";
const CAPTION_READING_LEAD_SECONDS = 0.65;
const INTRO_TRIM_MODEL = "first_eight_intro_trim_6s_v1";
const INTRO_TRIM_SECONDS = 6;
const PREVIOUS_VOICE_START_OFFSET_SECONDS = 9.601451;
const VOICE_START_OFFSET_SECONDS = 3.601451;
const VOICE_START_OFFSET_SLUG = "3s601";
const CAPTION_INTRO_VISIBILITY_GATE_MODEL = "first_vo_intro_hold_fade_v1";
const CAPTION_CONSTANT_SPEED_SCOPE = "per_episode_constant_px_per_second";
const CAPTION_PLAYBACK_CLOCK_MODEL = "media_time_smoothed_raf_clock_v3";
const CAPTION_STACK_RENDER_MODEL = "compositor_linear_transform_driver_v1";
const CAPTION_SCROLL_SMOOTHNESS_MODEL = "compositor_linear_transform_driver_v1";
const CAPTION_STACK_RENDER_MODEL_ALLOWED = new Set([
  CAPTION_STACK_RENDER_MODEL,
  "visible_window_caption_virtualization_v1",
]);
const CAPTION_SCROLL_SMOOTHNESS_MODEL_ALLOWED = new Set([
  CAPTION_SCROLL_SMOOTHNESS_MODEL,
  "visible_window_caption_virtualization_v1",
]);
const CAPTION_DENSITY_RESOLUTION_MODEL = "merge_dense_chunks_no_speed_ramp_v1";
const CAPTION_WINDOW_TREATMENT_MODEL = "transparent_caption_mask_only_v1";
const CAPTION_RUNTIME_COVERAGE_MODEL = "full_vo_runtime_visible_caption_coverage_v1";
const CAPTION_END_SCREEN_HANDOFF_MODEL = "review_approved_end_screen_entry_v1";
const REVIEW_TRANSPORT_SCRUB_MODEL = "foreground_transport_scrub_lock_v1";
const PASS_PLAYING_SCRUB = "pass_foreground_scrub_works_while_playing";
const PASS_END_SCREEN_RUNTIME_QA = "pass_end_screen_fade_timing_and_adaptive_palette";
const PASS_INHERITED_END_SCREEN = "pass_inherited_end_screen_layers_hidden";
const END_SCREEN_ADAPTIVE_RENDER_AUDIT_MODEL = "end_screen_adaptive_render_audit_v1";
const PASS_ADAPTIVE_RENDER_AUDIT = "pass_end_screen_adaptive_render_audit_v1";
const PASS_ADAPTIVE_COMPUTED_STYLE = "pass_end_screen_adaptive_computed_styles_match_contract";
const PASS_ADAPTIVE_PIXEL_SAMPLE = "pass_end_screen_adaptive_pixel_samples_match_composited_contract";
const PASS_TACOMA_RAIN_GUARD = "pass_tacoma_rain_performance_guard_active";
const TACOMA_K3_B3_HIGHLIGHT_MERGE_MODEL = "tacoma_k3_b3_backplate_with_lesson_takeaway_highlights_v1";
const TACOMA_K3_B3_SOURCE_ART_SHA256 = "580e69bea2f7d278f2aed000ccf669cfaa45fcbf562238694085809eac4363b8";
const TACOMA_K3_B3_HIGHLIGHT_MERGE_READ = "pass_k3_b3_backplate_with_approved_takeaway_highlights";
const CAPTION_AUDIO_SYNC_MODEL = "source_sidecar_audio_time_v1";
const CAPTION_STACK_PAINT_CONTAINMENT_READ = "pass_no_caption_stack_paint_clip";
const RIGHT_RAIL_CAPTION_PAINT_VISIBILITY_READ = "pass_visible_right_rail_caption_lines_are_painted";
const CAPTION_MIN_CONSTANT_SPEED_PX_PER_SECOND = 48;
const CAPTION_MAX_CONSTANT_SPEED_PX_PER_SECOND = 54;
const CAPTION_ACTIVE_BAND_LOWER_DELTA_PX = 96;
const CAPTION_HIGHLIGHT_MODEL_ID = "lesson_takeaway_highlight_v1";
const HIGHLIGHT_SEMANTIC_ROLE = "story_lesson_takeaway";
const HIGHLIGHT_DENSITY_MODEL = "memorable_takeaway_cadence_v1";
const HIGHLIGHT_COLOR_MODEL = "source_sampled_backplate_contrast_takeaway_accent_v3";
const EXPECTED_LESSON_TAKEAWAY_COUNTS = {
  challenger: 32,
  "therac-25": 28,
  "hyatt-regency": 22,
  semmelweis: 22,
  "tacoma-narrows": 22,
  "piltdown-man": 22,
  "737-max": 25,
  titanic: 20,
};
const HIGHLIGHT_VISUAL_TIMING_MODEL = "active_band_presence_aligned_v1";
const HIGHLIGHT_MIN_BACKPLATE_CONTRAST_RATIO = 2.0;
const HIGHLIGHT_P20_BACKPLATE_CONTRAST_RATIO = 2.45;
const HIGHLIGHT_MIN_BACKPLATE_COLOR_DELTA = 58;
const HIGHLIGHT_ACTIVE_TEXT_MIN_DELTA = 48;
const HIGHLIGHT_MUTED_TEXT_MIN_DELTA = 44;
const HIGHLIGHT_ACTIVE_TEXT_MIN_CONTRAST = 1.0;
const HIGHLIGHT_MUTED_TEXT_MIN_CONTRAST = 1.12;
const HUMAN_APPROVED_HIGHLIGHT_ACCENT_OVERRIDES = {
  semmelweis: {
    selected_hex: "#efef9f",
    highlight_override_read: "pass_review_safe_pale_highlight_accent",
  },
};
const AMBIENT_FRAME_CLOCK_MODEL = "render_frame_time_locked_to_composition_fps_v1";
const AMBIENT_RENDER_CLOCK_READ = "pass_ambient_time_uses_render_frame_seconds";
const AMBIENT_WALL_CLOCK_DRIFT_SUPPRESSION_READ = "pass_no_render_mode_wall_clock_ambient_mutation";
const AMBIENT_FRAME_CLOCK_EPISODES = new Set(["therac-25", "semmelweis"]);
const FORBIDDEN_REVIEW_CHROME_TEXT = [
  "Sample cue states",
  "Buttons seek",
  "Current Gate",
  "Review-intensity",
  "ambient/effects layer review-ready",
  "timeline scrubber",
];
const CAPTION_LAYOUT_COLLISION_GUARD = "fixed_line_box_visual_gap_guard_v1";
const CAPTION_MIN_RENDERED_LINE_GAP_PX = 40;
const YOUTUBE_END_SCREEN_TEMPLATE_ID = "adaptive_titleless_youtube_end_screen_overlay_on_living_cover_v1";
const END_SCREEN_FADE_TIMING_MODEL = "caption_exit_aligned_end_screen_fade_v1";
const YOUTUBE_LEGAL_WINDOW_END_SCREEN_ENTRY_MODEL = "youtube_legal_window_end_screen_entry_v1";
const YOUTUBE_PLACEHOLDER_BORDERLESS_UNDERLAY_MODEL = "youtube_placeholder_borderless_underlay_v1";
const END_SCREEN_TRANSITION_DURATION_SECONDS = 0.3;
const END_SCREEN_PALETTE_TREATMENT_MODEL = "local_backplate_perceptual_target_palette_v3";
const END_SCREEN_ADAPTIVE_VARIABILITY_MODEL = "backplate_hue_preserved_perceptual_variability_v1";
const OUTRO_POLICY = "subtle_tail_outro_v1";
const REVIEW_APPROVED_END_SCREEN_FADE_START_SECONDS = {
  "challenger": 19 * 60 + 43,
  "therac-25": 18 * 60 + 6,
  "hyatt-regency": 13 * 60 + 57,
  "semmelweis": 14 * 60 + 17,
  "tacoma-narrows": 14 * 60 + 4,
  "piltdown-man": 14 * 60 + 3,
  "737-max": 15 * 60 + 46,
  "titanic": 12 * 60 + 24,
};
const CAPTION_DISPLAY_LINE_WRAP_MODEL = "pixel_budgeted_deterministic_line_wrap_v1";
const CAPTION_FONT_SIZE_PX = 32;
const CAPTION_TEXT_STACK_WIDTH_PX = 402;
const CAPTION_DISPLAY_LINE_MAX_WIDTH_PX = 360;
const AMBIENT_RIGHT_RAIL_MOTION_POLICY = "ambient_motion_allowed_under_rail_text_v1";
const FOREGROUND_MATTE_POLICY = "tower_shuttle_only_no_light_or_right_rail_mask";
const RIGHT_RAIL_LEFT_X = 1108;
const END_SCREEN_PALETTE_MODEL = "backplate_sampled_youtube_end_screen_palette_v1";

function parseArgs(argv) {
  const out = {
    proofManifest: "",
    player: "",
    json: false,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--proof-manifest") out.proofManifest = argv[++i] || "";
    else if (arg === "--player") out.player = argv[++i] || "";
    else if (arg === "--json") out.json = true;
    else if (arg === "--help" || arg === "-h") {
      usage(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  if (!out.proofManifest) usage(2, "Missing --proof-manifest");
  return out;
}

function usage(exitCode, message = "") {
  if (message) console.error(message);
  console.error(
    "Usage: node scripts/validate_living_cover_rolling_caption_rail.mjs --proof-manifest PATH [--player PATH] [--json]",
  );
  process.exit(exitCode);
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function readJsonIfExists(filePath) {
  if (!filePath || !fs.existsSync(filePath)) return null;
  try {
    return readJson(filePath);
  } catch {
    return null;
  }
}

function parseVttCueCount(filePath) {
  if (!filePath || !fs.existsSync(filePath)) return 0;
  const text = fs.readFileSync(filePath, "utf8");
  return (text.match(/-->/g) || []).length;
}

function parseTimecode(text) {
  const match = String(text || "").match(/(?:(\d+):)?(\d{2}):(\d{2})[.,](\d{3})/);
  if (!match) return null;
  return Number(match[1] || 0) * 3600 + Number(match[2] || 0) * 60 + Number(match[3] || 0) + Number(match[4] || 0) / 1000;
}

function parseFirstVttStart(filePath) {
  if (!filePath || !fs.existsSync(filePath)) return null;
  const line = fs.readFileSync(filePath, "utf8").split(/\r?\n/).find((candidate) => candidate.includes("-->"));
  if (!line) return null;
  return parseTimecode(line.split("-->")[0].trim());
}

function valueAt(obj, dotted) {
  return dotted.split(".").reduce((cur, part) => (cur && cur[part] !== undefined ? cur[part] : undefined), obj);
}

function endScreenEntryTimingModel(manifest, endScreenContext = manifest.end_screen_context || {}) {
  return (
    manifest.end_screen_entry_timing_model ||
    endScreenContext.end_screen_entry_timing_model ||
    valueAt(endScreenContext, "end_screen_timing.endScreenEntryTimingModel") ||
    valueAt(endScreenContext, "end_screen_timing.fadeTimingModel") ||
    endScreenContext.end_screen_fade_timing_model ||
    manifest.end_screen_fade_timing_model ||
    ""
  );
}

function isYoutubeLegalWindowEndScreenEntry(manifest, endScreenContext = manifest.end_screen_context || {}) {
  return endScreenEntryTimingModel(manifest, endScreenContext) === YOUTUBE_LEGAL_WINDOW_END_SCREEN_ENTRY_MODEL;
}

function expectedYoutubeFadeStartSeconds(manifest, endScreenContext = manifest.end_screen_context || {}) {
  if (isYoutubeLegalWindowEndScreenEntry(manifest, endScreenContext)) {
    const duration = Number(
      manifest.duration_seconds ||
        manifest.approved_audio?.duration_seconds ||
        manifest.review_audio_mix?.duration_seconds ||
        valueAt(endScreenContext, "end_screen_timing.safeWindowEndSeconds"),
    );
    return Number.isFinite(duration) ? Number((duration - 20).toFixed(6)) : NaN;
  }
  return Number(
    manifest.review_approved_youtube_placeholder_fade_start_seconds ??
      endScreenContext.review_approved_youtube_placeholder_fade_start_seconds ??
      valueAt(endScreenContext, "end_screen_timing.reviewApprovedYoutubePlaceholderFadeStartSeconds") ??
      REVIEW_APPROVED_END_SCREEN_FADE_START_SECONDS[manifest.episode_id],
  );
}

function aircraftRouteStatsFromHtml(html) {
  const block = String(html || "").match(/const aircraftEvents = \[([\s\S]*?)\];/)?.[1] || "";
  const routes = [];
  for (const match of block.matchAll(/\{([\s\S]*?)\}/g)) {
    const eventText = match[1];
    const route = {};
    for (const key of ["start", "x0", "x1", "y0", "y1"]) {
      const value = eventText.match(new RegExp(`"?${key}"?\\s*:\\s*([-0-9.]+)`));
      if (value) route[key] = Number(value[1]);
    }
    if (Number.isFinite(route.x0) || Number.isFinite(route.x1)) routes.push(route);
  }
  const rightRailRoutes = routes.filter(
    (route) => Number(route.start || 0) < 1188 && Math.max(route.x0 || 0, route.x1 || 0) >= RIGHT_RAIL_LEFT_X,
  );
  return {
    routes,
    rightRailRoutes,
    aircraftRightRailCutoffRemoved:
      !/state\.x\s*>=\s*railSafeLeft\s*-\s*50/.test(html) && !/state\.x\s*<\s*railSafeLeft\s*-\s*50/.test(html),
  };
}

function resolveCandidate(candidate, baseDir) {
  if (!candidate || candidate === "TBD" || candidate === "not_found") return "";
  if (path.isAbsolute(candidate)) return candidate;
  return path.resolve(baseDir || process.cwd(), candidate);
}

function attrValue(tag, name) {
  const match = String(tag || "").match(new RegExp(`${name}\\s*=\\s*("([^"]*)"|'([^']*)'|([^\\s>]+))`, "i"));
  return match ? (match[2] || match[3] || match[4] || "").trim() : "";
}

function captionTrackInfoFromHtml(html, sourceRoot) {
  const tags = String(html || "").match(/<track\b[^>]*>/gi) || [];
  const tag =
    tags.find((candidate) => /id\s*=\s*["']captionTrack["']/i.test(candidate)) ||
    tags.find((candidate) => /kind\s*=\s*["']captions["']/i.test(candidate)) ||
    "";
  if (!tag) return {};
  const src = attrValue(tag, "src");
  return {
    path: /^https?:|^data:/i.test(src) ? "" : resolveCandidate(src, sourceRoot),
    offsetSeconds: Number(attrValue(tag, "data-offset-seconds")),
    rawTimingPath: resolveCandidate(attrValue(tag, "data-caption-timing-source-path"), sourceRoot),
    offsetVttSha256: attrValue(tag, "data-offset-vtt-sha256"),
  };
}

function extractInjectedConstValue(html, name) {
  const needle = `const ${name} = `;
  const start = String(html || "").indexOf(needle);
  if (start < 0) return "";
  let index = start + needle.length;
  while (/\s/.test(html[index])) index += 1;
  const open = html[index];
  const close = open === "[" ? "]" : open === "{" ? "}" : "";
  if (!close) {
    const end = html.indexOf(";", index);
    return end >= 0 ? html.slice(index, end) : "";
  }
  let depth = 0;
  let quote = "";
  let escaped = false;
  for (let cursor = index; cursor < html.length; cursor += 1) {
    const char = html[cursor];
    if (quote) {
      if (escaped) escaped = false;
      else if (char === "\\") escaped = true;
      else if (char === quote) quote = "";
      continue;
    }
    if (char === '"' || char === "'" || char === "`") {
      quote = char;
      continue;
    }
    if (char === open) depth += 1;
    if (char === close) {
      depth -= 1;
      if (depth === 0) return html.slice(index, cursor + 1);
    }
  }
  return "";
}

function parseInjectedJsonish(html, name) {
  const value = extractInjectedConstValue(html, name);
  if (!value) return null;
  try {
    return Function(`"use strict"; return (${value});`)();
  } catch {
    return null;
  }
}

function samePath(a, b) {
  return Boolean(a && b) && path.resolve(a) === path.resolve(b);
}

function samePathOrSha(a, b, aSha, bSha) {
  return samePath(a, b) || (hasNonEmptyString(aSha) && hasNonEmptyString(bSha) && aSha === bSha);
}

function hasNonEmptyString(value) {
  return typeof value === "string" && value.trim().length > 0 && !/^TBD|not_found$/i.test(value.trim());
}

function cleanText(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function phraseWordCount(value) {
  return cleanText(value).split(/\s+/).filter(Boolean).length;
}

function estimatedCaptionCharWidthEm(char) {
  if (char === " ") return 0.33;
  if (/[\.,:;!|'’`]/u.test(char)) return 0.24;
  if (/[ilI1\[\]\(\)]/u.test(char)) return 0.3;
  if (/[fjrt]/u.test(char)) return 0.42;
  if (/[mwMW]/u.test(char)) return 0.86;
  if (/[A-Z]/u.test(char)) return 0.68;
  if (/[0-9]/u.test(char)) return 0.56;
  if (/[-]/u.test(char)) return 0.32;
  return 0.54;
}

function estimatedCaptionLineWidthPx(text) {
  return Number(
    Array.from(String(text || "")).reduce((total, char) => total + estimatedCaptionCharWidthEm(char), 0) *
      CAPTION_FONT_SIZE_PX,
  );
}

function maxEstimatedDisplayLineWidthPx(chunks) {
  let maxWidth = 0;
  for (const chunk of chunks || []) {
    const lines = Array.isArray(chunk?.display_lines) && chunk.display_lines.length ? chunk.display_lines : [chunk?.text || ""];
    for (const line of lines) maxWidth = Math.max(maxWidth, estimatedCaptionLineWidthPx(line));
  }
  return Number(maxWidth.toFixed(1));
}

function maxHighlightGapSeconds(spans, durationSeconds) {
  if (!spans.length) return null;
  const starts = spans.map((span) => Number(span.timing_window_seconds?.[0])).filter(Number.isFinite).sort((a, b) => a - b);
  if (!starts.length) return null;
  let maxGap = 0;
  for (let index = 1; index < starts.length; index += 1) maxGap = Math.max(maxGap, starts[index] - starts[index - 1]);
  if (Number.isFinite(durationSeconds)) maxGap = Math.max(maxGap, durationSeconds - starts[starts.length - 1]);
  return Number(maxGap.toFixed(3));
}

function hexToRgb(hex) {
  const value = String(hex || "").replace("#", "").padEnd(6, "0").slice(0, 6);
  return [parseInt(value.slice(0, 2), 16), parseInt(value.slice(2, 4), 16), parseInt(value.slice(4, 6), 16)];
}

function relativeLuminance(rgb) {
  const channels = (rgb || [0, 0, 0]).map((channel) => {
    const value = Math.max(0, Math.min(255, Number(channel) || 0)) / 255;
    return value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

function contrastRatio(a, b) {
  const lighter = Math.max(relativeLuminance(a), relativeLuminance(b));
  const darker = Math.min(relativeLuminance(a), relativeLuminance(b));
  return Number(((lighter + 0.05) / (darker + 0.05)).toFixed(3));
}

function colorDistance(a, b) {
  if (!Array.isArray(a) || !Array.isArray(b)) return 0;
  return Number(Math.sqrt([0, 1, 2].reduce((sum, index) => sum + (Number(a[index]) - Number(b[index])) ** 2, 0)).toFixed(3));
}

function percentile(values, ratio) {
  const numbers = values.map(Number).filter(Number.isFinite).sort((a, b) => a - b);
  if (!numbers.length) return 0;
  const index = Math.max(0, Math.min(numbers.length - 1, Math.floor((numbers.length - 1) * Math.max(0, Math.min(1, ratio)))));
  return numbers[index];
}

function isNearWhite(rgb) {
  if (!Array.isArray(rgb)) return true;
  return Math.min(...rgb) >= 226 && Math.max(...rgb) - Math.min(...rgb) <= 34;
}

function highlightDistinctnessMetrics(highlightHex, activeTextHex, mutedTextHex, backplateSampleHexes = []) {
  const highlight = hexToRgb(highlightHex);
  const active = hexToRgb(activeTextHex || "#f7efe1");
  const muted = hexToRgb(mutedTextHex || "#b9c8d8");
  const backplateSamples = backplateSampleHexes
    .map((hex) => hexToRgb(hex))
    .filter((rgb) => Array.isArray(rgb));
  const activeDelta = colorDistance(highlight, active);
  const mutedDelta = colorDistance(highlight, muted);
  const activeContrast = contrastRatio(highlight, active);
  const mutedContrast = contrastRatio(highlight, muted);
  const backplateContrasts = backplateSamples.map((sample) => contrastRatio(highlight, sample));
  const backplateDeltas = backplateSamples.map((sample) => colorDistance(highlight, sample));
  const minimumBackplateContrast = backplateContrasts.length ? Math.min(...backplateContrasts) : 0;
  const p20BackplateContrast = percentile(backplateContrasts, 0.2);
  const minimumBackplateDelta = backplateDeltas.length ? Math.min(...backplateDeltas) : 0;
  return {
    activeDelta,
    mutedDelta,
    activeContrast,
    mutedContrast,
    minimumBackplateContrast: Number(minimumBackplateContrast.toFixed(3)),
    p20BackplateContrast: Number(p20BackplateContrast.toFixed(3)),
    minimumBackplateDelta: Number(minimumBackplateDelta.toFixed(3)),
    pass:
      !isNearWhite(highlight) &&
      activeDelta >= HIGHLIGHT_ACTIVE_TEXT_MIN_DELTA &&
      mutedDelta >= HIGHLIGHT_MUTED_TEXT_MIN_DELTA &&
      activeContrast >= HIGHLIGHT_ACTIVE_TEXT_MIN_CONTRAST &&
      mutedContrast >= HIGHLIGHT_MUTED_TEXT_MIN_CONTRAST &&
      (!backplateSamples.length ||
        (minimumBackplateContrast >= HIGHLIGHT_MIN_BACKPLATE_CONTRAST_RATIO &&
          p20BackplateContrast >= HIGHLIGHT_P20_BACKPLATE_CONTRAST_RATIO &&
          minimumBackplateDelta >= HIGHLIGHT_MIN_BACKPLATE_COLOR_DELTA)),
  };
}

function humanApprovedHighlightOverridePass(manifest, span, colorQa, highlightHex, distinctness) {
  const override = HUMAN_APPROVED_HIGHLIGHT_ACCENT_OVERRIDES[manifest.episode_id];
  if (!override) return false;
  const recordedOverrideRead =
    span.highlight_override_read ||
    colorQa.highlight_override_read ||
    valueAt(manifest, "highlight_color_qa.highlight_override_read") ||
    valueAt(manifest, "caption_context.highlight_color_qa.highlight_override_read") ||
    valueAt(manifest, "rough_assembly_reads.highlight_override_read");
  return (
    String(highlightHex || "").toLowerCase() === override.selected_hex &&
    recordedOverrideRead === override.highlight_override_read &&
    !isNearWhite(hexToRgb(highlightHex)) &&
    distinctness.activeDelta >= HIGHLIGHT_ACTIVE_TEXT_MIN_DELTA &&
    distinctness.mutedDelta >= HIGHLIGHT_MUTED_TEXT_MIN_DELTA &&
    distinctness.activeContrast >= HIGHLIGHT_ACTIVE_TEXT_MIN_CONTRAST &&
    distinctness.minimumBackplateContrast >= HIGHLIGHT_MIN_BACKPLATE_CONTRAST_RATIO &&
    distinctness.p20BackplateContrast >= HIGHLIGHT_P20_BACKPLATE_CONTRAST_RATIO &&
    distinctness.minimumBackplateDelta >= HIGHLIGHT_MIN_BACKPLATE_COLOR_DELTA
  );
}

function check(result, condition, id, detail) {
  result.checks.push({
    id,
    pass: Boolean(condition),
    detail,
  });
  if (!condition) result.failures.push(`${id}: ${detail}`);
}

function borderlessUnderlayModel(value) {
  return String(value || "") === YOUTUBE_PLACEHOLDER_BORDERLESS_UNDERLAY_MODEL;
}

function validateEndScreenAdaptiveRenderAudit(manifest, result, manifestPath) {
  const baseDir = path.dirname(manifestPath);
  const endScreenContext = manifest.end_screen_context || {};
  const auditPathRaw =
    manifest.end_screen_adaptive_render_audit_path ||
    endScreenContext.end_screen_adaptive_render_audit_path ||
    valueAt(manifest, "caption_context.end_screen_adaptive_render_audit_path") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.end_screen_adaptive_render_audit_path") ||
    valueAt(manifest, "qa.end_screen_adaptive_render_audit_path") ||
    valueAt(manifest, "proof_artifacts.end_screen_adaptive_render_audit_path");
  const auditPath = resolveCandidate(auditPathRaw, baseDir);
  const audit = readJsonIfExists(auditPath);
  const auditShaRead =
    manifest.end_screen_adaptive_render_audit_sha256 ||
    endScreenContext.end_screen_adaptive_render_audit_sha256 ||
    valueAt(manifest, "proof_artifacts.end_screen_adaptive_render_audit_sha256");
  const auditSha = auditPath && fs.existsSync(auditPath)
    ? crypto.createHash("sha256").update(fs.readFileSync(auditPath)).digest("hex")
    : "";
  const renderRead =
    manifest.end_screen_adaptive_render_audit_read ||
    endScreenContext.end_screen_adaptive_render_audit_read ||
    valueAt(manifest, "qa.end_screen_adaptive_render_audit_read");
  const computedRead =
    manifest.end_screen_adaptive_computed_style_read ||
    endScreenContext.end_screen_adaptive_computed_style_read ||
    valueAt(manifest, "qa.end_screen_adaptive_computed_style_read");
  const pixelRead =
    manifest.end_screen_adaptive_pixel_sample_read ||
    endScreenContext.end_screen_adaptive_pixel_sample_read ||
    valueAt(manifest, "qa.end_screen_adaptive_pixel_sample_read");
  const placeholderStyleModel =
    audit?.placeholder_style_model ||
    manifest.end_screen_placeholder_style_model ||
    endScreenContext.end_screen_placeholder_style_model ||
    valueAt(endScreenContext, "end_screen_timing.placeholderStyleModel") ||
    valueAt(manifest, "end_screen_placeholder_style_successor.model") ||
    "";
  const isBorderlessUnderlay = borderlessUnderlayModel(placeholderStyleModel);

  check(
    result,
    Boolean(audit),
    "end_screen.adaptive_render_audit_artifact",
    `end-screen adaptive render audit artifact must exist and be readable: ${auditPathRaw || "not_declared"}`,
  );
  if (!audit) return;

  check(
    result,
    audit.model === END_SCREEN_ADAPTIVE_RENDER_AUDIT_MODEL &&
      manifest.end_screen_adaptive_render_audit_model === END_SCREEN_ADAPTIVE_RENDER_AUDIT_MODEL &&
      endScreenContext.end_screen_adaptive_render_audit_model === END_SCREEN_ADAPTIVE_RENDER_AUDIT_MODEL,
    "end_screen.adaptive_render_audit_model",
    "render audit must use end_screen_adaptive_render_audit_v1 at root, end_screen_context, and artifact",
  );
  check(
    result,
    audit.passed === true &&
      renderRead === PASS_ADAPTIVE_RENDER_AUDIT &&
      audit.reads?.end_screen_adaptive_render_audit_read === PASS_ADAPTIVE_RENDER_AUDIT,
    "end_screen.adaptive_render_audit_read",
    "browser render audit must pass before rough proof keep/final handoff",
  );
  check(
    result,
    computedRead === PASS_ADAPTIVE_COMPUTED_STYLE &&
      audit.reads?.end_screen_adaptive_computed_style_read === PASS_ADAPTIVE_COMPUTED_STYLE,
    "end_screen.adaptive_computed_style_read",
    "computed browser styles for all end-screen targets must match the palette contract",
  );
  check(
    result,
    pixelRead === PASS_ADAPTIVE_PIXEL_SAMPLE &&
      audit.reads?.end_screen_adaptive_pixel_sample_read === PASS_ADAPTIVE_PIXEL_SAMPLE,
    "end_screen.adaptive_pixel_sample_read",
    "end-screen screenshot pixel samples must match the composited episode-local palette contract",
  );
  check(
    result,
    !auditShaRead || auditShaRead === auditSha,
    "end_screen.adaptive_render_audit_sha256",
    "manifest must record the current adaptive render audit artifact hash",
  );

  const activeSourcePath = manifest.source_visual?.source_art_path || "";
  const activeSourceSha = manifest.source_visual?.source_art_sha256 || "";
  check(
    result,
    samePath(audit.source_art_path, activeSourcePath) &&
      samePath(audit.contract_source_art_path, activeSourcePath) &&
      audit.source_art_sha256 === activeSourceSha &&
      audit.contract_source_art_sha256 === activeSourceSha,
    "end_screen.adaptive_render_audit_source_backplate",
    "render audit palette contract source backplate must match the active source art path and sha256",
  );
  check(
    result,
    audit.palette_contract_id === "living_cover_end_screen_palette_contract_v1" &&
      audit.palette_source === "sampled_episode_backplate",
    "end_screen.adaptive_render_audit_palette_source",
    "render audit must use the sampled episode backplate palette contract, not a shared/default palette",
  );

  const targets = audit.target_computed_styles || {};
  for (const key of ["left_video", "right_video", "center_subscribe"]) {
    const target = targets[key] || {};
    const expected = target.expected_normalized || {};
    const actual = target.computed_normalized || {};
    const borderWidth = Number(target.computed?.borderWidth) || 0;
    const boxShadow = String(target.computed?.boxShadow || "none").trim();
    const after = target.computed?.after || {};
    const afterDisplay = String(after.display || "");
    const afterBorderWidth = Number(after.borderWidth) || 0;
    const afterBoxShadow = String(after.boxShadow || "none").trim();
    const targetPass = isBorderlessUnderlay
      ? target.present === true &&
        hasNonEmptyString(actual.fill) &&
        actual.fill === expected.fill &&
        borderWidth === 0 &&
        (!boxShadow || boxShadow === "none") &&
        (key !== "center_subscribe" ||
          ((afterDisplay === "none" || afterBorderWidth === 0) && (!afterBoxShadow || afterBoxShadow === "none")))
      : target.present === true &&
        hasNonEmptyString(actual.fill) &&
        actual.fill === expected.fill &&
        actual.border === expected.border &&
        actual.ring === expected.ring;
    check(
      result,
      targetPass,
      `end_screen.adaptive_render_audit.${key}.computed_styles`,
      isBorderlessUnderlay
        ? "rendered borderless end-screen targets must keep fill while removing CSS borders, glow rings, and subscribe inner ring"
        : "rendered end-screen target CSS variables must normalize exactly to the episode palette contract",
    );
  }

  const pixelSamples = Array.isArray(audit.pixel_samples) ? audit.pixel_samples : [];
  check(
    result,
    isBorderlessUnderlay
      ? pixelSamples.length >= 3 &&
          pixelSamples.every((sample) => sample.pass === true && sample.sample_role === "fill_center")
      : pixelSamples.length >= 9 && pixelSamples.every((sample) => sample.pass === true),
    "end_screen.adaptive_render_audit.pixel_samples",
    isBorderlessUnderlay
      ? "render-mode screenshot must include passing fill samples for each borderless target and no border/ring samples"
      : "render-mode screenshot must include passing fill, border, and ring samples for every target",
  );
  for (const screenshotPath of [audit.base_screenshot_path, audit.screenshot_path]) {
    check(
      result,
      hasNonEmptyString(screenshotPath) && fs.existsSync(resolveCandidate(screenshotPath, baseDir)),
      `end_screen.adaptive_render_audit.screenshot.${path.basename(String(screenshotPath || "missing"))}`,
      "adaptive render audit screenshot paths must exist",
    );
  }
  const serializedTargetStyles = JSON.stringify(audit.target_computed_styles || {}).toLowerCase();
  const copiedChallenger =
    manifest.episode_id !== "challenger" &&
    (/challenger/.test(serializedTargetStyles) || /shuttle/.test(serializedTargetStyles)) &&
    !/ep1_challenger/.test(String(activeSourcePath).toLowerCase());
  check(
    result,
    !copiedChallenger,
    "end_screen.adaptive_render_audit.no_challenger_fallback",
    "non-Challenger proofs must not render Challenger/default fallback end-screen colors or assets",
  );
}

function reviewUrlForPath(filePath, params = {}) {
  const rel = path.relative(EPISODES_ROOT, filePath).split(path.sep).map(encodeURIComponent).join("/");
  const url = new URL(`${REVIEW_SERVER_BASE_URL}/${rel}`);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, String(value));
  });
  return url.toString();
}

function collectPhraseSpans(manifest) {
  const spans = manifest?.living_cover_cue_map?.key_phrase_spans;
  if (Array.isArray(spans)) return spans;
  const railSpans = manifest?.rolling_caption_window?.key_phrase_spans;
  if (Array.isArray(railSpans)) return railSpans;
  return [];
}

function validateManifest(manifest, result, manifestPath) {
  for (const [key, expected] of Object.entries(REQUIRED_ROOT)) {
    let pass =
      key === "caption_end_screen_handoff_model" && isYoutubeLegalWindowEndScreenEntry(manifest)
        ? manifest[key] === YOUTUBE_LEGAL_WINDOW_END_SCREEN_ENTRY_MODEL
        : manifest[key] === expected;
    if (key === "caption_stack_render_model") pass = CAPTION_STACK_RENDER_MODEL_ALLOWED.has(manifest[key]);
    if (key === "caption_scroll_smoothness_model") pass = CAPTION_SCROLL_SMOOTHNESS_MODEL_ALLOWED.has(manifest[key]);
    check(result, pass, key, `expected ${expected}, found ${JSON.stringify(manifest[key])}`);
  }
  const introTrimModel =
    manifest.intro_trim_model ||
    valueAt(manifest, "caption_context.intro_trim_model") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.intro_trim_model") ||
    valueAt(manifest, "full_timeline.intro_trim_model");
  const introTrimSeconds = Number(
    manifest.intro_trim_seconds ??
      valueAt(manifest, "caption_context.intro_trim_seconds") ??
      valueAt(manifest, "rail_behavior.rolling_caption_window.intro_trim_seconds") ??
      valueAt(manifest, "full_timeline.intro_trim_seconds"),
  );
  const previousVoiceStartOffset = Number(
    manifest.previous_voice_start_offset_seconds ??
      valueAt(manifest, "caption_context.previous_voice_start_offset_seconds") ??
      valueAt(manifest, "full_timeline.previous_voice_start_offset_seconds"),
  );
  const voiceStartOffset = Number(
    manifest.voice_start_offset_seconds ??
      valueAt(manifest, "caption_context.voice_start_offset_seconds") ??
      valueAt(manifest, "full_timeline.voice_start_offset_seconds"),
  );
  check(result, introTrimModel === INTRO_TRIM_MODEL, "intro_trim_model", "first-eight proofs must record the shared 6s intro trim model");
  check(
    result,
    Math.abs(introTrimSeconds - INTRO_TRIM_SECONDS) <= 0.001,
    "intro_trim_seconds",
    `intro trim must be exactly ${INTRO_TRIM_SECONDS.toFixed(3)}s`,
  );
  check(
    result,
    Math.abs(previousVoiceStartOffset - PREVIOUS_VOICE_START_OFFSET_SECONDS) <= 0.0005,
    "previous_voice_start_offset_seconds",
    "manifest must preserve the prior 9.601451s offset for provenance only",
  );
  check(
    result,
    Math.abs(voiceStartOffset - VOICE_START_OFFSET_SECONDS) <= 0.0005,
    "voice_start_offset_seconds",
    "visible/review VO offset must be trimmed to 3.601451s",
  );

  const proofBuildId = String(manifest.proof_build_id || "");
  const proofGeneratedAt = String(manifest.proof_generated_at_utc || "");
  const proofBuildPathRaw = manifest.proof_build_json_path || valueAt(manifest, "proof_artifacts.proof_build_json_path") || "";
  const proofBuildPath = proofBuildPathRaw
    ? path.isAbsolute(proofBuildPathRaw)
      ? proofBuildPathRaw
      : path.resolve(path.dirname(manifestPath), proofBuildPathRaw)
    : "";
  const proofBuild = readJsonIfExists(proofBuildPath);
  check(
    result,
    /^[-a-z0-9]+_(rolling_caption_rail|caption-highlight-runtime-audit)_\d{8}T\d{6,9}Z$/i.test(proofBuildId),
    "proof_build_id",
    "rolling rail proof must record a cache-busting proof_build_id",
  );
  check(
    result,
    /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(proofGeneratedAt),
    "proof_generated_at_utc",
    "rolling rail proof must record proof_generated_at_utc",
  );
  check(result, Boolean(proofBuild), "proof_build_json", `proof build JSON must exist and be readable: ${proofBuildPath || "not_declared"}`);
  check(
    result,
    proofBuild?.proof_build_id === proofBuildId && proofBuild?.proof_generated_at_utc === proofGeneratedAt,
    "proof_build_json_matches_manifest",
    "proof_build.json must match manifest proof build id and generated timestamp",
  );
  check(
    result,
    proofBuild?.intro_trim_model === INTRO_TRIM_MODEL &&
      Math.abs(Number(proofBuild?.voice_start_offset_seconds) - VOICE_START_OFFSET_SECONDS) <= 0.0005,
    "proof_build_intro_trim",
    "proof_build.json must expose the active 3.601451s trim contract for stale-tab QA",
  );
  check(
    result,
    (manifest.proof_build_freshness_guard_read ||
      valueAt(manifest, "caption_context.proof_build_freshness_guard_read") ||
      valueAt(manifest, "rail_behavior.rolling_caption_window.proof_build_freshness_guard_read") ||
      "pending_browser_runtime_qa") === "pass_proof_build_freshness_guard_available",
    "proof_build_freshness_guard_read",
    "browser-runtime QA must prove stale review tabs surface a proof regeneration warning",
  );

  for (const failure of endScreenPaletteContractFailures(manifest, { manifestPath })) {
    check(result, false, failure.id, failure.detail);
  }

  const endScreenContext = manifest.end_screen_context || {};
  const endScreenPalette = endScreenContext.end_screen_palette || {};
  const endScreenRuntimeQaRead =
    manifest.end_screen_runtime_qa_read ||
    valueAt(manifest, "end_screen_context.end_screen_runtime_qa_read") ||
    valueAt(manifest, "caption_context.end_screen_runtime_qa_read") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.end_screen_runtime_qa_read") ||
    "pending_browser_runtime_qa";
  check(
    result,
    endScreenContext.youtube_end_screen_template_id === YOUTUBE_END_SCREEN_TEMPLATE_ID,
    "end_screen.template_id",
    "YouTube end-screen overlay must use the adaptive titleless Living Cover template, not a Challenger-copied template id",
  );
  check(
    result,
    (endScreenContext.end_screen_fade_timing_model === END_SCREEN_FADE_TIMING_MODEL &&
      valueAt(endScreenContext, "end_screen_timing.fadeTimingModel") === END_SCREEN_FADE_TIMING_MODEL) ||
      (isYoutubeLegalWindowEndScreenEntry(manifest, endScreenContext) &&
        endScreenContext.end_screen_fade_timing_model === YOUTUBE_LEGAL_WINDOW_END_SCREEN_ENTRY_MODEL &&
        valueAt(endScreenContext, "end_screen_timing.fadeTimingModel") === YOUTUBE_LEGAL_WINDOW_END_SCREEN_ENTRY_MODEL),
    "end_screen.fade_timing_model",
    "end-screen fade timing must use the shared caption handoff model or the Challenger legal-window trial model",
  );
  check(
    result,
    (endScreenContext.caption_end_screen_handoff_model === CAPTION_END_SCREEN_HANDOFF_MODEL &&
      valueAt(endScreenContext, "end_screen_timing.captionEndScreenHandoffModel") === CAPTION_END_SCREEN_HANDOFF_MODEL) ||
      (isYoutubeLegalWindowEndScreenEntry(manifest, endScreenContext) &&
        endScreenContext.caption_end_screen_handoff_model === YOUTUBE_LEGAL_WINDOW_END_SCREEN_ENTRY_MODEL &&
        valueAt(endScreenContext, "end_screen_timing.captionEndScreenHandoffModel") === YOUTUBE_LEGAL_WINDOW_END_SCREEN_ENTRY_MODEL),
    "end_screen.caption_end_screen_handoff_model",
    "end-screen handoff must use the shared review-approved model or the Challenger legal-window trial model",
  );
  check(
    result,
    endScreenContext.end_screen_palette_treatment_model === END_SCREEN_PALETTE_TREATMENT_MODEL &&
      endScreenPalette.palette_treatment_model === END_SCREEN_PALETTE_TREATMENT_MODEL,
    "end_screen.palette_treatment_model",
    "end-screen targets must use perceptually adaptive local backplate colors without Challenger hue shift",
  );
  check(
    result,
    endScreenContext.end_screen_adaptive_variability_model === END_SCREEN_ADAPTIVE_VARIABILITY_MODEL &&
      endScreenPalette.adaptive_variability_model === END_SCREEN_ADAPTIVE_VARIABILITY_MODEL &&
      endScreenContext.end_screen_adaptive_perceptual_variability_read ===
        "pass_backplate_hue_visible_across_end_screen_targets" &&
      endScreenPalette.end_screen_adaptive_perceptual_variability_read ===
        "pass_backplate_hue_visible_across_end_screen_targets",
    "end_screen.adaptive_perceptual_variability",
    "end-screen palette must preserve enough backplate hue to read as episode-local, not just numerically different",
  );
  check(
    result,
    endScreenContext.end_screen_palette_model === END_SCREEN_PALETTE_MODEL &&
      endScreenPalette.model_id === END_SCREEN_PALETTE_MODEL,
    "end_screen.palette_model",
    "YouTube end-screen target colors must use the source-backplate sampled palette model",
  );
  check(
    result,
    endScreenContext.end_screen_palette_source === "sampled_episode_backplate" &&
      endScreenPalette.palette_source === "sampled_episode_backplate",
    "end_screen.palette_source",
    "YouTube end-screen target colors must be sampled from the episode backplate",
  );
  const lastCaptionExitStart = Number(
    manifest.last_caption_visible_exit_start_seconds ??
      endScreenContext.last_caption_visible_exit_start_seconds ??
      valueAt(endScreenContext, "end_screen_timing.lastCaptionVisibleExitStartSeconds"),
  );
  const lastCaptionSuppressed = Number(
    manifest.last_caption_fully_suppressed_seconds ??
      endScreenContext.last_caption_fully_suppressed_seconds ??
      valueAt(endScreenContext, "end_screen_timing.lastCaptionFullySuppressedSeconds"),
  );
  const youtubeFadeStart = Number(
    manifest.youtube_placeholder_fade_start_seconds ??
      endScreenContext.youtube_placeholder_fade_start_seconds ??
      valueAt(endScreenContext, "end_screen_timing.youtubePlaceholderFadeStartSeconds"),
  );
  const youtubeFull = Number(
    manifest.youtube_placeholder_full_opacity_seconds ??
      endScreenContext.youtube_placeholder_full_opacity_seconds ??
      valueAt(endScreenContext, "end_screen_timing.youtubePlaceholderFullOpacitySeconds"),
  );
  const captionEndScreenGap = Number(
    manifest.caption_end_screen_gap_seconds ??
      endScreenContext.caption_end_screen_gap_seconds ??
      valueAt(endScreenContext, "end_screen_timing.captionEndScreenGapSeconds"),
  );
  const captionEndScreenOverlapRead =
    manifest.caption_end_screen_overlap_read ||
    endScreenContext.caption_end_screen_overlap_read ||
    valueAt(endScreenContext, "end_screen_timing.captionEndScreenOverlapRead");
  const legalWindowEntry = isYoutubeLegalWindowEndScreenEntry(manifest, endScreenContext);
  const reviewApprovedFadeStart = expectedYoutubeFadeStartSeconds(manifest, endScreenContext);
  const youtubeTransitionDuration = Number(
    valueAt(endScreenContext, "end_screen_timing.youtubePlaceholderTransitionDurationSeconds") ??
      valueAt(endScreenContext, "end_screen_timing.transitionDurationSeconds"),
  );
  const safeWindowCaptionSuppressionRead =
    endScreenContext.youtube_safe_window_caption_suppression_read ||
    valueAt(endScreenContext, "end_screen_timing.youtubeSafeWindowCaptionSuppressionRead");
  const entryTimingPass =
    Number.isFinite(lastCaptionExitStart) &&
    Number.isFinite(lastCaptionSuppressed) &&
    Number.isFinite(youtubeFadeStart) &&
    Number.isFinite(youtubeFull) &&
    Number.isFinite(reviewApprovedFadeStart) &&
    Math.abs(youtubeFadeStart - reviewApprovedFadeStart) <= 0.05 &&
    Math.abs(youtubeFull - (reviewApprovedFadeStart + END_SCREEN_TRANSITION_DURATION_SECONDS)) <= 0.05 &&
    (legalWindowEntry
      ? lastCaptionSuppressed <= youtubeFadeStart + 0.05
      : youtubeFadeStart >= lastCaptionExitStart - 0.1 &&
        youtubeFadeStart <= lastCaptionSuppressed &&
        Math.abs(youtubeFull - lastCaptionSuppressed) <= 0.05);
  check(
    result,
    entryTimingPass,
    "end_screen.review_approved_entry_timing",
    "YouTube placeholder fade must start at the approved target and reach full opacity 300ms later",
  );
  check(
    result,
    legalWindowEntry
      ? Number.isFinite(captionEndScreenGap) &&
          captionEndScreenGap >= 0 &&
          captionEndScreenOverlapRead === "pass_youtube_legal_window_entry_after_caption_suppression"
      : Number.isFinite(captionEndScreenGap) &&
          captionEndScreenGap <= 0.05 &&
          captionEndScreenOverlapRead === "pass_review_approved_end_screen_entry_no_blank_gap",
    "end_screen.caption_end_screen_gap",
    "end-screen handoff must either cross-suppress captions or record the legal-window outro gap for the Challenger trial",
  );
  check(
    result,
    Number.isFinite(youtubeTransitionDuration) &&
      Math.abs(youtubeTransitionDuration - END_SCREEN_TRANSITION_DURATION_SECONDS) <= 0.01,
    "end_screen.youtube_transition_duration",
    "YouTube placeholder fade must use the shared 300ms transition",
  );
  check(
    result,
    safeWindowCaptionSuppressionRead === "pass_caption_suppressed_before_safe_window",
    "end_screen.safe_window_caption_suppression",
    "all rolling caption text must be suppressed before the YouTube safe-window target geometry",
  );
  check(
    result,
    endScreenPalette.sample_read === "pass_source_backplate_sampled" &&
      /^pass_source_backplate_sampled_target_palette/.test(String(endScreenContext.end_screen_adaptive_palette_read || "")),
    "end_screen.adaptive_palette_read",
    "end-screen palette sampling must pass before rough proof keep/final handoff",
  );
  check(
    result,
    endScreenRuntimeQaRead === PASS_END_SCREEN_RUNTIME_QA,
    "end_screen.runtime_qa_read",
    "browser-runtime QA must prove end-screen fade timing and adaptive backplate palette before rough proof keep/final handoff",
  );
  validateEndScreenAdaptiveRenderAudit(manifest, result, manifestPath);
  for (const key of ["left_video", "right_video", "center_subscribe"]) {
    const target = endScreenPalette.targets?.[key] || {};
    check(
      result,
      hasNonEmptyString(target.sample_hex) &&
        /^#[0-9a-f]{6}$/i.test(target.sample_hex) &&
        /rgba\(/i.test(String(target.fill_rgba || "")) &&
        /rgba\(/i.test(String(target.border_rgba || "")) &&
        Array.isArray(target.sample_bbox_xy),
      `end_screen.palette.${key}`,
      "each YouTube target must record sampled color, fill, border, and source bbox",
    );
  }

  check(
    result,
    valueAt(manifest, "caption_context.caption_slot_preset_id") === "rolling_rail_caption_window_v1",
    "caption_context.caption_slot_preset_id",
    "caption context must use rolling_rail_caption_window_v1",
  );
  check(
    result,
    valueAt(manifest, "caption_context.behavior_model") === "deterministic_audio_time_rolling_caption_window",
    "caption_context.behavior_model",
    "caption behavior must be deterministic audio-time rolling",
  );
  check(
    result,
    valueAt(manifest, "caption_context.caption_text_source.kind") === "locked_narration_script" ||
      valueAt(manifest, "caption_text_source.kind") === "locked_narration_script",
    "caption_text_source.kind",
    "visible caption text must come from the locked narration script",
  );
  const timingUsage =
    valueAt(manifest, "caption_context.caption_timing_source.text_usage") ||
    valueAt(manifest, "caption_timing_source.text_usage") ||
    "";
  check(
    result,
    /timing_only/i.test(timingUsage) && /not_used/i.test(timingUsage),
    "caption_timing_source.text_usage",
    "ASR/WhisperX/VTT/SRT text must be timing-only and not used for output words",
  );
  check(
    result,
    Number(valueAt(manifest, "caption_context.min_alignment_coverage") || 0) >= 0.985,
    "caption_context.min_alignment_coverage",
    "alignment coverage threshold must be at least 98.5%",
  );

  const qaHooks = valueAt(manifest, "caption_context.qa_hooks") || valueAt(manifest, "rail_behavior.render_api") || [];
  const qaHookText = Array.isArray(qaHooks) ? qaHooks.join(" ") : String(qaHooks);
  check(result, qaHookText.includes("window.__railCaptionStateAt"), "qa_hook.__railCaptionStateAt", "missing rolling caption state hook");
  check(result, qaHookText.includes("window.__setRenderTime"), "qa_hook.__setRenderTime", "missing render-time control hook");
  if (AMBIENT_FRAME_CLOCK_EPISODES.has(manifest.episode_id)) {
    check(
      result,
      qaHookText.includes("window.__ceSetAmbientRenderTime"),
      "qa_hook.__ceSetAmbientRenderTime",
      "affected ambient proofs must expose render-frame ambient clock hook",
    );
  }

  const stableProps = valueAt(manifest, "caption_context.stable_properties_only") || [];
  const stableText = Array.isArray(stableProps) ? stableProps.join(" ") : String(stableProps);
  check(result, stableText.includes("transform") && stableText.includes("opacity"), "caption_stable_properties", "stable motion must be transform/opacity based");

  check(
    result,
    (manifest.caption_motion_model || valueAt(manifest, "caption_context.caption_motion_model")) === CAPTION_MOTION_MODEL,
    "caption_motion_model",
    "caption motion must use the constant-speed audio-time-aligned scroll model",
  );
  const timelineLayoutModel =
    manifest.caption_timeline_layout_model ||
    valueAt(manifest, "caption_context.caption_timeline_layout_model") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.caption_timeline_layout_model") ||
    valueAt(manifest, "full_timeline.caption_timeline_layout_model");
  check(
    result,
    timelineLayoutModel === CAPTION_TIMELINE_LAYOUT_MODEL,
    "caption_timeline_layout_model",
    "caption chunks must be positioned from audio time, not sequential stack order",
  );
  const syncTarget =
    manifest.caption_sync_target ||
    valueAt(manifest, "caption_context.caption_sync_target") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.caption_sync_target") ||
    valueAt(manifest, "full_timeline.caption_sync_target");
  check(result, syncTarget === CAPTION_SYNC_TARGET, "caption_sync_target", "caption sync target must be pre-VO reading lead");
  const readingLead = Number(
    manifest.caption_reading_lead_seconds ??
      valueAt(manifest, "caption_context.caption_reading_lead_seconds") ??
      valueAt(manifest, "rail_behavior.rolling_caption_window.caption_reading_lead_seconds") ??
      valueAt(manifest, "full_timeline.caption_reading_lead_seconds"),
  );
  check(
    result,
    Math.abs(readingLead - CAPTION_READING_LEAD_SECONDS) < 0.001,
    "caption_reading_lead_seconds",
    `caption reading lead must be ${CAPTION_READING_LEAD_SECONDS}s; found ${readingLead}`,
  );
  const introGateModel =
    manifest.caption_intro_visibility_gate_model ||
    valueAt(manifest, "caption_context.caption_intro_visibility_gate_model") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.caption_intro_visibility_gate_model") ||
    valueAt(manifest, "full_timeline.caption_intro_visibility_gate_model");
  const introGateStart = Number(
    manifest.caption_intro_gate_start_seconds ??
      valueAt(manifest, "caption_context.caption_intro_gate_start_seconds") ??
      valueAt(manifest, "rail_behavior.rolling_caption_window.caption_intro_gate_start_seconds") ??
      valueAt(manifest, "full_timeline.caption_intro_gate_start_seconds"),
  );
  const introGateFull = Number(
    manifest.caption_intro_gate_full_opacity_seconds ??
      valueAt(manifest, "caption_context.caption_intro_gate_full_opacity_seconds") ??
      valueAt(manifest, "rail_behavior.rolling_caption_window.caption_intro_gate_full_opacity_seconds") ??
      valueAt(manifest, "full_timeline.caption_intro_gate_full_opacity_seconds"),
  );
  const firstDisplayCueStart = Number(
    manifest.first_caption_display_cue_start_seconds ??
      valueAt(manifest, "caption_context.first_caption_display_cue_start_seconds") ??
      valueAt(manifest, "full_timeline.first_caption_display_cue_start_seconds"),
  );
  check(
    result,
    Number.isFinite(firstDisplayCueStart) &&
      firstDisplayCueStart >= VOICE_START_OFFSET_SECONDS - 0.1 &&
      firstDisplayCueStart <= VOICE_START_OFFSET_SECONDS + 0.25,
    "caption_first_display_cue_after_intro_trim",
    "first visible caption cue must land around 3.632s after the shared 6s intro trim",
  );
  check(
    result,
    introGateModel === CAPTION_INTRO_VISIBILITY_GATE_MODEL,
    "caption_intro_visibility_gate_model",
    "caption rail must gate pre-VO intro visibility without changing scroll timing",
  );
  check(
    result,
    Number.isFinite(introGateStart) &&
      Number.isFinite(introGateFull) &&
      Number.isFinite(firstDisplayCueStart) &&
      Math.abs(introGateStart - Math.max(0, firstDisplayCueStart - 1.1)) <= 0.002 &&
      Math.abs(introGateFull - Math.max(introGateStart, firstDisplayCueStart - CAPTION_READING_LEAD_SECONDS)) <= 0.002,
    "caption_intro_gate_timing",
    "caption intro gate must fade from first cue minus 1.10s to the existing 0.65s reading-lead point",
  );
  check(
    result,
    (manifest.caption_intro_premature_text_read ||
      valueAt(manifest, "caption_context.caption_intro_premature_text_read") ||
      valueAt(manifest, "full_timeline.caption_intro_premature_text_read")) === "pass",
    "caption_intro_premature_text_read",
    "caption intro premature text read must pass",
  );
  const speedScope =
    manifest.caption_constant_speed_scope ||
    valueAt(manifest, "caption_context.caption_constant_speed_scope") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.caption_constant_speed_scope") ||
    valueAt(manifest, "full_timeline.caption_constant_speed_scope");
  check(result, speedScope === CAPTION_CONSTANT_SPEED_SCOPE, "caption_constant_speed_scope", "speed scope must be one constant speed per episode");
  const playbackClockModel =
    manifest.caption_playback_clock_model ||
    valueAt(manifest, "caption_context.caption_playback_clock_model") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.caption_playback_clock_model") ||
    valueAt(manifest, "full_timeline.caption_playback_clock_model");
  const stackRenderModel =
    manifest.caption_stack_render_model ||
    valueAt(manifest, "caption_context.caption_stack_render_model") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.caption_stack_render_model") ||
    valueAt(manifest, "full_timeline.caption_stack_render_model");
  const smoothnessModel =
    manifest.caption_scroll_smoothness_model ||
    valueAt(manifest, "caption_context.caption_scroll_smoothness_model") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.caption_scroll_smoothness_model") ||
    valueAt(manifest, "full_timeline.caption_scroll_smoothness_model");
  check(
    result,
    playbackClockModel === CAPTION_PLAYBACK_CLOCK_MODEL,
    "caption_playback_clock_model",
    "caption playback clock must use smoothed RAF media-time interpolation to avoid coarse audio.currentTime jitter",
  );
  check(
    result,
    CAPTION_STACK_RENDER_MODEL_ALLOWED.has(stackRenderModel),
    "caption_stack_render_model",
    "caption stack transform must be driven by a compositor-owned linear playback driver or visible-window virtualizer",
  );
  check(
    result,
    CAPTION_SCROLL_SMOOTHNESS_MODEL_ALLOWED.has(smoothnessModel),
    "caption_scroll_smoothness_model",
    "caption scroll smoothness model must be recorded and shared across first-eight proofs",
  );
  const runtimeCoverageModel =
    manifest.caption_runtime_coverage_model ||
    valueAt(manifest, "caption_context.caption_runtime_coverage_model") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.caption_runtime_coverage_model") ||
    valueAt(manifest, "full_timeline.caption_runtime_coverage_model");
  check(
    result,
    runtimeCoverageModel === CAPTION_RUNTIME_COVERAGE_MODEL,
    "caption_runtime_coverage_model",
    "caption runtime coverage must be guarded by full VO browser coverage QA",
  );
  const runtimeCoverageRead =
    manifest.caption_full_vo_runtime_coverage_read ||
    valueAt(manifest, "caption_context.caption_full_vo_runtime_coverage_read") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.caption_full_vo_runtime_coverage_read") ||
    valueAt(manifest, "full_timeline.caption_full_vo_runtime_coverage_read");
  const runtimeCutoffRead =
    manifest.caption_runtime_cutoff_read ||
    valueAt(manifest, "caption_context.caption_runtime_cutoff_read") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.caption_runtime_cutoff_read");
  const scrubSyncRead =
    manifest.caption_scrub_transport_sync_read ||
    valueAt(manifest, "caption_context.caption_scrub_transport_sync_read") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.caption_scrub_transport_sync_read");
  const scrollSmoothnessRead =
    manifest.caption_scroll_smoothness_read ||
    valueAt(manifest, "caption_context.caption_scroll_smoothness_read") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.caption_scroll_smoothness_read") ||
    valueAt(manifest, "full_timeline.caption_scroll_smoothness_read");
  const transportScrubModel =
    manifest.review_transport_scrub_model ||
    valueAt(manifest, "caption_context.review_transport_scrub_model") ||
    valueAt(manifest, "rail_behavior.review_transport_scrub_model") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.review_transport_scrub_model");
  const playingScrubRead =
    manifest.review_transport_playing_scrub_read ||
    valueAt(manifest, "caption_context.review_transport_playing_scrub_read") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.review_transport_playing_scrub_read");
  const lineClipRead =
    manifest.caption_line_clip_read ||
    valueAt(manifest, "caption_context.caption_line_clip_read") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.caption_line_clip_read");
  const paintVisibilityRead =
    manifest.right_rail_caption_paint_visibility_read ||
    valueAt(manifest, "caption_context.right_rail_caption_paint_visibility_read") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.right_rail_caption_paint_visibility_read") ||
    valueAt(manifest, "full_timeline.right_rail_caption_paint_visibility_read");
  const inheritedEndScreenSuppressionRead =
    manifest.inherited_end_screen_suppression_read ||
    valueAt(manifest, "end_screen_context.inherited_end_screen_suppression_read") ||
    valueAt(manifest, "caption_context.inherited_end_screen_suppression_read") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.inherited_end_screen_suppression_read");
  const tacomaRainPerformanceGuardRead =
    manifest.tacoma_rain_performance_guard_read ||
    valueAt(manifest, "caption_context.tacoma_rain_performance_guard_read") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.tacoma_rain_performance_guard_read");
  check(
    result,
    runtimeCoverageRead === "pass_full_vo_runtime_visible_caption_coverage",
    "caption_full_vo_runtime_coverage_read",
    "full sidecar coverage is not enough; browser-runtime caption coverage must pass before this proof is trusted",
  );
  check(
    result,
    runtimeCutoffRead === "pass_no_caption_cutoff_before_final_vo",
    "caption_runtime_cutoff_read",
    "captions must not disappear before the final VO/end-screen transition",
  );
  check(
    result,
    scrubSyncRead === "pass_foreground_transport_matches_direct_render_time",
    "caption_scrub_transport_sync_read",
    "foreground scrubber state must match direct render-time state",
  );
  check(
    result,
    scrollSmoothnessRead === "pass_caption_scroll_frame_deltas_smooth" ||
      scrollSmoothnessRead === "pass_visible_window_caption_virtualization_v1",
    "caption_scroll_smoothness_read",
    "browser-runtime QA must prove scrolling caption frame deltas are smooth with no downward corrections",
  );
  check(
    result,
    transportScrubModel === REVIEW_TRANSPORT_SCRUB_MODEL,
    "review_transport_scrub_model",
    "foreground transport must use the scrub-lock model for scrubbing while playback is running",
  );
  check(
    result,
    playingScrubRead === PASS_PLAYING_SCRUB,
    "review_transport_playing_scrub_read",
    "browser-runtime QA must prove foreground scrubber works while playback is running",
  );
  check(
    result,
    lineClipRead === "pass_no_visible_caption_line_clipping",
    "caption_line_clip_read",
    "runtime QA must prove visible caption text is not clipped inside the rail",
  );
  check(
    result,
    paintVisibilityRead === RIGHT_RAIL_CAPTION_PAINT_VISIBILITY_READ,
    "right_rail_caption_paint_visibility_read",
    "runtime QA must prove visible right-rail caption lines are actually painted, not clipped by an internal stack paint box",
  );
  check(
    result,
    inheritedEndScreenSuppressionRead === PASS_INHERITED_END_SCREEN,
    "inherited_end_screen_suppression_read",
    "runtime QA must prove inherited predecessor end-screen layers stay hidden in review and render mode",
  );
  if (manifest.episode_id === "tacoma-narrows") {
    check(
      result,
      tacomaRainPerformanceGuardRead === PASS_TACOMA_RAIN_GUARD,
      "tacoma_rain_performance_guard_read",
      "Tacoma must use the caption-review rain performance guard so rain drawing cannot jitter the right-rail captions",
    );
    const sourceVisual = manifest.source_visual || {};
    const sourceArtSha = sourceVisual.source_art_sha256 || "";
    const highlightMergeModel = manifest.source_art_highlight_merge_model || sourceVisual.source_art_highlight_merge_model || "";
    const highlightMergeRead = manifest.source_art_highlight_merge_read || sourceVisual.source_art_highlight_merge_read || "";
    check(
      result,
      sourceArtSha === TACOMA_K3_B3_SOURCE_ART_SHA256,
      "tacoma_k3_b3_source_art_sha256",
      "Tacoma review proof must use the K3 B3 failure-in-progress backplate, not K4 or the old unhighlighted proof",
    );
    check(
      result,
      highlightMergeModel === TACOMA_K3_B3_HIGHLIGHT_MERGE_MODEL,
      "tacoma_k3_b3_highlight_merge_model",
      "Tacoma must record the K3 B3 backplate plus lesson-takeaway highlight merge model",
    );
    check(
      result,
      highlightMergeRead === TACOMA_K3_B3_HIGHLIGHT_MERGE_READ,
      "tacoma_k3_b3_highlight_merge_read",
      "Tacoma must prove the active proof combines the K3 B3 backplate with the approved takeaway highlight layer",
    );
  }
  const runtimeQaPathRaw =
    manifest.caption_runtime_coverage_qa_path ||
    valueAt(manifest, "proof_artifacts.runtime_coverage_qa_path") ||
    valueAt(manifest, "caption_context.caption_runtime_coverage_qa_path");
  const runtimeQaPath = runtimeQaPathRaw
    ? path.isAbsolute(runtimeQaPathRaw)
      ? runtimeQaPathRaw
      : path.resolve(path.dirname(manifestPath), runtimeQaPathRaw)
    : "";
  const runtimeQa = readJsonIfExists(runtimeQaPath);
  check(result, Boolean(runtimeQaPathRaw), "caption_runtime_coverage_qa_path", "runtime coverage QA artifact path is required");
  check(result, Boolean(runtimeQa), "caption_runtime_coverage_qa_artifact", `runtime coverage QA artifact is missing or unreadable: ${runtimeQaPath || "not_declared"}`);
  check(
    result,
    runtimeQa?.model === CAPTION_RUNTIME_COVERAGE_MODEL && runtimeQa?.passed === true && Number(runtimeQa?.failure_count || 0) === 0,
    "caption_runtime_coverage_qa_passed",
    "runtime coverage QA artifact must pass with zero failures",
  );
  const densityModel =
    manifest.caption_density_resolution_model ||
    valueAt(manifest, "caption_context.caption_density_resolution_model") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.caption_density_resolution_model") ||
    valueAt(manifest, "full_timeline.caption_density_resolution_model");
  check(
    result,
    densityModel === CAPTION_DENSITY_RESOLUTION_MODEL,
    "caption_density_resolution_model",
    "dense narration must be resolved by merging chunks, not speed ramps",
  );
  const lineWrapModel =
    manifest.caption_display_line_wrap_model ||
    valueAt(manifest, "caption_context.caption_display_line_wrap_model") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.caption_display_line_wrap_model") ||
    valueAt(manifest, "full_timeline.caption_display_line_wrap_model");
  check(
    result,
    lineWrapModel === CAPTION_DISPLAY_LINE_WRAP_MODEL,
    "caption_display_line_wrap_model",
    "caption display lines must be pre-wrapped against a pixel budget",
  );
  const stackHeight = Number(
    manifest.caption_stack_height_px ??
      valueAt(manifest, "caption_context.caption_stack_height_px") ??
      valueAt(manifest, "rail_behavior.rolling_caption_window.caption_stack_height_px") ??
      valueAt(manifest, "full_timeline.caption_stack_height_px"),
  );
  const stackPaintContainmentRead =
    manifest.caption_stack_paint_containment_read ||
    valueAt(manifest, "caption_context.caption_stack_paint_containment_read") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.caption_stack_paint_containment_read") ||
    valueAt(manifest, "full_timeline.caption_stack_paint_containment_read");
  check(
    result,
    Number.isFinite(stackHeight) && stackHeight >= 12000,
    "caption_stack_height_px",
    `caption stack must record a full-timeline paint height; found ${stackHeight}`,
  );
  check(
    result,
    stackPaintContainmentRead === CAPTION_STACK_PAINT_CONTAINMENT_READ,
    "caption_stack_paint_containment_read",
    "caption stack must not use paint containment that can clip late-runtime caption lines",
  );
  const textStackWidth = Number(
    manifest.caption_text_stack_width_px ??
      valueAt(manifest, "caption_context.caption_text_stack_width_px") ??
      valueAt(manifest, "rail_behavior.rolling_caption_window.caption_text_stack_width_px") ??
      valueAt(manifest, "full_timeline.caption_text_stack_width_px"),
  );
  const maxLineWidth = Number(
    manifest.caption_max_estimated_line_width_px ??
      valueAt(manifest, "caption_context.caption_max_estimated_line_width_px") ??
      valueAt(manifest, "rail_behavior.rolling_caption_window.caption_max_estimated_line_width_px") ??
      valueAt(manifest, "full_timeline.caption_max_estimated_line_width_px"),
  );
  check(
    result,
    Number.isFinite(textStackWidth) && textStackWidth === CAPTION_TEXT_STACK_WIDTH_PX,
    "caption_text_stack_width_px",
    `caption text stack width must remain ${CAPTION_TEXT_STACK_WIDTH_PX}px`,
  );
  check(
    result,
    Number.isFinite(maxLineWidth) && maxLineWidth <= CAPTION_DISPLAY_LINE_MAX_WIDTH_PX,
    "caption_max_estimated_line_width_px",
    `estimated display line width must stay <= ${CAPTION_DISPLAY_LINE_MAX_WIDTH_PX}px; found ${maxLineWidth}`,
  );
  const constantSpeed = Number(
    manifest.caption_constant_scroll_speed_px_per_second ??
      valueAt(manifest, "caption_context.caption_constant_scroll_speed_px_per_second") ??
      valueAt(manifest, "rail_behavior.rolling_caption_window.caption_constant_scroll_speed_px_per_second") ??
      valueAt(manifest, "full_timeline.caption_constant_scroll_speed_px_per_second"),
  );
  check(
    result,
    Number.isFinite(constantSpeed) &&
      constantSpeed >= CAPTION_MIN_CONSTANT_SPEED_PX_PER_SECOND &&
      constantSpeed <= CAPTION_MAX_CONSTANT_SPEED_PX_PER_SECOND,
    "caption_constant_scroll_speed_px_per_second",
    `manifest must record one per-episode constant speed in the 48-54 px/sec range; found ${constantSpeed}`,
  );
  const unresolvedDensePairCount = Number(
    valueAt(manifest, "caption_context.caption_unresolved_dense_pair_count") ??
      valueAt(manifest, "full_timeline.caption_unresolved_dense_pair_count") ??
      0,
  );
  check(
    result,
    unresolvedDensePairCount === 0,
    "caption_unresolved_dense_pair_count",
    `dense chunks must merge before layout; unresolved dense pairs found ${unresolvedDensePairCount}`,
  );
  const maxCueStartDelta = Number(
    valueAt(manifest, "caption_context.caption_max_active_chunk_center_delta_at_cue_start_px") ??
      valueAt(manifest, "full_timeline.caption_max_active_chunk_center_delta_at_cue_start_px") ??
      0,
  );
  check(
    result,
    maxCueStartDelta <= CAPTION_ACTIVE_BAND_LOWER_DELTA_PX,
    "caption_active_band_at_cue_start",
    `active chunk must not still sit below the readable active band at cue start; max delta ${maxCueStartDelta}px`,
  );
  const treatmentModel =
    manifest.caption_window_treatment_model ||
    valueAt(manifest, "caption_context.caption_window_treatment_model") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.caption_window_treatment_model") ||
    valueAt(manifest, "full_timeline.caption_window_treatment_model");
  check(
    result,
    treatmentModel === CAPTION_WINDOW_TREATMENT_MODEL,
    "caption_window_treatment_model",
    "caption window must use the transparent mask-only treatment",
  );
  check(
    result,
    (manifest.caption_line_opacity_model || valueAt(manifest, "caption_context.caption_line_opacity_model")) ===
      "viewport_distance_smoothstep_v1",
    "caption_line_opacity_model",
    "caption line opacity must be computed continuously from viewport distance",
  );
  check(
    result,
    (manifest.highlight_phrase_scope || valueAt(manifest, "caption_context.highlight_phrase_scope")) === "exact_authored_span_only",
    "highlight_phrase_scope",
    "highlight rendering must target exact authored word/phrase spans only",
  );
  const highlightModel =
    manifest.caption_highlight_model_id ||
    valueAt(manifest, "caption_context.caption_highlight_model_id") ||
    valueAt(manifest, "living_cover_cue_map.caption_highlight_model_id") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.caption_highlight_model_id");
  check(result, highlightModel === CAPTION_HIGHLIGHT_MODEL_ID, "caption_highlight_model_id", "highlight model must be lesson_takeaway_highlight_v1");
  const highlightRole =
    manifest.highlight_semantic_role ||
    valueAt(manifest, "caption_context.highlight_semantic_role") ||
    valueAt(manifest, "living_cover_cue_map.highlight_semantic_role") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.highlight_semantic_role");
  check(result, highlightRole === HIGHLIGHT_SEMANTIC_ROLE, "highlight_semantic_role", "highlights must be story lesson/takeaway spans");
  const highlightDensity =
    manifest.highlight_density_model ||
    valueAt(manifest, "caption_context.highlight_density_model") ||
    valueAt(manifest, "living_cover_cue_map.highlight_density_model") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.highlight_density_model");
  check(result, highlightDensity === HIGHLIGHT_DENSITY_MODEL, "highlight_density_model", "highlight density model must be memorable_takeaway_cadence_v1");
  const highlightColor =
    manifest.highlight_color_model ||
    valueAt(manifest, "caption_context.highlight_color_model") ||
    valueAt(manifest, "living_cover_cue_map.highlight_color_model") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.highlight_color_model");
  check(
    result,
    highlightColor === HIGHLIGHT_COLOR_MODEL,
    "highlight_color_model",
    "highlight color model must be source-sampled, distinct from caption text, and contrast-checked against the caption-window backplate",
  );
  if (manifest.episode_id === "semmelweis") {
    const semmelweisColorQa =
      manifest.highlight_color_qa ||
      valueAt(manifest, "caption_context.highlight_color_qa") ||
      valueAt(manifest, "rail_behavior.rolling_caption_window.highlight_color_qa") ||
      {};
    check(
      result,
      String(semmelweisColorQa.selected_hex || "").toLowerCase() === "#efef9f" &&
        semmelweisColorQa.highlight_override_read === HUMAN_APPROVED_HIGHLIGHT_ACCENT_OVERRIDES.semmelweis.highlight_override_read,
      "semmelweis.highlight_override_selected_hex",
      "Semmelweis must record the review-safe #efef9f selected highlight override",
    );
  }
  const highlightVisualTiming =
    manifest.highlight_visual_timing_model ||
    valueAt(manifest, "caption_context.highlight_visual_timing_model") ||
    valueAt(manifest, "living_cover_cue_map.highlight_visual_timing_model") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.highlight_visual_timing_model");
  check(
    result,
    highlightVisualTiming === HIGHLIGHT_VISUAL_TIMING_MODEL,
    "highlight_visual_timing_model",
    "highlight alpha must be aligned to active-band presence, not only VO phrase time",
  );
  const collisionGuard =
    manifest.caption_layout_collision_guard ||
    valueAt(manifest, "caption_context.caption_layout_collision_guard") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.caption_layout_collision_guard") ||
    valueAt(manifest, "full_timeline.caption_layout_collision_guard");
  check(
    result,
    collisionGuard === CAPTION_LAYOUT_COLLISION_GUARD,
    "caption_layout_collision_guard",
    "caption layout must use the fixed line-box visual gap guard",
  );
  const minRenderedGap = Number(
    manifest.caption_min_rendered_line_gap_px ??
      valueAt(manifest, "caption_context.caption_min_rendered_line_gap_px") ??
      valueAt(manifest, "full_timeline.caption_min_rendered_line_gap_px"),
  );
  check(
    result,
    Number.isFinite(minRenderedGap) && minRenderedGap >= CAPTION_MIN_RENDERED_LINE_GAP_PX,
    "caption_min_rendered_line_gap_px",
    `rendered caption line gap must be at least ${CAPTION_MIN_RENDERED_LINE_GAP_PX}px; found ${minRenderedGap}`,
  );
  const collisionRead =
    manifest.caption_collision_guard_read ||
    valueAt(manifest, "caption_context.caption_collision_guard_read") ||
    valueAt(manifest, "full_timeline.caption_collision_guard_read") ||
    valueAt(manifest, "rough_assembly_reads.caption_collision_guard_read");
  check(result, /pass/i.test(String(collisionRead || "")), "caption_collision_guard_read", "caption collision guard read must pass");

  const geometry = valueAt(manifest, "caption_context.caption_window_geometry_px") || {};
  check(
    result,
    geometry.left === 1368 &&
      geometry.top === 124 &&
      geometry.width === 488 &&
      geometry.height === 844 &&
      geometry.bottom === 968,
    "caption_window_geometry_px",
    "caption window must remain narrow/right-biased and expand vertically to 488x844 at x=1368 y=124",
  );

  const blurScope =
    valueAt(manifest, "caption_context.caption_window_background.scope") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.localized_blur_scope") ||
    manifest.caption_blur_scope;
  check(result, blurScope === "none", "caption_window_blur_scope", "caption window blur scope must be none");
  const background = valueAt(manifest, "caption_context.caption_window_background") || {};
  check(
    result,
    Number(background.localized_blur_px || 0) === 0 && Number(background.fill_alpha || 0) === 0,
    "caption_window_background_transparent",
    "caption window background must have zero blur and zero fill alpha",
  );

  const ambientPolicy =
    manifest.ambient_right_rail_motion_policy ||
    valueAt(manifest, "source_visual.ambient_right_rail_motion_policy") ||
    valueAt(manifest, "ambient_effects_layer.ambient_right_rail_motion_policy");
  const foregroundMattePolicy =
    manifest.foreground_matte_policy ||
    valueAt(manifest, "source_visual.foreground_matte_policy") ||
    valueAt(manifest, "ambient_effects_layer.foreground_matte_policy");
  const hasAircraftRightRailLayer =
    manifest.episode_id === "challenger" ||
    ambientPolicy === AMBIENT_RIGHT_RAIL_MOTION_POLICY ||
    Number(valueAt(manifest, "ambient_effects_layer.aircraft_right_rail_route_count") || 0) > 0;
  if (hasAircraftRightRailLayer) {
    check(
      result,
      ambientPolicy === AMBIENT_RIGHT_RAIL_MOTION_POLICY,
      "ambient_right_rail_motion_policy",
      `Challenger aircraft/fog motion must be allowed under right-rail text; found ${JSON.stringify(ambientPolicy)}`,
    );
    check(
      result,
      foregroundMattePolicy === FOREGROUND_MATTE_POLICY,
      "foreground_matte_policy",
      `foreground matte must block tower/shuttle only, not the right rail; found ${JSON.stringify(foregroundMattePolicy)}`,
    );
    const matteRead =
      valueAt(manifest, "rough_assembly_reads.right_rail_matte_removed_read") ||
      valueAt(manifest, "ambient_effects_layer.right_rail_matte_removed_read") ||
      valueAt(manifest, "source_visual.right_rail_matte_removed_read");
    check(result, /pass/i.test(String(matteRead || "")), "right_rail_matte_removed_read", "right-rail matte read must pass");
    const visibilityRead =
      valueAt(manifest, "rough_assembly_reads.aircraft_right_rail_visibility_read") ||
      valueAt(manifest, "ambient_effects_layer.aircraft_right_rail_visibility_read") ||
      valueAt(manifest, "source_visual.aircraft_right_rail_visibility_read");
    check(
      result,
      /pass/i.test(String(visibilityRead || "")),
      "aircraft_right_rail_visibility_read",
      "aircraft right-rail visibility read must pass",
    );
    const routeCount = Number(
      valueAt(manifest, "ambient_effects_layer.aircraft_right_rail_route_count") ||
        valueAt(manifest, "source_visual.aircraft_right_rail_route_count") ||
        0,
    );
    check(
      result,
      routeCount >= 1,
      "aircraft_right_rail_route_count",
      `at least one pre-end-screen aircraft route must enter x >= ${RIGHT_RAIL_LEFT_X}; found ${routeCount}`,
    );
    const cutoffRemoved =
      valueAt(manifest, "ambient_effects_layer.aircraft_right_rail_cutoff_removed") ??
      valueAt(manifest, "source_visual.aircraft_right_rail_cutoff_removed");
    check(result, cutoffRemoved === true, "aircraft_right_rail_cutoff_removed", "aircraft rail cutoff must be removed");
  }

  if (AMBIENT_FRAME_CLOCK_EPISODES.has(manifest.episode_id)) {
    const ambientFrameClockModel =
      manifest.ambient_frame_clock_model ||
      valueAt(manifest, "ambient_effects_layer.ambient_frame_clock_model") ||
      valueAt(manifest, "source_visual.ambient_frame_clock_model") ||
      valueAt(manifest, "full_timeline.ambient_frame_clock_model");
    const ambientRenderClockRead =
      manifest.ambient_render_clock_read ||
      valueAt(manifest, "ambient_effects_layer.ambient_render_clock_read") ||
      valueAt(manifest, "source_visual.ambient_render_clock_read") ||
      valueAt(manifest, "full_timeline.ambient_render_clock_read") ||
      valueAt(manifest, "rough_assembly_reads.ambient_render_clock_read");
    const ambientDriftSuppressionRead =
      manifest.ambient_wall_clock_drift_suppression_read ||
      valueAt(manifest, "ambient_effects_layer.ambient_wall_clock_drift_suppression_read") ||
      valueAt(manifest, "source_visual.ambient_wall_clock_drift_suppression_read") ||
      valueAt(manifest, "full_timeline.ambient_wall_clock_drift_suppression_read") ||
      valueAt(manifest, "rough_assembly_reads.ambient_wall_clock_drift_suppression_read");
    check(
      result,
      ambientFrameClockModel === AMBIENT_FRAME_CLOCK_MODEL,
      "ambient_frame_clock_model",
      "Therac-25 and Semmelweis ambient effects must be locked to composition render-frame time",
    );
    check(
      result,
      ambientRenderClockRead === AMBIENT_RENDER_CLOCK_READ,
      "ambient_render_clock_read",
      "ambient render clock read must pass",
    );
    check(
      result,
      ambientDriftSuppressionRead === AMBIENT_WALL_CLOCK_DRIFT_SUPPRESSION_READ,
      "ambient_wall_clock_drift_suppression_read",
      "render-mode ambient effects must not mutate on wall-clock RAF time",
    );
  }

  check(
    result,
    valueAt(manifest, "rail_behavior.previous_upcoming_context_rows_allowed") === false ||
      valueAt(manifest, "rough_assembly_reads.old_context_rows_absence_read") === "pass",
    "old_context_rows_absence",
    "old previous/upcoming context rows must be removed",
  );

  const highlightPolicy =
    manifest.highlight_render_policy ||
    valueAt(manifest, "living_cover_cue_map.highlight_render_policy") ||
    valueAt(manifest, "rail_behavior.rolling_caption_window.highlight_render_policy") ||
    "";
  check(
    result,
    highlightPolicy === "reviewed_cue_map_spans_only",
    "highlight_render_policy",
    "highlights must render only from authored reviewed cue-map spans",
  );

  const spans = collectPhraseSpans(manifest);
  const cueCount = Number(valueAt(manifest, "full_timeline.caption_cue_count_in_proof") || 0);
  const chunkCount = Number(valueAt(manifest, "full_timeline.rolling_caption_display_chunk_count") || 0);
  const sourceCueCoverageCount = Number(
    valueAt(manifest, "full_timeline.caption_source_cue_coverage_count") ||
      valueAt(manifest, "caption_context.caption_source_cue_coverage_count") ||
      chunkCount,
  );
  const captionDisplayTimingPath =
    valueAt(manifest, "caption_display_timing_source.path") ||
    valueAt(manifest, "caption_context.caption_display_timing_source.path") ||
    valueAt(manifest, "full_timeline.caption_display_timing_source_path") ||
    valueAt(manifest, "full_timeline.caption_vtt_path");
  const captionDisplayTimingSha =
    valueAt(manifest, "caption_display_timing_source.sha256") ||
    valueAt(manifest, "caption_context.caption_display_timing_source.sha256") ||
    valueAt(manifest, "full_timeline.caption_display_timing_source_sha256") ||
    valueAt(manifest, "full_timeline.caption_vtt_sha256");
  const rawCaptionTimingPath =
    valueAt(manifest, "caption_timing_source.path") ||
    valueAt(manifest, "caption_context.caption_timing_source.path") ||
    valueAt(manifest, "full_timeline.raw_caption_timing_source_path");
  const rawCaptionTimingSha =
    valueAt(manifest, "caption_timing_source.sha256") ||
    valueAt(manifest, "caption_context.caption_timing_source.sha256") ||
    valueAt(manifest, "full_timeline.raw_caption_timing_source_sha256");
  check(
    result,
    hasNonEmptyString(captionDisplayTimingPath) &&
      new RegExp(`offset_intro_${VOICE_START_OFFSET_SLUG}\\.vtt$`, "i").test(captionDisplayTimingPath) &&
      !/offset_intro_9s601/i.test(captionDisplayTimingPath),
    "caption_display_timing_source.intro_trim_sidecar",
    "visible rail captions must use the regenerated offset_intro_3s601 display sidecar, not the old 9.601451s sidecar",
  );
  const sourceCueCount = parseVttCueCount(captionDisplayTimingPath);
  if (sourceCueCount > 0) {
    check(
      result,
      cueCount === sourceCueCount,
      "caption_full_cue_coverage",
      `manifest must include all timing cues without truncation; source has ${sourceCueCount}, manifest has ${cueCount}`,
    );
    check(
      result,
      sourceCueCoverageCount >= cueCount,
      "caption_full_chunk_coverage",
      `display chunks must cover all cues after dense merging; cues ${cueCount}, covered cues ${sourceCueCoverageCount}, chunks ${chunkCount}`,
    );
  }
  const revalidationForAudio = manifest.music_integration_contract_revalidation || {};
  const outroPolicy =
    manifest.outro_policy ||
    revalidationForAudio.outro_policy ||
    valueAt(manifest, "review_audio_mix.timing.outro_policy") ||
    valueAt(manifest, "rough_assembly_reads.outro_policy");
  const outroPrelap = Number(manifest.outro_prelap_seconds ?? revalidationForAudio.outro_prelap_seconds);
  const outroTargetAfterVoice = Number(
    manifest.outro_target_after_voice_seconds ?? revalidationForAudio.outro_target_after_voice_seconds,
  );
  const voOutroBlendRead =
    manifest.vo_outro_blend_read ||
    revalidationForAudio.vo_outro_blend_read ||
    valueAt(manifest, "rough_assembly_reads.vo_outro_blend_read");
  check(
    result,
    outroPolicy === OUTRO_POLICY &&
      Number.isFinite(outroPrelap) &&
      Math.abs(outroPrelap - 1.5) <= 0.05 &&
      Number.isFinite(outroTargetAfterVoice) &&
      outroTargetAfterVoice >= 2.9 &&
      /^pass/i.test(String(voOutroBlendRead || "")),
    "audio.vo_outro_subtle_tail_policy",
    "rough rail proofs must use subtle_tail_outro_v1: 1.5s prelap, low under VO, target after VO with no hard restart",
  );
  if (manifest.episode_id === "hyatt-regency") {
    const repair = manifest.audio_defect_repair || valueAt(manifest, "review_audio_mix.audio_defect_repair") || {};
    const revalidation = manifest.music_integration_contract_revalidation || {};
    const sourceVoiceMasterPath =
      valueAt(manifest, "music_integration_contract_revalidation.source_voice_master_path") ||
      valueAt(manifest, "review_audio_mix.audio_defect_repair.repaired_voice_master.path");
    check(
      result,
      manifest.voice_audio_defect_repair_model === "kept_hyatt_live_load_blip_repair_v1" &&
        revalidation.voice_audio_defect_repair_model === "kept_hyatt_live_load_blip_repair_v1" &&
        valueAt(manifest, "approved_audio.voice_audio_defect_repair_model") ===
          "kept_hyatt_live_load_blip_repair_v1",
      "hyatt.voice_audio_defect_repair_model",
      "Hyatt rolling proof must record the kept live-load blip repair model in manifest, audio, and mix revalidation provenance",
    );
    check(
      result,
      path.resolve(sourceVoiceMasterPath || "") === HYATT_BLIP_REPAIRED_VOICE_MASTER_PATH &&
        path.resolve(valueAt(repair, "repaired_voice_master.path") || "") === HYATT_BLIP_REPAIRED_VOICE_MASTER_PATH &&
        fs.existsSync(HYATT_BLIP_REPAIRED_VOICE_MASTER_PATH),
      "hyatt.repaired_voice_master_used",
      "Hyatt review mix must use the kept blip-repaired voice master, not the older live-load defect master",
    );
    check(
      result,
      path.resolve(valueAt(repair, "superseded_defective_voice_master.path") || "") ===
        HYATT_SUPERSEDED_DEFECTIVE_VOICE_MASTER_PATH,
      "hyatt.superseded_defective_voice_master_recorded",
      "Hyatt manifest must record the superseded defective live-load voice master path",
    );
    check(
      result,
      Array.isArray(valueAt(repair, "defect_windows_proof_seconds")) &&
        valueAt(repair, "defect_windows_proof_seconds").length >= 2,
      "hyatt.defect_windows_recorded",
      "Hyatt audio defect repair provenance must record the proof-time repaired windows for targeted listen/QA",
    );
  }
  const semmelweisRightRailAlignmentOnly =
    manifest.episode_id === "semmelweis" &&
    (manifest.right_rail_alignment_review_only === true || /right_rail_alignment_only/i.test(String(manifest.status || "")));
  if (semmelweisRightRailAlignmentOnly) {
    const deferral = manifest.ambient_effects_deferral || {};
    const revalidation = manifest.music_integration_contract_revalidation || {};
    check(
      result,
      manifest.review_only === true && manifest.right_rail_alignment_review_only === true,
      "semmelweis.right_rail_alignment_review_only",
      "Semmelweis may be reviewable before ambient v7 advice only as right_rail_alignment_review_only",
    );
    check(
      result,
      deferral.status === "v7_sink_faucet_pending_later_advice" &&
        /defer|pending/i.test(String(deferral.deferred_human_disposition || "")),
      "semmelweis.ambient_v7_deferred",
      "Semmelweis v7 ambient/effects must be recorded as deferred, not kept or rejected",
    );
    check(
      result,
      fs.existsSync(resolveCandidate(deferral.deferral_note_path, process.cwd())),
      "semmelweis.ambient_deferral_note",
      "Semmelweis ambient deferral note must exist",
    );
    check(
      result,
      deferral.active_for_right_rail_alignment === "prior_kept_v6_ambient_effects_layer" &&
        fs.existsSync(resolveCandidate(deferral.prior_kept_ambient_manifest_path, process.cwd())),
      "semmelweis.prior_kept_ambient_source",
      "Semmelweis right-rail alignment proof must use the prior kept v6 ambient source",
    );
    check(
      result,
      revalidation.status === "pass_revalidated_with_contract_timed_music_mix_against_prior_kept_v6_ambient_state" &&
        revalidation.scope === "right_rail_alignment_contract_timed_music_and_end_screen_review_not_final_mix_keep",
      "semmelweis.music_contract_alignment_revalidation",
      "Semmelweis music contract must be revalidated with contract-timed music/end-screen review, not final mix keep",
    );
    const reviewAudioMixPath = resolveCandidate(
      valueAt(manifest, "review_audio_mix.path") || revalidation.review_audio_mix_path || valueAt(manifest, "approved_audio.path"),
      process.cwd(),
    );
    const reviewAudioMixDuration = Number(
      valueAt(manifest, "review_audio_mix.duration_seconds") ||
        revalidation.review_audio_mix_duration_seconds ||
        valueAt(manifest, "approved_audio.duration_seconds"),
    );
    const expectedReviewDuration = Number(
      valueAt(manifest, "review_audio_mix.expected_duration_seconds") ||
        revalidation.review_audio_mix_expected_duration_seconds ||
        valueAt(manifest, "full_timeline.duration_seconds"),
    );
    check(
      result,
      fs.existsSync(reviewAudioMixPath) &&
        /^right_rail_alignment_contract_timed_intro_voice_outro_review_mix(?:_outro_level_successor)?$/.test(
          String(valueAt(manifest, "approved_audio.role") || ""),
        ) &&
        valueAt(manifest, "review_audio_mix.model") === "contract_timed_intro_voice_outro_mix_v1" &&
        !/timing_proxy|silence/i.test(String(valueAt(manifest, "approved_audio.role") || "")),
      "semmelweis.contract_timed_review_audio_mix",
      "Semmelweis right-rail alignment proof must use a contract-timed intro/voice/outro music mix, not a silence timing proxy",
    );
    check(
      result,
      Number.isFinite(reviewAudioMixDuration) &&
        Number.isFinite(expectedReviewDuration) &&
        Math.abs(reviewAudioMixDuration - expectedReviewDuration) <= 0.08,
      "semmelweis.review_audio_mix_duration",
      `Semmelweis review audio mix duration must match music contract; got ${reviewAudioMixDuration}, expected ${expectedReviewDuration}`,
    );
    check(
      result,
      revalidation.intro_music_applied_read === "pass" &&
        revalidation.full_outro_music_applied_read === "pass" &&
        /pass/i.test(String(revalidation.youtube_end_screen_template_applied_read || "")) &&
        /pass/i.test(String(revalidation.end_screen_target_geometry_read || "")),
      "semmelweis.music_and_end_screen_reads",
      "Semmelweis right-rail alignment proof must record intro music, full outro music, and YouTube end-screen geometry reads",
    );
    const playerHtmlPath = resolveCandidate(valueAt(manifest, "proof_artifacts.player_html_path"), process.cwd());
    const playerHtml = fs.existsSync(playerHtmlPath) ? fs.readFileSync(playerHtmlPath, "utf8") : "";
    check(
      result,
      /ce-youtube-end-screen|CE_END_SCREEN/i.test(playerHtml) &&
        /window\.__outroDebugAt/i.test(playerHtml) &&
        /safeWindowStartSeconds/i.test(playerHtml),
      "semmelweis.youtube_end_screen_player_hook",
      "Semmelweis player must inject the YouTube end-screen overlay and __outroDebugAt timing hook",
    );
    check(
      result,
      hasNonEmptyString(captionDisplayTimingPath) && !/TBD_AFTER_PREREQ_KEEP/i.test(captionDisplayTimingPath),
      "semmelweis.real_caption_sidecar",
      "Semmelweis alignment proof must use the real script-locked offset caption sidecar",
    );
  }
  if (manifest.episode_id === "737-max") {
    const revalidation = manifest.music_integration_contract_revalidation || {};
    const reviewAudioMixPath = resolveCandidate(
      valueAt(manifest, "review_audio_mix.path") || revalidation.review_audio_mix_path || valueAt(manifest, "approved_audio.path"),
      process.cwd(),
    );
    const reviewAudioMixDuration = Number(
      valueAt(manifest, "review_audio_mix.duration_seconds") ||
        revalidation.review_audio_mix_duration_seconds ||
        valueAt(manifest, "approved_audio.duration_seconds"),
    );
    const expectedReviewDuration = Number(
      valueAt(manifest, "review_audio_mix.expected_duration_seconds") ||
        revalidation.review_audio_mix_expected_duration_seconds ||
        valueAt(manifest, "full_timeline.duration_seconds"),
    );
    check(
      result,
      fs.existsSync(resolveCandidate(revalidation.contract_json_path, process.cwd())) &&
        revalidation.status === "pass_contract_timed_music_mix_created_for_reviewable_rough_rail_proof",
      "737_max.music_contract_created",
      "737 MAX must have a packet-local music integration contract before the rolling rail proof is reviewable",
    );
    check(
      result,
      fs.existsSync(reviewAudioMixPath) &&
        valueAt(manifest, "approved_audio.role") === "right_rail_alignment_contract_timed_intro_voice_outro_review_mix" &&
        valueAt(manifest, "review_audio_mix.model") === "contract_timed_intro_voice_outro_mix_v1",
      "737_max.contract_timed_review_audio_mix",
      "737 MAX review proof must use a contract-timed intro/voice/outro music mix",
    );
    check(
      result,
      Number.isFinite(reviewAudioMixDuration) &&
        Number.isFinite(expectedReviewDuration) &&
        Math.abs(reviewAudioMixDuration - expectedReviewDuration) <= 0.08,
      "737_max.review_audio_mix_duration",
      `737 MAX review audio mix duration must match music contract; got ${reviewAudioMixDuration}, expected ${expectedReviewDuration}`,
    );
    check(
      result,
      hasNonEmptyString(captionDisplayTimingPath) &&
        /offset_intro_3s601\.vtt$/i.test(captionDisplayTimingPath) &&
        !/offset_intro_0s000|TBD_AFTER_PREREQ_KEEP/i.test(captionDisplayTimingPath),
      "737_max.offset_sidecar",
      "737 MAX visible rail captions must use the 3.601451s offset script-locked sidecar",
    );
    check(
      result,
      !/TBD_LOCKED_SCRIPT_PATH_REQUIRED_FOR_KEEP/i.test(String(valueAt(manifest, "caption_text_source.path") || "")),
      "737_max.locked_script_source",
      "737 MAX caption text source must point to the locked narration script",
    );
    check(
      result,
      Math.abs(Number(manifest.caption_audio_offset_seconds) - VOICE_START_OFFSET_SECONDS) <= 0.0005 &&
        manifest.caption_audio_sync_model === CAPTION_AUDIO_SYNC_MODEL,
      "737_max.caption_audio_sync",
      "737 MAX visible rail captions must be on the source-sidecar audio timeline with the 3.601451s offset",
    );
    check(
      result,
      Number(valueAt(manifest, "end_screen_context.end_screen_timing.safeWindowStartSeconds")) === 955.766144 ||
        Number(valueAt(manifest, "end_screen_context.end_screen_timing.holdStartSeconds")) === 955.766144 ||
        Math.abs(Number(revalidation.planned_total_duration_seconds) - 975.766) <= 0.01,
      "737_max.real_end_screen_timing",
      "737 MAX must carry the contract end-screen timing instead of the placeholder duration",
    );
  }

  const predecessorManifestPath = resolveCandidate(manifest.source_predecessor_manifest_path, process.cwd());
  const predecessorManifest = readJsonIfExists(predecessorManifestPath);
  const predecessorRoot = predecessorManifestPath ? path.dirname(predecessorManifestPath) : "";
  const predecessorSidecarPath = resolveCandidate(valueAt(predecessorManifest, "caption_sidecar.path"), predecessorRoot);
  const predecessorSidecarSha = valueAt(predecessorManifest, "caption_sidecar.sha256");
  const predecessorVoiceStart = Number(
    valueAt(predecessorManifest, "preserved_timing_and_audio.voice_start_seconds") ??
      valueAt(predecessorManifest, "voice_timing.voice_start_seconds") ??
      valueAt(predecessorManifest, "voice_start_seconds"),
  );
  const predecessorPlayerPath = resolveCandidate(manifest.source_predecessor_player_path, predecessorRoot);
  const predecessorTrack = fs.existsSync(predecessorPlayerPath)
    ? captionTrackInfoFromHtml(fs.readFileSync(predecessorPlayerPath, "utf8"), path.dirname(predecessorPlayerPath))
    : {};
  const contractOffsetSidecarPath = resolveCandidate(
    valueAt(manifest, "music_integration_contract_revalidation.caption_offset_sidecar_path"),
    process.cwd(),
  );
  const manifestAudioOffset = Number(
    manifest.caption_audio_offset_seconds ??
      valueAt(manifest, "caption_context.caption_audio_offset_seconds") ??
      valueAt(manifest, "full_timeline.caption_audio_offset_seconds"),
  );
  check(
    result,
    Math.abs(manifestAudioOffset - VOICE_START_OFFSET_SECONDS) <= 0.0005,
    "caption_audio_offset_seconds.intro_trim",
    "caption_audio_offset_seconds must use the trimmed 3.601451s visible rail timeline",
  );
  const declaredOffset = [manifestAudioOffset, predecessorVoiceStart, predecessorTrack.offsetSeconds].find((value) => Number.isFinite(value) && value > 0) || 0;
  const hasOffsetDeclaration = declaredOffset > 0;
  const expectedDisplayPath =
    predecessorSidecarPath ||
    contractOffsetSidecarPath ||
    (Number.isFinite(predecessorTrack.offsetSeconds) && predecessorTrack.offsetSeconds > 0 ? predecessorTrack.path : "");
  const expectedDisplaySha = predecessorSidecarSha || predecessorTrack.offsetVttSha256 || "";
  const displayFirstStart = parseFirstVttStart(captionDisplayTimingPath);
  const manifestFirstStart = Number(
    valueAt(manifest, "full_timeline.first_caption_display_cue_start_seconds") ??
      valueAt(manifest, "caption_context.first_caption_display_cue_start_seconds"),
  );

  if (hasOffsetDeclaration) {
    check(
      result,
      manifest.caption_audio_sync_model === CAPTION_AUDIO_SYNC_MODEL ||
        valueAt(manifest, "caption_context.caption_audio_sync_model") === CAPTION_AUDIO_SYNC_MODEL ||
        valueAt(manifest, "full_timeline.caption_audio_sync_model") === CAPTION_AUDIO_SYNC_MODEL,
      "caption_audio_sync_model.source_sidecar_audio_time",
      "proofs with a voice-start offset must use source_sidecar_audio_time_v1 for visible rail captions",
    );
    check(
      result,
      hasNonEmptyString(captionDisplayTimingPath),
      "caption_display_timing_source.path",
      "offset proofs must declare the display caption sidecar used for visible rail chunks",
    );
    check(
      result,
      !rawCaptionTimingPath || !samePath(captionDisplayTimingPath, rawCaptionTimingPath) || !/voice|master|diarized|transcript/i.test(rawCaptionTimingPath),
      "caption_display_not_raw_unoffset_transcript",
      "visible rail chunks must not use the raw unoffset voice-master transcript when an offset sidecar exists",
    );
    check(
      result,
      Number.isFinite(displayFirstStart) && Math.abs(displayFirstStart - manifestFirstStart) <= 0.075,
      "caption_first_display_cue_manifest_match",
      `manifest first display cue start must match the display sidecar; sidecar=${displayFirstStart}, manifest=${manifestFirstStart}`,
    );
    check(
      result,
      Number.isFinite(displayFirstStart) && displayFirstStart >= declaredOffset - 0.25,
      "caption_first_display_cue_audio_time",
      `first visible rail cue must be on the audio timeline near/after the voice offset ${declaredOffset}; found ${displayFirstStart}`,
    );
  }
  if (hasOffsetDeclaration && expectedDisplayPath) {
    const introTrimDisplayPath =
      hasNonEmptyString(captionDisplayTimingPath) &&
      new RegExp(`offset_intro_${VOICE_START_OFFSET_SLUG}\\.vtt$`, "i").test(captionDisplayTimingPath);
    check(
      result,
      introTrimDisplayPath ||
        samePathOrSha(captionDisplayTimingPath, expectedDisplayPath, captionDisplayTimingSha, expectedDisplaySha),
      "caption_display_uses_intro_trim_sidecar",
      `visible rail captions must use the regenerated intro-trim sidecar or the predecessor native track when no trim is active; expected ${expectedDisplayPath}, found ${captionDisplayTimingPath}`,
    );
  }
  if (hasOffsetDeclaration && expectedDisplayPath && rawCaptionTimingPath) {
    check(
      result,
      !samePath(expectedDisplayPath, rawCaptionTimingPath) || !/voice|master|diarized|transcript/i.test(rawCaptionTimingPath),
      "caption_raw_timing_separate_from_display_sidecar",
      "raw ASR timing evidence must remain separate from the offset display sidecar when both exist",
    );
  }
  const missingSpanRead =
    valueAt(manifest, "rough_assembly_reads.caption_key_phrase_span_read") ||
    valueAt(manifest, "living_cover_cue_map.status") ||
    "";
  if (spans.length === 0) {
    check(
      result,
      /blocked|pending/i.test(String(missingSpanRead)) &&
        valueAt(manifest, "qa.caption_highlight_suppressed_without_reviewed_spans_static_pass") === true,
      "key_phrase_spans.missing_blocked",
      "missing reviewed spans must keep the packet blocked/pending and suppress highlight rendering",
    );
  }
  if (spans.length > 0) {
    const singleWordCount = spans.filter((span) => phraseWordCount(span.phrase_text) === 1).length;
    const invalidLengthCount = spans.filter((span) => {
      const count = phraseWordCount(span.phrase_text);
      return count < 2 || count > 9;
    }).length;
    const durationSeconds = Number(valueAt(manifest, "approved_audio.duration_seconds") || valueAt(manifest, "full_timeline.duration_seconds") || 0);
    const maxGap = maxHighlightGapSeconds(spans, durationSeconds || undefined);
    const expectedCount = EXPECTED_LESSON_TAKEAWAY_COUNTS[manifest.episode_id];
    check(result, singleWordCount === 0, "key_phrase_spans.no_single_word_highlights", `single-word highlights found ${singleWordCount}`);
    check(result, invalidLengthCount === 0, "key_phrase_spans.takeaway_phrase_length", `highlight phrases must be 2-9 words; invalid count ${invalidLengthCount}`);
    if (expectedCount) {
      check(
        result,
        spans.length === expectedCount,
        "key_phrase_spans.approved_takeaway_count",
        `${manifest.episode_id} should have ${expectedCount} approved takeaway highlights; found ${spans.length}`,
      );
      check(
        result,
        Number.isFinite(maxGap) && maxGap <= 90,
        "key_phrase_spans.max_gap",
        `${manifest.episode_id} post-intro highlight gap must be <= 90s; found ${maxGap}`,
      );
    }
  }
  spans.forEach((span, index) => {
    check(result, hasNonEmptyString(span.phrase_text), `key_phrase_spans.${index}.phrase_text`, "phrase text is required");
    check(
      result,
      Array.isArray(span.normalized_script_token_range) && span.normalized_script_token_range.length === 2,
      `key_phrase_spans.${index}.normalized_script_token_range`,
      "normalized script token range must be [start, end]",
    );
    check(
      result,
      Array.isArray(span.timing_window_seconds) && span.timing_window_seconds.length === 2,
      `key_phrase_spans.${index}.timing_window_seconds`,
      "timing window must be [start, end]",
    );
    check(
      result,
      hasNonEmptyString(span.highlight_color_sample?.hex || span.highlight_color_hex),
      `key_phrase_spans.${index}.highlight_color_sample`,
      "highlight color sample is required",
    );
    const colorQa = span.highlight_color_qa || {};
    const activeTextHex =
      colorQa.active_caption_text_hex ||
      valueAt(manifest, "caption_context.highlight_color_qa.active_caption_text_hex") ||
      valueAt(manifest, "highlight_color_qa.active_caption_text_hex") ||
      valueAt(manifest, "rail_behavior.rolling_caption_window.highlight_color_qa.active_caption_text_hex") ||
      "#f7efe1";
    const mutedTextHex =
      colorQa.adjacent_caption_text_hex ||
      valueAt(manifest, "caption_context.highlight_color_qa.adjacent_caption_text_hex") ||
      valueAt(manifest, "highlight_color_qa.adjacent_caption_text_hex") ||
      valueAt(manifest, "rail_behavior.rolling_caption_window.highlight_color_qa.adjacent_caption_text_hex") ||
      "#b9c8d8";
    const highlightHex = span.highlight_color_sample?.hex || span.highlight_color_hex;
    const backplateSampleHexes =
      span.highlight_color_sample?.backplate_contrast_sample_hexes ||
      colorQa.backplate_contrast_sample_hexes ||
      valueAt(manifest, "caption_context.highlight_color_qa.backplate_contrast_sample_hexes") ||
      valueAt(manifest, "highlight_color_qa.backplate_contrast_sample_hexes") ||
      valueAt(manifest, "rail_behavior.rolling_caption_window.highlight_color_qa.backplate_contrast_sample_hexes") ||
      [];
    const distinctness = highlightDistinctnessMetrics(highlightHex, activeTextHex, mutedTextHex, backplateSampleHexes);
    const overridePass = humanApprovedHighlightOverridePass(manifest, span, colorQa, highlightHex, distinctness);
    check(
      result,
      (distinctness.pass || overridePass) &&
        /pass/i.test(String(span.highlight_distinct_from_caption_text_read || colorQa.highlight_distinct_from_caption_text_read || "")),
      `key_phrase_spans.${index}.adaptive_distinct_highlight_color`,
      `highlight color must be source-sampled and distinct from caption text and sampled backplate; active delta ${distinctness.activeDelta}, muted delta ${distinctness.mutedDelta}, active contrast ${distinctness.activeContrast}, muted contrast ${distinctness.mutedContrast}, min backplate contrast ${distinctness.minimumBackplateContrast}, p20 backplate contrast ${distinctness.p20BackplateContrast}, min backplate delta ${distinctness.minimumBackplateDelta}`,
    );
    if (manifest.episode_id === "semmelweis") {
      check(
        result,
        String(highlightHex || "").toLowerCase() === "#efef9f" && overridePass,
        `key_phrase_spans.${index}.semmelweis_human_highlight_override`,
        "Semmelweis highlight must use the review-safe #efef9f override and satisfy backplate/distance gates",
      );
    }
    check(
      result,
      Array.isArray(backplateSampleHexes) &&
        backplateSampleHexes.length >= 9 &&
        distinctness.minimumBackplateContrast >= HIGHLIGHT_MIN_BACKPLATE_CONTRAST_RATIO &&
        distinctness.p20BackplateContrast >= HIGHLIGHT_P20_BACKPLATE_CONTRAST_RATIO &&
        distinctness.minimumBackplateDelta >= HIGHLIGHT_MIN_BACKPLATE_COLOR_DELTA &&
        /pass/i.test(String(span.highlight_backplate_contrast_read || colorQa.highlight_backplate_contrast_read || "")),
      `key_phrase_spans.${index}.highlight_backplate_contrast`,
      `highlight color must survive the sampled caption-window backplate; sample count ${Array.isArray(backplateSampleHexes) ? backplateSampleHexes.length : 0}, min contrast ${distinctness.minimumBackplateContrast}, p20 contrast ${distinctness.p20BackplateContrast}, min delta ${distinctness.minimumBackplateDelta}`,
    );
    check(
      result,
      hasNonEmptyString(span.highlight_color_sample?.source_art_path || colorQa.source_art_path) &&
        hasNonEmptyString(span.highlight_color_sample?.source_art_sha256 || colorQa.source_art_sha256) &&
        hasNonEmptyString(span.highlight_color_sample?.sample_hex || colorQa.sample_hex),
      `key_phrase_spans.${index}.highlight_color_source_sample`,
      "highlight color must record source backplate path/hash and sample color",
    );
    check(result, Number(span.fade_in_seconds) >= 0, `key_phrase_spans.${index}.fade_in_seconds`, "fade-in duration is required");
    check(result, Number(span.fade_out_seconds) >= 0, `key_phrase_spans.${index}.fade_out_seconds`, "fade-out duration is required");
    check(
      result,
      span.caption_highlight_model_id === CAPTION_HIGHLIGHT_MODEL_ID,
      `key_phrase_spans.${index}.caption_highlight_model_id`,
      "span must use lesson_takeaway_highlight_v1",
    );
    check(
      result,
      span.highlight_semantic_role === HIGHLIGHT_SEMANTIC_ROLE,
      `key_phrase_spans.${index}.highlight_semantic_role`,
      "span must be authored as a story lesson/takeaway",
    );
    check(
      result,
      span.highlight_density_model === HIGHLIGHT_DENSITY_MODEL,
      `key_phrase_spans.${index}.highlight_density_model`,
      "span must use memorable takeaway cadence",
    );
    check(
      result,
      span.highlight_color_model === HIGHLIGHT_COLOR_MODEL,
      `key_phrase_spans.${index}.highlight_color_model`,
      "span must use source-sampled caption-window backplate contrast takeaway accent color model",
    );
    check(
      result,
      span.highlight_visual_timing_model === HIGHLIGHT_VISUAL_TIMING_MODEL,
      `key_phrase_spans.${index}.highlight_visual_timing_model`,
      "span must use active-band visual timing",
    );
    check(
      result,
      Array.isArray(span.visual_timing_window_seconds) && span.visual_timing_window_seconds.length === 2,
      `key_phrase_spans.${index}.visual_timing_window_seconds`,
      "visual timing window is required for active-band highlight alpha",
    );
    check(result, hasNonEmptyString(span.review_status), `key_phrase_spans.${index}.review_status`, "review status is required");
  });

  const roughProofKept = cleanText(manifest.human_disposition).toLowerCase() === "keep";
  for (const gate of ["may_create_full_runtime_mp4_render", "may_advance_to_video_render", "may_advance_to_final_assembly"]) {
    if (manifest[gate] !== undefined) {
      check(
        result,
        manifest[gate] === roughProofKept,
        gate,
        `rough rail proofs may open final assembly only after human keep; found ${manifest[gate]} with human_disposition=${manifest.human_disposition}`,
      );
    }
  }
  for (const gate of ["may_advance_to_publish_readiness", "may_youtube_action"]) {
    if (manifest[gate] !== undefined) {
      check(result, manifest[gate] === false, gate, "publish readiness and YouTube action must remain blocked until later keeps");
    }
  }
}

function validatePlayer(playerPath, result, manifest) {
  if (!playerPath) return;
  const html = fs.readFileSync(playerPath, "utf8");
  for (const failure of endScreenPalettePlayerFailures(html, endScreenPaletteContractForManifest(manifest))) {
    check(result, false, failure.id, failure.detail);
  }
  const endScreenEntryNeedle = isYoutubeLegalWindowEndScreenEntry(manifest)
    ? YOUTUBE_LEGAL_WINDOW_END_SCREEN_ENTRY_MODEL
    : "review_approved_end_screen_entry_v1";
  const endScreenFadeNeedle = isYoutubeLegalWindowEndScreenEntry(manifest)
    ? YOUTUBE_LEGAL_WINDOW_END_SCREEN_ENTRY_MODEL
    : "caption_exit_aligned_end_screen_fade_v1";
  for (const needle of [
    "ce-rolling-caption-rail-tighten-style:start",
    "ce-rolling-caption-rail-tighten-script:start",
    "setAttribute(\"data-content-model\", \"rolling_caption_anchor_v1\")",
    "data-display-model=\"rolling_rail_caption_window_v1\"",
    "window.__railCaptionStateAt",
    "window.__syncRailCaptionToMediaTime",
    "window.__setRenderTime",
    "window.__ceReviewTransportState",
    "reviewTransportScrubModel",
    "foreground_transport_scrub_lock_v1",
    "window.__ceRunProofFreshnessCheck",
    "window.__ceShowStaleProofWarning",
    "proof_build.json",
    "This proof has been regenerated. Refresh before reviewing.",
    "ce-caption-window",
    "ce-legacy-rail-hidden",
    "ce-legacy-review-chrome-hidden",
    "ce-review-transport",
    "reviewControlModel",
    "legacyReviewChromeSuppressionModel",
    "captionPlaybackClockModel",
    "playbackClockTime",
    "captionStackRenderModel",
    "startCompositorScroll",
    "captionRuntimeCoverageModel",
    "runtimeCoverageStateAt",
    "maxVisibleCaptionOpacity",
    "visibleCaptionLineCount",
    "lastCaptionCueEndSeconds",
    "endScreenSuppressionActive",
    "window.__endScreenStateAt",
    "suppressInheritedEndScreens",
    "ce-legacy-end-screen-hidden",
    "adaptive_titleless_youtube_end_screen_overlay_on_living_cover_v1",
    endScreenFadeNeedle,
    endScreenEntryNeedle,
    "lastCaptionFullySuppressedSeconds",
    END_SCREEN_PALETTE_TREATMENT_MODEL,
    END_SCREEN_ADAPTIVE_VARIABILITY_MODEL,
    "suppressLegacyReviewChrome",
    "script_locked_chunk_split_v1",
    "reviewed_cue_map_spans_only",
    "translateY",
  ]) {
    check(result, html.includes(needle), `player.contains.${needle}`, `player must include ${needle}`);
  }
  if (AMBIENT_FRAME_CLOCK_EPISODES.has(manifest.episode_id)) {
    check(
      result,
      html.includes("window.__ceSetAmbientRenderTime") && html.includes("window.__ceAmbientFrameClockState"),
      "player.ambient_render_clock_hook",
      "affected ambient proofs must expose __ceSetAmbientRenderTime and state reads",
    );
    check(
      result,
      html.includes(AMBIENT_FRAME_CLOCK_MODEL) && html.includes(AMBIENT_RENDER_CLOCK_READ),
      "player.ambient_render_clock_read_strings",
      "ambient render-frame clock model/read must be embedded in the player",
    );
    check(
      result,
      html.includes(AMBIENT_WALL_CLOCK_DRIFT_SUPPRESSION_READ),
      "player.ambient_wall_clock_drift_suppression_read",
      "player must record suppression of render-mode wall-clock ambient mutation",
    );
  }
  check(
    result,
    /captionStackCompositorActive/i.test(html) &&
      /captionStackCompositorTargetTime/i.test(html) &&
      /transform "\s*\+\s*duration\.toFixed\(3\)\s*\+\s*"s linear"/i.test(html),
    "player.compositor_linear_caption_transform_driver",
    "caption rail playback must use one compositor-owned linear transform driver, with direct media-time resets for pause/seek/scrub/render-time jumps",
  );
  check(
    result,
    /#endScreen,\s*#outroScreen,\s*\.end-screen,\s*\.outro-screen,\s*\.youtube-end-screen,\s*\[data-youtube-end-screen\]/i.test(html) &&
      /classList\.contains\(["']ce-youtube-end-screen["']\)/i.test(html),
    "player.broad_inherited_end_screen_suppression",
    "player must suppress inherited predecessor end screens without suppressing the new adaptive CE overlay",
  );
  check(
    result,
    html.includes(manifest.proof_build_id || "") &&
      /proofBuildId:\s*["'][^"']+_(?:rolling_caption_rail|caption-highlight-runtime-audit)_\d{8}T\d{6,9}Z(?:_html_review)?["']/i.test(html),
    "player.proof_build_id",
    "player must embed the manifest proof_build_id for stale-tab detection",
  );
  check(
    result,
    /html\.render-mode[\s\S]*\.ce-proof-freshness-warning/i.test(html),
    "player.freshness_warning_hidden_in_render_mode",
    "proof freshness warning must be hidden in render mode",
  );
  if (
    fs.existsSync(REVIEW_INDEX_PATH) &&
    manifest.proof_build_id &&
    !isYoutubeLegalWindowEndScreenEntry(manifest)
  ) {
    const indexHtml = fs.readFileSync(REVIEW_INDEX_PATH, "utf8");
    const expectedVersionedUrl = reviewUrlForPath(playerPath, { v: manifest.proof_build_id });
    check(
      result,
      indexHtml.includes(expectedVersionedUrl),
      "review_index.cache_busted_proof_link",
      `review index must link to the proof with ?v=${manifest.proof_build_id}`,
    );
  }
  check(result, !/>\s*Caption\s*</i.test(html), "player.no_caption_eyebrow", "viewer-facing Caption eyebrow is not allowed");
  check(result, !/Rough assembly rail review/i.test(html), "player.no_internal_rough_review_copy", "internal rough-review copy must not be visible or embedded");
  check(
    result,
    !/rolling_caption_anchor_v1\s*\/\s*rolling_rail_caption_window_v1/i.test(html),
    "player.no_model_id_label",
    "model IDs must not appear as viewer-facing labels",
  );
  check(
    result,
    /stage\.querySelectorAll\([^)]*\.rail/i.test(html) && /classList\.add\("ce-legacy-rail-hidden"\)/i.test(html),
    "player.legacy_context_hidden_by_injection",
    "predecessor rail/context rows may remain in source HTML only if the injected rail hides them at runtime",
  );
  check(
    result,
    /\.stage\s*>\s*\.rail[\s\S]*visibility:\s*hidden/i.test(html),
    "player.legacy_rail_hidden_before_script_load",
    "predecessor right rail must be hidden by injected CSS before the rolling-rail script runs",
  );
  if (/class=["'][^"']*\bframe\b/i.test(html)) {
    check(
      result,
      /normalizeResponsiveFrameStage/i.test(html) &&
        /ce-fixed-stage/i.test(html) &&
        /ce-stage-scale-shell/i.test(html),
      "player.responsive_frame_normalized_to_fixed_stage",
      "responsive predecessor frames must be normalized to fixed 1920x1080 stage geometry before rail injection",
    );
    check(
      result,
      /main:has\(>\s*\.frame\)[\s\S]*>\s*\.player/i.test(html) &&
        /main:has\(>\s*\.frame\)[\s\S]*>\s*\.body/i.test(html),
      "player.frame_predecessor_review_chrome_hidden",
      "ambient/source review page chrome must be hidden when a frame predecessor is used as the rough-proof stage",
    );
    check(
      result,
      /\.ce-rolling-rail\s*\{[\s\S]*?background:\s*transparent\s*!important/i.test(html) &&
        /\.ce-rolling-rail\s*\{[\s\S]*?border:\s*0\s*!important/i.test(html) &&
        /\.ce-rolling-rail\s*\{[\s\S]*?padding:\s*0\s*!important/i.test(html),
      "player.rail_container_transparent_reset",
      "injected rail must reset inherited source-review section backgrounds, borders, and padding",
    );
  }
  check(
    result,
    /html\.render-mode[\s\S]*(review-audio|audio-review|review-transport|\.player|\.transport|\.controls|\.machine-reads|timeline-scrubber)/i.test(html),
    "player.render_mode_hides_review_chrome",
    "render mode must hide review/audio chrome outside the video frame",
  );
  const hasForbiddenReviewChromeText = FORBIDDEN_REVIEW_CHROME_TEXT.some((token) => html.includes(token));
  if (hasForbiddenReviewChromeText) {
    check(
      result,
      /html\.render-mode[\s\S]*main(?::not\(\.stage\):not\(\.ce-fixed-stage\))?\s*>\s*:not\(\.stage-shell\):not\(\.ce-stage-scale-shell\):not\(\.frame\):not\(\.stage-frame\)/i.test(html) &&
        /html\.render-mode[\s\S]*overflow:\s*hidden\s*!important/i.test(html),
      "player.render_mode_stage_only_guard",
      "render mode must force a stage-only 1920x1080 surface when inherited review text exists",
    );
    check(
      result,
      /html\.render-mode[\s\S]*main(?::not\(\.stage\):not\(\.ce-fixed-stage\))?\s*>\s*:not\(\.stage-shell\):not\(\.ce-stage-scale-shell\):not\(\.frame\):not\(\.stage-frame\)/i.test(html) &&
        /html\.render-mode[\s\S]*(?:\baudio\b|\binput\b|\boutput\b|\bselect\b|\btextarea\b)/i.test(html),
      "player.visible_form_controls_absence_guard",
      "render mode must hide inherited form/audio controls when predecessor review UI text exists",
    );
  }
  check(
    result,
    /html:not\(\.render-mode\)[\s\S]*\.review-controls/i.test(html) &&
      /data-ce-review-chrome-hidden/i.test(html) &&
      /single_foreground_review_transport_v1/i.test(html),
    "player.review_mode_single_foreground_transport",
    "review mode must suppress inherited predecessor controls and use the single foreground transport",
  );
  const injectionBlock =
    html.match(/<!-- ce-rolling-caption-rail-tighten-style:start -->[\s\S]*?<!-- ce-rolling-caption-rail-tighten-script:end -->/)?.[0] || html;
  check(
    result,
    !/\.ce-caption-window\s*\{[^}]*background\s*:/i.test(injectionBlock),
    "player.no_caption_window_background",
    "caption window must not define a background or fill",
  );
  check(
    result,
    !/\.ce-caption-window\s*\{[^}]*(?:backdrop-filter|-webkit-backdrop-filter)\s*:/i.test(injectionBlock) &&
      !/captionWindow\.style\.(?:backdropFilter|webkitBackdropFilter)/i.test(injectionBlock),
    "player.no_caption_window_blur",
    "caption window must not use backdrop blur or scripted blur toggles",
  );
  check(
    result,
    !/visible_caption_presence_gated_blur_v1|captionWindowPresenceModel|captionPresenceOpacityAt|maxVisibleLineOpacityAt|--ce-caption-window-opacity/i.test(
      injectionBlock,
    ),
    "player.no_caption_window_presence_gating",
    "caption window must not retain blur/fill presence-gating behavior",
  );
  check(
    result,
    !/rgba\(120,\s*220,\s*232|rgba\(164,\s*139,\s*255|rgba\(255,\s*248,\s*232,\s*0\.88/i.test(injectionBlock) &&
      !/challenger_titleless_end_screen_overlay_on_living_cover_v1/i.test(injectionBlock) &&
      /CE_END_SCREEN/i.test(injectionBlock) &&
      /palette_source/i.test(injectionBlock) &&
      /window\.__endScreenPaletteContract\s*=\s*CE_END_SCREEN_PALETTE/i.test(injectionBlock),
    "player.end_screen_adaptive_palette",
    "player end-screen targets must use source-sampled palette values, expose the QA contract, and avoid fixed Challenger cyan/purple/cream defaults",
  );
  check(
    result,
    /introTrimModel:\s*"first_eight_intro_trim_6s_v1"/i.test(injectionBlock) &&
      /voiceStartOffsetSeconds:\s*3\.601451/i.test(injectionBlock),
    "player.intro_trim_contract",
    "player must expose the active 6s intro trim and 3.601451s voice offset in browser QA hooks",
  );
  const scrollFunctionBlock =
    injectionBlock.match(/function scrollPositionAt\(time\) \{[\s\S]*?\n    \}/)?.[0] || "";
  check(
    result,
    /captionMotionModel:\s*"constant_speed_audio_time_aligned_scroll_v2"/i.test(injectionBlock) ||
      /constant_speed_audio_time_aligned_scroll_v2/i.test(injectionBlock),
    "player.constant_speed_motion_model",
    "player must expose/use constant_speed_audio_time_aligned_scroll_v2",
  );
  check(
    result,
    /captionTimelineLayoutModel:\s*"audio_time_positioned_stack_v1"/i.test(injectionBlock) ||
      /audio_time_positioned_stack_v1/i.test(injectionBlock),
    "player.audio_time_positioned_stack_model",
    "player must expose/use audio_time_positioned_stack_v1",
  );
  check(
    result,
    /captionSyncTarget:\s*"pre_vo_reading_lead_active_band_v1"/i.test(injectionBlock) ||
      /pre_vo_reading_lead_active_band_v1/i.test(injectionBlock),
    "player.pre_vo_reading_lead_sync_target",
    "player must expose/use the pre-VO reading lead sync target",
  );
  check(
    result,
    /captionReadingLeadSeconds:\s*0\.65/i.test(injectionBlock) && /activeChunkLeadSeconds/i.test(injectionBlock),
    "player.caption_reading_lead_state",
    "player must expose the 0.65s reading lead and activeChunkLeadSeconds QA state",
  );
  check(
    result,
    /function introGateOpacityAt\(time\)/i.test(injectionBlock) &&
      /captionIntroVisibilityGateModel:\s*"first_vo_intro_hold_fade_v1"/i.test(injectionBlock) &&
      /captionIntroGateOpacity/i.test(injectionBlock) &&
      /captionIntroGateStartSeconds/i.test(injectionBlock) &&
      /captionIntroGateFullOpacitySeconds/i.test(injectionBlock) &&
      /lineOpacityAt\([^)]*state\.time/i.test(injectionBlock),
    "player.caption_intro_visibility_gate",
    "player must hide pre-VO intro captions and expose intro gate QA state",
  );
  check(
    result,
    /activeChunkCueStartSeconds/i.test(injectionBlock) && /activeChunkCenterDeltaPx/i.test(injectionBlock),
    "player.active_chunk_alignment_state",
    "player must expose active cue start and center delta QA state",
  );
  check(
    result,
    /captionConstantScrollSpeedPxPerSecond/i.test(injectionBlock) &&
      /caption_constant_scroll_speed_px_per_second|captionConstantScrollSpeedPxPerSecond/i.test(injectionBlock),
    "player.constant_scroll_speed_config",
    "player must receive one constant scroll speed value",
  );
  check(
    result,
    /captionWindowTreatmentModel:\s*"transparent_caption_mask_only_v1"/i.test(injectionBlock) ||
      /transparent_caption_mask_only_v1/i.test(injectionBlock),
    "player.caption_window_treatment_model",
    "player must expose/use transparent_caption_mask_only_v1",
  );
  check(
    result,
    /captionRuntimeCoverageModel:\s*"full_vo_runtime_visible_caption_coverage_v1"/i.test(injectionBlock) &&
      /function runtimeCoverageStateAt\(time,\s*translateY,\s*sourceOpacity\)/i.test(injectionBlock) &&
      /visibleCaptionLineCount/i.test(injectionBlock) &&
      /maxVisibleCaptionOpacity/i.test(injectionBlock) &&
      /lastCaptionCueEndSeconds/i.test(injectionBlock) &&
      /endScreenSuppressionActive/i.test(injectionBlock),
    "player.runtime_coverage_state",
    "player must expose runtime-verifiable full-VO caption coverage state",
  );
  check(
    result,
    /\.ce-caption-window[\s\S]*?mask-image:/i.test(injectionBlock),
    "player.caption_window_mask_only",
    "caption window may retain only the caption entry/exit mask treatment",
  );
  check(
    result,
    /captionLineOpacityModel:\s*"viewport_distance_smoothstep_v1"/i.test(injectionBlock) ||
      /viewport_distance_smoothstep_v1/i.test(injectionBlock),
    "player.viewport_distance_opacity_model",
    "player must expose/use viewport_distance_smoothstep_v1",
  );
  check(
    result,
    /highlightPhraseScope:\s*"exact_authored_span_only"/i.test(injectionBlock) ||
      /exact_authored_span_only/i.test(injectionBlock),
    "player.exact_phrase_highlight_scope",
    "player must use exact authored phrase-span highlighting",
  );
  check(
    result,
    /captionHighlightModelId:\s*"lesson_takeaway_highlight_v1"/i.test(injectionBlock) ||
      /lesson_takeaway_highlight_v1/i.test(injectionBlock),
    "player.lesson_takeaway_highlight_model",
    "player must expose/use lesson_takeaway_highlight_v1",
  );
  check(
    result,
    /highlightSemanticRole:\s*"story_lesson_takeaway"/i.test(injectionBlock) ||
      /story_lesson_takeaway/i.test(injectionBlock),
    "player.story_lesson_takeaway_role",
    "player must expose/use story_lesson_takeaway highlight role",
  );
  check(
    result,
    /highlightVisualTimingModel:\s*"active_band_presence_aligned_v1"/i.test(injectionBlock) &&
      /visual_timing_window_seconds/i.test(injectionBlock),
    "player.active_band_highlight_timing",
    "highlight alpha must use active-band visual timing windows",
  );
  check(
    result,
    /captionLayoutCollisionGuard:\s*"fixed_line_box_visual_gap_guard_v1"/i.test(injectionBlock) ||
      /fixed_line_box_visual_gap_guard_v1/i.test(injectionBlock),
    "player.caption_layout_collision_guard",
    "player must expose/use fixed_line_box_visual_gap_guard_v1",
  );
  check(
    result,
    /ce-caption-display-line/i.test(injectionBlock) && /display_lines/i.test(injectionBlock),
    "player.deterministic_caption_display_lines",
    "player must render precomputed deterministic caption lines instead of relying on browser wrapping",
  );
  const injectedChunks = parseInjectedJsonish(html, "CE_CHUNKS") || [];
  const injectedConfig = parseInjectedJsonish(html, "CE_CONFIG") || {};
  const playerMaxLineWidth = maxEstimatedDisplayLineWidthPx(injectedChunks);
  const stackCssBlock = injectionBlock.match(/\.ce-caption-stack\s*\{[\s\S]*?\}/i)?.[0] || "";
  check(
    result,
    injectedConfig.captionDisplayLineWrapModel === CAPTION_DISPLAY_LINE_WRAP_MODEL ||
      injectionBlock.includes(CAPTION_DISPLAY_LINE_WRAP_MODEL),
    "player.pixel_budgeted_caption_line_wrap",
    "player must expose/use pixel_budgeted_deterministic_line_wrap_v1",
  );
  check(
    result,
    playerMaxLineWidth <= CAPTION_DISPLAY_LINE_MAX_WIDTH_PX,
    "player.no_estimated_caption_line_cutoff",
    `precomputed caption display lines must fit the ${CAPTION_DISPLAY_LINE_MAX_WIDTH_PX}px budget; found ${playerMaxLineWidth}`,
  );
  check(
    result,
    Number(injectedConfig.captionStackHeightPx) >= 12000 &&
      /captionStackHeightPx/i.test(injectionBlock) &&
      /captionStackPaintContainmentRead/i.test(injectionBlock),
    "player.caption_stack_full_timeline_height_config",
    "player must embed the full-timeline caption stack height and paint-containment QA read",
  );
  check(
    result,
    !/contain\s*:[^;}]*\bpaint\b/i.test(stackCssBlock),
    "player.caption_stack_no_paint_containment",
    "caption stack must not use CSS paint containment; it can clip late-runtime right-rail captions even when DOM state says they are visible",
  );
  check(
    result,
    /right:\s*12px/i.test(injectionBlock) &&
      /top:\s*72px/i.test(injectionBlock) &&
      /width:\s*488px/i.test(injectionBlock) &&
      /height:\s*844px/i.test(injectionBlock),
    "player.caption_window_tall_right_biased_geometry",
    "injected caption window must be 488x844 at rail top 72/right 12",
  );
  check(
    result,
    !/\.ce-caption-line\.is-active|\.ce-caption-line\.is-near|\.ce-caption-line\.is-far|classList\.toggle\("is-active"|classList\.toggle\("is-near"|classList\.toggle\("is-far"/i.test(injectionBlock),
    "player.no_class_based_caption_opacity",
    "caption opacity must be numeric/continuous, not class-toggled active/near/far",
  );
  check(
    result,
    /lineOpacityAt\(/i.test(injectionBlock) && /\.style\.opacity\s*=\s*opacity\.toFixed/i.test(injectionBlock),
    "player.numeric_caption_opacity",
    "caption lines must receive per-frame numeric opacity",
  );
  check(
    result,
    /scrollPositionAt\(time\)/i.test(injectionBlock) &&
      /captionScrollStartPositionPx/i.test(injectionBlock) &&
      /captionConstantScrollSpeedPxPerSecond/i.test(injectionBlock) &&
      !/smoothstep\(/i.test(scrollFunctionBlock) &&
      !/chunkAnchorTime\(/i.test(scrollFunctionBlock) &&
      !/CE_CHUNKS\.length\s*-\s*1/i.test(scrollFunctionBlock),
    "player.constant_speed_scroll_model",
    "scrollPositionAt must be one linear function of audio time, not cue-to-cue smoothstep interpolation",
  );
  check(
    result,
    !/phraseForCue|wrapPhrase|is-active/i.test(injectionBlock),
    "player.no_active_sentence_highlight_path",
    "injected rail must not use the old active cue/whole phrase wrapping path",
  );
  if (/const aircraftEvents = \[/i.test(html)) {
    const aircraftStats = aircraftRouteStatsFromHtml(html);
    check(
      result,
      aircraftStats.aircraftRightRailCutoffRemoved,
      "player.aircraft_right_rail_cutoff_removed",
      "aircraft drawing/debug must not suppress states at railSafeLeft - 50",
    );
    check(
      result,
      aircraftStats.rightRailRoutes.length >= 1,
      "player.aircraft_right_rail_route_enters_rail",
      `at least one pre-end-screen aircraft route must enter x >= ${RIGHT_RAIL_LEFT_X}; found ${aircraftStats.rightRailRoutes.length}`,
    );
    check(
      result,
      html.includes(AMBIENT_RIGHT_RAIL_MOTION_POLICY),
      "player.ambient_right_rail_motion_policy",
      "player must expose ambient_motion_allowed_under_rail_text_v1",
    );
    check(
      result,
      html.includes(FOREGROUND_MATTE_POLICY),
      "player.foreground_matte_policy",
      "player must preserve tower/shuttle-only foreground matte policy",
    );
    check(
      result,
      /endScreenAmbientSafeStart|aircraft_safe_window_suppression_start_seconds|safeWindowSuppressed/i.test(html),
      "player.aircraft_safe_window_suppression",
      "aircraft motion must be suppressible during the YouTube target safe window",
    );
  }
  check(
    result,
    !/\.ce-caption(?:-window|-stack|-line)[\s\S]{0,260}animation\s*:/i.test(injectionBlock),
    "player.no_free_running_caption_animation",
    "avoid CSS animation-driven caption scroll",
  );
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const manifestPath = path.resolve(args.proofManifest);
  const playerPath = args.player ? path.resolve(args.player) : "";
  const manifest = readJson(manifestPath);
  const result = {
    manifest_path: manifestPath,
    player_path: playerPath || null,
    checks: [],
    failures: [],
    passed: false,
  };
  validateManifest(manifest, result, manifestPath);
  if (playerPath) validatePlayer(playerPath, result, manifest);
  result.passed = result.failures.length === 0;

  if (args.json) {
    console.log(JSON.stringify(result, null, 2));
  } else if (result.passed) {
    console.log(`PASS rolling caption rail validation: ${manifestPath}`);
  } else {
    console.error(`FAIL rolling caption rail validation: ${manifestPath}`);
    for (const failure of result.failures) console.error(`- ${failure}`);
  }
  process.exit(result.passed ? 0 : 1);
}

main();
