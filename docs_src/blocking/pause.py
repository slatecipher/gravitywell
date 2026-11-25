import os

from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    api.dns.set_blocking(False, timer=300)  # every domain gets through for five minutes

    status = api.dns.blocking()
    print(status.blocking, status.timer)  # disabled 299.9

    api.dns.set_blocking(True)  # back on now, cancelling the timer
