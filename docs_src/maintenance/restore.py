import os
from pathlib import Path

from gravitywell import PiHole, PiHoleAuth
from gravitywell.models import GravityTables, RestoreParts

# Restore the rules, lists and groups, but keep this Pi-hole's settings, leases and clients.
tables = GravityTables(client=False, client_by_group=False)
parts = RestoreParts(config=False, dhcp_leases=False, gravity=tables)

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    restored = api.teleporter.restore(Path("pihole-backup.zip").read_bytes(), parts)
    print("\n".join(restored.files))
