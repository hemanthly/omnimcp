# 9. Federating three MCP servers

## What this note covers

This note records the earlier design where the Gemini client managed three
stdio MCP sessions itself. The project has since moved to a federated gateway:
see [note 17](17-federated-streamable-http-gateway.md) for the current design.
The early client-side federation concepts below explain the same routing
problem at a different layer.

## Three named server configurations

`_server_parameters()` at line 39 returns `(server_name, parameters)` pairs:

| Name | Server process |
| --- | --- |
| `local` | This package's `omnimcp_analytics.server` Python module |
| `fetch` | The official `mcp-server-fetch` Python package |
| `sqlite` | The `mcp-server-sqlite` Python package |

The SQLite server receives the path from `OMNIMCP_SQLITE_DB`; the default is
`data/omnimcp.db`. The client creates the parent directory if it is missing.

`_uvx_parameters()` constructs commands that run the packages in isolated
environments managed by `uvx`. This avoids installing their dependencies into
the OmniMCP project's environment.

The SQLite server is started with the extra constraint `mcp<2`. Its published
package currently uses the MCP v1 server API, while unconstrained `uvx` would
otherwise select the newer MCP v2 SDK, which removed an API that this SQLite
server calls. The Fetch server is maintained against MCP v2 and runs in its own
separate environment; it can still communicate with this project's v1 client
over the negotiated MCP protocol.

## One independent session for each server

At line 104, `_run()` loops over all three configurations. For each one, it:

1. Starts a process and obtains its stdio streams using
   `stdio_client(parameters)` at line 105.
2. Wraps the streams in a `ClientSession` at line 106.
3. Initializes the MCP session at line 107.
4. Lists that server's tools and adds them to the shared set of Gemini
   declarations.

Each server keeps its own session. The client later uses the namespaced tool
name to find the correct session, so a tool call reaches the server that
advertised that tool.

## How the gateway fit in at that stage

At this stage, the FastAPI gateway exposed only the custom analytics MCP
server over SSE at `/mcp`. It did not aggregate or proxy Fetch and SQLite.

The client described in the original implementation started all three
servers over stdio and did not connect to the FastAPI gateway. In other words:

- One Gemini client application orchestrates the tool choices.
- It creates one MCP client session per server.
- The gateway exposed the custom MCP server over HTTP/SSE; it was not another
  MCP client and was not the federation router.

The gateway was later migrated to Streamable HTTP and now owns the three
upstream sessions. Gemini connects to that one federated endpoint instead of
starting the servers itself.

## Practical implications

- The local server can be tested independently with Inspector; the fetch and
  SQLite servers are separate programs.
- The original npm package names in the initial scaffold returned npm 404
  errors. Running each server separately isolated the failure: the local server
  initialized, but Fetch and SQLite did not. Switching to their Python `uvx`
  commands fixed the startup issue. We verified all three sessions and listed
  their tools successfully. The SQLite v1 constraint is necessary because the
  published server source calls an MCP API removed in SDK v2.
- Running the full Gemini client requires `uvx` to run the community servers
  and a valid `GEMINI_API_KEY`. Node.js/`npx` is only needed for the optional
  MCP Inspector.
- The client reads `GEMINI_API_KEY` from the process environment. A `.env` file
  is not loaded automatically by `client.py`; use `uv run --env-file .env
  omnimcp-client "Summarize the current system metrics"` to have `uv` load it.
  Keep `.env` private and do not commit or paste the API key into chat.
- Prompts and tool results sent to the Gemini API are sent to Google's service;
  do not include information you do not want to send there.
- The client opens all three sessions even if a prompt only needs one server.

## Cross-check questions

1. What are the three server names in the client configuration?
2. Does federation combine the servers into one MCP server, or manage separate
   sessions from one client?
3. Which server receives a tool call when the client selects that server's
   namespaced tool?
4. What two external prerequisites are needed for the full client beyond the
   Python dependencies?

## Historical end-to-end run

Once `uvx` is available, run one end-to-end prompt with Gemini using the
command in the README. Inspect which server's tool Gemini selects. Keep the
prompt simple and do not paste your API key into chat.

### End-to-end run verified

The first full run succeeded. Given the prompt "Summarize the current system
metrics", Gemini selected the local metrics tool and returned a sentence
summarizing CPU and memory values. The reported numbers are readings from that
run; they can change on later calls.

A Fetch run also succeeded with the prompt to fetch and summarize
`https://example.com`. The Fetch server advertises its tool as `fetch`; this
client exposes it to Gemini under the namespaced name `fetch_fetch`.

### Next: exercise SQLite without changing data

The SQLite server is configured in `src/omnimcp_analytics/client.py` around
lines 57–62. It uses `OMNIMCP_SQLITE_DB`, defaulting to `data/omnimcp.db`, and
starts the `mcp-server-sqlite` package. Its discovered `list_tables` tool is
read-only, making it a safe first database request:

```powershell
uv run --env-file .env omnimcp-client "List the tables in the SQLite database"
```

The default database may have no tables yet. This request is for learning
discovery and routing; it should not create or modify any data.

The read-only request succeeded and Gemini reported that the database was
empty and contained no tables. This confirms it reached the SQLite server and
used its table-listing capability.

A subsequent prompt asked Gemini to create a `learning_notes` table with
`id INTEGER PRIMARY KEY` and `topic TEXT NOT NULL`. Gemini reported that the
table was created, exercising a database write operation through the SQLite
MCP server. A follow-up `list_tables` read can verify that the table is now
present. The follow-up succeeded and showed `learning_notes`.

The table has a schema but no rows yet. A `SELECT` through the SQLite server's
`read_query` tool returned no rows, as expected. Creating a table defines its
structure; it does not insert data.

This walkthrough did not insert a sample row. For the current Streamable HTTP
architecture, continue with [note 17](17-federated-streamable-http-gateway.md).
