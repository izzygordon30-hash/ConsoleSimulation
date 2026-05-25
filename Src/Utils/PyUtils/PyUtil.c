#include "PyUtil.h"
#include "Utilsv2.h"   /* ENGINE_TOOL_VERSION */
 
#include <string.h>
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>

//
// Internal Helpers
//

/**
 * ## Trim
 * Trim leading and trailing whitespace into dest (safe, null-terminates)
 */
static void trim(const char* src, char* dest, size_t dest_size) {
    while (*src && isspace((unsigned char)*src)) src++;

    const char* end = src + strlen(src);

    while (end > src && isspace((unsigned char)*(end - 1))) end--;

    size_t len = (size_t)(end - src);

    if (len >= dest_size) len = dest_size - 1;

    memcpy(dest, src, len);

    dest[len] = '\0';
}

/**
 * ## Copy Source Code into destination
 * Capped at dest_size - 1 always null-terminates
 */
static void safe_copy(char* dest, const char* src, size_t dest_size) {
    size_t len = strlen(src);
    if (len >= dest_size) len = dest_size - 1;
    memcpy(dest, src, len);
    dest[len] = '\0';
}

//========================================================
// Known primitive types PyUtil recognizes 
// Checked in order - put longer prefixes first to avoid "int"
// matching before "int *" etc.
//=========================================================

static const struct {
    const char* raw;
    const char* normalized;
} KNOWN_PRIMITIVES[] = {
    {"const char *", "const char*"},
    {"const char*",  "const char*"},
    {"char *",       "char*"      },
    {"char*",        "char*"      },
    {"float",        "float"      },
    {"int",          "int"        },
};
static const int KNOWN_PRIMITIVE_COUNT = 
    (int)(sizeof(KNOWN_PRIMITIVES) / sizeof(KNOWN_PRIMITIVES[0]));


// ================================================================
// V1 — Scope tracking
// =================================================================

PYUTIL_API PyUtilScope PyUtil_CreateScope(void) {
    PyUtilScope s;
    s.depth = 0;
    s.in_block_comment = 0;
    return s;
}

PYUTIL_API void PyUtil_UpdateScope(PyUtilScope* state, const char* line){
    if(!state || !line ) return;

    const char* p = line;
    int in_string = 0;
    int in_char   = 0;

    while (*p) {

        /* Exit block comment */
        if (state->in_block_comment){
            if(*p == '*' && *(p + 1) == '/') {
                state->in_block_comment = 0;
                p += 2;
            } else {
                p++;
            }
            continue;
        }

        /* Enter Block Comment */
        if (!in_string && !in_char && *p == '/' && *(p + 1) == '*') {
            state->in_block_comment = 1;
            p += 2;
            continue;
        }

        /* Line comment - stop processing this line */
        if (!in_string && !in_char && *p == '/' && *(p + 1) == '/') {
            break;
        }

        /* String literal toggle */
        if (*p == '"' && !in_char) {
            if (!in_string) {
                in_string = 1;
            } else if (*(p - 1) != '\\'){
                in_string = 0;
            }
            p++;
            continue;
        }

        /* Char literal toggle */
        if (*p == '\'' && !in_string) {
            if (!in_char) {
                in_char = 1;
            } else if (*(p - 1) != '\\'){
                in_char = 0;
            }
            p++;
            continue;
        }

        /* Only Count Braces outside outside string/char literals */
        if (!in_string && !in_char) {
            if      (*p == '{') state->depth++;
            else if (*p == '}') { if (state->depth > 0) state->depth--; }
        }
        p++;
    }
}

PYUTIL_API int32_t PyUtil_IsGlobal(const PyUtilScope* state) {
    if (!state) return 0;
    return state->depth == 0;
}


// ================================================================
// V1 — Declaration parsing
// =================================================================

