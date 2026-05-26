'''
PyUtil.pyi - Type Stub for PyUtil.py
---------------------------------------------
So Intellisense can recognize my file and gives me 
    - AutoComplete: So I can make less typos in the .py
    - Hover Docs
    - Type checking
'''


class PyUtilScope:
    """
    Tracks brace depth as lines are fed through PyUtil_UpdateScope.
    depth == 0 means global scope.
    """
    depth:            int # current brace nesting level
    in_block_comment: int # 1 while inside a block comment

class PyUtilDecl:
    """
    Output written by PyUtil_ParseDecl on a successful parse.
    type and name are bytes - call .decode() to get str.

    Examples after decode:
        type_name: "int" | "float" | "const char*" | "struct" | "enum" |
        name: "hp" | "player_speed" | "name"
    """
    type_name:  bytes # normalized C type
    name:       bytes # variable identifier
    compound_type: bytes
    is_array:   int   # 1 if int arr[5]
    is_struct:  int   # 1 if struct Foo bar
    is_enum:    int   # 1 if enum State s
    array_size: int   # N from arr[5], or -1 if not an array

class PyUtilExpr:
    """
    Output written by PyUtil_ParseExpr on a successful parse.

    Compound token examples:
        arr[0]         -> base=b"arr",     key=b"0",   is_array=1
        player->hp     -> base=b"player",  key=b"hp",  is_struct=1, is_arrow=1
        enemy.pos      -> base=b"enemy",   key=b"pos", is_struct=1, is_arrow=0
        hp             -> base=b"hp",      key=b"",    plain identifier
    """
    base: bytes # root identifier
    key:  bytes # field name or array index
    is_array:  int # 1 = arr[key]
    is_struct: int # 1 = base->key or base.key
    is_arrow:  int # 1 = -> 0 = .

#---------------------------------------------------------------
#   V1 - Scope Tracking
#---------------------------------------------------------------

def PyUtil_CreateScope() -> PyUtilScope:
    """
    Create a fresh scope tracker.
    Call once per file, before the line loop.

        scope = PyUtil_CreateScope()
    """
    ...

def PyUtil_UpdateScope(state: PyUtilScope, line: str) -> None:
    """
    Feed one line into the scope tracker.
    Counts { and } correctly - skips literals and comments.
    Call this for Every line regardless of whether you parse it.

        for line in file:
            PyUtil_UpdateScope(scope, line)
    """
    ...

def PyUtil_IsGlobal(state: PyUtilScope) -> bool:
    """
    Returns True if currently at global scope (depth == 0).
        if PyUtil_IsGlobal(scope):
            #safe to call PyUtil_ParseDecl here
    """
    ...

def PyUtil_ParseDecl(line: str, out: PyUtilDecl) -> bool:
    """
    Parse Declaration
        On Success: fills *out and returns 1
        On failure: return 0, *out is unchanged.

    Recognizes:

        int hp = 100;
        float speed = 3.5f;
        const char* name = "Bob";
        int arr[10];
        struct Player p;
        enum State s;

    Does Not recognize:
        function declarations (anything with '(' before ';' or '=')
        typdefs
        macros

        decl - PyUtilDecl()
        if PyUtil_ParseDecl(line, decl):
            print(decl.type_name.decode(), decl.name.decode())
    """
    ...

def PyUtil_NormalizeType(type_str: str) -> str:
    """
    
    Normalize Type
    Normalize a C Type string into its correct form.
    - "const char *" -> "const char*"
    - "int"          -> "int"
    - "float   "     -> "float"
    Returns str - no need to decode
 
    """
    ...

#---------------------------------------------------------------
#   V2 - Expression parser wrappers
#---------------------------------------------------------------

