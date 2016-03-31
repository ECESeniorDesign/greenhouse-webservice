import unittest
import mock
import os
import sys
import json
from datetime import datetime as dt, time
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import app.webservice as webservice
from app.config import TEST_DATABASE, SCHEMA

class TestPlantsController(unittest.TestCase):

    def setUp(self):
        # create a test client
        self.app = webservice.app.test_client()
        self.app.testing = True
        webservice.models.lazy_record.connect_db(TEST_DATABASE)
        with open(SCHEMA) as schema:
            webservice.models.lazy_record.load_schema(schema.read())

    def tearDown(self):
        webservice.models.lazy_record.close_db()

    def test_home_status_code(self):
        result = self.app.get('/')
        self.assertEqual(result.status_code, 200)

    @mock.patch("app.webservice.flask.render_template")
    def test_renders_home_page_with_plants_and_water(self, render_template):
        self.app.get('/')
        render_template.assert_called_with("plants/index.html",
                                           plants=[(None, 1), (None, 2)],
                                           water=0)

    @mock.patch("app.webservice.flask.render_template")
    def test_renders_home_page_with_plants_with_water(self, render_template):
        webservice.models.WaterLevel.create(level=85)
        self.app.get('/')
        render_template.assert_called_with("plants/index.html",
                                           plants=[(None, 1), (None, 2)],
                                           water=85)

    def test_plants_index_status_code(self):
        result = self.app.get('/plants')
        self.assertEqual(result.status_code, 200)

    @mock.patch("app.webservice.flask.render_template")
    def test_renders_plants_index_with_plants(self, render_template):
        self.app.get('/plants')
        render_template.assert_called_with("plants/index.html",
                                           plants=[(None, 1), (None, 2)],
                                           water=0)
    
    @mock.patch("app.webservice.models.PlantDatabase")
    def test_plants_new_status_code(self, PlantDatabase):
        plant = mock.Mock(name="plant")
        PlantDatabase.compatible_plants.return_value = [plant]
        result = self.app.get('/plants/new?slot_id=2')
        self.assertEqual(result.status_code, 200)

    @mock.patch("app.webservice.models.PlantDatabase")
    @mock.patch("app.webservice.flask.render_template")
    def test_renders_plants_new_with_plants(self, render_template,
                                            PlantDatabase):
        plant = mock.Mock(name="plant")
        PlantDatabase.compatible_plants.return_value = [plant]
        self.app.get('/plants/new?slot_id=2')
        render_template.assert_called_with("plants/new.html",
                                           plants=[plant],
                                           slot_id=2)

    @mock.patch("app.webservice.models.PlantDatabase.compatible_plants")
    def test_plants_new_redirects_on_connection_failure(self, all_plants):
        all_plants.side_effect = webservice.models.PlantDatabase.CannotConnect
        result = self.app.get("/plants/new?slot_id=1")
        self.assertEqual(result.status_code, 302)
        self.assertEqual(result.headers['Location'],
                         'http://localhost/plants')

    @mock.patch("app.webservice.models.PlantDatabase")
    def test_plants_create_redirects_to_show(self, PlantDatabase):
        PlantDatabase.find_plant.return_value = build_plant()
        result = self.app.post("/plants", data=dict(
            plant_database_id=1,
            slot_id=1
        ))
        self.assertEqual(result.status_code, 302)
        self.assertEqual(result.headers['Location'],
                         'http://localhost/plants/1')

    @mock.patch("app.webservice.models.PlantDatabase")
    def test_plants_create_saves_plant(self, PlantDatabase):
        plant = build_plant(slot_id=None)
        PlantDatabase.find_plant.return_value = plant
        result = self.app.post("/plants", data=dict(
            plant_database_id=1,
            slot_id=1
        ))
        self.assertEqual(plant.slot_id, 1)
        self.assertEqual(plant.id, 1)

    @mock.patch("app.webservice.models.PlantDatabase")
    def test_plants_create_saves_plant_settings(self, PlantDatabase):
        plant = build_plant(slot_id=None)
        PlantDatabase.find_plant.return_value = plant
        self.assertEqual(len(webservice.models.PlantSetting.all()), 0)
        result = self.app.post("/plants", data=dict(
            plant_database_id=1,
            slot_id=1
        ))
        self.assertEqual(webservice.models.PlantSetting.last().plant, plant)

    @mock.patch("app.webservice.models.PlantDatabase")
    def test_plants_create_redirects_to_index_on_failure(self, PlantDatabase):
        create_plant(slot_id=1)
        PlantDatabase.find_plant.return_value = build_plant(slot_id=1)
        result = self.app.post("/plants", data=dict(
            plant_database_id=1,
            slot_id=1
        ))
        self.assertEqual(result.status_code, 302)
        self.assertEqual(result.headers['Location'],
                         'http://localhost/plants')

    @mock.patch("app.webservice.models.PlantDatabase")
    def test_plants_create_redirects_to_index_if_no_plant(self,
                                                          PlantDatabase):
        PlantDatabase.find_plant.return_value = None
        result = self.app.post("/plants", data=dict(
            plant_database_id=1,
            slot_id=1
        ))
        self.assertEqual(result.status_code, 302)
        self.assertEqual(result.headers['Location'],
                         'http://localhost/plants')

    def test_plants_show_status_code(self):
        create_plant(slot_id=1)
        result = self.app.get('/plants/1')
        self.assertEqual(result.status_code, 200)

    @mock.patch("app.webservice.presenters.PlantPresenter")
    @mock.patch("app.webservice.flask.render_template")
    def test_renders_plants_show_with_plant(self, render_template,
                                            PlantPresenter):
        plant = create_plant(slot_id=1)
        self.app.get('/plants/1')
        PlantPresenter.assert_called_with(plant)
        render_template.assert_called_with("plants/show.html",
                                           plant=PlantPresenter.return_value)

    def test_show_redirects_to_index_when_plant_does_not_exist(self):
        response = self.app.get('/plants/1')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'],
                         'http://localhost/plants')

    def test_destroy_status_code(self):
        create_plant(slot_id=1)
        response = self.app.delete('/plants/1')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'],
                         'http://localhost/plants')

    def test_destroy_deletes_plant(self):
        create_plant(slot_id=1)
        response = self.app.delete('/plants/1')
        self.assertEqual(len(webservice.models.Plant.all()), 0)

    def test_destory_redirects_to_index_on_lookup_failure(self):
        response = self.app.delete('/plants/1')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'],
                         'http://localhost/plants')

