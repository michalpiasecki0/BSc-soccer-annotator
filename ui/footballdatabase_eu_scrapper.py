from selenium.webdriver.chrome.options import Options
from selenium.webdriver import Chrome
import pandas as pd
from bs4 import BeautifulSoup
from requests_html import HTMLSession
from selenium.webdriver.common.by import By
from unidecode import unidecode
import re
import json
import os
from csv import DictReader
import time
from scipy.spatial.distance import hamming
import math


def initialize_session_footballdatabase(path_default="ui/cookies_data/cookies.csv"):
    '''
    This function initializes dynamic session with the webpage using selenium and beautifulsoup.
    :return: Session object for beautifulsoup and driver object for selenium.
    '''
    options = Options()
    options.add_argument("user-agent=foo")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = Chrome(executable_path="ui/chromedriver", options=options)
    driver.minimize_window()
    session = HTMLSession()
    driver.get("https://www.footballdatabase.eu/en/")
    if path_default.__eq__("ui/cookies_data/cookies.csv"):
        path = os.path.join('ui', 'cookies_data', 'cookies.csv')
    else:
        path = path_default
    cookies = get_cookies(path)
    for i in cookies:
        driver.add_cookie(i)
    driver.refresh()
    driver.implicitly_wait(1)
    return session, driver


def get_cookies(file):
    '''
    This function gets the cookies stored in a csv file to the website that is used in the scrapping process and
    processes them to be readable by the website. (Cookies are necessary to input into website in order to function
    optimally)
    :param: File - the path to the file where the .csv with the cookies is stored. :return: List os
    dictionaries with keys and values for the cookies.
    '''
    with open(file, encoding='utf-8-sig') as f:
        dict_reader = DictReader(f)
        list_of_dicts = list(dict_reader)
    return list_of_dicts


def initialize_login_session(driver, session, path_default="ui/cookies_data/cookies.csv"):
    '''
    This function sets up the session and inputs the cookies into the session.
    :param driver: The driver object for selenium.
    :param session: The session driver for beautifulsoup.
    :return: Updated version of the session and driver objects.
    '''
    driver.get("https://www.footballdatabase.eu/en/")
    if path_default.__eq__("ui/cookies_data/cookies.csv"):
        path = os.path.join('ui', 'cookies_data', 'cookies.csv')
    else:
        path = path_default
    cookies = get_cookies(path)
    for i in cookies:
        driver.add_cookie(i)
    driver.refresh()

    return session, driver


# date format is YYYY-MM-DD
def get_data_from_GUI(date, team1, team2):
    '''
    This function formats the data and the names of the teams in order to be usable in the following functions.
    :param date: The date the match took place taken from the GUI (format YYY-MM-DD).
    :param team1: The name of the first team.
    :param team2: The name of the second team.
    :return: The formatted string tuple (triplet) of the date, team1 and team2.
    '''
    team1 = unidecode(team1).replace(" ", "_")
    team1 = team1.lower()
    team2 = unidecode(team2).replace(" ", "_")
    team2 = team2.lower()
    return date, team1, team2


