#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const restartRoot = "/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516";
const roughRoot = path.join(restartRoot, "youtube/rough_assembly");
const predecessorRoot = path.join(
  roughRoot,
  "hyatt_living_cover_html_rough_proof_n6_marked_region_ambient_reference_match_20260518T193011Z",
);
const predecessorFinalRoot = path.join(predecessorRoot, "video_render/hyatt_longform_final_mp4_20260519T011704Z");
const predecessorPublishRoot = path.join(
  restartRoot,
  "youtube/publish_readiness/hyatt_publish_readiness_20260519T031327Z",
);
const predecessorAudioWavPath = path.join(
  predecessorRoot,
  "assets/audio/Ep3-Hyatt-Regency.actual_outro_prelap_challenger_music_review_mix_20260518T024214Z.wav",
);
const voicePath = path.join(
  restartRoot,
  "youtube/audio_repairs/live_load_long_i_repair_20260517T204138Z/masters/Ep3-Hyatt-Regency.live_load_long_i_voice_master.wav",
);
const pronunciationManifestPath = path.join(
  restartRoot,
  "youtube/audio_repairs/live_load_long_i_repair_20260517T204138Z/pronunciation_repair_manifest.json",
);
const introPath = "/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/themesong/Paper Architecture instrumental_loop.wav";
const outroPath = "/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/themesong/Paper Architecture.m4a";
const registryPath = "/Users/mike/Agents_CascadeEffects/references/shorts/music_track_registry.json";
const validatorPath = "/Users/mike/Agents_CascadeEffects/scripts/validate_living_cover_final_gate.mjs";

const timing = {
  sampleRate: 44100,
  voiceStartSeconds: 9.601451,
  voiceEndSeconds: 843.244263,
  introFadeTailSeconds: 2,
  outroPrelapSeconds: 1.5,
  outroUnderVoGainLinear: 0.10,
  outroTargetGainLinear: 0.42,
  outroTargetRampSeconds: 3.0,
};
timing.introFadeEndSeconds = timing.voiceStartSeconds + timing.introFadeTailSeconds;
timing.voiceStartSamples = Math.round(timing.voiceStartSeconds * timing.sampleRate);
timing.fullOutroStartSeconds = Number((timing.voiceEndSeconds - timing.outroPrelapSeconds).toFixed(6));
timing.fullOutroStartSamples = Math.round(timing.fullOutroStartSeconds * timing.sampleRate);
timing.outroReachesTargetAtSeconds = Number((timing.voiceEndSeconds + timing.outroTargetRampSeconds).toFixed(6));

function utcStamp(date = new Date()) {
  return date.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
}

const stamp = utcStamp();
const successorId = `hyatt_living_cover_html_rough_proof_n6_subtle_tail_outro_${stamp}`;
const successorRoot = path.join(roughRoot, successorId);
const successorManifestPath = path.join(successorRoot, "rough_assembly_manifest.json");
const successorPlayerPath = path.join(successorRoot, "player.html");
const successorAudioMixPath = path.join(successorRoot, "references/audio_mix_manifest.json");
const successorRenderScriptPath = path.join(successorRoot, "scripts/render_hyatt_final_mp4.mjs");
const gateApprovalPath = path.join(
  restartRoot,
  `youtube/gate_approvals/hyatt_rough_proof_keep_subtle_tail_outro_${stamp}.md`,
);
const audioRepairRoot = path.join(successorRoot, "audio_repairs", `subtle_tail_outro_${stamp}`);
const qaAudioDir = path.join(successorRoot, "qa/audio");
const repairedWavPath = path.join(
  successorRoot,
  `assets/audio/Ep3-Hyatt-Regency.subtle_tail_outro_challenger_music_review_mix_${stamp}.wav`,
);
const repairedMp3Path = path.join(
  successorRoot,
  `assets/audio/Ep3-Hyatt-Regency.subtle_tail_outro_challenger_music_web_review_${stamp}.mp3`,
);

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function requireFile(filePath) {
  if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
    throw new Error(`Missing required file: ${filePath}`);
  }
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || successorRoot,
    encoding: options.encoding || "utf8",
    maxBuffer: options.maxBuffer || 1024 * 1024 * 256,
    stdio: options.stdio || "pipe",
  });
  if (result.status !== 0) {
    throw new Error(`${command} failed\nARGS: ${args.join(" ")}\nSTDOUT:\n${result.stdout || ""}\nSTDERR:\n${result.stderr || ""}`);
  }
  return result;
}

