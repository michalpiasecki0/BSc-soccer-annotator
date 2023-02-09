"""Script implements object detector, which detects players and ball from image."""

import numpy as np

from dataclasses import dataclass
from typing import Tuple, Dict, Optional, Any
from detect import detect_2
from labels import COCOLabels
from automatic_models.extra_utils.constants import PATH_TO_AUTOMATIC_MODELS

@dataclass
class ObjectDetectorConfig:
    """
    Dataclass used for storing object detection model configuration.
    """
    name: str = 'yolov7'
    objects_labels: Tuple = ('PERSON', 'SPORTS_BALL')
    device: str = 'cpu'
    weights_location = f'{PATH_TO_AUTOMATIC_MODELS}/object_detection/yolo/yolov7.pt'  # critical point, if yolo breaks
    conf_threshold: float = 0.25


class ObjectDetector:
    """
    ObjectDetector is responsible for detecting players and ball on a field.
    Currently Yolov7 is used to perform object detection.
    Link to repo with YoloV7: https://github.com/WongKinYiu/yolov7
    YOLO folder contains code implementation of YOLOV7.
    To use YOLO model for this task, I redesigned functions located in `yolo/detect.py` folder.
    In particular `detect_2.py` is implemented to use yolo inference to this project needs.
    Additionally private methods in this class serve to use YOLO for this task.

    """
    def __init__(self,
                 idx: int,
                 image_array: np.ndarray,
                 model_config: Optional[Dict] = None,
                 image_path: Optional[np.ndarray] = None,
                 xywh_format: bool = False) -> None:

        self.image_path = image_path
        self.idx = idx
        self.image_array = image_array
        self.xywh_format = xywh_format
        self.config = ObjectDetectorConfig()
        if model_config:
            for key, value in model_config.items():
                setattr(self.config, key, value)
        self.results = dict()
        self.output_image = None

    def __call__(self) -> Tuple[Dict, Any, Dict]:
        """
        When called, YOLODetector is called with specific arguments.
        :return: (dictionary_with_detected_objects, image_with_mapped_objects, configuration dict)
        """
        txt, image = detect_2(source=self.image_path,
                              img_array=self.image_array,
                              weights= self.config.weights_location,
                              img_size=640,
                              conf_threshold=self.config.conf_threshold,
                              device=self.config.device,
                              save_txt=True,
                              nosave=True,
                              xywh_format=self.xywh_format)
        self.results = self._map_raw_txt_to_dict(txt)
        self.output_image = image

        return self.results, self.output_image, self.config

    def _map_raw_txt_to_dict(self,
                             txt_raw: list,
                             labels=COCOLabels
                             ) -> Dict:
        """
        Map YOLO results in txt format to dictionary.
        :param txt_raw: list with results in txt format
        :param labels: labels for objects, by default COCOLabels are used
        :return: dictionary with detected objects, for each object class, location and confidence is calculated
        """
        if txt_raw:
            result_dict = {}
            for line in txt_raw:
                line = list(map(float, line))
                if labels(int(line[0])).name in self.config.objects_labels:
                    #  only saving PERSON AND SPORTSBALL DETECTED BY YOLO
                    if self.xywh_format:
                        result_dict[len(result_dict)] = {'class': labels(int(line[0])).name,
                                                         'x_center': line[1],
                                                         'y_center': line[2],
                                                         'width': line[3],
                                                         'height': line[4],
                                                         'confidence': line[5]}
                    else:
                        result_dict[len(result_dict)] = {'class': labels(int(line[0])).name,
                                                         'x_top_left': line[1],
                                                         'y_top_left': line[2],
                                                         'x_bottom_right': line[3],
                                                         'y_bottom_right': line[4],
                                                         'confidence': line[5]}

            return result_dict
        else:
            return None


