# coding=utf-8
import os
import pathlib
import CONSTANTS
import logging


L = logging.getLogger(__name__)


class ProjectPaths(BasePaths.BasePaths):

    def __init__(self, output_version="Default", files=None):
        """
        Return paths and information from file paths within the
        unreal project
        """

        super().__init__(output_version, files)

        # The files input is converted into a list on the parent if no value is passed in
        # If there is nothing passed in we process the whole content folder

        if len(self.files) == 0:
            L.debug("No file specified,  using all content files")
            self.files = self.get_all_content_files()

            L.debug("Found %s files ", len(self.files))

    def get_log_file_path(self):

        project_path = self.get_project_root_folder()
        project_name = self.get_project_name()
        log_file_path = pathlib.Path(project_path, "Saved", "Logs", project_name + ".log")

        return log_file_path

    def get_project_path(self):

        # should only return a single one

        uproject_files = list(self.project_root_folder.glob('*.uproject'))
        project_file = uproject_files[0]


        return project_file

    def get_ue4_editor_path(self):

        settings = self.load_settings(CONSTANTS.SETTINGS_FILE_NAME)
        path = self._read_path_from_config(settings["Unreal_Engine_Path"])
        L.debug("Configured path in settings file: %s", path)

        return path

    def get_ue4_UnrealBuildTool_path(self):

        p = os.path.join(self.settings.get_engine_path(), "Binaries", "DotNET", "UnrealBuildTool.exe")
        L.info("Build tool path: %s", p)

        return p

    def get_ue4_editor_executable_path(self):
        p = self.settings.get_engine_path()
        p = os.path.join(p, "Binaries", "Win64", "UE4Editor-Cmd.exe")

        return p

    def get_html_template_file(self, file_name):
        path = os.path.join(self.get_web_template_folder(), file_name)
        L.debug(path)

        return path

    def get_staged_build_path(self):
        # TODO Not have these paths hardcoded.  Need to support different types of builds
        # TODO Should also support it when the build is archived in a different folder
        p = self.project_root_folder.joinpath("Saved", "StagedBuilds", "WindowsNoEditor")

        return p

    def get_project_name(self):

        return self.get_project_path().stem

    def get_content_folder_path(self):

        content_dir = self.get_project_path().parent.joinpath('Content')
        return content_dir

    def get_project_root_folder(self):
        return os.path.dirname(self.get_project_path())

    def get_project_log(self):

        project_logfile_path = os.path.join(self.get_project_root_folder(), "Saved", "Logs",
                                            self.get_project_name()) + ".log"
        return project_logfile_path

    def get_log_folder_path(self):
        log_folder_path = os.path.join(self.get_project_root_folder(), "Saved", "Logs")
        return log_folder_path

    def get_all_content_files(self):

        content_dir = self.get_content_folder_path()

        file_list = self.get_files_from_path(content_dir, "uasset")
        file_list.extend(self.get_files_from_path(content_dir, "umap"))

        return file_list

    def add_esc_char_to_path(self, input_string):

        output = input_string.replace(" ", "\\ ")
        return output

