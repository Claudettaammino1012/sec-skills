#!/usr/bin/env python3
"""
bash-obfuscation: Bash command obfuscation for defensive testing
Based on Bashfuscator by capnspacehook (https://github.com/Bashfuscator/Bashfuscator)

This module provides various techniques to obfuscate Bash commands for
defensive security testing and detection rule development.
"""

import base64
import bz2
import gzip
import hashlib
import random
import re
import string
import subprocess
import json
from typing import List, Dict, Optional

# ============================================================================
# CORE OBFUSCATION TECHNIQUES
# ============================================================================

def technique_base64(cmd: str, level: int = 2) -> str:
    """
    Base64 encode the command and decode at runtime.
    Example: echo "a被害" | base64 -d | bash
    """
    encoded = base64.b64encode(cmd.encode('utf-8')).decode('utf-8').replace('\n', '')

    if level == 1:
        return f'echo "{encoded}" | base64 -d | bash'
    elif level == 2:
        return f'${{{{ printf "{encoded}" | base64 -d | bash; }}}}'
    else:
        # More obfuscated version
        var = _random_var(4)
        return f'{var}=${{{{ printf "{encoded}" | base64 -d | bash; }}}};${{{var}}}'

def technique_gzip(cmd: str, level: int = 2) -> str:
    """
    Compress command with gzip and decode at runtime.
    Example: printf "\x1f\x8b..." | base64 -d | gunzip -c | bash
    """
    compressed = gzip.compress(cmd.encode('utf-8'))
    encoded = base64.b64encode(compressed).decode('utf-8')

    return f'printf "{encoded}" | base64 -d | gunzip -c | bash'

def technique_bzip2(cmd: str, level: int = 2) -> str:
    """
    Compress command with bzip2 and decode at runtime.
    """
    compressed = bz2.compress(cmd.encode('utf-8'))
    encoded = base64.b64encode(compressed).decode('utf-8')

    return f'printf "{encoded}" | base64 -d | bunzip2 -c | bash'

def technique_hex(cmd: str, level: int = 2) -> str:
    """
    Encode command as hex and decode at runtime.
    Example: echo -e "\x65\x63\x68\x6f" | bash
    """
    hex_str = cmd.encode('utf-8').hex()

    if level == 1:
        return f'echo -e "{hex_str}" | xxd -r -p | bash'
    elif level == 2:
        return f'${{{{ echo -e "{hex_str}" | xxd -r -p | bash; }}}}'
    else:
        # Using printf instead of echo -e
        hex_pairs = [hex_str[i:i+2] for i in range(0, len(hex_str), 2)]
        hex_str_formatted = '\\x' + '\\x'.join(hex_pairs)
        return f'printf "{hex_str_formatted}" | bash'

def technique_reverse(cmd: str, level: int = 2) -> str:
    """
    Reverse command and use 'rev' to reconstruct at runtime.
    """
    reversed_cmd = cmd[::-1]

    if level == 1:
        return f'printf "{reversed_cmd}" | rev | bash'
    else:
        var = _random_var(4)
        return f'{var}=$(printf "{reversed_cmd}" | rev);${{{var}}} | bash'

def technique_case_swap(cmd: str, level: int = 2) -> str:
    """
    Swap case of command using Bash parameter expansion.
    Example: ${VAR~~} converts to uppercase
    """
    swapped = cmd.swapcase()

    if level == 1:
        return f'eval "$(printf "{swapped}")"'
    else:
        var = _random_var(4)
        return f'{var}="$(printf "{swapped}")"; eval "${{{var}}}"'

