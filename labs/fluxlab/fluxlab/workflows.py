from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .config import RuntimeConfig
from .io import read_json, write_json

OFFICIAL_GUIDANCE = 4
OFFICIAL_SAMPLER = "euler"
OFFICIAL_STEPS = 20


def load_raw_ui_template(path: Path) -> dict[str, Any]:
    return read_json(path)


def load_api_template(path: Path) -> dict[str, Any]:
    return read_json(path)


def _find_subgraph_container(workflow: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    subgraph = workflow["definitions"]["subgraphs"][0]
    container = next(node for node in workflow["nodes"] if node["type"] == subgraph["id"])
    return subgraph, container


def patch_ui_workflow(
    template: dict[str, Any],
    *,
    model_filenames: dict[str, str],
    positive_prompt: str,
    negative_prompt: str,
    width: int,
    height: int,
    batch_size: int,
    seed: int,
    filename_prefix: str,
    steps: int = OFFICIAL_STEPS,
) -> dict[str, Any]:
    workflow = copy.deepcopy(template)
    subgraph, container = _find_subgraph_container(workflow)

    container["widgets_values"][0] = positive_prompt
    container["widgets_values"][1] = width
    container["widgets_values"][2] = height
    container["widgets_values"][3] = False
    container["widgets_values"][4] = seed
    container["widgets_values"][5] = "fixed"
    container["widgets_values"][6] = model_filenames["diffusion_model"]
    container["widgets_values"][7] = model_filenames["text_encoder"]
    container["widgets_values"][8] = model_filenames["vae"]

    save_node = next(node for node in workflow["nodes"] if node["type"] == "SaveImage")
    save_node["widgets_values"][0] = filename_prefix

    by_id = {node["id"]: node for node in subgraph["nodes"]}
    by_id[6]["widgets_values"][0] = positive_prompt
    by_id[47]["widgets_values"] = [width, height, batch_size]
    by_id[48]["widgets_values"] = [steps, width, height]
    by_id[25]["widgets_values"] = [seed, "fixed"]
    by_id[10]["widgets_values"] = [model_filenames["vae"]]
    by_id[12]["widgets_values"] = [model_filenames["diffusion_model"], "default"]
    by_id[38]["widgets_values"] = [model_filenames["text_encoder"], "flux2", "default"]
    negative_node_id = subgraph["state"]["lastNodeId"] + 1
    negative_link_id = subgraph["state"]["lastLinkId"] + 1
    negative_node = {
        "id": negative_node_id,
        "type": "CLIPTextEncode",
        "pos": [-1010, 560],
        "size": [422.84375, 164.3125],
        "flags": {"collapsed": False},
        "order": max(node.get("order", 0) for node in subgraph["nodes"]) + 1,
        "mode": 0,
        "inputs": [
            {"name": "clip", "type": "CLIP", "link": negative_link_id},
            {"name": "text", "type": "STRING", "widget": {"name": "text"}, "link": None},
        ],
        "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": None}],
        "title": "CLIP Text Encode (Negative Prompt - Record Only)",
        "properties": {"Node name for S&R": "CLIPTextEncode"},
        "widgets_values": [negative_prompt],
        "color": "#322",
        "bgcolor": "#533",
    }
    subgraph["nodes"].append(negative_node)
    subgraph["links"].append([negative_link_id, 38, 0, negative_node_id, 0, "CLIP"])
    subgraph["state"]["lastNodeId"] = negative_node_id
    subgraph["state"]["lastLinkId"] = negative_link_id
    workflow["last_node_id"] = max(int(workflow["last_node_id"]), negative_node_id)
    workflow["last_link_id"] = max(int(workflow["last_link_id"]), negative_link_id)

    note_node = {
        "id": workflow["last_node_id"] + 1,
        "type": "MarkdownNote",
        "pos": [-1450, 470],
        "size": [510, 220],
        "flags": {"collapsed": False},
        "order": max(node.get("order", 0) for node in workflow["nodes"]) + 1,
        "mode": 0,
        "inputs": [],
        "outputs": [],
        "title": "FluxLab Overrides",
        "properties": {},
        "widgets_values": [
            f"Negative prompt retained for export portability.\n\nnegative_prompt: {negative_prompt}\nseed: {seed}\nbatch_size: {batch_size}\nsteps: {steps}\nfilename_prefix: {filename_prefix}"
        ],
        "color": "#432",
        "bgcolor": "#000",
    }
    workflow["nodes"].append(note_node)
    workflow["last_node_id"] = note_node["id"]
    return workflow


def patch_api_workflow(
    template_bundle: dict[str, Any],
    *,
    model_filenames: dict[str, str],
    positive_prompt: str,
    negative_prompt: str,
    width: int,
    height: int,
    batch_size: int,
    seed: int,
    filename_prefix: str,
    steps: int = OFFICIAL_STEPS,
) -> dict[str, Any]:
    bundle = copy.deepcopy(template_bundle)
    prompt = bundle["prompt"]
    prompt["1"]["inputs"]["unet_name"] = model_filenames["diffusion_model"]
    prompt["2"]["inputs"]["clip_name"] = model_filenames["text_encoder"]
    prompt["3"]["inputs"]["text"] = positive_prompt
    prompt["4"]["inputs"]["text"] = negative_prompt
    prompt["8"]["inputs"]["vae_name"] = model_filenames["vae"]
    prompt["9"]["inputs"]["steps"] = steps
    prompt["9"]["inputs"]["width"] = width
    prompt["9"]["inputs"]["height"] = height
    prompt["10"]["inputs"]["width"] = width
    prompt["10"]["inputs"]["height"] = height
    prompt["10"]["inputs"]["batch_size"] = batch_size
    prompt["11"]["inputs"]["noise_seed"] = seed
    prompt["14"]["inputs"]["filename_prefix"] = filename_prefix
    bundle["meta"]["applied"] = {
        "positive_prompt": positive_prompt,
        "negative_prompt": negative_prompt,
        "width": width,
        "height": height,
        "batch_size": batch_size,
        "steps": steps,
        "seed": seed,
        "filename_prefix": filename_prefix,
        "model_filenames": dict(model_filenames),
    }
    return bundle


def export_workflow_files(
    runtime: RuntimeConfig,
    export_dir: Path,
    *,
    positive_prompt: str,
    negative_prompt: str,
    width: int,
    height: int,
    batch_size: int,
    seed: int,
    filename_prefix: str,
    scene_id: str,
    stage: str,
    steps: int = OFFICIAL_STEPS,
) -> dict[str, Path]:
    export_dir.mkdir(parents=True, exist_ok=True)
    ui_template = load_raw_ui_template(runtime.raw_template_path)
    api_template = load_api_template(runtime.api_template_path)
    ui_payload = patch_ui_workflow(
        ui_template,
        model_filenames=runtime.model_filenames,
        positive_prompt=positive_prompt,
        negative_prompt=negative_prompt,
        width=width,
        height=height,
        batch_size=batch_size,
        seed=seed,
        filename_prefix=filename_prefix,
        steps=steps,
    )
    api_payload = patch_api_workflow(
        api_template,
        model_filenames=runtime.model_filenames,
        positive_prompt=positive_prompt,
        negative_prompt=negative_prompt,
        width=width,
        height=height,
        batch_size=batch_size,
        seed=seed,
        filename_prefix=filename_prefix,
        steps=steps,
    )
    ui_path = export_dir / f"{scene_id}__{stage}.ui.json"
    api_path = export_dir / f"{scene_id}__{stage}.api.json"
    write_json(ui_path, ui_payload)
    write_json(api_path, api_payload)
    return {"ui_path": ui_path, "api_path": api_path}
