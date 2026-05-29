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
    title: 'The Warning That Stopped Working',
    subject: 'Challenger',
    status: 'recorded',
    pillarId: 'one-decision',
    label: 'Design Failures · Launch Episode 01',
    summary:
      'Repeated O-ring warnings became accepted operating history, so cold-weather risk shifted from a reason to stop into a burden the engineers had to prove.',
    scheduleLabel: 'Release date',
    scheduleValue: 'To be announced',
    thumbnailCopy: 'WARNING IGNORED',
    thumbnailSrc:
      '/brand/episode-gallery/proof-v6-ink-lit-subjects/challenger-thumbnail-proof-v6-ink-lit-subjects.webp',
    thumbnailAlt:
      'Ink-lit paper architecture thumbnail of a clean space shuttle launch stack.',
    youtubeUrl: seasonOneEpisodeUrl('safBLFP3he8', 2),
  },
  {
    id: 'therac-25',
    title: 'The Machine That Killed Without Warning',
    subject: 'Therac-25',
    status: 'launchingSoon',
    pillarId: 'design-failures',
    label: 'Design Failures · Launch Episode 02',
    summary:
      'Software control, missing hardware interlocks, and institutional disbelief left a medical machine able to repeat lethal overdoses without an obvious warning.',
    scheduleLabel: 'Expected release',
    scheduleValue: 'To be announced',
    thumbnailCopy: 'NO SAFETY LEFT',
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
      'A shop-drawing revision looked like fabrication detail, but in the load path it doubled the force on a connection that was already too weak.',
    scheduleLabel: 'Expected release',
    scheduleValue: 'To be announced',
    thumbnailCopy: 'DOUBLED THE LOAD',
    thumbnailSrc:
      '/brand/episode-gallery/proof-v6-ink-lit-subjects/hyatt-regency-thumbnail-proof-v6-ink-lit-subjects.webp',
    thumbnailAlt:
      'Ink-lit paper architecture thumbnail of a clean hotel atrium with suspended walkways.',
    youtubeUrl: seasonOneEpisodeUrl('sE5YKLicnME', 4),
  },
  {
    id: 'semmelweis',
    title: 'He Proved It. They Rejected It.',
    subject: 'Semmelweis',
    status: 'launchingSoon',
    pillarId: 'one-decision',
    label: 'One Decision · Launch Episode 04',
    summary:
      "The mortality evidence pointed back at doctors' own routines, so the proof threatened professional identity before medicine had a theory ready to absorb it.",
    scheduleLabel: 'Expected release',
    scheduleValue: 'To be announced',
    thumbnailCopy: 'PROVED. REJECTED.',
    thumbnailSrc:
      '/brand/episode-gallery/proof-v6-ink-lit-subjects/semmelweis-thumbnail-proof-v6-ink-lit-subjects.webp',
    thumbnailAlt:
      'Ink-lit paper architecture thumbnail of a simplified nineteenth-century hospital ward with a washing basin.',
    youtubeUrl: seasonOneEpisodeUrl('VY7RXqWfdfs', 5),
  },
  {
    id: 'tacoma-narrows',
    title: 'The Bridge That Taught Itself to Fly',
    subject: 'Tacoma Narrows',
    status: 'launchingSoon',
    pillarId: 'design-failures',
    label: 'Design Failures · Launch Episode 05',
    summary:
      'The bridge did not need an extraordinary storm; its slender deck turned ordinary wind into motion the design process had not modeled.',
    scheduleLabel: 'Expected release',
    scheduleValue: 'To be announced',
    thumbnailCopy: 'IT STARTED TO TWIST',
    thumbnailSrc:
      '/brand/episode-gallery/proof-v6-ink-lit-subjects/tacoma-narrows-thumbnail-proof-v6-ink-lit-subjects.webp',
    thumbnailAlt:
      'Ink-lit paper architecture thumbnail of a clean suspension bridge on a dry paper model base.',
    youtubeUrl: seasonOneEpisodeUrl('sknu2lK8Z2o', 6),
  },
  {
    id: 'piltdown-man',
    title: 'The Perfect Hoax',
    subject: 'Piltdown Man',
    status: 'launchingSoon',
    pillarId: 'receipts',
    label: 'Receipts · Launch Episode 06',
    summary:
      'A fossil story survived because it flattered expectation, prestige limited scrutiny, and institutions accepted evidence that told them they were right.',
    scheduleLabel: 'Expected release',
    scheduleValue: 'To be announced',
    thumbnailCopy: '41 YEARS WRONG',
    thumbnailSrc:
      '/brand/episode-gallery/proof-v6-ink-lit-subjects/piltdown-man-thumbnail-proof-v6-ink-lit-subjects.webp',
    thumbnailAlt:
      'Ink-lit paper architecture thumbnail of a fossil skull and jaw specimen on a museum plinth.',
    youtubeUrl: seasonOneEpisodeUrl('s88BAewrp2M', 7),
  },
  {
    id: '737-max',
    title: 'The System That Fought the Pilot',
    subject: '737 MAX',
    status: 'launchingSoon',
    pillarId: 'design-failures',
    label: 'Design Failures · Launch Episode 07',
    summary:
      'A hidden control behavior moved risk onto crews who had been trained to treat the aircraft as familiar, even after the system had changed.',
    scheduleLabel: 'Expected release',
    scheduleValue: 'To be announced',
    thumbnailCopy: 'HIDDEN FROM PILOTS',
    thumbnailSrc:
      '/brand/episode-gallery/proof-v6-ink-lit-subjects/737-max-thumbnail-proof-v6-ink-lit-subjects.webp',
    thumbnailAlt:
      'Ink-lit paper architecture thumbnail of a clean modern passenger jet on a paper runway.',
    youtubeUrl: seasonOneEpisodeUrl('3F9MaG2IcmM', 8),
  },
  {
    id: 'titanic',
    title: 'The Law Said It Was Safe',
    subject: 'Titanic',
    status: 'launchingSoon',
    pillarId: 'receipts',
    label: 'Mystery That Has Receipts · Launch Episode 08',
    summary:
      'Titanic satisfied the lifeboat rules, but the rules had not kept up with scale, turning compliance into a false safety signal.',
    scheduleLabel: 'Expected release',
    scheduleValue: 'To be announced',
    thumbnailCopy: 'LEGAL. NOT SAFE.',
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
