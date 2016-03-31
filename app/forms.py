from datetime import time
import models

class GlobalSettingsForm(object):

    def __init__(self, controls, form_data):
        self.controls = controls
        self.form_data = form_data

    @property
    def data(self):
        def to_bool(onoff):
            return onoff == "on"
        controls = {control: self._data_for(control.id)
                    for control in self.controls}
        return dict(controls, notifications={
            'push': to_bool(self.form_data.get("push")),
            'email': to_bool(self.form_data.get("email"))})

    def submit(self):
        for control, data in self.data.items():
            if control == "notifications":
                models.PlantDatabase.update_notification_settings(data)
            else:
                control.update(**data)
                control.save()

    def _data_for(self, control_id):
        enabled = map(int, self.form_data.getlist('enabled'))
        active_starts = self.form_data.getlist('active_start')
        active_ends = self.form_data.getlist('active_end')
        data = zip(active_starts, active_ends, enabled)
        as_val, ae_val = next(((astart, aend)
                              for astart, aend, id in data
                              if int(id) == control_id), ('', ''))
        active_start = self._parse_timestamp(as_val)
        active_end = self._parse_timestamp(ae_val)
        return {
            'active_start': active_start,
            'active_end': active_end,
            'enabled': control_id in enabled
        }

    def _parse_timestamp(self, timestamp):
        if timestamp == '':
            return None
        tp, ampm = timestamp.split(" ")
        hours, minutes = map(int, tp.split(":"))
        if ampm == "PM":
            hours += 12
        elif ampm == "AM" and hours == 12:
            hours = 0
        return time(hours, minutes)
