# Requirements Document

## Introduction

A local web chat application that provides a clean, ChatGPT-like interface for interacting with AWS Bedrock's Claude 3.5 Sonnet model. The app runs on a Python FastAPI backend, serves on `0.0.0.0:3000` so it is reachable from both `localhost` and other devices on the same local network (e.g., a phone via `http://<mac-ip>:3000`), and supports real-time streaming responses. The API key (ABSK format) and AWS region are stored in a `.env` file. An extended scope covers optional public exposure via a tunnel (ngrok/Cloudflare) or cloud deployment (Railway, Fly.io) with basic password authentication to protect the Bedrock API key.

## Glossary

- **App**: The FastAPI-based web chat application described in this document.
- **Bedrock_Client**: The AWS Bedrock Runtime client responsible for invoking the Claude model.
- **Chat_Interface**: The browser-based UI that renders the conversation and accepts user input.
- **Message**: A single turn in the conversation, consisting of a role (`user` or `assistant`) and text content.
- **Conversation_History**: The ordered list of Messages maintained for the current session.
- **Stream**: The server-sent event (SSE) channel through which the App delivers incremental response tokens to the Chat_Interface.
- **API_Key**: The AWS Bedrock API key in ABSK format, used as a Bearer token via the `AWS_BEARER_TOKEN_BEDROCK` environment variable.
- **Auth_Middleware**: Optional HTTP Basic Authentication middleware that protects all routes when enabled.
- **Tunnel**: An optional reverse-proxy service (ngrok or Cloudflare Tunnel) that exposes the App to the public internet.

---

## Requirements

### Requirement 1: Server Binding and Local Network Accessibility

**User Story:** As a developer, I want the app to listen on all network interfaces so that I can access it from my Mac at `http://localhost:3000` and from my phone on the same Wi-Fi at `http://<mac-ip>:3000`.

#### Acceptance Criteria

1. THE App SHALL bind to host `0.0.0.0` and port `3000` when started with `python app.py`.
2. WHEN a client sends an HTTP request to port `3000` on any local network interface, THE App SHALL respond with a valid HTTP response.
3. THE App SHALL start without requiring any command-line arguments beyond `python app.py`.
4. WHEN the App starts successfully, THE App SHALL log the bound address (`0.0.0.0:3000`) at the INFO level so that the developer can confirm the server is listening.

---

### Requirement 2: Environment-Based Configuration

**User Story:** As a developer, I want credentials and configuration stored in a `.env` file so that secrets are not hard-coded in source files.

#### Acceptance Criteria

1. THE App SHALL read the AWS Bedrock API key (ABSK format) from the environment variable `AWS_BEARER_TOKEN_BEDROCK` defined in a `.env` file at the project root; this single key is used as a Bearer token and is the only credential required to authenticate with Bedrock.
2. THE App SHALL read the AWS region from the environment variable `AWS_REGION`, defaulting to `us-east-1` when the variable is absent.
3. THE App SHALL read the target model ID from the environment variable `BEDROCK_MODEL_ID`, defaulting to `anthropic.claude-3-5-sonnet-20241022-v2:0` when the variable is absent.
4. IF `AWS_BEARER_TOKEN_BEDROCK` is present and non-empty at startup, THEN THE App SHALL complete initialization and begin accepting incoming connections.
5. IF `AWS_BEARER_TOKEN_BEDROCK` is absent or empty at startup, THEN THE App SHALL immediately log an error message identifying the missing variable name and exit with a non-zero status code without attempting further initialization.
6. THE App SHALL provide a `.env.example` file that lists the variables `AWS_BEARER_TOKEN_BEDROCK`, `AWS_REGION`, `BEDROCK_MODEL_ID`, `AUTH_ENABLED`, `AUTH_USERNAME`, and `AUTH_PASSWORD`, each with a placeholder value and an inline comment explaining its purpose.

---

### Requirement 3: Chat Interface

**User Story:** As a user, I want a clean, ChatGPT-like chat interface so that I can have a natural conversation with the AI model in my browser.

#### Acceptance Criteria

