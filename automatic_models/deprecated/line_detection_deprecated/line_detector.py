import numpy as np
import cv2
import matplotlib.pyplot as plt
from pathlib import Path
from skimage.feature import canny
from skimage.transform import probabilistic_hough_line
from typing import Tuple
from automatic_models.extra_utils.helpers import write_list_to_txt

def detect_all_one_image(img_path: np.ndarray,
                         save_folder: Path,
                         img_name: str):
    img = cv2.imread(img_path)
    straight_lines = detect_straight_lines(img)

    if not save_folder.exists():
        save_folder.mkdir(parents=True)

    write_list_to_txt(straight_lines, f'{save_folder}/{img_name}.txt')
    save_img_and_lines(img, straight_lines, f'{save_folder}/{img_name}.jpg')



def detect_straight_lines(img: np.ndarray,
                          canny_sigma: int = 2,
                          canny_low_threshold: int = 1,
                          canny_high_threshold: int = 25,
                          hough_threshold: int = 10,
                          hough_min_line_length: int = 100,
                          hough_line_gap: int = 5):

    if len(img.shape) == 3:
        # make sure image is grayscale
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    edges = canny(img, canny_sigma, canny_low_threshold, canny_high_threshold)
    lines = probabilistic_hough_line(edges,
                                     threshold=hough_threshold,
                                     line_length=hough_min_line_length,
                                     line_gap=hough_line_gap)
    return lines

def save_img_and_lines(img: np.ndarray,
                       lines: Tuple,
                       output_file: str):
    fig, axes = plt.subplots(1, 2, figsize=(15, 5), sharex=True, sharey=True)
    ax = axes.ravel()

    ax[0].imshow(img, cmap='gray')
    ax[0].set_title('Input image')

    for line in lines:
        p0, p1 = line
        ax[1].plot((p0[0], p1[0]), (p0[1], p1[1]))
    ax[1].set_xlim((0, img.shape[1]))
    ax[1].set_ylim((img.shape[0], 0))
    ax[1].set_title('Probabilistic Hough')

    for a in ax:
        a.set_axis_off()

    plt.tight_layout()
    plt.savefig(output_file)


if __name__ == '__main__':
    img = cv2.imread('../data/barcelona_valencia_frames/raw_frames/frame_100.jpg')
    detect_all_one_image(img_path='../data/barcelona_valencia_frames/raw_frames/frame_100.jpg',
                         save_folder=Path('../data/barcelona_valencia_frames/lines'),
                         img_name=Path('../data/barcelona_valencia_frames/raw_frames/frame_100.jpg').stem)
