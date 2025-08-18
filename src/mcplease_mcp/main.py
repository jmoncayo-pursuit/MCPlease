"""Main entry point for MCPlease MCP Server."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from .server.server import MCPServer
from .adapters.ai_adapter import MCPAIAdapter
from .context.manager import MCPContextManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),  # Log to stderr to avoid interfering with stdio transport
    ]
)

logger = logging.getLogger(__name__)


def create_default_server_config() -> Dict[str, Any]:
    """Create default server configuration.
    
    Returns:
        Default server configuration
    """
    return {
        "server_name": "MCPlease MCP Server",
        "transports": [
            {"type": "stdio"}  # Default to stdio for IDE integration
        ],
        "ai_config": {
            "max_memory_gb": 12,
            "model_name": "openai/gpt-oss-20b"
        },
        "context_config": {
            "max_context_age_minutes": 30,
            "max_contexts_per_user": 10,
            "cleanup_interval_minutes": 5
        }
    }


def create_server_from_config(config: Dict[str, Any]) -> MCPServer:
    """Create MCP server from configuration.
    
    Args:
        config: Server configuration
        
    Returns:
        Configured MCP server
    """
    # Create AI adapter if configured
    ai_adapter = None
    ai_config = config.get("ai_config", {})
    if ai_config:
        try:
            ai_adapter = MCPAIAdapter(
                max_memory_gb=ai_config.get("max_memory_gb", 12)
            )
            logger.info("AI adapter created")
        except Exception as e:
            logger.warning(f"Failed to create AI adapter: {e}")
    
    # Create context manager
    context_config = config.get("context_config", {})
    context_manager = MCPContextManager(
        max_context_age_minutes=context_config.get("max_context_age_minutes", 30),
        max_contexts_per_user=context_config.get("max_contexts_per_user", 10),
        cleanup_interval_minutes=context_config.get("cleanup_interval_minutes", 5)
    )
    
    # Create server
    server = MCPServer(
        server_name=config.get("server_name", "MCPlease MCP Server"),
        transport_configs=config.get("transports", [{"type": "stdio"}]),
        ai_adapter=ai_adapter,
        context_manager=context_manager
    )
    
    return server


async def run_server_with_config(config: Dict[str, Any]) -> None:
    """Run MCP server with configuration.
    
    Args:
        config: Server configuration
    """
    server = create_server_from_config(config)
    
    try:
        await server.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


async def main_stdio() -> None:
    """Run MCP server with stdio transport (default for IDE integration)."""
    config = create_default_server_config()
    await run_server_with_config(config)


async def main_sse(host: str = "localhost", port: int = 8000) -> None:
    """Run MCP server with SSE transport for HTTP connections.
    
    Args:
        host: Host to bind to
        port: Port to bind to
    """
    config = create_default_server_config()
    config["transports"] = [{"type": "sse", "host": host, "port": port}]
    await run_server_with_config(config)


async def main_websocket(host: str = "localhost", port: int = 8001) -> None:
    """Run MCP server with WebSocket transport.
    
    Args:
        host: Host to bind to
        port: Port to bind to
    """
    config = create_default_server_config()
    config["transports"] = [{"type": "websocket", "host": host, "port": port}]
    await run_server_with_config(config)


async def main_multi_transport() -> None:
    """Run MCP server with multiple transports."""
    config = create_default_server_config()
    config["transports"] = [
        {"type": "stdio"},
        {"type": "sse", "host": "localhost", "port": 8000},
        {"type": "websocket", "host": "localhost", "port": 8001}
    ]
    await run_server_with_config(config)


def main() -> None:
    """Main entry point for command line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCPlease MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "websocket", "multi"],
        default="stdio",
        help="Transport type to use (default: stdio)"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host to bind to for network transports (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to for network transports (default: 8000)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Run appropriate server
    try:
        if args.transport == "stdio":
            asyncio.run(main_stdio())
        elif args.transport == "sse":
            asyncio.run(main_sse(args.host, args.port))
        elif args.transport == "websocket":
            asyncio.run(main_websocket(args.host, args.port + 1))  # Use different port
        elif args.transport == "multi":
            asyncio.run(main_multi_transport())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()