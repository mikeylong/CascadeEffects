import type { Metadata } from 'next';
import Image from 'next/image';
import Link from 'next/link';
import { Play } from 'lucide-react';

import { SignalBrandmark } from '@/components/brand/signal-brandmark';
import { siteIdentity } from '@/lib/site-facts';
import styles from './page.module.css';

const failureImages = [
  {
    src: '/brand/case-study/explorations/particle-workbench-dissolve.webp',
    alt: 'Particle workbench image showing a shuttle-like form dissolving into white points on black.',
    title: 'Particle workbench',
    caption:
      'Failure as drift and breakup. Strong in-browser, weaker once rendered to video.',
  },
  {
    src: '/brand/case-study/explorations/generated-collage-lookdev-candidate.webp',
    alt: 'Generated collage test with launch imagery, control-room fragments, torn-paper fields, and shuttle references.',
    title: 'Generated collage',
    caption:
      'Strong visual energy, but too much distance from the evidence.',
  },
  {
    src: '/brand/case-study/explorations/collage-flux-stress-test.webp',
    alt: 'Collage reference and generated-image stress board with multiple symbolic subjects and paper fragments.',
    title: 'Collage stress test',
    caption:
      'The busier the image became, the harder the mechanism was to read.',
  },
] as const;

const motionRejects = [
  {
    src: '/brand/case-study/image-to-video/plume-invented-i2v-reject.mp4',
    poster: '/brand/case-study/image-to-video/plume-invented-i2v-reject.jpg',
    title: 'Invented plume',
    caption: 'The clip performs a launch event that was not in the approved image.',
  },
  {
    src: '/brand/case-study/image-to-video/hand-intrusion-i2v-reject.mp4',
    poster: '/brand/case-study/image-to-video/hand-intrusion-i2v-reject.jpg',
    title: 'Hand enters',
    caption: 'A new object enters and changes the meaning of the still.',
  },
  {
    src: '/brand/case-study/image-to-video/tray-rewrite-i2v-reject.mp4',
    poster: '/brand/case-study/image-to-video/tray-rewrite-i2v-reject.jpg',
    title: 'Tray rewrite',
    caption: 'The physical layout shifts into a different object once it moves.',
  },
  {
    src: '/brand/case-study/image-to-video/status-wall-silhouette-i2v-reject.mp4',
    poster: '/brand/case-study/image-to-video/status-wall-silhouette-i2v-reject.jpg',
    title: 'Added figure',
    caption: 'A clean status-wall image gains a person.',
  },
] as const;

const astronautMotionTests = [
  {
    src: '/brand/origin-story/shot02-astronaut-enters-system.webp',
    alt: 'Generated Challenger image-to-video test still showing an astronaut holding a helmet in front of the shuttle launch pad.',
    title: 'Shot 02: astronaut enters system',
    caption:
      'The still had a strong sense of arrival, but the motion tests kept pulling attention into helmet and hand drift.',
  },
  {
    src: '/brand/origin-story/shot07-chest-up-motion.webp',
    alt: 'Generated Challenger image-to-video test still showing a chest-up astronaut near the shuttle launch pad.',
    title: 'Shot 07: chest-up motion',
    caption:
      'The frame worked better as a controlled still than as generated movement. Face, hair, body, and launch-pad details moved too freely.',
  },
] as const;

