import sys
import click
import logging

from pilot import commands, exc
from pilot.version import __version__
from pilot.commands.auth import auth_commands
from pilot.commands.search import search_commands, delete
from pilot.commands.transfer import transfer_commands, status_commands, analyze
from pilot.commands.project import project, context

log = logging.getLogger(__name__)

INVOKABLE_WITHOUT_LOGIN = ['login', 'logout', 'version']


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    pc = commands.get_pilot_client()

    if not pc.config.is_migrated():
        click.secho('Old config detected, upgrading... ', fg='yellow',
                    nl=False)
        try:
            pc.config.migrate()
            click.secho('Success!', fg='green')
        except Exception:
            click.secho(f'Failed! Try removing '
                        f'{pc.config.CFG_FILENAME} and logging in '
                        f'again.', fg='red')
    if pc.is_logged_in():
        if pc.context.is_cache_stale():
            try:
                if pc.context.update_with_diff(dry_run=True):
                    click.secho('Projects have updated. Use '
                                '"pilot project update"'
                                ' to get the newest changes.', fg='yellow')
            except exc.HTTPSClientException as hce:
                log.exception(hce)
                click.secho(
                    'Unable to fetch the master project manifest. '
                    'It may have moved, or the HTTP server hosting it is down.'
                    ' Uploads and downloads may not work. Please check with '
                    'your admin for further details.', fg='red')
        pcommands = ['delete', 'describe', 'download', 'list', 'mkdir',
                     'upload']
        if not pc.project.is_set() and ctx.invoked_subcommand in pcommands:
            click.secho('No project set, use "pilot project" to list projects '
                        'and "pilot project set <myproject>" '
                        'to set your current project.', fg='yellow')
            sys.exit(exc.ExitCodes.INVALID_CLIENT_CONFIGURATION)
    else:
        if (ctx.invoked_subcommand and
                ctx.invoked_subcommand not in INVOKABLE_WITHOUT_LOGIN):
            click.echo('You are not logged in.')
            sys.exit(exc.ExitCodes.NOT_LOGGED_IN)

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@click.command(help='Show version and exit')
def version():
    click.echo(__version__)


cli.add_command(auth_commands.login)
cli.add_command(auth_commands.logout)
cli.add_command(auth_commands.profile_command)

cli.add_command(project.project_command)
cli.add_command(context.context_command)

cli.add_command(search_commands.list_command)
cli.add_command(search_commands.describe)
cli.add_command(delete.delete_command)

cli.add_command(transfer_commands.upload)
cli.add_command(analyze.analyze)
cli.add_command(transfer_commands.download)
cli.add_command(transfer_commands.mkdir)
cli.add_command(transfer_commands.register)
cli.add_command(status_commands.status)

cli.add_command(version)
