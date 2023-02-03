from model_tester import ModelTester
from pathlib import Path
import pandas as pd

if __name__ == '__main__':
    '''
    # optim 200

    save_folder = 'data/test_lines/optim_200'
    model_tester = ModelTester(match_folder='data/test_lines/',
                               models_config_path='../data/configs/config_optim_200_it.json',
                               save_folder=save_folder,
                               save_images=True,
                               data_schema='lines_test')
    model_tester.calc_lines_stat()

    result = pd.DataFrame()
    result['iou_frame'] = pd.Series([model_tester.stats_fields['iou_field']])
    result.to_csv(f'{save_folder}/field_results.csv', header=False)
    '''
    # no optim
    save_folder = 'data/test_lines/no_optim'
    model_tester = ModelTester(match_folder='data/test_lines/data_soccernet',
                               models_config_path='../data/configs/basic_config.json',
                               save_folder=save_folder,
                               save_images=True,
                               data_schema='lines_test')
    model_tester.calc_lines_stats()

    result = pd.DataFrame()
    result['acc_@5'] = pd.Series([model_tester.stats_fields['acc_@5']])
    result['acc_@10'] = pd.Series([model_tester.stats_fields['acc_@10']])
    result['acc_@20'] = pd.Series([model_tester.stats_fields['acc_@20']])
    result['acc_@30'] = pd.Series([model_tester.stats_fields['acc_@30']])
    result.to_csv(f'{save_folder}/field_results.csv', header=False)
