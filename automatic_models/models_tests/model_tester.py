import cv2
import json
import numpy as np
import os

from time import time
from pathlib import Path
from typing import Optional, Dict
from automatic_models.handlers import VideoHandler, ImageHandler
from automatic_models.models_tests.test_utils import preprocess_labels_soccernet, \
    get_bbox_from_two_points_model_notation, show_save_image_with_lines, get_lines_from_test
from automatic_models.models_tests.metrics import acc_p_all_lines, avg_iou_frame, \
    ratio_balls_detected, ratio_players_detected


class ModelTester(VideoHandler):
    """
    Model tester is responsible for easing testing models on Soccernet.
    """
    def __init__(self,
                 match_folder: str,
                 models_config_path: str = None,
                 save_folder: Optional[str] = None,
                 data_schema: str = 'match_schema'):

        if not Path(match_folder).exists():
            raise Exception(f"Video path {match_folder} does not exist.")

        if save_folder:
            self.save_folder = Path(save_folder)
            if not self.save_folder.exists():
                self.save_folder.mkdir(parents=True, exist_ok=True)
        else:
            self.save_folder = None

        self.data_schema = data_schema
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

        self.meta_data = {}
        self.match_folder = match_folder
        self.frames: Optional[Dict[int, np.ndarray]] = None
        self.image_handlers = dict()

        if self.data_schema == 'match_schema':

            for valid_path in self._get_only_valid_images():
                self.image_handlers[valid_path.stem] = ImageHandler(idx=valid_path.stem,
                                                                    image_array=cv2.imread(str(valid_path)))

            with open(str(Path(match_folder) / 'Labels-v3.json')) as f:
                ground_truths = json.load(f)
                self.ground_truths = preprocess_labels_soccernet(ground_truths)
        elif self.data_schema == 'lines_test':
            self.ground_truths = {}
            for path in Path(self.match_folder).iterdir():
                if path.suffix == '.jpg':
                    self.image_handlers[path.stem] = ImageHandler(idx=path.stem,
                                                                  image_array=cv2.imread(str(path)))
                elif path.suffix == '.json' and path.stem != 'match_info':
                    with open(str(path), 'r') as f:
                        lines = json.load(f)
                    self.ground_truths[path.stem] = get_lines_from_test(lines)


        self.results = {'actions': {},
                        'lines': {},
                        'fields': {},
                        'homographies': {},
                        'objects': {}}
        self.results_transformed = {'lines': {},
                                    'players': {},
                                    'balls': {}}
        self.stats_objects = dict()
        self.stats_lines = dict()

    def _get_only_valid_images(self):
        return [path for path in (Path(self.match_folder) / 'Frames-v3').iterdir() if str(path).find('_') == -1]

    def transform_model_objects(self):
        if self.results['objects']:
            for index, objects in self.results['objects'].items():
                self.results_transformed['players'][index] = []
                self.results_transformed['balls'][index] = []
                for one_object in objects.values():
                    if one_object['class'] == 'PERSON':
                        self.results_transformed['players'][index]\
                            .append(get_bbox_from_two_points_model_notation(one_object))
                    elif one_object['class'] == 'SPORTS_BALL':
                        self.results_transformed['balls'][index]\
                            .append(get_bbox_from_two_points_model_notation(one_object))
        else:
            print('Objects were not calculated by models yet')

    def transform_model_lines(self):
        if self.results['lines']:
            self.results_transformed['lines'] = self.results['lines']
        else:
            print('Objects were not calculated by models yet')

    def calc_lines_stats(self, pixels_thresholds: list = [5, 10, 20, 30], save_figs: bool = True):
        if save_figs and self.save_folder:
            if not (self.save_folder / 'lines_images').exists():
                (self.save_folder / 'lines_images').mkdir()
        for pixel_threshold in pixels_thresholds:
            all_correct, all_total = self.calculate_accuracy_lines(pixels_threshold=pixel_threshold,
                                                                   save_fig_folder=str(self.save_folder / 'lines_images'))
            if not self.stats_lines.get('all_points'):
                self.stats_lines['all_points'] = all_total
            self.stats_lines[f'list_correct_@{pixel_threshold}'] = all_correct
            self.stats_lines[f'acc_@{pixel_threshold}'] = sum(all_correct) / sum(all_total)
        with open(str((self.save_folder / 'lines_results.json')), 'w') as f:
            json.dump(self.stats_lines, f)

    def calc_object_stats(self):
        self.stats_objects['iou_players'] = self.calculate_avg_iou(obj_type='players')
        self.stats_objects['iou_balls'] = self.calculate_avg_iou(obj_type='balls')
        self.stats_objects['n_players_detected'], self.stats_objects['n_players_gt'] =\
            self.count_object_frequency(obj_type='players')
        self.stats_objects['n_balls_detected'], self.stats_objects['n_balls_gt'] = \
            self.count_object_frequency(obj_type='balls')
        for name in ['balls', 'players']:
            if self.stats_objects[f'n_{name}_gt'] > 0:
                self.stats_objects[f'% of {name} detected'] = \
                    self.stats_objects[f'n_{name}_detected'] / self.stats_objects[f'n_{name}_gt']
        with open(str((self.save_folder / 'objects_results.json')), 'w') as f:
            json.dump(self.stats_objects, f)

    def calculate_avg_iou(self, obj_type: str):
        """
        Avg IOU for all frames included
        """
        assert obj_type in ['players', 'balls']
        if not self.results['objects']:
            self.detect_objects()
            self.transform_model_objects()
        iou_weights = []
        for idx in self.ground_truths[obj_type].keys():
            if self.results_transformed[obj_type].get(idx):
                iou_weights.append(avg_iou_frame(predicted_objects=self.results_transformed[obj_type][idx],
                                                 ground_truths=self.ground_truths[obj_type][idx]))
        if sum([weight[1] for weight in iou_weights]) == 0:
            return 0
        return sum([(iou * weight) for (iou, weight) in iou_weights]) / sum([weight[1] for weight in iou_weights])

    def count_object_frequency(self, obj_type: str):
        assert obj_type in ['balls', 'players']
        if not self.results['objects']:
            self.detect_objects()
            self.transform_model_objects()
        if obj_type == 'balls':
            return ratio_balls_detected(predicted_balls=self.results_transformed[obj_type],
                                        truth_balls=self.ground_truths[obj_type])
        else:
            return ratio_players_detected(predicted_players=self.results_transformed[obj_type],
                                          ground_truths=self.ground_truths[obj_type])

    def calculate_accuracy_lines(self, pixels_threshold: int, save_fig_folder: Optional[str] = None):
        if not self.results['lines']:
            self.detect_lines_and_fields()
            self.results_transformed['lines'] = self.results['lines']

        correct = []
        total = []
        for idx in self.results_transformed['lines']:
            if save_fig_folder:
                if not (self.save_folder / 'lines_images' / f'{idx}.png').exists():
                    show_save_image_with_lines(img_array=self.image_handlers[idx].image_array,
                                               lines=self.results_transformed['lines'][idx],
                                               save_fig_path=os.path.join(save_fig_folder, f'{idx}.png'))
            correct_current, total_current = acc_p_all_lines(predicted_lines=self.results_transformed['lines'][idx],
                                                             ground_truth_lines=self.ground_truths['lines'][idx],
                                                             pixels_threshold=pixels_threshold)
            correct.append(correct_current)
            total.append(total_current)

        return correct, total







