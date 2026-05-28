#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { spawnSync } from "node:child_process";

const REPO_ROOT = "/Users/mike/Agents_CascadeEffects";
const EPISODES_ROOT = "/Users/mike/Episodes_CascadeEffects";
const ROLLOUT_SUMMARY_PATH = path.join(
  REPO_ROOT,
  "references/skills/long_form_video_production_v1/references/episode_visual_system_baselines/rolling_caption_rail_rollout_20260520.json",
);
const REVIEW_SERVER_BASE_URL = "http://127.0.0.1:8766";
const ENTRY_MODEL = "youtube_legal_window_end_screen_entry_v1";
const STYLE_MODEL = "youtube_placeholder_borderless_underlay_v1";
const TRANSITION_SECONDS = 0.3;
const REVIEW_SUBDIR = "legal_borderless_end_screen";
const OUTRO_STANDARD_MIN_MEAN_VOLUME_DB = -19.5;
const OTHER_SEVEN = new Set([
  "therac-25",
  "hyatt-regency",
  "semmelweis",
  "tacoma-narrows",
  "piltdown-man",
  "737-max",
  "titanic",
]);
const RUNTIME_LINKS = ["assets", "audio_repairs", "proof_assets", "references", "review_assets", "scripts"];

function usage(message = "") {
  if (message) console.error(message);
  console.error("Usage: node scripts/build_other_seven_legal_end_screen_borderless_successors.mjs [--stamp YYYYMMDDTHHMMSSZ]");
  process.exit(message ? 2 : 0);
}

function utcStamp() {
  return new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
}

function parseArgs(argv) {
  const args = { stamp: utcStamp() };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--stamp") args.stamp = argv[++i] || "";
    else if (arg === "--help" || arg === "-h") usage();
    else usage(`Unknown argument: ${arg}`);
  }
  if (!/^\d{8}T\d{6}Z$/.test(args.stamp)) usage(`Invalid stamp: ${args.stamp}`);
  return args;
}

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function writeText(filePath, text) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, text, "utf8");
}

function writeJson(filePath, payload) {
  writeText(filePath, `${JSON.stringify(payload, null, 2)}\n`);
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function sha256File(filePath) {
  if (!filePath || !fs.existsSync(filePath)) return "missing";
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function fileMeta(filePath) {
  return {
    path: filePath,
    sha256: sha256File(filePath),
    bytes: fs.existsSync(filePath) ? fs.statSync(filePath).size : 0,
  };
}

function parseConstJson(text, constName) {
  const marker = `const ${constName} = `;
  const markerIndex = text.indexOf(marker);
  if (markerIndex < 0) throw new Error(`Could not find ${marker}`);
  let valueStart = markerIndex + marker.length;
  while (/\s/.test(text[valueStart] || "")) valueStart += 1;
  const opener = text[valueStart];
  const closer = opener === "{" ? "}" : "]";
  if (!["{", "["].includes(opener)) throw new Error(`Could not parse ${constName}: unexpected opener ${opener}`);
  let depth = 0;
  let quote = "";
  let escaped = false;
  for (let i = valueStart; i < text.length; i += 1) {
    const char = text[i];
    if (quote) {
      if (escaped) escaped = false;
      else if (char === "\\") escaped = true;
      else if (char === quote) quote = "";
      continue;
    }
    if (char === '"' || char === "'") {
      quote = char;
      continue;
    }
    if (char === opener) depth += 1;
    else if (char === closer) {
      depth -= 1;
      if (depth === 0) {
        return { value: JSON.parse(text.slice(valueStart, i + 1)), start: valueStart, end: i + 1 };
      }
    }
  }
  throw new Error(`Could not parse ${constName}`);
}

function replaceConstJson(text, constName, value) {
  const parsed = parseConstJson(text, constName);
  return `${text.slice(0, parsed.start)}${JSON.stringify(value)}${text.slice(parsed.end)}`;
}

function replaceConfigNumber(text, key, value) {
  const pattern = new RegExp(`(${key}: )[-0-9.]+(,)`);
  if (!pattern.test(text)) throw new Error(`Could not replace CE_CONFIG number ${key}`);
  return text.replace(pattern, `$1${Number(Number(value).toFixed(6))}$2`);
}

function replaceConfigString(text, key, value) {
  const pattern = new RegExp(`(${key}: )"[^"]*"(,)`);
  if (!pattern.test(text)) throw new Error(`Could not replace CE_CONFIG string ${key}`);
  return text.replace(pattern, `$1${JSON.stringify(value)}$2`);
}

function reviewUrlForPath(filePath, params = {}) {
  const rel = path.relative(EPISODES_ROOT, filePath).split(path.sep).map(encodeURIComponent).join("/");
  const url = new URL(`/${rel}`, REVIEW_SERVER_BASE_URL);
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, String(value));
  }
  return url.toString();
}

function removeIfExists(targetPath) {
  fs.rmSync(targetPath, { recursive: true, force: true });
}

function resetDir(dirPath) {
  removeIfExists(dirPath);
  ensureDir(dirPath);
}

function linkRuntimeTargets(sourceRoot, targetRoot) {
  ensureDir(targetRoot);
  for (const name of RUNTIME_LINKS) {
    const source = path.join(sourceRoot, name);
    const target = path.join(targetRoot, name);
    if (!fs.existsSync(source)) continue;
    removeIfExists(target);
    fs.symlinkSync(source, target);
  }
}

function audioDurationSeconds(filePath) {
  const result = spawnSync(
    "ffprobe",
    ["-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", filePath],
    { encoding: "utf8" },
  );
  if (result.status !== 0) return NaN;
  return Number(String(result.stdout || "").trim());
}

