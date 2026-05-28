#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import {
  endScreenPaletteContractFailures,
  endScreenPaletteContractForManifest,
} from "./living_cover_end_screen_palette_contract.mjs";

const DEFAULT_ROOT = "/Users/mike/Episodes_CascadeEffects";
const SKIP_DIRS = new Set([
  ".git",
  "node_modules",
  "archive",
  "archives",
  "experiments",
  "legacy",
  "retired",
  "midjourney",
  "proof_stills",
  "test-results",
]);

function parseArgs(argv) {
  const args = {
    root: DEFAULT_ROOT,
    json: false,
    failOnFindings: false,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--root") args.root = argv[++index] || "";
    else if (arg === "--json") args.json = true;
    else if (arg === "--fail-on-findings") args.failOnFindings = true;
    else if (arg === "--help" || arg === "-h") usage(0);
    else usage(2, `Unknown argument: ${arg}`);
  }
  if (!args.root) usage(2, "Missing --root");
  return args;
}

function usage(exitCode, message = "") {
  if (message) console.error(message);
  console.error(
    "Usage: node scripts/audit_living_cover_end_screen_palette_contracts.mjs [--root PATH] [--json] [--fail-on-findings]",
  );
  process.exit(exitCode);
}

function readJsonIfPossible(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch {
    return null;
  }
}

function isRelevantManifest(filePath) {
  const name = path.basename(filePath);
  return (
    name === "rough_assembly_manifest.json" ||
    name === "final_render_manifest.json" ||
    name === "publish_readiness_manifest.json" ||
    /publish_readiness.*\.json$/i.test(name)
  );
}

function isLivingCoverManifest(manifest) {
  return Boolean(
    manifest?.living_cover_system_version ||
      manifest?.rail_preset_id === "fixed_16x9_right_rail_v1" ||
      manifest?.end_screen_context ||
      manifest?.youtube_end_screen,
  );
}

function manifestGateFor(filePath, manifest) {
  const name = path.basename(filePath);
  if (name === "rough_assembly_manifest.json" || /rough/i.test(String(manifest?.phase_gate || manifest?.gate || ""))) {
    return "rough_assembly";
  }
  if (name === "final_render_manifest.json" || /final/i.test(String(manifest?.phase_gate || manifest?.gate || ""))) {
    return "final_assembly";
  }
  if (/publish_readiness/i.test(name) || /publish/i.test(String(manifest?.gate || manifest?.lifecycle_stage || ""))) {
    return "publish_readiness";
  }
  return "unknown";
}

function* walk(root) {
  const entries = fs.readdirSync(root, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(root, entry.name);
    if (entry.isDirectory()) {
      if (SKIP_DIRS.has(entry.name.toLowerCase())) continue;
      yield* walk(fullPath);
    } else if (entry.isFile() && isRelevantManifest(fullPath)) {
      yield fullPath;
    }
  }
}

function auditManifest(filePath) {
  const manifest = readJsonIfPossible(filePath);
  if (!manifest || !isLivingCoverManifest(manifest)) return null;
  const failures = endScreenPaletteContractFailures(manifest, {
    manifestPath: filePath,
    requireExistingBackplate: false,
  });
  const contract = endScreenPaletteContractForManifest(manifest);
  return {
    path: filePath,
    episode_id: manifest.episode_id || manifest.review_id || path.basename(path.dirname(filePath)),
    gate: manifestGateFor(filePath, manifest),
    status: failures.length ? "finding" : "pass",
    contract_status: contract?.status || "missing",
    palette_source: contract?.palette_source || "missing",
    findings: failures,
  };
}

function summarize(findings) {
  const byGate = {};
  for (const finding of findings) {
    byGate[finding.gate] ||= { total: 0, findings: 0 };
    byGate[finding.gate].total += 1;
    if (finding.status !== "pass") byGate[finding.gate].findings += 1;
  }
  return {
    scanned_manifests: findings.length,
    manifests_with_findings: findings.filter((finding) => finding.status !== "pass").length,
    by_gate: byGate,
  };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const root = path.resolve(args.root);
  if (!fs.existsSync(root) || !fs.statSync(root).isDirectory()) {
    throw new Error(`Audit root is not a directory: ${root}`);
  }
  const records = [];
  for (const filePath of walk(root)) {
    const record = auditManifest(filePath);
    if (record) records.push(record);
  }
  const report = {
    audit_id: "living_cover_end_screen_palette_contract_read_only_audit_v1",
    root,
    created_utc: new Date().toISOString(),
    summary: summarize(records),
    records,
  };
  if (args.json) {
    console.log(JSON.stringify(report, null, 2));
  } else {
    console.log(`Living Cover end-screen palette contract audit: ${root}`);
    console.log(
      `Scanned ${report.summary.scanned_manifests} manifests; ${report.summary.manifests_with_findings} have findings.`,
    );
    for (const record of records.filter((item) => item.status !== "pass")) {
      console.log(`- ${record.gate} ${record.episode_id}: ${record.path}`);
      for (const finding of record.findings) console.log(`  - ${finding.id}: ${finding.detail}`);
    }
  }
  if (args.failOnFindings && report.summary.manifests_with_findings > 0) process.exit(1);
}

main();
