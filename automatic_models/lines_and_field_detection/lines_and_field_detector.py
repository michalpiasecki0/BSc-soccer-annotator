"""
Line & Field Detector, which is responsible for Lines Detection, Field Detection, Homography calculation
"""
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import os
import cv2

from lines_and_field_detection.utils import utils, warp, image_utils, constant_var
from lines_and_field_detection.models import end_2_end_optimization
from lines_and_field_detection.utils.image_utils import *
from extra_utils.helpers import convert_numpy_to_bitmask
from extra_utils.constants import PATH_TO_AUTOMATIC_MODELS


@dataclass
class LineDetectorConfig:
    """
    Dataclass used for storing model configuration for Lines and Field detection
    """
    out_dir: str = PATH_TO_AUTOMATIC_MODELS + '/lines_and_field_detection/out'
    batch_size: int = 1
    coord_conv_template: bool = True
    error_model: str = 'loss_surface'
    error_target: str = 'iou_whole'
    guess_model: str = 'init_guess'
    homo_param_method: str = 'deep_homography'
    load_weights_error_model: str = 'pretrained_loss_surface'
    load_weights_upstream: str = 'pretrained_init_guess'
    lr_optim: float = 1e-5
    need_single_image_normalization: bool = True
    need_spectral_norm_error_model: bool = True
    need_spectral_norm_upstream: bool = False
    optim_criterion: str = 'l1loss'
    optim_iters: int = 30
    optim_method: str = 'stn'
    optim_type: str = 'adam'
    prevent_neg: str = 'sigmoid'
    template_path: str = PATH_TO_AUTOMATIC_MODELS + '/lines_and_field_detection/data/template.png'
    warp_dim: int = 8
    warp_type: str = 'homography'


