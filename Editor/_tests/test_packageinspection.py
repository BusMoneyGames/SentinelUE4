import unittest
import logging
import Editor.packageinspection as packageinspection
import Editor._tests.helper as helper

L = logging.getLogger()


class TestInspectPackages(unittest.TestCase):

    def setUp(self):
        L.setLevel(logging.DEBUG)
        run_config = helper.get_path_config_for_test()
        self.package_inspection = packageinspection.BasePackageInspection(run_config)

    def test_extract_basic_package_information(self):
        self.package_inspection.extract_basic_package_information(clean=True)

    def test_get_files_in_project(self):
        self.package_inspection.get_files_in_project()


class TestProcessPackageInfo(unittest.TestCase):

    def setUp(self):
        L.setLevel(logging.DEBUG)
        run_config = helper.get_path_config_for_test()

        self.package_processor = packageinspection.ProcessPackageInfo(run_config)

    def test_convert_raw_data_to_json(self):

        self.package_processor.convert_raw_data_to_json()
