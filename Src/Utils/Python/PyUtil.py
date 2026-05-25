"""
Pyutil.py - Python Wrapper for the PyUtil shared library.

Searches for pyutil.dll / pyutil.so by walking up from thi file's location, 
so it works regardless of where in the projects it's placed.

"""

import ctypes
import sys
import os

#---------------------------------------------------------------
#   Library Loader - Searches up the directory Tree
#---------------------------------------------------------------

def _find_lib() -> str:
    name = "pyutil.dll" if sys.platform == "win32" else "pyutil.so"
    here = os.path.dirname(os.path.abspath(__file__))

    #Walk up from Python/ towards ConsoleSimulation
    search = here
    for _ in range(6):
        candidate = os.path.join(search, name)
        if os.path.isfile(candidate):
            return candidate
        search = os.path.dirname(search)
    
    raise RuntimeError(
        f"[PyUtil] Could not find '{name}' in any parent directory of: \n"
        f"{here}\n"
        f"Build it first:\n"
        f" Windows: gcc -shared -o pyutil.dll Src\Utils\PyUtils\PyUtil.c -I Src/Utils/Ver2 -Wall"
        f" Linux:   gcc -shared -fPIC -o pyutil.so Src\Utils\PyUtils\PyUtil.c -I Src/Utils/Ver2 -Wall"
    )

_lib = ctypes.CDLL(_find_lib())

#---------------------------------------------------------------
#   Structures
#---------------------------------------------------------------

class PyUtilScope(ctypes.Structure):
    """Tracks Brace Depth. depth == 0 means global scope"""
    depth: int
    in_block_comment: int
    _fields_ = [
        ("depth",             ctypes.c_int),
        ("in_block_comment", ctypes.c_int),
    ]

class PyUtilDecl(ctypes.Structure):
    """Output from PyUtil_ParseDecl. type and name are bytes - call .decode()."""
    type:       bytes # normalized C type
    name:       bytes # variable identifier
    is_array:   int   # 1 if int arr[5]
    is_struct:  int   # 1 if struct Foo bar
    is_enum:    int   # 1 if enum State s
    array_size: int   # N from arr[5], or -1 if not an array
    _fields_ = [
        ("type",           ctypes.c_char * 64),
        ("name",           ctypes.c_char * 64),
        ("is_array",        ctypes.c_int      ),
        ("is_struct",       ctypes.c_int      ),
        ("is_enum",         ctypes.c_int      ),
        ("array_size",      ctypes.c_int      ),
    ]

class PyUtilExpr(ctypes.Structure):
    """Output from PyUtil_ParseExpr. Respresents arr[0], player->hp, enemy.pos."""
    base: bytes # root identifier
    key:  bytes # field name or array index
    is_array:  int # 1 = arr[key]
    is_struct: int # 1 = base->key or base.key
    is_arrow:  int # 1 = -> 0 = .
    _fields_ = [
        ("base",           ctypes.c_char * 64),
        ("key",            ctypes.c_char * 64),
        ("is_array",        ctypes.c_int      ),
        ("is_struct",       ctypes.c_int      ),
        ("is_arrow",        ctypes.c_int      ),
    ]

#---------------------------------------------------------------
#   Return Types
#---------------------------------------------------------------

_lib.PyUtil_CreateScope.restype       =    PyUtilScope
_lib.PyUtil_UpdateScope.restype       =    None
_lib.PyUtil_IsGlobal.restype          =    ctypes.c_int
_lib.PyUtil_ParseDecl.restype         =    ctypes.c_int
_lib.PyUtil_NormalizeType.restype     =    ctypes.c_char_p
_lib.PyUtil_ParseArrayExpr.restype    =    ctypes.c_int
_lib.PyUtil_ParseStructExpr.restype   =    ctypes.c_int
_lib.PyUtil_ParseExpr.restype         =    ctypes.c_int
_lib.PyUtil_IsValidIdentifier.restype =    ctypes.c_int
_lib.PyUtil_EngineVersion.restype     =    ctypes.c_int

#---------------------------------------------------------------
#   V1 - Typed Wrappers
#---------------------------------------------------------------

def PyUtil_CreateScope() -> PyUtilScope:
    """Create a fresh new scope tracker. Call once per file before the line loop"""
    return _lib.PyUtil_CreateScope()

def PyUtil_UpdateScope(state: PyUtilScope, line: str) -> None:
    """Feed one line into the scope tracker. Call for EVERY line"""
    _lib.PyUtil_UpdateScope(ctypes.byref(state), line.encode())

def PyUtil_IsGlobal(state: PyUtilScope) -> bool:
    """Returns True if currently at global scope (depth == 0)."""
    return bool(_lib.PyUtil_IsGlobal(ctypes.byref(state)))


def PyUtil_ParseDecl(line: str, out: PyUtilDecl) -> bool:
    """Try to parse a variable declaration. Return True and fills out on success"""
    return bool(_lib.PyUtil_ParseDecl(line.encode(), ctypes.byref(out)))


def PyUtil_NormalizeType(type_str: str) -> str:
    """Normalize a C type: 'const char*', 'float' -> 'float'. """
    result = _lib.PyUtil_NormalizeType(type_str.encode())
    return result.decode() if result else ""

#---------------------------------------------------------------
#   V2 - Expression parser wrappers
#---------------------------------------------------------------

def PyUtil_ParseArrayExpr(token: str, out: PyUtilExpr) -> bool:
    """Parse an array access token: 'arr[0]', 'values[i]'. """
    return bool(_lib.PyUtil_ParseArrayExpr(token.encode(), ctypes.byref(out)))

def PyUtil_ParseStructExpr(token: str, out: PyUtilExpr) -> bool:
    """Parse an struct access token: 'arr[0]', 'values[i]'. """
    return bool(_lib.PyUtil_ParseStructExpr(token.encode(), ctypes.byref(out)))

def PyUtil_ParseExpr(token: str, out: PyUtilExpr) -> bool:
    """Parse any expression: struct, array, or plain indentifier"""
    return bool(_lib.PyUtil_ParseExpr(token.encode(), ctypes.byref(out)))

def PyUtil_IsValidIdentifier(s: str) -> bool:
    """Return True if s is a valid C identifier"""
    return bool(_lib.PyUtil_IsValidIdentifier(s.encode()))

def PyUtil_EngineVersion() -> int:
    """Returns ENGINE_TOOL_VERSION the library was built against"""
    return int(_lib.PyUtil_EngineVersion())

