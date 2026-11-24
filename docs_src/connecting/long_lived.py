import atexit
import os

from gravitywell import PiHole, PiHoleAuth

# One client for the whole app: it logs in once and reuses the session.
api = PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"]))
atexit.register(api.close)  # log out when the app exits


def blocked_today() -> int:
    return api.stats.summary().queries.blocked


print(blocked_today())