class LineDetector:
    """
    LineDetector is responsible for detecting lines, segmenting field and calculating homography from given image.
    For an image input (image_width x image_height x channels) LineDetector outputs following objects:
    1) detected_field: numpy array with shape (image_width x image_height) containing 1 and 0's. 1: field, 0: no field
    2) detected_lines: numpy array with shape (image_width x image_height) containing 1 and 0's. 1: lines, 0: no lines
    3) homography: numpy array with shape [3x3] representing homography matrix
    This is achieved using architecture provided by Optimizing Through Learned Errors for Accurate Sports Field
    Registration - WACV 2020
    (https://github.com/vcg-uvic/sportsfield_release?fbclid=IwAR3_eErOdxlP2QN8KujvDP1sXGRm2knhx112mLx77Z0phlQGLMcd9weDW2w)

    Parameters for initialization:
    :param image_array: (width x height x channels) image in numpy array format. It is assumed that images are loaded
    with opencv package and therefore are in BGR format
    :param constant_var_use_cuda: boolean value indicating if cuda should be used (set False for CPU, true for GPU)
    :param torch_backend_cudnn_enabled: boolean value indicating if cuda is enabled (set False for CPU, true for GPU)
    :parma kwargs: keywords arguments, which changes default values in LineDetectorConfig
    """
    def __init__(self,
                 image_array: np.ndarray,
                 constant_var_use_cuda: bool = False,
                 torch_backends_cudnn_enabled: bool = False,
                 **kwargs):

        constant_var.USE_CUDA = constant_var_use_cuda
        torch.backends_cudnn_enabled = torch_backends_cudnn_enabled

        self.image_array = image_array
        self.config = LineDetectorConfig()
        for key, value in kwargs:
            self.config.key = value
        self.template_image = cv2.imread(self.config.template_path)

        self.homography: Optional[np.ndarray] = None
        self.lines: Optional[np.ndarray] = None
        self.field: Optional[np.ndarray] = None

    def __call__(self, desired_homography: str = 'orig'):
        """
        Perform operations on input image using homography method. Method updates instance field, lines and homography
        attributes and returns them in particular order.
        :param desired_homography: method for calculating homography. Possible options: 'orig', 'optim'
        :return: tuple (detected_field, detected_lines, homography)
        """
        if desired_homography not in ['orig', 'optim']:
            raise Exception('Invalid homography type. Please choose from {orig, optim}')
        if desired_homography == 'orig':
            self.config.optim_iters = 1

        self.get_orig_optim_homography(desired=desired_homography)
        warped_img = self.produce_images_on_homography(self.homography)
        self._get_field(warped_img)
        self._get_lines(warped_img)

        return self.field, self.lines, self.homography.detach().numpy().reshape((3,3))

    def _get_field(self, warped_image: np.ndarray) -> np.ndarray:
        """
        Create bit-image, segmenting field.
        :param warped_image: image after applying models
        :return: np.array (image_width x image_height) with 1 values indicating field
        """
        only_field = warped_image.copy()
        only_field[only_field > 0] = 1
        self.field = convert_numpy_to_bitmask(only_field)

    def _get_lines(self, warped_image, threshold_value_for_red_channel: int = 0.7) -> np.ndarray:
        """
        Create bit-image segmenting lines.
        :param warped_image: image after applying models
        :param threshold_value_for_red_channel: minimal pixel value in red channel to classified as line
        :return: np.array (image_width x image_height) with 1 values indicating field
        """
        lines = warped_image.copy()
        mask = lines[:, :, 0] < threshold_value_for_red_channel
        lines[mask] = 0
        lines[~mask] = 1
        self.lines = convert_numpy_to_bitmask(lines)

    def produce_images_on_homography(self, homography):
        """
        Produce image with lines and field, having homography matrix
        :param homography: homography matrix
        :return: Transforomed image
        """
        original_array = self.image_array.copy()
        original_array = cv2.cvtColor(original_array, cv2.COLOR_BGR2RGB) / 255.0
        out_shape = original_array.shape[0:2]

        template_image = self._preprocess_template_image(ask_configs=False)

        warped_tmp_orig = warp.warp_image(template_image, homography, out_shape=out_shape)[0]
        warped_tmp_orig = utils.torch_img_to_np_img(warped_tmp_orig)

        return warped_tmp_orig

    def get_orig_optim_homography(self, desired: str = 'orig'):
        """
        Calculate homography
        :param desired: homography type. Possible options: {'orig', 'optim'}
        :return: None
        """
        if desired not in ['orig', 'optim']:
            raise Exception('Invalid homography argument. Please choose from {orig, optim}')
        goal_image = self._preprocess_field_image()
        template_image = self._preprocess_template_image(ask_configs=True)
        e2e = end_2_end_optimization.End2EndOptimFactory.get_end_2_end_optimization_model(self.config)
        orig_homography, optim_homography = e2e.optim(goal_image[None], template_image)
        if desired == 'orig':
            self.homography = orig_homography
        elif desired == 'optim':
            self.homography = optim_homography


    def _preprocess_field_image(self):
        """
        Preprocess image containing field, so it is ready to be used by models
        :return: transformed image
        """
        goal_image = cv2.cvtColor(self.image_array, cv2.COLOR_BGR2RGB)
        goal_image = goal_image.astype(np.uint8)
        goal_image = cv2.resize(goal_image, (256, 256))

        goal_image = utils.np_img_to_torch_img(goal_image)
        if self.config.need_single_image_normalization:
            goal_image = image_utils.normalize_single_image(goal_image)
        return goal_image

    def _preprocess_template_image(self, ask_configs: bool = False):
        """
        Preprocess template image (image containing football field top view), so it is ready to be used by models
        :param ask_configs: boolean value, if used method performs operations based on LineDetectorConfig
        :return: transformed image
        """
        template_image = cv2.cvtColor(self.template_image, cv2.COLOR_BGR2RGB)
        template_image = template_image / 255.0
        if ask_configs:
            if self.config.coord_conv_template:
                template_image = image_utils.rgb_template_to_coord_conv_template(template_image)
            template_image = utils.np_img_to_torch_img(template_image)
            if self.config.need_single_image_normalization:
                template_image = image_utils.normalize_single_image(template_image)
        else:
            template_image = image_utils.rgb_template_to_coord_conv_template(template_image)
            template_image = utils.np_img_to_torch_img(template_image)

        return template_image
