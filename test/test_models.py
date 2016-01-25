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

    def test_gets_current_light_data(self):
        plant = self.plant_fixture()
        plant.save()
        plant.sensor_data_points.build(sensor_name="light",
                                       sensor_value=15).save()
        self.assertEqual(plant.light, 15)

    def test_returns_0_with_no_light_data(self):
        plant = self.plant_fixture()
        plant.save()
        self.assertEqual(plant.light, 0)

    def test_gets_current_water_data(self):
        plant = self.plant_fixture()
        plant.save()
        plant.sensor_data_points.build(sensor_name="water",
                                       sensor_value=15).save()
        self.assertEqual(plant.water, 15)

    def test_returns_0_with_no_water_data(self):
        plant = self.plant_fixture()
        plant.save()
        self.assertEqual(plant.water, 0)

    def test_gets_current_temperature_data(self):
        plant = self.plant_fixture()
        plant.save()
        plant.sensor_data_points.build(sensor_name="temperature",
                                       sensor_value=15).save()
        self.assertEqual(plant.temperature, 15)

    def test_returns_0_with_no_temperature_data(self):
        plant = self.plant_fixture()
        plant.save()
        self.assertEqual(plant.temperature, 0)

    def test_gets_current_humidity_data(self):
        plant = self.plant_fixture()
        plant.save()
        plant.sensor_data_points.build(sensor_name="humidity",
                                       sensor_value=15).save()
        self.assertEqual(plant.humidity, 15)

    def test_returns_0_with_no_humidity_data(self):
        plant = self.plant_fixture()
        plant.save()
        self.assertEqual(plant.humidity, 0)

    def test_gets_current_acidity_data(self):
        plant = self.plant_fixture()
        plant.save()
        plant.sensor_data_points.build(sensor_name="acidity",
                                       sensor_value=15).save()
        self.assertEqual(plant.acidity, 15)

    def test_returns_0_with_no_acidity_data(self):
        plant = self.plant_fixture()
        plant.save()
        self.assertEqual(plant.acidity, 0)

    def test_raises_attribute_error_on_bad_access(self):
        with self.assertRaises(AttributeError):
            self.plant_fixture().asfasdfsadfas

    def test_records_sensor_data(self):
        plant = self.plant_fixture()
        plant.save()
        plant.record_sensor("light", 17.6)
        self.assertEqual(plant.light, 17.6)

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


class TestPlantDatabase(unittest.TestCase):

    @mock.patch("app.models.PLANT_DATABASE", new="PLANT_DATABASE")
    @mock.patch("app.models.json")
    @mock.patch("app.models.urllib2")
    @mock.patch("app.models.Plant.from_json")
    def test_lists_plants_in_plant_database(self, from_json, urllib2, json):
        response = mock.Mock(name="response")
        json_response = {'json': 'response'}
        plant = mock.Mock(name="plant")
        urllib2.urlopen.return_value = response
        json.load.return_value = [json_response]
        from_json.return_value = plant
        self.assertEqual(models.PlantDatabase.all_plants(), [plant])
        urllib2.urlopen.assert_called_with("http://PLANT_DATABASE/api/plants")
        from_json.assert_called_with(json_response)
        json.load.assert_called_with(response)

    @mock.patch("app.models.PLANT_DATABASE", new="PLANT_DATABASE")
    @mock.patch("app.models.urllib2.urlopen")
    def test_list_raises_if_cannot_connect_to_plant_database(self, urlopen):
        urlopen.side_effect = models.urllib2.URLError(
            "[Errno 61] Connection refused")
        with self.assertRaises(models.PlantDatabase.CannotConnect):
            models.PlantDatabase.all_plants()

    @mock.patch("app.models.PLANT_DATABASE", new="PLANT_DATABASE")
    @mock.patch("app.models.json")
    @mock.patch("app.models.urllib2")
    @mock.patch("app.models.Plant.from_json")
    def test_finds_plant_in_plant_database(self, from_json, urllib2, json):
        response = mock.Mock(name="response")
        json_response = {'json': 'response'}
        plant = mock.Mock(name="plant")
        urllib2.urlopen.return_value = response
        json.load.return_value = json_response
        from_json.return_value = plant
        self.assertEqual(models.PlantDatabase.find_plant(1), plant)
        urllib2.urlopen.assert_called_with(
            "http://PLANT_DATABASE/api/plants/1")
        from_json.assert_called_with(json_response)
        json.load.assert_called_with(response)

    @mock.patch("app.models.PLANT_DATABASE", new="PLANT_DATABASE")
    @mock.patch("app.models.json")
    @mock.patch("app.models.urllib2")
    @mock.patch("app.models.Plant.from_json")
    def test_returns_none_if_no_plant(self, from_json, urllib2, json):
        response = mock.Mock(name="response")
        urllib2.urlopen.return_value = response
        json.load.return_value = None
        self.assertEqual(models.PlantDatabase.find_plant(1), None)
        urllib2.urlopen.assert_called_with(
            "http://PLANT_DATABASE/api/plants/1")
        json.load.assert_called_with(response)

    @mock.patch("app.models.PLANT_DATABASE", new="PLANT_DATABASE")
    @mock.patch("app.models.urllib2.urlopen")
    def test_find_raises_if_cannot_connect_to_plant_database(self, urlopen):
        urlopen.side_effect = models.urllib2.URLError(
            "[Errno 61] Connection refused")
        with self.assertRaises(models.PlantDatabase.CannotConnect):
            models.PlantDatabase.find_plant(1)


class TestSensorDataPoint(unittest.TestCase):

    def setUp(self):
        models.lazy_record.connect_db(TEST_DATABASE)
        with open(SCHEMA) as schema:
            models.lazy_record.load_schema(schema.read())
        self.point = models.SensorDataPoint(plant_id=1, sensor_value=17.3)

    def tearDown(self):
        models.lazy_record.close_db()

    def test_validates_sensor_name(self):
        self.point.sensor_name = "water"
        self.assertTrue(self.point.is_valid())

    def test_validates_sensor_name(self):
        self.point.sensor_name = "cactus"
        self.assertFalse(self.point.is_valid())

    def test_scope_looks_up_by_sensor_name(self):
        in_scope = models.SensorDataPoint(plant_id=1,
                                          sensor_value=17.3,
                                          sensor_name="light")
        in_scope.save()
        out_scope = models.SensorDataPoint(plant_id=1,
                                           sensor_value=17.3,
                                           sensor_name="water")
        out_scope.save()
        self.assertIn(in_scope, models.SensorDataPoint.light())
        self.assertNotIn(out_scope, models.SensorDataPoint.light())


if __name__ == '__main__':
    unittest.main()
