import unittest
import calc
import os
from footballdatabase_eu_scrapper import *

class TestCalc(unittest.TestCase):

    def setUp(self):
        data1 = ('2022-10-03', 'TU Ambato', 'Deportivo Cuenca')
        data2 = ('2022-10-03', 'Ruvu Shooting', 'Young Africans')
        data3 = ('2018-10-18', 'Moqaouloun', 'Wadi Degla')
        data4 = ('2022-11-10', 'Hellas Verona', 'Juventus')

    def test_session_init(self):
        driver, session = initialize_session_footballdatabase()
        self.assertIsNotNone(driver)
        self.assertIsNotNone(session)

    def test_get_cookies(self):
        cookies = get_cookies('cookies_data/cookies.csv')
        self.assertIsNotNone(cookies)

    def test_get_game_id_and_href(self):
        data1 = ('2022-10-03', 'TU Ambato', 'Deportivo Cuenca')
        data2 = ('2022-10-03', 'Ruvu Shooting', 'Young Africans')
        data3 = ('2018-10-18', 'Moqaouloun', 'Wadi Degla')
        data4 = ('2022-11-10', 'Hellas Verona', 'Juventus')
        session, driver = initialize_session_footballdatabase()
        session, driver = initialize_login_session(session, driver)


        href_1 = get_game_id_and_href(data1,session, driver)
        href_2 = get_game_id_and_href(data2,session, driver)
        href_3 = get_game_id_and_href(data3,session, driver)
        href_4 = get_game_id_and_href(data4,session, driver)

        self.assertEqual(href_1, 'https://www.footballdatabase.eu/en/match/overview/2348893')
        self.assertEqual(href_2, 'https://www.footballdatabase.eu/en/match/overview/2484134')
        self.assertEqual(href_3, 'https://www.footballdatabase.eu/en/match/overview/1762731')
        self.assertEqual(href_4, 'https://www.footballdatabase.eu/en/match/overview/2418737')


    def test_save_to_JSON(self):
        data1 = ('2022-10-03', 'TU Ambato', 'Deportivo Cuenca')
        data2 = ('2022-10-03', 'Ruvu Shooting', 'Young Africans')
        data3 = ('2018-10-18', 'Moqaouloun', 'Wadi Degla')
        data4 = ('2022-11-10', 'Hellas Verona', 'Juventus')

        date, team1, team2 = get_data_from_GUI(data1[0], data1[1], data1[2])
        match_date_string = str(date) + '_' + str(team1).replace('_', '') + '_' + str(team2).replace('_', '')
        path = os.path.join('matches', match_date_string, 'scrapped_data.json')
        self.assertTrue(os.path.exists(path))

        date, team1, team2 = get_data_from_GUI(data2[0], data2[1], data2[2])
        match_date_string = str(date) + '_' + str(team1).replace('_', '') + '_' + str(team2).replace('_', '')
        path = os.path.join('matches', match_date_string, 'scrapped_data.json')
        self.assertTrue(os.path.exists(path))

        date, team1, team2 = get_data_from_GUI(data3[0], data3[1], data3[2])
        match_date_string = str(date) + '_' + str(team1).replace('_', '') + '_' + str(team2).replace('_', '')
        path = os.path.join('matches', match_date_string, 'scrapped_data.json')
        self.assertTrue(os.path.exists(path))

        date, team1, team2 = get_data_from_GUI(data4[0], data4[1], data4[2])
        match_date_string = str(date) + '_' + str(team1).replace('_', '') + '_' + str(team2).replace('_', '')
        path = os.path.join('matches', match_date_string, 'scrapped_data.json')
        self.assertTrue(os.path.exists(path))