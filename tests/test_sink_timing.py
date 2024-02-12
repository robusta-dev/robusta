import pytest
from freezegun import freeze_time

from robusta.core.sinks.timing import TimeSlice


class TestTimeSlice:
    def test_unknown_timezone(self):
        with pytest.raises(ValueError):
            TimeSlice(["mon"], [], "Mars/Cydonia")

    @pytest.mark.parametrize(
        "days,time_intervals,timezone,expected_result",
        [
            (["MON", "fri"], [("13:30", "14:30"), ("17:30", "18:30")], "UTC", False),
            (["mon", "sun"], [("13:50", "14:30"), ("17:30", "18:30")], "UTC", False),
            (["SUN", "FRI"], [("13:45", "14:30"), ("11:30", "11:31")], "UTC", True),
            (["THR", "WED", "sun"], [("15:51", "16:41"), ("13:0", "14:44"), ("23:01", "23:03")], "CET", False),
            (["THR", "WED", "SUN"], [("15:51", "16:41"), ("13:0", "14:45"), ("23:01", "23:03")], "CET", True),
            (["mon", "SUN"], [], "America/New_York", True),
        ],
    )
    def test_is_active_now(self, days, time_intervals, timezone, expected_result):
        with freeze_time("2012-01-01 13:45"):  # this is UTC time
            assert TimeSlice(days, time_intervals, timezone).is_active_now() is expected_result

    def test_invalid_days(self):
        with pytest.raises(ValueError):
            TimeSlice(["MON", "sat", "monday", "TUE", "fri"], [], "UTC")

    @pytest.mark.parametrize("time", ["00:60", "000:11", "03:-1", "-5:4", "24:13", "x:13", "11:abc", "$:#"])
    def test_invalid_time(self, time):
        with pytest.raises(ValueError):
            TimeSlice([], [time], "UTC")
