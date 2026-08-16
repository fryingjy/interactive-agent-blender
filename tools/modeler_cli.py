"""Call one command on the typed Blender modeler socket.

This dependency-free CLI is useful for interactive development sessions where the
MCP wrapper is unavailable. It exposes the same length-prefixed JSON protocol and
does not add any unrestricted Blender execution path.
"""

from __future__ import annotations

import argparse
import json
import socket
import struct


def recv_exact(sock: socket.socket, length: int) -> bytes:
    data = b""
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise ConnectionError("modeler server closed the connection")
        data += chunk
    return data


def call(command: str, params: dict, *, host: str = "localhost", port: int = 9878) -> object:
    with socket.create_connection((host, port), timeout=30) as sock:
        payload = json.dumps({"id": "cli", "command": command, "params": params}).encode("utf-8")
        sock.sendall(struct.pack(">I", len(payload)) + payload)
        (length,) = struct.unpack(">I", recv_exact(sock, 4))
        response = json.loads(recv_exact(sock, length).decode("utf-8"))
    if response.get("status") != "ok":
        raise RuntimeError(response.get("message", "unknown modeler error"))
    return response.get("result")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command")
    parser.add_argument("params", nargs="?", default="{}", help="JSON object")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", default=9878, type=int)
    args = parser.parse_args()
    params = json.loads(args.params)
    if not isinstance(params, dict):
        raise TypeError("params must decode to a JSON object")
    print(json.dumps(call(args.command, params, host=args.host, port=args.port), indent=2))


if __name__ == "__main__":
    main()
