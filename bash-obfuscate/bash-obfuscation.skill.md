---
name: bash-obfuscation
description: Bash command obfuscation toolkit for defensive testing, based on Bashfuscator
triggers:
  - "obfuscate bash"
  - "bash obfuscation"
  - "linux obfuscation"
  - "bashfuscator"
---

# bash-obfuscation Skill

Bash命令混淆工具包，基于 [Bashfuscator](https://github.com/Bashfuscator/Bashfuscator) 项目。

## Commands

### obfuscate

Generate obfuscated Bash commands.

```bash
obfuscate <command> [--technique name|all] [--level 1-3]
```

**Parameters:**
- `command`: The Bash command to obfuscate
- `--technique`: Obfuscation technique (default: all)
- `--level`: Obfuscation level 1-3 (default: 2)

**Examples:**
```bash
obfuscate "cat /etc/passwd"
obfuscate "ls -la" --technique base64
obfuscate "whoami" --technique hex --level 3
```

### detect

Check if code matches known obfuscation patterns.

```bash
detect <command>
```

**Detection patterns:**
- `BASE64_PIPE`: Base64 decode piped to execution
- `HEX_ENCODING`: Hex encoded strings
- `GZIP_DECOMPRESS`: Gzip decompression
- `BZIP_DECOMPRESS`: Bzip2 decompression
- `REV_COMMAND`: Reverse command
- `EVAL_EXECUTION`: Eval execution
- `FOR_LOOP_SHELL`: FOR loop
- `XXD_HEXDUMP`: Hexdump reverse
- `TR_ROT13`: ROT13 translation

**Examples:**
```bash
detect "echo 'a被害' | base64 -d | bash"
detect "printf '\\x65\\x63\\x68\\x6f' | bash"
```

### list

List all available techniques.

```bash
list
```

---

## Techniques

### Encoding Techniques

| Technique | Description | Example |
|-----------|-------------|---------|
| `base64` | Base64 encode + decode | `echo "..." \| base64 -d \| bash` |
| `hex` | Hex encoding | `echo -e "\\x65\\x63\\x68\\x6f" \| xxd -r -p \| bash` |
| `gzip` | Gzip compression | `printf "..." \| base64 -d \| gunzip -c \| bash` |
| `bzip2` | Bzip2 compression | `printf "..." \| base64 -d \| bunzip2 -c \| bash` |
| `rot13` | ROT13 encoding | `echo "..." \| tr "a-z" "n-za-m" \| bash` |
| `xor` | XOR encoding with key | Uses Python for decode |

### Obfuscation Techniques

| Technique | Description |
|-----------|-------------|
| `reverse` | Reverse command + `rev` |
| `case_swap` | Case manipulation `${VAR~~}` |
| `for_code` | FOR loop character reassembly |
| `special_char` | Special character only |
| `env_subst` | Environment variable substitution |
| `whitespace` | Whitespace injection |
| `quote` | Quote wrapping variations |
| `pipe` | Dummy pipe stages |
| `subshell` | Subshell execution |

---

## Implementation

```python
from bash_obfuscation import obfuscate, detect, list_techniques

# List all techniques
print(list_techniques())

# Obfuscate a command
results = obfuscate("cat /etc/passwd", technique='base64', level=2)
for r in results:
    print(f"[{r['technique']}] {r['command']}")

# Detect patterns
matches = detect("echo 'data' | base64 -d | bash")
print(matches)
```

---

## Reference

- **Bashfuscator**: [https://github.com/Bashfuscator/Bashfuscator](https://github.com/Bashfuscator/Bashfuscator)
- **Author**: [capnspacehook](https://github.com/capnspacehook)
- **DEF CON Talk**: Bsides Charm - "Bashfuscator: Obfuscating Linux Commands"
