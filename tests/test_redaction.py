"""Tests for secret redaction."""

from media_engine.normalize.redaction import redact


def test_redacts_anthropic_key():
    text = "key is sk-ant-abcdefghijklmnopqrstuvwxyz0123 here"
    out = redact(text)
    assert "sk-ant-" not in out
    assert "[REDACTED]" in out


def test_redacts_aws_access_key():
    out = redact("AWS_KEY AKIAIOSFODNN7EXAMPLE end")
    assert "AKIAIOSFODNN7EXAMPLE" not in out


def test_redacts_key_value_pairs():
    out = redact('api_key = "supersecretvalue123"')
    assert "supersecretvalue123" not in out
    assert "[REDACTED]" in out


def test_redacts_private_key_block():
    text = (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEpAIBAAKCAQEA...\n"
        "-----END RSA PRIVATE KEY-----"
    )
    out = redact(text)
    assert "MIIEpAIBAAKCAQEA" not in out
    assert "[REDACTED]" in out


def test_preserves_normal_text():
    text = "Add WebSocket transport and Origin check for the agent"
    assert redact(text) == text


def test_empty_string():
    assert redact("") == ""
