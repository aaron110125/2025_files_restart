"""
tests/test_integration.py — Integration tests for bedrock-chat-app.

Tests cover:
  - End-to-end message submission with mocked Bedrock → SSE response
  - Auth middleware blocks unauthenticated requests when AUTH_ENABLED=true
  - GET / returns HTML with status 200

Requirements: 1.1, 1.2, 7.1
"""

import base64
import importlib.util
import os
import unittest.mock
from typing import List, Optional

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

APP_PATH = os.path.join(os.path.dirname(__file__), "..", "app.py")


def _load_app(auth_enabled: bool = False, tokens: Optional[List[str]] = None):
    """Load app.py with controlled settings and a mock Bedrock client.

    Args:
        auth_enabled: Whether to enable auth middleware.
        tokens: List of tokens the mock Bedrock client should return.
                Defaults to ["Hello", " ", "world", "!"].

    Returns the loaded module.
    """
    if tokens is None:
        tokens = ["Hello", " ", "world", "!"]

    mock_client = unittest.mock.MagicMock()
    mock_client.converse_stream.return_value = {
        "stream": [
            {"contentBlockDelta": {"delta": {"text": token}}}
            for token in tokens
        ]
    }

    env_patch = {
        "AWS_BEARER_TOKEN_BEDROCK": "test-token-abc123",
        "AWS_REGION": "us-east-1",
        "BEDROCK_MODEL_ID": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "AUTH_ENABLED": "true" if auth_enabled else "false",
        "AUTH_USERNAME": "admin",
        "AUTH_PASSWORD": "secret",
    }
    with unittest.mock.patch.dict(os.environ, env_patch, clear=False):
        with unittest.mock.patch("boto3.client", return_value=mock_client):
            spec = importlib.util.spec_from_file_location("app_integration_test", APP_PATH)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
    return mod


def _basic_auth_header(username: str, password: str) -> dict:
    """Build an Authorization: Basic header dict."""
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {credentials}"}


# ---------------------------------------------------------------------------
# Integration test: GET / returns HTML with status 200
# ---------------------------------------------------------------------------


class TestIndexRoute:
    """Integration tests for the GET / route."""

    def test_get_index_returns_html_200(self):
        """GET / returns status 200 with HTML content.

        Validates: Requirement 1.1
        """
        app_mod = _load_app()
        client = TestClient(app_mod.app)

        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "<!DOCTYPE html>" in response.text
        assert "Bedrock Chat" in response.text

    def test_get_index_contains_chat_interface_elements(self):
        """GET / returns HTML with key chat interface elements.

        Validates: Requirement 1.1, 1.2
        """
        app_mod = _load_app()
        client = TestClient(app_mod.app)

        response = client.get("/")
        assert response.status_code == 200
        # Check for key UI elements
        assert "message-input" in response.text
        assert "send-btn" in response.text
        assert "new-chat-btn" in response.text
        assert "chat-container" in response.text


# ---------------------------------------------------------------------------
# Integration test: End-to-end message → SSE response
# ---------------------------------------------------------------------------


class TestEndToEndChat:
    """Integration tests for the full chat flow with mocked Bedrock."""

    def test_submit_message_receives_streamed_tokens(self):
        """Submit a message → receive streamed SSE response with tokens.

        Validates: Requirements 1.1, 1.2
        """
        tokens = ["Hello", ", ", "how", " are", " you", "?"]
        app_mod = _load_app(tokens=tokens)
        client = TestClient(app_mod.app)

        response = client.post(
            "/chat",
            json={"messages": [{"role": "user", "content": "Hi there"}]},
        )

        assert response.status_code == 200
        body = response.text

        # All tokens should appear in the SSE stream
        for token in tokens:
            assert f"data: {token}" in body, (
                f"Expected token {token!r} in SSE stream.\nBody: {body!r}"
            )

        # Stream should end with done event
        assert "event: done" in body

    def test_multi_turn_conversation(self):
        """Multi-turn conversation is accepted and streamed correctly.

        Validates: Requirements 1.1, 1.2
        """
        app_mod = _load_app(tokens=["Sure", "!"])
        client = TestClient(app_mod.app)

        response = client.post(
            "/chat",
            json={
                "messages": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi! How can I help?"},
                    {"role": "user", "content": "Tell me a joke"},
                ]
            },
        )

        assert response.status_code == 200
        body = response.text
        assert "data: Sure" in body
        assert "event: done" in body

    def test_history_sent_to_bedrock(self):
        """The full conversation history is forwarded to Bedrock.

        Validates: Requirement 1.2
        """
        mock_client = unittest.mock.MagicMock()
        mock_client.converse_stream.return_value = {
            "stream": [{"contentBlockDelta": {"delta": {"text": "OK"}}}]
        }

        env_patch = {
            "AWS_BEARER_TOKEN_BEDROCK": "test-token-abc123",
            "AWS_REGION": "us-east-1",
            "BEDROCK_MODEL_ID": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "AUTH_ENABLED": "false",
        }
        with unittest.mock.patch.dict(os.environ, env_patch, clear=False):
            with unittest.mock.patch("boto3.client", return_value=mock_client):
                spec = importlib.util.spec_from_file_location("app_int_history", APP_PATH)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)

        client = TestClient(mod.app)

        messages = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "First response"},
            {"role": "user", "content": "Second message"},
        ]

        response = client.post("/chat", json={"messages": messages})
        assert response.status_code == 200

        # Verify converse_stream was called with the messages
        call_kwargs = mock_client.converse_stream.call_args.kwargs
        assert call_kwargs["messages"] == messages


# ---------------------------------------------------------------------------
# Integration test: Auth middleware blocks unauthenticated requests
# ---------------------------------------------------------------------------


class TestAuthIntegration:
    """Integration tests for auth middleware behavior."""

    def test_auth_blocks_unauthenticated_get(self):
        """GET / is blocked when AUTH_ENABLED=true and no credentials provided.

        Validates: Requirement 7.1
        """
        app_mod = _load_app(auth_enabled=True)
        client = TestClient(app_mod.app)

        response = client.get("/")
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers

    def test_auth_blocks_unauthenticated_post(self):
        """POST /chat is blocked when AUTH_ENABLED=true and no credentials provided.

        Validates: Requirement 7.1
        """
        app_mod = _load_app(auth_enabled=True)
        client = TestClient(app_mod.app)

        response = client.post(
            "/chat",
            json={"messages": [{"role": "user", "content": "hello"}]},
        )
        assert response.status_code == 401

    def test_auth_allows_authenticated_get(self):
        """GET / is allowed when AUTH_ENABLED=true and correct credentials provided.

        Validates: Requirement 7.1
        """
        app_mod = _load_app(auth_enabled=True)
        client = TestClient(app_mod.app)

        response = client.get("/", headers=_basic_auth_header("admin", "secret"))
        assert response.status_code == 200

    def test_auth_allows_authenticated_chat(self):
        """POST /chat is allowed when AUTH_ENABLED=true and correct credentials.

        Validates: Requirement 7.1
        """
        app_mod = _load_app(auth_enabled=True)
        client = TestClient(app_mod.app)

        response = client.post(
            "/chat",
            json={"messages": [{"role": "user", "content": "hello"}]},
            headers=_basic_auth_header("admin", "secret"),
        )
        assert response.status_code == 200
        assert "event: done" in response.text
