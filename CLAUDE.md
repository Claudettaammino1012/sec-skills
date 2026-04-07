# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Security research skills repository focused on defensive security tooling. Contains six skills:

1. `cmd-obfuscation` - cmd.exe command obfuscation (Invoke-DOSfuscation)
2. `powershell-obfuscation` - PowerShell command obfuscation (Invoke-Obfuscation)
3. `webshell-obfuscation` - Webshell obfuscation for PHP/JSP/ASP.NET
4. `bash-obfuscation` - Bash command obfuscation (Bashfuscator)
5. `donut` - .NET assembly to shellcode (TheWover/donut)
6. `msi-generator` - MSI installer generation (msilib)

**Purpose**: Generate obfuscated samples for defensive testing, red/blue team exercises, and detection rule development.

## Architecture

```
sec-skills/
├── cmd-obfuscate/
│   ├── cmd_obfuscation.py
│   └── cmd-obfuscation.skill.md
├── powershell-obfuscate/
│   ├── powershell_obfuscation.py
│   └── powershell-obfuscation.skill.md
├── webshell-obfuscate/
│   ├── webshell_obfuscation.py
│   └── webshell-obfuscation.skill.md
├── bash-obfuscate/
│   ├── bash_obfuscation.py
│   └── bash-obfuscation.skill.md
├── donut/
│   ├── donut.py
│   └── donut.skill.md
├── msi-generator/
│   ├── msi_generator.py
│   └── msi-generator.skill.md
└── docs/
    ├── cmd-obfuscate.md
    ├── powershell-obfuscation.md
    ├── webshell-obfuscation.md
    ├── bash-obfuscation.md
    ├── donut.md
    └── msi-generator.md
```

## Common Commands

```bash
# cmd-obfuscate: obfuscate cmd.exe commands
python3 cmd-obfuscate/cmd_obfuscation.py "netstat -ano" --technique all --level 3

# powershell-obfuscate: obfuscate PowerShell commands
python3 powershell-obfuscate/powershell_obfuscation.py "Write-Host 'Hello'" --encoding all
python3 powershell-obfuscate/powershell_obfuscation.py --list

# webshell-obfuscate: obfuscate webshells
python3 webshell-obfuscate/webshell_obfuscation.py "<?php system(\$_GET['cmd']);?>" --lang php --technique all

# bash-obfuscate: obfuscate Bash commands
python3 bash-obfuscate/bash_obfuscation.py "cat /etc/passwd" --technique all
python3 bash-obfuscate/bash_obfuscation.py "ls -la" --technique base64 --level 2

# donut: .NET assembly to shellcode (requires installing donut first)
python3 donut/donut.py generate malicious.exe -c Namespace.Class -m Main
python3 donut/donut.py detect "cb2f6723-ab3a-11d2-9c40"

# msi-generator: Generate MSI installers (Windows only)
python3 msi-generator/msi_generator.py generate output.msi -n MyApp -f myapp.exe
python3 msi-generator/msi_generator.py generate-suspicious fake.msi "calc.exe"
```

## cmd-obfuscation Techniques

| Technique | Description |
|-----------|-------------|
| `envvar` | `%VAR:~start,len%` substring extraction |
| `concat` | SET variables + CALL + delayed expansion |
| `reverse` | FOR /L loop with negative indexing |
| `for` | Index array-based character extraction |
| `fin` | Sequential `%VAR:old=new%` substitution |

## powershell-obfuscation Techniques

**Encoding:** `ascii`, `hex`, `octal`, `binary`, `bxor`, `whitespace`, `compressed`, `string`
**Launcher:** `ps`, `cmd`, `wmic`, `rundll`, `var`, `stdin`, `clip`, `mshta`

## webshell-obfuscation Techniques

**PHP:** `base64`, `nested_base64`, `hex`, `concat`, `variable_var`, `polymorphic`
**JSP:** `unicode`, `scriptlet`, `reflection`, `script_engine`, `xml_encoding`, `double_bom_xml`, `triple_encoding`
**ASP.NET:** `hidden_ns`, `soap`, `handler`

## bash-obfuscation Techniques

**Encoding:** `base64`, `hex`, `gzip`, `bzip2`, `rot13`, `xor`
**Obfuscation:** `reverse`, `case_swap`, `for_code`, `special_char`, `env_subst`, `whitespace`, `quote`, `pipe`, `subshell`

## donut Techniques

**Input types:** .NET EXE/DLL, VBS, JS, XSL
**Architecture:** x86, amd64, x86+amd64 (dual-mode)
**Bypass:** AMSI/WLDP none/abort/continue
**Output formats:** binary, base64, c, python, powershell, csharp, hex

## msi-generator Techniques

**MSI generation:** Basic MSI with executable, custom install/uninstall scripts
**Suspicious MSI:** Mimics legitimate update packages with hidden payload execution
**Analysis:** Detects MSI_CUSTOM_ACTION, MSI_HIDDEN_EXEC, MSI_REGISTRY_WRITE, MSI_SERVICE_INSTALL patterns

## Important Notes

- All tools are for **authorized defensive research only** - see README.md disclaimer
- Reference: Invoke-DOSfuscation, Invoke-Obfuscation, tennc/webshell
- Detection patterns can be extended for testing WAF/IDS/EDR rules
