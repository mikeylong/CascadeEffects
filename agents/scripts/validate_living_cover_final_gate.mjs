#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import {
  endScreenPaletteContractFailures,
  endScreenPaletteContractForManifest,
  endScreenPalettePlayerFailures,
} from "./living_cover_end_screen_palette_contract.mjs";

const REQUIRED_BLEND_READS = [
  "vo_outro_blend_plan_read",
  "vo_outro_music_blend_read",
  "vo_outro_perceptual_review_read",
  "outro_transition_review_sample_read",
  "outro_entry_level_match_read",
  "outro_under_vo_masking_read",
  "outro_target_after_voice_read",
];

const REQUIRED_PRELAP_READS = [
  "outro_prelap_source_read",
  "outro_prelap_start_read",
  "outro_no_restart_at_voice_end_read",
  "outro_source_continuity_read",
];

const REQUIRED_REGRESSION_READS = [
  "music_contract_regression_read",
];

const REQUIRED_MUSIC_READS = [
  ...REQUIRED_BLEND_READS,
  ...REQUIRED_PRELAP_READS,
  ...REQUIRED_REGRESSION_READS,
];

const REQUIRED_CHAPTER_TRANSITION_READS = [
  "challenger_staged_transition_model_read",
  "first_chapter_boundary_visual_ease_read",
  "chapter_boundary_hard_shift_read",
  "focused_transition_review_strip_read",
  "visual_state_debug_hook_read",
];

const REQUIRED_TEMPLATE_ID = "challenger_titleless_end_screen_overlay_on_living_cover_v1";
const REQUIRED_TARGETS = {
  left_video: { bbox_xy: [78, 382, 758, 765], role: "suggested_video" },
  right_video: { bbox_xy: [1162, 382, 1842, 765], role: "watch_next_video" },
  center_subscribe: { bbox_xy: [814, 429, 1106, 721], role: "subscribe" },
};

function usage() {
  console.error(
    "Usage: node scripts/validate_living_cover_final_gate.mjs --proof-manifest <path> --player <path> --audio-mix <path> [--final-manifest <path>] [--publish-readiness <path>]",
  );
  process.exit(2);
}

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 2) {
    const key = argv[i];
    const value = argv[i + 1];
    if (!key?.startsWith("--") || !value) usage();
    args[key.slice(2)] = value;
  }
  if (!args["proof-manifest"] || !args.player || !args["audio-mix"]) usage();
  return args;
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function requireFile(filePath, label = "file") {
  if (!filePath || !fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
    throw new Error(`Missing ${label}: ${filePath || "(empty)"}`);
  }
}

function resolveMaybeRelative(filePath, baseDir = process.cwd()) {
  if (!filePath || typeof filePath !== "string") return "";
  return path.isAbsolute(filePath) ? filePath : path.resolve(baseDir, filePath);
}

function readPasses(value) {
  return value === true || (typeof value === "string" && value.startsWith("pass"));
}

function checkMusicReads(reads, context) {
  for (const read of REQUIRED_MUSIC_READS) {
    if (!readPasses(reads?.[read])) {
      throw new Error(`${context} missing passing ${read}: ${reads?.[read] || "(missing)"}`);
    }
  }
}

function chapterTransitionScoped(proofManifest) {
  const reads = proofManifest.review_reads || proofManifest.rough_assembly_reads || proofManifest.qa?.reads || {};
  return (
    REQUIRED_CHAPTER_TRANSITION_READS.some((read) => reads?.[read] !== undefined)
    || Boolean(proofManifest.qa?.focused_transition_review_strip?.path)
    || Boolean(proofManifest.focused_transition_review_strip?.path)
    || Boolean(proofManifest.transition_review?.focused_transition_review_strip_path)
    || proofManifest.transition_review?.chapter_transition_model === "challenger_staged_visual_transition_v1"
  );
}

function checkChapterTransitionReads(proofManifest, proofManifestPath) {
  if (!chapterTransitionScoped(proofManifest)) return false;
  const reads = proofManifest.review_reads || proofManifest.rough_assembly_reads || proofManifest.qa?.reads || {};
  for (const read of REQUIRED_CHAPTER_TRANSITION_READS) {
    if (!readPasses(reads?.[read])) {
      throw new Error(`proof_manifest missing passing ${read}: ${reads?.[read] || "(missing)"}`);
    }
  }
  const proofDir = path.dirname(proofManifestPath);
  const transitionStripPath = resolveMaybeRelative(
    proofManifest.qa?.focused_transition_review_strip?.path
      || proofManifest.focused_transition_review_strip?.path
      || proofManifest.transition_review?.focused_transition_review_strip_path
      || "",
    proofDir,
  );
  requireFile(transitionStripPath, "focused chapter transition review strip");
  return true;
}

