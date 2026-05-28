#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const EPISODES_ROOT = "/Users/mike/Episodes_CascadeEffects";
const REVIEW_ROOT = path.join(EPISODES_ROOT, "first_eight_lesson_takeaway_review");
const REVIEW_PAGE_PATH = path.join(EPISODES_ROOT, "first-eight-lesson-takeaway-review.html");
const REVIEW_SERVER_BASE_URL = "http://127.0.0.1:8766";
const MODEL_ID = "lesson_takeaway_highlight_v1";
const SEMANTIC_ROLE = "story_lesson_takeaway";
const DENSITY_MODEL = "memorable_takeaway_cadence_v1";
const CANDIDATE_STATUS = "candidate_pending_human_review";
const GENERATED_AT_UTC = process.env.SOURCE_DATE_EPOCH
  ? new Date(Number(process.env.SOURCE_DATE_EPOCH) * 1000).toISOString()
  : new Date().toISOString();
const STAMP = GENERATED_AT_UTC.replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");

const EPISODES = [
  {
    episode_id: "therac-25",
    title: "Therac-25",
    target_count: 28,
    manifest_path:
      "/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/rough_assembly/therac-25_rolling_caption_rail_rough_proof_20260522T223902Z/rough_assembly_manifest.json",
  },
  {
    episode_id: "hyatt-regency",
    title: "Hyatt Regency",
    target_count: 22,
    manifest_path:
      "/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt-regency_rolling_caption_rail_rough_proof_20260522T223902Z/rough_assembly_manifest.json",
  },
  {
    episode_id: "semmelweis",
    title: "Semmelweis",
    target_count: 22,
    manifest_path:
      "/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/youtube/rough_assembly/semmelweis_rolling_caption_rail_rough_proof_20260522T223902Z/rough_assembly_manifest.json",
  },
  {
    episode_id: "tacoma-narrows",
    title: "Tacoma Narrows",
    target_count: 22,
    manifest_path:
      "/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_rough_proof_20260522T223902Z/rough_assembly_manifest.json",
  },
  {
    episode_id: "piltdown-man",
    title: "Piltdown Man",
    target_count: 22,
    manifest_path:
      "/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/youtube/rough_assembly/piltdown-man_rolling_caption_rail_rough_proof_20260522T223902Z/rough_assembly_manifest.json",
  },
  {
    episode_id: "737-max",
    title: "737 MAX",
    target_count: 25,
    manifest_path:
      "/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/youtube/rough_assembly/737-max_rolling_caption_rail_rough_proof_20260522T223902Z/rough_assembly_manifest.json",
  },
  {
    episode_id: "titanic",
    title: "Titanic",
    target_count: 20,
    manifest_path:
      "/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/youtube/rough_assembly/titanic_rolling_caption_rail_rough_proof_20260522T223902Z/rough_assembly_manifest.json",
  },
];

