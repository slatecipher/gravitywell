from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from gravitywell.models import TimeRange

START = datetime(2026, 11, 24, tzinfo=UTC)


def test_a_time_range_is_sent_as_unix_seconds_from_and_until() -> None:
    time_range = TimeRange(start=START, until=START + timedelta(days=1))

    assert time_range.model_dump(mode="json", by_alias=True) == {"from": 1795478400, "until": 1795564800}


def test_until_defaults_to_now() -> None:
    before = datetime.now(UTC)

    until = TimeRange(start=START).until

    assert before <= until <= datetime.now(UTC)


@pytest.mark.parametrize("start", ["2026-11-24T00:00:00", datetime(2026, 11, 24)])
def test_a_time_without_a_timezone_is_rejected(start: object) -> None:
    with pytest.raises(ValidationError, match="needs a timezone"):
        TimeRange.model_validate({"start": start})


def test_start_must_be_before_until() -> None:
    with pytest.raises(ValidationError, match="`start` must be before `until`"):
        TimeRange(start=START, until=START)
