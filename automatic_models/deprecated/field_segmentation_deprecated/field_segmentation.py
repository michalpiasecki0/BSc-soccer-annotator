import cv2
import numpy as np
import alphashape
import matplotlib.pyplot as plt
from typing import Tuple
from skimage.morphology import area_opening, reconstruction, convex_hull_image
from skimage.filters import roberts
from skimage.feature import corner_harris, corner_peaks
from scipy import ndimage

from automatic_models.extra_utils.helpers import mask_defined_color_pixels


def perform_pipeline(image_file: str, output_direction: str) -> None:
    """
    Perform all operations for field segmentation on one image
    :param image_file: image direction
    :param output_direction:
    :return: None
    """
    img = cv2.imread(image_file)
    green = mask_defined_color_pixels(image=img,
                                      convert_format='HSV',
                                      min_range=(36, 25, 25),
                                      max_range=(70, 255, 255))
    without_noise = remove_noise(green)
    chull = convex_hull_image(without_noise)
    after_convex = without_noise.copy()
    after_convex[chull] = 255
    cv2.imwrite(output_direction, after_convex)





def remove_noise(grayscale_img: np.ndarray,
                 area_threshold: int = 400) -> np.ndarray:
    """
    Apply openning morphology to get rid of small white blobs and erosion to get rid of small black holes
    :param grayscale_img: numpy array with shape (nrow, ncol)
    :param area_threshold: threshold for preserving white objects
    :return: grayscale image without noise
    """

    modified = area_opening(image=grayscale_img,
                            area_threshold=area_threshold)
    seed = np.copy(modified)
    seed[1:-1, 1:-1] = modified.max()
    mask = modified
    modified = reconstruction(seed, mask, method='erosion')

    return modified

def get_polygon_coordinates(filtered_image: np.ndarray, apply_convex_hull: bool):
    if apply_convex_hull:
        chull = convex_hull_image(filtered_image)
        filtered_image[chull] = 255
    #edges = roberts(filtered_image)
    coords = corner_peaks(corner_harris(filtered_image), min_distance=5, threshold_rel=0.02)
    ## adding edges to end-of-pictures

    return coords

if __name__ == '__main__':
    perform_pipeline(image_file='images/frame_36.jpg',
                     output_direction='images/frame36_field_segmented.jpg')