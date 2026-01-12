import logging

import click

import modpacker.compile
import modpacker.config as config
import modpacker.migration
import modpacker.services.curseforge as cf
import modpacker.services.modrinth as mr
import modpacker.services.packwiz as pw
from modpacker import server
from modpacker.commands.add import add
from modpacker.log.multi_formatter import MultiFormatter

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

    c = config.open_config(silently_fail=True)
    if c is None:
        logger.error(f"Can't find a 'packer_config.json' in the current directory.")
        exit(1)

    if modpacker.migration.check_migrations():
        logger.info("Running migrations...")
        modpacker.migration.migrate_add_project_url()
        modpacker.migration.migrate_add_slug()
        logger.info("Done!")

    if ctx.invoked_subcommand is None:
        modpacker.compile.compile()


@main.command(help="Compile the modpack in the current directory.")
def compile():
    modpacker.compile.compile()


@main.group(help="Curseforge helper tools")
def curseforge():
    pass


@curseforge.command(
    name="url", help="Get the download URL from the mod version page URL"
)
@click.argument("url")
def curseforge_url(url: str):
    cf.curseforge_url(url)


@curseforge.command(
    name="add", help="Add mod(s) from Curseforge to the packer config file."
)
@click.option("--save", type=bool, default=False, is_flag=True)
@click.option(
    "--latest",
    type=bool,
    default=False,
    is_flag=True,
    help="Will always pick the latest available version, and will NOT download optional dependencies.",
)
@click.argument("slugs", nargs=-1)
def curseforge_add(slugs, save, latest):
    provider = cf.CurseforgeProvider()
    add(provider, slugs, save, latest)


@main.group(help="Modrinth helper tools")
def modrinth():
    pass


@modrinth.command(
    name="add", help="Add mod(s) from Modrinth to the packer config file."
)
@click.option("--save", type=bool, default=False, is_flag=True)
@click.option(
    "--latest",
    type=bool,
    default=False,
    is_flag=True,
    help="Will always pick the latest available version, and will NOT download optional dependencies.",
)
@click.argument("slugs", nargs=-1)
def modrinth_add(slugs, save, latest):
    provider = mr.ModrinthProvider()
    add(provider, slugs, save, latest)


@main.command(help="Export modpack to packwiz format.")
@click.argument("output", type=click.Path())
def packwiz(output):
    pw.convert(output)


@main.group(name="server", help="Server tools")
def server_cmd():
    pass


@server_cmd.command(
    name="export", help="Export modpack for server (only server files)."
)
@click.argument("output", type=click.Path())
def server_export(output):
    server.export(output)
