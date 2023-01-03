import datetime
import os
import sys
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import pandas as pd
from streamlit_drawable_canvas import st_canvas
from PIL import Image
from streamlit_player import st_player
from youtube_dl import YoutubeDL
import cv2
from base64 import b64encode
import json
from tempfile import NamedTemporaryFile
# from execute_scrapper import run_script

# streamlit configs
st.set_page_config(
    page_title='Soccer annotator',
    page_icon=':soccer:',
    layout="wide"
)

# annotation types
EVENT_ANNOTATION = 'Event annotation'
FIELD_ANNOTATION = 'Field annotation'
LINE_ANNOTATION = 'Line annotation'
PLAYER_ANNOTATION = 'Player annotation'
BALL_ANNOTATION = 'Ball annotation'
MODIFY_ANNOTATIONS = 'Modifying annotations'
ADD_ANNOTATIONS = 'Adding annotations'

# loading default data
players = pd.read_csv('ui/data/default/players.csv')
events = pd.read_csv('ui/data/default/events.csv')
lines = pd.read_csv('ui/data/default/lines.csv')
fieldAnnotations = pd.read_csv('ui/data/default/field_annotations.csv')
lineAnnotations = pd.read_csv('ui/data/default/line_annotations.csv')
playerAnnotations = pd.read_csv('ui/data/default/player_annotations.csv')
ballAnnotations = pd.read_csv('ui/data/default/ball_annotations.csv')
eventAnnotations = pd.read_csv('ui/data/default/event_annotations.csv')

st.title('Soccer Annotator')

sidebar = st.sidebar
with sidebar:
    def video_on_change():
        if 'capturedVideo' in st.session_state:
            del st.session_state['capturedVideo']
        if 'scrapedData' in st.session_state:
            del st.session_state['scrapedData']
        if PLAYER_ANNOTATION in st.session_state:
            del st.session_state[PLAYER_ANNOTATION]
        if BALL_ANNOTATION in st.session_state:
            del st.session_state[BALL_ANNOTATION]
        if LINE_ANNOTATION in st.session_state:
            del st.session_state[LINE_ANNOTATION]
        if FIELD_ANNOTATION in st.session_state:
            del st.session_state[FIELD_ANNOTATION]


    st.write('Choosing a video to annotate')
    videoSourceType = st.radio(
        'Video Source',
        ['File', 'URL'],
        horizontal=True,
        # on_change=video_on_change,
        key='videoSourceType'
    )
    if videoSourceType == 'URL':
        default_video = "https://www.youtube.com/watch?v=muIp6hciYl8"
        videoURL = st.text_input(
            'Enter your video URL',
            value=default_video,
            placeholder='Enter YouTube URL',
            on_change=video_on_change
        )
    elif videoSourceType == 'File':
        matchDirectories = os.listdir('matches/')
        matchDirectory = 'matches/' + st.selectbox(
            'Select a match',
            matchDirectories
        )
        videoFile = open(matchDirectory + '/video.mp4', 'rb')
        if videoFile is not None:
            videoBytes = videoFile.read()
            videoData = b64encode(videoBytes).decode()
            mimeType = "video/mp4"
            videoURL = [{"type": mimeType, "src": f"data:{mimeType};base64,{videoData}"}]
        else:
            st.stop()

    with st.form(key='scraper_form'):
        st.write('Getting data about the match')
        matchDate = st.date_input('Choose the date of the match', value=datetime.date(2019, 8, 17))
        sidebarColumns = st.columns(2)
        with sidebarColumns[0]:
            firstTeam = st.text_input('The first team', value='Celta Vigo')
        with sidebarColumns[1]:
            secondTeam = st.text_input('The second team', value='Real Madrid')
        scrapData = st.form_submit_button('Get data')
        if scrapData:
            # initialize data scraping
            # try:
            #     run_script(matchDate, firstTeam, secondTeam)
            # except:
            #     st.error('No data could be found')

            st.session_state['scrapedData'] = json.load(
                open(matchDirectory + '/scrapped_data.json')
            )

    with st.form(key='automatic_annotation'):
        st.write('Getting automatic annotations')
        annotationDirectories = os.listdir(matchDirectory + '/annotations/')
        annotationDirectory = matchDirectory + '/annotations/' + st.selectbox(
            'Select directory with annotations',
            annotationDirectories
        )
        annotate = st.form_submit_button('Get annotations')
        if annotate:
            # initialize automatic annotation
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

            st.session_state[LINE_ANNOTATION] = json.load(
                open(os.path.join(annotationDirectory, 'lines.json'))
            )
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

            st.session_state[FIELD_ANNOTATION] = json.load(
                open(os.path.join(annotationDirectory, 'fields.json'))
            )
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

