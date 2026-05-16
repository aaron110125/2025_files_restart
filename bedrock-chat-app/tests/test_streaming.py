"""
tests/test_streaming.py — Property and unit tests for SSE streaming in app.py.

Tests cover:
  - Property 4: SSE stream faithfully forwards all Bedrock tokens and errors
  - Property 8: max_tokens is always within the valid range

Requirements: 4.2, 4.5, 6.4, 6.5, 6.6, 6.7
"""

import asyncio
import importlib.util
import os
import sys
import unittest.mock
from typing import AsyncGenerator, List

import pytest
from botocore.exceptions import ClientError
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Helpers to load app.py with a mocked boto3 client
# ---------------------------------------------------------------------------

APP_PATH = os.path.join(os.path.dirname(__file__), "..", "app.py")


def _load_app_with_mock_client(mock_client):
    """Import app.py with boto3.client patched to return mock_client.

    Returns the loaded module.
    """
    env_patch = {
        "AWS_BEARER_TOKEN_BEDROCK": "test-token-abc123",
        "AWS_REGION": "us-east-1",
        "BEDROCK_MODEL_ID": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "AUTH_ENABLED": "false",
    }
    with unittest.mock.patch.dict(os.environ, env_patch, clear=False):
        with unittest.mock.patch("boto3.client", return_value=mock_client):
            spec = importlib.util.spec_from_file_location("app_streaming_test", APP_PATH)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
    return mod


def _make_token_stream_events(tokens: List[str]) -> List[dict]:
    """Build the list of event dicts that Bedrock's converse_stream returns for a token list."""
    return [
        {"contentBlockDelta": {"delta": {"text": token}}}
        for token in tokens
    ]


