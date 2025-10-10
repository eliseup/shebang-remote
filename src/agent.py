#!/usr/bin/env python3
import argparse
import aiohttp
import asyncio
import subprocess
import json
import uuid
import os

from pathlib import Path
from typing import Any
from aiohttp import ClientSession

CONFIG_FILE_PATH = Path('/etc/shebang-remote/config.json')
UUID_PATH = Path('/etc/agent_uuid')

async def load_config():
    with open(CONFIG_FILE_PATH) as f:
        return json.load(f)

def get_or_create_uuid():
    if UUID_PATH.exists():
        return UUID_PATH.read_text().strip()
    new_uuid = str(uuid.uuid4())
    UUID_PATH.write_text(new_uuid)
    return new_uuid

async def register_agent(
        session: ClientSession,
        server_url: str,
        agent_id: str,
        name: str
) -> None:
    url = f'{server_url}/register_machine'
    payload = {'id': agent_id, 'name': name}

    try:
        async with session.post(url, json=payload) as resp:
            if resp.status == 200:
                print(f'Registered successfully as {name} ({agent_id})')
            else:
                print(f'Registration failed: {resp.status}')
    except Exception as e:
        print(f'Registration error: {e}')

async def send_command_result(
        session: ClientSession,
        server_url: str,
        command_id: str,
        command_output: dict[str, str]
) -> None:
    url = f'{server_url}/commands/{command_id}/result'

    payload = {'output': command_output}

    try:
        async with session.post(url, json=payload) as resp:
            if resp.status == 200:
                print(f'Successfully sent command result for command: {command_id}')

    except Exception as e:
        print(f'Error when sending command result: {e}')

async def execute_command(
        session: ClientSession,
        server_url: str,
        command_id: str,
        command: str
) -> None:
    print(f'Executing command: {command}')

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)

        output = {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }

        await send_command_result(session, server_url, command_id, output)

    except subprocess.TimeoutExpired:
        output = {'stdout': '', 'stderr': 'TimeoutExpired', 'returncode': 1}

        await send_command_result(session, server_url, command_id, output)

    except Exception as e:
        print(f'Error when executing the command "{command}": {e}')

async def check_pending_commands(
        session: ClientSession,
        server_url: str,
        agent_id: str
) -> list[dict[str, Any]]:
    url = f'{server_url}/commands/{agent_id}'

    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.json()
    except Exception as e:
        print(f'Pending commands fetch error: {e}')

    return []

async def main():
    parser = argparse.ArgumentParser(
        description='#! Remote - An Agent to manage Linux systems remotely from Discord.'
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    # Subcommand: register
    reg = subparsers.add_parser('register', help='Register agent with the server')
    reg.add_argument('--name', required=False, help='Name of the machine')
    reg.add_argument('--server', required=False, help='Base URL of the FastAPI server')

    args = parser.parse_args()

    #config = await load_config()
    #agent_id = get_or_create_uuid()
    #server_url = config['server_url']
    #name = config['name']
    #interval = config.get('interval', 300)

    async with aiohttp.ClientSession() as session:
        if args.command == 'register':
            print('to register', args)
            #await register_agent(session, server_url, agent_id, name)

        """while True:
            commands_response = await check_pending_commands(session, server_url, agent_id)

            for cmd_response in commands_response:
                cmd_id = cmd_response.get('id', '')
                cmd = cmd_response.get('script', {}).get('content')

                if cmd_id and cmd:
                    await execute_command(
                        session, server_url, command_id=cmd_id, command=cmd
                    )

            await asyncio.sleep(interval)"""

if __name__ == '__main__':
    asyncio.run(main())
