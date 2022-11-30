import numpy as np
import cv2
from typing import List, Dict, Optional
from automatic_models.extra_utils.helpers import divide_video_into_frames
from automatic_models.lines_and_field_detection.lines_and_field_detector import LineDetector

class VideoHandler:
    def __init__(self, video_path: str,
                 output_path: str):
        self.video_path = video_path
        self.output_path = output_path
        self.frames: Optional[Dict[int, np.ndarray]] = None
        self.image_handlers: Optional[Dict[int, ImageHandler]] = None
        self.events: Optional[Dict] = None
        self.lines: Optional[Dict] = None
        self.fields: Optional[Dict] = None
        self.homographies: Optional[Dict] = None
        self.objects_detected: Optional[Dict] = None

    def divide_video(self, desired_frequency: Optional[int] = None):
        if self.frames:
            print('Video is already divided')
        else:
            self.frames, self.image_handlers = {}, {}
            self.frames = divide_video_into_frames(video_path=self.video_path,
                                                   output_folder=self.output_path + '/raw_frames',
                                                   desired_frequency=desired_frequency)
            for idx, frame in self.frames.items():
                self.image_handlers[idx] = ImageHandler(idx = idx, image_array=frame)

    def annotate_events(self):
        pass

    def detect_lines_and_fields(self,
                                constant_var_use_cuda: bool = False,
                                torch_backends_cudnn_enabled: bool = False,
                                desired_homography: str = 'orig',
                                **kwargs):
        if self.fields:
            print('Fields and lines are already calculated')
        else:
            if self.image_handlers:
                self.fields, self.lines, self.homographies = {}, {}, {}
                for idx, image_handler in self.image_handlers.items():
                    field, lines, homography = image_handler.get_lines_field_and_homography(
                        constant_var_use_cuda=constant_var_use_cuda,
                        torch_backends_cudnn_enabled=torch_backends_cudnn_enabled,
                        desired_homography=desired_homography
                    )
                    self.fields[idx] = field
                    self.lines[idx] = lines
                    self.homographies[idx] = homography
                    print(f'{idx} was processed.')
            else:
                print('You must divide video and create image handlers before invoking Lines & FIeld Detection')


    def detect_objects(self):
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
        return ''

    def get_time(self):
        pass

    def get_objects(self):
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


