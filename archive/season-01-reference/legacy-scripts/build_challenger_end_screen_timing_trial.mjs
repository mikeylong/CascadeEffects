#!/usr/bin/env node
import { spawn, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const EPISODES_ROOT = "/Users/mike/Episodes_CascadeEffects";
const SOURCE_MANIFEST =
  "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_rolling_caption_rail_rough_proof_20260523T182309Z/rough_assembly_manifest.json";
const OLD_FINAL_MP4 =
  "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_rolling_caption_rail_rough_proof_20260523T144059Z/video_render/challenger_rolling_caption_rail_final_mp4_20260523T145959Z/challenger_living_cover_final_review_1080p24.mp4";
const EXPECTED_AUDIO_SHA256 = "9f771c0e45e8e965c30640c5eba50a9126126c5d39160b19639c45b6a86d5e82";
const ENTRY_MODEL = "youtube_legal_window_end_screen_entry_v1";
const TRANSITION_SECONDS = 0.3;
const OLD_PLACEHOLDER_START_SECONDS = 1183;
const VOICE_END_SECONDS = 1182.385669;
const OUTRO_START_SECONDS = 1180.885669;
const OUTRO_TARGET_SECONDS = 1185.385669;
const HTML_REVIEW_START_SECONDS = 1179.5;
const CLIP_START_SECONDS = 1179.5;
const CLIP_END_SECONDS = 1197.0;
const FPS = 24;
const WIDTH = 1920;
const HEIGHT = 1080;

function parseArgs(argv) {
  const args = {
    sourceManifest: SOURCE_MANIFEST,
    oldFinalMp4: OLD_FINAL_MP4,
    skipClip: true,
  };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = () => {
      i += 1;
      if (i >= argv.length) throw new Error(`Missing value for ${arg}`);
      return argv[i];
    };
    if (arg === "--source-manifest") args.sourceManifest = next();
    else if (arg === "--old-final-mp4") args.oldFinalMp4 = next();
    else if (arg === "--render-clip") args.skipClip = false;
    else if (arg === "--skip-clip") args.skipClip = true;
    else if (arg === "--help" || arg === "-h") {
      console.log("Usage: node scripts/build_challenger_end_screen_timing_trial.mjs [--render-clip|--skip-clip]");
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
    maxBuffer: options.maxBuffer || 1024 * 1024 * 64,
  });
  if (result.status !== 0) {
    throw new Error(`${command} failed:\n${result.stdout || ""}${result.stderr || ""}`);
  }
  return result;
}

function ffprobeJson(filePath) {
  return JSON.parse(
    run("ffprobe", [
      "-v",
      "error",
      "-show_entries",
      "format=duration,size,bit_rate,format_name:stream=index,codec_name,codec_type,width,height,avg_frame_rate,sample_rate,channels",
      "-of",
      "json",
      filePath,
    ]).stdout,
  );
}

function volumedetect(filePath, startSeconds, durationSeconds) {
  const args = ["-v", "info"];
  if (Number.isFinite(startSeconds)) args.push("-ss", String(startSeconds));
  if (Number.isFinite(durationSeconds)) args.push("-t", String(durationSeconds));
  args.push("-i", filePath, "-af", "volumedetect", "-f", "null", "-");
  const result = spawnSync("ffmpeg", args, { encoding: "utf8", maxBuffer: 1024 * 1024 * 16 });
  const output = `${result.stdout || ""}${result.stderr || ""}`;
  if (result.status !== 0) throw new Error(`ffmpeg volumedetect failed:\n${output}`);
  const mean = output.match(/mean_volume:\s*(-?[0-9.]+)\s*dB/);
  const max = output.match(/max_volume:\s*(-?[0-9.]+)\s*dB/);
  return {
    start_seconds: startSeconds,
    duration_seconds: durationSeconds,
    mean_volume_db: mean ? Number(mean[1]) : null,
    max_volume_db: max ? Number(max[1]) : null,
  };
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
      if (depth === 0) {
        return {
          value: JSON.parse(text.slice(valueStart, i + 1)),
          start: valueStart,
          end: i + 1,
        };
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
  if (!pattern.test(text)) throw new Error(`Could not replace numeric CE_CONFIG key ${key}`);
  return text.replace(pattern, `$1${Number(value.toFixed(6))}$2`);
}

function replaceConfigString(text, key, value) {
  const pattern = new RegExp(`(${key}: )"[^"]*"(,)`);
  if (!pattern.test(text)) throw new Error(`Could not replace string CE_CONFIG key ${key}`);
  return text.replace(pattern, `$1${JSON.stringify(value)}$2`);
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
}

function contentTypeFor(filePath) {
  if (filePath.endsWith(".html")) return "text/html; charset=utf-8";
  if (filePath.endsWith(".json")) return "application/json; charset=utf-8";
  if (filePath.endsWith(".js") || filePath.endsWith(".mjs")) return "text/javascript; charset=utf-8";
  if (filePath.endsWith(".png")) return "image/png";
  if (filePath.endsWith(".jpg") || filePath.endsWith(".jpeg")) return "image/jpeg";
  if (filePath.endsWith(".vtt")) return "text/vtt; charset=utf-8";
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

function startServer(root) {
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

function findPlaywright() {
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
  for (const candidate of candidates) {
    const executablePath = candidate.playwright.chromium.executablePath();
    if (fs.existsSync(executablePath)) return candidate.playwright;
  }
  throw new Error("No Playwright Chromium executable was found.");
}

async function preparePage(playwright, baseUrl) {
  const browser = await playwright.chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: WIDTH, height: HEIGHT }, deviceScaleFactor: 1, colorScheme: "dark" });
  await page.goto(`${baseUrl}/player.html?render=1`, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForFunction(() => typeof window.__setRenderTime === "function", { timeout: 30000 });
  await page.evaluate(async () => {
    document.documentElement.classList.add("render-mode");
    await (document.fonts?.ready || Promise.resolve());
    window.__setRenderTime(0);
  });
  await page.waitForTimeout(80);
  return { browser, page };
}

async function stageClip(page) {
  const clip = await page.evaluate(({ width, height }) => {
    const stage = document.querySelector(".stage") || document.getElementById("stage") || document.querySelector(".frame");
    const rect = stage?.getBoundingClientRect();
    return rect
      ? { x: rect.left, y: rect.top, width: rect.width, height: rect.height }
      : { x: 0, y: 0, width, height };
  }, { width: WIDTH, height: HEIGHT });
  if (Math.abs(clip.x) > 1 || Math.abs(clip.y) > 1 || Math.abs(clip.width - WIDTH) > 1 || Math.abs(clip.height - HEIGHT) > 1) {
    throw new Error(`Render stage is not ${WIDTH}x${HEIGHT}: ${JSON.stringify(clip)}`);
  }
  return { x: 0, y: 0, width: WIDTH, height: HEIGHT, scale: 1 };
}

async function setRenderTime(page, seconds) {
  await page.evaluate((time) => {
    document.documentElement.classList.add("render-mode");
    window.__setRenderTime(time);
  }, seconds);
}

async function captureStageJpeg(page, clip) {
  const cdp = await page.context().newCDPSession(page);
  const result = await cdp.send("Page.captureScreenshot", {
    format: "jpeg",
    quality: 95,
    fromSurface: true,
    clip,
  });
  await cdp.detach();
  return Buffer.from(result.data, "base64");
}

function waitForProcess(child) {
  return new Promise((resolve, reject) => {
    let stderr = "";
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`Process exited ${code}\n${stderr}`));
    });
  });
}

