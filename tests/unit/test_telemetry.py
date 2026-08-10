"""Unit tests for telemetry storage."""


from codebridge.telemetry.storage import TelemetryStore


def test_initial_state():
    store = TelemetryStore()
    snap = store.snapshot()
    assert snap["requests"] == 0
    assert snap["successful"] == 0
    assert snap["failed"] == 0


def test_record_success():
    store = TelemetryStore()
    store.record_request(
        model="test/model",
        success=True,
        latency_ms=100.0,
        input_tokens=50,
        output_tokens=20,
    )
    snap = store.snapshot()
    assert snap["requests"] == 1
    assert snap["successful"] == 1
    assert snap["failed"] == 0
    assert snap["input_tokens"] == 50
    assert snap["output_tokens"] == 20


def test_record_failure():
    store = TelemetryStore()
    store.record_request(model="test/model", success=False, latency_ms=50.0)
    snap = store.snapshot()
    assert snap["failed"] == 1
    assert snap["successful"] == 0


def test_streaming_tracking():
    store = TelemetryStore()
    store.record_request(model="test/model", success=True, latency_ms=200.0, streaming=True)
    snap = store.snapshot()
    assert snap["streaming_requests"] == 1


def test_per_model_tracking():
    store = TelemetryStore()
    store.record_request(model="model-a", success=True, latency_ms=100.0)
    store.record_request(model="model-b", success=True, latency_ms=200.0)
    store.record_request(model="model-a", success=False, latency_ms=50.0)
    snap = store.snapshot()
    assert "model-a" in snap["models"]
    assert snap["models"]["model-a"]["requests"] == 2
    assert snap["models"]["model-a"]["failed"] == 1
    assert snap["models"]["model-b"]["requests"] == 1


def test_null_tokens_when_not_provided():
    store = TelemetryStore()
    store.record_request(model="test/model", success=True, latency_ms=100.0)
    snap = store.snapshot()
    assert snap["input_tokens"] is None
    assert snap["output_tokens"] is None
