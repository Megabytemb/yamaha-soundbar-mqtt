"""Sensor Module."""
from yamaha_bt.const import DEVICE_INFO, BASE_TOPIC, DEFAULT_QOS, DEVICE_UNIQUE_ID
from yamaha_bt.util import slugify
from yamaha_bt.entity import Entity
import json
import logging
import asyncio

LOGGER = logging.getLogger(__name__)

INPUT_MAPPING = {
    "hdmi": "HDMI",
    "analog": "Analog",
    "bluetooth": "BT",
    "tv": "TV",
}

SURROUND_MAPPING = {
    "3d": "3D",
    "tv": "TV",
    "stereo": "Stereo",
    "movie": "Movie",
    "music": "Music",
    "sports": "Sports",
    "game": "Game",
}

def get_key_by_value(dictionary, target_value):
    return next((key for key, value in dictionary.items() if value == target_value), None)


class SelectEntity(Entity):
    async def register(self):
        self.discovery_msg.update({
            "command_topic": f"{BASE_TOPIC}{self.unique_id}/command",
            "options": self.options,
        })
        
        discovery_topic = f"homeassistant/select/{self.unique_id}/config"
        await self.device.mqtt.publish(
            discovery_topic, json.dumps(self.discovery_msg), DEFAULT_QOS, True
        )

        self.device.mqtt.add_msg_listner(self._handle_message)
        await self.device.mqtt.perform_subscription(
            self.discovery_msg["command_topic"], DEFAULT_QOS
        )

        await self.send_availability()

        await self.update()
    
    @property
    def options(self):
        return []
    
    def _handle_message(self, topic, payload):
        if topic == self.discovery_msg["command_topic"]:
            return self.handle_command(payload)
    
    def handle_command(self, payload):
        return 

class InputSelect(SelectEntity):

    def __init__(self, device):
        super().__init__(device)

    @property
    def icon(self) -> str:
        return "mdi:video-input-hdmi"
    
    @property
    def name(self) -> str:
        return "Input"
    
    @property
    def options(self):
        return list(INPUT_MAPPING.values())
    
    async def update(self) -> str:
        soundbar_state = self.device.yam.state
        current_input = soundbar_state.get("input")
        if current_input is not None:
            current_input = INPUT_MAPPING[current_input]
            await self.device.mqtt.publish(self.discovery_msg["state_topic"], current_input, DEFAULT_QOS, True)
        await self.send_availability()
    
    def handle_command(self, payload):
        LOGGER.info("New Command: %s", payload)
        new_input = get_key_by_value(INPUT_MAPPING, payload)
        self.device.loop.create_task(self.device.yam.set_input(new_input))
        return 


class SurroundSelect(SelectEntity):

    def __init__(self, device):
        super().__init__(device)

    @property
    def icon(self) -> str:
        return "mdi:surround-sound"
    
    @property
    def name(self) -> str:
        return "Surround"
    
    @property
    def options(self):
        return list(SURROUND_MAPPING.values())
    
    async def update(self) -> str:
        soundbar_state = self.device.yam.state
        current_surround = soundbar_state.get("surround")
        if current_surround is not None:
            current_surround = SURROUND_MAPPING[current_surround]
            await self.device.mqtt.publish(self.discovery_msg["state_topic"], current_surround, DEFAULT_QOS, True)
        await self.send_availability()
    
    def handle_command(self, payload):
        LOGGER.info("New Command: %s", payload)
        new_input = get_key_by_value(SURROUND_MAPPING, payload)
        self.device.loop.create_task(self.device.yam.set_surround(new_input))
        return 