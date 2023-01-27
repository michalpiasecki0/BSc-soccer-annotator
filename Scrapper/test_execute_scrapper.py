import os.path
import unittest
import calc
from execute_scrapper import run_script
from os.path import exists
from footballdatabase_eu_scrapper import get_data_from_GUI

class TestCalc(unittest.TestCase):

    def test_get_matches(self):
        matches = []
        matches.append(('2022-10-03', 'Leicester', 'Nottingham'))
        matches.append(('2022-10-03', 'TU Ambato', 'Deportivo Cuenca'))
        matches.append(('2022-10-03', 'Nacional', '12 de Octubre'))
        matches.append(('2022-10-03', 'Cukaricki', 'Radnicki Nis'))
        matches.append(('2022-10-03', 'Ruvu Shooting', 'Young Africans'))
        matches.append(('2018-10-18', 'Real Salt Lake', 'New England'))
        matches.append(('2018-10-18', 'Moqaouloun', 'Wadi Degla'))
        matches.append(('2018-10-18', 'Sertanense', 'Benfica'))
        matches.append(('2018-10-18', 'Zamora Barinas', 'Estudiantes'))
        matches.append(('2018-08-10', 'Gamba Osaka', 'FC Tokyo'))
        matches.append(('2018-08-10', 'Nancy', 'Lens'))
        matches.append(('2018-08-10', 'Wisla Krakow', 'Wisla Plock'))
        matches.append(('2016-08-16', 'Dinamo Zagreb', 'Salzburg'))
        matches.append(('2016-08-16', 'Bnei Sakhnin', 'Kfar Saba'))
        matches.append(('2016-08-16', 'Rosina', 'Senica'))
        matches.append(('2022-11-10', 'Hellas Verona', 'Juventus'))

        for match in matches:
            run_script(match[0], match[1], match[2])
            date, team1, team2 = get_data_from_GUI(match[0], match[1], match[2])
            match_date_string = str(date) + '_' + str(team1).replace('_', '') + '_' + str(team2).replace('_', '')
            path = os.path.join('matches', match_date_string, 'scrapped_data.json')
            self.assertTrue(os.path.exists(path))


