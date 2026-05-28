#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";

const REPO_ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const EPISODES_ROOT = "/Users/mike/Episodes_CascadeEffects";
const REVIEW_SERVER_BASE_URL = "http://127.0.0.1:8766";
const SOURCE_ROLLOUT_MANIFEST = path.join(
  EPISODES_ROOT,
  "other-seven-legal-borderless-end-screen-review-20260525T234119Z.json",
);
const SOURCE_CATALOG_PATH = path.join(
  REPO_ROOT,
  "references/skills/long_form_video_production_v1/references/other_seven_source_credit_gap_catalog.json",
);
const MODEL = "center_source_credit_gap_v1";
const REVIEW_SUBDIR = "source_credit_gap";
const CREDIT_BEFORE_LEGAL_SECONDS = 6.880884;
const CREDIT_FULL_AFTER_START_SECONDS = 0.75;
const CREDIT_FADE_OUT_BEFORE_LEGAL_SECONDS = 0.930884;
const REVIEW_CONTEXT_BEFORE_SOURCE_CREDIT_SECONDS = 5.3;
const REVIEW_START_MODEL = "challenger_contextual_source_credit_review_start_v1";
const OUTRO_STANDARD_MIN_MEAN_VOLUME_DB = -19.5;
const RUNTIME_LINKS = ["assets", "audio_repairs", "proof_assets", "references", "review_assets", "scripts"];
const OTHER_SEVEN = new Set([
  "therac-25",
  "hyatt-regency",
  "semmelweis",
  "tacoma-narrows",
  "piltdown-man",
  "737-max",
  "titanic",
]);

function usage(message = "") {
  if (message) console.error(message);
  console.error("Usage: node scripts/build_other_seven_source_credit_gap_successors.mjs [--stamp YYYYMMDDTHHMMSSZ]");
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

function resetDir(dirPath) {
  fs.rmSync(dirPath, { recursive: true, force: true });
  ensureDir(dirPath);
}

function removeIfExists(targetPath) {
  fs.rmSync(targetPath, { recursive: true, force: true });
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

function reviewUrlForPath(filePath, params = {}) {
  const rel = path.relative(EPISODES_ROOT, filePath).split(path.sep).map(encodeURIComponent).join("/");
  const url = new URL(`/${rel}`, REVIEW_SERVER_BASE_URL);
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, String(value));
  }
  return url.toString();
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
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
      if (depth === 0) return JSON.parse(text.slice(valueStart, i + 1));
    }
  }
  throw new Error(`Could not parse ${constName}`);
}

function sourceCreditTiming(legalFadeStartSeconds) {
  const legal = Number(legalFadeStartSeconds);
  return {
    fade_start_seconds: Number((legal - CREDIT_BEFORE_LEGAL_SECONDS).toFixed(6)),
    full_opacity_seconds: Number((legal - CREDIT_BEFORE_LEGAL_SECONDS + CREDIT_FULL_AFTER_START_SECONDS).toFixed(6)),
    fade_out_start_seconds: Number((legal - CREDIT_FADE_OUT_BEFORE_LEGAL_SECONDS).toFixed(6)),
    fade_out_end_seconds: Number(legal.toFixed(6)),
  };
}

function sourceCreditReviewStart(timing) {
  return Number(Math.max(0, Number(timing.fade_start_seconds) - REVIEW_CONTEXT_BEFORE_SOURCE_CREDIT_SECONDS).toFixed(3));
}

function formatReviewTime(seconds) {
  return Number(seconds).toFixed(3);
}

function sourceCreditStyle() {
  return `  <style id="ce-source-credit-gap-style">
    .ce-source-credit-gap {
      position: absolute;
      display: block;
      z-index: 6;
      left: 50%;
      top: 50%;
      width: 560px;
      max-width: 46vw;
      transform: translate3d(-50%, -50%, 0);
      opacity: var(--ce-source-credit-gap-opacity, 0);
      pointer-events: none;
      text-align: center;
      color: rgba(255, 248, 232, 0.96);
      text-shadow: 0 3px 18px rgba(0, 0, 0, 0.64);
      background: transparent !important;
      border: 0 !important;
      border-radius: 0 !important;
      box-shadow: none !important;
      padding: 0 !important;
      margin: 0 !important;
      backdrop-filter: none !important;
      -webkit-backdrop-filter: none !important;
      filter: none !important;
    }
    .ce-source-credit-gap[data-active="false"] {
      display: none;
    }
    .ce-source-credit-gap[data-active="true"] {
      display: block;
    }
    .ce-source-credit-gap::before {
      content: "";
      position: absolute;
      z-index: -1;
      inset: -28px -38px;
      border-radius: 10px;
      background: radial-gradient(closest-side, rgba(6, 10, 22, 0.52), rgba(6, 10, 22, 0.28) 64%, rgba(6, 10, 22, 0) 100%);
    }
    .ce-source-credit-gap__label {
      margin: 0 0 18px;
      color: rgba(203, 211, 232, 0.82);
      font-size: 22px;
      font-weight: 760;
      line-height: 1;
      letter-spacing: 0;
      text-transform: uppercase;
    }
    .ce-source-credit-gap__list {
      list-style: none;
      margin: 0;
      padding: 0;
      display: grid;
      gap: 13px;
    }
    .ce-source-credit-gap__item {
      margin: 0;
      color: rgba(255, 248, 232, 0.98);
      font-size: 32px;
      font-weight: 760;
      line-height: 1.12;
      letter-spacing: 0;
    }
  </style>
`;
}

function borderlessCompatStyle() {
  return `  <style id="ce-source-credit-borderless-compat-style">
    .end-screen .target.left,
    .end-screen .target.right,
    .end-screen .target.subscribe {
      border: 0 !important;
      box-shadow: none !important;
    }

    .end-screen .target.subscribe::after {
      content: none !important;
      display: none !important;
      border: 0 !important;
      box-shadow: none !important;
    }
  </style>
`;
}

