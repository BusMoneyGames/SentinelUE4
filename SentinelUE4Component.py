import argparse
import pathlib
import CONSTANTS
import logging
import helper
import sys

from Editor import buildcommands, commandlets, packageinspection
COMMANDS = ["build", "validate", "run"]

FORMAT = '%(message)s'
logging.basicConfig(format=FORMAT)

L = logging.getLogger()
L.setLevel(logging.INFO)


def get_default_build_presets():
    current_dir = pathlib.Path(pathlib.Path(__file__).parent)
    default_run_config = helper.read_config(current_dir)
    build_presets = dict(default_run_config[CONSTANTS.UNREAL_BUILD_SETTINGS_STRUCTURE])

    return "\n".join(build_presets.keys())


def get_default_automation_tasks():
    current_dir = pathlib.Path(pathlib.Path(__file__).parent)
    default_run_config = helper.read_config(current_dir)
    commandlet_settings = dict(default_run_config[CONSTANTS.COMMANDLET_SETTINGS])
    automation_tasks = []

    for each_automation_tasks in commandlet_settings.keys():
        if not each_automation_tasks.startswith("_"):
            automation_tasks.append(each_automation_tasks)

    return "\n".join(automation_tasks)


def main():
    parser = argparse.ArgumentParser(description='Runs sentinel tasks for Unreal Engine.',
                                     add_help=True,
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("-build", action='store_true')
    parser.add_argument("-validate", action='store_true')
    parser.add_argument("-run", action='store_true')

    global_settings = parser.add_argument_group('Global Settings')
    global_settings.add_argument("-debug", action='store_true', help="Enables detailed logging")
    global_settings.add_argument("-verify", action='store_true', help="Verifies the paths in the environment")
    global_settings.add_argument("-deploy", action='store_true', help="Uploads the artifacts to the server")
    global_settings.add_argument("-config_overwrite", default="", help="Config root directory if different that default")

    # Build settings
    build_tasks = parser.add_argument_group('Build Settings')
    build_tasks.add_argument('-build_preset', nargs='*', default=[])

    # Validation settings
    validate_settings = parser.add_argument_group('Validation Settings')
    validate_settings.add_argument('-validation_tasks', nargs='*', default=[])
    validate_settings.add_argument('-validation_inspect', action='store_true')

    # Run Settings
    run_settings = parser.add_argument_group('Run Settings')
    run_settings.add_argument('-run_tasks', nargs='*')

    args = parser.parse_args()

    if args.debug:
        L.setLevel(logging.DEBUG)

    # Construct the config file
    run_config = helper.read_config(args.config_overwrite)

    if args.verify:
        helper.verify_environment(run_config)
        import sys
        sys.exit()

    if args.build:
        L.debug("Available Builds: %s", "".join(get_default_build_presets()))

        if len(args.build_preset) == 0:
            L.info("No Build preset specified,  running with default")
            args.build_preset = ["default"]

        L.info("Running: %s builds", len(args.build_preset))
        for each_config in args.build_preset:
            L.info("Starting: %s", each_config)
            builder = buildcommands.UnrealClientBuilder(run_config=run_config,
                                                        build_config_name=each_config
                                                        )
            builder.run()

    if args.validate:

        if args.validation_inspect:
            L.info('Running Full Validation Export')
            packageinspection.BasePackageInspection(run_config).run()

        if args.validation_tasks:
            L.debug("Available Validation Steps: %s", "".join(get_default_automation_tasks()))
            L.info("Running: %s validation steps", len(args.validate_preset))

        for each_validation_config in args.validation_tasks:
            L.info("Starting: %s", each_validation_config)
            commandlet = commandlets.BaseUE4Commandlet(run_config, each_validation_config)
            commandlet.run()

    if args.run:
        pass


if __name__ == "__main__":
    main()
