#!/usr/bin/env python3
"""
msi-generator: Generate MSI installer files for defensive testing
Based on msilib (Python standard library)

This module generates MSI installer files for testing detection rules
against MSI installation behavior.
"""

import os
import tempfile
import shutil
from typing import Dict, List, Optional

try:
    import msilib
    from msilib import schema
    MSILIB_AVAILABLE = True
except ImportError:
    MSILIB_AVAILABLE = False

# ============================================================================
# MSI GENERATION
# ============================================================================

def generate_msi(
    output_path: str,
    name: str,
    version: str = "1.0.0",
    manufacturer: str = "TestVendor",
    source_file: Optional[str] = None,
    install_dir: Optional[str] = None,
    description: Optional[str] = None,
    executable_name: Optional[str] = None,
) -> Dict:
    """
    Generate a basic MSI installer.

    Args:
        output_path: Path to output MSI file
        name: Application name
        version: Application version (e.g., "1.0.0")
        manufacturer: Manufacturer/vendor name
        source_file: Path to executable to include in MSI
        install_dir: Custom installation directory name (default: app name)
        description: Product description
        executable_name: Name of executable in MSI (extracted from source_file if not provided)

    Returns:
        Dictionary with 'success', 'path', 'info', 'error'
    """
    result = {
        'success': False,
        'path': None,
        'info': {},
        'error': None,
    }

    if not MSILIB_AVAILABLE:
        result['error'] = "msilib not available. On Windows, msilib is included. On Linux, install msitools: apt-get install msitools"
        return result

    try:
        # Create temporary directory for building
        temp_dir = tempfile.mkdtemp()

        # Determine install directory
        if install_dir is None:
            install_dir = name.replace(' ', '')

        # Extract executable name from source file
        if executable_name is None and source_file:
            executable_name = os.path.basename(source_file)

        # Copy source file to temp directory if provided
        if source_file:
            if not os.path.exists(source_file):
                result['error'] = f"Source file not found: {source_file}"
                return result
            shutil.copy2(source_file, os.path.join(temp_dir, executable_name))

        # Create MSI database
        db = msilib.init_database(
            output_path,
            msilib.schema,
            name,
            version,
            manufacturer,
            description or name
        )

        # Define directories
        directories = [
            ('TARGETDIR', None, 'SourceDir'),  # Root directory (required)
            ('ProgramFilesFolder', 'TARGETDIR', '[ProgramFiles]'),
            ('AppFolder', 'ProgramFilesFolder', install_dir),
        ]
        msilib.add_data(db, 'Directory', directories)

        # Define component
        component_id = 'MainComponent'
        components = [
            (component_id, 'AppFolder', None, 0, None, None)
        ]
        msilib.add_data(db, 'Component', components)

        # Add files if source provided
        if executable_name:
            files = [
                (executable_name, executable_name, component_id, None, None, None)
            ]
            msilib.add_data(db, 'File', files)

        # Add feature
        features = [
            ('MainFeature', component_id, None, 1, 0, 0)
        ]
        msilib.add_data(db, 'Feature', features)

        # Add component to feature
        component_flags = [
            (component_id, 'MainFeature', 0)
        ]
        msilib.add_data(db, 'Component', component_flags)

        # Commit MSI
        db.Commit()

        result['success'] = True
        result['path'] = output_path
        result['info'] = {
            'name': name,
            'version': version,
            'manufacturer': manufacturer,
            'install_dir': install_dir,
            'executable': executable_name,
        }

    except Exception as e:
        result['error'] = str(e)
    finally:
        # Clean up temp directory
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir, ignore_errors=True)

    return result


