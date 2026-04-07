#!/usr/bin/env python3
"""
donut: Generate shellcode from .NET assemblies for defensive testing
Based on TheWover/donut (https://github.com/TheWover/donut)

This module provides shellcode generation capabilities for creating test samples
to validate detection rules against Donut-generated shellcode.

IMPORTANT: For authorized defensive security research only.
"""

import base64
import json
import os
import re
import subprocess
import tempfile
from typing import Dict, List, Optional

# ============================================================================
# CONFIGURATION
# ============================================================================

# Default Donut parameters
DEFAULT_ARCH = 3  # x86+amd64 dual-mode
DEFAULT_BYPASS = 3  # Continue on AMSI/WLDP fail
DEFAULT_FORMAT = 5  # Python format
DEFAULT_COMPRESS = 2  # aPLib compression

# Architecture options
ARCH_MAP = {
    'x86': 1,
    'amd64': 2,
    'x86+amd64': 3,
}

# Bypass options
BYPASS_MAP = {
    'none': 1,
    'abort': 2,
    'continue': 3,
}

# Format options
FORMAT_MAP = {
    'binary': 1,
    'base64': 2,
    'ruby': 3,
    'c': 4,
    'python': 5,
    'powershell': 6,
    'csharp': 7,
    'hex': 8,
}

# Compression options
COMPRESS_MAP = {
    'none': 1,
    'aplib': 2,
    'lznt1': 3,
    'xpress': 4,
    'xpress_huff': 5,
}

# Exit options
EXIT_MAP = {
    'thread': 1,  # RtlExitUserThread (default)
    'process': 2,  # RtlExitUserProcess
    'block': 3,  # Block indefinitely
}

# ============================================================================
# DETECTION PATTERNS
# ============================================================================

DETECTION_PATTERNS = {
    'DONUT_CLR_GUID': {
        'pattern': r'(cb2f6723[_-]ab3a[_-]11d2[_-]9c40|9280188d[_-]0e8e[_-]4867[_-]b3c)',
        'description': 'Donut CLR GUID - used for runtime binding',
        'severity': 'high',
    },
    'DONUT_MODULE_NAME': {
        'pattern': r'(donut|DONUT)',
        'description': 'Donut module name marker',
        'severity': 'medium',
    },
    'AMSI_BYPASS': {
        'pattern': r'(AmsiScan(Buffer|String)|amsiInitSession)',
        'description': 'AMSI bypass API references',
        'severity': 'high',
    },
    'HIGH_ENTROPY_PAYLOAD': {
        'description': 'High entropy indicates encrypted Donut payload',
        'severity': 'medium',
        'threshold': 7.0,
    },
    'APLIB_COMPRESSION': {
        'pattern': r'(\x24\x00|\x30\x00)',
        'description': 'aPLib compression signature',
        'severity': 'medium',
    },
    'SHELLCODE_PROLOGUE': {
        'pattern': r'(\x50\x51\x52\x53\x56\x57\x55)',
        'description': 'Typical shellcode prologue (pushad)',
        'severity': 'low',
    },
    'VIRTUALALLOC_CREATETHREAD': {
        'description': 'VirtualAlloc followed by CreateThread pattern',
        'severity': 'high',
    },
}

# ============================================================================
# SHELLCODE GENERATION
# ============================================================================

