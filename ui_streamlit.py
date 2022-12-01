import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import pandas as pd
from streamlit_drawable_canvas import st_canvas
from PIL import Image
from streamlit_player import st_player
from youtube_dl import YoutubeDL
import cv2

# streamlit configs
st.set_page_config(layout="wide")

default_video = "https://youtu.be/CmSKVW1v0xM"

# title
st.title('BSc Soccer Annotator')

# video
firstRow = st.columns([1, 1, 1])
with firstRow[0]:
    videoURL = st.text_input('',
                             value=default_video,
                             placeholder='Enter YouTube URL')

    videoPlayer = st_player(url=videoURL,
                            events=['onProgress'],
                            key='video')

    secondsOfVideoPlayed = videoPlayer[1]['playedSeconds'] if videoPlayer[1] is not None else videoPlayer[1]

with firstRow[2]:
    canvas_field = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
        background_image=Image.open('data/football_pitch.png'),
        update_streamlit=True,
        drawing_mode='point',
        key="canvas_pitch",
        point_display_radius=0.3
    )

    # debug
    if canvas_field.json_data is not None:
        objects = pd.json_normalize(canvas_field.json_data["objects"])  # need to convert obj to str because PyArrow
        for col in objects.select_dtypes(include=['object']).columns:
            objects[col] = objects[col].astype("str")
        if len(objects) > 0:
            st.dataframe(objects.loc[:, ['left', 'top']])
            st.dataframe(objects)

# table
st.subheader('Tables')
secondRow = st.columns([1, 2, 1, 1, 6])
with secondRow[0]:
    players = pd.read_csv('data/players.csv')
    players.set_index('_')
    teams = pd.DataFrame({'Teams': players.columns[[1, 2]]})
    gb_teams = GridOptionsBuilder.from_dataframe(teams)
    gb_teams.configure_default_column(editable=True)
    gb_teams.configure_selection(selection_mode='single',
                                 use_checkbox=True,
                                 pre_selected_rows=[0],
                                 suppressRowDeselection=True)

    ag_teams = AgGrid(teams,
                      gridOptions=gb_teams.build(),
                      fit_columns_on_grid_load=True,
                      allow_unsafe_jscode=True,
                      reload_data=False)

    selectedTeam = '-'
    if len(ag_teams['selected_rows']) > 0:
        selectedTeam = ag_teams['selected_rows'][0]['Teams']

with secondRow[1]:
    gb_players = GridOptionsBuilder.from_dataframe(
        players[
            ['_', selectedTeam] if selectedTeam != '-' else ['_']
        ])
    gb_players.configure_default_column(editable=True)
    gb_players.configure_selection(selection_mode='single',
                                   use_checkbox=True)

    ag_players = AgGrid(players,
                        gridOptions=gb_players.build(),
                        fit_columns_on_grid_load=True)

    selectedPlayer = '-'
    if len(ag_players['selected_rows']) > 0:
        selectedPlayer = ag_players['selected_rows'][0][selectedTeam]

with secondRow[2]:
    actions = pd.read_csv('data/actions.csv')
    gb_actions = GridOptionsBuilder.from_dataframe(actions)
    gb_actions.configure_default_column(editable=False)
    gb_actions.configure_selection(selection_mode='single',
                                   use_checkbox=True)
    ag_actions = AgGrid(data=actions,
                        gridOptions=gb_actions.build(),
                        fit_columns_on_grid_load=True,
                        update_on="selectionChanged")

    selectedAction = '-'
    if len(ag_actions['selected_rows']) > 0:
        selectedAction = ag_actions['selected_rows'][0]['Actions']

with secondRow[4]:
    annotations = pd.read_csv('data/annotations.csv')
    gb_annotations = GridOptionsBuilder.from_dataframe(annotations)
    gb_annotations.configure_default_column(editable=True)
    ag_annotations = AgGrid(data=annotations,
                            gridOptions=gb_annotations.build(),
                            fit_columns_on_grid_load=True)

with secondRow[3]:
    submitAnnotation = st.button('submit annotation')
    if submitAnnotation:
        newAnnotation = pd.DataFrame({
            annotations.columns[0]: [selectedTeam],
            annotations.columns[1]: [selectedPlayer],
            annotations.columns[2]: [selectedAction],
            annotations.columns[3]: [secondsOfVideoPlayed // 60],
            annotations.columns[4]: [secondsOfVideoPlayed % 60],
            annotations.columns[5]: ['-'],
            annotations.columns[6]: ['-'],
            annotations.columns[7]: ['-'],
            annotations.columns[8]: ['-']
        })
        pd.concat([ag_annotations.data, newAnnotation]).to_csv('data/annotations.csv')

with firstRow[1]:
    # @st.experimental_singleton
    def get_cv2_video(url):
        ydl = YoutubeDL()
        video_data = ydl.extract_info(url, download=False)

        # link with video and audio
        direct_video_url = [_format['url'] for _format in video_data['formats']
                            if _format['acodec'] != 'none' and _format['vcodec'] != 'none'][-1]

        capture = cv2.VideoCapture(direct_video_url)

        return capture


    if 'capturedVideo' not in st.session_state:
        st.session_state['capturedVideo'] = get_cv2_video(videoURL)
    capturedVideo = st.session_state['capturedVideo']


    @st.cache(max_entries=1)
    def get_frame(played):
        capturedVideo.set(cv2.CAP_PROP_POS_MSEC, played * 1000)
        check, frame = capturedVideo.read()
        if check:
            return Image.fromarray(frame)
        else:
            return None


    canvas_frame = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
        background_image=get_frame(secondsOfVideoPlayed),
        update_streamlit=True,
        drawing_mode='polygon',
        stroke_width=3
    )

# updated = ag_players['data']
# updated.to_csv('data/players.csv', index=False)
