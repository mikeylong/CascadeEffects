export type AccentKey = 'signal' | 'amber' | 'blueprint';
export type EpisodeStatus = 'recorded' | 'launchingSoon';
export type ChannelPillarId = 'one-decision' | 'receipts' | 'design-failures';

export type LaunchEpisode = {
  id: string;
  title: string;
  subject: string;
  status: EpisodeStatus;
  pillarId: ChannelPillarId;
  label: string;
  summary: string;
  scheduleLabel: string;
  scheduleValue: string;
  thumbnailCopy?: string;
  thumbnailSrc?: string;
  thumbnailAlt?: string;
  thumbnailObjectPosition?: string;
  youtubeUrl?: string;
};

export type ChannelPillar = {
  id: ChannelPillarId;
  title: string;
  accent: AccentKey;
  summary: string;
};

export const siteIdentity = {
  title: 'Cascade of Effects',
  url: 'https://cascadeeffects.tv',
  handle: '@CascadeEffects',
  email: 'hello@cascadeeffects.tv',
  youtubeUrl: 'https://www.youtube.com/@CascadeEffects',
  youtubeWatchUrl:
    'https://www.youtube.com/watch?v=VVOz8KYfNgY&list=PLYYmvm5t-VZZ3s7S_GKnHByJZW_JYWBXh',
  tagline: 'The overlooked detail that changed everything.',
  description:
    'Cascade Effects explores the hidden chains behind major events, design failures, and turning points in history.',
  longDescription:
    'Cascade Effects explores the hidden chains behind major events, design failures, and turning points in history. Each episode follows the decisions, constraints, incentives, and overlooked details that shaped what happened next.',
  premise:
    'Cascade Effects is a faceless documentary channel about hidden chains of cause and effect.',
} as const;

const seasonOnePlaylistId = 'PLYYmvm5t-VZZ3s7S_GKnHByJZW_JYWBXh';
const seasonOneEpisodeUrl = (videoId: string, index: number) =>
  `https://www.youtube.com/watch?v=${videoId}&list=${seasonOnePlaylistId}&index=${index}`;

