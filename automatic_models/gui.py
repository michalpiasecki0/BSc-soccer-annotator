import os

import streamlit as st
import sys
from base64 import b64encode
from pathlib import Path
import json
from streamlit_player import st_player
from streamlit_player import st_player
#import vlc
#import tkinter as tk
#from tkVideoPlayer import TkinterVideo
sys.path.append('/home/skocznapanda/programming/BSc-soccer-annotator/automatic_models/object_detection/yolo')
sys.path.append('/home/skocznapanda/programming/BSc-soccer-annotator/automatic_models')
sys.path.append('/home/skocznapanda/programming/BSc-soccer-annotator')
from main import perform_models

def check_resource_exist(path: str):
    print(path)
    return Path(path).exists()
def show_files_and_video(args: list):
    video_path, results_path = args[0]. args[1]
    if check_resource_exist(video_path):
        st.video(video_path)
    if check_resource_exist(results_path):
        try:
            with open(results_path + '/meta_data.json') as f:
                meta_data = json.load(f)
            st.write(meta_data)
        except:
            pass

def local_video(path, mime="video/mp4"):
    data = b64encode(Path(path).read_bytes()).decode()
    return [{"type": mime, "src": f"data:{mime};base64,{data}"}]

st.title('Soccer automatic annotator')

with st.sidebar:
    st.subheader('Loading results')
    load_video_path = st.text_input(label='Path to a video',
                                    key='load_video',
                                    value='/home/skocznapanda/programming/BSc-soccer-annotator/automatic_models/data/test.mp4')
    load_results = st.text_input(label='Path to folder with results',
                                 key='load_results',
                                 value='/home/skocznapanda/programming/BSc-soccer-annotator/automatic_models/data/test.mp4')
    load_requirements = [load_video_path, load_results]

    if any(list(map(lambda k: len(k) == 0, load_requirements))):
        load_args = (0, 0)
    else:
        load_args = (load_video_path, load_requirements)
    load_button = st.button(label='Load results',
                            disabled=any(list(map(lambda k: len(k) == 0, load_requirements))),
                            on_click=show_files_and_video,
                            args=load_args)
    st.subheader('Generating results')
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

if video_path:
    if check_resource_exist(video_path):
        st.video(video_path)
    else:
        st.write('no video')
'''
root = tk.Tk()

videoplayer = TkinterVideo(master=root, scaled=True)
videoplayer.load(r"automatic_models/test.mp4")
videoplayer.pack(expand=True, fill="both")

videoplayer.play() # play the video

root.mainloop()
'''