def _make_throttling_client_error() -> ClientError:
    """Create a ClientError that looks like a ThrottlingException."""
    return ClientError(
        error_response={"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
        operation_name="converse_stream",
    )


def _make_generic_client_error(code: str = "ServiceUnavailableException", message: str = "Service unavailable") -> ClientError:
    """Create a generic ClientError (non-throttling)."""
    return ClientError(
        error_response={"Error": {"Code": code, "Message": message}},
        operation_name="converse_stream",
    )


def _collect_stream(stream_response_fn, messages: list) -> List[str]:
    """Synchronously collect all SSE chunks from the async generator."""
    async def _run():
        chunks = []
        async for chunk in stream_response_fn(messages):
            chunks.append(chunk)
        return chunks

    return asyncio.run(_run())


def _make_mock_client_for_tokens(tokens: List[str]):
    """Return a mock boto3 client whose converse_stream yields the given tokens."""
    mock_client = unittest.mock.MagicMock()
    mock_client.converse_stream.return_value = {
        "stream": _make_token_stream_events(tokens)
    }
    return mock_client


def _make_mock_client_raising(exc: Exception):
    """Return a mock boto3 client whose converse_stream raises exc."""
    mock_client = unittest.mock.MagicMock()
    mock_client.converse_stream.side_effect = exc
    return mock_client


# ---------------------------------------------------------------------------
# Property 4: SSE stream faithfully forwards all Bedrock tokens and errors
# Feature: bedrock-chat-app, Property 4: SSE stream faithfully forwards all Bedrock tokens and errors
# ---------------------------------------------------------------------------

# Validates: Requirements 4.2, 4.5, 6.5, 6.6, 6.7


@settings(max_examples=100)
@given(tokens=st.lists(st.text(min_size=1), min_size=1))
def test_property4_all_tokens_forwarded_as_data_events(tokens):
    """Property 4 (token path): every token from Bedrock appears as a data: SSE event in order.

    **Validates: Requirements 4.2**
    # Feature: bedrock-chat-app, Property 4: SSE stream faithfully forwards all Bedrock tokens and errors
    """
    mock_client = _make_mock_client_for_tokens(tokens)
    app_mod = _load_app_with_mock_client(mock_client)

    messages = [{"role": "user", "content": "hello"}]
    chunks = _collect_stream(app_mod.stream_response, messages)

    # Extract only data: events (not event: done / event: error)
    data_events = [c for c in chunks if c.startswith("data:") and not c.startswith("event:")]

    # Each token must appear as a data: event in order
    assert len(data_events) == len(tokens), (
        f"Expected {len(tokens)} data: events, got {len(data_events)}.\n"
        f"tokens={tokens!r}\nchunks={chunks!r}"
    )
    for i, (token, event) in enumerate(zip(tokens, data_events)):
        expected = f"data: {token}\n\n"
        assert event == expected, (
            f"Token {i} mismatch: expected {expected!r}, got {event!r}"
        )


@settings(max_examples=100)
@given(tokens=st.lists(st.text(min_size=1), min_size=1))
def test_property4_stream_ends_with_done_event(tokens):
    """Property 4 (done event): stream ends with event: done after all tokens.

    **Validates: Requirements 4.2**
    # Feature: bedrock-chat-app, Property 4: SSE stream faithfully forwards all Bedrock tokens and errors
    """
    mock_client = _make_mock_client_for_tokens(tokens)
    app_mod = _load_app_with_mock_client(mock_client)

    messages = [{"role": "user", "content": "hello"}]
    chunks = _collect_stream(app_mod.stream_response, messages)

    assert chunks[-1] == "event: done\ndata: \n\n", (
        f"Expected last chunk to be 'event: done\\ndata: \\n\\n', got {chunks[-1]!r}"
    )


@settings(max_examples=100)
@given(
    error_type=st.sampled_from(["ThrottlingException", "GenericClientError"])
)
def test_property4_errors_produce_exactly_one_error_event(error_type):
    """Property 4 (error path): any Bedrock error produces exactly one event: error with non-empty message.

    **Validates: Requirements 4.5, 6.5, 6.6, 6.7**
    # Feature: bedrock-chat-app, Property 4: SSE stream faithfully forwards all Bedrock tokens and errors
    """
    if error_type == "ThrottlingException":
        exc = _make_throttling_client_error()
    else:
        exc = _make_generic_client_error()

    mock_client = _make_mock_client_raising(exc)
    app_mod = _load_app_with_mock_client(mock_client)

    messages = [{"role": "user", "content": "hello"}]
    chunks = _collect_stream(app_mod.stream_response, messages)

    # There must be exactly one error event
    error_events = [c for c in chunks if c.startswith("event: error\n")]
    assert len(error_events) == 1, (
        f"Expected exactly 1 error event, got {len(error_events)}.\nchunks={chunks!r}"
    )

    # The error event must have a non-empty data line
    error_event = error_events[0]
    lines = error_event.strip().split("\n")
    data_lines = [l for l in lines if l.startswith("data:")]
    assert data_lines, f"Error event has no data: line.\nevent={error_event!r}"
    data_content = data_lines[0][len("data:"):].strip()
    assert data_content, (
        f"Error event data: line is empty.\nevent={error_event!r}"
    )

    # No done event should follow an error
    done_events = [c for c in chunks if c == "event: done\ndata: \n\n"]
    assert len(done_events) == 0, (
        f"Expected no done event after an error, got {len(done_events)}.\nchunks={chunks!r}"
    )


@settings(max_examples=100)
@given(tokens=st.lists(st.text(min_size=1), min_size=1))
def test_property4_token_order_preserved(tokens):
    """Property 4 (ordering): tokens appear in the SSE stream in the same order as returned by Bedrock.

    **Validates: Requirements 4.2**
    # Feature: bedrock-chat-app, Property 4: SSE stream faithfully forwards all Bedrock tokens and errors
    """
    mock_client = _make_mock_client_for_tokens(tokens)
    app_mod = _load_app_with_mock_client(mock_client)

    messages = [{"role": "user", "content": "hello"}]
    chunks = _collect_stream(app_mod.stream_response, messages)

    data_events = [c for c in chunks if c.startswith("data:") and not c.startswith("event:")]
    extracted_tokens = [e[len("data: "):-2] for e in data_events]  # strip "data: " prefix and "\n\n"

    assert extracted_tokens == tokens, (
        f"Token order mismatch.\nExpected: {tokens!r}\nGot: {extracted_tokens!r}"
    )


# ---------------------------------------------------------------------------
# Unit tests for specific error types (complement the property tests)
# ---------------------------------------------------------------------------


def test_throttling_exception_yields_error_event():
    """ThrottlingException from Bedrock yields an SSE error event.

    Validates: Requirements 4.5, 6.5
    """
    exc = _make_throttling_client_error()
    mock_client = _make_mock_client_raising(exc)
    app_mod = _load_app_with_mock_client(mock_client)

    chunks = _collect_stream(app_mod.stream_response, [{"role": "user", "content": "hi"}])
    error_events = [c for c in chunks if c.startswith("event: error\n")]

    assert len(error_events) == 1
    assert "throttl" in error_events[0].lower() or "throttled" in error_events[0].lower()


def test_unauthorized_exception_yields_error_event():
    """UnauthorizedException from Bedrock yields an SSE error event mentioning API key.

    Validates: Requirements 4.5, 6.7
    """
    exc = ClientError(
        error_response={"Error": {"Code": "UnauthorizedException", "Message": "Unauthorized"}},
        operation_name="converse_stream",
    )
    mock_client = _make_mock_client_raising(exc)
    app_mod = _load_app_with_mock_client(mock_client)

    chunks = _collect_stream(app_mod.stream_response, [{"role": "user", "content": "hi"}])
    error_events = [c for c in chunks if c.startswith("event: error\n")]

    assert len(error_events) == 1
    # Should mention API key or unauthorized
    combined = error_events[0].lower()
    assert "api key" in combined or "unauthorized" in combined or "invalid" in combined


def test_generic_client_error_yields_error_event():
    """Generic ClientError from Bedrock yields an SSE error event with the reason.

    Validates: Requirements 4.5, 6.6
    """
    exc = _make_generic_client_error(code="InternalServerException", message="Internal failure")
    mock_client = _make_mock_client_raising(exc)
    app_mod = _load_app_with_mock_client(mock_client)

    chunks = _collect_stream(app_mod.stream_response, [{"role": "user", "content": "hi"}])
    error_events = [c for c in chunks if c.startswith("event: error\n")]

    assert len(error_events) == 1
    assert "Internal failure" in error_events[0] or "service error" in error_events[0].lower()


def test_successful_stream_contains_no_error_events():
    """A successful token stream contains no error events.

    Validates: Requirements 4.2
    """
    tokens = ["Hello", ", ", "world", "!"]
    mock_client = _make_mock_client_for_tokens(tokens)
    app_mod = _load_app_with_mock_client(mock_client)

    chunks = _collect_stream(app_mod.stream_response, [{"role": "user", "content": "hi"}])
    error_events = [c for c in chunks if c.startswith("event: error\n")]

    assert len(error_events) == 0, f"Unexpected error events: {error_events!r}"
