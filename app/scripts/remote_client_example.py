"""Minimal ZeroMQ client for the application's remote-control channel.

Run the application, then from ``app/``::

    uv run python main.py                                                   # terminal 1
    uv run python -m scripts.remote_client_example --command some.command   # terminal 2
    uv run python -m scripts.remote_client_example --command some.command --params '{"x": 1}'
"""

import argparse
import json
import sys

import zmq

from src.core.config import REMOTE_CONTROL_ENDPOINT
from src.core.remote.protocol import RemoteRequest, RemoteResponse

# --------------------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------------------
def parse_arguments() -> argparse.Namespace:
    """Parse the client command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", required=True)
    parser.add_argument("--params", default="{}", help="Command parameters as a JSON object.")
    parser.add_argument("--endpoint", default=REMOTE_CONTROL_ENDPOINT)
    parser.add_argument("--timeout", type=float, default=3.0)
    return parser.parse_args()

# --------------------------------------------------------------------------------------------------
# Client
# --------------------------------------------------------------------------------------------------
def main() -> int:
    """Send one command and print the response."""
    arguments = parse_arguments()
    request = RemoteRequest(command=arguments.command, params=json.loads(arguments.params))
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.LINGER, 0)
    socket.setsockopt(zmq.RCVTIMEO, int(arguments.timeout * 1000))
    socket.connect(arguments.endpoint)
    socket.send_string(request.model_dump_json())
    try:
        response = RemoteResponse.model_validate_json(socket.recv_string())
    except zmq.Again:
        print("No response received (is the application running?)", file=sys.stderr)
        return 1
    finally:
        socket.close()
        context.term()
    print(response.model_dump_json())
    return 0 if response.ok else 1

# --------------------------------------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    raise SystemExit(main())
