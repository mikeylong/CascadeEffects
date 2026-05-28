#!/usr/bin/env node
import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import {
  CHALLENGER_PRECISION_MATTE,
  challengerPrecisionMatteGuard,
} from "./challenger_precision_matte_guard.mjs";

const VISUAL_SOURCE_ROOT = CHALLENGER_PRECISION_MATTE.proofRoot;
const NON_MASK_DELTA_SOURCE_ROOT =
  "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_legal_end_screen_borderless_successor_20260525T223138Z";
const APPROVED_AUDIO_SOURCE_ROOT =
  "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_legal_end_screen_outro_level_successor_20260525T203318Z";
const STYLE_MODEL = "youtube_placeholder_borderless_underlay_v1";
const ENTRY_MODEL = "youtube_legal_window_end_screen_entry_v1";
const GEOMETRY_MODEL = "youtube_element_tight_geometry_v1";
const EXPECTED_AUDIO_SHA = "81174cc27fcbfc67f006dda89c9cf0c467103203a88f6faab2ba97e6209eebca";
const EXPECTED_FADE_START_SECONDS = 1191.680884;
const EXPECTED_FULL_OPACITY_SECONDS = 1191.980884;
const REVIEW_START_SECONDS = EXPECTED_FADE_START_SECONDS;
const LAST_CAPTION_VISIBLE_EXIT_SECONDS = 1183;
const LAST_CAPTION_FULLY_SUPPRESSED_SECONDS = 1190.655556;
const NEW_LAYOUT = {
  left_video: { role: "suggested_video", bbox_xy: [98, 394, 738, 754], aspect_ratio: "16:9" },
  right_video: { role: "watch_next_video", bbox_xy: [1182, 394, 1822, 754], aspect_ratio: "16:9" },
  center_subscribe: { role: "subscribe", bbox_xy: [792, 406, 1128, 742] },
};
const TARGET_CSS = {
  videoBorderPx: 3,
  videoRadiusPx: 14,
  videoOuterRingPx: 6,
  subscribeBorderPx: 6,
  subscribeOuterRingPx: 12,
  subscribeInnerInsetPx: 14,
  subscribeInnerBorderPx: 3,
};
const APPROVED_AUDIO_RELATIVE_PATH = "audio_successor/challenger_right_rail_alignment_music_mix_outro_plus5db_after_vo.wav";

function stamp() {
  return new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
}

function parseArgs(argv) {
  const args = { stamp: stamp() };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = () => {
      i += 1;
      if (i >= argv.length) throw new Error(`Missing value for ${arg}`);
      return argv[i];
    };
    if (arg === "--stamp") args.stamp = next();
    else if (arg === "--help" || arg === "-h") {
      console.log("Usage: node scripts/build_challenger_end_screen_borderless_successor.mjs [--stamp YYYYMMDDTHHMMSSZ]");
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  return args;
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJson(filePath, data) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`, "utf8");
}

function writeText(filePath, text) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, text, "utf8");
}

function sha256(filePath) {
  return createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function artifact(filePath) {
  return {
    path: filePath,
    sha256: fs.existsSync(filePath) ? sha256(filePath) : "missing",
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
  let inString = false;
  let escaped = false;
  for (let i = valueStart; i < text.length; i += 1) {
    const char = text[i];
    if (inString) {
      if (escaped) escaped = false;
      else if (char === "\\") escaped = true;
      else if (char === '"') inString = false;
      continue;
    }
    if (char === '"') {
      inString = true;
      continue;
    }
    if (char === opener) depth += 1;
    else if (char === closer) {
      depth -= 1;
      if (depth === 0) return { value: JSON.parse(text.slice(valueStart, i + 1)), start: valueStart, end: i + 1 };
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
  if (!pattern.test(text)) throw new Error(`Could not replace numeric CE_CONFIG key ${key}`);
  return text.replace(pattern, `$1${Number(Number(value).toFixed(6))}$2`);
}

function replaceConfigString(text, key, value) {
  const pattern = new RegExp(`(${key}: )"[^"]*"(,)`);
  if (!pattern.test(text)) throw new Error(`Could not replace string CE_CONFIG key ${key}`);
  return text.replace(pattern, `$1${JSON.stringify(value)}$2`);
}

function bboxMetrics(bbox) {
  return {
    x: bbox[0],
    y: bbox[1],
    width: bbox[2] - bbox[0],
    height: bbox[3] - bbox[1],
  };
}

function patchDimensionBlock(css, selector, bbox) {
  const metrics = bboxMetrics(bbox);
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pattern = new RegExp(
    `(${escaped}\\s*\\{[\\s\\S]*?left:\\s*)[-0-9.]+px;([\\s\\S]*?top:\\s*)[-0-9.]+px;([\\s\\S]*?width:\\s*)[-0-9.]+px;([\\s\\S]*?height:\\s*)[-0-9.]+px;`,
    "g",
  );
  return css.replace(pattern, `$1${metrics.x}px;$2${metrics.y}px;$3${metrics.width}px;$4${metrics.height}px;`);
}

