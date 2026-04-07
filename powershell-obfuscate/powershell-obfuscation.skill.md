---
name: powershell-obfuscation
description: PowerShell obfuscation toolkit for defensive testing, based on Invoke-Obfuscation by Daniel Bohannon
triggers:
  - "obfuscate powershell"
  - "powershell encoding"
  - "ps obfuscation"
  - "invoke-obfuscation"
---

# powershell-obfuscation Skill

PowerShell命令混淆工具包，基于 [Invoke-Obfuscation](https://github.com/danielbohannon/Invoke-Obfuscation) 项目。

## Commands

### obfuscate

Generate obfuscated PowerShell commands.

```bash
obfuscate <script> [--encoding name|all] [--launcher name] [--level 1-3]
```

**Parameters:**
- `script`: The PowerShell script to obfuscate
- `--encoding`: Encoding technique (default: base64)
- `--launcher`: Launcher technique (optional)
- `--level`: Obfuscation level 1-3 (default: 2)

**Examples:**
```bash
obfuscate "Write-Host 'Hello'" --encoding base64 --launcher ps
obfuscate "Get-Process" --encoding all
obfuscate "Invoke-Mimikatz" --encoding hex --level 3
```

### detect

Check if code matches known obfuscation patterns.

```bash
detect <code>
```

### list

List all available techniques.

```bash
list
```

---

## Encoding Techniques

| Technique | Description |
|-----------|-------------|
| `ascii` | Integer-char conversion `([Int][Char]'$_')` |
| `hex` | Hex encoding via `[Convert]::ToString(..., 16)` |
| `octal` | Octal encoding via `[Convert]::ToString(..., 8)` |
| `binary` | Binary encoding via `[Convert]::ToString(..., 2)` |
| `bxor` | Bitwise XOR with random key |
| `whitespace` | Tab/space encoding for digits |
| `compressed` | DeflateStream + Base64 compression |
| `string` | String concatenation obfuscation |

## Launcher Techniques

| Technique | Description |
|-----------|-------------|
| `ps` | Direct `powershell.exe` invocation |
| `cmd` | Wrap via `cmd.exe /c` |
| `wmic` | `wmic process call create` |
| `rundll` | `rundll32.exe` with JavaScript |
| `var` | VAR+ - environment variable push |
| `stdin` | STDIN+ - StandardInput push |
| `clip` | CLIP+ - clipboard push |
| `mshta` | MSHTA++ - VBScript launcher |
