"""Yamaha Module."""
import socket
import asyncio
import anyio
from datetime import datetime, timedelta
import logging

LOGGER = logging.getLogger(__name__)

HEARTBEAT_INTERVAL = timedelta(seconds=1)

# Mapping of input values to names
INPUT_NAMES = {
    0x0: 'hdmi',
    0xc: 'analog',
    0x5: 'bluetooth',
    0x7: 'tv',
}

# Mapping of surround values to names
SURROUND_NAMES = {
    0x0d: '3d',
    0x0a: 'tv',
    0x0100: 'stereo',
    0x03: 'movie',
    0x08: 'music',
    0x09: 'sports',
    0x0c: 'game',
}

COMMANDS = {
    # power management
    'power_toggle': "4078cc",
    'power_on': "40787e",
    'power_off': "40787f",

    # input management
    'set_input_hdmi': "40784a",
    'set_input_analog': "4078d1",
    'set_input_bluetooth': "407829",
    'set_input_tv': "4078df",

    # surround management
    'set_surround_3d': "4078c9", # -- 3d surround
    'set_surround_tv': "407ef1", # -- tv program
    'set_surround_stereo': "407850",
    'set_surround_movie': "4078d9",
    'set_surround_music': "4078da",
    'set_surround_sports': "4078db",
    'set_surround_game': "4078dc",
    'surround_toggle': "4078b4", # -- sets surround to `:movie` (or `:"3d"` if already `:movie`)
    'clearvoice_toggle': "40785c",
    'clearvoice_on': "407e80",
    'clearvoice_off': "407e82",
    'bass_ext_toggle': "40788b",
    'bass_ext_on': "40786e",
    'bass_ext_off': "40786f",

    # volume management
    'subwoofer_up': "40784c",
    'subwoofer_down': "40784d",
    'mute_toggle': "40789c",
    'mute_on': "407ea2",
    'mute_off': "407ea3",
    'volume_up': "40781e",
    'volume_down': "40781f",

    # extra -- IR -- don't use?
    'bluetooth_standby_toggle': "407834",
    'dimmer': "4078ba",

    # status report (query, soundbar returns a message)
    'report_status': "0305"
}



def csum(len, pload):
    return -(len + sum(pload)) & 0xff

def encode(packet) -> bytes:
    if isinstance(packet, str):
        pload = bytearray.fromhex(packet)
        csum_value = csum(len(pload), pload)
        return bytes([0xcc, 0xaa, len(pload), *pload, csum_value])
    else:
        pload = list(packet)
        csum_value = csum(len(pload), pload)
        return ''.join([chr(x) for x in [0xcc, 0xaa, len(pload)] + pload + [csum_value]])