class TestLogsController(unittest.TestCase):

    def setUp(self):
        # create a test client
        self.app = webservice.app.test_client()
        self.app.testing = True
        webservice.models.lazy_record.connect_db(TEST_DATABASE)
        with open(SCHEMA) as schema:
            webservice.models.lazy_record.load_schema(schema.read())
        self.plant = create_plant(slot_id=1)

    def test_index_status_code(self):
        response = self.app.get('/plants/1/logs')
        self.assertEqual(response.status_code, 200)

    @mock.patch("app.webservice.flask.render_template")
    def test_index_renders_template(self, render_template):
        response = self.app.get('/plants/1/logs')
        render_template.assert_called_with('logs/index.html',
                                           plant=self.plant,
                                           sensors=list(
                                                   enumerate(webservice\
                                                             .models\
                                                             .SensorDataPoint\
                                                             .SENSORS)))

    @mock.patch("app.webservice.presenters.LogDataPresenter")
    @mock.patch("app.webservice.flask.Response")
    def test_download_downloads_log_file(self, make_response, presenter):
        created_response = mock.Mock(name="response", headers={})
        make_response.return_value = created_response
        response = self.app.get('/plants/1/logs/download')
        presenter.assert_called_with(self.plant)
        make_response.assert_called_with(presenter.return_value\
                                                  .log_string\
                                                  .return_value,
                                         mimetype="text/plain")
        self.assertEqual(created_response.headers["Content-Disposition"],
                         "attachment; filename=sensors.log")


