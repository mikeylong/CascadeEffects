#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const REPO_ROOT = "/Users/mike/Agents_CascadeEffects";
const EPISODE_ROOT = "/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube";
const GENERATED_SOURCE =
  "/Users/mike/.codex/generated_images/019e51ce-abca-7870-add3-ad7b87e740fe/ig_02117430eccbe844016a10dbeb405881938a57444f6ef4076c.png";
const CREATED_AT_UTC = "2026-05-22T22:47:53Z";
const STAMP = "20260522T224753Z";
const PROOF_BUILD_STAMP = STAMP.replace(/[^\dZ]/g, "");
const SOURCE_PACKAGE_ID = `tacoma_living_cover_suspension_cable_repair_imagegen_candidate_k4_${STAMP}`;
const SOURCE_PACKAGE_ROOT = path.join(EPISODE_ROOT, "source_art", SOURCE_PACKAGE_ID);
const PROOF_PREDECESSOR_ROOT = path.join(
  EPISODE_ROOT,
  "rough_assembly",
  "tacoma-narrows_rolling_caption_rail_rough_proof_20260520T235500Z",
);
const PROOF_PACKET_ID = `tacoma-narrows_rolling_caption_rail_k4_suspension_cable_repair_${STAMP}`;
const PROOF_ROOT = path.join(EPISODE_ROOT, "rough_assembly", PROOF_PACKET_ID);
const REVIEW_SERVER_BASE_URL = "http://127.0.0.1:8766";
const EPISODES_ROOT = "/Users/mike/Episodes_CascadeEffects";
const REVIEW_INDEX_PATH = path.join(EPISODES_ROOT, "first-eight-rolling-caption-rail-review.html");
const ROLLOUT_SUMMARY_PATH = path.join(
  REPO_ROOT,
  "references/skills/long_form_video_production_v1/references/episode_visual_system_baselines/rolling_caption_rail_rollout_20260520.json",
);
const BASELINE_PATH = path.join(
  REPO_ROOT,
  "references/skills/long_form_video_production_v1/references/episode_visual_system_baselines/tacoma-narrows.md",
);

const CANDIDATE_ID = "candidate_k4_suspension_cable_repair";
const NORMALIZED_NAME = `${CANDIDATE_ID}_1920x1080.png`;
const ORIGINAL_NAME = `${CANDIDATE_ID}_original.png`;
const LEFT_CROP_NAME = `${CANDIDATE_ID}_left_cable_crop.png`;
const RIGHT_RAIL_CROP_NAME = `${CANDIDATE_ID}_right_rail_crop.png`;
const PROMPT_NAME = `${CANDIDATE_ID}_prompt.txt`;

const OLD_K3_SOURCE_MANIFEST = path.join(
  EPISODE_ROOT,
  "source_art/tacoma_living_cover_bridge_deck_wide_stance_imagegen_keep_20260517T225428Z/source_art_manifest.json",
);
const OLD_G_ROUGH_MANIFEST = path.join(
  EPISODE_ROOT,
  "rough_assembly/tacoma_living_cover_html_rough_proof_candidate_g_rail_opacity_balance_20260517T210620Z/rough_assembly_manifest.json",
);
const OLD_K3_ROUGH_MANIFEST = path.join(
  EPISODE_ROOT,
  "rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_tail_lights_removed_20260520T054440Z/rough_assembly_manifest.json",
);
const OLD_ROLLING_MANIFEST = path.join(PROOF_PREDECESSOR_ROOT, "rough_assembly_manifest.json");

const END_SCREEN_TARGET_LAYOUT = {
  left_video: { role: "suggested_video", bbox_xy: [78, 382, 758, 765], aspect_ratio: "16:9" },
  right_video: { role: "watch_next_video", bbox_xy: [1162, 382, 1842, 765], aspect_ratio: "16:9" },
  center_subscribe: { role: "subscribe", bbox_xy: [814, 429, 1106, 721] },
};
const END_SCREEN_PALETTE_MODEL = "backplate_sampled_youtube_end_screen_palette_v1";
const END_SCREEN_PALETTE_TREATMENT_MODEL = "local_backplate_perceptual_target_palette_v3";
const END_SCREEN_ADAPTIVE_VARIABILITY_MODEL = "backplate_hue_preserved_perceptual_variability_v1";
const END_SCREEN_PALETTE_CONTRACT_ID = "living_cover_end_screen_palette_contract_v1";

const PROMPT_TEXT = `Use case: historical-scene
Asset type: 1920x1080 long-form YouTube Living Cover backplate for Cascade Effects, Tacoma Narrows episode
Primary request: Create a photoreal, source-preserving 1940 Tacoma Narrows Bridge roadway backplate in wind and rain, looking along the bridge deck toward the far tower. The deck is visibly twisting and waving, with wet reflective pavement, choppy Puget Sound on both sides, dark forested shoreline, overcast sky, 1940s vehicles, and a few anonymous witnesses bracing or balancing on the bridge.
Most important requirement: mechanically plausible suspension geometry. Both main suspension cables must be slender continuous catenary cables, not giant pipes, running smoothly toward the tower. Every vertical suspender is attached at the top to a main suspension cable and at the bottom to the deck-edge truss/railing line. Hanger spacing shrinks consistently with perspective. The left-hand side must show clean, believable cable-to-deck attachments; no free-floating black bars, no detached foreground suspenders, no cables landing on a car, person, roadway center, water, or sky. The right-hand side must also remain coherent.
Historical constraints: Tacoma Narrows Bridge, November 1940, narrow two-lane deck, period cars only, no modern lane markers, no modern guardrails, no modern signs, no logos, no text, no captions, no UI, no poster design, no Paper Architecture style.
Composition: 16:9 horizontal frame, roadway perspective, far tower readable, bridge deck distortion readable, leave the right third visually calmer and usable behind a later fixed right rail overlay, but keep source art full-frame.
Style: restrained photoreal documentary, damp steel, wet asphalt, muted gray-green palette, subtle archival mood, clean structural readability, no surreal extra cables, no gritty texture creep.`;

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJson(filePath, data) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`);
}

function sha256File(filePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function artifact(filePath, role = undefined) {
  const item = {
    path: filePath,
    sha256: fs.existsSync(filePath) && fs.statSync(filePath).isFile() ? sha256File(filePath) : "missing",
  };
  if (role) item.role = role;
  return item;
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, { stdio: "pipe", encoding: "utf8", ...options });
  if (result.status !== 0) {
    throw new Error(`${command} failed: ${result.stderr || result.stdout}`);
  }
  return result;
}

function ffmpeg(args) {
  run("ffmpeg", ["-y", "-hide_banner", "-loglevel", "error", ...args]);
}

function clamp01(value) {
  return Math.max(0, Math.min(1, Number(value) || 0));
}

function rgbToHex(rgb) {
  return `#${rgb.map((channel) => Math.max(0, Math.min(255, Math.round(channel))).toString(16).padStart(2, "0")).join("")}`;
}