function reviewChromeGuardStyle() {
  return `  <style id="ce-source-credit-review-chrome-guard-style">
    html:not(.render-mode) main > .review-header,
    html:not(.render-mode) main > .audio-review,
    html:not(.render-mode) main > .controls,
    html:not(.render-mode) main > .review-grid,
    html:not(.render-mode) main > .review-note,
    html:not(.render-mode) main > .review-meta,
    html:not(.render-mode) main > .machine-reads,
    html:not(.render-mode) main > .player,
    html:not(.render-mode) main > .body,
    html:not(.render-mode) main > header {
      display: none !important;
    }

    html:not(.render-mode) main:has(> .stage-shell) {
      width: min(calc(100vw - 22px), 1920px) !important;
      max-width: none !important;
      padding: 0 0 110px !important;
    }

    html.render-mode main:not(.stage):not(.ce-fixed-stage) > :not(.stage-shell):not(.ce-stage-scale-shell):not(.frame):not(.stage-frame),
    html.render-mode .review-header,
    html.render-mode .audio-review,
    html.render-mode .controls,
    html.render-mode .review-grid,
    html.render-mode .review-note,
    html.render-mode .review-meta,
    html.render-mode .machine-reads,
    html.render-mode header,
    html.render-mode audio,
    html.render-mode output,
    html.render-mode input,
    html.render-mode select,
    html.render-mode textarea,
    html.render-mode .ce-review-transport {
      display: none !important;
      visibility: hidden !important;
      opacity: 0 !important;
    }
  </style>
`;
}

function sourceCreditMarkup(sourceLabels) {
  const items = sourceLabels
    .map((source) => `        <li class="ce-source-credit-gap__item">${escapeHtml(source)}</li>`)
    .join("\n");
  return `<section class="ce-source-credit-gap" id="ceSourceCreditGap" aria-label="Primary source credits" data-source-credit-model="${MODEL}" data-active="false" aria-hidden="true">
      <p class="ce-source-credit-gap__label">Sources</p>
      <ol class="ce-source-credit-gap__list">
${items}
      </ol>
    </section>`;
}

function sourceCreditRuntime(config) {
  const json = JSON.stringify(config);
  return `<script id="ce-source-credit-gap-config" type="application/json">${json}</script>
<script id="ce-source-credit-gap-runtime">
  (function () {
    const configEl = document.getElementById("ce-source-credit-gap-config");
    const config = configEl ? JSON.parse(configEl.textContent || "{}") : {};
    const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
    const smoother = (value) => {
      const t = clamp(Number(value) || 0, 0, 1);
      return t * t * (3 - 2 * t);
    };
    function sourceCreditOpacityAt(time) {
      const safe = Number(time) || 0;
      const fadeStart = Number(config.fade_start_seconds) || 0;
      const full = Number(config.full_opacity_seconds) || fadeStart;
      const fadeOutStart = Number(config.fade_out_start_seconds) || full;
      const fadeOutEnd = Number(config.fade_out_end_seconds) || fadeOutStart;
      if (safe < fadeStart || safe >= fadeOutEnd) return 0;
      if (safe < full) return smoother((safe - fadeStart) / Math.max(0.001, full - fadeStart));
      if (safe >= fadeOutStart) return 1 - smoother((safe - fadeOutStart) / Math.max(0.001, fadeOutEnd - fadeOutStart));
      return 1;
    }
    function updateSourceCreditGap(time) {
      const overlay = document.getElementById("ceSourceCreditGap");
      if (!overlay) return 0;
      const opacity = sourceCreditOpacityAt(time);
      overlay.style.setProperty("--ce-source-credit-gap-opacity", opacity.toFixed(4));
      overlay.dataset.active = opacity > 0.001 ? "true" : "false";
      return opacity;
    }
    function urlRequestedTime() {
      const params = new URLSearchParams(window.location.search);
      const raw = Number(params.get("t"));
      if (Number.isFinite(raw)) return raw;
      const fallback = Number(config.review_start_seconds);
      return Number.isFinite(fallback) ? fallback : 0;
    }
    function currentReviewTime() {
      const transportState = typeof window.__ceReviewTransportState === "function" ? window.__ceReviewTransportState() : null;
      if (
        transportState &&
        transportState.pendingScrubTime !== null &&
        transportState.pendingScrubTime !== undefined &&
        Number.isFinite(Number(transportState.pendingScrubTime))
      ) {
        return Number(transportState.pendingScrubTime);
      }
      if (audio && Number.isFinite(Number(audio.currentTime)) && Number(audio.currentTime) > 0) {
        return Number(audio.currentTime);
      }
      if (
        transportState &&
        transportState.scrubberValue !== null &&
        transportState.scrubberValue !== undefined &&
        Number.isFinite(Number(transportState.scrubberValue))
      ) {
        return Number(transportState.scrubberValue);
      }
      return urlRequestedTime();
    }
    const priorSetRenderTime = window.__setRenderTime;
    window.__setRenderTime = (time) => {
      const result = typeof priorSetRenderTime === "function" ? priorSetRenderTime(time) : time;
      updateSourceCreditGap(Number(time) || 0);
      return result;
    };
    window.__sourceCreditGapOpacityAt = sourceCreditOpacityAt;
    window.__sourceCreditGapStateAt = (time) => ({
      model: config.model,
      time: Number(time) || 0,
      opacity: sourceCreditOpacityAt(time),
      sources: config.sources || [],
      timing: config,
    });
    const audio = document.getElementById("audio") || document.querySelector("audio");
    let raf = 0;
    function syncFromAudio() {
      updateSourceCreditGap(currentReviewTime());
    }
    function tick() {
      syncFromAudio();
      if (audio && !audio.paused && !audio.ended) raf = requestAnimationFrame(tick);
    }
    if (audio) {
      ["timeupdate", "seeked", "seeking", "loadedmetadata", "pause"].forEach((eventName) => {
        audio.addEventListener(eventName, syncFromAudio);
      });
      audio.addEventListener("play", () => {
        cancelAnimationFrame(raf);
        tick();
      });
    }
    window.addEventListener("load", syncFromAudio);
    syncFromAudio();
  })();
</script>`;
}

function patchProofBuildConfig(html, { proofBuildId, createdUtc, proofBuildJsonPath }) {
  const replacements = [
    [/(proofBuildId:\s*)"[^"]*"(,)/, `$1${JSON.stringify(proofBuildId)}$2`, "proofBuildId"],
    [/(proofGeneratedAtUtc:\s*)"[^"]*"(,)/, `$1${JSON.stringify(createdUtc)}$2`, "proofGeneratedAtUtc"],
    [/(proofBuildJsonPath:\s*)"[^"]*"(,)/, `$1${JSON.stringify(proofBuildJsonPath)}$2`, "proofBuildJsonPath"],
  ];
  let patched = html;
  for (const [pattern, replacement, label] of replacements) {
    if (!pattern.test(patched)) throw new Error(`Could not patch player proof build field: ${label}`);
    patched = patched.replace(pattern, replacement);
  }
  return patched;
}

