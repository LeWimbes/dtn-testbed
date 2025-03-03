import glob
import os
import pathlib
import shutil

from core.emulator.coreemu import CoreEmu
from core.emulator.data import InterfaceData
from core.emulator.enumerations import EventTypes
from core.nodes.base import CoreNode, Position
from core.nodes.network import WlanNode


def clean_results_dir():
    """Clean up the results directory before running a new test."""
    results_dir = "/root/results"
    # Create if it doesn't exist
    os.makedirs(results_dir, exist_ok=True)

    # Remove any files in the root of the results directory
    for file_path in glob.glob(os.path.join(results_dir, "*")):
        if os.path.isfile(file_path):
            os.remove(file_path)


def organize_results():
    """Move results to a new numbered subdirectory after the test is complete."""
    results_dir = "/root/results"

    # Find the highest numbered subdirectory
    highest_num = -1
    for dir_name in os.listdir(results_dir):
        dir_path = os.path.join(results_dir, dir_name)
        if os.path.isdir(dir_path) and dir_name.isdigit():
            highest_num = max(highest_num, int(dir_name))

    # Create new subdirectory with the next number
    new_subdir_num = highest_num + 1
    new_subdir = os.path.join(results_dir, str(new_subdir_num))
    os.makedirs(new_subdir, exist_ok=True)

    # Move log and csv files to the new subdirectory
    for extension in ["*.log", "*.csv"]:
        for file_path in glob.glob(os.path.join(results_dir, extension)):
            if os.path.isfile(file_path):
                shutil.move(file_path, new_subdir)

    print(f"Test results saved to {new_subdir}")


def main():
    # Clean up results directory before starting
    clean_results_dir()

    coreemu = CoreEmu()
    session = coreemu.create_session()
    session.service_manager.load(pathlib.Path("/root/dtn-testbed/eval/core_services"))

    # enter the configuration state
    session.set_state(EventTypes.CONFIGURATION_STATE)

    # create WLAN node
    wlan = session.add_node(WlanNode, name="wlan", position=Position(x=0, y=0))

    # create nodes
    # add multicast capabilities for peer discovery
    options = CoreNode.create_options()
    options.model = "mdr"
    options.services.append("DefaultMulticastRoute")
    options.services.append("pidstat")
    options.services.append("bwm")
    position = Position(x=0, y=100)
    n1 = session.add_node(CoreNode, name="n1", position=position, options=options)
    options = CoreNode.create_options()
    options.model = "mdr"
    options.services.append("DefaultMulticastRoute")
    options.services.append("pidstat")
    options.services.append("bwm")
    position = Position(x=100, y=0)
    n2 = session.add_node(CoreNode, name="n2", position=position, options=options)
    options = CoreNode.create_options()
    options.model = "mdr"
    options.services.append("DefaultMulticastRoute")
    options.services.append("pidstat")
    options.services.append("bwm")
    position = Position(x=0, y=-100)
    n3 = session.add_node(CoreNode, name="n3", position=position, options=options)

    # link nodes to wlan
    # use /24 net mask for automatic routes configuration (https://github.com/coreemu/core/issues/658)
    iface1 = InterfaceData(ip4="10.0.0.1", ip4_mask=24)
    session.add_link(n1.id, wlan.id, iface1)
    iface1 = InterfaceData(ip4="10.0.0.2", ip4_mask=24)
    session.add_link(n2.id, wlan.id, iface1)
    iface1 = InterfaceData(ip4="10.0.0.3", ip4_mask=24)
    session.add_link(n3.id, wlan.id, iface1)

    print("Starting session...")

    # start the session
    session.instantiate()

    n2.cmd(
        "python /root/dtn-testbed/dtn7-rs_python/scheduled_node.py /root/dtn-testbed/dtn7-rs_python/schedule2",
        wait=False,
    )
    n3.cmd(
        "python /root/dtn-testbed/dtn7-rs_python/scheduled_node.py /root/dtn-testbed/dtn7-rs_python/schedule3",
        wait=False,
    )
    out = n1.cmd(
        "python /root/dtn-testbed/dtn7-rs_python/scheduled_node.py /root/dtn-testbed/dtn7-rs_python/schedule1",
        wait=True,
    )
    print(f"\n\n\n{out}\n\n\n")

    print("Stopping session...")

    session.shutdown()
    coreemu.delete_session(session.id)

    # Organize results after the session completes
    organize_results()


if __name__ == "__main__":
    main()
