import unittest
import Editor.commandlets as commandlets
import pathlib
import CONSTANTS
import Editor._tests.helper as helper

import logging

FORMAT = '%(message)s'
logging.basicConfig(format=FORMAT)

L = logging.getLogger()
L.setLevel(logging.DEBUG)


class TestDefaultCommandlets(unittest.TestCase):

    def setUp(self):
        helper.clean_compile_project()
        L.debug("Iterates through all the default commandlets and runs them")
        self.run_config = helper.get_path_config_for_test()
        self.commandlets = dict(self.run_config[CONSTANTS.COMMANDLET_SETTINGS])

    def test_runAll(self):

        L.debug("Found %s commandlets", len(self.commandlets.keys()))
        L.debug("\n".join(self.commandlets.keys()))

        for each_commandlet in self.commandlets.keys():
            L.info(self.commandlets[each_commandlet])

    def test_compileblueprints(self):

        cmd = commandlets.BaseUE4Commandlet(run_config=self.run_config, commandlet_name="Compile-Blueprints")
        cmd.run()

    def test_resaveAllPackages(self):

        cmd = commandlets.BaseUE4Commandlet(run_config=self.run_config, commandlet_name="Resave-All-Packages")
        cmd.run()

    def test_resaveBlueprints(self):

        cmd = commandlets.BaseUE4Commandlet(run_config=self.run_config, commandlet_name="Resave-Blueprints")
        cmd.run()

    def test_resaveLevels(self):

        cmd = commandlets.BaseUE4Commandlet(run_config=self.run_config, commandlet_name="Resave-Levels")
        cmd.run()

    def tearDown(self):
        helper.clean_compile_project()




class TestPackageInfoCommandlet(unittest.TestCase):
    def setUp(self):
        L.setLevel(logging.DEBUG)

        self.path_config = helper.get_path_config_for_test()

        files = self._get_test_files()
        self.package_info_commandlet = commandlets.PackageInfoCommandlet(self.path_config, files)

    def _get_test_files(self):
        content_value = self.path_config[CONSTANTS.UNREAL_PROJECT_STRUCTURE][CONSTANTS.UNREAL_CONTENT_ROOT_PATH]
        project_root = pathlib.Path(self.path_config[CONSTANTS.UNREAL_PROJECT_ROOT]).resolve()

        content_path = project_root.joinpath(content_value)

        files = []
        for i, each_file in enumerate(content_path.glob("**/*.uasset")):
            files.append(each_file)

            if i > 5:
                break

        return files

    def test_get_command(self):
        command = self.package_info_commandlet.get_command()
        print(command)

    def test_run(self):
        self.package_info_commandlet.run()


