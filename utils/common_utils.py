import datetime
import logging
import os
import os.path


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def setup_logger_to_console_file(log_file_path, log_level=None):
    if not log_level:
        log_level = logging.INFO

    # logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
    log_formatter = logging.Formatter("%(asctime)s %(levelname)-5.5s %(module)-10.10s %(funcName)-10.10s  %(message)s")
    root_logger = logging.getLogger()

    file_handler = logging.FileHandler(log_file_path)
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.setLevel(log_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)


def get_timestamped_file_name(root_path, base_name, extension=None):
    if not extension:
        extension = "txt"

    if "~" in str(root_path):
        root_path = root_path.expanduser(root_path)

    log_file_path = root_path.joinpath(
        '{}_{}.{}'.format(base_name, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'), extension))
    count = 0
    while os.path.isfile(log_file_path) and count < 2000:
        log_file_path = root_path.joinpath(
            '{}_{}.{}'.format(base_name, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'), extension))
        count += 1
    return log_file_path


def get_log_file_path(root_path, base_name):
    if "~" in root_path:
        root_path = os.path.expanduser(root_path)
    if not os.path.exists(root_path):
        os.mkdir(root_path)
    log_file_path = os.path.join(root_path,
                                 '{}_{}.txt'.format(base_name, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')))
    count = 0
    while os.path.isfile(log_file_path) and count < 2000:
        log_file_path = os.path.join(root_path, '{}_{}.txt'.format(base_name, datetime.datetime.now().strftime(
            '%Y-%m-%d_%H-%M-%S')))
        count += 1
    return log_file_path


EDITOR_EXE = "notepad++.exe"


def open_file_in_editor(file_path):
    rel_path = os.path.relpath(file_path)
    if os.path.isfile(rel_path):
        os.system("{} {}".format(EDITOR_EXE, rel_path))
    else:
        logging.debug("The path {} is not a valid file. Cannot open it".format(file_path))
