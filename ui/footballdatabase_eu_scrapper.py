from requests_html import HTMLSession
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import Chrome
import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession
from selenium.webdriver.common.by import By
from unidecode import unidecode
import re
import json
import os
from csv import DictReader

def initialize_session_footballdatabase():
    options = Options()
    # options.add_argument("--start-maximized")
    options.add_argument("user-agent=foo")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = Chrome(executable_path="ui/chromedriver", options=options)
    driver.minimize_window()
    session = HTMLSession()
    driver.get("https://www.footballdatabase.eu/en/")
    path = os.path.join('ui', 'cookies_data', 'cookies.csv')
    cookies = get_cookies(path)
    for i in cookies:
        driver.add_cookie(i)
    driver.refresh()
    driver.implicitly_wait(1)
    return session, driver


def get_cookies(file):
    with open(file, encoding='utf-8-sig') as f:
        dict_reader = DictReader(f)
        list_of_dicts = list(dict_reader)
    return list_of_dicts


def initialize_login_session(driver, session):
    driver.get("https://www.footballdatabase.eu/en/")
    cookies = get_cookies("ui/cookies_data/cookies.csv")
    for i in cookies:
        driver.add_cookie(i)
    driver.refresh()

    return session, driver


# date format is YYYY-MM-DD
def get_data_from_GUI(date, team1, team2):
    team1 = unidecode(team1).replace(" ", "_")
    team1 = team1.lower()
    team2 = unidecode(team2).replace(" ", "_")
    team2 = team2.lower()
    return date, team1, team2


def get_game_id_and_href(data, session, driver):
    def search_for_match_id(team1, team2):
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

    driver.implicitly_wait(1)
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
    driver.get(reference_link)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    temp = soup.find_all('div', class_='playerTitulaire outplayer')

    # <---- getting score ---->
    def get_score():
        temp = soup.find_all('div', class_="score0")
        return temp[0].find_all('h2')[0].text

    # <--- getting country and stadium ---->
    def get_country_stadium():
        temp = soup.find_all('div', class_='location')
        temp_2 = re.split('-', temp[0].find_all('p')[0].text)
        return unidecode(temp_2[0].replace(" ", "") + " " + temp_2[1].replace(" ", "")), unidecode(
            temp_2[2].replace(" ", ""))

    # <--- getting first eleven playing players for both teams ---->
    def get_first_eleven_both_teams(temp):
        table = temp[0].find_all('table')
        team_1 = pd.read_html(str(table))[0]

        table = temp[1].find_all('table')
        team_2 = pd.read_html(str(table))[0]

        return list(team_1['First 11.3'].apply(unidecode)), list(team_2['First 11.3'].apply(unidecode))

    # <--- getting match length ---->
    def get_match_length():
        # no information about match length given on the website
        return ''

    # <--- getting player scores and times ---->
    def get_players_scores():
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
        temp = soup.find_all('div', class_='section entraineur toggleteam1')
        temp = temp[0].find_all('a')[0]

        temp_2 = soup.find_all('div', class_='section entraineur toggleteam2')
        temp_2 = temp_2[0].find_all('a')[0]

        return unidecode(temp.text), unidecode(temp_2.text)

    # <--- getting match referee ---->
    def get_referee():
        temp = soup.find_all('p', class_='nameReferee')
        return unidecode(temp[0].text.replace(" ", "", 1))

    # <--- getting substitutions ---->
    def get_substitutions(temp):
        def correct_concat_numbers(z):
            # potential problem with games that last more than 100 minutes !!!
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
