import streamlit_authenticator as stauth
import database as db

usernames =['Jan','TestUser_1','TestUser_2','TestUser_3','Hieronim']
names = ['Jan','TestUser_1', 'TestUser_2','TestUser_3','Hieronim']
passwords = ['LUPA442','qwerty1', 'qwerty2', 'qwerty3','qwerty4']
emails = ['aaf6@o2.pl','aaf6@o2.pl','aaf6@o2.pl','aaf6@o2.pl','aaf6@o2.pl']

hashed_passwords = stauth.Hasher(passwords).generate()

for (username, name, hashed_passwords, email) in zip(usernames, names, hashed_passwords, emails):
    db.insert_user(username, name, hashed_passwords, email)
    print(db.insert_user(username, name, hashed_passwords, email))