export const launchEpisodes: LaunchEpisode[] = [
  {
    id: 'challenger',
    title: 'How the Warnings Stopped Working',
    subject: 'Challenger',
    status: 'recorded',
    pillarId: 'one-decision',
    label: 'Design Failures · Launch Episode 01',
    summary:
      'A chain of engineering warnings, schedule pressure, and normalized cold-weather risk turned one launch decision into catastrophe.',
    scheduleLabel: 'Release date',
    scheduleValue: 'To be announced',
    thumbnailSrc:
      '/brand/episode-gallery/proof-v6-ink-lit-subjects/challenger-thumbnail-proof-v6-ink-lit-subjects.webp',
    thumbnailAlt:
      'Ink-lit paper architecture thumbnail of a clean space shuttle launch stack.',
    youtubeUrl: seasonOneEpisodeUrl('safBLFP3he8', 2),
  },
  {
    id: 'therac-25',
    title: 'The Machine That Was Trusted Too Early',
    subject: 'Therac-25',
    status: 'launchingSoon',
    pillarId: 'design-failures',
    label: 'Design Failures · Launch Episode 02',
    summary:
      'Software assumptions, interface design, and institutional disbelief combined to let lethal radiation overdoses repeat.',
    scheduleLabel: 'Expected release',
    scheduleValue: 'To be announced',
    thumbnailSrc:
      '/brand/episode-gallery/proof-v6-ink-lit-subjects/therac-25-thumbnail-proof-v6-ink-lit-subjects.webp',
    thumbnailAlt:
      'Ink-lit paper architecture thumbnail of a clean medical linear accelerator and treatment couch.',
    youtubeUrl: seasonOneEpisodeUrl('OsPgjlPRN6M', 3),
  },
  {
    id: 'hyatt-regency',
    title: 'The Redesign That Doubled the Load',
    subject: 'Hyatt Regency',
    status: 'launchingSoon',
    pillarId: 'design-failures',
    label: 'Design Failures · Launch Episode 03',
    summary:
      'A shop-drawing revision doubled the load on an already weak walkway connection, turning a routine fabrication change into catastrophe.',
    scheduleLabel: 'Expected release',
    scheduleValue: 'To be announced',
    thumbnailSrc:
      '/brand/episode-gallery/proof-v6-ink-lit-subjects/hyatt-regency-thumbnail-proof-v6-ink-lit-subjects.webp',
    thumbnailAlt:
      'Ink-lit paper architecture thumbnail of a clean hotel atrium with suspended walkways.',
    youtubeUrl: seasonOneEpisodeUrl('sE5YKLicnME', 4),
  },
  {
    id: 'semmelweis',
    title: 'The Evidence Medicine Rejected',
    subject: 'Semmelweis',
    status: 'launchingSoon',
    pillarId: 'one-decision',
    label: 'One Decision · Launch Episode 04',
    summary:
      'Hospital mortality ledgers exposed the cause chain, but the profession resisted what the evidence implied about its own routines.',
    scheduleLabel: 'Expected release',
    scheduleValue: 'To be announced',
    thumbnailSrc:
      '/brand/episode-gallery/proof-v6-ink-lit-subjects/semmelweis-thumbnail-proof-v6-ink-lit-subjects.webp',
    thumbnailAlt:
      'Ink-lit paper architecture thumbnail of a simplified nineteenth-century hospital ward with a washing basin.',
    youtubeUrl: seasonOneEpisodeUrl('VY7RXqWfdfs', 5),
  },
  {
    id: 'tacoma-narrows',
    title: 'The Bridge That Lost Its Margin',
    subject: 'Tacoma Narrows',
    status: 'launchingSoon',
    pillarId: 'design-failures',
    label: 'Design Failures · Launch Episode 05',
    summary:
      'A wind-structure feedback loop the design process had not accounted for turned visible oscillation into collapse.',
    scheduleLabel: 'Expected release',
    scheduleValue: 'To be announced',
    thumbnailSrc:
      '/brand/episode-gallery/proof-v6-ink-lit-subjects/tacoma-narrows-thumbnail-proof-v6-ink-lit-subjects.webp',
    thumbnailAlt:
      'Ink-lit paper architecture thumbnail of a clean suspension bridge on a dry paper model base.',
    youtubeUrl: seasonOneEpisodeUrl('sknu2lK8Z2o', 6),
  },
  {
    id: 'piltdown-man',
    title: 'The Fossil That Flattered Authority',
    subject: 'Piltdown Man',
    status: 'launchingSoon',
    pillarId: 'receipts',
    label: 'Receipts · Launch Episode 06',
    summary:
      'A flattering fossil story survived because authority, expectation, and weak scrutiny protected the lie.',
    scheduleLabel: 'Expected release',
    scheduleValue: 'To be announced',
    thumbnailSrc:
      '/brand/episode-gallery/proof-v6-ink-lit-subjects/piltdown-man-thumbnail-proof-v6-ink-lit-subjects.webp',
    thumbnailAlt:
      'Ink-lit paper architecture thumbnail of a fossil skull and jaw specimen on a museum plinth.',
    youtubeUrl: seasonOneEpisodeUrl('s88BAewrp2M', 7),
  },
  {
    id: '737-max',
    title: 'The Hidden System That Moved the Risk',
    subject: '737 MAX',
    status: 'launchingSoon',
    pillarId: 'design-failures',
    label: 'Design Failures · Launch Episode 07',
    summary:
      'A hidden flight-control behavior moved risk onto crews who had been trained to believe the aircraft was familiar.',
    scheduleLabel: 'Expected release',
    scheduleValue: 'To be announced',
    thumbnailSrc:
      '/brand/episode-gallery/proof-v6-ink-lit-subjects/737-max-thumbnail-proof-v6-ink-lit-subjects.webp',
    thumbnailAlt:
      'Ink-lit paper architecture thumbnail of a clean modern passenger jet on a paper runway.',
    youtubeUrl: seasonOneEpisodeUrl('3F9MaG2IcmM', 8),
  },
  {
    id: 'titanic',
    title: 'Legal, Compliant, and Not Safe',
    subject: 'Titanic',
    status: 'launchingSoon',
    pillarId: 'receipts',
    label: 'Mystery That Has Receipts · Launch Episode 08',
    summary:
      'A ship could be legal, compliant, and still unsafe when lifeboat regulation lagged behind scale.',
    scheduleLabel: 'Expected release',
    scheduleValue: 'To be announced',
    thumbnailSrc:
      '/brand/episode-gallery/proof-v6-ink-lit-subjects/titanic-thumbnail-proof-v6-ink-lit-subjects.webp',
    thumbnailAlt:
      'Ink-lit paper architecture thumbnail of a clean early ocean liner on a dry display plinth.',
    youtubeUrl: seasonOneEpisodeUrl('yqcaIX9Lnws', 9),
  },
];

export const channelPillars: ChannelPillar[] = [
  {
    id: 'one-decision',
    title: 'One Decision Changed Everything',
    accent: 'signal',
    summary:
      'Stories centered on a pivotal choice, delay, shortcut, or missed moment that altered the outcome.',
  },
  {
    id: 'receipts',
    title: 'Mystery That Has Receipts',
    accent: 'amber',
    summary:
      'Stories where logs, manifests, transcripts, and official records complicate the accepted version of events.',
  },
  {
    id: 'design-failures',
    title: 'Design Failures That Changed the World',
    accent: 'blueprint',
    summary:
      'Stories about technical, organizational, or human-system failures shaped by constraints, incentives, and normalized risk.',
  },
];
