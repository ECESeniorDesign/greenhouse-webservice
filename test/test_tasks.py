import unittest
import mock
import os
import sys
from datetime import datetime as dt
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import app.webservice as webservice


@mock.patch("app.webservice.socketio")
class TestBackgroundTasks(unittest.TestCase):

    def test_sends_data_update(self, socketio):
        webservice.load_sensor_data()
        socketio.emit.assert_called_with('data-update',
                                         True,
                                         namespace="/plants")


if __name__ == '__main__':
    unittest.main()
