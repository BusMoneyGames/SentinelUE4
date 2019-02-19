from SentinelUE4.Game.ClientOutput import CLIENT_LOG_CONSTANTS

import logging

from SentinelUE4.Game.ClientOutput.LogLines import GPUStatsLine, TextureStatLine, TextureOverviewStatLine

L = logging.getLogger()


class ClientTestEntryParser:
    """
    Takes in a portion of the log that has to do with a specific test and extracts information out of it

    A test point takes in a list of lines between the start and end of the test flags from the client log and has
    methods to extract data from it


    # Texture Information
    # GPU information
    # Test name
    """

    def __init__(self, test_name, test_data):

        self.name = test_name
        self.post_fix = self._get_test_postfix()
        self.base_name = self._get_test_base_name()

        self.test_data = test_data
        L.debug("Parsing Segments for: %s with %s number of log lines", self.name, len(test_data))

        self.raw_gpu_data = self._parse_raw_gpu_data()
        self.raw_texture_data = self._parse_raw_texture_data()

        self.screenshot_paths = []
        self.screenshot_types = []
        self.relative_image_paths = []

    def _get_test_postfix(self) -> str:
        """
        Gets the postfix which is always behind the last underscore
        :return: str
        """

        split = self.name.split("_")
        post_fix = split[len(split)-1]

        L.debug(post_fix)

        return post_fix

    def _get_test_base_name(self):
        """
        Get the asset name without the post fix
        :return:
        """
        split = self.name.split("_")
        split.pop()

        base_name = "_".join(split)
        L.debug(base_name)

        return base_name

    def _get_test_name(self):
        return self.name

    def _get_gpu_data(self):
        L.debug("Constructing a parse GPU segment object using %s lines", len(self.raw_gpu_data))
        return ParseGPUSegment(self.raw_gpu_data)

    def get_gpu_frame_overview(self):
        gpu_obj = self._get_gpu_data()

        stats = gpu_obj.get_frame_info()

        return stats

    def _parse_raw_gpu_data(self):
        """
        Fetches the raw gpu data and filteres out everything that is not valid
        :return:
        """

        raw_data = self._parse_data_from_key(CLIENT_LOG_CONSTANTS.GPU_START_STRING, CLIENT_LOG_CONSTANTS.GPU_STOP_STRING)

        clean_raw_data = []
        for each_line in raw_data:
            if "%" in each_line and "LogRHI: ":
                each_line = each_line.replace("\n", "")
                clean_raw_data.append(each_line)

        return clean_raw_data

    def _parse_raw_texture_data(self):

        data = self._parse_data_from_key(CLIENT_LOG_CONSTANTS.TEXTURE_LIST_START_STRING,
                                         CLIENT_LOG_CONSTANTS.TEXTURE_LIST_STOP_STRING)
        new_data = []

        for each in data:
            new_data.append(each.replace("\n", ""))

        return new_data

    def get_texture_data(self):
        L.debug("Constructing a parse texture segment object using %s lines", len(self.raw_texture_data))
        return ParseTextureSegment(self.raw_texture_data)

    def _parse_data_from_key(self, start_key, end_key):

        save_log = False
        data = []
        for each_line in self.test_data:
            if start_key in each_line:
                save_log = True
                continue
            elif end_key in each_line:
                save_log = False
                continue

            if save_log:
                data.append(each_line)

        return data

    def get_test_screenshot_path(self):
        return self.screenshot_paths

    def set_test_screenshot_paths(self, paths):
        self.screenshot_paths = []
        self.screenshot_types = []

        for each_path in paths:
            self.screenshot_paths.append(each_path.as_posix())
            self.screenshot_types.append(self._get_screenshot_type_from_path())

    def _get_screenshot_type_from_path(self):

        return "Unit"


    def _extract_pattern_from_string(self, line, startletter, stopletter):
        """
        Iterates through the string and returns the string that is between the start letter and the stop letter

        :param line: log line
        :param startletter: the string to start at
        :param stopletter: the string to stop at
        :return: string between the startletter and stop letter
        """

        out_string = ""
        for each_letter in line:
            if each_letter == startletter:
                out_string = out_string + each_letter
            elif each_letter == stopletter:
                out_string = out_string + each_letter
                return out_string
            else:
                out_string = out_string + each_letter


