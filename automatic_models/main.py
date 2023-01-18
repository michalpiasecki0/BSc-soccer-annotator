"""This module serves as general API with automatic_models module"""

from handlers import VideoHandler
from argparse import ArgumentParser


def parse_args():
    argument_parser = ArgumentParser()
    argument_parser.add_argument('--video_path', type=str, help='direct/relative path to video to be analyzed')
    argument_parser.add_argument('--output_path', type=str, help='Path to folder where all results from models '
                                                                 'should be saved')
    argument_parser.add_argument('--frequency', type=float, help='Frequency for video division')
    argument_parser.add_argument('--start_point', type=float, help='Starting point to divide video')
    argument_parser.add_argument('--saving_strategy', type=float, help='Choose from add/overwrite. If latter new '
                                                                       'predictions overwrite older ones')
    argument_parser.add_argument('--models_config_path', type=float, help='Path to json with manually set models')
    return argument_parser.parse_args()


def perform_models(video_path: str,
                   output_path: str,
                   frequency: float,
                   start_point: float = 0,
                   models_config_path: str = None,
                   saving_strategy: str = 'overwrite') -> None:
    """

    :param video_path: path to a video file (currently mp4, mkv formats are supported)
    :param output_path: path to output folder, where all model results are saved
    :param frequency: fps for models (e.G )
    :param start_point: starting point
    :param saving_strategy: add/overwrite. Choose `overwrite` if new predictions should overwrite old ones in a folder
    Choose `add` if new predictions should be added to a folder
    :param models_config_path: path to json with models configuration
    """
    video_handler = VideoHandler(video_path=video_path,
                                 output_path=output_path,
                                 desired_frequency=frequency,
                                 starting_point=start_point,
                                 saving_strategy=saving_strategy,
                                 models_config_path=models_config_path)
    video_handler.divide_video()
    video_handler.annotate_events()
    video_handler.detect_lines_and_fields()
    video_handler.detect_objects()
    video_handler.save_results_to_files()


if __name__ == '__main__':
    perform_models(video_path='./data/output_5min.mp4',
                   output_path='./data/test_18_01',
                   frequency=1/20,
                   start_point=0,
                   saving_strategy='overwrite',
                   models_config_path='./data/configs/models_config.json')
