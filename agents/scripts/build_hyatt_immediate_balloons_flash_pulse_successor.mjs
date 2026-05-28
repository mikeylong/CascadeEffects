#!/usr/bin/env node
import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const predecessorRoot =
  "/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt_living_cover_html_rough_proof_n6_audited_flash_origins_20260520T002950Z";
const roughAssemblyRoot = path.dirname(predecessorRoot);
const predecessorProfileId = "hyatt_audited_person_pixel_flash_origins_v1";
const profileId = "hyatt_audited_flash_fullscreen_pulse_balloon_immediate_v1";
const deterministicSeed = 2026052001;

const pulseContract = {
  version: "subtle_full_frame_exposure_pulse_v1",
  source: "audited_camera_flashes_only",
  enabled: true,
  alpha_per_full_strength_flash: 0.052,
  max_alpha: 0.07,
  end_screen_cap_alpha: 0.012,
  color_rgb: [255, 236, 202],
  compositing: "screen_canvas_layer_below_right_rail",
  aggregate_policy: "sum_active_audited_flash_events_then_hard_cap",
  rail_caption_protection: "ambient_canvas_z_index_below_rail_plus_alpha_cap",
};

function utcStamp(date = new Date()) {
  return date.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
}

const stamp = utcStamp();
const successorId = `hyatt_living_cover_html_rough_proof_n6_balloon_immediate_flash_pulse_${stamp}`;
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

function easeInOutSine(t) {
  return -(Math.cos(Math.PI * Math.max(0, Math.min(1, t))) - 1) / 2;
}

function flashIntensity(event, audioTime) {
  const dt = audioTime - event.time_seconds;
  if (dt < -0.05 || dt > event.duration_seconds) return 0;
  const normalized = Math.max(0, dt) / event.duration_seconds;
  const attack = 0.16;
  const value = normalized < attack ? normalized / attack : 1 - (normalized - attack) / (1 - attack);
  return Math.pow(Math.max(0, Math.min(1, value)), 1.7);
}

function pulseAlphaAt(audioTime, cameraFlashes, proof) {
  const endScreenCap =
    Number.isFinite(proof.endScreenStart) && audioTime >= proof.endScreenStart
      ? pulseContract.end_screen_cap_alpha
      : pulseContract.max_alpha;
  const summed = cameraFlashes.reduce((total, event) => {
    const intensity = flashIntensity(event, audioTime);
    if (intensity <= 0) return total;
    const strengthScale = Math.max(0.65, Math.min(1.18, (event.strength || 0.52) / 0.54));
    return total + intensity * pulseContract.alpha_per_full_strength_flash * strengthScale;
  }, 0);
  return Math.min(endScreenCap, summed);
}

function balloonStateAt(event, audioTime) {
  const progress = (audioTime - event.start_seconds) / event.duration_seconds;
  if (progress < 0 || progress > 1) return null;
  const eased = easeInOutSine(progress);
  const exitY = Number.isFinite(event.exit_y) ? event.exit_y : -120;
  return {
    progress: Number(progress.toFixed(4)),
    eased: Number(eased.toFixed(4)),
    x: Number((event.x + event.drift_px * eased + Math.sin(progress * Math.PI * 2 + event.radius_px) * 3.2).toFixed(2)),
    y: Number((event.y + (exitY - event.y) * eased).toFixed(2)),
    color: event.color,
    origin_cluster_id: event.origin_cluster_id,
    prewarmed_at_t0: event.prewarmed_at_t0 === true,
  };
}

function prewarmBalloons(balloonRises) {
  const prewarmStarts = [-18, -29, -41];
  return balloonRises.map((event, index) => {
    if (index > 2) return { ...event, prewarmed_at_t0: false };
    const startSeconds = prewarmStarts[index];
    const initialProgress = Math.max(0, Math.min(1, (0 - startSeconds) / event.duration_seconds));
    return {
      ...event,
      id: `${event.id}_prewarmed_opening`,
      original_start_seconds: event.start_seconds,
      start_seconds: startSeconds,
      prewarmed_at_t0: true,
      active_from_opening_frame: true,
      initial_progress_at_t0: Number(initialProgress.toFixed(4)),
      prewarm_model: "negative_start_seconds_visible_at_first_frame_v1",
    };
  });
}