if 'scrapedData' in st.session_state:
    scrapedData = st.session_state['scrapedData']
    players.columns = ['_', firstTeam, secondTeam]
    players[firstTeam] = scrapedData['first_eleven_team_1']
    players[secondTeam] = scrapedData['first_eleven_team_2']
    for score in scrapedData['scores_team_1']:
        newEvent = {
            "videoTime": score[1][:-1],
            "gamePart": '1' if int(score[1][:2]) <= 45 else '2',
            "label": "Goal",
            "team": firstTeam,
            'player': score[0]
        }
        newEvent['gameTime'] = newEvent['gamePart'] + ' - ' + newEvent['videoTime']
        eventAnnotations = eventAnnotations.append(newEvent, ignore_index=True)
    for score in scrapedData['scores_team_2']:
        newEvent = {
            "videoTime": score[1][:-1],
            "gamePart": '1' if int(score[1][:2]) <= 45 else '2',
            "label": "Goal",
            "team": secondTeam,
            'player': score[0]
        }
        newEvent['gameTime'] = newEvent['gamePart'] + ' - ' + newEvent['videoTime']
        eventAnnotations = eventAnnotations.append(newEvent, ignore_index=True)
    for substitution in scrapedData['substitutions_team_1']:
        if str(substitution[1]) == 'nan':
            continue
        newEvent = {
            "videoTime": str(substitution[1]),
            "gamePart": '1' if int(substitution[1]) < 45 else '2',
            "label": "Substitution",
            "team": firstTeam,
            'player': substitution[0]
        }
        newEvent['gameTime'] = newEvent['gamePart'] + ' - ' + newEvent['videoTime']
        eventAnnotations = eventAnnotations.append(newEvent, ignore_index=True)
    for substitution in scrapedData['substitutions_team_2']:
        if str(substitution[1]) == 'nan':
            continue
        newEvent = {
            "videoTime": str(substitution[1]),
            "gamePart": '1' if int(substitution[1]) < 45 else '2',
            "label": "Substitution",
            "team": secondTeam,
            'player': substitution[0]
        }
        newEvent['gameTime'] = newEvent['gamePart'] + ' - ' + newEvent['videoTime']
        eventAnnotations = eventAnnotations.append(newEvent, ignore_index=True)

firstRow = st.columns([2.5, 5, 2.5])
with firstRow[0]:
    videoHeight = 350
    videoPlayer = st_player(url=videoURL,
                            events=['onProgress', 'onPause'],
                            key='video',
                            height=videoHeight)
    videoMode = st.empty()

    secondsOfVideoPlayed = videoPlayer[1]['playedSeconds'] if videoPlayer[1] is not None else 0.0
    secondsRoundedStr = str(float(int(secondsOfVideoPlayed)))

