"""
tests/test_history.py — Property and unit tests for conversation history management.

Tests cover:
  - Property 6: Conversation history pruning preserves recency and enforces the 100-turn cap

Requirements: 5.5
"""

from __future__ import annotations

import importlib.util
import os
import sys
import unittest.mock
from typing import List

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Helpers to load app.py with a mocked boto3 client
# ---------------------------------------------------------------------------

APP_PATH = os.path.join(os.path.dirname(__file__), "..", "app.py")


def _load_app():
    """Import app.py with boto3.client patched to a no-op mock.

    Returns the loaded module.
    """
    mock_client = unittest.mock.MagicMock()
    env_patch = {
        "AWS_BEARER_TOKEN_BEDROCK": "test-token-abc123",
        "AWS_REGION": "us-east-1",
        "BEDROCK_MODEL_ID": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "AUTH_ENABLED": "false",
    }
    with unittest.mock.patch.dict(os.environ, env_patch, clear=False):
        with unittest.mock.patch("boto3.client", return_value=mock_client):
            spec = importlib.util.spec_from_file_location("app_history_test", APP_PATH)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
    return mod


def _make_messages(n: int) -> list[dict]:
    """Build a list of n alternating user/assistant messages.

    The list always starts with a user message and alternates roles.
    Each message has unique content so ordering can be verified.
    """
    messages = []
    for i in range(n):
        role = "user" if i % 2 == 0 else "assistant"
        messages.append({"role": role, "content": f"message-{i}"})
    return messages


# ---------------------------------------------------------------------------
# Property 6: Conversation history pruning preserves recency and enforces the 100-turn cap
# Feature: bedrock-chat-app, Property 6: Conversation history pruning preserves recency and enforces the 100-turn cap
# ---------------------------------------------------------------------------

# Validates: Requirements 5.5


@settings(max_examples=100, deadline=None)
@given(n=st.integers(min_value=101, max_value=500))
def test_property6_pruned_history_has_at_most_100_turns(n):
    """Property 6 (cap): pruned history has at most 100 turns (200 messages).

    **Validates: Requirements 5.5**
    # Feature: bedrock-chat-app, Property 6: Conversation history pruning preserves recency and enforces the 100-turn cap
    """
    app_mod = _load_app()

    # n turns = n user/assistant pairs = 2*n messages
    messages = _make_messages(n * 2)
    pruned, was_pruned = app_mod.prune_history(messages)

    # Must enforce the 100-turn (200-message) cap
    assert len(pruned) <= 200, (
        f"Pruned history has {len(pruned)} messages, expected ≤ 200 (100 turns).\n"
        f"Input had {len(messages)} messages ({n} turns)."
    )
    assert was_pruned is True, (
        f"Expected was_pruned=True for input with {n} turns (> 100), got False."
    )


@settings(max_examples=100, deadline=None)
@given(n=st.integers(min_value=101, max_value=500))
def test_property6_pruned_history_contains_most_recent_turns(n):
    """Property 6 (recency): pruned history contains the most recent turns in original order.

    **Validates: Requirements 5.5**
    # Feature: bedrock-chat-app, Property 6: Conversation history pruning preserves recency and enforces the 100-turn cap
    """
    app_mod = _load_app()

    # n turns = 2*n messages
    messages = _make_messages(n * 2)
    pruned, _ = app_mod.prune_history(messages)

    # The pruned list must be a suffix of the original list (most recent turns)
    # i.e., pruned == messages[-len(pruned):]  (possibly minus one leading assistant)
    pruned_len = len(pruned)
    assert pruned_len > 0, "Pruned history must not be empty."

    # Find where the pruned slice starts in the original messages
    # It must be a contiguous suffix of the original list
    suffix = messages[-pruned_len:]

    # Allow for the case where prune_history drops a leading assistant message
    # (the implementation may trim one extra message to keep user-first invariant)
    if suffix[0]["role"] == "assistant":
        # The implementation dropped the leading assistant turn — that's acceptable
        # Check that pruned matches the suffix starting from the next user message
        suffix = suffix[1:]
        pruned_check = pruned
    else:
        pruned_check = pruned

    assert pruned_check == suffix, (
        f"Pruned history does not match the most recent turns of the original.\n"
        f"Expected suffix: {suffix!r}\n"
        f"Got pruned: {pruned_check!r}"
    )


