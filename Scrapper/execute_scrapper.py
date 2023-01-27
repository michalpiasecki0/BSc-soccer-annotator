from footballdatabase_eu_scrapper import *

def run_script(date,team1,team2):
    '''
    This function is responsible for running the whole data scrapping process. There is no return
    value, instead the data is saved into the appropriate folder structure.

    :param date: This is the date of the match. The formatting required is YYYY-MM-DD
    :param team1: The name of the first team participating in the match
    :param team2: The name of the second team participating in the match
    '''

    print("In scrapper")
    session, driver = initialize_session_footballdatabase()
    print("Session iniciated")
    data = get_data_from_GUI(date, team1, team2)
    print("Data retreived")
    id, reference_link = get_game_id_and_href(data, session, driver)
    print("Game id and href retrieved")
    dictionary_key = get_match_page_session_and_data(session, driver, reference_link)
    print("Match page and session id")
    match_date_string = str(data[0]) + '_' + str(data[1]).replace('_','') + '_' + str(data[2]).replace('_','')
    print("String made")
    save_to_JSON(dictionary_key, match_date_string)
    print("Data saved")



