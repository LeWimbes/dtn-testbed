import inspect
import logging
import os
import socket
import sys

# Global logger instance
logger = None


def setup_logger():
    """
    Set up the logger to output to both console and a file named after the hostname.
    Returns the configured logger instance.
    """
    global logger
    if logger is not None:
        return logger

    # Get hostname for the log filename
    hostname = socket.gethostname()

    # Create the results directory if it doesn't exist
    log_dir = "/root/results/"
    os.makedirs(log_dir, exist_ok=True)

    # Create log file in the results directory
    log_filename = os.path.join(log_dir, f"{hostname}.log")

    # Create logger
    logger = logging.getLogger("dtn_logger")
    logger.setLevel(logging.DEBUG)

    # Create formatter with more context
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - [%(caller_file)s:%(caller_line)d] - %(message)s"
    )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Create file handler
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def get_logger():
    """Get the logger instance, setting it up if needed."""
    global logger
    if logger is None:
        logger = setup_logger()
    return logger


# Convenience functions
def debug(msg):
    """Log a debug message."""
    caller = inspect.getframeinfo(inspect.stack()[1][0])
    get_logger().debug(
        msg,
        extra={
            "caller_file": os.path.basename(caller.filename),
            "caller_line": caller.lineno,
        },
    )


def info(msg):
    """Log an info message."""
    caller = inspect.getframeinfo(inspect.stack()[1][0])
    get_logger().info(
        msg,
        extra={
            "caller_file": os.path.basename(caller.filename),
            "caller_line": caller.lineno,
        },
    )


def warning(msg):
    """Log a warning message."""
    caller = inspect.getframeinfo(inspect.stack()[1][0])
    get_logger().warning(
        msg,
        extra={
            "caller_file": os.path.basename(caller.filename),
            "caller_line": caller.lineno,
        },
    )


def error(msg):
    """Log an error message."""
    caller = inspect.getframeinfo(inspect.stack()[1][0])
    get_logger().error(
        msg,
        extra={
            "caller_file": os.path.basename(caller.filename),
            "caller_line": caller.lineno,
        },
    )


def critical(msg):
    """Log a critical message."""
    caller = inspect.getframeinfo(inspect.stack()[1][0])
    get_logger().critical(
        msg,
        extra={
            "caller_file": os.path.basename(caller.filename),
            "caller_line": caller.lineno,
        },
    )
