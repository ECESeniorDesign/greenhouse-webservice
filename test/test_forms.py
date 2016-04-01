import unittest
import mock
import os
import sys
from datetime import time
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import app.forms as forms

class TestGlobalSettingsForm(unittest.TestCase):

    def setUp(self):
        self.controls = [mock.Mock(name="control1", id=1),
                         mock.Mock(name="control2", id=2)]
        self.form_data = {'active_start': ['02:00 PM', ''],
                          'enabled': ['2', '1'],
                          'id': ['2', '1'],
                          'active_end': ['01:30 AM', ''],
                          'push': 'on',
                          'notify_plants': 'on'}
        form_data = FormDataStub(self.form_data)
        self.form = forms.GlobalSettingsForm(self.controls, form_data)

    def test_parses_form_data(self):
        self.assertEqual(self.form.data, {
            self.controls[0]: {
                'enabled': True,
                'active_start': None,
                'active_end': None
            },
            self.controls[1]: {
                'enabled': True,
                'active_start': time(14, 0),
                'active_end': time(1, 30)
            },
            'notifications': {
                'push': True,
                'email': False
            },
            'global_settings': {
                'notify_plants': True,
                'notify_maintenance': False
            }
        })

    def test_parses_form_data_with_disabled(self):
        # Unchecked checkboxes give nothing back at all
        self.form_data['enabled'] = ['2']
        self.form_data['active_start'] = ['02:00 PM']
        self.form_data['active_end'] = ['01:30 AM']
        self.assertEqual(self.form.data, {
            self.controls[0]: {
                'enabled': False,
                'active_start': None,
                'active_end': None
            },
            self.controls[1]: {
                'enabled': True,
                'active_start': time(14, 0),
                'active_end': time(1, 30)
            },
            'notifications': {
                'push': True,
                'email': False
            },
            'global_settings': {
                'notify_plants': True,
                'notify_maintenance': False
            }
        })

    def test_parses_form_data_with_12AM(self):
        # Unchecked checkboxes give nothing back at all
        self.form_data['active_end'] = ['12:00 AM', '']
        self.assertEqual(self.form.data, {
            self.controls[0]: {
                'enabled': True,
                'active_start': None,
                'active_end': None
            },
            self.controls[1]: {
                'enabled': True,
                'active_start': time(14, 0),
                'active_end': time(0, 0)
            },
            'notifications': {
                'push': True,
                'email': False
            },
            'global_settings': {
                'notify_plants': True,
                'notify_maintenance': False
            }
        })

    @mock.patch("app.forms.models.GlobalSetting")
    @mock.patch("app.forms.models.PlantDatabase")
    def test_submit_saves_form(self, PlantDatabase, GS):
        self.form_data['enabled'] = ['2']
        self.form_data['active_start'] = ['02:00 PM']
        self.form_data['active_end'] = ['01:30 AM']
        self.form.submit()
        self.controls[0].update.assert_called_with(active_start=None,
                                                   active_end=None,
                                                   enabled=False)
        self.controls[1].update.assert_called_with(active_start=time(14, 0),
                                                   active_end=time(1, 30),
                                                   enabled=True)
        self.controls[0].save.assert_called_with()
        self.controls[1].save.assert_called_with()

    @mock.patch("app.forms.models.GlobalSetting")
    @mock.patch("app.forms.models.PlantDatabase")
    def test_submit_updates_notification_settings(self, PlantDatabase, GS):
        self.form.submit()
        PlantDatabase.update_notification_settings.assert_called_with({
            'push': True,
            'email': False
        })

    @mock.patch("app.forms.models.GlobalSetting")
    @mock.patch("app.forms.models.PlantDatabase")
    def test_submit_updates_global_settings(self, PD, GlobalSetting):
        self.form.submit()
        self.assertEqual(GlobalSetting.notify_plants, True)
        self.assertEqual(GlobalSetting.notify_maintenance, False)

class FormDataStub(object):
    def __init__(self, data):
        self.data = data

    def getlist(self, arg):
        return self.data[arg]

    def __getitem__(self, key):
        return self.data[key]

    def get(self, key, default=None):
        return self.data.get(key, default)

if __name__ == '__main__':
    unittest.main()
