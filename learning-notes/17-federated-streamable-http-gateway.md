# 17. The federated Streamable HTTP gateway

## What this note covers

This session moved the project from an analytics-only legacy SSE mount to one
federated Streamable HTTP gateway. The gateway now connects the local
analytics, Fetch, and SQLite servers; Inspector, Postman, and the Gemini
client all connect to the gateway.

## Two layers and two transports

There are MCP client/server connections on both sides of the gateway:

1. The gateway starts the three upstream MCP server processes over stdio.
2. The gateway discovers their tools and exposes them through Streamable HTTP
   at `/mcp`.
3. A client such as Gemini or Inspector connects to `/mcp` and requests a
   tool.
4. The gateway looks up which upstream owns that tool and sends the call over
   that upstream's stdio MCP session.
5. The result is passed back through the gateway to the original client.

The public endpoint can use Streamable HTTP even though upstream community
servers continue to use stdio. This lets one remote client access several
servers without deploying or rewriting every community server.

## Namespaces and routing

Tool names from different servers might collide. The gateway prefixes each
tool with its source server, for example:

- `local_get_system_metrics`
- `fetch_fetch`
- `sqlite_list_tables`

The tool list contains those exposed names and their original input schemas.
Internally, the gateway keeps a route from the exposed name to the upstream
session and original tool name. On `tools/call`, it uses that route and returns
the upstream result. The prefix identifies the source and makes routing
unambiguous.

Resources and prompts are also discovered and exposed. Unique resource URIs
are preserved; if upstreams publish the same URI, the gateway assigns a
server-specific URI to avoid an ambiguous read.

## Startup and lifecycle

The gateway initializes upstream sessions during application startup. It
lists tools, resources, and prompts before accepting MCP traffic. If an
upstream cannot initialize or capability discovery fails, startup reports an
error instead of returning an incomplete tool list as if everything worked.
The upstream sessions are closed when the gateway shuts down.

The HTTP MCP endpoint requires `X-API-Key`. `GET /health` remains public for
hosting-platform health checks. The gateway logs duration for every proxied
tool call; the analytics tool separately measures its own Python function
runtime.

## Gemini client change

The Gemini client no longer launches three subprocesses. It connects to
`OMNIMCP_GATEWAY_URL` (default `http://127.0.0.1:8000/mcp`), sends the gateway
key, discovers the combined tool list, and calls tools by their exposed names.
`GEMINI_API_KEY` is only used for Google's Gemini API. It is not forwarded to
the gateway or its child processes.

Start the gateway in one terminal and the Gemini client in another:

```powershell
uv run --env-file .env uvicorn omnimcp_analytics.gateway:app --host 127.0.0.1 --port 8000
uv run --env-file .env omnimcp-client "Summarize the current system metrics"
```

Inspector's Streamable HTTP connection should point to
`http://127.0.0.1:8000/mcp` and include the same `X-API-Key` header.

## Checkpoint complete

The topology is now a single protected HTTP gateway with three stdio
upstreams. The next useful phase is to run it locally, inspect the combined
tool list, and then use the Gemini client through that same endpoint.
