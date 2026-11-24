"""Check the publication's links and its numerical evidence, without network access."""
import csv
from html.parser import HTMLParser
import json
from pathlib import Path
import statistics
import unittest
from urllib.parse import urlsplit

DOCS = Path(__file__).resolve().parents[1] / "docs"


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        for attr in ("href", "src"):
            if attr in attrs:
                self.links.append(attrs[attr])


class ReportTests(unittest.TestCase):
    def test_local_links_and_unique_anchors(self):
        page = PageParser()
        page.feed((DOCS / "index.html").read_text(encoding="utf-8"))
        self.assertEqual(len(page.ids), len(set(page.ids)))
        for link in page.links:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue
            if url.path:
                self.assertTrue((DOCS / url.path).is_file(), link)
            elif url.fragment:
                self.assertIn(url.fragment, page.ids)

    def test_csv_reproduces_published_station_means(self):
        result = json.loads((DOCS / "assets/results.json").read_text())
        with (DOCS / "assets/station-years.csv").open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        for station in result["stations"]:
            for field, earlier in (("old", True), ("new", False)):
                values = [float(row["snowfall_inches"]) for row in rows
                          if row["station"] == station["id"]
                          and (int(row["year"]) < 2000) == earlier]
                self.assertAlmostEqual(statistics.mean(values), station[field], places=4)
                self.assertEqual(len(values), station["n_" + field])

    def test_published_state_weighting(self):
        result = json.loads((DOCS / "assets/results.json").read_text())
        self.assertEqual(set(result["states"]), {"CT", "MA", "ME", "NH", "RI", "VT"})
        for state, change in result["states"].items():
            values = [100 * (s["new"] / s["old"] - 1)
                      for s in result["stations"] if s["state"] == state]
            self.assertAlmostEqual(statistics.mean(values), change)
        self.assertAlmostEqual(statistics.mean(result["states"].values()), result["change"])


if __name__ == "__main__":
    unittest.main()
