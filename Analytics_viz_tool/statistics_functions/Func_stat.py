import json
from shapely.geometry import Polygon, Point, box
import numpy as np
import copy



def compare_field_annotations(annotations_1, annotations_2):
    comparison_dict = {}

    keys_set_1 = set(annotations_1.keys())
    keys_set_2 = set(annotations_2.keys())

    keys_intersection = keys_set_1.intersection(keys_set_2)

    if keys_intersection == 0:
        print("Intersection found to be 0, no comparison available due to divergence in length.")
        return

    annotations_changed = 0
    for key in keys_intersection:
        polygon1 = Polygon(annotations_1[key])
        polygon2 = Polygon(annotations_2[key])

        if len(annotations_1[key]) != len(annotations_2[key]):
            annotations_changed += 1
        else:
            if any([a != b for a, b in zip(annotations_1[key], annotations_2[key])]):
                annotations_changed += 1

        if len(annotations_1[key]) == len(annotations_2[key]):
            total_point_change = sum(
                [np.linalg.norm(np.array(points_1) - np.array(points_2)) for (points_1, points_2) in
                 zip(annotations_1[key], annotations_2[key])])
        else:
            total_point_change = 'Points number difference, not issued.'

        comparison_dict[key] = {'Points_num_1': len(annotations_1[key]),
                                'Points_num_2': len(annotations_2[key]),
                                'Difference_area': polygon2.difference(polygon1).area,
                                'Intersection_area': polygon2.intersection(polygon1).area,
                                'Length_1': polygon1.length,
                                'Length_2': polygon2.length,
                                'Total_point_change': total_point_change}

    comparison_dict['Number of annotations_1'] = len(keys_set_1)
    comparison_dict['Number of annotations_2'] = len(keys_set_2)
    comparison_dict['annotations_changed'] = annotations_changed

    return comparison_dict


def compare_lines_annotations(annotations_1, annotations_2):
    comparison_dict = {}

    keys_set_1 = set(annotations_1.keys())
    keys_set_2 = set(annotations_2.keys())
    keys_intersection = keys_set_1.intersection(keys_set_2)

    if keys_intersection == 0:
        print("Intersection found to be 0, no comparison available due to divergence in length.")
        return

    lines_types = ['SIDE LINE TOP', 'SIDE LINE BOTTOM', 'SIDE LINE LEFT, SIDE LINE RIGHT', 'BIG RECT. LEFT BOTTOM',
                   'BIG RECT.LEFT TOP', 'BIG RECT. MAIN LEFT', 'SMALL RECT. LEFT BOTTOM', 'SMALL RECT. LEFT TOP',
                   'BIG RECT. RIGHT BOTTOM', 'BIG RECT. RIGHT TOP', 'BIG RECT. RIGHT MAIN', 'SMALL RECT. RIGHT BOTTOM',
                   'SMALL RECT. RIGHT TOP', 'SMALL RECT. RIGHT MAIN', 'MIDDLE LINE']

    annotations_changed = 0
    for key in keys_intersection:
        frame_dict = {}
        for line_type in lines_types:

            if (line_type in annotations_1.keys() and line_type not in annotations_2.keys()) or (
                    line_type in annotations_2.keys() and line_type not in annotations_1.keys()):
                annotations_changed += 1
            elif line_type in annotations_1.keys() and line_type in annotations_2.keys():
                if any([a != b for a, b in zip(annotations_1[key][line_type], annotations_2[key][line_type])]):
                    annotations_changed += 1

            frame_dict[line_type] = {}

            if line_type in annotations_1[key].keys():
                frame_dict[line_type]['line_present_annotation_1'] = 1
            else:
                frame_dict[line_type]['line_present_annotation_1'] = 0
            if line_type in annotations_2[key].keys():
                frame_dict[line_type]['line_present_annotation_2'] = 1
            else:
                frame_dict[line_type]['line_present_annotation_2'] = 0
            if frame_dict[line_type]['line_present_annotation_2'] == 1 and frame_dict[line_type][
                'line_present_annotation_1'] == 1:
                frame_dict[line_type]['Position_difference'] = sum(
                    [np.linalg.norm(np.array(points_1) - np.array(points_2)) for (points_1, points_2) in
                     zip(annotations_1[key][line_type], annotations_2[key][line_type])])
                frame_dict[line_type]['Length_difference'] = np.linalg.norm(
                    np.array(annotations_1[key][line_type][0]) - np.array(
                        annotations_1[key][line_type][1])) - np.linalg.norm(
                    np.array(annotations_2[key][line_type][0]) - np.array(annotations_2[key][line_type][1]))

        comparison_dict[key] = frame_dict

    comparison_dict['Number of annotations_1'] = len(keys_set_1)
    comparison_dict['Number of annotations_2'] = len(keys_set_2)
    comparison_dict['Annotations changed'] = annotations_changed

    return comparison_dict


