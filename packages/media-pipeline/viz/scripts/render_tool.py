#!/usr/bin/env python3
from __future__ import annotations

import argparse
import colorsys
import copy
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageFilter, ImageOps
except ImportError:  # pragma: no cover - runtime dependency guard
    Image = None
    ImageFilter = None
    ImageOps = None

from guardrail_policy import load_guardrail_policy, visual_qc_policy_for
from midjourney_package_tool import (
    MidjourneyPackageError,
    build_reference_grid,
    grid_runtime_filename,
    normalize_negative_terms as normalize_midjourney_negative_terms,
)
from subject_reference_plate import build_status_for_output
from workflow_tool import (
    WorkflowCompiler,
    WorkflowError,
    minimal_surreal_full_frame_composition_active,
    minimal_surreal_midjourney_package_grid_active,
    parse_override_values,
    style_uses_subject_reference_conditioning,
    utc_now_iso,
    write_json,
)

START_TIMEOUT_SECONDS = 180
STOP_TIMEOUT_SECONDS = 20
POLL_INTERVAL_SECONDS = 2
QUALITY_PROFILES = {"fast", "standard", "hero"}
DELIVERY_MODES = {"strict", "advisory"}
OPENING_TABLEAU_PRESET = "opening_culture_cluster"
OPENING_TABLEAU_STAGE = "opening_tableau_compose"
MIDJOURNEY_ADAPTER_HARD_BLOCK_FAILURES = {
    "center_weighted_primary_subject",
    "subtitle_band_intrusion",
    "symmetry_too_high",
    "subject_count_exceeds_limit",
    "duplicate_human_identity",
    "multiple_shuttle_heroes",
    "unrecognizable_anchor",
    "scenic_exterior_drift",
    "text_artifacts",
}
MIDJOURNEY_ADAPTER_RANKING_BIAS_TAGS = {
    "single_object_severity",
    "compressed_monolith",
    "one_accent_only",
    "cold_pipe_detail",
    "winter_haze",
    "industrial_frost_signal",
    "accurate_shuttle_stack",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="bin/ce render")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--models-root", required=True)
    parser.add_argument("--comfy-workflows-dir", required=True)
    parser.add_argument("--comfy-output-dir", required=True)
    parser.add_argument("--references-root", required=True)
    parser.add_argument("--comfy-input-dir", required=True)
    parser.add_argument("--comfy-temp-dir", required=True)
    parser.add_argument("--comfy-user-dir", required=True)
    parser.add_argument("--comfy-extra-models-config", required=True)
    parser.add_argument("--comfy-python", required=True)
    parser.add_argument("--comfy-main-py", required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--pid-file", required=True)
    parser.add_argument("--log-file", required=True)
    parser.add_argument("--comfy-clip-vision-model", required=True)

    subparsers = parser.add_subparsers(dest="command", required=True)

    server_parser = subparsers.add_parser("server")
    server_parser.add_argument("action", choices=["status", "start", "stop"])

    stage_parser = subparsers.add_parser("stage")
    stage_parser.add_argument("family")
    stage_parser.add_argument("preset")
    stage_parser.add_argument("stage")
    stage_parser.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override allowed params for the selected render stage.",
    )

    pipeline_parser = subparsers.add_parser("pipeline")
    pipeline_parser.add_argument("family")
    pipeline_parser.add_argument("preset")
    pipeline_parser.add_argument("--selected-seed", type=int)
    pipeline_parser.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override allowed params for the render pipeline.",
    )
    pipeline_parser.add_argument(
        "--typography",
        choices=["auto", "off", "force"],
        default="auto",
        help="Control the still-image typography postprocess after final_upscale.",
    )
    pipeline_parser.add_argument(
        "--source-text-repair",
        choices=["auto", "off", "force"],
        default="auto",
        help="Control the shared source-text repair and cleanup stages in the still pipeline.",
    )
    pipeline_parser.add_argument(
        "--quality-profile",
        choices=sorted(QUALITY_PROFILES),
        default="standard",
        help="Render quality profile. fast keeps the lightweight single-candidate path; standard and hero run candidate search.",
    )
    pipeline_parser.add_argument(
        "--delivery-mode",
        choices=sorted(DELIVERY_MODES),
        default="strict",
        help="strict fails on QC gates; advisory delivers the best available output and records QC failures as metadata.",
    )

    review_proof_parser = subparsers.add_parser("review-proof")
    review_proof_parser.add_argument("family")
    review_proof_parser.add_argument("preset")
    review_proof_parser.add_argument("--selected-seed", type=int)
    review_proof_parser.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override allowed params for the review-proof pipeline.",
    )
    review_proof_parser.add_argument(
        "--quality-profile",
        choices=sorted(QUALITY_PROFILES),
        default="standard",
        help="Render quality profile. fast keeps the lightweight single-candidate path; standard and hero run candidate search.",
    )
    review_proof_parser.add_argument(
        "--delivery-mode",
        choices=sorted(DELIVERY_MODES),
        default="strict",
        help="strict fails on QC gates; advisory delivers the best available proof and records QC failures as metadata.",
    )

    finalize_parser = subparsers.add_parser("finalize-still")
    finalize_parser.add_argument("family")
    finalize_parser.add_argument("preset")
    finalize_parser.add_argument("--source-image", required=True, help="Absolute path to the approved proof image.")
    finalize_parser.add_argument("--selected-seed", type=int)
    finalize_parser.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override allowed params for the finalize-still pipeline.",
    )
    finalize_parser.add_argument(
        "--typography",
        choices=["auto", "off", "force"],
        default="auto",
        help="Control the still-image typography postprocess after final_upscale.",
    )
    finalize_parser.add_argument(
        "--source-text-repair",
        choices=["auto", "off", "force"],
        default="auto",
        help="Control the shared source-text repair and cleanup stages in the still pipeline.",
    )
    finalize_parser.add_argument(
        "--quality-profile",
        choices=sorted(QUALITY_PROFILES),
        default="standard",
        help="Render quality profile for the finishing stages.",
    )
    finalize_parser.add_argument(
        "--delivery-mode",
        choices=sorted(DELIVERY_MODES),
        default="strict",
        help="strict fails on QC gates; advisory keeps final outputs and records QC failures as metadata.",
    )

    typography_parser = subparsers.add_parser("typography")
    typography_parser.add_argument("family")
    typography_parser.add_argument("preset")
    typography_parser.add_argument("--image", required=True, help="Absolute path to the base final still image.")
    typography_parser.add_argument("--output", help="Optional output path for the typography-composited still.")

    return parser.parse_args()