function patchGeometryCss(html) {
  let next = html;
  for (const [selector, key] of [
    [".youtube-target.left-video", "left_video"],
    [".youtube-target.right-video", "right_video"],
    [".youtube-target.subscribe-target", "center_subscribe"],
    [".ce-youtube-end-screen-target.left-video", "left_video"],
    [".ce-youtube-end-screen-target.right-video", "right_video"],
    [".ce-youtube-end-screen-target.subscribe-target", "center_subscribe"],
  ]) {
    next = patchDimensionBlock(next, selector, NEW_LAYOUT[key].bbox_xy);
  }
  return next
    .replace(/border:\s*4px solid var\(--ce-end-screen-video-border-left/g, `border: ${TARGET_CSS.videoBorderPx}px solid var(--ce-end-screen-video-border-left`)
    .replace(/border:\s*4px solid var\(--ce-end-screen-video-border-right/g, `border: ${TARGET_CSS.videoBorderPx}px solid var(--ce-end-screen-video-border-right`)
    .replace(/border-radius:\s*18px;/g, `border-radius: ${TARGET_CSS.videoRadiusPx}px;`)
    .replace(/box-shadow:\s*0 0 0 10px var\(--ce-end-screen-video-ring-left\)/g, `box-shadow: 0 0 0 ${TARGET_CSS.videoOuterRingPx}px var(--ce-end-screen-video-ring-left)`)
    .replace(/box-shadow:\s*0 0 0 10px var\(--ce-end-screen-video-ring-right\)/g, `box-shadow: 0 0 0 ${TARGET_CSS.videoOuterRingPx}px var(--ce-end-screen-video-ring-right)`)
    .replace(/border:\s*7px solid var\(--ce-end-screen-subscribe-border/g, `border: ${TARGET_CSS.subscribeBorderPx}px solid var(--ce-end-screen-subscribe-border`)
    .replace(/box-shadow:\s*0 0 0 18px var\(--ce-end-screen-subscribe-soft-ring\)/g, `box-shadow: 0 0 0 ${TARGET_CSS.subscribeOuterRingPx}px var(--ce-end-screen-subscribe-soft-ring)`)
    .replace(/inset:\s*18px;\s*\n\s*border:\s*3px solid var\(--ce-end-screen-subscribe-inner-ring\)/g, `inset: ${TARGET_CSS.subscribeInnerInsetPx}px;\n      border: ${TARGET_CSS.subscribeInnerBorderPx}px solid var(--ce-end-screen-subscribe-inner-ring)`);
}

function patchDefaultStart(html) {
  return html.replace(
    "const CE_URL_FORCED_TIME = Number(CE_PARAMS.get(\"t\"));",
    `const CE_URL_FORCED_TIME = Number(CE_PARAMS.get("t") ?? "${REVIEW_START_SECONDS.toFixed(3)}");`,
  );
}

function patchPrecisionMaskMetadata(html) {
  let next = html.replace(
    /(<img\s+class="mask-reference"\s+id="foregroundOcclusionMatte"\s+src="assets\/masks\/foreground_occlusion_matte\.png)(?:\?v=[^"]*)?(")(?:\s+data-mask-sha256="[^"]*")?/,
    `$1?v=${CHALLENGER_PRECISION_MATTE.maskSha256}$2 data-mask-sha256="${CHALLENGER_PRECISION_MATTE.maskSha256}"`,
  );
  if (!next.includes(`const foregroundMattePrecisionModel = "${CHALLENGER_PRECISION_MATTE.precisionModel}";`)) {
    next = next.replace(
      'const foregroundMattePolicy = "tower_shuttle_only_no_light_or_right_rail_mask";',
      `const foregroundMattePolicy = "tower_shuttle_only_no_light_or_right_rail_mask";\n    const foregroundMattePrecisionModel = "${CHALLENGER_PRECISION_MATTE.precisionModel}";`,
    );
  }
  if (!next.includes("foreground_matte_precision_model: foregroundMattePrecisionModel")) {
    next = next.replace(
      "foreground_matte_policy: foregroundMattePolicy,",
      "foreground_matte_policy: foregroundMattePolicy,\n        foreground_matte_precision_model: foregroundMattePrecisionModel,",
    );
  }
  return next;
}

function patchApprovedAudio(html) {
  return html.replace(/<audio\s+src="[^"]+"/, `<audio src="${APPROVED_AUDIO_RELATIVE_PATH}"`);
}

function addBorderlessStyle(html) {
  const style = `
  <style id="ce-borderless-youtube-placeholder-style">
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
  if (html.includes('id="ce-borderless-youtube-placeholder-style"')) return html;
  return html.replace("</head>", `${style}\n</head>`);
}

function addRangeServerGuard(html) {
  let next = html;
  const style = `
  <style id="ce-byte-range-review-server-guard-style">
    html.render-mode .ce-range-server-warning {
      display: none !important;
    }
    .ce-range-server-warning {
      position: fixed;
      z-index: 2147483647;
      left: 18px;
      top: 18px;
      max-width: min(620px, calc(100vw - 36px));
      padding: 12px 14px;
      color: #fff6e2;
      background: rgba(122, 45, 20, 0.96);
      border: 1px solid rgba(255, 207, 129, 0.76);
      border-radius: 8px;
      box-shadow: 0 10px 34px rgba(0,0,0,0.36);
      font: 760 14px/1.35 Inter, ui-sans-serif, system-ui, sans-serif;
    }
    .ce-range-server-warning[hidden] {
      display: none !important;
    }
    .ce-range-server-warning code,
    .ce-range-server-warning span {
      display: block;
      margin-top: 4px;
      color: rgba(255, 246, 226, 0.86);
      font-weight: 560;
      font-size: 12px;
    }
  </style>`;
  if (!next.includes('id="ce-byte-range-review-server-guard-style"')) {
    next = next.replace("</head>", `${style}\n</head>`);
  }
  const script = `
<script id="ce-byte-range-review-server-guard">
(() => {
  const MODEL = "byte_range_required_local_review_server_v1";
  function findAudio() {
    return document.getElementById("audio") || document.querySelector("audio");
  }
  function escapeHtml(value) {
    return String(value || "").replace(/[<>&]/g, (char) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;" }[char]));
  }
  function installRangeServerWarning() {
    if (document.documentElement.classList.contains("render-mode")) return null;
    let warning = document.querySelector(".ce-range-server-warning");
    if (warning) return warning;
    warning = document.createElement("aside");
    warning.className = "ce-range-server-warning";
    warning.setAttribute("role", "status");
    warning.setAttribute("aria-live", "polite");
    warning.hidden = true;
    warning.innerHTML = 'This review is not being served by the byte-range server.<span>Run <code>node scripts/range_static_server.mjs 8766 /Users/mike/Episodes_CascadeEffects</code>, then reload this page.</span>';
    document.body.appendChild(warning);
    return warning;
  }
  function setRangeServerWarning(detail) {
    const warning = installRangeServerWarning();
    if (!warning) return false;
    warning.hidden = false;
    warning.innerHTML = 'This review is not being served by the byte-range server.<span>' + escapeHtml(detail || "range probe failed") + '</span><code>node scripts/range_static_server.mjs 8766 /Users/mike/Episodes_CascadeEffects</code>';
    window.__ceReviewRangeServerState.warning_visible = true;
    return true;
  }
  async function verifyReviewRangeServer() {
    const audio = findAudio();
    const source = audio ? (audio.currentSrc || audio.src || "") : "";
    const state = {
      model: MODEL,
      source,
      page_protocol: window.location.protocol,
      status: "pending",
      http_status: null,
      accept_ranges: "",
      content_range: "",
      range_server_read: "pending_byte_range_probe",
      warning_visible: false,
    };
    window.__ceReviewRangeServerState = state;
    if (document.documentElement.classList.contains("render-mode") || !audio || !source) {
      state.status = "skipped";
      state.range_server_read = document.documentElement.classList.contains("render-mode") ? "not_applicable_render_mode" : "not_applicable_no_audio_source";
      return state;
    }
    if (window.location.protocol === "file:") {
      state.status = "failed";
      state.range_server_read = "fail_file_protocol_no_byte_range_server";
      setRangeServerWarning("file:// review pages cannot satisfy late audio/video seeking.");
      return state;
    }
    try {
      const response = await fetch(source, { headers: { Range: "bytes=0-1023" }, cache: "no-store" });
      state.http_status = response.status;
      state.accept_ranges = response.headers.get("accept-ranges") || "";
      state.content_range = response.headers.get("content-range") || "";
      const ok = response.status === 206 && /bytes/i.test(state.accept_ranges) && /^bytes\\s+\\d+-\\d+\\/\\d+/i.test(state.content_range);
      state.status = ok ? "passed" : "failed";
      state.range_server_read = ok ? "pass_http_206_partial_content_byte_range_server" : "fail_missing_http_206_partial_content_byte_range_server";
      const warning = document.querySelector(".ce-range-server-warning");
      if (ok && warning) warning.hidden = true;
      if (!ok) setRangeServerWarning("range probe returned status " + response.status + ", accept-ranges " + (state.accept_ranges || "missing") + ", content-range " + (state.content_range || "missing") + ".");
    } catch (error) {
      state.status = "failed";
      state.range_server_read = "fail_byte_range_probe_exception";
      state.error = error && error.message ? String(error.message) : String(error);
      setRangeServerWarning(state.error);
    }
    return state;
  }
  window.__ceVerifyReviewRangeServer = verifyReviewRangeServer;
  window.addEventListener("load", () => {
    setTimeout(verifyReviewRangeServer, 0);
  });
})();
</script>`;
  if (!next.includes('id="ce-byte-range-review-server-guard"')) {
    next = next.replace("</body>", `${script}\n</body>`);
  }
  return next;
}

function patchPlayer({ sourceHtml, proofBuildId, createdUtc, proofBuildJsonPath, reviewRole }) {
  let html = patchDefaultStart(sourceHtml);
  html = html.replace(/<title>[\s\S]*?<\/title>/, "<title>Challenger Borderless End-Screen Review</title>");
  html = html.replace(/(proofBuildId: )"[^"]*"(,)/, `$1${JSON.stringify(proofBuildId)}$2`);
  html = html.replace(/(proofGeneratedAtUtc: )"[^"]*"(,)/, `$1${JSON.stringify(createdUtc)}$2`);
  html = html.replace(/(proofBuildJsonPath: )"[^"]*"(,)/, `$1${JSON.stringify(proofBuildJsonPath)}$2`);

  const endScreen = parseConstJson(html, "CE_END_SCREEN").value;
  Object.assign(endScreen, {
    fadeTimingModel: ENTRY_MODEL,
    transitionStartSeconds: EXPECTED_FADE_START_SECONDS,
    transitionDurationSeconds: 0.3,
    fullOpacityAtSeconds: EXPECTED_FULL_OPACITY_SECONDS,
    holdStartSeconds: EXPECTED_FULL_OPACITY_SECONDS,
    safeWindowStartSeconds: EXPECTED_FADE_START_SECONDS,
    layout: NEW_LAYOUT,
    timingSource: "kept_precision_matte_repair+youtube_legal_window_end_screen_entry_v1",
    reviewApprovedEndScreenEntryModel: ENTRY_MODEL,
    reviewApprovedFadeStartSeconds: EXPECTED_FADE_START_SECONDS,
    captionEndScreenHandoffModel: ENTRY_MODEL,
    lastCaptionVisibleExitStartSeconds: LAST_CAPTION_VISIBLE_EXIT_SECONDS,
    lastCaptionFullySuppressedSeconds: LAST_CAPTION_FULLY_SUPPRESSED_SECONDS,
    youtubePlaceholderFadeStartSeconds: EXPECTED_FADE_START_SECONDS,
    youtubePlaceholderFullOpacitySeconds: EXPECTED_FULL_OPACITY_SECONDS,
    captionEndScreenGapSeconds: 1.025328,
    captionEndScreenOverlapRead: "pass_youtube_legal_window_entry_after_caption_suppression",
    endScreenEntryTimingModel: ENTRY_MODEL,
    geometryModel: GEOMETRY_MODEL,
    youtubeElementSizingBasis: "16x9_video_elements_640x360_center_subscribe_336",
  });
  endScreen.placeholderStyleModel = STYLE_MODEL;
  endScreen.outlineModel = STYLE_MODEL;
  endScreen.borderlessUnderlay = {
    enabled: true,
    removed: ["css_border", "outer_glow_ring", "inset_glow_ring", "subscribe_inner_ring"],
    fill_preserved: true,
    timing_changed: false,
    geometry_changed: false,
  };
  html = replaceConstJson(html, "CE_END_SCREEN", endScreen);

  const paletteContract = parseConstJson(html, "CE_END_SCREEN_PALETTE").value;
  paletteContract.placeholder_style_model = STYLE_MODEL;
  paletteContract.outline_model = STYLE_MODEL;
  paletteContract.geometry_model = GEOMETRY_MODEL;
  paletteContract.borderless_underlay = endScreen.borderlessUnderlay;
  html = replaceConstJson(html, "CE_END_SCREEN_PALETTE", paletteContract);
  html = replaceConfigString(html, "captionEndScreenHandoffModel", ENTRY_MODEL);
  html = replaceConfigString(html, "reviewApprovedEndScreenEntryModel", ENTRY_MODEL);
  html = replaceConfigNumber(html, "reviewApprovedEndScreenFadeStartSeconds", EXPECTED_FADE_START_SECONDS);
  html = replaceConfigNumber(html, "lastCaptionVisibleExitStartSeconds", LAST_CAPTION_VISIBLE_EXIT_SECONDS);
  html = replaceConfigNumber(html, "lastCaptionFullySuppressedSeconds", LAST_CAPTION_FULLY_SUPPRESSED_SECONDS);
  html = replaceConfigNumber(html, "youtubePlaceholderFadeStartSeconds", EXPECTED_FADE_START_SECONDS);
  html = replaceConfigNumber(html, "youtubePlaceholderFullOpacitySeconds", EXPECTED_FULL_OPACITY_SECONDS);
  html = replaceConfigNumber(html, "youtubePlaceholderTransitionDurationSeconds", 0.3);
  html = replaceConfigNumber(html, "captionEndScreenGapSeconds", 1.025328);
  html = replaceConfigString(html, "captionEndScreenOverlapRead", "pass_youtube_legal_window_entry_after_caption_suppression");
  html = patchGeometryCss(html);
  html = patchApprovedAudio(html);
  html = patchPrecisionMaskMetadata(html);
  html = addBorderlessStyle(html);
  html = addRangeServerGuard(html);
  html = html.replace(
    "</body>",
    `<script id="ce-borderless-placeholder-review" type="application/json">${JSON.stringify({
      model: STYLE_MODEL,
      review_role: reviewRole,
      legal_timing_model: ENTRY_MODEL,
      geometry_model: GEOMETRY_MODEL,
      review_start_seconds: REVIEW_START_SECONDS,
      removed: endScreen.borderlessUnderlay.removed,
      fill_preserved: true,
      geometry_changed: false,
      timing_changed: false,
      audio_changed: false,
      approved_audio_sha256: EXPECTED_AUDIO_SHA,
    })}</script>\n</body>`,
  );
  return html;
}

function cloneRuntimeLinks(sourceRoot, outputRoot) {
  ensureDir(outputRoot);
  for (const name of ["assets", "audio_repairs", "references", "scripts", "proof_assets"]) {
    const sourcePath = path.join(sourceRoot, name);
    const targetPath = path.join(outputRoot, name);
    if (!fs.existsSync(sourcePath)) continue;
    fs.rmSync(targetPath, { recursive: true, force: true });
    fs.symlinkSync(sourcePath, targetPath);
  }
  const audioSourcePath = path.join(APPROVED_AUDIO_SOURCE_ROOT, "audio_successor");
  if (fs.existsSync(audioSourcePath)) {
    const audioTargetPath = path.join(outputRoot, "audio_successor");
    fs.rmSync(audioTargetPath, { recursive: true, force: true });
    fs.symlinkSync(audioSourcePath, audioTargetPath);
  }
}

function writeProofBuild({ sourceProofBuildPath, outputPath, proofBuildId, outputRoot, manifestPath, playerPath, createdUtc }) {
  const proofBuild = readJson(sourceProofBuildPath);
  Object.assign(proofBuild, {
    proof_build_id: proofBuildId,
    proof_generated_at_utc: createdUtc,
    packet_stamp: path.basename(outputRoot),
    player_path: playerPath,
    manifest_path: manifestPath,
    visual_source_root: VISUAL_SOURCE_ROOT,
    non_mask_delta_source_root: NON_MASK_DELTA_SOURCE_ROOT,
    end_screen_placeholder_style_successor: {
      model: STYLE_MODEL,
      visual_source_root: VISUAL_SOURCE_ROOT,
      non_mask_delta_source_root: NON_MASK_DELTA_SOURCE_ROOT,
      removed: ["css_border", "outer_glow_ring", "inset_glow_ring", "subscribe_inner_ring"],
      fill_preserved: true,
      geometry_changed: false,
      timing_changed: false,
      audio_changed: false,
    },
  });
  writeJson(outputPath, proofBuild);
}

function validateSourceManifest(sourceManifest) {
  const failures = [];
  const audioPath = sourceManifest.approved_audio?.path || "";
  const audioSha = audioPath && fs.existsSync(audioPath) ? sha256(audioPath) : "missing";
  if (sourceManifest.episode_id !== "challenger") failures.push("source manifest is not Challenger");
  if (sourceManifest.approved_audio?.sha256 !== EXPECTED_AUDIO_SHA) failures.push("approved audio manifest sha mismatch");
  if (audioSha !== EXPECTED_AUDIO_SHA) failures.push("approved audio file sha mismatch");
  if (sourceManifest.end_screen_context?.end_screen_timing?.fadeTimingModel !== ENTRY_MODEL) {
    failures.push("source timing model is not youtube legal-window entry");
  }
  if (Math.abs(Number(sourceManifest.youtube_placeholder_fade_start_seconds) - EXPECTED_FADE_START_SECONDS) > 0.001) {
    failures.push("source fade start changed");
  }
  if (Math.abs(Number(sourceManifest.youtube_placeholder_full_opacity_seconds) - EXPECTED_FULL_OPACITY_SECONDS) > 0.001) {
    failures.push("source full-opacity timestamp changed");
  }
  return { failures, audioPath, audioSha };
}

function borderlessQa({ outputRoot, manifestPath, playerPath, reviewPlayerPath, reviewIndexPath, sourceManifest, precisionGuard }) {
  const sourceCheck = validateSourceManifest(sourceManifest);
  const html = fs.readFileSync(playerPath, "utf8");
  const endScreen = parseConstJson(html, "CE_END_SCREEN").value;
  const palette = parseConstJson(html, "CE_END_SCREEN_PALETTE").value;
  const failures = [...sourceCheck.failures];
  if (endScreen.placeholderStyleModel !== STYLE_MODEL) failures.push("CE_END_SCREEN does not record borderless style model");
  if (palette.placeholder_style_model !== STYLE_MODEL) failures.push("CE_END_SCREEN_PALETTE does not record borderless style model");
  if (!/ce-borderless-youtube-placeholder-style/.test(html)) failures.push("borderless CSS override is missing");
  if (!/border:\s*0\s*!important/.test(html)) failures.push("borderless CSS override does not zero borders");
  if (!/box-shadow:\s*none\s*!important/.test(html)) failures.push("borderless CSS override does not remove glow rings");
  if (!/subscribe-target::after[\s\S]*?display:\s*none\s*!important/.test(html)) {
    failures.push("subscribe inner ring pseudo-element is not hidden");
  }
  const sourceLayout = sourceManifest.end_screen_context?.end_screen_timing?.layout || {};
  const htmlLayout = endScreen.layout || {};
  if (JSON.stringify(sourceLayout) !== JSON.stringify(htmlLayout)) failures.push("end-screen geometry changed");
  if (endScreen.fadeTimingModel && endScreen.fadeTimingModel !== ENTRY_MODEL) failures.push("HTML timing model changed");
  if (!precisionGuard?.ok) failures.push("Challenger precision matte guard failed");

  const qa = {
    model: "challenger_borderless_end_screen_html_static_qa_v1",
    created_utc: new Date().toISOString(),
    placeholder_style_model: STYLE_MODEL,
    manifest_path: manifestPath,
    canonical_player_path: playerPath,
    review_player_path: reviewPlayerPath,
    review_html_path: reviewIndexPath,
    visual_source_root: VISUAL_SOURCE_ROOT,
    non_mask_delta_source_root: NON_MASK_DELTA_SOURCE_ROOT,
    challenger_precision_matte_guard: precisionGuard,
    source_audio_path: sourceCheck.audioPath,
    expected_audio_sha256: EXPECTED_AUDIO_SHA,
    observed_audio_sha256: sourceCheck.audioSha,
    fade_start_seconds: EXPECTED_FADE_START_SECONDS,
    full_opacity_seconds: EXPECTED_FULL_OPACITY_SECONDS,
    removed: ["css_border", "outer_glow_ring", "inset_glow_ring", "subscribe_inner_ring"],
    failures,
    passed: failures.length === 0,
    reads: {
      end_screen_placeholder_style_read: failures.length
        ? "fail_youtube_placeholder_borderless_underlay_v1"
        : "pass_youtube_placeholder_borderless_underlay_v1",
      end_screen_outline_removal_read: failures.length
        ? "fail_visible_placeholder_outline_removal"
        : "pass_borders_glow_rings_inset_rings_and_subscribe_inner_ring_removed",
      end_screen_fill_preservation_read: "pass_translucent_target_fills_preserved",
      end_screen_geometry_preservation_read: failures.some((failure) => /geometry/.test(failure))
        ? "fail_tight_geometry_changed"
        : "pass_tight_geometry_unchanged",
      end_screen_legal_timing_preservation_read: failures.some((failure) => /timing|fade/.test(failure))
        ? "fail_youtube_legal_window_entry_changed"
        : "pass_youtube_legal_window_entry_v1_unchanged",
      challenger_audio_regression_guard_read: sourceCheck.failures.some((failure) => /audio/.test(failure))
        ? "fail_plus5db_successor_audio_sha_mismatch"
        : "pass_plus5db_successor_audio_sha_preserved_no_remix",
      challenger_precision_matte_guard_read:
        precisionGuard?.reads?.challenger_precision_matte_guard_read || "fail_challenger_precision_matte_guard_missing",
      youtube_action_read: "blocked_no_upload_or_visibility_change_performed",
    },
  };
  const qaPath = path.join(outputRoot, "qa", "challenger_borderless_end_screen_static_qa.json");
  writeJson(qaPath, qa);
  return { qaPath, qa };
}

function reviewIndex({ reviewIndexPath, reviewPlayerPath }) {
  const reviewHref = path.relative(path.dirname(reviewIndexPath), reviewPlayerPath).split(path.sep).join("/");
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Challenger Borderless End-Screen HTML Review</title>
  <style>
    :root { color-scheme: dark; --bg: #050817; --ink: #f7efe1; --muted: #aeb8ce; --line: rgba(247, 239, 225, 0.16); --panel: rgba(17, 23, 47, 0.78); --accent: #78dce8; }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; background: var(--bg); color: var(--ink); font: 16px/1.5 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    main { width: min(920px, calc(100vw - 40px)); margin: 0 auto; padding: 44px 0 52px; }
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
    <h1>Challenger Borderless End-Screen HTML Review</h1>
    <p>This successor removes only the visible YouTube placeholder outlines. It keeps tight geometry, legal-window timing, captions, metadata, and the approved +5 dB Challenger outro audio unchanged.</p>
    <a class="review-link" href="${reviewHref}">
      <strong>Open borderless Challenger review</strong>
      <span>Starts at <code>${REVIEW_START_SECONDS.toFixed(3)}s</code>; fade begins at the legal last-20s entry and reaches full opacity at <code>${EXPECTED_FULL_OPACITY_SECONDS.toFixed(3)}s</code>.</span>
    </a>
  </main>
</body>
</html>
`;
}

function patchManifest({
  sourceManifest,
  outputRoot,
  manifestPath,
  playerPath,
  reviewPlayerPath,
  reviewIndexPath,
  proofBuildPath,
  proofBuildId,
  createdUtc,
  qaPath,
  reviewPacketPath,
  precisionGuard,
}) {
  const predecessorReview = {
    visual_source_root: VISUAL_SOURCE_ROOT,
    non_mask_delta_source_root: NON_MASK_DELTA_SOURCE_ROOT,
    source_status: sourceManifest.status || "",
    source_human_disposition: sourceManifest.human_disposition || "",
    source_youtube_upload_result: sourceManifest.youtube_upload_result || null,
    source_youtube_unlisted_review: sourceManifest.youtube_unlisted_review || null,
    source_publish_readiness_package: sourceManifest.publish_readiness_package || null,
    source_rendered_video_proof: sourceManifest.rendered_video_proof || null,
  };
  const manifest = structuredClone(sourceManifest);
  Object.assign(manifest, {
    packet_id: path.basename(outputRoot),
    status: "challenger_borderless_end_screen_html_review_ready_pending_human_keep",
    human_disposition: "pending",
    human_disposition_source: "pending_challenger_borderless_end_screen_html_review",
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
    user_approval: {
      created_utc: createdUtc,
      source: "html_review_repair_preflight",
      text: "Repaired precision-matte borderless legal-timed Challenger HTML review is pending human approval.",
      allowed_actions: ["html_review"],
      public_release_allowed: false,
    },
    human_keep_recorded_at: null,
    human_keep_record: null,
    production_contract: {
      contract_id: "first-eight-longform-v1",
      intent: "successor",
      status: "blocked_html_review_pending_human_keep",
      youtube_action_approval_read: "blocked_pending_human_keep_and_explicit_upload_authorization",
      render_approval_read: "blocked_pending_human_keep",
      public_release_ready_read: "blocked_public_release_manual",
    },
    source_html_proof: {
      packet_path: outputRoot,
      manifest_path: manifestPath,
      player_path: playerPath,
      player_sha256: sha256(playerPath),
      current_proof_render_source_read: "blocked_html_review_pending_human_keep",
      current_kept_proof_render_source_read: "blocked_html_review_pending_human_keep",
      corrective_review_render_from_unkept_proof: false,
      challenger_precision_matte_guard: precisionGuard,
    },
    youtube_upload_request: {
      requested_at: createdUtc,
      requested_action: "none_html_review_only",
      disposition: "blocked_pending_challenger_borderless_html_approval",
      reason: "Borderless end-screen successor is HTML-review only until human approval.",
      next_valid_action: "review_challenger_borderless_html_keep_tighten_or_reject",
    },
    proof_build_id: proofBuildId,
    proof_generated_at_utc: createdUtc,
    proof_build_json_path: proofBuildPath,
    proof_build_json_sha256: fs.existsSync(proofBuildPath) ? sha256(proofBuildPath) : "pending",
    end_screen_placeholder_style_model: STYLE_MODEL,
    end_screen_placeholder_style_successor: {
      model: STYLE_MODEL,
      visual_source_root: VISUAL_SOURCE_ROOT,
      non_mask_delta_source_root: NON_MASK_DELTA_SOURCE_ROOT,
      style_delta: "remove_visible_placeholder_outlines_only",
      removed: ["css_border", "outer_glow_ring", "inset_glow_ring", "subscribe_inner_ring"],
      fill_preserved: true,
      geometry_changed: false,
      timing_changed: false,
      audio_changed: false,
      approved_audio_path: sourceManifest.approved_audio?.path || "",
      approved_audio_sha256: EXPECTED_AUDIO_SHA,
      mp4_render_guard_required_before_render: true,
      youtube_action_read: "blocked_no_upload_or_visibility_change_performed",
    },
    challenger_precision_matte_guard: precisionGuard,
    foreground_matte_policy: "tower_shuttle_only_no_light_or_right_rail_mask",
    foreground_matte_precision_model: CHALLENGER_PRECISION_MATTE.precisionModel,
    foreground_matte_path: path.join(outputRoot, CHALLENGER_PRECISION_MATTE.maskRelativePath),
    foreground_matte_sha256: CHALLENGER_PRECISION_MATTE.maskSha256,
    precision_matte_human_disposition: "keep",
    precision_matte_keep_receipt_path: CHALLENGER_PRECISION_MATTE.keepReceiptPath,
    precision_matte_keep_receipt_sha256: sha256(CHALLENGER_PRECISION_MATTE.keepReceiptPath),
    source_lineage: {
      visual_source_root: VISUAL_SOURCE_ROOT,
      non_mask_delta_source_root: NON_MASK_DELTA_SOURCE_ROOT,
      resolved_assets_realpath: precisionGuard?.observed?.assets_realpath || "",
      resolved_mask_realpath: precisionGuard?.observed?.mask_realpath || "",
      approved_audio_source_root: APPROVED_AUDIO_SOURCE_ROOT,
      stale_predecessor_blocked_mask_sha256: "48ebac2e7e4b8737cc56e884d902211ee574781b7363eb24c9799afa3606d208",
    },
    review_server: {
      model: "byte_range_required_local_review_server_v1",
      command: "node scripts/range_static_server.mjs 8766 /Users/mike/Episodes_CascadeEffects",
      required_probe_header: "Range: bytes=0-1023",
      required_probe_status: 206,
      required_response_headers: ["Accept-Ranges: bytes", "Content-Range"],
      range_server_guard: "embedded_in_player_html",
    },
    html_range_server_read: "pending_browser_range_server_probe_before_human_review",
    html_native_audio_scrub_read: "pending_browser_range_server_probe_before_human_review",
    predecessor_review_context: predecessorReview,
  });

  manifest.end_screen_context = manifest.end_screen_context || {};
  manifest.end_screen_context.end_screen_placeholder_style_model = STYLE_MODEL;
  manifest.end_screen_context.end_screen_outline_model = STYLE_MODEL;
  manifest.end_screen_context.end_screen_timing = {
    ...(manifest.end_screen_context.end_screen_timing || {}),
    placeholderStyleModel: STYLE_MODEL,
    outlineModel: STYLE_MODEL,
  };
  manifest.end_screen_context.end_screen_palette_contract = {
    ...(manifest.end_screen_context.end_screen_palette_contract || {}),
    placeholder_style_model: STYLE_MODEL,
    outline_model: STYLE_MODEL,
    borderless_underlay: {
      enabled: true,
      removed: ["css_border", "outer_glow_ring", "inset_glow_ring", "subscribe_inner_ring"],
      fill_preserved: true,
    },
  };
  manifest.reads = {
    ...(manifest.reads || {}),
    end_screen_placeholder_style_read: "pass_youtube_placeholder_borderless_underlay_v1",
    end_screen_outline_removal_read: "pass_borders_glow_rings_inset_rings_and_subscribe_inner_ring_removed",
    end_screen_fill_preservation_read: "pass_translucent_target_fills_preserved",
    end_screen_geometry_preservation_read: "pass_tight_geometry_unchanged",
    end_screen_legal_timing_preservation_read: "pass_youtube_legal_window_entry_v1_unchanged",
    challenger_audio_regression_guard_read: "pass_plus5db_successor_audio_sha_preserved_no_remix",
    challenger_precision_matte_guard_read:
      precisionGuard?.reads?.challenger_precision_matte_guard_read || "fail_challenger_precision_matte_guard_missing",
    challenger_precision_mask_sha_read:
      precisionGuard?.reads?.challenger_precision_mask_sha_read || "fail_mask_sha_not_987d1a96",
    challenger_superseded_mask_block_read:
      precisionGuard?.reads?.challenger_superseded_mask_block_read || "fail_superseded_challenger_mask_active",
    challenger_mask_lineage_read:
      precisionGuard?.reads?.challenger_mask_lineage_read || "fail_mask_does_not_resolve_to_kept_precision_matte_root",
    html_range_server_read: "pending_browser_range_server_probe_before_human_review",
    youtube_action_read: "blocked_pending_human_keep_and_explicit_upload_authorization",
    youtube_action_approval_read: "blocked_pending_human_keep_and_explicit_upload_authorization",
    unlisted_review_upload_approval_read: "blocked_pending_human_keep_and_explicit_upload_authorization",
    final_assembly_human_keep_read: "blocked_pending_human_keep",
    human_final_assembly_keep_read: "blocked_pending_human_keep",
    youtube_unlisted_review_upload_read: "not_applicable_no_upload_performed",
    youtube_unlisted_review_privacy_read: "not_applicable_no_upload_performed",
    youtube_unlisted_upload_status_read: "not_applicable_no_upload_performed",
    youtube_caption_sidecar_upload_read: "not_applicable_no_upload_performed",
    public_release_ready_read: "blocked_public_release_manual",
  };
  manifest.rough_assembly_reads = {
    ...(manifest.rough_assembly_reads || {}),
    mp4_created_read: "blocked_html_review_pending_human_keep",
    youtube_upload_ready_read: "blocked_pending_human_keep_and_explicit_upload_authorization",
    youtube_action_read: "blocked_pending_human_keep_and_explicit_upload_authorization",
    youtube_action_approval_read: "blocked_pending_human_keep_and_explicit_upload_authorization",
    unlisted_review_upload_approval_read: "blocked_pending_human_keep_and_explicit_upload_authorization",
    final_assembly_human_keep_read: "blocked_pending_human_keep",
    human_final_assembly_keep_read: "blocked_pending_human_keep",
    youtube_unlisted_review_upload_read: "not_applicable_no_upload_performed",
    youtube_unlisted_review_privacy_read: "not_applicable_no_upload_performed",
    youtube_unlisted_upload_status_read: "not_applicable_no_upload_performed",
    youtube_caption_sidecar_upload_read: "not_applicable_no_upload_performed",
    public_release_ready_read: "blocked_public_release_manual",
  };
  manifest.proof_artifacts = {
    ...(manifest.proof_artifacts || {}),
    source_predecessor_root: VISUAL_SOURCE_ROOT,
    non_mask_delta_source_root: NON_MASK_DELTA_SOURCE_ROOT,
    resolved_assets_realpath: precisionGuard?.observed?.assets_realpath || "",
    resolved_mask_realpath: precisionGuard?.observed?.mask_realpath || "",
    player_html_path: playerPath,
    review_player_html_path: reviewPlayerPath,
    review_html_path: reviewIndexPath,
    proof_build_json_path: proofBuildPath,
    proof_build_json_sha256: manifest.proof_build_json_sha256,
    borderless_placeholder_qa_path: qaPath,
    review_packet_path: reviewPacketPath,
  };
  return manifest;
}

function main() {
  const args = parseArgs(process.argv);
  const createdUtc = new Date().toISOString();
  const compactStamp = args.stamp.replace("T", "");
  const visualSourceGuard = challengerPrecisionMatteGuard({
    root: VISUAL_SOURCE_ROOT,
    manifestPath: path.join(VISUAL_SOURCE_ROOT, "rough_assembly_manifest.json"),
    playerPath: path.join(VISUAL_SOURCE_ROOT, "player.html"),
    context: "challenger_borderless_successor_visual_source_preflight",
  });
  const outputRoot = path.join(
    path.dirname(VISUAL_SOURCE_ROOT),
    `challenger_precision_matte_legal_end_screen_borderless_successor_${args.stamp}`,
  );
  const reviewDir = path.join(outputRoot, "review");
  const htmlReviewDir = path.join(outputRoot, "html_review", "borderless_youtube_geometry");
  ensureDir(reviewDir);
  ensureDir(htmlReviewDir);
  cloneRuntimeLinks(VISUAL_SOURCE_ROOT, outputRoot);
  cloneRuntimeLinks(VISUAL_SOURCE_ROOT, htmlReviewDir);

  const sourceManifest = readJson(path.join(NON_MASK_DELTA_SOURCE_ROOT, "rough_assembly_manifest.json"));
  const sourceCheck = validateSourceManifest(sourceManifest);
  if (sourceCheck.failures.length) throw new Error(`Source manifest guard failed:\n${sourceCheck.failures.join("\n")}`);

  const proofBuildId = `challenger-borderless-end-screen_rolling_caption_rail_${compactStamp}`;
  const manifestPath = path.join(outputRoot, "rough_assembly_manifest.json");
  const playerPath = path.join(outputRoot, "player.html");
  const proofBuildPath = path.join(outputRoot, "proof_build.json");
  const reviewPlayerPath = path.join(htmlReviewDir, "player.html");
  const reviewProofBuildPath = path.join(htmlReviewDir, "proof_build.json");
  const reviewIndexPath = path.join(reviewDir, "challenger_borderless_end_screen_html_review.html");
  const reviewPacketPath = path.join(reviewDir, "challenger_borderless_end_screen_review_packet.md");
  const sourceHtml = fs.readFileSync(path.join(NON_MASK_DELTA_SOURCE_ROOT, "player.html"), "utf8");
  const sourceReviewHtml = fs.readFileSync(
    path.join(NON_MASK_DELTA_SOURCE_ROOT, "html_review", "borderless_youtube_geometry", "player.html"),
    "utf8",
  );
  const sourceProofBuildPath = path.join(NON_MASK_DELTA_SOURCE_ROOT, "proof_build.json");

  writeText(
    playerPath,
    patchPlayer({
      sourceHtml,
      proofBuildId,
      createdUtc,
      proofBuildJsonPath: "proof_build.json",
      reviewRole: "canonical_borderless_successor",
    }),
  );
  writeText(
    reviewPlayerPath,
    patchPlayer({
      sourceHtml: sourceReviewHtml,
      proofBuildId: `${proofBuildId}_html_review`,
      createdUtc,
      proofBuildJsonPath: "proof_build.json",
      reviewRole: "human_html_review",
    }),
  );
  writeProofBuild({
    sourceProofBuildPath,
    outputPath: proofBuildPath,
    proofBuildId,
    outputRoot,
    manifestPath,
    playerPath,
    createdUtc,
  });
  writeProofBuild({
    sourceProofBuildPath,
    outputPath: reviewProofBuildPath,
    proofBuildId: `${proofBuildId}_html_review`,
    outputRoot: htmlReviewDir,
    manifestPath,
    playerPath: reviewPlayerPath,
    createdUtc,
  });
  writeText(reviewIndexPath, reviewIndex({ reviewIndexPath, reviewPlayerPath }));
  const guardReceiptPath = path.join(outputRoot, "qa", "challenger_precision_matte_guard.json");
  const precisionGuard = challengerPrecisionMatteGuard({
    root: outputRoot,
    playerPath,
    writeReceiptPath: guardReceiptPath,
    context: "challenger_borderless_successor_output_preflight",
  });
  precisionGuard.visual_source_preflight = visualSourceGuard;
  const { qaPath, qa } = borderlessQa({
    outputRoot,
    manifestPath,
    playerPath,
    reviewPlayerPath,
    reviewIndexPath,
    sourceManifest,
    precisionGuard,
  });
  const manifest = patchManifest({
    sourceManifest,
    outputRoot,
    manifestPath,
    playerPath,
    reviewPlayerPath,
    reviewIndexPath,
    proofBuildPath,
    proofBuildId,
    createdUtc,
    qaPath,
    reviewPacketPath,
    precisionGuard,
  });
  manifest.proof_build_json_sha256 = sha256(proofBuildPath);
  manifest.proof_artifacts.proof_build_json_sha256 = manifest.proof_build_json_sha256;
  writeJson(manifestPath, manifest);
  writeText(
    reviewPacketPath,
    [
      "# Challenger Borderless End-Screen Successor",
      "",
      `- Review index: ${reviewIndexPath}`,
      `- Review player: ${reviewPlayerPath}`,
      `- Visual source root: ${VISUAL_SOURCE_ROOT}`,
      `- Non-mask delta source root: ${NON_MASK_DELTA_SOURCE_ROOT}`,
      `- Precision matte guard: ${guardReceiptPath}`,
      `- Precision mask SHA: ${CHALLENGER_PRECISION_MATTE.maskSha256}`,
      `- Placeholder style model: ${STYLE_MODEL}`,
      `- Legal timing model preserved: ${ENTRY_MODEL}`,
      `- Fade start/full opacity: ${EXPECTED_FADE_START_SECONDS.toFixed(3)}s / ${EXPECTED_FULL_OPACITY_SECONDS.toFixed(3)}s`,
      `- Approved audio SHA preserved: ${EXPECTED_AUDIO_SHA}`,
      "- Removed: CSS borders, outer glow rings, inset glow rings, and subscribe inner ring.",
      "- Kept unchanged: translucent fills, tight geometry, legal timing, +5 dB Challenger outro successor audio, captions, and metadata.",
      `- Static QA: ${qaPath}`,
      "",
      "No MP4 render, upload, metadata update, or visibility action was performed.",
      "",
    ].join("\n"),
  );

  console.log(
    JSON.stringify(
      {
        output_root: outputRoot,
        review_html: reviewIndexPath,
        review_player_html: reviewPlayerPath,
        canonical_player_html: playerPath,
        manifest: artifact(manifestPath),
        borderless_static_qa: { ...artifact(qaPath), passed: qa.passed },
        challenger_precision_matte_guard: { ...artifact(guardReceiptPath), passed: precisionGuard.ok },
      },
      null,
      2,
    ),
  );
}

main();
