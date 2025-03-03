import json
import subprocess
import threading
import time
import urllib.request

import websocket
from cbor2 import dumps, loads
from log import debug, error, info, warning


class DtnClient:
    def __init__(self):
        self.node_id = None
        self.daemon_process = None
        self.ws = None
        self.callback = None
        self.receive_ready = False
        self.ws_thread = None

    def register_endpoint(self, endpoint_name, callback_function):
        """
        Register an endpoint and set up a WebSocket to receive bundles.

        Args:
            endpoint_name (str): Name of the endpoint to register
            callback_function (callable): Function called when a bundle arrives
                Will receive bundle data dict (src, dst, bid, data)

        Returns:
            bool: Success status
        """
        if self.ws:
            warning("WebSocket already connected")
            return False

        # Register the endpoint via HTTP API
        try:
            register_url = f"http://127.0.0.1:3000/register?{endpoint_name}"
            response = urllib.request.urlopen(register_url).read().decode("utf-8")
            if not response.startswith("Registered"):
                error(f"Failed to register endpoint: {response}")
                return False
            info(f"Registered endpoint {endpoint_name}: {response}")
        except Exception as e:
            error(f"Error registering endpoint {endpoint_name}: {str(e)}")
            return False

        # Store callback and initialize state
        self.callback = callback_function
        self.receive_ready = False

        def on_open(ws):
            info(f"WebSocket connected for endpoint {endpoint_name}")
            debug("Sending /data command to WebSocket")
            ws.send("/data")  # Switch to data mode

        def on_message(ws, message):
            if not self.receive_ready:
                if message == "200 tx mode: data":
                    info("Mode changed to 'data'")
                    debug(f"Sending subscription request for {endpoint_name}")
                    ws.send(f"/subscribe {endpoint_name}")
                elif message == "200 subscribed":
                    info(f"Successfully subscribed to {endpoint_name}")
                    self.receive_ready = True
                    debug("WebSocket is now ready to send/receive data")
            else:
                if isinstance(message, str):
                    # Handle text messages
                    if not message.startswith("200"):
                        error(f"Received Error: {message}")
                else:
                    # Handle binary messages
                    try:
                        bundle_data = loads(message)
                        debug(
                            f"Received bundle: src={bundle_data.get('src', 'unknown')}"
                        )
                        self.callback(bundle_data)
                    except Exception as e:
                        error(f"Error processing binary bundle: {str(e)}")
                        debug(f"Raw message: {message}")

        def on_error(ws, error_msg):
            error(f"WebSocket error: {error_msg}")

        def on_close(ws, close_status_code, close_msg):
            info(f"WebSocket closed: {close_status_code}")

        # Create and start WebSocket in a thread
        self.ws = websocket.WebSocketApp(
            "ws://127.0.0.1:3000/ws",
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )

        self.ws_thread = threading.Thread(target=self.ws.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()

        return True

    def unregister_endpoint(self, endpoint_name, timeout=5):
        """
        Close WebSocket and unregister the endpoint.

        Args:
            endpoint_name (str): Name of the endpoint to unregister
            timeout (int): Seconds to wait for WebSocket to close

        Returns:
            bool: Success status
        """
        # Unsubscribe from the endpoint if WebSocket is connected
        if self.ws and self.ws.sock and self.receive_ready:
            try:
                self.ws.send(f"/unsubscribe dtn://{self.node_id}/{endpoint_name}")
                # Give time for unsubscribe to process
                time.sleep(0.5)
            except Exception as e:
                error(f"Error unsubscribing from endpoint: {str(e)}")

        # Close WebSocket connection if it exists
        if self.ws:
            self.ws.close()

            # Wait for the thread to finish
            if self.ws_thread:
                self.ws_thread.join(timeout)
                self.ws_thread = None
            self.ws = None
            self.receive_ready = False

        # Unregister the endpoint via HTTP API
        try:
            unregister_url = f"http://127.0.0.1:3000/unregister?{endpoint_name}"
            response = urllib.request.urlopen(unregister_url).read().decode("utf-8")
            if not response.startswith("Unregistered"):
                error(f"Failed to unregister endpoint: {response}")
                return False
            info(f"Unregistered endpoint: {endpoint_name}")
            return True
        except Exception as e:
            error(f"Error unregistering endpoint: {str(e)}")
            return False

    def send_bundle(self, src, dst, data, lifetime_ms=1000):
        """
        Send a bundle through the WebSocket.

        Args:
            src (str): Source endpoint
            dst (str): Destination endpoint
            data (bytes): Payload data
            lifetime_ms (int): Bundle lifetime in milliseconds

        Returns:
            bool: Success status
        """
        if not self.receive_ready:
            warning("WebSocket not ready")
            return False

        try:
            bundle = {
                "src": src,
                "dst": dst,
                "delivery_notification": False,
                "lifetime": lifetime_ms,
                "data": data,
            }

            encoded_bundle = dumps(bundle)
            debug(f"Sending bundle: {src} -> {dst}")
            self.ws.send(encoded_bundle, opcode=2)  # binary mode
            return True
        except Exception as e:
            error(f"Error sending bundle: {str(e)}")
            return False

    def get_peers(self):
        """
        Get a list of all currently known peer names.

        Returns:
            list: List of peer names
        """
        try:
            # Make the HTTP request
            response = urllib.request.urlopen("http://127.0.0.1:3000/status/peers")

            # Parse the JSON response
            peers_data = json.loads(response.read().decode("utf-8"))

            # Extract peer names (keys in the JSON object)
            peer_names = list(peers_data.keys())

            return peer_names
        except Exception as e:
            error(f"Error retrieving peers: {str(e)}")
            return []

    def start_daemon(self, node_id, routing="epidemic", cla="mtcp"):
        """
        Start the DTN daemon (dtnd) with the specified parameters.

        Args:
            node_id (str): The node identifier
            routing (str): Routing algorithm (default: 'epidemic')
            cla (str): Convergence Layer Adapter (default: 'mtcp')

        Returns:
            bool: True if daemon started successfully, False otherwise
        """
        if self.daemon_process:
            warning("DTN daemon is already running")
            return False

        self.node_id = node_id

        cmd = [
            "dtnd",
            "-n",
            self.node_id,
            "-i",
            "1s",
            "-b",
            "-r",
            routing,
            "-C",
            cla,
        ]

        try:
            # Start the daemon process
            self.daemon_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            # Give time for the daemon to initialize
            time.sleep(1)

            # Check if process is running
            if self.daemon_process.poll() is None:
                info(f"DTN daemon started with node ID: {self.node_id}")
                return True
            else:
                stdout, stderr = self.daemon_process.communicate()
                error(f"Failed to start DTN daemon: {stderr}")
                self.daemon_process = None
                return False
        except Exception as e:
            error(f"Error starting DTN daemon: {str(e)}")
            self.daemon_process = None
            return False

    def stop_daemon(self, timeout=5):
        """
        Stop the running DTN daemon process.

        Args:
            timeout (int): Seconds to wait for graceful termination (default: 5)

        Returns:
            bool: True if daemon was stopped successfully, False otherwise
        """
        if not self.daemon_process:
            warning("No DTN daemon is running")
            return False

        try:
            # Try to terminate gracefully first
            self.daemon_process.terminate()

            # Wait for the process to terminate
            for _ in range(timeout):
                if self.daemon_process.poll() is not None:
                    info("DTN daemon stopped gracefully")
                    self.daemon_process = None
                    return True
                time.sleep(1)

            # Force kill if it doesn't terminate
            self.daemon_process.kill()
            self.daemon_process.wait()
            info("DTN daemon terminated forcefully")
            self.daemon_process = None
            return True
        except Exception as e:
            error(f"Error stopping DTN daemon: {str(e)}")
            return False

    def __del__(self):
        """Ensure daemon process is terminated when the client is destroyed"""
        if self.daemon_process:
            try:
                self.daemon_process.kill()
            except Exception as _:
                pass
