#!/usr/bin/env python3
import json
import os
import discord
import aiohttp

from discord.ext import commands
from emoji import emojize


SERVER_URL = os.environ.get('SERVER_URL')

description = 'Shebang Remote bot to run Linux commands remotely from Discord.'
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', description=description, intents=intents)

@bot.event
async def on_ready():
    assert bot.user is not None

    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.command()
async def list_machines(ctx):
    """List all active machines."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{SERVER_URL}/machines') as response:
            try:
                machines = await response.json()

                if response.status == 200:
                    machines = json.dumps(machines, indent=4)
                    await ctx.send(f'Máquinas ativas:\n\n {machines}')

            except Exception:
                await ctx.send(f'{emojize(":no_entry:")} Ocorreu um erro inesperado.')

@bot.command()
async def register_script(ctx, name: str, content: str):
    """Add a script into the server with an uniq name and its content."""
    payload = dict(name=name, content=content)

    async with aiohttp.ClientSession() as session:
        async with session.post(f'{SERVER_URL}/scripts', json=payload) as response:
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

@bot.command()
async def execute_script(ctx, name: str, machine_id: str):
    """Schedule the execution of the given script to the given machine."""
    payload = dict(script_name=name, machine_id=machine_id)

    async with aiohttp.ClientSession() as session:
        async with session.post(f'{SERVER_URL}/execute', json=payload) as response:
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

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
