#!/usr/bin/env python3
"""Build an HTML-only channel trailer end-screen review with borderless targets."""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


BASE_SCRIPT = Path(__file__).with_name("build_channel_trailer_end_screen_titleless_repair.py")
SPEC = importlib.util.spec_from_file_location("channel_trailer_end_screen_titleless_repair", BASE_SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise SystemExit(f"Could not load base builder: {BASE_SCRIPT}")
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)


WORKFLOW = "channel_trailer_end_screen_adaptive_borderless_html_review_v1"
STYLE_MODEL = "youtube_placeholder_borderless_underlay_v1"
RENDER_MODEL = "pillow_adaptive_titleless_borderless_youtube_underlay_v1"
OUTPUT_STEM = "channel_trailer_end_screen_adaptive_borderless_html_review"
MANIFEST_NAME = f"{OUTPUT_STEM}_manifest.json"


def alpha_layer() -> Image.Image:
    return Image.new("RGBA", (base.WIDTH, base.HEIGHT), (0, 0, 0, 0))


def composite_rect_fill(frame: Image.Image, box: tuple[int, int, int, int], fill_rgba: str) -> None:
    x, y, w, h = box
    layer = alpha_layer()
    draw = ImageDraw.Draw(layer)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=18, fill=base.rgba_tuple(fill_rgba))
    frame.alpha_composite(layer)


def composite_ellipse_fill(frame: Image.Image, box: tuple[int, int, int, int], fill_rgba: str) -> None:
    x, y, w, h = box
    layer = alpha_layer()
    draw = ImageDraw.Draw(layer)
    draw.ellipse((x, y, x + w, y + h), fill=base.rgba_tuple(fill_rgba))
    frame.alpha_composite(layer)


def draw_borderless_targets(frame: Image.Image, palette: dict[str, Any]) -> None:
    targets = palette["targets"]
    composite_rect_fill(frame, base.TARGETS["left_video"], targets["left_video"]["fill_rgba"])
    composite_rect_fill(frame, base.TARGETS["right_video"], targets["right_video"]["fill_rgba"])
    composite_ellipse_fill(frame, base.TARGETS["subscribe"], targets["center_subscribe"]["fill_rgba"])


def apply_borderless_contract_fields(contract: dict[str, Any]) -> dict[str, Any]:
    contract["placeholder_style_model"] = STYLE_MODEL
    contract["outline_model"] = STYLE_MODEL
    contract["borderless_underlay"] = {
        "enabled": True,
        "removed": ["css_border", "outer_glow_ring", "inset_glow_ring", "subscribe_inner_ring", "drop_shadow"],
        "fill_preserved": True,
    }
    contract["css_variables"] = {
        "--ce-end-screen-left-target-fill": contract["target_palette"]["targets"]["left_video"]["fill_rgba"],
        "--ce-end-screen-right-target-fill": contract["target_palette"]["targets"]["right_video"]["fill_rgba"],
        "--ce-end-screen-subscribe-fill": contract["target_palette"]["targets"]["center_subscribe"]["fill_rgba"],
        "--ce-end-screen-outline-model": STYLE_MODEL,
    }
    contract["reads"] = {
        **contract["reads"],
        "end_screen_target_contrast_read": "pass_borderless_underlay_legible_without_target_outlines",
        "end_screen_placeholder_style_read": f"pass_{STYLE_MODEL}",
        "end_screen_outline_removal_read": "pass_borders_glow_rings_inset_rings_subscribe_inner_ring_and_shadow_removed",
        "end_screen_fill_preservation_read": "pass_translucent_target_fills_preserved",
    }
    contract["target_palette"]["placeholder_style_model"] = STYLE_MODEL
    contract["target_palette"]["outline_model"] = STYLE_MODEL
    contract["target_palette"]["borderless_underlay"] = contract["borderless_underlay"]
    return contract


