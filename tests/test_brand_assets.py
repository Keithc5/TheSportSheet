import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
ASSETS=ROOT/"assets"/"sports"

class BrandingAssetsTests(unittest.TestCase):
 def test_official_brand_files_are_committed(self):
  names=["gaa-official.jpg","irfu-official.svg","rugby-world-cup.svg","snooker-federation.svg","pdc-official.png","darts-world-series.svg","racing-jockey-club.png","pga-tour-official.svg","lpga-tour-official.svg","nfl.svg","f1.svg","football.svg"]
  for name in names:
   with self.subTest(name=name):
    file=ASSETS/name
    self.assertTrue(file.is_file(),f"Missing committed brand asset: {name}")
    self.assertGreater(file.stat().st_size,100)
 def test_brand_fallback_files_are_committed(self):
  for name in ["rugby","gaa","hurling","snooker","darts","golf","racing","football"]:
   file=ASSETS/(name+"-generic.svg")
   with self.subTest(name=name):self.assertTrue(file.is_file(),f"Missing fallback: {file}")
 def test_site_uses_local_assets_and_handles_missing_logos(self):
  html=(ROOT/"index.html").read_text()
  self.assertIn("assets/sports/",html)
  self.assertIn("this.src=this.dataset.fallback",html)
  self.assertIn("gaa-official",html)
  self.assertIn("pdc-official",html)
  self.assertIn("snooker-federation",html)

if __name__=="__main__":unittest.main()
