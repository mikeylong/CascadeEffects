from __future__ import annotations

import html
import json
import mimetypes
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from inbox_app.agents_bridge import Context
from inbox_app.review import (
    build_review_inbox,
    build_review_message_detail,
    ensure_allowed_asset_path,
    perform_review_action,
)
from inbox_app.review_brand import BrandTheme, load_signal_brand_theme


ASSET_CHUNK_SIZE = 1024 * 1024

REVIEW_NEUTRAL_THEME_OVERRIDES = {
    "--alert": "#E8E8E8",
    "--alert-soft": "rgba(232, 232, 232, 0.12)",
    "--body-bg": "linear-gradient(180deg, #0E0E0E 0%, #191919 60%, #0E0E0E 100%)",
    "--charcoal": "#4F4F4F",
    "--ink": "#0E0E0E",
    "--line": "rgba(255, 255, 255, 0.14)",
    "--line-strong": "rgba(255, 255, 255, 0.28)",
    "--muted": "#C7C7C7",
    "--muted-soft": "#AFAFAF",
    "--paper": "#171717",
    "--paper-soft": "rgba(48, 48, 48, 0.94)",
    "--paper-strong": "rgba(62, 62, 62, 0.98)",
    "--parchment": "#242424",
    "--signal": "#D8D8D8",
    "--signal-soft": "rgba(216, 216, 216, 0.14)",
    "--signal-wash": "rgba(216, 216, 216, 0.14)",
    "--stage-bg": "linear-gradient(180deg, #353535 0%, #0E0E0E 100%)",
    "--stage-line": "rgba(255, 255, 255, 0.12)",
    "--text-inverse": "#F4F4F4",
    "--text-primary": "#F4F4F4",
    "--text-secondary-dark": "#CFCFCF",
    "--white-12": "rgba(255, 255, 255, 0.12)",
    "--white-24": "rgba(255, 255, 255, 0.24)",
    "--white-60": "#CFCFCF",
}


class UnsatisfiableRange(ValueError):
    pass


def _parse_byte_range(range_header: str | None, file_size: int) -> tuple[int, int] | None:
    if not range_header:
        return None
    unit, separator, raw_spec = range_header.partition("=")
    if separator != "=" or unit.strip().lower() != "bytes":
        return None
    spec = raw_spec.strip()
    if not spec or "," in spec:
        return None
    raw_start, dash, raw_end = spec.partition("-")
    if dash != "-":
        return None
    start_text = raw_start.strip()
    end_text = raw_end.strip()
    if not start_text:
        if not end_text.isdigit():
            return None
        suffix_length = int(end_text)
        if suffix_length <= 0 or file_size <= 0:
            raise UnsatisfiableRange
        if suffix_length >= file_size:
            return (0, file_size - 1)
        return (file_size - suffix_length, file_size - 1)
    if not start_text.isdigit():
        return None
    start = int(start_text)
    if end_text:
        if not end_text.isdigit():
            return None
        end = int(end_text)
        if end < start:
            raise UnsatisfiableRange
    else:
        end = file_size - 1
    if file_size <= 0 or start >= file_size:
        raise UnsatisfiableRange
    return (start, min(end, file_size - 1))


def _optional_request_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _request_tags(value: Any) -> list[str]:
    if isinstance(value, list):
        tags: list[str] = []
        seen: set[str] = set()
        for item in value:
            tag = str(item).strip()
            if not tag or tag in seen:
                continue
            seen.add(tag)
            tags.append(tag)
        return tags
    if value is None:
        return []
    tag = str(value).strip()
    return [tag] if tag else []


def _render_css_variables(css_variables: dict[str, str], *, indent: str = "      ") -> str:
    lines = [f"{indent}{name}: {value};" for name, value in sorted(css_variables.items())]
    return "\n".join(lines)


def _render_theme_styles(theme: BrandTheme) -> str:
    base_variables = (theme.dark_css_variables or theme.css_variables) | REVIEW_NEUTRAL_THEME_OVERRIDES
    color_scheme = "dark" if theme.dark_css_variables else "light"
    sections = [
        "    :root {",
        _render_css_variables(base_variables),
        f"      color-scheme: {color_scheme};",
        "    }",
    ]
    return "\n".join(sections)


def _render_warning_banner(theme: BrandTheme) -> str:
    if not theme.warning:
        return ""
    return (
        '<div class="theme-warning" role="status">'
        f"<strong>Brand fallback active.</strong> {html.escape(theme.warning)}"
        "</div>"
    )


