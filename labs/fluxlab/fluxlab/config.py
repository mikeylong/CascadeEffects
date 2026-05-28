from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DEFAULT_MODEL_FILENAMES = {
    "text_encoder": "mistral_3_small_flux2_bf16.safetensors",
    "diffusion_model": "flux2-dev.safetensors",
    "vae": "flux2-vae.safetensors",
}

MODEL_FILENAME_ENV_KEYS = {
    "text_encoder": "CE_FLUXLAB_TEXT_ENCODER_FILENAME",
    "diffusion_model": "CE_FLUXLAB_DIFFUSION_MODEL_FILENAME",
    "vae": "CE_FLUXLAB_VAE_FILENAME",
}


def _load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


@dataclass(frozen=True)
class RuntimeConfig:
    repo_root: Path
    prompts_path: Path
    scenes_root: Path
    benchmark_suites_root: Path
    proof_suites_root: Path
    exports_root: Path
    runs_root: Path
    reports_root: Path
    raw_template_path: Path
    api_template_path: Path
    comfy_root: Path
    comfy_api_url: str
    comfy_output_root: Path
    comfy_workflow_root: Path
    output_namespace: str
    model_filenames: dict[str, str]
    model_paths: dict[str, Path]


def _load_model_filenames(env: dict[str, str]) -> dict[str, str]:
    return {
        name: env.get(MODEL_FILENAME_ENV_KEYS[name], default_filename)
        for name, default_filename in DEFAULT_MODEL_FILENAMES.items()
    }


def load_runtime(repo_root: Path) -> RuntimeConfig:
    repo_root = repo_root.expanduser().resolve()
    env = _load_env(repo_root / "config" / "paths.env")
    comfy_root = Path(env.get("CE_COMFY_ROOT", "/Users/mike/AI/comfy")).expanduser().resolve()
    output_namespace = env.get("CE_FLUXLAB_OUTPUT_NAMESPACE", "cascadeeffects_fluxlab")
    model_filenames = _load_model_filenames(env)
    model_paths = {
        "text_encoder": comfy_root / "models" / "text_encoders" / model_filenames["text_encoder"],
        "diffusion_model": comfy_root / "models" / "diffusion_models" / model_filenames["diffusion_model"],
        "vae": comfy_root / "models" / "vae" / model_filenames["vae"],
    }
    return RuntimeConfig(
        repo_root=repo_root,
        prompts_path=repo_root / "prompts" / "canon.json",
        scenes_root=repo_root / "scenes",
        benchmark_suites_root=repo_root / "benchmarks" / "suites",
        proof_suites_root=repo_root / "proofs" / "suites",
        exports_root=repo_root / "exports",
        runs_root=repo_root / "runs",
        reports_root=repo_root / "reports",
        raw_template_path=repo_root / "templates" / "raw" / "image_flux2_text_to_image.official.json",
        api_template_path=repo_root / "templates" / "api" / "flux2_dev_text_to_image.api.json",
        comfy_root=comfy_root,
        comfy_api_url=env.get("CE_COMFY_API_URL", "http://127.0.0.1:8000").rstrip("/"),
        comfy_output_root=comfy_root / "output" / output_namespace,
        comfy_workflow_root=comfy_root / "user" / "default" / "workflows",
        output_namespace=output_namespace,
        model_filenames=model_filenames,
        model_paths=model_paths,
    )


def ensure_runtime_dirs(runtime: RuntimeConfig) -> None:
    for path in (
        runtime.exports_root,
        runtime.runs_root,
        runtime.reports_root,
        runtime.benchmark_suites_root,
        runtime.proof_suites_root,
    ):
        path.mkdir(parents=True, exist_ok=True)
