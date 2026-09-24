import tempfile, unittest
from pathlib import Path
import app
class Tests(unittest.TestCase):
 def test_alert_and_storage(self):
  with tempfile.TemporaryDirectory() as folder:
   app.DB=Path(folder)/'test.db'
   result=app.add({'facility':'Block A','occupancy':90,'air_quality':85,'water_level':5,'water_liters':8,'hours_since_clean':30})
   self.assertEqual(result['risk'],97)
   self.assertEqual(result['anomaly'],1)
   self.assertIn('Low water level',result['alert'])
   self.assertEqual(len(app.rows()),1)
 def test_invalid_input(self):
  with self.assertRaises(ValueError): app.add({'facility':'A','occupancy':-1,'air_quality':30,'water_level':50,'water_liters':2,'hours_since_clean':1})
if __name__=='__main__': unittest.main()
