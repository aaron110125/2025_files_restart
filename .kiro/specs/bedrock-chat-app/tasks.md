# Implementation Plan: bedrock-chat-app

## Overview

Implement a single-file Python FastAPI web application that streams Claude 3.5 Sonnet responses to a browser via SSE. The frontend is embedded HTML/CSS/JS served directly from `app.py`. Tasks are ordered to build the core server skeleton first, then add streaming, conversation history, auth, the frontend, and finally tests.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create `requirements.txt` with pinned versions: `fastapi==0.115.*`, `uvicorn==0.30.*`, `boto3==1.35.*`, `python-dotenv==1.0.*`, `hypothesis==6.112.0`, and `pytest`, `pytest-asyncio`, `httpx` for testing
  - Create `.env.example` with placeholder values and inline comments for all six variables: `AWS_BEARER_TOKEN_BEDROCK`, `AWS_REGION`, `BEDROCK_MODEL_ID`, `AUTH_ENABLED`, `AUTH_USERNAME`, `AUTH_PASSWORD`
  - Create `tests/` directory with empty `__init__.py` and `conftest.py`
  - _Requirements: 2.6, 8.2_

- [x] 2. Implement startup validation and environment loading
  - [x] 2.1 Write startup validation logic in `app.py`
    - Call `load_dotenv()` at module top
    - Read `AWS_BEARER_TOKEN_BEDROCK`; if absent or empty, log `ERROR: AWS_BEARER_TOKEN_BEDROCK is not set or empty` and call `sys.exit(1)`
    - Read `AWS_REGION` (default `us-east-1`) and `BEDROCK_MODEL_ID` (default `anthropic.claude-3-5-sonnet-20241022-v2:0`)
    - If `AUTH_ENABLED=true`, validate `AUTH_USERNAME` and `AUTH_PASSWORD` are present; exit with code 1 and an error log if either is missing
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 7.2_

  - [x] 2.2 Write unit tests for startup validation in `tests/test_startup.py`
    - Test exit code 1 when `AWS_BEARER_TOKEN_BEDROCK` is missing or empty
    - Test exit code 1 when `AUTH_ENABLED=true` and `AUTH_USERNAME` or `AUTH_PASSWORD` is missing
    - Test successful initialization with all required vars present
    - Test default values applied for `AWS_REGION` and `BEDROCK_MODEL_ID`
    - _Requirements: 2.2, 2.3, 2.4, 2.5, 7.2_

- [ ] 3. Implement the boto3 Bedrock client and streaming generator
  - [x] 3.1 Implement `BedrockClient` module-level singleton and `stream_response` in `app.py`
    - Set `os.environ["AWS_BEARER_TOKEN_BEDROCK"]` before constructing the boto3 client
    - Construct `boto3.client("bedrock-runtime", region_name=aws_region)` once at startup
    - Implement `async def stream_response(messages)` that calls `converse_stream` with `modelId` and `inferenceConfig={"maxTokens": 8192}`
    - Yield `contentBlockDelta` text chunks; handle `ThrottlingException`, `UnauthorizedException`, `AccessDeniedException`, and generic `ClientError` by yielding the appropriate SSE error event strings
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

  - [-] 3.2 Write property test for SSE stream token forwarding (Property 4)
    - **Property 4: SSE stream faithfully forwards all Bedrock tokens and errors**
    - **Validates: Requirements 4.2, 4.5, 6.5, 6.6, 6.7**
    - Use `st.lists(st.text(min_size=1), min_size=1)` to generate token sequences; assert each token appears as a `data:` event in order
    - Use `st.sampled_from([ThrottlingException, ClientError])` to generate errors; assert exactly one `event: error` event with non-empty message
    - Tag: `# Feature: bedrock-chat-app, Property 4: SSE stream faithfully forwards all Bedrock tokens and errors`
    - _File: `tests/test_streaming.py`_

  - [-] 3.3 Write property test for max_tokens range (Property 8)
    - **Property 8: max_tokens is always within the valid range**
    - **Validates: Requirements 6.4**
    - Assert `inferenceConfig.maxTokens` satisfies `4096 ≤ maxTokens ≤ 8192` on every mock invocation
    - Tag: `# Feature: bedrock-chat-app, Property 8: max_tokens is always within the valid range`
    - _File: `tests/test_streaming.py`_