1. THE Chat_Interface SHALL display a scrollable conversation history showing all Messages in the current session.
2. THE Chat_Interface SHALL display user Messages right-aligned and assistant Messages left-aligned, with visually distinct background colors for each role.
3. THE Chat_Interface SHALL provide a text input field (maximum 4000 characters) and a send button for composing and submitting new Messages.
4. WHEN the user presses the Enter key (without Shift) in the text input field, THE Chat_Interface SHALL submit exactly one Message, ignoring any simultaneous send button activation.
5. WHEN the user clicks the send button without simultaneously pressing Enter, THE Chat_Interface SHALL submit the Message.
6. WHEN a Message is submitted, THE Chat_Interface SHALL clear the text input field.
7. WHEN a Message is submitted, THE Chat_Interface SHALL scroll the conversation history to the latest Message.
8. THE Chat_Interface SHALL render both user and assistant Messages with basic Markdown formatting (bold, italic, inline code, code blocks, and bullet lists).
9. THE Chat_Interface SHALL display a visual loading indicator while awaiting the first token of a streaming response; IF no token is received within 30 seconds or the stream fails, THE Chat_Interface SHALL dismiss the loading indicator and display an error message in the conversation.
10. WHEN the user triggers the "New Chat" or "Clear" action while a stream is in progress, THE Chat_Interface SHALL cancel the in-flight stream before resetting the Conversation_History and clearing the display.
11. IF the submitted Message text is empty or whitespace-only, THE Chat_Interface SHALL NOT submit the Message and SHALL retain focus on the input field.

---

### Requirement 4: Streaming Responses

**User Story:** As a user, I want responses to appear word-by-word as they are generated so that I do not have to wait for the full response before reading it.

#### Acceptance Criteria

1. WHEN a user Message is submitted, THE App SHALL invoke the Bedrock_Client using the streaming API (`invoke_model_with_response_stream`).
2. WHEN the Bedrock_Client returns a stream, THE App SHALL forward each incremental text token to the Chat_Interface via a Server-Sent Events (SSE) endpoint.
3. WHEN the Chat_Interface receives a token via SSE, THE Chat_Interface SHALL append the token to the current assistant Message bubble without re-rendering the full conversation.
4. WHEN the stream ends, THE App SHALL send an SSE event with `event` field set to `done` so that THE Chat_Interface can dismiss the loading indicator, re-enable the message input, and mark the Message as complete.
5. IF the Bedrock_Client returns an error during streaming, THEN THE App SHALL send an SSE event with `event` field set to `error` containing a human-readable description of the failure.
6. WHEN the Chat_Interface receives an SSE event with `event` field set to `error`, THE Chat_Interface SHALL display the error message in the conversation and re-enable the message input.
7. IF the SSE connection drops mid-stream (network interruption or server close without a `done` event), THEN THE Chat_Interface SHALL display an error message indicating the connection was lost and re-enable the message input.

---

### Requirement 5: Conversation History Management

**User Story:** As a user, I want the app to remember the conversation context so that follow-up questions are answered correctly.

#### Acceptance Criteria

1. THE App SHALL maintain the Conversation_History for the duration of a browser session, where a session persists through page refresh but clears when the tab is closed or the user navigates away.
2. WHEN a new user Message is submitted, THE App SHALL append it to the Conversation_History before invoking the Bedrock_Client.
3. WHEN the Bedrock_Client returns a complete response, THE App SHALL append the full assistant Message to the Conversation_History.
4. WHEN the user triggers a "New Chat" action, THE App SHALL reset the Conversation_History to an empty state.
5. WHEN a Bedrock API request is made, THE App SHALL pass the full Conversation_History as the `messages` array; IF the Conversation_History exceeds 100 turns (50 user/assistant pairs), THE App SHALL prune the oldest pairs until the count is at or below 100 turns before sending the request.
6. IF the Bedrock_Client returns an error or the stream is interrupted, THEN THE App SHALL NOT append the failed assistant Message to the Conversation_History, and THE Chat_Interface SHALL display an error indication to the user.
7. WHEN the Conversation_History is pruned due to the 100-turn cap, THE Chat_Interface SHALL display a notice informing the user that older messages have been removed from context.

---

### Requirement 6: AWS Bedrock Integration

**User Story:** As a developer, I want the app to correctly authenticate with and invoke AWS Bedrock so that the Claude model responds to user messages.

#### Acceptance Criteria

