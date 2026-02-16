from __future__ import annotations

from bioplatform.core.pipeline_engine import PythonRPipelineEngine
from bioplatform.core.runtime import HardwareAbstractionLayer, accelerate


def test_hal_detect_returns_backend() -> None:
    ctx = HardwareAbstractionLayer().detect()
    assert ctx.backend
    assert isinstance(ctx.gpu_available, bool)


def test_accelerate_decorator_tracks_backend() -> None:
    @accelerate(threshold=1)
    def identity(values: list[int]) -> list[int]:
        return values

    out = identity([1, 2, 3])
    assert out == [1, 2, 3]
    assert hasattr(identity, "last_backend")


def test_pipeline_stream_prefetch_and_backend() -> None:
    engine = PythonRPipelineEngine()
    batches = [[0.1, 0.2, 0.3], [0.2, 0.4, 0.8]]

    def prefetch(idx: int):
        if idx == 0:
            return [0.5, 0.6, 0.7]
        return None

    res = engine.run_growth_pipeline_stream(batches, prefetch_next=prefetch)
    assert len(res) >= 2
    assert res[0].backend in {"cpu", "torch-cuda", "cupy"}
