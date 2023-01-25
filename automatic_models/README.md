# Automatic models module

## Description
This module aims to automatize annotations for football video matches.
In particular it automatizes following tasks:
1. Player and ball detection
2. Event Annotation
3. Field lines detection
4. Football field segmentation

## Usage 
In order to use this module make sure, you have completed installation steps mentioned on [main page]https://github.com/michalpiasecki0/BSc-soccer-annotator

It might be used standalone or together with Manual Annotator packed in `ui/ui_streamlit`.

## Usage from remote repository

In order to use models, once must do following steps:
1. download models weights from `https://drive.google.com/uc?id=1kgc6wfgdIDsHBhFMAr6YwTWbrigNv_UB&export=download`  
and place them in `lines_and_field_detection/out` folder.
2. Add additional python interpreter path pointing to `automatic_models/lines_and_field_detection` folder.
