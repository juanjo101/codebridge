"""Unit tests for secret redaction."""


from codebridge.logging import redact


def test_redact_nvidia_api_key():
    text = "nvidia_api_key=nvapi-supersecretkey123"
    result = redact(text)
    assert "nvapi-supersecretkey123" not in result
    assert "[REDACTED]" in result


def test_redact_authorization_bearer():
    text = "Authorization: Bearer nvapi-supersecretkey456"
    result = redact(text)
    assert "nvapi-supersecretkey456" not in result
    assert "[REDACTED]" in result


def test_redact_local_token():
    text = "codebridge_local_token=mysecrettoken999"
    result = redact(text)
    assert "mysecrettoken999" not in result
    assert "[REDACTED]" in result


def test_redact_nvapi_pattern():
    text = "key is nvapi-ABCDEFGHIJKLMNOP"
    result = redact(text)
    assert "nvapi-ABCDEFGHIJKLMNOP" not in result


def test_no_false_redaction():
    """Normal text should not be redacted."""
    text = "model=nvidia/llama-3 status=200"
    result = redact(text)
    assert result == text


def test_redact_json_authorization():
    text = '{"authorization": "Bearer mytoken123"}'
    result = redact(text)
    assert "mytoken123" not in result


def test_redacting_filter_preserves_integer_args():
    import logging
    from codebridge.logging import RedactingFilter

    filter_obj = RedactingFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Port %d and token %s",
        args=(8787, "codebridge_local_token=mysecrettoken999"),
        exc_info=None,
    )
    assert filter_obj.filter(record) is True
    assert record.args == (8787, "codebridge_local_token=[REDACTED]")
    # Verify formatting works without TypeError
    formatted = record.getMessage()
    assert formatted == "Port 8787 and token codebridge_local_token=[REDACTED]"
