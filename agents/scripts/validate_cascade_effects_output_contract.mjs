#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  endScreenPaletteContractFailures,
  endScreenPaletteContractForManifest,
} from "./living_cover_end_screen_palette_contract.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, "..");
const DEFAULT_REGISTRY_PATH = path.join(
  REPO_ROOT,
  "references/production_contracts/cascade_effects_output_contracts.v1.json",
);
const VALID_INTENTS = new Set(["repair", "successor", "experiment"]);
const PASS_RE = /^(pass|approved|kept|not_applicable)/i;
const FORBIDDEN_REVIEW_CHROME_TEXT = [
  "Sample cue states",
  "Buttons seek",
  "Current Gate",
  "Review-intensity",
  "ambient/effects layer review-ready",
  "timeline scrubber",
];
const FORBIDDEN_LONGFORM_STYLE_TEXT = [
  "Paper Architecture",
  "paper architecture",
  "paper-architecture",
  "folded-paper",
  "foam-core",
  "gallery-badge",
  "Shorts-derived",
  "vertical-card montage",
];
const THREE_CHAPTER_FALLBACK = ["Opening", "Main episode", "Closing"];

function usage(exitCode = 2, message = "") {
  if (message) console.error(message);
  console.error(
    [
      "Usage: node scripts/validate_cascade_effects_output_contract.mjs --manifest PATH --intent repair|successor|experiment --contract-id ID [--json]",
      "       [--registry PATH] [--write-receipt PATH|auto] [--youtube-action ACTION]",
    ].join("\n"),
  );
  process.exit(exitCode);
}

