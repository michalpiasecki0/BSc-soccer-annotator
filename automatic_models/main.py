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
                   start_point: float):
    video_handler = VideoHandler(video_path=video_path,
                                 output_path=output_path,
                                 desired_frequency=frequency,
                                 starting_point=start_point)
    video_handler.divide_video()
    video_handler.detect_lines_and_fields()
    video_handler.detect_objects()
    video_handler.save_results_to_files()

if __name__ == '__main__':
    args = parse_args()
    perform_models(video_path=args.video_path,
                   output_path=args.output_path,
                   frequency=args.frequency,
                   start_point=args.start_point)
