from model_tester import ModelTester
from pathlib import Path
import pandas as pd

if __name__ == '__main__':
    # optim 200
    for i in range(53):
        try:
            save_folder = f'data/test_lines/optim_200/results_batch_{i}'
            model_tester = ModelTester(match_folder=f'data/test_lines/batch_{i}',
                                       models_config_path='../data/configs/config_optim_200_it.json',
                                       save_folder=save_folder,
                                       save_images=True,
                                       data_schema='lines_test')
            model_tester.calc_lines_stats()
            print(model_tester.stats_lines)
            result = pd.DataFrame()
            result['acc_@5'] = pd.Series([model_tester.stats_lines['acc_@5']])
            result['acc_@10'] = pd.Series([model_tester.stats_lines['acc_@10']])
            result['acc_@20'] = pd.Series([model_tester.stats_lines['acc_@20']])
            result['acc_@30'] = pd.Series([model_tester.stats_lines['acc_@30']])
            result.to_csv(f'{save_folder}/lines_results.csv', header=False)

            print(f'Batch {i} processed')
        except Exception as e:
            print(e)
