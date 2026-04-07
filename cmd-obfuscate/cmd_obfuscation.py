#!/usr/bin/env python3
"""
cmd-obfuscation: cmd.exe command obfuscation for defensive testing
Based on Invoke-DOSfuscation by Daniel Bohannon
"""

import random
import string
import re
import subprocess
import json
from typing import List, Tuple, Optional

# Windows environment variables useful for substring extraction
WINDOWS_ENV_VARS = {
    'PUBLIC': r'C:\Users\Public',
    'TEMP': r'C:\Users\Username\AppData\Local\Temp',
    'WINDIR': r'C:\Windows',
    'SYSTEMROOT': r'C:\Windows',
    'USERPROFILE': r'C:\Users\Username',
    'HOMEDRIVE': r'C:',
    'HOMEPATH': r'\Users\Username',
    'USERNAME': r'Username',
    'USERDOMAIN': r'DESKTOP',
    'COMPUTERNAME': r'DESKTOP',
    'SESSIONNAME': r'Console',
    'PROGRAMDATA': r'C:\ProgramData',
    'PROGRAMFILES': r'C:\Program Files',
    'PROGRAMFILES(X86)': r'C:\Program Files (x86)',
    'LOCALAPPDATA': r'C:\Users\Username\AppData\Local',
    'APPDATA': r'C:\Users\Username\AppData\Roaming',
    'ALLUSERSPROFILE': r'C:\ProgramData',
    'COMSPEC': r'C:\Windows\system32\cmd.exe',
    'PATHEXT': r'.COM;.EXE;.BAT;.CMD;.VBS;.VBE;.JS;.JSE;.WSF;.WSH;.MSC',
    'OS': r'Windows_NT',
    'PROCESSOR_ARCHITECTURE': r'AMD64',
    'NUMBER_OF_PROCESSORS': r'2',
    'SystemDrive': r'C:',
    'SystemRoot': r'C:\Windows',
}

def random_case(s: str) -> str:
    """Randomize case of each character."""
    return ''.join(c.upper() if random.random() > 0.5 else c.lower() for c in s)

def get_random_var_name(length: int = 4, use_special: bool = False) -> str:
    """Generate a random environment variable name."""
    if use_special:
        chars = string.ascii_letters + string.digits + '_'
    else:
        chars = string.ascii_uppercase + string.digits + '_'
    return ''.join(random.choice(chars) for _ in range(length))

def get_random_whitespace() -> str:
    """Generate random whitespace."""
    return ''.join(random.choice(' \t') for _ in range(random.randint(1, 3)))

def get_random_delimiter() -> str:
    """Generate random delimiter character."""
    return random.choice([',', ';', '(', ')'])

def caret_escape(s: str) -> str:
    """Add caret escapes before non-escapable cmd.exe characters."""
    non_escapable = set('^&<>()|"n%')
    result = []
    for c in s:
        if c not in non_escapable and not c.isalnum():
            result.append('^')
        result.append(c)
    return ''.join(result)

def technique_envvar(cmd: str, level: int = 2, random_case_flag: bool = False) -> str:
    """
    Environment variable substring encoding using %VAR:~start,len%.
    """
    result = []
    i = 0

    while i < len(cmd):
        char = cmd[i]
        found = False

        for var_name, var_content in WINDOWS_ENV_VARS.items():
            idx = var_content.find(char)
            if idx != -1:
                encode_percent = 50 if level < 3 else 100
                if random.random() * 100 < encode_percent or level == 3:
                    result.append(f'%{var_name}:~{idx},1%')
                    found = True
                    break
                else:
                    result.append(char)
                    found = True
                    break

        if not found:
            result.append(char)

        if result[-1].startswith('%') and random_case_flag:
            for var_name in WINDOWS_ENV_VARS:
                if var_name in result[-1]:
                    new_name = random_case(var_name) if random_case_flag else var_name
                    result[-1] = result[-1].replace(var_name, new_name)
                    break

        i += 1

    output = ''.join(result)

    if random_case_flag:
        parts = []
        for part in re.split(r'(%[^%]+%)', output):
            if part.startswith('%'):
                parts.append(part)
            else:
                parts.append(random_case(part))
        output = ''.join(parts)

    return f'cmd /C "{output}"'

