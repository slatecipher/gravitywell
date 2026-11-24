import pytest

import gravitywell
from gravitywell import AsyncPiHole, PiHole, PiHoleAuth

BASE_URL = "http://pi.hole"
PASSWORD = "app-password"


def test_user_agent_starts_with_gravitywell_and_its_version() -> None:
    product = f"gravitywell/{gravitywell.__version__} "
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD)) as api:
        assert api.headers["User-Agent"].startswith(product)
    # Creating an async client opens nothing, so there's nothing to close.
    assert AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD)).headers["User-Agent"].startswith(product)


@pytest.mark.parametrize(
    "base_url", ["http://pi.hole", "http://pi.hole/", "http://pi.hole/api", "http://pi.hole/admin"]
)
def test_requests_go_under_api_whatever_path_the_base_url_has(base_url: str) -> None:
    with PiHole(base_url, auth=PiHoleAuth(PASSWORD)) as api:
        assert str(api.build_request("GET", "/info/version").url) == "http://pi.hole/api/info/version"
