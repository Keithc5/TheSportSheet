import datetime as dt
import unittest
from unittest.mock import patch
import fetch

class F1ScheduleTests(unittest.TestCase):
    def test_official_las_vegas_race_is_sunday_in_ireland(self):
        days=[dt.date(2026,11,20)+dt.timedelta(days=i) for i in range(3)]
        events,issues=fetch.official_f1_sessions(days)
        self.assertFalse(issues)
        race=[e for e in events if e["session"]=="Race" and "Las Vegas" in e["name"]]
        self.assertEqual(len(race),1)
        self.assertEqual(race[0]["start_time"],"2026-11-22T04:00:00+00:00")
        self.assertEqual(race[0]["verification"],"official-schedule")
        self.assertEqual(len([e for e in events if "Las Vegas" in e["name"]]),2)
        self.assertTrue(all(e["session"] in fetch.F1_DISPLAY_SESSIONS for e in events))

    def test_practice_sessions_are_excluded(self):
        self.assertNotIn("Practice 1",fetch.F1_DISPLAY_SESSIONS)
        self.assertIn("Qualifying",fetch.F1_DISPLAY_SESSIONS)
        self.assertIn("Sprint Qualifying",fetch.F1_DISPLAY_SESSIONS)
        self.assertIn("Sprint",fetch.F1_DISPLAY_SESSIONS)
        self.assertIn("Race",fetch.F1_DISPLAY_SESSIONS)

    def test_espn_meeting_date_is_not_a_race_start(self):
        payload={"events":[{"id":"123","date":"2026-11-20T00:30:00Z","name":"Las Vegas Grand Prix","competitions":[]}]}
        class Response:
            def __enter__(self):return self
            def __exit__(self,*args):pass
        with patch("fetch.urllib.request.urlopen",return_value=Response()),patch("fetch.json.load",return_value=payload):
            events,health=fetch.fetch_one(("racing-f1",dt.date(2026,11,20)))
        self.assertEqual(events,[])
        self.assertEqual(health["status"],"ok")

    def test_reject_naive_or_wrong_day(self):
        self.assertFalse(fetch.valid_start("2026-11-20T00:30:00",dt.date(2026,11,20)))
        self.assertFalse(fetch.valid_start("2026-11-20T00:30:00Z",dt.date(2026,11,21)))
        self.assertTrue(fetch.valid_start("2026-11-22T04:00:00Z",dt.date(2026,11,22)))

if __name__=="__main__":unittest.main()
