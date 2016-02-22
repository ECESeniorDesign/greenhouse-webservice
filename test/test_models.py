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
        plant = plant_fixture()
        datetime.today.return_value = dt(2016, 1, 3)
        self.assertEqual(plant.mature_in, 7)

    @mock.patch("app.models.datetime.datetime")
    def test_mature_in_when_mature_gives_mature(self, datetime):
        plant = plant_fixture()
        datetime.today.return_value = dt(2016, 1, 17)
        self.assertEqual(plant.mature_in, models.Plant.Mature)

    @mock.patch("app.models.datetime.datetime")
    def test_mature_when_not_mature_is_false(self, datetime):
        plant = plant_fixture()
        datetime.today.return_value = dt(2016, 1, 3)
        self.assertFalse(plant.mature)

    @mock.patch("app.models.datetime.datetime")
    def test_mature_when_mature_is_true(self, datetime):
        plant = plant_fixture()
        datetime.today.return_value = dt(2016, 1, 17)
        self.assertTrue(plant.mature)

    def test_only_allows_one_plant_per_slot_id(self):
        plant_fixture().save()
        self.assertFalse(plant_fixture().is_valid())

    def test_permits_max_of_two_plants(self):
        plant = plant_fixture()
        plant.slot_id = 3
        self.assertFalse(plant.is_valid())

    def test_looks_up_by_slot_id(self):
        plant = plant_fixture()
        plant.save()
        self.assertEqual(models.Plant.for_slot(plant.slot_id), plant)

    def test_raises_if_slot_id_lookup_fails(self):
        plant = plant_fixture()
        with self.assertRaises(models.lazy_record.RecordNotFound):
            models.Plant.for_slot(plant.slot_id)

    def test_returns_None_if_slot_id_lookup_fails_with_no_raise_option(self):
        plant = plant_fixture()
        self.assertEqual(models.Plant.for_slot(plant.slot_id,
                                               raise_if_not_found=False),
                         None)

    @mock.patch("app.models.datetime.datetime")
    def test_loads_from_json(self, datetime):
        datetime.today.return_value = dt(2016, 1, 1)
        json_plant = models.Plant.from_json(plant_json())
        self.assertEqual(json_plant.water_tolerance, 30.0)
        self.assertEqual(json_plant.water_ideal, 57.0)
        self.assertEqual(json_plant.photo_url, "testPlant.png")
        self.assertEqual(json_plant.name, "testPlant")
        self.assertEqual(json_plant.plant_database_id, 1)
        self.assertEqual(json_plant.mature_on, dt(2016, 1, 10))

    def test_gets_current_light_data(self):
        plant = plant_fixture()
        plant.save()
        plant.sensor_data_points.build(sensor_name="light",
                                       sensor_value=15).save()
        self.assertEqual(plant.light, 15)

    def test_returns_0_with_no_light_data(self):
        plant = plant_fixture()
        plant.save()
        self.assertEqual(plant.light, 0)

    def test_gets_current_water_data(self):
        plant = plant_fixture()
        plant.save()
        plant.sensor_data_points.build(sensor_name="water",
                                       sensor_value=15).save()
        self.assertEqual(plant.water, 15)

    def test_returns_0_with_no_water_data(self):
        plant = plant_fixture()
        plant.save()
        self.assertEqual(plant.water, 0)

    def test_gets_current_temperature_data(self):
        plant = plant_fixture()
        plant.save()
        plant.sensor_data_points.build(sensor_name="temperature",
                                       sensor_value=15).save()
        self.assertEqual(plant.temperature, 15)

    def test_returns_0_with_no_temperature_data(self):
        plant = plant_fixture()
        plant.save()
        self.assertEqual(plant.temperature, 0)

    def test_gets_current_humidity_data(self):
        plant = plant_fixture()
        plant.save()
        plant.sensor_data_points.build(sensor_name="humidity",
                                       sensor_value=15).save()
        self.assertEqual(plant.humidity, 15)

    def test_returns_0_with_no_humidity_data(self):
        plant = plant_fixture()
        plant.save()
        self.assertEqual(plant.humidity, 0)

    def test_gets_current_acidity_data(self):
        plant = plant_fixture()
        plant.save()
        plant.sensor_data_points.build(sensor_name="acidity",
                                       sensor_value=15).save()
        self.assertEqual(plant.acidity, 15)

    def test_returns_0_with_no_acidity_data(self):
        plant = plant_fixture()
        plant.save()
        self.assertEqual(plant.acidity, 0)

    def test_raises_attribute_error_on_bad_access(self):
        with self.assertRaises(AttributeError):
            plant_fixture().asfasdfsadfas

    def test_records_sensor_data(self):
        plant = plant_fixture()
        plant.save()
        plant.record_sensor("light", 17.6)
        self.assertEqual(plant.light, 17.6)

