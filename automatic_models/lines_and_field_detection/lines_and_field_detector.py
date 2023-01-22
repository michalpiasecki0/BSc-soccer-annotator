"""
Line & Field Detector, which is responsible for Homography calculation, Lines Detection and Field Detection.
All code in this folder except for `lines_and_field_detector` was implemented by authors of this repository.
https://github.com/vcg-uvic/sportsfield_release?fbclid=IwAR3_eErOdxlP2QN8KujvDP1sXGRm2knhx112mLx77Z0phlQGLMcd9weDW2w
"""
import json
import cv2
from dataclasses import dataclass
from typing import Optional, Dict, Tuple

import torch
from shapely.geometry import LineString, Polygon

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
    name: str = 'Optimization Based Image Registration'
    template_path: str = PATH_TO_AUTOMATIC_MODELS + '/lines_and_field_detection/data/template.png'
    lines_coordinates_path = PATH_TO_AUTOMATIC_MODELS + '/lines_and_field_detection/data/lines_coordinates.json'
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
    optim_iters: int = 20
    optim_method: str = 'stn'
    optim_type: str = 'adam'
    prevent_neg: str = 'sigmoid'
    warp_dim: int = 8
    warp_type: str = 'homography'
    constant_var_use_cuda: bool = False
    torch_backends_cudnn_enabled: bool = False
    desired_homography: str = 'optim'


