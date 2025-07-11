import asyncio
import logging
from contextlib import suppress

from greeclimate.device import Device
from greeclimate.deviceinfo import DeviceInfo
from greeclimate.discovery import Discovery
from greeclimate.exceptions import DeviceNotBoundError, DeviceTimeoutError
from prometheus_async.aio.web import MetricsHTTPServer, start_http_server

from .gauge import GAUGE_MAP


class GreeExporter:
    def __init__(
        self,
        port: int | None = None,
        discovery_interval: int | None = None,
        update_interval: int | None = None,
        wait_time: int | None = None,
        logger: logging.Logger | None = None,
    ):
        self.port = port or 49209
        self.discovery_interval = discovery_interval or 60
        self.update_interval = update_interval or 30
        self.wait_time = wait_time or 5

        self._event = asyncio.Event()
        self._tasks: list[asyncio.Task[None]] = []

        self._logger = logger or logging.getLogger(__name__)

        self.device_map: dict[str, Device] = {}

        self.discovery = Discovery()
        self.server: MetricsHTTPServer | None = None

    async def _bind(self, device_info: DeviceInfo) -> None:
        if device_info.mac not in self.device_map:
            device = Device(device_info)

            try:
                await device.bind()
            except (DeviceNotBoundError, DeviceTimeoutError):
                self._logger.warning("Unable to bind to a device: %r", device_info.mac)
                return

            self.device_map[device.device_info.mac] = device

            await self._update_state(device)

    async def _discover(self) -> None:
        while True:
            devices = await self.discovery.scan(wait_for=self.wait_time)
            await asyncio.gather(*[self._bind(device) for device in devices])
            await asyncio.sleep(self.discovery_interval)

    async def _update_state(self, device: Device) -> None:
        try:
            await device.update_state(wait_for=self.wait_time)
        except (DeviceNotBoundError, DeviceTimeoutError):
            self._logger.warning(
                "Failed to update device data: %r", device.device_info.mac
            )
            return

        for gauge, prop in GAUGE_MAP.items():
            with suppress(TypeError):
                if (value := getattr(device, prop)) is not None:
                    gauge.labels(mac=device.device_info.mac).set(value)

    async def _update(self) -> None:
        while True:
            await asyncio.gather(
                *[self._update_state(device) for device in self.device_map.values()]
            )
            await asyncio.sleep(self.update_interval)

    async def start(self) -> None:
        for task in (self._discover, self._update):
            self._tasks.append(asyncio.create_task(task()))

        self._event.clear()
        self.server = await start_http_server(port=self.port)

    async def serve_forever(self) -> None:
        await self._event.wait()

    async def stop(self) -> None:
        self._event.set()

        for task in self._tasks:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

        if self.server:
            await self.server.close()

        self.server = None