const MANUAL_CANDIDATE_PHRASES = {
  "therac-25": [
    "She says something went wrong",
    "system earns trust it was never tested",
    "The machine exists to hold that margin",
    "machine must not fire",
    "patient would still be safe",
    "code was already proven",
    "never been tested operating alone",
    "treated as proof that no problem existed",
    "safety net was removed",
    "skip the safety check",
    "machine earns trust it does not deserve",
    "track record belonged to a different context",
    "interface trained them to override warnings",
    "the data won",
    "safety that had never been stress-tested",
    "safety systems made such an overdose impossible",
    "machine was not responsible",
    "machine was fundamentally sound",
    "designed to confirm safety",
    "failure to prove itself",
    "no independent safety monitoring",
    "not designed to communicate danger",
    "software lived in a gap",
    "designed to trust itself",
    "safety layer is treated as simplification",
    "trust in systems that are too complex",
    "conditions where it could fail",
    "trust is the kind that has never been tested",
  ],
  "hyatt-regency": [
    "designed to feel like an occasion",
    "lost the ability to recognize it",
    "logic of that system is worth pausing",
    "looked like a minor adjustment",
    "approved with no load recalculation",
    "fabrication was inconvenient",
    "pass through the system unchecked",
    "responsible for verifying the load path",
    "fabrication convenience, not redesign",
    "behavior of the system may have changed",
    "does this change the load path",
    "warning signs during construction did not trigger",
    "signals about system-level weakness",
    "best opportunity to find problems",
    "already-deficient system into certainty",
    "no single person had made a decision",
    "process absorbed into a category labeled routine",
    "why the system did not require one",
    "changes the load path",
    "category that does not require deep review",
    "crossed a category boundary",
    "system worked exactly as designed",
  ],
  "semmelweis": [
    "problem it could measure but not explain",
    "difference was documented",
    "death rates told a story",
    "look directly at evidence",
    "This was not a subtle difference",
    "Semmelweis examined all of them",
    "Second Division midwives did not perform autopsies",
    "Not plain soap and water",
    "evidence actually required the profession to believe",
    "preserved the assumption",
    "results within weeks",
    "data-driven discipline should have moved decisively",
    "absence of a theoretical framework",
    "accepting the evidence meant accusing the physicians themselves",
    "evidence was too strong",
    "persistence in the face of accumulating evidence",
    "wrong in a specific, structural way",
    "resistance hardened",
    "handwashing become standard practice",
    "easier to absorb",
    "institution could afford to believe it",
    "cost of believing it was too high",
  ],
  "tacoma-narrows": [
    "motion changed the air around it",
    "feedback cycle the design had never been tested against",
    "outside the design process",
    "not the one that got built",
    "lightness and grace looked like the future",
    "made the motion easier to categorize",
    "Visible anomaly had been normalized",
    "design framework of the time",
    "advanced engineering within the limits",
    "wind mainly as a static load",
    "not as something that changed",
    "helping create the conditions",
    "discount the warning",
    "lessons were learned after the bridge fell",
    "wind did not need to become a hurricane",
    "bridge did not merely fail in the wind",
    "new engineering answer to a newly formalized problem",
    "domain itself had an edge",
    "not dynamically vetted against that problem",
    "framework that has not yet formalized a real risk",
    "trusted model stopped matching the world",
    "boundary of a model",
  ],
  "piltdown-man": [
    "precisely the kind of evolutionary missing link",
    "accepted for forty-one years",
    "not because the evidence was strong",
    "already prepared to believe",
    "fit this model precisely",
    "cost of the alternative was high",
    "exactly what was needed",
    "taken as evidence that it was real",
    "social cost of sustained public skepticism",
    "pattern of inconsistencies was never assembled",
    "story outran the quality of the evidence",
    "provenance was not independently controlled",
    "evidentiary basis had become almost invisible",
    "systematic analysis using microscopy",
    "institutional will to demand investigation",
    "forger is less significant than the question",
    "already disposed to accept it",
    "right credentials, at the right moment",
    "lenses were not designed to ask",
    "Forty-one years is not evidence of stupidity",
    "institutional belief can do",
    "evidence was too good to be true",
  ],
  "737-max": [
    "same automated system",
    "depended on a single sensor",
    "pilot cannot clearly see",
    "commonality was not incidental",
    "changed the aircraft's aerodynamic behavior",
    "make it fly like one",
    "special pilot awareness",
    "single angle-of-attack sensor",
    "system was not described",
    "familiar aircraft with improved engines",
    "system was hidden from pilots not through malice",
    "The crew encountered the same system",
    "competitive business pressure became a design requirement",
    "outcome that threatened the commonality argument",
    "system originally designed",
    "qualitatively different from what had originally been certified",
    "calibrated to the system's origin",
    "single point of failure",
    "pilots to recognize a failure mode",
    "decision not to name or describe MCAS",
    "commercial argument and the safety argument",
    "architectural question",
    "sufficient independent review",
    "commercial constraint became a design requirement",
    "pilots had been given what they needed",
  ],
  titanic: [
    "law was measuring the wrong thing",
    "They began with a category",
    "Titanic was far beyond the world",
    "the world changes around it",
    "table had stopped tracking the scale",
    "law did not say, count the people",
    "old rule had a simpler answer ready",
    "minimum into a signal of adequacy",
    "rulebook was the smaller imagination",
    "safety system would have had to think",
    "reduced that system to a table",
    "smaller version of the risk",
    "law had turned scale into a category",
    "A mature safety system does not pick",
    "Then the proof arrives all at once",
    "question was no longer just",
    "failure was already present in the table",
    "category built for yesterday's ship",
    "law had stopped measuring the ships",
    "reality audits the system",
  ],
};

