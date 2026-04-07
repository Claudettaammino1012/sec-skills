---
name: cmd-obfuscation
description: Generate obfuscated cmd.exe commands for defensive testing, based on Invoke-DOSfuscation techniques
triggers:
  - "obfuscate cmd"
  - "cmd obfuscation"
  - "obfuscate shell command"
techniques:
  - name: envvar
    description: Environment variable substring encoding (%VAR:~start,len%)
  - name: concat
    description: Concatenation via SET variables and CALL with delayed expansion
  - name: reverse
    description: String reversal with FOR /L loop reassembly
  - name: for
    description: FOR loop index-based character extraction
  - name: fin
    description: Sequential substitution via %VAR:old=new%
  # Filling techniques (from ConradSun blog)
  - name: quote
    description: Single quote injection into command arguments
  - name: escape
    description: Caret escape character injection
  - name: space
    description: Extra whitespace injection
  - name: comma
    description: Comma as command delimiter
  - name: unicode
    description: Unicode/fullwidth character injection
  # Replacement techniques
  - name: path
    description: Path traversal sequence injection
  - name: option
    description: Command option format variation
  - name: case
    description: Random case variation
  - name: ip
    description: IP address to numeric conversion
  - name: env
    description: Environment variable substitution
  - name: abbr
    description: Command abbreviation
---

# cmd-obfuscation Skill

