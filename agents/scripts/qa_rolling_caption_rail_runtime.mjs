#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import http from "node:http";
import { createRequire } from "node:module";
import crypto from "node:crypto";
import { spawnSync } from "node:child_process";

const REPO_ROOT = "/Users/mike/Agents_CascadeEffects";
const EPISODES_ROOT = "/Users/mike/Episodes_CascadeEffects";
const ROLLOUT_SUMMARY_PATH = path.join(
  REPO_ROOT,
  "references/skills/long_form_video_production_v1/references/episode_visual_system_baselines/rolling_caption_rail_rollout_20260520.json",
);
const MODEL = "full_vo_runtime_visible_caption_coverage_v1";
const PASS_COVERAGE = "pass_full_vo_runtime_visible_caption_coverage";
const PASS_CUTOFF = "pass_no_caption_cutoff_before_final_vo";
const PASS_SCRUB = "pass_foreground_transport_matches_direct_render_time";
const PASS_PLAYING_SCRUB = "pass_foreground_scrub_works_while_playing";
const PASS_CLIP = "pass_no_visible_caption_line_clipping";
const PASS_MEDIA_TIME = "pass_caption_stack_transform_bound_to_audio_current_time";
const PASS_SMOOTH_SCROLL = "pass_caption_scroll_frame_deltas_smooth";
const PASS_ACTIVE_TEXT = "pass_active_caption_text_matches_audio_time";
const PASS_FRESHNESS = "pass_proof_build_freshness_guard_available";
const PASS_PAINT = "pass_visible_right_rail_caption_lines_are_painted";
const PASS_INTRO_TRIM = "pass_first_eight_intro_trim_6s_v1";
const FAIL_COVERAGE = "fail_full_vo_runtime_visible_caption_coverage";
const FAIL_CUTOFF = "fail_caption_cutoff_before_final_vo";
const FAIL_SCRUB = "fail_foreground_transport_mismatch";
const FAIL_PLAYING_SCRUB = "fail_foreground_scrub_while_playing";
const FAIL_CLIP = "fail_visible_caption_line_clipping";
const FAIL_MEDIA_TIME = "fail_caption_stack_transform_drifted_from_audio_current_time";
const FAIL_SMOOTH_SCROLL = "fail_caption_scroll_jitter_detected";
const FAIL_ACTIVE_TEXT = "fail_active_caption_text_mismatch_at_audio_time";
const FAIL_FRESHNESS = "fail_proof_build_freshness_guard_missing";
const FAIL_PAINT = "fail_visible_right_rail_caption_lines_clipped_by_stack_paint_box";
const FAIL_INTRO_TRIM = "fail_first_eight_intro_trim_contract";
const PASS_END_SCREEN = "pass_end_screen_fade_timing_and_adaptive_palette";
const FAIL_END_SCREEN = "fail_end_screen_fade_timing_or_adaptive_palette";
const END_SCREEN_ADAPTIVE_RENDER_AUDIT_MODEL = "end_screen_adaptive_render_audit_v1";
const PASS_ADAPTIVE_RENDER_AUDIT = "pass_end_screen_adaptive_render_audit_v1";
const FAIL_ADAPTIVE_RENDER_AUDIT = "fail_end_screen_adaptive_render_audit_v1";
const PASS_ADAPTIVE_COMPUTED_STYLE = "pass_end_screen_adaptive_computed_styles_match_contract";
const FAIL_ADAPTIVE_COMPUTED_STYLE = "fail_end_screen_adaptive_computed_styles_mismatch";
const PASS_ADAPTIVE_PIXEL_SAMPLE = "pass_end_screen_adaptive_pixel_samples_match_composited_contract";
const FAIL_ADAPTIVE_PIXEL_SAMPLE = "fail_end_screen_adaptive_pixel_samples_mismatch";
const PASS_INHERITED_END_SCREEN = "pass_inherited_end_screen_layers_hidden";
const FAIL_INHERITED_END_SCREEN = "fail_inherited_end_screen_layer_visible";
const PASS_TACOMA_RAIN_GUARD = "pass_tacoma_rain_performance_guard_active";
const FAIL_TACOMA_RAIN_GUARD = "fail_tacoma_rain_performance_guard_missing";
const CAPTION_END_SCREEN_HANDOFF_MODEL = "review_approved_end_screen_entry_v1";
const END_SCREEN_FADE_TIMING_MODEL = "caption_exit_aligned_end_screen_fade_v1";
const YOUTUBE_LEGAL_WINDOW_END_SCREEN_ENTRY_MODEL = "youtube_legal_window_end_screen_entry_v1";
const YOUTUBE_PLACEHOLDER_BORDERLESS_UNDERLAY_MODEL = "youtube_placeholder_borderless_underlay_v1";
const END_SCREEN_TRANSITION_DURATION_SECONDS = 0.3;
const INTRO_TRIM_MODEL = "first_eight_intro_trim_6s_v1";
const INTRO_TRIM_SECONDS = 6;
const PREVIOUS_VOICE_START_OFFSET_SECONDS = 9.601451;
const VOICE_START_OFFSET_SECONDS = 3.601451;
const APPROVED_END_SCREEN_FADE_START_SECONDS = {
  "challenger": 19 * 60 + 43,
  "therac-25": 18 * 60 + 6,
  "hyatt-regency": 13 * 60 + 57,
  "semmelweis": 14 * 60 + 17,
  "tacoma-narrows": 14 * 60 + 4,
  "piltdown-man": 14 * 60 + 3,
  "737-max": 15 * 60 + 46,
  "titanic": 12 * 60 + 24,
};

function usage(exitCode = 0, message = "") {
  if (message) console.error(message);
  console.error(
    "Usage: node scripts/qa_rolling_caption_rail_runtime.mjs --all | --manifest PATH [--manifest PATH ...] [--episode ID] [--json]",
  );
  process.exit(exitCode);
}

function parseArgs(argv) {
  const args = { all: false, manifests: [], episode: "", json: false };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--all") args.all = true;
    else if (arg === "--manifest") args.manifests.push(path.resolve(argv[++i] || ""));
    else if (arg === "--episode") args.episode = argv[++i] || "";
    else if (arg === "--json") args.json = true;
    else if (arg === "--help" || arg === "-h") usage(0);
    else usage(2, `Unknown argument: ${arg}`);
  }
  if (!args.all && args.manifests.length === 0) usage(2, "Missing --all or --manifest");
  return args;
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJson(filePath, value) {
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`);
}

function sha256File(filePath) {
  if (!filePath || !fs.existsSync(filePath)) return "missing";
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function parseCssColor(value) {
  const text = String(value || "").trim();
  const rgbaMatch = /^rgba?\(([^)]+)\)$/i.exec(text);
  if (rgbaMatch) {
    const parts = rgbaMatch[1].split(",").map((part) => part.trim());
    return {
      r: Number(parts[0]),
      g: Number(parts[1]),
      b: Number(parts[2]),
      a: parts[3] === undefined ? 1 : Number(parts[3]),
    };
  }
  const hexMatch = /^#([0-9a-f]{6})$/i.exec(text);
  if (hexMatch) {
    const hex = hexMatch[1];
    return {
      r: parseInt(hex.slice(0, 2), 16),
      g: parseInt(hex.slice(2, 4), 16),
      b: parseInt(hex.slice(4, 6), 16),
      a: 1,
    };
  }
  return null;
}

function colorDelta(a, b) {
  if (!a || !b) return Infinity;
  return Math.max(
    Math.abs(Number(a.r) - Number(b.r)),
    Math.abs(Number(a.g) - Number(b.g)),
    Math.abs(Number(a.b) - Number(b.b)),
    Math.abs(Number(a.a ?? 1) - Number(b.a ?? 1)) * 255,
  );
}

function colorsMatch(actual, expected, tolerance = 1.5) {
  return colorDelta(parseCssColor(actual), parseCssColor(expected)) <= tolerance;
}

function normalizeCssColor(value) {
  const parsed = parseCssColor(value);
  if (!parsed) return String(value || "").trim().toLowerCase().replace(/\s+/g, "");
  const alpha = Number.isFinite(parsed.a) ? parsed.a : 1;
  return `rgba(${Math.round(parsed.r)},${Math.round(parsed.g)},${Math.round(parsed.b)},${Number(alpha.toFixed(3))})`;
}

function relUrlForPath(filePath) {
  return `/${path.relative(EPISODES_ROOT, filePath).split(path.sep).map(encodeURIComponent).join("/")}`;
}

function mimeFor(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  if (ext === ".html") return "text/html; charset=utf-8";
  if (ext === ".js" || ext === ".mjs") return "text/javascript; charset=utf-8";
  if (ext === ".json") return "application/json; charset=utf-8";
  if (ext === ".css") return "text/css; charset=utf-8";
  if (ext === ".png") return "image/png";
  if (ext === ".jpg" || ext === ".jpeg") return "image/jpeg";
  if (ext === ".webp") return "image/webp";
  if (ext === ".wav") return "audio/wav";
  if (ext === ".mp3") return "audio/mpeg";
  if (ext === ".m4a") return "audio/mp4";
  if (ext === ".vtt") return "text/vtt; charset=utf-8";
  return "application/octet-stream";
}

function startServer(root) {
  const server = http.createServer((req, res) => {
    const url = new URL(req.url || "/", "http://127.0.0.1");
    const decoded = decodeURIComponent(url.pathname);
    const filePath = path.resolve(root, `.${decoded}`);
    if (!filePath.startsWith(root) || !fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
      res.statusCode = 404;
      res.end("not found");
      return;
    }
    const stat = fs.statSync(filePath);
    res.setHeader("Accept-Ranges", "bytes");
    res.setHeader("Content-Type", mimeFor(filePath));
    const range = req.headers.range;
    if (range) {
      const match = /^bytes=(\d*)-(\d*)$/.exec(String(range));
      if (match) {
        const start = match[1] ? Number(match[1]) : 0;
        const end = match[2] ? Number(match[2]) : stat.size - 1;
        const safeStart = Math.max(0, Math.min(start, stat.size - 1));
        const safeEnd = Math.max(safeStart, Math.min(end, stat.size - 1));
        res.statusCode = 206;
        res.setHeader("Content-Range", `bytes ${safeStart}-${safeEnd}/${stat.size}`);
        res.setHeader("Content-Length", String(safeEnd - safeStart + 1));
        if (req.method === "HEAD") return res.end();
        fs.createReadStream(filePath, { start: safeStart, end: safeEnd }).pipe(res);
        return;
      }
    }
    res.setHeader("Content-Length", String(stat.size));
    if (req.method === "HEAD") return res.end();
    fs.createReadStream(filePath).pipe(res);
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => resolve({ server, baseUrl: `http://127.0.0.1:${server.address().port}` }));
  });
}

function findPlaywright() {
  const require = createRequire(import.meta.url);
  const candidates = [];
  try {
    candidates.push({ modulePath: null, playwright: require("playwright") });
  } catch {}
  const npxRoot = path.join(os.homedir(), ".npm/_npx");
  if (fs.existsSync(npxRoot)) {
    for (const entry of fs.readdirSync(npxRoot)) {
      const modulePath = path.join(npxRoot, entry, "node_modules/playwright");
      if (fs.existsSync(path.join(modulePath, "index.js"))) {
        candidates.push({ modulePath, playwright: createRequire(path.join(modulePath, "index.js"))(modulePath) });
      }
    }
  }
  candidates.sort((a, b) => {
    if (!a.modulePath || !b.modulePath) return a.modulePath ? 1 : -1;
    return fs.statSync(b.modulePath).mtimeMs - fs.statSync(a.modulePath).mtimeMs;
  });
  for (const candidate of candidates) {
    const executablePath = candidate.playwright.chromium.executablePath();
    if (fs.existsSync(executablePath)) return candidate.playwright;
  }
  throw new Error("No Playwright Chromium executable was found. Run the playwright skill wrapper once to install browsers.");
}

function extractConstJson(html, name) {
  const startNeedle = `const ${name} = `;
  const start = html.indexOf(startNeedle);
  if (start < 0) return null;
  const valueStart = start + startNeedle.length;
  const opener = html[valueStart];
  const closer = opener === "[" ? "]" : opener === "{" ? "}" : "";
  if (!closer) return null;
  let depth = 0;
  let inString = false;
  let quote = "";
  let escaped = false;
  for (let i = valueStart; i < html.length; i += 1) {
    const char = html[i];
    if (inString) {
      if (escaped) escaped = false;
      else if (char === "\\") escaped = true;
      else if (char === quote) inString = false;
      continue;
    }
    if (char === '"' || char === "'") {
      inString = true;
      quote = char;
      continue;
    }
    if (char === opener) depth += 1;
    else if (char === closer) {
      depth -= 1;
      if (depth === 0) return JSON.parse(html.slice(valueStart, i + 1));
    }
  }
  return null;
}

function manifestPaths(args) {
  if (!args.all) return args.manifests;
  const rollout = readJson(ROLLOUT_SUMMARY_PATH);
  let episodes = rollout.episodes || [];
  if (args.episode) episodes = episodes.filter((episode) => episode.episode_id === args.episode);
  return episodes.map((episode) => episode.manifest_path).filter(Boolean);
}

function uniqueSorted(numbers) {
  return Array.from(new Set(numbers.filter(Number.isFinite).map((value) => Number(value.toFixed(3))))).sort((a, b) => a - b);
}