# assumption - only one ball in the frame, if more return info
def compare_ball_annotations(annotations_1, annotations_2):
    comparison_dict = {}
    keys_set_1 = set(annotations_1.keys())
    keys_set_2 = set(annotations_2.keys())
    keys_intersection = keys_set_1.intersection(keys_set_2)

    if keys_intersection == 0:
        print("Intersection found to be 0, no comparison available due to divergence in length.")
        return
    annotations_changed = 0
    for key in keys_intersection:
        if len(annotations_1[key]) != len(annotations_2[key]) or len(annotations_1[key]) != 1 or len(
                annotations_2[key]) != 1:
            comparison_dict['Number of ball instances_1'] = len(annotations_1[key])
            comparison_dict['Number of ball instances_2'] = len(annotations_2[key])
            comparison_dict['Description'] = 'More than one instance of ball found in annotations'
            continue
        first = list(annotations_1[key].keys())[0]
        point1_1 = Point([annotations_1[key][first]['x_top_left'], annotations_1[key][first]['y_top_left']])
        point1_2 = Point([annotations_1[key][first]['x_bottom_right'], annotations_1[key][first]['y_bottom_right']])

        point2_1 = Point([annotations_2[key][first]['x_top_left'], annotations_2[key][first]['y_top_left']])
        point2_2 = Point([annotations_2[key][first]['x_bottom_right'], annotations_2[key][first]['y_bottom_right']])

        polygon1 = box(point1_1.x, point1_1.y, point1_2.x, point1_2.y)
        polygon2 = box(point2_1.x, point2_1.y, point2_2.x, point2_2.y)

        if point1_1 != point2_1 or point1_2 != point2_2:
            annotations_changed += 1

        total_point_change = point1_1.distance(point2_1) + point2_1.distance(point2_2)

        comparison_dict[key] = {'Difference_area': polygon2.difference(polygon1).area,
                                'Intersection_area': polygon2.intersection(polygon1).area,
                                'Length_1': polygon1.length,
                                'Length_2': polygon2.length,
                                'Total_point_change': total_point_change}

    comparison_dict['Number of annotations_1'] = len(keys_set_1)
    comparison_dict['Number of annotations_2'] = len(keys_set_2)
    comparison_dict['Annotations changed'] = annotations_changed

    return comparison_dict


