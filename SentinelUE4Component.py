import pathlib
import json
import logging
import os
import click
import ue4_constants
import shutil

from Editor import buildcommands, commandlets, packageinspection
from Game import clientrunner, clientutilities
from Game.LogProcessor import ClientRunProcessor

L = logging.getLogger()


def _read_config(path):
    """Reads the assembled config"""

    L.debug("Reading config from: %s - Exists: %s", path, path.exists())

    if path.exists():
        f = open(path, "r")
        config = json.load(f)
        f.close()

        return config
    else:
        L.error("Unable to find generated config at: %s ", path)
        quit(1)


def get_default_build_presets(default_run_config):
    """ Read the build presets from the config """
    return dict(default_run_config[ue4_constants.UNREAL_BUILD_SETTINGS_STRUCTURE])


def get_validate_presets(default_run_config):
    """ Read the commandlets settings from the config """
    return dict(default_run_config[ue4_constants.COMMANDLET_SETTINGS])


@click.group()
@click.option('--path', default="", help="path to the config overwrite folder")
@click.option('--debug', default=False, help="Turns on debug messages")
@click.pass_context
def cli(ctx, path, debug):
    """Sentinel Unreal Component handles running commands interacting with unreal engine"""

    if debug:
        L.setLevel(logging.DEBUG)
        message_format = '%(levelname)s - %(message)s '
    else:
        message_format = '%(levelname)s %(message)s '
        L.setLevel(logging.ERROR)

    logging.basicConfig(format=message_format)
    run_directory = pathlib.Path(os.getcwd())

    if path:
        custom_path = pathlib.Path(path)
        if custom_path.absolute():
            config_file_root_dir = path
        else:
            config_file_root_dir = run_directory.joinpath(path)
    else:
        # Default is one level up from current directory
        config_file_root_dir = run_directory.parent

    config_file_path = config_file_root_dir.joinpath(ue4_constants.GENERATED_CONFIG_FILE_NAME)
    L.debug("Reading config file from: %s Exists: %s", config_file_path, config_file_path.exists())

    ctx.ensure_object(dict)
    ctx.obj['CONFIG_ROOT'] = path
    ctx.obj['GENERATED_CONFIG_PATH'] = config_file_path
    ctx.obj['RUN_CONFIG'] = _read_config(config_file_path)


@cli.group()
def build():
    """Compile and build different targets"""


@build.command()
@click.option('-o', '--output', type=click.Choice(['text', 'json']), default='text', help="Output type.")
@click.pass_context
def show_build_profiles(ctx, output):
    """ Lists the available build profiles as defined in settings"""
    run_config = ctx.obj['RUN_CONFIG']
    presets = get_default_build_presets(run_config)
    
    if output == 'text':
        print("\n".join(presets.keys()))
    elif output == 'json':
        print(json.dumps(presets, indent=4))


@build.command()
@click.pass_context
@click.option('-p', '--preset', default='windows_default_client', help="Build profile to run.")
@click.option('-archive', '--should_archive', type=bool, default=False, help="Should archive.")
def client(ctx, preset, should_archive):
    """ Runs a build for the configured build preset"""

    # TODO making it so that the run config is loaded in as a global argument and made available
    # to all steps

    run_config = ctx.obj['RUN_CONFIG']
    L.debug("Available Builds: %s", "".join(get_default_build_presets(run_config)))

    factory = buildcommands.BuilderFactory(run_config=run_config, build_config_name=preset)
    builder = factory.get_builder("Client")

    builder.prepare()
    a = builder.run()

    # Creates an archive
    if should_archive:
        L.debug("Starting to archive")
        build_root_directory = builder.get_archive_directory()
        L.debug("Build Root: %s", build_root_directory)

        # zip_file_path =
        shutil.make_archive(build_root_directory, 'zip', build_root_directory)
        L.debug("Removing build source since we are making an archive")
        # Removing the original folder to only leave the archive
        shutil.rmtree(build_root_directory)


@build.command()
@click.pass_context
@click.option('-p', '--platform', default='windows', help="platform to run the editor on")
def editor(ctx, platform):

    run_config = ctx.obj['RUN_CONFIG']
    factory = buildcommands.BuilderFactory(run_config=run_config)
    builder = factory.get_builder("Editor")

    builder.prepare()
    builder.run()

