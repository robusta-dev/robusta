from unittest.mock import Mock

import pytest
from freezegun import freeze_time

from robusta.core.reporting import Finding
from robusta.core.sinks.sink_base import SinkBase
from robusta.core.sinks.sink_base_params import ActivityParams
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


class _TestSinkBase(SinkBase):
    def write_finding(self, finding: Finding, platform_enabled: bool):
        pass

    def create_summary_header(self):
        pass

    def _build_time_slices_from_params(self, params: ActivityParams):
        # We'll construct time_slices explicitly below in TestSinkBase.test_accepts
        pass


class TestSinkBase:
    @pytest.mark.parametrize(
        "days,time_intervals,expected_result",
        [
            (["mon", "tue"], [("10:10", "11:05"), ("13:05", "13:50")], False),
            (["Sun", "Wed"], [("13:30", "14:00"), ("19:01", "21:30")], True),
        ]
    )
    def test_accepts(self, days, time_intervals, expected_result):
        mock_registry = Mock(get_global_config=lambda: Mock())
        sink = _TestSinkBase(registry=mock_registry, sink_params=Mock())
        sink.time_slices = [TimeSlice(days, time_intervals, "UTC")]
        mock_finding = Mock(matches=Mock(return_value=True))
        with freeze_time("2012-01-01 13:45"):  # this is UTC time
            assert sink.accepts(mock_finding) is expected_result
