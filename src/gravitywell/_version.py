from collections.abc import Mapping
from importlib.metadata import version
from types import MappingProxyType
from typing import Final, Literal

__version__ = version("gravitywell")

PIHOLE_VERSIONS: Final[Mapping[Literal["core", "web", "ftl"], str]] = MappingProxyType(
    {"core": "v6.6", "web": "v6.6.1", "ftl": "v6.9"}
)
"""The Pi-hole release gravitywell was modeled on and tested against.

The versions of its components, as `api.info.version()` reports them. FTL
serves the REST API, so its version matters most. gravitywell works with other
Pi-hole v6 releases too, as long as the fields it reads stay the same.
"""

__all__ = ["PIHOLE_VERSIONS", "__version__"]