def compare_player_annotations(annotations_1, annotations_2):
    comparison_dict = {}
    keys_set_1 = set(annotations_1.keys())
    keys_set_2 = set(annotations_2.keys())
    keys_intersection = keys_set_1.intersection(keys_set_2)

    if keys_intersection == 0:
        print("Intersection found to be 0, no comparison available due to divergence in length.")
        return

    annotations_changed = 0
    for key in keys_intersection:
        num_players_1 = len(annotations_1[key].keys())
        Points_1 = [(Point([annotations_1[key][str(num)]['x_top_left'], annotations_1[key][str(num)]['y_top_left']]),
                     Point([annotations_1[key][str(num)]['x_bottom_right'],
                            annotations_1[key][str(num)]['y_bottom_right']]))
                    for num in annotations_1[key].keys()]

        Polygons_1 = [box(point[0].x, point[0].y, point[1].x, point[1].y) for point in
                      Points_1]

        num_players_2 = len(annotations_2[key].keys())

        Points_2 = [(Point([annotations_2[key][str(num)]['x_top_left'], annotations_2[key][str(num)]['y_top_left']]),
                     Point([annotations_2[key][str(num)]['x_bottom_right'],
                            annotations_2[key][str(num)]['y_bottom_right']]))
                    for num in annotations_2[key].keys()]

        Polygons_2 = [box(point[0].x, point[0].y, point[1].x, point[1].y) for point in
                      Points_2]

        confidence_list_1 = [annotations_1[key][str(num)]['confidence'] for num in annotations_1[key].keys()]

        confidence_list_2 = [annotations_2[key][str(num)]['confidence'] for num in annotations_2[key].keys()]

        total_area_difference_1 = 0
        total_area_1 = 0
        total_intersection_area_1 = 0
        total_length_1 = 0
        total_length_difference_1 = 0
        total_points_change_1 = 0
        total_centroid_distance_change_1 = 0
        total_centroid_distance_change_conf_adjusted_1 = 0
        total_area_difference_conf_adjusted_1 = 0
        total_intersection_area_conf_adjusted_1 = 0
        total_point_change_conf_adjusted_1 = 0

        total_area_difference_2 = 0
        total_area_2 = 0
        total_intersection_area_2 = 0
        total_length_2 = 0
        total_length_difference_2 = 0
        total_points_change_2 = 0
        total_centroid_distance_change_2 = 0
        total_centroid_distance_change_conf_adjusted_2 = 0
        total_area_difference_conf_adjusted_2 = 0
        total_intersection_area_conf_adjusted_2 = 0
        total_point_change_conf_adjusted_2 = 0

        average_confidence_1 = 0
        average_confidence_2 = 0

        for polygon, conf in zip(Polygons_1, zip(confidence_list_1, confidence_list_2)):
            total_area_1 += polygon.area
            closest_polygon = find_closest(polygon, Polygons_2)
            total_area_difference_1 += polygon.difference(closest_polygon).area
            total_intersection_area_1 += polygon.intersection(closest_polygon).area
            total_length_1 += polygon.length
            average_confidence_1 += conf[0]
            total_points_change_1 += abs(polygon.bounds[0] - closest_polygon.bounds[0]) + abs(
                polygon.bounds[1] - closest_polygon.bounds[1]) + abs(
                polygon.bounds[2] - closest_polygon.bounds[2]) + abs(polygon.bounds[3] - closest_polygon.bounds[3])
            total_centroid_distance_change_1 += polygon.centroid.distance(closest_polygon.centroid)

            total_area_difference_conf_adjusted_1 += polygon.difference(closest_polygon).area * min(conf[0], conf[1])
            total_intersection_area_conf_adjusted_1 += polygon.intersection(closest_polygon).area * min(conf[0],
                                                                                                        conf[1])
            total_point_change_conf_adjusted_1 += (abs(polygon.bounds[0] - closest_polygon.bounds[0]) + abs(
                polygon.bounds[1] - closest_polygon.bounds[1]) + abs(
                polygon.bounds[2] - closest_polygon.bounds[2]) + abs(
                polygon.bounds[3] - closest_polygon.bounds[3])) * min(conf[0], conf[1])
            total_centroid_distance_change_conf_adjusted_1 += polygon.centroid.distance(closest_polygon.centroid) * min(
                conf[0], conf[1])

            if polygon != closest_polygon:
                annotations_changed += 1

        for polygon, conf in zip(Polygons_2, zip(confidence_list_1, confidence_list_2)):
            total_area_2 += polygon.area
            closest_polygon = find_closest(polygon, Polygons_1)
            total_area_difference_2 += polygon.difference(closest_polygon).area
            total_intersection_area_2 += polygon.intersection(closest_polygon).area
            total_length_2 += polygon.length
            average_confidence_2 += conf[1]
            total_points_change_2 += abs(polygon.bounds[0] - closest_polygon.bounds[0]) + abs(
                polygon.bounds[1] - closest_polygon.bounds[1]) + abs(
                polygon.bounds[2] - closest_polygon.bounds[2]) + abs(polygon.bounds[3] - closest_polygon.bounds[3])
            total_centroid_distance_change_2 += polygon.centroid.distance(closest_polygon.centroid)

            total_area_difference_conf_adjusted_2 += polygon.difference(closest_polygon).area * min(conf[0], conf[1])
            total_intersection_area_conf_adjusted_2 += polygon.intersection(closest_polygon).area * min(conf[0],
                                                                                                        conf[1])
            total_point_change_conf_adjusted_2 += (abs(polygon.bounds[0] - closest_polygon.bounds[0]) + abs(
                polygon.bounds[1] - closest_polygon.bounds[1]) + abs(
                polygon.bounds[2] - closest_polygon.bounds[2]) + abs(
                polygon.bounds[3] - closest_polygon.bounds[3])) * min(conf[0], conf[1])
            total_centroid_distance_change_conf_adjusted_2 += polygon.centroid.distance(closest_polygon.centroid) * min(
                conf[0], conf[1])

            if polygon != closest_polygon:
                annotations_changed += 1

        if num_players_1 == 0 or num_players_2 == 0:
            average_confidence_1 = 'Not issued'
            average_confidence_2 = 'Not issued'
        else:

            average_confidence_1 = average_confidence_1 / num_players_1
            average_confidence_2 = average_confidence_2 / num_players_2

        comparison_dict[key] = {'total_area_difference_1': total_area_difference_1,
                                'total_area_1': total_area_1,
                                'total_intersection_area_1': total_intersection_area_1,
                                'total_length_1': total_length_1,
                                'total_length_difference_1': total_length_difference_1,
                                'total_points_change_1': total_points_change_1,
                                'total_area_difference_2': total_area_difference_2,
                                'total_area_2': total_area_2,
                                'total_intersection_area_2': total_intersection_area_2,
                                'total_length_2': total_length_2,
                                'total_length_difference_2': total_length_difference_2,
                                'total_points_change_2': total_points_change_2,
                                'average_confidence_1': average_confidence_1,
                                'average_confidence_2': average_confidence_2,
                                'total_area_difference_conf_adjusted_1': total_area_difference_conf_adjusted_1,
                                'total_intersection_area_conf_adjusted_1': total_intersection_area_conf_adjusted_1,
                                'total_point_change_conf_adjusted_1': total_point_change_conf_adjusted_1,
                                'total_area_difference_conf_adjusted_2': total_area_difference_conf_adjusted_2,
                                'total_intersection_area_conf_adjusted_2': total_intersection_area_conf_adjusted_2,
                                'total_point_change_conf_adjusted_2': total_point_change_conf_adjusted_2,
                                'total_centroid_distance_change_1': total_centroid_distance_change_1,
                                'total_centroid_distance_change_conf_adjusted_1': total_centroid_distance_change_conf_adjusted_1,
                                'total_centroid_distance_change_2': total_centroid_distance_change_2,
                                'total_centroid_distance_change_conf_adjusted_2': total_centroid_distance_change_conf_adjusted_2}

    comparison_dict['Number of annotations_1'] = len(keys_set_1)
    comparison_dict['Number of annotations_2'] = len(keys_set_2)
    comparison_dict['Annotations changed'] = annotations_changed

    return comparison_dict


