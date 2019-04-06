# coding=utf-8
import subprocess
import ue4_constants

if __package__ is None or __package__ == '':
    import clientutilities
else:
    from . import clientutilities


class GameClientRunner:
    """Handles running game clients"""
    def __init__(self, run_config, build_profile, test_name):
        self.test_name = test_name
        self.run_config = run_config

        self.client_utilities = clientutilities.UE4ClientUtilities(run_config)

    def run(self):
        print("Running baby!")