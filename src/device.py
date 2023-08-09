from src.mqtt import MQTTClient
from src.yamaha import SoundBar
import logging
import json
from src.const import DEVICE_INFO, DEVICE_NAME, DEVICE_UNIQUE_ID, DEFAULT_QOS, BASE_TOPIC
import os
import asyncio
from src.sensor import VolumeSensor
from src.select import InputSelect, SurroundSelect
from src.switch import PowerSwitch, MuteSwitch, ClearVoiceSwitch, BassBoostSwitch
from src.button import VolumeDownButton, VolumeUpButton, ToggleBluetoothStandbyButton
import anyio

_LOGGER = logging.getLogger(__name__)

MEDIA_PLAYER_ID = "media_player"
MEDIA_PLAYER_DEVICE_ID = DEVICE_UNIQUE_ID + "_" + MEDIA_PLAYER_ID

# Define the MQTT discovery message
discovery_msg = {
    "name": DEVICE_NAME,
    "unique_id": MEDIA_PLAYER_DEVICE_ID,
    "state_topic": f"home/{DEVICE_UNIQUE_ID}/{MEDIA_PLAYER_ID}/state",
    "command_topic": f"home/{DEVICE_UNIQUE_ID}/{MEDIA_PLAYER_ID}/set",
    "payload_on": "ON",
    "payload_off": "OFF",
    "device": DEVICE_INFO,
    "availability_topic": f"home/{DEVICE_UNIQUE_ID}/{MEDIA_PLAYER_ID}/availability",
    "payload_available": "online",
    "payload_not_available": "offline",
    "json_attributes_topic": f"home/{DEVICE_UNIQUE_ID}/{MEDIA_PLAYER_ID}/attributes",
}

class Device:
    def __init__(self):
        self.conf = get_config()
        self.loop = asyncio.get_event_loop()
        self.old_state = {}

        self.mqtt = MQTTClient(
            self,
            self.conf["host"],
            self.conf["port"],
            self.conf["username"],
            self.conf["password"],
        )

        self.yam = SoundBar(self.conf["bt_addr"])
        self.yam.state_update_callback = self.state_updated

        self.entities = []

        self.shutdown: asyncio.Event = None
    
    async def run(self):
        """Run the ScreenManager."""
        async def on_connect():
            await self.register()

        self.mqtt.on_connect = on_connect
        await self.yam.connect()
        await self.mqtt.connect()

        self.shutdown = asyncio.Event()

        self.entities.append(VolumeSensor(self))
        self.entities.append(InputSelect(self))
        self.entities.append(SurroundSelect(self))
        self.entities.append(PowerSwitch(self))
        self.entities.append(MuteSwitch(self))
        self.entities.append(BassBoostSwitch(self))
        self.entities.append(ClearVoiceSwitch(self))
        self.entities.append(VolumeUpButton(self))
        self.entities.append(VolumeDownButton(self))
        self.entities.append(ToggleBluetoothStandbyButton(self))
        
        await self.shutdown.wait()

    
    async def state_updated(self, new_state):
        if new_state == self.old_state:
            return
        _LOGGER.info(f"New State: {new_state}")

        self.old_state = new_state
        for entity in self.entities:
            asyncio.create_task(entity.update())
    
    async def register(self):
        # Publish the discovery message to Home Assistant
        for entity in self.entities:
            await entity.register()

def get_config():
    """Get MQTT config from environment."""
    mqtt_conf = {
        "host": os.environ.get("MQTT_HOST"),
        "port": int(os.environ.get("MQTT_PORT", 1883)),  # Use default port 1883 if not provided
        "username": os.environ.get("MQTT_USERNAME"),
        "password": os.environ.get("MQTT_PASSWORD"),
        "bt_addr": os.environ.get("BT_ATTR"),
    }

    # Validate the configuration
    if not mqtt_conf["host"]:
        raise ValueError("MQTT_HOST environment variable is not set.")
    if not mqtt_conf["username"]:
        raise ValueError("MQTT_USERNAME environment variable is not set.")
    if not mqtt_conf["password"]:
        raise ValueError("MQTT_PASSWORD environment variable is not set.")

    # Additional validation and type conversion can be added as needed

    return mqtt_conf
