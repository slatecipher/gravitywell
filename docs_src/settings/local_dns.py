import os

from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    api.config.add_dns_record("192.168.1.10", "nas.lan")  # nas.lan answers 192.168.1.10
    api.config.add_cname_record("files.lan", "nas.lan")  # files.lan is an alias of nas.lan

    for record in api.config.dns_records().records:
        print(record.ip, " ".join(record.hostnames))
    for alias in api.config.cname_records().records:
        print(", ".join(alias.domains), "->", alias.target)
