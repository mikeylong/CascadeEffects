'use client';

import Image from 'next/image';
import { useMemo, useState } from 'react';

import type { ChannelPillar, ChannelPillarId, LaunchEpisode } from '@/lib/site-facts';

import styles from './signal-homepage.module.css';

type EpisodeFilter = 'all' | ChannelPillarId;

type SignalHomepageFeedProps = {
  episodes: LaunchEpisode[];
  pillars: ChannelPillar[];
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
  pillars,
}: SignalHomepageFeedProps) {
  const [selectedFilter, setSelectedFilter] = useState<EpisodeFilter>('all');
  const selectedPillar = pillars.find((pillar) => pillar.id === selectedFilter);
  const visibleEpisodes = useMemo(
    () => (
      selectedFilter === 'all'
        ? episodes
        : episodes.filter((episode) => episode.pillarId === selectedFilter)
    ),
    [episodes, selectedFilter],
  );

  return (
    <div className={styles.storyFeed}>
      <div className={styles.filterBar} aria-label="Episode filters">
        <button
          type="button"
          className={styles.filterButton}
          data-state={selectedFilter === 'all' ? 'active' : 'idle'}
          aria-pressed={selectedFilter === 'all'}
          onClick={() => setSelectedFilter('all')}
        >
          All
        </button>

        {pillars.map((pillar) => (
          <button
            key={pillar.id}
            type="button"
            className={styles.filterButton}
            data-accent={pillar.accent}
            data-state={selectedFilter === pillar.id ? 'active' : 'idle'}
            aria-pressed={selectedFilter === pillar.id}
            onClick={() => setSelectedFilter(pillar.id)}
          >
            {pillar.title}
          </button>
        ))}
      </div>

      {selectedPillar ? (
        <div className={styles.filterDescription} data-accent={selectedPillar.accent}>
          <h2 className={styles.filterDescriptionTitle}>{selectedPillar.title}</h2>
          <p className={styles.filterDescriptionSummary}>{selectedPillar.summary}</p>
        </div>
      ) : null}

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
