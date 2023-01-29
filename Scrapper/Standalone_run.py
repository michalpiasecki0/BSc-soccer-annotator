import sys
import re
import os
from footballdatabase_eu_scrapper import *


def run_script(PATH):
    '''
    This function is responsible for running scrapper through the system's command line as a
    standalone module. After providing the PATH to the directory containing the folders with
    matches strings, it will extract game info from them and run scrapper on each of the matches.

    :param PATH: Reference to the directory that contains folders that represents matches (formatting of such folders
    must follow the rules of the naming convention among the application).
    '''

    def check_format(string):
        '''
        Auxiliary function that checks whether the match sting naming convention is followed.
        :param string: The string on which the naming convention is to be checked.
        '''
        pattern = r'^\d{4}-\d{2}-\d{2}_[^\s_]+_[^\s_]+$'
        match = re.search(pattern, string)
        if match:
            return True
        else:
            return False

    Matches_arr = list(os.walk(PATH))[0][1]
    for match in Matches_arr:
        if not check_format(match):
            pass

        date = match.split('_')[0]
        team1 = match.split('_')[1]
        team2 = match.split('_')[2]

        print("In scrapper")
        session, driver = initialize_session_footballdatabase(path_default = 'cookies_data/cookies.csv')
        print("Session iniciated")
        data = get_data_from_GUI(date, team1, team2)
        print("Data retreived")
        id, reference_link = get_game_id_and_href(data, session, driver)
        print("Game id and href retrieved")
        dictionary_key = get_match_page_session_and_data(session, driver, reference_link)
        print("Match page and session id")
        match_date_string = match
        print("String made")
        save_to_JSON(dictionary_key, match_date_string, PATH)
        print("Data saved")

if __name__ == "__main__":
    PATH = str(sys.argv[1])
    run_script(PATH)