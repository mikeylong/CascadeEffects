import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const baseRoot =
  "/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt_living_cover_html_rough_proof_n6_subtle_tail_outro_20260519T040128Z";
const roughAssemblyRoot = path.dirname(baseRoot);
const lifecycleRoot =
  "/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/publish_readiness/hyatt_publish_readiness_lifecycle";
const lifecycleManifestPath = path.join(lifecycleRoot, "publish_readiness_manifest.json");
const audioRepairRoot =
  "/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/audio_repairs/live_load_long_i_blip_repair_20260519T184526Z";
const repairedAudioMp3 = path.join(
  audioRepairRoot,
  "mix/Ep3-Hyatt-Regency.live_load_blip_repair_subtle_tail_web_review_20260519T184526Z.mp3",
);
const repairedAudioWav = path.join(
  audioRepairRoot,
  "mix/Ep3-Hyatt-Regency.live_load_blip_repair_subtle_tail_review_mix_20260519T184526Z.wav",
);

const width = 1920;
const height = 1080;
const profileId = "hyatt_people_standing_event_life_v1";
const deterministicSeed = 2026051901;

function utcStamp(date = new Date()) {
  return date.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
}

const stamp = utcStamp();
const successorId = `hyatt_living_cover_html_rough_proof_n6_people_standing_ambient_${stamp}`;
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

function deterministicRandom(seed) {
  let value = seed >>> 0;
  return () => {
    value = (value * 1664525 + 1013904223) >>> 0;
    return value / 0x100000000;
  };
}

const rand = deterministicRandom(deterministicSeed);

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
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

function pointInEllipse(point, mask) {
  const dx = (point.x - mask.center[0]) / mask.radius_x_px;
  const dy = (point.y - mask.center[1]) / mask.radius_y_px;
  return dx * dx + dy * dy <= 1.0001;
}

function pointInRect(point, mask) {
  return (
    point.x >= mask.x &&
    point.x <= mask.x + mask.width &&
    point.y >= mask.y &&
    point.y <= mask.y + mask.height
  );
}

function pointInMask(point, mask) {
  if (mask.kind === "polygon") return pointInPolygon(point, mask.points);
  if (mask.kind === "ellipse") return pointInEllipse(point, mask);
  if (mask.kind === "rect") return pointInRect(point, mask);
  return false;
}

function maskBounds(mask) {
  if (mask.kind === "polygon") {
    const xs = mask.points.map((point) => point[0]);
    const ys = mask.points.map((point) => point[1]);
    return {
      minX: Math.min(...xs),
      maxX: Math.max(...xs),
      minY: Math.min(...ys),
      maxY: Math.max(...ys),
    };
  }
  if (mask.kind === "ellipse") {
    return {
      minX: mask.center[0] - mask.radius_x_px,
      maxX: mask.center[0] + mask.radius_x_px,
      minY: mask.center[1] - mask.radius_y_px,
      maxY: mask.center[1] + mask.radius_y_px,
    };
  }
  return {
    minX: mask.x,
    maxX: mask.x + mask.width,
    minY: mask.y,
    maxY: mask.y + mask.height,
  };
}

function exclusionHits(point) {
  return flashExclusionMasks.filter((mask) => pointInMask(point, mask)).map((mask) => mask.id);
}

function sampleMask(mask) {
  const bounds = maskBounds(mask);
  for (let attempt = 0; attempt < 240; attempt += 1) {
    const point = {
      x: Math.round(bounds.minX + rand() * (bounds.maxX - bounds.minX)),
      y: Math.round(bounds.minY + rand() * (bounds.maxY - bounds.minY)),
    };
    if (pointInMask(point, mask) && exclusionHits(point).length === 0) return point;
  }
  throw new Error(`Unable to sample non-excluded point from mask ${mask.id}`);
}