@settings(max_examples=100, deadline=None)
@given(n=st.integers(min_value=101, max_value=500))
def test_property6_pruned_history_preserves_original_order(n):
    """Property 6 (order): messages in pruned history appear in the same relative order as original.

    **Validates: Requirements 5.5**
    # Feature: bedrock-chat-app, Property 6: Conversation history pruning preserves recency and enforces the 100-turn cap
    """
    app_mod = _load_app()

    messages = _make_messages(n * 2)
    pruned, _ = app_mod.prune_history(messages)

    # Every message in pruned must appear in the original list in the same order
    original_contents = [m["content"] for m in messages]
    pruned_contents = [m["content"] for m in pruned]

    # pruned_contents must be a subsequence of original_contents
    # (and since it's a contiguous suffix, it's also a sublist)
    it = iter(original_contents)
    is_subsequence = all(c in it for c in pruned_contents)
    assert is_subsequence, (
        f"Pruned history does not preserve original order.\n"
        f"Original contents: {original_contents!r}\n"
        f"Pruned contents: {pruned_contents!r}"
    )


# ---------------------------------------------------------------------------
# Unit tests for specific pruning scenarios (complement the property tests)
# ---------------------------------------------------------------------------


class TestPruneHistoryUnit:
    """Unit tests for the prune_history function with specific examples."""

    def setup_method(self):
        """Load app module once per test."""
        self.app_mod = _load_app()

    def test_no_pruning_when_exactly_100_turns(self):
        """History with exactly 100 turns (200 messages) is not pruned.

        Validates: Requirement 5.5
        """
        messages = _make_messages(200)  # 100 user + 100 assistant = 100 turns
        pruned, was_pruned = self.app_mod.prune_history(messages)

        assert was_pruned is False, "Expected was_pruned=False for exactly 100 turns."
        assert pruned == messages, "Expected pruned to equal original when at cap."

    def test_no_pruning_when_below_100_turns(self):
        """History with fewer than 100 turns is not pruned.

        Validates: Requirement 5.5
        """
        messages = _make_messages(10)  # 5 turns
        pruned, was_pruned = self.app_mod.prune_history(messages)

        assert was_pruned is False, "Expected was_pruned=False for 5 turns."
        assert pruned == messages, "Expected pruned to equal original when below cap."

    def test_pruning_at_101_turns(self):
        """History with 101 turns (202 messages) is pruned to ≤ 100 turns.

        Validates: Requirement 5.5
        """
        messages = _make_messages(202)  # 101 turns
        pruned, was_pruned = self.app_mod.prune_history(messages)

        assert was_pruned is True, "Expected was_pruned=True for 101 turns."
        assert len(pruned) <= 200, (
            f"Expected ≤ 200 messages after pruning, got {len(pruned)}."
        )

    def test_pruned_history_starts_with_user_message(self):
        """Pruned history always starts with a user message.

        Validates: Requirement 5.5 (Bedrock requires user-first message ordering)
        """
        # Build a history where the 200-message tail would start with an assistant
        # message — the implementation should drop it.
        messages = _make_messages(202)  # 101 turns, starts user/assistant/user/...
        # messages[2] is user (index 2), messages[201] is assistant (last)
        # The tail of 200 messages starts at index 2 (user) — already fine.
        # Force a case where tail starts with assistant by using odd total count.
        messages_odd = _make_messages(201)  # starts user, ends user (odd count)
        # tail of 200 = messages_odd[1:] which starts with assistant
        pruned, was_pruned = self.app_mod.prune_history(messages_odd)

        if pruned:
            assert pruned[0]["role"] == "user", (
                f"Pruned history must start with a user message, "
                f"but starts with role='{pruned[0]['role']}'.\n"
                f"pruned[0]={pruned[0]!r}"
            )

    def test_most_recent_messages_retained(self):
        """The most recent messages are retained after pruning.

        Validates: Requirement 5.5
        """
        messages = _make_messages(210)  # 105 turns
        pruned, _ = self.app_mod.prune_history(messages)

        # The last message in the original must be the last in pruned
        assert pruned[-1] == messages[-1], (
            f"Expected last message to be retained.\n"
            f"Original last: {messages[-1]!r}\n"
            f"Pruned last: {pruned[-1]!r}"
        )

    def test_oldest_messages_removed(self):
        """The oldest messages are removed after pruning.

        Validates: Requirement 5.5
        """
        messages = _make_messages(210)  # 105 turns
        pruned, _ = self.app_mod.prune_history(messages)

        # The very first message of the original must NOT be in pruned
        # (since we have 105 turns and keep only 100)
        assert messages[0] not in pruned, (
            f"Expected oldest message to be removed after pruning.\n"
            f"messages[0]={messages[0]!r}\npruned={pruned!r}"
        )

    def test_empty_history_not_pruned(self):
        """Empty history is returned unchanged with was_pruned=False.

        Validates: Requirement 5.5 (edge case)
        """
        pruned, was_pruned = self.app_mod.prune_history([])

        assert was_pruned is False
        assert pruned == []

    def test_single_message_not_pruned(self):
        """Single-message history is returned unchanged.

        Validates: Requirement 5.5 (edge case)
        """
        messages = [{"role": "user", "content": "hello"}]
        pruned, was_pruned = self.app_mod.prune_history(messages)

        assert was_pruned is False
        assert pruned == messages


