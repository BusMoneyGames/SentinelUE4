import hashlib
import io
import json
import logging
import os
import pathlib
import shutil
import subprocess

import ue4_constants
import Editor.LogProcesser.packageinfolog as PackageInfoLog
from Editor import commandlets, editorutilities


L = logging.getLogger(__name__)


class ProjectHashMap:
    """
    Takes in a list of files and generates a unique has value from them
    """

    def __init__(self, list_of_files):

        self.list_of_files = list_of_files

        self.hash_value_mapping = {}
        self.hash_values_in_project = []

        self._generate_hash_for_files()

    @staticmethod
    def _get_file_hash(file_path):
        """
        Reads a file and generates a hash value for it
        :return:
        """

        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)

        return hash_md5.hexdigest()

    def _generate_hash_for_files(self):
        """
        iterates through a list of files and generates a hash value for them
        :return:
        """

        for i, each_file in enumerate(self.list_of_files):
            file_hash_value = self._get_file_hash(each_file)

            # Making a simple list of hash values in the project
            self.hash_values_in_project.append(file_hash_value)

            # Creating a mapping with the hash value and the file path
            self.hash_value_mapping[file_hash_value] = each_file

            if i % 500 == 0:
                L.info("Generating Hash for %s out of %s", str(i), str(len(self.list_of_files)))

    def get_hash_from_filename(self, filename):

        for each_hash in self.hash_value_mapping:

            if str(self.hash_value_mapping[each_hash]) == filename:
                return each_hash

        L.warning("Unable to find hash from filename!")

        return ""


class ExtractedDataArchive:

    """
    Handles interacting with the archive both recovering data from there as well as updating it with new data
    """

    def __init__(self, path_to_archive, file_hash_mappings):
        self.archive_folder_path = path_to_archive
        self.project_hash_file_mappings = file_hash_mappings

        self.hash_values_in_archive = []

    def get_missing_files(self):
        """
        """

        missing_files = []
        # Go through each file and checks if its missing from the archive
        # Add to list if its missing

        for each_hash in self.project_hash_file_mappings:
            if not self.is_hash_value_in_archive(each_hash):
                missing_file = self.project_hash_file_mappings[each_hash]

                L.debug("Missing from archive %s", missing_file)
                missing_files.append(str(missing_file))

        return missing_files

    def is_hash_value_in_archive(self, value):
        """
        Check if a hash value exists in the archive
        :param value: hash value
        :return:
        """

        hash_values_in_archive = self._get_hash_values_from_archive()

        if value in hash_values_in_archive:
            return True
        else:
            return False

    def _get_hash_values_from_archive(self):
        """
        search through the archive to look for folder names with hash values
        :return:
        """

        # TODO make it so that this can be somewhat cached but make sure that we can refresh if we know
        # That the contents of the folder has changed

        self.hash_values_in_archive = []
        for each_file in self.archive_folder_path.glob("*"):
            each_file: pathlib.Path = each_file

            if each_file.is_dir():
                hash_value = each_file.name
                self.hash_values_in_archive.append(hash_value)

        return self.hash_values_in_archive