def PyUtil_ParseArrayExpr(token: str, out: PyUtilExpr) -> bool:
    """
    Parse an Array Expression
        parse an array access token: "arr[0]", "values[i]"
        Return True and fills out on success.

            expr = PyUtilExpr()
            if PyUtil_ParseArrayExpr("arr[0]", expr):
                print(expr.base.decode(), expr.key.decode()) # "arr", "0"

    """
    ...

def PyUtil_ParseStructExpr(token: str, out: PyUtilExpr) -> bool:
    """
        Parse a Struct Expression
        parse a Struct access token: "player->hp", "enemy.pos"
        Return True and fills out on success.

            expr = PyUtilExpr()
            if PyUtil_ParseStructExpr("player->hp", expr):
                print(expr.base.decode(), expr.key.decode()) # "player", "hp"
                print(expr.is_arrow) #1
    """
    ...

def PyUtil_ParseExpr(token: str, out: PyUtilExpr) -> bool:
    """

    Parse a supported Expression
        Tries struct access first, then array access, then plain identifier.
        Return 1 on success, 0 on failure.

        expr = PyUtilExpr()
        if PyUtil_ParseExpr("player->hp", expr):
            ...
    """
    ...

def PyUtil_IsValidIdentifier(s: str) -> bool:
    """
    Is Valid Identifier
        Return 1 if the string is valid C identifier, 0 otherwise. 
        Valid: starts with the letter or '_', contains only [a-zA-Z0-9_]
    """
    ...

def PyUtil_EngineVersion() -> int:
    """
    Engine Tool Version 
        Returns the ENGINE_TOOL_VERSION this PyUtil was built against.
        Tom.py checks this at startup to catch API drift between Utilsv2.h
        and the compiled library.
    """
    ...

#---------------------------------------------------------------
#   Python Native Tools
#---------------------------------------------------------------

EXPECTED_ENGINE_VERSION: int

TYPEMAP: dict[str, tuple[str, str, str]]
"""
Maps normalized C type -> (VAR_* tag, extern type string, pointer expression template).

"int" ->         ("VAR_INT",    "int",            "&{name}")
"float" ->       ("VAR_FLOAT",  "float",          "&{name}")
"const char*" -> ("VAR_STRING", "const char*",    "&{name}")
"array" ->       ("VAR_ARRAY",  "",                "{name}") <- No Ampersands for arrrays(&) for arrays
"struct" ->      ("VAR_STRUCT", "struct",         "&{name}")
"enum" ->        ("VAR_ENUM",   "enum",           "&{name}")

"""

class VarInfo:
    """
    One global variable found by scan_file().

    Properties automatically generate correct C strings - Tom.py never 
    formats C syntax itself.
    """
    base_type: str # int | "float" | "const char*" | "array" | "struct" | "enum"
    name: str # variable identifier: "hp", "speed", "p"
    compound_name: str # struct/enum type_name: "Player", "State" - empty for primitives
    elem_type: str
    is_array: bool
    is_struct: bool
    is_enum: bool
    array_size: int # N from arr[N], -1 if unknown

    def __init__(
        self,
        base_type: str, 
        name: str, 
        compound_name: str = ... , 
        elem_type: str = ..., 
        is_array:  bool  = ...,
        is_struct: bool = ..., 
        is_enum: bool = ..., 
        array_size: int   = ...,
    ) -> None:
        ...
    
    @property
    def var_tag(self) -> str:
        """
        VAR_ *tag for the C Var[] entry.

        "int"    → "VAR_INT"
        "array"  → "VAR_ARRAY"
        "struct" → "VAR_STRUCT"
        "enum"   → "VAR_ENUM"
        """
        ...

    @property
    def extern_decl(self) -> str:
        """
        Full extern declaration for generated_ctx.h.

            int hp           -> extern int hp;
            int arr[10]      -> extern int arr[10];
            struct Player p  -> struct Player p;
            enum State s     -> extern enum State s;
        """
        ...

    @property
    def var_ptr(self) -> str:
        """
        Pointer Expression for the Var[] entry in generated_ctx.c.

            int hp -> (void*)&hp
            int arr -> (void*)arr  <- no & - array decay to pointer 
        """
        ...

    @property
    def registry_entry(self) -> str:
        """
        Fully generated Var[] entry.
            {"hp", VAR_INT, (void*)&hp }

        Prevent Tom.py from manually formatting registry lines.
        """
        ...

    @property
    def is_supported(self) -> bool:
        """
        Always True in v2 - all types are now supported.
        """
        ...

  



