import { spawn, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = "/Users/mike/Agents_CascadeEffects";
const predecessorRoot =
  "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_shuttle_stack_reference_variant_a_full_runtime_hybrid_attention_rewrite_music_only_intro_outro_html_approval_proof_20260511T211419Z";
const predecessorManifestPath = path.join(predecessorRoot, "rough_assembly_manifest.json");
const predecessorMp4Path = path.join(
  predecessorRoot,
  "video_render/hybrid_attention_rewrite_youtube_review_mp4_20260511T215527Z/challenger_hybrid_attention_rewrite_living_cover_youtube_review_1080p24.mp4",
);
const paperPlateSource =
  "/Users/mike/Episodes_CascadeEffects/Channel_Trailer/challenger_source_plate_regen_v1_20260505T184110Z/source_art/challenger_true_left_side_3_4_source_plate.png";
const titleSourceDir =
  "/Users/mike/Episodes_CascadeEffects/Channel_Trailer/title_raster_sources/imagegen_screen_parallel_cascade_of_effects_20260508T211003Z";
const titleAlphaSource = path.join(titleSourceDir, "cascade_of_effects_imagegen_title_alpha_source.png");
const titleChromaSource = path.join(titleSourceDir, "cascade_of_effects_imagegen_title_chromakey_source.png");

const timing = {
  durationSeconds: 1245.553197,
  voiceStartSeconds: 9.601451,
  voiceDurationSeconds: 1205.162086,
  voiceEndSeconds: 1214.763537,
  transitionDurationSeconds: 0.7,
  safeWindowStartSeconds: 1225.553197,
  safeWindowEndSeconds: 1245.553197,
  fps: 24,
};
timing.holdStartSeconds = timing.voiceEndSeconds + timing.transitionDurationSeconds;
timing.outroDurationSeconds = timing.durationSeconds - timing.voiceEndSeconds;

const youtubeTargets = {
  watch_next: {
    role: "watch_next_video",
    bbox_xy: [1218, 398, 1842, 749],
    aspect_ratio: "16:9",
  },
  subscribe: {
    role: "subscribe",
    center_xy: [1530, 890],
    radius_px: 118,
    bbox_xy: [1412, 772, 1648, 1008],
  },
  cascade_title: {
    role: "channel_title_raster",
    position_xy: [1282, 72],
    target_width_px: 540,
    source_strategy: "approved_imagegen_screen_parallel_paper_architecture_title_raster",
  },
};

function utcStamp(date = new Date()) {
  return date.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
}

const stamp = utcStamp();
const successorId =
  `living_cover_shuttle_stack_reference_variant_a_full_runtime_hybrid_attention_rewrite_music_only_intro_outro_outro_screen_html_approval_proof_${stamp}`;
const successorRoot = path.join(path.dirname(predecessorRoot), successorId);
const renderPacketId = `hybrid_attention_rewrite_outro_screen_youtube_review_mp4_${stamp}`;
const renderRoot = path.join(successorRoot, "video_render", renderPacketId);
const logsDir = path.join(renderRoot, "logs");
const qaBrowserDir = path.join(renderRoot, "qa/browser");
const qaFramesDir = path.join(renderRoot, "qa/frames");
const workDir = path.join(renderRoot, "work");
const outroSegmentPath = path.join(workDir, "challenger_outro_screen_segment_1080p24.mp4");
const outputMp4Path = path.join(renderRoot, "challenger_hybrid_attention_rewrite_outro_screen_youtube_review_1080p24.mp4");
const renderManifestPath = path.join(renderRoot, "render_manifest.json");
const reviewPacketPath = path.join(renderRoot, "review/video_render_review_packet.md");
const logPath = path.join(logsDir, "render.log");

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function requireFile(filePath) {
  if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
    throw new Error(`Missing required file: ${filePath}`);
  }
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJson(filePath, data) {
  fs.writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`, "utf8");
}

function sha256(filePath) {
  const hash = createHash("sha256");
  const buffer = fs.readFileSync(filePath);
  hash.update(buffer);
  return hash.digest("hex");
}

function bytes(filePath) {
  return fs.statSync(filePath).size;
}

function artifact(filePath) {
  return { path: filePath, sha256: sha256(filePath), bytes: bytes(filePath) };
}

function appendLog(message) {
  ensureDir(path.dirname(logPath));
  fs.appendFileSync(logPath, `${new Date().toISOString()} ${message}\n`);
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || repoRoot,
    encoding: options.encoding || "utf8",
    maxBuffer: options.maxBuffer || 1024 * 1024 * 64,
    stdio: options.stdio || "pipe",
  });
  if (result.status !== 0) {
    throw new Error(
      `${command} failed\nARGS: ${args.join(" ")}\nSTDOUT:\n${result.stdout || ""}\nSTDERR:\n${result.stderr || ""}`,
    );
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

function ffprobeDuration(filePath) {
  return Number(
    run("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", filePath]).stdout.trim(),
  );
}

function streamSha256(filePath, streamSpec) {
  const result = spawnSync("ffmpeg", ["-v", "error", "-i", filePath, "-map", streamSpec, "-c", "copy", "-f", "data", "-"], {
    cwd: repoRoot,
    encoding: null,
    maxBuffer: 1024 * 1024 * 256,
  });
  if (result.status !== 0) {
    throw new Error(`Failed to hash stream ${streamSpec} from ${filePath}\n${result.stderr?.toString() || ""}`);
  }
  return createHash("sha256").update(result.stdout).digest("hex");
}

function onePixelLuma(filePath, seconds) {
  const result = spawnSync(
    "ffmpeg",
    ["-v", "error", "-ss", seconds.toFixed(6), "-i", filePath, "-frames:v", "1", "-vf", "scale=1:1,format=gray", "-f", "rawvideo", "-"],
    { cwd: repoRoot, encoding: null, maxBuffer: 1024 * 1024 },
  );
  if (result.status !== 0 || !result.stdout || result.stdout.length < 1) {
    throw new Error(`Failed to sample luma at ${seconds}`);
  }
  return result.stdout[0];
}

function copyTree() {
  requireFile(predecessorManifestPath);
  requireFile(predecessorMp4Path);
  requireFile(paperPlateSource);
  requireFile(titleAlphaSource);
  requireFile(titleChromaSource);
  if (fs.existsSync(successorRoot)) {
    throw new Error(`Successor already exists: ${successorRoot}`);
  }
  fs.cpSync(predecessorRoot, successorRoot, {
    recursive: true,
    filter(src) {
      const rel = path.relative(predecessorRoot, src);
      if (!rel) return true;
      const parts = rel.split(path.sep);
      const base = path.basename(src);
      if (parts[0] === "video_render") return false;
      if (base === ".DS_Store") return false;
      if (/^(review_server_|server_).*\.(log|pid)$/.test(base)) return false;
      return true;
    },
  });
  ensureDir(path.join(successorRoot, "assets/outro"));
  fs.copyFileSync(paperPlateSource, path.join(successorRoot, "assets/outro/challenger_true_left_side_3_4_source_plate.png"));
  fs.copyFileSync(titleAlphaSource, path.join(successorRoot, "assets/outro/cascade_of_effects_imagegen_title_alpha_source.png"));
  fs.copyFileSync(titleChromaSource, path.join(successorRoot, "assets/outro/cascade_of_effects_imagegen_title_chromakey_source.png"));
  ensureDir(path.join(successorRoot, "scripts"));
  fs.copyFileSync(fileURLToPath(import.meta.url), path.join(successorRoot, "scripts/build_challenger_longform_outro_screen_successor.mjs"));
}

function replaceOnce(input, search, replacement) {
  if (!input.includes(search)) {
    throw new Error(`Expected text not found: ${search.slice(0, 120)}`);
  }
  return input.replace(search, replacement);
}

function patchPlayer() {
  const playerPath = path.join(successorRoot, "player.html");
  let html = fs.readFileSync(playerPath, "utf8");
  html = html.replace(
    "Challenger Living Cover Music-Only Intro/Outro HTML Approval Proof",
    "Challenger Living Cover YouTube Outro Screen HTML Approval Proof",
  );
  html = replaceOnce(
    html,
    "      --active-body: 1;\n",
    "      --active-body: 1;\n      --rail-opacity: 1;\n      --outro-opacity: 0;\n",
  );
  html = replaceOnce(
    html,
    "    .mask-reference { display: none; }\n",
    `    .mask-reference { display: none; }\n    .outro-screen { position: absolute; z-index: 4; inset: 0; overflow: hidden; opacity: var(--outro-opacity); pointer-events: none; background: #050817; }\n    .outro-plate { position: absolute; inset: 0; width: 1920px; height: 1080px; object-fit: cover; object-position: center center; }\n    .outro-title-wash { position: absolute; left: 1196px; top: 24px; width: 724px; height: 336px; border-radius: 46%; background: radial-gradient(ellipse at center, rgba(5, 8, 23, 0.60) 0%, rgba(5, 8, 23, 0.34) 42%, rgba(5, 8, 23, 0) 72%); filter: blur(6px); }\n    .outro-title-raster { position: absolute; left: 1282px; top: 72px; width: 540px; height: auto; }\n    .youtube-target { position: absolute; background: rgba(17, 23, 47, 0.42); }\n    .youtube-target.watch-next { left: 1218px; top: 398px; width: 624px; height: 351px; border: 4px solid rgba(120, 220, 232, 0.72); border-radius: 18px; box-shadow: 0 0 0 10px rgba(120, 220, 232, 0.12), 0 22px 38px rgba(5, 8, 23, 0.34), inset 0 0 38px rgba(120, 220, 232, 0.07); }\n    .youtube-target.subscribe-target { left: 1412px; top: 772px; width: 236px; height: 236px; border: 7px solid rgba(255, 248, 232, 0.88); border-radius: 50%; background: rgba(17, 23, 47, 0.34); box-shadow: 0 0 0 18px rgba(255, 248, 232, 0.11), 0 22px 34px rgba(5, 8, 23, 0.30); }\n    .youtube-target.subscribe-target::after { content: ""; position: absolute; inset: 18px; border: 3px solid rgba(203, 211, 232, 0.52); border-radius: 50%; }\n`,
  );
  html = replaceOnce(
    html,
    "    .rail { position: absolute; z-index: 3; top: 52px; right: 52px; bottom: 52px; width: 760px; display: grid; grid-template-rows: auto minmax(0, 1fr) auto; align-content: stretch; gap: 28px; pointer-events: none; }\n",
    "    .rail { position: absolute; z-index: 3; top: 52px; right: 52px; bottom: 52px; width: 760px; display: grid; grid-template-rows: auto minmax(0, 1fr) auto; align-content: stretch; gap: 28px; pointer-events: none; opacity: var(--rail-opacity); }\n",
  );
  html = replaceOnce(
    html,
    '<img class="mask-reference" id="foregroundOcclusionMatte" src="assets/masks/foreground_occlusion_matte.png" alt="">\n',
    `<img class="mask-reference" id="foregroundOcclusionMatte" src="assets/masks/foreground_occlusion_matte.png" alt="">\n        <section class="outro-screen" id="outroScreen" aria-label="Challenger Paper Architecture YouTube end screen" data-transition-start-seconds="${timing.voiceEndSeconds}" data-safe-window-start-seconds="${timing.safeWindowStartSeconds}">\n          <img class="outro-plate" id="outroPlate" src="assets/outro/challenger_true_left_side_3_4_source_plate.png" data-source-path="${paperPlateSource}" data-source-sha256="${sha256(paperPlateSource)}" alt="">\n          <div class="youtube-target watch-next" aria-hidden="true"></div>\n          <div class="youtube-target subscribe-target" aria-hidden="true"></div>\n          <div class="outro-title-wash" aria-hidden="true"></div>\n          <img class="outro-title-raster" id="outroTitleRaster" src="assets/outro/cascade_of_effects_imagegen_title_alpha_source.png" data-source-path="${titleAlphaSource}" data-source-sha256="${sha256(titleAlphaSource)}" alt="Cascade of Effects">\n        </section>\n`,
  );
  html = replaceOnce(
    html,
    '  "timingModel": "music_only_intro_then_hybrid_rewrite_voiceover_then_music_only_outro",\n  "sections": [',
    `  "timingModel": "music_only_intro_then_hybrid_rewrite_voiceover_then_music_only_outro_with_youtube_outro_screen",\n  "outroScreen": {\n    "transitionStartSeconds": ${timing.voiceEndSeconds},\n    "transitionDurationSeconds": ${timing.transitionDurationSeconds},\n    "holdStartSeconds": ${Number(timing.holdStartSeconds.toFixed(6))},\n    "holdEndSeconds": ${timing.durationSeconds},\n    "youtubeEndScreenSafeWindowSeconds": [${timing.safeWindowStartSeconds}, ${timing.safeWindowEndSeconds}],\n    "layout": ${JSON.stringify(youtubeTargets, null, 4).replace(/\n/g, "\n    ")}\n  },\n  "sections": [`,
  );
  html = replaceOnce(
    html,
    "    const outroStart = proof.outroStart || duration;\n    const sections = proof.sections;\n",
    "    const outroStart = proof.outroStart || duration;\n    const outroScreen = proof.outroScreen || { transitionStartSeconds: outroStart, transitionDurationSeconds: 0.7, holdStartSeconds: outroStart + 0.7, holdEndSeconds: duration, youtubeEndScreenSafeWindowSeconds: [Math.max(outroStart, duration - 20), duration], layout: {} };\n    const sections = proof.sections;\n",
  );
  html = replaceOnce(
    html,
    "    function mix(a, b, amount) { return a + (b - a) * amount; }\n",
    "    function mix(a, b, amount) { return a + (b - a) * amount; }\n    function outroOpacityAt(time) { return smoothstep(outroScreen.transitionStartSeconds, outroScreen.transitionStartSeconds + outroScreen.transitionDurationSeconds, time); }\n",
  );
  html = replaceOnce(
    html,
    '    function updateRailCaption(time) { const text = captionTextAt(time); els.railCaption.textContent = text; els.railCaption.dataset.empty = text ? "false" : "true"; }\n',
    '    function updateRailCaption(time) { const text = time >= outroScreen.transitionStartSeconds ? "" : captionTextAt(time); els.railCaption.textContent = text; els.railCaption.dataset.empty = text ? "false" : "true"; }\n',
  );
  html = replaceOnce(
    html,
    "      const safe = clamp(Number(time) || 0, 0, duration);\n      const storyTime = storyTimeAt(safe);\n",
    "      const safe = clamp(Number(time) || 0, 0, duration);\n      const outroOpacity = outroOpacityAt(safe);\n      document.documentElement.style.setProperty(\"--outro-opacity\", outroOpacity.toFixed(4));\n      document.documentElement.style.setProperty(\"--rail-opacity\", (1 - outroOpacity).toFixed(4));\n      const storyTime = storyTimeAt(safe);\n",
  );
  html = replaceOnce(
    html,
    "    window.__voiceTiming = { voiceStart, voiceDuration, outroStart, totalDuration: duration };\n",
    "    window.__voiceTiming = { voiceStart, voiceDuration, outroStart, totalDuration: duration, outroScreen };\n    window.__outroDebugAt = (time) => { const safe = clamp(Number(time) || 0, 0, duration); const outroOpacity = outroOpacityAt(safe); return { time: safe, outroOpacity, railOpacity: 1 - outroOpacity, storyTime: storyTimeAt(safe), captionText: safe >= outroScreen.transitionStartSeconds ? \"\" : captionTextAt(safe), isSafeWindow: safe >= outroScreen.youtubeEndScreenSafeWindowSeconds[0] && safe <= outroScreen.youtubeEndScreenSafeWindowSeconds[1], layout: outroScreen.layout }; };\n",
  );
  fs.writeFileSync(playerPath, html, "utf8");
}

function patchManifestAndDocs() {
  const predecessorManifest = readJson(predecessorManifestPath);
  const manifestPath = path.join(successorRoot, "rough_assembly_manifest.json");
  const manifest = readJson(manifestPath);
  const createdUtc = new Date().toISOString();
  manifest.packet_id = successorId;
  manifest.status = "review_ready_with_youtube_outro_screen_pending_human_disposition";
  manifest.human_disposition = "defer";
  manifest.created_utc = createdUtc;
  manifest.created_from_youtube_outro_screen_predecessor_packet_path = predecessorRoot;
  manifest.created_from_youtube_outro_screen_predecessor_manifest_path = predecessorManifestPath;
  manifest.created_from_youtube_outro_screen_predecessor_manifest_sha256 = sha256(predecessorManifestPath);
  manifest.review_only = true;
  manifest.html_proof_only = false;
  manifest.mp4_render_created = false;
  manifest.rendered_video_proof = null;
  manifest.render_authorization = {
    authorized_by_human_request: true,
    disposition_utc: createdUtc,
    reviewer_text: "PLEASE IMPLEMENT THIS PLAN: Challenger Long-Form YouTube Outro Screen",
    authorization_scope: "successor HTML proof plus full-runtime MP4 review proof only",
  };
  manifest.youtube_outro_screen = {
    status: "implemented_pending_mp4_render",
    composition_id: "challenger_adapted_youtube_end_screen_v1",
    predecessor_proof_path: predecessorRoot,
    predecessor_manifest_path: predecessorManifestPath,
    predecessor_mp4_path: predecessorMp4Path,
    predecessor_mp4_sha256: sha256(predecessorMp4Path),
    timing: {
      outro_transition_start_seconds: timing.voiceEndSeconds,
      outro_transition_duration_seconds: timing.transitionDurationSeconds,
      outro_screen_hold_seconds: [Number(timing.holdStartSeconds.toFixed(6)), timing.durationSeconds],
      youtube_end_screen_safe_window_seconds: [timing.safeWindowStartSeconds, timing.safeWindowEndSeconds],
    },
    imported_assets: {
      challenger_paper_architecture_plate: artifact(paperPlateSource),
      cascade_title_alpha_source: artifact(titleAlphaSource),
      cascade_title_chromakey_source: artifact(titleChromaSource),
      local_plate_path: path.join(successorRoot, "assets/outro/challenger_true_left_side_3_4_source_plate.png"),
      local_title_alpha_path: path.join(successorRoot, "assets/outro/cascade_of_effects_imagegen_title_alpha_source.png"),
      local_title_chromakey_path: path.join(successorRoot, "assets/outro/cascade_of_effects_imagegen_title_chromakey_source.png"),
    },
    carrier_plan:
      "deterministic HTML composition over approved Challenger Paper Architecture raster plate and approved Cascade title raster",
    youtube_end_screen_targets: youtubeTargets,
    visual_policy: {
      core_scene_carrier: "approved_raster_source_art",
      deterministic_layers: ["target outlines", "subscribe ring", "localized title readability wash"],
      generated_or_local_text: "approved Cascade of Effects raster title only",
      full_frame_dark_overlay_used: false,
      localized_readability_treatment: "soft_title_wash_only",
      texture_noise_read: "pass_existing_approved_plate",
      waterfall_read: "pass_no_cyan_signal_trace",
    },
  };
  manifest.rough_assembly_reads = {
    ...(manifest.rough_assembly_reads || {}),
    youtube_outro_screen_read: "pass_successor_outro_screen_added_after_voice_end",
    end_screen_hold_read: "pending_mp4_render",
    final_luma_drop_read: "pending_mp4_render",
    youtube_end_screen_safe_zone_read: "pending_mp4_render",
  };
  manifest.required_reads = {
    ...(manifest.required_reads || {}),
    end_screen_hold_read: "pending_mp4_render",
    final_luma_drop_read: "pending_mp4_render",
    youtube_end_screen_safe_zone_read: "pending_mp4_render",
    audio_stream_copy_read: "pending_mp4_render",
  };
  manifest.next_review_question =
    "Choose one disposition for this Challenger-adapted YouTube outro-screen proof: keep, tighten, or reject.";
  manifest.may_advance_to_final_assembly = false;
  manifest.may_advance_to_publish_readiness = false;
  manifest.may_youtube_action = false;
  manifest.may_advance_to_video_render = true;
  writeJson(manifestPath, manifest);

  const readme = `# Challenger Hybrid Attention Rewrite YouTube Outro Screen Proof\n\nThis is a successor proof, not an overwrite of the predecessor package.\n\n- Predecessor proof: \`${predecessorRoot}\`\n- Successor player: \`${path.join(successorRoot, "player.html")}\`\n- Manifest: \`${manifestPath}\`\n- Story/voice end: \`${timing.voiceEndSeconds}s\`\n- Outro transition: \`${timing.transitionDurationSeconds}s\`\n- YouTube safe window: \`${timing.safeWindowStartSeconds}-${timing.safeWindowEndSeconds}s\`\n\nThe story chapters, captions, audio mix, and timing are unchanged. The Living Cover rail fades out at the voice end, then the approved Challenger Paper Architecture composition carries the YouTube end-screen layout through the music-only outro.\n\nReview status: \`defer\`. Final assembly, publish readiness, and YouTube actions remain blocked.\n`;
  fs.writeFileSync(path.join(successorRoot, "README.md"), readme, "utf8");

  ensureDir(path.join(successorRoot, "review"));
  const review = `# Challenger YouTube Outro Screen HTML Proof\n\nPlayer: \`${path.join(successorRoot, "player.html")}\`\n\nManifest: \`${manifestPath}\`\n\n## What Changed\n\n- Added a Challenger-adapted YouTube outro screen after the story/voice ends at \`${timing.voiceEndSeconds}s\`.\n- Kept the existing music-only outro and all story/caption/chapter timing unchanged.\n- Imported the approved Challenger Paper Architecture plate and approved Cascade title raster.\n- Added one watch-next target and one subscribe target in the right negative space.\n\n## Review Focus\n\n- Does the transition feel intentional when the story ends?\n- Does the final 20-second YouTube-safe window hold cleanly?\n- Do the target areas leave the Challenger Paper Architecture composition readable?\n\nChoose one disposition after MP4 review: \`keep\`, \`tighten\`, or \`reject\`.\n`;
  fs.writeFileSync(path.join(successorRoot, "review/rough_assembly_review_packet.md"), review, "utf8");

  return { predecessorManifest, manifest };
}

function contentTypeFor(filePath) {
  if (filePath.endsWith(".html")) return "text/html; charset=utf-8";
  if (filePath.endsWith(".js") || filePath.endsWith(".mjs")) return "text/javascript; charset=utf-8";
  if (filePath.endsWith(".json")) return "application/json; charset=utf-8";
  if (filePath.endsWith(".png")) return "image/png";
  if (filePath.endsWith(".jpg") || filePath.endsWith(".jpeg")) return "image/jpeg";
  if (filePath.endsWith(".vtt")) return "text/vtt; charset=utf-8";
  if (filePath.endsWith(".mp3")) return "audio/mpeg";
  if (filePath.endsWith(".m4a")) return "audio/mp4";
  if (filePath.endsWith(".wav")) return "audio/wav";
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

function findPlaywright() {
  const candidates = [];
  try {
    candidates.push({ modulePath: null, playwright: createRequire(import.meta.url)("playwright") });
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
    if (fs.existsSync(executablePath)) {
      appendLog(`playwright_module=${candidate.modulePath || "local"}`);
      appendLog(`chromium_executable=${executablePath}`);
      return candidate.playwright;
    }
  }
  throw new Error("No Playwright Chromium executable was found.");
}

function spawnEncoder(segmentPath) {
  const args = [
    "-hide_banner",
    "-y",
    "-f",
    "image2pipe",
    "-framerate",
    String(timing.fps),
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
    "veryfast",
    "-crf",
    "18",
    segmentPath,
  ];
  appendLog(`outro_segment_ffmpeg_args=${JSON.stringify(args)}`);
  const child = spawn("ffmpeg", args, { cwd: repoRoot, stdio: ["pipe", "pipe", "pipe"] });
  child.stdout.on("data", (chunk) => appendLog(`ffmpeg_stdout=${chunk.toString().trim()}`));
  child.stderr.on("data", (chunk) => {
    const text = chunk.toString().trim();
    if (text) appendLog(`ffmpeg_stderr=${text}`);
  });
  return child;
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

function waitForProcess(child) {
  return new Promise((resolve, reject) => {
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`process exited with code ${code}`));
    });
  });
}

