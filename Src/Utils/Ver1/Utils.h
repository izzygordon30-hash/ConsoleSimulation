#pragma once

#include <stdarg.h>

#ifdef __cplusplus
extern "C" {
#endif


/** 
 * Behind the Scenes
 * Look on this f-string style in C
 */


// ====================================
// Log System
// Log Type
// ====================================
typedef enum LogType{
    LOG_INFO = 0,
    LOG_WARN = 1,
    LOG_ERR =  2,
    LOG_DEBUG = 3,
} LogType;  

// ===============================================
// Reflection System (scanner output)
// ===============================================


typedef enum VarType{
    VAR_INT     =  0,
    VAR_FLOAT   =  1,
    VAR_STRING  =  2,
} VarType;  


typedef struct {    
    const char* name;
    VarType     type; // 0 - Int, 1 - Float, 2 = String
    void*       ptr;
} Var;

typedef struct {
    Var* vars;
    int count;
} Context;

// ===============================================
// ANSI COLOURS
// ===============================================

#define CORE_COLOR_RESET        "\x1b[0m"

#define CORE_COLOR_RED          "\x1b[31"   
#define CORE_COLOR_GREEN        "\x1b[32"
#define CORE_COLOR_YELLOW       "\x1b[33"
#define CORE_COLOR_BLUE         "\x1b[34"
#define CORE_COLOR_MAGENTA      "\x1b[35"
#define CORE_COLOR_CYAN         "\x1b[36"
#define CORE_COLOR_WHITE        "\x1b[37"



/**
 *  __cdecl portability
 * 
 * #### __core_cdecl: caller cleans the stack.
 *      Required for variadic fallback - callee cant know how many args were pushed
 * so it can't clean them up itself.
 * 
 * MSVC names it __cdecl. GCC on x64 has one calling convention
 * so the attribute is a no-op there - but we keep it in the 
 * declaration so the intent is documented and MSVC builds work.
 */
#ifdef _MSC_VER
    #define CORE_API __cdecl
#else
    #define CORE_API /** GCC/Clang already have a caller-cleanup on x86 by default */
#endif

/**
 * ## core_print
 * 
 * ### type - log_level
 * ### string_fmt - format string using {token} syntax
 * ### ctx - optional context.
 * ### ... - variadic fallback when ctx is NULL or key not found
 * 

 * 
 * #### Example Uses:
 *      core_print(LOG_INFO, "hp is {hp}", &ctx) // context path
 *      core_print(LOG_WARN, "val: {int}", NULL, 42) // variadic path
 *      core_print(LOG_ERR, "crash here", NULL) // plain string
 */
void CORE_API core_print(LogType type, const char* string_fmt, Context* ctx, ...);


#ifdef __cplusplus
}
#endif