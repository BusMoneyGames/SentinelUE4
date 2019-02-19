import json
import logging

L = logging.getLogger()


class GPUStatsLine:
    """
    Takes in a line from the gpu log and converts it to a dictonary
    """
    def __init__(self, stats_line):

        self.clean_line = stats_line
        self.level = -1

        # The processed lines is the line that gets chopped down
        self.processed_line = stats_line.lstrip()

        # This value is used if the millisecond percentage is equal or higher than 10 since that messes with
        # Figuring out where where in the hierarcy the value is
        self.long_percentage_value = False

        self.output_dict = {
            "Percentages": -0.0,
            "Milliseconds": -1,
            "Name": "Unknown",
            "Vertices": -1,
            "Triangles": -1,
            "Draws": -1
        }

        # Extracts information from the line and registers it in the line stats dict
        self.extract_info_from_line()

    def __repr__(self):

        # Converts the dictionary to a string for printing
        return json.dumps(self.output_dict)

    def __str__(self):

        # Converts the dictionary to a string for printing
        return json.dumps(self.output_dict)

    def set_level_in_hierarchy(self, level):
        self.level = level

    def _register_value_to_output_dict(self, name, value):

        if name in self.output_dict:
            self.output_dict[name] = value
        else:
            L.warning("Trying to register a value that is not configured in the output name: %s value: %s", name, value)

    def get_data(self):
        """
        :return: dictionary with the data from the gpu line
        """

        return self.output_dict

    def extract_info_from_line(self):
        """
        Finds the step name from the line
        :return:
        """

        # Breaks the string down into segments.  The order of these calls is important since it is removing things
        # From the line segments variables
        self._get_percentage()
        self._get_milliseconds()
        self._get_name()

        verts = self._get_prim_type_value("verts")
        prims = self._get_prim_type_value("prims")
        draws = self._get_prim_type_value("draws")

        self._register_value_to_output_dict("Vertices", int(verts))
        self._register_value_to_output_dict("Triangles", int(prims))
        self._register_value_to_output_dict("Draws", int(draws))

    def get_indent_amount(self):

        line = self.clean_line

        indent = len(line) - len(line.lstrip())

        # Dealing with the case where the indent value is equal or higher than 10
        if self.long_percentage_value and indent > 0:

            indent = indent + 1

        return indent

    def _get_prim_type_value(self, name):
        # This might be a step that does not include any data at the end of the string

        name = " " + name

        if name in self.clean_line:
            split = self.clean_line.split(name)[0]
            space_split = split.split(" ")
            value = space_split[len(space_split)-1]
            return int(value)

        else:
            return -1

    def _get_name(self):

        # find the millisecond value
        name_extract_line = self.clean_line.split("ms")[1]
        name = []
        for each_char in name_extract_line:
            if each_char.isnumeric():
                break

            name.append(each_char)
        name = "".join(name).lstrip()

        self._register_value_to_output_dict("Name", name.rstrip())

        return name

    def _get_milliseconds(self):
        # Find the part that is after the percentage
        line = self.clean_line.split("%")[1]

        # find the millisecond value
        milliseconds = line.split("ms")[0]

        # Removing the whitespace
        milliseconds = milliseconds.strip()

        # Add to output
        self._register_value_to_output_dict("Milliseconds", float(milliseconds))

        return milliseconds

    def _get_percentage(self):
        # First entry should always be the percentage
        percentage = self.clean_line.split("%")[0].lstrip()

        self._register_value_to_output_dict("Percentages", float(percentage))

        if len(percentage) == 4:
            self.long_percentage_value = True

        return percentage


class TextureStatLine:

    """
    Handle extracting the texture data from the log line
    """

    def __init__(self, raw_log_line):

        self.log_line = raw_log_line

        self.output_dict = {}
        self.get_line_dict()

    def __repr__(self):

        # Converts the dictionary to a string for printing
        return json.dumps(self.output_dict)

    def __str__(self):

        # Converts the dictionary to a string for printing
        return json.dumps(self.output_dict)

    def get_output_data(self):
        return self.output_dict

    def get_line_dict(self):

        self.output_dict["Texture Group"] = self.get_texture_group()
        self.output_dict["Compression"] = self.get_compression_type()
        self.output_dict["Current Size"] = self.get_current_size_ingame()
        self.output_dict["Current Resolution"] = self.get_current_resolution_ingame()
        self.output_dict["Max Resolution"] = self.get_on_disk_resolution()
        self.output_dict["Max Size"] = self.get_size_on_disk()
        self.output_dict["Asset Name"] = self.get_asset_name()
        self.output_dict["Number Of Uses"] = self.get_number_of_uses()
        self.output_dict["Streaming"] = self.get_is_streaming()

    def get_on_disk_resolution(self):

        data = self.log_line.split(" ")[0]

        return data

    def get_size_on_disk(self):

        split = self.log_line.split(",")[0]
        size = split.split(" ")[1].replace("(", "")
        return int(size)

    def get_current_size_ingame(self):
        split = self.log_line.split(" ")
        size = split[5].replace("(", "")

        return int(size)

    def get_current_resolution_ingame(self):
        split = self.log_line.split(" ")
        res = split[4]

        return res

    def get_compression_type(self):
        data = self._get_stat_at_index(7)
        return data

    def get_texture_group(self):
        data = self._get_stat_at_index(8)
        return data

    def get_asset_name(self):
        data = self._get_stat_at_index(9)
        return data

    def get_is_streaming(self):
        data = self._get_stat_at_index(10)
        return data

    def get_number_of_uses(self):
        data = self._get_stat_at_index(11)
        return int(data)

    def _get_stat_at_index(self, index):
        stat = self.log_line.split(" ")[index].replace(",","")
        return stat

    def _clean_timestamp(self, log_string):
        try:
            clean = log_string.split("]")[2]
        except:
            clean = ""

        return clean


class TextureOverviewStatLine:

    """
    A line form the texture overview stat
    """

    def __init__(self, line):
        pass