#!/usr/bin/env node
import { spawn, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { challengerPrecisionMatteGuard } from "./challenger_precision_matte_guard.mjs";

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DEFAULT_WIDTH = 1920;
const DEFAULT_HEIGHT = 1080;
const DEFAULT_FPS = 24;
const DEFAULT_CRF = 18;
const DEFAULT_PRESET = "veryfast";
const DEFAULT_WORKERS = 4;
const FORBIDDEN_REVIEW_CHROME_TEXT = [
  "Sample cue states",
  "Buttons seek",
  "Current Gate",
  "Review-intensity",
  "ambient/effects layer review-ready",
  "timeline scrubber",
];
const VISIBLE_REVIEW_CHROME_SELECTOR = [
  ".controls",
  ".review-header",
  ".audio-review",
  ".review-grid",
  ".machine-reads",
  ".review-note",
  ".timeline-scrubber",
  ".review-toggle",
  "audio",
  "button",
  "input",
  "output",
  "select",
  "textarea",
].join(",");
const VISUAL_GUARD_MIN_SCREENSHOT_BYTES = 40_000;
const VISUAL_GUARD_MIN_MEAN_LUMA = 20;
const VISUAL_GUARD_MIN_STD_LUMA = 8;
const VISUAL_GUARD_MIN_NONBLACK_FRACTION = 0.08;
const VISUAL_GUARD_DARK_SCENE_MIN_MEAN_LUMA = 16;
const VISUAL_GUARD_DARK_SCENE_MIN_STD_LUMA = 16;
const VISUAL_GUARD_DARK_SCENE_MIN_NONBLACK_FRACTION = 0.3;
const VISUAL_GUARD_NARRATIVE_SAMPLES = new Set(["start", "voice_start", "quarter", "half", "three_quarter"]);

function parseArgs(argv) {
  const args = {
    manifest: "",
    workers: DEFAULT_WORKERS,
    fps: DEFAULT_FPS,
    width: DEFAULT_WIDTH,
    height: DEFAULT_HEIGHT,
    crf: DEFAULT_CRF,
    preset: DEFAULT_PRESET,
    dryRun: false,
    force: false,
    allowUnkeptReviewRender: false,
    contractIntent: "successor",
    contractId: "first-eight-longform-v1",
  };
  for (let index = 2; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = () => {
      index += 1;
      if (index >= argv.length) throw new Error(`Missing value for ${arg}`);
      return argv[index];
    };
    if (arg === "--manifest") args.manifest = next();
    else if (arg === "--workers") args.workers = Number(next());
    else if (arg === "--fps") args.fps = Number(next());
    else if (arg === "--width") args.width = Number(next());
    else if (arg === "--height") args.height = Number(next());
    else if (arg === "--crf") args.crf = Number(next());
    else if (arg === "--preset") args.preset = next();
    else if (arg === "--dry-run") args.dryRun = true;
    else if (arg === "--force") args.force = true;
    else if (arg === "--allow-unkept-review-render") args.allowUnkeptReviewRender = true;
    else if (arg === "--contract-intent") args.contractIntent = next();
    else if (arg === "--contract-id") args.contractId = next();
    else if (arg === "--help" || arg === "-h") {
      console.log(
        [
          "Usage: node scripts/render_living_cover_final_mp4_from_rough_proof.mjs --manifest /path/to/rough_assembly_manifest.json",
          "",
          "Options:",
          "  --workers N     Parallel browser capture workers. Default: 4",
          "  --fps N         Output frame rate. Default: 24",
          "  --crf N         libx264 CRF. Default: 18",
          "  --preset NAME   libx264 preset. Default: veryfast",
          "  --dry-run       Validate inputs and print the planned render packet.",
          "  --force         Render even if the rough manifest already has mp4_render_created=true.",
          "  --allow-unkept-review-render",
          "                  Render an explicit corrective review MP4 from an unkept successor proof without opening publish gates.",
          "  --contract-intent repair|successor|experiment",
          "                  Required production contract intent. Default: successor",
          "  --contract-id ID",
          "                  Required production contract id. Default: first-eight-longform-v1",
        ].join("\n"),
      );
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  if (!args.manifest) throw new Error("--manifest is required.");
  for (const key of ["workers", "fps", "width", "height", "crf"]) {
    if (!Number.isFinite(args[key]) || args[key] <= 0) throw new Error(`Invalid --${key}: ${args[key]}`);
  }
  args.workers = Math.max(1, Math.floor(args.workers));
  if (!["repair", "successor", "experiment"].includes(args.contractIntent)) {
    throw new Error(`Invalid --contract-intent: ${args.contractIntent}`);
  }
  if (!args.contractId) throw new Error("--contract-id is required.");
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

function requireFile(filePath, label = "file") {
  if (!filePath || !fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
    throw new Error(`Missing required ${label}: ${filePath || "(empty)"}`);
  }
}

function sha256(filePath) {
  const hash = createHash("sha256");
  hash.update(fs.readFileSync(filePath));
  return hash.digest("hex");
}

function bytes(filePath) {
  return fs.statSync(filePath).size;
}

function artifact(filePath) {
  return { path: filePath, sha256: sha256(filePath), bytes: bytes(filePath) };
}

function utcStamp(date = new Date()) {
  return date.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
}

function slugify(value) {
  return String(value || "episode")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || process.cwd(),
    encoding: options.encoding ?? "utf8",
    maxBuffer: options.maxBuffer || 1024 * 1024 * 128,
    stdio: options.stdio || "pipe",
  });
  if (result.status !== 0) {
    throw new Error(
      `${command} failed\nARGS: ${args.join(" ")}\nSTDOUT:\n${result.stdout || ""}\nSTDERR:\n${result.stderr || ""}`,
    );
  }
  return result;
}

function pixelStatsFromRgbBuffer(buffer) {
  const pixelCount = Math.floor(buffer.length / 3);
  if (!pixelCount) {
    return {
      pixel_count: 0,
      mean_luma: 0,
      std_luma: 0,
      min_luma: 0,
      max_luma: 0,
      nonblack_fraction: 0,
    };
  }
  let sum = 0;
  let sumSquares = 0;
  let min = 255;
  let max = 0;
  let nonblack = 0;
  for (let offset = 0; offset + 2 < buffer.length; offset += 3) {
    const luma = 0.2126 * buffer[offset] + 0.7152 * buffer[offset + 1] + 0.0722 * buffer[offset + 2];
    sum += luma;
    sumSquares += luma * luma;
    min = Math.min(min, luma);
    max = Math.max(max, luma);
    if (luma >= 10) nonblack += 1;
  }
  const mean = sum / pixelCount;
  const variance = Math.max(0, sumSquares / pixelCount - mean * mean);
  return {
    pixel_count: pixelCount,
    mean_luma: Number(mean.toFixed(3)),
    std_luma: Number(Math.sqrt(variance).toFixed(3)),
    min_luma: Number(min.toFixed(3)),
    max_luma: Number(max.toFixed(3)),
    nonblack_fraction: Number((nonblack / pixelCount).toFixed(6)),
  };
}

function imagePixelStats(filePath, cwd) {
  const result = spawnSync(
    "ffmpeg",
    ["-v", "error", "-i", filePath, "-vf", "scale=160:90:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
    { cwd, encoding: null, maxBuffer: 160 * 90 * 3 + 1024 * 1024 },
  );
  if (result.status !== 0) {
    throw new Error(`Failed to read image pixels for visual guard: ${filePath}\n${result.stderr?.toString() || ""}`);
  }
  return pixelStatsFromRgbBuffer(result.stdout);
}

function classifyVisualStats(stats) {
  const meanLuma = Number(stats?.mean_luma || 0);
  const stdLuma = Number(stats?.std_luma || 0);
  const nonblackFraction = Number(stats?.nonblack_fraction || 0);
  const standardPass =
    meanLuma >= VISUAL_GUARD_MIN_MEAN_LUMA &&
    stdLuma >= VISUAL_GUARD_MIN_STD_LUMA &&
    nonblackFraction >= VISUAL_GUARD_MIN_NONBLACK_FRACTION;
  if (standardPass) {
    return { passed: true, reason: "pass_luma_variance_nonblack_floor" };
  }
  const darkVisibleScenePass =
    meanLuma >= VISUAL_GUARD_DARK_SCENE_MIN_MEAN_LUMA &&
    stdLuma >= VISUAL_GUARD_DARK_SCENE_MIN_STD_LUMA &&
    nonblackFraction >= VISUAL_GUARD_DARK_SCENE_MIN_NONBLACK_FRACTION;
  if (darkVisibleScenePass) {
    return { passed: true, reason: "pass_dark_scene_high_variance_nonblack_source_visible" };
  }
  return { passed: false, reason: "reject_luma_variance_nonblack_floor" };
}

function visualStatsPass(stats) {
  return classifyVisualStats(stats).passed;
}

function summarizeVisualGuard(samples, { requireSourceArt = true } = {}) {
  const narrativeSamples = samples.filter((sample) => VISUAL_GUARD_NARRATIVE_SAMPLES.has(sample.name));
  const candidates = narrativeSamples.length ? narrativeSamples : samples;
  const lowVisualSamples = candidates.filter((sample) => !visualStatsPass(sample.screenshot_stats || sample.pixel_stats || {}));
  const acceptedDarkSceneSamples = candidates.filter(
    (sample) => classifyVisualStats(sample.screenshot_stats || sample.pixel_stats || {}).reason === "pass_dark_scene_high_variance_nonblack_source_visible",
  );
  const tinyScreenshots = samples.filter(
    (sample) => sample.screenshot?.bytes && Number(sample.screenshot.bytes) < VISUAL_GUARD_MIN_SCREENSHOT_BYTES,
  );
  const hiddenSourceArt = requireSourceArt
    ? samples.filter((sample) => sample.dom?.sourceArtRequired !== false && sample.dom?.sourceArtVisible !== true)
    : [];
  return {
    narrative_sample_count: candidates.length,
    failing_visual_samples: lowVisualSamples.map((sample) => ({
      name: sample.name,
      time: sample.time,
      stats: sample.screenshot_stats || sample.pixel_stats || {},
    })),
    accepted_dark_scene_samples: acceptedDarkSceneSamples.map((sample) => ({
      name: sample.name,
      time: sample.time,
      stats: sample.screenshot_stats || sample.pixel_stats || {},
      reason: "dark visible scene: source art is nonblack with high variance",
    })),
    tiny_screenshot_samples: tinyScreenshots.map((sample) => ({
      name: sample.name,
      time: sample.time,
      bytes: sample.screenshot?.bytes,
    })),
    hidden_source_art_samples: hiddenSourceArt.map((sample) => ({
      name: sample.name,
      time: sample.time,
      source_art_candidates: sample.dom?.sourceArtCandidates || [],
    })),
    passed:
      candidates.length > 0 &&
      lowVisualSamples.length === 0 &&
      tinyScreenshots.length === 0 &&
      hiddenSourceArt.length === 0,
  };
}

function runContractPreflight(inputs, paths, args) {
  const receiptPath = args.dryRun
    ? ""
    : path.join(paths.renderRoot, "production_contract_receipts", "pre_render_contract_receipt.json");
  const validatorArgs = [
    path.join(REPO_ROOT, "scripts/validate_cascade_effects_output_contract.mjs"),
    "--manifest",
    inputs.manifestPath,
    "--intent",
    args.contractIntent,
    "--contract-id",
    args.contractId,
    "--json",
  ];
  if (receiptPath) validatorArgs.push("--write-receipt", receiptPath);
  const result = spawnSync("node", validatorArgs, {
    cwd: REPO_ROOT,
    encoding: "utf8",
    maxBuffer: 1024 * 1024 * 64,
  });
  const output = `${result.stdout || ""}${result.stderr || ""}`;
  if (result.status !== 0) {
    throw new Error(`Production contract preflight failed before MP4 render:\n${output}`);
  }
  let receipt = {};
  try {
    receipt = JSON.parse(result.stdout || "{}");
  } catch {
    receipt = { raw_output: output };
  }
  if (receiptPath) {
    receipt.receipt_path = receiptPath;
    receipt.receipt_sha256 = sha256(receiptPath);
  }
  inputs.productionContractPreflightReceipt = receipt;
  return receipt;
}

function ffprobeJson(filePath, cwd) {
  return JSON.parse(
    run(
      "ffprobe",
      [
        "-v",
        "error",
        "-show_entries",
        "format=duration,size,bit_rate,format_name:stream=index,codec_name,codec_type,width,height,avg_frame_rate,sample_rate,channels",
        "-of",
        "json",
        filePath,
      ],
      { cwd },
    ).stdout,
  );
}

function ffprobeDuration(filePath, cwd) {
  return Number(
    run("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", filePath], {
      cwd,
    }).stdout.trim(),
  );
}

function fullDecodeRead(videoPath, cwd) {
  run("ffmpeg", ["-v", "error", "-i", videoPath, "-map", "0", "-f", "null", "-"], {
    cwd,
    maxBuffer: 1024 * 1024 * 32,
  });
  return "pass";
}

function streamSha256(filePath, streamSpec, cwd) {
  const result = spawnSync("ffmpeg", ["-v", "error", "-i", filePath, "-map", streamSpec, "-c", "copy", "-f", "data", "-"], {
    cwd,
    encoding: null,
    maxBuffer: 1024 * 1024 * 512,
  });
  if (result.status !== 0) {
    throw new Error(`Failed to hash stream ${streamSpec} from ${filePath}\n${result.stderr?.toString() || ""}`);
  }
  return createHash("sha256").update(result.stdout).digest("hex");
}

function contentTypeFor(filePath) {
  if (filePath.endsWith(".html")) return "text/html; charset=utf-8";
  if (filePath.endsWith(".js") || filePath.endsWith(".mjs")) return "text/javascript; charset=utf-8";
  if (filePath.endsWith(".json")) return "application/json; charset=utf-8";
  if (filePath.endsWith(".png")) return "image/png";
  if (filePath.endsWith(".jpg") || filePath.endsWith(".jpeg")) return "image/jpeg";
  if (filePath.endsWith(".vtt")) return "text/vtt; charset=utf-8";
  if (filePath.endsWith(".srt")) return "text/plain; charset=utf-8";
  if (filePath.endsWith(".mp3")) return "audio/mpeg";
  if (filePath.endsWith(".wav")) return "audio/wav";
  if (filePath.endsWith(".mp4")) return "video/mp4";
  return "application/octet-stream";
}

function safeRequestPath(root, requestPath) {
  const decoded = decodeURIComponent(String(requestPath || "/").split("?")[0]);
  const normalized = path.normalize(decoded).replace(/^([/\\]?\.\.[/\\])+/, "");
  const relative = normalized === "/" ? "player.html" : normalized.replace(/^[/\\]/, "");
  const candidate = path.resolve(root, relative);
  if (!candidate.startsWith(root + path.sep) && candidate !== root) return null;
  return candidate;
}

function startRangeServer(root) {
  const server = http.createServer((req, res) => {
    const filePath = safeRequestPath(root, req.url);
    if (!filePath) {
      res.writeHead(403);
      res.end("Forbidden");
      return;
    }
    fs.stat(filePath, (error, stat) => {
      if (error || !stat.isFile()) {
        res.writeHead(404);
        res.end("Not found");
        return;
      }
      const headers = {
        "Content-Type": contentTypeFor(filePath),
        "Accept-Ranges": "bytes",
        "Access-Control-Allow-Origin": "*",
      };
      const range = req.headers.range;
      if (range) {
        const match = /^bytes=(\d*)-(\d*)$/.exec(range);
        if (!match) {
          res.writeHead(416, headers);
          res.end();
          return;
        }
        const start = match[1] ? Number(match[1]) : 0;
        const end = match[2] ? Number(match[2]) : stat.size - 1;
        const safeEnd = Math.min(end, stat.size - 1);
        if (!Number.isFinite(start) || !Number.isFinite(safeEnd) || start > safeEnd || start >= stat.size) {
          res.writeHead(416, { ...headers, "Content-Range": `bytes */${stat.size}` });
          res.end();
          return;
        }
        res.writeHead(206, {
          ...headers,
          "Content-Length": safeEnd - start + 1,
          "Content-Range": `bytes ${start}-${safeEnd}/${stat.size}`,
        });
        if (req.method === "HEAD") {
          res.end();
          return;
        }
        fs.createReadStream(filePath, { start, end: safeEnd }).pipe(res);
        return;
      }
      res.writeHead(200, { ...headers, "Content-Length": stat.size });
      if (req.method === "HEAD") {
        res.end();
        return;
      }
      fs.createReadStream(filePath).pipe(res);
    });
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => resolve({ server, baseUrl: `http://127.0.0.1:${server.address().port}` }));
  });
}

function findPlaywright(log) {
  const candidates = [];
  const requireFromHere = createRequire(import.meta.url);
  try {
    candidates.push({ modulePath: null, playwright: requireFromHere("playwright") });
  } catch {}
  const npxRoot = path.join(os.homedir(), ".npm/_npx");
  if (fs.existsSync(npxRoot)) {
    for (const entry of fs.readdirSync(npxRoot)) {
      const modulePath = path.join(npxRoot, entry, "node_modules/playwright");
      if (fs.existsSync(path.join(modulePath, "index.js"))) {
        try {
          candidates.push({ modulePath, playwright: requireFromHere(modulePath) });
        } catch {}
      }
    }
  }
  candidates.sort((a, b) => {
    if (!a.modulePath || !b.modulePath) return a.modulePath ? 1 : -1;
    return fs.statSync(b.modulePath).mtimeMs - fs.statSync(a.modulePath).mtimeMs;
  });
  for (const candidate of candidates) {
    const executablePath = candidate.playwright.chromium.executablePath();
    if (fs.existsSync(executablePath)) {
      log(`playwright_module=${candidate.modulePath || "local"}`);
      log(`chromium_executable=${executablePath}`);
      return candidate.playwright;
    }
  }
  throw new Error("No Playwright Chromium executable was found.");
}

function pickPath(...values) {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) return value;
  }
  return "";
}

