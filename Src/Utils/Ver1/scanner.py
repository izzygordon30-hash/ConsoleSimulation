"""
scanner.py - Tom
-------
Scans a C source file for top-level variable declarations and generates two files:
    - generated_ctx.h - extern declarations + ContextBuilder macro
    - generated_ctx.c - Var[] array with type tags and live pointers

Usage:
    - python scanner.py <input.c>

Outputs:
    generated_ctx.h
    generated_ctx.c

Notice: 
    This is a heuristic(quick or shallow) scanner (NOT a full C parser).
    A project for another day lol :)
"""

import re
import sys
import os

# =========================================
# ### Type Map
# C type String -> (VAR_* tag, printf hint)
# =========================================
TYPE_MAP = {
    "int":  ("VAR_INT", "%d"),
    "float":  ("VAR_FLOAT", "%f"),
    "const char*":  ("VAR_STRING", "%s"),
    "char*":  ("VAR_STRING", "%s")
}

# Regex: matches int hp = ... pr const char* name = ...
PATTERN = re.compile(
    r'^\s*'
    r'(int|float|const char\s*\*|char\s*\*)' #group 1: type
    r'\s+'
    r'(\w+)'                    #group 2: variable name
    r'\s*(=|;)'
)


def normalized_type(t: str) -> str:
    """Remove spaces for consistent matching"""
    return t


def scan(path: str):
    """Returns list of (c_type, var_name) tuples found in path"""
    found = []
    brace_depth = 0

    with open(path, "r") as f:
        for line in f:

            #crude scope tracking
            brace_depth += line.count("{")
            brace_depth -= line.count("}")

            # only accept GLOBAL scope variables
            if brace_depth != 0:
                continue

            m = PATTERN.search(line)
            if not m:
                continue
            
            c_type = normalized_type(m.group(1))
            name = m.group(2)

            if c_type not in TYPE_MAP:
                print(f"[WARN] unsupported type: {m.group(1)}")
                continue
            
            found.append((c_type, name))

    return found;

def emit_header(vars: list[tuple[str, str]], out_path: str, source_name: str):
    lines = [] 
    lines.append("#pragma once")
    lines.append('#include "Utils/Ver1/Utils.h"')
    lines.append("")
    lines.append(f"/* Auto Made By Tom from scanner.py from {source_name} -- DO NOT EDIT HIS WORK */")
    lines.append("")

    # restore readable type for header
    for c_type, name in vars:
        if c_type == "int":
            t = "int"
        elif c_type == "float":
            t = "float"
        else:
            t = "const char*"

        lines.append(f"extern {t} {name};")
    
    lines.append("")
    lines.append("extern Var   _VARS[];")
    lines.append("extern int   _VAR_COUNT;")
    lines.append("")

    # Convenience Macro - Builds a Context on the Stack, no malloc needed
    lines.append("/* Usage: BUILD_CTX(my_ctx); then pass &my_ctx to core_print */")
    lines.append("#define BUILD_CTX(name) \\")
    lines.append("  Context name = {_VARS, _VAR_COUNT}")

    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    
def emit_source(vars: list[tuple[str, str]], out_path: str, header_name: str):
    lines = []
    lines.append(f'#include "{header_name}"')
    lines.append(f'#include <stdint.h>')
    lines.append("")
    lines.append(f"/* Auto Made By Tom from scanner.py -- DO NOT EDIT HIS WORK */")
    lines.append("")
    lines.append("Var _VARS[] = {")

    for c_type, name in vars:
        tag, _ = TYPE_MAP[c_type]
        ptr = f"(void*)(uintptr_t)&{name}"
        lines.append(f' {{"{name}", {tag}, {ptr} }},')
    
    lines.append("};")
    lines.append("")
    lines.append(f"int _VAR_COUNT = {len(vars)};")

    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    
def main():
    if len(sys.argv) != 2:
        print("Usage: python scanner.py <input.c>")
        sys.exit(1)
    
    source = sys.argv[1]
    if not os.path.exists(source):
        print(f"Error: {source} not found")
        sys.exit(1)

    vars = scan(source)

    if not vars:
        print("No supported varables found (int/ float / const char*).")
        sys.exit(0)
    emit_header(vars, "generated_ctx.h", os.path.basename(source))
    emit_source(vars, "generated_ctx.c", "generated_ctx.h")

    print(f"scanned {source}:")
    for c_type, name in vars:
        tag, fmt = TYPE_MAP[c_type]
        print(f"    {c_type:<12} {name:<12} -> {tag}")
    print(f"\nWrote: generated_ctx.h")
    print("Wrote: generated_ctx.c")

if __name__ == "__main__":
    main()