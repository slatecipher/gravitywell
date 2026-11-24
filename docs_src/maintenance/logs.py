import os
import time

from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    log = api.logs.ftl(lines=20)  # the newest 20 lines
    while True:
        for line in log.log:
            print(line.timestamp, line.prio or "", line.message)
        time.sleep(5)
        next_id = log.next_id
        log = api.logs.ftl(next_id=next_id)  # only the lines written since
        if log.next_id < next_id:  # FTL restarted, and its log started over
            log = api.logs.ftl()