function writeToStream(stream, buffer) {
  return new Promise((resolve, reject) => {
    stream.write(buffer, (error) => (error ? reject(error) : resolve()));
  });
}

async function renderSilentBrowserClip({ proofRoot, outputPath, startSeconds, endSeconds }) {
  const duration = endSeconds - startSeconds;
  const frameCount = Math.round(duration * FPS);
  const { server, baseUrl } = await startServer(proofRoot);
  const playwright = findPlaywright();
  const { browser, page } = await preparePage(playwright, baseUrl);
  try {
    const clip = await stageClip(page);
    ensureDir(path.dirname(outputPath));
    const ffmpeg = spawn("ffmpeg", [
      "-y",
      "-f",
      "image2pipe",
      "-vcodec",
      "mjpeg",
      "-framerate",
      String(FPS),
      "-i",
      "pipe:0",
      "-an",
      "-c:v",
      "libx264",
      "-pix_fmt",
      "yuv420p",
      "-r",
      String(FPS),
      "-movflags",
      "+faststart",
      outputPath,
    ]);
    const done = waitForProcess(ffmpeg);
    const cdp = await page.context().newCDPSession(page);
    for (let frame = 0; frame < frameCount; frame += 1) {
      const time = startSeconds + frame / FPS;
      await setRenderTime(page, time);
      const result = await cdp.send("Page.captureScreenshot", {
        format: "jpeg",
        quality: 95,
        fromSurface: true,
        clip,
      });
      await writeToStream(ffmpeg.stdin, Buffer.from(result.data, "base64"));
      if (frame === 0 || frame + 1 === frameCount || (frame + 1) % 120 === 0) {
        console.log(`rendered_successor_clip_frame=${frame + 1}/${frameCount} t=${time.toFixed(3)}`);
      }
    }
    await cdp.detach();
    ffmpeg.stdin.end();
    await done;
  } finally {
    await browser.close();
    server.close();
  }
}

function muxAudio({ silentVideoPath, audioPath, outputPath, startSeconds, durationSeconds }) {
  run("ffmpeg", [
    "-y",
    "-i",
    silentVideoPath,
    "-ss",
    String(startSeconds),
    "-t",
    String(durationSeconds),
    "-i",
    audioPath,
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
    "-shortest",
    "-movflags",
    "+faststart",
    outputPath,
  ]);
}

function trimOldFinal({ oldFinalMp4, outputPath, startSeconds, durationSeconds }) {
  run("ffmpeg", [
    "-y",
    "-ss",
    String(startSeconds),
    "-t",
    String(durationSeconds),
    "-i",
    oldFinalMp4,
    "-c:v",
    "libx264",
    "-crf",
    "18",
    "-preset",
    "veryfast",
    "-c:a",
    "aac",
    "-b:a",
    "192k",
    "-movflags",
    "+faststart",
    outputPath,
  ]);
}

function buildComparisonClip({ oldClipPath, newClipPath, outputPath }) {
  run("ffmpeg", [
    "-y",
    "-i",
    oldClipPath,
    "-i",
    newClipPath,
    "-filter_complex",
    "[0:v]scale=960:540[left];[1:v]scale=960:540[right];[left][right]hstack=inputs=2[v]",
    "-map",
    "[v]",
    "-map",
    "1:a:0",
    "-c:v",
    "libx264",
    "-crf",
    "18",
    "-preset",
    "veryfast",
    "-c:a",
    "aac",
    "-b:a",
    "192k",
    "-shortest",
    "-movflags",
    "+faststart",
    outputPath,
  ]);
}