# ---------------------------------------------------------------------------
# Property 5: Conversation history round-trip integrity
# Feature: bedrock-chat-app, Property 5: Conversation history round-trip integrity
# ---------------------------------------------------------------------------

# Validates: Requirements 5.2, 5.3


@settings(max_examples=100, deadline=None)
@given(content=st.text(min_size=1).filter(lambda s: s.strip()))
def test_property5_user_message_forwarded_to_bedrock(content):
    """Property 5: Submitted user message appears in the messages array forwarded to Bedrock.

    **Validates: Requirements 5.2, 5.3**
    # Feature: bedrock-chat-app, Property 5: Conversation history round-trip integrity
    """
    from fastapi.testclient import TestClient

    mock_client = unittest.mock.MagicMock()
    mock_client.converse_stream.return_value = {
        "stream": [{"contentBlockDelta": {"delta": {"text": "response"}}}]
    }

    env_patch = {
        "AWS_BEARER_TOKEN_BEDROCK": "test-token-abc123",
        "AWS_REGION": "us-east-1",
        "BEDROCK_MODEL_ID": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "AUTH_ENABLED": "false",
    }
    with unittest.mock.patch.dict(os.environ, env_patch, clear=False):
        with unittest.mock.patch("boto3.client", return_value=mock_client):
            spec = importlib.util.spec_from_file_location("app_prop5_test", APP_PATH)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

    client = TestClient(mod.app)

    response = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": content}]},
    )

    assert response.status_code == 200

    # Verify the user message was forwarded to Bedrock
    call_kwargs = mock_client.converse_stream.call_args.kwargs
    messages_sent = call_kwargs["messages"]

    # The user message should be in the messages sent to Bedrock
    user_contents = [m["content"] for m in messages_sent if m["role"] == "user"]
    assert content in user_contents, (
        f"Expected user message {content!r} in messages forwarded to Bedrock.\n"
        f"Messages sent: {messages_sent!r}"
    )


