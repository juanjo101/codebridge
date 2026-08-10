"""Local telemetry store — no external data transmission."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field


@dataclass
class ModelStats:
    requests: int = 0
    successful: int = 0
    failed: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    streaming_requests: int = 0
    fallback_requests: int = 0
    total_latency_ms: float = 0.0


@dataclass
class TelemetryStore:
    """Thread-safe in-memory telemetry store."""

    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    requests: int = 0
    successful: int = 0
    failed: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    streaming_requests: int = 0
    fallback_requests: int = 0
    total_latency_ms: float = 0.0
    started_at: float = field(default_factory=time.time)
    models: dict[str, ModelStats] = field(default_factory=dict)

    def record_request(
        self,
        *,
        model: str,
        success: bool,
        latency_ms: float,
        streaming: bool = False,
        fallback: bool = False,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
    ) -> None:
        with self._lock:
            self.requests += 1
            if success:
                self.successful += 1
            else:
                self.failed += 1
            if streaming:
                self.streaming_requests += 1
            if fallback:
                self.fallback_requests += 1
            self.total_latency_ms += latency_ms

            if input_tokens is not None:
                self.input_tokens += input_tokens
            if output_tokens is not None:
                self.output_tokens += output_tokens

            # Per-model stats
            if model not in self.models:
                self.models[model] = ModelStats()
            ms = self.models[model]
            ms.requests += 1
            if success:
                ms.successful += 1
            else:
                ms.failed += 1
            if streaming:
                ms.streaming_requests += 1
            if fallback:
                ms.fallback_requests += 1
            ms.total_latency_ms += latency_ms
            if input_tokens is not None:
                ms.input_tokens += input_tokens
                ms.total_tokens += input_tokens
            if output_tokens is not None:
                ms.output_tokens += output_tokens
                ms.total_tokens += output_tokens

    def snapshot(self) -> dict:
        with self._lock:
            avg_latency = (
                round(self.total_latency_ms / self.requests, 1) if self.requests else 0.0
            )
            return {
                "provider": "nvidia",
                "uptime_seconds": round(time.time() - self.started_at),
                "requests": self.requests,
                "successful": self.successful,
                "failed": self.failed,
                "streaming_requests": self.streaming_requests,
                "fallback_requests": self.fallback_requests,
                "input_tokens": self.input_tokens or None,
                "output_tokens": self.output_tokens or None,
                "avg_latency_ms": avg_latency,
                "models": {
                    m: {
                        "requests": s.requests,
                        "successful": s.successful,
                        "failed": s.failed,
                        "input_tokens": s.input_tokens or None,
                        "output_tokens": s.output_tokens or None,
                        "streaming_requests": s.streaming_requests,
                        "fallback_requests": s.fallback_requests,
                    }
                    for m, s in self.models.items()
                },
            }


# Singleton
_store: TelemetryStore | None = None


def get_telemetry() -> TelemetryStore:
    global _store
    if _store is None:
        _store = TelemetryStore()
    return _store


def reset_telemetry() -> None:
    global _store
    _store = None
