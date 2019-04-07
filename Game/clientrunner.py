# coding=utf-8
import pathlib
import subprocess
import zipfile
import ue4_constants
import logging


if __package__ is None or __package__ == '':
    import clientutilities
else:
    from . import clientutilities

L = logging.getLogger(__name__)


class GameClientRunner:
    """Handles running game clients"""
    def __init__(self, run_config, build_profile, test_name):
        self.test_name = test_name
        self.run_config = run_config
        self.environment_config = self.run_config[ue4_constants.ENVIRONMENT_CATEGORY]
        self.build_profile = build_profile

        # TODO make this support other platforms
        self.test_suffix = ".bat"

        self.build_zip_file_path = pathlib.Path(self.get_build_profile_path())

    def get_build_profile_path(self):
        """Finds the path the the build zip file"""
        artifacts_path = pathlib.Path(self.environment_config[ue4_constants.SENTINEL_ARTIFACTS_ROOT_PATH])
        sentinel_internal_structure = self.run_config[ue4_constants.SENTINEL_PROJECT_STRUCTURE]

        build_folder_path = artifacts_path.joinpath(sentinel_internal_structure[ue4_constants.SENTINEL_BUILD_PATH])

        build_profile_path = artifacts_path.joinpath(build_folder_path, self.build_profile).with_suffix(".zip")

        L.debug("Build Profile Path: %s exists: %s", build_profile_path, build_profile_path.exists())
        return build_profile_path

    def does_build_exist(self):
        return self.build_zip_file_path.exists()

    def _extract_build_to_run_location(self, path):
        L.debug("Extracting to temporary location")

        out_path = pathlib.Path(path.parent).joinpath("_temp_client_run_dir", self.build_profile, self.test_name)
        with zipfile.ZipFile(path) as zf:
            zf.extractall(out_path)

        return out_path

    def run(self):
        # Extract path to temp directory:
        test_root_dir = self._extract_build_to_run_location(self.build_zip_file_path)
        # Run the build using the test command
        run_cmd = test_root_dir.joinpath(self.test_name).with_suffix(self.test_suffix)
        L.debug("run cmd path: %s exists: %s", run_cmd, run_cmd.exists())
        self._run_process(run_cmd)

        # Archive the saved folder

        # clean the build

        print("Running baby!")

    def _run_process(self, path):

        cmd = path.as_posix()
        popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


        """
        with open(path, "w", encoding='utf-8') as fp:
            for line in popen.stdout:
                line = line.decode('utf-8').rstrip()
                print(line, flush=True)
                print(line, file=fp, flush=True)
        """
        # Waiting for the process to close
        popen.wait()

        # quiting and returning with the correct return code
        if popen.returncode == 0:
            L.info("Command run successfully")
        else:
            import sys
            L.warning("Process exit with exit code: %s", popen.returncode)
            sys.exit(popen.returncode)



