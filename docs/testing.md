# Testing

Test code that uses gravitywell without a Pi-hole: give the client an `httpx2.MockTransport`, whose handler answers each request in the Pi-hole's place. Nothing reaches the network, and the test can check each request the client sent.

<!-- docs_src/testing/mock_transport.py -->
```python
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
```

- **Answer the login.** `PiHoleAuth` logs in at `/api/auth` before the first request, and logs out there when the client closes. Answer both with a session, such as `{"session": {"sid": "test-session"}, "took": 0.001}`, and the client sends that session in the `X-FTL-SID` header of every other request.
- **Answer with the Pi-hole's body.** Each endpoint decodes its answer into a model from `gravitywell.models`, which reads only the fields it uses: a test body needs those, and can leave out the rest. The model's fields, in your editor or the [API reference](reference.md), say which they are. Every response model has `took`.
- **Check what was sent:** `request.method`, `request.url.path`, `request.url.params`, and the JSON body, with `json.loads(request.content)`.
- **Test failures** by answering with an error status, such as `httpx2.Response(403, json={"error": {"key": "forbidden", "message": "...", "hint": None}, "took": 0.001})`, which raises `httpx2.HTTPStatusError` from the call. Answering the login with `401` makes it raise from the first call.
- **Async code:** `AsyncPiHole` takes a `MockTransport` too, with the same handler.

ClientX's [testing guide](https://github.com/slatecipher/ClientX/blob/mainline/docs/testing.md) has more on mock transports.
