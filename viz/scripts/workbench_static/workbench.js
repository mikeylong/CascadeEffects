import * as THREE from "three";
import { TrackballControls } from "/vendor/TrackballControls.js";

const DEFAULT_PRESET_ID = "default";

const sectionSpecs = {
  model: {
    title: "Model",
    help: "Rotate the selected source model itself. This rebakes the raw mesh preview and particle cloud orientation instead of only moving the camera.",
  },
  surface: {
    title: "Surface",
    help: "Adjust how dense, sharp, and legible the anchored shell reads before particles release.",
  },
  breakup: {
    title: "Breakup",
    help: "Control how quickly the shell releases into motion, how long the trail runs, and how chaotic the motion feels.",
  },
  emitter: {
    title: "Emitters",
    help: () => (
      emitterDirectionSpace() === "subject"
        ? "Model-backed emitters use model-space X/Y/Z. Direction stays attached to the selected mesh instead of the camera."
        : "Emitter direction uses camera-relative X/Y/Z."
    ),
  },
  volume: {
    title: "Volume",
    help: "Shape perceived depth and thickness so the point cloud reads as a dimensional subject instead of a flat layer.",
  },
  render: {
    title: "Render",
    help: "Tune the monochrome finish for preview and burn output without changing the underlying particle motion.",
  },
};

const effectFieldSpecs = {
  model: [
    { path: "model_source.transform.rotate_x_deg", label: "Rotate X", min: -180, max: 180, step: 1, displayScale: 1, continuous: true, help: "Rotate the selected model around its X axis before the particle effect is generated." },
    { path: "model_source.transform.rotate_y_deg", label: "Rotate Y", min: -180, max: 180, step: 1, displayScale: 1, continuous: true, help: "Rotate the selected model around its Y axis before the particle effect is generated." },
    { path: "model_source.transform.rotate_z_deg", label: "Rotate Z", min: -180, max: 180, step: 1, displayScale: 1, continuous: true, help: "Rotate the selected model around its Z axis before the particle effect is generated." },
  ],
  surface: [
    { path: "scene.surface.density", label: "Density", min: 0.2, max: 4.5, step: 0.01, displayScale: 10, help: "Overall point count. Higher values thicken the subject and reduce open space." },
    { path: "scene.surface.size", label: "Point Size", min: 0.1, max: 0.8, step: 0.01, displayScale: 100, help: "Base point radius before depth and glow are applied." },
    { path: "scene.surface.jitter", label: "Jitter", min: 0.0, max: 1.0, step: 0.01, displayScale: 100, help: "Small positional noise that breaks up overly uniform point placement." },
    { path: "scene.surface.luminance_floor", label: "Shadow Fill", min: 0.0, max: 1.0, step: 0.01, displayScale: 100, help: "Minimum brightness for darker areas so the silhouette stays readable." },
    { path: "scene.surface.edge_boost", label: "Edge Boost", min: 0.0, max: 1.0, step: 0.01, displayScale: 100, help: "Extra emphasis on silhouette edges and higher-contrast contours." },
    { path: "scene.surface.opacity", label: "Opacity", min: 0.1, max: 1.0, step: 0.01, displayScale: 100, help: "Global alpha for the anchored shell before emission points add energy." },
  ],
  breakup: [
    { path: "scene.breakup.amount", label: "Breakup", min: 0.0, max: 1.0, step: 0.01, displayScale: 100, help: "How much of the shell releases into motion." },
    { path: "scene.breakup.tail", label: "Tail", min: 0.0, max: 1.0, step: 0.01, displayScale: 100, help: "Trail length after particles leave the shell." },
    { path: "scene.breakup.drift_x", label: "Drift X", min: -1.0, max: 1.0, step: 0.01, displayScale: 100, help: "Horizontal drift bias for released particles." },
    { path: "scene.breakup.drift_y", label: "Drift Y", min: -1.0, max: 1.0, step: 0.01, displayScale: 100, help: "Vertical drift bias for released particles." },
    { path: "scene.breakup.turbulence", label: "Turbulence", min: 0.0, max: 1.0, step: 0.01, displayScale: 100, help: "Secondary noise that roughens the trail and breaks clean arcs." },
    { path: "scene.breakup.swirl", label: "Swirl", min: 0.0, max: 1.0, step: 0.01, displayScale: 100, help: "Rotational motion layered on top of drift and turbulence." },
    { path: "scene.breakup.retain", label: "Retention", min: 0.0, max: 1.0, step: 0.01, displayScale: 100, help: "How much of the shell stays anchored instead of peeling away." },
  ],
  emitter: [
    { path: "scene.emitter.direction_x", label: "Direction X", subjectLabel: "Model X", min: -1.0, max: 1.0, step: 0.01, displayScale: 100, help: "Emitter drift on the X axis." },
    { path: "scene.emitter.direction_y", label: "Direction Y", subjectLabel: "Model Y", min: -1.0, max: 1.0, step: 0.01, displayScale: 100, help: "Emitter drift on the Y axis." },
    { path: "scene.emitter.direction_z", label: "Direction Z", subjectLabel: "Model Z", min: -1.0, max: 1.0, step: 0.01, displayScale: 100, help: "Emitter drift on the Z axis." },
    { path: "scene.emitter.strength", label: "Strength", min: 0.0, max: 1.5, step: 0.01, displayScale: 100, help: "How strongly the emitter pushes released particles." },
    { path: "scene.emitter.rate", label: "Rate", min: 0.0, max: 1.5, step: 0.01, displayScale: 100, help: "How frequently emission builds across the loop." },
    { path: "scene.emitter.decay", label: "Decay", min: 0.0, max: 1.0, step: 0.01, displayScale: 100, help: "How quickly the emitted trail fades after release." },
  ],
  volume: [
    { path: "scene.volume.depth_scale", label: "Depth Scale", min: 0.0, max: 1.5, step: 0.01, displayScale: 100, help: "How much depth variation affects the particle cloud." },
    { path: "scene.volume.depth_curve", label: "Depth Curve", min: 0.25, max: 2.5, step: 0.01, displayScale: 10, help: "Bias for where depth compression or expansion is strongest." },
    { path: "scene.volume.thickness_jitter", label: "Thickness", min: 0.0, max: 1.0, step: 0.01, displayScale: 100, help: "Randomized thickness variation through the shell volume." },
  ],
  render: [
    { path: "scene.render.background", label: "Background", min: 0.0, max: 0.18, step: 0.01, displayScale: 100, help: "Background floor behind the point cloud." },
    { path: "scene.render.glow", label: "Glow", min: 0.0, max: 0.8, step: 0.01, displayScale: 100, help: "Bloom-like lift around bright particle clusters." },
    { path: "scene.render.contrast", label: "Contrast", min: 0.6, max: 1.6, step: 0.01, displayScale: 10, help: "Overall tonal separation between dim and bright particles." },
  ],
};

let project = null;
let currentTab = "model";
let currentViewportTab = "particle";
let previewProgress = 0.65;
let previewPlaybackState = "playing";
let effectPersistTimer = null;
let effectPersistInFlight = false;
let effectPersistQueued = false;
let effectPersistLastStart = 0;
let modelSourceResults = [];
let modelSourceResources = [];
let fetchedModelResults = new Map();
let modelSelectionState = { status: "idle", phases: [], targetKey: null };
let sketchfabAuth = {
  provider: "sketchfab",
  configured: false,
  connected: false,
  token_source: "none",
  display_name: "",
  username: "",
  profile_url: "",
  message: "",
};
let effectViewer = null;
let lastBurnManifest = null;
let tooltipIdCounter = 0;
let modelResourceModalReturnFocus = null;
window.__particleWorkbenchAppReady = false;
const EFFECT_PERSIST_INTERVAL_MS = 90;
const PREVIEW_AUTOPLAY_RESUME_MS = 700;
const MIN_PREVIEW_LOOP_SECONDS = 5.4;
const PARTICLE_MOTION_ANCHOR_SHELL = 0;
const PARTICLE_MOTION_ANCHOR_ATTACHMENT = 1;
const PARTICLE_MOTION_EMISSION_PLUME = 2;
const PARTICLE_MOTION_LEGACY_DYNAMIC = 3;
const EMISSION_TRAIL_STEPS = 6;
const EMISSION_TRAIL_MIN_RELEASE = 0.02;
const CAMERA_PITCH_LIMIT = (Math.PI * 0.5) - 1.0e-4;
const EXTERNAL_MODEL_RESOURCE_FALLBACKS = [
  {
    id: "cgtrader",
    label: "CGTrader",
    availability_note: "Large free-model catalog, but downloadability and reuse terms vary per listing.",
    license_note: "Free does not imply open-license. Verify the asset page before reuse.",
    search_url_template: "https://www.google.com/search?q=site%3Acgtrader.com%2Ffree-3d-models+{query}",
  },
  {
    id: "blend_swap",
    label: "Blend Swap",
    availability_note: "Useful for head basemeshes and sculpts, but downloads typically require login.",
    license_note: "Blend Swap assets vary by license. Check the listing before reuse.",
    search_url_template: "https://www.google.com/search?q=site%3Ablendswap.com+{query}",
  },
  {
    id: "free3d",
    label: "Free3D",
    availability_note: "Quick source for OBJ hits, though availability and download flows vary.",
    license_note: "Free3D licenses are per asset. Confirm commercial and attribution terms yourself.",
    search_url_template: "https://www.google.com/search?q=site%3Afree3d.com+{query}",
  },
  {
    id: "turbosquid",
    label: "TurboSquid",
    availability_note: "Broad catalog with some free assets, but the site has stronger gating and mixed formats.",
    license_note: "Free assets still carry per-item license terms. Review the listing before reuse.",
    search_url_template: "https://www.google.com/search?q=site%3Aturbosquid.com+{query}",
  },
];

const PLAY_ICON_SVG = `
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M8 6.82v10.36c0 .79.87 1.27 1.54.84l8.14-5.18a1 1 0 0 0 0-1.68L9.54 5.98A1 1 0 0 0 8 6.82Z"></path>
  </svg>
`;

const PAUSE_ICON_SVG = `
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M8 6a1 1 0 0 1 1 1v10a1 1 0 1 1-2 0V7a1 1 0 0 1 1-1Zm8 0a1 1 0 0 1 1 1v10a1 1 0 1 1-2 0V7a1 1 0 0 1 1-1Z"></path>
  </svg>
`;

function formatNumber(value) {
  return Number(value).toFixed(2);
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[char]));
}

function badgeClassToken(value) {
  return String(value || "").trim().replace(/[^a-z0-9]+/gi, "_").toLowerCase();
}

function nextAnimationFrame() {
  return new Promise((resolve) => requestAnimationFrame(() => resolve()));
}

