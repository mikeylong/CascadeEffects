#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PRODUCTION_TOOLS_ROOT = path.resolve(__dirname, "..");
const VALIDATOR = path.join(PRODUCTION_TOOLS_ROOT, "scripts/validate_cascade_effects_output_contract.mjs");
const FIXTURES = path.join(PRODUCTION_TOOLS_ROOT, "tests/fixtures/cascade_effects_output_contract");

function runValidator(args) {
  const result = spawnSync("node", [VALIDATOR, ...args, "--json"], {
    cwd: PRODUCTION_TOOLS_ROOT,
    encoding: "utf8",
    maxBuffer: 1024 * 1024 * 16,
  });
  let payload = {};
  try {
    payload = JSON.parse(result.stdout || "{}");
  } catch (error) {
    throw new Error(`Validator did not emit JSON.\nSTDOUT:\n${result.stdout}\nSTDERR:\n${result.stderr}\n${error}`);
  }
  return { result, payload };
}

function fixture(name) {
  return path.join(FIXTURES, name);
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function expectPass(name, args, inspect = () => {}) {
  const { result, payload } = runValidator(args);
  assert(result.status === 0, `${name} expected pass.\n${result.stderr}\n${JSON.stringify(payload.failures, null, 2)}`);
  assert(payload.ok === true, `${name} receipt ok should be true`);
  assert(payload.schema_version === "cascade_effects_output_contract_receipt_v1", `${name} receipt schema mismatch`);
  inspect(payload);
}

function expectFail(name, args, expectedFailureId) {
  const { result, payload } = runValidator(args);
  assert(result.status !== 0, `${name} expected failure`);
  assert(payload.ok === false, `${name} receipt ok should be false`);
  const ids = (payload.failures || []).map((failure) => failure.id);
  assert(ids.includes(expectedFailureId), `${name} missing failure ${expectedFailureId}; got ${ids.join(", ")}`);
}

const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "ce-contract-test-"));
const receiptPath = path.join(tempDir, "receipt.json");

expectPass("longform semmelweis successor", [
  "--manifest",
  fixture("longform_semmelweis_successor_pass.json"),
  "--intent",
  "successor",
  "--contract-id",
  "first-eight-longform-v1",
  "--write-receipt",
  receiptPath,
], (payload) => {
  assert(fs.existsSync(receiptPath), "receipt file should be written");
  assert(payload.youtube_action_allowed === false, "youtube action should be locked by default");
});

expectPass("longform youtube action approval", [
  "--manifest",
  fixture("longform_semmelweis_youtube_action_allowed.json"),
  "--intent",
  "successor",
  "--contract-id",
  "first-eight-longform-v1",
  "--youtube-action",
  "unlisted_review_upload",
], (payload) => {
  assert(payload.youtube_action_allowed === true, "explicit approved upload action should be allowed");
});

expectPass("channel trailer repair", [
  "--manifest",
  fixture("channel_trailer_repair_pass.json"),
  "--intent",
  "repair",
  "--contract-id",
  "channel-trailer-v1",
]);

expectPass("channel trailer successor", [
  "--manifest",
  fixture("channel_trailer_successor_pass.json"),
  "--intent",
  "successor",
  "--contract-id",
  "channel-trailer-v1",
]);

expectPass("channel trailer unlisted upload action approval", [
  "--manifest",
  fixture("channel_trailer_unlisted_upload_action_allowed.json"),
  "--intent",
  "successor",
  "--contract-id",
  "channel-trailer-v1",
  "--youtube-action",
  "unlisted_review_upload",
], (payload) => {
  assert(payload.youtube_action_requested === "unlisted_review_upload", "channel trailer upload action should be recorded");
  assert(payload.youtube_action_allowed === true, "channel trailer unlisted review upload should be allowed after explicit approval");
});

expectPass("channel trailer unlisted metadata action approval", [
  "--manifest",
  fixture("channel_trailer_unlisted_upload_action_allowed.json"),
  "--intent",
  "successor",
  "--contract-id",
  "channel-trailer-v1",
  "--youtube-action",
  "unlisted_review_metadata_update",
], (payload) => {
  assert(payload.youtube_action_requested === "unlisted_review_metadata_update", "channel trailer metadata action should be recorded");
  assert(payload.youtube_action_allowed === true, "channel trailer unlisted metadata update should be allowed after explicit approval");
});

expectPass("channel trailer replacement remains blocked", [
  "--manifest",
  fixture("channel_trailer_unlisted_upload_action_allowed.json"),
  "--intent",
  "successor",
  "--contract-id",
  "channel-trailer-v1",
  "--youtube-action",
  "channel_trailer_replacement",
], (payload) => {
  assert(payload.youtube_action_requested === "channel_trailer_replacement", "channel trailer replacement action should be recorded");
  assert(payload.youtube_action_allowed === false, "channel trailer replacement should stay blocked by contract");
});

expectFail("repair missing delta", [
  "--manifest",
  fixture("longform_repair_missing_delta_fail.json"),
  "--intent",
  "repair",
  "--contract-id",
  "first-eight-longform-v1",
], "allowed_delta");

expectFail("forbidden review chrome", [
  "--manifest",
  fixture("longform_forbidden_review_chrome_fail.json"),
  "--intent",
  "successor",
  "--contract-id",
  "first-eight-longform-v1",
], "review_chrome.forbidden_text");

expectFail("three chapter fallback", [
  "--manifest",
  fixture("longform_three_chapter_fallback_fail.json"),
  "--intent",
  "successor",
  "--contract-id",
  "first-eight-longform-v1",
], "chapters.three_chapter_fallback");

expectFail("paper architecture carryover", [
  "--manifest",
  fixture("longform_paper_architecture_fail.json"),
  "--intent",
  "successor",
  "--contract-id",
  "first-eight-longform-v1",
], "style.forbidden_legacy_carryover");

expectFail("missing production contract", [
  "--manifest",
  fixture("longform_missing_contract_fail.json"),
  "--intent",
  "successor",
  "--contract-id",
  "first-eight-longform-v1",
], "manifest.production_contract.contract_id");

console.log("PASS validate_cascade_effects_output_contract fixtures");