def technique_for_code(cmd: str, level: int = 2) -> str:
    """
    Shuffle command characters and reassemble in a FOR loop.
    Based on Bashfuscator's ForCode mutator.
    """
    chars = list(set(cmd))
    random.shuffle(chars)
    shuffled = ''.join(chars)

    # Build index mapping
    indices = [str(chars.index(c)) for c in cmd]
    index_str = ' '.join(indices)

    char_array = ' '.join([f'${{{_random_var(3)}[{i}]}}' for i in range(len(chars))])

    if level == 1:
        arr_var = _random_var(4)
        idx_var = _random_var(4)
        return f'{arr_var}=({shuffled}); for {idx_var} in {index_str}; do printf "${{{arr_var}[${idx_var}]}}"; done | bash'
    else:
        arr_var = _random_var(4)
        idx_var = _random_var(4)
        result_var = _random_var(4)
        return f'{arr_var}=({shuffled}); {result_var}=; for {idx_var} in {index_str}; do {result_var}=${{{result_var}}}${{{arr_var}[${idx_var}]}}; done; ${{{result_var}}} | bash'

def technique_special_char(cmd: str, level: int = 2) -> str:
    """
    Convert command to use only special characters.
    Uses bash arithmetic and error messages to generate characters.
    This is a simplified version - full implementation is very complex.
    """
    # Use $'...' syntax with hex escapes for characters
    hex_str = ''.join(f'\\x{ord(c):02x}' for c in cmd)

    if level == 1:
        return f'bash -c ${{{hex_str}}}'
    elif level == 2:
        var = _random_var(4)
        return f'{var}=${{{hex_str}}}; bash -c "${{{var}}}"'
    else:
        var1 = _random_var(4)
        var2 = _random_var(4)
        return f'{var1}=${{{hex_str}}}; {var2}=$(eval "${{{var1}}}"); bash -c "${{{var2}}}"'

def technique_rot13(cmd: str, level: int = 2) -> str:
    """
    ROT13 encoding - each letter replaced with one 13 positions later.
    Uses tr command for decoding.
    """
    def rot13_char(c):
        if c.isalpha():
            base = ord('a') if c.islower() else ord('A')
            return chr((ord(c) - base + 13) % 26 + base)
        return c

    encoded = ''.join(rot13_char(c) for c in cmd)

    if level == 1:
        return f'echo "{encoded}" | tr "a-zA-Z" "n-za-mN-ZA-M" | bash'
    else:
        var = _random_var(4)
        return f'{var}=$(echo "{encoded}" | tr "a-zA-Z" "n-za-mN-ZA-M"); bash -c "${{{var}}}"'

def technique_xor(cmd: str, level: int = 2) -> str:
    """
    XOR encode command with a key, decode using Python/Perl.
    Simplified version using base64 XOR.
    """
    key = _random_var(8)

    # XOR each character with key byte
    cmd_bytes = cmd.encode('utf-8')
    key_bytes = key.encode('utf-8')
    xor_bytes = bytes([cmd_bytes[i] ^ key_bytes[i % len(key_bytes)] for i in range(len(cmd_bytes))])
    encoded = base64.b64encode(xor_bytes).decode('utf-8')

    if level == 1:
        return f'python3 -c "import sys,base64;print(__import__("os").popen({{}}).read())" "$(echo {encoded} | base64 -d | xxd -p | tr -d "\\n")"'
    else:
        var1 = _random_var(4)
        var2 = _random_var(4)
        return f'{var1}="{encoded}"; {var2}="$(echo "${var1}" | base64 -d | xxd -p | tr -d "\\n")"; python3 -c "import sys;exec(bytes.fromhex(\"${{{var2}}}\").decode())"'

def technique_env_subst(cmd: str, level: int = 2) -> str:
    """
    Use environment variable substitution patterns.
    Example: ${PATH} ${HOME} etc.
    """
    # Simple version - just use variable expansion
    if level == 1:
        return f'eval "$(echo "{cmd}" | sed "s/\\$/\\\\$/g")"'
    else:
        var = _random_var(4)
        return f'{var}="$(echo {cmd})"; eval "${{{var}}}"'