function titleCase(value) {
  return String(value || "")
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function activePresetId() {
  return String(project?.active_preset_id || DEFAULT_PRESET_ID).trim() || DEFAULT_PRESET_ID;
}

function activePresetLabel() {
  const builtin = project?.available_presets?.[activePresetId()];
  if (builtin?.label) {
    return builtin.label;
  }
  const savedPreset = (project?.saved_presets || []).find((preset) => preset.id === activePresetId());
  if (savedPreset?.label) {
    return savedPreset.label;
  }
  return "Default";
}

function displayIntegerForSpec(spec, value) {
  return Math.round(Number(value || 0) * Number(spec.displayScale || 1));
}

function displayIntegerBounds(spec) {
  return {
    min: Math.round(Number(spec.min) * Number(spec.displayScale || 1)),
    max: Math.round(Number(spec.max) * Number(spec.displayScale || 1)),
  };
}

function rawValueFromDisplayInteger(spec, value) {
  const rounded = Math.round(Number(value || 0));
  if (spec.continuous === true) {
    return rounded / Number(spec.displayScale || 1);
  }
  const bounds = displayIntegerBounds(spec);
  return clamp(rounded, bounds.min, bounds.max) / Number(spec.displayScale || 1);
}

function formatSnapshotTimestamp(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

function tooltipText(value) {
  return typeof value === "function" ? value() : String(value || "").trim();
}

function easeInOut(progress) {
  const t = clamp(Number(progress) || 0, 0, 1);
  return t * t * (3 - (2 * t));
}

function wrap01(value) {
  const wrapped = Number(value) % 1;
  return wrapped < 0 ? wrapped + 1 : wrapped;
}

function plumeEmissionEnvelope(progress, pointPhase, drift, rate) {
  const cycles = 1 + (clamp(Number(rate) || 0, 0, 1.5) * 2.4);
  const phaseOffset = wrap01((Number(pointPhase) || 0) / (Math.PI * 2));
  const driftOffset = (Number(drift) || 0) * 0.37;
  const cycleProgress = wrap01((Number(progress) || 0) * cycles + phaseOffset + driftOffset);
  const outward = easeInOut(cycleProgress);
  return clamp((outward * 0.92) + 0.08, 0, 1);
}

function vectorAdd(a, b) {
  return [
    Number(a?.[0] || 0) + Number(b?.[0] || 0),
    Number(a?.[1] || 0) + Number(b?.[1] || 0),
    Number(a?.[2] || 0) + Number(b?.[2] || 0),
  ];
}

function vectorSub(a, b) {
  return [
    Number(a?.[0] || 0) - Number(b?.[0] || 0),
    Number(a?.[1] || 0) - Number(b?.[1] || 0),
    Number(a?.[2] || 0) - Number(b?.[2] || 0),
  ];
}

function vectorScale(vector, scalar) {
  return [
    Number(vector?.[0] || 0) * scalar,
    Number(vector?.[1] || 0) * scalar,
    Number(vector?.[2] || 0) * scalar,
  ];
}

function vectorDot(a, b) {
  return (
    (Number(a?.[0] || 0) * Number(b?.[0] || 0)) +
    (Number(a?.[1] || 0) * Number(b?.[1] || 0)) +
    (Number(a?.[2] || 0) * Number(b?.[2] || 0))
  );
}

function vectorCross(a, b) {
  return [
    (Number(a?.[1] || 0) * Number(b?.[2] || 0)) - (Number(a?.[2] || 0) * Number(b?.[1] || 0)),
    (Number(a?.[2] || 0) * Number(b?.[0] || 0)) - (Number(a?.[0] || 0) * Number(b?.[2] || 0)),
    (Number(a?.[0] || 0) * Number(b?.[1] || 0)) - (Number(a?.[1] || 0) * Number(b?.[0] || 0)),
  ];
}

function vectorLength(vector) {
  return Math.sqrt(
    (Number(vector?.[0] || 0) ** 2) +
    (Number(vector?.[1] || 0) ** 2) +
    (Number(vector?.[2] || 0) ** 2),
  );
}

function vectorNormalize(vector, fallback = [0, 0, 0]) {
  const length = vectorLength(vector);
  if (length <= 1.0e-8) {
    return [...fallback];
  }
  return [
    Number(vector?.[0] || 0) / length,
    Number(vector?.[1] || 0) / length,
    Number(vector?.[2] || 0) / length,
  ];
}

function vectorRotateAroundAxis(vector, axis, angle) {
  if (Math.abs(Number(angle) || 0) <= 1.0e-9) {
    return [...vector];
  }
  const normalizedAxis = vectorNormalize(axis, [0, 0, 1]);
  const cosine = Math.cos(angle);
  const sine = Math.sin(angle);
  const term1 = vectorScale(vector, cosine);
  const term2 = vectorScale(vectorCross(normalizedAxis, vector), sine);
  const term3 = vectorScale(normalizedAxis, vectorDot(normalizedAxis, vector) * (1 - cosine));
  return vectorAdd(vectorAdd(term1, term2), term3);
}

function cameraReferenceUp(forward) {
  const referenceUp = [0, 1, 0];
  if (Math.abs(vectorDot(forward, referenceUp)) > 0.98) {
    return [0, 0, 1];
  }
  return referenceUp;
}

function signedAngleAroundAxis(fromVector, toVector, axis) {
  const fromUnit = vectorNormalize(fromVector, [0, 1, 0]);
  const toUnit = vectorNormalize(toVector, [0, 1, 0]);
  const axisUnit = vectorNormalize(axis, [0, 0, -1]);
  return Math.atan2(
    vectorDot(vectorCross(fromUnit, toUnit), axisUnit),
    clamp(vectorDot(fromUnit, toUnit), -1, 1),
  );
}

function cameraVectors(cameraState) {
  const target = [
    Number(cameraState?.target_x || 0),
    Number(cameraState?.target_y || 0),
    Number(cameraState?.target_z || 0),
  ];
  const yaw = Number(cameraState?.yaw || 0);
  const pitch = clamp(Number(cameraState?.pitch || 0), -CAMERA_PITCH_LIMIT, CAMERA_PITCH_LIMIT);
  const distance = Math.max(0.2, Number(cameraState?.distance || 3.0));
  const roll = Number(cameraState?.roll || 0);
  const eye = [
    target[0] + (distance * Math.cos(pitch) * Math.sin(yaw)),
    target[1] + (distance * Math.sin(pitch)),
    target[2] + (distance * Math.cos(pitch) * Math.cos(yaw)),
  ];
  const forward = vectorNormalize(vectorSub(target, eye), [0, 0, -1]);
  const referenceUp = cameraReferenceUp(forward);
  const right = vectorNormalize(vectorCross(forward, referenceUp), [1, 0, 0]);
  const up = vectorNormalize(vectorCross(right, forward), [0, 1, 0]);
  if (Math.abs(roll) <= 1.0e-9) {
    return { target, eye, forward, right, up };
  }
  return {
    target,
    eye,
    forward,
    right: vectorRotateAroundAxis(right, forward, roll),
    up: vectorRotateAroundAxis(up, forward, roll),
  };
}

function projectPointToScreen(world, cameraState, width, height) {
  const camera = cameraVectors(cameraState || {});
  const relative = vectorSub(world, camera.eye);
  const cameraX = vectorDot(relative, camera.right);
  const cameraY = vectorDot(relative, camera.up);
  const cameraZ = vectorDot(relative, camera.forward);
  if (cameraZ <= 1.0e-3) {
    return null;
  }
  const fov = Math.max(1, Number(cameraState?.fov || 34));
  const focal = (height * 0.5) / Math.tan(THREE.MathUtils.degToRad(fov * 0.5));
  return [
    (width * 0.5) + ((cameraX * focal) / cameraZ),
    (height * 0.5) - ((cameraY * focal) / cameraZ),
    cameraZ,
  ];
}

function particleMotionContext(bounds, cameraState, breakup, emitter) {
  if (!bounds?.center || !Number.isFinite(Number(bounds?.radius))) {
    return {
      center: [0, 0, 0],
      radius: 1,
      directionSpace: "camera",
      forward: [0, 0, 1],
      right: [1, 0, 0],
      up: [0, 1, 0],
      driftDirection: [0, 0, 0],
      lateralDirection: [1, 0, 0],
      driftMagnitude: 0,
    };
  }
  const directionSpace = String(emitter?.direction_space || "camera").trim().toLowerCase() === "subject"
    ? "subject"
    : "camera";
  const camera = cameraVectors(cameraState || {});
  const basis = directionSpace === "subject"
    ? {
      right: [1, 0, 0],
      up: [0, 1, 0],
      forward: [0, 0, 1],
    }
    : camera;
  const directionX = Number(emitter?.direction_x || 0);
  const directionY = Number(emitter?.direction_y || 0);
  const directionZ = Number(emitter?.direction_z || 0);
  const strength = clamp(Number(emitter?.strength || 0), 0, 1.5);
  const driftVector = vectorAdd(
    vectorAdd(vectorScale(basis.right, directionX), vectorScale(basis.up, directionY)),
    vectorScale(basis.forward, directionZ),
  );
  const driftMagnitude = clamp(vectorLength(driftVector) * strength, 0, 1.5);
  let driftDirection = [0, 0, 0];
  let lateralDirection = basis.right;
  if (driftMagnitude >= 0.05) {
    driftDirection = vectorNormalize(driftVector, [0, 0, 0]);
    const lateralCandidate = vectorAdd(
      vectorScale(basis.right, -directionY),
      vectorScale(basis.up, directionX),
    );
    lateralDirection = vectorNormalize(
      lateralCandidate,
      basis.right,
    );
  }
  return {
    center: [
      Number(bounds.center.x || 0),
      Number(bounds.center.y || 0),
      Number(bounds.center.z || 0),
    ],
    radius: Math.max(0.001, Number(bounds.radius || 1)),
    directionSpace,
    forward: basis.forward,
    right: basis.right,
    up: basis.up,
    driftDirection,
    lateralDirection,
    driftMagnitude,
  };
}

function particleDirectionalReleaseBias(point, idx, motionContext) {
  if (!motionContext || Number(motionContext.driftMagnitude || 0) < 0.05) {
    return 1.0;
  }
  const projected = vectorDot(
    [
      Number(point[idx.x] || 0) - Number(motionContext.center?.[0] || 0),
      Number(point[idx.y] || 0) - Number(motionContext.center?.[1] || 0),
      Number(point[idx.z] || 0) - Number(motionContext.center?.[2] || 0),
    ],
    motionContext.driftDirection,
  ) / Math.max(Number(motionContext.radius || 1), 1.0e-3);
  const normalized = clamp(projected, -1.25, 1.25);
  const biasStrength = clamp(Number(motionContext.driftMagnitude || 0) * 0.72, 0, 0.92);
  return clamp(1.0 + (normalized * biasStrength), 0.24, 1.78);
}

function pointMotionMode(point, idx) {
  if (idx.motionMode < 0) {
    return PARTICLE_MOTION_LEGACY_DYNAMIC;
  }
  const value = Number(point[idx.motionMode]);
  return Number.isFinite(value) ? value : PARTICLE_MOTION_LEGACY_DYNAMIC;
}

function previewWarningText(scene) {
  const breakup = scene?.breakup || {};
  const amount = Number(breakup.amount || 0);
  const emitter = scene?.emitter || {};
  const motionLevel = Math.max(
    Math.abs(Number(emitter.direction_x || 0)),
    Math.abs(Number(emitter.direction_y || 0)),
    Math.abs(Number(emitter.direction_z || 0)),
    Number(emitter.strength || 0),
    Number(breakup.tail || 0),
    Number(breakup.turbulence || 0),
    Number(breakup.swirl || 0),
  );
  if (amount < 0.03 && motionLevel >= 0.08) {
    return "No emission: raise Breakup to release particles.";
  }
  return "";
}

function shotDurationSeconds() {
  return Math.max(MIN_PREVIEW_LOOP_SECONDS, Number(project?.scene?.shot?.duration_seconds || 3.0));
}

function getValue(path) {
  return path.split(".").reduce((current, part) => current?.[part], project);
}

function setValue(path, value) {
  const parts = path.split(".");
  let current = project;
  for (let index = 0; index < parts.length - 1; index += 1) {
    current = current[parts[index]];
  }
  current[parts[parts.length - 1]] = value;
}

function selectedModelActive() {
  return project?.scene?.volume_backend === "model_source_spike" && project?.model_source?.status === "selected";
}

function emitterDirectionSpace() {
  return String(project?.scene?.emitter?.direction_space || "camera").trim().toLowerCase() === "subject"
    ? "subject"
    : "camera";
}

function approvalApproved() {
  return project?.approval?.status === "approved";
}

function effectReady() {
  return selectedModelActive();
}

function burnReady() {
  return effectReady() && approvalApproved();
}

function setModelSourceLog(text) {
  document.getElementById("model-source-log").textContent = text;
}

function selectionInFlight() {
  return ["fetching", "decoding", "normalizing", "effect_reload"].includes(String(modelSelectionState?.status || ""));
}

function setModelSelectionState(status, phases = []) {
  modelSelectionState = {
    status: String(status || "idle"),
    phases: Array.isArray(phases) ? phases.map((phase) => ({ ...phase })) : [],
    targetKey: modelSelectionState?.targetKey || null,
  };
  renderModelSourcePanel();
}

function setModelSelectionTarget(targetKey) {
  modelSelectionState = {
    ...modelSelectionState,
    targetKey: targetKey || null,
  };
  renderModelSourcePanel();
}

function logSelectionPhases(selectionStatus) {
  const phases = Array.isArray(selectionStatus?.phases) ? selectionStatus.phases : [];
  if (!phases.length) {
    return;
  }
  const summary = phases
    .map((phase) => `${phase.label}: ${phase.status}${phase.detail ? ` (${phase.detail})` : ""}`)
    .join(" | ");
  setModelSourceLog(summary);
}

function modelCandidateUsable(candidate) {
  if (!candidate) return false;
  if (candidate.provider_capability === "search_only") return false;
  if (candidate.status === "fetched" && candidate.selection_eligible === false) return false;
  return true;
}

function modelCandidateKey(candidate) {
  if (!candidate) return "";
  return `${candidate.provider || "unknown"}:${candidate.remote_id || candidate.title || "candidate"}`;
}

function activeModelSourceQuery() {
  return (
    document.getElementById("model-source-query")?.value.trim()
    || modelSourceResults[0]?.query
    || project?.model_source?.query
    || ""
  );
}

function fallbackModelSourceResources(query) {
  const resolvedQuery = String(query || "").trim() || "3d model";
  const encodedQuery = encodeURIComponent(resolvedQuery).replace(/%20/g, "+");
  return EXTERNAL_MODEL_RESOURCE_FALLBACKS.map((resource) => ({
    ...resource,
    query: resolvedQuery,
    search_url: resource.search_url_template.replace("{query}", encodedQuery),
  }));
}

function sketchfabConnected() {
  return Boolean(sketchfabAuth?.configured && sketchfabAuth?.connected);
}

function sketchfabTokenSource() {
  return String(sketchfabAuth?.token_source || "none").trim() || "none";
}

function sketchfabEnvManaged() {
  return sketchfabTokenSource() === "env";
}

function candidateNeedsSketchfabAuth(candidate) {
  return Boolean(
    candidate
    && candidate.provider === "sketchfab"
    && candidate.requires_auth !== false
    && !sketchfabConnected()
    && !candidate.raw_asset_path
  );
}

function modelAttributionText(candidate) {
  const explicit = String(candidate?.attribution_text || "").trim();
  if (explicit) {
    return explicit;
  }
  const fallback = [];
  if (candidate?.author_name) {
    fallback.push(`By ${candidate.author_name}`);
  }
  if (candidate?.license_summary || candidate?.license_class) {
    fallback.push(candidate.license_summary || titleCase(candidate.license_class || ""));
  }
  return fallback.join(" · ");
}

function modelSourceLinksMarkup(candidate) {
  const links = [];
  if (candidate?.remote_url) {
    links.push(`<a href="${escapeHtml(candidate.remote_url)}" target="_blank" rel="noreferrer">Open Model</a>`);
  }
  if (candidate?.author_url) {
    links.push(`<a href="${escapeHtml(candidate.author_url)}" target="_blank" rel="noreferrer">Author</a>`);
  }
  if (candidate?.license_url) {
    links.push(`<a href="${escapeHtml(candidate.license_url)}" target="_blank" rel="noreferrer">License</a>`);
  }
  return links.join("");
}

function modelSourceProviderLabel(candidate) {
  return String(candidate?.provider_label || titleCase(candidate?.provider || "model")).trim() || "Model";
}

function modelSourceThumbnailFallbackMarkup(candidate) {
  return `
    <div class="model-source-thumbnail-fallback">
      <span class="model-source-thumbnail-provider">${escapeHtml(modelSourceProviderLabel(candidate))}</span>
      <span class="model-source-thumbnail-label">No preview</span>
    </div>
  `;
}

function modelSourceThumbnailMarkup(candidate, variant = "result") {
  const previewUrl = String(candidate?.preview_url || "").trim();
  const sizeClass = variant === "selected" ? "selected" : "result";
  const title = String(candidate?.title || candidate?.remote_id || modelSourceProviderLabel(candidate)).trim();
  if (!previewUrl) {
    return `
      <div class="model-source-thumbnail ${sizeClass} has-fallback" data-model-thumbnail-frame>
        ${modelSourceThumbnailFallbackMarkup(candidate)}
      </div>
    `;
  }
  return `
    <div class="model-source-thumbnail ${sizeClass}" data-model-thumbnail-frame>
      <img
        class="model-source-thumbnail-image"
        src="${escapeHtml(previewUrl)}"
        alt="${escapeHtml(`${title} preview`)}"
        loading="lazy"
        decoding="async"
        data-model-thumbnail
      >
      <div class="model-source-thumbnail-fallback" hidden>
        <span class="model-source-thumbnail-provider">${escapeHtml(modelSourceProviderLabel(candidate))}</span>
        <span class="model-source-thumbnail-label">No preview</span>
      </div>
    </div>
  `;
}

function setModelSourceThumbnailFallback(frame) {
  if (!frame) {
    return;
  }
  frame.classList.add("has-fallback");
  const image = frame.querySelector(".model-source-thumbnail-image");
  const fallback = frame.querySelector(".model-source-thumbnail-fallback");
  if (image) {
    image.hidden = true;
  }
  if (fallback) {
    fallback.hidden = false;
  }
}

function clearModelSourceThumbnailFallback(frame) {
  if (!frame) {
    return;
  }
  frame.classList.remove("has-fallback");
  const image = frame.querySelector(".model-source-thumbnail-image");
  const fallback = frame.querySelector(".model-source-thumbnail-fallback");
  if (image) {
    image.hidden = false;
  }
  if (fallback) {
    fallback.hidden = true;
  }
}

function wireModelSourceThumbnails(scope) {
  if (!scope) {
    return;
  }
  for (const image of scope.querySelectorAll("[data-model-thumbnail]")) {
    if (image.dataset.thumbnailWired === "true") {
      continue;
    }
    image.dataset.thumbnailWired = "true";
    const frame = image.closest("[data-model-thumbnail-frame]");
    image.addEventListener("load", () => clearModelSourceThumbnailFallback(frame));
    image.addEventListener("error", () => setModelSourceThumbnailFallback(frame));
    if (image.complete) {
      if (image.naturalWidth > 0) {
        clearModelSourceThumbnailFallback(frame);
      } else {
        setModelSourceThumbnailFallback(frame);
      }
    }
  }
}

function modelSelectionStatusForCandidate(candidate, fetched, selected) {
  const targetKey = modelSelectionState?.targetKey || "";
  const candidateKey = modelCandidateKey(candidate);
  const fetchedKey = modelCandidateKey(fetched);
  const activeKey = fetchedKey || candidateKey;
  const isSelected = Boolean(
    selectedModelActive()
    && selected?.remote_id
    && selected.remote_id === candidate.remote_id
    && selected.provider === candidate.provider
  );
  if (isSelected) {
    return { text: "Selected for the effect stage.", tone: "success" };
  }
  if (String(fetched?.selection_error || "").trim()) {
    return { text: fetched.selection_error, tone: "error" };
  }
  if (selectionInFlight() && targetKey && targetKey === activeKey) {
    const activePhase = (modelSelectionState?.phases || []).find((phase) => phase.status === "in_progress");
    const detail = String(activePhase?.detail || "").trim();
    return {
      text: detail || (modelSelectionState.status === "fetching" ? "Fetching…" : "Selecting…"),
      tone: "warning",
    };
  }
  if (candidateNeedsSketchfabAuth(candidate) && !fetched) {
    return { text: "Connect Sketchfab with a personal token to fetch this downloadable open-license model.", tone: "warning" };
  }
  if (fetched && modelCandidateUsable(fetched)) {
    return { text: "Fetched and ready to use.", tone: "success" };
  }
  if (candidate.provider_capability === "search_only") {
    return { text: "Research reference only. This provider is not selectable in the local runtime.", tone: "warning" };
  }
  return {
    text: String(candidate.eligibility_note || "").trim() || "Fetch this candidate to inspect and select it.",
    tone: "default",
  };
}

function setPreviewLog(text) {
  document.getElementById("preview-log").textContent = text;
}

function setBurnLog(text) {
  document.getElementById("burn-log").textContent = text;
}

function setAutosaveStatus(text, tone = "") {
  const node = document.getElementById("effect-autosave-status");
  if (!node) return;
  node.textContent = text;
  node.dataset.tone = tone;
}

function particleViewportActive() {
  return currentViewportTab === "particle";
}

function previewIsPlaying() {
  return previewPlaybackState === "playing";
}

function syncPlaybackButton() {
  const button = document.getElementById("preview-play-toggle");
  if (!button) return;
  const playing = previewIsPlaying();
  button.innerHTML = playing ? PAUSE_ICON_SVG : PLAY_ICON_SVG;
  button.classList.toggle("active", playing && !button.disabled);
  button.setAttribute("aria-pressed", playing ? "true" : "false");
  button.setAttribute("aria-label", playing ? "Pause playback" : "Play playback");
  button.setAttribute("title", playing ? "Pause playback" : "Play playback");
}

function syncViewportTabs() {
  for (const button of document.querySelectorAll("[data-viewport-tab]")) {
    const active = button.dataset.viewportTab === currentViewportTab;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", active ? "true" : "false");
  }
}

function syncViewportControls() {
  const particleViewEnabled = effectReady() && particleViewportActive();
  const progressInput = document.getElementById("preview-progress");
  const playButton = document.getElementById("preview-play-toggle");
  const snapshotButton = document.getElementById("snapshot-button");
  const approveButton = document.getElementById("approve-button");
  if (progressInput) {
    progressInput.disabled = !particleViewEnabled;
  }
  if (playButton) {
    playButton.disabled = !particleViewEnabled;
  }
  if (snapshotButton) {
    snapshotButton.disabled = !particleViewEnabled;
  }
  if (approveButton) {
    approveButton.disabled = !particleViewEnabled;
  }
  syncPlaybackButton();
}

function setPreviewPlaybackState(state) {
  previewPlaybackState = state === "paused" ? "paused" : "playing";
  if (effectViewer) {
    effectViewer.autoplayResumeAt = previewIsPlaying() ? performance.now() : Infinity;
  }
  syncPlaybackButton();
  effectViewer?.requestRender();
}

function togglePreviewPlayback() {
  setPreviewPlaybackState(previewIsPlaying() ? "paused" : "playing");
}

function setViewportTab(tabId) {
  if (!["particle", "model"].includes(String(tabId || ""))) return;
  currentViewportTab = tabId;
  if (!particleViewportActive()) {
    effectViewer?.endScrub();
  } else if (currentTab === "effect" && previewIsPlaying()) {
    if (effectViewer) {
      effectViewer.autoplayResumeAt = performance.now();
    }
  }
  effectViewer?.setViewportMode(currentViewportTab);
  syncViewportTabs();
  syncViewportControls();
  syncPreviewWarning();
  effectViewer?.requestRender();
}

async function withViewportTab(tabId, callback) {
  const previousViewportTab = currentViewportTab;
  if (previousViewportTab !== tabId) {
    setViewportTab(tabId);
    await nextAnimationFrame();
    await nextAnimationFrame();
  }
  try {
    return await callback();
  } finally {
    if (previousViewportTab !== tabId) {
      setViewportTab(previousViewportTab);
    }
  }
}

async function fetchJson(url) {
  const response = await fetch(url);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Request failed.");
  }
  return payload;
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || "Request failed.");
  }
  return payload;
}

