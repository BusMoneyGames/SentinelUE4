# coding=utf-8
import subprocess
import CONSTANTS

if __package__ is None or __package__ == '':
    import clientutilities
else:
    from . import clientutilities


class GameClientRunner:
    """Handles running game clients"""
    def __init__(self, run_config, test_name = "default"):
        self.test_name = test_name
        self.run_config = run_config
        self.client_utilities = clientutilities.UE4ClientUtilities(run_config)
        self.run_startup_test()

    def run_startup_test(self):
        # TODO somehow get the test name better
        builds = self.client_utilities.get_test_build_paths()

        if self.test_name in builds:
            pass