@build.group()
def build_query(ctx, preset):
    """ Shows information relevant to the builds"""
    pass


@build_query.command()
@click.pass_context
@click.option('-o', '--output', type=click.Choice(['text', 'json']), default='text', help="Output type.")
def get_available_maps(ctx, output):

    presets = {"Maps":"asdfasdf"}

    if output == 'text':
        print("\n".join(presets.keys()))
    elif output == 'json':
        print(json.dumps(presets, indent=4))


@cli.group()
def validate():
    """validate and extract project infrastructure information"""


@validate.command()
@click.pass_context
@click.option('-o', '--output', type=click.Choice(['text', 'json']), default='text', help="Output type.")
def show_validate_profiles(ctx, output):
    """ output validation profiles"""
    run_config = ctx.obj['RUN_CONFIG']

    presets = get_validate_presets(run_config)

    if output == 'text':
        print("\n".join(presets.keys()))
    elif output == 'json':
        print(json.dumps(presets, indent=4))


@validate.command()
@click.pass_context
@click.option('-o', '--task', help="Output type.")
def run_validation_task(ctx, task):
    """ Runs a validation task """

    # TODO Handle the config overwrite
    run_config = ctx.obj['RUN_CONFIG']
    presets = get_validate_presets(run_config)

    if not task or task not in presets:
        L.error("Task %s does not exist", task) 
    else:
        commandlet = commandlets.BaseUE4Commandlet(run_config, task)
        commandlet.run()


@validate.command()
@click.pass_context
def refresh_asset_info(ctx):
    """ extracts raw information about assets"""
    # TODO Handle the config overwrite
    run_config = ctx.obj['RUN_CONFIG']
    packageinspection.BasePackageInspection(run_config).run()


@cli.group()
def run():
    """Run client builds under different configurations"""
    pass


@run.command()
@click.option('-o', '--output', type=click.Choice(['text', 'json']), default='text', help="Output type.")
@click.pass_context
def show_test_profiles(ctx, output):
    """Lists profiles that can be run as tests"""
    run_config = ctx.obj['RUN_CONFIG']
    profiles = clientutilities.get_test_profiles(run_config)

    if output == 'text':
        print("\n".join(profiles.keys()))
    elif output == 'json':
        print(json.dumps(profiles, indent=4))


@run.command()
@click.option('--profile', default="", help="Output type.")
@click.option('--test', default="", help="Output type.")
@click.option('-o', '--output', type=click.Choice(['text', 'json']), default='text', help="Output type.")
@click.pass_context
def run_client(ctx, profile, test, output):

    """Lists profiles that can be run as tests"""
    run_config = ctx.obj['RUN_CONFIG']
    available_profiles = clientutilities.get_test_profiles(run_config)

    message_output = {"Available Tests": available_profiles}
    valid_profile = False
    valid_test = False

    if not profile:
        message_output["ProfileMessage"] = "--profile argument required"
    elif profile not in available_profiles:
        message_output["ProfileMessage"] = profile + " profile was not found"
    else:
        valid_profile = True

    if not test:
        message_output["TestMessage"] = "--test argument required..."
    elif test not in available_profiles[profile]:
        message_output["TestMessage"] = test + " is not an available test"
    else:
        valid_test = True

    # If the arguments are correct
    if valid_profile and valid_test:
        message_output["Output"] = "Running build"
        runner = clientrunner.GameClientRunner(run_config, profile, test)
        if runner.does_build_exist():
            runner.run()

    else:
        # Error messages
        if output == 'text':
            print("\n".join(message_output.keys()))
        elif output == 'json':
            print(json.dumps(message_output, indent=4))


@run.command()
@click.option('-o', '--output', type=click.Choice(['text', 'json']), default='text', help="Output type.")
@click.pass_context
def process_client_results(ctx, output):

    # Find the raw test folder
    run_config = ctx.obj['RUN_CONFIG']

    run_processor = ClientRunProcessor.ClientRunParser(run_config)


if __name__ == "__main__":
    cli()
