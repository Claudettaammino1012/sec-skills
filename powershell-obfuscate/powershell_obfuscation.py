#!/usr/bin/env python3
"""
powershell-obfuscation: PowerShell obfuscation toolkit for defensive testing
Based on Invoke-Obfuscation by Daniel Bohannon (https://github.com/danielbohannon/Invoke-Obfuscation)
"""

import base64
import zlib
import random
import string
import json
import re
import os
from typing import List, Dict, Tuple, Optional

# ============================================================================
# ENCODING TECHNIQUES
# ============================================================================

def _get_random_delimiters(count: int = 1) -> List[str]:
    """Get random delimiter characters used in PowerShell encoding."""
    delimiters = list('_-,*.|+') + list(string.ascii_lowercase)
    return [random.choice(delimiters) for _ in range(count)]

def _random_case(s: str) -> str:
    """Randomize case of string."""
    return ''.join(c.upper() if random.random() > 0.5 else c.lower() for c in s)

def powershell_ascii_encoding(script: str, level: int = 2) -> str:
    """
    ASCII encoding: Converts each char to its integer representation.
    Pattern: ([String]([Int][Char]'$_') + delimiter)
    """
    chars = []
    for c in script:
        delim = _get_random_delimiters(1)[0] if level >= 2 else ','
        chars.append(f'[Int][Char]\'{c}\'{delim}[String]')
    join_char = _get_random_delimiters(1)[0] if level >= 2 else '+'
    encoded = join_char.join(chars)
    return f"$({encoded}) -join ''"

def powershell_hex_encoding(script: str, level: int = 2) -> str:
    """
    Hex encoding: Converts each char to hex string.
    Pattern: [Convert]::ToString(([Int][Char]'$_'), 16)
    """
    chars = []
    delim = _get_random_delimiters(1)[0] if level >= 2 else ','
    join_char = _get_random_delimiters(1)[0] if level >= 2 else '+'

    for c in script:
        hex_val = hex(ord(c))[2:]
        if level >= 3:
            hex_val = _random_case(hex_val)
        chars.append(f'[{hex_val}]')

    # Build decode command
    delim2 = _get_random_delimiters(1)[0] if level >= 2 else ','
    joined = delim2.join(chars)
    return f"$('{joined}' -split '.{{{len(delim2)}}}' | % {{ [Convert]::ToString([int]$_, 16) }} | % {{ [Char][Convert]::ToInt32($_, 16) }} -join '')"

def powershell_octal_encoding(script: str, level: int = 2) -> str:
    """
    Octal encoding: Converts each char to octal string.
    Pattern: [Convert]::ToString(([Int][Char]'$_'), 8)
    """
    chars = []
    for c in script:
        oct_val = oct(ord(c))[2:]
        if level >= 3:
            oct_val = _random_case(oct_val)
        chars.append(f'{oct_val}')

    delim = _get_random_delimiters(1)[0] if level >= 2 else ','
    joined = delim.join(chars)
    return f"$('{joined}' -split '.{{{len(delim)}}}' | % {{ [Convert]::ToString([int]$_, 8) }} | % {{ [Char][Convert]::ToInt32($_, 8) }} -join '')"

def powershell_binary_encoding(script: str, level: int = 2) -> str:
    """
    Binary encoding: Converts each char to binary string.
    Pattern: [Convert]::ToString(([Int][Char]'$_'), 2)
    """
    chars = []
    for c in script:
        bin_val = bin(ord(c))[2:]
        if level >= 3:
            bin_val = _random_case(bin_val)
        chars.append(f'{bin_val}')

    delim = _get_random_delimiters(1)[0] if level >= 2 else ','
    joined = delim.join(chars)
    return f"$('{joined}' -split '.{{{len(delim)}}}' | % {{ [Convert]::ToString([int]$_, 2) }} | % {{ [Char][Convert]::ToInt32($_, 2) }} -join '')"

