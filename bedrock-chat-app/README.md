# Bedrock Chat App

A single-file Python FastAPI web application that streams Claude 3.5 Sonnet responses from AWS Bedrock to a browser via Server-Sent Events (SSE). The frontend is embedded HTML/CSS/JS served directly from `app.py`.

## Features

- 🚀 **Real-time streaming** — responses stream token-by-token via SSE
- 💬 **Conversation history** — stored in browser `sessionStorage`, sent with each request
- 📝 **Markdown rendering** — assistant responses rendered with marked.js
- 🔒 **Optional Basic Auth** — protect your instance with username/password
- 🎨 **Dark-themed UI** — clean, responsive chat interface
- ⚡ **Single file** — entire backend in one `app.py`

## Setup

### 1. Create a virtual environment

```bash
cd bedrock-chat-app
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AWS_BEARER_TOKEN_BEDROCK` | ✅ Yes | — | Your AWS Bedrock bearer token |
| `AWS_REGION` | No | `us-east-1` | AWS region for Bedrock |
| `BEDROCK_MODEL_ID` | No | `anthropic.claude-3-5-sonnet-20241022-v2:0` | Bedrock model identifier |
| `AUTH_ENABLED` | No | `false` | Enable Basic HTTP Auth |
| `AUTH_USERNAME` | If auth enabled | — | Username for Basic Auth |
| `AUTH_PASSWORD` | If auth enabled | — | Password for Basic Auth |

### 4. Run the application

```bash
python app.py
```

The app starts on `http://0.0.0.0:3000`. Open your browser to `http://localhost:3000`.

## Public Exposure via Tunnels

If you want to expose the app publicly (e.g., for testing or demos), **enable authentication first**:

```env
AUTH_ENABLED=true
AUTH_USERNAME=your_username
AUTH_PASSWORD=your_secure_password
```

### Cloudflare Tunnel

```bash
cloudflared tunnel --url http://localhost:3000
```

### ngrok

```bash
ngrok http 3000
```

> ⚠️ **Security Warning**: Always enable `AUTH_ENABLED=true` when exposing the app publicly to prevent unauthorized access to your AWS Bedrock credentials.

## Cloud Deployment

### Environment Variables (All Platforms)

Set these six environment variables in your deployment platform:

```
AWS_BEARER_TOKEN_BEDROCK=your-token-here
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
AUTH_ENABLED=true
AUTH_USERNAME=your_username
AUTH_PASSWORD=your_secure_password
```

### Railway

1. Create a new project from GitHub repo
2. Set the environment variables in the Railway dashboard
3. Set the start command: `python app.py`
4. Railway will automatically detect port 3000

### Fly.io

1. Create `fly.toml` with internal port 3000
2. Set secrets:
   ```bash
   fly secrets set AWS_BEARER_TOKEN_BEDROCK=your-token
   fly secrets set AUTH_ENABLED=true
   fly secrets set AUTH_USERNAME=admin
   fly secrets set AUTH_PASSWORD=your-password
   ```
3. Deploy: `fly deploy`

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_routes.py -v

# Run with hypothesis statistics
pytest tests/ -v --hypothesis-show-statistics
```

## Architecture

```
bedrock-chat-app/
├── app.py              # Single-file FastAPI application (routes, middleware, frontend)
├── requirements.txt    # Pinned dependencies
├── .env.example        # Environment variable template
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_startup.py      # Startup validation tests
    ├── test_streaming.py    # SSE streaming property tests
    ├── test_routes.py       # Route handler tests
    ├── test_history.py      # Conversation history tests
    ├── test_auth.py         # Auth middleware tests
    ├── test_markdown.py     # Frontend behavior tests
    └── test_integration.py  # End-to-end integration tests
```

## License

MIT
