"""
Pyutil.py - Python Wrapper for the PyUtil shared library.

Searches for pyutil.dll / pyutil.so by walking up from thi file's location, 
so it works regardless of where in the projects it's placed.

"""

import ctypes
import sys
import os
import re

import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

#---------------------------------------------------------------
#   Library Loader - Searches up the directory Tree
#---------------------------------------------------------------
def _find_lib() -> str:
    
    if sys.platform == "win32":
        name = "pyutil.dll"
    elif sys.platform == "darwin":
        name = "pyutil.dylib"
    else:
        name = "pyutil.so"

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
    type_name:  bytes # normalized C type
    name:       bytes # variable identifier
    is_array:   int   # 1 if int arr[5]
    is_struct:  int   # 1 if struct Foo bar
    is_enum:    int   # 1 if enum State s
    array_size: int   # N from arr[5], or -1 if not an array
    _fields_ = [
        ("type_name",       ctypes.c_char * 64),
        ("name",            ctypes.c_char * 64),
        ("is_array",        ctypes.c_int      ),
        ("is_struct",       ctypes.c_int      ),
        ("is_enum",         ctypes.c_int      ),
        ("array_size",      ctypes.c_int      ),
    ]

class PyUtilExpr(ctypes.Structure):
    """Output from PyUtil_ParseExpr. Represents arr[0], player->hp, enemy.pos."""
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

_lib.PyUtil_CreateScope.restype        =    PyUtilScope
_lib.PyUtil_CreateScope.argtypes       =    []

_lib.PyUtil_UpdateScope.restype        =    None
_lib.PyUtil_UpdateScope.argtypes       =    [ctypes.POINTER(PyUtilScope), ctypes.c_char_p]

_lib.PyUtil_IsGlobal.restype           =    ctypes.c_int
_lib.PyUtil_IsGlobal.argtypes          =    [ctypes.POINTER(PyUtilScope)]

_lib.PyUtil_ParseDecl.restype          =    ctypes.c_int
_lib.PyUtil_ParseDecl.argtypes         =    [ctypes.c_char_p, ctypes.POINTER(PyUtilDecl)]

_lib.PyUtil_NormalizeType.restype      =    ctypes.c_char_p
_lib.PyUtil_NormalizeType.argtypes     =    [ctypes.c_char_p]

_lib.PyUtil_ParseArrayExpr.restype     =    ctypes.c_int
_lib.PyUtil_ParseArrayExpr.argtypes    =    [ctypes.c_char_p, ctypes.POINTER(PyUtilExpr)]

_lib.PyUtil_ParseStructExpr.restype    =    ctypes.c_int
_lib.PyUtil_ParseStructExpr.argtypes   =    [ctypes.c_char_p, ctypes.POINTER(PyUtilExpr)]

_lib.PyUtil_ParseExpr.restype          =    ctypes.c_int
_lib.PyUtil_ParseExpr.argtypes         =    [ctypes.c_char_p, ctypes.POINTER(PyUtilExpr)]

_lib.PyUtil_IsValidIdentifier.restype  =    ctypes.c_int
_lib.PyUtil_IsValidIdentifier.argtypes =    [ctypes.c_char_p]

_lib.PyUtil_EngineVersion.restype      =    ctypes.c_int
_lib.PyUtil_EngineVersion.argtypes     =    []


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


#---------------------------------------------------------------
#   Python Native Tools
#   Everything below is pure Python - no ctypes, no C calls.
#   These are Helpers that make Tom.py stay clean.
#---------------------------------------------------------------

#---------------------------------------------------------------
#   Python Native - PyUtilPrint
#   Prints Contents With [PyUtil] 
#---------------------------------------------------------------

def PyUtilPrint(text: str, type: str):
    PyUtil_watermark: str = "[PyUtil]"
    Tom_watermark: str = "[Tom]"

    if type == "Tom":
        print(f"{Tom_watermark}: {text}")
    if type == "Py":
        print(f"{PyUtil_watermark}: {text}")
    
    


# #---------------------------------------------------------------
# Python Native - Type map
# Normalized C type -> (VAR_* tag, extern declaration type, pointer expression)

# pointer_expr controls how the address is taken in by generated_ctx.c:
# "&name" - standard variables
# "name" - arrays: name already decays to a pointer, & would give int(*)[N]
# #---------------------------------------------------------------

