from src.mqtt import MQTTClient
from src.yamaha import SoundBar
import logging
import json
from src.const import DEVICE_INFO, DEVICE_NAME, DEVICE_UNIQUE_ID, DEFAULT_QOS

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
        with open("config.json") as f:
            self.conf = json.loads(f.read())

        self.mqtt = MQTTClient(
            self,
            self.conf["host"],
            self.conf["port"],
            self.conf["username"],
            self.conf["password"],
        )

        self.yam = SoundBar(self.conf["bt_addr"])
    
    async def run(self):
        """Run the ScreenManager."""
        async def on_connect():
            await self.register()

        self.mqtt.on_connect = on_connect
        await self.yam.connect()
        await self.mqtt.connect()
    
    async def register(self):
        # Publish the discovery message to Home Assistant
        discovery_topic = f"homeassistant/media_player/{MEDIA_PLAYER_DEVICE_ID}/config"
        await self.mqtt.publish(
            discovery_topic, json.dumps(discovery_msg), DEFAULT_QOS, True
        )