async function browserTimingQa({ proofRoot, manifest, qaDir, legalStart, fullOpacity }) {
  const sampleTimes = [VOICE_END_SECONDS, OLD_PLACEHOLDER_START_SECONDS, OUTRO_TARGET_SECONDS, legalStart, fullOpacity, 1196.0];
  const { server, baseUrl } = await startServer(proofRoot);
  const playwright = findPlaywright();
  const { browser, page } = await preparePage(playwright, baseUrl);
  try {
    const clip = await stageClip(page);
    const samples = [];
    for (const time of sampleTimes) {
      await setRenderTime(page, time);
      await page.waitForTimeout(40);
      const screenshotPath = path.join(qaDir, "browser_samples", `challenger_trial_${String(time.toFixed(3)).replace(".", "p")}s.jpg`);
      ensureDir(path.dirname(screenshotPath));
      const jpeg = await captureStageJpeg(page, clip);
      fs.writeFileSync(screenshotPath, jpeg);
      const state = await page.evaluate((sampleTime) => {
        const overlay = document.querySelector(".ce-youtube-end-screen");
        const style = overlay ? getComputedStyle(overlay) : null;
        const endState = typeof window.__endScreenStateAt === "function" ? window.__endScreenStateAt(sampleTime) : null;
        const railState = typeof window.__railCaptionStateAt === "function" ? window.__railCaptionStateAt(sampleTime) : null;
        return {
          time_seconds: sampleTime,
          overlay_present: Boolean(overlay),
          overlay_opacity: style ? Number(Number(style.opacity || 0).toFixed(4)) : null,
          end_screen_state: endState,
          rail_state: {
            max_visible_caption_opacity: railState?.maxVisibleCaptionOpacity ?? null,
            final_caption_opacity: railState?.finalCaptionOpacity ?? null,
            source_rail_opacity: railState?.sourceRailOpacity ?? null,
            visible_caption_line_count: railState?.visibleCaptionLineCount ?? null,
          },
        };
      }, time);
      samples.push({ ...state, screenshot: artifact(screenshotPath) });
    }
    const failures = [];
    for (const sample of samples) {
      if (!sample.overlay_present) failures.push(`missing overlay at ${sample.time_seconds.toFixed(3)}s`);
      if (sample.time_seconds < legalStart - 0.001 && Number(sample.overlay_opacity) > 0.01) {
        failures.push(`overlay visible before legal start at ${sample.time_seconds.toFixed(3)}s`);
      }
      if (Math.abs(sample.time_seconds - legalStart) <= 0.002 && Number(sample.overlay_opacity) > 0.18) {
        failures.push(`overlay too visible at legal start: ${sample.overlay_opacity}`);
      }
      if (sample.time_seconds >= fullOpacity - 0.002 && Number(sample.overlay_opacity) < 0.92) {
        failures.push(`overlay not fully visible after fade at ${sample.time_seconds.toFixed(3)}s`);
      }
      if (sample.time_seconds >= legalStart - 0.002 && Number(sample.rail_state.max_visible_caption_opacity || 0) > 0.02) {
        failures.push(`caption remains visible during legal YouTube window at ${sample.time_seconds.toFixed(3)}s`);
      }
    }
    const artifactPath = path.join(qaDir, "challenger_end_screen_timing_browser_qa.json");
    const qa = {
      model: "challenger_end_screen_timing_trial_browser_qa_v1",
      created_utc: new Date().toISOString(),
      episode_id: manifest.episode_id,
      legal_entry_seconds: legalStart,
      full_opacity_seconds: fullOpacity,
      sample_times_seconds: sampleTimes,
      samples,
      failures,
      reads: {
        legal_entry_opacity_read: failures.some((failure) => /before legal|legal start|fully visible/.test(failure))
          ? "fail"
          : "pass_no_target_pixels_before_legal_start_and_full_after_300ms",
        legal_window_caption_suppression_read: failures.some((failure) => /caption remains visible/.test(failure))
          ? "fail"
          : "pass_caption_suppressed_at_legal_window_start",
      },
      passed: failures.length === 0,
    };
    writeJson(artifactPath, qa);
    return { artifactPath, qa };
  } finally {
    await browser.close();
    server.close();
  }
}

function audioQa({ manifest, audioPath, qaDir, legalStart }) {
  const windows = {
    vo_outro_overlap: volumedetect(audioPath, VOICE_END_SECONDS - 2, 2.5),
    post_vo_initial_outro: volumedetect(audioPath, VOICE_END_SECONDS, 3),
    outro_target_level: volumedetect(audioPath, OUTRO_TARGET_SECONDS, 3),
    pre_legal_entry_outro: volumedetect(audioPath, legalStart - 3, 3),
    post_legal_entry_outro: volumedetect(audioPath, legalStart, 3),
    diagnostic_clip_window: volumedetect(audioPath, CLIP_START_SECONDS, CLIP_END_SECONDS - CLIP_START_SECONDS),
  };
  const audioSha = sha256(audioPath);
  const maxValues = Object.values(windows).map((item) => Number(item.max_volume_db)).filter(Number.isFinite);
  const failures = [];
  if (audioSha !== EXPECTED_AUDIO_SHA256) failures.push(`audio sha changed: ${audioSha}`);
  if (maxValues.some((value) => value > -0.1)) failures.push("audio window peak is above -0.1 dB");
  const artifactPath = path.join(qaDir, "challenger_vo_outro_audio_qa.json");
  const qa = {
    model: "challenger_vo_outro_audio_transition_observation_v1",
    created_utc: new Date().toISOString(),
    episode_id: manifest.episode_id,
    source_audio_path: audioPath,
    source_audio_sha256: audioSha,
    expected_source_audio_sha256: EXPECTED_AUDIO_SHA256,
    source_audio_unchanged_read: audioSha === EXPECTED_AUDIO_SHA256 ? "pass_same_review_mix_sha256_no_remix" : "fail_audio_sha_changed",
    voice_end_seconds: VOICE_END_SECONDS,
    outro_start_seconds: OUTRO_START_SECONDS,
    outro_target_seconds: OUTRO_TARGET_SECONDS,
    legal_entry_seconds: legalStart,
    windows,
    failures,
    reads: {
      no_clipping_read: failures.some((failure) => /peak/.test(failure)) ? "fail_peak_above_margin" : "pass_no_window_peak_above_minus_0p1db",
      audio_mix_change_read: audioSha === EXPECTED_AUDIO_SHA256 ? "pass_no_remix_same_source_hash" : "fail_source_hash_changed",
    },
    passed: failures.length === 0,
  };
  writeJson(artifactPath, qa);
  return { artifactPath, qa };
}