async function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function projectRootFromManifest(manifest) {
  const projectPath = String(manifest?.project_path || "");
  const lastSlash = projectPath.lastIndexOf("/");
  return lastSlash > 0 ? projectPath.slice(0, lastSlash) : "";
}

function projectRootFromArtifactPath(absolutePath) {
  const target = String(absolutePath || "");
  const exportsIndex = target.lastIndexOf("/exports/");
  return exportsIndex > 0 ? target.slice(0, exportsIndex) : "";
}

function relativeProjectPath(manifest, absolutePath) {
  const root = projectRootFromManifest(manifest) || projectRootFromArtifactPath(absolutePath);
  const target = String(absolutePath || "");
  if (root && target.startsWith(`${root}/`)) {
    return target.slice(root.length + 1);
  }
  return "";
}

function previewAspectRatioValue() {
  const width = Number(project?.motion_contract?.width || 16);
  const height = Number(project?.motion_contract?.height || 9);
  if (width > 0 && height > 0) {
    return `${width} / ${height}`;
  }
  return "16 / 9";
}

function syncMediaViewportRatio() {
  document.documentElement.style.setProperty("--media-preview-aspect-ratio", previewAspectRatioValue());
}

function latestBurnArtifacts() {
  if (!approvalApproved()) {
    return null;
  }
  const approval = project?.approval || {};
  if (lastBurnManifest) {
    const approvalSnapshotId = String(approval.snapshot_id || "").trim();
    const manifestSnapshotId = String(lastBurnManifest?.snapshot_id || "").trim();
    if (approvalSnapshotId && manifestSnapshotId && manifestSnapshotId !== approvalSnapshotId) {
      return null;
    }
    return {
      project_path: lastBurnManifest.project_path || "",
      output_path: lastBurnManifest.output_path || approval.output_path || "",
      master_output_path: lastBurnManifest.master_output_path || approval.master_output_path || "",
      manifest_path: lastBurnManifest.manifest_path || approval.manifest_path || "",
      poster_path: lastBurnManifest.poster_path || approval.poster_path || "",
      still_path: lastBurnManifest.still_path || approval.still_path || "",
    };
  }
  if (approval.output_path || approval.master_output_path || approval.manifest_path || approval.poster_path || approval.still_path) {
    return {
      project_path: "",
      output_path: approval.output_path || "",
      master_output_path: approval.master_output_path || "",
      manifest_path: approval.manifest_path || "",
      poster_path: approval.poster_path || "",
      still_path: approval.still_path || "",
    };
  }
  return null;
}