class LineDetector:
    """
    LineDetector is responsible for detecting lines, segmenting field and calculating homography from given image.
    For an image input (image_width x image_height x channels) LineDetector outputs following objects:
    1) homography matrix, which defines transformation from input image to bird's view football pitch image
    1) detected_field: numpy array with points corresponding to field polygon: shape [Nx2]
    2) detected_lines: dictionary with all detected lines defined by their two extremities
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
                 model_config: Optional[Dict] = None):

        self.config = LineDetectorConfig()
        self.image_array = image_array
        if model_config:
            for key, value in model_config.items():
                setattr(self.config, key, value)

        constant_var.USE_CUDA = self.config.constant_var_use_cuda
        torch.backends_cudnn_enabled = self.config.torch_backends_cudnn_enabled

        self.template_image = cv2.imread(self.config.template_path)
        with open(self.config.lines_coordinates_path, 'r') as f:
            self.template_line_coords = json.load(f)
        self.homography: Optional[np.ndarray] = None
        self.homography_inv: Optional[np.ndarray] = None
        self.lines = {}
        self.field: Optional[np.ndarray] = None

    def __call__(self) -> Tuple[np.ndarray, Dict, np.ndarray, Dict]:
        """
        Perform operations on input image using homography method. Method updates instance field, lines and homography
        attributes and returns them in particular order.
        :return: tuple (detected_field, detected_lines, homography, config)
        """
        if self.config.desired_homography not in ['orig', 'optim']:
            raise Exception('Invalid homography type. Please choose from {orig, optim}')
        if self.config.desired_homography == 'orig':
            self.config.optim_iters = 1

        self.get_orig_optim_homography(desired=self.config.desired_homography)

        # warped_img = self.produce_images_on_homography(self.homography) u

        self.get_field()
        self.get_lines()

        return self.field, self.lines, self.homography_inv.tolist(), self.config

    def get_field(self) -> np.ndarray:
        """
        Find polygons which define pitch shape on a video frame.
        """
        out_shape = (self.image_array.shape[1], self.image_array.shape[0])
        template_shape = (self.template_image.shape[1], self.template_image.shape[0])
        points_template = np.array([[0, 0], [template_shape[0], 0],
                                    [template_shape[0], template_shape[1]], [0, template_shape[1]]])
        polygon_mapped = Polygon(np.apply_along_axis(
            lambda k: self._map_template_point_to_frame(k, H_inv=self.homography_inv, out_shape=out_shape,
                                                        template_shape=template_shape), axis=1, arr=points_template))
        polygon_frame = Polygon([[0, 0], [out_shape[0], 0], [out_shape[0], out_shape[1]], [0, out_shape[1]]])
        coords = np.array(polygon_frame.intersection(polygon_mapped).exterior.coords.xy).transpose()
        if coords.size > 0:
            self.field = coords.astype(int).tolist()
            return coords
        else:
            return None

    def get_lines(self):
        """
        Map template lines to frame.
        """
        for name, coords in self.template_line_coords.items():
            new_coords = self._map_line_to_frame(line_point_1=np.array(coords[0]),
                                                 line_point_2=np.array(coords[1]),
                                                 h_inv=self.homography_inv,
                                                 out_shape=(self.image_array.shape[1], self.image_array.shape[0]),
                                                 template_shape=(self.template_image.shape[1],
                                                                 self.template_image.shape[0]))
            if new_coords is not None:
                self.lines[name] = [[int(new_coords[0, 0]), int(new_coords[0, 1])],
                                    [int(new_coords[1, 0]), int(new_coords[1, 1])]]

    def get_orig_optim_homography(self, desired: str = 'orig'):
        """
        Calculate homography using one of t
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
            self.homography = orig_homography.detach().numpy()
        elif desired == 'optim':
            self.homography = optim_homography.detach().numpy()
        self.homography_inv = np.linalg.inv(self.homography)

    def produce_images_on_homography(self, homography: torch.Tensor):
        """
        Produce image with lines and field, having homography matrix
        :param homography: homography matrix
        :return: Transforomed image
        """
        if isinstance(homography, np.ndarray):
            homography = torch.Tensor(homography)
        original_array = self.image_array.copy()
        original_array = cv2.cvtColor(original_array, cv2.COLOR_BGR2RGB) / 255.0
        out_shape = original_array.shape[0:2]

        template_image = self._preprocess_template_image(ask_configs=False)

        warped_tmp_orig = warp.warp_image(template_image, homography, out_shape=out_shape)[0]
        warped_tmp_orig = utils.torch_img_to_np_img(warped_tmp_orig)

        return warped_tmp_orig


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

    @staticmethod
    def _check_point_within_boundaries(point: np.ndarray,
                                       boundaries: tuple):
        """
        Check if point lies inside an image of shape boundaries[0] x boundaries[1]
        More precisely, check if point[0] is in [0. boundaries[0], point[1] is in [0, boundaries[1]
        :param point: np.array ([x, y])
        :param boundaries; tuple (x_buondary, y_buondary):
        :returns: True if point inside, False otherwise
        """
        return (point[0] > 0) and (point[0] <= boundaries[0]) and (point[1] >= 0) and (point[1] < boundaries[1])

    def _map_template_point_to_frame(self,
                                     frame_point: np.ndarray,
                                     H_inv: np.ndarray,
                                     out_shape: tuple,
                                     template_shape=(1050, 680)) -> np.ndarray:
        """
        Map frame point from pitch template to frame.
        :param frame_point: (x, y) point from template
        :param H_inv: homography matrix from template to frame (np.array with shape (3,3))
        :param out_shape: video frame shape: (width x height)
        :param template_shape: template shape: (width x height)
        :returns: np.array([x_new, y_new])
        """
        assert isinstance(frame_point, np.ndarray)

        # moving frame_point to [-0.5, 0.5] range
        x = frame_point[0] / template_shape[0] - 0.5
        y = frame_point[1] / template_shape[1] - 0.5
        xy = np.array([x, y, 1])
        xy_warped = np.matmul(H_inv, xy)[0]
        xy_warped, z_warped = xy_warped[0:2], xy_warped[2]
        xy_warped = 2 * xy_warped / (z_warped + 1e-8)
        x_warped = (xy_warped[0] * 0.5 + 0.5) * out_shape[0]
        y_warped = (xy_warped[1] * 0.5 + 0.5) * out_shape[1]
        return np.array([x_warped, y_warped])

    def _map_line_to_frame(self,
                           line_point_1: np.ndarray,
                           line_point_2: np.ndarray,
                           h_inv: np.ndarray,
                           out_shape: tuple,
                           template_shape=(1050, 680)) -> Optional[np.array]:
        """
        Map line from template (more precisely its two extremities) onto frame using homography.
        :param line_point_1: np.array([x, y]): coordinates of first extremity
        :param line_point_2: np.array([x, y]): coordinates of second extremity
        :param h_inv: homography matrix from template to frame
        :param out_shape: video frame shape: (width x height)
        :param template_shape: template shape: (width x height)
        :returns: if both extremities are mapped withing new frame they are returned, Otherwise, function tries to find
        extremities on a new frame. If no part of line was mapped onto frame, None is returned.
        """
        point_1_new = self._map_template_point_to_frame(line_point_1,
                                                        H_inv=h_inv,
                                                        out_shape=out_shape,
                                                        template_shape=template_shape)
        point_2_new = self._map_template_point_to_frame(line_point_2,
                                                        H_inv=h_inv,
                                                        out_shape=out_shape,
                                                        template_shape=template_shape)
        flag_1 = self._check_point_within_boundaries(point_1_new, out_shape)
        flag_2 = self._check_point_within_boundaries(point_2_new, out_shape)
        if flag_1 and flag_2:
            # both extremities are mapped inside frame so they define line on frame
            return np.array([point_1_new, point_2_new])
        else:
            # either part of line was mapped onto new frame or nothing
            line = LineString([point_1_new, point_2_new])
            polygon = Polygon([(0, 0), (out_shape[0], 0), (out_shape[0], out_shape[1]), (0, out_shape[1])])
            intersection_points = np.array(polygon.intersection(line).coords.xy).transpose()
            return intersection_points if intersection_points.size > 0 else None

