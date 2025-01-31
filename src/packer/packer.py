import click
import packer.curseforge as cf
import packer.config as config
import packer.compile
import packer.migration

@click.group(invoke_without_command=True, help="By default, compile the modpack.")
@click.pass_context
def main(ctx):
    config.load_cache()

    if ctx.invoked_subcommand != "migrate":
        if packer.migration.check_migrations():
            print("Migration is recommended!")
            print("Run with `packer migrate`")

    if ctx.invoked_subcommand is None:
        packer.compile.compile()

@main.command(help="Compile the modpack in the current directory.")
def compile():
    packer.compile.compile()

@main.command(help="Update the packer config if needed!")
def migrate():
    if not packer.migration.check_migrations():
        print("No migration is needed.")
    else:
        packer.migration.migrate_add_project_url()

@main.group(help="Curseforge helper tools")
def curseforge():
    pass

@curseforge.command(name = "url")
@click.argument('url')
def curseforge_url(url: str):
    cf.curseforge_url(url)

@curseforge.command(name = "dep")
@click.argument('url')
@click.option("--latest", type=bool, default=False, help="Will always use latest files available (default: false)")
def curseforge_dep(url: str, latest: bool):
    print(latest)
    cf.curseforge_dep(url, latest)

@main.group(help="Modrinth helper tools")
def modrinth():
    pass

@modrinth.command(name = "url")
def modrinth_url():
    pass
