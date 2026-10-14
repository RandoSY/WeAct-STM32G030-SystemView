#!/usr/bin/env python3
"""SystemView IP handshake bridge to RTT channel 1 in VS Code's OpenOCD.

Python standard library only. This never launches a debug server or flashes
firmware. The 32-byte handshake follows yapicoprobe's net_sysview.c protocol.
"""
import argparse
import datetime
import json
from pathlib import Path
import re
import selectors
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
HELLO_SIZE = 32
TARGET_HELLO = b"SEGGER SystemView V3.32.00\0".ljust(HELLO_SIZE, b"\0")


def find_tcl_port(explicit):
    if explicit:
        return explicit
    if sys.platform != "win32":
        raise RuntimeError("Pass --tcl-port with the active OpenOCD TCL port")
    query = ('Get-CimInstance Win32_Process -Filter "Name = \'openocd.exe\'" | '
             'Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress')
    result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", query],
                            capture_output=True, text=True, check=True)
    rows = json.loads(result.stdout or "[]")
    if isinstance(rows, dict):
        rows = [rows]
    normalized_root = str(ROOT).replace("\\", "/").lower()
    matches = []
    for row in rows:
        command = (row.get("CommandLine") or "").replace("\\", "/")
        if normalized_root not in command.lower():
            continue
        match = re.search(r"(?:tcl_port|tcl port)\s+(\d+)", command)
        if match:
            matches.append(int(match[1]))
    if len(matches) != 1:
        raise RuntimeError("Start exactly one debug session for this project, "
                           "or pass its --tcl-port explicitly")
    return matches[0]


def tcl_command(port, command):
    with socket.create_connection(("127.0.0.1", port), timeout=3) as connection:
        connection.sendall(command.encode("utf-8") + b"\x1a")
        response = bytearray()
        while not response.endswith(b"\x1a"):
            part = connection.recv(16384)
            if not part:
                raise RuntimeError("OpenOCD closed the TCL connection")
            response.extend(part)
        return response[:-1].decode("utf-8", errors="replace")


def receive_hello(connection):
    data = bytearray()
    while len(data) < HELLO_SIZE:
        part = connection.recv(HELLO_SIZE - len(data))
        if not part:
            raise RuntimeError("Client disconnected during the IP handshake")
        data.extend(part)
    if not data.startswith(b"SEGGER SystemView"):
        raise RuntimeError("Client did not send a SystemView IP hello")
    return bytes(data)


def run_session(client, rtt_port, sessions, log_path):
    record = {"started": datetime.datetime.now().isoformat(timespec="seconds"),
              "target_to_host_bytes": 0, "host_to_target_bytes": 0}
    backend = None
    try:
        client.settimeout(5)
        hello = receive_hello(client)
        record["host_hello"] = hello.rstrip(b"\0").decode("ascii", errors="replace")
        backend = socket.create_connection(("127.0.0.1", rtt_port), timeout=3)
        for connection in (client, backend):
            connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            connection.settimeout(3)
        client.sendall(TARGET_HELLO)
        record["handshake_completed"] = True
        print("SystemView connected: " + record["host_hello"], flush=True)
        with selectors.DefaultSelector() as selector:
            selector.register(client, selectors.EVENT_READ, "host")
            selector.register(backend, selectors.EVENT_READ, "target")
            connected = True
            while connected:
                for key, _ in selector.select(timeout=1):
                    data = key.fileobj.recv(65536)
                    if not data:
                        connected = False
                        break
                    if key.data == "host":
                        backend.sendall(data)
                        record["host_to_target_bytes"] += len(data)
                    else:
                        client.sendall(data)
                        record["target_to_host_bytes"] += len(data)
    except (OSError, RuntimeError) as error:
        record["error"] = str(error)
        print("Connection: " + str(error), flush=True)
    finally:
        if backend is not None:
            # Stop tracing if the recorder disappears without its STOP command.
            try:
                backend.sendall(b"\x02")
            except OSError:
                pass
            backend.close()
        client.close()
        record["ended"] = datetime.datetime.now().isoformat(timespec="seconds")
        sessions.append(record)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps({"sessions": sessions}, indent=2) + "\n")
        print("Session ended: " + str(record["target_to_host_bytes"]) +
              " event bytes forwarded", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=19111)
    parser.add_argument("--rtt-port", type=int, default=19022)
    parser.add_argument("--tcl-port", type=int)
    parser.add_argument("--sessions-log", type=Path,
                        default=ROOT / "validation/systemview_bridge_sessions.json")
    args = parser.parse_args()
    for port in (args.port, args.rtt_port, args.tcl_port):
        if port is not None and not 1 <= port <= 65535:
            parser.error("Ports must be between 1 and 65535")
    tcl_port = find_tcl_port(args.tcl_port)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        # Binding first prevents a duplicate bridge from changing the RTT reader.
        server.bind(("127.0.0.1", args.port))
        server.listen(1)
        channels = tcl_command(tcl_port, "rtt channels")
        if "SysView" not in channels:
            raise RuntimeError("RTT channel 1 is not initialized; run the trace demo first")
        result = tcl_command(tcl_port,
                             f"set rc [catch {{rtt server start {args.rtt_port} 1}} msg]; list $rc $msg")
        if result.startswith("1 "):
            # An existing server on this port is normal after restarting the bridge.
            with socket.create_connection(("127.0.0.1", args.rtt_port), timeout=1):
                pass
        tcl_command(tcl_port, "rtt polling_interval 5")
        print(f"SystemView IP bridge ready: 127.0.0.1:{args.port} -> "
              f"OpenOCD RTT channel 1 on {args.rtt_port}; TCL {tcl_port}", flush=True)
        sessions = []
        if args.sessions_log.exists():
            sessions = json.loads(args.sessions_log.read_text()).get("sessions", [])
        while True:
            client, _ = server.accept()
            run_session(client, args.rtt_port, sessions, args.sessions_log)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("SystemView bridge stopped.", flush=True)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        sys.exit(1)
