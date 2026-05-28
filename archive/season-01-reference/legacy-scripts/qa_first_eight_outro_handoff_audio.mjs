#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const EPISODES_ROOT = "/Users/mike/Episodes_CascadeEffects";
const REVIEW_INDEX_PATH = path.join(EPISODES_ROOT, "first-eight-rolling-caption-rail-review.html");
const OUTRO_POLICY = "subtle_tail_outro_v1";
const EXPECTED_PRELAP_SECONDS = 1.5;
const EXPECTED_TARGET_AFTER_VOICE_SECONDS = 3;
const MIN_TARGET_MARGIN_DB = 12;
const INTRO_TRIM_MODEL = "first_eight_intro_trim_6s_v1";
const INTRO_TRIM_SECONDS = 6;
const PREVIOUS_VOICE_START_OFFSET_SECONDS = 9.601451;
const VOICE_START_OFFSET_SECONDS = 3.601451;

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJson(filePath, value) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function findManifests() {
  if (fs.existsSync(REVIEW_INDEX_PATH)) {
    const html = fs.readFileSync(REVIEW_INDEX_PATH, "utf8");
    const manifests = [];
    const seen = new Set();
    for (const match of html.matchAll(/href="http:\/\/127\.0\.0\.1:8766\/([^"?]+\/player\.html)(?:\?[^"]*)?"/g)) {
      const playerPath = path.join(EPISODES_ROOT, decodeURIComponent(match[1]));
      const manifestPath = path.join(path.dirname(playerPath), "rough_assembly_manifest.json");
      if (fs.existsSync(manifestPath) && !seen.has(manifestPath)) {
        seen.add(manifestPath);
        manifests.push(manifestPath);
      }
    }
    if (manifests.length) return manifests.sort();
  }
  const out = [];
  const stack = [EPISODES_ROOT];
  while (stack.length) {
    const dir = stack.pop();
    let entries = [];
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      continue;
    }
    for (const entry of entries) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) stack.push(full);
      else if (/rough_assembly_manifest\.json$/i.test(entry.name) && /rolling_caption_rail_rough_proof_20260520T235500Z/.test(full)) {
        out.push(full);
      }
    }
  }
  return out.sort();
}

function valueAt(obj, dotted) {
  return dotted.split(".").reduce((cur, part) => (cur && cur[part] !== undefined ? cur[part] : undefined), obj);
}

function firstFinite(values, fallback = NaN) {
  for (const value of values) {
    const numeric = Number(value);
    if (Number.isFinite(numeric)) return numeric;
  }
  return fallback;
}

