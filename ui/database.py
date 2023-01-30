from deta import Deta
from dotenv import load_dotenv
import os

load_dotenv(".env.txt")
DETA_KEY = os.getenv("DETA_KEY")
deta = Deta(DETA_KEY)
db = deta.Base("Application_user_db")


def insert_user(username, name, password, email):
    '''
    This function inputs the user into the database based on their credentials given.
    :param username: This is the username of the user. It serves as a key and is unique in the database.
    :param name: This is the personal name of the user. It will be displayed in the application.
    :param password: This is the password that the user will authenticate their session with.
    :param email: This is the email of the user. There can me multiple accounts for one email.
    :return: -1 if user was input unsuccessfully, 0 if user was input successfully
    '''

    if get_user(username) != -1:
        return -1
    return db.put({"key": username, "name": name, "password": password, "email": email})


def fetch_all_users():
    '''
    This function gets all the users (fetches them) from the database by their keys.
    :return: The dictrionary containing the user's credential with the username as the key
    '''
    res = db.fetch()
    return res.items


def get_user(username):
    '''
    This function returns a user from the database
    '''
    user = db.get(username)
    return user if user else -1


def update_user(username, updates):
    '''
    This function updates the credentials of the user in the database.
    :param username: The key of the user to login, which is the username.
    :param updates: The updates that we want to commit into the database. In the form of a dictionary containing
    {'key':updated_value}. Username can't be altered.
    :return: 0 if the update was successful, -1 if the update was unsuccessful.
    '''
    return db.update(updates, username)


def delete_user(username):
    '''
    This function deletes user from the database based on their username.
    :param username: String that identifies the user in the login process.
    :return: -1 if deletion was unsuccessful, 0 if the deletion was successful
    '''
    return db.delete(username)
