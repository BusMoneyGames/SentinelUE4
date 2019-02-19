# coding=utf-8
import os
import CONSTANTS
import logging

L = logging.getLogger(__name__)


class GamePaths:

    def __init__(self, build_folder, game_name):
        self.build_root_folder = build_folder
        self.game_name = game_name

    def get_startup_test_file_path(self):
        return os.path.join(self.build_root_folder, CONSTANTS.CLIENT_RUN_STARTUP_TEST + ".bat")

    def get_saved_folder_path(self):
        saved_folder_path = os.path.join(self.build_root_folder, self.game_name, "Saved")
        L.debug(saved_folder_path)

        return saved_folder_path

    def get_log_file_path(self):

        saved_folder = self.get_saved_folder_path()
        log_file_path = os.path.join(saved_folder, "Logs", self.game_name + ".log")

        L.debug(log_file_path)

        return log_file_path




