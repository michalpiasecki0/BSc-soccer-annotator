import torch
from dataclasses import dataclass
from automatic_models.event_annotation.CALF.inference.main import main
from typing import Optional, Dict


@dataclass
class EventAnnotatorConfig:
    """
    Dataclass used for storing object detection model configuration.
    """
    video_path: str = None
    load_weights: str = None
    test_only: bool = False
    challenge: bool = False
    K_params: torch.FloatTensor = None
    num_features: int = 512
    chunk_size: int = 120
    chunks_per_epoch: int = 18000
    evaluation_frequency: int = 20
    dim_capsule: int = 16
    receptive_field: int = 40
    lambda_coord: float = 5.0
    lambda_noobj: float = 0.5
    loss_weight_segmentation: float = 0.000367
    loss_weight_detection: float = 1.0
    batch_size: int = 32
    LR: float = 1e-03
    patience: int = 25
    GPU: int = -1
    max_num_workers: int = 4
    log_level: str = 'INFO'
    features: str = 'ResNET_PCA512.npy'
    max_epochs: int = 1000
    model_name: str = 'CALF_benchmark'
    framerate: int = 2 # modify
    confidence_threshold: float = 0.7 # modify
    device: str = 'cpu' # gpu/cpu modify
    save_predictions: bool = False # modify


class EventAnnotator:
    """
    EventAnnotator is responsible for detecting events during a video.
    Currently, CALF from Soccernet is used for this task.
    For more info, please check following link:
    https://github.com/SilvioGiancola/SoccerNetv2-DevKit/tree/main/Task1-ActionSpotting/CALF
    CALF folder contains implementation of CALF model, with  tweaks added by author of this code
    """
    def __init__(self,
                 video_path: str,
                 model_config: Optional[Dict] = None,
                 ):
        self.config = EventAnnotatorConfig()
        self.config.video_path = video_path
        if model_config:
            for key, value in model_config.items():
                setattr(self.config, key, value)
        self.results = dict()

    def __call__(self):
        self.results = main(self.config)
        return self.results, self.config