function parseArgs(argv) {
  const args = {
    manifest: "",
    intent: "",
    contractId: "",
    registry: DEFAULT_REGISTRY_PATH,
    json: false,
    writeReceipt: "",
    youtubeAction: "",
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = () => {
      index += 1;
      if (index >= argv.length) usage(2, `Missing value for ${arg}`);
      return argv[index];
    };
    if (arg === "--manifest") args.manifest = next();
    else if (arg === "--intent") args.intent = next();
    else if (arg === "--contract-id") args.contractId = next();
    else if (arg === "--registry") args.registry = next();
    else if (arg === "--write-receipt") args.writeReceipt = next();
    else if (arg === "--youtube-action") args.youtubeAction = next();
    else if (arg === "--json") args.json = true;
    else if (arg === "--help" || arg === "-h") usage(0);
    else usage(2, `Unknown argument: ${arg}`);
  }
  if (!args.manifest) usage(2, "Missing --manifest");
  if (!args.intent || !VALID_INTENTS.has(args.intent)) usage(2, "Missing or invalid --intent");
  if (!args.contractId) usage(2, "Missing --contract-id");
  return args;
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJson(filePath, data) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`, "utf8");
}

function sha256(filePath) {
  const hash = createHash("sha256");
  hash.update(fs.readFileSync(filePath));
  return hash.digest("hex");
}

function utcStamp(date = new Date()) {
  return date.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
}

function readPasses(value, contract, readKey = "") {
  if (value === true) return true;
  if (typeof value !== "string") return false;
  if (value === "not_applicable") return (contract.allowed_not_applicable_reads || []).includes(readKey);
  return PASS_RE.test(value);
}

function firstString(...values) {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) return value.trim();
  }
  return "";
}

function resolveMaybeRelative(filePath, baseDir) {
  if (!filePath || typeof filePath !== "string") return "";
  return path.isAbsolute(filePath) ? filePath : path.resolve(baseDir, filePath);
}

function flattenObject(value, prefix = "") {
  if (!value || typeof value !== "object") return [];
  if (Array.isArray(value)) {
    return value.flatMap((item, index) => flattenObject(item, `${prefix}[${index}]`));
  }
  const rows = [];
  for (const [key, item] of Object.entries(value)) {
    const nextPrefix = prefix ? `${prefix}.${key}` : key;
    if (item && typeof item === "object") rows.push(...flattenObject(item, nextPrefix));
    else rows.push([nextPrefix, item]);
  }
  return rows;
}

function collectReads(manifest) {
  const merged = {};
  for (const key of ["reads", "qa_reads", "rough_assembly_reads", "review_reads"]) {
    if (manifest[key] && typeof manifest[key] === "object" && !Array.isArray(manifest[key])) {
      Object.assign(merged, manifest[key]);
    }
  }
  if (manifest.browser_qa?.reads) Object.assign(merged, manifest.browser_qa.reads);
  if (manifest.qa?.reads) Object.assign(merged, manifest.qa.reads);
  return merged;
}

function isHtmlOnlyChannelTrailerReview(contract, manifest) {
  return (
    contract?.family === "channel_trailer" &&
    manifest?.mp4_render_created === false &&
    /html_review/i.test(String(manifest?.workflow || manifest?.status || ""))
  );
}

function collectSourceHashes(manifest, manifestPath) {
  const manifestDir = path.dirname(manifestPath);
  const rows = {
    artifact_manifest_path: manifestPath,
    artifact_manifest_sha256: sha256(manifestPath),
  };
  const candidates = [
    ["source_final_render.manifest", manifest.source_final_render?.manifest_path, manifest.source_final_render?.manifest_sha256],
    ["source_final_render.mp4", manifest.source_final_render?.mp4_path, manifest.source_final_render?.mp4_sha256],
    ["predecessor.mp4", manifest.predecessor?.mp4_path, manifest.predecessor?.mp4_sha256],
    ["predecessor.manifest", manifest.predecessor?.manifest_path, manifest.predecessor?.manifest_sha256],
    ["source_audio.file", manifest.source_audio?.path, manifest.source_audio?.sha256],
    ["audio_source.file", manifest.audio_source?.path, manifest.audio_source?.sha256],
    ["replacement_audio.file", manifest.replacement_audio?.path, manifest.replacement_audio?.sha256],
    ["rendered_video_proof.manifest", manifest.rendered_video_proof?.manifest_path, ""],
    ["rendered_video_proof.mp4", manifest.rendered_video_proof?.mp4_path, manifest.rendered_video_proof?.mp4_sha256],
  ];
  for (const [label, rawPath, declaredSha] of candidates) {
    const resolved = resolveMaybeRelative(rawPath, manifestDir);
    if (!resolved) continue;
    rows[label] = {
      path: resolved,
      declared_sha256: declaredSha || "",
      actual_sha256: fs.existsSync(resolved) && fs.statSync(resolved).isFile() ? sha256(resolved) : "",
    };
  }
  return rows;
}

function addFailure(failures, id, detail) {
  failures.push({ id, detail });
}

function checkRegistry(registry, contractId, failures) {
  if (registry.schema_version !== "cascade_effects_output_contract_registry_v1") {
    addFailure(failures, "registry.schema_version", `unexpected registry schema: ${registry.schema_version || "(missing)"}`);
  }
  const contract = registry.contracts?.[contractId];
  if (!contract) addFailure(failures, "contract_id", `contract not found: ${contractId}`);
  return contract;
}

function checkContractBasics({ contract, manifest, intent, failures }) {
  if (!contract.allowed_intents?.includes(intent)) {
    addFailure(failures, "intent", `${intent} is not allowed by ${contract.contract_id}`);
  }
  if (contract.blocked_read) {
    addFailure(failures, "contract.blocked_read", contract.blocked_read);
  }
  if (contract.episode_ids) {
    const episodeId = firstString(manifest.episode_id, manifest.episodeId);
    if (!episodeId) addFailure(failures, "episode_id", "manifest lacks episode_id");
    else if (!contract.episode_ids.includes(episodeId)) {
      addFailure(failures, "episode_id", `${episodeId} is not in ${contract.contract_id}`);
    }
  }
}

function checkDeclaredProductionContract({ contract, manifest, intent, failures }) {
  const declared = manifest.production_contract || manifest.contract || {};
  if (!declared.contract_id) {
    addFailure(failures, "manifest.production_contract.contract_id", "manifest must declare production_contract.contract_id");
  } else if (declared.contract_id !== contract.contract_id) {
    addFailure(failures, "manifest.production_contract.contract_id", `${declared.contract_id} does not match ${contract.contract_id}`);
  }
  if (!declared.intent) {
    addFailure(failures, "manifest.production_contract.intent", "manifest must declare production_contract.intent");
  } else if (declared.intent !== intent) {
    addFailure(failures, "manifest.production_contract.intent", `${declared.intent} does not match ${intent}`);
  }
}

function checkAllowedDelta({ contract, manifest, intent, failures }) {
  const delta =
    manifest.allowed_delta ||
    manifest.production_contract?.allowed_delta ||
    manifest.repair_delta_contract ||
    (intent === "repair" ? contract.repair_defaults : null);
  if (intent !== "repair") return delta || null;
  if (!delta || typeof delta !== "object") {
    addFailure(failures, "allowed_delta", "repair intent requires an allowed_delta contract");
    return null;
  }
  const ranges = delta.allowed_time_ranges_seconds || delta.allowed_time_spans_seconds || [];
  if (!Array.isArray(ranges) || ranges.length === 0) {
    addFailure(failures, "allowed_delta.allowed_time_ranges_seconds", "repair must name allowed time ranges");
  } else {
    for (const [index, range] of ranges.entries()) {
      if (!Array.isArray(range) || range.length !== 2 || !range.every((value) => Number.isFinite(Number(value)))) {
        addFailure(failures, `allowed_delta.allowed_time_ranges_seconds[${index}]`, "range must be [start,end]");
      } else if (Number(range[0]) > Number(range[1])) {
        addFailure(failures, `allowed_delta.allowed_time_ranges_seconds[${index}]`, "range start must be <= end");
      }
    }
  }
  if (!Array.isArray(delta.allowed_pixel_regions || []) && !Array.isArray(delta.allowed_stream_changes || [])) {
    addFailure(failures, "allowed_delta.scope", "repair must name allowed pixel regions or stream changes");
  }
  return delta;
}

function checkSourceHashes({ sourceHashes, failures }) {
  for (const [label, value] of Object.entries(sourceHashes)) {
    if (!value || typeof value !== "object" || !value.path) continue;
    if (!fs.existsSync(value.path)) {
      addFailure(failures, `source_hashes.${label}.exists`, `missing source path: ${value.path}`);
      continue;
    }
    if (value.declared_sha256 && value.actual_sha256 && value.declared_sha256 !== value.actual_sha256) {
      addFailure(
        failures,
        `source_hashes.${label}.sha256`,
        `sha256 mismatch for ${value.path}: declared ${value.declared_sha256}, actual ${value.actual_sha256}`,
      );
    }
  }
}

function requiredReadsForIntent(contract, intent) {
  const byIntent = contract.required_passing_reads_by_intent || {};
  if (Array.isArray(byIntent[intent])) return byIntent[intent];
  return contract.required_passing_reads || [];
}

function checkReads({ contract, manifest, intent, failures }) {
  const reads = collectReads(manifest);
  const allowedTightenReads = new Map(
    (contract.allowed_tighten_reads || []).map((entry) => [entry.read, entry]),
  );
  const htmlOnlyChannelTrailer = isHtmlOnlyChannelTrailerReview(contract, manifest);
  const mediaOnlyReads = new Set(["audio_stream_copy_read", "format_read", "full_decode_read"]);
  for (const read of requiredReadsForIntent(contract, intent)) {
    if (htmlOnlyChannelTrailer && mediaOnlyReads.has(read)) continue;
    if (!readPasses(reads[read], contract, read)) {
      addFailure(failures, `reads.${read}`, `${read} must pass; found ${reads[read] || "(missing)"}`);
    }
  }
  for (const [key, value] of Object.entries(reads)) {
    if (value === "not_applicable" && !(contract.allowed_not_applicable_reads || []).includes(key)) {
      addFailure(failures, `reads.${key}`, `${key} may not be not_applicable under ${contract.contract_id}`);
    }
    if (typeof value === "string" && /^tighten/i.test(value) && allowedTightenReads.has(key)) {
      const exception = allowedTightenReads.get(key);
      const dependencies = exception.requires_passing_reads || [];
      const dependenciesPass = dependencies.every((read) => readPasses(reads[read], contract, read));
      if (!dependenciesPass) {
        addFailure(
          failures,
          `reads.${key}`,
          `${key} is tighten and allowed only when these reads pass: ${dependencies.join(", ")}`,
        );
      }
      continue;
    }
    if (typeof value === "string" && /^(tighten|reject|fail)/i.test(value)) {
      addFailure(failures, `reads.${key}`, `${key} is not passing: ${value}`);
    }
    if (
      typeof value === "string" &&
      /^blocked/i.test(value) &&
      !(contract.allowed_blocked_reads || []).includes(key)
    ) {
      addFailure(failures, `reads.${key}`, `${key} is blocked under ${contract.contract_id}: ${value}`);
    }
  }
}

function checkTemplateIds({ contract, manifest, failures }) {
  const fields = {
    rail_preset_id: manifest.rail_preset_id,
    rail_content_model_id: manifest.rail_content_model_id,
    caption_display_model: manifest.caption_display_model,
    youtube_end_screen_template_id:
      manifest.end_screen_context?.youtube_end_screen_template_id ||
      manifest.timeline?.youtube_end_screen_template_id ||
      manifest.youtube_end_screen?.template_id,
    end_screen_palette_treatment_model:
      manifest.end_screen_context?.end_screen_palette_treatment_model ||
      manifest.end_screen_context?.end_screen_timing?.palette?.palette_treatment_model ||
      manifest.end_screen_palette_contract?.target_palette?.palette_treatment_model,
  };
  for (const [key, expected] of Object.entries(contract.required_template_ids || {})) {
    if (fields[key] && fields[key] !== expected) {
      addFailure(failures, `template.${key}`, `expected ${expected}; found ${fields[key]}`);
    }
  }
}

function checkEndScreenPalette({ contract, manifest, manifestPath, failures }) {
  if (contract.family !== "longform" && contract.family !== "channel_trailer") return;
  const contractData = endScreenPaletteContractForManifest(manifest);
  if (!contractData) {
    if (contract.family === "channel_trailer") {
      addFailure(failures, "end_screen_palette_contract", "missing required end_screen_palette_contract");
    }
    return;
  }
  for (const failure of endScreenPaletteContractFailures(manifest, { manifestPath })) {
    addFailure(failures, failure.id, failure.detail);
  }
}

function checkReviewChrome({ manifest, failures }) {
  const text = JSON.stringify(manifest);
  for (const forbidden of FORBIDDEN_REVIEW_CHROME_TEXT) {
    if (text.includes(forbidden)) {
      const reads = collectReads(manifest);
      if (!readPasses(reads.forbidden_review_chrome_text_read, { allowed_not_applicable_reads: [] }, "forbidden_review_chrome_text_read")) {
        addFailure(failures, "review_chrome.forbidden_text", `forbidden review chrome text present: ${forbidden}`);
      }
    }
  }
}

function checkForbiddenStyleCarryover({ contract, manifest, failures }) {
  if (contract.family !== "longform" && contract.family !== "channel_trailer") return;
  const text = JSON.stringify(manifest);
  for (const forbidden of FORBIDDEN_LONGFORM_STYLE_TEXT) {
    if (text.includes(forbidden)) {
      addFailure(failures, "style.forbidden_legacy_carryover", `forbidden legacy style text present: ${forbidden}`);
    }
  }
}

function checkSemmelweisHighlightOverride({ contract, manifest, failures }) {
  if (contract.family !== "longform" || manifest.episode_id !== "semmelweis") return;
  const highlightQa =
    manifest.highlight_color_qa ||
    manifest.caption_context?.highlight_color_qa ||
    manifest.rail_behavior?.rolling_caption_window?.highlight_color_qa ||
    manifest.living_cover_cue_map?.highlight_color_qa ||
    {};
  const selectedHex = String(highlightQa.selected_hex || highlightQa.selectedHex || "").trim().toLowerCase();
  if (!selectedHex) return;
  if (selectedHex === "#dede35") {
    addFailure(failures, "semmelweis.highlight_override_hex", "Semmelweis #dede35 highlight override is retired; rebuild with the review-safe pale highlight treatment");
  } else if (selectedHex !== "#efef9f") {
    addFailure(failures, "semmelweis.highlight_override_hex", `Semmelweis highlight must use #efef9f; found ${selectedHex}`);
  }
  const reads = collectReads(manifest);
  const overrideRead = highlightQa.highlight_override_read || reads.highlight_override_read || "";
  if (!readPasses(overrideRead, contract, "highlight_override_read")) {
    addFailure(failures, "semmelweis.highlight_override_read", `Semmelweis highlight override read must pass; found ${overrideRead || "(missing)"}`);
  }
  const backplateRead = highlightQa.highlight_backplate_contrast_read || reads.highlight_backplate_contrast_read || "";
  if (!readPasses(backplateRead, contract, "highlight_backplate_contrast_read")) {
    addFailure(failures, "semmelweis.highlight_backplate_contrast_read", `Semmelweis highlight backplate contrast must pass; found ${backplateRead || "(missing)"}`);
  }
}