class ParseTextureSegment:
    """
    Parses a raw texture segment
    """

    def __init__(self, raw_texture_segment):
        self.raw_texture_segment = raw_texture_segment
        self.texture_statistics = []
        self.texture_overview = []

        self._construct_stats_list()

    def __repr__(self):
        """
        Construct a string made from all the gpu objects
        :return:
        """

        value = ""
        for e in self.texture_statistics:
            value += "\n" + str(e)

        return value

    def _construct_stats_list(self):
        """ Iterate through the raw lines and create texture stat line objects"""
        for each_line in self.raw_texture_segment:
            try:
                line = self._remove_prefix_from_line(each_line)

                # If the first character is a number we know its a statistics line
                if line[0].isnumeric():
                    self.texture_statistics.append(TextureStatLine(line))

                # If the line starts with total then we know its part of the overview
                elif line.startswith("Total "):
                    self.texture_overview.append(TextureOverviewStatLine(line))
            except:
                L.warning("Unable to process line: %s", line)

    def get_stat_list(self):
        return self.texture_statistics

    @staticmethod
    def _remove_prefix_from_line(line):

        try:
            line.split("]")[2]
        except IndexError as e:
            # TODO this is a hack to deal with it when things are written to the log and don't follow the unreal
            # standard

            return line

        return line.split("]")[2]


class ParseGPUSegment:

    """
    Takes a section of lines that contain the gpu dump information from the log and parses them
    """

    def __init__(self, raw_gpu_segment):
        self.raw_gpu_lines = raw_gpu_segment
        self.clean_gpu_lines = self._strip_prefix_from_list(raw_gpu_segment)

        self.gpu_line_objects = self._get_gpu_line_list()

    def get_gpu_stats_list(self):
        gpu_stats = self._strip_prefix_from_list(self.raw_gpu_lines)

        return gpu_stats

    def _get_gpu_line_list(self):
        gpu_data_list = []

        for each_line in self.clean_gpu_lines:
            # Constructs a gpu line object that returns a gpu line dict
            gpu_line_obj = GPUStatsLine(each_line)
            gpu_data_list.append(gpu_line_obj)

        return gpu_data_list

    def get_frame_info(self):

        for gpu_line_obj in self.gpu_line_objects:
            data = gpu_line_obj.get_data()
            if data["Name"] == "FRAME":
                return data

        L.warning("Unable to find the FRAME value from the gpu log")

        return None

    def get_stats_at_level(self, level, threshold=0.25):
        """
        Get the top level gpu categories that are within the configured ranges

        The levels are still "magic",  level 1 is actualy level 4 and level 2 is actually level 7
        :return:
        """
        # TODO move the threshold value to a config file

        # TODO figure out how to get the levels to be more consistent
        if level == 1:
            level = 4
        elif level == 2:
            level = 7

        gpu_data_list = []
        for gpu_line_obj in self.gpu_line_objects:

            current_line_indent = gpu_line_obj.get_indent_amount()
            # print(str(current_line_indent) + " --" + str(each_line))

            # Top level categories ( values are hardcoded...
            if current_line_indent in [level]:
                gpu_data = gpu_line_obj.get_data()

                if gpu_data["Milliseconds"] > threshold:
                    gpu_data_list.append(gpu_line_obj)

        return gpu_data_list

    @staticmethod
    def _strip_prefix_from_list(raw_lines):
        stats_list = []
        for e in raw_lines:
            try:
                clean_line = e.split("LogRHI: ")[1]
                stats_list.append(clean_line)
            except:
                L.warning("Unable to parse stats line")

        return stats_list


