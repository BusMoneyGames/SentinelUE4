import argparse
import pathlib
import json
import logging
import CONSTANTS

if __package__ is None or __package__ == '':
    from Editor import buildcommands, commandlets, packageinspection
    from Game import clientrunner
else:
    from . Editor import buildcommands, commandlets, packageinspection
    from . Game import clientrunner

COMMANDS = ["build", "validate", "run"]

L = logging.getLogger()


def _read_config(assembled_config_path):
    """
    Reads the assembled config

    :param assembled_config_path:
    :return:
    """

    path = pathlib.Path(assembled_config_path).joinpath("_sentinelConfig.json").resolve()

    L.info(path)
    L.debug("Assembled Config Exists: " + str(path.exists()))

    f = open(path, "r")
    config = json.load(f)
    f.close()

    return config


def get_default_build_presets(default_run_config):

    build_presets = dict(default_run_config[CONSTANTS.UNREAL_BUILD_SETTINGS_STRUCTURE])

    return "\n".join(build_presets.keys())


def get_default_automation_tasks(default_run_config):

    commandlet_settings = dict(default_run_config[CONSTANTS.COMMANDLET_SETTINGS])
    automation_tasks = []

    for each_automation_tasks in commandlet_settings.keys():
        if not each_automation_tasks.startswith("_"):
            automation_tasks.append(each_automation_tasks)

    return "\n".join(automation_tasks)


def main(raw_args=None):

    parser = argparse.ArgumentParser(description='Runs sentinel tasks for Unreal Engine.',
                                     add_help=True,
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("-build", action='store_true')
    parser.add_argument("-validate", action='store_true')
    parser.add_argument("-run", action='store_true')

    global_settings = parser.add_argument_group('Global Settings')
    global_settings.add_argument("-config", default="", help="Absolute or relative path to"
                                                             " the config directory if other than default")
    global_settings.add_argument("-debug", action='store_true', help="Enables detailed logging")
    global_settings.add_argument("-detailed_help", action='store_true')
    global_settings.add_argument("-deploy", action='store_true', help="Uploads the artifacts to the server")

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

    args = parser.parse_args(raw_args)

    if args.debug:
        print("Running in debug mode!")
        FORMAT = '%(levelname)s - %(funcName)s - %(message)s'
        logging.basicConfig(format=FORMAT)
        L.setLevel(logging.DEBUG)
    else:
        FORMAT = '%(levelname)s - %(message)s'
        logging.basicConfig(format=FORMAT)
        L.setLevel(logging.DEBUG)

    # Construct the config file
    L.info("Reading Config From: %s", args.config)

    run_config = _read_config(args.config)

    if args.detailed_help:
        L.info("Showing detailed help")
        return

    if args.build:
        L.debug("Available Builds: %s", "".join(get_default_build_presets(run_config)))

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
            L.debug("Available Validation Steps: %s", "".join(get_default_automation_tasks(run_config)))
            # L.info("Running: %s validation steps", len(args.validate_preset))

        for each_validation_config in args.validation_tasks:
            L.info("Starting: %s", each_validation_config)
            commandlet = commandlets.BaseUE4Commandlet(run_config, each_validation_config)
            commandlet.run()

    if args.run:
        client_runner = clientrunner.GameClientRunner(run_config)


if __name__ == "__main__":
    main()
