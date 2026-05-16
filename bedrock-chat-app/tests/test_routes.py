"""
tests/test_routes.py — Property and unit tests for the /chat route handler in app.py.

Tests cover:
  - Property 10: INFO log entry for every user message and Bedrock invocation
  - Property 11: Handled errors produce HTTP 500 and an ERROR log entry

Requirements: 4.2, 4.4, 4.5, 6.5, 6.6, 6.7, 8.5, 8.6
"""

import importlib.util
import logging
import os
import sys
import unittest.mock
from typing import AsyncGenerator

import pytest
from botocore.exceptions import ClientError
from fastapi.testclient import TestClient
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Helpers to load app.py with a mocked boto3 client
# ---------------------------------------------------------------------------

APP_PATH = os.path.join(os.path.dirname(__file__), "..", "app.py")


def _load_app_module(mock_client=None):
    """Import app.py with boto3.client patched to return mock_client.

    Returns the loaded module.
    """
    if mock_client is None:
        mock_client = unittest.mock.MagicMock()
        mock_client.converse_stream.return_value = {"stream": []}

    env_patch = {
        "AWS_BEARER_TOKEN_BEDROCK": "test-token-abc123",
        "AWS_REGION": "us-east-1",
        "BEDROCK_MODEL_ID": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "AUTH_ENABLED": "false",
    }
    with unittest.mock.patch.dict(os.environ, env_patch, clear=False):
        with unittest.mock.patch("boto3.client", return_value=mock_client):
            spec = importlib.util.spec_from_file_location("app_routes_test", APP_PATH)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
    return mod


def _make_client_error(code: str, message: str = "Test error") -> ClientError:
    """Create a ClientError with the given code and message."""
    return ClientError(
        error_response={"Error": {"Code": code, "Message": message}},
        operation_name="converse_stream",
    )


# ---------------------------------------------------------------------------
# Property 10: INFO log entry for every user message and Bedrock invocation
# Feature: bedrock-chat-app, Property 10: INFO log entry for every user message and Bedrock invocation
# ---------------------------------------------------------------------------

# Validates: Requirements 8.5


@settings(max_examples=100, deadline=None)
@given(content=st.text(min_size=1).filter(lambda s: s.strip()))
def test_property10_info_log_for_user_message_and_invocation(content):
    """Property 10: Every user message and Bedrock invocation produces an INFO log entry.

    **Validates: Requirements 8.5**
    # Feature: bedrock-chat-app, Property 10: INFO log entry for every user message and Bedrock invocation
    """
    app_mod = _load_app_module()
    client = TestClient(app_mod.app, raise_server_exceptions=False)

    # Capture log records at INFO level — attach to the module's logger
    # The logger propagates to root, so also attach to root to be safe
    log_records = []

    class _CapturingHandler(logging.Handler):
        def emit(self, record):
            log_records.append(record)

    handler = _CapturingHandler(level=logging.INFO)
    # Attach to both the module logger and the root logger
    app_mod.logger.addHandler(handler)
    app_mod.logger.setLevel(logging.INFO)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    try:
        response = client.post(
            "/chat",
            json={"messages": [{"role": "user", "content": content}]},
        )
        # Force consumption of the streaming response body
        _ = response.text
    finally:
        app_mod.logger.removeHandler(handler)
        root_logger.removeHandler(handler)

    # Assert at least one INFO entry referencing the user message
    info_records = [r for r in log_records if r.levelno == logging.INFO]

    assert any("Incoming user message" in r.getMessage() for r in info_records), (
        f"Expected INFO log entry for incoming user message.\n"
        f"Content: {content!r}\n"
        f"INFO records: {[(r.levelname, r.getMessage()) for r in info_records]!r}"
    )

    # Assert at least one INFO entry for Bedrock invocation
    assert any("Invoking Bedrock" in r.getMessage() for r in info_records), (
        f"Expected INFO log entry for Bedrock invocation.\n"
        f"Content: {content!r}\n"
        f"INFO records: {[(r.levelname, r.getMessage()) for r in info_records]!r}"
    )


# ---------------------------------------------------------------------------
# Known error types for Property 11
# ---------------------------------------------------------------------------

# These are exceptions that escape stream_response and hit the route's
# outer except Exception handler, causing HTTP 500 + ERROR log.
KNOWN_ERROR_TYPES = [
    ValueError("Simulated value error"),
    RuntimeError("Simulated runtime error"),
    ConnectionError("Simulated connection error"),
    TimeoutError("Simulated timeout error"),
    MemoryError("Simulated memory error"),
]


