# 3. Reading live system metrics

## What this note covers

This checkpoint follows the code inside `get_system_metrics()` in
`src/omnimcp_analytics/server.py`. The function uses the third-party Python
library `psutil` to read current system statistics and returns them as a
dictionary.

## The function's work

The function performs two reads:

```python
memory = psutil.virtual_memory()
cpu_percent = psutil.cpu_percent(interval=0.1)
```

`psutil.virtual_memory()` returns memory statistics. This server selects:

- `memory.total`: total physical memory, in bytes.
- `memory.available`: memory the operating system estimates can be made
  available to processes without swapping, in bytes.
- `memory.percent`: the percentage of memory in use, as a percentage value.

`psutil.cpu_percent(interval=0.1)` measures CPU utilization over a short
sampling interval. Think of the result as how busy the CPU was across that
measurement window, rather than a single instantaneous reading. With a
non-zero interval, the call waits for the measurement; `0.1` means about 100
milliseconds. A longer interval generally makes this function take longer in
wall-clock time and measures across a longer window. It does not mean the
process spends that entire wait actively using the CPU to calculate the
measurement.

The function places these values into a Python dictionary:

```python
{
    "cpu_percent": ...,
    "memory_total_bytes": ...,
    "memory_available_bytes": ...,
    "memory_percent": ...,
}
```

The dictionary keys are the names clients see in the result. The values come
from the live machine at call time, so separate tool calls can produce
different numbers. The `dict[str, int | float]` return annotation indicates a
dictionary with string keys and numeric values; it is not an input parameter.

## Inspector experiment

Call `get_system_metrics` several times in Inspector. Compare the results:

- CPU percentage can change between calls as the computer does different work.
- Memory totals normally remain stable during the experiment.
- Available memory and memory percentage can shift as the operating system and
  applications use memory.
- Each call waits at least about a tenth of a second for the CPU sampling
  interval, in addition to the time spent by the rest of the system.
- Increasing the interval can make the CPU measurement window longer, but
  also increases response latency; it does not make the measurement itself use
  one full second of CPU computation.

These are machine measurements, not fixed examples. Your values need not match
someone else's.

## Cross-check questions

1. Which two `psutil` functions does `get_system_metrics()` call?
2. Are `memory_total_bytes` and `memory_available_bytes` measured in bytes or
   percentages?
3. Why might `cpu_percent(interval=0.1)` take a little time to return?
4. Is `dict[str, int | float]` an input schema or a return-type annotation?
5. Which values would you expect to change more between quick repeated calls:
   total memory, or CPU utilization?

## Checkpoint complete

We traced the values returned by `get_system_metrics()` and discussed why a
non-zero CPU sampling interval adds elapsed waiting time.

Continue with [note 4](4-starting-an-mcp-client-session.md) to see how the
client starts and connects to an MCP server.