class BasePackageInspection:

    def __init__(self, run_config):
        L.info("Starting Package Inspection")

        self.run_config = run_config
        self.environment_config = run_config[ue4_constants.ENVIRONMENT_CATEGORY]
        self.sentinel_structure = run_config[ue4_constants.SENTINEL_PROJECT_STRUCTURE]
        self._construct_paths()

        self.editor_util = editorutilities.UE4EditorUtilities(run_config)

        self._clear_old_data_from_raw()

    def _construct_paths(self):
        """Makes the paths for outputs inside of the root artifact folder"""

        self.sentinel_root = pathlib.Path(self.environment_config[ue4_constants.SENTINEL_ARTIFACTS_ROOT_PATH])
        L.debug("Sentinel Root: %s ", self.sentinel_root)

        self.archive_folder_path = pathlib.Path(self.environment_config[ue4_constants.SENTINEL_CACHE_ROOT])

        self.raw_data_dir = self.sentinel_root.joinpath(self.sentinel_structure[
                                                            ue4_constants.SENTINEL_RAW_LOGS_PATH]).resolve()

        self.processed_path = self.sentinel_root.joinpath(self.sentinel_structure[
                                                              ue4_constants.SENTINEL_PROCESSED_PATH]).resolve()

        if not self.archive_folder_path.exists():
            os.makedirs(self.archive_folder_path)
        if not self.raw_data_dir.exists():
            os.makedirs(self.raw_data_dir)
        if not self.processed_path.exists():
            os.makedirs(self.processed_path)

    def run(self):
        """
        Does a simple engine extract for asset to be able to determine asset type and other basic info
        """

        project_files = self.editor_util.get_all_content_files()
        L.info("UE project has: %s files total", len(project_files))

        # hash mapping for the files in the project
        hash_mapping = ProjectHashMap(project_files)
        L.info("Hash Mapping completed")

        # Compares the hash values with what has already been archived
        archive_object = ExtractedDataArchive(self.archive_folder_path, hash_mapping.hash_value_mapping)

        # Return a list of the missing files
        missing_file_list = archive_object.get_missing_files()
        L.info("%s files need to be refresh", len(missing_file_list))
        L.debug("Missing files:  %s", "\n".join(missing_file_list))

        chunks_of_files_to_process = split_list_into_chunks(missing_file_list, 100)

        #  This is where we go through all the to be able to get information about paths and types
        self._extract_from_files(chunks_of_files_to_process)
        # self._extract_detailed_package_info()

        # self.recover_files_from_archive()

    def _clear_old_data_from_raw(self):

        if self.raw_data_dir.exists():
            shutil.rmtree(self.raw_data_dir)

    def _clear_data_from_archive(self):
        if self.raw_data_dir.exists():
            shutil.rmtree(self.raw_data_dir)

    def _get_list_of_files_from_hash(self, list_of_hashes):
        """
        Returns a file list from the list a list of hashes
        :param list_of_hashes:
        :return:
        """

        file_list = []
        for each_hash in self.pkg_hash_obj.hash_value_mapping:
            if each_hash in list_of_hashes:
                file_list.append(
                    self.pkg_hash_obj.hash_value_mapping[each_hash])

        return file_list

    def _extract_from_files(self, chunks_of_files_to_process):

        # TODO deals the case where the user deletes files
        for i, each_chunk in enumerate(chunks_of_files_to_process):

            package_info_run_object = PackageInfoCommandlet(self.run_config, each_chunk)

            L.info("Starting chunk %s out of %s ", i + 1, str(len(chunks_of_files_to_process)))

            # Runs the extract
            package_info_run_object.run()

            # generated_logs = package_info_run_object.get_generated_logs()
            # self.convert_to_json(generated_logs)

            # self._process_generated_logs(generated_logs)

    def convert_to_json(self, generated_logs):

        for each_generated_log in generated_logs:
            log = PackageInfoLog.PkgLogObject(each_generated_log)
            data = log.get_data()
            name = pathlib.Path(each_generated_log).name

            path = self.processed_path.joinpath(name + ".json")

            with open(path, 'w') as outfile:
                json.dump(data, outfile,indent=4)

    def _process_generated_logs(self, generated_logs):

        for each_log in generated_logs:
            log_file = pathlib.Path(each_log)

            if not log_file.exists():
                L.error("No File Found at: %s", log_file)
                continue

            asset_path = get_asset_path_from_log_file(log_file)
            asset_type = get_asset_type_from_log_file(log_file)
            hash_value = self.pkg_hash_obj.get_hash_from_filename(asset_path)

            if log_file.name.endswith("Default.log"):
                name_with_type = log_file.name.replace("Default.log", asset_type + ".log")
            else:
                name_with_type = log_file.name

            target_file = pathlib.Path(self.raw_data_dir).joinpath(
                hash_value, name_with_type)

            if not target_file.parent.exists():
                os.makedirs(target_file.parent)

            # Moving the file to the archive folder:
            archive_file_path = self.archive_folder_path.joinpath(
                hash_value, name_with_type)

            # Moving the file to a folder with the hash value
            if not target_file.exists():
                shutil.move(each_log, target_file)
            else:
                L.error("Unable to move %s to the target location: %s", each_log, target_file)

            # Copy the file to the archive folder
            if not archive_file_path.parent.exists():
                os.mkdir(archive_file_path.parent)

            if not archive_file_path.exists():
                shutil.copy(target_file, archive_file_path)
            else:
                L.error("Unable to copy %s to archive folder, path already exists", target_file)

    def recover_files_from_archive(self):
        """
        Moves each file from the archive to the raw folder so that it can be processed
        :return:
        """

        # Clear the file in the archive to make sure that we have a folder to move the files to
        self._clear_old_data_from_raw()

        project_hash_object = self.get_file_hash_info()
        archive_obj = self.get_archive_info()

        # Clear the raw folder and copy the files from there to have a clean environment
        self._clear_old_data_from_raw()

        for each_hash_value in project_hash_object.hash_value_mapping:

            # Matching the paths in the archive folder with the hash for the project files
            if archive_obj.is_hash_value_in_archive(each_hash_value):

                # Construct the source path and the target path

                source_path = self.archive_folder_path.joinpath(each_hash_value)
                target_path = pathlib.Path(self.raw_data_dir).joinpath(each_hash_value)

                # Copy the folders to the target path
                if target_path.exists():
                    # TODO somehow figure out a way to handle if two files have the exact same hash value
                    L.error("Unable to recover file: %s from archive", target_path)
                else:
                    shutil.copytree(source_path, target_path)

            else:
                L.error("Attempting to copy a folder that has not been cached yet")


