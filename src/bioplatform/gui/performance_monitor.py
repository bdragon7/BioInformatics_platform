from __future__ import annotations

from dataclasses import dataclass

from ..core.runtime import HardwareAbstractionLayer


@dataclass(slots=True)
class PerformanceState:
    mode: str
    message: str
    color_hex: str


class PerformanceMonitorModel:
    """Headless model used by UI badge and tests."""

    def __init__(self) -> None:
        self.hal = HardwareAbstractionLayer()

    def snapshot(self, focused: bool = True) -> PerformanceState:
        ctx = self.hal.detect()
        if ctx.gpu_available and focused:
            return PerformanceState(mode="GPU", message=f"GPU: Active [{ctx.device_label}]", color_hex="#38BDF8")
        if ctx.gpu_available and not focused:
            return PerformanceState(mode="GPU", message="GPU: Throttled [Window unfocused]", color_hex="#2ECC71")
        return PerformanceState(mode="CPU", message="CPU: Optimized [Thread Load Managed]", color_hex="#2ECC71")
