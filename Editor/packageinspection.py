import hashlib
import io
import json
import logging
import os
import pathlib
import shutil

import CONSTANTS
from Editor import commandlets, editorutilities
from Editor.LogProcesser import packageinfolog

L = logging.getLogger(__name__)


class PackageHashInfo:
    """
    Takes in a list of files and generates a unique has value from them
    """

    def __init__(self, list_of_files, archive_folder_path):

        self.archive_folder_root = archive_folder_path
        self.list_of_files = list_of_files

        self.hash_value_mapping = {}
        self.hash_values_in_project = []
        self._generate_hash_for_files()

    @staticmethod
    def _get_file_hash(file_path):
        """
        Reads a file and generates a hash value for it
        :param file_path:
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
                L.info("Searching %s out of %s", str(
                    i), str(len(self.list_of_files)))

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
        Returns a file list from the list a list of hashes
        :param list_of_hashes:
        :return:
        """

        missing_files = []
        # Go through each file and checks if its missing from the archive
        # Add to list if its missing
        for each_hash in self.project_hash_file_mappings:
            if not self.is_hash_value_in_archive(each_hash):
                missing_file = self.project_hash_file_mappings[each_hash]
                L.debug("Missing from archive %s", missing_file )
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


class RawAssetUtilities:
    """
    Acts on a folder containing text files extracted from unreal engine and returns
    """

    def __init__(self, raw_folder_path):

        self.raw_folder_path: pathlib.Path = raw_folder_path

    def get_asset_names_by_type(self):
        """
        iterates through the raw folder folders,  finds the default data end figures out the types of the files
        :return:
        """

        asset_dict = {}
        for each_file in self.raw_folder_path.glob('**/*Default.log'):
            each_file = pathlib.Path(each_file)

            asset_type = get_asset_type_from_log_file(each_file)
            asset_path = get_asset_path_from_log_file(each_file)

            if asset_type in asset_dict:

                asset_dict[asset_type].append(asset_path)
            else:
                asset_dict[asset_type] = [asset_path]

        return asset_dict


class BasePackageInspection:

    def __init__(self, run_config):

        self.run_config = run_config

        self.sentinel_structure = run_config[CONSTANTS.SENTINEL_PROJECT_STRUCTURE]
        self._construct_paths()

        self.editor_util = editorutilities.UEUtilities(run_config)

        self._clear_old_data_from_raw()

        self.files_in_project = []
        self.pkg_hash_obj = None
        self.archive_obj = None

    def _construct_paths(self):
        """Makes the paths for outputs inside of the root artifact folder"""
        project_root = pathlib.Path(self.run_config[CONSTANTS.PROJECT_FILE_PATH]).parent
        artifact_root = pathlib.Path(project_root).joinpath(self.sentinel_structure[CONSTANTS.SENTINEL_PROJECT_NAME])

        self.archive_folder_path = artifact_root.joinpath(self.sentinel_structure[CONSTANTS.SENTINEL_ARCHIVES_PATH]).resolve()
        self.raw_data_dir = artifact_root.joinpath(self.sentinel_structure[CONSTANTS.SENTINEL_RAW_LOGS_PATH]).resolve()
        self.processed_path = artifact_root.joinpath(self.sentinel_structure[CONSTANTS.SENTINEL_PROCESSED_PATH]).resolve()

        if not self.archive_folder_path.exists():
            os.makedirs(self.archive_folder_path)
        if not self.raw_data_dir.exists():
            os.makedirs(self.raw_data_dir)
        if not self.processed_path.exists():
            os.makedirs(self.processed_path)

    def get_files_in_project(self):
        """
        :return: all files in the project
        """
        if self.files_in_project:
            return self.files_in_project

        self.files_in_project = self.editor_util.get_all_content_files()

        return self.files_in_project

    def get_file_hash_info(self):
        if self.pkg_hash_obj:
            return self.pkg_hash_obj

        files = self.get_files_in_project()
        self.pkg_hash_obj = PackageHashInfo(files, self.raw_data_dir)

        return self.pkg_hash_obj

    def get_archive_info(self):
        # Check if we have an archive object cached
        if self.archive_obj:
            return self.archive_obj

        hash_obj = self.get_file_hash_info()
        self.archive_obj = ExtractedDataArchive(self.archive_folder_path, hash_obj.hash_value_mapping)

        return self.archive_obj

    def extract_basic_package_information(self, clean=False):
        """
        Does a simple engine extract for asset to be able to determine asset type and other basic info
        """

        # Delete any existing data
        if clean:
            self._clear_data_from_archive()
            self._clear_old_data_from_raw()

        # Object that gives information about the archive
        archive_object = self.get_archive_info()

        # Convert the missing hash values to file paths
        missing_file_list = archive_object.get_missing_files()
        L.info("%s files missing... Starting package inspection", len(missing_file_list))
        L.debug("Missing files:  %s", "\n".join(missing_file_list))

        # Take all the files that were added to files_to process and split them up into smaller lists
        chunks_of_files_to_process = self.split_all_files_into_smaller_lists(missing_file_list, 100)

        #  This is where we go through all the to be able to get information about paths and types
        self._extract_from_files(chunks_of_files_to_process, "Default")
        self._extract_detailed_package_info()

        self.recover_files_from_archive()

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

    def _extract_detailed_package_info(self):

        raw_utilities = RawAssetUtilities(self.raw_data_dir)
        type_dict = raw_utilities.get_asset_names_by_type()

        for each in type_dict:
            package_paths = type_dict[each]
            chunks_of_files_to_process = self.split_all_files_into_smaller_lists(
                package_paths, 50)

            print("*"*50)
            print(each)
            print("*"*50)

            self._extract_from_files(chunks_of_files_to_process, each)

    def _extract_from_files(self, chunks_of_files_to_process, asset_types="Default"):

        # TODO deals the case where the user deletes files
        for i, each_chunk in enumerate(chunks_of_files_to_process):

            package_info_run_object = commandlets.PackageInfoCommandlet(
                self.run_config,
                each_chunk,
                asset_types
            )

            if not package_info_run_object.has_custom_type_config():
                print("Skipping detailed extract of type: ", asset_types)
                break

            L.info("Starting chunk %s out of %s ", i + 1,
                   str(len(chunks_of_files_to_process)))
            L.info("Files in chunk:\n %s \n", "\n".join(each_chunk))

            # Runs the extract
            package_info_run_object.run()

            generated_logs = package_info_run_object.get_generated_logs()

            self._process_generated_logs(generated_logs)

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

    @staticmethod
    def split_all_files_into_smaller_lists(all_files, count_per_list):
        """
        Takes a list and splits it up into smaller lists
        :param all_files:
        :param count_per_list:
        :return:
        """

        chunks = []
        for i in range(0, len(all_files), count_per_list):
            chunk = all_files[i:i + count_per_list]
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