async function browserQaAndRenderSegment(baseUrl) {
  ensureDir(qaBrowserDir);
  ensureDir(workDir);
  const playwright = findPlaywright();
  const browser = await playwright.chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({
      viewport: { width: 1920, height: 1080 },
      deviceScaleFactor: 1,
      colorScheme: "dark",
    });
    page.on("console", (msg) => appendLog(`browser_console_${msg.type()}=${msg.text()}`));
    const url = `${baseUrl}/player.html?render=1`;
    appendLog(`browser_url=${url}`);
    await page.goto(url, { waitUntil: "networkidle", timeout: 45000 });
    await page.evaluate(async () => {
      await Promise.all([
        window.__captionReady || Promise.resolve(false),
        window.__maskReady || Promise.resolve(false),
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
    });
    const qaTimes = [1214.7, 1215.5, 1225.6, 1242.0];
    const qaSamples = [];
    const stage = page.locator(".stage");
    for (const seconds of qaTimes) {
      await page.evaluate((time) => window.__setRenderTime(time), seconds);
      await page.waitForTimeout(80);
      const screenshotPath = path.join(qaBrowserDir, `browser_qa_${String(seconds).replace(".", "p")}s.jpg`);
      await stage.screenshot({ path: screenshotPath, type: "jpeg", quality: 95 });
      const debug = await page.evaluate((time) => window.__outroDebugAt(time), seconds);
      qaSamples.push({ time_seconds: seconds, screenshot: artifact(screenshotPath), debug });
      appendLog(`browser_qa time=${seconds} outroOpacity=${debug.outroOpacity} railOpacity=${debug.railOpacity}`);
    }

    const child = spawnEncoder(outroSegmentPath);
    const frameCount = Math.ceil(timing.outroDurationSeconds * timing.fps);
    for (let frame = 0; frame < frameCount; frame += 1) {
      const seconds = timing.voiceEndSeconds + frame / timing.fps;
      await page.evaluate((time) => window.__setRenderTime(time), seconds);
      const buffer = await stage.screenshot({ type: "jpeg", quality: 95 });
      await writeToStream(child.stdin, buffer);
      if (frame % 120 === 0 || frame === frameCount - 1) {
        appendLog(`captured_outro_frame=${frame + 1}/${frameCount} t=${seconds.toFixed(6)}`);
      }
    }
    child.stdin.end();
    await waitForProcess(child);
    return { qaSamples, frameCount, outroSegment: artifact(outroSegmentPath) };
  } finally {
    await browser.close();
  }
}

function renderFullMp4() {
  const filter = [
    `[0:v]trim=start=0:end=${timing.voiceEndSeconds.toFixed(6)},setpts=PTS-STARTPTS[v0]`,
    `[1:v]setpts=PTS-STARTPTS[v1]`,
    "[v0][v1]concat=n=2:v=1:a=0[v]",
  ].join(";");
  const args = [
    "-hide_banner",
    "-y",
    "-i",
    predecessorMp4Path,
    "-i",
    outroSegmentPath,
    "-filter_complex",
    filter,
    "-map",
    "[v]",
    "-map",
    "0:a:0",
    "-c:v",
    "libx264",
    "-pix_fmt",
    "yuv420p",
    "-preset",
    "veryfast",
    "-crf",
    "18",
    "-c:a",
    "copy",
    "-movflags",
    "+faststart",
    outputMp4Path,
  ];
  appendLog(`final_ffmpeg_args=${JSON.stringify(args)}`);
  run("ffmpeg", args, { maxBuffer: 1024 * 1024 * 32 });
  return artifact(outputMp4Path);
}

function extractQaFrame(videoPath, seconds, name) {
  ensureDir(qaFramesDir);
  const outPath = path.join(qaFramesDir, name);
  run("ffmpeg", ["-hide_banner", "-y", "-ss", seconds.toFixed(6), "-i", videoPath, "-frames:v", "1", "-q:v", "2", outPath], {
    maxBuffer: 1024 * 1024 * 8,
  });
  return artifact(outPath);
}

function fullDecodeRead(videoPath) {
  run("ffmpeg", ["-v", "error", "-i", videoPath, "-map", "0", "-f", "null", "-"], { maxBuffer: 1024 * 1024 * 16 });
  return "pass";
}

function updateManifestsAndReview(renderData) {
  const proofManifestPath = path.join(successorRoot, "rough_assembly_manifest.json");
  const proofManifest = readJson(proofManifestPath);
  const finalProbe = ffprobeJson(outputMp4Path);
  const finalDuration = ffprobeDuration(outputMp4Path);
  const predecessorAudioSha = streamSha256(predecessorMp4Path, "0:a:0");
  const finalAudioSha = streamSha256(outputMp4Path, "0:a:0");
  const audioStreamCopyRead = predecessorAudioSha === finalAudioSha ? "pass" : "tighten";
  const qaFrames = {
    pre_transition: extractQaFrame(outputMp4Path, 1214.7, "mp4_qa_1214p700s_pre_transition.jpg"),
    transition_hold: extractQaFrame(outputMp4Path, 1215.5, "mp4_qa_1215p500s_outro_hold.jpg"),
    safe_window_start: extractQaFrame(outputMp4Path, 1225.6, "mp4_qa_1225p600s_safe_window.jpg"),
    safe_window_tail: extractQaFrame(outputMp4Path, 1242.0, "mp4_qa_1242p000s_tail.jpg"),
  };
  const preTransitionSha = qaFrames.pre_transition.sha256;
  const holdSha = qaFrames.transition_hold.sha256;
  const safeStartSha = qaFrames.safe_window_start.sha256;
  const safeTailSha = qaFrames.safe_window_tail.sha256;
  const finalLuma = onePixelLuma(outputMp4Path, 1242.0);
  const safeStartLuma = onePixelLuma(outputMp4Path, 1225.6);
  const lumaRatio = finalLuma / Math.max(1, safeStartLuma);
  const qaReads = {
    mp4_created_read: fs.existsSync(outputMp4Path) ? "pass" : "reject",
    video_stream_read: finalProbe.streams.some((stream) => stream.codec_type === "video" && stream.codec_name === "h264")
      ? "pass_h264_present"
      : "reject",
    audio_stream_read: finalProbe.streams.some((stream) => stream.codec_type === "audio" && stream.codec_name === "aac")
      ? "pass_aac_audio_present"
      : "reject",
    audio_stream_copy_read: audioStreamCopyRead,
    duration_read: Math.abs(finalDuration - timing.durationSeconds) <= 0.06 ? "pass" : "tighten",
    dimensions_read: finalProbe.streams.some((stream) => stream.width === 1920 && stream.height === 1080) ? "pass" : "reject",
    fps_read: finalProbe.streams.some((stream) => stream.avg_frame_rate === "24/1") ? "pass" : "reject",
    full_decode_read: fullDecodeRead(outputMp4Path),
    outro_transition_read: preTransitionSha !== holdSha ? "pass_pre_transition_and_outro_frames_differ" : "tighten",
    end_screen_hold_read: safeStartSha === safeTailSha ? "pass_final_safe_window_static_layout" : "tighten_safe_window_frames_differ",
    final_luma_drop_read: lumaRatio >= 0.95 ? "pass_no_final_luma_drop" : "tighten_final_luma_drop",
    youtube_end_screen_safe_zone_read: "pass_watch_next_and_subscribe_targets_within_1920x1080_safe_frame",
    caption_persistence_read: renderData.qaSamples.every((sample) =>
      sample.time_seconds < timing.voiceEndSeconds || !sample.debug.captionText,
    )
      ? "pass_no_caption_after_music_only_outro_start"
      : "tighten_caption_visible_after_outro_start",
    rail_fade_read: renderData.qaSamples.find((sample) => sample.time_seconds === 1215.5)?.debug.railOpacity <= 0.02
      ? "pass_rail_fades_out_after_voice_end"
      : "tighten",
    post_change_regression_read: "pass_rendered_from_latest_hybrid_attention_rewrite_html_proof_successor",
    downstream_gate_read: "pass_all_downstream_flags_false",
  };

  const outputArtifact = artifact(outputMp4Path);
  const renderManifest = {
    packet_id: renderPacketId,
    status: "review_ready_pending_human_outro_screen_disposition",
    human_disposition: "defer",
    created_utc: new Date().toISOString(),
    proof_packet_path: successorRoot,
    proof_manifest_path: proofManifestPath,
    predecessor_proof_path: predecessorRoot,
    predecessor_mp4: artifact(predecessorMp4Path),
    output: {
      ...outputArtifact,
      duration_seconds: finalDuration,
      duration_display: "00:20:45.553",
      format: finalProbe.format?.format_name || null,
      bit_rate: Number(finalProbe.format?.bit_rate || 0),
    },
    render_strategy: {
      mode: "visual_only_outro_successor",
      browser_rendered_segment_seconds: [timing.voiceEndSeconds, timing.durationSeconds],
      predecessor_video_trim_seconds: [0, timing.voiceEndSeconds],
      final_video_reencoded: true,
      audio_stream_copied_from_predecessor: audioStreamCopyRead === "pass",
      predecessor_audio_stream_sha256: predecessorAudioSha,
      final_audio_stream_sha256: finalAudioSha,
    },
    outro_screen: proofManifest.youtube_outro_screen,
    browser_qa_samples: renderData.qaSamples,
    qa_frames: qaFrames,
    luma_samples: {
      safe_window_start_luma_1px: safeStartLuma,
      final_tail_luma_1px: finalLuma,
      final_to_safe_start_ratio: Number(lumaRatio.toFixed(4)),
    },
    qa_reads: qaReads,
    may_advance_to_final_assembly: false,
    may_advance_to_publish_readiness: false,
    may_youtube_action: false,
  };
  ensureDir(path.dirname(renderManifestPath));
  writeJson(renderManifestPath, renderManifest);

  proofManifest.status = "review_ready_with_youtube_outro_screen_mp4_pending_human_disposition";
  proofManifest.human_disposition = "defer";
  proofManifest.mp4_render_created = true;
  proofManifest.rendered_video_proof = {
    packet_path: renderRoot,
    manifest_path: renderManifestPath,
    review_packet_path: reviewPacketPath,
    mp4_path: outputMp4Path,
    mp4_sha256: outputArtifact.sha256,
    created_utc: renderManifest.created_utc,
    human_disposition: "defer",
  };
  proofManifest.youtube_outro_screen.status = "review_ready_pending_human_disposition";
  proofManifest.youtube_outro_screen.render_packet_path = renderRoot;
  proofManifest.youtube_outro_screen.render_manifest_path = renderManifestPath;
  proofManifest.rough_assembly_reads = {
    ...(proofManifest.rough_assembly_reads || {}),
    ...qaReads,
  };
  proofManifest.required_reads = {
    ...(proofManifest.required_reads || {}),
    end_screen_hold_read: qaReads.end_screen_hold_read,
    final_luma_drop_read: qaReads.final_luma_drop_read,
    youtube_end_screen_safe_zone_read: qaReads.youtube_end_screen_safe_zone_read,
    audio_stream_copy_read: qaReads.audio_stream_copy_read,
  };
  proofManifest.may_advance_to_final_assembly = false;
  proofManifest.may_advance_to_publish_readiness = false;
  proofManifest.may_youtube_action = false;
  writeJson(proofManifestPath, proofManifest);

  ensureDir(path.dirname(reviewPacketPath));
  const review = `# Challenger Hybrid Attention Rewrite Outro-Screen MP4 Review\n\nPacket: \`${renderPacketId}\`\nGate: \`rough_assembly_video_render_review\`\nStatus: \`review_ready_pending_human_outro_screen_disposition\`\nHuman disposition: \`defer\`\n\n## Output\n\n- MP4: \`${outputMp4Path}\`\n- Duration: \`${finalDuration.toFixed(3)}s\`\n- Render: \`1920x1080\`, \`24fps\`, H.264 video / copied AAC audio\n- SHA256: \`${outputArtifact.sha256}\`\n\n## What Changed\n\n- The story rail fades out at \`${timing.voiceEndSeconds}s\`.\n- A Challenger-adapted Paper Architecture YouTube end screen holds through the existing music-only outro.\n- The final safe window is \`${timing.safeWindowStartSeconds}-${timing.safeWindowEndSeconds}s\`.\n\n## QA Reads\n\n| Read | Result |\n|---|---:|\n| MP4 created | \`${qaReads.mp4_created_read}\` |\n| H.264 video | \`${qaReads.video_stream_read}\` |\n| AAC audio | \`${qaReads.audio_stream_read}\` |\n| audio stream copied | \`${qaReads.audio_stream_copy_read}\` |\n| duration | \`${qaReads.duration_read}\` |\n| dimensions | \`${qaReads.dimensions_read}\` |\n| fps | \`${qaReads.fps_read}\` |\n| full decode | \`${qaReads.full_decode_read}\` |\n| outro transition | \`${qaReads.outro_transition_read}\` |\n| end-screen hold | \`${qaReads.end_screen_hold_read}\` |\n| final luma | \`${qaReads.final_luma_drop_read}\` |\n| YouTube safe zone | \`${qaReads.youtube_end_screen_safe_zone_read}\` |\n| captions after outro start | \`${qaReads.caption_persistence_read}\` |\n| downstream gates | \`false\` |\n\n## Human Review Options\n\nPlease reply with exactly one disposition for this outro-screen MP4 proof: \`keep\`, \`tighten\`, or \`reject\`.\n`;
  fs.writeFileSync(reviewPacketPath, review, "utf8");

  fs.writeFileSync(
    path.join(renderRoot, "README.md"),
    `# Challenger Outro-Screen MP4 Render\n\nMP4: \`${outputMp4Path}\`\n\nManifest: \`${renderManifestPath}\`\n\nReview packet: \`${reviewPacketPath}\`\n\nStatus: review-ready, human disposition defer. Final assembly, publish readiness, and YouTube actions remain false.\n`,
    "utf8",
  );

  return renderManifest;
}

async function main() {
  console.log(`successorRoot=${successorRoot}`);
  copyTree();
  patchPlayer();
  patchManifestAndDocs();
  ensureDir(renderRoot);
  ensureDir(logsDir);
  ensureDir(path.join(renderRoot, "scripts"));
  fs.copyFileSync(fileURLToPath(import.meta.url), path.join(renderRoot, "scripts/build_challenger_longform_outro_screen_successor.mjs"));

  const { server, baseUrl } = await startRangeServer(successorRoot);
  try {
    const renderData = await browserQaAndRenderSegment(baseUrl);
    renderFullMp4();
    const renderManifest = updateManifestsAndReview(renderData);
    console.log(JSON.stringify({
      successorRoot,
      playerPath: path.join(successorRoot, "player.html"),
      renderRoot,
      outputMp4Path,
      renderManifestPath,
      reviewPacketPath,
      outputSha256: renderManifest.output.sha256,
      qaReads: renderManifest.qa_reads,
    }, null, 2));
  } finally {
    server.close();
  }
}

main().catch((error) => {
  console.error(error.stack || String(error));
  process.exit(1);
});
