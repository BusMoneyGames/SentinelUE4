import unittest
import Editor.buildcommands as buildcommands
import Editor._tests.helper as helper


class TestClientBuilder(unittest.TestCase):

    def setUp(self):
        path_config = helper.get_path_config_for_test()

        self.client_builder = buildcommands.UnrealClientBuilder(path_config)

    def test_build_client(self):
        self.client_builder.run()

    def test_get_command(self):
        cmd = self.client_builder.get_build_command()
        print(cmd)

    def test_build_server(self):
        path_config = helper.get_path_config_for_test()

        cmd = buildcommands.UnrealClientBuilder(path_config, build_config_name="server")
        cmd.run()


class TestEditorBuilder(unittest.TestCase):

    def setUp(self):
        path_config = helper.get_path_config_for_test()
        self.editor_builder = buildcommands.UnrealEditorBuilder(path_config)

    def test_build_client(self):
        self.editor_builder.run()

    def test_get_command(self):
        self.editor_builder.get_build_command()


