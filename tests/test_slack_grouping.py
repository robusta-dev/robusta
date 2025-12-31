import pytest

from datetime import datetime, timezone

from robusta.core.sinks.sink_base import NotificationSummary


utc = timezone.utc


class TestNotificationSummary:
    @pytest.mark.parametrize("input_dt,expected_output", [
        (datetime(2024, 6, 25, 12, 15, 33, tzinfo=utc), (1719273600, 1719360000)),
        (datetime(2024, 6, 30, 17, 22, 19, tzinfo=utc), (1719705600, 1719792000)),
        (datetime(2024, 12, 3, 10, 59, 59, tzinfo=utc), (1733184000, 1733270400)),
        (datetime(2024, 12, 31, 16, 42, 28, tzinfo=utc), (1735603200, 1735689600)),
    ])
    def test_get_day_boundaries(self, input_dt, expected_output):
        assert NotificationSummary.get_day_boundaries(input_dt) == expected_output
