export type BackplateOptionKind = 'new' | 'existing' | string;

export type BackplateReviewOption = {
  id: string;
  kind: BackplateOptionKind;
  status: string;
  path: string;
  imageUrl: string;
  sha256: string;
  promptPath: string;
  promptSha256: string;
};

export type BackplateReviewEpisode = {
  episodeId: string;
  title: string;
  status: string;
  mayAdvance: boolean;
  generatedOptionCount: number;
  existingOptionCount: number;
  manifestPath: string;
  manifestSha256: string;
  contactSheet: {
    path: string;
    url: string;
    sha256: string;
  };
  options: BackplateReviewOption[];
};

export type BackplateReviewManifest = {
  schemaVersion: 1;
  reviewId: string;
  createdAt: string;
  status: string;
  humanDisposition: string;
  mayAdvance: boolean;
  remoteReviewUrl: string;
  sourceManifestPath: string;
  sourceManifestSha256: string;
  episodes: BackplateReviewEpisode[];
  summary: {
    episodeCount: number;
    generatedOptionCount: number;
    existingOptionCount: number;
    optionCount: number;
    contactSheetCount: number;
  };
};

type UnknownRecord = Record<string, unknown>;

const isRecord = (value: unknown): value is UnknownRecord =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const readRecord = (value: unknown): UnknownRecord => (isRecord(value) ? value : {});

const readString = (value: unknown, fallback = ''): string =>
  typeof value === 'string' ? value : fallback;

const readBoolean = (value: unknown, fallback = false): boolean =>
  typeof value === 'boolean' ? value : fallback;

const readNumber = (value: unknown, fallback = 0): number =>
  typeof value === 'number' && Number.isFinite(value) ? value : fallback;

const readArray = (value: unknown): unknown[] => (Array.isArray(value) ? value : []);

const readOption = (value: unknown): BackplateReviewOption => {
  const option = readRecord(value);
  const path =
    readString(option.path) ||
    readString(option.artifact_path) ||
    readString(option.artifactFinalPath) ||
    readString(option.artifact_final_path);

  return {
    id: readString(option.id),
    kind: readString(option.kind, 'new'),
    status: readString(option.status),
    path,
    imageUrl: readString(option.imageUrl) || readString(option.image_url) || readString(option.url),
    sha256: readString(option.sha256) || readString(option.artifactFinalSha256) || readString(option.artifact_final_sha256),
    promptPath: readString(option.promptPath) || readString(option.prompt_path),
    promptSha256: readString(option.promptSha256) || readString(option.prompt_sha256),
  };
};

const readEpisode = (value: unknown): BackplateReviewEpisode => {
  const episode = readRecord(value);
  const contactSheet = readRecord(episode.contactSheet ?? episode.contact_sheet);

  return {
    episodeId: readString(episode.episodeId) || readString(episode.episode_id),
    title: readString(episode.title),
    status: readString(episode.status),
    mayAdvance: readBoolean(episode.mayAdvance, readBoolean(episode.may_advance)),
    generatedOptionCount: readNumber(episode.generatedOptionCount, readNumber(episode.generated_option_count)),
    existingOptionCount: readNumber(episode.existingOptionCount, readNumber(episode.existing_option_count)),
    manifestPath: readString(episode.manifestPath) || readString(episode.manifest_path),
    manifestSha256: readString(episode.manifestSha256) || readString(episode.manifest_sha256),
    contactSheet: {
      path: readString(contactSheet.path) || readString(episode.contact_sheet_path),
      url: readString(contactSheet.url) || readString(contactSheet.imageUrl) || readString(contactSheet.image_url),
      sha256: readString(contactSheet.sha256) || readString(episode.contact_sheet_sha256),
    },
    options: readArray(episode.options).map(readOption),
  };
};

export const normalizeBackplateReviewManifest = (value: unknown): BackplateReviewManifest => {
  const manifest = readRecord(value);
  const episodes = readArray(manifest.episodes).map(readEpisode);
  const generatedOptionCount = episodes.reduce((total, episode) => total + episode.generatedOptionCount, 0);
  const existingOptionCount = episodes.reduce((total, episode) => total + episode.existingOptionCount, 0);

  return {
    schemaVersion: 1,
    reviewId: readString(manifest.reviewId) || readString(manifest.review_id),
    createdAt: readString(manifest.createdAt) || readString(manifest.created_at),
    status: readString(manifest.status),
    humanDisposition: readString(manifest.humanDisposition) || readString(manifest.human_disposition),
    mayAdvance: readBoolean(manifest.mayAdvance, readBoolean(manifest.may_advance)),
    remoteReviewUrl: readString(manifest.remoteReviewUrl) || readString(manifest.remote_review_url),
    sourceManifestPath: readString(manifest.sourceManifestPath) || readString(manifest.source_manifest_path),
    sourceManifestSha256: readString(manifest.sourceManifestSha256) || readString(manifest.source_manifest_sha256),
    episodes,
    summary: {
      episodeCount: episodes.length,
      generatedOptionCount,
      existingOptionCount,
      optionCount: episodes.reduce((total, episode) => total + episode.options.length, 0),
      contactSheetCount: episodes.filter((episode) => Boolean(episode.contactSheet.url || episode.contactSheet.path)).length,
    },
  };
};
