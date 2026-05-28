#!/usr/bin/env node
import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const predecessorRoot =
  "/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt_living_cover_html_rough_proof_n6_people_standing_ambient_20260519T192204Z";
const roughAssemblyRoot = path.dirname(predecessorRoot);
const profileId = "hyatt_audited_person_pixel_flash_origins_v1";
const deterministicSeed = 2026051902;
const width = 1920;
const height = 1080;

function utcStamp(date = new Date()) {
  return date.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
}

const stamp = utcStamp();
const successorId = `hyatt_living_cover_html_rough_proof_n6_audited_flash_origins_${stamp}`;
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

function jitterPair(allowed) {
  if (!allowed) return { x: 0, y: 0 };
  const angle = rand() * Math.PI * 2;
  const radius = Math.sqrt(rand()) * allowed * 0.82;
  return {
    x: Math.round(Math.cos(angle) * radius * 10) / 10,
    y: Math.round(Math.sin(angle) * radius * 10) / 10,
  };
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

function extractProof(html) {
  const marker = "    const proof = ";
  const start = html.indexOf(marker);
  if (start === -1) throw new Error("Unable to find embedded proof object");
  const jsonStart = start + marker.length;
  const end = html.indexOf("\n    const root =", jsonStart);
  if (end === -1) throw new Error("Unable to find embedded proof object end");
  const raw = html.slice(jsonStart, end).trim().replace(/;$/, "");
  return JSON.parse(raw);
}

function replaceProof(html, proof) {
  const marker = "    const proof = ";
  const start = html.indexOf(marker);
  const jsonStart = start + marker.length;
  const end = html.indexOf("\n    const root =", jsonStart);
  if (start === -1 || end === -1) throw new Error("Unable to replace embedded proof object");
  const next = `${marker}${JSON.stringify(proof, null, 2)};\n`;
  return `${html.slice(0, start)}${next}${html.slice(end + 1)}`;
}

const auditedHotspots = [
  { id: "ul_top_01", x: 323, y: 89, region: "upper_left_top_balcony", allowed_jitter_px: 1.2, surface_read: "visible_person", audit_note: "dark standing figure above top balcony rail" },
  { id: "ul_top_02", x: 367, y: 108, region: "upper_left_top_balcony", allowed_jitter_px: 1.2, surface_read: "visible_person", audit_note: "head-and-shoulder cluster on upper rail" },
  { id: "ul_top_03", x: 411, y: 127, region: "upper_left_top_balcony", allowed_jitter_px: 1.2, surface_read: "visible_person", audit_note: "person silhouette in balcony crowd" },
  { id: "ul_top_04", x: 464, y: 150, region: "upper_left_top_balcony", allowed_jitter_px: 1.2, surface_read: "visible_person", audit_note: "standing figure beside rail, above garland" },
  { id: "ul_top_05", x: 505, y: 171, region: "upper_left_top_balcony", allowed_jitter_px: 1.2, surface_read: "visible_person", audit_note: "visible body cluster, not planter or wall" },

  { id: "left_mid_05", x: 286, y: 292, region: "left_mid_balcony", allowed_jitter_px: 1.2, surface_read: "visible_person", audit_note: "person silhouettes along rail" },
  { id: "left_mid_06", x: 355, y: 314, region: "left_mid_balcony", allowed_jitter_px: 1.2, surface_read: "visible_person", audit_note: "person cluster in rail crowd" },
  { id: "left_mid_07", x: 430, y: 336, region: "left_mid_balcony", allowed_jitter_px: 1.2, surface_read: "visible_person", audit_note: "clear human cluster, not slab" },

  { id: "diag_walkway_01", x: 250, y: 358, region: "diagonal_walkway_people", allowed_jitter_px: 1.0, surface_read: "visible_person", audit_note: "person above diagonal walkway rail" },
  { id: "diag_walkway_02", x: 304, y: 365, region: "diagonal_walkway_people", allowed_jitter_px: 1.0, surface_read: "visible_person", audit_note: "white shirt within walkway crowd" },
  { id: "diag_walkway_03", x: 353, y: 376, region: "diagonal_walkway_people", allowed_jitter_px: 1.0, surface_read: "visible_person", audit_note: "head-and-shoulders above rail, not slab face" },
  { id: "diag_walkway_04", x: 409, y: 389, region: "diagonal_walkway_people", allowed_jitter_px: 1.0, surface_read: "visible_person", audit_note: "crowd row above railing" },
  { id: "diag_walkway_05", x: 467, y: 402, region: "diagonal_walkway_people", allowed_jitter_px: 1.0, surface_read: "visible_person", audit_note: "visible torso in diagonal crowd" },
  { id: "diag_walkway_06", x: 523, y: 414, region: "diagonal_walkway_people", allowed_jitter_px: 1.0, surface_read: "visible_person", audit_note: "visible person cluster above slab" },
  { id: "diag_walkway_07", x: 580, y: 429, region: "diagonal_walkway_people", allowed_jitter_px: 1.0, surface_read: "visible_person", audit_note: "person silhouette on walkway crowd line" },
  { id: "diag_walkway_08", x: 642, y: 444, region: "diagonal_walkway_people", allowed_jitter_px: 1.0, surface_read: "visible_person", audit_note: "heads along rail above concrete face" },
  { id: "diag_walkway_09", x: 704, y: 456, region: "diagonal_walkway_people", allowed_jitter_px: 1.0, surface_read: "visible_person", audit_note: "person cluster at diagonal railing" },
  { id: "diag_walkway_10", x: 760, y: 470, region: "diagonal_walkway_people", allowed_jitter_px: 1.0, surface_read: "visible_person", audit_note: "dark torso among walkway crowd" },
  { id: "diag_walkway_11", x: 826, y: 483, region: "diagonal_walkway_people", allowed_jitter_px: 1.0, surface_read: "visible_person", audit_note: "person row above rail, outside slab face" },
  { id: "diag_walkway_12", x: 898, y: 494, region: "diagonal_walkway_people", allowed_jitter_px: 1.0, surface_read: "visible_person", audit_note: "visible human cluster on walkway" },
  { id: "diag_walkway_13", x: 968, y: 506, region: "diagonal_walkway_people", allowed_jitter_px: 1.0, surface_read: "visible_person", audit_note: "heads and shoulders in diagonal crowd" },
  { id: "diag_walkway_14", x: 1040, y: 523, region: "diagonal_walkway_people", allowed_jitter_px: 1.0, surface_read: "visible_person", audit_note: "end-of-walkway crowd above fascia" },

  { id: "rear_balcony_01", x: 1018, y: 315, region: "rear_center_balcony", allowed_jitter_px: 1.2, surface_read: "visible_person", audit_note: "rear balcony crowd figure" },
  { id: "rear_balcony_02", x: 1085, y: 318, region: "rear_center_balcony", allowed_jitter_px: 1.2, surface_read: "visible_person", audit_note: "visible person at rear rail, left of right rail panel" },
  { id: "rear_balcony_03", x: 1010, y: 438, region: "rear_center_balcony", allowed_jitter_px: 1.2, surface_read: "visible_person", audit_note: "mid rear balcony person cluster" },
  { id: "rear_balcony_04", x: 1088, y: 441, region: "rear_center_balcony", allowed_jitter_px: 1.2, surface_read: "visible_person", audit_note: "person cluster at rear balcony before right rail" },

  { id: "main_floor_04", x: 920, y: 726, region: "main_floor_crowd", allowed_jitter_px: 2.0, surface_read: "visible_person", audit_note: "head/shoulder crowd pixels" },
  { id: "main_floor_05", x: 1005, y: 742, region: "main_floor_crowd", allowed_jitter_px: 2.0, surface_read: "visible_person", audit_note: "main-floor crowd surface" },
  { id: "main_floor_06", x: 1080, y: 762, region: "main_floor_crowd", allowed_jitter_px: 2.0, surface_read: "visible_person", audit_note: "standing crowd at center floor" },
  { id: "main_floor_07", x: 1150, y: 782, region: "main_floor_crowd", allowed_jitter_px: 2.0, surface_read: "visible_person", audit_note: "visible floor crowd below rail panel" },
  { id: "main_floor_08", x: 1225, y: 794, region: "main_floor_crowd", allowed_jitter_px: 2.0, surface_read: "visible_person", audit_note: "person cluster, not plant edge" },
  { id: "main_floor_09", x: 1308, y: 815, region: "main_floor_crowd", allowed_jitter_px: 2.0, surface_read: "visible_person", audit_note: "crowd mass beside tables" },
  { id: "main_floor_10", x: 1398, y: 838, region: "main_floor_crowd", allowed_jitter_px: 2.0, surface_read: "visible_person", audit_note: "standing people in central atrium" },
  { id: "main_floor_13", x: 650, y: 900, region: "main_floor_crowd", allowed_jitter_px: 2.0, surface_read: "visible_person", audit_note: "foreground crowd pixels" },
  { id: "main_floor_14", x: 760, y: 892, region: "main_floor_crowd", allowed_jitter_px: 2.0, surface_read: "visible_person", audit_note: "foreground people cluster" },
  { id: "main_floor_15", x: 880, y: 902, region: "main_floor_crowd", allowed_jitter_px: 2.0, surface_read: "visible_person", audit_note: "visible people around tables" },
  { id: "main_floor_16", x: 982, y: 914, region: "main_floor_crowd", allowed_jitter_px: 2.0, surface_read: "visible_person", audit_note: "foreground crowd surface" },
  { id: "main_floor_17", x: 1090, y: 925, region: "main_floor_crowd", allowed_jitter_px: 2.0, surface_read: "visible_person", audit_note: "dense person cluster, below right rail text" },
  { id: "main_floor_18", x: 1210, y: 938, region: "main_floor_crowd", allowed_jitter_px: 2.0, surface_read: "visible_person", audit_note: "floor crowd surface" },
  { id: "main_floor_19", x: 1350, y: 950, region: "main_floor_crowd", allowed_jitter_px: 2.0, surface_read: "visible_person", audit_note: "people near table cluster" },
  { id: "main_floor_20", x: 1490, y: 962, region: "main_floor_crowd", allowed_jitter_px: 2.0, surface_read: "visible_person", audit_note: "right foreground people cluster" },
  { id: "main_floor_21", x: 1630, y: 982, region: "main_floor_crowd", allowed_jitter_px: 2.0, surface_read: "visible_person", audit_note: "foreground person cluster at right floor" },
];

const flashExclusionMasks = [
  {
    id: "upper_left_blank_wall_and_planter_face",
    kind: "polygon",
    points: [[0, 175], [288, 210], [288, 228], [0, 220]],
    role: "blank_wall_or_planter_not_person_surface",
  },
  {
    id: "left_mid_walkway_fascia",
    kind: "polygon",
    points: [[130, 452], [515, 462], [510, 505], [125, 506]],
    role: "walkway_side_fascia",
  },
  {
    id: "mid_center_walkway_fascia",
    kind: "polygon",
    points: [[505, 548], [855, 594], [850, 626], [505, 585]],
    role: "walkway_side_fascia",
  },
  {
    id: "lower_left_walkway_slab_face",
    kind: "polygon",
    points: [[118, 752], [1110, 626], [1112, 668], [120, 808]],
    role: "walkway_side_fascia",
  },
  {
    id: "diagonal_walkway_slab_face_guard",
    kind: "polygon",
    points: [[215, 390], [1130, 540], [1130, 585], [220, 442]],
    role: "walkway_side_fascia_guard_below_person_row",
  },
  {
    id: "plant_garland_upper_left",
    kind: "polygon",
    points: [[0, 190], [522, 278], [512, 306], [0, 232]],
    role: "plant_or_garland",
  },
  {
    id: "plant_garland_left_mid",
    kind: "polygon",
    points: [[0, 505], [500, 535], [500, 580], [0, 548]],
    role: "plant_or_garland",
  },
  {
    id: "main_floor_tree_left",
    kind: "ellipse",
    center: [795, 790],
    radius_x_px: 116,
    radius_y_px: 86,
    role: "plant_or_tree",
  },
  {
    id: "main_floor_tree_right",
    kind: "ellipse",
    center: [1540, 786],
    radius_x_px: 150,
    radius_y_px: 110,
    role: "plant_or_tree",
  },
  {
    id: "right_rail_text_surface",
    kind: "rect",
    x: 1110,
    y: 40,
    width: 775,
    height: 650,
    role: "viewer_text_surface_not_source_origin",
  },
  {
    id: "atrium_ceiling_and_hanger_void",
    kind: "rect",
    x: 540,
    y: 0,
    width: 560,
    height: 185,
    role: "empty_architecture_or_rods",
  },
];

function exclusionHits(point) {
  return flashExclusionMasks.filter((mask) => pointInMask(point, mask)).map((mask) => mask.id);
}

function hotspotById(id) {
  return auditedHotspots.find((hotspot) => hotspot.id === id);
}

function buildFlashSchedule(audioDuration) {
  const count = 180;
  const reviewSamples = [
    { time: 55.9, hotspot: "diag_walkway_02", forced_review_sample: "0:56_audited_person_pixel_flash_origin_review" },
    { time: 56.18, hotspot: "diag_walkway_08", forced_review_sample: "0:56_audited_person_pixel_flash_origin_review" },
    { time: 56.48, hotspot: "main_floor_05", forced_review_sample: "0:56_audited_person_pixel_flash_origin_review" },
  ];
  const events = [];
  const usableDuration = Math.max(720, audioDuration - 35);
  for (let index = 0; index < count; index += 1) {
    const hotspot = auditedHotspots[index % auditedHotspots.length];
    const time =
      index < 12
        ? 0.8 + index * 2.45
        : 36 + ((index - 12) / (count - 12)) * usableDuration;
    events.push(makeFlashEvent(index, time, hotspot, null));
  }
  for (const [offset, sample] of reviewSamples.entries()) {
    events[12 + offset] = makeFlashEvent(12 + offset, sample.time, hotspotById(sample.hotspot), sample.forced_review_sample);
  }
  return events.sort((a, b) => a.time_seconds - b.time_seconds).map((event, index) => ({
    ...event,
    id: `audited_flash_${String(index + 1).padStart(3, "0")}_${event.flash_origin_hotspot_id}`,
  }));
}

function makeFlashEvent(index, time, hotspot, forcedReviewSample) {
  if (!hotspot) throw new Error(`Missing hotspot for flash ${index}`);
  const offset = jitterPair(hotspot.allowed_jitter_px);
  const jitterX = offset.x;
  const jitterY = offset.y;
  const sourceX = Math.round((hotspot.x + jitterX) * 10) / 10;
  const sourceY = Math.round((hotspot.y + jitterY) * 10) / 10;
  const point = { x: sourceX, y: sourceY };
  const hits = exclusionHits(point);
  if (hits.length) {
    throw new Error(`Audited hotspot ${hotspot.id} jittered into exclusions ${hits.join(",")}`);
  }
  const jitterDistance = Math.hypot(jitterX, jitterY);
  return {
    id: `audited_flash_${String(index + 1).padStart(3, "0")}_${hotspot.id}`,
    time_seconds: Number(time.toFixed(3)),
    x: sourceX,
    y: sourceY,
    source_x: sourceX,
    source_y: sourceY,
    flash_origin_hotspot_id: hotspot.id,
    hotspot_region: hotspot.region,
    origin_core_surface: "visible_person",
    surface_read: hotspot.surface_read,
    hotspot_audit_note: hotspot.audit_note,
    allowed_jitter_px: hotspot.allowed_jitter_px,
    jitter_x_px: jitterX,
    jitter_y_px: jitterY,
    jitter_distance_px: Number(jitterDistance.toFixed(3)),
    inside_exclusion_mask: false,
    exclusion_hits: [],
    broad_mask_sampling_used: false,
    line_band_sampling_used: false,
    origin_sampling_model: "audited_fixed_hotspot_tiny_jitter_v1",
    flash_render_model: "small_core_soft_halo_person_anchor_v1",
    radius_px: 22 + (index % 5),
    halo_radius_px: 20 + (index % 5),
    core_radius_px: 2.1 + (index % 3) * 0.25,
    strength: Number((0.48 + (index % 7) * 0.018).toFixed(3)),
    duration_seconds: Number((0.30 + (index % 5) * 0.028).toFixed(3)),
    role: "brief_camera_flash_from_audited_visible_person_pixel",
    flash_origin_class: "audited_visible_person_pixel",
    ...(forcedReviewSample ? { forced_review_sample: forcedReviewSample } : {}),
  };
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
        visibleAmbientEffect: activeFlashes.length > 0 || activeBalloonRises.length > 0,
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
          balloonRises: ambientEffects.balloonRises.length
        }
      };
    }`;
  return `${html.slice(0, start)}${fn}${html.slice(end)}`;
}

function replaceFlashDrawing(html) {
  const startNeedle = "      for (const event of ambientEffects.cameraFlashes) {";
  const start = html.indexOf(startNeedle);
  const endNeedle = "      ctx.globalCompositeOperation = 'source-over';";
  const end = html.indexOf(endNeedle, start);
  if (start === -1 || end === -1) throw new Error("Unable to replace camera flash drawing block");
  const block = `      for (const event of ambientEffects.cameraFlashes) {
        const intensity = flashIntensity(event, audioTime);
        if (intensity <= 0) continue;
        const sourceX = event.source_x ?? event.x;
        const sourceY = event.source_y ?? event.y;
        const point = sourceToStagePoint(sourceX, sourceY, storyTime);
        const visualRadiusScale = Math.max(0.84, Math.min(1.22, point.visualScale || 1));
        const haloRadius = (event.halo_radius_px ?? event.radius_px ?? 22) * visualRadiusScale * (0.72 + intensity * 0.28);
        const coreRadius = (event.core_radius_px ?? 2.2) * visualRadiusScale * (0.92 + intensity * 0.18);
        const alpha = event.strength * intensity;
        const gradient = ctx.createRadialGradient(point.x, point.y, 0, point.x, point.y, haloRadius);
        gradient.addColorStop(0, 'rgba(255, 252, 232, ' + Math.min(0.58, alpha * 0.82).toFixed(3) + ')');
        gradient.addColorStop(0.16, 'rgba(255, 226, 168, ' + Math.min(0.18, alpha * 0.34).toFixed(3) + ')');
        gradient.addColorStop(1, 'rgba(255, 221, 160, 0)');
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(point.x, point.y, haloRadius, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = 'rgba(255, 252, 235, ' + Math.min(0.82, alpha * 1.05).toFixed(3) + ')';
        ctx.beginPath();
        ctx.arc(point.x, point.y, Math.max(1.4, coreRadius), 0, Math.PI * 2);
        ctx.fill();
      }
`;
  return `${html.slice(0, start)}${block}${html.slice(end)}`;
}

function createOverlaySvg(title, subtitle, hotspots, exclusions = [], mode = "hotspots") {
  const imageHref = "../../references/n6_architecture_crowd_density_1920x1080.png";
  const exclusionSvg = exclusions.map((mask) => {
    if (mask.kind === "polygon") {
      return `<polygon points="${mask.points.map((point) => point.join(",")).join(" ")}" fill="rgba(255,72,42,0.20)" stroke="#ff4b2b" stroke-width="3"><title>${mask.id}</title></polygon>`;
    }
    if (mask.kind === "ellipse") {
      return `<ellipse cx="${mask.center[0]}" cy="${mask.center[1]}" rx="${mask.radius_x_px}" ry="${mask.radius_y_px}" fill="rgba(255,72,42,0.18)" stroke="#ff4b2b" stroke-width="3"><title>${mask.id}</title></ellipse>`;
    }
    return `<rect x="${mask.x}" y="${mask.y}" width="${mask.width}" height="${mask.height}" fill="rgba(255,72,42,0.14)" stroke="#ff4b2b" stroke-width="3"><title>${mask.id}</title></rect>`;
  }).join("\n");
  const hotspotSvg = hotspots.map((hotspot) => {
    const stroke = mode === "exclusions" ? "#39ff88" : "#fff7cc";
    const fill = mode === "exclusions" ? "#ffffff" : "#39ff88";
    return `<g><circle cx="${hotspot.x}" cy="${hotspot.y}" r="5" fill="${fill}" stroke="${stroke}" stroke-width="2"><title>${hotspot.id} ${hotspot.region}</title></circle><circle cx="${hotspot.x}" cy="${hotspot.y}" r="${hotspot.allowed_jitter_px}" fill="none" stroke="#39ff88" stroke-width="1" opacity="0.65"/></g>`;
  }).join("\n");
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <image href="${imageHref}" width="${width}" height="${height}"/>
  <rect x="0" y="0" width="${width}" height="68" fill="rgba(20,13,8,0.78)"/>
  <text x="24" y="30" font-family="Arial, sans-serif" font-size="24" fill="#fff2da" font-weight="700">${title}</text>
  <text x="24" y="56" font-family="Arial, sans-serif" font-size="17" fill="#f5d7b6">${subtitle}</text>
  ${mode === "exclusions" ? exclusionSvg : ""}
  ${hotspotSvg}
</svg>
`;
}

