from footballdatabase_eu_scrapper import *


def run_script(date,team1,team2):
    session, driver = initialize_session_footballdatabase()

    data = get_data_from_GUI(date, team1, team2)

    id, reference_link = get_game_id_and_href(data, session, driver)
    dictionary_key = get_match_page_session_and_data(session, driver, reference_link)

    match_date_string = data[0] + '_' + data[1].replace('_','') + '_' + data[2].replace('_','')
    save_to_JSON(dictionary_key, match_date_string)




