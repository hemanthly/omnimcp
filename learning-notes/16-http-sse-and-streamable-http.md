# 16. HTTP, legacy SSE, and Streamable HTTP

## What this note covers

HTTP, SSE, and Streamable HTTP are related but not interchangeable. This
project's public gateway and Gemini client now use Streamable HTTP.

## HTTP is the network protocol

HTTP is the protocol used to send requests and responses between a client and
a server. Server-Sent Events (SSE) is one way to stream events over an HTTP
response. MCP uses JSON-RPC messages, and its transports define how those
messages travel:

- **stdio**: JSON-RPC messages travel over a local process's stdin/stdout.
- **Legacy HTTP+SSE**: separate endpoints are used for an event stream and
  client messages.
- **Streamable HTTP**: one MCP endpoint receives HTTP POST requests and can
  return JSON or an SSE stream. An optional GET stream can carry server events.

## Legacy HTTP+SSE

The older transport opened a GET connection to an SSE endpoint. The server
sent an `endpoint` event that told the client where to POST messages. The
client POSTed JSON-RPC to that separate endpoint, and the matching responses
arrived on the open SSE connection. This project previously used that
pattern, but the current gateway no longer exposes those `/sse` and
`/message` endpoints.

## Streamable HTTP in this project

The gateway exposes one MCP endpoint:

```text
http://127.0.0.1:8000/mcp
```

Clients send MCP messages to that endpoint. The gateway's server setting
returns JSON responses, although Streamable HTTP also supports SSE responses.
The MCP `X-API-Key` header is an application-level authorization check; it is
not a feature of the Streamable HTTP protocol itself.

Inspector should use its **Streamable HTTP** transport option. Postman should
use MCP request mode with HTTP, and a local Desktop Agent is required to reach
localhost from the Postman application.

## Why the project still uses stdio internally

The gateway's public transport and its upstream transport are separate
choices. The selected architecture has Gemini, Inspector, and Postman connect
over Streamable HTTP to one gateway. The gateway itself launches the local,
Fetch, and SQLite MCP processes over stdio and routes calls to them. This lets
stdio-oriented community servers participate without requiring each one to
be independently hosted over HTTP.

## Which transport to choose

- **Local child process:** stdio avoids opening a network port.
- **Remote MCP clients:** Streamable HTTP is the current HTTP transport.
- **Legacy service:** use an explicitly compatible legacy SSE client only
  when the server still exposes the older transport.

## Checkpoint complete

We distinguished HTTP, legacy SSE, and Streamable HTTP, and identified which
transport each connection in this project's federation uses.

Continue with [note 17](17-federated-streamable-http-gateway.md) to trace
capability discovery, tool name prefixing, and call routing through the gateway.