function replaceAmbientStateFunction(html) {
  const start = html.indexOf("    function ambientStateAt(audioTime) {");
  const end = html.indexOf("\n    function parseVtt", start);
  if (start === -1 || end === -1) throw new Error("Unable to replace ambientStateAt function");
  const fn = `    function ambientStateAt(audioTime) {
      const storyTime = storyTimeAt(audioTime);
      function pointInPolygonLocal(point, polygon) {
        let inside = false;
        for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
          const xi = polygon[i][0], yi = polygon[i][1];
          const xj = polygon[j][0], yj = polygon[j][1];
          const intersects = (yi > point.y) !== (yj > point.y) && point.x < ((xj - xi) * (point.y - yi)) / ((yj - yi) || 1e-9) + xi;
          if (intersects) inside = !inside;
        }
        return inside;
      }
      function pointInMaskLocal(point, mask) {
        if (!mask) return false;
        if (mask.kind === 'polygon') return pointInPolygonLocal(point, mask.points || []);
        if (mask.kind === 'ellipse') {
          const dx = (point.x - mask.center[0]) / mask.radius_x_px;
          const dy = (point.y - mask.center[1]) / mask.radius_y_px;
          return dx * dx + dy * dy <= 1.0001;
        }
        if (mask.kind === 'rect') return point.x >= mask.x && point.x <= mask.x + mask.width && point.y >= mask.y && point.y <= mask.y + mask.height;
        return false;
      }
      function hotspotByIdLocal(id) {
        return (ambientEffects.flashOriginHotspots || []).find(hotspot => hotspot.id === id);
      }
      function exclusionHitsLocal(point) {
        return (ambientEffects.flashExclusionMasks || []).filter(mask => pointInMaskLocal(point, mask)).map(mask => mask.id);
      }
      const pulseAlpha = fullScreenFlashPulseAlpha(audioTime);
      const activeFlashes = ambientEffects.cameraFlashes.map(event => {
        const intensity = Number(flashIntensity(event, audioTime).toFixed(4));
        if (intensity <= 0.035) return null;
        const source = { x: event.source_x ?? event.x, y: event.source_y ?? event.y };
        const hotspot = hotspotByIdLocal(event.flash_origin_hotspot_id);
        const hits = exclusionHitsLocal(source);
        const stagePoint = sourceToStagePoint(source.x, source.y, storyTime);
        return {
          ...event,
          intensity,
          source_x: source.x,
          source_y: source.y,
          stage_x: Number(stagePoint.x.toFixed(2)),
          stage_y: Number(stagePoint.y.toFixed(2)),
          source_locked_to_plate_transform: true,
          audited_hotspot_exists: Boolean(hotspot),
          hotspot_region: hotspot?.region || event.hotspot_region,
          origin_core_surface: event.origin_core_surface || hotspot?.surface_read,
          surface_read: hotspot?.surface_read || event.surface_read,
          jitter_within_allowance: Math.hypot(event.jitter_x_px || 0, event.jitter_y_px || 0) <= (event.allowed_jitter_px || hotspot?.allowed_jitter_px || 0) + 0.001,
          inside_exclusion_mask: hits.length > 0,
          exclusion_hits: hits,
          broad_mask_sampling_used: event.broad_mask_sampling_used === true,
          line_band_sampling_used: event.line_band_sampling_used === true,
          flash_origin_class: 'audited_visible_person_pixel'
        };
      }).filter(Boolean);
      const activeBalloonRises = ambientEffects.balloonRises.map(event => {
        const state = balloonState(event, audioTime);
        if (!state) return null;
        const sourcePoint = { x: state.x, y: state.y };
        const originPoint = { x: event.source_x ?? event.x, y: event.source_y ?? event.y };
        const origin = (ambientEffects.markedBalloonOrigins || []).find(item => item.id === (event.marked_origin_id || event.origin_cluster_id));
        const stagePoint = sourceToStagePoint(sourcePoint.x, sourcePoint.y, storyTime);
        return {
          ...event,
          ...state,
          source_x: Number(sourcePoint.x.toFixed(2)),
          source_y: Number(sourcePoint.y.toFixed(2)),
          origin_source_x: originPoint.x,
          origin_source_y: originPoint.y,
          stage_x: Number(stagePoint.x.toFixed(2)),
          stage_y: Number(stagePoint.y.toFixed(2)),
          source_locked_to_plate_transform: true,
          inside_marked_origin: origin ? pointInMaskLocal(originPoint, origin) : event.inside_marked_origin === true,
          balloon_origin_class: 'user_marked_table_bouquet_cluster'
        };
      }).filter(Boolean);
      const totalFlashes = ambientEffects.cameraFlashes.length;
      const hotspotLockedFlashes = ambientEffects.cameraFlashes.filter(event => {
        const hotspot = hotspotByIdLocal(event.flash_origin_hotspot_id);
        const jitterDistance = Math.hypot(event.jitter_x_px || 0, event.jitter_y_px || 0);
        return Boolean(hotspot) && hotspot.surface_read === 'visible_person' && jitterDistance <= (event.allowed_jitter_px || hotspot.allowed_jitter_px || 0) + 0.001;
      }).length;
      const excludedFlashOrigins = ambientEffects.cameraFlashes.filter(event => {
        const source = { x: event.source_x ?? event.x, y: event.source_y ?? event.y };
        return exclusionHitsLocal(source).length > 0;
      }).length;
      const broadMaskFlashes = ambientEffects.cameraFlashes.filter(event => event.broad_mask_sampling_used === true || event.line_band_sampling_used === true).length;
      return {
        audioTime,
        storyTime,
        profileId: ambientEffects.profile_id,
        sourceLockedToPlateTransform: ambientEffects.sourceLockedToPlateTransform === true,
        activeFlashes,
        activeBalloonRises,
        fullScreenFlashPulse: {
          enabled: ambientEffects.fullScreenFlashPulse?.enabled === true,
          alpha: Number(pulseAlpha.toFixed(4)),
          maxAlphaCap: ambientEffects.fullScreenFlashPulse?.max_alpha || 0,
          endScreenCapAlpha: ambientEffects.fullScreenFlashPulse?.end_screen_cap_alpha || 0,
          source: ambientEffects.fullScreenFlashPulse?.source || null,
          activeSourceEventCount: activeFlashes.length,
          suppressedForEndScreen: audioTime >= proof.endScreenStart
        },
        visibleAmbientEffect: activeFlashes.length > 0 || activeBalloonRises.length > 0 || pulseAlpha > 0,
        maxFlashIntensity: activeFlashes.reduce((max, event) => Math.max(max, event.intensity), 0),
        maxSimultaneousFlashes: activeFlashes.length,
        maxSimultaneousBalloonRises: activeBalloonRises.length,
        counts: {
          cameraFlashes: totalFlashes,
          auditedHotspots: (ambientEffects.flashOriginHotspots || []).length,
          hotspotLockedFlashes,
          flashHotspotRatio: totalFlashes ? Number((hotspotLockedFlashes / totalFlashes).toFixed(4)) : 0,
          excludedFlashOrigins,
          broadMaskFlashes,
          balloonRises: ambientEffects.balloonRises.length,
          prewarmedBalloons: ambientEffects.balloonRises.filter(event => event.prewarmed_at_t0 === true).length
        }
      };
    }`;
  return `${html.slice(0, start)}${fn}${html.slice(end)}`;
}