class TestPlantSettingsController(unittest.TestCase):

    def setUp(self):
        # create a test client
        self.app = webservice.app.test_client()
        self.app.testing = True
        webservice.models.lazy_record.connect_db(TEST_DATABASE)
        with open(SCHEMA) as schema:
            webservice.models.lazy_record.load_schema(schema.read())
        self.plant = create_plant(slot_id=1)
        self.setting = webservice.models.PlantSetting.create(plant=self.plant)
        self.threshold = webservice.models.NotificationThreshold.create(
                             plant_setting=self.setting,
                             sensor_name="light",
                             deviation_percent=15,
                             deviation_time=3)

    def test_index_response_code(self):
        response = self.app.get("/plants/1/settings")
        self.assertEqual(response.status_code, 200)

    @mock.patch("app.webservice.models.Plant")
    @mock.patch("app.webservice.flask.render_template")
    def test_index_shows_all_settings(self, render_template, Plant):
        Plant.for_slot.return_value.plant_setting.\
            notification_thresholds = [self.threshold]
        names = webservice.models.SensorDataPoint.SENSORS
        response = self.app.get("/plants/1/settings")
        render_template.assert_called_with("plant_settings/index.html",
                                           thresholds=[self.threshold],
                                           plant=Plant.for_slot.return_value,
                                           names=names)

    @mock.patch("app.webservice.models.PlantSetting.notification_thresholds")
    def test_create_adds_new_thresholds(self, notification_thresholds):
        self.app.post("/plants/1/settings", data=dict(
            attribute=["water", "humidity"],
            deviation_percent=["11", "15"],
            deviation_time=["1", "1.25"],
            threshold_id=["", ""],
            delete=["false", "false"],
        ))
        calls = [
                    mock.call(sensor_name="water",
                              deviation_percent=11,
                              deviation_time=1.0),
                    mock.call(sensor_name="humidity",
                              deviation_percent=15,
                              deviation_time=1.25),
                ]
        notification_thresholds.create.assert_has_calls(calls)
        self.assertEqual(len(notification_thresholds.create.mock_calls), 2)

    @mock.patch("app.webservice.models.PlantSetting.notification_thresholds")
    def test_create_rejects_invalid_thresholds(self, notification_thresholds):
        response = self.app.post("/plants/1/settings", data=dict(
            attribute=["water", "humidity", ""],
            deviation_percent=["11", "15", ""],
            deviation_time=["1", "1.25", ""],
            threshold_id=["", "", ""],
            delete=["false", "false", "false"],
        ))
        calls = [
                    mock.call(sensor_name="water",
                              deviation_percent=11,
                              deviation_time=1.0),
                    mock.call(sensor_name="humidity",
                              deviation_percent=15,
                              deviation_time=1.25),
                ]
        self.assertEqual(response.status_code, 302)
        notification_thresholds.create.assert_has_calls(calls)
        self.assertEqual(len(notification_thresholds.create.mock_calls), 2)

    @mock.patch("app.webservice.flask.flash")
    @mock.patch("app.webservice.models.PlantSetting.notification_thresholds")
    def test_create_flash_differs_with_rejected(self, notification_thresholds, flash):
        response = self.app.post("/plants/1/settings", data=dict(
            attribute=["water", "humidity"],
            deviation_percent=["11", "15"],
            deviation_time=["1", ""],
            threshold_id=["", ""],
            delete=["false", "false"],
        ))
        self.assertEqual(response.status_code, 302)
        flash.assert_called_with("Some Settings Updated", 'warning')

    @mock.patch("app.webservice.flask.flash")
    def test_redirects_to_index(self, flash):
        response = self.app.post("/plants/1/settings", data=dict(
            attribute=["water", "humidity"],
            deviation_percent=["11", "15"],
            deviation_time=["1", "1.25"],
            threshold_id=["", ""],
            delete=["false", "false"],
        ))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'],
                         'http://localhost/plants/1/settings')
        flash.assert_called_with("Settings Updated", 'notice')

    @mock.patch("app.webservice.models.PlantSetting.notification_thresholds")
    def test_updates_existing_thresholds(self, notification_thresholds):
        response = self.app.post("/plants/1/settings", data=dict(
            attribute=["water", "humidity"],
            deviation_percent=["11", "15"],
            deviation_time=["1", "1.25"],
            threshold_id=["", "1"],
            delete=["false", "false"],
        ))
        notification_thresholds.create.assert_called_once_with(
            sensor_name="water",
            deviation_percent=11,
            deviation_time=1.0
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(mock.call(id=1), notification_thresholds.where.mock_calls)
        notification_thresholds.where.return_value.first.assert_called_with()
        old = notification_thresholds.where.return_value.first.return_value
        old.update.assert_called_with(sensor_name="humidity",
                                      deviation_percent=15,
                                      deviation_time=1.25)
        old.save.assert_called_with()

    @mock.patch("app.webservice.models.PlantSetting.notification_thresholds")
    def test_update_rejects_thresholds(self, notification_thresholds):
        response = self.app.post("/plants/1/settings", data=dict(
            attribute=["water", "humidity"],
            deviation_percent=["11", "15"],
            deviation_time=["1", ""],
            threshold_id=["", "1"],
            delete=["false", "false"],
        ))
        notification_thresholds.create.assert_called_once_with(
            sensor_name="water",
            deviation_percent=11,
            deviation_time=1.0
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(notification_thresholds.where.called)

    @mock.patch("app.webservice.models.PlantSetting.notification_thresholds")
    def test_doesnt_update_deleted_thresholds(self, notification_thresholds):
        response = self.app.post("/plants/1/settings", data=dict(
            attribute=["water", "humidity"],
            deviation_percent=["11", "15"],
            deviation_time=["1", "1.25"],
            threshold_id=["", "1"],
            delete=["false", "true"],
        ))
        self.assertFalse(notification_thresholds.where.return_value.first.called)
        self.assertEqual(response.status_code, 302)

    @mock.patch("app.webservice.models.PlantSetting.notification_thresholds")
    def test_deletes_deleted_thresholds(self, notification_thresholds):
        old_threshold = mock.Mock(name="threshold")
        notification_thresholds.where.return_value = [old_threshold]
        response = self.app.post("/plants/1/settings", data=dict(
            attribute=["water", "humidity"],
            deviation_percent=["11", "15"],
            deviation_time=["1", "1.25"],
            threshold_id=["", "1"],
            delete=["false", "true"],
        ))
        notification_thresholds.where.assert_called_with(id=[1])
        old_threshold.destroy.assert_called_with()
        self.assertEqual(response.status_code, 302)

    @mock.patch("app.webservice.models.PlantSetting.notification_thresholds")
    def test_deletes_when_invalid(self, notification_thresholds):
        old_threshold = mock.Mock(name="threshold")
        notification_thresholds.where.return_value = [old_threshold]
        response = self.app.post("/plants/1/settings", data=dict(
            attribute=["water", "humidity"],
            deviation_percent=["11", "15"],
            deviation_time=["1", ""],
            threshold_id=["", "1"],
            delete=["false", "true"],
        ))
        notification_thresholds.where.assert_called_with(id=[1])
        old_threshold.destroy.assert_called_with()
        self.assertEqual(response.status_code, 302)

    @mock.patch("app.webservice.flask.flash")
    def test_create_flash_differs_with_invalid(self, flash):
        response = self.app.post("/plants/1/settings", data=dict(
            attribute=["water", "humidity"],
            deviation_percent=["11", "15"],
            deviation_time=["1", "0"],
            threshold_id=["", ""],
            delete=["false", "false"],
        ))
        self.assertEqual(response.status_code, 302)
        flash.assert_called_with("Some Settings Updated", 'warning')

    @mock.patch("app.webservice.flask.flash")
    def test_update_flash_differs_with_invalid(self, flash):
        response = self.app.post("/plants/1/settings", data=dict(
            attribute=["water", "humidity"],
            deviation_percent=["11", "15"],
            deviation_time=["1", "0"],
            threshold_id=["", "1"],
            delete=["false", "false"],
        ))
        self.assertEqual(response.status_code, 302)
        flash.assert_called_with("Some Settings Updated", 'warning')

    @mock.patch("app.webservice.flask.flash")
    def test_update_flash_differs_with_no_valid(self, flash):
        response = self.app.post("/plants/1/settings", data=dict(
            attribute=["water", "humidity"],
            deviation_percent=["15"],
            deviation_time=["0"],
            threshold_id=["1"],
            delete=["false"],
        ))
        self.assertEqual(response.status_code, 302)
        flash.assert_called_with("Settings could not be updated", 'error')

class TestSessions(unittest.TestCase):

    def setUp(self):
        # create a test client
        self.app = webservice.app.test_client()
        self.app.testing = True
        webservice.models.lazy_record.connect_db(TEST_DATABASE)
        with open(SCHEMA) as schema:
            webservice.models.lazy_record.load_schema(schema.read())

    def test_get_return_code(self):
        response = self.app.get("/login")
        self.assertEqual(response.status_code, 200)

    @mock.patch("app.webservice.flask.render_template")
    def test_renders_login_page(self, render_template):
        response = self.app.get("/login")
        render_template.assert_called_with("sessions/new.html")

    @mock.patch("app.webservice.models")
    def test_post_requests_token(self, models):
        response = self.app.post("/login",
                                 data={'username': 'chaseconklin',
                                       'password':'mysupersecretpassword'})
        models.Token.get.assert_called_with(username='chaseconklin',
                                            password='mysupersecretpassword')

    @mock.patch("app.webservice.models")
    def test_redirects_to_home_on_success(self, models):
        models.Token.get.return_value = True
        response = self.app.post("/login",
                                 data={'username': 'chaseconklin',
                                       'password':'mysupersecretpassword'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'],
                         'http://localhost/plants')

    @mock.patch("app.webservice.models")
    def test_renders_login_on_failure_a(self, models):
        models.Token.get.return_value = False
        response = self.app.post("/login",
                                 data={'username': 'chaseconklin',
                                       'password':'mysupersecretpassword'})
        self.assertEqual(response.status_code, 200)

    @mock.patch("app.webservice.flask.flash")
    @mock.patch("app.webservice.flask.render_template")
    @mock.patch("app.webservice.models")
    def test_renders_login_on_failure_b(self, models, render_template, flash):
        models.Token.get.return_value = False
        response = self.app.post("/login",
                                 data={'username': 'chaseconklin',
                                       'password':'mysupersecretpassword'})
        flash.assert_called_with("Invalid Credentials", "error")
        render_template.assert_called_with("sessions/new.html")


class TestGlobalSettingsController(unittest.TestCase):

    def setUp(self):
        # create a test client
        self.app = webservice.app.test_client()
        self.app.testing = True
        webservice.models.lazy_record.connect_db(TEST_DATABASE)
        with open(SCHEMA) as schema:
            webservice.models.lazy_record.load_schema(schema.read())

    @mock.patch(
        "app.webservice.models.PlantDatabase.get_notification_settings")
    @mock.patch("app.webservice.models.GlobalSetting")
    @mock.patch("app.webservice.flask.render_template")
    def test_index_renders_form(self, render_template, GlobalSetting, gns):
        ns = {'email': True, 'push': False}
        gns.return_value = ns
        control = mock.Mock(name="control",
                            enabled=True,
                            active_during=(
                                time(0, 12, 30),
                                dt(1, 11, 15)))
        control.name = "fan"
        GlobalSetting.controls = [control]
        self.app.get("/settings")
        render_template.assert_called_with("global_settings/index.html",
                                           controls=[control],
                                           notification_settings=ns)

    @mock.patch(
        "app.webservice.models.PlantDatabase.get_notification_settings")
    @mock.patch("app.webservice.models.GlobalSetting")
    def test_index_returns_200_status_code(self, GlobalSetting, gns):
        GlobalSetting.controls = []
        response = self.app.get("/settings")
        self.assertEqual(response.status_code, 200)

    @mock.patch("app.webservice.forms.GlobalSettingsForm")
    @mock.patch("app.webservice.models.GlobalSetting")
    def test_create_redirects_home(self, GlobalSetting, gs_form):
        control = mock.Mock(name="control",
                            enabled=True,
                            active_during=(
                                time(0, 12, 30),
                                dt(1, 11, 15)))
        control.name = "fan"
        GlobalSetting.controls = [control]
        response = self.app.post("/settings")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'],
                         'http://localhost/plants')

    @mock.patch("app.webservice.forms.GlobalSettingsForm")
    @mock.patch("app.webservice.flask")
    @mock.patch("app.webservice.models.GlobalSetting")
    def test_create_submits_form(self, GlobalSetting, flask, gs_form):
        control = mock.Mock(name="control",
                            enabled=True,
                            active_during=(
                                time(0, 12, 30),
                                dt(1, 11, 15)))
        control.name = "fan"
        GlobalSetting.controls = [control]
        self.app.post("/settings")
        gs_form.assert_called_with([control], flask.request.form)
        gs_form.return_value.submit.assert_called_with()

class TestAPIPlantsController(unittest.TestCase):

    def setUp(self):
        # create a test client
        self.app = webservice.app.test_client()
        self.app.testing = True
        webservice.models.lazy_record.connect_db(TEST_DATABASE)
        with open(SCHEMA) as schema:
            webservice.models.lazy_record.load_schema(schema.read())

    def test_index_with_no_plants(self):
        webservice.models.WaterLevel.create(level=51)
        response = self.app.get("/api/plants")
        self.assertEqual(json.loads(response.data), {
           'plants': [],
           'water_level': 51
        })

    def test_index_with_no_plants_and_no_water(self):
        response = self.app.get("/api/plants")
        self.assertEqual(json.loads(response.data), {
           'plants': [],
           'water_level': 0
        })

    def test_index_returns_plants(self):
        webservice.models.WaterLevel.create(level=51)
        build_plant().save()
        response = self.app.get("/api/plants")
        self.assertEqual(json.loads(response.data), {
           'plants': [
               {
                   'name': "testPlant",
                   'photo_url': "testPlant.png",
                   'slot_id': 1,
                   'plant_database_id': 1,
               }
           ],
           'water_level': 51
        })

    def test_show_gives_plant_condition_information(self):
        webservice.models.WaterLevel.create(level=51)
        plant = build_plant()
        plant.save()
        plant.record_sensor("light", 53.0)
        plant.record_sensor("water", 63.0)
        plant.record_sensor("humidity", 0.2)
        plant.record_sensor("temperature", 18.0)
        response = self.app.get("/api/plants/1")
        self.assertEqual(json.loads(response.data), {
           'name': "testPlant",
           'photo_url': "testPlant.png",
           'light': {
               'current': 53.0,
               'ideal': 50.0,
               'tolerance': 10.0,
           },
           'water': {
               'current': 63.0,
               'ideal': 57.0,
               'tolerance': 30.0,
           },
           'humidity': {
               'current': 0.2,
               'ideal': 0.2,
               'tolerance': 0.1,
           },
           'temperature': {
               'current': 18.0,
               'ideal': 11.2,
               'tolerance': 15.3,
           },
           'mature_on': 'Sun, 10 Jan 2016 00:00:00 GMT',
           'slot_id': 1,
           'plant_database_id': 1,
        })

    def test_show_returns_nothing_if_no_plant(self):
        response = self.app.get("/api/plants/1")
        self.assertEqual(json.loads(response.data), {})

    @mock.patch("app.webservice.models.PlantDatabase")
    def test_successful_create_returns_data(self, PlantDatabase):
        PlantDatabase.find_plant.return_value = build_plant()
        response = self.app.post("/api/plants", data={'plant_database_id': 1,
                                                      'slot_id': 1})
        self.assertEqual(json.loads(response.data), {
           'name': "testPlant",
           'photo_url': "testPlant.png",
           'light': {
               'current': 0.0,
               'ideal': 50.0,
               'tolerance': 10.0,
           },
           'water': {
               'current': 0.0,
               'ideal': 57.0,
               'tolerance': 30.0,
           },
           'humidity': {
               'current': 0.0,
               'ideal': 0.2,
               'tolerance': 0.1,
           },
           'temperature': {
               'current': 0.0,
               'ideal': 11.2,
               'tolerance': 15.3,
           },
           'mature_on': 'Sun, 10 Jan 2016 00:00:00 GMT',
           'slot_id': 1,
           'plant_database_id': 1,
        })

    @mock.patch("app.webservice.models.PlantDatabase")
    def test_successful_create_saves_plant(self, PlantDatabase):
        self.assertEqual(len(webservice.models.Plant), 0)
        PlantDatabase.find_plant.return_value = build_plant()
        self.app.post("/api/plants", data={'plant_database_id': 1,
                                           'slot_id': 1})
        self.assertEqual(len(webservice.models.Plant), 1)
        self.assertEqual(webservice.models.Plant.first().plant_database_id, 1)
        self.assertEqual(webservice.models.Plant.first().slot_id, 1)
        self.assertNotEqual(webservice.models.Plant.first().plant_setting, None)

    @mock.patch("app.webservice.models.PlantDatabase")
    def test_failed_create_does_not_save_plant(self, PlantDatabase):
        PlantDatabase.find_plant.return_value = None
        self.app.post("/api/plants", data={'plant_database_id': 1,
                                           'slot_id': 1})
        self.assertEqual(len(webservice.models.Plant), 0)

    @mock.patch("app.webservice.models.PlantDatabase")
    def test_failed_returns_error(self, PlantDatabase):
        PlantDatabase.find_plant.return_value = None
        response = self.app.post("/api/plants", data={'plant_database_id': 1,
                                                      'slot_id': 1})
        self.assertEqual(json.loads(response.data), {'error': 'could not save plant'})

    def test_delete_removes_plant(self):
        plant = build_plant()
        plant.save()
        response = self.app.delete("/api/plants/1")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(webservice.models.Plant), 0)

    def test_delete_with_no_plant_404(self):
        plant = build_plant()
        plant.save()
        response = self.app.delete("/api/plants/2")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(webservice.models.Plant), 1)

