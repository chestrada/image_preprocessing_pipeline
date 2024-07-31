from image_preprocessing_pipeline.process_images import merge_all_channels
from image_preprocessing_pipeline.convert import main
import subprocess
import os


def get_latest_tag():
    try:
        submodule_dir = os.path.dirname(__file__)
        
        latest_tag = subprocess.check_output(
            ['git', 'describe', '--tags', '--abbrev=0'],
            cwd=submodule_dir
        ).strip().decode('utf-8')
        
        return latest_tag
    except subprocess.CalledProcessError:
        return 'unknown'
