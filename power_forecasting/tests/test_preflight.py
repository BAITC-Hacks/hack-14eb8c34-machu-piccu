"""Tests for the implemented input/coverage gate, not full pipeline leakage tests."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from src.weather_cache import WeatherCache
from src.weather_client import summarize_response
from src.input_data import ROOT, inspect_file


class CoverageTests(unittest.TestCase):
    def response(self, hourly, status=200):
        return {"body": json.dumps({"hourly": hourly}), "status": status, "cache_key": "test", "url": "test"}

    def test_http_200_with_nulls_is_not_coverage(self):
        result = summarize_response(self.response({"time": ["2025-01-01T00:00"], "wind_speed_100m_previous_day1": [None]}), "2025-01-01", "previous_runs")
        self.assertFalse(result["has_nonnull_values"])
        self.assertEqual(result["earliest_nonnull_in_probe"], "")

    def test_zero_is_valid_weather_value(self):
        result = summarize_response(self.response({"time": ["2025-01-01T00:00"], "wind_speed_100m_previous_day1": [0.0]}), "2025-01-01", "previous_runs")
        self.assertTrue(result["has_nonnull_values"])

    def test_previous_day_offsets_are_not_issue_time_provenance(self):
        result = summarize_response(self.response({"time": ["2025-01-01T00:00"], "wind_speed_100m_previous_day2": [5]}), "2025-01-01", "previous_runs")
        self.assertEqual(result["nominal_offset_hours"], "48")
        self.assertEqual(result["run_lead_hours"], "")
        self.assertFalse(result["source_run_proven"])
        self.assertFalse(result["publication_time_proven"])
        self.assertFalse(result["exact_point_in_time_proven"])
        self.assertTrue(result["fixed_lead_method_accepted"])

    def test_run_time_alone_does_not_prove_publication(self):
        result = summarize_response(self.response({"time": ["2025-01-01T00:00", "2025-01-03T00:00"], "temperature_2m": [1, 2]}), "2025-01-01", "single_runs")
        self.assertEqual(result["run_lead_hours"], "0;48")
        self.assertFalse(result["exact_point_in_time_proven"])
        self.assertFalse(result["fixed_lead_method_accepted"])

    def test_invalid_response_does_not_become_coverage(self):
        entry = {"body": "Bad gateway", "status": 502, "url": "test", "cache_key": "test"}
        self.assertFalse(summarize_response(entry, "2025-01-01", "single_runs")["has_nonnull_values"])


class CacheTests(unittest.TestCase):
    settings = {"interval_seconds": 0, "max_attempts": 2, "timeout_seconds": 1, "max_retry_wait_seconds": 0}

    def test_cache_replays_without_network(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            cache = WeatherCache(directory, self.settings)
            with patch("src.weather_cache.urlopen") as network:
                response = network.return_value.__enter__.return_value
                response.status = 200
                response.read.return_value = b'{"test":1}'
                response.headers = {}
                first = cache.get("gfs", "https://example.com/forecast", {"b": 2, "a": 1})
            with patch("src.weather_cache.urlopen", side_effect=AssertionError("Unexpected network")):
                second = cache.get("gfs", "https://example.com/forecast", {"a": 1, "b": 2})
                self.assertEqual(first, second)
                offline = WeatherCache(directory, self.settings, offline=True)
                self.assertEqual(first, offline.get("gfs", "https://example.com/forecast", {"b": 2, "a": 1}))

    def test_coordinates_are_part_of_cache_key(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            cache = WeatherCache(directory, self.settings)
            with patch("src.weather_cache.urlopen") as network:
                response = network.return_value.__enter__.return_value
                response.status = 200
                response.read.return_value = b'{}'
                response.headers = {}
                first = cache.get("gfs", "https://example.com/forecast", {"latitude": 43.64515})
                second = cache.get("gfs", "https://example.com/forecast", {"latitude": 43.643198})
                self.assertNotEqual(first["cache_key"], second["cache_key"])
                self.assertEqual(network.call_count, 2)


class InputTests(unittest.TestCase):
    def test_gaps_duplicates_nulls_and_unknown_timezone_are_retained(self):
        header = "ID,Статистическое время,Средняя скорость ветра(m/s),Нормализованная активная мощность,Средняя температура окружающей среды(°C)\n"
        rows = "1,2025-01-01 00:00:00,2,0.1,3\n2,2025-01-01 00:10:00,3,,4\n3,2025-01-01 00:30:00,4,0.2,5\n4,2025-01-01 00:30:00,4,0.2,5\n"
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "scada.csv"
            path.write_text(header + rows, encoding="utf-8")
            result = inspect_file(path, "turbine_1")
            self.assertEqual(result["missing_timestamps"], 1)
            self.assertEqual(result["duplicate_timestamps"], 1)
            self.assertIsNone(result["timezone"])
            self.assertEqual(result["null_cells"]["Нормализованная активная мощность"], 1)
            self.assertEqual(result["rows"], 4)


if __name__ == "__main__":
    unittest.main()
