from yamaha_bt.device import Device
import anyio
import logging
import argparse
import os, subprocess
import json

LOGGER = logging.getLogger(__name__)

def get_args():
    parser = argparse.ArgumentParser(description="Yamaha BT Module")
    parser.add_argument("--install-service", action="store_true", help="Install the service so it runs on boot")

    args = parser.parse_args()

    return args

def install_service():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    service_path = os.path.join(script_dir, "systemd/yamaha_bt.service")
    subprocess.call(['sudo', 'cp', service_path, '/etc/systemd/system/'])
    subprocess.call(['sudo', 'systemctl', 'daemon-reload'])
    subprocess.call(['sudo', 'systemctl', 'enable', 'yamaha_bt'])
    # subprocess.call(['sudo', 'systemctl', 'start', 'yamaha_bt'])

async def run():
    device = Device()
    await device.run()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    LOGGER.info(json.dumps(dict(os.environ), indent=2))

    args = get_args()
    if args.install_service:
        install_service()
    else:
        anyio.run(run)
