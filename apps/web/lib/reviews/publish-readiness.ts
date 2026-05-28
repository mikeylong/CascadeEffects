export type ReviewAsset = {
  label: string;
  url: string;
  kind?: string;
  path?: string;
  sha256?: string;
  bytes?: number;
  mimeType?: string;
};

export type ReviewChapter = {
  title: string;
  timestamp: string;
  seconds: number;
  summary?: string;
};

export type YouTubeReview = {
  host: 'youtube_unlisted' | 'youtube_private';
  videoId: string;
  watchUrl: string;
  embedUrl: string;
  privacyStatus: string;
  processingStatus: string;
  uploadStatus?: string;
  embeddable?: boolean;
  receiptPath?: string;
  receiptSha256?: string;
  accessNote: string;
};

export type ReviewLifecycleStage = 'inception' | 'in_progress' | 'publish_readiness';

export type PublishReadinessReviewManifest = {
  schemaVersion: 1;
  lifecycleStage: ReviewLifecycleStage;
  reviewId: string;
  episodeId: string;
  episodeTitle: string;
  createdUtc: string;
  sourcePacketPath: string;
  status: string;
  humanDisposition: string;
  nextReviewQuestion: string;
  localReviewUrl: string;
  remoteReviewUrl: string;
  youtubeReview?: YouTubeReview;
  locks: {
    publishReady: boolean;
    youtubeUploadReady: boolean;
    publicReleaseReady: boolean;
    mayYoutubeAction: boolean;
    uploadPerformed: boolean;
  };
  assets: {
    video?: YouTubeReview;
    captions: ReviewAsset[];
    thumbnail?: ReviewAsset;
    qaFrames: ReviewAsset[];
    transitionSamples: ReviewAsset[];
    evidence: ReviewAsset[];
  };
  metadata: {
    title: string;
    description: string;
    chapters: ReviewChapter[];
    tags: string[];
    hashtags: string[];
    category?: string;
    audience?: string;
    visibility?: string;
  };
  reads: Record<string, string>;
  hashes: Record<string, string>;
  blockers: string[];
};

type UnknownRecord = Record<string, unknown>;

const isRecord = (value: unknown): value is UnknownRecord =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const readString = (value: unknown, fallback = ''): string =>
  typeof value === 'string' ? value : fallback;

const readBoolean = (value: unknown, fallback = false): boolean =>
  typeof value === 'boolean' ? value : fallback;

const readNumber = (value: unknown): number | undefined =>
  typeof value === 'number' && Number.isFinite(value) ? value : undefined;

const readStringArray = (value: unknown): string[] =>
  Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [];

const readRecord = (value: unknown): UnknownRecord => (isRecord(value) ? value : {});

const readLifecycleStage = (value: unknown): ReviewLifecycleStage => {
  const stage = readString(value).trim();
  if (stage === 'inception' || stage === 'in_progress' || stage === 'publish_readiness') return stage;
  return 'publish_readiness';
};

const readAsset = (value: unknown): ReviewAsset | undefined => {
  const record = readRecord(value);
  const url = readString(record.url);
  const label = readString(record.label);

  if (!url || !label) return undefined;

  return {
    label,
    url,
    kind: readString(record.kind) || undefined,
    path: readString(record.path) || undefined,
    sha256: readString(record.sha256) || undefined,
    bytes: readNumber(record.bytes),
    mimeType: readString(record.mimeType) || undefined,
  };
};

const readAssets = (value: unknown): ReviewAsset[] =>
  Array.isArray(value)
    ? value.map(readAsset).filter((asset): asset is ReviewAsset => Boolean(asset))
    : [];

export const parseTimestampToSeconds = (value: string | number | undefined): number => {
  if (typeof value === 'number' && Number.isFinite(value)) return Math.max(0, value);
  if (!value) return 0;

  const text = String(value).trim();
  if (/^\d+(\.\d+)?$/.test(text)) return Number(text);

  const parts = text.split(':').map((part) => Number(part));
  if (parts.some((part) => !Number.isFinite(part))) return 0;
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  if (parts.length === 2) return parts[0] * 60 + parts[1];

  return 0;
};

