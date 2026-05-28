from __future__ import annotations

import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from orchestration.research_sources import display_asset_path

LETTER_WIDTH = 612.0
LETTER_HEIGHT = 792.0
PAGE_MARGIN = 24.0
HEADER_GAP = 8.0
SECTION_GAP = 16.0
GRID_GAP = 12.0
TITLE_SIZE = 14.0
HEADING_SIZE = 11.0
LABEL_SIZE = 9.0
LABEL_LINE_HEIGHT = 12.0
SECTION_LABEL_SIZE = 10.0
SECTION_LABEL_HEIGHT = 14.0
IMAGE_COLS = 4


@dataclass(frozen=True)
class ContactSheetCandidate:
    source_id: str
    candidate_label: str
    image_path: Path


@dataclass(frozen=True)
class ContactSheetSection:
    heading: str
    candidates: tuple[ContactSheetCandidate, ...]


@dataclass(frozen=True)
class ContactSheetPage:
    heading: str
    subtitle: str
    sections: tuple[ContactSheetSection, ...]


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _run_checked(args: list[str]) -> str:
    completed = subprocess.run(args, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        combined = "\n".join(part for part in (completed.stdout.strip(), completed.stderr.strip()) if part).strip()
        raise SystemExit(combined or f"Command failed with exit code {completed.returncode}: {' '.join(args)}")
    return completed.stdout


def _image_dimensions(path: Path) -> tuple[int, int]:
    output = _run_checked(["/usr/bin/sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)])
    width_match = re.search(r"pixelWidth:\s*(\d+)", output)
    height_match = re.search(r"pixelHeight:\s*(\d+)", output)
    if width_match is None or height_match is None:
        raise SystemExit(f"Unable to determine image dimensions for {path}")
    return int(width_match.group(1)), int(height_match.group(1))


def _jpeg_asset(path: Path, temp_dir: Path) -> tuple[Path, int, int]:
    source = Path(path).expanduser()
    if not source.exists():
        raise SystemExit(f"Contact sheet source is missing: {source}")
    suffix = source.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        width, height = _image_dimensions(source)
        return source, width, height
    output_path = temp_dir / f"{source.stem}.jpg"
    _run_checked(["/usr/bin/sips", "-s", "format", "jpeg", str(source), "--out", str(output_path)])
    width, height = _image_dimensions(output_path)
    return output_path, width, height


def _fit_contain(
    *,
    source_width: int,
    source_height: int,
    box_x: float,
    box_y: float,
    box_width: float,
    box_height: float,
) -> tuple[float, float, float, float]:
    if source_width <= 0 or source_height <= 0:
        raise SystemExit("Contact sheet image dimensions must be positive.")
    scale = min(box_width / float(source_width), box_height / float(source_height))
    draw_width = float(source_width) * scale
    draw_height = float(source_height) * scale
    draw_x = box_x + ((box_width - draw_width) / 2.0)
    draw_y = box_y + ((box_height - draw_height) / 2.0)
    return draw_x, draw_y, draw_width, draw_height


def _section_row_count(section: ContactSheetSection) -> int:
    return max(1, (len(section.candidates) + IMAGE_COLS - 1) // IMAGE_COLS)


def _page_layout(page: ContactSheetPage) -> tuple[float, float, float, float, float]:
    total_rows = sum(_section_row_count(section) for section in page.sections)
    content_width = LETTER_WIDTH - (PAGE_MARGIN * 2.0)
    header_height = TITLE_SIZE + HEADING_SIZE + SECTION_GAP
    if page.subtitle:
        header_height += HEADER_GAP + LABEL_LINE_HEIGHT
    grid_top = LETTER_HEIGHT - PAGE_MARGIN - header_height
    grid_height = grid_top - PAGE_MARGIN
    section_heading_height_total = sum(SECTION_LABEL_HEIGHT for section in page.sections if section.heading)
    section_gap_total = SECTION_GAP * max(0, len(page.sections) - 1)
    internal_row_gap_total = sum(GRID_GAP * max(0, _section_row_count(section) - 1) for section in page.sections)
    cell_width = (content_width - (GRID_GAP * (IMAGE_COLS - 1))) / float(IMAGE_COLS)
    available_grid_height = grid_height - section_heading_height_total - section_gap_total - internal_row_gap_total
    cell_height = available_grid_height / float(total_rows)
    image_height = cell_height - LABEL_LINE_HEIGHT
    if image_height <= 0:
        raise SystemExit("Contact sheet layout left no space for images.")
    return content_width, grid_top, cell_width, cell_height, image_height


def _page_commands(
    *,
    title: str,
    page: ContactSheetPage,
    image_names: list[str],
    image_metrics: list[tuple[int, int]],
) -> str:
    content_width, grid_top, cell_width, cell_height, image_height = _page_layout(page)
    commands: list[str] = [
        "0 g",
        "BT",
        f"/F1 {TITLE_SIZE:.2f} Tf",
        f"1 0 0 1 {PAGE_MARGIN:.2f} {LETTER_HEIGHT - PAGE_MARGIN - TITLE_SIZE:.2f} Tm",
        f"({_pdf_escape(title)}) Tj",
        "ET",
        "BT",
        f"/F1 {HEADING_SIZE:.2f} Tf",
        f"1 0 0 1 {PAGE_MARGIN:.2f} {LETTER_HEIGHT - PAGE_MARGIN - TITLE_SIZE - SECTION_GAP:.2f} Tm",
        f"({_pdf_escape(page.heading)}) Tj",
        "ET",
    ]
    if page.subtitle:
        commands.extend(
            [
                "BT",
                f"/F1 {LABEL_SIZE:.2f} Tf",
                f"1 0 0 1 {PAGE_MARGIN:.2f} {LETTER_HEIGHT - PAGE_MARGIN - TITLE_SIZE - SECTION_GAP - HEADER_GAP - LABEL_LINE_HEIGHT:.2f} Tm",
                f"({_pdf_escape(page.subtitle)}) Tj",
                "ET",
            ]
        )
    image_index = 0
    section_top = grid_top
    for section_index, section in enumerate(page.sections):
        row_count = _section_row_count(section)
        if section.heading:
            commands.extend(
                [
                    "BT",
                    f"/F1 {SECTION_LABEL_SIZE:.2f} Tf",
                    f"1 0 0 1 {PAGE_MARGIN:.2f} {section_top - SECTION_LABEL_SIZE:.2f} Tm",
                    f"({_pdf_escape(section.heading)}) Tj",
                    "ET",
                ]
            )
            section_top -= SECTION_LABEL_HEIGHT
        for candidate_index, candidate in enumerate(section.candidates):
            row = candidate_index // IMAGE_COLS
            col = candidate_index % IMAGE_COLS
            cell_x = PAGE_MARGIN + (col * (cell_width + GRID_GAP))
            cell_y = section_top - ((row + 1) * cell_height) - (row * GRID_GAP)
            image_box_y = cell_y + LABEL_LINE_HEIGHT
            source_width, source_height = image_metrics[image_index]
            draw_x, draw_y, draw_width, draw_height = _fit_contain(
                source_width=source_width,
                source_height=source_height,
                box_x=cell_x,
                box_y=image_box_y,
                box_width=cell_width,
                box_height=image_height,
            )
            commands.append(
                f"q {draw_width:.2f} 0 0 {draw_height:.2f} {draw_x:.2f} {draw_y:.2f} cm /{image_names[image_index]} Do Q"
            )
            commands.extend(
                [
                    "BT",
                    f"/F1 {LABEL_SIZE:.2f} Tf",
                    f"1 0 0 1 {cell_x:.2f} {cell_y + 1.0:.2f} Tm",
                    f"({_pdf_escape(candidate.candidate_label)}) Tj",
                    "ET",
                ]
            )
            image_index += 1
        section_top -= (row_count * cell_height) + (max(0, row_count - 1) * GRID_GAP)
        if section_index < len(page.sections) - 1:
            section_top -= SECTION_GAP
    return "\n".join(commands) + "\n"


def _pdf_stream_object(stream: bytes, dictionary: str) -> bytes:
    return dictionary.encode("utf-8") + b"\nstream\n" + stream + b"\nendstream"


def _write_pdf(objects: list[bytes], output_path: Path) -> Path:
    resolved = Path(output_path).expanduser()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    offsets: list[int] = []
    payload = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(payload))
        payload.extend(f"{index} 0 obj\n".encode("utf-8"))
        payload.extend(obj)
        payload.extend(b"\nendobj\n")
    xref_offset = len(payload)
    payload.extend(f"xref\n0 {len(objects) + 1}\n".encode("utf-8"))
    payload.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        payload.extend(f"{offset:010d} 00000 n \n".encode("utf-8"))
    payload.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("utf-8")
    )
    resolved.write_bytes(payload)
    return resolved


def build_contact_sheet_pages(manifest: dict[str, Any]) -> list[ContactSheetPage]:
    visual_research = manifest.get("visual_research", {})
    inventory = visual_research.get("_source_inventory", {})
    sources = list(inventory.get("sources", [])) if isinstance(inventory, dict) else []
    opening_sequence = visual_research.get("opening_sequence", {})
    acts = list(visual_research.get("acts") or [])

    def build_candidate(entry: dict[str, Any]) -> ContactSheetCandidate:
        return ContactSheetCandidate(
            source_id=str(entry.get("source_id", "")).strip(),
            candidate_label=str(entry.get("candidate_label", "")).strip(),
            image_path=Path(display_asset_path(entry)).expanduser(),
        )

    opening_entries = [entry for entry in sources if str(entry.get("coverage_id", "")).strip() == "opening"]
    opening_object_strategy = str(opening_sequence.get("object_strategy", "")).strip() or "episode_specific_cluster"
    opening_slots = [
        {
            "slot_id": str(slot.get("slot_id", "")).strip(),
            "display_label": str(slot.get("display_label", "")).strip(),
        }
        for slot in opening_sequence.get("slots", [])
        if isinstance(slot, dict) and str(slot.get("slot_id", "")).strip()
    ]
    if opening_slots:
        slot_lookup = {slot["slot_id"]: slot for slot in opening_slots}
        unassigned_source_ids = [
            str(entry.get("source_id", "")).strip()
            for entry in opening_entries
            if str(entry.get("opening_slot_id", "")).strip() not in slot_lookup
        ]
        if unassigned_source_ids:
            raise SystemExit(
                "Opening tableau candidates must map to explicit opening slots: "
                + ", ".join(unassigned_source_ids)
                + "."
            )
        opening_sections = tuple(
            ContactSheetSection(
                heading=slot["display_label"],
                candidates=tuple(
                    build_candidate(entry)
                    for entry in opening_entries
                    if str(entry.get("opening_slot_id", "")).strip() == slot["slot_id"]
                ),
            )
            for slot in opening_slots
        )
    else:
        opening_sections = (
            ContactSheetSection(
                heading="",
                candidates=tuple(build_candidate(entry) for entry in opening_entries),
            ),
        )
    pages: list[ContactSheetPage] = [
        ContactSheetPage(
            heading="Opening Tableau",
            subtitle=" / ".join(
                part
                for part in (
                    str(opening_sequence.get("time_period_label", "")).strip(),
                    "generic era culture cluster" if opening_object_strategy == "generic_era_cluster" else "",
                )
                if part
            ),
            sections=opening_sections,
        )
    ]
    for act in acts:
        act_id = str(act.get("id", "")).strip()
        act_title = str(act.get("title", "")).strip()
        act_candidates = tuple(build_candidate(entry) for entry in sources if str(entry.get("coverage_id", "")).strip() == act_id)
        pages.append(
            ContactSheetPage(
                heading=f"{act_id.upper()} {act_title}".strip(),
                subtitle="",
                sections=(ContactSheetSection(heading="", candidates=act_candidates),),
            )
        )
    return pages


def render_contact_sheet_pdf(manifest: dict[str, Any], output_path: Path) -> Path:
    episode_title = str(manifest.get("title", "")).strip() or str(manifest.get("id", "")).strip()
    pages = build_contact_sheet_pages(manifest)
    temp_dir = Path(tempfile.mkdtemp(prefix="ce-contact-sheet-"))
    catalog_object = b"<< /Type /Catalog /Pages 2 0 R >>"
    font_object_number = 3
    page_count = len(pages)
    first_page_object_number = 4
    kids = " ".join(
        f"{first_page_object_number + (page_index * 2)} 0 R"
        for page_index in range(page_count)
    )
    pages_object = f"<< /Type /Pages /Count {page_count} /Kids [{kids}] >>".encode("utf-8")
    font_object = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    image_object_number = first_page_object_number + (page_count * 2)
    current_image_object_number = image_object_number
    page_objects: list[bytes] = []
    image_objects: list[bytes] = []
    for page_index, page in enumerate(pages):
        if not page.sections:
            raise SystemExit(f"Contact sheet page `{page.heading}` has no sections to render.")
        image_names: list[str] = []
        image_metrics: list[tuple[int, int]] = []
        xobjects: list[str] = []
        candidate_index = 0
        for section in page.sections:
            if not section.candidates:
                raise SystemExit(f"Contact sheet section `{section.heading or page.heading}` has no candidates to render.")
            for candidate in section.candidates:
                candidate_index += 1
                if not candidate.candidate_label:
                    raise SystemExit(f"Contact sheet candidate `{candidate.source_id}` is missing candidate_label.")
                if not candidate.image_path.exists():
                    raise SystemExit(
                        f"Contact sheet candidate `{candidate.source_id}` is missing a usable image at `{candidate.image_path}`."
                    )
                jpeg_path, width, height = _jpeg_asset(candidate.image_path, temp_dir)
                image_data = jpeg_path.read_bytes()
                image_name = f"Im{page_index + 1}_{candidate_index}"
                image_objects.append(
                    _pdf_stream_object(
                        image_data,
                        f"<< /Type /XObject /Subtype /Image /Width {width} /Height {height} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length {len(image_data)} >>",
                    )
                )
                image_names.append(image_name)
                image_metrics.append((width, height))
                xobjects.append(f"/{image_name} {current_image_object_number} 0 R")
                current_image_object_number += 1

        content_stream = _page_commands(
            title=f"{episode_title} Contact Sheet",
            page=page,
            image_names=image_names,
            image_metrics=image_metrics,
        ).encode("utf-8")
        content_object_number = first_page_object_number + (page_index * 2) + 1
        page_object = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {LETTER_WIDTH:.0f} {LETTER_HEIGHT:.0f}] "
            f"/Resources << /Font << /F1 {font_object_number} 0 R >> /XObject << {' '.join(xobjects)} >> >> "
            f"/Contents {content_object_number} 0 R >>"
        ).encode("utf-8")
        page_objects.extend(
            [
                page_object,
                _pdf_stream_object(content_stream, f"<< /Length {len(content_stream)} >>"),
            ]
        )

    objects = [catalog_object, pages_object, font_object, *page_objects, *image_objects]
    return _write_pdf(objects, output_path)


__all__ = [
    "ContactSheetCandidate",
    "ContactSheetSection",
    "ContactSheetPage",
    "build_contact_sheet_pages",
    "render_contact_sheet_pdf",
    "_fit_contain",
]
