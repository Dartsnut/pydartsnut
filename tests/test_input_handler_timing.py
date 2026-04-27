import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pydartsnut._input_handler import InputHandler


def _empty_darts():
    return [[-1, -1] for _ in range(12)]


def _darts_with(index, coord):
    darts = _empty_darts()
    darts[index] = [coord[0], coord[1]]
    return darts


class MockEngine:
    def __init__(self):
        self.current_darts = _empty_darts()

    def get_darts(self):
        return [list(d) for d in self.current_darts]

    def get_buttons(self):
        return {}


class TestInputHandlerTiming(unittest.TestCase):
    def test_get_dart_hits_respects_min_active_duration(self):
        engine = MockEngine()
        handler = InputHandler(engine, min_active_duration=0.11, idle_unblock_duration=0.5)
        coord = (42, 84)

        # Prime internal state.
        engine.current_darts = _empty_darts()
        with patch("pydartsnut._input_handler.time.time", return_value=0.00):
            self.assertEqual(handler.get_dart_hits(), [])

        # Coordinate becomes valid but has not stayed active long enough yet.
        engine.current_darts = _darts_with(0, coord)
        with patch("pydartsnut._input_handler.time.time", return_value=0.00):
            self.assertEqual(handler.get_dart_hits(), [])
        with patch("pydartsnut._input_handler.time.time", return_value=0.10):
            self.assertEqual(handler.get_dart_hits(), [])

        # At threshold, event should fire.
        with patch("pydartsnut._input_handler.time.time", return_value=0.11):
            self.assertEqual(handler.get_dart_hits(), [(0, coord[0], coord[1])])

    def test_blocked_dart_unblocks_after_idle_duration(self):
        engine = MockEngine()
        handler = InputHandler(engine, min_active_duration=0.11, idle_unblock_duration=0.5)
        coord = (10, 20)

        # Prime internal state.
        engine.current_darts = _empty_darts()
        with patch("pydartsnut._input_handler.time.time", return_value=0.00):
            self.assertEqual(handler.get_dart_hits(), [])

        # Trigger first hit and block dart index 0.
        engine.current_darts = _darts_with(0, coord)
        with patch("pydartsnut._input_handler.time.time", return_value=0.00):
            self.assertEqual(handler.get_dart_hits(), [])
        with patch("pydartsnut._input_handler.time.time", return_value=0.11):
            self.assertEqual(handler.get_dart_hits(), [(0, coord[0], coord[1])])

        # Still blocked while active.
        with patch("pydartsnut._input_handler.time.time", return_value=0.20):
            self.assertEqual(handler.get_dart_hits(), [])

        # Start invalid period for unblock timer.
        engine.current_darts = _empty_darts()
        with patch("pydartsnut._input_handler.time.time", return_value=0.30):
            self.assertEqual(handler.get_dart_hits(), [])
        with patch("pydartsnut._input_handler.time.time", return_value=0.79):
            self.assertEqual(handler.get_dart_hits(), [])

        # 0.5s of continuous invalid has elapsed (0.30 -> 0.80), so unblocked.
        with patch("pydartsnut._input_handler.time.time", return_value=0.80):
            self.assertEqual(handler.get_dart_hits(), [])

        # Dart can fire again once active for MIN_ACTIVE_DURATION after reappearing.
        engine.current_darts = _darts_with(0, coord)
        with patch("pydartsnut._input_handler.time.time", return_value=0.81):
            self.assertEqual(handler.get_dart_hits(), [])
        with patch("pydartsnut._input_handler.time.time", return_value=0.93):
            self.assertEqual(handler.get_dart_hits(), [(0, coord[0], coord[1])])

    def test_coordinate_change_while_blocked_does_not_emit_new_hit(self):
        engine = MockEngine()
        handler = InputHandler(engine, min_active_duration=0.11, idle_unblock_duration=0.5)
        first_coord = (30, 40)
        second_coord = (31, 41)

        # Prime internal state.
        engine.current_darts = _empty_darts()
        with patch("pydartsnut._input_handler.time.time", return_value=0.00):
            self.assertEqual(handler.get_dart_hits(), [])

        # First coordinate stabilizes and emits hit, which blocks dart index 0.
        engine.current_darts = _darts_with(0, first_coord)
        with patch("pydartsnut._input_handler.time.time", return_value=0.00):
            self.assertEqual(handler.get_dart_hits(), [])
        with patch("pydartsnut._input_handler.time.time", return_value=0.11):
            self.assertEqual(handler.get_dart_hits(), [(0, first_coord[0], first_coord[1])])

        # During block window, coordinate changes and remains active long enough,
        # but should not emit another hit while index 0 is still blocked.
        engine.current_darts = _darts_with(0, second_coord)
        with patch("pydartsnut._input_handler.time.time", return_value=0.12):
            self.assertEqual(handler.get_dart_hits(), [])
        with patch("pydartsnut._input_handler.time.time", return_value=0.24):
            self.assertEqual(handler.get_dart_hits(), [])

    def test_defaults_are_min_active_zero_and_idle_unblock_point_two(self):
        engine = MockEngine()
        handler = InputHandler(engine)
        coord = (50, 60)

        self.assertEqual(handler.MIN_ACTIVE_DURATION, 0.0)
        self.assertEqual(handler.IDLE_UNBLOCK_DURATION, 0.2)

        # Prime internal state.
        engine.current_darts = _empty_darts()
        with patch("pydartsnut._input_handler.time.time", return_value=0.00):
            self.assertEqual(handler.get_dart_hits(), [])

        # With MIN_ACTIVE_DURATION=0, first valid frame emits immediately.
        engine.current_darts = _darts_with(0, coord)
        with patch("pydartsnut._input_handler.time.time", return_value=0.01):
            self.assertEqual(handler.get_dart_hits(), [(0, coord[0], coord[1])])

    def test_zero_durations_skip_timing_safeguard_state(self):
        engine = MockEngine()
        handler = InputHandler(engine, min_active_duration=0, idle_unblock_duration=0)
        first_coord = (70, 71)
        second_coord = (72, 73)

        # Prime internal state.
        engine.current_darts = _empty_darts()
        with patch("pydartsnut._input_handler.time.time", return_value=0.00):
            self.assertEqual(handler.get_dart_hits(), [])

        # First hit blocks index 0 immediately.
        engine.current_darts = _darts_with(0, first_coord)
        with patch("pydartsnut._input_handler.time.time", return_value=0.01):
            self.assertEqual(handler.get_dart_hits(), [(0, first_coord[0], first_coord[1])])

        # No coordinate timing state should be tracked when min_active_duration is 0.
        self.assertEqual(handler.coord_active_start_times, {})

        # One invalid frame should unblock immediately when idle_unblock_duration is 0.
        engine.current_darts = _empty_darts()
        with patch("pydartsnut._input_handler.time.time", return_value=0.02):
            self.assertEqual(handler.get_dart_hits(), [])
        self.assertEqual(handler.dart_idle_start_times, {})

        # Same index can emit again immediately after reappearing.
        engine.current_darts = _darts_with(0, second_coord)
        with patch("pydartsnut._input_handler.time.time", return_value=0.03):
            self.assertEqual(handler.get_dart_hits(), [(0, second_coord[0], second_coord[1])])


if __name__ == "__main__":
    unittest.main()
