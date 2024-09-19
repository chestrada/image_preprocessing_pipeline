#!/bin/bash

# echo "Setting up conda environment..." 

# conda env create -f environment.yml

# echo "done." 

# conda activate stitching

# echo "Running pip install..." 

# pip install requirements.txt

# echo "done." 

echo "Updating image_preprocesing_pipeline module" 

# if [ -d "ZetaStitcher" ]; then
#     echo "ZetaStitcher directory already exists. Pulling the latest changes."
#     cd ZetaStitcher
#     git pull origin master
#     cd ..
# else
#     git clone https://github.com/LifeCanvas-Technologies/ZetaStitcher.git
# fi

git remote add upstream https://github.com/ucla-brain/image-preprocessing-pipeline.git

git fetch upstream

git checkout main

git merge upstream/main


echo "done." 


