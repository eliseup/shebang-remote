#!/usr/bin/env python3
import logging
import json
import sys

from logging.handlers import RotatingFileHandler

import discord
import aiohttp

from pathlib import Path

from discord.ext import commands
from emoji import emojize
from sqlalchemy import select

from server.config import settings
from server.database import get_db_session_ctx
from server.models import DiscordAuthorizedUser

APP_SERVER_URL = settings.APP_SERVER_URL.rstrip('/')
DISCORD_ADMIN_USER_ID = settings.DISCORD_ADMIN_USER_ID

# Logging setup
logging_file = Path('logs/discord_bot.log')

if not logging_file.parent.exists():
    logging_file.parent.mkdir()

logging_handler = RotatingFileHandler(
    filename=logging_file,
    maxBytes=5000000,
    backupCount=3,
)

logging_handler.setLevel(logging.INFO)

logging.basicConfig(
    handlers=[logging_handler, logging.StreamHandler(sys.stdout)],
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

def get_authorized_users() -> list[int]:
    """Reads the authorized users file decrypting its content."""
    with get_db_session_ctx() as session:
        authorized_users = session.scalars(select(DiscordAuthorizedUser)).all()

        return [i.author_id for i in authorized_users]

async def abort_chat(ctx: commands.Context) -> None:
    """Abort chat for not allowed users."""
    await ctx.send(f'{emojize(":stop_sign:")} You are not authorized to use this command.')

    return

async def is_allowed_user(ctx: commands.Context) -> bool:
    """Verify if the user is authorized to use this bot."""
    user_id = ctx.author.id

    with get_db_session_ctx() as session:
        authorized_user = session.scalar(select(DiscordAuthorizedUser).filter(
            DiscordAuthorizedUser.author_id == user_id,
        ))

        return authorized_user is not None

description = 'Shebang Remote bot to run Linux commands remotely from Discord.'
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', description=description, intents=intents)

@bot.event
async def on_command_error(ctx, error):
    # Handle "command not found"
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(
            f'{emojize(':warning:')} '
            f'That command doesn’t exist. Try `!help_` for a list of commands.'
        )

    # Handle missing arguments.
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'{emojize(':warning:')}️ Missing argument: `{error.param.name.upper()}`')

    # Catch-all fallback for unexpected errors.
    else:
        await ctx.send(f'{emojize(":no_entry:")} Oops! Something went wrong. Try again later.')
        logging.error(f'Unexpected error in command {ctx.command}: {error}')

@bot.event
async def on_ready():
    assert bot.user is not None

    msg = f'Logged in as {bot.user} (ID: {bot.user.id})'
    logging.info(msg)

    print(msg)
    print('------')

@bot.command()
async def help_(ctx: commands.Context) -> None:
    f"""Show the help command."""
    text = f"""    
    Shebang Remote Bot Commands:
    
    {emojize(':small_orange_diamond:')} **No Auth Required Commands**
    
    **!help_**
    _Shows this help message._
    
    **!whoami**
    _Shows the current user info like name and ID._
    
    ---
    
    {emojize(':small_orange_diamond:')} **Administrative Commands (Admin users only)**
    
    **!admin_allow_user** USER_ID
    _Allow a user to use this bot._
    
    **!admin_disallow_user** USER_ID
    _Disallow a user to use this bot._
    
    ---
    
    {emojize(':small_orange_diamond:')} **Auth Required Commands**
    
    **!list_machines**
    _List all active machines._
    
    **!register_script** "SCRIPT_NAME" "SCRIPT_CONTENT"
    _Register a script that can be scheduled later to run on a host._
    > Because the script name and its content may use 
    words with spaces in between, you should quote them.
    
    **!execute_script** SCRIPT_NAME MACHINE_ID
    _Schedule the execution of the given script to the given machine._
    > The script name is the same name returned by `!register_script` command.
    > The machine ID can be obtained using `!list_machines` command.
    """
    await ctx.send(text)

@bot.command()
async def whoami(ctx: commands.Context):
    user = ctx.author
    await ctx.send(
        f'You are **{user.name}**\n'
        f'Your user ID is **{user.id}**'
    )

