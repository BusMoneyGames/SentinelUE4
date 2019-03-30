import shutil

import ue4_constants
import sys
import pathlib
import logging

L = logging.getLogger(__name__)


class UE4EditorUtilities:

    def __init__(self, run_config, platform="Win64"):
        self.platform = platform
        self.run_config = run_config

        self.ue_structure = self.run_config[ue4_constants.UNREAL_ENGINE_STRUCTURE]
        self.environment_structure = self.run_config[ue4_constants.ENVIRONMENT_CATEGORY]

        self.project_root_path = pathlib.Path(self.environment_structure[ue4_constants.UNREAL_PROJECT_ROOT])

        self.engine_root_path = pathlib.Path(self.environment_structure[ue4_constants.ENGINE_ROOT_PATH])

    def get_editor_executable_path(self):

        file_name = self.ue_structure[ue4_constants.UNREAL_ENGINE_WIN64_CMD_EXE] + self._get_executable_ext()
        executable = self.engine_root_path.joinpath(self.ue_structure[ue4_constants.UNREAL_ENGINE_BINARIES_ROOT],
                                                    self.platform,
                                                    file_name
                                                    )

        executable = self.project_root_path.joinpath(executable).resolve()

        return executable

    def get_unreal_build_tool_path(self):

        engine_root_folder = self.project_root_path.joinpath(self.environment_structure[
                                                                 ue4_constants.ENGINE_ROOT_PATH]).resolve()

        engine_root_folder = engine_root_folder.joinpath("Engine")

        file_name = self.ue_structure[ue4_constants.UNREAL_ENGINE_UBT_EXE] + self._get_executable_ext()
        executable = self.engine_root_path.joinpath(engine_root_folder,
                                                    file_name
                                                    )

        L.debug("Found build tool at: %s, exists: %s ", executable, str(executable.exists()))

        if not executable.exists():
            L.error("Path not found!: %s ", executable)
            quit(1)

        return executable

    def _get_executable_ext(self):
        if self.platform == "Win64":
            return ".exe"
        else:
            sys.exit(1)

    def get_all_content_files(self):

        content_relative_path = self.run_config[ue4_constants.UNREAL_PROJECT_STRUCTURE][ue4_constants.UNREAL_CONTENT_ROOT_PATH]
        unreal_project_root = self.get_project_file_path().parent

        L.debug("Unreal Project Root: %s ", unreal_project_root)

        content_path = unreal_project_root.joinpath(content_relative_path).resolve()

        L.debug("Content Root Path: %s", content_path)
        files = []
        for i, each_file in enumerate(content_path.glob("**/*.uasset")):
            files.append(each_file)
            L.debug("Found: %s", each_file)

        return files

    def get_project_file_path(self):

        path = pathlib.Path(self.environment_structure[ue4_constants.UNREAL_PROJECT_ROOT])

        for e in path.glob("**/*.uproject"):
            return e

        L.error("Unable to find project file at: %s", path)
        quit(1)
        raise FileNotFoundError


def clean_unreal_project(project_root_folder):
    """

    :param project_root_folder: folder containing the uproject file
    :return:
    """

    project_root_folder = pathlib.Path(project_root_folder)
    root_folders_to_remove = ["Intermediate", "Saved", "Binaries", ".vs"]

    folders_to_remove = []

    for each_dir_to_remove in root_folders_to_remove:
        dir_to_remove = project_root_folder.joinpath(each_dir_to_remove)
        if dir_to_remove.exists():
            folders_to_remove.append(dir_to_remove)

    project_root_folder.joinpath("Plugins")

    for each_plugin in project_root_folder.joinpath("Plugins").glob("*"):
        for each_root_folder_to_remove in root_folders_to_remove:
            plugin_dir_to_remove = each_plugin.joinpath(each_root_folder_to_remove)
            if plugin_dir_to_remove.exists():
                folders_to_remove.append(plugin_dir_to_remove)

    # Deletes the folders that were found
    for each_folder in folders_to_remove:
        try:
            shutil.rmtree(each_folder.as_posix())
            print("Deleting: ", each_folder.as_posix())
        except Exception as e:
            print(e)
            print("Unable to remove ", each_folder.as_posix())