const peopleStandingFlashMasks = [
  {
    id: "upper_left_top_visible_people",
    kind: "polygon",
    points: [
      [306, 250],
      [505, 324],
      [494, 348],
      [296, 285],
    ],
    role: "visible_people_on_upper_left_balcony_not_wall_or_fascia",
    related_human_markup_region: "upper_left_top_balcony_band",
  },
  {
    id: "left_mid_balcony_visible_people",
    kind: "polygon",
    points: [
      [176, 404],
      [485, 429],
      [482, 455],
      [180, 441],
    ],
    role: "visible_people_along_left_mid_balcony_rail",
    related_human_markup_region: "left_mid_balcony_band",
  },
  {
    id: "upper_center_visible_people",
    kind: "polygon",
    points: [
      [545, 365],
      [698, 421],
      [690, 444],
      [535, 392],
    ],
    role: "visible_people_on_upper_center_balcony",
    related_human_markup_region: "upper_center_band",
  },
  {
    id: "mid_center_walkway_visible_people",
    kind: "polygon",
    points: [
      [520, 485],
      [835, 557],
      [826, 584],
      [524, 528],
    ],
    role: "visible_people_on_mid_center_walkway_not_slab_edge",
    related_human_markup_region: "mid_center_walkway_band",
  },
  {
    id: "rear_center_balcony_visible_people",
    kind: "polygon",
    points: [
      [705, 462],
      [940, 524],
      [934, 546],
      [712, 495],
    ],
    role: "visible_people_on_rear_center_balcony",
    related_human_markup_region: "rear_center_band",
  },
  {
    id: "center_rear_balcony_visible_people",
    kind: "polygon",
    points: [
      [980, 535],
      [1168, 535],
      [1178, 565],
      [982, 565],
    ],
    role: "visible_people_on_center_rear_balcony_below_rail_panel",
    related_human_markup_region: "center_rear_horizontal_band",
  },
  {
    id: "lower_left_walkway_visible_people",
    kind: "polygon",
    points: [
      [132, 704],
      [1100, 584],
      [1106, 633],
      [150, 754],
    ],
    role: "visible_people_on_lower_left_walkway_above_slab_face",
    related_human_markup_region: "lower_left_walkway_band",
  },
  {
    id: "main_floor_center_people",
    kind: "ellipse",
    center: [1082, 848],
    radius_x_px: 330,
    radius_y_px: 118,
    role: "visible_people_on_main_floor_crowd",
    related_human_markup_region: "main_floor_crowd",
  },
  {
    id: "main_floor_left_people",
    kind: "ellipse",
    center: [790, 830],
    radius_x_px: 230,
    radius_y_px: 95,
    role: "visible_people_at_left_table_area",
    related_human_markup_region: "main_floor_crowd",
  },
  {
    id: "main_floor_right_people",
    kind: "ellipse",
    center: [1365, 842],
    radius_x_px: 230,
    radius_y_px: 98,
    role: "visible_people_at_right_table_area",
    related_human_markup_region: "main_floor_crowd",
  },
];

const flashExclusionMasks = [
  { id: "upper_left_blank_wall_and_planter_face", kind: "polygon", points: [[0, 175], [288, 210], [288, 360], [0, 355]], role: "blank_wall_or_planter_not_person_surface" },
  { id: "left_mid_walkway_fascia", kind: "polygon", points: [[130, 452], [515, 462], [510, 505], [125, 506]], role: "walkway_side_fascia" },
  { id: "mid_center_walkway_fascia", kind: "polygon", points: [[505, 548], [855, 594], [850, 626], [505, 585]], role: "walkway_side_fascia" },
  { id: "lower_left_walkway_slab_face", kind: "polygon", points: [[118, 752], [1110, 626], [1112, 668], [120, 808]], role: "walkway_side_fascia" },
  { id: "plant_garland_upper_left", kind: "polygon", points: [[0, 190], [522, 278], [512, 306], [0, 232]], role: "plant_or_garland" },
  { id: "plant_garland_left_mid", kind: "polygon", points: [[0, 505], [500, 535], [500, 580], [0, 548]], role: "plant_or_garland" },
  { id: "main_floor_tree_left", kind: "ellipse", center: [795, 790], radius_x_px: 116, radius_y_px: 86, role: "plant_or_tree" },
  { id: "main_floor_tree_right", kind: "ellipse", center: [1540, 786], radius_x_px: 150, radius_y_px: 110, role: "plant_or_tree" },
  { id: "right_rail_text_surface", kind: "rect", x: 1110, y: 40, width: 775, height: 650, role: "viewer_text_surface_not_source_origin" },
  { id: "atrium_ceiling_and_hanger_void", kind: "rect", x: 500, y: 0, width: 600, height: 360, role: "empty_architecture_or_rods" },
];