TYPE_MAP: dict[str, tuple[str, str, str]] = {
    "int":         ("VAR_INT",    "int",            "&{name}"),
    "float":       ("VAR_FLOAT",  "float",          "&{name}"),
    "const char*": ("VAR_STRING", "const char*",    "&{name}"),
    "char*":       ("VAR_STRING", "char*",          "&{name}"),
    "array":       ("VAR_ARRAY",  "",                "{name}"), # <- No Ampersands for arrrays(&) for arrays
    "struct":      ("VAR_STRUCT", "struct",         "&{name}"),
    "enum":        ("VAR_ENUM",   "enum",           "&{name}")
}




class VarInfo:
    """
    One global variable found by scan_file().
    Properties automatically generate correct C strings - Tom.py never 
    formats C syntax itself.
    """

    def __init__(
        self,
        type_name:          str,
        name:          str,
        compound_name: str = "",
        elem_type:     str = "",
        is_array:      bool = False,
        is_struct:     bool = False,
        is_enum:       bool = False,
        array_size:    int  = -1,

    ):
        self.type_name = type_name
        self.name = name
        self.compound_name = compound_name
        self.elem_type = elem_type;
        self.is_array  = is_array
        self.is_struct  = is_struct
        self.is_enum    = is_enum
        self.array_size = array_size

    @property
    def var_tag(self) -> str:
        key = "array" if self.is_array else self.type_name
        return TYPE_MAP.get(key, ("VAR_INT", "", "&{name}"))[0]

    @property
    def extern_decl(self) -> str:
        if self.is_array:
            sz = str(self.array_size) if self.array_size > 0 else ""
            return f"extern {self.elem_type} {self.name}[{sz}];"
        if self.is_struct:
            return f"extern struct {self.compound_name} {self.name};"
        if self.is_enum:
            return f"extern enum {self.compound_name} {self.name};"
        _, ext_type, _ = TYPE_MAP.get(self.type_name, ("VAR_INT", self.type_name, "&{name}")),
        return f"extern {ext_type} {self.name};"
    
    @property
    def var_ptr(self) -> str:
        key = "array" if self.is_array else self.type_name
        _, _, ptr_tpl = TYPE_MAP.get(key, ("VAR_INT", "", "&{name}"))
        expr = ptr_tpl.replace("{name}", self.name)
        return f"(void*){expr}"
    
    @property
    def registry_entry(self) -> str:
        """
        Fully generated Var[] entry.
            {"hp", VAR_INT, (void*)&hp }

        Prevent Tom.py from manually formatting registry lines.
        """
        return f'{{ "{self.name}", {self.var_tag}, {self.var_ptr} }},'

    
    @property
    def is_supported(self) -> bool:
        """
        Always True in v2 - all types are now supported.
        """
        return True
    

    def __repr__(self) -> str:
        return f"VarInfo({self.type_name!r}, {self.name!r})"


#---------------------------------------------------------------
# _extract_compound_name
# Python Native - extracts "Player" from "struct Player p = ..."
# PyUtil only gives us type="struct" and name="p", not the type name.
#---------------------------------------------------------------

_STRUCT_RE  = re.compile(r'^\s*struct\s+(\w+)\s+\w+')
_ENUM_RE    = re.compile(r'^\s*enum\s+(\w+)\s+\w+')
_ARRAY_RE   = re.compile(r'^\s*(int|float|char\*|const char\*)\s+\w+\s*\[')

def _extract_compound_name(line: str, kind: str) -> str:
    """Extract 'Player' from 'struct Player p;' or State from 'enum State s;'""" 
    pattern = _STRUCT_RE if kind == "struct" else _ENUM_RE
    m = pattern.match(line)
    return m.group(1) if m else "Unknown"

def _extract_elem_type(line: str) -> str:
    """Extract 'int' from 'int arr[10];'""" 
    m = _ARRAY_RE.match(line)
    return m.group(1).strip() if m else "int"

#---------------------------------------------------------------
# check_version
# Python Native - Compares runtime version against expected
#---------------------------------------------------------------

EXPECTED_ENGINE_VERSION: int = 1

def check_version() -> None:
    """
    Compares ENGINE_TOOL_VERSION from the _lib against Native EXPECTED_ENGINE_VERSION.
    """
    v =  PyUtil_EngineVersion()
    if v != EXPECTED_ENGINE_VERSION:
        PyUtilPrint(
            f"Warning: version mismatch.\n"
            f"Expected {EXPECTED_ENGINE_VERSION}, got {v}."
            f"Rebuild pyutil.dll/so after updating Utilsv2.h.",
            "Py"
        )

#---------------------------------------------------------------
# Python Native - scan_file
# The Full Scan loop in one call.
# Tom.py calls this instead of managing scope/decl/loop itself.
#---------------------------------------------------------------

