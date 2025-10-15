#!/usr/bin/env python3
import argparse
import sys

import aiohttp
import asyncio
import subprocess
import json
import uuid
import logging

from pathlib import Path
from typing import Any, Dict
from aiohttp import ClientSession, ContentTypeError


# Basic logging setup
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(name)s - %(levelname)s - %(message)s',
)

async def load_config() -> Dict[str, str]:
    """Reads the agent's configuration file and returns it as a dictionary."""
    config_file_path = Path('/etc/agent/config.json')

    if config_file_path.is_file():
        return json.loads(config_file_path.read_text())

    return {}

def get_or_create_agent_uuid() -> str:
    random_uuid = str(uuid.uuid4())

    try:
        system_uuid = subprocess.run(
            ['dmidecode', '-s', 'system-uuid'], check=True, text=True, capture_output=True
        )

        system_uuid = system_uuid.stdout.strip()

        if system_uuid:
            return system_uuid
        return random_uuid

    except subprocess.CalledProcessError:
        return random_uuid

def get_or_create_agent_name() -> str:
    random_name = str(f'agent-{str(uuid.uuid4())[:5]}')

    try:
        name = subprocess.run(['hostname'], check=True, text=True, capture_output=True)
        name = name.stdout.strip()

        if name:
            return name
        return random_name

    except subprocess.CalledProcessError:
        return random_name

async def make_request(
        session: ClientSession,
        *,
        url: str,
        method: str,
        payload: dict | None = None,
) -> tuple[int, list[Any] | dict[str, Any] | None]:
    """This function makes a request to the given URL and returns (status, json) tuple."""
    status, response_data = 0, None

    try:
        async with session.request(method, url, json=payload) as response:
            status = response.status

            try:
                response_data = await response.json()
            except ContentTypeError:
                logging.exception('Error when getting response data:', exc_info=True)

    except Exception:
        logging.exception('Something went wrong when making a request.', exc_info=True)

    return status, response_data

async def register_agent(
        session: ClientSession,
        server_url: str,
        agent_id: str,
        agent_name: str
) -> bool:
    """
    Register this agent (machine) to the server.
    """
    url = f'{server_url}/register_machine'
    payload = {'id': agent_id, 'name': agent_name}

    status, data = await make_request(session, url=url, method='POST', payload=payload)

    if status == 200:
        config_file = Path('/etc/agent/config.json')
        config_content = dict(
            server_url=server_url, agent_id=agent_id, agent_name=agent_name, interval=300
        )

        try:
            with open(config_file, 'w') as f:
                json.dump(config_content, f, indent=4)
        except Exception as e:
            print('Something went wrong when writing the agent configuration file:', e)
        else:
            print(f'Registered successfully as {agent_name} ({agent_id})')

            return True

    else:
        print(f'Failed to register as {agent_name} ({agent_id})')

    return False

async def check_pending_commands(
        session: ClientSession,
        server_url: str,
        agent_id: str
) -> list[dict[str, Any]]:
    """Request the server to check if there are any pending commands for this agent."""
    logging.info('Checking pending commands.')

    url = f'{server_url}/commands/{agent_id}'

    status, data = await make_request(session, url=url, method='GET')

    if status == 200:
        return data

    return []

async def send_command_result(
        session: ClientSession,
        server_url: str,
        command_id: str,
        command: str,
        command_output: dict[str, str]
) -> None:
    """
    Sends a command result (output) to the server.
    After a command was executed, the command output must be sent back to the server.
    """
    url = f'{server_url}/commands/{command_id}/result'

    payload = {'output': command_output}

    status, data = await make_request(session, url=url, method='POST', payload=payload)

    if status == 200:
        logging.info(f'Successfully sent command result for command: {command}')
    else:
        logging.error(f'Error when sending command result for command: {command}: {data}')

async def execute_command(
        session: ClientSession,
        server_url: str,
        command_id: str,
        command: str
) -> None:
    """Execute the given command and send its result to the server."""
    try:
        logging.info(f'Executing command: {command}')

        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)

        output = {
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
            'returncode': result.returncode
        }

        logging.info(f'Command output: {output}')

        await send_command_result(
            session, server_url, command_id, command=command, command_output=output
        )

    except subprocess.TimeoutExpired:
        output = {'stdout': '', 'stderr': 'TimeoutExpired', 'returncode': 1}

        logging.error(f'Command output: {output}')
        await send_command_result(
            session, server_url, command_id, command=command, command_output=output
        )

    except Exception:
        logging.exception(f'Error when executing the command "{command}":', exc_info=True)

async def main():
    parser = argparse.ArgumentParser(
        description='#! Remote - An Agent to manage Linux systems remotely from Discord.'
    )

    subparsers = parser.add_subparsers(dest='command', required=False)

    # Subcommand: register
    reg = subparsers.add_parser(
        'register', help='Register this agent (machine) to the server'
    )
    reg.add_argument('--name', required=False, help='Name of the machine')
    reg.add_argument('--server', required=True, help='Base URL of the FastAPI server')

    args = parser.parse_args()

    if args.command == 'register':
        print('Registering agent...')
        agent_id = get_or_create_agent_uuid()
        agent_name = get_or_create_agent_name()

        async with aiohttp.ClientSession() as session:
            registered = await register_agent(
                session,
                server_url=args.server.rstrip('/'),
                agent_id=agent_id,
                agent_name=agent_name
            )

            if registered:
                print('Done! :)')
            else:
                print('Failed :(')

    else:
        logging.info('Running the agent main loop.')

        config = await load_config()

        server_url = config.get('server_url', '').rstrip('/')
        agent_id = config['agent_id']
        interval = config.get('interval', 300)

        async with aiohttp.ClientSession() as session:
            while True:
                commands_response = await check_pending_commands(session, server_url, agent_id)

                for cmd_response in commands_response:
                    cmd_id = cmd_response.get('id', '')
                    cmd = cmd_response.get('script', {}).get('content')

                    if cmd_id and cmd:
                        await execute_command(
                            session, server_url, command_id=cmd_id, command=cmd
                        )

                await asyncio.sleep(interval)

if __name__ == '__main__':
    asyncio.run(main())
