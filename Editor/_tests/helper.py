import os
import pathlib
import CONSTANTS
import json


def recursively_search_for_file_down_a_directory(file_suffix):
    """
    finds the folder path of the script
    :return: root path
    """

    script_file = pathlib.PurePath(os.path.realpath(__file__))

    # Walks down the folder structure looking for the uproject file to identify the root of the project
    level_to_check = len(script_file.parents) - 1

    while level_to_check >= 0:
        path_to_check = pathlib.Path(script_file.parents[level_to_check])
        for each_file in path_to_check.glob("*.*"):
            # Check if the file has the correct suffix
            if each_file.suffix == file_suffix:
                return each_file
        # Go lower
        level_to_check = level_to_check - 1

    print("No file found")
    return None


def get_path_config_for_test():
    uproject_file_path = recursively_search_for_file_down_a_directory(file_suffix=".uproject")

    # Test config file
    path = pathlib.Path("../../_test_config.json").resolve()

    # Read the config
    f = open(path)
    path_config = json.load(f)
    f.close()

    path_config[CONSTANTS.PROJECT_FILE_PATH] = uproject_file_path
    engine_relative_path = path_config[CONSTANTS.ENGINE_ROOT_PATH]

    # If the engine path in the config is not an absolute path then its relative to the project file
    if not pathlib.Path(engine_relative_path).is_absolute():
        # resolve the engine path relative to the project file location
        engine_path = uproject_file_path.parent.joinpath(path_config[CONSTANTS.ENGINE_ROOT_PATH]).resolve()
        path_config[CONSTANTS.ENGINE_ROOT_PATH] = engine_path

    return path_config