class TestAPIPlantSettingsController(unittest.TestCase):

    def setUp(self):
        # create a test client
        self.app = webservice.app.test_client()
        self.app.testing = True
        webservice.models.lazy_record.connect_db(TEST_DATABASE)
        with open(SCHEMA) as schema:
            webservice.models.lazy_record.load_schema(schema.read())
        self.plant = create_plant(slot_id=1)
        self.setting = webservice.models.PlantSetting.create(plant=self.plant)
        self.threshold = webservice.models.NotificationThreshold.create(
                             plant_setting=self.setting,
                             sensor_name="light",
                             deviation_percent=15,
                             deviation_time=3)

    def test_get_shows_existing_settings(self):
        response = self.app.get("/api/plants/1/settings")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {
            'settings': [
                {
                    'id': 1,
                    'sensor_name': "light",
                    'deviation_time': 3,
                    'deviation_percent': 15
                }
            ]
        })

    def test_get_shows_no_settings_if_none(self):
        self.threshold.destroy()
        response = self.app.get("/api/plants/1/settings")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {
            'settings': []
        })

    def test_get_shows_nothing_if_no_plant(self):
        self.plant.destroy()
        response = self.app.get("/api/plants/1/settings")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {
            'error': 'plant not found'
        })

    def test_post_creates_new_setting(self):
        response = self.app.post("/api/plants/1/settings", data={
            'sensor_name': 'light',
            'deviation_time': 5,
            'deviation_percent': 5,
            'row': 1
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {
            'id': 2,
            'row': 1,
            'sensor_name': 'light',
            'deviation_time': 5,
            'deviation_percent': 5
        })

    def test_create_returns_error_if_no_plant(self):
        self.plant.destroy()
        response = self.app.post("/api/plants/1/settings", data={
            'sensor_name': 'light',
            'deviation_time': 5,
            'deviation_percent': 5,
            'row': 1
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {
            'error': 'plant not found'
        })

    def test_update_edits_existing_settings(self):
        response = self.app.post("/api/plants/1/settings/1", data={
            'sensor_name': 'light',
            'deviation_time': 5,
            'deviation_percent': 50,
            'row': 1
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {
            'row': 1,
            'sensor_name': 'light',
            'deviation_time': 5,
            'deviation_percent': 50
        })
        self.assertEqual(
            webservice.models.NotificationThreshold.first().deviation_percent,
            50.0)

    def test_update_errors_if_no_setting(self):
        response = self.app.post("/api/plants/1/settings/2", data={
            'sensor_name': 'light',
            'deviation_time': 5,
            'deviation_percent': 5,
            'row': 1
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {
            'error': 'setting not found'
        })

    def test_update_errors_if_invalid(self):
        response = self.app.post("/api/plants/1/settings/1", data={
            'sensor_name': 'light',
            'deviation_time': 0,
            'deviation_percent': 5,
            'row': 1
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {
            'error': 'setting invalid'
        })

    def test_delete_deletes_setting(self):
        response = self.app.delete("/api/plants/1/settings/1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(webservice.models.NotificationThreshold), 0)

    def test_delete_error_if_no_setting(self):
        response = self.app.delete("/api/plants/1/settings/2")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(webservice.models.NotificationThreshold), 1)

class TestAPILogsController(unittest.TestCase):

    def setUp(self):
        # create a test client
        self.app = webservice.app.test_client()
        self.app.testing = True
        webservice.models.lazy_record.connect_db(TEST_DATABASE)
        with open(SCHEMA) as schema:
            webservice.models.lazy_record.load_schema(schema.read())
        self.plant = create_plant(slot_id=1)
        self.sensor_data = {
            "light": [10.0, 20.0, 30.0, 40.0],
            "water": [50.0, 60.0, 70.0, 80.0],
            "humidity": [0.1, 0.2, 0.3, 0.4],
            "temperature": [55.0, 65.0, 75.0, 85.0]
        }
        for sensor, vals in self.sensor_data.items():
            for val in vals:
                self.plant.record_sensor(sensor, val)

    def test_displays_sensor_data(self):
        response = self.app.get("/api/plants/1/logs")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data),
                         dict(id=1, **self.sensor_data))

    def test_displays_error_if_no_plant(self):
        self.plant.destroy()
        response = self.app.get("/api/plants/1/logs")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data),
                         {"error": "plant not found"})


@mock.patch("app.webservice.models.GlobalSetting")
class TestAPIGlobalSettingsController(unittest.TestCase):

    def setUp(self):
        # create a test client
        self.app = webservice.app.test_client()
        self.app.testing = True
        webservice.models.lazy_record.connect_db(TEST_DATABASE)
        with open(SCHEMA) as schema:
            webservice.models.lazy_record.load_schema(schema.read())

    def test_index_returns_current_settings(self, GlobalSetting):
        control = mock.Mock(name="control",
                            enabled=True,
                            id=1,
                            active=False,
                            active_start=time(0, 12, 30),
                            active_end=time(1, 11, 15))
        control.name = "fan"
        GlobalSetting.controls = [control]
        response = self.app.get("/api/settings")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {
            'fan': {
                'enabled': True,
                'id': 1,
                'active': False,
                'active_start': "00:12:30",
                'active_end': "01:11:15"
            }
        })

    def test_index_returns_with_always_active(self, GlobalSetting):
        control = mock.Mock(name="control",
                            id=1,
                            enabled=True,
                            active=False,
                            active_start=None,
                            active_end=None)
        control.name = "fan"
        GlobalSetting.controls = [control]
        response = self.app.get("/api/settings")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {
            'fan': {
                'enabled': True,
                'id': 1,
                'active': False,
                'active_start': None,
                'active_end': None
            }
        })

    def test_index_returns_with_temp_disabled(self, GlobalSetting):
        control = mock.Mock(name="control",
                            enabled=webservice.models.Control.TemporarilyDisabled,
                            id=1,
                            active=False,
                            active_start=time(0, 12, 30),
                            active_end=time(1, 11, 15))
        control.name = "fan"
        GlobalSetting.controls = [control]
        response = self.app.get("/api/settings")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {
            'fan': {
                'enabled': True,
                'id': 1,
                'active': False,
                'active_start': "00:12:30",
                'active_end': "01:11:15"
            }
        })

    def test_index_returns_with_disabled(self, GlobalSetting):
        control = mock.Mock(name="control",
                            enabled=False,
                            id=1,
                            active=False,
                            active_start=time(0, 12, 30),
                            active_end=time(1, 11, 15))
        control.name = "fan"
        GlobalSetting.controls = [control]
        response = self.app.get("/api/settings")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {
            'fan': {
                'enabled': False,
                'active': False,
                'id': 1,
                'active_start': "00:12:30",
                'active_end': "01:11:15"
            }
        })

    def test_update_edits_status(self, GlobalSetting):
        control = mock.Mock(name="control",
                            enabled=True,
                            id=1,
                            active=False,
                            active_start=time(0, 12, 30),
                            active_end=time(1, 11, 15))
        GlobalSetting.controls.find.return_value = control
        response = self.app.post("/api/settings/1", data={
            'enabled': False,
            'active': False,
            'active_start': "00:12:30",
            'active_end': "01:11:15"
        })
        self.assertEqual(response.status_code, 200)
        control.update.assert_called_with(enabled=False,
                                          active_start=time(0, 12, 30),
                                          active_end=time(1, 11, 15))
        control.save.assert_called_with()

    def test_errors_if_cannot_find_control(self, GlobalSetting):
        GlobalSetting.controls.find.side_effect = \
            webservice.models.lazy_record.RecordNotFound
        response = self.app.post("/api/settings/1", data={
            'enabled': False,
            'active': False,
            'active_start': "00:12:30",
            'active_end': "01:11:15"
        })
        self.assertEqual(response.status_code, 404)

    def test_update_edits_timestamp(self, GlobalSetting):
        control = mock.Mock(name="control",
                            enabled=True,
                            id=1,
                            active=False,
                            active_start=time(0, 12, 30),
                            active_end=time(1, 11, 15))
        GlobalSetting.controls.find.return_value = control
        response = self.app.post("/api/settings/1", data={
            'enabled': False,
            'active': False,
            'active_start': None,
            'active_end': None
        })
        self.assertEqual(response.status_code, 200)
        control.update.assert_called_with(enabled=False,
                                          active_start=None,
                                          active_end=None)
        control.save.assert_called_with()


