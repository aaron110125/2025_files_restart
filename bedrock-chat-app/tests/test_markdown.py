"""
tests/test_markdown.py — Property tests for frontend-observable behaviors.

Tests cover:
  - Property 1: Input field cleared after any valid submission
  - Property 3: Markdown rendering produces correct HTML elements

Requirements: 3.6, 3.8

Note: These are backend-testable approximations since the frontend uses
marked.js (a JS library). Property 1 tests that the /chat route accepts
valid messages (implying frontend will clear input). Property 3 validates
that the SSE tokens can contain Markdown that would render correctly.
"""

import importlib.util
import os
import unittest.mock

import pytest
from fastapi.testclient import TestClient
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

APP_PATH = os.path.join(os.path.dirname(__file__), "..", "app.py")


def _load_app_module(mock_client=None):
    """Import app.py with boto3.client patched."""
    if mock_client is None:
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
            spec = importlib.util.spec_from_file_location("app_markdown_test", APP_PATH)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Property 1: Input field cleared after any valid submission
# Feature: bedrock-chat-app, Property 1: Input field cleared after any valid submission
# ---------------------------------------------------------------------------

# Validates: Requirements 3.6
# Note: Since the input clearing is a frontend JS behavior, this test validates
# that the backend accepts any valid (non-whitespace) message and returns a
# successful streaming response — the precondition for the frontend clearing
# the input field.


@settings(max_examples=100, deadline=None)
@given(content=st.text(min_size=1).filter(lambda s: s.strip()))
def test_property1_valid_submission_accepted_by_backend(content):
    """Property 1: Any valid (non-whitespace) message is accepted by POST /chat,
    which is the precondition for the frontend clearing the input field.

    The frontend JS clears the input field immediately after a valid submission.
    This test verifies the server-side contract that enables this behavior.

    **Validates: Requirements 3.6**
    # Feature: bedrock-chat-app, Property 1: Input field cleared after any valid submission
    """
    app_mod = _load_app_module()
    client = TestClient(app_mod.app)

    response = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": content}]},
    )

    # A valid message should get a 200 streaming response (not 422 validation error)
    assert response.status_code == 200, (
        f"Expected HTTP 200 for valid message {content!r}, got {response.status_code}.\n"
        f"Response: {response.text!r}"
    )


# ---------------------------------------------------------------------------
# Property 3: Markdown rendering produces correct HTML elements
# Feature: bedrock-chat-app, Property 3: Markdown rendering produces correct HTML elements
# ---------------------------------------------------------------------------

# Validates: Requirements 3.8
# Note: Since marked.js is a JavaScript library running in the browser, we can't
# directly test its output in Python. However, we can validate that:
# 1. The frontend HTML includes the marked.js CDN script
# 2. The frontend calls marked.parse() for assistant messages
# 3. Markdown content tokens are faithfully delivered via SSE


# Markdown patterns and their expected HTML elements
MARKDOWN_PATTERNS = [
    ("**bold**", "<strong>", "bold text renders to <strong>"),
    ("*italic*", "<em>", "italic text renders to <em>"),
    ("`code`", "<code>", "inline code renders to <code>"),
    ("- item", "<li>", "list item renders to <li>"),
    ("```\ncode block\n```", "<pre>", "code block renders to <pre>"),
]


@settings(max_examples=100, deadline=None)
@given(
    pattern_idx=st.integers(min_value=0, max_value=len(MARKDOWN_PATTERNS) - 1),
    prefix=st.text(max_size=20),
)
def test_property3_markdown_tokens_delivered_faithfully(pattern_idx, prefix):
    """Property 3: Markdown content is delivered faithfully via SSE so the
    frontend's marked.parse() can produce correct HTML elements.

    **Validates: Requirements 3.8**
    # Feature: bedrock-chat-app, Property 3: Markdown rendering produces correct HTML elements
    """
    markdown_text, expected_element, description = MARKDOWN_PATTERNS[pattern_idx]
    full_content = prefix + markdown_text

    # Create a mock that returns the markdown as a token
    mock_client = unittest.mock.MagicMock()
    mock_client.converse_stream.return_value = {
        "stream": [{"contentBlockDelta": {"delta": {"text": full_content}}}]
    }

    app_mod = _load_app_module(mock_client)
    client = TestClient(app_mod.app)

    response = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "test"}]},
    )

    assert response.status_code == 200
    body = response.text

    # The markdown text should appear in the SSE stream (as data: events)
    assert markdown_text in body, (
        f"Expected markdown pattern {markdown_text!r} ({description}) "
        f"to be present in SSE stream.\nBody: {body!r}"
    )


def test_frontend_includes_marked_js():
    """The embedded HTML includes marked.js CDN for Markdown rendering.

    Validates: Requirement 3.8
    """
    app_mod = _load_app_module()
    client = TestClient(app_mod.app)

    response = client.get("/")
    assert response.status_code == 200
    assert "marked" in response.text, (
        "Expected 'marked' library reference in HTML page"
    )
    assert "cdn.jsdelivr.net/npm/marked@12" in response.text, (
        "Expected marked.js CDN URL in HTML page"
    )


def test_frontend_calls_marked_parse():
    """The embedded JS calls marked.parse() for rendering assistant messages.

    Validates: Requirement 3.8
    """
    app_mod = _load_app_module()
    client = TestClient(app_mod.app)

    response = client.get("/")
    assert response.status_code == 200
    assert "marked.parse" in response.text, (
        "Expected 'marked.parse' call in embedded JavaScript"
    )