def get_game_id_and_href(data, session, driver):
    '''
    This function searches for the game id of the game on the website and returns reference link to the page.
    :param data: Touple (triplet) containing (in this order) the date, team name 1, team name 2.
    :param session: The session object for beautifulsoup.
    :param driver: The driver object for selenium.
    :return: Id for the game on the corresponding webpage and link to the game page.
    '''

    def search_for_match_id(team1, team2):
        '''
        This is an auxiliary function to search through the string of games in the web resources.
        :param team1: The name of the first team.
        :param team2: The name of the second team.
        :return: Returns -1 if the game (hence match id) was not found and the id if it was found in the array.
        '''

        if len(team1) > len(team2):
            threshold = math.ceil(len(team2)/4)
        else:
            threshold = math.ceil(len(team1)/4)
        threshold = float(threshold)
        for i, element in enumerate(hrefs):
            element = re.split('/', element)
            element = element[4]
            element = re.split('-', element)
            # checking conditions
            if (element[1] == team1 and element[2] == team2) or (element[2] == team1 and element[1] == team2):
                return element[0]
            elif (matches_tuples[i][0] == team1 and matches_tuples[i][1] == team2) or (
                    matches_tuples[i][1] == team1 and matches_tuples[i][0] == team2):
                return element[0]
            elif (((hamming_execute_complete(matches_tuples[i][0], team1) <= threshold) and (
                    (hamming_execute_complete(matches_tuples[i][1], team2)) <= threshold)
                   or ((hamming_execute_complete(matches_tuples[i][1], team1) <= threshold) and (
                            (hamming_execute_complete(matches_tuples[i][0], team2)) <= threshold)))):
                return element[0]
        return -1

    date = data[0]
    team1 = data[1]
    team2 = data[2]
    url_full = 'https://www.footballdatabase.eu/en/results/-/{match_date}'.format(match_date=date)
    driver.get(url_full)
    driver.implicitly_wait(1)
    elements = driver.find_elements(By.CSS_SELECTOR, "a.plus")
    # checking alredy active
    soup = BeautifulSoup(driver.page_source, 'lxml')
    asf = soup.select('a.plus')
    for element, element_active in zip(asf, elements):
        if len(element.select('svg.moins')) == 0:
            driver.execute_script("arguments[0].click();", element_active)
            time.sleep(1)

    soup = BeautifulSoup(driver.page_source, 'lxml')

    matches_tuples = []
    game = soup.select("div.module.gamelist")
    lines = game[0].select("tr.line")
    for line in lines:
        club_left = unidecode(line.select('td.club.left')[0].text)
        club_left = unidecode(club_left).replace(" ", "_")
        club_left = club_left.lower()
        # ------- #
        club_right = unidecode(line.select('td.club.right')[0].text)
        club_right = unidecode(club_right).replace(" ", "_")
        club_right = club_right.lower()
        # ------- #
        temp_tuple = (club_left, club_right)
        matches_tuples.append(temp_tuple)

    scores = soup.select('td.score')
    links = []
    for score in scores:
        links += score.find_all('a')
    hrefs = [link['href'] for link in links]
    id = search_for_match_id(team1, team2)
    id = '/en/match/overview/' + str(id)
    key_dict = {'reference_core': 'https://www.footballdatabase.eu', 'match_id': id, 'team_1': team1, 'team_2': team2}
    reference_link = "{reference_core}{match_id}".format(**key_dict)

    return id, reference_link


