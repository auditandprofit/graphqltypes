import os
import re
import json
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))

NOAUTH_FILE = os.path.join(ROOT, 'noauthtypes.txt')

TYPES_DIRS = ['types_ce', 'types_ee']

def extract_type_name(path):
    stack = []
    try:
        with open(path, 'r') as f:
            for line in f:
                m = re.match(r'\s*module\s+([A-Za-z0-9_]+)', line)
                if m:
                    stack.append(m.group(1))
                    continue
                m = re.match(r'\s*class\s+([A-Za-z0-9_]+)', line)
                if m:
                    stack.append(m.group(1))
                    return '::'.join(stack)
                if re.match(r'\s*end\b', line) and stack:
                    stack.pop()
    except FileNotFoundError:
        return None
    return None

def grep_usages(constant, exclude_path):
    paths = [d for d in TYPES_DIRS if os.path.exists(d)]
    cmd = ['grep', '-R', constant, '-n'] + paths
    res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, stderr=subprocess.DEVNULL)
    lines = []
    for line in res.stdout.splitlines():
        if exclude_path in line:
            continue
        if 'field' not in line:
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


def main():
    result = {}
    with open(NOAUTH_FILE) as f:
        for file_path in f:
            file_path = file_path.strip()
            if not file_path or file_path.startswith('#'):
                continue
            type_file = file_path
            if not os.path.isabs(type_file):
                type_file = os.path.join(ROOT, type_file)
            constant = extract_type_name(type_file)
            if not constant:
                continue
            usages = []
            for line in grep_usages(constant, file_path):
                match = re.match(r'([^:]+):(\d+):(.*)', line)
                if not match:
                    continue
                other_file, ln, text = match.groups()
                ln = int(ln)
                field_name = extract_field_name(text)
                if not field_name:
                    continue
                if field_has_authorize(other_file, ln):
                    continue
                other_constant = extract_type_name(other_file)
                usages.append({
                    'file': os.path.relpath(other_file, ROOT),
                    'type': other_constant,
                    'field': field_name,
                    'line': ln
                })
            if usages:
                result[constant] = {
                    'file': file_path,
                    'usages': usages
                }
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
