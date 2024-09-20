#!/bin/bash

ENV_NAME="stitching"

# Check if conda is installed
if ! command -v conda &>/dev/null; then
    echo "Anaconda (or Miniconda) is not installed. Please install or load it before running this script."
    exit 1
fi

# Check if the environment already exists
if conda info --envs | grep -q "$ENV_NAME"; then
    echo "Activating existing Anaconda environment: $ENV_NAME"
    conda activate "$ENV_NAME"
else
    echo "Setting up conda environment..." 
    conda env create -f environment.yml -n "$ENV_NAME"
    conda init
    conda activate "$ENV_NAME"
    pip install -r requirements.txt
    if_error_echo "Problem installing pip requirements"
    echo "Environment ready"
fi

# echo "Updating image_preprocesing_pipeline module from source" 

# git remote add upstream https://github.com/ucla-brain/image-preprocessing-pipeline.git

# git fetch upstream

# git checkout main

# git merge upstream/main

# abs2rel

# echo "done." 
