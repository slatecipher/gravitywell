import os
import ssl

from gravitywell import PiHole, PiHoleAuth

# The certificate authority the Pi-hole created, copied from /etc/pihole/tls_ca.crt on the Pi-hole.
context = ssl.create_default_context(cafile="tls_ca.crt")

auth = PiHoleAuth(os.environ["PIHOLE_PASSWORD"])
with PiHole("https://pi.hole", auth=auth, verify=context) as api:
    print(api.dns.blocking().blocking)
