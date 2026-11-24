import os

from gravitywell import PiHole, PiHoleAuth

auth = PiHoleAuth(os.environ["PIHOLE_PASSWORD"])  # an application password

with PiHole("http://pi.hole", auth=auth) as api:
    summary = api.stats.summary()  # GET /api/stats/summary -> SummaryResponse
    print(f"{summary.queries.percent_blocked:.1f}% of queries blocked in the last 24 hours")

    status = api.dns.blocking()  # GET /api/dns/blocking -> BlockingResponse
    print(f"Blocking is {status.blocking}")  # enabled

    api.dns.set_blocking(False, timer=300)  # pause blocking for five minutes

    why = api.explain_domain("ads.example.com")  # rules, lists and recent queries in one call
    for rule in why.rules:
        print(f"{rule.type} rule ({rule.kind}): {rule.domain}")
