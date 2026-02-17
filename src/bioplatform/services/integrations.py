from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..core.r_integration import RIntegrationManager
from ..core.structure_integration import detect_pymol


@dataclass(slots=True)
class IntegrationService:
    r_manager: RIntegrationManager

    @classmethod
    def default(cls, app_dir: Path) -> IntegrationService:
        return cls(r_manager=RIntegrationManager(app_dir=app_dir))

    def detect_r(self):
        return self.r_manager.detect_r()

    @staticmethod
    def detect_pymol():
        return detect_pymol()