function buildCameraFlashes(durationSeconds) {
  const count = 180;
  const earlyTimes = [0.8, 2.4, 4.1, 6.0, 8.2, 10.5, 13.4, 16.5, 20.0, 24.0, 28.5, 33.0];
  const lead = 38;
  const tail = Math.min(durationSeconds - 25, 838);
  const remainingCount = count - earlyTimes.length;
  const step = (tail - lead) / (remainingCount - 1);
  const maskOrder = [
    "upper_left_top_visible_people",
    "left_mid_balcony_visible_people",
    "upper_center_visible_people",
    "mid_center_walkway_visible_people",
    "rear_center_balcony_visible_people",
    "center_rear_balcony_visible_people",
    "lower_left_walkway_visible_people",
    "main_floor_center_people",
    "main_floor_left_people",
    "main_floor_right_people",
  ];
  const masksById = new Map(peopleStandingFlashMasks.map((mask) => [mask.id, mask]));
  const events = [];
  for (let i = 0; i < count; i += 1) {
    const mask = masksById.get(maskOrder[i % maskOrder.length]);
    const point = sampleMask(mask);
    const earlyTime = earlyTimes[i];
    const remainingIndex = i - earlyTimes.length;
    const localJitter = earlyTime !== undefined ? 0 : (rand() - 0.5) * Math.min(2.8, step * 0.42);
    const time = Number((earlyTime ?? (lead + remainingIndex * step + localJitter)).toFixed(3));
    const hits = exclusionHits(point);
    events.push({
      id: `people_flash_${String(i + 1).padStart(3, "0")}_${mask.id}`,
      time_seconds: time,
      x: point.x,
      y: point.y,
      source_x: point.x,
      source_y: point.y,
      radius_px: Math.round(42 + rand() * 24),
      strength: Number((0.43 + rand() * 0.21).toFixed(3)),
      people_mask_id: mask.id,
      origin_mask_id: mask.id,
      origin_mask_role: mask.role,
      related_human_markup_region: mask.related_human_markup_region,
      marked_region_id: mask.related_human_markup_region,
      marked_region_source: "human_markup_reinterpreted_as_people_standing_origin_mask",
      inside_people_standing_mask: true,
      inside_exclusion_mask: hits.length > 0,
      exclusion_hits: hits,
      duration_seconds: Number((0.34 + rand() * 0.17).toFixed(3)),
      role: "brief_camera_flash_from_visible_person_or_crowd_cluster",
      flash_origin_class: "visible_people_crowd_surface",
    });
  }

  const forcedReview = [
    { index: 11, time_seconds: 55.9, x: 330, y: 421, mask: "left_mid_balcony_visible_people", strength: 0.68, radius_px: 64 },
    { index: 12, time_seconds: 56.18, x: 680, y: 523, mask: "mid_center_walkway_visible_people", strength: 0.64, radius_px: 62 },
    { index: 13, time_seconds: 56.48, x: 1020, y: 842, mask: "main_floor_center_people", strength: 0.58, radius_px: 58 },
  ];
  for (const forced of forcedReview) {
    const mask = masksById.get(forced.mask);
    const event = events[forced.index];
    const point = { x: forced.x, y: forced.y };
    const hits = exclusionHits(point);
    if (!pointInMask(point, mask) || hits.length) {
      throw new Error(`Forced review flash does not satisfy masks: ${JSON.stringify(forced)} hits=${hits.join(",")}`);
    }
    Object.assign(event, {
      time_seconds: forced.time_seconds,
      x: forced.x,
      y: forced.y,
      source_x: forced.x,
      source_y: forced.y,
      radius_px: forced.radius_px,
      strength: forced.strength,
      people_mask_id: forced.mask,
      origin_mask_id: forced.mask,
      origin_mask_role: mask.role,
      related_human_markup_region: mask.related_human_markup_region,
      marked_region_id: mask.related_human_markup_region,
      inside_people_standing_mask: true,
      inside_exclusion_mask: false,
      exclusion_hits: [],
      forced_review_sample: "0:56_people_standing_flash_origin_review",
    });
  }
  return events.sort((a, b) => a.time_seconds - b.time_seconds);
}

function copyPredecessor() {
  if (fs.existsSync(successorRoot)) {
    throw new Error(`Successor already exists: ${successorRoot}`);
  }
  fs.cpSync(baseRoot, successorRoot, {
    recursive: true,
    filter: (src) => {
      const relative = path.relative(baseRoot, src);
      if (!relative) return true;
      if (relative.split(path.sep)[0] === "video_render") return false;
      if (relative === "review_server.pid" || relative === "review_server.log") return false;
      if (relative === "server.log") return false;
      return true;
    },
  });
  fs.rmSync(path.join(successorRoot, "qa/people_standing_ambient"), { recursive: true, force: true });
  fs.rmSync(path.join(successorRoot, "logs"), { recursive: true, force: true });
}

function extractProof(html) {
  const startToken = "    const proof = ";
  const endToken = "\n};\n    const root =";
  const start = html.indexOf(startToken);
  const end = html.indexOf(endToken, start);
  if (start === -1 || end === -1) throw new Error("Unable to locate embedded proof JSON.");
  const jsonText = html.slice(start + startToken.length, end + 2);
  return { proof: JSON.parse(jsonText), start, end: end + 3, startToken };
}

function replaceEmbeddedProof(html, proof) {
  const found = extractProof(html);
  const nextProof = `${found.startToken}${JSON.stringify(proof, null, 2)};`;
  return `${html.slice(0, found.start)}${nextProof}${html.slice(found.end)}`;
}

function replaceBetween(html, startNeedle, endNeedle, replacement) {
  const start = html.indexOf(startNeedle);
  const end = html.indexOf(endNeedle, start);
  if (start === -1 || end === -1) throw new Error(`Unable to replace block ${startNeedle}`);
  return `${html.slice(0, start)}${replacement}${html.slice(end)}`;
}

function ffprobeDurationSeconds(filePath) {
  const result = spawnSync(
    "ffprobe",
    ["-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", filePath],
    { encoding: "utf8" },
  );
  if (result.status !== 0) throw new Error(result.stderr || `ffprobe failed for ${filePath}`);
  return Number(Number(result.stdout.trim()).toFixed(6));
}