def technique_concat(cmd: str, level: int = 2, random_case_flag: bool = False) -> str:
    """
    Concatenation via SET variables and CALL with delayed expansion.
    """
    chunk_size = max(2, len(cmd) // 4)
    chunks = [cmd[i:i+chunk_size] for i in range(0, len(cmd), chunk_size)]

    set_stmts = []
    for chunk in chunks:
        var_name = get_random_var_name(4)
        set_stmts.append(f'set {var_name}={chunk}')

    call_parts = ''.join(f'%{get_random_var_name(4)}%' for _ in chunks)

    separator = '&&'
    if random_case_flag:
        separator = random_case(separator)

    set_cmd = separator.join(set_stmts)
    call_cmd = f'call {call_parts}'

    cmd_inner = f'{set_cmd}&&{call_cmd}'

    if random_case_flag:
        cmd_inner = random_case(cmd_inner)

    return f'cmd /V:ON /C "{cmd_inner}"'

def technique_reverse(cmd: str, level: int = 2, random_case_flag: bool = False) -> str:
    """
    String reversal with FOR /L loop reassembly.
    """
    reversed_cmd = cmd[::-1]
    cmd_len = len(cmd)

    var_name = get_random_var_name(4)
    var_display = get_random_var_name(3)

    for_loop = f'FOR /L %{var_name} in ({cmd_len},-1,0) DO'

    if random_case_flag:
        for_loop = random_case(for_loop)

    set_stmt = f'set {var_display}={reversed_cmd}'

    acc_var = get_random_var_name(4)

    loop_body = []
    for i in range(cmd_len - 1, -1, -1):
        loop_body.append(f'set {acc_var}=!{acc_var}!!{var_display}:~{i},1!')

    loop_body.append(f'if %{var_name} equ 0 call %{acc_var}:~-{cmd_len}%')

    loop_body_str = '&&'.join(loop_body)

    full_cmd = f'set {var_display}={reversed_cmd}&&{for_loop} {loop_body_str}'

    if random_case_flag:
        full_cmd = random_case(full_cmd)

    return f'cmd /V:ON /C "{full_cmd}"'

def technique_for(cmd: str, level: int = 2, random_case_flag: bool = False) -> str:
    """
    FOR loop index-based character extraction.
    """
    cmd_len = len(cmd)
    indices = list(range(cmd_len))
    random.shuffle(indices)
    max_idx = max(indices)

    var_content = get_random_var_name(4)
    var_result = get_random_var_name(4)

    indices_str = ' '.join(str(i) for i in indices)
    for_loop = f'FOR %i in ({indices_str}) DO'

    if random_case_flag:
        for_loop = random_case(for_loop)

    extract = f'set {var_result}=!{var_result}!!{var_content}:~%i,1!'
    check = f'if %i geq {max_idx} call %{var_result}%'

    set_stmt = f'set {var_content}={cmd}'
    body = f'{extract}&&{check}'

    full_cmd = f'{set_stmt}&&{for_loop} {body}'

    if random_case_flag:
        full_cmd = random_case(full_cmd)

    return f'cmd /V:ON /C "{full_cmd}"'

def technique_fin(cmd: str, level: int = 2, random_case_flag: bool = False) -> str:
    """
    Sequential substitution via %VAR:old=new%.
    """
    garbage = 'a' * len(cmd)
    var_name = get_random_var_name(4)

    set_stmt = f'set {var_name}={garbage}'

    current = garbage
    substitutions = []

    for i, target_char in enumerate(cmd):
        if current[i] != target_char:
            substitutions.append(f'%{var_name}:{current[i]}={target_char}')
            current = current[:i] + target_char + current[i+1:]

    sub_chain = '&&'.join(substitutions)

    full_cmd = f'{set_stmt}&&{sub_chain}'

    if random_case_flag:
        full_cmd = random_case(full_cmd)

    return f'cmd /V:ON /C "{full_cmd}"'

# ============================================================================
# FILLING/INJECTION TECHNIQUES (from ConradSun blog)
# ============================================================================

def technique_quote_injection(cmd: str, level: int = 2, random_case_flag: bool = False) -> str:
    """
    Insert double quotes into command (CMD ignores them).
    Example: net u"ser -> net user
    """
    result = []
    for c in cmd:
        result.append(c)
        if c.isalpha() and random.random() < 0.3 * level / 3:
            result.append('"')
    return ''.join(result)

def technique_escape_injection(cmd: str, level: int = 2, random_case_flag: bool = False) -> str:
    """
    Insert caret escape characters (CMD only, doesn't affect collection).
    Example: net u^s^e^r
    """
    result = []
    for c in cmd:
        if c.isalpha() and random.random() < 0.3 * level / 3:
            result.append('^')
        result.append(c)
    return ''.join(result)

def technique_space_injection(cmd: str, level: int = 2, random_case_flag: bool = False) -> str:
    """
    Insert spaces into command.
    Example: net         user
    """
    result = []
    for c in cmd:
        result.append(c)
        if random.random() < 0.2 * level / 3:
            result.append(' ' * random.randint(1, 5))
    return ''.join(result)

def technique_comma_injection(cmd: str, level: int = 2, random_case_flag: bool = False) -> str:
    """
    Insert comma/semicolon as delimiter.
    Example: cmd /c ",;netstat -ano"
    """
    if not cmd.startswith('cmd '):
        cmd = 'cmd /c ' + cmd
    return cmd.replace('cmd /c ', 'cmd /c ",;', 1).replace(' ', ',;', 1) if random.random() > 0.5 else cmd

def technique_unicode_injection(cmd: str, level: int = 2, random_case_flag: bool = False) -> str:
    """
    Insert Unicode/invisible characters.
    Example: reg e჊⮱⑐xჇ୊p⹶Ԥ⿾ort
    """
    # Greek and special Unicode chars that look similar
    unicode_chars = ['჊', '⮱', '⑐', 'Ⴧ', '୊', '⹶', 'Ԥ', '⿾', '⿿', '⁯', '‧', 'ㅤ']
    result = []
    for c in cmd:
        result.append(c)
        if c.isalpha() and random.random() < 0.2 * level / 3:
            result.append(random.choice(unicode_chars))
    return ''.join(result)

def technique_path_traversal(cmd: str, level: int = 2, random_case_flag: bool = False) -> str:
    r"""
    Insert path traversal sequences to hide real paths.
    Example: mshta C:\Users\..\debug\..//sunkang\test.hta
    """
    traversals = ['\\..\\', '\\.\\', '/../', '/./']
    # Only applies to commands with file paths
    result = cmd
    if any(x in cmd.lower() for x in ['hta', 'exe', 'bat', 'cmd', 'ps1', 'c:\\', 'c:/']):
        for _ in range(level):
            if random.random() > 0.5:
                traversals_used = random.choice(traversals)
                # Find a good position to insert
                if '\\\\' in result:
                    result = result.replace('\\\\', traversals_used, 1)
                elif ':\\' in result:
                    idx = result.index(':\\') + 3
                    result = result[:idx] + traversals_used + result[idx:]
    return result

def technique_string_concatenation(cmd: str, level: int = 2, random_case_flag: bool = False) -> str:
    """
    Split strings using concatenation (for PowerShell).
    Example: curl ('http://' + 'example.com')
    """
    # Find a good string to split
    if "'" in cmd or '"' in cmd:
        return cmd  # Already has quotes
    # Wrap in PowerShell-style concatenation
    return cmd  # Simplified - full implementation would parse and split strings

def technique_option_replace(cmd: str, level: int = 2, random_case_flag: bool = False) -> str:
    """
    Replace option prefixes: / with - or vice versa.
    Example: taskkill -f -im -> taskkill /f /im
    """
    result = cmd
    # Replace - with / or / with -
    if '-/' in cmd:
        result = cmd.replace('-/', '/', random.randint(1, level))
    elif '/-' in cmd:
        result = cmd.replace('/-', '-', random.randint(1, level))
    return result

def technique_case_variation(cmd: str, level: int = 2, random_case_flag: bool = False) -> str:
    """
    Randomize case of command (Windows case-insensitive).
    Example: Net UseR
    """
    return random_case(cmd) if random_case_flag or level >= 2 else cmd

def technique_ip_numerical(cmd: str, level: int = 2, random_case_flag: bool = False) -> str:
    """
    Convert IP addresses to decimal/hex.
    Example: ping 127.0.0.1 -> ping 2130706433
    """
    import ipaddress
    result = cmd
    # Find IP addresses and convert
    ip_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    ips = re.findall(ip_pattern, result)
    for ip in ips:
        try:
            num = int(ipaddress.IPv4Address(ip))
            result = result.replace(ip, str(num))
        except:
            pass
    return result

def technique_envvar_replace(cmd: str, level: int = 2, random_case_flag: bool = False) -> str:
    """
    Replace commands with environment variables (doesn't affect collection).
    Example: %COMSPEC% /c echo Hello
    """
    env_replacements = {
        'cmd': '%COMSPEC%',
        'calc': '%WINDIR%\\System32\\calc.exe',
        'notepad': '%WINDIR%\\System32\\notepad.exe',
    }
    result = cmd
    for cmd_name, env_var in env_replacements.items():
        if cmd_name in result.lower():
            # Replace at word boundary
            pattern = re.compile(re.escape(cmd_name), re.IGNORECASE)
            result = pattern.sub(env_var, result, 1)
            break
    return result

def technique_abbreviation(cmd: str, level: int = 2, random_case_flag: bool = False) -> str:
    """
    Shorten command arguments.
    Example: cmdkey /l -> cmdkey /list
    """
    abbreviations = {
        '/list': '/l',
        '/delete': '/d',
        '/password': '/p',
        '/user': '/u',
    }
    result = cmd
    for full, short in abbreviations.items():
        if full in result.lower():
            result = re.sub(re.escape(full), short, result, flags=re.IGNORECASE)
            break
    return result

# ============================================================================
# DETECTION
# ============================================================================

DETECTION_PATTERNS = {
    'FOR_LOOP': {
        'pattern': r'FOR\s+\/[A-Z]\s+\%[A-Z]\s+IN',
        'description': 'Unobfuscated FOR loop pattern',
        'severity': 'medium'
    },
    'MULTI_SUBSTRING': {
        'pattern': r'\%.{0,25}:~.{0,25}\%.*\%.{0,25}:~.{0,25}\%',
        'description': 'Multiple environment variable substrings',
        'severity': 'low'
    },
    'CONCAT_SET': {
        'pattern': r'\bset\s+[A-Z_][A-Z0-9_]*=.+&&\bset\s+',
        'description': 'SET concatenation pattern (common obfuscation)',
        'severity': 'medium'
    },
    'REVERSAL': {
        'pattern': r'FOR /L.*in\s+\([0-9]+,-1,',
        'description': 'FOR /L reversal pattern',
        'severity': 'high'
    },
    'CARET_ACCUM': {
        'pattern': r'\^+',
        'description': 'Excessive caret accumulation',
        'severity': 'medium'
    },
    'DELAYED_EXP': {
        'pattern': r'\/V:ON',
        'description': 'Delayed variable expansion enabled',
        'severity': 'low'
    },
    'WHITESPACE_NOISE': {
        'pattern': r'[ \t]{4,}',
        'description': 'Excessive whitespace (potential obfuscation)',
        'severity': 'low'
    },
    # From ConradSun blog - additional patterns
    'UNICODE_INJECTION': {
        'pattern': r'[\u1000-\uFFFF]+',
        'description': 'Unicode character injection',
        'severity': 'low'
    },
    'ENVVAR_REPLACE': {
        'pattern': r'%[A-Z_]+%',
        'description': 'Environment variable reference',
        'severity': 'low'
    },
    'QUOTE_INJECTION': {
        'pattern': r'[a-z]"[a-z]',
        'description': 'Quote injection pattern',
        'severity': 'low'
    },
    'CARE T_ESCAPE': {
        'pattern': r'\^[a-z]',
        'description': 'Caret escape before letter',
        'severity': 'low'
    },
    'IP_NUMERICAL': {
        'pattern': r'\b\d{7,10}\b',
        'description': 'Numerical IP address (decimal)',
        'severity': 'medium'
    },
    'PATH_TRAVERSAL': {
        'pattern': r'(\\\.\.|/\./|\\\\\.\.)',
        'description': 'Path traversal sequence',
        'severity': 'medium'
    },
}

def detect(cmd: str) -> List[dict]:
    """
    Check if a command matches known detection patterns.
    """
    results = []
    for name, info in DETECTION_PATTERNS.items():
        if re.search(info['pattern'], cmd, re.IGNORECASE):
            match = re.search(info['pattern'], cmd, re.IGNORECASE)
            results.append({
                'pattern': name,
                'description': info['description'],
                'severity': info['severity'],
                'match': match.group() if match else ''
            })
    return results

# ============================================================================
# MAIN
# ============================================================================

def obfuscate(
    command: str,
    technique: str = 'all',
    level: int = 2,
    random_case_flag: bool = False,
    random_caret: bool = False,
    random_space: bool = False
) -> List[dict]:
    """
    Main obfuscation function.
    """
    results = []

    techniques_map = {
        'envvar': technique_envvar,
        'concat': technique_concat,
        'reverse': technique_reverse,
        'for': technique_for,
        'fin': technique_fin,
        # Filling techniques (from ConradSun blog)
        'quote': technique_quote_injection,
        'escape': technique_escape_injection,
        'space': technique_space_injection,
        'comma': technique_comma_injection,
        'unicode': technique_unicode_injection,
        'path': technique_path_traversal,
        'option': technique_option_replace,
        'case': technique_case_variation,
        'ip': technique_ip_numerical,
        'env': technique_envvar_replace,
        'abbr': technique_abbreviation,
    }

    if technique == 'all':
        for name, func in techniques_map.items():
            try:
                result = func(command, level, random_case_flag)
                results.append({
                    'technique': name,
                    'command': result
                })
            except Exception as e:
                results.append({
                    'technique': name,
                    'command': f'ERROR: {str(e)}'
                })
    else:
        if technique in techniques_map:
            result = techniques_map[technique](command, level, random_case_flag)
            results.append({
                'technique': technique,
                'command': result
            })
        else:
            return [{'error': f'Unknown technique: {technique}'}]

    for r in results:
        if random_space and 'command' in r and not r['command'].startswith('ERROR'):
            if r['command'].startswith('cmd '):
                r['command'] = r['command'].replace('cmd ', 'cmd  ', 1)

    return results

def test_cmd(original: str, obfuscated: str) -> dict:
    """
    Execute both commands and compare outputs.
    """
    try:
        orig_result = subprocess.run(
            original, shell=True, capture_output=True, text=True, timeout=10
        )
        obf_result = subprocess.run(
            obfuscated, shell=True, capture_output=True, text=True, timeout=10
        )
        return {
            'original_output': orig_result.stdout.strip(),
            'obfuscated_output': obf_result.stdout.strip(),
            'match': orig_result.stdout.strip() == obf_result.stdout.strip(),
            'original_rc': orig_result.returncode,
            'obfuscated_rc': obf_result.returncode
        }
    except Exception as e:
        return {
            'error': str(e),
            'original_output': None,
            'obfuscated_output': None,
            'match': False
        }

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: cmd_obfuscation.py <command> [options]")
        print("Options: --technique <name> --level <1-3> --random-case --detect")
        sys.exit(1)

    cmd = sys.argv[1]

    if '--detect' in sys.argv:
        results = detect(cmd)
        print(json.dumps(results, indent=2))
    else:
        technique = 'all'
        level = 2
        random_case_flag = '--random-case' in sys.argv

        if '--technique' in sys.argv:
            idx = sys.argv.index('--technique')
            if idx + 1 < len(sys.argv):
                technique = sys.argv[idx + 1]

        if '--level' in sys.argv:
            idx = sys.argv.index('--level')
            if idx + 1 < len(sys.argv):
                level = int(sys.argv[idx + 1])

        results = obfuscate(cmd, technique, level, random_case_flag)
        print(json.dumps(results, indent=2))
