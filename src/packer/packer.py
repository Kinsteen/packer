import logging

import click

import packer.compile
import packer.config as config
import packer.migration
import packer.services.curseforge as cf
import packer.services.modrinth as mr
import packer.services.packwiz as pw
from packer import server
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


@curseforge.command(name="url", help="Get the download URL from the mod version page URL")
@click.argument("url")
def curseforge_url(url: str):
    cf.curseforge_url(url)


@curseforge.command(name="add", help="Add mod(s) from Curseforge to the packer config file.")
@click.option("--save", type=bool, default=False, is_flag=True)
@click.argument("slugs", nargs=-1)
def curseforge_add(slugs, save):
    cf.curseforge_add(slugs, save)


@main.group(help="Modrinth helper tools")
def modrinth():
    pass


@modrinth.command(name="add", help="Add mod(s) from Modrinth to the packer config file.")
@click.option("--save", type=bool, default=False, is_flag=True)
@click.argument("slugs", nargs=-1)
def modrinth_add(slugs, save):
    mr.modrinth_add(slugs, save)


@main.command(help="Export modpack to packwiz format.")
@click.argument("output", type=click.Path())
def packwiz(output):
    pw.convert(output)


@main.group(name="server", help="Server tools")
def server_cmd():
    pass


@server_cmd.command(name="export", help="Export modpack for server (only server files).")
@click.argument("output", type=click.Path())
def server_export(output):
    server.export(output)
