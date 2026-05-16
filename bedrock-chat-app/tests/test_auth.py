"""
tests/test_auth.py — Unit and property tests for BasicAuthMiddleware in app.py.

Tests cover:
  - Task 6.3: Unit tests for auth middleware
  - Property 9: Auth middleware rejects any request without valid credentials

Requirements: 7.1, 7.3, 7.4
"""

import base64
import importlib.util
import os
import unittest.mock

import pytest
from fastapi.testclient import TestClient
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Helpers to load app.py with controlled auth settings
# ---------------------------------------------------------------------------

APP_PATH = os.path.join(os.path.dirname(__file__), "..", "app.py")

CONFIGURED_USERNAME = "admin"
CONFIGURED_PASSWORD = "s3cret!"


def _load_app_with_auth(auth_enabled: bool = True, username: str = CONFIGURED_USERNAME, password: str = CONFIGURED_PASSWORD):
    """Import app.py with auth enabled or disabled.

    Returns the loaded module.
    """
    mock_client = unittest.mock.MagicMock()
    mock_client.converse_stream.return_value = {"stream": []}

    env_patch = {
        "AWS_BEARER_TOKEN_BEDROCK": "test-token-abc123",
        "AWS_REGION": "us-east-1",
        "BEDROCK_MODEL_ID": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "AUTH_ENABLED": "true" if auth_enabled else "false",
        "AUTH_USERNAME": username,
        "AUTH_PASSWORD": password,
    }
    with unittest.mock.patch.dict(os.environ, env_patch, clear=False):
        with unittest.mock.patch("boto3.client", return_value=mock_client):
            spec = importlib.util.spec_from_file_location("app_auth_test", APP_PATH)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
    return mod


def _basic_auth_header(username: str, password: str) -> dict:
    """Build an Authorization: Basic header dict."""
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {credentials}"}


# ---------------------------------------------------------------------------
# Task 6.3: Unit tests for auth middleware
# ---------------------------------------------------------------------------


class TestAuthDisabled:
    """Tests that AUTH_ENABLED=false allows unauthenticated access."""

    def test_unauthenticated_access_to_index(self):
        """GET / is accessible without credentials when AUTH_ENABLED=false.

        Validates: Requirement 7.1
        """
        app_mod = _load_app_with_auth(auth_enabled=False)
        client = TestClient(app_mod.app)

        response = client.get("/")
        assert response.status_code == 200, (
            f"Expected 200 for unauthenticated GET / when auth disabled, "
            f"got {response.status_code}"
        )

    def test_unauthenticated_access_to_chat(self):
        """POST /chat is accessible without credentials when AUTH_ENABLED=false.

        Validates: Requirement 7.1
        """
        app_mod = _load_app_with_auth(auth_enabled=False)
        client = TestClient(app_mod.app)

        response = client.post(
            "/chat",
            json={"messages": [{"role": "user", "content": "hello"}]},
        )
        # Should not be 401 — it should proceed (200 for SSE stream)
        assert response.status_code != 401, (
            f"Expected non-401 for unauthenticated POST /chat when auth disabled, "
            f"got {response.status_code}"
        )


