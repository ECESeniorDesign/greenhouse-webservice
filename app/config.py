import os

DATABASE = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                        "greenhouse-webservice.db")
TEST_DATABASE = ":memory:"
SCHEMA = os.path.join(os.path.dirname(__file__), "schema.sql")
DEBUG = True
SECRET_KEY = "development key"
PORT = 5000
PLANT_DATABASE = "greenhouse.conklins.net"
NUMBER_OF_PLANTS = 2