class TestPlantDatabase(unittest.TestCase):

    @mock.patch("app.models.PLANT_DATABASE", new="PLANT_DATABASE")
    @mock.patch("app.models.json")
    @mock.patch("app.models.urllib2")
    @mock.patch("app.models.Plant.from_json")
    def test_lists_plants_in_plant_database(self, from_json, urllib2, json):
        response = mock.Mock(name="response")
        json_response = plant_json()
        json_response["id"] = json_response["plant_database_id"]
        del json_response["plant_database_id"]
        plant = mock.Mock(name="plant")
        urllib2.urlopen.return_value = response
        json.load.return_value = [json_response]
        from_json.return_value = plant
        self.assertEqual(models.PlantDatabase.all_plants(), [plant])
        urllib2.urlopen.assert_called_with("http://PLANT_DATABASE/api/plants")
        from_json.assert_called_with(plant_json())
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
        json_response = plant_json()
        json_response["id"] = json_response["plant_database_id"]
        del json_response["plant_database_id"]
        plant = mock.Mock(name="plant")
        urllib2.urlopen.return_value = response
        json.load.return_value = json_response
        from_json.return_value = plant
        self.assertEqual(models.PlantDatabase.find_plant(1), plant)
        urllib2.urlopen.assert_called_with(
            "http://PLANT_DATABASE/api/plants/1")
        from_json.assert_called_with(plant_json())
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

    @mock.patch("app.models.PLANT_DATABASE", new="PLANT_DATABASE")
    @mock.patch("app.models.json")
    @mock.patch("app.models.requests.post")
    @mock.patch("app.models.Plant.from_json")
    def test_comp_plants_in_plant_database(self, from_json, post, json):
        response = mock.Mock(name="response")
        json_response = plant_json()
        json_response["id"] = json_response["plant_database_id"]
        del json_response["plant_database_id"]
        plant = mock.Mock(name="plant", plant_database_id=1)
        post.return_value = response
        json.load.return_value = [json_response]
        from_json.return_value = plant
        self.assertEqual(models.PlantDatabase.compatible_plants([plant]), [plant])
        post.assert_called_with(
            "http://PLANT_DATABASE/api/plants/compatible", json={"ids": [1]})
        from_json.assert_called_with(plant_json())
        json.load.assert_called_with(response)

    @mock.patch("app.models.requests.post")
    def test_comp_raises_cannot_connect_if_cannot_connect(self, post):
        post.side_effect = models.requests.exceptions.ConnectionError
        with self.assertRaises(models.PlantDatabase.CannotConnect):
            models.PlantDatabase.compatible_plants(
                [mock.Mock(name="plant", plant_database_id=1)])

    @mock.patch("app.models.PLANT_DATABASE", new="PLANT_DATABASE")
    @mock.patch("app.models.json")
    @mock.patch("app.models.urllib2")
    def test_gets_plant_params(self, urllib2, json):
        response = mock.Mock(name="response")
        json_response = {'id': 5, 'inserted_at': 11, 'updated_at': 11,
                         'name': "Foo", "maturity": 17}
        expected = {'name': "Foo", "maturity": 17, 'plant_database_id': 5}
        plant = mock.Mock(name="plant")
        urllib2.urlopen.return_value = response
        json.load.return_value = json_response
        self.assertEqual(models.PlantDatabase.plant_params(1), expected)
        urllib2.urlopen.assert_called_with(
            "http://PLANT_DATABASE/api/plants/1")
        json.load.assert_called_with(response)

    @mock.patch("app.models.PLANT_DATABASE", new="PLANT_DATABASE")
    @mock.patch("app.models.json")
    @mock.patch("app.models.urllib2")
    def test_filters_plant_params(self, urllib2, json):
        response = mock.Mock(name="response")
        json_response = {'id': 5, 'inserted_at': 11, 'updated_at': 11,
                         'name': "Foo", "maturity": 17}
        expected = {'name': "Foo", 'plant_database_id': 5}
        plant = mock.Mock(name="plant")
        urllib2.urlopen.return_value = response
        json.load.return_value = json_response
        self.assertEqual(
            models.PlantDatabase.plant_params(1, filter=["maturity"]),
            expected)
        urllib2.urlopen.assert_called_with(
            "http://PLANT_DATABASE/api/plants/1")
        json.load.assert_called_with(response)

    @mock.patch("app.models.PLANT_DATABASE", new="PLANT_DATABASE")
    @mock.patch("app.models.urllib2.urlopen")
    def test_params_raises_if_cannot_connect_to_plant_database(self, urlopen):
        urlopen.side_effect = models.urllib2.URLError(
            "[Errno 61] Connection refused")
        with self.assertRaises(models.PlantDatabase.CannotConnect):
            models.PlantDatabase.plant_params(1)


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