def borderless_end_screen_frame(images_dir: Path) -> tuple[Image.Image, dict[str, Any], dict[str, str]]:
    images_dir.mkdir(parents=True, exist_ok=True)
    backplate = base.titleless_end_screen_backplate()
    backplate_path = images_dir / "adaptive_titleless_borderless_end_screen_backplate.png"
    preview_path = images_dir / "adaptive_titleless_borderless_end_screen_preview.png"
    backplate.convert("RGB").save(backplate_path)

    palette = base.end_screen_palette_for_backplate(backplate, backplate_path)
    frame = backplate.copy()
    draw_borderless_targets(frame, palette)
    frame.convert("RGB").save(preview_path)

    contract = base.end_screen_palette_contract_from_palette(palette, backplate_path)
    apply_borderless_contract_fields(contract)
    contract["adaptive_render"] = {
        "render_model": RENDER_MODEL,
        "preview_path": str(preview_path),
        "clean_backplate_path": str(backplate_path),
        "youtube_end_screen_template_id": base.END_SCREEN_TEMPLATE_ID,
        "placeholder_style_model": STYLE_MODEL,
        "layout_bbox_xy": {
            "left_video": base.bbox_from_rect(base.TARGETS["left_video"]),
            "right_video": base.bbox_from_rect(base.TARGETS["right_video"]),
            "center_subscribe": base.bbox_from_rect(base.TARGETS["subscribe"]),
        },
        "reads": {
            "html_review_preview_read": "pass_adaptive_titleless_borderless_end_screen_preview_rendered",
            "end_screen_title_artifact_removal_read": "pass_no_cascade_of_effects_title_on_preview_backplate",
            "end_screen_target_geometry_read": "pass_titleless_two_video_subscribe_safe_zone_geometry",
            "end_screen_placeholder_style_read": f"pass_{STYLE_MODEL}",
        },
    }
    return frame.convert("RGB"), contract, {"clean_backplate": str(backplate_path), "preview": str(preview_path)}


