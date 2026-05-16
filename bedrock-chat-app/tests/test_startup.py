"""
tests/test_startup.py — Unit tests for startup validation in app.py.

Since app.py performs validation at import time (module level), these tests
use subprocess.run to launch a fresh Python process with a controlled
environment for each scenario.

Requirements: 2.2, 2.3, 2.4, 2.5, 7.2
"""

import os
import subprocess
import sys
from typing import Optional, Tuple

import pytest

# Path to app.py relative to this file's location
APP_PATH = os.path.join(os.path.dirname(__file__), "..", "app.py")

# Minimal valid environment — only the vars app.py cares about.
# We strip the real environment to avoid accidentally inheriting a valid
# AWS_BEARER_TOKEN_BEDROCK from the developer's shell.
BASE_ENV = {
    "PATH": os.environ.get("PATH", ""),
    "HOME": os.environ.get("HOME", ""),
    "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
}


def run_app(env_overrides: dict, timeout: float = 10) -> subprocess.CompletedProcess:
    """Run app.py in a subprocess with a clean environment plus overrides.

    Returns the CompletedProcess so callers can inspect returncode and stderr.
    Raises subprocess.TimeoutExpired if the process does not exit within timeout.
    """
    env = {**BASE_ENV, **env_overrides}
    return subprocess.run(
        [sys.executable, APP_PATH],
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def run_app_expect_fast_exit(env_overrides: dict) -> subprocess.CompletedProcess:
    """Run app.py expecting it to exit quickly (validation failure).

    Uses a short timeout since validation errors should cause immediate exit.
    """
    return run_app(env_overrides, timeout=10)


def run_app_check_no_validation_error(env_overrides: dict) -> Tuple[Optional[int], str, str]:
    """Run app.py and check it doesn't fail due to startup validation.

    Since a valid configuration will start uvicorn (which runs indefinitely),
    we use a short timeout. If the process times out, it means it passed
    validation and started serving — that's a success. If it exits quickly
    with code 1, validation failed.

    Returns (returncode_or_None, stdout, stderr).
    returncode_or_None is None if the process timed out (i.e., started OK).
    """
    env = {**BASE_ENV, **env_overrides}
    try:
        result = subprocess.run(
            [sys.executable, APP_PATH],
            env=env,
            capture_output=True,
            text=True,
            timeout=3,  # short: if it's still running after 3s, validation passed
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        # Process is still running — validation passed, server started
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return None, stdout, stderr


# ---------------------------------------------------------------------------
# Requirement 2.5 — AWS_BEARER_TOKEN_BEDROCK is mandatory
# ---------------------------------------------------------------------------


class TestBedrockTokenValidation:
    """Tests that AWS_BEARER_TOKEN_BEDROCK is required and non-empty."""

    def test_exit_code_1_when_token_missing(self):
        """App exits with code 1 when AWS_BEARER_TOKEN_BEDROCK is not set.

        Validates: Requirement 2.5
        """
        result = run_app_expect_fast_exit({})  # no token in env
        assert result.returncode == 1, (
            f"Expected exit code 1 when AWS_BEARER_TOKEN_BEDROCK is missing, "
            f"got {result.returncode}.\nstderr: {result.stderr}\nstdout: {result.stdout}"
        )

    def test_exit_code_1_when_token_empty_string(self):
        """App exits with code 1 when AWS_BEARER_TOKEN_BEDROCK is an empty string.

        Validates: Requirement 2.5
        """
        result = run_app_expect_fast_exit({"AWS_BEARER_TOKEN_BEDROCK": ""})
        assert result.returncode == 1, (
            f"Expected exit code 1 when AWS_BEARER_TOKEN_BEDROCK is empty, "
            f"got {result.returncode}.\nstderr: {result.stderr}\nstdout: {result.stdout}"
        )

    def test_exit_code_1_when_token_whitespace_only(self):
        """App exits with code 1 when AWS_BEARER_TOKEN_BEDROCK is whitespace only.

        Validates: Requirement 2.5 (strip() makes whitespace-only equivalent to empty)
        """
        result = run_app_expect_fast_exit({"AWS_BEARER_TOKEN_BEDROCK": "   "})
        assert result.returncode == 1, (
            f"Expected exit code 1 when AWS_BEARER_TOKEN_BEDROCK is whitespace-only, "
            f"got {result.returncode}.\nstderr: {result.stderr}\nstdout: {result.stdout}"
        )

    def test_error_message_logged_when_token_missing(self):
        """App logs an error message identifying the missing variable.

        Validates: Requirement 2.5
        """
        result = run_app_expect_fast_exit({})
        combined_output = result.stdout + result.stderr
        assert "AWS_BEARER_TOKEN_BEDROCK" in combined_output, (
            "Expected error message mentioning AWS_BEARER_TOKEN_BEDROCK in output.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )


# ---------------------------------------------------------------------------
# Requirement 7.2 — AUTH_ENABLED=true requires AUTH_USERNAME and AUTH_PASSWORD
# ---------------------------------------------------------------------------


class TestAuthValidation:
    """Tests that auth credentials are validated when AUTH_ENABLED=true."""

    def test_exit_code_1_when_auth_enabled_and_username_missing(self):
        """App exits with code 1 when AUTH_ENABLED=true and AUTH_USERNAME is absent.

        Validates: Requirement 7.2
        """
        result = run_app_expect_fast_exit(
            {
                "AWS_BEARER_TOKEN_BEDROCK": "test-token-abc123",
                "AUTH_ENABLED": "true",
                # AUTH_USERNAME intentionally omitted
                "AUTH_PASSWORD": "secret",
            }
        )
        assert result.returncode == 1, (
            f"Expected exit code 1 when AUTH_USERNAME is missing, "
            f"got {result.returncode}.\nstderr: {result.stderr}\nstdout: {result.stdout}"
        )

    def test_exit_code_1_when_auth_enabled_and_username_empty(self):
        """App exits with code 1 when AUTH_ENABLED=true and AUTH_USERNAME is empty.

        Validates: Requirement 7.2
        """
        result = run_app_expect_fast_exit(
            {
                "AWS_BEARER_TOKEN_BEDROCK": "test-token-abc123",
                "AUTH_ENABLED": "true",
                "AUTH_USERNAME": "",
                "AUTH_PASSWORD": "secret",
            }
        )
        assert result.returncode == 1, (
            f"Expected exit code 1 when AUTH_USERNAME is empty, "
            f"got {result.returncode}.\nstderr: {result.stderr}\nstdout: {result.stdout}"
        )

    def test_exit_code_1_when_auth_enabled_and_password_missing(self):
        """App exits with code 1 when AUTH_ENABLED=true and AUTH_PASSWORD is absent.

        Validates: Requirement 7.2
        """
        result = run_app_expect_fast_exit(
            {
                "AWS_BEARER_TOKEN_BEDROCK": "test-token-abc123",
                "AUTH_ENABLED": "true",
                "AUTH_USERNAME": "admin",
                # AUTH_PASSWORD intentionally omitted
            }
        )
        assert result.returncode == 1, (
            f"Expected exit code 1 when AUTH_PASSWORD is missing, "
            f"got {result.returncode}.\nstderr: {result.stderr}\nstdout: {result.stdout}"
        )

    def test_exit_code_1_when_auth_enabled_and_password_empty(self):
        """App exits with code 1 when AUTH_ENABLED=true and AUTH_PASSWORD is empty.

        Validates: Requirement 7.2
        """
        result = run_app_expect_fast_exit(
            {
                "AWS_BEARER_TOKEN_BEDROCK": "test-token-abc123",
                "AUTH_ENABLED": "true",
                "AUTH_USERNAME": "admin",
                "AUTH_PASSWORD": "",
            }
        )
        assert result.returncode == 1, (
            f"Expected exit code 1 when AUTH_PASSWORD is empty, "
            f"got {result.returncode}.\nstderr: {result.stderr}\nstdout: {result.stdout}"
        )

    def test_auth_disabled_does_not_require_credentials(self):
        """App does not exit with code 1 when AUTH_ENABLED=false and credentials are absent.

        Validates: Requirement 7.2 (auth validation only applies when enabled)
        """
        returncode, stdout, stderr = run_app_check_no_validation_error(
            {
                "AWS_BEARER_TOKEN_BEDROCK": "test-token-abc123",
                "AUTH_ENABLED": "false",
                # No AUTH_USERNAME or AUTH_PASSWORD
            }
        )
        # returncode is None if the process timed out (server started OK).
        # If it exited quickly, it must not be code 1 due to auth validation.
        combined_output = stdout + stderr
        assert "AUTH_USERNAME" not in combined_output, (
            "AUTH_USERNAME error should not appear when AUTH_ENABLED=false.\n"
            f"stdout: {stdout}\nstderr: {stderr}"
        )
        assert "AUTH_PASSWORD" not in combined_output, (
            "AUTH_PASSWORD error should not appear when AUTH_ENABLED=false.\n"
            f"stdout: {stdout}\nstderr: {stderr}"
        )
        if returncode is not None:
            assert returncode != 1, (
                f"App should not exit with code 1 due to auth validation when AUTH_ENABLED=false.\n"
                f"returncode: {returncode}\nstdout: {stdout}\nstderr: {stderr}"
            )

    def test_auth_not_set_does_not_require_credentials(self):
        """App does not require credentials when AUTH_ENABLED is not set at all.

        Validates: Requirement 7.2
        """
        returncode, stdout, stderr = run_app_check_no_validation_error(
            {
                "AWS_BEARER_TOKEN_BEDROCK": "test-token-abc123",
                # AUTH_ENABLED not set — defaults to false
            }
        )
        combined_output = stdout + stderr
        assert "AUTH_USERNAME" not in combined_output
        assert "AUTH_PASSWORD" not in combined_output
        if returncode is not None:
            assert returncode != 1


# ---------------------------------------------------------------------------
# Requirement 2.2, 2.3, 2.4 — Successful initialization and default values
# ---------------------------------------------------------------------------


class TestSuccessfulInitialization:
    """Tests that the app initializes correctly when all required vars are present."""

    def test_no_sys_exit_with_all_required_vars(self):
        """App does not exit with code 1 when all required vars are present.

        Validates: Requirement 2.4
        """
        returncode, stdout, stderr = run_app_check_no_validation_error(
            {
                "AWS_BEARER_TOKEN_BEDROCK": "test-token-abc123",
            }
        )
        # returncode is None if the process timed out (server started OK — success).
        # If it exited quickly, it must not be code 1 (validation failure).
        if returncode is not None:
            assert returncode != 1, (
                f"App should not exit with code 1 when all required vars are present.\n"
                f"returncode: {returncode}\n"
                f"stdout: {stdout}\nstderr: {stderr}"
            )

    def test_no_sys_exit_with_auth_enabled_and_all_vars(self):
        """App does not exit with code 1 when AUTH_ENABLED=true and all vars present.

        Validates: Requirements 2.4, 7.2
        """
        returncode, stdout, stderr = run_app_check_no_validation_error(
            {
                "AWS_BEARER_TOKEN_BEDROCK": "test-token-abc123",
                "AUTH_ENABLED": "true",
                "AUTH_USERNAME": "admin",
                "AUTH_PASSWORD": "secret",
            }
        )
        if returncode is not None:
            assert returncode != 1, (
                f"App should not exit with code 1 when all required vars are present.\n"
                f"returncode: {returncode}\n"
                f"stdout: {stdout}\nstderr: {stderr}"
            )

    def test_default_aws_region_applied(self):
        """App uses us-east-1 as the default AWS_REGION when not set.

        Validates: Requirement 2.2
        """
        # Use the pre-existing helper script that patches boto3.client and prints
        # the resolved module-level variable — avoids compound-statement issues
        # with python -c.
        helper_path = os.path.join(os.path.dirname(__file__), "_helper_print_app_vars.py")
        result = subprocess.run(
            [sys.executable, helper_path, APP_PATH, "aws_region"],
            env={**BASE_ENV, "AWS_BEARER_TOKEN_BEDROCK": "test-token-abc123"},
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert "us-east-1" in result.stdout, (
            f"Expected default AWS_REGION to be 'us-east-1'.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_custom_aws_region_applied(self):
        """App uses the provided AWS_REGION when set.

        Validates: Requirement 2.2
        """
        helper_path = os.path.join(os.path.dirname(__file__), "_helper_print_app_vars.py")
        result = subprocess.run(
            [sys.executable, helper_path, APP_PATH, "aws_region"],
            env={
                **BASE_ENV,
                "AWS_BEARER_TOKEN_BEDROCK": "test-token-abc123",
                "AWS_REGION": "eu-west-1",
            },
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert "eu-west-1" in result.stdout, (
            f"Expected AWS_REGION to be 'eu-west-1'.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_default_bedrock_model_id_applied(self):
        """App uses the default BEDROCK_MODEL_ID when not set.

        Validates: Requirement 2.3
        """
        helper_path = os.path.join(os.path.dirname(__file__), "_helper_print_app_vars.py")
        result = subprocess.run(
            [sys.executable, helper_path, APP_PATH, "bedrock_model_id"],
            env={**BASE_ENV, "AWS_BEARER_TOKEN_BEDROCK": "test-token-abc123"},
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert "anthropic.claude-3-5-sonnet-20241022-v2:0" in result.stdout, (
            f"Expected default BEDROCK_MODEL_ID to be 'anthropic.claude-3-5-sonnet-20241022-v2:0'.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_custom_bedrock_model_id_applied(self):
        """App uses the provided BEDROCK_MODEL_ID when set.

        Validates: Requirement 2.3
        """
        custom_model = "anthropic.claude-3-haiku-20240307-v1:0"
        helper_path = os.path.join(os.path.dirname(__file__), "_helper_print_app_vars.py")
        result = subprocess.run(
            [sys.executable, helper_path, APP_PATH, "bedrock_model_id"],
            env={
                **BASE_ENV,
                "AWS_BEARER_TOKEN_BEDROCK": "test-token-abc123",
                "BEDROCK_MODEL_ID": custom_model,
            },
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert custom_model in result.stdout, (
            f"Expected BEDROCK_MODEL_ID to be '{custom_model}'.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