def powershell_bxor_encoding(script: str, level: int = 2) -> str:
    """
    BXOR (Bitwise XOR) encoding: XORs each char with a random key.
    Pattern: ([Int][Char]'$_' -BXOR $Key)
    """
    # Generate random XOR key (0-255)
    key = random.randint(1, 255)
    key_hex = hex(key)

    chars = []
    for c in script:
        xored = ord(c) ^ key
        delim = _get_random_delimiters(1)[0] if level >= 2 else ','
        chars.append(f'[{xored}]')

    delim2 = _get_random_delimiters(1)[0] if level >= 2 else ','
    joined = delim2.join(chars)

    # Decode
    decode = f"({joined}) | % {{ [Char]($_ -BXOR {key_hex}) }} -join ''"
    return decode

def powershell_whitespace_encoding(script: str, level: int = 2) -> str:
    """
    Whitespace encoding: Encodes digits as tabs/spaces.
    Each digit N+1 is represented as N repetitions of tab or space.
    """
    delim_char = '\t' if level >= 2 else ' '

    encoded_parts = []
    for c in script:
        for digit in str(ord(c)):
            count = int(digit) + 1
            encoded_parts.append(delim_char * count)
        encoded_parts.append('\n' if level >= 2 else ' ')

    joined = ''.join(encoded_parts)
    # Build decoder - counts tabs/spaces and converts back
    return f"$('{joined.replace(chr(9), '\\t').replace(chr(10), '\\n')}' -split '[\\n\\r]' | % {{ $s='';$_.ToCharArray() | % {{ if($_){{$s+=[Char]($_.Value__) }};$s+=$_ }};$s }} | % {{ [Char][int]($_) }} -join '')"

def powershell_special_char_only(script: str, level: int = 2) -> str:
    """
    Special character only encoding: Replaces alphanumeric with special chars.
    Uses $host, $$env for variable construction.
    """
    # This is a simplified version - full implementation uses complex variable techniques
    result = []
    for c in script:
        if c.isalnum():
            # Convert to hex and reference via variable
            hex_val = hex(ord(c))[2:]
            if level >= 2:
                result.append(f'$host.version.Major')
            result.append(f'[Char]({hex_val})')
        else:
            result.append(f'{c}')
    return ''.join(result)

def powershell_compressed(script: str, level: int = 2) -> str:
    """
    Compression: DeflateStream + Base64 encoding.
    Original Invoke-Obfuscation uses this technique heavily.
    """
    # Compress the script using deflate
    compressed = zlib.compress(script.encode('utf-16-le'))
    b64 = base64.b64encode(compressed).decode()

    # Build decoder
    if level >= 3:
        cmdlets = _random_case(' '.join(['New-Object', 'System.IO.Compression.DeflateStream',
                                        'System.IO.MemoryStream', 'IO.Compression.CompressionMode',
                                        'ToBase64String', 'Get-Content', 'ReadAllText']))
    else:
        cmdlets = ' '.join(['New-Object', 'System.IO.Compression.DeflateStream',
                            'System.IO.MemoryStream', 'IO.Compression.CompressionMode',
                            'ToBase64String', 'Get-Content', 'ReadAllText'])

    # Simplified decoder
    return f"(-join [System.IO.Compression.DeflateStream]::new([System.IO.MemoryStream]::new([Convert]::FromBase64String('{b64}')), [System.IO.Compression.CompressionMode]::Decompress) | Get-Content)"