def technique_whitespace(cmd: str, level: int = 2) -> str:
    """
    Add random whitespace and comments to obfuscate.
    """
    result = []
    for i, char in enumerate(cmd):
        result.append(char)
        if random.random() > 0.7 and char not in ' \t\n':
            result.append(random.choice([' ', '\t']))

    obfuscated = ''.join(result)

    if level == 1:
        return f'eval "$(printf "{obfuscated}")"'
    else:
        # Add comment noise
        comment = f'# {_random_string(10)}\n'
        return f'{comment}eval "$(printf "{obfuscated}")"'

def technique_quote(cmd: str, level: int = 2) -> str:
    """
    Wrap command in various quote styles.
    """
    if level == 1:
        return f"bash -c '{cmd}'"
    elif level == 2:
        return f'bash -c "{cmd}"'
    else:
        var = _random_var(4)
        cmd_escaped = cmd.replace("'", "'\"'\"'")
        return f"{var}='{cmd_escaped}'; bash -c \"${{{var}}}\""

def technique_pipe(cmd: str, level: int = 2) -> str:
    """
    Add dummy pipe stages to obfuscate command flow.
    """
    dummy_cmds = ['true', 'cat', ':', 'echo', 'printf ""']
    dummy = random.choice(dummy_cmds)

    if level == 1:
        return f'{cmd} | {dummy}'
    elif level == 2:
        return f'{cmd} | {dummy} | {dummy}'
    else:
        return f'{cmd} | {dummy} | {dummy} | {dummy}'

def technique_subshell(cmd: str, level: int = 2) -> str:
    """
    Execute in subshell with various syntax styles.
    """
    if level == 1:
        return f'( {cmd} )'
    elif level == 2:
        return f'${{{{ {cmd}; }}}}'
    else:
        var = _random_var(4)
        return f'({var}={cmd}; ${{{var}}})'

# ============================================================================
# DETECTION PATTERNS
# ============================================================================

