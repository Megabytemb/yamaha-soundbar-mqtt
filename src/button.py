"""Sensor Module."""
from src.const import DEVICE_INFO, BASE_TOPIC, DEFAULT_QOS, DEVICE_UNIQUE_ID
from src.util import slugify
from src.entity import Entity
import json
import logging
import asyncio

LOGGER = logging.getLogger(__name__)

class ButtonEntity(Entity):
    async def register(self):
        self.discovery_msg.update({
            "command_topic": f"{BASE_TOPIC}{self.unique_id}/command",
        })
        
        
        discovery_topic = f"homeassistant/button/{self.unique_id}/config"
        await self.device.mqtt.publish(
            discovery_topic, json.dumps(self.discovery_msg), DEFAULT_QOS, True
        )

        self.device.mqtt.add_msg_listner(self._handle_message)
        await self.device.mqtt.perform_subscription(
            self.discovery_msg["command_topic"], DEFAULT_QOS
        )

        await self.send_availability()

        await self.update()
    
    
    def _handle_message(self, topic, payload):
        if topic == self.discovery_msg["command_topic"]:
            return self.handle_command(payload)
    
    def handle_command(self, payload):
        return 
    
    async def update(self):
        await self.send_availability()

class VolumeUpButton(ButtonEntity):

    def __init__(self, device):
        super().__init__(device)

    @property
    def icon(self) -> str:
        return "mdi:volume-plus"
    
    @property
    def name(self) -> str:
        return "Volume Up"
    

    def handle_command(self, payload):
        self.device.loop.create_task(self.device.yam.volume_up())

class VolumeDownButton(ButtonEntity):

    def __init__(self, device):
        super().__init__(device)

    @property
    def icon(self) -> str:
        return "mdi:volume-minus"
    
    @property
    def name(self) -> str:
        return "Volume Down"
    

    def handle_command(self, payload):
        self.device.loop.create_task(self.device.yam.volume_down())

class ToggleBluetoothStandbyButton(ButtonEntity):

    def __init__(self, device):
        super().__init__(device)

    @property
    def icon(self) -> str:
        return "mdi:bluetooth"
    
    @property
    def name(self) -> str:
        return "Bluetooth Standby"
    
    def handle_command(self, payload):
        self.device.loop.create_task(self.device.yam.toggle_bl_standby())