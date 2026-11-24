import pytest


@pytest.fixture
def anyio_backend() -> str:
    # Run async tests on asyncio only. anyio 4.10, the lowest version
    # `pyproject.toml` allows, runs them on trio too by default, even though
    # trio isn't installed.
    return "asyncio"