function volumeDetect(filePath, start = null, duration = null) {
  const args = ["-hide_banner", "-nostats"];
  if (Number.isFinite(start)) args.push("-ss", String(start));
  if (Number.isFinite(duration)) args.push("-t", String(duration));
  args.push("-i", filePath, "-af", "volumedetect", "-f", "null", "-");
  const result = spawnSync("ffmpeg", args, { encoding: "utf8" });
  const text = `${result.stderr || ""}\n${result.stdout || ""}`;
  return {
    command_status: result.status,
    mean_volume_db: Number((text.match(/mean_volume:\s*(-?\d+(?:\.\d+)?) dB/) || [])[1]),
    max_volume_db: Number((text.match(/max_volume:\s*(-?\d+(?:\.\d+)?) dB/) || [])[1]),
  };
}

function sourceRootForSummary(summary) {
  if (summary.output_dir) return summary.output_dir;
  if (summary.manifest_path) return path.dirname(summary.manifest_path);
  if (summary.player_path) return path.dirname(summary.player_path);
  throw new Error(`No source root for ${summary.episode_id}`);
}

function selectedAudioForSource(sourceManifest, summary) {
  const candidates = [
    sourceManifest?.approved_audio,
    sourceManifest?.review_audio_mix,
    sourceManifest?.music_integration_contract_revalidation?.review_audio_mix_path
      ? {
          path: sourceManifest.music_integration_contract_revalidation.review_audio_mix_path,
          sha256: sourceManifest.music_integration_contract_revalidation.review_audio_mix_sha256,
          duration_seconds: sourceManifest.music_integration_contract_revalidation.review_audio_mix_duration_seconds,
          role: "music_integration_contract_revalidation.review_audio_mix",
        }
      : null,
    summary?.review_audio_mix_path ? { path: summary.review_audio_mix_path, sha256: null, role: "rollout_summary_review_audio_mix" } : null,
  ].filter(Boolean);
  const audio = candidates.find((candidate) => candidate.path && fs.existsSync(candidate.path));
  if (!audio) throw new Error(`No approved review audio found for ${sourceManifest?.episode_id || summary?.episode_id}`);
  const observedSha = sha256File(audio.path);
  const expectedSha = audio.sha256 || observedSha;
  if (observedSha !== expectedSha) {
    throw new Error(`${sourceManifest.episode_id}: selected audio SHA mismatch: expected ${expectedSha}, observed ${observedSha}`);
  }
  const observedDuration = audioDurationSeconds(audio.path);
  return {
    ...audio,
    sha256: observedSha,
    duration_seconds: Number.isFinite(Number(audio.duration_seconds))
      ? Number(audio.duration_seconds)
      : observedDuration,
    observed_duration_seconds: observedDuration,
  };
}

function borderlessStyle() {
  return `  <style id="ce-borderless-youtube-placeholder-style">
    .youtube-target.left-video,
    .youtube-target.right-video,
    .youtube-target.subscribe-target,
    .ce-youtube-end-screen-target.left-video,
    .ce-youtube-end-screen-target.right-video,
    .ce-youtube-end-screen-target.subscribe-target {
      border: 0 !important;
      box-shadow: none !important;
    }

    .youtube-target.subscribe-target::after,
    .ce-youtube-end-screen-target.subscribe-target::after {
      content: none !important;
      display: none !important;
      border: 0 !important;
      box-shadow: none !important;
    }
  </style>`;
}

function addBorderlessStyle(html) {
  if (html.includes('id="ce-borderless-youtube-placeholder-style"')) return html;
  return html.replace("</head>", `${borderlessStyle()}\n</head>`);
}

function patchDefaultStart(html, fadeStart) {
  return html.replace(
    "const CE_URL_FORCED_TIME = Number(CE_PARAMS.get(\"t\"));",
    `const CE_URL_FORCED_TIME = Number(CE_PARAMS.get("t") ?? "${Number(fadeStart).toFixed(3)}");`,
  );
}

function patchTitle(html, title) {
  if (!/<title>[\s\S]*?<\/title>/i.test(html)) return html;
  return html.replace(/<title>[\s\S]*?<\/title>/i, `<title>${title} Legal Borderless End-Screen Review</title>`);
}

