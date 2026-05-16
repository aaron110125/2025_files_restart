"""
bedrock-chat-app — single-file FastAPI application.

This module is the entry point. On import / startup it:
  1. Loads environment variables from .env
  2. Validates required variables and exits with code 1 on failure
  3. Constructs the boto3 Bedrock client as a module-level singleton
  4. Registers routes, serves the embedded frontend, etc.
"""

import logging
import os
import sys
import traceback
from typing import AsyncGenerator, Literal

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator, model_validator

# ---------------------------------------------------------------------------
# Logging — configure before any validation so error messages are visible
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment loading
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Startup validation
# ---------------------------------------------------------------------------

# Requirement 2.1 / 2.5 — AWS_BEARER_TOKEN_BEDROCK is mandatory
aws_bearer_token = os.environ.get("AWS_BEARER_TOKEN_BEDROCK", "").strip()
if not aws_bearer_token:
    logger.error("ERROR: AWS_BEARER_TOKEN_BEDROCK is not set or empty")
    sys.exit(1)

# Requirement 2.2 — AWS_REGION with default
aws_region: str = os.environ.get("AWS_REGION", "us-east-1")

# Requirement 2.3 — BEDROCK_MODEL_ID with default
bedrock_model_id: str = os.environ.get(
    "BEDROCK_MODEL_ID",
    "anthropic.claude-3-5-sonnet-20241022-v2:0",
)

# Requirement 7.2 — Optional auth validation
auth_enabled: bool = os.environ.get("AUTH_ENABLED", "false").strip().lower() == "true"

if auth_enabled:
    auth_username = os.environ.get("AUTH_USERNAME", "").strip()
    if not auth_username:
        logger.error("ERROR: AUTH_USERNAME is not set or empty")
        sys.exit(1)

    auth_password = os.environ.get("AUTH_PASSWORD", "").strip()
    if not auth_password:
        logger.error("ERROR: AUTH_PASSWORD is not set or empty")
        sys.exit(1)
else:
    auth_username = os.environ.get("AUTH_USERNAME", "")
    auth_password = os.environ.get("AUTH_PASSWORD", "")

# ---------------------------------------------------------------------------
# BedrockClient — module-level singleton (Requirement 6.1, 6.2)
# ---------------------------------------------------------------------------

# Requirement 6.1 — ensure the bearer token is set in os.environ so that
# boto3's bearer token credential provider picks it up automatically.
os.environ["AWS_BEARER_TOKEN_BEDROCK"] = aws_bearer_token

# Construct the client once at startup; reused for every request.
bedrock_client = boto3.client("bedrock-runtime", region_name=aws_region)


async def stream_response(messages: list[dict]) -> AsyncGenerator[str, None]:
    """Call Bedrock converse_stream and yield SSE-formatted strings.

    Yields:
        ``data: <token>\\n\\n`` for each content delta token.
        ``event: done\\ndata: \\n\\n`` when the stream ends normally.
        ``event: error\\ndata: <message>\\n\\n`` on any Bedrock error.
    """
    try:
        response = bedrock_client.converse_stream(
            modelId=bedrock_model_id,
            messages=messages,
            inferenceConfig={"maxTokens": 8192},
        )

        stream = response.get("stream")
        if stream is None:
            yield "event: error\ndata: Bedrock returned no stream.\n\n"
            return

        for event in stream:
            # contentBlockDelta carries incremental text tokens
            if "contentBlockDelta" in event:
                delta = event["contentBlockDelta"].get("delta", {})
                text = delta.get("text", "")
                if text:
                    yield f"data: {text}\n\n"

    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]

        if error_code == "ThrottlingException":
            yield (
                "event: error\n"
                "data: Request throttled by AWS Bedrock. Please try again.\n\n"
            )
        elif error_code in ("UnauthorizedException", "AccessDeniedException"):
            yield (
                "event: error\n"
                "data: Invalid or unauthorized API key. "
                "Check AWS_BEARER_TOKEN_BEDROCK.\n\n"
            )
        else:
            reason = exc.response["Error"].get("Message", str(exc))
            yield f"event: error\ndata: Bedrock service error: {reason}\n\n"
        return

    # Signal stream completion
    yield "event: done\ndata: \n\n"