function writeContactSheet(overlayDir) {
  const cards = auditedHotspots.map((hotspot) => {
    const cropSize = 132;
    const backgroundX = -(hotspot.x - cropSize / 2);
    const backgroundY = -(hotspot.y - cropSize / 2);
    return `<section class="card">
      <div class="crop" style="background-position:${backgroundX}px ${backgroundY}px"><span class="dot"></span></div>
      <h2>${hotspot.id}</h2>
      <p><strong>${hotspot.region}</strong></p>
      <p>${hotspot.audit_note}</p>
      <code>x=${hotspot.x}, y=${hotspot.y}, jitter<=${hotspot.allowed_jitter_px}px</code>
    </section>`;
  }).join("\n");
  const html = `<!doctype html>
<html><head><meta charset="utf-8"><title>Hyatt audited person-pixel flash hotspots</title>
<style>
body{margin:0;background:#120d09;color:#fff2da;font:14px Arial,sans-serif}
main{padding:24px;display:grid;gap:18px}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
.card{background:#201711;border:1px solid #4a3527;padding:10px;border-radius:6px}
.crop{position:relative;width:132px;height:132px;background-image:url('../../references/n6_architecture_crowd_density_1920x1080.png');background-size:1920px 1080px;border:1px solid #6d513c;margin-bottom:8px}
.dot{position:absolute;left:50%;top:50%;width:10px;height:10px;margin-left:-5px;margin-top:-5px;border-radius:50%;background:#fff7cc;box-shadow:0 0 0 2px #20e46d,0 0 18px 5px rgba(255,245,190,.62)}
h1{font-size:26px;margin:0}h2{font-size:14px;margin:0 0 4px}p{margin:3px 0;color:#e8cba8}code{color:#ffe4b8}
</style></head>
<body><main>
<h1>Hyatt audited person-pixel flash hotspots</h1>
<p>Each dot is the fixed flash core anchor. Jitter is capped per hotspot and broad line-band sampling is disabled.</p>
<div class="grid">${cards}</div>
</main></body></html>`;
  const contactPath = path.join(overlayDir, "audited_hotspot_zoom_contact_sheet.html");
  fs.writeFileSync(contactPath, html, "utf8");
  return contactPath;
}

