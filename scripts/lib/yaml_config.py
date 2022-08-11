# YAML configuration loading
import yaml
import os

from yaml import FullLoader


def _merge(dict1, dict2, path=None):
    """merges dict2 into dict1"""
    if path is None:
        path = []
    for key in dict2:
        if key in dict1:
            if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                # sub-dict properties, merge them
                _merge(dict1[key], dict2[key], path + [str(key)])
            else:
                # dict1 property takes precedence
                pass
        else:
            dict1[key] = dict2[key]
    return dict1


def load_config(filename):
    """
    :param filename: Load config from yaml file with specified name.
    :return: dict
    """
    with open(filename, 'r') as config_file:
        config = yaml.load(config_file, Loader=FullLoader)

    if 'extend' in config:
        parent_file = os.path.dirname(filename) + os.path.sep + config['extend']
        parent_config = load_config(parent_file)
        _merge(config, parent_config)
        del config['extend']

    return config
