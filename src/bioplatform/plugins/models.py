from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PluginManifest:
    id: str
    name: str
    version: str
    language: str
    source: str
    entrypoint: str
    description: str = ""
    docs_url: str | None = None