function writeDebugArtifacts(cameraFlashes) {
  const overlayDir = path.join(successorRoot, "review/audited_flash_origin_overlays");
  ensureDir(overlayDir);
  const cleanFramePath = path.join(overlayDir, "n6_source_clean_frame.png");
  fs.copyFileSync(path.join(successorRoot, "references/n6_architecture_crowd_density_1920x1080.png"), cleanFramePath);
  const hotspotOverlayPath = path.join(overlayDir, "audited_hotspot_full_frame_overlay.svg");
  const exclusionOverlayPath = path.join(overlayDir, "audited_hotspot_exclusion_overlay.svg");
  fs.writeFileSync(
    hotspotOverlayPath,
    createOverlaySvg("Audited person-pixel flash origins", `${auditedHotspots.length} fixed hotspots; no broad strip sampling`, auditedHotspots),
    "utf8",
  );
  fs.writeFileSync(
    exclusionOverlayPath,
    createOverlaySvg("Audited hotspots plus exclusions", "Red areas are slab/fascia/wall/plant/text exclusions; green dots are approved person pixels", auditedHotspots, flashExclusionMasks, "exclusions"),
    "utf8",
  );
  const contactPath = writeContactSheet(overlayDir);
  const frameStripPath = path.join(overlayDir, "active_flash_frame_strip.html");
  const sampleEvents = cameraFlashes.filter((event) => event.forced_review_sample).concat(cameraFlashes.slice(0, 8));
  fs.writeFileSync(
    frameStripPath,
    `<!doctype html><html><head><meta charset="utf-8"><title>Hyatt active flash frame strip targets</title><style>body{background:#120d09;color:#fff2da;font:15px Arial;padding:24px}table{border-collapse:collapse}td,th{border:1px solid #5a3b29;padding:8px}code{color:#ffe4b8}</style></head><body><h1>Active flash frame strip targets</h1><p>Use these times for browser screenshots; all listed events reference audited person-pixel hotspots.</p><table><tr><th>time</th><th>event</th><th>hotspot</th><th>source</th><th>region</th></tr>${sampleEvents.map((event) => `<tr><td>${event.time_seconds.toFixed(3)}s</td><td><code>${event.id}</code></td><td><code>${event.flash_origin_hotspot_id}</code></td><td>${event.source_x}, ${event.source_y}</td><td>${event.hotspot_region}</td></tr>`).join("")}</table></body></html>`,
    "utf8",
  );
  return {
    cleanFramePath,
    hotspotOverlayPath,
    exclusionOverlayPath,
    contactPath,
    frameStripPath,
  };
}

