from yamaha_bt.const import BASE_TOPIC, DEFAULT_QOS, DEVICE_UNIQUE_ID, DEVICE_INFO
from yamaha_bt.util import slugify
import json

class Entity:

    def __init__(self, device):
        """Init Entity."""
        self.device = device
        self.discovery_msg = {
            "device": DEVICE_INFO,
            "availability_topic": f"{BASE_TOPIC}{self.unique_id}/availability",
            "payload_available": "online",
            "payload_not_available": "offline",
            "name": self.name,
            "icon": self.icon,
            "unique_id": self.unique_id,
            "state_topic": f"{BASE_TOPIC}{self.unique_id}/state",
        }

    
    async def register(self):
        raise NotImplementedError
    
    @property
    def unique_id(self) -> str:
        return f"{DEVICE_UNIQUE_ID}_{slugify(self.name)}"
    
    @property
    def name(self) -> str:
        return "default sensor"
    
    @property
    def icon(self) -> str:
        return None
    
    async def update(self) -> str:
        raise NotImplementedError
    
    async def send_availability(self, available=None) -> str:
        # Publish the discovery message to Home Assistant
        if available is None:
            available = self.device.yam.connected

        availability_topic = self.discovery_msg["availability_topic"]
        if available is True:
            payload = self.discovery_msg["payload_available"]
        else:
            payload = self.discovery_msg["payload_not_available"]
        await self.device.mqtt.publish(
            availability_topic, payload, DEFAULT_QOS, False
        )
