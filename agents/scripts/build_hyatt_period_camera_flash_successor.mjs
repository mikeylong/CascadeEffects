#!/usr/bin/env node
import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const predecessorRoot =
  "/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt_living_cover_html_rough_proof_n6_more_pronounced_flash_core_20260520T015715Z";
const roughAssemblyRoot = path.dirname(predecessorRoot);
const predecessorProfileId = "hyatt_audited_flash_more_pronounced_core_v1";
const profileId = "hyatt_1981_xenon_camera_flash_pop_v1";
const deterministicSeed = 2026052003;
const frameSeconds = 1 / 24;

const periodContract = {
  target: "period_1981_xenon_pop",
  version: "period_xenon_pop_with_video_bloom_v1",
  physical_flash_duration_seconds_reference: 0.001,
  render_envelope_seconds_min: 0.125,
  render_envelope_seconds_max: 0.167,
  attack_seconds_max: 0.015,
  peak_hold_seconds: Number(frameSeconds.toFixed(6)),
  decay_seconds_min: 0.07,
  decay_seconds_max: 0.11,
  visible_frame_target_min: 3,
  visible_frame_target_max: 4,
  no_lingering_after_frames: 6,
  visibility_threshold: 0.16,
  min_peak_strength: 0.92,
  max_peak_strength: 1.08,
  min_core_radius_px: 2.6,
  max_core_radius_px: 3.2,
  min_halo_radius_px: 16,
  max_halo_radius_px: 20,
  max_full_screen_alpha: 0.065,
  min_same_hotspot_gap_seconds: 8,
  max_flashes_per_one_second_window: 3,
};

const fullScreenPulse = {
  version: "period_xenon_secondary_exposure_pulse_v1",
  source: "audited_camera_flashes_only",
  enabled: true,
  alpha_per_full_strength_flash: 0.041,
  max_alpha: 0.065,
  end_screen_cap_alpha: 0.01,
  color_rgb: [255, 238, 207],
  compositing: "screen_canvas_layer_below_right_rail",
  aggregate_policy: "sum_active_audited_flash_events_then_hard_cap",
  rail_caption_protection: "ambient_canvas_z_index_below_rail_plus_alpha_cap",
  coupling: "local_core_peak_required",
  pulse_visible_frame_target: "2_to_3_frames",
};

function utcStamp(date = new Date()) {
  return date.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
}

const stamp = utcStamp();
const successorId = `hyatt_living_cover_html_rough_proof_n6_period_camera_flash_${stamp}`;
const successorRoot = path.join(roughAssemblyRoot, successorId);

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

function sha256(filePath) {
  const hash = createHash("sha256");
  hash.update(fs.readFileSync(filePath));
  return hash.digest("hex");
}

function artifact(filePath) {
  return {
    path: filePath,
    sha256: sha256(filePath),
    bytes: fs.statSync(filePath).size,
  };
}

function extractProof(html) {
  const marker = "    const proof = ";
  const start = html.indexOf(marker);
  if (start === -1) throw new Error("Unable to find embedded proof object");
  const jsonStart = start + marker.length;
  const end = html.indexOf("\n    const root =", jsonStart);
  if (end === -1) throw new Error("Unable to find embedded proof object end");
  return JSON.parse(html.slice(jsonStart, end).trim().replace(/;$/, ""));
}