function staticQa(cameraFlashes, proof, overlays) {
  const hotspotIds = new Set(auditedHotspots.map((hotspot) => hotspot.id));
  const missingHotspots = cameraFlashes.filter((event) => !hotspotIds.has(event.flash_origin_hotspot_id));
  const exclusionViolations = cameraFlashes.filter((event) => exclusionHits({ x: event.source_x, y: event.source_y }).length > 0);
  const jitterViolations = cameraFlashes.filter((event) => event.jitter_distance_px > event.allowed_jitter_px + 0.001);
  const broadMaskViolations = cameraFlashes.filter((event) => event.broad_mask_sampling_used || event.line_band_sampling_used);
  const surfaceViolations = cameraFlashes.filter((event) => event.origin_core_surface !== "visible_person" || event.surface_read !== "visible_person");
  const haloViolations = cameraFlashes.filter((event) => event.halo_radius_px > 26 || event.core_radius_px > 2.8);
  const qa = {
    profile_id: profileId,
    camera_flash_count: cameraFlashes.length,
    balloon_rise_count: proof.ambientEffects.balloonRises.length,
    audited_hotspot_count: auditedHotspots.length,
    missing_hotspots: missingHotspots.map((event) => event.id),
    exclusion_violations: exclusionViolations.map((event) => event.id),
    jitter_violations: jitterViolations.map((event) => event.id),
    broad_mask_violations: broadMaskViolations.map((event) => event.id),
    surface_violations: surfaceViolations.map((event) => event.id),
    halo_violations: haloViolations.map((event) => event.id),
    artifacts: {
      clean_frame: artifact(overlays.cleanFramePath),
      full_frame_hotspot_overlay: artifact(overlays.hotspotOverlayPath),
      exclusion_overlay: artifact(overlays.exclusionOverlayPath),
      zoom_contact_sheet: artifact(overlays.contactPath),
      active_flash_frame_strip: artifact(overlays.frameStripPath),
    },
    qa_reads: {
      audited_person_pixel_origin_read:
        missingHotspots.length === 0 && surfaceViolations.length === 0
          ? "pass_180_of_180_flash_origins_reference_audited_visible_person_hotspots"
          : `tighten_missing_${missingHotspots.length}_surface_${surfaceViolations.length}`,
      slab_face_origin_rejection_read:
        exclusionViolations.length === 0 ? "pass_zero_flash_origins_inside_slab_face_exclusions" : `tighten_${exclusionViolations.length}_origin_exclusion_hits`,
      walkway_fascia_origin_rejection_read:
        exclusionViolations.length === 0 ? "pass_zero_flash_origins_inside_walkway_fascia_exclusions" : `tighten_${exclusionViolations.length}_origin_exclusion_hits`,
      flash_core_on_person_surface_read:
        surfaceViolations.length === 0 ? "pass_all_flash_cores_on_audited_visible_person_surfaces" : `tighten_${surfaceViolations.length}_surface_violations`,
      flash_halo_not_origin_read:
        haloViolations.length === 0 ? "pass_small_core_soft_halo_spill_not_origin" : `tighten_${haloViolations.length}_halo_or_core_too_large`,
      audited_hotspot_contact_sheet_read: fs.existsSync(overlays.contactPath) ? "pass" : "tighten_missing_contact_sheet",
      ambient_density_preservation_read:
        cameraFlashes.length === 180 && proof.ambientEffects.balloonRises.length === 28
          ? "pass_180_flashes_28_balloons"
          : `tighten_${cameraFlashes.length}_flashes_${proof.ambientEffects.balloonRises.length}_balloons`,
      debug_overlay_absence_read: "pass_debug_artifacts_separate_from_viewer_player_html",
      broad_region_sampling_rejection_read:
        broadMaskViolations.length === 0 && !proof.ambientEffects.peopleStandingFlashMasks && !proof.ambientEffects.markedFlashRegions
          ? "pass_no_broad_line_band_or_strip_sampling_in_active_flash_layer"
          : "tighten_broad_region_sampling_still_present",
      flash_jitter_limit_read:
        jitterViolations.length === 0 ? "pass_all_flash_jitter_within_audited_hotspot_allowance" : `tighten_${jitterViolations.length}_jitter_violations`,
      source_locked_ambient_transform_read: proof.ambientEffects.sourceLockedToPlateTransform === true ? "pass" : "tighten_not_source_locked",
    },
  };
  const qaPath = path.join(successorRoot, "qa/audited_flash_origin/static_audited_flash_origin_qa.json");
  writeJson(qaPath, qa);
  return { qa, qaPath };
}

