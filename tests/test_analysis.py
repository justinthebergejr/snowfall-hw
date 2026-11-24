import calendar
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("analysis", Path(__file__).parents[1] / "scripts/analyze.py")
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


class AnalysisTests(unittest.TestCase):
    def test_daily_parser_units_flags_and_invalid_calendar_days(self):
        values = [(254, " ", " "), (0, "T", " "), (-9999, " ", " "),
                  (500, " ", "X"), (-1, " ", " ")]
        values += [(0, " ", " ")] * (31 - len(values))
        record = "USC00000001" + "200002SNOW" + "".join(
            f"{value:5d}{flag}{quality}0" for value, flag, quality in values)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.dly"
            path.write_text(record + "\n")
            months = a.parse_snow(path)
        self.assertEqual(len(months[2000, 2]), 26)  # leap day included; 3 invalid
        self.assertEqual(sum(months[2000, 2]) / 25.4, 10)

    def test_monthly_coverage_and_no_missing_month_imputation(self):
        months = {(2000, m): [0]*calendar.monthrange(2000, m)[1] for m in range(1, 13)}
        months[2000, 1][0] = 254
        months[2000, 1].pop()
        self.assertEqual(a.annuals(months, .95)[2000], 10)
        self.assertNotIn(2000, a.annuals(months, 1))
        del months[2000, 7]
        self.assertNotIn(2000, a.annuals(months, .95))

    def test_state_weights_not_station_counts(self):
        panel = [dict(state=s, old=100, new=110) for s in a.STATES]
        panel += [dict(state="CT", old=100, new=110)] * 10
        value, _ = a.regional(panel)
        self.assertAlmostEqual(value, 10)
        panel[0]["new"] = 100
        panel = panel[:6]
        value, _ = a.regional(panel)
        self.assertAlmostEqual(value, 50 / 6)

    def test_incomplete_state_panel_not_reported(self):
        self.assertEqual(a.regional([dict(state="CT", old=100, new=90)]), (None, {}))

    def test_station_year_count_cutoffs(self):
        station = dict(id="test", state="CT")
        years = list(range(1960, 2000)) + list(range(2000, 2014))
        months = {(year, month): [1] * calendar.monthrange(year, month)[1]
                  for year in years for month in range(1, 13)}
        self.assertEqual(len(a.panel([(station, months)], .95)), 1)
        del months[1960, 1]
        self.assertEqual(a.panel([(station, months)], .95), [])

    def test_bootstrap_constant_panel(self):
        years = {year: (100 if year < 2000 else 110) for year in range(1940, 2020)}
        panel = [dict(state=s, old=100, new=110, years=years) for s in a.STATES]
        for block in (1, 5):
            interval = a.bootstrap(panel, repetitions=20, block=block)
            for bound in interval:
                self.assertAlmostEqual(bound, 10)


if __name__ == "__main__":
    unittest.main()
