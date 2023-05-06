"""
Script for comparing results from two folders.
"""
import json
import os
import sys
import warnings
from argparse import ArgumentParser
from typing import Dict
from pathlib import Path

warnings.filterwarnings("ignore")

bs_soccer = str((Path('./')).resolve())
automatic_models_path = str((Path('./') / 'automatic_models').resolve())

for path in (bs_soccer, automatic_models_path):
    if path not in sys.path:
        sys.path.append(path)
from automatic_models.models_tests.test_utils import get_bbox_from_two_points_model_notation
from automatic_models.models_tests.metrics import avg_iou_frame, ratio_balls_detected, \
    ratio_players_detected, intersection_over_union, acc_p_all_lines


def _check_files_in_directory(directory_path: str) -> Dict:
    existing_files_dict = {
        "fields.json": False,
        "lines.json": False,
        "objects.json": False,
    }
    files_in_directory = [path.name for path in Path(directory_path).iterdir()]
    for file_name in existing_files_dict:
        if file_name in files_in_directory:
            existing_files_dict[file_name] = True
    return existing_files_dict


def _load_data(file_path: str, annotation_type: str):
    assert annotation_type in ['lines', 'objects', 'fields']
    with open(file_path) as f:
        data = json.load(f)
    if annotation_type == 'objects':
        results = {'players': {},
                   'balls': {}
                   }
        for index, objects in data.items():
            if objects:
                results['players'][index] = []
                results['balls'][index] = []
                for one_object in objects.values():
                    if one_object['class'] == 'PERSON':
                        results['players'][index].append(get_bbox_from_two_points_model_notation(one_object))
                    elif one_object['class'] == 'SPORTS_BALL':
                        results['balls'][index].append(get_bbox_from_two_points_model_notation(one_object))
        return results
    if annotation_type in ['fields', 'lines']:
        return data


def calculate_object_stats(gt_objects: dict,
                           model_objects: dict,
                           obj_type: str):
    assert obj_type in ['players', 'balls']
    metrics = {}
    iou_weights = []
    for idx in gt_objects[obj_type]:
        if model_objects[obj_type].get(idx):
            iou_weights.append(avg_iou_frame(predicted_objects=model_objects[obj_type][idx],
                                             ground_truths=gt_objects[obj_type][idx]))
    if sum([weight[1] for weight in iou_weights]) == 0:
        metrics['Average IOU'] = 0
    else:
        metrics['Average IOU'] = sum([(iou * weight) for (iou, weight) in iou_weights]) \
                              / sum([weight[1] for weight in iou_weights])
    if obj_type == 'balls':
        detected_number, gt_number = ratio_balls_detected(predicted_balls=model_objects[obj_type],
                                                          truth_balls=gt_objects[obj_type])
    else:
        detected_number, gt_number = ratio_players_detected(predicted_players=model_objects[obj_type],
                                                            ground_truths=gt_objects[obj_type])
    metrics['Ratio Instances detected '] = detected_number / gt_number
    metrics['Detected instances number'] = detected_number
    metrics['Ground truth instances number'] = gt_number
    return metrics


def calculate_field_stats(gt_objects: dict,
                          model_objects: dict):
    iou_frames = []
    for idx in gt_objects:
        if idx in model_objects:
            iou_frames.append(intersection_over_union(predicted_object=model_objects[idx],
                                                      ground_truth=gt_objects[idx]))
    return sum(iou_frames) / len(iou_frames)


def calculate_lines_stats(gt_objects: dict,
                          model_objects: dict,
                          pixels_thresholds: list = [5, 10, 20, 30]):
    line_results = {}
    for pixel_threshold in pixels_thresholds:
        correct = []
        total = []
        for idx in gt_objects:
            if idx in model_objects:
                correct_current, total_current = acc_p_all_lines(predicted_lines=model_objects[idx],
                                                                 ground_truth_lines=gt_objects[idx],
                                                                 pixels_threshold=pixel_threshold)
            correct.append(correct_current)
            total.append(total_current)
        line_results[f'Accuracy_@{pixel_threshold}'] = sum(correct) / sum(total)
    return line_results


def parse_args():
    argument_parser = ArgumentParser()
    argument_parser.add_argument('-p_gt', '--path_ground_truth', required=True, type=str,
                                 help='direct/relative path to folder with ground truth annotations')
    argument_parser.add_argument('-p_m', '--path_model', required=True, type=str,
                                 help='direct/relative path to folder with model annotation')
    return argument_parser.parse_args()


def compare_results(path_ground_truth: str,
                    path_model: str):
    files_in_gt = _check_files_in_directory(directory_path=path_ground_truth)
    files_in_model = _check_files_in_directory(directory_path=path_model)

    for annotation_type in files_in_gt:
        if not (files_in_gt[annotation_type] and files_in_model[annotation_type]):
            print(f"{annotation_type} not present in both folders. "
                  f"Make sure it is placed in both gt and model annotation folder.")
        else:
            objects_gt = _load_data(file_path=os.path.join(path_ground_truth, annotation_type),
                                    annotation_type=annotation_type[:-5])
            objects_model = _load_data(file_path=os.path.join(path_model, annotation_type),
                                       annotation_type=annotation_type[:-5])
            if annotation_type == "objects.json":
                print("Stats players")
                print(calculate_object_stats(gt_objects=objects_gt,
                                             model_objects=objects_model,
                                             obj_type='players'))
                print("Stats balls")
                print(calculate_object_stats(gt_objects=objects_gt,
                                             model_objects=objects_model,
                                             obj_type='balls'))
            if annotation_type == 'fields.json':
                print("Stats fields")
                print("Average IOU", calculate_field_stats(gt_objects=objects_gt,
                                                           model_objects=objects_model))
            if annotation_type == 'lines.json':
                print("stats lines")
                print(calculate_lines_stats(gt_objects=objects_gt,
                                            model_objects=objects_model))




if __name__ == "__main__":
    if len(sys.argv) > 1:
        # User introduces arguments with CLI
        args = parse_args()
        compare_results(path_ground_truth=args.path_ground_truth,
                        path_model=args.path_model)
    else:
        # Default run if user does not introduce arguments
        compare_results(path_ground_truth="<PATH_TO_FOLDER_WITH_MANUAL_ANNOTATION_>",
                        path_model="<PATH_TO_FOLDER_WITH_MODEL_ANNOTATION>")