"""General helpers for video processing"""
import math
import cv2
import numpy as np
import shutil
from typing import Tuple, Optional, List, Dict
from pathlib import Path


def divide_video_into_frames(video_path: str,
                             output_folder: str,
                             desired_frequency: Optional[int] = None) -> List:
    """
    Divide video file into images with desired frequency rate
    :param video_path: path to video
    :param desired_frequency: number of frames per second generated by splitter, if N
    :param output_folder: location to save new images
    :return: None
    """
    try:
        capture = cv2.VideoCapture(video_path)
    except:
        print('No video for a given path.')

    fps = capture.get(cv2.CAP_PROP_FPS)

    if not desired_frequency:
        # if desired frequency is not provided, original video fps is chosen
        desired_frequency = fps
    if (fps / desired_frequency) < 1:
        raise Exception("""Desired fps is bigger than initial fps. Please change desired_frequency parameter to smaller
                        value""")

    output_path = Path(output_folder)
    if output_path.exists():
        # if folder already exists, we clear it up
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True)

    frames: Dict[str, np.ndarray] = {}
    frame_number = 0
    iterator = 0

    success, frame = capture.read()
    while success:
        if iterator == math.floor(fps / desired_frequency):
            cv2.imwrite(f'{output_folder}/frame_{frame_number}.jpg', frame)
            frames[frame_number] = frame
            frame_number += 1
            iterator = 0
        else:
            iterator += 1
        success, frame = capture.read()
    return frames

def mask_defined_color_pixels(image: np.ndarray,
                              convert_format: str,
                              min_range: Tuple = (36, 25, 25),
                              max_range: Tuple = (70, 255, 255)
                              ) -> np.ndarray:
    """
    Process image (loaded as opencv np.array) to get only green regions
    Following bounds work for colors in hsv:
    green (HSV): (36, 25, 25) - (70, 255, 255)
    white (HLS): (0, 250, 0) - (255, 255, 255)
    white
    :param image: image as a np.ndarray following cv2 convention
    :param min_range: minimum value of a pixel to be classified as green (in HSV scale)
    :param max_range: maximum value of a pixel to be classified as green (in HSV scale)
    :param convert_format: what format should BGR be transformed into (possible: HSV, HSL)
    :return: grayscale image with blue pixels indicating green pixels and black pixels rest
    """
    if convert_format not in ('HSV', 'HLS'):
        raise Exception('convert format incorrectly defined')
    if convert_format == 'HSV':
        converted = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    elif convert_format == 'HLS':
        converted = cv2.cvtColor(image, cv2.COLOR_BGR2HLS)


    mask = cv2.inRange(converted, min_range, max_range)

    im_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    im_gray[mask > 0] = 255
    im_gray[mask == 0] = 0
    return im_gray

def write_list_to_txt(elements: list,
                      output_path: str) -> None:
    with open(output_path, 'w') as f:
        for element in elements:
            f.write(f'{element}\n')

def convert_numpy_to_bitmask(array: np.ndarray) -> np.ndarray:
    """
    Convert image into bit array, where 1 indicates pixels with non-zero values
    :param array: numpy image, either grayscale or coloured
    :return: bitm
    """
    assert isinstance(array, np.ndarray)
    if len(array.shape) == 3:
        return np.any(array > 0, axis=2).astype(np.int)
    elif len(array.shape) == 2:
        return (array > 0).astype(np.int)

if __name__ == '__main__':
    divide_video_into_frames(video_path='./../data/barcelona_valencia.mp4',
                             desired_frequency=0.01,
                             output_folder='/home/skocznapanda/programming/BSc-soccer-annotator/automatic_models/notebooks/frames')
