import unittest
import mock
import os
import sys
from datetime import datetime as dt
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
    def test_renders_home_page_with_plants(self, render_template):
        self.app.get('/')
        render_template.assert_called_with("plants/index.html",
                                           plants=[(None, 1), (None, 2)])

    def test_plants_index_status_code(self):
        result = self.app.get('/plants')
        self.assertEqual(result.status_code, 200)

    @mock.patch("app.webservice.flask.render_template")
    def test_renders_plants_index_with_plants(self, render_template):
        self.app.get('/plants')
        render_template.assert_called_with("plants/index.html",
                                           plants=[(None, 1), (None, 2)])
    
    @mock.patch("app.webservice.models.PlantDatabase")
    def test_plants_new_status_code(self, PlantDatabase):
        plant = mock.Mock(name="plant")
        PlantDatabase.all_plants.return_value = [plant]
        result = self.app.get('/plants/new?slot_id=2')
        self.assertEqual(result.status_code, 200)

    @mock.patch("app.webservice.models.PlantDatabase")
    @mock.patch("app.webservice.flask.render_template")
    def test_renders_plants_new_with_plants(self, render_template,
                                            PlantDatabase):
        plant = mock.Mock(name="plant")
        PlantDatabase.all_plants.return_value = [plant]
        self.app.get('/plants/new?slot_id=2')
        render_template.assert_called_with("plants/new.html",
                                           plants=[plant],
                                           slot_id=2)

    @mock.patch("app.webservice.models.PlantDatabase.all_plants")
    def test_plants_new_redirects_on_connection_failure(self, all_plants):
        all_plants.side_effect = webservice.models.PlantDatabase.CannotConnect
        result = self.app.get("/plants/new?slot_id=1")
        self.assertEqual(result.status_code, 302)
        self.assertEqual(result.headers['Location'], 'http://localhost/plants')

    @mock.patch("app.webservice.models.PlantDatabase")
    def test_plants_create_redirects_to_show(self, PlantDatabase):
        PlantDatabase.find_plant.return_value = self.build_plant()
        result = self.app.post("/plants", data=dict(
            plant_database_id=1,
            slot_id=1
        ))
        self.assertEqual(result.status_code, 302)
        self.assertEqual(result.headers['Location'], 'http://localhost/plants/1')

    @mock.patch("app.webservice.models.PlantDatabase")
    def test_plants_create_saves_plant(self, PlantDatabase):
        plant = self.build_plant(slot_id=None)
        PlantDatabase.find_plant.return_value = plant
        result = self.app.post("/plants", data=dict(
            plant_database_id=1,
            slot_id=1
        ))
        self.assertEqual(plant.slot_id, 1)
        self.assertEqual(plant.id, 1)

    @mock.patch("app.webservice.models.PlantDatabase")
    def test_plants_create_redirects_to_index_on_failure(self, PlantDatabase):
        self.create_plant(slot_id=1)
        PlantDatabase.find_plant.return_value = self.build_plant(slot_id=1)
        result = self.app.post("/plants", data=dict(
            plant_database_id=1,
            slot_id=1
        ))
        self.assertEqual(result.status_code, 302)
        self.assertEqual(result.headers['Location'], 'http://localhost/plants')

    @mock.patch("app.webservice.models.PlantDatabase")
    def test_plants_create_redirects_to_index_if_no_plant(self, PlantDatabase):
        PlantDatabase.find_plant.return_value = None
        result = self.app.post("/plants", data=dict(
            plant_database_id=1,
            slot_id=1
        ))
        self.assertEqual(result.status_code, 302)
        self.assertEqual(result.headers['Location'], 'http://localhost/plants')

    def test_plants_show_status_code(self):
        self.create_plant(slot_id=1)
        result = self.app.get('/plants/1')
        self.assertEqual(result.status_code, 200)

    @mock.patch("app.webservice.flask.render_template")
    def test_renders_plants_show_with_plant(self, render_template):
        plant = self.create_plant(slot_id=1)
        self.app.get('/plants/1')
        render_template.assert_called_with("plants/show.html",
                                           plant=plant)

    def test_show_redirects_to_index_when_plant_does_not_exist(self):
        response = self.app.get('/plants/1')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], 'http://localhost/plants')

    def test_destroy_status_code(self):
        self.create_plant(slot_id=1)
        response = self.app.delete('/plants/1')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], 'http://localhost/plants')

    def test_destroy_deletes_plant(self):
        self.create_plant(slot_id=1)
        response = self.app.delete('/plants/1')
        self.assertEqual(len(webservice.models.Plant.all()), 0)

    def test_destory_redirects_to_index_on_lookup_failure(self):
        response = self.app.delete('/plants/1')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], 'http://localhost/plants')

    def build_plant(self, slot_id=1):
        return webservice.models.Plant(name="testPlant",
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
                                       slot_id=slot_id,
                                       plant_database_id=1)

    def create_plant(self, slot_id=1):
        plant = self.build_plant(slot_id)
        plant.save()
        return plant

if __name__ == '__main__':
    unittest.main()
