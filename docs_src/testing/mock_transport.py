import httpx2
from gravitywell import PiHole, PiHoleAuth


def is_blocking(api: PiHole) -> bool:
    """The code under test."""
    return api.dns.blocking().blocking == "enabled"


def test_is_blocking() -> None:
    sent: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        # PiHoleAuth logs in here before the first request, and logs out when the client closes.
        if request.url.path == "/api/auth":
            return httpx2.Response(200, json={"session": {"sid": "test-session"}, "took": 0.001})
        sent.append(request)
        return httpx2.Response(200, json={"blocking": "enabled", "timer": None, "took": 0.001})

    transport = httpx2.MockTransport(handler)
    with PiHole("http://pi.hole", auth=PiHoleAuth("test"), transport=transport) as api:
        assert is_blocking(api)

    [request] = sent
    assert request.method == "GET"
    assert request.url.path == "/api/dns/blocking"
    assert request.headers["X-FTL-SID"] == "test-session"
