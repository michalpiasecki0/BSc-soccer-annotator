import os


def read_teams_options(path_to_options):
    with open(path_to_options, "r") as f:
        data = f.read()
        data_into_list = data.split("\n")
        teams_list = data_into_list
    return teams_list
