"""Tests for privacy.strip_secrets / summarize_redactions."""

from __future__ import annotations

from privacy import strip_secrets, summarize_redactions


class TestStripSecrets:
    def test_empty_input_returns_empty(self):
        out, labels = strip_secrets("")
        assert out == ""
        assert labels == []

    def test_no_secrets_returns_unchanged(self):
        text = "Just a normal sentence about Python and SQLite."
        out, labels = strip_secrets(text)
        assert out == text
        assert labels == []

    def test_anthropic_key_redacted(self):
        text = "Token: sk-ant-api03-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-zzzzzz here"
        out, labels = strip_secrets(text)
        assert "sk-ant-" not in out
        assert "[REDACTED:api_key]" in out
        assert labels == ["api_key"]

    def test_openai_style_key_redacted(self):
        text = "key sk-proj1234567890abcdefghijklmnopqrstuv end"
        out, labels = strip_secrets(text)
        assert "[REDACTED:api_key]" in out
        assert labels == ["api_key"]

    def test_github_pat_redacted(self):
        text = "ghp_abcdefghijklmnopqrstuvwxyzABCDEFGHIJ used"
        out, labels = strip_secrets(text)
        assert "ghp_" not in out
        assert labels == ["api_key"]

    def test_aws_access_key_redacted(self):
        text = "credential AKIAIOSFODNN7EXAMPLE follows"
        out, labels = strip_secrets(text)
        assert "AKIA" not in out
        assert labels == ["api_key"]

    def test_jwt_redacted(self):
        text = "auth eyJabcdefgh.eyJpayload1.signature123 end"
        out, labels = strip_secrets(text)
        assert "[REDACTED:jwt]" in out
        assert labels == ["jwt"]

    def test_bearer_redacted(self):
        text = "Header: Bearer abcdef1234567890ABCDEFGH"
        out, labels = strip_secrets(text)
        assert "abcdef1234567890" not in out
        assert "[REDACTED:bearer]" in out

    def test_private_key_block_redacted(self):
        text = (
            "before\n-----BEGIN RSA PRIVATE KEY-----\n"
            "MIIEowIBAAKCAQEA1234\nfakekey\n"
            "-----END RSA PRIVATE KEY-----\nafter"
        )
        out, labels = strip_secrets(text)
        assert "MIIE" not in out
        assert "fakekey" not in out
        assert "[REDACTED:private_key]" in out
        assert "before" in out and "after" in out
        assert labels == ["private_key"]

    def test_password_assignment_redacted(self):
        text = 'config password = "hunter2supersecret"'
        out, labels = strip_secrets(text)
        assert "hunter2supersecret" not in out
        assert "password" in labels

    def test_home_path_rewritten(self):
        text = "Path: /Users/alice/projects/foo and /home/bob/code"
        out, labels = strip_secrets(text)
        assert "/Users/<user>" in out
        assert "/home/<user>" in out
        assert "alice" not in out
        assert "bob" not in out
        assert labels.count("home_path") == 2

    def test_personal_email_redacted(self):
        text = "Contact john.doe@example.com please"
        out, labels = strip_secrets(text)
        assert "john.doe@example.com" not in out
        assert "[REDACTED:email]" in out
        assert labels == ["email"]

    def test_allowlisted_email_not_redacted(self):
        text = "Write to support@anthropic.com or noreply@github.com"
        out, labels = strip_secrets(text)
        assert "support@anthropic.com" in out
        assert "noreply@github.com" in out
        assert labels == []

    def test_multiple_redactions_counted(self):
        text = "key sk-ant-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-x and AKIAIOSFODNN7EXAMPLE in /Users/foo/bar"
        out, labels = strip_secrets(text)
        assert labels.count("api_key") == 2
        assert labels.count("home_path") == 1
        assert "[REDACTED:api_key]" in out
        assert "/Users/<user>" in out

    def test_redacted_text_safe_to_repeat_strip(self):
        text = "sk-ant-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-end"
        first, _ = strip_secrets(text)
        second, second_labels = strip_secrets(first)
        assert first == second
        assert second_labels == []


class TestSummarizeRedactions:
    def test_empty_returns_empty(self):
        assert summarize_redactions([]) == ""

    def test_single_label(self):
        assert summarize_redactions(["api_key"]) == "api_key=1"

    def test_counts_and_sorted(self):
        labels = ["home_path", "api_key", "api_key", "email"]
        assert summarize_redactions(labels) == "api_key=2, email=1, home_path=1"