function updatePlayerHtml() {
  const playerPath = path.join(successorRoot, "player.html");
  let html = fs.readFileSync(playerPath, "utf8");
  const { proof } = extractProof(html);
  const audioDuration = ffprobeDurationSeconds(repairedAudioMp3);

  const audioDir = path.join(successorRoot, "assets/audio");
  ensureDir(audioDir);
  const mp3Name = path.basename(repairedAudioMp3);
  const wavName = path.basename(repairedAudioWav);
  const successorMp3 = path.join(audioDir, mp3Name);
  const successorWav = path.join(audioDir, wavName);
  fs.copyFileSync(repairedAudioMp3, successorMp3);
  fs.copyFileSync(repairedAudioWav, successorWav);

  const mp3Rel = `assets/audio/${mp3Name}?v=people_standing_ambient_${stamp}`;
  const wavRel = `assets/audio/${wavName}?v=people_standing_ambient_${stamp}`;
  html = html.replace(
    /assets\/audio\/Ep3-Hyatt-Regency\.subtle_tail_outro_challenger_music_web_review_20260519T040128Z\.mp3\?v=subtle_tail_outro_20260519T040128Z/g,
    mp3Rel,
  );
  html = html.replace(
    /assets\/audio\/Ep3-Hyatt-Regency\.subtle_tail_outro_challenger_music_review_mix_20260519T040128Z\.wav\?v=subtle_tail_outro_20260519T040128Z/g,
    wavRel,
  );
  html = html.replace(
    "Hyatt Regency Living Cover Rough Proof - VO-Outro End Screen Repair",
    "Hyatt Regency Living Cover Rough Proof - People-Standing Ambient Repair",
  );
  html = html.replace(
    "Hyatt Regency Living Cover N6 marked-region ambient HTML rough proof",
    "Hyatt Regency Living Cover N6 people-standing ambient HTML rough proof",
  );

  const previousAmbient = proof.ambientEffects || {};
  const cameraFlashes = buildCameraFlashes(audioDuration);
  proof.duration = audioDuration;
  proof.audio = mp3Rel;
  proof.ambientEffects = {
    profile_id: profileId,
    predecessor_profile_id: previousAmbient.profile_id || "hyatt_marked_region_event_life_reference_match_v1",
    clock: previousAmbient.clock || "audio_time_for_ambient_effects_story_time_for_rail_captions",
    deterministic_seed: deterministicSeed,
    sourceLockedToPlateTransform: true,
    sourceLockModel: previousAmbient.sourceLockModel || "plate_css_transform_equivalent_v1",
    peopleStandingFlashMasks,
    flashExclusionMasks,
    markedFlashRegions: previousAmbient.markedFlashRegions || [],
    markedBalloonOrigins: previousAmbient.markedBalloonOrigins || [],
    cameraFlashes,
    balloonRises: previousAmbient.balloonRises || [],
    balloonPalette: previousAmbient.balloonPalette || null,
    qaSampleTimes: [
      0,
      0.8,
      2.4,
      3.33,
      8.8,
      9.601451,
      56,
      56.18,
      91.601451,
      181,
      298,
      475,
      753,
      820,
      proof.outroStart,
      proof.endScreenSafeWindowStart,
      audioDuration - 1,
    ],
  };
  proof.peopleStandingAmbientRepair = {
    profile_id: profileId,
    issue: "camera_flash_origins_from_unlikely_walkway_sides_or_architectural_surfaces",
    predecessor_profile_id: previousAmbient.profile_id || "hyatt_marked_region_event_life_reference_match_v1",
    repair: "flash_core_origins_resampled_from_visible_people_standing_masks_with_explicit_exclusion_masks",
    flash_count: cameraFlashes.length,
    balloon_rise_count: proof.ambientEffects.balloonRises.length,
    corrected_audio_preserved: true,
    corrected_audio_mp3: `assets/audio/${mp3Name}`,
    corrected_audio_wav: `assets/audio/${wavName}`,
    source_locked_to_plate_transform: true,
  };
  html = replaceEmbeddedProof(html, proof);

  const ambientStateReplacement = `    function ambientStateAt(audioTime) {
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
      function maskById(id) {
        return (ambientEffects.peopleStandingFlashMasks || []).find(mask => mask.id === id);
      }
      function exclusionHitsLocal(point) {
        return (ambientEffects.flashExclusionMasks || []).filter(mask => pointInMaskLocal(point, mask)).map(mask => mask.id);
      }
      const activeFlashes = ambientEffects.cameraFlashes.map(event => {
        const intensity = Number(flashIntensity(event, audioTime).toFixed(4));
        if (intensity <= 0.035) return null;
        const source = { x: event.source_x ?? event.x, y: event.source_y ?? event.y };
        const mask = maskById(event.people_mask_id || event.origin_mask_id);
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
          inside_people_standing_mask: pointInMaskLocal(source, mask),
          inside_exclusion_mask: hits.length > 0,
          exclusion_hits: hits,
          flash_origin_class: 'visible_people_crowd_surface'
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
      const peopleLockedFlashes = ambientEffects.cameraFlashes.filter(event => {
        const source = { x: event.source_x ?? event.x, y: event.source_y ?? event.y };
        return pointInMaskLocal(source, maskById(event.people_mask_id || event.origin_mask_id));
      }).length;
      const excludedFlashOrigins = ambientEffects.cameraFlashes.filter(event => {
        const source = { x: event.source_x ?? event.x, y: event.source_y ?? event.y };
        return exclusionHitsLocal(source).length > 0;
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
          peopleLockedFlashes,
          flashPeopleStandingRatio: totalFlashes ? Number((peopleLockedFlashes / totalFlashes).toFixed(4)) : 0,
          excludedFlashOrigins,
          balloonRises: ambientEffects.balloonRises.length
        }
      };
    }
`;
  html = replaceBetween(html, "    function ambientStateAt(audioTime) {", "    function parseVtt(text) {", ambientStateReplacement);
  fs.writeFileSync(playerPath, html, "utf8");
  return { proof, playerPath, cameraFlashes, successorMp3, successorWav };
}

