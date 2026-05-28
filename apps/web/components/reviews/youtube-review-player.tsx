'use client';

import { useEffect, useId, useRef, useState } from 'react';
import { ExternalLink } from 'lucide-react';

import { formatClock, type ReviewChapter, type YouTubeReview } from '@/lib/reviews/publish-readiness';

import styles from './publish-readiness-review.module.css';

type PlayerEvent = {
  target: YouTubePlayer;
  data?: number;
};

type YouTubePlayer = {
  seekTo: (seconds: number, allowSeekAhead: boolean) => void;
  playVideo: () => void;
};

type YouTubeConstructor = new (
  elementId: string,
  options: {
    events: {
      onReady: (event: PlayerEvent) => void;
      onError: (event: PlayerEvent) => void;
    };
  },
) => YouTubePlayer;

declare global {
  interface Window {
    YT?: {
      Player?: YouTubeConstructor;
    };
    onYouTubeIframeAPIReady?: () => void;
  }
}

type YouTubeReviewPlayerProps = {
  review: Pick<YouTubeReview, 'host' | 'watchUrl' | 'embedUrl' | 'privacyStatus'>;
  chapters: ReviewChapter[];
  transitionSamples: Array<{ label: string; seconds?: number }>;
};

type PlayerReview = YouTubeReviewPlayerProps['review'];

const ensureYouTubeApi = (): Promise<YouTubeConstructor> =>
  new Promise((resolve) => {
    if (window.YT?.Player) {
      resolve(window.YT.Player);
      return;
    }

    const priorCallback = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = () => {
      priorCallback?.();
      if (window.YT?.Player) resolve(window.YT.Player);
    };

    if (!document.querySelector('script[src="https://www.youtube.com/iframe_api"]')) {
      const tag = document.createElement('script');
      tag.src = 'https://www.youtube.com/iframe_api';
      document.head.append(tag);
    }
  });

const playerErrorMessage = (code: number | undefined, review: PlayerReview): string => {
  if (code === 100 || code === 101 || code === 150) {
    return review.host === 'youtube_private'
      ? 'YouTube did not allow embedded playback for this private review. Open the fallback link while signed into an approved Google account.'
      : 'YouTube did not allow embedded playback for this unlisted review. Open the fallback link to continue review.';
  }

  return 'YouTube playback is unavailable in this browser session. Open the fallback link to continue review.';
};

export function YouTubeReviewPlayer({
  review,
  chapters,
  transitionSamples,
}: YouTubeReviewPlayerProps) {
  const generatedId = useId().replaceAll(':', '');
  const iframeId = `youtube-review-${generatedId}`;
  const playerRef = useRef<YouTubePlayer | null>(null);
  const [status, setStatus] = useState('Loading YouTube review player.');
  const label = review.privacyStatus === 'unlisted' ? 'Unlisted YouTube Review' : 'YouTube Review';

  useEffect(() => {
    let mounted = true;

    ensureYouTubeApi().then((Player) => {
      if (!mounted) return;

      playerRef.current = new Player(iframeId, {
        events: {
          onReady: () => {
            setStatus('YouTube review player loaded.');
          },
          onError: (event) => {
            setStatus(playerErrorMessage(event.data, review));
          },
        },
      });
    });

    return () => {
      mounted = false;
    };
  }, [iframeId, review]);

  const jumpTo = (seconds: number, label: string) => {
    if (!playerRef.current) {
      setStatus('YouTube player is still loading.');
      return;
    }

    playerRef.current.seekTo(seconds, true);
    playerRef.current.playVideo();
    setStatus(`Review sample loaded at ${label}.`);
  };

  return (
    <section className={styles.playerPanel} aria-labelledby="review-video-heading">
      <div className={styles.sectionHeader}>
        <div>
          <p className={styles.eyebrow}>{label}</p>
          <h2 id="review-video-heading">Final Video</h2>
        </div>
        <a className={styles.inlineLink} href={review.watchUrl} target="_blank" rel="noreferrer">
          Open on YouTube
          <ExternalLink aria-hidden="true" />
        </a>
      </div>

      <div className={styles.videoFrame}>
        <iframe
          id={iframeId}
          title="YouTube review player"
          src={review.embedUrl}
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowFullScreen
        />
      </div>

      <p className={styles.playerStatus} role="status">{status}</p>

      <div className={styles.jumpGrid} aria-label="Review jump controls">
        {chapters.map((chapter) => (
          <button
            key={`${chapter.timestamp}-${chapter.title}`}
            type="button"
            className={styles.jumpButton}
            onClick={() => jumpTo(chapter.seconds, `${chapter.timestamp} ${chapter.title}`)}
          >
            <span>{chapter.timestamp}</span>
            {chapter.title}
          </button>
        ))}
        {transitionSamples.map((sample) => (
          typeof sample.seconds === 'number' ? (
            <button
              key={sample.label}
              type="button"
              className={styles.jumpButton}
              onClick={() => jumpTo(sample.seconds ?? 0, `${formatClock(sample.seconds ?? 0)} ${sample.label}`)}
            >
              <span>{formatClock(sample.seconds)}</span>
              {sample.label}
            </button>
          ) : null
        ))}
      </div>
    </section>
  );
}
