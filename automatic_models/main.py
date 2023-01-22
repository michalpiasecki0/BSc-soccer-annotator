"""This module serves as general API with automatic_models module"""

from handlers import VideoHandler
from argparse import ArgumentParser


def parse_args():
    argument_parser = ArgumentParser()
    argument_parser.add_argument('-in', '--video_path', required=True, type=str,
                                 help='direct/relative path to video to be analyzed')
    argument_parser.add_argument('-out', '--output_path', required=True, type=str,
                                 help='Path to folder where all results from models should be saved')
    argument_parser.add_argument('-freq', '--frequency', default=1, type=float,
                                 help='Models will divide video into frames with this '
                                      'frequency and perform actions on each frame.')
    argument_parser.add_argument('-start', '--starting_point', default=0, type=float,
                                 help='Models will start dividing video and provide '
                                      'annotations from this point in video. PLease provide this number in seconds.')
    argument_parser.add_argument('-save', '--saving_strategy', default='overwrite', type=str,
                                 help='Choose from add/overwrite. If latter new predictions overwrite older ones.')
    argument_parser.add_argument('-conf', '--models_config_path', default=None, type=str,
                                 help='Path to json with parameters for models.')
    argument_parser.add_argument('-p_e', '--perform_events', default=True, type=bool,
                                 help='If True model will perform event annotation')
    argument_parser.add_argument('-p_o', '--perform_objects', default=True, type=bool,
                                 help='If True model will perform object detection')
    argument_parser.add_argument('-p_lf', '--perform_lines_fields', default=True, type=bool,
                                 help='If True model will perform field segmentation and lines detection')

    return argument_parser.parse_args()


def perform_models(video_path: str,
                   output_path: str,
                   frequency: float,
                   starting_point: float = 0,
                   models_config_path: str = None,
                   saving_strategy: str = 'overwrite',
                   perform_events: bool = True,
                   perform_objects: bool = True,
                   perform_lines_fields: bool = True
                   ) -> None:
    """
    Perform automatic processing on video.
    :param video_path: path to a video file (currently mp4, mkv formats are supported)
    :param output_path: path to output folder, where all model results are saved
    :param frequency: Models will divide video into frames with this frequency and perform actions on each frame
    :param starting_point: Models will start dividing video and provide annotations from this point in video.
     Please provide this number in seconds.
    :param saving_strategy: add/overwrite. Choose `overwrite` if new predictions should overwrite old ones in a folder
     Choose `add` if new predictions should be added to a folder
    :param models_config_path: path to json with models configuration
    :param perform_events: If true, model performs event annotation
    :param perform_objects: If true model performs object detection
    :param perform_lines_fields: If true model performs lines and field detection
    """
    video_handler = VideoHandler(video_path=video_path,
                                 output_path=output_path,
                                 desired_frequency=frequency,
                                 starting_point=starting_point,
                                 saving_strategy=saving_strategy,
                                 models_config_path=models_config_path)
    video_handler.divide_video()

    if perform_events:
        try:
            video_handler.annotate_events()
            print('Events successfully annotated.')
        except IndexError:
            print('Unable to perform Event Annotator, because file is too short, make sure it is longer than 2 minutes')
    if perform_lines_fields:
        video_handler.detect_lines_and_fields()
        print('Lines and fields successfully detected.')
    if perform_objects:
        video_handler.detect_objects()
        print('Players successfully detected.')

    video_handler.save_results_to_files()
    print('Files saved.')


if __name__ == '__main__':
    perform_models(video_path='./data/output_5min.mp4',
                   output_path='./data/test_22_01',
                   frequency=0.05,
                   starting_point=0,
                   saving_strategy='overwrite',
                   models_config_path='./data/configs/models_config.json',
                   perform_events=True,
                   perform_objects=False,
                   perform_lines_fields=False)

    '''
    args = parse_args()
    print(args)

    perform_models(video_path=args.video_path,
                   output_path=args.output_path,
                   frequency=args.frequency,
                   starting_point=args.starting_point,
                   saving_strategy=args.saving_strategy,
                   models_config_path=args.models_config_path)
    '''
