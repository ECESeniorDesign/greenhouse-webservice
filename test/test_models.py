import unittest
import mock
import os
import sys
from datetime import datetime as dt
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import app.models as models
from app.config import TEST_DATABASE, SCHEMA

class TestPlant(unittest.TestCase):

    def setUp(self):
        models.lazy_record.connect_db(TEST_DATABASE)
        with open(SCHEMA) as schema:
            models.lazy_record.load_schema(schema.read())

    def tearDown(self):
        models.lazy_record.close_db()

    @mock.patch("app.models.datetime.datetime")
    def test_mature_in_when_not_mature_gives_number_of_days(self, datetime):
        plant = self.plant_fixture()
        datetime.today.return_value = dt(2016, 1, 3)
        self.assertEqual(plant.mature_in, 7)

    @mock.patch("app.models.datetime.datetime")
    def test_mature_in_when_mature_gives_mature(self, datetime):
        plant = self.plant_fixture()
        datetime.today.return_value = dt(2016, 1, 17)
        self.assertEqual(plant.mature_in, models.Plant.Mature)

    def test_only_allows_one_plant_per_slot_id(self):
        self.plant_fixture().save()
        self.assertFalse(self.plant_fixture().is_valid())

    def test_permits_max_of_two_plants(self):
        plant = self.plant_fixture()
        plant.slot_id = 3
        self.assertFalse(plant.is_valid())

    def test_looks_up_by_slot_id(self):
        plant = self.plant_fixture()
        plant.save()
        self.assertEqual(models.Plant.for_slot(plant.slot_id), plant)

    def test_raises_if_slot_id_lookup_fails(self):
        plant = self.plant_fixture()
        with self.assertRaises(models.lazy_record.RecordNotFound):
            models.Plant.for_slot(plant.slot_id)

    def test_returns_None_if_slot_id_lookup_fails_with_no_raise_option(self):
        plant = self.plant_fixture()
        self.assertEqual(models.Plant.for_slot(plant.slot_id,
                                               raise_if_not_found=False),
                         None)

    @mock.patch("app.models.datetime.datetime")
    def test_loads_from_json(self, datetime):
        datetime.today.return_value = dt(2016, 1, 1)
        json_plant = models.Plant.from_json(self.plant_json())
        self.assertEqual(json_plant.water_tolerance, 30.0)
        self.assertEqual(json_plant.water_ideal, 57.0)
        self.assertEqual(json_plant.photo_url, "testPlant.png")
        self.assertEqual(json_plant.name, "testPlant")
        self.assertEqual(json_plant.plant_database_id, 1)
        self.assertEqual(json_plant.mature_on, dt(2016, 1, 10))

    def plant_fixture(self):
        return models.Plant(name="testPlant",
                            photo_url="testPlant.png",
                            water_ideal=57.0,
                            water_tolerance=30.0,
                            light_ideal=50.0,
                            light_tolerance=10.0,
                            acidity_ideal=9.0,
                            acidity_tolerance=1.0,
                            humidity_ideal=0.2,
                            humidity_tolerance=0.1,
                            mature_on=dt(2016, 1, 10),
                            slot_id=1,
                            plant_database_id=1)

    def plant_json(self):
        return {
                   "water_tolerance": 30.0,
                   "water_ideal": 57.0,
                   "updated_at": "2016-01-19T04:28:24Z",
                   "photo_url": "testPlant.png",
                   "name": "testPlant",
                   "maturity": 9,
                   "light_tolerance": 10.0,
                   "light_ideal": 50.0,
                   "inserted_at": "2016-01-19T04:28:24Z",
                   "id": 1,
                   "humidity_tolerance": 0.01,
                   "humidity_ideal": 0.2,
                   "acidity_tolerance": 1.0,
                   "acidity_ideal": 9.0
               }


class TestSensorDataPoint(unittest.TestCase):
    pass

if __name__ == '__main__':
    unittest.main()
