#!/usr/bin/env node
import fs from "node:fs";

function usage() {
  console.error("Usage: node scripts/validate_living_cover_ambient_effects_layer.mjs --ambient-layer <path>");
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
  if (!args["ambient-layer"]) usage();
  return args;
}

function readPasses(value) {
  return value === true || (typeof value === "string" && value.startsWith("pass"));
}

function pointInPolygon(point, polygon) {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i][0];
    const yi = polygon[i][1];
    const xj = polygon[j][0];
    const yj = polygon[j][1];
    const intersects =
      yi > point.y !== yj > point.y &&
      point.x < ((xj - xi) * (point.y - yi)) / ((yj - yi) || 1e-9) + xi;
    if (intersects) inside = !inside;
  }
  return inside;
}

function pointInMask(point, mask) {
  if (!mask) return false;
  if (mask.kind === "polygon") return pointInPolygon(point, mask.points || []);
  if (mask.kind === "ellipse") {
    const dx = (point.x - mask.center[0]) / mask.radius_x_px;
    const dy = (point.y - mask.center[1]) / mask.radius_y_px;
    return dx * dx + dy * dy <= 1.0001;
  }
  if (mask.kind === "rect") {
    return point.x >= mask.x && point.x <= mask.x + mask.width && point.y >= mask.y && point.y <= mask.y + mask.height;
  }
  return false;
}

function requireRead(reads, key) {
  if (!readPasses(reads?.[key])) throw new Error(`Missing passing ${key}: ${reads?.[key] || "(missing)"}`);
}

