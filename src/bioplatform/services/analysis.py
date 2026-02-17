from __future__ import annotations

from dataclasses import dataclass

from ..core.analysis_library import AnalysisLibrary
from ..core.pipeline_engine import PythonRPipelineEngine


@dataclass(slots=True)
class AnalysisService:
    analysis_library: AnalysisLibrary
    pipeline_engine: PythonRPipelineEngine

    @classmethod
    def default(cls) -> AnalysisService:
        library = AnalysisLibrary()
        return cls(analysis_library=library, pipeline_engine=PythonRPipelineEngine(library))