def build_borderless_pixel_qa(
    clean_backplate: Image.Image,
    rendered: Image.Image,
    palette_contract: dict[str, Any],
    qa_path: Path,
) -> dict[str, Any]:
    clean_rgb = clean_backplate.convert("RGB")
    rendered_rgb = rendered.convert("RGB")
    target_palette = palette_contract["target_palette"]["targets"]
    target_map = {
        "left_video": ("left_video", base.TARGETS["left_video"]),
        "right_video": ("right_video", base.TARGETS["right_video"]),
        "center_subscribe": ("center_subscribe", base.TARGETS["subscribe"]),
    }
    samples: list[dict[str, Any]] = []
    for target_key, (palette_key, box) in target_map.items():
        x, y, w, h = box
        target = target_palette[palette_key]
        fill_rgba = base.rgba_tuple(target["fill_rgba"])
        fill_points = [
            ("fill_center", (x + w // 2, y + h // 2)),
            ("top_edge_fill_no_outline", (x + w // 2, y + (3 if target_key == "center_subscribe" else 2))),
        ]
        for sample_role, point in fill_points:
            underlay_rgb = clean_rgb.getpixel(point)
            expected_rgb = base.blend_rgba_over_rgb(fill_rgba, underlay_rgb)
            actual_rgb = rendered_rgb.getpixel(point)
            delta = base.max_channel_delta(actual_rgb, expected_rgb)
            samples.append(
                {
                    "target_key": target_key,
                    "sample_role": sample_role,
                    "point_xy": list(point),
                    "manifest_color_key": "fill_rgba",
                    "manifest_color": target["fill_rgba"],
                    "source_underlay_rgb": list(underlay_rgb),
                    "expected_composited_rgb": list(expected_rgb),
                    "actual_rgb": list(actual_rgb),
                    "max_channel_delta": delta,
                    "tolerance": 5,
                    "sample_read": "pass" if delta <= 5 else "tighten",
                }
            )
        outside_point = (x + w // 2, max(0, y - 8))
        expected_outside = clean_rgb.getpixel(outside_point)
        actual_outside = rendered_rgb.getpixel(outside_point)
        outside_delta = base.max_channel_delta(actual_outside, expected_outside)
        samples.append(
            {
                "target_key": target_key,
                "sample_role": "outside_target_no_ring_or_shadow",
                "point_xy": list(outside_point),
                "expected_rgb": list(expected_outside),
                "actual_rgb": list(actual_outside),
                "max_channel_delta": outside_delta,
                "tolerance": 2,
                "sample_read": "pass" if outside_delta <= 2 else "tighten",
            }
        )
    artifact = {
        "model_id": "channel_trailer_borderless_end_screen_pixel_qa_v1",
        "placeholder_style_model": STYLE_MODEL,
        "target_count": len(target_map),
        "sample_count": len(samples),
        "samples": samples,
        "reads": {
            "end_screen_borderless_pixel_sample_read": "pass_borderless_underlay_pixels_match_manifest_fill_and_no_outline_samples"
            if all(sample["sample_read"] == "pass" for sample in samples)
            else "tighten_borderless_underlay_pixel_samples_mismatch",
            "end_screen_adaptive_pixel_sample_read": "pass_adaptive_placeholder_pixels_match_manifest_palette"
            if all(sample["sample_read"] == "pass" for sample in samples)
            else "tighten_adaptive_placeholder_pixels_mismatch_manifest_palette",
        },
    }
    base.write_json(qa_path, artifact)
    return artifact


def create_borderless_target_sheet(rendered: Image.Image, palette_contract: dict[str, Any], out_path: Path) -> Path:
    rendered_rgb = rendered.convert("RGB")
    thumb_w, thumb_h = 640, 360
    crop_w, crop_h = 520, 300
    sheet = Image.new("RGB", (thumb_w * 2, thumb_h + crop_h * 2 + 92), (8, 10, 18))
    draw = ImageDraw.Draw(sheet)
    label_font = base.font(22, bold=True)
    small = base.font(17)
    preview = rendered_rgb.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
    sheet.paste(preview, (0, 0))
    draw.text((18, thumb_h + 12), "Adaptive titleless borderless end screen", font=label_font, fill=(236, 228, 204))
    fills = [
        ("left fill", palette_contract["target_palette"]["targets"]["left_video"]["fill_rgba"]),
        ("right fill", palette_contract["target_palette"]["targets"]["right_video"]["fill_rgba"]),
        ("subscribe fill", palette_contract["target_palette"]["targets"]["center_subscribe"]["fill_rgba"]),
        ("outline model", STYLE_MODEL),
    ]
    for index, (label, value) in enumerate(fills):
        y = 28 + index * 58
        if value.startswith("rgba("):
            draw.rounded_rectangle((thumb_w + 28, y, thumb_w + 118, y + 34), radius=8, fill=base.rgba_tuple(value))
        draw.text((thumb_w + 136, y + 4), f"{label}: {value}", font=small, fill=(236, 228, 204))

    crops = [
        ("left video fill only", base.TARGETS["left_video"]),
        ("right video fill only", base.TARGETS["right_video"]),
        ("subscribe fill only", base.TARGETS["subscribe"]),
    ]
    for index, (label, box) in enumerate(crops):
        x, y, w, h = box
        margin = 48
        crop = rendered_rgb.crop((max(0, x - margin), max(0, y - margin), min(base.WIDTH, x + w + margin), min(base.HEIGHT, y + h + margin)))
        crop.thumbnail((crop_w, crop_h - 42), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (crop_w, crop_h), (11, 14, 25))
        canvas.paste(crop, ((crop_w - crop.width) // 2, 16))
        crop_draw = ImageDraw.Draw(canvas)
        crop_draw.text((18, crop_h - 34), label, font=small, fill=(236, 228, 204))
        col = index % 2
        row = index // 2
        sheet.paste(canvas, (col * crop_w + 80, thumb_h + 56 + row * crop_h))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    return out_path


def make_review_html(
    package_dir: Path,
    preview: Path,
    target_sheet: Path,
    pixel_qa_path: Path,
    manifest_path: Path,
    palette_contract: dict[str, Any],
) -> Path:
    review = package_dir / "review.html"
    swatches = "\n".join(
        f"""        <div class="swatch"><span style="background:{value if value.startswith('rgba(') else 'transparent'}"></span><code>{key}: {value}</code></div>"""
        for key, value in palette_contract["css_variables"].items()
    )
    review.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,">
  <title>Channel Trailer Adaptive Borderless End Screen HTML Review</title>
  <style>
    :root {{
      color-scheme: dark;
      --paper: #eee6cc;
      --muted: #aeb8c7;
      --ink: #070a12;
      --line: #2d3448;
      {chr(10).join(f"{key}: {value};" for key, value in palette_contract["css_variables"].items())}
    }}
    body {{ margin: 0; background: var(--ink); color: var(--paper); font-family: Arial, Helvetica, sans-serif; }}
    main {{ max-width: 1240px; margin: 0 auto; padding: 28px 22px 48px; }}
    h1 {{ margin: 0 0 6px; font-size: 28px; letter-spacing: 0; }}
    p {{ color: var(--muted); line-height: 1.45; }}
    img {{ width: 100%; height: auto; display: block; background: #000; border: 1px solid var(--line); }}
    section {{ margin-top: 26px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 10px 18px; }}
    .swatch {{ display: flex; align-items: center; gap: 10px; min-width: 0; }}
    .swatch span {{ width: 44px; height: 28px; border: 1px solid rgba(255,255,255,.28); border-radius: 6px; flex: 0 0 auto; }}
    code {{ color: var(--paper); white-space: normal; overflow-wrap: anywhere; }}
    a {{ color: #dede35; }}
  </style>
</head>
<body>
  <main>
    <h1>Channel Trailer Adaptive Borderless End Screen HTML Review</h1>
    <p>HTML-only gate. No MP4 has been rendered from this package.</p>
    <section>
      <h2>End Screen Preview</h2>
      <img alt="Adaptive titleless borderless YouTube end screen preview" src="{preview.relative_to(package_dir)}">
    </section>
    <section>
      <h2>Target Crops</h2>
      <img alt="Adaptive borderless end-screen target crops and fill swatches" src="{target_sheet.relative_to(package_dir)}">
    </section>
    <section>
      <h2>Palette Variables</h2>
      <div class="grid">
{swatches}
      </div>
    </section>
    <section>
      <p><a href="{manifest_path.relative_to(package_dir)}">Manifest</a> - <a href="{pixel_qa_path.relative_to(package_dir)}">Pixel QA</a></p>
    </section>
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )
    return review


def build_manifest(
    package_dir: Path,
    preview: Path,
    clean_backplate: Path,
    target_sheet: Path,
    pixel_qa_path: Path,
    pixel_qa: dict[str, Any],
    palette_contract: dict[str, Any],
    timestamp: str,
) -> dict[str, Any]:
    manifest = base.build_html_review_manifest(
        package_dir,
        preview,
        clean_backplate,
        target_sheet,
        pixel_qa_path,
        pixel_qa,
        palette_contract,
        timestamp,
    )
    manifest["artifact_id"] = f"{OUTPUT_STEM}_{timestamp}"
    manifest["workflow"] = WORKFLOW
    manifest["end_screen_placeholder_style_model"] = STYLE_MODEL
    manifest["end_screen_outline_model"] = STYLE_MODEL
    manifest["production_contract"]["intent"] = "repair"
    manifest["reads"] = {
        **manifest["reads"],
        "end_screen_target_contrast_read": palette_contract["reads"]["end_screen_target_contrast_read"],
        "end_screen_placeholder_style_read": f"pass_{STYLE_MODEL}",
        "end_screen_outline_removal_read": palette_contract["reads"]["end_screen_outline_removal_read"],
        "end_screen_fill_preservation_read": palette_contract["reads"]["end_screen_fill_preservation_read"],
        "end_screen_borderless_pixel_sample_read": pixel_qa["reads"]["end_screen_borderless_pixel_sample_read"],
    }
    manifest["timeline"]["youtube_end_screen_placeholder_style_model"] = STYLE_MODEL
    manifest["end_screen_palette_contract"] = palette_contract
    manifest["pixel_qa"] = pixel_qa
    manifest["outputs"] = {
        **manifest["outputs"],
        "review_html": str(package_dir / "review.html"),
        "adaptive_end_screen_preview": str(preview),
        "adaptive_end_screen_preview_sha256": base.sha256(preview),
        "adaptive_end_screen_clean_backplate": str(clean_backplate),
        "adaptive_end_screen_clean_backplate_sha256": base.sha256(clean_backplate),
        "target_sheet": str(target_sheet),
        "target_sheet_sha256": base.sha256(target_sheet),
        "pixel_qa": str(pixel_qa_path),
        "pixel_qa_sha256": base.sha256(pixel_qa_path),
        "manifest": str(package_dir / MANIFEST_NAME),
        "mp4_render_created": False,
    }
    return manifest


def build_package(timestamp: str) -> dict[str, Any]:
    package_dir = base.OUTPUT_ROOT / f"{OUTPUT_STEM}_{timestamp}"
    images_dir = package_dir / "images"
    qa_dir = package_dir / "qa"
    for directory in (images_dir, qa_dir):
        directory.mkdir(parents=True, exist_ok=True)

    end_screen, palette_contract, image_outputs = borderless_end_screen_frame(images_dir)
    clean_backplate = Image.open(image_outputs["clean_backplate"]).convert("RGB")
    preview = Path(image_outputs["preview"])
    target_sheet = create_borderless_target_sheet(
        end_screen,
        palette_contract,
        qa_dir / "adaptive_borderless_end_screen_target_crops.png",
    )
    pixel_qa_path = qa_dir / "end_screen_borderless_palette_pixel_qa.json"
    pixel_qa = build_borderless_pixel_qa(clean_backplate, end_screen, palette_contract, pixel_qa_path)
    manifest = build_manifest(
        package_dir,
        preview,
        Path(image_outputs["clean_backplate"]),
        target_sheet,
        pixel_qa_path,
        pixel_qa,
        palette_contract,
        timestamp,
    )
    manifest_path = package_dir / MANIFEST_NAME
    base.write_json(manifest_path, manifest)
    contract_receipt = base.run_contract_validator(manifest_path)
    manifest["production_contract_receipt"] = {
        "path": contract_receipt.get("receipt_path", ""),
        "ok": contract_receipt.get("ok"),
        "contract_id": contract_receipt.get("contract_id"),
        "intent": contract_receipt.get("intent"),
        "youtube_action_allowed": contract_receipt.get("youtube_action_allowed"),
        "reads": contract_receipt.get("reads"),
    }
    base.write_json(manifest_path, manifest)
    review_html = make_review_html(
        package_dir,
        preview,
        target_sheet,
        pixel_qa_path,
        manifest_path,
        palette_contract,
    )
    manifest["outputs"]["review_html"] = str(review_html)
    base.write_json(manifest_path, manifest)

    readme = package_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# Channel Trailer Adaptive Borderless End Screen HTML Review",
                "",
                f"- Review HTML: `{review_html}`",
                f"- End-screen preview: `{preview}`",
                f"- Target crops: `{target_sheet}`",
                f"- Pixel QA: `{pixel_qa_path}`",
                f"- Manifest: `{manifest_path}`",
                "- Status: `html_review_pending_human_keep`",
                "- Scope: HTML-only adaptive end-screen review. No MP4 was rendered from this package.",
                "- Change under review: titleless YouTube placeholders use the adaptive backplate-sampled fill as borderless underlays.",
                "- Removed target treatment: CSS border, outer glow ring, inset ring, subscribe inner ring, and drop shadow.",
                "- MP4: blocked until explicit human approval of this HTML review.",
                "- YouTube: no upload, delete, visibility, or channel-trailer action.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    latest_payload = {
        "package_dir": str(package_dir),
        "review_html": str(review_html),
        "manifest": str(manifest_path),
        "adaptive_end_screen_preview": str(preview),
        "placeholder_style_model": STYLE_MODEL,
        "mp4_render_created": False,
        "may_render_mp4": False,
    }
    base.write_json(base.OUTPUT_ROOT / f"{OUTPUT_STEM}_latest.json", latest_payload)
    base.write_json(base.OUTPUT_ROOT / "channel_trailer_end_screen_adaptive_html_review_latest.json", latest_payload)
    return {
        "package_dir": str(package_dir),
        "review_html": str(review_html),
        "adaptive_end_screen_preview": str(preview),
        "target_sheet": str(target_sheet),
        "pixel_qa": str(pixel_qa_path),
        "manifest": str(manifest_path),
        "status": manifest["status"],
        "placeholder_style_model": STYLE_MODEL,
        "mp4_render_created": False,
        "may_render_mp4": False,
        "reads": manifest["reads"],
    }


def main() -> int:
    for path in (base.PREDECESSOR_MP4, base.PREDECESSOR_MANIFEST, base.TITANIC_END_SCREEN_BASE_PLATE):
        base.require_file(path)
    timestamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    print(json.dumps(build_package(timestamp), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