class ProcessPackageInfo:

    def __init__(self, run_config):

        self.run_config = run_config
        self.sentinel_structure = run_config[CONSTANTS.SENTINEL_PROJECT_STRUCTURE]
        self._construct_paths()

        self.pkg_extractor = BasePackageInspection(run_config)

    def _construct_paths(self):
        """Makes the paths for outputs inside of the root artifact folder"""
        project_root = pathlib.Path(self.run_config[CONSTANTS.PROJECT_FILE_PATH]).parent
        artifact_root = pathlib.Path(project_root).joinpath(self.sentinel_structure[CONSTANTS.SENTINEL_PROJECT_NAME])

        self.archive_folder_path = artifact_root.joinpath(self.sentinel_structure[CONSTANTS.SENTINEL_ARCHIVES_PATH]).resolve()
        self.raw_data_dir = artifact_root.joinpath(self.sentinel_structure[CONSTANTS.SENTINEL_RAW_LOGS_PATH]).resolve()
        self.processed_path = artifact_root.joinpath(self.sentinel_structure[CONSTANTS.SENTINEL_PROCESSED_PATH]).resolve()

        if not self.archive_folder_path.exists():
            os.makedirs(self.archive_folder_path)
        if not self.raw_data_dir.exists():
            os.makedirs(self.raw_data_dir)
        if not self.processed_path.exists():
            os.makedirs(self.processed_path)

    def convert_raw_data_to_json(self):
        """
        Goes through all the raw extracted files and extracts any data of interest out of it.  The data of interest is then
        Saved as a json file

        # Find the sentinel output folder
        # Find the test folder
        # Iterate through all the raw package data files
        # Convert each raw file to json file
        # Move files to the parsed folder

        """

        self.pkg_extractor.extract_basic_package_information()

        # Goes through each raw file and saves it out as a json file
        for each_raw_file_path in self.raw_data_dir.glob("**/*.log"):
            # Create the pkg object
            each_pkg_obj = packageinfolog.PkgLogObject(each_raw_file_path)
            # Gets the name of the asset
            asset_name = each_pkg_obj.get_asset_name()

            # Save single json file
            path = os.path.join(self.processed_path, asset_name + ".json")

            f = open(path, 'w')
            # Saves the package object data to disk
            json.dump(each_pkg_obj.get_data(), f, indent=4)
            f.close()

            L.debug("Wrote: " + str(path))