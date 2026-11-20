import datetime as dt
import unittest
from unittest.mock import patch
import fetch

class FixtureCoverageTests(unittest.TestCase):
 def test_curated_inventory_and_broadcasts(self):
  days=[dt.date(2026,11,21)]
  rows,issues=fetch.curated_fixtures(days)
  self.assertFalse(issues)
  self.assertGreaterEqual(len(rows),14)
  self.assertTrue(any(x["name"]=="Ireland vs South Africa" and x["channel"]=="Virgin Media One" for x in rows))
  inventory=fetch.validate_inventory(rows,rows,days)
  self.assertEqual(inventory["missing_curated"],[])
  self.assertEqual(inventory["missing_curated_channels"],[])
  self.assertGreaterEqual(inventory["rugby_by_day"]["2026-11-21"]["with_tv"],7)

 def test_missing_channel_is_detected(self):
  fixture={"id":"test","sport":"Rugby","category":"rugby","name":"A vs B","start":"2026-11-21T14:00:00+00:00","start_time":"2026-11-21T14:00:00+00:00","channel":"Channel"}
  incomplete=dict(fixture,channel="")
  report=fetch.validate_inventory([incomplete],[fixture],[dt.date(2026,11,21)])
  self.assertEqual(report["missing_curated_channels"],["test"])

 def test_rejects_duplicate_ids(self):
  e={"id":"x","name":"A vs B","category":"rugby","start_time":"2026-11-21T14:00:00+00:00"}
  with self.assertRaises(ValueError): fetch.validate_output([e,e])

 def test_rugby_category_is_in_collector(self):
  self.assertIn("rugby-nations",fetch.LEAGUES)
  self.assertIn("rugby-premiership",fetch.LEAGUES)

if __name__=="__main__":
 unittest.main()
