# 4. Starting an MCP client session

## What this note covers

This checkpoint begins at the top of
`src/omnimcp_analytics/client.py`. It focuses on how the client describes and
starts its local MCP server. It does not cover Gemini tool calling yet.

## Server code and client code are separate roles

- `src/omnimcp_analytics/server.py` defines the MCP server and its tools.
- `src/omnimcp_analytics/client.py` is a separate program. It can start the
  server process and communicate with that process using MCP.

When Inspector tested the server, it also started a process and communicated
with it over stdio. The project client will do something similar.

## Describing a process to start

The `_server_parameters()` function returns a list of server names and
`StdioServerParameters`. For this project's local server, the key part is:

```python
StdioServerParameters(
    command=sys.executable,
    args=["-m", "omnimcp_analytics.server"],
    env=_environment("OMNIMCP_LOG_FILE", "LOG_LEVEL"),
)
```

This object describes how to start the process:

- `command=sys.executable` uses the Python interpreter running this client.
- `args=["-m", "omnimcp_analytics.server"]` tells Python to run the server
  module as a program.
- `env=...` passes only the selected environment settings to that child
  process.

Creating `StdioServerParameters` does not itself start the server. It is a
configuration object. Later, `stdio_client(parameters)` starts the process and
sets up stdin/stdout streams for MCP communication.

## Creating the MCP session

The client uses the streams from `stdio_client` to create a `ClientSession`.
These are two separate steps:

1. `stdio_client(parameters)` launches the server process and opens its
   stdin/stdout communication streams. This is process startup and transport
   setup; it is not the MCP initialization handshake.
2. `session.initialize()` sends the MCP initialization request and completes
   the protocol handshake over those streams.

After initialization, the client can send MCP requests such as
`session.list_tools()` or `session.call_tool(...)`.

The client uses `AsyncExitStack` to manage the subprocess and session
lifetimes. When execution leaves the stack, those resources are closed. This
matters because these connections should not be left running after the client
is finished.

## Cross-check questions

1. Which file defines the `get_system_metrics()` server tool?
2. Does constructing `StdioServerParameters` start the child process?
3. What does `stdio_client(parameters)` do with the configuration?
4. Which line performs the MCP handshake: `stdio_client(parameters)` or
   `session.initialize()`?
5. What is `AsyncExitStack` helping the client manage?

## Checkpoint complete

We distinguished process startup and stdio transport setup from the MCP
initialization handshake.

Continue with [note 5](5-discovering-tools-in-the-client.md) to see how the
client discovers tools and describes them to Gemini.
