/* eslint-disable @next/next/no-img-element */
import { CheckCircle2, CircleAlert, Clock3, LockKeyhole, ShieldCheck } from 'lucide-react';

import { type PublishReadinessReviewManifest, type ReviewAsset } from '@/lib/reviews/publish-readiness';

import styles from './publish-readiness-review.module.css';
import { YouTubeReviewPlayer } from './youtube-review-player';

type PublishReadinessReviewProps = {
  manifest: PublishReadinessReviewManifest;
};

const boolLabel = (value: boolean): string => (value ? 'True' : 'False');

const lifecycleLabel = (value: PublishReadinessReviewManifest['lifecycleStage']): string => {
  if (value === 'inception') return 'Episode Inception Review';
  if (value === 'in_progress') return 'Production Review';
  return 'Publish Readiness Review';
};

const transitionJumpTargets = (assets: ReviewAsset[]): Array<{ label: string; seconds?: number }> =>
  assets.map((asset) => {
    const match = /(?:^|[_-])(\d{2,5})p(\d{1,3})(?:[_-]|$)/.exec(asset.path ?? asset.url);
    if (!match) return { label: asset.label };

    return {
      label: asset.label,
      seconds: Number(`${match[1]}.${match[2]}`),
    };
  });

function LockCard({ label, value }: { label: string; value: boolean }) {
  return (
    <div className={styles.lockCard}>
      <LockKeyhole aria-hidden="true" />
      <span>{label}</span>
      <strong>{boolLabel(value)}</strong>
    </div>
  );
}

function AssetFigure({ asset }: { asset: ReviewAsset }) {
  return (
    <figure className={styles.assetFigure}>
      <img src={asset.url} alt={asset.label} loading="lazy" />
      <figcaption>
        <strong>{asset.label}</strong>
        {asset.sha256 ? <span>{asset.sha256.slice(0, 12)}</span> : null}
      </figcaption>
    </figure>
  );
}

function TransitionSamples({ assets }: { assets: ReviewAsset[] }) {
  if (assets.length === 0) return null;

  return (
    <section className={styles.section} aria-labelledby="transition-samples-heading">
      <div className={styles.sectionHeader}>
        <div>
          <p className={styles.eyebrow}>Audio Evidence</p>
          <h2 id="transition-samples-heading">Transition Samples</h2>
        </div>
      </div>
      <div className={styles.audioGrid}>
        {assets.map((asset) => (
          <figure className={styles.audioCard} key={`${asset.label}-${asset.url}`}>
            <figcaption>
              <strong>{asset.label}</strong>
              {asset.sha256 ? <span>{asset.sha256.slice(0, 12)}</span> : null}
            </figcaption>
            <audio controls preload="metadata" src={asset.url}>
              <a href={asset.url}>Open audio sample</a>
            </audio>
          </figure>
        ))}
      </div>
    </section>
  );
}

function PendingVideoPanel({ manifest }: { manifest: PublishReadinessReviewManifest }) {
  return (
    <section className={styles.playerPanel} aria-labelledby="review-video-heading">
      <div className={styles.sectionHeader}>
        <div>
          <p className={styles.eyebrow}>Video Pending</p>
          <h2 id="review-video-heading">Review Video Not Attached</h2>
        </div>
        <Clock3 aria-hidden="true" className={styles.sectionIcon} />
      </div>
      <div className={styles.pendingVideo}>
        <p>
          This production review page was created at episode inception. The unlisted YouTube review embed appears here
          after a real proof or final review upload exists.
        </p>
        <dl className={styles.factList}>
          <div>
            <dt>Current lifecycle</dt>
            <dd>{lifecycleLabel(manifest.lifecycleStage)}</dd>
          </div>
          <div>
            <dt>Local review</dt>
            <dd>{manifest.localReviewUrl || 'Pending local packet review URL'}</dd>
          </div>
        </dl>
      </div>
      <p className={styles.accessNote}>No upload, publish, schedule, or visibility action is available from this page.</p>
    </section>
  );
}

