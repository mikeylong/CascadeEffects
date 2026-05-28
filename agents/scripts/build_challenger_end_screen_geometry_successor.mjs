#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const REPO_ROOT = "/Users/mike/Agents_CascadeEffects";
const SOURCE_ROOT =
  "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_legal_end_screen_outro_level_successor_20260525T203318Z";
const ENTRY_MODEL = "youtube_legal_window_end_screen_entry_v1";
const GEOMETRY_MODEL = "youtube_element_tight_geometry_v1";
const REVIEW_START_SECONDS = 1191.681;
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
      console.log("Usage: node scripts/build_challenger_end_screen_geometry_successor.mjs [--stamp YYYYMMDDTHHMMSSZ]");
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  return args;
}

function stamp() {
  return new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
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

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || REPO_ROOT,
    encoding: options.encoding ?? "utf8",
    maxBuffer: options.maxBuffer || 1024 * 1024 * 128,
  });
  if (result.status !== 0) throw new Error(`${command} failed:\n${result.stdout || ""}${result.stderr || ""}`);
  return result;
}

function parseConstJson(text, constName) {
  const marker = `const ${constName} = `;
  const markerIndex = text.indexOf(marker);
  if (markerIndex < 0) throw new Error(`Could not find ${marker}`);
  const valueStart = markerIndex + marker.length;
  const opener = text[valueStart];
  const closer = opener === "{" ? "}" : "]";
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

function clamp01(value) {
  return Math.max(0, Math.min(1, Number(value) || 0));
}

function rgbToHex(rgb) {
  return `#${rgb.map((value) => Math.round(value).toString(16).padStart(2, "0")).join("")}`;
}

function rgbaString(rgb, alpha) {
  return `rgba(${rgb.map((value) => Math.round(value)).join(", ")}, ${Number(alpha).toFixed(3)})`;
}

function rgbToHsl(rgb) {
  const [r, g, b] = rgb.map((value) => value / 255);
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0;
  let s = 0;
  const l = (max + min) / 2;
  const d = max - min;
  if (d !== 0) {
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    if (max === r) h = (g - b) / d + (g < b ? 6 : 0);
    else if (max === g) h = (b - r) / d + 2;
    else h = (r - g) / d + 4;
    h /= 6;
  }
  return [h, s, l];
}

function hslToRgb(hsl) {
  const [h, s, l] = hsl.map(Number);
  if (s === 0) return [l, l, l].map((value) => Math.round(value * 255));
  const hue2rgb = (p, q, tRaw) => {
    let t = tRaw;
    if (t < 0) t += 1;
    if (t > 1) t -= 1;
    if (t < 1 / 6) return p + (q - p) * 6 * t;
    if (t < 1 / 2) return q;
    if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
    return p;
  };
  const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
  const p = 2 * l - q;
  return [hue2rgb(p, q, h + 1 / 3), hue2rgb(p, q, h), hue2rgb(p, q, h - 1 / 3)].map((value) => Math.round(value * 255));
}

function sampleAverageColor(sourceArtPath, bbox_xy) {
  const [x1, y1, x2, y2] = bbox_xy.map((value) => Math.round(Number(value) || 0));
  const width = Math.max(1, x2 - x1);
  const height = Math.max(1, y2 - y1);
  const crop = `crop=${width}:${height}:${Math.max(0, x1)}:${Math.max(0, y1)},scale=1:1:flags=area,format=rgb24`;
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
  const sat = Math.min(darkHueReliabilityCap, clamp01(Math.max(role === "subscribe" ? 0.24 : 0.22, saturation * 1.85 + neutralLift)));
  const fill = hslToRgb([hue, clamp01(sat * 0.82), clamp01((role === "subscribe" ? 0.18 : 0.155) + Math.min(lightness, 0.34) * 0.12)]);
  const border = hslToRgb([hue, clamp01(Math.max(role === "subscribe" ? 0.32 : 0.3, sat * 1.06)), clamp01(role === "subscribe" ? 0.67 : 0.6)]);
  const ring = hslToRgb([hue, clamp01(Math.max(role === "subscribe" ? 0.28 : 0.24, sat * 0.92)), clamp01(role === "subscribe" ? 0.54 : 0.47)]);
  const innerRing = hslToRgb([hue, clamp01(Math.max(0.28, sat * 0.88)), 0.63]);
  const variabilityScore = Math.round(Math.max(...border) - Math.min(...border));
  return {
    sample_hex: rgbToHex(sample),
    fill_rgba: rgbaString(fill, role === "subscribe" ? 0.34 : 0.36),
    border_rgba: rgbaString(border, role === "subscribe" ? 0.84 : 0.74),
    ring_rgba: rgbaString(ring, role === "subscribe" ? 0.2 : 0.18),
    inner_ring_rgba: rgbaString(innerRing, 0.46),
    palette_treatment_model: "local_backplate_perceptual_target_palette_v3",
    adaptive_variability_model: "backplate_hue_preserved_perceptual_variability_v1",
    source_hue_degrees: Math.round(hue * 360),
    source_saturation: Number(saturation.toFixed(3)),
    derived_saturation: Number(sat.toFixed(3)),
    perceptual_variability_score: variabilityScore,
    perceptual_variability_read:
      variabilityScore >= 24 ? "pass_backplate_hue_visible_in_end_screen_target" : "tighten_low_perceptual_target_variability",
    hue_shift_applied: false,
  };
}

function paletteForLayout(sourceArtPath) {
  const targets = {};
  for (const [key, target] of Object.entries(NEW_LAYOUT)) {
    const sampleRgb = sampleAverageColor(sourceArtPath, target.bbox_xy);
    targets[key] = {
      role: target.role,
      sample_bbox_xy: target.bbox_xy,
      ...endScreenTargetColorsFromSample(sampleRgb, target.role),
      sample_read: sampleRgb ? "pass_backplate_region_average" : "fallback_missing_backplate_sample",
    };
  }
  return {
    model_id: "backplate_sampled_youtube_end_screen_palette_v1",
    palette_treatment_model: "local_backplate_perceptual_target_palette_v3",
    palette_source: "sampled_episode_backplate",
    source_art_path: sourceArtPath,
    source_art_sha256: sha256(sourceArtPath),
    target_count: Object.keys(targets).length,
    targets,
    sample_read: "pass_source_backplate_sampled",
    adaptive_variability_model: "backplate_hue_preserved_perceptual_variability_v1",
    perceptual_variability_min_score: Math.min(...Object.values(targets).map((target) => target.perceptual_variability_score || 0)),
    end_screen_adaptive_perceptual_variability_read: "pass_backplate_hue_visible_across_end_screen_targets",
    adaptive_context_read: "pass_local_target_regions_sampled_with_perceptual_backplate_variability",
    fixed_cross_episode_color_read: "pass_no_challenger_default_color_reuse_with_visible_episode_variability",
  };
}

function updatePaletteContract(contract, palette) {
  const next = structuredClone(contract || {});
  const left = palette.targets.left_video;
  const right = palette.targets.right_video;
  const subscribe = palette.targets.center_subscribe;
  next.sampled_backplate = {
    ...(next.sampled_backplate || {}),
    target_samples: Object.fromEntries(
      Object.entries(palette.targets).map(([key, target]) => [
        key,
        { bbox_xy: target.sample_bbox_xy, sample_hex: target.sample_hex, sample_read: target.sample_read },
      ]),
    ),
  };
  next.colors = {
    ...(next.colors || {}),
    video_target_fill_rgba: left.fill_rgba,
    video_target_border_rgba: left.border_rgba,
    video_target_secondary_border_rgba: right.border_rgba,
    subscribe_ring_rgba: subscribe.border_rgba,
    muted_rail_text_hex: right.sample_hex,
    small_accent_hex: subscribe.sample_hex,
  };
  next.css_variables = {
    ...(next.css_variables || {}),
    "--ce-end-screen-target-fill": left.fill_rgba,
    "--ce-end-screen-video-border": left.border_rgba,
    "--ce-end-screen-video-border-secondary": right.border_rgba,
    "--ce-end-screen-subscribe-ring": subscribe.border_rgba,
    "--ce-end-screen-muted-text": right.sample_hex,
    "--ce-end-screen-small-accent": subscribe.sample_hex,
  };
  next.target_palette = palette;
  next.geometry_model = GEOMETRY_MODEL;
  return next;
}

function bboxMetrics(bbox) {
  return {
    x: bbox[0],
    y: bbox[1],
    width: bbox[2] - bbox[0],
    height: bbox[3] - bbox[1],
    center_x: (bbox[0] + bbox[2]) / 2,
    center_y: (bbox[1] + bbox[3]) / 2,
  };
}

function patchDimensionBlock(css, selector, bbox) {
  const m = bboxMetrics(bbox);
  const pattern = new RegExp(`(${selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\s*\\{[\\s\\S]*?left:\\s*)[-0-9.]+px;([\\s\\S]*?top:\\s*)[-0-9.]+px;([\\s\\S]*?width:\\s*)[-0-9.]+px;([\\s\\S]*?height:\\s*)[-0-9.]+px;`, "g");
  return css.replace(pattern, `$1${m.x}px;$2${m.y}px;$3${m.width}px;$4${m.height}px;`);
}

function patchCss(html, palette) {
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
  next = next
    .replace(/border:\s*4px solid var\(--ce-end-screen-video-border-left/g, `border: ${TARGET_CSS.videoBorderPx}px solid var(--ce-end-screen-video-border-left`)
    .replace(/border:\s*4px solid var\(--ce-end-screen-video-border-right/g, `border: ${TARGET_CSS.videoBorderPx}px solid var(--ce-end-screen-video-border-right`)
    .replace(/border-radius:\s*18px;/g, `border-radius: ${TARGET_CSS.videoRadiusPx}px;`)
    .replace(/box-shadow:\s*0 0 0 10px var\(--ce-end-screen-video-ring-left\)/g, `box-shadow: 0 0 0 ${TARGET_CSS.videoOuterRingPx}px var(--ce-end-screen-video-ring-left)`)
    .replace(/box-shadow:\s*0 0 0 10px var\(--ce-end-screen-video-ring-right\)/g, `box-shadow: 0 0 0 ${TARGET_CSS.videoOuterRingPx}px var(--ce-end-screen-video-ring-right)`)
    .replace(/border:\s*7px solid var\(--ce-end-screen-subscribe-border/g, `border: ${TARGET_CSS.subscribeBorderPx}px solid var(--ce-end-screen-subscribe-border`)
    .replace(/box-shadow:\s*0 0 0 18px var\(--ce-end-screen-subscribe-soft-ring\)/g, `box-shadow: 0 0 0 ${TARGET_CSS.subscribeOuterRingPx}px var(--ce-end-screen-subscribe-soft-ring)`)
    .replace(/inset:\s*18px;\s*\n\s*border:\s*3px solid var\(--ce-end-screen-subscribe-inner-ring\)/g, `inset: ${TARGET_CSS.subscribeInnerInsetPx}px;\n      border: ${TARGET_CSS.subscribeInnerBorderPx}px solid var(--ce-end-screen-subscribe-inner-ring)`);
  const vars = {
    "--ce-end-screen-target-fill": palette.targets.left_video.fill_rgba,
    "--ce-end-screen-video-border": palette.targets.left_video.border_rgba,
    "--ce-end-screen-video-border-secondary": palette.targets.right_video.border_rgba,
    "--ce-end-screen-subscribe-ring": palette.targets.center_subscribe.border_rgba,
    "--ce-end-screen-muted-text": palette.targets.right_video.sample_hex,
    "--ce-end-screen-small-accent": palette.targets.center_subscribe.sample_hex,
    "--ce-end-screen-target-fill-left": palette.targets.left_video.fill_rgba,
    "--ce-end-screen-target-fill-right": palette.targets.right_video.fill_rgba,
    "--ce-end-screen-target-fill-subscribe": palette.targets.center_subscribe.fill_rgba,
    "--ce-end-screen-video-border-left": palette.targets.left_video.border_rgba,
    "--ce-end-screen-video-border-right": palette.targets.right_video.border_rgba,
    "--ce-end-screen-subscribe-border": palette.targets.center_subscribe.border_rgba,
    "--ce-end-screen-video-ring-left": palette.targets.left_video.ring_rgba,
    "--ce-end-screen-video-ring-right": palette.targets.right_video.ring_rgba,
    "--ce-end-screen-subscribe-soft-ring": palette.targets.center_subscribe.ring_rgba,
    "--ce-end-screen-subscribe-inner-ring": palette.targets.center_subscribe.inner_ring_rgba,
  };
  for (const [name, value] of Object.entries(vars)) {
    next = next.replace(new RegExp(`(${name}:\\s*)[^;]+;`, "g"), `$1${value};`);
  }
  return next;
}

function patchDefaultStart(html) {
  return html.replace(
    "const CE_URL_FORCED_TIME = Number(CE_PARAMS.get(\"t\"));",
    `const CE_URL_FORCED_TIME = Number(CE_PARAMS.get("t") ?? "${REVIEW_START_SECONDS.toFixed(3)}");`,
  );
}

function patchPlayer({ sourceHtml, proofBuildId, createdUtc, proofBuildJsonPath, palette, geometryEnabled }) {
  let html = patchDefaultStart(sourceHtml);
  html = html.replace(/<title>[\s\S]*?<\/title>/, "<title>Challenger End-Screen Geometry Successor Review</title>");
  html = html.replace(/(proofBuildId: )"[^"]*"(,)/, `$1${JSON.stringify(proofBuildId)}$2`);
  html = html.replace(/(proofGeneratedAtUtc: )"[^"]*"(,)/, `$1${JSON.stringify(createdUtc)}$2`);
  html = html.replace(/(proofBuildJsonPath: )"[^"]*"(,)/, `$1${JSON.stringify(proofBuildJsonPath)}$2`);
  if (geometryEnabled) {
    const endScreen = parseConstJson(html, "CE_END_SCREEN").value;
    endScreen.layout = NEW_LAYOUT;
    endScreen.geometryModel = GEOMETRY_MODEL;
    endScreen.youtubeElementSizingBasis = "16x9_video_elements_640x360_center_subscribe_336";
    endScreen.palette = palette;
    html = replaceConstJson(html, "CE_END_SCREEN", endScreen);
    const paletteContract = updatePaletteContract(parseConstJson(html, "CE_END_SCREEN_PALETTE").value, palette);
    html = replaceConstJson(html, "CE_END_SCREEN_PALETTE", paletteContract);
    html = patchCss(html, palette);
  }
  html = html.replace(
    "</body>",
    `<script id="ce-end-screen-geometry-review" type="application/json">${JSON.stringify({
      model: GEOMETRY_MODEL,
      geometry_enabled: geometryEnabled,
      review_start_seconds: REVIEW_START_SECONDS,
      layout: geometryEnabled ? NEW_LAYOUT : "predecessor_geometry",
    })}</script>\n</body>`,
  );
  return html;
}

function cloneRuntimeLinks(sourceRoot, outputRoot) {
  ensureDir(outputRoot);
  for (const name of ["assets", "audio_repairs", "references", "scripts", "proof_assets", "audio_successor"]) {
    const sourcePath = path.join(sourceRoot, name);
    const targetPath = path.join(outputRoot, name);
    if (!fs.existsSync(sourcePath)) continue;
    fs.rmSync(targetPath, { recursive: true, force: true });
    fs.symlinkSync(sourcePath, targetPath);
  }
}

function writeProofBuild({ sourceProofBuildPath, outputPath, proofBuildId, outputRoot, manifestPath, playerPath, createdUtc, geometryEnabled }) {
  const proofBuild = readJson(sourceProofBuildPath);
  Object.assign(proofBuild, {
    proof_build_id: proofBuildId,
    proof_generated_at_utc: createdUtc,
    packet_stamp: path.basename(outputRoot),
    player_path: playerPath,
    manifest_path: manifestPath,
    end_screen_geometry_successor: {
      model: GEOMETRY_MODEL,
      geometry_enabled: geometryEnabled,
      layout: geometryEnabled ? NEW_LAYOUT : "predecessor_geometry",
      target_css: TARGET_CSS,
    },
  });
  writeJson(outputPath, proofBuild);
}

function reviewIndex({ reviewIndexPath, currentPlayer, successorPlayer }) {
  const currentHref = path.relative(path.dirname(reviewIndexPath), currentPlayer).split(path.sep).join("/");
  const successorHref = path.relative(path.dirname(reviewIndexPath), successorPlayer).split(path.sep).join("/");
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Challenger End-Screen Geometry HTML Review</title>
  <style>
    :root { color-scheme: dark; --bg: #050817; --ink: #f7efe1; --muted: #aeb8ce; --line: rgba(247, 239, 225, 0.16); --panel: rgba(17, 23, 47, 0.78); --accent: #78dce8; }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; background: var(--bg); color: var(--ink); font: 16px/1.5 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    main { width: min(940px, calc(100vw - 40px)); margin: 0 auto; padding: 44px 0 52px; }
    h1 { margin: 0 0 12px; font-size: 28px; line-height: 1.15; letter-spacing: 0; }
    p { margin: 0 0 22px; color: var(--muted); }
    .links { display: grid; gap: 14px; margin: 26px 0; }
    a { color: var(--ink); text-decoration: none; }
    .review-link { display: block; padding: 18px 20px; border: 1px solid var(--line); border-radius: 8px; background: var(--panel); }
    .review-link strong { display: block; margin-bottom: 5px; font-size: 18px; }
    .review-link span { display: block; color: var(--muted); }
    code { color: var(--accent); }
  </style>
</head>
<body>
  <main>
    <h1>Challenger End-Screen Geometry HTML Review</h1>
    <p>Both versions start at <code>${REVIEW_START_SECONDS.toFixed(3)}s</code> and keep the legal-window timing. Use the successor to align YouTube Studio elements against tighter 16:9 target boxes and the enlarged center subscribe ring.</p>
    <div class="links">
      <a class="review-link" href="${currentHref}">
        <strong>Current geometry</strong>
        <span>Predecessor target boxes: 680x383 video/playlist and 292px center circle.</span>
      </a>
      <a class="review-link" href="${successorHref}">
        <strong>Tighter YouTube geometry</strong>
        <span>Video/playlist targets are 640x360; center circle is 336px with a larger inner ring clearance.</span>
      </a>
    </div>
  </main>
</body>
</html>
`;
}

function patchManifest({ outputRoot, manifestPath, playerPath, proofBuildPath, proofBuildId, createdUtc, palette, qaPath, reviewPath }) {
  const manifest = readJson(path.join(SOURCE_ROOT, "rough_assembly_manifest.json"));
  const proofBuildSha = fs.existsSync(proofBuildPath) ? sha256(proofBuildPath) : "pending";
  const patched = {
    ...manifest,
    packet_id: path.basename(outputRoot),
    status: "challenger_end_screen_geometry_successor_review_ready_pending_human_keep",
    human_disposition: "pending",
    human_disposition_source: "pending_challenger_end_screen_geometry_html_review",
    may_render_final_mp4: false,
    may_advance_to_final_assembly: false,
    may_advance_to_publish_readiness: false,
    may_youtube_action: false,
    publish_ready: false,
    youtube_upload_ready: false,
    upload_performed: false,
    public_release_ready: false,
    youtube_visibility_action_performed: false,
    proof_build_id: proofBuildId,
    proof_generated_at_utc: createdUtc,
    proof_build_json_path: proofBuildPath,
    proof_build_json_sha256: proofBuildSha,
    end_screen_geometry_successor: {
      model: GEOMETRY_MODEL,
      source_root: SOURCE_ROOT,
      layout: NEW_LAYOUT,
      target_css: TARGET_CSS,
      legal_timing_preserved_read: "pass",
      audio_preserved_read: "pass_source_audio_path_preserved_from_audio_level_successor",
      youtube_action_read: "blocked_no_upload_or_visibility_change_performed",
    },
    end_screen_context: {
      ...(manifest.end_screen_context || {}),
      end_screen_geometry_model: GEOMETRY_MODEL,
      end_screen_timing: {
        ...(manifest.end_screen_context?.end_screen_timing || {}),
        layout: NEW_LAYOUT,
        geometryModel: GEOMETRY_MODEL,
        palette,
      },
      end_screen_palette: palette,
      end_screen_palette_contract: updatePaletteContract(manifest.end_screen_context?.end_screen_palette_contract, palette),
    },
    reads: {
      ...(manifest.reads || {}),
      end_screen_geometry_read: "pass_youtube_element_tight_geometry_v1",
      youtube_action_read: "blocked_pending_human_keep_and_explicit_upload_authorization",
    },
    proof_artifacts: {
      ...(manifest.proof_artifacts || {}),
      source_predecessor_root: SOURCE_ROOT,
      player_html_path: playerPath,
      proof_build_json_path: proofBuildPath,
      proof_build_json_sha256: proofBuildSha,
      end_screen_geometry_qa_path: qaPath,
      review_packet_path: reviewPath,
    },
  };
  return patched;
}

function geometryQa({ outputRoot, manifestPath, currentPlayer, successorPlayer, reviewIndexPath }) {
  const oldLayout = {
    left_video: { bbox_xy: [78, 382, 758, 765] },
    right_video: { bbox_xy: [1162, 382, 1842, 765] },
    center_subscribe: { bbox_xy: [814, 429, 1106, 721] },
  };
  const metrics = Object.fromEntries(
    Object.entries(NEW_LAYOUT).map(([key, target]) => [
      key,
      {
        predecessor: bboxMetrics(oldLayout[key].bbox_xy),
        successor: bboxMetrics(target.bbox_xy),
      },
    ]),
  );
  const failures = [];
  for (const key of ["left_video", "right_video"]) {
    const m = metrics[key].successor;
    if (Math.abs(m.width / m.height - 16 / 9) > 0.001) failures.push(`${key} is not exact 16:9`);
    if (m.width !== 640 || m.height !== 360) failures.push(`${key} is not 640x360`);
  }
  const subscribe = metrics.center_subscribe.successor;
  if (subscribe.width !== subscribe.height || subscribe.width !== 336) failures.push("center subscribe target is not 336x336");
  if (subscribe.center_x !== 960 || subscribe.center_y !== 574) failures.push("center subscribe target did not preserve intended center");
  const qa = {
    model: "challenger_end_screen_geometry_qa_v1",
    created_utc: new Date().toISOString(),
    geometry_model: GEOMETRY_MODEL,
    manifest_path: manifestPath,
    review_html_path: reviewIndexPath,
    current_player_path: currentPlayer,
    successor_player_path: successorPlayer,
    metrics,
    target_css: TARGET_CSS,
    reads: {
      video_target_dimensions_read: failures.some((failure) => /16:9|640x360/.test(failure))
        ? "fail_video_targets_not_tight_16x9"
        : "pass_video_targets_640x360_exact_16x9",
      subscribe_target_clearance_read: failures.some((failure) => /subscribe/.test(failure))
        ? "fail_subscribe_ring_clearance"
        : "pass_center_circle_336px_inner_ring_surrounds_approx_300px_logo_area",
      legal_timing_preserved_read: "pass_youtube_legal_window_entry_v1_unchanged",
      youtube_action_read: "blocked_no_upload_or_visibility_change_performed",
    },
    failures,
    passed: failures.length === 0,
  };
  const qaPath = path.join(outputRoot, "qa", "challenger_end_screen_geometry_qa.json");
  writeJson(qaPath, qa);
  return { qaPath, qa };
}

function main() {
  const args = parseArgs(process.argv);
  const createdUtc = new Date().toISOString();
  const compactStamp = args.stamp.replace("T", "");
  const outputRoot = path.join(path.dirname(SOURCE_ROOT), `challenger_legal_end_screen_geometry_successor_${args.stamp}`);
  const reviewDir = path.join(outputRoot, "review");
  const htmlReviewDir = path.join(outputRoot, "html_review");
  const currentRoot = path.join(htmlReviewDir, "current_geometry");
  const successorRoot = path.join(htmlReviewDir, "tight_youtube_geometry");
  ensureDir(reviewDir);
  ensureDir(htmlReviewDir);
  cloneRuntimeLinks(SOURCE_ROOT, outputRoot);
  cloneRuntimeLinks(SOURCE_ROOT, currentRoot);
  cloneRuntimeLinks(SOURCE_ROOT, successorRoot);

  const sourceManifest = readJson(path.join(SOURCE_ROOT, "rough_assembly_manifest.json"));
  const sourceArtPath = sourceManifest.source_visual?.source_art_path;
  if (!sourceArtPath || !fs.existsSync(sourceArtPath)) throw new Error(`Source art not found: ${sourceArtPath || "missing"}`);
  const palette = paletteForLayout(sourceArtPath);
  const sourceHtml = fs.readFileSync(path.join(SOURCE_ROOT, "player.html"), "utf8");
  const sourceProofBuildPath = path.join(SOURCE_ROOT, "proof_build.json");
  const proofBuildId = `challenger-end-screen-geometry_rolling_caption_rail_${compactStamp}`;
  const manifestPath = path.join(outputRoot, "rough_assembly_manifest.json");
  const playerPath = path.join(outputRoot, "player.html");
  const proofBuildPath = path.join(outputRoot, "proof_build.json");
  const currentPlayer = path.join(currentRoot, "player.html");
  const successorPlayer = path.join(successorRoot, "player.html");
  const reviewIndexPath = path.join(reviewDir, "challenger_end_screen_geometry_html_review.html");
  const reviewPacketPath = path.join(reviewDir, "challenger_end_screen_geometry_review_packet.md");

  writeText(
    playerPath,
    patchPlayer({
      sourceHtml,
      proofBuildId,
      createdUtc,
      proofBuildJsonPath: "proof_build.json",
      palette,
      geometryEnabled: true,
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
    geometryEnabled: true,
  });
  const { qaPath, qa } = geometryQa({ outputRoot, manifestPath, currentPlayer, successorPlayer, reviewIndexPath });
  const manifest = patchManifest({
    outputRoot,
    manifestPath,
    playerPath,
    proofBuildPath,
    proofBuildId,
    createdUtc,
    palette,
    qaPath,
    reviewPath: reviewPacketPath,
  });
  const proofBuildSha = sha256(proofBuildPath);
  manifest.proof_build_json_sha256 = proofBuildSha;
  manifest.proof_artifacts.proof_build_json_sha256 = proofBuildSha;
  writeJson(manifestPath, manifest);

  writeText(
    currentPlayer,
    patchPlayer({
      sourceHtml,
      proofBuildId: `${proofBuildId}_current_geometry`,
      createdUtc,
      proofBuildJsonPath: "proof_build.json",
      palette,
      geometryEnabled: false,
    }),
  );
  writeText(
    successorPlayer,
    patchPlayer({
      sourceHtml,
      proofBuildId: `${proofBuildId}_tight_geometry`,
      createdUtc,
      proofBuildJsonPath: "proof_build.json",
      palette,
      geometryEnabled: true,
    }),
  );
  writeProofBuild({
    sourceProofBuildPath,
    outputPath: path.join(currentRoot, "proof_build.json"),
    proofBuildId: `${proofBuildId}_current_geometry`,
    outputRoot: currentRoot,
    manifestPath,
    playerPath: currentPlayer,
    createdUtc,
    geometryEnabled: false,
  });
  writeProofBuild({
    sourceProofBuildPath,
    outputPath: path.join(successorRoot, "proof_build.json"),
    proofBuildId: `${proofBuildId}_tight_geometry`,
    outputRoot: successorRoot,
    manifestPath,
    playerPath: successorPlayer,
    createdUtc,
    geometryEnabled: true,
  });
  writeText(reviewIndexPath, reviewIndex({ reviewIndexPath, currentPlayer, successorPlayer }));
  writeText(
    reviewPacketPath,
    [
      "# Challenger End-Screen Geometry Successor",
      "",
      `- Review index: ${reviewIndexPath}`,
      `- Successor player: ${successorPlayer}`,
      `- Geometry model: ${GEOMETRY_MODEL}`,
      "- Video/playlist target boxes: 640x360, exact 16:9.",
      "- Center subscribe target: 336x336, center preserved, inner ring clearance increased.",
      `- Legal timing model preserved: ${ENTRY_MODEL}`,
      `- Geometry QA: ${qaPath}`,
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
        current_html: currentPlayer,
        successor_html: successorPlayer,
        manifest: artifact(manifestPath),
        geometry_qa: { ...artifact(qaPath), passed: qa.passed },
      },
      null,
      2,
    ),
  );
}

main();