function balloonProgress(event, audioTime) {
  const p = (audioTime - event.start_seconds) / event.duration_seconds;
  if (p < 0 || p > 1) return null;
  return Math.max(0, Math.min(1, p));
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function smoothstep(t) {
  const x = clamp(t, 0, 1);
  return x * x * (3 - 2 * x);
}

function periodFlashIntensity(event, audioTime) {
  const frameSeconds = 1 / 24;
  const envelope = Number(event.render_envelope_seconds ?? event.duration_seconds);
  const dt = audioTime - event.time_seconds;
  if (dt < 0 || dt > envelope) return 0;
  const attack = Math.min(Number(event.attack_seconds ?? 0.01), 0.015);
  const hold = Number(event.peak_hold_seconds ?? frameSeconds);
  const decay = Math.max(0.001, Number(event.decay_seconds ?? envelope - attack - hold));
  if (dt < attack) return 0.82 + 0.18 * smoothstep(dt / attack);
  if (dt < attack + hold) return 1;
  const p = (dt - attack - hold) / decay;
  return Math.pow(Math.max(0, 1 - p), 1.55);
}

function periodVisibleFrameCount(event, threshold) {
  let count = 0;
  for (let frame = 0; frame <= 6; frame += 1) {
    const time = Number(event.time_seconds) + frame / 24;
    if (periodFlashIntensity(event, time) >= threshold) count += 1;
  }
  return count;
}

function maxOneSecondWindow(flashes) {
  const times = flashes.map((event) => Number(event.time_seconds)).sort((a, b) => a - b);
  let max = 0;
  for (let i = 0; i < times.length; i += 1) {
    let count = 0;
    for (let j = i; j < times.length && times[j] - times[i] < 1; j += 1) count += 1;
    max = Math.max(max, count);
  }
  return max;
}

function sameHotspotGapViolations(flashes, minimumGapSeconds) {
  const byHotspot = new Map();
  for (const flash of flashes) {
    const list = byHotspot.get(flash.flash_origin_hotspot_id) || [];
    list.push(flash);
    byHotspot.set(flash.flash_origin_hotspot_id, list);
  }
  const violations = [];
  for (const [hotspotId, list] of byHotspot.entries()) {
    list.sort((a, b) => Number(a.time_seconds) - Number(b.time_seconds));
    for (let i = 1; i < list.length; i += 1) {
      const gap = Number(list[i].time_seconds) - Number(list[i - 1].time_seconds);
      if (gap < minimumGapSeconds) violations.push({ hotspotId, previous: list[i - 1].id, current: list[i].id, gap });
    }
  }
  return violations;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const manifest = JSON.parse(fs.readFileSync(args["ambient-layer"], "utf8"));
  const parameters = manifest.effect_parameters || {};
  const reads = manifest.qa_reads || {};
  const flashes = parameters.camera_flashes || [];
  const balloons = parameters.balloon_rises || [];
  const hotspots = parameters.flash_origin_hotspots || [];
  const exclusions = parameters.flash_exclusion_masks || [];
  const visibilityContract = parameters.flash_visibility_contract || {};
  const maxHaloRadius = Number(visibilityContract.max_halo_radius_px ?? 26);
  const maxCoreRadius = Number(visibilityContract.max_core_radius_px ?? 2.8);
  const hotspotById = new Map(hotspots.map((hotspot) => [hotspot.id, hotspot]));

  if (!Array.isArray(flashes) || flashes.length === 0) throw new Error("Ambient layer has no camera_flashes array");
  if (!Array.isArray(hotspots) || hotspots.length === 0) throw new Error("Camera flashes require flash_origin_hotspots");
  if (parameters.broad_region_sampling_used === true || parameters.line_band_sampling_used === true) {
    throw new Error("Person-operated flash layer cannot use broad region or line-band sampling");
  }
  if (parameters.people_standing_flash_masks || parameters.marked_flash_regions) {
    throw new Error("Person-operated flash layer still exposes broad mask/marked region origin sampling");
  }

  const failures = [];
  for (const flash of flashes) {
    const hotspot = hotspotById.get(flash.flash_origin_hotspot_id);
    const point = { x: flash.source_x ?? flash.x, y: flash.source_y ?? flash.y };
    if (!hotspot) failures.push(`${flash.id}: missing audited hotspot ${flash.flash_origin_hotspot_id}`);
    if (hotspot && hotspot.surface_read !== "visible_person") failures.push(`${flash.id}: hotspot surface is ${hotspot.surface_read}`);
    if (flash.origin_core_surface !== "visible_person" || flash.surface_read !== "visible_person") {
      failures.push(`${flash.id}: origin core surface is not visible_person`);
    }
    if (flash.broad_mask_sampling_used === true || flash.line_band_sampling_used === true) {
      failures.push(`${flash.id}: broad/line-band sampling flag is true`);
    }
    const jitterDistance = Math.hypot(flash.jitter_x_px || 0, flash.jitter_y_px || 0);
    const allowedJitter = Number(flash.allowed_jitter_px ?? hotspot?.allowed_jitter_px ?? 0);
    if (!(jitterDistance <= allowedJitter + 0.001)) {
      failures.push(`${flash.id}: jitter ${jitterDistance.toFixed(3)} exceeds ${allowedJitter}`);
    }
    const hits = exclusions.filter((mask) => pointInMask(point, mask)).map((mask) => mask.id);
    if (hits.length > 0) failures.push(`${flash.id}: origin hits exclusions ${hits.join(",")}`);
    if (Number(flash.halo_radius_px || flash.radius_px || 0) > maxHaloRadius) failures.push(`${flash.id}: halo radius too large`);
    if (Number(flash.core_radius_px || 0) > maxCoreRadius) failures.push(`${flash.id}: core radius too large`);
  }
  if (failures.length > 0) throw new Error(`Ambient flash origin validation failed:\n${failures.join("\n")}`);

  for (const read of [
    "audited_person_pixel_origin_read",
    "slab_face_origin_rejection_read",
    "walkway_fascia_origin_rejection_read",
    "flash_core_on_person_surface_read",
    "flash_halo_not_origin_read",
    "audited_hotspot_contact_sheet_read",
    "ambient_density_preservation_read",
    "debug_overlay_absence_read",
    "broad_region_sampling_rejection_read",
    "flash_jitter_limit_read",
    "source_locked_ambient_transform_read",
  ]) {
    requireRead(reads, read);
  }

  if (parameters.active_from_start_balloon_prewarm === true) {
    const activeAtZero = balloons.filter((event) => balloonProgress(event, 0) !== null);
    const prewarmed = balloons.filter((event) => event.prewarmed_at_t0 === true && Number(event.start_seconds) < 0);
    if (balloons.length !== 28) throw new Error(`Expected preserved 28 balloon rises, found ${balloons.length}`);
    if (activeAtZero.length < 3) throw new Error(`Expected at least 3 active balloons at t=0, found ${activeAtZero.length}`);
    if (prewarmed.length < 3) throw new Error(`Expected at least 3 prewarmed negative-start balloons, found ${prewarmed.length}`);
    for (const read of [
      "balloon_effect_initial_frame_read",
      "balloon_prewarm_origin_read",
      "balloon_count_preservation_read",
    ]) {
      requireRead(reads, read);
    }
  }

  if (parameters.full_screen_flash_pulse) {
    const pulse = parameters.full_screen_flash_pulse;
    if (pulse.enabled !== true) throw new Error("full_screen_flash_pulse exists but is not enabled");
    if (pulse.source !== "audited_camera_flashes_only") {
      throw new Error(`full_screen_flash_pulse source must be audited_camera_flashes_only, found ${pulse.source}`);
    }
    if (Number(pulse.max_alpha) > 0.075) throw new Error(`full_screen_flash_pulse max_alpha ${pulse.max_alpha} exceeds 0.075`);
    if (Number(pulse.end_screen_cap_alpha) > Number(pulse.max_alpha)) {
      throw new Error("full_screen_flash_pulse end_screen_cap_alpha cannot exceed max_alpha");
    }
    for (const read of [
      "fullscreen_flash_pulse_read",
      "flash_pulse_subtlety_read",
      "flash_core_origin_preservation_read",
      "audited_flash_origin_preservation_read",
      "end_screen_flash_pulse_suppression_read",
    ]) {
      requireRead(reads, read);
    }
  }

  if (visibilityContract.target === "period_1981_xenon_pop") {
    const threshold = Number(visibilityContract.visibility_threshold ?? 0.16);
    const minimumEnvelope = Number(visibilityContract.render_envelope_seconds_min ?? 0.125);
    const maximumEnvelope = Number(visibilityContract.render_envelope_seconds_max ?? 0.167);
    const minimumPeakStrength = Number(visibilityContract.min_peak_strength ?? 0.92);
    const maximumPeakStrength = Number(visibilityContract.max_peak_strength ?? 1.08);
    const minimumCoreRadius = Number(visibilityContract.min_core_radius_px ?? 2.6);
    const maximumCoreRadius = Number(visibilityContract.max_core_radius_px ?? 3.2);
    const maximumHaloRadius = Number(visibilityContract.max_halo_radius_px ?? 20);
    const minimumGap = Number(visibilityContract.min_same_hotspot_gap_seconds ?? 8);
    const maxWindowCount = Number(visibilityContract.max_flashes_per_one_second_window ?? 3);
    const frameMin = Number(visibilityContract.visible_frame_target_min ?? 3);
    const frameMax = Number(visibilityContract.visible_frame_target_max ?? 4);
    const contractFailures = [];
    for (const flash of flashes) {
      const envelope = Number(flash.render_envelope_seconds ?? flash.duration_seconds);
      const attack = Number(flash.attack_seconds ?? 0);
      const hold = Number(flash.peak_hold_seconds ?? 0);
      const decay = Number(flash.decay_seconds ?? 0);
      const peakStrength = Number(flash.peak_strength ?? flash.strength);
      const visibleFrames = periodVisibleFrameCount(flash, threshold);
      if (flash.flash_render_model !== "period_xenon_pop_with_video_bloom_v1") {
        contractFailures.push(`${flash.id}: flash_render_model ${flash.flash_render_model}`);
      }
      if (Number(flash.physical_flash_duration_seconds_reference) > 0.005) {
        contractFailures.push(`${flash.id}: missing/large physical flash duration reference`);
      }
      if (envelope < minimumEnvelope || envelope > maximumEnvelope) {
        contractFailures.push(`${flash.id}: render envelope ${envelope} outside ${minimumEnvelope}-${maximumEnvelope}`);
      }
      if (attack > Number(visibilityContract.attack_seconds_max ?? 0.015)) {
        contractFailures.push(`${flash.id}: attack ${attack} too slow`);
      }
      if (Math.abs(hold - Number(visibilityContract.peak_hold_seconds ?? 1 / 24)) > 0.004) {
        contractFailures.push(`${flash.id}: peak hold ${hold} is not frame-scale`);
      }
      if (decay < Number(visibilityContract.decay_seconds_min ?? 0.07) || decay > Number(visibilityContract.decay_seconds_max ?? 0.11)) {
        contractFailures.push(`${flash.id}: decay ${decay} outside target`);
      }
      if (visibleFrames < frameMin || visibleFrames > frameMax) {
        contractFailures.push(`${flash.id}: visible frame count ${visibleFrames} outside ${frameMin}-${frameMax}`);
      }
      if (periodFlashIntensity(flash, Number(flash.time_seconds) + 6 / 24) >= threshold) {
        contractFailures.push(`${flash.id}: lingering after six frames`);
      }
      if (peakStrength < minimumPeakStrength || peakStrength > maximumPeakStrength) {
        contractFailures.push(`${flash.id}: peak strength ${peakStrength} outside target`);
      }
      if (Number(flash.core_radius_px) < minimumCoreRadius || Number(flash.core_radius_px) > maximumCoreRadius) {
        contractFailures.push(`${flash.id}: core radius ${flash.core_radius_px} outside target`);
      }
      if (Number(flash.halo_radius_px) > maximumHaloRadius) {
        contractFailures.push(`${flash.id}: halo radius ${flash.halo_radius_px} exceeds target`);
      }
    }
    const gapViolations = sameHotspotGapViolations(flashes, minimumGap);
    if (gapViolations.length) contractFailures.push(`${gapViolations.length} same-hotspot recycle gap violations`);
    const windowCount = maxOneSecondWindow(flashes);
    if (windowCount > maxWindowCount) contractFailures.push(`one-second flash window count ${windowCount} exceeds ${maxWindowCount}`);
    if (parameters.full_screen_flash_pulse && Number(parameters.full_screen_flash_pulse.max_alpha) > Number(visibilityContract.max_full_screen_alpha ?? 0.065)) {
      contractFailures.push(`full-screen pulse max_alpha ${parameters.full_screen_flash_pulse.max_alpha} exceeds period cap`);
    }
    if (contractFailures.length) {
      throw new Error(`Period camera flash validation failed:\n${contractFailures.join("\n")}`);
    }
    for (const read of [
      "period_camera_flash_behavior_read",
      "xenon_pop_duration_read",
      "video_bloom_decay_read",
      "flash_core_peak_visibility_read",
      "flash_origin_precision_preservation_read",
      "flash_halo_boundary_read",
      "global_pulse_peak_coupling_read",
      "no_lingering_flash_dot_read",
      "per_hotspot_recycle_spacing_read",
      "irregular_cadence_read",
      "flash_not_strobe_read",
    ]) {
      requireRead(reads, read);
    }
  }

  if (visibilityContract.target === "more_pronounced") {
    if (!readPasses(reads.human_approved_stylized_long_flash_override_read)) {
      throw new Error("more_pronounced half-second camera flashes require human_approved_stylized_long_flash_override_read");
    }
    const weakFlashes = flashes.filter((flash) => Number(flash.strength) < 0.74 || Number(flash.strength) > 0.92);
    const shortFlashes = flashes.filter((flash) => Number(flash.duration_seconds) < 0.46 || Number(flash.duration_seconds) > 0.62);
    const smallCores = flashes.filter((flash) => Number(flash.core_radius_px) < 3.0 || Number(flash.core_radius_px) > maxCoreRadius);
    if (weakFlashes.length) throw new Error(`${weakFlashes.length} flashes outside more-pronounced strength range`);
    if (shortFlashes.length) throw new Error(`${shortFlashes.length} flashes outside more-pronounced duration range`);
    if (smallCores.length) throw new Error(`${smallCores.length} flashes outside more-pronounced core range`);
    for (const read of [
      "flash_core_visibility_read",
      "flash_duration_visibility_read",
      "flash_origin_precision_preservation_read",
      "flash_halo_boundary_read",
      "global_pulse_local_core_coupling_read",
      "flash_not_strobe_read",
    ]) {
      requireRead(reads, read);
    }
  }

  console.log(JSON.stringify({
    status: "pass",
    ambient_profile_id: manifest.ambient_profile_id,
    camera_flashes: flashes.length,
    audited_hotspots: hotspots.length,
    exclusions: exclusions.length,
    balloon_rises: balloons.length,
  }, null, 2));
}

main();
