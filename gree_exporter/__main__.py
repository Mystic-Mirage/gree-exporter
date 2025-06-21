import asyncio

from environs import env

from .exporter import GreeExporter


async def main() -> None:
    port = env.int("GREE_EXPORTER_PORT", None)
    discovery_interval = env.int("GREE_EXPORTER_DISCOVERY_INTERVAL", None)
    update_interval = env.int("GREE_EXPORTER_UPDATE_INTERVAL", None)
    wait_time = env.int("GREE_EXPORTER_WAIT_INTERVAL", None)

    exporter = GreeExporter(port, discovery_interval, update_interval, wait_time)
    await exporter.start()

    try:
        await exporter.serve_forever()
    except (KeyboardInterrupt, asyncio.CancelledError):
        await exporter.stop()


asyncio.run(main())
