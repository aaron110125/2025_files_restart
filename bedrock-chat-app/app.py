"""
bedrock-chat-app — single-file FastAPI application.

This module is the entry point. On import / startup it:
  1. Loads environment variables from .env
  2. Validates required variables and exits with code 1 on failure
  3. Constructs the boto3 Bedrock client as a module-level singleton
  4. Registers routes, serves the embedded frontend, etc.
"""

import base64
import binascii
import logging
import os
import sys
import traceback
from typing import AsyncGenerator, Dict, List, Literal, Tuple

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from pydantic import BaseModel, field_validator, model_validator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

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

# Support both IAM credentials (access key/secret key) and ABSK bearer tokens.
# IAM credentials take priority if both AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set.
aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID", "").strip()
aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "").strip()
aws_bearer_token = os.environ.get("AWS_BEARER_TOKEN_BEDROCK", "").strip()

if not aws_access_key and not aws_bearer_token:
    logger.error("ERROR: Either AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY or AWS_BEARER_TOKEN_BEDROCK must be set")
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

from botocore.config import Config as BotoConfig  # noqa: E402

if aws_access_key and aws_secret_key:
    # Use standard IAM credentials (access key + secret key)
    logger.info("Using IAM credentials for Bedrock authentication")
    aws_session_token = os.environ.get("AWS_SESSION_TOKEN", "").strip() or None
    _session = boto3.Session(
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        aws_session_token=aws_session_token,
        region_name=aws_region,
    )
    bedrock_client = _session.client("bedrock-runtime")
else:
    # Fallback: Use ABSK bearer token authentication
    logger.info("Using ABSK bearer token for Bedrock authentication")
    os.environ["AWS_BEARER_TOKEN_BEDROCK"] = aws_bearer_token

    _session = boto3.Session(region_name=aws_region)
    bedrock_client = _session.client(
        "bedrock-runtime",
        endpoint_url=f"https://bedrock-runtime.{aws_region}.amazonaws.com",
        config=BotoConfig(
            signature_version="bearer",
            request_min_compression_size_bytes=1024,
        ),
    )

    # Inject the bearer token into the Authorization header
    import botocore.auth  # noqa: E402

    def _patched_add_auth(self, request, **kwargs):
        """Inject the ABSK bearer token into the Authorization header."""
        request.headers["Authorization"] = f"Bearer {aws_bearer_token}"
        return

    botocore.auth.BearerAuth.add_auth = _patched_add_auth


async def stream_response(messages: List[Dict]) -> AsyncGenerator[str, None]:
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
# BasicAuthMiddleware (Requirements 7.1, 7.3, 7.4)
# ---------------------------------------------------------------------------

_WWW_AUTH_HEADER = 'Basic realm="Bedrock Chat"'


class BasicAuthMiddleware(BaseHTTPMiddleware):
    """HTTP Basic Authentication middleware.

    Only added to the app when AUTH_ENABLED=true.  Parses the
    ``Authorization: Basic <b64>`` header and returns HTTP 401 with a
    ``WWW-Authenticate`` challenge if the header is absent, malformed, or
    the decoded credentials do not match (case-sensitive) the configured
    AUTH_USERNAME / AUTH_PASSWORD.
    """

    def __init__(self, app: ASGIApp, username: str, password: str) -> None:
        super().__init__(app)
        self._username = username
        self._password = password

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        auth_header = request.headers.get("Authorization", "")

        # Must be "Basic <token>"
        if not auth_header.startswith("Basic "):
            return self._unauthorized()

        encoded = auth_header[len("Basic "):]
        try:
            decoded = base64.b64decode(encoded).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError):
            return self._unauthorized()

        # Credentials must contain exactly one colon
        if ":" not in decoded:
            return self._unauthorized()

        # Split on the first colon only — passwords may contain colons
        username, password = decoded.split(":", 1)

        if username != self._username or password != self._password:
            return self._unauthorized()

        return await call_next(request)

    @staticmethod
    def _unauthorized() -> Response:
        return Response(
            content="Unauthorized",
            status_code=401,
            headers={"WWW-Authenticate": _WWW_AUTH_HEADER},
        )


# ---------------------------------------------------------------------------
# FastAPI application instance
# ---------------------------------------------------------------------------
app = FastAPI()

# Conditionally register BasicAuthMiddleware (Requirement 7.1)
if auth_enabled:
    app.add_middleware(BasicAuthMiddleware, username=auth_username, password=auth_password)

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

    messages: List[Message]

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


def prune_history(messages: List[Dict]) -> Tuple[List[Dict], bool]:
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

        # Convert Pydantic models to Bedrock's expected format:
        # {"role": "user"|"assistant", "content": [{"text": "..."}]}
        messages_dicts = [
            {"role": m.role, "content": [{"text": m.content}]}
            for m in request.messages
        ]

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
# Embedded Chat_Interface HTML/CSS/JS (Requirements 3.1–3.11, 4.3, 4.6, 4.7, 5.1, 5.3–5.7)
# ---------------------------------------------------------------------------

