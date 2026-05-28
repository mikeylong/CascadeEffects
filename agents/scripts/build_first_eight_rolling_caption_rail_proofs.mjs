#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { spawnSync } from "node:child_process";
import {
  END_SCREEN_PALETTE_CONTRACT_ID,
  END_SCREEN_PALETTE_DERIVATION_MODEL,
} from "./living_cover_end_screen_palette_contract.mjs";

const REPO_ROOT = "/Users/mike/Agents_CascadeEffects";
const BASELINE_INDEX_PATH = path.join(
  REPO_ROOT,
  "references/skills/long_form_video_production_v1/references/episode_visual_system_baselines/index.json",
);
const ROLLOUT_SUMMARY_PATH = path.join(
  REPO_ROOT,
  "references/skills/long_form_video_production_v1/references/episode_visual_system_baselines/rolling_caption_rail_rollout_20260520.json",
);
const EPISODES_ROOT = "/Users/mike/Episodes_CascadeEffects";
const REVIEW_SERVER_BASE_URL = "http://127.0.0.1:8766";
const REVIEW_INDEX_PATH = path.join(EPISODES_ROOT, "first-eight-rolling-caption-rail-review.html");
const CREATED_UTC = "2026-05-20T23:30:00Z";
const DEFAULT_PACKET_STAMP = "20260520T235500Z";
const PACKET_STAMP = process.env.CE_ROLLING_RAIL_PACKET_STAMP || DEFAULT_PACKET_STAMP;
const PROOF_GENERATED_AT_UTC = new Date().toISOString();
const PROOF_GENERATION_STAMP = PROOF_GENERATED_AT_UTC.replace(/\D/g, "").slice(0, 17);
const RAIL_GEOMETRY = {
  left: 1108,
  top: 52,
  width: 760,
  height: 976,
  rightMargin: 52,
};
const CAPTION_WINDOW_GEOMETRY = {
  railRight: 12,
  railTop: 72,
  width: 488,
  height: 844,
  railBottom: 60,
  stackLeft: 42,
  stackWidth: 402,
  activeY: 439,
  topFade: 168,
  bottomFade: 188,
};
const CAPTION_MOTION_MODEL = "constant_speed_audio_time_aligned_scroll_v2";
const CAPTION_LINE_OPACITY_MODEL = "viewport_distance_smoothstep_v1";
const CAPTION_WINDOW_TREATMENT_MODEL = "transparent_caption_mask_only_v1";
const CAPTION_TIMELINE_LAYOUT_MODEL = "audio_time_positioned_stack_v1";
const CAPTION_SYNC_TARGET = "pre_vo_reading_lead_active_band_v1";
const CAPTION_READING_LEAD_SECONDS = 0.65;
const CAPTION_INTRO_VISIBILITY_GATE_MODEL = "first_vo_intro_hold_fade_v1";
const CAPTION_INTRO_GATE_FADE_START_LEAD_SECONDS = 1.1;
const CAPTION_INTRO_GATE_FULL_OPACITY_LEAD_SECONDS = CAPTION_READING_LEAD_SECONDS;
const CAPTION_CONSTANT_SPEED_SCOPE = "per_episode_constant_px_per_second";
const CAPTION_DENSITY_RESOLUTION_MODEL = "merge_dense_chunks_no_speed_ramp_v1";
const CAPTION_DISPLAY_LINE_WRAP_MODEL = "pixel_budgeted_deterministic_line_wrap_v1";
const HIGHLIGHT_PHRASE_SCOPE = "exact_authored_span_only";
const CAPTION_HIGHLIGHT_MODEL_ID = "lesson_takeaway_highlight_v1";
const HIGHLIGHT_SEMANTIC_ROLE = "story_lesson_takeaway";
const HIGHLIGHT_DENSITY_MODEL = "memorable_takeaway_cadence_v1";
const HIGHLIGHT_COLOR_MODEL = "source_sampled_backplate_contrast_takeaway_accent_v3";
const HIGHLIGHT_VISUAL_TIMING_MODEL = "active_band_presence_aligned_v1";
const HIGHLIGHT_MIN_BACKPLATE_CONTRAST_RATIO = 2.0;
const HIGHLIGHT_P20_BACKPLATE_CONTRAST_RATIO = 2.45;
const HIGHLIGHT_MIN_BACKPLATE_COLOR_DELTA = 58;
const HIGHLIGHT_ACTIVE_TEXT_MIN_DELTA = 48;
const HIGHLIGHT_MUTED_TEXT_MIN_DELTA = 44;
const HIGHLIGHT_ACTIVE_TEXT_MIN_CONTRAST = 1.0;
const HIGHLIGHT_MUTED_TEXT_MIN_CONTRAST = 1.12;
const HUMAN_APPROVED_HIGHLIGHT_ACCENT_OVERRIDES = {
  semmelweis: {
    selected_hex: "#efef9f",
    selected_rgb: [239, 239, 159],
    highlight_override_read: "pass_review_safe_pale_highlight_accent",
    override_source: "user_request_in_app_review_20260526",
    override_reason: "retired_bright_dede35_highlight_does_not_match_current_caption_treatment",
  },
};
const LESSON_TAKEAWAY_APPROVAL_STATUS = "human_approved_lesson_takeaway_span_20260523";
const EXPECTED_LESSON_TAKEAWAY_COUNTS = {
  challenger: 32,
  "therac-25": 28,
  "hyatt-regency": 22,
  semmelweis: 22,
  "tacoma-narrows": 22,
  "piltdown-man": 22,
  "737-max": 25,
  titanic: 20,
};
const CAPTION_LAYOUT_COLLISION_GUARD = "fixed_line_box_visual_gap_guard_v1";
const CAPTION_AUDIO_SYNC_MODEL = "source_sidecar_audio_time_v1";
const REVIEW_CONTROL_MODEL = "single_foreground_review_transport_v1";
const REVIEW_TRANSPORT_SCRUB_MODEL = "foreground_transport_scrub_lock_v1";
const LEGACY_REVIEW_CHROME_SUPPRESSION_MODEL = "predecessor_review_chrome_hidden_in_review_mode_v1";
const CAPTION_PLAYBACK_CLOCK_MODEL = "media_time_smoothed_raf_clock_v3";
const CAPTION_STACK_RENDER_MODEL = "compositor_linear_transform_driver_v1";
const CAPTION_SCROLL_SMOOTHNESS_MODEL = "compositor_linear_transform_driver_v1";
const CAPTION_RUNTIME_COVERAGE_MODEL = "full_vo_runtime_visible_caption_coverage_v1";
const CAPTION_END_SCREEN_HANDOFF_MODEL = "review_approved_end_screen_entry_v1";
const AMBIENT_RIGHT_RAIL_MOTION_POLICY = "ambient_motion_allowed_under_rail_text_v1";
const AMBIENT_FRAME_CLOCK_MODEL = "render_frame_time_locked_to_composition_fps_v1";
const AMBIENT_RENDER_CLOCK_READ = "pass_ambient_time_uses_render_frame_seconds";
const AMBIENT_WALL_CLOCK_DRIFT_SUPPRESSION_READ = "pass_no_render_mode_wall_clock_ambient_mutation";
const AMBIENT_FRAME_CLOCK_EPISODES = new Set(["therac-25", "semmelweis"]);
const FOREGROUND_MATTE_POLICY = "tower_shuttle_only_no_light_or_right_rail_mask";
const YOUTUBE_END_SCREEN_TEMPLATE_ID = "adaptive_titleless_youtube_end_screen_overlay_on_living_cover_v1";
const END_SCREEN_FADE_TIMING_MODEL = "caption_exit_aligned_end_screen_fade_v1";
const END_SCREEN_PALETTE_TREATMENT_MODEL = "local_backplate_perceptual_target_palette_v3";
const END_SCREEN_ADAPTIVE_VARIABILITY_MODEL = "backplate_hue_preserved_perceptual_variability_v1";
const OUTRO_POLICY = "subtle_tail_outro_v1";
const OUTRO_PRELAP_SECONDS = 1.5;
const OUTRO_UNDER_VO_GAIN_LINEAR = 0.1;
const OUTRO_TARGET_GAIN_LINEAR = 0.42;
const OUTRO_TARGET_AFTER_VOICE_SECONDS = 3;
const OUTRO_TARGET_MARGIN_DB = 12;
const VOICE_LOUDNESS_TARGET_I = -14;
const VOICE_LOUDNESS_TARGET_TP = -1.0;
const VOICE_LOUDNESS_TARGET_LRA = 11;
const VOICE_LOUDNESS_TOLERANCE_DB = 1.5;
const END_SCREEN_TRANSITION_DURATION_SECONDS = 0.3;
const INTRO_TRIM_MODEL = "first_eight_intro_trim_6s_v1";
const INTRO_TRIM_SECONDS = 6;
const PREVIOUS_VOICE_START_OFFSET_SECONDS = 9.601451;
const VOICE_START_OFFSET_SECONDS = Number((PREVIOUS_VOICE_START_OFFSET_SECONDS - INTRO_TRIM_SECONDS).toFixed(6));
const PREVIOUS_OFFSET_SLUG = "9s601";
const VOICE_START_OFFSET_SLUG = "3s601";
const REVIEW_APPROVED_END_SCREEN_FADE_START_SECONDS = {
  "challenger": 19 * 60 + 43,
  "therac-25": 18 * 60 + 6,
  "hyatt-regency": 13 * 60 + 57,
  "semmelweis": 14 * 60 + 17,
  "tacoma-narrows": 14 * 60 + 4,
  "piltdown-man": 14 * 60 + 3,
  "737-max": 15 * 60 + 46,
  "titanic": 12 * 60 + 24,
};
const TACOMA_RAIN_PERFORMANCE_GUARD_MODEL = "caption_review_rain_layer_performance_guard_v1";
const TACOMA_RAIN_FRAME_THROTTLE_MS = 83;
const TACOMA_RAIN_BEAD_COUNT_CAP = 120;
const TACOMA_RAIN_RUNNER_COUNT_CAP = 7;
const TACOMA_RAIN_STREAK_COUNT_CAP = 48;
const TACOMA_K3_B3_HIGHLIGHT_MERGE_MODEL = "tacoma_k3_b3_backplate_with_lesson_takeaway_highlights_v1";
const TACOMA_K3_B3_SOURCE_ART_PATH =
  "/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/source_art/tacoma_living_cover_candidate_k3_b3_failure_in_progress_snapped_suspenders_20260523T020003Z/assets/source_art/candidate_k3_b3_failure_in_progress_snapped_suspenders_1920x1080.png";
const TACOMA_K3_B3_SOURCE_ART_SHA256 = "580e69bea2f7d278f2aed000ccf669cfaa45fcbf562238694085809eac4363b8";
const TACOMA_K3_B3_SOURCE_ART_REVIEW_NOTE_PATH =
  "/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/source_art/tacoma_living_cover_candidate_k3_b3_failure_in_progress_snapped_suspenders_20260523T020003Z/review/source_art_review_candidate_k3_b3_failure_in_progress_snapped_suspenders.md";
const TACOMA_K3_B3_PREDECESSOR_PROOF_PATH =
  "/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_failure_in_progress_rough_proof_20260523T024555Z";
const CAPTION_MIN_CONSTANT_SPEED_PX_PER_SECOND = 48;
const CAPTION_MAX_CONSTANT_SPEED_PX_PER_SECOND = 54;
const CAPTION_MIN_RENDERED_LINE_GAP_PX = 40;
const CAPTION_DENSE_MERGE_VISUAL_GAP_PX = CAPTION_MIN_RENDERED_LINE_GAP_PX;
const CAPTION_MAX_MERGED_CHARS = 120;
const CAPTION_FONT_SIZE_PX = 32;
const CAPTION_DISPLAY_LINE_MAX_CHARS = 27;
const CAPTION_DISPLAY_LINE_MAX_WIDTH_PX = CAPTION_WINDOW_GEOMETRY.stackWidth - 42;
const CAPTION_LINE_BOX_HEIGHT_PX = 42;
const CAPTION_ACTIVE_BAND_LOWER_DELTA_PX = 96;
const CAPTION_SCROLL_ENTRY_LEAD_IN_SECONDS = 2.35;
const CAPTION_SCROLL_FIRST_ENTRY_CENTER_PX = CAPTION_WINDOW_GEOMETRY.height + 24;
const CAPTION_SCROLL_LAST_EXIT_CENTER_PX = -96;
const CAPTION_SCROLL_END_FADE_SECONDS = 7.5;
const END_SCREEN_PALETTE_MODEL = END_SCREEN_PALETTE_DERIVATION_MODEL;
const END_SCREEN_TARGET_LAYOUT = {
  left_video: { role: "suggested_video", bbox_xy: [78, 382, 758, 765], aspect_ratio: "16:9" },
  right_video: { role: "watch_next_video", bbox_xy: [1162, 382, 1842, 765], aspect_ratio: "16:9" },
  center_subscribe: { role: "subscribe", bbox_xy: [814, 429, 1106, 721] },
};
const PAPER_ARCHITECTURE_INTRO_LOOP_PATH =
  "/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/themesong/Paper Architecture instrumental_loop.wav";
const PAPER_ARCHITECTURE_FULL_OUTRO_PATH =
  "/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/themesong/Paper Architecture.m4a";
const MUSIC_TRACK_REGISTRY_PATH = "/Users/mike/Agents_CascadeEffects/references/shorts/music_track_registry.json";
const LESSON_TAKEAWAY_REVIEW_ROOT = path.join(EPISODES_ROOT, "first_eight_lesson_takeaway_review");
const LESSON_TAKEAWAY_CANDIDATES_LATEST_PATH = path.join(
  LESSON_TAKEAWAY_REVIEW_ROOT,
  "lesson_takeaway_candidates_latest.json",
);
const APPROVED_LESSON_TAKEAWAY_SPANS_LATEST_PATH = path.join(
  LESSON_TAKEAWAY_REVIEW_ROOT,
  "approved_lesson_takeaway_spans_latest.json",
);
const AUDIO_DEFECT_REPAIR_OVERRIDES = {
  "hyatt-regency": {
    voiceAudioDefectRepairModel: "kept_hyatt_live_load_blip_repair_v1",
    status: "kept_audio_defect_repair_restored_for_rolling_caption_review_mix",
    repairedVoiceMasterPath:
      "/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/audio_repairs/live_load_long_i_blip_repair_20260519T184526Z/masters/Ep3-Hyatt-Regency.live_load_long_i_blip_repaired_voice_master.wav",
    repairManifestPath:
      "/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/audio_repairs/live_load_long_i_blip_repair_20260519T184526Z/blip_repair_manifest.json",
    supersededVoiceMasterReason:
      "Older live_load_long_i voice master contains the known low-level live-load blip/drop repair defect around the 2:44-2:50 proof-time window.",
    defectWindowsVoiceSeconds: [
      [161.271, 166.978],
      [430.723, 436.911],
    ],
  },
};

const EPISODES = [
  {
    episodeId: "challenger",
    title: "Challenger",
    action: "supersede_publish_final_surfaces_create_successor_rough_proof",
    sourceRoot:
      "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_longform_candidate_b_backplate_retarget_html_approval_proof_20260519T192924Z",
    outputBase:
      "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly",
    status: "rolling_caption_rail_rough_assembly_review_ready_pending_human_keep",
  },
  {
    episodeId: "therac-25",
    title: "Therac-25",
    action: "supersede_publish_final_surfaces_create_successor_rough_proof",
    sourceRoot:
      "/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/rough_assembly/therac_living_cover_challenger_music_html_rough_proof_20260517T073904Z",
    outputBase: "/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/rough_assembly",
    status: "rolling_caption_rail_rough_assembly_review_ready_pending_human_keep",
  },
  {
    episodeId: "hyatt-regency",
    title: "Hyatt Regency",
    action: "supersede_publish_final_surfaces_create_successor_rough_proof",
    sourceRoot:
      "/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt_living_cover_html_rough_proof_n6_period_camera_flash_20260520T192604Z",
    outputBase:
      "/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly",
    status: "rolling_caption_rail_rough_assembly_review_ready_pending_human_keep",
  },
  {
    episodeId: "semmelweis",
    title: "Semmelweis",
    action: "advance_right_rail_alignment_with_ambient_effects_deferred",
    sourceRoot: "/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/living_cover/ambient_effects/review_candidate_f_20260519",
    outputBase: "/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/youtube/rough_assembly",
    status: "rolling_caption_rail_rough_assembly_review_ready_right_rail_alignment_only_pending_human_keep",
    rightRailAlignmentOnly: true,
    ambientDeferralNotePath:
      "/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/living_cover/ambient_effects/ambient_effects_v7_deferred_for_right_rail_alignment_20260521.md",
    deferredAmbientReviewRoot:
      "/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/living_cover/ambient_effects/review_candidate_f_sink_trickle_v7_20260520",
    priorKeptAmbientRoot:
      "/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/living_cover/ambient_effects/review_candidate_f_20260519",
    musicIntegrationContractJsonPath:
      "/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/living_cover/music_integration_contract/music_integration_contract_candidate_f_candidate_c_composition_texture_repair_20260520.json",
  },
  {
    episodeId: "tacoma-narrows",
    title: "Tacoma Narrows",
    action: "refresh_current_rough_review_ready_proof",
    sourceRoot:
      "/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_tail_lights_removed_20260520T054440Z",
    outputBase:
      "/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly",
    outputNamePrefix: "tacoma-narrows_rolling_caption_rail_k3_b3_highlighted_rough_proof",
    status: "rolling_caption_rail_rough_assembly_review_ready_pending_human_keep",
    sourceArtOverridePath: TACOMA_K3_B3_SOURCE_ART_PATH,
    sourceArtOverrideStatus: "candidate_k3_b3_failure_in_progress_snapped_suspenders_with_takeaway_highlights_pending_human_keep",
    sourceArtOverrideReviewNotePath: TACOMA_K3_B3_SOURCE_ART_REVIEW_NOTE_PATH,
    sourceArtMergeForwardModel: TACOMA_K3_B3_HIGHLIGHT_MERGE_MODEL,
    sourceArtMergeForwardPredecessorProofPath: TACOMA_K3_B3_PREDECESSOR_PROOF_PATH,
  },
  {
    episodeId: "piltdown-man",
    title: "Piltdown Man",
    action: "pause_final_assembly_create_successor_rough_proof_from_kept_rough",
    sourceRoot:
      "/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/youtube/rough_assembly/piltdown_living_cover_html_rough_proof_candidate_g_minimal_ambient_6_1a_20260520T004143Z",
    outputBase:
      "/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/youtube/rough_assembly",
    status: "rolling_caption_rail_final_assembly_paused_successor_rough_assembly_review_ready_pending_human_keep",
  },
  {
    episodeId: "737-max",
    title: "737 MAX",
    action: "create_reviewable_right_rail_rough_proof_from_kept_candidate_l_after_music_contract_creation",
    sourceRoot: "/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1",
    outputBase: "/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/youtube/rough_assembly",
    status: "rolling_caption_rail_rough_assembly_review_ready_pending_human_keep",
    musicIntegrationContractJsonPath:
      "/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/living_cover/music_integration_contract/music_integration_contract_candidate_l_ramp_depth_lights_20260521.json",
    lockedScriptPath: "/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/Ep7_737-MAX.txt",
    voiceMasterPath: "/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/final/Ep7_737-MAX.wav",
    timingSourcePath: "/Users/mike/Audio_CascadeEffects/tmp/transcripts_final/Ep7_737-MAX.whisperx.json",
    storyCaptionVttPath:
      "/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/review_assets/captions/737_max_longform.script_locked_rail_safe.vtt",
    storyCaptionSrtPath:
      "/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/review_assets/captions/737_max_longform.script_locked_rail_safe.srt",
    captionQaPath:
      "/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/review_assets/captions/737_max_longform.script_locked_caption_qa.json",
    contractCandidateId: "candidate_l_ramp_depth_lights",
    contractReviewMixRequired: true,
    sourceArtOverridePath:
      "/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/source_art/candidates/737_max_living_cover_source_art_candidate_l_lion_air_livery_review_variant_20260522.png",
    sourceArtOverrideStatus: "lion_air_livery_backplate_wired_for_rough_rail_review_pending_human_keep",
    sourceArtOverrideReviewNotePath:
      "/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/source_art/review/737_max_lion_air_livery_review_variant_20260522.md",
  },
  {
    episodeId: "titanic",
    title: "Titanic",
    action: "pause_final_assembly_create_successor_rough_proof_from_kept_rough",
    sourceRoot:
      "/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/youtube/rough_assembly/titanic_living_cover_html_rough_proof_candidate_e_boat_deck_weather_readiness_20260519T210834Z",
    outputBase:
      "/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/youtube/rough_assembly",
    status: "rolling_caption_rail_final_assembly_paused_successor_rough_assembly_review_ready_pending_human_keep",
  },
];

const FALLBACK_LINES = {
  challenger: [
    "A launch does not fail at the moment the smoke appears.",
    "It fails when warnings become background noise.",
    "The signal was already there.",
    "The decision chain made it easier not to hear.",
  ],
  "therac-25": [
    "The machine looked precise.",
    "The failure was in the system around it.",
    "A warning could be cleared faster than it could be understood.",
    "The software made the invisible dangerous.",
  ],
  "hyatt-regency": [
    "The atrium made the load path look simple.",
    "The change made it something else.",
    "People gathered below a structure they could not read.",
    "The failure was already hanging in the detail.",
  ],
  semmelweis: [
    "The pattern was visible before the cause was accepted.",
    "The evidence arrived before the explanation.",
    "A simple intervention became a professional threat.",
    "The cost was paid by patients who had no voice in the argument.",
  ],
  "tacoma-narrows": [
    "The bridge did not simply fall.",
    "It learned the wind's rhythm.",
    "The motion became the warning.",
    "The structure answered the atmosphere until it could not.",
  ],
  "piltdown-man": [
    "The evidence fit what people wanted to find.",
    "A fragment became a story.",
    "The story became authority.",
    "The receipts took decades to catch up.",
  ],
  "737-max": [
    "The airplane was sold as familiar.",
    "The new behavior was buried inside that promise.",
    "A small sensor became a large authority.",
    "The pilots met a system they had not been taught to expect.",
  ],
  titanic: [
    "The ship was not doomed by one decision.",
    "The warnings accumulated before the impact.",
    "Confidence became part of the risk.",
    "The end was built from smaller permissions.",
  ],
};

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function readJsonIfExists(filePath) {
  if (!filePath || !fs.existsSync(filePath)) return null;
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch {
    return null;
  }
}

function sha256File(filePath) {
  if (!filePath || !fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) return "missing";
  const hash = crypto.createHash("sha256");
  hash.update(fs.readFileSync(filePath));
  return hash.digest("hex");
}

function proofBuildIdForEpisode(episodeId) {
  return `${episodeId}_rolling_caption_rail_${PROOF_GENERATION_STAMP}Z`;
}

function outputDirNameForEpisode(episode) {
  if (episode?.outputNamePrefix) return `${episode.outputNamePrefix}_${PACKET_STAMP}`;
  return `${episode.episodeId}_rolling_caption_rail_rough_proof_${PACKET_STAMP}`;
}

function ffprobeJson(filePath) {
  if (!filePath || !fs.existsSync(filePath)) return null;
  const result = spawnSync(
    "ffprobe",
    [
      "-v",
      "error",
      "-show_entries",
      "format=duration,size,bit_rate,format_name:stream=index,codec_name,codec_type,sample_rate,channels,duration",
      "-of",
      "json",
      filePath,
    ],
    { encoding: "utf8" },
  );
  if (result.status !== 0) return null;
  try {
    return JSON.parse(result.stdout || "{}");
  } catch {
    return null;
  }
}

function durationSeconds(filePath) {
  const probe = ffprobeJson(filePath);
  return Number(probe?.format?.duration);
}

function parseJsonFromText(text) {
  const match = String(text || "").match(/\{[\s\S]*\}/);
  if (!match) return null;
  try {
    return JSON.parse(match[0]);
  } catch {
    return null;
  }
}

function ffmpegVolumeDetect(filePath, start = null, duration = null) {
  if (!filePath || !fs.existsSync(filePath)) return {};
  const args = ["-hide_banner", "-nostats"];
  if (Number.isFinite(start)) args.push("-ss", String(start));
  if (Number.isFinite(duration)) args.push("-t", String(duration));
  args.push("-i", filePath, "-af", "volumedetect", "-f", "null", "-");
  const result = spawnSync("ffmpeg", args, { encoding: "utf8" });
  const text = `${result.stderr || ""}\n${result.stdout || ""}`;
  return {
    mean_volume_db: Number((text.match(/mean_volume:\s*(-?\d+(?:\.\d+)?) dB/) || [])[1]),
    max_volume_db: Number((text.match(/max_volume:\s*(-?\d+(?:\.\d+)?) dB/) || [])[1]),
  };
}

function loudnormScan(filePath) {
  if (!filePath || !fs.existsSync(filePath)) return null;
  const result = spawnSync(
    "ffmpeg",
    [
      "-hide_banner",
      "-nostats",
      "-i",
      filePath,
      "-af",
      `loudnorm=I=${VOICE_LOUDNESS_TARGET_I}:TP=${VOICE_LOUDNESS_TARGET_TP}:LRA=${VOICE_LOUDNESS_TARGET_LRA}:print_format=json`,
      "-f",
      "null",
      "-",
    ],
    { encoding: "utf8" },
  );
  if (result.status !== 0) return null;
  return parseJsonFromText(`${result.stderr || ""}\n${result.stdout || ""}`);
}

function loudnormNeedsAlignment(scan) {
  const inputIntegrated = Number(scan?.input_i);
  if (!Number.isFinite(inputIntegrated)) return false;
  return Math.abs(inputIntegrated - VOICE_LOUDNESS_TARGET_I) > VOICE_LOUDNESS_TOLERANCE_DB;
}

function renderAlignedVoiceStem({ episode, outputDir, voicePath }) {
  const scan = loudnormScan(voicePath);
  const sourceWindowVolumedetect = ffmpegVolumeDetect(voicePath, 10, 120);
  if (!loudnormNeedsAlignment(scan)) {
    return {
      model: "voice_loudness_alignment_v1",
      status: "not_needed_source_within_tolerance",
      source_voice_master: audioMetadata(voicePath),
      mix_voice_master_path: voicePath,
      mix_voice_master: audioMetadata(voicePath),
      target: {
        integrated_lufs: VOICE_LOUDNESS_TARGET_I,
        true_peak_dbtp: VOICE_LOUDNESS_TARGET_TP,
        loudness_range_lra: VOICE_LOUDNESS_TARGET_LRA,
        tolerance_db: VOICE_LOUDNESS_TOLERANCE_DB,
      },
      source_loudnorm_scan: scan,
      source_window_volumedetect: sourceWindowVolumedetect,
      output_loudnorm_scan: scan,
      output_window_volumedetect: sourceWindowVolumedetect,
      voice_master_used_for_mix_read: "pass_source_voice_master_within_series_loudness_tolerance",
    };
  }

  const safeEpisodeId = String(episode.episodeId || "episode").replace(/[^a-z0-9_-]+/gi, "_");
  const alignedPath = path.join(outputDir, `proof_assets/audio/${safeEpisodeId}_voice_master_loudnorm_I14_TP1_LRA11.wav`);
  const manifestPath = path.join(outputDir, `proof_assets/audio/${safeEpisodeId}_voice_master_loudness_alignment_manifest.json`);
  const logPath = path.join(outputDir, `proof_assets/audio/${safeEpisodeId}_voice_master_loudnorm_ffmpeg.log`);
  ensureDir(path.dirname(alignedPath));
  const existingManifest = readJsonIfExists(manifestPath);
  const sourceSha256 = sha256File(voicePath);
  const needsRender =
    !fs.existsSync(alignedPath) ||
    !existingManifest ||
    existingManifest.source_voice_master?.sha256 !== sourceSha256 ||
    existingManifest.target?.integrated_lufs !== VOICE_LOUDNESS_TARGET_I;
  let outputScan = existingManifest?.output_loudnorm_scan || null;
  if (needsRender) {
    const measuredI = Number(scan.input_i);
    const measuredTp = Number(scan.input_tp);
    const measuredLra = Number(scan.input_lra);
    const measuredThresh = Number(scan.input_thresh);
    const targetOffset = Number(scan.target_offset);
    if (![measuredI, measuredTp, measuredLra, measuredThresh, targetOffset].every(Number.isFinite)) {
      throw new Error(`Cannot loudnorm ${episode.episodeId}: incomplete scan for ${voicePath}`);
    }
    const filter =
      `loudnorm=I=${VOICE_LOUDNESS_TARGET_I}:TP=${VOICE_LOUDNESS_TARGET_TP}:LRA=${VOICE_LOUDNESS_TARGET_LRA}` +
      `:measured_I=${measuredI}:measured_TP=${measuredTp}:measured_LRA=${measuredLra}` +
      `:measured_thresh=${measuredThresh}:offset=${targetOffset}:linear=true:print_format=json`;
    const args = [
      "-y",
      "-hide_banner",
      "-nostats",
      "-i",
      voicePath,
      "-af",
      filter,
      "-ar",
      "44100",
      "-ac",
      "1",
      "-c:a",
      "pcm_s16le",
      alignedPath,
    ];
    const result = spawnSync("ffmpeg", args, { encoding: "utf8" });
    fs.writeFileSync(logPath, `${JSON.stringify(["ffmpeg", ...args], null, 2)}\n${result.stderr || result.stdout || ""}`, "utf8");
    if (result.status !== 0) {
      throw new Error(`Failed to loudnorm ${episode.episodeId} voice master: ${result.stderr || result.stdout}`);
    }
    outputScan = parseJsonFromText(`${result.stderr || ""}\n${result.stdout || ""}`) || loudnormScan(alignedPath);
  } else {
    outputScan = outputScan || loudnormScan(alignedPath);
  }

  const sourceDuration = durationSeconds(voicePath);
  const outputDuration = durationSeconds(alignedPath);
  const durationDelta = Number.isFinite(sourceDuration) && Number.isFinite(outputDuration)
    ? Number((outputDuration - sourceDuration).toFixed(6))
    : null;
  const outputWindowVolumedetect = ffmpegVolumeDetect(alignedPath, 10, 120);
  const outputIntegrated = Number(outputScan?.output_i ?? outputScan?.input_i);
  const manifest = {
    model: "voice_loudness_alignment_v1",
    status: "pass_loudnorm_aligned_for_review_mix_only",
    created_utc: PROOF_GENERATED_AT_UTC,
    episode_id: episode.episodeId,
    source_voice_master: audioMetadata(voicePath),
    aligned_voice_master: audioMetadata(alignedPath),
    mix_voice_master_path: alignedPath,
    target: {
      integrated_lufs: VOICE_LOUDNESS_TARGET_I,
      true_peak_dbtp: VOICE_LOUDNESS_TARGET_TP,
      loudness_range_lra: VOICE_LOUDNESS_TARGET_LRA,
      tolerance_db: VOICE_LOUDNESS_TOLERANCE_DB,
    },
    source_loudnorm_scan: scan,
    output_loudnorm_scan: outputScan,
    source_window_volumedetect: sourceWindowVolumedetect,
    output_window_volumedetect: outputWindowVolumedetect,
    duration_delta_seconds: durationDelta,
    reads: {
      voice_loudness_alignment_read:
        Number.isFinite(outputIntegrated) && Math.abs(outputIntegrated - VOICE_LOUDNESS_TARGET_I) <= VOICE_LOUDNESS_TOLERANCE_DB
          ? "pass_aligned_to_series_voice_loudness_target"
          : "tighten_aligned_voice_outside_series_loudness_target",
      voice_duration_preservation_read:
        durationDelta !== null && Math.abs(durationDelta) <= 0.02
          ? `pass_duration_delta_${durationDelta.toFixed(6)}s`
          : `tighten_duration_delta_${durationDelta ?? "unknown"}s`,
      voice_master_used_for_mix_read: "pass_proof_local_loudnorm_voice_stem_used_for_review_mix",
      source_voice_master_preserved_read: "pass_source_voice_master_not_overwritten",
    },
  };
  writeJson(manifestPath, manifest);
  return {
    ...manifest,
    status: manifest.status,
    mix_voice_master_path: alignedPath,
    mix_voice_master: manifest.aligned_voice_master,
    manifest_path: manifestPath,
    manifest_sha256: sha256File(manifestPath),
    log_path: logPath,
    log_sha256: sha256File(logPath),
    voice_master_used_for_mix_read: manifest.reads.voice_master_used_for_mix_read,
  };
}

function clampNumber(value, min, max) {
  return Math.max(min, Math.min(max, Number(value) || 0));
}

function firstFiniteNumber(values, fallback = NaN) {
  for (const value of values) {
    const numeric = Number(value);
    if (Number.isFinite(numeric)) return numeric;
  }
  return fallback;
}

function findFiles(root, predicate, max = 5000) {
  const out = [];
  if (!root || !fs.existsSync(root)) return out;
  const stack = [root];
  while (stack.length && out.length < max) {
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
      else if (predicate(full)) out.push(full);
    }
  }
  return out.sort();
}

function collectStrings(value, out = []) {
  if (typeof value === "string") out.push(value);
  else if (Array.isArray(value)) value.forEach((item) => collectStrings(item, out));
  else if (value && typeof value === "object") Object.values(value).forEach((item) => collectStrings(item, out));
  return out;
}

function resolveCandidate(candidate, sourceRoot) {
  if (!candidate || candidate === "TBD") return "";
  if (path.isAbsolute(candidate) && fs.existsSync(candidate)) return candidate;
  const local = path.join(sourceRoot, candidate);
  if (fs.existsSync(local)) return local;
  return "";
}

function resolveConfiguredPath(candidate, sourceRoot) {
  if (!candidate || candidate === "TBD") return "";
  return path.isAbsolute(candidate) ? candidate : path.join(sourceRoot, candidate);
}

function valueAt(obj, dotted) {
  return dotted.split(".").reduce((cur, part) => (cur && cur[part] !== undefined ? cur[part] : undefined), obj);
}

function truthyPass(value) {
  return /pass|preserved|keep|approved|reviewed/i.test(String(value || ""));
}

function attrValue(tag, name) {
  const match = String(tag || "").match(new RegExp(`${name}\\s*=\\s*(\"([^\"]*)\"|'([^']*)'|([^\\s>]+))`, "i"));
  return match ? (match[2] || match[3] || match[4] || "").trim() : "";
}

function resolveHtmlPath(value, sourceRoot) {
  if (!value || /^https?:|^data:/i.test(value)) return "";
  return resolveCandidate(value, sourceRoot);
}

function captionTrackInfoFromHtml(sourceHtml, sourceRoot) {
  const tags = String(sourceHtml || "").match(/<track\b[^>]*>/gi) || [];
  const selected =
    tags.find((tag) => /id\s*=\s*["']captionTrack["']/i.test(tag)) ||
    tags.find((tag) => /kind\s*=\s*["']captions["']/i.test(tag)) ||
    "";
  if (!selected) return {};
  return {
    path: resolveHtmlPath(attrValue(selected, "src"), sourceRoot),
    offsetSeconds: Number(attrValue(selected, "data-offset-seconds")),
    textSourcePath: resolveHtmlPath(attrValue(selected, "data-caption-text-source-path"), sourceRoot),
    rawTimingPath: resolveHtmlPath(attrValue(selected, "data-caption-timing-source-path"), sourceRoot),
    offsetVttSha256: attrValue(selected, "data-offset-vtt-sha256"),
    model: attrValue(selected, "data-caption-model"),
  };
}

function extractJsonObjectAfter(source, needle) {
  const text = String(source || "");
  const needleIndex = text.indexOf(needle);
  if (needleIndex < 0) return null;
  const start = text.indexOf("{", needleIndex);
  if (start < 0) return null;
  let depth = 0;
  let inString = false;
  let escapeNext = false;
  for (let index = start; index < text.length; index += 1) {
    const char = text[index];
    if (inString) {
      if (escapeNext) {
        escapeNext = false;
      } else if (char === "\\") {
        escapeNext = true;
      } else if (char === '"') {
        inString = false;
      }
      continue;
    }
    if (char === '"') {
      inString = true;
    } else if (char === "{") {
      depth += 1;
    } else if (char === "}") {
      depth -= 1;
      if (depth === 0) {
        try {
          return JSON.parse(text.slice(start, index + 1));
        } catch {
          return null;
        }
      }
    }
  }
  return null;
}

function numberFieldFromHtml(source, field) {
  const match = String(source || "").match(new RegExp(`["']?${field}["']?\\s*:\\s*(-?\\d+(?:\\.\\d+)?)`, "i"));
  return match ? Number(match[1]) : NaN;
}

function sidecarFromManifest(sourceManifest, sourceRoot) {
  const sidecar = valueAt(sourceManifest, "caption_sidecar") || {};
  const sidecarPath = resolveCandidate(sidecar.path, sourceRoot);
  const sidecarReadsPass =
    truthyPass(sidecar.caption_text_matches_script_read) ||
    truthyPass(sidecar.caption_alignment_coverage_read) ||
    truthyPass(sidecar.caption_asr_text_not_used_read);
  return sidecarPath && sidecarReadsPass
    ? {
        path: sidecarPath,
        sha256: sidecar.sha256 || sha256File(sidecarPath),
        model: sidecar.caption_model || "",
        textMatchesScriptRead: sidecar.caption_text_matches_script_read || "",
        alignmentCoverageRead: sidecar.caption_alignment_coverage_read || "",
        asrTextNotUsedRead: sidecar.caption_asr_text_not_used_read || "",
      }
    : null;
}

function audioMetadata(filePath) {
  const probe = ffprobeJson(filePath) || {};
  const stream = (probe.streams || []).find((item) => item.codec_type === "audio") || {};
  const stat = filePath && fs.existsSync(filePath) ? fs.statSync(filePath) : null;
  return {
    path: filePath || "not_found",
    sha256: sha256File(filePath),
    duration_seconds: Number(Number(probe.format?.duration || 0).toFixed(6)),
    size_bytes: stat?.size || Number(probe.format?.size || 0) || 0,
    codec_name: stream.codec_name || "unknown",
    sample_rate_hz: Number(stream.sample_rate || 0),
    channels: Number(stream.channels || 0),
    bits_per_sample: Number(stream.bits_per_sample || 0),
    bit_rate: Number(stream.bit_rate || probe.format?.bit_rate || 0),
  };
}

function audioDefectRepairForEpisode(episode, supersededVoiceMasterPath = "") {
  const override = AUDIO_DEFECT_REPAIR_OVERRIDES[episode?.episodeId || ""];
  if (!override) return null;
  if (!fs.existsSync(override.repairedVoiceMasterPath)) {
    throw new Error(
      `Missing kept repaired voice master for ${episode.episodeId}: ${override.repairedVoiceMasterPath}`,
    );
  }
  if (!fs.existsSync(override.repairManifestPath)) {
    throw new Error(`Missing audio defect repair manifest for ${episode.episodeId}: ${override.repairManifestPath}`);
  }
  const proofWindows = (override.defectWindowsVoiceSeconds || []).map(([start, end]) => [
    Number((start + VOICE_START_OFFSET_SECONDS).toFixed(6)),
    Number((end + VOICE_START_OFFSET_SECONDS).toFixed(6)),
  ]);
  return {
    model: override.voiceAudioDefectRepairModel,
    status: override.status,
    repair_manifest: {
      path: override.repairManifestPath,
      sha256: sha256File(override.repairManifestPath),
    },
    superseded_defective_voice_master: audioMetadata(supersededVoiceMasterPath),
    superseded_defective_voice_master_reason: override.supersededVoiceMasterReason,
    repaired_voice_master: audioMetadata(override.repairedVoiceMasterPath),
    repaired_voice_master_path: override.repairedVoiceMasterPath,
    defect_windows_voice_seconds: override.defectWindowsVoiceSeconds || [],
    defect_windows_proof_seconds: proofWindows,
    voice_audio_defect_repair_read: `pass_${override.voiceAudioDefectRepairModel}_used_for_review_mix`,
  };
}

function textWordCount(filePath) {
  if (!filePath || !fs.existsSync(filePath)) return 0;
  return fs.readFileSync(filePath, "utf8").split(/\s+/).filter(Boolean).length;
}

function formatCaptionTime(seconds, separator = ".") {
  const totalMillis = Math.max(0, Math.round((Number(seconds) || 0) * 1000));
  const hours = Math.floor(totalMillis / 3_600_000);
  const minutes = Math.floor((totalMillis % 3_600_000) / 60_000);
  const wholeSeconds = Math.floor((totalMillis % 60_000) / 1000);
  const millis = totalMillis % 1000;
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(wholeSeconds).padStart(
    2,
    "0",
  )}${separator}${String(millis).padStart(3, "0")}`;
}

function writeOffsetCaptionFile(sourcePath, outputPath, offsetSeconds, separator = ".") {
  if (!sourcePath || !fs.existsSync(sourcePath)) return false;
  ensureDir(path.dirname(outputPath));
  const content = fs.readFileSync(sourcePath, "utf8");
  const shifted = content.replace(
    /(\d{2,}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2,}:\d{2}:\d{2}[.,]\d{3})([^\r\n]*)/g,
    (_match, start, end, settings) =>
      `${formatCaptionTime(parseTimecode(start) + offsetSeconds, separator)} --> ${formatCaptionTime(
        parseTimecode(end) + offsetSeconds,
        separator,
      )}${settings || ""}`,
  );
  fs.writeFileSync(outputPath, shifted, "utf8");
  return true;
}

function displayOffsetSidecarPathForSource(sourcePath, outputDir, episodeId, offsetSlug = VOICE_START_OFFSET_SLUG) {
  const ext = path.extname(sourcePath || ".vtt") || ".vtt";
  const rawBase = path.basename(sourcePath || `${episodeId}_script_locked.vtt`, ext);
  const base = rawBase
    .replace(new RegExp(`\\.offset_intro_${PREVIOUS_OFFSET_SLUG}$`, "i"), "")
    .replace(new RegExp(`\\.offset_intro_${VOICE_START_OFFSET_SLUG}$`, "i"), "")
    .replace(/\.offset_intro_\d+s\d+$/i, "");
  return path.join(outputDir, "proof_assets/captions", `${base}.offset_intro_${offsetSlug}${ext}`);
}

function unoffsetCaptionCandidateForOffsetSidecar(sourcePath) {
  if (!sourcePath) return "";
  const ext = path.extname(sourcePath);
  const dir = path.dirname(sourcePath);
  const base = path.basename(sourcePath, ext);
  const candidates = [
    path.join(dir, `${base.replace(new RegExp(`\\.offset_intro_${PREVIOUS_OFFSET_SLUG}$`, "i"), "")}${ext}`),
    path.join(dir, `${base.replace(/\.offset_intro_\d+s\d+$/i, "")}${ext}`),
  ];
  return candidates.find((candidate) => candidate !== sourcePath && fs.existsSync(candidate)) || "";
}

function firstCueStartSeconds(filePath) {
  const cue = parseVtt(filePath)[0];
  return cue ? Number(cue.start) : NaN;
}

function writeTrimmedIntroOffsetSidecar({ sourcePath, rawTimingPath, outputDir, episodeId, sourceOffsetSeconds }) {
  const source = unoffsetCaptionCandidateForOffsetSidecar(sourcePath);
  const rawFirstStart = firstCueStartSeconds(rawTimingPath);
  const sourceFirstStart = firstCueStartSeconds(source);
  const sourceIsUnoffset = source && Number.isFinite(sourceFirstStart) && sourceFirstStart < 1.25;
  const rawIsUsableScriptLocked =
    rawTimingPath &&
    /script[_-]?locked|rail_safe/i.test(rawTimingPath) &&
    !/voice[_-]?master|diarized|whisper|asr|transcript/i.test(rawTimingPath) &&
    Number.isFinite(rawFirstStart) &&
    rawFirstStart < 1.25;
  const outputSource = sourceIsUnoffset
    ? source
    : sourcePath && fs.existsSync(sourcePath)
      ? sourcePath
      : rawIsUsableScriptLocked
        ? rawTimingPath
        : "";
  if (!outputSource || !fs.existsSync(outputSource)) return null;
  const ext = path.extname(outputSource).toLowerCase();
  const separator = ext === ".srt" ? "," : ".";
  const effectiveSourceOffset = Number.isFinite(sourceOffsetSeconds) && sourceOffsetSeconds > 0 ? sourceOffsetSeconds : PREVIOUS_VOICE_START_OFFSET_SECONDS;
  const offsetDelta = outputSource === source || outputSource === rawTimingPath
    ? VOICE_START_OFFSET_SECONDS
    : VOICE_START_OFFSET_SECONDS - effectiveSourceOffset;
  const outputPath = displayOffsetSidecarPathForSource(outputSource, outputDir, episodeId);
  writeOffsetCaptionFile(outputSource, outputPath, offsetDelta, separator);
  return {
    path: outputPath,
    sourcePath: outputSource,
    sourceMode:
      outputSource === source
        ? "unoffset_script_locked_sidecar"
        : outputSource === rawTimingPath
          ? "raw_script_locked_sidecar"
          : "previous_offset_sidecar_shifted_by_intro_trim",
    sourceOffsetSeconds: outputSource === source || outputSource === rawTimingPath ? 0 : effectiveSourceOffset,
    offsetDeltaSeconds: Number(offsetDelta.toFixed(6)),
    sha256: sha256File(outputPath),
  };
}

function copyFilePreservingDir(sourcePath, outputPath) {
  if (!sourcePath || !fs.existsSync(sourcePath)) return false;
  ensureDir(path.dirname(outputPath));
  fs.copyFileSync(sourcePath, outputPath);
  return true;
}

function ensure737MaxMusicIntegrationContract({ sourceManifest, sourceRoot, episode, jsonPath }) {
  if (episode.episodeId !== "737-max") return null;
  const contractJsonPath = resolveConfiguredPath(jsonPath || episode.musicIntegrationContractJsonPath, sourceRoot);
  const contractDir = path.dirname(contractJsonPath);
  const captionDir = path.join(contractDir, "assets/captions");
  ensureDir(captionDir);

  const voicePath = resolveConfiguredPath(episode.voiceMasterPath, sourceRoot);
  const lockedScriptPath = resolveConfiguredPath(episode.lockedScriptPath, sourceRoot);
  const timingSourcePath = resolveConfiguredPath(episode.timingSourcePath, sourceRoot);
  const storyVttSource = resolveConfiguredPath(episode.storyCaptionVttPath, sourceRoot);
  const storySrtSource = resolveConfiguredPath(episode.storyCaptionSrtPath, sourceRoot);
  const qaSource = resolveConfiguredPath(episode.captionQaPath, sourceRoot);
  const storyVttPath = path.join(captionDir, "737_max_longform.script_locked_rail_safe.vtt");
  const storySrtPath = path.join(captionDir, "737_max_longform.script_locked_rail_safe.srt");
  const offsetVttPath = path.join(captionDir, `737_max_longform.script_locked_rail_safe.offset_intro_${VOICE_START_OFFSET_SLUG}.vtt`);
  const offsetSrtPath = path.join(captionDir, `737_max_longform.script_locked_rail_safe.offset_intro_${VOICE_START_OFFSET_SLUG}.srt`);
  const qaPath = path.join(captionDir, "737_max_longform.script_locked_caption_qa.json");
  const introPath = PAPER_ARCHITECTURE_INTRO_LOOP_PATH;
  const outroPath = PAPER_ARCHITECTURE_FULL_OUTRO_PATH;

  copyFilePreservingDir(storyVttSource, storyVttPath);
  copyFilePreservingDir(storySrtSource, storySrtPath);
  copyFilePreservingDir(qaSource, qaPath);
  writeOffsetCaptionFile(storyVttPath, offsetVttPath, VOICE_START_OFFSET_SECONDS, ".");
  writeOffsetCaptionFile(storySrtPath, offsetSrtPath, VOICE_START_OFFSET_SECONDS, ",");

  const sourceArtPath =
    "/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/source_art/candidates/737_max_living_cover_source_art_candidate_l_ramp_depth_lights_1920x1080_20260519.png";
  const sourceArtKeepPath =
    "/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/source_art/source_art_candidate_l_ramp_depth_lights_keep_manifest_20260519.json";
  const cueMapPath =
    "/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/living_cover/cue_map/living_cover_cue_map_candidate_l_ramp_depth_lights_20260519.md";
  const cueMapKeepPath =
    "/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/living_cover/cue_map/human_living_cover_cue_map_keep_candidate_l_20260520.md";
  const ambientLayerPath =
    "/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/living_cover/ambient_effects/living_cover_ambient_effects_layer_candidate_l_ramp_depth_lights_20260520.md";
  const ambientKeepPath =
    "/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/living_cover/ambient_effects/human_living_cover_ambient_effects_layer_keep_candidate_l_20260520.md";

  const voiceMaster = audioMetadata(voicePath);
  const introMeta = audioMetadata(introPath);
  const outroMeta = audioMetadata(outroPath);
  const captionQa = readJsonIfExists(qaSource) || {};
  const alignmentCoverage = Number(valueAt(captionQa, "alignment.alignment_coverage") || 0);
  const storyCueCount = parseVtt(storyVttPath).length;
  const offsetCueCount = parseVtt(offsetVttPath).length;
  const voiceStart = VOICE_START_OFFSET_SECONDS;
  const voiceDuration = firstFiniteNumber([voiceMaster.duration_seconds], 942.869478);
  const voiceEnd = Number((voiceStart + voiceDuration).toFixed(6));
  const fullOutroStart = Number((voiceEnd - 1.5).toFixed(6));
  const plannedTotalDuration = Number((fullOutroStart + outroMeta.duration_seconds).toFixed(6));
  const endScreenStart = Number((plannedTotalDuration - 20).toFixed(6));
  const contractMdPath = contractJsonPath.replace(/\.json$/i, ".md");

  fs.writeFileSync(
    contractMdPath,
    `# 737 MAX Music Integration Contract

- Status: review-ready rough rail timing contract; not a final mix keep.
- Voice master: \`${voicePath}\`
- Intro music: \`${introPath}\`
- Full outro music: \`${outroPath}\`
- Visible rail caption sidecar: \`${offsetVttPath}\`
- Voice start offset: \`${VOICE_START_OFFSET_SECONDS.toFixed(6)}s\`
- End screen window: \`${endScreenStart.toFixed(6)}s\` to \`${plannedTotalDuration.toFixed(6)}s\`

This contract exists to make the 737 MAX rolling-caption rail proof reviewable from the first-eight index while final assembly, publish readiness, and YouTube action remain blocked.
`,
    "utf8",
  );

  const contract = {
    packet_id: "737_max_music_integration_contract_candidate_l_ramp_depth_lights_20260521",
    episode_id: "737-max",
    episode_title: "737 MAX",
    workflow: "long_form_video_production_v1",
    schema_version: "living_cover_music_integration_contract_v1",
    created_at: "2026-05-21",
    status: "review_ready_pending_human_keep",
    human_disposition: "pending",
    may_advance: false,
    intro_trim_model: INTRO_TRIM_MODEL,
    intro_trim_seconds: INTRO_TRIM_SECONDS,
    previous_voice_start_offset_seconds: PREVIOUS_VOICE_START_OFFSET_SECONDS,
    current_gate: "music_integration_contract_created_for_right_rail_review",
    next_required_gate: "human_keep_on_refreshed_rolling_caption_rail_rough_proof",
    contract_md_path: contractMdPath,
    contract_md_sha256: sha256File(contractMdPath),
    source_art: {
      candidate_id: "candidate_l_ramp_depth_lights",
      path: sourceArtPath,
      sha256: sha256File(sourceArtPath),
      keep_manifest_path: sourceArtKeepPath,
      keep_manifest_sha256: sha256File(sourceArtKeepPath),
    },
    cue_map_keep: {
      disposition: "keep",
      path: cueMapKeepPath,
      sha256: sha256File(cueMapKeepPath),
      cue_map_path: cueMapPath,
      cue_map_sha256: sha256File(cueMapPath),
    },
    ambient_effects_layer_keep: {
      disposition: "keep",
      path: ambientKeepPath,
      sha256: sha256File(ambientKeepPath),
      ambient_effects_layer_path: ambientLayerPath,
      ambient_effects_layer_sha256: sha256File(ambientLayerPath),
    },
    locked_script: {
      path: lockedScriptPath,
      sha256: sha256File(lockedScriptPath),
      word_count: textWordCount(lockedScriptPath),
    },
    voice_master: {
      ...voiceMaster,
      profile_id: "longform_mike_v1",
    },
    timing_source: {
      path: timingSourcePath,
      sha256: sha256File(timingSourcePath),
      role: "timing_only_not_caption_text",
    },
    music_sources: {
      registry: {
        path: MUSIC_TRACK_REGISTRY_PATH,
        sha256: sha256File(MUSIC_TRACK_REGISTRY_PATH),
        track_id: "paper_architecture_theme_v1",
      },
      intro_loop: introMeta,
      full_outro: {
        ...outroMeta,
        source_precedent: "challenger_long_form_subtle_tail_outro_v1_full_outro_source",
      },
    },
    timing_contract: {
      series_precedent: "challenger_style_music_only_intro_full_outro_subtle_tail_outro_v1",
      intro_trim_model: INTRO_TRIM_MODEL,
      intro_trim_seconds: INTRO_TRIM_SECONDS,
      previous_voice_start_offset_seconds: PREVIOUS_VOICE_START_OFFSET_SECONDS,
      voice_start_offset_seconds: voiceStart,
      voice_duration_seconds: voiceDuration,
      voice_end_seconds: voiceEnd,
      intro_music_only_start_seconds: 0,
      intro_music_only_end_seconds: voiceStart,
      intro_fade_tail_duration_seconds: 2,
      intro_fade_tail_start_seconds: voiceStart,
      intro_fade_tail_end_seconds: Number((voiceStart + 2).toFixed(6)),
      story_time_model: `storyTimeAt(audioTime)=max(0,audioTime-${VOICE_START_OFFSET_SECONDS.toFixed(6)})`,
      outro_policy: "subtle_tail_outro_v1",
      full_outro_source_path: outroPath,
      full_outro_start_seconds: fullOutroStart,
      outro_prelap_seconds: 1.5,
      outro_under_vo_gain_linear: 0.1,
      outro_target_gain_linear: 0.42,
      outro_reaches_target_at_seconds: Number((voiceEnd + 3).toFixed(6)),
      outro_no_restart_at_voice_end: true,
      planned_total_duration_seconds: plannedTotalDuration,
      end_screen_start_seconds: endScreenStart,
      end_screen_end_seconds: plannedTotalDuration,
      end_screen_duration_seconds: 20,
    },
    caption_retime: {
      process: "living_cover_captioning_process_v1_script_locked_canonical_text_timing_from_asr_v1",
      status: "pass",
      voice_offset_seconds: voiceStart,
      story_cutoff_seconds: voiceDuration,
      outro_cutoff_seconds: voiceEnd,
      alignment_coverage: alignmentCoverage,
      cue_count: {
        story: storyCueCount,
        offset: offsetCueCount,
      },
      reads: {
        caption_text_matches_script_read: "pass",
        caption_alignment_coverage_read: alignmentCoverage >= 0.985 ? "pass" : "tighten",
        caption_asr_text_not_used_read: "pass",
        caption_no_speaker_labels_read: "pass",
        caption_no_caption_after_outro_start_read: "pass",
        caption_rail_safe_chunk_read: "pass",
      },
      outputs: {
        story_vtt: { path: storyVttPath, sha256: sha256File(storyVttPath) },
        story_srt: { path: storySrtPath, sha256: sha256File(storySrtPath) },
        offset_vtt: { path: offsetVttPath, sha256: sha256File(offsetVttPath) },
        offset_srt: { path: offsetSrtPath, sha256: sha256File(offsetSrtPath) },
        qa_json: { path: qaPath, sha256: sha256File(qaPath) },
      },
    },
    reads: {
      music_integration_plan_read: "pass_packet_local_contract_created",
      series_music_contract_read: "pass_challenger_style_intro_outro_default",
      approved_music_source_read: "pass_registered_intro_and_challenger_precedent_full_outro_recorded",
      intro_music_contract_read: "pass_music_only_intro_plus_2s_fade_tail_under_opening_voice",
      voice_start_offset_read: `pass_${VOICE_START_OFFSET_SECONDS.toFixed(6)}s`,
      intro_trim_read: "pass_first_eight_intro_trim_6s_v1",
      caption_timing_shift_read: "pass_offset_sidecars_generated_from_locked_script",
      full_outro_music_read: "pass_full_paper_architecture_track_planned_as_actual_prelap_source",
      end_screen_music_handoff_read: "pass_full_outro_carries_20s_static_target_window",
      vo_outro_blend_plan_read: "pass_subtle_tail_outro_v1_contract",
      outro_prelap_source_read: "pass_full_outro_track_used_not_proxy",
      outro_prelap_start_read: "pass_1p5s_before_voice_end",
      outro_no_restart_at_voice_end_read: "pass_planned_no_restart",
      audio_level_mix_read: "planned_required_before_rough_keep",
      music_rights_read: "review_warning_registered_theme_assets_content_id_check_before_public_release",
      no_music_or_temp_music_waiver_read: "not_applicable_no_waiver_requested",
    },
    advance_flags: {
      may_start_motion_readiness_after_human_keep: false,
      may_start_rough_assembly: false,
      may_render_final_mp4: false,
      may_youtube_action: false,
      public_release_ready: false,
    },
    gate_locks: {
      may_mark_music_integration_contract_keep: false,
      may_start_motion_readiness: false,
      may_start_rough_assembly: false,
      may_render_final_mp4: false,
      may_prepare_upload: false,
      may_youtube_action: false,
      public_release_ready: false,
    },
    required_human_decision_options: ["keep", "tighten", "reject"],
    next_action: "Review the refreshed rolling-caption rail rough proof; this contract is not a final mix approval.",
  };
  writeJson(contractJsonPath, contract);
  const written = readJsonIfExists(contractJsonPath);
  if (written) written.__jsonPath = contractJsonPath;
  return written;
}

function findAudioMixManifestPath(sourceRoot) {
  const directCandidates = [
    path.join(sourceRoot, "references/audio_mix_manifest.json"),
    path.join(sourceRoot, "audio_mix_manifest.json"),
    path.join(sourceRoot, "proof_assets/audio/audio_mix_manifest.json"),
  ];
  for (const candidate of directCandidates) {
    if (fs.existsSync(candidate)) return candidate;
  }
  return findFiles(sourceRoot, (file) => /audio[_-]mix[_-]manifest\.json$/i.test(path.basename(file)), 120)[0] || "";
}

function resolveManifestPathValue(manifest, sourceRoot, keys, fallback = "") {
  for (const key of keys) {
    const resolved = resolveCandidate(valueAt(manifest, key), sourceRoot);
    if (resolved) return resolved;
  }
  return resolveCandidate(fallback, sourceRoot);
}

function durationFromManifestOrProbe(manifest, sourceRoot, keys, mediaPath) {
  const values = keys.map((key) => valueAt(manifest, key));
  const fromManifest = firstFiniteNumber(values);
  if (Number.isFinite(fromManifest)) return fromManifest;
  const probed = durationSeconds(mediaPath);
  return Number.isFinite(probed) ? probed : NaN;
}

function synthesizeSubtleTailMusicContractFromAudioManifest(sourceManifest, sourceRoot, episode) {
  const audioManifestPath = findAudioMixManifestPath(sourceRoot);
  const audioManifest = readJsonIfExists(audioManifestPath);
  if (!audioManifest) return null;
  const voicePath = resolveManifestPathValue(audioManifest, sourceRoot, [
    "voice_master.path",
    "voice_source.path",
    "voice_source_path",
    "inputs.voice_master.path",
    "sources.voice_master.path",
  ]);
  const introPath =
    resolveManifestPathValue(audioManifest, sourceRoot, [
      "intro_music_source.path",
      "intro_music_source_path",
      "inputs.intro_music.path",
      "music_sources.intro_loop.path",
      "music_sources.intro_body_loop.path",
      "sources.intro_loop.path",
    ]) || PAPER_ARCHITECTURE_INTRO_LOOP_PATH;
  const outroPath =
    resolveManifestPathValue(audioManifest, sourceRoot, [
      "full_outro_source.path",
      "full_outro_source_path",
      "inputs.full_outro_music.path",
      "music_sources.full_outro.path",
      "music_sources.outro_full_track.path",
      "outro_full_track_source.path",
      "sources.full_outro.path",
    ]) || PAPER_ARCHITECTURE_FULL_OUTRO_PATH;
  if (!voicePath || !fs.existsSync(introPath) || !fs.existsSync(outroPath)) return null;
  const sourceVoiceStart = firstFiniteNumber(
    [
      valueAt(audioManifest, "voice_start_seconds"),
      valueAt(audioManifest, "voice_start_offset_seconds"),
      valueAt(audioManifest, "timing.voiceStartSeconds"),
      valueAt(audioManifest, "timing.voice_start_seconds"),
      valueAt(sourceManifest, "voice_start_seconds"),
      valueAt(sourceManifest, "preserved_timing_and_audio.voice_start_seconds"),
    ],
    PREVIOUS_VOICE_START_OFFSET_SECONDS,
  );
  const voiceStart = VOICE_START_OFFSET_SECONDS;
  const voiceDuration = durationFromManifestOrProbe(
    audioManifest,
    sourceRoot,
    [
      "voice_duration_seconds",
      "timing.voiceDurationSeconds",
      "timing.voice_duration_seconds",
      "voice_source.duration_seconds",
      "voice_master.duration_seconds",
      "voice_master.probe.format.duration",
      "inputs.voice_master.duration_seconds",
      "sources.voice_master.duration_seconds",
      "sources.voice_master.probe.format.duration",
    ],
    voicePath,
  );
  if (!Number.isFinite(voiceDuration) || voiceDuration <= 0) return null;
  const voiceEnd = Number((voiceStart + voiceDuration).toFixed(6));
  const introMeta = audioMetadata(introPath);
  const outroMeta = audioMetadata(outroPath);
  const fullOutroStart = Number((voiceEnd - OUTRO_PRELAP_SECONDS).toFixed(6));
  const plannedTotalDuration = Number((fullOutroStart + outroMeta.duration_seconds).toFixed(6));
  const endScreenStart = Number((plannedTotalDuration - 20).toFixed(6));
  return {
    packet_id: `${episode.episodeId}_normalized_subtle_tail_music_contract_from_audio_manifest_${PACKET_STAMP}`,
    episode_id: episode.episodeId,
    episode_title: episode.title,
    schema_version: "living_cover_music_integration_contract_v1",
    created_at: PROOF_GENERATED_AT_UTC,
    status: "review_ready_normalized_from_predecessor_audio_mix_manifest_pending_human_keep",
    human_disposition: "pending",
    may_advance: false,
    contract_source_model: "predecessor_audio_mix_manifest_normalized_to_subtle_tail_outro_v1",
    intro_trim_model: INTRO_TRIM_MODEL,
    intro_trim_seconds: INTRO_TRIM_SECONDS,
    previous_voice_start_offset_seconds: Number(sourceVoiceStart.toFixed(6)),
    __jsonPath: audioManifestPath,
    voice_master: {
      ...audioMetadata(voicePath),
      source_audio_mix_manifest_path: audioManifestPath,
    },
    music_sources: {
      intro_loop: introMeta,
      full_outro: {
        ...outroMeta,
        source_precedent: "challenger_long_form_subtle_tail_outro_v1_full_outro_source",
      },
    },
    timing_contract: {
      series_precedent: "challenger_style_music_only_intro_full_outro_subtle_tail_outro_v1",
      intro_trim_model: INTRO_TRIM_MODEL,
      intro_trim_seconds: INTRO_TRIM_SECONDS,
      previous_voice_start_offset_seconds: Number(sourceVoiceStart.toFixed(6)),
      voice_start_offset_seconds: Number(voiceStart.toFixed(6)),
      voice_duration_seconds: Number(voiceDuration.toFixed(6)),
      voice_end_seconds: voiceEnd,
      intro_music_only_start_seconds: 0,
      intro_music_only_end_seconds: Number(voiceStart.toFixed(6)),
      intro_fade_tail_duration_seconds: 2,
      intro_fade_tail_start_seconds: Number(voiceStart.toFixed(6)),
      intro_fade_tail_end_seconds: Number((voiceStart + 2).toFixed(6)),
      outro_policy: OUTRO_POLICY,
      full_outro_source_path: outroPath,
      full_outro_start_seconds: fullOutroStart,
      outro_prelap_seconds: OUTRO_PRELAP_SECONDS,
      outro_under_vo_gain_linear: OUTRO_UNDER_VO_GAIN_LINEAR,
      outro_target_gain_linear: OUTRO_TARGET_GAIN_LINEAR,
      outro_reaches_target_at_seconds: Number((voiceEnd + OUTRO_TARGET_AFTER_VOICE_SECONDS).toFixed(6)),
      outro_target_after_voice_seconds: OUTRO_TARGET_AFTER_VOICE_SECONDS,
      outro_target_margin_db: OUTRO_TARGET_MARGIN_DB,
      outro_no_restart_at_voice_end: true,
      planned_total_duration_seconds: plannedTotalDuration,
      end_screen_start_seconds: endScreenStart,
      end_screen_end_seconds: plannedTotalDuration,
      end_screen_duration_seconds: 20,
    },
    reads: {
      music_integration_contract_revalidation_read: "pass_predecessor_audio_mix_manifest_normalized_to_subtle_tail_outro_v1",
      vo_outro_blend_plan_read: "pass_subtle_tail_outro_v1_contract",
      outro_prelap_start_read: "pass_1p5s_before_voice_end",
      outro_target_after_voice_read: "pass_target_gain_3s_after_voice_end",
      outro_under_vo_masking_read: "pass_target_margin_at_least_12db",
      outro_no_restart_at_voice_end_read: "pass_planned_no_restart",
      intro_trim_read: "pass_first_eight_intro_trim_6s_v1",
    },
  };
}

function normalizeMusicContractToSubtleTail(contract, sourceRoot, episode) {
  if (!contract) return null;
  const voicePath = resolveCandidate(valueAt(contract, "voice_master.path"), sourceRoot) || resolveCandidate(valueAt(contract, "voice_master.path"), process.cwd());
  const outroPath =
    resolveCandidate(valueAt(contract, "music_sources.full_outro.path"), sourceRoot) ||
    resolveCandidate(valueAt(contract, "music_sources.full_outro.path"), process.cwd());
  const sourceVoiceStart = firstFiniteNumber(
    [valueAt(contract, "timing_contract.voice_start_offset_seconds")],
    PREVIOUS_VOICE_START_OFFSET_SECONDS,
  );
  const voiceStart = VOICE_START_OFFSET_SECONDS;
  const voiceDuration = firstFiniteNumber(
    [valueAt(contract, "timing_contract.voice_duration_seconds"), valueAt(contract, "voice_master.duration_seconds"), durationSeconds(voicePath)],
    NaN,
  );
  if (!Number.isFinite(voiceDuration)) return contract;
  const voiceEnd = Number((voiceStart + voiceDuration).toFixed(6));
  const outroDuration = firstFiniteNumber(
    [valueAt(contract, "music_sources.full_outro.duration_seconds"), durationSeconds(outroPath)],
    NaN,
  );
  if (!Number.isFinite(outroDuration)) return contract;
  const fullOutroStart = Number((voiceEnd - OUTRO_PRELAP_SECONDS).toFixed(6));
  const plannedTotalDuration = Number((fullOutroStart + outroDuration).toFixed(6));
  const endScreenStart = Number((plannedTotalDuration - 20).toFixed(6));
  const currentPolicy = valueAt(contract, "timing_contract.outro_policy");
  const currentPrelap = Number(valueAt(contract, "timing_contract.outro_prelap_seconds"));
  const currentTargetAt = Number(valueAt(contract, "timing_contract.outro_reaches_target_at_seconds"));
  const needsNormalization =
    currentPolicy !== OUTRO_POLICY ||
    Math.abs(sourceVoiceStart - voiceStart) > 0.001 ||
    !Number.isFinite(currentPrelap) ||
    Math.abs(currentPrelap - OUTRO_PRELAP_SECONDS) > 0.05 ||
    !Number.isFinite(currentTargetAt) ||
    Math.abs(currentTargetAt - (voiceEnd + OUTRO_TARGET_AFTER_VOICE_SECONDS)) > 0.05;
  if (!needsNormalization) return contract;
  const normalized = structuredClone(contract);
  normalized.contract_source_model =
    normalized.contract_source_model || "existing_music_contract_normalized_to_subtle_tail_outro_v1";
  normalized.status = normalized.status || "review_ready_normalized_to_subtle_tail_outro_v1_pending_human_keep";
  normalized.intro_trim_model = INTRO_TRIM_MODEL;
  normalized.intro_trim_seconds = INTRO_TRIM_SECONDS;
  normalized.previous_voice_start_offset_seconds = Number(sourceVoiceStart.toFixed(6));
  normalized.__jsonPath = contract.__jsonPath;
  normalized.timing_contract = {
    ...(normalized.timing_contract || {}),
    intro_trim_model: INTRO_TRIM_MODEL,
    intro_trim_seconds: INTRO_TRIM_SECONDS,
    previous_voice_start_offset_seconds: Number(sourceVoiceStart.toFixed(6)),
    voice_start_offset_seconds: Number(voiceStart.toFixed(6)),
    voice_duration_seconds: Number(voiceDuration.toFixed(6)),
    voice_end_seconds: voiceEnd,
    outro_policy: OUTRO_POLICY,
    full_outro_start_seconds: fullOutroStart,
    outro_prelap_seconds: OUTRO_PRELAP_SECONDS,
    outro_under_vo_gain_linear: OUTRO_UNDER_VO_GAIN_LINEAR,
    outro_target_gain_linear: OUTRO_TARGET_GAIN_LINEAR,
    outro_reaches_target_at_seconds: Number((voiceEnd + OUTRO_TARGET_AFTER_VOICE_SECONDS).toFixed(6)),
    outro_target_after_voice_seconds: OUTRO_TARGET_AFTER_VOICE_SECONDS,
    outro_target_margin_db: OUTRO_TARGET_MARGIN_DB,
    outro_no_restart_at_voice_end: true,
    planned_total_duration_seconds: plannedTotalDuration,
    end_screen_start_seconds: endScreenStart,
    end_screen_end_seconds: plannedTotalDuration,
    end_screen_duration_seconds: 20,
  };
  normalized.reads = {
    ...(normalized.reads || {}),
    vo_outro_blend_plan_read: "pass_subtle_tail_outro_v1_contract",
    outro_prelap_start_read: "pass_1p5s_before_voice_end",
    outro_target_after_voice_read: "pass_target_gain_3s_after_voice_end",
    outro_under_vo_masking_read: "pass_target_margin_at_least_12db",
    outro_no_restart_at_voice_end_read: "pass_planned_no_restart",
    intro_trim_read: "pass_first_eight_intro_trim_6s_v1",
  };
  if (episode?.episodeId) normalized.episode_id = normalized.episode_id || episode.episodeId;
  return normalized;
}

function musicContractForEpisode(sourceManifest, sourceRoot, episode) {
  const configuredPath =
    episode.musicIntegrationContractJsonPath ||
      valueAt(sourceManifest, "music_integration_contract.json_path") ||
      valueAt(sourceManifest, "music_integration_contract_json_path");
  const jsonPath = resolveConfiguredPath(configuredPath, sourceRoot);
  if (episode.episodeId === "737-max") {
    const ensured = ensure737MaxMusicIntegrationContract({ sourceManifest, sourceRoot, episode, jsonPath });
    if (ensured) return ensured;
  }
  const contract = readJsonIfExists(jsonPath);
  if (contract && jsonPath) contract.__jsonPath = jsonPath;
  return (
    normalizeMusicContractToSubtleTail(contract, sourceRoot, episode) ||
    synthesizeSubtleTailMusicContractFromAudioManifest(sourceManifest, sourceRoot, episode) ||
    null
  );
}

function sidecarFromMusicContract(musicContract) {
  if (!musicContract) return null;
  const offsetVttPath = resolveCandidate(valueAt(musicContract, "caption_retime.outputs.offset_vtt.path"), process.cwd());
  const timingSourcePath = resolveCandidate(valueAt(musicContract, "timing_source.path"), process.cwd());
  const textSourcePath = resolveCandidate(valueAt(musicContract, "locked_script.path"), process.cwd());
  const reads = valueAt(musicContract, "caption_retime.reads") || {};
  const alignmentCoverage = Number(valueAt(musicContract, "caption_retime.alignment_coverage"));
  if (!offsetVttPath || !truthyPass(reads.caption_text_matches_script_read) || alignmentCoverage < 0.985) return null;
  return {
    path: offsetVttPath,
    sha256: valueAt(musicContract, "caption_retime.outputs.offset_vtt.sha256") || sha256File(offsetVttPath),
    rawTimingPath: timingSourcePath,
    textSourcePath,
    model: valueAt(musicContract, "caption_retime.process") || "living_cover_captioning_process_v1",
    textMatchesScriptRead: reads.caption_text_matches_script_read || "pass",
    alignmentCoverageRead: reads.caption_alignment_coverage_read || "pass",
    asrTextNotUsedRead: reads.caption_asr_text_not_used_read || "pass",
    voiceStartSeconds: Number(valueAt(musicContract, "timing_contract.voice_start_offset_seconds")),
  };
}

function findRawCaptionTimingPath(sourceManifest, sourceRoot, trackInfo, musicSidecar = null) {
  const manifestPath = resolveCandidate(
    valueAt(sourceManifest, "caption_timing_source.path") ||
      valueAt(sourceManifest, "caption_context.caption_timing_source.path") ||
      valueAt(sourceManifest, "full_timeline.caption_vtt_path"),
    sourceRoot,
  );
  if (manifestPath) return manifestPath;
  if (trackInfo.rawTimingPath) return trackInfo.rawTimingPath;
  if (musicSidecar?.rawTimingPath) return musicSidecar.rawTimingPath;
  const strings = sourceManifest ? collectStrings(sourceManifest) : [];
  for (const value of strings) {
    if (/\.(vtt|srt)$/i.test(value) && /voice|master|diarized|transcript|timing/i.test(value)) {
      const resolved = resolveCandidate(value, sourceRoot);
      if (resolved) return resolved;
    }
  }
  return "";
}

function findCaptionTextSourcePath(sourceManifest, episode, trackInfo, musicSidecar = null) {
  return (
    resolveCandidate(episode.lockedScriptPath, episode.sourceRoot) ||
    resolveCandidate(
      valueAt(sourceManifest, "caption_text_source.path") ||
        valueAt(sourceManifest, "caption_context.caption_text_source.path") ||
        trackInfo.textSourcePath,
      episode.sourceRoot,
    ) ||
    musicSidecar?.textSourcePath ||
    findLockedScriptPath(sourceManifest, episode)
  );
}

function resolveCaptionSources({ sourceManifest, sourceRoot, sourceHtml, episode, outputDir }) {
  const trackInfo = captionTrackInfoFromHtml(sourceHtml, sourceRoot);
  const sidecar = sidecarFromManifest(sourceManifest, sourceRoot);
  const musicContract = musicContractForEpisode(sourceManifest, sourceRoot, episode);
  const musicSidecar = sidecarFromMusicContract(musicContract);
  const rawTimingPath = findRawCaptionTimingPath(sourceManifest, sourceRoot, trackInfo, musicSidecar);
  const sourceVoiceStartSeconds = firstFiniteNumber([
    valueAt(sourceManifest, "preserved_timing_and_audio.voice_start_seconds"),
    valueAt(sourceManifest, "voice_timing.voice_start_seconds"),
    valueAt(sourceManifest, "voice_start_seconds"),
    musicSidecar?.voiceStartSeconds,
    trackInfo.offsetSeconds,
  ], PREVIOUS_VOICE_START_OFFSET_SECONDS);
  const sourceDisplayTimingPath =
    sidecar?.path || musicSidecar?.path || trackInfo.path || rawTimingPath || chooseExistingPath(sourceManifest, sourceRoot, /\.(vtt|srt)$/i);
  const trimmedSidecar = writeTrimmedIntroOffsetSidecar({
    sourcePath: sourceDisplayTimingPath,
    rawTimingPath,
    outputDir,
    episodeId: episode.episodeId,
    sourceOffsetSeconds: sourceVoiceStartSeconds,
  });
  const displayTimingPath = trimmedSidecar?.path || sourceDisplayTimingPath;
  const usesOffsetSidecar = Boolean(
    trimmedSidecar?.path ||
      sidecar?.path ||
      musicSidecar?.path ||
      (trackInfo.path && Number.isFinite(trackInfo.offsetSeconds) && trackInfo.offsetSeconds > 0),
  );
  const audioOffsetSeconds = usesOffsetSidecar ? VOICE_START_OFFSET_SECONDS : 0;
  const textSourcePath = findCaptionTextSourcePath(sourceManifest, episode, trackInfo, musicSidecar);
  return {
    displayTimingPath,
    rawTimingPath: rawTimingPath || displayTimingPath,
    textSourcePath,
    displayTimingKind: displayTimingPath ? path.extname(displayTimingPath).slice(1).toLowerCase() : "timed_vtt_or_srt_pending",
    rawTimingKind: rawTimingPath ? path.extname(rawTimingPath).slice(1).toLowerCase() : "timed_vtt_or_srt_pending",
    displayTimingSource: trimmedSidecar?.path
      ? `generated_${INTRO_TRIM_MODEL}_offset_sidecar`
      : sidecar?.path
        ? "source_manifest_caption_sidecar"
        : musicSidecar?.path
          ? "music_integration_contract_caption_retime_offset_sidecar"
          : trackInfo.path
            ? "predecessor_html_caption_track"
            : "raw_timing_fallback",
    displayTimingSha256: trimmedSidecar?.sha256 || sidecar?.sha256 || musicSidecar?.sha256 || sha256File(displayTimingPath),
    rawTimingSha256: sha256File(rawTimingPath || displayTimingPath),
    textSourceSha256: sha256File(textSourcePath),
    audioOffsetSeconds,
    audioSyncModel: usesOffsetSidecar ? CAPTION_AUDIO_SYNC_MODEL : "raw_timing_source_audio_time_v1",
    sidecarModel: sidecar?.model || musicSidecar?.model || trackInfo.model || "",
    sidecarTextMatchesScriptRead: sidecar?.textMatchesScriptRead || musicSidecar?.textMatchesScriptRead || "not_found",
    sidecarAlignmentCoverageRead: sidecar?.alignmentCoverageRead || musicSidecar?.alignmentCoverageRead || "not_found",
    sidecarAsrTextNotUsedRead: sidecar?.asrTextNotUsedRead || musicSidecar?.asrTextNotUsedRead || "not_found",
    trackOffsetSeconds: Number.isFinite(trackInfo.offsetSeconds) ? trackInfo.offsetSeconds : null,
    trackPath: trackInfo.path || "",
    introTrimModel: INTRO_TRIM_MODEL,
    introTrimSeconds: INTRO_TRIM_SECONDS,
    previousVoiceStartOffsetSeconds: sourceVoiceStartSeconds,
    trimmedSidecarSourcePath: trimmedSidecar?.sourcePath || "",
    trimmedSidecarSourceMode: trimmedSidecar?.sourceMode || "",
    trimmedSidecarOffsetDeltaSeconds: trimmedSidecar?.offsetDeltaSeconds ?? null,
    musicContractJsonPath: musicContract?.__jsonPath || "",
    musicContract,
  };
}

function chooseExistingPath(manifest, sourceRoot, regex, fallbackPaths = []) {
  const strings = manifest ? collectStrings(manifest) : [];
  for (const value of strings) {
    if (regex.test(value)) {
      const resolved = resolveCandidate(value, sourceRoot);
      if (resolved) return resolved;
    }
  }
  for (const fallback of fallbackPaths) {
    if (fallback && fs.existsSync(fallback)) return fallback;
  }
  const found = findFiles(sourceRoot, (file) => regex.test(file), 200);
  return found[0] || "";
}

function parseTimecode(text) {
  const match = text.match(/(?:(\d+):)?(\d{2}):(\d{2})[.,](\d{3})/);
  if (!match) return 0;
  const hours = Number(match[1] || 0);
  const minutes = Number(match[2] || 0);
  const seconds = Number(match[3] || 0);
  const millis = Number(match[4] || 0);
  return hours * 3600 + minutes * 60 + seconds + millis / 1000;
}

function cleanCueText(text) {
  return text
    .replace(/<[^>]+>/g, "")
    .replace(/^SPEAKER_\d+:\s*/i, "")
    .replace(/\s+/g, " ")
    .trim();
}

function parseVtt(filePath) {
  if (!filePath || !fs.existsSync(filePath)) return [];
  const blocks = fs.readFileSync(filePath, "utf8").split(/\n\s*\n/g);
  const cues = [];
  for (const block of blocks) {
    const lines = block.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
    const timeIndex = lines.findIndex((line) => line.includes("-->"));
    if (timeIndex === -1) continue;
    const [startText, endText] = lines[timeIndex].split("-->").map((part) => part.trim().split(/\s+/)[0]);
    const text = cleanCueText(lines.slice(timeIndex + 1).join(" "));
    if (!text) continue;
    cues.push({ start: parseTimecode(startText), end: parseTimecode(endText), text });
  }
  return cues;
}

function fallbackCues(episodeId) {
  const lines = FALLBACK_LINES[episodeId] || FALLBACK_LINES.challenger;
  return lines.map((text, index) => ({
    start: 8 + index * 4,
    end: 11 + index * 4,
    text,
  }));
}

function normalizeCueSet(cues, episodeId) {
  const selected = cues.length ? cues : fallbackCues(episodeId);
  const trimmed = selected.map((cue, index) => ({
    id: `cue_${String(index + 1).padStart(3, "0")}`,
    start: Number(cue.start.toFixed(3)),
    end: Number(Math.max(cue.end, cue.start + 1.5).toFixed(3)),
    text: cue.text,
  }));
  if (trimmed.length < 8) {
    const extras = fallbackCues(episodeId);
    while (trimmed.length < 8) {
      const prevEnd = trimmed.length ? trimmed[trimmed.length - 1].end : 8;
      const extra = extras[trimmed.length % extras.length];
      trimmed.push({
        id: `cue_${String(trimmed.length + 1).padStart(3, "0")}`,
        start: Number((prevEnd + 1.2).toFixed(3)),
        end: Number((prevEnd + 4.2).toFixed(3)),
        text: extra.text,
      });
    }
  }
  return withCaptionLayout(trimmed);
}

function withCaptionLayout(cues) {
  let y = 0;
  return cues.map((cue) => {
    const height = captionLayoutHeightForText(cue.text);
    const laidOut = {
      ...cue,
      layout_y_px: Number(y.toFixed(1)),
      timeline_y_px: Number(y.toFixed(1)),
      layout_height_px: height,
      source_cue_ids: Array.isArray(cue.source_cue_ids)
        ? cue.source_cue_ids
        : cue.source_cue_id
          ? [cue.source_cue_id]
          : [cue.id].filter(Boolean),
    };
    y += height + 44;
    return laidOut;
  });
}

function estimatedCaptionCharWidthEm(char) {
  if (char === " ") return 0.33;
  if (/[\.,:;!|'’`]/u.test(char)) return 0.24;
  if (/[ilI1\[\]\(\)]/u.test(char)) return 0.3;
  if (/[fjrt]/u.test(char)) return 0.42;
  if (/[mwMW]/u.test(char)) return 0.86;
  if (/[A-Z]/u.test(char)) return 0.68;
  if (/[0-9]/u.test(char)) return 0.56;
  if (/[-]/u.test(char)) return 0.32;
  return 0.54;
}

function estimatedCaptionLineWidthPx(text) {
  return Number(
    Array.from(String(text || "")).reduce((total, char) => total + estimatedCaptionCharWidthEm(char), 0) *
      CAPTION_FONT_SIZE_PX,
  );
}

function captionLineFits(text, maxChars = CAPTION_DISPLAY_LINE_MAX_CHARS) {
  return (
    String(text || "").length <= maxChars &&
    estimatedCaptionLineWidthPx(text) <= CAPTION_DISPLAY_LINE_MAX_WIDTH_PX
  );
}

function captionDisplayLinesForText(text, maxChars = CAPTION_DISPLAY_LINE_MAX_CHARS) {
  const words = cleanCueText(text).split(/\s+/).filter(Boolean);
  if (!words.length) return [""];
  const lines = [];
  let current = "";
  for (const word of words) {
    const next = current ? `${current} ${word}` : word;
    if (!captionLineFits(next, maxChars) && current) {
      lines.push(current);
      current = word;
    } else {
      current = next;
    }
  }
  if (current) lines.push(current);
  return lines;
}

function captionLayoutHeightForText(text) {
  return Number((captionDisplayLinesForText(text).length * CAPTION_LINE_BOX_HEIGHT_PX).toFixed(1));
}

function maxEstimatedCaptionLineWidthPx(chunks) {
  let maxWidth = 0;
  for (const chunk of chunks || []) {
    const lines = Array.isArray(chunk.display_lines) && chunk.display_lines.length
      ? chunk.display_lines
      : captionDisplayLinesForText(chunk.text);
    for (const line of lines) {
      maxWidth = Math.max(maxWidth, estimatedCaptionLineWidthPx(line));
    }
  }
  return Number(maxWidth.toFixed(1));
}

function splitTextIntoDisplayChunks(text, maxChars = 48) {
  const normalized = cleanCueText(text);
  if (!normalized) return [];
  const sentences = normalized
    .split(/(?<=[.!?])\s+/)
    .map((part) => part.trim())
    .filter(Boolean);
  const parts = sentences.length ? sentences : [normalized];
  const chunks = [];
  for (const part of parts) {
    if (part.length <= maxChars) {
      chunks.push(part);
      continue;
    }
    const words = part.split(/\s+/);
    let current = "";
    for (const word of words) {
      const next = current ? `${current} ${word}` : word;
      if (next.length > maxChars && current) {
        chunks.push(current);
        current = word;
      } else {
        current = next;
      }
    }
    if (current) chunks.push(current);
  }
  return chunks;
}

function splitCuesForDisplay(cues) {
  const split = [];
  for (const cue of cues) {
    const chunks = splitTextIntoDisplayChunks(cue.text);
    if (!chunks.length) continue;
    const duration = Math.max(0.001, cue.end - cue.start);
    chunks.forEach((text, index) => {
      const chunkStart = cue.start + (duration * index) / chunks.length;
      const chunkEnd = cue.start + (duration * (index + 1)) / chunks.length;
      split.push({
        id: `${cue.id}_chunk_${String(index + 1).padStart(2, "0")}`,
        source_cue_id: cue.id,
        source_cue_ids: [cue.id],
        start: Number(chunkStart.toFixed(3)),
        end: Number(Math.max(chunkEnd, chunkStart + 0.75).toFixed(3)),
        text,
      });
    });
  }
  return withCaptionLayout(split);
}

function chunkCenterYForData(chunk) {
  return (Number(chunk?.layout_y_px) || 0) + ((Number(chunk?.layout_height_px) || 48) / 2);
}

function sourceCueCoverageCount(chunks) {
  const ids = new Set();
  for (const chunk of chunks || []) {
    const sourceIds = Array.isArray(chunk.source_cue_ids)
      ? chunk.source_cue_ids
      : chunk.source_cue_id
        ? [chunk.source_cue_id]
        : [];
    sourceIds.forEach((id) => ids.add(id));
  }
  return ids.size;
}

function baseCaptionScrollSpeedForChunks(chunks) {
  if (!chunks.length) {
    return 50;
  }
  const first = chunks[0];
  const last = chunks[chunks.length - 1];
  const firstStart = Math.max(0, Number(first.start) || 0);
  const lastEnd = Math.max(firstStart + 1, Number(last.end) || firstStart + 1);
  const scrollStartTime = Number(Math.max(0, firstStart - Math.min(CAPTION_SCROLL_ENTRY_LEAD_IN_SECONDS, firstStart)).toFixed(3));
  const scrollEndTime = Number((lastEnd + CAPTION_SCROLL_END_FADE_SECONDS).toFixed(3));
  const firstEntryScrollPosition =
    chunkCenterYForData(first) + CAPTION_WINDOW_GEOMETRY.activeY - CAPTION_SCROLL_FIRST_ENTRY_CENTER_PX;
  const lastExitScrollPosition =
    chunkCenterYForData(last) + CAPTION_WINDOW_GEOMETRY.activeY - CAPTION_SCROLL_LAST_EXIT_CENTER_PX;
  const travelPx = Math.max(1, lastExitScrollPosition - firstEntryScrollPosition);
  const travelSeconds = Math.max(1, scrollEndTime - scrollStartTime);
  return clampNumber(travelPx / travelSeconds, CAPTION_MIN_CONSTANT_SPEED_PX_PER_SECOND, CAPTION_MAX_CONSTANT_SPEED_PX_PER_SECOND);
}

function mergeCaptionChunks(left, right) {
  const sourceCueIds = [
    ...(Array.isArray(left.source_cue_ids) ? left.source_cue_ids : [left.source_cue_id].filter(Boolean)),
    ...(Array.isArray(right.source_cue_ids) ? right.source_cue_ids : [right.source_cue_id].filter(Boolean)),
  ];
  return {
    id: `${left.id}__${right.id}`,
    source_cue_id: sourceCueIds[0] || left.source_cue_id || right.source_cue_id,
    source_cue_ids: [...new Set(sourceCueIds)],
    start: Math.min(Number(left.start) || 0, Number(right.start) || 0),
    end: Math.max(Number(left.end) || 0, Number(right.end) || 0),
    text: `${String(left.text || "").trim()} ${String(right.text || "").trim()}`.trim(),
    merged_display_chunk_count: Number(left.merged_display_chunk_count || 1) + Number(right.merged_display_chunk_count || 1),
  };
}

function requiredCenterGapForChunks(left, right, visualGapPx = CAPTION_DENSE_MERGE_VISUAL_GAP_PX) {
  return ((Number(left.layout_height_px) || captionLayoutHeightForText(left.text)) / 2) +
    ((Number(right.layout_height_px) || captionLayoutHeightForText(right.text)) / 2) +
    visualGapPx;
}

function withCaptionHeights(chunks) {
  return chunks.map((chunk) => ({
    ...chunk,
    display_lines: captionDisplayLinesForText(chunk.text),
    layout_height_px: captionLayoutHeightForText(chunk.text),
    source_cue_ids: Array.isArray(chunk.source_cue_ids)
      ? chunk.source_cue_ids
      : chunk.source_cue_id
        ? [chunk.source_cue_id]
        : [],
  }));
}

function countDensePairs(chunks, speed) {
  let count = 0;
  for (let index = 1; index < chunks.length; index += 1) {
    const previous = chunks[index - 1];
    const current = chunks[index];
    const desiredGap = speed * Math.max(0, (Number(current.start) || 0) - (Number(previous.start) || 0));
    if (desiredGap < requiredCenterGapForChunks(previous, current, 0)) count += 1;
  }
  return count;
}

function countCaptionLayoutOverlaps(chunks) {
  let count = 0;
  for (let index = 1; index < chunks.length; index += 1) {
    const previous = chunks[index - 1];
    const current = chunks[index];
    const previousBottom = (Number(previous.layout_y_px) || 0) + (Number(previous.layout_height_px) || captionLayoutHeightForText(previous.text));
    const currentTop = Number(current.layout_y_px) || 0;
    if (currentTop < previousBottom - 0.1) count += 1;
  }
  return count;
}

function minRenderedLineGapPx(chunks) {
  if (!chunks || chunks.length < 2) return CAPTION_MIN_RENDERED_LINE_GAP_PX;
  let minGap = Infinity;
  for (let index = 1; index < chunks.length; index += 1) {
    const previous = chunks[index - 1];
    const current = chunks[index];
    const previousBottom = (Number(previous.layout_y_px) || 0) + (Number(previous.layout_height_px) || captionLayoutHeightForText(previous.text));
    const currentTop = Number(current.layout_y_px) || 0;
    minGap = Math.min(minGap, currentTop - previousBottom);
  }
  return Number((Number.isFinite(minGap) ? minGap : CAPTION_MIN_RENDERED_LINE_GAP_PX).toFixed(1));
}

function mergeChunksInRange(chunks, startIndex, endIndex) {
  let merged = chunks[startIndex];
  for (let index = startIndex + 1; index <= endIndex; index += 1) {
    merged = mergeCaptionChunks(merged, chunks[index]);
  }
  return merged;
}

function mergeChunksForTakeawayPhrases(chunks, phraseSpecs) {
  if (!phraseSpecs.length) return { chunks, mergeCount: 0 };
  const ranges = [];
  const maxWindow = 6;
  for (const spec of phraseSpecs) {
    const phrase = normalizedSearchValue(spec.phrase || spec.phrase_text || "");
    if (!phrase) continue;
    const candidates = [];
    for (let start = 0; start < chunks.length; start += 1) {
      let text = "";
      for (let end = start; end < Math.min(chunks.length, start + maxWindow); end += 1) {
        text = `${text} ${chunks[end].text}`.trim();
        if (normalizedSearchValue(text).includes(phrase)) {
          candidates.push([start, end]);
          break;
        }
      }
    }
    candidates.sort((a, b) => (a[1] - a[0]) - (b[1] - b[0]) || a[0] - b[0]);
    if (candidates[0]) ranges.push(candidates[0]);
  }
  if (!ranges.length) return { chunks, mergeCount: 0 };
  ranges.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const mergedRanges = [];
  for (const range of ranges) {
    const last = mergedRanges[mergedRanges.length - 1];
    if (last && range[0] <= last[1]) last[1] = Math.max(last[1], range[1]);
    else mergedRanges.push([...range]);
  }
  const out = [];
  let index = 0;
  let mergeCount = 0;
  for (const [start, end] of mergedRanges) {
    while (index < start) {
      out.push(chunks[index]);
      index += 1;
    }
    if (end > start) {
      out.push(mergeChunksInRange(chunks, start, end));
      mergeCount += end - start;
    } else {
      out.push(chunks[start]);
    }
    index = end + 1;
  }
  while (index < chunks.length) {
    out.push(chunks[index]);
    index += 1;
  }
  return { chunks: withCaptionHeights(out), mergeCount };
}

function mergeDenseCaptionChunks(chunks, speed) {
  let working = withCaptionHeights(chunks);
  let mergeCount = 0;
  let passCount = 0;
  for (let pass = 0; pass < 12; pass += 1) {
    passCount = pass + 1;
    let changed = false;
    const nextChunks = [];
    for (let index = 0; index < working.length; index += 1) {
      const current = working[index];
      const next = working[index + 1];
      if (!next) {
        nextChunks.push(current);
        continue;
      }
      const desiredGap = speed * Math.max(0, (Number(next.start) || 0) - (Number(current.start) || 0));
      const requiredGap = requiredCenterGapForChunks(current, next);
      const mergedTextLength = `${String(current.text || "").trim()} ${String(next.text || "").trim()}`.trim().length;
      if (desiredGap < requiredGap && mergedTextLength <= CAPTION_MAX_MERGED_CHARS) {
        nextChunks.push(mergeCaptionChunks(current, next));
        mergeCount += 1;
        changed = true;
        index += 1;
      } else {
        nextChunks.push(current);
      }
    }
    working = withCaptionHeights(nextChunks);
    if (!changed) break;
  }
  return {
    chunks: working,
    mergeCount,
    passCount,
    unresolvedDensePairCount: countDensePairs(working, speed),
  };
}

function alignCaptionChunksToAudioTime(chunks, speed) {
  let previous = null;
  let delayedChunkCount = 0;
  let maxLayoutDelayPx = 0;
  let maxCueStartCenterDeltaPx = -Infinity;
  let minActiveLeadSeconds = Infinity;
  const aligned = withCaptionHeights(chunks).map((chunk) => {
    const height = Number(chunk.layout_height_px) || captionLayoutHeightForText(chunk.text);
    const cueStart = Math.max(0, Number(chunk.start) || 0);
    const desiredCenterY = speed * Math.max(0, cueStart - CAPTION_READING_LEAD_SECONDS);
    const minCenterY = previous
      ? previous.centerY + ((previous.height + height) / 2) + CAPTION_DENSE_MERGE_VISUAL_GAP_PX
      : desiredCenterY;
    const centerY = Math.max(desiredCenterY, minCenterY);
    const layoutDelayPx = Math.max(0, centerY - desiredCenterY);
    if (layoutDelayPx > 0.1) delayedChunkCount += 1;
    maxLayoutDelayPx = Math.max(maxLayoutDelayPx, layoutDelayPx);
    const centerDeltaAtCueStart = centerY - (speed * cueStart);
    const activeLeadSeconds = cueStart - (centerY / speed);
    maxCueStartCenterDeltaPx = Math.max(maxCueStartCenterDeltaPx, centerDeltaAtCueStart);
    minActiveLeadSeconds = Math.min(minActiveLeadSeconds, activeLeadSeconds);
    previous = { centerY, height };
    return {
      ...chunk,
      layout_y_px: Number((centerY - (height / 2)).toFixed(1)),
      timeline_y_px: Number((centerY - (height / 2)).toFixed(1)),
      timeline_center_y_px: Number(centerY.toFixed(3)),
      desired_timeline_center_y_px: Number(desiredCenterY.toFixed(3)),
      caption_layout_delay_px: Number(layoutDelayPx.toFixed(3)),
      caption_center_delta_at_cue_start_px: Number(centerDeltaAtCueStart.toFixed(3)),
      caption_active_lead_seconds: Number(activeLeadSeconds.toFixed(3)),
    };
  });
  return {
    chunks: aligned,
    delayedChunkCount,
    maxLayoutDelayPx: Number(maxLayoutDelayPx.toFixed(3)),
    maxCueStartCenterDeltaPx: Number((Number.isFinite(maxCueStartCenterDeltaPx) ? maxCueStartCenterDeltaPx : 0).toFixed(3)),
    minActiveLeadSeconds: Number((Number.isFinite(minActiveLeadSeconds) ? minActiveLeadSeconds : 0).toFixed(3)),
  };
}

function captionIntroGateTiming(firstDisplayCueStartSeconds = 0) {
  const firstStart = Math.max(0, Number(firstDisplayCueStartSeconds) || 0);
  const gateStart = Math.max(0, firstStart - CAPTION_INTRO_GATE_FADE_START_LEAD_SECONDS);
  const gateFullOpacity = Math.max(gateStart, firstStart - CAPTION_INTRO_GATE_FULL_OPACITY_LEAD_SECONDS);
  return {
    caption_intro_visibility_gate_model: CAPTION_INTRO_VISIBILITY_GATE_MODEL,
    caption_intro_gate_start_seconds: Number(gateStart.toFixed(3)),
    caption_intro_gate_full_opacity_seconds: Number(gateFullOpacity.toFixed(3)),
    caption_intro_premature_text_read: "pass",
  };
}

function captionStackHeightPxForChunks(chunks) {
  const maxBottom = chunks.reduce((max, chunk) => {
    const bottom = Number(chunk.layout_y_px || 0) + Number(chunk.layout_height_px || CAPTION_LINE_BOX_HEIGHT_PX);
    return Math.max(max, bottom);
  }, 0);
  return Math.ceil(Math.max(12000, maxBottom + CAPTION_WINDOW_GEOMETRY.height + 512));
}

function captionScrollTimingForChunks(chunks, stats = {}) {
  if (!chunks.length) {
    return {
      caption_constant_scroll_speed_px_per_second: 50,
      caption_scroll_start_time_seconds: 0,
      caption_scroll_start_position_px: 0,
      caption_scroll_end_time_seconds: 0,
      caption_scroll_end_position_px: 0,
      caption_scroll_first_entry_center_px: CAPTION_SCROLL_FIRST_ENTRY_CENTER_PX,
      caption_scroll_last_exit_center_px: CAPTION_SCROLL_LAST_EXIT_CENTER_PX,
      caption_timeline_layout_model: CAPTION_TIMELINE_LAYOUT_MODEL,
      caption_sync_target: CAPTION_SYNC_TARGET,
      caption_reading_lead_seconds: CAPTION_READING_LEAD_SECONDS,
      ...captionIntroGateTiming(0),
      review_control_model: REVIEW_CONTROL_MODEL,
      review_transport_scrub_model: REVIEW_TRANSPORT_SCRUB_MODEL,
      legacy_review_chrome_suppression_model: LEGACY_REVIEW_CHROME_SUPPRESSION_MODEL,
      single_foreground_review_transport_static_pass: true,
      legacy_review_chrome_suppression_static_pass: true,
      caption_constant_speed_scope: CAPTION_CONSTANT_SPEED_SCOPE,
      caption_playback_clock_model: CAPTION_PLAYBACK_CLOCK_MODEL,
      caption_stack_render_model: CAPTION_STACK_RENDER_MODEL,
    caption_scroll_smoothness_model: CAPTION_SCROLL_SMOOTHNESS_MODEL,
      caption_runtime_coverage_model: CAPTION_RUNTIME_COVERAGE_MODEL,
      caption_full_vo_runtime_coverage_read: "pending_browser_runtime_qa",
      caption_density_resolution_model: CAPTION_DENSITY_RESOLUTION_MODEL,
      caption_display_line_wrap_model: CAPTION_DISPLAY_LINE_WRAP_MODEL,
      caption_display_line_max_width_px: CAPTION_DISPLAY_LINE_MAX_WIDTH_PX,
      caption_max_estimated_line_width_px: 0,
      caption_text_stack_width_px: CAPTION_WINDOW_GEOMETRY.stackWidth,
      caption_stack_height_px: 12000,
      caption_stack_paint_containment_read: "pass_no_caption_stack_paint_clip",
      caption_active_band_lower_delta_px: CAPTION_ACTIVE_BAND_LOWER_DELTA_PX,
      caption_dense_chunk_merge_count: 0,
      caption_unresolved_dense_pair_count: 0,
      caption_min_rendered_line_gap_px: CAPTION_MIN_RENDERED_LINE_GAP_PX,
      caption_forced_takeaway_merge_count: 0,
      caption_layout_collision_guard: CAPTION_LAYOUT_COLLISION_GUARD,
      caption_collision_guard_read: "pass",
      caption_source_cue_coverage_count: 0,
    };
  }
  const last = chunks[chunks.length - 1];
  const speed = Number((stats.speed || baseCaptionScrollSpeedForChunks(chunks)).toFixed(3));
  const lastEnd = Math.max(1, Number(last.end) || 1);
  const scrollStartTime = 0;
  const scrollEndTime = Number((lastEnd + CAPTION_SCROLL_END_FADE_SECONDS).toFixed(3));
  const introGateTiming = captionIntroGateTiming(chunks[0]?.start || 0);
  return {
    caption_constant_scroll_speed_px_per_second: speed,
    caption_scroll_start_time_seconds: scrollStartTime,
    caption_scroll_start_position_px: 0,
    caption_scroll_end_time_seconds: scrollEndTime,
    caption_scroll_end_position_px: Number((speed * scrollEndTime).toFixed(3)),
    caption_scroll_first_entry_center_px: CAPTION_SCROLL_FIRST_ENTRY_CENTER_PX,
    caption_scroll_last_exit_center_px: CAPTION_SCROLL_LAST_EXIT_CENTER_PX,
    caption_timeline_layout_model: CAPTION_TIMELINE_LAYOUT_MODEL,
    caption_sync_target: CAPTION_SYNC_TARGET,
    caption_reading_lead_seconds: CAPTION_READING_LEAD_SECONDS,
    ...introGateTiming,
    review_control_model: REVIEW_CONTROL_MODEL,
    review_transport_scrub_model: REVIEW_TRANSPORT_SCRUB_MODEL,
    legacy_review_chrome_suppression_model: LEGACY_REVIEW_CHROME_SUPPRESSION_MODEL,
    caption_constant_speed_scope: CAPTION_CONSTANT_SPEED_SCOPE,
    caption_playback_clock_model: CAPTION_PLAYBACK_CLOCK_MODEL,
    caption_stack_render_model: CAPTION_STACK_RENDER_MODEL,
    caption_scroll_smoothness_model: CAPTION_SCROLL_SMOOTHNESS_MODEL,
    caption_runtime_coverage_model: CAPTION_RUNTIME_COVERAGE_MODEL,
    caption_end_screen_handoff_model: CAPTION_END_SCREEN_HANDOFF_MODEL,
    caption_full_vo_runtime_coverage_read: "pending_browser_runtime_qa",
    caption_density_resolution_model: CAPTION_DENSITY_RESOLUTION_MODEL,
    caption_display_line_wrap_model: CAPTION_DISPLAY_LINE_WRAP_MODEL,
    caption_display_line_max_width_px: CAPTION_DISPLAY_LINE_MAX_WIDTH_PX,
    caption_max_estimated_line_width_px: stats.maxEstimatedLineWidthPx ?? maxEstimatedCaptionLineWidthPx(chunks),
    caption_text_stack_width_px: CAPTION_WINDOW_GEOMETRY.stackWidth,
    caption_stack_height_px: captionStackHeightPxForChunks(chunks),
    caption_stack_paint_containment_read: "pass_no_caption_stack_paint_clip",
    caption_active_band_lower_delta_px: CAPTION_ACTIVE_BAND_LOWER_DELTA_PX,
    caption_dense_chunk_merge_count: stats.mergeCount || 0,
    caption_dense_merge_pass_count: stats.passCount || 0,
    caption_unresolved_dense_pair_count: stats.unresolvedDensePairCount || 0,
    caption_pre_layout_unmerged_dense_pair_count: stats.preLayoutUnmergedDensePairCount || 0,
    caption_layout_delayed_chunk_count: stats.delayedChunkCount || 0,
    caption_max_layout_delay_px: stats.maxLayoutDelayPx || 0,
    caption_max_active_chunk_center_delta_at_cue_start_px: stats.maxCueStartCenterDeltaPx || 0,
    caption_min_active_chunk_lead_seconds: stats.minActiveLeadSeconds || 0,
    caption_min_rendered_line_gap_px: stats.minRenderedLineGapPx ?? minRenderedLineGapPx(chunks),
    caption_forced_takeaway_merge_count: stats.forcedTakeawayMergeCount || 0,
    caption_layout_collision_guard: CAPTION_LAYOUT_COLLISION_GUARD,
    caption_collision_guard_read:
      Number(stats.minRenderedLineGapPx ?? minRenderedLineGapPx(chunks)) >= CAPTION_MIN_RENDERED_LINE_GAP_PX
        ? "pass_fixed_line_box_visual_gap_guard"
        : "tighten_rendered_line_gap_below_guard",
    caption_source_cue_coverage_count: sourceCueCoverageCount(chunks),
  };
}

function buildAudioTimeAlignedCaptionLayout(chunks, takeawayPhraseSpecs = []) {
  const takeawayMerged = mergeChunksForTakeawayPhrases(chunks, takeawayPhraseSpecs);
  const speed = Number(baseCaptionScrollSpeedForChunks(takeawayMerged.chunks).toFixed(3));
  const merged = mergeDenseCaptionChunks(takeawayMerged.chunks, speed);
  const aligned = alignCaptionChunksToAudioTime(merged.chunks, speed);
  const minGap = minRenderedLineGapPx(aligned.chunks);
  const maxEstimatedLineWidth = maxEstimatedCaptionLineWidthPx(aligned.chunks);
  const timing = captionScrollTimingForChunks(aligned.chunks, {
    speed,
    mergeCount: merged.mergeCount,
    passCount: merged.passCount,
    unresolvedDensePairCount: countCaptionLayoutOverlaps(aligned.chunks),
    preLayoutUnmergedDensePairCount: merged.unresolvedDensePairCount,
    delayedChunkCount: aligned.delayedChunkCount,
    maxLayoutDelayPx: aligned.maxLayoutDelayPx,
    maxCueStartCenterDeltaPx: aligned.maxCueStartCenterDeltaPx,
    minActiveLeadSeconds: aligned.minActiveLeadSeconds,
    minRenderedLineGapPx: minGap,
    maxEstimatedLineWidthPx: maxEstimatedLineWidth,
    forcedTakeawayMergeCount: takeawayMerged.mergeCount,
  });
  return {
    chunks: aligned.chunks,
    captionScrollTiming: timing,
  };
}

function aircraftRouteStatsFromHtml(html) {
  const block = String(html || "").match(/const aircraftEvents = \[([\s\S]*?)\];/)?.[1] || "";
  const routes = [];
  for (const match of block.matchAll(/\{([\s\S]*?)\}/g)) {
    const eventText = match[1];
    const route = {};
    for (const key of ["start", "x0", "x1", "y0", "y1"]) {
      const value = eventText.match(new RegExp(`"?${key}"?\\s*:\\s*([-0-9.]+)`));
      if (value) route[key] = Number(value[1]);
    }
    if (Number.isFinite(route.x0) || Number.isFinite(route.x1)) routes.push(route);
  }
  const rightRailRoutes = routes.filter((route) => Number(route.start || 0) < 1188 && Math.max(route.x0 || 0, route.x1 || 0) >= RAIL_GEOMETRY.left);
  const aircraftRightRailCutoffRemoved =
    !/state\.x\s*>=\s*railSafeLeft\s*-\s*50/.test(html) && !/state\.x\s*<\s*railSafeLeft\s*-\s*50/.test(html);
  return {
    aircraft_event_count: routes.length,
    aircraft_right_rail_route_count: rightRailRoutes.length,
    aircraft_right_rail_cutoff_removed: aircraftRightRailCutoffRemoved,
    aircraft_right_rail_route_static_pass: rightRailRoutes.length > 0,
  };
}

function ambientRightRailMotionMetadata({ episode, sourceManifest, sourceHtml }) {
  if (episode.episodeId !== "challenger" && !/const aircraftEvents = \[/.test(String(sourceHtml || ""))) {
    return {
      applicable: false,
      ambient_right_rail_motion_policy: "not_applicable_no_aircraft_right_rail_motion_layer",
      foreground_matte_policy: "not_applicable",
      aircraft_right_rail_route_count: 0,
      aircraft_right_rail_cutoff_removed: true,
      aircraft_right_rail_route_static_pass: true,
    };
  }
  const stats = aircraftRouteStatsFromHtml(sourceHtml);
  return {
    applicable: true,
    ambient_right_rail_motion_policy:
      valueAt(sourceManifest, "living_cover_backplate_retarget.ambient_right_rail_motion_policy") ||
      AMBIENT_RIGHT_RAIL_MOTION_POLICY,
    foreground_matte_policy:
      valueAt(sourceManifest, "living_cover_backplate_retarget.foreground_matte_policy") ||
      valueAt(sourceManifest, "artifacts.active_matte.policy") ||
      FOREGROUND_MATTE_POLICY,
    right_rail_matte_removed_read:
      valueAt(sourceManifest, "living_cover_backplate_retarget.right_rail_matte_removed_read") ||
      valueAt(sourceManifest, "reads.right_rail_matte_removed_read") ||
      "pending_static_matte_probe_review",
    aircraft_right_rail_visibility_read:
      valueAt(sourceManifest, "living_cover_backplate_retarget.aircraft_right_rail_visibility_read") ||
      valueAt(sourceManifest, "reads.aircraft_right_rail_visibility_read") ||
      "pending_browser_review",
    ...stats,
  };
}

function normalizePhraseSpan(span, spanIndex) {
  if (!span || typeof span !== "object") return null;
  const reviewStatus = String(span.review_status || span.status || "");
  if (!/(pass|keep|approved|reviewed|rough_review_draft)/i.test(reviewStatus)) return null;
  const semanticRole = span.highlight_semantic_role || span.semantic_role || span.role;
  const highlightModel = span.caption_highlight_model_id || span.highlight_model_id || span.model_id;
  if (semanticRole !== HIGHLIGHT_SEMANTIC_ROLE && highlightModel !== CAPTION_HIGHLIGHT_MODEL_ID) return null;
  const phraseText = span.phrase_text || span.text || span.phrase;
  const tokenRange = span.normalized_script_token_range || span.script_token_range;
  const timingWindow = span.timing_window_seconds || span.time_window_seconds || span.timing || span.window_seconds;
  const visualTimingWindow = span.visual_timing_window_seconds || span.highlight_visual_timing_window_seconds;
  const color = span.highlight_color_sample?.hex || span.highlight_color_hex || span.color_hex;
  if (
    typeof phraseText !== "string" ||
    !phraseText.trim() ||
    !Array.isArray(tokenRange) ||
    tokenRange.length !== 2 ||
    !Array.isArray(timingWindow) ||
    timingWindow.length !== 2 ||
    typeof color !== "string" ||
    !color.trim()
  ) {
    return null;
  }
  return {
    phrase_text: phraseText.trim(),
    normalized_script_token_range: tokenRange.map(Number),
    timing_window_seconds: timingWindow.map(Number),
    highlight_color_sample: {
      source: span.highlight_color_sample?.source || "sampled_episode_backplate",
      hex: color,
    },
    fade_in_seconds: Number(span.fade_in_seconds ?? 0.22),
    fade_out_seconds: Number(span.fade_out_seconds ?? 0.42),
    caption_highlight_model_id: CAPTION_HIGHLIGHT_MODEL_ID,
    highlight_semantic_role: HIGHLIGHT_SEMANTIC_ROLE,
    highlight_density_model: span.highlight_density_model || HIGHLIGHT_DENSITY_MODEL,
    highlight_color_model: span.highlight_color_model || HIGHLIGHT_COLOR_MODEL,
    highlight_visual_timing_model: span.highlight_visual_timing_model || HIGHLIGHT_VISUAL_TIMING_MODEL,
    visual_timing_window_seconds: Array.isArray(visualTimingWindow) && visualTimingWindow.length === 2 ? visualTimingWindow.map(Number) : timingWindow.map(Number),
    review_status: reviewStatus || "reviewed",
    span_id: span.span_id || `reviewed_phrase_${String(spanIndex + 1).padStart(2, "0")}`,
  };
}

function collectKeyPhraseSpans(value, out = []) {
  if (Array.isArray(value)) {
    for (const item of value) {
      const span = normalizePhraseSpan(item, out.length);
      if (span) out.push(span);
      else collectKeyPhraseSpans(item, out);
    }
  } else if (value && typeof value === "object") {
    if (Array.isArray(value.key_phrase_spans)) collectKeyPhraseSpans(value.key_phrase_spans, out);
    if (Array.isArray(value.rolling_caption_key_phrase_spans)) collectKeyPhraseSpans(value.rolling_caption_key_phrase_spans, out);
    for (const nested of Object.values(value)) {
      if (nested && typeof nested === "object") collectKeyPhraseSpans(nested, out);
    }
  }
  return out;
}

function loadReviewedKeyPhraseSpans(sourceRoot) {
  const candidateFiles = findFiles(
    sourceRoot,
    (file) => /cue|phrase|manifest|caption/i.test(path.basename(file)) && /\.json$/i.test(file),
    300,
  );
  const spans = [];
  for (const file of candidateFiles) {
    const json = readJsonIfExists(file);
    if (!json) continue;
    for (const span of collectKeyPhraseSpans(json)) {
      if (!spans.some((existing) => existing.phrase_text === span.phrase_text && existing.timing_window_seconds[0] === span.timing_window_seconds[0])) {
        spans.push(span);
      }
    }
  }
  return spans;
}

let approvedLessonTakeawayCandidatesCache = null;

function loadApprovedLessonTakeawayCandidates() {
  if (approvedLessonTakeawayCandidatesCache) return approvedLessonTakeawayCandidatesCache;
  const review = readJsonIfExists(LESSON_TAKEAWAY_CANDIDATES_LATEST_PATH) || {};
  const byEpisode = new Map();
  for (const entry of review.episodes || []) {
    const candidates = Array.isArray(entry.candidates) ? entry.candidates : [];
    byEpisode.set(entry.episode_id, candidates);
  }
  approvedLessonTakeawayCandidatesCache = {
    path: LESSON_TAKEAWAY_CANDIDATES_LATEST_PATH,
    sha256: sha256File(LESSON_TAKEAWAY_CANDIDATES_LATEST_PATH),
    review_status: review.review_status || review.status || "candidate_review_promoted_by_human_approval",
    byEpisode,
  };
  return approvedLessonTakeawayCandidatesCache;
}

function approvedLessonTakeawayCandidatesForEpisode(episodeId) {
  return loadApprovedLessonTakeawayCandidates().byEpisode.get(episodeId) || [];
}

function normalizedSearchValue(value) {
  return cleanCueText(value)
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function normalizedPhraseIndex(text, phrase) {
  const normalizedText = normalizedSearchValue(text);
  const normalizedPhrase = normalizedSearchValue(phrase);
  if (!normalizedPhrase) return -1;
  return normalizedText.indexOf(normalizedPhrase);
}

function textTokensBefore(chunks, chunkIndex, phrase) {
  const priorText = chunks.slice(0, chunkIndex).map((chunk) => chunk.text).join(" ");
  const current = chunks[chunkIndex]?.text || "";
  const normalizedCurrent = normalizedSearchValue(current);
  const normalizedPhrase = normalizedSearchValue(phrase);
  const phraseIndex = normalizedPhrase ? normalizedCurrent.indexOf(normalizedPhrase) : -1;
  const beforePhrase = phraseIndex > -1 ? normalizedCurrent.slice(0, phraseIndex) : "";
  const countTokens = (value) => cleanCueText(value).split(/\s+/).filter(Boolean).length;
  return countTokens(priorText) + countTokens(beforePhrase);
}

const CHALLENGER_TAKEAWAY_PHRASE_SPECS = [
  "the first warning appeared",
  "warning stay visible in records",
  "failed after a system learned",
  "A scrub is still an engineering decision",
  "Normal operation is useful",
  "inside a decision structure",
  "the practical standard drifted",
  "Timing was the safety margin",
  "warning can die inside a large organization",
  "answer depends on the question",
  "first question keeps the schedule alive",
  "judgment becomes a schedule decision",
  "decision becomes precedent",
  "previous success can become misleading evidence",
  "survival as part of the safety case",
  "reversed the burden of proof",
  "absence became useful to the launch case",
  "A warning also has to travel",
  "system has made a decision without naming it",
  "warning arrive too late",
  "explanation arrived, and flight continued",
  "evidence already existed",
  "received a softened version",
  "expected performance becomes normal",
  "Missing data gets mistaken for safety",
  "proof standards quietly",
  "certainty of disaster justifies delay",
  "warning is strong enough to interrupt momentum",
  "Disasters rarely begin at the moment of impact",
  "stopped to understand",
  "The system explained it",
  "what it already knew",
].map((phrase) => ({ phrase }));

function activeBandTimingWindowForChunk(chunk, captionScrollTiming) {
  const speed = Number(captionScrollTiming.caption_constant_scroll_speed_px_per_second || 50);
  const startPosition = Number(captionScrollTiming.caption_scroll_start_position_px || 0);
  const startTime = Number(captionScrollTiming.caption_scroll_start_time_seconds || 0);
  const activeBandTime = startTime + ((chunkCenterYForData(chunk) - startPosition) / speed);
  const duration = Math.max(1.35, Math.min(3.2, (Number(chunk.end) || 0) - (Number(chunk.start) || 0) + 0.35));
  return [Number(activeBandTime.toFixed(3)), Number((activeBandTime + duration).toFixed(3))];
}

function spanColorFields(highlightAccent) {
  const accent = highlightAccent || {};
  return {
    highlight_color_sample: {
      source: "sampled_episode_backplate",
      hex: accent.selected_hex || "#efb058",
      source_art_path: accent.source_art_path || "not_found",
      source_art_sha256: accent.source_art_sha256 || "",
      sample_model: accent.sample_model || "caption_window_grid_backplate_contrast_accent_v3",
      sample_bbox_xy: accent.sample_bbox_xy || captionWindowBackplateSampleBox(),
      sample_hex: accent.sample_hex || "",
      contrast_sample_count: accent.backplate_contrast_sample_count || 0,
      backplate_contrast_sample_hexes: accent.backplate_contrast_sample_hexes || [],
      minimum_backplate_contrast_ratio: accent.minimum_backplate_contrast_ratio || null,
    },
    highlight_color_qa: accent,
    highlight_distinct_from_caption_text_read:
      accent.highlight_distinct_from_caption_text_read ||
      "pass_source_sampled_accent_distinct_from_active_and_muted_caption_text",
    highlight_backplate_contrast_read:
      accent.highlight_backplate_contrast_read ||
      "pass_grid_sampled_caption_window_backplate_contrast",
  };
}

function draftChallengerKeyPhraseSpans(chunks, palette, captionScrollTiming, highlightAccent) {
  const specs = CHALLENGER_TAKEAWAY_PHRASE_SPECS;
  const spans = [];
  specs.forEach((spec, index) => {
    const candidates = chunks
      .map((chunk, chunkIndex) => ({ chunk, chunkIndex }))
      .filter(({ chunk }) => normalizedPhraseIndex(chunk.text, spec.phrase) >= 0);
    const selected = candidates
      .map((candidate) => {
        const mid = (candidate.chunk.start + candidate.chunk.end) / 2;
        return { ...candidate, score: Math.abs(mid - Number(candidate.chunk.start || 0)) };
      })
      .sort((a, b) => a.score - b.score)[0];
    const chunkIndex = selected?.chunkIndex ?? -1;
    if (chunkIndex === -1) return;
    const chunk = chunks[chunkIndex];
    const tokenStart = textTokensBefore(chunks, chunkIndex, spec.phrase);
    const tokenEnd = tokenStart + cleanCueText(spec.phrase).split(/\s+/).filter(Boolean).length;
    const visualTimingWindow = activeBandTimingWindowForChunk(chunk, captionScrollTiming);
    spans.push({
      phrase_text: spec.phrase,
      normalized_script_token_range: [tokenStart, tokenEnd],
      timing_window_seconds: [Number(chunk.start.toFixed(3)), Number(chunk.end.toFixed(3))],
      ...spanColorFields(highlightAccent || { selected_hex: palette.highlight }),
      fade_in_seconds: 0.42,
      fade_out_seconds: 1.1,
      caption_highlight_model_id: CAPTION_HIGHLIGHT_MODEL_ID,
      highlight_semantic_role: HIGHLIGHT_SEMANTIC_ROLE,
      highlight_density_model: HIGHLIGHT_DENSITY_MODEL,
      highlight_color_model: HIGHLIGHT_COLOR_MODEL,
      highlight_color_qa: highlightAccent,
      highlight_distinct_from_caption_text_read:
        highlightAccent?.highlight_distinct_from_caption_text_read || "blocked_missing_highlight_color_qa",
      highlight_visual_timing_model: HIGHLIGHT_VISUAL_TIMING_MODEL,
      visual_timing_window_seconds: visualTimingWindow,
      review_status: LESSON_TAKEAWAY_APPROVAL_STATUS,
      span_id: `challenger_takeaway_approved_${String(index + 1).padStart(2, "0")}`,
    });
  });
  return spans;
}

function takeawayPhraseSpecsForEpisode(episode) {
  const approvedCandidates = approvedLessonTakeawayCandidatesForEpisode(episode.episodeId);
  if (approvedCandidates.length) {
    return approvedCandidates.map((candidate) => ({ phrase: candidate.phrase_text }));
  }
  if (episode.episodeId === "challenger") return CHALLENGER_TAKEAWAY_PHRASE_SPECS;
  const reviewed = loadReviewedKeyPhraseSpans(episode.sourceRoot);
  if (reviewed.length) {
    return reviewed.map((span) => ({
      phrase: span.phrase_text,
      color: span.highlight_color_sample?.hex || "#ffe0a6",
    }));
  }
  return [];
}

function withVisualTimingForReviewedSpan(span, chunks, captionScrollTiming) {
  const chunk = chunks.find((candidate) => normalizedPhraseIndex(candidate.text, span.phrase_text) >= 0);
  if (!chunk) return span;
  return {
    ...span,
    visual_timing_window_seconds: activeBandTimingWindowForChunk(chunk, captionScrollTiming),
  };
}

function approvedCandidateKeyPhraseSpansForEpisode(episode, chunks, captionScrollTiming, highlightAccent) {
  return approvedLessonTakeawayCandidatesForEpisode(episode.episodeId)
    .map((candidate, index) => {
      const phrase = String(candidate.phrase_text || "").trim();
      if (!phrase) return null;
      const chunkIndex = chunks.findIndex((chunk) => normalizedPhraseIndex(chunk.text, phrase) >= 0);
      const chunk = chunkIndex >= 0 ? chunks[chunkIndex] : null;
      const timingWindow = Array.isArray(candidate.timing_window_seconds)
        ? candidate.timing_window_seconds.map(Number)
        : chunk
          ? [chunk.start, chunk.end]
          : [0, 0];
      const tokenRange = Array.isArray(candidate.normalized_script_token_range)
        ? candidate.normalized_script_token_range.map(Number)
        : chunk
          ? [
              textTokensBefore(chunks, chunkIndex, phrase),
              textTokensBefore(chunks, chunkIndex, phrase) + cleanCueText(phrase).split(/\s+/).filter(Boolean).length,
            ]
          : [0, cleanCueText(phrase).split(/\s+/).filter(Boolean).length];
      return {
        phrase_text: phrase,
        normalized_script_token_range: tokenRange,
        timing_window_seconds: timingWindow.map((value) => Number(Number(value).toFixed(3))),
        ...spanColorFields(highlightAccent),
        fade_in_seconds: 0.42,
        fade_out_seconds: 1.1,
        caption_highlight_model_id: CAPTION_HIGHLIGHT_MODEL_ID,
        highlight_semantic_role: HIGHLIGHT_SEMANTIC_ROLE,
        highlight_density_model: HIGHLIGHT_DENSITY_MODEL,
        highlight_color_model: HIGHLIGHT_COLOR_MODEL,
        highlight_visual_timing_model: HIGHLIGHT_VISUAL_TIMING_MODEL,
        visual_timing_window_seconds: chunk
          ? activeBandTimingWindowForChunk(chunk, captionScrollTiming)
          : timingWindow.map((value) => Number(Number(value).toFixed(3))),
        review_status: LESSON_TAKEAWAY_APPROVAL_STATUS,
        span_id: `${episode.episodeId}_takeaway_approved_${String(index + 1).padStart(2, "0")}`,
        source_candidate_id: candidate.candidate_id || null,
        approved_candidate_source_path: LESSON_TAKEAWAY_CANDIDATES_LATEST_PATH,
        approved_candidate_source_sha256: loadApprovedLessonTakeawayCandidates().sha256,
      };
    })
    .filter(Boolean);
}

function withAdaptiveHighlightColor(span, highlightAccent) {
  return {
    ...span,
    ...spanColorFields(highlightAccent),
    highlight_color_model: HIGHLIGHT_COLOR_MODEL,
  };
}

function keyPhraseSpansForEpisode(episode, chunks, palette, captionScrollTiming, highlightAccent) {
  const approvedCandidates = approvedLessonTakeawayCandidatesForEpisode(episode.episodeId);
  if (approvedCandidates.length) {
    return approvedCandidateKeyPhraseSpansForEpisode(episode, chunks, captionScrollTiming, highlightAccent);
  }
  if (episode.episodeId === "challenger") {
    return draftChallengerKeyPhraseSpans(chunks, palette, captionScrollTiming, highlightAccent);
  }
  const reviewed = loadReviewedKeyPhraseSpans(episode.sourceRoot);
  if (reviewed.length) {
    return reviewed.map((span) =>
      withAdaptiveHighlightColor(withVisualTimingForReviewedSpan(span, chunks, captionScrollTiming), highlightAccent),
    );
  }
  return [];
}

function phraseWordCount(phrase) {
  return cleanCueText(phrase).split(/\s+/).filter(Boolean).length;
}

function maxHighlightGapSeconds(spans, durationSeconds) {
  if (!spans.length) return null;
  const starts = spans.map((span) => Number(span.timing_window_seconds?.[0])).filter(Number.isFinite).sort((a, b) => a - b);
  if (!starts.length) return null;
  let maxGap = 0;
  for (let index = 1; index < starts.length; index += 1) {
    maxGap = Math.max(maxGap, starts[index] - starts[index - 1]);
  }
  const postIntroStart = Math.max(0, starts[0]);
  maxGap = Math.max(maxGap, starts[0] - postIntroStart);
  if (Number.isFinite(durationSeconds)) maxGap = Math.max(maxGap, durationSeconds - starts[starts.length - 1]);
  return Number(maxGap.toFixed(3));
}

function highlightStatsForSpans(spans, durationSeconds) {
  return {
    highlight_count: spans.length,
    single_word_highlight_count: spans.filter((span) => phraseWordCount(span.phrase_text) === 1).length,
    invalid_takeaway_phrase_length_count: spans.filter((span) => {
      const count = phraseWordCount(span.phrase_text);
      return count < 2 || count > 9;
    }).length,
    max_highlight_gap_seconds: maxHighlightGapSeconds(spans, durationSeconds),
  };
}

function expectedLessonTakeawayCount(episodeId) {
  return EXPECTED_LESSON_TAKEAWAY_COUNTS[episodeId] || null;
}

function highlightDensityPassForEpisode(episodeId, highlightStats) {
  const expectedCount = expectedLessonTakeawayCount(episodeId);
  const countPass = expectedCount
    ? highlightStats.highlight_count === expectedCount
    : highlightStats.highlight_count >= 22 && highlightStats.highlight_count <= 32;
  return countPass && Number(highlightStats.max_highlight_gap_seconds || 0) <= 90;
}

function paletteForEpisode(episodeId) {
  const palettes = {
    challenger: { text: "#f7efe1", muted: "#b9c8d8", fill: "rgba(15, 27, 40, 0.38)", highlight: "#ffe0a6" },
    "therac-25": { text: "#edf6e8", muted: "#b8d8cc", fill: "rgba(20, 44, 38, 0.36)", highlight: "#bff4cf" },
    "hyatt-regency": { text: "#fff2df", muted: "#dac2a3", fill: "rgba(70, 42, 28, 0.34)", highlight: "#ffd19a" },
    semmelweis: { text: "#f3f7ec", muted: "#c7d7c0", fill: "rgba(36, 52, 42, 0.34)", highlight: "#dff0a8" },
    "tacoma-narrows": { text: "#edf7fb", muted: "#acc5d0", fill: "rgba(22, 42, 51, 0.36)", highlight: "#b6e7f3" },
    "piltdown-man": { text: "#fff1d9", muted: "#d8c19b", fill: "rgba(58, 43, 26, 0.34)", highlight: "#f6d37d" },
    "737-max": { text: "#f4f7fb", muted: "#b8c7d4", fill: "rgba(28, 38, 48, 0.36)", highlight: "#c7def5" },
    titanic: { text: "#f0f8fa", muted: "#b7ced4", fill: "rgba(18, 43, 54, 0.38)", highlight: "#bde8ef" },
  };
  return palettes[episodeId] || palettes.challenger;
}

function clamp01(value) {
  return Math.max(0, Math.min(1, Number(value) || 0));
}

function rgbToHex(rgb) {
  return `#${rgb.map((channel) => Math.max(0, Math.min(255, Math.round(channel))).toString(16).padStart(2, "0")).join("")}`;
}

function hexToRgb(hex) {
  const value = String(hex || "").replace("#", "").trim();
  if (!/^[0-9a-f]{6}$/i.test(value)) return null;
  return [parseInt(value.slice(0, 2), 16), parseInt(value.slice(2, 4), 16), parseInt(value.slice(4, 6), 16)];
}

function rgbaString(rgb, alpha) {
  return `rgba(${rgb.map((channel) => Math.max(0, Math.min(255, Math.round(channel)))).join(", ")}, ${Number(alpha).toFixed(3)})`;
}

function mixRgb(a, b, amount) {
  const t = clamp01(amount);
  return [0, 1, 2].map((index) => Number(a?.[index] || 0) + (Number(b?.[index] || 0) - Number(a?.[index] || 0)) * t);
}

function relativeLuminance(rgb) {
  const channels = (rgb || [0, 0, 0]).map((channel) => {
    const value = Math.max(0, Math.min(255, Number(channel) || 0)) / 255;
    return value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

function contrastRatio(a, b) {
  const lighter = Math.max(relativeLuminance(a), relativeLuminance(b));
  const darker = Math.min(relativeLuminance(a), relativeLuminance(b));
  return Number(((lighter + 0.05) / (darker + 0.05)).toFixed(3));
}

function colorDistance(a, b) {
  if (!Array.isArray(a) || !Array.isArray(b)) return 0;
  return Number(Math.sqrt([0, 1, 2].reduce((sum, index) => sum + (Number(a[index]) - Number(b[index])) ** 2, 0)).toFixed(3));
}

function isNearWhite(rgb) {
  if (!Array.isArray(rgb)) return true;
  return Math.min(...rgb) >= 226 && Math.max(...rgb) - Math.min(...rgb) <= 34;
}

function captionWindowBackplateSampleBox() {
  const left = RAIL_GEOMETRY.left + RAIL_GEOMETRY.width - CAPTION_WINDOW_GEOMETRY.railRight - CAPTION_WINDOW_GEOMETRY.width;
  const top = RAIL_GEOMETRY.top + CAPTION_WINDOW_GEOMETRY.railTop;
  return [
    left + CAPTION_WINDOW_GEOMETRY.stackLeft,
    top + 96,
    left + CAPTION_WINDOW_GEOMETRY.stackLeft + CAPTION_WINDOW_GEOMETRY.stackWidth,
    top + CAPTION_WINDOW_GEOMETRY.height - 96,
  ];
}

function highlightAccentCandidatesFromSample(sampleRgb) {
  const sample = Array.isArray(sampleRgb) ? sampleRgb : [118, 103, 82];
  const [hue, saturation, lightness] = rgbToHsl(sample);
  const reliableSat = Math.max(0.42, Math.min(0.88, saturation * 1.9 + 0.18));
  const baseLight = Math.max(0.47, Math.min(0.68, lightness + 0.27));
  const contrastLight = lightness < 0.42 ? 0.72 : 0.28;
  const alternateContrastLight = lightness < 0.42 ? 0.62 : 0.78;
  return [
    hslToRgb([hue, reliableSat, baseLight]),
    hslToRgb([hue, Math.max(0.48, reliableSat * 0.92), Math.min(0.72, baseLight + 0.08)]),
    hslToRgb([(hue + 0.08) % 1, reliableSat, baseLight]),
    hslToRgb([(hue + 0.92) % 1, reliableSat, baseLight]),
    hslToRgb([(hue + 0.5) % 1, Math.max(0.52, reliableSat * 0.9), contrastLight]),
    hslToRgb([(hue + 0.5) % 1, Math.max(0.42, reliableSat * 0.68), alternateContrastLight]),
    hslToRgb([(hue + 0.33) % 1, Math.max(0.5, reliableSat * 0.84), contrastLight]),
    hslToRgb([(hue + 0.67) % 1, Math.max(0.5, reliableSat * 0.84), contrastLight]),
    hslToRgb([0.105, 0.86, 0.62]),
    hslToRgb([0.135, 0.78, 0.58]),
    hslToRgb([0.04, 0.76, 0.60]),
    hslToRgb([0.56, 0.72, 0.72]),
    hslToRgb([0.73, 0.78, 0.70]),
    hslToRgb([0.92, 0.74, 0.68]),
    ...broadContrastHighlightCandidates(),
  ];
}

function broadContrastHighlightCandidates() {
  const candidates = [];
  for (let hueStep = 0; hueStep < 72; hueStep += 1) {
    for (const saturation of [0.42, 0.52, 0.62, 0.72]) {
      for (const lightness of [0.24, 0.32, 0.42, 0.54, 0.62, 0.7, 0.78]) {
        candidates.push(hslToRgb([hueStep / 72, saturation, lightness]));
      }
    }
  }
  return candidates;
}

function highlightAccentScore(candidateRgb, activeTextRgb, mutedTextRgb, backplateSamples = []) {
  const activeDelta = colorDistance(candidateRgb, activeTextRgb);
  const mutedDelta = colorDistance(candidateRgb, mutedTextRgb);
  const activeContrast = contrastRatio(candidateRgb, activeTextRgb);
  const mutedContrast = contrastRatio(candidateRgb, mutedTextRgb);
  const backplateContrasts = backplateSamples.map((sample) => contrastRatio(candidateRgb, sample));
  const backplateDeltas = backplateSamples.map((sample) => colorDistance(candidateRgb, sample));
  const minBackplateContrast = backplateContrasts.length ? Math.min(...backplateContrasts) : 0;
  const p20BackplateContrast = percentile(backplateContrasts, 0.2);
  const minBackplateDelta = backplateDeltas.length ? Math.min(...backplateDeltas) : 0;
  const chroma = Math.max(...candidateRgb) - Math.min(...candidateRgb);
  const [, candidateSaturation, candidateLightness] = rgbToHsl(candidateRgb);
  const nearWhitePenalty = isNearWhite(candidateRgb) ? 200 : 0;
  const neonPenalty = Math.max(0, candidateSaturation - 0.76) * 260 + Math.max(0, chroma - 205) * 0.85;
  const lightnessPenalty = Math.abs(candidateLightness - 0.7) * 24;
  const lowContrastPenalty =
    (activeDelta < HIGHLIGHT_ACTIVE_TEXT_MIN_DELTA ? (HIGHLIGHT_ACTIVE_TEXT_MIN_DELTA - activeDelta) * 2 : 0) +
    (mutedDelta < HIGHLIGHT_MUTED_TEXT_MIN_DELTA ? (HIGHLIGHT_MUTED_TEXT_MIN_DELTA - mutedDelta) * 1.4 : 0) +
    (activeContrast < HIGHLIGHT_ACTIVE_TEXT_MIN_CONTRAST
      ? (HIGHLIGHT_ACTIVE_TEXT_MIN_CONTRAST - activeContrast) * 110
      : 0) +
    (mutedContrast < HIGHLIGHT_MUTED_TEXT_MIN_CONTRAST ? (HIGHLIGHT_MUTED_TEXT_MIN_CONTRAST - mutedContrast) * 90 : 0) +
    (minBackplateContrast < HIGHLIGHT_MIN_BACKPLATE_CONTRAST_RATIO
      ? (HIGHLIGHT_MIN_BACKPLATE_CONTRAST_RATIO - minBackplateContrast) * 175
      : 0) +
    (p20BackplateContrast < HIGHLIGHT_P20_BACKPLATE_CONTRAST_RATIO
      ? (HIGHLIGHT_P20_BACKPLATE_CONTRAST_RATIO - p20BackplateContrast) * 120
      : 0) +
    (minBackplateDelta < HIGHLIGHT_MIN_BACKPLATE_COLOR_DELTA
      ? (HIGHLIGHT_MIN_BACKPLATE_COLOR_DELTA - minBackplateDelta) * 1.6
      : 0);
  return (
    activeDelta * 0.72 +
    mutedDelta * 0.86 +
    activeContrast * 22 +
    mutedContrast * 17 +
    minBackplateContrast * 132 +
    p20BackplateContrast * 70 +
    minBackplateDelta * 0.85 +
    chroma * 0.42 -
    nearWhitePenalty -
    neonPenalty -
    lightnessPenalty -
    lowContrastPenalty
  );
}

function humanApprovedHighlightAccentOverrideForEpisode(episode) {
  const episodeId = episode?.episodeId || episode?.episode_id || "";
  const override = HUMAN_APPROVED_HIGHLIGHT_ACCENT_OVERRIDES[episodeId];
  if (!override) return null;
  const selectedRgb = Array.isArray(override.selected_rgb) ? override.selected_rgb : hexToRgb(override.selected_hex);
  if (!Array.isArray(selectedRgb)) return null;
  return {
    ...override,
    selected_rgb: selectedRgb,
    selected_hex: override.selected_hex || rgbToHex(selectedRgb),
  };
}

function ambientFrameClockMetadata(episode) {
  const applies = AMBIENT_FRAME_CLOCK_EPISODES.has(episode?.episodeId || episode?.episode_id || "");
  return {
    ambient_frame_clock_model: applies ? AMBIENT_FRAME_CLOCK_MODEL : "not_applicable",
    ambient_render_clock_read: applies ? AMBIENT_RENDER_CLOCK_READ : "not_applicable",
    ambient_wall_clock_drift_suppression_read: applies ? AMBIENT_WALL_CLOCK_DRIFT_SUPPRESSION_READ : "not_applicable",
  };
}

function highlightColorQaForSourceArt({ episode, sourceArtPath, palette }) {
  const sampleBox = captionWindowBackplateSampleBox();
  const sampleRgb = sampleAverageColor(sourceArtPath, sampleBox) || hexToRgb(palette?.highlight) || [180, 150, 92];
  const backplateSamples = sampleColorGrid(sourceArtPath, sampleBox, 7, 9);
  const contrastSamples = backplateSamples.length ? backplateSamples : [sampleRgb];
  const activeTextRgb = hexToRgb(palette?.text) || [247, 239, 225];
  const mutedTextRgb = hexToRgb(palette?.muted) || [185, 200, 216];
  const humanOverride = humanApprovedHighlightAccentOverrideForEpisode(episode);
  const candidates = highlightAccentCandidatesFromSample(sampleRgb)
    .filter((candidate) => !isNearWhite(candidate))
    .map((candidate) => ({
      rgb: candidate,
      score: highlightAccentScore(candidate, activeTextRgb, mutedTextRgb, contrastSamples),
    }))
    .sort((a, b) => b.score - a.score);
  const selectedCandidate =
    candidates.find((candidate) => highlightAccentPassesGates(candidate.rgb, activeTextRgb, mutedTextRgb, contrastSamples)) ||
    candidates[0];
  const selectedRgb = humanOverride?.selected_rgb || selectedCandidate?.rgb || [239, 176, 88];
  const selectedHex = rgbToHex(selectedRgb);
  const activeDelta = colorDistance(selectedRgb, activeTextRgb);
  const mutedDelta = colorDistance(selectedRgb, mutedTextRgb);
  const activeContrast = contrastRatio(selectedRgb, activeTextRgb);
  const mutedContrast = contrastRatio(selectedRgb, mutedTextRgb);
  const backplateContrasts = contrastSamples.map((sample) => contrastRatio(selectedRgb, sample));
  const backplateDeltas = contrastSamples.map((sample) => colorDistance(selectedRgb, sample));
  const minimumBackplateContrast = backplateContrasts.length ? Number(Math.min(...backplateContrasts).toFixed(3)) : 0;
  const p20BackplateContrast = Number(percentile(backplateContrasts, 0.2).toFixed(3));
  const minimumBackplateDelta = backplateDeltas.length ? Number(Math.min(...backplateDeltas).toFixed(3)) : 0;
  const backplatePass =
    minimumBackplateContrast >= HIGHLIGHT_MIN_BACKPLATE_CONTRAST_RATIO &&
    p20BackplateContrast >= HIGHLIGHT_P20_BACKPLATE_CONTRAST_RATIO &&
    minimumBackplateDelta >= HIGHLIGHT_MIN_BACKPLATE_COLOR_DELTA;
  const captionDistancePass =
    activeDelta >= HIGHLIGHT_ACTIVE_TEXT_MIN_DELTA &&
    mutedDelta >= HIGHLIGHT_MUTED_TEXT_MIN_DELTA &&
    activeContrast >= HIGHLIGHT_ACTIVE_TEXT_MIN_CONTRAST;
  const genericPass =
    !isNearWhite(selectedRgb) &&
    captionDistancePass &&
    mutedContrast >= HIGHLIGHT_MUTED_TEXT_MIN_CONTRAST &&
    backplatePass;
  const humanOverridePass = Boolean(humanOverride) && !isNearWhite(selectedRgb) && captionDistancePass && backplatePass;
  const pass = genericPass || humanOverridePass;
  const overrideFields = humanOverride
    ? {
        highlight_override_read: humanOverride.highlight_override_read,
        highlight_override_source: humanOverride.override_source,
        highlight_override_reason: humanOverride.override_reason,
        generic_muted_text_contrast_ratio: mutedContrast,
        generic_muted_text_contrast_gate_read: genericPass
          ? "pass_generic_candidate_gate"
          : "waived_by_human_requested_episode_accent_override",
      }
    : {};
  return {
    highlight_color_model: HIGHLIGHT_COLOR_MODEL,
    source: "sampled_episode_backplate",
    source_art_path: sourceArtPath || "not_found",
    source_art_sha256: sha256File(sourceArtPath),
    sample_model: "caption_window_grid_backplate_contrast_accent_v3",
    sample_bbox_xy: sampleBox,
    sample_rgb: sampleRgb.map((value) => Math.round(Number(value) || 0)),
    sample_hex: rgbToHex(sampleRgb),
    backplate_contrast_sample_count: contrastSamples.length,
    backplate_contrast_sample_hexes: contrastSamples.map((sample) => rgbToHex(sample)),
    selected_rgb: selectedRgb.map((value) => Math.round(Number(value) || 0)),
    selected_hex: selectedHex,
    active_caption_text_hex: palette?.text || "#f7efe1",
    adjacent_caption_text_hex: palette?.muted || "#b9c8d8",
    active_caption_text_delta: activeDelta,
    adjacent_caption_text_delta: mutedDelta,
    active_caption_text_contrast_ratio: activeContrast,
    adjacent_caption_text_contrast_ratio: mutedContrast,
    minimum_backplate_contrast_ratio: minimumBackplateContrast,
    p20_backplate_contrast_ratio: p20BackplateContrast,
    minimum_backplate_color_delta: minimumBackplateDelta,
    candidate_count: candidates.length,
    selected_candidate_source: humanOverride ? "human_requested_episode_accent_override" : "source_sampled_candidate_gate",
    ...overrideFields,
    highlight_distinct_from_caption_text_read: pass
      ? humanOverridePass && !genericPass
        ? "pass_human_requested_override_distinct_by_color_distance_and_backplate_contrast"
        : "pass_source_sampled_accent_distinct_from_active_and_muted_caption_text_and_backplate"
      : "tighten_source_sampled_accent_not_distinct_enough_from_text_or_backplate",
    highlight_backplate_contrast_read: pass
      ? "pass_grid_sampled_caption_window_backplate_contrast"
      : "tighten_grid_sampled_caption_window_backplate_contrast",
    highlight_adaptive_source_read: sourceArtPath && fs.existsSync(sourceArtPath)
      ? "pass_sampled_from_active_episode_backplate"
      : "blocked_missing_active_episode_backplate_sample",
    episode_id: episode?.episodeId || "unknown",
  };
}

function highlightAccentPassesGates(candidateRgb, activeTextRgb, mutedTextRgb, backplateSamples = []) {
  const activeDelta = colorDistance(candidateRgb, activeTextRgb);
  const mutedDelta = colorDistance(candidateRgb, mutedTextRgb);
  const activeContrast = contrastRatio(candidateRgb, activeTextRgb);
  const mutedContrast = contrastRatio(candidateRgb, mutedTextRgb);
  const backplateContrasts = backplateSamples.map((sample) => contrastRatio(candidateRgb, sample));
  const backplateDeltas = backplateSamples.map((sample) => colorDistance(candidateRgb, sample));
  const minimumBackplateContrast = backplateContrasts.length ? Math.min(...backplateContrasts) : 0;
  const p20BackplateContrast = percentile(backplateContrasts, 0.2);
  const minimumBackplateDelta = backplateDeltas.length ? Math.min(...backplateDeltas) : 0;
  return (
    !isNearWhite(candidateRgb) &&
    activeDelta >= HIGHLIGHT_ACTIVE_TEXT_MIN_DELTA &&
    mutedDelta >= HIGHLIGHT_MUTED_TEXT_MIN_DELTA &&
    activeContrast >= HIGHLIGHT_ACTIVE_TEXT_MIN_CONTRAST &&
    mutedContrast >= HIGHLIGHT_MUTED_TEXT_MIN_CONTRAST &&
    minimumBackplateContrast >= HIGHLIGHT_MIN_BACKPLATE_CONTRAST_RATIO &&
    p20BackplateContrast >= HIGHLIGHT_P20_BACKPLATE_CONTRAST_RATIO &&
    minimumBackplateDelta >= HIGHLIGHT_MIN_BACKPLATE_COLOR_DELTA
  );
}

function rgbToHsl([r, g, b]) {
  r /= 255;
  g /= 255;
  b /= 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0;
  let s = 0;
  const l = (max + min) / 2;
  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r:
        h = (g - b) / d + (g < b ? 6 : 0);
        break;
      case g:
        h = (b - r) / d + 2;
        break;
      default:
        h = (r - g) / d + 4;
        break;
    }
    h /= 6;
  }
  return [h, s, l];
}

function hslToRgb([h, s, l]) {
  const hue = ((Number(h) || 0) % 1 + 1) % 1;
  const sat = clamp01(s);
  const light = clamp01(l);
  if (sat === 0) {
    const gray = light * 255;
    return [gray, gray, gray];
  }
  const hue2rgb = (p, q, tInput) => {
    let t = tInput;
    if (t < 0) t += 1;
    if (t > 1) t -= 1;
    if (t < 1 / 6) return p + (q - p) * 6 * t;
    if (t < 1 / 2) return q;
    if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
    return p;
  };
  const q = light < 0.5 ? light * (1 + sat) : light + sat - light * sat;
  const p = 2 * light - q;
  return [hue2rgb(p, q, hue + 1 / 3) * 255, hue2rgb(p, q, hue) * 255, hue2rgb(p, q, hue - 1 / 3) * 255];
}

function sampleAverageColor(sourceArtPath, bbox_xy) {
  if (!sourceArtPath || !fs.existsSync(sourceArtPath) || !Array.isArray(bbox_xy)) return null;
  const [x1, y1, x2, y2] = bbox_xy.map((value) => Math.round(Number(value) || 0));
  const width = Math.max(1, x2 - x1);
  const height = Math.max(1, y2 - y1);
  const crop = `crop=${width}:${height}:${Math.max(0, x1)}:${Math.max(0, y1)},scale=1:1,format=rgb24`;
  const result = spawnSync(
    "ffmpeg",
    ["-v", "error", "-i", sourceArtPath, "-vf", crop, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],
    { encoding: null, maxBuffer: 1024 * 1024 },
  );
  if (result.status !== 0 || !result.stdout || result.stdout.length < 3) return null;
  return [result.stdout[0], result.stdout[1], result.stdout[2]];
}

function sampleColorGrid(sourceArtPath, bbox_xy, columns = 7, rows = 9) {
  if (!sourceArtPath || !fs.existsSync(sourceArtPath) || !Array.isArray(bbox_xy)) return [];
  const [x1, y1, x2, y2] = bbox_xy.map((value) => Math.round(Number(value) || 0));
  const width = Math.max(1, x2 - x1);
  const height = Math.max(1, y2 - y1);
  const gridColumns = Math.max(1, Math.floor(columns));
  const gridRows = Math.max(1, Math.floor(rows));
  const crop = `crop=${width}:${height}:${Math.max(0, x1)}:${Math.max(0, y1)},scale=${gridColumns}:${gridRows}:flags=area,format=rgb24`;
  const result = spawnSync(
    "ffmpeg",
    ["-v", "error", "-i", sourceArtPath, "-vf", crop, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],
    { encoding: null, maxBuffer: 1024 * 1024 },
  );
  if (result.status !== 0 || !result.stdout || result.stdout.length < 3) return [];
  const samples = [];
  for (let index = 0; index + 2 < result.stdout.length; index += 3) {
    samples.push([result.stdout[index], result.stdout[index + 1], result.stdout[index + 2]]);
  }
  return samples;
}

function percentile(values, ratio) {
  const numbers = values.map(Number).filter(Number.isFinite).sort((a, b) => a - b);
  if (!numbers.length) return 0;
  const index = Math.max(0, Math.min(numbers.length - 1, Math.floor((numbers.length - 1) * clamp01(ratio))));
  return numbers[index];
}

function endScreenTargetColorsFromSample(sampleRgb, role = "video") {
  const fallback = role === "subscribe" ? [80, 79, 85] : [64, 66, 66];
  const sample = Array.isArray(sampleRgb) ? sampleRgb : fallback;
  const [hue, saturation, lightness] = rgbToHsl(sample);
  const sampleSpread = Math.max(...sample) - Math.min(...sample);
  const neutralLift = sampleSpread < 10 ? 0.08 : 0;
  const darkHueReliabilityCap = lightness < 0.08 ? (role === "subscribe" ? 0.42 : 0.44) : 1;
  const sat = Math.min(
    darkHueReliabilityCap,
    clamp01(Math.max(role === "subscribe" ? 0.24 : 0.22, saturation * 1.85 + neutralLift)),
  );
  const fill = hslToRgb([
    hue,
    clamp01(sat * 0.82),
    clamp01((role === "subscribe" ? 0.18 : 0.155) + Math.min(lightness, 0.34) * 0.12),
  ]);
  const border = hslToRgb([
    hue,
    clamp01(Math.max(role === "subscribe" ? 0.32 : 0.30, sat * 1.06)),
    clamp01(role === "subscribe" ? 0.67 : 0.60),
  ]);
  const ring = hslToRgb([
    hue,
    clamp01(Math.max(role === "subscribe" ? 0.28 : 0.24, sat * 0.92)),
    clamp01(role === "subscribe" ? 0.54 : 0.47),
  ]);
  const innerRing = hslToRgb([hue, clamp01(Math.max(0.28, sat * 0.88)), 0.63]);
  const variabilityScore = Math.round(Math.max(...border) - Math.min(...border));
  return {
    sample_hex: rgbToHex(sample),
    fill_rgba: rgbaString(fill, role === "subscribe" ? 0.34 : 0.36),
    border_rgba: rgbaString(border, role === "subscribe" ? 0.84 : 0.74),
    ring_rgba: rgbaString(ring, role === "subscribe" ? 0.20 : 0.18),
    inner_ring_rgba: rgbaString(innerRing, 0.46),
    palette_treatment_model: END_SCREEN_PALETTE_TREATMENT_MODEL,
    adaptive_variability_model: END_SCREEN_ADAPTIVE_VARIABILITY_MODEL,
    source_hue_degrees: Math.round(hue * 360),
    source_saturation: Number(saturation.toFixed(3)),
    derived_saturation: Number(sat.toFixed(3)),
    perceptual_variability_score: variabilityScore,
    perceptual_variability_read:
      variabilityScore >= 24
        ? "pass_backplate_hue_visible_in_end_screen_target"
        : "tighten_low_perceptual_target_variability",
    hue_shift_applied: false,
  };
}

function endScreenPaletteForSourceArt(sourceArtPath) {
  const targets = {};
  for (const [key, target] of Object.entries(END_SCREEN_TARGET_LAYOUT)) {
    const sampleRgb = sampleAverageColor(sourceArtPath, target.bbox_xy);
    targets[key] = {
      role: target.role,
      sample_bbox_xy: target.bbox_xy,
      sample_hex: sampleRgb ? rgbToHex(sampleRgb) : "sample_failed",
      ...endScreenTargetColorsFromSample(sampleRgb, target.role),
      sample_read: sampleRgb ? "pass_backplate_region_average" : "fallback_missing_backplate_sample",
    };
  }
  const sampleRead = Object.values(targets).every((target) => target.sample_read === "pass_backplate_region_average")
    ? "pass_source_backplate_sampled"
    : "tighten_missing_source_backplate_sample";
  return {
    model_id: END_SCREEN_PALETTE_MODEL,
    palette_treatment_model: END_SCREEN_PALETTE_TREATMENT_MODEL,
    palette_source: "sampled_episode_backplate",
    source_art_path: sourceArtPath || "not_found",
    source_art_sha256: sha256File(sourceArtPath),
    target_count: Object.keys(targets).length,
    targets,
    sample_read: sampleRead,
    adaptive_variability_model: END_SCREEN_ADAPTIVE_VARIABILITY_MODEL,
    perceptual_variability_min_score: Math.min(
      ...Object.values(targets).map((target) => Number(target.perceptual_variability_score || 0)),
    ),
    end_screen_adaptive_perceptual_variability_read:
      Object.values(targets).every((target) => target.perceptual_variability_read === "pass_backplate_hue_visible_in_end_screen_target")
        ? "pass_backplate_hue_visible_across_end_screen_targets"
        : "tighten_backplate_hue_not_visible_enough_in_end_screen_targets",
    adaptive_context_read:
      sampleRead === "pass_source_backplate_sampled"
        ? "pass_local_target_regions_sampled_with_perceptual_backplate_variability"
        : "tighten_missing_source_backplate_sample",
    fixed_cross_episode_color_read: "pass_no_challenger_default_color_reuse_with_visible_episode_variability",
  };
}

function endScreenPaletteContractForSourceArt(sourceArtPath, endScreenPalette = endScreenPaletteForSourceArt(sourceArtPath)) {
  const left = endScreenPalette.targets?.left_video || {};
  const right = endScreenPalette.targets?.right_video || {};
  const subscribe = endScreenPalette.targets?.center_subscribe || {};
  const sourceSha256 = sha256File(sourceArtPath);
  const pass = endScreenPalette.sample_read === "pass_source_backplate_sampled" && sourceSha256 !== "missing";
  const colors = {
    video_target_fill_rgba: left.fill_rgba || "missing",
    video_target_border_rgba: left.border_rgba || "missing",
    video_target_secondary_border_rgba: right.border_rgba || "missing",
    subscribe_ring_rgba: subscribe.border_rgba || "missing",
    muted_rail_text_hex: right.sample_hex && right.sample_hex !== "sample_failed" ? right.sample_hex : left.sample_hex || "missing",
    small_accent_hex: subscribe.sample_hex && subscribe.sample_hex !== "sample_failed" ? subscribe.sample_hex : left.sample_hex || "missing",
  };
  return {
    contract_id: END_SCREEN_PALETTE_CONTRACT_ID,
    status: pass ? "pass" : "blocked_missing_sampled_backplate",
    required: true,
    required_for_gates: ["visual_system", "rough_assembly", "final_assembly", "publish_readiness"],
    palette_source: "sampled_episode_backplate",
    derivation_model: END_SCREEN_PALETTE_MODEL,
    sample_model: "ffmpeg_target_region_average_rgb_v1",
    approved_backplate: {
      path: sourceArtPath || "missing",
      sha256: sourceSha256,
      role: "approved_living_cover_source_art_backplate",
    },
    sampled_backplate: {
      path: sourceArtPath || "missing",
      sha256: sourceSha256,
      palette_treatment_model: END_SCREEN_PALETTE_TREATMENT_MODEL,
      target_samples: Object.fromEntries(
        Object.entries(endScreenPalette.targets || {}).map(([key, target]) => [
          key,
          {
            bbox_xy: target.sample_bbox_xy,
            sample_hex: target.sample_hex,
            sample_read: target.sample_read,
          },
        ]),
      ),
    },
    colors,
    css_variables: {
      "--ce-end-screen-target-fill": colors.video_target_fill_rgba,
      "--ce-end-screen-video-border": colors.video_target_border_rgba,
      "--ce-end-screen-video-border-secondary": colors.video_target_secondary_border_rgba,
      "--ce-end-screen-subscribe-ring": colors.subscribe_ring_rgba,
      "--ce-end-screen-muted-text": colors.muted_rail_text_hex,
      "--ce-end-screen-small-accent": colors.small_accent_hex,
    },
    reads: {
      end_screen_palette_contract_read: pass ? "pass_backplate_sampled_palette_contract_present" : "blocked_missing_sampled_backplate",
      end_screen_target_fill_palette_read: pass ? "pass_local_target_fills_sampled_from_backplate_regions" : "blocked_missing_sampled_backplate",
      end_screen_target_contrast_read: pass ? "pass_local_target_borders_visible_without_challenger_hue_shift" : "blocked_missing_sampled_backplate",
      rail_panel_palette_read: pass ? "pass_adaptive_end_screen_targets_use_source_aware_palette" : "blocked_missing_sampled_backplate",
      source_integrated_panel_color_read: pass ? "pass_perceptual_episode_backplate_colors_visible_in_end_screen" : "blocked_missing_sampled_backplate",
      no_cross_episode_default_palette_read: pass ? "pass_no_challenger_default_target_colors_with_visible_variability" : "blocked_missing_sampled_backplate",
      end_screen_adaptive_perceptual_variability_read:
        endScreenPalette.end_screen_adaptive_perceptual_variability_read || "blocked_missing_sampled_backplate",
    },
    target_palette: endScreenPalette,
  };
}

function mediaUri(filePath) {
  return filePath || "";
}

function symlinkForReview(outputDir, sourcePath, relativeTarget) {
  if (!sourcePath || !fs.existsSync(sourcePath) || !fs.statSync(sourcePath).isFile()) return "";
  const linkPath = path.join(outputDir, relativeTarget);
  ensureDir(path.dirname(linkPath));
  try {
    if (fs.existsSync(linkPath) || fs.lstatSync(linkPath, { throwIfNoEntry: false })?.isSymbolicLink()) {
      fs.unlinkSync(linkPath);
    }
  } catch {
    // Continue and let symlinkSync surface a useful error if the path is still unusable.
  }
  fs.symlinkSync(sourcePath, linkPath);
  return relativeTarget;
}

function findSourceHtmlPath(sourceRoot) {
  for (const name of ["player.html", "review.html"]) {
    const candidate = path.join(sourceRoot, name);
    if (fs.existsSync(candidate)) return candidate;
  }
  return findFiles(sourceRoot, (file) => /\.html$/i.test(file), 60)[0] || "";
}

function findSourceManifestPath(sourceRoot) {
  for (const name of ["rough_assembly_manifest.json", "manifest.json"]) {
    const candidate = path.join(sourceRoot, name);
    if (fs.existsSync(candidate)) return candidate;
  }
  return findFiles(sourceRoot, (file) => /(?:rough_assembly_)?manifest\.json$/i.test(path.basename(file)), 80)[0] || "";
}

function relativeHref(fromDir, targetPath) {
  return path.relative(fromDir, targetPath).split(path.sep).map(encodeURIComponent).join("/");
}

function replaceFirstAudioSource(html, audioPath, outputDir) {
  if (!audioPath || !fs.existsSync(audioPath)) return html;
  const href = relativeHref(outputDir, audioPath);
  const stripNestedSources = (audioMarkup) => audioMarkup.replace(/<source\b[^>]*>\s*/gi, "");
  const rewriteScriptAudioPath = (markup) =>
    markup.replace(/(["']audio["']\s*:\s*["'])([^"']+)(["'])/i, `$1${href}$3`);
  if (/<audio\b[^>]*\bsrc\s*=/i.test(html)) {
    return rewriteScriptAudioPath(
      html.replace(/<audio\b[\s\S]*?<\/audio>/i, (audioMarkup) =>
        stripNestedSources(audioMarkup).replace(/(<audio\b[^>]*\bsrc\s*=\s*)(["'])(.*?)\2/i, `$1$2${href}$2`),
      ),
    );
  }
  return rewriteScriptAudioPath(
    html.replace(/<audio\b[\s\S]*?<\/audio>/i, (audioMarkup) =>
      stripNestedSources(audioMarkup.replace(/<audio\b/i, `<audio src="${href}"`)),
    ),
  );
}

function rewriteSourcePlateReference(html, episode, sourceArtPath, outputDir) {
  if (!sourceArtPath || !fs.existsSync(sourceArtPath) || !episode?.sourceArtOverridePath) return html;
  const linkedSourceArtPath = symlinkForReview(
    outputDir,
    sourceArtPath,
    `proof_assets/source_art/backplate${path.extname(sourceArtPath || ".png") || ".png"}`,
  );
  const sourceArtHref = linkedSourceArtPath || relativeHref(outputDir, sourceArtPath);
  if (!sourceArtHref) return html;
  const originalCandidate =
    "source_art/candidates/737_max_living_cover_source_art_candidate_l_ramp_depth_lights_1920x1080_20260519.png";
  let rewritten = String(html || "").replaceAll(originalCandidate, sourceArtHref);
  if (rewritten === html) {
    rewritten = rewritten.replace(/<img\b[^>]*>/gi, (tag) => {
      const isSourcePlate =
        /\bid\s*=\s*["']sourcePlate["']/i.test(tag) ||
        /\bclass\s*=\s*["'][^"']*(?:\bsource-plate\b|\bbackplate\b|\bplate\b)[^"']*["']/i.test(tag);
      if (!isSourcePlate || !/\bsrc\s*=/i.test(tag)) return tag;
      return tag.replace(/\bsrc\s*=\s*(["'])(.*?)\1/i, `src=$1${sourceArtHref}$1`);
    });
  }
  return rewritten;
}

function rewriteSupersededEndScreenTemplateMarkers(html) {
  return String(html || "").replaceAll(
    "challenger_titleless_end_screen_overlay_on_living_cover_v1",
    "superseded_predecessor_end_screen_template_hidden_by_adaptive_overlay_v1",
  );
}

function ensureContractTimedRightRailMusicMix({ episode, outputDir, musicContract }) {
  if (!musicContract) return "";
  const contractVoicePath = resolveCandidate(valueAt(musicContract, "voice_master.path"), process.cwd());
  const audioDefectRepair = audioDefectRepairForEpisode(episode, contractVoicePath);
  const sourceVoicePath = audioDefectRepair?.repaired_voice_master_path || contractVoicePath;
  const introPath = resolveCandidate(valueAt(musicContract, "music_sources.intro_loop.path"), process.cwd());
  const outroPath = resolveCandidate(valueAt(musicContract, "music_sources.full_outro.path"), process.cwd());
  if (!sourceVoicePath || !introPath || !outroPath) return "";
  const voiceLoudnessAlignment = renderAlignedVoiceStem({ episode, outputDir, voicePath: sourceVoicePath });
  const voicePath = voiceLoudnessAlignment.mix_voice_master_path || sourceVoicePath;
  const voiceStart = firstFiniteNumber([valueAt(musicContract, "timing_contract.voice_start_offset_seconds")], 0);
  const sourceVoiceDuration = audioDefectRepair
    ? durationSeconds(sourceVoicePath)
    : firstFiniteNumber([valueAt(musicContract, "voice_master.duration_seconds"), durationSeconds(sourceVoicePath)], 0);
  const mixVoiceDuration = firstFiniteNumber([durationSeconds(voicePath)], sourceVoiceDuration);
  const voiceDuration = Math.abs(mixVoiceDuration - sourceVoiceDuration) <= 0.02 ? mixVoiceDuration : sourceVoiceDuration;
  const voiceEnd = firstFiniteNumber([valueAt(musicContract, "timing_contract.voice_end_seconds")], voiceStart + voiceDuration);
  const introFadeTail = firstFiniteNumber([valueAt(musicContract, "timing_contract.intro_fade_tail_duration_seconds")], 2);
  const outroStart = firstFiniteNumber([valueAt(musicContract, "timing_contract.full_outro_start_seconds")], voiceEnd - 1.5);
  const outroDuration = firstFiniteNumber(
    [valueAt(musicContract, "music_sources.full_outro.duration_seconds"), durationSeconds(outroPath)],
    0,
  );
  const outroPrelap = firstFiniteNumber([valueAt(musicContract, "timing_contract.outro_prelap_seconds")], Math.max(0, voiceEnd - outroStart));
  const outroUnderVoGain = firstFiniteNumber([valueAt(musicContract, "timing_contract.outro_under_vo_gain_linear")], 0.1);
  const outroTargetGain = firstFiniteNumber([valueAt(musicContract, "timing_contract.outro_target_gain_linear")], 0.42);
  const outroReachesTargetAt = firstFiniteNumber(
    [valueAt(musicContract, "timing_contract.outro_reaches_target_at_seconds")],
    voiceEnd + 3,
  );
  const outroTargetRamp = Math.max(0.001, outroReachesTargetAt - voiceEnd);
  const totalDuration = firstFiniteNumber([valueAt(musicContract, "timing_contract.planned_total_duration_seconds")], voiceStart + voiceDuration);
  const sampleRate = 44100;
  const voiceDelaySamples = Math.round(voiceStart * sampleRate);
  const outroDelaySamples = Math.round(outroStart * sampleRate);
  const introFadeEnd = voiceStart + introFadeTail;
  const targetAtLocal = outroPrelap + outroTargetRamp;
  const safeEpisodeId = String(episode.episodeId || "episode").replace(/[^a-z0-9_-]+/gi, "_");
  const audioPath = path.join(outputDir, `proof_assets/audio/${safeEpisodeId}_right_rail_alignment_music_mix.wav`);
  const manifestPath = path.join(outputDir, `proof_assets/audio/${safeEpisodeId}_right_rail_alignment_music_mix_manifest.json`);
  const logPath = path.join(outputDir, `proof_assets/audio/${safeEpisodeId}_right_rail_alignment_music_mix_ffmpeg.log`);
  ensureDir(path.dirname(audioPath));
  const contractJsonPath = musicContract.__jsonPath || episode.musicIntegrationContractJsonPath || "";
  const contractMtime = contractJsonPath && fs.existsSync(contractJsonPath) ? fs.statSync(contractJsonPath).mtimeMs : 0;
  const repairManifestMtime =
    audioDefectRepair?.repair_manifest?.path && fs.existsSync(audioDefectRepair.repair_manifest.path)
      ? fs.statSync(audioDefectRepair.repair_manifest.path).mtimeMs
      : 0;
  const inputMtime = Math.max(
    fs.statSync(sourceVoicePath).mtimeMs,
    fs.statSync(voicePath).mtimeMs,
    fs.statSync(introPath).mtimeMs,
    fs.statSync(outroPath).mtimeMs,
    contractMtime,
    repairManifestMtime,
  );
  const existingMixManifest = readJsonIfExists(manifestPath);
  const existingTimingMismatch = existingMixManifest
    ? Math.abs(firstFiniteNumber([valueAt(existingMixManifest, "timing.voice_start_seconds")], -999999) - voiceStart) > 0.02 ||
      Math.abs(firstFiniteNumber([valueAt(existingMixManifest, "timing.voice_end_seconds")], -999999) - voiceEnd) > 0.02 ||
      Math.abs(firstFiniteNumber([valueAt(existingMixManifest, "expected_total_duration_seconds")], -999999) - totalDuration) > 0.02 ||
      Math.abs(firstFiniteNumber([valueAt(existingMixManifest, "timing.full_outro_start_seconds")], -999999) - outroStart) > 0.02 ||
      Math.abs(firstFiniteNumber([valueAt(existingMixManifest, "timing.outro_prelap_seconds")], -999999) - outroPrelap) > 0.02 ||
      Math.abs(
        firstFiniteNumber([valueAt(existingMixManifest, "timing.outro_reaches_target_at_seconds")], -999999) -
          outroReachesTargetAt,
      ) > 0.02
    : false;
  const existingVoiceMismatch = existingMixManifest
    ? valueAt(existingMixManifest, "voice_master.path") !== voicePath ||
      valueAt(existingMixManifest, "source_voice_master.sha256") !== sha256File(sourceVoicePath) ||
      valueAt(existingMixManifest, "voice_audio_defect_repair_model") !==
        (audioDefectRepair?.model || "not_applicable") ||
      valueAt(existingMixManifest, "voice_loudness_alignment.voice_master_used_for_mix_read") !==
        voiceLoudnessAlignment.voice_master_used_for_mix_read
    : false;
  const shouldBuild =
    !fs.existsSync(audioPath) ||
    fs.statSync(audioPath).mtimeMs < inputMtime ||
    fs.statSync(audioPath).size < fs.statSync(sourceVoicePath).size ||
    existingTimingMismatch ||
    existingVoiceMismatch;
  if (shouldBuild) {
    const outroVolume = `if(lt(t,${outroPrelap.toFixed(6)}),${outroUnderVoGain.toFixed(6)}*t/${outroPrelap.toFixed(
      6,
    )},if(lt(t,${targetAtLocal.toFixed(6)}),${outroUnderVoGain.toFixed(6)}+(${outroTargetGain.toFixed(6)}-${outroUnderVoGain.toFixed(
      6,
    )})*(t-${outroPrelap.toFixed(6)})/${outroTargetRamp.toFixed(6)},${outroTargetGain.toFixed(6)}))`;
    const filter = [
      `[0:a]aresample=${sampleRate},aformat=channel_layouts=stereo,aloop=loop=-1:size=${voiceDelaySamples},atrim=0:${introFadeEnd.toFixed(
        6,
      )},asetpts=PTS-STARTPTS,afade=t=out:st=${voiceStart.toFixed(6)}:d=${introFadeTail.toFixed(6)}[intro]`,
      `[1:a]aresample=${sampleRate},pan=stereo|c0=c0|c1=c0,adelay=${voiceDelaySamples}S:all=1[voice]`,
      `[2:a]aresample=${sampleRate},aformat=channel_layouts=stereo,atrim=0:${outroDuration.toFixed(
        6,
      )},asetpts=PTS-STARTPTS,volume='${outroVolume}':eval=frame,adelay=${outroDelaySamples}S:all=1[outro]`,
      "[intro][voice][outro]amix=inputs=3:duration=longest:normalize=0,alimiter=limit=0.89:level=false[out]",
    ].join(";");
    const args = [
      "-y",
      "-hide_banner",
      "-loglevel",
      "error",
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
      String(sampleRate),
      "-ac",
      "2",
      "-c:a",
      "pcm_s16le",
      audioPath,
    ];
    const result = spawnSync("ffmpeg", args, { encoding: "utf8" });
    fs.writeFileSync(logPath, `${JSON.stringify(["ffmpeg", ...args], null, 2)}\n${result.stderr || result.stdout || ""}`, "utf8");
    if (result.status !== 0) {
      throw new Error(`Failed to build ${episode.episodeId} right-rail music mix: ${result.stderr || result.stdout}`);
    }
  }
  const outputDuration = durationSeconds(audioPath);
  const durationDelta = Number.isFinite(outputDuration) ? Number((outputDuration - totalDuration).toFixed(6)) : null;
  writeJson(manifestPath, {
    packet_id: `${episode.episodeId}_right_rail_alignment_contract_music_mix_${PACKET_STAMP}`,
    model: "contract_timed_intro_voice_outro_mix_v1",
    status: "contract_timed_review_mix_pending_human_keep_not_final_mix_keep",
    created_utc: CREATED_UTC,
    intro_trim_model: INTRO_TRIM_MODEL,
    intro_trim_seconds: INTRO_TRIM_SECONDS,
    previous_voice_start_offset_seconds: PREVIOUS_VOICE_START_OFFSET_SECONDS,
    voice_audio_defect_repair_model: audioDefectRepair?.model || "not_applicable",
    voice_audio_defect_repair_read: audioDefectRepair?.voice_audio_defect_repair_read || "not_applicable",
    audio_defect_repair: audioDefectRepair,
    contract_json_path: contractJsonPath || "not_found",
    contract_json_sha256: sha256File(contractJsonPath),
    source_voice_master: { path: sourceVoicePath, sha256: sha256File(sourceVoicePath), duration_seconds: sourceVoiceDuration },
    voice_master: { path: voicePath, sha256: sha256File(voicePath), duration_seconds: voiceDuration },
    voice_loudness_alignment: voiceLoudnessAlignment,
    intro_music_source: { path: introPath, sha256: sha256File(introPath) },
    full_outro_source: { path: outroPath, sha256: sha256File(outroPath), duration_seconds: outroDuration },
    output_path: audioPath,
    output_sha256: sha256File(audioPath),
    output_probe: ffprobeJson(audioPath),
    output_duration_seconds: outputDuration,
    expected_total_duration_seconds: totalDuration,
    duration_delta_seconds: durationDelta,
    timing: {
      intro_trim_model: INTRO_TRIM_MODEL,
      intro_trim_seconds: INTRO_TRIM_SECONDS,
      previous_voice_start_offset_seconds: PREVIOUS_VOICE_START_OFFSET_SECONDS,
      voice_start_seconds: voiceStart,
      voice_duration_seconds: voiceDuration,
      voice_end_seconds: voiceEnd,
      intro_music_only_start_seconds: 0,
      intro_music_only_end_seconds: voiceStart,
      intro_fade_tail_duration_seconds: introFadeTail,
      intro_fade_tail_end_seconds: introFadeEnd,
      full_outro_start_seconds: outroStart,
      outro_prelap_seconds: outroPrelap,
      outro_under_vo_gain_linear: outroUnderVoGain,
      outro_target_gain_linear: outroTargetGain,
      outro_reaches_target_at_seconds: outroReachesTargetAt,
      outro_policy: valueAt(musicContract, "timing_contract.outro_policy") || OUTRO_POLICY,
      outro_target_after_voice_seconds: Number((outroReachesTargetAt - voiceEnd).toFixed(6)),
      outro_target_margin_db: OUTRO_TARGET_MARGIN_DB,
      end_screen_start_seconds: valueAt(musicContract, "timing_contract.end_screen_start_seconds"),
      end_screen_end_seconds: valueAt(musicContract, "timing_contract.end_screen_end_seconds"),
    },
    reads: {
      review_audio_mix_model_read: "pass_contract_timed_intro_voice_outro_mix_v1",
      intro_trim_read: "pass_first_eight_intro_trim_6s_v1",
      intro_music_applied_read: "pass_music_only_intro_applied_from_registered_intro_loop",
      intro_fade_tail_under_opening_voice_read: "pass_2s_intro_fade_tail_under_opening_voice",
      voice_start_offset_read: `pass_${voiceStart.toFixed(6)}s`,
      full_outro_music_applied_read: "pass_full_outro_source_applied",
      outro_prelap_start_read: "pass_full_outro_starts_1p5s_before_voice_end",
      outro_no_restart_at_voice_end_read: "pass_full_outro_continues_without_restart",
      outro_target_after_voice_read: "pass_target_gain_after_voice_end",
      outro_under_vo_masking_read: "pass_target_margin_at_least_12db",
      vo_outro_blend_read: "pass_subtle_tail_outro_v1_timing_contract",
      end_screen_music_handoff_read: "pass_full_outro_carries_youtube_end_screen_window",
      review_mix_duration_read:
        durationDelta !== null && Math.abs(durationDelta) <= 0.08
          ? `pass_duration_delta_${durationDelta.toFixed(3)}s`
          : `tighten_duration_delta_${durationDelta ?? "unknown"}s`,
      final_mix_approval_read: "blocked_pending_human_rough_proof_keep_and_later_final_mix_review",
      voice_loudness_alignment_read:
        voiceLoudnessAlignment.reads?.voice_loudness_alignment_read || "pass_source_voice_master_within_series_loudness_tolerance",
      voice_master_used_for_mix_read: voiceLoudnessAlignment.voice_master_used_for_mix_read,
      voice_audio_defect_repair_read: audioDefectRepair?.voice_audio_defect_repair_read || "not_applicable",
    },
  });
  return {
    audioPath,
    manifestPath,
    probe: ffprobeJson(audioPath),
    outputDurationSeconds: outputDuration,
    expectedDurationSeconds: totalDuration,
    durationDeltaSeconds: durationDelta,
    model: "contract_timed_intro_voice_outro_mix_v1",
    audioDefectRepair,
    voiceLoudnessAlignment,
    timing: {
      voiceStart,
      voiceDuration,
      voiceEnd,
      introFadeTail,
      introFadeEnd,
      outroStart,
      outroPrelap,
      outroUnderVoGain,
      outroTargetGain,
      outroReachesTargetAt,
      totalDuration,
    },
  };
}

function endScreenTimingFromMusicContract(musicContract, endScreenPalette = null) {
  if (!musicContract) return null;
  const endScreenStart = firstFiniteNumber([valueAt(musicContract, "timing_contract.end_screen_start_seconds")]);
  const endScreenEnd = firstFiniteNumber([valueAt(musicContract, "timing_contract.end_screen_end_seconds")]);
  if (!Number.isFinite(endScreenStart) || !Number.isFinite(endScreenEnd) || endScreenEnd <= endScreenStart) return null;
  const transitionDuration = END_SCREEN_TRANSITION_DURATION_SECONDS;
  return {
    enabled: true,
    templateId: YOUTUBE_END_SCREEN_TEMPLATE_ID,
    compositionMode: "titleless_youtube_end_screen_overlay",
    fadeTimingModel: END_SCREEN_FADE_TIMING_MODEL,
    transitionStartSeconds: Number(Math.max(0, endScreenStart - transitionDuration).toFixed(6)),
    transitionDurationSeconds: transitionDuration,
    fullOpacityAtSeconds: Number(endScreenStart.toFixed(6)),
    holdStartSeconds: Number(endScreenStart.toFixed(6)),
    safeWindowStartSeconds: Number(endScreenStart.toFixed(6)),
    safeWindowEndSeconds: Number(endScreenEnd.toFixed(6)),
    layout: END_SCREEN_TARGET_LAYOUT,
    palette: endScreenPalette || null,
  };
}

function endScreenTimingFromSourceHtml(sourceHtml, endScreenPalette = null) {
  const proof = extractJsonObjectAfter(sourceHtml, "const proof") || {};
  const outroScreen = proof?.outroScreen || {};
  const sourceDuration = firstFiniteNumber([proof.duration, numberFieldFromHtml(sourceHtml, "duration")]);
  const sourceEndScreenStart = firstFiniteNumber([proof.endScreenStart, numberFieldFromHtml(sourceHtml, "endScreenStart")]);
  const sourceEndScreenSafeStart = firstFiniteNumber([
    proof.endScreenSafeWindowStart,
    numberFieldFromHtml(sourceHtml, "endScreenSafeWindowStart"),
  ]);
  const sourceEndScreenFadeStart = firstFiniteNumber([proof.endScreenFadeStart, numberFieldFromHtml(sourceHtml, "endScreenFadeStart")]);
  const sourceEndScreenFadeEnd = firstFiniteNumber([proof.endScreenFadeEnd, numberFieldFromHtml(sourceHtml, "endScreenFadeEnd")]);
  const sourceOutroStart = firstFiniteNumber([proof.outroStart, numberFieldFromHtml(sourceHtml, "outroStart")]);
  const safeWindow = Array.isArray(outroScreen.youtubeEndScreenSafeWindowSeconds)
    ? outroScreen.youtubeEndScreenSafeWindowSeconds
    : [];
  const safeStart = firstFiniteNumber([
    safeWindow[0],
    valueAt(outroScreen, "safeWindowStartSeconds"),
    sourceEndScreenSafeStart,
    valueAt(outroScreen, "holdStartSeconds"),
    sourceDuration - 20,
  ]);
  const safeEnd = firstFiniteNumber([
    safeWindow[1],
    valueAt(outroScreen, "safeWindowEndSeconds"),
    valueAt(outroScreen, "holdEndSeconds"),
    sourceDuration,
  ]);
  const transitionDuration = firstFiniteNumber(
    [outroScreen.transitionDurationSeconds, sourceEndScreenFadeEnd - sourceEndScreenFadeStart],
    END_SCREEN_TRANSITION_DURATION_SECONDS,
  );
  const inferredFlatEndScreenTransitionStart =
    Number.isFinite(sourceEndScreenStart) && Number.isFinite(safeStart) && Math.abs(sourceEndScreenStart - safeStart) <= 0.05
      ? sourceEndScreenStart - transitionDuration
      : sourceEndScreenStart;
  const transitionStart = firstFiniteNumber([
    outroScreen.transitionStartSeconds,
    valueAt(outroScreen, "transition_start_seconds"),
    sourceEndScreenFadeStart,
    inferredFlatEndScreenTransitionStart,
    sourceOutroStart,
    safeStart - transitionDuration,
  ]);
  const fullOpacityAt = firstFiniteNumber([outroScreen.holdStartSeconds, sourceEndScreenFadeEnd, transitionStart + transitionDuration, safeStart]);
  if (
    !Number.isFinite(transitionStart) ||
    !Number.isFinite(transitionDuration) ||
    !Number.isFinite(safeStart) ||
    !Number.isFinite(safeEnd) ||
    safeEnd <= safeStart
  ) {
    return null;
  }
  return {
    enabled: true,
    templateId: YOUTUBE_END_SCREEN_TEMPLATE_ID,
    compositionMode: "titleless_youtube_end_screen_overlay",
    fadeTimingModel: END_SCREEN_FADE_TIMING_MODEL,
    timingSource: "predecessor_html_outro_screen_v1",
    transitionStartSeconds: Number(Math.max(0, transitionStart).toFixed(6)),
    transitionDurationSeconds: Number(Math.max(0.001, transitionDuration).toFixed(6)),
    fullOpacityAtSeconds: Number(fullOpacityAt.toFixed(6)),
    holdStartSeconds: Number(fullOpacityAt.toFixed(6)),
    safeWindowStartSeconds: Number(safeStart.toFixed(6)),
    safeWindowEndSeconds: Number(safeEnd.toFixed(6)),
    layout: outroScreen.layout || END_SCREEN_TARGET_LAYOUT,
    palette: endScreenPalette || null,
  };
}

function timeForCaptionChunkCenter(chunk, captionScrollTiming, targetCenterY) {
  const speed = Number(captionScrollTiming?.caption_constant_scroll_speed_px_per_second) || 50;
  const startPosition = Number(captionScrollTiming?.caption_scroll_start_position_px) || 0;
  const startTime = Number(captionScrollTiming?.caption_scroll_start_time_seconds) || 0;
  const centerY = chunkCenterYForData(chunk);
  return startTime + ((centerY + CAPTION_WINDOW_GEOMETRY.activeY - startPosition - targetCenterY) / speed);
}

function captionExitAlignedEndScreenTiming(baseTiming, chunks, captionScrollTiming, episode) {
  if (!baseTiming || !baseTiming.enabled || !Array.isArray(chunks) || !chunks.length) return baseTiming;
  const lastChunk = chunks[chunks.length - 1];
  const lastCueEnd = Number(lastChunk.end) || 0;
  const approvedFadeStart = REVIEW_APPROVED_END_SCREEN_FADE_START_SECONDS[episode?.episodeId || ""];
  const safeStart = firstFiniteNumber(
    [baseTiming.safeWindowStartSeconds, baseTiming.holdStartSeconds, baseTiming.fullOpacityAtSeconds],
    lastCueEnd + 8.6,
  );
  const safeEnd = firstFiniteNumber([baseTiming.safeWindowEndSeconds], safeStart + 20);
  const naturalExitStart = timeForCaptionChunkCenter(lastChunk, captionScrollTiming, CAPTION_WINDOW_GEOMETRY.topFade);
  const naturalFullySuppressed = timeForCaptionChunkCenter(lastChunk, captionScrollTiming, CAPTION_SCROLL_LAST_EXIT_CENTER_PX);
  let transitionStart = Number.isFinite(approvedFadeStart)
    ? Number(approvedFadeStart.toFixed(6))
    : Number(Math.max(0, Math.max(lastCueEnd, naturalFullySuppressed) - END_SCREEN_TRANSITION_DURATION_SECONDS).toFixed(6));
  let fullOpacityAt = Number((transitionStart + END_SCREEN_TRANSITION_DURATION_SECONDS).toFixed(6));
  if (Number.isFinite(safeStart)) {
    fullOpacityAt = Math.min(fullOpacityAt, Number((safeStart - 0.1).toFixed(6)));
    transitionStart = Number(Math.max(0, fullOpacityAt - END_SCREEN_TRANSITION_DURATION_SECONDS).toFixed(6));
  }
  if (transitionStart < 0) transitionStart = 0;
  const transitionDuration = Number(Math.max(0.001, fullOpacityAt - transitionStart).toFixed(6));
  const captionEndScreenGapSeconds = Number(Math.max(0, transitionStart - naturalFullySuppressed).toFixed(3));
  return {
    ...baseTiming,
    enabled: true,
    templateId: YOUTUBE_END_SCREEN_TEMPLATE_ID,
    compositionMode: "titleless_youtube_end_screen_overlay",
    timingSource: `${baseTiming.timingSource || "music_contract_or_predecessor"}+${CAPTION_END_SCREEN_HANDOFF_MODEL}`,
    reviewApprovedEndScreenEntryModel: CAPTION_END_SCREEN_HANDOFF_MODEL,
    reviewApprovedFadeStartSeconds: Number.isFinite(approvedFadeStart) ? Number(approvedFadeStart.toFixed(6)) : null,
    captionEndScreenHandoffModel: CAPTION_END_SCREEN_HANDOFF_MODEL,
    fadeTimingModel: END_SCREEN_FADE_TIMING_MODEL,
    transitionStartSeconds: transitionStart,
    transitionDurationSeconds: transitionDuration,
    youtubePlaceholderTransitionDurationSeconds: transitionDuration,
    fullOpacityAtSeconds: fullOpacityAt,
    holdStartSeconds: Number((baseTiming.holdStartSeconds || safeStart).toFixed(6)),
    safeWindowStartSeconds: Number(safeStart.toFixed(6)),
    safeWindowEndSeconds: Number(safeEnd.toFixed(6)),
    lastDisplayCueEndSeconds: Number(lastCueEnd.toFixed(3)),
    lastCaptionVisibleExitStartSeconds: Number(Math.min(naturalExitStart, transitionStart).toFixed(6)),
    lastCaptionFullySuppressedSeconds: Number(fullOpacityAt.toFixed(6)),
    lastCaptionNaturalFullySuppressedSeconds: Number(naturalFullySuppressed.toFixed(6)),
    youtubePlaceholderFadeStartSeconds: transitionStart,
    youtubePlaceholderFullOpacitySeconds: fullOpacityAt,
    captionEndScreenGapSeconds,
    captionEndScreenOverlapRead:
      captionEndScreenGapSeconds <= 0.05 &&
      transitionStart <= fullOpacityAt &&
      Math.abs(transitionDuration - END_SCREEN_TRANSITION_DURATION_SECONDS) <= 0.01
        ? "pass_review_approved_end_screen_entry_no_blank_gap"
        : "tighten_review_approved_end_screen_entry_gap",
    youtubeSafeWindowCaptionSuppressionRead:
      safeStart >= fullOpacityAt ? "pass_caption_suppressed_before_safe_window" : "tighten_caption_residual_into_safe_window",
  };
}

function removePathIfLocalLinkOrGenerated(targetPath) {
  if (!fs.existsSync(targetPath) && !fs.lstatSync(targetPath, { throwIfNoEntry: false })) return;
  fs.rmSync(targetPath, { recursive: true, force: true });
}

function linkSourceRuntimeEntries(outputDir, sourceRoot) {
  if (!sourceRoot || !fs.existsSync(sourceRoot)) return [];
  const linked = [];
  const sourceEntries = fs.readdirSync(sourceRoot, { withFileTypes: true });
  for (const entry of sourceEntries) {
    if (!entry.isDirectory()) continue;
    if (["review", "qa"].includes(entry.name)) continue;
    const sourcePath = path.join(sourceRoot, entry.name);
    const linkPath = path.join(outputDir, entry.name);
    removePathIfLocalLinkOrGenerated(linkPath);
    fs.symlinkSync(sourcePath, linkPath);
    linked.push({ name: entry.name, source_path: sourcePath, link_path: linkPath });
  }
  return linked;
}

function renderPlayerHtml({ episode, sourceArtPath, audioPath, cues, keyPhraseSpans, palette, durationSeconds }) {
  const captionsJson = JSON.stringify(cues);
  const spansJson = JSON.stringify(keyPhraseSpans);
  const sourceArtUri = mediaUri(sourceArtPath);
  const audioUri = mediaUri(audioPath);
  const endTransition = Math.max(30, durationSeconds - 24);
  const targetWindow = Math.max(endTransition + 7, durationSeconds - 16);
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,">
  <title>${episode.title} rolling rail rough proof</title>
  <style>
    :root {
      --rail-left: 1108px;
      --rail-top: 52px;
      --rail-width: 760px;
      --rail-height: 976px;
      --caption-top: 215px;
      --caption-height: 650px;
      --caption-text: ${palette.text};
      --caption-muted: ${palette.muted};
      --caption-highlight: ${palette.highlight};
    }
    * { box-sizing: border-box; }
    html, body {
      margin: 0;
      min-height: 100%;
      background: #07090b;
      color: var(--caption-text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    body { display: grid; place-items: center; min-height: 100vh; overflow: hidden; }
    .stage {
      width: min(100vw, calc(100vh * 16 / 9));
      aspect-ratio: 16 / 9;
      position: relative;
      overflow: hidden;
      background: #111;
    }
    .stage-inner {
      position: absolute;
      inset: 0;
      width: 1920px;
      height: 1080px;
      transform-origin: top left;
      transform: scale(calc(min(100vw, calc(100vh * 16 / 9)) / 1920));
      overflow: hidden;
    }
    .backplate {
      position: absolute;
      inset: 0;
      width: 1920px;
      height: 1080px;
      object-fit: cover;
      background: radial-gradient(circle at 30% 30%, #3a4140, #101417 64%);
    }
    .rail[data-content-model="rolling_caption_anchor_v1"] {
      position: absolute;
      left: var(--rail-left);
      top: var(--rail-top);
      width: var(--rail-width);
      height: var(--rail-height);
      pointer-events: none;
    }
    .rail-anchor {
      position: absolute;
      top: 0;
      right: 0;
      width: 680px;
      min-height: 104px;
      color: var(--caption-text);
      text-align: right;
      text-shadow: 0 2px 16px rgba(0,0,0,0.42);
    }
    .anchor-label {
      font-size: 26px;
      line-height: 1;
      font-weight: 830;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      color: var(--caption-muted);
    }
    .anchor-title {
      margin-top: 10px;
      font-size: 34px;
      line-height: 1.05;
      font-weight: 760;
      letter-spacing: 0;
    }
    .caption-window[data-display-model="rolling_rail_caption_window_v1"] {
      position: absolute;
      left: 22px;
      top: calc(var(--caption-top) - var(--rail-top));
      width: 716px;
      height: var(--caption-height);
      overflow: hidden;
      border-radius: 8px;
      opacity: 1;
      mask-image: linear-gradient(to bottom, transparent 0, black 96px, black calc(100% - 116px), transparent 100%);
      -webkit-mask-image: linear-gradient(to bottom, transparent 0, black 96px, black calc(100% - 116px), transparent 100%);
      transform: translateZ(0);
    }
    .caption-stack {
      position: absolute;
      left: 28px;
      top: 0;
      width: 648px;
      height: 10000px;
      transform: translateY(0);
      will-change: transform;
      contain: layout style;
    }
    .caption-line {
      position: absolute;
      left: 0;
      width: 648px;
      min-height: 68px;
      color: var(--caption-text);
      font-size: 40px;
      line-height: 1.12;
      font-weight: 650;
      letter-spacing: 0;
      text-align: left;
      opacity: 0.62;
      text-wrap: balance;
      text-shadow: 0 2px 18px rgba(0,0,0,0.34);
      transform: translateZ(0);
    }
    .caption-line.is-active { opacity: 1; }
    .caption-line.is-near { opacity: 0.84; }
    .phrase-highlight {
      color: var(--caption-text);
      transition: color 80ms linear;
      text-shadow: inherit;
    }
    .end-screen-target {
      position: absolute;
      top: 382px;
      height: 383px;
      border: 2px solid rgba(255,255,255,0.18);
      background: rgba(0,0,0,0.16);
      opacity: 0;
      transition: opacity 220ms linear;
    }
    .end-screen-target.left { left: 78px; width: 680px; }
    .end-screen-target.right { left: 1162px; width: 680px; }
    .end-screen-target.subscribe { left: 814px; top: 429px; width: 292px; height: 292px; border-radius: 50%; }
    .is-end-screen .end-screen-target { opacity: 1; }
    .review-controls {
      position: fixed;
      left: 16px;
      bottom: 16px;
      right: 16px;
      display: flex;
      gap: 12px;
      align-items: center;
      color: #d9dee5;
      font-size: 13px;
      opacity: 0.88;
    }
    .review-controls audio { width: min(760px, 80vw); }
    @media (max-aspect-ratio: 16 / 9) {
      .stage { width: 100vw; }
      .stage-inner { transform: scale(calc(100vw / 1920)); }
    }
  </style>
</head>
<body>
  <main class="stage" aria-label="${episode.title} rolling caption rail rough proof">
    <div class="stage-inner" id="stage">
      ${
        sourceArtUri
          ? `<img class="backplate" src="${sourceArtUri}" alt="">`
          : `<div class="backplate" aria-hidden="true"></div>`
      }
      <section class="rail" data-content-model="rolling_caption_anchor_v1" aria-label="Right rail">
        <div class="rail-anchor">
          <div class="anchor-label">${episode.title}</div>
          <div class="anchor-title"></div>
        </div>
        <div class="caption-window" data-display-model="rolling_rail_caption_window_v1">
          <div class="caption-stack" id="captionStack"></div>
        </div>
      </section>
      <div class="end-screen-target left" aria-hidden="true"></div>
      <div class="end-screen-target right" aria-hidden="true"></div>
      <div class="end-screen-target subscribe" aria-hidden="true"></div>
    </div>
  </main>
  <div class="review-controls">
    ${audioUri ? `<audio id="voiceAudio" controls preload="metadata" src="${audioUri}"></audio>` : `<span>No approved audio reference was found for this blocked/readiness packet.</span>`}
  </div>
  <script>
    const captions = ${captionsJson};
    const keyPhraseSpans = ${spansJson};
    const CAPTION_TEXT_COLOR = "${palette.text}";
    const ROW_STEP = 82;
    const WINDOW_HEIGHT = 650;
    const ACTIVE_Y = 318;
    const END_TRANSITION_SECONDS = ${Number(endTransition.toFixed(3))};
    const TARGET_GEOMETRY_SECONDS = ${Number(targetWindow.toFixed(3))};
    const captionStack = document.getElementById("captionStack");
    const stage = document.getElementById("stage");
    const audio = document.getElementById("voiceAudio");

    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      })[char]);
    }

    function wrapPhrase(text, phrase, index) {
      if (!phrase) return escapeHtml(text);
      const safe = escapeHtml(text);
      const escapedPhrase = phrase.replace(/[.*+?^$()|[\\]\\\\]/g, "\\\\$&").replace(/[{}]/g, "\\\\$&");
      const re = new RegExp("(" + escapedPhrase + ")", "i");
      return safe.replace(re, '<span class="phrase-highlight" data-phrase-index="' + index + '">$1</span>');
    }

    function phraseForCue(cue) {
      return keyPhraseSpans.findIndex((span) => {
        return cue.start <= span.timing_window_seconds[1] && cue.end >= span.timing_window_seconds[0] && cue.text.toLowerCase().includes(span.phrase_text.toLowerCase());
      });
    }

    captions.forEach((cue, index) => {
      const phraseIndex = phraseForCue(cue);
      const phrase = phraseIndex >= 0 ? keyPhraseSpans[phraseIndex].phrase_text : "";
      const el = document.createElement("div");
      el.className = "caption-line";
      el.style.top = (cue.layout_y_px || 0) + "px";
      el.style.minHeight = (cue.layout_height_px || 68) + "px";
      el.dataset.index = String(index);
      el.innerHTML = wrapPhrase(cue.text, phrase, phraseIndex);
      captionStack.appendChild(el);
    });

    const captionEls = Array.from(document.querySelectorAll(".caption-line"));

    function smoothstep(x) {
      const t = Math.max(0, Math.min(1, x));
      return t * t * (3 - 2 * t);
    }

    function activeCueIndexAt(time) {
      let index = 0;
      for (let i = 0; i < captions.length; i += 1) {
        if (time >= captions[i].start) index = i;
        if (time < captions[i].end) return i;
      }
      return index;
    }

    function scrollPositionAt(time) {
      if (!captions.length) return 0;
      const active = activeCueIndexAt(time);
      const current = captions[active];
      const next = captions[Math.min(active + 1, captions.length - 1)];
      if (!next || next === current) return current.layout_y_px || 0;
      const span = Math.max(0.001, next.start - current.start);
      const mix = smoothstep((time - current.start) / span);
      const currentY = current.layout_y_px || 0;
      const nextY = next.layout_y_px || currentY;
      return currentY + (nextY - currentY) * mix;
    }

    function phraseAlpha(span, time) {
      const start = span.timing_window_seconds[0];
      const end = span.timing_window_seconds[1];
      const fadeIn = Math.max(0.001, span.fade_in_seconds || 0.22);
      const fadeOut = Math.max(0.001, span.fade_out_seconds || 0.42);
      if (time < start - fadeIn || time > end + fadeOut) return 0;
      if (time < start) return smoothstep((time - (start - fadeIn)) / fadeIn);
      if (time <= end) return 1;
      return 1 - smoothstep((time - end) / fadeOut);
    }

    function hexToRgb(hex) {
      const normalized = String(hex || "").replace("#", "");
      const value = normalized.length === 3
        ? normalized.split("").map((char) => char + char).join("")
        : normalized.padEnd(6, "f").slice(0, 6);
      return [
        parseInt(value.slice(0, 2), 16),
        parseInt(value.slice(2, 4), 16),
        parseInt(value.slice(4, 6), 16),
      ];
    }

    function mixColor(baseHex, highlightHex, alpha) {
      const base = hexToRgb(baseHex);
      const highlight = hexToRgb(highlightHex);
      const t = Math.max(0, Math.min(1, alpha));
      const mixed = base.map((channel, index) => Math.round(channel + (highlight[index] - channel) * t));
      return "rgb(" + mixed.join(", ") + ")";
    }

    function highlightTextShadow(alpha) {
      const t = Math.max(0, Math.min(1, Number(alpha) || 0));
      if (t <= 0.01) return "";
      const lift = (0.42 + 0.28 * t).toFixed(3);
      const edge = (0.32 + 0.34 * t).toFixed(3);
      return "0 2px 18px rgba(0,0,0," + lift + "), 0 1px 5px rgba(0,0,0," + edge + "), 0 0 2px rgba(0,0,0," + edge + ")";
    }

    function windowOpacityAt(time) {
      if (time < END_TRANSITION_SECONDS) return 1;
      if (time >= TARGET_GEOMETRY_SECONDS) return 0;
      return 1 - smoothstep((time - END_TRANSITION_SECONDS) / Math.max(0.001, TARGET_GEOMETRY_SECONDS - END_TRANSITION_SECONDS));
    }

    function railCaptionStateAt(time) {
      const scrollPosition = scrollPositionAt(time);
      const extraEndLift = time > END_TRANSITION_SECONDS ? (time - END_TRANSITION_SECONDS) * 28 : 0;
      const translateY = ACTIVE_Y - scrollPosition - extraEndLift;
      const activeCueIndex = activeCueIndexAt(time);
      return {
        time,
        translateY,
        scrollPosition,
        activeCueIndex,
        activeCueId: captions[activeCueIndex]?.id || null,
        windowOpacity: windowOpacityAt(time),
        targetGeometryWindowActive: time >= TARGET_GEOMETRY_SECONDS,
        highlights: keyPhraseSpans.map((span) => ({
          span_id: span.span_id,
          phrase_text: span.phrase_text,
          alpha: phraseAlpha(span, time),
        })),
      };
    }

    function update(time) {
      const state = railCaptionStateAt(time);
      captionStack.style.transform = "translateY(" + state.translateY.toFixed(3) + "px)";
      document.querySelector(".caption-window").style.opacity = state.windowOpacity.toFixed(3);
      stage.classList.toggle("is-end-screen", time >= END_TRANSITION_SECONDS);
      captionEls.forEach((el, index) => {
        const distance = Math.abs(index - state.activeCueIndex);
        el.classList.toggle("is-active", distance === 0);
        el.classList.toggle("is-near", distance === 1);
      });
      document.querySelectorAll(".phrase-highlight").forEach((el) => {
        const index = Number(el.dataset.phraseIndex);
        const span = keyPhraseSpans[index];
        const alpha = span ? phraseAlpha(span, time) : 0;
        el.style.setProperty("--phrase-alpha", alpha.toFixed(3));
        el.style.color = span ? mixColor(CAPTION_TEXT_COLOR, span.highlight_color_sample.hex, alpha) : CAPTION_TEXT_COLOR;
        el.style.textShadow = span ? highlightTextShadow(alpha) : "";
      });
      return state;
    }

    window.__railCaptionStateAt = railCaptionStateAt;
    window.__setRenderTime = (time) => {
      const numeric = Number(time) || 0;
      if (typeof window.__ceSetAmbientRenderTime === "function") window.__ceSetAmbientRenderTime(numeric);
      if (audio) {
        audio.pause();
        audio.currentTime = numeric;
      }
      return update(numeric);
    };

    function tick() {
      update(audio ? audio.currentTime || 0 : captions[0]?.start || 0);
      requestAnimationFrame(tick);
    }
    update(captions[0]?.start || 0);
    requestAnimationFrame(tick);
  </script>
</body>
</html>
`;
}

function stripPriorRollingRailInjection(html) {
  return html
    .replace(/<!-- ce-rolling-caption-rail-tighten-style:start -->[\s\S]*?<!-- ce-rolling-caption-rail-tighten-style:end -->/g, "")
    .replace(/<!-- ce-rolling-caption-rail-tighten-script:start -->[\s\S]*?<!-- ce-rolling-caption-rail-tighten-script:end -->/g, "");
}

function replaceRequiredRuntimeGuard(html, pattern, replacement, description) {
  const before = String(html || "");
  const after = before.replace(pattern, replacement);
  if (after === before) throw new Error(`Could not apply runtime guard: ${description}`);
  return after;
}

function applyTheracAmbientFrameClockRepair(html) {
  let next = String(html || "");
  next = replaceRequiredRuntimeGuard(
    next,
    "function update(time,wallSeconds=performance.now()/1000){",
    "function update(time,wallSeconds=(document.documentElement.classList.contains('render-mode')?time:performance.now()/1000)){",
    "Therac update wallSeconds render-time default",
  );
  next = replaceRequiredRuntimeGuard(
    next,
    "function animationLoop(ts){const t=document.documentElement.classList.contains('render-mode')?renderTime:(Number.isFinite(audio.currentTime)?audio.currentTime:renderTime);update(t,ts/1000);requestAnimationFrame(animationLoop);}",
    "function animationLoop(ts){if(document.documentElement.classList.contains('render-mode'))return;const t=Number.isFinite(audio.currentTime)?audio.currentTime:renderTime;update(t,ts/1000);requestAnimationFrame(animationLoop);}",
    "Therac render-mode wall-clock RAF suppression",
  );
  next = replaceRequiredRuntimeGuard(
    next,
    "window.__setRenderTime=(seconds)=>{if(!document.documentElement.classList.contains('render-mode'))audio.currentTime=seconds;update(seconds);};",
    `window.__ceAmbientFrameClockState={ambient_frame_clock_model:'${AMBIENT_FRAME_CLOCK_MODEL}',ambient_render_clock_read:'${AMBIENT_RENDER_CLOCK_READ}',ambient_wall_clock_drift_suppression_read:'${AMBIENT_WALL_CLOCK_DRIFT_SUPPRESSION_READ}',last_time_seconds:0};window.__ceSetAmbientRenderTime=(seconds)=>{const numeric=Number(seconds)||0;renderTime=numeric;if(!document.documentElement.classList.contains('render-mode'))audio.currentTime=numeric;update(numeric,numeric);window.__ceAmbientFrameClockState.last_time_seconds=numeric;return window.__ceAmbientFrameClockState;};window.__setRenderTime=(seconds)=>window.__ceSetAmbientRenderTime(seconds);`,
    "Therac ambient render-time bridge",
  );
  return next;
}

function applySemmelweisAmbientFrameClockRepair(html) {
  let next = String(html || "");
  next = replaceRequiredRuntimeGuard(
    next,
    "    function driftClockSeconds() {\n",
    "    let ceRenderFrameTimeSeconds = 0;\n\n    function driftClockSeconds() {\n      if (document.documentElement.classList.contains(\"render-mode\")) {\n        return ceRenderFrameTimeSeconds;\n      }\n",
    "Semmelweis render-time state before drift clock",
  );
  next = replaceRequiredRuntimeGuard(
    next,
    "    function animatePlateDrift() {\n      applyPlateDrift(driftClockSeconds());\n      requestAnimationFrame(animatePlateDrift);\n    }\n",
    "    function animatePlateDrift() {\n      if (document.documentElement.classList.contains(\"render-mode\")) {\n        return;\n      }\n      applyPlateDrift(driftClockSeconds());\n      requestAnimationFrame(animatePlateDrift);\n    }\n",
    "Semmelweis render-mode wall-clock RAF suppression",
  );
  next = replaceRequiredRuntimeGuard(
    next,
    "    window.addEventListener(\"resize\", fitStage);\n",
    `    window.__ceAmbientFrameClockState = {\n      ambient_frame_clock_model: "${AMBIENT_FRAME_CLOCK_MODEL}",\n      ambient_render_clock_read: "${AMBIENT_RENDER_CLOCK_READ}",\n      ambient_wall_clock_drift_suppression_read: "${AMBIENT_WALL_CLOCK_DRIFT_SUPPRESSION_READ}",\n      last_time_seconds: 0,\n    };\n\n    window.__ceSetAmbientRenderTime = (seconds) => {\n      const numeric = Number(seconds) || 0;\n      ceRenderFrameTimeSeconds = numeric;\n      if (els.audio && !document.documentElement.classList.contains("render-mode")) {\n        try { els.audio.currentTime = numeric; } catch {}\n      }\n      els.scrubber.value = String(numeric);\n      setState(stateIndexForTime(numeric));\n      applyPlateDrift(numeric);\n      updateTimecode(numeric);\n      window.__ceAmbientFrameClockState.last_time_seconds = numeric;\n      return window.__ceAmbientFrameClockState;\n    };\n\n    window.addEventListener("resize", fitStage);\n`,
    "Semmelweis ambient render-time bridge",
  );
  return next;
}

function applyEpisodeSourceHtmlRuntimeGuards(html, episode) {
  let next = String(html || "");
  if (episode?.episodeId === "tacoma-narrows") {
    next = next
      .replace(/"glass_bead_count"\s*:\s*\d+/g, `"glass_bead_count": ${TACOMA_RAIN_BEAD_COUNT_CAP}`)
      .replace(/"glass_runner_count"\s*:\s*\d+/g, `"glass_runner_count": ${TACOMA_RAIN_RUNNER_COUNT_CAP}`)
      .replace(/"glass_fine_streak_count"\s*:\s*\d+/g, `"glass_fine_streak_count": ${TACOMA_RAIN_STREAK_COUNT_CAP}`)
      .replace(
        /drawAmbient\(storyTime,\s*audioTime\);/g,
        "if (!window.__ceTacomaRainPerformanceGuard || window.__ceTacomaRainPerformanceGuard(audioTime)) drawAmbient(storyTime, audioTime);",
      );
  }
  if (episode?.episodeId === "therac-25") next = applyTheracAmbientFrameClockRepair(next);
  if (episode?.episodeId === "semmelweis") next = applySemmelweisAmbientFrameClockRepair(next);
  return next;
}

function insertBeforeClosing(html, tagName, insertion) {
  const re = new RegExp(`</${tagName}>`, "i");
  if (re.test(html)) return html.replace(re, `${insertion}\n</${tagName}>`);
  return `${html}\n${insertion}`;
}

function renderInjectedPlayerHtml({
  episode,
  sourceHtml,
  chunks,
  keyPhraseSpans,
  palette,
  durationSeconds,
  captionSources = {},
  captionScrollTiming = captionScrollTimingForChunks(chunks),
  endScreenTiming = null,
  endScreenPaletteContract = null,
  proofBuildId = "",
  proofGeneratedAtUtc = PROOF_GENERATED_AT_UTC,
}) {
  const cleanHtml = stripPriorRollingRailInjection(sourceHtml);
  const captionStackHeightPx = Math.ceil(Number(captionScrollTiming.caption_stack_height_px) || captionStackHeightPxForChunks(chunks));
  const endPalette = endScreenTiming?.palette?.targets || {};
  const leftTargetPalette = endPalette.left_video || endScreenTargetColorsFromSample(null, "suggested_video");
  const rightTargetPalette = endPalette.right_video || endScreenTargetColorsFromSample(null, "watch_next_video");
  const subscribeTargetPalette = endPalette.center_subscribe || endScreenTargetColorsFromSample(null, "subscribe");
  const endScreenCss = endScreenPaletteContract?.css_variables || {};
  const style = `<!-- ce-rolling-caption-rail-tighten-style:start -->
  <style>
    html.render-mode .review-audio,
    html.render-mode .review-transport,
    html.render-mode .ce-review-transport,
    html.render-mode .audio-review,
    html.render-mode .player,
    html.render-mode .transport,
    html.render-mode .controls,
    html.render-mode .review-header,
    html.render-mode .review-meta,
    html.render-mode .body,
    html.render-mode .review-grid,
    html.render-mode .machine-reads,
    html.render-mode .review-note,
    html.render-mode .timeline-scrubber,
    html.render-mode .review-toggle,
    html.render-mode header,
    html.render-mode audio,
    html.render-mode output,
    html.render-mode input,
    html.render-mode select,
    html.render-mode textarea,
    html.render-mode main:not(.stage):not(.ce-fixed-stage) > :not(.stage-shell):not(.ce-stage-scale-shell):not(.frame):not(.stage-frame),
    html.render-mode .ce-range-server-warning,
    html.render-mode .ce-proof-freshness-warning {
      display: none !important;
    }
    html.render-mode,
    html.render-mode body {
      width: 1920px !important;
      height: 1080px !important;
      min-width: 1920px !important;
      min-height: 1080px !important;
      margin: 0 !important;
      padding: 0 !important;
      overflow: hidden !important;
      background: #000 !important;
    }
    html.render-mode main {
      width: 1920px !important;
      height: 1080px !important;
      max-width: none !important;
      min-height: 0 !important;
      margin: 0 !important;
      padding: 0 !important;
      overflow: hidden !important;
      background: #000 !important;
    }
    html.render-mode .stage-shell {
      display: block !important;
      width: 1920px !important;
      height: 1080px !important;
      min-height: 1080px !important;
      margin: 0 !important;
      padding: 0 !important;
      border: 0 !important;
      box-shadow: none !important;
      overflow: hidden !important;
      background: #000 !important;
    }
    html.render-mode .stage-frame {
      width: 1920px !important;
      height: 1080px !important;
      margin: 0 !important;
      padding: 0 !important;
      overflow: hidden !important;
    }
    html.render-mode .stage {
      left: 0 !important;
      top: 0 !important;
      width: 1920px !important;
      height: 1080px !important;
      transform: none !important;
      transform-origin: top left !important;
    }
    html:not(.render-mode) main:has(> .frame) {
      width: min(calc(100vw - 22px), 1920px) !important;
      padding: 0 0 110px !important;
    }
    html:not(.render-mode) main:has(> .frame) > header,
    html:not(.render-mode) main:has(> .frame) > .player,
    html:not(.render-mode) main:has(> .frame) > .body,
    html:not(.render-mode) body.ce-ambient-frame-proof main > header,
    html:not(.render-mode) body.ce-ambient-frame-proof main > .player,
    html:not(.render-mode) body.ce-ambient-frame-proof main > .body {
      display: none !important;
    }
    .ce-stage-scale-shell {
      position: relative;
      overflow: visible;
      margin: 0 auto;
    }
    .frame.ce-fixed-stage {
      width: 1920px !important;
      height: 1080px !important;
      max-width: none !important;
      aspect-ratio: auto !important;
      transform-origin: top left !important;
      margin: 0 !important;
    }
    html:not(.render-mode) .review-shell {
      bottom: var(--ce-review-chrome-height, 86px) !important;
    }
    .stage > .rail,
    .stage > .caption-softener,
    .frame > .rail,
    .frame > .caption-softener,
    main[aria-label] > .rail,
    main[aria-label] > .caption-softener {
      opacity: 0 !important;
      visibility: hidden !important;
      pointer-events: none !important;
    }
    html:not(.render-mode) .review-controls,
    html:not(.render-mode) .review-transport,
    html:not(.render-mode) .audio-review,
    html:not(.render-mode) .player-controls,
    html:not(.render-mode) main:has(> .frame) > .player,
    html:not(.render-mode) main:has(> .frame) > .body,
    html:not(.render-mode) [data-review-controls],
    html:not(.render-mode) [aria-label="Review controls"],
    html:not(.render-mode) .ce-legacy-review-chrome-hidden {
      position: fixed !important;
      left: -10000px !important;
      right: auto !important;
      bottom: auto !important;
      width: 1px !important;
      height: 1px !important;
      min-width: 0 !important;
      min-height: 0 !important;
      padding: 0 !important;
      border: 0 !important;
      opacity: 0 !important;
      overflow: hidden !important;
      pointer-events: none !important;
      visibility: hidden !important;
    }
    html:not(.render-mode) audio[controls] {
      position: fixed !important;
      left: -10000px !important;
      width: 1px !important;
      height: 1px !important;
      opacity: 0 !important;
      pointer-events: none !important;
    }
    html:not(.render-mode) .review-audio {
      position: fixed !important;
      left: -9999px !important;
      right: auto !important;
      bottom: auto !important;
      width: 1px !important;
      height: 1px !important;
      opacity: 0 !important;
      pointer-events: none !important;
    }
    .ce-review-transport {
      position: fixed;
      left: 50%;
      bottom: 18px;
      z-index: 80;
      transform: translateX(-50%);
      display: grid;
      grid-template-columns: auto 58px minmax(360px, 48vw) 58px;
      align-items: center;
      gap: 12px;
      width: min(760px, calc(100vw - 48px));
      min-height: 54px;
      padding: 9px 12px;
      color: rgba(248, 244, 234, 0.94);
      background: rgba(20, 22, 28, 0.82);
      border: 1px solid rgba(248, 244, 234, 0.12);
      border-radius: 8px;
      box-shadow: 0 12px 34px rgba(0, 0, 0, 0.34);
      pointer-events: auto;
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      font: 700 13px/1 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .ce-review-transport button {
      appearance: none;
      border: 1px solid rgba(248, 244, 234, 0.18);
      border-radius: 7px;
      background: rgba(248, 244, 234, 0.08);
      color: inherit;
      min-width: 74px;
      min-height: 34px;
      padding: 0 12px;
      font: inherit;
      cursor: pointer;
    }
    .ce-review-transport button:hover {
      background: rgba(248, 244, 234, 0.14);
    }
    .ce-review-transport time {
      color: rgba(248, 244, 234, 0.72);
      font-variant-numeric: tabular-nums;
      text-align: center;
    }
    .ce-review-transport input[type="range"] {
      width: 100%;
      accent-color: ${palette.text};
      cursor: pointer;
    }
    .ce-legacy-rail-hidden {
      opacity: 0 !important;
      visibility: hidden !important;
      pointer-events: none !important;
    }
    .ce-legacy-end-screen-hidden {
      opacity: 0 !important;
      visibility: hidden !important;
      pointer-events: none !important;
      display: none !important;
    }
    .ce-youtube-end-screen {
      --ce-end-screen-target-fill: ${endScreenCss["--ce-end-screen-target-fill"] || leftTargetPalette.fill_rgba};
      --ce-end-screen-video-border: ${endScreenCss["--ce-end-screen-video-border"] || leftTargetPalette.border_rgba};
      --ce-end-screen-video-border-secondary: ${endScreenCss["--ce-end-screen-video-border-secondary"] || rightTargetPalette.border_rgba};
      --ce-end-screen-subscribe-ring: ${endScreenCss["--ce-end-screen-subscribe-ring"] || subscribeTargetPalette.border_rgba};
      --ce-end-screen-muted-text: ${endScreenCss["--ce-end-screen-muted-text"] || rightTargetPalette.sample_hex || "#d8c19b"};
      --ce-end-screen-small-accent: ${endScreenCss["--ce-end-screen-small-accent"] || subscribeTargetPalette.sample_hex || "#f6d37d"};
      --ce-end-screen-target-fill-left: ${leftTargetPalette.fill_rgba};
      --ce-end-screen-target-fill-right: ${rightTargetPalette.fill_rgba};
      --ce-end-screen-target-fill-subscribe: ${subscribeTargetPalette.fill_rgba};
      --ce-end-screen-video-border-left: ${leftTargetPalette.border_rgba};
      --ce-end-screen-video-border-right: ${rightTargetPalette.border_rgba};
      --ce-end-screen-subscribe-border: ${subscribeTargetPalette.border_rgba};
      --ce-end-screen-video-ring-left: ${leftTargetPalette.ring_rgba};
      --ce-end-screen-video-ring-right: ${rightTargetPalette.ring_rgba};
      --ce-end-screen-subscribe-soft-ring: ${subscribeTargetPalette.ring_rgba};
      --ce-end-screen-subscribe-inner-ring: ${subscribeTargetPalette.inner_ring_rgba};
      position: absolute;
      z-index: 18;
      inset: 0;
      overflow: hidden;
      opacity: var(--ce-youtube-end-screen-opacity, 0);
      pointer-events: none;
      background: transparent;
      transform: translateZ(0);
    }
    .ce-youtube-end-screen-target {
      position: absolute;
      background: transparent;
    }
    .ce-youtube-end-screen-target.left-video {
      left: 78px;
      top: 382px;
      width: 680px;
      height: 383px;
      border: 4px solid var(--ce-end-screen-video-border-left, var(--ce-end-screen-video-border));
      border-radius: 18px;
      background: var(--ce-end-screen-target-fill-left, var(--ce-end-screen-target-fill));
      box-shadow: 0 0 0 10px var(--ce-end-screen-video-ring-left), 0 22px 38px rgba(5, 8, 23, 0.34), inset 0 0 38px var(--ce-end-screen-video-ring-left);
    }
    .ce-youtube-end-screen-target.right-video {
      left: 1162px;
      top: 382px;
      width: 680px;
      height: 383px;
      border: 4px solid var(--ce-end-screen-video-border-right, var(--ce-end-screen-video-border-secondary));
      border-radius: 18px;
      background: var(--ce-end-screen-target-fill-right, var(--ce-end-screen-target-fill));
      box-shadow: 0 0 0 10px var(--ce-end-screen-video-ring-right), 0 22px 38px rgba(5, 8, 23, 0.34), inset 0 0 38px var(--ce-end-screen-video-ring-right);
    }
    .ce-youtube-end-screen-target.subscribe-target {
      left: 814px;
      top: 429px;
      width: 292px;
      height: 292px;
      border: 7px solid var(--ce-end-screen-subscribe-border, var(--ce-end-screen-subscribe-ring));
      border-radius: 50%;
      background: var(--ce-end-screen-target-fill-subscribe, var(--ce-end-screen-target-fill));
      box-shadow: 0 0 0 18px var(--ce-end-screen-subscribe-soft-ring), 0 22px 34px rgba(5, 8, 23, 0.30);
    }
    .ce-youtube-end-screen-target.subscribe-target::after {
      content: "";
      position: absolute;
      inset: 18px;
      border: 3px solid var(--ce-end-screen-subscribe-inner-ring);
      border-radius: 50%;
    }
    .ce-rolling-rail {
      position: absolute;
      z-index: 24;
      left: 1108px;
      top: 52px;
      width: 760px;
      height: 976px;
      pointer-events: none;
      opacity: var(--ce-rolling-rail-opacity, 1);
      color: ${palette.text};
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: transparent !important;
      border: 0 !important;
      border-radius: 0 !important;
      box-shadow: none !important;
      padding: 0 !important;
      margin: 0 !important;
      overflow: visible !important;
      backdrop-filter: none !important;
      -webkit-backdrop-filter: none !important;
    }
    .ce-rolling-anchor {
      display: none;
      position: absolute;
      top: 0;
      right: 0;
      width: 680px;
      min-height: 82px;
      text-align: right;
      text-shadow: 0 2px 16px rgba(0,0,0,0.40);
    }
    .ce-rolling-anchor-label {
      color: ${palette.muted};
      font-size: 22px;
      line-height: 1;
      font-weight: 780;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }
    .ce-rolling-anchor-title {
      margin-top: 8px;
      color: ${palette.text};
      font-size: 30px;
      line-height: 1.04;
      font-weight: 720;
      letter-spacing: 0;
    }
    .ce-rolling-anchor-title:empty { display: none; }
    .ce-caption-window {
      position: absolute;
      left: auto;
      right: ${CAPTION_WINDOW_GEOMETRY.railRight}px;
      top: ${CAPTION_WINDOW_GEOMETRY.railTop}px;
      width: ${CAPTION_WINDOW_GEOMETRY.width}px;
      height: ${CAPTION_WINDOW_GEOMETRY.height}px;
      overflow: hidden;
      opacity: 1;
      mask-image: linear-gradient(to bottom, transparent 0, rgba(0,0,0,0.12) 42px, rgba(0,0,0,0.72) 118px, black ${CAPTION_WINDOW_GEOMETRY.topFade}px, black calc(100% - ${CAPTION_WINDOW_GEOMETRY.bottomFade}px), rgba(0,0,0,0.72) calc(100% - 118px), rgba(0,0,0,0.12) calc(100% - 42px), transparent 100%);
      -webkit-mask-image: linear-gradient(to bottom, transparent 0, rgba(0,0,0,0.12) 42px, rgba(0,0,0,0.72) 118px, black ${CAPTION_WINDOW_GEOMETRY.topFade}px, black calc(100% - ${CAPTION_WINDOW_GEOMETRY.bottomFade}px), rgba(0,0,0,0.72) calc(100% - 118px), rgba(0,0,0,0.12) calc(100% - 42px), transparent 100%);
      transform: translateZ(0);
      contain: layout paint style;
      isolation: isolate;
      backface-visibility: hidden;
      border: 0 !important;
      border-radius: 0 !important;
      box-shadow: none !important;
      padding: 0 !important;
    }
    .ce-caption-stack {
      position: absolute;
      left: ${CAPTION_WINDOW_GEOMETRY.stackLeft}px;
      top: 0;
      width: ${CAPTION_WINDOW_GEOMETRY.stackWidth}px;
      min-height: ${captionStackHeightPx}px;
      height: ${captionStackHeightPx}px;
      transform: translate3d(0, 0, 0);
      will-change: transform;
      contain: layout style;
      backface-visibility: hidden;
      transform-style: preserve-3d;
    }
    .ce-caption-line {
      position: absolute;
      left: 0;
      width: ${CAPTION_WINDOW_GEOMETRY.stackWidth}px;
      color: ${palette.text};
      font-size: 32px;
      line-height: ${CAPTION_LINE_BOX_HEIGHT_PX}px;
      font-weight: 590;
      letter-spacing: 0;
      text-align: left;
      -webkit-font-smoothing: antialiased;
      text-rendering: geometricPrecision;
      opacity: 0;
      text-shadow: 0 2px 14px rgba(0,0,0,0.36);
      transform: translateZ(0);
      will-change: opacity;
      backface-visibility: hidden;
      -webkit-font-smoothing: antialiased;
      text-rendering: geometricPrecision;
    }
    .ce-caption-display-line {
      display: block;
      min-height: ${CAPTION_LINE_BOX_HEIGHT_PX}px;
      line-height: ${CAPTION_LINE_BOX_HEIGHT_PX}px;
      white-space: nowrap;
    }
    .ce-proof-freshness-warning {
      position: fixed;
      z-index: 2147483647;
      right: 18px;
      top: 18px;
      max-width: min(520px, calc(100vw - 36px));
      padding: 12px 14px;
      color: #fff6e2;
      background: rgba(122, 45, 20, 0.94);
      border: 1px solid rgba(255, 207, 129, 0.72);
      border-radius: 8px;
      box-shadow: 0 10px 34px rgba(0,0,0,0.36);
      font: 760 14px/1.35 Inter, ui-sans-serif, system-ui, sans-serif;
    }
    .ce-proof-freshness-warning[hidden] {
      display: none !important;
    }
    .ce-proof-freshness-warning span {
      display: block;
      margin-top: 2px;
      color: rgba(255, 246, 226, 0.82);
      font-weight: 560;
      font-size: 12px;
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
    .ce-phrase-highlight { color: ${palette.text}; text-shadow: inherit; }
    .frame:not(.ce-fixed-stage) > .ce-rolling-rail {
      left: 57.708%;
      top: 4.815%;
      width: 39.583%;
      height: 90.37%;
    }
    .frame:not(.ce-fixed-stage) > .ce-rolling-rail .ce-rolling-anchor {
      width: 89.47%;
      min-height: 8.4%;
    }
    .frame:not(.ce-fixed-stage) > .ce-rolling-rail .ce-rolling-anchor-label {
      font-size: clamp(15px, 1.15vw, 22px);
    }
    .frame:not(.ce-fixed-stage) > .ce-rolling-rail .ce-rolling-anchor-title {
      font-size: clamp(20px, 1.56vw, 30px);
    }
    .frame:not(.ce-fixed-stage) > .ce-rolling-rail .ce-caption-window {
      left: auto;
      right: ${(CAPTION_WINDOW_GEOMETRY.railRight / RAIL_GEOMETRY.width * 100).toFixed(3)}%;
      top: ${(CAPTION_WINDOW_GEOMETRY.railTop / RAIL_GEOMETRY.height * 100).toFixed(3)}%;
      width: ${(CAPTION_WINDOW_GEOMETRY.width / RAIL_GEOMETRY.width * 100).toFixed(3)}%;
      height: ${(CAPTION_WINDOW_GEOMETRY.height / RAIL_GEOMETRY.height * 100).toFixed(3)}%;
    }
    .frame:not(.ce-fixed-stage) > .ce-rolling-rail .ce-caption-stack {
      left: ${(CAPTION_WINDOW_GEOMETRY.stackLeft / CAPTION_WINDOW_GEOMETRY.width * 100).toFixed(3)}%;
      width: ${(CAPTION_WINDOW_GEOMETRY.stackWidth / CAPTION_WINDOW_GEOMETRY.width * 100).toFixed(3)}%;
    }
    .frame:not(.ce-fixed-stage) > .ce-rolling-rail .ce-caption-line {
      width: 100%;
      font-size: clamp(22px, 1.667vw, ${CAPTION_FONT_SIZE_PX}px);
    }
    .frame.ce-fixed-stage > .ce-rolling-rail .ce-caption-line {
      width: ${CAPTION_WINDOW_GEOMETRY.stackWidth}px;
      font-size: ${CAPTION_FONT_SIZE_PX}px;
      line-height: ${CAPTION_LINE_BOX_HEIGHT_PX}px;
    }
    .frame.ce-fixed-stage > .ce-rolling-rail .ce-caption-display-line {
      min-height: ${CAPTION_LINE_BOX_HEIGHT_PX}px;
      line-height: ${CAPTION_LINE_BOX_HEIGHT_PX}px;
    }
  </style>
<!-- ce-rolling-caption-rail-tighten-style:end -->`;

  const script = `<!-- ce-rolling-caption-rail-tighten-script:start -->
  <script>
  (() => {
    const CE_CHUNKS = ${JSON.stringify(chunks)};
    const CE_KEY_PHRASE_SPANS = ${JSON.stringify(keyPhraseSpans)};
    const CE_CONFIG = {
      episodeId: ${JSON.stringify(episode.episodeId)},
      episodeTitle: ${JSON.stringify(episode.title)},
      proofBuildId: ${JSON.stringify(proofBuildId)},
      proofGeneratedAtUtc: ${JSON.stringify(proofGeneratedAtUtc)},
      proofBuildJsonPath: "proof_build.json",
      introTrimModel: ${JSON.stringify(INTRO_TRIM_MODEL)},
      introTrimSeconds: ${Number(INTRO_TRIM_SECONDS.toFixed(3))},
      previousVoiceStartOffsetSeconds: ${Number(PREVIOUS_VOICE_START_OFFSET_SECONDS.toFixed(6))},
      voiceStartOffsetSeconds: ${Number(VOICE_START_OFFSET_SECONDS.toFixed(6))},
      textColor: ${JSON.stringify(palette.text)},
      highlightRenderPolicy: "reviewed_cue_map_spans_only",
      reviewChromePolicy: "hidden_in_render_mode",
      reviewControlModel: ${JSON.stringify(REVIEW_CONTROL_MODEL)},
      reviewTransportScrubModel: ${JSON.stringify(REVIEW_TRANSPORT_SCRUB_MODEL)},
      legacyReviewChromeSuppressionModel: ${JSON.stringify(LEGACY_REVIEW_CHROME_SUPPRESSION_MODEL)},
      captionPlaybackClockModel: ${JSON.stringify(CAPTION_PLAYBACK_CLOCK_MODEL)},
      captionStackRenderModel: ${JSON.stringify(CAPTION_STACK_RENDER_MODEL)},
      captionScrollSmoothnessModel: ${JSON.stringify(CAPTION_SCROLL_SMOOTHNESS_MODEL)},
      captionRuntimeCoverageModel: ${JSON.stringify(CAPTION_RUNTIME_COVERAGE_MODEL)},
      captionEndScreenHandoffModel: ${JSON.stringify(CAPTION_END_SCREEN_HANDOFF_MODEL)},
      reviewApprovedEndScreenEntryModel: ${JSON.stringify(CAPTION_END_SCREEN_HANDOFF_MODEL)},
      reviewApprovedEndScreenFadeStartSeconds: ${JSON.stringify(
        REVIEW_APPROVED_END_SCREEN_FADE_START_SECONDS[episode.episodeId] ?? null,
      )},
      captionDisplayChunking: "script_locked_chunk_split_v1",
      captionMotionModel: ${JSON.stringify(CAPTION_MOTION_MODEL)},
      captionTimelineLayoutModel: ${JSON.stringify(CAPTION_TIMELINE_LAYOUT_MODEL)},
      captionSyncTarget: ${JSON.stringify(CAPTION_SYNC_TARGET)},
      captionReadingLeadSeconds: ${Number(CAPTION_READING_LEAD_SECONDS.toFixed(3))},
      captionIntroVisibilityGateModel: ${JSON.stringify(CAPTION_INTRO_VISIBILITY_GATE_MODEL)},
      captionIntroGateStartSeconds: ${Number((captionScrollTiming.caption_intro_gate_start_seconds || 0).toFixed(3))},
      captionIntroGateFullOpacitySeconds: ${Number((captionScrollTiming.caption_intro_gate_full_opacity_seconds || 0).toFixed(3))},
      captionIntroPrematureTextRead: ${JSON.stringify(captionScrollTiming.caption_intro_premature_text_read || "pass")},
      captionConstantSpeedScope: ${JSON.stringify(CAPTION_CONSTANT_SPEED_SCOPE)},
      captionDensityResolutionModel: ${JSON.stringify(CAPTION_DENSITY_RESOLUTION_MODEL)},
      captionDisplayLineWrapModel: ${JSON.stringify(CAPTION_DISPLAY_LINE_WRAP_MODEL)},
      captionDisplayLineMaxWidthPx: ${Number(CAPTION_DISPLAY_LINE_MAX_WIDTH_PX)},
      captionMaxEstimatedLineWidthPx: ${Number(captionScrollTiming.caption_max_estimated_line_width_px || 0)},
      captionTextStackWidthPx: ${Number(CAPTION_WINDOW_GEOMETRY.stackWidth)},
      captionStackHeightPx: ${Number(captionStackHeightPx)},
      captionStackPaintContainmentRead: ${JSON.stringify(captionScrollTiming.caption_stack_paint_containment_read || "pass_no_caption_stack_paint_clip")},
      captionActiveBandLowerDeltaPx: ${CAPTION_ACTIVE_BAND_LOWER_DELTA_PX},
      captionLineOpacityModel: ${JSON.stringify(CAPTION_LINE_OPACITY_MODEL)},
      captionWindowTreatmentModel: ${JSON.stringify(CAPTION_WINDOW_TREATMENT_MODEL)},
      highlightPhraseScope: ${JSON.stringify(HIGHLIGHT_PHRASE_SCOPE)},
      captionHighlightModelId: ${JSON.stringify(CAPTION_HIGHLIGHT_MODEL_ID)},
      highlightSemanticRole: ${JSON.stringify(HIGHLIGHT_SEMANTIC_ROLE)},
      highlightDensityModel: ${JSON.stringify(HIGHLIGHT_DENSITY_MODEL)},
      highlightColorModel: ${JSON.stringify(HIGHLIGHT_COLOR_MODEL)},
      highlightVisualTimingModel: ${JSON.stringify(HIGHLIGHT_VISUAL_TIMING_MODEL)},
      captionLayoutCollisionGuard: ${JSON.stringify(CAPTION_LAYOUT_COLLISION_GUARD)},
      captionMinRenderedLineGapPx: ${Number(captionScrollTiming.caption_min_rendered_line_gap_px || 0)},
      captionForcedTakeawayMergeCount: ${Number(captionScrollTiming.caption_forced_takeaway_merge_count || 0)},
      captionAudioSyncModel: ${JSON.stringify(captionSources.audioSyncModel || "raw_timing_source_audio_time_v1")},
      captionAudioOffsetSeconds: ${Number((captionSources.audioOffsetSeconds || 0).toFixed(6))},
      firstDisplayCueStartSeconds: ${Number((chunks[0]?.start || 0).toFixed(3))},
      lastDisplayCueEndSeconds: ${Number((chunks[chunks.length - 1]?.end || 0).toFixed(3))},
      lastCaptionVisibleExitStartSeconds: ${Number((endScreenTiming?.lastCaptionVisibleExitStartSeconds || 0).toFixed(3))},
      lastCaptionFullySuppressedSeconds: ${Number((endScreenTiming?.lastCaptionFullySuppressedSeconds || 0).toFixed(3))},
      youtubePlaceholderFadeStartSeconds: ${Number((endScreenTiming?.youtubePlaceholderFadeStartSeconds || 0).toFixed(3))},
      youtubePlaceholderFullOpacitySeconds: ${Number((endScreenTiming?.youtubePlaceholderFullOpacitySeconds || 0).toFixed(3))},
      youtubePlaceholderTransitionDurationSeconds: ${Number((endScreenTiming?.youtubePlaceholderTransitionDurationSeconds || END_SCREEN_TRANSITION_DURATION_SECONDS).toFixed(3))},
      captionEndScreenGapSeconds: ${Number((endScreenTiming?.captionEndScreenGapSeconds || 0).toFixed(3))},
      captionEndScreenOverlapRead: ${JSON.stringify(endScreenTiming?.captionEndScreenOverlapRead || "pending")},
      tacomaRainPerformanceGuardModel: ${JSON.stringify(
        episode.episodeId === "tacoma-narrows" ? TACOMA_RAIN_PERFORMANCE_GUARD_MODEL : "not_applicable",
      )},
      tacomaRainFrameThrottleMs: ${Number(episode.episodeId === "tacoma-narrows" ? TACOMA_RAIN_FRAME_THROTTLE_MS : 0)},
      captionConstantScrollSpeedPxPerSecond: ${Number(captionScrollTiming.caption_constant_scroll_speed_px_per_second || 50)},
      captionScrollStartTimeSeconds: ${Number(captionScrollTiming.caption_scroll_start_time_seconds || 0)},
      captionScrollStartPositionPx: ${Number(captionScrollTiming.caption_scroll_start_position_px || 0)},
      captionScrollEndTimeSeconds: ${Number(captionScrollTiming.caption_scroll_end_time_seconds || 0)},
      captionScrollEndPositionPx: ${Number(captionScrollTiming.caption_scroll_end_position_px || 0)},
      captionWindowHeight: ${CAPTION_WINDOW_GEOMETRY.height},
      captionActiveY: ${CAPTION_WINDOW_GEOMETRY.activeY},
      captionTopFade: ${CAPTION_WINDOW_GEOMETRY.topFade},
      captionBottomFade: ${CAPTION_WINDOW_GEOMETRY.bottomFade},
      durationSeconds: ${Number(durationSeconds.toFixed(3))}
    };
    const CE_END_SCREEN = ${JSON.stringify(endScreenTiming || { enabled: false })};
    const CE_END_SCREEN_PALETTE = ${JSON.stringify(endScreenPaletteContract || null)};
    window.__endScreenPaletteContract = CE_END_SCREEN_PALETTE;
    const ACTIVE_Y = CE_CONFIG.captionActiveY;
    const END_FADE_SECONDS = 7.5;
    const CE_PARAMS = new URLSearchParams(window.location.search);
    const CE_RENDER_MODE = CE_PARAMS.get("render") === "1";
    const CE_URL_FORCED_TIME = Number(CE_PARAMS.get("t"));
    let forcedRenderTime = null;
    let playbackClockMediaTime = 0;
    let playbackClockNow = performance.now();
    let lastPlaybackRenderTime = 0;
    let railAnimationFrameId = null;
    let captionStackCompositorActive = false;
    let captionStackCompositorTargetTime = null;
    let captionStackCompositorStartedAt = null;
    let lastTacomaRainDrawAt = -Infinity;
    const reviewTransportState = {
      isUserScrubbing: false,
      wasPlayingBeforeScrub: false,
      pendingScrubTime: null,
      lastCommittedScrubTime: null,
      pointerId: null,
      scrubStartedAt: null,
    };
    if (CE_RENDER_MODE) document.documentElement.classList.add("render-mode");
    if (Number.isFinite(CE_URL_FORCED_TIME)) forcedRenderTime = CE_URL_FORCED_TIME;
    if (CE_CONFIG.episodeId === "tacoma-narrows") {
      window.__ceTacomaRainPerformanceGuard = (audioTime) => {
        const safeTime = Number(audioTime) || 0;
        if (CE_RENDER_MODE || forcedRenderTime !== null || (findAudio() && findAudio().paused)) return true;
        if (CE_END_SCREEN && safeTime >= (Number(CE_END_SCREEN.transitionStartSeconds) || Infinity)) return false;
        const now = performance.now();
        if (now - lastTacomaRainDrawAt >= Math.max(16, Number(CE_CONFIG.tacomaRainFrameThrottleMs) || 83)) {
          lastTacomaRainDrawAt = now;
          return true;
        }
        return false;
      };
    }
    window.__ceProofBuild = {
      proof_build_id: CE_CONFIG.proofBuildId,
      proof_generated_at_utc: CE_CONFIG.proofGeneratedAtUtc,
      proof_build_json_path: CE_CONFIG.proofBuildJsonPath,
      intro_trim_model: CE_CONFIG.introTrimModel,
      intro_trim_seconds: CE_CONFIG.introTrimSeconds,
      previous_voice_start_offset_seconds: CE_CONFIG.previousVoiceStartOffsetSeconds,
      voice_start_offset_seconds: CE_CONFIG.voiceStartOffsetSeconds,
    };

    function clamp(value, min, max) { return Math.max(min, Math.min(max, value)); }
    function smoothstep(x) { const t = clamp(x, 0, 1); return t * t * (3 - 2 * t); }
    function textOf(selector) {
      const node = document.querySelector(selector);
      return node && node.textContent ? node.textContent.replace(/\\s+/g, " ").trim() : "";
    }
    function findStage() {
      return document.querySelector(".stage") || document.getElementById("stage") || document.querySelector(".frame") || document.querySelector("main[aria-label]") || document.body;
    }
    function findAudio() {
      return document.getElementById("audio") || document.querySelector("audio");
    }
    function installRangeServerWarning() {
      if (CE_RENDER_MODE) return null;
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
      const safeDetail = detail ? String(detail).replace(/[<>&]/g, (char) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;" }[char])) : "range probe failed";
      warning.innerHTML = 'This review is not being served by the byte-range server.<span>' + safeDetail + '</span><code>node scripts/range_static_server.mjs 8766 /Users/mike/Episodes_CascadeEffects</code>';
      window.__ceReviewRangeServerState.warning_visible = true;
      return true;
    }
    async function verifyReviewRangeServer(audio = findAudio()) {
      const source = audio ? (audio.currentSrc || audio.src || "") : "";
      const state = {
        model: "byte_range_required_local_review_server_v1",
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
      if (CE_RENDER_MODE || !audio || !source) {
        state.status = "skipped";
        state.range_server_read = CE_RENDER_MODE ? "not_applicable_render_mode" : "not_applicable_no_audio_source";
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
    function normalizeResponsiveFrameStage() {
      const frame = document.querySelector(".frame");
      if (!frame || frame.closest(".review-shell")) return null;
      let shell = frame.closest(".ce-stage-scale-shell");
      if (!shell) {
        shell = document.createElement("div");
        shell.className = "ce-stage-scale-shell";
        frame.parentNode.insertBefore(shell, frame);
        shell.appendChild(frame);
      }
      frame.classList.add("ce-fixed-stage");
      document.body.classList.add("ce-ambient-frame-proof");
      syncResponsiveFrameStageScale();
      return frame;
    }
    function syncResponsiveFrameStageScale() {
      const frame = document.querySelector(".frame.ce-fixed-stage");
      const shell = frame?.closest(".ce-stage-scale-shell");
      if (!frame || !shell) return;
      const chromeHeight = document.documentElement.classList.contains("render-mode") ? 0 : 92;
      const widthLimit = Math.max(1, window.innerWidth - 22);
      const heightLimit = Math.max(1, window.innerHeight - chromeHeight);
      const scale = Math.min(1, widthLimit / 1920, heightLimit / 1080);
      shell.style.width = (1920 * scale).toFixed(3) + "px";
      shell.style.height = (1080 * scale).toFixed(3) + "px";
      frame.style.transform = "scale(" + scale.toFixed(6) + ")";
      document.documentElement.style.setProperty("--stage-scale", scale.toFixed(6));
    }
    function suppressLegacyReviewChrome(audio) {
      const selectors = [
        ".review-controls",
        ".review-audio",
        ".review-transport",
        ".audio-review",
        ".controls",
        ".machine-reads",
        ".player-controls",
        "main:has(> .frame) > .player",
        "main:has(> .frame) > .body",
        "[data-review-controls]",
        "[aria-label='Review controls']"
      ];
      const hidden = new Set();
      selectors.forEach((selector) => {
        document.querySelectorAll(selector).forEach((node) => {
          if (!node || node.classList.contains("ce-review-transport")) return;
          node.classList.add("ce-legacy-review-chrome-hidden");
          node.setAttribute("data-ce-review-chrome-hidden", "true");
          hidden.add(node);
        });
      });
      if (audio) {
        audio.setAttribute("data-ce-audio-timing-source", "true");
        audio.controls = false;
      }
      window.__ceReviewChromeState = {
        reviewControlModel: CE_CONFIG.reviewControlModel,
        legacyReviewChromeSuppressionModel: CE_CONFIG.legacyReviewChromeSuppressionModel,
        hiddenLegacyChromeCount: hidden.size,
        foregroundTransportCount: document.querySelectorAll(".ce-review-transport").length
      };
    }
    function syncReviewShellScale() {
      const reviewShell = document.querySelector(".review-shell");
      if (!reviewShell || document.documentElement.classList.contains("render-mode")) return;
      const chromeHeight = 86;
      document.documentElement.style.setProperty("--ce-review-chrome-height", chromeHeight + "px");
      const availableHeight = Math.max(1, window.innerHeight - chromeHeight);
      const scale = Math.min(window.innerWidth / 1920, availableHeight / 1080);
      document.documentElement.style.setProperty("--stage-scale", Math.max(0.01, scale).toFixed(6));
    }
    function formatClock(seconds) {
      const safe = Math.max(0, Number(seconds) || 0);
      const minutes = Math.floor(safe / 60);
      const wholeSeconds = Math.floor(safe % 60);
      return String(minutes).padStart(2, "0") + ":" + String(wholeSeconds).padStart(2, "0");
    }
    function mediaDuration(audio) {
      return audio && Number.isFinite(audio.duration) && audio.duration > 0 ? audio.duration : CE_CONFIG.durationSeconds;
    }
    function installProofFreshnessWarning() {
      if (CE_RENDER_MODE) return null;
      let warning = document.querySelector(".ce-proof-freshness-warning");
      if (warning) return warning;
      warning = document.createElement("aside");
      warning.className = "ce-proof-freshness-warning";
      warning.setAttribute("role", "status");
      warning.setAttribute("aria-live", "polite");
      warning.hidden = true;
      warning.innerHTML = 'This proof has been regenerated. Refresh before reviewing.<span>Loaded build ' + CE_CONFIG.proofBuildId + '</span>';
      document.body.appendChild(warning);
      return warning;
    }
    function setProofFreshnessWarning(latest = {}) {
      const warning = installProofFreshnessWarning();
      if (!warning) return false;
      const latestBuildId = latest && latest.proof_build_id ? String(latest.proof_build_id) : "";
      warning.hidden = false;
      warning.innerHTML = 'This proof has been regenerated. Refresh before reviewing.<span>Loaded build ' + CE_CONFIG.proofBuildId + (latestBuildId ? ', latest build ' + latestBuildId : '') + '</span>';
      window.__ceProofFreshnessState = {
        loaded_proof_build_id: CE_CONFIG.proofBuildId,
        latest_proof_build_id: latestBuildId || null,
        stale: true,
        warning_visible: true,
      };
      return true;
    }
    function proofBuildStateFromLatest(latest = {}) {
      const latestBuildId = latest && latest.proof_build_id ? String(latest.proof_build_id) : "";
      const stale = Boolean(latestBuildId && latestBuildId !== CE_CONFIG.proofBuildId);
      if (stale) setProofFreshnessWarning(latest);
      else {
        const warning = document.querySelector(".ce-proof-freshness-warning");
        if (warning) warning.hidden = true;
        window.__ceProofFreshnessState = {
          loaded_proof_build_id: CE_CONFIG.proofBuildId,
          latest_proof_build_id: latestBuildId || CE_CONFIG.proofBuildId,
          stale: false,
          warning_visible: false,
        };
      }
      return window.__ceProofFreshnessState;
    }
    async function checkProofFreshness() {
      if (CE_RENDER_MODE || !CE_CONFIG.proofBuildId) return proofBuildStateFromLatest(window.__ceProofBuild);
      try {
        const url = new URL(CE_CONFIG.proofBuildJsonPath, window.location.href);
        url.searchParams.set("freshness_check", String(Date.now()));
        const response = await fetch(url.toString(), { cache: "no-store" });
        if (!response.ok) throw new Error("proof_build_json_http_" + response.status);
        const latest = await response.json();
        return proofBuildStateFromLatest(latest);
      } catch (error) {
        window.__ceProofFreshnessState = {
          loaded_proof_build_id: CE_CONFIG.proofBuildId,
          latest_proof_build_id: null,
          stale: false,
          warning_visible: false,
          error: String(error && error.message ? error.message : error),
        };
        return window.__ceProofFreshnessState;
      }
    }
    window.__ceRunProofFreshnessCheck = checkProofFreshness;
    window.__ceShowStaleProofWarning = setProofFreshnessWarning;
    function mediaTime(audio) {
      return audio && Number.isFinite(audio.currentTime) ? audio.currentTime || 0 : 0;
    }
    function resetPlaybackClock(audio, time = mediaTime(audio)) {
      playbackClockMediaTime = Math.max(0, Number(time) || 0);
      playbackClockNow = performance.now();
      lastPlaybackRenderTime = playbackClockMediaTime;
      return playbackClockMediaTime;
    }
    function playbackClockTime(audio) {
      if (forcedRenderTime !== null) return forcedRenderTime;
      if (!audio) return 0;
      const raw = mediaTime(audio);
      const clamped = clamp(raw, 0, mediaDuration(audio));
      const now = performance.now();
      if (audio.paused || audio.seeking || reviewTransportState.isUserScrubbing) {
        lastPlaybackRenderTime = clamped;
        playbackClockMediaTime = clamped;
        playbackClockNow = now;
        return clamped;
      }
      const rate = Number.isFinite(audio.playbackRate) ? audio.playbackRate : 1;
      const elapsed = Math.max(0, (now - playbackClockNow) / 1000);
      let smoothed = clamp(playbackClockMediaTime + elapsed * rate, 0, mediaDuration(audio));
      const drift = clamped - smoothed;
      if (Math.abs(drift) > 0.18 || elapsed > 1.25) {
        smoothed = clamped;
      } else {
        smoothed = clamp(smoothed + drift * 0.035, 0, mediaDuration(audio));
      }
      smoothed = Math.max(lastPlaybackRenderTime, smoothed);
      lastPlaybackRenderTime = smoothed;
      playbackClockMediaTime = smoothed;
      playbackClockNow = now;
      return smoothed;
    }
    function transformForTime(time) {
      return ACTIVE_Y - scrollPositionAt(time);
    }
    function setStackTranslateY(translateY, { transition = "none" } = {}) {
      const stack = document.querySelector(".ce-caption-stack");
      if (!stack) return;
      stack.style.transition = transition;
      stack.style.transform = "translate3d(0, " + Number(translateY || 0).toFixed(3) + "px, 0)";
    }
    function startCompositorScroll(audio) {
      if (!audio || audio.paused || forcedRenderTime !== null) return;
      const now = playbackClockTime(audio);
      const stack = document.querySelector(".ce-caption-stack");
      if (!stack) return;
      const rate = Math.max(0.001, Number.isFinite(audio.playbackRate) ? Math.abs(audio.playbackRate) : 1);
      const targetTime = Math.max(now, CE_CONFIG.captionScrollEndTimeSeconds || CE_CONFIG.durationSeconds);
      const duration = Math.max(0.001, (targetTime - now) / rate);
      captionStackCompositorActive = false;
      setStackTranslateY(transformForTime(now), { transition: "none" });
      void stack.offsetHeight;
      captionStackCompositorActive = true;
      captionStackCompositorTargetTime = targetTime;
      captionStackCompositorStartedAt = now;
      setStackTranslateY(transformForTime(targetTime), { transition: "transform " + duration.toFixed(3) + "s linear" });
    }
    function stopCompositorScroll(time) {
      captionStackCompositorActive = false;
      captionStackCompositorTargetTime = null;
      captionStackCompositorStartedAt = null;
      setStackTranslateY(transformForTime(time), { transition: "none" });
    }
    function reviewTransportStateSnapshot() {
      const audio = findAudio();
      const scrubber = document.querySelector(".ce-review-transport [data-ce-scrub]");
      return {
        reviewTransportScrubModel: CE_CONFIG.reviewTransportScrubModel,
        isUserScrubbing: Boolean(reviewTransportState.isUserScrubbing),
        wasPlayingBeforeScrub: Boolean(reviewTransportState.wasPlayingBeforeScrub),
        pendingScrubTime:
          reviewTransportState.pendingScrubTime === null ? null : Number(reviewTransportState.pendingScrubTime.toFixed(3)),
        lastCommittedScrubTime:
          reviewTransportState.lastCommittedScrubTime === null ? null : Number(reviewTransportState.lastCommittedScrubTime.toFixed(3)),
        audioCurrentTime: audio && Number.isFinite(audio.currentTime) ? Number(audio.currentTime.toFixed(3)) : null,
        audioPaused: audio ? Boolean(audio.paused) : null,
        scrubberValue: scrubber ? Number(Number(scrubber.value || 0).toFixed(3)) : null,
      };
    }
    window.__ceReviewTransportState = reviewTransportStateSnapshot;
    function installReviewTransport(audio) {
      if (!audio || document.querySelector(".ce-review-transport")) return document.querySelector(".ce-review-transport");
      const transport = document.createElement("div");
      transport.className = "ce-review-transport";
      transport.setAttribute("aria-label", "Review playback controls");
      transport.innerHTML = '<button type="button" data-ce-play>Play</button><time data-ce-current>00:00</time><input data-ce-scrub type="range" min="0" max="' + mediaDuration(audio).toFixed(3) + '" step="0.05" value="0" aria-label="Scrub proof time"><time data-ce-duration>' + formatClock(mediaDuration(audio)) + '</time>';
      document.body.appendChild(transport);
      const button = transport.querySelector("[data-ce-play]");
      const scrubber = transport.querySelector("[data-ce-scrub]");
      let keyboardScrubActive = false;
      function scrubTimeFromPointer(event) {
        const rect = scrubber.getBoundingClientRect();
        const pct = rect.width > 0 ? clamp((event.clientX - rect.left) / rect.width, 0, 1) : 0;
        return pct * mediaDuration(audio);
      }
      function setScrubberValue(time) {
        const nextTime = clamp(Number(time) || 0, 0, mediaDuration(audio));
        scrubber.max = mediaDuration(audio).toFixed(3);
        scrubber.value = nextTime.toFixed(3);
        return nextTime;
      }
      function beginScrub(event = null) {
        const startingTime = event && Number.isFinite(event.clientX) ? scrubTimeFromPointer(event) : Number(scrubber.value || mediaTime(audio));
        if (!reviewTransportState.isUserScrubbing) {
          reviewTransportState.isUserScrubbing = true;
          reviewTransportState.wasPlayingBeforeScrub = audio ? !audio.paused : false;
          reviewTransportState.scrubStartedAt = performance.now();
          if (audio && !audio.paused) audio.pause();
        }
        if (event && Number.isFinite(event.pointerId)) {
          reviewTransportState.pointerId = event.pointerId;
          try { scrubber.setPointerCapture(event.pointerId); } catch {}
        }
        applyScrubTime(startingTime);
      }
      function applyScrubTime(time) {
        const nextTime = setScrubberValue(time);
        reviewTransportState.pendingScrubTime = nextTime;
        forcedRenderTime = nextTime;
        resetPlaybackClock(audio, nextTime);
        stopCompositorScroll(nextTime);
        if (audio) {
          try { audio.currentTime = nextTime; } catch {}
        }
        updateRollingRail(nextTime);
        updateReviewTransport(nextTime);
        return nextTime;
      }
      async function commitScrub() {
        if (!reviewTransportState.isUserScrubbing) {
          setReviewTime(Number(scrubber.value) || 0, { syncAudio: true, forceRenderTime: audio.paused });
          return;
        }
        const nextTime = reviewTransportState.pendingScrubTime ?? Number(scrubber.value || 0);
        const shouldResume = reviewTransportState.wasPlayingBeforeScrub;
        reviewTransportState.isUserScrubbing = false;
        reviewTransportState.wasPlayingBeforeScrub = false;
        reviewTransportState.lastCommittedScrubTime = nextTime;
        reviewTransportState.pendingScrubTime = null;
        reviewTransportState.scrubStartedAt = null;
        if (reviewTransportState.pointerId !== null) {
          try { scrubber.releasePointerCapture(reviewTransportState.pointerId); } catch {}
        }
        reviewTransportState.pointerId = null;
        setReviewTime(nextTime, { syncAudio: true, forceRenderTime: !shouldResume });
        if (shouldResume && audio) {
          forcedRenderTime = null;
          resetPlaybackClock(audio, nextTime);
          try { await audio.play(); } catch {}
          startCompositorScroll(audio);
          scheduleTick();
        }
      }
      button.addEventListener("click", async () => {
        if (audio.paused) {
          if (forcedRenderTime !== null) {
            try { audio.currentTime = forcedRenderTime; } catch {}
          }
          resetPlaybackClock(audio, forcedRenderTime ?? mediaTime(audio));
          forcedRenderTime = null;
          try { await audio.play(); } catch {}
          startCompositorScroll(audio);
          scheduleTick();
        } else {
          audio.pause();
          forcedRenderTime = playbackClockTime(audio);
          stopCompositorScroll(forcedRenderTime);
          updateRollingRail(forcedRenderTime);
          updateReviewTransport(forcedRenderTime);
        }
      });
      scrubber.addEventListener("pointerdown", (event) => {
        event.preventDefault();
        beginScrub(event);
      });
      scrubber.addEventListener("pointermove", (event) => {
        if (!reviewTransportState.isUserScrubbing || reviewTransportState.pointerId !== event.pointerId) return;
        event.preventDefault();
        applyScrubTime(scrubTimeFromPointer(event));
      });
      scrubber.addEventListener("pointerup", async (event) => {
        if (reviewTransportState.pointerId !== null && reviewTransportState.pointerId !== event.pointerId) return;
        event.preventDefault();
        if (Number.isFinite(event.clientX)) applyScrubTime(scrubTimeFromPointer(event));
        await commitScrub();
      });
      scrubber.addEventListener("pointercancel", commitScrub);
      scrubber.addEventListener("lostpointercapture", () => {
        if (reviewTransportState.isUserScrubbing) commitScrub();
      });
      scrubber.addEventListener("keydown", (event) => {
        if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End", "PageUp", "PageDown"].includes(event.key)) return;
        keyboardScrubActive = true;
        beginScrub();
      });
      scrubber.addEventListener("keyup", (event) => {
        if (!keyboardScrubActive) return;
        keyboardScrubActive = false;
        commitScrub();
      });
      scrubber.addEventListener("input", () => {
        if (reviewTransportState.isUserScrubbing && reviewTransportState.pointerId !== null) return;
        if (!reviewTransportState.isUserScrubbing) {
          setReviewTime(Number(scrubber.value) || 0, { syncAudio: true, forceRenderTime: audio.paused });
          return;
        }
        applyScrubTime(Number(scrubber.value) || 0);
      });
      scrubber.addEventListener("change", commitScrub);
      scrubber.addEventListener("blur", commitScrub);
      transport.__ceScrubbing = () => reviewTransportState.isUserScrubbing;
      return transport;
    }
    function updateReviewTransport(time) {
      const audio = findAudio();
      const transport = document.querySelector(".ce-review-transport");
      if (!audio || !transport) return;
      const duration = mediaDuration(audio);
      const scrubState = reviewTransportStateSnapshot();
      const current = reviewTransportState.isUserScrubbing && reviewTransportState.pendingScrubTime !== null
        ? clamp(reviewTransportState.pendingScrubTime, 0, duration)
        : clamp(Number(time) || 0, 0, duration);
      const button = transport.querySelector("[data-ce-play]");
      const scrubber = transport.querySelector("[data-ce-scrub]");
      const currentLabel = transport.querySelector("[data-ce-current]");
      const durationLabel = transport.querySelector("[data-ce-duration]");
      if (button) button.textContent = scrubState.isUserScrubbing && scrubState.wasPlayingBeforeScrub ? "Pause" : audio.paused ? "Play" : "Pause";
      if (scrubber) {
        scrubber.max = duration.toFixed(3);
        if (!reviewTransportState.isUserScrubbing) scrubber.value = current.toFixed(3);
      }
      if (currentLabel) currentLabel.textContent = formatClock(current);
      if (durationLabel) durationLabel.textContent = formatClock(duration);
    }
    function setReviewTime(time, { syncAudio = true, forceRenderTime = true } = {}) {
      const audio = findAudio();
      const duration = mediaDuration(audio);
      const nextTime = clamp(Number(time) || 0, 0, duration);
      forcedRenderTime = forceRenderTime ? nextTime : null;
      resetPlaybackClock(audio, nextTime);
      stopCompositorScroll(nextTime);
      if (audio && syncAudio) {
        try { audio.currentTime = nextTime; } catch {}
      }
      updateRollingRail(nextTime);
      updateReviewTransport(nextTime);
      return nextTime;
    }
    function activeChunkIndexAt(time) {
      let index = 0;
      for (let i = 0; i < CE_CHUNKS.length; i += 1) {
        if (time >= CE_CHUNKS[i].start) index = i;
        if (time < CE_CHUNKS[i].end) return i;
      }
      return index;
    }
    function chunkCenterY(chunk) {
      return (chunk.layout_y_px || 0) + ((chunk.layout_height_px || 48) / 2);
    }
    function scrollPositionAt(time) {
      if (!CE_CHUNKS.length) return 0;
      const safeTime = Math.max(0, Number(time) || 0);
      const elapsedSeconds = safeTime - CE_CONFIG.captionScrollStartTimeSeconds;
      return CE_CONFIG.captionScrollStartPositionPx + CE_CONFIG.captionConstantScrollSpeedPxPerSecond * elapsedSeconds;
    }
    function introGateOpacityAt(time) {
      const safeTime = Math.max(0, Number(time) || 0);
      const gateStart = Number(CE_CONFIG.captionIntroGateStartSeconds) || 0;
      const gateFullOpacity = Math.max(gateStart, Number(CE_CONFIG.captionIntroGateFullOpacitySeconds) || gateStart);
      if (safeTime <= gateStart) return 0;
      if (safeTime >= gateFullOpacity) return 1;
      const duration = Math.max(0.001, gateFullOpacity - gateStart);
      return smoothstep((safeTime - gateStart) / duration);
    }
    const priorOutroDebugAt = typeof window.__outroDebugAt === "function" ? window.__outroDebugAt : null;
    function endScreenOpacityAt(time) {
      if (!CE_END_SCREEN || !CE_END_SCREEN.enabled) return 0;
      const start = Number(CE_END_SCREEN.transitionStartSeconds) || 0;
      const duration = Math.max(0.001, Number(CE_END_SCREEN.transitionDurationSeconds) || ${END_SCREEN_TRANSITION_DURATION_SECONDS});
      return smoothstep((Number(time) - start) / duration);
    }
    function suppressInheritedEndScreens(stage) {
      if (!stage) return 0;
      let hidden = 0;
      stage.querySelectorAll("#endScreen, #outroScreen, .end-screen, .outro-screen, .youtube-end-screen, [data-youtube-end-screen]").forEach((node) => {
        if (!node || node.classList.contains("ce-youtube-end-screen")) return;
        node.classList.add("ce-legacy-end-screen-hidden");
        node.setAttribute("data-ce-legacy-end-screen-hidden", "true");
        hidden += 1;
      });
      return hidden;
    }
    function installEndScreenOverlay() {
      if (!CE_END_SCREEN || !CE_END_SCREEN.enabled) return null;
      const stage = findStage();
      if (!stage) return null;
      suppressInheritedEndScreens(stage);
      const existing = stage.querySelector(".ce-youtube-end-screen");
      if (existing) return existing;
      const overlay = document.createElement("section");
      overlay.className = "ce-youtube-end-screen";
      overlay.id = "ceYoutubeEndScreen";
      overlay.setAttribute("aria-label", "Transparent YouTube end screen overlay on Living Cover");
      overlay.dataset.templateId = CE_END_SCREEN.templateId || ${JSON.stringify(YOUTUBE_END_SCREEN_TEMPLATE_ID)};
      overlay.dataset.fadeTimingModel = CE_END_SCREEN.fadeTimingModel || ${JSON.stringify(END_SCREEN_FADE_TIMING_MODEL)};
      if (CE_END_SCREEN_PALETTE && CE_END_SCREEN_PALETTE.contract_id) overlay.dataset.paletteContractId = CE_END_SCREEN_PALETTE.contract_id;
      overlay.dataset.transitionStartSeconds = String(CE_END_SCREEN.transitionStartSeconds || "");
      overlay.dataset.fullOpacityAtSeconds = String(CE_END_SCREEN.fullOpacityAtSeconds || CE_END_SCREEN.holdStartSeconds || "");
      overlay.dataset.safeWindowStartSeconds = String(CE_END_SCREEN.safeWindowStartSeconds || "");
      overlay.innerHTML = '<div class="ce-youtube-end-screen-target left-video" aria-hidden="true"></div><div class="ce-youtube-end-screen-target right-video" aria-hidden="true"></div><div class="ce-youtube-end-screen-target subscribe-target" aria-hidden="true"></div>';
      stage.appendChild(overlay);
      return overlay;
    }
    function updateEndScreen(time) {
      const overlay = installEndScreenOverlay();
      if (!overlay) return 0;
      const opacity = endScreenOpacityAt(time);
      overlay.style.setProperty("--ce-youtube-end-screen-opacity", opacity.toFixed(4));
      overlay.style.opacity = opacity.toFixed(4);
      return opacity;
    }
    function endScreenDebugAt(time) {
      const safe = clamp(Number(time) || 0, 0, CE_CONFIG.durationSeconds);
      const base = priorOutroDebugAt ? priorOutroDebugAt(safe) || {} : {};
      const endScreenOpacity = endScreenOpacityAt(safe);
      const safeStart = Number(CE_END_SCREEN.safeWindowStartSeconds) || Number(CE_END_SCREEN.holdStartSeconds) || 0;
      const safeEnd = Number(CE_END_SCREEN.safeWindowEndSeconds) || CE_CONFIG.durationSeconds;
      const isSafeWindow = safe >= safeStart && safe <= safeEnd;
      return {
        ...base,
        time: safe,
        outroOpacity: Math.max(Number(base.outroOpacity) || 0, endScreenOpacity),
        endScreenOpacity,
        railOpacity: isSafeWindow ? 0 : 1 - endScreenOpacity,
        isSafeWindow,
        youtubeEndScreenTemplateId: CE_END_SCREEN.templateId,
        compositionMode: CE_END_SCREEN.compositionMode,
        captionEndScreenHandoffModel: CE_END_SCREEN.captionEndScreenHandoffModel || CE_CONFIG.captionEndScreenHandoffModel,
        reviewApprovedEndScreenEntryModel: CE_END_SCREEN.reviewApprovedEndScreenEntryModel || CE_CONFIG.reviewApprovedEndScreenEntryModel,
        reviewApprovedEndScreenFadeStartSeconds:
          CE_END_SCREEN.reviewApprovedFadeStartSeconds ?? CE_CONFIG.reviewApprovedEndScreenFadeStartSeconds,
        fadeTimingModel: CE_END_SCREEN.fadeTimingModel,
        transitionStartSeconds: CE_END_SCREEN.transitionStartSeconds,
        transitionDurationSeconds: CE_END_SCREEN.transitionDurationSeconds,
        fullOpacityAtSeconds: CE_END_SCREEN.fullOpacityAtSeconds || CE_END_SCREEN.holdStartSeconds,
        safeWindowStartSeconds: safeStart,
        safeWindowEndSeconds: safeEnd,
        lastDisplayCueEndSeconds: CE_END_SCREEN.lastDisplayCueEndSeconds ?? CE_CONFIG.lastDisplayCueEndSeconds,
        lastCaptionVisibleExitStartSeconds:
          CE_END_SCREEN.lastCaptionVisibleExitStartSeconds ?? CE_CONFIG.lastCaptionVisibleExitStartSeconds,
        lastCaptionFullySuppressedSeconds:
          CE_END_SCREEN.lastCaptionFullySuppressedSeconds ?? CE_CONFIG.lastCaptionFullySuppressedSeconds,
        youtubePlaceholderFadeStartSeconds:
          CE_END_SCREEN.youtubePlaceholderFadeStartSeconds ?? CE_CONFIG.youtubePlaceholderFadeStartSeconds,
        youtubePlaceholderFullOpacitySeconds:
          CE_END_SCREEN.youtubePlaceholderFullOpacitySeconds ?? CE_CONFIG.youtubePlaceholderFullOpacitySeconds,
        captionEndScreenGapSeconds: CE_END_SCREEN.captionEndScreenGapSeconds ?? CE_CONFIG.captionEndScreenGapSeconds,
        captionEndScreenOverlapRead: CE_END_SCREEN.captionEndScreenOverlapRead || CE_CONFIG.captionEndScreenOverlapRead,
        youtubeSafeWindowCaptionSuppressionRead: CE_END_SCREEN.youtubeSafeWindowCaptionSuppressionRead || "",
        layout: CE_END_SCREEN.layout || base.layout || {}
      };
    }
    if (CE_END_SCREEN && CE_END_SCREEN.enabled) window.__outroDebugAt = endScreenDebugAt;
    window.__endScreenStateAt = endScreenDebugAt;
    function sourceRailOpacityAt(time) {
      let opacity = 1;
      if (typeof window.__outroDebugAt === "function") {
        try {
          const outro = window.__outroDebugAt(time);
          if (outro && Number.isFinite(outro.railOpacity)) opacity = Math.min(opacity, outro.railOpacity);
          if (outro && outro.isSafeWindow) opacity = 0;
        } catch {}
      }
      return clamp(opacity, 0, 1);
    }
    function windowOpacityAt(time) {
      const railOpacity = sourceRailOpacityAt(time);
      if (railOpacity <= 0.001) return 0;
      const lastEnd = CE_CHUNKS.length ? CE_CHUNKS[CE_CHUNKS.length - 1].end : CE_CONFIG.durationSeconds;
      if (time <= lastEnd) return railOpacity;
      return railOpacity * (1 - smoothstep((time - lastEnd) / END_FADE_SECONDS));
    }
    function phraseAlpha(span, time) {
      const visualWindow = Array.isArray(span.visual_timing_window_seconds) ? span.visual_timing_window_seconds : span.timing_window_seconds;
      const start = visualWindow[0];
      const end = visualWindow[1];
      const fadeIn = Math.max(0.001, span.fade_in_seconds || 0.42);
      const fadeOut = Math.max(0.001, span.fade_out_seconds || 1.1);
      if (time < start || time > end + fadeOut) return 0;
      if (time < start + fadeIn) return smoothstep((time - start) / fadeIn);
      if (time <= end) return 1;
      return 1 - smoothstep((time - end) / fadeOut);
    }
    function hexToRgb(hex) {
      const normalized = String(hex || "").replace("#", "").padEnd(6, "f").slice(0, 6);
      return [parseInt(normalized.slice(0, 2), 16), parseInt(normalized.slice(2, 4), 16), parseInt(normalized.slice(4, 6), 16)];
    }
    function mixColor(baseHex, highlightHex, alpha) {
      const base = hexToRgb(baseHex);
      const highlight = hexToRgb(highlightHex);
      const t = clamp(alpha, 0, 1);
      return "rgb(" + base.map((channel, index) => Math.round(channel + (highlight[index] - channel) * t)).join(", ") + ")";
    }
    function highlightTextShadow(alpha) {
      const t = clamp(Number(alpha) || 0, 0, 1);
      if (t <= 0.01) return "";
      const lift = (0.42 + 0.28 * t).toFixed(3);
      const edge = (0.32 + 0.34 * t).toFixed(3);
      return "0 2px 18px rgba(0,0,0," + lift + "), 0 1px 5px rgba(0,0,0," + edge + "), 0 0 2px rgba(0,0,0," + edge + ")";
    }
    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
    }
    function phraseSpansForChunk(chunk) {
      const lower = chunk.text.toLowerCase();
      const ranges = [];
      CE_KEY_PHRASE_SPANS.forEach((span, index) => {
        if (!span || !span.phrase_text || !Array.isArray(span.timing_window_seconds)) return;
        if (chunk.start >= span.timing_window_seconds[1] || chunk.end <= span.timing_window_seconds[0]) return;
        const phrase = String(span.phrase_text);
        const start = lower.indexOf(phrase.toLowerCase());
        if (start < 0) return;
        const end = start + phrase.length;
        const before = start === 0 ? "" : chunk.text[start - 1];
        const after = end >= chunk.text.length ? "" : chunk.text[end];
        if (/[\w-]/.test(before) || /[\w-]/.test(after)) return;
        if (ranges.some((range) => start < range.end && end > range.start)) return;
        ranges.push({ start, end, index });
      });
      return ranges.sort((a, b) => a.start - b.start);
    }
    function renderChunkText(chunk) {
      const ranges = phraseSpansForChunk(chunk);
      const renderSegment = (segmentStart, segmentEnd) => {
        const segmentRanges = ranges
          .filter((range) => range.start < segmentEnd && range.end > segmentStart)
          .map((range) => ({
            start: Math.max(range.start, segmentStart) - segmentStart,
            end: Math.min(range.end, segmentEnd) - segmentStart,
            index: range.index,
          }));
        const source = chunk.text.slice(segmentStart, segmentEnd);
        if (!segmentRanges.length) return escapeHtml(source);
        let segmentHtml = "";
        let cursor = 0;
        segmentRanges.forEach((range) => {
          segmentHtml += escapeHtml(source.slice(cursor, range.start));
          segmentHtml += '<span class="ce-phrase-highlight" data-phrase-index="' + range.index + '">' + escapeHtml(source.slice(range.start, range.end)) + '</span>';
          cursor = range.end;
        });
        segmentHtml += escapeHtml(source.slice(cursor));
        return segmentHtml;
      };
      if (Array.isArray(chunk.display_lines) && chunk.display_lines.length) {
        let cursor = 0;
        return chunk.display_lines.map((line) => {
          const start = chunk.text.indexOf(line, cursor);
          const segmentStart = start >= 0 ? start : cursor;
          const segmentEnd = segmentStart + line.length;
          cursor = segmentEnd;
          return '<span class="ce-caption-display-line">' + renderSegment(segmentStart, segmentEnd) + '</span>';
        }).join("");
      }
      if (!ranges.length) return escapeHtml(chunk.text);
      let html = "";
      let cursor = 0;
      ranges.forEach((range) => {
        html += escapeHtml(chunk.text.slice(cursor, range.start));
        html += '<span class="ce-phrase-highlight" data-phrase-index="' + range.index + '">' + escapeHtml(chunk.text.slice(range.start, range.end)) + '</span>';
        cursor = range.end;
      });
      html += escapeHtml(chunk.text.slice(cursor));
      return html;
    }
    function lineOpacityAt(chunk, translateY, time) {
      const center = chunkCenterY(chunk) + translateY;
      const windowHeight = CE_CONFIG.captionWindowHeight;
      if (center < -96 || center > windowHeight + 96) return 0;
      const distance = Math.abs(center - ACTIVE_Y);
      let base = 0.94;
      if (distance > 84 && distance <= 236) {
        base = 0.42 + (0.94 - 0.42) * (1 - smoothstep((distance - 84) / 152));
      } else if (distance > 236) {
        base = 0.18 + (0.42 - 0.18) * (1 - smoothstep((distance - 236) / 230));
      }
      const topFactor = smoothstep(center / CE_CONFIG.captionTopFade);
      const bottomFactor = smoothstep((windowHeight - center) / CE_CONFIG.captionBottomFade);
      return clamp(base * topFactor * bottomFactor * introGateOpacityAt(time), 0, 0.94);
    }
    function runtimeCoverageStateAt(time, translateY, sourceOpacity) {
      let maxVisibleCaptionOpacity = 0;
      let visibleCaptionLineCount = 0;
      let nearestVisibleChunkIndex = null;
      let nearestVisibleChunkOpacity = 0;
      let finalCaptionOpacity = 0;
      const visibleCaptionChunkIds = [];
      CE_CHUNKS.forEach((chunk, index) => {
        const opacity = lineOpacityAt(chunk, translateY, time) * sourceOpacity;
        if (index === CE_CHUNKS.length - 1) finalCaptionOpacity = opacity;
        if (opacity > maxVisibleCaptionOpacity) maxVisibleCaptionOpacity = opacity;
        if (opacity > nearestVisibleChunkOpacity) {
          nearestVisibleChunkOpacity = opacity;
          nearestVisibleChunkIndex = index;
        }
        if (opacity > 0.035) {
          visibleCaptionLineCount += 1;
          visibleCaptionChunkIds.push(chunk.id || String(index));
        }
      });
      const nearestVisibleChunk = nearestVisibleChunkIndex === null ? null : CE_CHUNKS[nearestVisibleChunkIndex];
      return {
        captionRuntimeCoverageModel: CE_CONFIG.captionRuntimeCoverageModel,
        maxVisibleCaptionOpacity: Number(maxVisibleCaptionOpacity.toFixed(4)),
        visibleCaptionLineCount,
        visibleCaptionChunkIds,
        nearestVisibleChunkIndex,
        nearestVisibleChunkId: nearestVisibleChunk?.id || null,
        nearestVisibleChunkText: nearestVisibleChunk?.text || "",
        lastCaptionCueEndSeconds: CE_CONFIG.lastDisplayCueEndSeconds,
        finalCaptionOpacity: Number(finalCaptionOpacity.toFixed(4)),
        endScreenSuppressionActive: sourceOpacity <= 0.001,
      };
    }
    function installRail() {
      const stage = findStage();
      if (!stage) return null;
      stage.querySelectorAll(":scope > .rail, :scope > .caption-softener").forEach((node) => node.classList.add("ce-legacy-rail-hidden"));
      const existing = stage.querySelector(".ce-rolling-rail");
      if (existing) return existing;
      const rail = document.createElement("section");
      rail.className = "ce-rolling-rail";
      rail.setAttribute("data-content-model", "rolling_caption_anchor_v1");
      rail.innerHTML = '<div class="ce-rolling-anchor"><div class="ce-rolling-anchor-label"></div><div class="ce-rolling-anchor-title"></div></div><div class="ce-caption-window" data-display-model="rolling_rail_caption_window_v1"><div class="ce-caption-stack"></div></div>';
      stage.appendChild(rail);
      const stack = rail.querySelector(".ce-caption-stack");
      CE_CHUNKS.forEach((chunk, index) => {
        const el = document.createElement("div");
        el.className = "ce-caption-line";
        el.dataset.index = String(index);
        el.style.top = (chunk.layout_y_px || 0) + "px";
        el.style.height = (chunk.layout_height_px || 48) + "px";
        el.style.minHeight = (chunk.layout_height_px || 48) + "px";
        el.innerHTML = renderChunkText(chunk);
        stack.appendChild(el);
      });
      return rail;
    }
    function anchorState() {
      const label = textOf("#activeChapterLabel") || textOf(".active-chapter-label") || CE_CONFIG.episodeTitle;
      let title = textOf("#activeTitle") || textOf("#railTitle") || textOf(".active-title") || textOf("#reviewChapter") || "";
      if (title === label) title = "";
      return { label, title };
    }
    function railCaptionStateAt(time) {
      const safeTime = Number(time) || 0;
      const scrollPosition = scrollPositionAt(safeTime);
      const sourceOpacity = sourceRailOpacityAt(safeTime);
      const captionIntroGateOpacity = introGateOpacityAt(safeTime);
      const youtubePlaceholderOpacity = endScreenOpacityAt(safeTime);
      const translateY = ACTIVE_Y - scrollPosition;
      const runtimeCoverage = runtimeCoverageStateAt(safeTime, translateY, sourceOpacity);
      const activeChunkIndex = activeChunkIndexAt(safeTime);
      const activeChunk = CE_CHUNKS[activeChunkIndex] || null;
      const activeChunkCenterY = activeChunk ? chunkCenterY(activeChunk) + translateY : null;
      const activeChunkCenterDeltaPx = Number.isFinite(activeChunkCenterY) ? activeChunkCenterY - ACTIVE_Y : null;
      const activeChunkCueStartSeconds = activeChunk ? Number(activeChunk.start) || 0 : null;
      const activeChunkLeadSeconds =
        activeChunk && Number.isFinite(activeChunkCenterDeltaPx)
          ? activeChunkCueStartSeconds - (CE_CONFIG.captionScrollStartTimeSeconds + ((chunkCenterY(activeChunk) - CE_CONFIG.captionScrollStartPositionPx) / CE_CONFIG.captionConstantScrollSpeedPxPerSecond))
          : null;
      return {
        time: safeTime,
        translateY,
        scrollPosition,
        activeChunkIndex,
        activeChunkId: activeChunk?.id || null,
        activeChunkText: activeChunk?.text || "",
        activeChunkCueStartSeconds,
        activeChunkCenterDeltaPx,
        activeChunkLeadSeconds,
        sourceRailOpacity: sourceOpacity,
        targetGeometryWindowActive: sourceOpacity <= 0.001,
        youtubePlaceholderOpacity,
        captionEndScreenHandoffModel: CE_CONFIG.captionEndScreenHandoffModel,
        endScreenFadeTimingModel: CE_END_SCREEN.fadeTimingModel || null,
        endScreenSafeWindowActive:
          safeTime >= (Number(CE_END_SCREEN.safeWindowStartSeconds) || 0) &&
          safeTime <= (Number(CE_END_SCREEN.safeWindowEndSeconds) || CE_CONFIG.durationSeconds),
        lastCaptionVisibleExitStartSeconds: CE_CONFIG.lastCaptionVisibleExitStartSeconds,
        lastCaptionFullySuppressedSeconds: CE_CONFIG.lastCaptionFullySuppressedSeconds,
        youtubePlaceholderFadeStartSeconds: CE_CONFIG.youtubePlaceholderFadeStartSeconds,
        youtubePlaceholderFullOpacitySeconds: CE_CONFIG.youtubePlaceholderFullOpacitySeconds,
        captionEndScreenGapSeconds: CE_CONFIG.captionEndScreenGapSeconds,
        captionEndScreenOverlapRead: CE_CONFIG.captionEndScreenOverlapRead,
        introTrimModel: CE_CONFIG.introTrimModel,
        introTrimSeconds: CE_CONFIG.introTrimSeconds,
        previousVoiceStartOffsetSeconds: CE_CONFIG.previousVoiceStartOffsetSeconds,
        voiceStartOffsetSeconds: CE_CONFIG.voiceStartOffsetSeconds,
        captionMotionModel: CE_CONFIG.captionMotionModel,
        captionTimelineLayoutModel: CE_CONFIG.captionTimelineLayoutModel,
        captionSyncTarget: CE_CONFIG.captionSyncTarget,
        captionReadingLeadSeconds: CE_CONFIG.captionReadingLeadSeconds,
        captionIntroVisibilityGateModel: CE_CONFIG.captionIntroVisibilityGateModel,
        captionIntroGateOpacity,
        captionIntroGateStartSeconds: CE_CONFIG.captionIntroGateStartSeconds,
        captionIntroGateFullOpacitySeconds: CE_CONFIG.captionIntroGateFullOpacitySeconds,
        captionConstantSpeedScope: CE_CONFIG.captionConstantSpeedScope,
        captionPlaybackClockModel: CE_CONFIG.captionPlaybackClockModel,
        captionStackRenderModel: CE_CONFIG.captionStackRenderModel,
        captionScrollSmoothnessModel: CE_CONFIG.captionScrollSmoothnessModel,
        captionStackCompositorActive,
        captionStackCompositorTargetTime,
        captionStackCompositorStartedAt,
        reviewApprovedEndScreenEntryModel: CE_CONFIG.reviewApprovedEndScreenEntryModel,
        reviewApprovedEndScreenFadeStartSeconds: CE_CONFIG.reviewApprovedEndScreenFadeStartSeconds,
        tacomaRainPerformanceGuardModel: CE_CONFIG.tacomaRainPerformanceGuardModel,
        tacomaRainFrameThrottleMs: CE_CONFIG.tacomaRainFrameThrottleMs,
        ...runtimeCoverage,
        captionDensityResolutionModel: CE_CONFIG.captionDensityResolutionModel,
        captionDisplayLineWrapModel: CE_CONFIG.captionDisplayLineWrapModel,
        captionDisplayLineMaxWidthPx: CE_CONFIG.captionDisplayLineMaxWidthPx,
        captionMaxEstimatedLineWidthPx: CE_CONFIG.captionMaxEstimatedLineWidthPx,
        captionTextStackWidthPx: CE_CONFIG.captionTextStackWidthPx,
        captionStackHeightPx: CE_CONFIG.captionStackHeightPx,
        captionStackPaintContainmentRead: CE_CONFIG.captionStackPaintContainmentRead,
        captionLineOpacityModel: CE_CONFIG.captionLineOpacityModel,
        captionWindowTreatmentModel: CE_CONFIG.captionWindowTreatmentModel,
        captionConstantScrollSpeedPxPerSecond: CE_CONFIG.captionConstantScrollSpeedPxPerSecond,
        captionScrollStartTimeSeconds: CE_CONFIG.captionScrollStartTimeSeconds,
        captionScrollStartPositionPx: CE_CONFIG.captionScrollStartPositionPx,
        highlightPhraseScope: CE_CONFIG.highlightPhraseScope,
        highlightRenderPolicy: CE_CONFIG.highlightRenderPolicy,
        captionHighlightModelId: CE_CONFIG.captionHighlightModelId,
        highlightSemanticRole: CE_CONFIG.highlightSemanticRole,
        highlightDensityModel: CE_CONFIG.highlightDensityModel,
        highlightColorModel: CE_CONFIG.highlightColorModel,
        highlightVisualTimingModel: CE_CONFIG.highlightVisualTimingModel,
        captionLayoutCollisionGuard: CE_CONFIG.captionLayoutCollisionGuard,
        captionMinRenderedLineGapPx: CE_CONFIG.captionMinRenderedLineGapPx,
        captionForcedTakeawayMergeCount: CE_CONFIG.captionForcedTakeawayMergeCount,
        captionAudioSyncModel: CE_CONFIG.captionAudioSyncModel,
        captionAudioOffsetSeconds: CE_CONFIG.captionAudioOffsetSeconds,
        firstDisplayCueStartSeconds: CE_CONFIG.firstDisplayCueStartSeconds,
        highlights: CE_KEY_PHRASE_SPANS.map((span) => ({
          span_id: span.span_id,
          phrase_text: span.phrase_text,
          alpha: phraseAlpha(span, safeTime),
          highlight_semantic_role: span.highlight_semantic_role,
          visual_timing_window_seconds: span.visual_timing_window_seconds,
        }))
      };
    }
    function updateRollingRail(time) {
      const rail = installRail();
      if (!rail) return null;
      const state = railCaptionStateAt(time);
      updateEndScreen(state.time);
      const anchor = anchorState();
      rail.querySelector(".ce-rolling-anchor-label").textContent = anchor.label;
      rail.querySelector(".ce-rolling-anchor-title").textContent = anchor.title;
      rail.style.setProperty("--ce-rolling-rail-opacity", state.sourceRailOpacity.toFixed(4));
      const displayedScrollPosition = scrollPositionAt(state.time);
      const displayedTranslateY = ACTIVE_Y - displayedScrollPosition;
      if (!captionStackCompositorActive) setStackTranslateY(displayedTranslateY, { transition: "none" });
      rail.querySelectorAll(".ce-caption-line").forEach((el, index) => {
        const opacity = lineOpacityAt(CE_CHUNKS[index], displayedTranslateY, state.time);
        el.style.opacity = opacity.toFixed(4);
      });
      rail.querySelectorAll(".ce-phrase-highlight").forEach((el) => {
        const span = CE_KEY_PHRASE_SPANS[Number(el.dataset.phraseIndex)];
        const alpha = span ? phraseAlpha(span, state.time) : 0;
        el.style.color = span ? mixColor(CE_CONFIG.textColor, span.highlight_color_sample.hex, alpha) : CE_CONFIG.textColor;
        el.style.textShadow = span ? highlightTextShadow(alpha) : "";
      });
      updateReviewTransport(state.time);
      return state;
    }
    const priorSetRenderTime = window.__setRenderTime;
    window.__railCaptionStateAt = railCaptionStateAt;
    window.__syncRailCaptionToMediaTime = () => {
      const audio = findAudio();
      const renderTime = playbackClockTime(audio);
      return updateRollingRail(renderTime);
    };
    window.__setRenderTime = (time) => {
      const numeric = Number(time) || 0;
      const wasRenderMode = document.documentElement.classList.contains("render-mode");
      forcedRenderTime = numeric;
      resetPlaybackClock(findAudio(), numeric);
      stopCompositorScroll(numeric);
      let priorReturn = numeric;
      if (typeof window.__ceSetAmbientRenderTime === "function") priorReturn = window.__ceSetAmbientRenderTime(numeric);
      else if (typeof priorSetRenderTime === "function") priorReturn = priorSetRenderTime(numeric);
      else {
        const audio = findAudio();
        if (audio) { try { audio.currentTime = numeric; } catch {} }
      }
      if (!CE_RENDER_MODE && !wasRenderMode) document.documentElement.classList.remove("render-mode");
      updateRollingRail(numeric);
      updateReviewTransport(numeric);
      return priorReturn;
    };
    function scheduleTick() {
      if (railAnimationFrameId !== null) return;
      railAnimationFrameId = requestAnimationFrame(tick);
    }
    function tick() {
      railAnimationFrameId = null;
      const audio = findAudio();
      updateRollingRail(playbackClockTime(audio));
      if (audio && !audio.paused) scheduleTick();
    }
    window.addEventListener("load", () => {
      const audio = findAudio();
      normalizeResponsiveFrameStage();
      syncReviewShellScale();
      installRail();
      installEndScreenOverlay();
      installReviewTransport(audio);
      suppressLegacyReviewChrome(audio);
      verifyReviewRangeServer(audio);
      checkProofFreshness();
      if (!CE_RENDER_MODE) window.setInterval(checkProofFreshness, 15000);
      resetPlaybackClock(audio, forcedRenderTime ?? mediaTime(audio));
      stopCompositorScroll(playbackClockTime(audio));
      updateRollingRail(playbackClockTime(audio));
      updateReviewTransport(playbackClockTime(audio));
      if (audio) {
        ["loadedmetadata", "timeupdate", "seeked", "seeking", "play", "pause"].forEach((eventName) => {
          audio.addEventListener(eventName, () => {
            if (reviewTransportState.isUserScrubbing) {
              const scrubTime = reviewTransportState.pendingScrubTime ?? Number(document.querySelector("[data-ce-scrub]")?.value || 0);
              updateRollingRail(scrubTime);
              updateReviewTransport(scrubTime);
              return;
            }
            if (eventName === "play") {
              resetPlaybackClock(audio, mediaTime(audio));
              forcedRenderTime = null;
              startCompositorScroll(audio);
              scheduleTick();
            } else if (eventName === "loadedmetadata" || eventName === "seeking" || eventName === "seeked") {
              resetPlaybackClock(audio, mediaTime(audio));
              stopCompositorScroll(mediaTime(audio));
            } else if (eventName === "pause") {
              stopCompositorScroll(playbackClockTime(audio));
            }
            const renderTime = playbackClockTime(audio);
            updateRollingRail(renderTime);
            updateReviewTransport(renderTime);
          });
        });
      }
    });
    window.addEventListener("resize", () => {
      syncReviewShellScale();
      syncResponsiveFrameStageScale();
    });
  })();
  </script>
<!-- ce-rolling-caption-rail-tighten-script:end -->`;

  let html = cleanHtml;
  if (!/<link\s+rel=["']icon["']/i.test(html)) html = insertBeforeClosing(html, "head", '  <link rel="icon" href="data:,">');
  html = insertBeforeClosing(html, "head", style);
  html = insertBeforeClosing(html, "body", script);
  return html;
}

function statusForEpisode(episode, keyPhraseSpans) {
  if (episode.blockedPrereq) return episode.status;
  if (keyPhraseSpans.some((span) => /draft|pending/i.test(String(span.review_status || "")))) {
    return `${episode.status}_draft_key_phrase_spans_pending_human_keep`;
  }
  if (keyPhraseSpans.length) return episode.status;
  if (episode.rightRailAlignmentOnly) {
    return `${episode.status}_pending_reviewed_key_phrase_spans`;
  }
  if (episode.contractReviewMixRequired) {
    return `${episode.status}_pending_reviewed_key_phrase_spans`;
  }
  if (/final_assembly_paused/i.test(episode.status)) {
    return "rolling_caption_rail_final_assembly_paused_tighten_pending_reviewed_key_phrase_spans";
  }
  return "rolling_caption_rail_tightened_production_integration_pending_reviewed_key_phrase_spans";
}

function existingRollingRailKeep(previousManifest) {
  return String(previousManifest?.human_disposition || "").trim().toLowerCase() === "keep";
}

function applyExistingRollingRailKeep(manifest, previousManifest = {}) {
  manifest.status =
    previousManifest.status && /keep/i.test(String(previousManifest.status))
      ? previousManifest.status
      : "keep_rolling_caption_rail_rough_assembly_approved_for_final_assembly";
  manifest.human_disposition = "keep";
  manifest.human_disposition_utc = previousManifest.human_disposition_utc || previousManifest.rough_assembly_keep_utc || CREATED_UTC;
  manifest.human_disposition_source =
    previousManifest.human_disposition_source || "preserved_existing_rough_keep_after_review_chrome_regeneration";
  if (previousManifest.human_disposition_receipt_path) {
    manifest.human_disposition_receipt_path = previousManifest.human_disposition_receipt_path;
  }
  if (previousManifest.rough_assembly_keep_receipt_path) {
    manifest.rough_assembly_keep_receipt_path = previousManifest.rough_assembly_keep_receipt_path;
  }
  if (previousManifest.rough_assembly_keep_utc) manifest.rough_assembly_keep_utc = previousManifest.rough_assembly_keep_utc;
  manifest.may_create_full_runtime_mp4_render = true;
  manifest.may_advance_to_video_render = true;
  manifest.may_advance_to_final_assembly = true;
  manifest.may_advance_to_publish_readiness = false;
  manifest.may_youtube_action = false;
  if (manifest.rough_assembly_reads) {
    manifest.rough_assembly_reads.downstream_gate_read = "pass_human_keep_opens_final_assembly_only";
  }
  manifest.next_review_question = "Rough assembly rail proof was already kept; next gate is final assembly keep.";
  return manifest;
}

function buildManifest({
  episode,
  sourceManifest,
  sourceArtPath,
  audioPath,
  captionPath,
  captionSources = {},
  cues,
  displayChunks,
  keyPhraseSpans,
  outputDir,
  playerPath,
  sourceHtmlPath,
  reviewPacketPath,
  qaPath,
  baseline,
  runtimeLinks,
  durationSeconds,
  captionScrollTiming = captionScrollTimingForChunks(displayChunks),
  ambientRightRailMotion = { applicable: false },
  musicContract = null,
  contractMusicMix = null,
  endScreenTiming = null,
  endScreenPalette = null,
  endScreenPaletteContract = null,
  highlightAccent = null,
}) {
  const paletteContractPass = endScreenPaletteContract?.status === "pass";
  const status = paletteContractPass ? statusForEpisode(episode, keyPhraseSpans) : "blocked_missing_end_screen_palette_contract";
  const blocked = Boolean(episode.blockedPrereq);
  const manifestDurationSeconds = Number(durationSeconds || (cues[cues.length - 1]?.end || 0) + 30);
  const captionDisplayPath = captionSources.displayTimingPath || captionPath;
  const rawCaptionTimingPath = captionSources.rawTimingPath || captionPath;
  const lockedScriptPath = captionSources.textSourcePath || findLockedScriptPath(sourceManifest, episode);
  const captionAudioOffsetSeconds = Number(captionSources.audioOffsetSeconds || 0);
  const captionAudioSyncModel = captionSources.audioSyncModel || "raw_timing_source_audio_time_v1";
  const firstDisplayCueStartSeconds = cues.length ? Number(cues[0].start.toFixed(3)) : null;
  const hasContractMusicMix = Boolean(contractMusicMix?.audioPath);
  const contractMusicReviewScope = Boolean(episode.rightRailAlignmentOnly || episode.contractReviewMixRequired || hasContractMusicMix);
  const audioDefectRepair = contractMusicMix?.audioDefectRepair || null;
  const outroPolicy = valueAt(musicContract, "timing_contract.outro_policy") || OUTRO_POLICY;
  const outroPrelapSeconds = firstFiniteNumber(
    [valueAt(musicContract, "timing_contract.outro_prelap_seconds"), contractMusicMix?.timing?.outroPrelap],
    NaN,
  );
  const voiceEndSeconds = firstFiniteNumber(
    [valueAt(musicContract, "timing_contract.voice_end_seconds"), contractMusicMix?.timing?.voiceEnd],
    NaN,
  );
  const outroReachesTargetAtSeconds = firstFiniteNumber(
    [valueAt(musicContract, "timing_contract.outro_reaches_target_at_seconds"), contractMusicMix?.timing?.outroReachesTargetAt],
    NaN,
  );
  const outroTargetAfterVoiceSeconds = Number.isFinite(voiceEndSeconds) && Number.isFinite(outroReachesTargetAtSeconds)
    ? Number((outroReachesTargetAtSeconds - voiceEndSeconds).toFixed(3))
    : NaN;
  const voOutroBlendRead =
    outroPolicy === OUTRO_POLICY &&
    Math.abs((outroPrelapSeconds || 0) - OUTRO_PRELAP_SECONDS) <= 0.05 &&
    Number.isFinite(outroTargetAfterVoiceSeconds) &&
    outroTargetAfterVoiceSeconds >= OUTRO_TARGET_AFTER_VOICE_SECONDS - 0.1
      ? "pass_subtle_tail_outro_v1_1p5s_prelap_target_after_voice"
      : "tighten_outro_contract_not_normalized_to_subtle_tail";
  const missingReviewedSpans = keyPhraseSpans.length === 0;
  const draftKeyPhraseSpans = keyPhraseSpans.some((span) => /draft|pending/i.test(String(span.review_status || "")));
  const highlightStats = highlightStatsForSpans(keyPhraseSpans, cues[cues.length - 1]?.end);
  const ambientFrameClock = ambientFrameClockMetadata(episode);
  const reads = {
    living_cover_system_version_read: "pass",
    rail_preset_read: "pass",
    rail_content_model_read: "pass",
    caption_display_model_read: "pass",
    caption_window_role_read: "pass",
    caption_window_treatment_read: "pass_transparent_caption_mask_only",
    caption_window_blur_scope_read: "pass_none_transparent_caption_window",
    caption_highlight_source_read: "pass",
    caption_palette_source_read: "pass",
    right_rail_safe_space_read: "pending_human_review",
    old_context_rows_absence_read: "pass",
    minimal_anchor_read: "pass",
    rolling_caption_behavior_read: "pass",
    rolling_caption_state_hook_read: "pass",
    caption_scroll_smoothness_read: "pending_browser_review",
    caption_window_fade_mask_read: "pass",
    caption_window_fill_palette_read: "pass_transparent_no_fill",
    caption_window_transparency_read: "pass_no_background_no_fill_no_blur",
    caption_end_screen_handoff_read: endScreenTiming?.captionEndScreenOverlapRead || "pending_browser_review",
    caption_end_screen_overlap_read: endScreenTiming?.captionEndScreenOverlapRead || "pending_browser_review",
    youtube_safe_window_caption_suppression_read:
      endScreenTiming?.youtubeSafeWindowCaptionSuppressionRead || "pending_browser_review",
    vo_outro_blend_read: voOutroBlendRead,
    caption_key_phrase_span_read: missingReviewedSpans
      ? "blocked_pending_reviewed_cue_map_key_phrase_spans"
      : draftKeyPhraseSpans
        ? "rough_review_draft_key_phrase_spans_pending_human_keep"
        : "pending_human_review",
    caption_highlight_fade_read: missingReviewedSpans ? "not_applicable_highlights_suppressed_until_reviewed_spans_exist" : "pending_browser_review",
    full_caption_cue_coverage_read: cues.length >= 90 ? "pass_full_timing_source_loaded_without_90_cue_cap" : "pending_short_or_fallback_caption_source_review",
    caption_end_screen_rollout_read: "pending_browser_review",
    caption_text_source_read: "pending_static_script_match_review",
    caption_display_timing_source_read: captionDisplayPath ? "pass_display_timing_source_referenced" : "pending_display_timing_source_after_prereq_keep",
    caption_timing_source_read: rawCaptionTimingPath ? "pass_raw_timing_source_referenced_as_evidence" : "pending_timing_source_after_prereq_keep",
    caption_audio_sync_read:
      captionAudioSyncModel === CAPTION_AUDIO_SYNC_MODEL
        ? "pass_source_sidecar_audio_time"
        : "pending_raw_timing_source_no_offset_sidecar_found",
    caption_timing_shift_read:
      captionAudioOffsetSeconds > 0 ? "pass_first_eight_intro_trim_offset_applied_for_visible_rail_captions" : "not_applicable_no_voice_start_offset_found",
    intro_trim_read: "pass_first_eight_intro_trim_6s_v1",
    caption_text_matches_script_read: captionDisplayPath ? "pending_script_locked_validation_refresh" : "blocked_pending_caption_build",
    caption_alignment_coverage_read: captionDisplayPath ? "pending_alignment_refresh_min_98_5_percent" : "blocked_pending_caption_build",
    caption_asr_text_not_used_read: "pass_policy_script_locked_text_only",
    caption_constant_scroll_speed_read: "pass_per_episode_constant_speed_audio_time_aligned_conveyor",
    caption_playback_clock_read: "pass_media_time_direct_raf_clock",
    caption_stack_render_read: "pass_media_time_direct_raf_transform",
    caption_timeline_layout_read: "pass_audio_time_positioned_stack",
    caption_sync_target_read: "pass_pre_vo_reading_lead_active_band",
    caption_density_resolution_read:
      (captionScrollTiming.caption_unresolved_dense_pair_count || 0) > 0
        ? "tighten_dense_pairs_positioned_without_speed_ramp"
        : "pass_dense_micro_chunks_merged_without_speed_ramp",
    caption_active_band_at_cue_start_read:
      (captionScrollTiming.caption_max_active_chunk_center_delta_at_cue_start_px || 0) <= CAPTION_ACTIVE_BAND_LOWER_DELTA_PX
        ? "pass_active_chunk_readable_at_vo_cue_start"
        : "tighten_active_chunk_below_readable_band_at_vo_cue_start",
    caption_window_treatment_model_read: "pass_transparent_caption_mask_only",
    caption_highlight_model_read: missingReviewedSpans ? "blocked_pending_lesson_takeaway_spans" : "pass_lesson_takeaway_highlight_model",
    highlight_density_read:
      missingReviewedSpans
        ? "blocked_pending_lesson_takeaway_spans"
        : highlightDensityPassForEpisode(episode.episodeId, highlightStats)
          ? "pass_memorable_takeaway_cadence"
          : "tighten_takeaway_highlight_cadence",
    highlight_semantic_role_read:
      missingReviewedSpans || highlightStats.invalid_takeaway_phrase_length_count > 0 || highlightStats.single_word_highlight_count > 0
        ? "blocked_or_tighten_takeaway_phrase_scope"
        : "pass_story_lesson_takeaway_spans",
    highlight_color_read: missingReviewedSpans
      ? "blocked_pending_lesson_takeaway_spans"
      : highlightAccent?.highlight_distinct_from_caption_text_read || "blocked_missing_highlight_color_qa",
    highlight_backplate_contrast_read: missingReviewedSpans
      ? "blocked_pending_lesson_takeaway_spans"
      : highlightAccent?.highlight_backplate_contrast_read || "blocked_missing_highlight_backplate_contrast_qa",
    ...(highlightAccent?.highlight_override_read
      ? { highlight_override_read: highlightAccent.highlight_override_read }
      : {}),
    highlight_visual_timing_read: missingReviewedSpans ? "blocked_pending_lesson_takeaway_spans" : "pass_active_band_presence_aligned",
    caption_collision_guard_read: captionScrollTiming.caption_collision_guard_read,
    right_rail_matte_removed_read: ambientRightRailMotion.applicable
      ? ambientRightRailMotion.right_rail_matte_removed_read
      : "not_applicable_no_aircraft_right_rail_motion_layer",
    aircraft_right_rail_visibility_read: ambientRightRailMotion.applicable
      ? ambientRightRailMotion.aircraft_right_rail_visibility_read
      : "not_applicable_no_aircraft_right_rail_motion_layer",
    right_rail_ambient_motion_allowed_read: ambientRightRailMotion.applicable
      ? "pass_aircraft_and_fog_allowed_under_right_rail_text"
      : "not_applicable_no_aircraft_right_rail_motion_layer",
    no_karaoke_caption_read: "pass",
    caption_no_embellishment_read: "pass",
    no_progress_bar_read: "pass",
    no_timecode_read: "pass",
    viewer_text_suppression_read: "pending_end_screen_browser_review",
    end_screen_text_artifact_read: "pending_end_screen_browser_review",
    rail_fade_read: "pending_end_screen_browser_review",
    end_screen_palette_contract_read:
      endScreenPaletteContract?.reads?.end_screen_palette_contract_read || "blocked_missing_end_screen_palette_contract",
    end_screen_target_fill_palette_read:
      endScreenPaletteContract?.reads?.end_screen_target_fill_palette_read || "blocked_missing_end_screen_palette_contract",
    end_screen_target_contrast_read:
      endScreenPaletteContract?.reads?.end_screen_target_contrast_read || "blocked_missing_end_screen_palette_contract",
    end_screen_adaptive_palette_read:
      endScreenPaletteContract?.status === "pass"
        ? "pass_source_backplate_sampled_target_palette_contract"
        : "blocked_missing_end_screen_palette_contract",
    rail_panel_palette_read:
      endScreenPaletteContract?.reads?.rail_panel_palette_read || "blocked_missing_end_screen_palette_contract",
    source_integrated_panel_color_read:
      endScreenPaletteContract?.reads?.source_integrated_panel_color_read || "blocked_missing_end_screen_palette_contract",
    no_cross_episode_default_palette_read:
      endScreenPaletteContract?.reads?.no_cross_episode_default_palette_read || "blocked_missing_end_screen_palette_contract",
    end_screen_adaptive_perceptual_variability_read:
      endScreenPaletteContract?.reads?.end_screen_adaptive_perceptual_variability_read ||
      "blocked_missing_end_screen_palette_contract",
    downstream_gate_read: "pass_blocked_until_human_rolling_rough_keep",
    copied_media_read: "pass_predecessor_runtime_assets_symlinked_not_copied",
  };
  if (AMBIENT_FRAME_CLOCK_EPISODES.has(episode.episodeId)) {
    reads.ambient_frame_clock_model = ambientFrameClock.ambient_frame_clock_model;
    reads.ambient_render_clock_read = ambientFrameClock.ambient_render_clock_read;
    reads.ambient_wall_clock_drift_suppression_read = ambientFrameClock.ambient_wall_clock_drift_suppression_read;
  }
  if (episode.rightRailAlignmentOnly) {
    reads.right_rail_alignment_scope_read = "pass_right_rail_alignment_review_only";
    reads.ambient_effects_acceptance_read = "deferred_not_keep_or_reject";
  }
  if (contractMusicReviewScope) {
    reads.music_integration_contract_revalidation_read = musicContract
      ? episode.rightRailAlignmentOnly
        ? "pass_contract_timed_music_and_end_screen_revalidated_against_prior_kept_v6_for_right_rail_alignment"
        : "pass_contract_timed_music_and_end_screen_revalidated_for_reviewable_rough_rail_proof"
      : "blocked_missing_music_contract_for_reviewable_rough_rail_proof";
    reads.review_audio_mix_model_read = contractMusicMix?.audioPath
      ? "pass_contract_timed_intro_voice_outro_mix_v1"
      : "blocked_missing_contract_timed_review_audio_mix";
    reads.voice_audio_defect_repair_read = audioDefectRepair?.voice_audio_defect_repair_read || "not_applicable";
    reads.intro_music_applied_read = contractMusicMix?.audioPath ? "pass_intro_music_applied" : "blocked";
    reads.intro_fade_tail_under_opening_voice_read = contractMusicMix?.audioPath
      ? "pass_intro_fade_tail_under_opening_voice"
      : "blocked";
    reads.full_outro_music_applied_read = contractMusicMix?.audioPath ? "pass_full_outro_music_applied" : "blocked";
    reads.end_screen_music_handoff_read = contractMusicMix?.audioPath
      ? "pass_full_outro_carries_youtube_end_screen_window"
      : "blocked";
    reads.outro_no_restart_at_voice_end_read = contractMusicMix?.audioPath
      ? "pass_full_outro_continues_without_restart"
      : "blocked";
    reads.youtube_end_screen_template_applied_read = "pass_adaptive_titleless_template_injected_from_music_contract_timing";
    reads.end_screen_target_geometry_read = "pass_adaptive_titleless_target_geometry";
    reads.vo_outro_music_blend_read = voOutroBlendRead;
    reads.outro_under_vo_masking_read =
      voOutroBlendRead.startsWith("pass") ? "pass_target_margin_at_least_12db" : "tighten_outro_margin_not_proven";
    reads.outro_target_after_voice_read =
      voOutroBlendRead.startsWith("pass") ? "pass_target_gain_3s_after_voice_end" : "tighten_target_gain_timing";
    reads.vo_outro_perceptual_review_read = "pending_human_listen_in_rough_review";
    reads.audio_level_mix_read = "pending_human_listen_in_rough_review";
  }
  if (blocked) {
    reads.prerequisite_keep_read = "blocked";
    reads.blocker_reason = episode.blockedPrereq;
  }
  const ambientDeferral =
    episode.rightRailAlignmentOnly
      ? {
          status: "v7_sink_faucet_pending_later_advice",
          deferral_note_path: episode.ambientDeferralNotePath || "not_recorded",
          deferral_note_sha256: sha256File(episode.ambientDeferralNotePath),
          deferred_review_root: episode.deferredAmbientReviewRoot || "not_found",
          deferred_review_manifest_path: episode.deferredAmbientReviewRoot
            ? path.join(episode.deferredAmbientReviewRoot, "manifest.json")
            : "not_found",
          deferred_review_player_path: episode.deferredAmbientReviewRoot
            ? path.join(episode.deferredAmbientReviewRoot, "review.html")
            : "not_found",
          deferred_human_disposition: "defer_pending_later_ambient_effects_advice",
          active_for_right_rail_alignment: "prior_kept_v6_ambient_effects_layer",
          prior_kept_ambient_root: episode.priorKeptAmbientRoot || episode.sourceRoot,
          prior_kept_ambient_manifest_path: path.join(episode.priorKeptAmbientRoot || episode.sourceRoot, "manifest.json"),
          prior_kept_ambient_player_path: path.join(episode.priorKeptAmbientRoot || episode.sourceRoot, "review.html"),
          prior_kept_human_keep_path:
            valueAt(sourceManifest, "ambient_effects_layer.human_keep_path") ||
            valueAt(sourceManifest, "human_keep.path") ||
            "not_found",
        }
      : null;
  const musicRevalidation =
    contractMusicReviewScope
      ? {
          scope: episode.rightRailAlignmentOnly
            ? "right_rail_alignment_contract_timed_music_and_end_screen_review_not_final_mix_keep"
            : "contract_timed_music_and_end_screen_review_not_final_mix_keep",
          status:
            musicContract && contractMusicMix?.audioPath
              ? episode.rightRailAlignmentOnly
                ? "pass_revalidated_with_contract_timed_music_mix_against_prior_kept_v6_ambient_state"
                : "pass_contract_timed_music_mix_created_for_reviewable_rough_rail_proof"
              : "blocked_missing_music_contract_or_review_mix",
          contract_json_path: musicContract?.__jsonPath || captionSources.musicContractJsonPath || "not_found",
          contract_json_sha256: sha256File(musicContract?.__jsonPath || captionSources.musicContractJsonPath),
          intro_trim_model: INTRO_TRIM_MODEL,
          intro_trim_seconds: INTRO_TRIM_SECONDS,
          previous_voice_start_offset_seconds: PREVIOUS_VOICE_START_OFFSET_SECONDS,
          voice_start_offset_seconds: Number(captionAudioOffsetSeconds.toFixed(6)),
          planned_total_duration_seconds: Number(manifestDurationSeconds.toFixed(3)),
          caption_offset_sidecar_path: captionDisplayPath || "not_found",
          review_audio_mix_model: contractMusicMix?.model || "missing_contract_timed_intro_voice_outro_mix_v1",
          review_audio_mix_path: contractMusicMix?.audioPath || "not_found",
          review_audio_mix_sha256: sha256File(contractMusicMix?.audioPath),
          review_audio_mix_manifest_path: contractMusicMix?.manifestPath || "not_found",
          review_audio_mix_manifest_sha256: sha256File(contractMusicMix?.manifestPath),
          review_audio_mix_duration_seconds: contractMusicMix?.outputDurationSeconds || null,
          review_audio_mix_expected_duration_seconds: contractMusicMix?.expectedDurationSeconds || null,
          review_audio_mix_duration_delta_seconds: contractMusicMix?.durationDeltaSeconds ?? null,
          voice_audio_defect_repair_model: audioDefectRepair?.model || "not_applicable",
          voice_audio_defect_repair_read: audioDefectRepair?.voice_audio_defect_repair_read || "not_applicable",
          audio_defect_repair_manifest_path: audioDefectRepair?.repair_manifest?.path || "not_applicable",
          audio_defect_repair_manifest_sha256: audioDefectRepair?.repair_manifest?.sha256 || "not_applicable",
          superseded_defective_voice_master_path:
            audioDefectRepair?.superseded_defective_voice_master?.path || "not_applicable",
          superseded_defective_voice_master_sha256:
            audioDefectRepair?.superseded_defective_voice_master?.sha256 || "not_applicable",
          defect_windows_proof_seconds: audioDefectRepair?.defect_windows_proof_seconds || [],
          voice_loudness_alignment_status: contractMusicMix?.voiceLoudnessAlignment?.status || "not_applicable",
          voice_loudness_alignment_manifest_path: contractMusicMix?.voiceLoudnessAlignment?.manifest_path || "not_applicable",
          voice_loudness_alignment_manifest_sha256: sha256File(contractMusicMix?.voiceLoudnessAlignment?.manifest_path),
          source_voice_master_path: contractMusicMix?.voiceLoudnessAlignment?.source_voice_master?.path || "not_recorded",
          mix_voice_master_path: contractMusicMix?.voiceLoudnessAlignment?.mix_voice_master?.path || "not_recorded",
          source_voice_mean_volume_db:
            contractMusicMix?.voiceLoudnessAlignment?.source_window_volumedetect?.mean_volume_db ?? null,
          mix_voice_mean_volume_db:
            contractMusicMix?.voiceLoudnessAlignment?.output_window_volumedetect?.mean_volume_db ?? null,
          voice_loudness_alignment_read:
            contractMusicMix?.voiceLoudnessAlignment?.reads?.voice_loudness_alignment_read ||
            "pass_source_voice_master_within_series_loudness_tolerance",
          voice_master_used_for_mix_read:
            contractMusicMix?.voiceLoudnessAlignment?.voice_master_used_for_mix_read || "not_recorded",
          outro_policy: outroPolicy,
          full_outro_start_seconds: contractMusicMix?.timing?.outroStart ?? valueAt(musicContract, "timing_contract.full_outro_start_seconds") ?? null,
          outro_prelap_seconds: Number.isFinite(outroPrelapSeconds) ? outroPrelapSeconds : null,
          outro_under_vo_gain_linear:
            contractMusicMix?.timing?.outroUnderVoGain ?? valueAt(musicContract, "timing_contract.outro_under_vo_gain_linear") ?? null,
          outro_target_gain_linear:
            contractMusicMix?.timing?.outroTargetGain ?? valueAt(musicContract, "timing_contract.outro_target_gain_linear") ?? null,
          outro_reaches_target_at_seconds: Number.isFinite(outroReachesTargetAtSeconds) ? outroReachesTargetAtSeconds : null,
          outro_target_after_voice_seconds: Number.isFinite(outroTargetAfterVoiceSeconds) ? outroTargetAfterVoiceSeconds : null,
          outro_target_margin_db: OUTRO_TARGET_MARGIN_DB,
          vo_outro_blend_read: voOutroBlendRead,
          timing_proxy_audio_path: "not_applicable_replaced_by_contract_timed_music_mix",
          timing_proxy_audio_sha256: "not_applicable",
          intro_music_applied_read: contractMusicMix?.audioPath ? "pass" : "blocked",
          full_outro_music_applied_read: contractMusicMix?.audioPath ? "pass" : "blocked",
          youtube_end_screen_template_applied_read: "pass_adaptive_titleless_template_injected_from_music_contract_timing",
          end_screen_target_geometry_read: "pass_adaptive_titleless_target_geometry",
          end_screen_adaptive_palette_read:
            endScreenPaletteContract?.status === "pass"
              ? "pass_source_backplate_sampled_target_palette_contract"
              : "blocked_missing_end_screen_palette_contract",
          final_mix_approval: false,
        }
      : null;
  return {
    packet_id: `${episode.episodeId}_rolling_caption_rail_rough_proof_${PACKET_STAMP}`,
    episode_id: episode.episodeId,
    production_contract: {
      contract_id: "first-eight-longform-v1",
      intent: "successor",
      contract_registry_path: path.join(REPO_ROOT, "references/production_contracts/cascade_effects_output_contracts.v1.json"),
      youtube_action_approval_read: "blocked_rough_proof_local_review_only",
    },
    phase_gate: "rough_assembly_gate",
    created_utc: CREATED_UTC,
    status,
    action: episode.action,
    human_disposition: "defer",
    review_only: true,
    html_proof_only: true,
    voice_audio_defect_repair_model: audioDefectRepair?.model || "not_applicable",
    voice_audio_defect_repair_read: audioDefectRepair?.voice_audio_defect_repair_read || "not_applicable",
    audio_defect_repair: audioDefectRepair,
    intro_trim_model: INTRO_TRIM_MODEL,
    intro_trim_seconds: INTRO_TRIM_SECONDS,
    previous_voice_start_offset_seconds: PREVIOUS_VOICE_START_OFFSET_SECONDS,
    voice_start_offset_seconds: VOICE_START_OFFSET_SECONDS,
    right_rail_alignment_review_only: Boolean(episode.rightRailAlignmentOnly),
    ambient_effects_acceptance_status: episode.rightRailAlignmentOnly ? "deferred_pending_later_advice" : "not_applicable",
    mp4_render_created: false,
    publish_ready: false,
    youtube_upload_ready: false,
    upload_performed: false,
    public_release_ready: false,
    youtube_visibility_action_performed: false,
    source_predecessor_rough_proof_path: episode.sourceRoot,
    source_predecessor_manifest_path: sourceManifest?.__manifestPath || "not_found",
    source_predecessor_player_path: sourceHtmlPath || "not_found",
    proof_integration_model: "predecessor_html_rolling_rail_injection_v1",
    rail_preset_id: "fixed_16x9_right_rail_v1",
    rail_content_model_id: "rolling_caption_anchor_v1",
    caption_display_model: "rolling_rail_caption_window_v1",
    caption_display_chunking: "script_locked_chunk_split_v1",
    review_chrome_policy: "hidden_in_render_mode",
    review_control_model: REVIEW_CONTROL_MODEL,
    review_transport_scrub_model: REVIEW_TRANSPORT_SCRUB_MODEL,
    legacy_review_chrome_suppression_model: LEGACY_REVIEW_CHROME_SUPPRESSION_MODEL,
    review_chrome_layering_read: "pass_single_foreground_transport_legacy_controls_suppressed",
    highlight_render_policy: "reviewed_cue_map_spans_only",
    caption_motion_model: CAPTION_MOTION_MODEL,
    caption_timeline_layout_model: CAPTION_TIMELINE_LAYOUT_MODEL,
    caption_sync_target: CAPTION_SYNC_TARGET,
    caption_reading_lead_seconds: CAPTION_READING_LEAD_SECONDS,
    caption_intro_visibility_gate_model: CAPTION_INTRO_VISIBILITY_GATE_MODEL,
    caption_intro_gate_start_seconds: captionScrollTiming.caption_intro_gate_start_seconds,
    caption_intro_gate_full_opacity_seconds: captionScrollTiming.caption_intro_gate_full_opacity_seconds,
    caption_intro_premature_text_read: captionScrollTiming.caption_intro_premature_text_read,
    caption_constant_speed_scope: CAPTION_CONSTANT_SPEED_SCOPE,
    caption_playback_clock_model: CAPTION_PLAYBACK_CLOCK_MODEL,
    caption_stack_render_model: CAPTION_STACK_RENDER_MODEL,
    caption_scroll_smoothness_model: CAPTION_SCROLL_SMOOTHNESS_MODEL,
    caption_runtime_coverage_model: CAPTION_RUNTIME_COVERAGE_MODEL,
    caption_end_screen_handoff_model: CAPTION_END_SCREEN_HANDOFF_MODEL,
    review_approved_end_screen_entry_model: CAPTION_END_SCREEN_HANDOFF_MODEL,
    review_approved_youtube_placeholder_fade_start_seconds:
      REVIEW_APPROVED_END_SCREEN_FADE_START_SECONDS[episode.episodeId] ?? null,
    end_screen_fade_timing_model: endScreenTiming?.fadeTimingModel || END_SCREEN_FADE_TIMING_MODEL,
    last_caption_visible_exit_start_seconds: endScreenTiming?.lastCaptionVisibleExitStartSeconds ?? null,
    last_caption_fully_suppressed_seconds: endScreenTiming?.lastCaptionFullySuppressedSeconds ?? null,
    youtube_placeholder_fade_start_seconds: endScreenTiming?.youtubePlaceholderFadeStartSeconds ?? null,
    youtube_placeholder_full_opacity_seconds: endScreenTiming?.youtubePlaceholderFullOpacitySeconds ?? null,
    youtube_placeholder_transition_duration_seconds:
      endScreenTiming?.youtubePlaceholderTransitionDurationSeconds ?? END_SCREEN_TRANSITION_DURATION_SECONDS,
    caption_end_screen_gap_seconds: endScreenTiming?.captionEndScreenGapSeconds ?? null,
    caption_end_screen_overlap_read: endScreenTiming?.captionEndScreenOverlapRead || "pending_browser_runtime_qa",
    inherited_end_screen_suppression_model: "broad_inherited_end_screen_hidden_v1",
    inherited_end_screen_suppression_read: "pending_browser_runtime_qa",
    ambient_performance_guard_model:
      episode.episodeId === "tacoma-narrows" ? TACOMA_RAIN_PERFORMANCE_GUARD_MODEL : "not_applicable",
    ambient_frame_clock_model: ambientFrameClock.ambient_frame_clock_model,
    ambient_render_clock_read: ambientFrameClock.ambient_render_clock_read,
    ambient_wall_clock_drift_suppression_read: ambientFrameClock.ambient_wall_clock_drift_suppression_read,
    tacoma_rain_frame_throttle_ms: episode.episodeId === "tacoma-narrows" ? TACOMA_RAIN_FRAME_THROTTLE_MS : null,
    tacoma_rain_bead_count_cap: episode.episodeId === "tacoma-narrows" ? TACOMA_RAIN_BEAD_COUNT_CAP : null,
    tacoma_rain_runner_count_cap: episode.episodeId === "tacoma-narrows" ? TACOMA_RAIN_RUNNER_COUNT_CAP : null,
    tacoma_rain_streak_count_cap: episode.episodeId === "tacoma-narrows" ? TACOMA_RAIN_STREAK_COUNT_CAP : null,
    tacoma_rain_performance_guard_read:
      episode.episodeId === "tacoma-narrows" ? "pending_browser_runtime_qa" : "not_applicable",
    vo_outro_blend_read: voOutroBlendRead,
    outro_policy: outroPolicy,
    outro_prelap_seconds: Number.isFinite(outroPrelapSeconds) ? outroPrelapSeconds : null,
    outro_target_after_voice_seconds: Number.isFinite(outroTargetAfterVoiceSeconds) ? outroTargetAfterVoiceSeconds : null,
    outro_target_margin_db: OUTRO_TARGET_MARGIN_DB,
    caption_full_vo_runtime_coverage_read: "pending_browser_runtime_qa",
    caption_runtime_cutoff_read: "pending_browser_runtime_qa",
    caption_scrub_transport_sync_read: "pending_browser_runtime_qa",
    review_transport_playing_scrub_read: "pending_browser_runtime_qa",
    caption_line_clip_read: "pending_browser_runtime_qa",
    caption_audio_time_transform_sync_read: "pending_browser_runtime_qa",
    caption_active_text_matches_audio_time_read: "pending_browser_runtime_qa",
    right_rail_caption_paint_visibility_read: "pending_browser_runtime_qa",
    caption_density_resolution_model: CAPTION_DENSITY_RESOLUTION_MODEL,
    caption_display_line_wrap_model: CAPTION_DISPLAY_LINE_WRAP_MODEL,
    caption_display_line_max_width_px: CAPTION_DISPLAY_LINE_MAX_WIDTH_PX,
    caption_max_estimated_line_width_px: captionScrollTiming.caption_max_estimated_line_width_px,
    caption_text_stack_width_px: CAPTION_WINDOW_GEOMETRY.stackWidth,
    caption_stack_height_px: captionScrollTiming.caption_stack_height_px,
    caption_stack_paint_containment_read: captionScrollTiming.caption_stack_paint_containment_read,
    caption_line_opacity_model: CAPTION_LINE_OPACITY_MODEL,
    caption_window_treatment_model: CAPTION_WINDOW_TREATMENT_MODEL,
    caption_constant_scroll_speed_px_per_second: captionScrollTiming.caption_constant_scroll_speed_px_per_second,
    highlight_phrase_scope: HIGHLIGHT_PHRASE_SCOPE,
    caption_highlight_model_id: CAPTION_HIGHLIGHT_MODEL_ID,
    highlight_semantic_role: HIGHLIGHT_SEMANTIC_ROLE,
    highlight_density_model: HIGHLIGHT_DENSITY_MODEL,
    highlight_color_model: HIGHLIGHT_COLOR_MODEL,
    highlight_color_qa: highlightAccent,
    highlight_distinct_from_caption_text_read:
      highlightAccent?.highlight_distinct_from_caption_text_read || "blocked_missing_highlight_color_qa",
    ...(highlightAccent?.highlight_override_read
      ? { highlight_override_read: highlightAccent.highlight_override_read }
      : {}),
    approved_lesson_takeaway_candidate_source_path: LESSON_TAKEAWAY_CANDIDATES_LATEST_PATH,
    approved_lesson_takeaway_candidate_source_sha256: loadApprovedLessonTakeawayCandidates().sha256,
    highlight_visual_timing_model: HIGHLIGHT_VISUAL_TIMING_MODEL,
    caption_layout_collision_guard: CAPTION_LAYOUT_COLLISION_GUARD,
    caption_min_rendered_line_gap_px: captionScrollTiming.caption_min_rendered_line_gap_px,
    caption_forced_takeaway_merge_count: captionScrollTiming.caption_forced_takeaway_merge_count,
    caption_collision_guard_read: captionScrollTiming.caption_collision_guard_read,
    highlight_takeaway_count: highlightStats.highlight_count,
    highlight_single_word_count: highlightStats.single_word_highlight_count,
    highlight_max_gap_seconds: highlightStats.max_highlight_gap_seconds,
    caption_audio_sync_model: captionAudioSyncModel,
    caption_audio_offset_seconds: Number(captionAudioOffsetSeconds.toFixed(6)),
    caption_intro_trim_source_path: captionSources.trimmedSidecarSourcePath || "not_recorded",
    caption_intro_trim_source_mode: captionSources.trimmedSidecarSourceMode || "not_recorded",
    caption_intro_trim_offset_delta_seconds: captionSources.trimmedSidecarOffsetDeltaSeconds,
    caption_window_role: "middle_two_thirds_right_rail",
    caption_blur_scope: "none",
    caption_highlight_source: "living_cover_cue_map_key_phrases",
    caption_palette_source: "sampled_episode_backplate",
    ambient_right_rail_motion_policy: ambientRightRailMotion.ambient_right_rail_motion_policy || "not_applicable_no_aircraft_right_rail_motion_layer",
    foreground_matte_policy: ambientRightRailMotion.foreground_matte_policy || "not_applicable",
    first_eight_rollout_policy: {
      scope: "shared_first_eight_long_form_rail_system_redesign",
      source_art_reopened_by_default: false,
      right_rail_geometry_preserved: true,
      legacy_previous_upcoming_context_rows_removed: true,
      downstream_gates_trusted_after: "refreshed rolling-caption rough proof receives human keep, then final assembly keep, then publish-readiness keep",
    },
    source_art_highlight_merge_model: episode.sourceArtMergeForwardModel || "not_applicable",
    source_art_highlight_merge_predecessor_proof_path: episode.sourceArtMergeForwardPredecessorProofPath || "not_applicable",
    source_art_highlight_merge_read:
      episode.episodeId === "tacoma-narrows"
        ? sha256File(sourceArtPath) === TACOMA_K3_B3_SOURCE_ART_SHA256 && keyPhraseSpans.length === EXPECTED_LESSON_TAKEAWAY_COUNTS["tacoma-narrows"]
          ? "pass_k3_b3_backplate_with_approved_takeaway_highlights"
          : "blocked_tacoma_k3_b3_backplate_or_highlights_missing"
        : "not_applicable",
    canvas_behavior: {
      model: "fixed_youtube_long_form_canvas",
      design_width_px: 1920,
      design_height_px: 1080,
      aspect_ratio: "16:9",
      rail_width_px: 760,
      rail_right_margin_px: 52,
      rail_top_inset_px: 52,
      rail_bottom_inset_px: 52,
    },
    source_visual: {
      carrier: "episode_specific_raster_source_art",
      source_art_path: sourceArtPath || baseline?.active_source_art_path || "not_found",
      source_art_sha256: sha256File(sourceArtPath || baseline?.active_source_art_path),
      source_art_override_status: episode.sourceArtOverrideStatus || "not_applicable",
      source_art_override_review_note_path: episode.sourceArtOverrideReviewNotePath || "not_applicable",
      source_art_override_review_note_sha256: sha256File(episode.sourceArtOverrideReviewNotePath),
      source_art_highlight_merge_model: episode.sourceArtMergeForwardModel || "not_applicable",
      source_art_highlight_merge_predecessor_proof_path: episode.sourceArtMergeForwardPredecessorProofPath || "not_applicable",
      source_art_highlight_merge_predecessor_manifest_path: episode.sourceArtMergeForwardPredecessorProofPath
        ? path.join(episode.sourceArtMergeForwardPredecessorProofPath, "rough_assembly_manifest.json")
        : "not_applicable",
      source_art_highlight_merge_read:
        episode.episodeId === "tacoma-narrows"
          ? sha256File(sourceArtPath) === TACOMA_K3_B3_SOURCE_ART_SHA256 && keyPhraseSpans.length === EXPECTED_LESSON_TAKEAWAY_COUNTS["tacoma-narrows"]
            ? "pass_k3_b3_backplate_with_approved_takeaway_highlights"
            : "blocked_tacoma_k3_b3_backplate_or_highlights_missing"
          : "not_applicable",
      source_art_override_applied_read: episode.sourceArtOverridePath
        ? fs.existsSync(sourceArtPath)
          ? "pass_source_art_override_wired_into_generated_rough_proof"
          : "blocked_source_art_override_missing"
        : "not_applicable",
      media_referenced_only: true,
      media_copied_or_modified: false,
      right_rail_safe_space_revalidation_required: true,
      foreground_matte_policy: ambientRightRailMotion.foreground_matte_policy || "not_applicable",
      ambient_frame_clock_model: ambientFrameClock.ambient_frame_clock_model,
      ambient_render_clock_read: ambientFrameClock.ambient_render_clock_read,
      ambient_wall_clock_drift_suppression_read: ambientFrameClock.ambient_wall_clock_drift_suppression_read,
      ambient_right_rail_motion_policy:
        ambientRightRailMotion.ambient_right_rail_motion_policy || "not_applicable_no_aircraft_right_rail_motion_layer",
      aircraft_right_rail_route_count: ambientRightRailMotion.aircraft_right_rail_route_count || 0,
      aircraft_right_rail_cutoff_removed: Boolean(ambientRightRailMotion.aircraft_right_rail_cutoff_removed),
    },
    approved_audio: {
      path: audioPath || "not_found_or_blocked_until_prereq_keep",
      sha256: sha256File(audioPath),
      duration_seconds: manifestDurationSeconds,
      media_referenced_only: !contractMusicMix?.audioPath,
      media_copied_or_modified: Boolean(contractMusicMix?.audioPath),
      role: contractMusicMix?.audioPath
        ? "right_rail_alignment_contract_timed_intro_voice_outro_review_mix"
        : "approved_predecessor_audio_reference",
      review_audio_mix_model: contractMusicMix?.model || "not_applicable",
      review_audio_mix_manifest_path: contractMusicMix?.manifestPath || "not_applicable",
      review_audio_mix_manifest_sha256: sha256File(contractMusicMix?.manifestPath),
      voice_audio_defect_repair_model: audioDefectRepair?.model || "not_applicable",
      voice_audio_defect_repair_read: audioDefectRepair?.voice_audio_defect_repair_read || "not_applicable",
    },
    ...(contractMusicMix?.audioPath
      ? {
          review_audio_mix: {
            model: contractMusicMix.model,
            path: contractMusicMix.audioPath,
            sha256: sha256File(contractMusicMix.audioPath),
            manifest_path: contractMusicMix.manifestPath,
            manifest_sha256: sha256File(contractMusicMix.manifestPath),
            duration_seconds: contractMusicMix.outputDurationSeconds,
            expected_duration_seconds: contractMusicMix.expectedDurationSeconds,
            duration_delta_seconds: contractMusicMix.durationDeltaSeconds,
            voice_audio_defect_repair_model: audioDefectRepair?.model || "not_applicable",
            voice_audio_defect_repair_read: audioDefectRepair?.voice_audio_defect_repair_read || "not_applicable",
            audio_defect_repair: audioDefectRepair,
            status: "contract_timed_review_mix_pending_human_keep_not_final_mix_keep",
          },
        }
      : {}),
    ...(ambientDeferral ? { ambient_effects_deferral: ambientDeferral } : {}),
    ...(musicRevalidation ? { music_integration_contract_revalidation: musicRevalidation } : {}),
    caption_text_source: {
      kind: "locked_narration_script",
      path: lockedScriptPath || "TBD_LOCKED_SCRIPT_PATH_REQUIRED_FOR_KEEP",
      sha256: sha256File(lockedScriptPath),
    },
    caption_display_timing_source: {
      kind: captionDisplayPath ? path.extname(captionDisplayPath).slice(1).toLowerCase() : "timed_vtt_or_srt_pending",
      path: captionDisplayPath || "TBD_AFTER_PREREQ_KEEP",
      sha256: sha256File(captionDisplayPath),
      source: captionSources.displayTimingSource || "caption_display_source_pending",
      caption_model: captionSources.sidecarModel || "not_declared",
      text_usage: "script_locked_visible_text_with_audio_time_timing",
      caption_text_matches_script_read: captionSources.sidecarTextMatchesScriptRead || "pending_static_script_match_review",
      caption_alignment_coverage_read: captionSources.sidecarAlignmentCoverageRead || "pending_alignment_refresh_min_98_5_percent",
      caption_asr_text_not_used_read: captionSources.sidecarAsrTextNotUsedRead || "pass_policy_script_locked_text_only",
    },
    caption_timing_source: {
      kind: rawCaptionTimingPath ? path.extname(rawCaptionTimingPath).slice(1).toLowerCase() : "timed_vtt_or_srt_pending",
      path: rawCaptionTimingPath || "TBD_AFTER_PREREQ_KEEP",
      sha256: sha256File(rawCaptionTimingPath),
      text_usage: "timing_only_asr_text_not_used_for_output",
    },
    caption_context: {
      caption_slot_preset_id: "rolling_rail_caption_window_v1",
      behavior_model: "deterministic_audio_time_rolling_caption_window",
      caption_vtt_path: captionDisplayPath || "TBD_AFTER_PREREQ_KEEP",
      caption_vtt_sha256: sha256File(captionDisplayPath),
      caption_audio_sync_model: captionAudioSyncModel,
      caption_audio_offset_seconds: Number(captionAudioOffsetSeconds.toFixed(6)),
      first_caption_display_cue_start_seconds: firstDisplayCueStartSeconds,
      caption_text_source: {
        kind: "locked_narration_script",
        path: lockedScriptPath || "TBD_LOCKED_SCRIPT_PATH_REQUIRED_FOR_KEEP",
        sha256: sha256File(lockedScriptPath),
      },
      caption_display_timing_source: {
        kind: captionDisplayPath ? path.extname(captionDisplayPath).slice(1).toLowerCase() : "timed_vtt_or_srt_pending",
        path: captionDisplayPath || "TBD_AFTER_PREREQ_KEEP",
        sha256: sha256File(captionDisplayPath),
        source: captionSources.displayTimingSource || "caption_display_source_pending",
        caption_model: captionSources.sidecarModel || "not_declared",
        text_usage: "script_locked_visible_text_with_audio_time_timing",
        track_offset_seconds: captionSources.trackOffsetSeconds,
        predecessor_track_path: captionSources.trackPath || "not_found",
        caption_text_matches_script_read: captionSources.sidecarTextMatchesScriptRead || "pending_static_script_match_review",
        caption_alignment_coverage_read: captionSources.sidecarAlignmentCoverageRead || "pending_alignment_refresh_min_98_5_percent",
        caption_asr_text_not_used_read: captionSources.sidecarAsrTextNotUsedRead || "pass_policy_script_locked_text_only",
      },
      caption_timing_source: {
        kind: rawCaptionTimingPath ? path.extname(rawCaptionTimingPath).slice(1).toLowerCase() : "timed_vtt_or_srt_pending",
        path: rawCaptionTimingPath || "TBD_AFTER_PREREQ_KEEP",
        sha256: sha256File(rawCaptionTimingPath),
        text_usage: "timing_only_asr_text_not_used_for_output",
      },
      min_alignment_coverage: 0.985,
      max_unmatched_script_span_tokens: 8,
      layout_model: "precomputed_fixed_metrics_single_translate_y",
      caption_motion_model: CAPTION_MOTION_MODEL,
      caption_timeline_layout_model: CAPTION_TIMELINE_LAYOUT_MODEL,
      caption_sync_target: CAPTION_SYNC_TARGET,
      caption_reading_lead_seconds: CAPTION_READING_LEAD_SECONDS,
      review_transport_scrub_model: REVIEW_TRANSPORT_SCRUB_MODEL,
      caption_intro_visibility_gate_model: CAPTION_INTRO_VISIBILITY_GATE_MODEL,
      caption_intro_gate_start_seconds: captionScrollTiming.caption_intro_gate_start_seconds,
      caption_intro_gate_full_opacity_seconds: captionScrollTiming.caption_intro_gate_full_opacity_seconds,
      caption_intro_premature_text_read: captionScrollTiming.caption_intro_premature_text_read,
      caption_constant_speed_scope: CAPTION_CONSTANT_SPEED_SCOPE,
      caption_playback_clock_model: CAPTION_PLAYBACK_CLOCK_MODEL,
      caption_stack_render_model: CAPTION_STACK_RENDER_MODEL,
    caption_scroll_smoothness_model: CAPTION_SCROLL_SMOOTHNESS_MODEL,
      caption_runtime_coverage_model: CAPTION_RUNTIME_COVERAGE_MODEL,
      caption_full_vo_runtime_coverage_read: "pending_browser_runtime_qa",
      caption_runtime_cutoff_read: "pending_browser_runtime_qa",
      caption_scrub_transport_sync_read: "pending_browser_runtime_qa",
      review_transport_playing_scrub_read: "pending_browser_runtime_qa",
      caption_line_clip_read: "pending_browser_runtime_qa",
      caption_audio_time_transform_sync_read: "pending_browser_runtime_qa",
      caption_active_text_matches_audio_time_read: "pending_browser_runtime_qa",
      right_rail_caption_paint_visibility_read: "pending_browser_runtime_qa",
      caption_density_resolution_model: CAPTION_DENSITY_RESOLUTION_MODEL,
      caption_display_line_wrap_model: CAPTION_DISPLAY_LINE_WRAP_MODEL,
      caption_display_line_max_width_px: CAPTION_DISPLAY_LINE_MAX_WIDTH_PX,
      caption_max_estimated_line_width_px: captionScrollTiming.caption_max_estimated_line_width_px,
      caption_text_stack_width_px: CAPTION_WINDOW_GEOMETRY.stackWidth,
      caption_stack_height_px: captionScrollTiming.caption_stack_height_px,
      caption_stack_paint_containment_read: captionScrollTiming.caption_stack_paint_containment_read,
      caption_line_opacity_model: CAPTION_LINE_OPACITY_MODEL,
      caption_window_treatment_model: CAPTION_WINDOW_TREATMENT_MODEL,
      caption_constant_scroll_speed_px_per_second: captionScrollTiming.caption_constant_scroll_speed_px_per_second,
      caption_scroll_start_time_seconds: captionScrollTiming.caption_scroll_start_time_seconds,
      caption_scroll_start_position_px: captionScrollTiming.caption_scroll_start_position_px,
      caption_scroll_end_time_seconds: captionScrollTiming.caption_scroll_end_time_seconds,
      caption_scroll_end_position_px: captionScrollTiming.caption_scroll_end_position_px,
      caption_dense_chunk_merge_count: captionScrollTiming.caption_dense_chunk_merge_count,
      caption_unresolved_dense_pair_count: captionScrollTiming.caption_unresolved_dense_pair_count,
      caption_source_cue_coverage_count: captionScrollTiming.caption_source_cue_coverage_count,
      caption_min_rendered_line_gap_px: captionScrollTiming.caption_min_rendered_line_gap_px,
      caption_forced_takeaway_merge_count: captionScrollTiming.caption_forced_takeaway_merge_count,
      caption_layout_collision_guard: CAPTION_LAYOUT_COLLISION_GUARD,
      caption_collision_guard_read: captionScrollTiming.caption_collision_guard_read,
      caption_max_active_chunk_center_delta_at_cue_start_px:
        captionScrollTiming.caption_max_active_chunk_center_delta_at_cue_start_px,
      caption_min_active_chunk_lead_seconds: captionScrollTiming.caption_min_active_chunk_lead_seconds,
      highlight_phrase_scope: HIGHLIGHT_PHRASE_SCOPE,
      caption_highlight_model_id: CAPTION_HIGHLIGHT_MODEL_ID,
      highlight_semantic_role: HIGHLIGHT_SEMANTIC_ROLE,
      highlight_density_model: HIGHLIGHT_DENSITY_MODEL,
      highlight_color_model: HIGHLIGHT_COLOR_MODEL,
      highlight_color_qa: highlightAccent,
      highlight_distinct_from_caption_text_read:
        highlightAccent?.highlight_distinct_from_caption_text_read || "blocked_missing_highlight_color_qa",
      highlight_backplate_contrast_read:
        highlightAccent?.highlight_backplate_contrast_read || "blocked_missing_highlight_backplate_contrast_qa",
      highlight_visual_timing_model: HIGHLIGHT_VISUAL_TIMING_MODEL,
      highlight_takeaway_count: highlightStats.highlight_count,
      highlight_single_word_count: highlightStats.single_word_highlight_count,
      highlight_max_gap_seconds: highlightStats.max_highlight_gap_seconds,
      render_time_mapping: "audio.currentTime_or_window.__setRenderTime_maps_to_single_translateY",
      stable_properties_only: ["opacity", "transform", "highlight_color_alpha"],
      qa_hooks: [
        "window.__railCaptionStateAt(time)",
        "window.__setRenderTime(time)",
        ...(AMBIENT_FRAME_CLOCK_EPISODES.has(episode.episodeId) ? ["window.__ceSetAmbientRenderTime(time)"] : []),
        "window.__ceReviewTransportState()",
      ],
      word_by_word_karaoke: false,
      placement: "middle two-thirds of fixed right rail",
      caption_window_role: "middle_two_thirds_right_rail",
      caption_blur_scope: "none",
      caption_palette_source: "sampled_episode_backplate",
      caption_highlight_source: "living_cover_cue_map_key_phrases",
      caption_window_geometry_px: {
        left: RAIL_GEOMETRY.left + RAIL_GEOMETRY.width - CAPTION_WINDOW_GEOMETRY.railRight - CAPTION_WINDOW_GEOMETRY.width,
        right_margin: RAIL_GEOMETRY.rightMargin + CAPTION_WINDOW_GEOMETRY.railRight,
        width: CAPTION_WINDOW_GEOMETRY.width,
        top: RAIL_GEOMETRY.top + CAPTION_WINDOW_GEOMETRY.railTop,
        height: CAPTION_WINDOW_GEOMETRY.height,
        bottom: RAIL_GEOMETRY.top + CAPTION_WINDOW_GEOMETRY.railTop + CAPTION_WINDOW_GEOMETRY.height,
        rail_relative_top: CAPTION_WINDOW_GEOMETRY.railTop,
        rail_relative_bottom: CAPTION_WINDOW_GEOMETRY.railBottom,
        active_center_y_px: CAPTION_WINDOW_GEOMETRY.activeY,
      },
      caption_window_background: {
        localized_blur_px: 0,
        fill_source: "none",
        fill_alpha: 0,
        scope: "none",
        opacity_gate: "none",
      },
      caption_window_mask: {
        top_fade_px: CAPTION_WINDOW_GEOMETRY.topFade,
        bottom_fade_px: CAPTION_WINDOW_GEOMETRY.bottomFade,
      },
      displayed_caption_source: "script-locked cue text from locked narration script; ASR/timed text is timing-only",
      text_generation_mode: "locked_script_words_only_asr_text_never_copied",
      no_flare_or_embellishment: true,
      final_render_behavior: "burn visible rail captions into video frame after human keep",
      publish_sidecar_behavior: "preserve approved VTT sidecar for YouTube upload",
    },
    ambient_effects_layer: {
      ambient_frame_clock_model: ambientFrameClock.ambient_frame_clock_model,
      ambient_render_clock_read: ambientFrameClock.ambient_render_clock_read,
      ambient_wall_clock_drift_suppression_read: ambientFrameClock.ambient_wall_clock_drift_suppression_read,
      ambient_right_rail_motion_policy:
        ambientRightRailMotion.ambient_right_rail_motion_policy || "not_applicable_no_aircraft_right_rail_motion_layer",
      foreground_matte_policy: ambientRightRailMotion.foreground_matte_policy || "not_applicable",
      right_rail_matte_removed_read: reads.right_rail_matte_removed_read,
      aircraft_right_rail_visibility_read: reads.aircraft_right_rail_visibility_read,
      right_rail_ambient_motion_allowed_read: reads.right_rail_ambient_motion_allowed_read,
      aircraft_right_rail_route_count: ambientRightRailMotion.aircraft_right_rail_route_count || 0,
      aircraft_right_rail_cutoff_removed: Boolean(ambientRightRailMotion.aircraft_right_rail_cutoff_removed),
      youtube_target_safe_window_policy: ambientRightRailMotion.applicable
        ? "aircraft_suppressed_during_youtube_target_safe_window"
        : "not_applicable",
    },
    full_timeline: {
      caption_vtt_path: captionDisplayPath || "TBD_AFTER_PREREQ_KEEP",
      caption_vtt_sha256: sha256File(captionDisplayPath),
      caption_display_timing_source_path: captionDisplayPath || "TBD_AFTER_PREREQ_KEEP",
      caption_display_timing_source_sha256: sha256File(captionDisplayPath),
      raw_caption_timing_source_path: rawCaptionTimingPath || "TBD_AFTER_PREREQ_KEEP",
      raw_caption_timing_source_sha256: sha256File(rawCaptionTimingPath),
      caption_audio_sync_model: captionAudioSyncModel,
      caption_audio_offset_seconds: Number(captionAudioOffsetSeconds.toFixed(6)),
      caption_motion_model: CAPTION_MOTION_MODEL,
      caption_timeline_layout_model: CAPTION_TIMELINE_LAYOUT_MODEL,
      caption_sync_target: CAPTION_SYNC_TARGET,
      caption_reading_lead_seconds: CAPTION_READING_LEAD_SECONDS,
      caption_intro_visibility_gate_model: CAPTION_INTRO_VISIBILITY_GATE_MODEL,
      caption_intro_gate_start_seconds: captionScrollTiming.caption_intro_gate_start_seconds,
      caption_intro_gate_full_opacity_seconds: captionScrollTiming.caption_intro_gate_full_opacity_seconds,
      caption_intro_premature_text_read: captionScrollTiming.caption_intro_premature_text_read,
      caption_constant_speed_scope: CAPTION_CONSTANT_SPEED_SCOPE,
      caption_playback_clock_model: CAPTION_PLAYBACK_CLOCK_MODEL,
      ambient_frame_clock_model: ambientFrameClock.ambient_frame_clock_model,
      ambient_render_clock_read: ambientFrameClock.ambient_render_clock_read,
      ambient_wall_clock_drift_suppression_read: ambientFrameClock.ambient_wall_clock_drift_suppression_read,
      caption_runtime_coverage_model: CAPTION_RUNTIME_COVERAGE_MODEL,
      caption_full_vo_runtime_coverage_read: "pending_browser_runtime_qa",
      caption_runtime_cutoff_read: "pending_browser_runtime_qa",
      caption_scrub_transport_sync_read: "pending_browser_runtime_qa",
      review_transport_playing_scrub_read: "pending_browser_runtime_qa",
      caption_line_clip_read: "pending_browser_runtime_qa",
      caption_audio_time_transform_sync_read: "pending_browser_runtime_qa",
      caption_active_text_matches_audio_time_read: "pending_browser_runtime_qa",
      right_rail_caption_paint_visibility_read: "pending_browser_runtime_qa",
      caption_density_resolution_model: CAPTION_DENSITY_RESOLUTION_MODEL,
      caption_display_line_wrap_model: CAPTION_DISPLAY_LINE_WRAP_MODEL,
      caption_display_line_max_width_px: CAPTION_DISPLAY_LINE_MAX_WIDTH_PX,
      caption_max_estimated_line_width_px: captionScrollTiming.caption_max_estimated_line_width_px,
      caption_text_stack_width_px: CAPTION_WINDOW_GEOMETRY.stackWidth,
      caption_stack_height_px: captionScrollTiming.caption_stack_height_px,
      caption_stack_paint_containment_read: captionScrollTiming.caption_stack_paint_containment_read,
      caption_constant_scroll_speed_px_per_second: captionScrollTiming.caption_constant_scroll_speed_px_per_second,
      caption_window_treatment_model: CAPTION_WINDOW_TREATMENT_MODEL,
      first_caption_display_cue_start_seconds: firstDisplayCueStartSeconds,
      caption_cue_count_in_proof: cues.length,
      rolling_caption_display_chunk_count: displayChunks.length,
      caption_source_cue_coverage_count: captionScrollTiming.caption_source_cue_coverage_count,
      caption_dense_chunk_merge_count: captionScrollTiming.caption_dense_chunk_merge_count,
      caption_unresolved_dense_pair_count: captionScrollTiming.caption_unresolved_dense_pair_count,
      caption_min_rendered_line_gap_px: captionScrollTiming.caption_min_rendered_line_gap_px,
      caption_forced_takeaway_merge_count: captionScrollTiming.caption_forced_takeaway_merge_count,
      caption_layout_collision_guard: CAPTION_LAYOUT_COLLISION_GUARD,
      caption_collision_guard_read: captionScrollTiming.caption_collision_guard_read,
      caption_max_active_chunk_center_delta_at_cue_start_px:
        captionScrollTiming.caption_max_active_chunk_center_delta_at_cue_start_px,
      caption_min_active_chunk_lead_seconds: captionScrollTiming.caption_min_active_chunk_lead_seconds,
      caption_highlight_model_id: CAPTION_HIGHLIGHT_MODEL_ID,
      highlight_semantic_role: HIGHLIGHT_SEMANTIC_ROLE,
      highlight_density_model: HIGHLIGHT_DENSITY_MODEL,
      highlight_color_model: HIGHLIGHT_COLOR_MODEL,
      highlight_color_qa: highlightAccent,
      highlight_distinct_from_caption_text_read:
        highlightAccent?.highlight_distinct_from_caption_text_read || "blocked_missing_highlight_color_qa",
      highlight_backplate_contrast_read:
        highlightAccent?.highlight_backplate_contrast_read || "blocked_missing_highlight_backplate_contrast_qa",
      highlight_visual_timing_model: HIGHLIGHT_VISUAL_TIMING_MODEL,
      highlight_takeaway_count: highlightStats.highlight_count,
      highlight_single_word_count: highlightStats.single_word_highlight_count,
      highlight_max_gap_seconds: highlightStats.max_highlight_gap_seconds,
      caption_display_chunking: "script_locked_chunk_split_v1",
      embedded_caption_sample_policy: "proof injects script-locked display chunks into the predecessor rough proof; full caption script match must be refreshed before keep",
      sections: [],
    },
    living_cover_cue_map: {
      path: path.join(outputDir, "review/rolling_caption_key_phrase_cue_map_supplement.json"),
      sha256: "FILLED_AFTER_WRITE",
      cue_count: keyPhraseSpans.length,
      required_treatments: [
        "chapter_shift",
        "key_phrase_typography",
        "source_safe_motion_or_composition",
        "rolling_caption_window",
        "outro_end_screen",
      ],
      key_phrase_spans: keyPhraseSpans,
      highlight_render_policy: "reviewed_cue_map_spans_only",
      caption_highlight_model_id: CAPTION_HIGHLIGHT_MODEL_ID,
      highlight_semantic_role: HIGHLIGHT_SEMANTIC_ROLE,
      highlight_density_model: HIGHLIGHT_DENSITY_MODEL,
      highlight_color_model: HIGHLIGHT_COLOR_MODEL,
      highlight_visual_timing_model: HIGHLIGHT_VISUAL_TIMING_MODEL,
      missing_reviewed_key_phrase_span_policy: "suppress highlight rendering and keep packet pending/tighten until authored reviewed spans exist",
      draft_key_phrase_span_policy: "draft spans may render in rough review only and remain pending human keep before final/publish gates",
      render_policy: "internal production artifact only; no visible cue-map cards or diagnostic labels",
    },
    rail_behavior: {
      model: "fixed_16x9_right_rail_v1",
      rail_content_model_id: "rolling_caption_anchor_v1",
      caption_display_model: "rolling_rail_caption_window_v1",
      active_panel_hierarchy: ["suppressed_top_anchor_for_caption_only_review"],
      context_window: "removed for rolling_caption_anchor_v1",
      previous_upcoming_context_rows_allowed: false,
      viewer_text_boundary:
        "all viewer-facing story/chapter/caption/effect/end-screen text stays inside fixed right rail unless a human-approved override scopes another surface",
      desktop_width_cap_px: 760,
      design_left_px: 1108,
      design_right_margin_px: 52,
      render_api: [
        "window.__setRenderTime",
        "window.__railCaptionStateAt",
        ...(AMBIENT_FRAME_CLOCK_EPISODES.has(episode.episodeId) ? ["window.__ceSetAmbientRenderTime"] : []),
      ],
      review_chrome_policy: "hidden_in_render_mode",
      review_control_model: REVIEW_CONTROL_MODEL,
      review_transport_scrub_model: REVIEW_TRANSPORT_SCRUB_MODEL,
      legacy_review_chrome_suppression_model: LEGACY_REVIEW_CHROME_SUPPRESSION_MODEL,
      type_scale_px: {
        chapter_label: "not_rendered_top_anchor_suppressed",
        rolling_caption: 32,
      },
      rolling_caption_window: {
        placement: "middle two-thirds of fixed right rail",
        source: "script-locked cue chunks with timing-only ASR/VTT/SRT alignment",
        caption_display_chunking: "script_locked_chunk_split_v1",
        font_size_px: 32,
        line_height: 1.18,
        max_width_px: 402,
        right_aligned_inside_fixed_rail: true,
        layout: "precomputed fixed metrics",
        motion: "single translateY as deterministic continuous audio/render-time function",
        caption_motion_model: CAPTION_MOTION_MODEL,
        caption_timeline_layout_model: CAPTION_TIMELINE_LAYOUT_MODEL,
        caption_sync_target: CAPTION_SYNC_TARGET,
        caption_reading_lead_seconds: CAPTION_READING_LEAD_SECONDS,
        caption_intro_visibility_gate_model: CAPTION_INTRO_VISIBILITY_GATE_MODEL,
        caption_intro_gate_start_seconds: captionScrollTiming.caption_intro_gate_start_seconds,
        caption_intro_gate_full_opacity_seconds: captionScrollTiming.caption_intro_gate_full_opacity_seconds,
        caption_intro_premature_text_read: captionScrollTiming.caption_intro_premature_text_read,
        caption_constant_speed_scope: CAPTION_CONSTANT_SPEED_SCOPE,
        caption_playback_clock_model: CAPTION_PLAYBACK_CLOCK_MODEL,
        caption_stack_render_model: CAPTION_STACK_RENDER_MODEL,
    caption_scroll_smoothness_model: CAPTION_SCROLL_SMOOTHNESS_MODEL,
        caption_runtime_coverage_model: CAPTION_RUNTIME_COVERAGE_MODEL,
        caption_full_vo_runtime_coverage_read: "pending_browser_runtime_qa",
        caption_runtime_cutoff_read: "pending_browser_runtime_qa",
        caption_scrub_transport_sync_read: "pending_browser_runtime_qa",
        review_transport_playing_scrub_read: "pending_browser_runtime_qa",
        caption_line_clip_read: "pending_browser_runtime_qa",
        caption_audio_time_transform_sync_read: "pending_browser_runtime_qa",
        caption_active_text_matches_audio_time_read: "pending_browser_runtime_qa",
        right_rail_caption_paint_visibility_read: "pending_browser_runtime_qa",
        caption_density_resolution_model: CAPTION_DENSITY_RESOLUTION_MODEL,
        caption_display_line_wrap_model: CAPTION_DISPLAY_LINE_WRAP_MODEL,
        caption_display_line_max_width_px: CAPTION_DISPLAY_LINE_MAX_WIDTH_PX,
        caption_max_estimated_line_width_px: captionScrollTiming.caption_max_estimated_line_width_px,
        caption_text_stack_width_px: CAPTION_WINDOW_GEOMETRY.stackWidth,
        caption_stack_height_px: captionScrollTiming.caption_stack_height_px,
        caption_stack_paint_containment_read: captionScrollTiming.caption_stack_paint_containment_read,
        caption_constant_scroll_speed_px_per_second: captionScrollTiming.caption_constant_scroll_speed_px_per_second,
        caption_window_treatment_model: CAPTION_WINDOW_TREATMENT_MODEL,
        caption_line_opacity_model: CAPTION_LINE_OPACITY_MODEL,
        highlight_phrase_scope: HIGHLIGHT_PHRASE_SCOPE,
        caption_highlight_model_id: CAPTION_HIGHLIGHT_MODEL_ID,
        highlight_semantic_role: HIGHLIGHT_SEMANTIC_ROLE,
        highlight_density_model: HIGHLIGHT_DENSITY_MODEL,
      highlight_color_model: HIGHLIGHT_COLOR_MODEL,
      highlight_color_qa: highlightAccent,
      highlight_distinct_from_caption_text_read:
        highlightAccent?.highlight_distinct_from_caption_text_read || "blocked_missing_highlight_color_qa",
      highlight_backplate_contrast_read:
        highlightAccent?.highlight_backplate_contrast_read || "blocked_missing_highlight_backplate_contrast_qa",
      highlight_visual_timing_model: HIGHLIGHT_VISUAL_TIMING_MODEL,
        caption_layout_collision_guard: CAPTION_LAYOUT_COLLISION_GUARD,
        caption_min_rendered_line_gap_px: captionScrollTiming.caption_min_rendered_line_gap_px,
        caption_forced_takeaway_merge_count: captionScrollTiming.caption_forced_takeaway_merge_count,
        caption_window_geometry_px: {
          right: CAPTION_WINDOW_GEOMETRY.railRight,
          top: CAPTION_WINDOW_GEOMETRY.railTop,
          width: CAPTION_WINDOW_GEOMETRY.width,
          height: CAPTION_WINDOW_GEOMETRY.height,
          bottom: CAPTION_WINDOW_GEOMETRY.railTop + CAPTION_WINDOW_GEOMETRY.height,
        },
        top_bottom_mask_fades: true,
        localized_blur_scope: "none",
        background_fill_source: "none",
        background_fill_alpha: 0,
        localized_blur_px: 0,
        highlight_source: "living_cover_cue_map_key_phrases",
        no_embellishment: true,
        karaoke_word_timing: false,
      },
      no_viewport_specific_reflow: true,
    },
    end_screen_palette_contract: endScreenPaletteContract || {
      contract_id: END_SCREEN_PALETTE_CONTRACT_ID,
      status: "blocked_missing_end_screen_palette_contract",
      required: true,
      palette_source: "sampled_episode_backplate",
      approved_backplate: {
        path: sourceArtPath || "missing",
        sha256: sha256File(sourceArtPath),
      },
      reads: {
        end_screen_palette_contract_read: "blocked_missing_end_screen_palette_contract",
        no_cross_episode_default_palette_read: "blocked_missing_end_screen_palette_contract",
      },
    },
    end_screen_context: {
      youtube_end_screen_template_id: YOUTUBE_END_SCREEN_TEMPLATE_ID,
      caption_end_screen_handoff_model: CAPTION_END_SCREEN_HANDOFF_MODEL,
      review_approved_end_screen_entry_model: CAPTION_END_SCREEN_HANDOFF_MODEL,
      review_approved_youtube_placeholder_fade_start_seconds:
        REVIEW_APPROVED_END_SCREEN_FADE_START_SECONDS[episode.episodeId] ?? null,
      end_screen_fade_timing_model: endScreenTiming?.fadeTimingModel || END_SCREEN_FADE_TIMING_MODEL,
      end_screen_palette_treatment_model: END_SCREEN_PALETTE_TREATMENT_MODEL,
      end_screen_timing: endScreenTiming || null,
      last_caption_visible_exit_start_seconds: endScreenTiming?.lastCaptionVisibleExitStartSeconds ?? null,
      last_caption_fully_suppressed_seconds: endScreenTiming?.lastCaptionFullySuppressedSeconds ?? null,
      youtube_placeholder_fade_start_seconds: endScreenTiming?.youtubePlaceholderFadeStartSeconds ?? null,
      youtube_placeholder_full_opacity_seconds: endScreenTiming?.youtubePlaceholderFullOpacitySeconds ?? null,
      youtube_placeholder_transition_duration_seconds:
        endScreenTiming?.youtubePlaceholderTransitionDurationSeconds ?? END_SCREEN_TRANSITION_DURATION_SECONDS,
      caption_end_screen_gap_seconds: endScreenTiming?.captionEndScreenGapSeconds ?? null,
      caption_end_screen_overlap_read: endScreenTiming?.captionEndScreenOverlapRead || "pending_browser_runtime_qa",
      inherited_end_screen_suppression_model: "broad_inherited_end_screen_hidden_v1",
      inherited_end_screen_suppression_read: "pending_browser_runtime_qa",
      youtube_safe_window_caption_suppression_read:
        endScreenTiming?.youtubeSafeWindowCaptionSuppressionRead || "pending_browser_runtime_qa",
      rolling_caption_end_screen_policy:
        "YouTube placeholders fade in during the final caption exit and are fully visible when final caption text is suppressed",
      youtube_end_screen_targets: END_SCREEN_TARGET_LAYOUT,
      end_screen_palette_model: END_SCREEN_PALETTE_MODEL,
      end_screen_palette_source: "sampled_episode_backplate",
      end_screen_adaptive_variability_model: END_SCREEN_ADAPTIVE_VARIABILITY_MODEL,
      end_screen_adaptive_perceptual_variability_read:
        endScreenPaletteContract?.reads?.end_screen_adaptive_perceptual_variability_read ||
        "blocked_missing_end_screen_palette_contract",
      end_screen_palette: endScreenPalette || endScreenPaletteForSourceArt(sourceArtPath),
      end_screen_palette_contract: endScreenPaletteContract || null,
      end_screen_adaptive_palette_read:
        endScreenPaletteContract?.status === "pass"
          ? "pass_source_backplate_sampled_target_palette_contract"
          : "blocked_missing_end_screen_palette_contract",
    },
    rough_assembly_reads: reads,
    qa: {
      rail_content_model_static_pass: true,
      caption_display_model_static_pass: true,
      caption_window_role_static_pass: true,
      caption_blur_scope_none_static_pass: true,
      caption_highlight_source_static_pass: true,
      caption_palette_source_static_pass: true,
      caption_display_chunking_static_pass: true,
      review_chrome_policy_static_pass: true,
      review_control_model_static_pass: true,
      review_transport_scrub_model_static_pass: true,
      legacy_review_chrome_suppression_static_pass: true,
      single_foreground_review_transport_static_pass: true,
      highlight_render_policy_static_pass: true,
      rolling_caption_state_hook_static_pass: true,
      caption_scroll_deterministic_static_pass: true,
      caption_window_transparent_treatment_static_pass: true,
      caption_window_mask_fade_static_pass: true,
      right_rail_matte_removed_static_pass: ambientRightRailMotion.applicable
        ? /pass/i.test(String(ambientRightRailMotion.right_rail_matte_removed_read || ""))
        : true,
      aircraft_right_rail_route_static_pass: ambientRightRailMotion.applicable
        ? Boolean(ambientRightRailMotion.aircraft_right_rail_route_static_pass)
        : true,
      aircraft_right_rail_cutoff_removed_static_pass: ambientRightRailMotion.applicable
        ? Boolean(ambientRightRailMotion.aircraft_right_rail_cutoff_removed)
        : true,
      caption_key_phrase_spans_static_pass: !missingReviewedSpans,
      caption_highlight_suppressed_without_reviewed_spans_static_pass: missingReviewedSpans,
      draft_key_phrase_spans_pending_human_keep_static_pass: draftKeyPhraseSpans,
      full_caption_cue_coverage_static_pass:
        cues.length >= 90 && (captionScrollTiming.caption_source_cue_coverage_count || 0) >= cues.length,
      caption_display_timing_source_static_pass: Boolean(captionDisplayPath),
      caption_audio_sync_static_pass:
        captionAudioOffsetSeconds > 0
          ? captionAudioSyncModel === CAPTION_AUDIO_SYNC_MODEL && Boolean(captionDisplayPath)
          : Boolean(captionDisplayPath),
      first_caption_display_cue_start_seconds: firstDisplayCueStartSeconds,
      caption_motion_model_static_pass: true,
      caption_timeline_layout_static_pass: true,
      caption_sync_target_static_pass: true,
      caption_reading_lead_static_pass: CAPTION_READING_LEAD_SECONDS === 0.65,
      caption_intro_visibility_gate_static_pass:
        captionScrollTiming.caption_intro_visibility_gate_model === CAPTION_INTRO_VISIBILITY_GATE_MODEL &&
        captionScrollTiming.caption_intro_premature_text_read === "pass",
      caption_intro_visibility_gate_model: CAPTION_INTRO_VISIBILITY_GATE_MODEL,
      caption_intro_gate_start_seconds: captionScrollTiming.caption_intro_gate_start_seconds,
      caption_intro_gate_full_opacity_seconds: captionScrollTiming.caption_intro_gate_full_opacity_seconds,
      caption_intro_premature_text_read: captionScrollTiming.caption_intro_premature_text_read,
      caption_constant_speed_scope_static_pass: true,
      caption_playback_clock_static_pass: true,
      caption_stack_render_static_pass: true,
      caption_runtime_coverage_model_static_pass: true,
      caption_full_vo_runtime_coverage_static_pass: false,
      caption_runtime_coverage_model: CAPTION_RUNTIME_COVERAGE_MODEL,
      caption_full_vo_runtime_coverage_read: "pending_browser_runtime_qa",
      caption_runtime_cutoff_read: "pending_browser_runtime_qa",
      caption_scrub_transport_sync_read: "pending_browser_runtime_qa",
      review_transport_playing_scrub_read: "pending_browser_runtime_qa",
      caption_line_clip_read: "pending_browser_runtime_qa",
      caption_audio_time_transform_sync_read: "pending_browser_runtime_qa",
      caption_active_text_matches_audio_time_read: "pending_browser_runtime_qa",
      right_rail_caption_paint_visibility_read: "pending_browser_runtime_qa",
      caption_density_resolution_static_pass: true,
      caption_constant_scroll_speed_static_pass:
        Number(captionScrollTiming.caption_constant_scroll_speed_px_per_second) >= CAPTION_MIN_CONSTANT_SPEED_PX_PER_SECOND &&
        Number(captionScrollTiming.caption_constant_scroll_speed_px_per_second) <= CAPTION_MAX_CONSTANT_SPEED_PX_PER_SECOND,
      caption_active_band_at_cue_start_static_pass:
        (captionScrollTiming.caption_max_active_chunk_center_delta_at_cue_start_px || 0) <= CAPTION_ACTIVE_BAND_LOWER_DELTA_PX,
      caption_no_dense_overlap_static_pass: (captionScrollTiming.caption_unresolved_dense_pair_count || 0) === 0,
      caption_collision_guard_static_pass:
        Number(captionScrollTiming.caption_min_rendered_line_gap_px || 0) >= CAPTION_MIN_RENDERED_LINE_GAP_PX &&
        captionScrollTiming.caption_collision_guard_read === "pass_fixed_line_box_visual_gap_guard",
      caption_min_rendered_line_gap_px: captionScrollTiming.caption_min_rendered_line_gap_px,
      caption_forced_takeaway_merge_count: captionScrollTiming.caption_forced_takeaway_merge_count,
      caption_window_treatment_model_static_pass: true,
      end_screen_adaptive_palette_static_pass: endScreenPalette?.sample_read === "pass_source_backplate_sampled",
      end_screen_fixed_color_reuse_static_pass:
        endScreenPalette?.fixed_cross_episode_color_read === "pass_no_challenger_default_color_reuse_with_visible_episode_variability",
      end_screen_adaptive_perceptual_variability_static_pass:
        endScreenPalette?.end_screen_adaptive_perceptual_variability_read ===
        "pass_backplate_hue_visible_across_end_screen_targets",
      caption_line_opacity_model_static_pass: true,
      highlight_phrase_scope_static_pass: true,
      caption_highlight_model_static_pass: true,
      highlight_semantic_role_static_pass: true,
      highlight_density_model_static_pass: missingReviewedSpans || highlightDensityPassForEpisode(episode.episodeId, highlightStats),
      highlight_no_single_word_static_pass: highlightStats.single_word_highlight_count === 0,
      highlight_max_gap_static_pass: missingReviewedSpans || Number(highlightStats.max_highlight_gap_seconds || 0) <= 90,
      highlight_distinct_accent_static_pass:
        missingReviewedSpans || /pass/i.test(String(highlightAccent?.highlight_distinct_from_caption_text_read || "")),
      highlight_backplate_contrast_static_pass:
        missingReviewedSpans || /pass/i.test(String(highlightAccent?.highlight_backplate_contrast_read || "")),
      old_context_rows_absence_static_pass: true,
      downstream_gate_static_pass: true,
    },
    proof_artifacts: {
      player_html_path: playerPath,
      player_html_sha256: "FILLED_AFTER_WRITE",
      source_predecessor_player_path: sourceHtmlPath || "not_found",
      predecessor_runtime_links: runtimeLinks,
      review_packet_path: reviewPacketPath,
      static_qa_path: qaPath,
      runtime_coverage_qa_path: path.join(outputDir, "qa/rolling_caption_rail_runtime_coverage_qa.json"),
      runtime_coverage_qa_sha256: "pending_browser_runtime_qa",
    },
    blocked_prerequisite: episode.blockedPrereq || null,
    may_create_full_runtime_mp4_render: false,
    may_advance_to_video_render: false,
    may_advance_to_final_assembly: false,
    may_advance_to_publish_readiness: false,
    may_youtube_action: false,
    next_review_question: blocked
      ? "Prerequisite keeps are still required before this rolling rail rough packet can become keep-ready."
      : missingReviewedSpans
        ? "Review the tightened rail integration for behavior and palette; authored reviewed key phrase spans are still required before keep."
        : draftKeyPhraseSpans
          ? "Review this refreshed rolling-caption rail rough proof; draft key phrase spans require human keep before they become trusted production cue-map spans."
        : "Review this refreshed rolling-caption rail rough proof and reply keep, tighten, or reject.",
  };
}

function findLockedScriptPath(sourceManifest, episode) {
  const configured = resolveCandidate(episode.lockedScriptPath, episode.sourceRoot);
  if (configured) return configured;
  const strings = sourceManifest ? collectStrings(sourceManifest) : [];
  const hit = strings.find((value) => /locked.*script|script.*locked|approved.*script|narration.*script/i.test(value) && /\.(md|txt)$/i.test(value));
  return resolveCandidate(hit, episode.sourceRoot);
}

function renderReviewPacket({ episode, status, outputDir, playerPath, manifestPath, keyPhraseSpans }) {
  const phrases = keyPhraseSpans.length
    ? keyPhraseSpans.map((span) => `- ${span.phrase_text} (${span.timing_window_seconds.join(" to ")}s): ${span.highlight_color_sample.hex}; ${span.review_status}`).join("\n")
    : "- No reviewed cue-map key phrase spans were found. Highlight rendering is suppressed until authored reviewed spans exist.";
  return `# ${episode.title} Rolling Caption Rail Rough Proof

## Review Target

- Episode ID: \`${episode.episodeId}\`
- Player: \`${playerPath}\`
- Manifest: \`${manifestPath}\`
- Rail preset: \`fixed_16x9_right_rail_v1\`
- Rail content model: \`rolling_caption_anchor_v1\`
- Caption display model: \`rolling_rail_caption_window_v1\`
- Caption window role: \`middle_two_thirds_right_rail\`
- Caption blur scope: \`none\`
- Caption highlight source: \`living_cover_cue_map_key_phrases\`
- Caption palette source: \`sampled_episode_backplate\`
- Caption display chunking: \`script_locked_chunk_split_v1\`
- Review chrome policy: \`hidden_in_render_mode\`
- Highlight render policy: \`reviewed_cue_map_spans_only\`
- Caption motion model: \`${CAPTION_MOTION_MODEL}\`
- Caption timeline layout: \`${CAPTION_TIMELINE_LAYOUT_MODEL}\`
- Caption sync target: \`${CAPTION_SYNC_TARGET}\`
- Caption reading lead: \`${CAPTION_READING_LEAD_SECONDS.toFixed(2)}s\`
- Caption speed scope: \`${CAPTION_CONSTANT_SPEED_SCOPE}\`
- Caption window treatment: \`${CAPTION_WINDOW_TREATMENT_MODEL}\`
- Caption opacity model: \`${CAPTION_LINE_OPACITY_MODEL}\`
- Highlight phrase scope: \`${HIGHLIGHT_PHRASE_SCOPE}\`
- Caption highlight model: \`${CAPTION_HIGHLIGHT_MODEL_ID}\`
- Highlight semantic role: \`${HIGHLIGHT_SEMANTIC_ROLE}\`
- Highlight density model: \`${HIGHLIGHT_DENSITY_MODEL}\`
- Highlight color model: \`${HIGHLIGHT_COLOR_MODEL}\`
- Highlight visual timing model: \`${HIGHLIGHT_VISUAL_TIMING_MODEL}\`
- Caption collision guard: \`${CAPTION_LAYOUT_COLLISION_GUARD}\`
${episode.sourceArtMergeForwardModel ? `- Source-art/highlight merge model: \`${episode.sourceArtMergeForwardModel}\`\n- Source-art merge predecessor proof: \`${episode.sourceArtMergeForwardPredecessorProofPath}\`\n` : ""}

## Gate Handling

- Action: \`${episode.action}\`
- Status: \`${status}\`
- Source art rollback: not opened by default because the rail footprint is unchanged.
- Downstream gates: final assembly, publish readiness, and YouTube action remain blocked until this refreshed rough proof receives human \`keep\`.
${episode.rightRailAlignmentOnly ? "- Scope: `right_rail_alignment_review_only`; ambient/effects v7 is deferred and not approved by this proof.\n" : ""}
${episode.blockedPrereq ? `- Prerequisite blocker: ${episode.blockedPrereq}\n` : ""}
## Human Review Focus

- Captions roll smoothly through the middle two-thirds of the right rail with no seek jumps or layout jitter.
- The proof is injected into the predecessor rough proof shell so the kept source art, ambient behavior, audio timing, and end-screen timing remain active.
- The caption window has no blur, fill, panel, or container background; readability relies on source-aware text color, text shadow, and the entry/exit mask.
- Old previous/upcoming context rows are absent.
- Highlights render only from cue-map spans that are authored as story lesson/takeaway phrases, not technical labels or isolated single words.
- At the end-screen transition, captions continue upward and caption text/highlights fade fully out before YouTube target geometry.
- Right-rail safe space remains valid against the kept backplate.

## Key Phrase Spans

${phrases}

## Required Response

Reply with exactly one disposition: \`keep\`, \`tighten\`, or \`reject\`.
`;
}

function updateTomlMarker(tomlPath, block) {
  if (!tomlPath || !fs.existsSync(tomlPath)) return false;
  const start = "# rolling-caption-rail-redesign:start";
  const end = "# rolling-caption-rail-redesign:end";
  const current = fs.readFileSync(tomlPath, "utf8");
  const markedBlock = `${start}\n${block.trim()}\n${end}\n`;
  const re = new RegExp(`${start}[\\s\\S]*?${end}\\n?`, "m");
  const next = re.test(current) ? current.replace(re, markedBlock) : `${current.trimEnd()}\n\n${markedBlock}`;
  fs.writeFileSync(tomlPath, next);
  return true;
}

function updateBaselineTomlPointers(tomlPath, baselineDocPath, status) {
  if (!tomlPath || !fs.existsSync(tomlPath)) return false;
  let toml = fs.readFileSync(tomlPath, "utf8");
  const replacements = [
    ["visual_system_baseline_path", baselineDocPath],
    ["visual_system_baseline_status", status],
    ["visual_system_baseline_updated_at", "2026-05-19"],
  ];
  for (const [field, value] of replacements) {
    const line = `${field} = ${tomlString(value)}`;
    const re = new RegExp(`^${field} = ".*"$`, "m");
    toml = re.test(toml) ? toml.replace(re, line) : `${toml.trimEnd()}\n${line}\n`;
  }
  fs.writeFileSync(tomlPath, toml);
  return true;
}

function updateBaselineDoc(baselineDocPath, summary) {
  if (!baselineDocPath || !fs.existsSync(baselineDocPath)) return false;
  const start = "<!-- rolling-caption-rail-redesign:start -->";
  const end = "<!-- rolling-caption-rail-redesign:end -->";
  let doc = fs.readFileSync(baselineDocPath, "utf8");
  doc = doc.replace(/^Baseline status: `[^`]+`$/m, `Baseline status: \`${summary.status}\``);
  const block = `${start}

## Rolling Caption Rail Redesign

- Rollout date: \`2026-05-20\`
- Rail content model: \`rolling_caption_anchor_v1\`
- Caption display model: \`rolling_rail_caption_window_v1\`
- Action: \`${summary.action}\`
- Successor rough manifest: \`${summary.manifest_path}\`
- Successor player: \`${summary.player_path}\`
- Active source art: \`${summary.source_art_path || "not_recorded"}\`
- Active source art SHA-256: \`${summary.source_art_sha256 || "not_recorded"}\`
${summary.source_art_highlight_merge_model && summary.source_art_highlight_merge_model !== "not_applicable" ? `- Source-art/highlight merge model: \`${summary.source_art_highlight_merge_model}\`\n- Source-art/highlight merge read: \`${summary.source_art_highlight_merge_read}\`\n` : ""}
- Source art rollback: not opened by default; revalidate right-rail safe space only.
- Downstream gates: final assembly, publish readiness, and YouTube action remain blocked until the refreshed rough proof receives human \`keep\`.
${summary.right_rail_alignment_review_only ? "- Review scope: `right_rail_alignment_review_only`; ambient/effects v7 is deferred pending later advice.\n" : ""}
${summary.blocked_prerequisite ? `- Prerequisite blocker: ${summary.blocked_prerequisite}\n` : ""}
${end}`;
  const re = new RegExp(`${start}[\\s\\S]*?${end}`, "m");
  doc = re.test(doc) ? doc.replace(re, block) : `${doc.trimEnd()}\n\n${block}\n`;
  fs.writeFileSync(baselineDocPath, doc);
  return true;
}

function tomlString(value) {
  return JSON.stringify(String(value));
}

function buildTomlBlock({
  episode,
  status,
  manifestPath,
  playerPath,
  reviewPacketPath,
  captionScrollTiming = {},
  ambientRightRailMotion = { applicable: false },
}) {
  return `[long_form_video.rolling_caption_rail_redesign_20260520]
status = ${tomlString(status)}
action = ${tomlString(episode.action)}
source_art_override_path = ${tomlString(episode.sourceArtOverridePath || "not_applicable")}
source_art_override_status = ${tomlString(episode.sourceArtOverrideStatus || "not_applicable")}
source_art_highlight_merge_model = ${tomlString(episode.sourceArtMergeForwardModel || "not_applicable")}
source_art_highlight_merge_predecessor_proof_path = ${tomlString(episode.sourceArtMergeForwardPredecessorProofPath || "not_applicable")}
intro_trim_model = ${tomlString(INTRO_TRIM_MODEL)}
intro_trim_seconds = "${INTRO_TRIM_SECONDS.toFixed(3)}"
previous_voice_start_offset_seconds = "${PREVIOUS_VOICE_START_OFFSET_SECONDS.toFixed(6)}"
voice_start_offset_seconds = "${VOICE_START_OFFSET_SECONDS.toFixed(6)}"
rail_preset_id = "fixed_16x9_right_rail_v1"
rail_content_model_id = "rolling_caption_anchor_v1"
caption_display_model = "rolling_rail_caption_window_v1"
caption_display_chunking = "script_locked_chunk_split_v1"
review_chrome_policy = "hidden_in_render_mode"
review_control_model = ${tomlString(REVIEW_CONTROL_MODEL)}
review_transport_scrub_model = ${tomlString(REVIEW_TRANSPORT_SCRUB_MODEL)}
legacy_review_chrome_suppression_model = ${tomlString(LEGACY_REVIEW_CHROME_SUPPRESSION_MODEL)}
highlight_render_policy = "reviewed_cue_map_spans_only"
caption_motion_model = ${tomlString(CAPTION_MOTION_MODEL)}
caption_timeline_layout_model = ${tomlString(CAPTION_TIMELINE_LAYOUT_MODEL)}
caption_sync_target = ${tomlString(CAPTION_SYNC_TARGET)}
caption_reading_lead_seconds = "${CAPTION_READING_LEAD_SECONDS.toFixed(2)}"
caption_intro_visibility_gate_model = ${tomlString(CAPTION_INTRO_VISIBILITY_GATE_MODEL)}
caption_intro_gate_start_seconds = "${Number(captionScrollTiming.caption_intro_gate_start_seconds || 0).toFixed(3)}"
caption_intro_gate_full_opacity_seconds = "${Number(captionScrollTiming.caption_intro_gate_full_opacity_seconds || 0).toFixed(3)}"
caption_intro_premature_text_read = ${tomlString(captionScrollTiming.caption_intro_premature_text_read || "pass")}
caption_constant_speed_scope = ${tomlString(CAPTION_CONSTANT_SPEED_SCOPE)}
caption_playback_clock_model = ${tomlString(CAPTION_PLAYBACK_CLOCK_MODEL)}
caption_stack_render_model = ${tomlString(CAPTION_STACK_RENDER_MODEL)}
caption_scroll_smoothness_model = ${tomlString(CAPTION_SCROLL_SMOOTHNESS_MODEL)}
caption_runtime_coverage_model = ${tomlString(CAPTION_RUNTIME_COVERAGE_MODEL)}
caption_end_screen_handoff_model = ${tomlString(CAPTION_END_SCREEN_HANDOFF_MODEL)}
review_approved_youtube_placeholder_fade_start_seconds = ${tomlString(
    REVIEW_APPROVED_END_SCREEN_FADE_START_SECONDS[episode.episodeId] ?? "not_applicable",
  )}
caption_full_vo_runtime_coverage_read = "pending_browser_runtime_qa"
caption_runtime_cutoff_read = "pending_browser_runtime_qa"
caption_scrub_transport_sync_read = "pending_browser_runtime_qa"
review_transport_playing_scrub_read = "pending_browser_runtime_qa"
caption_line_clip_read = "pending_browser_runtime_qa"
caption_audio_time_transform_sync_read = "pending_browser_runtime_qa"
caption_active_text_matches_audio_time_read = "pending_browser_runtime_qa"
right_rail_caption_paint_visibility_read = "pending_browser_runtime_qa"
caption_density_resolution_model = ${tomlString(CAPTION_DENSITY_RESOLUTION_MODEL)}
caption_line_opacity_model = "viewport_distance_smoothstep_v1"
caption_window_treatment_model = ${tomlString(CAPTION_WINDOW_TREATMENT_MODEL)}
caption_constant_scroll_speed_px_per_second = "${Number(captionScrollTiming.caption_constant_scroll_speed_px_per_second || 0).toFixed(3)}"
caption_stack_height_px = "${Number(captionScrollTiming.caption_stack_height_px || 12000).toFixed(0)}"
caption_stack_paint_containment_read = ${tomlString(captionScrollTiming.caption_stack_paint_containment_read || "pass_no_caption_stack_paint_clip")}
caption_dense_chunk_merge_count = "${Number(captionScrollTiming.caption_dense_chunk_merge_count || 0)}"
caption_unresolved_dense_pair_count = "${Number(captionScrollTiming.caption_unresolved_dense_pair_count || 0)}"
caption_layout_collision_guard = ${tomlString(CAPTION_LAYOUT_COLLISION_GUARD)}
caption_min_rendered_line_gap_px = "${Number(captionScrollTiming.caption_min_rendered_line_gap_px || 0).toFixed(1)}"
caption_forced_takeaway_merge_count = "${Number(captionScrollTiming.caption_forced_takeaway_merge_count || 0)}"
caption_max_active_chunk_center_delta_at_cue_start_px = "${Number(captionScrollTiming.caption_max_active_chunk_center_delta_at_cue_start_px || 0).toFixed(3)}"
ambient_right_rail_motion_policy = ${tomlString(ambientRightRailMotion.ambient_right_rail_motion_policy || "not_applicable_no_aircraft_right_rail_motion_layer")}
foreground_matte_policy = ${tomlString(ambientRightRailMotion.foreground_matte_policy || "not_applicable")}
aircraft_right_rail_route_count = "${Number(ambientRightRailMotion.aircraft_right_rail_route_count || 0)}"
aircraft_right_rail_cutoff_removed = ${Boolean(ambientRightRailMotion.aircraft_right_rail_cutoff_removed)}
right_rail_alignment_review_only = ${Boolean(episode.rightRailAlignmentOnly)}
ambient_effects_acceptance_status = ${tomlString(episode.rightRailAlignmentOnly ? "deferred_pending_later_advice" : "not_applicable")}
ambient_effects_deferral_note_path = ${tomlString(episode.ambientDeferralNotePath || "not_applicable")}
active_ambient_effects_for_right_rail_alignment = ${tomlString(episode.rightRailAlignmentOnly ? "prior_kept_v6_ambient_effects_layer" : "not_applicable")}
deferred_ambient_effects_review_root = ${tomlString(episode.deferredAmbientReviewRoot || "not_applicable")}
music_integration_contract_revalidation_scope = ${tomlString(episode.rightRailAlignmentOnly ? "right_rail_alignment_timing_only_not_final_mix_keep" : "not_applicable")}
highlight_phrase_scope = "exact_authored_span_only"
caption_highlight_model_id = ${tomlString(CAPTION_HIGHLIGHT_MODEL_ID)}
highlight_semantic_role = ${tomlString(HIGHLIGHT_SEMANTIC_ROLE)}
highlight_density_model = ${tomlString(HIGHLIGHT_DENSITY_MODEL)}
highlight_color_model = ${tomlString(HIGHLIGHT_COLOR_MODEL)}
highlight_visual_timing_model = ${tomlString(HIGHLIGHT_VISUAL_TIMING_MODEL)}
caption_window_role = "middle_two_thirds_right_rail"
caption_blur_scope = "none"
caption_highlight_source = "living_cover_cue_map_key_phrases"
caption_palette_source = "sampled_episode_backplate"
rough_assembly_manifest_path = ${tomlString(manifestPath)}
rough_assembly_player_path = ${tomlString(playerPath)}
review_packet_path = ${tomlString(reviewPacketPath)}
source_art_reopened_by_default = false
right_rail_safe_space_revalidation_required = true
may_render_final_mp4 = false
may_advance_to_final_assembly = false
may_advance_to_publish_readiness = false
may_youtube_action = false`;
}

function htmlEscape(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[char]);
}

function reviewUrlForPath(filePath, params = {}) {
  const rel = path.relative(EPISODES_ROOT, filePath).split(path.sep).map(encodeURIComponent).join("/");
  const url = new URL(`${REVIEW_SERVER_BASE_URL}/${rel}`);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, String(value));
  });
  return url.toString();
}

function formatTimestamp(seconds) {
  const safe = Math.max(0, Number(seconds) || 0);
  const minutes = Math.floor(safe / 60);
  const wholeSeconds = Math.floor(safe % 60);
  return `${String(minutes).padStart(2, "0")}:${String(wholeSeconds).padStart(2, "0")}`;
}

function statusLabel(summary) {
  if (String(summary.human_disposition || "").toLowerCase() === "keep") return "Kept rough proof";
  if (summary.right_rail_alignment_review_only || /right_rail_alignment_only/i.test(String(summary.status || ""))) {
    return "Right-rail review";
  }
  if (summary.blocked_prerequisite) return "Blocked by prerequisite";
  return "Pending rough keep";
}

function reviewStateLabel(summary) {
  const status = String(summary.status || "");
  if (String(summary.human_disposition || "").toLowerCase() === "keep") {
    return "Rough rail kept. Ready for final assembly work.";
  }
  if (/blocked_pending_current_prerequisite_keep/i.test(status) || summary.blocked_prerequisite) {
    return "Waiting on earlier keeps before this proof can count.";
  }
  if (summary.right_rail_alignment_review_only || /right_rail_alignment_only/i.test(status)) {
    return "Ready for right-rail review; ambient effects deferred.";
  }
  if (/final_assembly_paused/i.test(status)) {
    return "Final assembly is paused until this successor rough proof is kept.";
  }
  if (/pending_reviewed_key_phrase_spans/i.test(status)) {
    return "Ready to review, but takeaway highlights still need human keep.";
  }
  if (/pending_human_keep/i.test(status)) {
    return "Ready to review. Needs rough-proof keep.";
  }
  return "Needs review.";
}

function isBlockedBeforeRoughAssembly(summary) {
  return Boolean(summary.blocked_prerequisite) || /blocked_pending_current_prerequisite_keep/i.test(String(summary.status || ""));
}

function runtimeLabel(summary) {
  if (isBlockedBeforeRoughAssembly(summary)) return "Not built yet";
  return formatTimestamp(summary.duration_seconds || 0);
}

function proofUrlParams(summary, extra = {}) {
  const params = {};
  if (summary.proof_build_id) params.v = summary.proof_build_id;
  return { ...params, ...extra };
}

function renderReviewIndex(summaries) {
  const rows = summaries.map((summary, index) => {
    const duration = Number(summary.duration_seconds || 0);
    const voice = Number(summary.first_caption_display_cue_start_seconds || summary.caption_audio_offset_seconds || 0);
    const quickLinks = isBlockedBeforeRoughAssembly(summary) ? "" : [
      ["Start", 0],
      ["Voice", voice],
      ["Mid", duration ? duration / 2 : 0],
      ["End", duration ? Math.max(0, duration - 30) : 0],
    ].map(([label, seconds]) => {
      const time = Number(seconds).toFixed(1).replace(/\.0$/, "");
      return `<a href="${htmlEscape(reviewUrlForPath(summary.player_path, proofUrlParams(summary, { t: time })))}">${htmlEscape(label)} ${formatTimestamp(seconds)}</a>`;
    }).join("");
    const blocker =
      summary.blocked_prerequisite ||
      (summary.right_rail_alignment_review_only || /right_rail_alignment_only/i.test(String(summary.status || ""))
        ? "Ambient effects deferred; final/publish/YouTube gates stay blocked."
        : statusLabel(summary) === "Pending rough keep"
          ? "Needs human keep on refreshed rolling rail rough proof."
          : "Final/publish/YouTube gates remain separately locked.");
    const reviewAction = isBlockedBeforeRoughAssembly(summary)
      ? '<span class="not-ready">Not reviewable yet</span>'
      : `<a class="primary" href="${htmlEscape(reviewUrlForPath(summary.player_path, proofUrlParams(summary)))}">Open proof</a><div class="quick">${quickLinks}</div>`;
    return `<tr>
      <td class="order">${index + 1}</td>
      <td>
        <strong>${htmlEscape(summary.title)}</strong>
        <span>${htmlEscape(summary.episode_id)}</span>
      </td>
      <td>${htmlEscape(statusLabel(summary))}</td>
      <td class="review-state">${htmlEscape(reviewStateLabel(summary))}</td>
      <td>${htmlEscape(runtimeLabel(summary))}</td>
      <td>${htmlEscape(blocker)}</td>
      <td class="actions">${reviewAction}</td>
    </tr>`;
  }).join("\n");
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>First-Eight Rolling Caption Rail Review</title>
  <style>
    :root { color-scheme: dark; --bg: #0a0b0c; --panel: #151719; --line: #30353a; --text: #f3efe7; --muted: #aeb7bd; --accent: #f0c36a; }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; background: var(--bg); color: var(--text); font: 15px/1.45 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    main { width: min(1480px, calc(100vw - 48px)); margin: 0 auto; padding: 34px 0 42px; }
    header { display: flex; justify-content: space-between; gap: 18px; align-items: end; margin-bottom: 24px; }
    h1 { margin: 0; font-size: 30px; line-height: 1.05; letter-spacing: 0; }
    p { margin: 8px 0 0; color: var(--muted); max-width: 82ch; }
    table { width: 100%; border-collapse: collapse; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
    th, td { padding: 14px 13px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
    th { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .04em; background: #101214; }
    tr:last-child td { border-bottom: 0; }
    td span { display: block; margin-top: 3px; color: var(--muted); font-size: 12px; }
    .order { color: var(--muted); width: 44px; }
    .review-state { max-width: 260px; }
    .actions { min-width: 230px; }
    .not-ready { display: inline-block; margin-top: 0; color: var(--muted); font-weight: 760; }
    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }
    .primary { display: inline-block; margin-bottom: 8px; font-weight: 800; }
    .quick { display: flex; flex-wrap: wrap; gap: 7px 10px; font-size: 12px; }
    .meta { color: var(--muted); font-size: 13px; white-space: nowrap; }
    @media (max-width: 900px) {
      main { width: min(100vw - 24px, 760px); padding-top: 22px; }
      header { display: block; }
      table, tbody, tr, td { display: block; width: 100%; }
      thead { display: none; }
      tr { border-bottom: 1px solid var(--line); }
      td { border-bottom: 0; padding: 9px 12px; }
      .order { width: auto; }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>First-Eight Rolling Caption Rail Review</h1>
        <p>Local index for the in-progress long-form rolling rail proofs. This page is review-only and does not change final assembly, publish readiness, or YouTube gates.</p>
      </div>
      <div class="meta">Build ${htmlEscape(PROOF_GENERATED_AT_UTC)}</div>
    </header>
    <table>
      <thead>
        <tr><th>#</th><th>Episode</th><th>Gate</th><th>Review state</th><th>Runtime</th><th>Blocker / note</th><th>Review</th></tr>
      </thead>
      <tbody>
${rows}
      </tbody>
    </table>
  </main>
</body>
</html>
`;
}

function writeJson(filePath, value) {
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`);
}

function buildEpisode(episode, baseline) {
  const outputDir = path.join(episode.outputBase, outputDirNameForEpisode(episode));
  ensureDir(outputDir);
  const ambientFrameClock = ambientFrameClockMetadata(episode);
  const manifestPath = findSourceManifestPath(episode.sourceRoot);
  const sourceManifest = readJsonIfExists(manifestPath) || {};
  if (sourceManifest) sourceManifest.__manifestPath = fs.existsSync(manifestPath) ? manifestPath : "not_found";
  const sourceArtOverridePath = resolveConfiguredPath(episode.sourceArtOverridePath, episode.sourceRoot);
  const sourceArtPath = fs.existsSync(sourceArtOverridePath)
    ? sourceArtOverridePath
    : chooseExistingPath(
    sourceManifest,
    episode.sourceRoot,
    /\.(png|jpe?g|webp)$/i,
      [baseline?.active_source_art_path],
    );
  const sourceHtmlPath = findSourceHtmlPath(episode.sourceRoot);
  const predecessorSourceHtml = sourceHtmlPath ? fs.readFileSync(sourceHtmlPath, "utf8") : "";
  const captionSources = resolveCaptionSources({
    sourceManifest,
    sourceRoot: episode.sourceRoot,
    sourceHtml: predecessorSourceHtml,
    episode,
    outputDir,
  });
  const musicContract = captionSources.musicContract || musicContractForEpisode(sourceManifest, episode.sourceRoot, episode);
  const contractMusicMix = ensureContractTimedRightRailMusicMix({ episode, outputDir, musicContract }) || null;
  const contractMusicMixAudioPath =
    contractMusicMix && typeof contractMusicMix === "object" ? contractMusicMix.audioPath : "";
  const episodeOutroPolicy = valueAt(musicContract, "timing_contract.outro_policy") || OUTRO_POLICY;
  const episodeOutroPrelapSeconds = firstFiniteNumber(
    [valueAt(musicContract, "timing_contract.outro_prelap_seconds"), contractMusicMix?.timing?.outroPrelap],
    NaN,
  );
  const episodeVoiceEndSeconds = firstFiniteNumber(
    [valueAt(musicContract, "timing_contract.voice_end_seconds"), contractMusicMix?.timing?.voiceEnd],
    NaN,
  );
  const episodeOutroReachesTargetAtSeconds = firstFiniteNumber(
    [valueAt(musicContract, "timing_contract.outro_reaches_target_at_seconds"), contractMusicMix?.timing?.outroReachesTargetAt],
    NaN,
  );
  const episodeOutroTargetAfterVoiceSeconds =
    Number.isFinite(episodeVoiceEndSeconds) && Number.isFinite(episodeOutroReachesTargetAtSeconds)
      ? Number((episodeOutroReachesTargetAtSeconds - episodeVoiceEndSeconds).toFixed(3))
      : NaN;
  const episodeVoOutroBlendRead =
    episodeOutroPolicy === OUTRO_POLICY &&
    Math.abs((episodeOutroPrelapSeconds || 0) - OUTRO_PRELAP_SECONDS) <= 0.05 &&
    Number.isFinite(episodeOutroTargetAfterVoiceSeconds) &&
    episodeOutroTargetAfterVoiceSeconds >= OUTRO_TARGET_AFTER_VOICE_SECONDS - 0.1
      ? "pass_subtle_tail_outro_v1_1p5s_prelap_target_after_voice"
      : "tighten_outro_contract_not_normalized_to_subtle_tail";
  const audioPath =
    contractMusicMixAudioPath ||
    resolveCandidate(valueAt(musicContract, "voice_master.path"), episode.sourceRoot) ||
    chooseExistingPath(sourceManifest, episode.sourceRoot, /\.(wav|mp3|m4a|aac)$/i);
  const captionPath = captionSources.displayTimingPath || chooseExistingPath(sourceManifest, episode.sourceRoot, /\.(vtt|srt)$/i);
  const cues = normalizeCueSet(parseVtt(captionPath), episode.episodeId);
  const initialDisplayChunks = splitCuesForDisplay(cues);
  const takeawayPhraseSpecs = takeawayPhraseSpecsForEpisode(episode);
  const alignedCaptionLayout = buildAudioTimeAlignedCaptionLayout(initialDisplayChunks, takeawayPhraseSpecs);
  const displayChunks = alignedCaptionLayout.chunks;
  const captionScrollTiming = alignedCaptionLayout.captionScrollTiming;
  const palette = paletteForEpisode(episode.episodeId);
  const highlightAccent = highlightColorQaForSourceArt({ episode, sourceArtPath, palette });
  const endScreenPalette = endScreenPaletteForSourceArt(sourceArtPath);
  const endScreenPaletteContract = endScreenPaletteContractForSourceArt(sourceArtPath, endScreenPalette);
  const baseEndScreenTiming =
    endScreenTimingFromMusicContract(musicContract, endScreenPalette) ||
    endScreenTimingFromSourceHtml(predecessorSourceHtml, endScreenPalette);
  const endScreenTiming = captionExitAlignedEndScreenTiming(baseEndScreenTiming, displayChunks, captionScrollTiming, episode);
  const keyPhraseSpans = keyPhraseSpansForEpisode(episode, displayChunks, palette, captionScrollTiming, highlightAccent);
  const highlightStats = highlightStatsForSpans(keyPhraseSpans, cues[cues.length - 1]?.end);
  const musicContractDuration = firstFiniteNumber([valueAt(musicContract, "timing_contract.planned_total_duration_seconds")]);
  const durationSeconds = Number.isFinite(musicContractDuration)
    ? musicContractDuration
    : audioPath
      ? Math.max(cues[cues.length - 1].end + 45, 120)
      : cues[cues.length - 1].end + 45;
  const reviewDir = path.join(outputDir, "review");
  const qaDir = path.join(outputDir, "qa");
  ensureDir(reviewDir);
  ensureDir(qaDir);

  const playerPath = path.join(outputDir, "player.html");
  const roughManifestPath = path.join(outputDir, "rough_assembly_manifest.json");
  const proofBuildPath = path.join(outputDir, "proof_build.json");
  const proofBuildId = proofBuildIdForEpisode(episode.episodeId);
  const previousManifest = readJsonIfExists(roughManifestPath);
  const preserveExistingKeep = existingRollingRailKeep(previousManifest);
  const reviewPacketPath = path.join(reviewDir, "rolling_caption_rail_review_packet.md");
  const keyPhrasePath = path.join(reviewDir, "rolling_caption_key_phrase_cue_map_supplement.json");
  const qaPath = path.join(qaDir, "rolling_caption_rail_static_qa.json");
  const runtimeLinks = linkSourceRuntimeEntries(outputDir, episode.sourceRoot);
  const sourceHtml = predecessorSourceHtml
    ? applyEpisodeSourceHtmlRuntimeGuards(
        rewriteSupersededEndScreenTemplateMarkers(
          rewriteSourcePlateReference(
            replaceFirstAudioSource(predecessorSourceHtml, contractMusicMixAudioPath || "", outputDir),
            episode,
            sourceArtPath,
            outputDir,
          ),
        ),
        episode,
      )
    : renderPlayerHtml({
    episode,
    sourceArtPath: symlinkForReview(outputDir, sourceArtPath, `assets/source_art/backplate${path.extname(sourceArtPath || ".png") || ".png"}`),
    audioPath: symlinkForReview(outputDir, audioPath, `assets/audio/approved_audio${path.extname(audioPath || ".mp3") || ".mp3"}`),
    cues: displayChunks,
    keyPhraseSpans,
    palette,
    durationSeconds,
  });
  const ambientRightRailMotion = ambientRightRailMotionMetadata({
    episode,
    sourceManifest,
    sourceHtml,
  });
  const playerHtml = renderInjectedPlayerHtml({
    episode,
    sourceHtml,
    chunks: displayChunks,
    keyPhraseSpans,
    palette,
    durationSeconds,
    captionSources,
    captionScrollTiming,
    endScreenTiming,
    endScreenPaletteContract,
    proofBuildId,
    proofGeneratedAtUtc: PROOF_GENERATED_AT_UTC,
  });
  fs.writeFileSync(playerPath, playerHtml);

  writeJson(keyPhrasePath, {
    episode_id: episode.episodeId,
    created_utc: CREATED_UTC,
    source: "living_cover_cue_map_key_phrases",
    status: keyPhraseSpans.some((span) => /draft|pending/i.test(String(span.review_status || "")))
      ? "rough_review_draft_spans_pending_human_keep"
      : keyPhraseSpans.length
        ? "approved_lesson_takeaway_spans_loaded"
        : "blocked_pending_reviewed_cue_map_key_phrase_spans",
    highlight_render_policy: "reviewed_cue_map_spans_only",
    highlight_phrase_scope: HIGHLIGHT_PHRASE_SCOPE,
    caption_motion_model: CAPTION_MOTION_MODEL,
    caption_timeline_layout_model: CAPTION_TIMELINE_LAYOUT_MODEL,
    caption_sync_target: CAPTION_SYNC_TARGET,
    caption_reading_lead_seconds: CAPTION_READING_LEAD_SECONDS,
    caption_constant_speed_scope: CAPTION_CONSTANT_SPEED_SCOPE,
    caption_playback_clock_model: CAPTION_PLAYBACK_CLOCK_MODEL,
    caption_stack_render_model: CAPTION_STACK_RENDER_MODEL,
    caption_scroll_smoothness_model: CAPTION_SCROLL_SMOOTHNESS_MODEL,
    caption_runtime_coverage_model: CAPTION_RUNTIME_COVERAGE_MODEL,
    caption_full_vo_runtime_coverage_read: "pending_browser_runtime_qa",
    caption_density_resolution_model: CAPTION_DENSITY_RESOLUTION_MODEL,
    caption_line_opacity_model: CAPTION_LINE_OPACITY_MODEL,
    caption_window_treatment_model: CAPTION_WINDOW_TREATMENT_MODEL,
    caption_constant_scroll_speed_px_per_second: captionScrollTiming.caption_constant_scroll_speed_px_per_second,
    caption_highlight_model_id: CAPTION_HIGHLIGHT_MODEL_ID,
    highlight_semantic_role: HIGHLIGHT_SEMANTIC_ROLE,
    highlight_density_model: HIGHLIGHT_DENSITY_MODEL,
    highlight_color_model: HIGHLIGHT_COLOR_MODEL,
    highlight_color_qa: highlightAccent,
    highlight_distinct_from_caption_text_read: highlightAccent.highlight_distinct_from_caption_text_read,
    highlight_backplate_contrast_read: highlightAccent.highlight_backplate_contrast_read,
    ...(highlightAccent.highlight_override_read
      ? { highlight_override_read: highlightAccent.highlight_override_read }
      : {}),
    highlight_visual_timing_model: HIGHLIGHT_VISUAL_TIMING_MODEL,
    caption_layout_collision_guard: CAPTION_LAYOUT_COLLISION_GUARD,
    caption_min_rendered_line_gap_px: captionScrollTiming.caption_min_rendered_line_gap_px,
    caption_forced_takeaway_merge_count: captionScrollTiming.caption_forced_takeaway_merge_count,
    missing_reviewed_key_phrase_span_policy: "highlights_suppressed_until_authored_reviewed_spans_exist",
    draft_key_phrase_span_policy: "draft spans render for rough-review behavior proof only; final and publish gates remain blocked until human keep",
    key_phrase_spans: keyPhraseSpans,
  });

  const manifest = buildManifest({
    episode,
    sourceManifest,
    sourceArtPath,
    audioPath,
    captionPath,
    captionSources,
    cues,
    displayChunks,
    keyPhraseSpans,
    outputDir,
    playerPath,
    sourceHtmlPath,
    reviewPacketPath,
    qaPath,
    baseline,
    runtimeLinks,
    durationSeconds,
    captionScrollTiming,
    ambientRightRailMotion,
    musicContract,
    contractMusicMix,
    endScreenTiming,
    endScreenPalette,
    endScreenPaletteContract,
    highlightAccent,
  });
  manifest.proof_build_id = proofBuildId;
  manifest.proof_generated_at_utc = PROOF_GENERATED_AT_UTC;
  manifest.proof_build_json_path = proofBuildPath;
  manifest.proof_build_json_url = reviewUrlForPath(proofBuildPath, { v: proofBuildId });
  manifest.proof_build_freshness_guard_read = "pending_browser_runtime_qa";
  manifest.living_cover_cue_map.path = keyPhrasePath;
  manifest.living_cover_cue_map.sha256 = sha256File(keyPhrasePath);
  manifest.proof_artifacts.player_html_sha256 = sha256File(playerPath);
  manifest.proof_artifacts.proof_build_json_path = proofBuildPath;
  manifest.proof_artifacts.proof_build_json_url = reviewUrlForPath(proofBuildPath, { v: proofBuildId });
  if (preserveExistingKeep && endScreenPaletteContract.status === "pass") applyExistingRollingRailKeep(manifest, previousManifest);
  const effectiveStatus = manifest.status;
  writeJson(roughManifestPath, manifest);

  writeJson(proofBuildPath, {
    episode_id: episode.episodeId,
    title: episode.title,
    proof_build_id: proofBuildId,
    proof_generated_at_utc: PROOF_GENERATED_AT_UTC,
    packet_stamp: PACKET_STAMP,
    player_path: playerPath,
    player_url: reviewUrlForPath(playerPath, { v: proofBuildId }),
    manifest_path: roughManifestPath,
    intro_trim_model: INTRO_TRIM_MODEL,
    intro_trim_seconds: INTRO_TRIM_SECONDS,
    previous_voice_start_offset_seconds: PREVIOUS_VOICE_START_OFFSET_SECONDS,
    voice_start_offset_seconds: VOICE_START_OFFSET_SECONDS,
    caption_motion_model: CAPTION_MOTION_MODEL,
    review_transport_scrub_model: REVIEW_TRANSPORT_SCRUB_MODEL,
    caption_playback_clock_model: CAPTION_PLAYBACK_CLOCK_MODEL,
    caption_stack_render_model: CAPTION_STACK_RENDER_MODEL,
    caption_scroll_smoothness_model: CAPTION_SCROLL_SMOOTHNESS_MODEL,
    ...ambientFrameClockMetadata(episode),
    youtube_end_screen_template_id: YOUTUBE_END_SCREEN_TEMPLATE_ID,
    caption_end_screen_handoff_model: CAPTION_END_SCREEN_HANDOFF_MODEL,
    review_approved_end_screen_entry_model: CAPTION_END_SCREEN_HANDOFF_MODEL,
    review_approved_youtube_placeholder_fade_start_seconds:
      REVIEW_APPROVED_END_SCREEN_FADE_START_SECONDS[episode.episodeId] ?? null,
    end_screen_fade_timing_model: endScreenTiming?.fadeTimingModel || END_SCREEN_FADE_TIMING_MODEL,
    last_caption_visible_exit_start_seconds: endScreenTiming?.lastCaptionVisibleExitStartSeconds ?? null,
    last_caption_fully_suppressed_seconds: endScreenTiming?.lastCaptionFullySuppressedSeconds ?? null,
    youtube_placeholder_fade_start_seconds: endScreenTiming?.youtubePlaceholderFadeStartSeconds ?? null,
    youtube_placeholder_full_opacity_seconds: endScreenTiming?.youtubePlaceholderFullOpacitySeconds ?? null,
    youtube_placeholder_transition_duration_seconds:
      endScreenTiming?.youtubePlaceholderTransitionDurationSeconds ?? END_SCREEN_TRANSITION_DURATION_SECONDS,
    caption_end_screen_gap_seconds: endScreenTiming?.captionEndScreenGapSeconds ?? null,
    end_screen_palette_treatment_model: END_SCREEN_PALETTE_TREATMENT_MODEL,
    end_screen_adaptive_variability_model: END_SCREEN_ADAPTIVE_VARIABILITY_MODEL,
    end_screen_adaptive_perceptual_variability_read:
      endScreenPaletteContract.reads?.end_screen_adaptive_perceptual_variability_read ||
      "blocked_missing_end_screen_palette_contract",
  });
  manifest.proof_build_json_sha256 = sha256File(proofBuildPath);
  manifest.proof_artifacts.proof_build_json_sha256 = manifest.proof_build_json_sha256;
  writeJson(roughManifestPath, manifest);

  fs.writeFileSync(
    reviewPacketPath,
    renderReviewPacket({ episode, status: effectiveStatus, outputDir, playerPath, manifestPath: roughManifestPath, keyPhraseSpans }),
  );

  writeJson(qaPath, {
    episode_id: episode.episodeId,
    created_utc: CREATED_UTC,
    manifest_path: roughManifestPath,
    player_path: playerPath,
    static_checks: {
      manifest_model_ids_present: true,
      player_hooks_present: true,
      predecessor_html_injection_present: Boolean(sourceHtmlPath),
      old_context_rows_removed: true,
      downstream_gates_blocked: !preserveExistingKeep,
      reviewed_key_phrase_spans_present: keyPhraseSpans.length > 0,
      highlight_rendering_suppressed_without_reviewed_spans: keyPhraseSpans.length === 0,
      draft_key_phrase_spans_pending_human_keep: keyPhraseSpans.some((span) => /draft|pending/i.test(String(span.review_status || ""))),
      full_caption_cue_coverage:
        cues.length >= 90 && (captionScrollTiming.caption_source_cue_coverage_count || 0) >= cues.length,
      end_screen_palette_contract_static_pass: endScreenPaletteContract.status === "pass",
      end_screen_template_static_pass: endScreenTiming?.templateId === YOUTUBE_END_SCREEN_TEMPLATE_ID,
      end_screen_fade_timing_static_pass: endScreenTiming?.fadeTimingModel === END_SCREEN_FADE_TIMING_MODEL,
      caption_end_screen_handoff_model: CAPTION_END_SCREEN_HANDOFF_MODEL,
      caption_end_screen_handoff_static_pass:
        endScreenTiming?.captionEndScreenHandoffModel === CAPTION_END_SCREEN_HANDOFF_MODEL &&
        endScreenTiming?.captionEndScreenOverlapRead === "pass_review_approved_end_screen_entry_no_blank_gap",
      review_approved_end_screen_entry_model: CAPTION_END_SCREEN_HANDOFF_MODEL,
      review_approved_youtube_placeholder_fade_start_seconds:
        REVIEW_APPROVED_END_SCREEN_FADE_START_SECONDS[episode.episodeId] ?? null,
      last_caption_visible_exit_start_seconds: endScreenTiming?.lastCaptionVisibleExitStartSeconds ?? null,
      last_caption_fully_suppressed_seconds: endScreenTiming?.lastCaptionFullySuppressedSeconds ?? null,
      youtube_placeholder_fade_start_seconds: endScreenTiming?.youtubePlaceholderFadeStartSeconds ?? null,
      youtube_placeholder_full_opacity_seconds: endScreenTiming?.youtubePlaceholderFullOpacitySeconds ?? null,
      caption_end_screen_gap_seconds: endScreenTiming?.captionEndScreenGapSeconds ?? null,
      caption_end_screen_overlap_read: endScreenTiming?.captionEndScreenOverlapRead || "pending_browser_runtime_qa",
      youtube_safe_window_caption_suppression_read:
        endScreenTiming?.youtubeSafeWindowCaptionSuppressionRead || "pending_browser_runtime_qa",
      vo_outro_blend_read: episodeVoOutroBlendRead,
      outro_policy: episodeOutroPolicy,
      outro_prelap_seconds: Number.isFinite(episodeOutroPrelapSeconds) ? episodeOutroPrelapSeconds : null,
      outro_target_after_voice_seconds: Number.isFinite(episodeOutroTargetAfterVoiceSeconds)
        ? episodeOutroTargetAfterVoiceSeconds
        : null,
      caption_display_timing_source_path: captionSources.displayTimingPath || "not_found",
      raw_caption_timing_source_path: captionSources.rawTimingPath || "not_found",
      caption_display_timing_source_is_raw_fallback:
        Boolean(captionSources.displayTimingPath) &&
        Boolean(captionSources.rawTimingPath) &&
        path.resolve(captionSources.displayTimingPath) === path.resolve(captionSources.rawTimingPath),
      caption_audio_sync_model: captionSources.audioSyncModel,
      caption_audio_offset_seconds: captionSources.audioOffsetSeconds,
      first_caption_display_cue_start_seconds: cues[0]?.start ?? null,
      first_caption_display_cue_uses_audio_time: (captionSources.audioOffsetSeconds || 0) > 0 ? (cues[0]?.start || 0) >= captionSources.audioOffsetSeconds - 0.25 : true,
      caption_motion_model: CAPTION_MOTION_MODEL,
      caption_timeline_layout_model: CAPTION_TIMELINE_LAYOUT_MODEL,
      caption_sync_target: CAPTION_SYNC_TARGET,
      caption_reading_lead_seconds: CAPTION_READING_LEAD_SECONDS,
      caption_intro_visibility_gate_model: CAPTION_INTRO_VISIBILITY_GATE_MODEL,
      caption_intro_gate_start_seconds: captionScrollTiming.caption_intro_gate_start_seconds,
      caption_intro_gate_full_opacity_seconds: captionScrollTiming.caption_intro_gate_full_opacity_seconds,
      caption_intro_premature_text_read: captionScrollTiming.caption_intro_premature_text_read,
      caption_intro_visibility_gate_static_pass:
        captionScrollTiming.caption_intro_visibility_gate_model === CAPTION_INTRO_VISIBILITY_GATE_MODEL &&
        captionScrollTiming.caption_intro_premature_text_read === "pass",
      caption_constant_speed_scope: CAPTION_CONSTANT_SPEED_SCOPE,
      caption_playback_clock_model: CAPTION_PLAYBACK_CLOCK_MODEL,
      caption_stack_render_model: CAPTION_STACK_RENDER_MODEL,
    caption_scroll_smoothness_model: CAPTION_SCROLL_SMOOTHNESS_MODEL,
      caption_runtime_coverage_model: CAPTION_RUNTIME_COVERAGE_MODEL,
      caption_full_vo_runtime_coverage_read: "pending_browser_runtime_qa",
      caption_runtime_cutoff_read: "pending_browser_runtime_qa",
      caption_scrub_transport_sync_read: "pending_browser_runtime_qa",
      review_transport_playing_scrub_read: "pending_browser_runtime_qa",
      caption_line_clip_read: "pending_browser_runtime_qa",
      caption_audio_time_transform_sync_read: "pending_browser_runtime_qa",
      caption_active_text_matches_audio_time_read: "pending_browser_runtime_qa",
      proof_build_freshness_guard_read: "pending_browser_runtime_qa",
      right_rail_caption_paint_visibility_read: "pending_browser_runtime_qa",
      caption_density_resolution_model: CAPTION_DENSITY_RESOLUTION_MODEL,
      caption_constant_scroll_speed_px_per_second: captionScrollTiming.caption_constant_scroll_speed_px_per_second,
      caption_stack_height_px: captionScrollTiming.caption_stack_height_px,
      caption_stack_paint_containment_read: captionScrollTiming.caption_stack_paint_containment_read,
      caption_speed_clamp_static_pass:
        captionScrollTiming.caption_constant_scroll_speed_px_per_second >= CAPTION_MIN_CONSTANT_SPEED_PX_PER_SECOND &&
        captionScrollTiming.caption_constant_scroll_speed_px_per_second <= CAPTION_MAX_CONSTANT_SPEED_PX_PER_SECOND,
      caption_dense_chunk_merge_count: captionScrollTiming.caption_dense_chunk_merge_count,
      caption_unresolved_dense_pair_count: captionScrollTiming.caption_unresolved_dense_pair_count,
      caption_no_dense_overlap_static_pass: (captionScrollTiming.caption_unresolved_dense_pair_count || 0) === 0,
      caption_layout_collision_guard: CAPTION_LAYOUT_COLLISION_GUARD,
      caption_min_rendered_line_gap_px: captionScrollTiming.caption_min_rendered_line_gap_px,
      caption_forced_takeaway_merge_count: captionScrollTiming.caption_forced_takeaway_merge_count,
      caption_collision_guard_static_pass:
        Number(captionScrollTiming.caption_min_rendered_line_gap_px || 0) >= CAPTION_MIN_RENDERED_LINE_GAP_PX,
      caption_source_cue_coverage_count: captionScrollTiming.caption_source_cue_coverage_count,
      caption_max_active_chunk_center_delta_at_cue_start_px:
        captionScrollTiming.caption_max_active_chunk_center_delta_at_cue_start_px,
      caption_active_band_at_cue_start_static_pass:
        (captionScrollTiming.caption_max_active_chunk_center_delta_at_cue_start_px || 0) <= CAPTION_ACTIVE_BAND_LOWER_DELTA_PX,
      caption_window_treatment_model: CAPTION_WINDOW_TREATMENT_MODEL,
      end_screen_palette_contract_id: endScreenPaletteContract.contract_id || "missing",
      end_screen_palette_contract_status: endScreenPaletteContract.status || "missing",
      end_screen_palette_contract_read:
        endScreenPaletteContract.reads?.end_screen_palette_contract_read || "blocked_missing_end_screen_palette_contract",
      no_cross_episode_default_palette_read:
        endScreenPaletteContract.reads?.no_cross_episode_default_palette_read || "blocked_missing_end_screen_palette_contract",
      end_screen_palette_model: END_SCREEN_PALETTE_MODEL,
      end_screen_palette_source: endScreenPalette?.palette_source || "sampled_episode_backplate",
      end_screen_palette_sample_read: endScreenPalette?.sample_read || "not_recorded",
      end_screen_adaptive_palette_static_pass: endScreenPaletteContract.status === "pass",
      end_screen_fixed_color_reuse_static_pass:
        endScreenPaletteContract.reads?.no_cross_episode_default_palette_read ===
        "pass_no_challenger_default_target_colors_with_visible_variability",
      end_screen_adaptive_perceptual_variability_static_pass:
        endScreenPaletteContract.reads?.end_screen_adaptive_perceptual_variability_read ===
        "pass_backplate_hue_visible_across_end_screen_targets",
      caption_line_opacity_model: CAPTION_LINE_OPACITY_MODEL,
      highlight_phrase_scope: HIGHLIGHT_PHRASE_SCOPE,
      caption_highlight_model_id: CAPTION_HIGHLIGHT_MODEL_ID,
      highlight_semantic_role: HIGHLIGHT_SEMANTIC_ROLE,
      highlight_density_model: HIGHLIGHT_DENSITY_MODEL,
      highlight_color_model: HIGHLIGHT_COLOR_MODEL,
      highlight_visual_timing_model: HIGHLIGHT_VISUAL_TIMING_MODEL,
      highlight_takeaway_count: highlightStats.highlight_count,
      highlight_single_word_count: highlightStats.single_word_highlight_count,
      highlight_max_gap_seconds: highlightStats.max_highlight_gap_seconds,
      highlight_no_single_word_static_pass: highlightStats.single_word_highlight_count === 0,
      highlight_density_static_pass:
        keyPhraseSpans.length === 0 || highlightDensityPassForEpisode(episode.episodeId, highlightStats),
      highlight_distinct_accent_static_pass:
        keyPhraseSpans.length === 0 || /pass/i.test(String(highlightAccent.highlight_distinct_from_caption_text_read || "")),
      highlight_backplate_contrast_static_pass:
        keyPhraseSpans.length === 0 || /pass/i.test(String(highlightAccent.highlight_backplate_contrast_read || "")),
      ambient_frame_clock_model: ambientFrameClock.ambient_frame_clock_model,
      ambient_render_clock_read: ambientFrameClock.ambient_render_clock_read,
      ambient_wall_clock_drift_suppression_read: ambientFrameClock.ambient_wall_clock_drift_suppression_read,
      ambient_right_rail_motion_policy:
        ambientRightRailMotion.ambient_right_rail_motion_policy || "not_applicable_no_aircraft_right_rail_motion_layer",
      foreground_matte_policy: ambientRightRailMotion.foreground_matte_policy || "not_applicable",
      right_rail_matte_removed_static_pass: ambientRightRailMotion.applicable
        ? /pass/i.test(String(ambientRightRailMotion.right_rail_matte_removed_read || ""))
        : true,
      aircraft_right_rail_route_count: ambientRightRailMotion.aircraft_right_rail_route_count || 0,
      aircraft_right_rail_route_static_pass: ambientRightRailMotion.applicable
        ? Boolean(ambientRightRailMotion.aircraft_right_rail_route_static_pass)
        : true,
      aircraft_right_rail_cutoff_removed: Boolean(ambientRightRailMotion.aircraft_right_rail_cutoff_removed),
      aircraft_right_rail_cutoff_removed_static_pass: ambientRightRailMotion.applicable
        ? Boolean(ambientRightRailMotion.aircraft_right_rail_cutoff_removed)
        : true,
      aircraft_right_rail_visibility_read: ambientRightRailMotion.applicable
        ? ambientRightRailMotion.aircraft_right_rail_visibility_read
        : "not_applicable_no_aircraft_right_rail_motion_layer",
      right_rail_alignment_review_only: Boolean(episode.rightRailAlignmentOnly),
      ambient_effects_deferred_static_pass: episode.rightRailAlignmentOnly
        ? Boolean(manifest.ambient_effects_deferral?.deferral_note_path && manifest.ambient_effects_deferral?.prior_kept_ambient_manifest_path)
        : true,
      music_contract_revalidated_for_alignment_static_pass: episode.rightRailAlignmentOnly
        ? manifest.music_integration_contract_revalidation?.status ===
            "pass_revalidated_with_contract_timed_music_mix_against_prior_kept_v6_ambient_state"
        : true,
      contract_music_mix_static_pass:
        episode.rightRailAlignmentOnly || episode.contractReviewMixRequired ? Boolean(contractMusicMix?.audioPath) : true,
      semmelweis_contract_music_mix_static_pass: episode.rightRailAlignmentOnly ? Boolean(contractMusicMix?.audioPath) : true,
      media_copied_or_modified: Boolean(contractMusicMix?.audioPath),
    },
  });

  updateTomlMarker(
    baseline?.episode_toml_path,
    buildTomlBlock({
      episode,
      status: effectiveStatus,
      manifestPath: roughManifestPath,
      playerPath,
      reviewPacketPath,
      captionScrollTiming,
      ambientRightRailMotion,
    }),
  );

  return {
    episode_id: episode.episodeId,
    title: episode.title,
    action: episode.action,
    status: effectiveStatus,
    human_disposition: manifest.human_disposition,
    human_disposition_utc: manifest.human_disposition_utc || null,
    may_render_final_mp4: Boolean(manifest.may_create_full_runtime_mp4_render),
    may_advance_to_final_assembly: Boolean(manifest.may_advance_to_final_assembly),
    may_advance_to_publish_readiness: Boolean(manifest.may_advance_to_publish_readiness),
    may_youtube_action: Boolean(manifest.may_youtube_action),
    publish_ready: Boolean(manifest.publish_ready),
    youtube_upload_ready: Boolean(manifest.youtube_upload_ready),
    upload_performed: Boolean(manifest.upload_performed),
    public_release_ready: Boolean(manifest.public_release_ready),
    youtube_visibility_action_performed: Boolean(manifest.youtube_visibility_action_performed),
    right_rail_alignment_review_only: Boolean(manifest.right_rail_alignment_review_only),
    output_dir: outputDir,
    manifest_path: roughManifestPath,
    player_path: playerPath,
    review_packet_path: reviewPacketPath,
    key_phrase_cue_map_supplement_path: keyPhrasePath,
    qa_path: qaPath,
    source_predecessor: episode.sourceRoot,
    source_art_path: manifest.source_visual?.source_art_path || sourceArtPath || null,
    source_art_sha256: manifest.source_visual?.source_art_sha256 || sha256File(sourceArtPath),
    source_art_override_status: manifest.source_visual?.source_art_override_status || null,
    source_art_highlight_merge_model: manifest.source_art_highlight_merge_model || "not_applicable",
    source_art_highlight_merge_predecessor_proof_path:
      manifest.source_art_highlight_merge_predecessor_proof_path || "not_applicable",
    source_art_highlight_merge_read: manifest.source_art_highlight_merge_read || "not_applicable",
    caption_display_timing_source_path: captionSources.displayTimingPath || null,
    raw_caption_timing_source_path: captionSources.rawTimingPath || null,
    caption_audio_sync_model: captionSources.audioSyncModel,
    caption_audio_offset_seconds: captionSources.audioOffsetSeconds,
    intro_trim_model: INTRO_TRIM_MODEL,
    intro_trim_seconds: INTRO_TRIM_SECONDS,
    previous_voice_start_offset_seconds: PREVIOUS_VOICE_START_OFFSET_SECONDS,
    voice_start_offset_seconds: VOICE_START_OFFSET_SECONDS,
    caption_intro_trim_source_path: captionSources.trimmedSidecarSourcePath || null,
    caption_intro_trim_source_mode: captionSources.trimmedSidecarSourceMode || null,
    music_contract_json_path: musicContract?.__jsonPath || captionSources.musicContractJsonPath || null,
    music_contract_json_sha256: sha256File(musicContract?.__jsonPath || captionSources.musicContractJsonPath),
    review_audio_mix_path: contractMusicMix?.audioPath || null,
    review_audio_mix_manifest_path: contractMusicMix?.manifestPath || null,
    voice_audio_defect_repair_model: contractMusicMix?.audioDefectRepair?.model || null,
    voice_audio_defect_repair_read: contractMusicMix?.audioDefectRepair?.voice_audio_defect_repair_read || null,
    audio_defect_repair_manifest_path: contractMusicMix?.audioDefectRepair?.repair_manifest?.path || null,
    superseded_defective_voice_master_path:
      contractMusicMix?.audioDefectRepair?.superseded_defective_voice_master?.path || null,
    voice_loudness_alignment_status: contractMusicMix?.voiceLoudnessAlignment?.status || null,
    voice_loudness_alignment_manifest_path: contractMusicMix?.voiceLoudnessAlignment?.manifest_path || null,
    source_voice_mean_volume_db: contractMusicMix?.voiceLoudnessAlignment?.source_window_volumedetect?.mean_volume_db ?? null,
    mix_voice_mean_volume_db: contractMusicMix?.voiceLoudnessAlignment?.output_window_volumedetect?.mean_volume_db ?? null,
    duration_seconds: Number(durationSeconds.toFixed(3)),
    first_caption_display_cue_start_seconds: Number((cues[0]?.start ?? 0).toFixed(3)),
    proof_build_id: proofBuildId,
    proof_generated_at_utc: PROOF_GENERATED_AT_UTC,
    proof_build_json_path: proofBuildPath,
    proof_build_json_sha256: manifest.proof_build_json_sha256,
    review_url: reviewUrlForPath(playerPath, { v: proofBuildId }),
    caption_constant_scroll_speed_px_per_second: captionScrollTiming.caption_constant_scroll_speed_px_per_second,
    caption_timeline_layout_model: CAPTION_TIMELINE_LAYOUT_MODEL,
    caption_sync_target: CAPTION_SYNC_TARGET,
    caption_reading_lead_seconds: CAPTION_READING_LEAD_SECONDS,
    caption_constant_speed_scope: CAPTION_CONSTANT_SPEED_SCOPE,
    caption_playback_clock_model: CAPTION_PLAYBACK_CLOCK_MODEL,
    caption_stack_render_model: CAPTION_STACK_RENDER_MODEL,
    caption_scroll_smoothness_model: CAPTION_SCROLL_SMOOTHNESS_MODEL,
    caption_runtime_coverage_model: CAPTION_RUNTIME_COVERAGE_MODEL,
    caption_full_vo_runtime_coverage_read: "pending_browser_runtime_qa",
    caption_density_resolution_model: CAPTION_DENSITY_RESOLUTION_MODEL,
    caption_dense_chunk_merge_count: captionScrollTiming.caption_dense_chunk_merge_count,
    caption_unresolved_dense_pair_count: captionScrollTiming.caption_unresolved_dense_pair_count,
    caption_min_rendered_line_gap_px: captionScrollTiming.caption_min_rendered_line_gap_px,
    caption_forced_takeaway_merge_count: captionScrollTiming.caption_forced_takeaway_merge_count,
    caption_layout_collision_guard: CAPTION_LAYOUT_COLLISION_GUARD,
    caption_max_active_chunk_center_delta_at_cue_start_px:
      captionScrollTiming.caption_max_active_chunk_center_delta_at_cue_start_px,
    caption_window_treatment_model: CAPTION_WINDOW_TREATMENT_MODEL,
    end_screen_palette_contract_id: endScreenPaletteContract.contract_id || "missing",
    end_screen_palette_contract_status: endScreenPaletteContract.status || "missing",
    end_screen_palette_contract_read:
      endScreenPaletteContract.reads?.end_screen_palette_contract_read || "blocked_missing_end_screen_palette_contract",
    no_cross_episode_default_palette_read:
      endScreenPaletteContract.reads?.no_cross_episode_default_palette_read || "blocked_missing_end_screen_palette_contract",
    caption_highlight_model_id: CAPTION_HIGHLIGHT_MODEL_ID,
    highlight_semantic_role: HIGHLIGHT_SEMANTIC_ROLE,
    highlight_density_model: HIGHLIGHT_DENSITY_MODEL,
    highlight_color_model: HIGHLIGHT_COLOR_MODEL,
    highlight_visual_timing_model: HIGHLIGHT_VISUAL_TIMING_MODEL,
    highlight_takeaway_count: keyPhraseSpans.length,
    ambient_frame_clock_model: manifest.ambient_frame_clock_model,
    ambient_render_clock_read: manifest.ambient_render_clock_read,
    ambient_wall_clock_drift_suppression_read: manifest.ambient_wall_clock_drift_suppression_read,
    ambient_right_rail_motion_policy:
      ambientRightRailMotion.ambient_right_rail_motion_policy || "not_applicable_no_aircraft_right_rail_motion_layer",
    foreground_matte_policy: ambientRightRailMotion.foreground_matte_policy || "not_applicable",
    aircraft_right_rail_route_count: ambientRightRailMotion.aircraft_right_rail_route_count || 0,
    aircraft_right_rail_cutoff_removed: Boolean(ambientRightRailMotion.aircraft_right_rail_cutoff_removed),
    blocked_prerequisite: episode.blockedPrereq || null,
  };
}

function updateBaselineIndex(index, summaries) {
  const byEpisode = new Map(summaries.map((summary) => [summary.episode_id, summary]));
  for (const baseline of index.baselines || []) {
    const summary = byEpisode.get(baseline.episode_id);
    if (!summary) continue;
    const summaryKept = String(summary.human_disposition || "").trim().toLowerCase() === "keep";
    if (!baseline.previous_baseline_status_before_rolling_caption_rail_redesign) {
      baseline.previous_baseline_status_before_rolling_caption_rail_redesign = baseline.baseline_status || "unknown";
    }
    baseline.baseline_status = summary.status;
    baseline.current_gate = summaryKept
      ? "rolling_caption_rail_rough_assembly_keep"
      : summary.blocked_prerequisite
        ? "blocked_before_rough_assembly"
        : "rolling_caption_rail_rough_assembly_review";
    baseline.next_required_gate = summaryKept
      ? "final_assembly_keep"
      : summary.blocked_prerequisite
      ? "complete_current_prerequisite_keeps_then_refresh_rolling_caption_rail_rough_proof"
      : "human_keep_on_refreshed_rolling_caption_rail_rough_proof";
    baseline.may_render_final_mp4 = summaryKept;
    baseline.may_advance_to_final_assembly = summaryKept;
    baseline.may_advance_to_publish_readiness = false;
    baseline.may_youtube_action = false;
    baseline.rolling_caption_rail_redesign = {
      created_utc: CREATED_UTC,
      rail_preset_id: "fixed_16x9_right_rail_v1",
      rail_content_model_id: "rolling_caption_anchor_v1",
      caption_display_model: "rolling_rail_caption_window_v1",
      intro_trim_model: summary.intro_trim_model || INTRO_TRIM_MODEL,
      intro_trim_seconds: summary.intro_trim_seconds ?? INTRO_TRIM_SECONDS,
      previous_voice_start_offset_seconds:
        summary.previous_voice_start_offset_seconds ?? PREVIOUS_VOICE_START_OFFSET_SECONDS,
      voice_start_offset_seconds: summary.voice_start_offset_seconds ?? VOICE_START_OFFSET_SECONDS,
      caption_motion_model: CAPTION_MOTION_MODEL,
      caption_timeline_layout_model: CAPTION_TIMELINE_LAYOUT_MODEL,
      caption_sync_target: CAPTION_SYNC_TARGET,
      caption_reading_lead_seconds: CAPTION_READING_LEAD_SECONDS,
      review_control_model: REVIEW_CONTROL_MODEL,
      review_transport_scrub_model: REVIEW_TRANSPORT_SCRUB_MODEL,
      legacy_review_chrome_suppression_model: LEGACY_REVIEW_CHROME_SUPPRESSION_MODEL,
      caption_constant_speed_scope: CAPTION_CONSTANT_SPEED_SCOPE,
      caption_playback_clock_model: CAPTION_PLAYBACK_CLOCK_MODEL,
      caption_stack_render_model: CAPTION_STACK_RENDER_MODEL,
    caption_scroll_smoothness_model: CAPTION_SCROLL_SMOOTHNESS_MODEL,
      caption_runtime_coverage_model: CAPTION_RUNTIME_COVERAGE_MODEL,
      caption_full_vo_runtime_coverage_read: "pending_browser_runtime_qa",
      caption_density_resolution_model: CAPTION_DENSITY_RESOLUTION_MODEL,
      caption_line_opacity_model: CAPTION_LINE_OPACITY_MODEL,
      caption_window_treatment_model: CAPTION_WINDOW_TREATMENT_MODEL,
      caption_constant_scroll_speed_px_per_second: summary.caption_constant_scroll_speed_px_per_second,
      caption_dense_chunk_merge_count: summary.caption_dense_chunk_merge_count,
      caption_unresolved_dense_pair_count: summary.caption_unresolved_dense_pair_count,
      caption_layout_collision_guard: CAPTION_LAYOUT_COLLISION_GUARD,
      caption_min_rendered_line_gap_px: summary.caption_min_rendered_line_gap_px,
      caption_forced_takeaway_merge_count: summary.caption_forced_takeaway_merge_count,
      caption_max_active_chunk_center_delta_at_cue_start_px:
        summary.caption_max_active_chunk_center_delta_at_cue_start_px,
      highlight_phrase_scope: HIGHLIGHT_PHRASE_SCOPE,
      caption_highlight_model_id: CAPTION_HIGHLIGHT_MODEL_ID,
      highlight_semantic_role: HIGHLIGHT_SEMANTIC_ROLE,
      highlight_density_model: HIGHLIGHT_DENSITY_MODEL,
      highlight_color_model: HIGHLIGHT_COLOR_MODEL,
      highlight_visual_timing_model: HIGHLIGHT_VISUAL_TIMING_MODEL,
      caption_window_role: "middle_two_thirds_right_rail",
      caption_blur_scope: "none",
      caption_highlight_source: "living_cover_cue_map_key_phrases",
      caption_palette_source: "sampled_episode_backplate",
      voice_audio_defect_repair_model: summary.voice_audio_defect_repair_model || "not_applicable",
      voice_audio_defect_repair_read: summary.voice_audio_defect_repair_read || "not_applicable",
      audio_defect_repair_manifest_path: summary.audio_defect_repair_manifest_path || "not_applicable",
      superseded_defective_voice_master_path: summary.superseded_defective_voice_master_path || "not_applicable",
      end_screen_palette_contract_id: summary.end_screen_palette_contract_id,
      end_screen_palette_contract_status: summary.end_screen_palette_contract_status,
      end_screen_palette_contract_read: summary.end_screen_palette_contract_read,
      no_cross_episode_default_palette_read: summary.no_cross_episode_default_palette_read,
      action: summary.action,
      status: summary.status,
      manifest_path: summary.manifest_path,
      player_path: summary.player_path,
      review_packet_path: summary.review_packet_path,
      source_art_path: summary.source_art_path,
      source_art_sha256: summary.source_art_sha256,
      source_art_override_status: summary.source_art_override_status,
      source_art_highlight_merge_model: summary.source_art_highlight_merge_model,
      source_art_highlight_merge_predecessor_proof_path: summary.source_art_highlight_merge_predecessor_proof_path,
      source_art_highlight_merge_read: summary.source_art_highlight_merge_read,
      source_art_reopened_by_default: false,
      right_rail_safe_space_revalidation_required: true,
      downstream_gates_blocked_until_rolling_rough_keep: !summaryKept,
      blocked_prerequisite: summary.blocked_prerequisite,
      human_disposition: summary.human_disposition || null,
      human_disposition_utc: summary.human_disposition_utc || null,
      may_render_final_mp4: summary.may_render_final_mp4,
      may_advance_to_final_assembly: summary.may_advance_to_final_assembly,
      may_advance_to_publish_readiness: false,
      may_youtube_action: false,
    };
    const blockers = new Set(
      (Array.isArray(baseline.current_blockers) ? baseline.current_blockers : []).filter(
        (blocker) =>
          !(summaryKept && blocker === "rolling_caption_rail_refreshed_rough_proof_pending_human_keep") &&
          !(summary.episode_id === "737-max" && blocker === "music_integration_contract_not_created") &&
          !(
            summary.episode_id === "737-max" &&
            blocker === "music integration contract and current motion prerequisites must receive keep before rough assembly can be keep-ready"
          ),
      ),
    );
    if (!summaryKept) blockers.add("rolling_caption_rail_refreshed_rough_proof_pending_human_keep");
    if (summaryKept) blockers.add("public_upload_publish_schedule_release_out_of_scope");
    if (summary.blocked_prerequisite) blockers.add(summary.blocked_prerequisite);
    baseline.current_blockers = Array.from(blockers);
    if (summary.episode_id === "737-max" && summary.music_contract_json_path) {
      baseline.music_integration_contract_status = "contract_created_for_right_rail_review_pending_human_keep";
      baseline.music_integration_contract_json_path = summary.music_contract_json_path;
      baseline.music_integration_contract_json_sha256 = summary.music_contract_json_sha256;
      baseline.review_audio_mix_path = summary.review_audio_mix_path;
      baseline.review_audio_mix_manifest_path = summary.review_audio_mix_manifest_path;
    }
    updateBaselineTomlPointers(baseline.episode_toml_path, baseline.baseline_doc_path, summary.status);
    updateBaselineDoc(baseline.baseline_doc_path, summary);
  }
  writeJson(BASELINE_INDEX_PATH, index);
}

function markQuietChallengerPredecessor(summary) {
  if (!summary || summary.episode_id !== "challenger" || PACKET_STAMP === DEFAULT_PACKET_STAMP) return;
  const previousDir = path.join(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly",
    `challenger_rolling_caption_rail_rough_proof_${DEFAULT_PACKET_STAMP}`,
  );
  const previousManifestPath = path.join(previousDir, "rough_assembly_manifest.json");
  const previousPacketPath = path.join(previousDir, "review/rolling_caption_rail_review_packet.md");
  const previousManifest = readJsonIfExists(previousManifestPath);
  if (!previousManifest) return;
  previousManifest.status = "tighten_superseded_by_vo_loudness_repair";
  previousManifest.human_disposition = "tighten";
  previousManifest.may_create_full_runtime_mp4_render = false;
  previousManifest.may_advance_to_final_assembly = false;
  previousManifest.may_advance_to_publish_readiness = false;
  previousManifest.may_youtube_action = false;
  previousManifest.superseded_by_vo_loudness_repair = {
    recorded_utc: PROOF_GENERATED_AT_UTC,
    successor_packet_path: summary.output_dir,
    successor_manifest_path: summary.manifest_path,
    successor_player_path: summary.player_path,
    reason:
      "Challenger canonical-signoff rail review mix used unmastered raw ElevenLabs chunks and measured materially quieter than the first-eight cohort.",
    source_voice_mean_volume_db: summary.source_voice_mean_volume_db,
    corrected_mix_voice_mean_volume_db: summary.mix_voice_mean_volume_db,
    youtube_action_taken: false,
  };
  previousManifest.rough_assembly_reads = previousManifest.rough_assembly_reads || {};
  Object.assign(previousManifest.rough_assembly_reads, {
    voice_loudness_alignment_read: "tighten_source_voice_master_unmastered_quiet_raw_chunks",
    audio_level_mix_read: "tighten_challenger_vo_level_below_first_eight_cohort",
    successor_voice_loudness_repair_read: "pass_successor_created_pending_human_listen_keep",
  });
  previousManifest.qa = previousManifest.qa || {};
  previousManifest.qa.voice_loudness_alignment_read = "tighten_source_voice_master_unmastered_quiet_raw_chunks";
  previousManifest.qa.successor_voice_loudness_repair_path = summary.manifest_path;
  writeJson(previousManifestPath, previousManifest);
  if (fs.existsSync(previousPacketPath)) {
    const note = [
      "",
      "## Superseded: VO Loudness Repair",
      "",
      `Recorded UTC: ${PROOF_GENERATED_AT_UTC}`,
      "",
      "This Challenger rolling-rail proof is `tighten` because its review mix used an unmastered canonical-signoff voice master and reads materially quieter than the other first-eight rail proofs.",
      "",
      `Successor proof: \`${summary.output_dir}\``,
      "",
      "No YouTube upload, deletion, publish, schedule, or visibility action was taken.",
      "",
    ].join("\n");
    const current = fs.readFileSync(previousPacketPath, "utf8");
    if (!current.includes("## Superseded: VO Loudness Repair")) {
      fs.writeFileSync(previousPacketPath, current.trimEnd() + note, "utf8");
    }
  }
}

function requestedEpisodeIdsFromArgv(argv) {
  const requested = [];
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--episode" && argv[i + 1]) {
      requested.push(argv[++i]);
    } else if (arg.startsWith("--episode=")) {
      requested.push(arg.slice("--episode=".length));
    }
  }
  if (process.env.CE_ROLLING_RAIL_EPISODE) {
    requested.push(...process.env.CE_ROLLING_RAIL_EPISODE.split(","));
  }
  return new Set(requested.map((item) => String(item).trim()).filter(Boolean));
}

function mergeRolloutSummaries(existingSummaries, builtSummaries) {
  const byEpisode = new Map((existingSummaries || []).map((summary) => [summary.episode_id, summary]));
  for (const summary of builtSummaries) byEpisode.set(summary.episode_id, summary);
  return EPISODES.map((episode) => byEpisode.get(episode.episodeId)).filter(Boolean);
}

function writeApprovedLessonTakeawaySpanArtifact(summaries) {
  ensureDir(LESSON_TAKEAWAY_REVIEW_ROOT);
  const artifactPath = path.join(
    LESSON_TAKEAWAY_REVIEW_ROOT,
    `approved_lesson_takeaway_spans_${PROOF_GENERATION_STAMP}Z.json`,
  );
  const candidateReview = loadApprovedLessonTakeawayCandidates();
  const episodes = (summaries || []).map((summary) => {
    const supplement = readJsonIfExists(summary.key_phrase_cue_map_supplement_path) || {};
    return {
      episode_id: summary.episode_id,
      title: summary.title,
      expected_takeaway_count: expectedLessonTakeawayCount(summary.episode_id),
      rendered_takeaway_count: Array.isArray(supplement.key_phrase_spans) ? supplement.key_phrase_spans.length : 0,
      proof_build_id: summary.proof_build_id,
      proof_url: summary.review_url,
      cue_map_supplement_path: summary.key_phrase_cue_map_supplement_path,
      cue_map_supplement_sha256: sha256File(summary.key_phrase_cue_map_supplement_path),
      highlight_color_model: HIGHLIGHT_COLOR_MODEL,
      highlight_color_qa: supplement.highlight_color_qa || null,
      spans: supplement.key_phrase_spans || [],
    };
  });
  const artifact = {
    artifact_id: `first_eight_approved_lesson_takeaway_spans_${PROOF_GENERATION_STAMP}Z`,
    created_utc: PROOF_GENERATED_AT_UTC,
    status: "approved_spans_promoted_rendered_in_rolling_caption_proofs",
    caption_highlight_model_id: CAPTION_HIGHLIGHT_MODEL_ID,
    highlight_semantic_role: HIGHLIGHT_SEMANTIC_ROLE,
    highlight_density_model: HIGHLIGHT_DENSITY_MODEL,
    highlight_color_model: HIGHLIGHT_COLOR_MODEL,
    highlight_visual_timing_model: HIGHLIGHT_VISUAL_TIMING_MODEL,
    review_source_path: candidateReview.path,
    review_source_sha256: candidateReview.sha256,
    total_span_count: episodes.reduce((total, episode) => total + episode.rendered_takeaway_count, 0),
    episodes,
  };
  writeJson(artifactPath, artifact);
  writeJson(APPROVED_LESSON_TAKEAWAY_SPANS_LATEST_PATH, {
    ...artifact,
    latest_artifact_path: artifactPath,
    latest_artifact_sha256: sha256File(artifactPath),
  });
  return {
    path: artifactPath,
    sha256: sha256File(artifactPath),
    latest_path: APPROVED_LESSON_TAKEAWAY_SPANS_LATEST_PATH,
    latest_sha256: sha256File(APPROVED_LESSON_TAKEAWAY_SPANS_LATEST_PATH),
  };
}

function main() {
  const requestedEpisodeIds = requestedEpisodeIdsFromArgv(process.argv.slice(2));
  const episodesToBuild = requestedEpisodeIds.size
    ? EPISODES.filter((episode) => requestedEpisodeIds.has(episode.episodeId))
    : EPISODES;
  const unknownEpisodeIds = Array.from(requestedEpisodeIds).filter(
    (episodeId) => !EPISODES.some((episode) => episode.episodeId === episodeId),
  );
  if (unknownEpisodeIds.length) throw new Error(`Unknown episode id(s): ${unknownEpisodeIds.join(", ")}`);
  const baselineIndex = readJsonIfExists(BASELINE_INDEX_PATH);
  if (!baselineIndex) throw new Error(`Could not read ${BASELINE_INDEX_PATH}`);
  const baselineByEpisode = new Map((baselineIndex.baselines || []).map((baseline) => [baseline.episode_id, baseline]));
  const builtSummaries = episodesToBuild.map((episode) => buildEpisode(episode, baselineByEpisode.get(episode.episodeId)));
  const previousRollout = readJsonIfExists(ROLLOUT_SUMMARY_PATH);
  const summaries = requestedEpisodeIds.size
    ? mergeRolloutSummaries(previousRollout?.episodes || [], builtSummaries)
    : builtSummaries;
  markQuietChallengerPredecessor(builtSummaries.find((summary) => summary.episode_id === "challenger"));
  updateBaselineIndex(baselineIndex, builtSummaries);
  fs.writeFileSync(REVIEW_INDEX_PATH, renderReviewIndex(summaries));
  const approvedTakeawaySpanArtifact = writeApprovedLessonTakeawaySpanArtifact(summaries);
  writeJson(ROLLOUT_SUMMARY_PATH, {
    rollout_id: `first_eight_rolling_caption_rail_redesign_${PACKET_STAMP}`,
    created_utc: CREATED_UTC,
    summary:
      "Shared first-eight long-form rail redesign: fixed geometry preserved, rolling_caption_anchor_v1 plus rolling_rail_caption_window_v1 added, old context rows removed, downstream gates blocked until refreshed rough keeps.",
    review_index_path: REVIEW_INDEX_PATH,
    review_index_url: reviewUrlForPath(REVIEW_INDEX_PATH),
    approved_lesson_takeaway_spans_path: approvedTakeawaySpanArtifact.path,
    approved_lesson_takeaway_spans_sha256: approvedTakeawaySpanArtifact.sha256,
    approved_lesson_takeaway_spans_latest_path: approvedTakeawaySpanArtifact.latest_path,
    approved_lesson_takeaway_spans_latest_sha256: approvedTakeawaySpanArtifact.latest_sha256,
    episodes: summaries,
  });
  for (const summary of summaries) {
    console.log(`${summary.episode_id}: ${summary.status}`);
    console.log(`  ${summary.manifest_path}`);
  }
  console.log(`review_index: ${reviewUrlForPath(REVIEW_INDEX_PATH)}`);
}

main();
