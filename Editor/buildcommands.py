# coding=utf-8
import subprocess
import os
import logging
import CONSTANTS
import pathlib
import Editor.editorutilities as editorUtilities
L = logging.getLogger(__name__)


class BaseUnrealBuilder:
    """
    Base class for triggering builds for an unreal engine project
    """

    def __init__(self, run_config, build_config_name="default"):

        """
        :param unreal_project_info:
        """

        self.run_config = run_config
        self.all_build_settings = self.run_config[CONSTANTS.UNREAL_BUILD_SETTINGS_STRUCTURE]

        # TODO Add logic to be able to switch the build settings
        self.build_config_name = build_config_name
        self.build_settings = self.all_build_settings[self.build_config_name]

        self.platform = self.build_settings[CONSTANTS.UNREAL_BUILD_PLATFORM_NAME]
        self.editor_util = editorUtilities.UEUtilities(run_config, self.platform)

        self.project_root_path = pathlib.Path(run_config[CONSTANTS.PROJECT_FILE_PATH]).parent
        self.sentinel_project_structure = self.run_config[CONSTANTS.SENTINEL_PROJECT_STRUCTURE]

        sentinel_project_name = self.sentinel_project_structure[CONSTANTS.SENTINEL_PROJECT_NAME]
        sentinel_logs_path = self.sentinel_project_structure[CONSTANTS.SENTINEL_RAW_LOGS_PATH]

        self.log_output_folder = self.project_root_path.joinpath(sentinel_project_name,
                                                                 sentinel_logs_path)

        self.log_output_file_name = "Default_Log.log"

    @staticmethod
    def _prefix_config_with_dash(list_of_strings):

        new_list = []
        for each in list_of_strings:
            new_list.append("-"+each)

        return new_list

    def get_build_command(self):
        """
        Needs to be overwritten on child
        :return:
        """
        return ""

    def run(self):
        """
        No logic in the base class, should be overwritten on the child
        :return:
        """

        cmd = self.get_build_command()

        path = self.log_output_folder.joinpath(self.log_output_file_name)

        if not path.parent.exists():
            os.makedirs(path.parent)

        print(cmd)

        popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        with open(path, "w", encoding='utf-8') as fp:
            for line in popen.stdout:
                line = line.decode('utf-8').rstrip()
                print(line, flush=True)
                print(line, file=fp, flush=True)

        # Waiting for the process to close
        popen.wait()

        # quiting and returning with the correct return code
        if popen.returncode == 0:
            L.info("Command run successfully")
        else:
            import sys
            L.warning("Process exit with exit code: %s", popen.returncode)
            sys.exit(popen.returncode)


class UnrealEditorBuilder(BaseUnrealBuilder):

    """
    Handle building the unreal editor binaries for the game project
    """

    def __init__(self, run_config):
        """
        Uses the settings from the path object to compile the editor binaries for the project
        so that we can run a client build or commandlets
        :param unreal_project_info:
        """

        super().__init__(run_config)

        self.log_output_file_name = self.sentinel_project_structure[CONSTANTS.SENTINEL_DEFAULT_COMPILE_FILE_NAME]

    def get_build_command(self):
        """
        Construct the build command string
        :return: build command
        """

        project_path = "-project=" + "\"" + str(self.run_config[CONSTANTS.PROJECT_FILE_PATH]) + "\""

        # TODO after upgrading to 4.20 then I need to skip the project name to be able to compile the editor
        unreal_build_tool_path = self.editor_util.get_unreal_build_tool_path()

        cmd_list = [str(unreal_build_tool_path),
                    #self.unreal_project_info.get_project_name(),
                    "Development",  # The editor build is always development
                    self.platform,
                    project_path,
                    ]

        # Adding the compile flags at the end of the settings
        compile_flags = self._prefix_config_with_dash(self.build_settings[CONSTANTS.UNREAL_EDITOR_COMPILE_FLAGS])
        cmd_list.extend(compile_flags)

        cmd = " ".join(cmd_list)
        L.debug("Build command: %s", cmd)

        return cmd


class UnrealClientBuilder(BaseUnrealBuilder):
    """
    Handles making client builds of the game project that can be either archived for testing or deployed to the
    deploy location
    """

    def __init__(self, run_config, build_config_name="default"):
        """
        Use the settings from the path object to build the client based on the settings in the settings folder
        :param unreal_project_info:
        """
        super().__init__(run_config, build_config_name)

        self.log_output_file_name = self.sentinel_project_structure[CONSTANTS.SENTINEL_DEFAULT_COOK_FILE_NAME]
        self.editor_util = editorUtilities.UEUtilities(run_config, self.platform)

    def get_archive_directory(self):

        sentinel_output_root = self.sentinel_project_structure[CONSTANTS.SENTINEL_PROJECT_NAME]
        build_folder_name = self.sentinel_project_structure[CONSTANTS.SENTINEL_BUILD_PATH]
        out_dir = self.project_root_path.joinpath(sentinel_output_root, build_folder_name, self.build_config_name)

        out_dir = pathlib.Path(out_dir)
        if not out_dir.exists():
            os.makedirs(out_dir)

        return out_dir

    def get_build_command(self):
        """
        Construct the build command string
        :return: build command
        """

        project_path = pathlib.Path(self.run_config[CONSTANTS.PROJECT_FILE_PATH])
        engine_root = pathlib.Path(self.run_config[CONSTANTS.ENGINE_ROOT_PATH]).resolve()

        build_command_name = self.build_settings[CONSTANTS.UNREAL_BUILD_COMMAND_NAME]
        build_config = self.build_settings[CONSTANTS.UNREAL_BUILD_CONFIGURATION]

        # self.get_cook_list_string()

        run_uat_path = engine_root.joinpath("Engine", "Build", "BatchFiles", "RunUAT.bat")

        cmd_list = [str(run_uat_path),
                    build_command_name,
                    "-project=" + str(project_path),
                    "-clientconfig=" + build_config,
                    "-targetplatform=" + self.platform
                    ]

        config_flags = self._prefix_config_with_dash(self.build_settings[CONSTANTS.UNREAL_BUILD_CONFIG_FLAGS])

        if "-archive" in config_flags:
            archive_dir_flag = "-archivedirectory=" + str(self.get_archive_directory())
            config_flags.append(archive_dir_flag)

        cmd_list.extend(config_flags)
        cmd = " ".join(cmd_list)
        L.debug(cmd)

        return cmd

    def get_cook_list_string(self):
        # all_files = self.unreal_project_info.get_all_content_files()
        all_files = []
        maps_to_package = []
        for e in all_files:

            if e.suffix == ".umap":
                lower_name = e.name.lower()
                maps_to_package.append(lower_name)
                L.debug("Adding %s to cook list", lower_name)

                # TODO Add filtering based on prefixes from the settings file

        # TODO enable the maps to package flag again
        maps_to_package_flag = "-Map=\"" + "+".join(maps_to_package) + "\""

    def run(self):
        """
        Constructs the build command and runs it
        :return: None
        """

        super(UnrealClientBuilder, self).run()

    def package_for_testing(self):
        pass

