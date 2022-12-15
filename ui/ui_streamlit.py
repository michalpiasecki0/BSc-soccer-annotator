import datetime
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
# from tempfile import NamedTemporaryFile

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

# loading default data
players = pd.read_csv('ui/data/default/players.csv')
events = pd.read_csv('ui/data/default/events.csv')
fieldAnnotations = pd.read_csv('ui/data/default/field_annotations.csv')
lineAnnotations = pd.read_csv('ui/data/default/line_annotations.csv')
playerAnnotations = pd.read_csv('ui/data/default/player_annotations.csv')
ballAnnotations = pd.read_csv('ui/data/default/ball_annotations.csv')
eventAnnotations = pd.read_csv('ui/data/default/event_annotations.csv')

st.title('BSc Soccer Annotator')

sidebar = st.sidebar
with sidebar:
    with st.form(key='scraper_form'):
        st.write('Getting data about the match')
        matchDate = st.date_input('Choose the date of the match', value=datetime.date(2019, 8, 17))
        sidebarColumns = st.columns(2)
        with sidebarColumns[0]:
            firstTeam = st.text_input('The first team', value='Celta Vigo')
        with sidebarColumns[1]:
            secondTeam = st.text_input('The second team', value='Real Madrid')
        scrapeData = st.form_submit_button('Get data')
        if scrapeData:
            # initialize data scraping
            st.session_state['scrapedData'] = json.load(
                open('ui/data/scrapped_data.json')
            )

    with st.form(key='automatic_annotation'):
        st.write('Getting automatic annotations')
        annotate = st.form_submit_button('Get annotations')
        if annotate:
            # initialize automatic annotation
            st.session_state['annotatedPlayers'] = json.load(
                open('ui/data/annotations/objects.json')
            )

            st.session_state['annotatedBall'] = json.load(
                open('ui/data/annotations/objects.json')
            )

            st.session_state['annotatedLines'] = json.load(
                open('ui/data/annotations/lines.json')
            )
            for key, value in json.load(
                open('ui/data/annotations/lines.json')
            ).items():
                i = 0
                d = {}
                for key2, value2 in value.items():
                    d[i] = {
                        'line': key2,
                        'x1': value2[0][0],
                        'y1': value2[0][1],
                        'x2': value2[1][0],
                        'y2': value2[1][1]
                    }
                    i += 1
                st.session_state['annotatedLines'][key] = d

            st.session_state['annotatedFields'] = json.load(
                open('ui/data/annotations/fields.json')
            )
            for key, value in json.load(
                open('ui/data/annotations/fields.json')
            ).items():
                i = 1
                d = {}
                for xy in value:
                    d['x' + str(i)] = xy[0]
                    d['y' + str(i)] = xy[1]
                    i += 1
                st.session_state['annotatedFields'][key] = {0: d}

if 'scrapedData' in st.session_state:
    scrapedData = st.session_state['scrapedData']
    players.columns = ['_', firstTeam, secondTeam]
    players[firstTeam] = scrapedData['first_eleven_team_1']
    players[secondTeam] = scrapedData['first_eleven_team_2']
    for score in scrapedData['scores_team_1']:
        newEvent = {
            'Event': 'Goal',
            'Team': firstTeam,
            'Player': score[0],
            'Min': score[1],
            'Sec': 0
        }
        eventAnnotations = eventAnnotations.append(newEvent, ignore_index=True)
    for score in scrapedData['scores_team_2']:
        newEvent = {
            'Event': 'Goal',
            'Team': secondTeam,
            'Player': score[0],
            'Min': score[1],
            'Sec': 0
        }
        eventAnnotations = eventAnnotations.append(newEvent, ignore_index=True)
    for substitution in scrapedData['substitutions_team_1']:
        newEvent = {
            'Event': 'Substitution',
            'Team': firstTeam,
            'Player': substitution[0],
            'Min': substitution[1],
            'Sec': 0
        }
        eventAnnotations = eventAnnotations.append(newEvent, ignore_index=True)
    for substitution in scrapedData['substitutions_team_2']:
        newEvent = {
            'Event': 'Substitution',
            'Team': secondTeam,
            'Player': substitution[0],
            'Min': substitution[1],
            'Sec': 0
        }
        eventAnnotations = eventAnnotations.append(newEvent, ignore_index=True)

