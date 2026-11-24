import asyncio
import os

from gravitywell import AsyncPiHole, PiHoleAuth


async def main() -> None:
    async with AsyncPiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
        # Three requests at once. They share one login: the first logs in, the others wait for it.
        blocking, summary, health = await asyncio.gather(
            api.dns.blocking(),
            api.stats.summary(),
            api.check_health(),
        )
        print(blocking.blocking, summary.queries.total, health.findings)


asyncio.run(main())
