"""
Tom (Scanner.py v2)
--------------------
Reads a C source file, uses PyUtil.so to parse it correctly, then generates to files:
- generated_ctx.h - extern declarations + BUILD_CTX macro
- generated_ctx.c - Var registry + __attribute__((constructor))
Usage:
    python3 Tom.py <input.c>

Requirements
    pyutil.so must exist in the same directory
    Build it with: gcc -shared -fPIC -o pyutil.so PyUtil.c

The person using this never calls it directly - 
    make build runs it automaticallly before GCC.
"""

import ctypes
import sys
import os

#___________________________________________
# Step 1 - Load PyUtil.so
#___________________________________________

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def _load_pyutil():
    candidates = [
        os.path.join(SCRIPT_DIR, "pyutil.so"),
        os.path.join(SCRIPT_DIR, "pyutil.dll")
    ]
    for path in candidates:
        if os.path.exists(path):
            return ctypes.CDLL(path)
        print("ERROR: pyutil.so NOT FOUND. Build with:")  
        print("gcc -shared -fPIC -o pyutil.so Src/Utils/Python/PyUtil.c -I Src/Utils/Ver2 -Wall")
        print("or the dll here:")
        print("gcc -shared -o pyutil.dll Src/Utils/Python/PyUtil.c -I Src/Utils/Ver2 -Wall")
        sys.exit(1)
lib = _load_pyutil()


#___________________________________________
# Step 2 - Mirror C structs in python via ctypes
# These must match PyUtil.h
#___________________________________________

class PyUtilScope(ctypes.Structure):
    _fields_ = [
        ("depth", ctypes.c_int),
        ("in_block_comment", ctypes.c_int),
    ]

class PyUtilDecl(ctypes.Structure):
    _fields_ = [
        ("type,",           ctypes.c_char * 64),
        ("name,",           ctypes.c_char * 64),
        ("is_array",        ctypes.c_char * 64),
        ("is_struct",       ctypes.c_char * 64),
        ("is_enum",         ctypes.c_char * 64),
        ("array_size",      ctypes.c_char * 64),
    ]

#___________________________________________
# Step 3 - Declare function signatures
# Keeps Python from misinterpreting return types
#___________________________________________

lib.PyUtil_CreateScope.restype      =    PyUtilScope
lib.PyUtil_CreateScope.argtypes     =    []

lib.PyUtil_UpdateScope.restype      =    None
lib.PyUtil_UpdateScope.argtypes     =    [ctypes.POINTER(PyUtilScope), ctypes.c_char_p]

lib.PyUtil_IsGlobal.restype         =    ctypes.c_int
lib.PyUtil_IsGlobal.argtypes        =    [ctypes.POINTER(PyUtilScope), ctypes.c_char_p]

lib.PyUtil_ParseDecl.restype        =    ctypes.c_int
lib.PyUtil_ParseDecl.argtypes       =    [ctypes.c_char_p, ctypes.POINTER(PyUtilDecl)]

lib.PyUtil_NormalizeType.restype    =    ctypes.c_char_p
lib.PyUtil_NormalizeType.argtypes   =    [ctypes.c_char_p]

lib.PyUtil_EngineVersion.restype    =    ctypes.c_int
lib.PyUtil_EngineVersion.argtypes   =    []

#___________________________________________
# Step 4 - Type Map
# C type string -> (VAR_* tag, printf specifier)
#___________________________________________

TYPE_MAP = {
    "int":
    "float:"
}