function asNumber(value, label) {
  const number = Number(value);
  if (!Number.isFinite(number)) throw new Error(`Audio mix has invalid ${label}: ${value ?? "(missing)"}`);
  return number;
}

function truthyContractValue(value) {
  if (value === true) return true;
  if (typeof value === "string") return value === "true" || value.startsWith("pass");
  return false;
}

function checkVoOutroBlend(audioMix) {
  const plan = audioMix.vo_outro_blend_plan || {};
  const voiceEndSeconds = asNumber(
    plan.voice_end_seconds ?? audioMix.voice_end_seconds,
    "voice_end_seconds",
  );
  const fullOutroSourcePath = plan.full_outro_source_path ?? audioMix.full_outro_source_path;
  if (!fullOutroSourcePath || typeof fullOutroSourcePath !== "string") {
    throw new Error("Audio mix has no full_outro_source_path for actual-outro prelap validation");
  }
  const fullOutroStartSeconds = asNumber(
    plan.full_outro_start_seconds ?? audioMix.full_outro_start_seconds ?? audioMix.outro_music_start_seconds,
    "full_outro_start_seconds",
  );
  const outroPrelapSeconds = asNumber(
    plan.outro_prelap_seconds ?? audioMix.outro_prelap_seconds ?? voiceEndSeconds - fullOutroStartSeconds,
    "outro_prelap_seconds",
  );
  const fullOutroFadeInSeconds = asNumber(
    plan.full_outro_fade_in_seconds ?? audioMix.full_outro_fade_in_seconds ?? outroPrelapSeconds,
    "full_outro_fade_in_seconds",
  );

  if (!(fullOutroStartSeconds < voiceEndSeconds)) {
    throw new Error(
      `Full outro must start before voice end: full_outro_start_seconds=${fullOutroStartSeconds}, voice_end_seconds=${voiceEndSeconds}`,
    );
  }
  if (!(outroPrelapSeconds > 0)) {
    throw new Error(`Actual outro prelap must be positive: outro_prelap_seconds=${outroPrelapSeconds}`);
  }
  const reachesTargetAt = asNumber(
    plan.outro_reaches_target_at_seconds ?? audioMix.outro_reaches_target_at_seconds,
    "outro_reaches_target_at_seconds",
  );
  const policy = plan.policy || audioMix.mix_profile_id || "";
  if (policy === "subtle_tail_outro_v1") {
    if (!plan.human_approved_prelap_override && (outroPrelapSeconds < 1.0 || outroPrelapSeconds > 2.0)) {
      throw new Error(
        `Subtle-tail outro must enter only under the final 1-2s: outro_prelap_seconds=${outroPrelapSeconds}`,
      );
    }
    const targetDelay = reachesTargetAt - voiceEndSeconds;
    if (targetDelay < 1.0) {
      throw new Error(
        `Subtle-tail outro target level must arrive after voice end: outro_reaches_target_at_seconds=${reachesTargetAt}, voice_end_seconds=${voiceEndSeconds}`,
      );
    }
    const underVoGain = Number(plan.outro_under_vo_gain_linear ?? audioMix.outro_under_vo_gain_linear);
    if (Number.isFinite(underVoGain) && underVoGain > 0.1) {
      throw new Error(`Subtle-tail under-VO gain is too high: outro_under_vo_gain_linear=${underVoGain}`);
    }
    const margin = Number(
      plan.under_vo_music_margin_db
        ?? audioMix.under_vo_music_margin_db
        ?? audioMix.level_reads?.under_vo_music_margin_db,
    );
    if (Number.isFinite(margin) && margin < 12) {
      throw new Error(`Under-VO music masking margin is below 12dB: under_vo_music_margin_db=${margin}`);
    }
  } else {
    if (!plan.human_approved_prelap_override) {
      throw new Error(
        `Non-subtle VO/outro policy requires human_approved_prelap_override: policy=${policy || "(missing)"}`,
      );
    }
    if (outroPrelapSeconds < 4.5) {
      throw new Error(`Overridden broad VO/outro prelap must still be explicit and coherent: outro_prelap_seconds=${outroPrelapSeconds}`);
    }
    if (fullOutroFadeInSeconds > outroPrelapSeconds + 0.2) {
      throw new Error(
        `Full outro fade-in should complete by voice end: fade=${fullOutroFadeInSeconds}, prelap=${outroPrelapSeconds}`,
      );
    }
    if (Math.abs(reachesTargetAt - voiceEndSeconds) > 0.25) {
      throw new Error(
        `Outro target level must land at voice end: outro_reaches_target_at_seconds=${reachesTargetAt}, voice_end_seconds=${voiceEndSeconds}`,
      );
    }
  }
  if (!truthyContractValue(plan.outro_no_restart_at_voice_end ?? audioMix.outro_no_restart_at_voice_end)) {
    throw new Error("Audio mix must explicitly prove outro_no_restart_at_voice_end");
  }
  if (!truthyContractValue(plan.outro_source_continuity ?? audioMix.outro_source_continuity)) {
    throw new Error("Audio mix must explicitly prove outro_source_continuity");
  }
  if (plan.bridge_source_path && plan.bridge_source_path !== fullOutroSourcePath && fullOutroStartSeconds >= voiceEndSeconds) {
    throw new Error("Bridge/proxy source cannot be the only music under the final VO before the real outro starts");
  }
}

