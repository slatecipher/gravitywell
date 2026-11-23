import gravitywell
from gravitywell import AsyncPiHole, PiHole

BASE_URL = "http://pi.hole/api"


def test_user_agent_starts_with_gravitywell_and_its_version() -> None:
    product = f"gravitywell/{gravitywell.__version__} "
    with PiHole(BASE_URL) as api:
        assert api.headers["User-Agent"].startswith(product)
    # Creating an async client opens nothing, so there's nothing to close.
    assert AsyncPiHole(BASE_URL).headers["User-Agent"].startswith(product)
