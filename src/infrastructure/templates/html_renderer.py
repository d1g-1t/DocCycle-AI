"""HTML renderer — wraps Jinja2 output with proper HTML document structure."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog

log = structlog.get_logger(__name__)

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Times New Roman', Times, serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px;
            color: #333;
        }}
        h1 {{ text-align: center; font-size: 18pt; margin-bottom: 24pt; }}
        h2 {{ font-size: 14pt; margin-top: 18pt; }}
        h3 {{ font-size: 12pt; margin-top: 12pt; }}
        p {{ text-align: justify; text-indent: 1.5em; margin: 6pt 0; }}
        .clause {{ margin: 12pt 0; }}
        .signature-block {{ margin-top: 48pt; display: flex; justify-content: space-between; }}
        .signature-line {{ border-top: 1px solid #333; padding-top: 4pt; min-width: 200px; }}
        .metadata {{ font-size: 9pt; color: #666; margin-top: 24pt; border-top: 1px solid #ccc; padding-top: 8pt; }}
    </style>
</head>
<body>
{body}
<div class="metadata">
    <p>Generated: {generated_at} | ContractForge AI-Native CLM</p>
</div>
</body>
</html>"""


class HtmlRenderer:
    """Wrap rendered template body in a complete HTML document."""

    def render(
        self,
        body_html: str,
        title: str = "Contract",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Produce a full HTML document from rendered body content."""
        now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
        html = _HTML_TEMPLATE.format(
            title=title,
            body=body_html,
            generated_at=now,
        )
        log.debug("html_render.ok", title=title, length=len(html))
        return html
