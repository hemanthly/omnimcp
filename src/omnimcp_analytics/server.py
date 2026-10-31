"""Local system analytics MCP server."""

from __future__ import annotations

import logging
import os
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, TypeVar

import psutil
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("omnimcp_analytics")
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

mcp = FastMCP("omnimcp-analytics")

F = TypeVar("F", bound=Callable[..., Any])


def _timed_tool(function: F) -> F:
    @wraps(function)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        started = time.perf_counter()
        try:
            return function(*args, **kwargs)
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000
            logger.info("tool=%s duration_ms=%.3f", function.__name__, elapsed_ms)

    return wrapped  # type: ignore[return-value]


@mcp.tool()
@_timed_tool
def get_system_metrics() -> dict[str, int | float]:
    """Return current CPU utilization and system memory usage."""
    memory = psutil.virtual_memory()
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_total_bytes": memory.total,
        "memory_available_bytes": memory.available,
        "memory_percent": memory.percent,
    }


@mcp.resource("logs://latest")
def read_latest_log() -> str:
    """Read the most recent part of the configured local log file."""
    log_path = Path(os.getenv("OMNIMCP_LOG_FILE", "logs/omnimcp.log")).expanduser()
    max_chars = 20_000
    content = log_path.read_text(encoding="utf-8", errors="replace")
    return content[-max_chars:]


def main() -> None:
    """Run the MCP server over stdio for local MCP hosts."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
