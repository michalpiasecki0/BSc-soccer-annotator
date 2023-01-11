import os
from deta import Deta
from dotenv import load_dotenv

load_dotenv("App_final/ui/.env")
DETA_KEY = os.getenv("DETA_KEY")
DETA_KEY = 'a0so00po_wMBVb6Ni88dvp3UxJ9EUSa6QtbfBwkWn'
deta = Deta(DETA_KEY)
db = deta.Base("Application_user_db")


def insert_user(username, name, password, email):
    if get_user(username) != -1:
        return -1
    return db.put({"key": username, "name": name, "password": password, "email": email})


def fetch_all_users():
    res = db.fetch()
    return res.items


def get_user(username):
    user = db.get(username)
    return user if user else -1


def update_user(username, updates):
    return db.update(updates, username)


def delete_user(username):
    return db.delete(username)


insert_user("Tester", "Test", "abc123", "aaf6@o2.pl")