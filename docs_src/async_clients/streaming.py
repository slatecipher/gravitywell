import asyncio
import os
from pathlib import Path

from gravitywell import AsyncPiHole, PiHoleAuth


async def main() -> None:
    async with AsyncPiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
        with Path("pihole-backup.zip").open("wb") as file:
            async for chunk in await api.teleporter.export():
                file.write(chunk)


asyncio.run(main())
