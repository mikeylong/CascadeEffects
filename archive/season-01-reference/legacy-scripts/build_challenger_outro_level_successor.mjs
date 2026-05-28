#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const REPO_ROOT = "/Users/mike/Agents_CascadeEffects";
const LEGAL_PROOF_ROOT =
  "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_end_screen_legal_window_trial_20260525T192946Z";
const SOURCE_MIX =
  "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_rolling_caption_rail_rough_proof_20260523T182309Z/proof_assets/audio/challenger_right_rail_alignment_music_mix.wav";
const SOURCE_MIX_MANIFEST =
  "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_rolling_caption_rail_rough_proof_20260523T182309Z/proof_assets/audio/challenger_right_rail_alignment_music_mix_manifest.json";
const CURRENT_PUBLISH_MANIFEST =
  "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/publish_readiness/challenger_publish_readiness_20260525T195438Z/publish_readiness_manifest.json";
const EXPECTED_SOURCE_MIX_SHA256 = "9f771c0e45e8e965c30640c5eba50a9126126c5d39160b19639c45b6a86d5e82";
const VOICE_END_SECONDS = 1182.385669;
const OUTRO_TARGET_SECONDS = 1185.385669;
const LEGAL_ENTRY_SECONDS = 1191.680884;
const FULL_OPACITY_SECONDS = 1191.980884;
const REVIEW_START_SECONDS = 1179.5;
const DEFAULT_GAIN_DB = 5.0;

function parseArgs(argv) {
  const args = { gainDb: DEFAULT_GAIN_DB, stamp: stamp() };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = () => {
      i += 1;
      if (i >= argv.length) throw new Error(`Missing value for ${arg}`);
      return argv[i];
    };
    if (arg === "--gain-db") args.gainDb = Number(next());
    else if (arg === "--stamp") args.stamp = next();
    else if (arg === "--help" || arg === "-h") {
      console.log("Usage: node scripts/build_challenger_outro_level_successor.mjs [--gain-db 5]");
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  if (!Number.isFinite(args.gainDb) || args.gainDb <= 0 || args.gainDb > 9) {
    throw new Error(`Invalid --gain-db ${args.gainDb}; expected >0 and <=9`);
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
      "format=duration,size,bit_rate,format_name:stream=index,codec_name,codec_type,sample_rate,channels,bits_per_sample,duration",
      "-of",
      "json",
      filePath,
    ]).stdout,
  );
}

