# 2. FastMCP decorators and tool schemas

## What this note covers

This checkpoint explains how the `get_system_metrics` function becomes an MCP
tool, how FastMCP describes it to clients, and what the timing decorator does.
The source is `src/omnimcp_analytics/server.py`.

## The function before registration

At its core, this is a normal Python function:

```python
def get_system_metrics() -> dict[str, int | float]:
    """Return current CPU utilization and system memory usage."""
    ...
```

By itself, Python can call this function. MCP clients cannot discover it just
because it exists in a Python file. FastMCP must register it with the server.

## What `@mcp.tool()` does

```python
@mcp.tool()
def get_system_metrics() -> dict[str, int | float]:
    ...
```

The decorator registers the function with the `mcp` FastMCP server as a tool.
FastMCP can then include it in `tools/list` responses and invoke it when it
receives a matching `tools/call` request.

FastMCP derives useful metadata from the function:

- The Python function name becomes the tool name.
- The docstring becomes the tool description.
- The function signature and type hints are used to construct an input schema.

This function has no parameters, so its input schema has no fields. Its return
type annotation describes the shape of the result for Python tooling; tools
typically describe inputs to clients using `inputSchema`.

## The resource decorator

The server also contains:

```python
@mcp.resource("logs://latest")
def read_latest_log() -> str:
    ...
```

This registers a resource, not a tool. A tool represents an operation the
client asks the server to perform. A resource represents data the client can
read using MCP resource methods. `logs://latest` is the resource URI.

A client discovers resources with `resources/list`. To read this particular
resource, it sends a request conceptually like:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "resources/read",
  "params": {
    "uri": "logs://latest"
  }
}
```

The method identifies the operation (`resources/read`); the URI identifies
which resource to read. The server replies with the contents for that URI.
This differs from `tools/call`, which names a tool and supplies its arguments.
Here, the resource has a fixed URI and the Python function has no parameters.
If the configured log file does not exist or cannot be read, reading it will
fail; the URI itself does not create that file.

### Inspector experiment: missing backing file

With `OMNIMCP_LOG_FILE` unset, `read_latest_log()` tries to read
`logs/omnimcp.log`. Inspector can still discover the registered
`logs://latest` resource, but reading it fails if that local file is absent.
The MCP URI is the resource's address; it is not the path of a file and does
not create the backing file.

To try a successful read in PowerShell, create a small sample log:

```powershell
New-Item -ItemType Directory -Force logs | Out-Null
Set-Content -Path logs\omnimcp.log -Value "First sample log line"
```

Then read `logs://latest` again in Inspector. The resource should return the
text from the file. The `logs/` directory is git-ignored in this project, so
this local sample file is not included in source control. In this walkthrough,
Inspector returned:

```text
First sample log line
```

## Why the timing decorator is also present

The tool has two decorators:

```python
@mcp.tool()
@_timed_tool
def get_system_metrics() -> dict[str, int | float]:
    ...
```

Python applies stacked decorators from the bottom upward. This is equivalent
to:

```python
get_system_metrics = mcp.tool()(_timed_tool(get_system_metrics))
```

So the timing decorator first wraps the original function, then FastMCP
returns a wrapped function, and FastMCP receives/registers that function as the
tool. FastMCP does not receive an elapsed-time value during registration.

Only later, when a client calls the tool, the wrapper records a start time,
runs the original function, and logs elapsed milliseconds in a `finally`
block. The `finally` block means the duration is logged even if the function
raises an exception.

`functools.wraps` copies important metadata from the original function to its
wrapper, including its name and docstring. This helps the registration layer
continue to see the useful function metadata.

## Cross-check questions

Try to answer these before reading the explanations above:

1. Does a Python function become discoverable to an MCP client merely because
   it exists in a file?
2. What does FastMCP learn from the function name, docstring, and signature?
3. In `@mcp.tool()` above `@_timed_tool`, which decorator is applied first?
4. Is `logs://latest` registered as a tool or as a resource?
5. Why does the timing wrapper use `finally`?

## Checkpoint complete

We discovered the tool and resource in Inspector, read the resource while its
backing file was missing, then created a sample file and read its contents
successfully. A new read invokes the resource function again, so it reads the
current file contents.

Continue with [note 3](3-reading-live-system-metrics.md) to understand how the
tool obtains CPU and memory values.
