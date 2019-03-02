from Editor import buildcommands as buildcommands
from SentinelConfig.configelper import reset_ue_repo, get_path_config_for_test


def clean_compile_project():

    reset_ue_repo()
    editor_builder = buildcommands.UnrealEditorBuilder(get_path_config_for_test())
    editor_builder.run()