CHAT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bedrock Chat</title>
    <script src="https://cdn.jsdelivr.net/npm/marked@12/marked.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 20px;
            background: #16213e;
            border-bottom: 1px solid #0f3460;
        }
        header h1 { font-size: 1.2rem; color: #e94560; }
        #new-chat-btn {
            background: #0f3460;
            color: #eee;
            border: 1px solid #e94560;
            padding: 6px 14px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85rem;
        }
        #new-chat-btn:hover { background: #e94560; color: #fff; }
        #chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .message {
            max-width: 75%;
            padding: 12px 16px;
            border-radius: 12px;
            line-height: 1.5;
            word-wrap: break-word;
        }
        .message.user {
            align-self: flex-end;
            background: #0f3460;
            border-bottom-right-radius: 4px;
        }
        .message.assistant {
            align-self: flex-start;
            background: #16213e;
            border: 1px solid #0f3460;
            border-bottom-left-radius: 4px;
        }
        .message.system {
            align-self: center;
            background: #533483;
            font-size: 0.85rem;
            color: #ddd;
            padding: 8px 14px;
            border-radius: 8px;
        }
        .message.assistant pre {
            background: #0d1b2a;
            padding: 10px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 8px 0;
        }
        .message.assistant code {
            background: #0d1b2a;
            padding: 2px 5px;
            border-radius: 3px;
            font-size: 0.9em;
        }
        .message.assistant pre code {
            background: none;
            padding: 0;
        }
        #loading {
            display: none;
            align-self: flex-start;
            padding: 12px 16px;
        }
        #loading .dots span {
            display: inline-block;
            width: 8px;
            height: 8px;
            margin: 0 3px;
            background: #e94560;
            border-radius: 50%;
            animation: bounce 1.4s infinite both;
        }
        #loading .dots span:nth-child(2) { animation-delay: 0.2s; }
        #loading .dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
        #input-area {
            display: flex;
            gap: 10px;
            padding: 16px 20px;
            background: #16213e;
            border-top: 1px solid #0f3460;
        }
        #message-input {
            flex: 1;
            padding: 12px 16px;
            border: 1px solid #0f3460;
            border-radius: 8px;
            background: #1a1a2e;
            color: #eee;
            font-size: 1rem;
            resize: none;
            min-height: 44px;
            max-height: 120px;
            outline: none;
        }
        #message-input:focus { border-color: #e94560; }
        #send-btn {
            padding: 12px 20px;
            background: #e94560;
            color: #fff;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
        }
        #send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        #send-btn:hover:not(:disabled) { background: #c73e54; }
    </style>