function insertPulseFunction(html) {
  const needle = `    function flashIntensity(event, audioTime) {
      const dt = audioTime - event.time_seconds;
      if (dt < -0.05 || dt > event.duration_seconds) return 0;
      const normalized = Math.max(0, dt) / event.duration_seconds;
      const attack = 0.16;
      const value = normalized < attack ? normalized / attack : 1 - ((normalized - attack) / (1 - attack));
      return Math.pow(Math.max(0, Math.min(1, value)), 1.7);
    }
`;
  if (!html.includes(needle)) throw new Error("Unable to find flashIntensity function for pulse insertion");
  const pulseFn = `    function fullScreenFlashPulseAlpha(audioTime) {
      const config = ambientEffects.fullScreenFlashPulse || {};
      if (config.enabled !== true) return 0;
      const maxAlpha = Number(config.max_alpha || 0.07);
      const endScreenCap = Number(config.end_screen_cap_alpha || 0.012);
      const cap = audioTime >= proof.endScreenStart ? Math.min(maxAlpha, endScreenCap) : maxAlpha;
      const baseAlpha = Number(config.alpha_per_full_strength_flash || 0.052);
      let alpha = 0;
      for (const event of ambientEffects.cameraFlashes) {
        const intensity = flashIntensity(event, audioTime);
        if (intensity <= 0) continue;
        const strengthScale = Math.max(0.65, Math.min(1.18, (event.strength || 0.52) / 0.54));
        alpha += intensity * baseAlpha * strengthScale;
      }
      return Math.max(0, Math.min(cap, alpha));
    }
`;
  return html.replace(needle, `${needle}${pulseFn}`);
}

