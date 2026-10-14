"""Exercise real TCP handshake fragmentation and command/event forwarding."""
import importlib.util
import json
from pathlib import Path
import socket
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("bridge", ROOT / "systemview_bridge.py")
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class BridgeProtocolTests(unittest.TestCase):
    def test_fragmented_handshake(self):
        hello = b"SEGGER SystemView V4.10.02\0".ljust(32, b"\0")
        sender, receiver = socket.socketpair()
        try:
            sender.sendall(hello[:7])
            sender.sendall(hello[7:19])
            sender.sendall(hello[19:] + b"\x01")
            self.assertEqual(bridge.receive_hello(receiver), hello)
            self.assertEqual(receiver.recv(1), b"\x01")
        finally:
            sender.close()
            receiver.close()

    def test_invalid_handshake(self):
        sender, receiver = socket.socketpair()
        try:
            sender.sendall(b"not a SystemView client".ljust(32, b"\0"))
            with self.assertRaises(RuntimeError):
                bridge.receive_hello(receiver)
        finally:
            sender.close()
            receiver.close()

    def test_forwarding_and_disconnect_stops_trace(self):
        # The fixture stands for the raw RTT socket. No debugger is accessed.
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(3)
        app, peer = socket.socketpair()
        app.settimeout(3)
        sessions = []
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / "sessions.json"
            worker = threading.Thread(target=bridge.run_session,
                args=(peer, listener.getsockname()[1], sessions, log), daemon=True)
            worker.start()
            backend = None
            try:
                # Coalescing hello and START must preserve the first command.
                app.sendall(b"SEGGER SystemView V4.10.02\0".ljust(32, b"\0") + b"\x01")
                backend, _ = listener.accept()
                backend.settimeout(3)
                hello = bytearray()
                while len(hello) < 32:
                    hello.extend(app.recv(32 - len(hello)))
                self.assertEqual(bytes(hello), bridge.TARGET_HELLO)
                self.assertEqual(backend.recv(1), b"\x01")
                events = b"\x00" * 10 + b"\x0a\x00\x18\x00"
                backend.sendall(events[:5])
                backend.sendall(events[5:])
                received = bytearray()
                while len(received) < len(events):
                    received.extend(app.recv(len(events) - len(received)))
                self.assertEqual(bytes(received), events)
                app.close()
                self.assertEqual(backend.recv(1), b"\x02")
                worker.join(3)
                self.assertFalse(worker.is_alive())
                report = json.loads(log.read_text())["sessions"][0]
                self.assertTrue(report["handshake_completed"])
                self.assertEqual(report["target_to_host_bytes"], len(events))
                self.assertEqual(report["host_to_target_bytes"], 1)
                self.assertNotIn("error", report)
            finally:
                app.close()
                listener.close()
                if backend:
                    backend.close()


if __name__ == "__main__":
    unittest.main()