def powershell_string_obfuscation(script: str, level: int = 2) -> str:
    """
    String obfuscation: Breaks up strings using concatenation and variables.
    """
    # Split into chunks and reconstruct
    chunk_size = max(1, len(script) // 4)
    chunks = [script[i:i+chunk_size] for i in range(0, len(script), chunk_size)]

    var_names = [''.join(random.choices(string.ascii_lowercase, k=6)) for _ in chunks]

    assignments = []
    for var, chunk in zip(var_names, chunks):
        if level >= 3:
            var = _random_case(var)
        assignments.append(f'${var}=\'{chunk}\'')

    concat = '+'.join(f'${v}' for v in var_names)
    return '; '.join(assignments) + '; ' + concat

# ============================================================================
# LAUNCHER TECHNIQUES (from Out-PowerShellLauncher.ps1)
# ============================================================================

def launcher_ps(script: str, level: int = 2) -> str:
    """
    Direct PowerShell launcher.
    """
    encoded = base64.b64encode(script.encode('utf-16-le')).decode()
    return f'powershell -NoP -NonI -Enc {encoded}'

def launcher_cmd(script: str, level: int = 2) -> str:
    """
    CMD wrapper launcher.
    """
    encoded = base64.b64encode(script.encode('utf-16-le')).decode()
    return f'cmd /c powershell -NoP -NonI -Enc {encoded}'

def launcher_wmic(script: str, level: int = 2) -> str:
    """
    WMIC launcher: wmic process call create
    """
    encoded = base64.b64encode(script.encode('utf-16-le')).decode()
    return f'wmic process call create "powershell -NoP -NonI -Enc {encoded}"'

def launcher_rundll(script: str, level: int = 2) -> str:
    """
    RUNDLL32 launcher: Uses javascript: protocol.
    """
    encoded = base64.b64encode(script.encode('utf-16-le')).decode()
    return f'rundll32.exe javascript:"\\..\\mshtml,RunHTMLApplication";document.write();powershell -NoP -NonI -Enc {encoded}'

def launcher_var_push(script: str, level: int = 2) -> str:
    """
    VAR+ launcher: Pushes command to parent process via environment variable.
    """
    var_name = ''.join(random.choices(string.ascii_uppercase, k=6))
    encoded = base64.b64encode(script.encode('utf-16-le')).decode()
    set_cmd = f'set {var_name}={encoded}'
    ps_cmd = f'powershell -NoP -NonI -Enc %{var_name}%'
    return f'{set_cmd}&&{ps_cmd}'

def launcher_stdin_push(script: str, level: int = 2) -> str:
    """
    STDIN+ launcher: Pushes to parent via StandardInput.
    """
    encoded = base64.b64encode(script.encode('utf-16-le')).decode()
    return f'echo {encoded} | powershell -NoP -NonI'

def launcher_clip_push(script: str, level: int = 2) -> str:
    """
    CLIP+ launcher: Copies to clipboard for parent to execute.
    """
    encoded = base64.b64encode(script.encode('utf-16-le')).decode()
    set_clip = "powershell -NoP -NonI -Command \"Set-Clipboard -Value '" + encoded + "'\""
    ps_cmd = "powershell -NoP -NonI -Enc (Get-Clipboard)"
    return set_clip + "&&" + ps_cmd

def launcher_var_grandparent(script: str, level: int = 2) -> str:
    """
    VAR++ launcher: Pushes to grandparent process via environment variable.
    Similar to VAR+ but propagates further up the process tree.
    """
    var_name = ''.join(random.choices(string.ascii_uppercase, k=6))
    encoded = base64.b64encode(script.encode('utf-16-le')).decode()
    set_cmd = f'set {var_name}={encoded}'
    # Use START /B to create detached process
    ps_cmd = f'start /B /WAIT cmd /c set {var_name}&&powershell -NoP -NonI -Enc %{var_name}%'
    return f'{set_cmd}&&{ps_cmd}'

def launcher_mshta(script: str, level: int = 2) -> str:
    """
    MSHTA++ launcher: Uses mshta.exe with vbscript.
    """
    encoded = base64.b64encode(script.encode('utf-16-le')).decode()
    return f'mshta vbscript:Execute("Set sh=CreateObject(^"WScript.Shell^"):Set fs=CreateObject(^"Scripting.FileSystemObject^"):Set f=fs.GetStandardStream(1):f.WriteLine ^"powershell -NoP -NonI -Enc {encoded}^":sh.Run ^"cmd /c powershell -NoP -NonI -Enc {encoded}^",0"):Close()"):Execute("CreateObject(^"WScript.Shell^").Run ^"powershell -NoP -NonI -Enc {encoded}^",0"")'

# ============================================================================
# DETECTION PATTERNS
# ============================================================================

DETECTION_PATTERNS = {
    'BASE64_ENC': {
        'pattern': r'-Enc?\s+[A-Za-z0-9+/]{20,}={0,2}',
        'description': 'Base64 encoded PowerShell command (-Enc)',
        'severity': 'medium',
        'lang': 'powershell'
    },
    'INVOKE_EXPRESSION': {
        'pattern': r'(IEX|Invoke-Expression)\s*\(',
        'description': 'Dynamic code execution via IEX/Invoke-Expression',
        'severity': 'high',
        'lang': 'powershell'
    },
    'ENCODED_COMMAND': {
        'pattern': r'\[Convert\]::(ToString|FromBase64String|ToInt32)',
        'description': 'PowerShell encoding/decoding functions',
        'severity': 'medium',
        'lang': 'powershell'
    },
    'DEFLA TESTREAM': {
        'pattern': r'DeflateStream',
        'description': 'DeflateStream compression (common in obfuscated scripts)',
        'severity': 'medium',
        'lang': 'powershell'
    },
    'WMIC_LAUNCH': {
        'pattern': r'wmic\s+process\s+call\s+create',
        'description': 'WMIC process creation',
        'severity': 'high',
        'lang': 'batch'
    },
    'RUNDLL32_JS': {
        'pattern': r'rundll32.*javascript:',
        'description': 'RUNDLL32 with JavaScript protocol',
        'severity': 'high',
        'lang': 'batch'
    },
    'MSHTA_VBS': {
        'pattern': r'mshta\s+vbscript:',
        'description': 'MSHTA with VBScript',
        'severity': 'high',
        'lang': 'batch'
    },
    'SET_CLIPBOARD': {
        'pattern': r'(Set-Clipboard|Get-Clipboard)',
        'description': 'Clipboard manipulation',
        'severity': 'low',
        'lang': 'powershell'
    },
    'PROCESS_HOST': {
        'pattern': r'\$?(host|env|Profile)\.',
        'description': 'PowerShell host/environment variable access',
        'severity': 'low',
        'lang': 'powershell'
    },
    'OBFUSCATED_STRING': {
        'pattern': r'\$[a-zA-Z]{3,}\s*=\s*[\'"][^\'"]+[\'"]\s*;.*\+.*\$',
        'description': 'String concatenation with variables',
        'severity': 'low',
        'lang': 'powershell'
    },
}

def detect(content: str) -> List[Dict]:
    """Detect known obfuscation patterns in PowerShell/batch code."""
    results = []
    for name, info in DETECTION_PATTERNS.items():
        matches = re.finditer(info['pattern'], content, re.IGNORECASE)
        for match in matches:
            results.append({
                'pattern': name,
                'description': info['description'],
                'severity': info['severity'],
                'language': info['lang'],
                'match': match.group(),
                'position': match.start()
            })
    return results

# ============================================================================
# MAIN OBFUSCATION FUNCTIONS
# ============================================================================

ENCODING_TECHNIQUES = {
    'ascii': powershell_ascii_encoding,
    'hex': powershell_hex_encoding,
    'octal': powershell_octal_encoding,
    'binary': powershell_binary_encoding,
    'bxor': powershell_bxor_encoding,
    'whitespace': powershell_whitespace_encoding,
    'compressed': powershell_compressed,
    'string': powershell_string_obfuscation,
}

LAUNCHER_TECHNIQUES = {
    'ps': launcher_ps,
    'cmd': launcher_cmd,
    'wmic': launcher_wmic,
    'rundll': launcher_rundll,
    'var': launcher_var_push,
    'stdin': launcher_stdin_push,
    'clip': launcher_clip_push,
    'varpp': launcher_var_grandparent,
    'mshta': launcher_mshta,
}

def obfuscate(
    script: str,
    encoding: str = 'all',
    launcher: str = None,
    level: int = 2
) -> List[Dict]:
    """
    Obfuscate a PowerShell script.

    Args:
        script: The PowerShell script to obfuscate
        encoding: Encoding technique: 'ascii', 'hex', 'octal', 'binary',
                  'bxor', 'whitespace', 'compressed', 'string', or 'all'
        launcher: Launcher technique: 'ps', 'cmd', 'wmic', 'rundll', 'var',
                  'stdin', 'clip', 'varpp', 'mshta', or None
        level: Obfuscation level 1-3

    Returns:
        List of obfuscated command variants
    """
    results = []

    if encoding == 'all':
        encodings_to_apply = list(ENCODING_TECHNIQUES.keys())
    else:
        encodings_to_apply = [encoding] if encoding in ENCODING_TECHNIQUES else []

    for enc in encodings_to_apply:
        try:
            func = ENCODING_TECHNIQUES[enc]
            encoded = func(script, level)

            # Apply launcher if specified
            if launcher and launcher in LAUNCHER_TECHNIQUES:
                launch_func = LAUNCHER_TECHNIQUES[launcher]
                # The launcher typically handles its own encoding
                final_cmd = launch_func(script, level)
                results.append({
                    'technique': f'{enc}+{launcher}',
                    'encoding': enc,
                    'launcher': launcher,
                    'command': final_cmd
                })
            else:
                results.append({
                    'technique': enc,
                    'command': encoded
                })
        except Exception as e:
            results.append({
                'technique': enc,
                'error': str(e)
            })

    return results

def obfuscate_full(script: str, encoding: str = 'base64', launcher: str = 'ps', level: int = 2) -> str:
    """
    Full obfuscation: encode + wrap with launcher.

    Args:
        script: PowerShell script
        encoding: 'base64', 'hex', 'ascii', 'compressed'
        launcher: 'ps', 'cmd', 'wmic', 'rundll', 'var', 'stdin', 'clip', 'mshta'
        level: 1-3

    Returns:
        Final obfuscated command string
    """
    # First encode the script
    if encoding == 'base64':
        encoded = base64.b64encode(script.encode('utf-16-le')).decode()
        inner = f'powershell -NoP -NonI -Enc {encoded}'
    elif encoding == 'hex':
        inner = powershell_hex_encoding(script, level)
    elif encoding == 'ascii':
        inner = powershell_ascii_encoding(script, level)
    elif encoding == 'compressed':
        inner = powershell_compressed(script, level)
    else:
        inner = script

    # Then wrap with launcher
    if launcher == 'ps':
        return inner
    elif launcher == 'cmd':
        return f'cmd /c {inner}'
    elif launcher == 'wmic':
        return f'wmic process call create "{inner}"'
    elif launcher == 'rundll':
        return f'rundll32.exe javascript:"\\..\\mshtml,RunHTMLApplication";document.write();{inner}'
    elif launcher == 'var':
        var = ''.join(random.choices(string.ascii_uppercase, k=6))
        return f'set {var}={encoded}&&powershell -NoP -NonI -Enc %{var}%'
    elif launcher == 'mshta':
        return f'mshta vbscript:Execute("Set sh=CreateObject(^"WScript.Shell^"):sh.Run ^"{inner}^",0"):Close()'
    else:
        return inner

def list_techniques() -> Dict:
    """List all available techniques."""
    return {
        'encoding': list(ENCODING_TECHNIQUES.keys()),
        'launcher': list(LAUNCHER_TECHNIQUES.keys())
    }

# ============================================================================
# CLI
# ============================================================================

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: powershell_obfuscation.py <script> [options]")
        print("Options:")
        print("  --encoding <name>   Encoding technique")
        print("  --launcher <name>  Launcher technique")
        print("  --level <1-3>      Obfuscation level")
        print("  --detect           Detect patterns")
        print("  --list             List all techniques")
        sys.exit(1)

    script = sys.argv[1]

    if '--list' in sys.argv:
        print(json.dumps(list_techniques(), indent=2))
    elif '--detect' in sys.argv:
        results = detect(script)
        print(json.dumps(results, indent=2))
    else:
        encoding = 'base64'
        launcher = None
        level = 2

        if '--encoding' in sys.argv:
            idx = sys.argv.index('--encoding')
            if idx + 1 < len(sys.argv):
                encoding = sys.argv[idx + 1]

        if '--launcher' in sys.argv:
            idx = sys.argv.index('--launcher')
            if idx + 1 < len(sys.argv):
                launcher = sys.argv[idx + 1]

        if '--level' in sys.argv:
            idx = sys.argv.index('--level')
            if idx + 1 < len(sys.argv):
                level = int(sys.argv[idx + 1])

        results = obfuscate(script, encoding, launcher, level)
        print(json.dumps(results, indent=2))