- [ ] 4. Implement the `POST /chat` route handler
  - [x] 4.1 Define `Message` and `ChatRequest` Pydantic models and the `/chat` route in `app.py`
    - `Message`: `role: Literal["user", "assistant"]`, `content: str`
    - `ChatRequest`: `messages: list[Message]`; validate non-empty list, last message role is `user`, no whitespace-only content
    - Route logs incoming user message at INFO, applies 100-turn pruning, logs Bedrock invocation at INFO, returns `StreamingResponse(media_type="text/event-stream")` wrapping the async generator
    - Format tokens as `data: <token>\n\n`; send `event: done\ndata: \n\n` on completion; send `event: error\ndata: <msg>\n\n` on error
    - On unexpected exception: log full stack trace at ERROR, return HTTP 500 `{"detail": "Internal server error"}`
    - _Requirements: 4.1, 4.2, 4.4, 4.5, 5.2, 5.5, 8.5, 8.6, 8.7_

  - [~] 4.2 Write unit tests for the `/chat` route in `tests/test_routes.py`
    - Test HTTP 422 for empty messages list
    - Test HTTP 422 when last message role is not `user`
    - Test SSE stream ends with `event: done` after successful mock response
    - Test `event: error` is sent for `ThrottlingException`, `UnauthorizedException`, and generic `ClientError`
    - _Requirements: 4.2, 4.4, 4.5, 6.5, 6.6, 6.7_

  - [~] 4.3 Write property test for conversation history pruning (Property 6)
    - **Property 6: Conversation history pruning preserves recency and enforces the 100-turn cap**
    - **Validates: Requirements 5.5**
    - Use `st.integers(min_value=101, max_value=500)` for history length; assert pruned history has ≤ 100 turns and contains the most recent turns in original order
    - Tag: `# Feature: bedrock-chat-app, Property 6: Conversation history pruning preserves recency and enforces the 100-turn cap`
    - _File: `tests/test_history.py`_

  - [~] 4.4 Write property test for INFO logging (Property 10)
    - **Property 10: INFO log entry for every user message and Bedrock invocation**
    - **Validates: Requirements 8.5**
    - Use `st.text(min_size=1).filter(lambda s: s.strip())` for message content; assert log contains at least one INFO entry referencing the message and one INFO entry for the Bedrock invocation
    - Tag: `# Feature: bedrock-chat-app, Property 10: INFO log entry for every user message and Bedrock invocation`
    - _File: `tests/test_routes.py`_

  - [~] 4.5 Write property test for error HTTP 500 and ERROR log (Property 11)
    - **Property 11: Handled errors produce HTTP 500 and an ERROR log entry**
    - **Validates: Requirements 8.6**
    - Use `st.sampled_from` of known error types; assert HTTP response status is 500 and log contains an ERROR-level entry with error type and message
    - Tag: `# Feature: bedrock-chat-app, Property 11: Handled errors produce HTTP 500 and an ERROR log entry`
    - _File: `tests/test_routes.py`_

