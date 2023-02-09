import datetime
import json
import os
import re
import sys
from base64 import b64encode
from zipfile import ZipFile
from pathlib import Path

import cv2
import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
from PIL import Image, ImageDraw
from st_aggrid import AgGrid, GridOptionsBuilder
from streamlit_drawable_canvas import st_canvas
from streamlit_player import st_player
from youtube_dl import YoutubeDL

import database as db
import match_folder_structure_validator
from execute_scrapper import run_script
from footballdatabase_eu_scrapper import get_data_from_GUI
from read_team_options import read_teams_options

bs_soccer = str((Path('./')).resolve())
automatic_models_path = str((Path('./') / 'automatic_models').resolve())
yolo_path = str((Path('./') / 'automatic_models' / 'object_detection' / 'yolo').resolve())

for path in (bs_soccer, automatic_models_path, yolo_path):
    print(path)
    if path not in sys.path:
        sys.path.append(path)

from automatic_models.main import perform_models

# streamlit configs
st.set_page_config(
    page_title='Soccer annotator',
    page_icon=':soccer:',
    layout="wide",
    menu_items={
        'Get Help': 'https://github.com/michalpiasecki0/BSc-soccer-annotator/wiki/Tutorial',
        'Report a bug': "https://github.com/michalpiasecki0/BSc-soccer-annotator/issues",
        'About': "https://github.com/michalpiasecki0/BSc-soccer-annotator/wiki"
    }
)

# annotation type names
EVENT_ANNOTATION = 'Event annotation'
FIELD_ANNOTATION = 'Field annotation'
LINE_ANNOTATION = 'Line annotation'
PLAYER_ANNOTATION = 'Player annotation'
BALL_ANNOTATION = 'Ball annotation'
ANNOTATION_TYPES = [EVENT_ANNOTATION, FIELD_ANNOTATION, LINE_ANNOTATION, PLAYER_ANNOTATION, BALL_ANNOTATION]
MODIFY_ANNOTATIONS = 'Modifying annotations'
ADD_ANNOTATIONS = 'Adding annotations'

# loading default data
players = pd.read_csv('ui/data/default/players.csv')
events = pd.read_csv('ui/data/default/events.csv')
lines = list(json.load(open('automatic_models/lines_and_field_detection/data/lines_coordinates.json')).keys())
fieldAnnotations = pd.read_csv('ui/data/default/field_annotations.csv')
lineAnnotations = pd.read_csv('ui/data/default/line_annotations.csv')
playerAnnotations = pd.read_csv('ui/data/default/player_annotations.csv')
ballAnnotations = pd.read_csv('ui/data/default/ball_annotations.csv')
eventAnnotations = pd.read_csv('ui/data/default/event_annotations.csv')

# loading teams data
teams_options = read_teams_options("ui/teams_data/Teams_names_array.txt")
Countries_options = read_teams_options("ui/teams_data/Countries_names_array.txt")
Countries_options_fr = read_teams_options("ui/teams_data/Countries_names_fr_array.txt")
countries_dict = dict(zip(Countries_options, Countries_options_fr))
teams_dict = dict(zip(teams_options, teams_options))
dict_concatenated = {}
dict_concatenated.update(countries_dict)
dict_concatenated.update(teams_dict)

# --- User Authentication ---
users = db.fetch_all_users()

usernames = [user["key"] for user in users]
names = [user["name"] for user in users]
hashed_passwords = [user["password"] for user in users]

credentials = {"usernames": {}}
for uname, name, pwd in zip(usernames, names, hashed_passwords):
    user_dict = {"name": name, "password": pwd}
    credentials["usernames"].update({uname: user_dict})

title_placeholder = st.empty()
info_placeholder = st.empty()
authenticator = stauth.Authenticate(credentials, "cookies", 'cookies_named', cookie_expiry_days=5)

name, authentication_status, username = authenticator.login("Login", "main")

if not authentication_status:
    with title_placeholder:
        st.title('Soccer annotator')
    with info_placeholder:
        st.write('PLease login in or register to start using an app.')

    if authentication_status is None:
        st.warning("Enter your username and password")
    else:
        st.error("Username/password is incorrect")

