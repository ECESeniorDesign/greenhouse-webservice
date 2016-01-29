import unittest
import mock
import os
import sys
from datetime import datetime as dt
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import app.presenters as presenters

class TestPlantPresenter(unittest.TestCase):

    def test_light_bar_width_within_tolerance(self):
        presenter = presenters.PlantPresenter(plant())
        self.assertEqual(presenter.bar_width("light"), 56.0)
        self.assertEqual(presenter.error_bar_width("light"), 0.0)
        self.assertEqual(presenter.within_tolerance("light"), True)

    def test_light_bar_width_above_tolerance(self):
        presenter = presenters.PlantPresenter(plant(light=80.0))
        self.assertEqual(presenter.bar_width("light"), 60.0)
        self.assertEqual(presenter.error_bar_width("light"), 20.0)
        self.assertEqual(presenter.within_tolerance("light"), False)

    def test_light_bar_width_far_above_tolerance(self):
        presenter = presenters.PlantPresenter(plant(light=180.0))
        self.assertEqual(presenter.bar_width("light"), 60.0)
        self.assertEqual(presenter.error_bar_width("light"), 40.0)
        self.assertEqual(presenter.within_tolerance("light"), False)

    def test_light_bar_width_below_tolerance(self):
        presenter = presenters.PlantPresenter(plant(light=30.0))
        self.assertEqual(presenter.bar_width("light"), 30.0)
        self.assertEqual(presenter.error_bar_width("light"), 10.0)
        self.assertEqual(presenter.within_tolerance("light"), False)

    def test_water_bar_width_within_tolerance(self):
        presenter = presenters.PlantPresenter(plant(water=120.0))
        self.assertEqual(presenter.bar_width("water"), 60.0)
        self.assertEqual(presenter.error_bar_width("water"), 0.0)
        self.assertEqual(presenter.within_tolerance("water"), True)

    def test_water_bar_width_above_tolerance(self):
        presenter = presenters.PlantPresenter(plant(water=140.0))
        self.assertEqual(presenter.bar_width("water"), 65.0)
        self.assertEqual(presenter.error_bar_width("water"), 5.0)
        self.assertEqual(presenter.within_tolerance("water"), False)

    def test_water_bar_width_far_above_tolerance(self):
        presenter = presenters.PlantPresenter(plant(water=210.0))
        self.assertEqual(presenter.bar_width("water"), 65.0)
        self.assertEqual(presenter.error_bar_width("water"), 35.0)
        self.assertEqual(presenter.within_tolerance("water"), False)

    def test_water_bar_width_below_tolerance(self):
        presenter = presenters.PlantPresenter(plant(water=30.0))
        self.assertEqual(presenter.bar_width("water"), 15.0)
        self.assertEqual(presenter.error_bar_width("water"), 20.0)
        self.assertEqual(presenter.within_tolerance("water"), False)

    def test_icons(self):
        presenter = presenters.PlantPresenter(plant())
        self.assertEqual(presenter.icon_for("light"), "fa fa-sun-o")
        self.assertEqual(presenter.icon_for("water"), "wi wi-raindrop")
        self.assertEqual(presenter.icon_for("humidity"), "")

    def test_bar_class(self):
        presenter = presenters.PlantPresenter(plant())
        self.assertEqual(presenter.bar_class("light"), "progress-bar-sun")
        self.assertEqual(presenter.bar_class("water"), "progress-bar-water")

    def test_formats_humidity_to_percentage(self):
        presenter = presenters.PlantPresenter(plant())
        self.assertEqual(presenter.formatted_value("humidity"), "27.0%")

    def test_delegates_to_plant_for_other_attributes(self):
        presenter = presenters.PlantPresenter(plant())
        self.assertEqual(presenter.slot_id, 1)

    @mock.patch("app.presenters.datetime")
    def test_gets_maturity_dial_data(self, datetime):
        datetime.datetime.return_value = dt(2016, 1, 2)
        presenter = presenters.PlantPresenter(plant())
        self.assertEqual(presenter.maturity_dial_min, 7)
        self.assertEqual(presenter.maturity_dial_max, 16)

    def test_over_ideal_when_over(self):
        presenter = presenters.PlantPresenter(plant(water=110.0))
        self.assertTrue(presenter.over_ideal("water"))

    def test_over_ideal_when_under(self):
        presenter = presenters.PlantPresenter(plant(water=90.0))
        self.assertFalse(presenter.over_ideal("water"))

@mock.patch("app.presenters.models.Plant")
class TestChartDataPresenter(unittest.TestCase):

    def test_formats_and_filters_history_chart_data(self, Plant):
        data = [1.2, 3.6, 12.0, 65.0, 11.0, 3.2, 6.7, 15.2, 88.5]
        p = plant(sensor_data_points=mock.Mock(light=mock.Mock(
            return_value=[mock.Mock(sensor_value=v)
                          for v in data])))
        presenter = presenters.ChartDataPresenter(p)
        self.assertEqual(presenter.history_chart_data(), {
            "labels": ["", "", "", "", "", "", "", ""],
            "datasets": [{
                            'fillColor': "rgba(220,220,220,0.2)",
                            'strokeColor': "rgba(220,220,220,1)",
                            'pointColor': "rgba(220,220,220,1)",
                            'pointStrokeColor': "#fff",
                            'data': [3.6, 12.0, 65.0, 11.0,
                                     3.2, 6.7, 15.2, 88.5],
                        }]
        })

    def test_formats_ideal_chart_data(self, Plant):
        # Note: mocking queries is awful
        p = plant(sensor_data_points=mock.Mock(light=mock.Mock(
            return_value=mock.Mock(where=mock.Mock(
            return_value=mock.Mock(__len__=mock.Mock(
            return_value=15))), __len__=mock.Mock(
            return_value=19)))))
        presenter = presenters.ChartDataPresenter(p)
        self.assertEqual(presenter.ideal_chart_data(), [{
                "label": "Out of Tolerance",
                "value": 4,
                "color":"#F7464A",
                "highlight": "#FF5A5E",
            },
            {
                "label": "Ideal",
                "value": 15,
                "color": "#46BFBD",
                "highlight": "#5AD3D1",
            }])

def plant(**kwargs):
    p = mock.Mock(photo_url="testPlant.png",
                  water=80.0,
                  water_ideal=100.0,
                  water_tolerance=30.0,
                  light=56.0,
                  light_ideal=50.0,
                  light_tolerance=10.0,
                  acidity=9.2,
                  acidity_ideal=9.0,
                  acidity_tolerance=1.0,
                  humidity=0.27,
                  humidity_ideal=0.2,
                  humidity_tolerance=0.1,
                  mature_on=dt(2016, 1, 10),
                  created_at=dt(2016, 1, 1),
                  updated_at=dt(2016, 1, 1),
                  mature_in=8,
                  slot_id=1,
                  plant_database_id=1)
    p.name = "testPlant"
    for k, v in kwargs.items():
        setattr(p, k, v)
    return p

if __name__ == '__main__':
    unittest.main()
