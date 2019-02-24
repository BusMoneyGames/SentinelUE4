import unittest
import _tests.helper as helper
import CONSTANTS

from Validation import assetvalidation

class TestAssetValidation(unittest.TestCase):

    def setUp(self):
        run_config = helper.get_path_config_for_test()
        self.sentinel_structure = run_config[CONSTANTS.SENTINEL_PROJECT_STRUCTURE]

    def test_dostuff(self):

        assetvalidation.Validate()