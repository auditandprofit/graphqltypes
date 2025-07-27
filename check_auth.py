import os
import re
import json
import subprocess
import argparse

ROOT = os.path.dirname(os.path.abspath(__file__))

NOAUTH_FILE = os.path.join(ROOT, 'noauthtypes.txt')

TYPES_DIRS = ['types_ce', 'types_ee']


def parse_args():
    parser = argparse.ArgumentParser(
        description='Check GraphQL fields that return unauthenticated types'
    )
    parser.add_argument(
        '--inverse',
        action='store_true',
        help='Output usages where fields include an authorize: argument'
    )
    parser.add_argument(
        '--count',
        action='store_true',
        help='Output only a summary count of auth and no-auth usages'
    )
    return parser.parse_args()

def resolve_path(path):
    """Return an existing path, attempting to handle older entries."""
    if os.path.exists(path):
        return path

    candidates = []

    if 'app/graphql/types/' in path:
        candidates.append(path.replace('app/graphql/types/', ''))

    if 'graphql/types/' in path:
        candidates.append(path.replace('graphql/types/', ''))

    if 'app/' in path:
        candidates.append(path.replace('app/', ''))

    for alt in candidates:
        if os.path.exists(alt):
            return alt

    return path

def extract_type_name(path):
    path = resolve_path(path)
    stack = []
    deepest = []
    try:
        with open(path, 'r') as f:
            for line in f:
                m = re.match(r'\s*module\s+([A-Za-z0-9_]+)', line)
                if m:
                    stack.append(m.group(1))
                    if len(stack) > len(deepest):
                        deepest = stack.copy()
                    continue
                m = re.match(r'\s*class\s+([A-Za-z0-9_]+)', line)
                if m:
                    stack.append(m.group(1))
                    return '::'.join(stack)
                if re.match(r'\s*end\b', line) and stack:
                    stack.pop()
    except FileNotFoundError:
        return None
    if deepest:
        return '::'.join(deepest)
    return None

def grep_usages(constant, exclude_path):
    paths = [d for d in TYPES_DIRS if os.path.exists(d)]
    cmd = ['grep', '-R', constant, '-n'] + paths
    res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, stderr=subprocess.DEVNULL)
    lines = []
    for line in res.stdout.splitlines():
        if exclude_path in line:
            continue
        lines.append(line)
    return lines

def field_has_authorize(path, line_number):
    try:
        with open(path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return False
    start = max(0, line_number-2)
    end = min(len(lines), line_number+5)
    snippet = ''.join(lines[start:end])
    return 'authorize:' in snippet

def extract_field_name(line):
    m = re.search(r'field\s+:?([A-Za-z0-9_]+)', line)
    if m:
        return m.group(1)
    return None


def find_field_usage(path, line_number):
    """Return (line_number, field_name) for the field call near a constant."""
    try:
        with open(path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return None, None

    start = max(0, line_number - 3)
    end = min(len(lines), line_number + 2)
    for idx in range(start, end):
        line = lines[idx]
        if 'field' in line:
            name = extract_field_name(line)
            if name:
                return idx + 1, name
    return None, None


def main():
    args = parse_args()
    result = {}
    auth_count = 0
    noauth_count = 0
    total_types = 0
    with open(NOAUTH_FILE) as f:
        for file_path in f:
            file_path = file_path.strip()
            if not file_path or file_path.startswith('#'):
                continue
            total_types += 1
            type_file = file_path
            if not os.path.isabs(type_file):
                type_file = os.path.join(ROOT, type_file)
            type_file = resolve_path(type_file)
            constant = extract_type_name(type_file)
            if not constant:
                continue
            usages = []
            exclude = os.path.relpath(type_file, ROOT)
            for line in grep_usages(constant, exclude):
                match = re.match(r'([^:]+):(\d+):(.*)', line)
                if not match:
                    continue
                other_file, ln, text = match.groups()
                ln = int(ln)
                field_ln, field_name = find_field_usage(other_file, ln)
                if not field_name:
                    continue
                has_auth = field_has_authorize(other_file, field_ln)
                if args.count:
                    if has_auth:
                        auth_count += 1
                    else:
                        noauth_count += 1
                    continue
                if args.inverse:
                    if not has_auth:
                        continue
                else:
                    if has_auth:
                        continue
                other_constant = extract_type_name(other_file)
                usages.append({
                    'file': os.path.relpath(other_file, ROOT),
                    'type': other_constant,
                    'field': field_name,
                    'line': field_ln
                })
            if usages:
                result[constant] = {
                    'file': file_path,
                    'usages': usages
                }
    if args.count:
        summary = {
            'total_types': total_types,
            'auth_matches': auth_count,
            'noauth_matches': noauth_count
        }
        print(json.dumps(summary, indent=2))
    else:
        print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