# ---------------------------------------------------------------------------
# Property 11: Handled errors produce HTTP 500 and an ERROR log entry
# Feature: bedrock-chat-app, Property 11: Handled errors produce HTTP 500 and an ERROR log entry
# ---------------------------------------------------------------------------

# Validates: Requirements 8.6


@settings(max_examples=100, deadline=None)
@given(error=st.sampled_from(KNOWN_ERROR_TYPES))
def test_property11_handled_errors_produce_http_500_and_error_log(error):
    """Property 11: Any handled error during request processing produces HTTP 500
    and an ERROR-level log entry containing the error type and message.

    **Validates: Requirements 8.6**
    # Feature: bedrock-chat-app, Property 11: Handled errors produce HTTP 500 and an ERROR log entry
    """
    # Load the app module with a mock client
    app_mod = _load_app_module()

    # Patch prune_history to raise — this runs BEFORE StreamingResponse is returned
    # so the outer try/except in the route will catch it and return HTTP 500.
    with unittest.mock.patch.object(app_mod, "prune_history", side_effect=error):
        client = TestClient(app_mod.app, raise_server_exceptions=False)

        # Capture log records at ERROR level
        log_records = []

        class _CapturingHandler(logging.Handler):
            def emit(self, record):
                log_records.append(record)

        handler = _CapturingHandler(level=logging.ERROR)
        app_mod.logger.addHandler(handler)
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)

        try:
            response = client.post(
                "/chat",
                json={"messages": [{"role": "user", "content": "hello"}]},
            )
        finally:
            app_mod.logger.removeHandler(handler)
            root_logger.removeHandler(handler)

        # Assert HTTP 500
        assert response.status_code == 500, (
            f"Expected HTTP 500 for error {type(error).__name__!r}, "
            f"got {response.status_code}.\n"
            f"Response body: {response.text!r}\n"
            f"Error: {error!r}"
        )

        # Assert at least one ERROR-level log entry
        error_records = [r for r in log_records if r.levelno >= logging.ERROR]
        assert error_records, (
            f"Expected at least one ERROR-level log entry for error "
            f"{type(error).__name__!r}, but none were found.\n"
            f"All captured records: {[(r.levelname, r.getMessage()) for r in log_records]!r}"
        )

        # Assert the ERROR log entry contains the error type or message
        error_type_name = type(error).__name__
        error_message = str(error)
        combined_log = " ".join(r.getMessage() for r in error_records)

        # The log should reference either the error type or the error message
        # (app.py logs the full traceback which includes both)
        assert (error_type_name in combined_log or error_message in combined_log), (
            f"Expected ERROR log to contain error type {error_type_name!r} "
            f"or message {error_message!r}.\n"
            f"Actual ERROR log entries: {[(r.levelname, r.getMessage()) for r in error_records]!r}"
        )


# ---------------------------------------------------------------------------
# Property 2: Whitespace-only messages are rejected
# Feature: bedrock-chat-app, Property 2: Whitespace-only messages are rejected
# ---------------------------------------------------------------------------

# Validates: Requirements 3.11


# Whitespace characters that Python's str.strip() removes
_WHITESPACE_CHARS = " \t\n\r\x0b\x0c\u00a0\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u3000"


@settings(max_examples=100, deadline=None)
@given(
    content=st.text(
        alphabet=_WHITESPACE_CHARS,
        min_size=1,
    )
)
def test_property2_whitespace_only_messages_rejected(content):
    """Property 2: Whitespace-only messages are rejected with HTTP 422.

    **Validates: Requirements 3.11**
    # Feature: bedrock-chat-app, Property 2: Whitespace-only messages are rejected
    """
    app_mod = _load_app_module()
    client = TestClient(app_mod.app, raise_server_exceptions=False)

    response = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": content}]},
    )

    assert response.status_code == 422, (
        f"Expected HTTP 422 for whitespace-only content {content!r}, "
        f"got {response.status_code}.\n"
        f"Response: {response.text!r}"
    )


# ---------------------------------------------------------------------------
# Unit tests for specific route behaviors (complement property tests)
# ---------------------------------------------------------------------------


def test_chat_returns_422_for_empty_messages():
    """POST /chat with an empty messages list returns HTTP 422.

    Validates: Requirements 4.2, 4.4
    """
    app_mod = _load_app_module()
    client = TestClient(app_mod.app, raise_server_exceptions=False)

    response = client.post("/chat", json={"messages": []})
    assert response.status_code == 422, (
        f"Expected HTTP 422 for empty messages list, got {response.status_code}.\n"
        f"Response: {response.text!r}"
    )


