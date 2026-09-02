"""Minimal ZeroMQ client for the application's remote-control channel.

Run the application, then from ``app/``::

    uv run python main.py                                                   # terminal 1
    uv run python -m scripts.remote_client_example                          # terminal 2
    uv run python -m scripts.remote_client_example --command app.version
    uv run python -m scripts.remote_client_example --command terminal.append --params '{}'
"""

import argparse
import json
import sys
import time

import zmq

from src.core.config import (
    REMOTE_CONTROL_COMMAND_ENDPOINT,
    REMOTE_CONTROL_EVENT_ENDPOINT,
)
from src.core.remote.protocol import RemoteAck, RemoteEvent, RemoteRequest

# --------------------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------------------
def parse_arguments() -> argparse.Namespace:
    """Parse the client command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", default="terminal.append")
    parser.add_argument(
        "--params",
        default='{"text": "hello from outside"}',
        help="Command parameters as a JSON object.",
    )
    parser.add_argument("--command-endpoint", default=REMOTE_CONTROL_COMMAND_ENDPOINT)
    parser.add_argument("--event-endpoint", default=REMOTE_CONTROL_EVENT_ENDPOINT)
    parser.add_argument("--timeout", type=float, default=3.0)
    return parser.parse_args()

# --------------------------------------------------------------------------------------------------
# Client
# --------------------------------------------------------------------------------------------------
def main() -> int:
    """Send one command, print the acknowledgement, then print the next event."""
    arguments = parse_arguments()
    request = RemoteRequest(
        id=f"example-{int(time.time() * 1000)}",
        command=arguments.command,
        params=json.loads(arguments.params),
    )
    context = zmq.Context()
    # Event subscription (before sending, to avoid missing the reply event)
    event_socket = context.socket(zmq.SUB)
    event_socket.setsockopt(zmq.LINGER, 0)
    event_socket.setsockopt_string(zmq.SUBSCRIBE, "")
    event_socket.connect(arguments.event_endpoint)
    time.sleep(0.2)
    # Command request
    command_socket = context.socket(zmq.REQ)
    command_socket.setsockopt(zmq.LINGER, 0)
    command_socket.setsockopt(zmq.RCVTIMEO, int(arguments.timeout * 1000))
    command_socket.connect(arguments.command_endpoint)
    command_socket.send_string(request.model_dump_json())
    try:
        ack = RemoteAck.model_validate_json(command_socket.recv_string())
    except zmq.Again:
        print("No acknowledgement received (is remote control enabled?)", file=sys.stderr)
        return 1
    print(f"ack: {ack.model_dump_json()}")
    # Outcome event
    if ack.status == "accepted":
        poller = zmq.Poller()
        poller.register(event_socket, zmq.POLLIN)
        deadline = time.monotonic() + arguments.timeout
        while time.monotonic() < deadline:
            if dict(poller.poll(timeout=200)).get(event_socket) == zmq.POLLIN:
                event = RemoteEvent.model_validate_json(event_socket.recv_string())
                if event.id == request.id:
                    print(f"event: {event.model_dump_json()}")
                    break
        else:
            print("No matching event received before timeout", file=sys.stderr)
    command_socket.close()
    event_socket.close()
    context.term()
    return 0

# --------------------------------------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    raise SystemExit(main())