def generate_shellcode(
    file_path: str,
    cls: Optional[str] = None,
    method: Optional[str] = None,
    params: Optional[str] = None,
    arch: int = DEFAULT_ARCH,
    bypass: int = DEFAULT_BYPASS,
    format: int = DEFAULT_FORMAT,
    compress: int = DEFAULT_COMPRESS,
    entropy: int = 3,
    exit_opt: int = 1,
    runtime: Optional[str] = None,
    appdomain: Optional[str] = None,
    url: Optional[str] = None,
    unicode: bool = False,
) -> Dict:
    """
    Generate shellcode from a .NET assembly using Donut.

    Args:
        file_path: Path to .NET EXE/DLL, VBS, JS, or XSL file
        cls: Optional class name (required for .NET DLL)
        method: Optional method name (required for .NET DLL)
        params: Optional parameters for the method
        arch: Target architecture (1=x86, 2=amd64, 3=x86+amd64)
        bypass: AMSI/WLDP bypass behavior (1=none, 2=abort, 3=continue)
        format: Output format (1=binary, 2=base64, 3=ruby, 4=c, 5=python, 6=powershell, 7=csharp, 8=hex)
        compress: Compression engine (1=none, 2=aplib, 3=lznt1, 4=xpress, 5=xpress_huff)
        entropy: Entropy level (1=none, 2=random, 3=default)
        exit_opt: Exit behavior (1=thread, 2=process, 3=block)
        runtime: CLR runtime version (e.g., 'v4.0.30319')
        appdomain: AppDomain name
        url: HTTP server URL for staging
        unicode: Convert params to Unicode

    Returns:
        Dictionary with 'success', 'shellcode', 'format', 'info'
    """
    result = {
        'success': False,
        'shellcode': None,
        'format': None,
        'info': {},
        'error': None,
    }

    # Validate input file exists
    if not os.path.exists(file_path):
        result['error'] = f"File not found: {file_path}"
        return result

    # Check if donut is available
    donut_path = _find_donut()
    if not donut_path:
        result['error'] = "Donut not found. Install from https://github.com/TheWover/donut"
        return result

    # Build command
    cmd = [donut_path, '-f', file_path]

    if cls:
        cmd.extend(['-c', cls])
    if method:
        cmd.extend(['-m', method])
    if params:
        cmd.extend(['-p', params])

    cmd.extend(['-a', str(arch)])
    cmd.extend(['-b', str(bypass)])
    cmd.extend(['-o', str(format)])

    if compress != DEFAULT_COMPRESS:
        cmd.extend(['-e', str(compress)])

    if entropy != 3:
        cmd.extend(['-h', str(entropy)])

    if exit_opt != 1:
        cmd.extend(['-x', str(exit_opt)])

    if runtime:
        cmd.extend(['-r', runtime])
    if appdomain:
        cmd.extend(['-d', appdomain])
    if url:
        cmd.extend(['-u', url])
    if unicode:
        cmd.append('-w')

    # Generate to temporary file
    with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
        output_file = f.name

    try:
        cmd.extend(['-o', output_file])

        # Execute donut
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if proc.returncode != 0:
            result['error'] = proc.stderr or "Donut execution failed"
            return result

        # Read output
        with open(output_file, 'rb') as f:
            shellcode_bytes = f.read()

        # Format output based on requested format
        format_name = _get_format_name(format)

        if format == 2:  # Base64
            shellcode = base64.b64encode(shellcode_bytes).decode('utf-8')
        elif format == 8:  # Hex
            shellcode = shellcode_bytes.hex()
        elif format == 4:  # C
            shellcode = _format_as_c(shellcode_bytes)
        elif format == 5:  # Python
            shellcode = _format_as_python(shellcode_bytes)
        elif format == 6:  # PowerShell
            shellcode = _format_as_powershell(shellcode_bytes)
        elif format == 7:  # C#
            shellcode = _format_as_csharp(shellcode_bytes)
        else:  # Binary - return as base64 for text output
            shellcode = base64.b64encode(shellcode_bytes).decode('utf-8')

        result['success'] = True
        result['shellcode'] = shellcode
        result['format'] = format_name
        result['info'] = {
            'input_file': file_path,
            'arch': _get_arch_name(arch),
            'bypass': _get_bypass_name(bypass),
            'compression': _get_compress_name(compress),
            'entropy': entropy,
        }

    except subprocess.TimeoutExpired:
        result['error'] = "Donut execution timed out"
    except Exception as e:
        result['error'] = str(e)
    finally:
        # Clean up temp file
        if os.path.exists(output_file):
            os.unlink(output_file)

    return result