</head>
<body>
    <header>
        <h1>Bedrock Chat</h1>
        <button id="new-chat-btn">New Chat</button>
    </header>
    <div id="chat-container">
        <div id="loading"><div class="dots"><span></span><span></span><span></span></div></div>
    </div>
    <div id="input-area">
        <textarea id="message-input" placeholder="Type a message..." maxlength="4000" rows="1"></textarea>
        <button id="send-btn">Send</button>
    </div>

    <script>
    (function() {
        const chatContainer = document.getElementById('chat-container');
        const loadingEl = document.getElementById('loading');
        const messageInput = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');
        const newChatBtn = document.getElementById('new-chat-btn');

        let abortController = null;
        let isStreaming = false;

        // --- History Management ---
        function getHistory() {
            try {
                const raw = sessionStorage.getItem('Conversation_History');
                return raw ? JSON.parse(raw) : [];
            } catch { return []; }
        }

        function setHistory(history) {
            sessionStorage.setItem('Conversation_History', JSON.stringify(history));
        }

        function appendToHistory(role, content) {
            const history = getHistory();
            history.push({ role, content });
            setHistory(history);
        }

        // --- UI Helpers ---
        function scrollToBottom() {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function addMessageBubble(role, content, isHtml) {
            const div = document.createElement('div');
            div.className = 'message ' + role;
            if (isHtml) {
                div.innerHTML = content;
            } else {
                div.textContent = content;
            }
            chatContainer.insertBefore(div, loadingEl);
            scrollToBottom();
            return div;
        }

        function addSystemMessage(text) {
            addMessageBubble('system', text, false);
        }

        function showLoading() { loadingEl.style.display = 'block'; scrollToBottom(); }
        function hideLoading() { loadingEl.style.display = 'none'; }

        function setInputEnabled(enabled) {
            messageInput.disabled = !enabled;
            sendBtn.disabled = !enabled;
            if (enabled) messageInput.focus();
        }

        // --- Render history on page load ---
        function renderHistory() {
            // Remove all messages except loading
            const msgs = chatContainer.querySelectorAll('.message');
            msgs.forEach(m => m.remove());
            const history = getHistory();
            history.forEach(msg => {
                if (msg.role === 'assistant') {
                    addMessageBubble('assistant', marked.parse(msg.content), true);
                } else {
                    addMessageBubble('user', msg.content, false);
                }
            });
        }

        // --- Submit Message ---
        async function submitMessage() {
            const text = messageInput.value.trim();
            if (!text) {
                messageInput.focus();
                return;
            }

            // Clear input immediately
            messageInput.value = '';
            messageInput.style.height = 'auto';

            // Add user bubble
            addMessageBubble('user', text, false);
            appendToHistory('user', text);

            // Prepare request
            const history = getHistory();
            setInputEnabled(false);
            showLoading();

            abortController = new AbortController();
            const signal = abortController.signal;

            // 30-second timeout for first token
            let firstTokenReceived = false;
            const timeoutId = setTimeout(() => {
                if (!firstTokenReceived && abortController) {
                    abortController.abort();
                    hideLoading();
                    setInputEnabled(true);
                    addSystemMessage('Response timed out. Please try again.');
                }
            }, 30000);

            let assistantText = '';
            let assistantBubble = null;
            let streamDone = false;

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ messages: history }),
                    signal: signal
                });

                if (!response.ok) {
                    clearTimeout(timeoutId);
                    hideLoading();
                    setInputEnabled(true);
                    addSystemMessage('Error: Server returned ' + response.status);
                    return;
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\\n');
                    buffer = lines.pop() || '';

                    for (const line of lines) {
                        if (line.startsWith('event: done')) {
                            streamDone = true;
                            clearTimeout(timeoutId);
                            hideLoading();
                            // Final Markdown render
                            if (assistantBubble && assistantText) {
                                assistantBubble.innerHTML = marked.parse(assistantText);
                                scrollToBottom();
                            }
                            appendToHistory('assistant', assistantText);
                            setInputEnabled(true);
                        } else if (line.startsWith('event: error')) {
                            // Next data: line has the error message
                            continue;
                        } else if (line.startsWith('event: pruned')) {
                            // Next data: line has the pruning notice
                            continue;
                        } else if (line.startsWith('data: ') && !streamDone) {
                            const token = line.slice(6);
                            // Check if previous event was error or pruned
                            const prevLines = lines.slice(0, lines.indexOf(line));
                            const lastEvent = [...prevLines].reverse().find(l => l.startsWith('event:'));

                            if (lastEvent && lastEvent.startsWith('event: error')) {
                                clearTimeout(timeoutId);
                                hideLoading();
                                setInputEnabled(true);
                                addSystemMessage(token || 'An error occurred.');
                                // Remove user message from history on error
                                const h = getHistory();
                                if (h.length > 0 && h[h.length - 1].role === 'user') {
                                    h.pop();
                                    setHistory(h);
                                }
                                return;
                            } else if (lastEvent && lastEvent.startsWith('event: pruned')) {
                                addSystemMessage(token || 'Older messages removed from context.');
                                continue;
                            }

                            // Normal token
                            if (!firstTokenReceived) {
                                firstTokenReceived = true;
                                clearTimeout(timeoutId);
                                hideLoading();
                            }
                            assistantText += token;
                            if (!assistantBubble) {
                                assistantBubble = addMessageBubble('assistant', '', false);
                            }
                            assistantBubble.textContent = assistantText;
                            scrollToBottom();
                        }
                    }
                }

                // If stream ended without a done event
                if (!streamDone && assistantText) {
                    clearTimeout(timeoutId);
                    hideLoading();
                    setInputEnabled(true);
                    addSystemMessage('Connection lost. Response may be incomplete.');
                } else if (!streamDone && !assistantText) {
                    clearTimeout(timeoutId);
                    hideLoading();
                    setInputEnabled(true);
                    addSystemMessage('Connection lost. Please try again.');
                }

            } catch (err) {
                clearTimeout(timeoutId);
                hideLoading();
                setInputEnabled(true);
                if (err.name === 'AbortError') {
                    // Timeout or user-initiated cancel — already handled
                } else {
                    addSystemMessage('Connection lost. Please try again.');
                }
            } finally {
                abortController = null;
                isStreaming = false;
            }
        }

        // --- Event Listeners ---
        sendBtn.addEventListener('click', submitMessage);

        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submitMessage();
            }
        });

        // Auto-resize textarea
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });

        newChatBtn.addEventListener('click', function() {
            if (abortController) {
                abortController.abort();
                abortController = null;
            }
            sessionStorage.removeItem('Conversation_History');
            const msgs = chatContainer.querySelectorAll('.message');
            msgs.forEach(m => m.remove());
            hideLoading();
            setInputEnabled(true);
            messageInput.value = '';
        });

        // Render existing history on load
        renderHistory();
        messageInput.focus();
    })();
    </script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# GET / route — serve the embedded Chat_Interface (Requirements 1.1, 1.4, 8.1, 8.4)
# ---------------------------------------------------------------------------


@app.get("/")
async def index() -> HTMLResponse:
    """Serve the embedded chat interface."""
    return HTMLResponse(content=CHAT_HTML)


# ---------------------------------------------------------------------------
# Application entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    logger.info("Starting bedrock-chat-app on 0.0.0.0:3000")
    uvicorn.run(app, host="0.0.0.0", port=3000)
