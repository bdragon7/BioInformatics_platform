from __future__ import annotations

from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable

try:
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover
    pd = None  # type: ignore


@dataclass(slots=True)
class DataBuffer:
    """Arrow-backed table buffer for Python/R interop workflows."""

    frames: dict[str, Any] = field(default_factory=dict)

    def put(self, key: str, frame: Any) -> None:
        self.frames[key] = frame

    def get(self, key: str) -> Any:
        return self.frames[key]

    def to_arrow(self, key: str) -> Any:
        frame = self.frames[key]
        try:
            import pyarrow as pa

            if pd is not None and isinstance(frame, pd.DataFrame):
                return pa.Table.from_pandas(frame, preserve_index=False)
            if isinstance(frame, list):
                return pa.table({"value": frame})
            if isinstance(frame, dict):
                return pa.table(frame)
            raise TypeError("Unsupported frame type for Arrow conversion")
        except Exception:
            return frame

    def from_arrow(self, key: str, table: Any) -> Any:
        if hasattr(table, "to_pandas"):
            frame = table.to_pandas()
        else:
            frame = table
        self.frames[key] = frame
        return frame


def r_interop(func: Callable[..., Any]) -> Callable[..., Any]:
    """Convert pandas DataFrames in args/kwargs to R data.frame objects when rpy2 is available."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if pd is None:
            return func(*args, **kwargs)
        try:
            from rpy2.robjects import pandas2ri  # type: ignore

            pandas2ri.activate()

            def convert(v: Any) -> Any:
                if isinstance(v, pd.DataFrame):
                    return pandas2ri.py2rpy(v)
                return v

            new_args = tuple(convert(a) for a in args)
            new_kwargs = {k: convert(v) for k, v in kwargs.items()}
            return func(*new_args, **new_kwargs)
        except Exception:
            return func(*args, **kwargs)

    return wrapper
