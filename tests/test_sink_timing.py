from unittest.mock import Mock

import pytest
from freezegun import freeze_time

from robusta.core.reporting import Finding
from robusta.core.sinks.sink_base import SinkBase
from robusta.core.sinks.sink_base_params import ActivityParams
from robusta.core.sinks.timing import MuteDateInterval, TimeSlice


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


class TestMuteDateInterval:
    def test_unknown_timezone(self):
        with pytest.raises(ValueError):
            MuteDateInterval("2012-01-01 00:00", "2012-01-02 00:00", "Mars/Cydonia")

    @pytest.mark.parametrize(
        "start_date,end_date,timezone,expected_muted",
        [
            # 2012-01-01 13:45 UTC - currently muted (within range)
            ("2012-01-01 00:00", "2012-01-01 23:59", "UTC", True),
            # Currently muted (multi-day range spanning year boundary)
            ("2011-12-31 00:00", "2012-01-02 10:00", "UTC", True),
            # Not muted (range in February)
            ("2012-02-01 00:00", "2012-02-28 23:59", "UTC", False),
            # Not muted (same day but end is before current time)
            ("2012-01-01 00:00", "2012-01-01 13:00", "UTC", False),
            # Muted (same day, hours match)
            ("2012-01-01 13:00", "2012-01-01 14:00", "UTC", True),
            # Not muted (range is entirely in the past)
            ("2011-06-01 00:00", "2011-06-30 23:59", "UTC", False),
            # Not muted (range is entirely in the future)
            ("2013-01-01 00:00", "2013-12-31 23:59", "UTC", False),
            # Timezone test: 2012-01-01 13:45 UTC = 2012-01-01 14:45 CET
            ("2012-01-01 14:00", "2012-01-01 15:00", "CET", True),
            ("2012-01-01 15:00", "2012-01-01 16:00", "CET", False),
        ],
    )
    def test_is_muted_now(self, start_date, end_date, timezone, expected_muted):
        with freeze_time("2012-01-01 13:45"):  # UTC time
            assert MuteDateInterval(start_date, end_date, timezone).is_muted_now() is expected_muted


class _TestSinkBase(SinkBase):
    def write_finding(self, finding: Finding, platform_enabled: bool):
        pass

    def create_summary_header(self):
        pass

    def _build_time_slices_from_params(self, params: ActivityParams):
        # We'll construct time_slices explicitly below in TestSinkBase.test_accepts
        pass

    def _build_mute_intervals_from_params(self, params):
        # We'll construct mute_date_intervals explicitly below
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
        sink.mute_date_intervals = []
        mock_finding = Mock(matches=Mock(return_value=True))
        with freeze_time("2012-01-01 13:45"):  # this is UTC time
            assert sink.accepts(mock_finding) is expected_result

    def test_accepts_muted(self):
        """When a mute interval is active, accepts() should return False."""
        mock_registry = Mock(get_global_config=lambda: Mock())
        sink = _TestSinkBase(registry=mock_registry, sink_params=Mock())
        sink.time_slices = [TimeSlice(["sun"], [("13:30", "14:00")], "UTC")]
        sink.mute_date_intervals = [MuteDateInterval("2012-01-01 00:00", "2012-01-01 23:59", "UTC")]
        mock_finding = Mock(matches=Mock(return_value=True))
        with freeze_time("2012-01-01 13:45"):  # this is UTC time, Sunday
            # Would normally be accepted (Sunday 13:45 in 13:30-14:00), but muted
            assert sink.accepts(mock_finding) is False

    def test_accepts_not_muted(self):
        """When no mute interval is active, accepts() works normally."""
        mock_registry = Mock(get_global_config=lambda: Mock())
        sink = _TestSinkBase(registry=mock_registry, sink_params=Mock())
        sink.time_slices = [TimeSlice(["sun"], [("13:30", "14:00")], "UTC")]
        sink.mute_date_intervals = [MuteDateInterval("2012-02-01 00:00", "2012-02-28 23:59", "UTC")]
        mock_finding = Mock(matches=Mock(return_value=True))
        with freeze_time("2012-01-01 13:45"):  # this is UTC time, Sunday
            # Mute is for February, so should still accept
            assert sink.accepts(mock_finding) is True