# ---------------------------------------------------------------------------
# FastAPI application instance
# ---------------------------------------------------------------------------
app = FastAPI()

# ---------------------------------------------------------------------------
# Pydantic models (Requirements 4.1, 4.2, 4.4)
# ---------------------------------------------------------------------------


class Message(BaseModel):
    """A single conversation turn."""

    role: Literal["user", "assistant"]
    content: str

    @field_validator("content")
    @classmethod
    def content_must_not_be_whitespace_only(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content must not be whitespace-only")
        return v


class ChatRequest(BaseModel):
    """Request body for POST /chat."""

    messages: list[Message]

    @model_validator(mode="after")
    def validate_messages(self) -> "ChatRequest":
        if not self.messages:
            raise ValueError("messages must be non-empty")
        if self.messages[-1].role != "user":
            raise ValueError("last message must have role 'user'")
        return self


# ---------------------------------------------------------------------------
# Helper: prune conversation history to at most 100 turns (Requirement 5.5)
# ---------------------------------------------------------------------------
MAX_TURNS = 100


def prune_history(messages: list[dict]) -> tuple[list[dict], bool]:
    """Return (pruned_messages, was_pruned).

    A "turn" is one user/assistant pair (2 messages). 100 turns = 200 messages.
    If the list exceeds 200 messages, remove the oldest pairs until ≤ 200.
    """
    max_messages = MAX_TURNS * 2
    if len(messages) <= max_messages:
        return messages, False

    # Keep only the most recent max_messages entries.
    # Ensure we start on a user message (even index from the original start).
    pruned = messages[-max_messages:]
    # If the first message after pruning is an assistant turn, drop it so the
    # list always starts with a user message.
    if pruned and pruned[0]["role"] == "assistant":
        pruned = pruned[1:]
    return pruned, True


# ---------------------------------------------------------------------------
# POST /chat route (Requirements 4.1, 4.2, 4.4, 4.5, 5.2, 5.5, 8.5, 8.6, 8.7)
# ---------------------------------------------------------------------------


@app.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    """Accept a chat request and return a streaming SSE response."""
    try:
        # Requirement 8.5 — log incoming user message at INFO
        last_user_msg = request.messages[-1].content
        logger.info("Incoming user message: %s", last_user_msg)

        # Convert Pydantic models to plain dicts for boto3
        messages_dicts = [m.model_dump() for m in request.messages]

        # Requirement 5.5 — apply 100-turn pruning
        messages_dicts, was_pruned = prune_history(messages_dicts)
        if was_pruned:
            logger.info(
                "Conversation history pruned to %d messages (100-turn cap applied).",
                len(messages_dicts),
            )

        # Requirement 8.5 — log Bedrock API invocation at INFO
        logger.info(
            "Invoking Bedrock model %s with %d messages.",
            bedrock_model_id,
            len(messages_dicts),
        )

        async def generate() -> AsyncGenerator[str, None]:
            """Wrap stream_response, formatting SSE events."""
            pruning_notice_sent = was_pruned
            if pruning_notice_sent:
                # Notify the frontend that history was pruned (Requirement 5.7)
                yield "event: pruned\ndata: Older messages have been removed from context.\n\n"

            async for chunk in stream_response(messages_dicts):
                yield chunk

        return StreamingResponse(generate(), media_type="text/event-stream")

    except Exception:
        # Requirement 8.7 — log full stack trace at ERROR, return HTTP 500
        logger.error(
            "Unexpected exception in /chat route:\n%s", traceback.format_exc()
        )
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail="Internal server error")


# ---------------------------------------------------------------------------
# Application entry point (uvicorn wiring added in a later task)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    logger.info("Starting bedrock-chat-app on 0.0.0.0:3000")
    uvicorn.run(app, host="0.0.0.0", port=3000)
