import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import test from 'node:test';

const ROOT = path.resolve(import.meta.dirname, '..');
const SCRIPT = path.join(ROOT, 'scripts', 'publish-readiness-review.mjs');

function runReviewCli(args) {
  const output = execFileSync('node', [SCRIPT, ...args], {
    cwd: ROOT,
    encoding: 'utf8',
  });
  return JSON.parse(output);
}

function writePacket(manifest) {
  const packet = mkdtempSync(path.join(tmpdir(), 'cascade-review-'));
  writeFileSync(path.join(packet, 'publish_readiness_manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
  return packet;
}

const baseManifest = {
  review_id: 'test-episode',
  episode_id: 'test-episode',
  episode_title: 'Test Episode',
  created_utc: '2026-05-18T00:00:00Z',
  status: 'inception_review_initialized',
  human_disposition: 'defer',
  next_review_question: 'Review inception state.',
  local_review_url: 'file:///tmp/review.html',
  metadata: {
    title: 'Test Episode',
    description: 'Review placeholder.',
    chapters: [],
    tags: [],
    hashtags: [],
  },
  locks: {
    publish_ready: false,
    youtube_upload_ready: false,
    public_release_ready: false,
    may_youtube_action: false,
    upload_performed: false,
  },
};

test('inception mode permits a lifecycle manifest without YouTube video', () => {
  const packet = writePacket({
    ...baseManifest,
    lifecycle_stage: 'inception',
    youtube_review: {
      host: 'youtube_unlisted',
      video_id: '',
      privacy_status: '',
    },
  });
  try {
    const result = runReviewCli(['validate', '--packet', packet, '--mode', 'inception', '--json']);
    assert.equal(result.ok, true);
    assert.equal(result.manifest.lifecycleStage, 'inception');
    assert.equal(result.youtubeVideoId, '');
    assert.equal(result.manifest.youtubeReview, null);

    const publish = runReviewCli(['publish', '--packet', packet, '--mode', 'inception', '--dry-run']);
    assert.equal(publish.ok, true);
    assert.equal(publish.dryRun, true);
    assert.match(publish.remoteReviewUrl, /\/reviews\/publish-readiness\/test-episode$/);
  } finally {
    rmSync(packet, { recursive: true, force: true });
  }
});

test('publish-readiness mode still requires an unlisted YouTube review receipt', () => {
  const packet = writePacket({
    ...baseManifest,
    lifecycle_stage: 'publish_readiness',
    youtube_review: {
      host: 'youtube_unlisted',
      video_id: 'yt-private',
      privacy_status: 'private',
      receipt_path: '/tmp/youtube_review_upload_receipt_private.json',
    },
  });
  try {
    const result = runReviewCli(['validate', '--packet', packet, '--mode', 'publish-readiness', '--json']);
    assert.equal(result.ok, false);
    assert.deepEqual(result.issues, ['YouTube privacy must be unlisted, got private']);
  } finally {
    rmSync(packet, { recursive: true, force: true });
  }
});

test('publish-readiness mode accepts an unlisted YouTube review descriptor', () => {
  const packet = writePacket({
    ...baseManifest,
    lifecycle_stage: 'publish_readiness',
    youtube_review: {
      host: 'youtube_unlisted',
      video_id: 'yt-unlisted',
      privacy_status: 'unlisted',
      processing_status: 'succeeded',
      receipt_path: '/tmp/youtube_review_upload_receipt_unlisted.json',
    },
  });
  try {
    const result = runReviewCli(['validate', '--packet', packet, '--mode', 'publish-readiness', '--json']);
    assert.equal(result.ok, true);
    assert.equal(result.youtubeVideoId, 'yt-unlisted');
    assert.equal(result.youtubePrivacyStatus, 'unlisted');
  } finally {
    rmSync(packet, { recursive: true, force: true });
  }
});

test('publish-readiness mode blocks video titles with channel suffix', () => {
  const packet = writePacket({
    ...baseManifest,
    lifecycle_stage: 'publish_readiness',
    metadata: {
      ...baseManifest.metadata,
      title: 'Test Episode | Cascade Effects',
    },
    youtube_review: {
      host: 'youtube_unlisted',
      video_id: 'yt-unlisted',
      privacy_status: 'unlisted',
      processing_status: 'succeeded',
      receipt_path: '/tmp/youtube_review_upload_receipt_unlisted.json',
    },
  });
  try {
    const result = runReviewCli(['validate', '--packet', packet, '--mode', 'publish-readiness', '--json']);
    assert.equal(result.ok, false);
    assert.deepEqual(result.issues, ['metadata.title must not append `| Cascade Effects`']);
  } finally {
    rmSync(packet, { recursive: true, force: true });
  }
});

test('publish-readiness mode blocks unlisted videos with embeds disabled', () => {
  const packet = writePacket({
    ...baseManifest,
    lifecycle_stage: 'publish_readiness',
    youtube_review: {
      host: 'youtube_unlisted',
      video_id: 'yt-unlisted-no-embed',
      privacy_status: 'unlisted',
      processing_status: 'succeeded',
      embeddable: false,
      receipt_path: '/tmp/youtube_review_upload_receipt_unlisted_no_embed.json',
    },
  });
  try {
    const result = runReviewCli(['validate', '--packet', packet, '--mode', 'publish-readiness', '--json']);
    assert.equal(result.ok, false);
    assert.deepEqual(result.issues, ['YouTube review video must be embeddable for cascadeeffects.tv playback']);
  } finally {
    rmSync(packet, { recursive: true, force: true });
  }
});

test('publish-readiness title-update receipts preserve current YouTube title', () => {
  const packet = writePacket({
    ...baseManifest,
    lifecycle_stage: 'publish_readiness',
  });
  const receiptPath = path.join(packet, 'youtube_title_update_receipt.json');
  writeFileSync(
    receiptPath,
    `${JSON.stringify(
      {
        receipt_type: 'youtube_title_update',
        video_id: 'yt-title-update',
        video_url: 'https://www.youtube.com/watch?v=yt-title-update',
        new_title: 'Test Episode',
        verification: {
          after: {
            video_id: 'yt-title-update',
            video_url: 'https://www.youtube.com/watch?v=yt-title-update',
            title: 'Test Episode',
            privacy_status: 'unlisted',
            processing_status: 'succeeded',
            upload_status: 'processed',
            raw_response: {
              items: [
                {
                  snippet: {
                    title: 'Test Episode',
                  },
                  status: {
                    embeddable: true,
                    privacyStatus: 'unlisted',
                    uploadStatus: 'processed',
                  },
                },
              ],
            },
          },
        },
      },
      null,
      2,
    )}\n`,
  );
  try {
    const result = runReviewCli([
      'validate',
      '--packet',
      packet,
      '--receipt',
      receiptPath,
      '--mode',
      'publish-readiness',
      '--json',
    ]);
    assert.equal(result.ok, true);
    assert.equal(result.manifest.youtubeReview.videoId, 'yt-title-update');
    assert.equal(result.manifest.youtubeReview.title, 'Test Episode');
    assert.equal(result.manifest.youtubeReview.embeddable, true);
  } finally {
    rmSync(packet, { recursive: true, force: true });
  }
});

test('publish-readiness mode blocks current YouTube receipt titles with channel suffix', () => {
  const packet = writePacket({
    ...baseManifest,
    lifecycle_stage: 'publish_readiness',
  });
  const receiptPath = path.join(packet, 'youtube_title_update_receipt_bad_title.json');
  writeFileSync(
    receiptPath,
    `${JSON.stringify(
      {
        receipt_type: 'youtube_title_update',
        video_id: 'yt-title-suffix',
        video_url: 'https://www.youtube.com/watch?v=yt-title-suffix',
        new_title: 'Test Episode | Cascade Effects',
        verification: {
          after: {
            video_id: 'yt-title-suffix',
            video_url: 'https://www.youtube.com/watch?v=yt-title-suffix',
            title: 'Test Episode | Cascade Effects',
            privacy_status: 'unlisted',
            processing_status: 'succeeded',
            upload_status: 'processed',
            raw_response: {
              items: [{ status: { embeddable: true, privacyStatus: 'unlisted', uploadStatus: 'processed' } }],
            },
          },
        },
      },
      null,
      2,
    )}\n`,
  );
  try {
    const result = runReviewCli([
      'validate',
      '--packet',
      packet,
      '--receipt',
      receiptPath,
      '--mode',
      'publish-readiness',
      '--json',
    ]);
    assert.equal(result.ok, false);
    assert.deepEqual(result.issues, ['YouTube review title must not append `| Cascade Effects`']);
  } finally {
    rmSync(packet, { recursive: true, force: true });
  }
});

test('publish-readiness receipts preserve YouTube embeddable status', () => {
  const packet = writePacket({
    ...baseManifest,
    lifecycle_stage: 'publish_readiness',
  });
  const receiptPath = path.join(packet, 'youtube_review_upload_receipt.json');
  writeFileSync(
    receiptPath,
    `${JSON.stringify(
      {
        receipt_type: 'youtube_longform_unlisted_visibility',
        video_id: 'yt-from-receipt',
        video_url: 'https://www.youtube.com/watch?v=yt-from-receipt',
        privacy: 'unlisted',
        after: {
          video_id: 'yt-from-receipt',
          video_url: 'https://www.youtube.com/watch?v=yt-from-receipt',
          privacy_status: 'unlisted',
          processing_status: 'succeeded',
          upload_status: 'processed',
          raw_response: {
            items: [
              {
                status: {
                  embeddable: false,
                  privacyStatus: 'unlisted',
                  uploadStatus: 'processed',
                },
              },
            ],
          },
        },
      },
      null,
      2,
    )}\n`,
  );
  try {
    const result = runReviewCli([
      'validate',
      '--packet',
      packet,
      '--receipt',
      receiptPath,
      '--mode',
      'publish-readiness',
      '--json',
    ]);
    assert.equal(result.ok, false);
    assert.equal(result.manifest.youtubeReview.videoId, 'yt-from-receipt');
    assert.equal(result.manifest.youtubeReview.embeddable, false);
    assert.deepEqual(result.issues, ['YouTube review video must be embeddable for cascadeeffects.tv playback']);
  } finally {
    rmSync(packet, { recursive: true, force: true });
  }
});
