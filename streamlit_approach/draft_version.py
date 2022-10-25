import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, DataReturnMode, GridUpdateMode
import pandas as pd
from streamlit_drawable_canvas import st_canvas
from PIL import Image

# streamlit configs
st.set_page_config(layout="wide")

# title
st.title('BS Soccer Annotator')

# video
video_columns = st.columns([0.3,1,0.3])
with video_columns[1]:
       video_file = open('data/proper.mp4', 'rb')
       video_bytes = video_file.read()
       st.video(video_bytes)

# table
st.subheader('Tables')
columns = st.columns([1,0.5,1])
with columns[0]:
    players = pd.read_csv('data/players.csv')
    players.set_index('_')
    gb = GridOptionsBuilder.from_dataframe(players)
    gb.configure_default_column(editable=True)

    ag_players = AgGrid(players,
               gridOptions=gb.build(),
               allow_unsafe_jscode=True,
               reload_data=False)

with columns[1]:
    actions = pd.read_csv('data/actions.csv')
    gb_actions = GridOptionsBuilder.from_dataframe(actions)
    gb_actions.configure_default_column(editable=False)
    ag_actions = AgGrid(data=actions,
                        gridOptions=gb_actions.build(),
                        update_on="selectionChanged")
    st.write(ag_players['selected_rows'])

with columns[2]:
    combined = pd.read_csv('data/combined.csv')
    gb_combined = GridOptionsBuilder.from_dataframe(combined)
    gb_combined.configure_default_column(editable=True)
    ag_combined = AgGrid(data=combined,
                         gridOptions=gb_combined.build())

other_columns = st.columns([1,1])
with other_columns[0]:
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
        background_image=Image.open('data/football_pitch.png'),
        update_streamlit=True,
        drawing_mode='point',
        key="canvas",
        point_display_radius=0.3
    )
with other_columns[1]:
    if canvas_result.json_data is not None:
        objects = pd.json_normalize(canvas_result.json_data["objects"])  # need to convert obj to str because PyArrow
        for col in objects.select_dtypes(include=['object']).columns:
            objects[col] = objects[col].astype("str")
            print(objects.columns)
        st.dataframe(objects.loc[:, ['left', 'top']])


updated = ag_players['data']
updated.to_csv('data/players.csv', index=False)