function checkChapters({ contract, manifest, failures }) {
  if (contract.family !== "longform") return;
  const metadata = manifest.youtube_metadata || manifest.metadata || {};
  const chapters = Array.isArray(metadata.chapters) ? metadata.chapters : Array.isArray(manifest.chapters) ? manifest.chapters : [];
  if (!chapters.length) return;
  const labels = chapters.map((chapter) => String(chapter.label || chapter.title || "").trim());
  if (labels.length === 3 && labels.every((label, index) => label === THREE_CHAPTER_FALLBACK[index])) {
    addFailure(failures, "chapters.three_chapter_fallback", "three-chapter fallback is not allowed when full chapter sources exist");
  }
  if (["hyatt-regency", "semmelweis", "tacoma-narrows", "piltdown-man", "titanic"].includes(manifest.episode_id) && chapters.length < 4) {
    addFailure(failures, "chapters.full_source_count", `${manifest.episode_id} requires full chapter metadata; found ${chapters.length}`);
  }
}

function runExistingValidators({ contract, manifest, manifestPath }) {
  const rows = [];
  if (contract.family === "longform") {
    const proofLike = Boolean(manifest.rail_content_model_id || manifest.proof_artifacts?.player_html_path);
    const finalAssemblyRendered = Boolean(
      manifest.mp4_render_created === true &&
        (manifest.rendered_video_proof?.mp4_path || manifest.source_final_render?.mp4_path),
    );
    const playerPath = resolveMaybeRelative(manifest.proof_artifacts?.player_html_path || "player.html", path.dirname(manifestPath));
    if (proofLike && fs.existsSync(playerPath) && !finalAssemblyRendered) {
      const result = spawnSync(
        "node",
        [path.join(REPO_ROOT, "scripts/validate_living_cover_rolling_caption_rail.mjs"), "--proof-manifest", manifestPath, "--player", playerPath, "--json"],
        { cwd: REPO_ROOT, encoding: "utf8", maxBuffer: 1024 * 1024 * 64 },
      );
      rows.push({
        id: "validate_living_cover_rolling_caption_rail",
        status: result.status === 0 ? "pass" : "fail",
        stderr: result.stderr || "",
      });
    }
  }
  return rows;
}