def generate_msi_with_scripts(
    output_path: str,
    name: str,
    version: str = "1.0.0",
    manufacturer: str = "TestVendor",
    install_script: Optional[str] = None,
    uninstall_script: Optional[str] = None,
    install_dir: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict:
    """
    Generate MSI with custom install/uninstall scripts.

    Args:
        output_path: Path to output MSI file
        name: Application name
        version: Application version
        manufacturer: Manufacturer name
        install_script: PowerShell/VBScript to run during install
        uninstall_script: PowerShell/VBScript to run during uninstall
        install_dir: Custom installation directory
        description: Product description

    Returns:
        Dictionary with success status and details
    """
    result = {
        'success': False,
        'path': None,
        'info': {},
        'error': None,
    }

    if not MSILIB_AVAILABLE:
        result['error'] = "msilib not available"
        return result

    try:
        if install_dir is None:
            install_dir = name.replace(' ', '')

        # Create MSI database
        db = msilib.init_database(
            output_path,
            msilib.schema,
            name,
            version,
            manufacturer,
            description or name
        )

        # Define directories
        directories = [
            ('TARGETDIR', None, 'SourceDir'),
            ('ProgramFilesFolder', 'TARGETDIR', '[ProgramFiles]'),
            ('AppFolder', 'ProgramFilesFolder', install_dir),
            ('SystemFolder', 'TARGETDIR', '[SystemFolder]'),
        ]
        msilib.add_data(db, 'Directory', directories)

        # Create custom actions table
        if install_script:
            # Write script to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False) as f:
                f.write(install_script)
                script_path = f.name

            custom_actions = [
                ('InstallAction', 1, script_path, 'powershell.exe -ExecutionPolicy Bypass -File "[SourceDir]install.ps1"'),
            ]
            msilib.add_data(db, 'CustomAction', custom_actions)

        if uninstall_script:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False) as f:
                f.write(uninstall_script)
                script_path = f.name

            custom_actions_uninstall = [
                ('UninstallAction', 1, script_path, 'powershell.exe -ExecutionPolicy Bypass -File "[SourceDir]uninstall.ps1"'),
            ]
            msilib.add_data(db, 'CustomAction', custom_actions_uninstall)

        # Define component
        component_id = 'ScriptComponent'
        components = [
            (component_id, 'AppFolder', None, 0, None, None)
        ]
        msilib.add_data(db, 'Component', components)

        # Add feature
        features = [
            ('MainFeature', component_id, None, 1, 0, 0)
        ]
        msilib.add_data(db, 'Feature', features)

        # Commit
        db.Commit()

        result['success'] = True
        result['path'] = output_path
        result['info'] = {
            'name': name,
            'version': version,
            'manufacturer': manufacturer,
            'has_install_script': install_script is not None,
            'has_uninstall_script': uninstall_script is not None,
        }

    except Exception as e:
        result['error'] = str(e)

    return result


def generate_suspicious_msi(
    output_path: str,
    name: str = "SystemUpdate",
    payload_command: str = "calc.exe",
) -> Dict:
    """
    Generate a suspicious-looking MSI for detection testing.

    This creates an MSI that mimics patterns commonly seen in
    malicious installers for testing detection rules.

    Args:
        output_path: Path to output MSI
        name: Product name (default: SystemUpdate - sounds legitimate)
        payload_command: Command to execute (for testing)

    Returns:
        Dictionary with success status
    """
    result = {
        'success': False,
        'path': None,
        'info': {},
        'error': None,
    }

    if not MSILIB_AVAILABLE:
        result['error'] = "msilib not available"
        return result

    try:
        # Use suspicious naming/behavior
        suspicious_name = name
        suspicious_manufacturer = "Microsoft Update"

        # Generate MSI with custom action to run payload
        install_script = f'''
# Hidden PowerShell script
$p = Start-Process -FilePath "{payload_command}" -WindowStyle Hidden
'''

        result = generate_msi_with_scripts(
            output_path=output_path,
            name=suspicious_name,
            version="1.0.4321.1234",
            manufacturer=suspicious_manufacturer,
            install_script=install_script,
            description="Critical system update for Windows"
        )

        if result['success']:
            result['info']['detection_hints'] = [
                "Suspicious product name: " + suspicious_name,
                "Suspicious manufacturer: " + suspicious_manufacturer,
                "Hidden payload execution",
                "Version number pattern: 1.0.4321.1234"
            ]

    except Exception as e:
        result['error'] = str(e)

    return result


# ============================================================================
# MSI ANALYSIS (Detection)
# ============================================================================

DETECTION_PATTERNS = {
    'MSI_CUSTOM_ACTION': {
        'description': 'Custom action in MSI',
        'severity': 'medium',
        'indicators': ['CustomAction', 'Script', 'powershell.exe']
    },
    'MSI_HIDDEN_EXEC': {
        'description': 'Hidden execution pattern',
        'severity': 'high',
        'indicators': ['WindowStyle Hidden', 'Hidden', 'NoVisible']
    },
    'MSI_REGISTRY_WRITE': {
        'description': 'Registry modification',
        'severity': 'medium',
        'indicators': ['Registry', 'HKLM', 'HKCU']
    },
    'MSI_SCHEDULE_TASK': {
        'description': 'Scheduled task creation',
        'severity': 'high',
        'indicators': ['Schedule', 'ScheduledTask', 'AtStartup']
    },
    'MSI_SERVICE_INSTALL': {
        'description': 'Windows service installation',
        'severity': 'high',
        'indicators': ['ServiceControl', 'ServiceInstall']
    },
    'MSI_FILE_OVERWRITE': {
        'description': 'File overwrite/modification',
        'severity': 'medium',
        'indicators': ['RemoveFile', 'DuplicateFiles']
    },
}