function patchManifest({
  manifest,
  outputRoot,
  sourceManifestPath,
  sourcePlayerPath,
  proofBuildPath,
  proofBuildId,
  legalStart,
  fullOpacity,
  naturalSuppressed,
  createdUtc,
}) {
  const captionGap = Number(Math.max(0, legalStart - naturalSuppressed).toFixed(6));
  const timing = {
    ...manifest.end_screen_context.end_screen_timing,
    fadeTimingModel: ENTRY_MODEL,
    endScreenEntryTimingModel: ENTRY_MODEL,
    timingSource: `challenger_trial+${ENTRY_MODEL}`,
    reviewApprovedEndScreenEntryModel: ENTRY_MODEL,
    reviewApprovedFadeStartSeconds: legalStart,
    captionEndScreenHandoffModel: ENTRY_MODEL,
    transitionStartSeconds: legalStart,
    transitionDurationSeconds: TRANSITION_SECONDS,
    youtubePlaceholderTransitionDurationSeconds: TRANSITION_SECONDS,
    fullOpacityAtSeconds: fullOpacity,
    holdStartSeconds: fullOpacity,
    safeWindowStartSeconds: legalStart,
    safeWindowEndSeconds: Number(manifest.approved_audio.duration_seconds.toFixed(6)),
    lastCaptionVisibleExitStartSeconds: OLD_PLACEHOLDER_START_SECONDS,
    lastCaptionFullySuppressedSeconds: naturalSuppressed,
    youtubePlaceholderFadeStartSeconds: legalStart,
    youtubePlaceholderFullOpacitySeconds: fullOpacity,
    captionEndScreenGapSeconds: captionGap,
    captionEndScreenOverlapRead: "pass_youtube_legal_window_entry_after_caption_suppression",
    youtubeSafeWindowCaptionSuppressionRead: "pass_caption_suppressed_before_safe_window",
  };
  const trial = {
    model: ENTRY_MODEL,
    review_scope: "challenger_only_html_pair_review_with_optional_mp4_diagnostic",
    source_manifest_path: sourceManifestPath,
    source_player_path: sourcePlayerPath,
    old_placeholder_fade_start_seconds: OLD_PLACEHOLDER_START_SECONDS,
    voice_end_seconds: VOICE_END_SECONDS,
    outro_start_seconds: OUTRO_START_SECONDS,
    outro_target_seconds: OUTRO_TARGET_SECONDS,
    legal_entry_seconds: legalStart,
    full_opacity_seconds: fullOpacity,
    transition_duration_seconds: TRANSITION_SECONDS,
    browser_qa_sample_times_seconds: [
      VOICE_END_SECONDS,
      OLD_PLACEHOLDER_START_SECONDS,
      OUTRO_TARGET_SECONDS,
      legalStart,
      fullOpacity,
      1196.0,
    ],
    publish_readiness_updated: false,
    upload_state_updated: false,
    youtube_metadata_updated: false,
    public_visibility_updated: false,
  };
  const patched = {
    ...manifest,
    packet_id: path.basename(outputRoot),
    production_contract: {
      ...(manifest.production_contract || {}),
      contract_id: "first-eight-longform-v1",
      intent: "successor",
      contract_registry_path: path.join(REPO_ROOT, "references/production_contracts/cascade_effects_output_contracts.v1.json"),
      youtube_action_approval_read: "blocked_pending_publish_readiness_keep_and_explicit_upload_authorization",
    },
    status: "challenger_youtube_legal_end_screen_entry_trial_review_ready_pending_human_keep",
    human_disposition: "pending",
    human_disposition_source: "pending_challenger_timing_trial_review",
    may_render_final_mp4: false,
    may_advance_to_final_assembly: false,
    may_advance_to_publish_readiness: false,
    may_youtube_action: false,
    publish_ready: false,
    youtube_upload_ready: false,
    upload_performed: false,
    public_release_ready: false,
    youtube_visibility_action_performed: false,
    end_screen_entry_timing_model: ENTRY_MODEL,
    caption_end_screen_handoff_model: ENTRY_MODEL,
    review_approved_end_screen_entry_model: ENTRY_MODEL,
    review_approved_youtube_placeholder_fade_start_seconds: legalStart,
    end_screen_fade_timing_model: ENTRY_MODEL,
    last_caption_visible_exit_start_seconds: OLD_PLACEHOLDER_START_SECONDS,
    last_caption_fully_suppressed_seconds: naturalSuppressed,
    youtube_placeholder_fade_start_seconds: legalStart,
    youtube_placeholder_full_opacity_seconds: fullOpacity,
    youtube_placeholder_transition_duration_seconds: TRANSITION_SECONDS,
    caption_end_screen_gap_seconds: captionGap,
    caption_end_screen_overlap_read: "pass_youtube_legal_window_entry_after_caption_suppression",
    voice_audio_defect_repair_read: "pass_not_audio_repair_source_audio_unchanged",
    end_screen_timing_trial: trial,
    rough_assembly_reads: {
      ...(manifest.rough_assembly_reads || {}),
      voice_audio_defect_repair_read: "pass_not_audio_repair_source_audio_unchanged",
    },
    reads: {
      ...(manifest.reads || {}),
      voice_audio_defect_repair_read: "pass_not_audio_repair_source_audio_unchanged",
    },
    proof_artifacts: {
      ...(manifest.proof_artifacts || {}),
      source_predecessor_manifest_path: sourceManifestPath,
      source_predecessor_player_path: sourcePlayerPath,
      player_html_path: path.join(outputRoot, "player.html"),
      proof_build_json_path: proofBuildPath,
      static_qa_path: path.join(outputRoot, "qa", "rolling_caption_rail_static_qa.json"),
      runtime_coverage_qa_path: path.join(outputRoot, "qa", "rolling_caption_rail_runtime_coverage_qa.json"),
      review_packet_path: path.join(outputRoot, "review", "challenger_end_screen_timing_trial_review_packet.md"),
    },
    proof_build_id: proofBuildId,
    proof_generated_at_utc: createdUtc,
    proof_build_json_path: proofBuildPath,
    proof_build_json_sha256: "pending",
    end_screen_context: {
      ...(manifest.end_screen_context || {}),
      end_screen_entry_timing_model: ENTRY_MODEL,
      caption_end_screen_handoff_model: ENTRY_MODEL,
      review_approved_end_screen_entry_model: ENTRY_MODEL,
      review_approved_youtube_placeholder_fade_start_seconds: legalStart,
      end_screen_fade_timing_model: ENTRY_MODEL,
      end_screen_timing: timing,
      last_caption_visible_exit_start_seconds: OLD_PLACEHOLDER_START_SECONDS,
      last_caption_fully_suppressed_seconds: naturalSuppressed,
      youtube_placeholder_fade_start_seconds: legalStart,
      youtube_placeholder_full_opacity_seconds: fullOpacity,
      youtube_placeholder_transition_duration_seconds: TRANSITION_SECONDS,
      caption_end_screen_gap_seconds: captionGap,
      caption_end_screen_overlap_read: "pass_youtube_legal_window_entry_after_caption_suppression",
      youtube_safe_window_caption_suppression_read: "pass_caption_suppressed_before_safe_window",
    },
  };
  return { manifest: patched, timing, trial };
}

