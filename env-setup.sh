#!/bin/bash

ENV_NAME="stitching"

# Check if conda is installed
if ! command -v conda &>/dev/null; then
    echo "Anaconda (or Miniconda) is not installed. Please install or load it before running this script."
    exit 1
fi

conda init bash
source ~/.bashrc

# Check if the environment already exists
if conda info --envs | grep -q "$ENV_NAME"; then
    echo "Activating existing conda environment: $ENV_NAME"
    source activate "$ENV_NAME"  # Use source activate for better compatibility
else
    echo "Creating and activating new conda environment: $ENV_NAME"
    conda env create -f environment.yml -n "$ENV_NAME"
    source activate "$ENV_NAME"
fi

echo "Environment ready"

echo "Updating image_preprocesing_pipeline module from source" 

# git remote add upstream https://github.com/ucla-brain/image-preprocessing-pipeline.git

# git fetch upstream

# git checkout main

# git merge upstream/main

yes | abs2rel

echo "done." 