# only compares manual to automatic
def compare_event_annotations(annotations_1, annotations_2):
    # (gameTime, label and team) is an identifier of an event
    comparison_dict = {}

    if len(annotations_1) == 0 or len(annotations_2) == 0:
        print('No annotations found in comparison')

    annotations_changed = 0
    for i, event_compare in enumerate(annotations_1['actions']):
        for event in annotations_2['actions']:

            if event_compare['gameTime'] == event['gameTime'] and event_compare['label'] == event['label'] and \
                    event_compare['team'] == event['team']:
                comparison_dict[i] = {}
                comparison_dict[i]['gameTime_1'] = event_compare['gameTime']
                comparison_dict[i]['gameTime_2'] = event['gameTime']
                comparison_dict[i]['label'] = event_compare['label']
                comparison_dict[i]['player_1'] = event_compare['player']
                comparison_dict[i]['player_2'] = event['player']
                comparison_dict[i]['videoTime_1'] = event_compare['videoTime']
                comparison_dict[i]['videoTime_2'] = event['videoTime']
                comparison_dict[i]['Time_difference(sec)'] = to_seconds(event['videoTime']) - to_seconds(
                    event_compare['videoTime'])
                comparison_dict[i]['Description'] = 'Event mapping found'
                annotations_changed += 1
                break

            comparison_dict[i] = {}
            comparison_dict[i]['gameTime_1'] = event_compare['gameTime']
            comparison_dict[i]['label'] = event_compare['label']
            comparison_dict[i]['player_1'] = event_compare['player']
            comparison_dict[i]['videoTime_1'] = event_compare['videoTime']
            comparison_dict[i]['Description'] = 'No matching found'

    return comparison_dict

def to_seconds(s):
    minu, sec = [float(x) for x in s.split(':')]
    return minu*60 + sec

def find_closest(polygon_target, polygon_list):
    placeholder = None
    min_dist = 10**6
    centroid = polygon_target.centroid
    for polygon in polygon_list:
        if polygon.centroid.distance(centroid) < min_dist:
            placeholder = polygon
            min_dist = polygon.centroid.distance(centroid)
    return placeholder