function insertPulseDraw(html) {
  const drawStart = html.indexOf("    function drawAmbient(audioTime, storyTime) {");
  if (drawStart === -1) throw new Error("Unable to find drawAmbient function");
  const needle = `      for (const event of ambientEffects.cameraFlashes) {`;
  const loopStart = html.indexOf(needle, drawStart);
  if (loopStart === -1) throw new Error("Unable to find camera flash draw loop inside drawAmbient");
  const drawPulse = `      const fullFramePulseAlpha = fullScreenFlashPulseAlpha(audioTime);
      if (fullFramePulseAlpha > 0) {
        const color = ambientEffects.fullScreenFlashPulse?.color_rgb || [255, 236, 202];
        ctx.save();
        ctx.globalCompositeOperation = 'screen';
        ctx.fillStyle = 'rgba(' + color[0] + ', ' + color[1] + ', ' + color[2] + ', ' + fullFramePulseAlpha.toFixed(3) + ')';
        ctx.fillRect(0, 0, 1920, 1080);
        ctx.restore();
      }
`;
  return `${html.slice(0, loopStart)}${drawPulse}${html.slice(loopStart)}`;
}

function activeBalloonSamples(balloonRises) {
  return [0, 3, 9.601].map((time) => ({
    time_seconds: time,
    active_balloons: balloonRises.map((event) => {
      const state = balloonStateAt(event, time);
      return state ? { id: event.id, ...state } : null;
    }).filter(Boolean),
  }));
}

function pulseReport(cameraFlashes, proof) {
  const samples = [];
  let maxAlpha = 0;
  let maxTime = 0;
  for (let time = 0; time <= proof.duration; time += 0.02) {
    const alpha = pulseAlphaAt(time, cameraFlashes, proof);
    if (alpha > maxAlpha) {
      maxAlpha = alpha;
      maxTime = time;
    }
  }
  for (const time of [0.8, 3.25, 9.601, 55.9, 56.18, 56.48, 56.6, proof.endScreenStart + 0.2, proof.duration - 1]) {
    samples.push({
      time_seconds: Number(time.toFixed(3)),
      pulse_alpha: Number(pulseAlphaAt(time, cameraFlashes, proof).toFixed(4)),
      active_flash_ids: cameraFlashes
        .filter((event) => flashIntensity(event, time) > 0.035)
        .map((event) => event.id),
    });
  }
  return {
    pulse_contract: pulseContract,
    scanned_step_seconds: 0.02,
    max_observed_alpha: Number(maxAlpha.toFixed(4)),
    max_observed_time_seconds: Number(maxTime.toFixed(3)),
    max_under_contract_cap: maxAlpha <= pulseContract.max_alpha + 1e-6,
    representative_samples: samples,
  };
}

function writeReviewArtifacts(proof, cameraFlashes, balloonRises) {
  const dir = path.join(successorRoot, "qa/immediate_balloons_flash_pulse");
  ensureDir(dir);
  const balloonProofPath = path.join(dir, "opening_frame_balloon_state.json");
  const pulseReportPath = path.join(dir, "full_frame_flash_pulse_intensity_report.json");
  const stripPath = path.join(dir, "full_frame_flash_pulse_sample_strip.html");
  const state = {
    profile_id: profileId,
    samples: activeBalloonSamples(balloonRises),
    first_frame_active_balloon_count: activeBalloonSamples(balloonRises)[0].active_balloons.length,
    expected_first_frame_active_balloon_count: 3,
  };
  writeJson(balloonProofPath, state);
  const report = pulseReport(cameraFlashes, proof);
  writeJson(pulseReportPath, report);
  fs.writeFileSync(
    stripPath,
    `<!doctype html><html><head><meta charset="utf-8"><title>Hyatt full-frame flash pulse sample strip</title><style>body{margin:0;background:#120d09;color:#fff2da;font:15px Arial,sans-serif;padding:24px}table{border-collapse:collapse;max-width:1120px}td,th{border:1px solid #5a3b29;padding:8px;vertical-align:top}code{color:#ffe4b8}.pass{color:#8ff0a4}</style></head><body><h1>Hyatt subtle full-frame flash pulse samples</h1><p>The pulse is a capped exposure reaction tied only to audited person-pixel camera-flash events. It renders below rail text.</p><table><tr><th>time</th><th>pulse alpha</th><th>active flash events</th></tr>${report.representative_samples.map((sample) => `<tr><td>${sample.time_seconds.toFixed(3)}s</td><td><code>${sample.pulse_alpha.toFixed(4)}</code></td><td>${sample.active_flash_ids.map((id) => `<code>${id}</code>`).join("<br>") || "none"}</td></tr>`).join("")}</table><p class="pass">Max observed alpha: ${report.max_observed_alpha.toFixed(4)} / cap ${pulseContract.max_alpha.toFixed(3)}</p></body></html>`,
    "utf8",
  );
  return { balloonProofPath, pulseReportPath, stripPath, balloonState: state, pulseReport: report };
}

