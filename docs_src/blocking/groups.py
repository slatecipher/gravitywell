import os

from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    kids = api.groups.add("Kids", comment="Stricter rules").groups[0]

    # The tablet stays in the Default group (ID 0), so the usual blocking applies too.
    api.clients.add("192.168.1.50", comment="Tablet", groups=[0, kids.id])

    # A rule only the Kids group's clients get.
    api.domains.add("deny", "regex", r"(\.|^)videos\.example$", groups=[kids.id])
