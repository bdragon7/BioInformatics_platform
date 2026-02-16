from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlencode
from urllib.request import urlopen

from .models import PluginManifest


@dataclass(slots=True)
class PluginQuery:
    text: str
    limit: int = 20


class PluginIndexAggregator:
    """Aggregates plugin/package metadata from PyPI, CRAN and Bioconductor.

    GitHub repositories can always be imported directly as a fallback source.
    """

    def _get_json(self, url: str) -> object | None:
        try:
            with urlopen(url, timeout=20) as response:
                if response.status != 200:
                    return None
                return json.loads(response.read().decode("utf-8"))
        except Exception:
            return None

    def search_pypi(self, query: PluginQuery) -> list[PluginManifest]:
        _ = urlencode({"q": query.text})
        # PyPI does not expose a stable public search JSON endpoint.
        return []

    def search_cran(self, query: PluginQuery) -> list[PluginManifest]:
        data = self._get_json("https://crandb.r-pkg.org/")
        if not isinstance(data, dict):
            return []
        out: list[PluginManifest] = []
        for name, payload in data.items():
            if query.text.lower() in name.lower() and len(out) < query.limit:
                payload_map = payload if isinstance(payload, dict) else {}
                out.append(
                    PluginManifest(
                        id=f"cran:{name}",
                        name=name,
                        version=str(payload_map.get("Version", "unknown")),
                        language="r",
                        source="cran",
                        entrypoint=name,
                        description=str(payload_map.get("Title", "")),
                    )
                )
        return out

    def search_bioconductor(self, query: PluginQuery) -> list[PluginManifest]:
        data = self._get_json("https://bioconductor.org/packages/json/3.19/bioc/packages.json")
        if not isinstance(data, list):
            return []
        out: list[PluginManifest] = []
        for pkg in data:
            if not isinstance(pkg, dict):
                continue
            name = str(pkg.get("Package", ""))
            if query.text.lower() in name.lower() and len(out) < query.limit:
                out.append(
                    PluginManifest(
                        id=f"bioc:{name}",
                        name=name,
                        version=str(pkg.get("Version", "unknown")),
                        language="r",
                        source="bioconductor",
                        entrypoint=name,
                        description=str(pkg.get("Title", "")),
                    )
                )
        return out

    def import_from_github(self, repo: str) -> PluginManifest:
        clean = repo.replace("https://github.com/", "").strip("/")
        owner_repo = clean
        name = owner_repo.split("/")[-1]
        return PluginManifest(
            id=f"github:{owner_repo}",
            name=name,
            version="git",
            language="mixed",
            source="github",
            entrypoint=owner_repo,
            description="User-imported GitHub plugin.",
            docs_url=f"https://github.com/{owner_repo}",
        )

    def search_all(self, query: PluginQuery) -> list[PluginManifest]:
        results: list[PluginManifest] = []
        for batch in [
            self.search_pypi(query),
            self.search_cran(query),
            self.search_bioconductor(query),
        ]:
            results.extend(batch)
        return results[: query.limit]


def unique_plugins(items: Iterable[PluginManifest]) -> list[PluginManifest]:
    seen: set[str] = set()
    out: list[PluginManifest] = []
    for item in items:
        if item.id not in seen:
            seen.add(item.id)
            out.append(item)
    return out