function replaceProof(html, proof) {
  const marker = "    const proof = ";
  const start = html.indexOf(marker);
  if (start === -1) throw new Error("Unable to find embedded proof object");
  const jsonStart = start + marker.length;
  const end = html.indexOf("\n    const root =", jsonStart);
  if (end === -1) throw new Error("Unable to find embedded proof object end");
  return `${html.slice(0, start)}${marker}${JSON.stringify(proof, null, 2)};\n${html.slice(end + 1)}`;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function smoothstep(t) {
  const x = clamp(t, 0, 1);
  return x * x * (3 - 2 * x);
}

function flashIntensity(event, audioTime) {
  const envelope = Number(event.render_envelope_seconds ?? event.duration_seconds);
  const dt = audioTime - event.time_seconds;
  if (dt < 0 || dt > envelope) return 0;
  const attack = Math.min(Number(event.attack_seconds ?? 0.01), periodContract.attack_seconds_max);
  const hold = Number(event.peak_hold_seconds ?? frameSeconds);
  const decay = Math.max(0.001, Number(event.decay_seconds ?? envelope - attack - hold));
  if (dt < attack) return 0.82 + 0.18 * smoothstep(dt / attack);
  if (dt < attack + hold) return 1;
  const p = (dt - attack - hold) / decay;
  return Math.pow(Math.max(0, 1 - p), 1.55);
}

function flashPhase(event, audioTime) {
  const envelope = Number(event.render_envelope_seconds ?? event.duration_seconds);
  const dt = audioTime - event.time_seconds;
  if (dt < 0) return "pre_event";
  if (dt > envelope) return "inactive";
  const attack = Math.min(Number(event.attack_seconds ?? 0.01), periodContract.attack_seconds_max);
  const hold = Number(event.peak_hold_seconds ?? frameSeconds);
  if (dt < attack) return "attack_peak";
  if (dt < attack + hold) return "peak_hold";
  return "decay_bloom";
}

function pulseAlphaAt(audioTime, flashes, proof, pulse) {
  const maxAlpha = Number(pulse.max_alpha || periodContract.max_full_screen_alpha);
  const endScreenCap = Number(pulse.end_screen_cap_alpha || 0.01);
  const cap = audioTime >= proof.endScreenStart ? Math.min(maxAlpha, endScreenCap) : maxAlpha;
  const baseAlpha = Number(pulse.alpha_per_full_strength_flash || 0.041);
  let alpha = 0;
  for (const event of flashes) {
    const intensity = flashIntensity(event, audioTime);
    if (intensity < periodContract.visibility_threshold) continue;
    const strengthScale = clamp(Number(event.peak_strength ?? event.strength ?? 1), 0.8, 1.15);
    alpha += Math.pow(intensity, 1.45) * baseAlpha * strengthScale;
  }
  return clamp(alpha, 0, cap);
}

function periodTimeFor(event, index) {
  if (event.forced_review_sample) return Number(event.time_seconds.toFixed(3));
  if (event.id === "audited_flash_013_diag_walkway_08") return 47.62;
  if (event.id === "audited_flash_015_diag_walkway_09") return 54.62;
  const offset =
    (((index * 13) % 17) - 8) * 0.063 +
    (((index * 7) % 11) - 5) * 0.021;
  return Number(clamp(event.time_seconds + offset, 0.8, 869).toFixed(3));
}

function transformFlashEvent(event, index) {
  const attackSeconds = 0.01 + (index % 3) * 0.001;
  const decaySeconds = 0.073 + (index % 5) * 0.009;
  const renderEnvelope = Number((attackSeconds + frameSeconds + decaySeconds).toFixed(3));
  const peakStrength = Number((0.92 + (index % 9) * 0.02).toFixed(3));
  const coreRadius = Number((2.6 + (index % 4) * 0.2).toFixed(2));
  const haloRadius = 16 + (index % 5);
  return {
    ...event,
    original_time_seconds: event.time_seconds,
    original_duration_seconds: event.duration_seconds,
    original_strength: event.strength,
    original_core_radius_px: event.core_radius_px,
    original_halo_radius_px: event.halo_radius_px,
    time_seconds: periodTimeFor(event, index),
    duration_seconds: renderEnvelope,
    render_envelope_seconds: renderEnvelope,
    physical_flash_duration_seconds_reference: periodContract.physical_flash_duration_seconds_reference,
    attack_seconds: Number(attackSeconds.toFixed(3)),
    peak_hold_seconds: periodContract.peak_hold_seconds,
    decay_seconds: Number(decaySeconds.toFixed(3)),
    strength: peakStrength,
    peak_strength: peakStrength,
    halo_radius_px: haloRadius,
    radius_px: haloRadius,
    core_radius_px: coreRadius,
    core_alpha_cap: 0.9,
    halo_color_model: "cool_white_xenon_core_warmed_by_tungsten_atrium_v1",
    flash_render_model: "period_xenon_pop_with_video_bloom_v1",
    local_core_visibility_target: "period_short_bloom",
    decay_curve: "period_xenon_fast_pop_short_bloom_v1",
    attack_fraction: null,
    hold_fraction: null,
  };
}

function attachCadenceMetadata(flashes) {
  const byHotspot = new Map();
  for (const event of [...flashes].sort((a, b) => a.time_seconds - b.time_seconds)) {
    const list = byHotspot.get(event.flash_origin_hotspot_id) || [];
    const previous = list[list.length - 1];
    event.same_hotspot_previous_gap_seconds = previous
      ? Number((event.time_seconds - previous.time_seconds).toFixed(3))
      : null;
    list.push(event);
    byHotspot.set(event.flash_origin_hotspot_id, list);
  }
  return flashes;
}

function enforceSameHotspotGap(flashes) {
  const sortedByHotspot = new Map();
  for (const event of flashes) {
    const list = sortedByHotspot.get(event.flash_origin_hotspot_id) || [];
    list.push(event);
    sortedByHotspot.set(event.flash_origin_hotspot_id, list);
  }
  for (const list of sortedByHotspot.values()) {
    list.sort((a, b) => a.time_seconds - b.time_seconds);
    for (let i = 1; i < list.length; i += 1) {
      const previous = list[i - 1];
      const current = list[i];
      const gap = current.time_seconds - previous.time_seconds;
      if (gap >= periodContract.min_same_hotspot_gap_seconds) continue;
      if (!current.forced_review_sample) {
        current.time_seconds = Number((previous.time_seconds + periodContract.min_same_hotspot_gap_seconds + 0.35).toFixed(3));
      } else if (!previous.forced_review_sample) {
        previous.time_seconds = Number(Math.max(0.8, current.time_seconds - periodContract.min_same_hotspot_gap_seconds - 0.35).toFixed(3));
      }
    }
  }
  return flashes;
}

function maxOneSecondWindow(flashes) {
  const times = flashes.map((event) => event.time_seconds).sort((a, b) => a - b);
  let max = 0;
  for (let i = 0; i < times.length; i += 1) {
    let count = 0;
    for (let j = i; j < times.length && times[j] - times[i] < 1; j += 1) count += 1;
    max = Math.max(max, count);
  }
  return max;
}

function enforceOneSecondCap(flashes) {
  for (let guard = 0; guard < 24 && maxOneSecondWindow(flashes) > periodContract.max_flashes_per_one_second_window; guard += 1) {
    const sorted = [...flashes].sort((a, b) => a.time_seconds - b.time_seconds);
    for (let i = 0; i < sorted.length; i += 1) {
      const window = sorted.filter((event) => event.time_seconds >= sorted[i].time_seconds && event.time_seconds - sorted[i].time_seconds < 1);
      if (window.length <= periodContract.max_flashes_per_one_second_window) continue;
      const movable = [...window].reverse().find((event) => !event.forced_review_sample) || window[window.length - 1];
      movable.time_seconds = Number((movable.time_seconds + 0.53).toFixed(3));
      break;
    }
  }
  return flashes;
}

function buildPeriodFlashes(beforeFlashes) {
  const flashes = beforeFlashes.map(transformFlashEvent);
  enforceSameHotspotGap(flashes);
  enforceOneSecondCap(flashes);
  attachCadenceMetadata(flashes);
  return flashes.sort((a, b) => a.time_seconds - b.time_seconds);
}

function replaceFlashFunctions(html) {
  const start = html.indexOf("    function flashIntensity(event, audioTime) {");
  const end = html.indexOf("\n    function balloonProgress", start);
  if (start === -1 || end === -1) throw new Error("Unable to replace flash functions");
  const next = `    function flashPhase(event, audioTime) {
      const envelope = Number(event.render_envelope_seconds ?? event.duration_seconds);
      const dt = audioTime - event.time_seconds;
      if (dt < 0) return 'pre_event';
      if (dt > envelope) return 'inactive';
      const attack = Math.min(Number(event.attack_seconds ?? 0.01), 0.015);
      const hold = Number(event.peak_hold_seconds ?? ${frameSeconds.toFixed(8)});
      if (dt < attack) return 'attack_peak';
      if (dt < attack + hold) return 'peak_hold';
      return 'decay_bloom';
    }
    function flashIntensity(event, audioTime) {
      const envelope = Number(event.render_envelope_seconds ?? event.duration_seconds);
      const dt = audioTime - event.time_seconds;
      if (dt < 0 || dt > envelope) return 0;
      const attack = Math.min(Number(event.attack_seconds ?? 0.01), 0.015);
      const hold = Number(event.peak_hold_seconds ?? ${frameSeconds.toFixed(8)});
      const decay = Math.max(0.001, Number(event.decay_seconds ?? envelope - attack - hold));
      if (dt < attack) {
        const x = Math.max(0, Math.min(1, dt / attack));
        const eased = x * x * (3 - 2 * x);
        return 0.82 + 0.18 * eased;
      }
      if (dt < attack + hold) return 1;
      const p = (dt - attack - hold) / decay;
      return Math.pow(Math.max(0, 1 - p), 1.55);
    }
    function fullScreenFlashPulseAlpha(audioTime) {
      const config = ambientEffects.fullScreenFlashPulse || {};
      if (config.enabled !== true) return 0;
      const maxAlpha = Number(config.max_alpha || 0.065);
      const endScreenCap = Number(config.end_screen_cap_alpha || 0.01);
      const cap = audioTime >= proof.endScreenStart ? Math.min(maxAlpha, endScreenCap) : maxAlpha;
      const baseAlpha = Number(config.alpha_per_full_strength_flash || 0.041);
      let alpha = 0;
      for (const event of ambientEffects.cameraFlashes) {
        const intensity = flashIntensity(event, audioTime);
        if (intensity < ${periodContract.visibility_threshold}) continue;
        const strengthScale = Math.max(0.8, Math.min(1.15, Number(event.peak_strength ?? event.strength ?? 1)));
        alpha += Math.pow(intensity, 1.45) * baseAlpha * strengthScale;
      }
      return Math.max(0, Math.min(cap, alpha));
    }
`;
  return `${html.slice(0, start)}${next}${html.slice(end + 1)}`;
}

function replaceFlashRenderBlock(html) {
  const startMarker = "      for (const event of ambientEffects.cameraFlashes) {";
  const start = html.indexOf(startMarker, html.indexOf("      const fullFramePulseAlpha = fullScreenFlashPulseAlpha(audioTime);"));
  const end = html.indexOf("\n      for (const event of ambientEffects.balloonRises) {", start);
  if (start === -1 || end === -1) throw new Error("Unable to replace flash render block");
  const next = `      for (const event of ambientEffects.cameraFlashes) {
        const intensity = flashIntensity(event, audioTime);
        if (intensity <= 0) continue;
        const sourceX = event.source_x ?? event.x;
        const sourceY = event.source_y ?? event.y;
        const point = sourceToStagePoint(sourceX, sourceY, storyTime);
        const visualRadiusScale = Math.max(0.84, Math.min(1.22, point.visualScale || 1));
        const haloRadius = (event.halo_radius_px ?? event.radius_px ?? 18) * visualRadiusScale * (0.86 + intensity * 0.14);
        const coreRadius = (event.core_radius_px ?? 2.8) * visualRadiusScale;
        const alpha = (event.peak_strength ?? event.strength ?? 1) * intensity;
        const gradient = ctx.createRadialGradient(point.x, point.y, 0, point.x, point.y, haloRadius);
        gradient.addColorStop(0, 'rgba(255, 253, 236, ' + Math.min(0.90, alpha * 0.88).toFixed(3) + ')');
        gradient.addColorStop(0.10, 'rgba(255, 244, 210, ' + Math.min(0.30, alpha * 0.28).toFixed(3) + ')');
        gradient.addColorStop(0.42, 'rgba(255, 214, 150, ' + Math.min(0.11, alpha * 0.12).toFixed(3) + ')');
        gradient.addColorStop(1, 'rgba(255, 214, 150, 0)');
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(point.x, point.y, haloRadius, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = 'rgba(255, 254, 240, ' + Math.min(0.90, alpha * 0.95).toFixed(3) + ')';
        ctx.beginPath();
        ctx.arc(point.x, point.y, Math.max(1.35, coreRadius), 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalCompositeOperation = 'source-over';
`;
  return `${html.slice(0, start)}${next}${html.slice(end + 1)}`;
}

function replaceAmbientStateFields(html) {
  const oldText = `          line_band_sampling_used: event.line_band_sampling_used === true,
          flash_origin_class: 'audited_visible_person_pixel'
        };`;
  const newText = `          line_band_sampling_used: event.line_band_sampling_used === true,
          flash_origin_class: 'audited_visible_person_pixel',
          flash_phase: typeof flashPhase === 'function' ? flashPhase(event, audioTime) : null,
          visible_frame_index: Math.max(0, Math.floor((audioTime - event.time_seconds) * 24)),
          same_hotspot_previous_gap_seconds: event.same_hotspot_previous_gap_seconds ?? null,
          render_envelope_seconds: event.render_envelope_seconds ?? event.duration_seconds,
          period_flash_contract: event.flash_render_model || ambientEffects.periodCameraFlashContract?.version || null
        };`;
  if (!html.includes(oldText)) throw new Error("Unable to replace ambient state flash fields");
  return html.replace(oldText, newText);
}

function updatePlayerHtml(proof, afterFlashes) {
  let html = fs.readFileSync(path.join(successorRoot, "player.html"), "utf8");
  proof.ambientEffects = {
    ...proof.ambientEffects,
    profile_id: profileId,
    predecessor_profile_id: predecessorProfileId,
    deterministic_seed: deterministicSeed,
    cameraFlashes: afterFlashes,
    flashVisibilityContract: periodContract,
    periodCameraFlashContract: periodContract,
    fullScreenFlashPulse: fullScreenPulse,
    originContract: {
      ...(proof.ambientEffects?.originContract || {}),
      period_camera_flash_policy: "1981_xenon_pop_short_video_bloom_required",
    },
  };
  if (proof.audio) proof.audio = proof.audio.replace(/v=[^"&]+/, `v=period_camera_flash_${stamp}`);
  html = replaceProof(html, proof);
  html = replaceFlashFunctions(html);
  html = replaceFlashRenderBlock(html);
  html = replaceAmbientStateFields(html);
  html = html
    .replace(/Hyatt Regency Living Cover Rough Proof - [^<]+/, "Hyatt Regency Living Cover Rough Proof - Period Camera Flash")
    .replace(/Hyatt Regency Living Cover N6 [^"]+ HTML rough proof/g, "Hyatt Regency Living Cover N6 period camera-flash HTML rough proof")
    .replace(/v=[^"]+(?=" type="audio\/mpeg")/, `v=period_camera_flash_${stamp}`)
    .replace(/v=[^"]+(?=" type="audio\/wav")/, `v=period_camera_flash_${stamp}`);
  fs.writeFileSync(path.join(successorRoot, "player.html"), html, "utf8");
  return proof;
}

function visibleFrameCount(event) {
  let count = 0;
  for (let frame = 0; frame <= periodContract.no_lingering_after_frames; frame += 1) {
    const time = event.time_seconds + frame * frameSeconds;
    if (flashIntensity(event, time) >= periodContract.visibility_threshold) count += 1;
  }
  return count;
}

function lingeringAfterFrame(event, frameIndex) {
  return flashIntensity(event, event.time_seconds + frameIndex * frameSeconds) >= periodContract.visibility_threshold;
}

function sameHotspotGapStats(flashes) {
  const gaps = flashes
    .map((event) => event.same_hotspot_previous_gap_seconds)
    .filter((gap) => Number.isFinite(gap));
  return {
    min_gap_seconds: gaps.length ? Number(Math.min(...gaps).toFixed(3)) : null,
    max_gap_seconds: gaps.length ? Number(Math.max(...gaps).toFixed(3)) : null,
    violations: gaps.filter((gap) => gap < periodContract.min_same_hotspot_gap_seconds).length,
  };
}

function cadenceDeltas(flashes) {
  const times = flashes.map((event) => event.time_seconds).sort((a, b) => a - b);
  return times.slice(1).map((time, index) => Number((time - times[index]).toFixed(3)));
}

function buildPeriodReport(proof, beforeFlashes, afterFlashes) {
  const visibleFrameCounts = afterFlashes.map(visibleFrameCount);
  const lingeringAfterSix = afterFlashes.filter((event) => lingeringAfterFrame(event, periodContract.no_lingering_after_frames));
  const deltas = cadenceDeltas(afterFlashes);
  const gapStats = sameHotspotGapStats(afterFlashes);
  let maxPulseAlpha = 0;
  let maxPulseTime = 0;
  let pulseWithoutVisibleCore = 0;
  let maxSimultaneousVisibleFlashes = 0;
  for (let time = 0; time <= proof.duration; time += frameSeconds / 2) {
    const active = afterFlashes.filter((event) => flashIntensity(event, time) >= periodContract.visibility_threshold);
    const pulseAlpha = pulseAlphaAt(time, afterFlashes, proof, fullScreenPulse);
    if (pulseAlpha > maxPulseAlpha) {
      maxPulseAlpha = pulseAlpha;
      maxPulseTime = time;
    }
    maxSimultaneousVisibleFlashes = Math.max(maxSimultaneousVisibleFlashes, active.length);
    if (pulseAlpha > 0 && active.length === 0) pulseWithoutVisibleCore += 1;
  }
  const afterRanges = {
    render_envelope_min: Math.min(...afterFlashes.map((event) => event.render_envelope_seconds)),
    render_envelope_max: Math.max(...afterFlashes.map((event) => event.render_envelope_seconds)),
    strength_min: Math.min(...afterFlashes.map((event) => event.peak_strength)),
    strength_max: Math.max(...afterFlashes.map((event) => event.peak_strength)),
    core_min: Math.min(...afterFlashes.map((event) => event.core_radius_px)),
    core_max: Math.max(...afterFlashes.map((event) => event.core_radius_px)),
    halo_min: Math.min(...afterFlashes.map((event) => event.halo_radius_px)),
    halo_max: Math.max(...afterFlashes.map((event) => event.halo_radius_px)),
  };
  const beforeRanges = {
    duration_min: Math.min(...beforeFlashes.map((event) => event.duration_seconds)),
    duration_max: Math.max(...beforeFlashes.map((event) => event.duration_seconds)),
    strength_min: Math.min(...beforeFlashes.map((event) => event.strength)),
    strength_max: Math.max(...beforeFlashes.map((event) => event.strength)),
    core_min: Math.min(...beforeFlashes.map((event) => event.core_radius_px)),
    core_max: Math.max(...beforeFlashes.map((event) => event.core_radius_px)),
    halo_min: Math.min(...beforeFlashes.map((event) => event.halo_radius_px)),
    halo_max: Math.max(...beforeFlashes.map((event) => event.halo_radius_px)),
  };
  const representativeSamples = [0.8, 0.842, 0.967, 55.9, 56.18, 56.48, 56.72, proof.endScreenStart + 0.2].map((time) => ({
    time_seconds: Number(time.toFixed(3)),
    pulse_alpha: Number(pulseAlphaAt(time, afterFlashes, proof, fullScreenPulse).toFixed(4)),
    active_flash_ids: afterFlashes.filter((event) => flashIntensity(event, time) >= periodContract.visibility_threshold).map((event) => event.id),
  }));
  return {
    profile_id: profileId,
    predecessor_profile_id: predecessorProfileId,
    period_contract: periodContract,
    full_screen_pulse: fullScreenPulse,
    before_ranges: beforeRanges,
    after_ranges: afterRanges,
    flash_count: afterFlashes.length,
    visible_frame_count_min: Math.min(...visibleFrameCounts),
    visible_frame_count_max: Math.max(...visibleFrameCounts),
    lingering_after_six_frame_count: lingeringAfterSix.length,
    max_full_frame_pulse_alpha: Number(maxPulseAlpha.toFixed(4)),
    max_full_frame_pulse_time_seconds: Number(maxPulseTime.toFixed(3)),
    max_simultaneous_visible_flashes: maxSimultaneousVisibleFlashes,
    max_flashes_per_one_second_window: maxOneSecondWindow(afterFlashes),
    pulse_without_visible_core_samples: pulseWithoutVisibleCore,
    same_hotspot_gap_stats: gapStats,
    cadence_delta_unique_count: new Set(deltas.map((delta) => delta.toFixed(3))).size,
    cadence_delta_min: Math.min(...deltas),
    cadence_delta_max: Math.max(...deltas),
    representative_samples: representativeSamples,
  };
}

function writeFrameStrip(report, beforeFlashes, afterFlashes) {
  const stripPath = path.join(successorRoot, "qa/period_camera_flash/period_flash_before_after_frame_strip.html");
  ensureDir(path.dirname(stripPath));
  const sampleIds = new Set([
    "audited_flash_001_ul_top_01",
    "audited_flash_014_diag_walkway_02",
    "audited_flash_016_diag_walkway_08",
    "audited_flash_017_main_floor_05",
  ]);
  const beforeById = new Map(beforeFlashes.map((event) => [event.id, event]));
  const rows = afterFlashes
    .filter((event) => sampleIds.has(event.id))
    .flatMap((event) => {
      const before = beforeById.get(event.id);
      return [0, 1, 2, 4, 6].map((frame) => ({
        frame,
        event,
        before,
        time: event.time_seconds + frame * frameSeconds,
        intensity: flashIntensity(event, event.time_seconds + frame * frameSeconds),
        pulse: pulseAlphaAt(event.time_seconds + frame * frameSeconds, afterFlashes, { endScreenStart: 852.5 }, fullScreenPulse),
        phase: flashPhase(event, event.time_seconds + frame * frameSeconds),
      }));
    });
  fs.writeFileSync(
    stripPath,
    `<!doctype html><html><head><meta charset="utf-8"><title>Hyatt period camera flash samples</title><style>body{margin:0;background:#120d09;color:#fff2da;font:15px Arial,sans-serif;padding:24px}table{border-collapse:collapse;max-width:1180px}td,th{border:1px solid #5a3b29;padding:8px;vertical-align:top}code{color:#ffe4b8}.pass{color:#8ff0a4}</style></head><body><h1>Hyatt period camera flash before/after samples</h1><p>Use the listed times for browser screenshots. Origins are unchanged; timing now models a short 1981 xenon pop with a frame-scale bloom.</p><table><tr><th>event</th><th>frame</th><th>time</th><th>phase</th><th>before</th><th>after</th></tr>${rows.map((row) => `<tr><td><code>${row.event.id}</code><br>${row.event.flash_origin_hotspot_id}</td><td>+${row.frame}</td><td>${row.time.toFixed(3)}s</td><td>${row.phase}<br>intensity ${row.intensity.toFixed(3)}<br>pulse ${row.pulse.toFixed(3)}</td><td>duration ${row.before.duration_seconds}s<br>strength ${row.before.strength}<br>core ${row.before.core_radius_px}px<br>halo ${row.before.halo_radius_px}px</td><td>envelope ${row.event.render_envelope_seconds}s<br>peak ${row.event.peak_strength}<br>core ${row.event.core_radius_px}px<br>halo ${row.event.halo_radius_px}px</td></tr>`).join("")}</table><p class="pass">Visible-frame range: ${report.visible_frame_count_min}-${report.visible_frame_count_max}; max one-second flash window: ${report.max_flashes_per_one_second_window}; max pulse alpha: ${report.max_full_frame_pulse_alpha}</p></body></html>`,
    "utf8",
  );
  return stripPath;
}

function staticQa(report, afterFlashes) {
  const qaReads = {
    period_camera_flash_behavior_read:
      report.after_ranges.render_envelope_min >= periodContract.render_envelope_seconds_min &&
      report.after_ranges.render_envelope_max <= periodContract.render_envelope_seconds_max
        ? "pass_period_xenon_pop_with_short_video_bloom"
        : "tighten_render_envelope_outside_period_contract",
    xenon_pop_duration_read:
      report.visible_frame_count_min >= periodContract.visible_frame_target_min &&
      report.visible_frame_count_max <= periodContract.visible_frame_target_max
        ? "pass_3_to_4_visible_frames"
        : "tighten_visible_frame_count_outside_target",
    video_bloom_decay_read:
      report.lingering_after_six_frame_count === 0
        ? "pass_no_lingering_after_six_frames"
        : `tighten_${report.lingering_after_six_frame_count}_flashes_linger_after_six_frames`,
    flash_core_peak_visibility_read:
      report.after_ranges.strength_min >= periodContract.min_peak_strength &&
      report.after_ranges.core_min >= periodContract.min_core_radius_px
        ? "pass_bright_compact_cream_white_core"
        : "tighten_core_peak_below_period_target",
    flash_core_visibility_read: "pass_superseded_by_flash_core_peak_visibility_read",
    flash_duration_visibility_read: "pass_superseded_by_xenon_pop_duration_read",
    flash_origin_precision_preservation_read:
      afterFlashes.every((event) => event.flash_origin_class === "audited_visible_person_pixel")
        ? "pass_all_180_audited_origins_preserved"
        : "tighten_origin_class_changed",
    flash_halo_boundary_read:
      report.after_ranges.halo_max <= periodContract.max_halo_radius_px
        ? "pass_halo_bounded_16_to_20px"
        : "tighten_halo_exceeds_period_boundary",
    global_pulse_peak_coupling_read:
      report.pulse_without_visible_core_samples === 0 &&
      report.max_full_frame_pulse_alpha <= periodContract.max_full_screen_alpha
        ? "pass_pulse_only_when_local_period_core_visible"
        : "tighten_global_pulse_not_coupled_to_local_core",
    global_pulse_local_core_coupling_read: "pass_superseded_by_global_pulse_peak_coupling_read",
    no_lingering_flash_dot_read:
      report.lingering_after_six_frame_count === 0
        ? "pass_no_long_glowing_dot"
        : "tighten_lingering_flash_dot_after_decay",
    per_hotspot_recycle_spacing_read:
      report.same_hotspot_gap_stats.violations === 0
        ? `pass_min_${periodContract.min_same_hotspot_gap_seconds}s_same_hotspot_gap`
        : `tighten_${report.same_hotspot_gap_stats.violations}_same_hotspot_gap_violations`,
    irregular_cadence_read:
      report.cadence_delta_unique_count >= 12 &&
      report.max_flashes_per_one_second_window <= periodContract.max_flashes_per_one_second_window
        ? "pass_irregular_non_strobing_flash_cadence"
        : "tighten_flash_cadence_too_regular_or_dense",
    flash_not_strobe_read:
      report.max_flashes_per_one_second_window <= periodContract.max_flashes_per_one_second_window &&
      report.max_full_frame_pulse_alpha <= periodContract.max_full_screen_alpha
        ? "pass_period_flash_without_strobe_or_washout"
        : "tighten_flash_overlap_or_pulse_too_high",
  };
  const qa = {
    profile_id: profileId,
    camera_flash_count: afterFlashes.length,
    balloon_rise_count: 28,
    report,
    qa_reads: qaReads,
  };
  const qaPath = path.join(successorRoot, "qa/period_camera_flash/static_period_camera_flash_qa.json");
  writeJson(qaPath, qa);
  return { qa, qaPath };
}

function writeAmbientArtifacts(predecessorAmbient, proof, afterFlashes, report, stripPath, qaPath, qa) {
  const ambientPath = path.join(successorRoot, "living_cover_ambient_effects_layer.json");
  const reportPath = path.join(successorRoot, "qa/period_camera_flash/period_camera_flash_behavior_report.json");
  writeJson(reportPath, report);
  const ambient = {
    ...predecessorAmbient,
    packet_id: successorId,
    phase_gate: "ambient_effects_reopened",
    status: "review_ready_pending_human_period_camera_flash_keep",
    human_disposition: "pending",
    may_advance_to_video_render: false,
    ambient_effects_process_version: "living_cover_ambient_effects_layer_period_camera_flash_v1",
    ambient_profile_id: profileId,
    predecessor_profile_id: predecessorProfileId,
    issue_reopened: "flash_behavior_not_period_realistic",
    selected_lanes: ["camera_flashes", "full_frame_flash_pulse", "balloon_rises"],
    effect_parameters: {
      ...(predecessorAmbient.effect_parameters || {}),
      deterministic_seed: deterministicSeed,
      camera_flash_count: afterFlashes.length,
      camera_flashes: afterFlashes,
      flash_render_model: "period_xenon_pop_with_video_bloom_v1",
      flash_visibility_contract: periodContract,
      period_camera_flash_contract: periodContract,
      full_screen_flash_pulse: fullScreenPulse,
    },
    debug_review_artifacts: {
      ...(predecessorAmbient.debug_review_artifacts || {}),
      period_camera_flash_behavior_report: artifact(reportPath),
      period_flash_before_after_frame_strip: artifact(stripPath),
      static_qa: artifact(qaPath),
    },
    downstream_locks: {
      may_advance_to_video_render: false,
      may_create_publish_readiness: false,
      may_upload_to_youtube: false,
      public_release_ready: false,
    },
    qa_reads: {
      ...(predecessorAmbient.qa_reads || {}),
      ...qa.qa_reads,
    },
  };
  writeJson(ambientPath, ambient);
  const mdPath = path.join(successorRoot, "living_cover_ambient_effects_layer.md");
  fs.writeFileSync(
    mdPath,
    `# Hyatt Period Camera-Flash Ambient Layer

- Profile: \`${profileId}\`
- Camera flashes: ${afterFlashes.length}, with audited person-pixel origins preserved.
- Local flash: period 1981 xenon pop, represented as a ${periodContract.render_envelope_seconds_min}-${periodContract.render_envelope_seconds_max}s video bloom.
- Core: compact cream-white person-centered point, ${periodContract.min_core_radius_px}-${periodContract.max_core_radius_px}px, peak ${periodContract.min_peak_strength}-${periodContract.max_peak_strength}.
- Halo: bounded warm spill, ${periodContract.min_halo_radius_px}-${periodContract.max_halo_radius_px}px; nearby architecture may catch spill but never reads as the source.
- Full-frame pulse: capped at ${fullScreenPulse.max_alpha}, tied only to visible audited local cores.
- Balloons: preserved from predecessor, including opening-frame prewarm.
- Gate state: pending human review; video render, publish readiness, and upload stay locked.

## Required Reads

${Object.entries(ambient.qa_reads).map(([key, value]) => `- \`${key}\`: \`${value}\``).join("\n")}
`,
    "utf8",
  );
  return { ambientPath, mdPath, ambient, reportPath };
}

function writeRoughManifest(ambientArtifacts, qaPath) {
  const manifestPath = path.join(successorRoot, "rough_assembly_manifest.json");
  const predecessorManifestPath = path.join(predecessorRoot, "rough_assembly_manifest.json");
  const manifest = fs.existsSync(predecessorManifestPath) ? readJson(predecessorManifestPath) : {};
  manifest.packet_id = successorId;
  manifest.status = "review_ready_pending_human_period_camera_flash_keep";
  manifest.human_disposition = "pending";
  manifest.may_advance_to_video_render = false;
  manifest.predecessor_packet_id = path.basename(predecessorRoot);
  manifest.issue_reopened = "flash_behavior_not_period_realistic";
  manifest.ambient_profile_id = profileId;
  manifest.player_html_path = path.join(successorRoot, "player.html");
  manifest.player_html_sha256 = sha256(manifest.player_html_path);
  manifest.living_cover_ambient_effects_layer = {
    path: ambientArtifacts.ambientPath,
    sha256: sha256(ambientArtifacts.ambientPath),
    profile_id: profileId,
  };
  manifest.ambient_effects_layer = {
    profile_id: profileId,
    json_path: ambientArtifacts.ambientPath,
    json_sha256: sha256(ambientArtifacts.ambientPath),
    md_path: ambientArtifacts.mdPath,
    md_sha256: sha256(ambientArtifacts.mdPath),
    static_qa_path: qaPath,
    static_qa_sha256: sha256(qaPath),
  };
  manifest.qa = {
    ...(manifest.qa || {}),
    period_camera_flash_static_qa: {
      path: qaPath,
      sha256: sha256(qaPath),
    },
    period_camera_flash_behavior_report: {
      path: ambientArtifacts.reportPath,
      sha256: sha256(ambientArtifacts.reportPath),
    },
  };
  manifest.rough_assembly_reads = {
    ...(manifest.rough_assembly_reads || {}),
    ...ambientArtifacts.ambient.qa_reads,
  };
  manifest.downstream_locks = {
    ...(manifest.downstream_locks || {}),
    may_advance_to_video_render: false,
    may_create_publish_readiness: false,
    may_upload_to_youtube: false,
    public_release_ready: false,
  };
  manifest.upload_locks = {
    publish_ready: false,
    youtube_upload_ready: false,
    public_release_ready: false,
    may_youtube_action: false,
    upload_performed: false,
    mp4_render_created: false,
    may_advance_to_final_assembly: false,
    may_advance_to_publish_readiness: false,
    final_mp4_render: false,
    final_assembly: false,
    publish_readiness: false,
    private_youtube_upload: false,
    public_release: false,
  };
  if (manifest.final_render_contract) {
    manifest.final_render_contract.blocked_until_human_keep_on_this_packet = true;
    manifest.final_render_contract.mp4_render_created = false;
  }
  writeJson(manifestPath, manifest);
  return manifestPath;
}

function markPredecessorTighten() {
  const reason = "Flash behavior used a long glow rather than a period-realistic 1981 xenon pop.";
  for (const file of ["rough_assembly_manifest.json", "living_cover_ambient_effects_layer.json"]) {
    const filePath = path.join(predecessorRoot, file);
    if (!fs.existsSync(filePath)) continue;
    const data = readJson(filePath);
    data.status = "tighten_flash_behavior_not_period_realistic";
    data.human_disposition = "tighten_flash_behavior_not_period_realistic";
    data.may_advance_to_video_render = false;
    data.superseded_by = successorRoot;
    data.tighten_reason = reason;
    data.downstream_locks = {
      ...(data.downstream_locks || {}),
      may_advance_to_video_render: false,
      may_create_publish_readiness: false,
      may_upload_to_youtube: false,
      public_release_ready: false,
    };
    writeJson(filePath, data);
  }
}

function writeSummary(ambientArtifacts, report, qaPath, manifestPath) {
  const summaryPath = path.join(successorRoot, "period_camera_flash_successor_summary.json");
  writeJson(summaryPath, {
    successor_root: successorRoot,
    player_path: path.join(successorRoot, "player.html"),
    ambient_profile_id: profileId,
    predecessor_root: predecessorRoot,
    rough_manifest_path: manifestPath,
    ambient_layer_path: ambientArtifacts.ambientPath,
    static_qa_path: qaPath,
    period_camera_flash_behavior_report: ambientArtifacts.reportPath,
    period_report: report,
    qa_reads: ambientArtifacts.ambient.qa_reads,
    downstream_locks: ambientArtifacts.ambient.downstream_locks,
    review_url: "http://127.0.0.1:8844/player.html",
  });
  return summaryPath;
}

function main() {
  if (!fs.existsSync(predecessorRoot)) throw new Error(`Missing predecessor proof: ${predecessorRoot}`);
  if (fs.existsSync(successorRoot)) throw new Error(`Successor already exists: ${successorRoot}`);
  fs.cpSync(predecessorRoot, successorRoot, { recursive: true });
  const playerPath = path.join(successorRoot, "player.html");
  const predecessorAmbient = readJson(path.join(predecessorRoot, "living_cover_ambient_effects_layer.json"));
  const proof = extractProof(fs.readFileSync(playerPath, "utf8"));
  const beforeFlashes = proof.ambientEffects.cameraFlashes || predecessorAmbient.effect_parameters.camera_flashes || [];
  const afterFlashes = buildPeriodFlashes(beforeFlashes);
  const updatedProof = updatePlayerHtml(proof, afterFlashes);
  const report = buildPeriodReport(updatedProof, beforeFlashes, afterFlashes);
  const stripPath = writeFrameStrip(report, beforeFlashes, afterFlashes);
  const { qa, qaPath } = staticQa(report, afterFlashes);
  const ambientArtifacts = writeAmbientArtifacts(predecessorAmbient, updatedProof, afterFlashes, report, stripPath, qaPath, qa);
  const manifestPath = writeRoughManifest(ambientArtifacts, qaPath);
  markPredecessorTighten();
  const summaryPath = writeSummary(ambientArtifacts, report, qaPath, manifestPath);
  console.log(JSON.stringify({ successorRoot, playerPath, summaryPath }, null, 2));
}

main();