firstRow = st.columns([3, 4, 3])
with firstRow[0]:
    def video_on_change():
        if 'capturedVideo' in st.session_state:
            del st.session_state['capturedVideo']
        if 'scrapedData' in st.session_state:
            del st.session_state['scrapedData']
        if 'annotatedPlayers' in st.session_state:
            del st.session_state['annotatedPlayers']
        if 'annotatedBall' in st.session_state:
            del st.session_state['annotatedBall']
        if 'annotatedLines' in st.session_state:
            del st.session_state['annotatedLines']
        if 'annotatedFields' in st.session_state:
            del st.session_state['annotatedFields']


    videoSourceType = st.radio('Video Source',
                               ['File', 'URL'],
                               horizontal=True,
                               on_change=video_on_change)

    if videoSourceType == 'URL':
        default_video = "https://www.youtube.com/watch?v=muIp6hciYl8"
        videoURL = st.text_input('Enter your video URL',
                                 value=default_video,
                                 placeholder='Enter YouTube URL',
                                 on_change=video_on_change)

    elif videoSourceType == 'File':
        videoFile = open('ui/data/bar_val.mp4', 'rb')
        if videoFile is not None:
            videoBytes = videoFile.read()  # .getvalue()
            videoData = b64encode(videoBytes).decode()
            mimeType = "video/mp4"
            videoURL = [{"type": mimeType, "src": f"data:{mimeType};base64,{videoData}"}]
        else:
            st.stop()

    videoHeight = 500
    videoPlayer = st_player(url=videoURL,
                            events=['onProgress', 'onPause'],
                            key='video',
                            height=videoHeight)

    secondsOfVideoPlayed = videoPlayer[1]['playedSeconds'] if videoPlayer[1] is not None else 0
    secondsRoundedStr = str(float(int(secondsOfVideoPlayed)))

    if 'annotatedPlayers' in st.session_state:
        annotatedPlayers = st.session_state['annotatedPlayers']
        if secondsRoundedStr in annotatedPlayers:
            annotatedObjectsDf = pd.DataFrame.from_dict(
                annotatedPlayers[secondsRoundedStr],
                orient='index')
            playerAnnotations = annotatedObjectsDf

    if 'annotatedLines' in st.session_state:
        annotatedLines = st.session_state['annotatedLines']
        if secondsRoundedStr in annotatedLines:
            annotatedObjectsDf = pd.DataFrame.from_dict(
                annotatedLines[secondsRoundedStr],
                orient='index')
            lineAnnotations = annotatedObjectsDf

    if 'annotatedFields' in st.session_state:
        annotatedFields = st.session_state['annotatedFields']
        if secondsRoundedStr in annotatedFields:
            annotatedObjectsDf = pd.DataFrame.from_dict(
                annotatedFields[secondsRoundedStr],
                orient='index')
            fieldAnnotations = annotatedObjectsDf

with firstRow[1]:
    annotationType = st.radio('Choose annotation type',
                              [EVENT_ANNOTATION,
                               FIELD_ANNOTATION,
                               LINE_ANNOTATION,
                               PLAYER_ANNOTATION,
                               BALL_ANNOTATION],
                              index=0,
                              horizontal=True)
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

with firstRow[2]:
    # if annotationType == LINE_ANNOTATION:
    #     canvas_field = st_canvas(
    #         fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
    #         background_image=Image.open('ui/data/football_pitch.png'),
    #         update_streamlit=True,
    #         drawing_mode='point',
    #         key="canvas_pitch",
    #         point_display_radius=0.3
    #     )
    #     # debug
    #     # if canvas_field.json_data is not None:
    #     #     objects = pd.json_normalize(canvas_field.json_data["objects"])
    #     #     for col in objects.select_dtypes(include=['object']).columns:
    #     #         objects[col] = objects[col].astype("str")
    #     #     if len(objects) > 0:
    #     #         st.dataframe(objects.loc[:, ['left', 'top']])
    #     #         st.dataframe(objects)

    presentedAnnotations = st.dataframe(annotations)

with st.expander('Editing', expanded=False):
    secondRow = st.columns([1, 2, 1, 1, 6])
with secondRow[0]:
    players.set_index('_')
    teams = pd.DataFrame({'Teams': players.columns[[1, 2]]})
    gb_teams = GridOptionsBuilder.from_dataframe(teams)
    gb_teams.configure_default_column(editable=True)

    ag_teams = AgGrid(teams,
                      gridOptions=gb_teams.build(),
                      fit_columns_on_grid_load=True)

with secondRow[1]:
    gb_players = GridOptionsBuilder.from_dataframe(players)
    gb_players.configure_default_column(editable=True)

    ag_players = AgGrid(players,
                        gridOptions=gb_players.build(),
                        fit_columns_on_grid_load=True)

with secondRow[2]:
    gb_events = GridOptionsBuilder.from_dataframe(events)
    gb_events.configure_default_column(editable=True)
    ag_events = AgGrid(data=events,
                       gridOptions=gb_events.build(),
                       fit_columns_on_grid_load=True)

