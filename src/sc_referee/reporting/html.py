from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from sc_referee.storage.atomic import atomic_write_bytes

from .policy import validate_report_contract


def render_report(bundle: dict[str, Any], destination: Path) -> None:
    atomic_write_bytes(destination, render_report_bytes(bundle))


def render_report_bytes(bundle: dict[str, Any]) -> bytes:
    """Render the deterministic report payload without writing it."""

    validate_report_contract(bundle)
    template_root = Path(__file__).parent / "templates"
    environment = Environment(
        loader=FileSystemLoader(template_root),
        autoescape=select_autoescape(enabled_extensions=("html", "xml"), default_for_string=True),
        undefined=StrictUndefined,
    )
    template = environment.get_template("report.html.j2")
    return template.render(bundle=bundle).encode("utf-8")
