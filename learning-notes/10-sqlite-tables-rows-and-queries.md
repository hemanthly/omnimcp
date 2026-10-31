# 10. SQLite tables, rows, and queries

## What this note covers

We are using the `learning_notes` table in the local SQLite database. This
checkpoint separates table structure from table data, and read operations
from write operations.

## The table exists, but it is empty

We created this table:

```sql
CREATE TABLE learning_notes (
    id INTEGER PRIMARY KEY,
    topic TEXT NOT NULL
)
```

The table has a schema—its name and column definitions—but creating it did not
add any rows. A `SELECT` request through the SQLite server's `read_query` tool
returned an empty result. This is normal: a query can succeed even when there
are no matching rows.

## Insert one sample row

The SQLite server also provides a `write_query` tool. To add one row, it can
execute:

```sql
INSERT INTO learning_notes (topic)
VALUES ('MCP federation practice')
```

`id` is an integer primary key, so SQLite assigns it automatically when it is
omitted. `topic` is required because the column is `NOT NULL`, so the insert
provides a value for it.

Ask Gemini to insert that row, then use a read-only `SELECT` request to verify
it. The write changes the local `data/omnimcp.db` file. Repeat inserts can add
duplicate topics; do not rerun the insert unless you intend to add another row.

## Cross-check questions

1. What is the difference between a table schema and a row?
2. Which SQLite server tool is intended for a `SELECT` query?
3. Which tool executes an `INSERT` query?
4. Why can this insert omit `id` but not `topic`?

## Checkpoint complete

We verified that the SQLite server starts, that its table-listing tool reports
the database state, and that a read-only `SELECT` against the new table returns
no rows. This is enough to confirm the SQLite route is working for this
walkthrough; we are stopping here without inserting sample data.

Continue with [note 11](11-why-the-gateway-uses-http-and-sse.md) to compare the
local stdio transport with the networked gateway.