export const formatClock = (seconds: number): string => {
  const whole = Math.max(0, Math.round(seconds));
  const hours = Math.floor(whole / 3600);
  const minutes = Math.floor((whole % 3600) / 60);
  const secs = String(whole % 60).padStart(2, '0');

  return hours > 0 ? `${hours}:${String(minutes).padStart(2, '0')}:${secs}` : `${minutes}:${secs}`;
};

export const youtubeWatchUrl = (videoId: string): string =>
  videoId ? `https://www.youtube.com/watch?v=${encodeURIComponent(videoId)}` : '';

export const youtubeEmbedUrl = (videoId: string): string =>
  videoId
    ? `https://www.youtube-nocookie.com/embed/${encodeURIComponent(videoId)}?enablejsapi=1&rel=0&modestbranding=1&playsinline=1`
    : '';

const DEFAULT_UNLISTED_ACCESS_NOTE =
  'This unlisted YouTube review video can be viewed by anyone with the link. Keep the cascadeeffects.tv URL and YouTube watch URL limited to reviewers.';

const youtubeReviewHost = (value: string): YouTubeReview['host'] =>
  value === 'youtube_private' ? 'youtube_private' : 'youtube_unlisted';

const readChapter = (value: unknown): ReviewChapter | undefined => {
  const record = readRecord(value);
  const title = readString(record.title);
  const timestamp = readString(record.timestamp) || readString(record.time);
  const seconds = readNumber(record.seconds) ?? parseTimestampToSeconds(timestamp);

  if (!title || !timestamp) return undefined;

  return {
    title,
    timestamp,
    seconds,
    summary: readString(record.summary) || undefined,
  };
};