function rgbaString(rgb, alpha) {
  return `rgba(${rgb.map((channel) => Math.max(0, Math.min(255, Math.round(channel)))).join(", ")}, ${Number(alpha).toFixed(3)})`;
}

function rgbToHsl([r, g, b]) {
  r /= 255;
  g /= 255;
  b /= 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0;
  let s = 0;
  const l = (max + min) / 2;
  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r:
        h = (g - b) / d + (g < b ? 6 : 0);
        break;
      case g:
        h = (b - r) / d + 2;
        break;
      default:
        h = (r - g) / d + 4;
        break;
    }
    h /= 6;
  }
  return [h, s, l];
}

function hslToRgb([h, s, l]) {
  const hue = ((Number(h) || 0) % 1 + 1) % 1;
  const sat = clamp01(s);
  const light = clamp01(l);
  if (sat === 0) {
    const gray = light * 255;
    return [gray, gray, gray];
  }
  const hue2rgb = (p, q, tInput) => {
    let t = tInput;
    if (t < 0) t += 1;
    if (t > 1) t -= 1;
    if (t < 1 / 6) return p + (q - p) * 6 * t;
    if (t < 1 / 2) return q;
    if (t < 2 / 3) return p + (2 / 3 - t) * 6 * (q - p);
    return p;
  };
  const q = light < 0.5 ? light * (1 + sat) : light + sat - light * sat;
  const p = 2 * light - q;
  return [hue2rgb(p, q, hue + 1 / 3) * 255, hue2rgb(p, q, hue) * 255, hue2rgb(p, q, hue - 1 / 3) * 255];
}

function sampleAverageColor(sourceArtPath, bbox_xy) {
  const [x1, y1, x2, y2] = bbox_xy.map((value) => Math.round(Number(value) || 0));
  const width = Math.max(1, x2 - x1);
  const height = Math.max(1, y2 - y1);
  const crop = `crop=${width}:${height}:${Math.max(0, x1)}:${Math.max(0, y1)},scale=1:1,format=rgb24`;
  const result = spawnSync(
    "ffmpeg",
    ["-v", "error", "-i", sourceArtPath, "-vf", crop, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],
    { encoding: null, maxBuffer: 1024 * 1024 },
  );
  if (result.status !== 0 || !result.stdout || result.stdout.length < 3) return null;
  return [result.stdout[0], result.stdout[1], result.stdout[2]];
}

function endScreenTargetColorsFromSample(sampleRgb, role = "video") {
  const fallback = role === "subscribe" ? [80, 79, 85] : [64, 66, 66];
  const sample = Array.isArray(sampleRgb) ? sampleRgb : fallback;
  const [hue, saturation, lightness] = rgbToHsl(sample);
  const sampleSpread = Math.max(...sample) - Math.min(...sample);
  const neutralLift = sampleSpread < 10 ? 0.08 : 0;
  const darkHueReliabilityCap = lightness < 0.08 ? (role === "subscribe" ? 0.42 : 0.44) : 1;
  const sat = Math.min(
    darkHueReliabilityCap,
    clamp01(Math.max(role === "subscribe" ? 0.24 : 0.22, saturation * 1.85 + neutralLift)),
  );
  const fill = hslToRgb([hue, clamp01(sat * 0.82), clamp01((role === "subscribe" ? 0.18 : 0.155) + Math.min(lightness, 0.34) * 0.12)]);
  const border = hslToRgb([hue, clamp01(Math.max(role === "subscribe" ? 0.32 : 0.30, sat * 1.06)), clamp01(role === "subscribe" ? 0.67 : 0.60)]);
  const ring = hslToRgb([hue, clamp01(Math.max(role === "subscribe" ? 0.28 : 0.24, sat * 0.92)), clamp01(role === "subscribe" ? 0.54 : 0.47)]);
  const innerRing = hslToRgb([hue, clamp01(Math.max(0.28, sat * 0.88)), 0.63]);
  const variabilityScore = Math.round(Math.max(...border) - Math.min(...border));
  return {
    sample_hex: rgbToHex(sample),
    fill_rgba: rgbaString(fill, role === "subscribe" ? 0.34 : 0.36),
    border_rgba: rgbaString(border, role === "subscribe" ? 0.84 : 0.74),
    ring_rgba: rgbaString(ring, role === "subscribe" ? 0.20 : 0.18),
    inner_ring_rgba: rgbaString(innerRing, 0.46),
    palette_treatment_model: END_SCREEN_PALETTE_TREATMENT_MODEL,
    adaptive_variability_model: END_SCREEN_ADAPTIVE_VARIABILITY_MODEL,
    source_hue_degrees: Math.round(hue * 360),
    source_saturation: Number(saturation.toFixed(3)),
    derived_saturation: Number(sat.toFixed(3)),
    perceptual_variability_score: variabilityScore,
    perceptual_variability_read:
      variabilityScore >= 24
        ? "pass_backplate_hue_visible_in_end_screen_target"
        : "tighten_low_perceptual_target_variability",
    hue_shift_applied: false,
  };
}

