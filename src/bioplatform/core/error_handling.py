from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import json
import platform
import sys
from datetime import datetime


@dataclass(frozen=True)
class ErrorTemplate:
    title: str
    message: str
    causes: tuple[str, ...] = ()
    solutions: tuple[str, ...] = ()
    log_level: str = "ERROR"


class WorkplaceErrorHandler:
    """Centralized, actionable error messaging for non-technical users."""

    ERROR_CATALOG: dict[str, ErrorTemplate] = {
        "FILE_NOT_FOUND": ErrorTemplate(
            title="File Not Found",
            message="The file '{filename}' could not be found.",
            causes=(
                "The file was moved or deleted.",
                "The file path is incorrect.",
                "You do not have permission to access this file.",
            ),
            solutions=(
                "Confirm the file exists at the selected location.",
                "Use the file browser to re-select the file.",
                "Check access permissions for the containing folder.",
            ),
            log_level="WARNING",
        ),
        "INVALID_DATA_FORMAT": ErrorTemplate(
            title="Invalid Data Format",
            message="The data in '{column}' could not be processed.",
            causes=(
                "The column contains text where numbers are expected.",
                "Missing values are not encoded consistently.",
                "Decimal separators are inconsistent.",
            ),
            solutions=(
                "Use Data Cleaning tools to normalize numeric columns.",
                "Replace malformed entries with blank or NA values.",
                "Re-import the file after correcting delimiters/decimals.",
            ),
        ),
        "PLUGIN_NOT_FOUND": ErrorTemplate(
            title="Plugin Not Available",
            message="The {plugin} plugin is required but not installed.",
            solutions=(
                "Open Tools > Plugin Manager and install the plugin.",
                "Run install command: {install_cmd}",
                "Use an alternative feature path that avoids this plugin.",
            ),
        ),
        "UNEXPECTED_ERROR": ErrorTemplate(
            title="Unexpected Error",
            message="An unexpected error occurred: {detail}",
            solutions=(
                "Try the action again.",
                "Review Runtime Status and logs.",
                "Restart the application if the issue persists.",
            ),
        ),
    }

    def format_error(self, error_type: str, **context: Any) -> dict[str, Any]:
        tpl = self.ERROR_CATALOG.get(error_type, self.ERROR_CATALOG["UNEXPECTED_ERROR"])
        safe_context = {**context}
        if "detail" not in safe_context:
            safe_context["detail"] = "No additional details."

        def _safe_fmt(text: str) -> str:
            try:
                return text.format(**safe_context)
            except Exception:
                return text

        return {
            "type": error_type,
            "title": tpl.title,
            "message": _safe_fmt(tpl.message),
            "causes": [_safe_fmt(x) for x in tpl.causes],
            "solutions": [_safe_fmt(x) for x in tpl.solutions],
            "log_level": tpl.log_level,
        }

    def to_plaintext(self, error_type: str, **context: Any) -> str:
        payload = self.format_error(error_type, **context)
        lines = [f"{payload['title']}", payload["message"], ""]
        if payload["causes"]:
            lines.append("Why this happened:")
            lines.extend([f"- {x}" for x in payload["causes"]])
            lines.append("")
        lines.append("How to fix it:")
        lines.extend([f"- {x}" for x in payload["solutions"]])
        return "\n".join(lines)

    def support_snapshot(self, context: dict[str, Any]) -> str:
        return json.dumps(
            {
                "time": datetime.utcnow().isoformat(timespec="seconds"),
                "context": context,
                "system": {
                    "platform": platform.platform(),
                    "python": sys.version,
                },
            },
            indent=2,
        )
