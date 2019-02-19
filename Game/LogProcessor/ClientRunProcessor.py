# coding=utf-8
from SentinelUE4.Game.ClientOutput import CLIENT_LOG_CONSTANTS
from SentinelUE4.Game.ClientOutput.ClientLogParser import ClientTestEntryParser
import pathlib
import logging
L = logging.getLogger()


class ClientRunProcessor:

    """
    Handles processing the whole log from the client run.

    Extracts out the sections of the logs for each test
    Match screenshots to the _featuretests names
    # Extracts information from the log about the run ( graphics adapter for example )
    """

    def __init__(self, test_result_path):

        self.test_result_path = pathlib.Path(test_result_path)

        log_file = self.get_log_from_test_dir(test_result_path)

        f = open(log_file, "r")
        self.raw_log_lines = f.readlines()
        f.close()

        # Information that will be collected during hte run
        self.run_time = -1
        self.graphics_adapter = "Unknown"
        self.build_configuration = "Unknown"
        self.engine_version = "Unknown"

        self.filtered_graphics_log = self._filter_log_file()

        # TODO this whole thing needs to be refactored to better deal with how the screenshots are matched
        self.image_test_dict = {}

    @staticmethod
    def get_log_from_test_dir(test_directory):
        """
        Return the log file from the test directory
        :param test_directory:
        :return:
        """
        test_directory = test_directory.joinpath("Logs")

        logs = []
        for e in test_directory.iterdir():
            logs.append(e)

        if not len(logs) == 1:
            L.warning("More than 1 log file found in the output folder")

        log_file = logs[0]
        L.debug("Found logfile at: %s", log_file)

        return log_file

    def get_graphic_test_objects(self):
        """
        Parse the log file and extracts the gpu stats for each test step
        """

        list_of_test_results = []

        for test_name in self.filtered_graphics_log.keys():

            test_data = self.filtered_graphics_log[test_name]
            result_objects = ClientTestEntryParser(test_name, test_data)

            images = self.get_images_for_test_result(test_name)
            result_objects.set_test_screenshot_paths(images)

            list_of_test_results.append(result_objects)

        return list_of_test_results

    def _check_single_line_for_information(self, line):
        """
        Checks each line if it contains information that we want to store
        :param line:
        :return:
        """

        if "Log file open, " in line:
            # Get the test start time stamp

            time = line.split(", ")[1]
            L.debug("Found test start time: " + time)
            self.run_time = time

        elif "LogInit: Engine Version: " in line:
            # Get Engine version for this run
            engine_version = line.split(": ")[2]
            L.debug("Found Engine Version:" + engine_version)
            self.engine_version = engine_version

        elif "LogInit: Build Configuration:" in line:
            # Get Build config
            build_config = line.split(": ")[2]
            L.debug("Found Build Config: " + build_config)
            self.build_configuration = build_config

        elif "LogD3D11RHI:     Adapter Name: " in line:
            # GPU type
            adapter_name = line.split(": ")[2]
            L.debug("Found GPU adapter: " + adapter_name)
            self.graphics_adapter = adapter_name

    def _filter_log_file(self):
        """
        Goes through the log file and returns a dict with the info within the start and end
        test tags
        :return:
        """

        should_save_log = False

        logs_filtered_by_test = {}
        for each_line in self.raw_log_lines:

            # Stripping out the end of line symbol if its there
            each_line = each_line.replace("\n", "")

            self._check_single_line_for_information(each_line)

            if CLIENT_LOG_CONSTANTS.TEST_START_STRING in each_line:
                test_name_value = self.get_test_name_from_log(each_line)

                logs_filtered_by_test[test_name_value] = []

                should_save_log = True

            elif CLIENT_LOG_CONSTANTS.TEST_END_STRING in each_line:
                should_save_log = False

            if should_save_log:
                logs_filtered_by_test[test_name_value].append(each_line)

        L.debug("Found %s raw test results", len(logs_filtered_by_test))

        return logs_filtered_by_test

    def get_test_name_from_log(self, line):
        """
        return the name of the test based on the gpu start string

        :param line: the line that includes the gpu start string
        :return: test name
        """

        split = line.split(CLIENT_LOG_CONSTANTS.TEST_START_STRING)[1].replace("\n", "")
        return split.lstrip().lower()

    def _get_images(self):

        bugit_dir = self.test_result_path.joinpath("BugIt")

        paths = []
        for p in bugit_dir.glob("**/*.png"):
            L.debug("Found image: %s", p.as_posix())
            paths.append(p)

        return paths

    def get_images_for_test_result(self, test_name):

        images = self._get_images()
        matches = []
        for each_image in images:
            L.debug("Matching %s with %s", test_name, each_image.name)
            if test_name.lower() in each_image.stem.lower():
                L.info("Found Match!")
                matches.append(each_image)

        return matches