function checkTargets(context) {
  if (context?.youtube_end_screen_template_id !== REQUIRED_TEMPLATE_ID) {
    throw new Error(`Wrong end-screen template: ${context?.youtube_end_screen_template_id || "(missing)"}`);
  }
  const targets = context.youtube_end_screen_targets || {};
  for (const [id, expected] of Object.entries(REQUIRED_TARGETS)) {
    const actual = targets[id];
    if (!actual) throw new Error(`Missing end-screen target ${id}`);
    const actualBox = actual.bbox_xy || [];
    if (actual.role !== expected.role) {
      throw new Error(`End-screen target ${id} role mismatch: ${actual.role} !== ${expected.role}`);
    }
    if (JSON.stringify(actualBox) !== JSON.stringify(expected.bbox_xy)) {
      throw new Error(`End-screen target ${id} bbox mismatch: ${JSON.stringify(actualBox)} !== ${JSON.stringify(expected.bbox_xy)}`);
    }
  }
}

function checkEndScreenPalette(manifest, manifestPath, context) {
  const failures = endScreenPaletteContractFailures(manifest, { manifestPath });
  if (failures.length > 0) {
    throw new Error(`${context} ${failures[0].id}: ${failures[0].detail}`);
  }
  return endScreenPaletteContractForManifest(manifest);
}

function normalizeEndScreenContext(manifest) {
  if (manifest?.end_screen_context) return manifest.end_screen_context;
  const screen = manifest?.youtube_end_screen;
  const targets = screen?.baked_placeholder_targets || screen?.layout || {};
  if (!screen || !targets) return null;
  return {
    youtube_end_screen_template_id: screen.template_id || "challenger_titleless_end_screen_overlay_on_living_cover_v1",
    youtube_end_screen_targets: {
      left_video: targets.left_video,
      right_video: targets.right_video,
      center_subscribe: targets.center_subscribe,
    },
  };
}

function checkPlayer(playerPath, options = {}, paletteContract = null) {
  const html = fs.readFileSync(playerPath, "utf8");
  const paletteFailures = endScreenPalettePlayerFailures(html, paletteContract);
  if (paletteFailures.length > 0) {
    throw new Error(`${paletteFailures[0].id}: ${paletteFailures[0].detail}`);
  }
  const classSets = [
    ["youtube-target left-video", "youtube-target right-video", "youtube-target subscribe-target"],
    ['class="target left"', 'class="target right"', 'class="target subscribe"'],
  ];
  const hasRequiredTemplate = classSets.some((requiredClasses) =>
    requiredClasses.every((required) => html.includes(required)),
  );
  if (!hasRequiredTemplate) {
    throw new Error(
      "Player does not include a recognized Challenger/Therac titleless three-target end-screen class set",
    );
  }
  for (const forbidden of ["end-target video", "end-target subscribe"]) {
    if (html.includes(forbidden)) throw new Error(`Player still includes forbidden ad hoc end-screen class: ${forbidden}`);
  }
  if (options.requireChapterTransitionHooks && !html.includes("window.__visualStateAt")) {
    throw new Error("Player does not expose window.__visualStateAt for chapter-transition QA");
  }
  if (options.requireChapterTransitionHooks && !html.includes("challenger_staged_visual_transition_v1")) {
    throw new Error("Player does not declare challenger_staged_visual_transition_v1");
  }
}