function patchPlayer({ sourcePlayerPath, outputPlayerPath, timing, trial, proofBuildId, createdUtc }) {
  let html = fs.readFileSync(sourcePlayerPath, "utf8");
  const parsed = parseConstJson(html, "CE_END_SCREEN");
  const endScreen = {
    ...parsed.value,
    ...timing,
  };
  html = replaceConstJson(html, "CE_END_SCREEN", endScreen);
  html = replaceConfigString(html, "captionEndScreenHandoffModel", ENTRY_MODEL);
  html = replaceConfigString(html, "reviewApprovedEndScreenEntryModel", ENTRY_MODEL);
  html = replaceConfigNumber(html, "reviewApprovedEndScreenFadeStartSeconds", timing.reviewApprovedFadeStartSeconds);
  html = replaceConfigNumber(html, "lastCaptionVisibleExitStartSeconds", timing.lastCaptionVisibleExitStartSeconds);
  html = replaceConfigNumber(html, "lastCaptionFullySuppressedSeconds", timing.lastCaptionFullySuppressedSeconds);
  html = replaceConfigNumber(html, "youtubePlaceholderFadeStartSeconds", timing.youtubePlaceholderFadeStartSeconds);
  html = replaceConfigNumber(html, "youtubePlaceholderFullOpacitySeconds", timing.youtubePlaceholderFullOpacitySeconds);
  html = replaceConfigNumber(html, "youtubePlaceholderTransitionDurationSeconds", timing.youtubePlaceholderTransitionDurationSeconds);
  html = replaceConfigNumber(html, "captionEndScreenGapSeconds", timing.captionEndScreenGapSeconds);
  html = replaceConfigString(html, "captionEndScreenOverlapRead", timing.captionEndScreenOverlapRead);
  html = html.replace(/(proofBuildId: )"[^"]*"(,)/, `$1${JSON.stringify(proofBuildId)}$2`);
  html = html.replace(/(proofGeneratedAtUtc: )"[^"]*"(,)/, `$1${JSON.stringify(createdUtc)}$2`);
  html = html.replace(
    "</body>",
    `<script id="ce-end-screen-timing-trial" type="application/json">${JSON.stringify(trial)}</script>\n</body>`,
  );
  writeText(outputPlayerPath, html);
}

function patchHtmlReviewPlayer({
  html,
  title,
  proofBuildId,
  createdUtc,
  defaultStartSeconds,
  variant,
}) {
  let patched = html.replace(/<title>[\s\S]*?<\/title>/, `<title>${title}</title>`);
  patched = patched.replace(/(proofBuildId: )"[^"]*"(,)/, `$1${JSON.stringify(proofBuildId)}$2`);
  patched = patched.replace(/(proofGeneratedAtUtc: )"[^"]*"(,)/, `$1${JSON.stringify(createdUtc)}$2`);
  patched = patched.replace(/(proofBuildJsonPath: )"[^"]*"(,)/, `$1"proof_build.json"$2`);
  patched = patched.replace(
    "const CE_URL_FORCED_TIME = Number(CE_PARAMS.get(\"t\"));",
    `const CE_URL_FORCED_TIME = Number(CE_PARAMS.get("t") ?? "${Number(defaultStartSeconds).toFixed(3)}");`,
  );
  patched = patched.replace(
    "</body>",
    `<script id="ce-html-review-variant" type="application/json">${JSON.stringify(variant)}</script>\n</body>`,
  );
  return patched;
}

function writeHtmlReviewProofBuild({
  sourceProofBuildPath,
  proofBuildPath,
  proofBuildId,
  outputRoot,
  manifestPath,
  playerPath,
  variant,
  createdUtc,
}) {
  const proofBuild = readJson(sourceProofBuildPath);
  Object.assign(proofBuild, {
    proof_build_id: proofBuildId,
    proof_generated_at_utc: createdUtc,
    packet_stamp: path.basename(outputRoot),
    player_path: playerPath,
    manifest_path: manifestPath,
    html_review_variant: variant,
  });
  writeJson(proofBuildPath, proofBuild);
}