PYUTIL_API int32_t PyUtil_ParseDecl(const char* line, PyUtilDecl* out){
    if (!line || !out) return 0;

    char trimmed[256];
    trim(line, trimmed, sizeof(trimmed));

    /* Skip Blank lines, preprocessors*/
    const char* paren = strchr(trimmed, '(');
    const char* eq    = strchr(trimmed, '=');
    const char* semi  = strchr(trimmed, ';');
    if (paren && (!eq || paren < eq) && (!semi || paren < semi)) return 0;

    /* _____ struct Foo Name ... ____*/
    if (strncmp(trimmed, "struct ", 7) == 0) {
        const char* after_struct = trimmed + 7;
        const char* name_start   = strchr(after_struct, ' ');
        if (!name_start) return 0;
        name_start++;
        char name_buf[64];
        int i = 0;
        while (name_start[i] && (isalnum((unsigned char)name_start[i]) || name_start[i] == '_')) i++;
        if (i == 0) return 0;
        safe_copy(name_buf, name_start, (size_t)i + 1);
        safe_copy(out->type_name, "struct", sizeof(out->type_name));
        safe_copy(out->name, name_buf, sizeof(out->name));
        out->is_struct  = 1;
        out->is_array   = 0;
        out->is_enum    = 0;
        out->array_size = -1;
        return 1;
    }

    /* _____ enum state name ... ____*/
    if (strncmp(trimmed, "enum ", 5) == 0) {
        const char* after_enum = trimmed + 5;
        const char* name_start   = strchr(after_enum, ' ');
        if (!name_start) return 0;
        name_start++;
        char name_buf[64];
        int i = 0;
        while (name_start[i] && (isalnum((unsigned char)name_start[i]) || name_start[i] == '_')) i++;
        if (i == 0) return 0;
        safe_copy(name_buf, name_start, (size_t)i + 1);
        safe_copy(out->type_name, "enum", sizeof(out->type_name));
        safe_copy(out->name, name_buf, sizeof(out->name));
        out->is_enum    = 1;
        out->is_struct  = 0;
        out->is_array   = 0;
        out->array_size = -1;
        return 1;
    }

    /*____Primitive types____*/
    for (int i = 0; i < KNOWN_PRIMITIVE_COUNT; i++) {
        const char* raw = KNOWN_PRIMITIVES[i].raw;
        size_t raw_len = strlen(raw);

        if (strncmp(trimmed, raw, raw_len) != 0) continue;

        /* Character after the type must be space, *, or end-of-type*/
        char next = trimmed[raw_len];
        if (next != ' ' && next != '\0' && next != '*') continue;

        /* Skip spaces and stars after the type to find the identifier*/
        const char* p = trimmed + raw_len;
        while (*p == ' ' || *p == '*') p++;
        if (!*p) continue;
        
        char name_buf[64];
        int nlen = 0;

        while (p[nlen] && (isalnum((unsigned char)p[nlen]) || p[nlen] == '_'))
        nlen++;

        if (nlen == 0) continue;
        safe_copy(name_buf, p, (size_t)nlen + 1);

        /* Check for array brackets: name[N]*/
        int is_arr = 0;
        int arr_sz = -1;

        const char* bracket = strchr(p + nlen, '[');
        if (bracket) {
            is_arr = 1;
            arr_sz = atoi(bracket + 1);
        }

        safe_copy(out->type_name, KNOWN_PRIMITIVES[i].normalized, sizeof(out->type_name));
        safe_copy(out->name, name_buf, sizeof(out->name));
        out->is_array   = is_arr;
        out->array_size = arr_sz;
        out->is_enum    = 0;
        out->is_struct  = 0;
        return 1;
    }
    return 0; /* No match */
}

PYUTIL_API int32_t PyUtil_NormalizeType(const char* type, char* out, size_t out_size){
    if (!type || !out || out_size == 0) return 0;

    out[0] = '\0';

    /* Check known primitives table first*/
    for (int i = 0; i < KNOWN_PRIMITIVE_COUNT; i++) {
        if (strcmp(type, KNOWN_PRIMITIVES[i].raw) == 0) {
            safe_copy(out, KNOWN_PRIMITIVES[i].normalized, out_size);
            return 1;
        }
    }

    /* Generic: trim whitespace and collapse  "   *" into "*" */
    char tmp[PYUTIL_NAME_MAX];
    trim(type, tmp, sizeof(tmp));

    /* Collapse " *" -> "*" */
    char* star = strstr(tmp, " *");

    while (star) {
        memmove(star, star + 1, strlen(star));
        star = strstr(tmp, " *");
    }

    safe_copy(out, tmp, out_size);

    return 1;
} 

// ================================================================
// V2 — Expression parsing
// =================================================================
 