class TestNotificationThreshold(unittest.TestCase):

    @mock.patch("app.models.datetime.datetime")
    def setUp(self, datetime):
        models.lazy_record.connect_db(TEST_DATABASE)
        with open(SCHEMA) as schema:
            models.lazy_record.load_schema(schema.read())
        self.start_time = dt.now()
        datetime.now.return_value = self.start_time
        datetime.today.return_value = self.start_time
        self.plant = plant_fixture()
        self.plant.plant_setting = models.PlantSetting()
        self.plant.save()
        self.point = models.SensorDataPoint.create(plant_id=1,
                                                   sensor_value=17.3,
                                                   sensor_name="light")
        self.point2 = models.SensorDataPoint.create(plant_id=1,
                                                    sensor_value=17.3,
                                                    sensor_name="water")
        self.point3 = models.SensorDataPoint.create(plant_id=2,
                                                    sensor_name="light",
                                                    sensor_value=17.3)
        self.nt = self.plant.plant_setting.notification_thresholds.create(
            sensor_name="light",
            deviation_percent=15,
            deviation_time=1)

    def test_knows_sensors(self):
        self.assertIn(self.point, self.nt.sensor_data_points)
        self.assertNotIn(self.point2, self.nt.sensor_data_points)
        self.assertNotIn(self.point3, self.nt.sensor_data_points)

    def test_is_invalid_if_time_is_zero(self):
        self.nt.deviation_time = 0
        self.assertFalse(self.nt.is_valid())

    def test_is_invalid_if_percent_is_zero(self):
        self.nt.deviation_percent = 0
        self.assertFalse(self.nt.is_valid())

    def test_sets_triggered_at_to_creation_time(self):
        self.assertEqual(self.nt.triggered_at, self.start_time)

