# Pi-hole compatibility

gravitywell works with **Pi-hole v6** and its REST API. Pi-hole v5 and older had a different interface, which gravitywell doesn't support.

## The release it's modeled on

gravitywell's endpoints were modeled on, and tested against, Pi-hole core v6.6, web v6.6.1 and FTL v6.9. `gravitywell.PIHOLE_VERSIONS` records them, by component, as `api.info.version()` names them:

<!-- docs_src/compatibility/versions.py -->
```python
import os

from gravitywell import PIHOLE_VERSIONS, PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    ftl = api.info.version().version.ftl.local.version
    tested = PIHOLE_VERSIONS["ftl"]  # v6.9
    if ftl != tested:
        print(f"This Pi-hole runs FTL {ftl}; gravitywell was tested against FTL {tested}.")
```

FTL serves the API, so its version matters most. Other Pi-hole v6 releases work too, as long as the fields gravitywell reads stay the same:

- Each model reads only the fields gravitywell uses, and ignores the rest, so fields a newer release adds change nothing.
- A field a release removes or changes raises a `pydantic.ValidationError` from the endpoint that returns it. Please [open an issue](https://github.com/slatecipher/gravitywell/issues) with the Pi-hole's versions.
- Where Pi-hole's API specification and FTL disagree, gravitywell accepts what FTL sends. For a DNS server that isn't running, for example, FTL reports the blocking status `failure`, while the specification says `failed`: gravitywell accepts both.

Each Pi-hole serves its own API specification, for its release, at `http://pi.hole/api/docs`.

## What it covers

| Pi-hole API | gravitywell |
|---|---|
| `/api/auth` | `PiHoleAuth` logs in and out. `api.sessions` lists and deletes sessions. |
| `/api/action` | `api.action` |
| `/api/clients` | `api.clients` |
| `/api/config` | `api.config`: typed methods for local DNS and CNAME records, upstream servers, reverse servers and static leases, and `settings()` and `update()` for the [topics it covers](settings.md#other-settings). |
| `/api/dhcp` | `api.dhcp` |
| `/api/dns` | `api.dns` |
| `/api/domains` | `api.domains` |
| `/api/groups` | `api.groups` |
| `/api/history` | `api.history` |
| `/api/info` | `api.info` |
| `/api/lists` | `api.lists` |
| `/api/logs` | `api.logs` |
| `/api/network` | `api.network` |
| `/api/padd` | `api.padd` |
| `/api/queries` | `api.queries` |
| `/api/search` | `api.search` |
| `/api/stats` | `api.stats` |
| `/api/teleporter` | `api.teleporter`, for Python code only. |

## What it leaves out

| Endpoint | Why |
|---|---|
| `GET /api/auth` | It returns the session ID and CSRF token, which a tool would hand to a model. `PiHoleAuth` manages the session itself. |
| `GET /api/info/client` | It echoes the request's headers, the session among them. |
| `GET /api/info/login` | `api.dns.blocking()` already gives the DNS server's state. |
| `/api/auth/app`, `/api/auth/totp` | They create an application password and a two-factor secret: credentials, which belong in the web interface. |
| `/api/config` beyond the topics `api.config` covers | Settings such as the web server's, its passwords and `app_sudo` could lock you out of the Pi-hole. |
| `/api/endpoints`, `/api/docs` | They describe the API itself. |
| `POST /api/action/flush/arp` | An older name for `POST /api/action/flush/network`. |

Two-factor authentication isn't supported: with it on, log in with an [application password](connecting.md#passwords).
