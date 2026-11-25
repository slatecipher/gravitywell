import os

from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    # What did the tablet ask for that a blocklist blocked?
    page = api.queries.log(client_ip="192.168.1.50", upstream="blocklist", count=50)
    for query in page.queries:
        print(query.time, query.domain, query.status)

    # The next page skips the first 50, with the first page's cursor so new queries don't shift it.
    if page.records_filtered > 50:
        page = api.queries.log(
            client_ip="192.168.1.50", upstream="blocklist", count=50, start=50, cursor=page.cursor
        )