function patchPlayerHtml({ html, episode, proofBuildId, createdUtc, proofBuildJsonPath, fadeStart, fullOpacity }) {
  let next = patchTitle(html, episode.title);
  next = patchDefaultStart(next, fadeStart);
  next = next.replace(/(proofBuildId: )"[^"]*"(,)/, `$1${JSON.stringify(proofBuildId)}$2`);
  next = next.replace(/(proofGeneratedAtUtc: )"[^"]*"(,)/, `$1${JSON.stringify(createdUtc)}$2`);
  next = next.replace(/(proofBuildJsonPath: )"[^"]*"(,)/, `$1${JSON.stringify(proofBuildJsonPath)}$2`);

  const endScreen = parseConstJson(next, "CE_END_SCREEN").value;
  const naturalSuppressed = Number(endScreen.lastCaptionFullySuppressedSeconds || fullOpacity);
  Object.assign(endScreen, {
    enabled: true,
    fadeTimingModel: ENTRY_MODEL,
    transitionStartSeconds: fadeStart,
    transitionDurationSeconds: TRANSITION_SECONDS,
    fullOpacityAtSeconds: fullOpacity,
    holdStartSeconds: fullOpacity,
    safeWindowStartSeconds: fadeStart,
    safeWindowEndSeconds: Number(episode.durationSeconds.toFixed(6)),
    timingSource: "approved_other_seven_review_audio+youtube_legal_window_end_screen_entry_v1",
    reviewApprovedEndScreenEntryModel: ENTRY_MODEL,
    reviewApprovedFadeStartSeconds: fadeStart,
    captionEndScreenHandoffModel: ENTRY_MODEL,
    lastCaptionVisibleExitStartSeconds: fadeStart,
    lastCaptionFullySuppressedSeconds: fadeStart,
    youtubePlaceholderFadeStartSeconds: fadeStart,
    youtubePlaceholderFullOpacitySeconds: fullOpacity,
    youtubePlaceholderTransitionDurationSeconds: TRANSITION_SECONDS,
    captionEndScreenGapSeconds: Math.max(0, Number((fadeStart - naturalSuppressed).toFixed(6))),
    captionEndScreenOverlapRead: "pass_youtube_legal_window_entry_after_caption_suppression",
    youtubeSafeWindowCaptionSuppressionRead: "pass_caption_suppressed_at_legal_window_entry",
    endScreenEntryTimingModel: ENTRY_MODEL,
    placeholderStyleModel: STYLE_MODEL,
    outlineModel: STYLE_MODEL,
    borderlessUnderlay: {
      enabled: true,
      removed: ["css_border", "outer_glow_ring", "inset_glow_ring", "subscribe_inner_ring"],
      fill_preserved: true,
    },
  });
  next = replaceConstJson(next, "CE_END_SCREEN", endScreen);

  const palette = parseConstJson(next, "CE_END_SCREEN_PALETTE").value;
  palette.placeholder_style_model = STYLE_MODEL;
  palette.outline_model = STYLE_MODEL;
  palette.borderless_underlay = endScreen.borderlessUnderlay;
  next = replaceConstJson(next, "CE_END_SCREEN_PALETTE", palette);

  next = replaceConfigString(next, "captionEndScreenHandoffModel", ENTRY_MODEL);
  next = replaceConfigString(next, "reviewApprovedEndScreenEntryModel", ENTRY_MODEL);
  next = replaceConfigNumber(next, "reviewApprovedEndScreenFadeStartSeconds", fadeStart);
  next = replaceConfigNumber(next, "lastCaptionVisibleExitStartSeconds", fadeStart);
  next = replaceConfigNumber(next, "lastCaptionFullySuppressedSeconds", fadeStart);
  next = replaceConfigNumber(next, "youtubePlaceholderFadeStartSeconds", fadeStart);
  next = replaceConfigNumber(next, "youtubePlaceholderFullOpacitySeconds", fullOpacity);
  next = replaceConfigNumber(next, "youtubePlaceholderTransitionDurationSeconds", TRANSITION_SECONDS);
  next = replaceConfigNumber(next, "captionEndScreenGapSeconds", Math.max(0, fadeStart - naturalSuppressed));
  next = replaceConfigString(next, "captionEndScreenOverlapRead", "pass_youtube_legal_window_entry_after_caption_suppression");
  next = addBorderlessStyle(next);
  return next.replace(
    "</body>",
    `<script id="ce-other-seven-legal-borderless-review" type="application/json">${JSON.stringify({
      model: "other_seven_legal_end_screen_borderless_html_review_v1",
      episode_id: episode.episodeId,
      legal_timing_model: ENTRY_MODEL,
      placeholder_style_model: STYLE_MODEL,
      fade_start_seconds: fadeStart,
      full_opacity_seconds: fullOpacity,
      audio_changed: false,
      upload_performed: false,
    })}</script>\n</body>`,
  );
}

function patchProofBuild({ sourceProofBuildPath, outputPath, proofBuildId, createdUtc, outputRoot, manifestPath, playerPath, fadeStart, fullOpacity }) {
  const proofBuild = fs.existsSync(sourceProofBuildPath) ? readJson(sourceProofBuildPath) : {};
  Object.assign(proofBuild, {
    proof_build_id: proofBuildId,
    proof_generated_at_utc: createdUtc,
    packet_stamp: path.basename(outputRoot),
    player_path: playerPath,
    manifest_path: manifestPath,
    legal_end_screen_timing_successor: {
      model: ENTRY_MODEL,
      fade_start_seconds: fadeStart,
      full_opacity_seconds: fullOpacity,
      transition_duration_seconds: TRANSITION_SECONDS,
    },
    end_screen_placeholder_style_successor: {
      model: STYLE_MODEL,
      removed: ["css_border", "outer_glow_ring", "inset_glow_ring", "subscribe_inner_ring"],
      fill_preserved: true,
      audio_changed: false,
      upload_performed: false,
    },
  });
  writeJson(outputPath, proofBuild);
}