class HeadlessComfyRunner:
    def __init__(self, args: argparse.Namespace) -> None:
        self.repo_root = Path(args.repo_root)
        self.models_root = Path(args.models_root)
        self.comfy_workflows_dir = Path(args.comfy_workflows_dir)
        self.comfy_output_dir = Path(args.comfy_output_dir)
        self.references_root = Path(args.references_root)
        self.comfy_input_dir = Path(args.comfy_input_dir)
        self.comfy_temp_dir = Path(args.comfy_temp_dir)
        self.comfy_user_dir = Path(args.comfy_user_dir)
        self.comfy_extra_models_config = Path(args.comfy_extra_models_config)
        self.comfy_python = Path(args.comfy_python)
        self.comfy_main_py = Path(args.comfy_main_py)
        desktop_frontend_root = self.comfy_main_py.parent / "web_custom_versions" / "desktop_app"
        self.comfy_frontend_root = desktop_frontend_root if desktop_frontend_root.exists() else None
        self.host = args.host
        self.port = args.port
        self.pid_file = Path(args.pid_file)
        self.log_file = Path(args.log_file)
        self.comfy_clip_vision_model = str(args.comfy_clip_vision_model).strip()
        self.server_url = f"http://{self.host}:{self.port}"

        self.compiler = WorkflowCompiler(
            repo_root=self.repo_root,
            models_root=self.models_root,
            comfy_workflows_dir=self.comfy_workflows_dir,
            comfy_output_dir=self.comfy_output_dir,
            references_root=self.references_root,
            comfy_clip_vision_model=self.comfy_clip_vision_model,
        )
        self.runs_root = self.compiler.generated_dir / "runs"

    def api_get(self, path: str) -> Any:
        request = urllib.request.Request(f"{self.server_url}{path}", method="GET")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.URLError as exc:
            raise WorkflowError(f"Failed to reach Comfy server at {self.server_url}{path}: {exc}") from exc

    def api_post(self, path: str, payload: dict[str, Any]) -> Any:
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.server_url}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise WorkflowError(
                f"Comfy API request failed for {path}: HTTP {exc.code} {exc.reason}: {body}"
            ) from exc
        except urllib.error.URLError as exc:
            raise WorkflowError(f"Failed to reach Comfy server at {self.server_url}{path}: {exc}") from exc

    def server_healthy(self) -> bool:
        try:
            self.api_get("/system_stats")
            return True
        except WorkflowError:
            return False

    def read_pid(self) -> int | None:
        if not self.pid_file.exists():
            return None
        raw = self.pid_file.read_text(encoding="utf-8").strip()
        if not raw:
            return None
        try:
            return int(raw)
        except ValueError:
            return None

    @staticmethod
    def pid_alive(pid: int | None) -> bool:
        if pid is None:
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    def cleanup_stale_pid_file(self) -> None:
        pid = self.read_pid()
        if pid is None:
            if self.pid_file.exists():
                self.pid_file.unlink(missing_ok=True)
            return
        if not self.pid_alive(pid):
            self.pid_file.unlink(missing_ok=True)

    def server_status(self) -> dict[str, Any]:
        self.cleanup_stale_pid_file()
        pid = self.read_pid()
        healthy = self.server_healthy()
        managed = pid is not None and self.pid_alive(pid)
        return {
            "healthy": healthy,
            "managed": managed,
            "pid": pid,
            "server_url": self.server_url,
            "pid_file": str(self.pid_file),
            "log_file": str(self.log_file),
        }

    def print_server_status(self) -> int:
        try:
            self.ensure_runtime_paths()
        except WorkflowError as exc:
            print(f"ERROR {exc}")
            return 1
        status = self.server_status()
        if status["healthy"]:
            managed_text = "yes" if status["managed"] else "no"
            pid_text = status["pid"] if status["pid"] is not None else "unknown"
            print(
                f"OK   headless server running url={status['server_url']} pid={pid_text} managed={managed_text}"
            )
            return 0
        print(f"WARN  headless server not reachable at {status['server_url']}")
        if status["managed"] and status["pid"] is not None:
            print(f"WARN  stale managed pid file points to pid={status['pid']}")
        return 1

    def ensure_runtime_paths(self) -> None:
        if not self.comfy_clip_vision_model:
            raise WorkflowError("CLIP vision model not configured: --comfy-clip-vision-model")
        required_files = [
            ("Comfy Python", self.comfy_python),
            ("Comfy main.py", self.comfy_main_py),
            ("extra_models_config.yaml", self.comfy_extra_models_config),
            (
                "CLIP vision model",
                self.models_root / "clip_vision" / self.comfy_clip_vision_model,
            ),
        ]
        for label, path in required_files:
            if not path.exists():
                raise WorkflowError(f"{label} not found: {path}")
        if self.comfy_frontend_root is not None and not self.comfy_frontend_root.exists():
            raise WorkflowError(f"Comfy frontend root not found: {self.comfy_frontend_root}")
        for directory in (
            self.comfy_output_dir,
            self.comfy_input_dir,
            self.comfy_temp_dir,
            self.comfy_user_dir,
            self.log_file.parent,
            self.runs_root,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def start_server(self) -> None:
        self.ensure_runtime_paths()
        self.cleanup_stale_pid_file()
        if self.server_healthy():
            print(f"INFO  headless server already running at {self.server_url}")
            return

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        cmd = [
            str(self.comfy_python),
            str(self.comfy_main_py),
            "--listen",
            self.host,
            "--port",
            str(self.port),
            "--disable-auto-launch",
            "--user-directory",
            str(self.comfy_user_dir),
            "--input-directory",
            str(self.comfy_input_dir),
            "--output-directory",
            str(self.comfy_output_dir),
            "--temp-directory",
            str(self.comfy_temp_dir),
            "--extra-model-paths-config",
            str(self.comfy_extra_models_config),
        ]
        if self.comfy_frontend_root is not None:
            cmd.extend(
                [
                    "--front-end-root",
                    str(self.comfy_frontend_root),
                ]
            )

        with self.log_file.open("ab") as log_handle:
            process = subprocess.Popen(
                cmd,
                cwd=str(self.repo_root),
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )

        self.pid_file.write_text(f"{process.pid}\n", encoding="utf-8")

        deadline = time.monotonic() + START_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if self.server_healthy():
                print(f"START headless server url={self.server_url} pid={process.pid}")
                return
            exit_code = process.poll()
            if exit_code is not None:
                self.pid_file.unlink(missing_ok=True)
                raise WorkflowError(
                    f"Headless Comfy server exited during startup with code {exit_code}. "
                    f"See {self.log_file}"
                )
            time.sleep(1.5)

        raise WorkflowError(
            f"Timed out waiting for headless Comfy server at {self.server_url}. See {self.log_file}"
        )

    def stop_server(self) -> int:
        self.cleanup_stale_pid_file()
        pid = self.read_pid()
        if pid is None:
            if self.server_healthy():
                raise WorkflowError(
                    f"Comfy server is reachable at {self.server_url}, but no managed pid file exists."
                )
            print("INFO  no managed headless server to stop")
            return 0

        if not self.pid_alive(pid):
            self.pid_file.unlink(missing_ok=True)
            print(f"INFO  removed stale pid file for pid={pid}")
            return 0

        os.kill(pid, signal.SIGTERM)
        deadline = time.monotonic() + STOP_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if not self.pid_alive(pid):
                self.pid_file.unlink(missing_ok=True)
                print(f"STOP headless server pid={pid}")
                return 0
            time.sleep(0.5)

        os.kill(pid, signal.SIGKILL)
        self.pid_file.unlink(missing_ok=True)
        print(f"STOP headless server pid={pid} signal=SIGKILL")
        return 0

    def load_history_item(self, prompt_id: str) -> dict[str, Any] | None:
        history = self.api_get(f"/history/{prompt_id}")
        return history.get(prompt_id)

    def wait_for_prompt(self, prompt_id: str) -> dict[str, Any]:
        deadline = time.monotonic() + (START_TIMEOUT_SECONDS * 10)
        while time.monotonic() < deadline:
            history_item = self.load_history_item(prompt_id)
            if history_item is not None and history_item.get("status", {}).get("completed"):
                status_str = history_item.get("status", {}).get("status_str", "unknown")
                if status_str != "success":
                    raise WorkflowError(
                        f"Prompt {prompt_id} completed with status {status_str!r}. "
                        f"See {self.log_file}"
                    )
                return history_item
            time.sleep(POLL_INTERVAL_SECONDS)
        raise WorkflowError(f"Timed out waiting for prompt {prompt_id}. See {self.log_file}")

    def map_media_base_dir(self, media_type: str) -> Path:
        if media_type == "output":
            return self.comfy_output_dir
        if media_type == "input":
            return self.comfy_input_dir
        if media_type == "temp":
            return self.comfy_temp_dir
        return self.comfy_output_dir

    def collect_output_files(self, history_item: dict[str, Any]) -> list[Path]:
        outputs = history_item.get("outputs", {})
        files: list[Path] = []
        for node_output in outputs.values():
            for media_items in node_output.values():
                if not isinstance(media_items, list):
                    continue
                for media in media_items:
                    if not isinstance(media, dict) or "filename" not in media:
                        continue
                    base_dir = self.map_media_base_dir(str(media.get("type", "output")))
                    subfolder = str(media.get("subfolder", "")).strip("/")
                    path = base_dir / subfolder / str(media["filename"])
                    files.append(path)
        unique_paths: list[Path] = []
        seen: set[str] = set()
        for path in files:
            text = str(path)
            if text not in seen:
                seen.add(text)
                unique_paths.append(path)
        return unique_paths

    def relative_output_path(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.comfy_output_dir.resolve())).replace(os.sep, "/")
        except ValueError as exc:
            raise WorkflowError(f"Expected an output under {self.comfy_output_dir}, got {path}") from exc

    def relative_input_path(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.comfy_input_dir.resolve())).replace(os.sep, "/")
        except ValueError as exc:
            raise WorkflowError(f"Expected an input under {self.comfy_input_dir}, got {path}") from exc

    def midjourney_grid_output_path(
        self,
        *,
        package_id: str,
        shot_id: str,
        width: int,
        height: int,
    ) -> Path:
        return (
            self.compiler.generated_dir
            / "midjourney_package_grids"
            / package_id
            / f"{shot_id}__{width}x{height}.png"
        )

    def stage_subject_reference_asset(
        self,
        source_path: Path,
        *,
        family: str,
        preset: str,
        subdir: str = "subject_refs",
        destination_name: str | None = None,
    ) -> tuple[Path, bool]:
        destination = (
            self.comfy_input_dir
            / "cascadeeffects"
            / subdir
            / family
            / preset
            / (destination_name or source_path.name)
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            source_stat = source_path.stat()
            destination_stat = destination.stat()
            if (
                destination_stat.st_size == source_stat.st_size
                and destination_stat.st_mtime_ns == source_stat.st_mtime_ns
            ):
                return destination.resolve(), False
        shutil.copy2(source_path, destination)
        return destination.resolve(), True

    def prepare_subject_reference_overrides(
        self,
        family: str,
        base_preset: str,
        stage: str,
        overrides: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        spec_path = self.compiler.resolve_stage_spec_path(family, base_preset, stage)
        spec = self.compiler.load_spec(spec_path)
        params = copy.deepcopy(spec["params"])
        for key, value in overrides.items():
            params[key] = value
        if not self.compiler.is_active_family(spec["family"]):
            return dict(overrides), None
        style = self.compiler.load_style_profile(str(params["style_profile"]))
        if not style_uses_subject_reference_conditioning(style):
            return dict(overrides), None
        if stage not in {"draft_txt2img", "refine_img2img"}:
            return dict(overrides), None
        midjourney_package_mode = minimal_surreal_midjourney_package_grid_active(
            spec=spec,
            style=style,
            params=params,
        )
        if "subject_reference_image" in overrides:
            raw_override_subject_reference = str(params.get("subject_reference_image", "")).strip()
            if raw_override_subject_reference:
                override_source_path = self.compiler.resolve_subject_reference_path(raw_override_subject_reference)
                override_plate_status = build_status_for_output(override_source_path)
                if override_plate_status is not None and not override_plate_status["ready"]:
                    raise WorkflowError(
                        f"{family}/{base_preset} stage={stage} subject_reference_image is stale: "
                        f"{override_plate_status['reason']}. Rebuild it with "
                        f"`bin/ce refs build subject-plates {override_source_path.parents[1].parent.name}`."
                    )
        if midjourney_package_mode:
            try:
                shot = self.compiler.resolve_midjourney_package_shot(params)
                adapter = self.compiler.resolve_midjourney_package_adapter(params, shot=shot)
                grid_output_path = self.midjourney_grid_output_path(
                    package_id=shot.package_id,
                    shot_id=shot.shot_id,
                    width=int(params["width"]),
                    height=int(params["height"]),
                )
                grid_manifest = build_reference_grid(
                    shot,
                    output_path=grid_output_path,
                    width=int(params["width"]),
                    height=int(params["height"]),
                    adapter=adapter,
                )
            except MidjourneyPackageError as exc:
                raise WorkflowError(str(exc)) from exc
            staged_path, copied = self.stage_subject_reference_asset(
                grid_output_path,
                family=family,
                preset=base_preset,
                subdir="midjourney_package_grids",
                destination_name=grid_runtime_filename(shot_id=shot.shot_id),
            )
            prepared_overrides = dict(overrides)
            prepared_overrides["subject_reference_runtime_image"] = self.relative_input_path(staged_path)
            prepared_overrides["subject_reference_clip_vision_model"] = self.comfy_clip_vision_model
            return prepared_overrides, {
                "subject_reference": {
                    "source_path": str(grid_output_path),
                    "preview_path": str(grid_output_path),
                    "runtime_source_path": str(grid_output_path),
                    "staged_input_path": str(staged_path),
                    "staged_input_image": self.relative_input_path(staged_path),
                    "clip_vision_model": self.comfy_clip_vision_model,
                    "reused_existing_stage": not copied,
                },
                "midjourney_package": {
                    "active": True,
                    "package_manifest_path": str(shot.package_manifest_path),
                    "package_id": shot.package_id,
                    "shot_id": shot.shot_id,
                    "reference_files": list(shot.reference_files),
                    "reference_paths": grid_manifest["reference_paths"],
                    "reference_grid_path": str(grid_output_path),
                    "staged_reference_grid_path": str(staged_path),
                    "staged_input_image": self.relative_input_path(staged_path),
                    "prompt_doc_path": shot.prompt_doc_path,
                    "references_manifest_path": shot.references_manifest_path,
                    "prompt_text": shot.prompt_text,
                    "negative_terms": normalize_midjourney_negative_terms(list(shot.negative_terms)),
                    "adapter": copy.deepcopy(grid_manifest.get("adapter", {"active": False})),
                    "grid_tiles": copy.deepcopy(grid_manifest.get("grid_tiles", [])),
                    "reused_existing_stage": not copied,
                },
            }
        full_frame_mode = minimal_surreal_full_frame_composition_active(spec=spec, style=style, params=params)
        raw_subject_reference = str(params.get("subject_reference_image", "")).strip()
        if not raw_subject_reference:
            raise WorkflowError(f"{family}/{base_preset} stage={stage} is missing subject_reference_image.")
        source_path = self.compiler.resolve_subject_reference_path(raw_subject_reference)
        if not source_path.exists():
            raise WorkflowError(
                f"{family}/{base_preset} stage={stage} subject_reference_image was not found: {source_path}"
            )
        plate_status = build_status_for_output(source_path)
        if plate_status is not None and not plate_status["ready"]:
            raise WorkflowError(
                f"{family}/{base_preset} stage={stage} subject_reference_image is stale: {plate_status['reason']}. "
                f"Rebuild it with `bin/ce refs build subject-plates {source_path.parents[1].parent.name}`."
            )
        if full_frame_mode and plate_status is None:
            raise WorkflowError(
                f"{family}/{base_preset} stage={stage} requires generated hidden-control assets; "
                "the preview plate cannot be used as a runtime generation input."
            )
        staging_source_path = (
            Path(str(plate_status["vision_ref_path"])).expanduser().resolve()
            if full_frame_mode and plate_status
            else Path(str(plate_status["seed_rgba_path"])).expanduser().resolve() if plate_status else source_path
        )
        if not staging_source_path.exists():
            raise WorkflowError(
                f"{family}/{base_preset} stage={stage} subject reference runtime asset was not found: "
                f"{staging_source_path}"
            )
        staged_path, copied = self.stage_subject_reference_asset(
            staging_source_path,
            family=family,
            preset=base_preset,
        )
        staged_mask_path: Path | None = None
        staged_mask_copied = False
        layout_mask_source_path: Path | None = None
        if full_frame_mode:
            layout_mask_source_path = Path(str(plate_status["layout_mask_path"])).expanduser().resolve() if plate_status else None
            if layout_mask_source_path is None or not layout_mask_source_path.exists():
                raise WorkflowError(
                    f"{family}/{base_preset} stage={stage} layout mask asset was not found: {layout_mask_source_path}"
                )
            staged_mask_path, staged_mask_copied = self.stage_subject_reference_asset(
                layout_mask_source_path,
                family=family,
                preset=base_preset,
            )
        subject_reference_manifest: dict[str, Any] = {
            "source_path": str(source_path),
            "preview_path": str(source_path),
            "runtime_source_path": str(staging_source_path),
            "staged_input_path": str(staged_path),
            "staged_input_image": self.relative_input_path(staged_path),
            "clip_vision_model": self.comfy_clip_vision_model,
            "reused_existing_stage": not copied,
        }
        if plate_status is not None:
            subject_reference_manifest.update(
                {
                    "plate_ready": True,
                    "plate_manifest_path": plate_status["manifest_path"],
                    "plate_build_manifest_path": plate_status["build_manifest_path"],
                    "plate_id": plate_status.get("plate_id", ""),
                    "source_id": plate_status.get("source_id", ""),
                    "vision_ref_path": plate_status.get("vision_ref_path", ""),
                    "layout_mask_path": plate_status.get("layout_mask_path", ""),
                    "seed_rgba_path": plate_status.get("seed_rgba_path", ""),
                    "soft_mask_path": plate_status.get("soft_mask_path", ""),
                }
            )
        if full_frame_mode and staged_mask_path is not None:
            subject_reference_manifest.update(
                {
                    "runtime_mask_source_path": str(layout_mask_source_path),
                    "staged_mask_input_path": str(staged_mask_path),
                    "staged_input_mask": self.relative_input_path(staged_mask_path),
                    "mask_reused_existing_stage": not staged_mask_copied,
                }
            )
        prepared_overrides = dict(overrides)
        prepared_overrides["subject_reference_runtime_image"] = self.relative_input_path(staged_path)
        if full_frame_mode and staged_mask_path is not None:
            prepared_overrides["subject_reference_runtime_mask"] = self.relative_input_path(staged_mask_path)
        prepared_overrides["subject_reference_clip_vision_model"] = self.comfy_clip_vision_model
        return prepared_overrides, {"subject_reference": subject_reference_manifest}

    @staticmethod
    def default_typography_output_path(image_path: Path) -> Path:
        return image_path.with_name(f"{image_path.stem}__typography{image_path.suffix}")

    @staticmethod
    def default_repair_output_path(image_path: Path) -> Path:
        return image_path.with_name(f"{image_path.stem}__repair{image_path.suffix}")

    @staticmethod
    def default_cleanup_output_path(image_path: Path) -> Path:
        return image_path.with_name(f"{image_path.stem}__cleanup{image_path.suffix}")

    def typography_should_run(self, family: str, preset: str, mode: str) -> tuple[bool, tuple[Path, dict[str, Any]] | None]:
        sidecar = self.compiler.load_typography_sidecar(family, preset, required=False)
        if mode == "off":
            return False, sidecar
        if mode == "force":
            if sidecar is None:
                raise WorkflowError(f"Controlled typography is not configured for {family}/{preset}.")
            return True, sidecar
        if mode == "auto" and sidecar is not None and bool(sidecar[1]["enabled"]):
            return True, sidecar
        return False, sidecar

    def repair_policy_should_run(
        self,
        family: str,
        preset: str,
        mode: str,
    ) -> tuple[bool, tuple[Path, dict[str, Any]] | None]:
        sidecar = self.compiler.load_repair_policy(family, preset, required=False)
        if mode == "off":
            return False, sidecar
        if mode == "force":
            if sidecar is None:
                raise WorkflowError(f"Source-text repair is not configured for {family}/{preset}.")
            return True, sidecar
        if mode == "auto" and sidecar is not None and (
            bool(sidecar[1]["enabled"]) or bool(sidecar[1].get("post_final_cleanup", {}).get("enabled"))
        ):
            return True, sidecar
        return False, sidecar

    def ensure_repair_runtime(self, policy_path: Path, policy: dict[str, Any]) -> None:
        backend = str(policy.get("llm_backend", "")).strip()
        model = str(policy.get("llm_model", "")).strip()
        if backend != "ollama":
            raise WorkflowError(f"Unsupported source-text repair backend {backend!r} in {policy_path}.")
        try:
            completed = subprocess.run(
                ["ollama", "show", model],
                check=False,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise WorkflowError(
                f"Source-text repair policy {policy_path} requires ollama, but it is not installed."
            ) from exc
        if completed.returncode != 0:
            stderr = completed.stderr.strip() or completed.stdout.strip()
            raise WorkflowError(
                f"Source-text repair policy {policy_path} requires missing Ollama model {model!r}: {stderr}"
            )

    def run_typography_apply(
        self,
        *,
        target: str,
        artifact_path: Path,
        intent_path: Path,
        repair_manifest_path: Path | None = None,
        output_path: Path | None = None,
        allow_validation_failure: bool = False,
    ) -> dict[str, Any]:
        input_path = artifact_path.expanduser().resolve()
        if not input_path.exists():
            raise WorkflowError(f"Typography input artifact was not found: {input_path}")
        resolved_intent = intent_path.expanduser().resolve()
        if not resolved_intent.exists():
            raise WorkflowError(f"Typography intent was not found: {resolved_intent}")
        resolved_output = (
            output_path.expanduser().resolve()
            if output_path is not None
            else self.default_typography_output_path(input_path)
        )
        cmd = [
            str(self.comfy_python),
            str(self.repo_root / "scripts" / "typography_tool.py"),
            "--repo-root",
            str(self.repo_root),
            "--models-root",
            str(self.models_root),
            "--comfy-workflows-dir",
            str(self.comfy_workflows_dir),
            "--comfy-output-dir",
            str(self.comfy_output_dir),
            "--references-root",
            str(self.references_root),
            "apply",
            "--target",
            target,
            "--artifact",
            str(input_path),
            "--intent",
            str(resolved_intent),
            "--output",
            str(resolved_output),
        ]
        if repair_manifest_path is not None:
            resolved_repair_manifest = repair_manifest_path.expanduser().resolve()
            if not resolved_repair_manifest.exists():
                raise WorkflowError(f"Repair manifest was not found: {resolved_repair_manifest}")
            cmd.extend(["--repair-manifest", str(resolved_repair_manifest)])
        completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
        try:
            summary = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            stderr = completed.stderr.strip() or completed.stdout.strip()
            raise WorkflowError(f"Controlled typography returned invalid JSON: {stderr}") from exc
        if completed.returncode != 0 and not allow_validation_failure:
            stderr = completed.stderr.strip() or completed.stdout.strip()
            raise WorkflowError(f"Controlled typography failed for target={target} artifact={input_path}: {stderr}")
        return summary

    def run_typography_validate(
        self,
        *,
        target: str,
        artifact_path: Path,
        intent_path: Path,
        repair_manifest_path: Path | None = None,
        debug_dir: Path | None = None,
    ) -> dict[str, Any]:
        input_path = artifact_path.expanduser().resolve()
        if not input_path.exists():
            raise WorkflowError(f"Typography validation artifact was not found: {input_path}")
        resolved_intent = intent_path.expanduser().resolve()
        if not resolved_intent.exists():
            raise WorkflowError(f"Typography intent was not found: {resolved_intent}")
        cmd = [
            str(self.comfy_python),
            str(self.repo_root / "scripts" / "typography_tool.py"),
            "--repo-root",
            str(self.repo_root),
            "--models-root",
            str(self.models_root),
            "--comfy-workflows-dir",
            str(self.comfy_workflows_dir),
            "--comfy-output-dir",
            str(self.comfy_output_dir),
            "--references-root",
            str(self.references_root),
            "validate",
            "--target",
            target,
            "--artifact",
            str(input_path),
            "--intent",
            str(resolved_intent),
        ]
        if repair_manifest_path is not None:
            resolved_repair_manifest = repair_manifest_path.expanduser().resolve()
            if not resolved_repair_manifest.exists():
                raise WorkflowError(f"Repair manifest was not found: {resolved_repair_manifest}")
            cmd.extend(["--repair-manifest", str(resolved_repair_manifest)])
        if debug_dir is not None:
            cmd.extend(["--debug-dir", str(debug_dir.expanduser().resolve())])
        completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
        try:
            summary = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            stderr = completed.stderr.strip() or completed.stdout.strip()
            raise WorkflowError(f"Typography validation returned invalid JSON for {input_path}: {stderr}") from exc
        if completed.returncode != 0 and not summary.get("validation", {}).get("failures"):
            stderr = completed.stderr.strip() or completed.stdout.strip()
            raise WorkflowError(f"Typography validation failed for {input_path}: {stderr}")
        return summary

    def run_source_text_repair(
        self,
        artifact_path: Path,
        *,
        policy_path: Path,
        output_path: Path | None = None,
        debug_dir: Path | None = None,
    ) -> dict[str, Any]:
        input_path = artifact_path.expanduser().resolve()
        if not input_path.exists():
            raise WorkflowError(f"Source-text repair artifact was not found: {input_path}")
        resolved_policy = policy_path.expanduser().resolve()
        if not resolved_policy.exists():
            raise WorkflowError(f"Source-text repair policy was not found: {resolved_policy}")
        resolved_output = (
            output_path.expanduser().resolve()
            if output_path is not None
            else self.default_repair_output_path(input_path)
        )
        cmd = [
            str(self.comfy_python),
            str(self.repo_root / "scripts" / "typography_tool.py"),
            "--repo-root",
            str(self.repo_root),
            "--models-root",
            str(self.models_root),
            "--comfy-workflows-dir",
            str(self.comfy_workflows_dir),
            "--comfy-output-dir",
            str(self.comfy_output_dir),
            "--references-root",
            str(self.references_root),
            "repair-source-text",
            "--artifact",
            str(input_path),
            "--policy",
            str(resolved_policy),
            "--output",
            str(resolved_output),
        ]
        if debug_dir is not None:
            cmd.extend(["--debug-dir", str(debug_dir.expanduser().resolve())])
        completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if completed.returncode != 0:
            stderr = completed.stderr.strip() or completed.stdout.strip()
            raise WorkflowError(f"Source-text repair failed for artifact={input_path}: {stderr}")
        try:
            return json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise WorkflowError(f"Source-text repair returned invalid JSON: {completed.stdout}") from exc

    def run_cleanup_final_text(
        self,
        artifact_path: Path,
        *,
        intent_path: Path | None,
        policy_path: Path,
        repair_manifest_path: Path | None = None,
        output_path: Path | None = None,
        debug_dir: Path | None = None,
    ) -> dict[str, Any]:
        input_path = artifact_path.expanduser().resolve()
        if not input_path.exists():
            raise WorkflowError(f"Final-text cleanup artifact was not found: {input_path}")
        resolved_intent = intent_path.expanduser().resolve() if intent_path is not None else None
        if resolved_intent is not None and not resolved_intent.exists():
            raise WorkflowError(f"Typography intent was not found for final-text cleanup: {resolved_intent}")
        resolved_policy = policy_path.expanduser().resolve()
        if not resolved_policy.exists():
            raise WorkflowError(f"Source-text repair policy was not found: {resolved_policy}")
        resolved_output = (
            output_path.expanduser().resolve()
            if output_path is not None
            else self.default_cleanup_output_path(input_path)
        )
        cmd = [
            str(self.comfy_python),
            str(self.repo_root / "scripts" / "typography_tool.py"),
            "--repo-root",
            str(self.repo_root),
            "--models-root",
            str(self.models_root),
            "--comfy-workflows-dir",
            str(self.comfy_workflows_dir),
            "--comfy-output-dir",
            str(self.comfy_output_dir),
            "--references-root",
            str(self.references_root),
            "cleanup-final-text",
            "--artifact",
            str(input_path),
            "--policy",
            str(resolved_policy),
            "--output",
            str(resolved_output),
        ]
        if resolved_intent is not None:
            cmd.extend(["--intent", str(resolved_intent)])
        if repair_manifest_path is not None:
            resolved_repair_manifest = repair_manifest_path.expanduser().resolve()
            if not resolved_repair_manifest.exists():
                raise WorkflowError(f"Repair manifest was not found for final-text cleanup: {resolved_repair_manifest}")
            cmd.extend(["--repair-manifest", str(resolved_repair_manifest)])
        if debug_dir is not None:
            cmd.extend(["--debug-dir", str(debug_dir.expanduser().resolve())])
        completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
        try:
            summary = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            stderr = completed.stderr.strip() or completed.stdout.strip()
            raise WorkflowError(f"Final-text cleanup returned invalid JSON for {input_path}: {stderr}") from exc
        if completed.returncode != 0 and not summary.get("residual_validation", {}).get("failures"):
            stderr = completed.stderr.strip() or completed.stdout.strip()
            raise WorkflowError(f"Final-text cleanup failed for {input_path}: {stderr}")
        return summary

    def run_zero_letter_audit(
        self,
        artifact_path: Path,
        *,
        debug_dir: Path | None = None,
    ) -> dict[str, Any]:
        input_path = artifact_path.expanduser().resolve()
        if not input_path.exists():
            raise WorkflowError(f"Zero-letter audit artifact was not found: {input_path}")
        cmd = [
            str(self.comfy_python),
            str(self.repo_root / "scripts" / "typography_tool.py"),
            "--repo-root",
            str(self.repo_root),
            "--models-root",
            str(self.models_root),
            "--comfy-workflows-dir",
            str(self.comfy_workflows_dir),
            "--comfy-output-dir",
            str(self.comfy_output_dir),
            "--references-root",
            str(self.references_root),
            "audit-zero-letter",
            "--artifact",
            str(input_path),
        ]
        if debug_dir is not None:
            cmd.extend(["--debug-dir", str(debug_dir.expanduser().resolve())])
        completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
        try:
            summary = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            stderr = completed.stderr.strip() or completed.stdout.strip()
            raise WorkflowError(f"Zero-letter audit returned invalid JSON for {input_path}: {stderr}") from exc
        if completed.returncode != 0 and not summary.get("failures"):
            stderr = completed.stderr.strip() or completed.stdout.strip()
            raise WorkflowError(f"Zero-letter audit failed for {input_path}: {stderr}")
        return summary

    def run_source_text_audit(
        self,
        artifact_path: Path,
        *,
        intent_path: Path,
        debug_dir: Path | None = None,
    ) -> dict[str, Any]:
        input_path = artifact_path.expanduser().resolve()
        if not input_path.exists():
            raise WorkflowError(f"Source-text audit artifact was not found: {input_path}")
        resolved_intent = intent_path.expanduser().resolve()
        if not resolved_intent.exists():
            raise WorkflowError(f"Typography intent was not found for source-text audit: {resolved_intent}")
        cmd = [
            str(self.comfy_python),
            str(self.repo_root / "scripts" / "typography_tool.py"),
            "--repo-root",
            str(self.repo_root),
            "--models-root",
            str(self.models_root),
            "--comfy-workflows-dir",
            str(self.comfy_workflows_dir),
            "--comfy-output-dir",
            str(self.comfy_output_dir),
            "--references-root",
            str(self.references_root),
            "audit-source-text",
            "--artifact",
            str(input_path),
            "--intent",
            str(resolved_intent),
        ]
        if debug_dir is not None:
            cmd.extend(["--debug-dir", str(debug_dir.expanduser().resolve())])
        completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
        try:
            summary = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            stderr = completed.stderr.strip() or completed.stdout.strip()
            raise WorkflowError(f"Source-text audit returned invalid JSON for {input_path}: {stderr}") from exc
        if completed.returncode != 0 and not summary.get("failures"):
            stderr = completed.stderr.strip() or completed.stdout.strip()
            raise WorkflowError(f"Source-text audit failed for {input_path}: {stderr}")
        return summary

    def run_repaired_text_audit(
        self,
        artifact_path: Path,
        *,
        repair_manifest_path: Path,
        intent_path: Path,
        debug_dir: Path | None = None,
    ) -> dict[str, Any]:
        input_path = artifact_path.expanduser().resolve()
        if not input_path.exists():
            raise WorkflowError(f"Repaired-text audit artifact was not found: {input_path}")
        resolved_repair_manifest = repair_manifest_path.expanduser().resolve()
        if not resolved_repair_manifest.exists():
            raise WorkflowError(f"Repair manifest was not found for repaired-text audit: {resolved_repair_manifest}")
        resolved_intent = intent_path.expanduser().resolve()
        if not resolved_intent.exists():
            raise WorkflowError(f"Typography intent was not found for repaired-text audit: {resolved_intent}")
        cmd = [
            str(self.comfy_python),
            str(self.repo_root / "scripts" / "typography_tool.py"),
            "--repo-root",
            str(self.repo_root),
            "--models-root",
            str(self.models_root),
            "--comfy-workflows-dir",
            str(self.comfy_workflows_dir),
            "--comfy-output-dir",
            str(self.comfy_output_dir),
            "--references-root",
            str(self.references_root),
            "audit-repaired-text",
            "--artifact",
            str(input_path),
            "--repair-manifest",
            str(resolved_repair_manifest),
            "--intent",
            str(resolved_intent),
        ]
        if debug_dir is not None:
            cmd.extend(["--debug-dir", str(debug_dir.expanduser().resolve())])
        completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
        try:
            summary = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            stderr = completed.stderr.strip() or completed.stdout.strip()
            raise WorkflowError(f"Repaired-text audit returned invalid JSON for {input_path}: {stderr}") from exc
        if completed.returncode != 0 and not summary.get("failures"):
            stderr = completed.stderr.strip() or completed.stdout.strip()
            raise WorkflowError(f"Repaired-text audit failed for {input_path}: {stderr}")
        return summary

    def run_visual_qc_audit(
        self,
        artifact_path: Path,
        *,
        family: str,
        preset: str,
        semantic_profile: str = "",
        semantic_stage: str = "final",
        ban_scanlines: bool | None = None,
        contract_config: dict[str, Any] | None = None,
        debug_dir: Path | None = None,
        allow_invalid_json: bool = False,
    ) -> dict[str, Any]:
        input_path = artifact_path.expanduser().resolve()
        if not input_path.exists():
            raise WorkflowError(f"Visual QC artifact was not found: {input_path}")
        visual_qc_policy = visual_qc_policy_for(load_guardrail_policy(self.repo_root), family, preset)
        cmd = [
            str(self.comfy_python),
            str(self.repo_root / "scripts" / "typography_tool.py"),
            "--repo-root",
            str(self.repo_root),
            "--models-root",
            str(self.models_root),
            "--comfy-workflows-dir",
            str(self.comfy_workflows_dir),
            "--comfy-output-dir",
            str(self.comfy_output_dir),
            "--references-root",
            str(self.references_root),
            "audit-visual-qc",
            "--artifact",
            str(input_path),
        ]
        resolved_ban_scanlines = (
            bool(visual_qc_policy.get("ban_scanlines", False))
            if ban_scanlines is None
            else bool(ban_scanlines)
        )
        if resolved_ban_scanlines:
            cmd.append("--ban-scanlines")
        if semantic_profile:
            cmd.extend(
                [
                    "--family",
                    str(family),
                    "--preset",
                    str(preset),
                    "--semantic-profile",
                    str(semantic_profile),
                    "--semantic-stage",
                    str(semantic_stage),
                ]
            )
        if contract_config:
            cmd.extend(["--contract-config-json", json.dumps(contract_config, sort_keys=True)])
        if debug_dir is not None:
            cmd.extend(["--debug-dir", str(debug_dir.expanduser().resolve())])
        completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
        try:
            summary = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            stderr = completed.stderr.strip() or completed.stdout.strip()
            if allow_invalid_json:
                return {
                    "score": 0.0,
                    "threshold": 1.0,
                    "metrics": {},
                    "status": "failed",
                    "warnings": ["visual_qc_invalid_json"],
                    "failures": ["visual_qc_invalid_json"],
                    "semantic": {
                        "status": "failed",
                        "ranking_score": 0.0,
                    },
                    "debug_artifacts": [],
                    "parser_error": stderr,
                }
            raise WorkflowError(f"Visual QC returned invalid JSON for {input_path}: {stderr}") from exc
        if completed.returncode != 0 and not summary.get("failures"):
            stderr = completed.stderr.strip() or completed.stdout.strip()
            raise WorkflowError(f"Visual QC failed for {input_path}: {stderr}")
        return summary

    def run_render_typography_apply(
        self,
        family: str,
        preset: str,
        image_path: Path,
        repair_manifest_path: Path | None = None,
        output_path: Path | None = None,
        allow_validation_failure: bool = False,
    ) -> dict[str, Any]:
        sidecar = self.compiler.load_typography_sidecar(family, preset, required=True)
        if sidecar is None:
            raise WorkflowError(f"No typography sidecar configured for {family}/{preset}.")
        intent_path, _ = sidecar
        return self.run_typography_apply(
            target="still",
            artifact_path=image_path,
            intent_path=intent_path,
            repair_manifest_path=repair_manifest_path,
            output_path=output_path,
            allow_validation_failure=allow_validation_failure,
        )

    def write_typography_run_manifest(
        self,
        family: str,
        preset: str,
        input_image: Path,
        typography_summary: dict[str, Any],
        invocation: str,
        pipeline_id: str | None,
    ) -> Path:
        run_timestamp = utc_now_iso()
        run_dir = self.runs_root / family / preset
        run_dir.mkdir(parents=True, exist_ok=True)
        run_manifest_path = run_dir / f"{run_timestamp.replace(':', '').replace('-', '')}__typography_overlay.run.json"
        manifest = {
            "run_id": str(uuid.uuid4()),
            "created_at": run_timestamp,
            "invocation": invocation,
            "pipeline_id": pipeline_id,
            "family": family,
            "preset": preset,
            "stage": "typography_overlay",
            "base_final_image": str(input_image),
            "target": typography_summary["target"],
            "artifact_type": typography_summary["artifact_type"],
            "application_phase": typography_summary["application_phase"],
            "typography_sidecar": typography_summary["intent_path"],
            "typography_output_image": typography_summary["output_artifact"],
            "typography_mode": typography_summary["mode"],
            "typography_apply_stage": typography_summary["apply_stage_alias"],
            "typography_application_phase": typography_summary["application_phase"],
            "zone_count": typography_summary["zone_count"],
            "zones": typography_summary["zones"],
            "validation": typography_summary["validation"],
            "debug_artifacts": typography_summary.get("debug_artifacts", []),
        }
        if "post_typography_cleanup_run_manifest" in typography_summary:
            manifest["post_typography_cleanup_run_manifest"] = typography_summary["post_typography_cleanup_run_manifest"]
        if "post_typography_cleanup_output_image" in typography_summary:
            manifest["post_typography_cleanup_output_image"] = typography_summary["post_typography_cleanup_output_image"]
        if "post_typography_cleanup_validation" in typography_summary:
            manifest["post_typography_cleanup_validation"] = typography_summary["post_typography_cleanup_validation"]
        write_json(run_manifest_path, manifest)
        return run_manifest_path

    def write_zero_letter_audit_run_manifest(
        self,
        *,
        family: str,
        preset: str,
        stage: str,
        artifact_path: Path,
        audit_summary: dict[str, Any],
        invocation: str,
        pipeline_id: str | None,
        selected_seed: int,
    ) -> Path:
        run_timestamp = utc_now_iso()
        run_dir = self.runs_root / family / preset
        run_dir.mkdir(parents=True, exist_ok=True)
        filename = (
            f"{run_timestamp.replace(':', '').replace('-', '')}"
            f"__{stage}__zero_letter_audit__seed-{selected_seed}.run.json"
        )
        run_manifest_path = run_dir / filename
        manifest = {
            "run_id": str(uuid.uuid4()),
            "created_at": run_timestamp,
            "invocation": invocation,
            "pipeline_id": pipeline_id,
            "family": family,
            "preset": preset,
            "stage": stage,
            "validation_stage": "zero_letter_audit",
            "artifact_path": str(artifact_path),
            "status": audit_summary["status"],
            "unapproved_text": audit_summary["unapproved_text"],
            "warnings": audit_summary["warnings"],
            "failures": audit_summary["failures"],
            "debug_artifacts": audit_summary.get("debug_artifacts", []),
        }
        write_json(run_manifest_path, manifest)
        return run_manifest_path

    def write_source_text_audit_run_manifest(
        self,
        *,
        family: str,
        preset: str,
        stage: str,
        artifact_path: Path,
        intent_path: Path,
        audit_summary: dict[str, Any],
        invocation: str,
        pipeline_id: str | None,
        selected_seed: int,
    ) -> Path:
        run_timestamp = utc_now_iso()
        run_dir = self.runs_root / family / preset
        run_dir.mkdir(parents=True, exist_ok=True)
        filename = (
            f"{run_timestamp.replace(':', '').replace('-', '')}"
            f"__{stage}__pre_typography_source_text_audit__seed-{selected_seed}.run.json"
        )
        run_manifest_path = run_dir / filename
        manifest = {
            "run_id": str(uuid.uuid4()),
            "created_at": run_timestamp,
            "invocation": invocation,
            "pipeline_id": pipeline_id,
            "family": family,
            "preset": preset,
            "stage": stage,
            "validation_stage": "pre_typography_source_text_audit",
            "artifact_path": str(artifact_path),
            "intent_path": str(intent_path),
            "status": audit_summary["status"],
            "unapproved_text": audit_summary["unapproved_text"],
            "warnings": audit_summary["warnings"],
            "failures": audit_summary["failures"],
            "debug_artifacts": audit_summary.get("debug_artifacts", []),
        }
        write_json(run_manifest_path, manifest)
        return run_manifest_path

    def write_repair_run_manifest(
        self,
        *,
        family: str,
        preset: str,
        artifact_path: Path,
        repair_summary: dict[str, Any],
        invocation: str,
        pipeline_id: str | None,
        selected_seed: int,
    ) -> Path:
        run_timestamp = utc_now_iso()
        run_dir = self.runs_root / family / preset
        run_dir.mkdir(parents=True, exist_ok=True)
        filename = (
            f"{run_timestamp.replace(':', '').replace('-', '')}"
            f"__repair_source_text__seed-{selected_seed}.run.json"
        )
        run_manifest_path = run_dir / filename
        manifest = {
            "run_id": str(uuid.uuid4()),
            "created_at": run_timestamp,
            "invocation": invocation,
            "pipeline_id": pipeline_id,
            "family": family,
            "preset": preset,
            "stage": "repair_source_text",
            "artifact_path": str(artifact_path),
            **repair_summary,
        }
        write_json(run_manifest_path, manifest)
        return run_manifest_path

    def write_cleanup_run_manifest(
        self,
        *,
        family: str,
        preset: str,
        artifact_path: Path,
        cleanup_summary: dict[str, Any],
        invocation: str,
        pipeline_id: str | None,
        selected_seed: int,
    ) -> Path:
        run_timestamp = utc_now_iso()
        run_dir = self.runs_root / family / preset
        run_dir.mkdir(parents=True, exist_ok=True)
        filename = (
            f"{run_timestamp.replace(':', '').replace('-', '')}"
            f"__cleanup_final_text__seed-{selected_seed}.run.json"
        )
        run_manifest_path = run_dir / filename
        manifest = {
            "run_id": str(uuid.uuid4()),
            "created_at": run_timestamp,
            "invocation": invocation,
            "pipeline_id": pipeline_id,
            "family": family,
            "preset": preset,
            "stage": "cleanup_final_text",
            "artifact_path": str(artifact_path),
            **cleanup_summary,
        }
        write_json(run_manifest_path, manifest)
        return run_manifest_path

    def write_cleanup_text_audit_run_manifest(
        self,
        *,
        family: str,
        preset: str,
        artifact_path: Path,
        cleanup_manifest_path: Path,
        audit_summary: dict[str, Any],
        invocation: str,
        pipeline_id: str | None,
        selected_seed: int,
    ) -> Path:
        run_timestamp = utc_now_iso()
        run_dir = self.runs_root / family / preset
        run_dir.mkdir(parents=True, exist_ok=True)
        filename = (
            f"{run_timestamp.replace(':', '').replace('-', '')}"
            f"__cleanup_final_text__post_cleanup_text_audit__seed-{selected_seed}.run.json"
        )
        run_manifest_path = run_dir / filename
        manifest = {
            "run_id": str(uuid.uuid4()),
            "created_at": run_timestamp,
            "invocation": invocation,
            "pipeline_id": pipeline_id,
            "family": family,
            "preset": preset,
            "stage": "cleanup_final_text",
            "validation_stage": "post_cleanup_text_audit",
            "artifact_path": str(artifact_path),
            "cleanup_manifest_path": str(cleanup_manifest_path),
            "status": audit_summary["status"],
            "unapproved_text": audit_summary["unapproved_text"],
            "warnings": audit_summary["warnings"],
            "failures": audit_summary["failures"],
            "repair_region_results": audit_summary.get("repair_region_results", []),
            "debug_artifacts": audit_summary.get("debug_artifacts", []),
        }
        write_json(run_manifest_path, manifest)
        return run_manifest_path

    def write_visual_qc_run_manifest(
        self,
        *,
        family: str,
        preset: str,
        source_stage: str,
        validation_stage: str,
        artifact_path: Path,
        audit_summary: dict[str, Any],
        invocation: str,
        pipeline_id: str | None,
        candidate_seed: int,
    ) -> Path:
        run_timestamp = utc_now_iso()
        run_dir = self.runs_root / family / preset
        run_dir.mkdir(parents=True, exist_ok=True)
        filename = (
            f"{run_timestamp.replace(':', '').replace('-', '')}"
            f"__{validation_stage}__seed-{candidate_seed}.run.json"
        )
        run_manifest_path = run_dir / filename
        manifest = {
            "run_id": str(uuid.uuid4()),
            "created_at": run_timestamp,
            "invocation": invocation,
            "pipeline_id": pipeline_id,
            "family": family,
            "preset": preset,
            "stage": "visual_qc",
            "source_stage": source_stage,
            "validation_stage": validation_stage,
            "artifact_path": str(artifact_path),
            "score": audit_summary["score"],
            "threshold": audit_summary["threshold"],
            "metrics": audit_summary.get("metrics", {}),
            "status": audit_summary["status"],
            "warnings": audit_summary["warnings"],
            "failures": audit_summary["failures"],
            "semantic": audit_summary.get("semantic", {}),
            "debug_artifacts": audit_summary.get("debug_artifacts", []),
        }
        write_json(run_manifest_path, manifest)
        return run_manifest_path

    def write_repaired_text_audit_run_manifest(
        self,
        *,
        family: str,
        preset: str,
        stage: str,
        artifact_path: Path,
        repair_manifest_path: Path,
        intent_path: Path,
        audit_summary: dict[str, Any],
        invocation: str,
        pipeline_id: str | None,
        selected_seed: int,
    ) -> Path:
        run_timestamp = utc_now_iso()
        run_dir = self.runs_root / family / preset
        run_dir.mkdir(parents=True, exist_ok=True)
        filename = (
            f"{run_timestamp.replace(':', '').replace('-', '')}"
            f"__{stage}__post_repair_text_audit__seed-{selected_seed}.run.json"
        )
        run_manifest_path = run_dir / filename
        manifest = {
            "run_id": str(uuid.uuid4()),
            "created_at": run_timestamp,
            "invocation": invocation,
            "pipeline_id": pipeline_id,
            "family": family,
            "preset": preset,
            "stage": stage,
            "validation_stage": "post_repair_text_audit",
            "artifact_path": str(artifact_path),
            "repair_manifest_path": str(repair_manifest_path),
            "intent_path": str(intent_path),
            "status": audit_summary["status"],
            "unapproved_text": audit_summary["unapproved_text"],
            "warnings": audit_summary["warnings"],
            "failures": audit_summary["failures"],
            "repair_region_results": audit_summary.get("repair_region_results", []),
            "debug_artifacts": audit_summary.get("debug_artifacts", []),
        }
        write_json(run_manifest_path, manifest)
        return run_manifest_path

    def ensure_runtime_requirements(self, result: Any) -> None:
        requirements = result.manifest["stage_requirements"]
        assets_by_kind = {
            asset["kind"]: asset for asset in result.manifest["dependency_report"]["assets"]
        }
        missing: list[str] = []
        for kind in requirements["runtime_required_asset_kinds"]:
            asset = assets_by_kind.get(kind)
            if not asset or not asset["present"]:
                asset_path = asset["path"] if asset else ""
                missing.append(f"{kind} -> {asset_path}")
        if missing:
            raise WorkflowError(
                f"{result.family}/{result.base_preset} stage={result.stage} is not runnable. "
                f"Missing runtime assets: {', '.join(missing)}"
            )

    def queue_prompt(self, result: Any) -> str:
        payload = {
            "prompt": result.prompt,
            "client_id": "cascadeeffects-headless",
            "extra_data": {
                "extra_pnginfo": {
                    "workflow": result.workflow,
                }
            },
        }
        response = self.api_post("/prompt", payload)
        node_errors = response.get("node_errors") or {}
        if node_errors:
            raise WorkflowError(
                f"Comfy rejected prompt for {result.family}/{result.base_preset} stage={result.stage}: "
                f"{json.dumps(node_errors, indent=2)}"
            )
        prompt_id = response.get("prompt_id")
        if not prompt_id:
            raise WorkflowError(f"Comfy prompt response did not include prompt_id: {response}")
        return str(prompt_id)

    def write_run_manifest(
        self,
        result: Any,
        prompt_id: str,
        history_item: dict[str, Any],
        output_files: list[Path],
        source_image: str,
        subject_reference: dict[str, Any] | None,
        invocation: str,
        pipeline_id: str | None,
    ) -> Path:
        run_id = str(uuid.uuid4())
        run_timestamp = utc_now_iso()
        seed_value = int(result.params.get("selected_seed", result.params.get("seed", 0)))
        run_dir = self.runs_root / result.family / result.base_preset
        run_dir.mkdir(parents=True, exist_ok=True)
        filename = (
            f"{run_timestamp.replace(':', '').replace('-', '')}"
            f"__{result.stage}__seed-{seed_value}.run.json"
        )
        run_manifest_path = run_dir / filename
        run_manifest = {
            "run_id": run_id,
            "created_at": run_timestamp,
            "invocation": invocation,
            "pipeline_id": pipeline_id,
            "family": result.family,
            "preset": result.base_preset,
            "spec_preset": result.preset,
            "stage": result.stage,
            "prompt_id": prompt_id,
            "server_url": self.server_url,
            "selected_seed": result.params["selected_seed"],
            "seed": result.params["seed"],
            "variant_count": result.params["variant_count"],
            "source_image": source_image,
            "artifact_paths": {
                "workflow": str(result.generated_workflow_path),
                "prompt": str(result.generated_prompt_path),
                "manifest": str(result.generated_manifest_path),
                "sync_target": str(result.sync_target_path),
            },
            "output_files": [str(path) for path in output_files],
            "dimensions": {
                "width": int(result.params["width"]),
                "height": int(result.params["height"]),
            },
            "checkpoint": result.params["checkpoint"],
            "positive_prompt": result.params["positive_prompt"],
            "negative_prompt": result.params["negative_prompt"],
            "subject_reference": subject_reference or copy.deepcopy(result.manifest.get("subject_reference", {})),
            "plate_seed": copy.deepcopy(result.manifest.get("plate_seed", {})),
            "composition_control": copy.deepcopy(result.manifest.get("composition_control", {})),
            "midjourney_package": copy.deepcopy(result.manifest.get("midjourney_package", {})),
            "palette_lock": copy.deepcopy(result.manifest.get("palette_lock", {})),
            "spatial_mask": copy.deepcopy(result.manifest.get("spatial_mask", {})),
            "history": history_item,
        }
        write_json(run_manifest_path, run_manifest)
        return run_manifest_path

    def build_stage_result(self, family: str, base_preset: str, stage: str, overrides: dict[str, Any]) -> Any:
        self.ensure_runtime_paths()
        prepared_overrides, reference_runtime = self.prepare_subject_reference_overrides(
            family,
            base_preset,
            stage,
            overrides,
        )
        spec_path = self.compiler.resolve_stage_spec_path(family, base_preset, stage)
        result = self.compiler.build_one(spec_path, write_generated=True, overrides=prepared_overrides)
        if reference_runtime is not None:
            manifest_subject_reference = dict(result.manifest.get("subject_reference", {}))
            manifest_subject_reference.update(reference_runtime.get("subject_reference", {}))
            result.manifest["subject_reference"] = manifest_subject_reference
            manifest_plate_seed = dict(result.manifest.get("plate_seed", {}))
            if manifest_plate_seed.get("active"):
                manifest_plate_seed.update(
                    {
                        "source_path": manifest_subject_reference.get("seed_rgba_path", ""),
                        "preview_path": manifest_subject_reference.get("preview_path", ""),
                        "soft_mask_path": manifest_subject_reference.get("soft_mask_path", ""),
                        "runtime_image": manifest_subject_reference.get("staged_input_image", ""),
                        "staged_input_path": manifest_subject_reference.get("staged_input_path", ""),
                    }
                )
                result.manifest["plate_seed"] = manifest_plate_seed
            manifest_composition_control = dict(result.manifest.get("composition_control", {}))
            if manifest_composition_control.get("active"):
                manifest_composition_control.update(
                    {
                        "preview_path": manifest_subject_reference.get("preview_path", ""),
                        "vision_ref_path": manifest_subject_reference.get("vision_ref_path", ""),
                        "layout_mask_path": manifest_subject_reference.get("layout_mask_path", ""),
                        "runtime_image": manifest_subject_reference.get("staged_input_image", ""),
                        "runtime_mask": manifest_subject_reference.get("staged_input_mask", ""),
                        "staged_input_path": manifest_subject_reference.get("staged_input_path", ""),
                        "staged_mask_input_path": manifest_subject_reference.get("staged_mask_input_path", ""),
                    }
                )
                result.manifest["composition_control"] = manifest_composition_control
            manifest_midjourney_package = dict(result.manifest.get("midjourney_package", {}))
            if reference_runtime.get("midjourney_package"):
                manifest_midjourney_package.update(reference_runtime["midjourney_package"])
                result.manifest["midjourney_package"] = manifest_midjourney_package
            write_json(result.generated_manifest_path, result.manifest)
        return result

    def render_stage_once(
        self,
        family: str,
        base_preset: str,
        stage: str,
        overrides: dict[str, Any],
        invocation: str,
        pipeline_id: str | None = None,
    ) -> dict[str, Any]:
        result = self.build_stage_result(family, base_preset, stage, overrides)
        self.ensure_runtime_requirements(result)
        self.start_server()
        prompt_id = self.queue_prompt(result)
        history_item = self.wait_for_prompt(prompt_id)
        output_files = self.collect_output_files(history_item)
        source_image = str(result.params.get("source_image", ""))
        run_manifest_path = self.write_run_manifest(
            result=result,
            prompt_id=prompt_id,
            history_item=history_item,
            output_files=output_files,
            source_image=source_image,
            subject_reference=copy.deepcopy(result.manifest.get("subject_reference", {})),
            invocation=invocation,
            pipeline_id=pipeline_id,
        )
        output_text = ", ".join(str(path) for path in output_files) if output_files else "none"
        print(
            f"RENDER {result.family}/{result.base_preset} stage={result.stage} "
            f"prompt_id={prompt_id} outputs={output_text}"
        )
        print(f"INFO  run manifest -> {run_manifest_path}")
        return {
            "result": result,
            "prompt_id": prompt_id,
            "history_item": history_item,
            "output_files": output_files,
            "run_manifest_path": run_manifest_path,
        }


def normalize_seed_overrides(overrides: dict[str, Any], seed: int, *, seed_mode: str = "fixed") -> dict[str, Any]:
    normalized = dict(overrides)
    normalized["seed"] = seed
    normalized["selected_seed"] = seed
    normalized["seed_mode"] = seed_mode
    return normalized


def contract_config_from_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    style_contract = manifest.get("style_contract", {})
    if not isinstance(style_contract, dict) or not style_contract:
        return {}
    contract_metrics = style_contract.get("contract_metrics", {})
    if not isinstance(contract_metrics, dict) or not contract_metrics:
        return {}
    return {
        "style_id": str(manifest.get("style_profile", "")).strip(),
        "contract_metrics": contract_metrics,
        "caption_safe_defaults": style_contract.get("caption_safe_defaults", {}),
        "caption_safe_zone": manifest.get("caption_safe_zone", {}),
        "negative_prompt_defaults": style_contract.get("negative_prompt_defaults", []),
        "composition_control": manifest.get("composition_control", {}),
    }


def contract_config_from_run(
    run_record: dict[str, Any],
    *,
    fallback_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = run_record.get("result") if isinstance(run_record, dict) else None
    manifest = getattr(result, "manifest", None)
    if isinstance(manifest, dict):
        return contract_config_from_manifest(manifest)
    if isinstance(fallback_manifest, dict):
        return contract_config_from_manifest(fallback_manifest)
    return {}


def resolve_quality_profile_settings(
    *,
    family: str,
    pipeline_strategy: dict[str, Any],
    quality_profile: str,
) -> dict[str, Any]:
    if quality_profile not in QUALITY_PROFILES:
        raise WorkflowError(f"Unsupported quality profile {quality_profile!r}.")
    base_candidate_count = max(1, int(pipeline_strategy.get("draft_candidate_count", 1) or 1))
    if quality_profile == "fast":
        return {
            "quality_profile": quality_profile,
            "draft_candidate_count": 1,
            "use_hero_refine": False,
            "hero_model": "",
            "hero_refine_denoise": None,
        }
    if quality_profile == "hero":
        base_candidate_count = max(base_candidate_count, 8)
    return {
        "quality_profile": quality_profile,
        "draft_candidate_count": base_candidate_count,
        "use_hero_refine": True,
        "hero_model": str(pipeline_strategy.get("hero_model", "")).strip(),
        "hero_refine_denoise": float(pipeline_strategy.get("hero_refine_denoise", 0.0) or 0.0),
    }


def package_grid_softpass_policy(manifest: dict[str, Any]) -> dict[str, Any] | None:
    package_manifest = manifest.get("midjourney_package", {})
    if not isinstance(package_manifest, dict) or not bool(package_manifest.get("active")):
        return None
    adapter = package_manifest.get("adapter", {})
    if not isinstance(adapter, dict) or not bool(adapter.get("active")):
        return None
    softpass = adapter.get("draft_visual_softpass", {})
    if not isinstance(softpass, dict) or not bool(softpass.get("enabled")):
        return None
    allowed_visual_failures = {
        str(item).strip()
        for item in softpass.get("allowed_visual_failures", [])
        if str(item).strip()
    }
    if not allowed_visual_failures:
        return None
    return {
        "allowed_visual_failures": allowed_visual_failures,
        "hard_block_failures": set(MIDJOURNEY_ADAPTER_HARD_BLOCK_FAILURES),
    }


def package_grid_ranking_policy(manifest: dict[str, Any]) -> dict[str, Any] | None:
    package_manifest = manifest.get("midjourney_package", {})
    if not isinstance(package_manifest, dict) or not bool(package_manifest.get("active")):
        return None
    adapter = package_manifest.get("adapter", {})
    if not isinstance(adapter, dict) or not bool(adapter.get("active")):
        return None
    ranking_bias_tags = tuple(
        item
        for item in (
            str(raw).strip()
            for raw in adapter.get("ranking_bias_tags", [])
        )
        if item
    )
    unsupported_tags = sorted(set(ranking_bias_tags) - MIDJOURNEY_ADAPTER_RANKING_BIAS_TAGS)
    if unsupported_tags:
        raise WorkflowError(
            f"Unsupported MidJourney adapter ranking tags: {', '.join(unsupported_tags)}"
        )
    if not ranking_bias_tags:
        return None
    return {
        "steer_target": str(adapter.get("steer_target", "")).strip(),
        "steer_keep_traits": [
            str(item).strip()
            for item in adapter.get("steer_keep_traits", [])
            if str(item).strip()
        ],
        "steer_avoid_traits": [
            str(item).strip()
            for item in adapter.get("steer_avoid_traits", [])
            if str(item).strip()
        ],
        "ranking_bias_tags": ranking_bias_tags,
    }


def candidate_softpass_eligible(candidate_qc_summary: dict[str, Any], policy: dict[str, Any] | None) -> bool:
    if not policy:
        return False
    semantic = candidate_qc_summary.get("semantic", {})
    if not isinstance(semantic, dict) or str(semantic.get("status", "")).strip() != "ok":
        return False
    failures = {
        str(item).strip()
        for item in candidate_qc_summary.get("failures", [])
        if str(item).strip()
    }
    if not failures:
        return False
    if failures & set(policy.get("hard_block_failures", set())):
        return False
    return failures <= set(policy.get("allowed_visual_failures", set()))


def _semantic_text_blob(candidate_qc_summary: dict[str, Any]) -> str:
    semantic = candidate_qc_summary.get("semantic", {})
    parts: list[str] = []
    if isinstance(semantic, dict):
        for field in ("notes",):
            value = semantic.get(field)
            if isinstance(value, str) and value.strip():
                parts.append(value.strip())
        for field in ("issues", "warnings", "failures", "hard_fail_tags"):
            values = semantic.get(field, [])
            if isinstance(values, list):
                parts.extend(str(item).strip() for item in values if str(item).strip())
    failures = candidate_qc_summary.get("failures", [])
    if isinstance(failures, list):
        parts.extend(str(item).strip() for item in failures if str(item).strip())
    return " ".join(parts).lower()


def _image_ranking_signals(artifact_path: Path) -> dict[str, float]:
    if Image is None or ImageFilter is None or ImageOps is None or not artifact_path.exists():
        return {}
    try:
        with Image.open(artifact_path) as source_image:
            image = ImageOps.exif_transpose(source_image).convert("RGB").resize((256, 256))
    except OSError:
        return {}
    pixels = list(image.getdata())
    if not pixels:
        return {}

    sample_pixels = pixels[::4]
    saturation_total = 0.0
    brightness_total = 0.0
    cool_cast_total = 0.0
    accent_columns: set[int] = set()
    width, height = image.size
    for index, (red, green, blue) in enumerate(sample_pixels):
        hue, saturation, value = colorsys.rgb_to_hsv(red / 255.0, green / 255.0, blue / 255.0)
        saturation_total += saturation
        brightness_total += value
        cool_cast_total += max(0.0, blue - red) / 255.0
        if saturation >= 0.45 and value >= 0.25 and (hue <= 0.06 or hue >= 0.94 or (0.06 < hue < 0.12 and red > blue)):
            source_index = index * 4
            if source_index < len(pixels):
                accent_columns.add(source_index % width)
    sample_count = max(1, len(sample_pixels))

    edges = image.convert("L").filter(ImageFilter.FIND_EDGES)
    left_crop = edges.crop((0, 0, width // 3, height))
    center_crop = edges.crop((width // 3, 0, (width * 2) // 3, height))
    right_crop = edges.crop(((width * 2) // 3, 0, width, height))

    def mean_intensity(crop_image: Any) -> float:
        data = list(crop_image.getdata())
        if not data:
            return 0.0
        return float(sum(data) / len(data)) / 255.0

    accent_cluster_count = 0
    last_column: int | None = None
    for column in sorted(accent_columns):
        if last_column is None or column > last_column + 6:
            accent_cluster_count += 1
        last_column = column

    return {
        "mean_saturation": saturation_total / sample_count,
        "mean_brightness": brightness_total / sample_count,
        "cool_cast": cool_cast_total / sample_count,
        "left_edge_mean": mean_intensity(left_crop),
        "center_edge_mean": mean_intensity(center_crop),
        "right_edge_mean": mean_intensity(right_crop),
        "accent_cluster_count": float(accent_cluster_count),
    }


def candidate_ranking_bias(
    candidate_qc_summary: dict[str, Any],
    *,
    ranking_policy: dict[str, Any] | None,
    artifact_path: Path,
) -> tuple[float, dict[str, float]]:
    if not ranking_policy:
        return 0.0, {}
    failures = {
        str(item).strip()
        for item in candidate_qc_summary.get("failures", [])
        if str(item).strip()
    }
    semantic_text = _semantic_text_blob(candidate_qc_summary)
    image_signals = _image_ranking_signals(artifact_path)
    bias_breakdown: dict[str, float] = {}

    def has_any_text_phrase(*phrases: str) -> bool:
        return any(str(phrase).lower() in semantic_text for phrase in phrases if str(phrase).strip())

    for tag in ranking_policy.get("ranking_bias_tags", ()):
        score = 0.0
        if tag == "single_object_severity":
            score += 1.35 if "subject_count_exceeds_limit" not in failures else -1.35
            if "multiple_shuttle_heroes" in failures:
                score -= 1.25
            if "duplicate_human_identity" in failures:
                score -= 1.0
        elif tag == "compressed_monolith":
            if "center_weighted_primary_subject" in failures:
                score -= 0.9
            else:
                score += 0.45
            if "symmetry_too_high" in failures:
                score -= 0.9
            else:
                score += 0.35
            if image_signals and image_signals.get("left_edge_mean", 0.0) > image_signals.get("right_edge_mean", 0.0) * 1.05:
                score += 0.45
            if has_any_text_phrase("rocket on the pad", "full shuttle", "launch photo", "orbiter"):
                score -= 0.75
        elif tag == "one_accent_only":
            if "more_than_one_saturated_accent" in failures:
                score -= 1.1
            else:
                score += 0.55
            if "palette_discipline_below_threshold" in failures:
                score -= 0.65
            else:
                score += 0.35
            accent_cluster_count = int(round(image_signals.get("accent_cluster_count", 0.0)))
            if accent_cluster_count == 1:
                score += 0.55
            elif accent_cluster_count > 1:
                score -= 0.8
        elif tag == "cold_pipe_detail":
            if has_any_text_phrase("pipe", "pipes", "gantry", "steel", "industrial", "infrastructure"):
                score += 0.55
            if has_any_text_phrase("rocket on the pad", "tower", "roadway", "launch site"):
                score -= 0.55
            if image_signals and image_signals.get("left_edge_mean", 0.0) > max(
                image_signals.get("center_edge_mean", 0.0),
                image_signals.get("right_edge_mean", 0.0),
            ) * 1.08:
                score += 0.45
        elif tag == "winter_haze":
            if has_any_text_phrase("winter", "cold", "ice", "icy", "frost", "fog", "haze", "snow"):
                score += 0.55
            if image_signals:
                if image_signals.get("mean_saturation", 1.0) <= 0.24:
                    score += 0.45
                if image_signals.get("cool_cast", 0.0) >= 0.035:
                    score += 0.35
                if image_signals.get("mean_brightness", 0.0) >= 0.62:
                    score += 0.2
        elif tag == "industrial_frost_signal":
            if has_any_text_phrase("industrial", "infrastructure", "gantry", "signal"):
                score += 0.45
            if has_any_text_phrase("person", "people", "crowd", "road", "roadway", "truck", "vehicle"):
                score -= 0.65
            if "scenic_exterior_drift" in failures:
                score -= 1.0
            if "subject_count_exceeds_limit" in failures:
                score -= 0.45
            else:
                score += 0.25
        elif tag == "accurate_shuttle_stack":
            if has_any_text_phrase(
                "space shuttle",
                "orbiter",
                "external tank",
                "solid rocket booster",
                "twin boosters",
                "winged orbiter",
            ):
                score += 0.95
            if has_any_text_phrase(
                "generic rocket",
                "toy rocket",
                "single-stick rocket",
                "missile",
                "capsule rocket",
                "needle rocket",
                "conical nose rocket",
            ):
                score -= 1.15
            if has_any_text_phrase("front exhaust", "nose exhaust", "side exhaust", "plume from fuselage"):
                score -= 1.25
            if "unrecognizable_anchor" in failures:
                score -= 1.1
            if "multiple_shuttle_heroes" in failures:
                score -= 0.75
        if score:
            bias_breakdown[str(tag)] = round(score, 4)

    return round(sum(bias_breakdown.values()), 4), bias_breakdown


def is_opening_tableau_request(family: str, preset: str) -> bool:
    return str(family).strip() == "scene_still" and str(preset).strip().rsplit("__", 1)[0] == OPENING_TABLEAU_PRESET


def require_opening_tableau_payload(overrides: dict[str, Any]) -> dict[str, Any]:
    payload = overrides.get("opening_payload")
    if not isinstance(payload, dict):
        raise WorkflowError(
            "opening_culture_cluster requires a structured `opening_payload` override with slot descriptors and asset paths."
        )
    slots = payload.get("slots")
    if not isinstance(slots, list) or not slots:
        raise WorkflowError("opening_culture_cluster requires at least one ordered slot in opening_payload.slots.")
    subject_slots = [
        slot for slot in slots if isinstance(slot, dict) and str(slot.get("role", "")).strip() == "subject_object"
    ]
    if len(subject_slots) != 1:
        raise WorkflowError("opening_culture_cluster requires exactly one subject_object slot in opening_payload.")
    for slot in slots:
        if not isinstance(slot, dict):
            raise WorkflowError("opening_culture_cluster opening_payload.slots entries must be objects.")
        slot_id = str(slot.get("slot_id", "")).strip()
        asset_path = str(slot.get("asset_path", "")).strip()
        if not slot_id:
            raise WorkflowError("opening_culture_cluster opening_payload slots require slot_id.")
        if not asset_path:
            raise WorkflowError(f"opening_culture_cluster slot `{slot_id}` is missing asset_path.")
    return payload


def derive_opening_tableau_prompt_overrides(payload: dict[str, Any]) -> dict[str, Any]:
    slots = [slot for slot in payload.get("slots", []) if isinstance(slot, dict)]
    support_labels = [
        str(slot.get("display_label", "")).strip() or str(slot.get("slot_id", "")).strip()
        for slot in slots
        if str(slot.get("role", "")).strip() != "subject_object"
    ]
    subject_slot = next(
        slot for slot in slots if str(slot.get("role", "")).strip() == "subject_object"
    )
    subject_descriptor = str(payload.get("subject_descriptor", "")).strip() or str(
        subject_slot.get("visual_descriptor", "")
    ).strip() or str(subject_slot.get("display_label", "")).strip()
    required_reads = [
        str(label).strip()
        for label in (payload.get("required_reads") or [])
        if str(label).strip()
    ]
    if not required_reads:
        required_reads = [
            str(slot.get("display_label", "")).strip() or str(slot.get("slot_id", "")).strip()
            for slot in slots
        ]
    return {
        "opening_payload": payload,
        "opening_anchor_fragment": f"central dominant subject isolated for the pull-in: {subject_descriptor}",
        "opening_support_summary": ", ".join(support_labels),
        "opening_required_reads": ", ".join(required_reads),
    }


def build_opening_tableau_layout(width: int, height: int, support_slots: list[dict[str, Any]]) -> dict[str, Any]:
    if width <= 0 or height <= 0:
        raise WorkflowError("Opening tableau layout requires positive dimensions.")
    subject_box = {
        "x": int(round(width * 0.30)),
        "y": int(round(height * 0.08)),
        "width": int(round(width * 0.40)),
        "height": int(round(height * 0.80)),
        "rotation_degrees": 0.0,
    }
    templates = [
        {"x": 0.03, "y": 0.10, "width": 0.16, "height": 0.16, "rotation_degrees": -11.0},
        {"x": 0.09, "y": 0.39, "width": 0.18, "height": 0.21, "rotation_degrees": -5.0},
        {"x": 0.07, "y": 0.74, "width": 0.14, "height": 0.14, "rotation_degrees": 7.0},
        {"x": 0.445, "y": 0.0, "width": 0.11, "height": 0.07, "rotation_degrees": -2.0},
        {"x": 0.80, "y": 0.24, "width": 0.13, "height": 0.13, "rotation_degrees": 8.0},
        {"x": 0.74, "y": 0.72, "width": 0.16, "height": 0.15, "rotation_degrees": -6.0},
        {"x": 0.445, "y": 0.88, "width": 0.12, "height": 0.09, "rotation_degrees": 1.5},
        {"x": 0.72, "y": 0.49, "width": 0.18, "height": 0.18, "rotation_degrees": 3.0},
    ]
    placements: list[dict[str, Any]] = []
    for index, slot in enumerate(support_slots):
        template = templates[min(index, len(templates) - 1)]
        placements.append(
            {
                "slot_id": str(slot.get("slot_id", "")).strip(),
                "display_label": str(slot.get("display_label", "")).strip(),
                "role": str(slot.get("role", "")).strip() or "supporting_object",
                "x": int(round(width * float(template["x"]))),
                "y": int(round(height * float(template["y"]))),
                "width": int(round(width * float(template["width"]))),
                "height": int(round(height * float(template["height"]))),
                "rotation_degrees": float(template["rotation_degrees"]),
            }
        )
    return {
        "canvas": {"width": int(width), "height": int(height)},
        "subject": subject_box,
        "supports": placements,
    }


def compose_opening_tableau_draft(
    runner: HeadlessComfyRunner,
    *,
    family: str,
    preset: str,
    payload: dict[str, Any],
    selected_seed: int,
    pipeline_id: str,
    invocation: str,
    width: int,
    height: int,
) -> dict[str, Any]:
    slots = [slot for slot in payload.get("slots", []) if isinstance(slot, dict)]
    subject_slot = next(slot for slot in slots if str(slot.get("role", "")).strip() == "subject_object")
    support_slots = [slot for slot in slots if str(slot.get("role", "")).strip() != "subject_object"]
    layout = build_opening_tableau_layout(width, height, support_slots)
    layout["subject"]["slot_id"] = str(subject_slot.get("slot_id", "")).strip()
    layout["subject"]["display_label"] = str(subject_slot.get("display_label", "")).strip()
    layout["subject"]["role"] = "subject_object"

    run_timestamp = utc_now_iso()
    safe_stamp = run_timestamp.replace(":", "").replace("-", "")
    run_dir = runner.runs_root / family / preset
    run_dir.mkdir(parents=True, exist_ok=True)
    debug_dir = run_dir / "debug" / f"{OPENING_TABLEAU_STAGE}__seed-{selected_seed}"
    plates_dir = debug_dir / "plates"
    plates_dir.mkdir(parents=True, exist_ok=True)
    payload_path = run_dir / f"{safe_stamp}__{OPENING_TABLEAU_STAGE}__seed-{selected_seed}.payload.json"
    layout_path = run_dir / f"{safe_stamp}__{OPENING_TABLEAU_STAGE}__seed-{selected_seed}.layout.json"
    write_json(payload_path, payload)
    write_json(layout_path, layout)

    composite_dir = runner.comfy_output_dir / "cascadeeffects" / family / preset / "draft"
    composite_dir.mkdir(parents=True, exist_ok=True)
    composite_output_path = composite_dir / f"{preset}_draft_seed-{selected_seed}.png"

    cmd = [
        str(runner.comfy_python),
        str(runner.repo_root / "scripts" / "opening_tableau_tool.py"),
        "compose",
        "--payload",
        str(payload_path),
        "--layout",
        str(layout_path),
        "--output",
        str(composite_output_path),
        "--plates-dir",
        str(plates_dir),
    ]
    completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip()
        raise WorkflowError(f"Opening tableau composition failed for {family}/{preset}: {stderr}")
    try:
        composition_summary = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        stderr = completed.stderr.strip() or completed.stdout.strip()
        raise WorkflowError(f"Opening tableau composition returned invalid JSON: {stderr}") from exc
    if not composite_output_path.exists():
        raise WorkflowError(f"Opening tableau composition did not create {composite_output_path}.")

    run_manifest_path = run_dir / f"{safe_stamp}__{OPENING_TABLEAU_STAGE}__seed-{selected_seed}.run.json"
    write_json(
        run_manifest_path,
        {
            "run_id": str(uuid.uuid4()),
            "created_at": run_timestamp,
            "invocation": invocation,
            "pipeline_id": pipeline_id,
            "family": family,
            "preset": preset,
            "stage": OPENING_TABLEAU_STAGE,
            "selected_seed": int(selected_seed),
            "artifact_path": str(composite_output_path),
            "payload_path": str(payload_path),
            "layout_path": str(layout_path),
            "plates_dir": str(plates_dir),
            "composition": composition_summary,
        },
    )
    return {
        "output_path": composite_output_path,
        "run_manifest_path": run_manifest_path,
        "composition": composition_summary,
    }


def generate_draft_candidates(
    *,
    runner: HeadlessComfyRunner,
    args: argparse.Namespace,
    overrides: dict[str, Any],
    draft_probe: Any,
    pipeline_id: str,
    candidate_seeds: list[int],
    semantic_profile: str,
    softpass_policy: dict[str, Any] | None,
    ranking_policy: dict[str, Any] | None,
    invocation: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    draft_candidates: list[dict[str, Any]] = []
    candidate_scores: dict[str, dict[str, Any]] = {}
    pre_refine_semantic: list[dict[str, Any]] = []
    if is_opening_tableau_request(args.family, args.preset):
        payload = require_opening_tableau_payload(overrides)
        seed = int(candidate_seeds[0])
        compose_run = compose_opening_tableau_draft(
            runner,
            family=args.family,
            preset=args.preset,
            payload=payload,
            selected_seed=seed,
            pipeline_id=pipeline_id,
            invocation=invocation,
            width=int(draft_probe.params.get("width", 0) or 0),
            height=int(draft_probe.params.get("height", 0) or 0),
        )
        draft_artifact = Path(compose_run["output_path"])
        candidate_record: dict[str, Any] = {
            "seed": seed,
            "draft_stage": OPENING_TABLEAU_STAGE,
            "draft_run_manifest": str(compose_run["run_manifest_path"]),
            "draft_output": str(draft_artifact),
            "semantic_qc_manifest": "",
            "semantic_status": "skipped",
            "semantic_profile_status": "skipped",
            "semantic_failures": [],
            "ranking_score": 0.0,
            "ranking_bias_score": 0.0,
            "ranking_bias_breakdown": {},
            "selection_score": 0.0,
            "softpass_eligible": False,
        }
        if semantic_profile:
            candidate_debug_dir = (
                runner.runs_root
                / args.family
                / args.preset
                / "debug"
                / f"pre_refine_semantic_qc__seed-{seed}"
            )
            candidate_qc_summary = runner.run_visual_qc_audit(
                draft_artifact,
                family=args.family,
                preset=args.preset,
                semantic_profile=semantic_profile,
                semantic_stage="candidate",
                ban_scanlines=False,
                contract_config=contract_config_from_manifest(draft_probe.manifest),
                debug_dir=candidate_debug_dir,
                allow_invalid_json=args.delivery_mode == "advisory",
            )
            candidate_qc_run_path = runner.write_visual_qc_run_manifest(
                family=args.family,
                preset=args.preset,
                source_stage=OPENING_TABLEAU_STAGE,
                validation_stage="pre_refine_semantic_qc",
                artifact_path=draft_artifact,
                audit_summary=candidate_qc_summary,
                invocation=invocation,
                pipeline_id=pipeline_id,
                candidate_seed=seed,
            )
            candidate_record["semantic_qc_manifest"] = str(candidate_qc_run_path)
            candidate_record["semantic_status"] = str(candidate_qc_summary["status"])
            candidate_record["semantic_profile_status"] = str(candidate_qc_summary.get("semantic", {}).get("status", ""))
            candidate_record["semantic_failures"] = list(candidate_qc_summary.get("failures", []))
            candidate_record["ranking_score"] = float(
                candidate_qc_summary.get("semantic", {}).get("ranking_score", 0.0)
            )
            ranking_bias_score, ranking_bias_breakdown = candidate_ranking_bias(
                candidate_qc_summary,
                ranking_policy=ranking_policy,
                artifact_path=draft_artifact,
            )
            candidate_record["ranking_bias_score"] = float(ranking_bias_score)
            candidate_record["ranking_bias_breakdown"] = ranking_bias_breakdown
            candidate_record["selection_score"] = float(candidate_record["ranking_score"]) + float(ranking_bias_score)
            candidate_record["softpass_eligible"] = candidate_softpass_eligible(candidate_qc_summary, softpass_policy)
            pre_refine_semantic.append(
                {
                    "seed": seed,
                    "artifact_path": str(draft_artifact),
                    "manifest": str(candidate_qc_run_path),
                    "status": str(candidate_qc_summary["status"]),
                    "failures": list(candidate_qc_summary.get("failures", [])),
                    "ranking_score": float(candidate_record["ranking_score"]),
                    "ranking_bias_score": float(candidate_record["ranking_bias_score"]),
                    "ranking_bias_breakdown": copy.deepcopy(candidate_record["ranking_bias_breakdown"]),
                    "selection_score": float(candidate_record["selection_score"]),
                    "semantic_profile_status": candidate_record["semantic_profile_status"],
                    "softpass_eligible": bool(candidate_record["softpass_eligible"]),
                }
            )
        draft_candidates.append(candidate_record)
        candidate_scores[str(seed)] = {
            "status": candidate_record["semantic_status"],
            "semantic_profile_status": candidate_record["semantic_profile_status"],
            "failures": candidate_record["semantic_failures"],
            "ranking_score": candidate_record["ranking_score"],
            "ranking_bias_score": candidate_record["ranking_bias_score"],
            "ranking_bias_breakdown": copy.deepcopy(candidate_record["ranking_bias_breakdown"]),
            "selection_score": candidate_record["selection_score"],
            "softpass_eligible": bool(candidate_record["softpass_eligible"]),
        }
        return draft_candidates, candidate_scores, pre_refine_semantic

    for seed in candidate_seeds:
        draft_overrides = normalize_seed_overrides(overrides, seed)
        draft_overrides["variant_count"] = 1
        draft_run = runner.render_stage_once(
            args.family,
            args.preset,
            "draft_txt2img",
            draft_overrides,
            invocation=invocation,
            pipeline_id=pipeline_id,
        )
        draft_outputs = draft_run["output_files"]
        if not draft_outputs:
            raise WorkflowError(f"Draft stage for {args.family}/{args.preset} did not produce any output files.")
        draft_artifact = draft_outputs[0]
        candidate_record = {
            "seed": int(seed),
            "draft_stage": "draft_txt2img",
            "draft_run_manifest": str(draft_run["run_manifest_path"]),
            "draft_output": str(draft_artifact),
            "semantic_qc_manifest": "",
            "semantic_status": "skipped",
            "semantic_profile_status": "skipped",
            "semantic_failures": [],
            "ranking_score": 0.0,
            "ranking_bias_score": 0.0,
            "ranking_bias_breakdown": {},
            "selection_score": 0.0,
            "softpass_eligible": False,
        }
        if semantic_profile:
            candidate_debug_dir = (
                runner.runs_root
                / args.family
                / args.preset
                / "debug"
                / f"pre_refine_semantic_qc__seed-{seed}"
            )
            candidate_qc_summary = runner.run_visual_qc_audit(
                draft_artifact,
                family=args.family,
                preset=args.preset,
                semantic_profile=semantic_profile,
                semantic_stage="candidate",
                ban_scanlines=False,
                contract_config=contract_config_from_run(draft_run, fallback_manifest=draft_probe.manifest),
                debug_dir=candidate_debug_dir,
                allow_invalid_json=args.delivery_mode == "advisory",
            )
            candidate_qc_run_path = runner.write_visual_qc_run_manifest(
                family=args.family,
                preset=args.preset,
                source_stage="draft_txt2img",
                validation_stage="pre_refine_semantic_qc",
                artifact_path=draft_artifact,
                audit_summary=candidate_qc_summary,
                invocation=invocation,
                pipeline_id=pipeline_id,
                candidate_seed=seed,
            )
            candidate_record["semantic_qc_manifest"] = str(candidate_qc_run_path)
            candidate_record["semantic_status"] = str(candidate_qc_summary["status"])
            candidate_record["semantic_profile_status"] = str(candidate_qc_summary.get("semantic", {}).get("status", ""))
            candidate_record["semantic_failures"] = list(candidate_qc_summary.get("failures", []))
            candidate_record["ranking_score"] = float(
                candidate_qc_summary.get("semantic", {}).get("ranking_score", 0.0)
            )
            ranking_bias_score, ranking_bias_breakdown = candidate_ranking_bias(
                candidate_qc_summary,
                ranking_policy=ranking_policy,
                artifact_path=draft_artifact,
            )
            candidate_record["ranking_bias_score"] = float(ranking_bias_score)
            candidate_record["ranking_bias_breakdown"] = ranking_bias_breakdown
            candidate_record["selection_score"] = float(candidate_record["ranking_score"]) + float(ranking_bias_score)
            candidate_record["softpass_eligible"] = candidate_softpass_eligible(candidate_qc_summary, softpass_policy)
            pre_refine_semantic.append(
                {
                    "seed": int(seed),
                    "artifact_path": str(draft_artifact),
                    "manifest": str(candidate_qc_run_path),
                    "status": str(candidate_qc_summary["status"]),
                    "failures": list(candidate_qc_summary.get("failures", [])),
                    "ranking_score": float(candidate_record["ranking_score"]),
                    "ranking_bias_score": float(candidate_record["ranking_bias_score"]),
                    "ranking_bias_breakdown": copy.deepcopy(candidate_record["ranking_bias_breakdown"]),
                    "selection_score": float(candidate_record["selection_score"]),
                    "semantic_profile_status": candidate_record["semantic_profile_status"],
                    "softpass_eligible": bool(candidate_record["softpass_eligible"]),
                }
            )
        draft_candidates.append(candidate_record)
        candidate_scores[str(seed)] = {
            "status": candidate_record["semantic_status"],
            "semantic_profile_status": candidate_record["semantic_profile_status"],
            "failures": candidate_record["semantic_failures"],
            "ranking_score": candidate_record["ranking_score"],
            "ranking_bias_score": candidate_record["ranking_bias_score"],
            "ranking_bias_breakdown": copy.deepcopy(candidate_record["ranking_bias_breakdown"]),
            "selection_score": candidate_record["selection_score"],
            "softpass_eligible": bool(candidate_record["softpass_eligible"]),
        }
    return draft_candidates, candidate_scores, pre_refine_semantic


def ensure_quality_profile_runtime(
    *,
    runner: Any,
    family: str,
    preset: str,
    quality_settings: dict[str, Any],
) -> None:
    if not quality_settings.get("use_hero_refine"):
        return
    hero_model = str(quality_settings.get("hero_model", "")).strip()
    if not hero_model:
        return
    models_root = getattr(runner, "models_root", None)
    if models_root is None:
        return
    model_name = hero_model if hero_model.endswith(".safetensors") else f"{hero_model}.safetensors"
    model_path = Path(models_root) / "diffusion_models" / model_name
    if model_path.exists():
        return
    raise WorkflowError(
        f"Quality profile {quality_settings['quality_profile']!r} for {family}/{preset} requires hero model "
        f"{model_name!r} in {model_path.parent}. Install the full FLUX assets or use "
        f"--quality-profile fast until the hero model is present."
    )


def derive_candidate_seeds(
    *,
    base_seed: int,
    seed_policy: str,
    candidate_count: int,
) -> list[int]:
    if seed_policy == "fixed":
        return [int(base_seed)]
    return [int(base_seed) + index for index in range(max(1, int(candidate_count)))]


def command_server(runner: HeadlessComfyRunner, args: argparse.Namespace) -> int:
    if args.action == "status":
        return runner.print_server_status()
    if args.action == "start":
        runner.start_server()
        return 0
    if args.action == "stop":
        return runner.stop_server()
    raise WorkflowError(f"Unknown server action {args.action!r}")


def command_stage(runner: HeadlessComfyRunner, args: argparse.Namespace) -> int:
    overrides = parse_override_values(args.overrides)
    probe_result = runner.build_stage_result(args.family, args.preset, args.stage, overrides)
    if args.stage == "draft_txt2img":
        render_count = int(probe_result.params["variant_count"])
        base_seed = int(probe_result.params.get("selected_seed", probe_result.params["seed"]))
        for index in range(render_count):
            variant_seed = base_seed + index
            variant_overrides = normalize_seed_overrides(overrides, variant_seed)
            variant_overrides["variant_count"] = 1
            runner.render_stage_once(
                args.family,
                args.preset,
                args.stage,
                variant_overrides,
                invocation="stage",
            )
        return 0

    if "selected_seed" in overrides and "seed" not in overrides:
        overrides = normalize_seed_overrides(overrides, int(overrides["selected_seed"]))
    overrides["variant_count"] = 1
    runner.render_stage_once(args.family, args.preset, args.stage, overrides, invocation="stage")
    return 0


def command_review_proof(runner: HeadlessComfyRunner, args: argparse.Namespace) -> int:
    overrides = parse_override_values(args.overrides)
    if is_opening_tableau_request(args.family, args.preset):
        payload = require_opening_tableau_payload(overrides)
        enriched_overrides = dict(overrides)
        enriched_overrides.update(derive_opening_tableau_prompt_overrides(payload))
        overrides = enriched_overrides
    draft_probe = runner.build_stage_result(args.family, args.preset, "draft_txt2img", overrides)
    pipeline_strategy = dict(draft_probe.manifest.get("pipeline_strategy", {}))
    quality_settings = resolve_quality_profile_settings(
        family=args.family,
        pipeline_strategy=pipeline_strategy,
        quality_profile=args.quality_profile,
    )
    semantic_profile = (
        str(pipeline_strategy.get("semantic_qc_profile", "")).strip()
        if args.quality_profile != "fast"
        else ""
    )
    if args.quality_profile != "fast" and not semantic_profile:
        raise WorkflowError(
            f"{args.family}/{args.preset} is missing pipeline_strategy.semantic_qc_profile for "
            f"quality profile {args.quality_profile!r}."
        )

    base_seed = (
        int(args.selected_seed)
        if args.selected_seed is not None
        else int(draft_probe.params.get("selected_seed", draft_probe.params["seed"]))
    )
    candidate_seeds = derive_candidate_seeds(
        base_seed=base_seed,
        seed_policy=str(pipeline_strategy.get("seed_policy", draft_probe.params.get("seed_mode", "fixed"))),
        candidate_count=int(quality_settings["draft_candidate_count"]),
    )
    pipeline_id = str(uuid.uuid4())
    pipeline_timestamp = utc_now_iso()
    softpass_policy = package_grid_softpass_policy(draft_probe.manifest)
    ranking_policy = package_grid_ranking_policy(draft_probe.manifest)
    stage_runs: dict[str, str] = {}
    stage_validations: dict[str, dict[str, Any]] = {}
    draft_candidates: list[dict[str, Any]] = []
    candidate_scores: dict[str, dict[str, Any]] = {}
    selected_candidate: dict[str, Any] = {}
    semantic_qc: dict[str, Any] = {
        "pre_refine": [],
        "post_final": {},
    }
    delivery_advisory_used = False
    delivery_notes: list[str] = []
    proof_outputs: list[str] = []
    failure_text: str | None = None
    pipeline_manifest_path = (
        runner.runs_root
        / args.family
        / args.preset
        / f"{pipeline_timestamp.replace(':', '').replace('-', '')}__review_proof.run.json"
    )

    def write_pipeline_manifest(status: str) -> None:
        pipeline_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest: dict[str, Any] = {
            "pipeline_id": pipeline_id,
            "created_at": pipeline_timestamp,
            "family": args.family,
            "preset": args.preset,
            "selected_seed": int(selected_candidate.get("seed", base_seed)),
            "server_url": runner.server_url,
            "status": status,
            "delivery_mode": args.delivery_mode,
            "quality_profile": args.quality_profile,
            "hero_model": str(quality_settings.get("hero_model", "")),
            "pipeline_strategy": pipeline_strategy,
            "draft_candidates": draft_candidates,
            "candidate_scores": candidate_scores,
            "selected_candidate": selected_candidate,
            "semantic_qc": semantic_qc,
            "stage_runs": stage_runs,
            "stage_validations": stage_validations,
            "source_text_repair_mode": "off",
            "repair_policy_path": None,
            "repair_run_manifest": None,
            "final_cleanup_run_manifest": None,
            "typography_mode": "off",
            "typography_runs": [],
            "base_final_outputs": proof_outputs,
            "final_outputs": proof_outputs,
        }
        manifest["delivery_advisory_used"] = bool(delivery_advisory_used)
        if delivery_notes:
            manifest["delivery_notes"] = list(delivery_notes)
        if failure_text is not None:
            manifest["failure"] = failure_text
        write_json(pipeline_manifest_path, manifest)

    try:
        ensure_quality_profile_runtime(
            runner=runner,
            family=args.family,
            preset=args.preset,
            quality_settings=quality_settings,
        )
        draft_candidates, candidate_scores, pre_refine_semantic = generate_draft_candidates(
            runner=runner,
            args=args,
            overrides=overrides,
            draft_probe=draft_probe,
            pipeline_id=pipeline_id,
            candidate_seeds=candidate_seeds,
            semantic_profile=semantic_profile,
            softpass_policy=softpass_policy,
            ranking_policy=ranking_policy,
            invocation="review-proof",
        )
        semantic_qc["pre_refine"].extend(pre_refine_semantic)

        passing_candidates = (
            [
                candidate
                for candidate in draft_candidates
                if not candidate["semantic_failures"] or bool(candidate.get("softpass_eligible"))
            ]
            if semantic_profile
            else draft_candidates
        )
        if not passing_candidates:
            if args.delivery_mode == "advisory" and draft_candidates:
                delivery_advisory_used = True
                delivery_notes.append(
                    "No draft candidate cleared semantic QC or adapter soft-pass; selected best available proof in advisory mode."
                )
                passing_candidates = list(draft_candidates)
            else:
                raise WorkflowError(
                    f"No draft candidate cleared semantic QC or adapter soft-pass for {args.family}/{args.preset}; "
                    f"review draft_candidates in {pipeline_manifest_path}."
                )
        selected_candidate = max(
            passing_candidates,
            key=lambda candidate: (
                1 if not candidate["semantic_failures"] else 0,
                float(candidate.get("selection_score", candidate["ranking_score"])),
                -int(candidate["seed"]),
            ),
        )
        selected_seed = int(selected_candidate["seed"])
        selected_draft_stage = str(selected_candidate.get("draft_stage", "draft_txt2img")).strip() or "draft_txt2img"
        stage_runs[selected_draft_stage] = str(selected_candidate["draft_run_manifest"])
        if selected_draft_stage != "draft_txt2img":
            stage_runs["draft_txt2img"] = str(selected_candidate["draft_run_manifest"])
        draft_output_path = Path(selected_candidate["draft_output"])
        draft_source = runner.relative_output_path(draft_output_path)
        skip_refine = is_opening_tableau_request(args.family, args.preset) and selected_draft_stage == OPENING_TABLEAU_STAGE
        if skip_refine:
            proof_image = draft_output_path
        else:
            refine_overrides = normalize_seed_overrides(overrides, selected_seed)
            refine_overrides["variant_count"] = 1
            refine_overrides["source_image"] = draft_source
            if quality_settings["use_hero_refine"]:
                hero_model = str(quality_settings["hero_model"]).strip()
                if hero_model:
                    refine_overrides["full_unet_name"] = f"{hero_model}.safetensors"
                hero_refine_denoise = quality_settings.get("hero_refine_denoise")
                if hero_refine_denoise is not None:
                    refine_overrides["refine_denoise"] = float(hero_refine_denoise)
            refine_run = runner.render_stage_once(
                args.family,
                args.preset,
                "refine_img2img",
                refine_overrides,
                invocation="review-proof",
                pipeline_id=pipeline_id,
            )
            stage_runs["refine_img2img"] = str(refine_run["run_manifest_path"])
            refine_outputs = refine_run["output_files"]
            if not refine_outputs:
                raise WorkflowError(f"Refine stage for {args.family}/{args.preset} did not produce any output files.")
            proof_image = refine_outputs[0]
        proof_outputs = [str(proof_image)]

        visual_qc_debug_dir = (
            runner.runs_root
            / args.family
            / args.preset
            / "debug"
            / f"post_refine_visual_qc__seed-{selected_seed}"
        )
        visual_qc_summary = runner.run_visual_qc_audit(
            proof_image,
            family=args.family,
            preset=args.preset,
            semantic_profile=semantic_profile,
            semantic_stage="final",
            contract_config=(
                contract_config_from_manifest(draft_probe.manifest)
                if skip_refine
                else contract_config_from_run(refine_run, fallback_manifest=draft_probe.manifest)
            ),
            debug_dir=visual_qc_debug_dir,
            allow_invalid_json=args.delivery_mode == "advisory",
        )
        visual_qc_run_path = runner.write_visual_qc_run_manifest(
            family=args.family,
            preset=args.preset,
            source_stage=selected_draft_stage if skip_refine else "refine_img2img",
            validation_stage="post_refine_visual_qc",
            artifact_path=proof_image,
            audit_summary=visual_qc_summary,
            invocation="review-proof",
            pipeline_id=pipeline_id,
            candidate_seed=selected_seed,
        )
        stage_validations["visual_qc"] = {
            "audit_manifest": str(visual_qc_run_path),
            "artifact_path": str(proof_image),
            "score": visual_qc_summary["score"],
            "threshold": visual_qc_summary["threshold"],
            "status": str(visual_qc_summary["status"]),
        }
        semantic_qc["post_final"] = {
            "artifact_path": str(proof_image),
            "manifest": str(visual_qc_run_path),
            "status": str(visual_qc_summary["status"]),
            "failures": list(visual_qc_summary.get("failures", [])),
            "ranking_score": float(visual_qc_summary.get("semantic", {}).get("ranking_score", 0.0)),
        }
        if visual_qc_summary["failures"]:
            if args.delivery_mode == "advisory":
                delivery_advisory_used = True
                delivery_notes.append(
                    "Review-proof visual QC reported failures; kept proof output in advisory mode."
                )
            else:
                failure = "; ".join(str(item) for item in visual_qc_summary["failures"])
                raise WorkflowError(f"Visual QC failed for artifact={proof_image}: {failure}")

        write_pipeline_manifest("advisory_success" if delivery_advisory_used else "success")
        print(f"INFO  pipeline manifest -> {pipeline_manifest_path}")
        return 0
    except WorkflowError as exc:
        failure_text = str(exc)
        write_pipeline_manifest("failed")
        print(f"INFO  pipeline manifest -> {pipeline_manifest_path}")
        raise


def command_finalize_still(runner: HeadlessComfyRunner, args: argparse.Namespace) -> int:
    source_image = Path(args.source_image).expanduser().resolve()
    if not source_image.is_absolute():
        raise WorkflowError(f"--source-image must be an absolute path, got {args.source_image!r}.")
    if not source_image.exists():
        raise WorkflowError(f"Source image was not found: {source_image}")

    overrides = parse_override_values(args.overrides)
    draft_probe = runner.build_stage_result(args.family, args.preset, "draft_txt2img", overrides)
    pipeline_strategy = dict(draft_probe.manifest.get("pipeline_strategy", {}))
    quality_settings = resolve_quality_profile_settings(
        family=args.family,
        pipeline_strategy=pipeline_strategy,
        quality_profile=args.quality_profile,
    )
    semantic_profile = (
        str(pipeline_strategy.get("semantic_qc_profile", "")).strip()
        if args.quality_profile != "fast"
        else ""
    )
    if args.quality_profile != "fast" and not semantic_profile:
        raise WorkflowError(
            f"{args.family}/{args.preset} is missing pipeline_strategy.semantic_qc_profile for "
            f"quality profile {args.quality_profile!r}."
        )

    selected_seed = (
        int(args.selected_seed)
        if args.selected_seed is not None
        else int(draft_probe.params.get("selected_seed", draft_probe.params["seed"]))
    )
    pipeline_id = str(uuid.uuid4())
    pipeline_timestamp = utc_now_iso()
    softpass_policy = package_grid_softpass_policy(draft_probe.manifest)
    ranking_policy = package_grid_ranking_policy(draft_probe.manifest)
    stage_runs: dict[str, str] = {}
    stage_validations: dict[str, dict[str, Any]] = {}
    base_final_outputs: list[str] = []
    typography_manifest_paths: list[str] = []
    typography_outputs: list[str] = []
    selected_candidate: dict[str, Any] = {
        "seed": int(selected_seed),
        "source_image": str(source_image),
    }
    semantic_qc: dict[str, Any] = {
        "pre_refine": [],
        "post_final": {},
    }
    delivery_advisory_used = False
    delivery_notes: list[str] = []
    repair_policy_path: str | None = None
    repair_run_manifest_path: str | None = None
    final_cleanup_run_manifest_path: str | None = None
    failure_text: str | None = None
    pipeline_manifest_path = (
        runner.runs_root
        / args.family
        / args.preset
        / f"{pipeline_timestamp.replace(':', '').replace('-', '')}__finalize_still.run.json"
    )

    def write_pipeline_manifest(status: str) -> None:
        pipeline_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest: dict[str, Any] = {
            "pipeline_id": pipeline_id,
            "created_at": pipeline_timestamp,
            "family": args.family,
            "preset": args.preset,
            "selected_seed": int(selected_seed),
            "server_url": runner.server_url,
            "status": status,
            "delivery_mode": args.delivery_mode,
            "quality_profile": args.quality_profile,
            "hero_model": str(quality_settings.get("hero_model", "")),
            "pipeline_strategy": pipeline_strategy,
            "draft_candidates": [],
            "candidate_scores": {},
            "selected_candidate": selected_candidate,
            "semantic_qc": semantic_qc,
            "stage_runs": stage_runs,
            "stage_validations": stage_validations,
            "source_text_repair_mode": args.source_text_repair,
            "repair_policy_path": repair_policy_path,
            "repair_run_manifest": repair_run_manifest_path,
            "final_cleanup_run_manifest": final_cleanup_run_manifest_path,
            "typography_mode": args.typography,
            "typography_runs": typography_manifest_paths,
            "base_final_outputs": base_final_outputs,
            "final_outputs": typography_outputs,
        }
        manifest["delivery_advisory_used"] = bool(delivery_advisory_used)
        if delivery_notes:
            manifest["delivery_notes"] = list(delivery_notes)
        if failure_text is not None:
            manifest["failure"] = failure_text
        write_json(pipeline_manifest_path, manifest)

    should_run_repair, repair_sidecar = runner.repair_policy_should_run(
        args.family,
        args.preset,
        args.source_text_repair,
    )
    should_run_pre_final_repair = False
    should_run_post_final_cleanup = False
    policy_path: Path | None = None
    policy: dict[str, Any] | None = None
    if should_run_repair:
        if repair_sidecar is None:
            raise WorkflowError(f"No source-text repair policy configured for {args.family}/{args.preset}.")
        policy_path, policy = repair_sidecar
        repair_policy_path = str(policy_path)
        should_run_pre_final_repair = bool(policy["enabled"])
        should_run_post_final_cleanup = bool(policy.get("post_final_cleanup", {}).get("enabled"))
        if should_run_pre_final_repair:
            runner.ensure_repair_runtime(policy_path, policy)

    try:
        ensure_quality_profile_runtime(
            runner=runner,
            family=args.family,
            preset=args.preset,
            quality_settings=quality_settings,
        )
        repair_manifest_path_obj: Path | None = None
        final_source = str(source_image)
        if should_run_pre_final_repair:
            if policy_path is None:
                raise WorkflowError(f"No source-text repair policy configured for {args.family}/{args.preset}.")
            repair_debug_dir = (
                runner.runs_root
                / args.family
                / args.preset
                / "debug"
                / f"repair_source_text__seed-{selected_seed}"
            )
            repair_summary = runner.run_source_text_repair(
                source_image,
                policy_path=policy_path,
                debug_dir=repair_debug_dir,
            )
            repair_run_path = runner.write_repair_run_manifest(
                family=args.family,
                preset=args.preset,
                artifact_path=source_image,
                repair_summary=repair_summary,
                invocation="finalize-still",
                pipeline_id=pipeline_id,
                selected_seed=selected_seed,
            )
            stage_runs["repair_source_text"] = str(repair_run_path)
            repair_run_manifest_path = str(repair_run_path)
            repair_manifest_path_obj = repair_run_path
            final_source = str(Path(repair_summary["output_artifact"]).resolve())

        final_overrides = normalize_seed_overrides(overrides, selected_seed)
        final_overrides["variant_count"] = 1
        final_overrides["source_image"] = final_source
        final_run = runner.render_stage_once(
            args.family,
            args.preset,
            "final_upscale",
            final_overrides,
            invocation="finalize-still",
            pipeline_id=pipeline_id,
        )
        stage_runs["final_upscale"] = str(final_run["run_manifest_path"])
        if not final_run["output_files"]:
            raise WorkflowError(f"Final stage for {args.family}/{args.preset} did not produce any output files.")
        base_final_outputs = [str(path) for path in final_run["output_files"]]
        typography_outputs = list(base_final_outputs)
        source_text_output: Path | None = None
        visual_qc_source_stage = "final_upscale"
        should_run_typography, typography_sidecar = runner.typography_should_run(
            args.family,
            args.preset,
            args.typography,
        )
        if should_run_post_final_cleanup:
            if policy_path is None:
                raise WorkflowError(f"No source-text repair policy configured for {args.family}/{args.preset}.")
            if not final_run["output_files"]:
                raise WorkflowError(
                    f"Final stage for {args.family}/{args.preset} did not produce any output files for cleanup."
                )
            intent_path = typography_sidecar[0] if typography_sidecar is not None else None
            cleanup_debug_dir = (
                runner.runs_root
                / args.family
                / args.preset
                / "debug"
                / f"cleanup_final_text__seed-{selected_seed}"
            )
            cleanup_summary = runner.run_cleanup_final_text(
                final_run["output_files"][0],
                intent_path=intent_path,
                policy_path=policy_path,
                repair_manifest_path=repair_manifest_path_obj,
                debug_dir=cleanup_debug_dir,
            )
            cleanup_run_path = runner.write_cleanup_run_manifest(
                family=args.family,
                preset=args.preset,
                artifact_path=final_run["output_files"][0],
                cleanup_summary=cleanup_summary,
                invocation="finalize-still",
                pipeline_id=pipeline_id,
                selected_seed=selected_seed,
            )
            stage_runs["cleanup_final_text"] = str(cleanup_run_path)
            final_cleanup_run_manifest_path = str(cleanup_run_path)
            source_text_output = Path(cleanup_summary["output_artifact"])
            visual_qc_source_stage = "cleanup_final_text"
            typography_outputs = [str(source_text_output)]
            cleanup_audit_summary = cleanup_summary["residual_validation"]
            cleanup_audit_run_path = runner.write_cleanup_text_audit_run_manifest(
                family=args.family,
                preset=args.preset,
                artifact_path=source_text_output,
                cleanup_manifest_path=Path(cleanup_summary["cleanup_manifest_path"]),
                audit_summary=cleanup_audit_summary,
                invocation="finalize-still",
                pipeline_id=pipeline_id,
                selected_seed=selected_seed,
            )
            stage_validations["cleanup_final_text"] = {
                "post_cleanup_text_audit": str(cleanup_audit_run_path),
                "status": str(cleanup_audit_summary["status"]),
            }
            if cleanup_audit_summary["failures"]:
                failure = "; ".join(str(item) for item in cleanup_audit_summary["failures"])
                raise WorkflowError(
                    f"Final cleanup audit failed for artifact={source_text_output}: {failure}"
                )
        elif final_run["output_files"]:
            source_text_output = final_run["output_files"][0]

        if source_text_output is not None:
            visual_qc_debug_dir = (
                runner.runs_root
                / args.family
                / args.preset
                / "debug"
                / f"visual_qc__seed-{selected_seed}"
            )
            visual_qc_summary = runner.run_visual_qc_audit(
                source_text_output,
                family=args.family,
                preset=args.preset,
                semantic_profile=semantic_profile,
                semantic_stage="final",
                contract_config=contract_config_from_run(final_run),
                debug_dir=visual_qc_debug_dir,
                allow_invalid_json=args.delivery_mode == "advisory",
            )
            visual_qc_run_path = runner.write_visual_qc_run_manifest(
                family=args.family,
                preset=args.preset,
                source_stage=visual_qc_source_stage,
                validation_stage="post_final_visual_qc",
                artifact_path=source_text_output,
                audit_summary=visual_qc_summary,
                invocation="finalize-still",
                pipeline_id=pipeline_id,
                candidate_seed=selected_seed,
            )
            stage_validations["visual_qc"] = {
                "audit_manifest": str(visual_qc_run_path),
                "artifact_path": str(source_text_output),
                "score": visual_qc_summary["score"],
                "threshold": visual_qc_summary["threshold"],
                "status": str(visual_qc_summary["status"]),
            }
        semantic_qc["post_final"] = {
            "artifact_path": str(source_text_output),
            "manifest": str(visual_qc_run_path),
            "status": str(visual_qc_summary["status"]),
            "failures": list(visual_qc_summary.get("failures", [])),
            "ranking_score": float(visual_qc_summary.get("semantic", {}).get("ranking_score", 0.0)),
        }
        if visual_qc_summary["failures"]:
            if args.delivery_mode == "advisory":
                delivery_advisory_used = True
                delivery_notes.append(
                    "Final visual QC reported failures; kept finalize-still output in advisory mode."
                )
            else:
                failure = "; ".join(str(item) for item in visual_qc_summary["failures"])
                raise WorkflowError(f"Visual QC failed for artifact={source_text_output}: {failure}")

        if source_text_output is not None:
            if typography_sidecar is not None:
                intent_path, _ = typography_sidecar
                if repair_manifest_path_obj is not None:
                    audit_debug_dir = (
                        runner.runs_root
                        / args.family
                        / args.preset
                        / "debug"
                        / f"final_upscale__post_repair_text_audit__seed-{selected_seed}"
                    )
                    audit_summary = runner.run_repaired_text_audit(
                        source_text_output,
                        repair_manifest_path=repair_manifest_path_obj,
                        intent_path=intent_path,
                        debug_dir=audit_debug_dir,
                    )
                    audit_run_path = runner.write_repaired_text_audit_run_manifest(
                        family=args.family,
                        preset=args.preset,
                        stage="final_upscale",
                        artifact_path=source_text_output,
                        repair_manifest_path=repair_manifest_path_obj,
                        intent_path=intent_path,
                        audit_summary=audit_summary,
                        invocation="finalize-still",
                        pipeline_id=pipeline_id,
                        selected_seed=selected_seed,
                    )
                    stage_validations["final_upscale"] = {
                        "post_repair_text_audit": str(audit_run_path),
                        "status": str(audit_summary["status"]),
                    }
                else:
                    audit_debug_dir = (
                        runner.runs_root
                        / args.family
                        / args.preset
                        / "debug"
                        / f"final_upscale__pre_typography_source_text_audit__seed-{selected_seed}"
                    )
                    audit_summary = runner.run_source_text_audit(
                        source_text_output,
                        intent_path=intent_path,
                        debug_dir=audit_debug_dir,
                    )
                    audit_run_path = runner.write_source_text_audit_run_manifest(
                        family=args.family,
                        preset=args.preset,
                        stage="final_upscale",
                        artifact_path=source_text_output,
                        intent_path=intent_path,
                        audit_summary=audit_summary,
                        invocation="finalize-still",
                        pipeline_id=pipeline_id,
                        selected_seed=selected_seed,
                    )
                    stage_validations["final_upscale"] = {
                        "pre_typography_source_text_audit": str(audit_run_path),
                        "status": str(audit_summary["status"]),
                    }
            else:
                audit_debug_dir = (
                    runner.runs_root
                    / args.family
                    / args.preset
                    / "debug"
                    / f"final_upscale__zero_letter_audit__seed-{selected_seed}"
                )
                audit_summary = runner.run_zero_letter_audit(
                    source_text_output,
                    debug_dir=audit_debug_dir,
                )
                audit_run_path = runner.write_zero_letter_audit_run_manifest(
                    family=args.family,
                    preset=args.preset,
                    stage="final_upscale",
                    artifact_path=source_text_output,
                    audit_summary=audit_summary,
                    invocation="finalize-still",
                    pipeline_id=pipeline_id,
                    selected_seed=selected_seed,
                )
                stage_validations["final_upscale"] = {
                    "zero_letter_audit": str(audit_run_path),
                    "status": str(audit_summary["status"]),
                }
            if audit_summary["failures"]:
                failure = "; ".join(str(item) for item in audit_summary["failures"])
                raise WorkflowError(
                    f"Final-stage text audit failed for stage=final_upscale artifact={source_text_output}: {failure}"
                )
        if should_run_typography:
            typography_output_paths: list[str] = []
            input_paths = [Path(path) for path in typography_outputs]
            intent_path = typography_sidecar[0] if typography_sidecar is not None else None
            if intent_path is None:
                raise WorkflowError(f"No typography sidecar configured for {args.family}/{args.preset}.")
            for output_path in input_paths:
                typography_summary = runner.run_render_typography_apply(
                    args.family,
                    args.preset,
                    output_path,
                    repair_manifest_path=repair_manifest_path_obj,
                    allow_validation_failure=should_run_post_final_cleanup,
                )
                if should_run_post_final_cleanup and typography_summary["validation"]["failures"]:
                    cleanup_debug_dir = (
                        runner.runs_root
                        / args.family
                        / args.preset
                        / "debug"
                        / f"typography_overlay__post_cleanup__seed-{selected_seed}"
                    )
                    cleanup_summary = runner.run_cleanup_final_text(
                        Path(typography_summary["output_artifact"]),
                        intent_path=intent_path,
                        policy_path=policy_path,
                        repair_manifest_path=repair_manifest_path_obj,
                        debug_dir=cleanup_debug_dir,
                    )
                    cleanup_run_path = runner.write_cleanup_run_manifest(
                        family=args.family,
                        preset=args.preset,
                        artifact_path=Path(typography_summary["output_artifact"]),
                        cleanup_summary=cleanup_summary,
                        invocation="finalize-still",
                        pipeline_id=pipeline_id,
                        selected_seed=selected_seed,
                    )
                    validation_debug_dir = cleanup_debug_dir / "post_cleanup_validate"
                    validated_summary = runner.run_typography_validate(
                        target="still",
                        artifact_path=Path(cleanup_summary["output_artifact"]),
                        intent_path=intent_path,
                        repair_manifest_path=repair_manifest_path_obj,
                        debug_dir=validation_debug_dir,
                    )
                    typography_summary["output_artifact"] = cleanup_summary["output_artifact"]
                    typography_summary["validation"] = validated_summary["validation"]
                    typography_summary["debug_artifacts"] = list(
                        dict.fromkeys(
                            list(typography_summary.get("debug_artifacts", []))
                            + list(cleanup_summary.get("debug_artifacts", []))
                            + list(validated_summary.get("debug_artifacts", []))
                        )
                    )
                    typography_summary["post_typography_cleanup_run_manifest"] = str(cleanup_run_path)
                    typography_summary["post_typography_cleanup_output_image"] = cleanup_summary["output_artifact"]
                    typography_summary["post_typography_cleanup_validation"] = validated_summary["validation"]
                    if validated_summary["validation"]["failures"]:
                        failure = "; ".join(str(item) for item in validated_summary["validation"]["failures"])
                        raise WorkflowError(
                            f"Controlled typography post-cleanup validation failed for "
                            f"artifact={cleanup_summary['output_artifact']}: {failure}"
                        )
                elif typography_summary["validation"]["failures"]:
                    failure = "; ".join(str(item) for item in typography_summary["validation"]["failures"])
                    raise WorkflowError(
                        f"Controlled typography failed for target=still artifact={output_path}: {failure}"
                    )
                typography_output_paths.append(str(typography_summary["output_artifact"]))
                typography_run_path = runner.write_typography_run_manifest(
                    family=args.family,
                    preset=args.preset,
                    input_image=output_path,
                    typography_summary=typography_summary,
                    invocation="finalize-still",
                    pipeline_id=pipeline_id,
                )
                typography_manifest_paths.append(str(typography_run_path))
            typography_outputs = typography_output_paths

        write_pipeline_manifest("advisory_success" if delivery_advisory_used else "success")
        print(f"INFO  pipeline manifest -> {pipeline_manifest_path}")
        return 0
    except WorkflowError as exc:
        failure_text = str(exc)
        write_pipeline_manifest("failed")
        print(f"INFO  pipeline manifest -> {pipeline_manifest_path}")
        raise


def command_pipeline(runner: HeadlessComfyRunner, args: argparse.Namespace) -> int:
    overrides = parse_override_values(args.overrides)
    if is_opening_tableau_request(args.family, args.preset):
        payload = require_opening_tableau_payload(overrides)
        enriched_overrides = dict(overrides)
        enriched_overrides.update(derive_opening_tableau_prompt_overrides(payload))
        overrides = enriched_overrides
    draft_probe = runner.build_stage_result(args.family, args.preset, "draft_txt2img", overrides)
    pipeline_strategy = dict(draft_probe.manifest.get("pipeline_strategy", {}))
    quality_settings = resolve_quality_profile_settings(
        family=args.family,
        pipeline_strategy=pipeline_strategy,
        quality_profile=args.quality_profile,
    )
    semantic_profile = (
        str(pipeline_strategy.get("semantic_qc_profile", "")).strip()
        if args.quality_profile != "fast"
        else ""
    )
    if args.quality_profile != "fast" and not semantic_profile:
        raise WorkflowError(
            f"{args.family}/{args.preset} is missing pipeline_strategy.semantic_qc_profile for "
            f"quality profile {args.quality_profile!r}."
        )

    base_seed = (
        int(args.selected_seed)
        if args.selected_seed is not None
        else int(draft_probe.params.get("selected_seed", draft_probe.params["seed"]))
    )
    candidate_seeds = derive_candidate_seeds(
        base_seed=base_seed,
        seed_policy=str(pipeline_strategy.get("seed_policy", draft_probe.params.get("seed_mode", "fixed"))),
        candidate_count=int(quality_settings["draft_candidate_count"]),
    )
    pipeline_id = str(uuid.uuid4())
    pipeline_timestamp = utc_now_iso()
    softpass_policy = package_grid_softpass_policy(draft_probe.manifest)
    ranking_policy = package_grid_ranking_policy(draft_probe.manifest)
    stage_runs: dict[str, str] = {}
    stage_validations: dict[str, dict[str, Any]] = {}
    base_final_outputs: list[str] = []
    typography_manifest_paths: list[str] = []
    typography_outputs: list[str] = []
    draft_candidates: list[dict[str, Any]] = []
    candidate_scores: dict[str, dict[str, Any]] = {}
    selected_candidate: dict[str, Any] = {}
    semantic_qc: dict[str, Any] = {
        "pre_refine": [],
        "post_final": {},
    }
    delivery_advisory_used = False
    delivery_notes: list[str] = []
    repair_policy_path: str | None = None
    repair_run_manifest_path: str | None = None
    final_cleanup_run_manifest_path: str | None = None
    failure_text: str | None = None
    pipeline_manifest_path = (
        runner.runs_root
        / args.family
        / args.preset
        / f"{pipeline_timestamp.replace(':', '').replace('-', '')}__pipeline.run.json"
    )

    def write_pipeline_manifest(status: str) -> None:
        pipeline_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest: dict[str, Any] = {
            "pipeline_id": pipeline_id,
            "created_at": pipeline_timestamp,
            "family": args.family,
            "preset": args.preset,
            "selected_seed": int(selected_candidate.get("seed", base_seed)),
            "server_url": runner.server_url,
            "status": status,
            "delivery_mode": args.delivery_mode,
            "quality_profile": args.quality_profile,
            "hero_model": str(quality_settings.get("hero_model", "")),
            "pipeline_strategy": pipeline_strategy,
            "draft_candidates": draft_candidates,
            "candidate_scores": candidate_scores,
            "selected_candidate": selected_candidate,
            "semantic_qc": semantic_qc,
            "stage_runs": stage_runs,
            "stage_validations": stage_validations,
            "source_text_repair_mode": args.source_text_repair,
            "repair_policy_path": repair_policy_path,
            "repair_run_manifest": repair_run_manifest_path,
            "final_cleanup_run_manifest": final_cleanup_run_manifest_path,
            "typography_mode": args.typography,
            "typography_runs": typography_manifest_paths,
            "base_final_outputs": base_final_outputs,
            "final_outputs": typography_outputs,
        }
        manifest["delivery_advisory_used"] = bool(delivery_advisory_used)
        if delivery_notes:
            manifest["delivery_notes"] = list(delivery_notes)
        if failure_text is not None:
            manifest["failure"] = failure_text
        write_json(pipeline_manifest_path, manifest)

    should_run_repair, repair_sidecar = runner.repair_policy_should_run(
        args.family,
        args.preset,
        args.source_text_repair,
    )
    should_run_pre_final_repair = False
    should_run_post_final_cleanup = False
    policy_path: Path | None = None
    policy: dict[str, Any] | None = None
    if should_run_repair:
        if repair_sidecar is None:
            raise WorkflowError(f"No source-text repair policy configured for {args.family}/{args.preset}.")
        policy_path, policy = repair_sidecar
        repair_policy_path = str(policy_path)
        should_run_pre_final_repair = bool(policy["enabled"])
        should_run_post_final_cleanup = bool(policy.get("post_final_cleanup", {}).get("enabled"))
        if should_run_pre_final_repair:
            runner.ensure_repair_runtime(policy_path, policy)

    try:
        ensure_quality_profile_runtime(
            runner=runner,
            family=args.family,
            preset=args.preset,
            quality_settings=quality_settings,
        )
        draft_candidates, candidate_scores, pre_refine_semantic = generate_draft_candidates(
            runner=runner,
            args=args,
            overrides=overrides,
            draft_probe=draft_probe,
            pipeline_id=pipeline_id,
            candidate_seeds=candidate_seeds,
            semantic_profile=semantic_profile,
            softpass_policy=softpass_policy,
            ranking_policy=ranking_policy,
            invocation="pipeline",
        )
        semantic_qc["pre_refine"].extend(pre_refine_semantic)

        passing_candidates = (
            [
                candidate
                for candidate in draft_candidates
                if not candidate["semantic_failures"] or bool(candidate.get("softpass_eligible"))
            ]
            if semantic_profile
            else draft_candidates
        )
        if not passing_candidates:
            if args.delivery_mode == "advisory" and draft_candidates:
                delivery_advisory_used = True
                delivery_notes.append(
                    "No draft candidate cleared semantic QC or adapter soft-pass; selected best available draft in advisory mode."
                )
                passing_candidates = list(draft_candidates)
            else:
                raise WorkflowError(
                    f"No draft candidate cleared semantic QC or adapter soft-pass for {args.family}/{args.preset}; "
                    f"review draft_candidates in {pipeline_manifest_path}."
                )
        selected_candidate = max(
            passing_candidates,
            key=lambda candidate: (
                1 if not candidate["semantic_failures"] else 0,
                float(candidate.get("selection_score", candidate["ranking_score"])),
                -int(candidate["seed"]),
            ),
        )
        selected_seed = int(selected_candidate["seed"])
        selected_draft_stage = str(selected_candidate.get("draft_stage", "draft_txt2img")).strip() or "draft_txt2img"
        stage_runs[selected_draft_stage] = str(selected_candidate["draft_run_manifest"])
        if selected_draft_stage != "draft_txt2img":
            stage_runs["draft_txt2img"] = str(selected_candidate["draft_run_manifest"])
        draft_output_path = Path(selected_candidate["draft_output"])
        draft_source = runner.relative_output_path(draft_output_path)
        skip_refine = is_opening_tableau_request(args.family, args.preset) and selected_draft_stage == OPENING_TABLEAU_STAGE
        if skip_refine:
            refine_outputs = [draft_output_path]
            refine_source = draft_source
        else:
            refine_overrides = normalize_seed_overrides(overrides, selected_seed)
            refine_overrides["variant_count"] = 1
            refine_overrides["source_image"] = draft_source
            if quality_settings["use_hero_refine"]:
                hero_model = str(quality_settings["hero_model"]).strip()
                if hero_model:
                    refine_overrides["full_unet_name"] = f"{hero_model}.safetensors"
                hero_refine_denoise = quality_settings.get("hero_refine_denoise")
                if hero_refine_denoise is not None:
                    refine_overrides["refine_denoise"] = float(hero_refine_denoise)
            refine_run = runner.render_stage_once(
                args.family,
                args.preset,
                "refine_img2img",
                refine_overrides,
                invocation="pipeline",
                pipeline_id=pipeline_id,
            )
            stage_runs["refine_img2img"] = str(refine_run["run_manifest_path"])
            refine_outputs = refine_run["output_files"]
            if not refine_outputs:
                raise WorkflowError(f"Refine stage for {args.family}/{args.preset} did not produce any output files.")
            refine_source = runner.relative_output_path(refine_outputs[0])
        repair_manifest_path_obj: Path | None = None

        final_source = refine_source
        if should_run_pre_final_repair:
            if policy_path is None:
                raise WorkflowError(f"No source-text repair policy configured for {args.family}/{args.preset}.")
            repair_debug_dir = (
                runner.runs_root
                / args.family
                / args.preset
                / "debug"
                / f"repair_source_text__seed-{selected_seed}"
            )
            repair_summary = runner.run_source_text_repair(
                refine_outputs[0],
                policy_path=policy_path,
                debug_dir=repair_debug_dir,
            )
            repair_run_path = runner.write_repair_run_manifest(
                family=args.family,
                preset=args.preset,
                artifact_path=refine_outputs[0],
                repair_summary=repair_summary,
                invocation="pipeline",
                pipeline_id=pipeline_id,
                selected_seed=selected_seed,
            )
            stage_runs["repair_source_text"] = str(repair_run_path)
            repair_run_manifest_path = str(repair_run_path)
            repair_manifest_path_obj = repair_run_path
            final_source = runner.relative_output_path(Path(repair_summary["output_artifact"]))

        final_overrides = normalize_seed_overrides(overrides, selected_seed)
        final_overrides["variant_count"] = 1
        final_overrides["source_image"] = final_source
        final_run = runner.render_stage_once(
            args.family,
            args.preset,
            "final_upscale",
            final_overrides,
            invocation="pipeline",
            pipeline_id=pipeline_id,
        )
        stage_runs["final_upscale"] = str(final_run["run_manifest_path"])
        if not final_run["output_files"]:
            raise WorkflowError(f"Final stage for {args.family}/{args.preset} did not produce any output files.")
        base_final_outputs = [str(path) for path in final_run["output_files"]]
        typography_outputs = list(base_final_outputs)
        source_text_output: Path | None = None
        visual_qc_source_stage = "final_upscale"
        should_run_typography, typography_sidecar = runner.typography_should_run(
            args.family,
            args.preset,
            args.typography,
        )
        if should_run_post_final_cleanup:
            if policy_path is None:
                raise WorkflowError(f"No source-text repair policy configured for {args.family}/{args.preset}.")
            if not final_run["output_files"]:
                raise WorkflowError(
                    f"Final stage for {args.family}/{args.preset} did not produce any output files for cleanup."
                )
            intent_path = typography_sidecar[0] if typography_sidecar is not None else None
            cleanup_debug_dir = (
                runner.runs_root
                / args.family
                / args.preset
                / "debug"
                / f"cleanup_final_text__seed-{selected_seed}"
            )
            cleanup_summary = runner.run_cleanup_final_text(
                final_run["output_files"][0],
                intent_path=intent_path,
                policy_path=policy_path,
                repair_manifest_path=repair_manifest_path_obj,
                debug_dir=cleanup_debug_dir,
            )
            cleanup_run_path = runner.write_cleanup_run_manifest(
                family=args.family,
                preset=args.preset,
                artifact_path=final_run["output_files"][0],
                cleanup_summary=cleanup_summary,
                invocation="pipeline",
                pipeline_id=pipeline_id,
                selected_seed=selected_seed,
            )
            stage_runs["cleanup_final_text"] = str(cleanup_run_path)
            final_cleanup_run_manifest_path = str(cleanup_run_path)
            source_text_output = Path(cleanup_summary["output_artifact"])
            visual_qc_source_stage = "cleanup_final_text"
            typography_outputs = [str(source_text_output)]
            cleanup_audit_summary = cleanup_summary["residual_validation"]
            cleanup_audit_run_path = runner.write_cleanup_text_audit_run_manifest(
                family=args.family,
                preset=args.preset,
                artifact_path=source_text_output,
                cleanup_manifest_path=Path(cleanup_summary["cleanup_manifest_path"]),
                audit_summary=cleanup_audit_summary,
                invocation="pipeline",
                pipeline_id=pipeline_id,
                selected_seed=selected_seed,
            )
            stage_validations["cleanup_final_text"] = {
                "post_cleanup_text_audit": str(cleanup_audit_run_path),
                "status": str(cleanup_audit_summary["status"]),
            }
            if cleanup_audit_summary["failures"]:
                failure = "; ".join(str(item) for item in cleanup_audit_summary["failures"])
                raise WorkflowError(
                    f"Final cleanup audit failed for artifact={source_text_output}: {failure}"
                )
        elif final_run["output_files"]:
            source_text_output = final_run["output_files"][0]

        if source_text_output is not None:
            visual_qc_debug_dir = (
                runner.runs_root
                / args.family
                / args.preset
                / "debug"
                / f"visual_qc__seed-{selected_seed}"
            )
            visual_qc_summary = runner.run_visual_qc_audit(
                source_text_output,
                family=args.family,
                preset=args.preset,
                semantic_profile=semantic_profile,
                semantic_stage="final",
                contract_config=contract_config_from_run(final_run),
                debug_dir=visual_qc_debug_dir,
                allow_invalid_json=args.delivery_mode == "advisory",
            )
            visual_qc_run_path = runner.write_visual_qc_run_manifest(
                family=args.family,
                preset=args.preset,
                source_stage=visual_qc_source_stage,
                validation_stage="post_final_visual_qc",
                artifact_path=source_text_output,
                audit_summary=visual_qc_summary,
                invocation="pipeline",
                pipeline_id=pipeline_id,
                candidate_seed=selected_seed,
            )
            stage_validations["visual_qc"] = {
                "audit_manifest": str(visual_qc_run_path),
                "artifact_path": str(source_text_output),
                "score": visual_qc_summary["score"],
                "threshold": visual_qc_summary["threshold"],
                "status": str(visual_qc_summary["status"]),
            }
        semantic_qc["post_final"] = {
            "artifact_path": str(source_text_output),
            "manifest": str(visual_qc_run_path),
            "status": str(visual_qc_summary["status"]),
            "failures": list(visual_qc_summary.get("failures", [])),
            "ranking_score": float(visual_qc_summary.get("semantic", {}).get("ranking_score", 0.0)),
        }
        if visual_qc_summary["failures"]:
            if args.delivery_mode == "advisory":
                delivery_advisory_used = True
                delivery_notes.append(
                    "Final visual QC reported failures; kept best available output in advisory mode."
                )
            else:
                failure = "; ".join(str(item) for item in visual_qc_summary["failures"])
                raise WorkflowError(f"Visual QC failed for artifact={source_text_output}: {failure}")

        if source_text_output is not None:
            if typography_sidecar is not None:
                intent_path, _ = typography_sidecar
                if repair_manifest_path_obj is not None:
                    audit_debug_dir = (
                        runner.runs_root
                        / args.family
                        / args.preset
                        / "debug"
                        / f"final_upscale__post_repair_text_audit__seed-{selected_seed}"
                    )
                    audit_summary = runner.run_repaired_text_audit(
                        source_text_output,
                        repair_manifest_path=repair_manifest_path_obj,
                        intent_path=intent_path,
                        debug_dir=audit_debug_dir,
                    )
                    audit_run_path = runner.write_repaired_text_audit_run_manifest(
                        family=args.family,
                        preset=args.preset,
                        stage="final_upscale",
                        artifact_path=source_text_output,
                        repair_manifest_path=repair_manifest_path_obj,
                        intent_path=intent_path,
                        audit_summary=audit_summary,
                        invocation="pipeline",
                        pipeline_id=pipeline_id,
                        selected_seed=selected_seed,
                    )
                    stage_validations["final_upscale"] = {
                        "post_repair_text_audit": str(audit_run_path),
                        "status": str(audit_summary["status"]),
                    }
                else:
                    audit_debug_dir = (
                        runner.runs_root
                        / args.family
                        / args.preset
                        / "debug"
                        / f"final_upscale__pre_typography_source_text_audit__seed-{selected_seed}"
                    )
                    audit_summary = runner.run_source_text_audit(
                        source_text_output,
                        intent_path=intent_path,
                        debug_dir=audit_debug_dir,
                    )
                    audit_run_path = runner.write_source_text_audit_run_manifest(
                        family=args.family,
                        preset=args.preset,
                        stage="final_upscale",
                        artifact_path=source_text_output,
                        intent_path=intent_path,
                        audit_summary=audit_summary,
                        invocation="pipeline",
                        pipeline_id=pipeline_id,
                        selected_seed=selected_seed,
                    )
                    stage_validations["final_upscale"] = {
                        "pre_typography_source_text_audit": str(audit_run_path),
                        "status": str(audit_summary["status"]),
                    }
            else:
                audit_debug_dir = (
                    runner.runs_root
                    / args.family
                    / args.preset
                    / "debug"
                    / f"final_upscale__zero_letter_audit__seed-{selected_seed}"
                )
                audit_summary = runner.run_zero_letter_audit(
                    source_text_output,
                    debug_dir=audit_debug_dir,
                )
                audit_run_path = runner.write_zero_letter_audit_run_manifest(
                    family=args.family,
                    preset=args.preset,
                    stage="final_upscale",
                    artifact_path=source_text_output,
                    audit_summary=audit_summary,
                    invocation="pipeline",
                    pipeline_id=pipeline_id,
                    selected_seed=selected_seed,
                )
                stage_validations["final_upscale"] = {
                    "zero_letter_audit": str(audit_run_path),
                    "status": str(audit_summary["status"]),
                }
            if audit_summary["failures"]:
                failure = "; ".join(str(item) for item in audit_summary["failures"])
                raise WorkflowError(
                    f"Final-stage text audit failed for stage=final_upscale artifact={source_text_output}: {failure}"
                )
        if should_run_typography:
            typography_output_paths: list[str] = []
            input_paths = [Path(path) for path in typography_outputs]
            intent_path = typography_sidecar[0] if typography_sidecar is not None else None
            if intent_path is None:
                raise WorkflowError(f"No typography sidecar configured for {args.family}/{args.preset}.")
            for output_path in input_paths:
                typography_summary = runner.run_render_typography_apply(
                    args.family,
                    args.preset,
                    output_path,
                    repair_manifest_path=repair_manifest_path_obj,
                    allow_validation_failure=should_run_post_final_cleanup,
                )
                if should_run_post_final_cleanup and typography_summary["validation"]["failures"]:
                    cleanup_debug_dir = (
                        runner.runs_root
                        / args.family
                        / args.preset
                        / "debug"
                        / f"typography_overlay__post_cleanup__seed-{selected_seed}"
                    )
                    cleanup_summary = runner.run_cleanup_final_text(
                        Path(typography_summary["output_artifact"]),
                        intent_path=intent_path,
                        policy_path=policy_path,
                        repair_manifest_path=repair_manifest_path_obj,
                        debug_dir=cleanup_debug_dir,
                    )
                    cleanup_run_path = runner.write_cleanup_run_manifest(
                        family=args.family,
                        preset=args.preset,
                        artifact_path=Path(typography_summary["output_artifact"]),
                        cleanup_summary=cleanup_summary,
                        invocation="pipeline",
                        pipeline_id=pipeline_id,
                        selected_seed=selected_seed,
                    )
                    validation_debug_dir = cleanup_debug_dir / "post_cleanup_validate"
                    validated_summary = runner.run_typography_validate(
                        target="still",
                        artifact_path=Path(cleanup_summary["output_artifact"]),
                        intent_path=intent_path,
                        repair_manifest_path=repair_manifest_path_obj,
                        debug_dir=validation_debug_dir,
                    )
                    typography_summary["output_artifact"] = cleanup_summary["output_artifact"]
                    typography_summary["validation"] = validated_summary["validation"]
                    typography_summary["debug_artifacts"] = list(
                        dict.fromkeys(
                            list(typography_summary.get("debug_artifacts", []))
                            + list(cleanup_summary.get("debug_artifacts", []))
                            + list(validated_summary.get("debug_artifacts", []))
                        )
                    )
                    typography_summary["post_typography_cleanup_run_manifest"] = str(cleanup_run_path)
                    typography_summary["post_typography_cleanup_output_image"] = cleanup_summary["output_artifact"]
                    typography_summary["post_typography_cleanup_validation"] = validated_summary["validation"]
                    if validated_summary["validation"]["failures"]:
                        failure = "; ".join(str(item) for item in validated_summary["validation"]["failures"])
                        raise WorkflowError(
                            f"Controlled typography post-cleanup validation failed for "
                            f"artifact={cleanup_summary['output_artifact']}: {failure}"
                        )
                elif typography_summary["validation"]["failures"]:
                    failure = "; ".join(str(item) for item in typography_summary["validation"]["failures"])
                    raise WorkflowError(
                        f"Controlled typography failed for target=still artifact={output_path}: {failure}"
                    )
                typography_output_paths.append(str(typography_summary["output_artifact"]))
                typography_run_path = runner.write_typography_run_manifest(
                    family=args.family,
                    preset=args.preset,
                    input_image=output_path,
                    typography_summary=typography_summary,
                    invocation="pipeline",
                    pipeline_id=pipeline_id,
                )
                typography_manifest_paths.append(str(typography_run_path))
            typography_outputs = typography_output_paths

        write_pipeline_manifest("advisory_success" if delivery_advisory_used else "success")
        print(f"INFO  pipeline manifest -> {pipeline_manifest_path}")
        return 0
    except WorkflowError as exc:
        failure_text = str(exc)
        write_pipeline_manifest("failed")
        print(f"INFO  pipeline manifest -> {pipeline_manifest_path}")
        raise


def command_typography(runner: HeadlessComfyRunner, args: argparse.Namespace) -> int:
    image_path = Path(args.image).expanduser()
    if not image_path.is_absolute():
        raise WorkflowError(f"--image must be an absolute path, got {args.image!r}.")
    output_path = Path(args.output).expanduser() if args.output else None
    typography_summary = runner.run_render_typography_apply(args.family, args.preset, image_path, output_path)
    run_manifest_path = runner.write_typography_run_manifest(
        family=args.family,
        preset=args.preset,
        input_image=image_path,
        typography_summary=typography_summary,
        invocation="typography",
        pipeline_id=None,
    )
    print(
        f"TYPO  {args.family}/{args.preset} image={image_path} "
        f"output={typography_summary['output_artifact']}"
    )
    print(f"INFO  typography run manifest -> {run_manifest_path}")
    return 0


def main() -> int:
    args = parse_args()
    runner = HeadlessComfyRunner(args)
    try:
        if args.command == "server":
            return command_server(runner, args)
        if args.command == "stage":
            return command_stage(runner, args)
        if args.command == "review-proof":
            return command_review_proof(runner, args)
        if args.command == "finalize-still":
            return command_finalize_still(runner, args)
        if args.command == "pipeline":
            return command_pipeline(runner, args)
        if args.command == "typography":
            return command_typography(runner, args)
        raise WorkflowError(f"Unknown command {args.command!r}")
    except WorkflowError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