function computeYoutubeActionAllowed({ contract, manifest, intent, args }) {
  if (intent === "experiment") return false;
  if (!args.youtubeAction) return false;
  const allowedActions = contract.youtube_policy?.allowed_actions_after_receipt || [];
  if (!allowedActions.includes(args.youtubeAction)) return false;
  const reads = collectReads(manifest);
  const actionApprovalRead =
    manifest.production_contract?.youtube_action_approval_read ||
    manifest.production_contract_action_approval_read ||
    reads.production_contract_youtube_action_approval_read ||
    reads[`${args.youtubeAction}_approval_read`] ||
    "";
  return readPasses(actionApprovalRead, contract, "youtube_action_approval_read");
}

function receiptPathFor(args, manifestPath) {
  if (!args.writeReceipt) return "";
  if (args.writeReceipt !== "auto") return path.resolve(args.writeReceipt);
  return path.join(path.dirname(manifestPath), "production_contract_receipts", `contract_receipt_${utcStamp()}.json`);
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const manifestPath = path.resolve(args.manifest);
  const registryPath = path.resolve(args.registry);
  const failures = [];
  if (!fs.existsSync(manifestPath)) usage(2, `Missing manifest: ${manifestPath}`);
  if (!fs.existsSync(registryPath)) usage(2, `Missing registry: ${registryPath}`);

  const registry = readJson(registryPath);
  const manifest = readJson(manifestPath);
  const contract = checkRegistry(registry, args.contractId, failures);
  const sourceHashes = collectSourceHashes(manifest, manifestPath);
  let allowedDelta = null;
  let existingValidators = [];
  let youtubeActionAllowed = false;

  if (contract) {
    checkContractBasics({ contract, manifest, intent: args.intent, failures });
    checkDeclaredProductionContract({ contract, manifest, intent: args.intent, failures });
    allowedDelta = checkAllowedDelta({ contract, manifest, intent: args.intent, failures });
    checkSourceHashes({ sourceHashes, failures });
    checkReads({ contract, manifest, intent: args.intent, failures });
    checkTemplateIds({ contract, manifest, failures });
    checkEndScreenPalette({ contract, manifest, manifestPath, failures });
    checkReviewChrome({ manifest, failures });
    checkForbiddenStyleCarryover({ contract, manifest, failures });
    checkSemmelweisHighlightOverride({ contract, manifest, failures });
    checkChapters({ contract, manifest, failures });
    existingValidators = runExistingValidators({ contract, manifest, manifestPath });
    for (const validator of existingValidators) {
      if (validator.status !== "pass") {
        addFailure(failures, `existing_validator.${validator.id}`, validator.stderr || "existing validator failed");
      }
    }
    youtubeActionAllowed = computeYoutubeActionAllowed({ contract, manifest, intent: args.intent, args });
  }

  const ok = failures.length === 0;
  const reads = {
    contract_read: ok ? "pass_contract_loaded_and_required_reads_passed" : "reject_contract_validation_failed",
    delta_read:
      args.intent === "repair"
        ? ok
          ? "pass_repair_allowed_delta_contract_present"
          : "reject_repair_allowed_delta_contract_failed"
        : "pass_no_repair_delta_required_for_intent",
    style_read: ok ? "pass_style_contract_reads_passed" : "reject_style_contract_reads_failed",
    media_read: ok ? "pass_source_hashes_and_media_reads_valid" : "reject_source_hash_or_media_read_failed",
    youtube_action_allowed_read: youtubeActionAllowed ? "pass_contract_allows_requested_youtube_action" : "blocked_contract_does_not_allow_youtube_action",
  };
  const receipt = {
    receipt_type: "cascade_effects_output_contract_validation",
    schema_version: "cascade_effects_output_contract_receipt_v1",
    created_at: new Date().toISOString(),
    ok,
    artifact_manifest_path: manifestPath,
    artifact_manifest_sha256: sourceHashes.artifact_manifest_sha256,
    contract_registry_path: registryPath,
    contract_id: args.contractId,
    family: contract?.family || "unknown",
    intent: args.intent,
    source_hashes: sourceHashes,
    allowed_delta: allowedDelta,
    reads,
    existing_validators: existingValidators,
    failures,
    youtube_action_requested: args.youtubeAction || "",
    youtube_action_allowed: youtubeActionAllowed,
  };
  const outPath = receiptPathFor(args, manifestPath);
  if (outPath) {
    writeJson(outPath, receipt);
    receipt.receipt_path = outPath;
  }
  if (args.json) {
    console.log(JSON.stringify(receipt, null, 2));
  } else if (ok) {
    console.log(`PASS ${args.contractId} ${args.intent}${outPath ? ` receipt=${outPath}` : ""}`);
  } else {
    console.error(`FAIL ${args.contractId} ${args.intent}`);
    for (const failure of failures) console.error(`- ${failure.id}: ${failure.detail}`);
  }
  process.exit(ok ? 0 : 1);
}

main();