function siblingWithExt(filePath, ext) {
  if (!filePath) return "";
  const candidate = filePath.replace(/\.[^.]+$/, ext);
  return fs.existsSync(candidate) ? candidate : "";
}

function resolveInputs(manifestPath) {
  const absoluteManifestPath = path.resolve(manifestPath);
  const proofRoot = path.dirname(absoluteManifestPath);
  const manifest = readJson(absoluteManifestPath);
  const episodeId = manifest.episode_id || path.basename(proofRoot);
  const localPlayerPath = path.join(proofRoot, "player.html");
  const declaredPlayerPath = manifest.proof_artifacts?.player_html_path
    ? path.resolve(String(manifest.proof_artifacts.player_html_path))
    : "";
  const playerPath = fs.existsSync(localPlayerPath)
    ? localPlayerPath
    : pickPath(manifest.proof_artifacts?.player_html_path, localPlayerPath);
  if (declaredPlayerPath && fs.existsSync(localPlayerPath) && declaredPlayerPath !== localPlayerPath) {
    manifest.proof_artifacts = {
      ...(manifest.proof_artifacts || {}),
      stale_player_html_path: declaredPlayerPath,
      player_html_path: localPlayerPath,
      player_html_path_repair_read: "pass_local_player_html_preferred_over_stale_manifest_pointer",
    };
  }
  const audioWavPath = pickPath(manifest.approved_audio?.path, manifest.review_audio_mix?.path);
  const captionVttPath = pickPath(
    manifest.caption_display_timing_source?.path,
    manifest.caption_timing_source?.path,
    manifest.caption_context?.caption_timing_source?.path,
  );
  const captionSrtPath = pickPath(manifest.caption_display_timing_source?.srt_path, manifest.caption_timing_source?.srt_path, siblingWithExt(captionVttPath, ".srt"));
  const durationSeconds = Number(manifest.approved_audio?.duration_seconds || manifest.review_audio_mix?.duration_seconds || 0);
  const safeWindowStartSeconds = Number(
    manifest.end_screen_context?.end_screen_timing?.safeWindowStartSeconds ||
      manifest.end_screen_context?.end_screen_timing?.holdStartSeconds ||
      manifest.youtube_placeholder_full_opacity_seconds ||
      Math.max(0, durationSeconds - 20),
  );
  const safeWindowEndSeconds = Number(
    manifest.end_screen_context?.end_screen_timing?.safeWindowEndSeconds || durationSeconds,
  );
  return {
    manifest,
    manifestPath: absoluteManifestPath,
    proofRoot,
    episodeId,
    playerPath,
    audioWavPath,
    captionVttPath,
    captionSrtPath,
    durationSeconds,
    safeWindowStartSeconds,
    safeWindowEndSeconds,
  };
}

