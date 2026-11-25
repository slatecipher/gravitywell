import os

from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    report = api.check_health()
    for finding in report.findings:  # in plain words, the most urgent first
        print(f"- {finding}")
    if not report.findings:
        print("Nothing to fix.")
