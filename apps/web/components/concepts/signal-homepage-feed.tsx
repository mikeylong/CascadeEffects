'use client';

import Image from 'next/image';

import type { LaunchEpisode } from '@/lib/site-facts';

import styles from './signal-homepage.module.css';

type SignalHomepageFeedProps = {
  episodes: LaunchEpisode[];
};

function StoryThumbnail({ episode }: { episode: LaunchEpisode }) {
  if (episode.thumbnailSrc) {
    const thumbnail = (
      <div className={styles.storyThumbnail} data-variant="image">
        <Image
          src={episode.thumbnailSrc}
          alt={episode.thumbnailAlt ?? ''}
          fill
          sizes="(max-width: 720px) 100vw, (max-width: 1100px) 50vw, 33vw"
          className={styles.storyThumbnailImage}
          style={{ objectPosition: episode.thumbnailObjectPosition ?? 'center' }}
        />
        <div className={styles.storyMeta}>
          <p className={styles.storyPill}>{episode.subject}</p>
        </div>
      </div>
    );

    if (!episode.youtubeUrl) {
      return thumbnail;
    }

    return (
      <a
        className={styles.storyThumbnailLink}
        href={episode.youtubeUrl}
        target="_blank"
        rel="noopener noreferrer"
        aria-label={`Open ${episode.subject} episode on YouTube`}
      >
        {thumbnail}
      </a>
    );
  }

  return (
    <div className={styles.storyThumbnail}>
      <div className={styles.storyThumbnailFrame} aria-hidden="true" />
      <div className={styles.storyThumbnailGrid} aria-hidden="true" />
      <span className={styles.storyThumbnailSignal} aria-hidden="true" />
      <div className={styles.storyMeta}>
        <p className={styles.storyPill}>{episode.subject}</p>
      </div>
    </div>
  );
}

export function SignalHomepageFeed({
  episodes,
}: SignalHomepageFeedProps) {
  const visibleEpisodes = episodes.filter((episode) => episode.seasonId === 'season-1');

  return (
    <div className={styles.storyFeed}>
      <div className={styles.filterBar} aria-label="Episode filters">
        <button
          type="button"
          className={styles.filterButton}
          data-state="active"
          aria-pressed={true}
          aria-label="Season 1 filter is selected"
        >
          Season 1
        </button>
      </div>

      <div className={styles.storyList}>
        {visibleEpisodes.map((episode) => {
          const titleId = `episode-card-title-${episode.id}`;

          return (
            <article key={episode.id} className={styles.storyItem} aria-labelledby={titleId}>
              <StoryThumbnail episode={episode} />
              <div className={styles.storyContent}>
                <h3 id={titleId} className={styles.storyTitle}>{episode.title}</h3>
                <p className={styles.storySummary}>{episode.summary}</p>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