export function PublishReadinessReview({ manifest }: PublishReadinessReviewProps) {
  const playerReview = manifest.youtubeReview
    ? {
        host: manifest.youtubeReview.host,
        watchUrl: manifest.youtubeReview.watchUrl,
        embedUrl: manifest.youtubeReview.embedUrl,
        privacyStatus: manifest.youtubeReview.privacyStatus,
      }
    : undefined;

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <p className={styles.eyebrow}>{lifecycleLabel(manifest.lifecycleStage)}</p>
        <h1>{manifest.episodeTitle}</h1>
      </header>

      <div className={styles.primaryGrid}>
        {playerReview ? (
          <YouTubeReviewPlayer
            review={playerReview}
            chapters={manifest.metadata.chapters}
            transitionSamples={transitionJumpTargets(manifest.assets.transitionSamples)}
          />
        ) : (
          <PendingVideoPanel manifest={manifest} />
        )}

        <aside className={styles.decisionPanel} aria-labelledby="decision-heading">
          <div className={styles.sectionHeader}>
            <div>
              <p className={styles.eyebrow}>Disposition</p>
              <h2 id="decision-heading">Review State</h2>
            </div>
            <ShieldCheck aria-hidden="true" className={styles.sectionIcon} />
          </div>

          <dl className={styles.factList}>
            <div>
              <dt>Status</dt>
              <dd>{manifest.status}</dd>
            </div>
            <div>
              <dt>Human disposition</dt>
              <dd>{manifest.humanDisposition}</dd>
            </div>
            <div>
              <dt>YouTube privacy</dt>
              <dd>{manifest.youtubeReview?.privacyStatus || 'pending unlisted review upload'}</dd>
            </div>
            <div>
              <dt>YouTube processing</dt>
              <dd>{manifest.youtubeReview?.processingStatus || 'pending review video'}</dd>
            </div>
          </dl>

          <div className={styles.lockGrid}>
            <LockCard label="Publish ready" value={manifest.locks.publishReady} />
            <LockCard label="YouTube upload ready" value={manifest.locks.youtubeUploadReady} />
            <LockCard label="Public release ready" value={manifest.locks.publicReleaseReady} />
            <LockCard label="May YouTube action" value={manifest.locks.mayYoutubeAction} />
            <LockCard label="Upload performed" value={manifest.locks.uploadPerformed} />
          </div>

          <div className={styles.blockerBox}>
            <h3>Remaining Blockers</h3>
            {manifest.blockers.length > 0 ? (
              <ul>
                {manifest.blockers.map((blocker) => (
                  <li key={blocker}>
                    <CircleAlert aria-hidden="true" />
                    {blocker}
                  </li>
                ))}
              </ul>
            ) : (
              <p>No blockers recorded in the remote manifest.</p>
            )}
          </div>
        </aside>
      </div>

      <section className={styles.section} aria-labelledby="metadata-heading">
        <div className={styles.sectionHeader}>
          <div>
            <p className={styles.eyebrow}>YouTube Metadata</p>
            <h2 id="metadata-heading">Public Copy Preview</h2>
          </div>
          <CheckCircle2 aria-hidden="true" className={styles.sectionIcon} />
        </div>
        <div className={styles.metadataGrid}>
          <div>
            <h3>Title</h3>
            <p>{manifest.metadata.title || 'Pending public title'}</p>
          </div>
          <div>
            <h3>Visibility</h3>
            <p>{manifest.metadata.visibility ?? 'Unlisted review only'}</p>
          </div>
          <div>
            <h3>Category</h3>
            <p>{manifest.metadata.category ?? 'Pending'}</p>
          </div>
          <div>
            <h3>Audience</h3>
            <p>{manifest.metadata.audience ?? 'Pending'}</p>
          </div>
        </div>
        <pre className={styles.description}>{manifest.metadata.description || 'Public description pending.'}</pre>
        <div className={styles.tagList}>
          {manifest.metadata.tags.map((tag) => <span key={tag}>{tag}</span>)}
        </div>
      </section>

      <section className={styles.section} aria-labelledby="qa-heading">
        <div className={styles.sectionHeader}>
          <div>
            <p className={styles.eyebrow}>Visual Evidence</p>
            <h2 id="qa-heading">QA Frames</h2>
          </div>
        </div>
        {manifest.assets.qaFrames.length > 0 ? (
          <div className={styles.frameGrid}>
            {manifest.assets.qaFrames.map((asset) => <AssetFigure key={`${asset.label}-${asset.url}`} asset={asset} />)}
          </div>
        ) : (
          <p className={styles.muted}>QA frames will appear after a reviewable proof or final render exists.</p>
        )}
      </section>

      <TransitionSamples assets={manifest.assets.transitionSamples} />
    </main>
  );
}