def scan_file(path: str) -> list[VarInfo]:
    found: list[VarInfo] = []
    scope = PyUtil_CreateScope()
    decl = PyUtilDecl()

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            PyUtil_UpdateScope(scope, line)
                
            if not PyUtil_IsGlobal(scope):
                continue

            if not PyUtil_ParseDecl(line, decl):
                continue

            type_name = decl.type_name.decode()
            name   = decl.name.decode()

            #structs and enums need compound_name extracted from source line
            if decl.is_struct:
                found.append(VarInfo(
                    type_name = "struct",
                    name = name,
                    compound_name = _extract_compound_name(line, "struct"),
                    is_struct = True,
                ))

            elif decl.is_enum:
                found.append(VarInfo(
                    type_name = "enum",
                    name = name,
                    compound_name = _extract_compound_name(line, "enum"),
                    is_enum = True,
                ))
            
            elif decl.is_array:
                found.append(VarInfo(
                    type_name = "array",
                    name      = name,
                    elem_type =  _extract_elem_type(line),
                    is_array  =  True,
                    array_size=  decl.array_size,
                ))
            
            else:
                found.append(VarInfo(
                    type_name = type_name,
                    name      = name,
                ))
            
        return found
    




#---------------------------------------------------------------
# Python Native - scan_file
# Prints a scan result table.
#
#---------------------------------------------------------------

def report(vars: list[VarInfo], source_name: str) -> None:
    PyUtilPrint(f"Scanning {source_name}...", "Tom")
    for v in vars:
        detail = ""
        if v.is_struct or v.is_enum:
            detail = f"({v.compound_name})"
        elif v.is_array:
            sz = str(v.array_size) if v.array_size > 0 else "?"
            detail = f"{v.elem_type}[{sz}]"
        print(f" {v.type_name:<14} {v.name:<20} {detail:<16} -> {v.var_tag}")





#---------------------------------------------------------------
# Python Native - NativeLoader
# Cross Platform native Library Loader.
#---------------------------------------------------------------

class NativeLoader:
    """
    Cross-Platform native loader for PyUtil

        Automatically finds:
            pyutil.dll
            pyutil.so
            pyutil.dylib
        depending on the platform.
    """
    def __init__(self):
        self.loaded: bool
        self.library_path: str
        self.platform_name: str
        self.lib = None




    def _library_name(self) -> str:
        if sys.platform == "win32":
            return "pyutil.dll"
        elif sys.platform == "darwin":
            return "pyutil.dylib"
        return "pyutil.so"
    
    def _find_library(self) -> str:
        here = os.path.dirname(os.path.abspath(__file__))
        name = self._library_name()

        search = here

        for _ in range(8):
            candidate = os.path.join(search, name)

            if os.path.isfile(candidate):
                return candidate
            
            parent = os.path.dirname(search)

            if parent == search:
                break

            raise RuntimeError(
                PyUtilPrint(f"Could not locate '{name}'")
            )
            

    def load(self) -> "NativeLoader":
        if self.loaded:
            return self

        self.library_path = self._find_library()
        self.lib = ctypes.CDLL(self.library_path)
        self.loaded = True        
    
        return self


    def reload(self) -> None:
        self.loaded = False
        self.lib = None
        self.load()
        

    def has_symbol(self, name: str) -> bool:
        return hasattr(self.lib, name)
    
class PathResolver:

    def __init__(self):
        self.root = self.find_project_root()

    def find_project_root(self) -> str:
        here = os.path.dirname(os.path.abspath(__file__))
        search = here

        markers = [".git", "Src", "Generated"]

        for _ in range(10):
            
            for marker in markers:
                if os.path.exists(os.path.join(search, marker)):
                    return search
            
            parent = os.path.dirname(search)

            if parent == search:
                break

            search = parent

        return here
    
    def resolve_include(self, header:str) -> str:

        for root, _, files in os.walk(self.root):

            if header in files:
                return os.path.join(root, header)
            
        raise FileNotFoundError(header)
    
    def generated_path(self, filename: str) -> str:

        path = os.path.join(self.root, "Generated")

        os.makedirs(path, exist_ok=True)

        return os.path.join(path, filename)
    
    def build_path(self, filename: str) -> str:

        path = os.path.join(self.root, "Build")

        os.makedirs(path, exist_ok=True)

        return os.path.join(path, filename)
    

class SourceWatcher:

    """
    Live source watcher for automatic rescanning/regeneration.

    Designed for hot reload workflows and rapid iteration.
    """
    def __init__(self):
        self.watching: False

    def watch(self, path: str) -> None:


        ...

    def stop(self) -> None:
        """
        Stop Watching.
        """

    def on_change(self, changed_file: str) -> None:
        """
        Called when thw file changes
        """
        ...