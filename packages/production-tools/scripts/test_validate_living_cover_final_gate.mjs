#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const validator = path.join(repoRoot, "scripts/validate_living_cover_final_gate.mjs");
const fixtureRoot = path.join(repoRoot, "tests/fixtures/living_cover_final_gate");
const player = path.join(fixtureRoot, "player.html");

function runCase(name, audioMixFile, shouldPass, expectedMessage = "", extraArgs = [], proofManifestFile = "proof_manifest.json") {
  const result = spawnSync(
    "node",
    [
      validator,
      "--proof-manifest",
      path.join(fixtureRoot, proofManifestFile),
      "--player",
      player,
      "--audio-mix",
      path.join(fixtureRoot, audioMixFile),
      ...extraArgs,
    ],
    { cwd: repoRoot, encoding: "utf8" },
  );
  const output = `${result.stdout || ""}${result.stderr || ""}`;
  if (shouldPass && result.status !== 0) {
    throw new Error(`${name} should pass but failed:\n${output}`);
  }
  if (!shouldPass && result.status === 0) {
    throw new Error(`${name} should fail but passed:\n${output}`);
  }
  if (!shouldPass && expectedMessage && !output.includes(expectedMessage)) {
    throw new Error(`${name} failed for the wrong reason. Expected ${JSON.stringify(expectedMessage)} in:\n${output}`);
  }
  console.log(`${name}: ${shouldPass ? "pass" : "expected failure"}`);
}

runCase("subtle-tail outro fixture", "audio_mix_pass.json", true);
runCase(
  "non-subtle actual-outro default fixture",
  "audio_mix_actual_outro_default_fail.json",
  false,
  "Non-subtle VO/outro policy requires human_approved_prelap_override",
);
runCase("bridge-only fixture", "audio_mix_bridge_only_fail.json", false, "Full outro must start before voice end");
runCase("outro-at-voice-end fixture", "audio_mix_outro_at_voice_end_fail.json", false, "Full outro must start before voice end");
runCase(
  "publish-readiness VO/outro evidence fixture",
  "audio_mix_pass.json",
  true,
  "",
  ["--publish-readiness", path.join(fixtureRoot, "publish_readiness_pass.json")],
);
runCase(
  "in-progress lifecycle review fixture",
  "audio_mix_pass.json",
  true,
  "",
  ["--publish-readiness", path.join(fixtureRoot, "publish_lifecycle_in_progress_pass.json")],
);
runCase(
  "in-progress lifecycle missing review.html fixture",
  "audio_mix_pass.json",
  false,
  "Missing publish-readiness review.html",
  ["--publish-readiness", path.join(fixtureRoot, "publish_lifecycle_missing_html_fail.json")],
);
runCase(
  "publish-readiness broad-only music fixture",
  "audio_mix_pass.json",
  false,
  "publish_readiness_manifest.reads missing passing vo_outro_blend_plan_read",
  ["--publish-readiness", path.join(fixtureRoot, "publish_readiness_missing_blend_fail.json")],
);
runCase(
  "missing end-screen palette contract fixture",
  "audio_mix_pass.json",
  false,
  "missing required end_screen_palette_contract",
  [],
  "proof_manifest_palette_missing_fail.json",
);
runCase(
  "stale end-screen palette backplate hash fixture",
  "audio_mix_pass.json",
  false,
  "approved backplate sha256 mismatch",
  [],
  "proof_manifest_palette_stale_fail.json",
);
runCase(
  "copied Challenger end-screen colors fixture",
  "audio_mix_pass.json",
  false,
  "fixed Challenger/default end-screen colors",
  [],
  "proof_manifest_palette_default_fail.json",
);
runCase(
  "human-approved end-screen palette override fixture",
  "audio_mix_pass.json",
  true,
  "",
  [],
  "proof_manifest_palette_override_pass.json",
);
