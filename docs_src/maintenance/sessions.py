import os
from datetime import UTC, datetime, timedelta

from gravitywell import PiHole, PiHoleAuth

idle_since = datetime.now(UTC) - timedelta(hours=1)

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    for session in api.sessions.list().sessions:
        if session.app and not session.current_session and session.last_active < idle_since:
            api.sessions.delete(session.id)  # an app's session, idle for an hour
