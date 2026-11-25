import os

from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    summary = api.stats.summary()
    print(f"{summary.queries.total:,} queries, {summary.queries.percent_blocked:.1f}% blocked")
    print(f"{summary.gravity.domains_being_blocked:,} domains on the blocklists")

    for client in api.stats.top_clients(count=5).clients:
        print(f"{client.count:>6}  {client.name or client.ip}")