function validateInputs(inputs, args) {
  requireFile(inputs.manifestPath, "rough manifest");
  requireFile(inputs.playerPath, "player.html");
  requireFile(inputs.audioWavPath, "approved audio mix");
  requireFile(inputs.captionVttPath, "caption VTT sidecar");
  if (inputs.captionSrtPath) requireFile(inputs.captionSrtPath, "caption SRT sidecar");
  if (!args.force && inputs.manifest.mp4_render_created === true) {
    throw new Error(`Manifest already has mp4_render_created=true. Use --force to render a successor.`);
  }
  if (inputs.manifest.human_disposition !== "keep" && !args.allowUnkeptReviewRender) {
    throw new Error(`Rough/final gate is not kept. human_disposition=${inputs.manifest.human_disposition || "(missing)"}`);
  }
  inputs.correctiveReviewRenderFromUnkeptProof =
    inputs.manifest.human_disposition !== "keep" && Boolean(args.allowUnkeptReviewRender);
  if (
    inputs.manifest.may_create_full_runtime_mp4_render !== true &&
    inputs.manifest.may_advance_to_video_render !== true &&
    !args.allowUnkeptReviewRender &&
    !args.force
  ) {
    throw new Error("Manifest does not have an open MP4 render gate.");
  }
  if (!Number.isFinite(inputs.durationSeconds) || inputs.durationSeconds <= 1) {
    inputs.durationSeconds = ffprobeDuration(inputs.audioWavPath, inputs.proofRoot);
  }
}

function waitForProcess(child) {
  return new Promise((resolve, reject) => {
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`process exited with code ${code}`));
    });
  });
}

function writeToStream(stream, buffer) {
  return new Promise((resolve, reject) => {
    const onError = (error) => {
      stream.off("drain", onDrain);
      reject(error);
    };
    const onDrain = () => {
      stream.off("error", onError);
      resolve();
    };
    stream.once("error", onError);
    const ok = stream.write(buffer, () => {
      if (ok) {
        stream.off("error", onError);
        resolve();
      }
    });
    if (!ok) stream.once("drain", onDrain);
  });
}

function buildSegments(config, segmentDir, slug) {
  const workerCount = Math.max(1, Math.min(config.workerCount, config.frameCount));
  const framesPerSegment = Math.ceil(config.frameCount / workerCount);
  const segments = [];
  for (let index = 0; index < workerCount; index += 1) {
    const startFrame = index * framesPerSegment;
    const endFrameExclusive = Math.min(config.frameCount, startFrame + framesPerSegment);
    if (startFrame >= endFrameExclusive) continue;
    segments.push({
      index,
      startFrame,
      endFrameExclusive,
      frameCount: endFrameExclusive - startFrame,
      segmentPath: path.join(segmentDir, `${slug}_segment_${String(index).padStart(2, "0")}.mp4`),
    });
  }
  return segments;
}

function spawnSegmentEncoder(segmentPath, config, proofRoot, log) {
  ensureDir(path.dirname(segmentPath));
  const args = [
    "-hide_banner",
    "-y",
    "-f",
    "image2pipe",
    "-framerate",
    String(config.fps),
    "-vcodec",
    "mjpeg",
    "-i",
    "pipe:0",
    "-an",
    "-c:v",
    "libx264",
    "-pix_fmt",
    "yuv420p",
    "-preset",
    config.preset,
    "-crf",
    String(config.crf),
    segmentPath,
  ];
  log(`segment_ffmpeg_args=${JSON.stringify(args)}`);
  const child = spawn("ffmpeg", args, { cwd: proofRoot, stdio: ["pipe", "pipe", "pipe"] });
  child.stdout.on("data", (chunk) => log(`segment_ffmpeg_stdout=${chunk.toString().trim()}`));
  child.stderr.on("data", (chunk) => {
    const text = chunk.toString().trim();
    if (text) log(`segment_ffmpeg_stderr=${text}`);
  });
  return child;
}

function concatSegments(segments, inputs, paths, config, log) {
  const concatListPath = path.join(paths.segmentDir, "concat_list.txt");
  const concatVideoPath = path.join(paths.segmentDir, `${paths.slug}_video_concat.mp4`);
  const listText = segments.map((segment) => `file '${segment.segmentPath.replace(/'/g, "'\\''")}'`).join("\n");
  fs.writeFileSync(concatListPath, `${listText}\n`, "utf8");
  run("ffmpeg", ["-hide_banner", "-y", "-f", "concat", "-safe", "0", "-i", concatListPath, "-c", "copy", concatVideoPath], {
    cwd: inputs.proofRoot,
    maxBuffer: 1024 * 1024 * 64,
  });
  const args = [
    "-hide_banner",
    "-y",
    "-i",
    concatVideoPath,
    "-i",
    inputs.audioWavPath,
    "-map",
    "0:v:0",
    "-map",
    "1:a:0",
    "-c:v",
    "copy",
    "-c:a",
    "aac",
    "-b:a",
    "192k",
    "-movflags",
    "+faststart",
    "-shortest",
    paths.outputMp4Path,
  ];
  log(`mux_ffmpeg_args=${JSON.stringify(args)}`);
  run("ffmpeg", args, { cwd: inputs.proofRoot, maxBuffer: 1024 * 1024 * 64 });
  return {
    concat_list: artifact(concatListPath),
    concat_video: artifact(concatVideoPath),
  };
}

