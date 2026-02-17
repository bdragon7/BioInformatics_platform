from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ..plugins.discovery import PluginIndexAggregator, PluginQuery
from ..plugins.manager import PluginRegistry
from ..plugins.models import PluginManifest
from ..plugins.runtime import LocalPluginRuntime


class PluginIndexClient(Protocol):
    def search(self, query: str, limit: int = 25) -> list[PluginManifest]:
        ...

    def import_from_github(self, repo: str) -> PluginManifest:
        ...


@dataclass(slots=True)
class HttpPluginIndexClient:
    aggregator: PluginIndexAggregator
    retries: int = 2

    def search(self, query: str, limit: int = 25) -> list[PluginManifest]:
        last_result: list[PluginManifest] = []
        for _ in range(max(1, self.retries)):
            last_result = self.aggregator.search_all(PluginQuery(query, limit=limit))
            if last_result:
                return last_result
        return last_result

    def import_from_github(self, repo: str) -> PluginManifest:
        return self.aggregator.import_from_github(repo)


@dataclass(slots=True)
class FakePluginIndexClient:
    manifests: list[PluginManifest]

    def search(self, query: str, limit: int = 25) -> list[PluginManifest]:
        q = query.lower()
        out = [m for m in self.manifests if q in m.id.lower() or q in m.name.lower()]
        return out[:limit]

    def import_from_github(self, repo: str) -> PluginManifest:
        return PluginManifest(
            id=f"github:{repo}",
            name=repo.split("/")[-1],
            version="git",
            language="mixed",
            source="github",
            entrypoint=repo,
            description="fake-import",
            docs_url=f"https://github.com/{repo}",
        )


@dataclass(slots=True)
class PluginService:
    runtime: LocalPluginRuntime
    registry: PluginRegistry
    index_client: PluginIndexClient

    @classmethod
    def default(cls, config_dir: Path = Path("config"), plugins_dir: Path = Path("plugins")) -> PluginService:
        return cls(
            runtime=LocalPluginRuntime(plugins_dir, config_dir / "plugins_enabled.json", seed_builtins=True),
            registry=PluginRegistry(config_dir / "plugins.json"),
            index_client=HttpPluginIndexClient(PluginIndexAggregator()),
        )

    def search(self, query: str, limit: int = 25) -> list[PluginManifest]:
        return self.index_client.search(query, limit=limit)

    def install_selected(self, raw_id: str, mode: str = "portable") -> Path:
        if not raw_id.startswith("github:"):
            raise ValueError("Select a GitHub plugin result to install.")
        manifest = self.index_client.import_from_github(raw_id.replace("github:", ""))
        return self.registry.install_github_plugin(manifest, Path("plugins"), mode=mode)
