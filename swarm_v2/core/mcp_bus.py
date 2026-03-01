"""
MCP Protocol Bus — Model Context Protocol Server/Client
Provides a universal tooling bus for registering, discovering, and calling
tools across the swarm with JSON-RPC-style schema validation.
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("MCPBus")


@dataclass
class ToolSchema:
    """Schema definition for an MCP-registered tool."""
    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    provider: str = "local"  # "local" or remote server URL
    version: str = "1.0.0"
    registered_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ToolCallResult:
    """Result of an MCP tool call."""
    tool_name: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    elapsed_ms: float = 0.0


class MCPBus:
    """
    Model Context Protocol Bus.

    Acts as both MCP server (exposes local tools) and MCP client
    (connects to remote MCP servers and imports their tools).

    Tools are registered with JSON schemas and called with validation.
    """

    def __init__(self):
        self._tools: Dict[str, ToolSchema] = {}
        self._handlers: Dict[str, Callable] = {}
        self._remote_servers: Dict[str, Dict[str, Any]] = {}
        self._call_log: List[Dict[str, Any]] = []
        self._stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
        }

    def register_tool(self, name: str, description: str,
                      input_schema: Dict[str, Any] = None,
                      output_schema: Dict[str, Any] = None,
                      handler: Callable = None,
                      provider: str = "local") -> ToolSchema:
        """
        Register a tool with the MCP bus.

        Args:
            name: Unique tool name
            description: Human-readable description
            input_schema: JSON Schema for input validation
            output_schema: JSON Schema for output description
            handler: Callable that executes the tool (sync or async)
            provider: "local" or remote server identifier
        """
        schema = ToolSchema(
            name=name,
            description=description,
            input_schema=input_schema or {},
            output_schema=output_schema or {},
            provider=provider,
        )
        self._tools[name] = schema
        if handler:
            self._handlers[name] = handler
        logger.info(f"[MCPBus] Registered tool: {name} (provider={provider})")
        return schema

    def unregister_tool(self, name: str) -> bool:
        """Remove a tool from the registry."""
        if name in self._tools:
            del self._tools[name]
            self._handlers.pop(name, None)
            return True
        return False

    def list_tools(self, provider: str = None) -> List[Dict[str, Any]]:
        """
        List registered tools (MCP server endpoint).

        Args:
            provider: Filter by provider. None returns all tools.
        """
        tools = []
        for name, schema in self._tools.items():
            if provider and schema.provider != provider:
                continue
            tools.append({
                "name": schema.name,
                "description": schema.description,
                "input_schema": schema.input_schema,
                "output_schema": schema.output_schema,
                "provider": schema.provider,
                "version": schema.version,
            })
        return tools

    def _validate_input(self, tool_name: str, args: Dict[str, Any]) -> Optional[str]:
        """Basic schema validation (checks required fields)."""
        schema = self._tools.get(tool_name)
        if not schema or not schema.input_schema:
            return None

        required = schema.input_schema.get("required", [])
        for field_name in required:
            if field_name not in args:
                return f"Missing required field: {field_name}"
        return None

    async def call_tool(self, name: str, args: Dict[str, Any] = None) -> ToolCallResult:
        """
        Execute a registered tool with schema validation.

        Args:
            name: Tool name
            args: Input arguments

        Returns:
            ToolCallResult with result or error
        """
        args = args or {}
        start = datetime.now()
        self._stats["total_calls"] += 1

        if name not in self._tools:
            self._stats["failed_calls"] += 1
            return ToolCallResult(tool_name=name, success=False,
                                  error=f"Tool '{name}' not found")

        # Validate input
        validation_error = self._validate_input(name, args)
        if validation_error:
            self._stats["failed_calls"] += 1
            return ToolCallResult(tool_name=name, success=False,
                                  error=validation_error)

        # Execute handler
        handler = self._handlers.get(name)
        if not handler:
            self._stats["failed_calls"] += 1
            return ToolCallResult(tool_name=name, success=False,
                                  error=f"No handler registered for '{name}'")

        try:
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**args)
            else:
                result = handler(**args)

            elapsed = (datetime.now() - start).total_seconds() * 1000
            self._stats["successful_calls"] += 1

            call_result = ToolCallResult(
                tool_name=name, success=True, result=result, elapsed_ms=elapsed
            )
        except Exception as e:
            elapsed = (datetime.now() - start).total_seconds() * 1000
            self._stats["failed_calls"] += 1
            call_result = ToolCallResult(
                tool_name=name, success=False, error=str(e), elapsed_ms=elapsed
            )

        # Log the call
        self._call_log.append({
            "tool": name,
            "success": call_result.success,
            "elapsed_ms": round(call_result.elapsed_ms, 2),
            "timestamp": datetime.now().isoformat(),
        })
        if len(self._call_log) > 200:
            self._call_log = self._call_log[-100:]

        return call_result

    def connect_remote(self, server_name: str, server_url: str,
                       tools: List[Dict[str, Any]] = None) -> int:
        """
        Connect to a remote MCP server and import its tools.

        Args:
            server_name: Human-readable server identifier
            server_url: Base URL of the remote MCP server
            tools: Pre-fetched tool list (if already known)

        Returns:
            Number of tools imported
        """
        self._remote_servers[server_name] = {
            "url": server_url,
            "connected_at": datetime.now().isoformat(),
            "tool_count": 0,
        }

        imported = 0
        if tools:
            for tool in tools:
                self.register_tool(
                    name=f"{server_name}/{tool['name']}",
                    description=tool.get("description", ""),
                    input_schema=tool.get("input_schema", {}),
                    output_schema=tool.get("output_schema", {}),
                    provider=server_name,
                )
                imported += 1

        self._remote_servers[server_name]["tool_count"] = imported
        logger.info(f"[MCPBus] Connected to remote server '{server_name}' — imported {imported} tools")
        return imported

    def get_stats(self) -> Dict[str, Any]:
        """Get MCP bus statistics."""
        return {
            "total_tools": len(self._tools),
            "local_tools": sum(1 for t in self._tools.values() if t.provider == "local"),
            "remote_servers": len(self._remote_servers),
            "remote_tools": sum(1 for t in self._tools.values() if t.provider != "local"),
            "calls": self._stats,
            "recent_calls": self._call_log[-10:],
        }


# Singleton
_bus: Optional[MCPBus] = None

def get_mcp_bus() -> MCPBus:
    global _bus
    if _bus is None:
        _bus = MCPBus()
    return _bus
