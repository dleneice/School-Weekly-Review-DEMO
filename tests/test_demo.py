import unittest,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(path):
 with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
class DemoTests(unittest.TestCase):
 def test_outputs(self):
  rows=load(ROOT/'sample_outputs/student_weekly_review.csv')
  self.assertEqual(len(rows),288)
  self.assertEqual(len({(x['week_ending'],x['student_id']) for x in rows}),288)
  self.assertEqual(len({x['week_ending'] for x in rows}),4)
 def test_reporting(self):
  path=ROOT/'reports/student_weekly_review_demo.html'
  self.assertTrue(path.is_file())
  html=path.read_text(encoding='utf-8')
  self.assertIn('Fictional data demonstration',html)
  self.assertIn('data-lens="current-f"',html)
  self.assertIn('S0001',html)
if __name__=='__main__':unittest.main()
