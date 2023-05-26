from Aux_functions.Func_aux import *
from statistics_functions.Func_stat import *
from visualization_functions import *
import os


def main():
    annotations_1 = loading_data_script('D:/Pulpit/matches/2022-10-01_manu_aston/annotations/model_annotation')
    annotations_2 = loading_data_script('D:/Pulpit/matches/2022-10-01_manu_aston/annotations/model_annotation_v2')

    ball_diff_dict = compare_ball_annotations(ball_person_aux_function(annotations_1['objects'], anotation_keep='SPORTS_BALL'),
                                              ball_person_aux_function(annotations_2['objects'], anotation_keep='SPORTS_BALL'))
    fields_diff_dict = compare_field_annotations(annotations_1['fields'], annotations_2['fields'])
    player_diff_dict = compare_player_annotations(ball_person_aux_function(annotations_1['objects'], anotation_keep='PERSON'),
                                                  ball_person_aux_function(annotations_2['objects'], anotation_keep='PERSON'))
    event_diff_dict = compare_event_annotations(annotations_1['actions'], annotations_2['actions'])
    lines_diff_dict = compare_lines_annotations(annotations_1['lines'], annotations_2['lines'])

    file_path = 'data_output/'

    files_names = ['ball', 'fields', 'player', 'event', 'lines']
    data_files = [ball_diff_dict, fields_diff_dict, player_diff_dict, event_diff_dict, lines_diff_dict]

    for file_name, data_file in zip(files_names, data_files):
        mode = 'a' if os.path.exists(file_path + file_name + '_comparison_dict' + '.json') else 'w+'
        with open(file_path + file_name + '_comparison_dict' + '.json', mode) as fp:
            json.dump(data_file, fp)

    return ball_diff_dict, fields_diff_dict, player_diff_dict, event_diff_dict, lines_diff_dict



if __name__ == '__main__':
    main()