def get_match_page_session_and_data(session, driver, reference_link):
    '''
    This function retrieves all the data from the page and creates a dictionary containing all the required elements.
    :param session: Session object for beautifulsoup.
    :param driver: Driver object for selenium.
    :param reference_link: The reference link (hyperlink) to the game page in the web domain.
    :return: Dictionary containing all the keys and their respective values for required data in the scrapping.
    '''
    driver.get(reference_link)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    temp = soup.find_all('div', class_='playerTitulaire outplayer')

    # <---- getting score ---->
    def get_score():
        '''
        Auxiliary function to retrieve score of the match from the web page.
        :return: The score in the string format.
        '''
        temp = soup.find_all('div', class_="score0")
        return temp[0].find_all('h2')[0].text

    # <--- getting country and stadium ---->
    def get_country_stadium():
        '''
        Auxiliary function to retrieve country and the stadium name of the match from the web page.
        :return: Tuple in the format (string country name, string stadium name).
        '''
        temp = soup.find_all('div', class_='location')
        temp_2 = re.split('-', temp[0].find_all('p')[0].text)
        return unidecode(temp_2[0].replace(" ", "") + " " + temp_2[1].replace(" ", "")), unidecode(
            temp_2[2].replace(" ", ""))

    # <--- getting first eleven playing players for both teams ---->
    def get_first_eleven_both_teams(temp):
        '''
        Auxiliary function to retrieve the first eleven players of both teams the match from the web page.
        :param temp: The beautifulsoup table to be passed in order to optimize the code.
        :return: Two lists containing the names of the players. Respectively the first team and second team players.
        '''
        table = temp[0].find_all('table')
        team_1 = pd.read_html(str(table))[0]

        table = temp[1].find_all('table')
        team_2 = pd.read_html(str(table))[0]

        return list(team_1['First 11.3'].apply(unidecode)), list(team_2['First 11.3'].apply(unidecode))

    # <--- getting match length ---->
    def get_match_length():
        '''
        Placeholder due to the lack of information of the match length (to be developed in the future).
        :return: Empty sting.
        '''
        # no information about match length given on the website
        return ''

    # <--- getting player scores and times ---->
    def get_players_scores():
        '''
        Auxiliary function to retrieve who and at what time scored in the match.
        :return: Two lists containing tuples of (player, score time) which indicates who and when scored a goal.
        '''
        temp = soup.find_all('div', class_='scorerTeam1')
        # list of tuples (player, time)
        scores_team1 = []
        for element in temp:
            scores_team1.append((unidecode(element.find_all('a')[0].text), element.find_all('p')[0].text))

        temp = soup.find_all('div', class_='scorerTeam2')
        scores_team2 = []
        for element in temp:
            scores_team2.append((unidecode(element.find_all('a')[0].text), element.find_all('p')[0].text))
        return scores_team1, scores_team2

    # <--- getting team managers ---->
    def get_team_managers():
        '''
        Auxiliary function to retrieve managers of the teams from the match from the web page.
        :return: Tuple in the format (string manager of team1, string manager of team2).
        '''
        temp = soup.find_all('div', class_='section entraineur toggleteam1')
        temp = temp[0].find_all('a')[0]

        temp_2 = soup.find_all('div', class_='section entraineur toggleteam2')
        temp_2 = temp_2[0].find_all('a')[0]

        return unidecode(temp.text), unidecode(temp_2.text)

    # <--- getting match referee ---->
    def get_referee():
        '''
        Auxiliary function to retrieve referee of the match from the web page.
        :return: String with the referee name and surname.
        '''
        temp = soup.find_all('p', class_='nameReferee')
        return unidecode(temp[0].text.replace(" ", "", 1))

    # <--- getting substitutions ---->
    def get_substitutions(temp):
        '''
        This function gets all the substitutions that occurred in the match for both teams.
        :param temp: The beautifulsoup table to be passed in order to optimize the code.
        :return: Two lists (for team1 and team2 respectively) containing the tuples
        in the format (player, time, up/down), where up indicates that player came to the field and down that player
        went down from the field in the substitution.
        '''

        def correct_concat_numbers(z):
            if len(str(int(z))) < 3:
                return int(z)
            z = str(int(z))
            return z[len(z) // 2:]

        table_for_two_first = temp[2].find_all('table')
        df_for_two_first = pd.read_html(str(table_for_two_first))[0][["Substitutes.3", "Substitutes.4"]]
        df_for_two_first["Substitutes.3"] = df_for_two_first["Substitutes.3"].apply(unidecode)
        df_for_two_first['type'] = 'up'
        x = list(df_for_two_first.itertuples(index=False, name=None))
        # ------------------- #
        table_for_one_first = temp[0].find_all('table')
        df_for_one_first = pd.read_html(str(table_for_one_first))[0][["First 11.3", "First 11.4"]]
        df_for_one_first = df_for_one_first[df_for_one_first['First 11.4'].notna()]
        df_for_one_first["First 11.4"] = df_for_one_first["First 11.4"].apply(correct_concat_numbers)
        df_for_one_first["First 11.3"] = df_for_one_first["First 11.3"].apply(unidecode)
        df_for_one_first['type'] = 'down'
        y = list(df_for_one_first.itertuples(index=False, name=None))
        # ------------------ #
        team_1_substitutions = x + y

        table_for_two_second = temp[3].find_all('table')
        df_for_two_second = pd.read_html(str(table_for_two_second))[0][["Substitutes.3", "Substitutes.4"]]
        df_for_two_second["Substitutes.3"] = df_for_two_second["Substitutes.3"].apply(unidecode)
        df_for_two_second['type'] = 'up'
        x = list(df_for_two_second.itertuples(index=False, name=None))

        table_for_one_second = temp[1].find_all('table')
        df_for_one_second = pd.read_html(str(table_for_one_second))[0][["First 11.3", "First 11.4"]]
        df_for_one_second = df_for_one_second[df_for_one_second['First 11.4'].notna()]
        df_for_one_second["First 11.4"] = df_for_one_second["First 11.4"].apply(correct_concat_numbers)
        df_for_one_second["First 11.3"] = df_for_one_second["First 11.3"].apply(unidecode)
        df_for_one_second['type'] = 'down'
        y = list(df_for_one_second.itertuples(index=False, name=None))
        # ------------------ #
        team_2_substitutions = x + y

        return team_1_substitutions, team_2_substitutions

    def intent_to_get_data(data_get_func):
        '''
        Function designed to softly get data should it not be available on the web page.
        :param data_get_func: One of the auxiliary functions to get data.
        :return: Data that the function would normally return.
        '''
        try:
            data = data_get_func()
        except Exception:
            data = ''
        return data

    score = intent_to_get_data(get_score)

    try:
        stadium, country = get_country_stadium()
    except Exception:
        stadium, country = '', ''

    try:
        first_eleven_team_1, first_eleven_team_2 = get_first_eleven_both_teams(temp)
    except Exception:
        first_eleven_team_1, first_eleven_team_2 = '', ''

    match_length = get_match_length()

    try:
        scores_team_1, scores_team_2 = get_players_scores()
    except Exception:
        scores_team_1, scores_team_2 = '', ''

    try:
        team_manager_1, team_manager_2 = get_team_managers()
    except Exception:
        team_manager_1, team_manager_2 = '', ''

    referee = intent_to_get_data(get_referee)

    try:
        substitutions_team_1, substitutions_team_2 = get_substitutions(temp)
    except Exception:
        substitutions_team_1, substitutions_team_2 = '', ''

    dict_return = {'score': score, 'stadium_name': stadium, 'country': country,
                   'first_eleven_team_1': first_eleven_team_1,
                   'first_eleven_team_2': first_eleven_team_2, 'match_length': match_length,
                   'scores_team_1': scores_team_1,
                   'scores_team_2': scores_team_2, 'team_manager_1': team_manager_1, 'team_manager_2': team_manager_2,
                   'referee': referee, 'substitutions_team_1': substitutions_team_1,
                   'substitutions_team_2': substitutions_team_2}

    return dict_return


def save_to_JSON(to_json_dict, match_string):
    '''
    This function saves the scrapped data to the folder structure in the JSON format.
    :param to_json_dict: The dictionary containing the data that are to be saved to the folder structure.
    :param match_string: The string representing the match (date-team1_team2).
    '''
    try:
        file = os.path.join('matches', match_string)
        os.makedirs(file)
    except FileExistsError:
        # directory already exists
        pass
    print("Checkpoint 1")
    file = os.path.join('matches', match_string, 'scrapped_data.json')
    print("Checkpoint 2")
    with open(file, "w+") as outfile:
        print('Opening {file}'.format(file=str(file)))
        json.dump(to_json_dict, outfile)
    print("Checkpoint 3")


def hamming_execute_complete(string1, string2):
    '''
    This function calculates the hamming distance between two strings that are not necessary the same length.
    The difference in length corresponds to 1 hamming distance for every unit of length difference.
    :param string1: First string to calculate hamming distance.
    :param string2: Second string to calculate hamming distance.
    :return: Hamming distance as a floating number.
    '''
    def which_longer(string1, string2):
        '''
        Auxiliary function that checks which string is longer.
        :param string1: First string to compare.
        :param string2: Second string to compare.
        :return: Returns the shorter string.
        '''
        if len(string1) > len(string2):
            return string1
        else:
            return string2

    def equalize_string_length(string1, string2):
        '''
        Auxiliary function that add non-equal characters to the shorter string to make both strings equal length .
        :param string1: First string to equalize length.
        :param string2: Second string to equalize length.
        :return: A shorter string with concatenated characters so that is the equal length as the second string.
        '''
        if len(string1) > len(string2):
            longer_string = string1
            shorter_string = string2
        else:
            longer_string = string2
            shorter_string = string1
        difference = len(longer_string) - len(shorter_string)
        new_string = shorter_string
        for i in range(difference):
            new_string += chr(ord('a') + i)
        return new_string

    string_longer = which_longer(string1, string2)
    string_shorter = equalize_string_length(string1, string2)
    hamming_distance = hamming(list(string_shorter), list(string_longer)) * len(string_shorter)

    return hamming_distance
