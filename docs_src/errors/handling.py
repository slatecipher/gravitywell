import os

import httpx2
from clientx import ArgumentError
from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    try:
        api.config.add_dns_record("192.168.1.10", "nas.lan")
    except httpx2.HTTPStatusError as error:
        if error.response.status_code == 403:
            print("Turn on webserver.api.app_sudo to change settings with an application password.")
        else:
            # Pi-hole's reason, such as a record that exists already.
            print(error.response.json()["error"]["message"])
    except httpx2.RequestError as error:
        print(f"Couldn't reach the Pi-hole: {error}")

    try:
        api.groups.delete("Default")
    except ArgumentError as error:
        print(error)  # gravitywell refused, and deleted nothing