@mock.patch("app.webservice.models.PlantDatabase")
class TestAPIDevicesController(unittest.TestCase):

    def setUp(self):
        # create a test client
        self.app = webservice.app.test_client()
        self.app.testing = True
        webservice.models.lazy_record.connect_db(TEST_DATABASE)
        with open(SCHEMA) as schema:
            webservice.models.lazy_record.load_schema(schema.read())

    def test_sends_device_id_to_plant_database(self, PlantDatabase):
        response = self.app.post("/api/devices",
                                 data={"device_id": "<DEVICE ID>"})
        self.assertEqual(response.status_code, 200)
        PlantDatabase.add_device.assert_called_with("DEVICEID")


class TestAPINotificationSettingsController(unittest.TestCase):

    def setUp(self):
        # create a test client
        self.app = webservice.app.test_client()
        self.app.testing = True
        webservice.models.lazy_record.connect_db(TEST_DATABASE)
        with open(SCHEMA) as schema:
            webservice.models.lazy_record.load_schema(schema.read())

    @mock.patch("app.webservice.models.PlantDatabase")
    def test_gets_settings_from_plant_database(self, PlantDatabase):
        PlantDatabase.get_notification_settings.return_value = {'email': True,
                                                                'push': False}
        response = self.app.get("/api/notification_settings")
        self.assertEqual(response.status_code, 200)
        PlantDatabase.get_notification_settings.assert_called_with()
        self.assertEqual(json.loads(response.data),
                         {'email': True, 'push': False})

    @mock.patch(
        "app.webservice.models.PlantDatabase.get_notification_settings")
    def test_gets_settings_404s_on_error(self, get_notification_settings):
        get_notification_settings.side_effect = \
            webservice.models.PlantDatabase.CannotConnect
        response = self.app.get("/api/notification_settings")
        self.assertEqual(response.status_code, 404)

    @mock.patch("app.webservice.models.PlantDatabase")
    def test_sends_settings_to_plant_database(self, PlantDatabase):
        response = self.app.post("/api/notification_settings",
                                 data={"email": True, "push": False})
        self.assertEqual(response.status_code, 200)
        PlantDatabase.update_notification_settings.assert_called_with(
            {"email": True, "push": False})


def build_plant(slot_id=1):
    return webservice.models.Plant(name="testPlant",
                                   photo_url="testPlant.png",
                                   water_ideal=57.0,
                                   water_tolerance=30.0,
                                   light_ideal=50.0,
                                   light_tolerance=10.0,
                                   humidity_ideal=0.2,
                                   humidity_tolerance=0.1,
                                   temperature_ideal=11.2,
                                   temperature_tolerance=15.3,
                                   mature_on=dt(2016, 1, 10),
                                   slot_id=slot_id,
                                   plant_database_id=1)

def create_plant(slot_id=1):
    plant = build_plant(slot_id)
    plant.save()
    return plant

if __name__ == '__main__':
    unittest.main()
