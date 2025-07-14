"""Command line interface of realtime_pollen_calibration."""

import click

# First-party
from realtime_pollen_calibration.set_up import set_up_config
from realtime_pollen_calibration.update_phenology import update_phenology_realtime
from realtime_pollen_calibration.update_strength import update_strength_realtime
from realtime_pollen_calibration.utils import Config

# Local
from . import __version__


# pylint: disable-next=W0613  # unused-argument (param)
def print_version(ctx, param, value: bool) -> None:
    """Print the version number and exit."""
    if value:
        click.echo(__version__)
        ctx.exit(0)


@click.option(
    "--version",
    "-V",
    help="Print version and exit.",
    is_flag=True,
    expose_value=False,
    callback=print_version,
)
@click.group()
def main():
    pass


@main.command("update_phenology")
@click.argument("config_file", type=click.Path(exists=True, readable=True))
def update_phenology(config_file):
    """Configure and call update_phenology_realtime.

    Args:
        config_file (str): yaml configuration file

    """
    config_obj: Config = set_up_config(config_file)

    update_phenology_realtime(config_obj, True)


@main.command("update_strength")
@click.argument("config_file", type=click.Path(exists=True, readable=True))
def update_strength(config_file):
    """Configure and call update_strength_realtime.

    Args:
        config_file (str): yaml configuration file

    """
    config_obj: Config = set_up_config(config_file)

    update_strength_realtime(config_obj, True)
