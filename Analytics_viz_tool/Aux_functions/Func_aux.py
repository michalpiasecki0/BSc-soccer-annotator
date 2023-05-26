import copy
import json

#returns only ball/person annotations
def ball_person_aux_function(annotations, anotation_keep):
    ball_annotations = copy.deepcopy(annotations)
    for key in ball_annotations.keys():
        for key2 in list(ball_annotations[key].keys()):
            if ball_annotations[key][key2]['class'] != anotation_keep:
                ball_annotations[key].pop(key2)
    return ball_annotations


# Loading data
# path to the annotations folder
def loading_data_script(path):
    files_names = ['fields', 'lines', 'objects', 'actions']
    files_dict = {}

    for file_name in files_names:
        # files_dict[file_name] = file_name + '_data'
        try:
            with open(path + "\\" + file_name + '.json', 'r') as file_annotation:
                files_dict[file_name] = json.load(file_annotation)
        except FileNotFoundError:
            print('File ' + file_name + ' not present in the annotation file system')
    return files_dict

