# 13. Tool telemetry and running the gateway locally

## What this note covers

The analytics tool logs how long its Python function takes to run. The
federated gateway also measures each upstream tool call and serves MCP clients
over Streamable HTTP.

## Measure tool execution time

In `src/omnimcp_analytics/server.py`, `_timed_tool()` begins at line 31. It
records a start value using `time.perf_counter()` at line 34, invokes the
wrapped tool, and calculates elapsed milliseconds in the `finally` block at
lines 37–39.

`perf_counter()` is a high-resolution monotonic timer, suited to measuring
elapsed durations. The `finally` block logs the duration whether the tool
returns normally or raises an exception. It measures the wrapped function's
execution, not the entire network request or Gemini's response time.

## Start the gateway locally

The README shows the local gateway command:

```powershell
uv run --env-file .env uvicorn omnimcp_analytics.gateway:app --host 127.0.0.1 --port 8000
```

For local practice, put `OMNIMCP_API_KEY=local-learning-secret` in the
project-root `.env` file. `uv run --env-file .env` loads it into the gateway
process environment. The gateway also starts the analytics, Fetch, and SQLite
MCP processes at startup.

Here, `uvicorn` runs the FastAPI `app` object from
`omnimcp_analytics.gateway`. Binding to `127.0.0.1` makes it reachable only
from the local machine. The placeholder key is only for local practice; use a
private, strong secret for any shared deployment, and do not paste it into
chat.

With the server running, `GET http://127.0.0.1:8000/health` should return a
small health response. The Streamable HTTP MCP endpoint is
`http://127.0.0.1:8000/mcp` and requires the `X-API-Key` header. You can stop
the local server with Ctrl+C in its terminal.

The gateway logs upstream tool durations in milliseconds, including network
and MCP overhead for that upstream call. The analytics server separately logs
the duration of its local Python function. Those measurements cover different
parts of a tool call.

## Cross-check questions

1. What interval does `_timed_tool()` measure: only the Python tool function,
   or the full Gemini round trip?
2. Why is `127.0.0.1` a safer binding for local practice than `0.0.0.0`?
3. Which secret does the gateway check?

## Next checkpoint

Continue with [note 14](14-docker-and-render-deployment.md) to understand how
Docker packages the gateway and how Render runs that container.