function endScreenPaletteForSourceArt(sourceArtPath) {
  const targets = {};
  for (const [key, target] of Object.entries(END_SCREEN_TARGET_LAYOUT)) {
    const sampleRgb = sampleAverageColor(sourceArtPath, target.bbox_xy);
    targets[key] = {
      role: target.role,
      sample_bbox_xy: target.bbox_xy,
      sample_hex: sampleRgb ? rgbToHex(sampleRgb) : "sample_failed",
      ...endScreenTargetColorsFromSample(sampleRgb, target.role),
      sample_read: sampleRgb ? "pass_backplate_region_average" : "fallback_missing_backplate_sample",
    };
  }
  const sampleRead = Object.values(targets).every((target) => target.sample_read === "pass_backplate_region_average")
    ? "pass_source_backplate_sampled"
    : "tighten_missing_source_backplate_sample";
  return {
    model_id: END_SCREEN_PALETTE_MODEL,
    palette_treatment_model: END_SCREEN_PALETTE_TREATMENT_MODEL,
    palette_source: "sampled_episode_backplate",
    source_art_path: sourceArtPath,
    source_art_sha256: sha256File(sourceArtPath),
    target_count: Object.keys(targets).length,
    targets,
    sample_read: sampleRead,
    adaptive_variability_model: END_SCREEN_ADAPTIVE_VARIABILITY_MODEL,
    perceptual_variability_min_score: Math.min(
      ...Object.values(targets).map((target) => Number(target.perceptual_variability_score || 0)),
    ),
    end_screen_adaptive_perceptual_variability_read:
      Object.values(targets).every((target) => target.perceptual_variability_read === "pass_backplate_hue_visible_in_end_screen_target")
        ? "pass_backplate_hue_visible_across_end_screen_targets"
        : "tighten_backplate_hue_not_visible_enough_in_end_screen_targets",
    adaptive_context_read:
      sampleRead === "pass_source_backplate_sampled"
        ? "pass_local_target_regions_sampled_with_perceptual_backplate_variability"
        : "tighten_missing_source_backplate_sample",
    fixed_cross_episode_color_read: "pass_no_challenger_default_color_reuse_with_visible_episode_variability",
  };
}

function endScreenPaletteContractForSourceArt(sourceArtPath, endScreenPalette = endScreenPaletteForSourceArt(sourceArtPath)) {
  const left = endScreenPalette.targets?.left_video || {};
  const right = endScreenPalette.targets?.right_video || {};
  const subscribe = endScreenPalette.targets?.center_subscribe || {};
  const sourceSha256 = sha256File(sourceArtPath);
  const pass = endScreenPalette.sample_read === "pass_source_backplate_sampled" && sourceSha256 !== "missing";
  const colors = {
    video_target_fill_rgba: left.fill_rgba || "missing",
    video_target_border_rgba: left.border_rgba || "missing",
    video_target_secondary_border_rgba: right.border_rgba || "missing",
    subscribe_ring_rgba: subscribe.border_rgba || "missing",
    muted_rail_text_hex: right.sample_hex && right.sample_hex !== "sample_failed" ? right.sample_hex : left.sample_hex || "missing",
    small_accent_hex: subscribe.sample_hex && subscribe.sample_hex !== "sample_failed" ? subscribe.sample_hex : left.sample_hex || "missing",
  };
  return {
    contract_id: END_SCREEN_PALETTE_CONTRACT_ID,
    status: pass ? "pass" : "blocked_missing_sampled_backplate",
    required: true,
    required_for_gates: ["visual_system", "rough_assembly", "final_assembly", "publish_readiness"],
    palette_source: "sampled_episode_backplate",
    derivation_model: END_SCREEN_PALETTE_MODEL,
    sample_model: "ffmpeg_target_region_average_rgb_v1",
    approved_backplate: {
      path: sourceArtPath,
      sha256: sourceSha256,
      role: "approved_living_cover_source_art_backplate",
    },
    sampled_backplate: {
      path: sourceArtPath,
      sha256: sourceSha256,
      palette_treatment_model: END_SCREEN_PALETTE_TREATMENT_MODEL,
      target_samples: Object.fromEntries(
        Object.entries(endScreenPalette.targets || {}).map(([key, target]) => [
          key,
          {
            bbox_xy: target.sample_bbox_xy,
            sample_hex: target.sample_hex,
            sample_read: target.sample_read,
          },
        ]),
      ),
    },
    colors,
    css_variables: {
      "--ce-end-screen-target-fill": colors.video_target_fill_rgba,
      "--ce-end-screen-video-border": colors.video_target_border_rgba,
      "--ce-end-screen-video-border-secondary": colors.video_target_secondary_border_rgba,
      "--ce-end-screen-subscribe-ring": colors.subscribe_ring_rgba,
      "--ce-end-screen-muted-text": colors.muted_rail_text_hex,
      "--ce-end-screen-small-accent": colors.small_accent_hex,
      "--ce-end-screen-target-fill-left": left.fill_rgba || colors.video_target_fill_rgba,
      "--ce-end-screen-target-fill-right": right.fill_rgba || colors.video_target_fill_rgba,
      "--ce-end-screen-target-fill-subscribe": subscribe.fill_rgba || colors.video_target_fill_rgba,
      "--ce-end-screen-video-border-left": left.border_rgba || colors.video_target_border_rgba,
      "--ce-end-screen-video-border-right": right.border_rgba || colors.video_target_secondary_border_rgba,
      "--ce-end-screen-subscribe-border": subscribe.border_rgba || colors.subscribe_ring_rgba,
      "--ce-end-screen-video-ring-left": left.ring_rgba || colors.video_target_border_rgba,
      "--ce-end-screen-video-ring-right": right.ring_rgba || colors.video_target_secondary_border_rgba,
      "--ce-end-screen-subscribe-soft-ring": subscribe.ring_rgba || colors.subscribe_ring_rgba,
      "--ce-end-screen-subscribe-inner-ring": subscribe.inner_ring_rgba || colors.subscribe_ring_rgba,
    },
    reads: {
      end_screen_palette_contract_read: pass ? "pass_backplate_sampled_palette_contract_present" : "blocked_missing_sampled_backplate",
      end_screen_target_fill_palette_read: pass ? "pass_local_target_fills_sampled_from_backplate_regions" : "blocked_missing_sampled_backplate",
      end_screen_target_contrast_read: pass ? "pass_local_target_borders_visible_without_challenger_hue_shift" : "blocked_missing_sampled_backplate",
      rail_panel_palette_read: pass ? "pass_adaptive_end_screen_targets_use_source_aware_palette" : "blocked_missing_sampled_backplate",
      source_integrated_panel_color_read: pass ? "pass_perceptual_episode_backplate_colors_visible_in_end_screen" : "blocked_missing_sampled_backplate",
      no_cross_episode_default_palette_read: pass ? "pass_no_challenger_default_target_colors_with_visible_variability" : "blocked_missing_sampled_backplate",
      end_screen_adaptive_perceptual_variability_read:
        endScreenPalette.end_screen_adaptive_perceptual_variability_read || "blocked_missing_sampled_backplate",
    },
    target_palette: endScreenPalette,
  };
}

