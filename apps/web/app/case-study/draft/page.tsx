import type { Metadata } from 'next';
import Image from 'next/image';

import styles from './page.module.css';

const sourceBasis = [
  {
    source: 'Editorial frame',
    contribution:
      'The channel promise is to explain familiar failures through the hidden mechanism that made them consequential.',
  },
  {
    source: 'Episode records',
    contribution:
      'The first slate showed that each subject needed a different route into the same question: what changed, who missed it, and why it mattered.',
  },
  {
    source: 'Voice trials',
    contribution:
      'Early narration tests made clear that the channel needed a stable voice, not a new voice decision for every episode.',
  },
  {
    source: 'Visual experiments',
    contribution:
      'Particles, collage, generated stills, and motion tests exposed where visual energy could make the cause chain less legible.',
  },
  {
    source: 'Public identity',
    contribution:
      'Paper Architecture became the channel face, while episode video kept its own evidence rules.',
  },
] as const;

const pipelineRows = [
  {
    lane: 'Research',
    question: 'What actually changed?',
    result: 'A focused story problem instead of a topic recap.',
  },
  {
    lane: 'Script',
    question: 'Can the listener follow the cause chain?',
    result: 'Narration that has been challenged, tightened, and approved.',
  },
  {
    lane: 'Voice',
    question: 'Does the essay sound like the channel?',
    result: 'A stable voice track instead of a fresh voice experiment.',
  },
  {
    lane: 'Short-form video',
    question: 'Can a small cut stay source-led?',
    result:
      'A vertical piece that survives without becoming a detached explainer.',
  },
  {
    lane: 'Long-form',
    question: 'Can the audio essay hold attention without fake footage?',
    result: 'A Living Cover that gives the episode a body without rewriting evidence.',
  },
  {
    lane: 'Publishing',
    question: 'Does the public package match the approved story?',
    result: 'Titles, descriptions, and uploads that do not overpromise the work.',
  },
] as const;

const motionEvidence = [
  {
    src: '/brand/case-study/image-to-video/plume-invented-i2v-reject.mp4',
    poster: '/brand/case-study/image-to-video/plume-invented-i2v-reject.jpg',
    title: 'Plume invented',
    caption:
      'A normal-operations still picks up launch escalation the story did not ask for.',
  },
  {
    src: '/brand/case-study/image-to-video/hand-intrusion-i2v-reject.mp4',
    poster: '/brand/case-study/image-to-video/hand-intrusion-i2v-reject.jpg',
    title: 'Hand enters frame',
    caption: 'A clean evidence tray gains a new object at the edge of the shot.',
  },
  {
    src: '/brand/case-study/image-to-video/tray-rewrite-i2v-reject.mp4',
    poster: '/brand/case-study/image-to-video/tray-rewrite-i2v-reject.jpg',
    title: 'Tray rewrites itself',
    caption: 'The evidence layout collapses into a different physical object.',
  },
  {
    src: '/brand/case-study/image-to-video/status-wall-silhouette-i2v-reject.mp4',
    poster: '/brand/case-study/image-to-video/status-wall-silhouette-i2v-reject.jpg',
    title: 'Silhouette appears',
    caption: 'A wordless status-wall frame acquires a person the still never contained.',
  },
] as const;

export const metadata: Metadata = {
  title: 'Cascade Effects YouTube Channel Production System White Paper',
  description:
    'A white paper on the Cascade Effects YouTube channel production system, from mechanism-led research to voice, visuals, Living Covers, and public identity.',
  alternates: {
    canonical: '/case-study/draft',
  },
  robots: {
    index: false,
    follow: false,
    googleBot: {
      index: false,
      follow: false,
    },
  },
};

