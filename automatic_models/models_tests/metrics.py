import numpy as np
from shapely.geometry import Polygon


def acc_p_all_lines(predicted_lines: dict,
                    ground_truth_lines: dict,
                    pixels_threshold: int):
    """
    Calculate
    """
    correct = 0
    for ground_name, ground_coordinates in ground_truth_lines.items():
        # if line not in predictions, setting very far away to get negative outcome
        predicted = predicted_lines.get(ground_name, [[-1500, -1500], [-1000, -1000]])
        correct += acc_p_one_line(ground_truth=ground_coordinates,
                                  predicted=predicted,
                                  pixels_threshold=pixels_threshold)

    return correct, 2 * len(ground_truth_lines.keys())


def acc_p_one_line(ground_truth: list, predicted: list, pixels_threshold: int) -> int:
    """
    Test if predicted line lies in given  distance to ground truth
    :param pixels_threshold: acceptance threshold for distance between ground truth and prediction points
    :returns: 2 if both match, 1 if only one, 0 if none match
    """
    def test_one_point(ground_point, predicted_point):

        x_check = (ground_point[0] - pixels_threshold) <= predicted_point[0] <= (ground_point[0] + pixels_threshold)
        y_check = (ground_point[1] - pixels_threshold) <= predicted_point[1] <= (ground_point[1] + pixels_threshold)
        return x_check and y_check

    if np.linalg.norm(np.array(ground_truth[0]) - np.array(predicted[1])) < np.linalg.norm(
            np.array(ground_truth[0]) - np.array(predicted[0])):
        # make sure ground truth and predicted extremities correspond to each other
        predicted = [predicted[1], predicted[0]]

    p0 = test_one_point(ground_point=ground_truth[0], predicted_point=predicted[0])
    p1 = test_one_point(ground_point=ground_truth[1], predicted_point=predicted[1])

    return int(p0) + int(p1)


def ratio_balls_detected(predicted_balls: dict,
                         truth_balls: dict):
    """
    Count how often models recognizes ball, when there is one on image.
    :param predicted_balls: results['balls']
    :param truth_balls: gt['balls']
    """
    n_predicted, n_truth = 0, 0
    for idx in truth_balls:
        if idx in predicted_balls:
            if len(truth_balls[idx]) > 0:
                n_truth += 1
            if len(predicted_balls[idx]) > 0:
                n_predicted += 1
    return n_predicted, n_truth


def ratio_players_detected(predicted_players: dict,
                           ground_truths: dict):
    """
    Given all images, count number of detected objects and ground truths
    :param predicted_balls: results['balls']
    :param truth_balls: gt['balls']
    """
    n_predicted, n_truth = 0, 0
    for idx in ground_truths:
        if idx in predicted_players:
            n_predicted += len(predicted_players[idx])
            n_truth += len(ground_truths[idx])

    return n_predicted, n_truth


def avg_iou_frame(predicted_objects: list,
                  ground_truths: list) -> tuple:
    """
    Calculate average iou on given frame.
    If no ground truths are on the frame, returns 0.
    :param predicted_objects: results[objects][idx]
    :param ground_truths: gt[objects][idx]
    """
    iou = 0
    if len(ground_truths) == 0:
        return 0, 0
    for gt_bbox in ground_truths:
        if len(predicted_objects) > 0:
            iou += max([intersection_over_union(pred_bbox, gt_bbox) for pred_bbox in predicted_objects])
        else:
            iou = 0
    return iou / len(ground_truths), len(ground_truths)


def intersection_over_union(predicted_object: list,
                            ground_truth: list) -> float:
    """
    Calculate IOU for one object.
    :param predicted_object: list of shape [4X2]
    :param ground_truth: list of shape [4x2]
    """
    predicted_polygon, gt_polygon = Polygon(predicted_object), Polygon(ground_truth)
    return predicted_polygon.intersection(gt_polygon).area / predicted_polygon.union(gt_polygon).area