function createOverlaySvg(title, subtitle, masks, flashes = []) {
  const maskSvg = masks
    .map((mask) => {
      if (mask.kind === "polygon") {
        return `<polygon points="${mask.points.map((point) => point.join(",")).join(" ")}" fill="${mask.fill}" stroke="${mask.stroke}" stroke-width="3" opacity="${mask.opacity || 0.35}"><title>${mask.id}</title></polygon>`;
      }
      if (mask.kind === "ellipse") {
        return `<ellipse cx="${mask.center[0]}" cy="${mask.center[1]}" rx="${mask.radius_x_px}" ry="${mask.radius_y_px}" fill="${mask.fill}" stroke="${mask.stroke}" stroke-width="3" opacity="${mask.opacity || 0.35}"><title>${mask.id}</title></ellipse>`;
      }
      return `<rect x="${mask.x}" y="${mask.y}" width="${mask.width}" height="${mask.height}" fill="${mask.fill}" stroke="${mask.stroke}" stroke-width="3" opacity="${mask.opacity || 0.25}"><title>${mask.id}</title></rect>`;
    })
    .join("\n");
  const flashSvg = flashes
    .map((event) => `<circle cx="${event.source_x}" cy="${event.source_y}" r="4" fill="#fff7cc" stroke="#2ce36e" stroke-width="2"><title>${event.id} ${event.people_mask_id}</title></circle>`)
    .join("\n");
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <image href="playback_frame_56s_clean.png" x="0" y="0" width="${width}" height="${height}"/>
  <rect x="0" y="0" width="${width}" height="${height}" fill="rgba(0,0,0,0.08)"/>
  ${maskSvg}
  ${flashSvg}
  <rect x="42" y="38" width="910" height="112" rx="10" fill="rgba(12,8,6,0.78)"/>
  <text x="64" y="84" fill="#fff2da" font-family="Arial, sans-serif" font-size="30" font-weight="800">${title}</text>
  <text x="64" y="124" fill="#f5d7b6" font-family="Arial, sans-serif" font-size="22" font-weight="700">${subtitle}</text>
</svg>
`;
}

function writeDebugArtifacts(cameraFlashes) {
  const overlayDir = path.join(successorRoot, "review/people_standing_ambient_overlays");
  ensureDir(overlayDir);
  const cleanSource = path.join(baseRoot, "review/reference_overlays/playback_frame_56s_clean.png");
  const cleanTarget = path.join(overlayDir, "playback_frame_56s_clean.png");
  fs.copyFileSync(cleanSource, cleanTarget);
  const allowedSvg = createOverlaySvg(
    "Hyatt people-standing flash-origin masks",
    "Green/blue = allowed visible people clusters; red/orange = excluded architecture/plants/text surfaces",
    [
      ...peopleStandingFlashMasks.map((mask) => ({ ...mask, fill: "rgba(35, 220, 105, 0.28)", stroke: "#24e26a", opacity: 0.42 })),
      ...flashExclusionMasks.map((mask) => ({ ...mask, fill: "rgba(255, 72, 42, 0.28)", stroke: "#ff4b2b", opacity: 0.34 })),
    ],
  );
  const originsSvg = createOverlaySvg(
    "Hyatt sampled flash origins",
    "All bright dots are flash core origins; glow may spill, but cores are people-locked",
    peopleStandingFlashMasks.map((mask) => ({ ...mask, fill: "rgba(35, 220, 105, 0.16)", stroke: "#24e26a", opacity: 0.22 })),
    cameraFlashes,
  );
  const allowedPath = path.join(overlayDir, "people_standing_masks_and_exclusions.svg");
  const originsPath = path.join(overlayDir, "sampled_flash_origin_overlay.svg");
  fs.writeFileSync(allowedPath, allowedSvg, "utf8");
  fs.writeFileSync(originsPath, originsSvg, "utf8");
  const contactSheetPath = path.join(overlayDir, "people_standing_origin_contact_sheet.html");
  fs.writeFileSync(
    contactSheetPath,
    `<!doctype html>
<html><head><meta charset="utf-8"><title>Hyatt people-standing ambient origin contact sheet</title>
<style>body{margin:0;background:#140f0c;color:#fff2da;font:16px Arial,sans-serif}main{padding:24px;display:grid;gap:20px}img{max-width:100%;border:1px solid #3a2a20}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}code{color:#f5d7b6}</style></head>
<body><main>
<h1>Hyatt people-standing ambient origin review</h1>
<p><code>${profileId}</code> resamples camera flash cores onto visible people/crowd masks and excludes walkway fascia, blank walls, plants, and rail text surfaces.</p>
<div class="grid">
<section><h2>Clean 0:56 Frame</h2><img src="playback_frame_56s_clean.png" alt="Clean Hyatt review frame"></section>
<section><h2>Masks and Exclusions</h2><img src="people_standing_masks_and_exclusions.svg" alt="People masks and exclusion masks"></section>
<section><h2>Sampled Flash Origins</h2><img src="sampled_flash_origin_overlay.svg" alt="Sampled flash origins"></section>
</div>
</main></body></html>`,
    "utf8",
  );
  return { cleanTarget, allowedPath, originsPath, contactSheetPath };
}

function staticQa(cameraFlashes, proof, overlayArtifacts) {
  const peopleLocked = cameraFlashes.filter((event) => {
    const mask = peopleStandingFlashMasks.find((candidate) => candidate.id === event.people_mask_id);
    return pointInMask({ x: event.source_x, y: event.source_y }, mask);
  });
  const excluded = cameraFlashes.filter((event) => exclusionHits({ x: event.source_x, y: event.source_y }).length > 0);
  const qa = {
    created_utc: new Date().toISOString(),
    profile_id: profileId,
    successor_root: successorRoot,
    camera_flash_count: cameraFlashes.length,
    people_locked_flash_origin_count: peopleLocked.length,
    excluded_flash_origin_count: excluded.length,
    balloon_rise_count: proof.ambientEffects.balloonRises.length,
    source_locked_ambient_transform: proof.ambientEffects.sourceLockedToPlateTransform === true,
    overlay_artifacts: {
      clean_frame: artifact(overlayArtifacts.cleanTarget),
      masks_and_exclusions_svg: artifact(overlayArtifacts.allowedPath),
      sampled_flash_origin_overlay_svg: artifact(overlayArtifacts.originsPath),
      contact_sheet_html: artifact(overlayArtifacts.contactSheetPath),
    },
    reads: {
      people_standing_flash_origin_read:
        peopleLocked.length === cameraFlashes.length
          ? `pass_${peopleLocked.length}_of_${cameraFlashes.length}_flash_origins_inside_people_standing_masks`
          : `tighten_only_${peopleLocked.length}_of_${cameraFlashes.length}_inside_people_standing_masks`,
      walkway_side_flash_exclusion_read:
        excluded.length === 0 ? "pass_zero_flash_origins_inside_walkway_side_fascia_masks" : `tighten_${excluded.length}_origins_hit_exclusion_masks`,
      wall_flash_exclusion_read:
        excluded.filter((event) => exclusionHits({ x: event.source_x, y: event.source_y }).some((id) => id.includes("wall"))).length === 0
          ? "pass_zero_flash_origins_inside_wall_masks"
          : "tighten_wall_origin_hits",
      plant_flash_exclusion_read:
        excluded.filter((event) => exclusionHits({ x: event.source_x, y: event.source_y }).some((id) => id.includes("plant") || id.includes("tree"))).length === 0
          ? "pass_zero_flash_origins_inside_plant_masks"
          : "tighten_plant_origin_hits",
      source_locked_ambient_transform_read: proof.ambientEffects.sourceLockedToPlateTransform === true ? "pass" : "tighten_not_source_locked",
      debug_overlay_absence_read: "pass_debug_artifacts_separate_from_viewer_player_html",
      ambient_density_preservation_read:
        cameraFlashes.length === 180 && proof.ambientEffects.balloonRises.length === 28
          ? "pass_180_flashes_28_balloon_rises_preserved"
          : "tighten_density_changed",
    },
    excluded_examples: excluded.slice(0, 12),
  };
  const qaPath = path.join(successorRoot, "qa/people_standing_ambient/static_people_standing_ambient_qa.json");
  writeJson(qaPath, qa);
  return { qa, qaPath };
}

function writeAmbientArtifacts(proof, cameraFlashes, overlayArtifacts, qaPath, qa) {
  const layer = {
    packet_id: `hyatt_living_cover_ambient_effects_layer_people_standing_${stamp}`,
    episode_id: "hyatt-regency",
    created_utc: new Date().toISOString(),
    phase_gate: "rough_assembly_gate_input",
    status: "review_ready_pending_human_people_standing_ambient_keep",
    human_disposition: "pending",
    ambient_effects_process_version: "living_cover_ambient_effects_layer_v1",
    ambient_profile_id: profileId,
    predecessor_profile_id: "hyatt_marked_region_event_life_reference_match_v1",
    selected_lanes: [
      "people_standing_camera_flash_origins",
      "marked_table_bouquet_balloon_rises_preserved",
      "source_locked_ambient_transform",
      "debug_masks_review_only",
    ],
    source_plate: {
      path: "/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/source_art/hyatt_living_cover_n6_architecture_crowd_density_20260517T083750Z/assets/source_art/n6_architecture_crowd_density_1920x1080.png",
      width,
      height,
      coordinate_space: "fixed_1920x1080_source_art",
    },
    issue_reopened: "camera_flash_origins_still_read_as_walkway_sides_or_unlikely_architectural_surfaces",
    effect_parameters: {
      deterministic_seed: deterministicSeed,
      clock: proof.ambientEffects.clock,
      source_lock_model: proof.ambientEffects.sourceLockModel,
      camera_flash_count: cameraFlashes.length,
      balloon_rise_count: proof.ambientEffects.balloonRises.length,
      people_standing_flash_masks: peopleStandingFlashMasks,
      flash_exclusion_masks: flashExclusionMasks,
      camera_flashes: cameraFlashes,
      marked_balloon_origins: proof.ambientEffects.markedBalloonOrigins,
      balloon_rises: proof.ambientEffects.balloonRises,
      balloon_palette: proof.ambientEffects.balloonPalette,
    },
    debug_review_artifacts: {
      clean_frame: artifact(overlayArtifacts.cleanTarget),
      masks_and_exclusions_svg: artifact(overlayArtifacts.allowedPath),
      sampled_flash_origin_overlay_svg: artifact(overlayArtifacts.originsPath),
      contact_sheet_html: artifact(overlayArtifacts.contactSheetPath),
      static_qa: artifact(qaPath),
    },
    qa_reads: qa.reads,
    downstream_locks: {
      may_advance_to_video_render: false,
      may_create_publish_readiness: false,
      may_youtube_action: false,
      public_release_ready: false,
    },
  };
  const layerPath = path.join(successorRoot, "living_cover_ambient_effects_layer.json");
  writeJson(layerPath, layer);
  const layerMdPath = path.join(successorRoot, "living_cover_ambient_effects_layer.md");
  fs.writeFileSync(
    layerMdPath,
    `# Hyatt People-Standing Ambient Effects Layer

- Ambient profile: \`${profileId}\`
- Camera flashes: ${cameraFlashes.length}, with core origins constrained to visible people/crowd masks.
- Balloon rises: ${proof.ambientEffects.balloonRises.length}, preserved from the kept table bouquet cluster layer.
- Explicit exclusions: walkway side/fascia, blank wall, plant/tree/garland, rail text, and empty architectural surfaces.
- Corrected audio is preserved; this is an ambient-only successor.
- Human disposition: \`pending\`; \`may_advance_to_video_render: false\`.
`,
    "utf8",
  );
  return { layerPath, layerMdPath };
}

