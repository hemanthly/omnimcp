# OmniMCP Analytics

A Python MCP server exposing local system metrics and a configured log resource,
plus a Gemini-powered client that federates it with the community Fetch and
SQLite MCP servers. The package also provides one API-key-protected,
federated Streamable HTTP gateway.

## Requirements

- Python 3.11 or newer
- `uv` (recommended) or `pip`
- `uv`/`uvx` to run the community Fetch and SQLite servers
- Node.js and `npx` only for the optional MCP Inspector command
- A Gemini API key to use the AI client

Install the package for local development:

```powershell
uv sync --extra dev
```

Or install it with pip:

```powershell
python -m pip install -e ".[dev]"
```

The project pins `mcp` to its v1 API line (`mcp[cli]>=1.28,<2`) to match the
FastMCP and stdio client APIs used here. Choose and add a license before
publishing your own distribution.
The Fetch server is launched in its own `uvx` environment and uses the newer
official package. The SQLite server is also launched with `uvx`, constrained
to MCP v1 because its current PyPI release uses the v1 server API.

The client reads `GEMINI_API_KEY` from its process environment. To load it from
a project-root `.env` file with `uv`, run:

```powershell
uv run --env-file .env omnimcp-client "Summarize the current system metrics"
```

The `.env` file should contain both keys:

```text
GEMINI_API_KEY=your-gemini-key
OMNIMCP_API_KEY=your-private-gateway-key
```

It must not be committed or shared. The `.gitignore` already excludes `.env`.
Alternatively, set both environment variables in PowerShell. Start the gateway
before running the Gemini client.
Optional settings:

| Variable | Default | Purpose |
| --- | --- | --- |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model used by the client |
| `OMNIMCP_LOG_FILE` | `logs/omnimcp.log` | File exposed by the `logs://latest` resource |
| `OMNIMCP_SQLITE_DB` | `data/omnimcp.db` | Database file passed to the community SQLite server |
| `OMNIMCP_API_KEY` | unset | Required key for the federated gateway and client |
| `OMNIMCP_GATEWAY_URL` | `http://127.0.0.1:8000/mcp` | Streamable HTTP endpoint used by the Gemini client |
| `LOG_LEVEL` | `INFO` | Python log level |

The SQLite server receives the configured database path. Create and populate
the database with data you are authorized to access before asking the agent to
query it. The Fetch server can make outbound web requests; only use it with
trusted prompts and endpoints.

## Phase 1: Local MCP server

Run the server over stdio:

```powershell
uv run omnimcp-analytics
```

Inspect its generated tool and resource schemas without involving an LLM:

```powershell
npx -y @modelcontextprotocol/inspector uv run python -m omnimcp_analytics.server
```

The `get_system_metrics` tool reports CPU and memory usage. The
`logs://latest` resource reads the last 20,000 characters of the file specified
by `OMNIMCP_LOG_FILE`. File read errors are returned as MCP resource errors.

## Phases 2 and 3: Gemini and server federation

The gateway launches three upstream MCP servers over stdio: this package, the
Fetch server, and the SQLite server. It namespaces their tools and presents
them through one Streamable HTTP endpoint. Gemini connects to that gateway
instead of starting each upstream server itself.

Start the gateway in one terminal:

```powershell
uv run --env-file .env uvicorn omnimcp_analytics.gateway:app --host 127.0.0.1 --port 8000
```

In another terminal, ask Gemini to use the gateway:

```powershell
uv run --env-file .env omnimcp-client "Summarize the current system metrics"
```

You can ask for web retrieval or SQL operations as well. Tool names include
the upstream prefix, such as `local_get_system_metrics` and
`sqlite_list_tables`. The client limits the Gemini tool-call loop to eight
rounds and reports missing credentials and protocol errors rather than
silently continuing.

## Phase 4: Federated Streamable HTTP gateway

