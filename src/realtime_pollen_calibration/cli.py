"""Command line interface of realtime_pollen_calibration."""

# Third-party
import click


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
@click.argument("data_path", type=click.Path(exists=True, readable=True, dir_okay=True))
@click.argument("date_string", type=str)
def update_strength(data_path: str, date_string: str):
    pass


@main.command("update_phenology")
@click.argument("data_path", type=click.Path(exists=True, readable=True, dir_okay=True))
@click.argument("date_string", type=str)
def update_phenology():
    pass
