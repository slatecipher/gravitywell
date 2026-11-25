# Connecting to a Pi-hole

A client takes the Pi-hole's URL and a `PiHoleAuth` with its password. It logs in on its first request, reuses that session for every request after it, and logs out when it closes:

<!-- docs_src/connecting/basic.py -->
```python
import os

from gravitywell import PiHole, PiHoleAuth

auth = PiHoleAuth(os.environ["PIHOLE_PASSWORD"])

with PiHole("http://pi.hole", auth=auth) as api:  # logs in on the first request
    versions = api.info.version().version
    print(f"FTL {versions.ftl.local.version}")
# Leaving the block logged out.
```

## The URL

Pass the address of the Pi-hole's web interface: `http://pi.hole`, its IP address, such as `http://192.168.1.2`, or another name that reaches it. Add the port if the web interface isn't on the default one, such as `http://192.168.1.2:8080`.

The REST API is under `/api`, and the client sets the URL's path to it, so `http://pi.hole/api` works too, and any other path, such as `/admin`, is replaced.

## Passwords

`PiHoleAuth` takes the password the web interface asks for. Use an **application password** rather than the main one: create it in the web interface, under **Settings › Web interface / API**.

- It keeps the main password out of your scripts and their configuration.
- It works when the main password has two-factor authentication on. gravitywell can't send two-factor codes, so with two-factor authentication on, an application password is the only way to log in.
- Some endpoints refuse an application password unless the Pi-hole allows it: see [Settings that need `app_sudo`](#settings-that-need-app_sudo).

Read the password from the environment or a secret store, never from your code:

```bash
export PIHOLE_PASSWORD='...'   # or a .env file your app loads
```

To read the password at each login instead, pass a function that returns it. A client logs in before its first request and again after a `401`, so a new password in a secret file, such as a Kubernetes secret that's updated in place, takes effect at the next login, with no restart:

<!-- docs_src/connecting/password_file.py -->
```python
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
```

`AsyncPiHole` calls the function in its event loop, so keep it quick: reading a file is, but a password manager's command can take a second.

A Pi-hole without a password still takes a login, so pass an empty one: `PiHoleAuth("")`.

## Sessions

A Pi-hole allows only a few sessions at a time, and ends the ones left idle. A client is careful with them:

- It logs in once, before its first request (`POST /api/auth`), and sends the session in the `X-FTL-SID` header, never in the URL, which httpx2 logs at `INFO`.
- Concurrent requests share that one login.
- When the session has expired, the Pi-hole answers `401`: the client logs in again, once, and sends the request again.
- Closing the client logs out (`DELETE /api/auth`), so its session doesn't hold one of the Pi-hole's few until it expires.

Close a client by leaving its `with` block, or by calling `close()` (`await aclose()` for `AsyncPiHole`). An app that talks to the Pi-hole all day keeps one client for its whole life, and closes it at shutdown:

<!-- docs_src/connecting/long_lived.py -->
```python
import atexit
import os

from gravitywell import PiHole, PiHoleAuth

# One client for the whole app: it logs in once and reuses the session.
api = PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"]))
atexit.register(api.close)  # log out when the app exits


def blocked_today() -> int:
    return api.stats.summary().queries.blocked


print(blocked_today())
```

To see the sessions logged in to a Pi-hole, and log out the ones apps left open, use [`api.sessions`](maintenance.md#sessions).

## HTTPS

A Pi-hole serves its web interface and API over HTTPS too, with a certificate it creates and signs itself at install time. Python doesn't trust that certificate, so tell the client to, with `verify=`. Copy the Pi-hole's certificate authority, `/etc/pihole/tls_ca.crt`, from the Pi-hole, and pass an `ssl.SSLContext` that trusts it:

<!-- docs_src/connecting/https.py -->
```python
import os
import ssl

from gravitywell import PiHole, PiHoleAuth

# The certificate authority the Pi-hole created, copied from /etc/pihole/tls_ca.crt on the Pi-hole.
context = ssl.create_default_context(cafile="tls_ca.crt")

auth = PiHoleAuth(os.environ["PIHOLE_PASSWORD"])
with PiHole("https://pi.hole", auth=auth, verify=context) as api:
    print(api.dns.blocking().blocking)
```

The certificate is valid only for the name in the Pi-hole's `webserver.domain` setting, `pi.hole` by default, so connect by that name. Pi-hole's [TLS documentation](https://docs.pi-hole.net/api/tls/) explains its certificates, and how to use one of your own.

`verify=False` skips the check. Use it only on a network you trust: the connection is still encrypted, but anyone who can intercept it could pose as the Pi-hole and read the password.

## Settings that need `app_sudo`

With an application password, a Pi-hole answers some endpoints with `403 Forbidden`, unless its `webserver.api.app_sudo` setting is on:

| Area | Methods that need it |
|---|---|
| [Settings](settings.md) | Every `api.config` method that changes something: adding and deleting records, reverse servers and static leases, `set_upstreams()` and `update()`. Reading settings works without it. |
| [Sessions](maintenance.md#sessions) | `api.sessions.list()` and `delete()`. |
| [Teleporter backups](maintenance.md#teleporter-backups) | `api.teleporter.export()` and `restore()`. |

Turn it on in the web interface, on the **Settings › All settings** page, or on the Pi-hole itself:

```bash
sudo pihole-FTL --config webserver.api.app_sudo true
```

Each of these methods' descriptions says so, so an AI model that gets a `403` can tell the user what to change.

## The client underneath

`PiHole` is an `httpx2.Client`, and `AsyncPiHole` an `httpx2.AsyncClient`, built with [ClientX](https://github.com/slatecipher/ClientX). They take only the arguments a Pi-hole needs: the URL, `auth=`, `verify=` and `transport=`, which replaces the network in [tests](testing.md).

- Each endpoint returns a model of the whole response body, from `gravitywell.models`, which you can read with your editor's autocomplete. Each response model has `took`, the seconds the Pi-hole spent on the request.
- Times are `datetime`s in UTC.
- A `4xx` or `5xx` answer raises `httpx2.HTTPStatusError`: see [Errors](errors.md).
- Requests use httpx2's default timeouts, except a gravity update's, which waits up to 10 minutes for the Pi-hole to download its lists.
