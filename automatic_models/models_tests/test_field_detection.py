from model_tester import ModelTester
from pathlib import Path
import pandas as pd


if __name__ == '__main__':
    # optim 200

    save_folder = 'data/test_fields/optim_200'
    model_tester = ModelTester(match_folder='data/test_fields/',
                               models_config_path='../data/configs/config_optim_200_it.json',
                               save_folder=save_folder,
                               save_images=True,
                               data_schema='fields_test')
    model_tester.calc_fields_stat()

    result = pd.DataFrame()
    result['iou_frame'] = pd.Series([model_tester.stats_fields['iou_field']])
    result.to_csv(f'{save_folder}/field_results.csv', header=False)

    # no optim
    save_folder = 'data/test_fields/no_optim'
    model_tester = ModelTester(match_folder='data/test_fields/',
                               models_config_path='../data/configs/basic_config.json',
                               save_folder=save_folder,
                               save_images=True,
                               data_schema='fields_test')
    model_tester.calc_fields_stat()

    result = pd.DataFrame()
    result['iou_frame'] = pd.Series([model_tester.stats_fields['iou_field']])
    result.to_csv(f'{save_folder}/field_results.csv', header=False)