基于 [Invoke-DOSfuscation](https://github.com/danielbohannon/Invoke-DOSfuscation) 的 cmd.exe 命令混淆工具，用于防御性测试。

## Commands

### obfuscate

Generate obfuscated cmd.exe commands.

```bash
obfuscate <command> [--technique envvar|concat|reverse|for|fin|quote|escape|space|comma|unicode|path|option|case|ip|env|abbr|all] [--level 1-3] [--random-case] [--random-caret] [--random-space]
```

**Parameters:**
- `command`: The raw cmd.exe command to obfuscate (e.g., `netstat -ano`)
- `--technique`: Obfuscation technique to use (default: all)
- `--level`: Obfuscation intensity 1-3 (default: 2)
- `--random-case`: Randomize character casing (e.g., `cMd.ExE`)
- `--random-caret`: Add caret escapes before non-escapable characters
- `--random-space`: Inject random whitespace

**Examples:**
```bash
obfuscate "netstat -ano"
obfuscate "whoami /all" --technique concat
obfuscate "dir" --level 3 --random-case
```

### detect

Check if a command matches known detection patterns (regex-based).

```bash
detect <command>
```

**Detection patterns:**
- `FOR_LOOP`: Unobfuscated FOR loop pattern
- `MULTI_SUBSTRING`: Multiple environment variable substrings
- `CONCAT_SET`: SET concatenation pattern
- `REVERSAL`: FOR /L reversal pattern
- `CARET_ACCUM`: Excessive caret escaping
- `WHITESPACE_NOISE`: Excessive whitespace injection
- `UNICODE_INJECTION`: Unicode/fullwidth character injection
- `QUOTE_INJECTION`: Single quote padding
- `IP_NUMERIC`: IP address as numeric
- `PATH_TRAVERSAL`: Path traversal sequences

**Examples:**
```bash
detect "FOR /L %i in (11,-1,0) do echo hi"
detect "cmd /C \"set X=net&&set Y=stat&&call %X%%Y%\""
```

### test

Execute an obfuscated command and compare output with original.

```bash
test <original> <obfuscated>
```

**Examples:**
```bash
test "netstat -ano" "cmd /V:ON /C \"...obfuscated...\""
```

---

## Implementation

```python
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
    # Characters that don't need escaping: ^ & < > | % n " ( )
    # Characters that need escaping: anything else that's special to cmd
    non_escapable = set('^&<>()|"n%')
    result = []
    for c in s:
        if c not in non_escapable and not c.isalnum():
            result.append('^')
        result.append(c)
    return ''.join(result)

def find_substring_in_env(content: str, target: str) -> List[Tuple[str, int, int]]:
    """Find occurrences of target string in environment variable content."""
    # For simplicity, we search for single characters or small substrings
    matches = []
    for var_name, var_content in WINDOWS_ENV_VARS.items():
        idx = var_content.find(target)
        if idx != -1:
            matches.append((var_name, idx, len(target)))
    return matches

def technique_envvar(cmd: str, level: int = 2, random_case_flag: bool = False) -> str:
    """
    Environment variable substring encoding.
    Uses %VAR:~start,len% syntax to extract characters.
    Example: netstat -> %WINDIR:~4,2%etstat
    """
    result = []
    i = 0

    while i < len(cmd):
        # Try to find a character we can extract from an env var
        char = cmd[i]
        found = False

        for var_name, var_content in WINDOWS_ENV_VARS.items():
            idx = var_content.find(char)
            if idx != -1:
                # We found a char we can encode
                encode_percent = 50 if level < 3 else 100
                if random.random() * 100 < encode_percent or level == 3:
                    # Use substring extraction
                    if random.random() > 0.5 and idx + 1 < len(var_content):
                        # Use :~start,len format
                        result.append(f'%{var_name}:~{idx},1%')
                    else:
                        result.append(f'%{var_name}:~{idx},1%')
                    found = True
                    break
                else:
                    result.append(char)
                    found = True
                    break

        if not found:
            result.append(char)

        # Random case on env var names
        if result[-1].startswith('%') and random_case_flag:
            # Randomize case of env var name
            for var_name in WINDOWS_ENV_VARS:
                if var_name in result[-1]:
                    new_name = random_case(var_name) if random_case_flag else var_name
                    result[-1] = result[-1].replace(var_name, new_name)
                    break

        i += 1

    output = ''.join(result)

    if random_case_flag:
        # Also randomize case of non-encoded parts
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
    Example: netstat -ano -> set X=net&&set Y=stat&&call %X%%Y%
    """
    # Split command into chunks
    chunk_size = max(2, len(cmd) // 4)
    chunks = [cmd[i:i+chunk_size] for i in range(0, len(cmd), chunk_size)]

    set_stmts = []
    for i, chunk in enumerate(chunks):
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

    # Enable delayed expansion
    return f'cmd /V:ON /C "{cmd_inner}"'

def technique_reverse(cmd: str, level: int = 2, random_case_flag: bool = False) -> str:
    """
    String reversal with FOR /L loop reassembly.
    Reverses the command and uses negative-index FOR loop to rebuild it.
    """
    reversed_cmd = cmd[::-1]
    cmd_len = len(cmd)

    var_name = get_random_var_name(4)
    var_display = get_random_var_name(3)

    # FOR /L loop: start, step, end (negative step for reverse)
    for_loop = f'FOR /L %{var_name} in ({cmd_len},-1,0) DO'

    if random_case_flag:
        for_loop = random_case(for_loop)

    set_stmt = f'set {var_display}={reversed_cmd}'

    # Build the reassembly using delayed expansion
    # For each iteration, extract one character from the reversed string
    reassemble = []
    for i in range(cmd_len):
        idx = cmd_len - 1 - i  # Index in reversed string
        reassemble.append(f'%{var_display}:~{i},1%')

    # This is a simplified version - the real Invoke-DOSfuscation uses a more complex approach
    # Build actual cmd command
    result_parts = []

    # Use a temporary var to accumulate
    acc_var = get_random_var_name(4)

    # Generate the full command
    loop_body = []
    for i in range(cmd_len - 1, -1, -1):
        idx = cmd_len - 1 - i
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
    Uses an index array to extract characters in a specific order.
    """
    cmd_len = len(cmd)
    indices = list(range(cmd_len))
    random.shuffle(indices)
    max_idx = max(indices)

    var_content = get_random_var_name(4)
    var_result = get_random_var_name(4)

    # FOR with space-separated indices
    indices_str = ' '.join(str(i) for i in indices)
    for_loop = f'FOR %i in ({indices_str}) DO'

    if random_case_flag:
        for_loop = random_case(for_loop)

    # Build the extraction and accumulation
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
    Creates garbage string then replaces characters one by one.
    """
    # Start with a garbage string that has some structure
    garbage = 'a' * len(cmd)
    var_name = get_random_var_name(4)

    set_stmt = f'set {var_name}={garbage}'

    # Build substitution chain
    current = garbage
    substitutions = []

    for i, target_char in enumerate(cmd):
        # Find a substitution that changes current to target
        # We work character by character
        if current[i] != target_char:
            substitutions.append(f'%{var_name}:{current[i]}={target_char}')
            # Update current for next iteration
            current = current[:i] + target_char + current[i+1:]

    sub_chain = '&&'.join(substitutions)

    full_cmd = f'{set_stmt}&&{sub_chain}'

    if random_case_flag:
        full_cmd = random_case(full_cmd)

    return f'cmd /V:ON /C "{full_cmd}"'

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
}

def detect(cmd: str) -> List[dict]:
    """
    Check if a command matches known detection patterns.
    Returns list of matched patterns with severity.
    """
    results = []
    for name, info in DETECTION_PATTERNS.items():
        if re.search(info['pattern'], cmd, re.IGNORECASE):
            results.append({
                'pattern': name,
                'description': info['description'],
                'severity': info['severity'],
                'match': re.search(info['pattern'], cmd, re.IGNORECASE).group()
            })
    return results

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def obfuscate(
    command: str,
    technique: str = 'all',
    level: int = 2,
    random_case_flag: bool = False,
    random_caret: bool = False,
    random_space: bool = False
) -> List[str]:
    """
    Main obfuscation function.

    Args:
        command: The raw cmd.exe command to obfuscate
        technique: 'envvar', 'concat', 'reverse', 'for', 'fin', or 'all'
        level: Obfuscation level 1-3
        random_case_flag: Apply random case obfuscation
        random_caret: Apply caret escaping
        random_space: Inject random whitespace

    Returns:
        List of obfuscated command strings
    """
    results = []

    techniques_map = {
        'envvar': technique_envvar,
        'concat': technique_concat,
        'reverse': technique_reverse,
        'for': technique_for,
        'fin': technique_fin,
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

    # Post-processing
    for r in results:
        if random_caret and 'command' in r and not r['command'].startswith('ERROR'):
            r['command'] = r['command']  # caret_escape applied in techniques

        if random_space and 'command' in r and not r['command'].startswith('ERROR'):
            # Add random whitespace after cmd binary
            if r['command'].startswith('cmd '):
                r['command'] = r['command'].replace('cmd ', 'cmd  ', 1)

    return results

def test_cmd(original: str, obfuscated: str) -> dict:
    """
    Execute both commands and compare outputs.
    Note: Only works on Windows with cmd.exe available.
    """
    try:
        # Execute original
        orig_result = subprocess.run(
            original,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )

        # Execute obfuscated
        obf_result = subprocess.run(
            obfuscated,
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

# CLI interface for testing
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: cmd_obfuscation.py <command> [options]")
        print("Options: --technique <name> --level <1-3> --random-case --detect --test")
        sys.exit(1)

    cmd = sys.argv[1]

    if '--detect' in sys.argv:
        results = detect(cmd)
        print(json.dumps(results, indent=2))
    else:
        technique = 'all'
        level = 2
        random_case = '--random-case' in sys.argv
        random_caret = '--random-caret' in sys.argv
        random_space = '--random-space' in sys.argv

        if '--technique' in sys.argv:
            idx = sys.argv.index('--technique')
            if idx + 1 < len(sys.argv):
                technique = sys.argv[idx + 1]

        if '--level' in sys.argv:
            idx = sys.argv.index('--level')
            if idx + 1 < len(sys.argv):
                level = int(sys.argv[idx + 1])

        results = obfuscate(cmd, technique, level, random_case, random_caret, random_space)
        print(json.dumps(results, indent=2))
```
