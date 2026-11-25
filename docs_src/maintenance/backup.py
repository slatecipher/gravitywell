import os
from pathlib import Path

from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    # The archive holds password hashes: keep it as safe as a password.
    with Path("pihole-backup.zip").open("wb") as file:
        for chunk in api.teleporter.export():
            file.write(chunk)