export const normalizeReviewManifest = (value: unknown): PublishReadinessReviewManifest => {
  const manifest = readRecord(value);
  const assets = readRecord(manifest.assets);
  const metadata = readRecord(manifest.metadata);
  const locks = readRecord(manifest.locks);
  const youtubeReview = readRecord(manifest.youtubeReview);
  const snakeYoutubeReview = readRecord(manifest.youtube_review);
  const snakeYoutubeUnlistedReview = readRecord(manifest.youtube_unlisted_review);
  const legacyYoutubePrivateReview = readRecord(manifest.youtubePrivateReview);
  const legacySnakeYoutubePrivateReview = readRecord(manifest.youtube_private_review);
  const remoteReview = readRecord(manifest.remote_review);
  const reviewSource =
    [youtubeReview, snakeYoutubeReview, snakeYoutubeUnlistedReview, legacyYoutubePrivateReview, legacySnakeYoutubePrivateReview].find(
      (candidate) => Object.keys(candidate).length > 0,
    ) ?? {};
  const video = readRecord(assets.video);
  const videoId = readString(reviewSource.videoId) || readString(reviewSource.video_id) || readString(video.videoId);
  const watchUrl =
    readString(reviewSource.watchUrl) ||
    readString(reviewSource.watch_url) ||
    readString(video.watchUrl) ||
    youtubeWatchUrl(videoId);
  const embedUrl =
    readString(reviewSource.embedUrl) ||
    readString(reviewSource.embed_url) ||
    readString(video.embedUrl) ||
    youtubeEmbedUrl(videoId);

  const youtube: YouTubeReview | undefined = videoId
    ? {
        host: youtubeReviewHost(readString(reviewSource.host) || readString(video.host)),
        videoId,
        watchUrl,
        embedUrl,
        privacyStatus:
          readString(reviewSource.privacyStatus) ||
          readString(reviewSource.privacy_status) ||
          readString(video.privacyStatus),
        processingStatus:
          readString(reviewSource.processingStatus) ||
          readString(reviewSource.processing_status) ||
          readString(video.processingStatus),
        uploadStatus:
          readString(reviewSource.uploadStatus) ||
          readString(reviewSource.upload_status) ||
          readString(video.uploadStatus) ||
          undefined,
        embeddable: readBoolean(reviewSource.embeddable, readBoolean(video.embeddable, true)),
        receiptPath:
          readString(reviewSource.receiptPath) ||
          readString(reviewSource.receipt_path) ||
          readString(video.receiptPath) ||
          undefined,
        receiptSha256:
          readString(reviewSource.receiptSha256) ||
          readString(reviewSource.receipt_sha256) ||
          readString(video.receiptSha256) ||
          undefined,
        accessNote:
          readString(reviewSource.accessNote) ||
          readString(video.accessNote) ||
          DEFAULT_UNLISTED_ACCESS_NOTE,
      }
    : undefined;

  const chapterValues = Array.isArray(metadata.chapters) ? metadata.chapters : [];
  const chapters = chapterValues
    .map(readChapter)
    .filter((chapter): chapter is ReviewChapter => Boolean(chapter));

  return {
    schemaVersion: 1,
    lifecycleStage: readLifecycleStage(
      manifest.lifecycleStage ?? manifest.lifecycle_stage ?? remoteReview.lifecycleStage ?? remoteReview.lifecycle_stage,
    ),
    reviewId: readString(manifest.reviewId) || readString(manifest.review_id),
    episodeId: readString(manifest.episodeId) || readString(manifest.episode_id),
    episodeTitle: readString(manifest.episodeTitle) || readString(manifest.episode_title),
    createdUtc: readString(manifest.createdUtc) || readString(manifest.created_utc),
    sourcePacketPath: readString(manifest.sourcePacketPath) || readString(manifest.source_packet_path),
    status: readString(manifest.status),
    humanDisposition: readString(manifest.humanDisposition) || readString(manifest.human_disposition),
    nextReviewQuestion: readString(manifest.nextReviewQuestion) || readString(manifest.next_review_question),
    localReviewUrl: readString(manifest.localReviewUrl) || readString(manifest.local_review_url),
    remoteReviewUrl: readString(manifest.remoteReviewUrl) || readString(remoteReview.remote_review_url),
    youtubeReview: youtube,
    locks: {
      publishReady: readBoolean(locks.publishReady, readBoolean(locks.publish_ready)),
      youtubeUploadReady: readBoolean(locks.youtubeUploadReady, readBoolean(locks.youtube_upload_ready)),
      publicReleaseReady: readBoolean(locks.publicReleaseReady, readBoolean(locks.public_release_ready)),
      mayYoutubeAction: readBoolean(locks.mayYoutubeAction, readBoolean(locks.may_youtube_action)),
      uploadPerformed: readBoolean(locks.uploadPerformed, readBoolean(locks.upload_performed)),
    },
    assets: {
      video: youtube,
      captions: readAssets(assets.captions),
      thumbnail: readAsset(assets.thumbnail),
      qaFrames: readAssets(assets.qaFrames),
      transitionSamples: readAssets(assets.transitionSamples),
      evidence: readAssets(assets.evidence),
    },
    metadata: {
      title: readString(metadata.title),
      description: readString(metadata.description),
      chapters,
      tags: readStringArray(metadata.tags),
      hashtags: readStringArray(metadata.hashtags),
      category: readString(metadata.category) || undefined,
      audience: readString(metadata.audience) || undefined,
      visibility: readString(metadata.visibility) || undefined,
    },
    reads: Object.fromEntries(
      Object.entries(readRecord(manifest.reads)).map(([key, item]) => [key, String(item)]),
    ),
    hashes: Object.fromEntries(
      Object.entries(readRecord(manifest.hashes)).map(([key, item]) => [key, String(item)]),
    ),
    blockers: readStringArray(manifest.blockers).length > 0 ? readStringArray(manifest.blockers) : readStringArray(manifest.remaining_blockers),
  };
};