function parseLoudnorm(output) {
  const match = output.match(/\{[\s\S]*?"target_offset"\s*:\s*"[^"]+"\s*\}/);
  if (!match) return null;
  return JSON.parse(match[0]);
}

function loudnorm(filePath, startSeconds, durationSeconds) {
  const result = run("ffmpeg", [
    "-hide_banner",
    "-nostats",
    "-ss",
    String(startSeconds),
    "-t",
    String(durationSeconds),
    "-i",
    filePath,
    "-af",
    "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
    "-f",
    "null",
    "-",
  ]);
  const parsed = parseLoudnorm(`${result.stdout || ""}${result.stderr || ""}`);
  return parsed
    ? {
        input_i_lufs: Number(parsed.input_i),
        input_tp_dbtp: Number(parsed.input_tp),
        input_lra: Number(parsed.input_lra),
        input_thresh: Number(parsed.input_thresh),
      }
    : {};
}

function volumedetect(filePath, startSeconds, durationSeconds) {
  const result = run("ffmpeg", [
    "-hide_banner",
    "-nostats",
    "-ss",
    String(startSeconds),
    "-t",
    String(durationSeconds),
    "-i",
    filePath,
    "-af",
    "volumedetect",
    "-f",
    "null",
    "-",
  ]);
  const output = `${result.stdout || ""}${result.stderr || ""}`;
  const mean = output.match(/mean_volume:\s*(-?[0-9.]+)\s*dB/);
  const max = output.match(/max_volume:\s*(-?[0-9.]+)\s*dB/);
  return {
    mean_volume_db: mean ? Number(mean[1]) : null,
    max_volume_db: max ? Number(max[1]) : null,
  };
}

function measureWindows(filePath) {
  const windows = [
    ["intro_music_only", 0.3, 3.0],
    ["opening_vo_after_intro_tail", 6.0, 12.0],
    ["mid_vo", 600.0, 12.0],
    ["final_vo_prelap", 1179.5, 2.886],
    ["post_vo_outro_ramp", VOICE_END_SECONDS, OUTRO_TARGET_SECONDS - VOICE_END_SECONDS],
    ["target_outro_pre_legal", OUTRO_TARGET_SECONDS, LEGAL_ENTRY_SECONDS - OUTRO_TARGET_SECONDS],
    ["legal_window_outro", LEGAL_ENTRY_SECONDS, 10.0],
    ["final_outro_tail", 1203.0, 8.0],
  ];
  return Object.fromEntries(
    windows.map(([name, start, duration]) => [
      name,
      {
        start_seconds: start,
        duration_seconds: Number(duration.toFixed(6)),
        ...loudnorm(filePath, start, duration),
        ...volumedetect(filePath, start, duration),
      },
    ]),
  );
}

function createOutMix({ sourcePath, outputPath, gainDb }) {
  const gainLinear = Math.pow(10, gainDb / 20);
  const rampSeconds = OUTRO_TARGET_SECONDS - VOICE_END_SECONDS;
  const gainExpression = `if(lt(t,${VOICE_END_SECONDS}),1,if(lt(t,${OUTRO_TARGET_SECONDS}),1+(${gainLinear}-1)*(t-${VOICE_END_SECONDS})/${rampSeconds},${gainLinear}))`;
  run("ffmpeg", [
    "-y",
    "-i",
    sourcePath,
    "-af",
    `volume='${gainExpression}':eval=frame`,
    "-c:a",
    "pcm_s16le",
    outputPath,
  ]);
  return { gainLinear, rampSeconds, gainExpression };
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

function linkDir(sourcePath, targetPath) {
  fs.rmSync(targetPath, { recursive: true, force: true });
  fs.symlinkSync(sourcePath, targetPath);
}

function patchDefaultStart(html) {
  return html.replace(
    "const CE_URL_FORCED_TIME = Number(CE_PARAMS.get(\"t\"));",
    `const CE_URL_FORCED_TIME = Number(CE_PARAMS.get("t") ?? "${REVIEW_START_SECONDS.toFixed(3)}");`,
  );
}

function patchPlayerHtml({ sourceHtml, audioSrc, proofBuildId, createdUtc, proofBuildJsonPath, successor }) {
  let html = sourceHtml;
  if (audioSrc) {
    html = html.replace(/(<audio\s+src=")[^"]+(" class="review-audio")/, `$1${audioSrc}$2`);
  }
  html = html.replace(/<title>[\s\S]*?<\/title>/, "<title>Challenger Outro Level Successor Review</title>");
  html = html.replace(/(proofBuildId: )"[^"]*"(,)/, `$1${JSON.stringify(proofBuildId)}$2`);
  html = html.replace(/(proofGeneratedAtUtc: )"[^"]*"(,)/, `$1${JSON.stringify(createdUtc)}$2`);
  html = html.replace(/(proofBuildJsonPath: )"[^"]*"(,)/, `$1${JSON.stringify(proofBuildJsonPath)}$2`);
  html = patchDefaultStart(html);
  html = html.replace(
    "</body>",
    `<script id="ce-outro-level-successor" type="application/json">${JSON.stringify(successor)}</script>\n</body>`,
  );
  return html;
}

function writeProofBuild({ sourceProofBuildPath, outputPath, proofBuildId, outputRoot, manifestPath, playerPath, createdUtc, successor }) {
  const proofBuild = readJson(sourceProofBuildPath);
  Object.assign(proofBuild, {
    proof_build_id: proofBuildId,
    proof_generated_at_utc: createdUtc,
    packet_stamp: path.basename(outputRoot),
    player_path: playerPath,
    manifest_path: manifestPath,
    outro_level_successor: successor,
  });
  writeJson(outputPath, proofBuild);
}

function patchManifest({
  outputRoot,
  outputAudioPath,
  outputAudioProbe,
  outputAudioSha,
  sourceMixSha,
  sourceMixManifestSha,
  qaPath,
  reviewPath,
  proofBuildId,
  proofBuildPath,
  createdUtc,
  gainDb,
  gainLinear,
}) {
  const manifestPath = path.join(LEGAL_PROOF_ROOT, "rough_assembly_manifest.json");
  const manifest = readJson(manifestPath);
  const successor = {
    model: "challenger_outro_post_vo_level_successor_v1",
    created_utc: createdUtc,
    source_manifest_path: manifestPath,
    source_audio_path: SOURCE_MIX,
    source_audio_sha256: sourceMixSha,
    source_audio_manifest_path: SOURCE_MIX_MANIFEST,
    source_audio_manifest_sha256: sourceMixManifestSha,
    output_audio_path: outputAudioPath,
    output_audio_sha256: outputAudioSha,
    gain_db_after_voice: gainDb,
    gain_linear_after_voice: Number(gainLinear.toFixed(6)),
    gain_ramp_start_seconds: VOICE_END_SECONDS,
    gain_ramp_full_seconds: OUTRO_TARGET_SECONDS,
    unchanged_timing_read: "pass_visual_end_screen_timing_preserved_youtube_legal_window_entry",
    under_vo_overlap_read: "pass_no_gain_increase_before_voice_end",
    source_mix_hash_preservation_read: sourceMixSha === EXPECTED_SOURCE_MIX_SHA256 ? "pass_predecessor_mix_hash_recorded" : "fail_unexpected_predecessor_mix_hash",
    youtube_action_read: "blocked_pending_human_keep_and_explicit_upload_authorization",
  };
  const patched = {
    ...manifest,
    packet_id: path.basename(outputRoot),
    production_contract: {
      ...(manifest.production_contract || {}),
      contract_id: "first-eight-longform-v1",
      intent: "successor",
      allowed_delta: {
        model: "audio_only_post_vo_outro_level_delta_v1",
        audio_change_start_seconds: VOICE_END_SECONDS,
        audio_full_gain_seconds: OUTRO_TARGET_SECONDS,
        visual_timing_unchanged_read: "pass",
        youtube_action_allowed: false,
      },
      youtube_action_approval_read: "blocked_pending_human_keep_and_explicit_upload_authorization",
    },
    status: "challenger_outro_level_successor_review_ready_pending_human_keep",
    human_disposition: "pending",
    human_disposition_source: "pending_challenger_outro_level_html_review",
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
    proof_build_json_sha256: "pending",
    approved_audio: {
      ...(manifest.approved_audio || {}),
      path: outputAudioPath,
      sha256: outputAudioSha,
      duration_seconds: Number(outputAudioProbe.format?.duration || manifest.approved_audio?.duration_seconds),
      role: "right_rail_alignment_contract_timed_intro_voice_outro_review_mix_outro_level_successor",
      review_audio_mix_model: "challenger_outro_post_vo_level_successor_v1",
      review_audio_mix_manifest_path: path.join(outputRoot, "audio_successor", "challenger_outro_post_vo_level_successor_manifest.json"),
      media_copied_or_modified: true,
    },
    audio_level_successor: successor,
    rough_assembly_reads: {
      ...(manifest.rough_assembly_reads || {}),
      outro_entry_level_match_read: "pass_successor_outro_lifted_to_intro_music_loudness_window",
      outro_transition_review_sample_read: "pass_html_ab_review_created_current_vs_plus5db_successor",
      vo_outro_perceptual_review_read: "pending_human_listen",
      final_mix_approval_read: "blocked_pending_human_keep_on_audio_level_successor",
    },
    reads: {
      ...(manifest.reads || {}),
      outro_entry_level_match_read: "pass_successor_outro_lifted_to_intro_music_loudness_window",
      outro_transition_review_sample_read: "pass_html_ab_review_created_current_vs_plus5db_successor",
      vo_outro_perceptual_review_read: "pending_human_listen",
      youtube_action_read: "blocked_pending_human_keep_and_explicit_upload_authorization",
    },
    proof_artifacts: {
      ...(manifest.proof_artifacts || {}),
      player_html_path: path.join(outputRoot, "player.html"),
      proof_build_json_path: proofBuildPath,
      proof_build_json_sha256: "pending",
      audio_level_qa_path: qaPath,
      review_packet_path: reviewPath,
    },
  };
  return patched;
}

function reviewIndex({ reviewIndexPath, currentPlayer, successorPlayer, qaPath, gainDb }) {
  const relCurrent = path.relative(path.dirname(reviewIndexPath), currentPlayer).split(path.sep).join("/");
  const relSuccessor = path.relative(path.dirname(reviewIndexPath), successorPlayer).split(path.sep).join("/");
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Challenger Outro Level HTML Review</title>
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
    <h1>Challenger Outro Level HTML Review</h1>
    <p>Both versions keep the new legal-window end-screen timing. They start at <code>${REVIEW_START_SECONDS.toFixed(3)}s</code> so you can hear the final VO, the old visual-entry moment, the outro target point, and the legal end-screen entry without rendering a new MP4.</p>
    <div class="links">
      <a class="review-link" href="${relCurrent}">
        <strong>Current YouTube audio level</strong>
        <span>The audio used for the unlisted YouTube review. Outro target remains at the prior level.</span>
      </a>
      <a class="review-link" href="${relSuccessor}">
        <strong>Successor: post-VO outro +${gainDb.toFixed(1)} dB</strong>
        <span>The final VO overlap is unchanged; the outro gain ramps up after VO end and reaches full lift at the existing target point.</span>
      </a>
    </div>
    <dl>
      <dt>VO end</dt><dd><code>${VOICE_END_SECONDS.toFixed(3)}s</code></dd>
      <dt>Full lift</dt><dd><code>${OUTRO_TARGET_SECONDS.toFixed(3)}s</code></dd>
      <dt>Legal entry</dt><dd><code>${LEGAL_ENTRY_SECONDS.toFixed(3)}s</code></dd>
      <dt>QA</dt><dd><code>${path.relative(path.dirname(qaPath), qaPath)}</code></dd>
    </dl>
  </main>
</body>
</html>
`;
}

function patchPublishReadinessManifest({ createdUtc, successorRoot, qaPath, gainDb }) {
  if (!fs.existsSync(CURRENT_PUBLISH_MANIFEST)) return null;
  const manifest = readJson(CURRENT_PUBLISH_MANIFEST);
  manifest.status = "tighten_user_feedback_outro_music_too_quiet";
  manifest.human_disposition = "tighten";
  manifest.human_disposition_source = "user_feedback_2026-05-25_outro_music_notably_quieter_than_intro_and_vo";
  manifest.publish_ready = false;
  manifest.youtube_upload_ready = false;
  manifest.public_release_ready = false;
  manifest.may_youtube_action = false;
  manifest.reads = {
    ...(manifest.reads || {}),
    human_publish_readiness_keep_read: "tighten_user_feedback_outro_music_too_quiet",
    final_mix_approval_read: "tighten_outro_level_successor_required",
    outro_entry_level_match_read: "tighten_outro_music_noticeably_quieter_than_intro_and_vo",
    youtube_public_release_read: "blocked_manual_youtube_studio_only_current_upload_tighten",
  };
  manifest.user_feedback = [
    ...(Array.isArray(manifest.user_feedback)
      ? manifest.user_feedback.filter((item) => item?.successor_review_root !== successorRoot)
      : []),
    {
      created_utc: createdUtc,
      source: "in_app_browser_youtube_review",
      feedback: "the outro music isn't at the same level as the intro and VO - it's noticably quieter",
      disposition: "tighten",
      successor_review_root: successorRoot,
      successor_audio_qa_path: qaPath,
      proposed_successor_gain_db: gainDb,
      youtube_video_state: "unchanged_unlisted_review_video_remains_available_no_visibility_action_taken",
    },
  ];
  writeJson(CURRENT_PUBLISH_MANIFEST, manifest);
  return CURRENT_PUBLISH_MANIFEST;
}

function main() {
  const { gainDb, stamp: packetStamp } = parseArgs(process.argv);
  const createdUtc = new Date().toISOString();
  const outputRoot = path.join(
    path.dirname(LEGAL_PROOF_ROOT),
    `challenger_legal_end_screen_outro_level_successor_${packetStamp}`,
  );
  const audioDir = path.join(outputRoot, "audio_successor");
  const qaDir = path.join(outputRoot, "qa");
  const reviewDir = path.join(outputRoot, "review");
  const htmlReviewDir = path.join(outputRoot, "html_review");
  ensureDir(audioDir);
  ensureDir(qaDir);
  ensureDir(reviewDir);
  ensureDir(htmlReviewDir);

  const sourceMixSha = sha256(SOURCE_MIX);
  if (sourceMixSha !== EXPECTED_SOURCE_MIX_SHA256) {
    throw new Error(`Unexpected source mix sha ${sourceMixSha}`);
  }
  const sourceMixManifestSha = sha256(SOURCE_MIX_MANIFEST);
  const outputAudioPath = path.join(audioDir, `challenger_right_rail_alignment_music_mix_outro_plus${String(gainDb).replace(".", "p")}db_after_vo.wav`);
  const { gainLinear, rampSeconds, gainExpression } = createOutMix({ sourcePath: SOURCE_MIX, outputPath: outputAudioPath, gainDb });
  const outputAudioSha = sha256(outputAudioPath);
  const outputAudioProbe = ffprobeJson(outputAudioPath);

  cloneRuntimeLinks(LEGAL_PROOF_ROOT, outputRoot);
  const sourcePlayerPath = path.join(LEGAL_PROOF_ROOT, "player.html");
  const sourceProofBuildPath = path.join(LEGAL_PROOF_ROOT, "proof_build.json");
  const sourceHtml = fs.readFileSync(sourcePlayerPath, "utf8");
  const proofBuildId = `challenger-outro-level-successor_rolling_caption_rail_${packetStamp.replace("T", "")}`;
  const successor = {
    model: "challenger_outro_post_vo_level_successor_v1",
    created_utc: createdUtc,
    gain_db_after_voice: gainDb,
    gain_linear_after_voice: Number(gainLinear.toFixed(6)),
    gain_expression: gainExpression,
    gain_ramp_start_seconds: VOICE_END_SECONDS,
    gain_ramp_full_seconds: OUTRO_TARGET_SECONDS,
    gain_ramp_seconds: Number(rampSeconds.toFixed(6)),
    legal_entry_seconds: LEGAL_ENTRY_SECONDS,
    full_opacity_seconds: FULL_OPACITY_SECONDS,
    source_audio_sha256: sourceMixSha,
    output_audio_sha256: outputAudioSha,
    visual_timing_changed: false,
    youtube_upload_or_visibility_changed: false,
  };

  const playerPath = path.join(outputRoot, "player.html");
  const proofBuildPath = path.join(outputRoot, "proof_build.json");
  const manifestPath = path.join(outputRoot, "rough_assembly_manifest.json");
  const playerHtml = patchPlayerHtml({
    sourceHtml,
    audioSrc: `audio_successor/${path.basename(outputAudioPath)}`,
    proofBuildId,
    proofBuildPath,
    createdUtc,
    proofBuildJsonPath: "proof_build.json",
    successor,
  });
  writeText(playerPath, playerHtml);

  const qaPath = path.join(qaDir, "challenger_outro_level_audio_qa.json");
  const reviewPath = path.join(reviewDir, "challenger_outro_level_review_packet.md");
  const manifest = patchManifest({
    outputRoot,
    outputAudioPath,
    outputAudioProbe,
    outputAudioSha,
    sourceMixSha,
    sourceMixManifestSha,
    qaPath,
    reviewPath,
    proofBuildId,
    proofBuildPath,
    createdUtc,
    gainDb,
    gainLinear,
  });
  writeProofBuild({
    sourceProofBuildPath,
    outputPath: proofBuildPath,
    proofBuildId,
    outputRoot,
    manifestPath,
    playerPath,
    createdUtc,
    successor,
  });
  const proofBuildSha = sha256(proofBuildPath);
  manifest.proof_build_json_sha256 = proofBuildSha;
  manifest.proof_artifacts.proof_build_json_sha256 = proofBuildSha;
  writeJson(manifestPath, manifest);

  const currentRoot = path.join(htmlReviewDir, "current_youtube_audio_level");
  const successorRoot = path.join(htmlReviewDir, "successor_outro_plus5db_after_vo");
  cloneRuntimeLinks(LEGAL_PROOF_ROOT, currentRoot);
  cloneRuntimeLinks(LEGAL_PROOF_ROOT, successorRoot);
  linkDir(audioDir, path.join(successorRoot, "audio_successor"));

  const currentPlayer = path.join(currentRoot, "player.html");
  const successorPlayer = path.join(successorRoot, "player.html");
  const currentProofBuild = path.join(currentRoot, "proof_build.json");
  const successorProofBuild = path.join(successorRoot, "proof_build.json");
  const currentVariant = {
    ...successor,
    variant_id: "current_youtube_audio_level",
    output_audio_sha256: sourceMixSha,
    gain_db_after_voice: 0,
    gain_linear_after_voice: 1,
    gain_expression: "1",
    gain_ramp_seconds: 0,
  };
  writeText(
    currentPlayer,
    patchPlayerHtml({
      sourceHtml,
      audioSrc: null,
      proofBuildId: `${proofBuildId}_current_youtube_audio`,
      createdUtc,
      proofBuildJsonPath: "proof_build.json",
      successor: currentVariant,
    }),
  );
  writeText(
    successorPlayer,
    patchPlayerHtml({
      sourceHtml,
      audioSrc: `audio_successor/${path.basename(outputAudioPath)}`,
      proofBuildId: `${proofBuildId}_successor_outro_plus5db`,
      createdUtc,
      proofBuildJsonPath: "proof_build.json",
      successor: { ...successor, variant_id: "successor_outro_plus5db_after_vo" },
    }),
  );
  writeProofBuild({
    sourceProofBuildPath,
    outputPath: currentProofBuild,
    proofBuildId: `${proofBuildId}_current_youtube_audio`,
    outputRoot: currentRoot,
    manifestPath,
    playerPath: currentPlayer,
    createdUtc,
    successor: currentVariant,
  });
  writeProofBuild({
    sourceProofBuildPath,
    outputPath: successorProofBuild,
    proofBuildId: `${proofBuildId}_successor_outro_plus5db`,
    outputRoot: successorRoot,
    manifestPath,
    playerPath: successorPlayer,
    createdUtc,
    successor: { ...successor, variant_id: "successor_outro_plus5db_after_vo" },
  });

  const sourceMeasurements = measureWindows(SOURCE_MIX);
  const successorMeasurements = measureWindows(outputAudioPath);
  const qa = {
    model: "challenger_outro_level_audio_qa_v1",
    created_utc: createdUtc,
    source_audio: {
      path: SOURCE_MIX,
      sha256: sourceMixSha,
      expected_sha256: EXPECTED_SOURCE_MIX_SHA256,
      manifest_path: SOURCE_MIX_MANIFEST,
      manifest_sha256: sourceMixManifestSha,
    },
    successor_audio: {
      path: outputAudioPath,
      sha256: outputAudioSha,
      probe: outputAudioProbe,
    },
    gain: {
      db: gainDb,
      linear: Number(gainLinear.toFixed(6)),
      ramp_start_seconds: VOICE_END_SECONDS,
      full_gain_seconds: OUTRO_TARGET_SECONDS,
    },
    measurements: {
      source: sourceMeasurements,
      successor: successorMeasurements,
    },
    reads: {
      source_mix_hash_read: sourceMixSha === EXPECTED_SOURCE_MIX_SHA256 ? "pass_expected_predecessor_mix_hash" : "fail_unexpected_source_mix_hash",
      under_vo_overlap_read:
        Math.abs(sourceMeasurements.final_vo_prelap.input_i_lufs - successorMeasurements.final_vo_prelap.input_i_lufs) <= 0.25
          ? "pass_final_vo_overlap_loudness_unchanged"
          : "tighten_final_vo_overlap_changed",
      legal_window_level_match_read:
        Math.abs(successorMeasurements.legal_window_outro.input_i_lufs - sourceMeasurements.intro_music_only.input_i_lufs) <= 1.5
          ? "pass_successor_legal_window_outro_matches_intro_music_loudness_window"
          : "tighten_successor_legal_window_outro_still_not_matched",
      no_clipping_read:
        Math.max(...Object.values(successorMeasurements).map((item) => Number(item.max_volume_db)).filter(Number.isFinite)) <= -1
          ? "pass_no_window_peak_above_minus_1db"
          : "tighten_peak_margin_below_minus_1db_not_proven",
      youtube_action_read: "blocked_no_upload_or_visibility_change_performed",
    },
  };
  qa.passed = Object.values(qa.reads).every((read) => String(read).startsWith("pass") || String(read).startsWith("blocked"));
  writeJson(qaPath, qa);
  writeJson(path.join(audioDir, "challenger_outro_post_vo_level_successor_manifest.json"), {
    ...successor,
    source_audio_path: SOURCE_MIX,
    source_audio_manifest_path: SOURCE_MIX_MANIFEST,
    output_audio_path: outputAudioPath,
    output_audio_probe: outputAudioProbe,
    audio_qa_path: qaPath,
    audio_qa_sha256: sha256(qaPath),
    reads: qa.reads,
  });

  const reviewIndexPath = path.join(reviewDir, "challenger_outro_level_html_review.html");
  writeText(reviewIndexPath, reviewIndex({ reviewIndexPath, currentPlayer, successorPlayer, qaPath, gainDb }));
  writeText(
    reviewPath,
    [
      "# Challenger Outro Level Successor Review",
      "",
      `- Review index: ${reviewIndexPath}`,
      `- Current audio HTML: ${currentPlayer}`,
      `- Successor audio HTML: ${successorPlayer}`,
      `- Gain: +${gainDb.toFixed(1)} dB after VO end, ramping to full by ${OUTRO_TARGET_SECONDS.toFixed(3)}s`,
      `- Legal end-screen timing unchanged: fade starts ${LEGAL_ENTRY_SECONDS.toFixed(3)}s; full opacity ${FULL_OPACITY_SECONDS.toFixed(3)}s`,
      `- Source mix SHA: ${sourceMixSha}`,
      `- Successor mix SHA: ${outputAudioSha}`,
      `- QA: ${qaPath}`,
      "",
      "No MP4 render, upload, metadata update, or visibility action was performed.",
      "",
    ].join("\n"),
  );

  const publishManifestPath = patchPublishReadinessManifest({ createdUtc, successorRoot: outputRoot, qaPath, gainDb });
  console.log(
    JSON.stringify(
      {
        output_root: outputRoot,
        review_html: reviewIndexPath,
        current_html: currentPlayer,
        successor_html: successorPlayer,
        successor_audio: artifact(outputAudioPath),
        qa: artifact(qaPath),
        publish_manifest_marked_tighten: publishManifestPath,
        qa_passed: qa.passed,
      },
      null,
      2,
    ),
  );
}

main();
