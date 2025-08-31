# Playground for the Unix Domain Socket Interface

A tiny testbed to exercise DTN daemons communicating over Unix Domain Sockets. The image bundles a small client that can "connect" to daemon sockets inside the container.

## Build and run
Build and run the image interactively:

```bash
docker build -t unix_dtn . && \
docker run --privileged --rm -it --name unix_dtn unix_dtn
```

Two shells are opened automatically.

## dtn7-rs

### Using the HTTP Interface
Run the sender and receiver commands:

```bash
# Sender
rs1-exec sh -lc 'printf "Hello World!" | dtn7send -r dtn://rs2/in'

# Receiver
rs2-exec sh -lc 'dtn7recv -e in'
```

The "Hello World!" message should appear on the receiver pane.

### Using the Rust Unix Domain Socket Client
Run the sender and receiver commands:

```bash
# Sender
dtnclientrs -s "/tmp/dtnd_rs1.socket" send "dtn://rs2/in" "Hello World!"

# Receiver
dtnclientrs -s "/tmp/dtnd_rs2.socket" receive "in"
```

The "Hello World!" message should appear on the receiver pane.

### Using the Go Unix Domain Socket Client
Run the sender and receiver commands:

```bash
# Sender
echo "Hello World!" | dtnclientgo create -s "dtn://rs1/" -d "dtn://rs2/in" -p "stdin" -a "/tmp/dtnd_rs1.socket"

# Receiver
dtnclientgo list -i "dtn://rs2/in" -a "/tmp/dtnd_rs2.socket"
dtnclientgo get bundle -o "stdout" -m "dtn://rs2/in" -b "<Bundle ID>" -a "/tmp/dtnd_rs2.socket"
```

The "Hello World!" message should appear on the receiver pane.


## dtn7-go

### Using the Rust Unix Domain Socket Client
Run the sender and receiver commands:

```bash
# Receiver
dtnclientrs -s "/tmp/dtnd_go2.socket" register "dtn://go2/in"

# Sender
dtnclientrs -s "/tmp/dtnd_go1.socket" send "dtn://go2/in" "Hello World!"

# Receiver
dtnclientrs -s "/tmp/dtnd_go2.socket" receive "dtn://go2/in"
dtnclientrs -s "/tmp/dtnd_go2.socket" unregister "dtn://go2/in"
```

### Using the Go Unix Domain Socket Client
Run the sender and receiver commands:

```bash
# Receiver
dtnclientgo register -i "dtn://go2/in" -a "/tmp/dtnd_go2.socket"

# Sender
echo "Hello World!" | dtnclientgo create -s "dtn://go1/" -d "dtn://go2/in" -p "stdin" -a "/tmp/dtnd_go1.socket"

# Receiver
dtnclientgo list -i "dtn://go2/in" -a "/tmp/dtnd_go2.socket"
dtnclientgo get bundle -o "stdout" -m "dtn://go2/in" -b "<Bundle ID>" -a "/tmp/dtnd_go2.socket"
dtnclientgo unregister -i "dtn://go2/in" -a "/tmp/dtnd_go2.socket"
```
