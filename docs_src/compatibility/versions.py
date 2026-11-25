import os

from gravitywell import PIHOLE_VERSIONS, PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    ftl = api.info.version().version.ftl.local.version
    tested = PIHOLE_VERSIONS["ftl"]  # v6.9
    if ftl != tested:
        print(f"This Pi-hole runs FTL {ftl}; gravitywell was tested against FTL {tested}.")
