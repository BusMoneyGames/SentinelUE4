import argparse
import pprint
import json
import pathlib
import CONSTANTS

from Editor import buildcommands
COMMANDS = ["build", "test", "run"]


def read_config(config_dir):
    config_dir = pathlib.Path(config_dir).resolve()

    if not config_dir.exists():
        print("Unable to find a run config directory at: %", str(config_dir))
    else:
        print("Reading Config from directory: ", str(config_dir))

    run_config = {}

    for each_file in config_dir.glob("**/*.json"):

        f = open(str(each_file))
        json_data = json.load(f)
        f.close()

        run_config.update(json_data)

    pprint.pprint(run_config)

    relative_project_path = pathlib.Path(run_config[CONSTANTS.UNREAL_PROJECT_ROOT])
    project_root = config_dir.joinpath(relative_project_path).resolve()
    run_config[CONSTANTS.UNREAL_PROJECT_ROOT] = str(project_root)

    return run_config


def main():
    parser = argparse.ArgumentParser(description='Runs sentinel tasks for Unreal Engine.')

    parser.add_argument("-config",
                        "--build_configure",
                        default="default",
                        help="Build config to use (options: default, linux)")

    parser.add_argument("-run_config_dir",
                        "--run_config_directory",
                        default="",
                        help="Build config to use (options: default, linux)")

    parser.add_argument("-cmd",
                        "--command",
                        required=True,
                        help="runs a sentinel task")

    args = parser.parse_args()

    # Construct the config file
    run_config = read_config(args.run_config_directory)
    # pprint.pprint(run_config)

    if args.command.lower() in COMMANDS:
        if args.command.lower() == "build":
            pass
            builder = buildcommands.UnrealClientBuilder(run_config=run_config,
                                              build_config_name=args.build_configure
                                              )

            builder.run()

    else:
        print(args.command + " " + "is not a valid command...")
        print("Available Commands: \n\n" + "\n".join(COMMANDS) + "\n")


if __name__ == "__main__":
    main()
