"""Sensor Module."""
from src.const import DEVICE_INFO, BASE_TOPIC, DEFAULT_QOS, DEVICE_UNIQUE_ID
from src.util import slugify
from src.entity import Entity
import json

MAX_VOLUME = 50

class SensorEntity(Entity):
    async def register(self):       
        discovery_topic = f"homeassistant/sensor/{self.unique_id}/config"
        self.discovery_msg["unit_of_measurement"] = "%"
        await self.device.mqtt.publish(
            discovery_topic, json.dumps(self.discovery_msg), DEFAULT_QOS, True
        )

        await self.send_availability()

        await self.update()

class VolumeSensor(SensorEntity):

    def __init__(self, device):
        super().__init__(device)

    @property
    def icon(self) -> str:
        return "mdi:volume-high"
    
    @property
    def name(self) -> str:
        return "Volume"
    
    async def update(self) -> str:
        soundbar_state = self.device.yam.state
        volume = soundbar_state.get("volume")
        if volume is not None:
            volume_percentage = (volume / MAX_VOLUME)

            await self.device.mqtt.publish(self.discovery_msg["state_topic"], volume_percentage, DEFAULT_QOS, True)
        await self.send_availability()