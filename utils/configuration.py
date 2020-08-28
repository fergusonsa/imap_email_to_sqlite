import json
import logging
import pathlib

import flatten_dict

CONFIGURATION_TYPE_PYTHON = 'py'
CONFIGURATION_TYPE_JSON = 'json'

VALID_CONFIGURATION_TYPES = [
    # CONFIGURATION_TYPE_PYTHON,
    CONFIGURATION_TYPE_JSON]

logger = logging.getLogger(__name__)


def get_configuration(config_name, location_path, config_type):
    """

    :param config_name: The file name, not including the extension.
    :param location_path: Pathlib.Path instance . If None, then the user's home path is used.
    :param config_type: The type of file to be loaded. Should be one of @VALID_CONFIGURATION_TYPES
    """
    if not config_name:
        logger.warning('Cannot load config from None config')
        return None
    if config_type not in VALID_CONFIGURATION_TYPES:
        logger.warning('Cannot load invalid config type "{}"'.format(config_type))
        return None
    if not location_path:
        location_path = pathlib.Path('~')
    config_file_path = location_path.joinpath('{}.{}'.format(config_name, config_type))
    if '~' in str(config_file_path):
        config_file_path = config_file_path.expanduser()
    if config_file_path.is_file():
        if config_type == CONFIGURATION_TYPE_PYTHON:
            pass
        elif config_type == CONFIGURATION_TYPE_JSON:
            return json.load(open(config_file_path))
        else:
            logger.warning('Unable to load config file {} of unknown type {}'.format(config_file_path, config_type))
    else:
        logger.warning('Unable to find config file {}'.format(config_file_path))
    return None


def create_configuration_file_defaults(config_name, location_path, config_type, defaults):
    if not config_name:
        logger.warning('Cannot create config from None config')
        return None
    if config_type not in VALID_CONFIGURATION_TYPES:
        logger.warning('Cannot load invalid config type "{}"'.format(config_type))
        return None
    if not location_path:
        location_path = pathlib.Path('~')
    config_file_path = location_path.joinpath('{}.{}'.format(config_name, config_type))
    if '~' in str(config_file_path):
        config_file_path = config_file_path.expanduser()
    if config_file_path.is_file():
        if config_type == CONFIGURATION_TYPE_JSON:
            configs = json.load(open(config_file_path))
        else:
            logger.warning('Unable to load config file {} of unknown type {}'.format(config_file_path, config_type))
            return None
    else:
        configs = {}

    expected_configs_keys = set(flatten_dict.flatten(defaults).keys())
    existing_configs_keys = set(flatten_dict.flatten(configs).keys())
    missing_keys = expected_configs_keys - existing_configs_keys
    if missing_keys:
        for key_list in missing_keys:
            pass
        if config_file_path.parent.is_dir():
            config_file_path.touch()
    return configs
