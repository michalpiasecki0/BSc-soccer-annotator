from requests_html import HTMLSession
from selenium.webdriver import Chrome
import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession
from selenium.webdriver.common.by import By
from unidecode import unidecode
import re
import json
import os


def initialize_session_footballdatabase():
    driver = Chrome(executable_path="chromedriver")
    session = HTMLSession()
    return session, driver


def initialize_login_session(driver, session):
    # for now left empty, login to the website will be implemented
    pass


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
        return -1

    date = data[0]
    team1 = data[1]
    team2 = data[2]
    url_full = 'https://www.footballdatabase.eu/en/results/-/{match_date}'.format(match_date=date)
    driver.get(url_full)
    elements = driver.find_elements(By.CSS_SELECTOR, "a.plus")
    for i, element in enumerate(elements):
        driver.execute_script("arguments[0].click();", element)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    scores = soup.select('td.score')
    links = []
    for score in scores:
        links += score.find_all('a')
    hrefs = [link['href'] for link in links]
    id = search_for_match_id(team1, team2)
    id = '/en/match/overview/' + str(id)
    key_dict = {'reference_core': 'https://www.footballdatabase.eu', 'match_id': id, 'team_1': team1,
                'team_2': team2}
    reference_link = "{reference_core}{match_id}/{team_1}-{team_2}".format(**key_dict)
    return id, reference_link


def get_match_page_session_and_data(session, driver, reference_link):
    driver.get(reference_link)
    soup = BeautifulSoup(driver.page_source, 'lxml')

    # <---- getting score ---->
    def get_score():
        text = requests.get(reference_link).text
        soup = BeautifulSoup(text,features="lxml")
        temp = soup.find_all('div', class_="score0")
        return temp[0].find_all('h2')[0].text

    # <--- getting country and stadium ---->
    def get_country_stadium():
        temp = soup.find_all('div', class_='location')
        temp_2 = re.split('-', temp[0].find_all('p')[0].text)
        return unidecode(temp_2[2].replace(" ", "")), unidecode(temp_2[0].replace(" ", "") + " " + temp_2[1].replace(" ", ""))

    # <--- getting first eleven playing players for both teams ---->
    def get_first_eleven_both_teams():
        temp = soup.find_all('div', class_='playerTitulaire outplayer')
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
        temp = temp[0].find_all('a')

        temp_2 = soup.find_all('div', class_='section entraineur toggleteam2')
        temp_2 = temp_2[0].find_all('a')

        return unidecode(temp.text), unidecode(temp_2.text)

    # <--- getting match referee ---->
    def get_referee():
        temp = soup.find_all('p', class_='nameReferee')
        return unidecode(temp[0].text.replace(" ", "", 1))

    # <--- getting substitutions ---->
    def get_substitutions():
        def correct_concat_numbers(z):
            # potential problem with games that last more than 100 minutes !!!
            if len(str(int(z))) < 3:
                return int(z)
            z = str(int(z))
            return z[len(z) // 2:]

        temp = soup.find_all('div', class_='playerTitulaire outplayer')
        table = temp[2].find_all('table')
        df1 = pd.read_html(str(table))[0][["Substitutes.3", "Substitutes.4"]]
        df1["Substitutes.3"] = df1["Substitutes.3"].apply(unidecode)
        df1['type'] = 'up'
        x = list(df1.itertuples(index=False, name=None))

        temp = soup.find_all('div', class_='playerTitulaire outplayer')
        table = temp[0].find_all('table')
        df1 = pd.read_html(str(table))[0][["First 11.3", "First 11.4"]]
        df1 = df1[df1['First 11.4'].notna()]
        df1["First 11.4"] = df1["First 11.4"].apply(correct_concat_numbers)
        df1["First 11.3"] = df1["First 11.3"].apply(unidecode)
        df1['type'] = 'down'
        y = list(df1.itertuples(index=False, name=None))
        team_1_substitutions = x + y

        temp = soup.find_all('div', class_='playerTitulaire outplayer')
        table = temp[3].find_all('table')
        df1 = pd.read_html(str(table))[0][["Substitutes.3", "Substitutes.4"]]
        df1["Substitutes.3"] = df1["Substitutes.3"].apply(unidecode)
        df1['type'] = 'up'
        x = list(df1.itertuples(index=False, name=None))

        temp = soup.find_all('div', class_='playerTitulaire outplayer')
        table = temp[1].find_all('table')
        df1 = pd.read_html(str(table))[0][["First 11.3", "First 11.4"]]
        df1 = df1[df1['First 11.4'].notna()]
        df1["First 11.4"] = df1["First 11.4"].apply(correct_concat_numbers)
        df1["First 11.3"] = df1["First 11.3"].apply(unidecode)
        df1['type'] = 'down'
        y = list(df1.itertuples(index=False, name=None))
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
        first_eleven_team_1, first_eleven_team_2 = get_first_eleven_both_teams()
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
        substitutions_team_1, substitutions_team_2 = get_substitutions()
    except Exception:
        substitutions_team_1, substitutions_team_2 = '', ''

    dict_return = {'score' : score,'stadium_name':stadium,'country':country,'first_eleven_team_1':first_eleven_team_1,
                   'first_eleven_team_2':first_eleven_team_2,'match_length':match_length,'scores_team_1':scores_team_1,
                   'scores_team_2':scores_team_2,'team_manager_1':team_manager_1,'team_manager_2':team_manager_2,
                   'referee':referee,'substitutions_team_1':substitutions_team_1,'substitutions_team_2':substitutions_team_2}

    return dict_return


def save_to_JSON(to_json_dict, match_string):
    try:
        file = os.path.join('..\matches', match_string)
        os.makedirs(file)
    except FileExistsError:
        # directory already exists
        pass
    #file = '/././matches/{match_string}'.format(match_string = match_string) + '/' + 'scrapped_data.json'
    file = os.path.join('..\matches',match_string,'scrapped_data.json')
    with open(file, "w+") as outfile:
        print('Opening {file}'.format(file = str(file)))
        json.dump(to_json_dict, outfile)


def execute_all(date, team1, team2):
    pass