def test_chat_returns_422_when_last_message_not_user():
    """POST /chat when last message role is not 'user' returns HTTP 422.

    Validates: Requirements 4.2, 4.4
    """
    app_mod = _load_app_module()
    client = TestClient(app_mod.app, raise_server_exceptions=False)

    response = client.post(
        "/chat",
        json={
            "messages": [
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "hi there"},
            ]
        },
    )
    assert response.status_code == 422, (
        f"Expected HTTP 422 when last message is not 'user', got {response.status_code}.\n"
        f"Response: {response.text!r}"
    )


def test_chat_returns_422_for_whitespace_only_content():
    """POST /chat with whitespace-only message content returns HTTP 422.

    Validates: Requirements 4.2, 4.4
    """
    app_mod = _load_app_module()
    client = TestClient(app_mod.app, raise_server_exceptions=False)

    response = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "   "}]},
    )
    assert response.status_code == 422, (
        f"Expected HTTP 422 for whitespace-only content, got {response.status_code}.\n"
        f"Response: {response.text!r}"
    )


def test_chat_stream_ends_with_done_event():
    """Successful mock response: SSE stream ends with event: done.

    Validates: Requirements 4.2, 4.5
    """
    mock_client = unittest.mock.MagicMock()
    mock_client.converse_stream.return_value = {
        "stream": [
            {"contentBlockDelta": {"delta": {"text": "Hello"}}},
            {"contentBlockDelta": {"delta": {"text": " world"}}},
        ]
    }
    app_mod = _load_app_module(mock_client)
    client = TestClient(app_mod.app, raise_server_exceptions=False)

    response = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "hi"}]},
    )
    assert response.status_code == 200
    body = response.text
    assert "event: done" in body, (
        f"Expected 'event: done' in SSE stream.\nBody: {body!r}"
    )


def test_chat_stream_sends_error_event_for_throttling():
    """ThrottlingException from Bedrock produces an SSE error event.

    Validates: Requirements 4.5, 6.5
    """
    mock_client = unittest.mock.MagicMock()
    mock_client.converse_stream.side_effect = _make_client_error(
        "ThrottlingException", "Rate exceeded"
    )
    app_mod = _load_app_module(mock_client)
    client = TestClient(app_mod.app, raise_server_exceptions=False)

    response = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "hi"}]},
    )
    assert response.status_code == 200
    body = response.text
    assert "event: error" in body, (
        f"Expected 'event: error' in SSE stream for ThrottlingException.\nBody: {body!r}"
    )


def test_chat_stream_sends_error_event_for_unauthorized():
    """UnauthorizedException from Bedrock produces an SSE error event.

    Validates: Requirements 4.5, 6.7
    """
    mock_client = unittest.mock.MagicMock()
    mock_client.converse_stream.side_effect = _make_client_error(
        "UnauthorizedException", "Unauthorized"
    )
    app_mod = _load_app_module(mock_client)
    client = TestClient(app_mod.app, raise_server_exceptions=False)

    response = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "hi"}]},
    )
    assert response.status_code == 200
    body = response.text
    assert "event: error" in body, (
        f"Expected 'event: error' in SSE stream for UnauthorizedException.\nBody: {body!r}"
    )


def test_chat_stream_sends_error_event_for_generic_client_error():
    """Generic ClientError from Bedrock produces an SSE error event.

    Validates: Requirements 4.5, 6.6
    """
    mock_client = unittest.mock.MagicMock()
    mock_client.converse_stream.side_effect = _make_client_error(
        "InternalServerException", "Internal failure"
    )
    app_mod = _load_app_module(mock_client)
    client = TestClient(app_mod.app, raise_server_exceptions=False)

    response = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "hi"}]},
    )
    assert response.status_code == 200
    body = response.text
    assert "event: error" in body, (
        f"Expected 'event: error' in SSE stream for generic ClientError.\nBody: {body!r}"
    )


def test_chat_returns_500_for_unexpected_exception():
    """Unexpected exception in route handler returns HTTP 500.

    Validates: Requirements 8.6, 8.7
    """
    app_mod = _load_app_module()

    # Patch prune_history to raise — this runs before StreamingResponse is created
    with unittest.mock.patch.object(
        app_mod, "prune_history", side_effect=RuntimeError("Unexpected boom")
    ):
        client = TestClient(app_mod.app, raise_server_exceptions=False)
        response = client.post(
            "/chat",
            json={"messages": [{"role": "user", "content": "hi"}]},
        )

    assert response.status_code == 500, (
        f"Expected HTTP 500 for unexpected exception, got {response.status_code}.\n"
        f"Response: {response.text!r}"
    )
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Internal server error"
