/* eslint-disable @next/next/no-img-element */
import { Images, ShieldCheck } from 'lucide-react';

import { type BackplateReviewEpisode, type BackplateReviewManifest, type BackplateReviewOption } from '@/lib/reviews/backplate-options';

import styles from './backplate-options-review.module.css';

type BackplateOptionsReviewProps = {
  manifest: BackplateReviewManifest;
};

const boolLabel = (value: boolean): string => (value ? 'true' : 'false');

const optionLabel = (option: BackplateReviewOption): string =>
  `${option.kind === 'existing' ? 'Existing' : 'New'} ${option.id.replace(/-/g, ' ')}`;

function OptionCard({ episode, option }: { episode: BackplateReviewEpisode; option: BackplateReviewOption }) {
  return (
    <article className={styles.optionCard}>
      <a href={option.imageUrl} target="_blank" rel="noreferrer">
        <img src={option.imageUrl} alt={`${episode.title} ${option.id} backplate option`} loading="lazy" />
      </a>
      <div className={styles.optionBody}>
        <div className={styles.optionTitle}>
          <h3>{optionLabel(option)}</h3>
          <span className={styles.pill}>{option.kind}</span>
        </div>
        <p className={styles.meta}>{option.status}</p>
        <p className={styles.hash}>sha256 {option.sha256}</p>
        {option.promptSha256 ? <p className={styles.hash}>prompt {option.promptSha256}</p> : null}
      </div>
    </article>
  );
}

function EpisodeSection({ episode }: { episode: BackplateReviewEpisode }) {
  return (
    <section id={episode.episodeId} className={styles.episode} data-episode-id={episode.episodeId}>
      <header className={styles.episodeHead}>
        <div>
          <p className={styles.eyebrow}>{episode.episodeId}</p>
          <h2>{episode.title}</h2>
        </div>
        <div className={styles.statusBlock}>
          <span>{episode.status}</span>
          <span>may_advance: {boolLabel(episode.mayAdvance)}</span>
          <span>
            {episode.generatedOptionCount} new / {episode.existingOptionCount} existing
          </span>
        </div>
      </header>

      <div className={styles.contactRow}>
        <a href={episode.contactSheet.url} target="_blank" rel="noreferrer">
          <img src={episode.contactSheet.url} alt={`${episode.episodeId} contact sheet`} loading="lazy" />
        </a>
      </div>

      <div className={styles.optionsGrid}>
        {episode.options.map((option) => (
          <OptionCard key={`${episode.episodeId}-${option.id}`} episode={episode} option={option} />
        ))}
      </div>
    </section>
  );
}

export function BackplateOptionsReview({ manifest }: BackplateOptionsReviewProps) {
  return (
    <main className={styles.page} data-review-id={manifest.reviewId}>
      <header className={styles.header}>
        <p className={styles.eyebrow}>Season 2 Source Art Review</p>
        <h1>Backplate Options Review</h1>
        <p className={styles.lede}>
          Candidate-only living-cover backplates for human review. No source-art, living-cover, publish, or upload gate is advanced by this page.
        </p>
      </header>

      <section className={styles.summary} aria-label="Review summary">
        <div>
          <strong>{manifest.summary.episodeCount}</strong>
          <span>episodes</span>
        </div>
        <div>
          <strong>{manifest.summary.generatedOptionCount}</strong>
          <span>new 1920x1080 options</span>
        </div>
        <div>
          <strong>{manifest.summary.existingOptionCount}</strong>
          <span>existing ep09 options retained</span>
        </div>
        <div>
          <strong>{manifest.summary.optionCount}</strong>
          <span>total option images</span>
        </div>
        <div>
          <strong>{boolLabel(manifest.mayAdvance)}</strong>
          <span>may_advance</span>
        </div>
      </section>

      <nav className={styles.nav} aria-label="Episode shortcuts">
        {manifest.episodes.map((episode) => (
          <a key={episode.episodeId} href={`#${episode.episodeId}`}>
            {episode.episodeId.replace(/^ep/, 'ep ')}
          </a>
        ))}
      </nav>

      {manifest.episodes.map((episode) => (
        <EpisodeSection key={episode.episodeId} episode={episode} />
      ))}

      <footer className={styles.footer}>
        <p>
          <ShieldCheck aria-hidden="true" /> {manifest.status}; human disposition {manifest.humanDisposition}; remote publication is review-only.
        </p>
        <p>
          <Images aria-hidden="true" /> {manifest.summary.contactSheetCount} contact sheets and {manifest.summary.optionCount} option images served from Vercel Blob.
        </p>
      </footer>
    </main>
  );
}
