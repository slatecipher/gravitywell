import os
from datetime import UTC, datetime, timedelta

import httpx2
from gravitywell import PiHole, PiHoleAuth
from gravitywell.models import TimeRange

# One client, with an application password from the environment.
# Leaving the `with` block logs out.
with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    # Each method returns a model of the whole response body: read its fields.
    print(api.dns.blocking().blocking)  # "enabled", "disabled", "failure" or "unknown"
    for domain in api.stats.top_domains(blocked=True, count=5).domains:
        print(domain.domain, domain.count)

    # The query database, over a time range whose datetimes have a timezone.
    last_week = TimeRange(start=datetime.now(UTC) - timedelta(days=7))
    print(api.stats.database.summary(last_week).sum_queries)

    # A change, then what decides the domain now, in one call.
    added = api.domains.add("deny", "exact", "ads.example.com", comment="Banner ads")
    if added.processed and added.processed.errors:
        print(added.processed.errors[0].error)
    print(api.explain_domain("ads.example.com").rules)

    # A 4xx or 5xx raises httpx2.HTTPStatusError, with the Pi-hole's reason in the body.
    try:
        api.config.add_dns_record("192.168.1.10", "nas.lan")
    except httpx2.HTTPStatusError as error:
        print(error.response.status_code, error.response.json()["error"]["message"])