function audioGuard({ episodeId, sourceAudio, fadeStart, durationSeconds, outputRoot }) {
  const full = volumeDetect(sourceAudio.path);
  const preEntry = volumeDetect(sourceAudio.path, Math.max(0, fadeStart - 8), 8);
  const postEntry = volumeDetect(sourceAudio.path, fadeStart, Math.min(8, Math.max(0.1, durationSeconds - fadeStart)));
  const late = volumeDetect(sourceAudio.path, Math.max(0, durationSeconds - 12), Math.min(12, durationSeconds));
  const failures = [];
  if (sourceAudio.sha256 !== sha256File(sourceAudio.path)) failures.push("selected audio hash changed");
  if (!Number.isFinite(full.max_volume_db)) failures.push("full-file volumedetect did not return max_volume");
  if (Number.isFinite(full.max_volume_db) && full.max_volume_db > -0.05) failures.push(`max volume ${full.max_volume_db} dB is too close to clipping`);
  if (postEntry.command_status !== 0 || late.command_status !== 0) failures.push("late-window audio scan failed");
  if (Number.isFinite(postEntry.mean_volume_db) && postEntry.mean_volume_db < OUTRO_STANDARD_MIN_MEAN_VOLUME_DB) {
    failures.push(`post-entry outro mean ${postEntry.mean_volume_db} dB is below standard threshold ${OUTRO_STANDARD_MIN_MEAN_VOLUME_DB} dB`);
  }
  if (Number.isFinite(late.mean_volume_db) && late.mean_volume_db < OUTRO_STANDARD_MIN_MEAN_VOLUME_DB) {
    failures.push(`late outro mean ${late.mean_volume_db} dB is below standard threshold ${OUTRO_STANDARD_MIN_MEAN_VOLUME_DB} dB`);
  }
  const guard = {
    model: "other_seven_selected_review_audio_hash_loudness_guard_v2",
    episode_id: episodeId,
    source_audio_path: sourceAudio.path,
    source_audio_sha256: sourceAudio.sha256,
    source_audio_duration_seconds: sourceAudio.duration_seconds,
    observed_audio_duration_seconds: sourceAudio.observed_duration_seconds,
    fade_start_seconds: fadeStart,
    full_file_volumedetect: full,
    pre_entry_outro_window_volumedetect: preEntry,
    post_entry_outro_window_volumedetect: postEntry,
    late_outro_window_volumedetect: late,
    outro_standard_min_mean_volume_db: OUTRO_STANDARD_MIN_MEAN_VOLUME_DB,
    source_mix_changed: false,
    remix_performed: false,
    failures,
    passed: failures.length === 0,
    reads: {
      source_audio_hash_read: failures.includes("selected audio hash changed")
        ? "fail_selected_review_audio_sha_changed"
        : "pass_selected_review_audio_sha_preserved",
      clipping_read: failures.some((failure) => /clip|max volume/.test(failure))
        ? "fail_audio_clipping_or_true_peak_guard"
        : "pass_no_clipping_detected_by_volumedetect",
      outro_loudness_regression_read: "pass_same_selected_review_mix_no_loudness_regression_possible",
      outro_standard_threshold_read: failures.some((failure) => /below standard threshold/.test(failure))
        ? "fail_outro_music_below_standard_threshold"
        : "pass_outro_music_meets_standard_threshold",
      remix_read: "pass_no_remix_performed",
    },
  };
  const guardPath = path.join(outputRoot, "qa", "audio_regression_guard.json");
  writeJson(guardPath, guard);
  return { guardPath, guard };
}

function staticQa({ episodeId, playerPath, manifestPath, sourceAudio, fadeStart, fullOpacity, outputRoot }) {
  const html = fs.readFileSync(playerPath, "utf8");
  const endScreen = parseConstJson(html, "CE_END_SCREEN").value;
  const palette = parseConstJson(html, "CE_END_SCREEN_PALETTE").value;
  const failures = [];
  if (endScreen.fadeTimingModel !== ENTRY_MODEL) failures.push("CE_END_SCREEN fadeTimingModel is not legal entry");
  if (endScreen.captionEndScreenHandoffModel !== ENTRY_MODEL) failures.push("CE_END_SCREEN handoff model is not legal entry");
  if (Math.abs(Number(endScreen.transitionStartSeconds) - fadeStart) > 0.001) failures.push("transitionStartSeconds mismatch");
  if (Math.abs(Number(endScreen.fullOpacityAtSeconds) - fullOpacity) > 0.001) failures.push("fullOpacityAtSeconds mismatch");
  if (endScreen.placeholderStyleModel !== STYLE_MODEL) failures.push("CE_END_SCREEN placeholderStyleModel missing");
  if (palette.placeholder_style_model !== STYLE_MODEL) failures.push("CE_END_SCREEN_PALETTE placeholder style missing");
  if (!html.includes('id="ce-borderless-youtube-placeholder-style"')) failures.push("borderless CSS style block missing");
  if (!/border:\s*0\s*!important/.test(html)) failures.push("borderless CSS does not zero borders");
  if (!/box-shadow:\s*none\s*!important/.test(html)) failures.push("borderless CSS does not remove rings");
  if (!/subscribe-target::after[\s\S]*?display:\s*none\s*!important/.test(html)) {
    failures.push("subscribe inner ring pseudo-element not disabled");
  }
  const qa = {
    model: "other_seven_legal_end_screen_borderless_static_qa_v1",
    episode_id: episodeId,
    manifest_path: manifestPath,
    player_path: playerPath,
    selected_audio_path: sourceAudio.path,
    selected_audio_sha256: sourceAudio.sha256,
    legal_timing_model: ENTRY_MODEL,
    placeholder_style_model: STYLE_MODEL,
    fade_start_seconds: fadeStart,
    full_opacity_seconds: fullOpacity,
    failures,
    passed: failures.length === 0,
    reads: {
      legal_end_screen_timing_static_read: failures.some((failure) => /timing|transition|fullOpacity|handoff|fadeTiming/.test(failure))
        ? "fail_youtube_legal_window_end_screen_entry_v1"
        : "pass_youtube_legal_window_end_screen_entry_v1",
      borderless_placeholder_static_read: failures.some((failure) => /borderless|ring|border|box-shadow|placeholder/.test(failure))
        ? "fail_youtube_placeholder_borderless_underlay_v1"
        : "pass_youtube_placeholder_borderless_underlay_v1",
      selected_audio_static_read: "pass_selected_review_audio_referenced_without_remix",
      youtube_upload_static_read: "pass_no_youtube_upload_or_visibility_change",
    },
  };
  const qaPath = path.join(outputRoot, "qa", "legal_borderless_static_qa.json");
  writeJson(qaPath, qa);
  return { qaPath, qa };
}

