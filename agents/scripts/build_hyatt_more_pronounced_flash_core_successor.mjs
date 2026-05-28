#!/usr/bin/env node
import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const predecessorRoot =
  "/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt_living_cover_html_rough_proof_n6_balloon_immediate_flash_pulse_20260520T011444Z";
const roughAssemblyRoot = path.dirname(predecessorRoot);
const predecessorProfileId = "hyatt_audited_flash_fullscreen_pulse_balloon_immediate_v1";
const profileId = "hyatt_audited_flash_more_pronounced_core_v1";
const deterministicSeed = 2026052002;

const visibilityContract = {
  target: "more_pronounced",
  version: "audited_flash_local_core_visibility_v1",
  min_duration_seconds: 0.46,
  max_duration_seconds: 0.62,
  min_strength: 0.74,
  max_strength: 0.92,
  min_core_radius_px: 3.0,
  max_core_radius_px: 3.8,
  max_halo_radius_px: 26,
  local_core_visibility_threshold: 0.16,
  max_simultaneous_visible_flashes: 4,
};

function utcStamp(date = new Date()) {
  return date.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
}

const stamp = utcStamp();
const successorId = `hyatt_living_cover_html_rough_proof_n6_more_pronounced_flash_core_${stamp}`;
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

function flashIntensity(event, audioTime) {
  const dt = audioTime - event.time_seconds;
  if (dt < -0.04 || dt > event.duration_seconds) return 0;
  const normalized = Math.max(0, dt) / event.duration_seconds;
  const attack = event.attack_fraction ?? 0.11;
  const hold = event.hold_fraction ?? 0.16;
  let value;
  if (normalized < attack) value = normalized / attack;
  else if (normalized < attack + hold) value = 1;
  else value = 1 - (normalized - attack - hold) / (1 - attack - hold);
  return Math.pow(Math.max(0, Math.min(1, value)), 1.18);
}

function pulseAlphaAt(audioTime, flashes, proof, pulse) {
  const maxAlpha = Number(pulse.max_alpha || 0.07);
  const endScreenCap = Number(pulse.end_screen_cap_alpha || 0.012);
  const cap = audioTime >= proof.endScreenStart ? Math.min(maxAlpha, endScreenCap) : maxAlpha;
  const baseAlpha = Number(pulse.alpha_per_full_strength_flash || 0.052);
  let alpha = 0;
  for (const event of flashes) {
    const intensity = flashIntensity(event, audioTime);
    if (intensity <= 0.035) continue;
    const strengthScale = Math.max(0.65, Math.min(1.18, (event.strength || 0.52) / 0.54));
    alpha += intensity * baseAlpha * strengthScale;
  }
  return Math.max(0, Math.min(cap, alpha));
}

function transformFlashEvent(event, index) {
  return {
    ...event,
    original_duration_seconds: event.duration_seconds,
    original_strength: event.strength,
    original_core_radius_px: event.core_radius_px,
    original_halo_radius_px: event.halo_radius_px,
    duration_seconds: Number((0.46 + (index % 5) * 0.04).toFixed(3)),
    strength: Number((0.74 + (index % 7) * 0.03).toFixed(3)),
    halo_radius_px: 22 + (index % 5),
    radius_px: 22 + (index % 5),
    core_radius_px: Number((3.0 + (index % 5) * 0.2).toFixed(2)),
    attack_fraction: 0.11,
    hold_fraction: 0.16,
    decay_curve: "slower_visible_decay_v1",
    flash_render_model: "pronounced_person_centered_core_bounded_halo_v1",
    local_core_visibility_target: "more_pronounced",
  };
}

function replaceFlashIntensity(html) {
  const start = html.indexOf("    function flashIntensity(event, audioTime) {");
  const end = html.indexOf("\n    function fullScreenFlashPulseAlpha", start);
  if (start === -1 || end === -1) throw new Error("Unable to replace flashIntensity");
  const next = `    function flashIntensity(event, audioTime) {
      const dt = audioTime - event.time_seconds;
      if (dt < -0.04 || dt > event.duration_seconds) return 0;
      const normalized = Math.max(0, dt) / event.duration_seconds;
      const attack = event.attack_fraction ?? 0.11;
      const hold = event.hold_fraction ?? 0.16;
      let value;
      if (normalized < attack) value = normalized / attack;
      else if (normalized < attack + hold) value = 1;
      else value = 1 - ((normalized - attack - hold) / (1 - attack - hold));
      return Math.pow(Math.max(0, Math.min(1, value)), 1.18);
    }
`;
  return `${html.slice(0, start)}${next}${html.slice(end + 1)}`;
}

