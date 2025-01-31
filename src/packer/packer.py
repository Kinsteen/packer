import click
import packer.curseforge as cf
import packer.config as config
import packer.compile

@click.group(invoke_without_command=True, help="By default, compile the modpack.")
@click.pass_context
def main(ctx):
    config.load_cache()

    if ctx.invoked_subcommand is None:
        packer.compile.compile()

@main.command(help="Compile the modpack in the current directory.")
def compile():
    packer.compile.compile()

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
