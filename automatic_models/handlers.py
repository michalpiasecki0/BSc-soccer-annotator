import numpy as np
import cv2
from pathlib import Path
from typing import List, Dict, Optional

from automatic_models.extra_utils.helpers import divide_video_into_frames
from automatic_models.lines_and_field_detection.lines_and_field_detector import LineDetector
#from detect import detect_2

class VideoHandler:
    def __init__(self, video_path: str,
                 output_path: str):
        self.video_path = video_path
        self.output_path = output_path
        self.frames: Optional[Dict[int, np.ndarray]] = None
        self.image_handlers: Optional[Dict[int, ImageHandler]] = None
        #self.events: Optional[Dict] = None
        #self.lines: Optional[Dict] = None
        #self.fields: Optional[Dict] = None
        #self.homographies: Optional[Dict] = None
        #self.objects_detected: Optional[Dict] = None
        self.results = {'events': {},
                        'lines': {},
                        'fields': {},
                        'homographies': {},
                        'objects': {}}
    def save_results_to_files(self):
        general_path = Path(self.output_path)

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




    def divide_video(self, desired_frequency: Optional[int] = None):
        if self.frames:
            print('Video is already divided')
        else:
            self.frames, self.image_handlers = {}, {}
            self.frames = divide_video_into_frames(video_path=self.video_path,
                                                   output_folder=self.output_path + '/raw_frames',
                                                   desired_frequency=desired_frequency)
            for idx, frame in self.frames.items():
                self.image_handlers[idx] = ImageHandler(idx = idx,
                                                        image_array=frame)

    def annotate_events(self):
        """TO DO"""
        pass

    def detect_lines_and_fields(self,
                                constant_var_use_cuda: bool = False,
                                torch_backends_cudnn_enabled: bool = False,
                                desired_homography: str = 'orig',
                                **kwargs):
        if self.results['fields']:
            print('Fields and lines are already calculated')
        else:
            if self.image_handlers:
                for idx, image_handler in self.image_handlers.items():
                    field, lines, homography = image_handler.get_lines_field_and_homography(
                        constant_var_use_cuda=constant_var_use_cuda,
                        torch_backends_cudnn_enabled=torch_backends_cudnn_enabled,
                        desired_homography=desired_homography
                    )
                    self.results['fields'][idx] = field
                    self.results['lines'][idx] = lines
                    self.results['homographies'][idx] = homography
                    #self.fields[idx] = field
                    #self.lines[idx] = lines
                    #self.homographies[idx] = homography
                    print(f'{idx} was processed.')
            else:
                print('You must divide video and create image handlers before invoking Lines & FIeld Detection')


    def detect_objects(self):
        """This part is not yet integrated with Handlers.
        Provisional usage is provided in object_detection/yolo/object_detection.py"""
        pass


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

    def __str__(self):
        pass

    def get_time(self):
        """TO DO """
        pass

    def get_objects(self):
        """This part is not yet integrated with Handlers.
        Provisional usage is provided in object_detection/yolo/object_detection.py"""
        pass


    def get_lines_field_and_homography(self,
                                       constant_var_use_cuda: bool = False,
                                       torch_backends_cudnn_enabled: bool = False,
                                       desired_homography: str = 'orig',
                                       **kwargs):
        line_detector = LineDetector(image_array=self.image_array,
                                     constant_var_use_cuda=constant_var_use_cuda,
                                     torch_backends_cudnn_enabled=torch_backends_cudnn_enabled)
        self.field, self.lines, self.homography = line_detector(desired_homography=desired_homography)
        return self.field, self.lines, self.homography


