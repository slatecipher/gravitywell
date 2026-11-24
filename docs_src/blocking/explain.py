import os

from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    why = api.explain_domain("ads.example.com")
    print(f"Blocking is {why.blocking}")
    for rule in why.rules:
        groups = ", ".join(why.groups[group] for group in rule.groups)
        print(f"{rule.type} rule ({rule.kind}) {rule.domain}, for {groups}")
    for match in why.lists:
        print(f"On the {match.type}list {match.address}")
    for query in why.recent_queries:
        print(query.time, query.client.ip, query.status)
