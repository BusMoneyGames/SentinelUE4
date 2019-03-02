import pathlib
from SentinelConfig import CONSTANTS


class Validate:

    def __init__(self, run_config):

        self.run_config = run_config

        self.environment_structure = self.run_config[CONSTANTS.ENVIRONMENT_CATEGORY]
        self.sentinel_structure = self.run_config[CONSTANTS.SENTINEL_PROJECT_STRUCTURE]

        sentinel_root_path = pathlib.Path(self.environment_structure[CONSTANTS.SENTINEL_ARTIFACTS_ROOT_PATH])

        self.processed_path = sentinel_root_path.joinpath(self.sentinel_structure[CONSTANTS.SENTINEL_PROCESSED_PATH])

    def run(self):

        for each_file in self.processed_path.glob("**/*.json"):
            print(each_file)