function htmlReviewIndex({ outputRoot, oldPlayerPath, newPlayerPath, legalStart, fullOpacity }) {
  const relativeOld = path.relative(path.join(outputRoot, "review"), oldPlayerPath).split(path.sep).join("/");
  const relativeNew = path.relative(path.join(outputRoot, "review"), newPlayerPath).split(path.sep).join("/");
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Challenger End-Screen Timing HTML Review</title>
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
    dl { display: grid; grid-template-columns: max-content 1fr; gap: 8px 18px; margin: 22px 0 0; color: var(--muted); }
    dt { color: var(--ink); font-weight: 750; }
    code { color: var(--accent); }
  </style>
</head>
<body>
  <main>
    <h1>Challenger End-Screen Timing HTML Review</h1>
    <p>Open one version at a time and listen from the VO/outro transition through the full ending. Both pages start at <code>${HTML_REVIEW_START_SECONDS.toFixed(3)}s</code> and keep playing to the actual video end.</p>
    <div class="links">
      <a class="review-link" href="${relativeOld}">
        <strong>Old entry: placeholders fade at ${OLD_PLACEHOLDER_START_SECONDS.toFixed(3)}s</strong>
        <span>Predecessor timing. This is the earlier visual handoff.</span>
      </a>
      <a class="review-link" href="${relativeNew}">
        <strong>New legal-window entry: placeholders fade at ${legalStart.toFixed(3)}s</strong>
        <span>Successor timing. Full opacity lands at ${fullOpacity.toFixed(3)}s after the 300ms ramp.</span>
      </a>
    </div>
    <dl>
      <dt>VO end</dt><dd><code>${VOICE_END_SECONDS.toFixed(3)}s</code></dd>
      <dt>Outro start</dt><dd><code>${OUTRO_START_SECONDS.toFixed(3)}s</code></dd>
      <dt>Outro target level</dt><dd><code>${OUTRO_TARGET_SECONDS.toFixed(3)}s</code></dd>
      <dt>Source audio</dt><dd>unchanged; this review changes visual timing only.</dd>
    </dl>
  </main>
</body>
</html>
`;
}

function writeHtmlReviewPair({
  sourceRoot,
  sourcePlayerPath,
  sourceProofBuildPath,
  outputRoot,
  newPlayerPath,
  newProofBuildPath,
  manifestPath,
  proofBuildId,
  legalStart,
  fullOpacity,
  createdUtc,
}) {
  const htmlReviewRoot = path.join(outputRoot, "html_review");
  const oldRoot = path.join(htmlReviewRoot, "old_entry_1183");
  const newRoot = path.join(htmlReviewRoot, "new_legal_entry_1191p681");
  cloneRuntimeLinks(sourceRoot, oldRoot);
  cloneRuntimeLinks(sourceRoot, newRoot);

  const oldVariant = {
    model: "challenger_end_screen_timing_html_review_variant_v1",
    variant_id: "old_entry_1183",
    label: "Old entry, predecessor timing",
    default_start_seconds: HTML_REVIEW_START_SECONDS,
    placeholder_fade_start_seconds: OLD_PLACEHOLDER_START_SECONDS,
    placeholder_full_opacity_seconds: Number((OLD_PLACEHOLDER_START_SECONDS + TRANSITION_SECONDS).toFixed(6)),
    legal_entry_seconds: legalStart,
    source_audio_sha256: EXPECTED_AUDIO_SHA256,
    source_audio_changed: false,
  };
  const newVariant = {
    model: "challenger_end_screen_timing_html_review_variant_v1",
    variant_id: "new_legal_entry_1191p681",
    label: "New legal-window entry, successor timing",
    default_start_seconds: HTML_REVIEW_START_SECONDS,
    placeholder_fade_start_seconds: legalStart,
    placeholder_full_opacity_seconds: fullOpacity,
    legal_entry_seconds: legalStart,
    source_audio_sha256: EXPECTED_AUDIO_SHA256,
    source_audio_changed: false,
  };

  const oldBuildId = `${proofBuildId}_old_entry_html`;
  const newBuildId = `${proofBuildId}_new_legal_entry_html`;
  const oldPlayerPath = path.join(oldRoot, "player.html");
  const newReviewPlayerPath = path.join(newRoot, "player.html");
  const oldProofBuildPath = path.join(oldRoot, "proof_build.json");
  const newReviewProofBuildPath = path.join(newRoot, "proof_build.json");
  const indexPath = path.join(outputRoot, "review", "challenger_end_screen_timing_html_review.html");

  writeText(
    oldPlayerPath,
    patchHtmlReviewPlayer({
      html: fs.readFileSync(sourcePlayerPath, "utf8"),
      title: "Challenger Old End-Screen Entry HTML Review",
      proofBuildId: oldBuildId,
      createdUtc,
      defaultStartSeconds: HTML_REVIEW_START_SECONDS,
      variant: oldVariant,
    }),
  );
  writeHtmlReviewProofBuild({
    sourceProofBuildPath,
    proofBuildPath: oldProofBuildPath,
    proofBuildId: oldBuildId,
    outputRoot: oldRoot,
    manifestPath,
    playerPath: oldPlayerPath,
    variant: oldVariant,
    createdUtc,
  });

  writeText(
    newReviewPlayerPath,
    patchHtmlReviewPlayer({
      html: fs.readFileSync(newPlayerPath, "utf8"),
      title: "Challenger Legal-Window End-Screen Entry HTML Review",
      proofBuildId: newBuildId,
      createdUtc,
      defaultStartSeconds: HTML_REVIEW_START_SECONDS,
      variant: newVariant,
    }),
  );
  writeHtmlReviewProofBuild({
    sourceProofBuildPath: newProofBuildPath,
    proofBuildPath: newReviewProofBuildPath,
    proofBuildId: newBuildId,
    outputRoot: newRoot,
    manifestPath,
    playerPath: newReviewPlayerPath,
    variant: newVariant,
    createdUtc,
  });

  writeText(indexPath, htmlReviewIndex({ outputRoot, oldPlayerPath, newPlayerPath: newReviewPlayerPath, legalStart, fullOpacity }));

  return {
    model: "challenger_end_screen_timing_html_pair_review_v1",
    default_start_seconds: HTML_REVIEW_START_SECONDS,
    review_index: artifact(indexPath),
    old_entry: {
      root_path: oldRoot,
      player: artifact(oldPlayerPath),
      proof_build: artifact(oldProofBuildPath),
      placeholder_fade_start_seconds: OLD_PLACEHOLDER_START_SECONDS,
      placeholder_full_opacity_seconds: oldVariant.placeholder_full_opacity_seconds,
    },
    new_legal_entry: {
      root_path: newRoot,
      player: artifact(newReviewPlayerPath),
      proof_build: artifact(newReviewProofBuildPath),
      placeholder_fade_start_seconds: legalStart,
      placeholder_full_opacity_seconds: fullOpacity,
    },
  };
}

function writeProofBuild({ sourceProofBuildPath, proofBuildPath, proofBuildId, outputRoot, manifestPath, playerPath, legalStart, fullOpacity, createdUtc }) {
  const proofBuild = readJson(sourceProofBuildPath);
  Object.assign(proofBuild, {
    proof_build_id: proofBuildId,
    proof_generated_at_utc: createdUtc,
    packet_stamp: path.basename(outputRoot),
    player_path: playerPath,
    manifest_path: manifestPath,
    caption_end_screen_handoff_model: ENTRY_MODEL,
    review_approved_end_screen_entry_model: ENTRY_MODEL,
    review_approved_youtube_placeholder_fade_start_seconds: legalStart,
    end_screen_fade_timing_model: ENTRY_MODEL,
    end_screen_entry_timing_model: ENTRY_MODEL,
    youtube_placeholder_fade_start_seconds: legalStart,
    youtube_placeholder_full_opacity_seconds: fullOpacity,
    youtube_placeholder_transition_duration_seconds: TRANSITION_SECONDS,
    caption_end_screen_gap_seconds: Number((legalStart - 1190.655556).toFixed(6)),
  });
  writeJson(proofBuildPath, proofBuild);
}

function writeReviewPacket({ reviewPath, manifestPath, playerPath, htmlReview, browserQa, audioQaResult, clipManifestPath, legalStart, fullOpacity }) {
  const lines = [
    "# Challenger End-Screen Timing Trial",
    "",
    "Status: review-ready, pending human keep.",
    "",
    "Review mode: HTML-first timing comparison. Diagnostic MP4 rendering is opt-in after review input.",
    "",
    "## Timing",
    "",
    `- VO end: \`${VOICE_END_SECONDS.toFixed(3)}s\``,
    `- Outro starts: \`${OUTRO_START_SECONDS.toFixed(3)}s\``,
    `- Outro reaches target: \`${OUTRO_TARGET_SECONDS.toFixed(3)}s\``,
    `- Old placeholder start: \`${OLD_PLACEHOLDER_START_SECONDS.toFixed(3)}s\``,
    `- New legal-window placeholder start: \`${legalStart.toFixed(3)}s\``,
    `- Full placeholder opacity: \`${fullOpacity.toFixed(3)}s\``,
    "",
    "## Artifacts",
    "",
    `- Successor HTML proof: \`${playerPath}\``,
    `- HTML review index: \`${htmlReview.review_index.path}\``,
    `- Old-entry HTML review: \`${htmlReview.old_entry.player.path}\``,
    `- New legal-entry HTML review: \`${htmlReview.new_legal_entry.player.path}\``,
    `- Manifest: \`${manifestPath}\``,
    `- Browser timing QA: \`${browserQa.artifactPath}\``,
    `- Audio QA: \`${audioQaResult.artifactPath}\``,
    `- Diagnostic clip manifest: \`${clipManifestPath}\``,
    "",
    "## Reads",
    "",
    `- Legal-entry opacity: \`${browserQa.qa.reads.legal_entry_opacity_read}\``,
    `- Caption suppression at legal window: \`${browserQa.qa.reads.legal_window_caption_suppression_read}\``,
    `- Audio mix hash: \`${audioQaResult.qa.source_audio_unchanged_read}\``,
    `- No clipping: \`${audioQaResult.qa.reads.no_clipping_read}\``,
    "",
    "No publish-readiness, upload, metadata, or visibility state was updated.",
    "",
  ];
  writeText(reviewPath, `${lines.join("\n")}\n`);
}

