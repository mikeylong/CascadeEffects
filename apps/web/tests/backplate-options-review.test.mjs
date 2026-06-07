import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import crypto from 'node:crypto';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import test from 'node:test';

const ROOT = path.resolve(import.meta.dirname, '..');
const SCRIPT = path.join(ROOT, 'scripts', 'backplate-options-review.mjs');
const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

function runBackplateCli(args, options = {}) {
  const output = execFileSync('node', [SCRIPT, ...args], {
    cwd: ROOT,
    encoding: 'utf8',
    ...options,
  });
  return JSON.parse(output);
}

function sha256(bytes) {
  return crypto.createHash('sha256').update(bytes).digest('hex');
}

function writePng(root, relPath, label) {
  const bytes = Buffer.concat([PNG_SIGNATURE, Buffer.from(label)]);
  const filePath = path.join(root, relPath);
  mkdirSync(path.dirname(filePath), { recursive: true });
  writeFileSync(filePath, bytes);
  return { relPath, sha256: sha256(bytes), bytes: bytes.length };
}

function createPacket(overrides = {}) {
  const packet = mkdtempSync(path.join(tmpdir(), 'cascade-backplate-review-'));
  const slugs = [
    ['ep09-apollo-13', 'Apollo 13'],
    ['ep10-citicorp-center', 'Citicorp Center'],
    ['ep11-air-france-447', 'Air France 447'],
    ['ep12-tenerife', 'Tenerife'],
    ['ep13-uss-thresher', 'USS Thresher'],
    ['ep14-hindenburg', 'Hindenburg'],
    ['ep15-texas-city-1947', 'Texas City 1947'],
    ['ep16-aberfan', 'Aberfan'],
  ];

  const episodes = slugs.map(([episodeId, title], episodeIndex) => {
    const contact = writePng(packet, `assets/${episodeId}/contact.png`, `${episodeId}-contact`);
    const options = [];

    if (episodeIndex === 0) {
      for (const id of ['existing-1', 'existing-2']) {
        const image = writePng(packet, `assets/${episodeId}/${id}.png`, `${episodeId}-${id}`);
        options.push({
          id,
          kind: 'existing',
          path: image.relPath,
          sha256: image.sha256,
          status: 'existing_review_candidate_provenance_only_not_keep',
        });
      }
    }

    for (const id of ['option-a', 'option-b', 'option-c']) {
      const image = writePng(packet, `assets/${episodeId}/${id}.png`, `${episodeId}-${id}`);
      options.push({
        id,
        kind: 'new',
        path: image.relPath,
        sha256: image.sha256,
        status: 'review_candidate_not_keep',
        prompt_path: `prompts/${episodeId}-${id}.md`,
        prompt_sha256: sha256(Buffer.from(`${episodeId}-${id}-prompt`)),
      });
    }

    return {
      episode_id: episodeId,
      title,
      status: 'review_ready_blocked_options_only',
      may_advance: Boolean(overrides.episodeMayAdvance && episodeIndex === 0),
      generated_option_count: 3,
      existing_option_count: episodeIndex === 0 ? 2 : 0,
      manifest_path: `manifests/${episodeId}.json`,
      manifest_sha256: sha256(Buffer.from(`${episodeId}-manifest`)),
      contact_sheet_path: contact.relPath,
      contact_sheet_sha256: contact.sha256,
      options,
    };
  });

  const manifest = {
    schema_version: 1,
    created_at: '2026-06-07T00:36:13Z',
    review_id: overrides.reviewId ?? 'season-02-backplate-options-review',
    status: 'review_ready_blocked_options_only',
    human_disposition: 'defer',
    may_advance: Boolean(overrides.mayAdvance),
    episodes,
  };

  if (overrides.badHash) {
    manifest.episodes[0].options[0].sha256 = '0'.repeat(64);
  }

  if (overrides.missingImage) {
    manifest.episodes[0].options[0].path = 'assets/missing.png';
  }

  const manifestPath = path.join(packet, 'manifest.json');
  writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
  return { packet, manifestPath };
}

test('backplate review publish dry-run normalizes the review packet', () => {
  const { packet, manifestPath } = createPacket();
  try {
    const result = runBackplateCli(['publish', '--manifest', manifestPath, '--dry-run']);
    assert.equal(result.ok, true);
    assert.equal(result.dryRun, true);
    assert.equal(result.uploadAssetCount, 34);
    assert.equal(
      result.remoteReviewUrl,
      'https://cascadeeffects.tv/reviews/season-02/backplate-options/season-02-backplate-options-review',
    );
    assert.match(result.manifestBlobUrl, /^dry-run:reviews\/backplate-options\/season-02-backplate-options-review\/manifest\.json$/);
  } finally {
    rmSync(packet, { recursive: true, force: true });
  }
});

test('backplate review validation rejects invalid review ids', () => {
  const { packet, manifestPath } = createPacket({ reviewId: 'bad review id' });
  try {
    const result = runBackplateCli(['validate', '--manifest', manifestPath, '--json']);
    assert.equal(result.ok, false);
    assert.deepEqual(result.issues, ['invalid reviewId']);
  } finally {
    rmSync(packet, { recursive: true, force: true });
  }
});

test('backplate review validation catches image hash drift', () => {
  const { packet, manifestPath } = createPacket({ badHash: true });
  try {
    const result = runBackplateCli(['validate', '--manifest', manifestPath, '--json']);
    assert.equal(result.ok, false);
    assert.match(result.issues.join('\n'), /sha256 mismatch/);
  } finally {
    rmSync(packet, { recursive: true, force: true });
  }
});

test('backplate review validation catches missing images', () => {
  const { packet, manifestPath } = createPacket({ missingImage: true });
  try {
    const result = runBackplateCli(['validate', '--manifest', manifestPath, '--json']);
    assert.equal(result.ok, false);
    assert.match(result.issues.join('\n'), /image not found/);
  } finally {
    rmSync(packet, { recursive: true, force: true });
  }
});

test('backplate review validation blocks may_advance true anywhere in the manifest', () => {
  const { packet, manifestPath } = createPacket({ mayAdvance: true, episodeMayAdvance: true });
  try {
    const result = runBackplateCli(['validate', '--manifest', manifestPath, '--json']);
    assert.equal(result.ok, false);
    assert.match(result.issues.join('\n'), /may_advance must remain false/);
  } finally {
    rmSync(packet, { recursive: true, force: true });
  }
});