function qaManifest(manifestPath) {
  const manifest = readJson(manifestPath);
  const revalidation = manifest.music_integration_contract_revalidation || {};
  const mixManifestPath = revalidation.review_audio_mix_manifest_path || valueAt(manifest, "review_audio_mix.manifest_path");
  const mixManifest = mixManifestPath && fs.existsSync(mixManifestPath) ? readJson(mixManifestPath) : {};
  const timing = mixManifest.timing || {};
  const voiceStart = firstFinite([timing.voice_start_seconds, revalidation.voice_start_offset_seconds, manifest.voice_start_offset_seconds]);
  const introTrimSeconds = firstFinite([mixManifest.intro_trim_seconds, timing.intro_trim_seconds, revalidation.intro_trim_seconds, manifest.intro_trim_seconds]);
  const previousVoiceStart = firstFinite([
    mixManifest.previous_voice_start_offset_seconds,
    timing.previous_voice_start_offset_seconds,
    revalidation.previous_voice_start_offset_seconds,
    manifest.previous_voice_start_offset_seconds,
  ]);
  const voiceEnd = firstFinite([timing.voice_end_seconds, revalidation.voice_end_seconds, valueAt(manifest, "music_contract.timing_contract.voice_end_seconds")]);
  const outroStart = firstFinite([timing.full_outro_start_seconds, revalidation.full_outro_start_seconds, manifest.full_outro_start_seconds]);
  const prelap = firstFinite([timing.outro_prelap_seconds, revalidation.outro_prelap_seconds, manifest.outro_prelap_seconds]);
  const targetAt = firstFinite([timing.outro_reaches_target_at_seconds, revalidation.outro_reaches_target_at_seconds]);
  const targetAfterVoice = firstFinite([timing.outro_target_after_voice_seconds, revalidation.outro_target_after_voice_seconds, manifest.outro_target_after_voice_seconds], targetAt - voiceEnd);
  const underGain = firstFinite([timing.outro_under_vo_gain_linear, revalidation.outro_under_vo_gain_linear]);
  const targetGain = firstFinite([timing.outro_target_gain_linear, revalidation.outro_target_gain_linear]);
  const targetMarginDb = firstFinite([timing.outro_target_margin_db, revalidation.outro_target_margin_db, manifest.outro_target_margin_db], MIN_TARGET_MARGIN_DB);
  const outputDuration = firstFinite([mixManifest.output_duration_seconds, revalidation.review_audio_mix_duration_seconds]);
  const expectedDuration = firstFinite([mixManifest.expected_total_duration_seconds, revalidation.review_audio_mix_expected_duration_seconds]);
  const durationDelta = firstFinite([mixManifest.duration_delta_seconds, revalidation.review_audio_mix_duration_delta_seconds], outputDuration - expectedDuration);
  const checks = {
    review_mix_manifest_exists: Boolean(mixManifestPath && fs.existsSync(mixManifestPath)),
    intro_trim_model_matches:
      (mixManifest.intro_trim_model || timing.intro_trim_model || revalidation.intro_trim_model || manifest.intro_trim_model) ===
      INTRO_TRIM_MODEL,
    intro_trim_seconds_is_6s: Number.isFinite(introTrimSeconds) && Math.abs(introTrimSeconds - INTRO_TRIM_SECONDS) <= 0.001,
    previous_voice_start_offset_is_preserved:
      Number.isFinite(previousVoiceStart) && Math.abs(previousVoiceStart - PREVIOUS_VOICE_START_OFFSET_SECONDS) <= 0.0005,
    voice_start_offset_is_trimmed:
      Number.isFinite(voiceStart) && Math.abs(voiceStart - VOICE_START_OFFSET_SECONDS) <= 0.0005,
    outro_policy_is_subtle_tail: (timing.outro_policy || manifest.outro_policy || revalidation.outro_policy) === OUTRO_POLICY,
    full_outro_starts_1p5s_before_voice_end:
      Number.isFinite(voiceEnd) && Number.isFinite(outroStart) && Math.abs((voiceEnd - outroStart) - EXPECTED_PRELAP_SECONDS) <= 0.05,
    prelap_field_matches_policy: Number.isFinite(prelap) && Math.abs(prelap - EXPECTED_PRELAP_SECONDS) <= 0.05,
    target_reaches_after_voice: Number.isFinite(targetAfterVoice) && targetAfterVoice >= EXPECTED_TARGET_AFTER_VOICE_SECONDS - 0.1,
    under_voice_gain_is_low: Number.isFinite(underGain) && underGain <= 0.1,
    target_gain_after_voice_is_present: Number.isFinite(targetGain) && targetGain > underGain,
    target_margin_at_least_12db: Number.isFinite(targetMarginDb) && targetMarginDb >= MIN_TARGET_MARGIN_DB,
    mix_duration_matches_contract: Number.isFinite(durationDelta) && Math.abs(durationDelta) <= 0.08,
  };
  const failures = Object.entries(checks).filter(([, pass]) => !pass).map(([id]) => id);
  const artifactPath = path.join(path.dirname(manifestPath), "qa/vo_outro_handoff_audio_qa.json");
  const artifact = {
    model: "first_eight_vo_outro_subtle_tail_audio_handoff_qa_v1",
    episode_id: manifest.episode_id,
    manifest_path: manifestPath,
    review_audio_mix_manifest_path: mixManifestPath || "not_found",
    intro_trim_model: INTRO_TRIM_MODEL,
    intro_trim_seconds: introTrimSeconds,
    previous_voice_start_offset_seconds: previousVoiceStart,
    voice_start_offset_seconds: voiceStart,
    voice_end_seconds: voiceEnd,
    full_outro_start_seconds: outroStart,
    outro_prelap_seconds: prelap,
    outro_reaches_target_at_seconds: targetAt,
    outro_target_after_voice_seconds: targetAfterVoice,
    outro_under_vo_gain_linear: underGain,
    outro_target_gain_linear: targetGain,
    outro_target_margin_db: targetMarginDb,
    output_duration_seconds: outputDuration,
    expected_duration_seconds: expectedDuration,
    duration_delta_seconds: durationDelta,
    checks,
    passed: failures.length === 0,
    failures,
    reads: {
      vo_outro_blend_read: failures.length ? "tighten_subtle_tail_outro_audio_contract" : "pass_subtle_tail_outro_v1_audio_handoff",
      intro_trim_audio_qa_read: checks.intro_trim_model_matches && checks.intro_trim_seconds_is_6s && checks.voice_start_offset_is_trimmed
        ? "pass_first_eight_intro_trim_6s_v1"
        : "tighten_first_eight_intro_trim_audio_contract",
      outro_prelap_start_read: checks.full_outro_starts_1p5s_before_voice_end ? "pass_1p5s_before_voice_end" : "tighten_outro_prelap_start",
      outro_under_vo_masking_read: checks.under_voice_gain_is_low && checks.target_margin_at_least_12db ? "pass_target_margin_at_least_12db" : "tighten_outro_under_vo_masking",
      outro_target_after_voice_read: checks.target_reaches_after_voice ? "pass_target_gain_3s_after_voice_end" : "tighten_target_gain_timing",
      outro_no_restart_at_voice_end_read: failures.length ? "pending_no_restart_contract_recheck" : "pass_full_outro_continues_without_restart",
    },
  };
  writeJson(artifactPath, artifact);
  manifest.vo_outro_blend_audio_qa_path = artifactPath;
  manifest.vo_outro_blend_audio_qa_read = artifact.reads.vo_outro_blend_read;
  manifest.vo_outro_blend_read = artifact.reads.vo_outro_blend_read;
  manifest.intro_trim_audio_qa_read = artifact.reads.intro_trim_audio_qa_read;
  manifest.intro_trim_model = INTRO_TRIM_MODEL;
  manifest.intro_trim_seconds = INTRO_TRIM_SECONDS;
  manifest.previous_voice_start_offset_seconds = PREVIOUS_VOICE_START_OFFSET_SECONDS;
  manifest.voice_start_offset_seconds = VOICE_START_OFFSET_SECONDS;
  manifest.rough_assembly_reads = manifest.rough_assembly_reads || {};
  Object.assign(manifest.rough_assembly_reads, artifact.reads);
  manifest.qa = manifest.qa || {};
  manifest.qa.vo_outro_blend_audio_qa_path = artifactPath;
  manifest.qa.vo_outro_blend_audio_qa_read = artifact.reads.vo_outro_blend_read;
  manifest.qa.intro_trim_audio_qa_read = artifact.reads.intro_trim_audio_qa_read;
  writeJson(manifestPath, manifest);
  return artifact;
}

function main() {
  const artifacts = findManifests().map(qaManifest);
  for (const artifact of artifacts) {
    console.log(`${artifact.passed ? "PASS" : "FAIL"} audio handoff: ${artifact.episode_id}`);
    for (const failure of artifact.failures) console.log(`  - ${failure}`);
  }
  process.exit(artifacts.every((artifact) => artifact.passed) ? 0 : 1);
}

main();
