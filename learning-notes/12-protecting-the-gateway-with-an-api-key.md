# 12. Protecting the gateway with an API key

## What this note covers

The gateway can expose MCP tools over a network, so it checks an API key before
allowing MCP transport requests. This is separate from `GEMINI_API_KEY`, which
authenticates the Gemini client to Google.

## Middleware checks MCP transport requests

In `src/omnimcp_analytics/gateway.py`, the HTTP middleware checks requests to
`/mcp` and paths under `/mcp/`. These are the Streamable HTTP MCP endpoint and
its transport requests.

For those paths, it reads:

- The expected secret from the server's `OMNIMCP_API_KEY` environment variable.
- The caller's value from the `X-API-Key` HTTP request header.

If the server has no configured key, it returns HTTP 503 at lines 22–26: the
gateway is not configured to accept MCP requests. If the key is configured but
the caller's header does not match, it returns HTTP 401 at lines 27–31.
`hmac.compare_digest()` is used to compare the values safely.

The `/health` endpoint is intentionally outside those guarded MCP paths, so a
hosting service can check whether the process is responding without
possessing the MCP API key.

## Keep the two keys distinct

- `GEMINI_API_KEY` is used by `client.py` when it calls Google's Gemini API.
- `OMNIMCP_API_KEY` is used by the gateway to authorize incoming HTTP MCP
  requests.

The Gemini client supplies `OMNIMCP_API_KEY` when connecting to the gateway.
Never put either secret in a prompt, source file, or learning notes. Set the
gateway key in the gateway process environment or hosting platform's secret
settings.

## Cross-check questions

1. What header does a remote caller send to the gateway?
2. What status does the gateway return if its own key is not configured?
3. What status does it return if the caller sends the wrong key?
4. Is `GEMINI_API_KEY` the same secret as `OMNIMCP_API_KEY`?

## Checkpoint complete

We identified which requests require `OMNIMCP_API_KEY`, distinguished it from
`GEMINI_API_KEY`, and reviewed the gateway's fail-closed responses.

Continue with [note 13](13-tool-telemetry-and-local-gateway.md) to examine
tool-duration logging and start the HTTP gateway locally.