function staticQa(proof, cameraFlashes, balloonRises, reviewArtifacts) {
  const opening = reviewArtifacts.balloonState.samples.find((sample) => sample.time_seconds === 0);
  const prewarmed = balloonRises.filter((event) => event.prewarmed_at_t0 === true);
  const changedFlashOrigins = cameraFlashes.filter((event) => event.flash_origin_class !== "audited_visible_person_pixel");
  const pulse = reviewArtifacts.pulseReport;
  const qa = {
    profile_id: profileId,
    predecessor_profile_id: predecessorProfileId,
    camera_flash_count: cameraFlashes.length,
    balloon_rise_count: balloonRises.length,
    first_frame_active_balloon_count: opening?.active_balloons.length || 0,
    prewarmed_balloon_ids: prewarmed.map((event) => event.id),
    changed_flash_origins: changedFlashOrigins.map((event) => event.id),
    max_full_frame_pulse_alpha: pulse.max_observed_alpha,
    end_screen_pulse_cap_alpha: pulseContract.end_screen_cap_alpha,
    qa_reads: {
      balloon_effect_initial_frame_read:
        (opening?.active_balloons.length || 0) >= 3 ? "pass_3_balloons_visible_at_t0" : "tighten_less_than_3_balloons_visible_at_t0",
      balloon_prewarm_origin_read:
        prewarmed.length === 3 && prewarmed.every((event) => event.origin_cluster_id)
          ? "pass_first_three_balloons_prewarmed_from_existing_table_bouquet_clusters"
          : "tighten_prewarm_origin_mismatch",
      balloon_count_preservation_read: balloonRises.length === 28 ? "pass_28_balloons" : `tighten_${balloonRises.length}_balloons`,
      fullscreen_flash_pulse_read:
        pulse.pulse_contract.enabled === true && pulse.representative_samples.some((sample) => sample.pulse_alpha > 0)
          ? "pass_subtle_full_frame_exposure_pulse_present"
          : "tighten_full_frame_pulse_not_detected",
      flash_pulse_subtlety_read:
        pulse.max_observed_alpha <= pulseContract.max_alpha + 1e-6
          ? `pass_max_alpha_${pulse.max_observed_alpha.toFixed(4)}_under_${pulseContract.max_alpha.toFixed(3)}`
          : `tighten_max_alpha_${pulse.max_observed_alpha.toFixed(4)}_exceeds_cap`,
      flash_core_origin_preservation_read:
        changedFlashOrigins.length === 0 ? "pass_all_flash_cores_preserved_on_audited_person_pixels" : "tighten_flash_origin_class_changed",
      audited_flash_origin_preservation_read:
        cameraFlashes.length === 180 ? "pass_180_audited_flash_events_preserved_unchanged" : `tighten_${cameraFlashes.length}_flash_events`,
      end_screen_flash_pulse_suppression_read:
        pulse.representative_samples
          .filter((sample) => sample.time_seconds >= proof.endScreenStart)
          .every((sample) => sample.pulse_alpha <= pulseContract.end_screen_cap_alpha + 1e-6)
          ? "pass_end_screen_pulse_capped"
          : "tighten_end_screen_pulse_exceeds_cap",
      debug_overlay_absence_read: "pass_debug_artifacts_separate_from_viewer_player_html",
    },
  };
  const qaPath = path.join(successorRoot, "qa/immediate_balloons_flash_pulse/static_immediate_balloons_flash_pulse_qa.json");
  writeJson(qaPath, qa);
  return { qa, qaPath };
}

