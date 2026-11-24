# Async clients

`AsyncPiHole` has the same API areas and methods as `PiHole`, as `async def` methods: `await` each one. It takes the same arguments, and the same `PiHoleAuth`.

<!-- docs_src/readme/quickstart_async.py -->
```python
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
```

## Closing

Leave its `async with` block, or call `await api.aclose()`, to log out of the Pi-hole. An async app, such as a web service or a bot, creates one client at startup and closes it at shutdown, the way [Sessions](connecting.md#sessions) describes for the sync client.

## Concurrent requests

`asyncio.gather()`, or a task group, sends several requests at once. They share one login: the first request logs in, and the others wait for it rather than each opening a session of its own.

<!-- docs_src/async_clients/concurrent.py -->
```python
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
```

## Streaming

A Teleporter backup arrives as a stream of bytes. On `AsyncPiHole`, `await` the method to start the download, then iterate over its chunks with `async for`:

<!-- docs_src/async_clients/streaming.py -->
```python
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
```

## Event loops

gravitywell runs on asyncio. `PiHoleAuth` works with the sync and async clients alike, but give each client its own: it holds that client's session.
