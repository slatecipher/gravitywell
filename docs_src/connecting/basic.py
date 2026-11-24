import os

from gravitywell import PiHole, PiHoleAuth

auth = PiHoleAuth(os.environ["PIHOLE_PASSWORD"])

with PiHole("http://pi.hole", auth=auth) as api:  # logs in on the first request
    versions = api.info.version().version
    print(f"FTL {versions.ftl.local.version}")
# Leaving the block logged out.
