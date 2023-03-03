# this file is going to keep the structure of our matches folder and
import os


def make_id_from_data(team1, team2, date):
    team1 = (team1.lower()).replace(" ", "")
    team2 = (team2.lower()).replace(" ", "")
    return "{date}_{team1}_{team2}".format(team1=team1, team2=team2, date=date)


def input_match(directory, team1, team2, date):
    id_string = make_id_from_data(team1, team2, date)
    file_path = os.path.join(directory, id_string)

    if os.path.exists(file_path) and os.path.isdir(file_path):
        print('Path already exists')
        return file_path
    else:
        os.mkdir(file_path)
        print('Path for match created')
        return file_path


def check_if_exists_return_path(team1, team2, date):
    id_string = make_id_from_data(team1, team2, date)
    file_path = os.path.join('matches', id_string)

    if os.path.exists(file_path) and os.path.isdir(file_path):
        print('Path already exists')
        return file_path
    else:
        return None


def get_item_path_from_match(team1, team2, date, data_type):
    valid = {'Objects', 'Lines', 'Players', 'Field', 'Annotations', 'Scrapped_data'}
    if data_type not in valid:
        raise ValueError("results: status must be one of %r." % valid)

    path = check_if_exists_return_path(team1, team2, date)
    if path is None:
        raise TypeError("The match data doesn't exist")
    item = os.path.join(path, data_type)

    return item


def from_id_to_atomic(id_string):
    return id_string.split("_")


def search_matches():
    matches = []
    for file in os.listdir("matches/"):
        match_info = from_id_to_atomic(str(file))
        matches.append(match_info)
    return matches


def read_teams_options(path_to_options):
    with open(path_to_options, "r") as f:
        data = f.read()
        data_into_list = data.split("\n")
        teams_list = data_into_list
    return teams_list
