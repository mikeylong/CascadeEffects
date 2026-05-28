from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path

from PIL import Image

from stylelab.boards import build_motion_reel, build_still_contact_sheet
from stylelab.config import ensure_runtime_dirs, load_runtime
from stylelab.evaluation import run_evaluation
from stylelab.io import list_scene_paths, read_json
from stylelab.manifests import load_profile, load_scene, load_short
from stylelab.motion import render_motion
from stylelab.rendering import render_still
from stylelab.shorts import build_short


REPO_ROOT = Path(__file__).resolve().parents[1]


def _copy_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_silent_wav(path: Path, duration_seconds: float = 8.0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 24000
    frame_count = int(sample_rate * duration_seconds)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(b"\x00\x00" * frame_count)


class SmokePipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="stylelab-smoke-")
        self.repo_root = Path(self.temp_dir.name)
        for relative in ("profiles", "scenes", "references", "renders", "exports", "boards", "evaluations", "shorts", "tests"):
            (self.repo_root / relative).mkdir(parents=True, exist_ok=True)
        for profile_path in (REPO_ROOT / "profiles").glob("*.json"):
            _copy_file(profile_path, self.repo_root / "profiles" / profile_path.name)
        _copy_file(REPO_ROOT / "references" / "benchmark_pack.json", self.repo_root / "references" / "benchmark_pack.json")
        for scene_path in (REPO_ROOT / "scenes").glob("*.json"):
            _copy_file(scene_path, self.repo_root / "scenes" / scene_path.name)
        for short_path in (REPO_ROOT / "shorts").glob("*.json"):
            _copy_file(short_path, self.repo_root / "shorts" / short_path.name)
        self.runtime = load_runtime(self.repo_root)
        ensure_runtime_dirs(self.runtime)
        self.monolith_profile = load_profile(self.runtime.profiles_root / "monolith_reflection_v1.json")
        self.minimal_profile = load_profile(self.runtime.profiles_root / "minimal_surreal_editorial_v1.json")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_still_motion_board_and_eval_smoke(self) -> None:
        scene_01_path = self.runtime.scenes_root / "scene_01_shuttle_exterior.json"
        motion_01_path = self.runtime.scenes_root / "motion_01_shuttle_exterior.json"
        beat_07_path = self.runtime.scenes_root / "scene_challenger_beat_07_thesis_close.json"
        short_path = self.runtime.shorts_root / "challenger_short_v1.json"
        audio_path = self.repo_root / "fixtures" / "audio.wav"
        transcript_path = self.repo_root / "fixtures" / "transcript.txt"
        _write_silent_wav(audio_path)
        transcript_path.write_text("Fixture transcript.", encoding="utf-8")
        short_payload = read_json(short_path)
        short_payload["audio_path"] = str(audio_path)
        short_payload["transcript_path"] = str(transcript_path)
        _write_json(short_path, short_payload)

        scene_01 = load_scene(scene_01_path)
        motion_01 = load_scene(motion_01_path)
        beat_07 = load_scene(beat_07_path)
        short_manifest = load_short(short_path, scenes_root=self.runtime.scenes_root)

        # Keep the smoke test fast by trimming clip spans in the temp repo only.
        short_manifest["beats"] = [
            {
                **beat,
                "clip_start_seconds": float(index),
                "clip_end_seconds": float(index + 1),
            }
            for index, beat in enumerate(short_manifest["beats"])
        ]
        _write_json(short_path, short_manifest)
        for beat in short_manifest["beats"]:
            scene_path = self.runtime.scenes_root / f"{beat['scene_id']}.json"
            scene_payload = read_json(scene_path)
            scene_payload["target_duration_seconds"] = 1.0
            _write_json(scene_path, scene_payload)
        short_manifest = load_short(short_path, scenes_root=self.runtime.scenes_root)
        beat_07 = load_scene(beat_07_path)

        sketch = render_still(self.runtime, scene_01_path, scene_01, self.monolith_profile, mode="sketch")
        lock = render_still(self.runtime, beat_07_path, beat_07, self.minimal_profile, mode="lock")
        motion = render_motion(self.runtime, motion_01_path, motion_01, self.monolith_profile, preset="stillness_breathe")
        profiles = {
            self.monolith_profile["id"]: self.monolith_profile,
            self.minimal_profile["id"]: self.minimal_profile,
        }
        short_result = build_short(self.runtime, short_path, short_manifest, profiles)

        with Image.open(sketch.image_path) as image:
            self.assertEqual(image.size, (1080, 1920))
        with Image.open(lock.image_path) as image:
            self.assertEqual(image.size, (1080, 1920))

        manifest = read_json(motion.manifest_path)
        self.assertEqual(manifest["final_size"], {"width": 1080, "height": 1920})
        self.assertEqual(manifest["motion_preset"], "stillness_breathe")
        self.assertTrue(Path(short_result["output_path"]).exists())
        self.assertTrue(Path(short_result["packaging_frame_path"]).exists())

        still_board = build_still_contact_sheet(self.runtime, list_scene_paths(self.runtime.scenes_root))
        motion_reel = build_motion_reel(self.runtime, list_scene_paths(self.runtime.scenes_root))
        self.assertTrue(still_board.exists())
        self.assertTrue(motion_reel.exists())

        summary_path = run_evaluation(self.runtime, list_scene_paths(self.runtime.scenes_root), profiles)
        summary = read_json(summary_path)
        self.assertIn("scene_01_shuttle_exterior", summary["scenes"])
        self.assertIn("scene_challenger_beat_01_warning_cold", summary["scenes"])

        probe = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "json",
                short_result["output_path"],
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(probe.stdout)
        stream = payload["streams"][0]
        self.assertEqual((stream["width"], stream["height"]), (1080, 1920))

        duration_probe = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nk=1:nw=1",
                short_result["output_path"],
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        duration = float(duration_probe.stdout.strip())
        self.assertGreater(duration, 6.0)
        self.assertLess(duration, 9.0)


if __name__ == "__main__":
    unittest.main()
