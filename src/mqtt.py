"""MQTT Module."""
import asyncio
import logging
import socket
import time

import paho.mqtt.client as mqtt

_LOGGER = logging.getLogger(__name__)


class MQTTClient:
    """MQTT Client Wrapper."""

    def __init__(
        self, screen_manager, host: str, port: str, username: str, password: str
    ):
        """Initialize the MQTT client."""
        self._mqttc = mqtt.Client()
        self.screen_manager = screen_manager
        self.loop = self.screen_manager.loop

        # Enable logging
        self._mqttc.enable_logger()

        self._msg_listners = []
        self.connected = False

        self.host = host
        self.port = port
        self._paho_lock = asyncio.Lock()

        self._connect_event: asyncio.Event = None
        

        self.on_connect = None

        if username is not None:
            self._mqttc.username_pw_set(username, password)

        # Set keep-alive interval to 60 seconds
        self._mqttc.keep_alive = 60
        self._mqttc.reconnect_delay_set(
            min_delay=1, max_delay=1800
        )  # Set reconnect delay between 1 and 1800 seconds

        self._mqttc.on_connect = self._mqtt_on_connect
        self._mqttc.on_disconnect = self._mqtt_on_disconnect
        self._mqttc.on_message = self._mqtt_on_message
        self._mqttc.on_publish = self._mqtt_on_callback
        self._mqttc.on_subscribe = self._mqtt_on_callback
        self._mqttc.on_unsubscribe = self._mqtt_on_callback
        # self._mqttc.will_set(
        #     discovery_msg["availability_topic"],
        #     payload=discovery_msg["payload_not_available"],
        #     qos=1,
        #     retain=True,
        # )

        _LOGGER.info("Client Init Complete")

    async def connect(self):
        """Connect to the MQTT broker."""

        self._connect_event = asyncio.Event()

        result = await self.loop.run_in_executor(
            None, self._mqttc.connect, self.host, self.port, 60
        )

        self._mqttc.loop_start()

        await self._connect_event.wait()
        self._connect_event = None

        return result

    async def perform_subscription(self, topic: str, qos: int):
        """Perform subscription to the given topic with the specified quality of service."""

        async with self._paho_lock:
            result, mid = await self.loop.run_in_executor(
                None, self._mqttc.subscribe, topic, qos
            )
            _LOGGER.info("Subscribing to %s, mid: %s", topic, mid)
        return result

    async def publish(self, topic: str, payload, qos: int, retain: bool):
        """Publish a MQTT payload."""

        return asyncio.run_coroutine_threadsafe(
            self._publish(topic, payload, qos, retain),
            self.loop,
        )

    async def _publish(self, topic: str, payload, qos: int, retain: bool):
        """Publish a message to the MQTT broker."""
        async with self._paho_lock:
            msg_info = await self.loop.run_in_executor(
                None, self._mqttc.publish, topic, payload, qos, retain
            )
            _LOGGER.info(
                "Transmitting message on %s: '%s', mid: %s",
                topic,
                payload,
                msg_info.mid,
            )

    def add_msg_listner(self, func):
        """Add a function to the listener."""
        self._msg_listners.append(func)

    def _mqtt_on_connect(self, _mqttc, _userdata, _flags, result_code: int):
        """Handle the on_connect event of the MQTT client."""
        if result_code != mqtt.CONNACK_ACCEPTED:
            _LOGGER.error(
                "Unable to connect to the MQTT broker: %s",
                mqtt.connack_string(result_code),
            )
            return

        if self._connect_event is not None:
            self.loop.call_soon_threadsafe(self._connect_event.set)

        self.connected = True
        _LOGGER.info(
            "Connected to MQTT server %s:%s (%s)",
            self.host,
            self.port,
            result_code,
        )

        if self.on_connect is not None:
            if asyncio.iscoroutinefunction(self.on_connect):
                asyncio.run_coroutine_threadsafe(self.on_connect(), self.loop)
            else:
                self.loop.run_in_executor(None, self.on_connect)

    def _mqtt_on_disconnect(self, _mqttc, _userdata, result_code: int):
        """Handle the on_disconnect event of the MQTT client."""

        self.connected = False
        _LOGGER.error("Client Got Disconnected")
        if result_code != 0:
            _LOGGER.error("Trying to Reconnect")
            self.reconnect_mqtt()
        else:
            _LOGGER.error("rc value: %s", str(result_code))

    def _mqtt_on_message(self, _mqttc, _userdata, msg):
        """Handle the on_message event of the MQTT client."""

        _LOGGER.info(
            "Received message on %s%s: %s",
            msg.topic,
            " (retained)" if msg.retain else "",
            msg.payload,
        )

        topic = msg.topic
        payload = msg.payload.decode()

        for func in self._msg_listners:
            if asyncio.iscoroutinefunction(func):
                asyncio.run_coroutine_threadsafe(func(topic, payload), self.loop)
            else:
                self.loop.run_in_executor(None, func, topic, payload)

    def _mqtt_on_callback(self, _mqttc, _userdata, mid, _granted_qos=None):
        """Handle the on_callback event of the MQTT client."""

    def reconnect_mqtt(self):
        """Attempt to reconnect to MQTT broker."""
        retry_count = 0
        max_retries = 10
        while retry_count < max_retries:
            try:
                self._mqttc.reconnect()
                self.connected = True
                _LOGGER.info("Reconnected successfully")
                break  # Exit the retry loop on successful reconnection
            except (ConnectionRefusedError, socket.timeout) as err:
                _LOGGER.warning("Error occurred during reconnection: %s", str(err))
                delay = 2**retry_count  # Exponential backoff
                _LOGGER.warning("Retrying in %d seconds...", delay)
                time.sleep(delay)
                retry_count += 1
        else:
            _LOGGER.error("Failed to reconnect after %d attempts", max_retries)
            asyncio.run_coroutine_threadsafe(self.screen_manager.stop(), self.loop)