@bot.command()
async def admin_allow_user(ctx: commands.Context, user_id: int) -> None:
    """Administrative command to add a new user into authorized users."""
    if ctx.author.id == DISCORD_ADMIN_USER_ID:

        with get_db_session_ctx() as session:
            if not session.scalar(select(DiscordAuthorizedUser).filter(
                DiscordAuthorizedUser.author_id == user_id,
            )):
                try:
                    session.add(DiscordAuthorizedUser(author_id=user_id))
                    session.commit()

                    await ctx.send(
                        f'{emojize(":check_mark_button:")} '
                        f'{ctx.author.name} is now an authorized user.'
                    )

                except Exception:
                    session.rollback()
                    logging.exception('Something went wrong when adding user to authorized users.')

                    await ctx.send(
                        f'{emojize(":no_entry:")} Was not possible to add this user now.'
                    )

    else:
        await abort_chat(ctx)

@bot.command()
async def admin_disallow_user(ctx: commands.Context, user_id: int) -> None:
    """Administrative command to remove a user from authorized users."""
    if ctx.author.id == DISCORD_ADMIN_USER_ID:

        with get_db_session_ctx() as session:
            existing_user = session.scalar(select(DiscordAuthorizedUser).filter(
                DiscordAuthorizedUser.author_id == user_id,
            ))

            if existing_user:
                try:
                    session.delete(existing_user)
                    session.commit()

                    await ctx.send(
                        f'{emojize(":check_mark_button:")} '
                        f'{ctx.author.name} was removed from authorized users.'
                    )

                except Exception:
                    session.rollback()
                    logging.exception(
                        'Something went wrong when removing user from authorized users.'
                    )

                    await ctx.send(
                        f'{emojize(":no_entry:")} Was not possible to disallow this user now.'
                    )

    else:
        await abort_chat(ctx)

@bot.command()
async def list_machines(ctx: commands.Context):
    """List all active machines."""
    async with aiohttp.ClientSession() as session:
        if await is_allowed_user(ctx):
            async with session.get(f'{APP_SERVER_URL}/machines') as response:
                try:
                    machines = await response.json()

                    if response.status == 200:
                        machines = json.dumps(machines, indent=4)
                        await ctx.send(f'Máquinas ativas:\n\n {machines}')

                except Exception:
                    await ctx.send(f'{emojize(":no_entry:")} Ocorreu um erro inesperado.')

        else:
            await abort_chat(ctx)

@bot.command()
async def register_script(ctx: commands.Context, name: str, content: str):
    """Add a script into the server with an uniq name and its content."""
    payload = dict(name=name, content=content)

    async with aiohttp.ClientSession() as session:
        if await is_allowed_user(ctx):
            async with session.post(f'{APP_SERVER_URL}/scripts', json=payload) as response:
                try:
                    data = await response.json()

                    if response.status == 200:
                        await ctx.send(
                            f'{emojize(":check_mark_button:")} '
                            f'O script "{data.get('name')}" foi adicionado com sucesso.'
                        )

                    else:
                        data = json.dumps(data, indent=4)
                        msg = (
                            f'{emojize(":slight_frown:")} '
                            f'Não foi possível adicionar este script.\n\n{data}'
                        )

                        logging.error(f'{msg} :: Response code: {response.status}')

                        await ctx.send(msg)

                except Exception:
                    await ctx.send(f'{emojize(":no_entry:")} Ocorreu um erro inesperado.')

        else:
            await abort_chat(ctx)

@bot.command()
async def execute_script(ctx: commands.Context, name: str, machine_id: str):
    """Schedule the execution of the given script to the given machine."""
    payload = dict(script_name=name, machine_id=machine_id)

    async with aiohttp.ClientSession() as session:
        if await is_allowed_user(ctx):
            async with session.post(f'{APP_SERVER_URL}/execute', json=payload) as response:
                try:
                    data = await response.json()

                    if response.status == 200:
                        await ctx.send(
                            f'{emojize(":check_mark_button:")} Sucesso!\n'
                            f'O script "{name}" foi agendado para '
                            f'ser executado na máquina "{machine_id}"'
                        )

                    else:
                        data = json.dumps(data, indent=4)
                        msg = (
                            f'{emojize(":slight_frown:")} '
                            f'Não foi possível agendar a execução deste script.\n\n{data}'
                        )

                        logging.error(f'{msg} :: Response code: {response.status}')

                        await ctx.send(msg)

                except Exception:
                    await ctx.send(f'{emojize(":no_entry:")} Ocorreu um erro inesperado.')

        else:
            await abort_chat(ctx)

bot.run(settings.DISCORD_BOT_TOKEN)
