---
name: msi-generator
description: Generate MSI installer files for defensive testing, based on Python msilib
triggers:
  - "generate msi"
  - "msi installer"
  - "windows installer"
  - "msi generator"
---

# msi-generator Skill

MSI 安装包生成工具，基于 Python 内置 `msilib` 库。

用于生成 MSI 安装包样本，测试检测规则对恶意安装包的识别能力。

## Commands

### generate

Generate a basic MSI installer.

```bash
generate <output.msi> [-n name] [-v version] [-m manufacturer] [-f file] [-d dir]
```

**Parameters:**
- `output.msi`: Output path for MSI file
- `-n, --name`: Product name (default: App)
- `-v, --version`: Version (default: 1.0.0)
- `-m, --manufacturer`: Manufacturer name
- `-f, --file`: Source executable to include
- `-d, --dir`: Installation directory

**Examples:**
```bash
generate malicious.msi -n SystemUpdate -f payload.exe
generate test.msi -n MyApp -v 1.0.0 -m "TestVendor"
```

### generate-suspicious

Generate a suspicious-looking MSI for detection testing.

```bash
generate-suspicious <output.msi> [payload_command]
```

**Examples:**
```bash
generate-suspicious fake_update.msi "calc.exe"
generate-suspicious fake_update.msi "powershell -enc ..."
```

### analyze

Analyze MSI for suspicious patterns.

```bash
analyze <file.msi>
```

**Examples:**
```bash
analyze suspicious.msi
```

---

## Detection Patterns

| Pattern | Severity | Description |
|---------|----------|-------------|
| `MSI_CUSTOM_ACTION` | medium | Custom action detected |
| `MSI_HIDDEN_EXEC` | high | Hidden execution |
| `MSI_REGISTRY_WRITE` | medium | Registry modification |
| `MSI_SCHEDULE_TASK` | high | Scheduled task creation |
| `MSI_SERVICE_INSTALL` | high | Windows service installation |

---

## Implementation

```python
from msi_generator import generate_msi, generate_suspicious_msi, analyze_msi

# Generate basic MSI
result = generate_msi(
    output_path="test.msi",
    name="MyApp",
    version="1.0.0",
    manufacturer="TestVendor",
    source_file="myapp.exe"
)

# Generate suspicious MSI for testing
result = generate_suspicious_msi(
    output_path="fake_update.msi",
    name="CriticalUpdate",
    payload_command="calc.exe"
)

# Analyze MSI
analysis = analyze_msi("suspicious.msi")
print(analysis['suspicious'])
```

---

## Reference

- **msilib**: Python standard library for MSI creation (Windows only)
- **Alternative**: [msitools](https://manpages.ubuntu.com/manpages/focal/man1/msi.1.html) for Linux
- **MSI SDK**: [Microsoft Windows Installer SDK](https://docs.microsoft.com/en-us/windows/win32/msi/windows-installer-portal)
