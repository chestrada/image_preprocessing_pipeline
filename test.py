# from pystripe_forked.raw import raw_imsave, raw_imread
# from pystripe_forked.core import imread, imsave, _find_all_images
# from skimage.transform import resize
# from flat import update_progress
# import shutil
# import numpy as np
# import os
# import pandas as pd
# import pathlib
# from flat import get_flat_classifier
#
#
# input_path = pathlib.Path(
#     r"D:\downsample_ds_lightsheet\20210729_16_18_40_SW210318-07_R-HPC_15x_Zstep1um_50p_4ms_flat_applied_tif_8b_3bsh_ds\Ex_642_Em_680"
# )
# imgs_path = _find_all_images(input_path)
# save_path = pathlib.Path(
#     r"D:\downsample_ds_lightsheet\20210729_16_18_40_SW210318-07_R-HPC_15x_Zstep1um_50p_4ms_flat_applied_tif_8b_3bsh_ds_resized\Ex_642_Em_680"
# )
#
# i = 0
# total = len(imgs_path)
# for path in imgs_path:
#     if path.suffix == '.tif':
#         try:
#             i += 1
#             update_progress(i // total * 100)
#             img = imread(path)
#             new_path = save_path / path.relative_to(input_path)
#             if not new_path.parent.exists():
#                 new_path.parent.mkdir(parents=True)
#             if img.shape > (781, 781):
#                 img = resize(img, (781, 781), preserve_range=True, anti_aliasing=True)
#                 imsave(new_path, img.astype(np.uint8))
#             else:
#                 shutil.copy(path, new_path)
#         except Exception:
#             print(path)
#             print(Exception)
#             pass
#         # print(path)
#         # img = imread(path)
#         # new_path = str(path)[0:-3] + 'raw'
#         # print(new_path)
#         # raw_imsave(new_path, img.astype('uint16'))
#         # path.unlink()

# import sys
# from PyQt5.QtWidgets import (QWidget, QPushButton, QApplication,
#                              QGridLayout, QLCDNumber)
#
# class Example(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.Init_UI()
#
#     def Init_UI(self):
#         self.setGeometry(750, 300, 400, 300)
#         self.setWindowTitle('QGridLayout-QLCDNumber-calculator')
#
#         grid = QGridLayout()
#         self.setLayout(grid)
#
#         self.lcd = QLCDNumber()
#         grid.addWidget(self.lcd, 0, 0, 3, 0)
#         grid.setSpacing(10)
#
#         names = ['Cls', 'Bc', '',  'Close',
#                  '7',   '8',  '9', '/',
#                  '4',   '5',  '6', '*',
#                  '1',   '2',  '3', '-',
#                  '0',   '.',  '=', '+']
#
#         positions = [(i,j) for i in range(4,9) for j in range(4,8)]
#
#         for position, name in zip(positions, names):
#             print("position=`{}`, name=`{}`".format(position, name))
#             if name == '':
#                 continue
#
#             button = QPushButton(name)
#
#             grid.addWidget(button, *position)
#
#             button.clicked.connect(self.Cli)
#
#         self.show()
#
#     def Cli(self):
#         sender = self.sender().text()
#         ls = ['/', '*', '-', '=', '+']
#         if sender in ls:
#             self.lcd.display('A')
#         else:
#             self.lcd.display(sender)
#
#
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     ex = Example()
#     app.exit(app.exec_())

# def img_path_generator():
#     img_folder = pathlib.Path(r"F:\test")
#     try:
#         if img_folder.exists():
#             for root, dirs, files in os.walk(img_folder):
#                 for name in files:
#                     name_l = name.lower()
#                     if name_l.endswith(".raw") or name_l.endswith(".tif") or name_l.endswith(".tiff"):
#                         img_path = os.path.join(root, name)
#                         yield img_path
#     except StopIteration:
#         yield None
#
#
# generator = img_path_generator()
# print(next(generator))
# print(next(generator))
# print(next(generator))
# print(next(generator))