function endScreenEntryTimingModel(manifest, endScreen = {}) {
  return (
    manifest.end_screen_entry_timing_model ||
    manifest.end_screen_context?.end_screen_entry_timing_model ||
    endScreen.endScreenEntryTimingModel ||
    endScreen.fadeTimingModel ||
    manifest.end_screen_context?.end_screen_fade_timing_model ||
    manifest.end_screen_fade_timing_model ||
    ""
  );
}

function isYoutubeLegalWindowEndScreenEntry(manifest, endScreen = {}) {
  return endScreenEntryTimingModel(manifest, endScreen) === YOUTUBE_LEGAL_WINDOW_END_SCREEN_ENTRY_MODEL;
}

function expectedApprovedFadeStartSeconds(manifest, endScreen = {}) {
  if (isYoutubeLegalWindowEndScreenEntry(manifest, endScreen)) {
    const duration = Number(
      manifest.approved_audio?.duration_seconds ||
        manifest.duration_seconds ||
        manifest.review_audio_mix?.duration_seconds ||
        endScreen.safeWindowEndSeconds,
    );
    return Number.isFinite(duration) ? Number((duration - 20).toFixed(6)) : NaN;
  }
  return Number(APPROVED_END_SCREEN_FADE_START_SECONDS[manifest.episode_id] ?? endScreen?.reviewApprovedFadeStartSeconds);
}

function sampleTimesFor(manifest, chunks, endScreen) {
  const first = Number(chunks[0]?.start || manifest.first_caption_display_cue_start_seconds || 0);
  const lastEnd = Number(chunks[chunks.length - 1]?.end || 0);
  const duration = Number(manifest.approved_audio?.duration_seconds || manifest.duration_seconds || lastEnd + 30);
  const safeStart = Number(endScreen?.safeWindowStartSeconds || endScreen?.holdStartSeconds || endScreen?.transitionStartSeconds || duration - 20);
  const approvedEndScreenStart = expectedApprovedFadeStartSeconds(manifest, endScreen);
  const candidates = [
    0,
    Math.max(0, first - 1.1),
    Math.max(0, first - 0.65),
    VOICE_START_OFFSET_SECONDS,
    first,
    230,
    first + (lastEnd - first) * 0.5,
    first + (lastEnd - first) * 0.82,
    Math.max(first, lastEnd - 1.2),
    safeStart,
  ];
  if (Number.isFinite(approvedEndScreenStart)) {
    candidates.push(approvedEndScreenStart - 1, approvedEndScreenStart, approvedEndScreenStart + 0.15, approvedEndScreenStart + 0.3);
  }
  if (Array.isArray(manifest.end_screen_timing_trial?.browser_qa_sample_times_seconds)) {
    candidates.push(...manifest.end_screen_timing_trial.browser_qa_sample_times_seconds.map(Number));
  }
  if (manifest.episode_id === "semmelweis") candidates.push(300, 500, 720, 858);
  return uniqueSorted(candidates.filter((time) => time >= 0 && time <= duration + 0.25));
}

function isExpectedVisible(time, firstCueStart, lastCueEnd, endScreen) {
  const safeStart = Number(endScreen?.safeWindowStartSeconds || endScreen?.holdStartSeconds || Infinity);
  const endScreenFull = Number(endScreen?.fullOpacityAtSeconds || endScreen?.youtubePlaceholderFullOpacitySeconds || Infinity);
  return time >= firstCueStart && time <= lastCueEnd - 0.2 && time < safeStart - 0.1 && time < endScreenFull - 0.05;
}

function activeChunkForTime(chunks, time) {
  if (!chunks.length) return null;
  let active = chunks[0];
  for (const chunk of chunks) {
    if (time >= Number(chunk.start || 0)) active = chunk;
    if (time < Number(chunk.end || 0)) return chunk;
  }
  return active;
}

async function collectPageState(page, requestedTime, method) {
  return page.evaluate(
    ({ requestedTime, method }) => {
      const audio = document.querySelector("audio");
      const scrubber = document.querySelector("[data-ce-scrub]");
      const rail = document.querySelector(".ce-rolling-rail");
      const windowEl = document.querySelector(".ce-caption-window");
      const stack = document.querySelector(".ce-caption-stack");
      const state =
        typeof window.__railCaptionStateAt === "function" ? window.__railCaptionStateAt(requestedTime) : null;
      const windowRect = windowEl ? windowEl.getBoundingClientRect() : null;
      const stackRect = stack ? stack.getBoundingClientRect() : null;
      const railOpacity = rail ? Number.parseFloat(getComputedStyle(rail).opacity || "1") : 1;
      const stackTransform = stack ? getComputedStyle(stack).transform : "";
      let stackTranslateYPx = null;
      try {
        if (stackTransform && stackTransform !== "none") stackTranslateYPx = new DOMMatrixReadOnly(stackTransform).m42;
      } catch {}
      const stackStateTranslateDeltaPx =
        state && Number.isFinite(state.translateY) && Number.isFinite(stackTranslateYPx)
          ? stackTranslateYPx - state.translateY
          : null;
      const lines = Array.from(document.querySelectorAll(".ce-caption-line"));
      const visibleLines = [];
      let maxVisibleCaptionOpacity = 0;
      let maxTextRightOverflowPx = 0;
      let maxTextLeftOverflowPx = 0;
      let maxStackPaintOverflowPx = 0;
      let stackPaintClipRiskCount = 0;
      for (const line of lines) {
        const opacity = Number.parseFloat(getComputedStyle(line).opacity || "0") * railOpacity;
        const rect = line.getBoundingClientRect();
        const overlapsWindow =
          windowRect && rect.bottom > windowRect.top + 1 && rect.top < windowRect.bottom - 1 && rect.right > windowRect.left && rect.left < windowRect.right;
        if (opacity > maxVisibleCaptionOpacity && overlapsWindow) maxVisibleCaptionOpacity = opacity;
        if (opacity > 0.035 && overlapsWindow) {
          const text = (line.textContent || "").replace(/\s+/g, " ").trim();
          let stackPaintOverflowPx = 0;
          if (stackRect) {
            stackPaintOverflowPx = Math.max(
              0,
              stackRect.top - rect.top,
              rect.bottom - stackRect.bottom,
              stackRect.left - rect.left,
              rect.right - stackRect.right,
            );
            maxStackPaintOverflowPx = Math.max(maxStackPaintOverflowPx, stackPaintOverflowPx);
            if (stackPaintOverflowPx > 1) stackPaintClipRiskCount += 1;
          }
          const displayLines = Array.from(line.querySelectorAll(".ce-caption-display-line"));
          for (const displayLine of displayLines.length ? displayLines : [line]) {
            const range = document.createRange();
            range.selectNodeContents(displayLine);
            const textRect = range.getBoundingClientRect();
            range.detach();
            if (windowRect) {
              maxTextRightOverflowPx = Math.max(maxTextRightOverflowPx, textRect.right - windowRect.right);
              maxTextLeftOverflowPx = Math.max(maxTextLeftOverflowPx, windowRect.left - textRect.left);
            }
          }
          visibleLines.push({
            index: Number(line.dataset.index || -1),
            opacity: Number(opacity.toFixed(4)),
            text,
            top: Number(rect.top.toFixed(2)),
            bottom: Number(rect.bottom.toFixed(2)),
            stack_paint_overflow_px: Number(stackPaintOverflowPx.toFixed(2)),
          });
        }
      }
      return {
        method,
        requested_time_seconds: requestedTime,
        audio_current_time_seconds: audio && Number.isFinite(audio.currentTime) ? Number(audio.currentTime.toFixed(3)) : null,
        scrubber_value_seconds: scrubber ? Number(Number(scrubber.value || 0).toFixed(3)) : null,
        rail_opacity: Number((Number.isFinite(railOpacity) ? railOpacity : 1).toFixed(4)),
        state,
        stack_translate_y_px: Number.isFinite(stackTranslateYPx) ? Number(stackTranslateYPx.toFixed(3)) : null,
        stack_state_translate_delta_px: Number.isFinite(stackStateTranslateDeltaPx)
          ? Number(stackStateTranslateDeltaPx.toFixed(3))
          : null,
        visible_line_count: visibleLines.length,
        max_visible_caption_opacity: Number(maxVisibleCaptionOpacity.toFixed(4)),
        visible_lines: visibleLines.slice(0, 8),
        max_text_right_overflow_px: Number(Math.max(0, maxTextRightOverflowPx).toFixed(2)),
        max_text_left_overflow_px: Number(Math.max(0, maxTextLeftOverflowPx).toFixed(2)),
        caption_stack_paint_clip_risk_count: stackPaintClipRiskCount,
        max_caption_stack_paint_overflow_px: Number(maxStackPaintOverflowPx.toFixed(2)),
      };
    },
    { requestedTime, method },
  );
}

async function collectPlaybackSyncState(page, startTime, durationMs = 1800) {
  await page.evaluate(async (nextTime) => {
    const audio = document.querySelector("audio");
    if (!audio) throw new Error("audio element not found for playback sync QA");
    if (typeof window.__setRenderTime === "function") window.__setRenderTime(nextTime);
    audio.muted = true;
    audio.currentTime = nextTime;
    await new Promise((resolve) => setTimeout(resolve, 80));
    await audio.play();
  }, startTime);
  await page.waitForTimeout(durationMs);
  const sample = await page.evaluate(({ initialTime, elapsedMs }) => {
    const audio = document.querySelector("audio");
    const stack = document.querySelector(".ce-caption-stack");
    const rawAudioTime = audio && Number.isFinite(audio.currentTime) ? audio.currentTime : 0;
    const syncedState =
      typeof window.__syncRailCaptionToMediaTime === "function" ? window.__syncRailCaptionToMediaTime() : null;
    const audioTime = syncedState?.time ?? rawAudioTime;
    const state = syncedState || (typeof window.__railCaptionStateAt === "function" ? window.__railCaptionStateAt(audioTime) : null);
    const transform = stack ? getComputedStyle(stack).transform : "";
    let stackTranslateYPx = null;
    try {
      if (transform && transform !== "none") stackTranslateYPx = new DOMMatrixReadOnly(transform).m42;
    } catch {}
    const deltaPx =
      state && Number.isFinite(state.translateY) && Number.isFinite(stackTranslateYPx)
        ? stackTranslateYPx - state.translateY
        : null;
    if (audio) audio.pause();
    return {
      start_time_seconds: initialTime,
      requested_start_time_seconds: initialTime,
      elapsed_wall_seconds: elapsedMs / 1000,
      audio_current_time_seconds: Number(audioTime.toFixed(3)),
      state,
      stack_translate_y_px: Number.isFinite(stackTranslateYPx) ? Number(stackTranslateYPx.toFixed(3)) : null,
      stack_state_translate_delta_px: Number.isFinite(deltaPx) ? Number(deltaPx.toFixed(3)) : null,
    };
  }, { initialTime: startTime, elapsedMs: durationMs });
  return sample;
}