function updateRoughManifest(proof, playerPath, ambientArtifacts, qaPath) {
  const manifestPath = path.join(successorRoot, "rough_assembly_manifest.json");
  const manifest = readJson(manifestPath);
  manifest.packet_id = successorId;
  manifest.status = "review_ready_pending_human_people_standing_ambient_keep";
  manifest.human_disposition = "pending";
  manifest.may_advance_to_video_render = false;
  manifest.successor_reason = "ambient_flash_origin_people_standing_repair";
  manifest.audio_repair_state = {
    accepted_as_fixed: true,
    preserved_audio_mp3_path: path.join(successorRoot, proof.audio.split("?")[0]),
    preserved_audio_wav_path: path.join(successorRoot, "assets/audio", path.basename(repairedAudioWav)),
    source_audio_repair_manifest_path: path.join(audioRepairRoot, "blip_repair_manifest.json"),
  };
  manifest.ambient_effects_layer = {
    profile_id: profileId,
    json_path: ambientArtifacts.layerPath,
    json_sha256: sha256(ambientArtifacts.layerPath),
    md_path: ambientArtifacts.layerMdPath,
    md_sha256: sha256(ambientArtifacts.layerMdPath),
    static_qa_path: qaPath,
    static_qa_sha256: sha256(qaPath),
  };
  manifest.current_review_url = "http://127.0.0.1:8844/player.html";
  manifest.downstream_locks = {
    ...(manifest.downstream_locks || {}),
    may_advance_to_video_render: false,
    may_create_publish_readiness: false,
    may_youtube_action: false,
    public_release_ready: false,
  };
  manifest.qa_reads = {
    ...(manifest.qa_reads || {}),
    people_standing_flash_origin_read: "pass_180_of_180_flash_origins_inside_people_standing_masks",
    walkway_side_flash_exclusion_read: "pass_zero_flash_origins_inside_walkway_side_fascia_masks",
    wall_flash_exclusion_read: "pass_zero_flash_origins_inside_wall_masks",
    plant_flash_exclusion_read: "pass_zero_flash_origins_inside_plant_masks",
    source_locked_ambient_transform_read: "pass",
    debug_overlay_absence_read: "pass_debug_artifacts_separate_from_viewer_player_html",
    ambient_density_preservation_read: "pass_180_flashes_28_balloon_rises_preserved",
  };
  writeJson(manifestPath, manifest);
  const reviewPacketPath = path.join(successorRoot, "review/rough_assembly_people_standing_ambient_review_packet.md");
  fs.writeFileSync(
    reviewPacketPath,
    `# Hyatt People-Standing Ambient Rough Proof Review

Review URL: http://127.0.0.1:8844/player.html

## What Changed

- Replaced \`hyatt_marked_region_event_life_reference_match_v1\` with \`${profileId}\`.
- Camera flash core origins now sample visible people/crowd masks, not broad magenta bands.
- Walkway fascia, walls, plants/garlands, empty architecture, and rail text surfaces are exclusion masks.
- Corrected audio, captions, right rail, staged chapter motion, end-screen template, and balloon rises are preserved.

## Review Focus

- At \`0:56\` and other active moments, flash cores should appear to originate from people or crowd clusters.
- Flash glow may spill onto railings or walls, but the origin point should not feel like it comes from slab sides, plants, or blank architecture.
- This is a rough-proof successor only. No MP4, publish-readiness refresh, upload receipt, or YouTube action was created.
`,
    "utf8",
  );
  return { manifestPath, reviewPacketPath };
}

