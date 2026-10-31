# 7. How the client routes a tool call

## What this note covers

This checkpoint starts following the client code in
`src/omnimcp_analytics/client.py`. It focuses on how a tool requested by Gemini
is routed to the correct MCP server session.

## There are two protocols involved

The client talks to Gemini through the Google Gen AI SDK, and to MCP servers
through MCP client sessions. Gemini's function-call response is not itself an
MCP `tools/call` request. The Python client acts as the bridge:

1. It tells Gemini about the available tools.
2. Gemini may return a function call.
3. The Python client finds which MCP session owns that tool and asks that
   session to call it.
4. The Python client can then pass the MCP result back to Gemini.

## Namespacing and the routing table

After connecting to an MCP server, the client discovers its tools with
`session.list_tools()`. It gives each tool a Gemini-facing name that includes
the server namespace. For example, the local tool `get_system_metrics` is
exposed to Gemini as `local_get_system_metrics`.

The client records a mapping like:

```text
"local_get_system_metrics" -> (local MCP session, "get_system_metrics")
```

Gemini uses the exposed name. The MCP server expects its original tool name.
This mapping lets the client translate between them and avoids collisions if
different servers have tools with the same original name.

## What `session.call_tool()` does

When Gemini returns a function call, the client looks up the returned name:

```python
session, original_name = routing[function_call.name]
result = await session.call_tool(
    original_name,
    arguments=dict(function_call.args or {}),
)
```

The lookup selects both the right server session and its original tool name.
`await session.call_tool(...)` asks the MCP SDK to make the MCP tool-call
request over that session's transport. For the local server, this is stdio.
The MCP server receives the request and invokes the registered Python tool.
The result is an MCP call result; the client is not directly calling the
Python function across the process boundary.

The client also passes Gemini's arguments to MCP:

Gemini's function-call arguments are converted to a Python dictionary. If
Gemini provided no arguments, the client uses an empty dictionary. That matches
the current `get_system_metrics()` tool in `server.py`, whose definition has
empty parentheses and no parameters. `threshold` was only a hypothetical
example from the earlier schema discussion; it is not part of this project's
current tool.

## Cross-check questions

1. Is Gemini's function-call response already an MCP `tools/call` message?
2. What is the purpose of prefixing the local tool with `local_`?
3. If Gemini asks for `local_get_system_metrics`, which original tool name
   should the local MCP server receive?
4. Does `session.call_tool()` call a function in the same Python process, or
   send a request through the MCP session?

## Checkpoint complete

We followed Gemini's namespaced function name through the routing table to the
original MCP tool name, server session, and arguments. For the current
no-parameter `get_system_metrics()` tool, the client sends an empty arguments
dictionary.

Continue with [note 8](8-returning-mcp-results-to-gemini.md) to follow the
result back into Gemini's conversation.
