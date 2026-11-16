import datetime as dt
import unittest
from unittest.mock import patch
import fetch

class ResultsCollectionTests(unittest.TestCase):
 def test_recent_history(self):
  days=fetch.collection_days()
  today=dt.datetime.now(fetch.TZ).date()
  self.assertIn(today-dt.timedelta(days=1),days)

 def test_final_score_only_when_completed(self):
  class Response:
   def __enter__(self):return self
   def __exit__(self,*args):pass
  for completed,expected in ((True,"2 – 1"),(False,None)):
   payload={"events":[{"id":"42","date":"2026-11-15T14:00:00Z","name":"A vs B","status":{"type":{"completed":completed}},"competitions":[{"competitors":[{"team":{"displayName":"A"},"score":"2"},{"team":{"displayName":"B"},"score":"1"}]}]}]}
   with patch("fetch.urllib.request.urlopen",return_value=Response()),patch("fetch.json.load",return_value=payload):
    events,_=fetch.fetch_one(("soccer-eng.1",dt.date(2026,11,15)))
   self.assertEqual(events[0]["result"],expected)

if __name__=="__main__":unittest.main()
