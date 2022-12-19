import requests
import pandas as pd
from bs4 import BeautifulSoup
import datetime

def get_urls():
    url = ""
    data = requests.get(url)
    return data


#Ta funkcja będzie pobierała dane z GUI o meczu, który użytkownik chce dokonać scrapingu
def prepare_search_data():
    #Get team 1 name
    Team_1 = ""
    #Get team 2 name
    Team_2 = ""
    #Get date
    Date = datetime.date(2022,11,21)
    #Get league name
    League = ""
    return (Team_1,Team_2,Date,League)


def scrap_from_footballdatabaseeu(options=None):
    data = prepare_search_data()
    url = 'https://www.footballdatabase.eu/en/results/-/' + str(data[2])

    return None


def save_to_csv(options = None):
    pass


