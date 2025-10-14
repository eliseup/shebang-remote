import json
import re
import shlex

from dataclasses import field
from datetime import datetime
from typing import Set, Iterable

from pydantic import BaseModel, field_validator


class DefaultResponseSchemaMixin:
    created_at: datetime
    updated_at: datetime


class MachineSchema(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True


class MachineResponseSchema(DefaultResponseSchemaMixin, MachineSchema):
    last_seen: datetime


class ScriptSchema(BaseModel):
    name: str
    content: str

    @field_validator('content', mode='before')
    def validate_allowed_commands(cls, v: str) -> str:
        allowed_commands: Set[str] = {
            'awk', 'basename', 'cat', 'cd', 'cp', 'cut', 'date', 'df', 'diff', 'diff3', 'dig',
            'dirname', 'dmesg', 'dmidecode', 'du', 'echo', 'env', 'find', 'free', 'grep', 'head',
            'help', 'history', 'host', 'hostname', 'id', 'info', 'ip', 'journalctl', 'less', 'll',
            'ls', 'lsof', 'man', 'md5sum', 'mkdir', 'more', 'nmap', 'ping', 'printenv', 'printf',
            'ps', 'pwd', 'readlink', 'rmdir', 'sar', 'sed', 'sleep', 'sort', 'ss', 'stat', 'tac',
            'tail', 'tar', 'touch', 'tr', 'uname', 'uniq', 'uptime', 'vmstat', 'wc', 'which',
            'whoami', 'whois', 'xargs'
        }

        # Paths (prefixes) that must NOT be accessed (read or write)
        forbidden_path_prefixes: Iterable[str] = (
            '/etc', '/root', '/boot', '/dev', '/proc', '/sys', '/var/lib', '/var/run', '/run'
        )

        # Very unsafe tokens we outright disallow anywhere in the script
        disallowed_tokens: Iterable[str] = (
            ';', '&&', '||', '`', '$(', 'sudo', 'su'
        )

        if not v:
            return v

        # Helper: check whether a token references a forbidden path
        def token_references_forbidden_path(tok: str) -> bool:
            # simple canonicalization: remove quotes
            tok_clean = tok.strip('\'"')
            # Expand common tokens we can reason about simply:
            if tok_clean.startswith('~'):
                # conservative: treat ~ as potentially /root or user home; forbid if explicitly /root
                # here we do not map ~ to actual user home; if script contains ~root/... block conservatively
                if tok_clean.startswith('~root') or tok_clean == '~root' or tok_clean.startswith(
                        '~/root'):
                    return True
                # otherwise be lenient and do not consider ~ as forbidden
            if not tok_clean.startswith('/'):
                return False
            for pref in forbidden_path_prefixes:
                # consider exact prefix or prefix + '/'
                if tok_clean == pref or tok_clean.startswith(pref + '/'):
                    return True
            return False

        # Quick overall-scan for disallowed tokens (anywhere)
        lowered = v.lower()
        for bad in disallowed_tokens:
            if bad in lowered:
                raise ValueError(f'Script contains disallowed token or construct: "{bad}"')

        # Break into lines and validate each "command line". Comments/blank lines ignored.
        for lineno, raw_line in enumerate(v.splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue

            # Reject inline command-chaining characters explicitly if present
            if ';' in line or '&&' in line or '||' in line:
                raise ValueError(f'Chaining with ";", "&&" or "||" is not allowed (line {lineno})')

            # We allow pipelines: split on '|' and validate each segment
            segments = [seg.strip() for seg in line.split('|')]
            if not segments:
                raise ValueError(f'Unable to parse line {lineno}: "{line}"')

            for seg in segments:
                if not seg:
                    raise ValueError(f'Empty pipeline segment in line {lineno}')

                # Handle redirections: we'll parse tokens and keep track if there's a '>' or '<'
                try:
                    tokens = shlex.split(seg, comments=False)
                except ValueError:
                    raise ValueError(
                        f'Unable to safely parse tokens (shell quoting issue) on line {lineno}')

                if not tokens:
                    raise ValueError(f'No tokens found in pipeline segment on line {lineno}')

                # Skip leading environment assignments like VAR=val VAR2=val2 cmd ...
                cmd_token = None
                token_index = 0
                for i, tok in enumerate(tokens):
                    if re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', tok):
                        continue
                    # first non env-assignment token is expected to be command
                    cmd_token = tok
                    token_index = i
                    break

                if cmd_token is None:
                    raise ValueError(f'No command found in segment on line {lineno}')

                # If command is a path (/bin/ls) get basename to compare against allowlist
                cmd_basename = cmd_token
                if '/' in cmd_token:
                    cmd_basename = cmd_token.split('/')[-1]

                # Normalize to lowercase for comparison
                cmd_basename_l = cmd_basename.lower()

                if cmd_basename_l not in allowed_commands:
                    raise ValueError(f'Command "{cmd_token}" is not allowed (line {lineno})')

                # Now inspect remaining tokens for forbidden paths or dangerous file writes
                # Detect redirections in the ORIGINAL segment text to find redirect targets reliably
                # Simple approach: check tokens after the command token
                i = token_index + 1
                while i < len(tokens):
                    tok = tokens[i]
                    # redirection operators
                    if tok in ('>', '>>', '<', '2>', '2>>'):
                        # next token should be a path/filename
                        if i + 1 >= len(tokens):
                            raise ValueError(
                                f'Redirection operator "{tok}" with no target (line {lineno})')
                        target = tokens[i + 1]
                        if token_references_forbidden_path(target):
                            raise ValueError(
                                f'Redirection target "{target}" is forbidden (line {lineno})')
                        i += 2
                        continue

                    # If token itself is something like 'output.txt' or '/etc/passwd'
                    if token_references_forbidden_path(tok):
                        raise ValueError(f'Access to forbidden path "{tok}" (line {lineno})')

                    i += 1

        # If we reach here, the script passed checks
        return v

    @field_validator('name', mode='before')
    def normalize_name(cls, value):
        return value.replace(' ', '').lower().strip()

    class Config:
        from_attributes = True


class ScriptResponseSchema(DefaultResponseSchemaMixin, ScriptSchema):
    pass


class CommandStatusReferenceResponseSchema(DefaultResponseSchemaMixin, BaseModel):
    title: str
    title_internal: str


class CommandSchema(BaseModel):
    machine_id: str
    script_name: str

    class Config:
        from_attributes = True


class CommandResponseSchema(DefaultResponseSchemaMixin, CommandSchema):
    id: int
    status: CommandStatusReferenceResponseSchema
    script: ScriptSchema
    output: str | None


class CommandResultSchema(BaseModel):
    output: str | None

    @field_validator('output', mode='before')
    def normalize_output(cls, value):
        try:
            return json.dumps(value)
        except TypeError:
            return value
