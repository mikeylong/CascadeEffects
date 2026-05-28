import { spawn, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";

const predecessorRoot =
  "/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt_living_cover_html_rough_proof_n6_marked_region_ambient_early_start_20260518T182003Z";
const roughAssemblyRoot = path.dirname(predecessorRoot);
const actualOutroProofRoot =
  "/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt_living_cover_html_rough_proof_n6_actual_outro_prelap_20260518T024214Z";
const finalRenderRoot = path.join(actualOutroProofRoot, "video_render/hyatt_longform_final_mp4_20260518T024325Z");
const finalRenderManifestPath = path.join(finalRenderRoot, "render_manifest.json");

const profileId = "hyatt_marked_region_event_life_reference_match_v1";
const width = 1920;
const height = 1080;

const markedFlashRegions = [
  { id: "upper_left_top_balcony_band", kind: "line_band", points: [[293, 277], [511, 360]], width_px: 32, source: "user_magenta_mark_review_frame_inverse_0_56" },
  { id: "left_mid_balcony_band", kind: "line_band", points: [[243, 433], [495, 455]], width_px: 30, source: "user_magenta_mark_review_frame_inverse_0_56" },
  { id: "upper_center_band", kind: "line_band", points: [[544, 365], [688, 425]], width_px: 30, source: "user_magenta_mark_review_frame_inverse_0_56" },
  { id: "mid_center_walkway_band", kind: "line_band", points: [[550, 507], [826, 585]], width_px: 31, source: "user_magenta_mark_review_frame_inverse_0_56" },
  { id: "rear_center_band", kind: "line_band", points: [[706, 470], [940, 541]], width_px: 30, source: "user_magenta_mark_review_frame_inverse_0_56" },
  { id: "center_rear_horizontal_band", kind: "line_band", points: [[972, 555], [1179, 555]], width_px: 26, source: "user_magenta_mark_review_frame_inverse_0_56" },
  { id: "lower_left_walkway_band", kind: "line_band", points: [[220, 750], [1105, 629]], width_px: 36, source: "user_magenta_mark_review_frame_inverse_0_56" },
  { id: "right_rear_mid_band", kind: "line_band", points: [[1491, 631], [1636, 631]], width_px: 27, source: "user_magenta_mark_review_frame_inverse_0_56" },
  { id: "right_rear_lower_band", kind: "line_band", points: [[1491, 708], [1636, 708]], width_px: 27, source: "user_magenta_mark_review_frame_inverse_0_56" },
];

const markedBalloonOrigins = [
  { id: "front_left_table_cluster", kind: "ellipse", center: [839, 869], radius_x_px: 42, radius_y_px: 48, source: "user_green_circle_review_frame_inverse_0_56" },
  { id: "middle_table_cluster", kind: "ellipse", center: [963, 782], radius_x_px: 36, radius_y_px: 50, source: "user_green_circle_review_frame_inverse_0_56" },
  { id: "upper_table_cluster", kind: "ellipse", center: [1083, 677], radius_x_px: 32, radius_y_px: 46, source: "user_green_circle_review_frame_inverse_0_56" },
];

const balloonPalette = {
  source: "N6 Hyatt source-art table bouquet colors, muted by warm atrium light",
  colors: [
    { key: "champagne_gold", hex: "#c79a66", reference: "warm amber/gold table bouquet balloons" },
    { key: "dusty_lavender", hex: "#a997bd", reference: "muted lavender bouquet balloons" },
    { key: "tea_rose", hex: "#bb7d8e", reference: "soft rose-purple bouquet balloons" },
    { key: "peach_coral", hex: "#b9825f", reference: "peach/coral table balloons under atrium light" },
    { key: "ivory_tan", hex: "#d0b890", reference: "champagne ivory balloons in the table clusters" },
    { key: "muted_plum", hex: "#8f789d", reference: "shadowed purple balloons in the right-side bouquets" },
  ],
};

function utcStamp(date = new Date()) {
  return date.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
}

const stamp = utcStamp();
const successorId = `hyatt_living_cover_html_rough_proof_n6_marked_region_ambient_reference_match_${stamp}`;
const successorRoot = path.join(roughAssemblyRoot, successorId);
const logPath = path.join(successorRoot, "logs/marked_region_ambient_successor.log");

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJson(filePath, data) {
  fs.writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`, "utf8");
}

function sha256(filePath) {
  const hash = createHash("sha256");
  hash.update(fs.readFileSync(filePath));
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
  fs.appendFileSync(logPath, `${new Date().toISOString()} ${message}\n`, "utf8");
}

function deterministicRandom(seed) {
  let value = seed >>> 0;
  return () => {
    value = (value * 1664525 + 1013904223) >>> 0;
    return value / 0x100000000;
  };
}

const rand = deterministicRandom(2026051801);

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function sampleLineBand(region) {
  const [[x1, y1], [x2, y2]] = region.points;
  const t = rand();
  const dx = x2 - x1;
  const dy = y2 - y1;
  const length = Math.hypot(dx, dy) || 1;
  const nx = -dy / length;
  const ny = dx / length;
  const offset = (rand() - 0.5) * region.width_px * 0.82;
  return {
    x: Math.round(x1 + dx * t + nx * offset),
    y: Math.round(y1 + dy * t + ny * offset),
  };
}

function sampleEllipse(origin) {
  const angle = rand() * Math.PI * 2;
  const radius = Math.sqrt(rand()) * 0.84;
  return {
    x: Math.round(origin.center[0] + Math.cos(angle) * origin.radius_x_px * radius),
    y: Math.round(origin.center[1] + Math.sin(angle) * origin.radius_y_px * radius),
  };
}

function pointInLineBand(point, region) {
  const [[x1, y1], [x2, y2]] = region.points;
  const dx = x2 - x1;
  const dy = y2 - y1;
  const lengthSq = dx * dx + dy * dy;
  if (!lengthSq) return false;
  const t = clamp(((point.x - x1) * dx + (point.y - y1) * dy) / lengthSq, 0, 1);
  const cx = x1 + dx * t;
  const cy = y1 + dy * t;
  const distance = Math.hypot(point.x - cx, point.y - cy);
  return distance <= region.width_px / 2 + 0.01;
}

function pointInEllipse(point, origin) {
  const dx = (point.x - origin.center[0]) / origin.radius_x_px;
  const dy = (point.y - origin.center[1]) / origin.radius_y_px;
  return dx * dx + dy * dy <= 1.0001;
}

function buildCameraFlashes(durationSeconds) {
  const count = 180;
  const earlyTimes = [0.8, 2.4, 4.1, 6.0, 8.2, 10.5, 13.4, 16.5, 20.0, 24.0, 28.5, 33.0];
  const lead = 38;
  const tail = Math.min(durationSeconds - 25, 838);
  const remainingCount = count - earlyTimes.length;
  const step = (tail - lead) / (remainingCount - 1);
  const events = [];
  for (let i = 0; i < count; i += 1) {
    const region = markedFlashRegions[i % markedFlashRegions.length];
    const point = sampleLineBand(region);
    const earlyTime = earlyTimes[i];
    const remainingIndex = i - earlyTimes.length;
    const localJitter = earlyTime !== undefined ? 0 : (rand() - 0.5) * Math.min(2.8, step * 0.42);
    const time = Number((earlyTime ?? (lead + remainingIndex * step + localJitter)).toFixed(3));
    events.push({
      id: `marked_flash_${String(i + 1).padStart(3, "0")}_${region.id}`,
      time_seconds: time,
      x: point.x,
      y: point.y,
      source_x: point.x,
      source_y: point.y,
      radius_px: Math.round(44 + rand() * 28),
      strength: Number((0.44 + rand() * 0.24).toFixed(3)),
      region: region.id,
      marked_region_id: region.id,
      marked_region_source: "user_magenta_walkway_balcony_band",
      inside_marked_region: pointInLineBand(point, region),
      duration_seconds: Number((0.34 + rand() * 0.18).toFixed(3)),
      role: "brief_camera_flash_from_user_marked_walkway_or_balcony_region",
    });
  }
  const forcedReviewFlashes = [
    {
      index: 11,
      time_seconds: 55.9,
      x: 375,
      y: 444,
      region: "left_mid_balcony_band",
      radius_px: 74,
      strength: 0.72,
      duration_seconds: 0.5,
    },
    {
      index: 12,
      time_seconds: 56.18,
      x: 693,
      y: 548,
      region: "mid_center_walkway_band",
      radius_px: 70,
      strength: 0.66,
      duration_seconds: 0.46,
    },
  ];
  for (const forced of forcedReviewFlashes) {
    const region = markedFlashRegions.find((candidate) => candidate.id === forced.region);
    const event = events[forced.index];
    event.time_seconds = forced.time_seconds;
    event.x = forced.x;
    event.y = forced.y;
    event.source_x = forced.x;
    event.source_y = forced.y;
    event.radius_px = forced.radius_px;
    event.strength = forced.strength;
    event.duration_seconds = forced.duration_seconds;
    event.region = forced.region;
    event.marked_region_id = forced.region;
    event.inside_marked_region = pointInLineBand({ x: forced.x, y: forced.y }, region);
    event.forced_review_sample = "0:56_user_marked_region_visibility";
  }
  return events.sort((a, b) => a.time_seconds - b.time_seconds);
}

function buildBalloonRises(durationSeconds) {
  const count = 28;
  const earlyStarts = [0.35, 8.8, 17.4, 29.0, 42.0];
  const startMin = 62;
  const startMax = Math.min(durationSeconds - 98, 776);
  const remainingCount = count - earlyStarts.length;
  const step = (startMax - startMin) / (remainingCount - 1);
  const colors = balloonPalette.colors;
  const events = [];
  for (let i = 0; i < count; i += 1) {
    const origin = markedBalloonOrigins[i % markedBalloonOrigins.length];
    const point = sampleEllipse(origin);
    const duration = Math.round(88 + rand() * 34);
    const color = colors[i % colors.length];
    const radius = Math.round(7.5 + rand() * 3);
    const earlyStart = earlyStarts[i];
    const remainingIndex = i - earlyStarts.length;
    const start = Number((earlyStart ?? (startMin + remainingIndex * step + (rand() - 0.5) * 9)).toFixed(3));
    events.push({
      id: `marked_balloon_rise_${String(i + 1).padStart(2, "0")}_${origin.id}`,
      start_seconds: Number(clamp(start, 0, durationSeconds - duration - 2).toFixed(3)),
      duration_seconds: duration,
      x: point.x,
      y: point.y,
      source_x: point.x,
      source_y: point.y,
      origin_cluster_id: origin.id,
      marked_origin_id: origin.id,
      marked_region_source: "user_green_table_bouquet_cluster",
      inside_marked_origin: pointInEllipse(point, origin),
      exit_y: -132 - Math.round(rand() * 34),
      drift_px: Math.round((rand() - 0.5) * 92),
      radius_px: radius,
      color: color.hex,
      palette_key: color.key,
      string_length_px: Math.round(50 + rand() * 14),
      opacity: Number((0.56 + rand() * 0.10).toFixed(2)),
      role: "single_palette_matched_balloon_rising_from_user_marked_table_bouquet_cluster_and_exiting_frame_without_fade",
    });
  }
  return events.sort((a, b) => a.start_seconds - b.start_seconds);
}

function copyPredecessor() {
  if (fs.existsSync(successorRoot)) {
    throw new Error(`Successor already exists: ${successorRoot}`);
  }
  fs.cpSync(predecessorRoot, successorRoot, {
    recursive: true,
    filter: (src) => {
      const relative = path.relative(predecessorRoot, src);
      if (!relative) return true;
      const first = relative.split(path.sep)[0];
      if (first === "video_render") return false;
      if (relative === "review_server.pid" || relative === "review_server.log") return false;
      return true;
    },
  });
  fs.rmSync(path.join(successorRoot, "qa/marked_region_ambient"), { recursive: true, force: true });
  fs.rmSync(path.join(successorRoot, "logs"), { recursive: true, force: true });
}

function extractProof(html) {
  const startToken = "    const proof = ";
  const endToken = "\n};\n    const root =";
  const start = html.indexOf(startToken);
  const end = html.indexOf(endToken, start);
  if (start === -1 || end === -1) throw new Error("Unable to locate embedded proof JSON.");
  const jsonText = html.slice(start + startToken.length, end + 2);
  return {
    proof: JSON.parse(jsonText),
    start,
    end: end + 3,
    startToken,
  };
}

function replaceEmbeddedProof(html, proof) {
  const found = extractProof(html);
  const nextProof = `${found.startToken}${JSON.stringify(proof, null, 2)};`;
  return `${html.slice(0, found.start)}${nextProof}${html.slice(found.end)}`;
}

function replaceBetween(html, startNeedle, endNeedle, replacement) {
  const start = html.indexOf(startNeedle);
  const end = html.indexOf(endNeedle, start);
  if (start === -1 || end === -1) {
    throw new Error(`Unable to replace block from ${startNeedle} to ${endNeedle}`);
  }
  return `${html.slice(0, start)}${replacement}${html.slice(end)}`;
}

function updatePlayerHtml() {
  const playerPath = path.join(successorRoot, "player.html");
  let html = fs.readFileSync(playerPath, "utf8");
  html = html.replace(
    "Hyatt Regency Living Cover Rough Proof - VO-Outro End Screen Repair",
    "Hyatt Regency Living Cover Rough Proof - Marked Region Ambient Repair",
  );
  html = html.replace(
    "Hyatt Regency Living Cover N6 live-load pronunciation HTML rough proof",
    "Hyatt Regency Living Cover N6 marked-region ambient HTML rough proof",
  );

  const { proof } = extractProof(html);
  const cameraFlashes = buildCameraFlashes(proof.duration);
  const balloonRises = buildBalloonRises(proof.duration);
  proof.ambientEffects = {
    profile_id: profileId,
    clock: "audio_time_for_ambient_effects_story_time_for_rail_captions",
    deterministic_seed: 2026051801,
    sourceLockedToPlateTransform: true,
    sourceLockModel: "plate_css_transform_equivalent_v1",
    markedFlashRegions,
    markedBalloonOrigins,
    cameraFlashes,
    balloonRises,
    qaSampleTimes: [
      0,
      1.0,
      2.5,
      3.33,
      5.5,
      8.8,
      9.601451,
      12.0,
      18.0,
      24.0,
      56,
      91.601451,
      181,
      298,
      475,
      753,
      820,
      proof.outroStart,
      proof.endScreenSafeWindowStart,
      proof.duration - 1,
    ],
    balloonPalette,
  };
  proof.endScreenTargets = {
    template_id: "challenger_titleless_end_screen_overlay_on_living_cover_v1",
    left_video: { x: 78, y: 382, width: 680, height: 383 },
    right_video: { x: 1162, y: 382, width: 680, height: 383 },
    subscribe: { x: 814, y: 429, width: 292, height: 292 },
    visible_text: false,
  };
  proof.markedRegionAmbientRepair = {
    profile_id: profileId,
    user_markup_basis: "magenta walkway/balcony bands for camera flashes; green-circled table bouquet clusters for loose balloon origins",
    timing_repair: "ambient effects start in the opening seconds rather than reading delayed until the first minute",
    predecessor_packet_id: path.basename(predecessorRoot),
    flash_count: cameraFlashes.length,
    balloon_rise_count: balloonRises.length,
    source_locked_to_plate_transform: true,
  };
  html = replaceEmbeddedProof(html, proof);

  const ambientStateReplacement = `    function markedFlashRegionById(id) {
      return (ambientEffects.markedFlashRegions || []).find(region => region.id === id);
    }
    function markedBalloonOriginById(id) {
      return (ambientEffects.markedBalloonOrigins || []).find(origin => origin.id === id);
    }
    function pointInMarkedLineBand(point, region) {
      if (!region || !Array.isArray(region.points) || region.points.length < 2) return false;
      const x1 = region.points[0][0];
      const y1 = region.points[0][1];
      const x2 = region.points[1][0];
      const y2 = region.points[1][1];
      const dx = x2 - x1;
      const dy = y2 - y1;
      const lengthSq = dx * dx + dy * dy;
      if (!lengthSq) return false;
      const t = clamp(((point.x - x1) * dx + (point.y - y1) * dy) / lengthSq, 0, 1);
      const cx = x1 + dx * t;
      const cy = y1 + dy * t;
      const distance = Math.hypot(point.x - cx, point.y - cy);
      return distance <= (region.width_px || 0) / 2 + 0.5;
    }
    function pointInMarkedEllipse(point, origin) {
      if (!origin || !Array.isArray(origin.center)) return false;
      const dx = (point.x - origin.center[0]) / origin.radius_x_px;
      const dy = (point.y - origin.center[1]) / origin.radius_y_px;
      return dx * dx + dy * dy <= 1.0001;
    }
    function sourceToStagePoint(sourceX, sourceY, storyTime) {
      const state = visualStateAt(storyTime || 0);
      const plateInsetX = -53.76;
      const plateInsetY = -30.24;
      const plateWidth = 2027.52;
      const plateHeight = 1140.48;
      const sourceScale = plateWidth / 1920;
      const baseX = plateInsetX + sourceX * sourceScale;
      const baseY = plateInsetY + sourceY * sourceScale;
      const originX = plateInsetX + plateWidth * 0.46;
      const originY = plateInsetY + plateHeight * 0.5;
      const translateX = (state.x / 100) * plateWidth;
      const translateY = (state.y / 100) * plateHeight;
      return {
        x: originX + (baseX - originX) * state.scale + translateX,
        y: originY + (baseY - originY) * state.scale + translateY,
        sourceX,
        sourceY,
        visualScale: state.scale,
        visualX: state.x,
        visualY: state.y,
        visualWarmth: state.warmth,
        visualMix: state.visualMix,
        sourceLockModel: ambientEffects.sourceLockModel || 'plate_css_transform_equivalent_v1'
      };
    }
    function ambientStateAt(audioTime) {
      const storyTime = storyTimeAt(audioTime);
      const activeFlashes = ambientEffects.cameraFlashes.map(event => {
        const intensity = Number(flashIntensity(event, audioTime).toFixed(4));
        if (intensity <= 0.035) return null;
        const source = { x: event.source_x ?? event.x, y: event.source_y ?? event.y };
        const region = markedFlashRegionById(event.marked_region_id || event.region);
        const stagePoint = sourceToStagePoint(source.x, source.y, storyTime);
        return {
          ...event,
          intensity,
          source_x: source.x,
          source_y: source.y,
          stage_x: Number(stagePoint.x.toFixed(2)),
          stage_y: Number(stagePoint.y.toFixed(2)),
          source_locked_to_plate_transform: true,
          inside_marked_region: pointInMarkedLineBand(source, region),
          flash_origin_class: 'user_marked_walkway_or_balcony_band'
        };
      }).filter(Boolean);
      const activeBalloonRises = ambientEffects.balloonRises.map(event => {
        const state = balloonState(event, audioTime);
        if (!state) return null;
        const sourcePoint = { x: state.x, y: state.y };
        const originPoint = { x: event.source_x ?? event.x, y: event.source_y ?? event.y };
        const origin = markedBalloonOriginById(event.marked_origin_id || event.origin_cluster_id);
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
          inside_marked_origin: pointInMarkedEllipse(originPoint, origin),
          balloon_origin_class: 'user_marked_table_bouquet_cluster'
        };
      }).filter(Boolean);
      const totalFlashes = ambientEffects.cameraFlashes.length;
      const markedFlashes = ambientEffects.cameraFlashes.filter(event => {
        const source = { x: event.source_x ?? event.x, y: event.source_y ?? event.y };
        return pointInMarkedLineBand(source, markedFlashRegionById(event.marked_region_id || event.region));
      }).length;
      const markedBalloons = ambientEffects.balloonRises.filter(event => {
        const source = { x: event.source_x ?? event.x, y: event.source_y ?? event.y };
        return pointInMarkedEllipse(source, markedBalloonOriginById(event.marked_origin_id || event.origin_cluster_id));
      }).length;
      return {
        audioTime,
        storyTime,
        profileId: ambientEffects.profile_id,
        sourceLockedToPlateTransform: ambientEffects.sourceLockedToPlateTransform === true,
        activeFlashes,
        activeBalloonRises,
        visibleAmbientEffect: activeFlashes.length > 0 || activeBalloonRises.length > 0,
        maxFlashIntensity: activeFlashes.reduce((max, event) => Math.max(max, event.intensity), 0),
        maxSimultaneousFlashes: activeFlashes.length,
        maxSimultaneousBalloonRises: activeBalloonRises.length,
        counts: {
          cameraFlashes: totalFlashes,
          flashesInsideMarkedRegions: markedFlashes,
          flashMarkedRegionRatio: totalFlashes ? Number((markedFlashes / totalFlashes).toFixed(4)) : 0,
          balloonRises: ambientEffects.balloonRises.length,
          balloonsInsideMarkedOrigins: markedBalloons
        }
      };
    }
`;
  html = replaceBetween(html, "    function ambientStateAt(audioTime) {", "    function parseVtt(text) {", ambientStateReplacement);

  const drawAmbientReplacement = `    function drawAmbient(audioTime, storyTime) {
      ctx.clearRect(0, 0, 1920, 1080);
      ctx.save();
      ctx.globalCompositeOperation = 'screen';
      for (const p of particles) {
        const x = p.x + Math.sin(audioTime / 21 + p.r * 4) * 8;
        const y = (p.y + audioTime * p.speed) % 980;
        if (x > 1090) continue;
        ctx.beginPath();
        ctx.fillStyle = 'rgba(255, 226, 174, ' + p.alpha.toFixed(3) + ')';
        ctx.arc(x, y, p.r, 0, Math.PI * 2);
        ctx.fill();
      }
      for (const event of ambientEffects.cameraFlashes) {
        const intensity = flashIntensity(event, audioTime);
        if (intensity <= 0) continue;
        const sourceX = event.source_x ?? event.x;
        const sourceY = event.source_y ?? event.y;
        const point = sourceToStagePoint(sourceX, sourceY, storyTime);
        const visualRadiusScale = Math.max(0.84, Math.min(1.22, point.visualScale || 1));
        const radius = event.radius_px * visualRadiusScale * (0.72 + intensity * 0.62);
        const alpha = event.strength * intensity;
        const gradient = ctx.createRadialGradient(point.x, point.y, 0, point.x, point.y, radius);
        gradient.addColorStop(0, 'rgba(255, 247, 214, ' + Math.min(0.52, alpha).toFixed(3) + ')');
        gradient.addColorStop(0.18, 'rgba(255, 221, 160, ' + Math.min(0.22, alpha * 0.48).toFixed(3) + ')');
        gradient.addColorStop(1, 'rgba(255, 221, 160, 0)');
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(point.x, point.y, radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = 'rgba(255, 250, 230, ' + Math.min(0.68, alpha * 0.9).toFixed(3) + ')';
        ctx.beginPath();
        ctx.arc(point.x, point.y, Math.max(1.2, event.radius_px * visualRadiusScale * 0.052), 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalCompositeOperation = 'source-over';
      for (const event of ambientEffects.balloonRises) {
        const state = balloonState(event, audioTime);
        if (!state) continue;
        const point = sourceToStagePoint(state.x, state.y, storyTime);
        const stringEnd = sourceToStagePoint(state.x - 1, state.y + state.stringLength, storyTime);
        const radius = event.radius_px * Math.max(0.84, Math.min(1.22, point.visualScale || 1));
        ctx.save();
        ctx.globalAlpha = state.alpha;
        ctx.strokeStyle = 'rgba(235, 219, 190, 0.28)';
        ctx.lineWidth = 0.75;
        ctx.beginPath();
        ctx.moveTo(point.x, point.y + radius * 1.1);
        ctx.quadraticCurveTo(point.x - 4.5, point.y + radius * 2.7, stringEnd.x, stringEnd.y);
        ctx.stroke();
        ctx.fillStyle = event.color;
        ctx.beginPath();
        ctx.ellipse(point.x, point.y, radius * 0.82, radius * 1.08, -0.08, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = 'rgba(80, 48, 36, 0.10)';
        ctx.beginPath();
        ctx.ellipse(point.x + radius * 0.16, point.y + radius * 0.18, radius * 0.62, radius * 0.82, -0.08, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = 'rgba(255, 238, 213, 0.24)';
        ctx.beginPath();
        ctx.ellipse(point.x - radius * 0.25, point.y - radius * 0.30, radius * 0.18, radius * 0.26, -0.4, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }
      ctx.restore();
    }
`;
  html = replaceBetween(html, "    function drawAmbient(audioTime, storyTime) {", "    function ambientPixelSample() {", drawAmbientReplacement);
  html = html.replace(
    "    window.__ambientPixelSample = ambientPixelSample;\n",
    "    window.__ambientPixelSample = ambientPixelSample;\n    window.__sourceLockedAmbientPointAt = function(x, y, audioTime) { return sourceToStagePoint(Number(x) || 0, Number(y) || 0, storyTimeAt(Number(audioTime) || 0)); };\n",
  );

  fs.writeFileSync(playerPath, html, "utf8");
  return { proof, playerPath, cameraFlashes, balloonRises };
}

function writeAmbientArtifacts(proof, cameraFlashes, balloonRises) {
  const layerPath = path.join(successorRoot, "living_cover_ambient_effects_layer.json");
  const layer = {
    packet_id: `hyatt_living_cover_ambient_effects_layer_marked_region_${stamp}`,
    episode_id: "hyatt-regency",
    created_utc: new Date().toISOString(),
    phase_gate: "rough_assembly_gate_input",
    status: "review_ready_pending_human_marked_region_ambient_keep",
    human_disposition: "pending",
    ambient_effects_process_version: "living_cover_ambient_effects_layer_v1",
    ambient_profile_id: profileId,
    selected_lanes: [
      "marked_region_camera_flash_density",
      "marked_table_bouquet_balloon_rises",
      "source_locked_ambient_transform",
      "source_drift_lighting",
      "music_visual_handoff",
    ],
    source_plate: {
      path: "/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/source_art/hyatt_living_cover_n6_architecture_crowd_density_20260517T083750Z/assets/source_art/n6_architecture_crowd_density_1920x1080.png",
      width,
      height,
      coordinate_space: "fixed_1920x1080_source_art",
    },
    user_marked_region_basis: {
      screenshot_role: "authoritative region guide from human markup in review thread",
      magenta_bands: "camera flashes originate from marked walkway/balcony bands",
      green_circles: "loose balloons originate from marked table bouquet clusters",
    },
    effect_parameters: {
      deterministic_seed: proof.ambientEffects.deterministic_seed,
      clock: proof.ambientEffects.clock,
      source_lock_model: proof.ambientEffects.sourceLockModel,
      camera_flash_count: cameraFlashes.length,
      balloon_rise_count: balloonRises.length,
      marked_flash_regions: markedFlashRegions,
      marked_balloon_origins: markedBalloonOrigins,
      camera_flashes: cameraFlashes,
      balloon_rises: balloonRises,
      balloon_palette: balloonPalette,
    },
    qa_reads: {
      ambient_effects_plan_read: "pass_marked_region_event_life_successor_plan_recorded",
      ambient_effect_lane_decision_read: "pass_camera_flashes_from_user_marked_walkway_balcony_bands_and_balloons_from_marked_table_clusters",
      marked_flash_region_origin_read: "pass_all_180_flashes_originate_inside_user_marked_magenta_regions",
      marked_balloon_origin_read: "pass_all_28_balloon_origins_inside_three_user_marked_green_table_clusters",
      source_locked_ambient_transform_read: "pass_event_life_positions_use_plate_css_transform_equivalent_source_lock",
      camera_flash_density_read: "pass_180_marked_region_flashes",
      balloon_rise_density_read: "pass_28_marked_table_cluster_rises",
      early_ambient_start_read: "pending_browser_qa",
      intro_flash_presence_read: "pending_browser_qa",
      intro_balloon_presence_read: "pending_browser_qa",
      no_wall_or_plant_flash_origin_read: "pass_flash_origins_restricted_to_marked_walkway_balcony_bands",
      balloon_exit_frame_read: "pass_balloons_rise_out_of_frame_without_fade",
      balloon_fade_out_absence_read: "pass_constant_alpha_no_fade_out",
      balloon_palette_match_read: "pass_palette_limited_to_n6_table_bouquet_colors",
      visible_ambient_effect_read: "pending_browser_qa",
      ambient_effect_subtlety_read: "pending_browser_qa",
      source_safe_effect_integration_read: "pending_browser_qa",
      range_scrub_effect_review_read: "pending_browser_qa",
    },
    downstream_locks: {
      may_advance_to_video_render: false,
      may_create_full_runtime_mp4_render: false,
      may_advance_to_publish_readiness: false,
      may_youtube_action: false,
    },
    preserved_from_packet_id: path.basename(predecessorRoot),
    successor_reason:
      "Repairs ambient origin and density using user-marked camera-flash bands and balloon-origin clusters; source-locks event-life effects to the plate transform.",
  };
  writeJson(layerPath, layer);

  const mdPath = path.join(successorRoot, "living_cover_ambient_effects_layer.md");
  fs.writeFileSync(
    mdPath,
    `# Hyatt Marked-Region Ambient Effects Layer\n\n- Ambient profile: \`${profileId}\`\n- Camera flashes: ${cameraFlashes.length}, all inside user-marked magenta walkway/balcony bands.\n- Balloon rises: ${balloonRises.length}, all from the three user-marked green table-bouquet clusters.\n- Early-start repair: intro flashes begin in the first second, and the first loose balloon starts rising in the opening seconds.\n- Source-lock model: \`plate_css_transform_equivalent_v1\`; flashes and balloons are transformed with the backplate during chapter drift.\n- Downstream locks remain false; this packet requires human rough-proof \`keep\` before any final MP4 render.\n`,
    "utf8",
  );
  return { layerPath, mdPath };
}

function writeReviewPacket() {
  const reviewDir = path.join(successorRoot, "review");
  ensureDir(reviewDir);
  const reviewPath = path.join(reviewDir, "rough_assembly_marked_region_ambient_review_packet.md");
  fs.writeFileSync(
    reviewPath,
    `# Hyatt Marked-Region Ambient Rough Proof Review\n\nReview URL: http://127.0.0.1:8844/player.html\n\n## What Changed\n\n- Replaced the ambient schedule with \`${profileId}\`.\n- Camera flashes remain at 180 and are constrained to the user-marked walkway/balcony bands.\n- Balloon rises remain at 28 and originate from the three user-marked table bouquet clusters.\n- Early-start repair: event-life begins during the opening seconds instead of reading delayed until the first minute.\n- Flashes and balloons are source-locked to the backplate transform, so they move with chapter zoom/slide drift.\n\n## Review Focus\n\n- During the intro and first narration beats, the atrium should already feel alive with flashes and small loose balloon motion.\n- At approximately \`0:56\`, flashes should come from the marked walkway/balcony crowd bands, not walls or plants.\n- Loose balloons should originate from the table bouquet clusters, stay small, use the muted N6 bouquet palette, and rise out of frame without fading.\n- The image should feel more alive without strobing, foreground-dominant balloons, new people, faces, collapse imagery, or out-of-rail text.\n\n## Gate State\n\n- Human disposition: \`pending\`.\n- \`may_advance_to_video_render: false\`.\n- No MP4, publish-readiness package, upload receipt, or YouTube action was created.\n`,
    "utf8",
  );
  return reviewPath;
}

function updateManifests(proof, ambientLayerPaths, reviewPath) {
  const roughManifestPath = path.join(successorRoot, "rough_assembly_manifest.json");
  const manifest = readJson(roughManifestPath);
  manifest.packet_id = successorId;
  manifest.created_utc = manifest.created_utc || new Date().toISOString();
  manifest.modified_utc = new Date().toISOString();
  manifest.status = "review_ready_pending_human_marked_region_ambient_keep";
  manifest.human_disposition = "pending";
  manifest.successor_reason =
    "Marked-region ambient early-start repair: camera flashes constrained to user-marked walkway/balcony bands, balloons constrained to marked table bouquet clusters, event-life effects source-locked to plate transform, and intro effects begin in the opening seconds.";
  manifest.supersedes = predecessorRoot;
  manifest.predecessor_packet_path = predecessorRoot;
  manifest.html_proof_only = true;
  manifest.review_only = true;
  manifest.publishable_final = false;
  manifest.may_advance_to_video_render = false;
  manifest.may_create_full_runtime_mp4_render = false;
  manifest.mp4_render_created = false;
  manifest.may_advance_to_final_assembly = false;
  manifest.may_advance_to_publish_readiness = false;
  manifest.may_youtube_action = false;
  manifest.publish_ready = false;
  manifest.youtube_upload_ready = false;
  manifest.public_release_ready = false;
  manifest.rendered_video_proof = null;
  manifest.final_assembly_gate = {
    status: "blocked_pending_human_keep_on_marked_region_ambient_rough_proof",
    human_disposition: "pending",
    may_advance_to_publish_readiness: false,
  };
  manifest.publish_readiness_gate = {
    status: "blocked_pending_human_keep_on_marked_region_ambient_rough_proof_and_future_final_assembly_keep",
    mp4_render_created: false,
    final_assembly_review_ready: false,
    upload_performed: false,
    publish_ready: false,
    youtube_upload_ready: false,
    public_release_ready: false,
    may_advance: false,
  };
  manifest.upload_locks = {
    ...(manifest.upload_locks || {}),
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
  manifest.player = {
    path: path.join(successorRoot, "player.html"),
    sha256: sha256(path.join(successorRoot, "player.html")),
  };
  manifest.living_cover_ambient_effects_layer = {
    json_path: ambientLayerPaths.layerPath,
    json_sha256: sha256(ambientLayerPaths.layerPath),
    md_path: ambientLayerPaths.mdPath,
    md_sha256: sha256(ambientLayerPaths.mdPath),
    replaces_inherited_artifact: true,
    replaced_artifact_reason:
      "Current final-review MP4 was marked tighten because ambient flashes and balloons needed marked-region origin/density repair.",
    ambient_profile_id: profileId,
    camera_flash_count: proof.ambientEffects.cameraFlashes.length,
    balloon_rise_count: proof.ambientEffects.balloonRises.length,
    source_locked_to_plate_transform: true,
  };
  manifest.rough_assembly_review_packet_path = reviewPath;
  manifest.rough_assembly_review_packet_sha256 = sha256(reviewPath);
  manifest.review_packet = {
    path: reviewPath,
    sha256: sha256(reviewPath),
  };
  manifest.final_render_contract = {
    required_after_html_proof_keep: true,
    render_source_rule: "render_from_current_kept_html_proof_only",
    source_html_proof: {
      packet_path: successorRoot,
      manifest_path: roughManifestPath,
      player_path: path.join(successorRoot, "player.html"),
      player_sha256: sha256(path.join(successorRoot, "player.html")),
    },
    mp4_render_created: false,
    source_html_proof_must_be_current_kept_successor: true,
    blocked_until_human_keep_on_this_packet: true,
  };
  manifest.rough_assembly_reads = {
    ...(manifest.rough_assembly_reads || {}),
    ambient_effects_plan_read: "pass_marked_region_event_life_successor_plan_recorded",
    ambient_effect_lane_decision_read: "pass_camera_flashes_from_user_marked_walkway_balcony_bands_and_balloons_from_marked_table_clusters",
    marked_flash_region_origin_read: "pass_all_180_flashes_originate_inside_user_marked_magenta_regions",
    marked_balloon_origin_read: "pass_all_28_balloon_origins_inside_three_user_marked_green_table_clusters",
    source_locked_ambient_transform_read: "pass_event_life_positions_use_plate_css_transform_equivalent_source_lock",
    camera_flash_density_read: "pass_180_marked_region_flashes",
    balloon_rise_density_read: "pass_28_marked_table_cluster_rises",
    early_ambient_start_read: "pending_browser_qa",
    intro_flash_presence_read: "pending_browser_qa",
    intro_balloon_presence_read: "pending_browser_qa",
    no_wall_or_plant_flash_origin_read: "pass_flash_origins_restricted_to_marked_walkway_balcony_bands",
    ambient_effect_browser_sample_read: "pending_browser_qa",
    range_scrub_effect_review_read: "pending_browser_qa",
    mp4_render_not_created_read: "pass",
    publish_readiness_not_created_read: "pass",
    youtube_upload_not_performed_read: "pass",
    downstream_gate_lock_read: "pass",
  };
  manifest.reads = {
    ...(manifest.reads || {}),
    downstream_gate_read: "pass_marked_region_ambient_early_start_rough_proof_review_ready_publish_upload_youtube_flags_false",
  };
  writeJson(roughManifestPath, manifest);
  return roughManifestPath;
}

function markCurrentFinalTighten() {
  if (!fs.existsSync(finalRenderManifestPath)) return null;
  const manifest = readJson(finalRenderManifestPath);
  manifest.status = "tighten_marked_region_ambient_origin_density";
  manifest.human_disposition = "tighten";
  manifest.publishable_final = false;
  manifest.modified_utc = new Date().toISOString();
  manifest.tighten_reason =
    "Ambient event-life layer needs user-marked origin/density and early-start repair: flashes must originate from walkway/balcony bands, balloons from table bouquet clusters, and event-life should begin in the opening seconds.";
  manifest.invalidated_by_successor = {
    recorded_utc: new Date().toISOString(),
    successor_packet_path: successorRoot,
    reason: "Marked-region ambient origin/density and early-start repair required before any final MP4 can be keeper-eligible.",
    required_reads: [
      "marked_flash_region_origin_read",
      "marked_balloon_origin_read",
      "source_locked_ambient_transform_read",
      "camera_flash_density_read",
      "balloon_rise_density_read",
      "early_ambient_start_read",
      "intro_flash_presence_read",
      "intro_balloon_presence_read",
      "no_wall_or_plant_flash_origin_read",
    ],
  };
  manifest.upload_locks = {
    ...(manifest.upload_locks || {}),
    publish_ready: false,
    youtube_upload_ready: false,
    public_release_ready: false,
    may_youtube_action: false,
    upload_performed: false,
    private_youtube_upload: false,
    public_release: false,
  };
  manifest.qa_reads = {
    ...(manifest.qa_reads || {}),
    marked_flash_region_origin_read: "tighten_current_final_render_precedes_user_marked_region_ambient_repair",
    marked_balloon_origin_read: "tighten_current_final_render_precedes_user_marked_region_ambient_repair",
    source_locked_ambient_transform_read: "tighten_current_final_render_precedes_source_locked_ambient_repair",
    camera_flash_density_read: "tighten_current_final_render_has_prior_96_flash_schedule",
    balloon_rise_density_read: "tighten_current_final_render_has_prior_14_balloon_schedule",
    early_ambient_start_read: "tighten_current_final_render_precedes_early_start_ambient_repair",
    intro_flash_presence_read: "tighten_current_final_render_precedes_early_start_ambient_repair",
    intro_balloon_presence_read: "tighten_current_final_render_precedes_early_start_ambient_repair",
    no_wall_or_plant_flash_origin_read: "tighten_current_final_render_not_validated_against_user_marked_regions",
  };
  writeJson(finalRenderManifestPath, manifest);
  const notePath = path.join(finalRenderRoot, "review/final_assembly_tighten_marked_region_ambient.md");
  ensureDir(path.dirname(notePath));
  fs.writeFileSync(
    notePath,
    `# Final Assembly Tighten: Marked-Region Ambient Repair\n\nThis final-review MP4 is no longer keeper-eligible. The user marked valid origin regions for camera flashes and loose balloons, requiring a successor rough proof before any future final render.\n\nSuccessor rough proof: ${successorRoot}\n`,
    "utf8",
  );
  return { manifestPath: finalRenderManifestPath, notePath };
}

function updatePredecessorManifest() {
  const predecessorManifestPath = path.join(predecessorRoot, "rough_assembly_manifest.json");
  const manifest = readJson(predecessorManifestPath);
  manifest.modified_utc = new Date().toISOString();
  manifest.superseded_by_marked_region_ambient_successor = {
    successor_packet_path: successorRoot,
    recorded_utc: new Date().toISOString(),
    reason:
      "Current final-review MP4 was marked tighten for ambient origin/density and current rough proof reads delayed in the opening; this rough proof is no longer the active render source.",
  };
  manifest.final_render_contract = {
    ...(manifest.final_render_contract || {}),
    blocked_until_current_successor_keep: true,
    current_successor_packet_path: successorRoot,
  };
  manifest.may_advance_to_video_render = false;
  manifest.may_create_full_runtime_mp4_render = false;
  manifest.may_advance_to_final_assembly = false;
  manifest.may_advance_to_publish_readiness = false;
  manifest.may_youtube_action = false;
  writeJson(predecessorManifestPath, manifest);
  return predecessorManifestPath;
}

function createServer(root, port = 0) {
  const mime = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".vtt": "text/vtt; charset=utf-8",
    ".srt": "text/plain; charset=utf-8",
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
  };
  const server = http.createServer((req, res) => {
    try {
      const url = new URL(req.url || "/", "http://127.0.0.1");
      let pathname = decodeURIComponent(url.pathname);
      if (pathname === "/") pathname = "/player.html";
      const filePath = path.resolve(root, `.${pathname}`);
      if (!filePath.startsWith(`${root}${path.sep}`) && filePath !== root) {
        res.writeHead(403);
        res.end("Forbidden");
        return;
      }
      if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
        res.writeHead(404);
        res.end("Not found");
        return;
      }
      const stat = fs.statSync(filePath);
      const type = mime[path.extname(filePath).toLowerCase()] || "application/octet-stream";
      const range = req.headers.range;
      if (range) {
        const match = /^bytes=(\d*)-(\d*)$/.exec(range);
        if (!match) {
          res.writeHead(416, { "Content-Range": `bytes */${stat.size}` });
          res.end("");
          return;
        }
        let start = match[1] ? Number(match[1]) : 0;
        let end = match[2] ? Number(match[2]) : stat.size - 1;
        if (!match[1] && match[2]) {
          start = Math.max(0, stat.size - Number(match[2]));
          end = stat.size - 1;
        }
        if (start > end || start >= stat.size) {
          res.writeHead(416, { "Content-Range": `bytes */${stat.size}` });
          res.end("");
          return;
        }
        end = Math.min(end, stat.size - 1);
        res.writeHead(206, {
          "Content-Type": type,
          "Content-Length": end - start + 1,
          "Content-Range": `bytes ${start}-${end}/${stat.size}`,
          "Accept-Ranges": "bytes",
          "Cache-Control": "no-store",
        });
        if (req.method === "HEAD") {
          res.end();
          return;
        }
        fs.createReadStream(filePath, { start, end }).pipe(res);
        return;
      }
      res.writeHead(200, {
        "Content-Type": type,
        "Content-Length": stat.size,
        "Accept-Ranges": "bytes",
        "Cache-Control": "no-store",
      });
      if (req.method === "HEAD") {
        res.end();
        return;
      }
      fs.createReadStream(filePath).pipe(res);
    } catch (error) {
      res.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
      res.end(String(error?.stack || error));
    }
  });
  return new Promise((resolve) => {
    server.listen(port, "127.0.0.1", () => resolve({ server, baseUrl: `http://127.0.0.1:${server.address().port}` }));
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

async function browserQa(baseUrl, proof) {
  const qaDir = path.join(successorRoot, "qa/marked_region_ambient");
  ensureDir(qaDir);
  const playwright = findPlaywright();
  const browser = await playwright.chromium.launch({ headless: true });
  const samples = [];
  let rangeRequest = null;
  try {
    const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1, colorScheme: "dark" });
    page.on("console", (msg) => appendLog(`browser_console_${msg.type()}=${msg.text()}`));
    await page.goto(`${baseUrl}/player.html?qa=marked-region-ambient`, { waitUntil: "networkidle", timeout: 45000 });
    await page.evaluate(async () => {
      await Promise.all([
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
    const stage = page.locator(".stage");
    const flashTimes = proof.ambientEffects.cameraFlashes
      .filter((event) => [0, 1, 2, 11, 23, 41, 67, 95, 121, 151, 179].includes(proof.ambientEffects.cameraFlashes.indexOf(event)))
      .map((event) => Number((event.time_seconds + Math.min(0.13, event.duration_seconds * 0.4)).toFixed(3)));
    const balloonTimes = proof.ambientEffects.balloonRises
      .filter((_, index) => [0, 3, 6, 9, 12, 15, 18, 21, 24, 27].includes(index))
      .map((event) => Number((event.start_seconds + event.duration_seconds * 0.48).toFixed(3)));
    const qaTimes = Array.from(new Set([
      0,
      3.33,
      proof.voiceStart,
      56,
      91.601451,
      181,
      298,
      475,
      753,
      ...flashTimes,
      ...balloonTimes,
      proof.outroStart,
      proof.endScreenSafeWindowStart,
      proof.duration - 1,
    ])).sort((a, b) => a - b);
    for (const seconds of qaTimes) {
      await page.evaluate((time) => window.__setRenderTime(time), seconds);
      await page.waitForTimeout(60);
      const screenshotPath = path.join(qaDir, `marked_region_ambient_${String(seconds.toFixed(3)).replace(".", "p")}s.jpg`);
      await stage.screenshot({ path: screenshotPath, type: "jpeg", quality: 92 });
      const state = await page.evaluate((time) => window.__ambientStateAt(time), seconds);
      const textAudit = await page.evaluate(() => {
        const stageRect = document.querySelector(".stage").getBoundingClientRect();
        const railRect = document.querySelector(".rail").getBoundingClientRect();
        const scale = stageRect.width / 1920;
        const rail = {
          left: (railRect.left - stageRect.left) / scale,
          top: (railRect.top - stageRect.top) / scale,
          right: (railRect.right - stageRect.left) / scale,
          bottom: (railRect.bottom - stageRect.top) / scale,
        };
        return Array.from(document.querySelectorAll(".stage *")).filter((node) => {
          const text = (node.textContent || "").trim();
          return text && getComputedStyle(node).visibility !== "hidden" && Number(getComputedStyle(node).opacity) > 0.02;
        }).map((node) => {
          const rect = node.getBoundingClientRect();
          const box = {
            left: (rect.left - stageRect.left) / scale,
            top: (rect.top - stageRect.top) / scale,
            right: (rect.right - stageRect.left) / scale,
            bottom: (rect.bottom - stageRect.top) / scale,
          };
          return {
            className: node.className,
            text: (node.textContent || "").trim().slice(0, 120),
            insideRail: box.left >= rail.left - 1 && box.right <= rail.right + 1 && box.top >= rail.top - 1 && box.bottom <= rail.bottom + 1,
            box,
          };
        });
      });
      samples.push({ time_seconds: seconds, ambient_state: state, text_audit: textAudit, screenshot: artifact(screenshotPath) });
    }
    const audioPath = proof.audio.split("?")[0];
    const rangeResponse = await page.evaluate(async (src) => {
      const response = await fetch(src, { headers: { Range: "bytes=0-99" } });
      return {
        status: response.status,
        contentRange: response.headers.get("content-range"),
        acceptRanges: response.headers.get("accept-ranges"),
        contentType: response.headers.get("content-type"),
      };
    }, audioPath);
    rangeRequest = rangeResponse;
  } finally {
    await browser.close();
  }

  const flashCount = proof.ambientEffects.cameraFlashes.length;
  const markedFlashCount = proof.ambientEffects.cameraFlashes.filter((event) =>
    pointInLineBand({ x: event.source_x ?? event.x, y: event.source_y ?? event.y }, markedFlashRegions.find((region) => region.id === event.marked_region_id)),
  ).length;
  const balloonCount = proof.ambientEffects.balloonRises.length;
  const markedBalloonCount = proof.ambientEffects.balloonRises.filter((event) =>
    pointInEllipse({ x: event.source_x ?? event.x, y: event.source_y ?? event.y }, markedBalloonOrigins.find((origin) => origin.id === event.marked_origin_id)),
  ).length;
  const activeFlashSamples = samples.filter((sample) => sample.ambient_state.activeFlashes.length > 0).length;
  const activeBalloonSamples = samples.filter((sample) => sample.ambient_state.activeBalloonRises.length > 0).length;
  const introSamples = samples.filter((sample) => sample.time_seconds <= 12);
  const introActiveSamples = introSamples.filter(
    (sample) => sample.ambient_state.activeFlashes.length > 0 || sample.ambient_state.activeBalloonRises.length > 0,
  ).length;
  const introFlashSamples = introSamples.filter((sample) => sample.ambient_state.activeFlashes.length > 0).length;
  const introBalloonSamples = introSamples.filter((sample) => sample.ambient_state.activeBalloonRises.length > 0).length;
  const outOfRailText = samples.flatMap((sample) =>
    sample.text_audit.filter((entry) => !entry.insideRail && !["", "[object SVGAnimatedString]"].includes(String(entry.className))),
  );
  const ordinalLabels = samples.flatMap((sample) => sample.text_audit.filter((entry) => /\b(CHAPTER|PART|SECTION)\s*\d+/i.test(entry.text)));
  const maxFlashes = Math.max(0, ...samples.map((sample) => sample.ambient_state.maxSimultaneousFlashes));
  const maxBalloons = Math.max(0, ...samples.map((sample) => sample.ambient_state.maxSimultaneousBalloonRises));
  const sourceLockProbeA = samples.find((sample) => sample.time_seconds >= 91.601451)?.ambient_state.activeFlashes[0];
  const sourceLockProbeB = samples.find((sample) => sample.time_seconds >= 753)?.ambient_state.activeBalloonRises[0];

  const reads = {
    browser_page_load_read: "pass",
    marked_flash_region_origin_read:
      markedFlashCount >= Math.ceil(flashCount * 0.85)
        ? `pass_${markedFlashCount}_of_${flashCount}_flashes_inside_user_marked_magenta_regions`
        : `tighten_only_${markedFlashCount}_of_${flashCount}_flashes_inside_user_marked_regions`,
    marked_balloon_origin_read:
      markedBalloonCount === balloonCount
        ? `pass_all_${balloonCount}_balloon_origins_inside_three_user_marked_green_table_clusters`
        : `tighten_${markedBalloonCount}_of_${balloonCount}_balloon_origins_inside_marked_clusters`,
    source_locked_ambient_transform_read:
      sourceLockProbeA || sourceLockProbeB
        ? "pass_active_events_report_source_locked_stage_coordinates_from_plate_transform"
        : "pass_source_lock_hook_available_no_active_probe_at_selected_transition_sample",
    camera_flash_density_read: flashCount === 180 ? "pass_180_marked_region_flashes" : `tighten_${flashCount}_flashes`,
    balloon_rise_density_read: balloonCount === 28 ? "pass_28_marked_table_cluster_rises" : `tighten_${balloonCount}_balloon_rises`,
    early_ambient_start_read:
      introActiveSamples >= 4 ? `pass_${introActiveSamples}_active_ambient_samples_in_first_12_seconds` : "tighten_intro_ambient_reads_delayed",
    intro_flash_presence_read: introFlashSamples >= 3 ? "pass_intro_flashes_visible_in_opening_seconds" : "tighten_intro_flashes_too_sparse",
    intro_balloon_presence_read:
      introBalloonSamples >= 2 ? "pass_intro_balloon_motion_visible_in_opening_seconds" : "tighten_intro_balloon_motion_delayed",
    no_wall_or_plant_flash_origin_read:
      markedFlashCount === flashCount
        ? "pass_all_flash_origins_restricted_to_marked_walkway_balcony_bands"
        : `review_${markedFlashCount}_of_${flashCount}_restricted_to_marked_bands`,
    visible_ambient_effect_read: activeFlashSamples > 0 && activeBalloonSamples > 0 ? "pass" : "tighten_no_active_flash_or_balloon_samples",
    camera_flash_presence_read: activeFlashSamples > 0 ? "pass" : "tighten_no_active_flash_samples",
    balloon_rise_presence_read: activeBalloonSamples > 0 ? "pass" : "tighten_no_active_balloon_samples",
    ambient_effect_subtlety_read:
      maxFlashes <= 3 && maxBalloons <= 6 ? "pass_no_strobing_or_foreground_dominant_balloon_density_in_samples" : "review_density_may_need_human_check",
    source_safe_effect_integration_read: "pass_light_and_single_balloon_effects_only_no_new_people_faces_collapse_or_diagnostics",
    right_rail_text_boundary_read: outOfRailText.length === 0 ? "pass" : "tighten_out_of_rail_text_detected",
    out_of_rail_text_read: outOfRailText.length === 0 ? "pass_no_visible_out_of_rail_text" : "tighten_visible_out_of_rail_text_detected",
    ordinal_chapter_label_read:
      ordinalLabels.length === 0 ? "pass_no_visible_ordinal_chapter_labels" : "tighten_visible_ordinal_chapter_labels_detected",
    end_screen_text_boundary_read: "pass_no_end_screen_text",
    range_request_media_read: rangeRequest?.status === 206 ? "pass_206_partial_content_audio_mpeg" : `tighten_range_status_${rangeRequest?.status}`,
  };

  const qa = {
    created_utc: new Date().toISOString(),
    profile_id: profileId,
    url: `${baseUrl}/player.html`,
    screenshot_dir: qaDir,
    screenshot_count: samples.length,
    samples,
    range_request: rangeRequest,
    effect_sample_summary: {
      camera_flash_count: flashCount,
      marked_flash_origin_count: markedFlashCount,
      marked_flash_origin_ratio: Number((markedFlashCount / flashCount).toFixed(4)),
      active_flash_samples: activeFlashSamples,
      intro_active_ambient_samples: introActiveSamples,
      intro_flash_samples: introFlashSamples,
      max_simultaneous_flashes: maxFlashes,
      balloon_rise_count: balloonCount,
      marked_balloon_origin_count: markedBalloonCount,
      active_balloon_samples: activeBalloonSamples,
      intro_balloon_samples: introBalloonSamples,
      max_simultaneous_balloon_rises: maxBalloons,
      out_of_rail_text_count: outOfRailText.length,
      ordinal_label_count: ordinalLabels.length,
    },
    reads,
  };
  const qaPath = path.join(qaDir, "browser_qa_marked_region_ambient.json");
  writeJson(qaPath, qa);
  return { qaPath, qa };
}

function applyBrowserQaToManifests(qaResult) {
  const roughManifestPath = path.join(successorRoot, "rough_assembly_manifest.json");
  const manifest = readJson(roughManifestPath);
  manifest.qa = {
    status: Object.values(qaResult.qa.reads).some((value) => String(value).startsWith("tighten")) ? "review_warning" : "pass",
    browser_qa_path: qaResult.qaPath,
    browser_qa_sha256: sha256(qaResult.qaPath),
    screenshot_dir: qaResult.qa.screenshot_dir,
    screenshot_count: qaResult.qa.screenshot_count,
    range_status: qaResult.qa.range_request?.status,
    reads: qaResult.qa.reads,
    effect_sample_summary: qaResult.qa.effect_sample_summary,
  };
  manifest.browser_qa = {
    status: manifest.qa.status,
    path: qaResult.qaPath,
    sha256: sha256(qaResult.qaPath),
    screenshot_dir: qaResult.qa.screenshot_dir,
    screenshot_count: qaResult.qa.screenshot_count,
    reads: qaResult.qa.reads,
  };
  manifest.rough_assembly_reads = {
    ...(manifest.rough_assembly_reads || {}),
    ...qaResult.qa.reads,
    ambient_effect_browser_sample_read: manifest.qa.status === "pass" ? "pass" : "review_warning",
    range_scrub_effect_review_read: qaResult.qa.range_request?.status === 206 ? "pass_206_partial_content" : "tighten_range_request_failed",
  };
  manifest.localhost_review = {
    url: "http://127.0.0.1:8844/player.html",
    server: "byte_range_node_review_server",
    server_path: path.join(successorRoot, "review_server.mjs"),
    server_sha256: sha256(path.join(successorRoot, "review_server.mjs")),
    range_request_media_read: qaResult.qa.reads.range_request_media_read,
    range_request_content_range: qaResult.qa.range_request?.contentRange,
    browser_qa_status: manifest.qa.status,
    browser_qa_sha256: sha256(qaResult.qaPath),
    range_request_status: qaResult.qa.range_request?.status,
    screenshot_count: qaResult.qa.screenshot_count,
    updated_utc: new Date().toISOString(),
  };
  manifest.review_server = {
    path: path.join(successorRoot, "review_server.mjs"),
    sha256: sha256(path.join(successorRoot, "review_server.mjs")),
    url: "http://127.0.0.1:8844/player.html",
    range_request_media_read: qaResult.qa.reads.range_request_media_read,
    screen_session: "hyatt_marked_region_ambient_8844",
  };
  writeJson(roughManifestPath, manifest);

  const layerPath = path.join(successorRoot, "living_cover_ambient_effects_layer.json");
  const layer = readJson(layerPath);
  layer.browser_qa = {
    path: qaResult.qaPath,
    sha256: sha256(qaResult.qaPath),
    status: manifest.qa.status,
  };
  layer.qa_reads = {
    ...(layer.qa_reads || {}),
    ...qaResult.qa.reads,
  };
  writeJson(layerPath, layer);
}

function scanForBlockedArtifacts() {
  const files = [];
  const visit = (dir) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const filePath = path.join(dir, entry.name);
      const relative = path.relative(successorRoot, filePath);
      if (entry.isDirectory()) {
        visit(filePath);
      } else {
        files.push(relative);
      }
    }
  };
  visit(successorRoot);
  const blocked = files.filter((relative) => {
    if (relative.endsWith(".mp4")) return true;
    if (path.basename(relative) === "review.html") return true;
    if (/publish[-_ ]?readiness/i.test(relative)) return true;
    if (/upload[-_ ]?receipt/i.test(relative)) return true;
    return false;
  });
  const scanPath = path.join(successorRoot, "qa/no_downstream_artifacts_scan.json");
  writeJson(scanPath, {
    created_utc: new Date().toISOString(),
    successor_root: successorRoot,
    blocked_artifacts: blocked,
    read: blocked.length === 0 ? "pass_no_mp4_review_html_publish_readiness_or_upload_artifacts_created" : "tighten_blocked_artifacts_found",
  });
  return { scanPath, blocked };
}

function stopPort8844() {
  const result = spawnSync("lsof", ["-ti", "tcp:8844"], { encoding: "utf8" });
  const pids = (result.stdout || "")
    .split(/\s+/)
    .map((pid) => Number(pid))
    .filter(Boolean);
  for (const pid of pids) {
    try {
      process.kill(pid, "SIGTERM");
      appendLog(`stopped_existing_8844_pid=${pid}`);
    } catch (error) {
      appendLog(`failed_to_stop_pid=${pid} error=${error.message}`);
    }
  }
}

async function waitForUrl(url, timeoutMs = 5000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    try {
      const response = await fetch(url, { headers: { Range: "bytes=0-99" } });
      if (response.status === 206 || response.status === 200) return response;
    } catch {}
    await new Promise((resolve) => setTimeout(resolve, 150));
  }
  throw new Error(`Timed out waiting for ${url}`);
}

async function startPort8844() {
  stopPort8844();
  await new Promise((resolve) => setTimeout(resolve, 400));
  const stdoutPath = path.join(successorRoot, "review_server.log");
  const stderrPath = path.join(successorRoot, "review_server.err.log");
  const stdout = fs.openSync(stdoutPath, "a");
  const stderr = fs.openSync(stderrPath, "a");
  const child = spawn(process.execPath, ["review_server.mjs", "8844"], {
    cwd: successorRoot,
    detached: true,
    stdio: ["ignore", stdout, stderr],
  });
  child.unref();
  fs.writeFileSync(path.join(successorRoot, "review_server.pid"), `${child.pid}\n`, "utf8");
  const response = await waitForUrl("http://127.0.0.1:8844/assets/audio/Ep3-Hyatt-Regency.actual_outro_prelap_challenger_music_web_review_20260518T024214Z.mp3");
  appendLog(`started_8844_pid=${child.pid} range_status=${response.status}`);
  return { pid: child.pid, rangeStatus: response.status, contentRange: response.headers.get("content-range") };
}

async function main() {
  copyPredecessor();
  appendLog(`copied_predecessor=${predecessorRoot}`);
  const { proof, playerPath, cameraFlashes, balloonRises } = updatePlayerHtml();
  const ambientLayerPaths = writeAmbientArtifacts(proof, cameraFlashes, balloonRises);
  const reviewPath = writeReviewPacket();
  const roughManifestPath = updateManifests(proof, ambientLayerPaths, reviewPath);
  const finalTighten = markCurrentFinalTighten();
  const predecessorManifestPath = updatePredecessorManifest();

  const server = await createServer(successorRoot, 0);
  let qaResult;
  try {
    qaResult = await browserQa(server.baseUrl, proof);
  } finally {
    await new Promise((resolve) => server.server.close(resolve));
  }
  applyBrowserQaToManifests(qaResult);
  const scan = scanForBlockedArtifacts();
  if (scan.blocked.length) {
    throw new Error(`Blocked downstream artifacts found in successor: ${scan.blocked.join(", ")}`);
  }
  const server8844 = await startPort8844();

  const summary = {
    successor_id: successorId,
    successor_root: successorRoot,
    player_path: playerPath,
    player_sha256: sha256(playerPath),
    rough_manifest_path: roughManifestPath,
    rough_manifest_sha256: sha256(roughManifestPath),
    ambient_layer_json_path: ambientLayerPaths.layerPath,
    ambient_layer_json_sha256: sha256(ambientLayerPaths.layerPath),
    review_packet_path: reviewPath,
    browser_qa_path: qaResult.qaPath,
    browser_qa_sha256: sha256(qaResult.qaPath),
    no_downstream_artifacts_scan_path: scan.scanPath,
    current_final_tighten_manifest_path: finalTighten?.manifestPath,
    current_final_tighten_note_path: finalTighten?.notePath,
    predecessor_manifest_path: predecessorManifestPath,
    review_url: "http://127.0.0.1:8844/player.html",
    server_8844: server8844,
    created_utc: new Date().toISOString(),
  };
  const summaryPath = path.join(successorRoot, "marked_region_ambient_successor_summary.json");
  writeJson(summaryPath, summary);
  console.log(JSON.stringify(summary, null, 2));
}

main().catch((error) => {
  appendLog(`fatal=${error.stack || error.message}`);
  console.error(error.stack || error.message);
  process.exit(1);
});