class EffectViewer {
  constructor(host) {
    this.host = host;
    this.viewportMode = "particle";
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true, powerPreference: "high-performance" });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.domElement.style.width = "100%";
    this.renderer.domElement.style.height = "100%";
    this.host.replaceChildren(this.renderer.domElement);

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(34, 1, 0.01, 100);
    this.rawModelTextureLoader = new THREE.TextureLoader();
    this.controls = new TrackballControls(this.camera, this.renderer.domElement);
    this.controls.staticMoving = true;
    this.controls.rotateSpeed = 2.4;
    this.controls.zoomSpeed = 0.9;
    this.controls.panSpeed = 0.9;
    this.controls.mouseButtons.LEFT = THREE.MOUSE.ROTATE;
    this.controls.mouseButtons.RIGHT = THREE.MOUSE.PAN;
    this.renderer.domElement.addEventListener("dblclick", () => this.resetCameraToFit());

    this.shellGeometry = new THREE.BufferGeometry();
    this.rawModelGeometry = new THREE.BufferGeometry();
    this.shellMaterial = new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      depthTest: true,
      blending: THREE.NormalBlending,
      uniforms: {
        focalPx: { value: 120 },
        minPointSizePx: { value: 0.68 },
      },
      vertexShader: `
        attribute float size;
        attribute float brightness;
        attribute float alphaFactor;
        uniform float focalPx;
        uniform float minPointSizePx;
        varying float vBrightness;
        varying float vAlpha;
        void main() {
          vBrightness = brightness;
          vAlpha = alphaFactor;
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          gl_PointSize = max((size * (focalPx / max(-mvPosition.z, 0.0001))) * 2.0, minPointSizePx);
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        varying float vBrightness;
        varying float vAlpha;
        void main() {
          vec2 centered = gl_PointCoord - vec2(0.5);
          float dist = dot(centered, centered);
          if (dist > 0.25) discard;
          float edge = smoothstep(0.25, 0.02, dist);
          float core = smoothstep(0.18, 0.0, dist);
          vec3 color = pow(vec3(vBrightness), vec3(2.2));
          gl_FragColor = vec4(color, mix(edge, core, 0.82) * vAlpha);
        }
      `,
    });
    this.rawModelMaterial = this.shellMaterial.clone();
    this.emitterGeometry = new THREE.BufferGeometry();
    this.emitterMaterial = this.shellMaterial.clone();
    this.emitterMaterial.blending = THREE.AdditiveBlending;
    this.trailGeometry = new THREE.BufferGeometry();
    this.trailMaterial = this.shellMaterial.clone();
    this.trailMaterial.blending = THREE.AdditiveBlending;
    this.rawModelMeshGroup = new THREE.Group();
    this.rawModelLights = new THREE.Group();
    const rawModelAmbientLight = new THREE.AmbientLight(0xffffff, 1.25);
    const rawModelKeyLight = new THREE.DirectionalLight(0xffffff, 1.45);
    rawModelKeyLight.position.set(2.6, 3.1, 2.8);
    const rawModelFillLight = new THREE.DirectionalLight(0xa8c4ff, 0.38);
    rawModelFillLight.position.set(-2.8, 1.4, -1.8);
    const rawModelRimLight = new THREE.DirectionalLight(0xfff0dc, 0.24);
    rawModelRimLight.position.set(0.4, -2.6, 2.2);
    this.rawModelLights.add(rawModelAmbientLight);
    this.rawModelLights.add(rawModelKeyLight);
    this.rawModelLights.add(rawModelFillLight);
    this.rawModelLights.add(rawModelRimLight);
    this.rawModelPointsObject = new THREE.Points(this.rawModelGeometry, this.rawModelMaterial);
    this.rawModelPointsObject.frustumCulled = false;
    this.shellPoints = new THREE.Points(this.shellGeometry, this.shellMaterial);
    this.shellPoints.frustumCulled = false;
    this.emitterPointsObject = new THREE.Points(this.emitterGeometry, this.emitterMaterial);
    this.emitterPointsObject.frustumCulled = false;
    this.trailPointsObject = new THREE.Points(this.trailGeometry, this.trailMaterial);
    this.trailPointsObject.frustumCulled = false;
    this.scene.add(this.rawModelLights);
    this.scene.add(this.rawModelMeshGroup);
    this.scene.add(this.rawModelPointsObject);
    this.scene.add(this.shellPoints);
    this.scene.add(this.emitterPointsObject);
    this.scene.add(this.trailPointsObject);

    this.basePoints = [];
    this.rawModelMesh = { meshes: [], visibility_points: [] };
    this.rawModelMeshVisibilityPoints = [];
    this.rawModelPoints = [];
    this.anchoredPoints = [];
    this.emitterPoints = [];
    this.pointIndex = {};
    this.rawModelIndex = {};
    this.fitCamera = null;
    this.resetCamera = null;
    this.rawModelFitCamera = null;
    this.rawModelResetCamera = null;
    this.particleCameraState = null;
    this.rawModelCameraState = null;
    this.currentBounds = null;
    this.currentScene = null;
    this.currentAppearance = { min_radius_px: 0.34, background: 0.03 };
    this.scrubbing = false;
    this.captureDepth = 0;
    this.autoplayResumeAt = 0;
    this.lastFrameMs = 0;
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(this.host);
    this.controls.handleResize();
    this.controls.addEventListener("change", () => this.requestRender());
    this.controls.addEventListener("end", () => this.persistCamera());
    this.renderRequested = false;
    this._applyViewportModeVisibility();
    this.animate = this.animate.bind(this);
    requestAnimationFrame(this.animate);
  }

  clear() {
    this.basePoints = [];
    this.rawModelMesh = { meshes: [], visibility_points: [] };
    this.rawModelMeshVisibilityPoints = [];
    this.rawModelPoints = [];
    this.anchoredPoints = [];
    this.emitterPoints = [];
    this.pointIndex = {};
    this.rawModelIndex = {};
    this.fitCamera = null;
    this.resetCamera = null;
    this.rawModelFitCamera = null;
    this.rawModelResetCamera = null;
    this.particleCameraState = null;
    this.rawModelCameraState = null;
    this.currentBounds = null;
    this.currentScene = null;
    this._disposeRawModelMeshes();
    for (const geometry of [this.rawModelGeometry, this.shellGeometry, this.emitterGeometry, this.trailGeometry]) {
      geometry.setAttribute("position", new THREE.Float32BufferAttribute([], 3));
      geometry.setAttribute("size", new THREE.Float32BufferAttribute([], 1));
      geometry.setAttribute("brightness", new THREE.Float32BufferAttribute([], 1));
      geometry.setAttribute("alphaFactor", new THREE.Float32BufferAttribute([], 1));
    }
    this.renderer.setClearColor(new THREE.Color().setRGB(0.03, 0.03, 0.03, THREE.SRGBColorSpace), 1);
    this._applyViewportModeVisibility();
    this.requestRender();
  }

  animate(timestamp) {
    if (!this.lastFrameMs) {
      this.lastFrameMs = timestamp;
    }
    const deltaSeconds = Math.min(Math.max((timestamp - this.lastFrameMs) / 1000, 0), 0.12);
    this.lastFrameMs = timestamp;
    if (this.shouldAutoplay(timestamp)) {
      const nextProgress = (previewProgress + (deltaSeconds / shotDurationSeconds())) % 1;
      setPreviewProgress(nextProgress, { fromAutoplay: true });
    }
    this.controls.update();
    if (this.renderRequested) {
      this.resize();
      this.renderer.render(this.scene, this.camera);
      this.renderRequested = false;
    }
    requestAnimationFrame(this.animate);
  }

  requestRender() {
    this.renderRequested = true;
  }

  _currentPixelRatio() {
    const pixelRatio = Number(this.renderer.getPixelRatio?.() || 1);
    return Number.isFinite(pixelRatio) && pixelRatio > 0 ? pixelRatio : 1;
  }

  _syncMaterialPointScale(height) {
    const pixelRatio = this._currentPixelRatio();
    const drawBufferHeight = Math.max(1, height * pixelRatio);
    const focalPx = (drawBufferHeight * 0.5) / Math.tan(THREE.MathUtils.degToRad(this.camera.fov * 0.5));
    const minPointSizePx = Math.max(0.4, Number(this.currentAppearance.min_radius_px || 0.34) * 2.0) * pixelRatio;
    this.shellMaterial.uniforms.focalPx.value = focalPx;
    this.rawModelMaterial.uniforms.focalPx.value = focalPx;
    this.emitterMaterial.uniforms.focalPx.value = focalPx;
    this.trailMaterial.uniforms.focalPx.value = focalPx;
    this.shellMaterial.uniforms.minPointSizePx.value = minPointSizePx;
    this.rawModelMaterial.uniforms.minPointSizePx.value = minPointSizePx * 1.12;
    this.emitterMaterial.uniforms.minPointSizePx.value = minPointSizePx * 1.85;
    this.trailMaterial.uniforms.minPointSizePx.value = minPointSizePx * 1.8;
  }

  _applyRendererSize(width, height, options = {}) {
    const requestedPixelRatio = Number(options.pixelRatio);
    if (Number.isFinite(requestedPixelRatio) && requestedPixelRatio > 0) {
      this.renderer.setPixelRatio(requestedPixelRatio);
    }
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height, false);
    this._syncMaterialPointScale(height);
  }

  shouldAutoplay(timestamp = performance.now()) {
    return (
      previewIsPlaying()
      &&
      currentTab === "effect"
      && this.viewportMode === "particle"
      && effectReady()
      && this.basePoints.length > 0
      && this.captureDepth <= 0
      && !this.scrubbing
      && timestamp >= this.autoplayResumeAt
    );
  }

  beginScrub() {
    this.scrubbing = true;
    this.autoplayResumeAt = Infinity;
    setPreviewPlaybackState("paused");
  }

  endScrub() {
    this.scrubbing = false;
    this.autoplayResumeAt = Infinity;
    setPreviewPlaybackState("paused");
  }

  resize() {
    const width = Math.max(1, this.host.clientWidth);
    const height = Math.max(1, this.host.clientHeight);
    this._applyRendererSize(width, height);
    this.controls.handleResize();
  }

  _disposeRawModelMeshes() {
    for (const child of [...this.rawModelMeshGroup.children]) {
      this.rawModelMeshGroup.remove(child);
      child.geometry?.dispose?.();
      const materials = Array.isArray(child.material) ? child.material : [child.material];
      for (const material of materials.filter(Boolean)) {
        for (const key of ["map", "normalMap", "metalnessMap", "roughnessMap", "emissiveMap"]) {
          material[key]?.dispose?.();
        }
        material.dispose?.();
      }
    }
  }

  _textureFromDataUrl(dataUrl, { flipY = true, colorSpace = THREE.NoColorSpace } = {}) {
    if (!dataUrl) {
      return null;
    }
    const texture = this.rawModelTextureLoader.load(dataUrl, () => this.requestRender());
    texture.flipY = flipY;
    texture.colorSpace = colorSpace;
    texture.needsUpdate = true;
    return texture;
  }

  _buildRawModelMaterial(spec = {}) {
    const baseColor = Array.isArray(spec.base_color) ? spec.base_color : [0.82, 0.82, 0.82, 1];
    const emissive = Array.isArray(spec.emissive) ? spec.emissive : [0, 0, 0];
    const opacity = clamp(Number(spec.opacity ?? baseColor[3] ?? 1), 0, 1);
    const alphaMode = String(spec.alpha_mode || (opacity < 0.999 ? "BLEND" : "OPAQUE")).toUpperCase();
    const transparent = alphaMode === "BLEND" || opacity < 0.999;
    const flipY = Boolean(spec.flip_y);
    const material = new THREE.MeshStandardMaterial({
      color: new THREE.Color().setRGB(
        clamp(Number(baseColor[0] ?? 0.82), 0, 1),
        clamp(Number(baseColor[1] ?? 0.82), 0, 1),
        clamp(Number(baseColor[2] ?? 0.82), 0, 1),
        THREE.SRGBColorSpace,
      ),
      emissive: new THREE.Color().setRGB(
        clamp(Number(emissive[0] ?? 0), 0, 1),
        clamp(Number(emissive[1] ?? 0), 0, 1),
        clamp(Number(emissive[2] ?? 0), 0, 1),
        THREE.SRGBColorSpace,
      ),
      metalness: clamp(Number(spec.metalness ?? 0), 0, 1),
      roughness: clamp(Number(spec.roughness ?? 1), 0, 1),
      transparent,
      opacity,
      alphaTest: alphaMode === "MASK" ? clamp(Number(spec.alpha_cutoff ?? 0.5), 0, 1) : 0,
      depthWrite: !transparent,
      side: spec.double_sided ? THREE.DoubleSide : THREE.FrontSide,
    });
    material.map = this._textureFromDataUrl(spec.map, { flipY, colorSpace: THREE.SRGBColorSpace });
    material.normalMap = this._textureFromDataUrl(spec.normal_map, { flipY, colorSpace: THREE.NoColorSpace });
    material.metalnessMap = this._textureFromDataUrl(spec.metallic_roughness_map, { flipY, colorSpace: THREE.NoColorSpace });
    material.roughnessMap = material.metalnessMap;
    material.emissiveMap = this._textureFromDataUrl(spec.emissive_map, { flipY, colorSpace: THREE.SRGBColorSpace });
    material.needsUpdate = true;
    return material;
  }

  _applyRawModelMeshPayload(payload = {}) {
    this._disposeRawModelMeshes();
    const meshes = Array.isArray(payload.meshes) ? payload.meshes : [];
    this.rawModelMeshVisibilityPoints = Array.isArray(payload.visibility_points) ? payload.visibility_points : [];
    for (const meshPayload of meshes) {
      const positions = Array.isArray(meshPayload.positions) ? meshPayload.positions : [];
      const indices = Array.isArray(meshPayload.indices) ? meshPayload.indices : [];
      if (!positions.length || !indices.length) {
        continue;
      }
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
      if (Array.isArray(meshPayload.uvs) && meshPayload.uvs.length === ((positions.length / 3) * 2)) {
        geometry.setAttribute("uv", new THREE.Float32BufferAttribute(meshPayload.uvs, 2));
      }
      geometry.setIndex(new THREE.BufferAttribute(new Uint32Array(indices), 1));
      if (Array.isArray(meshPayload.normals) && meshPayload.normals.length === positions.length) {
        geometry.setAttribute("normal", new THREE.Float32BufferAttribute(meshPayload.normals, 3));
      } else {
        geometry.computeVertexNormals();
      }
      geometry.computeBoundingSphere();
      const mesh = new THREE.Mesh(geometry, this._buildRawModelMaterial(meshPayload.material || {}));
      mesh.name = String(meshPayload.name || "raw_model_mesh");
      mesh.frustumCulled = false;
      this.rawModelMeshGroup.add(mesh);
    }
  }

  applyPayload(payload) {
    this.currentScene = structuredClone(payload.scene || {});
    this.currentBounds = payload.bounds || null;
    this.currentAppearance = payload.appearance || this.currentAppearance;
    this.fitCamera = payload.fit_camera;
    this.resetCamera = payload.reset_camera || payload.fit_camera || null;
    this.rawModelFitCamera = payload.raw_model_fit_camera || payload.fit_camera || null;
    this.rawModelResetCamera = payload.raw_model_reset_camera || this.rawModelFitCamera || this.resetCamera || null;
    this.rawModelMesh = payload.raw_model_mesh || { meshes: [], visibility_points: [] };
    this.basePoints = payload.points || [];
    this.rawModelPoints = payload.raw_model_points || [];
    this.anchoredPoints = payload.anchored_points || this.basePoints.filter((point) => pointMotionMode(point, { motionMode: this.pointIndex.motion_mode ?? -1 }) <= PARTICLE_MOTION_ANCHOR_ATTACHMENT);
    this.emitterPoints = payload.emitter_points || [];
    this.pointIndex = Object.fromEntries((payload.point_schema || []).map((name, index) => [name, index]));
    this.rawModelIndex = Object.fromEntries((payload.raw_model_schema || []).map((name, index) => [name, index]));
    this._applyRawModelMeshPayload(this.rawModelMesh);
    this.rawModelGeometry.setAttribute("position", new THREE.Float32BufferAttribute(this._rawModelPositions(this.rawModelPoints), 3));
    this.rawModelGeometry.setAttribute("size", new THREE.Float32BufferAttribute(this._rawModelSizes(this.rawModelPoints), 1));
    this.rawModelGeometry.setAttribute("brightness", new THREE.Float32BufferAttribute(this._rawModelBrightnesses(this.rawModelPoints), 1));
    this.rawModelGeometry.setAttribute("alphaFactor", new THREE.Float32BufferAttribute(this._rawModelAlphas(this.rawModelPoints), 1));
    this.shellGeometry.setAttribute("size", new THREE.Float32BufferAttribute(this._sizes(this.anchoredPoints), 1));
    this.shellGeometry.setAttribute("brightness", new THREE.Float32BufferAttribute(this._brightnesses(this.anchoredPoints), 1));
    this.emitterGeometry.setAttribute("size", new THREE.Float32BufferAttribute(this._sizes(this.emitterPoints), 1));
    this.emitterGeometry.setAttribute("brightness", new THREE.Float32BufferAttribute(this._brightnesses(this.emitterPoints), 1));
    this.trailGeometry.setAttribute("size", new THREE.Float32BufferAttribute([], 1));
    this.trailGeometry.setAttribute("brightness", new THREE.Float32BufferAttribute([], 1));
    this.rawModelGeometry.computeBoundingSphere();
    this.shellGeometry.computeBoundingSphere();
    this.emitterGeometry.computeBoundingSphere();
    this.trailGeometry.computeBoundingSphere();
    const background = clamp(Number(payload.scene.render.background || 0.03), 0, 1);
    this.renderer.setClearColor(new THREE.Color().setRGB(background, background, background, THREE.SRGBColorSpace), 1);
    this._syncMaterialPointScale(Math.max(1, this.host.clientHeight || this.renderer.getSize(new THREE.Vector2()).y || 1));
    this.setProgress(previewProgress);
    const particleCamera = this._resolvedPayloadCamera(payload.camera, this.resetCamera, payload.fit_camera);
    this.particleCameraState = particleCamera ? structuredClone(particleCamera) : null;
    if (!this.rawModelCameraState || !this._cameraHasVisibleRawModel(this.rawModelCameraState)) {
      this.rawModelCameraState = this.rawModelResetCamera ? structuredClone(this.rawModelResetCamera) : null;
    }
    this.applyCamera(this.viewportMode === "model"
      ? (this.rawModelCameraState || this.rawModelResetCamera || this.rawModelFitCamera || particleCamera)
      : (this.particleCameraState || this.resetCamera || particleCamera));
    this._applyViewportModeVisibility();
    this.requestRender();
  }

  _resolvedPayloadCamera(cameraState, resetCamera, fitCamera) {
    if (!cameraState) {
      return resetCamera || fitCamera;
    }
    if (!resetCamera && !fitCamera) {
      return cameraState;
    }
    return this._cameraHasVisibleAnchors(cameraState) ? cameraState : (resetCamera || fitCamera);
  }

  _cameraHasVisibleAnchors(cameraState) {
    return this._cameraHasVisiblePoints(cameraState, this.anchoredPoints, {
      x: this.pointIndex.x ?? 0,
      y: this.pointIndex.y ?? 1,
      z: this.pointIndex.z ?? 2,
    });
  }

  _cameraHasVisibleRawModel(cameraState) {
    if (this.rawModelMeshVisibilityPoints.length) {
      return this._cameraHasVisiblePoints(cameraState, this.rawModelMeshVisibilityPoints, { x: 0, y: 1, z: 2 });
    }
    return this._cameraHasVisiblePoints(cameraState, this.rawModelPoints, {
      x: this.rawModelIndex.x ?? 0,
      y: this.rawModelIndex.y ?? 1,
      z: this.rawModelIndex.z ?? 2,
    });
  }

  _cameraHasVisiblePoints(cameraState, points, idx) {
    if (!points.length) {
      return false;
    }
    const width = Math.max(1, this.host.clientWidth || 1);
    const height = Math.max(1, this.host.clientHeight || 1);
    const step = Math.max(1, Math.floor(points.length / 320));
    let visible = 0;
    let sampled = 0;
    for (let index = 0; index < points.length; index += step) {
      const point = points[index];
      const projected = projectPointToScreen(
        [Number(point[idx.x] || 0), Number(point[idx.y] || 0), Number(point[idx.z] || 0)],
        cameraState,
        width,
        height,
      );
      sampled += 1;
      if (!projected) {
        continue;
      }
      const [x, y] = projected;
      if (x >= -32 && x <= (width + 32) && y >= -32 && y <= (height + 32)) {
        visible += 1;
      }
    }
    return visible >= Math.max(24, Math.floor(sampled * 0.18));
  }

  previewScene(sceneState) {
    if (!this.currentScene) return;
    this.currentScene = structuredClone(sceneState);
    const background = clamp(Number(this.currentScene.render.background || 0.03), 0, 1);
    this.renderer.setClearColor(new THREE.Color().setRGB(background, background, background, THREE.SRGBColorSpace), 1);
    this.setProgress(previewProgress);
    this.requestRender();
  }

  _stateForProgress(progress) {
    const eased = easeInOut(progress);
    const settleEnvelope = Math.max(0, Math.sin(eased * Math.PI));
    const breakup = this.currentScene.breakup;
    const emitter = this.currentScene.emitter || {};
    const anchoredPositions = new Float32Array(this.anchoredPoints.length * 3);
    const anchoredReleases = new Float32Array(this.anchoredPoints.length);
    const emitterPositions = new Float32Array(this.emitterPoints.length * 3);
    const emitterReleases = new Float32Array(this.emitterPoints.length);
    const trailPositions = [];
    const trailSizes = [];
    const trailBrightness = [];
    const trailAlphas = [];
    const motion = particleMotionContext(this.currentBounds, this.cameraState(), breakup, emitter);
    const indexOf = (name) => this.pointIndex[name] ?? -1;
    const idx = {
      x: indexOf("x"),
      y: indexOf("y"),
      z: indexOf("z"),
      radius: indexOf("radius"),
      release: indexOf("release"),
      retain: indexOf("retain"),
      normalX: indexOf("normal_x"),
      normalY: indexOf("normal_y"),
      normalZ: indexOf("normal_z"),
      phase: indexOf("phase"),
      drift: indexOf("drift"),
      depth: indexOf("depth"),
      halo: indexOf("halo"),
      shell: indexOf("shell"),
      travel: indexOf("travel"),
      emit: indexOf("emit"),
      brightness: indexOf("brightness"),
      alphaBase: indexOf("alpha_base"),
      alphaDecay: indexOf("alpha_decay"),
      motionMode: indexOf("motion_mode"),
    };
    const applyState = (points, positions, releases, anchoredLayer) => {
      for (let index = 0; index < points.length; index += 1) {
        const point = points[index];
      const shellWeight = idx.shell >= 0 ? Number(point[idx.shell] || 0) : 0;
      const emissionWeight = idx.emit >= 0 ? Number(point[idx.emit] || 0) : Number(point[idx.halo] || 0);
      const travelWeight = idx.travel >= 0 ? Number(point[idx.travel] || 0.22) : (0.22 + (emissionWeight * 1.1));
      const motionMode = pointMotionMode(point, idx);
      const releaseBias = particleDirectionalReleaseBias(point, idx, motion);
      const releaseGate = clamp(0.32 + (point[idx.release] * releaseBias * 1.04), 0, 1.85);
      const retainFactor = 1 - (point[idx.retain] * 0.22);
      const emissionGain = 0.78 + (emissionWeight * 0.94);
      const strength = Number(emitter.strength || 0.74);
      const rate = Number(emitter.rate || 0.82);
      const plumeEnvelope = motionMode === PARTICLE_MOTION_EMISSION_PLUME
        ? plumeEmissionEnvelope(progress, point[idx.phase], point[idx.drift], rate)
        : eased;
      let release = breakup.amount > 0
        ? ((breakup.amount ** 0.72) * plumeEnvelope * releaseGate * retainFactor * emissionGain * (0.34 + (rate * (motionMode === PARTICLE_MOTION_EMISSION_PLUME ? 1.24 : 0.28))) * (0.92 + (strength * (motionMode === PARTICLE_MOTION_EMISSION_PLUME ? 0.34 : 0.08))))
        : 0;
      const normal = [point[idx.normalX], point[idx.normalY], point[idx.normalZ]];
      let offset = [0, 0, 0];
      if (anchoredLayer || motionMode === PARTICLE_MOTION_ANCHOR_SHELL || motionMode === PARTICLE_MOTION_ANCHOR_ATTACHMENT) {
        release = Math.min(release * (motionMode === PARTICLE_MOTION_ANCHOR_SHELL ? 0.10 : 0.14), 0.09);
        const settleDistance = Math.min(
          anchoredLayer ? 0.0024 : 0.0034,
          breakup.tail * (0.0012 + (shellWeight * 0.0009) + ((1 - point[idx.retain]) * 0.0007)) * (0.30 + (breakup.amount * 0.34)) * settleEnvelope,
        );
        offset = vectorScale(normal, settleDistance);
      } else {
        release *= 0.92 + (strength * 0.22);
        const decayTailGain = 0.86 + ((1 - Number(emitter.decay || 0.56)) * 0.68);
        const tailDistance = breakup.tail * release * decayTailGain * (0.72 + (travelWeight * (1.42 + (strength * 1.36) + (rate * 0.28))) + (motion.driftMagnitude * 1.02) + (point[idx.halo] * 0.22));
        const phase = point[idx.phase] + (eased * Math.PI * 2.0 * point[idx.drift]);
        const normalLift = 0.30 + (point[idx.depth] * 0.24);
        const haloLift = 0.18 + (point[idx.halo] * 0.36);
        const driftWeight = 0.36 + haloLift + (point[idx.drift] * 0.14) + (emissionWeight * 0.34) + (strength * 0.52) + (rate * 0.18);
        const normalOffset = vectorScale(normal, tailDistance * normalLift * (0.72 + (emissionWeight * 0.14)));
        const directionalOffset = motion.driftMagnitude >= 0.05
          ? vectorScale(motion.driftDirection, tailDistance * driftWeight * (0.46 + (motion.driftMagnitude * 1.28) + (travelWeight * 0.28) + (strength * 0.24)))
          : [0, 0, 0];
        const depthOffset = vectorScale(motion.forward, (point[idx.depth] - 0.5) * tailDistance * (0.12 + (emissionWeight * 0.08)));
        const turbulence = breakup.turbulence * release * (0.34 + (emissionWeight * 0.26) + (rate * 0.08)) * (0.82 + ((1 - Number(emitter.decay || 0.56)) * 0.40));
        const swirl = breakup.swirl * release * (0.28 + (emissionWeight * 0.18)) * (0.78 + ((1 - Number(emitter.decay || 0.56)) * 0.32));
        const turbulenceOffset = vectorAdd(
          vectorScale(motion.lateralDirection, Math.cos(phase) * turbulence * (0.16 + (point[idx.halo] * 0.08) + (travelWeight * 0.04))),
          vectorScale(motion.forward, Math.sin(phase * 0.73) * turbulence * (0.10 + (point[idx.depth] * 0.05) + (emissionWeight * 0.04))),
        );
        let swirlAxis = vectorCross(motion.driftMagnitude >= 0.05 ? motion.driftDirection : motion.lateralDirection, normal);
        swirlAxis = vectorLength(swirlAxis) <= 1.0e-8 ? [...motion.lateralDirection] : vectorNormalize(swirlAxis, motion.lateralDirection);
        const swirlOffset = vectorAdd(
          vectorScale(swirlAxis, Math.sin(phase * 0.81) * swirl * (0.10 + (point[idx.halo] * 0.07) + (emissionWeight * 0.05))),
          vectorAdd(
            vectorScale(motion.lateralDirection, Math.cos(phase * 0.93) * swirl * (0.07 + (travelWeight * 0.015))),
            vectorScale(motion.forward, Math.cos(phase * 0.61) * swirl * (0.05 + (emissionWeight * 0.02)) * Math.abs(point[idx.normalZ])),
          ),
        );
        offset = vectorAdd(
          vectorAdd(normalOffset, directionalOffset),
          vectorAdd(depthOffset, vectorAdd(turbulenceOffset, swirlOffset)),
        );
      }
        positions[(index * 3) + 0] = point[idx.x] + offset[0];
        positions[(index * 3) + 1] = point[idx.y] + offset[1];
        positions[(index * 3) + 2] = point[idx.z] + offset[2];
        releases[index] = release;
        if (!anchoredLayer && motionMode === PARTICLE_MOTION_EMISSION_PLUME && release >= EMISSION_TRAIL_MIN_RELEASE) {
          const trailDistance = vectorLength(offset);
          if (trailDistance >= 0.004) {
            const trailSteps = EMISSION_TRAIL_STEPS + Math.round(emissionWeight * 2.0);
            for (let trailIndex = 1; trailIndex <= trailSteps; trailIndex += 1) {
              const trailRatio = trailIndex / (trailSteps + 1);
              trailPositions.push(
                point[idx.x] + (offset[0] * trailRatio * 0.96),
                point[idx.y] + (offset[1] * trailRatio * 0.96),
                point[idx.z] + (offset[2] * trailRatio * 0.96),
              );
              trailSizes.push(Math.max(0.0011, point[idx.radius] * (1.34 - (trailRatio * 0.18))));
              trailBrightness.push(clamp((point[idx.brightness] * 1.18) - (trailRatio * 0.06), 0, 1));
              const trailRelease = release * (0.72 - (trailRatio * 0.18));
              const trailAlpha = clamp(
                ((point[idx.alphaBase] * (1.9 - (trailRatio * 0.18))) - (trailRelease * point[idx.alphaDecay] * (0.08 + (Number(emitter.decay || 0.56) * 0.42)))),
                0.10,
                1.0,
              );
              trailAlphas.push(trailAlpha);
            }
          }
        }
      }
    };
    applyState(this.anchoredPoints, anchoredPositions, anchoredReleases, true);
    applyState(this.emitterPoints, emitterPositions, emitterReleases, false);
    return {
      anchoredPositions,
      anchoredReleases,
      emitterPositions,
      emitterReleases,
      trailPositions: new Float32Array(trailPositions),
      trailSizes: new Float32Array(trailSizes),
      trailBrightness: new Float32Array(trailBrightness),
      trailAlphas: new Float32Array(trailAlphas),
    };
  }

  _sizes(points) {
    const radiusIndex = this.pointIndex.radius ?? 3;
    return new Float32Array((points || []).map((point) => Math.max(0.0008, point[radiusIndex])));
  }

  _rawModelPositions(points) {
    const xIndex = this.rawModelIndex.x ?? 0;
    const yIndex = this.rawModelIndex.y ?? 1;
    const zIndex = this.rawModelIndex.z ?? 2;
    const positions = new Float32Array((points || []).length * 3);
    for (let index = 0; index < (points || []).length; index += 1) {
      const point = points[index];
      positions[(index * 3) + 0] = Number(point[xIndex] || 0);
      positions[(index * 3) + 1] = Number(point[yIndex] || 0);
      positions[(index * 3) + 2] = Number(point[zIndex] || 0);
    }
    return positions;
  }

  _rawModelSizes(points) {
    const radiusIndex = this.rawModelIndex.radius ?? 3;
    return new Float32Array((points || []).map((point) => Math.max(0.0012, Number(point[radiusIndex] || 0))));
  }

  _rawModelBrightnesses(points) {
    const brightnessIndex = this.rawModelIndex.brightness ?? 4;
    return new Float32Array((points || []).map((point) => clamp(Number(point[brightnessIndex] || 0), 0, 1)));
  }

  _rawModelAlphas(points) {
    const alphaIndex = this.rawModelIndex.alpha ?? 5;
    return new Float32Array((points || []).map((point) => clamp(Number(point[alphaIndex] || 0), 0.04, 1)));
  }

  _brightnesses(points) {
    const brightnessIndex = this.pointIndex.brightness ?? 15;
    return new Float32Array((points || []).map((point) => clamp(point[brightnessIndex], 0, 1)));
  }

  _alphas(points, releases) {
    const alphaBaseIndex = this.pointIndex.alpha_base ?? 16;
    const alphaDecayIndex = this.pointIndex.alpha_decay ?? 17;
    const motionModeIndex = this.pointIndex.motion_mode ?? 20;
    const emitterDecay = clamp(Number(this.currentScene?.emitter?.decay || 0.56), 0, 1);
    const alphas = new Float32Array((points || []).length);
    for (let index = 0; index < (points || []).length; index += 1) {
      const point = points[index];
      const motionMode = Number.isFinite(Number(point[motionModeIndex])) ? Number(point[motionModeIndex]) : PARTICLE_MOTION_LEGACY_DYNAMIC;
      const emissionPoint = motionMode === PARTICLE_MOTION_EMISSION_PLUME;
      const alphaBase = clamp(point[alphaBaseIndex], emissionPoint ? 0.06 : 0.025, 1);
      const alphaDecay = clamp(point[alphaDecayIndex], emissionPoint ? 0.008 : 0.01, 0.45);
      const alpha = emissionPoint
        ? ((alphaBase * 1.18) - (releases[index] * alphaDecay * (0.14 + (emitterDecay * 1.02))))
        : (alphaBase - (releases[index] * alphaDecay));
      alphas[index] = clamp(alpha, emissionPoint ? 0.06 : 0.025, 1);
    }
    return alphas;
  }

  setProgress(progress) {
    if (!this.basePoints.length) return;
    const state = this._stateForProgress(progress);
    this.shellGeometry.setAttribute("position", new THREE.Float32BufferAttribute(state.anchoredPositions, 3));
    this.shellGeometry.attributes.position.needsUpdate = true;
    this.shellGeometry.computeBoundingSphere();
    this.shellGeometry.setAttribute("alphaFactor", new THREE.Float32BufferAttribute(this._alphas(this.anchoredPoints, state.anchoredReleases), 1));
    this.shellGeometry.attributes.alphaFactor.needsUpdate = true;
    this.emitterGeometry.setAttribute("position", new THREE.Float32BufferAttribute(state.emitterPositions, 3));
    this.emitterGeometry.attributes.position.needsUpdate = true;
    this.emitterGeometry.computeBoundingSphere();
    this.emitterGeometry.setAttribute("alphaFactor", new THREE.Float32BufferAttribute(this._alphas(this.emitterPoints, state.emitterReleases), 1));
    this.emitterGeometry.attributes.alphaFactor.needsUpdate = true;
    this.trailGeometry.setAttribute("position", new THREE.Float32BufferAttribute(state.trailPositions, 3));
    this.trailGeometry.attributes.position.needsUpdate = true;
    this.trailGeometry.computeBoundingSphere();
    this.trailGeometry.setAttribute("size", new THREE.Float32BufferAttribute(state.trailSizes, 1));
    this.trailGeometry.attributes.size.needsUpdate = true;
    this.trailGeometry.setAttribute("brightness", new THREE.Float32BufferAttribute(state.trailBrightness, 1));
    this.trailGeometry.attributes.brightness.needsUpdate = true;
    this.trailGeometry.setAttribute("alphaFactor", new THREE.Float32BufferAttribute(state.trailAlphas, 1));
    this.trailGeometry.attributes.alphaFactor.needsUpdate = true;
    this.requestRender();
  }

  _applyViewportModeVisibility() {
    const particleMode = this.viewportMode === "particle";
    const hasRawModelMesh = this.rawModelMeshGroup.children.length > 0;
    this.rawModelLights.visible = !particleMode && hasRawModelMesh;
    this.rawModelMeshGroup.visible = !particleMode && hasRawModelMesh;
    this.rawModelPointsObject.visible = !particleMode && !hasRawModelMesh && this.rawModelPoints.length > 0;
    this.shellPoints.visible = particleMode;
    this.emitterPointsObject.visible = particleMode;
    this.trailPointsObject.visible = particleMode;
  }

  setViewportMode(mode) {
    const nextMode = mode === "model" ? "model" : "particle";
    if (this.viewportMode === nextMode) {
      this._applyViewportModeVisibility();
      this.requestRender();
      return;
    }
    const currentCamera = this.cameraState();
    if (this.viewportMode === "model") {
      this.rawModelCameraState = currentCamera;
    } else {
      this.particleCameraState = currentCamera;
    }
    this.viewportMode = nextMode;
    const nextCamera = this.viewportMode === "model"
      ? (this.rawModelCameraState && this._cameraHasVisibleRawModel(this.rawModelCameraState)
        ? this.rawModelCameraState
        : (this.rawModelResetCamera || this.rawModelFitCamera || this.particleCameraState || this.resetCamera || this.fitCamera))
      : (this.particleCameraState || this.resetCamera || this.fitCamera || this.rawModelResetCamera || this.rawModelFitCamera);
    if (nextCamera) {
      this.applyCamera(nextCamera);
    }
    this._applyViewportModeVisibility();
    this.requestRender();
  }

  applyCamera(cameraState) {
    const resolvedCamera = cameraVectors(cameraState);
    const target = new THREE.Vector3(...resolvedCamera.target);
    const eye = new THREE.Vector3(...resolvedCamera.eye);
    this.camera.fov = Number(cameraState?.fov || this.camera.fov || 34);
    this.camera.position.copy(eye);
    this.camera.up.set(...resolvedCamera.up);
    this.controls.target.copy(target);
    this.camera.lookAt(target);
    this.camera.updateProjectionMatrix();
    this.controls.update();
    this.requestRender();
  }

  cameraState() {
    const target = this.controls.target.clone();
    const offset = this.camera.position.clone().sub(target);
    const forward = vectorNormalize(
      [target.x - this.camera.position.x, target.y - this.camera.position.y, target.z - this.camera.position.z],
      [0, 0, -1],
    );
    const referenceUp = cameraReferenceUp(forward);
    const baseRight = vectorNormalize(vectorCross(forward, referenceUp), [1, 0, 0]);
    const baseUp = vectorNormalize(vectorCross(baseRight, forward), [0, 1, 0]);
    const rawUp = vectorNormalize([this.camera.up.x, this.camera.up.y, this.camera.up.z], [0, 1, 0]);
    let projectedUp = vectorSub(rawUp, vectorScale(forward, vectorDot(rawUp, forward)));
    if (vectorLength(projectedUp) <= 1.0e-8) {
      projectedUp = [...baseUp];
    } else {
      projectedUp = vectorNormalize(projectedUp, baseUp);
    }
    return {
      target_x: Number(target.x.toFixed(4)),
      target_y: Number(target.y.toFixed(4)),
      target_z: Number(target.z.toFixed(4)),
      yaw: Number(Math.atan2(offset.x, offset.z).toFixed(4)),
      pitch: Number(Math.atan2(offset.y, Math.sqrt((offset.x ** 2) + (offset.z ** 2))).toFixed(4)),
      roll: Number(signedAngleAroundAxis(baseUp, projectedUp, forward).toFixed(4)),
      distance: Number(offset.length().toFixed(4)),
      fov: Number(this.camera.fov.toFixed(4)),
    };
  }

  resetCameraToFit() {
    const targetCamera = this.viewportMode === "model"
      ? (this.rawModelResetCamera || this.rawModelFitCamera || this.resetCamera || this.fitCamera)
      : (this.resetCamera || this.fitCamera || this.rawModelResetCamera || this.rawModelFitCamera);
    if (!targetCamera) return;
    this.applyCamera(targetCamera);
    if (this.viewportMode === "model") {
      this.rawModelCameraState = this.cameraState();
      return;
    }
    this.particleCameraState = this.cameraState();
    this.persistCamera();
  }

  async persistCamera() {
    if (!project || !effectReady()) return;
    const camera = this.cameraState();
    if (this.viewportMode === "model") {
      this.rawModelCameraState = camera;
      return;
    }
    this.particleCameraState = camera;
    setValue("scene.camera", camera);
    try {
      project = await postJson("/api/project", { scene: { camera } });
      refreshStats();
    } catch (error) {
      setPreviewLog(error.message || "Unable to save camera.");
    }
  }

  forceRender() {
    this.resize();
    this.renderer.render(this.scene, this.camera);
    this.renderRequested = false;
  }

  async captureDataUrl(progress = previewProgress, options = {}) {
    this.captureDepth += 1;
    const wasScrubbing = this.scrubbing;
    this.scrubbing = true;
    const requestedWidth = Math.max(0, Number(options.width || 0));
    const requestedHeight = Math.max(0, Number(options.height || 0));
    const transparentBackground = options.transparentBackground === true;
    const originalSize = this.renderer.getSize(new THREE.Vector2());
    const originalPixelRatio = this._currentPixelRatio();
    const originalAspect = this.camera.aspect;
    const originalClearAlpha = this.renderer.getClearAlpha();
    const originalClearColor = this.renderer.getClearColor(new THREE.Color());
    try {
      if (typeof progress === "number") {
        this.setProgress(progress);
      }
      if (requestedWidth > 0 && requestedHeight > 0) {
        const capturePixelRatio = Math.max(1, Number(options.pixelRatio || 1));
        this._applyRendererSize(requestedWidth, requestedHeight, { pixelRatio: capturePixelRatio });
      }
      const background = clamp(Number(this.currentScene?.render?.background || this.currentAppearance.background || 0.03), 0, 1);
      this.renderer.setClearColor(new THREE.Color().setRGB(background, background, background, THREE.SRGBColorSpace), transparentBackground ? 0 : 1);
      if (requestedWidth > 0 && requestedHeight > 0) {
        this.renderRequested = false;
        this.renderer.render(this.scene, this.camera);
      } else {
        await nextAnimationFrame();
        await nextAnimationFrame();
        this.forceRender();
      }
      return this.renderer.domElement.toDataURL("image/png");
    } finally {
      this.renderer.setClearColor(originalClearColor, originalClearAlpha);
      if (requestedWidth > 0 && requestedHeight > 0) {
        this._applyRendererSize(originalSize.x, originalSize.y, { pixelRatio: originalPixelRatio });
        this.camera.aspect = originalAspect;
        this.camera.updateProjectionMatrix();
      } else {
        this._syncMaterialPointScale(Math.max(1, this.host.clientHeight || originalSize.y || 1));
      }
      this.captureDepth = Math.max(0, this.captureDepth - 1);
      this.scrubbing = wasScrubbing;
      if (!wasScrubbing) {
        this.autoplayResumeAt = performance.now() + 120;
      }
    }
  }
}

