#!/usr/bin/env node
import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import { dirname, isAbsolute, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, "..");
const baselineDir = join(
  repoRoot,
  "references/skills/long_form_video_production_v1/references/episode_visual_system_baselines"
);
const indexPath = join(baselineDir, "index.json");

const expectedEpisodeIds = new Set([
  "737-max",
  "challenger",
  "hyatt-regency",
  "piltdown-man",
  "semmelweis",
  "therac-25",
  "titanic",
  "tacoma-narrows",
]);

const requiredFields = [
  "episode_id",
  "baseline_status",
  "active_source_art_path",
  "active_source_art_sha256",
  "source_manifest_path",
  "source_manifest_sha256",
  "style_lane",
  "required_reads",
  "ambient_lane",
  "end_screen_template",
  "known_superseded_artifacts",
  "current_blockers",
];

const errors = [];

function addError(message) {
  errors.push(message);
}

function sha256File(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function requireExistingFile(path, label) {
  if (!path || typeof path !== "string") {
    addError(`${label} is missing or not a string`);
    return false;
  }
  if (!isAbsolute(path)) {
    addError(`${label} must be absolute: ${path}`);
    return false;
  }
  if (!existsSync(path)) {
    addError(`${label} does not exist: ${path}`);
    return false;
  }
  return true;
}

function requireNonEmptyString(entry, field) {
  if (typeof entry[field] !== "string" || entry[field].trim() === "") {
    addError(`${entry.episode_id || "unknown"} ${field} must be a non-empty string`);
  }
}

function requireStringArray(entry, field, { allowEmpty = false } = {}) {
  if (!Array.isArray(entry[field])) {
    addError(`${entry.episode_id || "unknown"} ${field} must be an array`);
    return;
  }
  if (!allowEmpty && entry[field].length === 0) {
    addError(`${entry.episode_id || "unknown"} ${field} must not be empty`);
    return;
  }
  for (const [index, value] of entry[field].entries()) {
    if (typeof value !== "string" || value.trim() === "") {
      addError(`${entry.episode_id || "unknown"} ${field}[${index}] must be a non-empty string`);
    }
  }
}

function assertHashMatches(path, expectedHash, label) {
  if (!requireExistingFile(path, label)) {
    return;
  }
  if (!/^[a-f0-9]{64}$/.test(expectedHash || "")) {
    addError(`${label} SHA-256 is not a valid lowercase hex digest: ${expectedHash}`);
    return;
  }
  const actualHash = sha256File(path);
  if (actualHash !== expectedHash) {
    addError(`${label} SHA-256 mismatch for ${path}: expected ${expectedHash}, got ${actualHash}`);
  }
}

function assertTomlPointer(entry) {
  if (!requireExistingFile(entry.episode_toml_path, `${entry.episode_id} episode_toml_path`)) {
    return;
  }
  const toml = readFileSync(entry.episode_toml_path, "utf8");
  const pointerChecks = [
    ["visual_system_baseline_path", entry.baseline_doc_path],
    ["visual_system_baseline_status", entry.baseline_status],
    ["visual_system_baseline_updated_at", "2026-05-19"],
  ];

  for (const [field, expected] of pointerChecks) {
    const pattern = new RegExp(`^${field} = "${escapeRegExp(expected)}"$`, "m");
    if (!pattern.test(toml)) {
      addError(`${entry.episode_id} TOML missing ${field} = "${expected}"`);
    }
  }
}

if (!existsSync(indexPath)) {
  throw new Error(`Missing baseline index: ${indexPath}`);
}

let index;
try {
  index = JSON.parse(readFileSync(indexPath, "utf8"));
} catch (error) {
  throw new Error(`Failed to parse ${indexPath}: ${error.message}`);
}

if (index.schema_version !== "living_cover_episode_visual_system_baselines_v1") {
  addError(`Unexpected schema_version: ${index.schema_version}`);
}

if (!Array.isArray(index.baselines)) {
  addError("index.baselines must be an array");
} else {
  const seenEpisodeIds = new Set();

  for (const entry of index.baselines) {
    for (const field of requiredFields) {
      if (!(field in entry)) {
        addError(`${entry.episode_id || "unknown"} missing required field ${field}`);
      }
    }

    if (!expectedEpisodeIds.has(entry.episode_id)) {
      addError(`Unexpected episode_id: ${entry.episode_id}`);
    }
    if (seenEpisodeIds.has(entry.episode_id)) {
      addError(`Duplicate episode_id: ${entry.episode_id}`);
    }
    seenEpisodeIds.add(entry.episode_id);

    for (const field of [
      "episode_id",
      "baseline_status",
      "active_source_art_path",
      "active_source_art_sha256",
      "source_manifest_path",
      "source_manifest_sha256",
      "style_lane",
      "ambient_lane",
      "end_screen_template",
    ]) {
      requireNonEmptyString(entry, field);
    }

    requireStringArray(entry, "required_reads");
    requireStringArray(entry, "current_blockers");

    if (!Array.isArray(entry.known_superseded_artifacts)) {
      addError(`${entry.episode_id} known_superseded_artifacts must be an array`);
    } else {
      for (const [index, artifact] of entry.known_superseded_artifacts.entries()) {
        if (artifact.active !== false) {
          addError(`${entry.episode_id} known_superseded_artifacts[${index}] must have active: false`);
        }
        if (artifact.path) {
          if (artifact.path === entry.active_source_art_path || artifact.path === entry.source_manifest_path) {
            addError(`${entry.episode_id} superseded artifact path is marked active elsewhere: ${artifact.path}`);
          }
          if (!existsSync(artifact.path)) {
            addError(`${entry.episode_id} superseded artifact path does not exist: ${artifact.path}`);
          }
        }
      }
    }

    if (/paper[\s_-]*architecture/i.test(entry.style_lane)) {
      addError(`${entry.episode_id} uses Paper Architecture as active style_lane: ${entry.style_lane}`);
    }

    if (!entry.required_reads.includes("paper_architecture_visual_style_read")) {
      addError(`${entry.episode_id} must include paper_architecture_visual_style_read in required_reads`);
    }

    assertHashMatches(
      entry.active_source_art_path,
      entry.active_source_art_sha256,
      `${entry.episode_id} active_source_art_path`
    );
    assertHashMatches(
      entry.source_manifest_path,
      entry.source_manifest_sha256,
      `${entry.episode_id} source_manifest_path`
    );

    if (requireExistingFile(entry.baseline_doc_path, `${entry.episode_id} baseline_doc_path`)) {
      const doc = readFileSync(entry.baseline_doc_path, "utf8");
      for (const expected of [
        `Episode ID: \`${entry.episode_id}\``,
        `Baseline status: \`${entry.baseline_status}\``,
        entry.active_source_art_sha256,
        entry.source_manifest_sha256,
      ]) {
        if (!doc.includes(expected)) {
          addError(`${entry.episode_id} baseline doc missing expected text: ${expected}`);
        }
      }
    }

    assertTomlPointer(entry);
  }

  for (const episodeId of expectedEpisodeIds) {
    if (!seenEpisodeIds.has(episodeId)) {
      addError(`Missing baseline entry for ${episodeId}`);
    }
  }
}

if (errors.length > 0) {
  console.error("Living Cover episode visual baseline validation failed:");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(`Validated ${index.baselines.length} Living Cover episode visual baselines.`);
