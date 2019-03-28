import argparse
import pathlib
import json
import logging
import click
import CONSTANTS

if __package__ is None or __package__ == '':
    from Editor import buildcommands, commandlets, packageinspection
    from Game import clientrunner
else:
    from . Editor import buildcommands, commandlets, packageinspection
    from . Game import clientrunner

L = logging.getLogger()


def _read_config(assembled_config_path=""):
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
    """ Read the build presets from the config """
    return dict(default_run_config[CONSTANTS.UNREAL_BUILD_SETTINGS_STRUCTURE])


def get_validate_presets(default_run_config):
    """ Read the commandlets settings from the config """
    return dict(default_run_config[CONSTANTS.COMMANDLET_SETTINGS])


@click.group()
def cli():
    """Sentinel Unreal Component handles running commands interacting with unreal engine"""
    pass

@cli.group()
def build():
    """Compile and build different targets"""

@build.command()
@click.option('-o','--output', type=click.Choice(['text', 'json']), default='text', help="Output type.")
def show_build_profiles(output):
    """ Lists the available build profiles as defined in settings"""
    config = _read_config()
    presets = get_default_build_presets(config)

    if output == 'text':
        print("\n".join(presets.keys()))
    elif output == 'json':
        print(json.dumps(presets, indent=4))


@build.command()
@click.option('-p','--preset', default='default', help="Build profile to run.")
def run_build(profile):
    """ Runs a build for the configured build preset"""

    # TODO making it so that the run config is loaded in as a global argument and made available
    # to all steps

    run_config = _read_config()
    L.debug("Available Builds: %s", "".join(get_default_build_presets(run_config)))

    builder = buildcommands.UnrealClientBuilder(run_config=run_config, build_config_name=profile) 
    builder.run()

@build.command()
@click.option('-o','--profile', type=click.Choice(['text', 'json']), default='text', help="Output type.")
def client(output):
    """Generates a client build based on the build profile"""

@cli.group()
def validate():
    """validate and extract project infrastructure information"""

@validate.command()
@click.option('-o','--output', type=click.Choice(['text', 'json']), default='text', help="Output type.")
def show_validate_profiles(output):
    """ output validation profiles"""
    config = _read_config()
    presets = get_validate_presets(config)

    if output == 'text':
        print("\n".join(presets.keys()))
    elif output == 'json':
        print(json.dumps(presets, indent=4))

@validate.command()
@click.option('-o','--task', help="Output type.")
def run_validation_task(task):
    """ Runs a validation task """
    #TODO Handle the config overwrite
    config = _read_config()

    presets = get_validate_presets(config)

    if not task or task not in presets:
        L.error("Task %s does not exist", task) 
    else:
        commandlet = commandlets.BaseUE4Commandlet(config, task)
        commandlet.run()

@validate.command()
def refresh_asset_info():
    """ extracts raw information about assets"""
    #TODO Handle the config overwrite
    config = _read_config()
    packageinspection.BasePackageInspection(config).run()

@cli.group()
def run():
    """Run client builds under different configurations"""
    pass


if __name__ == "__main__":
    cli()