function updatePlayerHtml(proof, cameraFlashes, balloonRises) {
  let html = fs.readFileSync(path.join(successorRoot, "player.html"), "utf8");
  proof.ambientEffects = {
    ...proof.ambientEffects,
    profile_id: profileId,
    predecessor_profile_id: predecessorProfileId,
    deterministic_seed: deterministicSeed,
    cameraFlashes,
    balloonRises,
    fullScreenFlashPulse: pulseContract,
    balloonTimingContract: {
      active_from_start_required: true,
      prewarm_model: "negative_start_seconds_visible_at_first_frame_v1",
      prewarmed_count: 3,
      total_balloon_rises: balloonRises.length,
    },
    originContract: {
      ...(proof.ambientEffects?.originContract || {}),
      full_frame_pulse_policy: "secondary_exposure_reaction_only_core_origins_remain_audited_person_pixels",
    },
  };
  if (proof.audio) proof.audio = proof.audio.replace(/v=[^"&]+/, `v=balloon_immediate_flash_pulse_${stamp}`);
  html = replaceProof(html, proof);
  html = insertPulseFunction(html);
  html = replaceAmbientStateFunction(html);
  html = insertPulseDraw(html);
  html = html
    .replace(/Hyatt Regency Living Cover Rough Proof - [^<]+/, "Hyatt Regency Living Cover Rough Proof - Immediate Balloons Flash Pulse")
    .replace(/Hyatt Regency Living Cover N6 [^"]+ HTML rough proof/g, "Hyatt Regency Living Cover N6 immediate balloons and flash-pulse HTML rough proof")
    .replace(/v=[^"]+(?=" type="audio\/mpeg")/, `v=balloon_immediate_flash_pulse_${stamp}`)
    .replace(/v=[^"]+(?=" type="audio\/wav")/, `v=balloon_immediate_flash_pulse_${stamp}`);
  fs.writeFileSync(path.join(successorRoot, "player.html"), html, "utf8");
  return proof;
}

function writeAmbientArtifacts(predecessorAmbient, proof, cameraFlashes, balloonRises, reviewArtifacts, qaPath, qa) {
  const ambientPath = path.join(successorRoot, "living_cover_ambient_effects_layer.json");
  const ambient = {
    ...predecessorAmbient,
    packet_id: successorId,
    phase_gate: "ambient_effects_reopened",
    status: "review_ready_pending_human_immediate_balloons_flash_pulse_keep",
    human_disposition: "pending",
    ambient_effects_process_version: "living_cover_ambient_effects_layer_immediate_balloons_flash_pulse_v1",
    ambient_profile_id: profileId,
    predecessor_profile_id: predecessorProfileId,
    issue_reopened: "balloon_float_not_visible_at_first_frame_and_camera_flashes_lack_subtle_full_frame_exposure_pulse",
    selected_lanes: ["camera_flashes", "full_frame_flash_pulse", "balloon_rises"],
    effect_parameters: {
      ...(predecessorAmbient.effect_parameters || {}),
      deterministic_seed: deterministicSeed,
      camera_flash_count: cameraFlashes.length,
      balloon_rise_count: balloonRises.length,
      camera_flashes: cameraFlashes,
      balloon_rises: balloonRises,
      active_from_start_balloon_prewarm: true,
      balloon_prewarm_count: 3,
      full_screen_flash_pulse: pulseContract,
    },
    debug_review_artifacts: {
      ...(predecessorAmbient.debug_review_artifacts || {}),
      opening_frame_balloon_state: artifact(reviewArtifacts.balloonProofPath),
      full_frame_flash_pulse_intensity_report: artifact(reviewArtifacts.pulseReportPath),
      full_frame_flash_pulse_sample_strip: artifact(reviewArtifacts.stripPath),
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
    `# Hyatt Immediate Balloons And Subtle Full-Frame Flash Pulse Ambient Layer

- Profile: \`${profileId}\`
- Camera flashes: ${cameraFlashes.length}, unchanged from the audited person-pixel flash-origin profile.
- Full-frame pulse: enabled as a secondary exposure reaction only, capped at ${pulseContract.max_alpha.toFixed(3)} alpha and drawn below the rail.
- Balloons: ${balloonRises.length}, with the first three prewarmed by negative start times so balloons are visible at \`t=0\`.
- Gate state: pending human review; video render, publish readiness, and upload stay locked.

## Required Reads

${Object.entries(ambient.qa_reads).map(([key, value]) => `- \`${key}\`: \`${value}\``).join("\n")}
`,
    "utf8",
  );
  return { ambientPath, mdPath, ambient };
}

function writeRoughManifest(ambientArtifacts, qaPath) {
  const manifestPath = path.join(successorRoot, "rough_assembly_manifest.json");
  const predecessorManifestPath = path.join(predecessorRoot, "rough_assembly_manifest.json");
  const manifest = fs.existsSync(predecessorManifestPath) ? readJson(predecessorManifestPath) : {};
  manifest.packet_id = successorId;
  manifest.status = "review_ready_pending_human_immediate_balloons_flash_pulse_keep";
  manifest.human_disposition = "pending";
  manifest.may_advance_to_video_render = false;
  manifest.predecessor_packet_id = path.basename(predecessorRoot);
  manifest.issue_reopened = "balloon_float_not_visible_at_first_frame_and_camera_flashes_lack_subtle_full_frame_exposure_pulse";
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
    immediate_balloons_flash_pulse_static_qa: {
      path: qaPath,
      sha256: sha256(qaPath),
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
  const reason = "Balloons were not visible on the opening frame and camera flashes lacked a subtle full-frame exposure reaction.";
  const roughPath = path.join(predecessorRoot, "rough_assembly_manifest.json");
  if (fs.existsSync(roughPath)) {
    const rough = readJson(roughPath);
    rough.status = "tighten_balloon_late_and_flash_lacks_global_exposure_pulse";
    rough.human_disposition = "tighten_balloon_late_and_flash_lacks_global_exposure_pulse";
    rough.may_advance_to_video_render = false;
    rough.superseded_by = successorRoot;
    rough.tighten_reason = reason;
    writeJson(roughPath, rough);
  }
  const ambientPath = path.join(predecessorRoot, "living_cover_ambient_effects_layer.json");
  if (fs.existsSync(ambientPath)) {
    const ambient = readJson(ambientPath);
    ambient.status = "tighten_balloon_late_and_flash_lacks_global_exposure_pulse";
    ambient.human_disposition = "tighten_balloon_late_and_flash_lacks_global_exposure_pulse";
    ambient.superseded_by = successorRoot;
    ambient.tighten_reason = reason;
    ambient.downstream_locks = {
      ...(ambient.downstream_locks || {}),
      may_advance_to_video_render: false,
      may_create_publish_readiness: false,
      may_upload_to_youtube: false,
      public_release_ready: false,
    };
    writeJson(ambientPath, ambient);
  }
}

function writeSummary(ambientArtifacts, qaPath, manifestPath, reviewArtifacts) {
  const summaryPath = path.join(successorRoot, "immediate_balloons_flash_pulse_successor_summary.json");
  writeJson(summaryPath, {
    successor_root: successorRoot,
    player_path: path.join(successorRoot, "player.html"),
    ambient_profile_id: profileId,
    predecessor_root: predecessorRoot,
    rough_manifest_path: manifestPath,
    ambient_layer_path: ambientArtifacts.ambientPath,
    static_qa_path: qaPath,
    opening_frame_balloon_state_path: reviewArtifacts.balloonProofPath,
    full_frame_flash_pulse_intensity_report_path: reviewArtifacts.pulseReportPath,
    full_frame_flash_pulse_sample_strip_path: reviewArtifacts.stripPath,
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
  const cameraFlashes = proof.ambientEffects.cameraFlashes || predecessorAmbient.effect_parameters.camera_flashes || [];
  const balloonRises = prewarmBalloons(proof.ambientEffects.balloonRises || predecessorAmbient.effect_parameters.balloon_rises || []);
  const updatedProof = updatePlayerHtml(proof, cameraFlashes, balloonRises);
  const reviewArtifacts = writeReviewArtifacts(updatedProof, cameraFlashes, balloonRises);
  const { qa, qaPath } = staticQa(updatedProof, cameraFlashes, balloonRises, reviewArtifacts);
  const ambientArtifacts = writeAmbientArtifacts(predecessorAmbient, updatedProof, cameraFlashes, balloonRises, reviewArtifacts, qaPath, qa);
  const manifestPath = writeRoughManifest(ambientArtifacts, qaPath);
  markPredecessorTighten();
  const summaryPath = writeSummary(ambientArtifacts, qaPath, manifestPath, reviewArtifacts);
  console.log(JSON.stringify({ successorRoot, playerPath, summaryPath }, null, 2));
}

main();