function setActiveTab(tabId) {
  if (tabId === "effect" && !effectReady()) return;
  if (tabId === "burn" && !burnReady()) return;
  currentTab = tabId;
  for (const button of document.querySelectorAll(".workflow-step[data-tab]")) {
    const active = button.dataset.tab === tabId;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", active ? "true" : "false");
  }
  for (const panel of document.querySelectorAll("[data-tab-panel]")) {
    panel.classList.toggle("active", panel.dataset.tabPanel === tabId);
  }
  if (tabId === "effect") {
    effectViewer?.endScrub();
    if (previewIsPlaying()) {
      effectViewer.autoplayResumeAt = performance.now();
    }
  }
  updateWorkflowState();
}

function updateWorkflowState() {
  const modelStep = document.getElementById("workflow-model");
  const effectStep = document.getElementById("workflow-effect");
  const burnStep = document.getElementById("workflow-burn");
  [modelStep, effectStep, burnStep].forEach((element) => element.classList.remove("complete", "locked"));
  if (selectedModelActive()) {
    modelStep.classList.add("complete");
  }
  if (!effectReady()) {
    effectStep.classList.add("locked");
    burnStep.classList.add("locked");
  } else if (approvalApproved()) {
    effectStep.classList.add("complete");
    burnStep.classList.add("complete");
  } else {
    burnStep.classList.add("locked");
  }
}