@settings(max_examples=100, deadline=None)
@given(content=st.text(min_size=1).filter(lambda s: s.strip()))
def test_property5_assistant_response_in_sse_stream(content):
    """Property 5: Completed assistant response appears in the SSE stream as data events.

    **Validates: Requirements 5.2, 5.3**
    # Feature: bedrock-chat-app, Property 5: Conversation history round-trip integrity
    """
    from fastapi.testclient import TestClient

    mock_client = unittest.mock.MagicMock()
    mock_client.converse_stream.return_value = {
        "stream": [{"contentBlockDelta": {"delta": {"text": content}}}]
    }

    env_patch = {
        "AWS_BEARER_TOKEN_BEDROCK": "test-token-abc123",
        "AWS_REGION": "us-east-1",
        "BEDROCK_MODEL_ID": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "AUTH_ENABLED": "false",
    }
    with unittest.mock.patch.dict(os.environ, env_patch, clear=False):
        with unittest.mock.patch("boto3.client", return_value=mock_client):
            spec = importlib.util.spec_from_file_location("app_prop5b_test", APP_PATH)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

    client = TestClient(mod.app)

    response = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 200
    body = response.text

    # The assistant response content should appear as a data: event
    assert f"data: {content}" in body, (
        f"Expected assistant response {content!r} in SSE stream.\n"
        f"Body: {body!r}"
    )


# ---------------------------------------------------------------------------
# Property 7: Failed Bedrock responses do not mutate conversation history
# Feature: bedrock-chat-app, Property 7: Failed Bedrock responses do not mutate conversation history
# ---------------------------------------------------------------------------

# Validates: Requirements 5.6


@settings(max_examples=100, deadline=None)
@given(
    error_type=st.sampled_from(["ThrottlingException", "ClientError", "ConnectionError"])
)
def test_property7_failed_response_does_not_mutate_history(error_type):
    """Property 7: Failed Bedrock responses do not mutate the conversation history
    sent to the backend (the server doesn't persist history, so this validates
    that errors produce error events rather than done events).

    **Validates: Requirements 5.6**
    # Feature: bedrock-chat-app, Property 7: Failed Bedrock responses do not mutate conversation history
    """
    from botocore.exceptions import ClientError as BotoClientError
    from fastapi.testclient import TestClient

    mock_client = unittest.mock.MagicMock()

    if error_type == "ThrottlingException":
        mock_client.converse_stream.side_effect = BotoClientError(
            error_response={"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
            operation_name="converse_stream",
        )
    elif error_type == "ClientError":
        mock_client.converse_stream.side_effect = BotoClientError(
            error_response={"Error": {"Code": "InternalServerException", "Message": "Boom"}},
            operation_name="converse_stream",
        )
    else:  # ConnectionError — will be caught by generic except
        mock_client.converse_stream.side_effect = ConnectionError("Connection failed")

    env_patch = {
        "AWS_BEARER_TOKEN_BEDROCK": "test-token-abc123",
        "AWS_REGION": "us-east-1",
        "BEDROCK_MODEL_ID": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "AUTH_ENABLED": "false",
    }
    with unittest.mock.patch.dict(os.environ, env_patch, clear=False):
        with unittest.mock.patch("boto3.client", return_value=mock_client):
            spec = importlib.util.spec_from_file_location("app_prop7_test", APP_PATH)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

    client = TestClient(mod.app, raise_server_exceptions=False)

    # Original messages sent to the backend
    original_messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
    ]

    response = client.post("/chat", json={"messages": original_messages})

    # All error types: the StreamingResponse is returned with HTTP 200 (stream starts),
    # but the stream should contain an error event OR abort without a done event.
    # This validates that errors do NOT produce a "done" event (which would signal success).
    assert response.status_code == 200
    body = response.text

    if error_type == "ConnectionError":
        # ConnectionError isn't a ClientError, so stream_response won't catch it.
        # The stream will fail mid-way — no done event should be present.
        assert "event: done" not in body, (
            f"Expected NO 'event: done' in response for ConnectionError.\nBody: {body!r}"
        )
    else:
        # ClientError variants: stream returns an error event, no done event
        assert "event: error" in body, (
            f"Expected 'event: error' in response for {error_type}.\nBody: {body!r}"
        )
        # Must NOT contain a done event (which would signal success)
        assert "event: done" not in body, (
            f"Expected NO 'event: done' in response for failed request.\nBody: {body!r}"
        )
