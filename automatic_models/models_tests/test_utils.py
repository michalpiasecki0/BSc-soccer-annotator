import numpy as np
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







