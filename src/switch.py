"""Sensor Module."""
from src.const import DEVICE_INFO, BASE_TOPIC, DEFAULT_QOS, DEVICE_UNIQUE_ID
from src.util import slugify
from src.entity import Entity
import json
import logging
import asyncio

LOGGER = logging.getLogger(__name__)

class SwitchEntity(Entity):
    async def register(self):
        self.discovery_msg.update({
            "command_topic": f"{BASE_TOPIC}{self.unique_id}/command",
        })
        
        discovery_topic = f"homeassistant/switch/{self.unique_id}/config"
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

class PowerSwitch(SwitchEntity):

    def __init__(self, device):
        super().__init__(device)

    @property
    def icon(self) -> str:
        return "mdi:power"
    
    @property
    def name(self) -> str:
        return "Power"
    
    async def update(self) -> str:
        soundbar_state = self.device.yam.state
        power_status = soundbar_state.get("power")
        if power_status is not None:
            if power_status is True:
                payload = "ON"
            else:
                payload = "OFF"
            await self.send_availability()
            await self.device.mqtt.publish(self.discovery_msg["state_topic"], payload, DEFAULT_QOS, True)
    
    def handle_command(self, payload):
        LOGGER.info("New Command: %s", payload)
        desired_state = payload == "ON"
        self.device.loop.create_task(self.device.yam.set_power(desired_state))

class MuteSwitch(SwitchEntity):

    def __init__(self, device):
        super().__init__(device)

    @property
    def icon(self) -> str:
        return "mdi:volume-mute"
    
    @property
    def name(self) -> str:
        return "Mute"
    
    async def update(self) -> str:
        soundbar_state = self.device.yam.state
        mute_status = soundbar_state.get("mute")
        if mute_status is not None:
            if mute_status is True:
                payload = "ON"
            else:
                payload = "OFF"
            await self.send_availability()
            await self.device.mqtt.publish(self.discovery_msg["state_topic"], payload, DEFAULT_QOS, True)
    
    def handle_command(self, payload):
        LOGGER.info("New Command: %s", payload)
        desired_state = payload == "ON"
        self.device.loop.create_task(self.device.yam.set_mute(desired_state))

class ClearVoiceSwitch(SwitchEntity):

    def __init__(self, device):
        super().__init__(device)

    @property
    def icon(self) -> str:
        return "mdi:volume-mute"
    
    @property
    def name(self) -> str:
        return "Clear Voice"
    
    async def update(self) -> str:
        soundbar_state = self.device.yam.state
        clearvoice_status = soundbar_state.get("clearvoice")
        if clearvoice_status is not None:
            if clearvoice_status is True:
                payload = "ON"
            else:
                payload = "OFF"
            await self.send_availability()
            await self.device.mqtt.publish(self.discovery_msg["state_topic"], payload, DEFAULT_QOS, True)
    
    def handle_command(self, payload):
        LOGGER.info("New Command: %s", payload)
        desired_state = payload == "ON"
        self.device.loop.create_task(self.device.yam.set_clear_voice(desired_state))

class BassBoostSwitch(SwitchEntity):

    def __init__(self, device):
        super().__init__(device)

    @property
    def icon(self) -> str:
        return "mdi:volume-mute"
    
    @property
    def name(self) -> str:
        return "Bass Boost"
    
    async def update(self) -> str:
        soundbar_state = self.device.yam.state
        bass_ext_status = soundbar_state.get("bass_ext")
        if bass_ext_status is not None:
            if bass_ext_status is True:
                payload = "ON"
            else:
                payload = "OFF"
            await self.send_availability()
            await self.device.mqtt.publish(self.discovery_msg["state_topic"], payload, DEFAULT_QOS, True)
    
    def handle_command(self, payload):
        LOGGER.info("New Command: %s", payload)
        desired_state = payload == "ON"
        self.device.loop.create_task(self.device.yam.set_bass_boost(desired_state))