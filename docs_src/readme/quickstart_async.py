import asyncio
import os

from gravitywell import AsyncPiHole, PiHoleAuth


async def main() -> None:
    auth = PiHoleAuth(os.environ["PIHOLE_PASSWORD"])
    async with AsyncPiHole("http://pi.hole", auth=auth) as api:
        summary, top = await asyncio.gather(
            api.stats.summary(),
            api.stats.top_domains(blocked=True, count=5),
        )
        print(f"{summary.queries.percent_blocked:.1f}% of queries blocked")
        for domain in top.domains:
            print(f"{domain.count:>6}  {domain.domain}")


asyncio.run(main())
