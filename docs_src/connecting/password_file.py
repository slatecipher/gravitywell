import os
from pathlib import Path

from gravitywell import PiHole, PiHoleAuth

# The path of a file that holds the password, such as a Docker or Kubernetes secret.
password_file = Path(os.environ["PIHOLE_PASSWORD_FILE"])


def read_password() -> str:
    # `echo password > file` ends the file with a newline, which isn't part of the password.
    return password_file.read_text().strip()


# PiHoleAuth calls read_password() at each login: before the first request, and after a 401.
with PiHole("http://pi.hole", auth=PiHoleAuth(read_password)) as api:
    print(api.dns.blocking().blocking)