class SoundBar:
    def __init__(self, bt_attr, bt_port=1, loop=None):
        self.bt_attr = bt_attr
        self.bt_port = bt_port
        self.loop = loop

        self.reader = None
        self.writer = None

        self.reader_task = None
        self.heartbeat_task = None
        self.watchdog_task = None
        self.state = {}
        self.state_update_callback = None
        self.connected = False
        self.last_recieved = datetime.now()

        self.sock: socket.socket = None
    
    async def set_surround(self, surround):
        surround_str = "set_surround_" + surround
        command = COMMANDS.get(surround_str)
        if command is None:
            raise ValueError("Surround not found")
        await self._send_command(command)
        await self.report_status()
    
    async def set_input(self, input):
        input_str = "set_input_" + input
        command = COMMANDS.get(input_str)
        if command is None:
            raise ValueError("Input not found")
        await self._send_command(command)
        await self.report_status()
    
    async def set_power(self, power: bool):
        if power is True:
            command = COMMANDS["power_on"]
        else:
            command = COMMANDS["power_off"]
        await self._send_command(command)
        if power is False:
            await self.close()

        await self.report_status()
    
    async def set_bass_boost(self, state: bool):
        if state is True:
            command = COMMANDS["bass_ext_on"]
        else:
            command = COMMANDS["bass_ext_off"]
        await self._send_command(command)
        await self.report_status()
    
    async def set_clear_voice(self, state: bool):
        if state is True:
            command = COMMANDS["clearvoice_on"]
        else:
            command = COMMANDS["clearvoice_off"]
        await self._send_command(command)
        await self.report_status()
    
    async def set_mute(self, mute: bool):
        if mute is True:
            command = COMMANDS["mute_on"]
        else:
            command = COMMANDS["mute_off"]
        await self._send_command(command)
        await self.report_status()
    
    async def volume_up(self):
        command = COMMANDS["volume_up"]
        await self._send_command(command)
        await self.report_status()
    
    async def volume_down(self):
        command = COMMANDS["volume_down"]
        await self._send_command(command)
        await self.report_status()
    
    async def toggle_bl_standby(self):
        command = COMMANDS["bluetooth_standby_toggle"]
        await self._send_command(command)
        await self.report_status()
    
    async def report_status(self):
        command = COMMANDS["report_status"]
        await self._send_command(command)
    
    async def _heartbeat(self):
        while True:
            await self.report_status()
            await asyncio.sleep(HEARTBEAT_INTERVAL.seconds)
    
    async def _watchdog(self):
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL.seconds*3)
            now = datetime.now()
            diff = now - self.last_recieved
            if diff.seconds > HEARTBEAT_INTERVAL.seconds*3:
                LOGGER.warning("Watchdog Triggered.")
                break
        await self.reconnect()
            
    
    async def handle_recieved(self):
        while True:
            data = await self.reader.read(1024)
            LOGGER.debug("Received", data.hex())
            self.last_recieved = datetime.now()
            self.state = self.parse_device_status(data)
            if self.state_update_callback is not None:
                asyncio.create_task(self.state_update_callback(self.state))
    
    def _connect_to_socket(self):
        """Create a connection to the socket."""
        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        sock.settimeout(1)
        try:
            sock.connect((self.bt_attr, self.bt_port))
        except Exception as e:
            sock.close()
            raise e

        return sock
    
    async def connect(self, forground_retry=False):
        while self.connected is False:
            LOGGER.info("Trying to connect to Soundbar.")
            try:
                async with anyio.fail_after(1):
                    self.sock = await anyio.to_thread.run_sync(self._connect_to_socket)
                    self.reader, self.writer = await asyncio.open_connection(sock=self.sock)
                    self.connected = True
            except Exception as e:
                LOGGER.debug(str(e))
                await asyncio.sleep(1)
                
                if forground_retry is False:
                    LOGGER.info("re-trying in background task.")
                    asyncio.create_task(self.connect(True))
                    return


        LOGGER.info("Connected to Soundbar.")
        self.reader_task = asyncio.create_task(self.handle_recieved())
        self.heartbeat_task = asyncio.create_task(self._heartbeat())
        
        if self.watchdog_task is None:
            self.watchdog_task = asyncio.create_task(self._watchdog())
        await self.report_status()
    
    async def close(self):
        self.connected = False
        if self.writer:
            self.writer.close()
        if self.sock:
            await anyio.to_thread.run_sync(self.sock.close)

        asyncio.create_task(self.state_update_callback({}))
        
        if self.reader_task is not None:
            self.reader_task.cancel()
            self.reader_task = None
        
        if self.heartbeat_task is not None:
            self.heartbeat_task.cancel()
            self.heartbeat_task = None
        
        # if self.watchdog_task is not None:
        #     self.watchdog_task.cancel()
        #     self.watchdog_task = None
    
    async def reconnect(self):
        await self.close()
        await self.connect()
    
    async def _send_command(self, command):
        packet = encode(command)
        self.writer.write(packet)
        try:
            await self.writer.drain()
        except:
            await self.reconnect()
    
    @staticmethod
    def parse_device_status(pkt):
        pkt = pkt[3:]
        # remove the first 4 bytes, which is <ccaa><length><type>
        params = {}
        params['power'] = pkt[2] != 0
        params['input'] = INPUT_NAMES.get(pkt[3])
        params['mute'] = pkt[4] != 0
        params['volume'] = pkt[5]
        params['subwoofer'] = pkt[6]
        srd = (pkt[10] << 8) + pkt[11]
        params['surround'] = SURROUND_NAMES.get(srd, srd)
        params['bass_ext'] = not (pkt[12] & 0x20 == 0)
        params['clearvoice'] = not (pkt[12] & 0x4 == 0)
        return params