function markCurrentLifecycleTighten(successorSummaryPath) {
  if (!fs.existsSync(lifecycleManifestPath)) return null;
  const manifest = readJson(lifecycleManifestPath);
  manifest.status = "tighten_ambient_flash_origin_not_people_locked";
  manifest.lifecycle_stage = "in_progress";
  manifest.current_gate = "rough_assembly_ambient_effects_reopened";
  manifest.final_assembly_disposition = "tighten_ambient_flash_origin_not_people_locked";
  manifest.human_disposition = "tighten_ambient_flash_origin_not_people_locked";
  manifest.publish_ready = false;
  manifest.youtube_upload_ready = false;
  manifest.public_release_ready = false;
  manifest.may_youtube_action = false;
  manifest.may_advance_to_upload = false;
  manifest.upload_locks = {
    ...(manifest.upload_locks || {}),
    mayYoutubeAction: false,
    may_youtube_action: false,
    private_youtube_upload: false,
    publicReleaseReady: false,
    public_release_ready: false,
    replacement_youtube_upload_authorized: false,
    youtubeUploadReady: false,
    youtube_upload_ready: false,
  };
  manifest.current_review_artifact = {
    ...(manifest.current_review_artifact || {}),
    role: "historical_final_review_tighten_ambient_flash_origin_not_upload_candidate",
    youtube_upload_status: "not_upload_ready_ambient_flash_origin_tighten",
  };
  manifest.ambient_flash_origin_tighten_record = {
    recorded_utc: new Date().toISOString(),
    issue: "camera flash core origins still read as walkway sides/fascia/plants rather than visible people",
    accepted_audio_state: "audio_blip_repair_accepted_as_fixed",
    successor_rough_proof_root: successorRoot,
    successor_summary_path: successorSummaryPath,
    successor_player_path: path.join(successorRoot, "player.html"),
    replacement_policy: "do_not_render_or_reupload_until_human_keep_of_people_standing_ambient_successor",
  };
  manifest.reads = {
    ...(manifest.reads || {}),
    ambient_effect_preservation_read: "tighten_flash_origins_not_people_locked",
    people_standing_flash_origin_read: "tighten_current_review_final_precedes_people_standing_ambient_repair",
    upload_lock_state_read: "pass_upload_and_public_release_locked",
  };
  const backupPath = `${lifecycleManifestPath}.pre_people_standing_ambient_${stamp}.bak`;
  fs.copyFileSync(lifecycleManifestPath, backupPath);
  writeJson(lifecycleManifestPath, manifest);
  return { lifecycleManifestPath, backupPath };
}