function checkAudioMix(audioMixPath) {
  const audioMix = readJson(audioMixPath);
  if (!audioMix.vo_outro_blend_plan) throw new Error("Audio mix has no vo_outro_blend_plan");
  if (!audioMix.outro_transition_review_sample?.mp3?.path) throw new Error("Audio mix has no outro transition MP3 sample");
  requireFile(audioMix.outro_transition_review_sample.mp3.path, "outro transition review MP3");
  checkMusicReads(audioMix.reads || {}, "audio_mix_manifest");
  checkVoOutroBlend(audioMix);
  return audioMix;
}

function collectTransitionSamplePaths(publishManifest) {
  const refs = [];
  const media = publishManifest.media || {};
  if (Array.isArray(media.transition_samples)) refs.push(...media.transition_samples);
  if (media.vo_outro_transition_sample) refs.push(media.vo_outro_transition_sample);
  if (publishManifest.local_assets?.vo_outro_transition_sample_mp3) {
    refs.push(publishManifest.local_assets.vo_outro_transition_sample_mp3);
  }
  const musicSample = publishManifest.music_integration_contract?.outro_transition_review_sample;
  if (musicSample?.mp3) refs.push(musicSample.mp3);
  if (musicSample?.wav) refs.push(musicSample.wav);
  return refs.map((ref) => ref?.path || ref?.rel || ref?.relative_path).filter(Boolean);
}

function reviewHtmlPathFor(publishManifest, manifestDir) {
  const explicitCandidates = [
    publishManifest.publish_readiness_review_html_path,
    publishManifest.review_html?.path,
    publishManifest.primary_review_artifact?.path,
  ].filter((candidate) => typeof candidate === "string" && candidate.trim());
  if (explicitCandidates.length > 0) return resolveMaybeRelative(explicitCandidates[0], manifestDir);
  return resolveMaybeRelative("review.html", manifestDir);
}

function isLifecycleReview(publishManifest) {
  return ["inception", "in_progress"].includes(publishManifest.lifecycle_stage)
    || publishManifest.stage === "publish_readiness_lifecycle_review";
}

function checkUploadLocksFalse(publishManifest, context) {
  const locks = publishManifest.upload_locks || publishManifest.locks || {};
  for (const key of ["publish_ready", "youtube_upload_ready", "public_release_ready", "may_youtube_action", "upload_performed"]) {
    const value = locks[key] ?? publishManifest[key];
    if (value === true || value === "true" || (typeof value === "string" && value.startsWith("pass"))) {
      throw new Error(`${context} must keep ${key}=false before explicit upload approval`);
    }
  }
}

function checkOptionalLocalMedia(publishManifest, manifestDir) {
  const media = publishManifest.media || {};
  for (const key of ["final_mp4", "caption_vtt", "caption_srt", "thumbnail_candidate", "vo_outro_transition_sample"]) {
    const ref = media[key];
    const mediaPath = ref?.path || ref?.rel || ref?.relative_path;
    if (mediaPath) requireFile(resolveMaybeRelative(mediaPath, manifestDir), `publish-readiness ${key}`);
  }
}

