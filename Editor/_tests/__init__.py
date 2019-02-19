import pathlib
import os


def recursively_search_for_file_down_a_directory(file_suffix, file_name=""):
    """
    finds the folder path of the script
    :return: root path
    """

    script_file = pathlib.PurePath(os.path.realpath(__file__))

    # TODO fix this so that it searches for the path down until we hit the root of scripts folder

    # Walks down the folder structure looking for the uproject file to identify the root of the project
    level_to_check = len(script_file.parents) - 1
    file_path = ""

    while level_to_check >= 0:
        path_to_check = pathlib.Path(script_file.parents[level_to_check])

        for each_file in path_to_check.glob("*.*"):

            # Check if the file has the correct suffix
            if each_file.suffix == file_suffix and file_name == "":

                # If the filename is not set then we just return the first one we find
                if not file_name:
                    # Return the folder path
                    file_path = each_file.parents[0]
                    break

            else:
                # If there is a file name along with the extention,  match that
                if each_file.suffix == file_suffix and file_name.lower() in each_file.name.lower():
                    file_path = each_file.parents[0]
                    break

        level_to_check = level_to_check - 1

    return file_path