DETECTION_PATTERNS = {
    'BASE64_PIPE': {
        'pattern': r'base64\s+(-d|--decode)\s*\|',
        'description': 'Base64 decode piped to command execution',
        'severity': 'medium'
    },
    'HEX_ENCODING': {
        'pattern': r'(\\x[0-9a-fA-F]{2}|0x[0-9a-fA-F]{2})',
        'description': 'Hex encoded strings',
        'severity': 'low'
    },
    'GZIP_DECOMPRESS': {
        'pattern': r'(gunzip|gzip\s+-d)\s*\|',
        'description': 'Gzip decompression',
        'severity': 'medium'
    },
    'BZIP_DECOMPRESS': {
        'pattern': r'(bunzip2|bzip2\s+-d)\s*\|',
        'description': 'Bzip2 decompression',
        'severity': 'medium'
    },
    'REV_COMMAND': {
        'pattern': r'\|\s*rev\s*\|',
        'description': 'Reverse command piped to execution',
        'severity': 'low'
    },
    'EVAL_EXECUTION': {
        'pattern': r'\beval\s+\$',
        'description': 'Eval execution of variable',
        'severity': 'medium'
    },
    'FOR_LOOP_SHELL': {
        'pattern': r'for\s+\w+\s+in\s+[^;]+;\s*do',
        'description': 'FOR loop in shell',
        'severity': 'low'
    },
    'SUBSHELL_EXEC': {
        'pattern': r'\$\{\{.*\}\}',
        'description': 'Double bracket subshell execution',
        'severity': 'low'
    },
    'BACKTICK_EXEC': {
        'pattern': r'`[^`]+`',
        'description': 'Backtick command substitution',
        'severity': 'low'
    },
    'DOLLAR_PAREN': {
        'pattern': r'\$\([^)]+\)',
        'description': 'Command substitution $(...)',
        'severity': 'low'
    },
    'XXD_HEXDUMP': {
        'pattern': r'xxd\s+-r\s*-p',
        'description': 'Hexdump reverse operation',
        'severity': 'low'
    },
    'TR_ROT13': {
        'pattern': r'tr\s+"\[a-z\]"\s+"\[n-za-m\]"',
        'description': 'ROT13 translation pattern',
        'severity': 'low'
    },
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _random_var(length: int = 4) -> str:
    """Generate random variable name."""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def _random_string(length: int = 10) -> str:
    """Generate random string."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# ============================================================================
# MAIN API
# ============================================================================

TECHNIQUES_MAP = {
    'base64': technique_base64,
    'gzip': technique_gzip,
    'bzip2': technique_bzip2,
    'hex': technique_hex,
    'reverse': technique_reverse,
    'case_swap': technique_case_swap,
    'for_code': technique_for_code,
    'special_char': technique_special_char,
    'rot13': technique_rot13,
    'xor': technique_xor,
    'env_subst': technique_env_subst,
    'whitespace': technique_whitespace,
    'quote': technique_quote,
    'pipe': technique_pipe,
    'subshell': technique_subshell,
}

def list_techniques() -> List[str]:
    """List all available obfuscation techniques."""
    return list(TECHNIQUES_MAP.keys())

def obfuscate(
    command: str,
    technique: str = 'all',
    level: int = 2
) -> List[Dict[str, str]]:
    """
    Obfuscate a Bash command.

    Args:
        command: The Bash command to obfuscate
        technique: Technique name or 'all'
        level: Obfuscation level 1-3

    Returns:
        List of dicts with 'technique' and 'command' keys
    """
    results = []

    if technique == 'all':
        for name, func in TECHNIQUES_MAP.items():
            try:
                result = func(command, level)
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
        if technique in TECHNIQUES_MAP:
            try:
                result = TECHNIQUES_MAP[technique](command, level)
                results.append({
                    'technique': technique,
                    'command': result
                })
            except Exception as e:
                results.append({
                    'technique': technique,
                    'command': f'ERROR: {str(e)}'
                })
        else:
            return [{'error': f'Unknown technique: {technique}'}]

    return results

def detect(command: str) -> List[Dict[str, str]]:
    """
    Check if a command matches known detection patterns.

    Args:
        command: The command to check

    Returns:
        List of matched patterns with severity
    """
    results = []
    for name, info in DETECTION_PATTERNS.items():
        match = re.search(info['pattern'], command, re.IGNORECASE)
        if match:
            results.append({
                'pattern': name,
                'description': info['description'],
                'severity': info['severity'],
                'match': match.group()
            })
    return results

def test_cmd(original: str, obfuscated: str) -> Dict:
    """
    Test if obfuscated command produces same output as original.
    Note: Only works on Unix-like systems with bash available.
    """
    try:
        # Execute original
        orig_result = subprocess.run(
            f'bash -c {repr(original)}',
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )

        # Execute obfuscated
        obf_result = subprocess.run(
            f'bash -c {repr(obfuscated)}',
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
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

# ============================================================================
# CLI
# ============================================================================

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: bash_obfuscation.py <command> [options]")
        print("Options: --technique <name|all> --level <1-3> --detect --list")
        print("\nTechniques:", ', '.join(TECHNIQUES_MAP.keys()))
        sys.exit(1)

    cmd = sys.argv[1]

    if '--detect' in sys.argv:
        results = detect(cmd)
        print(json.dumps(results, indent=2))
    elif '--list' in sys.argv:
        print(json.dumps(list_techniques(), indent=2))
    else:
        technique = 'all'
        level = 2

        if '--technique' in sys.argv:
            idx = sys.argv.index('--technique')
            if idx + 1 < len(sys.argv):
                technique = sys.argv[idx + 1]

        if '--level' in sys.argv:
            idx = sys.argv.index('--level')
            if idx + 1 < len(sys.argv):
                level = int(sys.argv[idx + 1])

        results = obfuscate(cmd, technique, level)
        print(json.dumps(results, indent=2))