def analyze_msi(msi_path: str) -> Dict:
    """
    Analyze an MSI file for suspicious patterns.

    Args:
        msi_path: Path to MSI file

    Returns:
        Dictionary with analysis results
    """
    result = {
        'exists': False,
        'suspicious': False,
        'patterns_found': [],
        'info': {},
        'error': None,
    }

    if not os.path.exists(msi_path):
        result['error'] = f"MSI file not found: {msi_path}"
        return result

    result['exists'] = True

    try:
        # Open MSI database
        import msilib.database
        db = msilib.database.OpenDatabase(msi_path, msilib.database.MSIDBOPEN_READONLY)

        # Get summary info
        summary = db.GetSummaryInformation(0)
        result['info'] = {
            'title': summary.GetProperty(2),  # PID_TITLE
            'subject': summary.GetProperty(3),  # PID_SUBJECT
            'author': summary.GetProperty(4),  # PID_AUTHOR
            'comments': summary.GetProperty(6),  # PID_COMMENTS
        }

        # Check for custom actions
        try:
            view = db.OpenView("SELECT * FROM CustomAction")
            view.Execute(None)
            custom_actions = []
            while True:
                record = view.Fetch()
                if record is None:
                    break
                custom_actions.append(record.GetString(2))  # Action name
            result['info']['custom_actions'] = custom_actions
        except:
            pass

        # Check for suspicious patterns
        msi_content = str(msi_path).lower()

        for pattern_name, pattern_info in DETECTION_PATTERNS.items():
            for indicator in pattern_info['indicators']:
                if indicator.lower() in msi_content:
                    result['patterns_found'].append({
                        'pattern': pattern_name,
                        'description': pattern_info['description'],
                        'severity': pattern_info['severity'],
                        'indicator': indicator,
                    })
                    break

        if len(result['patterns_found']) >= 2:
            result['suspicious'] = True

        db.Close()

    except Exception as e:
        result['error'] = str(e)

    return result


# ============================================================================
# CLI
# ============================================================================

if __name__ == '__main__':
    import sys
    import json

    def print_help():
        print("Usage: msi_generator.py <command> [options]")
        print("")
        print("Commands:")
        print("  generate <output.msi>    Generate basic MSI")
        print("  generate-suspicious        Generate suspicious MSI for testing")
        print("  analyze <file.msi>       Analyze MSI for patterns")
        print("")
        print("Generate Options:")
        print("  -n, --name         Product name")
        print("  -v, --version      Version (default: 1.0.0)")
        print("  -m, --manufacturer Manufacturer")
        print("  -f, --file         Source executable to include")
        print("  -d, --dir          Installation directory")
        print("")
        print("Examples:")
        print("  msi_generator.py generate output.msi -n MyApp -f myapp.exe")
        print("  msi_generator.py analyze suspicious.msi")

    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'generate':
        if len(sys.argv) < 3:
            print("Error: Missing output path")
            print_help()
            sys.exit(1)

        output_path = sys.argv[2]
        kwargs = {'output_path': output_path}

        # Parse options
        i = 3
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg in ('-n', '--name') and i + 1 < len(sys.argv):
                kwargs['name'] = sys.argv[i + 1]
                i += 2
            elif arg in ('-v', '--version') and i + 1 < len(sys.argv):
                kwargs['version'] = sys.argv[i + 1]
                i += 2
            elif arg in ('-m', '--manufacturer') and i + 1 < len(sys.argv):
                kwargs['manufacturer'] = sys.argv[i + 1]
                i += 2
            elif arg in ('-f', '--file') and i + 1 < len(sys.argv):
                kwargs['source_file'] = sys.argv[i + 1]
                i += 2
            elif arg in ('-d', '--dir') and i + 1 < len(sys.argv):
                kwargs['install_dir'] = sys.argv[i + 1]
                i += 2
            else:
                i += 1

        result = generate_msi(**kwargs)

        if result['success']:
            print(f"MSI created: {result['path']}")
            print(json.dumps(result['info'], indent=2))
        else:
            print(f"Error: {result['error']}")
            sys.exit(1)

    elif cmd == 'generate-suspicious':
        if len(sys.argv) < 3:
            print("Error: Missing output path")
            sys.exit(1)

        output_path = sys.argv[2]
        payload = sys.argv[3] if len(sys.argv) > 3 else "calc.exe"

        result = generate_suspicious_msi(output_path, payload_command=payload)

        if result['success']:
            print(f"Suspicious MSI created: {result['path']}")
            print("Detection hints:")
            for hint in result['info'].get('detection_hints', []):
                print(f"  - {hint}")
        else:
            print(f"Error: {result['error']}")
            sys.exit(1)

    elif cmd == 'analyze':
        if len(sys.argv) < 3:
            print("Error: Missing MSI path")
            print_help()
            sys.exit(1)

        msi_path = sys.argv[2]
        result = analyze_msi(msi_path)

        if result['error']:
            print(f"Error: {result['error']}")
            sys.exit(1)

        print(f"MSI: {msi_path}")
        print(f"Suspicious: {result['suspicious']}")
        if result['info']:
            print("\nInfo:")
            for k, v in result['info'].items():
                print(f"  {k}: {v}")
        if result['patterns_found']:
            print("\nPatterns found:")
            for p in result['patterns_found']:
                print(f"  [{p['severity']}] {p['description']} ({p['indicator']})")

    else:
        print(f"Unknown command: {cmd}")
        print_help()
        sys.exit(1)
