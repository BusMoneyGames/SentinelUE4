# coding=utf-8
import CONSTANTS
import os
import subprocess
import shutil

from SentinelUE4.Game import GamePaths
from Utilities import fileutils
import logging

L = logging.getLogger(__name__)


def run_startup_test(path_obj):

    # Find the path to the build
    # Extract the build to a test directory
    # Run the _featuretests
    # Extract the saved folder from the _featuretests
    # Remove the test directory

    # Fetching the target build folder path
    build_folder_path = path_obj.get_output_data_path(CONSTANTS.BUILD_FOLDER_PATH)
    L.info("Build folder path: " + build_folder_path.as_posix())

    files = os.listdir(build_folder_path)
    build_name = "Unknown"
    zip_file_name = "Unknown.zip"

    target_testing_location = os.path.join(build_folder_path, "_testing")
    for each_file in files:
        if each_file.endswith(".zip"):
            zip_file_name = each_file
            build_name = each_file.split(".")[0]
            break

    tests_to_run = path_obj.settings.get_client_tests_to_run()

    for test_name in tests_to_run:
        L.info("Starting client test: %s", test_name)
        test_name_flag = test_name

        target_zip_path = os.path.join(build_folder_path, zip_file_name)

        fileutils.unzip_folder(target_zip_path, target_testing_location)
        game_paths = GamePaths.GamePaths(target_testing_location, build_name)

        # cmd
        exe_path = os.path.join(target_testing_location, build_name + ".exe")

        extra_settings = path_obj.settings.get_client_extra_settings_for_test(test_name)

        level = ""
        if extra_settings:

            if "map" in extra_settings:
                level = extra_settings["map"]

            test_name_flag += " -" + " -".join(extra_settings["extra_startup_flags"])

        cmd = exe_path + " " + level + " -" + test_name_flag
        L.info(cmd)
        subprocess.run(cmd)

        saved_folder = game_paths.get_saved_folder_path()

        # Moving the test results into the results folder
        client_test_results = path_obj.get_client_test_directory()
        test_target = os.path.join(client_test_results, test_name)

        if os.path.exists(test_target):
            L.info("Removing old test results from: %s", test_target)
            shutil.rmtree(test_target)

        shutil.copytree(saved_folder, test_target)
        shutil.rmtree(target_testing_location)

        L.info("Client test: %s finished", test_name)
