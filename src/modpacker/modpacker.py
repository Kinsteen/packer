import atexit
import logging

import click
import jsonschema

import modpacker.compile
import modpacker.config as config
import modpacker.migration
import modpacker.services.curseforge as cf
import modpacker.services.modrinth as mr
import modpacker.services.packwiz as pw
from modpacker import server
from modpacker.cache import Cache
from modpacker.commands.add import add
from modpacker.commands.update import update as update_exec
from modpacker.log.multi_formatter import MultiFormatter
from modpacker.packer_config import PackerConfig

logger = logging.getLogger(__name__)

@click.group(invoke_without_command=True, help="By default, compile the modpack.")
@click.option("-v", "--verbose", count=True)
@click.pass_context
@click.version_option()
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

    try:
        c = config.open_config()
    except jsonschema.exceptions.ValidationError as e:
        logger.error(f"'packer_config.json' is invalid: {e.message}", exc_info=True)
        logger.error(e.message)
        exit(1)
    except Exception as e:
        logger.error("There was an error while opening 'packer_config.json':")
        logger.error(e)
        exit(1)

    if c is None:
        logger.error("Can't find a 'packer_config.json' in the current directory.")
        exit(1)

    cache = Cache()
    ctx.obj = {
        "packer_config": PackerConfig(c),
        "cache": cache
    }

    def on_exit():
        cache.persist()
    atexit.register(on_exit)

    if modpacker.migration.check_migrations():
        logger.info("Running migrations...")
        modpacker.migration.migrate_add_project_url()
        modpacker.migration.migrate_add_slug()
        logger.info("Done!")

    if ctx.invoked_subcommand is None:
        modpacker.compile.compile(ctx.obj["packer_config"], ctx.obj["cache"])


@main.command(help="Compile the modpack in the current directory.")
@click.option("--prism", default=False, is_flag=True)
@click.pass_obj
def compile(obj, prism):
    modpacker.compile.compile(obj["packer_config"], obj["cache"], prism)


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
@click.pass_obj
def curseforge_add(obj, slugs, save, latest):
    provider = cf.CurseforgeProvider(obj["packer_config"])
    add(obj["packer_config"], provider, slugs, save, latest)


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
@click.pass_obj
def modrinth_add(obj, slugs, save, latest):
    provider = mr.ModrinthProvider(obj["packer_config"])
    add(obj["packer_config"], provider, slugs, save, latest)


@main.command(help="Export modpack to packwiz format.")
@click.argument("output", type=click.Path())
@click.pass_obj
def packwiz(obj, output):
    pw.convert(obj["packer_config"], obj["cache"], output)


@main.group(name="server", help="Server tools")
def server_cmd():
    pass


@server_cmd.command(
    name="export", help="Export modpack for server (only server files)."
)
@click.argument("output", type=click.Path())
@click.pass_obj
def server_export(obj, output):
    server.export(obj["packer_config"], obj["cache"], output)


@main.command(help="Update all mods.")
@click.pass_obj
def update(obj):
    update_exec(obj["packer_config"])
