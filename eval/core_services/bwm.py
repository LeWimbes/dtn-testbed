from typing import Optional

from core.config import Configuration
from core.services.base import CoreService, ServiceMode, ShadowDir


class BwmService(CoreService):
    # globally unique name for service
    name: Optional[str] = "bwm"
    # group to categorize service within
    group: Optional[str] = "Logging"
    # directories to create unique mount points for
    directories: list[str] = []
    # files to create for service
    files: list[str] = []
    # configurable values that this service can use, for file generation
    default_configs: list[Configuration] = []
    # executables that should exist on path, that this service depends on
    executables: list[str] = ["bwm-ng"]
    # other services that this service depends on, defines service start order
    dependencies: list[str] = []
    # commands to run to start this service
    startup: list[str] = [
        "nohup bwm-ng --timeout=1000 --unit=bytes --type=rate --output=csv -F /root/results/$(hostname).bwm.csv > /root/results/$(hostname).bwm.err.log 2>&1 &"
    ]
    # commands to run to validate this service
    validate: list[str] = ["pgrep -x bwm-ng >/dev/null"]
    # commands to run to stop this service
    shutdown: list[str] = ["pkill -TERM -x bwm-ng"]
    # validation mode, blocking, non-blocking, and timer
    validation_mode: ServiceMode = ServiceMode.NON_BLOCKING
    # predefined configuration value groupings
    modes: dict[str, dict[str, str]] = {}
    # validation period in seconds, how frequent validation is attempted
    validation_period: float = 0.5
    # time to wait in seconds for determining if service started successfully
    validation_timer: int = 5
    # directories to shadow and copy files from
    shadow_directories: list[ShadowDir] = []