- [~] 5. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement `BasicAuthMiddleware` and the `GET /` route
  - [~] 6.1 Implement `BasicAuthMiddleware` Starlette middleware in `app.py`
    - Subclass `BaseHTTPMiddleware`; only added to the app when `AUTH_ENABLED=true`
    - Parse `Authorization: Basic <b64>` header; return HTTP 401 with `WWW-Authenticate: Basic realm="Bedrock Chat"` if absent, malformed, or credentials don't match (case-sensitive)
    - Call `await call_next(request)` on success
    - _Requirements: 7.1, 7.3, 7.4_

  - [~] 6.2 Implement `GET /` route that serves the embedded HTML page
    - Return the Chat_Interface HTML string as an `HTMLResponse`
    - Log bound address `0.0.0.0:3000` at INFO in the `uvicorn.run` call block
    - _Requirements: 1.1, 1.4, 8.1, 8.4_

  - [~] 6.3 Write unit tests for auth middleware in `tests/test_auth.py`
    - Test `AUTH_ENABLED=false` allows unauthenticated access to all routes
    - Test HTTP 401 returned when no credentials provided and `AUTH_ENABLED=true`
    - Test HTTP 401 returned for wrong credentials
    - Test HTTP 200 returned for correct credentials
    - _Requirements: 7.1, 7.3, 7.4_

  - [~] 6.4 Write property test for auth rejection (Property 9)
    - **Property 9: Auth middleware rejects any request without valid credentials**
    - **Validates: Requirements 7.1, 7.3**
    - Use `st.text()` for username/password pairs that don't match configured values; assert HTTP 401 with `WWW-Authenticate: Basic realm="Bedrock Chat"` header
    - Tag: `# Feature: bedrock-chat-app, Property 9: Auth middleware rejects any request without valid credentials`
    - _File: `tests/test_auth.py`_

- [ ] 7. Implement the embedded Chat_Interface HTML/CSS/JS
  - [~] 7.1 Write the HTML skeleton and CSS styles embedded in `app.py`
    - Scrollable conversation history; user messages right-aligned with distinct background; assistant messages left-aligned
    - Text input (max 4000 chars) and send button
    - Loading indicator (animated dots)
    - "New Chat" button
    - Include marked.js 12.x via CDN for Markdown rendering
    - _Requirements: 3.1, 3.2, 3.3, 3.8_

  - [~] 7.2 Write the JavaScript for message submission, SSE streaming, and history management
    - Store `Conversation_History` in `sessionStorage` as a JSON array of `{role, content}` objects
    - On submit (Enter without Shift, or send button click): validate non-empty/non-whitespace, POST to `/chat` with full history, read `ReadableStream` response body to consume SSE events
    - Append tokens to current assistant bubble without full re-render; use `marked.parse()` for final render on `event: done`
    - On `event: done`: dismiss loading indicator, re-enable input, append assistant message to `sessionStorage`
    - On `event: error`: display error as system message, re-enable input, do NOT append to history
    - 30-second timeout for first token; display "Response timed out" on timeout
    - On SSE connection drop without `done`: display "Connection lost" error
    - Clear input field after every valid submission; retain focus on input if submission rejected
    - Scroll to latest message on every new message
    - Display pruning notice as system message when backend prunes history
    - "New Chat": cancel in-flight `AbortController`, clear `sessionStorage`, reset UI
    - _Requirements: 3.4, 3.5, 3.6, 3.7, 3.9, 3.10, 3.11, 4.3, 4.6, 4.7, 5.1, 5.3, 5.4, 5.6, 5.7_

