# 11. Why the gateway separates stdio and HTTP

## What this note covers

The gateway accepts client connections using Streamable HTTP, while it starts
its upstream servers over stdio. The two transports serve different parts of
the system.

## Two ways to connect to the same MCP server

The local analytics server in `src/omnimcp_analytics/server.py` runs over
stdio when launched as a child process. The gateway in
`src/omnimcp_analytics/gateway.py` creates separate MCP client sessions to
that server and the community Fetch and SQLite servers:

- **stdio**: a local client starts the server process and exchanges MCP
  messages through the process's stdin/stdout pipes.
- **Streamable HTTP**: an HTTP client connects to one MCP endpoint. The
  protocol supports JSON responses and optional SSE streaming.

The gateway is an aggregator: it discovers each upstream's capabilities,
prefixes tool names with the upstream name, and exposes the combined tools
from `/mcp`. A caller such as the Gemini client or Inspector connects to this
single remote endpoint. Inside the gateway, tool calls route back to the
upstream MCP session that owns that tool.

The transport changes how messages travel; federation changes which tools
are presented at the endpoint. They are separate design choices.

`GET /health` is an ordinary HTTP health check, not an MCP resource. The
Streamable HTTP mount at `/mcp` is the MCP endpoint.

## Cross-check questions

1. What changes between stdio and Streamable HTTP: the tool capability or
   the communication transport?
2. Why does the gateway use stdio internally but HTTP for outside clients?
3. Is `/health` an MCP tool?
4. Does the Gemini client connect to the gateway or directly to the upstreams?

## Checkpoint complete

We separated the upstream process transport from the client-facing network
transport and learned how the gateway routes federated tools.

Continue with [note 12](12-protecting-the-gateway-with-an-api-key.md) to
understand which requests require the gateway key and what the failure
responses mean.