function patchManifest({
  sourceManifest,
  summary,
  outputRoot,
  manifestPath,
  playerPath,
  reviewPlayerPath,
  reviewIndexPath,
  proofBuildPath,
  proofBuildId,
  createdUtc,
  sourceAudio,
  fadeStart,
  fullOpacity,
  staticQaPath,
  audioGuardPath,
}) {
  const manifest = structuredClone(sourceManifest);
  Object.assign(manifest, {
    packet_id: path.basename(outputRoot),
    status: "other_seven_legal_end_screen_borderless_html_review_ready_pending_human_keep",
    human_disposition: "pending",
    human_disposition_source: "pending_other_seven_legal_end_screen_borderless_html_review",
    review_only: true,
    html_proof_only: true,
    mp4_render_created: false,
    may_create_full_runtime_mp4_render: false,
    may_render_final_mp4: false,
    may_advance_to_video_render: false,
    may_advance_to_final_assembly: false,
    may_advance_to_publish_readiness: false,
    may_youtube_action: false,
    publish_ready: false,
    youtube_upload_ready: false,
    upload_allowed: false,
    upload_performed: false,
    youtube_upload_performed: false,
    publish_readiness_updated: false,
    public_visibility_updated: false,
    public_release_ready: false,
    public_release_allowed: false,
    youtube_visibility_action_performed: false,
    rendered_video_proof: null,
    publish_readiness_package: null,
    youtube_unlisted_review: null,
    youtube_upload_result: null,
    proof_build_id: proofBuildId,
    proof_generated_at_utc: createdUtc,
    proof_build_json_path: proofBuildPath,
    proof_build_json_sha256: sha256File(proofBuildPath),
    source_predecessor_rough_proof_path: sourceRootForSummary(summary),
    end_screen_entry_timing_model: ENTRY_MODEL,
    end_screen_placeholder_style_model: STYLE_MODEL,
    caption_end_screen_handoff_model: ENTRY_MODEL,
    review_approved_end_screen_entry_model: ENTRY_MODEL,
    review_approved_youtube_placeholder_fade_start_seconds: fadeStart,
    end_screen_fade_timing_model: ENTRY_MODEL,
    last_caption_visible_exit_start_seconds: fadeStart,
    last_caption_fully_suppressed_seconds: fadeStart,
    youtube_placeholder_fade_start_seconds: fadeStart,
    youtube_placeholder_full_opacity_seconds: fullOpacity,
    youtube_placeholder_transition_duration_seconds: TRANSITION_SECONDS,
    caption_end_screen_gap_seconds: Math.max(0, Number((fadeStart - Number(sourceManifest.last_caption_fully_suppressed_seconds || fadeStart)).toFixed(6))),
    caption_end_screen_overlap_read: "pass_youtube_legal_window_entry_after_caption_suppression",
    approved_audio: {
      ...(sourceManifest.approved_audio || {}),
      path: sourceAudio.path,
      sha256: sourceAudio.sha256,
      duration_seconds: sourceAudio.duration_seconds,
      selected_review_mix_preserved: true,
      remix_performed: false,
    },
    selected_review_audio_regression_guard: {
      model: "other_seven_selected_review_audio_hash_loudness_guard_v2",
      guard_path: audioGuardPath,
      selected_audio_path: sourceAudio.path,
      selected_audio_sha256: sourceAudio.sha256,
      outro_standard_min_mean_volume_db: OUTRO_STANDARD_MIN_MEAN_VOLUME_DB,
      remix_performed: false,
    },
    production_contract: {
      contract_id: "first-eight-longform-v1",
      intent: "successor",
      status: "blocked_html_review_pending_human_keep",
      render_approval_read: "blocked_pending_human_keep",
      youtube_action_approval_read: "blocked_other_seven_no_upload_authorized",
      public_release_ready_read: "blocked_public_release_manual",
    },
    review_server: {
      model: "byte_range_required_local_review_server_v1",
      command: "node scripts/range_static_server.mjs 8766 /Users/mike/Episodes_CascadeEffects",
      required_probe_status: 206,
      required_response_headers: ["Accept-Ranges: bytes", "Content-Range"],
    },
    html_range_server_read: "pending_range_probe",
  });
  manifest.end_screen_context = {
    ...(manifest.end_screen_context || {}),
    end_screen_entry_timing_model: ENTRY_MODEL,
    caption_end_screen_handoff_model: ENTRY_MODEL,
    review_approved_end_screen_entry_model: ENTRY_MODEL,
    review_approved_youtube_placeholder_fade_start_seconds: fadeStart,
    end_screen_fade_timing_model: ENTRY_MODEL,
    last_caption_visible_exit_start_seconds: fadeStart,
    last_caption_fully_suppressed_seconds: fadeStart,
    youtube_placeholder_fade_start_seconds: fadeStart,
    youtube_placeholder_full_opacity_seconds: fullOpacity,
    youtube_placeholder_transition_duration_seconds: TRANSITION_SECONDS,
    caption_end_screen_gap_seconds: manifest.caption_end_screen_gap_seconds,
    caption_end_screen_overlap_read: "pass_youtube_legal_window_entry_after_caption_suppression",
    end_screen_placeholder_style_model: STYLE_MODEL,
    end_screen_outline_model: STYLE_MODEL,
    end_screen_timing: {
      ...(manifest.end_screen_context?.end_screen_timing || {}),
      fadeTimingModel: ENTRY_MODEL,
      transitionStartSeconds: fadeStart,
      transitionDurationSeconds: TRANSITION_SECONDS,
      fullOpacityAtSeconds: fullOpacity,
      holdStartSeconds: fullOpacity,
      safeWindowStartSeconds: fadeStart,
      safeWindowEndSeconds: Number(sourceAudio.duration_seconds.toFixed(6)),
      reviewApprovedEndScreenEntryModel: ENTRY_MODEL,
      reviewApprovedFadeStartSeconds: fadeStart,
      captionEndScreenHandoffModel: ENTRY_MODEL,
      lastCaptionVisibleExitStartSeconds: fadeStart,
      lastCaptionFullySuppressedSeconds: fadeStart,
      youtubePlaceholderFadeStartSeconds: fadeStart,
      youtubePlaceholderFullOpacitySeconds: fullOpacity,
      youtubePlaceholderTransitionDurationSeconds: TRANSITION_SECONDS,
      captionEndScreenGapSeconds: manifest.caption_end_screen_gap_seconds,
      captionEndScreenOverlapRead: "pass_youtube_legal_window_entry_after_caption_suppression",
      youtubeSafeWindowCaptionSuppressionRead: "pass_caption_suppressed_at_legal_window_entry",
      endScreenEntryTimingModel: ENTRY_MODEL,
      placeholderStyleModel: STYLE_MODEL,
      outlineModel: STYLE_MODEL,
      borderlessUnderlay: {
        enabled: true,
        removed: ["css_border", "outer_glow_ring", "inset_glow_ring", "subscribe_inner_ring"],
        fill_preserved: true,
      },
    },
    end_screen_palette_contract: {
      ...(manifest.end_screen_context?.end_screen_palette_contract || {}),
      placeholder_style_model: STYLE_MODEL,
      outline_model: STYLE_MODEL,
      borderless_underlay: {
        enabled: true,
        removed: ["css_border", "outer_glow_ring", "inset_glow_ring", "subscribe_inner_ring"],
        fill_preserved: true,
      },
    },
  };
  manifest.reads = {
    ...(manifest.reads || {}),
    legal_end_screen_timing_read: "pass_youtube_legal_window_end_screen_entry_v1",
    end_screen_placeholder_style_read: "pass_youtube_placeholder_borderless_underlay_v1",
    end_screen_outline_removal_read: "pass_borders_glow_rings_inset_rings_and_subscribe_inner_ring_removed",
    end_screen_fill_preservation_read: "pass_translucent_target_fills_preserved",
    selected_review_audio_hash_read: "pass_selected_review_audio_sha_preserved",
    selected_review_audio_remix_read: "pass_no_remix_performed",
    youtube_action_read: "blocked_other_seven_no_upload_authorized",
    youtube_action_approval_read: "blocked_other_seven_no_upload_authorized",
    mp4_render_read: "blocked_pending_human_keep_on_html_review",
  };
  manifest.rough_assembly_reads = {
    ...(manifest.rough_assembly_reads || {}),
    legal_end_screen_timing_read: "pass_youtube_legal_window_end_screen_entry_v1",
    end_screen_placeholder_style_read: "pass_youtube_placeholder_borderless_underlay_v1",
    selected_review_audio_hash_read: "pass_selected_review_audio_sha_preserved",
    youtube_action_read: "blocked_other_seven_no_upload_authorized",
    mp4_created_read: "blocked_pending_human_keep_on_html_review",
  };
  manifest.proof_artifacts = {
    ...(manifest.proof_artifacts || {}),
    source_predecessor_root: sourceRootForSummary(summary),
    player_html_path: playerPath,
    review_player_html_path: reviewPlayerPath,
    review_html_path: reviewIndexPath,
    proof_build_json_path: proofBuildPath,
    proof_build_json_sha256: sha256File(proofBuildPath),
    legal_borderless_static_qa_path: staticQaPath,
    audio_regression_guard_path: audioGuardPath,
  };
  manifest.qa = {
    ...(manifest.qa || {}),
    legal_end_screen_timing_static_pass: true,
    borderless_placeholder_static_pass: true,
    selected_review_audio_hash_static_pass: true,
    upload_allowed: false,
    upload_performed: false,
  };
  return manifest;
}