- [~] 8. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Write property and unit tests for frontend-observable behaviors
  - [~] 9.1 Write property test for input cleared after submission (Property 1)
    - **Property 1: Input field cleared after any valid submission**
    - **Validates: Requirements 3.6**
    - Use `st.text(min_size=1).filter(lambda s: s.strip())` for message content; assert input field value is empty immediately after submission
    - Tag: `# Feature: bedrock-chat-app, Property 1: Input field cleared after any valid submission`
    - _File: `tests/test_markdown.py` or a dedicated frontend test_

  - [~] 9.2 Write property test for whitespace rejection (Property 2)
    - **Property 2: Whitespace-only messages are rejected**
    - **Validates: Requirements 3.11**
    - Use `st.text(alphabet=st.characters(whitelist_categories=("Zs", "Cc")), min_size=1)` for whitespace strings; assert message list unchanged and no request sent
    - Tag: `# Feature: bedrock-chat-app, Property 2: Whitespace-only messages are rejected`
    - _File: `tests/test_routes.py`_

  - [~] 9.3 Write property test for Markdown rendering (Property 3)
    - **Property 3: Markdown rendering produces correct HTML elements**
    - **Validates: Requirements 3.8**
    - Use `st.sampled_from(["**bold**", "*italic*", "`code`", "- item"])` combined with `st.text()`; assert rendered output contains `<strong>`, `<em>`, `<code>`, `<pre>`, `<ul>/<li>` as appropriate
    - Tag: `# Feature: bedrock-chat-app, Property 3: Markdown rendering produces correct HTML elements`
    - _File: `tests/test_markdown.py`_

  - [~] 9.4 Write property test for history round-trip integrity (Property 5)
    - **Property 5: Conversation history round-trip integrity**
    - **Validates: Requirements 5.2, 5.3**
    - Use `st.text(min_size=1).filter(lambda s: s.strip())` for message content; assert submitted user message appears in the `messages` array forwarded to Bedrock, and completed assistant response appears in `sessionStorage` as an `assistant` role entry
    - Tag: `# Feature: bedrock-chat-app, Property 5: Conversation history round-trip integrity`
    - _File: `tests/test_history.py`_

  - [~] 9.5 Write property test for failed response not mutating history (Property 7)
    - **Property 7: Failed Bedrock responses do not mutate conversation history**
    - **Validates: Requirements 5.6**
    - Use `st.sampled_from([ThrottlingException, ClientError, ConnectionError])` for error types; assert history after failed request is identical to history before the request
    - Tag: `# Feature: bedrock-chat-app, Property 7: Failed Bedrock responses do not mutate conversation history`
    - _File: `tests/test_history.py`_

- [ ] 10. Write README.md and wire everything together
  - [~] 10.1 Create `README.md` with setup instructions and deployment guidance
    - Step-by-step setup: virtual environment creation, `pip install -r requirements.txt`, `.env` configuration, `python app.py`
    - Section on public exposure via tunnels: Cloudflare Tunnel (`cloudflared tunnel --url http://localhost:3000`), ngrok (`ngrok http 3000`), enabling `AUTH_ENABLED`
    - Section on cloud deployment listing all six environment variables for Railway and Fly.io
    - _Requirements: 7.5, 7.6, 8.3_

  - [~] 10.2 Verify end-to-end wiring in `tests/test_integration.py`
    - Write integration test: submit a message with a mocked Bedrock client, receive streamed SSE response, verify history is updated
    - Write integration test: auth middleware blocks unauthenticated requests when `AUTH_ENABLED=true`
    - Write integration test: `GET /` returns HTML with status 200
    - _Requirements: 1.1, 1.2, 7.1_

- [~] 11. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at logical milestones
- Property tests use Hypothesis with `@settings(max_examples=100)` and the tag format `# Feature: bedrock-chat-app, Property <N>: <text>`
- Unit tests complement property tests by covering specific examples and edge cases
- The entire application lives in a single `app.py` — all tasks write to or test that file plus the `tests/` directory

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["2.1"] },
    { "id": 1, "tasks": ["2.2", "3.1"] },
    { "id": 2, "tasks": ["3.2", "3.3", "4.1"] },
    { "id": 3, "tasks": ["4.2", "4.3", "4.4", "4.5", "6.1", "6.2"] },
    { "id": 4, "tasks": ["6.3", "6.4", "7.1"] },
    { "id": 5, "tasks": ["7.2"] },
    { "id": 6, "tasks": ["9.1", "9.2", "9.3", "9.4", "9.5", "10.1"] },
    { "id": 7, "tasks": ["10.2"] }
  ]
}
```
