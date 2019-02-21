import argparse
import json
import pathlib
import CONSTANTS
import logging

L = logging.getLogger()
L.setLevel(logging.INFO)

from Editor import buildcommands, commandlets, packageinspection
COMMANDS = ["build", "validate", "run"]


def read_config(config_dir):
    config_dir = pathlib.Path(config_dir).resolve()

    if not config_dir.exists():
        print("Unable to find a run config directory at: %", str(config_dir))
    else:
        pass
        # print("Reading Config from directory: ", str(config_dir))

    run_config = {}

    for each_file in config_dir.glob("**/*.json"):

        f = open(str(each_file))
        json_data = json.load(f)
        f.close()

        run_config.update(json_data)

    relative_project_path = pathlib.Path(run_config[CONSTANTS.UNREAL_PROJECT_ROOT])
    project_root = config_dir.joinpath(relative_project_path).resolve()
    run_config[CONSTANTS.UNREAL_PROJECT_ROOT] = str(project_root)

    return run_config


def get_default_build_presets():
    default_run_config = read_config("")
    build_presets = dict(default_run_config[CONSTANTS.UNREAL_BUILD_SETTINGS_STRUCTURE])

    return "\n".join(build_presets.keys())


def get_default_automation_tasks():
    default_run_config = read_config("")
    commandlet_settings = dict(default_run_config[CONSTANTS.COMMANDLET_SETTINGS])
    automation_tasks = []

    for each_automation_tasks in commandlet_settings.keys():
        if not each_automation_tasks.startswith("_"):
            automation_tasks.append(each_automation_tasks)

    return "\n".join(automation_tasks)


def main():
    L.info("Do stuff")
    default_build_presets = get_default_build_presets()
    default_validation_tasks = get_default_automation_tasks()

    parser = argparse.ArgumentParser(description='Runs sentinel tasks for Unreal Engine.',
                                     add_help=True,
                                     formatter_class=argparse.RawTextHelpFormatter)

    build_tasks = parser.add_argument_group('Build Tools')
    build_tasks.add_argument("-build_preset", default="default",
                             help="\nall\n" + default_build_presets)

    validate_tasks = parser.add_argument_group('Project Validation')

    validate_tasks.add_argument("-automation_task", default="",
                                help=default_validation_tasks)

    validate_tasks.add_argument("-inspect", "--package_inspection", action='store_true',
                                help="True/False")

    parser.add_argument("-config_overwrite",
                        default="",
                        help="Overwrite the config folder path")

    parser.add_argument("-task",
                        required=True,
                        help="runs a sentinel task")

    args = parser.parse_args()

    # Construct the config file
    run_config = read_config(args.config_overwrite)

    if args.task.lower() in COMMANDS:
        if args.task.lower() == "build":
            builder = buildcommands.UnrealClientBuilder(run_config=run_config,
                                                        build_config_name=args.build_preset
                                                        )

            builder.run()

        if args.task.lower() == "validate" and args.automation_task:
            commandlet = commandlets.BaseUE4Commandlet(run_config, args.automation_task)
            commandlet.run()

        if args.task.lower() == "validate" and args.package_inspection:
            inspection_obj = packageinspection.ProcessPackageInfo(run_config)
            inspection_obj.run()

    else:
        print(args.task + " " + "is not a valid task...")
        print("Available Commands: \n\n" + "\n".join(COMMANDS) + "\n")


if __name__ == "__main__":
    main()
