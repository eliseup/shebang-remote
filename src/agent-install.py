#!/usr/bin/env python3
import argparse
import asyncio
import subprocess
import json
import uuid
import os

from pathlib import Path
from typing import Any

CONFIG_FILE_PATH = Path('/etc/shebang-remote/config.json')

async def load_config():
    with open(CONFIG_FILE_PATH) as f:
        return json.load(f)

def agent_install():
    config_path_parent = CONFIG_FILE_PATH.parent

    # Backup the current config
    if CONFIG_FILE_PATH.exists():
        CONFIG_FILE_PATH.rename(f'{CONFIG_FILE_PATH.absolute()}.bkp')

    if not config_path_parent.exists():
        config_path_parent.mkdir()

    if not CONFIG_FILE_PATH.exists():
        CONFIG_FILE_PATH.touch()

def main():
    parser = argparse.ArgumentParser(
        description='#! Remote - Installer.'
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    # Subcommand: install
    inst = subparsers.add_parser('install', help='Install the agent')

    args = parser.parse_args()

    if args.command == 'install':
        print('Installing agent...')
        agent_install()

    #config = await load_config()
    #agent_id = get_or_create_uuid()
    #server_url = config['server_url']
    #name = config['name']
    #interval = config.get('interval', 300)

if __name__ == '__main__':
    main()
