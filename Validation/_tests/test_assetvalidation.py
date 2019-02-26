import unittest
import helper as helper

from Validation import assetvalidation


class TestAssetValidation(unittest.TestCase):

    def setUp(self):
        self.run_config = helper.get_path_config_for_test()


    def test_dostuff(self):
        assetvalidation.Validate(self.run_config).run()