function replacePulseFunction(html) {
  const start = html.indexOf("    function fullScreenFlashPulseAlpha(audioTime) {");
  const end = html.indexOf("\n    function balloonProgress", start);
  if (start === -1 || end === -1) throw new Error("Unable to replace fullScreenFlashPulseAlpha");
  const next = `    function fullScreenFlashPulseAlpha(audioTime) {
      const config = ambientEffects.fullScreenFlashPulse || {};
      if (config.enabled !== true) return 0;
      const maxAlpha = Number(config.max_alpha || 0.07);
      const endScreenCap = Number(config.end_screen_cap_alpha || 0.012);
      const cap = audioTime >= proof.endScreenStart ? Math.min(maxAlpha, endScreenCap) : maxAlpha;
      const baseAlpha = Number(config.alpha_per_full_strength_flash || 0.052);
      let alpha = 0;
      for (const event of ambientEffects.cameraFlashes) {
        const intensity = flashIntensity(event, audioTime);
        if (intensity <= 0.035) continue;
        const strengthScale = Math.max(0.65, Math.min(1.18, (event.strength || 0.52) / 0.54));
        alpha += intensity * baseAlpha * strengthScale;
      }
      return Math.max(0, Math.min(cap, alpha));
    }
`;
  return `${html.slice(0, start)}${next}${html.slice(end + 1)}`;
}

function visibleFrameCount(event) {
  let count = 0;
  for (let frame = 0; frame <= Math.ceil(event.duration_seconds * 24); frame += 1) {
    const time = event.time_seconds + frame / 24;
    if (flashIntensity(event, time) >= visibilityContract.local_core_visibility_threshold) count += 1;
  }
  return count;
}

function buildVisibilityReport(proof, beforeFlashes, afterFlashes, pulse) {
  const visibleFrameCounts = afterFlashes.map(visibleFrameCount);
  let maxPulseAlpha = 0;
  let maxPulseTime = 0;
  let maxSimultaneous = 0;
  let pulseWithoutVisibleCore = 0;
  for (let time = 0; time <= proof.duration; time += 0.01) {
    const active = afterFlashes.filter((event) => flashIntensity(event, time) > 0.035);
    const pulseAlpha = pulseAlphaAt(time, afterFlashes, proof, pulse);
    if (pulseAlpha > maxPulseAlpha) {
      maxPulseAlpha = pulseAlpha;
      maxPulseTime = time;
    }
    if (active.length > maxSimultaneous) maxSimultaneous = active.length;
    if (pulseAlpha > 0 && active.length === 0) pulseWithoutVisibleCore += 1;
  }
  const afterRanges = {
    duration_min: Math.min(...afterFlashes.map((event) => event.duration_seconds)),
    duration_max: Math.max(...afterFlashes.map((event) => event.duration_seconds)),
    strength_min: Math.min(...afterFlashes.map((event) => event.strength)),
    strength_max: Math.max(...afterFlashes.map((event) => event.strength)),
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
  const representativeSamples = [0.8, 3.25, 55.9, 56.06, 56.24, 56.54, 56.72, proof.endScreenStart + 0.2].map((time) => ({
    time_seconds: Number(time.toFixed(3)),
    pulse_alpha: Number(pulseAlphaAt(time, afterFlashes, proof, pulse).toFixed(4)),
    active_flash_ids: afterFlashes.filter((event) => flashIntensity(event, time) > 0.035).map((event) => event.id),
  }));
  return {
    profile_id: profileId,
    visibility_contract: visibilityContract,
    before_ranges: beforeRanges,
    after_ranges: afterRanges,
    visible_frame_count_min: Math.min(...visibleFrameCounts),
    visible_frame_count_max: Math.max(...visibleFrameCounts),
    max_simultaneous_visible_flashes: maxSimultaneous,
    max_full_frame_pulse_alpha: Number(maxPulseAlpha.toFixed(4)),
    max_full_frame_pulse_time_seconds: Number(maxPulseTime.toFixed(3)),
    pulse_without_visible_core_samples: pulseWithoutVisibleCore,
    representative_samples: representativeSamples,
  };
}

function writeFrameStrip(report, beforeFlashes, afterFlashes) {
  const stripPath = path.join(successorRoot, "qa/more_pronounced_flash_core/flash_core_before_after_frame_strip.html");
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
      return [
        { phase: "start", offset: 0 },
        { phase: "peak", offset: event.duration_seconds * 0.14 },
        { phase: "decay", offset: event.duration_seconds * 0.72 },
      ].map((sample) => ({
        ...sample,
        event,
        time: event.time_seconds + sample.offset,
        before,
      }));
    });
  fs.writeFileSync(
    stripPath,
    `<!doctype html><html><head><meta charset="utf-8"><title>Hyatt more pronounced flash core samples</title><style>body{margin:0;background:#120d09;color:#fff2da;font:15px Arial,sans-serif;padding:24px}table{border-collapse:collapse;max-width:1180px}td,th{border:1px solid #5a3b29;padding:8px;vertical-align:top}code{color:#ffe4b8}.pass{color:#8ff0a4}</style></head><body><h1>Hyatt more pronounced flash core before/after samples</h1><p>Use the listed times for browser screenshots. Origins are unchanged; only duration, strength, and core visibility are retuned.</p><table><tr><th>event</th><th>phase</th><th>time</th><th>before</th><th>after</th></tr>${rows.map((row) => `<tr><td><code>${row.event.id}</code><br>${row.event.flash_origin_hotspot_id}</td><td>${row.phase}</td><td>${row.time.toFixed(3)}s</td><td>duration ${row.before.duration_seconds}s<br>strength ${row.before.strength}<br>core ${row.before.core_radius_px}px</td><td>duration ${row.event.duration_seconds}s<br>strength ${row.event.strength}<br>core ${row.event.core_radius_px}px<br>halo ${row.event.halo_radius_px}px</td></tr>`).join("")}</table><p class="pass">Visible-frame min: ${report.visible_frame_count_min}; max simultaneous visible flashes: ${report.max_simultaneous_visible_flashes}; max pulse alpha: ${report.max_full_frame_pulse_alpha}</p></body></html>`,
    "utf8",
  );
  return stripPath;
}

