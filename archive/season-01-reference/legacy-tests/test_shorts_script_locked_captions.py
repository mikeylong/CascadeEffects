import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_shorts_script_locked_captions import (
    SCRIPT_LOCKED_CAPTION_MODEL,
    ShortsCaptionPolicyError,
    build_shorts_script_locked_caption_package,
)


def write_whisperx(path: Path, words: list[str], seconds_per_word: float = 0.2) -> None:
    cursor = 0.0
    word_segments = []
    for word in words:
        word_segments.append({"word": word, "start": cursor, "end": cursor + seconds_per_word})
        cursor += seconds_per_word
    path.write_text(json.dumps({"word_segments": word_segments}), encoding="utf-8")


class ShortsScriptLockedCaptionTests(unittest.TestCase):
    def test_asr_mishearing_is_not_used_as_caption_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            prefix = " ".join(f"anchor{i}" for i in range(80))
            suffix = " ".join(f"tail{i}" for i in range(80))
            script_text = f"{prefix} final decision too weak to stop the machine {suffix}"
            script_path = tmp_path / "locked_script.txt"
            timing_path = tmp_path / "timing.whisperx.json"
            script_path.write_text(script_text, encoding="utf-8")
            write_whisperx(
                timing_path,
                prefix.split() + "final decision two weeks to stop the machine".split() + suffix.split(),
            )

            qa = build_shorts_script_locked_caption_package(
                caption_text_source_path=script_path,
                caption_timing_source_path=timing_path,
                output_dir=tmp_path / "out",
                basename="short",
                voice_offset_seconds=3.0,
            )
            offset_srt = Path(qa["outputs"]["offset_srt"]["path"]).read_text(encoding="utf-8")

        self.assertEqual(qa["caption_model"], SCRIPT_LOCKED_CAPTION_MODEL)
        self.assertEqual(qa["reads"]["caption_text_matches_script_read"], "pass")
        self.assertIn("too weak", offset_srt)
        self.assertNotIn("two weeks", offset_srt)

    def test_diarized_text_is_blocked_as_caption_word_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            script_path = tmp_path / "short.diarized.txt"
            timing_path = tmp_path / "timing.whisperx.json"
            script_path.write_text("ASR words only\n", encoding="utf-8")
            write_whisperx(timing_path, ["ASR", "words", "only"])

            with self.assertRaises(ShortsCaptionPolicyError):
                build_shorts_script_locked_caption_package(
                    caption_text_source_path=script_path,
                    caption_timing_source_path=timing_path,
                    output_dir=tmp_path / "out",
                    basename="short",
                    voice_offset_seconds=3.0,
                )

    def test_existing_challenger_script_locked_caption_source_passes_policy(self) -> None:
        script_path = Path(
            "/Users/mike/Audio_CascadeEffects/tmp/ep1_challenger_ending_cadence_pass_01/"
            "challenger_short_restart_v1_ending_cadence_script.txt"
        )
        timing_path = Path(
            "/Users/mike/Audio_CascadeEffects/tmp/ep1_challenger_ending_cadence_pass_01/selected/"
            "challenger_short_restart_v1_ending_cadence_pass_01.whisperx.json"
        )
        if not script_path.exists() or not timing_path.exists():
            self.skipTest("Challenger short script/timing fixture is not available.")

        with tempfile.TemporaryDirectory() as tmp:
            qa = build_shorts_script_locked_caption_package(
                caption_text_source_path=script_path,
                caption_timing_source_path=timing_path,
                output_dir=Path(tmp),
                basename="challenger_short",
                voice_offset_seconds=3.0,
                min_alignment_coverage=0.94,
            )

        self.assertEqual(qa["status"], "pass")
        self.assertEqual(qa["reads"]["caption_asr_text_not_used_read"], "pass")


if __name__ == "__main__":
    unittest.main()
