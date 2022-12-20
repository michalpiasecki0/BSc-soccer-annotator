from handlers import VideoHandler
from argparse import ArgumentParser


def parse_args():
    argument_parser = ArgumentParser()
    argument_parser.add_argument('--video_path', type=str, help='direct/relative path to video to be analyzed')
    argument_parser.add_argument('--output_path', type=str, help='Path to folder where all results from models '
                                                                 'should be saved')
    argument_parser.add_argument('--frequency', type=float, help='Frequency for video division')
    argument_parser.add_argument('--start_point', type=float, help='Starting point to divide video')
    return argument_parser.parse_args()

def perform_models(video_path: str,
                   output_path: str,
                   frequency: float,
                   start_point: float = 0) -> None:
    """

    :param video_path: path to a video file (currently mp4 format is supported)
    :param output_path: path to output folder, where all model results are saved
    :param frequency: fps for models (e.G )
    :param start_point: starting point
    :return:
    """
    video_handler = VideoHandler(video_path=video_path,
                                 output_path=output_path,
                                 desired_frequency=frequency,
                                 starting_point=start_point)
    video_handler.divide_video()
    video_handler.detect_lines_and_fields()
    video_handler.detect_objects()
    video_handler.save_results_to_files()

if __name__ == '__main__':
    perform_models(video_path='data/test.mp4',
                   output_path='../matches/2022-03-1_team1_team2',
                   frequency=1/5,
                   start_point=0)
