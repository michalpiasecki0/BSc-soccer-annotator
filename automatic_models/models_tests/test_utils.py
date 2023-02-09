import numpy as np
import pandas as pd
import json
import os
import matplotlib.pyplot as plt
from typing import Optional
from automatic_models.extra_utils.constants import PATH_TO_AUTOMATIC_MODELS

with open(os.path.join(PATH_TO_AUTOMATIC_MODELS, 'lines_and_field_detection', 'data', 'lines_coordinates.json')) as f:
    LINES_DICT = json.load(f)

def preprocess_labels_soccernet(labels: dict) -> dict:
    """
    Transform Labels-v3.json to have format for testing
    """
    result = {'players': {},
              'balls': {},
              'lines': {}}
    for frame_id, frame in labels['actions'].items():
        idx = str.split(frame_id, sep='.')[0]
        result['players'][idx], result['balls'][idx] = get_players_ball(frame['bboxes'])
        result['lines'][idx] = get_all_lines(frame['lines'])
    return result

def preprocess_csv_soccernet(soccernet_table: pd.DataFrame):
    """Convert csv located in each SNMOT folder to get players and balls"""
    result = {'players': {},
              'balls': {}}
    idxs = soccernet_table['frame_id'].unique()
    for idx in idxs:
        constrained_players = soccernet_table[(soccernet_table['frame_id'] == idx) & (soccernet_table['class'] == 'PERSON')]
        constrained_balls = soccernet_table[(soccernet_table['frame_id'] == idx) & (soccernet_table['class'] == 'Ball')]
        constrained_players.apply(lambda k: result[''], axis=1)




def get_players_ball(bboxes: list):
    """
    Get player bounding boxes and football ball
    """
    players, ball = [], []
    for item in bboxes:
        if item['class'] == 'Ball':
            ball.append(get_bbox_from_two_points(item['points']))
        else:
            players.append(get_bbox_from_two_points(item['points']))
    return players, ball


def get_bbox_from_two_points(points: dict):
    """
    Convert dict with two points to numpy array with four points.
    """
    return [(points['x1'], points['y1']),
            (points['x1'], points['y2']),
            (points['x2'], points['y2']),
            (points['x2'], points['y1'])]


def get_bbox_from_two_points_model_notation(item: dict):
    return [(item['x_top_left'], item['y_top_left']),
            (item['x_top_left'], item['y_bottom_right']),
            (item['x_bottom_right'], item['y_bottom_right']),
            (item['x_bottom_right'], item['y_top_left'])]


def get_all_lines(lines: list):
    """
    Get lines from json in convenient format
    """
    result = dict()
    for line in lines:
        if str.upper(line['class']) in LINES_DICT:
            result[str.upper(line['class'])] = \
                [(line['points'][0], line['points'][1]), (line['points'][2], line['points'][3])]
    return result


def get_lines_from_test(lines: dict, width=540, height=960):
    result = dict()
    for line_name, points in lines.items():
        if str.upper(line_name) in LINES_DICT:
            result[str.upper(line_name)] = \
                [
                    [points[0]['x'] * height, points[0]['y'] * width],
                    [points[1]['x'] * height, points[1]['y'] * width]
                ]
    return result


def show_save_image_with_lines(img_array: np.ndarray,
                               lines: dict,
                               save_fig_path: Optional[str],
                               fig_size: tuple = (12, 7),
                               color: str = 'royalblue'
                               ):
    """
    Show image with predicted lines on it.
    If save_fig provided image is saved in some location
    """
    rgb = img_array[:, :, ::-1].copy()  # convert image from bgr to rgb

    fig = plt.figure(frameon=False)
    fig.set_size_inches(12, 7)

    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)
    ax.imshow(rgb, aspect='auto')
    for line_name, coords in lines.items():
        plt.plot([coords[0][0], coords[1][0]], [coords[0][1], coords[1][1]], linewidth=3, color=color)
    if save_fig_path:
        fig.savefig(save_fig_path)


def convert_gameinfo_ini(gameinfo: list):
    """
    Convert gameinfo.ini to get mappings from numbers to object type
    """

    mapping = {}
    for line in gameinfo:
        if line.find('trackletID_') != -1:
            number = line.split('trackletID_')[1].split('=')[0]
            if line.find('ball') != -1:
                mapping[number] = 'Ball'
            else:
                mapping[number] = 'PERSON'
    return mapping


def convert_and_save_txt_to_csv(folder_path: str,
                                output_folder: Optional[str] = None):
    """
    Convert gt.txt and gameinfo.ini (located in each SNMOT folder) to csv table
    """
    with open(os.path.join(folder_path, 'gameinfo.ini')) as f:
        game_info = f.readlines()
    mapping = convert_gameinfo_ini(game_info)

    gt = pd.read_csv(os.path.join(folder_path, 'gt.txt'), header=None)
    gt = gt.iloc[:, 0:6]
    gt.columns = ['frame_id', 'track_id', 'top_left_coordinate', 'top_y_coordinate', 'width', 'height']
    gt['x_top_left'] = gt['top_left_coordinate']
    gt['y_top_left'] = gt['top_y_coordinate']
    gt['x_bottom_right'] = gt['top_left_coordinate'] + gt['width']
    gt['y_bottom_right'] = gt['top_y_coordinate'] + gt['height']
    gt['class'] = gt['track_id'].apply(lambda k: mapping[str(k)])
    gt['polygon'] = gt.apply(lambda k:
                             [(k['x_top_left'], k['y_top_left']),
                              (k['x_bottom_right'], k['y_top_left']),
                              (k['x_bottom_right'], k['y_bottom_right']),
                              (k['x_top_left'], k['y_bottom_right'])],
                             axis=1)

    gt = gt.loc[:, ['frame_id', 'class', 'polygon']]
    if output_folder:
        gt.to_csv(os.path.join(output_folder, 'gt.csv'))
    return gt


def get_bbox_lists_from_csv(dataframe: pd.DataFrame, obj_type = str):
    """

    """
    assert obj_type in ['PERSON', 'Ball']
    results = {}
    filtered = dataframe[dataframe['class'] == obj_type]
    idxs = filtered['frame_id'].unique()
    for idx in idxs:
        singled = filtered[filtered['frame_id'] == idx]
        results[idx] = singled['polygon'].tolist()
    return results