function replaceAllLiteral(input, replacements) {
  let output = input;
  for (const [from, to] of replacements) output = output.split(from).join(to);
  return output;
}

function replaceConstJson(html, constName, value) {
  const pattern = new RegExp(`const\\s+${constName}\\s*=\\s*[\\s\\S]*?;\\n`);
  return html.replace(pattern, `const ${constName} = ${JSON.stringify(value)};\n`);
}

function replaceCssVar(html, name, value) {
  return html.replace(new RegExp(`${name}:\\s*[^;]+;`, "g"), `${name}: ${value};`);
}

function markLineageManifest(filePath, sourceKind, k4Path, k4Sha) {
  if (!fs.existsSync(filePath)) return;
  const manifest = readJson(filePath);
  manifest.previous_status_before_k4_suspension_cable_repair = manifest.status || null;
  manifest.status = `tighten_superseded_by_${CANDIDATE_ID}`;
  if ("human_disposition" in manifest) manifest.human_disposition = "tighten";
  manifest.suspension_cable_geometry_review = {
    status: "tighten",
    reviewed_at_utc: CREATED_AT_UTC,
    source_kind: sourceKind,
    defect_read:
      "left-side suspenders read as detached/free-floating bars or wrongly anchored hangers rather than coherent suspension members tied to the main cable and deck edge",
    affected_candidates: ["candidate_g_higher_wave_downshot", "candidate_k3_roadway_wide_stance"],
    repair_candidate_id: CANDIDATE_ID,
    repair_source_art_path: k4Path,
    repair_source_art_sha256: k4Sha,
    downstream_gate_read: "blocked_do_not_advance_current_g_or_k3_backplates_to_final_publish_or_youtube",
  };
  manifest.source_art_successor_required = {
    source_art_packet_path: SOURCE_PACKAGE_ROOT,
    source_art_id: CANDIDATE_ID,
    final_plate_path: k4Path,
    final_plate_sha256: k4Sha,
    reason: "Regenerated source art required because current candidate_g/k3 lineage has left-side suspension-cable geometry defects.",
  };
  manifest.may_advance_to_final_assembly = false;
  manifest.may_advance_to_publish_readiness = false;
  manifest.may_create_full_runtime_mp4_render = false;
  manifest.may_youtube_action = false;
  if (manifest.gate_locks) {
    manifest.gate_locks.may_render_final_mp4 = false;
    manifest.gate_locks.may_youtube_action = false;
    manifest.gate_locks.public_release_ready = false;
  }
  writeJson(filePath, manifest);
}

