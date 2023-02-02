from model_tester import ModelTester
from pathlib import Path
import pandas as pd
if __name__ == '__main__':
    i = 0
    columns = ["iou_players", "iou_balls", "n_players_detected", "n_players_gt", "n_balls_gt", "n_balls_detected",
               '% of balls detected', '% of players detected']
    results_combined = dict()
    for name in columns:
        results_combined[name] = []
    for folder in Path('./data/test_objects/data').iterdir():
        try:
            model_tester = ModelTester(match_folder=str(folder),
                                       models_config_path='../data/configs/basic_config.json',
                                       save_folder=str(folder),
                                       save_images=False,
                                       data_schema='objects_test')
            model_tester.calc_object_stats()
            for name in columns:
                results_combined[name].append(model_tester.stats_objects[name])
        except:
            i += 1
            print(f'{i} folders were not processed')

    results_frame = pd.DataFrame()
    for name in results_combined.keys():
        results_frame[name] = results_combined[name]

    combined = pd.DataFrame()
    for col in ['iou_players', 'iou_balls', '% balls detected', '% players detected']:
        combined[col] = pd.Series(results_frame[col].mean())

    results_frame.to_csv('data/test_objects/results_combined.csv')

