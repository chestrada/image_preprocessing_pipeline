import os
import sys
import csv
import psutil
import pathlib
import numpy as np
import pandas as pd
import pystripe_forked as pystripe
from pystripe_forked.raw import raw_imread
from scipy import stats
from sklearn.linear_model import LogisticRegression
from skimage.restoration import denoise_bilateral
from multiprocessing import freeze_support, Process, Queue
from queue import Empty
from time import time, sleep


def get_flat_classifier(training_data_path):
    df = pd.read_csv(training_data_path)
    x = df[["mean", "min", "max", "cv", "variance", "std", "skewness", "kurtosis"]]
    x = x.to_numpy()
    y = np.where(df['flat'].isin(['yes']), True, False)
    model = LogisticRegression(max_iter=10000)
    log_reg = model.fit(x, y)
    print("Training set score: {:.3f}".format(log_reg.score(x, y)))
    return model


def img_path_generator(path):
    if path.exists():
        for root, dirs, files in os.walk(path):
            for name in files:
                name_l = name.lower()
                if name_l.endswith(".raw") or name_l.endswith(".tif") or name_l.endswith(".tiff"):
                    img_path = os.path.join(root, name)
                    yield img_path


def img_read(path):
    img_mem_map = None
    if path.lower().endswith(".tif") or path.lower().endswith(".tiff"):
        img_mem_map = pystripe.imread(path)
    elif path.lower().endswith(".raw"):
        img_mem_map = raw_imread(path)
    return img_mem_map


def update_progress(percent, prefix='progress', posix=''):
    percent = int(percent)
    hash_count = percent//10
    space_count = 10 - hash_count
    sys.stdout.write(f"\r{prefix}: [{'#' * hash_count}{' ' * space_count}] {percent}% {posix}")
    sys.stdout.flush()


def save_csv(path, list_2d):
    with open(path, 'w') as file:
        write = csv.writer(file)
        write.writerows(list_2d)


def get_img_stats(img_mem_map):
    if img_mem_map is None:
        return ['mean', 'min', 'max', 'cv', 'variance', 'std', 'skewness', 'kurtosis', 'n']
    img_mem_map = img_mem_map.flatten()
    img_nobs, (img_min, img_max), img_mean, img_variance, img_skewness, img_kurtosis = stats.describe(img_mem_map)
    img_std = np.sqrt(img_variance)
    img_cv = img_std / img_mean
    return [img_mean, img_min, img_max, img_cv, img_variance, img_std, img_skewness, img_kurtosis, img_nobs]


class MultiProcessImageProcessing(Process):
    def __init__(self, queue, classifier_model, img_path, sigma_spatial=1):
        Process.__init__(self)
        self.queue = queue
        self.classifier_model = classifier_model
        self.img_path = img_path
        self.sigma_spatial = sigma_spatial

    def run(self):
        t = time()
        img_mem_map_denoised = None
        try:
            img_mem_map = img_read(self.img_path)
            if img_mem_map is not None:
                # ['mean', 'min', 'max', 'cv', 'variance', 'std', 'skewness', 'kurtosis', 'n']
                img_stats = get_img_stats(img_mem_map)
                is_flat = self.classifier_model.predict([img_stats[0:-1]])
                if is_flat:
                    img_mem_map_denoised = denoise_bilateral(img_mem_map, sigma_spatial=self.sigma_spatial)
        except Exception as inst:
            print(f'Process failed for {self.img_path}.')
            print(type(inst))    # the exception instance
            print(inst.args)     # arguments stored in .args
            print(inst)
        self.queue.put([img_mem_map_denoised, time() - t])


def create_flat_img(img_source_path, flat_training_data_path,
                    cpu_physical_core_count=psutil.cpu_count(logical=False),
                    cpu_logical_core_count=psutil.cpu_count(logical=True),
                    max_images=1024, patience_before_skipping=10, skips=100, sigma_spatial=1, save_as_tiff=True):
    print()
    img_path_gen = iter(img_path_generator(img_source_path))
    img_flat_count = 0
    img_non_flat_count = 0
    queue = Queue()
    running_processes = 0
    sleep_durations = 1.0  # seconds
    print_time = 0
    img_flat_sum = np.zeros((1850, 1850), dtype='float64')
    classifier_model = get_flat_classifier(flat_training_data_path)

    there_is_img_to_process = True
    while img_flat_count < max_images and there_is_img_to_process:
        for run in range(cpu_logical_core_count - running_processes):
            img_path = next(img_path_gen, None)
            if img_path is None:
                there_is_img_to_process = False
                break
            MultiProcessImageProcessing(queue, classifier_model, img_path, sigma_spatial=sigma_spatial).start()
            running_processes += 1

        sleep(sleep_durations / cpu_physical_core_count)
        somethings_could_be_in_queue = True
        while somethings_could_be_in_queue:
            try:  # check the queue for the optimization results then show result
                [img_mem_map_denoised, sleep_durations] = queue.get(block=False)
                if running_processes > 0:
                    running_processes -= 1
                if img_mem_map_denoised is not None:
                    img_flat_sum += img_mem_map_denoised
                    img_flat_count += 1
                    if img_non_flat_count > 0:
                        img_non_flat_count -= 1
                else:
                    img_non_flat_count += 1
                    if img_non_flat_count > patience_before_skipping:
                        img_non_flat_count = 0
                        for skip in range(skips):
                            next(img_path_gen, None)
            except Empty:
                somethings_could_be_in_queue = False

        if time() - print_time > 2:
            progress = img_flat_count / max_images * 100
            update_progress(
                progress,
                prefix=img_source_path.name,
                posix=f'found: {img_flat_count}, time: {sleep_durations:.1f}s/thread')
            print_time = time()

    while running_processes > 0:
        try:  # check the queue for the optimization results then show result
            img_mem_map_denoised = queue.get(block=False)[0]
            running_processes -= 1
            if img_mem_map_denoised is not None:
                img_flat_sum += img_mem_map_denoised
                img_flat_count += 1
        except Empty:
            pass

    if img_flat_count > 0:
        img_flat_average = img_flat_sum / img_flat_count
        img_flat_average = denoise_bilateral(img_flat_average, sigma_spatial=sigma_spatial)
        img_flat = img_flat_average / np.max(img_flat_average)
        if save_as_tiff:
            pystripe.imsave(
                str(img_source_path.parent / (img_source_path.name + '_flat.tif')),
                img_flat,
                convert_to_8bit=False
            )
        update_progress(
            100, prefix=img_source_path.name, posix=f'found: {img_flat_count}, time: {sleep_durations:.1f}s/thread')
        return img_flat
    else:
        print("no flat image found!")
        raise RuntimeError


if __name__ == '__main__':
    freeze_support()
    AllChannels = ["Ex_488_Em_0", "Ex_561_Em_1", "Ex_642_Em_2"]  #
    SourceFolder = pathlib.Path("/media/kmoradi/Elements/20210729_16_18_40_SW210318-07_R-HPC_15x_Zstep1um_50p_4ms")
    # SourceFolder = pathlib.Path(__file__).parent
    for Folder in AllChannels:
        create_flat_img(SourceFolder/Folder, SourceFolder/"image_classes.csv")
    print()