def check_version() -> None:
    """
    Compare ENGINE_TOOL_VERSION in the loaded library against EXPECTED_ENGINE_VERSION.
    prints a warning on mismatch. Does not raise.
    """
    ...

def scan_file(path: str) -> list[VarInfo]:
    """
    Scan a C source file and return every global variable declaration.

    Handles: int, float, const char*, char*, arrays, structs, enums.
    PyUtil handles parsing. This function handles the loop and VarInfo construction.

        vars = scan_file("main.c")
        for v in vars:
            print(v.extern_decl)
    """
    ...

def report(vars: list[VarInfo], source_name: str) -> None:
    """
    Print a formatted scan report to stdout.

        [Tom] Scanning main.c
            int    hp    -> VAR_INT
            float  speed -> VAR_FLOAT
            struct p     -> VAR_STRUCT
            array  arr   -> VAR_ARRAY
    """
    ...
    
class NativeLoader:
    """
    Cross-Platform native loader for PyUtil

        Automatically finds:
            pyutil.dll
            pyutil.so
            pyutil.dylib
        depending on the platform.
    """
    loaded: bool
    library_path: str
    platform_name: str

    def load(self) -> "NativeLoader":
        """
        Load the native PyUtil library.
        Safe to call multiple times.
        """
        ...

    def reload(self) -> None:
        """
        Force reload the library from disk.
        Useful during development/hot reload
        """
        ...

    


    def has_symbol(self, name: str) -> bool:
        """
        Return True if exported C symbol exists.
        """
        ...

class PathResolver:
    """
    Resolves project-relative paths automatically.

    Prevents hardcoded:
        Src/
        include/
        generated/
        build/
    """

    root: str

    
    def find_project_root(self) -> str:
        """
        Locate project root automatically
        """
        ...

    def resolve_include(self, header: str) -> str:
        """
        Find a header anywhere in the project.
            resolve_include("Utilsv2.h")    
        """
        ...

    def generated_path(self, filename: str) -> str:
        """
        Return path inside generated output directory.
        """
        ...

    def build_path(self, filename: str) -> str:
        """
        Return path inside build directory.   
        """
        ...

class CodeGen:

    """
    High-Level C code Generation helper.

    Prevents manual line.append spam.
    """

    lines: list[str]

    def newline(self, text: str = "") -> None:
        """
        Add a line to the output
        """
        ...

    def include(self, header: str) -> None:
        """
        Emit #include.
        """

    def begin_array(self, signature: str) -> None:
        """
        Begin a C array block.
        """
        ...
    
    def end_block(self, suffix: str = "") -> None:
        """
        Close current code block.
        """
        ...

    def comment(self, text: str) -> None:
        """
        Write a comment wrapped in /** */
        """
        ...
    
    def emit_var_registry(self, var: list[VarInfo]) -> None:
        """
        Emit Var _VARS[] automatically.
        """
        ...

    def scan_text(source: str) -> list[VarInfo]:
        """
        Scans The Source.
        """
        ...

    def emit_context_builder(self) -> None:
        """
        Emit BUILD_CTX macro automatically.
        """
        ...
    
    def write(self, path: str) -> None:
        """
        Write generated output to disk.
        """
        ...

class SourceWatcher:

    """
    Live source watcher for automatic rescanning/regeneration.

    Designed for hot reload workflows and rapid iteration.
    """

    watching: bool

    def watch(self, path: str) -> None:
        """
        Begin watching a file or directory.
        """
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