function createTooltip(helpText, label) {
  const text = tooltipText(helpText);
  const wrapper = document.createElement("div");
  wrapper.className = "tooltip";
  if (!text) {
    return wrapper;
  }
  const trigger = document.createElement("button");
  trigger.type = "button";
  trigger.className = "tooltip-trigger";
  trigger.setAttribute("aria-label", `${label} help`);
  trigger.innerHTML = '<span aria-hidden="true">i</span>';
  const popup = document.createElement("div");
  popup.className = "tooltip-popup";
  popup.setAttribute("role", "tooltip");
  popup.id = `tooltip-${tooltipIdCounter += 1}`;
  popup.textContent = text;
  trigger.setAttribute("aria-describedby", popup.id);
  wrapper.append(trigger, popup);
  return wrapper;
}

function resolvedControlLabel(targetId, spec) {
  if (targetId === "emitter-controls" && emitterDirectionSpace() === "subject" && spec.subjectLabel) {
    return spec.subjectLabel;
  }
  return spec.label;
}

function renderControlSectionHeaders() {
  for (const [sectionKey, spec] of Object.entries(sectionSpecs)) {
    const host = document.querySelector(`[data-section-key="${sectionKey}"] .section-title-row`);
    if (!host) continue;
    host.innerHTML = "";
    const title = document.createElement("h2");
    title.textContent = spec.title;
    host.append(title, createTooltip(spec.help, spec.title));
  }
}

function renderControls(targetId, specs) {
  const host = document.getElementById(targetId);
  host.innerHTML = "";
  for (const spec of specs) {
    const wrapper = document.createElement("div");
    wrapper.className = "control";
    const labelRow = document.createElement("div");
    labelRow.className = "control-label-row";
    const controlLabel = document.createElement("label");
    controlLabel.textContent = resolvedControlLabel(targetId, spec);
    labelRow.append(controlLabel, createTooltip(spec.help, controlLabel.textContent));

    const numberInput = document.createElement("input");
    numberInput.type = "number";
    numberInput.className = "control-number";
    numberInput.step = "1";
    if (spec.continuous !== true) {
      const displayBounds = displayIntegerBounds(spec);
      numberInput.min = String(displayBounds.min);
      numberInput.max = String(displayBounds.max);
    }
    numberInput.value = String(displayIntegerForSpec(spec, getValue(spec.path)));
    numberInput.disabled = !effectReady();

    const sliderInput = document.createElement("input");
    sliderInput.type = "range";
    sliderInput.min = String(spec.min);
    sliderInput.max = String(spec.max);
    sliderInput.step = String(spec.step);
    sliderInput.value = spec.continuous === true ? "0" : String(getValue(spec.path));
    sliderInput.disabled = !effectReady();

    const syncValue = (rawValue, source) => {
      let value = Number(rawValue);
      if (!Number.isFinite(value)) {
        value = Number(getValue(spec.path) || 0);
      }
      if (spec.continuous !== true) {
        value = clamp(value, Number(spec.min), Number(spec.max));
      }
      setValue(spec.path, value);
      if (source !== "number") {
        numberInput.value = String(displayIntegerForSpec(spec, value));
      }
      if (source !== "slider") {
        sliderInput.value = spec.continuous === true ? "0" : String(value);
      }
      syncPreviewWarning();
      effectViewer?.previewScene(project.scene);
      queueEffectPersist();
    };

    if (spec.continuous === true) {
      let sliderDeltaAnchor = 0;
      const resetContinuousSlider = () => {
        sliderDeltaAnchor = 0;
        sliderInput.value = "0";
      };
      sliderInput.addEventListener("input", () => {
        const nextOffset = Number(sliderInput.value);
        const delta = nextOffset - sliderDeltaAnchor;
        sliderDeltaAnchor = nextOffset;
        syncValue(Number(getValue(spec.path) || 0) + delta, "slider");
      });
      sliderInput.addEventListener("change", resetContinuousSlider);
      sliderInput.addEventListener("blur", resetContinuousSlider);
    } else {
      sliderInput.addEventListener("input", () => {
        syncValue(Number(sliderInput.value), "slider");
      });
    }
    const commitNumberInput = () => {
      if (numberInput.value === "") {
        numberInput.value = String(displayIntegerForSpec(spec, getValue(spec.path)));
        return;
      }
      syncValue(rawValueFromDisplayInteger(spec, numberInput.value), "number");
    };
    numberInput.addEventListener("change", commitNumberInput);
    numberInput.addEventListener("blur", commitNumberInput);
    numberInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        commitNumberInput();
        numberInput.blur();
      }
    });

    wrapper.append(labelRow, numberInput, sliderInput);
    host.appendChild(wrapper);
  }
}

async function selectSnapshot(snapshotId) {
  setPreviewLog(`Loading ${snapshotId}…`);
  project = await postJson("/api/snapshot/select", { snapshot_id: snapshotId });
  if (!approvalApproved()) {
    lastBurnManifest = null;
  }
  await refreshForProject(approvalApproved() && currentTab === "burn" ? "burn" : "effect");
  setPreviewLog(`Loaded ${snapshotId}`);
}

function snapshotKindLabel(kind) {
  if (kind === "approved") return "Approved";
  if (kind === "initial") return "Initial";
  return "Snapshot";
}

function renderSnapshotList() {
  const host = document.getElementById("snapshot-list");
  host.innerHTML = "";
  const snapshots = [...(project.snapshots || [])].reverse();
  for (const snapshot of snapshots) {
    const item = document.createElement("button");
    item.type = "button";
    item.className = `snapshot-item ${snapshot.id === project.active_snapshot_id ? "active" : ""}`;
    item.innerHTML = `
      <div class="snapshot-primary">
        <strong>${snapshot.label}</strong>
        <span class="snapshot-badge kind-${badgeClassToken(snapshot.kind || "snapshot")}">${snapshotKindLabel(snapshot.kind)}</span>
      </div>
      <span class="snapshot-meta">${[formatSnapshotTimestamp(snapshot.created_at), snapshot.id].filter(Boolean).join(" · ")}</span>
    `;
    item.addEventListener("click", async () => {
      if (snapshot.id === project.active_snapshot_id) {
        return;
      }
      try {
        await selectSnapshot(snapshot.id);
      } catch (error) {
        setPreviewLog(error.message || "Unable to load snapshot.");
      }
    });
    host.appendChild(item);
  }
}

function renderPresetOptions() {
  const presetSelect = document.getElementById("preset-family");
  presetSelect.innerHTML = "";
  const builtinOption = document.createElement("option");
  builtinOption.value = DEFAULT_PRESET_ID;
  builtinOption.textContent = project?.available_presets?.[DEFAULT_PRESET_ID]?.label || "Default";
  presetSelect.appendChild(builtinOption);
  for (const preset of project?.saved_presets || []) {
    const option = document.createElement("option");
    option.value = preset.id;
    option.textContent = preset.label;
    presetSelect.appendChild(option);
  }
  presetSelect.value = activePresetId();
}

function renderSketchfabAuthControls() {
  const statusNode = document.getElementById("sketchfab-auth-status");
  const actionButton = document.getElementById("sketchfab-auth-action");
  const tokenInput = document.getElementById("sketchfab-token-input");
  if (!statusNode || !actionButton || !tokenInput) {
    return;
  }
  tokenInput.hidden = true;
  tokenInput.disabled = false;
  actionButton.disabled = false;
  if (sketchfabAuth?.connected && sketchfabEnvManaged()) {
    const label = sketchfabAuth.display_name || sketchfabAuth.username || "your account";
    statusNode.textContent = sketchfabAuth?.message || `Sketchfab connected as ${label}. Token is managed by CE_SKETCHFAB_API_TOKEN.`;
    actionButton.textContent = "Env Managed";
    actionButton.disabled = true;
    return;
  }
  if (sketchfabAuth?.connected) {
    const label = sketchfabAuth.display_name || sketchfabAuth.username || "your account";
    statusNode.textContent = sketchfabAuth?.message || `Sketchfab connected as ${label}. Downloadable CC0 and CC BY results can be fetched.`;
    actionButton.textContent = "Disconnect";
    actionButton.disabled = false;
    return;
  }
  if (sketchfabTokenSource() === "env") {
    statusNode.textContent = sketchfabAuth?.message || "CE_SKETCHFAB_API_TOKEN is configured but not usable.";
    actionButton.textContent = "Env Managed";
    actionButton.disabled = true;
    return;
  }
  tokenInput.hidden = false;
  statusNode.textContent = sketchfabAuth?.message || "Paste a Sketchfab personal token to fetch downloadable CC0 and CC BY models.";
  actionButton.textContent = "Connect";
}

function renderModelSourceResources() {
  const host = document.getElementById("model-source-resources");
  if (!host) {
    return;
  }
  const resources = modelSourceResources.length ? modelSourceResources : fallbackModelSourceResources(activeModelSourceQuery());
  host.innerHTML = "";
  for (const resource of resources) {
    const card = document.createElement("div");
    card.className = "model-resource-card";
    card.innerHTML = `
      <div class="model-source-line">
        <div class="model-source-title">${escapeHtml(resource.label || "External Library")}</div>
        <span class="model-source-badge capability-${badgeClassToken("external_only")}">External Only</span>
      </div>
      <div class="model-source-meta">${escapeHtml(resource.availability_note || "")}</div>
      <div class="model-source-status">${escapeHtml(resource.license_note || "")}</div>
      <div class="model-resource-actions">
        <a class="resource-link" href="${escapeHtml(resource.search_url || "#")}" target="_blank" rel="noreferrer">Search Site</a>
      </div>
    `;
    host.appendChild(card);
  }
}

function syncModelResourceModalState(open) {
  const trigger = document.getElementById("model-resource-modal-trigger");
  const shell = document.getElementById("model-resource-modal");
  if (!trigger || !shell) {
    return;
  }
  shell.hidden = !open;
  document.body.classList.toggle("modal-open", open);
  trigger.setAttribute("aria-expanded", open ? "true" : "false");
}

function openModelResourceModal(trigger = document.activeElement) {
  const linkTrigger = document.getElementById("model-resource-modal-trigger");
  const closeButton = document.getElementById("model-resource-modal-close");
  if (!linkTrigger || !closeButton) {
    return;
  }
  modelResourceModalReturnFocus = trigger instanceof HTMLElement ? trigger : linkTrigger;
  renderModelSourceResources();
  syncModelResourceModalState(true);
  closeButton.focus();
}

function closeModelResourceModal({ restoreFocus = true } = {}) {
  const linkTrigger = document.getElementById("model-resource-modal-trigger");
  syncModelResourceModalState(false);
  if (restoreFocus) {
    (modelResourceModalReturnFocus || linkTrigger)?.focus();
  }
  modelResourceModalReturnFocus = null;
}

