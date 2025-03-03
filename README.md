# Playground for DTN7-rs & CORE

## Running the Test

See [Getting Started](#getting-started) for instructions on how to set up the environment.

Now just run the following commands to run the test:

```bash
docker compose up -d && \
sleep 5 && \
docker exec -it core_eval bash -c "python /root/dtn-testbed/eval/run_eval.py" && \
docker compose down
```

## Getting Started

First you need to clone the repository and create the virtual environment:

```bash
git clone git@github.com:LeWimbes/dtn-testbed.git && \
cd dtn-testbed && \
uv sync --frozen
```

## Accessing a Python Interpreter with CORE Bindings

The simplest way to use the Python interpreter with CORE is via **Dev Containers**. Although they are not yet
well-supported in PyCharm, you can still use Docker as a remote interpreter.

### Visual Studio Code

Refer to
the [official documentation for Visual Studio Code](https://code.visualstudio.com/docs/devcontainers/create-dev-container)
for more details.  
Using the provided `.devcontainer` configuration is as easy as clicking **Reopen in Container** in the bottom right
corner of Visual Studio Code.

### PyCharm Professional

Follow these steps based on
the [official documentation for PyCharm Professional](https://www.jetbrains.com/help/pycharm/using-docker-as-a-remote-interpreter.html):

1. Go to **File** → **Settings** → **Project: ucp-eval** → **Python Interpreter**.
2. Click on **Add Interpreter**.
3. Select **Docker**.
4. Choose `Dockerfile`.
5. Select the interpreter located at `/opt/core/venv/bin/python`.
