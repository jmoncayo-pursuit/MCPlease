#!/usr/bin/env python3
"""Start the MCP stdio server and call health/check to verify connectivity.

Usage:
  python scripts/check_mcp_health.py

Requires:
  - Run inside the project venv so the 'mcp' package is available
"""

import json
import os
import sys
import time
import subprocess


def send_message(proc, payload: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    header = f"Content-Length: {len(data)}\r\n\r\n".encode("ascii")
    proc.stdin.write(header)
    proc.stdin.write(data)
    proc.stdin.flush()


def read_message(proc, timeout_seconds: float = 5.0) -> dict:
    start = time.time()
    header_bytes = b""
    # Read headers until CRLF CRLF
    while b"\r\n\r\n" not in header_bytes:
        if time.time() - start > timeout_seconds:
            raise TimeoutError("Timed out waiting for header")
        chunk = proc.stdout.read(1)
        if not chunk:
            raise RuntimeError("Server closed stdout while reading header")
        header_bytes += chunk

    header_text = header_bytes.decode("ascii", errors="replace")
    content_length = None
    for line in header_text.split("\r\n"):
        if line.lower().startswith("content-length:"):
            try:
                content_length = int(line.split(":", 1)[1].strip())
            except Exception:
                pass
    if content_length is None:
        raise ValueError(f"Missing Content-Length in header: {header_text!r}")

    body = proc.stdout.read(content_length)
    if not body or len(body) != content_length:
        raise RuntimeError("Incomplete body read")
    return json.loads(body.decode("utf-8"))


def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    server_path = os.path.join(repo_root, "mcplease_mcp_server.py")
    if not os.path.exists(server_path):
        print(f"Server not found: {server_path}")
        return 1

    # Start server
    proc = subprocess.Popen(
        [sys.executable, "-u", server_path],
        cwd=repo_root,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
    )

    try:
        # initialize
        send_message(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "health-check", "version": "0.1.0"},
                },
            },
        )
        init_resp = read_message(proc)

        # tools/list
        send_message(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            },
        )
        list_resp = read_message(proc)

        # tools/call health/check
        send_message(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "health/check", "arguments": {}},
            },
        )
        call_resp = read_message(proc)

        # Print concise summary
        tool_names = [t["name"] for t in list_resp.get("result", {}).get("tools", [])]
        print("initialize_ok:", "error" not in init_resp)
        print("has_health_check:", "health/check" in tool_names)
        content = call_resp.get("result", {}).get("content", [])
        if content and isinstance(content, list) and content[0].get("type") == "text":
            print("health_check:", content[0]["text"])
        else:
            print("health_check:", call_resp)

        return 0
    finally:
        try:
            proc.terminate()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())


