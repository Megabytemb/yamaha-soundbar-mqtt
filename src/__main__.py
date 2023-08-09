from src.device import Device
import anyio
import logging

async def run():
    device = Device()
    await device.run()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    anyio.run(run)