function checkPublishReadiness(publishReadinessPath, audioMixPath) {
  requireFile(publishReadinessPath, "publish-readiness manifest");
  const publishManifest = readJson(publishReadinessPath);
  const manifestDir = path.dirname(publishReadinessPath);
  requireFile(reviewHtmlPathFor(publishManifest, manifestDir), "publish-readiness review.html");
  checkUploadLocksFalse(publishManifest, "publish-readiness manifest");
  checkOptionalLocalMedia(publishManifest, manifestDir);

  if (isLifecycleReview(publishManifest)) {
    if (publishManifest.lifecycle_stage === "publish_readiness") {
      throw new Error("Lifecycle review cannot claim publish_readiness lifecycle_stage");
    }
    return;
  }

  checkMusicReads(publishManifest.reads || publishManifest.readiness_reads || {}, "publish_readiness_manifest.reads");
  checkEndScreenPalette(publishManifest, publishReadinessPath, "publish_readiness_manifest");
  const finalKeepRead = (publishManifest.reads || publishManifest.readiness_reads || {}).final_assembly_human_keep_read;
  if (!readPasses(finalKeepRead)) {
    throw new Error(`publish_readiness_manifest.reads missing passing final_assembly_human_keep_read: ${finalKeepRead || "(missing)"}`);
  }

  const samplePaths = collectTransitionSamplePaths(publishManifest);
  if (samplePaths.length === 0) {
    throw new Error("Publish-readiness manifest has no VO/outro transition sample");
  }
  for (const samplePath of samplePaths) {
    requireFile(resolveMaybeRelative(samplePath, manifestDir), "publish-readiness VO/outro transition sample");
  }

  const contractPath = publishManifest.music_integration_contract?.audio_mix_manifest_path;
  if (contractPath && resolveMaybeRelative(contractPath, manifestDir) !== path.resolve(audioMixPath)) {
    throw new Error("Publish-readiness music_integration_contract points at a different audio mix manifest");
  }
  if (Array.isArray(publishManifest.required_reads)) {
    for (const read of REQUIRED_MUSIC_READS) {
      if (!publishManifest.required_reads.includes(read)) {
        throw new Error(`Publish-readiness required_reads omits ${read}`);
      }
    }
  }
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  requireFile(args["proof-manifest"], "proof manifest");
  requireFile(args.player, "player");
  requireFile(args["audio-mix"], "audio mix manifest");
  const proofManifest = readJson(args["proof-manifest"]);
  const audioMix = checkAudioMix(args["audio-mix"]);
  const chapterTransitionRequired = chapterTransitionScoped(proofManifest);
  const proofPaletteContract = checkEndScreenPalette(proofManifest, args["proof-manifest"], "proof_manifest");
  checkPlayer(args.player, { requireChapterTransitionHooks: chapterTransitionRequired }, proofPaletteContract);
  checkMusicReads(proofManifest.music_integration_contract?.reads || proofManifest.rough_assembly_reads || {}, "proof_manifest");
  const chapterTransitionChecked = checkChapterTransitionReads(proofManifest, args["proof-manifest"]);
  checkTargets(normalizeEndScreenContext(proofManifest));
  if (proofManifest.music_integration_contract?.audio_mix_manifest_sha256 && proofManifest.music_integration_contract.audio_mix_manifest_path !== args["audio-mix"]) {
    throw new Error("Proof manifest music_integration_contract points at a different audio mix manifest");
  }
  if (args["final-manifest"]) {
    requireFile(args["final-manifest"], "final render manifest");
    const finalManifest = readJson(args["final-manifest"]);
    checkMusicReads(finalManifest.qa_reads || {}, "final_render_manifest.qa_reads");
    const finalEndScreenContext = finalManifest.end_screen_context
      || normalizeEndScreenContext(finalManifest)
      || normalizeEndScreenContext(readJson(finalManifest.proof_manifest_path));
    checkTargets(finalEndScreenContext);
    checkEndScreenPalette(finalManifest, args["final-manifest"], "final_render_manifest");
    if (!finalManifest.music_integration_contract) throw new Error("Final render manifest omits music_integration_contract");
    if (!finalManifest.review_audio_mix) throw new Error("Final render manifest omits review_audio_mix");
    if (finalManifest.music_integration_contract?.audio_mix_manifest_path && finalManifest.music_integration_contract.audio_mix_manifest_path !== args["audio-mix"]) {
      throw new Error("Final render music_integration_contract points at a different audio mix manifest");
    }
    if (finalManifest.review_audio_mix?.audio_mix_manifest_path && finalManifest.review_audio_mix.audio_mix_manifest_path !== args["audio-mix"]) {
      throw new Error("Final render review_audio_mix points at a different audio mix manifest");
    }
  }
  if (args["publish-readiness"]) {
    checkPublishReadiness(args["publish-readiness"], args["audio-mix"]);
  }
  console.log(
    JSON.stringify(
      {
        status: "pass",
        template_id: REQUIRED_TEMPLATE_ID,
        chapter_transition_model: chapterTransitionChecked ? "challenger_staged_visual_transition_v1" : "not_scoped",
        audio_mix: audioMix.packet_id || path.basename(args["audio-mix"]),
      },
      null,
      2,
    ),
  );
}

main();