async function collectScrollSmoothnessState(page, startTime, durationMs = 1400) {
  return page.evaluate(
    async ({ nextTime, elapsedMs }) => {
      const audio = document.querySelector("audio");
      const stack = document.querySelector(".ce-caption-stack");
      if (!audio || !stack) throw new Error("audio/stack not found for scroll smoothness QA");
      if (typeof window.__setRenderTime === "function") window.__setRenderTime(nextTime);
      audio.muted = true;
      audio.currentTime = nextTime;
      await new Promise((resolve) => setTimeout(resolve, 80));
      await audio.play();
      const frames = [];
      const stateAtStart =
        typeof window.__railCaptionStateAt === "function" ? window.__railCaptionStateAt(nextTime) || {} : {};
      const start = performance.now();
      await new Promise((resolve) => {
        function step(now) {
          const transform = getComputedStyle(stack).transform;
          let y = null;
          try {
            if (transform && transform !== "none") y = new DOMMatrixReadOnly(transform).m42;
          } catch {}
          if (Number.isFinite(y)) frames.push({ t: now, y });
          if (now - start >= elapsedMs) resolve();
          else requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
      });
      audio.pause();
      const velocities = [];
      let positiveCorrectionMaxPx = 0;
      let directionBreakCount = 0;
      let maxFrameGapMs = 0;
      for (let i = 1; i < frames.length; i += 1) {
        const dt = (frames[i].t - frames[i - 1].t) / 1000;
        const dy = frames[i].y - frames[i - 1].y;
        maxFrameGapMs = Math.max(maxFrameGapMs, dt * 1000);
        if (dy > positiveCorrectionMaxPx) positiveCorrectionMaxPx = dy;
        if (dy > 0.2) directionBreakCount += 1;
        if (dt > 0.004 && dt < 0.08) velocities.push(dy / dt);
      }
      const first = frames[0] || null;
      const last = frames[frames.length - 1] || null;
      const measuredElapsedSeconds = first && last ? Math.max(0, (last.t - first.t) / 1000) : 0;
      const observedTravelPx = first && last ? first.y - last.y : 0;
      const observedVelocityPxPerSecond =
        measuredElapsedSeconds > 0 ? observedTravelPx / measuredElapsedSeconds : 0;
      const expectedSpeedPxPerSecond =
        Number(stateAtStart.captionConstantScrollSpeedPxPerSecond) || null;
      const expectedTravelPx =
        expectedSpeedPxPerSecond && measuredElapsedSeconds > 0
          ? expectedSpeedPxPerSecond * measuredElapsedSeconds
          : null;
      const travelErrorPx =
        expectedTravelPx !== null ? Math.abs(observedTravelPx - expectedTravelPx) : null;
      const mean = velocities.length ? velocities.reduce((sum, value) => sum + value, 0) / velocities.length : 0;
      const variance = velocities.length
        ? velocities.reduce((sum, value) => sum + Math.pow(value - mean, 2), 0) / velocities.length
        : 0;
      return {
        start_time_seconds: nextTime,
        elapsed_ms: elapsedMs,
        frame_count: frames.length,
        velocity_sample_count: velocities.length,
        mean_velocity_px_per_second: Number(mean.toFixed(3)),
        velocity_stddev_px_per_second: Number(Math.sqrt(variance).toFixed(3)),
        positive_correction_max_px: Number(positiveCorrectionMaxPx.toFixed(3)),
        direction_break_count: directionBreakCount,
        max_frame_gap_ms: Number(maxFrameGapMs.toFixed(3)),
        measured_elapsed_seconds: Number(measuredElapsedSeconds.toFixed(3)),
        observed_travel_px: Number(observedTravelPx.toFixed(3)),
        expected_travel_px: expectedTravelPx === null ? null : Number(expectedTravelPx.toFixed(3)),
        travel_error_px: travelErrorPx === null ? null : Number(travelErrorPx.toFixed(3)),
        observed_velocity_px_per_second: Number(observedVelocityPxPerSecond.toFixed(3)),
        expected_velocity_px_per_second:
          expectedSpeedPxPerSecond === null ? null : Number(expectedSpeedPxPerSecond.toFixed(3)),
        first_translate_y_px: frames.length ? Number(frames[0].y.toFixed(3)) : null,
        last_translate_y_px: frames.length ? Number(frames[frames.length - 1].y.toFixed(3)) : null,
        caption_scroll_smoothness_model: stateAtStart.captionScrollSmoothnessModel || "",
        caption_stack_render_model: stateAtStart.captionStackRenderModel || "",
        caption_stack_compositor_active: Boolean(stateAtStart.captionStackCompositorActive),
      };
    },
    { nextTime: startTime, elapsedMs: durationMs },
  );
}

function compareScrollSmoothnessSamples(samples) {
  const failures = [];
  for (const sample of samples) {
    if (sample.frame_count < 8) {
      failures.push({ time_seconds: sample.start_time_seconds, failure: "smooth scroll: insufficient RAF samples" });
    }
    if (sample.positive_correction_max_px > 0.5) {
      failures.push({
        time_seconds: sample.start_time_seconds,
        failure: `smooth scroll: downward correction ${sample.positive_correction_max_px}px detected`,
      });
    }
    if (sample.direction_break_count > 0) {
      failures.push({
        time_seconds: sample.start_time_seconds,
        failure: `smooth scroll: ${sample.direction_break_count} downward frame corrections detected`,
      });
    }
    if (sample.expected_velocity_px_per_second === null) {
      failures.push({ time_seconds: sample.start_time_seconds, failure: "smooth scroll: missing expected constant speed" });
    }
    if (sample.expected_velocity_px_per_second !== null && Math.abs(sample.observed_velocity_px_per_second - sample.expected_velocity_px_per_second) > 9) {
      failures.push({
        time_seconds: sample.start_time_seconds,
        failure: `smooth scroll: observed speed ${sample.observed_velocity_px_per_second}px/s diverges from constant speed ${sample.expected_velocity_px_per_second}px/s`,
      });
    }
    if (sample.travel_error_px !== null && sample.travel_error_px > 14) {
      failures.push({
        time_seconds: sample.start_time_seconds,
        failure: `smooth scroll: measured travel differs by ${sample.travel_error_px}px`,
      });
    }
    if (sample.caption_scroll_smoothness_model !== "compositor_linear_transform_driver_v1") {
      failures.push({
        time_seconds: sample.start_time_seconds,
        failure: `smooth scroll: smoothness model is ${sample.caption_scroll_smoothness_model || "missing"}`,
      });
    }
    if (
      sample.caption_stack_render_model !== "compositor_linear_transform_driver_v1" ||
      Math.abs(Number(sample.observed_travel_px || 0)) <= 1
    ) {
      failures.push({
        time_seconds: sample.start_time_seconds,
        failure: "smooth scroll: caption stack is not using active compositor linear transform driver",
      });
    }
  }
  return failures;
}

async function setDirectTime(page, time) {
  await page.evaluate((nextTime) => {
    if (typeof window.__setRenderTime === "function") window.__setRenderTime(nextTime);
  }, time);
  await page.waitForTimeout(90);
}

async function setScrubTime(page, time) {
  await page.evaluate((nextTime) => {
    const audio = document.querySelector("audio");
    if (audio) audio.pause();
    const scrubber = document.querySelector("[data-ce-scrub]");
    if (!scrubber) throw new Error("foreground review scrubber not found");
    scrubber.value = String(nextTime);
    scrubber.dispatchEvent(new Event("input", { bubbles: true }));
    scrubber.dispatchEvent(new Event("change", { bubbles: true }));
  }, time);
  await page.waitForTimeout(90);
}

async function collectPlayingScrubState(page, targetTime) {
  const setup = await page.evaluate(async (nextTime) => {
    const audio = document.querySelector("audio");
    const scrubber = document.querySelector("[data-ce-scrub]");
    if (!audio || !scrubber) throw new Error("audio/scrubber not found for playing scrub QA");
    const startTime = Math.max(0, nextTime - 45);
    if (typeof window.__setRenderTime === "function") window.__setRenderTime(startTime);
    audio.muted = true;
    audio.currentTime = startTime;
    await new Promise((resolve) => setTimeout(resolve, 80));
    await audio.play();
    scrubber.scrollIntoView({ block: "center", inline: "nearest" });
    await new Promise((resolve) => requestAnimationFrame(() => resolve()));
    const rect = scrubber.getBoundingClientRect();
    if (!rect.width || !rect.height) throw new Error("foreground review scrubber has no visible layout box for playing scrub QA");
    const max = Number(scrubber.max || audio.duration || 1);
    const startX = rect.left + rect.width * Math.max(0, Math.min(1, Number(scrubber.value || startTime) / max));
    const targetX = rect.left + rect.width * Math.max(0, Math.min(1, nextTime / max));
    return {
      start_time_seconds: startTime,
      target_time_seconds: nextTime,
      max_seconds: max,
      y: rect.top + rect.height / 2,
      start_x: startX,
      target_x: targetX,
    };
  }, targetTime);
  await page.waitForTimeout(250);
  await page.mouse.move(setup.start_x, setup.y);
  await page.mouse.down();
  await page.mouse.move((setup.start_x + setup.target_x) / 2, setup.y, { steps: 6 });
  await page.mouse.move(setup.target_x, setup.y, { steps: 10 });
  await page.mouse.up();
  await page.waitForTimeout(850);
  return page.evaluate((setupState) => {
    const audio = document.querySelector("audio");
    const scrubber = document.querySelector("[data-ce-scrub]");
    const currentLabel = document.querySelector("[data-ce-current]");
    const stack = document.querySelector(".ce-caption-stack");
    const transportState = typeof window.__ceReviewTransportState === "function" ? window.__ceReviewTransportState() : null;
    const rawAudioTime = audio && Number.isFinite(audio.currentTime) ? audio.currentTime : 0;
    const syncedState =
      typeof window.__syncRailCaptionToMediaTime === "function" ? window.__syncRailCaptionToMediaTime() : null;
    const audioTime = syncedState?.time ?? rawAudioTime;
    const state = syncedState || (typeof window.__railCaptionStateAt === "function" ? window.__railCaptionStateAt(audioTime) : null);
    const transform = stack ? getComputedStyle(stack).transform : "";
    let stackTranslateYPx = null;
    try {
      if (transform && transform !== "none") stackTranslateYPx = new DOMMatrixReadOnly(transform).m42;
    } catch {}
    const deltaPx =
      state && Number.isFinite(state.translateY) && Number.isFinite(stackTranslateYPx)
        ? stackTranslateYPx - state.translateY
        : null;
    return {
      ...setupState,
      audio_current_time_seconds: Number(audioTime.toFixed(3)),
      audio_paused: audio ? audio.paused : null,
      scrubber_value_seconds: scrubber ? Number(Number(scrubber.value || 0).toFixed(3)) : null,
      current_label: currentLabel ? currentLabel.textContent : "",
      transport_state: transportState,
      state,
      stack_translate_y_px: Number.isFinite(stackTranslateYPx) ? Number(stackTranslateYPx.toFixed(3)) : null,
      stack_state_translate_delta_px: Number.isFinite(deltaPx) ? Number(deltaPx.toFixed(3)) : null,
    };
  }, setup);
}

function comparePlayingScrubSamples({ samples, chunks }) {
  const failures = [];
  for (const sample of samples) {
    const target = Number(sample.target_time_seconds);
    const audioTime = Number(sample.audio_current_time_seconds);
    const committed = Number(sample.transport_state?.lastCommittedScrubTime);
    const scrubber = Number(sample.scrubber_value_seconds);
    const expectedChunk = activeChunkForTime(chunks, audioTime);
    if (sample.transport_state?.reviewTransportScrubModel !== "foreground_transport_scrub_lock_v1") {
      failures.push({
        time_seconds: target,
        failure: "playing scrub: foreground transport scrub-lock model is missing",
      });
    }
    if (!Number.isFinite(committed) || Math.abs(committed - target) > 0.65) {
      failures.push({
        time_seconds: target,
        failure: `playing scrub: committed time ${Number.isFinite(committed) ? committed.toFixed(3) : "missing"} did not land at target ${target.toFixed(3)}s`,
      });
    }
    if (!Number.isFinite(audioTime) || Math.abs(audioTime - target) > 2.25) {
      failures.push({
        time_seconds: target,
        failure: `playing scrub: audio currentTime ${Number.isFinite(audioTime) ? audioTime.toFixed(3) : "missing"} did not stay near target ${target.toFixed(3)}s after resume`,
      });
    }
    if (!Number.isFinite(scrubber) || Math.abs(scrubber - audioTime) > 0.75) {
      failures.push({
        time_seconds: target,
        failure: `playing scrub: foreground scrubber ${Number.isFinite(scrubber) ? scrubber.toFixed(3) : "missing"} does not track resumed audio ${audioTime.toFixed(3)}s`,
      });
    }
    if (sample.audio_paused !== false) {
      failures.push({
        time_seconds: target,
        failure: "playing scrub: playback did not resume after committing a scrub that started during playback",
      });
    }
    const playingScrubDeltaTolerancePx = sample.state?.captionStackCompositorActive ? 24 : 2;
    if (
      sample.stack_state_translate_delta_px !== null &&
      Number.isFinite(sample.stack_state_translate_delta_px) &&
      Math.abs(sample.stack_state_translate_delta_px) > playingScrubDeltaTolerancePx
    ) {
      failures.push({
        time_seconds: target,
        failure: `playing scrub: caption stack transform drifted ${sample.stack_state_translate_delta_px}px after scrub commit`,
      });
    }
    if (expectedChunk?.id && sample.state?.activeChunkId && sample.state.activeChunkId !== expectedChunk.id) {
      failures.push({
        time_seconds: target,
        failure: `playing scrub: active caption text is not bound to post-scrub audio time (expected ${expectedChunk.id}, got ${sample.state.activeChunkId})`,
      });
    }
  }
  return failures;
}

async function collectEndScreenQaState(page, endScreen) {
  if (!endScreen?.enabled) return { skipped: true, reason: "end_screen_not_enabled", samples: [] };
  const transitionStart = Number(endScreen.transitionStartSeconds || 0);
  const transitionDuration = Number(endScreen.transitionDurationSeconds || END_SCREEN_TRANSITION_DURATION_SECONDS);
  const fullOpacityAt = Number(endScreen.fullOpacityAtSeconds || endScreen.holdStartSeconds || transitionStart + transitionDuration);
  const approvedFadeStart = Number(endScreen.reviewApprovedFadeStartSeconds ?? endScreen.transitionStartSeconds);
  const lastCaptionExitStart = Number(endScreen.lastCaptionVisibleExitStartSeconds || transitionStart);
  const lastCaptionSuppressed = Number(endScreen.lastCaptionFullySuppressedSeconds || fullOpacityAt);
  const safeStart = Number(endScreen.safeWindowStartSeconds || endScreen.holdStartSeconds || transitionStart + transitionDuration);
  const times = uniqueSorted([
    Math.max(0, approvedFadeStart - 1),
    Math.max(0, approvedFadeStart - 0.05),
    approvedFadeStart,
    transitionStart + transitionDuration / 2,
    fullOpacityAt + 0.05,
    safeStart + Math.max(0.1, transitionDuration + 0.2),
  ]);
  const samples = [];
  for (const time of times) {
    await setDirectTime(page, time);
    samples.push(await page.evaluate((sampleTime) => {
      const overlay = document.querySelector(".ce-youtube-end-screen");
      const style = overlay ? getComputedStyle(overlay) : null;
      const state = typeof window.__endScreenStateAt === "function" ? window.__endScreenStateAt(sampleTime) : null;
      const railState = typeof window.__railCaptionStateAt === "function" ? window.__railCaptionStateAt(sampleTime) : null;
      const contract = window.__endScreenPaletteContract || null;
      const inheritedEndScreens = [...document.querySelectorAll("#endScreen, #outroScreen, .end-screen, .outro-screen, .youtube-end-screen, [data-youtube-end-screen]")]
        .filter((node) => node && !node.classList.contains("ce-youtube-end-screen"));
      const visibleInheritedEndScreens = inheritedEndScreens.filter((node) => {
        const inheritedStyle = getComputedStyle(node);
        const rect = node.getBoundingClientRect();
        return inheritedStyle.display !== "none" &&
          inheritedStyle.visibility !== "hidden" &&
          Number(inheritedStyle.opacity || 0) > 0.01 &&
          rect.width > 1 &&
          rect.height > 1;
      });
      return {
        time_seconds: sampleTime,
        overlay_present: Boolean(overlay),
        opacity: style ? Number(Number(style.opacity || 0).toFixed(4)) : null,
        inherited_end_screen_count: inheritedEndScreens.length,
        visible_inherited_end_screen_count: visibleInheritedEndScreens.length,
        template_id: overlay?.dataset.templateId || state?.youtubeEndScreenTemplateId || "",
        fade_timing_model: overlay?.dataset.fadeTimingModel || state?.fadeTimingModel || "",
        caption_end_screen_handoff_model: state?.captionEndScreenHandoffModel || railState?.captionEndScreenHandoffModel || "",
        review_approved_end_screen_entry_model:
          state?.reviewApprovedEndScreenEntryModel || railState?.reviewApprovedEndScreenEntryModel || "",
        review_approved_youtube_placeholder_fade_start_seconds:
          state?.reviewApprovedEndScreenFadeStartSeconds ?? railState?.reviewApprovedEndScreenFadeStartSeconds ?? null,
        last_caption_visible_exit_start_seconds:
          state?.lastCaptionVisibleExitStartSeconds ?? railState?.lastCaptionVisibleExitStartSeconds ?? null,
        last_caption_fully_suppressed_seconds:
          state?.lastCaptionFullySuppressedSeconds ?? railState?.lastCaptionFullySuppressedSeconds ?? null,
        youtube_placeholder_fade_start_seconds:
          state?.youtubePlaceholderFadeStartSeconds ?? railState?.youtubePlaceholderFadeStartSeconds ?? null,
        youtube_placeholder_full_opacity_seconds:
          state?.youtubePlaceholderFullOpacitySeconds ?? railState?.youtubePlaceholderFullOpacitySeconds ?? null,
        caption_end_screen_gap_seconds: state?.captionEndScreenGapSeconds ?? railState?.captionEndScreenGapSeconds ?? null,
        caption_end_screen_overlap_read: state?.captionEndScreenOverlapRead || railState?.captionEndScreenOverlapRead || "",
        final_caption_opacity: railState?.finalCaptionOpacity ?? null,
        max_visible_caption_opacity: railState?.maxVisibleCaptionOpacity ?? null,
        source_rail_opacity: railState?.sourceRailOpacity ?? null,
        end_screen_safe_window_active: state?.isSafeWindow || railState?.endScreenSafeWindowActive || false,
        youtube_safe_window_caption_suppression_read: state?.youtubeSafeWindowCaptionSuppressionRead || "",
        palette_contract_id: overlay?.dataset.paletteContractId || contract?.contract_id || "",
        palette_treatment_model: contract?.sampled_backplate?.palette_treatment_model || contract?.target_palette?.palette_treatment_model || "",
        palette_source: contract?.palette_source || "",
        source_backplate_path: contract?.approved_backplate?.path || "",
        colors: contract?.colors || {},
      };
    }, time));
  }
  return {
    skipped: false,
    entryTimingModel: endScreenEntryTimingModel({}, endScreen),
    transitionStart,
    transitionDuration,
    fullOpacityAt,
    approvedFadeStart,
    lastCaptionExitStart,
    lastCaptionSuppressed,
    safeStart,
    samples,
  };
}

function compareEndScreenQaState(endScreenQa) {
  const failures = [];
  if (endScreenQa.skipped) {
    return [{ time_seconds: null, failure: `end screen: ${endScreenQa.reason || "runtime QA skipped"}` }];
  }
  const [before, preFade, fadeStart, mid, full, safe] = endScreenQa.samples;
  if (!endScreenQa.samples.every((sample) => sample.overlay_present)) {
    failures.push({ time_seconds: null, failure: "end screen: adaptive overlay is missing" });
  }
  if (before && Number(before.opacity) > 0.05) {
    failures.push({ time_seconds: before.time_seconds, failure: `end screen: opacity before transition is ${before.opacity}, expected near 0` });
  }
  if (preFade && Number(preFade.opacity) > 0.05) {
    failures.push({ time_seconds: preFade.time_seconds, failure: `end screen: opacity before approved fade start is ${preFade.opacity}, expected near 0` });
  }
  if (fadeStart && Number(fadeStart.opacity) > 0.18) {
    failures.push({ time_seconds: fadeStart.time_seconds, failure: `end screen: opacity at approved fade start is ${fadeStart.opacity}, expected near 0` });
  }
  if (mid && !(Number(mid.opacity) > 0.05 && Number(mid.opacity) < 0.95)) {
    failures.push({ time_seconds: mid.time_seconds, failure: `end screen: opacity during fade is ${mid.opacity}, expected between 0 and 1` });
  }
  if (full && Number(full.opacity) < 0.92) {
    failures.push({ time_seconds: full.time_seconds, failure: `end screen: opacity when final caption is suppressed is ${full.opacity}, expected fully visible` });
  }
  if (safe && Number(safe.opacity) < 0.92) {
    failures.push({ time_seconds: safe.time_seconds, failure: `end screen: opacity at safe window is ${safe.opacity}, expected fully visible` });
  }
  for (const sample of endScreenQa.samples) {
    const legalWindowEntry = endScreenQa.entryTimingModel === YOUTUBE_LEGAL_WINDOW_END_SCREEN_ENTRY_MODEL;
    const expectedFadeTimingModel = legalWindowEntry ? YOUTUBE_LEGAL_WINDOW_END_SCREEN_ENTRY_MODEL : END_SCREEN_FADE_TIMING_MODEL;
    const expectedHandoffModel = legalWindowEntry ? YOUTUBE_LEGAL_WINDOW_END_SCREEN_ENTRY_MODEL : CAPTION_END_SCREEN_HANDOFF_MODEL;
    if (sample.template_id !== "adaptive_titleless_youtube_end_screen_overlay_on_living_cover_v1") {
      failures.push({ time_seconds: sample.time_seconds, failure: `end screen: template id is ${sample.template_id || "missing"}, expected adaptive titleless template` });
    }
    if (sample.fade_timing_model !== expectedFadeTimingModel) {
      failures.push({ time_seconds: sample.time_seconds, failure: `end screen: fade timing model is ${sample.fade_timing_model || "missing"}` });
    }
    if (sample.caption_end_screen_handoff_model !== expectedHandoffModel) {
      failures.push({
        time_seconds: sample.time_seconds,
        failure: `end screen: handoff model is ${sample.caption_end_screen_handoff_model || "missing"}`,
      });
    }
    if (sample.review_approved_end_screen_entry_model !== expectedHandoffModel) {
      failures.push({ time_seconds: sample.time_seconds, failure: "end screen: review-approved entry model is missing" });
    }
    if (Number(sample.visible_inherited_end_screen_count || 0) > 0) {
      failures.push({
        time_seconds: sample.time_seconds,
        failure: `end screen: ${sample.visible_inherited_end_screen_count} inherited end-screen layer(s) are visible`,
      });
    }
    if (sample.palette_source !== "sampled_episode_backplate" || !sample.source_backplate_path) {
      failures.push({ time_seconds: sample.time_seconds, failure: "end screen: palette contract is not tied to the episode backplate" });
    }
    const colorText = JSON.stringify(sample.colors || {});
    if (/184,\s*111,\s*111|111,\s*184,\s*184|124,\s*111,\s*184|challenger/i.test(colorText + sample.template_id)) {
      failures.push({ time_seconds: sample.time_seconds, failure: "end screen: palette still contains Challenger-style copied red/cyan/purple treatment" });
    }
  }
  const reference = endScreenQa.samples.find((sample) => sample.caption_end_screen_handoff_model) || {};
  const fadeStartSeconds = Number(reference.youtube_placeholder_fade_start_seconds);
  const suppressedSeconds = Number(reference.last_caption_fully_suppressed_seconds);
  const fullSeconds = Number(reference.youtube_placeholder_full_opacity_seconds);
  const gapSeconds = Number(reference.caption_end_screen_gap_seconds);
  const transitionDuration = Number(endScreenQa.transitionDuration);
  const approvedFadeStartSeconds = Number(reference.review_approved_youtube_placeholder_fade_start_seconds ?? endScreenQa.approvedFadeStart);
  const legalWindowEntry = endScreenQa.entryTimingModel === YOUTUBE_LEGAL_WINDOW_END_SCREEN_ENTRY_MODEL;
  const captionTimingPass = legalWindowEntry
    ? Number.isFinite(suppressedSeconds) && suppressedSeconds <= fadeStartSeconds + 0.05
    : Number.isFinite(suppressedSeconds) && fadeStartSeconds <= suppressedSeconds && Math.abs(fullSeconds - suppressedSeconds) <= 0.05;
  const gapPass = legalWindowEntry
    ? Number.isFinite(gapSeconds) &&
      gapSeconds >= 0 &&
      reference.caption_end_screen_overlap_read === "pass_youtube_legal_window_entry_after_caption_suppression"
    : Number.isFinite(gapSeconds) &&
      gapSeconds <= 0.05 &&
      reference.caption_end_screen_overlap_read === "pass_review_approved_end_screen_entry_no_blank_gap";
  if (
    !Number.isFinite(fadeStartSeconds) ||
    !Number.isFinite(suppressedSeconds) ||
    !Number.isFinite(fullSeconds) ||
    !Number.isFinite(approvedFadeStartSeconds) ||
    Math.abs(fadeStartSeconds - approvedFadeStartSeconds) > 0.05 ||
    Math.abs(fullSeconds - (approvedFadeStartSeconds + END_SCREEN_TRANSITION_DURATION_SECONDS)) > 0.05 ||
    !captionTimingPass ||
    !gapPass
  ) {
    failures.push({
      time_seconds: Number.isFinite(fadeStartSeconds) ? fadeStartSeconds : null,
      failure: "end screen: review-approved fade start, full opacity, and caption suppression are not aligned",
    });
  }
  if (!Number.isFinite(transitionDuration) || Math.abs(transitionDuration - END_SCREEN_TRANSITION_DURATION_SECONDS) > 0.015) {
    failures.push({
      time_seconds: Number.isFinite(fadeStartSeconds) ? fadeStartSeconds : null,
      failure: `end screen: transition duration ${transitionDuration}s is not the shared 300ms value`,
    });
  }
  if (safe && (Number(safe.max_visible_caption_opacity) > 0.02 || Number(safe.final_caption_opacity) > 0.02)) {
    failures.push({
      time_seconds: safe.time_seconds,
      failure: "end screen: rolling caption text remains visible during the YouTube safe window",
    });
  }
  return failures;
}

function sampleAdaptiveAuditPixels({ baseScreenshotPath, overlayScreenshotPath, samples }) {
  const script = `
import json
import sys
from PIL import Image

payload = json.load(sys.stdin)
base = Image.open(payload["baseScreenshotPath"]).convert("RGBA")
overlay = Image.open(payload["overlayScreenshotPath"]).convert("RGBA")

def parse_rgba(value):
    text = str(value or "").strip().lower()
    if text.startswith("#") and len(text) == 7:
        return [int(text[1:3], 16), int(text[3:5], 16), int(text[5:7], 16), 1.0]
    if text.startswith("rgb"):
        inside = text[text.find("(") + 1:text.rfind(")")]
        parts = [part.strip() for part in inside.split(",")]
        alpha = float(parts[3]) if len(parts) > 3 else 1.0
        return [float(parts[0]), float(parts[1]), float(parts[2]), alpha]
    raise ValueError(f"Unsupported color: {value}")

def composite(fg, bg):
    alpha = max(0.0, min(1.0, float(fg[3])))
    return [
        round(float(fg[0]) * alpha + float(bg[0]) * (1 - alpha)),
        round(float(fg[1]) * alpha + float(bg[1]) * (1 - alpha)),
        round(float(fg[2]) * alpha + float(bg[2]) * (1 - alpha)),
    ]

out = []
for sample in payload["samples"]:
    x = max(0, min(base.width - 1, int(round(sample["x"]))))
    y = max(0, min(base.height - 1, int(round(sample["y"]))))
    base_rgb = list(base.getpixel((x, y))[:3])
    actual_rgb = list(overlay.getpixel((x, y))[:3])
    expected_rgba = parse_rgba(sample["expected_rgba"])
    expected_rgb = composite(expected_rgba, base_rgb)
    deltas = [abs(actual_rgb[i] - expected_rgb[i]) for i in range(3)]
    max_delta = max(deltas)
    out.append({
        **sample,
        "x": x,
        "y": y,
        "base_rgb": base_rgb,
        "actual_rgb": actual_rgb,
        "expected_rgb": expected_rgb,
        "channel_deltas": deltas,
        "max_channel_delta": max_delta,
        "pass": max_delta <= float(sample.get("tolerance", 18)),
    })

print(json.dumps(out))
`;
  const result = spawnSync("python3", ["-c", script], {
    input: JSON.stringify({ baseScreenshotPath, overlayScreenshotPath, samples }),
    encoding: "utf8",
    maxBuffer: 1024 * 1024,
  });
  if (result.status !== 0) {
    return {
      ok: false,
      error: result.stderr || result.stdout || "pixel sampler failed",
      samples: [],
    };
  }
  try {
    return { ok: true, samples: JSON.parse(result.stdout) };
  } catch (error) {
    return { ok: false, error: error.message, samples: [] };
  }
}

function borderlessUnderlayModel(value) {
  return String(value || "") === YOUTUBE_PLACEHOLDER_BORDERLESS_UNDERLAY_MODEL;
}

function expectedTargetStyleContract(contract) {
  const targets = contract?.target_palette?.targets || {};
  const styleModel =
    contract?.placeholder_style_model ||
    contract?.target_palette?.placeholder_style_model ||
    contract?.target_palette?.style_model ||
    "";
  return {
    left_video: {
      selector: ".left-video",
      targetKey: "left_video",
      styleModel,
      fill: targets.left_video?.fill_rgba,
      border: targets.left_video?.border_rgba,
      ring: targets.left_video?.ring_rgba,
      borderSample: "left",
      ringSample: "left",
    },
    right_video: {
      selector: ".right-video",
      targetKey: "right_video",
      styleModel,
      fill: targets.right_video?.fill_rgba,
      border: targets.right_video?.border_rgba,
      ring: targets.right_video?.ring_rgba,
      borderSample: "right",
      ringSample: "right",
    },
    center_subscribe: {
      selector: ".subscribe-target",
      targetKey: "center_subscribe",
      styleModel,
      fill: targets.center_subscribe?.fill_rgba,
      border: targets.center_subscribe?.border_rgba,
      ring: targets.center_subscribe?.ring_rgba,
      borderSample: "top",
      ringSample: "top",
    },
  };
}

function compareComputedStyleSamples(targets) {
  const failures = [];
  for (const [key, target] of Object.entries(targets || {})) {
    if (!target.present) {
      failures.push(`adaptive render audit: ${key} target is missing`);
      continue;
    }
    if (borderlessUnderlayModel(target.expected?.styleModel)) {
      const actualFill = target.computed?.fill;
      const expectedFill = target.expected?.fill;
      const borderWidth = Number(target.computed?.borderWidth) || 0;
      const boxShadow = String(target.computed?.boxShadow || "none").trim();
      if (!expectedFill || !colorsMatch(actualFill, expectedFill, 1.5)) {
        failures.push(
          `adaptive render audit: ${key} fill computed style ${actualFill || "missing"} does not match contract ${expectedFill || "missing"}`,
        );
      }
      if (borderWidth !== 0) {
        failures.push(`adaptive render audit: ${key} border width is ${borderWidth}, expected 0 for borderless underlay`);
      }
      if (boxShadow && boxShadow !== "none") {
        failures.push(`adaptive render audit: ${key} box-shadow is ${boxShadow}, expected none for borderless underlay`);
      }
      if (key === "center_subscribe") {
        const after = target.computed?.after || {};
        const afterContent = String(after.content || "").replace(/^["']|["']$/g, "");
        const afterDisplay = String(after.display || "");
        const afterBorderWidth = Number(after.borderWidth) || 0;
        const afterBoxShadow = String(after.boxShadow || "none").trim();
        if (!["none", "normal", ""].includes(afterContent) && afterDisplay !== "none") {
          failures.push(`adaptive render audit: subscribe inner ring pseudo-element content is ${after.content}`);
        }
        if (afterDisplay !== "none" && afterBorderWidth !== 0) {
          failures.push(
            `adaptive render audit: subscribe inner ring pseudo-element border width is ${afterBorderWidth}, expected hidden/0`,
          );
        }
        if (afterBoxShadow && afterBoxShadow !== "none") {
          failures.push(`adaptive render audit: subscribe inner ring pseudo-element box-shadow is ${afterBoxShadow}`);
        }
      }
      continue;
    }
    for (const property of ["fill", "border", "ring"]) {
      const actual = target.computed?.[property];
      const expected = target.expected?.[property];
      if (!expected || !colorsMatch(actual, expected, property === "ring" ? 2.5 : 1.5)) {
        failures.push(
          `adaptive render audit: ${key} ${property} computed style ${actual || "missing"} does not match contract ${expected || "missing"}`,
        );
      }
    }
  }
  return failures;
}

function comparePixelSamples(samples, samplerOk) {
  if (!samplerOk) return ["adaptive render audit: pixel sampler failed"];
  return (samples || [])
    .filter((sample) => !sample.pass)
    .map(
      (sample) =>
        `adaptive render audit: ${sample.target_key} ${sample.sample_role} pixel delta ${sample.max_channel_delta} exceeds tolerance ${sample.tolerance}`,
    );
}

async function collectEndScreenAdaptiveRenderAudit({ page, manifest, manifestPath, endScreen, qaDir }) {
  const auditDir = path.join(qaDir, "end_screen_adaptive_render_audit");
  fs.mkdirSync(auditDir, { recursive: true });
  const auditPath = path.join(auditDir, "end_screen_adaptive_render_audit.json");
  const baseScreenshotPath = path.join(auditDir, "end_screen_backplate_reference.png");
  const overlayScreenshotPath = path.join(auditDir, "end_screen_adaptive_overlay.png");
  const auditTime = Number(endScreen?.fullOpacityAtSeconds || endScreen?.holdStartSeconds || endScreen?.transitionStartSeconds || 0) + 0.05;
  await setDirectTime(page, auditTime);
  const styleState = await page.evaluate((time) => {
    const overlay = document.querySelector(".ce-youtube-end-screen");
    if (typeof window.__setRenderTime === "function") window.__setRenderTime(time);
    const contract = window.__endScreenPaletteContract || null;
    const placeholderStyleModel =
      contract?.placeholder_style_model ||
      contract?.target_palette?.placeholder_style_model ||
      contract?.target_palette?.style_model ||
      "";
    const targetSpecs = {
      left_video: { selector: ".left-video", ringVar: "--ce-end-screen-video-ring-left" },
      right_video: { selector: ".right-video", ringVar: "--ce-end-screen-video-ring-right" },
      center_subscribe: { selector: ".subscribe-target", ringVar: "--ce-end-screen-subscribe-soft-ring" },
    };
    const stage =
      document.querySelector(".frame.ce-fixed-stage") ||
      document.querySelector(".stage") ||
      document.querySelector("#stage") ||
      document.querySelector(".frame");
    const stageRect = stage ? stage.getBoundingClientRect() : null;
    const targets = {};
    for (const [key, spec] of Object.entries(targetSpecs)) {
      const node = overlay ? overlay.querySelector(spec.selector) : null;
      const style = node ? getComputedStyle(node) : null;
      const afterStyle = node ? getComputedStyle(node, "::after") : null;
      const rect = node ? node.getBoundingClientRect() : null;
      const borderWidth = style ? Number.parseFloat(style.borderLeftWidth || style.borderTopWidth || "0") || 0 : 0;
      targets[key] = {
        present: Boolean(node),
        rect: rect
          ? {
              left: rect.left,
              top: rect.top,
              right: rect.right,
              bottom: rect.bottom,
              width: rect.width,
              height: rect.height,
            }
          : null,
        computed: style
          ? {
              fill: style.backgroundColor,
              border: style.borderLeftColor || style.borderTopColor,
              ring: style.getPropertyValue(spec.ringVar).trim(),
              boxShadow: style.boxShadow,
              borderWidth,
              after: afterStyle
                ? {
                    content: afterStyle.content,
                    display: afterStyle.display,
                    borderWidth:
                      Number.parseFloat(afterStyle.borderLeftWidth || afterStyle.borderTopWidth || "0") || 0,
                    boxShadow: afterStyle.boxShadow,
                  }
                : null,
            }
          : {},
      };
    }
    return {
      audit_time_seconds: time,
      overlay_present: Boolean(overlay),
      overlay_opacity: overlay ? Number(Number(getComputedStyle(overlay).opacity || 0).toFixed(4)) : null,
      stage_rect: stageRect
        ? {
            left: stageRect.left,
            top: stageRect.top,
            width: stageRect.width,
            height: stageRect.height,
          }
        : null,
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight,
      },
      palette_contract_id: contract?.contract_id || "",
      palette_source: contract?.palette_source || "",
      placeholder_style_model: placeholderStyleModel,
      approved_backplate: contract?.approved_backplate || null,
      contract,
      targets,
    };
  }, auditTime);
  const expected = expectedTargetStyleContract(styleState.contract);
  const isBorderlessUnderlay = borderlessUnderlayModel(styleState.placeholder_style_model);
  const targets = {};
  for (const [key, target] of Object.entries(styleState.targets || {})) {
    targets[key] = {
      ...target,
      expected: expected[key] || {},
      computed_normalized: {
        fill: normalizeCssColor(target.computed?.fill),
        border: normalizeCssColor(target.computed?.border),
        ring: normalizeCssColor(target.computed?.ring),
      },
      expected_normalized: {
        fill: normalizeCssColor(expected[key]?.fill),
        border: normalizeCssColor(expected[key]?.border),
        ring: normalizeCssColor(expected[key]?.ring),
      },
    };
  }
  const computedStyleFailures = compareComputedStyleSamples(targets);
  await page.evaluate(() => {
    const overlay = document.querySelector(".ce-youtube-end-screen");
    if (!overlay) return;
    overlay.dataset.ceAuditSavedVisibility = overlay.style.visibility || "";
    overlay.style.visibility = "hidden";
  });
  await page.screenshot({ path: baseScreenshotPath, fullPage: false });
  await page.evaluate(() => {
    const overlay = document.querySelector(".ce-youtube-end-screen");
    if (!overlay) return;
    overlay.style.visibility = overlay.dataset.ceAuditSavedVisibility || "";
    delete overlay.dataset.ceAuditSavedVisibility;
  });
  await page.screenshot({ path: overlayScreenshotPath, fullPage: false });
  const pixelSampleRequests = [];
  for (const [key, target] of Object.entries(targets)) {
    const rect = target.rect || {};
    const borderWidth = Math.max(1, Number(target.computed?.borderWidth) || (key === "center_subscribe" ? 7 : 4));
    const centerX = Number(rect.left) + Number(rect.width) / 2;
    const centerY = Number(rect.top) + Number(rect.height) / 2;
    if (!Number.isFinite(centerX) || !Number.isFinite(centerY)) continue;
    pixelSampleRequests.push({
      target_key: key,
      sample_role: "fill_center",
      x: centerX,
      y: centerY,
      expected_rgba: target.expected?.fill,
      tolerance: 18,
    });
    if (isBorderlessUnderlay) continue;
    if (key === "left_video") {
      pixelSampleRequests.push({
        target_key: key,
        sample_role: "border_midpoint",
        x: Number(rect.left) + borderWidth / 2,
        y: centerY,
        expected_rgba: target.expected?.border,
        tolerance: 22,
      });
      pixelSampleRequests.push({
        target_key: key,
        sample_role: "outer_ring_midpoint",
        x: Number(rect.left) - 5,
        y: centerY,
        expected_rgba: target.expected?.ring,
        tolerance: 28,
      });
    } else if (key === "right_video") {
      const rightEdgeVisible = Number(rect.right) <= Number(styleState.viewport?.width || 0) - 2;
      const borderX = rightEdgeVisible ? Number(rect.right) - borderWidth / 2 : Number(rect.left) + borderWidth / 2;
      const ringX = rightEdgeVisible ? Number(rect.right) + 5 : Number(rect.left) - 5;
      pixelSampleRequests.push({
        target_key: key,
        sample_role: "border_midpoint",
        x: borderX,
        y: centerY,
        expected_rgba: target.expected?.border,
        tolerance: 22,
      });
      pixelSampleRequests.push({
        target_key: key,
        sample_role: "outer_ring_midpoint",
        x: ringX,
        y: centerY,
        expected_rgba: target.expected?.ring,
        tolerance: 28,
      });
    } else {
      pixelSampleRequests.push({
        target_key: key,
        sample_role: "border_midpoint",
        x: centerX,
        y: Number(rect.top) + borderWidth / 2,
        expected_rgba: target.expected?.border,
        tolerance: 24,
      });
      pixelSampleRequests.push({
        target_key: key,
        sample_role: "outer_ring_midpoint",
        x: centerX,
        y: Number(rect.top) - 9,
        expected_rgba: target.expected?.ring,
        tolerance: 30,
      });
    }
  }
  const pixelResult = sampleAdaptiveAuditPixels({
    baseScreenshotPath,
    overlayScreenshotPath,
    samples: pixelSampleRequests.filter((sample) => sample.expected_rgba),
  });
  const pixelFailures = comparePixelSamples(pixelResult.samples, pixelResult.ok);
  const sourceArtPath = manifest.source_visual?.source_art_path || "";
  const activeSourceSha = sha256File(sourceArtPath);
  const contractSourcePath = styleState.approved_backplate?.path || "";
  const contractSourceSha = styleState.approved_backplate?.sha256 || "";
  const sourceFailures = [];
  if (!sourceArtPath || !contractSourcePath || path.resolve(sourceArtPath) !== path.resolve(contractSourcePath)) {
    sourceFailures.push("adaptive render audit: palette contract source backplate does not match active source art path");
  }
  if (!activeSourceSha || activeSourceSha === "missing" || activeSourceSha !== contractSourceSha) {
    sourceFailures.push("adaptive render audit: palette contract source backplate sha256 does not match active source art");
  }
  const failures = [
    ...(!styleState.overlay_present ? ["adaptive render audit: adaptive end-screen overlay is missing"] : []),
    ...(Number(styleState.overlay_opacity) < 0.92 ? [`adaptive render audit: overlay opacity is ${styleState.overlay_opacity}, expected full opacity`] : []),
    ...computedStyleFailures,
    ...pixelFailures,
    ...sourceFailures,
  ];
  const artifact = {
    model: END_SCREEN_ADAPTIVE_RENDER_AUDIT_MODEL,
    created_utc: new Date().toISOString(),
    episode_id: manifest.episode_id,
    audit_time_seconds: Number(auditTime.toFixed(3)),
    manifest_path: manifestPath,
    source_art_path: sourceArtPath,
    source_art_sha256: activeSourceSha,
    contract_source_art_path: contractSourcePath,
    contract_source_art_sha256: contractSourceSha,
    palette_contract_id: styleState.palette_contract_id,
    palette_source: styleState.palette_source,
    placeholder_style_model: styleState.placeholder_style_model,
    base_screenshot_path: baseScreenshotPath,
    screenshot_path: overlayScreenshotPath,
    target_computed_styles: targets,
    pixel_samples: pixelResult.samples,
    pixel_sampler_error: pixelResult.ok ? "" : pixelResult.error,
    computed_style_failure_count: computedStyleFailures.length,
    pixel_sample_failure_count: pixelFailures.length,
    source_backplate_failure_count: sourceFailures.length,
    failure_count: failures.length,
    passed: failures.length === 0,
    failures,
    reads: {
      end_screen_adaptive_computed_style_read: computedStyleFailures.length
        ? FAIL_ADAPTIVE_COMPUTED_STYLE
        : PASS_ADAPTIVE_COMPUTED_STYLE,
      end_screen_adaptive_pixel_sample_read: pixelFailures.length
        ? FAIL_ADAPTIVE_PIXEL_SAMPLE
        : PASS_ADAPTIVE_PIXEL_SAMPLE,
      end_screen_adaptive_render_audit_read: failures.length ? FAIL_ADAPTIVE_RENDER_AUDIT : PASS_ADAPTIVE_RENDER_AUDIT,
    },
  };
  writeJson(auditPath, artifact);
  return { artifact, artifactPath: auditPath };
}

function compareSamples({ time, direct, scrub, expectedVisible, expectedChunk, firstCueStart, lastCueEnd, endScreen }) {
  const failures = [];
  const safeStart = Number(endScreen?.safeWindowStartSeconds || endScreen?.holdStartSeconds || Infinity);
  const endScreenSample = time >= safeStart - 0.1;
  for (const sample of [direct, scrub]) {
    if (expectedVisible) {
      if (sample.visible_line_count <= 0 || sample.max_visible_caption_opacity <= 0.035) {
        failures.push(
          `${sample.method}: no visible captions at ${time.toFixed(3)}s inside VO window (${firstCueStart.toFixed(3)}-${lastCueEnd.toFixed(3)}s)`,
        );
      }
      if (sample.state?.activeChunkIndex === sample.state?.nearestVisibleChunkIndex && !sample.state?.activeChunkText) {
        failures.push(`${sample.method}: missing active chunk text at ${time.toFixed(3)}s`);
      }
      if (expectedChunk?.id && sample.state?.activeChunkId && sample.state.activeChunkId !== expectedChunk.id) {
        failures.push(
          `${sample.method}: active caption text is not bound to audio time at ${time.toFixed(3)}s (expected ${expectedChunk.id}, got ${sample.state.activeChunkId})`,
        );
      }
    }
    if (endScreenSample && (sample.visible_line_count > 0 || sample.max_visible_caption_opacity > 0.02)) {
      failures.push(`${sample.method}: residual caption text during end-screen safe window at ${time.toFixed(3)}s`);
    }
    if (sample.max_text_right_overflow_px > 2 || sample.max_text_left_overflow_px > 2) {
      failures.push(
        `${sample.method}: visible caption text clips outside rail at ${time.toFixed(3)}s (right=${sample.max_text_right_overflow_px}px left=${sample.max_text_left_overflow_px}px)`,
      );
    }
    if (sample.caption_stack_paint_clip_risk_count > 0 || sample.max_caption_stack_paint_overflow_px > 1) {
      failures.push(
        `${sample.method}: visible right-rail caption lines are outside the caption stack paint box at ${time.toFixed(3)}s (count=${sample.caption_stack_paint_clip_risk_count}, overflow=${sample.max_caption_stack_paint_overflow_px}px)`,
      );
    }
    if (
      sample.stack_state_translate_delta_px !== null &&
      Number.isFinite(sample.stack_state_translate_delta_px) &&
      Math.abs(sample.stack_state_translate_delta_px) > 1.5
    ) {
      failures.push(
        `${sample.method}: caption stack transform drifted ${sample.stack_state_translate_delta_px}px from audio-time state at ${time.toFixed(3)}s`,
      );
    }
  }
  if (Math.abs((direct.audio_current_time_seconds ?? time) - time) > 0.35) {
    failures.push(`direct: audio currentTime did not land at requested time ${time.toFixed(3)}s`);
  }
  if (Math.abs((scrub.scrubber_value_seconds ?? time) - time) > 0.11) {
    failures.push(`scrub: foreground scrubber did not hold requested time ${time.toFixed(3)}s`);
  }
  if (
    direct.state?.activeChunkId &&
    scrub.state?.activeChunkId &&
    direct.state.activeChunkId !== scrub.state.activeChunkId
  ) {
    failures.push(
      `scrub mismatch: direct active ${direct.state.activeChunkId} != scrub active ${scrub.state.activeChunkId} at ${time.toFixed(3)}s`,
    );
  }
  return failures;
}

function comparePlaybackSyncSamples({ samples, chunks, firstCueStart, lastCueEnd, endScreen }) {
  const failures = [];
  for (const sample of samples) {
    const time = Number(sample.audio_current_time_seconds);
    const expectedVisible = isExpectedVisible(time, firstCueStart, lastCueEnd, endScreen);
    const expectedChunk = activeChunkForTime(chunks, time);
    const playbackDeltaTolerancePx = sample.state?.captionStackCompositorActive ? 24 : 2;
    if (
      sample.stack_state_translate_delta_px !== null &&
      Number.isFinite(sample.stack_state_translate_delta_px) &&
      Math.abs(sample.stack_state_translate_delta_px) > playbackDeltaTolerancePx
    ) {
      failures.push({
        time_seconds: time,
        failure: `playback: caption stack transform drifted ${sample.stack_state_translate_delta_px}px from audio.currentTime at ${time.toFixed(3)}s`,
      });
    }
    if (expectedVisible && expectedChunk?.id && sample.state?.activeChunkId && sample.state.activeChunkId !== expectedChunk.id) {
      failures.push({
        time_seconds: time,
        failure: `playback: active caption text is not bound to audio.currentTime at ${time.toFixed(3)}s (expected ${expectedChunk.id}, got ${sample.state.activeChunkId})`,
      });
    }
  }
  return failures;
}

async function qaManifest({ manifestPath, browser, baseUrl }) {
  const manifest = readJson(manifestPath);
  const playerPath = manifest.proof_artifacts?.player_html_path || path.join(path.dirname(manifestPath), "player.html");
  const html = fs.readFileSync(playerPath, "utf8");
  const chunks = extractConstJson(html, "CE_CHUNKS") || [];
  const endScreen = extractConstJson(html, "CE_END_SCREEN") || { enabled: false };
  if (
    !isYoutubeLegalWindowEndScreenEntry(manifest, endScreen) &&
    Number.isFinite(APPROVED_END_SCREEN_FADE_START_SECONDS[manifest.episode_id])
  ) {
    endScreen.reviewApprovedFadeStartSeconds = APPROVED_END_SCREEN_FADE_START_SECONDS[manifest.episode_id];
  }
  if (!chunks.length) throw new Error(`No injected CE_CHUNKS found in ${playerPath}`);

  const firstCueStart = Number(chunks[0].start || 0);
  const lastCueEnd = Number(chunks[chunks.length - 1].end || 0);
  let sampleTimes = sampleTimesFor(manifest, chunks, endScreen);
  const qaDir = path.join(path.dirname(manifestPath), "qa");
  const screenshotDir = path.join(qaDir, "runtime_coverage_failures");
  fs.mkdirSync(qaDir, { recursive: true });
  fs.mkdirSync(screenshotDir, { recursive: true });

  const page = await browser.newPage({
    viewport: { width: 1920, height: 1180 },
    deviceScaleFactor: 1,
    colorScheme: "dark",
  });
  page.on("console", (msg) => {
    if (msg.type() === "error") console.error(`[${manifest.episode_id}] browser console: ${msg.text()}`);
  });
  const url = `${baseUrl}${relUrlForPath(playerPath)}`;
  const samples = [];
  const failures = [];
  let endScreenQaResult = null;
  let adaptiveRenderAuditResult = null;
  try {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForSelector(".ce-review-transport [data-ce-scrub]", { timeout: 20000 });
    await page.waitForSelector(".ce-caption-line", { timeout: 20000 });
    const freshnessGuard = await page.evaluate(() => {
      const build = window.__ceProofBuild || {};
      const hasCheck = typeof window.__ceRunProofFreshnessCheck === "function";
      const hasWarn = typeof window.__ceShowStaleProofWarning === "function";
      const warningShown = hasWarn ? window.__ceShowStaleProofWarning({ proof_build_id: "qa_stale_build" }) : false;
      const warning = document.querySelector(".ce-proof-freshness-warning");
      const style = warning ? getComputedStyle(warning) : null;
      const visible =
        Boolean(warning) &&
        warning.hidden === false &&
        style &&
        style.display !== "none" &&
        style.visibility !== "hidden" &&
        Number.parseFloat(style.opacity || "1") > 0;
      if (warning) warning.hidden = true;
      return {
        proof_build_id: build.proof_build_id || "",
        proof_generated_at_utc: build.proof_generated_at_utc || "",
        intro_trim_model: build.intro_trim_model || "",
        intro_trim_seconds: Number(build.intro_trim_seconds),
        previous_voice_start_offset_seconds: Number(build.previous_voice_start_offset_seconds),
        voice_start_offset_seconds: Number(build.voice_start_offset_seconds),
        has_check_hook: hasCheck,
        has_warning_hook: hasWarn,
        stale_warning_visible_when_forced: visible,
        warning_text: warning ? (warning.textContent || "").replace(/\s+/g, " ").trim() : "",
      };
    });
    if (
      !freshnessGuard.proof_build_id ||
      !freshnessGuard.has_check_hook ||
      !freshnessGuard.has_warning_hook ||
      !freshnessGuard.stale_warning_visible_when_forced ||
      !/This proof has been regenerated\. Refresh before reviewing\./.test(freshnessGuard.warning_text)
    ) {
      failures.push({
        time_seconds: null,
        failure: "proof build freshness guard is missing or does not surface a stale-tab warning",
      });
    }
    const initialTrimState = await page.evaluate(() => {
      const state = typeof window.__railCaptionStateAt === "function" ? window.__railCaptionStateAt(0) || {} : {};
      return {
        intro_trim_model: state.introTrimModel || "",
        intro_trim_seconds: Number(state.introTrimSeconds),
        previous_voice_start_offset_seconds: Number(state.previousVoiceStartOffsetSeconds),
        voice_start_offset_seconds: Number(state.voiceStartOffsetSeconds),
        caption_audio_offset_seconds: Number(state.captionAudioOffsetSeconds),
        first_display_cue_start_seconds: Number(state.firstDisplayCueStartSeconds),
      };
    });
    if (
      initialTrimState.intro_trim_model !== INTRO_TRIM_MODEL ||
      Math.abs(initialTrimState.intro_trim_seconds - INTRO_TRIM_SECONDS) > 0.001 ||
      Math.abs(initialTrimState.previous_voice_start_offset_seconds - PREVIOUS_VOICE_START_OFFSET_SECONDS) > 0.0005 ||
      Math.abs(initialTrimState.voice_start_offset_seconds - VOICE_START_OFFSET_SECONDS) > 0.0005 ||
      Math.abs(initialTrimState.caption_audio_offset_seconds - VOICE_START_OFFSET_SECONDS) > 0.0005 ||
      initialTrimState.first_display_cue_start_seconds < VOICE_START_OFFSET_SECONDS - 0.1 ||
      initialTrimState.first_display_cue_start_seconds > VOICE_START_OFFSET_SECONDS + 0.25 ||
      freshnessGuard.intro_trim_model !== INTRO_TRIM_MODEL ||
      Math.abs(freshnessGuard.voice_start_offset_seconds - VOICE_START_OFFSET_SECONDS) > 0.0005
    ) {
      failures.push({
        time_seconds: null,
        failure: `intro trim contract is not exposed consistently; state=${JSON.stringify(initialTrimState)}, build=${JSON.stringify(freshnessGuard)}`,
      });
    }
    const tacomaRainGuard = await page.evaluate(() => {
      const state = typeof window.__railCaptionStateAt === "function" ? window.__railCaptionStateAt(20) || {} : {};
      return {
        applicable: state.tacomaRainPerformanceGuardModel === "caption_review_rain_layer_performance_guard_v1",
        model: state.tacomaRainPerformanceGuardModel || "not_applicable",
        throttle_ms: state.tacomaRainFrameThrottleMs || null,
        hook_present: typeof window.__ceTacomaRainPerformanceGuard === "function",
      };
    });
    if (manifest.episode_id === "tacoma-narrows" && (!tacomaRainGuard.applicable || !tacomaRainGuard.hook_present || Number(tacomaRainGuard.throttle_ms) < 16)) {
      failures.push({
        time_seconds: null,
        failure: "Tacoma rain performance guard is missing or inactive",
      });
    }
    await page.evaluate(async () => {
      await Promise.race([
        new Promise((resolve) => setTimeout(resolve, 4000)),
        Promise.all([
          document.fonts?.ready || Promise.resolve(),
          ...Array.from(document.images).map((image) =>
            image.complete && image.naturalWidth > 0
              ? Promise.resolve(true)
              : new Promise((resolve) => {
                  image.addEventListener("load", () => resolve(true), { once: true });
                  image.addEventListener("error", () => resolve(false), { once: true });
                }),
          ),
        ]),
      ]);
    });
    const actualDuration = await page.evaluate(() => {
      const audio = document.querySelector("audio");
      const scrubber = document.querySelector("[data-ce-scrub]");
      const audioDuration = audio && Number.isFinite(audio.duration) && audio.duration > 0 ? audio.duration : null;
      const scrubberMax = scrubber ? Number(scrubber.max || 0) : null;
      return audioDuration || scrubberMax || null;
    });
    if (Number.isFinite(actualDuration) && actualDuration > 0) {
      sampleTimes = uniqueSorted(sampleTimes.map((time) => Math.min(time, actualDuration)));
    }

    for (const time of sampleTimes) {
      await setDirectTime(page, time);
      const direct = await collectPageState(page, time, "direct_render_time");
      await setScrubTime(page, time);
      const scrub = await collectPageState(page, time, "foreground_scrubber");
      const expectedVisible = isExpectedVisible(time, firstCueStart, lastCueEnd, endScreen);
      const expectedChunk = activeChunkForTime(chunks, time);
      const sampleFailures = compareSamples({
        time,
        direct,
        scrub,
        expectedVisible,
        expectedChunk,
        firstCueStart,
        lastCueEnd,
        endScreen,
      });
      const sample = {
        time_seconds: time,
        expected_visible_caption: expectedVisible,
        direct,
        scrub,
        failures: sampleFailures,
      };
      if (sampleFailures.length) {
        const screenshotPath = path.join(
          screenshotDir,
          `${String(time.toFixed(3)).replace(".", "p")}s_${sampleFailures.length}_fail.png`,
        );
        await page.locator(".stage, #stage, .frame").first().screenshot({ path: screenshotPath }).catch(async () => {
          await page.screenshot({ path: screenshotPath, fullPage: false });
        });
        sample.failure_screenshot_path = screenshotPath;
        failures.push(...sampleFailures.map((failure) => ({ time_seconds: time, failure, screenshot_path: screenshotPath })));
      }
      samples.push(sample);
    }
    const playbackSampleTimes = uniqueSorted([
      Math.min(Math.max(firstCueStart + 4, 14), Math.max(firstCueStart, lastCueEnd - 12)),
      Math.min(firstCueStart + (lastCueEnd - firstCueStart) * 0.45, Math.max(firstCueStart, lastCueEnd - 12)),
    ]);
    const playback_sync_samples = [];
    for (const time of playbackSampleTimes) {
      await setDirectTime(page, time);
      const playbackSample = await collectPlaybackSyncState(page, time, 1800);
      playback_sync_samples.push(playbackSample);
    }
    const playbackFailures = comparePlaybackSyncSamples({
      samples: playback_sync_samples,
      chunks,
      firstCueStart,
      lastCueEnd,
      endScreen,
    });
    failures.push(...playbackFailures);
    const smoothScrollSampleTimes = uniqueSorted([
      Math.min(firstCueStart + 24, Math.max(firstCueStart, lastCueEnd - 20)),
      Math.min(firstCueStart + (lastCueEnd - firstCueStart) * 0.52, Math.max(firstCueStart, lastCueEnd - 20)),
    ]);
    const smooth_scroll_samples = [];
    for (const time of smoothScrollSampleTimes) {
      smooth_scroll_samples.push(await collectScrollSmoothnessState(page, time));
    }
    const smoothScrollFailures = compareScrollSmoothnessSamples(smooth_scroll_samples);
    failures.push(...smoothScrollFailures);
    const playbackSafeEnd = Math.max(
      firstCueStart + 35,
      Math.min(
        lastCueEnd - 8,
        Number(endScreen.safeWindowStartSeconds || endScreen.holdStartSeconds || lastCueEnd + 1) - 8,
        Number.isFinite(actualDuration) && actualDuration > 0 ? actualDuration - 8 : lastCueEnd - 8,
      ),
    );
    const playingScrubSampleTimes = uniqueSorted(
      [
        firstCueStart + (playbackSafeEnd - firstCueStart) * 0.36,
        firstCueStart + (playbackSafeEnd - firstCueStart) * 0.72,
      ].filter((time) => Number.isFinite(time) && time > firstCueStart + 20 && time < playbackSafeEnd),
    );
    const playing_scrub_samples = [];
    for (const time of playingScrubSampleTimes) {
      const playingScrubSample = await collectPlayingScrubState(page, time);
      playing_scrub_samples.push(playingScrubSample);
    }
    const playingScrubFailures = comparePlayingScrubSamples({
      samples: playing_scrub_samples,
      chunks,
    });
    failures.push(...playingScrubFailures);
    const end_screen_qa = await collectEndScreenQaState(page, endScreen);
    endScreenQaResult = end_screen_qa;
    const endScreenFailures = compareEndScreenQaState(end_screen_qa);
    failures.push(...endScreenFailures);
    adaptiveRenderAuditResult = await collectEndScreenAdaptiveRenderAudit({
      page,
      manifest,
      manifestPath,
      endScreen,
      qaDir,
    });
    const adaptiveRenderFailures = (adaptiveRenderAuditResult.artifact.failures || []).map((failure) => ({
      time_seconds: adaptiveRenderAuditResult.artifact.audit_time_seconds ?? null,
      failure,
      screenshot_path: adaptiveRenderAuditResult.artifact.screenshot_path,
    }));
    failures.push(...adaptiveRenderFailures);
    samples.push({
      proof_build_freshness_guard: freshnessGuard,
      intro_trim_contract: initialTrimState,
    });
    samples.push({
      tacoma_rain_performance_guard: tacomaRainGuard,
    });
    samples.push({
      playback_sync_qa: true,
      sample_times_seconds: playbackSampleTimes,
      samples: playback_sync_samples,
      failures: playbackFailures.map((failure) => failure.failure),
    });
    samples.push({
      smooth_scroll_qa: true,
      sample_times_seconds: smoothScrollSampleTimes,
      samples: smooth_scroll_samples,
      failures: smoothScrollFailures.map((failure) => failure.failure),
    });
    samples.push({
      playing_scrub_qa: true,
      sample_times_seconds: playingScrubSampleTimes,
      samples: playing_scrub_samples,
      failures: playingScrubFailures.map((failure) => failure.failure),
    });
    samples.push({
      end_screen_runtime_qa: true,
      ...end_screen_qa,
      failures: endScreenFailures.map((failure) => failure.failure),
    });
    samples.push({
      end_screen_adaptive_render_audit: true,
      audit_path: adaptiveRenderAuditResult.artifactPath,
      ...adaptiveRenderAuditResult.artifact,
    });
  } finally {
    await page.close();
  }

  const coverageFailures = failures.filter((failure) => /no visible captions|residual caption text/i.test(failure.failure));
  const cutoffFailures = failures.filter((failure) => /no visible captions/i.test(failure.failure));
  const scrubFailures = failures.filter((failure) => /scrub|mismatch/i.test(failure.failure));
  const clipFailures = failures.filter((failure) => /clips outside rail/i.test(failure.failure));
  const mediaTimeFailures = failures.filter((failure) => /transform drifted|audio\.currentTime/i.test(failure.failure));
  const smoothScrollFailures = failures.filter((failure) => /smooth scroll/i.test(failure.failure));
  const activeTextFailures = failures.filter((failure) => /active caption text/i.test(failure.failure));
  const freshnessFailures = failures.filter((failure) => /freshness guard|stale-tab warning/i.test(failure.failure));
  const introTrimFailures = failures.filter((failure) => /intro trim contract/i.test(failure.failure));
  const paintFailures = failures.filter((failure) => /caption stack paint box/i.test(failure.failure));
  const playingScrubFailures = failures.filter((failure) => /playing scrub/i.test(failure.failure));
  const endScreenFailures = failures.filter((failure) => /end screen/i.test(failure.failure));
  const inheritedEndScreenFailures = failures.filter((failure) => /inherited end-screen/i.test(failure.failure));
  const tacomaRainGuardFailures = failures.filter((failure) => /Tacoma rain performance guard/i.test(failure.failure));
  const adaptiveAuditReads = adaptiveRenderAuditResult?.artifact?.reads || {};
  const adaptiveRenderFailures = failures.filter((failure) => /adaptive render audit/i.test(failure.failure));
  const adaptiveComputedStyleFailures = failures.filter((failure) => /computed style/i.test(failure.failure));
  const adaptivePixelFailures = failures.filter((failure) => /pixel sampler|pixel delta/i.test(failure.failure));
  const artifactPath = path.join(qaDir, "rolling_caption_rail_runtime_coverage_qa.json");
  const artifact = {
    model: MODEL,
    created_utc: new Date().toISOString(),
    episode_id: manifest.episode_id,
    manifest_path: manifestPath,
    player_path: playerPath,
    player_url: url,
    intro_trim_model: INTRO_TRIM_MODEL,
    intro_trim_seconds: INTRO_TRIM_SECONDS,
    previous_voice_start_offset_seconds: PREVIOUS_VOICE_START_OFFSET_SECONDS,
    voice_start_offset_seconds: VOICE_START_OFFSET_SECONDS,
    first_display_cue_start_seconds: firstCueStart,
    last_caption_cue_end_seconds: lastCueEnd,
    end_screen_safe_window_start_seconds:
      endScreen.safeWindowStartSeconds || endScreen.holdStartSeconds || endScreen.transitionStartSeconds || null,
    end_screen_qa: endScreenQaResult,
    end_screen_adaptive_render_audit: adaptiveRenderAuditResult?.artifact || null,
    end_screen_adaptive_render_audit_path: adaptiveRenderAuditResult?.artifactPath || null,
    sample_times_seconds: sampleTimes,
    passed: failures.length === 0,
    failure_count: failures.length,
    failures,
    reads: {
      caption_full_vo_runtime_coverage_read: coverageFailures.length ? FAIL_COVERAGE : PASS_COVERAGE,
      caption_runtime_cutoff_read: cutoffFailures.length ? FAIL_CUTOFF : PASS_CUTOFF,
      caption_scrub_transport_sync_read: scrubFailures.length ? FAIL_SCRUB : PASS_SCRUB,
      caption_line_clip_read: clipFailures.length ? FAIL_CLIP : PASS_CLIP,
      caption_audio_time_transform_sync_read: mediaTimeFailures.length ? FAIL_MEDIA_TIME : PASS_MEDIA_TIME,
      caption_scroll_smoothness_read: smoothScrollFailures.length ? FAIL_SMOOTH_SCROLL : PASS_SMOOTH_SCROLL,
      caption_active_text_matches_audio_time_read: activeTextFailures.length ? FAIL_ACTIVE_TEXT : PASS_ACTIVE_TEXT,
      proof_build_freshness_guard_read: freshnessFailures.length ? FAIL_FRESHNESS : PASS_FRESHNESS,
      intro_trim_runtime_read: introTrimFailures.length ? FAIL_INTRO_TRIM : PASS_INTRO_TRIM,
      right_rail_caption_paint_visibility_read: paintFailures.length ? FAIL_PAINT : PASS_PAINT,
      review_transport_playing_scrub_read: playingScrubFailures.length ? FAIL_PLAYING_SCRUB : PASS_PLAYING_SCRUB,
      end_screen_runtime_qa_read: endScreenFailures.length ? FAIL_END_SCREEN : PASS_END_SCREEN,
      inherited_end_screen_suppression_read: inheritedEndScreenFailures.length
        ? FAIL_INHERITED_END_SCREEN
        : PASS_INHERITED_END_SCREEN,
      end_screen_adaptive_render_audit_read:
        adaptiveAuditReads.end_screen_adaptive_render_audit_read ||
        (adaptiveRenderFailures.length ? FAIL_ADAPTIVE_RENDER_AUDIT : PASS_ADAPTIVE_RENDER_AUDIT),
      end_screen_adaptive_computed_style_read:
        adaptiveAuditReads.end_screen_adaptive_computed_style_read ||
        (adaptiveComputedStyleFailures.length ? FAIL_ADAPTIVE_COMPUTED_STYLE : PASS_ADAPTIVE_COMPUTED_STYLE),
      end_screen_adaptive_pixel_sample_read:
        adaptiveAuditReads.end_screen_adaptive_pixel_sample_read ||
        (adaptivePixelFailures.length ? FAIL_ADAPTIVE_PIXEL_SAMPLE : PASS_ADAPTIVE_PIXEL_SAMPLE),
      tacoma_rain_performance_guard_read:
        manifest.episode_id === "tacoma-narrows"
          ? tacomaRainGuardFailures.length
            ? FAIL_TACOMA_RAIN_GUARD
            : PASS_TACOMA_RAIN_GUARD
          : "not_applicable",
    },
    samples,
  };
  writeJson(artifactPath, artifact);
  updateManifestWithRuntimeQa({ manifestPath, artifactPath, artifact });
  return artifact;
}

function setNested(target, pathParts, value) {
  let cursor = target;
  for (const part of pathParts.slice(0, -1)) {
    if (!cursor[part] || typeof cursor[part] !== "object") cursor[part] = {};
    cursor = cursor[part];
  }
  cursor[pathParts[pathParts.length - 1]] = value;
}

function updateManifestWithRuntimeQa({ manifestPath, artifactPath, artifact }) {
  const manifest = readJson(manifestPath);
  const reads = artifact.reads;
  const artifactSha = sha256File(artifactPath);
  manifest.caption_runtime_coverage_model = MODEL;
  manifest.caption_runtime_coverage_qa_path = artifactPath;
  manifest.caption_runtime_coverage_qa_sha256 = artifactSha;
  manifest.caption_runtime_coverage_sample_times_seconds = artifact.sample_times_seconds;
  manifest.caption_runtime_coverage_failure_count = artifact.failure_count;
  manifest.caption_full_vo_runtime_coverage_read = reads.caption_full_vo_runtime_coverage_read;
  manifest.caption_runtime_cutoff_read = reads.caption_runtime_cutoff_read;
  manifest.caption_scrub_transport_sync_read = reads.caption_scrub_transport_sync_read;
  manifest.caption_line_clip_read = reads.caption_line_clip_read;
  manifest.caption_audio_time_transform_sync_read = reads.caption_audio_time_transform_sync_read;
  manifest.caption_scroll_smoothness_read = reads.caption_scroll_smoothness_read;
  manifest.caption_active_text_matches_audio_time_read = reads.caption_active_text_matches_audio_time_read;
  manifest.proof_build_freshness_guard_read = reads.proof_build_freshness_guard_read;
  manifest.intro_trim_model = INTRO_TRIM_MODEL;
  manifest.intro_trim_seconds = INTRO_TRIM_SECONDS;
  manifest.previous_voice_start_offset_seconds = PREVIOUS_VOICE_START_OFFSET_SECONDS;
  manifest.voice_start_offset_seconds = VOICE_START_OFFSET_SECONDS;
  manifest.intro_trim_runtime_read = reads.intro_trim_runtime_read;
  manifest.right_rail_caption_paint_visibility_read = reads.right_rail_caption_paint_visibility_read;
  manifest.review_transport_scrub_model = "foreground_transport_scrub_lock_v1";
  manifest.review_transport_playing_scrub_read = reads.review_transport_playing_scrub_read;
  manifest.end_screen_runtime_qa_read = reads.end_screen_runtime_qa_read;
  manifest.inherited_end_screen_suppression_read = reads.inherited_end_screen_suppression_read;
  manifest.end_screen_adaptive_render_audit_model = END_SCREEN_ADAPTIVE_RENDER_AUDIT_MODEL;
  manifest.end_screen_adaptive_render_audit_path = artifact.end_screen_adaptive_render_audit_path || "";
  manifest.end_screen_adaptive_render_audit_sha256 = sha256File(artifact.end_screen_adaptive_render_audit_path || "");
  manifest.end_screen_adaptive_render_audit_read = reads.end_screen_adaptive_render_audit_read;
  manifest.end_screen_adaptive_computed_style_read = reads.end_screen_adaptive_computed_style_read;
  manifest.end_screen_adaptive_pixel_sample_read = reads.end_screen_adaptive_pixel_sample_read;
  manifest.tacoma_rain_performance_guard_read = reads.tacoma_rain_performance_guard_read;
  const endScreenQa = artifact.end_screen_qa || {};
  const endScreenReferenceSample = Array.isArray(endScreenQa.samples)
    ? endScreenQa.samples.find((sample) => sample.caption_end_screen_handoff_model) || endScreenQa.samples[0] || {}
    : {};
  manifest.caption_end_screen_handoff_model =
    endScreenReferenceSample.caption_end_screen_handoff_model || manifest.caption_end_screen_handoff_model;
  manifest.review_approved_end_screen_entry_model =
    endScreenReferenceSample.review_approved_end_screen_entry_model || CAPTION_END_SCREEN_HANDOFF_MODEL;
  manifest.review_approved_youtube_placeholder_fade_start_seconds =
    endScreenReferenceSample.review_approved_youtube_placeholder_fade_start_seconds ??
    manifest.review_approved_youtube_placeholder_fade_start_seconds;
  manifest.last_caption_visible_exit_start_seconds =
    endScreenReferenceSample.last_caption_visible_exit_start_seconds ?? manifest.last_caption_visible_exit_start_seconds;
  manifest.last_caption_fully_suppressed_seconds =
    endScreenReferenceSample.last_caption_fully_suppressed_seconds ?? manifest.last_caption_fully_suppressed_seconds;
  manifest.youtube_placeholder_fade_start_seconds =
    endScreenReferenceSample.youtube_placeholder_fade_start_seconds ?? manifest.youtube_placeholder_fade_start_seconds;
  manifest.youtube_placeholder_full_opacity_seconds =
    endScreenReferenceSample.youtube_placeholder_full_opacity_seconds ?? manifest.youtube_placeholder_full_opacity_seconds;
  manifest.caption_end_screen_gap_seconds =
    endScreenReferenceSample.caption_end_screen_gap_seconds ?? manifest.caption_end_screen_gap_seconds;
  manifest.caption_end_screen_overlap_read =
    endScreenReferenceSample.caption_end_screen_overlap_read || manifest.caption_end_screen_overlap_read;
  const nestedPaths = ["caption_context", "full_timeline", "rail_behavior.rolling_caption_window"].map((item) => item.split("."));
  for (const prefix of nestedPaths) {
    setNested(manifest, [...prefix, "caption_runtime_coverage_model"], MODEL);
    setNested(manifest, [...prefix, "caption_runtime_coverage_qa_path"], artifactPath);
    setNested(manifest, [...prefix, "caption_runtime_coverage_qa_sha256"], artifactSha);
    setNested(manifest, [...prefix, "caption_runtime_coverage_sample_times_seconds"], artifact.sample_times_seconds);
    setNested(manifest, [...prefix, "caption_runtime_coverage_failure_count"], artifact.failure_count);
    setNested(manifest, [...prefix, "caption_full_vo_runtime_coverage_read"], reads.caption_full_vo_runtime_coverage_read);
    setNested(manifest, [...prefix, "caption_runtime_cutoff_read"], reads.caption_runtime_cutoff_read);
    setNested(manifest, [...prefix, "caption_scrub_transport_sync_read"], reads.caption_scrub_transport_sync_read);
    setNested(manifest, [...prefix, "caption_line_clip_read"], reads.caption_line_clip_read);
    setNested(manifest, [...prefix, "caption_audio_time_transform_sync_read"], reads.caption_audio_time_transform_sync_read);
    setNested(manifest, [...prefix, "caption_scroll_smoothness_read"], reads.caption_scroll_smoothness_read);
    setNested(
      manifest,
      [...prefix, "caption_active_text_matches_audio_time_read"],
      reads.caption_active_text_matches_audio_time_read,
    );
    setNested(manifest, [...prefix, "proof_build_freshness_guard_read"], reads.proof_build_freshness_guard_read);
    setNested(manifest, [...prefix, "intro_trim_model"], INTRO_TRIM_MODEL);
    setNested(manifest, [...prefix, "intro_trim_seconds"], INTRO_TRIM_SECONDS);
    setNested(manifest, [...prefix, "previous_voice_start_offset_seconds"], PREVIOUS_VOICE_START_OFFSET_SECONDS);
    setNested(manifest, [...prefix, "voice_start_offset_seconds"], VOICE_START_OFFSET_SECONDS);
    setNested(manifest, [...prefix, "intro_trim_runtime_read"], reads.intro_trim_runtime_read);
    setNested(manifest, [...prefix, "right_rail_caption_paint_visibility_read"], reads.right_rail_caption_paint_visibility_read);
    setNested(manifest, [...prefix, "review_transport_scrub_model"], "foreground_transport_scrub_lock_v1");
    setNested(manifest, [...prefix, "review_transport_playing_scrub_read"], reads.review_transport_playing_scrub_read);
    setNested(manifest, [...prefix, "end_screen_runtime_qa_read"], reads.end_screen_runtime_qa_read);
    setNested(manifest, [...prefix, "inherited_end_screen_suppression_read"], reads.inherited_end_screen_suppression_read);
    setNested(manifest, [...prefix, "end_screen_adaptive_render_audit_model"], END_SCREEN_ADAPTIVE_RENDER_AUDIT_MODEL);
    setNested(manifest, [...prefix, "end_screen_adaptive_render_audit_path"], manifest.end_screen_adaptive_render_audit_path);
    setNested(manifest, [...prefix, "end_screen_adaptive_render_audit_sha256"], manifest.end_screen_adaptive_render_audit_sha256);
    setNested(manifest, [...prefix, "end_screen_adaptive_render_audit_read"], reads.end_screen_adaptive_render_audit_read);
    setNested(manifest, [...prefix, "end_screen_adaptive_computed_style_read"], reads.end_screen_adaptive_computed_style_read);
    setNested(manifest, [...prefix, "end_screen_adaptive_pixel_sample_read"], reads.end_screen_adaptive_pixel_sample_read);
    setNested(manifest, [...prefix, "tacoma_rain_performance_guard_read"], reads.tacoma_rain_performance_guard_read);
  }
  manifest.end_screen_context = manifest.end_screen_context || {};
  manifest.end_screen_context.end_screen_runtime_qa_read = reads.end_screen_runtime_qa_read;
  manifest.end_screen_context.inherited_end_screen_suppression_read = reads.inherited_end_screen_suppression_read;
  manifest.end_screen_context.end_screen_adaptive_render_audit_model = END_SCREEN_ADAPTIVE_RENDER_AUDIT_MODEL;
  manifest.end_screen_context.end_screen_adaptive_render_audit_path = manifest.end_screen_adaptive_render_audit_path;
  manifest.end_screen_context.end_screen_adaptive_render_audit_sha256 = manifest.end_screen_adaptive_render_audit_sha256;
  manifest.end_screen_context.end_screen_adaptive_render_audit_read = reads.end_screen_adaptive_render_audit_read;
  manifest.end_screen_context.end_screen_adaptive_computed_style_read = reads.end_screen_adaptive_computed_style_read;
  manifest.end_screen_context.end_screen_adaptive_pixel_sample_read = reads.end_screen_adaptive_pixel_sample_read;
  manifest.end_screen_context.caption_end_screen_handoff_model =
    manifest.caption_end_screen_handoff_model || CAPTION_END_SCREEN_HANDOFF_MODEL;
  manifest.end_screen_context.review_approved_end_screen_entry_model =
    manifest.review_approved_end_screen_entry_model || CAPTION_END_SCREEN_HANDOFF_MODEL;
  manifest.end_screen_context.review_approved_youtube_placeholder_fade_start_seconds =
    manifest.review_approved_youtube_placeholder_fade_start_seconds;
  manifest.end_screen_context.last_caption_visible_exit_start_seconds = manifest.last_caption_visible_exit_start_seconds;
  manifest.end_screen_context.last_caption_fully_suppressed_seconds = manifest.last_caption_fully_suppressed_seconds;
  manifest.end_screen_context.youtube_placeholder_fade_start_seconds = manifest.youtube_placeholder_fade_start_seconds;
  manifest.end_screen_context.youtube_placeholder_full_opacity_seconds = manifest.youtube_placeholder_full_opacity_seconds;
  manifest.end_screen_context.caption_end_screen_gap_seconds = manifest.caption_end_screen_gap_seconds;
  manifest.end_screen_context.caption_end_screen_overlap_read = manifest.caption_end_screen_overlap_read;
  manifest.qa = manifest.qa || {};
  manifest.qa.caption_runtime_coverage_model_static_pass = true;
  manifest.qa.caption_full_vo_runtime_coverage_static_pass = artifact.passed;
  manifest.qa.caption_runtime_coverage_model = MODEL;
  manifest.qa.caption_runtime_coverage_qa_path = artifactPath;
  manifest.qa.caption_runtime_coverage_qa_sha256 = artifactSha;
  Object.assign(manifest.qa, reads);
  manifest.proof_artifacts = manifest.proof_artifacts || {};
  manifest.proof_artifacts.runtime_coverage_qa_path = artifactPath;
  manifest.proof_artifacts.runtime_coverage_qa_sha256 = artifactSha;
  manifest.proof_artifacts.end_screen_adaptive_render_audit_path = manifest.end_screen_adaptive_render_audit_path;
  manifest.proof_artifacts.end_screen_adaptive_render_audit_sha256 = manifest.end_screen_adaptive_render_audit_sha256;
  if (!artifact.passed && String(manifest.human_disposition || "").toLowerCase() !== "keep") {
    manifest.status = "rolling_caption_rail_runtime_coverage_blocked";
    manifest.blocked_prerequisite =
      manifest.blocked_prerequisite || "rolling_caption_rail_runtime_coverage_browser_qa_failed";
  }
  writeJson(manifestPath, manifest);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const manifests = manifestPaths(args);
  if (!manifests.length) usage(2, "No manifests matched the requested scope");
  const { server, baseUrl } = await startServer(EPISODES_ROOT);
  const playwright = findPlaywright();
  const artifacts = [];
  try {
    for (const manifestPath of manifests) {
      const maxAttempts = args.all ? 2 : 1;
      let artifact = null;
      for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
        const browser = await playwright.chromium.launch({ headless: true });
        try {
          artifact = await qaManifest({ manifestPath, browser, baseUrl });
        } finally {
          await browser.close();
        }
        if (artifact.passed || attempt === maxAttempts) break;
        console.log(
          `RETRY runtime caption coverage: ${artifact.episode_id} (${artifact.failure_count} transient failures on attempt ${attempt})`,
        );
      }
      artifacts.push({
        episode_id: artifact.episode_id,
        passed: artifact.passed,
        failure_count: artifact.failure_count,
        qa_path: path.join(path.dirname(manifestPath), "qa/rolling_caption_rail_runtime_coverage_qa.json"),
      });
      const status = artifact.passed ? "PASS" : "FAIL";
      console.log(`${status} runtime caption coverage: ${artifact.episode_id} (${artifact.failure_count} failures)`);
    }
  } finally {
    server.close();
  }
  const passed = artifacts.every((artifact) => artifact.passed);
  if (args.json) console.log(JSON.stringify({ model: MODEL, passed, artifacts }, null, 2));
  process.exit(passed ? 0 : 1);
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