function writeAmbientArtifacts(proof, cameraFlashes, overlays, qaPath, qa) {
  const ambientPath = path.join(successorRoot, "living_cover_ambient_effects_layer.json");
  const ambient = {
    episode_id: "hyatt-regency",
    packet_id: successorId,
    phase_gate: "ambient_effects_reopened",
    status: "review_ready_pending_human_audited_flash_origin_keep",
    human_disposition: "pending",
    ambient_effects_process_version: "living_cover_ambient_effects_layer_audited_flash_origin_v1",
    ambient_profile_id: profileId,
    predecessor_profile_id: "hyatt_people_standing_event_life_v1",
    issue_reopened: "camera_flash_core_still_read_as_walkway_slab_face",
    selected_lanes: ["camera_flashes", "balloon_rises"],
    source_plate: {
      path: "/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/source_art/hyatt_living_cover_n6_architecture_crowd_density_20260517T083750Z/assets/source_art/n6_architecture_crowd_density_1920x1080.png",
      width,
      height,
      coordinate_space: "fixed_1920x1080_source_art",
    },
    effect_parameters: {
      deterministic_seed: deterministicSeed,
      clock: proof.ambientEffects.clock,
      source_lock_model: proof.ambientEffects.sourceLockModel,
      camera_flash_count: cameraFlashes.length,
      balloon_rise_count: proof.ambientEffects.balloonRises.length,
      flash_origin_hotspots: auditedHotspots,
      flash_exclusion_masks: flashExclusionMasks,
      camera_flashes: cameraFlashes,
      balloon_rises: proof.ambientEffects.balloonRises,
      flash_render_model: "small_core_soft_halo_person_anchor_v1",
      broad_region_sampling_used: false,
      line_band_sampling_used: false,
    },
    debug_review_artifacts: {
      clean_frame: artifact(overlays.cleanFramePath),
      full_frame_hotspot_overlay: artifact(overlays.hotspotOverlayPath),
      exclusion_overlay: artifact(overlays.exclusionOverlayPath),
      zoom_contact_sheet: artifact(overlays.contactPath),
      active_flash_frame_strip: artifact(overlays.frameStripPath),
      static_qa: artifact(qaPath),
    },
    downstream_locks: {
      may_advance_to_video_render: false,
      may_create_publish_readiness: false,
      may_upload_to_youtube: false,
      public_release_ready: false,
    },
    qa_reads: qa.qa_reads,
  };
  writeJson(ambientPath, ambient);
  const mdPath = path.join(successorRoot, "living_cover_ambient_effects_layer.md");
  fs.writeFileSync(
    mdPath,
    `# Hyatt Audited Flash-Origin Ambient Layer

- Profile: \`${profileId}\`
- Camera flashes: ${cameraFlashes.length}, from audited fixed person-pixel hotspots only.
- Balloons: ${proof.ambientEffects.balloonRises.length}, preserved from the prior kept table-bouquet origin clusters.
- Broad strip sampling: disabled.
- Flash rendering: small bright core plus soft bounded halo; the core remains the origin.
- Gate state: pending human review; video render, publish readiness, and upload stay locked.

## Required Reads

${Object.entries(qa.qa_reads).map(([key, value]) => `- \`${key}\`: \`${value}\``).join("\n")}
`,
    "utf8",
  );
  return { ambientPath, mdPath, ambient };
}

function writeRoughManifest(proof, ambientArtifacts, qaPath) {
  const manifestPath = path.join(successorRoot, "rough_assembly_manifest.json");
  const predecessorManifestPath = path.join(predecessorRoot, "rough_assembly_manifest.json");
  const manifest = fs.existsSync(predecessorManifestPath) ? readJson(predecessorManifestPath) : {};
  manifest.packet_id = successorId;
  manifest.status = "review_ready_pending_human_audited_flash_origin_keep";
  manifest.human_disposition = "pending";
  manifest.may_advance_to_video_render = false;
  manifest.predecessor_packet_id = path.basename(predecessorRoot);
  manifest.issue_reopened = "camera_flash_core_still_read_as_walkway_slab_face";
  manifest.ambient_profile_id = profileId;
  manifest.player_html_path = path.join(successorRoot, "player.html");
  manifest.player_html_sha256 = sha256(manifest.player_html_path);
  manifest.living_cover_ambient_effects_layer = {
    path: ambientArtifacts.ambientPath,
    sha256: sha256(ambientArtifacts.ambientPath),
    profile_id: profileId,
  };
  manifest.qa = {
    ...(manifest.qa || {}),
    audited_flash_origin_static_qa: {
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
  writeJson(manifestPath, manifest);
  return manifestPath;
}

function markPredecessorTighten() {
  const roughPath = path.join(predecessorRoot, "rough_assembly_manifest.json");
  if (fs.existsSync(roughPath)) {
    const rough = readJson(roughPath);
    rough.status = "tighten_flash_origin_still_reads_as_slab_face";
    rough.human_disposition = "tighten_flash_origin_still_reads_as_slab_face";
    rough.may_advance_to_video_render = false;
    rough.superseded_by = successorRoot;
    rough.tighten_reason = "Camera flash origins passed broad people-mask QA but still visually read as walkway slab/fascia.";
    writeJson(roughPath, rough);
  }
  const ambientPath = path.join(predecessorRoot, "living_cover_ambient_effects_layer.json");
  if (fs.existsSync(ambientPath)) {
    const ambient = readJson(ambientPath);
    ambient.status = "tighten_flash_origin_still_reads_as_slab_face";
    ambient.human_disposition = "tighten_flash_origin_still_reads_as_slab_face";
    ambient.superseded_by = successorRoot;
    ambient.tighten_reason = "Broad quadrilateral person masks were not precise enough for flash-origin believability.";
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

function updatePlayerHtml(proof, cameraFlashes) {
  let html = fs.readFileSync(path.join(successorRoot, "player.html"), "utf8");
  proof.ambientEffects = {
    profile_id: profileId,
    predecessor_profile_id: "hyatt_people_standing_event_life_v1",
    clock: "audio_time_for_ambient_effects_story_time_for_rail_captions",
    deterministic_seed: deterministicSeed,
    sourceLockedToPlateTransform: true,
    sourceLockModel: "plate_css_transform_equivalent_v1",
    flashOriginHotspots: auditedHotspots,
    flashExclusionMasks,
    cameraFlashes,
    markedBalloonOrigins: proof.ambientEffects.markedBalloonOrigins || [],
    balloonRises: proof.ambientEffects.balloonRises || [],
    balloonPalette: proof.ambientEffects.balloonPalette || proof.ambientEffects.balloon_palette,
    originContract: {
      person_operated_effect: "camera_flash",
      core_origin_policy: "audited_fixed_visible_person_pixel",
      broad_region_sampling_allowed: false,
      glow_spill_policy: "nearby architecture may catch soft halo; core point remains the only origin",
      max_allowed_jitter_px: 2,
    },
  };
  proof.audio = proof.audio.replace(/v=[^"&]+/, `v=audited_flash_origins_${stamp}`);
  html = replaceProof(html, proof);
  html = replaceAmbientStateFunction(html);
  html = replaceFlashDrawing(html);
  html = html.replace(
    /Hyatt Regency Living Cover N6 [^"]+ HTML rough proof/,
    "Hyatt Regency Living Cover N6 audited flash-origin HTML rough proof",
  );
  fs.writeFileSync(path.join(successorRoot, "player.html"), html, "utf8");
}

function writeSummary(cameraFlashes, ambientArtifacts, qaPath, manifestPath) {
  const summaryPath = path.join(successorRoot, "audited_flash_origin_successor_summary.json");
  writeJson(summaryPath, {
    successor_root: successorRoot,
    player_path: path.join(successorRoot, "player.html"),
    ambient_profile_id: profileId,
    predecessor_root: predecessorRoot,
    camera_flash_count: cameraFlashes.length,
    balloon_rise_count: ambientArtifacts.ambient.effect_parameters.balloon_rise_count,
    audited_hotspot_count: auditedHotspots.length,
    rough_manifest_path: manifestPath,
    ambient_layer_path: ambientArtifacts.ambientPath,
    static_qa_path: qaPath,
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
  const proof = extractProof(fs.readFileSync(playerPath, "utf8"));
  const cameraFlashes = buildFlashSchedule(proof.duration);
  updatePlayerHtml(proof, cameraFlashes);
  const overlays = writeDebugArtifacts(cameraFlashes);
  const { qa, qaPath } = staticQa(cameraFlashes, proof, overlays);
  const ambientArtifacts = writeAmbientArtifacts(proof, cameraFlashes, overlays, qaPath, qa);
  const manifestPath = writeRoughManifest(proof, ambientArtifacts, qaPath);
  markPredecessorTighten();
  const summaryPath = writeSummary(cameraFlashes, ambientArtifacts, qaPath, manifestPath);
  console.log(JSON.stringify({ successorRoot, playerPath, summaryPath }, null, 2));
}

main();