with secondRow[3]:
    saveChanges = st.button('Save changes')
    if saveChanges:
        updatedTeams = list(ag_teams['data']['Teams'])
        updatedPlayers = ag_players['data']
        updatedPlayers.columns = [updatedPlayers.columns[0]] + updatedTeams
        updatedPlayers.to_csv('ui/data/players.csv', index=False)
        updatedEvents = ag_events['data']
        updatedEvents.to_csv('ui/data/events.csv', index=False)

with secondRow[4]:
    gb_annotations = GridOptionsBuilder.from_dataframe(annotations)
    gb_annotations.configure_default_column(editable=True)
    ag_annotations = AgGrid(data=annotations,
                            gridOptions=gb_annotations.build(),
                            fit_columns_on_grid_load=True)

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
            capture = cv2.VideoCapture('ui/data/bar_val.mp4')
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
        frameHeight = videoHeight
        frameWidth = videoHeight * (currentFrame.width / currentFrame.height) if currentFrame else 1.5
        scaleWidth = frameWidth / currentFrame.width
        scaleHeight = frameHeight / currentFrame.height

        if annotationType == PLAYER_ANNOTATION:
            selectedTeam = st.selectbox(
                'Choose team',
                ['-'] + list(players.columns[[1, 2]]))
            selectedPlayer = st.selectbox(
                'Choose player',
                players[selectedTeam] if selectedTeam != '-' else ['Referee'])

        if annotationType in [PLAYER_ANNOTATION, BALL_ANNOTATION]:
            for index, row in annotations.iterrows():
                player = json.load(open('ui/data/canvas_templates/canvas_player_template.json'))
                player['left'] = row['x_top_left'] * scaleWidth
                player['top'] = row['y_top_left'] * scaleHeight
                player['width'] = (row['x_bottom_right'] - row['x_top_left']) * scaleWidth
                player['height'] = (row['y_bottom_right'] - row['y_top_left']) * scaleHeight
                initialDrawing['objects'].append(player)
        elif annotationType == LINE_ANNOTATION:
            for index, row in annotations.iterrows():
                line = json.load(open('ui/data/canvas_templates/canvas_line_template.json'))
                line['left'] = (row['x1'] + row['x2']) / 2 * scaleWidth
                line['top'] = (row['y1'] + row['y2']) / 2 * scaleHeight
                line['width'] = abs(row['x2'] - row['x1']) * scaleWidth
                line['height'] = abs(row['y2'] - row['y1']) * scaleHeight
                line['x1'] = row['x1'] * scaleWidth - line['left']
                line['x2'] = row['x2'] * scaleWidth - line['left']
                line['y1'] = row['y1'] * scaleWidth - line['top']
                line['y2'] = row['y2'] * scaleWidth - line['top']
                initialDrawing['objects'].append(line)
        elif annotationType == FIELD_ANNOTATION:
            for index, row in annotations.iterrows():
                field = json.load(open('ui/data/canvas_templates/canvas_field_template.json'))
                maxX = -float('Inf')
                minX = float('Inf')
                maxY = -float('Inf')
                minY = float('Inf')
                for i in range(len(row) // 2):
                    field['path'].append([
                        'M' if i == 0 else 'L',
                        row[2*i] * scaleWidth,
                        row[2*i + 1] * scaleHeight
                    ])
                    maxX = max(maxX, row[2*i])
                    minX = min(minX, row[2*i])
                    maxY = max(maxY, row[2*i + 1])
                    minY = min(minY, row[2*i + 1])
                field['path'].append(['z'])
                field['width'] = (maxX - minX) * scaleWidth
                field['height'] = (maxY - minY) * scaleHeight
                field['left'] = minX * scaleWidth + field['width'] / 2
                field['top'] = minY * scaleHeight + field['height'] / 2
                initialDrawing['objects'].append(field)

        canvas_frame = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
            background_image=currentFrame,
            update_streamlit=True,
            drawing_mode=canvasDrawingMode,
            height=frameHeight,
            width=frameWidth,
            stroke_width=3,
            initial_drawing=initialDrawing
        )
        # debug
        # if canvas_frame.json_data is not None:
        #     objects = pd.json_normalize(canvas_frame.json_data["objects"])
        #     for col in objects.select_dtypes(include=['object']).columns:
        #         objects[col] = objects[col].astype("str")
        #     if len(objects) > 0:
        #         st.dataframe(objects.loc[:, ['left', 'top']])
        #         st.dataframe(objects)
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
        if submitAnnotation:
            pass
            # presentedAnnotations.add_rows({'Event': [selectedEvent],
            #                                'Team': [selectedTeam],
            #                                'Player': [selectedPlayer],
            #                                'Min': [secondsOfVideoPlayed // 60],
            #                                'Sec': [round(secondsOfVideoPlayed % 60, 2)]})
