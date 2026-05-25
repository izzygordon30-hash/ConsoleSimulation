#ifndef PYUTIL_H
#define PYUTIL_H

/**
 * RULE:
 * NO PyUtil_* function may be called without validating the version prior!
 * ## Caller MUST do:
 * `if (PyUtil_EngineVersion() != EXPECTED) abort;`
 * 
 * PyUtil answers exactly these questions about a C source file:
 *  - Are we in the Global Scope?
 *  - Is this line a variable declaration
 *  - What type is it?
 *  - What is its name?
 *  - Is it an array, struct or enum?
 *  - (V2) Is this a compound expression like arr[0] or player->hp
 * 
 * Important things to note:
 *  - All String Fields are:
 *      - Null Terminated
 *      -  truncated safely if input exceeds PYUTIL_NAME_MAX-1
 * - All parsing functions rely on PyUtil_IsValidIdentifier for validation.
 * 
 * 
 *  It does NOT:
 *     - Resolve memory addresses
 *     - Parse function bodies
 *     - Handle macros or Templates
 *     - Write any C output -> that's Tom's(scanner.py) job.
 * 
 * Used by scanner.py via ctypes:
 * 
 *      lib = ctypes.CDLL("./pyutil.so")
 *      scope = lib.PyUtil_CreateScope()
 *      lib.PyUtil_UpdateScope(ctypes.byref(scope), lines.encode())
 * 
 * Compile as shared library
 *  gcc -shared -fPIC -o pyutil.so PyUtil.c
*/

#include <stddef.h>
#include <stdint.h>




#define PYUTIL_NAME_MAX 64

/**
 * Shared Library export
*/
#if defined(_WIN32) || defined(_WIN64)
    #define PYUTIL_API __declspec(dllexport)
#else 
    #define PYUTIL_API __attribute__((visibility("default")))
#endif


/**
 * 
 * # NOTE: This Feature is currently uses a stub mode system reserved for future release.
 * -------------------------------------------------------------------------------------------
 * ## PyUtilLangMode
 * Controls parsing rules (future use).
 * 
 * CURRENT STATE:
 *  - All modes behave identically (C99 rules only)
 *
 * EXPECTATIONS:
 *  - CPP: May Support templates / overload hints
 *  - CUSTOM: user-defined parsing rules
 *      
 */
typedef enum {
    PYUTIL_LANG_C99,
    PYUTIL_LANG_CPP,
    PYUTIL_LANG_CUSTOM
} PyUtilLangMode;

/**
 * ## PyUtilScope
 * Tracks brace depth as PyUtil_UpdateScope is fed lines one at a time.
 * depth == 0 means global scope.
 */
typedef struct {
    int32_t depth; /** Current brace nesting level */
    int32_t in_block_comment; /** 1 while inside a block comment */
} PyUtilScope;


/**
 * ## PyUtilDecl
 * Output struct written by PyUtil_ParseDecl.
 * Strings are stored directly in the struct.
 */
typedef struct {
    char type_name[PYUTIL_NAME_MAX]; /** Normalized Type: "int", "float", "const char*" */
    char name[PYUTIL_NAME_MAX]; /** identifier: "hp, player_speed" */

    int32_t is_array; /** 1 if its an array */
    int32_t is_struct; /** 1 if struct Foo bar */
    int32_t is_enum; /** 1 if its an enum State s */
    int32_t array_size; /** N from arr[N], or -1 if unknown/not array */
} PyUtilDecl;

/**
 * ## PyUtilExpr
 * Output Struct written by PyUtil_ParseExpr
 */
typedef struct {
    char base[PYUTIL_NAME_MAX]; /** "arr", "player" */
    char key[PYUTIL_NAME_MAX]; /** "0", "hp" */

    int32_t is_array; /** 1 = arr[key] */
    int32_t is_struct; /** 1 means dot or arrow access */
    int32_t is_arrow; /** 1 only when operator is -> */
} PyUtilExpr;


#ifdef __cplusplus
extern "C" {
#endif

//======================================
// PyUtils API Version 1
//======================================


/**
 * ## Create A Scope Tracker
 * Call once per file before the line loop;
 * Returns a fully zero-initialized struct(all bytes are set to zero).
 */
PYUTIL_API PyUtilScope PyUtil_CreateScope(void);


/**
 * ## Feed a Line
 * Feed one line in the scope tracker.
 * Counts { and } correctly skipping any string literals and comments.
 * Call this for every line regardless for whether you parse it
*/
PYUTIL_API void PyUtil_UpdateScope(PyUtilScope* state, const char* line);


/**
 * ## Is Global Variable
 * Returns 1 if currently at global scope (depth == 0), 0 otherwise
*/
PYUTIL_API int32_t PyUtil_IsGlobal(const PyUtilScope* state);

/**
 * ## Parse Declaration
 * 
 * Return 1 on success, failure would mean it clears or resets the output(`out`)
 * 
 * Recognizes:
 * - int hp = 100;
 * - float speed = 3.5f;
 * - const char* name = "Bob";
 * - int arr[10];
 * - struct Player p;
 * - enum State s;
 * 
 * Does Not recognize:
 * function declarations (anything with '(' before ';' or '=')
 * typedefs
 * macros
*/
PYUTIL_API int32_t PyUtil_ParseDecl(const char* line, PyUtilDecl* out);

/**
 * ## Normalize Type
 * Normalize a C Type string into its correct form.
 * - "const char *" -> "const char*"
 * - "int"          -> "int"
 * - "float   "     -> "float"
 * This Always writes a null-terminated string into the parameter `out` on success
 * On failure, it writes an empty string "" and returns 0.
 */
PYUTIL_API int32_t PyUtil_NormalizeType(const char* type, char* out, size_t out_size);

//======================================
// PyUtils API Version 2
//======================================


/**
 * ## Parse an Array Expression
 * parse an array access token: "arr[0]", "values[i]"
 * Return 1 on success, failure would mean the token did not match.
 */
PYUTIL_API int32_t PyUtil_ParseArrayExpr(const char* token, PyUtilExpr* out);


/**
 * ## Parse a Struct Expression
 * parse a struct access token: "player->hp", "enemy.pos"
 * Return 1 on success, failure would mean the token did not match.
 */
PYUTIL_API int32_t PyUtil_ParseStructExpr(const char* token, PyUtilExpr* out);

/**
 * ## Parse a supported Expression
 * Tries struct access first, then array access, then plain identifier.
 * Return 1 on success, failure would mean it clears or resets the output(`out`)
 */
PYUTIL_API int32_t PyUtil_ParseExpr(const char* token, PyUtilExpr* out);

/**
 * # NOTE: This Feature is currently uses a stub mode system reserved for future release.
 * -------------------------------------------------------------------------------------------
 * ## IsValidIdentifier
 * Validates identifiers.
 * - PyUtilLangMode Is currently ignored(reserved for future rule changes.)
 *  C99 Rules:
 *  - First Char: [A-Z a-z _].
 *  - Next: [A-Z a-z 0-9 _].
 *  - ASCII only (no unicode $, @, etc...).
 * 
 * CPP/CUSTOM
 * - Currently Act Identical to C99.
 */
PYUTIL_API int32_t PyUtil_IsValidIdentifier(const char* str, PyUtilLangMode mode);

/**
 * NOTE: Refer to first Rule at Top
 * 
 * ## Engine Tool Version 
 * Returns the ENGINE_TOOL_VERSION this PyUtil was built against.
 * scanner.py checks this at startup to detect API drift.
 */
PYUTIL_API int32_t PyUtil_EngineVersion(void);

#ifdef __cplusplus
}
#endif

#endif // End of PYUTIL_H