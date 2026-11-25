import os

from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    [setting] = api.config.settings("database.maxDBdays").settings
    print(setting.value, setting.default, setting.description)

    # All or none: an invalid value changes nothing, and raises with Pi-hole's reason.
    api.config.update({"database.maxDBdays": 30, "dns.dnssec": True})
