"""Tests for logging configuration and sanitization."""

import logging

import pytest

from app.logging_config import SanitizingFilter


class TestSanitizingFilter:
    """Tests for the SanitizingFilter class."""

    def setup_method(self):
        """Set up test logger with SanitizingFilter."""
        # Use a unique logger name for each test to avoid conflicts
        import uuid
        logger_name = f"test_sanitizing_filter_{uuid.uuid4().hex[:8]}"
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()
        # Prevent propagation to avoid interference with root logger
        self.logger.propagate = False

        # Create a custom handler that captures log records
        self.log_records = []

        class ListHandler(logging.Handler):
            def __init__(self, records_list):
                super().__init__()
                self.records = records_list

            def emit(self, record):
                self.records.append(record)

        self.handler = ListHandler(self.log_records)
        self.sanitizing_filter = SanitizingFilter()
        self.handler.addFilter(self.sanitizing_filter)
        self.logger.addHandler(self.handler)

    def teardown_method(self):
        """Clean up logger after each test."""
        # Remove all handlers and filters
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)
        self.log_records.clear()
        # Reset propagate flag
        self.logger.propagate = True

    def test_sanitize_removes_newlines(self):
        """Test that newlines are removed from log messages."""
        test_input = "user\ninjection"
        expected = "userinjection"
        result = self.sanitizing_filter._sanitize(test_input)
        assert result == expected

    def test_sanitize_removes_carriage_returns(self):
        """Test that carriage returns are removed from log messages."""
        test_input = "user\rinjection"
        expected = "userinjection"
        result = self.sanitizing_filter._sanitize(test_input)
        assert result == expected

    def test_sanitize_removes_tabs(self):
        """Test that tabs are removed from log messages."""
        test_input = "user\tinjection"
        expected = "userinjection"
        result = self.sanitizing_filter._sanitize(test_input)
        assert result == expected

    def test_sanitize_removes_ansi_escape_sequences(self):
        """Test that ANSI escape sequences are removed."""
        test_input = "test\x1b[31mred\x1b[0m"
        expected = "test[31mred[0m"
        result = self.sanitizing_filter._sanitize(test_input)
        assert result == expected

    def test_sanitize_removes_all_control_characters(self):
        """Test that all control characters (0x00-0x1F, 0x7F-0x9F) are removed."""
        # Test various control characters
        test_input = "test\x00\x01\x02\x03\x7f\x80\x9fdata"
        expected = "testdata"
        result = self.sanitizing_filter._sanitize(test_input)
        assert result == expected

    def test_sanitize_preserves_none_as_string(self):
        """Test that None values are preserved as 'None' string."""
        result = self.sanitizing_filter._sanitize(None)
        assert result == "None"

    def test_sanitize_preserves_empty_string(self):
        """Test that empty strings are preserved."""
        result = self.sanitizing_filter._sanitize("")
        assert result == ""

    def test_sanitize_converts_integers_to_string(self):
        """Test that integers are converted to strings."""
        result = self.sanitizing_filter._sanitize(123)
        assert result == "123"

    def test_sanitize_converts_floats_to_string(self):
        """Test that floats are converted to strings."""
        result = self.sanitizing_filter._sanitize(123.45)
        assert result == "123.45"

    def test_sanitize_handles_boolean(self):
        """Test that booleans are converted to strings."""
        assert self.sanitizing_filter._sanitize(True) == "True"
        assert self.sanitizing_filter._sanitize(False) == "False"

    def test_sanitize_truncates_long_strings(self):
        """Test that strings longer than 1000 characters are truncated."""
        long_string = "a" * 2000
        result = self.sanitizing_filter._sanitize(long_string)
        assert len(result) == 1000
        assert result == "a" * 1000

    def test_sanitize_preserves_normal_text(self):
        """Test that normal text without control characters is preserved."""
        test_input = "Hello, World! This is a normal message."
        result = self.sanitizing_filter._sanitize(test_input)
        assert result == test_input

    def test_filter_sanitizes_string_message(self):
        """Test that the filter sanitizes string log messages."""
        self.logger.info("test\nmessage")
        assert len(self.log_records) == 1
        assert self.log_records[0].msg == "testmessage"

    def test_filter_sanitizes_tuple_args(self):
        """Test that the filter sanitizes tuple arguments."""
        self.logger.info("User: %s, Action: %s", "admin\ninjection", "login\rtest")
        assert len(self.log_records) == 1
        assert self.log_records[0].args == ("admininjection", "logintest")

    def test_filter_sanitizes_dict_args(self):
        """Test that the filter sanitizes dictionary arguments."""
        self.logger.info("Operation %(op)s by %(user)s", {"op": "create\ntest", "user": "admin\rtest"})
        assert len(self.log_records) == 1
        assert self.log_records[0].args == {"op": "createtest", "user": "admintest"}

    def test_filter_handles_none_in_args(self):
        """Test that the filter handles None values in arguments."""
        self.logger.info("Value: %s", None)
        assert len(self.log_records) == 1
        assert self.log_records[0].args == ("None",)

    def test_filter_handles_integer_args(self):
        """Test that the filter handles integer arguments."""
        self.logger.info("Count: %s", 42)
        assert len(self.log_records) == 1
        # Integer args are not sanitized (only strings)
        assert self.log_records[0].args == (42,)

    def test_filter_handles_mixed_type_args(self):
        """Test that the filter handles mixed type arguments."""
        self.logger.info("User: %s, ID: %s, Active: %s", "test\nuser", 123, True)
        assert len(self.log_records) == 1
        assert self.log_records[0].args == ("testuser", 123, True)

    def test_filter_handles_empty_args(self):
        """Test that the filter handles empty arguments."""
        self.logger.info("Simple message")
        assert len(self.log_records) == 1
        assert self.log_records[0].msg == "Simple message"
        assert not self.log_records[0].args

    def test_filter_returns_true(self):
        """Test that the filter always returns True to allow logging."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test",
            args=(),
            exc_info=None
        )
        result = self.sanitizing_filter.filter(record)
        assert result is True

    def test_multiple_injections_in_single_message(self):
        """Test handling multiple injection attempts in a single message."""
        test_input = "user\ntest\rmore\tdata\x1b[31m"
        expected = "usertestmoredata[31m"
        result = self.sanitizing_filter._sanitize(test_input)
        assert result == expected

    def test_unicode_characters_preserved(self):
        """Test that valid unicode characters are preserved."""
        test_input = "Hello 世界 🌍"
        result = self.sanitizing_filter._sanitize(test_input)
        assert result == test_input

    def test_filter_with_exception_info(self):
        """Test that the filter works with exception information."""
        try:
            raise ValueError("test\nerror")
        except ValueError:
            self.logger.exception("Exception occurred")

        assert len(self.log_records) == 1
        # The message should be sanitized
        assert self.log_records[0].msg == "Exception occurred"

    @pytest.mark.parametrize("control_char", [
        "\x00", "\x01", "\x02", "\x03", "\x04", "\x05", "\x06", "\x07",
        "\x08", "\x09", "\x0a", "\x0b", "\x0c", "\x0d", "\x0e", "\x0f",
        "\x10", "\x11", "\x12", "\x13", "\x14", "\x15", "\x16", "\x17",
        "\x18", "\x19", "\x1a", "\x1b", "\x1c", "\x1d", "\x1e", "\x1f",
        "\x7f", "\x80", "\x81", "\x82", "\x83", "\x84", "\x85", "\x86",
        "\x87", "\x88", "\x89", "\x8a", "\x8b", "\x8c", "\x8d", "\x8e",
        "\x8f", "\x90", "\x91", "\x92", "\x93", "\x94", "\x95", "\x96",
        "\x97", "\x98", "\x99", "\x9a", "\x9b", "\x9c", "\x9d", "\x9e", "\x9f"
    ])
    def test_individual_control_characters(self, control_char):
        """Test that each individual control character is removed."""
        test_input = f"before{control_char}after"
        expected = "beforeafter"
        result = self.sanitizing_filter._sanitize(test_input)
        assert result == expected, f"Failed to sanitize control character {repr(control_char)}"