class TestAuthEnabled:
    """Tests that AUTH_ENABLED=true blocks unauthenticated or wrong credentials."""

    def test_401_when_no_credentials(self):
        """HTTP 401 returned when no credentials provided and AUTH_ENABLED=true.

        Validates: Requirement 7.3
        """
        app_mod = _load_app_with_auth(auth_enabled=True)
        client = TestClient(app_mod.app)

        response = client.get("/")
        assert response.status_code == 401, (
            f"Expected 401 when no credentials, got {response.status_code}"
        )
        assert "WWW-Authenticate" in response.headers
        assert 'Basic realm="Bedrock Chat"' in response.headers["WWW-Authenticate"]

    def test_401_when_wrong_username(self):
        """HTTP 401 returned for wrong username.

        Validates: Requirement 7.3
        """
        app_mod = _load_app_with_auth(auth_enabled=True)
        client = TestClient(app_mod.app)

        response = client.get("/", headers=_basic_auth_header("wrong_user", CONFIGURED_PASSWORD))
        assert response.status_code == 401

    def test_401_when_wrong_password(self):
        """HTTP 401 returned for wrong password.

        Validates: Requirement 7.3
        """
        app_mod = _load_app_with_auth(auth_enabled=True)
        client = TestClient(app_mod.app)

        response = client.get("/", headers=_basic_auth_header(CONFIGURED_USERNAME, "wrong_pass"))
        assert response.status_code == 401

    def test_401_when_malformed_auth_header(self):
        """HTTP 401 returned for malformed Authorization header.

        Validates: Requirement 7.3
        """
        app_mod = _load_app_with_auth(auth_enabled=True)
        client = TestClient(app_mod.app)

        response = client.get("/", headers={"Authorization": "Bearer some-token"})
        assert response.status_code == 401

    def test_401_when_invalid_base64(self):
        """HTTP 401 returned for invalid base64 in Authorization header.

        Validates: Requirement 7.3
        """
        app_mod = _load_app_with_auth(auth_enabled=True)
        client = TestClient(app_mod.app)

        response = client.get("/", headers={"Authorization": "Basic !!!invalid!!!"})
        assert response.status_code == 401

    def test_200_with_correct_credentials(self):
        """HTTP 200 returned for correct credentials.

        Validates: Requirement 7.4
        """
        app_mod = _load_app_with_auth(auth_enabled=True)
        client = TestClient(app_mod.app)

        response = client.get("/", headers=_basic_auth_header(CONFIGURED_USERNAME, CONFIGURED_PASSWORD))
        assert response.status_code == 200, (
            f"Expected 200 with correct credentials, got {response.status_code}"
        )

    def test_200_with_correct_credentials_on_chat(self):
        """POST /chat with correct credentials returns non-401.

        Validates: Requirement 7.4
        """
        app_mod = _load_app_with_auth(auth_enabled=True)
        client = TestClient(app_mod.app)

        response = client.post(
            "/chat",
            json={"messages": [{"role": "user", "content": "hello"}]},
            headers=_basic_auth_header(CONFIGURED_USERNAME, CONFIGURED_PASSWORD),
        )
        assert response.status_code != 401, (
            f"Expected non-401 with correct credentials on POST /chat, "
            f"got {response.status_code}"
        )


# ---------------------------------------------------------------------------
# Property 9: Auth middleware rejects any request without valid credentials
# Feature: bedrock-chat-app, Property 9: Auth middleware rejects any request without valid credentials
# ---------------------------------------------------------------------------

# Validates: Requirements 7.1, 7.3


@settings(max_examples=100, deadline=None)
@given(
    username=st.text(min_size=0, max_size=50),
    password=st.text(min_size=0, max_size=50),
)
def test_property9_invalid_credentials_rejected(username, password):
    """Property 9: Any request with credentials that don't match configured values
    is rejected with HTTP 401 and WWW-Authenticate: Basic realm="Bedrock Chat" header.

    **Validates: Requirements 7.1, 7.3**
    # Feature: bedrock-chat-app, Property 9: Auth middleware rejects any request without valid credentials
    """
    # Skip if the generated credentials happen to match the configured ones
    if username == CONFIGURED_USERNAME and password == CONFIGURED_PASSWORD:
        return

    app_mod = _load_app_with_auth(auth_enabled=True)
    client = TestClient(app_mod.app)

    response = client.get("/", headers=_basic_auth_header(username, password))

    assert response.status_code == 401, (
        f"Expected HTTP 401 for invalid credentials ({username!r}:{password!r}), "
        f"got {response.status_code}"
    )
    assert "WWW-Authenticate" in response.headers, (
        f"Expected WWW-Authenticate header in 401 response for credentials "
        f"({username!r}:{password!r})"
    )
    assert 'Basic realm="Bedrock Chat"' in response.headers["WWW-Authenticate"], (
        f"Expected 'Basic realm=\"Bedrock Chat\"' in WWW-Authenticate header, "
        f"got {response.headers['WWW-Authenticate']!r}"
    )