PYUTIL_API int32_t PyUtil_IsValidIdentifier(const char* str, PyUtilLangMode mode){
    if (!str || !*str) return 0;
    if (!isalpha((unsigned char)*str) && *str != '_') return 0;
    for (const char* p = str + 1; *p; p++)
        if (!isalnum((unsigned char)*p) && *p != '_') return 0;
    return 1;
}

PYUTIL_API int32_t PyUtil_ParseArrayExpr(const char* token, PyUtilExpr* out) {
    if (!token || !out) return 0;

    /* Expect identifier[key] */
    const char* bracket_open = strchr(token, '[');
    const char* bracket_close = strchr(token, ']');
    
    if (!bracket_open || !bracket_close || bracket_close < bracket_open) return 0;

    /* Extract base identifier*/
    int base_len = (int)(bracket_open - token);
    if (base_len <= 0 || base_len >= 64) return 0;

    char base[64];
    safe_copy(base, token, (size_t)base_len + 1);
    if (!PyUtil_IsValidIdentifier(base, PYUTIL_LANG_C99)) return 0;

    /* Extract key*/
    int key_len = (int)(bracket_close - bracket_open - 1);
    if (key_len <= 0 || key_len >= 64) return 0;

    char key[64];
    safe_copy(key, bracket_open + 1, (size_t)key_len + 1);

    safe_copy(out->base, base, sizeof(out->base));
    safe_copy(out->key, key, sizeof(out->key));
    out->is_array = 1;
    out->is_struct = 0;
    out->is_arrow = 0;
    return 1;
}

PYUTIL_API int32_t PyUtil_ParseStructExpr(const char* token, PyUtilExpr* out){
    if (!token || !out) return 0;

    /* Expect identifier[key] */
    const char* arrow = strstr(token, "->");
    
    if (arrow) { 
        int base_len = (int)(arrow - token);
        int key_len = (int)strlen(arrow + 2);
        if (base_len <=  0  || base_len >=  64)  return 0;
        if (key_len  <=  0  || key_len  >=  64)  return 0;

        char base[64];
        char key[64];
        safe_copy(base, token, (size_t)base_len + 1);
        safe_copy(key, arrow + 2, (size_t)key_len + 1);
        if (!PyUtil_IsValidIdentifier(base, PYUTIL_LANG_C99)) return 0;
        if (!PyUtil_IsValidIdentifier(key, PYUTIL_LANG_C99))  return 0;

        safe_copy(out -> base, base, sizeof(out->base));
        safe_copy(out -> key, key, sizeof(out->key));
        out->is_array = 0;
        out->is_struct = 1;
        out->is_arrow = 1;
        return 1;
    }

    /* Try dot: base.key */
    const char* dot = strchr(token, '.');

    if (dot) { 
        int base_len = (int)(dot - token);
        int key_len = (int)strlen(dot + 1);
        if (base_len <=  0  || base_len >=  64)  return 0;
        if (key_len  <=  0  || key_len  >=  64)  return 0;

        char base[64];
        char key[64];
        safe_copy(base, token, (size_t)base_len + 1);
        safe_copy(key, dot + 1, (size_t)key_len + 1);
        if (!PyUtil_IsValidIdentifier(base, PYUTIL_LANG_C99)) return 0;
        if (!PyUtil_IsValidIdentifier(key, PYUTIL_LANG_C99))  return 0;

        safe_copy(out -> base, base, sizeof(out->base));
        safe_copy(out -> key, key, sizeof(out->key));
        out->is_array = 0;
        out->is_struct = 1;
        out->is_arrow = 0;
        return 1;
    }
    return 0;
}

PYUTIL_API int32_t PyUtil_ParseExpr(const char* token, PyUtilExpr* out){
    if (!token || !out) return 0;

    if (PyUtil_ParseStructExpr(token, out)) return 1;
    if (PyUtil_ParseArrayExpr(token, out)) return 1;

    /* Plain Identifier - base only, no key */
    if (PyUtil_IsValidIdentifier(token, PYUTIL_LANG_C99)) {
        safe_copy(out->base, token, sizeof(out->base));
        out->key[0] = '\0';
        out->is_array = 0;
        out->is_struct = 0;
        out->is_arrow = 0;
        return 1;
    }
    return 0;
}

PYUTIL_API int32_t PyUtil_EngineVersion(void){
    return ENGINE_TOOL_VERSION;
}