def split_list_into_chunks(list_to_split, max_entries_per_list):
    """
    Takes a list and splits it up into smaller lists
    """

    chunks = []
    for i in range(0, len(list_to_split), max_entries_per_list):
        chunk = list_to_split[i:i + max_entries_per_list]
        chunks.append(chunk)

    return chunks


# TODO move this function to the LogParser package
def get_asset_path_from_log_file(log_file_path):

    path = "Unknown"
    if not log_file_path.exists():
        L.warning("Unable to find logfile at path: %s", log_file_path)
        return path

    L.debug("Checking filename from log file: %s ", log_file_path)
    with io.open(log_file_path, encoding='utf-8', errors="ignore") as infile:

        for each in infile:
            if "Filename: " in each:
                path = each.split("Filename: ")[1].replace("\n", "")
                path = os.path.abspath(path)
                L.debug("Found filename in log file: %s", path)
                break

    if path == "Unknown":
        L.error("Unable to find path from log file path")

    return path


# TODO move this function to the LogParser package
def get_asset_type_from_log_file(log_file_path):

    log_file_path.exists()
    asset_type = "Unknown"

    if not log_file_path.exists():
        L.warning("Unable to find logfile at path: %s", log_file_path)
        return asset_type

    with io.open(log_file_path, encoding='utf-8', errors="ignore") as infile:

        for i, each in enumerate(infile):
            if "Number of assets with Asset Registry data: " in each:
                read_line = infile.readline(i + 1)
                import re
                try:
                    asset_type = re.search(r'0\) (.*?)\'', read_line).group(1)
                except AttributeError:
                    asset_type = "Unknown"
                break

    if asset_type == "Unknown":
        L.error("Unable to find type")
        print(log_file_path)

    return asset_type


class PackageInfoCommandlet(commandlets.BaseUE4Commandlet):
    """ Runs the package info commandlet """
    def __init__(self, run_config, unreal_asset_file_paths):
        # Initializes the object
        super().__init__(run_config, "_PkgInfoCommandlet", files=unreal_asset_file_paths)

        self.temp_extract_dir = pathlib.Path(self.environment_config["sentinel_artifacts_path"]).joinpath("temp")

    def run(self):
        """
        Prepares and runs the Package info commandlet
        :return: path to the log file
        """

        commandlet_command = self.get_command()

        name = "_raw_package_info.log"
        path = pathlib.Path(self.temp_extract_dir, "0" + name)

        if not os.path.exists(self.temp_extract_dir):
            os.makedirs(self.temp_extract_dir)

        if path.exists():
            number_of_files = len(os.listdir(self.temp_extract_dir))
            path = pathlib.Path(self.temp_extract_dir, str(number_of_files) + name)

        L.info("Writing to: %s", path)

        with open(path, "w", encoding='utf-8', errors="ignore") as temp_out:
            subprocess.run(commandlet_command, stdout=temp_out, stderr=subprocess.STDOUT)

        # RawLogSplitter().split_temp_log_into_raw_files(temp_dump_file)


class RawLogSplitter:

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
        path = pathlib.Path(self.temp_extract_path).joinpath(asset_file_name)

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