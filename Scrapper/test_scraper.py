import unittest
import calc
import os
from footballdatabase_eu_scrapper import *
import time
import statistics
import logging

class TestCalc(unittest.TestCase):

    def setUp(self):
        '''
        Prepares data to be tested in the scrapper.
        '''
        Testing_data = []
        Testing_data.append(('2022-10-03', 'TU Ambato', 'Deportivo Cuenca'))
        Testing_data.append(('2022-10-03', 'Ruvu Shooting', 'Young Africans'))
        Testing_data.append(('2018-10-18', 'Moqaouloun', 'Wadi Degla'))
        Testing_data.append(('2022-11-10', 'Hellas Verona', 'Juventus'))
        Testing_data.append(('2010-05-05', 'Sibenik', 'Hajduk Split'))
        Testing_data.append(('2010-05-05', 'Colorado Rapids', 'LA Galaxy'))
        Testing_data.append(('2006-05-10', 'Grays Athletic', 'Halifax Town'))
        Testing_data.append(('2006-05-10', 'Wisla Krakow', 'Arka Gdynia'))
        Testing_data.append(('2006-05-10', 'Zaglebie Lubin', 'Groclin'))
        Testing_data.append(('2004-08-10', 'Juventus', 'Djurgaardens IF'))
        Testing_data.append(('2004-08-10', 'Minnesota', 'Vancouver'))
        Testing_data.append(('2021-10-06', 'Italy', 'Spain'))
        Testing_data.append(('2022-12-13', 'Argentina', 'Croatia'))
        Testing_data.append(('2022-11-20', 'Qatar', 'Ecuador'))
        Testing_data.append(('2022-11-21', 'Senegal', 'Netherlands'))
        Testing_data.append(('2018-07-04', 'Minnesota United', 'Toronto FC'))
        Testing_data.append(('2018-07-04', 'LA Galaxy', 'D.C. United'))
        Testing_data.append(('2018-07-04', 'Nth Carolina', 'Red Stars Fém.'))
        Testing_data.append(('2019-10-10', 'Guinea-Bissau', 'São Tomé'))
        Testing_data.append(('2019-10-10', 'Belarus U-21', 'Portugal U-21'))
        Testing_data.append(('2010-05-05', 'Nice', 'Bordeaux'))
        Testing_data.append(('2023-01-01', 'Blackpool', 'Sunderland'))
        Testing_data.append(('2023-01-01', 'Nantes', 'Auxerre'))
        Testing_data.append(('2023-01-01', 'Nottingham', 'Chelsea'))

        #data1 = ('2022-10-03', 'TU Ambato', 'Deportivo Cuenca')
        #data2 = ('2022-10-03', 'Ruvu Shooting', 'Young Africans')
        #data3 = ('2018-10-18', 'Moqaouloun', 'Wadi Degla')
        #data4 = ('2022-11-10', 'Hellas Verona', 'Juventus')

    def test_session_init(self):
        '''
        Test whether the initialization of the session is correct.
        '''
        driver, session = initialize_session_footballdatabase("cookies_data/cookies.csv")
        self.assertIsNotNone(driver)
        self.assertIsNotNone(session)

    def test_get_cookies(self):
        '''
        Test whether cookies have been inserted properly.
        '''
        cookies = get_cookies('cookies_data/cookies.csv')
        self.assertIsNotNone(cookies)

    def test_get_game_id_and_href(self):
        '''
        Tests whether the correct reference links have been obtained to the scrapper.
        '''
        hrefs = []
        Testing_data = []
        Testing_data.append(('2022-10-03', 'TU Ambato', 'Deportivo Cuenca'))
        Testing_data.append(('2022-10-03', 'Ruvu Shooting', 'Young Africans'))
        Testing_data.append(('2018-10-18', 'Moqaouloun', 'Wadi Degla'))
        Testing_data.append(('2022-11-10', 'Hellas Verona', 'Juventus'))
        Testing_data.append(('2010-05-05', 'Sibenik', 'Hajduk Split'))
        Testing_data.append(('2010-05-05', 'Colorado Rapids', 'LA Galaxy'))
        Testing_data.append(('2006-05-10', 'Grays Athletic', 'Halifax Town'))
        Testing_data.append(('2006-05-10', 'Wisla Krakow', 'Arka Gdynia'))
        Testing_data.append(('2006-05-10', 'Zaglebie Lubin', 'Groclin'))
        Testing_data.append(('2004-08-10', 'Juventus', 'Djurgaardens IF'))
        Testing_data.append(('2004-08-10', 'Minnesota', 'Vancouver'))
        Testing_data.append(('2021-10-06', 'Italy', 'Spain'))
        Testing_data.append(('2022-12-13', 'Argentina', 'Croatia'))
        Testing_data.append(('2022-11-20', 'Qatar', 'Ecuador'))
        Testing_data.append(('2022-11-21', 'Senegal', 'Netherlands'))
        Testing_data.append(('2018-07-04', 'Minnesota United', 'Toronto FC'))
        Testing_data.append(('2018-07-04', 'LA Galaxy', 'D.C. United'))
        Testing_data.append(('2018-07-04', 'Nth Carolina', 'Red Stars Fém.'))
        Testing_data.append(('2010-05-05', 'Nice', 'Bordeaux'))
        Testing_data.append(('2023-01-01', 'Blackpool', 'Sunderland'))
        Testing_data.append(('2023-01-01', 'Nantes', 'Auxerre'))
        Testing_data.append(('2023-01-01', 'Nottingham', 'Chelsea'))

        hrefs.append('https://www.footballdatabase.eu/en/match/overview/2348893')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/2484134')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/1762731')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/2418737')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/1151060')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/534635')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/1135166')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/195821')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/195825')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/1027437')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/1817455')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/2132991')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/2534910')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/2382851')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/2382852')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/1690000')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/1690004')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/1977565')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/470611')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/2415143')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/2406612')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/2402681')

        session, driver = initialize_session_footballdatabase("cookies_data/cookies.csv")
        session, driver = initialize_login_session(driver, session, "cookies_data/cookies.csv")

        times_arr = []

        for href, data in zip(hrefs, Testing_data):
            data_transformed = get_data_from_GUI(data[0], data[1], data[2])
            print(data_transformed)
            t1 = time.time()
            self.assertEqual(get_game_id_and_href(data_transformed, session, driver)[1], href)
            t2 = time.time()
            times_arr.append(t2-t1)
            print(f"Search time : {t2-t1}")
        print(f"Average search time: {statistics.mean(times_arr)} for {len(times_arr)} observations")
        print(f"Standard deviation for search time: {statistics.stdev(times_arr)} for {len(times_arr)} observations")

    def test_save_to_JSON(self):
        Testing_data = []
        Testing_data.append(('2022-10-03', 'TU Ambato', 'Deportivo Cuenca'))
        Testing_data.append(('2022-10-03', 'Ruvu Shooting', 'Young Africans'))
        Testing_data.append(('2018-10-18', 'Moqaouloun', 'Wadi Degla'))
        Testing_data.append(('2022-11-10', 'Hellas Verona', 'Juventus'))
        Testing_data.append(('2010-05-05', 'Sibenik', 'Hajduk Split'))
        Testing_data.append(('2010-05-05', 'Colorado Rapids', 'LA Galaxy'))
        Testing_data.append(('2006-05-10', 'Grays Athletic', 'Halifax Town'))
        Testing_data.append(('2006-05-10', 'Wisla Krakow', 'Arka Gdynia'))
        Testing_data.append(('2006-05-10', 'Zaglebie Lubin', 'Groclin'))
        Testing_data.append(('2004-08-10', 'Juventus', 'Djurgaardens IF'))
        Testing_data.append(('2004-08-10', 'Minnesota', 'Vancouver'))
        Testing_data.append(('2021-10-06', 'Italy', 'Spain'))
        Testing_data.append(('2022-12-13', 'Argentina', 'Croatia'))
        Testing_data.append(('2022-11-20', 'Qatar', 'Ecuador'))
        Testing_data.append(('2022-11-21', 'Senegal', 'Netherlands'))
        Testing_data.append(('2018-07-04', 'Minnesota United', 'Toronto FC'))
        Testing_data.append(('2018-07-04', 'LA Galaxy', 'D.C. United'))
        Testing_data.append(('2018-07-04', 'Nth Carolina', 'Red Stars Fém.'))
        Testing_data.append(('2019-10-10', 'Guinea-Bissau', 'São Tomé'))
        Testing_data.append(('2019-10-10', 'Belarus U-21', 'Portugal U-21'))
        Testing_data.append(('2010-05-05', 'Nice', 'Bordeaux'))
        Testing_data.append(('2023-01-01', 'Blackpool', 'Sunderland'))
        Testing_data.append(('2023-01-01', 'Nantes', 'Auxerre'))
        Testing_data.append(('2023-01-01', 'Nottingham', 'Chelsea'))
        times_arr = []

        for data in Testing_data:
            date, team1, team2 = get_data_from_GUI(data[0], data[1], data[2])
            match_date_string = str(date) + '_' + str(team1).replace('_', '') + '_' + str(team2).replace('_', '')
            path = os.path.join('matches', match_date_string, 'scrapped_data.json')
            #Save with empty data
            t1 = time.time()
            save_to_JSON({},match_date_string)
            t2 = time.time()
            times_arr.append(t2 - t1)
            print(f"Saving time : {t2 - t1}")
            self.assertTrue(os.path.exists(path))
        print(f"Average save time: {statistics.mean(times_arr)} for {len(times_arr)} observations")
        print(f"Standard deviation for save time: {statistics.stdev(times_arr)} for {len(times_arr)} observations")

    def test_get_data_from_link(self):
        hrefs = []
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/2348893')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/2484134')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/1762731')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/2418737')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/1151060')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/534635')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/1135166')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/195821')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/195825')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/1027437')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/1817455')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/2132991')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/2534910')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/2382851')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/2382852')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/1690000')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/1690004')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/1977565')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/1898673')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/1831461')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/470611')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/2415143')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/2406612')
        hrefs.append('https://www.footballdatabase.eu/en/match/overview/2402681')

        times_arr = []
        session, driver = initialize_session_footballdatabase("cookies_data/cookies.csv")
        session, driver = initialize_login_session(driver, session, "cookies_data/cookies.csv")
        for href in hrefs:
            t1 = time.time()
            data_dict = get_match_page_session_and_data(session, driver, href)
            t2 = time.time()
            times_arr.append(t2 - t1)
            print(f"Data retrieval time : {t2 - t1}")
            self.assertTrue(len(list(data_dict.keys())) != 0)
        print(f"Average retrieval time: {statistics.mean(times_arr)} for {len(times_arr)} observations")
        print(f"Standard deviation for retrieval time: {statistics.stdev(times_arr)} for {len(times_arr)} observations")

if __name__ == '__main__':
    unittest.main()
