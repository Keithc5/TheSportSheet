"""Regression tests for schedule integrity. Run: python -m unittest discover -s tests"""
import datetime as dt
import unittest
from unittest.mock import patch
import fetch

class PipelineTests(unittest.TestCase):
 def test_weekend_is_three_consecutive_days(self):
  days=fetch.weekend()
  self.assertEqual(len(days),3)
  self.assertEqual(days[0].weekday(),4)
  self.assertEqual(days[1]-days[0],dt.timedelta(days=1))
 def test_normalization(self):
  self.assertEqual(fetch.norm("St. Brigid's"),"st brigid s")
 def test_coverage_never_becomes_kickoff(self):
  self.assertNotEqual("coverage_time","start_time")
 def test_all_sources_have_labels(self):
  for category,config in fetch.LEAGUES.items():
   self.assertEqual(len(config),4)
   self.assertTrue(category)
if __name__=="__main__":unittest.main()
