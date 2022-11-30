import datetime

import requests
import streamlit as st
from streamlit_lottie import st_lottie
from PIL import Image
import os
from Database.Objects.Annotation import Annotation
from Database.Base_functionalities.base import *
from datetime import date


# emojis here: https://www.webfx.com/tools/emoji-cheat-sheet/
st.set_page_config(page_title="Scrapper page test", page_icon=":tada:", layout="wide")


def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


# local CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

PATH_style = os.path.join('Gui_test_demo','style','style.css')
local_css(PATH_style)

# ---- LOAD ASSETS ----
lottie_coding = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_fcfjwiyb.json")
img_contact_form = Image.open("Gui_test_demo/images/yt_contact_form.png")
img_lottie_animation = Image.open("Gui_test_demo/images/yt_lottie_animation.png")

# ---- HEADER SECTION ----
with st.container():
    st.subheader("Version 1.0")
    st.title("Scrapper tool")
    st.write(
        "Version to perform scrapping testing and user registration"
    )

with st.container():
    st.write("---")
    left_column, right_column = st.columns(2)
    with left_column:
        st.header("Implemented functionalities (as for now)")
        st.write("##")
        st.write(
            """
            -
            -
            -
            -
            """
        )
    with right_column:
        st_lottie(lottie_coding, height=300, key="coding")

# ---- CONTACT ----
with st.container():
    st.write("---")
    st.header("Login Form")
    st.write("##")

    contact_form = """
    <form action="https://formsubmit.co/aaf6@o2.pl" method="POST">
        <input type="hidden" name="_captcha" value="false">
        <input type="text" name="Login" placeholder="Login" required>
        <input type="email" name="email" placeholder="Your email" required>
        <textarea name="message" placeholder="Additional information" required></textarea>
        <button type="submit">Send</button>
    </form>
    """
    left_column, right_column = st.columns(2)
    with left_column:
        st.markdown(contact_form, unsafe_allow_html=True)
    with right_column:
        st.empty()

#---- DATABASE INIT ----
conn = initialize_base()

# ---- INPUT DATA SIMULATOR ----

with st.container():
    st.write("---")
    st.header("Imput Data Simulator")
    st.write("##")
    st.write('This section serves to simulate data input to perform tests on the annotation database')

    col1, col2 = st.columns(2)

    form_input = st.form(key="form_input")

    x_cor = form_input.text_input(label = 'Enter x coordinate')
    y_cor = form_input.text_input(label='Enter y coordinate')
    time_start = form_input.text_input(label='Enter action start time')
    time_finish = form_input.text_input(label='Enter action finish time')
    match = form_input.text_input(label='Enter match (in format team1-team2)')
    match_date = form_input.date_input(label='Select match date')
    annotator_name = form_input.text_input(label='Input annotator name')
    action_type = form_input.text_input(label='Input action name')
    desc = form_input.text_input(label='Write some description')
    submit = form_input.form_submit_button(label = 'Input data')

    if submit:
        x_cor = float(x_cor)
        y_cor = float(y_cor)
        time_start = float(time_start)
        time_finish = float(time_finish)
        match_date = str(match_date)


        annotation = Annotation.Annotation(x_cor,y_cor,time_start,time_finish,match,match_date,annotator_name,action_type,desc)
        if insert_to_base(annotation,conn):
            output_text = 'Successfully added data row'
            st.write(output_text)
        else:
            output_text = 'Row not added successfully'
            st.write(output_text)

# ---- DELETE DATA SIMULATOR ----

with st.container():
    st.write("---")
    st.header("Delete Data Simulator")
    st.write("##")
    st.write('This section serves to simulate data deleation to perform tests on the annotation database')
    st.write('ID of a annotation is composed of "team1-team2-date-annotator-annotation_time" in a form of a string')

    form_delete = st.form(key="form_delete")
    ID = form_delete.text_input(label='Enter match ID')
    match = form_delete.text_input(label='Enter match (in format team1-team2)')
    match_date = form_delete.date_input(label='Select match date')
    submit = form_delete.form_submit_button(label='Delete data')

    if submit:
        match_date = str(match_date)
        annotation_key = (match,match_date)
        if remove(annotation_key,conn):
            output_text = 'Successfully deleted data'
            st.write(output_text)
        else:
            output_text = 'Row not deleted (such an instance did not exist)'
            st.write(output_text)