const LESSON_TERMS = new Set(
  [
    "ability",
    "absorbed",
    "accepted",
    "accountability",
    "answer",
    "architecture",
    "assumption",
    "authority",
    "boundary",
    "burden",
    "category",
    "changed",
    "condition",
    "cost",
    "decision",
    "designed",
    "discipline",
    "evidence",
    "failure",
    "fail",
    "failed",
    "framework",
    "hidden",
    "ignore",
    "implied",
    "institutional",
    "law",
    "margin",
    "measured",
    "model",
    "normal",
    "ordinary",
    "process",
    "proof",
    "question",
    "recognize",
    "require",
    "risk",
    "routine",
    "safety",
    "standard",
    "system",
    "tested",
    "trust",
    "visible",
    "warning",
    "wrong",
  ].flatMap((term) => [term, `${term}s`]),
);

const FILLER_WORDS = new Set([
  "a",
  "an",
  "and",
  "are",
  "as",
  "at",
  "be",
  "by",
  "for",
  "from",
  "in",
  "is",
  "it",
  "of",
  "on",
  "or",
  "that",
  "the",
  "then",
  "this",
  "to",
  "was",
  "were",
  "when",
  "with",
]);

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJson(filePath, value) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`);
}

function sha256File(filePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function secondsFromTimestamp(timestamp) {
  const [hours, minutes, rest] = timestamp.split(":");
  const [seconds, milliseconds = "0"] = rest.split(".");
  return Number(hours) * 3600 + Number(minutes) * 60 + Number(seconds) + Number(milliseconds.padEnd(3, "0")) / 1000;
}

function formatTimestamp(seconds) {
  const value = Math.max(0, Number(seconds) || 0);
  const minutes = Math.floor(value / 60);
  const secs = Math.floor(value % 60);
  return `${minutes}:${String(secs).padStart(2, "0")}`;
}

function cleanText(value) {
  return String(value || "")
    .replace(/<[^>]+>/g, "")
    .replace(/[“”]/g, "\"")
    .replace(/[‘’]/g, "'")
    .replace(/\s+/g, " ")
    .trim();
}

function parseVtt(vttPath) {
  const blocks = fs.readFileSync(vttPath, "utf8").split(/\n\n+/);
  const cues = [];
  for (const block of blocks) {
    const lines = block.trim().split(/\n/).filter(Boolean);
    const timeLineIndex = lines.findIndex((line) => line.includes("-->"));
    if (timeLineIndex === -1) continue;
    const [startRaw, endRaw] = lines[timeLineIndex].split("-->").map((part) => part.trim().split(/\s+/)[0]);
    const text = cleanText(lines.slice(timeLineIndex + 1).join(" "));
    if (!text) continue;
    cues.push({
      start: secondsFromTimestamp(startRaw),
      end: secondsFromTimestamp(endRaw),
      text,
    });
  }
  return cues;
}

function buildTextIndex(cues) {
  const pieces = [];
  let cursor = 0;
  for (const cue of cues) {
    const prefix = pieces.length ? " " : "";
    const start = cursor + prefix.length;
    pieces.push(prefix, cue.text);
    cursor = start + cue.text.length;
    cue.char_start = start;
    cue.char_end = cursor;
  }
  return pieces.join("");
}

function sentenceItems(cues) {
  const out = [];
  let current = "";
  let start = null;
  let end = null;
  for (const cue of cues) {
    if (start === null) start = cue.start;
    end = cue.end;
    current = cleanText(`${current} ${cue.text}`);
    const parts = current.split(/(?<=[.!?])\s+/);
    while (parts.length > 1) {
      const text = parts.shift().trim();
      if (text.split(/\s+/).length >= 5) out.push({ start, end, text });
      start = cue.start;
    }
    current = parts.join(" ");
  }
  if (current.trim()) out.push({ start: start || 0, end: end || start || 0, text: current.trim() });
  return out;
}

function wordTokens(text) {
  const tokens = [];
  const regex = /[\p{L}\p{N}][\p{L}\p{N}'-]*/gu;
  let match;
  while ((match = regex.exec(text))) {
    tokens.push({
      raw: match[0],
      lower: match[0].toLowerCase(),
      start: match.index,
      end: match.index + match[0].length,
    });
  }
  return tokens;
}

function wordCount(text) {
  return wordTokens(text).length;
}

function phraseFromTokens(sentence, tokens, startIndex, length) {
  const first = tokens[startIndex];
  const last = tokens[startIndex + length - 1];
  return sentence.slice(first.start, last.end);
}

function phraseScore(phrase, sentenceText, sentenceStart) {
  const words = wordTokens(phrase);
  if (words.length < 2 || words.length > 9) return -Infinity;
  const first = words[0].lower;
  const last = words[words.length - 1].lower;
  if (/[,;:]/.test(phrase)) return -Infinity;
  if (["and", "or", "but", "because", "while", "with", "from", "into", "onto"].includes(first)) return -Infinity;
  if (
    [
      "and",
      "or",
      "but",
      "the",
      "a",
      "an",
      "of",
      "to",
      "in",
      "as",
      "with",
      "was",
      "were",
      "is",
      "are",
      "had",
      "has",
      "have",
      "not",
      "did",
      "do",
      "could",
      "would",
      "should",
      "been",
      "being",
      "become",
      "because",
      "than",
      "if",
    ].includes(last)
  ) {
    return -Infinity;
  }
  const lowerSentence = sentenceText.toLowerCase();
  const lowerPhrase = phrase.toLowerCase();
  const uniqueTerms = new Set(words.map((word) => word.lower.replace(/'s$/, "")));
  let score = 0;
  for (const term of uniqueTerms) {
    if (LESSON_TERMS.has(term)) score += 6;
    if (!FILLER_WORDS.has(term) && term.length > 5) score += 0.45;
  }
  if (/\b(not|never|no|without|rather than|instead of)\b/i.test(phrase)) score += 4;
  if (/\b(system|process|framework|model|category|law|rule|standard|question|evidence|proof|trust|warning|decision|safety)\b/i.test(phrase)) {
    score += 7;
  }
  if (/\bwhat happens\b|\bwhat failed\b|\bwhy the system\b|\bthe deeper failure\b|\bthe question\b/i.test(lowerSentence)) score += 5;
  if (/\bnot\b.*\bbut\b/i.test(lowerSentence)) score += 4;
  if (/\bwas not\b|\bdid not\b|\bcould not\b/i.test(lowerPhrase)) score += 3;
  if (words.length >= 4 && words.length <= 7) score += 5;
  if (words.length === 2) score -= 5;
  if (sentenceStart < 12 && /\b(on|in|by|at)\b/i.test(first)) score -= 4;
  if (/\b(july|november|december|october|march|pm|a\.m|miles|feet|degrees|percent|people|patients)\b/i.test(lowerPhrase)) {
    score -= 5;
  }
  return score;
}

function bestPhraseForSentence(sentence) {
  const tokens = wordTokens(sentence.text);
  let best = null;
  const exactCandidates = [];
  const sentenceWithoutPeriod = sentence.text.replace(/[.!?]+$/g, "").trim();
  if (wordCount(sentenceWithoutPeriod) <= 9) exactCandidates.push({ phrase: sentenceWithoutPeriod, fragmentBonus: 7 });
  for (const part of sentence.text.split(/[,;:]/)) {
    const phrase = part.replace(/[.!?]+$/g, "").trim();
    const count = wordCount(phrase);
    if (count >= 2 && count <= 9) exactCandidates.push({ phrase, fragmentBonus: 6 });
  }
  for (const candidate of exactCandidates) {
    const score = phraseScore(candidate.phrase, sentence.text, sentence.start) + candidate.fragmentBonus;
    if (!best || score > best.score) best = { phrase: candidate.phrase, score };
  }
  for (let start = 0; start < tokens.length; start += 1) {
    for (let length = 2; length <= 9 && start + length <= tokens.length; length += 1) {
      const phrase = phraseFromTokens(sentence.text, tokens, start, length);
      const score = phraseScore(phrase, sentence.text, sentence.start);
      if (!best || score > best.score) best = { phrase, score };
    }
  }
  return best;
}

function proofUrlAtTime(manifest, seconds) {
  const base = manifest.review_url || manifest.proof_build_json_url || "";
  const playerPath = manifest.proof_artifacts?.player_html_path || manifest.player_path;
  const url = base && base.includes("player.html")
    ? new URL(base)
    : new URL(`${REVIEW_SERVER_BASE_URL}/${path.relative(EPISODES_ROOT, playerPath).split(path.sep).map(encodeURIComponent).join("/")}`);
  url.searchParams.set("t", Number(seconds).toFixed(1));
  return url.toString();
}

function findPhraseTiming(fullText, cues, phrase) {
  const phraseIndex = fullText.indexOf(phrase);
  if (phraseIndex === -1) return null;
  const phraseEnd = phraseIndex + phrase.length;
  const startCue = cues.find((cue) => phraseIndex >= cue.char_start && phraseIndex <= cue.char_end) || cues.find((cue) => cue.char_end >= phraseIndex);
  const endCue = cues.find((cue) => phraseEnd >= cue.char_start && phraseEnd <= cue.char_end) || startCue;
  const priorText = fullText.slice(0, phraseIndex);
  const tokenStart = wordCount(priorText);
  const tokenEnd = tokenStart + wordCount(phrase);
  return {
    start: startCue?.start ?? 0,
    end: endCue?.end ?? startCue?.end ?? 0,
    normalized_script_token_range: [tokenStart, tokenEnd],
  };
}

function contextForPhrase(fullText, phrase) {
  const index = fullText.indexOf(phrase);
  if (index === -1) return "";
  const start = Math.max(0, index - 150);
  const end = Math.min(fullText.length, index + phrase.length + 150);
  return cleanText(`${start > 0 ? "..." : ""}${fullText.slice(start, end)}${end < fullText.length ? "..." : ""}`);
}

function chooseCandidates({ episode, manifest, cues, sentences, fullText }) {
  const manualPhrases = MANUAL_CANDIDATE_PHRASES[episode.episode_id] || [];
  if (manualPhrases.length) {
    return manualPhrases
      .map((phrase) => ({
        phrase,
        timing: findPhraseTiming(fullText, cues, phrase),
      }))
      .sort((a, b) => (a.timing?.start ?? 0) - (b.timing?.start ?? 0))
      .map(({ phrase, timing }, index) => {
      return {
        candidate_id: `${episode.episode_id}_takeaway_candidate_${String(index + 1).padStart(2, "0")}`,
        episode_id: episode.episode_id,
        episode_title: episode.title,
        phrase_text: phrase,
        word_count: wordCount(phrase),
        timing_window_seconds: [
          Number((timing?.start ?? 0).toFixed(3)),
          Number((timing?.end ?? timing?.start ?? 0).toFixed(3)),
        ],
        normalized_script_token_range: timing?.normalized_script_token_range || [0, 0],
        nearby_script_context: timing ? contextForPhrase(fullText, phrase) : "PHRASE_NOT_FOUND",
        proof_review_url: proofUrlAtTime(manifest, timing?.start ?? 0),
        caption_highlight_model_id: MODEL_ID,
        highlight_semantic_role: SEMANTIC_ROLE,
        highlight_density_model: DENSITY_MODEL,
        review_status: CANDIDATE_STATUS,
        candidate_score: null,
        exact_locked_script_substring_read: timing ? "pass" : "fail_phrase_not_found",
        candidate_authoring_mode: "human_curated_exact_script_draft",
      };
    });
  }
  const scored = [];
  const seenPhrase = new Set();
  for (const sentence of sentences) {
    const best = bestPhraseForSentence(sentence);
    if (!best || best.score < 7) continue;
    const phrase = best.phrase.trim();
    const normalized = phrase.toLowerCase();
    if (seenPhrase.has(normalized)) continue;
    const timing = findPhraseTiming(fullText, cues, phrase);
    if (!timing) continue;
    seenPhrase.add(normalized);
    scored.push({
      phrase,
      score: best.score,
      sentence,
      timing,
    });
  }
  const firstCue = cues[0]?.start || 0;
  const finalCue = cues.at(-1)?.end || firstCue;
  const effectiveEnd = Math.max(firstCue + 60, Math.min(finalCue - 12, Number(manifest.youtube_placeholder_fade_start_seconds || Infinity)));
  const slots = Array.from({ length: episode.target_count }, (_, index) => {
    const ratio = episode.target_count === 1 ? 0 : index / (episode.target_count - 1);
    return firstCue + 22 + ratio * Math.max(1, effectiveEnd - firstCue - 44);
  });
  const slotSpacing = slots.length > 1 ? Math.max(1, slots[1] - slots[0]) : 60;
  const selected = [];
  const selectedKeys = new Set();
  for (const slot of slots) {
    const available = scored.filter((candidate) => !selectedKeys.has(candidate.phrase.toLowerCase()));
    const nearby = available.filter((candidate) => Math.abs(candidate.timing.start - slot) <= slotSpacing * 0.9);
    const pool = nearby.length ? nearby : available;
    const best = pool
      .filter((candidate) => !selectedKeys.has(candidate.phrase.toLowerCase()))
      .map((candidate) => ({
        ...candidate,
        slotScore: candidate.score - Math.abs(candidate.timing.start - slot) / 1.75,
      }))
      .sort((a, b) => b.slotScore - a.slotScore)[0];
    if (!best) continue;
    selected.push(best);
    selectedKeys.add(best.phrase.toLowerCase());
  }
  while (selected.length < episode.target_count) {
    const next = scored
      .filter((candidate) => !selectedKeys.has(candidate.phrase.toLowerCase()))
      .sort((a, b) => b.score - a.score)[0];
    if (!next) break;
    selected.push(next);
    selectedKeys.add(next.phrase.toLowerCase());
  }
  return selected
    .sort((a, b) => a.timing.start - b.timing.start)
    .slice(0, episode.target_count)
    .map((candidate, index) => ({
      candidate_id: `${episode.episode_id}_takeaway_candidate_${String(index + 1).padStart(2, "0")}`,
      episode_id: episode.episode_id,
      episode_title: episode.title,
      phrase_text: candidate.phrase,
      word_count: wordCount(candidate.phrase),
      timing_window_seconds: [Number(candidate.timing.start.toFixed(3)), Number(candidate.timing.end.toFixed(3))],
      normalized_script_token_range: candidate.timing.normalized_script_token_range,
      nearby_script_context: contextForPhrase(fullText, candidate.phrase),
      proof_review_url: proofUrlAtTime(manifest, candidate.timing.start),
      caption_highlight_model_id: MODEL_ID,
      highlight_semantic_role: SEMANTIC_ROLE,
      highlight_density_model: DENSITY_MODEL,
      review_status: CANDIDATE_STATUS,
      candidate_score: Number(candidate.score.toFixed(3)),
      exact_locked_script_substring_read: "pass",
    }));
}

function validateEpisodeCandidates({ episode, candidates, fullText }) {
  const failures = [];
  if (candidates.length !== episode.target_count) {
    failures.push(`expected ${episode.target_count} candidates, found ${candidates.length}`);
  }
  const seen = new Set();
  for (const candidate of candidates) {
    if (!fullText.includes(candidate.phrase_text)) failures.push(`${candidate.candidate_id}: phrase is not an exact locked-script substring`);
    if (candidate.word_count < 2 || candidate.word_count > 9) failures.push(`${candidate.candidate_id}: word count ${candidate.word_count} is outside 2-9`);
    const key = candidate.phrase_text.toLowerCase();
    if (seen.has(key)) failures.push(`${candidate.candidate_id}: duplicate phrase`);
    seen.add(key);
    if (candidate.review_status !== CANDIDATE_STATUS) failures.push(`${candidate.candidate_id}: status must remain review-only`);
  }
  const starts = candidates.map((candidate) => candidate.timing_window_seconds[0]).sort((a, b) => a - b);
  let maxGap = 0;
  for (let index = 1; index < starts.length; index += 1) {
    maxGap = Math.max(maxGap, starts[index] - starts[index - 1]);
  }
  if (maxGap > 90) failures.push(`max candidate gap ${maxGap.toFixed(3)}s exceeds 90s`);
  return {
    passed: failures.length === 0,
    failures,
    candidate_count: candidates.length,
    max_candidate_gap_seconds: Number(maxGap.toFixed(3)),
  };
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderReviewPage(artifact) {
  const rows = artifact.episodes
    .flatMap((episode) =>
      episode.candidates.map(
        (candidate) => `
          <tr>
            <td><strong>${escapeHtml(episode.title)}</strong><span>${escapeHtml(candidate.candidate_id)}</span></td>
            <td><a href="${escapeHtml(candidate.proof_review_url)}">${escapeHtml(formatTimestamp(candidate.timing_window_seconds[0]))}</a></td>
            <td class="phrase">${escapeHtml(candidate.phrase_text)}</td>
            <td>${escapeHtml(candidate.word_count)}</td>
            <td class="context">${escapeHtml(candidate.nearby_script_context)}</td>
            <td><span class="status">${escapeHtml(candidate.review_status)}</span></td>
          </tr>`,
      ),
    )
    .join("\n");
  const cards = artifact.episodes
    .map(
      (episode) => `
        <section>
          <h2>${escapeHtml(episode.title)}</h2>
          <dl>
            <div><dt>Candidates</dt><dd>${episode.candidate_count}/${episode.target_count}</dd></div>
            <div><dt>Max gap</dt><dd>${episode.validation.max_candidate_gap_seconds}s</dd></div>
            <div><dt>Status</dt><dd>${episode.validation.passed ? "Ready for review" : "Needs repair"}</dd></div>
          </dl>
        </section>`,
    )
    .join("\n");
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>First-Eight Lesson Takeaway Review</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #080b0f;
      --panel: #111820;
      --panel-2: #17202a;
      --line: #2d3a46;
      --text: #eef3f4;
      --muted: #9eacb6;
      --accent: #f6c768;
      --good: #89d59b;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      padding: 28px;
    }
    header {
      max-width: 1420px;
      margin: 0 auto 22px;
    }
    h1 {
      margin: 0 0 8px;
      font-size: 32px;
      line-height: 1.08;
      letter-spacing: 0;
    }
    p {
      margin: 0;
      color: var(--muted);
      max-width: 980px;
      line-height: 1.45;
    }
    .meta {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      max-width: 1420px;
      margin: 0 auto 22px;
    }
    section, .table-wrap {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    section {
      padding: 14px;
    }
    h2 {
      margin: 0 0 10px;
      font-size: 16px;
    }
    dl, dt, dd { margin: 0; }
    dl { display: grid; gap: 8px; }
    dl div { display: flex; justify-content: space-between; gap: 12px; }
    dt { color: var(--muted); }
    dd { color: var(--text); font-weight: 700; }
    .table-wrap {
      max-width: 1420px;
      margin: 0 auto;
      overflow: auto;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 1160px;
    }
    th, td {
      border-bottom: 1px solid var(--line);
      padding: 12px 14px;
      vertical-align: top;
      text-align: left;
    }
    th {
      position: sticky;
      top: 0;
      background: var(--panel-2);
      color: #d8e0e5;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      z-index: 1;
    }
    td:first-child { width: 210px; }
    td:first-child span {
      display: block;
      margin-top: 5px;
      color: var(--muted);
      font-size: 12px;
      overflow-wrap: anywhere;
    }
    td:nth-child(2) { width: 82px; white-space: nowrap; }
    .phrase {
      width: 270px;
      color: var(--accent);
      font-weight: 800;
      font-size: 17px;
      line-height: 1.25;
    }
    .context {
      color: #c9d3d9;
      line-height: 1.4;
    }
    a { color: var(--accent); text-decoration: none; font-weight: 800; }
    a:hover { text-decoration: underline; }
    .status {
      display: inline-block;
      color: var(--good);
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }
    @media (max-width: 900px) {
      body { padding: 18px; }
      .meta { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <h1>First-Eight Lesson Takeaway Review</h1>
    <p>Review-only candidates for the seven episodes that do not yet have authored rolling-rail highlights. Every phrase is an exact substring from the current script-locked <code>offset_intro_3s601</code> visible rail sidecar and remains <code>${CANDIDATE_STATUS}</code>, so no proof will render these highlights until reviewed spans are promoted later.</p>
  </header>
  <div class="meta">
    ${cards}
  </div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Episode</th>
          <th>Time</th>
          <th>Takeaway candidate</th>
          <th>Words</th>
          <th>Nearby script context</th>
          <th>Review state</th>
        </tr>
      </thead>
      <tbody>
        ${rows}
      </tbody>
    </table>
  </div>
</body>
</html>
`;
}