with firstRow[1]:
    annotationType = st.radio(
        'Choose annotation type',
        [
            EVENT_ANNOTATION,
            FIELD_ANNOTATION,
            LINE_ANNOTATION,
            PLAYER_ANNOTATION,
            BALL_ANNOTATION
        ],
        index=0,
        horizontal=True
    )
    if annotationType == FIELD_ANNOTATION:
        canvasDrawingMode = 'polygon'
        annotations = fieldAnnotations
    elif annotationType == LINE_ANNOTATION:
        canvasDrawingMode = 'line'
        annotations = lineAnnotations
    elif annotationType == PLAYER_ANNOTATION:
        canvasDrawingMode = 'rect'
        annotations = playerAnnotations
    elif annotationType == BALL_ANNOTATION:
        canvasDrawingMode = 'rect'
        annotations = ballAnnotations
    elif annotationType == EVENT_ANNOTATION:
        annotations = eventAnnotations

    if annotationType != EVENT_ANNOTATION:
        videoModeContainer = videoMode.container()
        with videoModeContainer:
            videoModeType = st.radio(
                '',
                ['Video player', 'Frame by frame'],
                key='videoModeType'
            )
            if videoModeType == 'Frame by frame':
                if 'capturedVideo' in st.session_state:
                    max_frames = st.session_state['capturedVideo'].get(cv2.CAP_PROP_FRAME_COUNT)
                    video_fps = st.session_state['capturedVideo'].get(cv2.CAP_PROP_FPS)
                else:
                    max_frames = 100
                    video_fps = 30

                st.write(f'Video FPS rate is {video_fps}.')

                frameInterval = st.slider(
                    'Frame interval',
                    min_value=1,
                    max_value=100,
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

                secondsInterval = st.slider(
                    'Seconds interval',
                    min_value=1 / video_fps,
                    max_value=100 / video_fps,
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
                    st.session_state['frameNumber'] += frameInterval
                    st.session_state['secondsNumber'] += secondsInterval


                nextFrameButton = st.button(
                    'Next frame',
                    on_click=next_frame_button_on_click
                )

                secondsOfVideoPlayed = frameNumber / video_fps

with firstRow[2]:
    annotationEditingMode = st.radio(
        'Choose mode',
        [MODIFY_ANNOTATIONS,
         ADD_ANNOTATIONS],
        horizontal=True
    )

# with st.expander('Editing', expanded=False):
#     secondRow = st.columns([1, 2, 1, 1, 6])
#
# with secondRow[0]:
#     players.set_index('_')
#     teams = pd.DataFrame({'Teams': players.columns[[1, 2]]})
#     gb_teams = GridOptionsBuilder.from_dataframe(teams)
#     gb_teams.configure_default_column(editable=True)
#
#     ag_teams = AgGrid(teams,
#                       gridOptions=gb_teams.build(),
#                       fit_columns_on_grid_load=True)
#
# with secondRow[1]:
#     gb_players = GridOptionsBuilder.from_dataframe(players)
#     gb_players.configure_default_column(editable=True)
#
#     ag_players = AgGrid(players,
#                         gridOptions=gb_players.build(),
#                         fit_columns_on_grid_load=True)
#
# with secondRow[2]:
#     gb_events = GridOptionsBuilder.from_dataframe(events)
#     gb_events.configure_default_column(editable=True)
#     ag_events = AgGrid(data=events,
#                        gridOptions=gb_events.build(),
#                        fit_columns_on_grid_load=True)
#
# with secondRow[3]:
#     saveChanges = st.button('Save changes')
#     if saveChanges:
#         updatedTeams = list(ag_teams['data']['Teams'])
#         updatedPlayers = ag_players['data']
#         updatedPlayers.columns = [updatedPlayers.columns[0]] + updatedTeams
#         updatedPlayers.to_csv('ui/data/players.csv', index=False)
#         updatedEvents = ag_events['data']
#         updatedEvents.to_csv('ui/data/events.csv', index=False)
#
# with secondRow[4]:
#     gb_annotations = GridOptionsBuilder.from_dataframe(annotations)
#     gb_annotations.configure_default_column(editable=True)
#     ag_annotations = AgGrid(data=annotations,
#                             gridOptions=gb_annotations.build(),
#                             fit_columns_on_grid_load=True)

with firstRow[1]:
    if 'capturedVideo' not in st.session_state:
        if videoSourceType == 'URL':
            ydl = YoutubeDL()
            video_data = ydl.extract_info(videoURL, download=False)

            # link with video and audio
            direct_video_url = [_format['url'] for _format in video_data['formats']
                                if _format['acodec'] != 'none' and _format['vcodec'] != 'none'][-1]

            capture = cv2.VideoCapture(direct_video_url)
        elif videoSourceType == 'File':
            # temporaryFile = NamedTemporaryFile(delete=False)
            # temporaryFile.write(videoFile.read())
            capture = cv2.VideoCapture(matchDirectory + '/video.mp4')
        st.session_state['capturedVideo'] = capture

    capturedVideo = st.session_state['capturedVideo']


    @st.cache(max_entries=1)
    def get_frame(played):
        capturedVideo.set(cv2.CAP_PROP_POS_MSEC, played * 1000)
        check, frame = capturedVideo.read()
        if check:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(frame)
        else:
            st.error('Could not get current frame.')
            return None


    if annotationType != EVENT_ANNOTATION:
        initialDrawing = {
            "version": "4.4.0",
            "objects": []
        }

        currentFrame = get_frame(secondsOfVideoPlayed)
        frameHeight = videoHeight + 300
        frameWidth = frameHeight * (currentFrame.width / currentFrame.height) if currentFrame else 1.5
        scaleWidth = frameWidth / currentFrame.width
        scaleHeight = frameHeight / currentFrame.height
        teamsColors = {
            '-': "rgba(255, 165, 0, 0.3)",
            firstTeam: "rgba(0, 255, 165, 0.3)",
            secondTeam: "rgba(165, 0, 255, 0.3)"
        }
        canvasFillColor = "rgba(255, 165, 0, 0.3)"
        if annotationType == PLAYER_ANNOTATION:
            selectedTeam = st.selectbox(
                'Choose team',
                ['-'] + list(players.columns[[1, 2]])
            )
            selectedPlayer = st.selectbox(
                'Choose player',
                players[selectedTeam] if selectedTeam != '-' else ['-', 'Referee']
            )
            canvasFillColor = teamsColors[selectedTeam] if selectedTeam in teamsColors else "rgba(255, 165, 0, 0.3)"
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

        canvas_frame = st_canvas(
            fill_color=canvasFillColor,
            background_image=currentFrame,
            update_streamlit=True,
            drawing_mode=canvasDrawingMode if annotationEditingMode == ADD_ANNOTATIONS else 'transform',
            height=frameHeight,
            width=frameWidth,
            stroke_width=3,
            initial_drawing=initialDrawing
        )

        if canvas_frame.json_data is not None:
            annotationsDict = {}
            if annotationType == PLAYER_ANNOTATION:
                if 'player_info' not in st.session_state:
                    st.session_state['player_info'] = {}
                if secondsRoundedStr not in st.session_state['player_info']:
                    st.session_state['player_info'][secondsRoundedStr] = {}
                for i, player in enumerate(canvas_frame.json_data['objects']):
                    annotationsDict[str(i)] = {
                        'class': 'PERSON',
                        'Team': '-',
                        'Player': '-',
                        'x_top_left': round(player['left'] / scaleWidth),
                        'y_top_left': round(player['top'] / scaleHeight),
                        'x_bottom_right': round((player['width'] * player['scaleX'] + player['left']) / scaleWidth),
                        'y_bottom_right': round((player['height'] * player['scaleY'] + player['top']) / scaleHeight),
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
                            selectedTeam,
                            selectedPlayer
                        )
                    annotationsDict[str(i)]['confidence'] = \
                        st.session_state['player_info'][secondsRoundedStr][coor_tuple][0]
                    annotationsDict[str(i)]['Team'] = \
                        st.session_state['player_info'][secondsRoundedStr][coor_tuple][1]
                    annotationsDict[str(i)]['Player'] = \
                        st.session_state['player_info'][secondsRoundedStr][coor_tuple][2]
            elif annotationType == BALL_ANNOTATION:
                for i, ball in enumerate(canvas_frame.json_data['objects']):
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
                for i, line in enumerate(canvas_frame.json_data['objects']):
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
                        st.session_state['lines_names'][secondsRoundedStr][coor_tuple] = selectedLine
                    annotationsDict[str(i)]['line'] = st.session_state['lines_names'][secondsRoundedStr][coor_tuple]
            elif annotationType == FIELD_ANNOTATION:
                if annotationEditingMode == ADD_ANNOTATIONS:
                    for i, field in enumerate(canvas_frame.json_data['objects']):
                        annotationsDict[str(i)] = {}
                        for j, point in enumerate(field['path']):
                            if point[0] != 'z':
                                annotationsDict[str(i)]['x' + str(j + 1)] = \
                                    round(point[1] * field['scaleX'] / scaleWidth)
                                annotationsDict[str(i)]['y' + str(j + 1)] = \
                                    round(point[2] * field['scaleY'] / scaleHeight)
                elif annotationEditingMode == MODIFY_ANNOTATIONS:
                    if len(canvas_frame.json_data['objects']) > 0:
                        annotationsDict['0'] = {}
                    for i, point in enumerate(canvas_frame.json_data['objects']):
                        annotationsDict['0']['x' + str(i + 1)] = \
                            round((point['left'] + point['radius']) * point['scaleX'] / scaleWidth)
                        annotationsDict['0']['y' + str(i + 1)] = \
                            round((point['top'] + point['radius']) * point['scaleY'] / scaleHeight)

            if len(annotationsDict.keys()) > 0:
                annotations = pd.DataFrame.from_dict(
                    annotationsDict,
                    orient='index')
            elif annotationType == PLAYER_ANNOTATION:
                annotations = playerAnnotations
            elif annotationType == BALL_ANNOTATION:
                annotations = ballAnnotations
            elif annotationType == LINE_ANNOTATION:
                annotations = lineAnnotations
            elif annotationType == FIELD_ANNOTATION:
                annotations = fieldAnnotations
            if annotationType in st.session_state:
                st.session_state[annotationType][secondsRoundedStr] = annotationsDict
            else:
                st.session_state[annotationType] = {
                    secondsRoundedStr: annotationsDict
                }

    elif annotationType == EVENT_ANNOTATION:
        selectedEvent = st.selectbox(
            'Choose event',
            ['-'] + list(events['Actions']))
        selectedTeam = st.selectbox(
            'Choose team',
            ['-'] + list(players.columns[[1, 2]]))
        selectedPlayer = st.selectbox(
            'Choose player',
            ['-'] + list(players[selectedTeam]) if selectedTeam != '-' else ['-'])
        submitAnnotation = st.button('Add annotation')
        if EVENT_ANNOTATION not in st.session_state:
            st.session_state[EVENT_ANNOTATION] = pd.read_csv('ui/data/default/event_annotations.csv')
        if submitAnnotation:
            newEvent = {
                "videoTime": str(int(secondsOfVideoPlayed // 60)) + ':' + str(round(secondsOfVideoPlayed % 60)),
                "gamePart": '1' if secondsOfVideoPlayed // 60 < 45 else '2',
                "label": selectedEvent,
                "team": selectedTeam,
                'player': selectedPlayer
            }
            newEvent['gameTime'] = newEvent['gamePart'] + ' - ' + newEvent['videoTime']
            st.session_state[EVENT_ANNOTATION] = st.session_state[EVENT_ANNOTATION].append(
                newEvent,
                ignore_index=True
            )
        annotations = eventAnnotations.append(st.session_state[EVENT_ANNOTATION])

with firstRow[2]:
    gridOptionsBuilder = GridOptionsBuilder.from_dataframe(annotations)
    gridOptionsBuilder.configure_default_column(editable=True)
    ag_events = AgGrid(
        data=annotations,
        gridOptions=gridOptionsBuilder.build(),
        fit_columns_on_grid_load=True
    )

    saveAnnotations = st.button('Save annotations')
    if saveAnnotations:
        datetimeStr = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        dirName = matchDirectory + '/annotations/annotations_' + datetimeStr
        os.mkdir(dirName)
        filenameEnding = '.json'


        def save_annotations(annotations_data, filename):
            with open(dirName + '/' + filename + filenameEnding, 'w') as file:
                json.dump(
                    annotations_data,
                    file,
                    indent=2
                )


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

        eventsDict = eventAnnotations.to_dict(
            orient='records'
        )
        save_annotations({'actions': eventsDict}, 'actions')
