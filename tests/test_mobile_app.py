import json
import pathlib
import re
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]

class MobileAppTests(unittest.TestCase):
 def test_manifest_and_routes(self):
  manifest=json.loads((ROOT/'app/manifest.webmanifest').read_text())
  self.assertEqual(manifest['start_url'],'/TheSportSheet/app/')
  self.assertEqual(manifest['display'],'standalone')
  self.assertTrue((ROOT/'app/icon.svg').exists())
  self.assertTrue((ROOT/'app/sw.js').exists())
 def test_shared_data_and_settings(self):
  page=(ROOT/'app/index.html').read_text()
  for token in ('../data/events.json','thesportsheet-favourites-v1','thesportsheet-timezone-v1','America/Los_Angeles','Intl.DateTimeFormat','escapeHtml','serviceWorker.register'):
   with self.subTest(token=token):self.assertIn(token,page)
 def test_mobile_navigation_and_accessibility(self):
  page=(ROOT/'app/index.html').read_text()
  for view in ('fixtures','results','favourites','settings'):
   self.assertIn('data-view="'+view+'"',page)
  self.assertIn('aria-label="Choose date"',page)
  self.assertIn('aria-label="Filter by sport"',page)
 def test_cache_only_stores_successful_responses(self):
  sw=(ROOT/'app/sw.js').read_text()
  self.assertIn('if(res.ok)',sw)
  self.assertIn('caches.match(event.request)',sw)

if __name__=='__main__':unittest.main()