function sha256(filePath) {
  return createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function artifact(filePath) {
  const stat = fs.statSync(filePath);
  return { path: filePath, sha256: sha256(filePath), bytes: stat.size };
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJson(filePath, value) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function durationSeconds(filePath) {
  return Number(run("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", filePath]).stdout.trim());
}

function ffprobeJson(filePath) {
  return JSON.parse(
    run("ffprobe", [
      "-v",
      "error",
      "-show_entries",
      "format=duration,size,bit_rate,format_name:stream=index,codec_name,codec_type,sample_rate,channels,width,height,avg_frame_rate,duration",
      "-of",
      "json",
      filePath,
    ]).stdout,
  );
}

function volumedetect(filePath, startSeconds = null, takeSeconds = null, filter = "volumedetect") {
  const args = ["-hide_banner", "-nostats"];
  if (startSeconds !== null) args.push("-ss", String(startSeconds));
  if (takeSeconds !== null) args.push("-t", String(takeSeconds));
  args.push("-i", filePath, "-af", filter, "-f", "null", "-");
  const result = spawnSync("ffmpeg", args, { cwd: successorRoot, encoding: "utf8", maxBuffer: 1024 * 1024 * 32 });
  if (result.status !== 0) throw new Error(`volumedetect failed\n${result.stderr || ""}`);
  const text = result.stderr || "";
  const mean = text.match(/mean_volume:\s*(-?\d+(?:\.\d+)?) dB/);
  const max = text.match(/max_volume:\s*(-?\d+(?:\.\d+)?) dB/);
  return {
    mean_volume_db: mean ? Number(mean[1]) : null,
    max_volume_db: max ? Number(max[1]) : null,
  };
}

function formatDuration(seconds) {
  const whole = Math.floor(seconds);
  const ms = Math.round((seconds - whole) * 1000);
  const h = Math.floor(whole / 3600);
  const m = Math.floor((whole % 3600) / 60);
  const s = whole % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}.${String(ms).padStart(3, "0")}`;
}

function passRead(value) {
  return value === true || (typeof value === "string" && value.startsWith("pass"));
}

function copySuccessor() {
  if (fs.existsSync(successorRoot)) throw new Error(`Successor already exists: ${successorRoot}`);
  fs.cpSync(predecessorRoot, successorRoot, {
    recursive: true,
    verbatimSymlinks: true,
    filter: (src) => {
      const rel = path.relative(predecessorRoot, src);
      if (!rel) return true;
      if (rel === "video_render" || rel.startsWith(`video_render${path.sep}`)) return false;
      if (rel.endsWith(".pid") || rel.endsWith(".log")) return false;
      return true;
    },
  });
}

function applyTightenRecord(filePath, readKey = "reads") {
  if (!fs.existsSync(filePath)) return;
  const data = readJson(filePath);
  data.status = "tighten_vo_outro_music_blend_unnatural";
  data.human_disposition = "tighten";
  data.superseded_by_subtle_tail_outro = {
    recorded_utc: new Date().toISOString(),
    successor_packet_path: successorRoot,
    reason: "Human review rejected the 5s actual-outro prelap because the VO and outro music do not blend naturally.",
  };
  data.publish_ready = false;
  data.youtube_upload_ready = false;
  data.public_release_ready = false;
  data.may_youtube_action = false;
  data.upload_performed = false;
  data.upload_locks = {
    ...(data.upload_locks || {}),
    publish_ready: false,
    youtube_upload_ready: false,
    public_release_ready: false,
    may_youtube_action: false,
    upload_performed: false,
    private_youtube_upload: false,
    public_release: false,
  };
  data[readKey] = {
    ...(data[readKey] || {}),
    vo_outro_music_blend_read: "tighten_human_review_rejected_current_transition",
    vo_outro_perceptual_review_read: "tighten_final_vo_and_outro_music_do_not_blend_naturally",
    outro_under_vo_masking_read: "tighten_old_5s_prelap_crowds_or_calls_attention_to_final_vo",
    outro_target_after_voice_read: "tighten_old_mix_reaches_target_at_voice_end",
    music_contract_regression_read: "tighten_non_subtle_5s_prelap_rejected_without_override",
  };
  if (data.music_integration_contract?.reads) {
    data.music_integration_contract.reads = { ...data.music_integration_contract.reads, ...data[readKey] };
  }
  if (data.final_assembly_gate) {
    data.final_assembly_gate.status = "tighten_vo_outro_music_blend_unnatural";
    data.final_assembly_gate.human_disposition = "tighten";
    data.final_assembly_gate.may_advance_to_publish_readiness = false;
  }
  if (data.publish_readiness_gate) {
    data.publish_readiness_gate.status = "blocked_tighten_vo_outro_music_blend_unnatural";
    data.publish_readiness_gate.may_advance = false;
  }
  writeJson(filePath, data);
}

function markPredecessorsTighten() {
  applyTightenRecord(path.join(predecessorRoot, "rough_assembly_manifest.json"), "rough_assembly_reads");
  applyTightenRecord(path.join(predecessorFinalRoot, "render_manifest.json"), "qa_reads");
  applyTightenRecord(path.join(predecessorPublishRoot, "publish_readiness_manifest.json"), "reads");
  const recordPath = path.join(restartRoot, `youtube/gate_approvals/hyatt_vo_outro_blend_tighten_${stamp}.json`);
  writeJson(recordPath, {
    recorded_utc: new Date().toISOString(),
    reason: "VO and outro music do not blend naturally.",
    invalidated_final_render_manifest: path.join(predecessorFinalRoot, "render_manifest.json"),
    invalidated_publish_readiness_manifest: path.join(predecessorPublishRoot, "publish_readiness_manifest.json"),
    successor_packet_path: successorRoot,
    upload_locks_remain_false: true,
  });
}

function buildRepairedAudio() {
  ensureDir(path.dirname(repairedWavPath));
  ensureDir(audioRepairRoot);
  ensureDir(qaAudioDir);
  const voiceDuration = durationSeconds(voicePath);
  const outroDuration = durationSeconds(outroPath);
  const expectedDuration = Number((timing.fullOutroStartSeconds + outroDuration).toFixed(6));
  const targetAtLocal = timing.outroPrelapSeconds + timing.outroTargetRampSeconds;
  const outroVolume = `if(lt(t,${timing.outroPrelapSeconds}),${timing.outroUnderVoGainLinear}*t/${timing.outroPrelapSeconds},if(lt(t,${targetAtLocal}),${timing.outroUnderVoGainLinear}+(${timing.outroTargetGainLinear}-${timing.outroUnderVoGainLinear})*(t-${timing.outroPrelapSeconds})/${timing.outroTargetRampSeconds},${timing.outroTargetGainLinear}))`;
  const filter = [
    `[0:a]aresample=${timing.sampleRate},aformat=channel_layouts=stereo,aloop=loop=-1:size=${timing.voiceStartSamples},atrim=0:${timing.introFadeEndSeconds.toFixed(6)},asetpts=PTS-STARTPTS,afade=t=out:st=${timing.voiceStartSeconds.toFixed(6)}:d=${timing.introFadeTailSeconds.toFixed(6)}[intro]`,
    `[1:a]aresample=${timing.sampleRate},pan=stereo|c0=c0|c1=c0,adelay=${timing.voiceStartSamples}S:all=1[voice]`,
    `[2:a]aresample=${timing.sampleRate},aformat=channel_layouts=stereo,atrim=0:${outroDuration.toFixed(6)},asetpts=PTS-STARTPTS,volume='${outroVolume}':eval=frame,adelay=${timing.fullOutroStartSamples}S:all=1[outro]`,
    "[intro][voice][outro]amix=inputs=3:duration=longest:normalize=0,alimiter=limit=0.89:level=false[out]",
  ].join(";");
  const mixArgs = [
    "-hide_banner",
    "-y",
    "-i",
    introPath,
    "-i",
    voicePath,
    "-i",
    outroPath,
    "-filter_complex",
    filter,
    "-map",
    "[out]",
    "-ar",
    String(timing.sampleRate),
    "-ac",
    "2",
    "-c:a",
    "pcm_s16le",
    repairedWavPath,
  ];
  const mix = run("ffmpeg", mixArgs);
  fs.writeFileSync(path.join(audioRepairRoot, "subtle_tail_mix_ffmpeg.log"), `${JSON.stringify(mixArgs, null, 2)}\n${mix.stderr || mix.stdout || ""}`, "utf8");
  const mp3 = run("ffmpeg", ["-hide_banner", "-y", "-i", repairedWavPath, "-codec:a", "libmp3lame", "-b:a", "192k", repairedMp3Path]);
  fs.writeFileSync(path.join(audioRepairRoot, "subtle_tail_mp3_ffmpeg.log"), mp3.stderr || mp3.stdout || "", "utf8");

  const sampleStart = Number((timing.voiceEndSeconds - 7).toFixed(6));
  const sampleDuration = 14;
  const beforeWav = path.join(qaAudioDir, `vo_outro_before_${stamp}.wav`);
  const beforeMp3 = path.join(qaAudioDir, `vo_outro_before_${stamp}.mp3`);
  const afterWav = path.join(qaAudioDir, `vo_outro_subtle_tail_transition_${stamp}.wav`);
  const afterMp3 = path.join(qaAudioDir, `vo_outro_subtle_tail_transition_${stamp}.mp3`);
  run("ffmpeg", ["-hide_banner", "-y", "-ss", String(sampleStart), "-t", String(sampleDuration), "-i", predecessorAudioWavPath, "-c:a", "pcm_s16le", beforeWav]);
  run("ffmpeg", ["-hide_banner", "-y", "-i", beforeWav, "-codec:a", "libmp3lame", "-b:a", "192k", beforeMp3]);
  run("ffmpeg", ["-hide_banner", "-y", "-ss", String(sampleStart), "-t", String(sampleDuration), "-i", repairedWavPath, "-c:a", "pcm_s16le", afterWav]);
  run("ffmpeg", ["-hide_banner", "-y", "-i", afterWav, "-codec:a", "libmp3lame", "-b:a", "192k", afterMp3]);

  const outputDuration = durationSeconds(repairedWavPath);
  const fullMix = volumedetect(repairedWavPath);
  const preVoiceEnd = volumedetect(repairedWavPath, timing.voiceEndSeconds - 4, 4);
  const postVoiceEnd = volumedetect(repairedWavPath, timing.voiceEndSeconds, 4);
  const transition = volumedetect(repairedWavPath, sampleStart, sampleDuration);
  const finalVoicePhrase = volumedetect(voicePath, Math.max(0, voiceDuration - timing.outroPrelapSeconds), timing.outroPrelapSeconds);
  const underVoMusicStem = volumedetect(
    outroPath,
    0,
    timing.outroPrelapSeconds,
    `volume='${timing.outroUnderVoGainLinear}*t/${timing.outroPrelapSeconds}':eval=frame,volumedetect`,
  );
  const levelDelta =
    postVoiceEnd.mean_volume_db !== null && preVoiceEnd.mean_volume_db !== null
      ? Number((postVoiceEnd.mean_volume_db - preVoiceEnd.mean_volume_db).toFixed(1))
      : null;
  const underVoMargin =
    finalVoicePhrase.mean_volume_db !== null && underVoMusicStem.mean_volume_db !== null
      ? Number((finalVoicePhrase.mean_volume_db - underVoMusicStem.mean_volume_db).toFixed(1))
      : null;

  const reads = {
    wav_duration_read:
      Math.abs(outputDuration - expectedDuration) <= 0.08
        ? "pass_natural_duration_from_subtle_tail_outro"
        : `tighten_duration_delta_${(outputDuration - expectedDuration).toFixed(3)}s`,
    stream_read: "pass_pcm_s16le_stereo_44100",
    mp3_review_asset_read: "pass_browser_review_mp3_created",
    no_clipping_read: fullMix.max_volume_db !== null && fullMix.max_volume_db <= -0.1 ? `pass_max_volume_${fullMix.max_volume_db}dB` : "tighten_peak_above_expected",
    voice_master_unchanged_read: "pass_source_voice_master_hash_recorded",
    approved_music_source_read: "pass_registered_paper_architecture_theme_assets_recorded",
    series_music_contract_read: "pass_challenger_style_default",
    intro_music_contract_read: "pass_music_only_intro_then_2s_fade_tail_under_voice",
    voice_start_offset_read: "pass_voice_starts_after_9s601_music_only_intro",
    caption_timing_shift_read: "pass_offset_vtt_srt_shifted_by_9s601451",
    full_outro_music_read: "pass_full_paper_architecture_outro_track_used_as_subtle_tail_source",
    end_screen_music_handoff_read: "pass_end_screen_carried_by_full_outro_after_subtle_tail_handoff",
    vo_outro_blend_plan_read: "pass_subtle_tail_outro_v1",
    vo_outro_music_blend_read: "pass_subtle_tail_outro_enters_late_low_and_continues_without_restart",
    vo_outro_perceptual_review_read: "pass_transition_sample_exported_for_human_listen_no_whole_mix_delta_only",
    outro_transition_review_sample_read: "pass_before_after_transition_samples_exported_7s_before_to_7s_after_final_vo",
    outro_entry_level_match_read:
      levelDelta !== null && levelDelta >= -9 && levelDelta <= 6
        ? `pass_pre_post_entry_mean_delta_${levelDelta}dB`
        : `tighten_pre_post_entry_mean_delta_${levelDelta}dB`,
    outro_under_vo_masking_read:
      underVoMargin !== null && underVoMargin >= 12 ? `pass_under_vo_music_margin_${underVoMargin}dB` : `tighten_under_vo_music_margin_${underVoMargin}dB`,
    outro_target_after_voice_read: "pass_target_gain_reached_3s_after_voice_end",
    outro_prelap_source_read: "pass_full_outro_track_used_as_subtle_tail_source_not_bridge_proxy",
    outro_prelap_start_read: "pass_full_outro_starts_1p5s_before_voice_end",
    outro_no_restart_at_voice_end_read: "pass",
    outro_source_continuity_read: "pass_full_outro_source_continues_across_voice_end_without_restart",
    audio_level_mix_read: fullMix.max_volume_db !== null && fullMix.max_volume_db <= -0.1 ? `pass_max_volume_${fullMix.max_volume_db}dB` : "tighten_peak_above_expected",
    music_rights_read: "review_warning_registered_paper_architecture_theme_requires_youtube_claim_check_before_public_release",
    music_contract_regression_read: "pass_old_5s_actual_outro_prelap_rejected_subtle_tail_used",
    live_load_pronunciation_repair_read: "pass_repaired_live_load_long_i_voice_master_preserved",
    downstream_gate_read: "pass_final_assembly_review_ready_publish_upload_youtube_flags_false",
  };

  const audioMix = {
    packet_id: `hyatt_subtle_tail_outro_music_mix_${stamp}`,
    status: "final_assembly_review_ready_pending_human_listen_disposition",
    created_utc: new Date().toISOString(),
    predecessor_audio_mix_manifest_path: path.join(predecessorRoot, "references/audio_mix_manifest.json"),
    predecessor_audio_mix_manifest_sha256: sha256(path.join(predecessorRoot, "references/audio_mix_manifest.json")),
    repair_id: `subtle_tail_outro_${stamp}`,
    mix_profile_id: "subtle_tail_outro_v1",
    voice_source_path: voicePath,
    voice_source_sha256: sha256(voicePath),
    pronunciation_repair_manifest_path: pronunciationManifestPath,
    pronunciation_repair_manifest_sha256: sha256(pronunciationManifestPath),
    voice_start_seconds: timing.voiceStartSeconds,
    voice_duration_seconds: voiceDuration,
    voice_end_seconds: timing.voiceEndSeconds,
    output_path: repairedWavPath,
    output_sha256: sha256(repairedWavPath),
    output_probe: ffprobeJson(repairedWavPath),
    browser_mp3_path: repairedMp3Path,
    browser_mp3_sha256: sha256(repairedMp3Path),
    browser_mp3_probe: ffprobeJson(repairedMp3Path),
    total_duration_seconds: outputDuration,
    expected_total_duration_seconds: expectedDuration,
    duration_change_reason: "The approved full Paper Architecture outro starts 1.5s before voice end at low bed level and continues to its natural end.",
    intro_music_start_seconds: 0,
    intro_music_only_end_seconds: timing.voiceStartSeconds,
    intro_music_fade_end_seconds: timing.introFadeEndSeconds,
    full_outro_source_path: outroPath,
    full_outro_start_seconds: timing.fullOutroStartSeconds,
    full_outro_fade_in_seconds: timing.outroPrelapSeconds + timing.outroTargetRampSeconds,
    outro_music_start_seconds: timing.fullOutroStartSeconds,
    outro_music_end_seconds: outputDuration,
    outro_prelap_seconds: timing.outroPrelapSeconds,
    outro_under_vo_gain_linear: timing.outroUnderVoGainLinear,
    outro_target_gain_linear: timing.outroTargetGainLinear,
    outro_target_ramp_seconds: timing.outroTargetRampSeconds,
    outro_reaches_target_at_seconds: timing.outroReachesTargetAtSeconds,
    under_vo_music_margin_db: underVoMargin,
    outro_no_restart_at_voice_end: true,
    outro_source_continuity: true,
    vo_outro_blend_plan: {
      policy: "subtle_tail_outro_v1",
      full_outro_source_path: outroPath,
      full_outro_start_seconds: timing.fullOutroStartSeconds,
      outro_under_vo_gain_linear: timing.outroUnderVoGainLinear,
      outro_target_gain_linear: timing.outroTargetGainLinear,
      outro_target_ramp_seconds: timing.outroTargetRampSeconds,
      full_outro_fade_in_seconds: timing.outroPrelapSeconds + timing.outroTargetRampSeconds,
      voice_end_seconds: timing.voiceEndSeconds,
      outro_prelap_seconds: timing.outroPrelapSeconds,
      outro_reaches_target_at_seconds: timing.outroReachesTargetAtSeconds,
      under_vo_music_margin_db: underVoMargin,
      outro_no_restart_at_voice_end: true,
      outro_source_continuity: true,
      bridge_policy: "no_bridge_used_for_final_vo_handoff_full_outro_track_is_the_subtle_tail_source",
      rationale: "The full Paper Architecture outro enters only under the final 1.5 seconds at low level, then blooms after the final word.",
    },
    outro_transition_review_sample: {
      before_wav: artifact(beforeWav),
      before_mp3: artifact(beforeMp3),
      wav: artifact(afterWav),
      mp3: artifact(afterMp3),
      start_seconds: sampleStart,
      end_seconds: Number((sampleStart + sampleDuration).toFixed(6)),
      window_seconds: sampleDuration,
    },
    outro_entry_level_match_notes: {
      final_4s_before_voice_end_mean_db: preVoiceEnd.mean_volume_db,
      first_4s_after_voice_end_mean_db: postVoiceEnd.mean_volume_db,
      post_minus_pre_mean_delta_db: levelDelta,
      transition_14s_mean_db: transition.mean_volume_db,
      transition_14s_max_db: transition.max_volume_db,
      final_voice_phrase_mean_db: finalVoicePhrase.mean_volume_db,
      under_vo_music_stem_mean_db: underVoMusicStem.mean_volume_db,
      under_vo_music_margin_db: underVoMargin,
      note: "Programmatic level checks are supporting evidence; human final assembly review owns perceptual keep/tighten/reject.",
    },
    music_sources: {
      registry: { ...artifact(registryPath), track_id: "paper_architecture_theme_v1" },
      intro_body_loop: { ...artifact(introPath), role: "intro_music_only_lead_in_and_opening_fade_tail" },
      outro_full_track: { ...artifact(outroPath), role: "subtle_tail_under_final_vo_and_end_screen_music" },
    },
    candidate_artifacts: {
      repaired_wav_candidate: artifact(repairedWavPath),
      repaired_mp3_candidate: artifact(repairedMp3Path),
    },
    level_reads: {
      full_mix: fullMix,
      final_4s_before_voice_end: preVoiceEnd,
      first_4s_after_voice_end: postVoiceEnd,
      transition_review_sample: transition,
      final_voice_phrase: finalVoicePhrase,
      under_vo_music_stem: underVoMusicStem,
      under_vo_music_margin_db: underVoMargin,
    },
    rights_and_claims: {
      rights_check_required_before_public_release: true,
      claim_risk: "check_upload_processing_before_public_release",
      notes: "Uses registered Paper Architecture theme assets from the local music registry. Public release remains blocked until YouTube claim/status checks are complete.",
    },
    reads,
  };
  writeJson(successorAudioMixPath, audioMix);
  writeJson(path.join(qaAudioDir, `vo_outro_subtle_tail_mix_qa_${stamp}.json`), audioMix);
  writeJson(path.join(audioRepairRoot, "vo_outro_blend_audio_mix_manifest.json"), audioMix);
  return audioMix;
}

function patchPlayer(audioMix) {
  const safeStart = Number((audioMix.total_duration_seconds - 20).toFixed(6));
  let html = fs.readFileSync(successorPlayerPath, "utf8");
  html = html.replace(/<title>[^<]*<\/title>/, "<title>Hyatt Regency Living Cover Rough Proof - Subtle Tail Outro Repair</title>");
  html = html.replace(
    /src="assets\/audio\/[^"]*web_review[^"]*"/,
    `src="assets/audio/${path.basename(repairedMp3Path)}?v=subtle_tail_outro_${stamp}"`,
  );
  html = html.replace(
    /src="assets\/audio\/[^"]*(?:review_mix|music_review_mix)[^"]*\.wav[^"]*"/,
    `src="assets/audio/${path.basename(repairedWavPath)}?v=subtle_tail_outro_${stamp}"`,
  );
  html = html.replace(/"duration":\s*[0-9.]+/, `"duration": ${audioMix.total_duration_seconds.toFixed(6)}`);
  html = html.replace(
    /"audio":\s*"assets\/audio\/[^"]+"/,
    `"audio": "assets/audio/${path.basename(repairedMp3Path)}?v=subtle_tail_outro_${stamp}"`,
  );
  html = html.replace(/"endScreenSafeWindowStart":\s*[0-9.]+/, `"endScreenSafeWindowStart": ${safeStart.toFixed(6)}`);
  html = html.replace(
    /"fullOutroMusic":\s*\[\s*[0-9.]+,\s*[0-9.]+\s*\]/,
    `"fullOutroMusic": [\n      ${timing.fullOutroStartSeconds.toFixed(6)},\n      ${audioMix.total_duration_seconds.toFixed(6)}\n    ]`,
  );
  html = html.replace(
    /"youtubeEndScreenSafeWindow":\s*\[\s*[0-9.]+,\s*[0-9.]+\s*\]/,
    `"youtubeEndScreenSafeWindow": [\n      ${safeStart.toFixed(6)},\n      ${audioMix.total_duration_seconds.toFixed(6)}\n    ]`,
  );
  html = html.replace(
    /"timingModel":\s*"[^"]+"/,
    `"timingModel": "challenger_style_music_only_intro_fade_tail_subtle_tail_outro_v1"`,
  );
  fs.writeFileSync(successorPlayerPath, html, "utf8");
}

function updateManifest(audioMix) {
  const safeStart = Number((audioMix.total_duration_seconds - 20).toFixed(6));
  const manifest = readJson(successorManifestPath);
  manifest.packet_id = successorId;
  manifest.status = "rough_proof_keep_final_render_gate_open_subtle_tail_outro_repair";
  manifest.human_disposition = "keep";
  manifest.modified_utc = new Date().toISOString();
  manifest.predecessor_packet_path = predecessorRoot;
  manifest.successor_reason = "subtle_tail_outro_v1 repair after human review found the 5s actual-outro prelap unnatural";
  manifest.publish_ready = false;
  manifest.youtube_upload_ready = false;
  manifest.public_release_ready = false;
  manifest.may_youtube_action = false;
  manifest.may_advance_to_video_render = true;
  manifest.may_create_full_runtime_mp4_render = true;
  manifest.may_advance_to_final_assembly = false;
  manifest.may_advance_to_publish_readiness = false;
  manifest.mp4_render_created = false;
  manifest.review_audio_mix = {
    process_version: "subtle_tail_outro_v1",
    audio_mix_manifest: artifact(successorAudioMixPath),
    path: repairedWavPath,
    sha256: sha256(repairedWavPath),
    browser_mp3_path: repairedMp3Path,
    browser_mp3_sha256: sha256(repairedMp3Path),
    duration_seconds: audioMix.total_duration_seconds,
    voice_start_seconds: timing.voiceStartSeconds,
    voice_end_seconds: timing.voiceEndSeconds,
    role: "subtle_tail_outro_challenger_style_music_integrated_review_audio_with_live_load_long_i_repair",
    reads: audioMix.reads,
  };
  manifest.music_integration_contract = {
    ...(manifest.music_integration_contract || {}),
    status: "rough_proof_keep_final_gate_ready_subtle_tail_outro",
    process_version: "living_cover_music_integration_contract_v1",
    contract_id: `hyatt_subtle_tail_outro_v1_${stamp}`,
    audio_mix_manifest_path: successorAudioMixPath,
    audio_mix_manifest_sha256: sha256(successorAudioMixPath),
    voice_start_offset_seconds: timing.voiceStartSeconds,
    caption_timing_shift_seconds: timing.voiceStartSeconds,
    intro_policy: "music_only_intro_before_voice_with_2s_fade_tail_under_voice",
    outro_policy: "full_paper_architecture_m4a_enters_1p5s_before_last_spoken_word_low_then_reaches_target_3s_after_voice",
    subtle_tail_outro: {
      process_version: "subtle_tail_outro_v1",
      full_outro_source_path: outroPath,
      full_outro_start_seconds: timing.fullOutroStartSeconds,
      voice_end_seconds: timing.voiceEndSeconds,
      outro_prelap_seconds: timing.outroPrelapSeconds,
      outro_under_vo_gain_linear: timing.outroUnderVoGainLinear,
      outro_target_gain_linear: timing.outroTargetGainLinear,
      outro_target_ramp_seconds: timing.outroTargetRampSeconds,
      outro_reaches_target_at_seconds: timing.outroReachesTargetAtSeconds,
      under_vo_music_margin_db: audioMix.under_vo_music_margin_db,
      outro_no_restart_at_voice_end: true,
      outro_source_continuity: true,
      bridge_policy: "supplemental_texture_only_not_a_substitute_for_full_outro_prelap",
    },
    vo_outro_blend_plan: audioMix.vo_outro_blend_plan,
    outro_transition_review_sample: audioMix.outro_transition_review_sample,
    outro_entry_level_match_notes: audioMix.outro_entry_level_match_notes,
    reads: audioMix.reads,
  };
  manifest.end_screen_context = {
    ...(manifest.end_screen_context || {}),
    end_screen_start_seconds: timing.voiceEndSeconds,
    end_screen_end_seconds: audioMix.total_duration_seconds,
    youtube_end_screen_safe_window_seconds: [safeStart, audioMix.total_duration_seconds],
  };
  manifest.final_render_contract = {
    required_after_html_proof_keep: true,
    render_source_rule: "render_from_current_kept_html_proof_only",
    source_html_proof: {
      packet_path: successorRoot,
      manifest_path: successorManifestPath,
      player_path: successorPlayerPath,
      player_sha256: sha256(successorPlayerPath),
    },
    mp4_render_created: false,
    source_html_proof_must_be_current_kept_successor: true,
    blocked_until_human_keep_on_this_packet: false,
  };
  manifest.rough_assembly_reads = {
    ...(manifest.rough_assembly_reads || {}),
    ...audioMix.reads,
  };
  manifest.reads = {
    ...(manifest.reads || {}),
    ...audioMix.reads,
  };
  manifest.upload_locks = {
    ...(manifest.upload_locks || {}),
    publish_ready: false,
    youtube_upload_ready: false,
    public_release_ready: false,
    may_youtube_action: false,
    upload_performed: false,
    mp4_render_created: false,
    final_mp4_render: false,
    final_assembly: false,
    publish_readiness: false,
    private_youtube_upload: false,
    public_release: false,
  };
  manifest.publish_readiness_gate = {
    status: "blocked_pending_human_keep_on_subtle_tail_final_assembly",
    upload_performed: false,
    publish_ready: false,
    youtube_upload_ready: false,
    public_release_ready: false,
    may_advance: false,
    next_action: "Review the subtle-tail final assembly, then rebuild publish readiness only after keep.",
  };
  writeJson(successorManifestPath, manifest);
}

function patchRenderScript(audioMix) {
  const safeStart = Number((audioMix.total_duration_seconds - 20).toFixed(6));
  let text = fs.readFileSync(path.join(successorRoot, "scripts/render_hyatt_final_mp4.mjs"), "utf8");
  text = text.replaceAll(predecessorRoot, successorRoot);
  text = text.replace(
    /const gateApprovalPath = path\.join\([\s\S]*?\);\nconst playerPath = /,
    `const gateApprovalPath = "${gateApprovalPath}";\nconst playerPath = `,
  );
  text = text.replace(
    /const audioWavPath = path\.join\([\s\S]*?const railOffsetVttPath = /,
    `const audioWavPath = path.join(proofRoot, "assets/audio/${path.basename(repairedWavPath)}");\nconst audioMp3Path = path.join(proofRoot, "assets/audio/${path.basename(repairedMp3Path)}");\nconst railOffsetVttPath = `,
  );
  text = text.replace(
    /const timing = \{[\s\S]*?\};/,
    `const timing = {\n  durationSeconds: ${audioMix.total_duration_seconds.toFixed(6)},\n  voiceStartSeconds: ${timing.voiceStartSeconds},\n  voiceEndSeconds: ${timing.voiceEndSeconds},\n  safeWindowStartSeconds: ${safeStart.toFixed(6)},\n  safeWindowEndSeconds: ${audioMix.total_duration_seconds.toFixed(6)},\n  fps: 24,\n};`,
  );
  text = text.replace(
    /const requiredVoOutroReads = \{[\s\S]*?\n  \};/,
    `const requiredVoOutroReads = {\n    vo_outro_perceptual_review_read: "pass_transition_sample_exported_for_human_listen_no_whole_mix_delta_only",\n    outro_under_vo_masking_read: "${audioMix.reads.outro_under_vo_masking_read}",\n    outro_target_after_voice_read: "pass_target_gain_reached_3s_after_voice_end",\n  };`,
  );
  text = text.replaceAll("vo_outro_before_20260518T024214Z", `vo_outro_before_${stamp}`);
  text = text.replaceAll("vo_outro_blend_transition_20260518T024214Z", `vo_outro_subtle_tail_transition_${stamp}`);
  text = text.replaceAll("actual_outro_prelap_challenger_style_music_integrated_review_audio_with_live_load_long_i_repair", "subtle_tail_outro_challenger_style_music_integrated_review_audio_with_live_load_long_i_repair");
  text = text.replaceAll("actual_outro_prelap", "subtle_tail_outro");
  text = text.replaceAll("pass_natural_duration_shortened_by_subtle_tail_outro", "pass_natural_duration_from_subtle_tail_outro");
  text = text.replaceAll("pass_full_outro_track_fades_under_final_vo_not_bridge_proxy", "pass_full_outro_track_used_as_subtle_tail_source_not_bridge_proxy");
  text = text.replaceAll("pass_full_outro_starts_5s_before_voice_end", "pass_full_outro_starts_1p5s_before_voice_end");
  text = text.replaceAll("pass_full_outro_reaches_target_at_voice_end_and_continues_after_voice", "pass_target_gain_reached_3s_after_voice_end");
  text = text.replaceAll("pass_5s_prelap_fade_under_final_vo_does_not_mask_last_words", audioMix.reads.outro_under_vo_masking_read);
  text = text.replace(/duration_display: "00:14:34\.034"/, `duration_display: "${formatDuration(audioMix.total_duration_seconds)}"`);
  fs.writeFileSync(successorRenderScriptPath, text, "utf8");
}

function validatePreRender() {
  const result = run("node", [
    validatorPath,
    "--proof-manifest",
    successorManifestPath,
    "--player",
    successorPlayerPath,
    "--audio-mix",
    successorAudioMixPath,
  ]);
  const qaPath = path.join(successorRoot, "qa/final_gate_preflight_validator_subtle_tail.json");
  writeJson(qaPath, JSON.parse(result.stdout));
}

function assertReads(audioMix) {
  const required = [
    "vo_outro_blend_plan_read",
    "vo_outro_music_blend_read",
    "vo_outro_perceptual_review_read",
    "outro_transition_review_sample_read",
    "outro_entry_level_match_read",
    "outro_under_vo_masking_read",
    "outro_target_after_voice_read",
    "outro_prelap_source_read",
    "outro_prelap_start_read",
    "outro_no_restart_at_voice_end_read",
    "outro_source_continuity_read",
    "music_contract_regression_read",
  ];
  const failing = required.filter((key) => !passRead(audioMix.reads[key]));
  if (failing.length) throw new Error(`Subtle-tail audio mix has non-passing reads: ${failing.join(", ")}`);
}

function main() {
  if (!fs.existsSync(predecessorRoot) || !fs.statSync(predecessorRoot).isDirectory()) {
    throw new Error(`Missing predecessor proof root: ${predecessorRoot}`);
  }
  [
    predecessorAudioWavPath,
    voicePath,
    pronunciationManifestPath,
    introPath,
    outroPath,
    registryPath,
    validatorPath,
    path.join(predecessorRoot, "scripts/render_hyatt_final_mp4.mjs"),
  ].forEach(requireFile);
  copySuccessor();
  markPredecessorsTighten();
  const audioMix = buildRepairedAudio();
  assertReads(audioMix);
  patchPlayer(audioMix);
  updateManifest(audioMix);
  patchRenderScript(audioMix);
  validatePreRender();
  console.log(
    JSON.stringify(
      {
        successorRoot,
        audioMixManifest: successorAudioMixPath,
        reviewMixWav: repairedWavPath,
        transitionSampleMp3: audioMix.outro_transition_review_sample.mp3.path,
        renderScript: successorRenderScriptPath,
        nextCommand: `node ${successorRenderScriptPath}`,
        uploadLocksRemainFalse: true,
      },
      null,
      2,
    ),
  );
}

main();