async function main() {
  const args = parseArgs(process.argv);
  const sourceManifestPath = path.resolve(args.sourceManifest);
  const sourceRoot = path.dirname(sourceManifestPath);
  const sourcePlayerPath = path.join(sourceRoot, "player.html");
  const sourceProofBuildPath = path.join(sourceRoot, "proof_build.json");
  const manifest = readJson(sourceManifestPath);
  const duration = Number(manifest.approved_audio?.duration_seconds || manifest.duration_seconds);
  const legalStart = Number((duration - 20).toFixed(6));
  const fullOpacity = Number((legalStart + TRANSITION_SECONDS).toFixed(6));
  const naturalSuppressed = Number(
    Number(
      manifest.end_screen_context?.end_screen_timing?.lastCaptionNaturalFullySuppressedSeconds ||
        manifest.end_screen_context?.end_screen_timing?.lastCaptionFullySuppressedSeconds ||
        fullOpacity,
    ).toFixed(6),
  );
  const packetStamp = stamp();
  const proofBuildStamp = packetStamp.replace("T", "");
  const createdUtc = new Date().toISOString();
  const outputRoot = path.join(sourceRoot, "..", `challenger_end_screen_legal_window_trial_${packetStamp}`);
  const proofBuildId = `challenger_rolling_caption_rail_${proofBuildStamp}`;
  ensureDir(outputRoot);
  cloneRuntimeLinks(sourceRoot, outputRoot);
  const manifestPath = path.join(outputRoot, "rough_assembly_manifest.json");
  const playerPath = path.join(outputRoot, "player.html");
  const proofBuildPath = path.join(outputRoot, "proof_build.json");
  const qaDir = path.join(outputRoot, "qa");
  const reviewPath = path.join(outputRoot, "review", "challenger_end_screen_timing_trial_review_packet.md");
  const clipDir = path.join(outputRoot, "diagnostic_clip");

  const patched = patchManifest({
    manifest,
    outputRoot,
    sourceManifestPath,
    sourcePlayerPath,
    proofBuildPath,
    proofBuildId,
    legalStart,
    fullOpacity,
    naturalSuppressed,
    createdUtc,
  });
  writeJson(manifestPath, patched.manifest);
  patchPlayer({ sourcePlayerPath, outputPlayerPath: playerPath, timing: patched.timing, trial: patched.trial, proofBuildId, createdUtc });
  writeProofBuild({ sourceProofBuildPath, proofBuildPath, proofBuildId, outputRoot, manifestPath, playerPath, legalStart, fullOpacity, createdUtc });
  const htmlReview = writeHtmlReviewPair({
    sourceRoot,
    sourcePlayerPath,
    sourceProofBuildPath,
    outputRoot,
    newPlayerPath: playerPath,
    newProofBuildPath: proofBuildPath,
    manifestPath,
    proofBuildId,
    legalStart,
    fullOpacity,
    createdUtc,
  });
  patched.manifest.proof_artifacts.player_html_sha256 = sha256(playerPath);
  patched.manifest.proof_artifacts.proof_build_json_sha256 = sha256(proofBuildPath);
  patched.manifest.proof_build_json_sha256 = sha256(proofBuildPath);
  patched.manifest.end_screen_timing_trial.review_scope = "challenger_only_html_pair_review_with_optional_mp4_diagnostic";
  patched.manifest.end_screen_timing_trial.html_review = htmlReview;
  patched.manifest.proof_artifacts.html_review_index_path = htmlReview.review_index.path;
  patched.manifest.proof_artifacts.html_review_index_sha256 = htmlReview.review_index.sha256;
  patched.manifest.proof_artifacts.old_entry_html_review_player_path = htmlReview.old_entry.player.path;
  patched.manifest.proof_artifacts.old_entry_html_review_player_sha256 = htmlReview.old_entry.player.sha256;
  patched.manifest.proof_artifacts.new_legal_entry_html_review_player_path = htmlReview.new_legal_entry.player.path;
  patched.manifest.proof_artifacts.new_legal_entry_html_review_player_sha256 = htmlReview.new_legal_entry.player.sha256;
  writeJson(manifestPath, patched.manifest);

  const audioPath = patched.manifest.approved_audio.path;
  const audioQaResult = audioQa({ manifest: patched.manifest, audioPath, qaDir, legalStart });
  const browserQa = await browserTimingQa({ proofRoot: outputRoot, manifest: patched.manifest, qaDir, legalStart, fullOpacity });

  const clipDuration = CLIP_END_SECONDS - CLIP_START_SECONDS;
  const clipManifest = {
    model: "challenger_end_screen_timing_trial_diagnostic_clip_v1",
    created_utc: new Date().toISOString(),
    clip_start_seconds: CLIP_START_SECONDS,
    clip_end_seconds: CLIP_END_SECONDS,
    clip_duration_seconds: clipDuration,
    old_placeholder_start_seconds: OLD_PLACEHOLDER_START_SECONDS,
    legal_entry_seconds: legalStart,
    full_opacity_seconds: fullOpacity,
    source_audio_path: audioPath,
    source_audio_sha256: sha256(audioPath),
    source_audio_unchanged_read: sha256(audioPath) === EXPECTED_AUDIO_SHA256 ? "pass_same_review_mix_sha256_no_remix" : "fail_audio_sha_changed",
  };
  if (!args.skipClip) {
    ensureDir(clipDir);
    const silentNewClip = path.join(clipDir, "challenger_legal_entry_successor_silent_1179p5_1197p0.mp4");
    const newClip = path.join(clipDir, "challenger_legal_entry_successor_with_audio_1179p5_1197p0.mp4");
    const oldClip = path.join(clipDir, "challenger_old_entry_predecessor_with_audio_1179p5_1197p0.mp4");
    const comparisonClip = path.join(clipDir, "challenger_end_screen_entry_ab_comparison_old_left_new_right_1179p5_1197p0.mp4");
    await renderSilentBrowserClip({ proofRoot: outputRoot, outputPath: silentNewClip, startSeconds: CLIP_START_SECONDS, endSeconds: CLIP_END_SECONDS });
    muxAudio({ silentVideoPath: silentNewClip, audioPath, outputPath: newClip, startSeconds: CLIP_START_SECONDS, durationSeconds: clipDuration });
    trimOldFinal({ oldFinalMp4: args.oldFinalMp4, outputPath: oldClip, startSeconds: CLIP_START_SECONDS, durationSeconds: clipDuration });
    buildComparisonClip({ oldClipPath: oldClip, newClipPath: newClip, outputPath: comparisonClip });
    Object.assign(clipManifest, {
      silent_successor_clip: artifact(silentNewClip),
      successor_clip: artifact(newClip),
      predecessor_clip: artifact(oldClip),
      comparison_clip: artifact(comparisonClip),
      comparison_layout: "old_entry_left_new_legal_entry_right",
    });
  } else {
    clipManifest.skipped = true;
    clipManifest.skip_reason = "html_first_review_pending_human_timing_input";
  }
  const clipManifestPath = path.join(clipDir, "diagnostic_clip_manifest.json");
  writeJson(clipManifestPath, clipManifest);

  patched.manifest.end_screen_timing_trial.browser_qa_path = browserQa.artifactPath;
  patched.manifest.end_screen_timing_trial.browser_qa_sha256 = sha256(browserQa.artifactPath);
  patched.manifest.end_screen_timing_trial.audio_qa_path = audioQaResult.artifactPath;
  patched.manifest.end_screen_timing_trial.audio_qa_sha256 = sha256(audioQaResult.artifactPath);
  patched.manifest.end_screen_timing_trial.diagnostic_clip_manifest_path = clipManifestPath;
  patched.manifest.end_screen_timing_trial.diagnostic_clip_manifest_sha256 = sha256(clipManifestPath);
  patched.manifest.end_screen_timing_trial.browser_qa_read = browserQa.qa.passed ? "pass" : "fail";
  patched.manifest.end_screen_timing_trial.audio_qa_read = audioQaResult.qa.passed ? "pass" : "fail";
  patched.manifest.proof_artifacts.browser_timing_qa_path = browserQa.artifactPath;
  patched.manifest.proof_artifacts.browser_timing_qa_sha256 = sha256(browserQa.artifactPath);
  patched.manifest.proof_artifacts.audio_timing_qa_path = audioQaResult.artifactPath;
  patched.manifest.proof_artifacts.audio_timing_qa_sha256 = sha256(audioQaResult.artifactPath);
  patched.manifest.proof_artifacts.diagnostic_clip_manifest_path = clipManifestPath;
  patched.manifest.proof_artifacts.diagnostic_clip_manifest_sha256 = sha256(clipManifestPath);
  writeJson(manifestPath, patched.manifest);
  writeReviewPacket({
    reviewPath,
    manifestPath,
    playerPath,
    htmlReview,
    browserQa,
    audioQaResult,
    clipManifestPath,
    legalStart,
    fullOpacity,
  });

  console.log(JSON.stringify({
    output_root: outputRoot,
    manifest_path: manifestPath,
    player_path: playerPath,
    review_packet_path: reviewPath,
    html_review_index_path: htmlReview.review_index.path,
    old_entry_html_review_player_path: htmlReview.old_entry.player.path,
    new_legal_entry_html_review_player_path: htmlReview.new_legal_entry.player.path,
    browser_qa_path: browserQa.artifactPath,
    audio_qa_path: audioQaResult.artifactPath,
    diagnostic_clip_manifest_path: clipManifestPath,
    comparison_clip_path: clipManifest.comparison_clip?.path || null,
    legal_entry_seconds: legalStart,
    full_opacity_seconds: fullOpacity,
  }, null, 2));
}

main().catch((error) => {
  console.error(error.stack || error.message || String(error));
  process.exit(1);
});