def render_markdown_html(markdown_text: str, title: str = "Markdown Preview", *, theme: BrandTheme | None = None) -> str:
    active_theme = theme or BrandTheme()
    escaped = html.escape(markdown_text).replace("\r\n", "\n")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
  <style>
{_render_theme_styles(active_theme)}
    body {{
      margin: 0;
      padding: 32px;
      font: var(--type-body-weight, 400) var(--type-body-size, 12px)/1.6 var(--font-mono, "IBM Plex Mono", monospace);
      color: var(--text-primary, #18191c);
      background: var(--body-bg, linear-gradient(180deg, #f3f1eb 0%, #e8e2d7 58%, #f3f1eb 100%));
      white-space: pre-wrap;
    }}
    .theme-warning {{
      margin-bottom: 20px;
      padding: 14px 16px;
      border-radius: var(--radius-md, 12px);
      border: 1px solid var(--alert, #ff3b30);
      background: var(--alert-soft, rgba(255, 59, 48, 0.16));
      color: var(--text-primary, #18191c);
      font-family: var(--font-ui, sans-serif);
    }}
    .theme-warning strong {{
      display: block;
      margin-bottom: 4px;
      font: var(--type-overline-weight, 400) var(--type-overline-size, 11px)/1.2 var(--font-ui, sans-serif);
      letter-spacing: var(--tracking-caps, 0.8px);
      text-transform: uppercase;
    }}
  </style>
</head>
<body>{_render_warning_banner(active_theme)}{escaped}</body>
</html>"""


def render_review_page(
    *,
    title: str,
    episode_id: str | None = None,
    theme: BrandTheme | None = None,
    dev_reload_enabled: bool = False,
    server_instance_id: str = "",
) -> str:
    active_theme = theme or BrandTheme()
    template = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Cascade Effects / Review Desk</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
__THEME_STYLES__
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      background: var(--body-bg);
      color: var(--text-primary);
      font: var(--type-body-weight) var(--type-body-size)/1.6 var(--font-sans);
      min-height: 100vh;
      overflow-x: auto;
      overflow-y: hidden;
    }
    a {
      color: inherit;
      text-decoration: none;
    }
    button,
    input,
    select,
    textarea {
      font: inherit;
    }
    .app-shell {
      width: max(1081px, 100vw);
      height: 100vh;
      display: flex;
      flex-direction: column;
      min-height: 0;
    }
    .eyebrow {
      margin: 0;
      color: var(--muted);
      font: var(--type-overline-weight) var(--type-overline-size)/1.2 var(--font-ui);
      letter-spacing: var(--tracking-caps);
      text-transform: uppercase;
    }
    h2, h3 {
      margin: 0;
      color: var(--text-primary);
    }
    h2 {
      font-family: var(--font-sans);
      font-size: var(--type-heading-size);
      font-weight: var(--type-heading-weight);
      letter-spacing: 0;
      line-height: 1.2;
    }
    h3 {
      font-family: var(--font-sans);
      font-size: var(--type-heading-size);
      font-weight: var(--type-heading-weight);
      letter-spacing: 0;
      line-height: 1.2;
    }
    .theme-warning {
      margin: 0;
      padding: 14px 16px;
      border: 0;
      border-bottom: 1px solid var(--alert);
      background: var(--alert-soft);
      color: var(--text-primary);
    }
    .theme-warning strong {
      display: block;
      margin-bottom: 4px;
      font: var(--type-overline-weight) var(--type-overline-size)/1.2 var(--font-ui);
      letter-spacing: var(--tracking-caps);
      text-transform: uppercase;
    }
    .workspace {
      background: var(--paper);
      flex: 1 1 auto;
      min-height: 0;
      overflow: hidden;
      opacity: 0;
      transform: translateY(12px);
      transition: opacity var(--dur-base) var(--ease-standard), transform var(--dur-base) var(--ease-standard);
    }
    .workspace.is-ready {
      opacity: 1;
      transform: translateY(0);
    }
    .review-shell {
      --history-rail-collapsed-width: 40px;
      --history-rail-expanded-width: 320px;
      --history-rail-width: var(--history-rail-collapsed-width);
      display: grid;
      grid-template-columns:
        minmax(280px, 340px)
        minmax(0, 1fr)
        minmax(var(--history-rail-width), var(--history-rail-width));
      height: 100%;
      min-height: 0;
      transition: grid-template-columns var(--dur-base) var(--ease-standard);
    }
    .review-shell.is-history-expanded {
      --history-rail-width: var(--history-rail-expanded-width);
    }
    .inbox-rail {
      border-right: 1px solid var(--line);
      background: linear-gradient(180deg, var(--paper-strong), var(--paper-soft));
      display: grid;
      grid-template-rows: auto 1fr;
      min-height: 0;
    }
    .rail-header {
      position: sticky;
      top: 0;
      z-index: 1;
      padding: 14px 16px 10px;
      border-bottom: 1px solid var(--line);
      display: grid;
      gap: 8px;
      background: linear-gradient(180deg, var(--paper-strong), var(--paper-soft));
    }
    .rail-controls {
      display: grid;
      gap: 10px;
    }
    .rail-select-wrap {
      display: grid;
      gap: 6px;
    }
    .control-trigger {
      position: relative;
      display: inline-flex;
      align-items: center;
      min-height: 34px;
      padding: 0 12px;
      border-radius: var(--radius-pill);
      border: 1px solid var(--line);
      background: var(--paper-strong);
      color: var(--text-primary);
      box-shadow: var(--shadow-panel);
      font: var(--type-body-weight) var(--type-body-size)/1.2 var(--font-ui);
      transition:
        background-color var(--dur-fast) var(--ease-standard),
        border-color var(--dur-fast) var(--ease-standard),
        color var(--dur-fast) var(--ease-standard),
        box-shadow var(--dur-fast) var(--ease-standard);
    }
    .control-trigger:hover {
      border-color: var(--line-strong);
      background: var(--paper);
    }
    .control-trigger:focus-within {
      outline: 2px solid var(--signal);
      outline-offset: 2px;
    }
    .control-trigger::after {
      content: "▾";
      position: absolute;
      right: 12px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--muted);
      font-size: var(--type-overline-size);
      line-height: 1;
      pointer-events: none;
    }
    .rail-select-shell {
      width: 100%;
    }
    .rail-select {
      flex: 1 1 auto;
      min-width: 0;
      min-height: 32px;
      border: 0;
      background: transparent;
      color: inherit;
      padding: 0 18px 0 0;
      appearance: none;
      -webkit-appearance: none;
      font: inherit;
      cursor: pointer;
    }
    .rail-filter-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .rail-filter {
      border: 1px solid var(--line);
      border-radius: var(--radius-pill);
      background: var(--paper-strong);
      color: var(--muted);
      min-height: 28px;
      padding: 0 12px;
      cursor: pointer;
      font: var(--type-body-weight) var(--type-body-size)/1.2 var(--font-ui);
      transition:
        background-color var(--dur-fast) var(--ease-standard),
        border-color var(--dur-fast) var(--ease-standard),
        color var(--dur-fast) var(--ease-standard);
    }
    .rail-filter.is-active {
      border-color: var(--signal);
      background: var(--signal-soft);
      color: var(--text-primary);
    }
    .rail-select:focus {
      outline: none;
    }
    .rail-filter:focus {
      outline: 2px solid var(--signal);
      outline-offset: 2px;
    }
    .chip {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-height: 28px;
      padding: 0 10px;
      border-radius: var(--radius-pill);
      border: 1px solid var(--line);
      background: var(--paper-strong);
      color: var(--muted);
      font: var(--type-body-weight) var(--type-body-size)/1.2 var(--font-ui);
    }
    .chip.ok {
      border-color: var(--line-strong);
      background: var(--paper-strong);
      color: var(--text-primary);
    }
    .chip.warn {
      border-color: var(--signal);
      background: var(--signal-soft);
      color: var(--text-primary);
    }
    .chip.danger {
      border-color: var(--alert);
      background: var(--alert-soft);
      color: var(--alert);
    }
    .rail-list {
      overflow: auto;
      min-height: 0;
      padding: 2px 0;
    }
    .rail-empty {
      padding: 18px 16px;
    }
    .state-panel {
      display: grid;
      gap: 8px;
      align-content: start;
      max-width: 42rem;
      padding: 18px;
      border: 1px solid var(--line);
      border-radius: var(--radius-md);
      background: var(--paper-strong);
      color: var(--text-primary);
      box-shadow: var(--shadow-panel);
    }
    .state-panel p {
      margin: 0;
    }
    .phase-group {
      display: grid;
    }
    .phase-label {
      display: block;
      padding: 10px 16px 9px;
      border-bottom: 1px solid var(--line);
      background: var(--paper-strong);
      color: var(--muted);
      font: var(--type-overline-weight) var(--type-overline-size)/1.2 var(--font-ui);
      letter-spacing: var(--tracking-caps);
      text-transform: uppercase;
    }
    .phase-group + .phase-group .phase-label {
      border-top: 1px solid var(--line);
    }
    .message-link {
      width: 100%;
      border: 0;
      border-bottom: 1px solid var(--line);
      background: transparent;
      padding: 10px 16px 11px;
      text-align: left;
      cursor: pointer;
      display: grid;
      gap: 6px;
      transition:
        background-color var(--dur-fast) var(--ease-standard),
        transform var(--dur-fast) var(--ease-standard);
    }
    .message-link:hover {
      background: var(--paper-strong);
      transform: translateX(2px);
    }
    .message-link.is-selected {
      background: var(--paper);
      box-shadow: inset 3px 0 0 0 var(--signal);
    }
    .message-line {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: start;
    }
    .message-title {
      font-size: var(--type-heading-size);
      font-weight: var(--type-heading-weight);
      line-height: 1.2;
      color: var(--text-primary);
    }
    .message-subline,
    .meta,
    .meta-value,
    .history-meta {
      color: var(--muted);
      font-size: var(--type-body-size);
    }
    .message-tags,
    .detail-tags,
    .support-links,
    .docs-list,
    .metrics-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 0;
      padding: 0;
      list-style: none;
    }
    .read-dot {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: var(--line);
      margin-top: 4px;
      flex: 0 0 auto;
    }
    .read-dot.is-unread {
      background: var(--signal);
    }
    .message-pane {
      padding: 18px calc(var(--space-card) + 2px) calc(var(--space-card) + 4px);
      display: grid;
      gap: 18px;
      align-content: start;
      min-height: 0;
      overflow: auto;
    }
    .detail-main,
    .history-rail,
    .history-rail-list,
    .history-rail-expanded,
    .history-list,
    .history-row,
    .history-topline,
    .history-title-block,
    .history-meta-grid,
    .history-row .support-links,
    .history-row .support-links a,
    .history-row .detail-tags,
    .history-row .chip {
      min-width: 0;
    }
    .detail-main {
      display: grid;
      gap: 18px;
      align-content: start;
    }
    .history-rail {
      display: grid;
      grid-template-rows: 1fr;
      min-width: 0;
      min-height: 0;
      overflow: hidden;
      border-left: 1px solid var(--line);
      background: linear-gradient(180deg, var(--paper-strong), var(--paper-soft));
      position: relative;
    }
    .history-rail-collapsed,
    .history-rail-expanded {
      grid-area: 1 / 1;
      min-height: 0;
    }
    .history-rail-collapsed {
      padding: 4px;
      opacity: 1;
      transition: opacity var(--dur-fast) var(--ease-standard);
    }
    .review-shell.is-history-expanded .history-rail-collapsed {
      opacity: 0;
      pointer-events: none;
    }
    .history-rail-collapsed-toggle {
      width: 100%;
      height: 100%;
      border: 0;
      background: transparent;
      color: var(--text-primary);
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 12px;
      padding: 8px 0;
      transition: background-color var(--dur-fast) var(--ease-standard);
    }
    .history-rail-collapsed-toggle:hover {
      background: var(--paper-strong);
    }
    .history-rail-collapsed-toggle:focus-visible,
    .history-rail-collapse:focus-visible {
      outline: 2px solid var(--signal);
      outline-offset: -2px;
    }
    .history-rail-collapsed-label {
      color: var(--muted);
      font: var(--type-overline-weight) var(--type-overline-size)/1.2 var(--font-ui);
      letter-spacing: var(--tracking-caps);
      text-transform: uppercase;
      writing-mode: vertical-rl;
      transform: rotate(180deg);
    }
    .history-rail-collapsed-count {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 24px;
      min-height: 24px;
      padding: 0 6px;
      border-radius: var(--radius-pill);
      border: 1px solid var(--line);
      background: var(--paper-strong);
      color: var(--text-primary);
      font: var(--type-body-weight) var(--type-body-size)/1 var(--font-ui);
    }
    .history-rail-expanded {
      display: grid;
      grid-template-rows: auto 1fr;
      overflow: hidden;
      opacity: 0;
      transform: translateX(12px);
      pointer-events: none;
      transition:
        opacity var(--dur-fast) var(--ease-standard),
        transform var(--dur-base) var(--ease-standard);
    }
    .review-shell.is-history-expanded .history-rail-expanded {
      opacity: 1;
      transform: translateX(0);
      pointer-events: auto;
      transition-delay: 70ms;
    }
    .history-rail-header {
      position: sticky;
      top: 0;
      z-index: 1;
      padding: 14px 16px 10px;
      border-bottom: 1px solid var(--line);
      display: grid;
      gap: 10px;
      background: linear-gradient(180deg, var(--paper-strong), var(--paper-soft));
    }
    .history-rail-header-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .history-rail-header-copy {
      display: flex;
      align-items: center;
      gap: 8px;
      min-width: 0;
      flex-wrap: wrap;
    }
    .history-rail-body {
      min-height: 0;
      overflow-x: hidden;
      overflow-y: auto;
    }
    .history-rail-list {
      display: grid;
      gap: 0;
    }
    .history-rail-collapse {
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      padding: 0 10px;
      border-radius: var(--radius-pill);
      border: 1px solid var(--line);
      background: var(--paper-strong);
      color: var(--muted);
      cursor: pointer;
      font: var(--type-body-weight) var(--type-body-size)/1.2 var(--font-ui);
      transition:
        background-color var(--dur-fast) var(--ease-standard),
        border-color var(--dur-fast) var(--ease-standard),
        color var(--dur-fast) var(--ease-standard);
    }
    .history-rail-collapse:hover {
      border-color: var(--line-strong);
      color: var(--text-primary);
    }
    .detail-summary-bar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-top: 12px;
    }
    .detail-summary-bar .meta-actions {
      margin-left: auto;
    }
    .summary-pill-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .summary-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-height: 30px;
      padding: 0 10px;
      border-radius: var(--radius-pill);
      border: 1px solid var(--line);
      background: var(--paper-strong);
      color: var(--text-primary);
      font: var(--type-body-weight) var(--type-body-size)/1.2 var(--font-ui);
    }
    .summary-pill-label {
      color: var(--muted);
      font: var(--type-overline-weight) var(--type-overline-size)/1.2 var(--font-ui);
      letter-spacing: var(--tracking-caps);
      text-transform: uppercase;
    }
    .section-block {
      border-top: 1px solid var(--line);
      padding-top: 16px;
    }
    .section-block:first-child {
      border-top: 0;
      padding-top: 0;
    }
    .message-meta-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
    }
    .detail-meta-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr)) auto;
      gap: 12px;
      align-items: end;
    }
    .meta-label {
      display: block;
      margin-bottom: 4px;
      color: var(--muted);
      font: var(--type-overline-weight) var(--type-overline-size)/1.2 var(--font-ui);
      letter-spacing: var(--tracking-caps);
      text-transform: uppercase;
    }
    .metrics-inline {
      margin-top: 10px;
    }
    .disclosure-block {
      border: 1px solid var(--line);
      border-radius: var(--radius-md);
      background: var(--paper-strong);
      overflow: hidden;
    }
    .disclosure-summary {
      list-style: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      min-height: 44px;
      padding: 0 14px;
      color: var(--text-primary);
      font: var(--type-body-weight) var(--type-body-size)/1.2 var(--font-ui);
    }
    .disclosure-summary::-webkit-details-marker {
      display: none;
    }
    .disclosure-summary::after {
      content: "+";
      color: var(--muted);
      font-size: var(--type-body-size);
      line-height: 1;
    }
    .disclosure-block[open] .disclosure-summary::after {
      content: "−";
    }
    .disclosure-body {
      display: grid;
      gap: 14px;
      padding: 0 14px 14px;
    }
    .guardrail-stack {
      display: grid;
      gap: 14px;
    }
    .doc-tabs-wrap {
      display: grid;
      gap: 12px;
    }
    .doc-tablist {
      display: flex;
      gap: 10px;
      flex-wrap: nowrap;
      overflow-x: auto;
      padding-bottom: 2px;
      scrollbar-width: thin;
    }
    .doc-tab {
      flex: 0 0 auto;
      display: inline-flex;
      align-items: center;
      min-height: 34px;
      padding: 0 14px;
      border-radius: var(--radius-pill);
      border: 1px solid var(--line);
      background: var(--paper-strong);
      color: var(--muted);
      cursor: pointer;
      white-space: nowrap;
      transition:
        transform var(--dur-fast) var(--ease-standard),
        background-color var(--dur-fast) var(--ease-standard),
        border-color var(--dur-fast) var(--ease-standard),
        color var(--dur-fast) var(--ease-standard);
    }
    .doc-tab:hover {
      transform: translateY(-1px);
      border-color: var(--line-strong);
      color: var(--text-primary);
    }
    .doc-tab.is-active {
      border-color: var(--signal);
      background: var(--signal-soft);
      color: var(--text-primary);
    }
    .doc-tab[disabled] {
      cursor: default;
      opacity: 0.55;
      transform: none;
      color: var(--muted);
    }
    .doc-tab:focus-visible {
      outline: 2px solid var(--signal);
      outline-offset: 2px;
    }
    .preview-stage {
      position: relative;
      min-height: 360px;
      border-radius: var(--radius-lg);
      overflow: hidden;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0)),
        var(--stage-bg);
      box-shadow: inset 0 0 0 1px var(--stage-line);
    }
    .preview-stage::after {
      content: "";
      position: absolute;
      inset: 0;
      pointer-events: none;
      background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0) 24%, rgba(0,0,0,0.16) 100%);
    }
    .preview-stage img,
    .preview-stage video,
    .preview-stage iframe,
    .preview-stage .preview-fallback {
      width: 100%;
      height: 100%;
      border: 0;
      display: block;
      min-height: 360px;
      background: transparent;
    }
    .preview-stage img,
    .preview-stage video {
      object-fit: cover;
    }
    .preview-stage .preview-audio {
      width: 100%;
      min-height: 360px;
      display: grid;
      place-items: center;
      padding: 24px;
      position: relative;
      z-index: 1;
    }
    .preview-stage .preview-audio audio {
      width: min(100%, 560px);
      max-width: 100%;
      display: block;
    }
    .preview-fallback {
      display: grid;
      place-items: center;
      color: var(--text-secondary-dark);
      padding: 24px;
    }
    .menu-panel {
      width: min(360px, calc(100vw - 40px));
      padding: 14px;
      border-radius: var(--radius-md);
      background: var(--paper-strong);
      border: 1px solid var(--line);
      box-shadow: var(--shadow-panel);
      display: grid;
      gap: 14px;
      max-height: min(78vh, 720px);
      overflow-x: hidden;
      overflow-y: auto;
    }
    .menu-panel > * {
      min-width: 0;
    }
    .menu-panel label {
      display: block;
      color: var(--muted);
      font: var(--type-overline-weight) var(--type-overline-size)/1.2 var(--font-ui);
      letter-spacing: var(--tracking-caps);
      text-transform: uppercase;
      margin-bottom: 6px;
    }
    .menu-panel input,
    .menu-panel textarea {
      width: 100%;
      min-width: 0;
      max-width: 100%;
      border: 1px solid var(--line);
      border-radius: var(--radius-md);
      padding: 9px 11px;
      background: var(--paper);
      color: var(--text-primary);
    }
    .menu-panel textarea {
      min-height: 96px;
      resize: vertical;
    }
    .menu-button-row {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      width: 100%;
      min-width: 0;
    }
    button.action {
      border: 1px solid var(--line);
      border-radius: var(--radius-pill);
      padding: 11px 16px;
      min-width: 0;
      max-width: 100%;
      cursor: pointer;
      transition:
        transform var(--dur-fast) var(--ease-standard),
      background-color var(--dur-fast) var(--ease-standard),
        border-color var(--dur-fast) var(--ease-standard),
        color var(--dur-fast) var(--ease-standard);
    }
    button.action:hover {
      transform: translateY(-1px);
    }
    .approve {
      background: var(--ink);
      border-color: var(--ink);
      color: var(--text-inverse);
    }
    .reject {
      background: var(--alert);
      border-color: var(--alert);
      color: var(--text-inverse);
    }
    .unapprove {
      background: var(--paper-strong);
      border-color: var(--line-strong);
      color: var(--text-primary);
    }
    .unreject {
      background: var(--paper);
      border-color: var(--line-strong);
      color: var(--text-primary);
    }
    button.action[aria-disabled="true"] {
      background: var(--paper-strong);
      border-color: var(--line);
      color: var(--muted);
      cursor: not-allowed;
      opacity: 0.72;
    }
    button.action[aria-disabled="true"]:hover {
      transform: none;
    }
    .message-toolbar {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: end;
      flex-wrap: wrap;
    }
    .meta-actions {
      position: relative;
      justify-self: end;
    }
    .menu-trigger {
      padding-right: 30px;
      cursor: pointer;
    }
    .action-menu {
      position: relative;
    }
    .action-menu-panel {
      position: absolute;
      top: calc(100% + 8px);
      right: 0;
      z-index: 3;
      display: none;
    }
    .action-menu.is-open .action-menu-panel {
      display: block;
    }
    .menu-links,
    .menu-form-fields {
      display: grid;
      gap: 10px;
      width: 100%;
      min-width: 0;
    }
    .menu-links > *,
    .menu-form-fields > * {
      min-width: 0;
    }
    .menu-links .support-links,
    .menu-links .docs-list,
    .menu-form-fields .menu-button-row {
      width: 100%;
      min-width: 0;
    }
    .menu-section-label {
      color: var(--muted);
      font: var(--type-overline-weight) var(--type-overline-size)/1.2 var(--font-ui);
      letter-spacing: var(--tracking-caps);
      text-transform: uppercase;
    }
    .menu-empty {
      color: var(--muted);
      font-size: var(--type-body-size);
    }
    .detail-note {
      margin-top: 14px;
      padding: 14px 16px;
      border-radius: var(--radius-md);
      border: 1px solid var(--line);
      background: var(--paper-strong);
      color: var(--muted);
      font-size: var(--type-body-size);
    }
    .support-links a,
    .docs-list a {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-height: 30px;
      padding: 0 10px;
      border-radius: var(--radius-pill);
      background: var(--paper-strong);
      border: 1px solid var(--line);
      color: var(--muted);
      font: var(--type-body-weight) var(--type-body-size)/1.2 var(--font-ui);
      max-width: 100%;
    }
    .menu-links a {
      min-width: 0;
      white-space: normal;
      overflow-wrap: anywhere;
    }
    .metrics-list li {
      display: inline-flex;
      align-items: center;
      min-height: 30px;
      padding: 0 10px;
      border-radius: var(--radius-pill);
      background: var(--paper-soft);
      border: 1px solid var(--line);
      color: var(--muted);
      font: var(--type-body-weight) var(--type-body-size)/1.2 var(--font-ui);
    }
    .history-empty {
      color: var(--muted);
      font-size: var(--type-body-size);
      padding: 18px 16px;
    }
    .history-row {
      padding: 14px 16px 16px;
      display: grid;
      gap: 10px;
      border-top: 1px solid var(--line);
    }
    .history-row:first-child {
      border-top: 0;
    }
    .history-topline {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: start;
      flex-wrap: wrap;
    }
    .history-title-block {
      min-width: 0;
      flex: 1 1 180px;
    }
    .history-title-block h3,
    .history-row .history-notes,
    .history-row .meta-value {
      overflow-wrap: anywhere;
      word-break: break-word;
    }
    .history-row .detail-tags {
      flex: 0 1 auto;
    }
    .history-row .support-links a {
      white-space: normal;
      overflow-wrap: anywhere;
      word-break: break-word;
    }
    .history-meta-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }
    .history-meta-grid > div {
      min-width: 0;
    }
    .history-notes {
      color: var(--text-primary);
      font-size: var(--type-body-size);
      line-height: 1.5;
    }
    .guardrail-list {
      margin: 0;
      padding-left: 18px;
      color: var(--muted);
      display: grid;
      gap: 6px;
    }
    .empty {
      color: var(--muted);
    }
    .error {
      color: var(--alert);
      white-space: pre-wrap;
      font-size: var(--type-body-size);
    }
    @media (min-width: 1081px) and (max-width: 1180px) {
      .detail-summary-bar .meta-actions {
        margin-left: 0;
      }
      .message-meta-grid,
      .detail-meta-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .meta-actions {
        justify-self: start;
        grid-column: 1 / -1;
      }
      .history-topline {
        flex-direction: column;
      }
      .action-menu-panel {
        left: 0;
        right: auto;
      }
    }
  </style>
</head>
<body>
  <main class="app-shell">
    __WARNING_BANNER__
    <section id="app" class="workspace" aria-live="polite"></section>
  </main>
  <script>
    const app = document.getElementById("app");
    const DEV_RELOAD_ENABLED = __DEV_RELOAD_ENABLED__;
    const HISTORY_RAIL_PANEL_ID = "history-rail-panel";
    let currentServerInstanceId = __SERVER_INSTANCE_ID__;
    let currentInbox = null;
    let currentMessageId = "";
    let currentDetail = null;
    let shellRoot = null;
    let railRoot = null;
    let detailRoot = null;
    let historyRoot = null;
    let historyRailExpanded = false;
    const visualResearchTabState = {};
    const VISUAL_RESEARCH_DOC_LABELS = [
      "Contact sheet",
      "Act breakdown",
      "Reference notes",
      "Sources",
      "Assembly notes",
    ];
    const PHASE_GATE_ORDER = [
      { gateType: "visual_research", label: "Visual research" },
      { gateType: "audio", label: "Audio" },
      { gateType: "scene_still", label: "Scene still" },
      { gateType: "motion_source", label: "Motion source" },
      { gateType: "packaging_still", label: "Packaging still" },
      { gateType: "motion_asset", label: "Motion asset" },
    ];
    const STATUS_FILTER_OPTIONS = [
      { key: "all", label: "All" },
      { key: "pending", label: "Pending" },
      { key: "rejected", label: "Rejected" },
      { key: "approved", label: "Approved" },
    ];
    const STATUS_FILTER_VALUES = new Set(STATUS_FILTER_OPTIONS.map((option) => option.key));
    const PENDING_FILTER_STATUSES = new Set(["pending", "unapproved"]);
    const APPROVED_FILTER_STATUSES = new Set(["approved", "approved_for_motion"]);
    let currentEpisodeFilter = "all";
    let currentStatusFilter = "all";

    function assetUrl(path, version = "") {
      const params = new URLSearchParams({ path: String(path ?? "") });
      if (version) {
        params.set("v", String(version));
      }
      return "/api/review/assets?" + params.toString();
    }

    function escapeHtml(value) {
      return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    function labelize(value) {
      return String(value ?? "").replaceAll("_", " ");
    }

    function fileLabel(path) {
      if (!path) {
        return "";
      }
      const bits = String(path).split("/");
      return bits[bits.length - 1] || path;
    }

    function domId(value) {
      return String(value ?? "").replace(/[^a-zA-Z0-9_-]+/g, "-");
    }

    const TIMESTAMP_FORMATTER = typeof Intl !== "undefined" && typeof Intl.DateTimeFormat === "function"
      ? new Intl.DateTimeFormat(undefined, {
          dateStyle: "medium",
          timeStyle: "short",
          hourCycle: "h23",
        })
      : null;

    function formatTimestamp(value) {
      if (!value) {
        return "";
      }
      const stamp = new Date(value);
      if (Number.isNaN(stamp.getTime())) {
        return value;
      }
      if (TIMESTAMP_FORMATTER) {
        return TIMESTAMP_FORMATTER.format(stamp);
      }
      return stamp.toLocaleString(undefined, { hour12: false });
    }

    function toneForStatus(status) {
      const normalized = String(status || "").toLowerCase();
      if (["approved", "done", "approved_for_motion", "current"].includes(normalized)) {
        return "ok";
      }
      if (["rejected", "blocked"].includes(normalized)) {
        return "danger";
      }
      if (["review", "pending", "todo", "in_progress", "unapproved", "provisional", "not_ready", "out_of_sync", "unknown"].includes(normalized)) {
        return "warn";
      }
      return "";
    }

    function decisionStatus(message) {
      return String((message && (message.decision_status || message.status)) || "").trim();
    }

    function decisionLabel(message) {
      return String((message && (message.decision_label || message.status)) || "").trim();
    }

    function laneStatus(message) {
      return String((message && message.lane_status) || "").trim();
    }

    function laneLabel(message) {
      return String((message && (message.lane_label || message.lane_status)) || "").trim();
    }

    function freshnessStatus(message) {
      return String((message && message.freshness_status) || "").trim();
    }

    function freshnessLabel(message) {
      return String((message && (message.freshness_label || message.freshness_status)) || "").trim();
    }

    function packageSyncStatus(message) {
      return String((message && message.package_sync_status) || "").trim();
    }

    function packageSyncLabel(message) {
      return String((message && (message.package_sync_label || message.package_sync_status)) || "").trim();
    }

    function chipMarkup(label, status) {
      if (!label) {
        return "";
      }
      return `<span class="chip ${toneForStatus(status)}">${escapeHtml(label)}</span>`;
    }

    async function fetchJson(url, init) {
      const response = await fetch(url, init);
      const body = await response.json().catch(() => ({ error: "Invalid server response." }));
      if (!response.ok) {
        throw new Error(body.error || "Request failed.");
      }
      return body;
    }

    async function checkForServerRestart() {
      if (!DEV_RELOAD_ENABLED) {
        return;
      }
      try {
        const state = await fetchJson("/api/review/dev-state", { cache: "no-store" });
        if (!state.server_instance_id || state.server_instance_id === currentServerInstanceId) {
          return;
        }
        currentServerInstanceId = state.server_instance_id;
        window.location.reload();
      } catch (_error) {
        // Ignore brief fetch failures while the autoreloader swaps processes.
      }
    }

    function selectedMessageIdFromUrl() {
      const params = new URLSearchParams(window.location.search);
      return params.get("message") || "";
    }

    function normalizeStatusFilter(value) {
      const normalized = String(value || "").trim().toLowerCase();
      return STATUS_FILTER_VALUES.has(normalized) ? normalized : "all";
    }

    function selectedEpisodeIdFromUrl() {
      const params = new URLSearchParams(window.location.search);
      return params.get("episode") || "all";
    }

    function selectedStatusFilterFromUrl() {
      const params = new URLSearchParams(window.location.search);
      return normalizeStatusFilter(params.get("status") || "all");
    }

    function syncViewState(messageId, episodeId, statusFilter, push) {
      const resolvedMessageId = String(messageId || "").trim();
      const resolvedEpisodeId = String(episodeId || "all").trim() || "all";
      const resolvedStatusFilter = normalizeStatusFilter(statusFilter);
      const url = new URL(window.location.href);
      if (resolvedMessageId) {
        url.searchParams.set("message", resolvedMessageId);
      } else {
        url.searchParams.delete("message");
      }
      if (resolvedEpisodeId !== "all") {
        url.searchParams.set("episode", resolvedEpisodeId);
      } else {
        url.searchParams.delete("episode");
      }
      if (resolvedStatusFilter !== "all") {
        url.searchParams.set("status", resolvedStatusFilter);
      } else {
        url.searchParams.delete("status");
      }
      window.history[push ? "pushState" : "replaceState"]({}, "", url);
      currentMessageId = resolvedMessageId;
      currentEpisodeFilter = resolvedEpisodeId;
      currentStatusFilter = resolvedStatusFilter;
    }

    function setWorkspace() {
      if (shellRoot && railRoot && detailRoot && historyRoot) {
        return;
      }
      app.classList.remove("is-ready");
      app.innerHTML = `
        <div class="review-shell" data-shell-root>
          <aside class="inbox-rail" data-rail-root></aside>
          <section class="message-pane" data-detail-root></section>
          <aside class="history-rail" data-history-root></aside>
        </div>
      `;
      shellRoot = app.querySelector("[data-shell-root]");
      railRoot = app.querySelector("[data-rail-root]");
      detailRoot = app.querySelector("[data-detail-root]");
      historyRoot = app.querySelector("[data-history-root]");
      window.requestAnimationFrame(() => {
        syncHistoryRailState();
        app.classList.add("is-ready");
      });
    }

    function statePanelMarkup(title, message, role = "status") {
      return `
        <div class="state-panel" role="${escapeHtml(role)}">
          <h2>${escapeHtml(title)}</h2>
          <p class="empty">${escapeHtml(message)}</p>
        </div>
      `;
    }

    function renderRailStatus(message) {
      setWorkspace();
      railRoot.innerHTML = `
        <div class="rail-header">
          <p class="eyebrow">Review desk</p>
          <h2>Inbox</h2>
        </div>
        <div class="rail-list">
          <div class="rail-empty empty">${escapeHtml(message)}</div>
        </div>
      `;
    }

    function renderLoadingState() {
      renderRailStatus("Loading review inbox...");
      detailRoot.innerHTML = statePanelMarkup(
        "Loading review inbox",
        "Review gates and approval items will appear here once the inbox loads.",
      );
      renderHistory(null);
    }

    function renderLoadError(error) {
      const message = error && error.message ? error.message : "Unable to load the review inbox.";
      renderRailStatus("Review inbox failed to load.");
      detailRoot.innerHTML = statePanelMarkup(
        "Review inbox failed to load",
        message,
        "alert",
      );
      renderHistory(null);
    }

    function captureRailScrollState() {
      const railList = railRoot ? railRoot.querySelector(".rail-list") : null;
      if (!railList) {
        return null;
      }
      return { scrollTop: railList.scrollTop };
    }

    function restoreRailScrollState(state) {
      if (!state) {
        return;
      }
      const railList = railRoot ? railRoot.querySelector(".rail-list") : null;
      if (railList) {
        railList.scrollTop = state.scrollTop;
      }
    }

    function previewMarkup(preview, version = "") {
      if (!preview || !preview.preview_path) {
        return '<div class="preview-fallback empty">No preview</div>';
      }
      const label = preview.label || "Preview";
      if (preview.preview_type === "image") {
        return `<img alt="${escapeHtml(label)}" src="${assetUrl(preview.preview_path, version)}">`;
      }
      if (preview.preview_type === "video") {
        return `<video controls preload="metadata" src="${assetUrl(preview.preview_path, version)}"></video>`;
      }
      if (preview.preview_type === "audio") {
        return `<div class="preview-audio"><audio controls preload="metadata" src="${assetUrl(preview.preview_path, version)}" aria-label="${escapeHtml(label)}"></audio></div>`;
      }
      if (preview.preview_type === "markdown") {
        return `<iframe title="${escapeHtml(label)}" src="${assetUrl(preview.preview_path, version)}"></iframe>`;
      }
      if (preview.preview_type === "pdf") {
        return `<iframe title="${escapeHtml(label)}" src="${assetUrl(preview.preview_path, version)}"></iframe>`;
      }
      return `<div class="preview-fallback"><a href="${assetUrl(preview.preview_path, version)}" target="_blank" rel="noreferrer">${escapeHtml(fileLabel(preview.preview_path))}</a></div>`;
    }

    function metricsMarkup(message) {
      if (!message.metrics) {
        return "";
      }
      const sourceInventory = message.source_inventory || {};
      const unresolvedSources = Array.isArray(sourceInventory.unresolved_source_ids)
        ? sourceInventory.unresolved_source_ids.filter(Boolean)
        : [];
      const blockedSources = Array.isArray(sourceInventory.blocked_source_ids)
        ? sourceInventory.blocked_source_ids.filter(Boolean)
        : [];
      const unresolvedMarkup = unresolvedSources.length
        ? `<li>Needs cleanup ${escapeHtml(unresolvedSources.join(", "))}</li>`
        : "";
      const blockedMarkup = blockedSources.length
        ? `<li>Blocked ${escapeHtml(blockedSources.join(", "))}</li>`
        : "";
      return `
        <ul class="metrics-list">
          <li>Acts ${escapeHtml(message.metrics.act_count)}</li>
          <li>Beats ${escapeHtml(message.metrics.beat_count_total)}</li>
          <li>Motion ${escapeHtml(message.metrics.planned_motion_total)}/${escapeHtml(message.metrics.required_motion_total)}</li>
          <li>Sources ${escapeHtml(message.metrics.ready_source_total || 0)}/${escapeHtml(message.metrics.approved_source_total || 0)}</li>
          <li>Cleaned ${escapeHtml(message.metrics.cleaned_source_total || 0)}</li>
          ${unresolvedMarkup}
          ${blockedMarkup}
        </ul>
      `;
    }

    function docsMarkup(message) {
      if (!message.docs || !message.docs.length) {
        return "";
      }
      return `
        <ul class="docs-list">
          ${message.docs.filter((doc) => doc.path).map((doc) => `
            <li><a href="${assetUrl(doc.path, message.updated_at)}" target="_blank" rel="noreferrer">${escapeHtml(doc.label)}</a></li>
          `).join("")}
        </ul>
      `;
    }

    function reviewContextMarkup(message) {
      if (!message.review_notes) {
        return "";
      }
      return `
        <div>
          <p class="eyebrow">Reviewer Notes</p>
          <div class="history-notes">${escapeHtml(message.review_notes)}</div>
        </div>
      `;
    }

    function episodeGuardrailsMarkup(message) {
      const guardrails = message && message.episode_guardrails ? message.episode_guardrails : {};
      const signalObject = String(guardrails.signal_object || "").trim();
      const bannedMotifs = Array.isArray(guardrails.banned_motifs) ? guardrails.banned_motifs.filter(Boolean) : [];
      if (!signalObject && !bannedMotifs.length) {
        return "";
      }
      return `
        <div class="guardrail-stack">
          <div>
            <p class="eyebrow">Signal Object</p>
            <div class="message-meta-grid">
              ${metaField("Signal Object", signalObject || "-")}
            </div>
          </div>
          ${bannedMotifs.length ? `
            <div>
              <p class="eyebrow">Banned Motifs</p>
              <ul class="guardrail-list">
                ${bannedMotifs.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
              </ul>
            </div>
          ` : ""}
        </div>
      `;
    }

    function supportLinksMarkup(message) {
      const links = [];
      if (message.proof_path && message.gate_type !== "visual_research") {
        links.push(`<a href="${assetUrl(message.proof_path, message.updated_at)}" target="_blank" rel="noreferrer">Proof ${escapeHtml(fileLabel(message.proof_path))}</a>`);
      }
      if (message.proof_manifest_path) {
        links.push(`<a href="${assetUrl(message.proof_manifest_path, message.updated_at)}" target="_blank" rel="noreferrer">Manifest ${escapeHtml(fileLabel(message.proof_manifest_path))}</a>`);
      }
      if (message.audio_source_manifest_path) {
        links.push(`<a href="${assetUrl(message.audio_source_manifest_path, message.updated_at)}" target="_blank" rel="noreferrer">Source ${escapeHtml(fileLabel(message.audio_source_manifest_path))}</a>`);
      }
      if (message.audio_package_metadata_path) {
        links.push(`<a href="${assetUrl(message.audio_package_metadata_path, message.updated_at)}" target="_blank" rel="noreferrer">Package ${escapeHtml(fileLabel(message.audio_package_metadata_path))}</a>`);
      }
      if (message.selected_asset) {
        links.push(`<a href="${assetUrl(message.selected_asset, message.updated_at)}" target="_blank" rel="noreferrer">Selected ${escapeHtml(fileLabel(message.selected_asset))}</a>`);
      }
      if (message.output_path) {
        links.push(`<a href="${assetUrl(message.output_path, message.updated_at)}" target="_blank" rel="noreferrer">Output ${escapeHtml(fileLabel(message.output_path))}</a>`);
      }
      if (!links.length) {
        return "";
      }
      return `<div class="support-links">${links.join("")}</div>`;
    }

    function actionMenuMarkup(message) {
      const actions = message.actions || {};
      const blockedActions = message.blocked_actions || {};
      const blockedReason = message.blocked_reason
        ? `<div class="menu-empty">${escapeHtml(message.blocked_reason)}</div>`
        : "";
      const approveButton = actions.approve
        ? '<button class="action approve" type="button">Approve</button>'
        : blockedActions.approve
          ? `<button class="action approve" type="button" aria-disabled="true" title="${escapeHtml(blockedActions.approve)}">Approve</button>`
          : "";
      const hasActions = Boolean(approveButton || actions.reject || actions.unapprove || actions.unreject);
      const docs = message.gate_type === "visual_research" ? "" : docsMarkup(message);
      const links = supportLinksMarkup(message);
      const hasPanelContent = Boolean(hasActions || blockedReason || docs || links);
      return `
        <div class="action-menu" data-action-menu>
          <button class="menu-trigger control-trigger" type="button" aria-haspopup="true" aria-expanded="false">Actions</button>
          <div class="action-menu-panel" hidden>
            <div class="menu-panel">
              ${hasActions ? `
                <form data-message-id="${escapeHtml(message.message_id)}" data-episode-id="${escapeHtml(message.episode_id)}" data-gate-type="${escapeHtml(message.gate_type)}" data-item-id="${escapeHtml(message.item_id === "visual_research" ? "" : message.item_id || "")}">
                  <div class="menu-form-fields">
                    <div>
                      <label>Reviewer</label>
                      <input type="text" name="reviewer" value="${escapeHtml(message.reviewer || "")}">
                    </div>
                    <div>
                      <label>Notes</label>
                      <textarea name="notes">${escapeHtml(message.review_notes || "")}</textarea>
                    </div>
                    <div class="menu-button-row">
                      ${approveButton}
                      ${actions.reject ? '<button class="action reject" type="button">Reject</button>' : ""}
                      ${actions.unreject ? '<button class="action unreject" type="button">Undo Reject</button>' : ""}
                      ${actions.unapprove ? '<button class="action unapprove" type="button">Unapprove</button>' : ""}
                    </div>
                    <div class="error"></div>
                  </div>
                </form>
              ` : ""}
              ${blockedReason}
              ${docs ? `<div class="menu-links"><span class="menu-section-label">Docs</span>${docs}</div>` : ""}
              ${links ? `<div class="menu-links"><span class="menu-section-label">Files</span>${links}</div>` : ""}
              ${hasPanelContent ? "" : '<div class="menu-empty">No actions</div>'}
            </div>
          </div>
        </div>
      `;
    }

    function orderedVisualResearchDocs(message) {
      const docs = Array.isArray(message.docs) ? message.docs : [];
      const docsByLabel = new Map(docs.map((doc) => [String(doc.label || "").trim(), doc]));
      return VISUAL_RESEARCH_DOC_LABELS.map((label) => {
        const doc = docsByLabel.get(label) || {};
        const path = String(doc.path || "").trim();
        return {
          label,
          path,
          preview_path: path,
          preview_type: String(doc.preview_type || "markdown").trim() || "markdown",
        };
      });
    }

    function firstExistingVisualResearchDoc(docs) {
      return docs.find((doc) => doc.path) || null;
    }

    function resolveVisualResearchPreview(message, previousMessageId) {
      const docs = orderedVisualResearchDocs(message);
      const storedLabel = previousMessageId === message.message_id
        ? String(visualResearchTabState[message.message_id] || "")
        : "";
      let activeDoc = docs.find((doc) => doc.label === storedLabel && doc.path) || null;
      if (!activeDoc) {
        activeDoc = firstExistingVisualResearchDoc(docs);
      }
      if (activeDoc) {
        visualResearchTabState[message.message_id] = activeDoc.label;
      } else {
        delete visualResearchTabState[message.message_id];
      }
      return { docs, activeDoc };
    }

    function visualResearchPreviewMarkup(message, previousMessageId) {
      const previewState = resolveVisualResearchPreview(message, previousMessageId);
      const panelId = "visual-research-panel-" + domId(message.message_id);
      const activeTabId = previewState.activeDoc
        ? "visual-research-tab-" + domId(message.message_id + "-" + previewState.activeDoc.label)
        : "";
      const preview = previewState.activeDoc
        ? previewState.activeDoc
        : { label: message.label, preview_path: "", preview_type: "markdown" };
      return `
        <div class="doc-tabs-wrap">
          <div class="doc-tablist" role="tablist" aria-label="Visual research files">
            ${previewState.docs.map((doc) => {
              const tabId = "visual-research-tab-" + domId(message.message_id + "-" + doc.label);
              const isActive = Boolean(previewState.activeDoc && previewState.activeDoc.label === doc.label);
              return `
                <button
                  class="doc-tab ${isActive ? "is-active" : ""}"
                  type="button"
                  role="tab"
                  id="${escapeHtml(tabId)}"
                  data-doc-label="${escapeHtml(doc.label)}"
                  data-message-id="${escapeHtml(message.message_id)}"
                  aria-selected="${isActive ? "true" : "false"}"
                  aria-controls="${escapeHtml(panelId)}"
                  tabindex="${isActive ? "0" : "-1"}"
                  ${doc.path ? "" : "disabled"}
                >${escapeHtml(doc.label)}</button>
              `;
            }).join("")}
          </div>
          <div class="preview-stage" id="${escapeHtml(panelId)}" role="tabpanel"${activeTabId ? ` aria-labelledby="${escapeHtml(activeTabId)}"` : ' aria-label="Visual research preview"'}>
            ${previewMarkup(preview, message.updated_at)}
          </div>
        </div>
      `;
    }

    function metaField(label, value) {
      return `
        <div>
          <span class="meta-label">${escapeHtml(label)}</span>
          <div class="meta-value">${escapeHtml(value || "-")}</div>
        </div>
      `;
    }

    function summaryPillMarkup(label, value) {
      if (!value) {
        return "";
      }
      return `
        <span class="summary-pill">
          <span class="summary-pill-label">${escapeHtml(label)}</span>
          <span>${escapeHtml(value)}</span>
        </span>
      `;
    }

    function disclosureSectionMarkup(title, body, extraClass) {
      if (!body) {
        return "";
      }
      const sectionClass = extraClass ? " " + extraClass : "";
      return `
        <section class="section-block disclosure-section${sectionClass}">
          <details class="disclosure-block">
            <summary class="disclosure-summary">${escapeHtml(title)}</summary>
            <div class="disclosure-body">
              ${body}
            </div>
          </details>
        </section>
      `;
    }

    function historyCount(message) {
      const items = message && Array.isArray(message.history) ? message.history : [];
      const resolvedCount = Number(message && message.history_count != null ? message.history_count : items.length);
      return Number.isFinite(resolvedCount) ? resolvedCount : items.length;
    }

    function historyCountLabel(count) {
      return `${count} event${count === 1 ? "" : "s"}`;
    }

    function historyToggleLabel(expanded, count) {
      return expanded ? "Collapse history" : `Expand history (${historyCountLabel(count)})`;
    }

    function historyEntryMarkup(message, item) {
      return `
        <article class="history-row">
          <div class="history-topline">
            <div class="history-title-block">
              <h3>${escapeHtml(item.item_label || message.label)}</h3>
              <div class="history-meta">${escapeHtml(formatTimestamp(item.timestamp))}</div>
            </div>
            <div class="detail-tags">
              <span class="chip ${toneForStatus(item.decision_status || item.status)}">${escapeHtml(item.decision_label || item.status || item.decision || "")}</span>
            </div>
          </div>
          <div class="history-meta-grid">
            ${metaField("Reviewer", item.reviewer || "-")}
            ${metaField("Gate", item.gate_label || labelize(item.gate_type))}
          </div>
          ${item.notes ? `<div class="history-notes">${escapeHtml(item.notes)}</div>` : ""}
          ${item.proof_path ? `<div class="support-links"><a href="${assetUrl(item.proof_path, item.timestamp || message.updated_at)}" target="_blank" rel="noreferrer">Proof ${escapeHtml(fileLabel(item.proof_path))}</a></div>` : ""}
        </article>
      `;
    }

    function historyListMarkup(message) {
      const items = message && Array.isArray(message.history) ? message.history : [];
      if (!items.length) {
        return '<div class="history-empty">No history</div>';
      }
      return `<div class="history-list">${items.map((item) => historyEntryMarkup(message, item)).join("")}</div>`;
    }

    function historyRailMarkup(detail) {
      const message = detail && detail.message ? detail.message : null;
      const historyCountValue = historyCount(message);
      const toggleLabel = historyToggleLabel(historyRailExpanded, historyCountValue);
      return `
        <div class="history-rail-collapsed">
          <button
            class="history-rail-collapsed-toggle"
            type="button"
            data-history-toggle
            aria-controls="${HISTORY_RAIL_PANEL_ID}"
            aria-expanded="${historyRailExpanded ? "true" : "false"}"
            aria-label="${escapeHtml(toggleLabel)}"
          >
            <span class="history-rail-collapsed-label">History</span>
            <span class="history-rail-collapsed-count">${escapeHtml(String(historyCountValue))}</span>
          </button>
        </div>
        <div class="history-rail-expanded">
          <div class="history-rail-header">
            <div class="history-rail-header-row">
              <div class="history-rail-header-copy">
                <p class="eyebrow">History</p>
                <span class="chip">${escapeHtml(historyCountLabel(historyCountValue))}</span>
              </div>
              <button
                class="history-rail-collapse"
                type="button"
                data-history-toggle
                aria-controls="${HISTORY_RAIL_PANEL_ID}"
                aria-expanded="${historyRailExpanded ? "true" : "false"}"
                aria-label="${escapeHtml(toggleLabel)}"
              >Collapse</button>
            </div>
          </div>
          <div class="history-rail-body" id="${HISTORY_RAIL_PANEL_ID}" role="region" aria-label="History">
            <div class="history-rail-list">${historyListMarkup(message)}</div>
          </div>
        </div>
      `;
    }

    function syncHistoryRailState() {
      if (!shellRoot || !historyRoot) {
        return;
      }
      shellRoot.classList.toggle("is-history-expanded", historyRailExpanded);
      historyRoot.dataset.expanded = historyRailExpanded ? "true" : "false";
      const toggleButtons = historyRoot.querySelectorAll("[data-history-toggle]");
      const currentMessage = currentDetail && currentDetail.message ? currentDetail.message : null;
      const toggleLabel = historyToggleLabel(historyRailExpanded, historyCount(currentMessage));
      toggleButtons.forEach((node) => {
        node.setAttribute("aria-expanded", historyRailExpanded ? "true" : "false");
        node.setAttribute("aria-label", toggleLabel);
      });
      const collapsedToggle = historyRoot.querySelector(".history-rail-collapsed-toggle");
      if (collapsedToggle) {
        collapsedToggle.tabIndex = historyRailExpanded ? -1 : 0;
      }
      const expandedPanel = historyRoot.querySelector(".history-rail-expanded");
      if (expandedPanel) {
        expandedPanel.inert = !historyRailExpanded;
        expandedPanel.setAttribute("aria-hidden", historyRailExpanded ? "false" : "true");
      }
      const collapseButton = historyRoot.querySelector(".history-rail-collapse");
      if (collapseButton) {
        collapseButton.tabIndex = historyRailExpanded ? 0 : -1;
      }
    }

    function toggleHistoryRail(forceExpanded) {
      historyRailExpanded = typeof forceExpanded === "boolean" ? forceExpanded : !historyRailExpanded;
      syncHistoryRailState();
    }

    function renderHistory(detail) {
      setWorkspace();
      historyRoot.innerHTML = historyRailMarkup(detail);
      syncHistoryRailState();
    }

    function detailMarkup(detail, previousMessageId) {
      if (!detail || !detail.message) {
        const title = detail && detail.emptyMessage ? detail.emptyMessage : "No messages";
        const message = currentInbox && currentInbox.messages && currentInbox.messages.length
          ? "No review items match the current filters."
          : "Review items will appear here when an episode gate is ready.";
        return statePanelMarkup(title, message);
      }
      const message = detail.message;
      const reviewContext = reviewContextMarkup(message);
      const detailMetadata = `
        <div class="detail-meta-grid">
          ${metaField("Episode", message.episode_id)}
          ${metaField("Gate", message.gate_label || labelize(message.gate_type))}
          ${metaField("Item ID", message.item_id || "-")}
          ${metaField("Workflow", laneLabel(message) || "-")}
          ${metaField("Decision", decisionLabel(message) || "-")}
          ${freshnessLabel(message) ? metaField("Audio Freshness", freshnessLabel(message)) : ""}
          ${packageSyncLabel(message) ? metaField("Package Sync", packageSyncLabel(message)) : ""}
          ${message.audio_provider ? metaField("Audio Provider", message.audio_provider) : ""}
          ${message.audio_voice ? metaField("Audio Voice", message.audio_voice) : ""}
          ${message.audio_model ? metaField("Audio Model", message.audio_model) : ""}
          ${message.audio_source_manifest_path ? metaField("Source Manifest", fileLabel(message.audio_source_manifest_path)) : ""}
          ${metaField("Updated", formatTimestamp(message.updated_at))}
        </div>
        ${message.gate_type === "visual_research" ? `<div class="metrics-inline">${metricsMarkup(message)}</div>` : ""}
      `;
      const blockedReasonMarkup = message.blocked_reason
        ? `<div class="detail-note">${escapeHtml(message.blocked_reason)}</div>`
        : "";
      const previewSection = message.gate_type === "visual_research"
        ? visualResearchPreviewMarkup(message, previousMessageId)
        : `<div class="preview-stage">${previewMarkup(message, message.updated_at)}</div>`;
      return `
        <div class="detail-main">
          <section class="section-block">
            <div class="message-toolbar">
              <div>
                <p class="eyebrow">${escapeHtml(message.episode_id)} / ${escapeHtml(message.gate_label || labelize(message.gate_type))}</p>
                <h2>${escapeHtml(message.label)}</h2>
              </div>
              <div class="detail-tags">
                ${chipMarkup(decisionLabel(message), decisionStatus(message))}
                ${chipMarkup(laneLabel(message), laneStatus(message))}
                ${chipMarkup(freshnessLabel(message), freshnessStatus(message))}
                ${chipMarkup(packageSyncLabel(message), packageSyncStatus(message))}
                <span class="chip ${message.unread ? "warn" : "ok"}">${escapeHtml(message.unread ? "Unread" : "Read")}</span>
              </div>
            </div>
            <div class="detail-summary-bar">
              <div class="summary-pill-row">
                ${summaryPillMarkup("Updated", formatTimestamp(message.updated_at))}
                ${summaryPillMarkup("Episode", message.episode_id)}
              </div>
              <div class="meta-actions">
                ${actionMenuMarkup(message)}
              </div>
            </div>
            ${blockedReasonMarkup}
          </section>
          <section class="section-block">
            ${previewSection}
          </section>
          ${disclosureSectionMarkup("Details", detailMetadata, "detail-disclosure")}
          ${disclosureSectionMarkup("Review Context", reviewContext, "review-context-disclosure")}
          ${disclosureSectionMarkup("Episode Guardrails", episodeGuardrailsMarkup(message), "guardrails-disclosure")}
        </div>
      `;
    }

    function episodeOptions(inbox) {
      const options = [{ episode_id: "all", episode_title: "All episodes" }];
      const seen = new Set();
      (inbox && inbox.messages ? inbox.messages : []).forEach((message) => {
        const episodeId = String(message.episode_id || "").trim();
        if (!episodeId || seen.has(episodeId)) {
          return;
        }
        seen.add(episodeId);
        options.push({
          episode_id: episodeId,
          episode_title: String(message.episode_title || "").trim() || episodeId,
        });
      });
      return options;
    }

    function normalizeEpisodeFilter(inbox, value) {
      const requested = String(value || "").trim();
      if (!requested || requested === "all") {
        return "all";
      }
      return episodeOptions(inbox).some((option) => option.episode_id === requested) ? requested : "all";
    }

    function statusFilterKey(message) {
      const normalized = String(decisionStatus(message)).trim().toLowerCase();
      if (PENDING_FILTER_STATUSES.has(normalized)) {
        return "pending";
      }
      if (normalized === "rejected") {
        return "rejected";
      }
      if (APPROVED_FILTER_STATUSES.has(normalized)) {
        return "approved";
      }
      return "other";
    }

    function filterMessages(inbox, episodeId, statusFilter) {
      const resolvedEpisodeId = normalizeEpisodeFilter(inbox, episodeId);
      const resolvedStatusFilter = normalizeStatusFilter(statusFilter);
      return (inbox && inbox.messages ? inbox.messages : []).filter((message) => {
        if (resolvedEpisodeId !== "all" && message.episode_id !== resolvedEpisodeId) {
          return false;
        }
        if (resolvedStatusFilter === "all") {
          return true;
        }
        return statusFilterKey(message) === resolvedStatusFilter;
      });
    }

    function groupMessagesByGate(messages) {
      const groups = PHASE_GATE_ORDER.map((group) => ({ ...group, messages: [] }));
      const groupsByGate = new Map(groups.map((group) => [group.gateType, group]));
      messages.forEach((message) => {
        const group = groupsByGate.get(message.gate_type);
        if (group) {
          group.messages.push(message);
        }
      });
      return groups.filter((group) => group.messages.length);
    }

    function resolveRailSelection(inbox, requestedMessageId, episodeId, statusFilter) {
      const resolvedEpisodeId = normalizeEpisodeFilter(inbox, episodeId);
      const resolvedStatusFilter = normalizeStatusFilter(statusFilter);
      const visibleMessages = filterMessages(inbox, resolvedEpisodeId, resolvedStatusFilter);
      const selected = visibleMessages.find((message) => message.message_id === requestedMessageId);
      return {
        episodeId: resolvedEpisodeId,
        statusFilter: resolvedStatusFilter,
        visibleMessages,
        activeMessageId: selected ? requestedMessageId : (visibleMessages[0] ? visibleMessages[0].message_id : ""),
      };
    }

    function railMessageMarkup(message, selectedMessageId) {
      const episodeLabel = message.episode_title || message.episode_id;
      const workflowLabel = laneLabel(message);
      const packageLabel = packageSyncStatus(message) && packageSyncStatus(message) !== "unknown"
        ? packageSyncLabel(message)
        : "";
      const itemSuffix = message.item_id ? ` / ${escapeHtml(message.item_id)}` : "";
      return `
        <button class="message-link ${message.message_id === selectedMessageId ? "is-selected" : ""}" type="button" data-message-id="${escapeHtml(message.message_id)}">
          <div class="message-line">
            <div style="display:flex; gap:10px; min-width:0;">
              <span class="read-dot ${message.unread ? "is-unread" : ""}"></span>
              <div style="min-width:0;">
                <div class="message-title">${escapeHtml(message.label)}</div>
                <div class="message-subline">${escapeHtml(episodeLabel)} / ${escapeHtml(message.gate_label || labelize(message.gate_type))}${itemSuffix}${workflowLabel ? ` / ${escapeHtml(workflowLabel)}` : ""}${packageLabel ? ` / ${escapeHtml(packageLabel)}` : ""}</div>
              </div>
            </div>
          </div>
          <div class="message-tags">
            ${chipMarkup(decisionLabel(message), decisionStatus(message))}
          </div>
        </button>
      `;
    }

    function railMarkup(inbox, selectedMessageId, episodeId, statusFilter) {
      const visibleMessages = filterMessages(inbox, episodeId, statusFilter);
      const groupedMessages = groupMessagesByGate(visibleMessages);
      if (!inbox.messages.length) {
        return `
          <div class="rail-header">
            <div class="rail-controls">
              <label class="rail-select-wrap">
                <span class="meta-label">Episode</span>
                <span class="control-trigger rail-select-shell">
                  <select class="rail-select" data-episode-filter aria-label="Episode filter">
                    ${episodeOptions(inbox).map((option) => `
                      <option value="${escapeHtml(option.episode_id)}"${option.episode_id === episodeId ? " selected" : ""}>${escapeHtml(option.episode_title)}</option>
                    `).join("")}
                  </select>
                </span>
              </label>
              <div class="rail-select-wrap">
                <span class="meta-label">Decision</span>
                <div class="rail-filter-row">
                  ${STATUS_FILTER_OPTIONS.map((option) => `
                    <button class="rail-filter ${option.key === statusFilter ? "is-active" : ""}" type="button" data-status-filter="${escapeHtml(option.key)}" aria-pressed="${option.key === statusFilter ? "true" : "false"}">${escapeHtml(option.label)}</button>
                  `).join("")}
                </div>
              </div>
            </div>
          </div>
          <div class="rail-list"><div class="rail-empty empty">No messages</div></div>
        `;
      }
      return `
        <div class="rail-header">
          <div class="rail-controls">
            <label class="rail-select-wrap">
              <span class="meta-label">Episode</span>
              <span class="control-trigger rail-select-shell">
                <select class="rail-select" data-episode-filter aria-label="Episode filter">
                  ${episodeOptions(inbox).map((option) => `
                    <option value="${escapeHtml(option.episode_id)}"${option.episode_id === episodeId ? " selected" : ""}>${escapeHtml(option.episode_title)}</option>
                  `).join("")}
                </select>
              </span>
            </label>
            <div class="rail-select-wrap">
              <span class="meta-label">Decision</span>
              <div class="rail-filter-row">
                ${STATUS_FILTER_OPTIONS.map((option) => `
                  <button class="rail-filter ${option.key === statusFilter ? "is-active" : ""}" type="button" data-status-filter="${escapeHtml(option.key)}" aria-pressed="${option.key === statusFilter ? "true" : "false"}">${escapeHtml(option.label)}</button>
                `).join("")}
              </div>
            </div>
          </div>
        </div>
        <div class="rail-list">
          ${groupedMessages.length
            ? groupedMessages.map((group) => `
                <section class="phase-group" data-gate-group="${escapeHtml(group.gateType)}">
                  <div class="phase-label">${escapeHtml(group.label)}</div>
                  ${group.messages.map((message) => railMessageMarkup(message, selectedMessageId)).join("")}
                </section>
              `).join("")
            : '<div class="rail-empty empty">No messages match current filters</div>'}
        </div>
      `;
    }

    function renderRail(inbox, selectedMessageId, episodeId, statusFilter, preserveScroll) {
      setWorkspace();
      const railState = preserveScroll ? captureRailScrollState() : null;
      railRoot.innerHTML = railMarkup(inbox, selectedMessageId, episodeId, statusFilter);
      if (preserveScroll) {
        window.requestAnimationFrame(() => restoreRailScrollState(railState));
      }
    }

    function renderDetail(detail) {
      setWorkspace();
      const previousMessageId = currentDetail && currentDetail.message ? currentDetail.message.message_id : "";
      currentDetail = detail || null;
      detailRoot.innerHTML = detailMarkup(detail, previousMessageId);
      if (detail && detail.message) {
        detailRoot.dataset.messageId = detail.message.message_id;
      } else {
        delete detailRoot.dataset.messageId;
      }
      renderHistory(detail);
    }

    function setSelectedMessageClasses(messageId) {
      if (!railRoot) {
        return;
      }
      railRoot.querySelectorAll("button.message-link[data-message-id]").forEach((node) => {
        node.classList.toggle("is-selected", node.dataset.messageId === messageId);
      });
    }

    async function loadMessage(messageId, pushHistory) {
      if (!currentInbox) {
        return;
      }
      const resolved = resolveRailSelection(currentInbox, messageId, currentEpisodeFilter, currentStatusFilter);
      const activeMessageId = resolved.activeMessageId;
      syncViewState(activeMessageId, resolved.episodeId, resolved.statusFilter, pushHistory);
      setSelectedMessageClasses(activeMessageId);
      if (!activeMessageId) {
        renderDetail({ emptyMessage: currentInbox.messages.length ? "No messages match current filters" : "No messages" });
        return;
      }
      const detail = await fetchJson("/api/review/messages/" + encodeURIComponent(activeMessageId));
      if (
        currentMessageId !== activeMessageId
        || currentEpisodeFilter !== resolved.episodeId
        || currentStatusFilter !== resolved.statusFilter
      ) {
        return;
      }
      renderDetail(detail);
    }

    async function syncInboxView(preferredMessageId, episodeId, statusFilter, pushHistory, preserveScroll) {
      if (!currentInbox) {
        return;
      }
      const requestedMessageId = preferredMessageId || selectedMessageIdFromUrl() || currentMessageId || currentInbox.default_message_id || "";
      const resolved = resolveRailSelection(currentInbox, requestedMessageId, episodeId, statusFilter);
      renderRail(currentInbox, resolved.activeMessageId, resolved.episodeId, resolved.statusFilter, preserveScroll);
      syncViewState(resolved.activeMessageId, resolved.episodeId, resolved.statusFilter, pushHistory);
      setSelectedMessageClasses(resolved.activeMessageId);
      if (!resolved.activeMessageId) {
        renderDetail({ emptyMessage: currentInbox.messages.length ? "No messages match current filters" : "No messages" });
        return;
      }
      const detail = await fetchJson("/api/review/messages/" + encodeURIComponent(resolved.activeMessageId));
      if (
        currentMessageId !== resolved.activeMessageId
        || currentEpisodeFilter !== resolved.episodeId
        || currentStatusFilter !== resolved.statusFilter
      ) {
        return;
      }
      renderDetail(detail);
    }

    async function applyRailFilters(episodeId, statusFilter, pushHistory) {
      const preferredMessageId = currentMessageId || selectedMessageIdFromUrl() || "";
      await syncInboxView(preferredMessageId, episodeId, statusFilter, pushHistory, false);
    }

    async function loadInbox(preferredMessageId, pushHistory) {
      setWorkspace();
      renderLoadingState();
      try {
        currentInbox = await fetchJson("/api/review/inbox");
        await syncInboxView(preferredMessageId, selectedEpisodeIdFromUrl(), selectedStatusFilterFromUrl(), pushHistory, true);
      } catch (error) {
        currentInbox = null;
        syncViewState("", "all", "all", false);
        renderLoadError(error);
      }
    }

    async function submitAction(form, decision) {
      const payload = {
        episode_id: form.dataset.episodeId,
        gate_type: form.dataset.gateType,
        reviewer: form.querySelector('input[name="reviewer"]').value,
        notes: form.querySelector('textarea[name="notes"]').value,
        decision,
      };
      if (form.dataset.itemId) {
        payload.item_id = form.dataset.itemId;
      }
      const response = await fetch("/api/review/actions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const body = await response.json().catch(() => ({ error: "Invalid server response." }));
      const errorEl = form.querySelector(".error");
      if (!response.ok) {
        errorEl.textContent = body.error || "Error";
        return;
      }
      await loadInbox(form.dataset.messageId || currentMessageId || selectedMessageIdFromUrl(), false);
    }

    function closeActionMenus(exceptMenu) {
      app.querySelectorAll("[data-action-menu]").forEach((menu) => {
        if (exceptMenu && menu === exceptMenu) {
          return;
        }
        menu.classList.remove("is-open");
        const trigger = menu.querySelector(".menu-trigger");
        const panel = menu.querySelector(".action-menu-panel");
        if (trigger) {
          trigger.setAttribute("aria-expanded", "false");
        }
        if (panel) {
          panel.hidden = true;
        }
      });
    }

    function toggleActionMenu(menu) {
      if (!menu) {
        return;
      }
      const willOpen = !menu.classList.contains("is-open");
      closeActionMenus(menu);
      menu.classList.toggle("is-open", willOpen);
      const trigger = menu.querySelector(".menu-trigger");
      const panel = menu.querySelector(".action-menu-panel");
      if (trigger) {
        trigger.setAttribute("aria-expanded", willOpen ? "true" : "false");
      }
      if (panel) {
        panel.hidden = !willOpen;
      }
    }

    app.addEventListener("click", async (event) => {
      const actionButton = event.target.closest("button.action");
      if (actionButton && app.contains(actionButton)) {
        event.stopPropagation();
        if (actionButton.getAttribute("aria-disabled") === "true") {
          return;
        }
        const form = actionButton.closest("form[data-message-id]");
        if (form) {
          const decision = actionButton.classList.contains("approve")
            ? "approve"
            : actionButton.classList.contains("reject")
              ? "reject"
              : actionButton.classList.contains("unapprove")
                ? "unapprove"
                : "unreject";
          await submitAction(form, decision);
        }
        return;
      }

      const menuTrigger = event.target.closest(".menu-trigger");
      if (menuTrigger && app.contains(menuTrigger)) {
        event.stopPropagation();
        toggleActionMenu(menuTrigger.closest("[data-action-menu]"));
        return;
      }

      if (event.target.closest(".action-menu-panel")) {
        event.stopPropagation();
        return;
      }

      const statusFilterButton = event.target.closest("button[data-status-filter]");
      if (statusFilterButton && app.contains(statusFilterButton)) {
        event.stopPropagation();
        await applyRailFilters(currentEpisodeFilter, statusFilterButton.dataset.statusFilter, true);
        return;
      }

      const historyToggle = event.target.closest("button[data-history-toggle]");
      if (historyToggle && app.contains(historyToggle)) {
        event.stopPropagation();
        toggleHistoryRail();
        return;
      }

      const docTab = event.target.closest("button.doc-tab[data-doc-label][data-message-id]");
      if (docTab && app.contains(docTab)) {
        event.stopPropagation();
        if (currentDetail && currentDetail.message && currentDetail.message.message_id === docTab.dataset.messageId) {
          visualResearchTabState[docTab.dataset.messageId] = docTab.dataset.docLabel;
          renderDetail(currentDetail);
        }
        return;
      }

      const messageLink = event.target.closest("button.message-link[data-message-id]");
      if (messageLink && app.contains(messageLink)) {
        loadMessage(messageLink.dataset.messageId, true);
      }
    });
    app.addEventListener("change", async (event) => {
      const episodeSelect = event.target.closest("select[data-episode-filter]");
      if (!episodeSelect || !app.contains(episodeSelect)) {
        return;
      }
      await applyRailFilters(episodeSelect.value, currentStatusFilter, true);
    });

    document.addEventListener("click", (event) => {
      if (!event.target.closest("[data-action-menu]")) {
        closeActionMenus();
      }
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        closeActionMenus();
      }
    });
    app.addEventListener("keydown", (event) => {
      const currentTab = event.target.closest("button.doc-tab[role='tab']");
      if (!currentTab || !app.contains(currentTab)) {
        return;
      }
      if (!["ArrowRight", "ArrowLeft", "Home", "End"].includes(event.key)) {
        return;
      }
      const tabList = currentTab.closest("[role='tablist']");
      const tabs = tabList ? Array.from(tabList.querySelectorAll("button.doc-tab[role='tab']:not([disabled])")) : [];
      if (!tabs.length) {
        return;
      }
      event.preventDefault();
      const currentIndex = Math.max(tabs.indexOf(currentTab), 0);
      const nextIndex = event.key === "Home"
        ? 0
        : event.key === "End"
          ? tabs.length - 1
          : (currentIndex + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
      tabs[nextIndex].focus();
      tabs[nextIndex].click();
    });

    window.addEventListener("popstate", () => {
      loadInbox(selectedMessageIdFromUrl(), false);
    });

    if (DEV_RELOAD_ENABLED) {
      window.setInterval(checkForServerRestart, 1000);
    }

    loadInbox(selectedMessageIdFromUrl(), false);
  </script>
</body>
</html>"""
    return (
        template.replace("__THEME_STYLES__", _render_theme_styles(active_theme))
        .replace("__WARNING_BANNER__", _render_warning_banner(active_theme))
        .replace("__DEV_RELOAD_ENABLED__", "true" if dev_reload_enabled else "false")
        .replace("__SERVER_INSTANCE_ID__", json.dumps(server_instance_id))
    )


def make_review_handler(
    context: Context,
    *,
    dev_reload_enabled: bool = False,
    server_instance_id: str = "",
) -> type[BaseHTTPRequestHandler]:
    class ReviewHandler(BaseHTTPRequestHandler):
        server_version = "CEReview/0.1"

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _send_json(self, payload: dict[str, Any], *, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, body: str, *, status: HTTPStatus = HTTPStatus.OK) -> None:
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _send_error_json(self, status: HTTPStatus, message: str) -> None:
            self._send_json({"error": message}, status=status)

        def _send_redirect(self, location: str, *, status: HTTPStatus = HTTPStatus.FOUND) -> None:
            self.send_response(status)
            self.send_header("Location", location)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

        def _write_file_bytes(self, path: Path, start: int, length: int) -> None:
            remaining = length
            with path.open("rb") as handle:
                handle.seek(start)
                while remaining > 0:
                    chunk = handle.read(min(ASSET_CHUNK_SIZE, remaining))
                    if not chunk:
                        return
                    self.wfile.write(chunk)
                    remaining -= len(chunk)

        def _serve_asset(self, path_value: str) -> None:
            try:
                path = ensure_allowed_asset_path(context, path_value)
            except SystemExit as exc:
                self._send_error_json(HTTPStatus.FORBIDDEN, str(exc))
                return
            if not path.exists():
                self._send_error_json(HTTPStatus.NOT_FOUND, f"Asset is missing: {path}")
                return
            if path.suffix.lower() in {".md", ".markdown"}:
                theme = load_signal_brand_theme(context)
                self._send_html(render_markdown_html(path.read_text(encoding="utf-8"), title=path.name, theme=theme))
                return
            content_type, _encoding = mimetypes.guess_type(str(path))
            file_size = path.stat().st_size
            try:
                byte_range = _parse_byte_range(self.headers.get("Range"), file_size)
            except UnsatisfiableRange:
                self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                self.send_header("Content-Type", content_type or "application/octet-stream")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Range", f"bytes */{file_size}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if byte_range is None:
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", content_type or "application/octet-stream")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Length", str(file_size))
                self.end_headers()
                self._write_file_bytes(path, 0, file_size)
                return
            start, end = byte_range
            content_length = end - start + 1
            self.send_response(HTTPStatus.PARTIAL_CONTENT)
            self.send_header("Content-Type", content_type or "application/octet-stream")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.send_header("Content-Length", str(content_length))
            self.end_headers()
            self._write_file_bytes(path, start, content_length)

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/favicon.ico":
                self.send_response(HTTPStatus.NO_CONTENT)
                self.end_headers()
                return
            if parsed.path in {"/review", "/review/"}:
                self._send_html(
                    render_review_page(
                        title="Review Inbox",
                        theme=load_signal_brand_theme(context),
                        dev_reload_enabled=dev_reload_enabled,
                        server_instance_id=server_instance_id,
                    )
                )
                return
            if parsed.path.startswith("/review/episodes/"):
                self._send_redirect("/review")
                return
            if parsed.path == "/api/review/dev-state":
                self._send_json(
                    {
                        "dev_reload_enabled": dev_reload_enabled,
                        "server_instance_id": server_instance_id,
                    }
                )
                return
            if parsed.path == "/api/review/inbox":
                self._send_json(build_review_inbox(context))
                return
            if parsed.path.startswith("/api/review/messages/"):
                message_id = unquote(parsed.path.removeprefix("/api/review/messages/")).strip()
                try:
                    self._send_json(build_review_message_detail(context, message_id))
                except SystemExit as exc:
                    self._send_error_json(HTTPStatus.NOT_FOUND, str(exc))
                return
            if parsed.path == "/api/review/assets":
                params = parse_qs(parsed.query)
                raw_path = params.get("path", [""])[0]
                if not raw_path:
                    self._send_error_json(HTTPStatus.BAD_REQUEST, "Missing required query parameter: path")
                    return
                self._serve_asset(raw_path)
                return
            self._send_error_json(HTTPStatus.NOT_FOUND, f"Unknown route: {parsed.path}")

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path != "/api/review/actions":
                self._send_error_json(HTTPStatus.NOT_FOUND, f"Unknown route: {parsed.path}")
                return
            content_length = int(self.headers.get("Content-Length", "0") or "0")
            payload = self.rfile.read(content_length) if content_length else b"{}"
            try:
                body = json.loads(payload.decode("utf-8"))
            except json.JSONDecodeError:
                self._send_error_json(HTTPStatus.BAD_REQUEST, "Request body must be valid JSON.")
                return
            try:
                result = perform_review_action(
                    context,
                    episode_id=_optional_request_text(body.get("episode_id", "")) or "",
                    gate_type=_optional_request_text(body.get("gate_type", "")) or "",
                    item_id=_optional_request_text(body.get("item_id", "")),
                    decision=_optional_request_text(body.get("decision", "")) or "",
                    reviewer=_optional_request_text(body.get("reviewer", "")),
                    notes=str(body.get("notes", "")),
                    tags=_request_tags(body.get("tags", [])),
                )
            except SystemExit as exc:
                self._send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self._send_json(result)

    return ReviewHandler


def build_review_server(
    context: Context,
    host: str = "127.0.0.1",
    port: int = 8765,
    *,
    dev_reload_enabled: bool = False,
    server_instance_id: str | None = None,
) -> ThreadingHTTPServer:
    resolved_server_instance_id = server_instance_id or uuid.uuid4().hex
    return ThreadingHTTPServer(
        (host, port),
        make_review_handler(
            context,
            dev_reload_enabled=dev_reload_enabled,
            server_instance_id=resolved_server_instance_id,
        ),
    )


def serve_review_server(
    context: Context,
    host: str = "127.0.0.1",
    port: int = 8765,
    *,
    dev_reload_enabled: bool = False,
    server_instance_id: str | None = None,
) -> ThreadingHTTPServer:
    server = build_review_server(
        context,
        host=host,
        port=port,
        dev_reload_enabled=dev_reload_enabled,
        server_instance_id=server_instance_id,
    )
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return server


__all__ = [
    "build_review_server",
    "make_review_handler",
    "render_markdown_html",
    "render_review_page",
    "serve_review_server",
]
