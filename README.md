# BSc-soccer-annotator

## Installation

In order to use this repository please follow these steps:


1. Clone directory to a folder : `git clone git@github.com:michalpiasecki0/BSc-soccer-annotator.git`
2. Move to cloned directory `cd <path_to_cloned_dir>`
3. Create venv: `python -m venv venv`
4. Activate environment: `source venv/bin/activate`
5. Install reqs: `pip install -r requirements.txt`
6. If you want to use automatic models, upload model weights:  
    Download `yolov7.pt` from https://github.com/WongKinYiu/yolov7/releases and place it in `automatic_models/object_detection/yolo`  
    Download 