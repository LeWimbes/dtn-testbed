#!/usr/bin/env python3

import argparse
import socket
import sys
import time

from dtn_client import DtnClient
from log import error, info, warning


def parse_schedule(filepath):
    """Parse a schedule file and return sorted list of commands by execution time"""
    commands = []
    lifetime = None

    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            if len(parts) == 2:
                try:
                    execution_time = int(parts[0])
                    command = parts[1]
                    if command == "LIFETIME":
                        lifetime = execution_time
                    else:
                        commands.append((execution_time, command))
                except ValueError:
                    warning(f"Warning: Invalid time value in line: {line}")

    # Sort commands by execution time
    return lifetime, sorted(commands, key=lambda x: x[0])


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run a scheduled DTN node")
    parser.add_argument("schedule_file", help="Path to the schedule file")
    args = parser.parse_args()

    # Initialize variables
    node_id = socket.gethostname()
    lifetime = None
    client = DtnClient()
    start_time = time.time()
    endpoint_registered = False
    endpoint_name = "scheduled"
    daemon_running = False

    # Parse schedule file
    try:
        lifetime, commands = parse_schedule(args.schedule_file)
    except FileNotFoundError:
        error(f"Error: Schedule file '{args.schedule_file}' not found")
        sys.exit(1)

    info(f"Starting scheduled node {node_id} with lifetime {lifetime} seconds")

    try:
        # Process each command at the scheduled time
        for execution_time, command in commands:
            # Wait until it's time to execute this command
            current_time = time.time() - start_time
            if current_time < execution_time:
                time.sleep(execution_time - current_time)

            # Execute command
            if command == "CONNECT":
                info(f"[T+{execution_time}s] Starting DTN daemon for node {node_id}")
                if not daemon_running:
                    if client.start_daemon(node_id):
                        daemon_running = True

                        # Register endpoint for messages
                        def message_callback(bundle):
                            src = bundle.get("src", "unknown")
                            data = bundle.get("data", b"").decode(
                                "utf-8", errors="ignore"
                            )
                            info(f"Received message from {src}: {data}")

                        if client.register_endpoint(endpoint_name, message_callback):
                            endpoint_registered = True
                            info(f"Registered endpoint: {endpoint_name}")
                else:
                    warning(f"[T+{execution_time}s] DTN daemon already running")

            elif command == "DISCONNECT":
                info(f"[T+{execution_time}s] Stopping DTN daemon")
                if daemon_running:
                    if endpoint_registered:
                        if client.unregister_endpoint(endpoint_name):
                            info(f"Unregistered endpoint: {endpoint_name}")
                        endpoint_registered = False

                    if client.stop_daemon():
                        daemon_running = False
                        info("DTN daemon stopped successfully")
                else:
                    warning(f"[T+{execution_time}s] DTN daemon not running")

            elif command == "MESSAGE":
                if not daemon_running:
                    warning(
                        f"[T+{execution_time}s] Can't send message - daemon not running"
                    )
                    continue

                message = f"Hello from {node_id} at {execution_time}"
                info(f"[T+{execution_time}s] Sending message: {message}")

                # Get all peers
                peers = client.get_peers()

                if not peers:
                    warning(f"[T+{execution_time}s] No peers found, message not sent")
                    continue

                # Send message to all peers
                src = f"dtn://{node_id}"
                for peer in peers:
                    dst = f"dtn://{peer}/{endpoint_name}"
                    info(f"  - Sending to {dst}")
                    client.send_bundle(src, dst, message.encode("utf-8"))

        # Wait until the lifetime is over
        current_time = time.time() - start_time
        if current_time < lifetime:
            remaining_time = lifetime - current_time
            info(f"Waiting for remaining lifetime: {remaining_time:.1f} seconds")
            time.sleep(remaining_time)

    finally:
        # Clean up at the end
        info("Shutting down scheduled node")
        if endpoint_registered:
            client.unregister_endpoint(endpoint_name)
        if daemon_running:
            client.stop_daemon()


if __name__ == "__main__":
    main()
