# BSc-soccer-annotator
Tool for manual and automatic football match videos annotation.  
  
This work was developed by *Jan Gąska*, *Michał Piasecki* and *Konstanty Kraszewski* as a project for Bachelor's diploma thesis.  
*Ph.D. Anna Wróblewska* and *MSc Seweryn Karolina* were thesis supervisors.  


## Installation

In order to use this repository please follow these steps:


1. Clone directory to a folder : `git clone git@github.com:michalpiasecki0/BSc-soccer-annotator.git`
2. Move to cloned directory `cd <path_to_cloned_dir>`
3. Create venv: `python -m venv venv`
4. Activate environment: `source venv/bin/activate`
5. Install reqs: `pip install -r requirements.txt`
6. If you want to use automatic models, please follow instruction, which is located in [automatic_models](automatic_models)
7. To run the application type (through the level of the directory): `streamlit run ui/ui_streamlit.py`