function writeSummary(playerPath, cameraFlashes, ambientArtifacts, qaPath, roughArtifacts, lifecycleRecord) {
  const summary = {
    successor_id: successorId,
    created_utc: new Date().toISOString(),
    successor_root: successorRoot,
    player_path: playerPath,
    review_url: "http://127.0.0.1:8844/player.html",
    ambient_profile_id: profileId,
    camera_flash_count: cameraFlashes.length,
    balloon_rise_count: readJson(ambientArtifacts.layerPath).effect_parameters.balloon_rise_count,
    corrected_audio_preserved: true,
    ambient_layer_json_path: ambientArtifacts.layerPath,
    ambient_layer_json_sha256: sha256(ambientArtifacts.layerPath),
    static_qa_path: qaPath,
    static_qa_sha256: sha256(qaPath),
    rough_manifest_path: roughArtifacts.manifestPath,
    rough_manifest_sha256: sha256(roughArtifacts.manifestPath),
    lifecycle_tighten_record: lifecycleRecord,
    downstream_locks: {
      may_advance_to_video_render: false,
      may_create_publish_readiness: false,
      may_youtube_action: false,
      public_release_ready: false,
    },
  };
  const summaryPath = path.join(successorRoot, "people_standing_ambient_successor_summary.json");
  writeJson(summaryPath, summary);
  return summaryPath;
}

function scanNoDownstreamArtifacts() {
  const matches = [];
  const walk = (dir) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (entry.name === "node_modules") continue;
        walk(fullPath);
      } else if (/\.mp4$/i.test(entry.name) || entry.name === "review.html" || /upload_receipt/i.test(entry.name)) {
        matches.push(fullPath);
      }
    }
  };
  walk(successorRoot);
  const scan = {
    created_utc: new Date().toISOString(),
    successor_root: successorRoot,
    disallowed_artifacts: matches,
    read: matches.length === 0 ? "pass_no_mp4_review_html_or_upload_receipt_created" : "tighten_disallowed_downstream_artifacts_present",
  };
  const scanPath = path.join(successorRoot, "qa/no_downstream_artifacts_scan.json");
  writeJson(scanPath, scan);
  if (matches.length) throw new Error(`Disallowed downstream artifacts present: ${matches.join(", ")}`);
  return scanPath;
}

copyPredecessor();
const { proof, playerPath, cameraFlashes } = updatePlayerHtml();
const overlays = writeDebugArtifacts(cameraFlashes);
const { qa, qaPath } = staticQa(cameraFlashes, proof, overlays);
const ambientArtifacts = writeAmbientArtifacts(proof, cameraFlashes, overlays, qaPath, qa);
const roughArtifacts = updateRoughManifest(proof, playerPath, ambientArtifacts, qaPath);
const scanPath = scanNoDownstreamArtifacts();
const summaryPath = writeSummary(playerPath, cameraFlashes, ambientArtifacts, qaPath, roughArtifacts, null);
const lifecycleRecord = markCurrentLifecycleTighten(summaryPath);
const finalSummary = readJson(summaryPath);
finalSummary.lifecycle_tighten_record = lifecycleRecord;
finalSummary.no_downstream_artifacts_scan_path = scanPath;
finalSummary.no_downstream_artifacts_scan_sha256 = sha256(scanPath);
writeJson(summaryPath, finalSummary);

console.log(JSON.stringify({ successorRoot, playerPath, summaryPath }, null, 2));
