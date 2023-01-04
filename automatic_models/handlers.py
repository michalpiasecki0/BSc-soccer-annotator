import json
import numpy as np
import cv2
import dataclasses
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from automatic_models.extra_utils.helpers import divide_video_into_frames
from automatic_models.lines_and_field_detection.lines_and_field_detector import LineDetector
from automatic_models.object_detection.object_detector import ObjectDetector


class VideoHandler:
    """
    VideoHandler is responsible for high level interaction between video and models.
    Parameters:
    :param video_path: path to video
    :param desired_frequency: desired amount of frames per second
    """
    def __init__(self,
                 video_path: str,
                 desired_frequency: float,
                 output_path: str,
                 starting_point: float = 0,
                 saving_strategy: str = 'overwrite',
                 models_config_path: str = None):

        if not Path(video_path).exists():
            raise Exception(f"Video path {video_path} does not exist.")

        self.model_configs = {}
        if models_config_path:
            with open(models_config_path, 'r') as f:
                try:
                    self.model_configs = json.load(f)
                except FileNotFoundError:
                    print(f'File {models_config_path} does not exist.')
                    self.model_configs = {}
                except json.JSONDecodeError:
                    print(f'Unable to update models from {models_config_path}.\n'
                          f'Model Configuration file is not formatted properly.')
                    self.model_configs = {}

        self.video_path = video_path
        self.output_path = output_path
        if not Path(output_path).exists():
            Path(output_path).mkdir(parents=True)
        self.desired_frequency = desired_frequency
        self.starting_point = starting_point
        self.frames: Optional[Dict[int, np.ndarray]] = None
        self.image_handlers: Optional[Dict[int, ImageHandler]] = None
        self.results = {'events': {},
                        'lines': {},
                        'fields': {},
                        'homographies': {},
                        'objects': {}}
        self.meta_data = {'frequency': desired_frequency}
        self.saving_strategy = saving_strategy

    def save_results_to_files(self) -> None:
        """
        Save obtained results to files in an output folder.
        """
        def get_files_naming(output_path: Path, data_type: str, strategy: str) -> str:
            file_name = f'{str(output_path / data_type)}'
            if strategy == 'add':
                file_name += f'_{datetime.now().strftime("%m_%d_%Y_%H:%M:%S")}'
            file_name += '.json'
            return file_name

        assert self.saving_strategy in ['overwrite', 'add']
        general_path = Path(self.output_path)
        for name in ['homographies', 'objects', 'lines', 'fields']:
            if self.results[name]:
                file_path = get_files_naming(general_path, name, self.saving_strategy)
                with open(file_path, 'w') as f:
                    json.dump(self.results[name], f)
            with open(get_files_naming(general_path, 'meta_data', self.saving_strategy), 'w') as f:
                json.dump(self.meta_data, f)

    def save_one_result(self, result_type: str,):
        general_path = Path(self.output_path)
        result = self.results[result_type]
        if not result:
            print('Nothing is saved. These results have not been generated yet.')
        else:
            path_to_resources = (general_path / result_type)
            if not path_to_resources.exists():
                path_to_resources.mkdir(parents=True)
            for idx, value in result.items():
                if isinstance(value, np.ndarray):
                    np.save(str(path_to_resources / str(idx)) + '.npy', value)

    def divide_video(self):
        """
        Divide given video into equally spaced frames.
        :return:
        """
        if self.frames:
            print('Video is already divided')
        else:
            self.frames, self.image_handlers = {}, {}
            self.frames = divide_video_into_frames(video_path=self.video_path,
                                                   output_folder=self.output_path + '/raw_frames',
                                                   desired_frequency=self.desired_frequency)
            for idx, frame in self.frames.items():
                self.image_handlers[self.starting_point + idx * (1 / self.desired_frequency)] = \
                    ImageHandler(idx=self.starting_point + idx * (1 / self.desired_frequency), image_array=frame)

    def annotate_events(self):
        """TO DO"""
        pass

    def detect_lines_and_fields(self):
        if self.results['fields']:
            print('Fields and lines are already calculated')
        else:
            if self.image_handlers:
                for idx, image_handler in self.image_handlers.items():
                    field, lines, homography, config = \
                        image_handler.get_lines_field_and_homography(
                            model_config=self.model_configs.get('lines_field_homo_model'))
                    self.results['fields'][idx] = field
                    self.results['lines'][idx] = lines
                    self.results['homographies'][idx] = homography
                    print(f'{idx} was processed.')
                    if not self.meta_data.get('lines_field_homo_model'):
                        # add object detection config to meta-data
                        model_dict = dataclasses.asdict(config)
                        for name in ['template_path', 'out_dir']:
                            del model_dict[name]
                        self.meta_data['lines_field_homo_model'] = model_dict
            else:
                print('You must divide video and create image handlers before invoking Lines & FIeld Detection')

    def detect_objects(self):
        """
        Detect players on a field
        """
        if self.results['objects']:
            print('Fields and lines are already calculated')
        else:
            if self.image_handlers:
                for idx, image_handler in self.image_handlers.items():
                    objects, config = \
                        image_handler.get_objects(model_config=self.model_configs.get('object_detection_model'))
                    if not self.meta_data.get('object_detection_model'):
                        # add object detection config to meta-data
                        self.meta_data['object_detection_model'] = dataclasses.asdict(config)

                    self.results['objects'][idx] = objects
                    print(f'{idx} was processed.')
            else:
                print('You must divide video and create image handlers before invoking Object Detection')


class ImageHandler:
    def __init__(self,
                 idx: Optional[str],
                 image_path: Optional[str] = None,
                 image_array: Optional[np.ndarray] = None):
        self.idx = idx
        self.image_path = image_path
        self.image_array = cv2.imread(image_path) if (image_path and not image_array) else image_array
        self.time = None
        self.lines = None
        self.field = None
        self.homography = None
        self.objects = None

    def get_objects(self, model_config: Optional[Dict] = None):
        object_detector = ObjectDetector(idx=self.idx,
                                         image_array=self.image_array,
                                         model_config=model_config)
        object_detector()
        self.objects = object_detector.results
        return self.objects, object_detector.config

    def get_lines_field_and_homography(self, model_config: Optional[Dict] = None):
        line_detector = LineDetector(image_array=self.image_array,
                                     model_config=model_config)
        self.field, self.lines, self.homography, config = line_detector()
        return self.field, self.lines, self.homography, config