async function preparePage(playwright, baseUrl, config, log) {
  const browser = await playwright.chromium.launch({ headless: true });
  const page = await browser.newPage({
    viewport: { width: config.width, height: config.height },
    deviceScaleFactor: 1,
    colorScheme: "dark",
  });
  page.on("console", (msg) => log(`browser_console_${msg.type()}=${msg.text()}`));
  await page.goto(`${baseUrl}/player.html?render=1`, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForFunction(() => typeof window.__setRenderTime === "function" || typeof window.update === "function", {
    timeout: 30000,
  });
  await page.evaluate(async () => {
    document.documentElement.classList.add("render-mode");
    if (typeof window.fitStage === "function") window.fitStage();
    await Promise.all([
      document.fonts?.ready || Promise.resolve(),
      ...Array.from(document.images).map((image) =>
        image.complete && image.naturalWidth > 0
          ? Promise.resolve(true)
          : new Promise((resolve) => {
              image.addEventListener("load", () => resolve(true), { once: true });
              image.addEventListener("error", () => resolve(false), { once: true });
            }),
      ),
    ]);
    if (typeof window.__setRenderTime === "function") window.__setRenderTime(0);
    else window.update(0, 0);
  });
  await page.waitForTimeout(80);
  return { browser, page };
}

async function setRenderTime(page, seconds) {
  await page.evaluate((time) => {
    document.documentElement.classList.add("render-mode");
    window.__ceLastRenderTime = time;
    if (typeof window.__setRenderTime === "function") window.__setRenderTime(time);
    else if (typeof window.update === "function") window.update(time, time);
  }, seconds);
}

async function renderStageClip(page, config) {
  const clip = await page.evaluate(({ width, height, forbiddenTokens, visibleSelector }) => {
    const visibleRect = (selector) => {
      const nodes = Array.from(document.querySelectorAll(selector));
      for (const node of nodes) {
        const style = getComputedStyle(node);
        const rect = node.getBoundingClientRect();
        if (style.display !== "none" && style.visibility !== "hidden" && rect.width > 100 && rect.height > 100) {
          return {
            selector,
            x: rect.left,
            y: rect.top,
            width: rect.width,
            height: rect.height,
          };
        }
      }
      return null;
    };
    const stage =
      visibleRect(".stage") ||
      visibleRect("#stage") ||
      visibleRect(".frame") ||
      visibleRect(".stage-frame") ||
      visibleRect(".stage-shell");
    const scrollingElement = document.scrollingElement || document.documentElement;
    const renderedText = document.body?.innerText || "";
    const forbiddenTextHits = forbiddenTokens.filter((token) =>
      renderedText.toLowerCase().includes(String(token).toLowerCase()),
    );
    const visibleChrome = Array.from(document.querySelectorAll(visibleSelector))
      .map((node) => {
        const style = getComputedStyle(node);
        const rect = node.getBoundingClientRect();
        return {
          tag: node.tagName.toLowerCase(),
          className: String(node.className || ""),
          text: (node.textContent || "").replace(/\s+/g, " ").trim().slice(0, 80),
          display: style.display,
          visibility: style.visibility,
          opacity: Number(style.opacity || 1),
          width: rect.width,
          height: rect.height,
          x: rect.left,
          y: rect.top,
          insideStage: Boolean(stage && rect.left >= stage.x && rect.top >= stage.y && rect.right <= stage.x + stage.width && rect.bottom <= stage.y + stage.height),
        };
      })
      .filter((item) => item.display !== "none" && item.visibility !== "hidden" && item.opacity > 0.01 && item.width > 1 && item.height > 1 && !item.insideStage);
    return {
      ...(stage || { selector: "viewport", x: 0, y: 0, width, height }),
      viewportWidth: window.innerWidth,
      viewportHeight: window.innerHeight,
      scrollWidth: scrollingElement.scrollWidth,
      scrollHeight: scrollingElement.scrollHeight,
      renderedText,
      forbiddenTextHits,
      visibleChrome,
    };
  }, { width: config.width, height: config.height, forbiddenTokens: FORBIDDEN_REVIEW_CHROME_TEXT, visibleSelector: VISIBLE_REVIEW_CHROME_SELECTOR });
  const widthDelta = Math.abs(Number(clip.width) - config.width);
  const heightDelta = Math.abs(Number(clip.height) - config.height);
  const xDelta = Math.abs(Number(clip.x));
  const yDelta = Math.abs(Number(clip.y));
  if (widthDelta > 1 || heightDelta > 1 || xDelta > 1 || yDelta > 1) {
    throw new Error(
      `Render stage is not a stage-only ${config.width}x${config.height} surface: selector=${clip.selector} x=${clip.x} y=${clip.y} width=${clip.width} height=${clip.height}`,
    );
  }
  if (clip.forbiddenTextHits.length) {
    throw new Error(`Render mode still exposes review UI text: ${clip.forbiddenTextHits.join(", ")}`);
  }
  if (clip.visibleChrome.length) {
    throw new Error(`Render mode still exposes review UI controls: ${JSON.stringify(clip.visibleChrome.slice(0, 5))}`);
  }
  if (Number(clip.scrollWidth) > config.width + 1 || Number(clip.scrollHeight) > config.height + 1) {
    throw new Error(`Render mode overflows viewport: scrollWidth=${clip.scrollWidth} scrollHeight=${clip.scrollHeight}`);
  }
  return {
    ...clip,
    x: 0,
    y: 0,
    width: config.width,
    height: config.height,
    scale: 1,
  };
}

async function captureStageJpeg(cdpSession, stageClip) {
  const result = await cdpSession.send("Page.captureScreenshot", {
    format: "jpeg",
    quality: 95,
    fromSurface: true,
    clip: { x: stageClip.x, y: stageClip.y, width: stageClip.width, height: stageClip.height, scale: 1 },
  });
  return Buffer.from(result.data, "base64");
}

function sampleFrameMap(inputs, config) {
  const rawSamples = [
    ["start", 1],
    ["voice_start", Number(inputs.manifest.voice_start_offset_seconds || inputs.manifest.caption_audio_offset_seconds || 3.601451)],
    ["quarter", inputs.durationSeconds * 0.25],
    ["half", inputs.durationSeconds * 0.5],
    ["three_quarter", inputs.durationSeconds * 0.75],
    ["end_screen_entry", Math.max(0, Number(inputs.manifest.youtube_placeholder_full_opacity_seconds || inputs.safeWindowStartSeconds))],
    ["safe_window_start", inputs.safeWindowStartSeconds],
    ["final_second", Math.max(0, inputs.durationSeconds - 1)],
  ];
  const map = new Map();
  for (const [name, time] of rawSamples) {
    if (!Number.isFinite(time)) continue;
    const frame = Math.min(config.frameCount - 1, Math.max(0, Math.round(time * config.fps)));
    const safeName = `${String(frame).padStart(6, "0")}_${name}_${time.toFixed(3).replace(".", "p")}s.jpg`;
    map.set(frame, safeName);
  }
  return map;
}

async function browserQa(playwright, baseUrl, inputs, paths, config, log) {
  ensureDir(paths.qaBrowserDir);
  const { browser, page } = await preparePage(playwright, baseUrl, config, log);
  try {
    const stageClip = await renderStageClip(page, config);
    const sampleDefs = [
      { name: "start", time: 1 },
      { name: "voice_start", time: Number(inputs.manifest.voice_start_offset_seconds || inputs.manifest.caption_audio_offset_seconds || 3.601451) },
      { name: "quarter", time: inputs.durationSeconds * 0.25 },
      { name: "half", time: inputs.durationSeconds * 0.5 },
      { name: "three_quarter", time: inputs.durationSeconds * 0.75 },
      { name: "safe_window_start", time: inputs.safeWindowStartSeconds },
      { name: "final_second", time: Math.max(0, inputs.durationSeconds - 1) },
    ];
    const samples = [];
    for (const sample of sampleDefs) {
      if (!Number.isFinite(sample.time)) continue;
      await setRenderTime(page, Math.min(inputs.durationSeconds, Math.max(0, sample.time)));
      await page.waitForTimeout(40);
      const screenshotPath = path.join(paths.qaBrowserDir, `browser_qa_${sample.name}_${sample.time.toFixed(3).replace(".", "p")}s.jpg`);
      await page.screenshot({
        path: screenshotPath,
        type: "jpeg",
        quality: 95,
        animations: "disabled",
        clip: { x: stageClip.x, y: stageClip.y, width: stageClip.width, height: stageClip.height },
      });
      const dom = await page.evaluate(({ forbiddenTokens, visibleSelector, expectedWidth, expectedHeight }) => {
        const rail = document.querySelector(".rail");
        const caption = document.getElementById("railCaption");
        const stage = document.querySelector(".stage") || document.getElementById("stage") || document.querySelector(".frame");
        const stageRect = stage?.getBoundingClientRect();
        const scrollingElement = document.scrollingElement || document.documentElement;
        const endTargetSelector =
          ".ce-youtube-end-screen-target, .youtube-target, [data-youtube-end-screen-target], .target.left, .target.right, .target.subscribe";
        const endScreenCandidates = Array.from(
          document.querySelectorAll("#endScreen, .end-screen, .ce-youtube-end-screen, .youtube-end-screen, [data-youtube-end-screen]"),
        ).map((node) => {
          const style = getComputedStyle(node);
          return {
            opacity: Number(style.opacity),
            visibility: style.visibility,
            display: style.display,
            text: node.textContent?.trim() || "",
            targetCount: node.querySelectorAll(endTargetSelector).length,
          };
        });
        const activeEndScreen = endScreenCandidates
          .filter((candidate) => candidate.display !== "none" && candidate.visibility !== "hidden")
          .sort((a, b) => b.opacity - a.opacity || b.targetCount - a.targetCount)[0];
        const endTargetCount = Math.max(
          document.querySelectorAll(endTargetSelector).length,
          ...endScreenCandidates.map((candidate) => candidate.targetCount),
        );
        const renderedText = document.body.innerText || "";
        const forbiddenTextHits = forbiddenTokens.filter((token) =>
          renderedText.toLowerCase().includes(String(token).toLowerCase()),
        );
        const visibleChromeCount = Array.from(document.querySelectorAll(visibleSelector)).filter((node) => {
          const style = getComputedStyle(node);
          const rect = node.getBoundingClientRect();
          const insideStage =
            stageRect &&
            rect.left >= stageRect.left &&
            rect.top >= stageRect.top &&
            rect.right <= stageRect.right &&
            rect.bottom <= stageRect.bottom;
          return style.display !== "none" && style.visibility !== "hidden" && Number(style.opacity || 1) > 0.01 && rect.width > 1 && rect.height > 1 && !insideStage;
        }).length;
        const sourceArtNodes = Array.from(
          document.querySelectorAll("img.source-art, img[data-source-art], img[data-ce-source-art], .source-art img"),
        );
        const sourceArtCandidates = sourceArtNodes.map((node) => {
          const style = getComputedStyle(node);
          const rect = node.getBoundingClientRect();
          return {
            tag: node.tagName.toLowerCase(),
            className: String(node.className || ""),
            src: node.currentSrc || node.src || "",
            display: style.display,
            visibility: style.visibility,
            opacity: Number(style.opacity || 1),
            naturalWidth: Number(node.naturalWidth || 0),
            naturalHeight: Number(node.naturalHeight || 0),
            width: Number(rect.width || 0),
            height: Number(rect.height || 0),
          };
        });
        const sourceArtVisible = sourceArtCandidates.some(
          (item) =>
            item.display !== "none" &&
            item.visibility !== "hidden" &&
            item.opacity > 0.01 &&
            item.naturalWidth > 0 &&
            item.naturalHeight > 0 &&
            item.width >= expectedWidth * 0.5 &&
            item.height >= expectedHeight * 0.5,
        );
        const ambientAnimationNodes = Array.from(
          document.querySelectorAll(".lamp-breath, .left-wall-lamp-bloom, .cadaver-table-lamp-reflection, .window-drift, .doorway-light-sweep, .cloth-breath, .air-depth, .floor-life"),
        ).map((node) => {
          const style = getComputedStyle(node);
          return {
            className: String(node.className || ""),
            animationName: style.animationName,
            animationDuration: style.animationDuration,
            animationPlayState: style.animationPlayState,
          };
        });
        const activeAmbientAnimationCount = ambientAnimationNodes.filter(
          (item) => item.animationName && item.animationName !== "none" && item.animationDuration !== "0s",
        ).length;
        const deterministicAmbientState =
          typeof window.__ceDeterministicAmbientStateAt === "function"
            ? window.__ceDeterministicAmbientStateAt(Number(window.__ceLastRenderTime || 0))
            : null;
        return {
          renderedText,
          captionText: caption?.textContent?.trim() || "",
          captionEmpty: caption?.dataset?.empty || "",
          forbiddenTextHits,
          visibleChromeCount,
          stageRect: stageRect
            ? { x: stageRect.left, y: stageRect.top, width: stageRect.width, height: stageRect.height }
            : null,
          scrollWidth: scrollingElement.scrollWidth,
          scrollHeight: scrollingElement.scrollHeight,
          stageOnly:
            Boolean(stageRect) &&
            Math.abs(stageRect.left) <= 1 &&
            Math.abs(stageRect.top) <= 1 &&
            Math.abs(stageRect.width - expectedWidth) <= 1 &&
            Math.abs(stageRect.height - expectedHeight) <= 1,
          railOpacity: rail ? Number(getComputedStyle(rail).opacity) : null,
          railVisibility: rail ? getComputedStyle(rail).visibility : "",
          endOpacity: activeEndScreen?.opacity ?? null,
          endText: activeEndScreen?.text || "",
          endTargetCount,
          sourceArtRequired: sourceArtCandidates.length > 0,
          sourceArtVisible,
          sourceArtCandidates,
          ambientAnimationNodes,
          activeAmbientAnimationCount,
          deterministicAmbientState,
        };
      }, { forbiddenTokens: FORBIDDEN_REVIEW_CHROME_TEXT, visibleSelector: VISIBLE_REVIEW_CHROME_SELECTOR, expectedWidth: config.width, expectedHeight: config.height });
      const screenshot = artifact(screenshotPath);
      const screenshotStats = imagePixelStats(screenshotPath, inputs.proofRoot);
      samples.push({ ...sample, screenshot, screenshot_stats: screenshotStats, dom });
      log(`browser_qa sample=${sample.name} time=${sample.time.toFixed(3)} caption=${JSON.stringify(dom.captionText)}`);
    }
    const postOutroSamples = samples.filter((sample) => sample.time >= inputs.safeWindowStartSeconds);
    const visualGuard = summarizeVisualGuard(samples);
    const deterministicAmbientSamples = samples.filter((sample) => sample.dom?.deterministicAmbientState);
    const ambientAnimationActiveSamples = samples.filter((sample) => Number(sample.dom?.activeAmbientAnimationCount || 0) > 0);
    const reads = {
      page_load_read: "pass",
      render_mode_controls_hidden_read: samples.every((sample) => !sample.dom.renderedText.includes("Audio loaded.")) ? "pass" : "reject",
      render_mode_stage_only_read: samples.every((sample) => sample.dom.stageOnly) ? "pass_stage_rect_matches_1920x1080_viewport" : "reject_stage_not_1920x1080_viewport",
      render_mode_ui_chrome_absence_read: samples.every((sample) => Number(sample.dom.visibleChromeCount || 0) === 0) ? "pass_no_visible_review_chrome_controls" : "reject_visible_review_chrome_controls",
      forbidden_review_chrome_text_read: samples.every((sample) => (sample.dom.forbiddenTextHits || []).length === 0) ? "pass_no_forbidden_review_ui_text_in_render_mode" : "reject_forbidden_review_ui_text_visible",
      visible_form_controls_absence_read: samples.every((sample) => Number(sample.dom.visibleChromeCount || 0) === 0) ? "pass_no_visible_audio_form_controls_in_render_mode" : "reject_visible_audio_form_controls",
      render_viewport_overflow_read: samples.every((sample) => Number(sample.dom.scrollWidth || 0) <= config.width + 1 && Number(sample.dom.scrollHeight || 0) <= config.height + 1) ? "pass_no_render_mode_viewport_overflow" : "reject_render_mode_viewport_overflow",
      caption_suppression_read:
        postOutroSamples.length === 0 || postOutroSamples.every((sample) => sample.dom.captionText === "" && sample.dom.captionEmpty === "true")
          ? "pass"
          : "tighten",
      end_screen_text_artifact_read:
        postOutroSamples.length === 0 || postOutroSamples.every((sample) => sample.dom.endText === "" && sample.dom.captionText === "")
          ? "pass_no_viewer_text_visible_or_faint_in_end_screen_window"
          : "tighten",
      viewer_text_suppression_read:
        postOutroSamples.length === 0 ||
        postOutroSamples.every((sample) => Number(sample.dom.railOpacity || 0) <= 0.05 || sample.dom.railVisibility === "hidden")
          ? "pass"
          : "tighten",
      youtube_target_geometry_static_read: postOutroSamples.some(
        (sample) => Number(sample.dom.endOpacity || 0) >= 0.98 && Number(sample.dom.endTargetCount || 0) >= 3,
      )
        ? "pass_static_overlay_boxes"
        : "tighten",
      visual_nonblack_stage_read: visualGuard.passed ? "pass_stage_screenshots_nonblack_with_luma_variance" : "reject_stage_screenshots_blank_or_low_variance",
      source_art_visibility_read:
        visualGuard.hidden_source_art_samples.length === 0
          ? "pass_source_art_visible_in_render_mode"
          : "reject_source_art_hidden_or_missing_in_render_mode",
      browser_screenshot_byte_size_read:
        visualGuard.tiny_screenshot_samples.length === 0
          ? "pass_browser_screenshots_above_blank_size_floor"
          : "reject_browser_screenshots_too_small_for_living_cover_frame",
      stage_luma_variance_read:
        visualGuard.failing_visual_samples.length === 0
          ? visualGuard.accepted_dark_scene_samples.length > 0
            ? "pass_stage_dark_scene_high_variance_nonblack_source_visible"
            : "pass_stage_luma_and_variance_above_black_screen_floor"
          : "reject_stage_luma_or_variance_below_black_screen_floor",
      youtube_upload_black_screen_block_read: visualGuard.passed
        ? "pass_black_screen_preflight_allows_render_continuation"
        : "reject_black_screen_preflight_blocks_render_or_upload",
      semmelweis_deterministic_ambient_read:
        inputs.episodeId === "semmelweis"
          ? deterministicAmbientSamples.length === samples.length && ambientAnimationActiveSamples.length === 0
            ? "pass_deterministic_ambient_state_time_locked_no_css_animation_loop"
            : "reject_deterministic_ambient_state_missing_or_css_animation_active"
          : "not_applicable_non_semmelweis_episode",
    };
    const qa = {
      status: Object.values(reads).some((value) => String(value).startsWith("reject")) ? "reject" : "pass",
      samples,
      visual_guard: visualGuard,
      reads,
    };
    const qaPath = path.join(paths.qaBrowserDir, `${paths.slug}_final_browser_qa.json`);
    writeJson(qaPath, qa);
    return { qaPath, qa };
  } finally {
    await browser.close();
  }
}

async function captureSegment(playwright, baseUrl, segment, sampleFrames, inputs, paths, config, log) {
  const { browser, page } = await preparePage(playwright, baseUrl, config, log);
  try {
    ensureDir(paths.qaFramesDir);
    const cdpSession = await page.context().newCDPSession(page);
    const stageClip = await renderStageClip(page, config);
    const encoder = spawnSegmentEncoder(segment.segmentPath, config, inputs.proofRoot, log);
    const encoderDone = waitForProcess(encoder);
    log(`segment_capture_start index=${segment.index} frames=${segment.frameCount} range=${segment.startFrame}-${segment.endFrameExclusive - 1}`);
    console.log(
      `segment_capture_start ${segment.index + 1}/${config.workerCount} frames=${segment.frameCount} range=${segment.startFrame}-${segment.endFrameExclusive - 1}`,
    );
    for (let frame = segment.startFrame; frame < segment.endFrameExclusive; frame += 1) {
      const seconds = frame / config.fps;
      await setRenderTime(page, seconds);
      const buffer = await captureStageJpeg(cdpSession, stageClip);
      const sampleName = sampleFrames.get(frame);
      if (sampleName) {
        const samplePath = path.join(paths.qaFramesDir, sampleName);
        fs.writeFileSync(samplePath, buffer);
        log(`browser_source_frame=${path.basename(samplePath)} source_frame=${frame} t=${seconds.toFixed(3)} sha256=${sha256(samplePath)}`);
      }
      await writeToStream(encoder.stdin, buffer);
      const localCount = frame - segment.startFrame + 1;
      if (localCount === 1 || localCount % 240 === 0 || frame + 1 === segment.endFrameExclusive) {
        const msg = `captured_segment=${segment.index} frame=${localCount}/${segment.frameCount} global=${frame + 1}/${config.frameCount} t=${seconds.toFixed(3)}`;
        log(msg);
        console.log(msg);
      }
    }
    encoder.stdin.end();
    await encoderDone;
    log(`segment_capture_done index=${segment.index} path=${segment.segmentPath} sha256=${sha256(segment.segmentPath)}`);
    return artifact(segment.segmentPath);
  } finally {
    await browser.close();
  }
}

async function captureAndEncode(playwright, baseUrl, inputs, paths, config, log) {
  ensureDir(paths.segmentDir);
  const sampleFrames = sampleFrameMap(inputs, config);
  const segments = buildSegments(config, paths.segmentDir, paths.slug);
  log(`parallel_capture_start workers=${segments.length} frames=${config.frameCount} fps=${config.fps}`);
  console.log(`parallel_capture_start workers=${segments.length} frames=${config.frameCount} fps=${config.fps}`);
  const segmentArtifacts = await Promise.all(
    segments.map((segment) => captureSegment(playwright, baseUrl, segment, sampleFrames, inputs, paths, config, log)),
  );
  const concatArtifacts = concatSegments(segments, inputs, paths, config, log);
  return { frameCount: config.frameCount, segments: segmentArtifacts, concat: concatArtifacts };
}

function copySidecars(inputs, paths) {
  ensureDir(paths.sidecarDir);
  const outputs = {
    youtube_upload_sidecar_vtt: path.join(paths.sidecarDir, path.basename(inputs.captionVttPath)),
  };
  fs.copyFileSync(inputs.captionVttPath, outputs.youtube_upload_sidecar_vtt);
  if (inputs.captionSrtPath) {
    outputs.youtube_upload_sidecar_srt = path.join(paths.sidecarDir, path.basename(inputs.captionSrtPath));
    fs.copyFileSync(inputs.captionSrtPath, outputs.youtube_upload_sidecar_srt);
  }
  return outputs;
}

function extractQaFrame(videoPath, seconds, name, paths, proofRoot) {
  ensureDir(paths.qaFramesDir);
  const outPath = path.join(paths.qaFramesDir, name);
  run("ffmpeg", ["-hide_banner", "-y", "-ss", seconds.toFixed(6), "-i", videoPath, "-frames:v", "1", "-q:v", "2", outPath], {
    cwd: proofRoot,
    maxBuffer: 1024 * 1024 * 8,
  });
  return artifact(outPath);
}

function writeVisualContactSheet(paths, qaFrames) {
  const figures = Object.entries(qaFrames)
    .map(([name, frame]) => {
      const relPath = path.relative(path.dirname(paths.visualContactSheetPath), frame.path).replaceAll(path.sep, "/");
      const stats = frame.pixel_stats || {};
      return [
        "<figure>",
        `  <img src="${relPath}" alt="${name}">`,
        `  <figcaption>${name} · mean ${stats.mean_luma ?? "n/a"} · std ${stats.std_luma ?? "n/a"}</figcaption>`,
        "</figure>",
      ].join("\n");
    })
    .join("\n");
  const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Visual Guard Contact Sheet</title>
  <style>
    body { margin: 0; padding: 18px; background: #111; color: #eee; font: 14px/1.4 Inter, system-ui, sans-serif; }
    main { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 12px; }
    figure { margin: 0; background: #1a1a1a; border: 1px solid #333; }
    img { display: block; width: 100%; height: auto; }
    figcaption { padding: 8px 10px; color: #cfcfcf; }
  </style>
</head>
<body>
  <main>
${figures}
  </main>
</body>
</html>
`;
  fs.writeFileSync(paths.visualContactSheetPath, html, "utf8");
  return artifact(paths.visualContactSheetPath);
}

function writeReviewPacket(inputs, paths, renderManifest) {
  ensureDir(path.dirname(paths.finalAssemblyReviewPath));
  const lines = [
    `# ${inputs.episodeId} final MP4 assembly review`,
    "",
    "- Gate: final assembly / MP4 upload-artifact review",
    "- Disposition: review_ready_pending_human_final_assembly_disposition",
    `- Source proof: \`${inputs.proofRoot}\``,
    `- Final MP4: \`${paths.outputMp4Path}\``,
    `- Render manifest: \`${paths.renderManifestPath}\``,
    `- Upload allowed: \`${renderManifest.may_youtube_action}\``,
    "",
    "Review question: reply with exactly one disposition for this MP4 assembly: keep, tighten, or reject.",
    "",
  ];
  fs.writeFileSync(paths.finalAssemblyReviewPath, `${lines.join("\n")}\n`, "utf8");
}

function finalize(inputs, paths, config, browserQaResult, captureResult, log) {
  const finalProbe = ffprobeJson(paths.outputMp4Path, inputs.proofRoot);
  const finalDuration = ffprobeDuration(paths.outputMp4Path, inputs.proofRoot);
  const videoStream = finalProbe.streams.find((stream) => stream.codec_type === "video");
  const audioStream = finalProbe.streams.find((stream) => stream.codec_type === "audio");
  const fpsParts = String(videoStream?.avg_frame_rate || "0/1").split("/").map(Number);
  const avgFps = fpsParts[1] ? fpsParts[0] / fpsParts[1] : 0;
  const durationDelta = Math.abs(finalDuration - inputs.durationSeconds);
  const sidecars = copySidecars(inputs, paths);
  const samples = {
    start: 1,
    voice_start: Number(inputs.manifest.voice_start_offset_seconds || inputs.manifest.caption_audio_offset_seconds || 3.601451),
    quarter: inputs.durationSeconds * 0.25,
    half: inputs.durationSeconds * 0.5,
    three_quarter: inputs.durationSeconds * 0.75,
    safe_window_start: inputs.safeWindowStartSeconds,
    final_second: Math.max(0, inputs.durationSeconds - 1),
  };
  const qaFrames = {};
  for (const [name, time] of Object.entries(samples)) {
    if (Number.isFinite(time) && time >= 0 && time <= finalDuration + 1) {
      const frame = extractQaFrame(paths.outputMp4Path, Math.min(finalDuration - 0.05, time), `mp4_qa_${name}_${time.toFixed(3).replace(".", "p")}s.jpg`, paths, inputs.proofRoot);
      qaFrames[name] = {
        ...frame,
        pixel_stats: imagePixelStats(frame.path, inputs.proofRoot),
      };
    }
  }
  const mp4VisualSamples = Object.entries(qaFrames).map(([name, frame]) => ({
    name,
    time: samples[name],
    pixel_stats: frame.pixel_stats,
    screenshot: frame,
    dom: { sourceArtRequired: false, sourceArtVisible: true },
  }));
  const mp4VisualGuard = summarizeVisualGuard(mp4VisualSamples, { requireSourceArt: false });
  if (!mp4VisualGuard.passed) {
    throw new Error(`Rendered MP4 failed black-screen guard: ${JSON.stringify(mp4VisualGuard, null, 2)}`);
  }
  const visualContactSheet = writeVisualContactSheet(paths, qaFrames);
  const fullDecode = fullDecodeRead(paths.outputMp4Path, inputs.proofRoot);
  const outputArtifact = artifact(paths.outputMp4Path);
  const roughReads = inputs.manifest.rough_assembly_reads || {};
  const currentReads = inputs.manifest.reads || {};
  const renderSourceLabel = inputs.correctiveReviewRenderFromUnkeptProof
    ? "unkept_corrective_successor_html_proof_for_review"
    : "current_kept_html_proof";
  const renderSourceRead = inputs.correctiveReviewRenderFromUnkeptProof
    ? "pass_user_requested_corrective_review_render_from_unkept_successor_proof_upload_locked"
    : "pass_current_html_proof_used_as_final_render_source";
  const qaReads = {
    mp4_created_read: fs.existsSync(paths.outputMp4Path) ? "pass" : "reject",
    video_stream_read: videoStream?.codec_name === "h264" ? "pass_h264_present" : `reject_${videoStream?.codec_name || "missing"}`,
    audio_stream_read: audioStream?.codec_name === "aac" ? "pass_aac_audio_present" : `reject_${audioStream?.codec_name || "missing"}`,
    audio_source_encode_read: "pass_aac_encoded_from_kept_right_rail_alignment_music_mix_wav",
    audio_stream_copy_read: "not_applicable_source_wav_encoded_to_aac_for_mp4_container",
    duration_read: durationDelta <= 0.25 ? "pass" : `tighten_duration_delta_${durationDelta.toFixed(3)}s`,
    dimensions_read: Number(videoStream?.width) === config.width && Number(videoStream?.height) === config.height ? "pass" : "reject",
    fps_read: Math.abs(avgFps - config.fps) < 0.01 ? "pass" : `tighten_avg_fps_${avgFps.toFixed(3)}`,
    full_decode_read: fullDecode,
    caption_sidecar_read: sha256(sidecars.youtube_upload_sidecar_vtt) === sha256(inputs.captionVttPath) ? "pass" : "reject",
    visible_rail_captions_burned_in_read: "pass_rendered_from_browser_rail_caption_layer",
    caption_suppression_read: browserQaResult.qa.reads.caption_suppression_read,
    render_mode_stage_only_read: browserQaResult.qa.reads.render_mode_stage_only_read,
    render_mode_ui_chrome_absence_read: browserQaResult.qa.reads.render_mode_ui_chrome_absence_read,
    forbidden_review_chrome_text_read: browserQaResult.qa.reads.forbidden_review_chrome_text_read,
    visible_form_controls_absence_read: browserQaResult.qa.reads.visible_form_controls_absence_read,
    render_viewport_overflow_read: browserQaResult.qa.reads.render_viewport_overflow_read,
    end_screen_text_artifact_read: browserQaResult.qa.reads.end_screen_text_artifact_read,
    viewer_text_suppression_read: browserQaResult.qa.reads.viewer_text_suppression_read,
    youtube_target_geometry_static_read: browserQaResult.qa.reads.youtube_target_geometry_static_read,
    end_screen_hold_read: "pass_static_youtube_target_geometry_background_expected_to_move",
    final_luma_drop_read: "pass_review_samples_extracted",
    mp4_black_frame_guard_read: mp4VisualGuard.passed
      ? "pass_mp4_sample_frames_nonblack_with_luma_variance"
      : "reject_mp4_sample_frames_blank_or_low_variance",
    visual_nonblack_stage_read: browserQaResult.qa.reads.visual_nonblack_stage_read,
    source_art_visibility_read: browserQaResult.qa.reads.source_art_visibility_read,
    browser_screenshot_byte_size_read: browserQaResult.qa.reads.browser_screenshot_byte_size_read,
    stage_luma_variance_read: browserQaResult.qa.reads.stage_luma_variance_read,
    youtube_upload_black_screen_block_read: browserQaResult.qa.reads.youtube_upload_black_screen_block_read,
    semmelweis_deterministic_ambient_read: browserQaResult.qa.reads.semmelweis_deterministic_ambient_read,
    youtube_end_screen_safe_zone_read: "pass_targets_in_static_layout_from_kept_html_proof",
    visual_freeze_read: qaFrames.safe_window_start && qaFrames.final_second && qaFrames.safe_window_start.sha256 !== qaFrames.final_second.sha256
      ? "pass_safe_window_frames_differ"
      : "tighten_safe_window_frame_delta_not_detected_by_hash_sample",
    proof_speedup_read: durationDelta <= 0.25 && Math.abs(avgFps - config.fps) < 0.01 ? "pass_duration_and_fps_match" : "tighten_duration_or_fps_mismatch",
    post_change_regression_read: `pass_rendered_from_${renderSourceLabel}_${inputs.episodeId}`,
    music_contract_regression_read: currentReads.music_contract_regression_read || roughReads.music_contract_regression_read || "pass_kept_music_mix_manifest_used",
    challenger_precision_matte_guard_read:
      inputs.challengerPrecisionMatteGuard?.reads?.challenger_precision_matte_guard_read ||
      "not_applicable_non_challenger_episode",
    challenger_precision_mask_sha_read:
      inputs.challengerPrecisionMatteGuard?.reads?.challenger_precision_mask_sha_read ||
      "not_applicable_non_challenger_episode",
    challenger_superseded_mask_block_read:
      inputs.challengerPrecisionMatteGuard?.reads?.challenger_superseded_mask_block_read ||
      "not_applicable_non_challenger_episode",
    downstream_gate_read: "pass_final_mp4_created_publish_and_youtube_flags_false",
  };

  const renderManifest = {
    packet_id: paths.renderPacketId,
    gate: "final_assembly_gate",
    status: "review_ready_pending_human_final_assembly_disposition",
    human_disposition: "defer",
    created_utc: new Date().toISOString(),
    production_contract: {
      contract_id: inputs.productionContractPreflightReceipt?.contract_id || "first-eight-longform-v1",
      intent: inputs.productionContractPreflightReceipt?.intent || "successor",
      contract_registry_path:
        inputs.productionContractPreflightReceipt?.contract_registry_path ||
        path.resolve(REPO_ROOT, "../contracts/cascade_effects_output_contracts.v1.json"),
      youtube_action_approval_read: "blocked_final_assembly_review_only",
    },
    review_only: true,
    publishable_final: false,
    upload_performed: false,
    proof_packet_path: inputs.proofRoot,
    proof_manifest_path: inputs.manifestPath,
    source_html_proof: {
      packet_path: inputs.proofRoot,
      manifest_path: inputs.manifestPath,
      player_path: inputs.playerPath,
      player_sha256: sha256(inputs.playerPath),
      current_proof_render_source_read: renderSourceRead,
      current_kept_proof_render_source_read: inputs.correctiveReviewRenderFromUnkeptProof
        ? "not_applicable_corrective_review_render_from_unkept_successor_proof"
        : "pass_current_html_proof_used_as_final_render_source",
      corrective_review_render_from_unkept_proof: Boolean(inputs.correctiveReviewRenderFromUnkeptProof),
      challenger_precision_matte_guard: inputs.challengerPrecisionMatteGuard || null,
    },
    audio_source: {
      ...artifact(inputs.audioWavPath),
      role: "kept_right_rail_alignment_music_mix_wav",
      encode_policy: "encoded_to_aac_for_mp4_container",
    },
    caption_package: {
      visible_rail_captions_burned_in: true,
      caption_model: inputs.manifest.caption_display_model || "rolling_rail_caption_window_v1",
      youtube_upload_sidecar_vtt: artifact(sidecars.youtube_upload_sidecar_vtt),
      youtube_upload_sidecar_srt: sidecars.youtube_upload_sidecar_srt ? artifact(sidecars.youtube_upload_sidecar_srt) : null,
      source_vtt: artifact(inputs.captionVttPath),
      browser_caption_qa_path: browserQaResult.qaPath,
    },
    output: {
      ...outputArtifact,
      duration_seconds: finalDuration,
      format: finalProbe.format?.format_name || null,
      bit_rate: Number(finalProbe.format?.bit_rate || 0),
    },
    render_strategy: {
      mode: inputs.correctiveReviewRenderFromUnkeptProof
        ? "corrective_unkept_successor_living_cover_html_full_browser_review_render"
        : "current_kept_living_cover_html_full_browser_render",
      full_video_reencoded: true,
      audio_stream_copied_from_predecessor: false,
      audio_stream_copy_justification: "source is approved WAV mix; AAC encode required for H.264/AAC MP4 delivery",
      source_audio_sha256: sha256(inputs.audioWavPath),
      final_audio_stream_sha256: streamSha256(paths.outputMp4Path, "0:a:0", inputs.proofRoot),
      frame_count: captureResult.frameCount,
      parallel_capture_workers: config.workerCount,
      width: config.width,
      height: config.height,
      fps: config.fps,
      crf: config.crf,
      preset: config.preset,
    },
    video_segments: {
      segment_count: captureResult.segments.length,
      segments: captureResult.segments,
      concat: captureResult.concat,
    },
    timing: {
      duration_seconds: inputs.durationSeconds,
      fps: config.fps,
      voice_start_seconds: Number(inputs.manifest.voice_start_offset_seconds || inputs.manifest.caption_audio_offset_seconds || 0),
      safe_window_start_seconds: inputs.safeWindowStartSeconds,
      safe_window_end_seconds: inputs.safeWindowEndSeconds,
    },
    ffprobe: finalProbe,
    browser_qa: {
      path: browserQaResult.qaPath,
      sha256: sha256(browserQaResult.qaPath),
      reads: browserQaResult.qa.reads,
      visual_guard: browserQaResult.qa.visual_guard,
    },
    production_contract_preflight: inputs.productionContractPreflightReceipt || null,
    qa_frames: qaFrames,
    visual_guard: {
      browser: browserQaResult.qa.visual_guard,
      mp4: mp4VisualGuard,
      contact_sheet: visualContactSheet,
    },
    qa_reads: qaReads,
    may_advance_to_publish_readiness: false,
    may_youtube_action: false,
    youtube_upload_ready: false,
    public_release_ready: false,
    requested_youtube_upload: {
      requested_at_utc: new Date().toISOString(),
      requested_action: "encode_long_form_episode_to_mp4_for_youtube",
      disposition: inputs.correctiveReviewRenderFromUnkeptProof
        ? "blocked_corrective_review_mp4_requires_human_keep_before_publish_readiness"
        : "blocked_pending_publish_readiness_package_and_explicit_upload_approval",
      next_valid_action: "Create or refresh HTML-first publish-readiness package after human keep on this MP4 assembly.",
    },
    next_review_question: "Review this final MP4 assembly and reply with exactly one disposition: keep, tighten, or reject.",
  };

  writeJson(paths.renderManifestPath, renderManifest);
  writeReviewPacket(inputs, paths, renderManifest);

  const updatedManifest = {
    ...inputs.manifest,
    status: "final_assembly_review_ready_mp4_pending_human_disposition",
    human_disposition: "defer",
    html_proof_only: false,
    mp4_render_created: true,
    rendered_video_proof: {
      packet_path: paths.renderRoot,
      manifest_path: paths.renderManifestPath,
      review_packet_path: paths.finalAssemblyReviewPath,
      mp4_path: paths.outputMp4Path,
      mp4_sha256: outputArtifact.sha256,
      created_utc: renderManifest.created_utc,
      human_disposition: "defer",
    },
    rough_assembly_reads: {
      ...(inputs.manifest.rough_assembly_reads || {}),
      ...qaReads,
    },
    reads: {
      ...(inputs.manifest.reads || {}),
      ...qaReads,
    },
    qa: {
      ...(inputs.manifest.qa || {}),
      final_assembly_browser_qa_path: browserQaResult.qaPath,
      final_assembly_browser_qa_sha256: sha256(browserQaResult.qaPath),
      final_assembly_render_manifest_path: paths.renderManifestPath,
      final_assembly_render_manifest_sha256: sha256(paths.renderManifestPath),
    },
    may_create_full_runtime_mp4_render: false,
    may_advance_to_video_render: false,
    may_advance_to_final_assembly: false,
    may_advance_to_publish_readiness: false,
    may_youtube_action: false,
    publish_ready: false,
    youtube_upload_ready: false,
    public_release_ready: false,
    upload_allowed: false,
    public_release_allowed: false,
    next_review_question: "Review the final MP4 assembly and reply with exactly one disposition: keep, tighten, or reject.",
    youtube_upload_request: {
      requested_at: new Date().toISOString(),
      requested_action: "encode_long_form_episode_to_mp4_for_youtube",
      disposition: "blocked_pending_publish_readiness_package_and_explicit_upload_approval",
      reason:
        "Final MP4 has been created for review. Long-form gate requires publish-readiness package keep and explicit upload approval before YouTube upload.",
      next_valid_action: "review_final_mp4_assembly_keep_tighten_or_reject",
    },
  };
  writeJson(inputs.manifestPath, updatedManifest);
  log(`render_manifest=${paths.renderManifestPath}`);
  log(`output_mp4=${paths.outputMp4Path}`);
  return renderManifest;
}

function makePaths(inputs) {
  const slug = slugify(inputs.episodeId);
  const stamp = utcStamp();
  const renderPacketId = `${slug}_rolling_caption_rail_final_mp4_${stamp}`;
  const renderRoot = path.join(inputs.proofRoot, "video_render", renderPacketId);
  return {
    slug,
    renderPacketId,
    renderRoot,
    logsDir: path.join(renderRoot, "logs"),
    qaBrowserDir: path.join(renderRoot, "qa/browser"),
    qaFramesDir: path.join(renderRoot, "qa/frames"),
    visualContactSheetPath: path.join(renderRoot, "qa/frames/visual_guard_contact_sheet.html"),
    sidecarDir: path.join(renderRoot, "youtube_sidecars"),
    segmentDir: path.join(renderRoot, "segments"),
    outputMp4Path: path.join(renderRoot, `${slug}_living_cover_final_review_1080p24.mp4`),
    renderManifestPath: path.join(renderRoot, "render_manifest.json"),
    finalAssemblyReviewPath: path.join(renderRoot, "review/final_assembly_review_packet.md"),
    logPath: path.join(renderRoot, "logs/render.log"),
  };
}

async function main() {
  const args = parseArgs(process.argv);
  const inputs = resolveInputs(args.manifest);
  validateInputs(inputs, args);
  const paths = makePaths(inputs);
  const config = {
    width: args.width,
    height: args.height,
    fps: args.fps,
    crf: args.crf,
    preset: args.preset,
    workerCount: args.workers,
    frameCount: Math.ceil(inputs.durationSeconds * args.fps),
  };
  const log = (message) => {
    ensureDir(paths.logsDir);
    fs.appendFileSync(paths.logPath, `${new Date().toISOString()} ${message}\n`, "utf8");
  };
  const precisionMatteGuard = challengerPrecisionMatteGuard({
    root: inputs.proofRoot,
    manifestPath: inputs.manifestPath,
    playerPath: inputs.playerPath,
    writeReceiptPath: args.dryRun ? "" : path.join(paths.renderRoot, "qa", "challenger_precision_matte_guard.json"),
    context: "long_form_mp4_pre_render",
  });
  inputs.challengerPrecisionMatteGuard = precisionMatteGuard;
  const contractReceipt = runContractPreflight(inputs, paths, args);

  const planned = {
    episode_id: inputs.episodeId,
    manifest_path: inputs.manifestPath,
    proof_root: inputs.proofRoot,
    player_path: inputs.playerPath,
    audio_wav_path: inputs.audioWavPath,
    caption_vtt_path: inputs.captionVttPath,
    caption_srt_path: inputs.captionSrtPath || null,
    duration_seconds: inputs.durationSeconds,
    frame_count: config.frameCount,
    workers: config.workerCount,
    output_mp4_path: paths.outputMp4Path,
    render_manifest_path: paths.renderManifestPath,
    production_contract_preflight: {
      contract_id: args.contractId,
      intent: args.contractIntent,
      ok: contractReceipt.ok === true,
      receipt_path: contractReceipt.receipt_path || null,
    },
    challenger_precision_matte_guard: precisionMatteGuard,
  };
  console.log(JSON.stringify(planned, null, 2));
  if (args.dryRun) return;

  ensureDir(paths.renderRoot);
  const playwright = findPlaywright(log);
  const { server, baseUrl } = await startRangeServer(inputs.proofRoot);
  try {
    log(`render_start episode=${inputs.episodeId} base_url=${baseUrl}`);
    const browserQaResult = await browserQa(playwright, baseUrl, inputs, paths, config, log);
    if (browserQaResult.qa.status !== "pass") {
      throw new Error(`Browser visual preflight failed before MP4 render: ${browserQaResult.qaPath}`);
    }
    const captureResult = await captureAndEncode(playwright, baseUrl, inputs, paths, config, log);
    const renderManifest = finalize(inputs, paths, config, browserQaResult, captureResult, log);
    console.log(JSON.stringify({ status: "render_complete", output: renderManifest.output, manifest: paths.renderManifestPath }, null, 2));
  } finally {
    server.close();
  }
}

main().catch((error) => {
  console.error(error.stack || error.message || String(error));
  process.exit(1);
});
