# 1. MCP tools and the message lifecycle

These notes record the concepts covered so far. The project is being learned
step by step; this is a reference for revision, not a checklist to rush through.

## Checkpoint: MCP tools and the message lifecycle

### What an MCP server does

An MCP server exposes capabilities—such as tools and resources—that an MCP
client can discover and use. In this project, the server is defined in
`src/omnimcp_analytics/server.py`.

The Python function is still an ordinary Python function. The `@mcp.tool()`
decorator registers it with FastMCP. FastMCP uses information such as its name,
docstring, and type hints to describe it to MCP clients, then invokes it when a
client makes a tool call.

### The `get_system_metrics` tool

- Tool name: `get_system_metrics`
- Description: `Return current CPU utilization and system memory usage.`
- It has no function parameters, so its input schema has no fields.
- The client supplied no input values when calling it.
- The returned JSON fields—`cpu_percent`, `memory_total_bytes`,
  `memory_available_bytes`, and `memory_percent`—are output values produced by
  the function, not inputs.
- FastMCP typically includes a structured result and a text representation in a
  tool response. Exact result fields can depend on the SDK and the return type.

### Tool discovery vs. tool invocation

- `tools/list` asks the server to describe its available tools. Tool
  descriptions include details such as a tool's name, description, and
  `inputSchema`. Inspector can use the schema to decide what input controls to
  show.
- `tools/call` asks the server to run one specific tool. Its parameters include
  the tool name and the argument values.
- In a JSON-RPC message, `method: "tools/call"` identifies the MCP operation.
  `params.name` identifies which tool to call. The method stays the same when a
  different tool is selected; the name and arguments change.

### JSON-RPC and the MCP lifecycle

MCP messages use JSON-RPC 2.0. A simplified lifecycle is:

1. The client sends an `initialize` request.
2. The server replies with the same request ID and its initialization result.
3. The client sends an `initialized` notification.
4. The client can discover tools with `tools/list`.
5. The client invokes a selected tool with `tools/call`.
6. The server replies with a result using the request's ID.

An illustrative tool request:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "get_system_metrics",
    "arguments": {}
  }
}
```

The `id` is a correlation label. The matching ID in the response tells the
client which request that response belongs to. The ID does not identify the
tool; `method` and `params` describe the operation and tool.

A notification, such as `notifications/initialized`, has no ID because the
sender does not expect a reply. This differs from a request, which expects a
response.

The exact initialization fields and tool-result representation can vary with
protocol/SDK versions and negotiated capabilities; the examples here are
conceptual illustrations rather than a byte-for-byte capture from Inspector.

### Stdio transport

The server is started with `mcp.run(transport="stdio")`. Inspector launches it
as a separate process and exchanges MCP messages through standard input and
standard output (stdin/stdout). This is a local communication channel and does
not require an HTTP server or port.

Because stdout carries protocol messages, arbitrary `print(...)` output there
can interfere with the MCP stream. Python logging normally writes to stderr,
which keeps diagnostic messages separate from protocol output; use the logger
for debugging a stdio server.

### Why the `__main__` guard matters

At the bottom of the server module:

```python
if __name__ == "__main__":
    main()
```

This starts the stdio server when the module is run directly. It does not start
the server loop merely because another module imports it. For example, the
gateway imports `mcp` from the server module so it can mount that server over
SSE. Without the guard, importing the module could unexpectedly start a
blocking stdio loop and keep the gateway from starting.

### Self-test

Try to answer these without looking at the answers above:

1. What does `@mcp.tool()` do, and what remains an ordinary Python function?
2. Why does Inspector show no input fields for `get_system_metrics`?
3. What is the difference between `tools/list` and `tools/call`?
4. In a `tools/call` request, what does the JSON-RPC `id` correlate?
5. Why does a notification have no request ID?
6. Why can printing debug text to stdout break a stdio MCP server?
7. Why is it useful that importing `server.py` does not automatically start
   the server?

## Next checkpoint

Continue with the decorators in `server.py`: inspect how `@mcp.tool()` and
`@mcp.resource(...)` register capabilities with FastMCP, and relate the Python
function's docstring and type hints to the schema Inspector displayed. Do this
before moving on to the Gemini client, federation, or gateway.