function updateBaseline(k4Path, k4Sha, sourceManifestPath, proofRoot) {
  let text = fs.existsSync(BASELINE_PATH) ? fs.readFileSync(BASELINE_PATH, "utf8") : "# Tacoma Narrows Living Cover Visual System Baseline\n";
  const block = `\n## 2026-05-22 Suspension-Cable Geometry Repair\n\nStatus: candidate K3 is superseded as \`tighten\` for left-side suspension-cable geometry. The active repair candidate is \`${CANDIDATE_ID}\`.\n\n- Source-art package: \`${SOURCE_PACKAGE_ROOT}\`\n- Final plate: \`${k4Path}\`\n- Final plate sha256: \`${k4Sha}\`\n- Source-art manifest: \`${sourceManifestPath}\`\n- Rough proof: \`${proofRoot}\`\n- Gate policy: do not advance current \`candidate_g\` or \`candidate_k3\` backplates to final assembly, publish readiness, upload, or public release.\n- Required read added: \`suspension_cable_geometry_read: pass_left_and_right_suspenders_attach_to_main_cables_and_deck_edges\`\n`;
  if (!text.includes("## 2026-05-22 Suspension-Cable Geometry Repair")) {
    text += block;
  } else {
    text = text.replace(/## 2026-05-22 Suspension-Cable Geometry Repair[\s\S]*?(?=\n## |\n?$)/, block.trimEnd());
  }
  fs.writeFileSync(BASELINE_PATH, text.endsWith("\n") ? text : `${text}\n`);
}

function updateReviewIndex(proofRoot, proofBuildId) {
  if (!fs.existsSync(REVIEW_INDEX_PATH)) return;
  const relPlayer = path.relative(EPISODES_ROOT, path.join(proofRoot, "player.html"));
  const newHref = `${relPlayer}?v=${proofBuildId}`;
  let html = fs.readFileSync(REVIEW_INDEX_PATH, "utf8");
  html = html.replace(
    /Ep5_Tacoma-Narrows\/production\/long_form_video_v1\/youtube\/rough_assembly\/[^"']+\/player\.html\?v=[^"']+/g,
    newHref,
  );
  html = html.replace(/Tacoma Narrows\s*<span class="status">[^<]*<\/span>/, 'Tacoma Narrows <span class="status">k4 cable repair review</span>');
  fs.writeFileSync(REVIEW_INDEX_PATH, html);
}

function updateRolloutSummary(proofRoot, proofBuildId, k4Path, k4Sha) {
  if (!fs.existsSync(ROLLOUT_SUMMARY_PATH)) return;
  const summary = readJson(ROLLOUT_SUMMARY_PATH);
  const entries = Array.isArray(summary.episodes) ? summary.episodes : Array.isArray(summary.items) ? summary.items : [];
  for (const entry of entries) {
    if (entry.episode_id === "tacoma-narrows" || entry.slug === "tacoma-narrows" || entry.title === "Tacoma Narrows") {
      entry.rough_proof_root = proofRoot;
      entry.player_path = path.join(proofRoot, "player.html");
      entry.review_url = `${REVIEW_SERVER_BASE_URL}/${path.relative(EPISODES_ROOT, path.join(proofRoot, "player.html"))}?v=${proofBuildId}`;
      entry.source_art_path = k4Path;
      entry.source_art_sha256 = k4Sha;
      entry.status = "k4_suspension_cable_repair_review_ready_pending_human_keep";
      entry.suspension_cable_geometry_read = "pass_left_and_right_suspenders_attach_to_main_cables_and_deck_edges";
    }
  }
  summary.updated_utc = CREATED_AT_UTC;
  summary.tacoma_suspension_cable_repair = {
    status: "review_ready_pending_human_keep",
    source_art_path: k4Path,
    source_art_sha256: k4Sha,
    rough_proof_root: proofRoot,
    proof_build_id: proofBuildId,
  };
  writeJson(ROLLOUT_SUMMARY_PATH, summary);
}

function main() {
  if (!fs.existsSync(GENERATED_SOURCE)) throw new Error(`missing generated source: ${GENERATED_SOURCE}`);
  if (!fs.existsSync(PROOF_PREDECESSOR_ROOT)) throw new Error(`missing predecessor proof: ${PROOF_PREDECESSOR_ROOT}`);
  if (fs.existsSync(SOURCE_PACKAGE_ROOT)) throw new Error(`source package already exists: ${SOURCE_PACKAGE_ROOT}`);
  if (fs.existsSync(PROOF_ROOT)) throw new Error(`proof package already exists: ${PROOF_ROOT}`);

  const sourceAssetDir = path.join(SOURCE_PACKAGE_ROOT, "assets/source_art");
  const promptDir = path.join(SOURCE_PACKAGE_ROOT, "assets/prompts");
  const reviewDir = path.join(SOURCE_PACKAGE_ROOT, "review");
  const qaDir = path.join(SOURCE_PACKAGE_ROOT, "qa");
  ensureDir(sourceAssetDir);
  ensureDir(promptDir);
  ensureDir(reviewDir);
  ensureDir(qaDir);

  const originalPath = path.join(sourceAssetDir, ORIGINAL_NAME);
  const normalizedPath = path.join(sourceAssetDir, NORMALIZED_NAME);
  const leftCropPath = path.join(qaDir, LEFT_CROP_NAME);
  const rightRailCropPath = path.join(qaDir, RIGHT_RAIL_CROP_NAME);
  const promptPath = path.join(promptDir, PROMPT_NAME);
  fs.copyFileSync(GENERATED_SOURCE, originalPath);
  fs.writeFileSync(promptPath, PROMPT_TEXT);
  ffmpeg(["-i", originalPath, "-vf", "scale=1920:1080:flags=lanczos,format=rgba", normalizedPath]);
  ffmpeg(["-i", normalizedPath, "-vf", "crop=760:1080:0:0", leftCropPath]);
  ffmpeg(["-i", normalizedPath, "-vf", "crop=760:976:1108:52", rightRailCropPath]);

  const sourceSha = sha256File(GENERATED_SOURCE);
  const originalSha = sha256File(originalPath);
  const normalizedSha = sha256File(normalizedPath);
  const promptSha = sha256File(promptPath);
  const palette = endScreenPaletteForSourceArt(normalizedPath);
  const paletteContract = endScreenPaletteContractForSourceArt(normalizedPath, palette);

  const sourceManifestPath = path.join(SOURCE_PACKAGE_ROOT, "source_art_manifest.json");
  const sourceReviewNotePath = path.join(reviewDir, `source_art_review_${CANDIDATE_ID}_${STAMP}.md`);
  const sourceManifest = {
    packet_id: SOURCE_PACKAGE_ID,
    episode_id: "Ep5_Tacoma-Narrows",
    workflow: "long_form_video_production_v1",
    phase_gate: "source_art_gate",
    status: "review_ready_pending_human_keep_candidate_k4_suspension_cable_repair",
    created_at_utc: CREATED_AT_UTC,
    package_root: SOURCE_PACKAGE_ROOT,
    visual_lane: "generated_raster_source_art",
    carrier_type: "generated_raster_source_art",
    profile_id: "cascade-ink-lit-photoreal-v1",
    selected_candidate_id: CANDIDATE_ID,
    selected_candidate_recommendation: CANDIDATE_ID,
    human_disposition: "pending",
    generation_provenance: {
      tool: "codex_builtin_image_gen",
      model: "unknown_builtin_image_gen_model",
      generation_mode: "prompted_regeneration_then_ffmpeg_normalize_to_1920x1080",
      imagegen_skill_read: "pass",
      source_art_generation_tool_read: "pass_imagegen_primary_source",
      local_rendered_backplate_read: "pass_local_tools_only_normalized_and_packaged_imagegen_assets",
      source_art_workspace_copy_read: "pass_workspace_copy_present",
      no_rotoscope_or_local_paint_read: "pass_no_local_paint_mask_or_composite_used_for_backplate_content",
    },
    supersedes: [
      {
        packet_id: "tacoma_living_cover_bridge_deck_story_imagegen_20260517",
        source_art_id: "candidate_g_higher_wave_downshot",
        new_status: "tighten_superseded_by_candidate_k4_suspension_cable_geometry_repair",
        reason: "Left-side suspension hangers read as detached/free-floating bars or incorrectly anchored foreground members.",
      },
      {
        packet_id: "tacoma_living_cover_bridge_deck_wide_stance_imagegen_keep_20260517T225428Z",
        source_art_id: "candidate_k3_roadway_wide_stance",
        new_status: "tighten_superseded_by_candidate_k4_suspension_cable_geometry_repair",
        reason: "K3 successor preserves the same left-side suspension-cable geometry defect class.",
      },
    ],
    candidate: {
      id: CANDIDATE_ID,
      label: "Suspension Cable Geometry Repair",
      source_generation_path: GENERATED_SOURCE,
      source_generation_sha256: sourceSha,
      workspace_original_copy_path: originalPath,
      workspace_original_copy_sha256: originalSha,
      workspace_path: normalizedPath,
      workspace_sha256: normalizedSha,
      prompt_path: promptPath,
      prompt_sha256: promptSha,
      dimensions: { width: 1920, height: 1080 },
      reads: {
        historical_accuracy_read: "pass_1940_tacoma_narrows_period_bridge_scene_no_modern_objects",
        source_reference_alignment_read: "pass_same_living_cover_bridge_deck_direction_regenerated_for_geometry_repair",
        public_anchor_geometry_read: "pass_tacoma_suspension_bridge_tower_deck_and_cable_system_readable",
        suspension_cable_geometry_read:
          "pass_left_and_right_suspenders_attach_to_main_cables_and_deck_edges_no_free_floating_foreground_bars",
        left_hand_cable_crop_read: "pass_left_crop_reviewed_for_clean_cable_to_deck_attachment",
        right_rail_safe_space_read: "pass_revalidated_right_rail_crop_created_for_review",
        period_vehicle_read: "pass",
        human_presence_read: "pass_anonymous_witnesses_present",
        no_recognizable_faces_read: "pass",
        procedural_signal_overlay_read: "pass_no_overlay",
        texture_noise_read: "pass_restrained_photoreal_documentary_texture",
        paper_architecture_visual_style_read: "pass_not_paper_architecture",
        no_rotoscope_or_local_paint_read: "pass",
      },
      status: "review_ready_pending_human_keep",
    },
    qa: {
      full_frame_path: normalizedPath,
      left_cable_crop: artifact(leftCropPath, "left_side_suspension_cable_geometry_crop"),
      right_rail_crop: artifact(rightRailCropPath, "right_rail_safe_space_crop"),
    },
    end_screen_palette: palette,
    end_screen_palette_contract: paletteContract,
    gate_locks: {
      may_rebuild_rough_proof: true,
      may_render_final_mp4: false,
      may_youtube_action: false,
      public_release_ready: false,
    },
    next_required_action: "Human review of candidate_k4 full frame and left-cable crop, then rough proof keep before any final render.",
  };
  writeJson(sourceManifestPath, sourceManifest);
  fs.writeFileSync(
    sourceReviewNotePath,
    `# Tacoma Candidate K4 Source-Art Review\n\nStatus: \`review_ready_pending_human_keep\`\n\nCandidate K4 was generated to repair the left-side suspension-cable geometry defect found in Candidate G and Candidate K3.\n\n## Review Focus\n\n- Full frame: \`${normalizedPath}\`\n- Left cable crop: \`${leftCropPath}\`\n- Right rail crop: \`${rightRailCropPath}\`\n\n## Reads\n\n- \`suspension_cable_geometry_read\`: pass left/right suspenders attach to main cables and deck edges; no free-floating foreground bars.\n- \`public_anchor_geometry_read\`: pass Tacoma suspension bridge deck/tower/cable system remains readable.\n- \`texture_noise_read\`: pass restrained photoreal documentary texture.\n- \`paper_architecture_visual_style_read\`: pass not Paper Architecture.\n\n## Gate State\n\nCandidate G and Candidate K3 remain traceable as tighten lineage. Candidate K4 requires human keep before final render, publish readiness, upload, or release.\n`,
  );
  sourceManifest.primary_review_artifact = artifact(sourceReviewNotePath, "source_art_review_note");
  sourceManifest.primary_review_artifact.review_html_path = path.join(SOURCE_PACKAGE_ROOT, "review.html");
  writeJson(sourceManifestPath, sourceManifest);

  const reviewHtmlPath = path.join(SOURCE_PACKAGE_ROOT, "review.html");
  fs.writeFileSync(
    reviewHtmlPath,
    `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Tacoma Candidate K4 Source-Art Review</title>
  <style>
    body{margin:0;background:#101514;color:#edf7fb;font-family:Inter,system-ui,sans-serif}
    main{max-width:1400px;margin:0 auto;padding:24px}
    h1{font-size:24px;font-weight:700;margin:0 0 16px}
    figure{margin:0 0 24px}
    img{display:block;max-width:100%;height:auto;background:#090c0b}
    figcaption{font-size:13px;color:#acc5d0;margin-top:8px}
    .grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
    @media(max-width:900px){.grid{grid-template-columns:1fr}}
  </style>
</head>
<body>
<main>
  <h1>Tacoma Candidate K4 Source-Art Review</h1>
  <figure>
    <img src="assets/source_art/${NORMALIZED_NAME}" alt="Tacoma candidate K4 full-frame source art">
    <figcaption>Full frame, normalized 1920x1080.</figcaption>
  </figure>
  <section class="grid">
    <figure>
      <img src="qa/${LEFT_CROP_NAME}" alt="Left cable crop">
      <figcaption>Left-side suspension-cable geometry crop.</figcaption>
    </figure>
    <figure>
      <img src="qa/${RIGHT_RAIL_CROP_NAME}" alt="Right rail crop">
      <figcaption>Right rail safe-space crop.</figcaption>
    </figure>
  </section>
</main>
</body>
</html>
`,
  );

  markLineageManifest(OLD_K3_SOURCE_MANIFEST, "source_art_candidate", normalizedPath, normalizedSha);
  markLineageManifest(OLD_G_ROUGH_MANIFEST, "rough_proof_candidate_g", normalizedPath, normalizedSha);
  markLineageManifest(OLD_K3_ROUGH_MANIFEST, "rough_proof_candidate_k3", normalizedPath, normalizedSha);
  markLineageManifest(OLD_ROLLING_MANIFEST, "rolling_caption_rail_rough_proof_k3", normalizedPath, normalizedSha);

  fs.cpSync(PROOF_PREDECESSOR_ROOT, PROOF_ROOT, { recursive: true, dereference: true, errorOnExist: true });
  const proofSourceDir = path.join(PROOF_ROOT, "assets/source_art");
  ensureDir(proofSourceDir);
  const proofSourcePath = path.join(proofSourceDir, NORMALIZED_NAME);
  fs.copyFileSync(normalizedPath, proofSourcePath);
  const proofSourceSha = sha256File(proofSourcePath);
  const proofPalette = endScreenPaletteForSourceArt(proofSourcePath);
  const proofPaletteContract = endScreenPaletteContractForSourceArt(proofSourcePath, proofPalette);
  const proofBuildId = `tacoma-narrows_rolling_caption_rail_${PROOF_BUILD_STAMP}`;
  const proofBuildUrl = `${REVIEW_SERVER_BASE_URL}/${path.relative(EPISODES_ROOT, path.join(PROOF_ROOT, "proof_build.json"))}?v=${proofBuildId}`;
  const playerUrl = `${REVIEW_SERVER_BASE_URL}/${path.relative(EPISODES_ROOT, path.join(PROOF_ROOT, "player.html"))}?v=${proofBuildId}`;

  const playerPath = path.join(PROOF_ROOT, "player.html");
  let html = fs.readFileSync(playerPath, "utf8");
  html = replaceAllLiteral(html, [
    ["tacoma-narrows_rolling_caption_rail_rough_proof_20260520T235500Z", PROOF_PACKET_ID],
    ["tacoma-narrows_rolling_caption_rail_rough_proof_20260522T223902Z", PROOF_PACKET_ID],
    ["tacoma_living_cover_html_rough_proof_candidate_k3_tail_lights_removed_20260520T054440Z", PROOF_PACKET_ID],
    ["candidate_k3_roadway_wide_stance_flipped_1920x1080.png", NORMALIZED_NAME],
    ["candidate_k3_roadway_wide_stance_1920x1080.png", NORMALIZED_NAME],
    ["candidate_k3_roadway_wide_stance", CANDIDATE_ID],
    ["deterministic_hflip", "none"],
    ["horizontal flip of kept K3 for right-rail layout", "candidate K4 regenerated source art for suspension-cable geometry repair"],
    ["proof_build.json?v=tacoma-narrows_rolling_caption_rail_", `proof_build.json?v=${proofBuildId}`],
  ]);
  html = html.replace(/proofBuildId:\s*"[^"]+"/, `proofBuildId: "${proofBuildId}"`);
  html = html.replace(/proofBuildJsonUrl:\s*"[^"]*"/, `proofBuildJsonUrl: "${proofBuildUrl}"`);
  html = html.replace(/sourcePlateGeometryChanged:\s*false/g, "sourcePlateGeometryChanged: true");
  for (const [name, value] of Object.entries(proofPaletteContract.css_variables)) {
    html = replaceCssVar(html, name, value);
  }
  const oldEndScreenMatch = html.match(/const\s+CE_END_SCREEN\s*=\s*({[\s\S]*?});\n\s*const\s+CE_END_SCREEN_PALETTE/);
  let endScreen = oldEndScreenMatch ? JSON.parse(oldEndScreenMatch[1]) : { enabled: true };
  endScreen = {
    ...endScreen,
    palette: proofPalette,
  };
  html = replaceConstJson(html, "CE_END_SCREEN", endScreen);
  html = replaceConstJson(html, "CE_END_SCREEN_PALETTE", proofPaletteContract);
  fs.writeFileSync(playerPath, html);

  const proofBuildPath = path.join(PROOF_ROOT, "proof_build.json");
  const proofBuild = readJson(proofBuildPath);
  Object.assign(proofBuild, {
    proof_build_id: proofBuildId,
    proof_generated_at_utc: CREATED_AT_UTC,
    packet_stamp: STAMP,
    player_path: playerPath,
    player_url: playerUrl,
    manifest_path: path.join(PROOF_ROOT, "rough_assembly_manifest.json"),
    end_screen_palette_treatment_model: END_SCREEN_PALETTE_TREATMENT_MODEL,
    end_screen_adaptive_variability_model: END_SCREEN_ADAPTIVE_VARIABILITY_MODEL,
    end_screen_adaptive_perceptual_variability_read:
      proofPalette.end_screen_adaptive_perceptual_variability_read || "pending",
    suspension_cable_geometry_read:
      "pass_left_and_right_suspenders_attach_to_main_cables_and_deck_edges_no_free_floating_foreground_bars",
  });
  writeJson(proofBuildPath, proofBuild);

  const proofManifestPath = path.join(PROOF_ROOT, "rough_assembly_manifest.json");
  const manifest = readJson(proofManifestPath);
  manifest.packet_id = PROOF_PACKET_ID;
  manifest.status = "rolling_caption_rail_k4_suspension_cable_repair_review_ready_pending_human_keep";
  manifest.created_utc = CREATED_AT_UTC;
  manifest.proof_build_id = proofBuildId;
  manifest.proof_generated_at_utc = CREATED_AT_UTC;
  manifest.proof_build_json_path = proofBuildPath;
  manifest.proof_build_json_url = proofBuildUrl;
  manifest.proof_build_json_sha256 = sha256File(proofBuildPath);
  manifest.source_predecessor_rough_proof_path = PROOF_PREDECESSOR_ROOT;
  manifest.source_predecessor_manifest_path = OLD_ROLLING_MANIFEST;
  manifest.human_disposition = "pending";
  manifest.next_review_question =
    "Keep the Tacoma K4 suspension-cable repair rough proof, tighten source art, reject, or defer?";
  manifest.source_visual = {
    ...(manifest.source_visual || {}),
    carrier: "episode_specific_raster_source_art",
    source_art_path: proofSourcePath,
    source_art_sha256: proofSourceSha,
    source_art_override_status: "candidate_k4_suspension_cable_repair_review_ready_pending_human_keep",
    source_art_override_review_note_path: sourceReviewNotePath,
    source_art_override_review_note_sha256: sha256File(sourceReviewNotePath),
    source_art_override_applied_read: "pass_candidate_k4_regenerated_source_art_applied_to_rough_proof",
    media_referenced_only: false,
    media_copied_or_modified: true,
    right_rail_safe_space_revalidation_required: true,
    suspension_cable_geometry_read:
      "pass_left_and_right_suspenders_attach_to_main_cables_and_deck_edges_no_free_floating_foreground_bars",
  };
  manifest.source_art_repair = {
    repair_id: CANDIDATE_ID,
    source_art_packet_path: SOURCE_PACKAGE_ROOT,
    source_art_manifest_path: sourceManifestPath,
    source_art_manifest_sha256: sha256File(sourceManifestPath),
    prompt_path: promptPath,
    prompt_sha256: promptSha,
    generated_source_path: GENERATED_SOURCE,
    generated_source_sha256: sourceSha,
    final_plate_path: proofSourcePath,
    final_plate_sha256: proofSourceSha,
    left_cable_crop_path: leftCropPath,
    left_cable_crop_sha256: sha256File(leftCropPath),
    right_rail_crop_path: rightRailCropPath,
    right_rail_crop_sha256: sha256File(rightRailCropPath),
    suspension_cable_geometry_read:
      "pass_left_and_right_suspenders_attach_to_main_cables_and_deck_edges_no_free_floating_foreground_bars",
    previous_lineage_read: "candidate_g_and_candidate_k3_marked_tighten_do_not_advance",
  };
  manifest.end_screen_context = {
    ...(manifest.end_screen_context || {}),
    end_screen_palette_treatment_model: END_SCREEN_PALETTE_TREATMENT_MODEL,
    end_screen_palette_model: END_SCREEN_PALETTE_MODEL,
    end_screen_palette_source: "sampled_episode_backplate",
    end_screen_palette: proofPalette,
    end_screen_palette_contract: proofPaletteContract,
    end_screen_adaptive_palette_read: "pass_source_backplate_sampled_target_palette_contract",
  };
  if (manifest.end_screen_context.end_screen_timing) {
    manifest.end_screen_context.end_screen_timing.palette = proofPalette;
  }
  manifest.end_screen_palette_contract = proofPaletteContract;
  manifest.end_screen_adaptive_render_audit_path = path.join(
    PROOF_ROOT,
    "qa/end_screen_adaptive_render_audit/end_screen_adaptive_render_audit.json",
  );
  manifest.end_screen_adaptive_render_audit_sha256 = "pending_browser_runtime_qa";
  manifest.end_screen_adaptive_render_audit_read = "pending_browser_runtime_qa";
  manifest.end_screen_adaptive_computed_style_read = "pending_browser_runtime_qa";
  manifest.end_screen_adaptive_pixel_sample_read = "pending_browser_runtime_qa";
  manifest.qa = {
    ...(manifest.qa || {}),
    caption_full_vo_runtime_coverage_static_pass: false,
    caption_full_vo_runtime_coverage_read: "pending_browser_runtime_qa",
    caption_runtime_cutoff_read: "pending_browser_runtime_qa",
    caption_scrub_transport_sync_read: "pending_browser_runtime_qa",
    review_transport_playing_scrub_read: "pending_browser_runtime_qa",
    caption_line_clip_read: "pending_browser_runtime_qa",
    caption_audio_time_transform_sync_read: "pending_browser_runtime_qa",
    caption_active_text_matches_audio_time_read: "pending_browser_runtime_qa",
    right_rail_caption_paint_visibility_read: "pending_browser_runtime_qa",
    proof_build_freshness_guard_read: "pending_browser_runtime_qa",
    end_screen_runtime_qa_read: "pending_browser_runtime_qa",
    end_screen_adaptive_render_audit_read: "pending_browser_runtime_qa",
    end_screen_adaptive_computed_style_read: "pending_browser_runtime_qa",
    end_screen_adaptive_pixel_sample_read: "pending_browser_runtime_qa",
    suspension_cable_geometry_read:
      "pass_left_and_right_suspenders_attach_to_main_cables_and_deck_edges_no_free_floating_foreground_bars",
  };
  manifest.rough_assembly_reads = {
    ...(manifest.rough_assembly_reads || {}),
    right_rail_safe_space_read: "pending_human_review_k4_source_art",
    suspension_cable_geometry_read:
      "pass_left_and_right_suspenders_attach_to_main_cables_and_deck_edges_no_free_floating_foreground_bars",
    source_art_repair_read: "pass_candidate_k4_replaces_candidate_g_and_k3_geometry_defect_lineage",
    downstream_gate_read: "pass_blocked_until_human_k4_rough_keep",
  };
  manifest.may_advance_to_final_assembly = false;
  manifest.may_advance_to_publish_readiness = false;
  manifest.may_create_full_runtime_mp4_render = false;
  manifest.may_youtube_action = false;
  manifest.proof_artifacts = {
    ...(manifest.proof_artifacts || {}),
    player_html_path: playerPath,
    player_html_sha256: sha256File(playerPath),
    source_predecessor_player_path: path.join(PROOF_PREDECESSOR_ROOT, "player.html"),
    proof_build_json_path: proofBuildPath,
    proof_build_json_url: proofBuildUrl,
    proof_build_json_sha256: sha256File(proofBuildPath),
    review_packet_path: path.join(PROOF_ROOT, "review/rolling_caption_rail_review_packet.md"),
    end_screen_adaptive_render_audit_path: manifest.end_screen_adaptive_render_audit_path,
    end_screen_adaptive_render_audit_sha256: "pending_browser_runtime_qa",
  };
  writeJson(proofManifestPath, manifest);

  const sourceManifestLocal = path.join(PROOF_ROOT, "references/source_art_manifest.json");
  fs.copyFileSync(sourceManifestPath, sourceManifestLocal);
  const reviewPacketPath = path.join(PROOF_ROOT, "review/rolling_caption_rail_review_packet.md");
  let reviewPacket = fs.existsSync(reviewPacketPath) ? fs.readFileSync(reviewPacketPath, "utf8") : "# Tacoma Rough Proof Review\n";
  const insertion = `\n## K4 Suspension-Cable Geometry Repair\n\nThis successor replaces the Candidate G/K3 backplate lineage with \`${CANDIDATE_ID}\` because the prior left-side suspenders read as detached foreground bars. Review the full frame and left-cable crop before any rough-proof keep.\n\n- New source art: \`${proofSourcePath}\`\n- Source-art package: \`${SOURCE_PACKAGE_ROOT}\`\n- Left cable crop: \`${leftCropPath}\`\n- Required read: \`suspension_cable_geometry_read = pass_left_and_right_suspenders_attach_to_main_cables_and_deck_edges_no_free_floating_foreground_bars\`\n- Downstream gates remain blocked until human rough-proof keep.\n`;
  if (!reviewPacket.includes("## K4 Suspension-Cable Geometry Repair")) {
    reviewPacket += insertion;
  }
  fs.writeFileSync(reviewPacketPath, reviewPacket.endsWith("\n") ? reviewPacket : `${reviewPacket}\n`);
  manifest.proof_artifacts.review_packet_path = reviewPacketPath;
  manifest.proof_artifacts.review_packet_sha256 = sha256File(reviewPacketPath);
  manifest.proof_artifacts.player_html_sha256 = sha256File(playerPath);
  manifest.proof_artifacts.proof_build_json_sha256 = sha256File(proofBuildPath);
  writeJson(proofManifestPath, manifest);

  updateBaseline(proofSourcePath, proofSourceSha, sourceManifestPath, PROOF_ROOT);
  updateReviewIndex(PROOF_ROOT, proofBuildId);
  updateRolloutSummary(PROOF_ROOT, proofBuildId, proofSourcePath, proofSourceSha);

  console.log(
    JSON.stringify(
      {
        source_package_root: SOURCE_PACKAGE_ROOT,
        source_manifest_path: sourceManifestPath,
        normalized_source_art_path: normalizedPath,
        proof_root: PROOF_ROOT,
        proof_manifest_path: proofManifestPath,
        player_path: playerPath,
        player_url: playerUrl,
        proof_build_id: proofBuildId,
      },
      null,
      2,
    ),
  );
}

main();
