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
from tempfile import NamedTemporaryFile
import json

# streamlit configs
st.set_page_config(
    page_title='Soccer annotator',
    page_icon=':soccer:',
    layout="wide"
)

# loading default data
players = pd.read_csv('ui/data/players.csv')
events = pd.read_csv('ui/data/events.csv')
fieldAnnotations = pd.read_csv('ui/data/field_annotations.csv')
lineAnnotations = pd.read_csv('ui/data/line_annotations.csv')
playerAnnotations = pd.read_csv('ui/data/player_annotations.csv')
ballAnnotations = pd.read_csv('ui/data/ball_annotations.csv')
eventAnnotations = pd.read_csv('ui/data/event_annotations.csv')

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
            # scrapedData = json.load(
            #     open(
            #         'matches/' + str(matchDate) + '_' + firstTeam + '_' + secondTeam + '/scrapped_data.json'
            #     )
            # )
            st.session_state['scrapedData'] = json.load(
                open('matches/2019-08-17_celtavigo_realmadrid/scrapped_data.json')
            )

    with st.form(key='automatic_annotation'):
        st.write('Getting automatic annotations')
        annotate = st.form_submit_button('Get annotations')
        if annotate:
            # initialize automatic annotation
            st.session_state['annotatedEvents'] = json.load(
                open('matches/2019-08-17_celtavigo_realmadrid/objects.json')
            )

if 'scrapedData' in st.session_state:
    scrapedData = st.session_state['scrapedData']
    players.columns = ['_', firstTeam, secondTeam]
    players[firstTeam] = scrapedData['first_eleven_team_1']
    players[secondTeam] = scrapedData['first_eleven_team_2']

firstRow = st.columns([3, 4, 3])
with firstRow[0]:
    videoSourceType = st.radio('Video Source',
                               ['URL', 'File'],
                               horizontal=True)


    def video_on_change():
        if 'capturedVideo' in st.session_state:
            del st.session_state['capturedVideo']


    if videoSourceType == 'URL':
        default_video = "https://www.youtube.com/watch?v=muIp6hciYl8"
        videoURL = st.text_input('Enter your video URL',
                                 value=default_video,
                                 placeholder='Enter YouTube URL',
                                 on_change=video_on_change)

    elif videoSourceType == 'File':
        videoFile = st.file_uploader('Upload your video file',
                                     on_change=video_on_change)
        if videoFile is not None:
            videoBytes = videoFile.getvalue()
            data = b64encode(videoBytes).decode()
            mime = "video/mp4"
            videoURL = [{"type": mime, "src": f"data:{mime};base64,{data}"}]
        else:
            st.stop()

    videoHeight = 500
    videoPlayer = st_player(url=videoURL,
                            events=['onProgress', 'onPause'],
                            key='video',
                            height=videoHeight)

    secondsOfVideoPlayed = videoPlayer[1]['playedSeconds'] if videoPlayer[1] is not None else 0

if 'annotatedEvents' in st.session_state:
    annotatedEvents = st.session_state['annotatedEvents']
    if str(float(int(secondsOfVideoPlayed))) in annotatedEvents:
        annotatedEventsDf = pd.DataFrame.from_dict(annotatedEvents[str(float(int(secondsOfVideoPlayed)))], orient='index')
        playerAnnotations = annotatedEventsDf

with firstRow[1]:
    annotationType = st.radio('Choose annotation type',
                              ['Event annotation',
                               'Field annotation',
                               'Line annotation',
                               'Player annotation',
                               'Ball annotation'],
                              index=0,
                              horizontal=True)
    if annotationType == 'Field annotation':
        canvasDrawingMode = 'polygon'
        annotations = fieldAnnotations
    elif annotationType == 'Line annotation':
        canvasDrawingMode = 'line'
        annotations = lineAnnotations
    elif annotationType == 'Player annotation':
        canvasDrawingMode = 'rect'
        annotations = playerAnnotations
    elif annotationType == 'Ball annotation':
        canvasDrawingMode = 'rect'
        annotations = ballAnnotations
    elif annotationType == 'Event annotation':
        annotations = eventAnnotations

with firstRow[2]:
    if annotationType == 'Line annotation':
        canvas_field = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
            background_image=Image.open('ui/data/football_pitch.png'),
            update_streamlit=True,
            drawing_mode='point',
            key="canvas_pitch",
            point_display_radius=0.3
        )

        # debug
        # if canvas_field.json_data is not None:
        #     objects = pd.json_normalize(canvas_field.json_data["objects"])
        #     for col in objects.select_dtypes(include=['object']).columns:
        #         objects[col] = objects[col].astype("str")
        #     if len(objects) > 0:
        #         st.dataframe(objects.loc[:, ['left', 'top']])
        #         st.dataframe(objects)

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
        # updatedPlayers.to_csv('ui/data/players.csv', index=False)
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
            temporaryFile = NamedTemporaryFile(delete=False)
            temporaryFile.write(videoFile.read())
            capture = cv2.VideoCapture(temporaryFile.name)
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


    if annotationType != 'Event annotation':
        if annotationType == 'Object annotation':
            selectedTeam = st.selectbox(
                'Choose team',
                ['-'] + list(players.columns[[1, 2]]))
            selectedPlayer = st.selectbox(
                'Choose player',
                players[selectedTeam] if selectedTeam != '-' else ['Ball', 'Referee'])

        currentFrame = get_frame(secondsOfVideoPlayed)
        canvas_frame = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
            background_image=currentFrame,
            update_streamlit=True,
            drawing_mode=canvasDrawingMode,
            height=videoHeight,
            width=videoHeight * (currentFrame.width / currentFrame.height) if currentFrame else 1.5,
            stroke_width=3
        )
    elif annotationType == 'Event annotation':
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
