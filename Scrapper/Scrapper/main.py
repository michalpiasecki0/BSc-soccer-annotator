from Dedicated_scrappers.footballdatabase_eu_scrapper import *


def main():
    session, driver = initialize_session_footballdatabase()

    #date, team1, team2 = get_data_from_GUI()

    date = '2014-05-13'
    team1 = 'MC El Eulma'
    team2 = 'ES Sétif'

    data = (date, team1, team2)

    id, reference_link = get_game_id_and_href(data, session, driver)
    print(reference_link)
    dictionary_key = get_match_page_session_and_data(session, driver, reference_link)

    match_date_string = '2014-05-13-mc_el_eulma_es_setif'
    save_to_JSON(dictionary_key, match_date_string)

if __name__ == "__main__":
    main()



