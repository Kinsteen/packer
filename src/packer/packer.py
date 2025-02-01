import logging

import click

import packer.compile
import packer.config as config
import packer.migration
import packer.services.curseforge as cf
import packer.services.modrinth as mr
from packer.log.multi_formatter import MultiFormatter

logger = logging.getLogger(__name__)


@click.group(invoke_without_command=True, help="By default, compile the modpack.")
@click.option("-v", "--verbose", count=True)
@click.pass_context
def main(ctx, verbose):
    root_logger = logging.getLogger()
    if verbose > 0:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(MultiFormatter())
    root_logger.addHandler(console_handler)

    config.load_cache()

    if ctx.invoked_subcommand != "migrate":
        if packer.migration.check_migrations():
            logger.info("Migration is recommended!")
            logger.info("Run with `packer migrate`")

    if ctx.invoked_subcommand is None:
        packer.compile.compile()


@main.command(help="Compile the modpack in the current directory.")
def compile():
    packer.compile.compile()


@main.command(help="Update the packer config if needed!")
def migrate():
    if not packer.migration.check_migrations():
        logger.info("No migration is needed.")
    else:
        packer.migration.migrate_add_project_url()


@main.group(help="Curseforge helper tools")
def curseforge():
    pass


@curseforge.command(name="url")
@click.argument("url")
def curseforge_url(url: str):
    cf.curseforge_url(url)


@curseforge.command(name="dep")
@click.argument("url")
@click.option(
    "--latest",
    type=bool,
    default=False,
    help="Will always use latest files available (default: false)",
)
def curseforge_dep(url: str, latest: bool):
    cf.curseforge_dep(url, latest)


@main.group(help="Modrinth helper tools")
def modrinth():
    pass


@modrinth.command(name="dep")
@click.argument("url")
def modrinth_dep(url):
    mr.modrinth_dep(url)