# path = pathlib.Path(r'F:\flat_data').rglob('*.csv')
# frames = []
# for file in path:
#     print(file)
#     frames += [pd.read_csv(file)]
# pd.concat(frames).drop_duplicates().to_csv(r'F:\flat_data\image_classes.csv')
# import os
# import sys
# import csv
# import psutil
# import pathlib
# import numpy as np
# import pandas as pd
# import pystripe_forked as pystripe
# from pystripe_forked.raw import raw_imread
# from scipy import stats
# from sklearn.linear_model import LogisticRegression
# from sklearn.ensemble import RandomForestClassifier
# from sklearn.model_selection import train_test_split
# from sklearn.preprocessing import StandardScaler
# from sklearn.neural_network import MLPClassifier
# from sklearn.neighbors import KNeighborsClassifier
# from sklearn.svm import SVC
# from sklearn.gaussian_process import GaussianProcessClassifier
# from sklearn.gaussian_process.kernels import RBF
# from sklearn.tree import DecisionTreeClassifier
# from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
# from sklearn.naive_bayes import GaussianNB
# from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
# from skimage.restoration import denoise_bilateral
# from multiprocessing import freeze_support, Process, Queue
# from queue import Empty
# from time import time, sleep


# def get_flat_classifier(training_data_path, train_test=False):
#     # model = LogisticRegression(max_iter=10000)  # 83.1%
#     model = RandomForestClassifier(
#         n_estimators=10,
#         # criterion="entropy",
#         min_samples_split=60,
#         n_jobs=psutil.cpu_count(logical=True)
#     )  # 89.8%
#     # model = SVC()  # 77.7%
#     # model = MLPClassifier(
#     #     activation='tanh',
#     #     hidden_layer_sizes=30,
#     #     # batch_size=1024,
#     #     max_iter=10000,
#     #     solver='adam',
#     #     learning_rate='adaptive',
#     #     learning_rate_init=0.01,
#     #     # tol=1e-6,
#     #     early_stopping=True,
#     #     shuffle=True
#     # )  # 84-85%
#     # model = KNeighborsClassifier(n_neighbors=9)  # 84.1%
#     # model = GaussianProcessClassifier()
#     # model = DecisionTreeClassifier(
#     #     max_depth=10,
#     #     min_samples_split=100
#     # )  # 89.3%
#     # model = AdaBoostClassifier(n_estimators=60)  # 87.7%
#     # model = QuadraticDiscriminantAnalysis()  # 80.8%
#     df = pd.read_csv(training_data_path)
#     x = df[["mean", "min", "max", "cv", "variance", "std", "skewness", "kurtosis"]]
#     x = x.to_numpy()
#     y = np.where(df['flat'].isin(['yes']), True, False)
#     if train_test:
#         x_train, x_test, y_train, y_test = train_test_split(x, y)
#         log_reg = model.fit(x_train, y_train)
#         print(f"Training set score: {log_reg.score(x_test, y_test)*100:.1f}%")
#     else:
#         log_reg = model.fit(x, y)
#         print(f"Training set score: {log_reg.score(x, y) * 100:.1f}%")
#     return model

# from flat import get_flat_classifier
# model = get_flat_classifier(r'F:\flat_data\image_classes.csv', train_test=True)

# import tsv
# from tsv.convert import convert_to_2D_tif
# from multiprocessing import freeze_support
#
# if __name__ == '__main__':
#     freeze_support()
#     volume = tsv.volume.TSVVolume.load(
#         r"D:\20210928_16_23_37_SM210705_01_BS_LS_15X_1000z_Compressed_flat_applied_8b_2bsh_ds_stitched_v4\Ex_642_Em_680_xml_import_step_5.xml")
#     convert_to_2D_tif(
#         volume,
#         r"C:\Users\kmoradi\Desktop\2D\img_{z:05d}.tif",
#         compression=None
#     )

# from pystripe_forked.core import read_filter_save
#
#
# read_filter_save(
#     r"D:\20211020_11_21_05_SM210705_02_4x_2000z_Compressed_stitched_v4\RES(8740x7355x3900)\090500\090500_098010\090500_098010_028000.tif",
#     r"D:\090500_098010_028000.tif",
#     (256, 256)
# )

from distributed import Client, progress
from multiprocessing import freeze_support

def inc(x):
    return x + 1


if __name__ == '__main__':
    freeze_support()
    client = Client()
    L = client.map(inc, range(10000))
    # total = client.submit(sum, L)
    print(progress(L))