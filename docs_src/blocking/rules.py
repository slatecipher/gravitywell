import os

from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    # Block one domain exactly, and a domain with all its subdomains by regex.
    api.domains.add("deny", "exact", "ads.example.com", comment="Banner ads")
    api.domains.add("deny", "regex", r"(\.|^)tracker\.example$")

    # Several domains at once: `processed` says which were saved, and why others weren't.
    result = api.domains.add("allow", "exact", ["cdn.example.com", "login.example.com"])
    if result.processed:
        for failure in result.processed.errors:
            print(f"{failure.item}: {failure.error}")

    for rule in api.domains.list().domains:
        print(rule.type, rule.kind, rule.domain, "enabled" if rule.enabled else "disabled")

    # Stop blocking a domain by moving its deny rule to allow, then remove the rule.
    api.domains.move(
        "ads.example.com", from_type="deny", from_kind="exact", to_type="allow", to_kind="exact"
    )
    api.domains.delete("allow", "exact", "ads.example.com")