function staticQa(report, afterFlashes) {
  const qa = {
    profile_id: profileId,
    camera_flash_count: afterFlashes.length,
    balloon_rise_count: 28,
    report,
    qa_reads: {
      flash_core_visibility_read:
        report.after_ranges.strength_min >= visibilityContract.min_strength &&
        report.after_ranges.core_min >= visibilityContract.min_core_radius_px &&
        report.visible_frame_count_min >= 6
          ? "pass_more_pronounced_core_visible_for_multiple_frames"
          : "tighten_flash_core_visibility_below_target",
      flash_duration_visibility_read:
        report.after_ranges.duration_min >= visibilityContract.min_duration_seconds &&
        report.after_ranges.duration_max <= visibilityContract.max_duration_seconds
          ? "pass_0p46_to_0p62_second_flash_duration"
          : "tighten_flash_duration_outside_target",
      flash_origin_precision_preservation_read:
        afterFlashes.every((event) => event.flash_origin_class === "audited_visible_person_pixel")
          ? "pass_all_180_audited_origins_preserved"
          : "tighten_origin_class_changed",
      flash_halo_boundary_read:
        report.after_ranges.halo_max <= visibilityContract.max_halo_radius_px
          ? "pass_halo_bounded_22_to_26px"
          : "tighten_halo_exceeds_boundary",
      global_pulse_local_core_coupling_read:
        report.pulse_without_visible_core_samples === 0
          ? "pass_no_global_pulse_without_visible_local_flash_core"
          : `tighten_${report.pulse_without_visible_core_samples}_pulse_samples_without_local_core`,
      flash_not_strobe_read:
        report.max_simultaneous_visible_flashes <= visibilityContract.max_simultaneous_visible_flashes &&
        report.max_full_frame_pulse_alpha <= 0.07
          ? "pass_more_pronounced_without_strobe_or_washout"
          : "tighten_pulse_or_overlap_too_high",
    },
  };
  const qaPath = path.join(successorRoot, "qa/more_pronounced_flash_core/static_more_pronounced_flash_core_qa.json");
  writeJson(qaPath, qa);
  return { qa, qaPath };
}

