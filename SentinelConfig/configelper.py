import git
import pathlib
import CONSTANTS
import json
import logging

L = logging.getLogger()


def verify_environment(run_config):

    env_config = run_config[CONSTANTS.ENVIRONMENT_CATEGORY]
    print('\n')
    print("%-75s %-25s %4s" % ("Path", "Value", "Exists"))

    for each_env_config in env_config.keys():
        path = pathlib.Path(env_config[each_env_config])
        exists = path.exists()

        print("%-75s %-25s %4s" % (path, each_env_config, str(exists)))

    print('\n')


def reset_ue_repo():
    """
    cleans the git repo so that it is clean to run
    :return:
    """

    run_config = get_path_config_for_test()
    environment = run_config[CONSTANTS.ENVIRONMENT_CATEGORY]
    project_root = pathlib.Path(environment[CONSTANTS.UNREAL_PROJECT_ROOT])

    repo = git.Repo(str(project_root.parent))
    clean_result = repo.git.execute(["git", "clean", "-dfx"])
    L.debug(clean_result)

    reset_result = repo.git.execute(["git", "reset", "--hard"])
    L.debug(reset_result)


def read_config(config_dir):
    """
    Reads the config file and
    :param config_dir:
    :return:
    """

    L.debug("Reading Config from: %s", config_dir)
    config_dir = pathlib.Path(config_dir).resolve()

    if not config_dir.exists():
        print("Unable to find a run config directory at: %", str(config_dir))
    else:
        pass
        # print("Reading Config from directory: ", str(config_dir))

    run_config = {}

    asset_types = []
    for each_file in config_dir.glob("**/*.json"):

        f = open(str(each_file))
        json_data = json.load(f)
        f.close()

        if "type_" in each_file.name:
            asset_types.append(json_data)
        else:
            run_config.update(json_data)

    run_config.update({"AssetTypes": asset_types})

    env_category = run_config[CONSTANTS.ENVIRONMENT_CATEGORY]
    relative_project_path = pathlib.Path(env_category[CONSTANTS.UNREAL_PROJECT_ROOT])
    project_root = config_dir.joinpath(relative_project_path).resolve()

    L.info("Project Root: " + str(project_root))

    # Resolves all relative paths in the project structure to absolute paths
    for each_value in env_category.keys():
        if not each_value == CONSTANTS.UNREAL_PROJECT_ROOT:
            each_relative_path = env_category[each_value]
            abs_path = project_root.joinpath(each_relative_path).resolve()
            L.debug(each_value + " :" + str(abs_path) + " Exists:  " + str(abs_path.exists()))
            env_category[each_value] = abs_path

    env_category[CONSTANTS.UNREAL_PROJECT_ROOT] = str(project_root)
    run_config[CONSTANTS.ENVIRONMENT_CATEGORY] = env_category

    return run_config


def get_path_config_for_test():

    # Test config file
    current_dir = pathlib.Path(pathlib.Path(__file__))
    path = current_dir.joinpath("../defaultConfig").resolve()

    config = read_config(path)

    return config
