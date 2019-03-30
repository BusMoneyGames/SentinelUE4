import ue4_constants
import pathlib


class UE4ClientUtilities:

    def __init__(self, run_config):
        self.run_config = run_config

    def get_test_build_paths(self):
        import pprint

        environment = self.run_config[ue4_constants.ENVIRONMENT_CATEGORY]
        sentinel_paths = self.run_config[ue4_constants.SENTINEL_PROJECT_STRUCTURE]

        relative_build_path = sentinel_paths[ue4_constants.SENTINEL_BUILD_PATH]
        artifact_root_path = pathlib.Path(environment[ue4_constants.SENTINEL_ARTIFACTS_ROOT_PATH])

        pprint.pprint(environment[ue4_constants.SENTINEL_ARTIFACTS_ROOT_PATH])

        builds_path = artifact_root_path.joinpath(relative_build_path)

        build_directories = {}
        for each in builds_path.glob("*"):
            build_directories[each.name] = each

        pprint.pprint(build_directories)
        return build_directories
