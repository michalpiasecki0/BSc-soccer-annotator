import sqlite3
import os
from Database.Objects import Annotation
import pandas as pd

# x-cor, y-cor, time-start, time-finish, match, match-date, annotator-name, action-type, description
# match is composed of given string: team1-team2, where team1 and team2 should be in alphabetical order

def initialize_base():
    if not os.path.isfile('Database/annotations.db'):
        conn = sqlite3.connect('Database/annotations.db')
        c = conn.cursor()
        c.execute("""
        CREATE TABLE annotations (
        x_cor REAL NOT NULL,
        y_cor REAL NOT NULL,
        time_start REAL NOT NULL,
        time_finish REAL,
        match TEXT PRIMARY KEY,
        match_date TEXT PRIMARY KEY,
        annotator-name TEXT,
        action_type TEXT NOT NULL,
        description TEXT)   
        """)
        return conn
    conn = sqlite3.connect('Database/annotations.db')
    return conn


# for now, it will be left empty
def restart_connection(connector):
    connector.close()
    conn = sqlite3.connect('Database/annotations.db')
    c = conn.cursor()
    return c


def insert_to_base(annotation, connector):
    c = connector.cursor()
    c.execute(
        "INSERT INTO annotations VALUES (:x_cor,:y_cor,:time_start,:time_finish,:match,:match_date,:annotator_name,:action_type,:description)",
        {'x_cor': annotation.pos_x, 'y_cor': annotation.pos_y, 'time_start': annotation.time_start,
         'time_finish': annotation.time_finish, 'match': annotation.match,'match_date':annotation.match_date,
         'annotator_name': annotation.annotator_name, 'action_type': annotation.action_type,
         'description': annotation.description})

    try:
        connector.commit()
        return True
    except Exception:
        return False



#annotation key is a tuple consisting of match and date
def update(annotation_key,connector,annotation_updated):
    match = annotation_key[0]
    date = annotation_key[1]
    c = connector.cursor()
    a_new = annotation_updated
    c.execute('''UPDATE annotations SET 
                x_cor =:x_new,
                y_cor =:y_new,
                time_start =:time_snew,
                time_finish =:time_fnew,
                match =:match_new,
                match_date =:match_date_new,
                annotator_name =:annotator_name_new,
                action_type =:action_type_new,
                description =:description_new
                WHERE match = :match AND date = :date''',
              {'match': match, 'date': date,'x_new':a_new[0],'y_new':a_new[1],
               'time_snew':a_new[2],'time_fnew':a_new[3],'match_new':a_new[4],
               'match_date_new':a_new[5],'annotator_name_new':a_new[6],'action_type_new':a_new[7],
               'description_new':a_new[8]})
    connector.commit()


def remove(annotation_key, connector):
    match = annotation_key[0]
    date = annotation_key[1]
    c = connector.cursor()

    c.execute("DELETE from annotations WHERE match = :match AND match_date = :date",
              {'match':match,'date':date})
    try:
        connector.commit()
        return True
    except:
        return False

def get_row(annotation_key,connector):
    match = annotation_key[0]
    date = annotation_key[1]
    c = connector.cursor()
    c.execute("SELECT * FROM annotations WHERE match_date=:date and match=:match",{'date':date,'match':match})
    return c.fetchall()

def get_data_frame(annotation_key,connector):
    match = annotation_key[0]
    date = annotation_key[1]
    c = connector.cursor()
    #c.execute("SELECT * FROM annotations WHERE match_date=:date and match=:match", {'date': date, 'match': match})
    to_execute = "SELECT * FROM annotations WHERE match_date = '{}' AND match = '{}'".format(date,match)
    to_execute_2 = "SELECT * FROM annotations"
    try:
        df = pd.read_sql_query(to_execute, connector)
    except Exception:
        df = None
    return df

def register_user(user_data,connnector):
    pass

def user_login(user_data,connector):
    pass

#to be performed via GUI
def download_selected(keys_arr):
    pass

