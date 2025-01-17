import numpy as np
import os, sys, glob, pickle
from pathlib import Path
from os.path import join, exists, dirname, abspath
import random
import jaklas
import logging

# from .base_dataset import BaseDataset, BaseDatasetSplit
# from ..utils import make_dir, DATASET
import ml3d.torch as ml3d
from ml3d.datasets.base_dataset import BaseDataset, BaseDatasetSplit
from ml3d.utils import make_dir, DATASET

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(asctime)s - %(module)s - %(message)s',
)
log = logging.getLogger(__name__)


class Jakarto3D(BaseDataset):
    """
    This class is used to create a dataset based on the Jakarto3D dataset, and used in visualizer, training, or testing. 
    You can download Jakarto3D dataset on TODO url
    """

    def __init__(self, dataset_path, name='Jakarto3D', **kwargs):
        super().__init__(dataset_path=dataset_path, name=name, **kwargs)

        cfg = self.cfg

        self.label_to_names = self.get_label_to_names()
        self.dataset_path = dataset_path
        self.num_classes = len(self.label_to_names)
        self.label_values = np.sort([k for k, v in self.label_to_names.items()])
        self.label_to_idx = {l: i for i, l in enumerate(self.label_values)}
        self.ignored_labels = np.array([0])

        train_path = self.dataset_path + "/train/"
        self.train_files = glob.glob(train_path + "/*.las")
        self.val_files = [
            f for f in self.train_files if Path(f).name in cfg.val_files
        ]
        self.train_files = [
            # f for f in self.train_files if f not in self.val_files
            f for f in self.train_files
        ]

        test_path = self.dataset_path + "/test/"
        self.test_files = glob.glob(test_path + "/*.las")

    @staticmethod
    def get_label_to_names():
        """
	Returns a label to names dictonary object.
        
        Returns:
            A dict where keys are label numbers and 
            values are the corresponding names.
    """
        label_to_names = {
            0: 'unclassified',
            1: 'ground',
            2: 'building',
            3: 'natural-vegetation',
            4: 'cars',
            5: 'pole-road_sign-traffic_light',
            6: 'electric-wires'
        }
        return label_to_names

    def get_split(self, split):
        return Jakarto3DSplit(self, split=split)
        """Returns a dataset split.
        
        Args:
            split: A string identifying the dataset split that is usually one of
            'training', 'test', 'validation', or 'all'.
        Returns:
            A dataset split object providing the requested subset of the data.
	"""

    def get_split_list(self, split):
        """Returns a dataset split.
        
        Args:
            split: A string identifying the dataset split that is usually one of
            'training', 'test', 'validation', or 'all'.
        Returns:
            A dataset split object providing the requested subset of the data.
			
		Raises:
			ValueError: Indicates that the split name passed is incorrect. The split name should be one of
            'training', 'test', 'validation', or 'all'.
    """
        if split in ['test', 'testing']:
            files = self.test_files
        elif split in ['train', 'training']:
            files = self.train_files
        elif split in ['val', 'validation']:
            files = self.val_files
        elif split in ['all']:
            files = self.val_files + self.train_files + self.test_files
        else:
            raise ValueError("Invalid split {}".format(split))

        return files

    def is_tested(self, attr):
        """Checks if a datum in the dataset has been tested.
        
        Args:
            dataset: The current dataset to which the datum belongs to.
			attr: The attribute that needs to be checked.
        Returns:
            If the dataum attribute is tested, then resturn the path where the attribute is stored; else, returns false.
			
	"""
        cfg = self.cfg
        name = attr['name']
        path = cfg.test_result_folder
        store_path = join(path, self.name, name + '.txt')
        if exists(store_path):
            print("{} already exists.".format(store_path))
            return True
        else:
            return False

    def save_test_result(self, results, attr):
        """Saves the output of a model.
        Args:
            results: The output of a model for the datum associated with the attribute passed.
            attr: The attributes that correspond to the outputs passed in results.
    """

        cfg = self.cfg
        name = attr['name'].split('.')[0]
        path = cfg.test_result_folder
        make_dir(path)

        pred = results['predict_labels'] + 1
        store_path = join(path, self.name, name + '.txt')
        make_dir(Path(store_path).parent)
        np.savetxt(store_path, pred.astype(np.int32), fmt='%d')

        log.info("Saved {} in {}.".format(name, store_path))


class Jakarto3DSplit(BaseDatasetSplit):

    def __init__(self, dataset, split='training'):
        super().__init__(dataset, split=split)

    def __len__(self):
        return len(self.path_list)

    def get_data(self, idx):
        pc_path = self.path_list[idx]
        log.debug("get_data called {}".format(pc_path))
        data = jaklas.read(pc_path)

        points = (data["xyz"] - np.mean(data["xyz"], axis=0)).astype("float32")

        labels = data["Label"].astype("int32")

        # feat = np.vstack((data["red"], data["green"], data["blue"])).T.astype("float32")
        feat = None 

        data = {'point': points, 'feat': feat, 'label': labels}

        return data

    def get_attr(self, idx):
        pc_path = Path(self.path_list[idx])
        name = pc_path.name.replace('.las', '')

        pc_path = str(pc_path)
        split = self.split
        attr = {'idx': idx, 'name': name, 'path': pc_path, 'split': split}
        return attr


DATASET._register_module(Jakarto3D)