export const metadata: Metadata = {
  title: 'Cascade of Effects Origin Story',
  description:
    'A first-person origin story for Cascade of Effects: why it uses artificial intelligence, how the visual language evolved, and where the evidence sets the limits.',
  alternates: {
    canonical: '/origin-story',
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

export default function OriginStoryPage() {
  return (
    <main className={styles.page}>
      <header className={styles.siteHeader}>
        <Link className={styles.siteBrand} href="/" aria-label={siteIdentity.title}>
          <SignalBrandmark className={styles.siteBrandMark} />
          <span className={styles.siteBrandWordmark}>{siteIdentity.title}</span>
        </Link>

        <a
          className={styles.siteHeaderLink}
          href={siteIdentity.youtubeWatchUrl}
          target="_blank"
          rel="noreferrer"
          aria-label="Watch on YouTube"
        >
          <Play className={styles.siteHeaderLinkIcon} aria-hidden="true" />
          <span className={styles.siteHeaderLinkLabelFull}>Watch on YouTube</span>
          <span className={styles.siteHeaderLinkLabelCompact}>YouTube</span>
        </a>
      </header>

      <article className={styles.story}>
        <header className={styles.intro}>
          <h1 className={styles.kicker}>Origin Story</h1>
          <p className={styles.introText}>
            I&apos;m using artificial intelligence to create narratives that explain
            the warning signs in systems that become overly complex, overly
            trusted, and overly expedited: factors that prevent us from
            recognizing problems before it&apos;s too late.
          </p>
        </header>

        <section className={styles.section} aria-labelledby="why-i-started">
          <h2 id="why-i-started">How it started</h2>
          <p>
            I&apos;ve mostly focused on creating software and interfaces for my AI
            projects. That work had value, but it was narrow. I wanted to apply
            AI to researched stories with voice, visuals, music, motion, and
            enough production discipline that the result did not feel
            disposable.
          </p>
          <p>
            I didn&apos;t set out to create a channel that&apos;s just for fun with AI. I
            wanted a production system that could get serious documentary
            stories out faster than a traditional manual workflow could manage.
          </p>
        </section>

        <section className={styles.section} aria-labelledby="why-failures">
          <h2 id="why-failures">Why I chose &quot;system failures&quot;</h2>
          <p>
            System failures are fascinating because they&apos;re both a part of our
            history and something we&apos;re dealing with right now. They impacted
            specific people, places, and situations due to unique technical and
            organizational factors. The patterns we observe aren&apos;t just from the
            past.
          </p>
          <p>
            We&apos;re constantly building more systems, and we&apos;re doing it super
            fast. AI is becoming more integrated into and influencing software
            systems, tools, machines, and essential activities. By reflecting on
            the past, we can gain valuable insights, or we might risk living in
            a bubble, thinking these failures are just old news.
          </p>
          <p>
            When I first started, I wasn&apos;t super familiar with these stories. I
            knew about Challenger and the Tacoma Narrows Bridge, but not the
            specifics. Therac-25 and the Hyatt Regency were completely new to
            me. As I researched, I kept finding more, and the project taught me
            along the way.
          </p>
        </section>

        <section className={styles.section} aria-labelledby="ai-rule">
          <h2 id="ai-rule">Created with the assistance of AI, but not solely by AI</h2>
          <p>
            The Cascade of Effects series bible comprises 186 episodes. Given the
            sheer number of episodes, the project cannot be a one-time endeavor.
            It necessitates a repeatable model to ensure the continuity of
            research, writing, production, review, and publishing. The rule was
            straightforward yet challenging to uphold: AI could be integrated
            into nearly every aspect of production, but the final product should
            not appear as if it was created by AI.
          </p>
          <p>
            I am transparent about the tools utilized in the creation of the
            project. The Living Cover image backplates, ambient effects, my
            voice, and the music tracks were all generated by artificial
            intelligence. Furthermore, the episode assembly code was also
            created by AI. While these tools are undoubtedly essential, they do
            not constitute the primary focus of the episodes.
          </p>
          <p>
            The primary limitation of the episodes is that AI can generate
            images, voiceovers, or moving frames, but it cannot fabricate
            evidence. This project relies on research and a script. The
            voiceover accurately presents the facts. A still image can be
            reviewed and corrected. However, generated video often introduced
            inaccurate motion and grossly altered details, creating plausible
            footage that the evidence does not support. This crossed the line in
            this project.
          </p>
        </section>

        <section className={styles.section} aria-labelledby="what-failed">
          <h2 id="what-failed">Exploring visual expressions</h2>
          <p>
            The initial promising direction was particle workbench development.
            I created an AI-assisted app with sliders that powered 3D particle
            simulations using open-source 3D models. The ethereal yet detailed
            feel of this approach was quite unexpected. A tool that would have
            been too expensive to develop as a side project became an instant
            tool for testing the direction. It also revealed the need for review
            points: moments to pause, examine the results, and determine if it
            was contributing to the project or simply becoming captivating on
            its own.
          </p>

          <div className={styles.figureGrid} aria-label="Early visual tests">
            {failureImages.map((image) => (
              <figure className={styles.figure} key={image.src}>
                <Image
                  src={image.src}
                  alt={image.alt}
                  width={1280}
                  height={720}
                  sizes="(max-width: 760px) 100vw, 32vw"
                />
                <figcaption>
                  <strong>{image.title}.</strong> {image.caption}
                </figcaption>
              </figure>
            ))}
          </div>

          <p>
            The particles, despite appearing crisp in the browser, failed to
            serve as an effective visual language when compressed for YouTube.
            This compression resulted in a significant loss of their original
            functionality, ultimately requiring excessive time and effort for a
            marginal result.
          </p>
          <p>
            A second direction focused on AI-generated collage compositions.
            While visually appealing, these compositions often deviated from the
            original evidence. For instance, the Challenger disaster could be
            depicted as a sci-fi-inspired rocket-like object instead of the
            actual space shuttle, and large O-rings could be transformed into an
            unusual evidence tray of tiny rings. Furthermore, this style risked
            becoming overly reliant on the aesthetic of established collage
            artists.
          </p>
          <p>
            Image-to-video technology, while promising, proved inefficient and
            cost-prohibitive. While the technology is great at creating a few
            seconds of motion content, the approach was insufficient to create a
            twenty-minute episode or scale to a channel with a substantial
            backlog of content.
          </p>

          <p>
            The female astronaut tests made that boundary concrete. I was not
            trying to create fake Challenger footage. I was testing whether a
            generated still could carry a researched emotional beat into motion.
            The stills had promise. The motion did not.
          </p>

          <div
            className={styles.motionStillGrid}
            aria-label="Challenger astronaut image-to-video tests"
          >
            {astronautMotionTests.map((image) => (
              <figure className={styles.motionStillFigure} key={image.src}>
                <Image
                  src={image.src}
                  alt={image.alt}
                  width={941}
                  height={1672}
                  sizes="(max-width: 760px) 100vw, 28vw"
                />
                <figcaption>
                  <strong>{image.title}.</strong> {image.caption}
                </figcaption>
              </figure>
            ))}
          </div>

          <div className={styles.motionGrid} aria-label="Rejected image-to-video clips">
            {motionRejects.map((clip) => (
              <figure className={styles.videoFigure} key={clip.src}>
                <video
                  controls
                  muted
                  playsInline
                  preload="metadata"
                  poster={clip.poster}
                  aria-label={`${clip.title} image-to-video reject`}
                >
                  <source src={clip.src} type="video/mp4" />
                </video>
                <figcaption>
                  <strong>{clip.title}.</strong> {clip.caption}
                </figcaption>
              </figure>
            ))}
          </div>
        </section>

        <section className={styles.section} aria-labelledby="three-lanes">
          <h2 id="three-lanes">Three production lanes</h2>
          <p>
            Long-form episodes transformed into what I refer to as Living
            Covers. A Living Cover is a single, authored image that captures a
            frozen moment from the story. Beneath the narration, subtle,
            controlled motion is introduced. Atmospheric elements and lights
            shift and shimmer, while caption text smoothly scrolls through the
            composition. The frame remains still enough to allow the viewer to
            think without being abruptly cut off. This single image grants me
            composition control, making it easier to repair and mask.
            Additionally, code-driven motion ensures consistent rendering across
            delivery mediums.
          </p>

          <figure className={styles.wideFigure}>
            <Image
              src="/brand/case-study/process/challenger-source-pixel-matte-route-overlay.webp"
              alt="Challenger Living Cover process overlay showing matte regions and aircraft flight-path tests."
              width={1920}
              height={1080}
              sizes="(max-width: 760px) 100vw, 880px"
            />
            <figcaption>
              <strong>Living Cover process.</strong> The source image becomes a
              permission map: motion can pass through the open sky, but the
              shuttle and tower stay fixed.
            </figcaption>
          </figure>

          <p>
            YouTube Shorts videos have their own guidelines. When archival
            footage is compelling and the rights situation is clear, it can
            achieve something that generated media cannot: capture a genuine
            moment in time. However, this also means that Shorts cannot be
            mandated for every episode. Some subjects have the appropriate
            amount of quality source material, while others do not.
          </p>
          <p>
            The third lane, which I like to call Ink-Lit Paper Architecture, is
            what makes the channel unique. It&apos;s all about paper sculptures that
            represent the episodes, glowing from inside like ink flowing through
            them. You can see this idea on the website, channel art, and gallery
            pieces. It&apos;s not something we use to prove anything in the episodes.
            If every episode were turned into a paper sculpture, the long videos
            would feel like stepping into a paper world instead of being based
            on real stories.
          </p>

          <p>
            The phrase &quot;Paper Architecture&quot; originated from the music-making
            process. One of the song titles the AI generated was &quot;Paper
            Architecture,&quot; and the lyric &quot;fragile architecture can&apos;t hold water&quot;
            lingered in my mind. Consequently, the paper collage direction was
            abandoned, but the signals about fragility remained.
          </p>
        </section>

        <section className={styles.section} aria-labelledby="authorship">
          <h2 id="authorship">The definition of authorship</h2>
          <p>
            I still hesitate to call myself an &quot;artist&quot; in this project, partly
            because AI-generated work complicates the question. I understand the
            dilemma: is this art, or am I merely typing prompts into a computer?
            I share some of that skepticism myself.
          </p>
          <p>
            Cascade of Effects has never felt like prompt engineering. Instead, it
            has been more akin to directing a living media system. I set the
            initial premise, designed the workflow, selected what survived,
            rejected regressions, and determined when something constituted
            evidence, interpretation, or simply an intriguing failure.
          </p>
          <p>
            I didn&apos;t directly engage with the historical evidence. Instead, I
            modified the system responsible for discovering, curating, and
            utilizing it.
          </p>
          <p>
            If &quot;artist&quot; is the appropriate term, it&apos;s not because I meticulously
            hand-crafted every pixel. Rather, it&apos;s because I make the decisions:
            what to retain, what to discard, and what the generated material can
            represent.
          </p>
        </section>

        <section className={styles.section} aria-labelledby="trust">
          <h2 id="trust">Maintaining trust and good judgment</h2>
          <p>
            The Living Cover concept is designed to be a reflective experience
            rather than provocative or overstimulating. The format allows viewers
            to listen, comfortably read, and immerse themselves in the story.
            Small animated details keep the experience engaging without turning
            the episode into a spectacle.
          </p>
          <p>
            I am not inclined to support Cascade of Effects in celebrating
            disasters or death. These narratives carry significant weight
            because real individuals were impacted, and we should refrain from
            utilizing that impact for shock value. In certain episodes,
            individuals are depicted, but their faces are obscured. This is
            intentional. We can incorporate individuals into the narrative
            without reducing them to mere plot devices for the audience.
          </p>
          <p>
            By the conclusion of an episode, I aspire for the viewer to harbor
            confidence in the meticulous research conducted, the impartial
            treatment of evidence, and the compassionate consideration extended
            to those impacted by the narrative.
          </p>
          <p>
            Furthermore, I aim to encourage the viewer to carry the pattern into
            the present. These failures were not due to a lack of sophistication
            in the past. Systems naturally deviate, organizations normalize
            risk, warning signs are disregarded, and trust is incorrectly placed
            on technology.
          </p>
          <p>
            The incorrect conclusion is that we have learned our lessons from
            the past and confidently move on. We remain vulnerable.
          </p>
        </section>

        <section className={styles.section} aria-labelledby="next">
          <h2 id="next">Looking to the future</h2>
          <p>
            Cascade of Effects is constructed around historical failures, yet the
            concerns about the present remain in the background. The episodes
            don&apos;t need to pause and explicitly state that they revolve around
            present-day risks. The connection is already evident: the stories are
            being created using AI at a time when AI is becoming an integral part
            of the environments and machines where future failures may
            originate.
          </p>
          <p>
            I frequently revisit a recurring thought: the warning signs are
            evident, but the disaster has yet to occur.
          </p>
        </section>
      </article>
    </main>
  );
}
