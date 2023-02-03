from pathlib import Path
import os
PATH_TO_AUTOMATIC_MODELS = list(Path('./').glob('**/automatic_models'))
if len(PATH_TO_AUTOMATIC_MODELS) != 1:
    raise Exception('Not explicit location of automatic models package')
else:
    PATH_TO_AUTOMATIC_MODELS = str(PATH_TO_AUTOMATIC_MODELS[0].resolve())
