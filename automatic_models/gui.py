import os

import streamlit as st
import sys
sys.path.append('/home/skocznapanda/programming/BSc-soccer-annotator/automatic_models/object_detection/yolo')
sys.path.append('/home/skocznapanda/programming/BSc-soccer-annotator/automatic_models')
from main import perform_models

st.title('Soccer automatic annotator')

with st.sidebar:
    st.write(os.getcwd())
    video_path = st.text_input('Path to a video', value='automatic_models/data/test.mp4')
    output_folder = st.text_input('Path to save results', value='~/streamlit_test')
    config_path = st.text_input('Path to model configurations', value='automatic_models/models_config.json')
    frequency = st.text_input('Frequency', value='0.1')
    start_point = st.text_input('Starting point')
    requirements = [video_path, output_folder, frequency, start_point]
    if any(list(map(lambda k: len(k) == 0, requirements))):
        args = (0, 0, 0, 0)
    else:
        args = (video_path, output_folder, float(frequency), float(start_point))
    apply = st.button(label='generate results',
                      disabled=any(list(map(lambda k: len(k) == 0, requirements))),
                      on_click=perform_models,
                      args=args)


col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    print('dupa')