@mock.patch("app.models.PLANT_DATABASE", new="PLANT_DATABASE")
@mock.patch("app.models.requests.post")
class TestToken(unittest.TestCase):

    @mock.patch("app.models.datetime.datetime")
    def setUp(self, datetime):
        models.lazy_record.connect_db(TEST_DATABASE)
        with open(SCHEMA) as schema:
            models.lazy_record.load_schema(schema.read())

    def test_makes_request_to_plant_database(self, post):
        post.return_value = mock.Mock(ok=True, status_code=200,
                                      text='{"token":"g3QAAAACZAAEZGF0YWEBZAA'
                                           'Gc2lnbmVkbgYAdyhV01IB--4XapswheNb'
                                           'ceQfCSoSrQRTbUJ2c="}')
        models.Token.get(username="chaseconklin",
                         password="mypassword")
        post.assert_called_with("http://PLANT_DATABASE/api/token",
                                json={'user': {'username': 'chaseconklin',
                                               'password': 'mypassword'}})

    def test_makes_request_to_plant_database_with_token(self, post):
        post.return_value = mock.Mock(ok=True, status_code=200,
                                      text='{"token":"g3QAAAACZAAEZGF0YWEBZAA'
                                           'Gc2lnbmVkbgYAdyhV01IB--4XapswheNb'
                                           'ceQfCSoSrQRTbUJ2c="}')
        models.Token.get(token="mytoken")
        post.assert_called_with("http://PLANT_DATABASE/api/token",
                                json={'token': 'mytoken'})

    def test_raises_cannot_connect_if_cannot_connect(self, post):
        post.side_effect = models.requests.exceptions.ConnectionError
        with self.assertRaises(models.PlantDatabase.CannotConnect):
            models.Token.get(username="chaseconklin",
                             password="mypassword")

    def test_returns_false_if_credentials_invalid(self, post):
        post.return_value = mock.Mock(ok=False, status_code=403)
        self.assertFalse(models.Token.get(username="chaseconklin",
                                          password="mypassword"))

    def test_returns_true_if_credentials_valid(self, post):
        post.return_value = mock.Mock(ok=True, status_code=200,
                                      text='{"token":"g3QAAAACZAAEZGF0YWEBZAA'
                                           'Gc2lnbmVkbgYAdyhV01IB--4XapswheNb'
                                           'ceQfCSoSrQRTbUJ2c="}')
        self.assertTrue(models.Token.get(username="chaseconklin",
                                          password="mypassword"))

    def test_saves_token_if_valid(self, post):
        post.return_value = mock.Mock(ok=True, status_code=200,
                                      text='{"token":"g3QAAAACZAAEZGF0YWEBZAA'
                                           'Gc2lnbmVkbgYAdyhV01IB--4XapswheNb'
                                           'ceQfCSoSrQRTbUJ2c="}')
        models.Token.get(username="chaseconklin",
                         password="mypassword")
        self.assertEqual(models.Token.last().token, "g3QAAAACZAAEZGF0YWEBZAA"
                                                    "Gc2lnbmVkbgYAdyhV01IB--"
                                                    "4XapswheNbceQfCSoSrQRTb"
                                                    "UJ2c=")

    @mock.patch("app.models.Token.get")
    def test_refresh_calls_get_with_last_token(self, get, _post):
        models.Token.create(token="mytoken")
        models.Token.refresh()
        get.assert_called_with(token="mytoken")

def plant_json():
    return {
               "water_tolerance": 30.0,
               "water_ideal": 57.0,
               "photo_url": "testPlant.png",
               "name": "testPlant",
               "maturity": 9,
               "light_tolerance": 10.0,
               "light_ideal": 50.0,
               "plant_database_id": 1,
               "humidity_tolerance": 0.01,
               "humidity_ideal": 0.2,
               "acidity_tolerance": 1.0,
               "acidity_ideal": 9.0
           }


def plant_fixture():
    return models.Plant(name="testPlant",
                        photo_url="testPlant.png",
                        water_ideal=57.0,
                        water_tolerance=30.0,
                        light_ideal=50.0,
                        light_tolerance=10.0,
                        acidity_ideal=9.0,
                        acidity_tolerance=1.0,
                        temperature_ideal=55.5,
                        temperature_tolerance=11.3,
                        humidity_ideal=0.2,
                        humidity_tolerance=0.1,
                        mature_on=dt(2016, 1, 10),
                        slot_id=1,
                        plant_database_id=1)


if __name__ == '__main__':
    unittest.main()
