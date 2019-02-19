# coding=utf-8
import subprocess
import os
import sys

import CONSTANTS


class ClientRunner:
    """Handles running game clients"""
    def __init__(self, game_path_obj):
        self.game_path_obj = game_path_obj

    def run_startup_test(self):
        # TODO somehow get the test name better

        cmd = self.game_path_obj.get_startup_test_file_path()

        os.chdir(os.path.join(os.path.abspath(sys.path[0]), os.path.dirname(cmd)))
        subprocess.run(cmd)