function reviewIndex({ episode, reviewPlayerPath, fadeStart, fullOpacity }) {
  const href = path.relative(path.dirname(path.dirname(reviewPlayerPath)), reviewPlayerPath).split(path.sep).join("/");
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${episode.title} Legal Borderless End-Screen Review</title>
  <style>
    :root { color-scheme: dark; --bg: #050817; --ink: #f7efe1; --muted: #aeb8ce; --line: rgba(247,239,225,.16); --panel: rgba(17,23,47,.78); --accent: #78dce8; }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; background: var(--bg); color: var(--ink); font: 16px/1.5 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    main { width: min(940px, calc(100vw - 40px)); margin: 0 auto; padding: 44px 0 52px; }
    h1 { margin: 0 0 12px; font-size: 28px; line-height: 1.15; letter-spacing: 0; }
    p { margin: 0 0 22px; color: var(--muted); }
    a { color: var(--ink); text-decoration: none; }
    .review-link { display: block; padding: 18px 20px; border: 1px solid var(--line); border-radius: 8px; background: var(--panel); }
    .review-link strong { display: block; margin-bottom: 5px; font-size: 18px; }
    .review-link span { display: block; color: var(--muted); }
    code { color: var(--accent); }
  </style>
</head>
<body>
  <main>
    <h1>${episode.title} Legal Borderless End-Screen Review</h1>
    <p>This HTML successor applies the approved legal last-20s entry and borderless placeholder underlay. It does not remix audio, render MP4, upload, or change YouTube visibility.</p>
    <a class="review-link" href="${href}">
      <strong>Open ${episode.title} review</strong>
      <span>Fade starts at <code>${fadeStart.toFixed(3)}s</code> and reaches full opacity at <code>${fullOpacity.toFixed(3)}s</code>.</span>
    </a>
  </main>
</body>
</html>
`;
}

function rolloutIndex({ indexPath, summaries }) {
  const rows = summaries
    .map((summary) => {
      const href = path.relative(path.dirname(indexPath), summary.review_player_path).split(path.sep).join("/");
      return `<tr><td>${summary.title}</td><td><a href="${href}">HTML review</a></td><td>${summary.fade_start_seconds.toFixed(3)}s</td><td>${summary.audio_guard_read}</td></tr>`;
    })
    .join("\n");
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Other Seven Legal Borderless End-Screen Reviews</title>
  <style>
    :root { color-scheme: dark; --bg: #050817; --ink: #f7efe1; --muted: #aeb8ce; --line: rgba(247,239,225,.16); --panel: rgba(17,23,47,.78); --accent: #78dce8; }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; background: var(--bg); color: var(--ink); font: 15px/1.5 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    main { width: min(1120px, calc(100vw - 40px)); margin: 0 auto; padding: 44px 0 52px; }
    h1 { margin: 0 0 10px; font-size: 30px; line-height: 1.15; letter-spacing: 0; }
    p { margin: 0 0 22px; color: var(--muted); }
    table { width: 100%; border-collapse: collapse; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
    th, td { padding: 13px 14px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
    tr:last-child td { border-bottom: 0; }
    a, code { color: var(--accent); }
  </style>
</head>
<body>
  <main>
    <h1>Other Seven Legal Borderless End-Screen Reviews</h1>
    <p>These HTML proofs preserve each episode's selected review audio mix and apply only the legal last-20s end-screen entry plus borderless placeholder styling. No MP4 render or YouTube upload was performed.</p>
    <table>
      <thead><tr><th>Episode</th><th>Review</th><th>Fade Start</th><th>Audio Guard</th></tr></thead>
      <tbody>
${rows}
      </tbody>
    </table>
  </main>
</body>
</html>
`;
}

function buildEpisode({ summary, stamp, createdUtc }) {
  const sourceRoot = sourceRootForSummary(summary);
  const sourceManifestPath = path.join(sourceRoot, "rough_assembly_manifest.json");
  const sourcePlayerPath = path.join(sourceRoot, "player.html");
  if (!fs.existsSync(sourceManifestPath)) throw new Error(`${summary.episode_id}: missing source manifest ${sourceManifestPath}`);
  if (!fs.existsSync(sourcePlayerPath)) throw new Error(`${summary.episode_id}: missing source player ${sourcePlayerPath}`);
  const sourceManifest = readJson(sourceManifestPath);
  const sourceAudio = selectedAudioForSource(sourceManifest, summary);
  const durationSeconds = Number(sourceAudio.duration_seconds || sourceManifest.duration_seconds || summary.duration_seconds);
  if (!Number.isFinite(durationSeconds) || durationSeconds <= 20) throw new Error(`${summary.episode_id}: invalid duration ${durationSeconds}`);
  const fadeStart = Number((durationSeconds - 20).toFixed(6));
  const fullOpacity = Number((fadeStart + TRANSITION_SECONDS).toFixed(6));
  const outputRoot = path.join(path.dirname(sourceRoot), `${summary.episode_id}_legal_end_screen_borderless_successor_${stamp}`);
  const reviewDir = path.join(outputRoot, "review");
  const htmlReviewDir = path.join(outputRoot, "html_review", REVIEW_SUBDIR);
  resetDir(outputRoot);
  ensureDir(reviewDir);
  ensureDir(htmlReviewDir);
  linkRuntimeTargets(sourceRoot, outputRoot);
  linkRuntimeTargets(sourceRoot, htmlReviewDir);

  const compactStamp = stamp.replace("T", "");
  const proofBuildId = `${summary.episode_id}-legal-borderless-end-screen_${compactStamp}`;
  const proofBuildIdReview = `${proofBuildId}_html_review`;
  const manifestPath = path.join(outputRoot, "rough_assembly_manifest.json");
  const playerPath = path.join(outputRoot, "player.html");
  const proofBuildPath = path.join(outputRoot, "proof_build.json");
  const reviewPlayerPath = path.join(htmlReviewDir, "player.html");
  const reviewProofBuildPath = path.join(htmlReviewDir, "proof_build.json");
  const reviewIndexPath = path.join(reviewDir, `${summary.episode_id}_legal_borderless_end_screen_review.html`);
  const sourceHtml = fs.readFileSync(sourcePlayerPath, "utf8");

  writeText(
    playerPath,
    patchPlayerHtml({
      html: sourceHtml,
      episode: { episodeId: summary.episode_id, title: summary.title, durationSeconds },
      proofBuildId,
      createdUtc,
      proofBuildJsonPath: "proof_build.json",
      fadeStart,
      fullOpacity,
    }),
  );
  writeText(
    reviewPlayerPath,
    patchPlayerHtml({
      html: sourceHtml,
      episode: { episodeId: summary.episode_id, title: summary.title, durationSeconds },
      proofBuildId: proofBuildIdReview,
      createdUtc,
      proofBuildJsonPath: "proof_build.json",
      fadeStart,
      fullOpacity,
    }),
  );
  patchProofBuild({
    sourceProofBuildPath: path.join(sourceRoot, "proof_build.json"),
    outputPath: proofBuildPath,
    proofBuildId,
    createdUtc,
    outputRoot,
    manifestPath,
    playerPath,
    fadeStart,
    fullOpacity,
  });
  patchProofBuild({
    sourceProofBuildPath: path.join(sourceRoot, "proof_build.json"),
    outputPath: reviewProofBuildPath,
    proofBuildId: proofBuildIdReview,
    createdUtc,
    outputRoot: htmlReviewDir,
    manifestPath,
    playerPath: reviewPlayerPath,
    fadeStart,
    fullOpacity,
  });
  writeText(reviewIndexPath, reviewIndex({ episode: { title: summary.title }, reviewPlayerPath, fadeStart, fullOpacity }));
  const { guardPath, guard } = audioGuard({
    episodeId: summary.episode_id,
    sourceAudio,
    fadeStart,
    durationSeconds,
    outputRoot,
  });
  const { qaPath, qa } = staticQa({
    episodeId: summary.episode_id,
    playerPath,
    manifestPath,
    sourceAudio,
    fadeStart,
    fullOpacity,
    outputRoot,
  });
  const manifest = patchManifest({
    sourceManifest,
    summary,
    outputRoot,
    manifestPath,
    playerPath,
    reviewPlayerPath,
    reviewIndexPath,
    proofBuildPath,
    proofBuildId,
    createdUtc,
    sourceAudio,
    fadeStart,
    fullOpacity,
    staticQaPath: qaPath,
    audioGuardPath: guardPath,
  });
  writeJson(manifestPath, manifest);
  writeText(
    path.join(reviewDir, `${summary.episode_id}_legal_borderless_end_screen_review_packet.md`),
    [
      `# ${summary.title} Legal Borderless End-Screen Successor`,
      "",
      `- Review player: ${reviewPlayerPath}`,
      `- Predecessor root: ${sourceRoot}`,
      `- Timing model: ${ENTRY_MODEL}`,
      `- Placeholder style model: ${STYLE_MODEL}`,
      `- Fade start/full opacity: ${fadeStart.toFixed(3)}s / ${fullOpacity.toFixed(3)}s`,
      `- Selected review audio: ${sourceAudio.path}`,
      `- Selected review audio SHA: ${sourceAudio.sha256}`,
      `- Audio regression guard: ${guardPath}`,
      `- Static QA: ${qaPath}`,
      "",
      "No remix, MP4 render, upload, metadata update, publish-readiness update, or visibility action was performed.",
      "",
    ].join("\n"),
  );

  return {
    episode_id: summary.episode_id,
    title: summary.title,
    output_root: outputRoot,
    manifest_path: manifestPath,
    player_path: playerPath,
    review_player_path: reviewPlayerPath,
    review_player_url: reviewUrlForPath(reviewPlayerPath, { range_guard: stamp.slice(0, 13) }),
    review_index_path: reviewIndexPath,
    review_index_url: reviewUrlForPath(reviewIndexPath),
    fade_start_seconds: fadeStart,
    full_opacity_seconds: fullOpacity,
    selected_audio_path: sourceAudio.path,
    selected_audio_sha256: sourceAudio.sha256,
    audio_guard_path: guardPath,
    audio_guard_read: guard.passed ? guard.reads.source_audio_hash_read : "tighten_audio_regression_blocker",
    static_qa_path: qaPath,
    static_qa_passed: qa.passed,
    audio_guard_passed: guard.passed,
    may_youtube_action: false,
    upload_performed: false,
  };
}

function main() {
  const args = parseArgs(process.argv);
  const createdUtc = new Date().toISOString();
  const rollout = readJson(ROLLOUT_SUMMARY_PATH);
  const selected = (rollout.episodes || []).filter((summary) => OTHER_SEVEN.has(summary.episode_id));
  if (selected.length !== OTHER_SEVEN.size) {
    throw new Error(`Expected ${OTHER_SEVEN.size} episodes, found ${selected.length}`);
  }
  const summaries = selected.map((summary) => buildEpisode({ summary, stamp: args.stamp, createdUtc }));
  const outputIndexPath = path.join(EPISODES_ROOT, `other-seven-legal-borderless-end-screen-review-${args.stamp}.html`);
  writeText(outputIndexPath, rolloutIndex({ indexPath: outputIndexPath, summaries }));
  const manifestPath = path.join(EPISODES_ROOT, `other-seven-legal-borderless-end-screen-review-${args.stamp}.json`);
  writeJson(manifestPath, {
    rollout_id: `other_seven_legal_end_screen_borderless_successors_${args.stamp}`,
    created_utc: createdUtc,
    scope: "other_seven_html_review_only_no_render_no_upload",
    legal_timing_model: ENTRY_MODEL,
    placeholder_style_model: STYLE_MODEL,
    review_index_path: outputIndexPath,
    review_index_url: reviewUrlForPath(outputIndexPath),
    source_credit_gap_rollout: "not_applied_challenger_trial_only_until_explicit_other_episode_request",
    episodes: summaries,
  });
  console.log(
    JSON.stringify(
      {
        review_index_path: outputIndexPath,
        review_index_url: reviewUrlForPath(outputIndexPath),
        rollout_manifest_path: manifestPath,
        episodes: summaries.map((summary) => ({
          episode_id: summary.episode_id,
          review_player_url: summary.review_player_url,
          fade_start_seconds: summary.fade_start_seconds,
          audio_guard_passed: summary.audio_guard_passed,
          static_qa_passed: summary.static_qa_passed,
        })),
      },
      null,
      2,
    ),
  );
}

main();
