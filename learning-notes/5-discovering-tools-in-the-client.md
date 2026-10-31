# 5. Discovering tools in the client

## What this note covers

After an MCP client session is initialized, the client can ask the server
which tools it provides. This note focuses on that discovery step and how the
client presents the discovered tools to Gemini. It does not cover executing
Gemini's function call yet.

## Ask the MCP server to list tools

In `src/omnimcp_analytics/client.py`, the client calls:

```python
server_tools = await session.list_tools()
```

This sends the MCP `tools/list` request over the initialized session. The
server replies with descriptions of its tools, including names, descriptions,
and input schemas. This is the same discovery operation you previously saw in
Inspector.

## Prepare Gemini's tool declarations

For each MCP tool, the client makes a Gemini-facing function declaration:

```python
exposed_name = _gemini_name(server_name, tool.name, used_names)
schema = tool.inputSchema or {"type": "object", "properties": {}}
```

The client uses a namespaced name so tools from different MCP servers are
distinguishable. It reuses the MCP tool's input schema so Gemini can know what
arguments are valid. For the local `get_system_metrics` tool, the namespaced
Gemini name is `local_get_system_metrics`; because the MCP tool takes no
arguments, its input schema has no fields.

The namespace is important for more than model clarity. The client's routing
table is keyed by the Gemini-facing name. If two servers had the same
unmodified name, one mapping could overwrite the other, making it possible to
send a call to the wrong server. Giving each server's tool a distinct name
avoids that collision.

The client then constructs a Google Gen AI `FunctionDeclaration` with that
name, a description, and the schema. These declarations tell Gemini which
functions it may request. Creating a declaration does not execute the tool and
does not send an MCP `tools/call` request.

As a hypothetical example, if the Python tool instead had a required parameter
`threshold: float`, FastMCP would describe that parameter in the input schema
as a required number. The client would pass that schema to Gemini, which could
then provide a numeric `threshold` argument in its function-call request. The
current `get_system_metrics()` function has no such parameter.

The names and schema have different audiences at this point:

- The MCP server originally supplies the tool's name and `inputSchema`.
- The Python client adapts that information into a Gemini function declaration.
- Gemini can later return a request to call a declared function.

## Cross-check questions

1. What MCP operation does `session.list_tools()` perform?
2. Does listing tools execute `get_system_metrics()`?
3. Why does the client add a server prefix to the Gemini-facing tool name?
4. What information does the input schema provide to Gemini?
5. Does building a `FunctionDeclaration` itself call the MCP server tool?

## Checkpoint complete

We followed `tools/list` and saw how the client adapts MCP tool descriptions
into Gemini declarations. These declarations describe tools but do not execute
them.

Continue with [note 6](6-sending-the-prompt-to-gemini.md) to see how the client
sends the prompt and declarations to Gemini.