For local testing, add `OMNIMCP_API_KEY=local-learning-secret` to the
project-root `.env` file. Keep real deployment keys private. All three upstream
servers are initialized during gateway startup. If any cannot start, the
gateway reports the server that failed and will not serve MCP requests.
- `GET /health` is a public health check.
- `/mcp` is the single Streamable HTTP MCP endpoint.
- Requests to `/mcp` require the `X-API-Key` header.

The gateway uses ASGI middleware to protect the mounted MCP transport; FastAPI
route dependencies do not apply to routes handled by a mounted ASGI app.
Missing server-side key configuration fails closed with HTTP 503. Invalid or
missing client keys receive HTTP 401. Tool execution durations are logged in
milliseconds.

Do not expose the gateway without setting a strong secret and using HTTPS at
the hosting layer.

### Test the gateway with MCP Inspector and Postman

For interactive tool/resource discovery and calls, start MCP Inspector and
connect to the running gateway using **Streamable HTTP**:

1. Run `npx -y @modelcontextprotocol/inspector`.
2. In Inspector, select Streamable HTTP and enter
   `http://127.0.0.1:8000/mcp`.
3. Add the custom header `X-API-Key` with the local value from `.env`, then
   connect. Tools from all three upstreams appear with their server prefix.
   The local metrics tool is `local_get_system_metrics`; `logs://latest` is a
   resource exposed by the local server.

In Postman's MCP request mode, select HTTP/Streamable HTTP and connect to
`http://127.0.0.1:8000/mcp` with the same `X-API-Key` header. Use the Postman
desktop app or Desktop Agent for localhost; a cloud agent cannot reach your
computer's `127.0.0.1`.

See [learning note 15](learning-notes/15-testing-the-gateway-with-inspector-and-postman.md)
for the request examples and the complete sequence.

## Phase 5: Docker, Render, and PyPI

Build and run the gateway container:

```powershell
docker build -t omnimcp-gateway .
docker run --rm -p 8000:8000 -e OMNIMCP_API_KEY="replace-me" omnimcp-gateway
```

`render.yaml` configures a Render Docker web service with `/health` checks. The
image includes `uv` because the gateway uses `uvx` to start the Fetch and SQLite
upstreams. Set `OMNIMCP_API_KEY` as a secret environment variable in Render
before deployment. The upstream SQLite database and package caches use the
container filesystem; check the host's persistence and resource limits before
relying on them.

### Publish a release to PyPI

The GitHub Actions workflow at `.github/workflows/publish.yml` runs tests,
builds the wheel and source distribution, checks their metadata, and publishes
when a `v*` version tag is pushed. It uses PyPI Trusted Publishing, so no
PyPI API token is stored in the repository.

Before the first release:

1. Push this project to a GitHub repository.
2. Create the `pypi` GitHub Actions environment in repository settings.
3. In PyPI, configure a Trusted Publisher for this project's GitHub owner and
   repository, workflow file `.github/workflows/publish.yml`, and environment
   `pypi`. If the project does not exist on PyPI yet, use PyPI's
   **Pending publisher** setup so the first trusted workflow run can create it.
4. Confirm the desired package name is still available. PyPI package names
   are permanent once claimed.
5. Ensure `version` in `pyproject.toml` matches the release tag. For the
   current version, the tag would be `v0.1.0`.
6. Push the tag from the repository root:

   ```powershell
   git tag v0.1.0
   git push origin v0.1.0
   ```

The workflow must be present on the default branch and the tag must point to a
commit containing the release files. Monitor the run in the repository's
**Actions** tab; it will stop before publishing if tests or package checks
fail. To release a later update, increase `version` in `pyproject.toml`, then
create and push a matching new tag. PyPI does not allow reusing a published
version.

You can build the distributions locally first with `uv build`. The `mcp.servers`
entry point is packaging metadata; client auto-discovery depends on the client
implementation choosing to support that entry-point group.

## Tests

```powershell
uv run pytest
```
