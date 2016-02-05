import os

DATABASE = "/tmp/greenhouse-webservice.db"
TEST_DATABASE = ":memory:"
SCHEMA = os.path.join(os.path.dirname(__file__), "schema.sql")
DEBUG = True
SECRET_KEY = "development key"
USERNAME = "admin"
PASSWORD = "password"
PLANT_DATABASE = "localhost:4000"
NUMBER_OF_PLANTS = 2
