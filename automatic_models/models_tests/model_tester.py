import cv2
import json
import numpy as np
import os

from time import time
from pathlib import Path
from typing import Optional, Dict

import pandas as pd

from automatic_models.handlers import VideoHandler, ImageHandler
from automatic_models.models_tests.test_utils import preprocess_labels_soccernet, \
    get_bbox_from_two_points_model_notation, show_save_image_with_lines, \
    get_lines_from_test, convert_and_save_txt_to_csv, get_bbox_lists_from_csv

from automatic_models.extra_utils.helpers import show_save_img_with_polygons
from automatic_models.models_tests.metrics import acc_p_all_lines, avg_iou_frame, \
    ratio_balls_detected, ratio_players_detected, intersection_over_union


class ModelTester(VideoHandler):
    """
    Model tester is responsible for easing testing models on Soccernet.
    """
    def __init__(self,
                 match_folder: str,
                 models_config_path: str = None,
                 save_folder: Optional[str] = None,
                 data_schema: str = 'match_schema',
                 save_images: bool = True):

        assert data_schema in ['match_schema', 'lines_test', 'fields_test', 'objects_test']

        if not Path(match_folder).exists():
            raise Exception(f"Video path {match_folder} does not exist.")

        if save_folder:
            self.output_path = Path(save_folder)
            if not self.output_path.exists():
                self.output_path.mkdir(parents=True, exist_ok=True)
        else:
            self.output_path = None

        self.save_images = save_images
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
            self.ground_truths = {'lines': {}}
            for path in Path(self.match_folder).iterdir():
                if path.suffix == '.jpg':
                    self.image_handlers[path.stem] = ImageHandler(idx=path.stem,
                                                                  image_array=cv2.imread(str(path)))
                elif path.suffix == '.json' and path.stem != 'match_info':
                    with open(str(path), 'r') as f:
                        lines = json.load(f)
                    self.ground_truths['lines'][path.stem] = get_lines_from_test(lines)
        elif self.data_schema == 'fields_test':
            with open(str(Path(match_folder) / 'total_100_converted.json')) as f:
                self.ground_truths = json.load(f)
            for path in (Path(self.match_folder) / 'img').iterdir():
                self.image_handlers[path.stem] = ImageHandler(path.stem,
                                                              image_array=cv2.imread(str(path)))
        elif self.data_schema == 'objects_test':
            for path in Path(self.match_folder).iterdir():
                if path.suffix == '.jpg':
                    self.image_handlers[int(path.stem)] = ImageHandler(idx=int(path.stem),
                                                                  image_array=cv2.imread(str(path)))
            #if not (self.output_path / 'gt.csv').exists():
            gt_csv = convert_and_save_txt_to_csv(folder_path=str(self.match_folder),
                                                 output_folder=str(self.match_folder))

            self.ground_truths = {}
            self.ground_truths['players'] = get_bbox_lists_from_csv(gt_csv, 'PERSON')
            self.ground_truths['balls'] = get_bbox_lists_from_csv(gt_csv, 'Ball')



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
        self.stats_fields = dict()

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
        self.detect_lines_and_fields()
        self.results_transformed['lines'] = self.results['lines']
        if save_figs and self.output_path:
            if not (self.output_path / 'lines_images').exists():
                (self.output_path / 'lines_images').mkdir()
        for pixel_threshold in pixels_thresholds:
            all_correct, all_total = self.calculate_accuracy_lines(pixels_threshold=pixel_threshold,
                                                                   save_fig_folder=str(self.output_path / 'lines_images'))
            if not self.stats_lines.get('all_points'):
                self.stats_lines['all_points'] = all_total
            self.stats_lines[f'list_correct_@{pixel_threshold}'] = all_correct
            self.stats_lines[f'acc_@{pixel_threshold}'] = sum(all_correct) / sum(all_total)
        with open(str((self.output_path / 'lines_results.json')), 'w') as f:
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
        with open(str((self.output_path / 'objects_results.json')), 'w') as f:
            json.dump(self.stats_objects, f)

    def calc_fields_stat(self):
        if not self.results['fields']:
            self.detect_lines_and_fields()
        iou_frames = []
        for idx in self.ground_truths.keys():
            iou_frames.append(intersection_over_union(predicted_object=self.results['fields'][idx],
                                                      ground_truth=self.ground_truths[idx]))
        self.stats_fields['iou_field'] = sum(iou_frames) / len(iou_frames)
        with open(str((self.output_path / 'field_results.json')), 'w') as f:
            json.dump(self.stats_fields, f)

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
                if not (self.output_path / 'lines_images' / f'{idx}.png').exists():
                    show_save_image_with_lines(img_array=self.image_handlers[idx].image_array,
                                               lines=self.results_transformed['lines'][idx],
                                               save_fig_path=os.path.join(save_fig_folder, f'{idx}.png'))
            correct_current, total_current = acc_p_all_lines(predicted_lines=self.results_transformed['lines'][idx],
                                                             ground_truth_lines=self.ground_truths['lines'][idx],
                                                             pixels_threshold=pixels_threshold)
            correct.append(correct_current)
            total.append(total_current)

        return correct, total




if __name__ == '__main__':
    # tester match
    tester_objects = ModelTester(match_folder='data/test_objects/data/SNMOT-116',
                                 models_config_path='../data/configs/basic_config.json',
                                 save_folder='test',
                                 data_schema='objects_test')
    tester_objects.calc_object_stats()
    # tester fields optim
    '''
    tester_optim = ModelTester(match_folder='data/test_fields',
                               models_config_path='../data/configs/config_optim_200_it.json',
                               save_folder='data/test_fields/optim_200',
                               data_schema='fields_test')
    tester_optim.calc_fields_stat()
    
    # tester lines
    tester_lines = ModelTester(match_folder='data/test_lines/data_soccernet',
                               models_config_path='../data/configs/basic_config.json',
                               save_folder='data/test_lines/test',
                               data_schema='lines_test')
    '''