function renderModelSourcePanel() {
  renderSketchfabAuthControls();
  renderModelSourceResources();
  const activeHost = document.getElementById("model-source-active");
  const resultsSummary = document.getElementById("model-results-summary");
  const selected = project?.model_source || {};
  if (selectedModelActive()) {
    const selectedAttribution = modelAttributionText(selected);
    const selectedLinks = modelSourceLinksMarkup(selected);
    activeHost.classList.remove("empty");
    activeHost.classList.add("active");
    activeHost.innerHTML = `
      <div class="selected-model-head">
        ${modelSourceThumbnailMarkup(selected, "selected")}
        <div class="selected-model-copy">
          <div class="model-source-line">
            <div class="model-source-title">${escapeHtml(selected.title || selected.remote_id || "Selected model")}</div>
            <span class="model-source-badge kind-${badgeClassToken(selected.provider_kind || "user_supplied")}">${escapeHtml(titleCase(selected.provider_kind || "user_supplied"))}</span>
            <span class="model-source-badge capability-${badgeClassToken(selected.provider_capability || "enabled")}">${escapeHtml(titleCase(selected.provider_capability || "enabled"))}</span>
          </div>
          <div class="model-source-meta">${escapeHtml(selected.provider_label || titleCase(selected.provider || "local_upload"))} · ${escapeHtml(selected.license_summary || titleCase(selected.license_class || "unknown"))}</div>
          ${selectedAttribution ? `<div class="model-source-meta">${escapeHtml(selectedAttribution)}</div>` : ""}
          ${selectedLinks ? `<div class="model-source-links">${selectedLinks}</div>` : ""}
          <div class="model-source-status success">Currently loaded for the effect stage.</div>
        </div>
        <div class="selected-model-actions">
          <button id="clear-model-button" type="button" class="secondary">Clear Selection</button>
        </div>
      </div>
    `;
    activeHost.querySelector("#clear-model-button")?.addEventListener("click", clearModelSourceSelection);
  } else {
    activeHost.classList.add("empty");
    activeHost.classList.remove("active");
    activeHost.textContent = "No model selected. Search for a subject or upload a local mesh when you already know the exact asset you need.";
  }
  wireModelSourceThumbnails(activeHost);

  const host = document.getElementById("model-source-results");
  host.innerHTML = "";
  if (!modelSourceResults.length) {
    if (resultsSummary) {
      resultsSummary.textContent = "Search a provider to load candidates.";
    }
    const empty = document.createElement("div");
    empty.className = "selected-model-card empty";
    empty.textContent = "Connected providers: NASA 3D, Poly Pizza, and Sketchfab are selectable when eligible. Smithsonian Open Access remains search-only. External libraries below open site-scoped search.";
    host.appendChild(empty);
    return;
  }
  if (resultsSummary) {
    const activeQuery = (document.getElementById("model-source-query")?.value || modelSourceResults[0]?.query || "").trim();
    resultsSummary.textContent = `${modelSourceResults.length} candidate${modelSourceResults.length === 1 ? "" : "s"}${activeQuery ? ` for “${activeQuery}”` : ""}`;
  }
  for (const candidate of modelSourceResults) {
    const result = document.createElement("div");
    result.className = `model-source-result${candidate.provider_capability === "search_only" ? " search-only" : ""}`;
    const fetched = fetchedModelResults.get(`${candidate.provider}:${candidate.remote_id}`);
    const searchOnly = candidate.provider_capability === "search_only";
    const authRequired = candidateNeedsSketchfabAuth(candidate) && !fetched;
    const fetchedUsable = modelCandidateUsable(fetched);
    const selectedCandidate = fetched || candidate;
    const isSelected = selectedModelActive() && selected.remote_id === candidate.remote_id && selected.provider === candidate.provider;
    if (isSelected) {
      result.classList.add("selected");
    }
    const rowStatus = modelSelectionStatusForCandidate(candidate, fetched, selected);
    const rowTargeted = modelSelectionState?.targetKey && modelSelectionState.targetKey === (modelCandidateKey(fetched) || modelCandidateKey(candidate));
    const fetchDisabled = searchOnly || Boolean(fetched) || (selectionInFlight() && !rowTargeted);
    const useDisabled = searchOnly || !fetched || !fetchedUsable || isSelected || (selectionInFlight() && !rowTargeted);
    const metaParts = [
      fetched?.eligibility_note || candidate.eligibility_note,
      candidate.author_name ? `By ${candidate.author_name}` : "",
      candidate.remote_url,
    ].filter(Boolean);
    result.innerHTML = `
      <div class="model-source-result-layout">
        ${modelSourceThumbnailMarkup(selectedCandidate, "result")}
        <div class="model-source-result-copy">
          <div class="model-source-line">
            <div class="model-source-title">${escapeHtml(candidate.title || candidate.remote_id)}</div>
            <span class="model-source-badge">${escapeHtml(candidate.provider_label || titleCase(candidate.provider || "provider"))}</span>
            <span class="model-source-badge kind-${badgeClassToken(candidate.provider_kind || "unknown")}">${escapeHtml(titleCase(candidate.provider_kind || "unknown"))}</span>
            <span class="model-source-badge capability-${badgeClassToken(candidate.provider_capability || "unknown")}">${escapeHtml(titleCase(candidate.provider_capability || "unknown"))}</span>
            <span class="model-source-badge">${escapeHtml(candidate.license_summary || titleCase(candidate.license_class || "unknown"))}</span>
          </div>
          <div class="model-source-meta">${escapeHtml(metaParts.join(" · "))}</div>
        </div>
      </div>
    `;
    const copy = result.querySelector(".model-source-result-copy");
    const actions = document.createElement("div");
    actions.className = "model-source-actions";
    const fetchButton = document.createElement("button");
    fetchButton.type = "button";
    fetchButton.className = "secondary";
    fetchButton.textContent = searchOnly
      ? "Search Only"
      : authRequired
        ? "Connect Sketchfab"
        : (rowTargeted && selectionInFlight() && !fetched ? "Fetching…" : (fetched ? "Fetched" : "Fetch"));
    fetchButton.disabled = fetchDisabled;
    if (!searchOnly) {
      fetchButton.addEventListener("click", async () => {
        try {
          if (authRequired) {
            await ensureSketchfabTokenConnected();
            return;
          }
          await fetchModelSourceCandidate(candidate);
        } catch (error) {
          setModelSelectionState("idle");
          setModelSourceLog(error.message || "Unable to fetch model.");
        }
      });
    }
    const useButton = document.createElement("button");
    useButton.type = "button";
    useButton.className = fetched && fetchedUsable && !isSelected ? "primary" : "";
    useButton.textContent = isSelected ? "Selected" : ((rowTargeted && selectionInFlight() && fetched) ? "Using Model…" : "Use Model");
    useButton.disabled = useDisabled;
    useButton.addEventListener("click", () => selectModelSourceCandidate(selectedCandidate));
    actions.append(fetchButton, useButton);
    const status = document.createElement("div");
    status.className = `model-source-status${rowStatus.tone && rowStatus.tone !== "default" ? ` ${rowStatus.tone}` : ""}`;
    status.textContent = rowStatus.text;
    copy?.append(actions, status);
    host.appendChild(result);
  }
  wireModelSourceThumbnails(host);
}

function renderBurnResults() {
  const manifest = latestBurnArtifacts();
  const video = document.getElementById("burn-video");
  const emptyState = document.getElementById("burn-empty-state");
  const approvalArtifacts = approvalApproved() ? (project?.approval || {}) : {};
  document.getElementById("burn-video-path").textContent = manifest?.output_path || approvalArtifacts.output_path || "--";
  document.getElementById("burn-master-path").textContent = manifest?.master_output_path || approvalArtifacts.master_output_path || "--";
  document.getElementById("burn-manifest-path").textContent = manifest?.manifest_path || approvalArtifacts.manifest_path || "--";
  document.getElementById("burn-poster-path").textContent = manifest?.poster_path || approvalArtifacts.poster_path || "--";
  document.getElementById("burn-still-path").textContent = manifest?.still_path || approvalArtifacts.still_path || "--";
  if (!manifest) {
    video.removeAttribute("src");
    video.removeAttribute("poster");
    video.load();
    delete video.dataset.relativePath;
    delete video.dataset.posterPath;
    video.hidden = true;
    emptyState.hidden = false;
    emptyState.textContent = "Burn a video to preview the approved export here.";
    return;
  }
  const videoRel = relativeProjectPath(manifest, manifest.output_path);
  const posterRel = relativeProjectPath(manifest, manifest.poster_path);
  if (videoRel) {
    if (video.dataset.relativePath !== videoRel) {
      video.src = `/project-file?path=${encodeURIComponent(videoRel)}`;
      video.dataset.relativePath = videoRel;
    }
    if (posterRel) {
      if (video.dataset.posterPath !== posterRel) {
        video.poster = `/project-file?path=${encodeURIComponent(posterRel)}`;
        video.dataset.posterPath = posterRel;
      }
    } else {
      video.removeAttribute("poster");
      delete video.dataset.posterPath;
    }
    video.hidden = false;
    emptyState.hidden = true;
  } else {
    video.removeAttribute("src");
    video.removeAttribute("poster");
    video.load();
    delete video.dataset.relativePath;
    delete video.dataset.posterPath;
    video.hidden = true;
    emptyState.hidden = false;
    emptyState.textContent = manifest.output_path
      ? "Latest burn saved. Preview unavailable here, but the export artifacts are listed in Latest Burn."
      : "Burn a video to preview the approved export here.";
  }
}

function syncPreviewWarning() {
  const warning = document.getElementById("preview-warning");
  if (!warning) return;
  if (!effectReady()) {
    warning.hidden = true;
    warning.textContent = "";
    return;
  }
  if (!particleViewportActive()) {
    warning.textContent = "Raw model view is static. Switch back to Particle View to scrub, snapshot, or approve the breakup.";
    warning.hidden = false;
    return;
  }
  const text = previewWarningText(project?.scene);
  warning.textContent = text;
  warning.hidden = !text;
}

function refreshStats() {
  const selected = project?.model_source || {};
  const selectedAttribution = modelAttributionText(selected);
  syncMediaViewportRatio();
  if (!approvalApproved()) {
    lastBurnManifest = null;
  }
  document.getElementById("project-title").textContent = `${project.episode_id} / ${project.motion_item_id}`;
  document.getElementById("project-meta").textContent = `${activePresetLabel()} · ${project.motion_contract.width}x${project.motion_contract.height} · ${project.motion_contract.frames} frames`;
  document.getElementById("approval-stat").textContent = approvalApproved() ? "Approved" : "Draft";
  document.getElementById("seed-stat").textContent = String(project.scene.seed);
  document.getElementById("backend-stat").textContent = project.scene.volume_backend === "model_source_spike" ? "Model" : "Shell";
  document.getElementById("preset-stat").textContent = activePresetLabel();
  document.getElementById("selected-model-title").textContent = selected.title || "No model loaded";
  document.getElementById("selected-model-provider").textContent = selected.provider_label || titleCase(selected.provider || "--");
  document.getElementById("selected-model-license").textContent = selected.license_summary || titleCase(selected.license_class || "--");
  document.getElementById("model-selection-title").textContent = selected.title || "No model selected";
  document.getElementById("model-selection-provider").textContent = selected.provider_label || titleCase(selected.provider || "--");
  document.getElementById("model-selection-license").textContent = selected.license_summary || titleCase(selected.license_class || "--");
  const authorNode = document.getElementById("model-selection-author");
  const attributionNode = document.getElementById("model-selection-attribution");
  if (authorNode) {
    authorNode.textContent = selected.author_name || "--";
  }
  if (attributionNode) {
    attributionNode.textContent = selectedAttribution || "--";
  }
  document.getElementById("model-next-step").textContent = selectedModelActive()
    ? "Model selected. Move to the Effect step to author particle behavior."
    : "Search for a subject model or upload a local mesh to unlock the Effect step.";
  document.getElementById("burn-status").textContent = approvalApproved() ? "Approved" : "Draft";
  document.getElementById("burn-snapshot").textContent = project.approval?.snapshot_id || "--";
  document.getElementById("burn-contract").textContent = `${project.motion_contract.frames}f · ${project.motion_contract.fps}fps · ${project.motion_contract.width}x${project.motion_contract.height}`;
  const approvalPill = document.getElementById("approval-pill");
  approvalPill.textContent = approvalApproved() ? "Approved" : "Draft";
  approvalPill.className = `status-pill ${approvalApproved() ? "approved" : "draft"}`;
  document.getElementById("preview-progress-output").textContent = formatNumber(previewProgress);
  document.getElementById("preset-family").disabled = !effectReady();
  document.getElementById("save-preset-button").disabled = !effectReady();
  document.getElementById("reset-camera-button").disabled = !effectReady();
  document.getElementById("burn-video-button").disabled = !burnReady();
  renderPresetOptions();
  renderControlSectionHeaders();
  renderSnapshotList();
  renderModelSourcePanel();
  renderBurnResults();
  updateWorkflowState();
  syncViewportTabs();
  syncViewportControls();
  syncPreviewWarning();
  setAutosaveStatus(effectReady() ? "All changes autosave." : "Load a 3D model to unlock autosave.");
}

async function reloadEffectScene() {
  if (!effectReady()) {
    effectViewer?.clear();
    setPreviewLog("Load a 3D model before authoring the effect.");
    return;
  }
  setPreviewLog("Rebuilding particle cloud…");
  const payload = await fetchJson("/api/effect-scene");
  if (!effectViewer) {
    effectViewer = new EffectViewer(document.getElementById("effect-viewer"));
  }
  effectViewer.applyPayload(payload);
  effectViewer.setViewportMode(currentViewportTab);
  effectViewer.setProgress(previewProgress);
  setPreviewLog(`Viewer ${formatNumber(previewProgress)}`);
}

function setPreviewProgress(progress, options = {}) {
  previewProgress = clamp(Number(progress), 0, 1);
  document.getElementById("preview-progress").value = String(previewProgress);
  document.getElementById("preview-progress-output").textContent = formatNumber(previewProgress);
  effectViewer?.setProgress(previewProgress);
  if (!options.fromAutoplay) {
    effectViewer?.requestRender();
  }
}

async function captureEffectViewport(progress = previewProgress) {
  if (!effectReady()) {
    throw new Error("Load a 3D model before capturing the effect viewport.");
  }
  return withViewportTab("particle", async () => {
    setActiveTab("effect");
    if (!effectViewer) {
      await reloadEffectScene();
    }
    const previousPlaybackState = previewPlaybackState;
    effectViewer?.beginScrub();
    setPreviewProgress(progress);
    await nextAnimationFrame();
    await nextAnimationFrame();
    const capture = {
      progress: previewProgress,
      data_url: await effectViewer.captureDataUrl(previewProgress),
      scene: structuredClone(project.scene),
    };
    effectViewer?.endScrub();
    setPreviewPlaybackState(previousPlaybackState);
    return capture;
  });
}

async function exportEffectFrame(options = {}) {
  return withViewportTab("particle", async () => {
    const progress = clamp(Number(options.progress ?? previewProgress), 0, 1);
    const payload = await fetchJson("/api/effect-scene");
    if (!effectViewer) {
      effectViewer = new EffectViewer(document.getElementById("effect-viewer"));
    }
    effectViewer.applyPayload(payload);
    effectViewer.setViewportMode("particle");
    return {
      progress,
      data_url: await effectViewer.captureDataUrl(progress, {
        width: options.width,
        height: options.height,
        transparentBackground: options.alpha === true,
        pixelRatio: options.pixelRatio ?? 1,
      }),
      scene: structuredClone(payload.scene || project?.scene || {}),
    };
  });
}

function queueEffectPersist() {
  effectPersistQueued = true;
  setAutosaveStatus("Saving…", "saving");
  if (effectPersistInFlight) {
    return;
  }
  if (effectPersistTimer !== null) {
    return;
  }
  const now = performance.now();
  const elapsed = now - effectPersistLastStart;
  const delay = effectPersistLastStart > 0 ? Math.max(0, EFFECT_PERSIST_INTERVAL_MS - elapsed) : 0;
  effectPersistTimer = window.setTimeout(() => {
    effectPersistTimer = null;
    flushEffectPersist();
  }, delay);
}