def _find_donut() -> Optional[str]:
    """Find donut executable in PATH or common locations."""
    # Check PATH
    for path in os.environ.get('PATH', '').split(os.pathsep):
        donut_path = os.path.join(path, 'donut')
        if os.path.exists(donut_path):
            return donut_path
        if os.path.exists(donut_path + '.exe'):
            return donut_path + '.exe'

    # Check common locations
    common_paths = [
        '/tmp/donut/donut',
        '/usr/local/bin/donut',
        '/usr/bin/donut',
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path

    return None

def _get_arch_name(arch: int) -> str:
    for name, val in ARCH_MAP.items():
        if val == arch:
            return name
    return f"unknown({arch})"

def _get_bypass_name(bypass: int) -> str:
    for name, val in BYPASS_MAP.items():
        if val == bypass:
            return name
    return f"unknown({bypass})"

def _get_compress_name(compress: int) -> str:
    for name, val in COMPRESS_MAP.items():
        if val == compress:
            return name
    return f"unknown({compress})"

def _get_format_name(format: int) -> str:
    for name, val in FORMAT_MAP.items():
        if val == format:
            return name
    return f"unknown({format})"

def _format_as_c(data: bytes) -> str:
    """Format shellcode as C array."""
    hex_pairs = ['0x' + format(b, '02x') for b in data]
    chunks = [', '.join(hex_pairs[i:i+12]) for i in range(0, len(hex_pairs), 12)]
    return 'unsigned char shellcode[] = {\n    ' + ',\n    '.join(chunks) + '\n};'

def _format_as_python(data: bytes) -> str:
    """Format shellcode as Python bytes."""
    hex_str = data.hex()
    return f'shellcode = bytes.fromhex("{hex_str}")'

def _format_as_powershell(data: bytes) -> str:
    """Format shellcode as PowerShell."""
    hex_str = data.hex()
    return f'$shellcode = [byte[]]({",".join([hex_str[i:i+2] for i in range(0, len(hex_str), 2)])})'

def _format_as_csharp(data: bytes) -> str:
    """Format shellcode as C# byte array."""
    hex_pairs = [format(b, '02x') for b in data]
    chunks = [', '.join(hex_pairs[i:i+16]) for i in range(0, len(hex_pairs), 16)]
    return 'byte[] shellcode = {\n    ' + ',\n    '.join(chunks) + '\n};'

# ============================================================================
# DETECTION
# ============================================================================

def detect(data: str) -> List[Dict]:
    """
    Check if data contains Donut shellcode patterns.

    Args:
        data: String to check

    Returns:
        List of detected patterns
    """
    results = []

    for pattern_name, info in DETECTION_PATTERNS.items():
        pattern = info.get('pattern')

        if pattern:
            matches = re.finditer(pattern, data, re.IGNORECASE)
            for match in matches:
                results.append({
                    'pattern': pattern_name,
                    'description': info['description'],
                    'severity': info['severity'],
                    'match': match.group()[:50],
                })

    return results

# ============================================================================
# CLI
# ============================================================================

if __name__ == '__main__':
    import sys

    def print_help():
        print("Usage: donut.py <command> [options]")
        print("")
        print("Commands:")
        print("  generate <file>   Generate shellcode from .NET assembly")
        print("  detect <data>     Detect Donut patterns in data")
        print("  list              List available options")
        print("")
        print("Generate Options:")
        print("  -c, --cls        Class name (required for DLL)")
        print("  -m, --method     Method name (required for DLL)")
        print("  -p, --params     Parameters")
        print("  -a, --arch       Architecture: 1=x86, 2=amd64, 3=x86+amd64 (default)")
        print("  -b, --bypass     Bypass: 1=none, 2=abort, 3=continue (default)")
        print("  -f, --format     Format: 1=binary, 2=base64, 4=c, 5=python, 6=ps, 7=cs, 8=hex")
        print("  -e, --compress   Compression: 1=none, 2=aplib (default)")
        print("  -o, --output     Output file")
        print("")
        print("Examples:")
        print("  donut.py generate malicious.exe -c Namespace.Class -m Main")
        print("  donut.py detect 'cb2f6723-ab3a-11d2-9c40'")
        print("  donut.py list")

    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'list':
        print("Architecture options:")
        for name, val in ARCH_MAP.items():
            print(f"  {val} = {name}")
        print("\nBypass options:")
        for name, val in BYPASS_MAP.items():
            print(f"  {val} = {name}")
        print("\nFormat options:")
        for name, val in FORMAT_MAP.items():
            print(f"  {val} = {name}")
        print("\nCompression options:")
        for name, val in COMPRESS_MAP.items():
            print(f"  {val} = {name}")

    elif cmd == 'generate':
        if len(sys.argv) < 3:
            print("Error: Missing input file")
            print_help()
            sys.exit(1)

        file_path = sys.argv[2]

        # Parse options
        kwargs = {}
        i = 3
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg in ('-c', '--cls') and i + 1 < len(sys.argv):
                kwargs['cls'] = sys.argv[i + 1]
                i += 2
            elif arg in ('-m', '--method') and i + 1 < len(sys.argv):
                kwargs['method'] = sys.argv[i + 1]
                i += 2
            elif arg in ('-p', '--params') and i + 1 < len(sys.argv):
                kwargs['params'] = sys.argv[i + 1]
                i += 2
            elif arg in ('-a', '--arch') and i + 1 < len(sys.argv):
                kwargs['arch'] = int(sys.argv[i + 1])
                i += 2
            elif arg in ('-b', '--bypass') and i + 1 < len(sys.argv):
                kwargs['bypass'] = int(sys.argv[i + 1])
                i += 2
            elif arg in ('-f', '--format') and i + 1 < len(sys.argv):
                kwargs['format'] = int(sys.argv[i + 1])
                i += 2
            elif arg in ('-e', '--compress') and i + 1 < len(sys.argv):
                kwargs['compress'] = int(sys.argv[i + 1])
                i += 2
            elif arg in ('-o', '--output'):
                output_file = sys.argv[i + 1] if i + 1 < len(sys.argv) else None
                i += 2
            else:
                i += 1

        result = generate_shellcode(file_path, **kwargs)

        if result['success']:
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(result['shellcode'])
                print(f"Shellcode written to {output_file}")
            else:
                print(result['shellcode'])
        else:
            print(f"Error: {result['error']}")
            sys.exit(1)

    elif cmd == 'detect':
        if len(sys.argv) < 3:
            print("Error: Missing data to detect")
            print_help()
            sys.exit(1)

        data = sys.argv[2]
        results = detect(data)

        if results:
            print(json.dumps(results, indent=2))
        else:
            print("No Donut patterns detected")

    else:
        print(f"Unknown command: {cmd}")
        print_help()
        sys.exit(1)