function main() {
  fs.mkdirSync(REVIEW_ROOT, { recursive: true });
  const episodes = [];
  const failures = [];
  for (const episode of EPISODES) {
    const manifest = readJson(episode.manifest_path);
    const captionPath = manifest.caption_display_timing_source?.path || manifest.caption_sidecar?.path;
    if (!captionPath || !/offset_intro_3s601\.vtt$/.test(captionPath)) {
      failures.push(`${episode.episode_id}: expected offset_intro_3s601 visible VTT, got ${captionPath || "missing"}`);
      continue;
    }
    const cues = parseVtt(captionPath);
    const fullText = buildTextIndex(cues);
    const sentences = sentenceItems(cues);
    const candidates = chooseCandidates({ episode, manifest, cues, sentences, fullText });
    const validation = validateEpisodeCandidates({ episode, candidates, fullText });
    if (!validation.passed) failures.push(...validation.failures.map((failure) => `${episode.episode_id}: ${failure}`));
    episodes.push({
      episode_id: episode.episode_id,
      title: episode.title,
      target_count: episode.target_count,
      candidate_count: candidates.length,
      manifest_path: episode.manifest_path,
      caption_display_timing_source_path: captionPath,
      caption_display_timing_source_sha256: sha256File(captionPath),
      review_only_policy: "candidate files are outside episode sourceRoot and use candidate_pending_human_review, so the current renderer ignores them",
      validation,
      candidates,
    });
  }
  const artifactPath = path.join(REVIEW_ROOT, `lesson_takeaway_candidates_${STAMP}.json`);
  const latestPath = path.join(REVIEW_ROOT, "lesson_takeaway_candidates_latest.json");
  const artifact = {
    model: MODEL_ID,
    review_artifact_model: "first_eight_lesson_takeaway_candidate_review_v1",
    generated_at_utc: GENERATED_AT_UTC,
    status: failures.length ? "candidate_review_blocked_validation_failed" : "candidate_review_ready_pending_human_review",
    review_page_path: REVIEW_PAGE_PATH,
    review_page_url: `${REVIEW_SERVER_BASE_URL}/first-eight-lesson-takeaway-review.html`,
    candidate_status: CANDIDATE_STATUS,
    highlight_semantic_role: SEMANTIC_ROLE,
    highlight_density_model: DENSITY_MODEL,
    phrase_policy: "exact_locked_script_substrings_only",
    proof_regeneration_policy: "do_not_regenerate_or_render_highlights_until_human_review_promotes_spans",
    challenger_policy: "unchanged_reference_with_existing_32_draft_takeaway_spans",
    episodes,
    totals: {
      episode_count: episodes.length,
      candidate_count: episodes.reduce((sum, episode) => sum + episode.candidate_count, 0),
      expected_candidate_count: EPISODES.reduce((sum, episode) => sum + episode.target_count, 0),
    },
    failures,
    passed: failures.length === 0,
  };
  writeJson(artifactPath, artifact);
  writeJson(latestPath, artifact);
  fs.writeFileSync(REVIEW_PAGE_PATH, renderReviewPage(artifact));
  if (failures.length) {
    console.error(failures.join("\n"));
    process.exit(1);
  }
  console.log(
    JSON.stringify(
      {
        review_page_path: REVIEW_PAGE_PATH,
        review_page_url: artifact.review_page_url,
        candidate_artifact_path: artifactPath,
        latest_candidate_artifact_path: latestPath,
        candidate_count: artifact.totals.candidate_count,
      },
      null,
      2,
    ),
  );
}

main();
