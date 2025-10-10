#!/usr/bin/env python3
import argparse
import textwrap
import shutil
import subprocess

from pathlib import Path


def systemd_setup(remove: bool = False) -> None:
    """Install or remove the systemd service for the Shebang Remote Agent."""
    systemd_file = Path('/etc/systemd/system/shebang-remote-agent.service')
    agent_src = Path('agent.py')
    agent_dest = Path('/usr/local/bin/agent.py')

    if remove:
        # Remove agent's systemd config
        subprocess.run(['systemctl', 'stop', 'shebang-remote-agent'])
        subprocess.run(['systemctl', 'disable', 'shebang-remote-agent'])
        subprocess.run(['systemctl', 'daemon-reload'])
        systemd_file.unlink()

        # Removes /usr/local/bin/agent.py
        agent_dest.unlink()

    else:
        # Copy agent.py to /usr/local/bin/
        shutil.copy(agent_src, agent_dest)
        agent_dest.chmod(0o755)

        # Setup agent's systemd config
        systemd_file.touch()
        systemd_file.chmod(0o644)

        systemd_file_content = textwrap.dedent("""
               [Unit]
               Description=Shebang Remote Agent Service
               After=network.target

               [Service]
               ExecStart=/usr/local/bin/agent.py
               Restart=always
               RestartSec=10
               User=root

               [Install]
               WantedBy=multi-user.target
           """)

        systemd_file.write_text(systemd_file_content)

        subprocess.run(['systemctl', 'daemon-reload'])
        subprocess.run(['systemctl', 'enable', 'shebang-remote-agent'])
        subprocess.run(['systemctl', 'start', 'shebang-remote-agent'])

def agent_config_setup(remove: bool = False) -> None:
    """Create or remove the configuration directory and file for the agent."""
    config_file_path = Path('/etc/shebang-remote/config.json')
    config_file_parent_path = config_file_path.parent

    if remove:
        # Removes the agent's config
        shutil.rmtree(config_file_parent_path)

    else:
        # Setup agent's config
        if config_file_path.exists():
            # Backup the current config
            config_file_path.rename(f'{config_file_path.absolute()}.bkp')

        if not config_file_parent_path.exists():
            # Create the config path
            config_file_parent_path.mkdir()

        if not config_file_path.exists():
            # Create an empty config file
            config_file_path.touch()

def uninstall():
    """Completely remove the agent, its service, and configuration."""
    systemd_setup(remove=True)
    agent_config_setup(remove=True)

def install():
    """Install and configure the agent and its systemd service."""
    agent_config_setup()
    systemd_setup()

def main():
    parser = argparse.ArgumentParser(
        description='#! Remote - Setup CLI.'
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    # Subcommands: install and uninstall
    subparsers.add_parser('install', help='Install the agent')
    subparsers.add_parser('uninstall', help='Uninstall the agent')

    args = parser.parse_args()

    if args.command == 'install':
        print('Installing agent...')
        install()

    elif args.command == 'uninstall':
        print('Uninstalling agent...')
        uninstall()

if __name__ == '__main__':
    main()