async function persistCurrentScene(options = {}) {
  const rebuild = options.rebuild !== false;
  const payload = { scene: project.scene };
  if (selectedModelActive()) {
    payload.model_source = {
      transform: structuredClone(project?.model_source?.transform || {}),
    };
  }
  project = await postJson("/api/project", payload);
  refreshStats();
  if (rebuild && effectReady()) {
    await reloadEffectScene();
  }
  setAutosaveStatus("All changes autosave.", "saved");
  return project;
}

async function flushEffectPersist() {
  if (!effectPersistQueued || effectPersistInFlight) {
    return;
  }
  effectPersistQueued = false;
  effectPersistInFlight = true;
  effectPersistLastStart = performance.now();
  try {
    await persistCurrentScene();
  } catch (error) {
    setAutosaveStatus("Autosave failed.", "error");
    setPreviewLog(error.message || "Unable to save effect settings.");
  } finally {
    effectPersistInFlight = false;
    if (effectPersistQueued) {
      queueEffectPersist();
    }
  }
}

async function refreshSketchfabAuthStatus(options = {}) {
  try {
    sketchfabAuth = await fetchJson("/api/model-source/sketchfab/auth/status");
  } catch (error) {
    sketchfabAuth = {
      provider: "sketchfab",
      configured: false,
      connected: false,
      token_source: "none",
      display_name: "",
      username: "",
      profile_url: "",
      message: error.message || "Unable to load Sketchfab auth status.",
    };
    if (!options.silent) {
      setModelSourceLog(sketchfabAuth.message);
    }
  }
  renderModelSourcePanel();
  return sketchfabAuth;
}

function focusSketchfabTokenInput() {
  const input = document.getElementById("sketchfab-token-input");
  if (!input || input.hidden || input.disabled) {
    return false;
  }
  input.focus();
  input.select();
  return true;
}

async function connectSketchfabToken() {
  const input = document.getElementById("sketchfab-token-input");
  const token = input?.value.trim() || "";
  if (!token) {
    if (focusSketchfabTokenInput()) {
      setModelSourceLog("Paste a Sketchfab personal token before connecting.");
    } else {
      setModelSourceLog(sketchfabAuth?.message || "Sketchfab is not ready for token input.");
    }
    return false;
  }
  setModelSourceLog("Connecting Sketchfab…");
  sketchfabAuth = await postJson("/api/model-source/sketchfab/token/connect", { token });
  if (input) {
    input.value = "";
  }
  renderModelSourcePanel();
  const label = sketchfabAuth.display_name || sketchfabAuth.username || "your account";
  setModelSourceLog(sketchfabAuth?.message || `Sketchfab connected as ${label}.`);
  return Boolean(sketchfabAuth?.connected);
}

async function ensureSketchfabTokenConnected() {
  if (sketchfabConnected()) {
    return true;
  }
  if (sketchfabEnvManaged()) {
    setModelSourceLog(sketchfabAuth?.message || "Sketchfab is managed by CE_SKETCHFAB_API_TOKEN.");
    return false;
  }
  const input = document.getElementById("sketchfab-token-input");
  if (!input?.value.trim()) {
    focusSketchfabTokenInput();
    setModelSourceLog("Paste a Sketchfab personal token, then connect it to fetch this model.");
    return false;
  }
  return connectSketchfabToken();
}

async function disconnectSketchfab() {
  sketchfabAuth = await postJson("/api/model-source/sketchfab/auth/disconnect", {});
  renderModelSourcePanel();
  setModelSourceLog(sketchfabAuth?.message || "Sketchfab disconnected.");
}

async function uploadModel(file) {
  setModelSelectionTarget(null);
  setModelSourceLog(`Uploading ${file.name}…`);
  const content_base64 = await readFileAsDataUrl(file);
  project = await postJson("/api/model-source/upload", {
    filename: file.name,
    label: file.name.replace(/\.[^.]+$/, "").replace(/[_-]+/g, " "),
    content_base64,
    query: document.getElementById("model-source-query").value.trim(),
  });
  modelSourceResults = [];
  fetchedModelResults = new Map();
  await refreshForProject("effect");
  setModelSourceLog(`Loaded ${project.model_source.title || project.model_source.remote_id}`);
}

async function searchModelSources() {
  const query = document.getElementById("model-source-query").value.trim();
  setModelSelectionTarget(null);
  setModelSourceLog(`Searching ${query || "subject"}…`);
  const response = await postJson("/api/model-source/search", { query });
  modelSourceResults = response.results || [];
  modelSourceResources = response.resources || [];
  fetchedModelResults = new Map();
  for (const result of modelSourceResults) {
    result.query = response.query;
  }
  renderModelSourcePanel();
  setModelSourceLog(`${modelSourceResults.length} candidates`);
}

async function fetchModelSourceCandidate(candidate) {
  setModelSelectionTarget(modelCandidateKey(candidate));
  setModelSelectionState("fetching", [{ label: "fetching", status: "in_progress", detail: `Fetching ${candidate.title || candidate.remote_id}…` }]);
  setModelSourceLog(`Fetching ${candidate.title || candidate.remote_id}…`);
  const response = await postJson("/api/model-source/fetch", { candidate });
  const fetched = response.candidate || {};
  fetched.query = candidate.query || document.getElementById("model-source-query").value.trim();
  fetchedModelResults.set(`${fetched.provider}:${fetched.remote_id}`, fetched);
  setModelSelectionState("idle");
  setModelSelectionTarget(modelCandidateKey(fetched));
  renderModelSourcePanel();
  if (fetched.selection_eligible === false) {
    setModelSourceLog(`${fetched.title || fetched.remote_id} fetched, but cannot be selected: ${fetched.selection_error || "unsupported asset"}`);
    return;
  }
  setModelSourceLog(`Fetched ${fetched.title || fetched.remote_id}`);
}

async function selectModelSourceCandidate(candidate) {
  if (candidate?.selection_eligible === false) {
    setModelSourceLog(candidate.selection_error || "Fetched model is not eligible for selection.");
    return;
  }
  const selectionTitle = candidate.title || candidate.remote_id;
  setModelSelectionTarget(modelCandidateKey(candidate));
  setModelSelectionState("fetching", [
    { label: "fetching", status: "in_progress", detail: `Fetching ${selectionTitle}…` },
    { label: "decoding", status: "pending", detail: "Decoding compressed geometry when required." },
    { label: "normalizing", status: "pending", detail: "Normalizing mesh bounds." },
    { label: "point_cache", status: "pending", detail: "Generating model point cache." },
    { label: "effect_reload", status: "pending", detail: "Refreshing the viewer payload." },
  ]);
  setModelSourceLog(`Selecting ${selectionTitle}…`);
  try {
    const response = await postJson("/api/model-source/select", { candidate });
    project = response.project || response;
    fetchedModelResults = new Map();
    const selectionStatus = response.selection_status || { status: "selected", phases: [] };
    setModelSelectionState(selectionStatus.status || "selected", selectionStatus.phases || []);
    await refreshForProject("effect");
    logSelectionPhases(selectionStatus);
    setModelSelectionTarget(modelCandidateKey(project.model_source || candidate));
    setModelSelectionState("selected", selectionStatus.phases || []);
    setModelSourceLog(`Using ${project.model_source.title || project.model_source.remote_id}`);
  } catch (error) {
    setModelSelectionState("failed");
    setModelSourceLog(error.message || "Unable to select model.");
    throw error;
  }
}

async function clearModelSourceSelection() {
  setModelSelectionTarget(null);
  setModelSourceLog("Clearing model selection…");
  project = await postJson("/api/model-source/clear", {});
  lastBurnManifest = null;
  await refreshForProject("model");
}

async function snapshotProject() {
  const label = window.prompt("Snapshot label", "Manual snapshot");
  if (!label) return;
  setAutosaveStatus("Saving…", "saving");
  await persistCurrentScene({ rebuild: false });
  project = await postJson("/api/snapshot", { label });
  refreshStats();
  setPreviewLog(`Snapshot saved ${project.active_snapshot_id}`);
}

async function savePreset() {
  const label = window.prompt("Preset name", activePresetLabel());
  if (!label) return;
  project = await postJson("/api/preset/save", { label });
  refreshStats();
  setPreviewLog(`Saved preset ${activePresetLabel()}`);
}

async function approveLook() {
  setAutosaveStatus("Saving…", "saving");
  await persistCurrentScene({ rebuild: false });
  project = await postJson("/api/approve", {});
  lastBurnManifest = null;
  refreshStats();
  setPreviewLog(`Approved ${project.approval.snapshot_id}`);
  setActiveTab("burn");
}

async function burnVideo() {
  setBurnLog("Burning video…");
  lastBurnManifest = await postJson("/api/export-shot", {});
  project = await fetchJson("/api/project");
  refreshStats();
  renderBurnResults();
  setBurnLog(`Burned ${lastBurnManifest.output_path}`);
  setActiveTab("burn");
}

async function refreshForProject(preferredTab = "model") {
  renderControls("model-controls", effectFieldSpecs.model);
  renderControls("surface-controls", effectFieldSpecs.surface);
  renderControls("breakup-controls", effectFieldSpecs.breakup);
  renderControls("emitter-controls", effectFieldSpecs.emitter);
  renderControls("volume-controls", effectFieldSpecs.volume);
  renderControls("render-controls", effectFieldSpecs.render);
  refreshStats();
  if (effectReady()) {
    await reloadEffectScene();
    setActiveTab(preferredTab === "burn" && burnReady() ? "burn" : (preferredTab === "effect" ? "effect" : currentTab));
  } else {
    effectViewer?.clear();
    setPreviewLog("Load a 3D model before authoring the effect.");
    if (currentTab !== "model") {
      setActiveTab("model");
    }
  }
}

function wireModelDropZone() {
  const input = document.getElementById("model-upload-input");
  document.getElementById("upload-model-button").addEventListener("click", () => input.click());
  input.addEventListener("change", async (event) => {
    const file = event.target.files?.[0];
    if (file) {
      await uploadModel(file);
    }
    input.value = "";
  });
}

function wireModelResourceModal() {
  const trigger = document.getElementById("model-resource-modal-trigger");
  const closeButton = document.getElementById("model-resource-modal-close");
  const shell = document.getElementById("model-resource-modal");
  if (!trigger || !closeButton || !shell) {
    return;
  }
  syncModelResourceModalState(false);
  trigger.addEventListener("click", (event) => {
    event.preventDefault();
    openModelResourceModal(trigger);
  });
  closeButton.addEventListener("click", () => closeModelResourceModal());
  shell.addEventListener("click", (event) => {
    if (event.target instanceof Element && event.target.hasAttribute("data-model-resource-modal-dismiss")) {
      closeModelResourceModal();
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !shell.hidden) {
      event.preventDefault();
      closeModelResourceModal();
    }
  });
}

async function loadProject() {
  project = await fetchJson("/api/project");
  await refreshSketchfabAuthStatus({ silent: true });
  const presetSelect = document.getElementById("preset-family");
  presetSelect.addEventListener("change", async () => {
    try {
      setPreviewLog(`Applying ${presetSelect.options[presetSelect.selectedIndex]?.textContent || "preset"}…`);
      project = await postJson("/api/preset/apply", { preset_id: presetSelect.value });
      lastBurnManifest = null;
      await refreshForProject(currentTab === "burn" && burnReady() ? "burn" : "effect");
      setPreviewLog(`Applied ${activePresetLabel()}`);
    } catch (error) {
      setPreviewLog(error.message || "Unable to apply preset.");
    }
  });
  document.getElementById("save-preset-button").addEventListener("click", async () => {
    try {
      await savePreset();
    } catch (error) {
      setPreviewLog(error.message || "Unable to save preset.");
    }
  });
  renderControls("model-controls", effectFieldSpecs.model);
  renderControls("surface-controls", effectFieldSpecs.surface);
  renderControls("breakup-controls", effectFieldSpecs.breakup);
  renderControls("emitter-controls", effectFieldSpecs.emitter);
  renderControls("volume-controls", effectFieldSpecs.volume);
  renderControls("render-controls", effectFieldSpecs.render);
  lastBurnManifest = null;
  refreshStats();
  await refreshForProject("model");
}

document.getElementById("model-source-search-button").addEventListener("click", searchModelSources);
document.getElementById("model-source-query").addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    searchModelSources();
  }
});
document.getElementById("model-source-query").addEventListener("input", () => renderModelSourceResources());
document.getElementById("sketchfab-auth-action").addEventListener("click", () => {
  if (sketchfabAuth?.connected) {
    disconnectSketchfab();
    return;
  }
  if (sketchfabEnvManaged()) {
    setModelSourceLog(sketchfabAuth?.message || "Sketchfab is managed by CE_SKETCHFAB_API_TOKEN.");
    return;
  }
  connectSketchfabToken().catch((error) => {
    setModelSourceLog(error.message || "Unable to connect Sketchfab.");
  });
});
document.getElementById("sketchfab-token-input").addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    connectSketchfabToken().catch((error) => {
      setModelSourceLog(error.message || "Unable to connect Sketchfab.");
    });
  }
});
const previewProgressInput = document.getElementById("preview-progress");
previewProgressInput.addEventListener("pointerdown", () => effectViewer?.beginScrub());
previewProgressInput.addEventListener("mousedown", () => effectViewer?.beginScrub());
previewProgressInput.addEventListener("touchstart", () => effectViewer?.beginScrub(), { passive: true });
previewProgressInput.addEventListener("input", (event) => {
  effectViewer?.beginScrub();
  setPreviewProgress(event.target.value);
});
previewProgressInput.addEventListener("change", () => effectViewer?.endScrub());
previewProgressInput.addEventListener("pointerup", () => effectViewer?.endScrub());
previewProgressInput.addEventListener("pointercancel", () => effectViewer?.endScrub());
previewProgressInput.addEventListener("keyup", (event) => {
  if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End", "PageUp", "PageDown"].includes(event.key)) {
    effectViewer?.endScrub();
  }
});
document.getElementById("preview-play-toggle").addEventListener("click", togglePreviewPlayback);
document.getElementById("snapshot-button").addEventListener("click", snapshotProject);
document.getElementById("approve-button").addEventListener("click", approveLook);
document.getElementById("burn-video-button").addEventListener("click", burnVideo);
document.getElementById("reset-camera-button").addEventListener("click", () => effectViewer?.resetCameraToFit());

for (const button of document.querySelectorAll("[data-viewport-tab]")) {
  button.addEventListener("click", () => setViewportTab(button.dataset.viewportTab));
}

for (const button of document.querySelectorAll(".workflow-step[data-tab]")) {
  button.addEventListener("click", () => setActiveTab(button.dataset.tab));
}

wireModelResourceModal();
wireModelDropZone();
syncViewportTabs();
syncViewportControls();
window.__particleWorkbench = {
  getProject: () => structuredClone(project),
  getCurrentTab: () => currentTab,
  getCurrentViewportTab: () => currentViewportTab,
  setActiveTab,
  setViewportTab,
  setPreviewProgress,
  captureEffectViewport,
  exportEffectFrame,
};

loadProject().then(() => {
  window.__particleWorkbenchAppReady = true;
}).catch((error) => {
  window.__particleWorkbenchAppReady = false;
  document.body.innerHTML = `<pre style="padding:24px;color:#ffd6d6">${String(error.message || error)}</pre>`;
});
