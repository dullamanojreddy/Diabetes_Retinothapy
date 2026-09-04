import time
from typing import Dict, Any
from contextlib import contextmanager

class PipelineTimer:
    """
    Phase 10: High-Resolution Monotonic Timing & Performance Instrumentation.
    Measures per-stage pipeline execution times using time.perf_counter() and tracks
    system warm/cold model execution status without exposing sensitive internals.
    """
    _inference_count: int = 0

    def __init__(self):
        self._start_time: float = time.perf_counter()
        self._stages: Dict[str, float] = {}
        self._is_cold_start: bool = (PipelineTimer._inference_count == 0)

    @contextmanager
    def track(self, stage_name: str):
        """
        Context manager to measure high-precision latency of a single pipeline stage.
        """
        stage_start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = (time.perf_counter() - stage_start) * 1000.0
            self._stages[stage_name] = round(elapsed, 2)

    def record_inference_executed(self):
        """
        Increments the process-lifetime inference counter to differentiate cold start vs warm runs.
        """
        PipelineTimer._inference_count += 1

    def get_summary(self) -> Dict[str, Any]:
        """
        Returns a structured timing dictionary including stage latencies, total pipeline time,
        and warmup indicator.
        """
        total_ms = round((time.perf_counter() - self._start_time) * 1000.0, 2)
        inference_ms = self._stages.get("inference", 0.0)

        return {
            "total_pipeline_ms": total_ms,
            "inference_ms": inference_ms,
            "is_warmup": self._is_cold_start,
            "stages_ms": dict(self._stages)
        }
