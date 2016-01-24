import unittest
import mock
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import app.webservice as webservice
from app.config import TEST_DATABASE, SCHEMA

class TestRouting(unittest.TestCase):

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

if __name__ == '__main__':
    unittest.main()
