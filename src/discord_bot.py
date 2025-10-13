#!/usr/bin/env python3
import json
import os
from typing import Any

import discord
import aiohttp

from pathlib import Path

from itsdangerous import URLSafeSerializer, BadSignature
from discord.ext import commands
from emoji import emojize


APP_SERVER_URL = os.environ.get('APP_SERVER_URL')
DISCORD_ADMIN_USER_ID = int(os.getenv('DISCORD_ADMIN_USER_ID', 0))

description = 'Shebang Remote bot to run Linux commands remotely from Discord.'
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', description=description, intents=intents)


class EncryptSerializer(URLSafeSerializer):
    """
    An object that can be used to encrypt any data using the APP SECRET KEY.
    """
    def __init__(self):
        secret_key = os.getenv('APP_SECRET_KEY')
        salt = os.getenv('APP_SECURITY_SALT')

        super().__init__(
            secret_key=secret_key,
            salt=salt,
        )


def encrypt_data(data: Any) -> str:
    """Encrypt the given data."""
    encrypt_serializer = EncryptSerializer()
    encrypted_data = encrypt_serializer.dumps(data)
    return encrypted_data

def decrypt_data(encrypted_data: str) -> Any:
    """
    Decrypt the given encrypted_data.
    The encrypted_data should be encrypted using the :func: `encrypt_data`.
    """
    encrypt_serializer = EncryptSerializer()

    try:
        return encrypt_serializer.loads(encrypted_data)
    except BadSignature:
        return None

def get_authorized_users_file():
    """
    Get the file used to verify if a user is authorized to use this bot.
    Authorized users must have theirs ID wrote in thi file.
    """
    users_file = Path('./.dbot_auth.db')

    if not users_file.exists():
        users_file.touch()

    return users_file

def save_authorized_users_file(authorized_users: list[int]) -> bool:
    """
    Encrypt the given authorized users data and write the content
    to the authorized users file.
    """
    try:
        file_data = encrypt_data(json.dumps(authorized_users))
        authorized_users_file = get_authorized_users_file()
        authorized_users_file.write_text(file_data)
    except Exception:
        return False

    return True

def get_authorized_users() -> list[int]:
    """Reads the authorized users file decrypting its content."""
    users_file = get_authorized_users_file()
    content = users_file.read_text()
    content = decrypt_data(content)

    try:
        return json.loads(content)
    except TypeError:
        return []

async def abort_chat(ctx: commands.Context) -> None:
    """Abort chat for not allowed users."""
    await ctx.send(f'{emojize(":stop_sign:")} You are not authorized to use this command.')

    return

async def is_allowed_user(ctx: commands.Context) -> bool:
    """Verify if the user is authorized to use this bot."""
    user_id = ctx.author.id
    authorized_users = get_authorized_users()

    #return user_id in authorized_users or user_id == DISCORD_ADMIN_USER_ID
    return user_id in authorized_users

@bot.event
async def on_ready():
    assert bot.user is not None

    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.command()
async def whoami(ctx: commands.Context):
    user = ctx.author
    await ctx.send(
        f'You are {user.name}\n'
        f'Your user ID is {user.id}'
    )

@bot.command()
async def admin_allow_user(ctx: commands.Context, user_id: int) -> None:
    """Administrative command to add a new user into authorized users."""
    if ctx.author.id == DISCORD_ADMIN_USER_ID:
        authorized_users = get_authorized_users()

        if user_id not in authorized_users:
            authorized_users.append(user_id)
            success = save_authorized_users_file(authorized_users)

            if success:
                await ctx.send(
                    f'{emojize(":check_mark_button:")} '
                    f'{ctx.author.name} is now an authorized user.'
                )

            else:
                await ctx.send(f'{emojize(":no_entry:")} Was not possible to add this user now.')

    else:
        await abort_chat(ctx)

@bot.command()
async def admin_disallow_user(ctx: commands.Context, user_id: int) -> None:
    """Administrative command to remove a user from authorized users."""
    if ctx.author.id == DISCORD_ADMIN_USER_ID:
        authorized_users = get_authorized_users()

        if user_id in authorized_users:
            authorized_users.remove(user_id)
            success = save_authorized_users_file(authorized_users)

            if success:
                await ctx.send(
                    f'{emojize(":check_mark_button:")} '
                    f'{ctx.author.name} was removed from authorized users.'
                )

            else:
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
                        await ctx.send(
                            f'{emojize(":slight_frown:")} '
                            f'Não foi possível adicionar este script.\n\n{data}'
                        )

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
                        await ctx.send(
                            f'{emojize(":slight_frown:")} '
                            f'Não foi possível agendar a execução deste script.\n\n{data}'
                        )

                except Exception:
                    await ctx.send(f'{emojize(":no_entry:")} Ocorreu um erro inesperado.')

        else:
            await abort_chat(ctx)

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