if authentication_status:
    # the beginning of the ui rendering
    st.title('Soccer Annotator')
    st.write('Annotation tool for video matches.')
    sidebar = st.sidebar
    authenticator.logout("Logout", "sidebar")
    st.sidebar.title(f"Welcome {name}")
    with sidebar:
        # a function used on video change
        def reset_video_data():
            for obj in ANNOTATION_TYPES + ['capturedVideo', 'scrapedData']:
                if obj in st.session_state:
                    del st.session_state[obj]


        st.write('Choosing a video to annotate')
        videoSourceType = st.radio(
            'Video Source',
            ['File', 'URL', 'Upload local file'],
            horizontal=True,
            key='videoSourceType'
        )
        if videoSourceType == 'URL':
            with st.form(key='get_video_from_url'):
                default_video = "https://www.youtube.com/watch?v=muIp6hciYl8"
                videoURL = st.text_input(
                    'Enter your video URL',
                    value=default_video,
                    placeholder='Enter YouTube URL'
                )
                st.write('Supply data about the match')
                matchDate = st.date_input(
                    'Choose the date of the match'
                )
                sidebarColumns = st.columns(2)
                with sidebarColumns[0]:
                    firstTeam = st.text_input('The first team', value='Team1')
                with sidebarColumns[1]:
                    secondTeam = st.text_input('The second team', value='Team2')
                loadVideo = st.form_submit_button('Load video')
                if loadVideo and firstTeam and secondTeam:
                    reset_video_data()
                    matchDirectory = match_folder_structure_validator.input_match(
                        firstTeam,
                        secondTeam,
                        matchDate
                    )
                    configFilePath = os.path.join(matchDirectory, 'config.json')
                    if not os.path.exists(configFilePath):
                        config = json.load(open('ui/data/template_config.json'))
                    else:
                        config = json.load(open(configFilePath))
                    config["url_youtube"] = videoURL
                    with open(configFilePath, 'w') as file:
                        json.dump(
                            config,
                            file,
                            indent=2
                        )
                    st.session_state['matchDirectory'] = matchDirectory
                    st.success('Video loaded!')
            if 'matchDirectory' not in st.session_state:
                st.warning('Load a video to start annotating.')
                st.stop()
            else:
                matchDirectory = st.session_state['matchDirectory']

        elif videoSourceType == 'File':
            matchDirectories = os.listdir('matches/')
            if len(matchDirectories) == 0:
                st.error('No videos to annotate')
                st.stop()
            matchDirectory = os.path.join(
                'matches',
                st.selectbox(
                    'Select a match',
                    matchDirectories
                )
            )
            videoFiles = list(filter(
                lambda file_name: file_name.endswith('.mp4'),
                os.listdir(matchDirectory)
            ))
            configFilePath = os.path.join(matchDirectory, 'config.json')
            if not os.path.exists(configFilePath):
                config = json.load(open('ui/data/template_config.json'))
            else:
                config = json.load(open(configFilePath))
            if len(videoFiles) > 0:
                config['url_local'] = list(map(lambda file_name: os.path.join(matchDirectory, file_name), videoFiles))
                with open(configFilePath, 'w') as file:
                    json.dump(
                        config,
                        file,
                        indent=2
                    )
                videoFileName = st.selectbox(
                    'Select a video',
                    videoFiles
                )
                videoFile = open(os.path.join(matchDirectory, videoFileName), 'rb')
                videoBytes = videoFile.read()
                videoData = b64encode(videoBytes).decode()
                mimeType = "video/mp4"
                videoURL = [{"type": mimeType, "src": f"data:{mimeType};base64,{videoData}"}]
            elif config['url_youtube']:
                videoURL = config['url_youtube']
                videoFileName = None
            else:
                st.error('No video file found!')
                st.stop()

            if st.session_state.get('matchDirectory') and st.session_state['matchDirectory'] != matchDirectory:
                reset_video_data()
            st.session_state['matchDirectory'] = matchDirectory

        elif videoSourceType == 'Upload local file':
            with st.form(key='get_video_from_local'):
                file_uploader = st.file_uploader(label='Upload your video', type='mp4')
                st.write('Supply data about the match')
                matchDate = st.date_input('Choose the date of the match')
                sidebarColumns = st.columns(2)
                with sidebarColumns[0]:
                    firstTeam = st.text_input('The first team', value='Team1')
                with sidebarColumns[1]:
                    secondTeam = st.text_input('The second team', value='Team2')
                loadVideo = st.form_submit_button('Load video')
                if loadVideo and firstTeam and secondTeam:
                    reset_video_data()
                    matchDirectory = match_folder_structure_validator.input_match(
                        firstTeam,
                        secondTeam,
                        matchDate
                    )
                    videoBytes = file_uploader.getvalue()
                    dateStr = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    with open(os.path.join(matchDirectory, 'video' + dateStr + '.mp4'), 'wb') as binary_file:
                        binary_file.write(videoBytes)
                    st.info('File correctly saved. Choose File option to start annotating')
                    configFilePath = os.path.join(matchDirectory, 'config.json')
                    if not os.path.exists(configFilePath):
                        config = json.load(open('ui/data/template_config.json'))
                    else:
                        config = json.load(open(configFilePath))
                    config["url_local"] = [os.path.join(matchDirectory, 'video' + dateStr + '.mp4')]
                    with open(configFilePath, 'w') as file:
                        json.dump(
                            config,
                            file,
                            indent=2
                        )
                    st.session_state['matchDirectory'] = matchDirectory
                    st.success('Video loaded!')
                    st.info('Go to *File* page to start annotating.')

            if 'matchDirectory' not in st.session_state:
                st.warning('Load a video to start annotating.')
            else:
                matchDirectory = st.session_state['matchDirectory']
            st.stop()

        # create a directory for annotations if there isn't one
        if not (os.path.exists(os.path.join(matchDirectory, 'annotations')) and os.path.isdir(
                os.path.join(matchDirectory, 'annotations'))):
            os.mkdir(os.path.join(matchDirectory, 'annotations'))

        with st.form(key='scraper_form'):
            st.write('Getting data about the match')
            if videoSourceType == 'File':
                matchDate = st.date_input(
                    'Choose the date of the match',
                    value=datetime.datetime.strptime(matchDirectory[8:18], '%Y-%m-%d')
                )
                sidebarColumns = st.columns(2)
                Teams_split = matchDirectory.split('_')
                Team_split_1 = Teams_split[1]
                Team_split_2 = Teams_split[2]
                with sidebarColumns[0]:
                    firstTeam = st.text_input('The first team', value=Team_split_1.capitalize())
                with sidebarColumns[1]:
                    secondTeam = st.text_input('The second team', value=Team_split_2.capitalize())
            scrapData = st.form_submit_button('Get data')
            if scrapData:
                # initialize data scraping
                try:
                    with st.spinner('Scraping the data...'):
                        if firstTeam in dict_concatenated:
                            firstTeam = dict_concatenated[str(firstTeam)]
                        if secondTeam in dict_concatenated:
                            secondTeam = dict_concatenated[str(secondTeam)]
                        run_script(matchDate, firstTeam, secondTeam)
                        data = get_data_from_GUI(matchDate, firstTeam, secondTeam)
                        match_date_string = str(data[0]) + '_' + str(data[1]).replace('_', '') + '_' + str(
                            data[2]).replace(
                            '_', '')
                        path_to_scrapped_data = os.path.join('matches', match_date_string, 'scrapped_data.json')
                    st.success('Acquired the data!')
                except:
                    st.error('No data could be found')

            # loading scraped data if exists
            if os.path.exists(
                    os.path.join(matchDirectory, 'scrapped_data.json')
            ) and 'scrapedData' not in st.session_state:
                st.session_state['scrapedData'] = json.load(
                    open(os.path.join(matchDirectory, 'scrapped_data.json'))
                )
                scrapedData = st.session_state['scrapedData']
                players.columns = ['_', firstTeam, secondTeam]
                players[firstTeam] = scrapedData['first_eleven_team_1']
                players[secondTeam] = scrapedData['first_eleven_team_2']
                if EVENT_ANNOTATION not in st.session_state:
                    st.session_state[EVENT_ANNOTATION] = {"actions": []}
                for score in scrapedData['scores_team_1']:
                    minute = re.findall(r'\d+', score[1])
                    if minute:
                        gamepart = '1' if int(minute[0]) <= 45 else '2'
                    else:
                        gamepart = 'other'
                    newEvent = {
                        "videoTime": score[1][:-1] + ':0',
                        "gamePart": gamepart,
                        "label": "Goal",
                        "team": firstTeam,
                        'player': score[0]
                    }
                    newEvent['gameTime'] = newEvent['gamePart'] + ' - ' + newEvent['videoTime']
                    st.session_state[EVENT_ANNOTATION]['actions'].append(newEvent)
                for score in scrapedData['scores_team_2']:
                    minute = re.findall(r'\d+', score[1])
                    if minute:
                        gamepart = '1' if int(minute[0]) <= 45 else '2'
                    else:
                        gamepart = 'other'
                    newEvent = {
                        "videoTime": score[1][:-1] + ':0',
                        "gamePart": gamepart,
                        "label": "Goal",
                        "team": secondTeam,
                        'player': score[0]
                    }
                    newEvent['gameTime'] = newEvent['gamePart'] + ' - ' + newEvent['videoTime']
                    st.session_state[EVENT_ANNOTATION]['actions'].append(newEvent)
                for substitution in scrapedData['substitutions_team_1']:
                    if str(substitution[1]) == 'nan':
                        continue
                    newEvent = {
                        "videoTime": str(substitution[1]) + ':0',
                        "gamePart": '1' if int(substitution[1]) < 45 else '2',
                        "label": "Substitution - " + substitution[2],
                        "team": firstTeam,
                        'player': substitution[0]
                    }
                    newEvent['gameTime'] = newEvent['gamePart'] + ' - ' + newEvent['videoTime']
                    st.session_state[EVENT_ANNOTATION]['actions'].append(newEvent)
                for substitution in scrapedData['substitutions_team_2']:
                    if str(substitution[1]) == 'nan':
                        continue
                    newEvent = {
                        "videoTime": str(substitution[1]) + ':0',
                        "gamePart": '1' if int(substitution[1]) < 45 else '2',
                        "label": "Substitution - " + substitution[2],
                        "team": secondTeam,
                        'player': substitution[0]
                    }
                    newEvent['gameTime'] = newEvent['gamePart'] + ' - ' + newEvent['videoTime']
                    st.session_state[EVENT_ANNOTATION]['actions'].append(newEvent)
            elif not os.path.exists(os.path.join(matchDirectory, 'scrapped_data.json')):
                st.error('No scraped data found!')
            elif 'scrapedData' in st.session_state:
                scrapedData = st.session_state['scrapedData']
                players.columns = ['_', firstTeam, secondTeam]
                players[firstTeam] = scrapedData['first_eleven_team_1']
                players[secondTeam] = scrapedData['first_eleven_team_2']

        with st.form(key='loading_annotations'):
            st.write('Loading saved annotations')
            annotationDirectories = os.listdir(os.path.join(matchDirectory, 'annotations'))
            if len(annotationDirectories) == 0:
                st.warning('No saved annotations to load.')
            else:
                annotationDirectory = os.path.join(
                    matchDirectory,
                    'annotations',
                    st.selectbox(
                        'Select directory with annotations',
                        annotationDirectories
                    )
                )
            loadAnnotations = st.form_submit_button('Load annotations')
            if loadAnnotations:
                if len(annotationDirectories) == 0:
                    st.error('No saved annotations to load!')
                else:
                    # converting annotations to uniform format
                    if os.path.exists(os.path.join(annotationDirectory, 'objects.json')):
                        st.session_state[PLAYER_ANNOTATION] = json.load(
                            open(os.path.join(annotationDirectory, 'objects.json'))
                        )
                        st.session_state['player_info'] = {}
                        for key, value in st.session_state[PLAYER_ANNOTATION].items():
                            st.session_state['player_info'][key] = {}
                            for key2, value2 in value.items():
                                if value2['class'] == 'PERSON':
                                    st.session_state['player_info'][key][
                                        (value2['x_top_left'] // 10,
                                         value2['y_top_left'] // 10,
                                         value2['x_bottom_right'] // 10,
                                         value2['y_bottom_right'] // 10)
                                    ] = (
                                        value2['confidence'],
                                        value2['Team'] if 'Team' in value2 else '-',
                                        value2['Player'] if 'Player' in value2 else '-'
                                    )

                        st.session_state[BALL_ANNOTATION] = json.load(
                            open(os.path.join(annotationDirectory, 'objects.json'))
                        )

                        st.success('objects.json file loaded')
                    else:
                        st.warning('no objects.json file found')

                    if os.path.exists(os.path.join(annotationDirectory, 'lines.json')):
                        st.session_state[LINE_ANNOTATION] = {}
                        st.session_state['lines_names'] = {}
                        for key, value in json.load(
                                open(os.path.join(annotationDirectory, 'lines.json'))
                        ).items():
                            i = 0
                            d = {}
                            st.session_state['lines_names'][key] = {}
                            for key2, value2 in value.items():
                                d[str(i)] = {
                                    'line': key2,
                                    'x1': value2[0][0],
                                    'y1': value2[0][1],
                                    'x2': value2[1][0],
                                    'y2': value2[1][1]
                                }
                                i += 1
                                st.session_state['lines_names'][key][
                                    (value2[0][0] // 10,
                                     value2[0][1] // 10,
                                     value2[1][0] // 10,
                                     value2[1][1] // 10)
                                ] = key2
                            st.session_state[LINE_ANNOTATION][key] = d

                        st.success('lines.json file loaded')
                    else:
                        st.warning('no lines.json file found')

                    if os.path.exists(os.path.join(annotationDirectory, 'fields.json')):
                        st.session_state[FIELD_ANNOTATION] = {}
                        for key, value in json.load(
                                open(os.path.join(annotationDirectory, 'fields.json'))
                        ).items():
                            i = 1
                            d = {}
                            for xy in value:
                                d['x' + str(i)] = xy[0]
                                d['y' + str(i)] = xy[1]
                                i += 1
                            st.session_state[FIELD_ANNOTATION][key] = {'0': d}

                        st.success('fields.json file loaded')
                    else:
                        st.warning('no fields.json file found')

                    if os.path.exists(os.path.join(annotationDirectory, 'actions.json')):
                        st.session_state[EVENT_ANNOTATION] = json.load(
                            open(os.path.join(annotationDirectory, 'actions.json'))
                        )

                        st.success('actions.json file loaded')
                    else:
                        st.warning('no actions.json file found')

        if videoSourceType == 'File' and videoFileName:
            with st.form(key='automatic_annotation'):
                annotationDirectories = os.listdir(os.path.join(matchDirectory, 'annotations'))
                st.write('Getting automatic annotations')
                col1, col2 = st.columns(2)
                with col1:
                    models_frequency = st.text_input("Model's frequency", value='0.1')
                with col2:
                    models_start_point = st.text_input("Video start point", value='0')
                c1, c2, c3 = st.columns(3)
                with c1:
                    annotate_events = st.checkbox(label='Annotate events', value=False)
                with c2:
                    annotate_objects = st.checkbox(label='Annotate objects', value=False)
                with c3:
                    annotate_lines = st.checkbox(label='Annotate lines&fields', value=False)
                annotation_name = st.text_input('Annotation name', value='model_annotation')
                model_config = st.text_input("Configuration for models", placeholder='Field not necesarry')
                annotate = st.form_submit_button(label='Get annotations')
                if annotate:
                    with st.spinner('Annotating...'):
                        perform_models(video_path=os.path.join(matchDirectory, videoFileName),
                                       output_path=matchDirectory + '/annotations/' + annotation_name,
                                       frequency=float(models_frequency),
                                       starting_point=float(models_start_point),
                                       models_config_path=model_config,
                                       saving_strategy='overwrite',
                                       perform_events=annotate_events,
                                       perform_objects=annotate_objects,
                                       perform_lines_fields=annotate_lines,
                                       save_imgs=False)
                    st.success('Finished annotating!')

        # create a file with annotations to download
        zipFileName = 'zippedAnnotations.zip'
        with ZipFile(zipFileName, 'w') as zipFile:
            # Iterate over all the files in directory
            for folderName, subfolders, filenames in os.walk(os.path.join(matchDirectory, 'annotations')):
                for filename in filenames:
                    # create complete filepath of file in directory
                    filePath = os.path.join(folderName, filename)
                    # Add file to zip
                    zipFile.write(filePath, filePath)
        # downloading annotations
        with open(zipFileName, 'rb') as zipFile:
            downloadAnnotations = st.download_button(
                'Download annotations',
                zipFile,
                file_name="annotations.zip",
                mime="application/zip"
            )
        players.columns = ['_', firstTeam, secondTeam]

    # the main part of the interface
    uiColumns = st.columns([2.5, 5, 2.6])
    with uiColumns[0]:
        if 'annotationType' not in st.session_state:  # setting default annotation type
            st.session_state['annotationType'] = EVENT_ANNOTATION

        videoModeType = st.radio(
            '',
            [
                'Video player', 'Frame by frame', 'By annotations'
            ] if st.session_state[
                     'annotationType'
                 ] != EVENT_ANNOTATION and st.session_state['annotationType'] in st.session_state else [
                'Video player', 'Frame by frame'
            ],
            key='videoModeType'
        )
        if 'capturedVideo' in st.session_state:
            max_frames = st.session_state['capturedVideo'].get(cv2.CAP_PROP_FRAME_COUNT)
            video_fps = st.session_state['capturedVideo'].get(cv2.CAP_PROP_FPS)
        else:  # setting default placeholder values if video is not yet loaded
            max_frames = 100
            video_fps = 30

        if videoModeType == 'Video player':
            if st.session_state.get('annotationType') == EVENT_ANNOTATION:
                videoPlayerContainer = uiColumns[1]
            else:
                videoPlayerContainer = st.empty()
            with videoPlayerContainer:
                videoPlayer = st_player(
                    url=videoURL,
                    events=['onProgress'],
                    key='video'
                )
            secondsOfVideoPlayed = videoPlayer[1]['playedSeconds'] if videoPlayer[1] is not None else 0.0

        elif videoModeType == 'Frame by frame':
            st.write(f'Video FPS rate is {video_fps}.')

            frameInterval = st.number_input(
                'Frame interval',
                min_value=1,
                max_value=int(max_frames),
                value=int(video_fps * st.session_state[
                    'secondsInterval']) if 'secondsInterval' in st.session_state else 1,
                key='frameInterval'
            )
            frameNumber = st.slider(
                'Frame number',
                step=st.session_state['frameInterval'],
                min_value=0,
                max_value=int(max_frames),
                value=int(video_fps * st.session_state[
                    'secondsNumber']) if 'secondsNumber' in st.session_state else 0,
                key='frameNumber'
            )

            secondsInterval = st.number_input(
                'Seconds interval',
                min_value=1 / video_fps,
                max_value=max_frames / video_fps,
                value=st.session_state['frameInterval'] / video_fps,
                key='secondsInterval'
            )
            secondsNumber = st.slider(
                'Seconds number',
                value=st.session_state['frameNumber'] / video_fps,
                step=st.session_state['secondsInterval'],
                min_value=0.0,
                max_value=max_frames / video_fps,
                key='secondsNumber'
            )


            def next_frame_button_on_click():
                st.session_state['frameNumber'] = min(
                    st.session_state['frameNumber'] + frameInterval,
                    int(max_frames)
                )
                st.session_state['secondsNumber'] = min(
                    st.session_state['secondsNumber'] + secondsInterval,
                    max_frames / video_fps
                )


            nextFrameButton = st.button(
                'Next frame',
                on_click=next_frame_button_on_click
            )

            secondsOfVideoPlayed = frameNumber / video_fps

        elif videoModeType == 'By annotations':
            annotationSecond = st.select_slider(
                'Select second with annotations',
                st.session_state[st.session_state['annotationType']].keys(),
                key='annotationSecond'
            )


            def next_annotation_button_on_click():
                current_annotations = list(st.session_state[annotationType].keys())
                current_annotation_index = current_annotations.index(annotationSecond)
                if current_annotation_index < len(current_annotations) - 1:
                    next_annotation = current_annotations[current_annotation_index + 1]
                    st.session_state['annotationSecond'] = next_annotation


            nextAnnotationButton = st.button(
                'Next annotation',
                on_click=next_annotation_button_on_click
            )

            secondsOfVideoPlayed = float(annotationSecond)

    secondsRoundedStr = str(float(secondsOfVideoPlayed))  # formatted seconds to get annotations

    with uiColumns[2]:
        annotationType = st.radio(
            'Choose annotation type',
            ANNOTATION_TYPES,
            horizontal=True,
            key='annotationType'
        )
        # setting values for every annotation type
        annotationType2DrawingMode = {
            FIELD_ANNOTATION: ('polygon', fieldAnnotations),
            LINE_ANNOTATION: ('line', lineAnnotations),
            PLAYER_ANNOTATION: ('rect', playerAnnotations),
            BALL_ANNOTATION: ('rect', ballAnnotations),
            EVENT_ANNOTATION: ('', eventAnnotations)
        }
        canvasDrawingMode, annotations = annotationType2DrawingMode[annotationType]

        # assuring objects are initialized
        if annotationType == EVENT_ANNOTATION and EVENT_ANNOTATION not in st.session_state:
            st.session_state[EVENT_ANNOTATION] = {"actions": []}
        if 'selectedAnnotation' not in st.session_state:
            st.session_state['selectedAnnotation'] = None

    with uiColumns[2]:
        annotationEditingMode = st.radio(
            'Choose mode',
            [MODIFY_ANNOTATIONS,
             ADD_ANNOTATIONS],
            horizontal=True
        ) if annotationType != EVENT_ANNOTATION else MODIFY_ANNOTATIONS

        if annotationType != EVENT_ANNOTATION and annotationEditingMode == MODIFY_ANNOTATIONS:
            st.info('Double-click an object in the frame to remove it.')

    with uiColumns[1]:
        # create the cv2.CaptureVideo object
        if 'capturedVideo' not in st.session_state:
            if videoSourceType == 'URL' or (videoSourceType == 'File' and not videoFileName):
                ydl = YoutubeDL()
                video_data = ydl.extract_info(videoURL, download=False)
                # link with video and audio
                direct_video_url = [_format['url'] for _format in video_data['formats']
                                    if _format['acodec'] != 'none' and _format['vcodec'] != 'none'][-1]
                capture = cv2.VideoCapture(direct_video_url)
            elif videoSourceType == 'File' and videoFileName:
                # temporaryFile = NamedTemporaryFile(delete=False)
                # temporaryFile.write(videoFile.read())
                capture = cv2.VideoCapture(os.path.join(matchDirectory, videoFileName))
            st.session_state['capturedVideo'] = capture

        capturedVideo = st.session_state['capturedVideo']


        def get_frame(played_seconds):
            capturedVideo.set(cv2.CAP_PROP_POS_MSEC, played_seconds * 1000)
            check, frame = capturedVideo.read()
            if check:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                return Image.fromarray(frame)
            else:
                st.error('Could not get current frame.')
                return None


        currentFrame = get_frame(secondsOfVideoPlayed)
        if not currentFrame:
            st.stop()

        # creating the canvas to draw annotations on
        if annotationType != EVENT_ANNOTATION:
            initialDrawing = {
                "version": "4.4.0",
                "objects": []
            }

            frameWidth = st.slider(
                'Set frame canvas width',
                min_value=100,
                max_value=3000,
                value=500,
                step=10,
                key='frameWidth'
            )
            frameHeight = frameWidth * (currentFrame.height / currentFrame.width) if currentFrame else 0.5
            scaleWidth = frameWidth / currentFrame.width
            scaleHeight = frameHeight / currentFrame.height
            teamsColors = {
                '-': "rgba(255, 165, 0, 0.3)",
                firstTeam: "rgba(0, 255, 165, 0.3)",
                secondTeam: "rgba(165, 0, 255, 0.3)"
            }
            canvasFillColor = teamsColors['-']
            # creating input fields and converting annotations to canvas objects
            if annotationType == PLAYER_ANNOTATION:
                if annotationEditingMode == ADD_ANNOTATIONS:
                    with uiColumns[2]:
                        selectedTeam = st.selectbox(
                            'Choose team',
                            ['-'] + list(players.columns[[1, 2]])
                        )
                        selectedPlayer = st.selectbox(
                            'Choose player',
                            players[selectedTeam] if selectedTeam != '-' else ['-', 'Referee']
                        )
                        canvasFillColor = teamsColors[
                            selectedTeam] if selectedTeam in teamsColors else "rgba(255, 165, 0, 0.3)"
                if PLAYER_ANNOTATION in st.session_state and secondsRoundedStr in st.session_state[PLAYER_ANNOTATION]:
                    for index, data in st.session_state[PLAYER_ANNOTATION][secondsRoundedStr].items():
                        if data['class'] != 'PERSON':
                            continue
                        player = json.load(open('ui/data/canvas_templates/canvas_rect_template.json'))
                        player['left'] = data['x_top_left'] * scaleWidth
                        player['top'] = data['y_top_left'] * scaleHeight
                        player['width'] = (data['x_bottom_right'] - data['x_top_left']) * scaleWidth
                        player['height'] = (data['y_bottom_right'] - data['y_top_left']) * scaleHeight
                        if 'Team' in data and data['Team'] in teamsColors:
                            player['fill'] = teamsColors[data['Team']]
                        st.session_state['player_info'][secondsRoundedStr][
                            (data['x_top_left'] // 10,
                             data['y_top_left'] // 10,
                             data['x_bottom_right'] // 10,
                             data['y_bottom_right'] // 10)
                        ] = (
                            data['confidence'],
                            data['Team'] if 'Team' in data else '-',
                            data['Player'] if 'Player' in data else '-'
                        )
                        initialDrawing['objects'].append(player)
            elif annotationType == BALL_ANNOTATION:
                if BALL_ANNOTATION in st.session_state and secondsRoundedStr in st.session_state[BALL_ANNOTATION]:
                    for index, data in st.session_state[BALL_ANNOTATION][secondsRoundedStr].items():
                        if data['class'] != 'SPORTSBALL':
                            continue
                        ball = json.load(open('ui/data/canvas_templates/canvas_rect_template.json'))
                        ball['left'] = data['x_top_left'] * scaleWidth
                        ball['top'] = data['y_top_left'] * scaleHeight
                        ball['width'] = (data['x_bottom_right'] - data['x_top_left']) * scaleWidth
                        ball['height'] = (data['y_bottom_right'] - data['y_top_left']) * scaleHeight
                        initialDrawing['objects'].append(ball)
            elif annotationType == LINE_ANNOTATION:
                if annotationEditingMode == ADD_ANNOTATIONS:
                    with uiColumns[2]:
                        selectedLine = st.selectbox(
                            'Choose line',
                            lines
                        )
                if LINE_ANNOTATION in st.session_state and secondsRoundedStr in st.session_state[LINE_ANNOTATION]:
                    for index, data in st.session_state[LINE_ANNOTATION][secondsRoundedStr].items():
                        line = json.load(open('ui/data/canvas_templates/canvas_line_template.json'))
                        line['left'] = (data['x1'] + data['x2']) / 2 * scaleWidth
                        line['top'] = (data['y1'] + data['y2']) / 2 * scaleHeight
                        line['width'] = abs(data['x2'] - data['x1']) * scaleWidth
                        line['height'] = abs(data['y2'] - data['y1']) * scaleHeight
                        line['x1'] = data['x1'] * scaleWidth - line['left']
                        line['x2'] = data['x2'] * scaleWidth - line['left']
                        line['y1'] = data['y1'] * scaleHeight - line['top']
                        line['y2'] = data['y2'] * scaleHeight - line['top']
                        st.session_state['lines_names'][secondsRoundedStr][
                            (data['x1'] // 10,
                             data['y1'] // 10,
                             data['x2'] // 10,
                             data['y2'] // 10)
                        ] = data['line']
                        initialDrawing['objects'].append(line)
            elif annotationType == FIELD_ANNOTATION:
                if FIELD_ANNOTATION in st.session_state and secondsRoundedStr in st.session_state[FIELD_ANNOTATION]:
                    if annotationEditingMode == ADD_ANNOTATIONS:
                        for index, data in st.session_state[FIELD_ANNOTATION][secondsRoundedStr].items():
                            field = json.load(open('ui/data/canvas_templates/canvas_polygon_template.json'))
                            maxX = -float('Inf')
                            minX = float('Inf')
                            maxY = -float('Inf')
                            minY = float('Inf')
                            for i in range(len(data) // 2):
                                field['path'].append([
                                    'M' if i == 0 else 'L',
                                    data['x' + str(i + 1)] * scaleWidth,
                                    data['y' + str(i + 1)] * scaleHeight
                                ])
                                maxX = max(maxX, data['x' + str(i + 1)])
                                minX = min(minX, data['x' + str(i + 1)])
                                maxY = max(maxY, data['y' + str(i + 1)])
                                minY = min(minY, data['y' + str(i + 1)])
                            field['path'].append(['z'])
                            field['width'] = (maxX - minX) * scaleWidth
                            field['height'] = (maxY - minY) * scaleHeight
                            field['left'] = minX * scaleWidth + field['width'] / 2
                            field['top'] = minY * scaleHeight + field['height'] / 2
                            initialDrawing['objects'].append(field)
                    elif annotationEditingMode == MODIFY_ANNOTATIONS:
                        for index, data in st.session_state[FIELD_ANNOTATION][secondsRoundedStr].items():
                            for i in range(len(data) // 2):
                                point = json.load(open('ui/data/canvas_templates/canvas_point_template.json'))
                                point['left'] = data['x' + str(i + 1)] * scaleWidth - point['radius']
                                point['top'] = data['y' + str(i + 1)] * scaleHeight - point['radius']
                                initialDrawing['objects'].append(point)
                            break

            canvasFrame = st_canvas(
                fill_color=canvasFillColor,
                background_image=currentFrame,
                update_streamlit=True,
                drawing_mode=canvasDrawingMode if annotationEditingMode == ADD_ANNOTATIONS else 'transform',
                height=frameHeight,
                width=frameWidth,
                stroke_width=3,
                initial_drawing=initialDrawing
            )

            if canvasFrame.json_data is not None:
                # converting canvas objects back to annotations
                annotationsDict = {}
                if annotationType == PLAYER_ANNOTATION:
                    if 'player_info' not in st.session_state:
                        st.session_state['player_info'] = {}
                    if secondsRoundedStr not in st.session_state['player_info']:
                        st.session_state['player_info'][secondsRoundedStr] = {}
                    for i, player in enumerate(canvasFrame.json_data['objects']):
                        annotationsDict[str(i)] = {
                            'class': 'PERSON',
                            'Team': firstTeam if player['fill'] == teamsColors[firstTeam] else (
                                secondTeam if player['fill'] == teamsColors[secondTeam] else '-'),
                            'Player': '-',
                            'x_top_left': round(player['left'] / scaleWidth),
                            'y_top_left': round(player['top'] / scaleHeight),
                            'x_bottom_right': round((player['width'] * player['scaleX'] + player['left']) / scaleWidth),
                            'y_bottom_right': round(
                                (player['height'] * player['scaleY'] + player['top']) / scaleHeight),
                            'confidence': 1
                        }
                        coor_tuple = (
                            annotationsDict[str(i)]['x_top_left'] // 10,
                            annotationsDict[str(i)]['y_top_left'] // 10,
                            annotationsDict[str(i)]['x_bottom_right'] // 10,
                            annotationsDict[str(i)]['y_bottom_right'] // 10
                        )
                        if coor_tuple not in st.session_state['player_info'][secondsRoundedStr]:
                            st.session_state['player_info'][secondsRoundedStr][coor_tuple] = (
                                1,
                                selectedTeam if annotationEditingMode == ADD_ANNOTATIONS else '-',
                                selectedPlayer if annotationEditingMode == ADD_ANNOTATIONS else '-'
                            )
                        annotationsDict[str(i)]['confidence'] = \
                            st.session_state['player_info'][secondsRoundedStr][coor_tuple][0]
                        # annotationsDict[str(i)]['Team'] = \
                        #     st.session_state['player_info'][secondsRoundedStr][coor_tuple][1]
                        annotationsDict[str(i)]['Player'] = \
                            st.session_state['player_info'][secondsRoundedStr][coor_tuple][2]
                elif annotationType == BALL_ANNOTATION:
                    for i, ball in enumerate(canvasFrame.json_data['objects']):
                        annotationsDict[str(i)] = {
                            'class': 'SPORTSBALL',
                            'x_top_left': round(ball['left'] / scaleWidth),
                            'y_top_left': round(ball['top'] / scaleHeight),
                            'x_bottom_right': round((ball['width'] * ball['scaleX'] + ball['left']) / scaleWidth),
                            'y_bottom_right': round((ball['height'] * ball['scaleY'] + ball['top']) / scaleHeight),
                            'confidence': 1
                        }
                elif annotationType == LINE_ANNOTATION:
                    if 'lines_names' not in st.session_state:
                        st.session_state['lines_names'] = {}
                    if secondsRoundedStr not in st.session_state['lines_names']:
                        st.session_state['lines_names'][secondsRoundedStr] = {}
                    for i, line in enumerate(canvasFrame.json_data['objects']):
                        annotationsDict[str(i)] = {
                            'line': '-',
                            'x1': round((line['x1'] * line['scaleX'] + line['left']) / scaleWidth),
                            'y1': round((line['y1'] * line['scaleY'] + line['top']) / scaleHeight),
                            'x2': round((line['x2'] * line['scaleX'] + line['left']) / scaleWidth),
                            'y2': round((line['y2'] * line['scaleY'] + line['top']) / scaleHeight)
                        }
                        coor_tuple = (
                            annotationsDict[str(i)]['x1'] // 10,
                            annotationsDict[str(i)]['y1'] // 10,
                            annotationsDict[str(i)]['x2'] // 10,
                            annotationsDict[str(i)]['y2'] // 10
                        )
                        if coor_tuple not in st.session_state['lines_names'][secondsRoundedStr]:
                            st.session_state['lines_names'][secondsRoundedStr][
                                coor_tuple] = selectedLine if annotationEditingMode == ADD_ANNOTATIONS else '-'
                        annotationsDict[str(i)]['line'] = st.session_state['lines_names'][secondsRoundedStr][coor_tuple]
                elif annotationType == FIELD_ANNOTATION:
                    if annotationEditingMode == ADD_ANNOTATIONS:
                        for i, field in enumerate(canvasFrame.json_data['objects']):
                            annotationsDict[str(i)] = {}
                            for j, point in enumerate(field['path']):
                                if point[0] != 'z':
                                    annotationsDict[str(i)]['x' + str(j + 1)] = \
                                        round(point[1] * field['scaleX'] / scaleWidth)
                                    annotationsDict[str(i)]['y' + str(j + 1)] = \
                                        round(point[2] * field['scaleY'] / scaleHeight)
                    elif annotationEditingMode == MODIFY_ANNOTATIONS:
                        if len(canvasFrame.json_data['objects']) > 0:
                            annotationsDict['0'] = {}
                        for i, point in enumerate(canvasFrame.json_data['objects']):
                            annotationsDict['0']['x' + str(i + 1)] = \
                                round((point['left'] + point['radius']) * point['scaleX'] / scaleWidth)
                            annotationsDict['0']['y' + str(i + 1)] = \
                                round((point['top'] + point['radius']) * point['scaleY'] / scaleHeight)

                if len(annotationsDict.keys()) > 0:
                    annotations = pd.DataFrame.from_dict(
                        annotationsDict,
                        orient='index')
                else:
                    annotations = annotationType2DrawingMode[annotationType][1]

                st.session_state['currentAnnotations'] = annotationsDict

        elif annotationType == EVENT_ANNOTATION:
            if videoModeType != 'Video player':
                st.image(currentFrame)
            with uiColumns[2]:
                selectedEvent = st.selectbox(
                    'Choose event',
                    ['-'] + list(events['Actions'])
                )
                selectedTeam = st.selectbox(
                    'Choose team',
                    ['-'] + list(players.columns[[1, 2]])
                )
                selectedPlayer = st.selectbox(
                    'Choose player',
                    ['-'] + list(players[selectedTeam]) if selectedTeam != '-' else ['-']
                )
                submitAnnotation = st.button('Add annotation')
            if submitAnnotation:
                newEvent = {
                    "videoTime": str(int(secondsOfVideoPlayed // 60)) + ':' + str(round(secondsOfVideoPlayed % 60)),
                    "gamePart": '1' if secondsOfVideoPlayed // 60 < 45 else '2',
                    "label": selectedEvent,
                    "team": selectedTeam,
                    'player': selectedPlayer
                }
                newEvent['gameTime'] = newEvent['gamePart'] + ' - ' + newEvent['videoTime']
                st.session_state[EVENT_ANNOTATION]['actions'].append(newEvent)
            if len(st.session_state[EVENT_ANNOTATION]['actions']) > 0:
                annotations = pd.DataFrame.from_dict(
                    st.session_state[EVENT_ANNOTATION]['actions']
                )
            else:
                annotations = eventAnnotations
        confirmAnnotations = st.button('Confirm annotations')

    with uiColumns[2]:
        # getting image with line names and selected line
        if annotationType == LINE_ANNOTATION and annotationEditingMode == ADD_ANNOTATIONS:
            linesCoordinates = json.load(
                open('automatic_models/lines_and_field_detection/data/lines_coordinates.json')
            )
            pitchImage = Image.open('automatic_models/lines_and_field_detection/data/templateLineNames.png')
            pitchImageDraw = ImageDraw.Draw(pitchImage)
            lineCoordinates = [
                (linesCoordinates[selectedLine][0][0], linesCoordinates[selectedLine][0][1]),
                (linesCoordinates[selectedLine][1][0], linesCoordinates[selectedLine][1][1])
            ]
            pitchImageDraw.line(lineCoordinates, fill='red', width=10)
            st.image(pitchImage)
        elif annotationType == FIELD_ANNOTATION and annotationEditingMode == ADD_ANNOTATIONS:
            st.info(
                'To annotate the field, click the subsequent corners of the polygon, and then right click to finish.'
            )
        st.warning('Remember to confirm your changes with the CONFIRM ANNOTATIONS button!')

    # configuring the table with annotations
    gridOptionsBuilder = GridOptionsBuilder.from_dataframe(annotations)
    gridOptionsBuilder.configure_default_column(editable=True)
    gridOptionsBuilder.configure_selection(selection_mode='single')
    if annotationType == EVENT_ANNOTATION:
        gridOptionsBuilder.configure_column(
            'label',
            cellEditor='agRichSelectCellEditor',
            cellEditorParams={'values': ['-'] + list(events['Actions'])},
            cellEditorPopup=True
        )
        gridOptionsBuilder.configure_column(
            'team',
            cellEditor='agRichSelectCellEditor',
            cellEditorParams={'values': ['-'] + list(players.columns[[1, 2]])},
            cellEditorPopup=True
        )
        gridOptionsBuilder.configure_column(
            'player',
            cellEditor='agRichSelectCellEditor',
            cellEditorParams={
                'values': ['-'] + list(players[players.columns[1]]) + list(players[players.columns[2]])
            },
            cellEditorPopup=True
        )
    elif annotationType == LINE_ANNOTATION:
        gridOptionsBuilder.configure_column(
            'line',
            cellEditor='agRichSelectCellEditor',
            cellEditorParams={'values': lines},
            cellEditorPopup=True
        )
    elif annotationType == PLAYER_ANNOTATION:
        gridOptionsBuilder.configure_column(
            'Team',
            cellEditor='agRichSelectCellEditor',
            cellEditorParams={'values': ['-'] + list(players.columns[[1, 2]])},
            cellEditorPopup=True
        )
        gridOptionsBuilder.configure_column(
            'Player',
            cellEditor='agRichSelectCellEditor',
            cellEditorParams={
                'values':
                    ['-', 'Referee'] + list(players[players.columns[1]]) + list(players[players.columns[2]])
            },
            cellEditorPopup=True
        )
    gridOptionsBuilder.configure_grid_options(enableRangeSelection=True)
    # creating annotations table
    annotationsTable = AgGrid(
        data=annotations,
        gridOptions=gridOptionsBuilder.build(),
        fit_columns_on_grid_load=True
    )
    if len(annotationsTable['selected_rows']) > 0:
        st.session_state['selectedAnnotation'] = annotationsTable['selected_rows'][0]
    else:
        st.session_state['selectedAnnotation'] = None

    if len(annotationsTable['selected_rows']) > 0:
        deleteAnnotation = st.button(
            'Delete selected annotation',
            key='deleteAnnotation'
        )
    # saving current annotations
    if confirmAnnotations or st.session_state.get('deleteAnnotation'):
        if annotationType == EVENT_ANNOTATION:
            st.session_state[annotationType]['actions'] = annotationsTable['data'].to_dict(orient='records')
            if st.session_state.get('deleteAnnotation'):
                st.session_state[annotationType]['actions'].pop(
                    annotationsTable['selected_rows'][0]['_selectedRowNodeInfo']['nodeRowIndex']
                )
        else:
            st.session_state['currentAnnotations'] = annotationsTable['data'].to_dict(orient='index')
            if st.session_state.get('deleteAnnotation'):
                del st.session_state['currentAnnotations'][
                    annotationsTable['selected_rows'][0]['_selectedRowNodeInfo']['nodeRowIndex']]
            if annotationType in st.session_state:
                st.session_state[annotationType][secondsRoundedStr] = st.session_state['currentAnnotations']
            else:
                st.session_state[annotationType] = {
                    secondsRoundedStr: st.session_state['currentAnnotations']
                }

    saveAnnotations = st.button('Save annotations')
    if saveAnnotations:
        datetimeStr = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        dirName = os.path.join(matchDirectory, 'annotations/annotations_' + datetimeStr)
        os.mkdir(dirName)
        filenameEnding = '.json'


        def save_annotations(annotations_data, file_name):
            with open(os.path.join(dirName, file_name + filenameEnding), 'w') as f:
                json.dump(
                    annotations_data,
                    f,
                    indent=2
                )
            st.success(f'{file_name + filenameEnding} saved!')


        # creating changelog file
        save_annotations({
            'name': name,
            'username': username,
            'creation_timestamp': datetimeStr
        }, 'changelog')

        # converting annotations to required formats
        if PLAYER_ANNOTATION in st.session_state and BALL_ANNOTATION in st.session_state:
            objectAnnotations = st.session_state[PLAYER_ANNOTATION]
            for second, objects in st.session_state[BALL_ANNOTATION].items():
                if second in st.session_state[PLAYER_ANNOTATION]:
                    index = str(int(max(st.session_state[PLAYER_ANNOTATION][second].keys())) + 1)
                    objectAnnotations[second][index] = objects[min(objects.keys())]
                else:
                    objectAnnotations[second] = objects
            save_annotations(objectAnnotations, 'objects')
        elif PLAYER_ANNOTATION in st.session_state:
            save_annotations(st.session_state[PLAYER_ANNOTATION], 'objects')
        elif BALL_ANNOTATION in st.session_state:
            save_annotations(st.session_state[BALL_ANNOTATION], 'objects')
        else:
            save_annotations({}, 'objects')

        if LINE_ANNOTATION in st.session_state:
            reformattedLines = {}
            for second, line_annotations in st.session_state[LINE_ANNOTATION].items():
                lines_dict = {}
                for key, line in line_annotations.items():
                    lines_dict[line['line']] = [
                        [
                            line['x1'],
                            line['y1']
                        ],
                        [
                            line['x2'],
                            line['y2']
                        ]
                    ]
                reformattedLines[second] = lines_dict
            save_annotations(reformattedLines, 'lines')
        else:
            save_annotations({}, 'lines')

        if FIELD_ANNOTATION in st.session_state:
            reformattedFields = {}
            for second, field in st.session_state[FIELD_ANNOTATION].items():
                coordinates_list = []
                for i in range(len(field['0']) // 2):
                    coordinates_list.append(
                        [
                            field['0']['x' + str(i + 1)],
                            field['0']['y' + str(i + 1)]
                        ]
                    )
                reformattedFields[second] = coordinates_list
            save_annotations(reformattedFields, 'fields')
        else:
            save_annotations({}, 'fields')

        if EVENT_ANNOTATION in st.session_state:
            save_annotations(st.session_state[EVENT_ANNOTATION], 'actions')
        else:
            save_annotations({'actions': []}, 'actions')

if authentication_status is False or authentication_status is None:
    st.title('Registration Form')
    registration_form = st.form(key='form-1', clear_on_submit=True)
    name_reg = registration_form.text_input('Enter your name:')
    username_reg = registration_form.text_input('Enter a username:')
    password_reg = registration_form.text_input("Enter a password", type="password")
    email = registration_form.text_input('Enter your email:')
    submit = registration_form.form_submit_button('Submit')
    if submit:
        if db.get_user(username_reg) != -1:
            st.warning("User with such username already exists")
        else:
            hashed_registration_password = stauth.Hasher([password_reg]).generate()
            db.insert_user(username_reg, name_reg, hashed_registration_password[0], email)
            st.info("Successfully added user")
