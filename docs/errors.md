# Errors

gravitywell raises the errors of the libraries it's built on: httpx2 for requests, ClientX for arguments it refuses, and Pydantic for data that doesn't fit a model.

| Error | When |
|---|---|
| `httpx2.HTTPStatusError` | The Pi-hole answered with a `4xx` or `5xx` status, including a failed login. `error.response` holds its answer. |
| `httpx2.RequestError` | The Pi-hole couldn't be reached: a connection refused, a name that doesn't resolve, a certificate that isn't trusted (`httpx2.ConnectError`), or a timeout (`httpx2.TimeoutException`). |
| `clientx.ArgumentError` | gravitywell refused a call before changing anything. It's a `ValueError`, and its message says why. |
| `pydantic.ValidationError` | An argument model is invalid, such as a `TimeRange` without a timezone, or the Pi-hole's answer doesn't fit its model, which can happen with a Pi-hole release that changed it. |
| `clientx.tools.ToolError` | From an AI tool's `call()` only: what went wrong, for the model. See [AI tools](ai-tools.md#calling-tools). |

## The Pi-hole's errors

The Pi-hole explains each error in its answer's body, as `{"error": {"key": ..., "message": ..., "hint": ...}}`:

<!-- docs_src/errors/handling.py -->
```python
import os

import httpx2
from clientx import ArgumentError
from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    try:
        api.config.add_dns_record("192.168.1.10", "nas.lan")
    except httpx2.HTTPStatusError as error:
        if error.response.status_code == 403:
            print("Turn on webserver.api.app_sudo to change settings with an application password.")
        else:
            # Pi-hole's reason, such as a record that exists already.
            print(error.response.json()["error"]["message"])
    except httpx2.RequestError as error:
        print(f"Couldn't reach the Pi-hole: {error}")

    try:
        api.groups.delete("Default")
    except ArgumentError as error:
        print(error)  # gravitywell refused, and deleted nothing
```

| Status | Usually means |
|---|---|
| `400 Bad Request` | An invalid value, such as a malformed IP address or regex, or an entry that exists already. The message names it. |
| `401 Unauthorized` | A wrong password, from the login. After a login, the client handles a `401` itself: it logs in again once and repeats the request. |
| `403 Forbidden` | With an application password, an endpoint that needs the Pi-hole's `app_sudo` setting: see [Settings that need `app_sudo`](connecting.md#settings-that-need-app_sudo). |
| `404 Not Found` | No such item, such as a group that doesn't exist. |
| `429 Too Many Requests` | From the login: every one of the Pi-hole's sessions is in use. Log out the ones apps left open, with [`api.sessions`](maintenance.md#sessions) or the web interface, or wait for them to expire. |

## Arguments gravitywell refuses

Some calls would do harm Pi-hole doesn't guard against, or need checking that Pi-hole skips silently. gravitywell checks them first, and raises `clientx.ArgumentError`, naming the argument in `error.parameter`:

- Deleting the Default group, whatever its name.
- A setting outside the [topics `api.config` covers](settings.md#other-settings), one it refuses to change, or a key Pi-hole doesn't have, which it would skip without a word.
- Deleting a local DNS record, CNAME record, reverse server or static lease that doesn't exist, or a record that names other hostnames too.
- A name or address with spaces, commas or `#` in a local DNS or CNAME record, which would change the entry Pi-hole stores.
- An empty list of upstream servers, which would leave the Pi-hole resolving only its local records.
- An `explain_client()` address that isn't an IP address.
