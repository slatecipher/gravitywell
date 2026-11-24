import os
from datetime import UTC, datetime, timedelta

from gravitywell import PiHole, PiHoleAuth
from gravitywell.models import TimeRange

last_week = TimeRange(start=datetime.now(UTC) - timedelta(days=7))  # `until` is now by default

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    summary = api.stats.database.summary(last_week)
    print(f"{summary.sum_queries:,} queries last week, {summary.percent_blocked:.1f}% blocked")

    for domain in api.stats.database.top_domains(last_week, blocked=True).domains:
        print(f"{domain.count:>6}  {domain.domain}")