function patchDefaultReviewStart(html, { reviewStartSeconds }) {
  const replacement = `const CE_URL_FORCED_TIME = Number(CE_PARAMS.get("t") ?? "${formatReviewTime(reviewStartSeconds)}");`;
  const pattern = /const CE_URL_FORCED_TIME = Number\(CE_PARAMS\.get\("t"\)(?: \?\? "[^"]*")?\);/;
  if (!pattern.test(html)) throw new Error("Could not patch player default review start time");
  return html.replace(pattern, replacement);
}

function playerProofBuildConfig(html) {
  const readField = (field) => {
    const match = html.match(new RegExp(`${field}:\\s*"([^"]*)"`));
    return match ? match[1] : "";
  };
  return {
    proofBuildId: readField("proofBuildId"),
    proofGeneratedAtUtc: readField("proofGeneratedAtUtc"),
    proofBuildJsonPath: readField("proofBuildJsonPath"),
  };
}

function playerDefaultReviewStartSeconds(html) {
  const match = html.match(/const CE_URL_FORCED_TIME = Number\(CE_PARAMS\.get\("t"\) \?\? "([^"]+)"\);/);
  return match ? Number(match[1]) : NaN;
}

function sourceCreditConfigFromHtml(html) {
  const match = html.match(/<script id="ce-source-credit-gap-config" type="application\/json">([\s\S]*?)<\/script>/);
  return match ? JSON.parse(match[1]) : null;
}

function firstAudioSrcFromHtml(html) {
  const match = html.match(/<audio\b[^>]*\bsrc=("[^"]*"|'[^']*')[^>]*>/i);
  if (!match) return "";
  return match[1].slice(1, -1);
}

function localPathForPlayerSrc(playerPath, src) {
  if (!src || /^[a-z]+:/i.test(src)) return "";
  const cleanSrc = src.split(/[?#]/)[0];
  return path.resolve(path.dirname(playerPath), cleanSrc);
}

function playerAudioSrcRead({ html, playerPath, selectedAudio, label }) {
  const src = firstAudioSrcFromHtml(html);
  const resolvedPath = localPathForPlayerSrc(playerPath, src);
  const observedSha = resolvedPath && fs.existsSync(resolvedPath) ? sha256File(resolvedPath) : "missing";
  const passed = Boolean(src && resolvedPath && fs.existsSync(resolvedPath) && observedSha === selectedAudio.sha256);
  return {
    label,
    src,
    resolved_path: resolvedPath,
    observed_sha256: observedSha,
    expected_audio_path: selectedAudio.path,
    expected_audio_sha256: selectedAudio.sha256,
    passed,
    read: passed ? "pass_player_audio_src_resolves_to_selected_audio_sha" : "fail_player_audio_src_not_selected_audio_sha",
  };
}

function patchPlayerHtml({
  html,
  summary,
  catalogEntry,
  timing,
  legalFullOpacitySeconds,
  reviewStartSeconds,
  proofBuildId,
  createdUtc,
  proofBuildJsonPath,
}) {
  if (html.includes("ce-source-credit-gap-style")) {
    throw new Error(`${summary.episode_id}: source credit gap style already exists in source player`);
  }
  let patched = patchProofBuildConfig(html, { proofBuildId, createdUtc, proofBuildJsonPath });
  patched = patchDefaultReviewStart(patched, { reviewStartSeconds });
  patched = patched.replace("</head>", `${sourceCreditStyle()}${borderlessCompatStyle()}${reviewChromeGuardStyle()}</head>`);
  const railNeedle = /<((?:section|aside)\s+class="rail")/;
  if (!railNeedle.test(patched)) throw new Error(`${summary.episode_id}: could not find insertion point before rolling rail`);
  patched = patched.replace(railNeedle, `${sourceCreditMarkup(catalogEntry.source_labels)}<$1`);
  const config = {
    model: MODEL,
    review_scope: "other_seven_html_review_only_no_render_no_upload",
    placement: "center_frame_between_final_caption_and_legal_end_screen",
    episode_id: summary.episode_id,
    title: summary.title,
    sources: catalogEntry.source_labels,
    source_selection_basis: catalogEntry.source_selection_basis,
    provenance_paths: catalogEntry.provenance_paths || [],
    external_provenance_urls: catalogEntry.external_provenance_urls || [],
    fade_start_seconds: timing.fade_start_seconds,
    full_opacity_seconds: timing.full_opacity_seconds,
    fade_out_start_seconds: timing.fade_out_start_seconds,
    fade_out_end_seconds: timing.fade_out_end_seconds,
    review_start_model: REVIEW_START_MODEL,
    review_start_seconds: reviewStartSeconds,
    review_context_before_source_credit_seconds: REVIEW_CONTEXT_BEFORE_SOURCE_CREDIT_SECONDS,
    legal_end_screen_fade_start_seconds: Number(summary.fade_start_seconds),
    legal_end_screen_full_opacity_seconds: Number(legalFullOpacitySeconds),
    audio_changed: false,
    end_screen_timing_changed: false,
    placeholder_style_changed: false,
    youtube_upload_or_visibility_changed: false,
  };
  return patched.replace("</body>", `${sourceCreditRuntime(config)}\n</body>`);
}

function selectedAudio(summary, sourceManifest) {
  const audioPath = summary.selected_audio_path || sourceManifest?.approved_audio?.path;
  const expectedSha = summary.selected_audio_sha256 || sourceManifest?.approved_audio?.sha256;
  if (!audioPath || !fs.existsSync(audioPath)) throw new Error(`${summary.episode_id}: selected audio missing`);
  const observedSha = sha256File(audioPath);
  if (expectedSha && observedSha !== expectedSha) {
    throw new Error(`${summary.episode_id}: selected audio SHA mismatch: expected ${expectedSha}, observed ${observedSha}`);
  }
  return {
    path: audioPath,
    sha256: observedSha,
    duration_seconds: sourceManifest?.approved_audio?.duration_seconds || sourceManifest?.duration_seconds || null,
  };
}

function readInheritedAudioGuard(summary) {
  const guardPath = summary.audio_guard_path;
  if (!guardPath || !fs.existsSync(guardPath)) {
    throw new Error(`${summary.episode_id}: inherited audio guard missing`);
  }
  const guard = readJson(guardPath);
  if (!guard.passed) {
    throw new Error(`${summary.episode_id}: inherited audio guard did not pass`);
  }
  validateInheritedAudioGuardMeetsStandard(summary.episode_id, guard);
  return { guardPath, guard, sha256: sha256File(guardPath) };
}

function validateInheritedAudioGuardMeetsStandard(episodeId, guard) {
  const postEntryMean = Number(guard?.post_entry_outro_window_volumedetect?.mean_volume_db);
  const lateMean = Number(guard?.late_outro_window_volumedetect?.mean_volume_db);
  const failures = [];
  if (Number.isFinite(postEntryMean) && postEntryMean < OUTRO_STANDARD_MIN_MEAN_VOLUME_DB) {
    failures.push(`post-entry outro mean ${postEntryMean} dB is below standard threshold ${OUTRO_STANDARD_MIN_MEAN_VOLUME_DB} dB`);
  }
  if (Number.isFinite(lateMean) && lateMean < OUTRO_STANDARD_MIN_MEAN_VOLUME_DB) {
    failures.push(`late outro mean ${lateMean} dB is below standard threshold ${OUTRO_STANDARD_MIN_MEAN_VOLUME_DB} dB`);
  }
  if (failures.length) {
    throw new Error(`${episodeId}: inherited audio guard is preservation-only and fails outro standard: ${failures.join("; ")}`);
  }
}

function validateCatalogEntry(episodeId, catalogEntry) {
  const failures = [];
  if (!catalogEntry) failures.push("source catalog entry missing");
  const labels = catalogEntry?.source_labels || [];
  if (labels.length !== 3) failures.push(`expected exactly 3 source labels, found ${labels.length}`);
  labels.forEach((label, index) => {
    if (!label || typeof label !== "string") failures.push(`source label ${index + 1} is empty`);
    if (/https?:\/\//i.test(label)) failures.push(`source label ${index + 1} contains a URL`);
  });
  for (const provenancePath of catalogEntry?.provenance_paths || []) {
    if (!fs.existsSync(provenancePath)) failures.push(`provenance path missing: ${provenancePath}`);
  }
  if (failures.length) throw new Error(`${episodeId}: source catalog validation failed: ${failures.join("; ")}`);
}

function patchProofBuild({ sourceProofBuildPath, outputPath, proofBuildId, createdUtc, manifestPath, playerPath, sourceCreditGap }) {
  const proofBuild = fs.existsSync(sourceProofBuildPath) ? readJson(sourceProofBuildPath) : {};
  Object.assign(proofBuild, {
    proof_build_id: proofBuildId,
    proof_generated_at_utc: createdUtc,
    player_path: playerPath,
    manifest_path: manifestPath,
    source_credit_gap_successor: sourceCreditGap,
    html_review_only: true,
    mp4_render_created: false,
    upload_performed: false,
  });
  writeJson(outputPath, proofBuild);
}

function staticQa({
  summary,
  playerPath,
  reviewPlayerPath,
  proofBuildPath,
  reviewProofBuildPath,
  expectedProofBuildId,
  expectedReviewProofBuildId,
  createdUtc,
  reviewStartSeconds,
  manifestPath,
  sourceManifest,
  sourceAudio,
  inheritedAudioGuard,
  catalogEntry,
  timing,
  outputRoot,
}) {
  const html = fs.readFileSync(playerPath, "utf8");
  const reviewHtml = fs.readFileSync(reviewPlayerPath, "utf8");
  const playerProofConfig = playerProofBuildConfig(html);
  const reviewPlayerProofConfig = playerProofBuildConfig(reviewHtml);
  const playerDefaultReviewStart = playerDefaultReviewStartSeconds(html);
  const reviewPlayerDefaultReviewStart = playerDefaultReviewStartSeconds(reviewHtml);
  const sourceCreditConfig = sourceCreditConfigFromHtml(html);
  const reviewSourceCreditConfig = sourceCreditConfigFromHtml(reviewHtml);
  const playerAudioRead = playerAudioSrcRead({ html, playerPath, selectedAudio: sourceAudio, label: "root_player" });
  const reviewPlayerAudioRead = playerAudioSrcRead({
    html: reviewHtml,
    playerPath: reviewPlayerPath,
    selectedAudio: sourceAudio,
    label: "html_review_player",
  });
  const proofBuild = readJson(proofBuildPath);
  const reviewProofBuild = readJson(reviewProofBuildPath);
  const endScreen = parseConstJson(html, "CE_END_SCREEN");
  const failures = [];
  if (!html.includes('id="ce-source-credit-gap-style"')) failures.push("source credit CSS missing");
  if (!html.includes(`data-source-credit-model="${MODEL}"`)) failures.push("source credit model metadata missing");
  if (!html.includes("window.__sourceCreditGapStateAt")) failures.push("source credit runtime hook missing");
  for (const label of catalogEntry.source_labels) {
    if (!html.includes(escapeHtml(label))) failures.push(`source label missing from HTML: ${label}`);
  }
  if (catalogEntry.source_labels.length !== 3) failures.push("source catalog does not contain exactly three labels");
  if (catalogEntry.source_labels.some((label) => /https?:\/\//i.test(label))) failures.push("source label contains URL");
  if (Math.abs(Number(endScreen.transitionStartSeconds) - Number(summary.fade_start_seconds)) > 0.001) {
    failures.push("legal end-screen transition start changed");
  }
  if (Math.abs(Number(endScreen.fullOpacityAtSeconds) - Number(summary.full_opacity_seconds)) > 0.001) {
    failures.push("legal end-screen full opacity changed");
  }
  if (endScreen.fadeTimingModel !== "youtube_legal_window_end_screen_entry_v1") {
    failures.push("legal end-screen timing model changed");
  }
  if (endScreen.placeholderStyleModel !== "youtube_placeholder_borderless_underlay_v1") {
    failures.push("placeholder style model changed");
  }
  if (!html.includes('id="ce-borderless-youtube-placeholder-style"')) failures.push("borderless placeholder style missing");
  if (!html.includes('id="ce-source-credit-review-chrome-guard-style"')) failures.push("source-credit review chrome guard style missing");
  if (!html.includes("function currentReviewTime()")) failures.push("source-credit URL/review-time sync guard missing");
  if (!html.includes("background: transparent !important;")) failures.push("source-credit container reset missing");
  if (sourceAudio.sha256 !== sha256File(sourceAudio.path)) failures.push("selected audio SHA changed");
  if (!playerAudioRead.passed) failures.push(`root player audio src does not resolve to selected audio SHA: ${playerAudioRead.src || "(missing)"}`);
  if (!reviewPlayerAudioRead.passed) {
    failures.push(`review player audio src does not resolve to selected audio SHA: ${reviewPlayerAudioRead.src || "(missing)"}`);
  }
  if (!inheritedAudioGuard.guard?.reads?.source_audio_hash_read?.startsWith("pass")) {
    failures.push("inherited audio hash guard is not pass");
  }
  if (!sourceManifest?.upload_performed === false && sourceManifest?.upload_performed) failures.push("source manifest records upload performed");
  if (timing.fade_out_end_seconds !== Number(summary.fade_start_seconds)) failures.push("source credit does not clear at legal entry");
  if (timing.fade_start_seconds >= timing.full_opacity_seconds) failures.push("source credit fade start/full order invalid");
  if (timing.fade_out_start_seconds >= timing.fade_out_end_seconds) failures.push("source credit fade-out order invalid");
  if (playerProofConfig.proofBuildId !== expectedProofBuildId) {
    failures.push(`root player proofBuildId mismatch: ${playerProofConfig.proofBuildId} !== ${expectedProofBuildId}`);
  }
  if (reviewPlayerProofConfig.proofBuildId !== expectedReviewProofBuildId) {
    failures.push(
      `review player proofBuildId mismatch: ${reviewPlayerProofConfig.proofBuildId} !== ${expectedReviewProofBuildId}`,
    );
  }
  if (playerProofConfig.proofGeneratedAtUtc !== createdUtc) failures.push("root player proofGeneratedAtUtc mismatch");
  if (reviewPlayerProofConfig.proofGeneratedAtUtc !== createdUtc) failures.push("review player proofGeneratedAtUtc mismatch");
  if (playerProofConfig.proofBuildJsonPath !== "proof_build.json") failures.push("root player proofBuildJsonPath mismatch");
  if (reviewPlayerProofConfig.proofBuildJsonPath !== "proof_build.json") {
    failures.push("review player proofBuildJsonPath mismatch");
  }
  if (proofBuild.proof_build_id !== expectedProofBuildId) {
    failures.push(`root proof_build.json id mismatch: ${proofBuild.proof_build_id} !== ${expectedProofBuildId}`);
  }
  if (reviewProofBuild.proof_build_id !== expectedReviewProofBuildId) {
    failures.push(`review proof_build.json id mismatch: ${reviewProofBuild.proof_build_id} !== ${expectedReviewProofBuildId}`);
  }
  if (!(reviewStartSeconds < timing.fade_start_seconds)) failures.push("review start is not before source-credit fade start");
  if (Math.abs(playerDefaultReviewStart - reviewStartSeconds) > 0.001) {
    failures.push(`root player default review start mismatch: ${playerDefaultReviewStart} !== ${reviewStartSeconds}`);
  }
  if (Math.abs(reviewPlayerDefaultReviewStart - reviewStartSeconds) > 0.001) {
    failures.push(`review player default review start mismatch: ${reviewPlayerDefaultReviewStart} !== ${reviewStartSeconds}`);
  }
  if (sourceCreditConfig?.review_start_model !== REVIEW_START_MODEL) failures.push("root source-credit review start model missing");
  if (reviewSourceCreditConfig?.review_start_model !== REVIEW_START_MODEL) {
    failures.push("review source-credit review start model missing");
  }
  if (Math.abs(Number(sourceCreditConfig?.review_start_seconds) - reviewStartSeconds) > 0.001) {
    failures.push("root source-credit review start seconds mismatch");
  }
  if (Math.abs(Number(reviewSourceCreditConfig?.review_start_seconds) - reviewStartSeconds) > 0.001) {
    failures.push("review source-credit review start seconds mismatch");
  }

  const qa = {
    model: "other_seven_source_credit_gap_static_qa_v1",
    created_utc: new Date().toISOString(),
    episode_id: summary.episode_id,
    status: failures.length ? "fail" : "pass",
    passed: failures.length === 0,
    manifest_path: manifestPath,
    player_path: playerPath,
    source_credit_model: MODEL,
    source_labels: catalogEntry.source_labels,
    source_selection_basis: catalogEntry.source_selection_basis,
    provenance_paths: catalogEntry.provenance_paths || [],
    external_provenance_urls: catalogEntry.external_provenance_urls || [],
    source_credit_timing: timing,
    source_credit_review_start_model: REVIEW_START_MODEL,
    source_credit_review_start_seconds: reviewStartSeconds,
    player_default_review_start_seconds: playerDefaultReviewStart,
    review_player_default_review_start_seconds: reviewPlayerDefaultReviewStart,
    player_proof_build_config: playerProofConfig,
    review_player_proof_build_config: reviewPlayerProofConfig,
    expected_proof_build_id: expectedProofBuildId,
    expected_review_proof_build_id: expectedReviewProofBuildId,
    legal_end_screen_fade_start_seconds: Number(summary.fade_start_seconds),
    legal_end_screen_full_opacity_seconds: Number(summary.full_opacity_seconds),
    selected_audio_path: sourceAudio.path,
    selected_audio_sha256: sourceAudio.sha256,
    player_audio_src_read: playerAudioRead,
    review_player_audio_src_read: reviewPlayerAudioRead,
    inherited_audio_guard_path: inheritedAudioGuard.guardPath,
    inherited_audio_guard_sha256: inheritedAudioGuard.sha256,
    failures,
    reads: {
      source_credit_gap_static_read: failures.length ? "fail_source_credit_gap_static_qa" : "pass_source_credit_gap_static_qa",
      source_credit_names_read: failures.some((failure) => /source label|catalog/.test(failure))
        ? "fail_three_named_sources_missing_or_invalid"
        : "pass_three_named_sources_present_no_urls_on_screen",
      source_credit_timing_read: failures.some((failure) => /source credit.*(clear|order)|fade/.test(failure))
        ? "fail_source_credit_gap_timing"
        : "pass_source_credits_clear_at_legal_end_screen_entry",
      end_screen_legal_timing_preservation_read: failures.some((failure) => /legal end-screen|timing model/.test(failure))
        ? "fail_legal_end_screen_timing_changed"
        : "pass_youtube_legal_window_end_screen_entry_v1_unchanged",
      borderless_placeholder_preservation_read: failures.some((failure) => /borderless|placeholder/.test(failure))
        ? "fail_borderless_placeholder_style_changed"
        : "pass_youtube_placeholder_borderless_underlay_v1_unchanged",
      audio_regression_guard_read: failures.some((failure) => /audio/.test(failure))
        ? "fail_selected_review_audio_guard"
        : "pass_selected_review_audio_sha_preserved_no_remix",
      player_audio_src_read:
        playerAudioRead.passed && reviewPlayerAudioRead.passed
          ? "pass_players_reference_selected_review_audio_sha"
          : "fail_player_audio_src_not_selected_review_audio_sha",
      proof_build_freshness_config_read: failures.some((failure) => /proofBuild|proof_build|proofGeneratedAtUtc/.test(failure))
        ? "fail_player_proof_build_config_mismatch"
        : "pass_player_proof_build_config_matches_proof_build_json",
      source_credit_review_start_read: failures.some((failure) => /review start/.test(failure))
        ? "fail_source_credit_review_start_not_contextual"
        : "pass_source_credit_review_starts_before_fade_like_challenger",
      youtube_action_read: "blocked_other_seven_no_upload_authorized",
    },
  };
  const qaPath = path.join(outputRoot, "qa", "source_credit_gap_static_qa.json");
  writeJson(qaPath, qa);
  if (failures.length) throw new Error(`${summary.episode_id}: static QA failed:\n${JSON.stringify(qa, null, 2)}`);
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
  inheritedAudioGuard,
  catalogEntry,
  timing,
  reviewStartSeconds,
  staticQaPath,
}) {
  const manifest = structuredClone(sourceManifest);
  Object.assign(manifest, {
    packet_id: path.basename(outputRoot),
    status: "other_seven_source_credit_gap_html_review_ready_pending_human_keep",
    human_disposition: "pending",
    human_disposition_source: "pending_other_seven_source_credit_gap_html_review",
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
    source_predecessor_rough_proof_path: summary.output_root,
    source_credit_gap_model: MODEL,
    source_credit_gap_timing: timing,
    source_credit_gap_review_start_model: REVIEW_START_MODEL,
    source_credit_gap_review_start_seconds: reviewStartSeconds,
    source_credit_gap_audio_changed: false,
    source_credit_gap_end_screen_timing_changed: false,
    source_credit_gap_placeholder_style_changed: false,
    approved_audio: {
      ...(sourceManifest.approved_audio || {}),
      path: sourceAudio.path,
      sha256: sourceAudio.sha256,
      selected_review_mix_preserved: true,
      remix_performed: false,
    },
    selected_review_audio_regression_guard: {
      ...(sourceManifest.selected_review_audio_regression_guard || {}),
      inherited_guard_path: inheritedAudioGuard.guardPath,
      inherited_guard_sha256: inheritedAudioGuard.sha256,
      selected_audio_path: sourceAudio.path,
      selected_audio_sha256: sourceAudio.sha256,
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
    source_credit_gap: {
      model: MODEL,
      source_labels: catalogEntry.source_labels,
      source_selection_basis: catalogEntry.source_selection_basis,
      provenance_paths: catalogEntry.provenance_paths || [],
      external_provenance_urls: catalogEntry.external_provenance_urls || [],
      timing,
      review_start_model: REVIEW_START_MODEL,
      review_start_seconds: reviewStartSeconds,
      review_context_before_source_credit_seconds: REVIEW_CONTEXT_BEFORE_SOURCE_CREDIT_SECONDS,
      placement: "center_frame_between_final_caption_and_legal_end_screen",
      legal_end_screen_fade_start_seconds: Number(summary.fade_start_seconds),
      legal_end_screen_full_opacity_seconds: Number(summary.full_opacity_seconds),
      screen_text_policy: "three_named_sources_no_urls",
      audio_changed: false,
      end_screen_timing_changed: false,
      placeholder_style_changed: false,
      mp4_render_created: false,
      upload_performed: false,
      may_youtube_action: false,
      static_qa_path: staticQaPath,
    },
    html_range_server_read: "pending_range_probe",
  });
  manifest.reads = {
    ...(manifest.reads || {}),
    source_credit_gap_static_read: "pass_source_credit_gap_static_qa",
    source_credit_names_read: "pass_three_named_sources_present_no_urls_on_screen",
    source_credit_timing_read: "pass_source_credits_clear_at_legal_end_screen_entry",
    source_credit_review_start_read: "pass_source_credit_review_starts_before_fade_like_challenger",
    end_screen_legal_timing_preservation_read: "pass_youtube_legal_window_end_screen_entry_v1_unchanged",
    borderless_placeholder_preservation_read: "pass_youtube_placeholder_borderless_underlay_v1_unchanged",
    selected_review_audio_hash_read: "pass_selected_review_audio_sha_preserved",
    selected_review_audio_remix_read: "pass_no_remix_performed",
    audio_regression_guard_read: "pass_inherited_selected_review_audio_guard_preserved",
    youtube_action_read: "blocked_other_seven_no_upload_authorized",
    youtube_action_approval_read: "blocked_other_seven_no_upload_authorized",
    mp4_render_read: "blocked_pending_human_keep_on_html_review",
  };
  manifest.rough_assembly_reads = {
    ...(manifest.rough_assembly_reads || {}),
    source_credit_gap_static_read: "pass_source_credit_gap_static_qa",
    source_credit_timing_read: "pass_source_credits_clear_at_legal_end_screen_entry",
    source_credit_review_start_read: "pass_source_credit_review_starts_before_fade_like_challenger",
    selected_review_audio_hash_read: "pass_selected_review_audio_sha_preserved",
    youtube_action_read: "blocked_other_seven_no_upload_authorized",
    mp4_created_read: "blocked_pending_human_keep_on_html_review",
  };
  manifest.proof_artifacts = {
    ...(manifest.proof_artifacts || {}),
    source_predecessor_root: summary.output_root,
    player_html_path: playerPath,
    player_html_sha256: sha256File(playerPath),
    review_player_html_path: reviewPlayerPath,
    review_html_path: reviewIndexPath,
    proof_build_json_path: proofBuildPath,
    proof_build_json_sha256: sha256File(proofBuildPath),
    source_credit_gap_static_qa_path: staticQaPath,
    inherited_audio_regression_guard_path: inheritedAudioGuard.guardPath,
    source_credit_catalog_path: SOURCE_CATALOG_PATH,
    source_credit_catalog_sha256: sha256File(SOURCE_CATALOG_PATH),
  };
  manifest.qa = {
    ...(manifest.qa || {}),
    source_credit_gap_static_pass: true,
    source_credit_names_pass: true,
    source_credit_timing_pass: true,
    selected_review_audio_hash_static_pass: true,
    upload_allowed: false,
    upload_performed: false,
  };
  return manifest;
}

function reviewIndex({ episode, reviewPlayerPath, timing, legalFadeStart, reviewStartSeconds, proofBuildId }) {
  const relHref = path.relative(path.dirname(path.dirname(reviewPlayerPath)), reviewPlayerPath).split(path.sep).join("/");
  const href = `${relHref}?t=${encodeURIComponent(formatReviewTime(reviewStartSeconds))}&range_guard=${encodeURIComponent(proofBuildId)}`;
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(episode.title)} Source Credit Gap Review</title>
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
    <h1>${escapeHtml(episode.title)} Source Credit Gap Review</h1>
    <p>This HTML successor adds only the centered source-credit gap treatment. Legal end-screen timing, borderless placeholders, selected review audio, captions, and YouTube state remain unchanged.</p>
    <a class="review-link" href="${href}">
      <strong>Open ${escapeHtml(episode.title)} review</strong>
      <span>Review opens at <code>${formatReviewTime(reviewStartSeconds)}s</code>; source credits begin at <code>${timing.fade_start_seconds.toFixed(3)}s</code> and clear before legal end-screen entry at <code>${Number(legalFadeStart).toFixed(3)}s</code>.</span>
    </a>
  </main>
</body>
</html>
`;
}

function rolloutIndex({ indexPath, summaries }) {
  const rows = summaries
    .map((summary) => {
      const relHref = path.relative(path.dirname(indexPath), summary.review_player_path).split(path.sep).join("/");
      const href = `${relHref}?t=${encodeURIComponent(formatReviewTime(summary.review_start_seconds))}&range_guard=${encodeURIComponent(summary.review_proof_build_id)}`;
      return `<tr><td>${escapeHtml(summary.title)}</td><td><a href="${href}">HTML review</a></td><td>${formatReviewTime(summary.review_start_seconds)}s</td><td>${summary.source_credit_timing.fade_start_seconds.toFixed(3)}s</td><td>${summary.fade_start_seconds.toFixed(3)}s</td><td>${escapeHtml(summary.source_labels.join("; "))}</td></tr>`;
    })
    .join("\n");
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Other Seven Source Credit Gap Reviews</title>
  <style>
    :root { color-scheme: dark; --bg: #050817; --ink: #f7efe1; --muted: #aeb8ce; --line: rgba(247,239,225,.16); --panel: rgba(17,23,47,.78); --accent: #78dce8; }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; background: var(--bg); color: var(--ink); font: 15px/1.5 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    main { width: min(1260px, calc(100vw - 40px)); margin: 0 auto; padding: 44px 0 52px; }
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
    <h1>Other Seven Source Credit Gap Reviews</h1>
    <p>These HTML proofs preserve each episode's legal-timed borderless end-screen review and selected audio mix, adding only the centered source-credit gap content. No MP4 render or YouTube upload was performed.</p>
    <table>
      <thead><tr><th>Episode</th><th>Review</th><th>Opens At</th><th>Sources In</th><th>End Screen In</th><th>Source Labels</th></tr></thead>
      <tbody>
${rows}
      </tbody>
    </table>
  </main>
</body>
</html>
`;
}

function buildEpisode({ summary, catalog, stamp, createdUtc }) {
  if (!OTHER_SEVEN.has(summary.episode_id)) throw new Error(`Unexpected episode ${summary.episode_id}`);
  const catalogEntry = catalog.episodes?.[summary.episode_id];
  validateCatalogEntry(summary.episode_id, catalogEntry);
  const sourceRoot = summary.output_root;
  const sourceManifestPath = summary.manifest_path || path.join(sourceRoot, "rough_assembly_manifest.json");
  const sourcePlayerPath = summary.player_path || path.join(sourceRoot, "player.html");
  if (!fs.existsSync(sourceManifestPath)) throw new Error(`${summary.episode_id}: missing source manifest ${sourceManifestPath}`);
  if (!fs.existsSync(sourcePlayerPath)) throw new Error(`${summary.episode_id}: missing source player ${sourcePlayerPath}`);
  const sourceManifest = readJson(sourceManifestPath);
  const sourceAudio = selectedAudio(summary, sourceManifest);
  const inheritedAudioGuard = readInheritedAudioGuard(summary);
  const sourceHtml = fs.readFileSync(sourcePlayerPath, "utf8");
  const sourceEndScreen = parseConstJson(sourceHtml, "CE_END_SCREEN");
  const legalFadeStart = Number(summary.fade_start_seconds);
  const legalFullOpacity = Number(summary.full_opacity_seconds);
  if (Math.abs(Number(sourceEndScreen.transitionStartSeconds) - legalFadeStart) > 0.001) {
    throw new Error(`${summary.episode_id}: source legal fade start mismatch`);
  }
  if (Math.abs(Number(sourceEndScreen.fullOpacityAtSeconds) - legalFullOpacity) > 0.001) {
    throw new Error(`${summary.episode_id}: source legal full opacity mismatch`);
  }
  const timing = sourceCreditTiming(legalFadeStart);
  const reviewStartSeconds = sourceCreditReviewStart(timing);
  const outputRoot = path.join(path.dirname(sourceRoot), `${summary.episode_id}_legal_borderless_source_credit_gap_successor_${stamp}`);
  const reviewDir = path.join(outputRoot, "review");
  const htmlReviewDir = path.join(outputRoot, "html_review", REVIEW_SUBDIR);
  const qaDir = path.join(outputRoot, "qa");
  resetDir(outputRoot);
  ensureDir(reviewDir);
  ensureDir(htmlReviewDir);
  ensureDir(qaDir);
  linkRuntimeTargets(sourceRoot, outputRoot);
  linkRuntimeTargets(sourceRoot, htmlReviewDir);

  const compactStamp = stamp.replace("T", "");
  const proofBuildId = `${summary.episode_id}-source-credit-gap_${compactStamp}`;
  const proofBuildIdReview = `${proofBuildId}_html_review`;
  const manifestPath = path.join(outputRoot, "rough_assembly_manifest.json");
  const playerPath = path.join(outputRoot, "player.html");
  const proofBuildPath = path.join(outputRoot, "proof_build.json");
  const reviewPlayerPath = path.join(htmlReviewDir, "player.html");
  const reviewProofBuildPath = path.join(htmlReviewDir, "proof_build.json");
  const reviewIndexPath = path.join(reviewDir, `${summary.episode_id}_source_credit_gap_review.html`);
  const sourceCreditGap = {
    model: MODEL,
    source_labels: catalogEntry.source_labels,
    source_selection_basis: catalogEntry.source_selection_basis,
    provenance_paths: catalogEntry.provenance_paths || [],
    external_provenance_urls: catalogEntry.external_provenance_urls || [],
    timing,
    review_start_model: REVIEW_START_MODEL,
    review_start_seconds: reviewStartSeconds,
    review_context_before_source_credit_seconds: REVIEW_CONTEXT_BEFORE_SOURCE_CREDIT_SECONDS,
    legal_end_screen_fade_start_seconds: legalFadeStart,
    legal_end_screen_full_opacity_seconds: legalFullOpacity,
    audio_changed: false,
    end_screen_timing_changed: false,
    placeholder_style_changed: false,
    mp4_render_created: false,
    upload_performed: false,
  };

  const patchedPlayer = patchPlayerHtml({
    html: sourceHtml,
    summary,
    catalogEntry,
    timing,
    legalFullOpacitySeconds: legalFullOpacity,
    reviewStartSeconds,
    proofBuildId,
    createdUtc,
    proofBuildJsonPath: "proof_build.json",
  });
  const patchedReviewPlayer = patchPlayerHtml({
    html: sourceHtml,
    summary,
    catalogEntry,
    timing,
    legalFullOpacitySeconds: legalFullOpacity,
    reviewStartSeconds,
    proofBuildId: proofBuildIdReview,
    createdUtc,
    proofBuildJsonPath: "proof_build.json",
  });
  writeText(playerPath, patchedPlayer);
  writeText(reviewPlayerPath, patchedReviewPlayer);
  patchProofBuild({
    sourceProofBuildPath: path.join(sourceRoot, "proof_build.json"),
    outputPath: proofBuildPath,
    proofBuildId,
    createdUtc,
    manifestPath,
    playerPath,
    sourceCreditGap,
  });
  patchProofBuild({
    sourceProofBuildPath: path.join(sourceRoot, "proof_build.json"),
    outputPath: reviewProofBuildPath,
    proofBuildId: proofBuildIdReview,
    createdUtc,
    manifestPath,
    playerPath: reviewPlayerPath,
    sourceCreditGap,
  });
  writeText(
    reviewIndexPath,
    reviewIndex({ episode: summary, reviewPlayerPath, timing, legalFadeStart, reviewStartSeconds, proofBuildId: proofBuildIdReview }),
  );
  const { qaPath, qa } = staticQa({
    summary,
    playerPath,
    reviewPlayerPath,
    proofBuildPath,
    reviewProofBuildPath,
    expectedProofBuildId: proofBuildId,
    expectedReviewProofBuildId: proofBuildIdReview,
    createdUtc,
    reviewStartSeconds,
    manifestPath,
    sourceManifest,
    sourceAudio,
    inheritedAudioGuard,
    catalogEntry,
    timing,
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
    inheritedAudioGuard,
    catalogEntry,
    timing,
    reviewStartSeconds,
    staticQaPath: qaPath,
  });
  writeJson(manifestPath, manifest);
  const finalStaticQa = readJson(qaPath);
  finalStaticQa.manifest_sha256_after_write = sha256File(manifestPath);
  writeJson(qaPath, finalStaticQa);
  writeText(
    path.join(reviewDir, `${summary.episode_id}_source_credit_gap_review_packet.md`),
    [
      `# ${summary.title} Source Credit Gap Successor`,
      "",
      `- Review player: ${reviewPlayerPath}`,
      `- Predecessor root: ${sourceRoot}`,
      `- Source-credit model: ${MODEL}`,
      `- Source credits: ${catalogEntry.source_labels.join("; ")}`,
      `- Review opens at: ${formatReviewTime(reviewStartSeconds)}s`,
      `- Source-credit fade: ${timing.fade_start_seconds.toFixed(3)}s -> ${timing.full_opacity_seconds.toFixed(3)}s`,
      `- Source-credit clear: ${timing.fade_out_start_seconds.toFixed(3)}s -> ${timing.fade_out_end_seconds.toFixed(3)}s`,
      `- Legal end-screen entry remains: ${legalFadeStart.toFixed(3)}s`,
      `- Selected review audio: ${sourceAudio.path}`,
      `- Selected review audio SHA: ${sourceAudio.sha256}`,
      `- Inherited audio regression guard: ${inheritedAudioGuard.guardPath}`,
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
    proof_build_id: proofBuildId,
    review_proof_build_id: proofBuildIdReview,
    review_start_model: REVIEW_START_MODEL,
    review_start_seconds: reviewStartSeconds,
    manifest_path: manifestPath,
    player_path: playerPath,
    review_player_path: reviewPlayerPath,
    review_player_url: reviewUrlForPath(reviewPlayerPath, {
      t: formatReviewTime(reviewStartSeconds),
      range_guard: proofBuildIdReview,
    }),
    review_index_path: reviewIndexPath,
    review_index_url: reviewUrlForPath(reviewIndexPath),
    source_credit_model: MODEL,
    source_credit_timing: timing,
    source_labels: catalogEntry.source_labels,
    source_selection_basis: catalogEntry.source_selection_basis,
    provenance_paths: catalogEntry.provenance_paths || [],
    external_provenance_urls: catalogEntry.external_provenance_urls || [],
    fade_start_seconds: legalFadeStart,
    full_opacity_seconds: legalFullOpacity,
    selected_audio_path: sourceAudio.path,
    selected_audio_sha256: sourceAudio.sha256,
    inherited_audio_guard_path: inheritedAudioGuard.guardPath,
    inherited_audio_guard_sha256: inheritedAudioGuard.sha256,
    static_qa_path: qaPath,
    static_qa_passed: qa.passed,
    may_youtube_action: false,
    upload_performed: false,
    mp4_render_created: false,
  };
}

function main() {
  const args = parseArgs(process.argv);
  const createdUtc = new Date().toISOString();
  const sourceRollout = readJson(SOURCE_ROLLOUT_MANIFEST);
  const catalog = readJson(SOURCE_CATALOG_PATH);
  const selected = (sourceRollout.episodes || []).filter((summary) => OTHER_SEVEN.has(summary.episode_id));
  if (selected.length !== OTHER_SEVEN.size) {
    throw new Error(`Expected ${OTHER_SEVEN.size} episodes, found ${selected.length}`);
  }
  const summaries = selected.map((summary) => buildEpisode({ summary, catalog, stamp: args.stamp, createdUtc }));
  const outputIndexPath = path.join(EPISODES_ROOT, `other-seven-source-credit-gap-review-${args.stamp}.html`);
  writeText(outputIndexPath, rolloutIndex({ indexPath: outputIndexPath, summaries }));
  const manifestPath = path.join(EPISODES_ROOT, `other-seven-source-credit-gap-review-${args.stamp}.json`);
  writeJson(manifestPath, {
    rollout_id: `other_seven_source_credit_gap_successors_${args.stamp}`,
    created_utc: createdUtc,
    scope: "other_seven_html_review_only_no_render_no_upload",
    predecessor_rollout_manifest_path: SOURCE_ROLLOUT_MANIFEST,
    predecessor_rollout_manifest_sha256: sha256File(SOURCE_ROLLOUT_MANIFEST),
    source_credit_catalog_path: SOURCE_CATALOG_PATH,
    source_credit_catalog_sha256: sha256File(SOURCE_CATALOG_PATH),
    source_credit_model: MODEL,
    source_credit_review_start_model: REVIEW_START_MODEL,
    legal_timing_model: "youtube_legal_window_end_screen_entry_v1",
    placeholder_style_model: "youtube_placeholder_borderless_underlay_v1",
    review_index_path: outputIndexPath,
    review_index_url: reviewUrlForPath(outputIndexPath),
    mp4_render_created: false,
    may_youtube_action: false,
    upload_performed: false,
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
          review_start_seconds: summary.review_start_seconds,
          source_credit_fade_start_seconds: summary.source_credit_timing.fade_start_seconds,
          legal_fade_start_seconds: summary.fade_start_seconds,
          static_qa_passed: summary.static_qa_passed,
        })),
      },
      null,
      2,
    ),
  );
}

main();