function updatePlayerHtml(proof, afterFlashes) {
  let html = fs.readFileSync(path.join(successorRoot, "player.html"), "utf8");
  proof.ambientEffects = {
    ...proof.ambientEffects,
    profile_id: profileId,
    predecessor_profile_id: predecessorProfileId,
    deterministic_seed: deterministicSeed,
    cameraFlashes: afterFlashes,
    flashVisibilityContract: visibilityContract,
    originContract: {
      ...(proof.ambientEffects?.originContract || {}),
      local_core_visibility_policy: "more_pronounced_visible_core_required_before_full_frame_pulse",
    },
  };
  if (proof.audio) proof.audio = proof.audio.replace(/v=[^"&]+/, `v=more_pronounced_flash_core_${stamp}`);
  html = replaceProof(html, proof);
  html = replaceFlashIntensity(html);
  html = replacePulseFunction(html);
  html = html
    .replace(/Hyatt Regency Living Cover Rough Proof - [^<]+/, "Hyatt Regency Living Cover Rough Proof - More Pronounced Flash Core")
    .replace(/Hyatt Regency Living Cover N6 [^"]+ HTML rough proof/g, "Hyatt Regency Living Cover N6 more pronounced flash-core HTML rough proof")
    .replace(/v=[^"]+(?=" type="audio\/mpeg")/, `v=more_pronounced_flash_core_${stamp}`)
    .replace(/v=[^"]+(?=" type="audio\/wav")/, `v=more_pronounced_flash_core_${stamp}`);
  fs.writeFileSync(path.join(successorRoot, "player.html"), html, "utf8");
  return proof;
}

function writeAmbientArtifacts(predecessorAmbient, proof, afterFlashes, report, stripPath, qaPath, qa) {
  const ambientPath = path.join(successorRoot, "living_cover_ambient_effects_layer.json");
  const reportPath = path.join(successorRoot, "qa/more_pronounced_flash_core/flash_core_visibility_report.json");
  writeJson(reportPath, report);
  const ambient = {
    ...predecessorAmbient,
    packet_id: successorId,
    phase_gate: "ambient_effects_reopened",
    status: "review_ready_pending_human_more_pronounced_flash_core_keep",
    human_disposition: "pending",
    ambient_effects_process_version: "living_cover_ambient_effects_layer_more_pronounced_flash_core_v1",
    ambient_profile_id: profileId,
    predecessor_profile_id: predecessorProfileId,
    issue_reopened: "local_flash_core_too_subtle_for_full_frame_pulse",
    selected_lanes: ["camera_flashes", "full_frame_flash_pulse", "balloon_rises"],
    effect_parameters: {
      ...(predecessorAmbient.effect_parameters || {}),
      deterministic_seed: deterministicSeed,
      camera_flash_count: afterFlashes.length,
      camera_flashes: afterFlashes,
      flash_render_model: "pronounced_person_centered_core_bounded_halo_v1",
      flash_visibility_contract: visibilityContract,
    },
    debug_review_artifacts: {
      ...(predecessorAmbient.debug_review_artifacts || {}),
      flash_core_visibility_report: artifact(reportPath),
      flash_core_before_after_frame_strip: artifact(stripPath),
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
    `# Hyatt More Pronounced Flash-Core Ambient Layer

- Profile: \`${profileId}\`
- Camera flashes: ${afterFlashes.length}, with audited person-pixel origins preserved.
- Local core: retuned to ${visibilityContract.min_core_radius_px}-${visibilityContract.max_core_radius_px}px, ${visibilityContract.min_strength}-${visibilityContract.max_strength} strength, ${visibilityContract.min_duration_seconds}-${visibilityContract.max_duration_seconds}s duration.
- Full-frame pulse: unchanged cap, coupled to visible local cores only.
- Balloons: preserved from predecessor.
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
  manifest.status = "review_ready_pending_human_more_pronounced_flash_core_keep";
  manifest.human_disposition = "pending";
  manifest.may_advance_to_video_render = false;
  manifest.predecessor_packet_id = path.basename(predecessorRoot);
  manifest.issue_reopened = "local_flash_core_too_subtle_for_full_frame_pulse";
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
    more_pronounced_flash_core_static_qa: {
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
  const reason = "Local flash cores were too subtle to justify the full-frame exposure pulse.";
  for (const file of ["rough_assembly_manifest.json", "living_cover_ambient_effects_layer.json"]) {
    const filePath = path.join(predecessorRoot, file);
    if (!fs.existsSync(filePath)) continue;
    const data = readJson(filePath);
    data.status = "tighten_flash_core_too_subtle_for_global_pulse";
    data.human_disposition = "tighten_flash_core_too_subtle_for_global_pulse";
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
  const summaryPath = path.join(successorRoot, "more_pronounced_flash_core_successor_summary.json");
  writeJson(summaryPath, {
    successor_root: successorRoot,
    player_path: path.join(successorRoot, "player.html"),
    ambient_profile_id: profileId,
    predecessor_root: predecessorRoot,
    rough_manifest_path: manifestPath,
    ambient_layer_path: ambientArtifacts.ambientPath,
    static_qa_path: qaPath,
    visibility_report: report,
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
  const afterFlashes = beforeFlashes.map(transformFlashEvent);
  const pulse = proof.ambientEffects.fullScreenFlashPulse || predecessorAmbient.effect_parameters.full_screen_flash_pulse || {};
  const updatedProof = updatePlayerHtml(proof, afterFlashes);
  const report = buildVisibilityReport(updatedProof, beforeFlashes, afterFlashes, pulse);
  const stripPath = writeFrameStrip(report, beforeFlashes, afterFlashes);
  const { qa, qaPath } = staticQa(report, afterFlashes);
  const ambientArtifacts = writeAmbientArtifacts(predecessorAmbient, updatedProof, afterFlashes, report, stripPath, qaPath, qa);
  const manifestPath = writeRoughManifest(ambientArtifacts, qaPath);
  markPredecessorTighten();
  const summaryPath = writeSummary(ambientArtifacts, report, qaPath, manifestPath);
  console.log(JSON.stringify({ successorRoot, playerPath, summaryPath }, null, 2));
}

main();