1. THE Bedrock_Client SHALL authenticate using the `AWS_BEARER_TOKEN_BEDROCK` value as a Bearer token; THE App SHALL set this environment variable before constructing the boto3 `bedrock-runtime` client so that boto3 picks it up automatically via its bearer token credential provider — no `aws_access_key_id` or `aws_secret_access_key` are required or used.
2. THE Bedrock_Client SHALL target the AWS region specified by `AWS_REGION` (defaulting to `us-east-1`) by passing it as the `region_name` parameter at client construction time.
3. THE Bedrock_Client SHALL invoke the model specified by `BEDROCK_MODEL_ID` using the Anthropic Messages API format via the `converse_stream` API.
4. THE Bedrock_Client SHALL set a `max_tokens` value between `4096` and `8192` (inclusive) per request.
5. IF the Bedrock_Client receives a throttling error, THEN THE App SHALL send an SSE event with `event` field set to `error` and a message indicating the throttling failure.
6. IF the Bedrock_Client receives a service error that is not a throttling error, THEN THE App SHALL send an SSE event with `event` field set to `error` and a message indicating the service failure reason.
7. IF the Bedrock_Client receives an authentication or authorization error (invalid or expired Bearer token), THEN THE App SHALL send an SSE event with `event` field set to `error` and a message indicating the API key is invalid or unauthorized.

---

### Requirement 7: Optional Public Exposure with Authentication

**User Story:** As a developer, I want the option to expose the app publicly via a tunnel or cloud deployment with password protection so that my Bedrock API key is not accessible to unauthorized users.

#### Acceptance Criteria

1. WHERE the environment variable `AUTH_ENABLED` is set to `true`, THE Auth_Middleware SHALL require HTTP Basic Authentication on all routes.
2. WHERE `AUTH_ENABLED` is `true`, THE App SHALL read the required username from `AUTH_USERNAME` and the required password from `AUTH_PASSWORD` in the environment; IF either `AUTH_USERNAME` or `AUTH_PASSWORD` is absent or empty at startup, THE App SHALL log an error identifying the missing variable and exit with a non-zero status code.
3. WHERE `AUTH_ENABLED` is `true`, IF a request does not include Basic Authentication credentials or includes credentials that do not exactly match (case-sensitive) the configured `AUTH_USERNAME` and `AUTH_PASSWORD`, THEN THE Auth_Middleware SHALL return HTTP 401 with a `WWW-Authenticate: Basic realm="Bedrock Chat"` header.
4. WHERE `AUTH_ENABLED` is `false` or absent, THE App SHALL serve all routes without authentication.
5. THE App SHALL include a `README.md` section on public exposure via tunnels that covers: starting a Cloudflare Tunnel (`cloudflared tunnel --url http://localhost:3000`), starting an ngrok tunnel (`ngrok http 3000`), and enabling `AUTH_ENABLED` before exposing publicly.
6. THE App SHALL include a `README.md` section on cloud deployment that lists the environment variables `AWS_BEARER_TOKEN_BEDROCK`, `AWS_REGION`, `BEDROCK_MODEL_ID`, `AUTH_ENABLED`, `AUTH_USERNAME`, and `AUTH_PASSWORD` as required deployment configuration for Railway and Fly.io.

---

### Requirement 8: Developer Experience and Project Structure

**User Story:** As a developer, I want a well-structured project with clear setup instructions so that I can get the app running in under five minutes.

#### Acceptance Criteria

1. THE App SHALL be implemented as a single entry-point file `app.py` that starts the server when executed with `python app.py`.
2. THE App SHALL include a `requirements.txt` listing all Python dependencies with pinned versions.
3. THE App SHALL include a `README.md` with step-by-step setup instructions covering virtual environment creation, dependency installation, `.env` configuration, and the start command.
4. THE App SHALL serve the Chat_Interface as a static HTML/CSS/JS file embedded in or served by `app.py`, requiring no separate frontend build step.
5. THE App SHALL log each incoming user Message and each Bedrock API invocation at the INFO level to standard output.
6. WHEN a handled error condition occurs during request processing, THE App SHALL log the error type and error message at the ERROR level and return an HTTP 500 response to the client.
7. WHEN an unhandled exception occurs, THE App SHALL log the full stack trace at the ERROR level and return an HTTP 500 response to the client.
