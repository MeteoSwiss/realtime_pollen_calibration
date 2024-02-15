"""Command line interface of realtime_pollen_calibration."""

# Third-party
import click

# First-party
from realtime_pollen_calibration.set_up import set_up_paths
from realtime_pollen_calibration.update_phenology import update_phenology_realtime
from realtime_pollen_calibration.update_strength import update_strength_realtime
from realtime_pollen_calibration.utils import FilePaths

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


@main.command("update_strength")
@click.argument(
    "data_path",
    type=click.Path(exists=True, readable=True, dir_okay=True),
)
@click.argument("date_string", type=str)
def update_strength(data_path: str, date_string: str):
    """TODO 1

    Args:
        data_path (str): _description_
        date_string (str): _description_

    """
    file_paths: FilePaths = set_up_paths(data_path, date_string)

    hour_incr = 1
    update_strength_realtime(
        file_paths,
        hour_incr,
        True,
    )


@main.command("update_phenology")
@click.argument("data_path", type=click.Path(exists=True, readable=True, dir_okay=True))
@click.argument("date_string", type=str)
def update_phenology(data_path: str, date_string: str):
    """TODO  2

    Args:
        data_path (str): _description_
        date_string (str): _description_

    """
    file_paths: FilePaths = set_up_paths(data_path, date_string)

    hour_incr = 0
    update_phenology_realtime(file_paths, hour_incr, True)


@main.command("full_update")
@click.argument("data_path", type=click.Path(exists=True, readable=True, dir_okay=True))
@click.argument("date_string", type=str)
def update_phenology(data_path: str, date_string: str):
    """TODO 3

    Args:
        data_path (str): _description_
        date_string (str): _description_

    """
    file_paths: FilePaths = set_up_paths(data_path, date_string)

    hour_incr = 0
    update_phenology_realtime(file_paths, hour_incr, True)

    hour_incr = 1
    update_strength_realtime(
        file_paths,
        hour_incr,
        True,
    )