export default function CaseStudyDraftPage() {
  return (
    <main className={styles.page}>
      <article className={styles.paper}>
        <header className={styles.header}>
          <h1>Cascade Effects YouTube Channel: Production System White Paper</h1>
          <dl className={styles.meta}>
            <div>
              <dt>Status</dt>
              <dd>Working draft</dd>
            </div>
            <div>
              <dt>Date</dt>
              <dd>May 21, 2026</dd>
            </div>
          </dl>
        </header>

        <section className={styles.abstract} aria-labelledby="abstract">
          <h2 id="abstract">Abstract</h2>
          <p>
            Cascade Effects did not mature by finding a single visual style. The
            broader project record shows a production system taking shape around
            one editorial promise: familiar public failures should be explained
            through the hidden mechanism that made the consequence possible.
            That promise forced separate decisions for research, scripts,
            voiceover, visual evidence, motion, long-form carriers, public
            identity, metadata, and publishing.
          </p>
        </section>

        <nav className={styles.contents} aria-labelledby="contents">
          <h2 id="contents">Contents</h2>
          <ol>
            <li>
              <a href="#editorial-premise">Editorial Premise</a>
            </li>
            <li>
              <a href="#source-basis">Source Basis</a>
            </li>
            <li>
              <a href="#early-visual-search">Early Visual Search</a>
            </li>
            <li>
              <a href="#generated-video">Generated Video And Motion Failure</a>
            </li>
            <li>
              <a href="#governance-turn">Governance Turn</a>
            </li>
            <li>
              <a href="#voice-pipeline">Voice And Script Development</a>
            </li>
            <li>
              <a href="#living-cover-system">Living Cover System</a>
            </li>
            <li>
              <a href="#paper-architecture">Paper Architecture As Identity</a>
            </li>
            <li>
              <a href="#production-model">Production Model</a>
            </li>
            <li>
              <a href="#implications">Implications For The Designed Case Study</a>
            </li>
            <li>
              <a href="#motion-evidence">Appendix: Motion Evidence</a>
            </li>
          </ol>
        </nav>

        <section className={styles.section} id="editorial-premise">
          <h2>1. Editorial Premise</h2>
          <p>
            Cascade Effects starts from the idea that the viewer may already
            know the public headline, but not the mechanism. The recurring
            question is what shifted, who failed to recognize the shift, and how
            the system converted that blindness into consequence.
          </p>
          <p>
            That premise made the first-eight slate more than a topic list.
            Challenger, Therac-25, Hyatt Regency, Semmelweis, Tacoma Narrows,
            Piltdown Man, 737 MAX, and Titanic each test the same channel
            promise against a different kind of failure: warning signals,
            misplaced trust, absorbed revisions, rejected evidence, unmodeled
            forces, protected myths, hidden automation, and compliance mistaken
            for safety.
          </p>
        </section>

        <section className={styles.section} id="source-basis">
          <h2>2. Source Basis</h2>
          <p>
            This draft uses the project record as evidence, but the document is
            not meant to display the machinery of that record. The useful
            material is the pattern of decisions: what clarified the channel,
            what made the story harder to read, and what had to be separated
            before production could repeat.
          </p>
          <table className={styles.table}>
            <thead>
              <tr>
                <th scope="col">Evidence area</th>
                <th scope="col">What it clarifies</th>
              </tr>
            </thead>
            <tbody>
              {sourceBasis.map((item) => (
                <tr key={item.source}>
                  <th scope="row">{item.source}</th>
                  <td>{item.contribution}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className={styles.section} id="early-visual-search">
          <h2>3. Early Visual Search</h2>
          <p>
            Early work tried to make hidden mechanisms visible through one
            dominant visual language. Particle workbench tests made failure feel
            like break-up, drift, and dissolution. Collage reference boards
            led into FLUX-era generated stills, which pushed toward fragments,
            evidence-like objects, and compressed metaphors.
          </p>
          <p>
            Those passes were valuable because they failed honestly. Particles
            could turn a cause chain into atmosphere. Generated collage could
            make the viewer solve a visual riddle before the episode had earned
            it. Symbolic stills could look disciplined while losing the source
            anchor that made the story trustworthy.
          </p>
          <figure className={styles.figure}>
            <Image
              src="/brand/case-study/explorations/particle-workbench-dissolve.webp"
              alt="Archived particle workbench exploration showing a shuttle-like form dissolving into small points."
              width={1280}
              height={720}
              sizes="(max-width: 760px) 100vw, 760px"
            />
            <figcaption>
              Figure 1. Particle workbench tests gave failure motion and energy,
              but could pull the story toward atmosphere instead of evidence.
            </figcaption>
          </figure>
          <figure className={styles.figure}>
            <Image
              src="/brand/case-study/explorations/generated-collage-lookdev-candidate.webp"
              alt="Generated collage lookdev candidate combining control-room screens, shuttle fragments, torn-paper fields, and launch imagery."
              width={1280}
              height={720}
              sizes="(max-width: 760px) 100vw, 760px"
            />
            <figcaption>
              Figure 2. A generated collage lookdev candidate showed the
              opposite risk: too many visual claims made the mechanism harder
              to read.
            </figcaption>
          </figure>
        </section>

        <section className={styles.section} id="generated-video">
          <h2>4. Generated Video And Motion Failure</h2>
          <p>
            The next step was not pure abstraction. The work moved toward more
            realistic, evidence-based stills and then tried to carry them into
            image-to-video. The goal was not to fake documentary footage. It was
            to find a moving carrier that could hold a researched frame on
            screen.
          </p>
          <p>
            The tests exposed the constraint that the system still uses. A still
            and a moving sequence need separate approval. A frame can be useful,
            accurate enough to discuss, and still become misleading when motion
            invents objects, changes layouts, or adds a story beat the evidence
            never supported. The representative clips below and the fuller
            appendix set are evidence, not a visual style proposal.
          </p>
          <figure className={styles.motionReference}>
            <div className={styles.motionReferenceGrid}>
              {motionEvidence.slice(0, 2).map((clip) => (
                <div className={styles.motionReferenceItem} key={clip.src}>
                  <video
                    controls
                    muted
                    playsInline
                    preload="metadata"
                    poster={clip.poster}
                    aria-label={`${clip.title} rejected image-to-video test`}
                  >
                    <source src={clip.src} type="video/mp4" />
                  </video>
                  <p>
                    <strong>{clip.title}.</strong> {clip.caption}
                  </p>
                </div>
              ))}
            </div>
            <figcaption>
              Figure 3. Representative image-to-video rejects. The full set is
              retained in the appendix.
            </figcaption>
          </figure>
        </section>

        <section className={styles.section} id="governance-turn">
          <h2>5. Governance Turn</h2>
          <p>
            Once the visual experiments started failing in repeatable ways, the
            answer was not a better prompt. The answer was a cleaner separation
            of decisions. Sources, type, still frames, motion, narration,
            captions, and publishing copy each needed their own approval moment.
          </p>
          <p>
            That is why the archive matters. Old particles, collage boards,
            FLUX tests, trailer edits, and motion scouts are learning evidence.
            They do not become rules by being old. A constraint only becomes
            active when the current work names the decision it controls.
          </p>
        </section>

        <section className={styles.section} id="voice-pipeline">
          <h2>6. Voice And Script Development</h2>
          <p>
            Early narration work tested ChatGPT/OpenAI voice options before
            moving to ElevenLabs and the current Mike voice profile. The point
            was consistency: one recognizable voice makes quality easier to
            judge across episodes.
          </p>
          <p>
            The bigger change happened upstream. Research becomes a script, then
            the draft is reviewed with Claude, fact-checked, and revised. Notes
            are either incorporated or explicitly deferred before voiceover
            production begins.
          </p>
        </section>

        <section className={styles.section} id="living-cover-system">
          <h2>7. Living Cover System</h2>
          <p>
            The generated-video failures pushed the long-form answer away from
            full synthetic documentary footage. The better target was a stable
            carrier for the audio essay: approved source art, a fixed 16:9 frame,
            restrained ambient motion, timed text, music, and chapter moments.
          </p>
          <p>
            A Living Cover gives the episode a body without asking motion to
            invent the evidence. The viewer has something authored to watch, but
            the moving image stays subordinate to the approved story.
          </p>
          <table className={styles.table}>
            <thead>
              <tr>
                <th scope="col">Element</th>
                <th scope="col">Purpose</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <th scope="row">Stable frame</th>
                <td>
                  Gives the episode a visual anchor that can be reviewed before
                  motion is added.
                </td>
              </tr>
              <tr>
                <th scope="row">Scripted text</th>
                <td>
                  Keeps important words tied to the approved narration instead
                  of letting generated imagery invent them.
                </td>
              </tr>
              <tr>
                <th scope="row">Restrained motion</th>
                <td>
                  Adds life to the frame without changing the evidence or
                  creating new story events.
                </td>
              </tr>
              <tr>
                <th scope="row">Music and chapters</th>
                <td>
                  Give the essay pacing and structure without turning it into a
                  montage.
                </td>
              </tr>
            </tbody>
          </table>
        </section>

        <section className={styles.section} id="paper-architecture">
          <h2>8. Paper Architecture As Identity</h2>
          <p>
            Ink-Lit Paper Architecture solved a different problem. It gave the
            channel a recognizable public face: deep ink fields, cream paper
            forms, lavender shadows, cyan vellum signal paths, restrained coral
            warnings, and locally controlled title composition.
          </p>
          <p>
            That lane belongs on the website, YouTube channel surfaces, podcast
            and package assets, and selected gallery images. It does not become
            the default source art for Shorts or long-form documentary video.
            That separation is part of the production doctrine.
          </p>
          <figure className={styles.figure}>
            <Image
              src="/brand/youtube-channel/advanced-features-corrected-banner-20260520T210213Z/channel-banner-strip-2048x340.png"
              alt="Cascade Effects YouTube channel banner strip in the Ink-Lit Paper Architecture identity system."
              width={2048}
              height={340}
              sizes="(max-width: 760px) 100vw, 760px"
            />
            <figcaption>
              Figure 4. Paper Architecture gives the channel a public identity
              without presenting itself as documentary footage.
            </figcaption>
          </figure>
        </section>

        <section className={styles.section} id="production-model">
          <h2>9. Production Model</h2>
          <p>
            The coherent story across the repositories is not visual style
            evolution alone. It is a channel learning where decisions have to
            live. Research does not approve a script. A script does not approve
            audio. A still does not approve motion. A proof does not approve
            publishing. Each lane exists because an earlier shortcut created a
            real risk.
          </p>
          <table className={styles.table}>
            <thead>
              <tr>
                <th scope="col">Lane</th>
                <th scope="col">Question</th>
                <th scope="col">Result</th>
              </tr>
            </thead>
            <tbody>
              {pipelineRows.map((row) => (
                <tr key={row.lane}>
                  <th scope="row">{row.lane}</th>
                  <td>{row.question}</td>
                  <td>{row.result}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className={styles.section} id="implications">
          <h2>10. Implications For The Designed Case Study</h2>
          <p>
            The designed page should not present Cascade Effects as a brand
            refresh with production details attached. It should show how a
            mechanism-led editorial idea became a repeatable operating model.
            The visual journey matters, but it belongs inside the larger story:
            research, review, voice, evidence, motion, identity, metadata, and
            publishing all had to stop collapsing into one another.
          </p>
        </section>

        <section className={styles.appendix} id="motion-evidence">
          <h2>Appendix: Motion Evidence</h2>
          <p>
            These clips are included as rejected evidence from the
            image-to-video exploration. They document the failure mode that led
            to separate still and motion approval.
          </p>
          <ol className={styles.motionList}>
            {motionEvidence.map((clip) => (
              <li className={styles.motionItem} key={clip.src}>
                <video
                  controls
                  muted
                  playsInline
                  preload="metadata"
                  poster={clip.poster}
                  aria-label={`${clip.title} rejected image-to-video test`}
                >
                  <source src={clip.src} type="video/mp4" />
                </video>
                <p>
                  <strong>{clip.title}.</strong> {clip.caption}
                </p>
              </li>
            ))}
          </ol>
        </section>
      </article>
    </main>
  );
}
