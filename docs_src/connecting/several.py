import os

from gravitywell import PiHole, PiHoleAuth

# Each Pi-hole has its own application password, and each client its own PiHoleAuth.
primary_auth = PiHoleAuth(os.environ["PIHOLE_PRIMARY_PASSWORD"])
secondary_auth = PiHoleAuth(os.environ["PIHOLE_SECONDARY_PASSWORD"])

with (
    PiHole("http://192.168.1.2", auth=primary_auth) as primary,
    PiHole("http://192.168.1.3", auth=secondary_auth) as secondary,
):
    # Devices send their queries to either Pi-hole, so pause blocking on both: a domain one lets
    # through, the other would still block.
    for api in (primary, secondary):
        api.dns.set_blocking(False, timer=300)
# Leaving the block logged out of both.
