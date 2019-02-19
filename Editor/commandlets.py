# coding=utf-8
import subprocess
import shutil
import sys
import os
import logging
import pathlib
import io

import CONSTANTS
import Editor.editorutilities as editorUtilities

L = logging.getLogger(__name__)


class BaseUE4Commandlet:

    """
    Base class that handles calling engine commandlets and gathering / moving the logs and output to the correct
    location
    """

    def __init__(self, run_config, commandlet_name, log_file_name="", files=[], platform="Win64"):

        self.run_config = run_config
        self.commandlet_name = commandlet_name
        self.files = files
        self.platform = platform

        self.editor_util = editorUtilities.UEUtilities(run_config, self.platform)

        if log_file_name:
            self.log_file_name = log_file_name
        else:
            self.log_file_name = self.commandlet_name + ".log"

        commandlet_settings_config = self.run_config[CONSTANTS.COMMANDLET_SETTINGS]

        self.commandlet_settings = commandlet_settings_config[self.commandlet_name]

        # Getting paths and making them absolute
        self.project_root_path = pathlib.Path(self.run_config[CONSTANTS.PROJECT_FILE_PATH]).resolve()
        self.engine_root_path = pathlib.Path(self.run_config[CONSTANTS.ENGINE_ROOT_PATH]).resolve()
        self.raw_log_path = pathlib.Path(self.run_config[CONSTANTS.TARGET_LOG_FOLDER_PATH]).resolve()
        self.saved_logs_folder_path = pathlib.Path(self.run_config[CONSTANTS.SAVED_LOGS_FOLDER_PATH]).resolve()

        # Information about the relative structure of ue4
        self.ue_structure = self.run_config[CONSTANTS.UNREAL_ENGINE_STRUCTURE]

    def get_commandlet_settings(self):

        commandlet_name = self.commandlet_settings["command"]
        commandlet_prefix = "-run=" + commandlet_name
        # special flags that is used for extracting data from the engine for parsing

        return commandlet_prefix

    def get_command(self):
        """
        Constructs the command that runs the commandlet
        :return:
        """
        commandlet_prefix = self.get_commandlet_settings()

        # special flags that is used for extracting data from the engine for parsing
        commandlet_flags = self.get_commandlet_flags()

        flags_cmd = ""
        if commandlet_flags:
            flags_cmd = "-" + " -".join(commandlet_flags)

        args_list = []
        args_list.append(commandlet_prefix)

        if self.files:
            path_string = self._get_file_list_as_strings()
            args_list.append(path_string)
        if flags_cmd:
            args_list.append(flags_cmd)

        new_args = " ".join(args_list)

        engine_executable = self.editor_util.get_editor_executable_path().as_posix()
        project_file_path = self.run_config[CONSTANTS.PROJECT_FILE_PATH].as_posix()

        cmd = engine_executable + " " + project_file_path + " " + new_args + " -LOG=" + self.log_file_name + " -UNATTENDED"
        L.info(cmd)

        return cmd

    def _get_file_list_as_strings(self):

        path_string = ""
        for each_file_to_extract in self.files:

            path_string = path_string + " " + str(each_file_to_extract)

        return path_string

    def get_commandlet_flags(self):

        """
        Search for the the flags in the for the package extract and returns the default one if we find one
        :param commandlet_settings:
        :return:
        """

        commandlet_flags = self.commandlet_settings["flags"]
        return commandlet_flags

    def run(self):
        """
        Runs the command
        :return:
        """

        commandlet_command = self.get_command()

        L.info("Running commandlet: %s", commandlet_command)

        # Not sure why the info doesn't work
        print(commandlet_command)

        temp_dump_file = os.path.join(self.raw_log_path, self.log_file_name)

        if not os.path.exists(os.path.dirname(temp_dump_file)):
            os.mkdir(os.path.dirname(temp_dump_file))

        popen = subprocess.Popen(commandlet_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        with open(temp_dump_file, "w", encoding='utf-8') as fp:
            for line in popen.stdout:
                line = line.decode('utf-8').rstrip()
                print(line, flush=True)
                print(line, file=fp, flush=True)

        # Waiting for the process to close
        popen.wait()

        # quiting and returning with the correct return code
        if popen.returncode == 0:
            L.info("Command ran successfully")
        else:
            import sys
            L.warning("Process exit with exit code: %s", popen.returncode)
            sys.exit(popen.returncode)

    def get_source_log_file(self):
        """
        Get the path to the log file that is saved by the engine
        :return: source log file path
        """

        path = self.saved_logs_folder_path.joinpath(self.log_file_name)

        return path

    def get_target_log_file(self):
        """
        Get the path to the log file where it is stored for processing
        :return:  extracted log file
        """

        return os.path.join(self.raw_log_path, self.log_file_name)

    def move_log_to_report_folder(self):

        """
        Move the log file from the source location to the target location
        :return: None
        """

        shutil.copy(self.get_source_log_file(), self.get_target_log_file())

        return self.get_target_log_file()


class PackageInfoCommandlet(BaseUE4Commandlet):
    """ Runs the package info commandlet """
    def __init__(self, run_config, unreal_asset_file_paths, asset_type="Default"):
        """

        :param unreal_project_info:
        :param unreal_asset_file_path:  Absolute path to the unreal engine asset file
        :param each_chunk_hash:  list of package file hashes for archiving
        """

        # Initializes the object
        super().__init__(run_config, "PkgInfoCommandlet", files=unreal_asset_file_paths)

        self.unreal_asset_file_paths = unreal_asset_file_paths
        self.asset_type = asset_type
        self.generated_logs = []

    def has_custom_type_config(self):

        # The default asset type is always valid
        if self.asset_type == "Default":
            return True

        return self.asset_type in self.commandlet_settings["detail_extract_types"]

    def get_commandlet_flags(self):

        # The Default asset type just used the default flags
        if self.asset_type == "Default":
            return super(PackageInfoCommandlet, self).get_commandlet_flags()

        commandlet_flags = self.commandlet_settings["detailed_extract"]

        return commandlet_flags

    def run(self):
        """
        Prepares and runs the Package info commandlet
        :return: path to the log file
        """

        commandlet_command = self.get_command()
        print(commandlet_command)

        temp_dump_file = os.path.join(self.raw_log_path, "temp", "_tempDump.log")
        print(temp_dump_file)

        if not os.path.exists(os.path.dirname(temp_dump_file)):
            os.makedirs(os.path.dirname(temp_dump_file))

        with open(temp_dump_file, "w", encoding='utf-8', errors="ignore") as temp_out:
            subprocess.run(commandlet_command, stdout=temp_out, stderr=subprocess.STDOUT)

        self.split_temp_log_into_raw_files(temp_dump_file)

        # Deleting the temp file and folder
        # shutil.rmtree(os.path.dirname(temp_dump_file))

    def _register_log_path(self, path):
        self.generated_logs.append(path)

    def get_generated_logs(self):
        return self.generated_logs

    def split_temp_log_into_raw_files(self, temp_log_path):

        """
        Split the temp file into smaller pieces in the raw folder
        :param temp_log_path:
        :return:
        """

        out_log = None

        with io.open(temp_log_path, encoding='utf-8', errors="ignore") as infile:
            for i, line in enumerate(infile):
                if self.is_start_of_package_summary(line):

                    asset_name = self.get_asset_name_from_summary_line(line)
                    path = self.get_out_log_path(asset_name)

                    self._register_log_path(path)

                    if not out_log:
                        # If we have never saved anything open a new file
                        out_log = io.open(path, "w", encoding='utf-8', errors="ignore")
                        # Adding the path to the log so we can move it to the archive folder when we finish
                    else:
                        # Closing the last file that was written into
                        out_log.close()

                        # Opening an new file with a new path
                        out_log = open(path, "w")
                        # Adding the path to the log so we can move it to the archive folder when we finish

                if out_log:
                    # Write the data into the logs
                    try:
                        out_log.write(line + "")
                    except UnicodeEncodeError:
                        L.warning("Unable to process line" + str(i))

        if out_log:
            out_log.close()

    def get_out_log_path(self, asset_name):
        """
        Constructs the name of the output log file
        :return:
        """

        asset_file_name = asset_name + "_" + self.asset_type + ".log"
        path = pathlib.Path(self.raw_log_path).joinpath(asset_file_name)

        return path

    @staticmethod
    def is_start_of_package_summary(line):

        if "Package '" and "' Summary" in line:
            return True
        else:
            return False

    @staticmethod
    def get_asset_name_from_summary_line(line):

        """
        :return: name of the asset being worked on
        """

        split = line.split(" ")
        split.pop()
        asset_path = split[len(split)-1]

        asset_path_split = asset_path.split("/")

        asset_name = asset_path_split[len(asset_path_split)-1]
        asset_name = asset_name.replace("'", "")

        return asset_name


class ResavePackages(BaseUE4Commandlet):

    def __init__(self, unreal_paths_object):
        super().__init__(unreal_paths_object, commandlet_name="ResavePackages")


class ResaveAllBlueprints(BaseUE4Commandlet):
    def __init__(self, unreal_paths_object):
        super().__init__(unreal_paths_object, commandlet_name="ResaveAllBlueprints")


class CompileAllBlueprints(BaseUE4Commandlet):
    def __init__(self, unreal_paths_object):
        super().__init__(unreal_paths_object, commandlet_name="CompileAllBlueprints")


class RebuildLightingCommandlet(BaseUE4Commandlet):
    def __init__(self, unreal_paths_object):
        super().__init__(unreal_paths_object, commandlet_name="BuildLighting")


class FillDDCCacheCommandlet(BaseUE4Commandlet):
    def __init__(self, unreal_paths_object):
        super().__init__(unreal_paths_object, commandlet_name="FillDDCCache")